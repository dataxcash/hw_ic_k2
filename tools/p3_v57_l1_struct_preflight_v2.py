#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 含旧板身份字面量 ['f6273de6'] ⇒ **不可重放**（重跑会静默换板，禁默认重跑）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""L1 结构可行性预检 v2 —— 整改通知 #02（L1/L2 定层纠正，宪法 Ch.3 §5 / Ch.9 row2-3）。

只做**确定性结构数学**（一次算对，零搜索/零枚举，O(n)）：
  P1 走廊宏观闭合（横截需求 vs 可用带高 / x 净跨）
  P2 焊盘墙穿透（连接器 pin field + 芯片逃逸区：行内 pad 间隙 vs 单道 lane 需求）
  P3 pin 逃逸可达性（需换层 pad 数 / 内部信号层数 / In2 逃逸带预算）
  P4 强条内嵌核查（完整净距套件 + 对内等长是否进入 L2 包络）—— #02 根因
输出 verdict ∈ {PREFLIGHT_FAIL, PREFLIGHT_PASS}；FAIL 不得进入 L3，须走变更单回 L1/L2。

数据源（冻结）：SPEC_k2_v4.json / m13_v57_s1_page_manifest.json / k2_v4.kicad_pcb / drc_rules.json
CLI: --out PATH [--quiet]
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from collections import defaultdict
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
S2 = L3 / "mcio_feas_step2"
F = {
    "spec": L3 / "SPEC_k2_v4.json",
    "manifest": S2 / "m13_v57_s1_page_manifest.json",
    "pcb": K2 / "k2_v4.kicad_pcb",
    "rules": K2 / "_shared" / "eda_core" / "drc_rules.json",
}
EXPECT = {  # 冻结四源 SHA-256 前缀（drift -> 非零退出）
    "spec": "0bd52ed48e720b8c", "manifest": "a8ef3ea8ecff99d7",
    "pcb": "f6273de613f43d05", "rules": "0a459839e15960b8",
}


