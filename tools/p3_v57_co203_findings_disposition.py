#!/usr/bin/env python3
"""CO-203 — **L2 自裁：工具自声明修订号（自声明面）↔ 内容 同步 + 机判齿**：findings 入登记簿（幂等、注解**原位**）+ counts 复算。

M-1：CO-202 已把 oracle 内容升为 CO-202（`CASES` 5 案 / 牙齿 10），而其记录自声明 `revision` 仍 CO-200
（`nature` 仍「4 案」、`trigger` 未述第 5 案、docstring 仍「3 案」）；runner 头部修订清单亦漏 CO-200/CO-202。
只改登记簿。CLI: python3 tools/p3_v57_co203_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co203:M-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**工具自声明修订号面与内容不同步**：CO-202 处置已把 oracle 内容升为按 CO-202（`CASES` **5 案** / 牙齿 **10**），"
             "但其记录自声明 `revision` 仍为 **CO-200**（且 `nature` 仍称「4 案」、`trigger` 未述第 5 案、文件头 docstring 仍称「3 案」）；"
             "runner 头部修订清单亦漏 CO-200/CO-202。⇒ 下游读「oracle revision」者见 CO-200，会误判第 5 案（图/`.svg`）**未被覆盖** —— "
             "即「声明↔实现」在**自声明面**的漂移（承 R-CO194-1/2 之精神）。",
     "disposition": "CO-203（L2 自裁）：① oracle 自声明面 sync —— `revision` → **CO-202**、`nature` → **5 案**、`trigger` 补 CO-202（L-4）条款、"
                    "docstring 五案化；② runner 新增 `TOOL_REVISION_DECLARED`（自声明修订号类工具之**权威声明**）+ 纯判据 "
                    "`tool_revision_bound()`（**AST** 抽取记录 dict 字面量之 `revision`；注释/散文不得满足 —— 承 R-CO202-4）+ 静态齿 **t33**；"
                    "runner 头部修订清单补 CO-200/CO-202/CO-203。红线 **R-CO203-1**。",
     "status": "CLOSED",
     "next": "凡工具自声明 `revision` 者，内容升级须同 commit 同步其**自声明面**，并由 t33 机判（新增此类工具须入 `TOOL_REVISION_DECLARED`）。",
     "evidence": ["修前（AST 复算，零落盘）：as-found `27e9fe3` oracle 记录字面 `revision=\"CO-200\"` 而内容 5 案/10 牙齿；"
                  "`tool_revision_bound(<oracle>, rev=CO-200)` ⇒ `revision_mismatch`",
                  "修后：抽取字面 = `(True, 'CO-202')`；`tool_revision_bound(<oracle>, rev=CO-202)` ⇒ `ok`；"
                  "注释/散文源 ⇒ `(False, None)`（判别力控）；`--check` t33 = True（35 项全 True）；oracle 记录 `revision` = CO-202"],
     "refs": ["CO-203", "CO-202", "CO-200", "CO-194"], "closed_by": ["CO-203"]},
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
    note = ("；**CO-203（L2 自裁 · 自声明修订号 ↔ 内容 同步）**：+1 TOOL_DEFECT（`co203:M-1`，low，CLOSED；"
            "oracle 自声明面 sync（`revision`→CO-202 / `nature`→5 案 / `trigger` / docstring）+ runner "
            "`TOOL_REVISION_DECLARED` + `tool_revision_bound()`（AST 字面量）+ 静态齿 **t33**）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-203（L2 自裁 · 自声明修订号", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
