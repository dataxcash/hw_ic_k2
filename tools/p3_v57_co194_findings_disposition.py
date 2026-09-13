#!/usr/bin/env python3
"""CO-194 — **基据↔判官 + 声明↔工具能力**（L2 自裁）：findings 入登记簿（幂等 upsert）+ counts 复算。

来源 = z58 §6.2 指定的 L2 续扫（`judgment_basis` 的 `register_consistency` 隐式依赖 / 白名单 rc 语义的静态绑定）。
只改 `L2/input_defect_register_v1.json`。
CLI: python3 tools/p3_v57_co194_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ITEM_REF = "CO-194（runner 升 **CO-194.1**）"
ADD = [
    {"finding": "co194:H-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**基据类别无判官绑定（latent）**：`judgment_basis()` 的 `register_consistency` 类别仅凭 `_REG ∈ STEP_ARTIFACTS[step]` 认定，"
             "**未绑定任何判官**（登记簿自洽实际由 co124 机判）。实测：该分支当前**不可达**（27 个写登记簿步皆先命中 `verdict` ⇒ 死码）；"
             "但一旦可达（某步只写登记簿而无 teeth/verdict），其基据即 `register_consistency` 而**无任何步**保证登记簿自洽被机判 ⇒ "
             "t25「每步须有可机判基据」可被**空真**满足。R-CO191-1 已把「登记簿自洽」列为合法基据，故须绑定其判官。",
     "disposition": ITEM_REF + "：新增 `BASIS_JUDGE_DECLARED`（每基据类别显式声明判定机制；外部判官须在序内、须**读**被judged件、"
                    "且**自身有机判基据**）+ 纯函数 `basis_judge_decision()` + 静态齿 **t27**（正控 + 判官不在序/不读件/自身无基据/声明不完整 负控）。"
                    "`register_consistency` 判官 = `co124_input_selfcheck_gate`（读 `input_defect_register_v1.json`，自身基据 = teeth）。",
     "status": "CLOSED", "next": "新增基据类别须先入 `BASIS_JUDGE_DECLARED` 并过 t27；外部判官须可执行（在序/读件/自身有基据）。",
     "evidence": ["实测（修前）：`judgment_basis` 分布 = {teeth:19, verdict:28, downstream:1, register_consistency:0} ⇒ 该分支死码",
                  "实测（修前）：把 co124 移出 ORDER 后 `all(basis != none)` 仍 True ⇒ 无判官亦成立（基据空真面）",
                  "实测（修后）：`register_consistency` 判官 co124 在序、`artifact_readers('input_defect_register_v1.json')` 含 co124、`judgment_basis(co124)`=teeth ⇒ `basis_judge_decision`=ok（t27）"],
     "refs": ["CO-194", "CO-191", "CO-168"], "closed_by": ["CO-194"]},
    {"finding": "co194:H-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**白名单声明与工具能力无静态绑定**：`EXPECTED_NONZERO` 的 `verdict` 声明只受形状约束（非 PASS + 与运行期记录一致），**不要求**该 verdict "
             "字面出现在该步**工具源**内 ⇒ 声明可指向工具**不可能产出**的 verdict。实测：伪造 `verdict=TOTALLY_BROKEN` / `ERROR` ⇒ 旧静态条款"
             "（t03/t07/t09/t14）**全过**（仅运行期以 `expected_step_verdict_mismatch` fail-closed ⇒ 声明面未绑定、诊断滞后）。",
     "disposition": ITEM_REF + "：新增纯函数 `declared_verdict_in_tool()`（声明 verdict 字面须 ∈ 该步工具源）+ 静态齿 **t27** 负控"
                    "（`TOTALLY_BROKEN` 必须 False）。现行基线 co146_jlc_dfm_gate 工具源含 `FAIL` ⇒ ok（零基线冲击）。",
     "status": "CLOSED", "next": "白名单 verdict 声明须能在其工具源内找到（声明↔能力绑定）；变更须过 t27。",
     "evidence": ["实测（修前）：伪造 `verdict=TOTALLY_BROKEN` ⇒ 形状/证据/牙齿三条静态条款全过 = True（无绑定）",
                  "实测（修后）：`declared_verdict_in_tool('co146_jlc_dfm_gate', {'verdict':'FAIL'})`=True、`{'verdict':'TOTALLY_BROKEN'}`=False（t27）"],
     "refs": ["CO-194", "CO-165", "CO-167"], "closed_by": ["CO-194"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    have = {i["finding"] for i in reg["items"]}
    added = [it["finding"] for it in ADD if it["finding"] not in have]
    reg["items"] += [it for it in ADD if it["finding"] not in have]
    note = ("；**CO-194（L2 自裁 · 基据↔判官 + 声明↔工具能力）**：+2 TOOL_DEFECT（`co194:H-1/H-2`，全 CLOSED；"
            "runner 升 CO-194.1 —— `BASIS_JUDGE_DECLARED` + `basis_judge_decision()` + `declared_verdict_in_tool()` + 静态齿 t27）。")
    if "CO-194（L2 自裁 · 基据↔判官" not in reg["meta"].get("updated_by", ""):
        reg["meta"]["updated_by"] = reg["meta"].get("updated_by", "") + note
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "counts": reg["meta"]["counts"], "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
