#!/usr/bin/env python3
"""CO-217 — 登记簿入册（幂等、注解**原位**）+ counts 复算。

入册 1 项（`TOOL_DEFECT` / low / CLOSED）：`co217:N-1` —— L5 SI 判定记录之**判据源**为**硬编码旧 rev**
（`SPEC_k2_v4.spec-rev-7.json`，记录自述更作 rev-5）⇒ 把**已退役** legacy `inter_pair_spacing_mm=0.875`
呈现为现行口径（rev-19 现行 = `0.41`）。
只改登记簿。CLI: python3 tools/p3_v57_co217_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co217:N-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**L5 SI 判定记录之判据源为硬编码旧 rev ⇒ 退役定值被当作现行口径**：`p3_v57_l5_signoff.py` 读 "
             "`SPEC_k2_v4.spec-rev-7.json`（而该记录之 `netclass_geometry.source` 又自述为 **rev-5** ⇒ 自述源与实现源**亦不一致**），"
             "其 `net_classes.PCIe85.inter_pair_spacing_mm` = **0.875** 系 **已退役** legacy（`retired_inter_pair_spacing_0p875_v1` 标 "
             "`LEGACY_DERIVED`、ledger `DV-INTPAIR-EDGE.supersedes` 同判；rev-19 现行绑定 = **0.41**（外层 2×w=2×0.205），逐层 0.41/0.32）"
             "⇒ 判定记录把**退役定值**呈现为现行口径（记录面 **fail-open**：人/机读者据以误判对间规则 —— 承 CO-210「须引现行定案」同族，面 = **判定记录**而非随单）；"
             "且硬编码旧 rev 为**潜在陈旧阈值源**（**实测非惰性**：`net_classes` 在 rev-7/rev-19 间不同；`impedance` 同 ⇒ 见「影响面」）。"
             "**影响面（如实）**：SI verdict = `widths_ok ∧ skew ≤ drc_rules.diff_pair.intra_pair_skew_mm`，二者皆不取 `net_classes` ⇒ **判决未变**（PASS / skew 0.1300 ≤ 0.15 / 34 页）；"
             "本项为**记录正确性 + 漂移防护**，非判决翻转。",
     "disposition": "CO-217（L2 自裁）：① 判据源改读**现行冻结源** `SPEC_k2_v4.spec-rev-19.json` 并**钉 sha16**（`SPEC_SRC` / `SPEC_SRC_SHA16` + "
                    "`load_spec()`：缺件/漂移 ⇒ `SystemExit`，**fail-closed**，禁静默降级到旧 rev）；② SI 记录增 `inter_pair_derivation`（现行逐层 0.41/0.32）"
                    "与 `retired_inter_pair_spacing`（0.875 / `LEGACY_DERIVED` / `replaced_by`，**显式留存** —— 承「退役决策须显式留存」）；"
                    "③ `source` 自述改指 rev-19 + sha16；④ 齿 **+2**（`spec_src_ok` / `spec_src_discriminates`（注入伪造字节必判否 ⇒ 非恒真））并入 rc；"
                    "⑤ SI 记录 **L5-SI.8→.9**、G7 记录 **L5-G7.8→.9** 且 G7 增「L5 SI 判据源」行。**序不变（仍 50 次）**。**R-CO217-1**。",
     "status": "CLOSED",
     "next": "凡产出判据性 verdict 之工具，其**判据源**须为**现行冻结源**且**钉 sha**（缺件/漂移 ⇒ fail-closed）；"
             "SPEC/规则源升级时须**同 commit** 更新源常数与 pin；**退役定值不得以现行口径呈现**（须标 kind/replaced_by）。",
     "evidence": ["实测（rev-7 vs rev-19）：`net_classes.PCIe85.inter_pair_spacing_mm` = 0.875 → **0.41**；rev-19 另存 `retired_inter_pair_spacing_0p875_v1`（value 0.875 / kind LEGACY_DERIVED / replaced_by net_classes.PCIe85.inter_pair_derivation_v1）；`impedance` 块跨 rev **逐字节同**（故 widths_ok 不变）",
                  "修后实测：SI **verdict=PASS**（widths_match=True / skew 0.1300 ≤ 0.15 / 34 页）；记录 `spec.inter_pair_spacing_mm=0.41`、`inter_pair_derivation.by_layer_edge_mm={F.Cu:0.41,B.Cu:0.41,In2.Cu:0.32,In5.Cu:0.32}`、`retired_inter_pair_spacing` 显式留存、`source` = rev-19+sha16；齿 4/4（含新 2 枚）；**独立探针**：错 pin16 ⇒ False、注入 `b\"{}\"` ⇒ False（sha 确被比较，非恒真）",
                  "并存事实（登记免误判）：`SPEC_k2_v4.json`（spec_version 1.1.spec-rev-1，sha16 0bd52ed48e720b8c）= **监理级原始冻结点**（watch.py FROZEN），与设计现行源 rev-19 **语义不同**；G7 §5「冻结四源」行沿用 rev-1 冻结点，本工具判据一律取 rev-19"],
     "refs": ["CO-54", "CO-68", "CO-134", "CO-210", "CO-212", "CO-217"], "closed_by": ["CO-217"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def upsert_note(ub: str, mark: str, note: str) -> str:
    """注解 upsert：**原位**替换本段（右界 = 下一 `；**CO-` 起点 / 末尾）—— 禁无界裁尾、禁移段（R-CO197-4）。"""
    if mark in ub:
        i = ub.index(mark); j = ub.find("；**CO-", i + len(mark))
        return ub[:i] + note + (ub[j:] if j != -1 else "")
    return ub + note


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    by_id = {i["finding"]: n for n, i in enumerate(reg["items"])}
    added, updated = [], []
    for it in ADD:
        if it["finding"] in by_id:
            if reg["items"][by_id[it["finding"]]] != it:
                reg["items"][by_id[it["finding"]]] = it
                updated.append(it["finding"])
        else:
            reg["items"].append(it)
            added.append(it["finding"])
    note = ("；**CO-217（L2 自裁 · L5 判据源绑定 + 退役定值留存）**：+1 TOOL_DEFECT（`co217:N-1` L5 SI 记录之判据源为硬编码 rev-7 "
            "⇒ 退役 legacy `inter_pair_spacing_mm=0.875` 被当作现行口径（rev-19 = 0.41）⇒ 改读现行冻结 rev-19 + 钉 sha + 退役值显式留存；low、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-217（L2 自裁 · L5 判据源绑定", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG), "n_items": len(reg["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
