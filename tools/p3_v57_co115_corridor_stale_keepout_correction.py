#!/usr/bin/env python3
"""CO-115：【L2 自裁 · 事实更正】In4 走廊空洞 = **失效 keepout 的残留**（待 L3 派生），**非**「按设计」。

更正对象：CO-109（`R2 = 按设计`）/ CO-110 / CO-113（rev-14 `in4_corridor_void_by_design_v1`）对「走廊空洞 = 按设计」的判定。

机判依据（全部来自声明源）：
  1. `pd.zone_defs.retired_in4_keepout_band_6l.band = x[50.0, 88.17], y[43.44, 65.1]`（CO-95 退役，premise voided by CO-74）
  2. 走廊两侧边界 = 该 keepout 的 **0.2mm 内缩**：`MCU_VDD_WEST.e = 49.8 = 50.0 - 0.2`；`P3V3_EAST.w = 88.37 = 88.17 + 0.2`
     （keepout premise =「铜皮东西两区**禁止跨越此带**（两侧各留 POWER clearance 0.2）」）
  3. CO-95 `effect` 明文 =「退役后 **In4 铜可在原 band 区内按网归属铺设**（仍须满足 plane_reachability_requirement）」
  ⇒ 走廊空洞 = **约束退役后的边界未随动的残留** ⇒ **属待 L3 派生**（handoff §4-2 原判正确），非永久按设计。

推论（本件同时更正）：
  - CO-111 的 In5 PCIe 40.1% 暴露 **可修**（把 In4 铜按网归属铺入 band），**非** 永久缺口；
  - 该铺铜的**区域归属拆分**（band 内 MCU_VDD / P3V3_AUX / P3V3 界面）= **区域/电源域划分 = L1** ⇒ 须 owner（与既有 L1 项「P3V3_AUX 西区归属」同族）。
只读；不改 SPEC/板/阈值/冻结源（SPEC 更正须后续 rev-15 + 全链重基线）。
CLI: python3 tools/p3_v57_co115_corridor_stale_keepout_correction.py
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC14 = L3 / "SPEC_k2_v4.spec-rev-14.json"
OUT = STEP2 / "m13_v57_co115_corridor_stale_keepout_correction.json"
TOL = 1e-6


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    spec = json.loads(SPEC14.read_text())
    zd = spec["pd"]["zone_defs"]
    keep = zd["retired_in4_keepout_band_6l"]
    band = keep["band"]
    e = float(spec["constraints"]["edge_copper_min"])
    zones = {z["zone"]: z for z in zd["power_zones"] if z.get("polygon")}
    west_e = max(p[0] for p in zones["MCU_VDD_WEST"]["polygon"])
    east_w = min(p[0] for p in zones["P3V3_EAST"]["polygon"])
    checks, teeth = {}, {}
    checks["A_corridor_is_keepout_inset"] = {
        "ok": (abs(west_e - (band["x"][0] - 0.2)) < TOL) and (abs(east_w - (band["x"][1] + 0.2)) < TOL),
        "keepout_band_x": band["x"], "keepout_band_y": band["y"],
        "MCU_VDD_WEST_east_edge": west_e, "P3V3_EAST_west_edge": east_w,
        "rule": "两侧各留 POWER clearance 0.2", "corridor_x": [west_e, east_w],
        "note": "走廊空洞的两侧边界 = 退役 keepout 的 0.2mm 内缩（算术吻合）⇒ 空洞是 keepout 残留，非独立设计意图"}
    checks["B_keepout_retired_authorizes_pour"] = {
        "ok": keep.get("retired_by") == "CO-95" and "按网归属铺设" in str(keep.get("effect", "")),
        "retired_by": keep.get("retired_by"), "premise_voided_by": keep.get("premise_voided_by"),
        "premise": keep.get("premise"), "void_reason": keep.get("void_reason"), "effect": keep.get("effect"),
        "note": "CO-95 明示『退役后 In4 铜可在原 band 区内按网归属铺设』⇒ band 内铺铜被授权"}
    checks["C_correction_by_design_void"] = {
        "ok": (abs(west_e - (band["x"][0] - 0.2)) < TOL) and ("按网归属铺设" in str(keep.get("effect", ""))),
        "correction": "CO-109 `R2=按设计` / CO-110 / CO-113 rev-14 `in4_corridor_void_by_design_v1` **更正**："
                      "走廊空洞 = 失效 keepout（CO-95 退役）的边界残留 ⇒ **待 L3 派生**（handoff §4-2 原判正确）。",
        "consequences": ["CO-111 的 In5 PCIe 40.1% 暴露 **可修**（按网归属把 In4 铜铺入 band）",
                         "CO-113 rev-14 的 `in4_corridor_void_by_design_v1` 键需后续 rev-15 更正",
                         "CO-98 `declared_pending_l3`（8 桥区 target + 6 band 义务）语义回到『待派生』"],
        "requires": "后续 rev-15（SPEC 更正）+ 全链重基线 + 换会话复评"}
    checks["D_ownership_split_is_L1"] = {
        "ok": True,
        "decision": "band x∈(50.0,88.17) 内铺铜的**区域归属拆分**（MCU_VDD / P3V3_AUX / P3V3 界面）= **区域/电源域划分 = L1** ⇒ 须 owner；"
                    "与既有 L1 项『P3V3_AUX 西区归属』同族（CO-98 ruling_pending_l1=6 的 C90.1/R1.2/U1.15 即此）。",
        "in_band_features": {"P3V3_U6_balls_x": [85.4, 88.28], "MCU_VDD_R29_R34_x": [50.2, 57.55],
                             "P3V3_AUX_vias_x": [26.5, 58.9]},
        "note": "界面未定 ⇒ 无法在 L2 内唯一确定铺铜几何（不得以假设值代填界面）"}
    teeth = {"inset_arithmetic_control": (abs((band["x"][0] - 0.2) - 49.8) < TOL and abs((band["x"][1] + 0.2) - 88.37) < TOL),
             "keepout_present": bool(band.get("x") and band.get("y"))}
    teeth["teeth_ok"] = all(bool(v) for v in teeth.values())
    hard = all(v["ok"] for v in checks.values()) and teeth["teeth_ok"]
    rec = {"artifact": "m13_v57_co115_corridor_stale_keepout_correction", "schema": 1, "revision": "CO-115.1",
           "nature": "L2 事实更正：In4 走廊空洞 = 失效 keepout 残留（待 L3 派生），非按设计",
           "inputs": {"spec_rev14": s16(SPEC14)},
           "corrects": ["CO-109 R2", "CO-110", "CO-113 rev-14 in4_corridor_void_by_design_v1"],
           "checks": checks, "teeth": teeth,
           "verdict": "L2_CORRECTION_STALE_KEEPOUT_PENDING_L3_L1_OWNERSHIP" if hard else "FAIL",
           "escalation": {"level": "OWNER", "one_line": "band x∈(50.0,88.17) 内 In4 铺铜的**区域归属界面**（MCU_VDD/P3V3_AUX/P3V3）如何划分？（定则 L2 可派生铺铜并消除 In5 40.1% 参考缺失）"},
           "non_claims": ["只读；不改 SPEC/板/阈值/冻结源", "本件不做铺铜几何派生（界面属 L1）", "不代填归属假设值"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-115 verdict=%s | keepout_x=%s | west_e=%s east_w=%s | checks=%s | teeth=%s" % (
        rec["verdict"], band["x"], west_e, east_w, {k: v["ok"] for k, v in checks.items()}, teeth["teeth_ok"]))
    print("  record sha16:", s16(Path(a.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
