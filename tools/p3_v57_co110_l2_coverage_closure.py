#!/usr/bin/env python3
"""CO-110：【L2 自裁 · 施加】参考平面判据入 CO-87 矩阵（F-C）+ CO-106 D 项读径修复（F-E）+ In4 走廊空洞按设计定案（F-D / R5'）。

触发：CO-108 F-C/F-D + 本件新发现 **F-E**（CO-106 D 项读 `co87["inputs"]["matrix"]`，而 CO-87 记录无 `inputs` 键 ⇒
KeyError 被 except 吞掉 ⇒ 覆盖性检查**恒空真**，从未真正校验「参考平面」行）。
施加：① CO-87 矩阵补「参考平面」行（证据机取自 CO-106 记录，非手填）；② CO-106 D 项改读 `constitution.ch2_l2_criteria` + 顶层 `matrix`；
③ 定案 R5'（L2）：**不开 In4 走廊铜**（确认 PM T2-ECN-1/2 既有设计，非反转）⇒ In5 在该带 = In6-单参考域，SI 终判 = 外部。

**零 SPEC/板/阈值/冻结源改动 ⇒ 不需重基线、不需新复评**（先例 CO-105）。只读（除自身记录）。
CLI: python3 tools/p3_v57_co110_l2_coverage_closure.py
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
CO87 = STEP2 / "m13_v57_co87_l2_acceptance_coverage.json"
CO106 = STEP2 / "m13_v57_co106_reference_plane_gate.json"
CO109 = STEP2 / "m13_v57_co109_in4_void_l2_ruling.json"
SPEC13 = L3 / "SPEC_k2_v4.spec-rev-13.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT = STEP2 / "m13_v57_co110_l2_coverage_closure.json"
RP_ROW = "参考平面"
CH2_KEYS = ("走廊", "等长", "参考平面", "PDN 压降", "热")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def row_present(items) -> bool:
    return any(RP_ROW in i for i in items)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    co87 = json.loads(CO87.read_text()); co106 = json.loads(CO106.read_text())
    co109 = json.loads(CO109.read_text())
    items = [r["item"] for r in co87["matrix"]]
    d = co106["checks"]["D_acceptance_matrix_coverage"]
    cov = co109["checks"]["B_band_coverage_insufficient"]
    checks, teeth = {}, {}

    checks["A_r5_prime_ruled"] = {
        "ok": co109["checks"]["A_bridge_zone_layer_ruling"]["ok"] and cov["frac_inside_declared_bands"] <= 0.10,
        "decision": "R5'（L2）：不开 In4 走廊铜（确认 PM T2-ECN-1/2 既有设计）；CO-109 的 OWNER 升级撤回——该选择不反转 PM 裁决。"
                    "In5 在该带 = In6-单参考域；SI 终判 = 外部（SI9000 + 板厂阻抗券）。",
        "bridge_layer": "B.Cu", "withdrawn_escalation": "CO-109 R5（OWNER）→ 撤回",
        "evidence": {"frac_inside_declared_bands": cov["frac_inside_declared_bands"],
                     "frac_inside_corridor_polygon": cov["frac_inside_corridor_polygon"]}}

    checks["B_fc_reference_plane_row"] = {
        "ok": row_present(items) and co87["teeth"].get("ch2_criteria_all_have_rows") is True,
        "co87_matrix_items": items, "n_closed": co87["n_closed"], "n_open": co87["n_open"],
        "ch2_all_covered": co87["teeth"].get("ch2_criteria_all_have_rows")}

    checks["C_fe_co106_d_readpath"] = {
        "ok": bool(d.get("co87_matrix_items")) and d.get("co87_has_reference_plane_row") is True,
        "co87_has_reference_plane_row": d.get("co87_has_reference_plane_row"),
        "d_items_n": len(d.get("co87_matrix_items") or []), "readpath_note": "CO-106 现读 constitution.ch2_l2_criteria + 顶层 matrix（原 inputs.* 恒空真）"}

    checks["D_fd_by_design_void"] = {
        "ok": cov["ok"] and cov["n_inside_corridor_polygon"] == cov["n_in5_in4_miss_points"],
        "n_in5_in4_miss_points": cov["n_in5_in4_miss_points"],
        "n_inside_declared_bands": cov["n_inside_declared_bands"],
        "n_inside_corridor_polygon": cov["n_inside_corridor_polygon"],
        "disposition": "In5←In4 残余 = 按设计 In4 走廊空洞（非『待 L3 派生』）；CO-106 的 region_scoped_indeterminate 由本件声明叠加为 by-design（改判属后续 rev）"}

    teeth["row_absent_detector"] = (not row_present(["容量总和 >= 需求"])) and row_present(items)
    teeth["ch2_keyword_floor"] = all(k in " ".join(items) for k in CH2_KEYS)
    teeth["teeth_ok"] = all(bool(v) for v in teeth.values())
    rec = {"artifact": "m13_v57_co110_l2_coverage_closure", "schema": 1, "revision": "CO-110.1",
           "nature": "L2 自裁施加：参考平面判据入 CO-87 矩阵 + CO-106 D 读径修复 + In4 走廊空洞按设计定案（R5'）",
           "inputs": {"co87_record": s16(CO87), "co106_record": s16(CO106), "co109_record": s16(CO109),
                      "spec_rev13": s16(SPEC13), "board": s16(BOARD)},
           "changes": {"tools": ["p3_v57_co87_l2_acceptance_coverage.py", "p3_v57_co106_reference_plane_gate.py"],
                       "spec_changed": False, "board_changed": False, "rebuild_required": False},
           "checks": checks, "teeth": teeth,
           "verdict": "L2_CLOSED_NO_SPEC_CHANGE_NO_REBASELINE" if all(v["ok"] for v in checks.values()) and teeth["teeth_ok"] else "FAIL",
           "non_claims": ["零 SPEC/板/阈值/冻结源改动 ⇒ 不重基线（先例 CO-105）",
                          "不改 CO-106 分类字节（by-design 叠加声明由本件承载；改判属后续 rev）",
                          "不做 SI/阻抗数值计算（终判 = SI9000 + 板厂券）"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-110 verdict=%s | checks=%s | teeth=%s" % (rec["verdict"], {k: v["ok"] for k, v in checks.items()}, teeth["teeth_ok"]))
    print("  record sha16:", s16(Path(a.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
