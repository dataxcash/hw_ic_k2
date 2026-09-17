#!/usr/bin/env python3
"""K2 P4 · ⑥ **L2 placement 增量 + 40 件 courtyard 补全 v1**（改板，默认 dry-run）。

依据：`k2/docs/K2-P4-COURTYARD-AND-LIB-REGISTER-v1.md` §2（L2 最小集）+ handoff inc36 §3。
本工具执行 ⑥ 的可执行工作单（**判据只读，落板归监理**）：

  ① 移 `D2`（+x，解 `U4↔D2`/`D2↔U2` 的 courtyard 实重叠）
  ② 移 `L1`（+y，解 `L1↔U2`）
  ③ 移 `U4`（+y，解 `U4↔D2`）并为其 P3V3 顶盘补 0/90° 短线（保连接，非 45°=0）
  ④ 为 40 件无 courtyard 封装**按面补** `CrtYd`（Add-only；无 `RemoveNative`，T-37）
     margin = min(KLC nominal 0.25, 该件**最大可用外扩**)：逐件对**同面**既有/已补 courtyard
     做真实多边形交集二分（跨面不计，与 KiCad `courtyards_overlap` 同语义）。

硬闸（任一不达 ⇒ 退出码 1，禁缩口径）：error = 0 · unconnected = 0 · `missing_courtyard` = 0 ·
`courtyards_overlap` = 0 · 无违规类型增量。
纪律：T-22（备份 src；落板后同名 pro 逐字节不变）· T-25（ZONE_FILLER 重填）· T-37 · T-38（种子）·
T-41（写仓库须 `--apply --confirm-repo-write`）。默认只写 work-dir。

用法（dry-run）：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_l2_placement_courtyard_v1.py \
    --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
    --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/l2/run
（落板）追加 `--apply --confirm-repo-write`
"""
import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import k2_p4_w7_repair_v1 as W

NM = 1_000_000
SEED = 20260918
CRTYD_W = 50_000          # 0.05mm
TRACE_W = 200_000         # 0.2mm
D2_DX = 0.40              # mm, +x
L1_DY = 0.30              # mm, +y
U4_DY = 0.95              # mm, +y
MARGIN_NOM = 0.25         # KLC nominal courtyard margin (mm)
INTERFACE_REFS = ["J2", "J3", "J4", "J6", "J9", "J11", "J12", "J13"]


def v2(x, y):
    return pcbnew.VECTOR2I(int(round(x)), int(round(y)))


def sha16(p):
    return W.sha16(p)


# --------------------------------------------------------------- courtyard geo
def poly_of(fp, layer):
    try:
        ps = fp.GetCourtyard(layer)
    except Exception:
        return []
    out = []
    for i in range(ps.OutlineCount()):
        ol = ps.Outline(i)
        pts = [(ol.CPoint(j).x, ol.CPoint(j).y) for j in range(ol.PointCount())]
        if len(pts) >= 3:
            out.append(pts)
    return out


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def polyset_from(pts_list):
    ps = pcbnew.SHAPE_POLY_SET()
    for pts in pts_list:
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in pts:
            ch.Append(pcbnew.VECTOR2I(int(x), int(y)))
        ch.SetClosed(True)
        ps.AddOutline(ch)
    return ps


def overlaps(pts, others_ps):
    if not pts:
        return False
    cand = polyset_from([pts])
    cand.BooleanIntersection(others_ps)
    return cand.OutlineCount() > 0


def pad_fab_box(fp):
    xs, ys = [], []
    for p in fp.Pads():
        b = p.GetBoundingBox()
        xs += [b.GetLeft(), b.GetRight()]
        ys += [b.GetTop(), b.GetBottom()]
    side_fab = pcbnew.B_Fab if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_Fab
    for g in fp.GraphicalItems():
        if g.GetLayer() == side_fab:
            b = g.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]
            ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def crtyd_layer(fp):
    return pcbnew.B_CrtYd if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_CrtYd


def lacks_courtyard(fp):
    for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        if poly_of(fp, lay):
            return False
    return True


# ------------------------------------------------------------------ mutations
def move_fp(bd, ref, dx_nm, dy_nm):
    fp = next((f for f in bd.GetFootprints() if f.GetReference() == ref), None)
    if fp is None:
        raise RuntimeError(f"{ref} not found")
    old = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(int(old.x + dx_nm), int(old.y + dy_nm)))
    return {"ref": ref, "from": [old.x, old.y], "to": [int(old.x + dx_nm), int(old.y + dy_nm)]}


ANG_TOL = 2_000  # nm：允许 45° 线因端点取整产生的 ~0.08µm 偏差（板内既有 6 条）


