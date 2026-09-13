#!/usr/bin/env python3
"""CO-199 — **白名单 rc 类语义声明**（L2 自裁）：findings 入登记簿（幂等 upsert、注解**原位**）+ counts 复算。

F-1 = `EXPECTED_NONZERO` 只声明 `verdict`，**不声明预期 rc 值** ⇒ `allowlist_decision` 仅判 `rc != 0`：
白名单步以**任何**非零码退出（内部错误 / 参数错 / `sys.exit(2)` / 127）都被当「预期 FAIL」放行；
`why` 里的「rc=1」只是散文、无机判 ⇒ **rc 语义被架空**（「别的原因失败」不可与「预期判决」区分）。
只改登记簿。CLI: python3 tools/p3_v57_co199_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co199:F-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**白名单 rc 语义未声明**：`EXPECTED_NONZERO` 只声明 `verdict`（+ `record`/`teeth_path`），**不声明预期 rc 值** ⇒ "
             "`allowlist_decision()` 对白名单步仅判 `rc != 0` ⇒ **任何**非零退出（内部错误 / 参数错 / `sys.exit(2)` / 127）"
             "只要记录 verdict 与声明相符、无 Traceback、牙齿全 True 即被放行 ⇒ **rc 语义被架空**："
             "「因别的原因失败」与「预期判决 FAIL」不可区分（`why` 之『rc=1 即生效』为散文，无机判）。"
             "此前的收严（CO-165/167/176/185/193/194）都在**同一 rc 值域**内，未约束**值本身**。",
     "disposition": "CO-199（runner 升 **CO-199.1**）：① `EXPECTED_NONZERO` 每条须显式声明 `rc`（非零 int，= 该判决的"
                    "**规格化出口**）；② `allowlist_decision()` 增 `expected_step_rc_undeclared`（未声明）与 "
                    "`expected_step_rc_mismatch`（实际 rc ≠ 声明 rc）两停机类；③ `expected_nonzero_binding()` 增 `rc_not_declared`"
                    "（声明面完备性）；④ 静态齿 **t30**（正控 rc 匹配 + 负控 rc=2/127/0 与 rc 缺失）。红线 **R-CO199-1**。",
     "status": "CLOSED", "next": "白名单类豁免须逐项声明**语义出口**（rc 值等）；「非零 / 非 PASS」等**笼统判据**不得充当豁免边界。",
     "evidence": ["修前（实测）：`allowlist_decision('co146_jlc_dfm_gate', 2, '', 'FAIL', True, True)` 与 `... 127 ...` 均返回 "
                  "`expected_nonzero`（放行）—— 与 rc=1 不可区分",
                  "修后：rc=1 ⇒ `expected_nonzero`；rc=2 / 127 ⇒ `expected_step_rc_mismatch`；rc=0 ⇒ `expected_step_returned_zero`；"
                  "声明缺失/为零 ⇒ `rc_not_declared`；`--check` **t01..t30 全 True（32 项）**，收敛 rc=0（co146 步仍 rc=1 放行）"],
     "refs": ["CO-199", "CO-165", "CO-193", "CO-194"], "closed_by": ["CO-199"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


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
    note = ("；**CO-199（L2 自裁 · 白名单 rc 类语义）**：+1 TOOL_DEFECT（`co199:F-1`，low，CLOSED；runner 升 **CO-199.1** —— "
            "`EXPECTED_NONZERO` 须声明预期 rc 值 + `expected_step_rc_mismatch`/`expected_step_rc_undeclared` 停机类 + "
            "`rc_not_declared` 声明面完备性 + 静态齿 **t30**）。")
    _MARK = "；**CO-199（L2 自裁 · 白名单"
    _ub = reg["meta"].get("updated_by", "")
    if _MARK in _ub:                                   # 原位替换本段（R-CO197-4）
        _i = _ub.index(_MARK); _j = _ub.find("；**CO-", _i + len(_MARK))
        _ub = _ub[:_i] + note + (_ub[_j:] if _j != -1 else "")
    else:
        _ub = _ub + note
    reg["meta"]["updated_by"] = _ub
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
