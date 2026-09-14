#!/usr/bin/env python3
"""CO-228 — L2 自裁（等长覆盖面名集等式 + kind 词表域钉定）发现入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co228:F-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**等长覆盖面隐含定义 + 两套页枚举无机判绑定**：SI 等长判定之**页覆盖面**由 `m13_v57_w3_joint_assignment.json`（**非冻结、非序内 watch**）之 `kind` 过滤隐含定义 —— "
             "① 未识别 kind 一律 `else: continue`（**静默跳过**）；② 与**冻结页清单** `m13_v57_s1_page_manifest.json`（`n_pages` = 34）之间**无机判绑定**；"
             "③ 两件 kind 词表不一致（清单 `refclk_pass` / 图纸 `refclk`）且无声明映射 ⇒ 覆盖面可**无声缩水**而 verdict 仍 PASS（fail-open；违 R-CO219-1 / R-CO225-1）。",
     "disposition": "CO-228（L2 自裁）：① **词表域钉定** `PAGE_KIND_VOCAB_DECLARED`（清单→图纸，**双向**）；② **名集等式**（冻结清单页集 == 图纸页集，双向 + `n_pages` 自述一致）；"
                    "③ **l5 端 fail-closed**（未识别 kind / 名集不等 ⇒ `SystemExit`，禁静默跳过与静默缩水）；④ 记录增期望页集 + 覆盖源指纹（图纸/清单 sha16 + 词表）；"
                    "⑤ 入机判 runner 静态齿 **t38_page_coverage_bound**（正/负控齐备）；⑥ 自声明面 bump（`L5-SI.11` / runner `CO-203.6`）。**R-CO228-1**。",
     "status": "CLOSED",
     "next": "覆盖面枚举面须与声明源做**双向名集等式 + 词表域钉定**，未识别枚举值禁静默跳过（承 R-CO219-1 / R-CO225-1 / R-CO227-1）。"
             "**残余（未闭）**：`m13_v57_w3_joint_assignment.json`（覆盖源）**非冻结源、亦不在序内 watch 名单** ⇒ 其**身份**无机判 pin（本件仅保证「页集 == 冻结清单页集」之不变量；"
             "内容变更而页集不变者不触发）⇒ 后续可将其纳入 watch 或每 rev 显式 pin。",
     "evidence": ["实件：两件 page_id 集完全相同（34/34，双向差集空）⇒ t38 PASS；`--check` 40/40",
                  "注入未识别 kind ⇒ l5 `SystemExit`（`未登记 kind ['weird_kind']`，记录零污染）",
                  "注入删一页 ⇒ l5 `SystemExit`（`冻结清单 34 vs 实测 33，清单独有 ['PCIE_REFCLK1/input']`，记录零污染）"],
     "refs": ["CO-45", "CO-62", "CO-219", "CO-225", "CO-228"], "closed_by": ["CO-228"]},
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
    note = ("；**CO-228（L2 自裁 · 等长覆盖面名集等式）**：+1 TOOL_DEFECT（`co228:F-1` SI 等长覆盖面隐含定义（未识别 kind 静默跳过）+ 与冻结页清单无机判绑定 ⇒ 覆盖面可无声缩水；"
            "处置 = 名集等式（双向）+ kind 词表域钉定 + l5 fail-closed + 静态齿 t38 + 记录覆盖源指纹；low、CLOSED；**残余**见该项 `next`）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-228（L2 自裁", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
