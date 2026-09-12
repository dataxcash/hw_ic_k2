#!/usr/bin/env python3
"""CO-164 — 收敛判定硬化（G-1）：规范复现序机判执行器（rc 优先，禁「sha 稳定即收敛」）。

性质：只改**登记簿**（L2 政策层）；执行器由 `p3_v57_co164_order_runner.py` 承载（不在规范序内，避免自递归）。
CLI: python3 tools/p3_v57_co164_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co164:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**规范复现序无 rc 机判执行器 ⇒ 「假收敛」**：收敛判定若只看 boundary/记录 sha，则某步**恒崩溃（rc≠0）**时，"
          "其产物不变的步骤（如 pin 再对齐）sha 恒不变 ⇒ 报 CONVERGED，而该步实际从未生效。实测事故（CO-163 期间）："
          "`p3_v57_co146_boundary_append.py` 因 §37 文本内 f-string 花括号语法错误每轮 rc=1 崩溃 ⇒ boundary 停在 v2.08、§37 未写入、"
          "pin 表陈旧（co77 = CITATION_MISMATCH、co135/co136 = FAIL），而「幂等循环」却报收敛；仅由一个独立 rc 复核发现。",
  "disposition": "CO-164：新增 `p3_v57_co164_order_runner.py`（**不在**规范序内运行，避免自递归；报告落 `.archer_tmp/`、**不被 boundary 引用**以免不动点）："
                 "① rc 策略 `EXPECTED_NONZERO = {co146_jlc_dfm_gate}`（verdict=FAIL 属预期），其余任一步非零 ⇒ **立即停机**并报门名/rc/stderr 尾；"
                 "② **真收敛** = rc 全合规 ∧ 受控 sha 逐轮稳定；③ `--check` 静态体检：步骤存在/可编译/rc 策略声明/判据灵敏度/序文本一致（t06）；"
                 "④ 端到端负控：把 co78 步替换为 rc=3 合成件 ⇒ abort（rc=1, iterations=1），**不报收敛**；⑤ t06 当场抓到「本文档序 vs 执行器 ORDER」"
                 "短别名漂移（`co159_rev19_review` → 实际步骤名），已修。",
  "status": "CLOSED", "next": "任何会话的收敛判定一律以本 runner（或至少逐步 rc==0 检查）为准；禁止以「sha 稳定」单独判收敛。",
  "evidence": ["CO-163 事故实测：boundary_append rc=1（SyntaxError）而幂等循环报 CONVERGED；boundary 停留 v2.08 / co77 CITATION_MISMATCH",
               "CO-164 负控：合成 rc=3 步 ⇒ abort(rc=1, iterations=1)；--check t01..t06 全 True（t06 抓到短别名漂移）"],
  "refs": ["CO-164", "CO-163", "CO-162", "CO-160", "CO-158"], "closed_by": ["CO-164"]},
]
MARK = ("；**CO-164（L2 自裁 · 收敛判定硬化）**：G-1 复现序无 rc 机判执行器 ⇒ 「恒崩溃步 + sha 稳定」被误判收敛（CO-163 期间实测事故）"
        "⇒ 新增 `p3_v57_co164_order_runner.py`：rc 策略（EXPECTED_NONZERO=DFM 闸）+ fail-fast + 真收敛（rc ∧ sha）+ `--check` t01..t06（含文档序↔执行器一致性）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
        patch = {k: v for k, v in it.items() if k != "id"}
        if f in have:
            have[f].update(patch); updated.append(f)
        else:
            reg["items"].append(dict(finding=f, **patch)); added.append(f)
    if MARK not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"register: +{len(added)} / upd {len(updated)} | counts={reg['meta']['counts']} | sha16 {s16(REG)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
