#!/usr/bin/env python3
"""CO-231 — L2 自裁（boundary pin 表**内容**入机判）发现入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co231:F-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**boundary pin 表之「内容」无机判齿 + 一枚不可复核行**：R-CO152-1 以 boundary pin 表为**唯一**现行 sha 承载面，但此前只判「每节**有** pin 表」（t35）⇒ ① 表内所列为**陈旧/伪造值**时无齿可检（手改、或序中途 abort 使末步 boundary_append 未跑）；"
             "② §87 实测一枚**名实不符**行「被消费 L5 记录（DFM/DFT、SI/PI/EMC、G7）| `6632179e1ef63183`」——标签声称**三件**而所列 sha16 实为 `m13_v57_l5_dfm_dft_record.json` **一件** ⇒ 该行**指称不唯一、不可复核**，且就 §87 节而言 SI/PI/EMC 与 G7 两件**未钉**（他节有钉，故非全链缺口）。",
     "disposition": "CO-231（L2 自裁）：① **生成器**拆分 §87 该行为三行（各带唯一文件指称）；② 新增 runner 静态齿 **t40_boundary_pin_rows_current**：pin 行标签须**恰一个**文件指称（于显式声明根集 `BOUNDARY_PIN_ROOTS` **唯一**解析）"
                    "且所列 sha16 **== 实件**；不可解析之标签须入**显式豁免名集** `BOUNDARY_PIN_LABEL_EXEMPT`（**名集等式**，现为**空**）+ 正/负控；③ 自声明面同步 runner report revision → **CO-203.9**；④ **R-CO231-1**。",
     "status": "CLOSED",
     "next": "boundary pin 表行须始终「**指称唯一 + 值 == 实件**」；新增解析根或豁免标签须**显式**入 `BOUNDARY_PIN_ROOTS` / `BOUNDARY_PIN_LABEL_EXEMPT`（否则 fail-closed）。"
             "**残余（未闭，界定）**：本件**不**判 pin 表之**完备性**（哪件**应有** pin 由各节自身 / co120 / co135 citation 扫描承载），亦不判节内叙述完备性。",
     "evidence": ["修前实件 548 行：**1 行**不可复核（§87 三件标签）、余皆可解析且值 == 实件（0 陈旧）",
                  "判别力（本会话实测，非合成）：编辑 runner 后**未**跑 boundary_append ⇒ **48 行** `pin_value_stale` ⇒ t40 **False**；realign 后 ⇒ t40 **True**（`--check` 42/42）",
                  "合成负控：值陈旧 ⇒ `pin_value_stale`；指称不唯一/无指称而未豁免 ⇒ `pin_reference_unresolved`；豁免名集覆盖 ⇒ ok"],
     "refs": ["CO-212", "CO-214", "CO-230", "CO-231"], "closed_by": ["CO-231"]},
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
    note = ("；**CO-231（L2 自裁 · boundary pin 表内容入机判）**：+1 TOOL_DEFECT（`co231:F-1` §87 一枚 pin 行**名实不符**（标签三件/实钉一件）⇒ 不可复核；"
            "且「pin 表内容 == 实件」原无机判齿；处置 = 生成器拆行 + 静态齿 t40（指称唯一 + 值 == 实件 + 豁免名集等式）；low、CLOSED。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-231（L2 自裁", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
