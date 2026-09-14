#!/usr/bin/env python3
"""CO-233 — L2 自裁（状态齿与扰动实验协议之相容性）发现入册（幂等、注解原位）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
WHAT = ("**新增状态齿与扰动实验协议不相容**：CO-231/CO-232 之状态齿（t40 pin 行现值 == 实件、t41 boundary == 生成器输出）"
        "依赖派生件 boundary 之**现行一致态**，而序之**静态前置含全部齿**（`static_ok = all(checks)`）⇒ 扰动受控件即令 pin 与实件不符 ⇒ **序停机 rc=1**。"
        "实测：不动点 oracle case A（扰登记簿）⇒ `order_rc=1 / order_converged=false / restored=false` ⇒ oracle **FAIL**（`FAIL_FIXPOINT_PATH_DEPENDENT_OR_ABORT`）。"
        "该不相容**已存在于 `c1a880b`（CO-231）**（当时未复跑 oracle 故未现）。另：oracle 之 `finally` 只复原**受控件**、**未**复原**派生件** ⇒ 异常路径留 boundary stale（t40/t41 随即停机）。")
DISPO = ("CO-233（L2 自裁）：① oracle 每案**注入后**先 `_realign`（重跑 boundary 生成器）**再**跑序；② `finally` 复原受控件后**再 realign**（异常/中断路径亦不留 stale）；"
         "③ oracle 自声明 revision `CO-219 -> CO-232` 与 runner `TOOL_REVISION_DECLARED` **双侧同步**（t33 机判）；④ **R-CO233-1**。")
NEXT = ("凡**状态齿**（判据依赖受控件现行值者）**新增/修改**时，须**同 commit 复查与扰动实验（不动点 oracle）之相容性**：扰动后须先 realign 派生件再跑序，复原路径亦须 realign。"
        "**残余（未闭，界定）**：本件为相容性修正，不改 t40/t41 判据强度（规范态违例仍 fail-closed）；oracle 仍不扰动冻结四源/板/SPEC。")
ADD = [{"finding": "co233:F-1", "sev": "mid", "kind": "TOOL_DEFECT", "what": WHAT, "disposition": DISPO,
        "status": "CLOSED", "next": NEXT,
        "evidence": ["修前（本会话实测）：oracle case A `order_rc=1 / restored=false` ⇒ verdict `FAIL_FIXPOINT_PATH_DEPENDENT_OR_ABORT`",
                     "修后（本会话实测）：oracle **PASS**（5 案 `order_rc=0` 全复原、10 齿全 True、rc=0）",
                     "另实测异常路径：`_realign` 于 finally 之前崩溃 ⇒ boundary 留 stale ⇒ t40/t41 停机（已由 finally realign 修正）"],
        "refs": ["CO-195", "CO-219", "CO-231", "CO-232", "CO-233"], "closed_by": ["CO-233"]}]
NOTE = ("；**CO-233（L2 自裁 · 状态齿与扰动实验之相容性）**：+1 TOOL_DEFECT（`co233:F-1` 新增状态齿 t40/t41 与 oracle 扰动协议不相容 ⇒ 扰动后序停机 rc=1（含既存于 `c1a880b` 之态）；"
        "处置 = oracle 注入后 realign + finally realign + revision 双侧绑定 CO-232；mid、CLOSED）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def upsert_note(ub: str, mark: str, note: str) -> str:
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
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-233（L2 自裁", NOTE)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