def angle_ok(s, e):
    dx, dy = e.x - s.x, e.y - s.y
    if dx == 0 and dy == 0:
        return False
    return dx == 0 or dy == 0 or abs(abs(dx) - abs(dy)) <= ANG_TOL


def add_track(bd, net, layer, a, b, width=TRACE_W):
    s, e = v2(*a), v2(*b)
    if s.x == e.x and s.y == e.y:
        return None
    tr = pcbnew.PCB_TRACK(bd)
    tr.SetStart(s)
    tr.SetEnd(e)
    tr.SetWidth(width)
    tr.SetLayer(layer)
    tr.SetNet(bd.FindNet(net))
    bd.Add(tr)
    rec = {"net": net, "layer": pcbnew.LayerName(layer), "from": [s.x, s.y], "to": [e.x, e.y]}
    if not angle_ok(s, e):
        raise RuntimeError(f"non-45/90 leg: {rec}")
    return rec


def prune_pad_stubs(bd, moved):
    """移件后：若某 pad 的原连接段「旧盘心端」已离开新盘且在空处、而「另一端」落在新盘内，
    则该段冗余（新盘已直接覆盖另一端）⇒ 删除，避免 track_dangling（改既有铜，逐条登记）。"""
    removed = []
    for m in moved:
        ref, dx, dy = m["ref"], m["to"][0] - m["from"][0], m["to"][1] - m["from"][1]
        fp = next(f for f in bd.GetFootprints() if f.GetReference() == ref)
        for p in fp.Pads():
            net = p.GetNetname()
            if not net:
                continue
            pc = p.GetPosition()
            oldc = pcbnew.VECTOR2I(pc.x - dx, pc.y - dy)
            for t in list(bd.GetTracks()):
                if W.is_via(t) or t.GetNetname() != net:
                    continue
                s, e = t.GetStart(), t.GetEnd()
                for near, far in ((s, e), (e, s)):
                    if abs(near.x - oldc.x) <= 2_000 and abs(near.y - oldc.y) <= 2_000:
                        if (not p.HitTest(near)) and p.HitTest(far):
                            bd.RemoveNative(t)
                            removed.append({"ref": ref, "pad": p.GetPadName(), "net": net,
                                            "uuid": W.uid(t)[:8],
                                            "from": [s.x, s.y], "to": [e.x, e.y]})
                        break
    return removed


def u4_stub(bd, u4_dy_nm):
    """U4 顶盘 (pad3, P3V3) 南移后，补 90° 竖线回原 y 轨道行 + 桥接需接的原段。"""
    fp = next(f for f in bd.GetFootprints() if f.GetReference() == "U4")
    pad = next(p for p in fp.Pads() if p.GetNetname() == "P3V3")
    pc = pad.GetPosition()                      # 新位置
    old_y = pc.y - u4_dy_nm                     # 原盘 y
    net = pad.GetNetname()
    segs = []
    for t in bd.GetTracks():
        if W.is_via(t) or t.GetNetname() != net or t.GetLayer() != pcbnew.F_Cu:
            continue
        s, e = t.GetStart(), t.GetEnd()
        if s.y != e.y or abs(s.y - old_y) > 400_000:
            continue
        a, b = min(s.x, e.x), max(s.x, e.x)
        if b < pc.x - 1_500_000 or a > pc.x + 1_500_000:
            continue
        segs.append((a, b, s.y))
    if not segs:
        raise RuntimeError("U4 P3V3 轨道行未找到")
    y_row = segs[0][2]
    made = [add_track(bd, net, pcbnew.F_Cu, (pc.x, pc.y), (pc.x, y_row))]
    bridges = []
    for a, b, y in segs:
        if not (a <= pc.x <= b):
            near = a if a > pc.x else b
            bridges.append((near, y))
    for near, y in sorted(set(bridges)):
        if near == pc.x:
            continue
        made.append(add_track(bd, net, pcbnew.F_Cu, (pc.x, y_row), (near, y)))
    return {"pad": pad.GetPadName(), "row_y": y_row, "legs": [m for m in made if m]}


