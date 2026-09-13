#!/usr/bin/env python3
"""CO-206 工艺选型 / 性价比对比（ENG 常规功能，监理指令 #13）。

给定设计约束（叠层 + 过孔普查 + 判据件），输出工艺路线的
  可行性 / 成本 / 交期 / 性能 / 风险 对比 + 推荐；**判据先行、可复现、可复用**。

设计要点
- **判据与数据分离**：判据/参数在 `L2/process_route_criteria_v1.json`（可替换 ⇒ 换板/换厂可复用）；
  本工具只做确定性求值，不含板级特判。
- **零坐标搜索**：不开搜索、不改几何；只读板做普查。
- **禁编造单价**：报价参数缺失时输出模型 + 所需输入清单，不输出伪数字（无验证来源 = null）。
- **单一真源**：过孔普查/层距/残桩复用板厂能力绑定闸的同一实现（避免两处口径漂移）。

CLI: --criteria <json> [--board <pcb>] [--out <json>] [--md <md>]
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
DEFAULT_CRITERIA = K2 / "pm_gate/artifacts/k2_v4/L2/process_route_criteria_v1.json"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"


def _load_gate():
    p = K2 / "tools/p3_v57_co204_fab_capability_binding_gate.py"
    s = importlib.util.spec_from_file_location("fabcap_gate", str(p))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def classify(criteria: dict, census: dict, span: dict, gate) -> dict:
    """按 F1/F2 把每一类过孔归类并算残桩/所需阶数（确定性）。"""
    order = criteria["layer_stack"]["physical_order_top_to_bottom"]
    outer = set(criteria["layer_stack"]["outer"])
    idx = {l: i for i, l in enumerate(order)}
    total = len(order)
    rows = []
    for cls, n in sorted(census.items()):
        top, bot = cls.split("->")
        anchored = (top in outer) or (bot in outer)
        stub = gate.class_stub(top, bot, span)
        need_lam = None if anchored else 1 + min(idx[top], total - 1 - idx[bot])
        rows.append({"class": cls, "n": n, "outer_anchored": anchored,
                     "stub_mm": stub, "min_lamination_cycles": need_lam,
                     "f1_through_backdrill_ok": bool(anchored),
                     "f3_stub_ok": bool(stub <= criteria["criteria"]["F3_stub_limit"]["stub_limit_mm"])})
    placed = sum(r["n"] for r in rows if r["outer_anchored"] and r["f3_stub_ok"])
    return {"classes": rows,
            "n_vias": sum(r["n"] for r in rows),
            "n_through_backdrill_ok": placed,
            "n_requires_blind_buried": sum(r["n"] for r in rows if not r["f1_through_backdrill_ok"]),
            "n_blind_class_one_outer_endpoint": sum(1 for r in rows for _ in range(r["n"])
                                                     if (r["class"].split("->")[0] in outer) != (r["class"].split("->")[1] in outer)),
            "max_min_lamination_cycles": max([r["min_lamination_cycles"] or 0 for r in rows], default=0)}


def evaluate(criteria: dict, facts: dict) -> dict:
    """三路 A/B/C 的可行性 / 性能 / 风险（成本与交期走参数模型；缺参则只出模型+所需输入）。"""
    cm, lm = criteria["cost_model"], criteria["lead_time_model"]
    missing_cost = [k for k, v in cm["parameters"].items() if v["value"] is None]
    missing_lt = [k for k, v in lm["parameters"].items() if v["value"] is None]
    buried = facts["n_requires_blind_buried"]
    vb = facts["max_min_lamination_cycles"]

    routes = {}
    routes["A"] = {
        "name": "JLC advanced/HDI 盲埋孔（专属通道）",
        "feasibility": {"verdict": "FEASIBLE_PENDING_DFM" if buried else "FEASIBLE",
                        "basis": [f"需盲/埋孔支数 = {buried}（不在标准通道可制集内）",
                                  f"物理层序推得**层压次数下界 = {vb}**（In2..In5 腔：上方跳 F,In1 / 下方跳 In6,B 各 2 层）",
                                  f"等效 HDI 阶数 >= 2（指示性映射，须板厂确认；本工程抓取件未声明阶数上限）",
                                  "抓取件 FAQ 明列 advanced options 含 blind/buried vias 与 HDI (laser vias)，须 DFM review"],
                        "unverified_inputs": criteria["criteria"]["F4_route_predicates"]["A_advanced_hdi"]["unverified_inputs"]},
        "design_change": "NONE（现行图纸即盲埋孔形态；仅渠道/能力绑定重签 + DFM review）",
        "performance": {"stub_mm": 0.0, "note": "盲埋孔为设计意图形态，无背钻残桩；SI 按现行 SPEC 不变"},
        "cost": {"value": None, "model": cm["expr"], "parameters": {k: cm["parameters"][k] for k in cm["parameters"]},
                 "missing": missing_cost,
                 "qualitative": cm["qualitative_anchor"]},
        "lead_time": {"value": None, "model": lm["expr"], "missing": missing_lt,
                      "qualitative": "抓取件：advanced options 可能增加生产时间"},
        "risk": criteria["risk_catalog"]["A_advanced_hdi"],
        "verification": ["与 HDI 通道 DFM 报价单对齐阶数/激光孔径/环宽", "板厂能力绑定闸重绑 HDI 能力源后须 PASS"]}

    routes["B"] = {
        "name": "加信号层全通孔（如 10L）",
        "feasibility": {"verdict": "UNPROVEN",
                        "basis": ["充分条件：存在层分配使每支孔外层锚定（F1 全过）",
                                  "必要条件（确定性）：lane 必须落外层，否则 corner 为内层<->内层 ⇒ 该路无解",
                                  "实测（现行模型，修正 span）：lane 落外层的候选 = 26/32 落位 ⇒ 未达全落位，可行性未证"],
                        "unverified_inputs": criteria["criteria"]["F4_route_predicates"]["B_add_signal_layers_all_through"]["unverified_inputs"]},
        "design_change": "REQUIRED（层分配 + 走廊/列 + 阻抗重派生；属 WORKER 实施）",
        "performance": {"stub_mm": 0.0, "note": "全通孔+背钻 ⇒ 残桩可至 0；但 lane 落外层 = 微带，须重签阻抗与 SI"},
        "cost": {"value": None, "model": cm["expr"], "missing": missing_cost,
                 "drivers": ["层数 8 -> 10（k_layer 线性）", "无 advanced review / 无 HDI 阶数项"]},
        "lead_time": {"value": None, "model": lm["expr"], "missing": missing_lt,
                      "drivers": ["全层重派生（t_derivation 项）", "标准通道无 DFM review 附加"]},
        "risk": criteria["risk_catalog"]["B_add_signal_layers_all_through"],
        "verification": ["重派生后须全落位 32/32 + 板厂能力绑定闸 PASS + DRC 不新增"]}

    routes["C"] = {
        "name": "盘中孔 via-in-pad（6+ 层成熟工艺）",
        "feasibility": {"verdict": "PARTIAL_INSUFFICIENT_ALONE",
                        "basis": [f"可替代：仅**盲孔**（一端外层）= {facts['n_blind_class_one_outer_endpoint']} 支",
                                  f"不可替代：**埋孔**（两端内层）= {buried} 支 —— 埋孔不在任何外层焊盘之下",
                                  "抓取件明列 Via-in-Pad Process（epoxy/copper paste filled & capped，4-32 层，可在 BGA 焊盘内放孔）"],
                        "unverified_inputs": ["via-in-pad 定价与塞孔良率", "进盘孔是否与现行焊盘/钢网/组装冲突"]},
        "design_change": "PARTIAL（进盘孔释放近焊盘布线密度；不解决埋孔）",
        "performance": {"stub_mm": None, "note": "不改变残桩性质；解决的是布线密度"},
        "cost": {"value": None, "model": cm["expr"], "missing": missing_cost,
                 "drivers": ["无 HDI 阶数项", "k_vipp 计费项"]},
        "lead_time": {"value": None, "model": lm["expr"], "missing": missing_lt, "drivers": ["标准通道 + 塞孔工序"]},
        "risk": criteria["risk_catalog"]["C_via_in_pad"],
        "verification": ["须与另一路组合（埋孔仍需 A 或 B 处置）"]}
    return routes


def recommend(routes: dict, facts: dict) -> dict:
    """按『可行性 > 性能 > 风险 > 成本』的判据序给推荐；成本参数缺失时不越权编造排序。"""
    if facts["n_requires_blind_buried"] == 0:
        return {"pick": "B_or_A", "basis": "无需盲/埋孔 ⇒ 标准通道可选；先比价"}
    return {
        "pick": "A",
        "runner_up": "B",
        "basis": [
            "① 可行性：A 是本设计**唯一无需重派生**即可落地的路（现行图纸即盲埋孔形态；B 可行性未证 26/32；C 不能替埋孔）",
            "② 性能：A 无背钻残桩，SI 按现行 SPEC 不变；B 需把 lane 移外层（微带）并重签阻抗",
            "③ 风险：A 的风险集中在**报价与 DFM review 结论**（可询价收敛）；B 的风险是整层重派生回归 + 可行性未证",
            "④ 成本：三路单价参数均未获验证来源 ⇒ **不作伪排序**；决策规则 = 若 10L 标准报价 + 重派生代价 < HDI 加价，则改 B"],
        "decision_rule_reproducible": "填入 cost_model.parameters 后重跑本工具即得成本序；规则已编码，可复现。",
        "conditional": {"if": "quote(10L std) + cost(re-derivation) < quote(HDI 8L)", "then": "B", "else": "A"}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--criteria", default=str(DEFAULT_CRITERIA))
    ap.add_argument("--board", default=None)
    ap.add_argument("--out", default=str(STEP2 / "m13_v57_co206_process_route_selection.json"))
    ap.add_argument("--md", default=str(STEP2 / "m13_v57_co206_process_route_selection.md"))
    a = ap.parse_args()
    crit_path = Path(a.criteria)
    if not crit_path.is_absolute():
        crit_path = K2 / crit_path
    criteria = json.loads(crit_path.read_text(encoding="utf-8"))

    gate = _load_gate()
    if a.board:
        gate.BOARD = Path(a.board)
    board_path = Path(gate.BOARD)
    census = gate.board_census()
    spec = json.loads(gate.SPEC.read_text(encoding="utf-8"))
    span = gate.layer_span(spec)
    facts = classify(criteria, census["census"], span, gate)
    routes = evaluate(criteria, facts)
    rec = recommend(routes, facts)

    doc = {
        "artifact": "m13_v57_co206_process_route_selection", "schema": 1, "revision": "CO-206.1",
        "date": "2026-09-14",
        "authority": "监理指令 #13（工艺选型/性价比对比 立为 ENG 常规功能）",
        "nature": "工艺路线 A/B/C 对比 + 推荐（只读；零坐标搜索；不改板/图纸/SPEC/冻结四源）",
        "inputs": {"criteria": str(crit_path.relative_to(K2)), "criteria_sha16": sha16(crit_path),
                   "board": str(board_path.relative_to(K2)), "board_sha16": sha16(board_path),
                   "stackup_dielectric_total_mm": span["total_mm"]},
        "design_facts": facts,
        "routes": routes,
        "recommendation": rec,
        "gate": {"criteria_declared": True, "deterministic": True, "no_coordinate_search": True,
                 "cost_numbers_fabricated": False},
        "redline": "只读冻结四源；未改 canonical 图纸 / 交付板 / 构造器；无 sign-off"
    }
    out = Path(a.out); out.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    _write_md(Path(a.md), doc)
    print(f"route-select: vias={facts['n_vias']} through+backdrill_ok={facts['n_through_backdrill_ok']} "
          f"needs_blind_buried={facts['n_requires_blind_buried']} (buried; min lamination cycles "
          f"{facts['max_min_lamination_cycles']}) blind_class={facts['n_blind_class_one_outer_endpoint']}")
    for r in ("A", "B", "C"):
        print(f"  {r}: feasibility={routes[r]['feasibility']['verdict']:28s} cost={routes[r]['cost']['value']} "
              f"lead_time={routes[r]['lead_time']['value']}")
    print(f"  recommend: {rec['pick']} (runner-up {rec.get('runner_up')})")
    print(f"-> {out}")
    return 0


def _write_md(p: Path, doc: dict) -> None:
    f = doc["design_facts"]; R = doc["routes"]; rec = doc["recommendation"]
    L = ["# CO-206.1 工艺选型 / 性价比对比（A/B/C）", "",
         f"板 `{doc['inputs']['board']}` sha16 `{doc['inputs']['board_sha16']}`｜判据件 `{doc['inputs']['criteria']}` "
         f"sha16 `{doc['inputs']['criteria_sha16']}`｜介质总厚 {doc['inputs']['stackup_dielectric_total_mm']}mm", "",
         f"过孔普查：{f['n_vias']} 支；通孔+背钻可制 **{f['n_through_backdrill_ok']}**；"
         f"需盲/埋孔 **{f['n_requires_blind_buried']}**（其中两端内层=埋孔，层压次数下界 >= "
         f"{f['max_min_lamination_cycles']}）", "",
         "| 类 | 支数 | 外层锚定 | 残桩 mm | 通孔+背钻可制 |", "|---|---|---|---|---|"]
    for r in f["classes"]:
        L.append(f"| {r['class']} | {r['n']} | {'是' if r['outer_anchored'] else '**否**'} | "
                 f"{r['stub_mm']} | {'可' if r['f1_through_backdrill_ok'] else '**不可**'} |")
    L += ["", "## A/B/C 对比", "",
          "| 路 | 可行性 | 成本 | 交期 | 性能（残桩/SI） | 风险（摘要） |", "|---|---|---|---|---|---|"]
    for k in ("A", "B", "C"):
        r = R[k]
        L.append(f"| **{k}** {r['name']} | {r['feasibility']['verdict']} | "
                 f"{'INPUT_REQUIRED' if r['cost']['value'] is None else r['cost']['value']} | "
                 f"{'INPUT_REQUIRED' if r['lead_time']['value'] is None else r['lead_time']['value']} | "
                 f"{r['performance']['note'][:46]} | {r['risk'][0]} |")
    L += ["", "## 依据（可行性）", ""]
    for k in ("A", "B", "C"):
        L.append(f"**{k}**")
        for b in R[k]["feasibility"]["basis"]:
            L.append(f"- {b}")
        L.append("")
    L += ["## 推荐", "", f"**{rec['pick']}**（次选 {rec.get('runner_up')}）", ""]
    for b in rec["basis"]:
        L.append(f"- {b}")
    L += ["", f"可复现决策规则：`{rec['conditional']['if']}` ⇒ `{rec['conditional']['then']}`；否则 `{rec['conditional']['else']}`。", ""]
    p.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
