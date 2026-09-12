#!/usr/bin/env python3
"""CO-109：【L2 自裁 · 参考平面/PDN】In5←In4 走廊空洞 = **按设计**（非『待 L3 派生』）；bridge zone = B.Cu。

触发：CO-108 F-D（medium，未决前提）—— 3 个 bridge zone `layer=In4.Cu` 但名含 `BCU`、basis 明文经 B.Cu 桥接。
本件以**客观证据**裁定并把 step ②（「L3 桥区几何派生」）重定范围：

  R1（L2）3 bridge zone = **B.Cu** 桥（zone 名 + basis 为权威；`layer: In4.Cu` 仅 In4-可达性簿记字段）
  R2（L2）In4 走廊空洞 x∈(49.8, 88.37) = **按设计**（basis 记 PM T2-ECN-1/2：经 B.Cu 桥接、In4 走线带不跨）
  R3（L2）派生**声明的 bridge band 不能清除** In5←In4 残余 —— band 仅覆盖 miss 点的 ≤10%（点级实测）
  R4（L2）⇒ CO-106 `region_scoped_indeterminate`（『几何待 L3 派生』）对 In5←In4 的前提不成立；该带 In5 实为
          **仅 In6 参考**，与 SPEC `impedance.per_layer["In5.Cu"]`（symmetric_stripline, refs=[In4,In6]）**不符**
  R5（OWNER，停）几何侧唯一补救 = 在走廊补 In4 铜 ⇒ **反转已记录的 PM T2-ECN 裁决** ⇒ 须 owner

只读；不改 SPEC/板/阈值/冻结源、不做谐波/SI 计算（终判 = SI9000 + 板厂阻抗券，不得以假设值代填）。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co109_in4_void_l2_ruling.py
"""
from __future__ import annotations
import argparse, collections, hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-13.json"
DRAW = STEP2 / "m13_v57_w3_joint_assignment.json"
CO106 = STEP2 / "m13_v57_co106_reference_plane_gate.json"
OUT = STEP2 / "m13_v57_co109_in4_void_l2_ruling.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
CORRIDOR_X = (49.8, 88.37)          # MCU_VDD_WEST 右缘 ↔ P3V3_EAST 左缘（In4 未声明铜）
FRAME_Y = (33.3, 78.7)
# 声明 bridge band —— 逐字引自 SPEC power_zones[].basis（零坐标搜索：坐标只来自声明 palette）
BANDS = {"P3V3_BCU_BRIDGE_IN4_top": [[23.3, 33.3], [90.0, 33.3], [90.0, 35.0], [23.3, 35.0]],
         "P3V3_AUX_BCU_BRIDGE_IN4_up": [[46.0, 47.75], [62.0, 47.75], [62.0, 52.35], [46.0, 52.35]],
         "P3V3_AUX_BCU_BRIDGE_IN4_low": [[53.75, 61.9], [62.0, 61.9], [62.0, 64.35], [53.75, 64.35]]}
CORRIDOR_POLY = [[CORRIDOR_X[0], FRAME_Y[0]], [CORRIDOR_X[1], FRAME_Y[0]],
                 [CORRIDOR_X[1], FRAME_Y[1]], [CORRIDOR_X[0], FRAME_Y[1]]]
COVER_MAX = 0.10                    # 声明 band 覆盖率上限（超此即须重新裁定）
CORRIDOR_MIN = 0.90                 # 走廊多边形覆盖率下限（牙齿：检测器须能分辨两种口径）


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def polys_of(z):
    ps, p = z.get("polygons"), z.get("polygon")
    if ps:
        return ps if isinstance(ps[0][0], list) else [ps]
    if p:
        return [p] if not isinstance(p[0][0], list) else p
    return []


def pip(pt, poly):
    x, y = pt
    ins = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def in5_in4_miss(spec, draw):
    cu = collections.defaultdict(list)
    for g in spec["pd"]["zone_defs"].get("gnd_planes", []):
        for p in polys_of(g):
            cu[g["layer"]].append(p)
    for z in spec["pd"]["zone_defs"]["power_zones"]:
        for p in polys_of(z):
            cu[z["layer"]].append(p)
    pts = []
    for r in draw["route_geometry"]:
        if r["layer"] != "In5.Cu":
            continue
        P = r["points"]
        sam = [tuple(P[0]), tuple(P[-1])] + [((P[i][0] + P[i + 1][0]) / 2, (P[i][1] + P[i + 1][1]) / 2)
                                             for i in range(len(P) - 1)]
        pts += [q for q in sam if not any(pip(q, p) for p in cu.get("In4.Cu", []))]
    return pts


