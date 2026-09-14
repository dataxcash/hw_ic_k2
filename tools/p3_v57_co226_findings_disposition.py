#!/usr/bin/env python3
"""CO-226 — L2 自裁（跨源判据语义绑定 + 退役显式留存）发现入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co226:F-1", "sev": "mid", "kind": "TOOL_DEFECT",
     "what": "**跨源副本静默充当判据源（+ 退役定值以现行口径呈现）**：L5 SI **等长窗口判据**原直接消费共享规则件 `_shared/eda_core/drc_rules.json` 之 "
             "`diff_pair.intra_pair_skew_mm`（**副本**）而非 SPEC 真源 ⇒ 真源升级时判据**静默失锚**；且该副本把 SPEC **已显式退役**之 legacy `0.875`"
             "（`retired_inter_pair_spacing_0p875_v1`，kind=LEGACY_DERIVED）以**现行口径**呈现（副本 `inter_pair_spacing` = 0.875 vs SPEC rev-19 = 0.41）"
             "⇒ 违 **R-CO217-1** 两处（判据源绑定 / 退役显式留存），且属 **R-CO225-1** 之「红线无机判齿即空真」。",
     "disposition": "CO-226（L2 自裁）：① 等长窗口判据源改绑 **SPEC 真源**（`net_classes.PCIe85.intra_pair_skew_mm`，sha 由 `load_spec()` 钉）+ 副本**交叉校验**"
                    "（分歧 ⇒ SystemExit fail-closed；两者一并入 SI 记录）；② 入机判 runner 静态齿 **t36_cross_source_semantics_bound**（键映射**名集钉定** + 副本键**域钉定** "
                    "+ **被消费键**一致性 + 其余分歧须入**显式分歧登记**（登记值须 == 副本现值）；正/负控齐备）；③ `inter_pair_spacing` 分歧**显式登记**（副本漂移，SPEC 已退役 0.875）；"
                    "④ 自声明面 bump（`L5-SI.9 → L5-SI.10` / runner `CO-203.3 → CO-203.4`）。**R-CO226-1**。",
     "status": "CLOSED",
     "next": "凡判据源与**共享层副本**并存者，须以「键映射名集 + 副本域钉定 + 被消费键一致性」机判绑定；副本漂移须**显式登记**（含退役依据/取代者）方可放行。"
             "**容器级（未闭）**：`_shared/eda_core/drc_rules.json` 内含**单板特判**（K2 SPEC 派生量 + `net_prefix=PCIE`）且把**已退役** 0.875 以现行口径呈现 ⇒ 违容器 "
             "AGENTS.md §3「共享层零单板特判」；K2 侧无权单方面改动 **5 工程同字节**冻结件 ⇒ 待**容器侧**处置（K2 已改为不消费该键作判据）。",
     "evidence": ["机判实测：真源/副本逐键对照 —— p_gap 0.175/0.175、p_width 0.205/0.205、intra_pair_skew_mm 0.15/0.15、target_zdiff 85.0/85.0 皆等；"
                  "inter_pair_spacing = SPEC 0.41 vs 副本 0.875（分歧）",
                  "修前（空分歧登记）：`cross_source_semantics_decision(...) == \"divergence_unregistered\"` ⇒ 齿非空真",
                  "fail-closed 实测：副本注入 intra_pair_skew_mm=0.99 驱动 L5 工具 ⇒ SystemExit（记录零污染：仍 L5-SI.10 / 0.15/0.15 / PASS）",
                  "修后：`--check` 38/38 全 True；L5 SI verdict=PASS（skew 0.1300 ≤ SPEC 真源 0.15）"],
     "refs": ["CO-81", "CO-217", "CO-219", "CO-225", "CO-226"], "closed_by": ["CO-226"]},
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
    by = {i["finding"]: n for n, i in enumerate(reg["items"])}
    added, updated = [], []
    for it in ADD:
        if it["finding"] in by:
            if reg["items"][by[it["finding"]]] != it:
                reg["items"][by[it["finding"]]] = it; updated.append(it["finding"])
        else:
            reg["items"].append(it); added.append(it["finding"])
    note = ("；**CO-226（L2 自裁 · 跨源判据语义绑定 + 退役显式留存）**：+1 TOOL_DEFECT（`co226:F-1` L5 等长窗口判据源为共享副本而非 SPEC 真源"
            "（R-CO217-1）+ 副本把已退役 0.875 以现行口径呈现；处置 = 判据源改绑 SPEC 真源 + 副本交叉校验（分歧 fail-closed）+ 静态齿 t36（键映射名集 / 副本域钉定 / "
            "被消费键一致 / 分歧显式登记）；mid、CLOSED；**容器级残余**见该项 `next`）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-226（L2 自裁", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
