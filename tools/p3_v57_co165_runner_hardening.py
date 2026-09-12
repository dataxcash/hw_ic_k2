#!/usr/bin/env python3
"""CO-165 — 收敛执行器自加固（G-1 白名单证据不足 / G-2 受控 sha 盲区）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co164_order_runner.py`（CO-164.2）承载。
CLI: python3 tools/p3_v57_co165_runner_hardening.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co165:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**CO-164 执行器的白名单只按 rc 放行 ⇒ 崩溃可伪装成「预期 FAIL」**：`EXPECTED_NONZERO` 仅以 `rc≠0` 判定，"
          "故白名单步（当前仅 `co146_jlc_dfm_gate`）的任何非零——含语法错误崩溃、静默失败——都被当预期结果放行。"
          "实测（负控）：把 DFM 闸替换为 `raise SystemExit(\"boom\")`（rc=1、stderr 无 traceback）⇒ 旧判据**放行**。"
          "第一次加固（仅检测 Traceback）**仍不足**：不打印 traceback 的失败会让盘上**陈旧**的 FAIL 记录充当 verdict 证据 ⇒ "
          "由本会话自己的端到端负控当场证伪。",
  "disposition": "CO-165：执行器升 **CO-164.2** —— 白名单项改为 `{verdict, record, why}` 并新增纯判据 "
                 "`allowlist_decision(step, rc, stderr, verdict, record_fresh)`：白名单步须 **rc≠0 ∧ 无 Traceback ∧ 记录由本次执行产出（mtime 新鲜）"
                 "∧ 记录 verdict == 声明 verdict** 方能判 `expected_nonzero`；其余分别判 `expected_step_returned_zero` / "
                 "`expected_step_crashed` / `expected_step_record_not_produced` / `expected_step_verdict_mismatch` 并**立即停机**；"
                 "`--check` 增 t07（四类伪通过的负控 + 恒真路径正控）。",
  "status": "CLOSED", "next": "白名单步一律须给出「verdict + 记录由本次执行产出」证据；新增白名单须登记期望 verdict 并由 t07 覆盖。",
  "evidence": ["CO-165 负控 A：DFM 步换 `SystemExit(\"boom\")` ⇒ 旧判据放行；加固后 abort（class=expected_step_record_not_produced）",
               "CO-165 正控：真 DFM 闸（重写记录、verdict=FAIL）⇒ 判 expected_nonzero，整体 run converged"],
  "refs": ["CO-165", "CO-164", "CO-158"], "closed_by": ["CO-165"]},
 {"id": "G-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**CO-164 执行器的受控 sha 清单过窄**：`WATCH` 仅 7 件（boundary + 4 记录 + 台账 + 登记簿），漏 `co106`/`co150`/打样包件（MANIFEST/ORDER_NOTES）"
          "等产物 ⇒ 未受控文件若出现 2-循环或抖动，收敛判定**看不见**。",
  "disposition": "CO-165：`watch_paths()` 改为覆盖 boundary + **全部** `m13_v57_co*.json` 记录 + 台账/登记簿 + 打样包 `MANIFEST.json`/`ORDER_NOTES.md`；"
                 "`--check` 增 t08（受控集须覆盖记录类产物，含 co106 与 MANIFEST）。",
  "status": "CLOSED", "next": "新增会写產物的步骤须确保其产物在 `watch_paths()` 覆盖范围内。",
  "evidence": ["CO-165：`watch_paths()` 覆盖 ≥20 件（含 co106 记录与打样包 MANIFEST）；t08=True"],
  "refs": ["CO-165", "CO-164"], "closed_by": ["CO-165"]},
]
MARK = ("；**CO-165（L2 自裁 · 收敛执行器加固）**：G-1 白名单只按 rc 放行 ⇒ 崩溃/静默失败可伪装预期 FAIL（含「陈旧 verdict 充当证据」二次漏洞）"
        "⇒ CO-164.2 `allowlist_decision` 要求 verdict + 记录由本次执行产出；G-2 受控 sha 仅 7 件 ⇒ `watch_paths()` 覆盖全部记录类产物；`--check` 增 t07/t08。")


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
