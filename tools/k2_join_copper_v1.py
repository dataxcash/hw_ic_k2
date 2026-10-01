#!/usr/bin/env python3
"""k2_join_copper_v1.py —— #K2-507「join 半」之**链内动词**（子进程 · 有界 · 确定性 · fail-loud）。

把板上**单端悬空**（one-end-dangling）之走线桩，用**同网有界缝合**接上：**同层**用一条直线腿，**跨层**用
**一枚过孔**；两者皆走**真形间距模型**（`k2_pin_escape_plan_v1._leg_clear`）。**找不到目标者逐件具名**。
落铜经**在册** `k2_port_plane_stitch_v1.stitch()`（自带 ∂R 边界校验 ＋ 在册落盘模板）⇒ **框内纪律**。
"""
import argparse, importlib.util, json, os, sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


def build_pad_rects(board_path, planner, pcmod, P):
    """#K2-509 sec.2 item 2（真形化）：把板上**全部焊盘**建成**真形圆角矩形**障碍记录。

    旧路（`board_items`）把焊盘建成**内切胶囊** —— 正是 `R1668` 已在**逃逸规划器**里修掉的那把粗尺
    （内切 ⇒ **方角隐形** ⇒ 缝合腿会擦角）。join 现改用同一真形模型（`_true_corner_radius` ＋
    `pad_obstacle_shape`），与逃逸侧口径一致。只读 · 确定性。
    """
    b = P.LoadBoard(board_path)
    out = []
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            pos = pd.GetPosition(); cx, cy = P.ToMM(pos.x), P.ToMM(pos.y)
            sz = pd.GetSize(); sx, sy = P.ToMM(sz.x), P.ToMM(sz.y)
            rr = pcmod._true_corner_radius(P, pd, sx, sy)
            for L in pd.GetLayerSet().Seq():
                out.append(planner.pad_obstacle_shape(pd.GetNetname() or "", b.GetLayerName(L),
                                                      cx, cy, sx, sy, pd.GetOrientationDegrees(), rr))
    return out


def build_hole_walls(board_path, P):
    """#K2-528: every existing DRILL as an obstacle on EVERY layer it passes (radius = drill/2). Layers come from the
    board's own CuStack order - no integer-id assumption. Covers buried/blind vias (whose drill crosses layers with no
    annulus) and PTH pads (modelled on F.Cu/B.Cu only, yet their drill crosses every layer)."""
    b = P.LoadBoard(board_path)
    stack = [b.GetLayerName(L) for L in b.GetLayerSet().CuStack()]
    idx = {n: i for i, n in enumerate(stack)}
    out = []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        ids = list(t.GetLayerSet().Seq())
        if not ids:
            continue
        try:
            r = P.ToMM(t.GetDrill()) / 2.0
        except Exception:                                          # noqa: BLE001
            continue
        if r <= 0:
            continue
        pos = t.GetPosition(); x, y = P.ToMM(pos.x), P.ToMM(pos.y)
        a, c = idx.get(b.GetLayerName(ids[0])), idx.get(b.GetLayerName(ids[-1]))
        if a is None or c is None:
            continue
        for i in range(min(a, c), max(a, c) + 1):
            out.append((t.GetNetname(), stack[i], x, y, x, y, r))
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            try:
                ds = pd.GetDrillSize()
            except Exception:                                      # noqa: BLE001
                continue
            if ds.x <= 0:
                continue
            r = P.ToMM(ds.x) / 2.0
            pos = pd.GetPosition(); x, y = P.ToMM(pos.x), P.ToMM(pos.y)
            for n in stack:
                out.append((pd.GetNetname() or "", n, x, y, x, y, r))
    return out


