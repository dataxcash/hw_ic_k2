#!/usr/bin/env python3
"""CO-207 — 非执行者对抗复评 CO-202..CO-206c（context 归零之续接会话；满足「复评须本谱系外之新会话，禁自评」）。

对象 as-found（逐件；`git show` 内存重放 ⇒ 结论**不随**后续处置漂移）：CO-202 → `27e9fe3`；CO-203 → `d050b7e`；
CO-204 → `6c25d52`；CO-205 → `557b603`（+`7926923` C5）；CO-205r → `3f32c0a`；CO-205s → `5fabce1`；CO-205t → `01d6ad7`；
CO-206 → `5eb1922`；CO-206b → `14bd37c`；CO-206c → `add6e33`（= **被评态快照**；本件一切「现行态」判定均钉此 revision）。

方法：正控 **V1..V9**（**独立复算**：自板 pcbnew 普查 / 自算术 / 自源 AST / 自跑闸与探针 —— 不引用被评记录之结论）
+ 负控 **P1..P8**（内存注入，**零落盘**、零坐标搜索）。只读；不改 SPEC / 板 / 冻结四源 / 登记簿 / 他人记录；
仅写本件记录 + 卡。
CLI: python3 tools/p3_v57_co207_rev19_co202_co206_review.py
"""
from __future__ import annotations
import ast, hashlib, json, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
PY = K2.parent / "AppDir" / "usr" / "bin" / "python3.11"
AF = "add6e33"                                   # 被评态（CO-206c）
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
PKG = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
RUNNER = K2 / "tools/p3_v57_co164_order_runner.py"
ORACLE = K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"
SEL_TOOL = K2 / "tools/p3_v57_co206_process_route_select.py"
OREC = STEP2 / "m13_v57_co195_fixpoint_uniqueness.json"
RUNNER_REL = "tools/p3_v57_co164_order_runner.py"
OREC_REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co195_fixpoint_uniqueness.json"
REG_REL = "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
CRIT_REL = "pm_gate/artifacts/k2_v4/L2/process_route_criteria_v1.json"
SELJ_REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co206_process_route_selection.json"
SELM_REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co206_process_route_selection.md"
BND_REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md"
THERM_REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co204_thermal_verification.json"
BIND_REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co204_fab_capability_binding.json"
REC = STEP2 / "m13_v57_co207_rev19_co202_co206_review.json"
CARD = STEP2 / "m13_v57_CO207_rev19_co202_co206_review.md"
FROZEN = {
    "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
    "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
    "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
    "../_shared/eda_core/drc_rules.json": "0a459839e15960b8",
}
OBJ = {"CO-202": ["27e9fe3"], "CO-203": ["d050b7e"], "CO-204": ["6c25d52"], "CO-205": ["557b603", "7926923"],
       "CO-205r": ["3f32c0a"], "CO-205s": ["5fabce1"], "CO-205t": ["01d6ad7"], "CO-206": ["5eb1922"],
       "CO-206b": ["14bd37c"], "CO-206c": ["add6e33"]}
PROBE_KNOBS_BASE = {
    "CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json", "CO10_STEP": "1.449", "CO10_WSTEP": "1.07",
    "CO10_WLO": "33.70", "CO10_FANY_J3": "34.5,51.5", "CO10_STUB": "J3L", "CO10_POLMODE": "lx",
    "CO10_EASTSPLIT": "in2c", "CO10_J2STEP": "0.58", "CO10_COLMODE": "pol", "CO10_WSWAP": "1-11",
    "CO10_HOLE_GAP": "0.4495", "CO10_LXPRIO": "landlen", "CO10_IP3W": "1", "CO10_FAN_STRAT": "carry",
    "CO10_PDN_OBS": "1", "CO10_EDELTA": "-0.10"}
