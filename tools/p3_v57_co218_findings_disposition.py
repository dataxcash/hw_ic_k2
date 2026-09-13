#!/usr/bin/env python3
"""CO-218 — 登记簿入册（幂等、注解**原位**）+ counts 复算。

入册 1 项（`TOOL_DEFECT` / low / CLOSED）：`co218:O-1` —— **冻结源不变性 + 规则源唯一性**在规范序内**无机判**
（跨会话仅由人手复核；CO-91.2 之 K2↔容器 `drc_rules` 同字节断言为一次性）⇒ 源漂移不使序失败、判定基据失锚。
只改登记簿。CLI: python3 tools/p3_v57_co218_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co218:O-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**冻结源不变性 + 规则源唯一性未入机判（判定基据失锚）**：冻结四源（`SPEC_k2_v4.spec-rev-19.json` / "
             "`m13_v57_s1_page_manifest.json` / 冻结板 `k2_v4_8L.kicad_pcb` / `_shared/eda_core/drc_rules.json`）之**不变性**，"
             "跨会话仅由**人手复核**（各件「写件时复核」之「4/4 MATCH」）+ **CO-91.2 之一次性断言**（K2 ↔ 容器 `drc_rules.json` 同字节）承载；"
             "规范序内**无任何步机判** ⇒ 源漂移**不使序失败**（序只消费当下内容，仍可收敛，boundary 亦仍可写「4/4」）⇒ 全部下游判据失去锚点。"
             "**可达性**：K2 副本 `_shared/eda_core/drc_rules.json` 为**可写**（`-rw-rw-r--`）而容器副本**只读**（`-r--r--r--`）"
             "⇒ 「单向漂移」路径真实存在（改 K2 副本即改 K2 各闸所读规则，而冻结 pin 仍指容器副本）。",
     "disposition": "CO-218（L2 自裁）：runner 增 ① `FROZEN_SOURCES`（4 源 → sha16 pin）+ `FROZEN_SRC_COPIES`（K2 ↔ 容器 `drc_rules` 同字节）；"
                    "② 纯判据 `frozen_sources_decision()`（`sha16_of`/`bytes_of` 可注入 ⇒ 合成控零落盘；返回 `ok`/`frozen_source_missing`/`frozen_source_drift`/`rule_source_not_unique`）；"
                    "③ **静态齿 t34**（缺件 / 漂移 / 副本不同字节 ⇒ 序停机 `static_precheck_failed`，fail-closed）；"
                    "④ 报告增 `frozen_sources` 证据块（逐源 pin/actual + 副本 `identical`）。**齿数 35 → 36（t01..t34）**；**序不变（仍 50 次）**。"
                    "**边界（诚实）**：本齿只锚**冻结源**（输入）；**交付板** `k2_v4_8L.l4.kicad_pcb` 属**产物**（随 rev 合法变更；CO-144 曾改板）⇒ **不**入冻结 pin，"
                    "其「本 rev 内不变」由 co120 P5 + 各记录板指纹 + 人手复核承载。**R-CO218-1**。",
     "status": "CLOSED",
     "next": "凡「判定基据之锚点」（冻结输入 / 规则源 / 唯一性断言）须**入规范序机判**（fail-closed），不得仅以人手复核或一次性断言承载；"
             "源之**唯一性**（多副本）须机判同字节；**产物**（随 rev 变更者）不得混入冻结 pin。",
     "evidence": ["修后实测：`frozen_sources_decision(FROZEN_SOURCES, …)` = **ok**；4/4 pin 命中（SPEC `5f72182a2616392c` / 清单 `a8ef3ea8ecff99d7` / 冻结板 `fb07d25ac426ff84` / 规则 `0a459839e15960b8`）；K2 ↔ 容器副本 `identical=True`",
                  "判别力（独立探针，内存注入）：错 pin ⇒ `frozen_source_drift`；伪造副本字节 ⇒ `rule_source_not_unique`；缺件（注入 OSError）⇒ `frozen_source_missing`",
                  "`--check` **36/36 全 True**（t34 = `t34_frozen_sources_pinned`）；报告含 `frozen_sources` 证据块"],
     "refs": ["CO-91", "CO-91.2", "CO-217", "CO-218"], "closed_by": ["CO-218"]},
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
    note = ("；**CO-218（L2 自裁 · 冻结源不变性 + 规则源唯一性入机判）**：+1 TOOL_DEFECT（`co218:O-1` 冻结四源不变性与 "
            "K2↔容器 `drc_rules` 同字节原仅人手/一次性断言承载 ⇒ runner 增 `FROZEN_SOURCES`/`FROZEN_SRC_COPIES`/`frozen_sources_decision()` + 静态齿 **t34**"
            "（缺件/漂移/副本不同字节 ⇒ 停机）+ 报告证据块；齿数 35→36；low、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-218（L2 自裁 · 冻结源不变性", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG), "n_items": len(reg["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
