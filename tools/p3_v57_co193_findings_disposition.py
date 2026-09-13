#!/usr/bin/env python3
"""CO-193 — **声明↔实现绑定的可执行性**（L2 自裁）：findings 入登记簿（幂等 upsert）+ counts 复算。

来源 = z57 §6.2 指定的 L2 续扫（`JUDGMENT_DOWNSTREAM` ref 可执行性 / 白名单声明↔工具 rc 语义静态绑定）。
只改 `L2/input_defect_register_v1.json`。
CLI: python3 tools/p3_v57_co193_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ITEM_REF = "CO-193（runner 升 **CO-193.1**）"
ADD = [
    {"finding": "co193:G-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "`JUDGMENT_DOWNSTREAM` 下游声明**只查形状**（`why` 非空 + `ref` 非空 list + `ref ⊆ ORDER`）⇒ "
             "**方向**（ref 须在序内晚于声明步）与**可执行性**（ref 步工具须确实引用被judged工件）无机判。"
             "任一步可被声明为「由下游判」而实际无任何步判它 ⇒ 该步静默逃逸 t25（CO-191「禁静默步」的目的被绕过）。",
     "disposition": ITEM_REF + "：`JUDGMENT_DOWNSTREAM` 每条增 `artifact`（被judged工件 basename）；新增纯函数 "
                    "`downstream_refs_after()`（多次出现**存在性**方向判据）与 `judgment_downstream_binding()`"
                    "（缺件/方向错/ref 不引用工件 ⇒ fail-closed）；`artifact_readers()` 为**语法代理**（basename 字面 **或** "
                    "可 `fnmatch` 命中的 glob，如 co77 经 `…_v1_*.md` 定位最新版）；静态齿 **t26**。",
     "status": "CLOSED", "next": "新增/修改下游声明须过 t26（方向 + 可执行 + 完整）；否则停机。",
     "evidence": ["实测（修前）负控：ref 改为上游步 `co146_impedance_table`（位 0，声明步位 37/40/49）⇒ 旧 t25 仍 True（漏）",
                  "实测（修前）负控：ref 改为不引用 boundary 的 `co136_gate_hygiene` ⇒ 旧 t25 仍 True（漏）",
                  "实测（修后）：真声明 `judgment_downstream_binding`=ok；方向错=refs_not_downstream；不引用=refs_not_reading_artifact；缺 artifact=declaration_incomplete（t26 合成控）",
                  "实现期自捕获：`artifact_readers` 初版按 basename 子串匹配 **漏 co77**（其经 glob 定位）⇒ 改 glob-aware 后 co77 计入（否则真声明被误判 refs_not_reading_artifact）"],
     "refs": ["CO-193", "CO-191", "CO-187"], "closed_by": ["CO-193"]},
    {"finding": "co193:G-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "`EXPECTED_NONZERO` 证据声明未**本步绑定**：`record` 只须 ∈ `watch_paths()`（t09）而**不须** ∈ `STEP_ARTIFACTS[step]` ⇒ "
             "声明的证据记录可指向**他步**产物（步本地归因/新鲜度测错件）；`teeth_path` 只须键存在（t14）而不须在记录内**可解析** ⇒ "
             "声明坏 key 时自检牙齿判据静默降级（`_tcand` 过滤 None 后回落到 `step_declared_teeth`）。二者均属声明↔实现脱钩。",
     "disposition": ITEM_REF + "：新增纯函数 `expected_nonzero_binding()` —— `record` 须 ∈ `STEP_ARTIFACTS[step]`、"
                    "`teeth_path` 须经 `record_json_path()` **可解析**（否则 `teeth_path_unresolved`）；并入静态齿 **t26**。",
     "status": "CLOSED", "next": "白名单证据须指向**本步**声明产物且 `teeth_path` 可解析；否则停机。",
     "evidence": ["实测（修前）负控：`record` 改指 `m13_v57_co146_impedance_table.json` ⇒ 旧 t09 仍 True（漏）",
                  "实测（修后）：`record_not_step_artifact`；`teeth_path=['nope']` ⇒ `teeth_path_unresolved`（t26 合成控）",
                  "现行基线：co146_jlc_dfm_gate `record` ∈ 本步 3 件声明产物、`teeth_path=['teeth']` 可解析 ⇒ ok（零基线冲击）"],
     "refs": ["CO-193", "CO-176", "CO-165"], "closed_by": ["CO-193"]},
    {"finding": "co193:G-3", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "CO-192 复评件 `m13_v57_co192_rev19_co187_co191_review.json` 在 `as_found` 内嵌**处置态** sha "
             "`runner_current_sha16` ⇒ 该 controlled 证据件的内容随 runner 变更漂移。实测：CO-193 改 runner 后，同一复评命令重跑得"
             "**另一记录 sha**（`db887764c8693176` → `2e43deda4f73fd76`），而该 sha 已被 boundary §65 pin 表引用 ⇒ 复跑即令 §65 "
             "引用失配（须再跑 boundary_append 重 pin）。违 **CO-152 已闭规则**「新记录不得再嵌下游 sha 快照；跨件现行 sha 一律走 "
             "boundary pin 表」= 已闭缺陷类 `records_snapshot_downstream_sha_causes_pin_drift` 的**复发**。",
     "disposition": "CO-193：复评件回归 **as-found 证据**语义 —— 移除 `runner_current_sha16`（只留 `runner_as_found_sha16`）；"
                    "处置态现行 sha 由 boundary pin 表单点承载。改后复评命令**幂等**（连跑两遍记录逐字节相同 `b58a374c337d75e8`）。",
     "status": "CLOSED", "next": "证据/复评件只钉**被评对象**（as-found）；现行 sha 一律由 boundary pin 表承载，禁内嵌。",
     "evidence": ["实测（修前）：重跑 CO-192 复评件 ⇒ 记录 sha db887764c8693176 → 2e43deda4f73fd76（漂移）",
                  "实测（修后）：连跑两遍记录 sha 恒为 `b58a374c337d75e8`（与 runner 当前值无关）",
                  "同类先例：`tool_defect:records_snapshot_downstream_sha_causes_pin_drift`（CLOSED @ CO-152）"],
     "refs": ["CO-193", "CO-192", "CO-152", "CO-151"], "closed_by": ["CO-193"]},
    {"finding": "co193:G-4", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "co120 `_is_downstream_snapshot()` 只识别 `*_sha16_after` + `register/ledger` 命名面 ⇒ **显式现行态键** "
             "（`*_current_sha16` / `*_sha16_current` / `*_live_sha16` …）漏判。该判据正是 CO-152 为「禁复发」而设的守卫，"
             "盲区使 G-3 得以再犯（`as_found.runner_current_sha16` 逃逸 co120 扫描，corpus 实测仅此 1 处命中）。",
     "disposition": "CO-193（co120 升 **CO-120.6**）：新增 `_DOWNSTREAM_LIVE_KEY_RE` 覆盖显式现行/时点语义键；新增负控"
                    "（`as_found.runner_current_sha16` 必被截）、正控（`SNAPSHOT_DECLARED` 声明放行）与**对偶正控**"
                    "（`inputs.spec_sha16` / `board_sha16` 等**上游输入 pin 不得误报**）。**残余如实登记**：判据为**键名启发式**，"
                    "改名（如 `*_state_sha16`）仍可逃逸 ⇒ 触发 = 出现「记录随文档化复现序漂移」事件时收为语义判据。",
     "status": "CLOSED", "next": "下游快照键新增命名形态须先入 co120 判据 + 合成控；未声明一律 FAIL。",
     "evidence": ["corpus 全扫：显式现行态键仅 1 处 = G-3（修 G-3 后 0 处）",
                  "co120.6 teeth 全 True：`negative_control_live_state_snapshot_caught` / `positive_control_declared_live_snapshot_passes` / `positive_control_upstream_input_pin_not_snapshot`",
                  "co120.6 verdict=PASS、`n_snapshot_undeclared`=0"],
     "refs": ["CO-193", "CO-152", "CO-156", "CO-159"], "closed_by": ["CO-193"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    have = {i["finding"] for i in reg["items"]}
    added = [it["finding"] for it in ADD if it["finding"] not in have]
    reg["items"] += [it for it in ADD if it["finding"] not in have]
    note = ("；**CO-193（L2 自裁 · 声明↔实现绑定的可执行性）**：+4 TOOL_DEFECT（`co193:G-1..G-4`，全 CLOSED；"
            "runner 升 CO-193.1 —— `JUDGMENT_DOWNSTREAM` 方向+可执行机判、`EXPECTED_NONZERO` 证据本步绑定、静态齿 t26；"
            "复评件回归 as-found 语义（去处置态 sha）；co120 升 CO-120.6 补现行态键判据+对偶控）。")
    if "CO-193（L2 自裁 · 声明↔实现绑定" not in reg["meta"].get("updated_by", ""):
        reg["meta"]["updated_by"] = reg["meta"].get("updated_by", "") + note
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "counts": reg["meta"]["counts"], "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