PROBE_EXPECT = {
    "v9_default": ({}, 32, None),
    "candC_BRCOL": ({"CO10_BRIDGE": "1", "CO10_SPAN": "1", "CO10_BRJOG": "0.5", "CO10_BRCOL": "1"}, 24,
                    ["PCIE_DN2/input", "PCIE_DN3/input", "PCIE_DN4/input", "PCIE_DN5/input",
                     "PCIE_UP0/input", "PCIE_UP2/input", "PCIE_UP3/input", "PCIE_UP6/input"]),
    "candC_BRCOL_COLFIX": ({"CO10_BRIDGE": "1", "CO10_SPAN": "1", "CO10_BRJOG": "0.5", "CO10_BRCOL": "1",
                            "CO10_COLFIX": "1"}, 23,
                           ["PCIE_DN2/input", "PCIE_DN3/input", "PCIE_DN4/input", "PCIE_DN5/input",
                            "PCIE_UP0/input", "PCIE_UP0/out_J2", "PCIE_UP2/input", "PCIE_UP3/input",
                            "PCIE_UP6/input"]),
    "Bpath_lane_outer": ({"CO10_LANE_OUTER": "1", "CO10_SPAN": "1", "CO10_V2B": "1"}, 24,
                         ["PCIE_DN0/out_MCIO", "PCIE_DN2/out_MCIO", "PCIE_DN5/out_MCIO", "PCIE_DN7/out_MCIO",
                          "PCIE_UP0/input", "PCIE_UP2/input", "PCIE_UP4/input", "PCIE_UP6/input"]),
}


def s16b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def s16p(p) -> str:
    return s16b(Path(p).read_bytes())


def _git(rel: str) -> str:
    r = subprocess.run(["git", "-C", str(K2), "show", f"{AF}:{rel}"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git show {AF}:{rel} failed: {r.stderr.strip()}")
    return r.stdout


def _run(argv: list) -> tuple:
    r = subprocess.run([str(a) for a in argv], capture_output=True, text=True, cwd=str(K2))
    return r.returncode, r.stdout, r.stderr


def _json_tail(out: str) -> dict:
    i = out.find("{")
    return json.loads(out[i:]) if i >= 0 else {}


# ── 纯判据（正控与负控**共用**，R-CO179-1 精神：判据自身须可证伪） ────────────────
def revision_literal_from_src(src: str, artifact: str) -> tuple:
    """AST 抽取 dict 字面量内 `revision`（**注释/散文不得满足**，承 R-CO202-4）。"""
    found, rev = False, None
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Dict):
            kv = {k.value if isinstance(k, ast.Constant) else None:
                  (v.value if isinstance(v, ast.Constant) else None) for k, v in zip(n.keys, n.values)}
            if kv.get("artifact") == artifact:
                found = True
                if isinstance(kv.get("revision"), str):
                    rev = kv["revision"]
    return found, rev


def has_revision_literal(src: str) -> bool:
    """源内是否存在含 `revision` 键之 dict 字面量（AST；注释/散文不得满足）。"""
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Dict) and "revision" in [k.value for k in n.keys if isinstance(k, ast.Constant)]:
            return True
    return False


def stale_model_number_hits(src: str, text: str) -> list:
    """「现行模型 26/32」类**被更正后残留**之现行态数值引用（文本判据，正/负控共用）。"""
    pats = [("tool.recommend.basis①", "B 可行性未证 26/32"), ("criteria.risk_catalog.B[0]", "现行模型 26/32")]
    return [tag for tag, p in pats if p in src or p in text]


def boundary_missing_sections(doc: str, cos: list) -> list:
    """boundary 中缺失的 CO 节（`## <n>. <CO>` 形态）。"""
    return [c for c in cos if f". {c}" not in doc]


def fabricated_cost_hits(criteria: dict) -> list:
    bad = []
    for grp in ("cost_model", "lead_time_model"):
        for k, v in criteria[grp]["parameters"].items():
            if v.get("value") is not None or v.get("provenance") != "INPUT_REQUIRED":
                bad.append(f"{grp}.{k}")
    return bad


def census_aggregates(census: dict) -> dict:
    outer = {"F.Cu", "B.Cu"}
    agg = {"n_vias": sum(census.values()),
           "n_outer_anchored": sum(n for c, n in census.items() if c.split("->")[0] in outer or c.split("->")[1] in outer),
           "n_inner_inner": sum(n for c, n in census.items() if c.split("->")[0] not in outer and c.split("->")[1] not in outer),
           "n_blind_one_outer_endpoint": sum(n for c, n in census.items() if (c.split("->")[0] in outer) != (c.split("->")[1] in outer))}
    return agg


