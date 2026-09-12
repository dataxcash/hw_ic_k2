#!/usr/bin/env python3
"""CO-153 — K9 覆盖缺口关闭（L2 自裁 · 闸硬化）：`declared` 类证据化 + 保守实现闭式证明。

缘起（本件执行前实测）：co124 K9 对 `kind == "declared"` **无任何判据**（默认 kind 亦为 declared）⇒
  · `DV-CO146-ZDIFF`（kind=declared）**从不被校验**——且其 `evidence_ref.sha16` 已陈旧（CO-152 改过阻抗表记录）；
  · `DV-ENGINE-INT_PAIR_PITCH`（无 kind ⇒ 视作 declared）亦**从不被校验**，而其「保守实现」实为可闭式证明的命题。
即 9 个派生值中 2 个**零校验通过** ＝「声明即通过」缺口（与 CO-148 登记的热/压降域缺口同族）。

本件（executor）：
  ① 台账归一：`DV-ENGINE-INT_PAIR_PITCH.reachability.kind` → `conservative_ge`（其可达性是可闭式证明的）；
  ② 登记 1 项 TOOL_DEFECT 并 CLOSED（证据事后由 co124 牙齿 T12/T12b/T13/T13b 承接）；
  ③ 幂等（按 id 归一 / 按 finding 去重）。
配套：`p3_v57_co146_ledger_add.py`（DV 证据 pin 的**生产者**）并入规范复现序 ⇒ ZDIFF pin 随记录自动刷新。
只改台账 + 登记簿（L2 政策层）；不改 SPEC/板/阈值/冻结四源/其它工件。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co153_k9_domain_coverage.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
LED = L2 / "derived_value_ledger_v1.json"
REG = L2 / "input_defect_register_v1.json"
FINDING = "tool_defect:co124_k9_declared_kind_has_no_evidence_check"
ITEM = {
    "finding": FINDING,
    "kind": "TOOL_DEFECT", "severity": "medium",
    "what": "co124 K9 对 `kind == \"declared\"`（含无 kind 的默认值）**无任何判据** ⇒ 9 个派生值中 2 个零校验通过、"
            "「声明即通过」：① `DV-CO146-ZDIFF` 声明类但 `evidence_ref.sha16` 从不核对（CO-152 改过阻抗表记录后"
            "该 pin 实测陈旧）；② `DV-ENGINE-INT_PAIR_PITCH` 无 kind（视作 declared）且无证据，其「保守实现」"
            "（value ≥ 忠实下界）本可闭式证明却未证明。（判定依据：CO-153 执行前实测 co124 findings = 2："
            "`derived_value_declared_unpinned:DV-ENGINE-INT_PAIR_PITCH` / `...:DV-CO146-ZDIFF`。）",
    "refs": ["CO-151", "CO-152", "CO-153", "CO-148", "CO-150"],
    "disposition": "CO-153 处置：① co124 K9 新增 `declared` 判据（evidence_ref 须可解析 + sha16 与现行一致 + "
                   "basis 非空，与 process_floor 同口径）与 `conservative_ge` 判据（闭式重算 "
                   "faithful = span + 2·w_outer 并证 value ≥ faithful，且 cited 一致）；② 台账归一 "
                   "`DV-ENGINE-INT_PAIR_PITCH.kind = conservative_ge`；③ 证据 pin 生产者 "
                   "`p3_v57_co146_ledger_add.py` **并入规范复现序**（阻抗表之后）⇒ 记录变更即自动刷新 pin；"
                   "④ 牙齿 T12/T12b（声明未锚定必抓 / 无假阳）、T13/T13b（保守未证明必抓 / 无假阳）。"
                   "闭合复核：co124 = PASS、findings 0、牙齿全 True。",
    "status": "CLOSED",
    "next": "新增 `declared` 类派生值必须带可解析且 sha 现行的 evidence_ref + 非空 basis；"
            "保守实现类一律用 `conservative_ge` 并给 span/w_outer/value/faithful 四值。",
    "evidence": ["CO-153 执行前 co124 findings（2 条 declared_unpinned）",
                 "co124 牙齿 T12/T12b/T13/T13b（记录在 co124 记录 teeth）",
                 "台账 DV-ENGINE-INT_PAIR_PITCH.kind=conservative_ge"],
    "closed_by": ["CO-153"],
}
ITEM2 = {
    "finding": "tool_defect:co146_ledger_add_schema_drift_and_out_of_order",
    "kind": "TOOL_DEFECT", "severity": "medium",
    "what": "DV 证据 pin 的**生产者** `p3_v57_co146_ledger_add.py` 因 schema 漂移**失修**（读 `pm.thermal.Tj` / "
            "`hotspot_Tj_C`，而 CO-148 起 pm_eval 已改为 routes/T_board ⇒ KeyError）**且从未列入规范复现序** "
            "⇒ `DV-CO146-ZDIFF.reachability.evidence_ref.sha16` 自 CO-146 起再未刷新；CO-152 修改阻抗表记录后"
            "该 pin 实测陈旧（因 K9 无 declared 判据、co120 亦不扫台账 ⇒ **无人发现**）。",
    "refs": ["CO-146", "CO-148", "CO-152", "CO-153"],
    "disposition": "CO-153 处置：① 修复本件为 schema 自适应（字段齐备才登记 DV-CO146-THERMAL，否则跳过并提示——"
                   "该项归 CO-148/CO-149 拥有）⇒ 现可正常执行；② 并入**规范复现序**（`co146_pm_eval` 之后）⇒ "
                   "ZIDFF/PDN-DROP 的证据 pin 随记录自动刷新；③ 新增 K9 `declared` 判据 + 牙齿 T12/T12b，"
                   "使此类陈旧 pin **必然被抓**（执行前实测 2 findings、执行后 PASS）。",
    "status": "CLOSED",
    "next": "凡产出发行性证据 pin 的工具必须列入规范复现序；工具读取上游记录时须对 schema 漂移 fail-soft（跳过多余项并提示）。",
    "evidence": ["co146_ledger_add 运行输出（note: 跳过 DV-CO146-THERMAL）",
                 "co124 牙齿 T12/T12b；台账 DV-CO146-ZDIFF.evidence_ref 与阻抗表记录一致"],
    "closed_by": ["CO-153"],
}

ITEM3 = {
    "finding": "tool_defect:k9_drop_domain_has_no_producer_in_reproduction_order",
    "kind": "TOOL_DEFECT", "severity": "medium",
    "what": "K9 的 `drop_domain` 可达性**在规范复现序内无生产者**：`DV-CO146-PDN-DROP.reachability.kind = drop_domain` "
            "系一次性写入，co146/co148/co149/co150 诸工具均不产出之；而 `p3_v57_co146_ledger_add.py`（原三 DV 一并重写）"
            "会把该 DV 复位为 `declared` ⇒ **drop 域机判静默失效**（co124 牙齿 `T11_drop_domain_teeth` 由 True 变 False，"
            "CO-153 实测）。同族风险：任何「一次性写入的可达性域」在台账重写后都会静默退化。",
    "refs": ["CO-150", "CO-153", "CO-152"],
    "disposition": "CO-153 处置：① `p3_v57_co146_ledger_add.py` **收窄**为仅 upsert DV-CO146-ZDIFF（不再 clobber PDN/THERMAL 归属）；"
                   "② `p3_v57_co153_k9_domain_coverage.py` 成为 `drop_domain` 的**归一生产者**（kind + 证据 pin=pm_eval）并置入规范序 "
                   "（co146_pm_eval 之后、co124 之前）⇒ 无滞后；③ co124 `T11_drop_domain_teeth` 恢复 True 作为回归牙齿。",
    "status": "CLOSED",
    "next": "K9 各域（domain_cap/identity/process_floor/declared/conservative_ge/drop_domain/thermal_option_domain）"
            "均须由规范序内**具名生产者**产出；禁止一次性写入台账域。",
    "evidence": ["co124 teeth `T11_drop_domain_teeth`（False→True，CO-153 实测）",
                 "co153 归一输出 ledger sha；co146_ledger_add 收窄后输出（n_dv=9）"],
    "closed_by": ["CO-153"],
}

MARK = ("；**CO-153（L2 自裁 · K9 覆盖缺口关闭）**：co124 K9 新增 `declared`（证据须锚定）+ `conservative_ge`"
        "（保守实现闭式证明）两支 + 牙齿 T12/T12b/T13/T13b；台账 DV-ENGINE-INT_PAIR_PITCH 归一等价可证；"
        "`p3_v57_co146_ledger_add.py` 并入规范序 ⇒ 证据 pin 自动刷新。关闭 TOOL_DEFECT："
        "`co124_k9_declared_kind_has_no_evidence_check`。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

# CO-156（F-4）：本件是 K9 **全部七域** `kind` 的规范序内具名生产者（此前仅 drop_domain/conservative_ge），
# 使 R-CO153-1「各域均由规范序内具名生产者产出」成立；域内容（computed/domains）仍归各派生 CO。
# CO-161（F-1）：提到模块级 ⇒ 作为**必需 DV 清单**的单一真值，由 co124 消费、co150 交叉比对（防两处清单漂移）。
KIND_EXPECT = {
    "DV-INTPAIR-EDGE": "domain_cap", "DV-PAIR-CROSS": "identity",
    "DV-CLR-POWER": "process_floor", "DV-EDGE-COPPER": "process_floor",
    "DV-M3-KEEPOUT": "process_floor", "DV-ENGINE-INT_PAIR_PITCH": "conservative_ge",
    "DV-CO146-ZDIFF": "declared", "DV-CO146-PDN-DROP": "drop_domain",
    "DV-CO146-THERMAL": "thermal_option_domain",
}
assert set(KIND_EXPECT.values()) == {"domain_cap", "identity", "process_floor", "declared",
                                     "conservative_ge", "drop_domain", "thermal_option_domain"}




def main() -> int:
    led = json.loads(LED.read_text())
    norm = []
    pm = json.loads((K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_pm_eval.json").read_text())
    _by_id = {d["id"]: d for d in led["derived_values"]}
    _auth_edge = ((_by_id.get("DV-INTPAIR-EDGE") or {}).get("computed") or {}).get("edge_outer_binding_mm")
    _auth_span = ((_by_id.get("DV-PAIR-CROSS") or {}).get("computed") or {}).get("span_mm")
    for dv in led["derived_values"]:
        rc = dv.setdefault("reachability", {})
        want = KIND_EXPECT.get(dv["id"])
        if want and rc.get("kind") != want:
            rc["kind"] = want
            norm.append(dv["id"] + ":kind")
        if dv["id"] == "DV-CO146-PDN-DROP":
            # CO-153：`drop_domain` 此前无生产者（一次性写入）⇒ 本件为其归一生产者（kind + 证据 pin）。
            if rc.get("kind") != "drop_domain":
                rc["kind"] = "drop_domain"
                rc["predicate"] = "每轨 ΔV% ≤ 预算%（监理指令 #10 定值）"
                norm.append(dv["id"] + ":kind")
            if (rc.get("evidence_ref") or {}).get("sha16") != s16(K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_pm_eval.json"):
                rc["evidence_ref"] = {"path": "m13_v57_co146_pm_eval.json",
                                      "sha16": s16(K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_pm_eval.json")}
                rc.setdefault("basis", "几何取自交付板 zone 声明域；电流为显式声明值（非实测）")
                norm.append(dv["id"] + ":pin")
        if dv["id"] == "DV-ENGINE-INT_PAIR_PITCH":
            # CO-153：可闭式证明的保守实现（K9 新判据）；CO-156（F-7）：span/w_outer 须**引用**权威 DV 并显式标注来源。
            rc["kind"] = "conservative_ge"
            rc.setdefault("predicate", "value_mm ≥ span + 2·w_outer（忠实下界，闭式重算）")
            inp = dv.setdefault("inputs", {})
            if isinstance(_auth_span, (int, float)):
                inp["span_mm"] = round(float(_auth_span), 4)
                inp["span_src"] = "DV-PAIR-CROSS.computed.span_mm"
            if isinstance(_auth_edge, (int, float)):
                inp["w_outer_mm"] = round(float(_auth_edge) / 2.0, 4)
                inp["w_outer_src"] = "DV-INTPAIR-EDGE.computed.edge_outer_binding_mm/2"
            if isinstance(inp.get("span_mm"), (int, float)) and isinstance(inp.get("w_outer_mm"), (int, float)):
                dv.setdefault("computed", {})["faithful_min_mm"] = round(float(inp["span_mm"]) + 2.0 * float(inp["w_outer_mm"]), 4)
            norm.append(dv["id"] + ":binding")
    LED.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n")

    reg = json.loads(REG.read_text())
    have = {i["finding"] for i in reg["items"]}
    added = []
    for it in (ITEM, ITEM2, ITEM3):
        if it["finding"] not in have:
            reg["items"].append(it)
            added.append(it["finding"])
    if MARK not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")

    print(f"ledger normalized: {norm or 'already'} | sha16 {s16(LED)}")
    print(f"register: +{len(added)} items (total {len(reg['items'])}), counts={reg['meta']['counts']} | sha16 {s16(REG)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
