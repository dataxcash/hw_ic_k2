#!/usr/bin/env python3
"""k2_p6_triage_hidden_failures_v1.py — 13 项「隐藏失败」的**只读根因 triage**（可复现）。

背景：`test_hs_route_model.py` 的 22 个 skip 解锁后 13 项失败（见
`k2/docs/K2-P6-SHADOW-VERIFICATION-BATCH2-20260920.md` §4）。本器只读统计
**走廊命名权威分歧**（SPEC 新 id ↔ alloc/模型/测试/判据 旧 id）并输出二分建议。

只读；输出确定性 JSON（无时间戳、键排序）。标准命令（容器根 ic_hw）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
      k2/tools/k2_p6_triage_hidden_failures_v1.py
"""
from __future__ import annotations

import argparse
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEF_OUT = os.path.join(REPO, "k2", "pm_gate", "artifacts", "k2_v4", "P6_execution",
                       "HIDDEN_FAILURES_TRIAGE_v1.json")
OLD = ("J2_TO_U", "U_TO_MCIO")
NEW = ("EAST_CHIP_TO_J2", "WEST_MCIO_TO_CHIP")
CARRIERS = {
    "engine_hs_route_model": "k2/_shared/eda_core/hs_route_model.py",
    "gate_check_l3_expects": "k2/_shared/pm_gate/check_l3.py",
    "tests": "k2/_shared/eda_core/tests/test_hs_route_model.py",
    "spec_plain": "k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json",
    "spec_rev52": "k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-52.json",
    "legacy_alloc_v2_pinned_by_tests": "k2/pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json",
}
# 13 项失败 → 家族（依 SHADOW_VERIFY 的 failed_tests；家族依失败形态判读）
FAMILIES = {
    "corridor_id_pinned_old": [
        "test_probe_escape_capacity_dn0", "test_probe_reports_via_gap_fact",
        "test_corridor_clear_span", "test_flip_polarity_cross_rejected",
        "test_drawing_only_refuses_no_node", "test_correct_polarity_solves_clean",
        "test_escape_deterministic_byte_identical",
    ],
    "region_derivation": ["test_capacity_regions_derived", "test_probe_region_capacity_structure",
                          "test_capacity_map_persist"],
    "solve_all_unsolved": ["test_board_level_consistency", "test_chain_no_pn_zero_spacing"],
    "topology_set": ["test_link_topology_crossing_old_topology"],
}


def counts(path: str) -> dict:
    p = os.path.join(REPO, path)
    if not os.path.isfile(p):
        return {"exists": False}
    s = open(p, encoding="utf-8", errors="replace").read()
    return {"exists": True, "bytes": len(s),
            "old_ids": {k: s.count(k) for k in OLD}, "new_ids": {k: s.count(k) for k in NEW},
            "old_total": sum(s.count(k) for k in OLD), "new_total": sum(s.count(k) for k in NEW)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEF_OUT)
    args = ap.parse_args()
    table = {name: counts(rel) for name, rel in CARRIERS.items()}
    doc = {
        "artifact": "k2_p6_hidden_failures_triage",
        "schema": 1,
        "scope": "22 skip 解锁后 13 项失败的只读根因 triage（走廊命名权威分歧）",
        "readonly": True,
        "corridor_naming": {"old": list(OLD), "new": list(NEW)},
        "carrier_distribution": table,
        "root_cause_reading": [
            f"SPEC 侧已用新 id（plain new_total={table['spec_plain'].get('new_total')} / rev-52 new_total={table['spec_rev52'].get('new_total')}）",
            f"遗留 alloc v2（**测试钉住的输入**；08-28 自 strix-halo-ioconvert 字节导入、从未重生成；现役工具链**不读**）仍全为旧 id（old_total={table['legacy_alloc_v2_pinned_by_tests'].get('old_total')}，new_total={table['legacy_alloc_v2_pinned_by_tests'].get('new_total')}）⇒ 与 SPEC 脱钩",
            f"引擎 hs_route_model 与判据 check_l3 亦含旧 id（engine old_total={table['engine_hs_route_model'].get('old_total')} / gate old_total={table['gate_check_l3_expects'].get('old_total')}）",
            f"测试旧 id 引用密集（old_total={table['tests'].get('old_total')}）",
        ],
        "failure_families": FAMILIES,
        "binary_recommendation": {
            "expectation_drift_needs_supervisor": [
                "tests + check_l3.SPEC_EXPECTS 跟随**旧**命名 ⇒ 若新 id 为权威：须监理批「改名承接」后同步（含 G3.1 期望集）",
                "反之若旧 id 为权威：SPEC 改名须回退/双名兼容（属判据/载体决策，ENG 不自决）",
            ],
            "carrier_defect_eng_after_approval": [
                "测试输入钉在**遗留 alloc v2**（与 SPEC 命名脱钩；现役工具链不读该件）⇒ 处置 = 测试重钉现行真源（SPEC 派生通道 / 现行配置）＋ 遗留件标 RETIRED（N-05 卫生）；均须授权",
                "hs_route_model 的旧 id 引用（若为语义硬编码而非兼容层）随 B2-1/B2-2 同批处置",
            ],
        },
        "reproduce": "grep -c 旧/新 id × 6 载体（见 carrier_distribution）；失败清单见 SHADOW_VERIFY_v1.json",
    }
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    for name, c in table.items():
        print(f"  {name:32s} old={c.get('old_total')} new={c.get('new_total')}")
    print("→", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