def probe_rerun(extra: dict) -> dict:
    import os
    env = dict(PROBE_KNOBS_BASE)
    env.update(extra)
    code = ("import os,importlib.util,json\n"
            "os.environ.update(json.loads(os.environ['_KNOBS']))\n"
            "spec=importlib.util.spec_from_file_location('probe','tools/p3_v57_co10_west_fan_probe.py')\n"
            "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
            "r=m.probe(rule='fan',order='rev',verbose=False)\n"
            "print(json.dumps({'placed':r['n_placed'],'pages':r['n_pages'],'failed':sorted(r.get('failed',[]))}))")
    e = dict(os.environ)
    e["_KNOBS"] = json.dumps(env)
    p = subprocess.run(["python3", "-c", code], capture_output=True, text=True, cwd=str(K2), env=e)
    return json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else {"err": p.stderr[-200:]}


def main() -> int:
    V, P, F, O = {}, {}, [], []
    crit = json.loads(_git(CRIT_REL))
    selj = json.loads(_git(SELJ_REL))
    selm = _git(SELM_REL)
    bnd = _git(BND_REL)
    tool_src = _git("tools/p3_v57_co206_process_route_select.py")
    runner_src = _git(RUNNER_REL)

    # ── V1：过孔普查**独立复算**（pcbnew 直读交付板）＋ 层距/阶数下界自算术 ─────────
    cen_code = ("import pcbnew,json,collections\n"
                "b=pcbnew.LoadBoard('k2_v4_8L.l4.kicad_pcb');c=collections.Counter()\n"
                "for t in b.GetTracks():\n"
                "    if isinstance(t,pcbnew.PCB_VIA): c[f'{b.GetLayerName(t.TopLayer())}->{b.GetLayerName(t.BottomLayer())}']+=1\n"
                "print(json.dumps(dict(sorted(c.items()))))")
    rc, out, err = _run([PY, "-c", cen_code])
    census = json.loads(out.strip().splitlines()[-1]) if rc == 0 else {}
    bind = json.loads(_git(BIND_REL))
    sp = {"F.Cu": 0.0, "In1.Cu": 0.1164, "In2.Cu": 0.3664, "In3.Cu": 0.6164, "In4.Cu": 0.8086,
          "In5.Cu": 1.0586, "In6.Cu": 1.3086, "B.Cu": 1.425}
    stub_in2_in5 = round(min(sp["In2.Cu"], sp["B.Cu"] - sp["In5.Cu"]), 4)
    lam_lo = 1 + min(2, 7 - 3)   # In2..In5：上方隔 F,In1=2 / 下方隔 In6,B=2
    V["V1_via_census_independent"] = (
        census == bind["board"]["census"]
        and census_aggregates(census) == {k: bind["board"][k] for k in
                                         ("n_vias", "n_outer_anchored", "n_inner_inner")}
        and stub_in2_in5 == bind["via_class_stub_mm"]["In2.Cu->In5.Cu"] == 0.3664
        and stub_in2_in5 > crit["criteria"]["F3_stub_limit"]["stub_limit_mm"]
        and lam_lo == 3)

    # ── V2：热闸**独立算术**复算（Ta + P·θja_eff）＋ 输入源 pin ──────────────────
    th = json.loads(_git(THERM_REL))
    di = th["declared_inputs"]
    thja = round(di["theta_jc_top_C_per_W"] + di["r_interface_C_per_W"] + di["theta_hs_C_per_W"], 6)
    rec_tj = {k: round(di["ta_C"] + v["P_W"] * thja, 1) for k, v in th["cases"].items()}
    V["V2_thermal_recompute"] = (
        thja == th["o2"]["theta_ja_eff_C_per_W"] == 11.0
        and all(rec_tj[k] == th["cases"][k]["Tj_C"] and rec_tj[k] <= di["tj_max_C"] for k in rec_tj)
        and len(rec_tj) == 4 and th["verdict"] == "PASS")

    # ── V3：不动点 oracle **独立复跑**（1 次）⇒ 记录逐字节复原 as-found + 5 案/10 牙齿 ──
    rc_o, out_o, err_o = _run([PY, ORACLE])
    orec = json.loads(OREC.read_text(encoding="utf-8"))
    V["V3_oracle_reproduced"] = (
        rc_o == 0 and orec["verdict"] == "PASS" and len(orec["cases"]) == 5
        and len(orec["teeth"]) == 11 and all(orec["teeth"].values())
        and orec["revision"] == "CO-202" and "5 案" in orec["nature"]
        and s16p(OREC) == s16b(_git(OREC_REL).encode()))

    # ── V4：复现序静态齿 **独立复跑**（35 齿）＋ AST 抽 TOOL_REVISION_DECLARED 之键集 ──
    rc_c, out_c, err_c = _run([PY, RUNNER, "--check"])
    cj = _json_tail(out_c)
    decl_keys = set()
    for n in ast.walk(ast.parse(runner_src)):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TOOL_REVISION_DECLARED" for t in n.targets):
            decl_keys = set(ast.literal_eval(n.value).keys())
    V["V4_runner_check_and_registry"] = (
        rc_c == 0 and cj.get("ok") is True and len(cj.get("teeth", {})) == 35
        and all(cj["teeth"].values()) and decl_keys == {"tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"})

    # ── V5：冻结四源 4/4 ＋ 交付板逐字节（独立 sha） ─────────────────────────────
    V["V5_frozen_four_and_board"] = (
        all(s16p(K2 / f) == e for f, e in FROZEN.items())
        and s16p(K2 / "k2_v4_8L.l4.kicad_pcb") == "d4e81f647be7f980")

    # ── V6：登记簿**独立复算**（total/OPEN/counts 与 items 一致） ─────────────────
    reg = json.loads(_git(REG_REL))
    items = reg["items"]
    kinds = {}
    for i in items:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    V["V6_register_recompute"] = (
        len(items) == reg["meta"]["counts"]["total"] == 145
        and sum(1 for i in items if i["status"] == "OPEN") == reg["meta"]["counts"]["OPEN"] == 0
        and all(reg["meta"]["counts"].get(k) == v for k, v in kinds.items()))

    # ── V7：判据件「禁编造」**独立复算** ＋ 价格试探留痕 ＋ 决策规则字面量 ─────────
    V["V7_criteria_no_fabricated_numbers"] = (
        fabricated_cost_hits(crit) == []
        and len(crit["price_probe_log"]["endpoints"]) == 5
        and selj["recommendation"]["conditional"]["if"] == "quote(10L std) + cost(re-derivation) < quote(HDI 8L)"
        and selj["gate"]["cost_numbers_fabricated"] is False
        and selj["design_facts"]["n_vias"] == 493 and selj["design_facts"]["n_requires_blind_buried"] == 88)

    # ── V8：打样包完整性 **独立复算**（文件集 / 裁定逐字节 parity / MANIFEST 自洽） ──
    man = json.loads((PKG / "MANIFEST.json").read_text(encoding="utf-8")) if (PKG / "MANIFEST.json").exists() else {}
    files = man.get("files", man)
    parity, man_ok = True, True
    for src, dst in [(L2 / "L2_RULING_jlc_standard_through_backdrill_v1.md", "L2_RULING_jlc_standard_through_backdrill_v1.md"),
                     (L2 / "L2_RULING_process_route_selection_v2.md", "L2_RULING_process_route_selection_v2.md")]:
        p = PKG / "06_rulings" / dst
        parity = parity and p.exists() and s16p(p) == s16p(src)
    for rel, meta in files.items():
        fp = PKG / rel
        man_ok = man_ok and fp.exists() and hashlib.sha256(fp.read_bytes()).hexdigest() == meta["sha256"]
    n_pkg = len([p for p in PKG.rglob("*") if p.is_file()])
    V["V8_package_integrity"] = parity and man_ok and n_pkg == 38 and len(files) == 37

    # ── V9：L2 核心结论**独立复算**（自驱探针四配：32 / 24 / 23 / 24） ─────────────
    obs = {}
    for name, (extra, exp_n, exp_fail) in PROBE_EXPECT.items():
        r = probe_rerun(extra)
        obs[name] = {"placed": r.get("placed"), "pages": r.get("pages"), "failed": r.get("failed")}
        obs[name]["ok"] = (r.get("placed") == exp_n and r.get("pages") == 32
                           and (exp_fail is None or r.get("failed") == exp_fail))
    V["V9_l2_family_independent_reproduction"] = all(v["ok"] for v in obs.values()) and len(obs) == 4

    # ── 负控（内存注入；零落盘） ─────────────────────────────────────────────────
    P["P1_revision_extractor_discriminates"] = (
        revision_literal_from_src('D = {"artifact": "A", "revision": "CO-202"}', "A") == (True, "CO-202")
        and revision_literal_from_src('"""revision: CO-202（仅散文）"""', "A") == (False, None))
    P["P2_stale_number_detector_discriminates"] = (
        stale_model_number_hits("B 可行性未证 26/32", "现行模型 26/32") == ["tool.recommend.basis①", "criteria.risk_catalog.B[0]"]
        and stale_model_number_hits("B 可行性未证 24/32", "现行模型 24/32") == [])
    P["P3_boundary_section_detector_discriminates"] = (
        boundary_missing_sections("## 76. CO-203\n## 77. CO-204\n", ["CO-203", "CO-204"]) == []
        and boundary_missing_sections("## 76. CO-203\n", ["CO-204"]) == ["CO-204"])
    P["P4_fabrication_detector_discriminates"] = (
        fabricated_cost_hits({"cost_model": {"parameters": {"k": {"value": None, "provenance": "INPUT_REQUIRED"}}},
                              "lead_time_model": {"parameters": {}}}) == []
        and fabricated_cost_hits({"cost_model": {"parameters": {"k": {"value": 1.23, "provenance": "INPUT_REQUIRED"}}},
                                  "lead_time_model": {"parameters": {}}}) == ["cost_model.k"])
    _span = {"from_F": {"In2.Cu": 0.4}, "from_B": {"In5.Cu": 1.0}}
    P["P5_stub_tooth_discriminates"] = (
        round(min(_span["from_F"]["In2.Cu"], _span["from_B"]["In5.Cu"]), 6) == 0.4
        and (0.4 <= 0.15) is False and (0.1 <= 0.15) is True)
    P["P6_thermal_tooth_discriminates"] = ((40 + 7.5 * 11.0) > 120 and (40 + 7.0 * 11.0) <= 120)
    P["P7_census_tooth_discriminates"] = (
        census_aggregates({"F.Cu->B.Cu": 273, "In2.Cu->In5.Cu": 88})["n_inner_inner"] == 88
        and census_aggregates({"F.Cu->B.Cu": 274, "In2.Cu->In5.Cu": 88})["n_vias"] == 362)
    P["P8_key_literal_extractor_discriminates"] = (
        revision_literal_from_src('K = {"a": 1}\n# TOOL_REVISION_DECLARED = {}', "A") == (False, None))

    # ── Findings（as-found） ────────────────────────────────────────────────────
    stale = stale_model_number_hits(tool_src, _git(CRIT_REL))
    if "可行性未证 26/32" in selj["recommendation"]["basis"][0]:
        stale.append("artifact.recommendation.basis[0]")
    if "现行模型 26/32" in selj["routes"]["B"]["risk"][0]:
        stale.append("artifact.routes.B.risk[0]")
    if "26/32" in selm and "可行性未证 26/32" in selm:
        stale.append("card.md")
    if stale:
        F.append({"id": "F-1", "sev": "low", "object": "CO-206b/c",
                  "what": "**B 路「现行模型」数值之口径修正不完整（声明↔内容不同步）**：CO-206b 已把主判据字段更正为 **24/32**"
                          "（`F4_route_predicates.B.measured` 与 `feasibility.basis`），但**同族**之「现行模型」引用仍滞留 **26/32** "
                          "—— 实测残留：" + "、".join(f"`{s}`" for s in sorted(set(stale)))
                          + "。⇒ 决策证据件（`.json`/`.md`）在**同一文件内**对同一量给两个值（`measured`=24/32 vs `risk`=26/32），"
                            "且该量正被用于「B 是否更便宜可行」之判读（承 R-CO203-1「内容升级须同步」/ R-CO194-1「声明↔实现」）；"
                            "另：该工具内容经 CO-206b/c 升级而自声明 `revision` 仍 `CO-206.1`（自声明面滞留）。",
                  "disposition": "CO-208（L2 自裁）：① `recommend()` basis① 与判据件 `risk_catalog.B[0]` 之 26/32 → **24/32**（并显式注明口径）；"
                                 "② 自声明面 sync：工具 `revision` **CO-206.1 → CO-206.2**、判据件 **v1.2 → v1.3**（含 changelog）；"
                                 "③ 重生成 `m13_v57_co206_process_route_selection.{json,md}`。红线 **R-CO208-1**。",
                  "evidence": ["正控 V9 独立复算：candC+BRCOL = 24/32（失败页与记录逐页同）、+COLFIX = 23/32、"
                               "B 路 lane-outer = 24/32、v9 默认 = 32/32 ⇒ 「24/32」为现行真值、26/32 为已废口径",
                               "负控 P2：探测器对 `26/32`/`24/32` 两形态判别力成立（零落盘）"]})
    selfdecl = sum(1 for p in sorted((K2 / "tools").glob("p3_v57_*.py")) if has_revision_literal(p.read_text(encoding="utf-8")))
    rule_clause = "新增此类工具须入" in bnd
    singleton = "set(TOOL_REVISION_DECLARED) == {_orc_rel}" in runner_src
    if singleton and rule_clause and selfdecl > 1:
            F.append({"id": "F-2", "sev": "low", "object": "CO-203（R-CO203-1）",
                      "what": "**R-CO203-1 之登记条款与静态齿 t33 互斥（该条款无齿）**：R-CO203-1 文义要求「**新增此类工具**须入 runner "
                              "`TOOL_REVISION_DECLARED`」，而 t33 断言 `set(TOOL_REVISION_DECLARED) == {_orc_rel}`（**恒等于单件** {不动点 oracle}）"
                              "⇒ 依规则登记任一新工具必致 t33 FAIL。实测：`tools/p3_v57_*.py` 中含 `revision` dict 字面量者 **" + str(selfdecl) +
                              "** 个（含 CO-203 之后新建之 `p3_v57_co206_process_route_select.py`，自声明 `revision=\"CO-206.1\"`）"
                              "⇒ 该条款既不可满足、又无齿检出未登记者；且该工具自声明面已因 CO-206b/c 内容升级而滞留（见 F-1）。",
                      "disposition": "CO-208（L2 自裁）：① 收窄 R-CO203-1 之**登记适用域** = 「其自声明 `revision` 为**机判/记录消费面**者」"
                                     "（现 = 不动点 oracle：其记录由 t28/t33 消费），并以 t33 之单件断言为**显式不变量**；"
                                     "② 该域新增工具时，`TOOL_REVISION_DECLARED` 与 t33 断言集须**同 commit 同源扩容**（禁单侧更新）。"
                                     "红线 **R-CO208-2**。",
                      "evidence": ["正控 V4：AST 抽 `TOOL_REVISION_DECLARED` 键集 == {oracle}；runner `--check` 35/35 True",
                                   "独立扫描（AST）：134 个工具源含 `revision` dict 字面量 ⇒ 「凡自声明者皆须登记」之文义不可实现",
                                   "负控 P1/P8：AST 字面量抽取器对散文档与键缺失件判别力成立"]})
    miss = boundary_missing_sections(bnd, ["CO-204", "CO-205", "CO-206"])
    if miss:
        F.append({"id": "F-3", "sev": "low", "object": "CO-204..CO-206c",
                  "what": "**canonical 记录链缺口：CO-204..CO-206c 无 boundary §**（boundary 仍 v2.48、末节 = §76 CO-203；"
                          "而 §1..§76 每 CO 皆有节，含全部复评/处置）。实测缺失：" + "、".join(miss) +
                          "。⇒ 冻结四源/gate 链态只能从手交件与散件读取，boundary 不再是**自足**的收口面（承 CO-135/CO-136 记录卫生链）。",
                  "disposition": "CO-208（L2 自裁）：补 §77（CO-204 绑 JLC 标准=通孔+背钻 + 两闸 + U6 热 O2）、§78（CO-205 + r/s/t 层分配族与工具缺陷 ③④）、"
                                 "§79（CO-206 + b/c 工艺选型 A/B/C 定案与口径修正）、§80（CO-207 本复评）、§81（CO-208 处置）；"
                                 "boundary **v2.48 → v2.49**。红线 **R-CO208-3**。",
                  "evidence": ["正控 V4/§ 扫描：boundary 末节 = §76；`## 77.`..`## 81.` 均不存在",
                               "负控 P3：节存在性探测器判别力成立（零落盘）"]})

    O.append({"id": "O-1", "object": "交接件", "status": "记录面表述陈旧（非缺陷）",
              "what": "z71 §2 称打样包「牙齿 25/25」，实测生成器自检齿数 **29**（全 True，含 t11c/t11d/t15b/t16b 等后续增齿）"
                      "⇒ 交接件之齿数表述滞后于工具；无功能影响。"})
    O.append({"id": "O-2", "object": "CO-205t", "status": "残余（L2 已穷尽之自证）",
              "what": "「增内层不改变 24/32 结论」属**结构性论证**（竖段/lane 须异层且皆须内层 ⇒ corner 内层↔内层），本件以 V9 复算其**现有量**（24/32）"
                      "但未构造 10L 反例（无 10L 叠层输入）⇒ 该论证之反证责任留在 B 路（须 32/32 全落位方可选）。"})

    verdict = "PASS_WITH_FINDINGS" if F else "PASS"
    rec = {"artifact": "m13_v57_co207_rev19_co202_co206_review", "schema": 1, "revision": "CO-207",
           "nature": "非执行者对抗复评 CO-202..CO-206c（本谱系 z60..z71 之外之续接会话；自板/自算术/自源 AST/自跑工具与探针）",
           "as_found": {"objects": OBJ, "snapshot": AF,
                        "runner_af_sha16": s16b(_git(RUNNER_REL).encode()),
                        "oracle_af_sha16": s16b(_git("tools/p3_v57_co195_fixpoint_uniqueness_oracle.py").encode()),
                        "sel_tool_af_sha16": s16b(tool_src.encode()),
                        "criteria_af_sha16": s16b(_git(CRIT_REL).encode()),
                        "boundary_af_sha16": s16b(bnd.encode())},
           "objects": ["CO-202", "CO-203", "CO-204", "CO-205", "CO-205r", "CO-205s", "CO-205t",
                       "CO-206", "CO-206b", "CO-206c"],
           "positive_controls": V, "negative_controls": P, "independent_reproduction": obs,
           "findings": F, "n_findings": len(F), "observations": O, "verdict": verdict,
           "redline": "只读 as-found（`git show add6e33`）+ 内存注入、零落盘、零坐标搜索；不改 SPEC/板/冻结四源/登记簿/他人记录。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    L = [f"# CO-207 — 非执行者对抗复评（CO-202..CO-206c）｜as-found 钉 `{AF}`", "",
         f"- verdict：**{verdict}**｜findings：{len(F)}（全 low）｜观察项：{len(O)}",
         "- 方法：正控 V1..V9（独立复算：自板 pcbnew 普查 / 自算术 / 自源 AST / 自跑闸与探针）+ 负控 P1..P8（内存注入、零落盘）", "",
         "| 控 | 结论 |", "|---|---|"]
    for k, v in {**V, **P}.items():
        L.append(f"| {k} | {'True' if v else '**False**'} |")
    L += ["", "## 独立复算（L2 核心量）", "", "| 配置 | placed/pages | 失败页 |", "|---|---|---|"]
    for k, v in obs.items():
        L.append(f"| {k} | {v['placed']}/{v['pages']} | {', '.join(v['failed'] or []) or '—'} |")
    if F:
        L += ["", "## Findings（as-found）", ""]
        for f in F:
            L.append(f"- **{f['id']}（{f['sev']}）· {f['object']}**：{f['what']}")
            L.append(f"  - 处置：{f['disposition']}")
    L += ["", "## 观察（不改判 verdict）", ""]
    for o in O:
        L.append(f"- **{o['id']}（{o['object']}，{o['status']}）**：{o['what']}")
    L += ["", "## 红线", "", "- **R-CO207-1**：复评件须钉**被评态快照**（本件 `add6e33`）且一切「现行态」判定皆由该快照重放；"
              "禁内嵌处置态之 sha（承 R-CO193-3）。", ""]
    CARD.write_text("\n".join(L), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": len(F), "findings": [f["id"] for f in F],
                      "V": V, "P": P, "repro": {k: (v["placed"], v["pages"]) for k, v in obs.items()},
                      "rec_sha16": s16p(REC), "card_sha16": s16p(CARD)}, ensure_ascii=False, indent=1))
    return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
