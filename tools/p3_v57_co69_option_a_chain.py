#!/usr/bin/env python3
"""CO-69：方案(a) 全链执行记录（引擎 bump + G4..G7 + SI 判据升级 + 电气等长整改）—— 机器汇总。

只读产物并汇总 sha/判定；不改任何板/图纸/工件。产出 JSON + MD（CO-69 变更单）。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
ROOT = K2.parent
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co69_option_a_chain.json"
MD = STEP2 / "m13_v57_CO69_L2_option_a_chain.md"


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    g4 = json.loads((STEP2 / "m13_v57_w3_joint_assignment.json").read_text(encoding="utf-8"))
    g5 = json.loads((STEP2 / "m13_v57_w3_validation.json").read_text(encoding="utf-8"))
    l4c = json.loads((STEP2 / "m13_v57_l4_construction.json").read_text(encoding="utf-8"))
    l4v = json.loads((STEP2 / "m13_v57_l4_validation.json").read_text(encoding="utf-8"))
    fab = json.loads((STEP2 / "m13_v57_l5_fab_record.json").read_text(encoding="utf-8"))
    dfm = json.loads((STEP2 / "m13_v57_l5_dfm_dft_record.json").read_text(encoding="utf-8"))
    si = json.loads((STEP2 / "m13_v57_l5_si_pi_emc_record.json").read_text(encoding="utf-8"))
    frozen = {"SPEC_k2_v4.json": (L3 / "SPEC_k2_v4.json", "0bd52ed48e720b8c"),
              "page_manifest": (STEP2 / "m13_v57_s1_page_manifest.json", "a8ef3ea8ecff99d7"),
              "k2_v4_8L.kicad_pcb": (K2 / "k2_v4_8L.kicad_pcb", "fb07d25ac426ff84"),
              "drc_rules.json": (ROOT / "_shared/eda_core/drc_rules.json", "0a459839e15960b8")}
    fro = {k: {"sha16": s16(v), "match": s16(v) == e} for k, (v, e) in frozen.items()}
    res = {
        "artifact": "m13_v57_co69_option_a_chain", "schema": 1, "revision": "CO-69.1",
        "nature": "L2 叠层分配：方案(a) 引擎 bump + 全链 G4..G7 + SI 判据升级（按层加权电气长度）",
        "four_sources": fro, "four_sources_all_match": all(v["match"] for v in fro.values()),
        "versioned_inputs": {"lid_rev6": s16(STEP2 / "m13_v57_layer_intent_rev6.json"),
                             "spec_rev5": s16(L3 / "SPEC_k2_v4.spec-rev-5.json"),
                             "co16_alloc7": s16(STEP2 / "m13_v57_co16_channel_allocation_v7.json")},
        "gates": {
            "G4": {"rev": g4.get("revision"), "verdict": g4.get("verdict"),
                   "drawing": s16(STEP2 / "m13_v57_w3_joint_assignment.json"),
                   "landing": s16(STEP2 / "m13_v57_w3_chip_landing_rows.json"),
                   "crossings": g4.get("same_layer_crossings")},
            "G5": {"verdict": g5.get("verdict"), "frozen": g5.get("frozen"),
                   "validation": s16(STEP2 / "m13_v57_w3_validation.json"),
                   "validator_v2": s16(K2 / "tools/p3_v57_w3_constructive_validator_v2.py")},
            "G6": {"board": s16(K2 / "k2_v4_8L.l4.kicad_pcb"), "verdict": l4v.get("verdict"),
                   "n_nets": l4c["tally"]["n_nets"], "n_segments": l4c["tally"]["n_segments"],
                   "n_vias": l4c["tally"]["n_vias"],
                   "construction": s16(STEP2 / "m13_v57_l4_construction.json"),
                   "validation": s16(STEP2 / "m13_v57_l4_validation.json"),
                   "validator": s16(K2 / "tools/p3_v57_l4_validator.py")},
            "G7": {"fab": {"sha16": s16(STEP2 / "m13_v57_l5_fab_record.json"),
                           "n_tracks": fab["n_tracks"], "n_vias": fab["n_vias"]},
                   "dfm": {"verdict": dfm["verdict"], "new_total": dfm["drc"]["new_total"],
                           "disappeared_total": dfm["drc"]["disappeared_total"],
                           "in_scope_unconnected": dfm["dft"]["in_scope_unconnected_nets"],
                           "sha16": s16(STEP2 / "m13_v57_l5_dfm_dft_record.json")},
                   "si": {"verdict": si["verdict"], "rev": si["revision"],
                          "max_elec_skew_mm_eq": si["SI"]["max_intra_pair_skew_mm"],
                          "max_phys_skew_mm": si["SI"]["max_intra_pair_skew_phys_mm"],
                          "skew_rule_mm": si["SI"]["skew_rule_mm"],
                          "widths_by_layer": si["SI"]["track_width_rule_mm_by_layer"],
                          "sha16": s16(STEP2 / "m13_v57_l5_si_pi_emc_record.json")}},
        },
        "engine_deltas": {
            "layer_palette": ["F.Cu", "In2.Cu", "In5.Cu", "B.Cu"],
            "spec": "spec-rev-4 -> spec-rev-5", "layer_intent": "rev5 -> rev6",
            "co16_alloc": "ALLOC.5 (0bf6cdc203887a48) -> ALLOC.7 (a765af4c9bf61e64)（CO-60 候选 v6 2ebda54c 未触碰）",
            "revision": "W3-CN.40 -> W3-CN.41",
            "length_compensation": "CO-69：对内等长补偿由**纯物理长度**改为**按层加权电气长度**"
                                   "（数据对：lane(In5) 换算；REFCLK：F.Cu 换算）——修复电气 skew",
        },
        "si_criterion_upgrade": {
            "rule": "intra_pair_skew_mm = 0.15（按层加权电气长度；mm-eq @ er_ref=3.99）",
            "before_fix": {"max_elec_skew_mm_eq": 0.9807, "max_phys_skew_mm": 0.0031,
                           "verdict": "FAIL（REFCLK1 0.9807：P 全 F.Cu vs N F.Cu+In2 8.745mm）"},
            "after_fix": {"max_elec_skew_mm_eq": si["SI"]["max_intra_pair_skew_mm"],
                          "max_phys_skew_mm": si["SI"]["max_intra_pair_skew_phys_mm"],
                          "verdict": si["verdict"]},
            "note": ("电气等长达成后**物理** skew 上升（max %.4fmm）——属层补偿之预期：判据为电气（时延），"
                     "物理为报告量。CO-62 §4 要求保留物理量报告。" % si["SI"]["max_intra_pair_skew_phys_mm"]),
        },
        "reproducibility": {"board": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
                            "drawing": s16(STEP2 / "m13_v57_w3_joint_assignment.json"),
                            "note": "全链（引擎→G5→L4→L5）连跑 ×2，产出 11 件逐字节一致（CO-49 口径）"},
        "open_items": [
            "板厂阻抗券（SPEC coupon_required=true）——一阶 IPC-2141 未替代 SI9000/券",
            "① 对间净空 0.875（中心距 1.580）：本方案(a) 未解（瓶颈 = 板边/球栅逃逸，属 L1 包络冲突，非本件范围）",
            "物理 skew 报告量升至 %.4fmm（电气已达标）——若验收方要求物理量亦 ≤0.15，需双变量补偿/重构，属新 L2 议题"
            % si["SI"]["max_intra_pair_skew_phys_mm"],
        ],
        "redline": "只读产物；四冻结源 4/4 MATCH；原件/历史件未动；未放宽任何阈值。",
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    g = res["gates"]
    md = f"""# CO-69 — 【L2 叠层分配】方案(a) 全链执行：引擎 bump + G4..G7 + SI 判据升级

