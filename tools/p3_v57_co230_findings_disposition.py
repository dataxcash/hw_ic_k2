#!/usr/bin/env python3
"""CO-230 — 非执行者对抗复评 CO-225..CO-229（+ 同会话处置）发现入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co230:F-1", "sev": "mid", "kind": "TOOL_DEFECT",
     "what": "**boundary 节集（枚举域）由被判对象自述 ⇒ 整节删除不被检出（空真）**：t35 臂① 以 `boundary_sections_with_fp()` 为域，而该域 = boundary **文档自身**之实存节集 "
             "⇒ 删整节（含其 pin 表）后该节**同时**从域与现实中消失 ⇒ `boundary_fp_missing() == []` 恒成立（方向 fail-open）。"
             "实测（内存注入、零落盘）：删 §95 ⇒ 臂① 仍 `[]`；删 §98..§102（五节）⇒ 仍 PASS；且 runner 内**无任何齿**声明「应有节集/节数」。"
             "承 R-CO219-1（枚举面须名集等式）/ R-CO225-1（判定面完整性须名集钉定）—— CO-225 把**齿名集**钉定，但**节集**面遗漏。",
     "disposition": "CO-230（L2 自裁）：① 新增 `BOUNDARY_SECTIONS_DECLARED`（**100 节** = 实存 99 节 `{1..7, 11..102}` + 本件 §103；实测 8/9/10 不存在，属**显式**声明）+ 纯判据 "
                    "`boundary_section_set_decision(found, declared)`（**双向**：缺节 ⇒ `section_missing`；未声明之新增节 ⇒ `section_undeclared`）；② **扩 t35 臂①**入该等式（正/负控齐备；"
                    "**不新增齿**，齿数仍 **41**）；③ 自声明面同步：runner report revision → **CO-203.8**；④ 登记簿入册本项（CLOSED）。**R-CO230-1**。",
     "status": "CLOSED",
     "next": "凡以**文档/工件自述**为其枚举域之判定面，须另立 `*_DECLARED` 名集做**双向等式**（缺项/未声明新增皆停机）；判据面之**域**不得由被判对象自身给出（承 R-CO219-1 / R-CO225-1）。"
             "**残余（未闭，界定）**：本件只钉「节集」；节内叙述完备性、pin 表**内容**之正确性（现行态再对齐，见在册项）与红线—齿之全量映射仍由各节 / co120 / co135 / 逐案处置承载。",
     "evidence": ["as-found 钉 `fdb72a2`：逐件 sha16 复核全对（runner 5dc43f6e3aedd50d / boundary e5fe950356777eff / 登记簿 ecf2963e9165f6f4）",
                  "判别力（本会话实测）：实存 99 节 `missing=[]`；删 §95 ⇒ 臂① `[]`（**PASS**，空真）；删 §98..§102 ⇒ `[]`（**PASS**）；修后（`BOUNDARY_SECTIONS_DECLARED`）同一注入 ⇒ `section_missing`",
                  "runner 静态齿面：`--check` 修前 41/41 True（违例不可见）⇒ 修后 41/41 True（新增节集臂）"],
     "refs": ["CO-212", "CO-219", "CO-225", "CO-230"], "closed_by": ["CO-230"]},
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
    note = ("；**CO-230（非执行者对抗复评 CO-225..CO-229）**：+1 TOOL_DEFECT（`co230:F-1` boundary **节集**由自述而非声明承载 ⇒ "
            "整节删除不被检出（空真）；处置 = 声明集 `BOUNDARY_SECTIONS_DECLARED` + 纯判据双向等式扩 t35 臂①，不新增齿；mid、CLOSED。"
            "观测：§98 之「标签 CO-203.3 ↔ pin 现行 sha」为**已在册**之 pin 再对齐语义项，非本件新发现）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-230（非执行者对抗复评", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