def declared_geom(spec_path, rect, mr):
    """#K2-532: the AUTHORISED outside-frame geometry of the in-register drawing (lines with allow_outside_dR).

    Returns {(net, layer_or_VIA, *canonical outside geometry)} WITHOUT the width, so the verb can mark ONLY those
    emitted lines as allow_outside_dR for the registered stitch(). Everything else stays REFUSED by the dR bound.
    """
    import json as _j, sys as _s
    _s.path.insert(0, _HERE)
    from eda_eng import block as _blk
    out = set()
    if not spec_path or not os.path.isfile(spec_path):
        return out
    try:
        d = _j.load(open(spec_path, encoding="utf-8"))
    except Exception:                                          # noqa: BLE001
        return out
    for L in (d.get("lines") or []):
        if not L.get("allow_outside_dR"):
            continue
        if L.get("kind") == "via":
            at = [float(v) for v in L["at"]]
            out.add((L.get("net"), "VIA", round(at[0], 3), round(at[1], 3)))
        elif L.get("kind") == "track":
            a = tuple(float(v) for v in L["a"]); b = tuple(float(v) for v in L["b"])
            for (pp, qq) in _blk.clip_iu(a, b, rect)[1]:
                if (pp[0] - qq[0]) ** 2 + (pp[1] - qq[1]) ** 2 <= 1e-16:
                    continue
                out.add((L.get("net"), L.get("layer")) + tuple(round(v, 3) for v in _blk._canon(pp, qq)))
    return out