def add_courtyards(bd, margin_nom_nm):
    """Add-only 补 CrtYd；margin 逐件二分（同面真实多边形交集）。返回逐件记录。"""
    fps = list(bd.GetFootprints())
    # 同面 others 集合（既有 courtyard 全部先入）
    others = {pcbnew.F_CrtYd: polyset_from([p for f in fps for p in poly_of(f, pcbnew.F_CrtYd)]),
              pcbnew.B_CrtYd: polyset_from([p for f in fps for p in poly_of(f, pcbnew.B_CrtYd)])}
    rows = []
    for fp in fps:
        if not lacks_courtyard(fp):
            continue
        box = pad_fab_box(fp)
        if box is None:
            rows.append({"ref": fp.GetReference(), "error": "no pad/fab geometry"})
            continue
        lay = crtyd_layer(fp)
        x0, y0, x1, y1 = box
        # 二分最大可用外扩（<= nominal）
        lo, hi = 0, margin_nom_nm
        best = None
        if not overlaps(rect_pts(x0, y0, x1, y1), others[lay]):
            best = 0
            while lo <= hi:
                mid = (lo + hi) // 2
                if not overlaps(rect_pts(x0 - mid, y0 - mid, x1 + mid, y1 + mid), others[lay]):
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
        rows.append({"ref": fp.GetReference(), "side": pcbnew.LayerName(lay),
                     "box_mm": [round(v / NM, 3) for v in box],
                     "margin_mm": None if best is None else round(best / NM, 3),
                     "overlap_at_margin0": best is None})
        if best is None:
            continue
        mx = best
        sh = pcbnew.PCB_SHAPE(fp)
        sh.SetShape(pcbnew.SHAPE_T_RECT)
        sh.SetStart(v2(x0 - mx, y0 - mx))
        sh.SetEnd(v2(x1 + mx, y1 + mx))
        sh.SetLayer(lay)
        sh.SetWidth(CRTYD_W)
        fp.Add(sh)
        others[lay].BooleanAdd(polyset_from([rect_pts(x0 - mx, y0 - mx, x1 + mx, y1 + mx)]))
    return rows


# --------------------------------------------------------------------- audit
def non45_count(bd):
    bad = []
    for t in bd.GetTracks():
        if W.is_via(t):
            continue
        s, e = t.GetStart(), t.GetEnd()
        if not angle_ok(s, e):
            bad.append([W.uid(t)[:8], pcbnew.LayerName(t.GetLayer()),
                        round(s.x / NM, 3), round(s.y / NM, 3), round(e.x / NM, 3), round(e.y / NM, 3)])
    return bad


def interface_out_of_frame(bd, inset_nm=300_000):
    x0, y0, x1, y1 = None, None, None, None
    xs, ys = [], []
    for d in bd.GetDrawings():
        if pcbnew.LayerName(d.GetLayer()) == "Edge.Cuts":
            try:
                p1, p2 = d.GetStart(), d.GetEnd()
                xs += [p1.x, p2.x]; ys += [p1.y, p2.y]
            except Exception:
                b = d.GetBoundingBox()
                xs += [b.GetLeft(), b.GetRight()]; ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        return {"error": "no Edge.Cuts"}
    x0, y0, x1, y1 = min(xs) + inset_nm, min(ys) + inset_nm, max(xs) - inset_nm, max(ys) - inset_nm
    bad = []
    for f in bd.GetFootprints():
        if f.GetReference() not in INTERFACE_REFS:
            continue
        for p in f.Pads():
            b = p.GetBoundingBox()
            if b.GetLeft() < x0 or b.GetTop() < y0 or b.GetRight() > x1 or b.GetBottom() > y1:
                bad.append([f.GetReference(), p.GetPadName()])
    return {"frame_inset_nm": [x0, y0, x1, y1], "violations": bad}


