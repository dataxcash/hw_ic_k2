#!/usr/bin/env python3
"""CO-216 — 登记簿入册（幂等、注解**原位**）+ counts 复算。

入册 1 项（`TOOL_DEFECT` / low / CLOSED）：`co216:M-1` —— runner 内**其余两枚源面帮助函数**仍以**原文**
判事（`declared_verdict_in_tool` 之 `v in src`；`boundary_read_scan` 之 `re` 扫原文 + 读取**原文子串**）
⇒ 注释/散文即可伪造（R-CO202-4 / R-CO215-1 同源缺陷）。
只改登记簿。CLI: python3 tools/p3_v57_co216_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co216:M-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**源面判据仍以原文判事（AST 收窄未竟）**：CO-215 只收窄了 `artifact_readers()`，runner 内另有两枚**源面帮助函数**仍以**原文**判 —— "
             "① `declared_verdict_in_tool()`（R-CO194-2「声明↔工具能力」）取 **`v in src`** ⇒ 源内**注释**含该 verdict 字面即满足"
             "（如 `# FAIL here`）⇒ **t27 该臂近乎空真**（任何含该词之注释均可满足）；"
             "② `boundary_read_scan()`（CO-187/CO-192，判「该步读取 boundary」）以 `re` 扫**原文**判引用 + 以 "
             "`read_text`/`read_bytes`/`.read(`/`io.open(` 之**原文子串**判读取 ⇒ **注释即可伪造引用与读取者身份**（t21 之读取者集可被散文污染）；"
             "反向：以**无可匹配字面量**之完全动态方式引用者**漏判** ⇒ t21 之等式检查**静默漏过**未声明读者（fail-closed 方向的静默）。"
             "二者皆与 **R-CO202-4**「注释/散文不得满足源内声明」**同源**。",
     "disposition": "CO-216（L2 自裁 · 承 R-CO215-1）：① `declared_verdict_in_tool()` 改判 **AST 字符串字面量集**（`_source_strings`）并支持 `src` 注入（合成控零落盘）；"
                    "② `boundary_read_scan()` 改判 **AST 形态** —— 引用面 = 字面量命中族正则 **或** `_latest_boundary` **标识符**；"
                    "读取面 = `Attribute.attr ∈ READ_ATTRS`（`read_text`/`read_bytes`/`read`/`readline`/`readlines`）**或** `io.open(...)` 调用；"
                    "③ 两枚一并纳入 `PROXY_HELPERS_PINNED`（消费齿 = **t27** / **t21**）与 `PROXY_RESIDUAL_EXPLICIT`（残余显式：动态引用漏判 fail-closed / 非读取语境误判 fail-open；"
                    "字面量出现 ≠ 可产出 verdict），由 t29 覆盖面齿机判；④ t21 增 4 控、t27 增 3 控。**序不变（仍 50 次）/ 齿数不变（t01..t33 = 35 项）**。**R-CO216-1**。",
     "status": "CLOSED",
     "next": "凡**源面判据**（扫工具源以判声明/能力/读者身份者）一律以 **AST 形态/字面量**判，禁原文子串或原文正则；"
             "新增此类帮助函数须入 `PROXY_HELPERS_PINNED` + `PROXY_RESIDUAL_EXPLICIT`（承 R-CO215-1）。",
     "evidence": ["实测复现（内存、零落盘）：`'FAIL' in '# FAIL here'` = True（旧判据满足）；`boundary_read_scan('# w3_joint_assignment_boundary\\n# read_text\\n')` 旧 = True（注释伪造引用+读取）",
                  "修后实测：读取者集 = `BOUNDARY_SCAN_GUARDED ∪ BOUNDARY_READ_DECLARED`（5 步，与修前**逐字节同**）；`declared_verdict_in_tool` 真声明 = ok；"
                  "注释-only ⇒ 两面皆 False；字面量 ⇒ 命中；`base / suffix` 动态引用 ⇒ False（残余方向如实登记）",
                  "`--check` **t01..t33 全 True（35 项）**（t21/t27/t29 含新控）；`proxy_coverage_decision` = ok（3 枚帮助函数皆已登记）"],
     "refs": ["CO-187", "CO-192", "CO-194", "CO-202", "CO-215", "CO-216"], "closed_by": ["CO-216"]},
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
    note = ("；**CO-216（L2 自裁 · 源面判据之 AST 收窄（续））**：+1 TOOL_DEFECT（`co216:M-1` "
            "`declared_verdict_in_tool`（`v in src` ⇒ 注释即满足）与 `boundary_read_scan`（原文正则/子串 ⇒ 注释可伪造读者）"
            "⇒ 改判 AST 字面量/形态 + 两枚纳入 `PROXY_HELPERS_PINNED`/`PROXY_RESIDUAL_EXPLICIT`；low、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-216（L2 自裁 · 源面判据之 AST 收窄", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG), "n_items": len(reg["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
