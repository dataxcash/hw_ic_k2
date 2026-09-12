#!/usr/bin/env python3
"""CO-168 — 登记簿自洽性硬化：status 词汇 + `meta.counts` 复算（G-1/G-2）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.10）承载。
幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co168_register_consistency.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co168:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**登记簿 `status` 词汇未机判 ⇒ 未结项可静默落出 OPEN 计数**：`meta.counts[\"OPEN\"]` 与一切下游"
          "「OPEN ?」报告均为 `status == \"OPEN\"` 的**精确串匹配**；但无任何闸校验 `status` ∈ 合法词汇。"
          "实测：把任一项 `status` 改成 `open`/`Closed`（拼写/大小写错）⇒ co124 仍 **PASS / 0 findings**，"
          "而该项已静默不计入 OPEN（未结缺陷被算作已结）。handoff/§ 节引用的「OPEN 0」因此不可信。",
  "disposition": "CO-168：co124 增纯函数 `register_consistency(reg)` + 词汇 `REGISTER_STATUSES = (OPEN, CLOSED, PROVED)`；"
                 "任一项 status 不在词汇内 ⇒ `FAIL_REGISTER_STALE`（记录落 `register_stale`）+ 牙齿 T21/T21c。",
  "status": "CLOSED", "next": "新增登记状态须先入 `REGISTER_STATUSES`；拼写错误即 fail-closed。",
  "evidence": ["CO-168 实测（修前）：`status='open'`/`'Closed'` ⇒ co124 verdict PASS / unreg 0 / reg_bad []（静默）",
               "CO-168 复核（修后）：同注入 ⇒ `status_not_in_vocabulary`；真登记簿 `register_stale == []`"],
  "refs": ["CO-168", "CO-124", "CO-153", "CO-161"], "closed_by": ["CO-168"]},
 {"id": "G-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**`meta.counts` 为自述摘要、无闸据 `items` 复算**：各 disposition 工具各自 `Counter(kind)` + OPEN + total 重算，"
          "但没有任何闸把 `meta.counts` 与 `items` 复算结果比对。实测：把 `counts.total` 改 999、`counts.OPEN` 改 7 "
          "⇒ co124 仍 **PASS / 0 findings**（handoff §2/§8 与 boundary § 节把该摘要当权威引用）。",
  "disposition": "CO-168：`register_consistency` 追加判据 —— `meta.counts` 须与 `{{kind: n, OPEN: n, total: n}}` 复算结果"
                 "**键集与值逐项一致**，否则 `counts_not_rederived_from_items` ⇒ `FAIL_REGISTER_STALE`；牙齿 T21b。",
  "status": "CLOSED", "next": "任何写登记簿的步骤须在写后重算 `meta.counts`（现行 disposition 工具已如此）。",
  "evidence": ["CO-168 实测（修前）：`counts.total=999 / OPEN=7` ⇒ co124 verdict PASS（静默漂移）",
               "CO-168 复核（修后）：同注入 ⇒ `counts_not_rederived_from_items`；真登记簿复算逐项一致（71/OPEN 0）"],
  "refs": ["CO-168", "CO-124", "CO-152", "CO-165"], "closed_by": ["CO-168"]},
]
MARK = ("；**CO-168（L2 自裁 · 登记簿自洽性硬化）**：G-1 `status` 词汇无机判（拼写错 ⇒ 未结项静默落出 OPEN 计数）⇒ "
        "co124 `register_consistency` + `REGISTER_STATUSES` + T21/T21c；G-2 `meta.counts` 无闸据 items 复算（自述摘要可漂移）⇒ "
        "复算一致性判据 + T21b。co124 升 CO-124.10（40 牙齿）。")


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