def column_x_check(bd, want_mm=27.94):
    rows = {}
    for f in bd.GetFootprints():
        if f.GetReference() in ["J6", "J9", "J11", "J12", "J13"]:
            rows[f.GetReference()] = round(f.GetPosition().x / NM, 4)
    rows["all_equal_want"] = all(abs(v - want_mm) < 1e-4 for k, v in rows.items() if k != "all_equal_want")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--pro", required=True)
    ap.add_argument("--kicad-cli", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--d2-dx", type=float, default=D2_DX)
    ap.add_argument("--u4-dy", type=float, default=U4_DY)
    ap.add_argument("--l1-dy", type=float, default=L1_DY)
    ap.add_argument("--margin-nom", type=float, default=MARGIN_NOM)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)
    if a.apply and not a.confirm_repo_write:
        print("REFUSE: --apply 需 --confirm-repo-write（T-41）", file=sys.stderr)
        return 2
    try:
        pcbnew.KIID.SeedGenerator(SEED)
    except Exception:
        pass
    board_src, pro_src = os.path.abspath(a.board), os.path.abspath(a.pro)
    work = os.path.abspath(a.work_dir)
    os.makedirs(work, exist_ok=True)
    stem = os.path.splitext(os.path.basename(board_src))[0]
    src_pro_bytes = open(pro_src, "rb").read() if a.apply else None
    if a.apply:
        shutil.copy2(board_src, os.path.join(work, stem + ".src-backup.kicad_pcb"))
        shutil.copy2(pro_src, os.path.join(work, stem + ".pro-backup.kicad_pro"))
    base = W.stage(board_src, pro_src, work, stem)
    probe = os.path.join(work, stem + ".kicad_pro")
    r0 = W.run_drc(a.kicad_cli, base, os.path.join(work, "drc_before.json"))
    bd = pcbnew.LoadBoard(base)
    rep = {"src": {"board": board_src, "board_sha16": sha16(board_src),
                   "pro": pro_src, "pro_sha16": sha16(pro_src)},
           "params_mm": {"d2_dx": a.d2_dx, "u4_dy": a.u4_dy, "l1_dy": a.l1_dy, "margin_nom": a.margin_nom},
           "before": {"counts": W.counts(r0), "unconnected": W.unconn(r0),
                      "non45": non45_count(pcbnew.LoadBoard(base))},
           "moves": [], "u4_stub": None, "courtyards": []}
    rep["moves"].append(move_fp(bd, "D2", int(round(a.d2_dx * NM)), 0))
    rep["moves"].append(move_fp(bd, "L1", 0, int(round(a.l1_dy * NM))))
    rep["moves"].append(move_fp(bd, "U4", 0, int(round(a.u4_dy * NM))))
    rep["pruned_stubs"] = prune_pad_stubs(bd, rep["moves"])
    rep["u4_stub"] = u4_stub(bd, int(round(a.u4_dy * NM)))
    rep["courtyards"] = add_courtyards(bd, int(round(a.margin_nom * NM)))
    W.refill(bd)
    out = os.path.join(work, stem + ".l2-placed.kicad_pcb")
    W.save_with_pro(bd, out, probe)
    rc = W.run_drc(a.kicad_cli, out, out + ".json")
    bd2 = pcbnew.LoadBoard(out)
    rep["after"] = {"counts": W.counts(rc), "unconnected": W.unconn(rc),
                    "board": out, "board_sha16": sha16(out),
                    "non45": non45_count(bd2),
                    "interface_frame": interface_out_of_frame(bd2),
                    "column_x": column_x_check(bd2)}
    # gates
    bad = []
    hb, ha = W.type_hist(r0), W.type_hist(rc)
    for t in sorted(set(hb) | set(ha)):
        if ha.get(t, 0) > hb.get(t, 0):
            bad.append(f"{t}:{hb.get(t, 0)}->{ha.get(t, 0)}")
    for v in rc.get("violations", []):
        if v["severity"] == "error":
            bad.append(f"error:{v['type']}")
    if W.unconn(rc) != 0:
        bad.append(f"unconnected:{W.unconn(rc)}")
    if ha.get("missing_courtyard", 0) != 0:
        bad.append(f"missing_courtyard:{ha.get('missing_courtyard', 0)}")
    if ha.get("courtyards_overlap", 0) != 0:
        bad.append(f"courtyards_overlap:{ha.get('courtyards_overlap', 0)}")
    if len(rep["after"]["non45"]) > len(rep["before"]["non45"]):
        bad.append(f"non45:{len(rep['before']['non45'])}->{len(rep['after']['non45'])}")
    if rep["after"]["interface_frame"].get("violations"):
        bad.append("interface_out_of_frame")
    if not rep["after"]["column_x"].get("all_equal_want"):
        bad.append("column_x")
    if any(c.get("overlap_at_margin0") for c in rep["courtyards"]):
        bad.append("courtyard_unresolved(margin0 overlap)")
    rep["gates"] = {"passed": not bad, "failures": bad}
    # 落板
    if a.apply and not bad:
        shutil.copy2(out, board_src)
        if open(pro_src, "rb").read() != src_pro_bytes:
            shutil.copy2(os.path.join(work, stem + ".pro-backup.kicad_pro"), pro_src)
            raise RuntimeError("pro 字节被改动，已回滚")
        rep["applied"] = {"board_sha16": sha16(board_src), "pro_sha16": sha16(pro_src), "pro_unchanged": True}
    elif a.apply:
        rep["applied"] = {"refused": "gates failed"}
    outrep = a.report or os.path.join(work, "l2_placement_report.json")
    with open(outrep, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1, ensure_ascii=False)
    print("before:", json.dumps(rep["before"], ensure_ascii=False))
    print("after :", json.dumps(rep["after"]["counts"], ensure_ascii=False))
    print("unconnected:", rep["after"]["unconnected"], "| non45:", len(rep["after"]["non45"]))
    print("moves:", json.dumps(rep["moves"], ensure_ascii=False))
    print("u4_stub:", json.dumps(rep["u4_stub"], ensure_ascii=False))
    print("courtyard margins:", json.dumps([(c["ref"], c.get("margin_mm")) for c in rep["courtyards"]], ensure_ascii=False))
    print("gates:", json.dumps(rep["gates"], ensure_ascii=False))
    print("report:", outrep, "| board:", out)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