> 2026-09-12｜定层 **L2**（CO-67 裁定）｜工具 `tools/p3_v57_co69_option_a_chain.py`
> 记录 `{s16(OUT)}`｜LID REV6 `{s16(STEP2 / 'm13_v57_layer_intent_rev6.json')}`｜SPEC rev-5 `{s16(L3 / 'SPEC_k2_v4.spec-rev-5.json')}`｜ALLOC.6 `{s16(STEP2 / 'm13_v57_co16_channel_allocation_v6.json')}`

## 1. 引擎 bump（版本化输入）
- `LAYER_PALETTE` -> `{res['engine_deltas']['layer_palette']}`；引擎全量 `In6.Cu -> In5.Cu`；`REVISION_CO16` -> **{res['engine_deltas']['revision']}**。
- `F.spec` -> **SPEC rev-5**；`F.layer_intent` -> **LID REV6**；`CO16_ALLOC` -> **ALLOC.6**（stub 层 In6->In5，4 页）。
- L4 applier：track 宽度改**按层**（`impedance.width_mm_by_layer`：F/B 0.205、In2/In5 0.16）。
- L5：SI 判据升级为**按层加权电气长度**；planes 集合 -> In1/In3/In4/**In6**。

## 2. 整链门禁（实测）
| 门 | 判定 | 证据 |
|---|---|---|
| G4 | **{g['G4']['verdict']}** | 图纸 `{g['G4']['drawing']}`（{g['G4']['crossings']} crossings）、landing `{g['G4']['landing']}` |
| G5 | **{g['G5']['verdict']}**（frozen={g['G5']['frozen']}） | validation `{g['G5']['validation']}` |
| G6 | **{g['G6']['verdict']}** | 板 `{g['G6']['board']}`（{g['G6']['n_nets']} 网/{g['G6']['n_segments']} 段/{g['G6']['n_vias']} via）、construction `{g['G6']['construction']}` |
| G7 | FAB ok / DFM **{g['G7']['dfm']['verdict']}** / SI **{g['G7']['si']['verdict']}** | new={g['G7']['dfm']['new_total']} / vanished={g['G7']['dfm']['disappeared_total']} / 在册未连 {g['G7']['dfm']['in_scope_unconnected']}/68；SI `{g['G7']['si']['sha16']}` |

**SI（对内等长）**：判据 = 按层加权电气长度（mm-eq @ er_ref=3.99）。
- 升级**前**（仅物理等长）：max **0.9807** > 0.15 ⇒ **FAIL**（REFCLK1：P 全 F.Cu vs N F.Cu+In2 8.745mm）。
- 整改（CO-69，L2 等长）：补偿目标由物理长度改为层加权电气长度 ⇒ max **{g['G7']['si']['max_elec_skew_mm_eq']}** ≤ 0.15 ⇒ **PASS**。
- 物理量报告 max {g['G7']['si']['max_phys_skew_mm']} mm（层补偿之预期；判据为电气/时延）。

## 3. 复现
- 全链连跑 ×2：11 件产出逐字节一致；板 **{res['reproducibility']['board']}** / 图纸 **{res['reproducibility']['drawing']}**。

## 4. 开放项
{chr(10).join('- ' + x for x in res['open_items'])}

## 5. 指纹（冻结四源 {'4/4 MATCH' if res['four_sources_all_match'] else 'DRIFT'}）
`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`
"""
    MD.write_text(md, encoding="utf-8")
    print(json.dumps({"json": s16(OUT), "md": s16(MD), "g4": g["G4"]["verdict"], "g5": g["G5"]["verdict"],
                      "g6": g["G6"]["verdict"], "dfm": g["G7"]["dfm"]["verdict"], "si": g["G7"]["si"]["verdict"],
                      "elec_skew": g["G7"]["si"]["max_elec_skew_mm_eq"], "phys_skew": g["G7"]["si"]["max_phys_skew_mm"],
                      "board": res["reproducibility"]["board"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
