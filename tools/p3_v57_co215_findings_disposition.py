#!/usr/bin/env python3
"""CO-215 — 登记簿入册（幂等、注解**原位**）+ counts 复算。

入册 1 项（`TOOL_DEFECT` / low / CLOSED）：`co215:L-1` —— 代理帮助函数 `artifact_readers()` 之「源面判据过宽」
（按**原文子串**判 ⇒ **注释/散文即可满足**「该步读取该工件」），且该代理**未入** `PROXY_SEMANTIC_BINDING`（R-CO198-1）。
只改登记簿。CLI: python3 tools/p3_v57_co215_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co215:L-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**代理帮助函数之源面判据过宽（注释/散文即可满足）+ 该代理未登记**：`artifact_readers()` 判「某步**确实读取**该工件」时"
             "取**原文子串** `basename in src` ⇒ 源内仅一行**注释** `# x.md` 即使该式成真（实测复现）⇒ 与 **R-CO202-4**"
             "「源内**声明**须以 AST 字面量集判；注释/散文不得满足」**同源缺陷**；后果 = t26 `judgment_downstream_binding` 之 "
             "`refs_not_reading_artifact` 面（下游声明之**可执行性**）**可由散文满足**（方向 = **fail-open**：声明被误认为可执行）。"
             "又该代理**未入** `PROXY_SEMANTIC_BINDING`（R-CO198-1），历件仅以「有据延后」带过。",
     "disposition": "CO-215（L2 自裁）：① `artifact_readers()` 收窄为 **AST 字符串字面量集**（`_source_strings`）匹配 + glob 字面量匹配，"
                    "注释/散文一律不计；支持 `sources` 注入 ⇒ 牙齿合成控零落盘；② t26 增 **4 项控**（注释负控 / 路径字面量正控 / "
                    "glob 正控 / 动态构造如实登记）；③ **残余显式登记** `PROXY_RESIDUAL_EXPLICIT`（动态构造 ⇒ 漏判，方向 fail-closed；"
                    "非读取语境之字面量 ⇒ 误判为读者，方向 fail-open；**不宣称完备**）；④ **覆盖面机判**：`PROXY_HELPERS_PINNED` + "
                    "`proxy_coverage_decision()` 入 **t29** —— 每枚代理帮助函数须**恰**登记于 `PROXY_SEMANTIC_BINDING` 或 "
                    "`PROXY_RESIDUAL_EXPLICIT` 之一（互斥 + 完备覆盖本表），残余条目三字段须非空、消费齿须为本工具源内字面量。"
                    "**序不变（仍 50 次）/ 齿数不变（t01..t33 = 35 项，仅 t26/t29 内加控）**。**R-CO215-1**。",
     "status": "CLOSED",
     "next": "凡代理帮助函数须**恰**登记于 `PROXY_SEMANTIC_BINDING`（有外部语义判官）或 `PROXY_RESIDUAL_EXPLICIT`（残余显式 + 依据 + 触发 + 消费齿）之一，"
             "由覆盖面齿机判；**源面判据不得以原文子串判**（注释/散文不得满足，承 R-CO202-4）；残余不得宣称完备。",
     "evidence": ["实测复现（内存、零落盘）：`'m13_v57_s1_page_manifest.json' in '# m13_v57_s1_page_manifest.json'` = True（注释即满足）",
                  "修后实测：`artifact_readers(boundary_basename)` = 7 步（含 co77/co135），真声明 `judgment_downstream_binding('co146_boundary_append')` = **ok**；"
                  "注释-only 源 ⇒ `[]`；路径字面量 ⇒ 命中；glob 字面量（`x_*.md` ⊇ `x_v1.md`）⇒ 命中；`f'{pre}/x.md'` ⇒ `[]`（残余方向如实登记）",
                  "`--check` **t01..t33 全 True（35 项）**（t26/t29 含新控）；`proxy_coverage_decision(PROXY_HELPERS_PINNED, PROXY_SEMANTIC_BINDING, PROXY_RESIDUAL_EXPLICIT)` = ok"],
     "refs": ["CO-193", "CO-198", "CO-202", "CO-215"], "closed_by": ["CO-215"]},
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
    note = ("；**CO-215（L2 自裁 · 代理帮助函数源面收窄 + 覆盖面机判）**：+1 TOOL_DEFECT（`co215:L-1` "
            "`artifact_readers` 源面判据过宽（注释即可满足）⇒ 收窄为 AST 字面量 + `PROXY_RESIDUAL_EXPLICIT` 残левиз登记 + t29 覆盖面齿；low、CLOSED）。")
    note = note.replace("残левиз登记", "残余显式登记")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-215（L2 自裁 · 代理帮助函数源面收窄", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG), "n_items": len(reg["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
