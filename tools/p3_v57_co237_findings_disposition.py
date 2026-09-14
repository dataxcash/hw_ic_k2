#!/usr/bin/env python3
"""CO-237 — L2 自裁（复评件覆盖面入机判）发现入册（幂等、注解原位）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
WHAT = ("**t44 之「域」= 手写 2 件声明 ⇒ 复评件覆盖面无机判（新增复评件不被强制纳入）**："
        "CO-236 新增静态齿 t44（复评/重出件 as-found 幂等）之声明集 `REISSUE_RECORDS_DECLARED` 只列 **2 件**，"
        "而 boundary pin 面实测受 pin 之 `*_review.json` 共 **14 件** ⇒ 12 件**域外**（无声明臂、无最低覆盖面） ⇒ "
        "**新增复评件可不经声明而落于 t44 之外**（「域由声明自述给出」= R-CO230-1 所禁；「覆盖面须机判 + 域下限」= R-CO234-1 所立）。"
        "**同类已实测两次漏项**：z96 之复评债声明面**漏 CO-231**（CO-235 F-2 实测）；复评债连续性无机判齿。"
        "承 R-CO225-1（红线之形态无机判齿即空真）/ R-CO193-3（复评件须 as-found 幂等）/ R-CO234-1（覆盖面须机判 + 域下限）。")
DISPO = ("CO-237（L2 自裁）：① t44 **域显式化** —— 域 = **boundary pin 面**中一切 `*_review.json` 受 pin 件（**非**由声明自述给出，承 R-CO230-1）；"
         "② 域成员须 ∈ `REISSUE_RECORDS_DECLARED` ∪ **显式豁免集** `REISSUE_RECORDS_EXEMPT`（**名集等式** = 域 − 声明，防静默缩域/漏项；每项须有 `why` + **同源锚**）；"
         "③ **域下限** `REISSUE_DOMAIN_FLOOR = 12`（防「删 pin 行即空真」）；④ 12 件既有复评件（CO-236 前）**显式豁免**并附理由（as-found 内嵌于散文、非 `.rev` 结构；"
         "工具经**只读复核无现行链读取**）—— 属**如实登记之残余**；⑤ 扩 **t44** 之覆盖面臂（**不新增齿**，仍 46）；⑥ report revision → **CO-203.14**；⑦ **R-CO237-1**。")
NEXT = ("复评件之**覆盖面**须**机判**：域须由**受 pin 面**给出（**不得**由声明自述）；域成员须 ∈ 声明集 ∪ 显式豁免集（名集等式 + 理由 + 同源锚）+ 域下限。"
        "**残余（未闭，界定）**：① 域以**文件名形态** `*_review.json` 界定 ⇒ 异名复评件（改命名约定）可逃逸（须先入域规则）；② 豁免之 12 件为**既有**复评件（其 as-found 纯性未逐一入结构臂）。")
ADD = [{"finding": "co237:F-1", "sev": "mid", "kind": "TOOL_DEFECT", "what": WHAT, "disposition": DISPO,
        "status": "CLOSED", "next": NEXT,
        "evidence": ["实测（本会话只读）：boundary pin 面受 pin 之 `*_review.json` **14 件**，而 t44 声明集仅 **2 件** ⇒ 12 件域外",
                     "同类漏项实测：z96 复评债声明面漏 CO-231（CO-235 F-2）；复评债连续性无机判齿",
                     "修后：域 = 14，声明 2 + 豁免 12（**名集等式**成立：`set(EXEMPT) == set(domain) - set(DECLARED)`）；负控：域成员未列 ⇒ `domain - declared` 与豁免集不等 ⇒ t44 Fail"],
        "refs": ["CO-225", "CO-230", "CO-234", "CO-235", "CO-236", "CO-237"], "closed_by": ["CO-237"]}]
NOTE = ("；**CO-237（L2 自裁 · 复评件覆盖面入机判）**：+1 TOOL_DEFECT"
        "（`co237:F-1`：t44 域 = 手写 2 件声明 ⇒ 覆盖面无机判、新增复评件不被强制纳入；同类漏项实测两次；"
        "处置 = 域改由 boundary pin 面给出 + 域成员 ∈ 声明 ∪ 显式豁免（名集等式 + 锚）+ 域下限 + 扩 t44 覆盖面臂；mid、CLOSED）。")


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
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-237（L2 自裁", NOTE)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
