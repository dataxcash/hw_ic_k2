#!/usr/bin/env python3
"""CO-169 — 收敛判据硬化：**逐步产物产出证据**（非白名单步 rc==0 亦须写出受控产物）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co164_order_runner.py`（CO-169.1）承载。
幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co169_step_output_oracle.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co169:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**收敛执行器只对白名单步证明「做了事」⇒ 静默 no-op 步被收敛背书**：CO-165/CO-167 的「记录由本次执行产出」"
          "（`record_refreshed` 变更检测）**只作用于 `EXPECTED_NONZERO` 白名单步**；其余 36 步的契约仅为 `rc == 0`。"
          "一个**不崩也不写**的步（早退分支、漏写、被改成只读检查）会因产物 sha 不变而被「sha 稳定 ⇒ 收敛」背书 —— "
          "与 CO-164 的假收敛同族，但故障类相反（CO-164 = 崩而 sha 不变；本项 = 不崩而不写）。",
  "disposition": "CO-169：执行器增纯判据 `step_did_work(before, after)`（受控产物集 `watch_paths()` 的 mtime_ns 快照，"
                 "前进/新增/删除任一即算做事）+ `zero_rc_class`；运行循环逐步取受控快照，`rc==0` 而**零产物变动** ⇒ "
                 "类 `step_wrote_nothing` 并**立即停机**；报告内逐步落 `did_work` 证据；`--check` 增 **t11**（判据正/负控）。",
  "status": "CLOSED", "next": "新增规范序步骤须确保其至少写出一个受控产物（`watch_paths()` 覆盖内）；纯只读步骤应登记豁免而非默认放行。",
  "evidence": ["CO-169 实测（修前）：37 步探针显示每步均有产物刷写，但判据仅白名单步受检 ⇒ 合成「rc=0 不写」步旧判据判 `ok`",
               "CO-169 实测（修后）：同合成步 ⇒ `step_wrote_nothing` 停机；真序 37 步 `did_work` 全 True，run converged"],
  "refs": ["CO-169", "CO-164", "CO-165", "CO-167"], "closed_by": ["CO-169"]},
]
MARK = ("；**CO-169（L2 自裁 · 收敛判据硬化）**：G-1 白名单外诸步仅以 `rc==0` 为契约 ⇒ 静默 no-op 步（不崩也不写）会被「sha 稳定」背书 "
        "⇒ 执行器增 `step_did_work`（受控产物 mtime_ns 快照）+ `zero_rc_class`，`rc==0` 且零产物变动 ⇒ `step_wrote_nothing` 停机；"
        "报告落逐步 `did_work`；`--check` 增 t11。执行器升 CO-169.1。")


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