def plan_joins(items, rect, planner, mr, clear=0.30, max_len=2.0, step=0.1, tol=0.02, reach=2.0,
               via_r=0.175, local_r=3.5, pad_rects=None, hole_walls=None):
    """**纯函数**：给定 item 清单与域，返回 {"joins":[...], "refused":[...], "n_one_end":n}。
    one-end 桩（恰好一端悬空）⇒ 同层直线腿优先，其次跨层过孔；**零搜索之外的定步长枚举**；确定性。
    """
    bad = mr.dangling_ends(items)
    owner = defaultdict(set)
    by_key = defaultdict(list)
    for i, it in enumerate(items):
        k, l, x1, y1, x2, y2, hw, net = it
        for (px, py) in ((x1, y1), (x2, y2)):
            by_key[(round(px, 4), round(py, 4), l, net)].append(i)
    for d in bad:
        for i in by_key.get((round(d["at"][0], 4), round(d["at"][1], 4), d["layer"], d["net"]), []):
            owner[i].add((round(d["at"][0], 4), round(d["at"][1], 4)))
    x0, y0, x1r, y1r = [float(v) for v in rect]
    joins, refused = [], []
    n_one = 0
    for i in sorted(owner):
        it = items[i]; k, l, xa, ya, xb, yb, hw, net = it
        if k != "TRK" or len(owner[i]) != 1:
            continue                                    # 全漂浮件属 prune 域；非走线件不动
        ex, ey = sorted(owner[i])[0]
        if not (x0 <= ex <= x1r and y0 <= ey <= y1r):
            continue                                    # 框外不碰（C6 纪律）
        n_one += 1
        loc = [o for o in items
               if o[1] == l and (abs(o[2] - ex) <= local_r or abs(o[4] - ex) <= local_r)
               and (abs(o[3] - ey) <= local_r or abs(o[5] - ey) <= local_r)]
        targs = [(o[2], o[3], o[4], o[5]) for o in loc
                 if o[7] == net and o[0] != "PAD" and not (o[2] == xa and o[3] == ya and o[4] == xb and o[5] == yb)]
        # #K2-509 sec.2 item 2: foreign pads come from the TRUE-SHAPE list (rect records), not the inscribed
        # capsule that board_items still yields; tracks/vias stay as exact capsules.
        obsg = [(o[7], mr.LNAME[o[1]], o[2], o[3], o[4], o[5], o[6])
                for o in loc if o[7] != net and o[0] != "PAD"]
        for _h in (hole_walls or []):
            if _h[0] != net and _h[1] == mr.LNAME[l] and abs(_h[2] - ex) <= local_r and abs(_h[3] - ey) <= local_r:
                obsg.append(_h)
        for _r in (pad_rects or []):
            if _r[0] == net or _r[1] != mr.LNAME[l]:
                continue
            cx_, cy_ = (float(_r[2]) + float(_r[4])) / 2.0, (float(_r[3]) + float(_r[5])) / 2.0
            if abs(cx_ - ex) <= local_r and abs(cy_ - ey) <= local_r:
                obsg.append(_r)
        r = planner.join_for_end(net, mr.LNAME[l], (ex, ey), obsg, targs, clear, max_len, step, tol,
                                 own=(xa, ya, xb, yb))   # #K2-507(a): no degenerate re-lay along our own line
        if r.get("join"):
            j = r["join"]; j["_kind"] = "track"; joins.append(j)
            continue
        # 跨层：找同网他层最近之铜
        cand = []
        for o in items:
            if o[7] != net or o[1] == l or o[0] == "PAD":
                continue
            for (qx, qy) in ((o[2], o[3]), (o[4], o[5])):
                dd = ((qx - ex) ** 2 + (qy - ey) ** 2) ** 0.5
                if dd <= reach:
                    cand.append((round(dd, 6), mr.LNAME[o[1]], qx, qy))
        cand.sort()
        got = None
        for (dd, ol, qx, qy) in cand:
            # #K2-509 sec.2 item 2: check EVERY copper layer (a blind via's annulus may reach layers the integer
            # id ordering mis-suggests). Conservative superset - the ordering assumption is gone.
            span = [mr.LNAME[z] for z in mr.LAYERS]
            osp = [x_ for x_ in items if x_[7] != net]
            obs2 = [(o[7], mr.LNAME[o[1]], o[2], o[3], o[4], o[5], o[6]) for o in osp
                    if (abs(o[2] - ex) <= local_r or abs(o[4] - ex) <= local_r)
                    and (abs(o[3] - ey) <= local_r or abs(o[5] - ey) <= local_r)]
            for _h in (hole_walls or []):
                if _h[0] != net and abs(_h[2] - ex) <= local_r and abs(_h[3] - ey) <= local_r:
                    obs2.append(_h)
            for _r in (pad_rects or []):                       # true-shape pads, every layer the via may touch
                if _r[0] == net:
                    continue
                cx_, cy_ = (float(_r[2]) + float(_r[4])) / 2.0, (float(_r[3]) + float(_r[5])) / 2.0
                if abs(cx_ - ex) <= local_r and abs(cy_ - ey) <= local_r:
                    obs2.append(_r)
            rv = planner.via_join_for_end(net, mr.LNAME[l], ol, (ex, ey), (qx, qy), obs2, span,
                                          clear=clear, via_r=via_r, step=0.05, tol=tol,
                                          existing_vias=[x_ for x_ in items if x_[0] == "VIA"])
            if rv.get("join"):
                got = rv["join"]; got["_kind"] = "via"; got["_other"] = ol; break
            # #K2-519: the single-via family is provably infeasible here -> try the TWO-HOP connector (deterministic)
            rh = planner.via_hop_join(net, mr.LNAME[l], ol, (ex, ey), (qx, qy), obs2, span,
                                      clear=clear, via_r=via_r, step=0.1, max_len=max_len,
                                      existing_vias=[x_ for x_ in items if x_[0] == "VIA"])
            if rh.get("join"):
                got = rh["join"]; got["_kind"] = "multi"; got["_other"] = ol; break
        if got:
            joins.append(got)
        else:
            refused.append({"net": net, "layer": mr.LNAME[l], "at": [ex, ey],
                            "why": "no same-layer leg and no clear via to a same-net target within reach"})
    return {"joins": joins, "refused": refused, "n_one_end": n_one}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--rect", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--json-out")
    ap.add_argument("--clear", type=float, default=0.30); ap.add_argument("--max-len", type=float, default=2.0)
    ap.add_argument("--declare", default=None, help="#K2-532: drawing whose allow_outside_dR lines authorise emitted geometry")
    a = ap.parse_args(argv)
    mr = _mod("k2mrjoin", os.path.join(_HERE, "k2_p4_mroute_v1.py"))
    planner = _mod("k2pejoin", os.path.join(_HERE, "k2_pin_escape_plan_v1.py"))
    pps = _mod("k2ppsjoin", os.path.join(_HERE, "k2_port_plane_stitch_v1.py"))
    rect = [float(v) for v in a.rect.split(",")]
    items = mr.board_items(a.board)
    pcmod = _mod("k2pcjoin", os.path.join(_HERE, "k2_pin_escape_precheck_v1.py"))
    import pcbnew as _P
    # #K2-528/R1788: the planner's via radius MUST be the radius the registered stitch() actually lays
    # (k2_port_plane_stitch_v1: L.get("size", 0.45)); the old 0.175 assumption was 0.05mm smaller than the laid
    # 0.225, which systematically widened the clearance verdict and let an edge-case pair (0.1967 vs 0.200) through.
    _VIA_SIZE = 0.45
    pj = plan_joins(items, rect, planner, mr, clear=a.clear, max_len=a.max_len, via_r=_VIA_SIZE / 2.0,
                    pad_rects=build_pad_rects(a.board, planner, pcmod, _P),
                    hole_walls=build_hole_walls(a.board, _P))
    lines = []
    for n, j in enumerate(pj["joins"]):
        if j["_kind"] == "track":
            lines.append({"n": "J%d" % n, "kind": "track", "net": j["net"], "layer": j["layer"],
                          "a": j["a"], "b": j["b"]})
        elif j["_kind"] == "via":
            lines.append({"n": "J%d" % n, "kind": "via", "net": j["net"], "at": j["at"],
                          "layers": [j["layers"][0], j["_other"]]})
        else:                                            # #K2-519 two-hop: one via + two legs
            lines.append({"n": "J%da" % n, "kind": "via", "net": j["net"], "at": j["via"]["at"],
                          "layers": [j["via"]["layers"][0], j["_other"]]})
            for _li, _lg in enumerate(j["legs"]):
                lines.append({"n": "J%db%d" % (n, _li), "kind": "track", "net": j["net"],
                              "layer": _lg["layer"], "a": _lg["a"], "b": _lg["b"]})
    import sys as _s2
    _s2.path.insert(0, _HERE)
    from eda_eng import block as _blk2
    _dg = declared_geom(a.declare, rect, mr) if getattr(a, "declare", None) else set()
    _n_auth = 0
    for _L in lines:
        if _L["kind"] == "via":
            if (_L["net"], "VIA", round(float(_L["at"][0]), 3), round(float(_L["at"][1]), 3)) in _dg:
                _L["allow_outside_dR"] = True; _n_auth += 1
            continue
        _a = tuple(float(v) for v in _L["a"]); _b = tuple(float(v) for v in _L["b"])
        for (_pp, _qq) in _blk2.clip_iu(_a, _b, rect)[1]:
            if (_pp[0] - _qq[0]) ** 2 + (_pp[1] - _qq[1]) ** 2 <= 1e-16:
                continue
            if (_L["net"], _L["layer"]) + tuple(round(v, 3) for v in _blk2._canon(_pp, _qq)) in _dg:
                _L["allow_outside_dR"] = True; _n_auth += 1
    rep = {"artifact": "k2_join_copper_v1", "board": a.board, "out": a.out,
           "n_one_end": pj["n_one_end"], "n_planned": len(pj["joins"]), "n_refused": len(pj["refused"]), "n_authorised": _n_auth,
           "pad_model": "TRUE rounded-rectangle (pad_obstacle_shape) - #K2-509 sec.2 item 2",
           "refused": pj["refused"], "lines": lines}
    if lines:
        r = pps.stitch(a.board, rect, {"rect": rect, "lines": lines}, a.out)
        rep["lay"] = {"n_added": r.get("n_added"), "n_refused": r.get("n_refused"), "refused": r.get("refused")}
    else:
        rep["lay"] = {"n_added": 0, "n_refused": 0, "refused": []}
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in ("n_one_end", "n_planned", "n_refused", "lay")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
