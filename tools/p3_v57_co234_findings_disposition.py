#!/usr/bin/env python3
"""CO-234 — L2 自裁（pin 面对受控集之覆盖面入机判）发现入册（幂等、注解原位）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
WHAT = ("**受控集之 pin 覆盖面无机判齿 ⇒ 件可静默漏钉**：受控集（`STEP_ARTIFACTS` ∪ `ORDER_MD_PRODUCTS`）虽已声明，但「哪件**应有** pin」从无机判。"
        "实测（本会话只读）：**43 件**受控产物中 **8 件**在 boundary pin 面**无任何 pin** —— 7 枚 `.md` 卡片（CO124/CO150/CO159/CO172/co146_impedance_table/co146_jlc_dfm_gate/co146_pm_eval）"
        "与 **`m13_v57_co77_closure_declaration_sweep.json`**（**收口扫描记录**，判定性产物）。承 R-CO219-1 枚举面名集等式 / R-CO225-1「无机判齿即空真」/ R-CO230-1。")
DISPO = ("CO-234（L2 自裁）：① **域名显式**：覆盖面钉定以「**非 `.md` 受控件**」为域（`.md` 卡片之受控性与种类由 **t20** 机判 ⇒ 以显式域名排除，非静默跳过）；"
         "② **显式豁免（附理由）**：`co77` 收口扫描记录**不可 pin** —— 其内容依赖 boundary 而 boundary pin 其 sha 即**自指循环**（首版实测：序 5 轮不收敛；oracle `FAIL_SETTLE_NOT_CONVERGED`）⇒ 入 `PIN_COVERAGE_EXEMPT`（名集等式 + 理由）；③ 入机判 runner 静态齿 **t42_pin_face_covers_controlled**（覆盖 + **域下限** `PIN_COVERAGE_FLOOR` 防「删声明即空真」；正/负控齐备）；"
         "④ 自声明面同步 runner report revision → **CO-203.11**；⑤ **R-CO234-1**。")
NEXT = ("凡序内受控产物须全部入 pin 面（显式域名除外）；新增受控件须同 commit 补 pin（否则 t42 停机）。**残余（未闭，界定）**：① 域由 runner **声明**承载 ⇒ 域缩水仅由**下限**部分拦阻（非完整名集等式，留待后续 CO）；② 本件判**覆盖面**，"
        "不判各件内容正确性（t41 类模式可逐件扩展）；③ `.md` 卡片面无 pin 判据（其受控性由 t20 承接）。")
ADD = [{"finding": "co234:F-1", "sev": "mid", "kind": "TOOL_DEFECT", "what": WHAT, "disposition": DISPO,
        "status": "CLOSED", "next": NEXT,
        "evidence": ["修前（本会话实测）：受控集 43 件中 8 件在 pin 面无 pin（含 co77 收口扫描记录）",
                     "修后：`--check` 44/44 全 True（t42 覆盖臂 True；合成负控 `pin_coverage_gap` / `pin_coverage_vacuous` 皆触发）",
                     "自指循环实测（本会话）：首版补钉 co77 收扫记录 ⇒ 序 **5 轮不收敛**（sha 各异）+ oracle FAIL_SETTLE_NOT_CONVERGED；改显式豁免后 ⇒ rc=0 / 2 轮 / oracle PASS",
                     "观测：改生成器/新增节后**首跑可能非不动点** ⇒ t41 报警（fail-closed，属有意）；重跑生成器至幂等即达不动点（与既有「循环 2-3 次至 sha 稳定」口径一致）"],
        "refs": ["CO-186", "CO-219", "CO-225", "CO-230", "CO-231", "CO-234"], "closed_by": ["CO-234"]}]
NOTE = ("；**CO-234（L2 自裁 · pin 面对受控集之覆盖面）**：+1 TOOL_DEFECT（`co234:F-1` 受控集 43 件有 8 件漏钉且无声明；处置 = 域名显式（非 md）+ 补钉 co77 记录 + 静态齿 t42（覆盖 + 域下限）；mid、CLOSED）。")


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
    added = []
    for it in ADD:
        if it["finding"] not in by:
            reg["items"].append(it); added.append(it["finding"])
        elif reg["items"][by[it["finding"]]] != it:
            reg["items"][by[it["finding"]]] = it; added.append(it["finding"] + "(updated)")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-234（L2 自裁", NOTE)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
