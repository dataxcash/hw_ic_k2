#!/usr/bin/env python3
"""CO-57：L1 阈值 vs 交付几何 **冲突机判**（对间铜边净空 ≥0.875mm）。

阈值来源（**L1 冻结源，只读**）：
  - `pm_gate/artifacts/k2_v4/L1/frozen/L1_TOPOLOGY_v1.0.md` 硬约束 3：
    「对内等长 <0.15mm；**对间间距 ≥0.875mm（R3-2 3W 原则，2026-08-15 强条**；原 0.5 旧口径已提升）」
  - `.../L1_TOPOLOGY_v2.0.md` 硬约束 2（v22 用户裁决 2026-09-05）：
    「R3-2『0.875』= 对间铜边净空 → 对中心距 = 0.585(对铜跨) + 0.875 = **1.46mm** … 口径统一 = 1.46」
  ⇒ **该阈值/口径属 L1（owner 冻结）**，L2 不得自行放宽。

本工具只测量与换算：交付实距、L1 口径、按现行对内铜跨换算的所需中心距、以及走廊容量可行性。
零几何/阈值改动；不预判裁定。
输出：m13_v57_co57_l1_interpair_conflict.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L1 = K2 / "pm_gate/artifacts/k2_v4/L1/frozen"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-4.json"
AUDIT = STEP2 / "m13_v57_co54_spec_delivery_audit.json"
OUT = STEP2 / "m13_v57_co57_l1_interpair_conflict.json"

L1_REQ_EDGE = 0.875          # L1 硬约束（R3-2 3W / v22 裁决）
L1_LEGACY_SPAN = 0.585       # L1 v2.0 推导 1.46 时采用的对内铜跨（w 0.205 + gap 0.175）
L1_PITCH = 1.46
WING_ROOM_MM = {"N": 16.2, "S": 20.8}   # L2 v2.0 记载的翼内可用高度（L1 口径）


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))

    w = spec["impedance"]["per_layer"]["F.Cu"]["w_mm"]
    intra_centers = audit["delivered"]["intra_pair"]["per_pair_min_center_mm_unique"]
    spans = {f"center_{c}": round(c + w, 4) for c in intra_centers}
    span_now = spans[f"center_{intra_centers[0]}"] if f"center_{intra_centers[0]}" in spans else round(intra_centers[0] + w, 4)
    bands = audit["corridor_pitch"]["spec_bands"]
    pitch_delivered = sorted({p for b in bands if b.get("pairs") == 8 for p in b["tracks_y_pitch_mm"]})
    min_inter_center = audit["delivered"]["inter_pair"]["min_center_mm"]
    min_inter_edge = audit["delivered"]["inter_pair"]["min_edge_gap_mm"]

    pitch_needed = round(span_now + L1_REQ_EDGE, 4)
    edge_at_l1_pitch = round(L1_PITCH - span_now, 4)
    edge_at_delivered_pitch = round(pitch_delivered[0] - span_now, 4) if pitch_delivered else None
    cap = {k: {"pairs": 8, "need_mm": round(8 * pitch_needed, 3), "room_mm": v,
               "feasible": 8 * pitch_needed <= v} for k, v in WING_ROOM_MM.items()}

    rec = {
        "artifact": "m13_v57_co57_l1_interpair_conflict", "schema": 1, "revision": "CO-57.1",
        "nature": "L1 阈值 vs 交付几何冲突机判（只读；零几何/阈值改动）",
        "authority": "L1 冻结阈值（R3-2 3W / 用户裁决 v22）；本件=L2/L3 事实与升档材料",
        "l1_threshold": {"required_edge_clearance_mm": L1_REQ_EDGE,
                         "l1_stated_pitch_mm": L1_PITCH, "l1_legacy_span_mm": L1_LEGACY_SPAN,
                         "sources": [{"file": str((L1 / "L1_TOPOLOGY_v1.0.md").relative_to(K2)), "sha16": sha16(L1 / "L1_TOPOLOGY_v1.0.md"),
                                      "line": "硬约束 3：对间间距 ≥0.875mm（R3-2 3W 原则，2026-08-15 强条）"},
                                     {"file": str((L1 / "L1_TOPOLOGY_v2.0.md").relative_to(K2)), "sha16": sha16(L1 / "L1_TOPOLOGY_v2.0.md"),
                                      "line": "硬约束 2：R3-2『0.875』= 对间铜边净空 → 中心距 0.585+0.875 = 1.46mm；口径统一 = 1.46"}]},
        "delivered": {"intra_center_mm_unique": intra_centers, "w_mm": w, "intra_spans_mm": spans,
                      "span_dominant_mm": span_now,
                      "corridor_pitch_mm": pitch_delivered,
                      "min_inter_pair_center_mm": min_inter_center, "min_inter_pair_edge_mm": min_inter_edge},
        "conflict": {
            "C1_pitch": {"l1_pitch_mm": L1_PITCH, "delivered_pitch_mm": pitch_delivered,
                         "delta_mm": round(pitch_delivered[0] - L1_PITCH, 4) if pitch_delivered else None,
                         "verdict": "VIOLATION（交付走廊轨距 < L1 口径）"},
            "C2_span_breaks_formula": {"l1_formula_assumed_span_mm": L1_LEGACY_SPAN, "span_dominant_mm": span_now,
                                       "edge_at_l1_pitch_mm": edge_at_l1_pitch,
                                       "verdict": "VIOLATION（L2 的 CO-10 把对内铜跨 0.585→%.3f，使 L1 的 1.46 公式不再给出 0.875 净空）" % span_now},
            "C3_min_edge": {"required_mm": L1_REQ_EDGE, "delivered_min_mm": min_inter_edge,
                            "verdict": "VIOLATION（最紧处 = 内层长平行带）"},
            "pitch_needed_for_L1_mm": pitch_needed,
            "edge_at_delivered_pitch_mm": edge_at_delivered_pitch,
        },
        "remedy_capacity_check": cap,
        "options": [
            {"id": "A", "change": "重开 W3 走廊：轨距 ≥ %.3fmm（按现行对内铜跨 %.3f + 0.875）并按 L1 口径重导" % (pitch_needed, span_now),
             "owner_needed": True, "impact": "图纸/landing/板/记录全链重建（G4..G7）；触及 J2/J3/J4 落列与球行派生走廊行 ⇒ 拓扑相邻"},
            {"id": "B", "change": "回退对内铜跨至 0.585（L2 的 CO-10 决定反向）以恢复 1.46 口径",
             "owner_needed": False, "impact": "与前序 L2 裁定（CO-10 §7.2 via-track 净距 0.4525）冲突；同样触发 W3/L4/L5 重建"},
            {"id": "C", "change": "正式修订 L1 R3-2 阈值/口径（接受交付实距 0.345/0.495）",
             "owner_needed": True, "impact": "属 L1 阈值变更（铁律：阈值不得放宽 ⇒ 必须 owner 明示）"},
        ],
        "conformance": "L1_CONSTRAINT_VIOLATION_PENDING_OWNER",
        "gate_impact": "none（本件零改动；G4..G7 现状不变）",
        "request": "请 owner 裁定 A / B / C（L1；L2 不得自行放宽 R3-2）。",
    }
    a.out.write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(a.out.relative_to(K2)), "sha16": sha16(a.out),
                      "l1_req_edge": L1_REQ_EDGE, "delivered_min_edge": min_inter_edge,
                      "delivered_pitch": pitch_delivered, "span_now": span_now,
                      "pitch_needed_for_L1": pitch_needed, "wing_feasible": {k: v["feasible"] for k, v in cap.items()},
                      "verdict": rec["conformance"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
