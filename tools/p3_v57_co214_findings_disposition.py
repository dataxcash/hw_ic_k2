#!/usr/bin/env python3
"""CO-214 — 登记簿入册（幂等、注解**原位**）+ counts 复算。

入册 1 项（`TOOL_DEFECT` / low / CLOSED）：`co214:K-1` —— L5 verdict 记录之板指纹**消费面 = ∅**
（CO-213 判明并列为「有据延后」，触发 = 板变更 **或** 下次 L5 重跑；本会话 L5 sign-off 已重跑 ⇒ 触发成立）。
只改登记簿。CLI: python3 tools/p3_v57_co214_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co214:K-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**L5 verdict 记录之被评板指纹在复现序内无消费者（消费面 = ∅）**：CO-212 把 `board`/`board_sha256` 钉**进**三件 L5 记录、"
             "CO-213 又把其自检改**真判别**，但两轮都停在**生产者侧**（`p3_v57_l5_signoff.py` 自检）—— 复现序内**无任何步读**该指纹 ⇒ "
             "「记录所钉的是不是**现行** L4 板」在序内**不可判**；被评板一旦变更（新 rev），L5 之 PASS（含等长 `0.1300 ≤ 0.15` 与 DFM PASS）"
             "**不会可见地失效**，而交办/放行恰以「L5 全绿」为据（承 R-CO212-1 之立意）。CO-213 已判明 `消费者（读记录 ∩ 含板指纹，除生产者）= ∅` "
             "并据实列为**有据延后**（触发 = 板变更或下次 L5 重跑）—— 不虚增。",
     "disposition": "CO-214（L2 自裁；**触发已成立**：本会话 L5 sign-off 重跑出 `.8` 版记录）⇒ 把该指纹**消费面机判入序**："
                    "`p3_v57_co120_provenance_pin_gate.py` 升 **CO-120.7**，补判据 **P5 / `l5_board_binding()`** —— "
                    "① 两件 JSON 记录（DFM/DFT、SI/PI/EMC）之 `board_sha256`（**全 64-hex**）须 == **现行** L4 板 sha256 且 != **冻结源板**；"
                    "② G7 md 记录须含**现行** L4 板 sha16；③ 缺件 / 不可解析 / 退化（全零）⇒ 该行 `ok=False`（**fail-closed**，禁静默跳过）。"
                    "任一不合格 ⇒ 本闸 verdict = `FAIL_L5_RECORD_BOARD_BINDING`（rc≠0）而**非** PASS。齿 **+4**（1 正控 = 实件全 ok；"
                    "3 负控 = JSON 退回冻结源板 / 退化全零 / md 以冻结源 sha16 顶替，皆须被抓）；runner `EXPECTED_TEETH` 同步（co120 **15 → 19 齿**）；"
                    "**步集/序列不变（仍 50 次）**。**R-CO214-1**。",
     "status": "CLOSED",
     "next": "凡产出 verdict 记录（L5 sign-off / L4 图纸 / 闸记录等）者，其**被评态指纹**须有**至少一个序内或闸内消费者**以机判核对；"
             "被评态记录之生产者与消费者须同 commit 双侧同步，缺消费者即 fail-closed。",
     "evidence": ["CO-213 复评（as-found `f0016ae`）：全工具集扫描 `board_sha256` 消费面 = ∅（除生产者自检）",
                  "修后实测（本会话）：co120 **PASS**、`l5_board_binding.all_ok=True`、`l5_bad=0`、齿 **19/19 全 True**、revision **CO-120.7**",
                  "独立判别探针（直调 `l5_board_binding()` 注入，零落盘）：注入**冻结源板** sha256 ⇒ `all_ok=False`；注入**退化全零** ⇒ `all_ok=False`；实件 ⇒ `all_ok=True`"],
     "refs": ["CO-172", "CO-193", "CO-212", "CO-213", "CO-214"], "closed_by": ["CO-214"]},
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
    note = ("；**CO-214（L2 自裁 · L5 记录板指纹消费面机判）**：+1 TOOL_DEFECT（`co214:K-1` L5 板指纹消费面 = ∅ ⇒ "
            "co120 升 CO-120.7 补 P5 `l5_board_binding()`（4 齿，15→19）；low、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-214（L2 自裁 · L5 记录板指纹消费面机判", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG), "n_items": len(reg["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