def board_zone_count():
    try:
        import sys
        sys.path.insert(0, str(K2.parent / "_shared"))
        import pcbnew
        return len(list(pcbnew.LoadBoard(str(BOARD)).Zones()))
    except Exception as ex:
        return {"error": str(ex)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    spec = json.loads(SPEC.read_text())
    draw = json.loads(DRAW.read_text())
    zd = spec["pd"]["zone_defs"]
    bridges = [{"zone": z.get("zone"), "net": z.get("net"), "layer": z.get("layer"),
                "name_has_BCU": "BCU" in str(z.get("zone")), "basis_has_B_Cu": "B.Cu" in str(z.get("basis")),
                "basis_says_In4_not_crossed": "不跨" in str(z.get("basis")),
                "polygons_empty": not z.get("polygons"), "geometry_status": z.get("geometry_status"),
                "vias": len(z.get("vias", [])), "targets": z.get("targets")}
               for z in zd["power_zones"] if z.get("geometry_status") == "L3_CONSTRUCTION_DERIVED"]
    miss = in5_in4_miss(spec, draw)
    n = len(miss)
    cov_bands = sum(1 for q in miss if any(pip(q, p) for p in BANDS.values()))
    cov_corridor = sum(1 for q in miss if pip(q, CORRIDOR_POLY))
    yh = collections.Counter(int(q[1] // 5) * 5 for q in miss)
    xh = collections.Counter(int(q[0] // 5) * 5 for q in miss)
    in4 = [[min(p[0] for p in ps), max(p[0] for p in ps)] for _, ps in
           [(z["net"], p) for z in zd["power_zones"] if z.get("layer") == "In4.Cu" and z.get("polygon")
            for p in polys_of(z)]]
    checks = {
        "A_bridge_zone_layer_ruling": {
            "ok": bool(bridges) and all(b["name_has_BCU"] and b["basis_has_B_Cu"] and b["polygons_empty"] for b in bridges),
            "bridges": bridges,
            "ruling": "R1：3 bridge zone = B.Cu 桥（名 + basis 权威；layer=In4.Cu 仅簿记）"},
        "B_band_coverage_insufficient": {
            "ok": (cov_bands / n) <= COVER_MAX if n else False,
            "n_in5_in4_miss_points": n, "n_inside_declared_bands": cov_bands,
            "frac_inside_declared_bands": round(cov_bands / n, 4) if n else None,
            "n_inside_corridor_polygon": cov_corridor,
            "frac_inside_corridor_polygon": round(cov_corridor / n, 4) if n else None,
            "cover_max": COVER_MAX, "corridor_min": CORRIDOR_MIN,
            "y_bucket_5mm": dict(sorted(yh.items())), "x_bucket_5mm": dict(sorted(xh.items())),
            "ruling": "R3：声明 bridge band 覆盖 ≤10% ⇒ 几何派生不能清除 In5←In4 残余；空洞主体 = In4 走廊"},
        "C_in5_model_mismatch": {
            "ok": "In4.Cu" in spec["impedance"]["per_layer"]["In5.Cu"]["refs"]
                  and spec["impedance"]["per_layer"]["In5.Cu"]["kind"] == "symmetric_stripline",
            "declared_in5_model": spec["impedance"]["per_layer"]["In5.Cu"],
            "in4_declared_x_ranges": in4, "corridor_x": list(CORRIDOR_X),
            "ruling": "R4：走廊内 In4 无铜 ⇒ In5 实为仅 In6 参考；declared symmetric_stripline(refs=[In4,In6]) 在该带不适用"},
        "D_plane_not_realized_at_l4": {
            "ok": True, "board_zone_count": board_zone_count(),
            "ruling": "板在 L4 只落 track/via；平面铺铜为下游步骤 ⇒ 无法以板实判定 In4 走廊铜（亦无声明几何可派生）"},
    }
    teeth = {}
    teeth["coverage_detector"] = ((cov_bands / n) <= COVER_MAX) and ((cov_corridor / n) >= CORRIDOR_MIN)
    teeth["pip_control"] = (pip((70.0, 45.0), CORRIDOR_POLY) is True) and (pip((30.0, 45.0), CORRIDOR_POLY) is False)
    teeth["teeth_ok"] = all(bool(v) for v in teeth.values())
    rulings = [
        {"id": "R1", "level": "L2", "decision": "3 bridge zone 的桥接层 = **B.Cu**（zone 名 `*_BCU_*` + basis 明文；`layer: In4.Cu` 为 In4-可达性簿记字段）。派生这些 zone 不产生该带 In4 铜。"},
        {"id": "R2", "level": "L2", "decision": "In4 走廊空洞 x∈(49.8, 88.37) = **按设计**（basis 记 PM T2-ECN-1/2：经 B.Cu 桥接、『In4 走线带不跨』）。"},
        {"id": "R3", "level": "L2", "decision": f"声明的 3 条 bridge band 仅覆盖 In5←In4 miss 点的 {round(100*cov_bands/n,1)}%（{cov_bands}/{n}）⇒ **『L3 桥区几何派生』不能清除** In5←In4 残余（走廊主体覆盖率 {round(100*cov_corridor/n,1)}%）。"},
        {"id": "R4", "level": "L2", "decision": "CO-106 对 In5←In4 的 `region_scoped_indeterminate`（『几何待 L3 派生』）**前提不成立**：该带 In5 实为仅 In6 参考，与 declared `symmetric_stripline(refs=[In4,In6])` 不符 ⇒ 应改判为**按设计 In4 空洞**并登记为 SI 待验项（终判 = SI9000 + 板厂阻抗券）。"},
        {"id": "R5", "level": "OWNER", "decision": "几何侧唯一补救 = 在走廊补 In4 铜 ⇒ **反转已记录的 PM T2-ECN-1/2 裁决** ⇒ 须 owner（一句话升级，见 escalation）。"},
    ]
    rec = {"artifact": "m13_v57_co109_in4_void_l2_ruling", "schema": 1, "revision": "CO-109.1",
           "nature": "L2 自裁裁定 + step ② 重定范围：In5←In4 走廊空洞 = 按设计（非待 L3 派生）",
           "inputs": {"spec_rev13": s16(SPEC), "drawing": s16(DRAW), "co106_record": s16(CO106),
                      "board": s16(BOARD)},
           "checks": checks, "teeth": teeth, "rulings": rulings,
           "escalation": {"level": "OWNER", "one_line": "是否允许在 In4 走廊 x∈(49.8,88.37) 补平面铜（反转 PM T2-ECN-1/2 裁决）？——否则 In5 该带只能按 In6-单参考域走 SI 终判。"},
           "step2_rescope": ["②a（L2）声明修正：把走廊标为按设计 In4 空洞 + CO-106 分类改判（新 rev）",
                             "②b（SI/外部）走廊内 In5 按 In6-单参考做 SI 终判（SI9000 + 板厂阻抗券；不得以假设值代填）",
                             "②c（L2/L3）3 个 bridge zone 的 B.Cu 几何声明（须声明 palette；MCU_VDD 带未给矩形 ⇒ 缺 palette）",
                             "②d（换会话）任何新 rev 重基线后须另一会话复评"],
           "verdict": "RULED_L2_RESCOPE_WITH_OWNER_ESCALATION",
           "non_claims": ["只读；不改 SPEC/板/阈值/冻结源", "不做 SI/阻抗数值计算（终判 = SI9000 + 板厂阻抗券）",
                          "不改 CO-106 记录字节（改判属后续 rev）"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-109 verdict=%s | bridge=%d | band_cov=%.1f%% corridor_cov=%.1f%% | checks=%s | teeth=%s" % (
        rec["verdict"], len(bridges), 100 * cov_bands / n, 100 * cov_corridor / n,
        {k: v["ok"] for k, v in checks.items()}, teeth["teeth_ok"]))
    print("  record sha16:", s16(Path(a.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
