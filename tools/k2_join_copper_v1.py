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


def plan_joins(items, rect, planner, mr, clear=0.30, max_len=2.0, step=0.1, tol=0.02, reach=2.0,
               via_r=0.175, local_r=3.5):
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
        obsg = [(o[7], mr.LNAME[o[1]], o[2], o[3], o[4], o[5], o[6]) for o in loc if o[7] != net]
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
            rv = planner.via_join_for_end(net, mr.LNAME[l], ol, (ex, ey), (qx, qy), obs2, span,
                                          clear=clear, via_r=via_r, step=0.05, tol=tol,
                                          existing_vias=[x_ for x_ in items if x_[0] == "VIA"])
            if rv.get("join"):
                got = rv["join"]; got["_kind"] = "via"; got["_other"] = ol; break
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
    a = ap.parse_args(argv)
    mr = _mod("k2mrjoin", os.path.join(_HERE, "k2_p4_mroute_v1.py"))
    planner = _mod("k2pejoin", os.path.join(_HERE, "k2_pin_escape_plan_v1.py"))
    pps = _mod("k2ppsjoin", os.path.join(_HERE, "k2_port_plane_stitch_v1.py"))
    rect = [float(v) for v in a.rect.split(",")]
    items = mr.board_items(a.board)
    pj = plan_joins(items, rect, planner, mr, clear=a.clear, max_len=a.max_len)
    lines = []
    for n, j in enumerate(pj["joins"]):
        if j["_kind"] == "track":
            lines.append({"n": "J%d" % n, "kind": "track", "net": j["net"], "layer": j["layer"],
                          "a": j["a"], "b": j["b"]})
        else:
            lines.append({"n": "J%d" % n, "kind": "via", "net": j["net"], "at": j["at"],
                          "layers": [j["_other"], j["layers"][0]] if False else [j["layers"][0], j["_other"]]})
    rep = {"artifact": "k2_join_copper_v1", "board": a.board, "out": a.out,
           "n_one_end": pj["n_one_end"], "n_planned": len(pj["joins"]), "n_refused": len(pj["refused"]),
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
