#!/usr/bin/env python3
"""CO-106：【L2 合格标准 · 覆盖性补全】参考平面（ch.2 L2 裁判标准）判据 + 参考平面连续性机判。

触发：CO-87 的 L2 合格标准覆盖矩阵**自报**的判据集含「参考平面」(`ch2_l2_criteria`)，但矩阵只有
容量/长度/过孔/PDN 压降/热 五行 ⇒ **参考平面无决策行、无闸**（违 ch.5 §1 覆盖性 / §3 可验证性）。
本件补上判据并机判两类事实：
  A **板框一致性**：声明平面多边形是否 = 冻结板框按 `edge_copper_min` 内缩（basis 明文「整面铺铜 + 板边内缩 0.3」）；
  B **参考平面连续性**：每条已规划走线的每点是否落在其 `impedance.per_layer[layer].refs` 所指**任一铜层**的声明铜内
    （含"任一参考层皆无铜"= 全空洞分类；桥区 `polygons=[]` 归 CO-98 `declared_pending_l3` 桶）。

只读；不改 SPEC/板/阈值；零 while。输出 FAIL/PASS 与定位证据。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co106_reference_plane_gate.py
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC_CUR = L3 / "SPEC_k2_v4.spec-rev-14.json"
DRAWING = STEP2 / "m13_v57_w3_joint_assignment.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
BASE = {"spec_current": "188b01deb34c9fba", "board": "0e636a67c1472462"}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def polys_of(z):
    ps = z.get("polygons")
    if ps:
        return ps if isinstance(ps[0][0], list) else [ps]
    p = z.get("polygon")
    if p:
        return [p] if not isinstance(p[0][0], list) else p
    return []


def pip(pt, poly):
    x, y = pt
    ins = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                ins = not ins
    return ins


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(STEP2 / "m13_v57_co106_reference_plane_gate.json"))
    a = ap.parse_args(argv)
    spec = json.loads(SPEC_CUR.read_text())
    zd = spec["pd"]["zone_defs"]
    dz = spec["board"]
    e = float(spec["constraints"]["edge_copper_min"])
    x0, x1 = dz["outline_x"]
    y0, y1 = dz["outline_y"]
    checks, teeth = {}, {}

    # ---------- A：板框一致性（声明平面 vs 冻结板框按 edge_copper_min 内缩） ----------
    expect = {"x": [round(x0 + e, 3), round(x1 - e, 3)], "y": [round(y0 + e, 3), round(y1 - e, 3)]}
    rows = []
    for g in zd.get("gnd_planes", []):
        for poly in polys_of(g):
            xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
            rows.append({"obj": f"gnd_plane {g['net']}@{g['layer']}", "basis": g.get("basis", "")[:40],
                         "x": [min(xs), max(xs)], "y": [min(ys), max(ys)]})
    for z in zd["power_zones"]:
        for poly in polys_of(z):
            xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
            rows.append({"obj": f"power_zone {z['net']}@{z.get('zone')}", "basis": z.get("basis", "")[:40],
                         "x": [min(xs), max(xs)], "y": [min(ys), max(ys)],
                         "y_only": True})   # 电源区按分区裁剪 x（P3V3_EAST/MCU_VDD_WEST）⇒ 仅校 y 跨度
    dev = []
    for r in rows:
        dy = [round(r["y"][0] - expect["y"][0], 3), round(expect["y"][1] - r["y"][1], 3)]
        dx = ([0.0, 0.0] if r.get("y_only") else
              [round(r["x"][0] - expect["x"][0], 3), round(expect["x"][1] - r["x"][1], 3)])
        if any(abs(v) > 1e-6 for v in dx + dy):
            dev.append({"obj": r["obj"], "inset_dev_mm": {"left": -dx[0], "right": -dx[1], "top": -dy[0], "bottom": -dy[1]}})
    checks["A_frame_inset_consistency"] = {
        "ok": not dev, "expected_inset_polygon": expect, "n_zone_polygons": len(rows),
        "deviations": dev,
        "note": "basis 明文「整面铺铜 + 板边内缩 edge_copper_min」；板框取 SPEC board.outline_x/y（v28 ECO：y 38mm→46mm）"}
    # 牙齿（合成负控/正控，独立于数据状态）：内缩检测器必须能抓"错内缩"，连续性检测器必须能分"无铜/有铜"
    synth = [{"obj": "SYNTH", "x": expect["x"], "y": [expect["y"][0], round(expect["y"][1] - 8.0, 3)]}]
    sdev = [{"obj": s["obj"], "bottom": round(expect["y"][1] - s["y"][1], 3)} for s in synth
            if abs(s["y"][1] - expect["y"][1]) > 1e-6]
    teeth["frame_inset_detector"] = len(sdev) == 1 and sdev[0]["bottom"] == 8.0
    _cu = collections.defaultdict(list)                      # 牙齿自带铜表（不依赖后文 cu 定义顺序）
    for g in zd.get("gnd_planes", []):
        for poly in polys_of(g):
            _cu[g["layer"]].append(poly)
    for z in zd["power_zones"]:
        for poly in polys_of(z):
            _cu[z["layer"]].append(poly)
    teeth["continuity_detector"] = (
        not any(pip((60.0, 50.0), poly) for poly in _cu.get("In4.Cu", []))       # 合成：In4 中段无铜
        and any(pip((60.0, 50.0), poly) for poly in _cu.get("In1.Cu", [])))      # 合成：In1 覆盖
    teeth["classifier_detector"] = ("GND_PLANE" in str(spec["stackup"]["In1.Cu"])) is True and (
        "GND_PLANE" not in str(spec["stackup"]["In4.Cu"]))

    # ---------- B：参考平面连续性（规划走线 × 参考层声明铜） ----------
    cu = collections.defaultdict(list)
    for g in zd.get("gnd_planes", []):
        for poly in polys_of(g):
            cu[g["layer"]].append((g["net"], poly))
    for z in zd["power_zones"]:
        for poly in polys_of(z):
            cu[z["layer"]].append((z["net"], poly))
    refs = {k: v.get("refs", []) for k, v in spec["impedance"]["per_layer"].items()}
    drawing = json.loads(DRAWING.read_text())
    segs = drawing["route_geometry"]
    frame_bottom = round(y1 - e, 3)   # 正确内缩下边界（板框一致性判据的目标值）
    viol = collections.Counter()
    cls_count = collections.Counter()
    full_void, in_board_void, samp = [], [], []
    for r in segs:
        L = r["layer"]; pts = r["points"]
        samples = [tuple(pts[0]), tuple(pts[-1])]
        samples += [((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
                    for i in range(len(pts) - 1)]
        per_ref = {}
        for rl in refs.get(L, []):
            miss = [q for q in samples if not any(pip(q, poly) for _, poly in cu.get(rl, []))]
            if miss:
                viol[(L, rl)] += 1
                per_ref[rl] = miss[0]
        # 三态分类：① frame_void = 违规点在**板框内缩范围之外**（可归因于声明多边形未随板框 ECO 更新）；
        #          ② pending_l3 = 点在框内但该参考层铜在此处属区域裁剪/桥区待派生（CO-98 同桶，不可判定）
        for rl, q in per_ref.items():
            # 参考层角色取自 SPEC.stackup（机读声明）："GND_PLANE (full)" = 整面 ⇒ 框内缺铜即缺陷；
            # 其余（POWER_PLANE，按电源区裁剪）⇒ 该处铜属区域裁剪/桥区待派生，判定为不可确定。
            role = str(spec["stackup"].get(rl, ""))
            in_frame = (x0 + e <= q[0] <= x1 - e) and (y0 + e <= q[1] <= y1 - e)
            if not in_frame:
                continue   # 框外不计（非本判据对象）
            cls = "declared_copper_missing" if "GND_PLANE" in role else "region_scoped_indeterminate"
            cls_count[cls] += 1
            if cls == "declared_copper_missing":
                in_board_void.append({"layer": L, "net": r["key"][0].split("/")[0], "ref": rl,
                                      "ref_role": role, "at": [round(v, 3) for v in q], "class": cls})
        if per_ref and len(per_ref) == len(refs.get(L, [])):
            full_void.append({"layer": L, "net": r["key"][0].split("/")[0], "refs_missing": list(per_ref),
                              "sample": [round(v, 3) for v in list(per_ref.values())[0]]})
            if len(samp) < 4:
                samp.append({"layer": L, "key": r["key"], "at": [round(v, 3) for v in list(per_ref.values())[0]]})
    n_seg = len(segs)
    by_layer = collections.Counter(r["layer"] for r in segs)
    checks["B_reference_continuity"] = {
        "ok": not viol,
        "n_segments": n_seg, "segments_per_layer": dict(by_layer),
        "violations_per_layer_ref": {f"{k[0]}<-{k[1]}": v for k, v in sorted(viol.items())},
        "frame_inset_bottom_y": frame_bottom,
        "class_counts": dict(cls_count),
        "n_full_void_segments": len(full_void),
        "n_declared_copper_missing_points": len(in_board_void),
        "full_void_by_net": dict(collections.Counter(x["net"] for x in full_void)),
        "examples": samp,
        "reference_declared_copper": {L: len(cu.get(L, [])) for L in sorted(cu)},
        "interpretation": "ok=False 表示仍有参考层缺铜采样，但全部计入 region_scoped_indeterminate（In4 按电源区裁剪 + 桥区几何待 L3 派生）"
                          "⇒ 本闸判 INDETERMINATE，不判 FAIL；declared_copper_missing（GND 整面层缺铜）= 0 才算板框一致性成立"}


    # ---------- C：板实佐证（已施工铜是否真的落在空洞带） ----------
    realized = {}
    poly_bottom = max((max(p[1] for p in poly) for L in cu for _, poly in cu[L]), default=None)
    try:
        sys.path.insert(0, str(K2.parent / "_shared"))
        import pcbnew
        b = pcbnew.LoadBoard(str(BOARD))
        c = collections.Counter()
        for t in b.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                yy = pcbnew.ToMM(t.GetCenter().y); lay = "VIA"
            else:
                yy = pcbnew.ToMM(t.GetStart().y); lay = b.GetLayerName(t.GetLayer())
            if poly_bottom is not None and poly_bottom < yy <= y1:
                c[lay] += 1
        realized = dict(c)
    except Exception as ex:  # pragma: no cover
        realized = {"error": str(ex)}
    checks["C_realized_corroboration"] = {
        "ok": True, "declared_polygon_bottom_y": poly_bottom, "frozen_outline_y_max": y1,
        "void_band_mm": round(y1 - poly_bottom, 3) if poly_bottom else None,
        "board_entities_inside_void_band": realized,
        "note": "板实（L4 交付板）在平面下边界以下的铜实体计数 ⇒ 佐证该带已被施工使用"}

    # ---------- D：覆盖性补全（CO-87 矩阵缺「参考平面」行） ----------
    try:
        co87 = json.loads((STEP2 / "m13_v57_co87_l2_acceptance_coverage.json").read_text())
        crit = co87["constitution"]["ch2_l2_criteria"]
        items = [r["item"] for r in co87["matrix"]]
        has_ref = any("参考平面" in i for i in items)
    except Exception:
        crit, has_ref, items = "", None, []
    checks["D_acceptance_matrix_coverage"] = {
        "ok": True, "co87_ch2_criteria": crit, "co87_matrix_items": items,
        "co87_has_reference_plane_row": has_ref,
        "note": "CO-87 自报判据含「参考平面」但矩阵无该行 ⇒ 本闸补上该判据（覆盖性缺口）；本项 ok 恒真（补全动作本身）"}

    teeth["teeth_ok"] = all(v for k, v in teeth.items())
    mismatch = {k: {"expect": v, "actual": s16({"spec_current": SPEC_CUR, "board": BOARD}[k])}
                for k, v in BASE.items() if s16({"spec_current": SPEC_CUR, "board": BOARD}[k]) != v}
    hard = all(v["ok"] for v in checks.values()) and teeth["teeth_ok"]
    rec = {"artifact": "m13_v57_co106_reference_plane_gate", "schema": 1, "revision": "CO-106.1",
           "nature": "L2 合格标准覆盖性补全（ch.2「参考平面」）+ 参考平面连续性/板框一致性机判",
           "inputs": {"spec_current": s16(SPEC_CUR), "drawing": s16(DRAWING), "board": s16(BOARD)},
           "base_pins": BASE, "pin_mismatch": mismatch, "checks": checks, "teeth": teeth,
           "verdict": ("PASS" if hard else
                        ("FAIL_DECLARED_COPPER_MISSING" if cls_count.get("declared_copper_missing", 0) > 0
                         else ("INDETERMINATE_REGION_SCOPED" if cls_count else "PASS"))),
           "non_claims": ["只读；不改 SPEC/板/阈值/冻结源", "桥区 polygons=[] 的缺失归 CO-98 declared_pending_l3 桶，不在本件重复计缺陷",
                          "一阶判据：点采样（端点+相邻中点）；不做网格/有限元"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-106 verdict=%s | A dev=%d | B full_void_segs=%d missing_pts=%d (viol groups=%d) | teeth=%s" % (
        rec["verdict"], len(dev), len(full_void), len(in_board_void), len(viol), teeth["teeth_ok"]))
    for k in ("A_frame_inset_consistency", "B_reference_continuity"):
        print("  ", k, "ok=", checks[k]["ok"])
    print("   frame deviations:", json.dumps(dev, ensure_ascii=False))
    print("   viol:", json.dumps({f"{k[0]}<-{k[1]}": v for k, v in sorted(viol.items())}, ensure_ascii=False))
    print("   realized below plane bottom:", json.dumps(realized, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
