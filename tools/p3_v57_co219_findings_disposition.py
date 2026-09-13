#!/usr/bin/env python3
"""CO-219 — 登记簿入册（幂等、注解**原位**）+ counts 复算。

入册 2 项（皆 `TOOL_DEFECT` / low / CLOSED）：
`co219:F-1` 覆盖面表/锚点表/消费面枚举表**未名集钉定** ⇒ 删项即**空真**（frozen_sources_decision / proxy_coverage_decision /
l5_board_binding 皆只遍历已登记项；实测删 SPEC pin 后注入漂移仍返 `ok`）；
`co219:F-2` 不动点 oracle **前置未达不阻断 + `sha_canon` 重锚污染态 + 污染不自愈**（实测致 co124 FAIL_REGISTER_STALE）。
只改登记簿。CLI: python3 tools/p3_v57_co219_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co219:F-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**覆盖面/锚点/消费面三表未名集钉定 ⇒ 删项即空真（fail-open）**：`frozen_sources_decision()`（CO-218）、"
             "`proxy_coverage_decision()`（CO-215）、`l5_board_binding()`（CO-214）皆**只遍历已登记项** ⇒ `FROZEN_SOURCES={}`、"
             "**删单枚 pin**（如期 CO-217 之 SPEC pin）、`PROXY_HELPERS_PINNED={}`、`L5_RECORD_JSON={}` 时对应齿仍 **True**。"
             "**可达性后果（实测）**：删 SPEC pin 后**注入 SPEC 漂移仍返回 `ok`** ⇒ 该源之不变性**检出率归零**（静默失锚）；"
             "此即 CO-215/216 所修「近乎空真」之**表级上一层**。同档 t27（`set(BASIS_JUDGE_DECLARED) == {…}`）、"
             "t21（读者集等式）、t16（齿集 pin）已有该制 ⇒ 三处为**遗漏**（t34 之负控甚至把空表 `ok` 写死为期望）。",
     "disposition": "CO-219（L2 自裁）：三表各加**名集等式**（**不新增齿**）：t29 增 `set(PROXY_HELPERS_PINNED) == {3 枚}` + "
                    "`set(PROXY_RESIDUAL_EXPLICIT) == set(PROXY_HELPERS_PINNED)`；t34 增 `set(FROZEN_SOURCES) == {4 源}` + "
                    "`set(FROZEN_SRC_COPIES) == {1 对}`；co120 P5 之 `teeth_ok` 增 `set(L5_RECORD_JSON) == {2 记录}`。"
                    "自声明面同 commit bump：runner **CO-203.1 → CO-203.2**、co120 **CO-120.7 → CO-120.8**。**R-CO219-1**。",
     "status": "CLOSED",
     "next": "凡**覆盖面 / 判定基据锚点 / 消费面**之**枚举表**，须以**名集（或集合）等式**机判其内容；"
             "不得以「已登记项自洽」代替「登记面完整」（纯判据对空表返 `ok` 属合理设计，但**齿**须钉实表内容）。",
     "evidence": ["修前（内存注入、零落盘）：空 `FROZEN_SOURCES` / 删 SPEC pin / 空 `FROZEN_SRC_COPIES` ⇒ t34 **True**；空 `PROXY_HELPERS_PINNED` ⇒ t29 **True**；空 `L5_RECORD_JSON` ⇒ 仅余 1 行且 `all_ok=True`",
                  "修前检出率归零：pin 在 ⇒ 漂移注入 = `frozen_source_drift`；pin 删 ⇒ 同注入 = `ok`",
                  "修后（同法重放）：五注入**全部** ⇒ 对应齿 **False**；`--check` **36/36 全 True**；co120 PASS（teeth=True）；序收敛 rc=0"],
     "refs": ["CO-214", "CO-215", "CO-216", "CO-218", "CO-219"], "closed_by": ["CO-219"]},
    {"finding": "co219:F-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**不动点 oracle 前置未达不阻断 + 基线重锚 + 污染不自愈**：`t00`（先结算）不成立时仍注入/度量，且 `sha_canon` 取自"
             "**当下（污染）态**（实测 `914b65197ad76b19`，as-found 记录为 `3b02b97dc9f1f4bc`）⇒ 记录把非规范态**重锚为 canonical**；"
             "逐案 `finally` 只复原到**案前（污染）态**（`saved`）⇒ 污染在工具内**不自愈**。实证：该次运行后某已闭合登记项被重开为 OPEN "
             "而 `meta.counts.OPEN=0` ⇒ **co124 随即 FAIL_REGISTER_STALE**（`T21c=false`），人工复原 HEAD 后全绿。"
             "**诚实边界**：污染态之上游写入者**未根因定位**（疑并发/带外写者与 oracle 交叠）⇒ 只据**可复现之工具行为**立据。",
     "disposition": "CO-219（L2 自裁）：oracle 增**前置 fail-fast** —— t00 不成立即落 `verdict=FAIL_SETTLE_NOT_CONVERGED` + "
                    "`aborted_case=precondition_settle_not_converged` + `how_to_recover`（先收敛或先复原再重跑），**不注入、不度量、不重锚**，rc=1。"
                    "自声明面同 commit bump：oracle **CO-202 → CO-219**（runner `TOOL_REVISION_DECLARED` 双侧同步 ⇒ t33 仍 True）。**R-CO219-2**。",
     "status": "CLOSED",
     "next": "**先结算**类前置（不动点/收敛类判据）须**fail-closed 阻断**：前置不成立即停（不注入、不度量、不落基线），"
             "并给出**复原指引**；禁以污染态充当 canonical（否则记录自身把污染合法化）。",
     "evidence": ["实测（污染态）：t00=False 仍走完 case A 并落记录；`sha_canon` 914b65197ad76b19 ≠ as-found 3b02b97dc9f1f4bc；register 落于「OPEN 项 + counts.OPEN=0」不自洽态",
                  "复原 HEAD 后重跑：oracle **PASS 11/11 齿**；`--check` 36/36；diff 空（幂等）",
                  "修后判据：t00 不成立 ⇒ 早期返回（cases=[]、verdict=FAIL_SETTLE_NOT_CONVERGED、rc=1）"],
     "refs": ["CO-195", "CO-202", "CO-219"], "closed_by": ["CO-219"]},
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
    note = ("；**CO-219（非执行者对抗复评 CO-213..CO-218 + 同会话处置）**：+2 TOOL_DEFECT（`co219:F-1` 覆盖面/锚点/消费面三表"
            "**未名集钉定 ⇒ 删项即空真**（实测删 SPEC pin 后漂移检出率归零）⇒ 三表加**名集等式**（不新增齿），runner CO-203.2 / co120 CO-120.8；"
            "`co219:F-2` 不动点 oracle **前置未达不阻断 + 基线重锚**（实测致 co124 FAIL_REGISTER_STALE）⇒ 增**前置 fail-fast**，oracle CO-219；皆 low、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-219（非执行者对抗复评", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG), "n_items": len(reg["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
