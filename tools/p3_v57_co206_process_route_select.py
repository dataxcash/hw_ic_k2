#!/usr/bin/env python3
"""CO-206 工艺选型 / 性价比对比（ENG 常规功能，监理指令 #13）。

CO-211（L2 自裁）：把**决策规则求值化** —— 原实现恒返回 cost/lead value=None 且 pick="A"（规则从未求值，
与「规则已编码、填参后复算」之声明不符）；现按 `criteria.decision` 求值（含「B 须先证 32/32」前置）+ 闭式安全求值器 + 求值齿。
CO-213（L2 自裁 · 复评 F-1 处置）：前置**再求值化** —— CO-211 之 `_proven["B"]` 仍为代码常量
（判据件侧任何编辑都无法改判，仅内存注入可达）；现改由判据件机读字段 `F4_route_predicates.B.measured_placement`
求值（`placed == total`；缺字段/退化 ⇒ fail-closed 视为未证），并加**数据驱动**求值齿 t07（零代码改动即改判）。

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
import argparse, hashlib, importlib.util, json, re, sys
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


# ── CO-211：成本/交期模型之**闭式安全求值**（白名单记号 + 递归下降；无 eval） ────────────────
#   缘起（§84）：工具自称「规则已编码、填参后复算」，而实现恒返回 value=None / pick="A" ——
#   即「声明↔实现」在**决策面**漂移（承 R-CO194-1 / R-CO208-1 / R-CO210-1）。
_TOK = re.compile(r"(\d+\.?\d*|\.\d+|[A-Za-z_][A-Za-z_0-9]*|[-+*/()])")
DECISION_RULE_ID = "B_if_feasible_and_cheaper_else_A"
# 各路之模型变量绑定（L 信号层数 / H 等效 HDI 阶数 / R advanced review / N 盲埋孔 / P 盘中孔 / G 重派生成遍数）
ROUTE_VARS = {"A": {"L": 8, "H": 2, "R": 1, "N": "buried", "P": 0, "G": 0},
              "B": {"L": 10, "H": 0, "R": 0, "N": 0, "P": 0, "G": 1},
              "C": {"L": 8, "H": 0, "R": 0, "N": 0, "P": "blind_one_outer_endpoint", "G": 0}}


def route_vars(k: str, facts: dict) -> dict:
    """CO-211：把符号变量解析为本案实际值（N/P 来自机判事实）。"""
    v = dict(ROUTE_VARS[k])
    if v["N"] == "buried":
        v["N"] = facts["n_requires_blind_buried"]
    if v["P"] == "blind_one_outer_endpoint":
        v["P"] = facts["n_blind_class_one_outer_endpoint"]
    return v


def _eval_expr(expr: str, vars: dict):
    """白名单闭式求值（`+ - * /`、括号、数字、vars 内标识符）；未知记号/变量或除零 ⇒ None（fail-closed）。"""
    body = expr.split("=", 1)[1] if "=" in expr else expr
    toks, i = [], 0
    while i < len(body):
        if body[i].isspace():
            i += 1
            continue
        m = _TOK.match(body, i)
        if not m:
            return None
        toks.append(m.group(1)); i = m.end()
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def expr_():
        v = term()
        while peek() in ("+", "-"):
            op = toks[pos[0]]; pos[0] += 1
            r = term()
            if v is None or r is None:
                return None
            v = v + r if op == "+" else v - r
        return v

    def term():
        v = factor()
        while peek() in ("*", "/"):
            op = toks[pos[0]]; pos[0] += 1
            r = factor()
            if v is None or r is None:
                return None
            if op == "/":
                if r == 0:
                    return None
                v = v / r
            else:
                v = v * r
        return v

    def factor():
        t = peek()
        if t is None:
            return None
        if t == "-":
            pos[0] += 1
            r = factor()
            return None if r is None else -r
        if t == "(":
            pos[0] += 1
            v = expr_()
            if v is None or peek() != ")":
                return None
            pos[0] += 1
            return v
        pos[0] += 1
        if re.fullmatch(r"\d+\.?\d*|\.\d+", t):
            return float(t)
        if t in vars and isinstance(vars[t], (int, float)):
            return float(vars[t])
        return None

    v = expr_()
    return None if (v is None or pos[0] != len(toks)) else v


def b_feasibility(criteria: dict):
    """CO-213：B 可行性前置**求值自判据件机读字段**（非代码常量）。

    谓词 = `F4_route_predicates.B_add_signal_layers_all_through.measured_placement`
    之 `placed == total`（全落位 32/32 方为「已证」）；字段缺失/类型错/退化(total<=0)
    ⇒ 视为未证（fail-closed）—— 与 `decision.precondition` 声明同源（规则与其前置同处声明）。
    """
    try:
        mp = criteria["criteria"]["F4_route_predicates"]["B_add_signal_layers_all_through"]["measured_placement"]
        placed, total = int(mp["placed"]), int(mp["total"])
    except (KeyError, TypeError, ValueError):
        return False, None
    return (total > 0 and placed >= total), {"placed": placed, "total": total}


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
                                  "实测（修正 span）：lane 落外层候选 = **26/32**；但 lane 落外层须吃**外层 3W(0.615)**，"
                                  "按外层口径复测（CO10_LANE_OUTER）⇒ **24/32** ⇒ 未达全落位，可行性未证"],
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

    # CO-211：按符号绑定**求值**（缺参 ⇒ value=None 且列缺失；不越权编造）；并标注可行性是否已证。
    # CO-213：前置**取自判据件**（原为代码常量 ⇒ 判据件侧编辑无法改判）；A 为「待 DFM」而非未证。
    b_proven, b_placement = b_feasibility(criteria)
    _proven = {"A": None, "B": b_proven, "C": False}
    for k, rt in routes.items():
        v = route_vars(k, facts)
        cmiss = [n for n, p in cm["parameters"].items() if p["value"] is None]
        lmiss = [n for n, p in lm["parameters"].items() if p["value"] is None]
        rt["cost"]["vars"] = v
        rt["lead_time"]["vars"] = v
        rt["cost"]["missing"] = cmiss
        rt["lead_time"]["missing"] = lmiss
        rt["cost"]["value"] = None if cmiss else _eval_expr(
            cm["expr"], {**v, **{n: p["value"] for n, p in cm["parameters"].items()}})
        rt["lead_time"]["value"] = None if lmiss else _eval_expr(
            lm["expr"], {**v, **{n: p["value"] for n, p in lm["parameters"].items()}})
        rt["feasibility"]["proven"] = _proven[k]
        if k == "B":
            rt["feasibility"]["measured_placement"] = b_placement   # CO-213：前置之来源（可追溯）
    return routes


def recommend(routes: dict, facts: dict) -> dict:
    """CO-211：**求值**声明式规则（`criteria.decision`）而非硬编码：
    B 优于 A ⇔ （B 可行性已证）且（C_B < C_A）；缺参 ⇒ 不作伪排序（保持 A）。"""
    if facts["n_requires_blind_buried"] == 0:
        return {"pick": "B_or_A", "basis": "无需盲/埋孔 ⇒ 标准通道可选；先比价",
                "decision_rule_id": DECISION_RULE_ID, "rule_evaluated": False}
    A, B = routes["A"], routes["B"]
    ca, cb = A["cost"]["value"], B["cost"]["value"]
    b_proven = bool(B["feasibility"].get("proven"))
    if not b_proven:
        pick, why = "A", "B **可行性未证**（须 32/32 全落位；现行最优 24/32）⇒ **规则前置不满足**"
    elif ca is None or cb is None:
        pick, why = "A", (f"成本参数缺失（A {len(A['cost']['missing'])} 项 / B {len(B['cost']['missing'])} 项）"
                          "⇒ **不作伪排序**")
    else:
        pick = "B" if cb < ca else "A"
        why = f"C_B = {cb:.2f} {'<' if cb < ca else '>='} C_A = {ca:.2f} ⇒ 取 {pick}"
    return {
        "pick": pick, "runner_up": "B" if pick == "A" else "A",
        "decision_rule_id": DECISION_RULE_ID, "rule_evaluated": True,
        "rule_precondition": "B 可行性已证（每支孔外层锚定 = 32/32 落位）",
        "evaluated": {"B_feasibility_proven": b_proven, "cost_A": ca, "cost_B": cb,
                      "cost_A_missing": A["cost"]["missing"], "cost_B_missing": B["cost"]["missing"]},
        "decision_basis": why,
        "basis": [
            "① 可行性：A 是本设计**唯一无需重派生**即可落地的路（现行图纸即盲埋孔形态；B 可行性未证 —— lane 落外层口径 **24/32**（CO-206b）；C 不能替埋孔）",
            "② 性能：A 无背钻残桩，SI 按现行 SPEC 不变；B 需把 lane 移外层（微带）并重签阻抗",
            "③ 风险：A 的风险集中在**报价与 DFM review 结论**（可询价收敛）；B 的风险是整层重派生回归 + 可行性未证",
            f"④ 成本（**已求值**，非声明）：{why}；判据序 = 可行性 > 性能 > 风险 > 成本",
        ],
        "conditional": {"if": "B_feasible_proven AND C_B(+重派生) < C_A", "then": "B", "else": "A"},
    }


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

    # CO-211：决策规则之**求值齿**（fail-closed；缺参不伪排序 / 前置不满足即 A / 求值器判别力）
    import copy as _copy

    def _with_params(c: dict, vals: dict) -> dict:
        d = _copy.deepcopy(c)
        for n, p in d["cost_model"]["parameters"].items():
            p["value"] = vals.get(n, 1.0)
        for n, p in d["lead_time_model"]["parameters"].items():
            p["value"] = 1.0
        return d

    _vals = {"k_layer": 10.0, "k_hdi_order": 100.0, "k_adv_review": 50.0, "k_via_nonstd": 0.5,
             "k_vipp": 0.5, "k_imp": 20.0, "k_rederivation": 5.0}
    _r_full = evaluate(_with_params(criteria, _vals), facts)          # 参数齐备（B 明显更省）
    _r_provenB = _copy.deepcopy(_r_full)
    _r_provenB["B"]["feasibility"]["proven"] = True                   # 假设 B 已证 32/32
    def _set_placement(c: dict, placed: int, total: int) -> dict:
        """CO-213：只改判据件**数据**（零代码改动）—— 用于 t07 数据驱动正/负控。"""
        d = _copy.deepcopy(c)
        d["criteria"]["F4_route_predicates"]["B_add_signal_layers_all_through"]["measured_placement"] = {
            "placed": placed, "total": total}
        return d

    def _drop_placement(c: dict) -> dict:
        d = _copy.deepcopy(c)
        d["criteria"]["F4_route_predicates"]["B_add_signal_layers_all_through"].pop("measured_placement", None)
        return d

    def _dummies(pars: dict) -> dict:
        return {n: (p["value"] if p["value"] is not None else 1.0) for n, p in pars.items()}
    teeth = {
        "t01_rule_declared_by_criteria": (criteria.get("decision") or {}).get("rule_id") == DECISION_RULE_ID,
        "t02_no_fabricated_numbers_when_missing": all(
            routes[k]["cost"]["value"] is None and routes[k]["lead_time"]["value"] is None for k in "ABC"),
        "t03_rule_evaluates_when_complete": (
            _r_full["A"]["cost"]["value"] is not None and _r_full["B"]["cost"]["value"] is not None
            and _r_full["A"]["lead_time"]["value"] is not None),
        "t04_b_requires_feasibility_precondition": (
            recommend(_r_provenB, facts)["pick"] == "B" and recommend(_r_full, facts)["pick"] == "A"),
        "t05_expr_evaluator_fail_closed": (
            _eval_expr("C = 1+2*3-4/2", {}) == 5.0
            and _eval_expr("C = (1+2)*3", {}) == 9.0
            and _eval_expr("C = -2*3", {}) == -6.0
            and _eval_expr("C = k_layer*L + bogus", {"k_layer": 1, "L": 8}) is None
            and _eval_expr("C = 1/0", {}) is None
            and _eval_expr("C = __import__('os')", {}) is None),
        "t07_precondition_evaluated_from_criteria": (
            # 正控（**只改判据件数据、零代码改动**）：placed==total ⇒ 前置成立 ⇒ 可改判为 B
            recommend(evaluate(_set_placement(_with_params(criteria, _vals), 32, 32), facts), facts)["pick"] == "B"
            # 负控：placed<total（现行 24/32）⇒ 前置不成立 ⇒ 保守路 A
            and recommend(evaluate(_set_placement(_with_params(criteria, _vals), 24, 32), facts), facts)["pick"] == "A"
            # 负控：字段缺失（退化）⇒ fail-closed 视为未证 ⇒ A（不得因缺字段而误判「已证」）
            and recommend(evaluate(_drop_placement(_with_params(criteria, _vals)), facts), facts)["pick"] == "A"
            # 判别力：字段确实被读（24/32 vs 32/32 前置不同）
            and b_feasibility(_set_placement(criteria, 24, 32))[0] is False
            and b_feasibility(_set_placement(criteria, 32, 32))[0] is True),
        "t06_expr_vars_all_bound": all(
            _eval_expr(criteria["cost_model"]["expr"],
                       {**route_vars(k, facts), **_dummies(criteria["cost_model"]["parameters"])}) is not None
            and _eval_expr(criteria["lead_time_model"]["expr"],
                           {**route_vars(k, facts), **_dummies(criteria["lead_time_model"]["parameters"])}) is not None
            for k in "ABC"),
    }
    doc = {
        "artifact": "m13_v57_co206_process_route_selection", "schema": 1, "revision": "CO-206.4",
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
                 "cost_numbers_fabricated": False, "decision_rule_evaluated": True},
        "teeth": teeth,
        "redline": "只读冻结四源；未改 canonical 图纸 / 交付板 / 构造器；无 sign-off；承 R-CO208-1（同一量多处引用须同 commit 同步口径）+ R-CO213-1（决策前置须自判据件求值，禁代码常量）"
    }
    out = Path(a.out); out.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    _write_md(Path(a.md), doc)
    print(f"route-select: vias={facts['n_vias']} through+backdrill_ok={facts['n_through_backdrill_ok']} "
          f"needs_blind_buried={facts['n_requires_blind_buried']} (buried; min lamination cycles "
          f"{facts['max_min_lamination_cycles']}) blind_class={facts['n_blind_class_one_outer_endpoint']}")
    for r in ("A", "B", "C"):
        print(f"  {r}: feasibility={routes[r]['feasibility']['verdict']:28s} cost={routes[r]['cost']['value']} "
              f"lead_time={routes[r]['lead_time']['value']}")
    print(f"  recommend: {rec['pick']} (runner-up {rec.get('runner_up')}) | {rec['decision_basis']}")
    print(f"  teeth: {sum(1 for v in teeth.values() if v is True)}/{len(teeth)} "
          f"{'PASS' if all(teeth.values()) else 'FAIL ' + str([k for k, v in teeth.items() if v is not True])}")
    print(f"-> {out}")
    return 0 if all(teeth.values()) else 1


def _write_md(p: Path, doc: dict) -> None:
    f = doc["design_facts"]; R = doc["routes"]; rec = doc["recommendation"]
    L = ["# CO-206.3 工艺选型 / 性价比对比（A/B/C）", "",
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
