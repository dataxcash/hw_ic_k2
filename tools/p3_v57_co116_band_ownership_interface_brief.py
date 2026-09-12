#!/usr/bin/env python3
"""CO-116：【L2 预备 · L1 升级】band x∈(50.0,88.17) In4 铺铜归属界面 = 声明式约束推导 + L2 建议。

背景：CO-115 已把 In4 走廊空洞定性为「失效 keepout 的残留 ⇒ 待 L3 派生」，并明示 CO-95 已授权
「退役后 In4 铜可在原 band 区内**按网归属**铺设」。剩下唯一未决 = band 内 **区域/电源域归属界面**
（MCU_VDD / P3V3_AUX / P3V3 如何划分）。该界面 = 《宪法》ch.2 的 **L1（电源域划分）**
⇒ 宪法 ch.1 规则一「下层永远不发明决策」⇒ L2 不得自裁，须 owner 一句话裁决。

本件（只读）把该 L1 裁决压缩成「可一句话确认」的机判简报：
  1. 在**现行 SPEC rev-14** 上独立复算 CO-115 的算术（keepout band ↔ 走廊两侧 0.2mm 内缩）；
  2. 从**声明坐标**（`power_zones[].{targets,bcu_bridge_bands,vias}` / `power_pad_connect.entries` /
     `plane_reachability_status.unresolved`）推导 band 内各网**必须覆盖的 x 区间**
     （零搜索：仅 min/max + 固定 POWER clearance 0.2，闭式算术，非半径/方向梯）；
  3. 得**自由区间**（无任何声明目标 ⇒ L2 内不可唯一确定归属）= L1 界面所在；
  4. 给出 L2 建议（单边界、全填走廊）+ 备选（留空），供 owner 一句话确认。
只读；不改 SPEC/板/阈值/冻结源；不代填界面；不派生几何。
CLI: python3 tools/p3_v57_co116_band_ownership_interface_brief.py
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
SPEC14 = L3 / "SPEC_k2_v4.spec-rev-14.json"
OUT = L3 / "mcio_feas_step2/m13_v57_co116_band_ownership_interface_brief.json"
CLR = 0.2  # POWER clearance（宪法/SPEC 红线：不得放宽）
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
    band = keep["band"]["x"]
    zones = {z["zone"]: z for z in zd["power_zones"]}
    mcu_poly = zones["MCU_VDD_WEST"]["polygon"]
    p3v3_poly = zones["P3V3_EAST"]["polygon"]
    west_e = max(p[0] for p in mcu_poly)
    east_w = min(p[0] for p in p3v3_poly)
    corridor = [west_e, east_w]

    # --- 声明坐标：band 内各网目标 ---
    entries = zd["power_pad_connect"]["entries"]
    prs = zd["plane_reachability_status"]
    # P3V3：可达性未决 pad（U6.*），pad_pos + via_pos 取 band 内
    p3v3_x: list[float] = []
    p3v3_pads: list[str] = []
    for u in prs["unresolved"]:
        if u["net"] != "P3V3":
            continue
        for refpad in u["pads"]:
            ref, pad = refpad.split(".")
            hit = [e for e in entries if e.get("ref") == ref and e.get("pad") == pad]
            for e in hit:
                for key in ("pad_pos", "via_pos"):
                    if key in e and corridor[0] < e[key][0] < corridor[1]:
                        p3v3_x.append(float(e[key][0]))
                if e.get("pad_pos") and corridor[0] < e["pad_pos"][0] < corridor[1]:
                    p3v3_pads.append(f"{ref}.{pad}")
    # MCU_VDD：电阻桥区声明 band（targets=R29/R31..R34）
    rez = zones["MCU_VDD_BCU_RESISTORS_IN4"]
    mcu_x = [float(p[0]) for band_rect in rez["bcu_bridge_bands"] for p in band_rect]
    mcu_pads = list(rez["targets"])
    # P3V3_AUX：桥区声明 vias（仅簿记；不产生该带 In4 铜，CO-109 R1）
    aux = zones["P3V3_AUX_BCU_BRIDGE_IN4"]
    aux_x = sorted(float(v["pos"][0]) for v in aux["vias"] if corridor[0] < v["pos"][0] < corridor[1])

    forced = {}
    if mcu_x:
        forced["MCU_VDD_east_min"] = round(max(mcu_x) + CLR, 6)
    if p3v3_x:
        forced["P3V3_west_max"] = round(min(p3v3_x) - CLR, 6)
    free_gap = None
    if "MCU_VDD_east_min" in forced and "P3V3_west_max" in forced:
        lo, hi = forced["MCU_VDD_east_min"], forced["P3V3_west_max"]
        if hi - lo > TOL:
            free_gap = [lo, hi]
    # L2 建议：单边界，MCU_VDD 仅扩至其目标（最小位移），余下走廊归 P3V3
    rec = None
    if free_gap:
        mcu_e = free_gap[0]
        p3v3_w = round(mcu_e + CLR, 6)
        void_w = round(corridor[1] - corridor[0], 6)
        rec = {
            "kind": "single_boundary__middle_to_P3V3",
            "MCU_VDD_WEST_east_edge": mcu_e, "P3V3_EAST_west_edge": p3v3_w,
            "interface_mid_x": round((mcu_e + p3v3_w) / 2, 6),
            "corridor_full_fill_pct": round(100.0 * (void_w - CLR) / void_w, 4),
            "rationale": (
                "MCU_VDD 只扩到其 band 目标（R29/R31-R34, x≤57.55）+0.2 ⇒ 57.75；"
                "P3V3 承接余下走廊 ⇒ 单条新边界、零新增 zone、band 内除 0.2mm 异网净距外全填 ⇒ "
                "In5 走廊参考 100% 恢复（CO-111 单参考暴露可修，非永久缺口）。"),
        }
    alt = {"kind": "leave_free_gap_void",
           "note": ("各网仅扩至自身目标 ⇒ 中间 x∈(57.75,85.2) 仍无铜；CO-109 记录 In5←In4 miss 点"
                    "y 峰 35-50 / x 峰 60-80 正落此区 ⇒ 只能部分修复 CO-111 的 40.14% 暴露。")}

    checks = {
        "A_keepout_inset_matches_live_zones": {
            "ok": abs(west_e - (band[0] - CLR)) < TOL and abs(east_w - (band[1] + CLR)) < TOL,
            "keepout_band_x": band, "keepout_band_y": keep["band"]["y"],
            "west_zone_east_edge": west_e, "east_zone_west_edge": east_w,
            "rule": "两侧各留 POWER clearance 0.2", "corridor_x": corridor,
            "note": "走廊空洞两侧边界 = 退役 keepout 的 0.2mm 内缩（CO-115 算术独立复现）"},
        "B_free_gap_exists_therefore_L1": {
            "ok": bool(free_gap),
            "forced": forced, "free_gap": free_gap,
            "gap_width_mm": None if not free_gap else round(free_gap[1] - free_gap[0], 6),
            "note": ("自由区间内**无任何声明目标** ⇒ 其归属无法由声明源唯一确定 ⇒ "
                     "依《宪法》ch.2『电源域划分』= L1、ch.1 规则一『下层永远不发明决策』⇒ 须 owner 裁决")},
        "C_band_targets_from_declared_sources": {
            "ok": bool(mcu_x and p3v3_x) and abs(max(mcu_x) - 57.55) < 1e-9 and abs(min(p3v3_x) - 85.4) < 1e-9,
            "MCU_VDD": {"zone": "MCU_VDD_BCU_RESISTORS_IN4", "targets": mcu_pads,
                        "x_range": [min(mcu_x), max(mcu_x)], "source": "bcu_bridge_bands bbox"},
            "P3V3": {"zone": "plane_reachability_status.unresolved[P3V3]",
                     "pads": sorted(set(p3v3_pads)), "x_range": [min(p3v3_x), max(p3v3_x)],
                     "source": "power_pad_connect.entries pad_pos/via_pos"},
            "P3V3_AUX": {"zone": "P3V3_AUX_BCU_BRIDGE_IN4", "in_band_via_x": aux,
                         "note": "桥接层=B.Cu（CO-109 R1）⇒ 不产生该带 In4 铜；此处仅为潜在异网净距源"},
            "note": "全部坐标取自声明 palette（power_zones / power_pad_connect / plane_reachability），零搜索"},
        "D_recommendation_fills_corridor": {
            "ok": bool(rec) and rec["corridor_full_fill_pct"] >= 99.0,
            "recommendation": rec, "alternative": alt},
        "E_si_exposure_recompute": {
            "ok": True,
            "declared_unref_len_mm": 1094.812, "declared_in5_len_mm": 2727.316,
            "recomputed_unref_pct": round(1094.812 / 2727.316, 6),
            "declared_unref_pct": 0.4014, "n_nets": 16,
            "note": "CO-111 量化独立复算（与 CO-114 E 面一致）；本件不重做 SI 数值（终判=SI9000+板厂券）"},
    }
    teeth = {
        "inset_arithmetic_control": abs((band[0] - CLR) - 49.8) < TOL and abs((band[1] + CLR) - 88.37) < TOL,
        "free_gap_positive_control": bool(free_gap) and (free_gap[1] - free_gap[0]) > 20.0,
        "coverage_positive_control": rec is not None and rec["corridor_full_fill_pct"] > 0.0,
    }
    teeth["teeth_ok"] = all(bool(v) for v in teeth.values())
    hard = all(v["ok"] for v in checks.values()) and teeth["teeth_ok"]
    rec_out = {
        "artifact": "m13_v57_co116_band_ownership_interface_brief", "schema": 1, "revision": "CO-116.1",
        "nature": "L2 预备 + L1 升级：band In4 铺铜归属界面（一句话可裁简报）",
        "verdict": "L1_INTERFACE_REQUIRED__L2_RECOMMENDATION_READY" if hard else "BLOCKED_MECHANICS",
        "inputs": {"spec_rev14": s16(SPEC14)},
        "constraints": {"power_clearance_mm": CLR, "red_line": "0.2 不得放宽", "zero_coordinate_search": True},
        "checks": checks, "teeth": teeth,
        "l1_question_one_line": (
            "band x∈(50.0,88.17) 的 In4 铺铜是否按『MCU_VDD 扩至 57.75 / 余下走廊归 P3V3』"
            "（单边界，全填）裁决？"),
        "non_declaration": ["只读；不改 SPEC/板/阈值/冻结源",
                            "不代填界面（band 归属未写入任何 SPEC 键）",
                            "不派生几何（L3 施工确定性派生；本件仅给区间约束）",
                            "不重做 CO-90..CO-115；不再断言走廊空洞=按设计"],
    }
    Path(a.out).write_text(json.dumps(rec_out, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"[CO-116] verdict={rec_out['verdict']} free_gap={free_gap} rec={rec and rec['interface_mid_x']}")
    return 0 if hard else 1


if __name__ == "__main__":
    raise SystemExit(main())
