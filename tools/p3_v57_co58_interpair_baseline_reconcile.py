#!/usr/bin/env python3
"""CO-58：对间净空**口径对账**（更正 CO-57 的过度升档；只读）。

背景：CO-57 把「交付实距 vs R3-2 0.875」判为 L1 冲突。复核发现 L1/L2/学习闸另有一档**冻结口径**：
  - `L1_TOPOLOGY_v2.0.md` 硬约束 2：「…**冻结轨距仍 1.08（实际排轨居中值）**。口径统一 = 1.46（capacity 口径）」
  - `L2_STRUCTURE_v2.0.md`：「capacity_audit.inter_pair_spacing 注入 1.46，勿用 drc_rules.json 0.875；**冻结轨距 1.08 为实际排轨居中值**」
  - `mcio_learning_gate.md` §4.2：「模板参数（**生产过/结构冻结**）：track_pitch **1.08** / pair_half_pitch 0.19 / clearance 0.175 …」
⇒ 「0.875」在 v2.0 被明确定义为**铜边净空口径**（用于 capacity 换算 1.46），而**实排轨距冻结值 = 1.08**（其铜边净空 = 1.08 − 0.585 = 0.495 < 0.875）。
本工具把各口径与实际交付并排换算，判定"交付是否偏离某档口径"，并给出收窄后的待裁问题。零几何/阈值改动。
输出：m13_v57_co58_interpair_baseline_reconcile.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-4.json"
AUDIT = STEP2 / "m13_v57_co54_spec_delivery_audit.json"
OUT = STEP2 / "m13_v57_co58_interpair_baseline_reconcile.json"

W_LEGACY, GAP_LEGACY = 0.205, 0.175           # L1 v2.0 推导 1.46 时采用
SPAN_LEGACY = round(2 * W_LEGACY + GAP_LEGACY, 4)   # 0.585
PITCH_CAPACITY = 1.46                          # v22「口径统一」
EDGE_RULE_R3_2 = 0.875                         # v1.1 R3-2 强条（铜边净空）
PITCH_FROZEN = 1.08                            # v2.0 冻结轨距（实际排轨居中值；生产过模板）


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    w = spec["impedance"]["per_layer"]["F.Cu"]["w_mm"]
    centers = audit["delivered"]["intra_pair"]["per_pair_min_center_mm_unique"]
    span_now = round(max(centers) if len(centers) == 1 else centers[0] + w, 4)
    span_now = round(centers[0] + w, 4) if len(centers) == 1 else round(2 * w + max(
        float(k) - w for k in audit["delivered"]["intra_pair"]["per_layer_values_mm_counts"].get("In2.Cu", {"0.5": 1})), 4)
    pitch_delivered = sorted({p for b in audit["corridor_pitch"]["spec_bands"]
                              if b.get("pairs") == 8 for p in b["tracks_y_pitch_mm"]})
    # 芯片侧 In6 长平行带：交错排布（UP2_N 与 UP4_P 相邻）⇒ 对中心距 = 最近跨对中心距 + 对内中心距
    chip_pair_pitch = round(audit["delivered"]["inter_pair"]["min_center_mm"] + centers[0], 4)
    rows = [
        {"id": "R3-2 强条(v1.1)", "pitch_mm": None, "span_mm": SPAN_LEGACY,
         "edge_mm": EDGE_RULE_R3_2, "source": "L1_TOPOLOGY_v1.0.md 硬约束 3（2026-08-15 强条）", "kind": "requirement"},
        {"id": "v22 容量口径", "pitch_mm": PITCH_CAPACITY, "span_mm": SPAN_LEGACY,
         "edge_mm": round(PITCH_CAPACITY - SPAN_LEGACY, 4), "source": "L1_TOPOLOGY_v2.0.md 硬约束 2（用户裁决 v22）", "kind": "capacity"},
        {"id": "冻结轨距(v2.0/模板)", "pitch_mm": PITCH_FROZEN, "span_mm": SPAN_LEGACY,
         "edge_mm": round(PITCH_FROZEN - SPAN_LEGACY, 4),
         "source": "L1_TOPOLOGY_v2.0.md 硬约束 2 + L2_STRUCTURE_v2.0.md:145 + mcio_learning_gate.md §4.2（生产过模板）",
         "kind": "frozen_as_built"},
        {"id": "交付·走廊", "pitch_mm": pitch_delivered[0] if pitch_delivered else None, "span_mm": span_now,
         "edge_mm": round(pitch_delivered[0] - span_now, 4) if pitch_delivered else None,
         "source": "L4 construction 实测（CO-54 audit）", "kind": "delivered"},
        {"id": "交付·芯片侧 In6 长平行带", "pitch_mm": chip_pair_pitch, "span_mm": span_now,
         "edge_mm": round(chip_pair_pitch - span_now, 4),
         "source": "L4 construction 实测（CO-54 audit worst：PCIE_UP2_N‖PCIE_UP4_P，29.1mm）", "kind": "delivered"},
    ]
    frozen_edge = round(PITCH_FROZEN - SPAN_LEGACY, 4)
    corridor_edge = rows[3]["edge_mm"]
    reconcile = {
        "corridor_equals_frozen_edge": abs(corridor_edge - frozen_edge) < 1e-9,
        "frozen_edge_mm": frozen_edge,
        "corridor_matches": "与冻结口径同值（0.495）⇒ 走廊**不构成对冻结口径的偏离**（轨距 +0.12 与铜跨 +0.12 相抵）",
        "r3_2_realized_by_frozen": False,
        "r3_2_note": "0.875 未被 v2.0 冻结口径满足（0.495）⇒ R3-2 的『realized 0.875』时效/范围属 L1 口径问题，非交付单方面违约",
        "chip_side_below_frozen": round(frozen_edge - rows[4]["edge_mm"], 4),
    }
    rec = {
        "artifact": "m13_v57_co58_interpair_baseline_reconcile", "schema": 1, "revision": "CO-58.1",
        "nature": "口径对账（只读；更正 CO-57 的过度升档表述；零几何/阈值改动）",
        "supersedes_framing_of": "m13_v57_CO57_L1_escalation_interpair_clearance.md（事实保留；『交付违约』表述按本件更正）",
        "delivered_constants": {"w_mm": w, "intra_center_mm": centers, "span_now_mm": span_now,
                                "corridor_pitch_mm": pitch_delivered, "chip_side_pair_pitch_mm": chip_pair_pitch},
        "baselines": rows,
        "reconciliation": reconcile,
        "narrowed_owner_questions": [
            {"id": "Q1", "level": "L1", "question": "R3-2『对间铜边净空 ≥0.875』是 **realized 要求** 还是 **capacity 口径**？（v2.0 冻结轨距 1.08 ⇒ 实排 0.495，本身即不满足 0.875）",
             "if_realized": "走廊轨距需 ≥ span(0.705)+0.875 = **1.580**（芯片侧同理）⇒ W3..G7 全链重导（8×1.580=12.64 < N16.2/S20.8 ⇒ 几何可行）",
             "if_capacity_only": "以 v2.0 冻结口径 1.08（铜边 0.495）为准 ⇒ 走廊交付（0.495）已一致；仅芯片侧 In6 带（0.345，低于冻结 0.15）需 L2 重导至 ≥1.08"},
            {"id": "Q2", "level": "L2-ready（待 Q1 定标）", "question": "芯片侧 In6 长平行带 pair pitch 1.05（铜边 0.345）是否重导？",
             "note": "若 Q1=capacity_only ⇒ 目标 1.08（+0.03/对）即可对齐冻结口径；若 Q1=realized ⇒ 目标 1.580。**目标值取决于 Q1，故不预开 W3**。"},
        ],
        "conformance": "PENDING_L1_Q1（更正后：走廊=冻结口径一致；芯片侧低于冻结口径）",
        "gate_impact": "none（本件零改动；G4..G7 不变）",
    }
    a.out.write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(a.out.relative_to(K2)), "sha16": sha16(a.out),
                      "span_now": span_now, "corridor_edge": corridor_edge, "frozen_edge": frozen_edge,
                      "chip_edge": rows[4]["edge_mm"], "corridor_equals_frozen": reconcile["corridor_equals_frozen_edge"],
                      "Q1": "realized 0.875 vs capacity 口径 1.08"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