def sha16(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def r(x, n=4):
    return round(float(x), n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    drift = {k: {"expected": EXPECT[k], "actual": sha16(p)} for k, p in F.items()}
    if any(v["expected"] != v["actual"] for v in drift.values()):
        print("FROZEN_DRIFT", json.dumps(drift)); return 2
    spec = json.loads(F["spec"].read_text())
    man = json.loads(F["manifest"].read_text())
    pc = spec["net_classes"]["PCIe85"]
    w, clr = pc["width"], pc["clearance"]
    pgap, pwidth = pc["diff_pair"]["p_gap"], pc["diff_pair"]["p_width"]
    via_r = spec["vias"]["std"]["outer"] / 2
    per_ball = spec["components"]["redriver"]["DS320PR1601"]["bga_escape"]["per_ball"]
    ipair = per_ball["inter_pair_spacing"]
    pad_mm = per_ball["pad_mm"]
    pad_pitch_mm = per_ball["pair_pitch_mm"]
    skew_max = pc["intra_pair_skew_mm"]
    # 完整净距套件（L5 暴露；SPEC/drc_rules 可推出，非新口径）
    suite = {
        "track_track_center_mm": r(w + clr),
        "via_track_center_mm": r(via_r + clr + w / 2),
        "via_via_center_mm": r(2 * via_r + clr),
    }
    lane_needed = r(w + 2 * clr)  # 行内穿透单道 lane 需求
    pair_copper = r(2 * w + pgap)
    pair_pitch = r(ipair)  # 对中心距 = 1.46（L1 硬约束 3；0.585 铜跨 + 0.875 铜边净空）

    # ---- 端点几何（manifest 实测）----
    chip = defaultdict(list); conn = defaultdict(list)
    for p in man["pages"]:
        for pol, d in p.get("anchors", {}).get("chip", {}).items():
            chip[p["page_id"]].append((pol, tuple(d["pad_global"])))
        for pol, d in p.get("anchors", {}).get("conn", {}).items():
            conn[d["ref"]].append((pol, tuple(d["pad_global"]), d.get("pad_num")))
    chip_pts = [pt for v in chip.values() for _, pt in v]

    def wall_gaps(pts):
        xs = sorted({r(x[0]) for x in pts}); ys = sorted({r(x[1]) for x in pts})
        pts_s = sorted(set((r(x[0]), r(x[1])) for x in pts))
        mn = min((abs(q0[0] - q1[0]) ** 2 + abs(q0[1] - q1[1]) ** 2) ** .5
                 for q0, q1 in itertools.combinations(pts_s, 2))
        return xs, ys, r(mn)

    # ---- P1 走廊宏观闭合 ----
    P1 = {}
    for c in spec["corridors"]:
        n = c["pairs"]; bands = c["bands"]
        nb = max(b["pairs"] for b in bands)
        P1[c["id"]] = {
            "x_range": c["x_range"], "x_net_span_mm": r(c["x_range"][1] - c["x_range"][0]),
            "pairs_total": n, "pairs_per_band": nb,
            "band_span_needed_mm": r((nb - 1) * pair_pitch + pair_copper),
            "total_span_if_one_plane_mm": r((n - 1) * pair_pitch + pair_copper),
        }
    P1["available"] = {"usable_y_span_mm": 45.4, "n_wing_mm": 16.2, "s_wing_mm": 20.8}
    P1["closure"] = all(v["band_span_needed_mm"] <= 16.2 for k, v in P1.items() if k != "available")

    # ---- P2 焊盘墙穿透 ----
    P2 = {"lane_needed_mm": lane_needed, "walls": {}}
    cxs, cys, cmn = wall_gaps(chip_pts)
    P2["walls"]["chip_field(64 pads)"] = {
        "min_ctr_dist_mm": cmn, "pad_mm": pad_mm, "min_pad_gap_mm": r(cmn - pad_mm),
        "penetrable": r(cmn - pad_mm) >= lane_needed,
        "pitch_zone_mm": 0.4, "note": "SPEC escape_transition_zone pitch=0.4",
    }
    for ref, v in conn.items():
        pts = [pt for _, pt, _ in v]
        xs, ys, mn = wall_gaps(pts)
        P2["walls"][f"connector {ref}"] = {
            "n_pads": len(v), "min_ctr_dist_mm": mn, "pad_mm": pad_mm,
        "min_pad_gap_mm": r(mn - pad_mm),
            "penetrable": r(mn - pad_mm) >= lane_needed,
        }
    P2["penetrable_wall_count"] = sum(1 for x in P2["walls"].values() if x["penetrable"])
    P2["all_walls_impenetrable"] = P2["penetrable_wall_count"] == 0

    # ---- P3 pin 逃逸可达性 ----
    # 需换层 pad（内环/非外环）：manifest 芯片球全在内区 -> 全部经 In2 逃逸；连接器双列墙行内不可穿
    n_chip_pads = len(chip_pts)
    n_conn_pads = sum(len(v) for v in conn.values())
    n_pairs = man["tally"]["data_input"] + man["tally"]["data_out_j2"] + man["tally"]["data_out_mcio"]
    stack_6l = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]
    stack_8l = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
    inner_6 = [x for x in stack_6l if "In" in x and "POWER" not in x and "GND" not in x]
    P3 = {
        "chip_pads": n_chip_pads, "conn_pads": n_conn_pads, "data_pairs": n_pairs,
        "via_per_line_max": spec["vias"]["high_speed"]["max_per_line"],
        "internal_signal_layers_6L": ["In2.Cu"],
        "internal_signal_layers_8L": ["In2.Cu", "In6.Cu"],
        "via_escape_budget": {
            "chip_side_vias": n_chip_pads,  # 行内不可穿 -> 每球至少 1 via
            "conn_side_inner_col_vias": 0,  # 外列可 F.Cu 外逃；内列需换层（保守记 0，P2 已给"墙不可穿"）
            "note": "P2=0 可穿透 -> 高速球一律需层转移；6L 只有 1 个内部信号层承接全部逃逸",
        },
        "in2_escape_band": {"n_wing_mm": 16.2, "s_wing_mm": 20.8,
                            "pairs_capacity": r((16.2 + 20.8) / pair_pitch)},
    }

    # ---- P4 强条内嵌核查（L2 包络）----
    l2_lines = (L3 / ".." / "L2" / "frozen" / "L2_STRUCTURE_v2.0.md")
    l2_txt = l2_lines.read_text(errors="ignore") if l2_lines.exists() else ""
    suite_in_l2 = all(k in l2_txt for k in ("0.38", "0.4525", "0.525"))
    len_in_l2 = ("等长" in l2_txt) or ("skew" in l2_txt.lower())
    P4 = {
        "l2_structure_doc": str(l2_lines.relative_to(K2)),
        "full_clearance_suite_in_L2": suite_in_l2,
        "length_match_declared_in_L2": len_in_l2,
        "length_match_machine_gate_in_L2": False,  # 文本声明 (<0.15mm) 但无机器谓词；L3 口径未含
        "verdict": "FAIL: L2 包络缺完整净距套件 (0.38/0.4525/0.525)；对内等长仅文本声明未机检"
        if not (suite_in_l2 and len_in_l2) else "embedded",
    }

    # 语义：P1 闭合，但 P2 全墙不可穿 => 高速 pad 一律需层转移；6L 内部信号层仅 1 个
    # 承接全部逃逸/穿越 => 资源不足；P4=强条（完整净距+等长）未进 L2 包络 => 原"闭合✓"失效。
    verdict = "PREFLIGHT_FAIL" if (
        (not P1["closure"])
        or len(P3["internal_signal_layers_6L"]) < 2
        or P4["verdict"].startswith("L2 envelope does NOT")
    ) else "PREFLIGHT_PASS"

    out = {
        "artifact": "m13_v57_l1_struct_preflight_v2", "revision": "L1-PF.2", "schema": 1,
        "date": "2026-09-11",
        "authority": "LAYOUT_CONSTITUTION Ch.3 §5 + Ch.9 row2/3; rectification #02 (定层纠正)",
        "inputs_sha": {k: v["actual"] for k, v in drift.items()},
        "hard_gates": {"jlc_limits": {"edge_copper_min_mm": spec["constraints"]["edge_copper_min"]},
                       "clearance_suite": suite, "length_match_intra_pair_skew_mm": skew_max,
                       "via_per_line_max": spec["vias"]["high_speed"]["max_per_line"]},
        "constants": {"w_mm": w, "clr_mm": clr, "via_outer_mm": 2 * via_r,
                      "pair_copper_mm": pair_copper, "pair_pitch_mm": pair_pitch, "lane_needed_mm": lane_needed},
        "P1_corridor_macro_closure": P1,
        "P2_pad_wall_penetration": P2,
        "P3_pin_escape_reachability": P3,
        "P4_strong_gate_embedding": P4,
        "verdict": verdict,
        "escalation": "变更单 CO-02 -> L2 结构方案竞标（叠层分配/走廊矩阵/过孔策略/等长窗口）",
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    if not a.quiet:
        print(json.dumps({k: out[k] for k in ("verdict", "P1_corridor_macro_closure", "P2_pad_wall_penetration", "P4_strong_gate_embedding")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
