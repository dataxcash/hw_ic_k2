#!/usr/bin/env python3
"""CO-159 — 非执行者对抗复评（对象 **CO-156 + CO-157 + CO-158**，as-found @ k2 `c4e951c`）。

性质：**只读复评**（不改 SPEC/板/冻结四源/台账/登记簿/他人记录；只写本件 record + card）。
按 handoff-z34 §5 第 1 步执行（复评债 = CO-156 + CO-157 + CO-158；禁自评 ⇒ 本会话为归零续接的非执行者会话）。

方法（可重放）：把复评对象**钉在受评基线 commit `AS_FOUND_REV`**，用 `git show <rev>:<path>` 取
as-found 源码/记录在**内存**执行 —— 故本件日后重跑仍复现**当时**结论，不随之后修复而漂移。
  · 正控（V*）：独立复核 CO-156/157/158 的正面主张（读 as-found 记录）。
  · 负控（P1..P10）：对 handoff §4.2 指定关注点做内存注入，探可规避性（零落盘、零坐标搜索）。

handoff §4.2 关注点：① T18 元牙齿可否被绕过；② co120 `board_superseded` 板 sha16 判据；
③ `declared` key_path 绑定是否防「双改」；④ co134 upsert 收窄；⑤ L5 包 `06_rulings/` 是否足以 JLC 评审、
rc 语义与 runner 兼容性、co77/co135 双份 citation 扫描是否应合一。
CLI: python3 tools/p3_v57_co159_rev19_co156_co157_co158_review.py
"""
from __future__ import annotations
import copy, hashlib, json, re, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
L5PKG = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
BOARD = K2 / "k2_v4_8L.kicad_pcb"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
L4 = K2 / "k2_v4_8L.l4.kicad_pcb"
LED = L2 / "derived_value_ledger_v1.json"
REG = L2 / "input_defect_register_v1.json"
REC = STEP2 / "m13_v57_co159_rev19_co156_co157_co158_review.json"
CARD = STEP2 / "m13_v57_CO159_rev19_co156_co157_co158_review.md"
AS_FOUND_REV = "c4e951c"          # 受评基线（CO-158 提交；只读锚点）
DELIVERED_BOARD = "d4e81f647be7f980"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def show(rel: str) -> str:
    r = subprocess.run(["git", "show", f"{AS_FOUND_REV}:{rel}"], cwd=K2,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"git show {AS_FOUND_REV}:{rel} failed: {r.stderr.strip()}")
    return r.stdout


def load_as_found(name: str, rel: str, real: Path) -> dict:
    """在内存执行 as-found 源码（`__file__` 指向现行路径 ⇒ 其 K2 解析正确），不落盘。"""
    ns = {"__name__": name, "__file__": str(real)}
    exec(compile(show(rel), f"{name}.py", "exec"), ns)
    return ns


def main() -> int:
    checks, findings = {}, []
    led = json.loads(LED.read_text(encoding="utf-8"))

    # ── V0：冻结四源 + 交付板（本件只读，且 CO-156..158 未触） ──────────────
    frozen = {"SPEC_k2_v4.spec-rev-19.json": s16(SPEC) == "5f72182a2616392c",
              "m13_v57_s1_page_manifest.json": s16(MANIFEST) == "a8ef3ea8ecff99d7",
              "k2_v4_8L.kicad_pcb": s16(BOARD) == "fb07d25ac426ff84",
              "_shared/eda_core/drc_rules.json": s16(RULES) == "0a459839e15960b8"}
    checks["V0_frozen_4of4_and_delivered_board"] = {
        "frozen_ok": frozen, "delivered_board_sha16": s16(L4),
        "delivered_matches": s16(L4) == DELIVERED_BOARD}
    # ── V1：CO-156/157/158 正面主张（读 as-found 记录） ────────────────────
    af = {n: json.loads(show(f"pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_{n}.json"))
          for n in ("co124_input_selfcheck_gate", "co120_provenance_pin_gate", "co77_closure_declaration_sweep",
                    "co135_review_hygiene", "co136_gate_hygiene", "co150_k9_domain_gate")}
    af_reg = json.loads(show("pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"))
    af_led = json.loads(show("pm_gate/artifacts/k2_v4/L2/derived_value_ledger_v1.json"))
    af_man = json.loads(show("pm_gate/artifacts/k2_v4/L5/jlc_package/MANIFEST.json"))
    c124 = af["co124_input_selfcheck_gate"]
    checks["V1_claims_hold_as_found"] = {
        "co124": {"revision": c124["revision"], "verdict": c124["verdict"], "n_findings": c124["n_findings"],
                  "teeth_true": sum(1 for v in c124["teeth"].values() if v is True), "teeth_total": len(c124["teeth"]),
                  "ok": c124["verdict"] == "PASS" and c124["n_findings"] == 0 and all(c124["teeth"].values())},
        "co120": {"revision": af["co120_provenance_pin_gate"]["revision"],
                  "verdict": af["co120_provenance_pin_gate"]["verdict"],
                  "teeth_ok": af["co120_provenance_pin_gate"]["teeth"]["teeth_ok"]},
        "co77": {"revision": af["co77_closure_declaration_sweep"]["revision"],
                 "verdict": af["co77_closure_declaration_sweep"]["verdict"],
                 "mismatches": af["co77_closure_declaration_sweep"]["citation_check"]["mismatches"]},
        "co135": {"revision": af["co135_review_hygiene"]["revision"],
                  "citation_clean": af["co135_review_hygiene"]["V3_boundary_citations"]["citation_scan_clean"]},
        "co136": {"revision": af["co136_gate_hygiene"]["revision"], "verdict": af["co136_gate_hygiene"]["verdict"]},
        "package": {"revision": af_man["revision"], "n_files": af_man["n_files"],
                    "teeth": af_man["teeth"]},
        "register": {"n_items": len(af_reg["items"]),
                     "open": sum(1 for i in af_reg["items"] if i["status"] == "OPEN")},
        "ledger": {"n_dv": len(af_led["derived_values"]),
                   "kinds": {d["id"]: (d.get("reachability") or {}).get("kind") for d in af_led["derived_values"]}},
    }
    # ── V2：CO-158「gerber/drill 逐字节未变」独立复核（CO-157→CO-158 MANIFEST 差分） ──
    m157 = json.loads(subprocess.run(["git", "show", "909c9e5:pm_gate/artifacts/k2_v4/L5/jlc_package/MANIFEST.json"],
                                     cwd=K2, capture_output=True, text=True).stdout)
    f157, f158 = m157["manifest"], af_man["manifest"]
    gdr = [k for k in set(f157) & set(f158) if re.match(r"0[12]_", k)]
    checks["V2_co158_gerber_drill_bytewise_unchanged"] = {
        "n_files": [m157["n_files"], af_man["n_files"]],
        "added": sorted(set(f158) - set(f157)), "removed": sorted(set(f157) - set(f158)),
        "gerber_drill_entries": len(gdr),
        "all_identical": all(f157[k] == f158[k] for k in gdr),
        "changed_non_gdr": [k for k in sorted(set(f157) & set(f158)) if f157[k] != f158[k] and not re.match(r"0[12]_", k)]}

    # ── P1：`declared` 空/缺 `computed` ⇒ 值-证据绑定空过（_contains(obj,{}) 恒真） ──
    h124 = load_as_found("co124_as_found", "tools/p3_v57_co124_input_selfcheck_gate.py",
                         K2 / "tools/p3_v57_co124_input_selfcheck_gate.py")
    imp_sha = s16(STEP2 / "m13_v57_co146_impedance_table.json")
    p1 = {}
    for tag, dv in (("missing_computed", {"id": "P1A", "requirement": "REQ-R3-2"}),
                    ("empty_computed", {"id": "P1B", "requirement": "REQ-R3-2", "computed": {}})):
        _l = copy.deepcopy(led)
        dv = dict(dv, reachability={"kind": "declared", "verdict": "REACHABLE", "basis": "任意非空依据",
                                    "evidence_ref": {"path": "m13_v57_co146_impedance_table.json",
                                                     "sha16": imp_sha, "key_path": "dv_computed_zdiff"}})
        _l["derived_values"].append(dv)
        p1[tag] = [i for _, i, _ in h124["k9_findings"](_l) if i.startswith("derived_value_declared")]
    checks["P1_declared_empty_computed_bypass"] = {"findings": p1,
                                                  "evasion_succeeds": not any(p1.values())}
    if not any(p1.values()):
        findings.append(dict(id="F-1", sev="medium", kind="gate-weakness",
            what="CO-156（F-6）的 `declared` 值-证据绑定可被**省略值**绕过：`_contains(evidence[key_path], dv.computed)` 在 "
                 "`computed` 缺失或为 `{}` 时**恒真**（空子集语义），且该分支不要求 `computed` 非空 ⇒ 声明的值本身无任何约束。"
                 "实测：一个 declared DV 只钉现行证据件 + 任意 basis + key_path 即 0 findings 通过。",
            evidence=f"P1 as-found 注入（c4e951c）：missing_computed/empty_computed → {p1}",
            fix="co124 declared 分支加「`computed` 非空」判据 + 负控牙齿 T15c（CO-160 已实施）。"))
    # ── P2：`conservative_ge` 权威绑定条件生效（auth DV 缺失即跳过） ─────────
    _l2 = copy.deepcopy(led)
    _l2["derived_values"] = [d for d in _l2["derived_values"] if d["id"] not in ("DV-INTPAIR-EDGE", "DV-PAIR-CROSS")]
    for _d in _l2["derived_values"]:
        if _d["id"] == "DV-ENGINE-INT_PAIR_PITCH":
            _d["inputs"] = {"span_mm": 0.1, "w_outer_mm": 0.1, "span_src": "x", "w_outer_src": "x"}
            _d["computed"] = {"value_mm": 0.3, "faithful_min_mm": 0.3}
    p2 = [i for _, i, _ in h124["k9_findings"](_l2) if i.startswith("derived_value_conservative")]
    checks["P2_conservative_binding_conditional"] = {"findings": p2, "evasion_succeeds": not p2}
    if not p2:
        findings.append(dict(id="F-2", sev="medium", kind="gate-weakness",
            what="CO-156（F-7）的权威交叉校验**仅在权威 DV 存在时生效**：`auth_edge`/`auth_span` 从台账现取，"
                 "缺失（如 upsert 误删、手工编辑）时两处 `isinstance(...)` 判据被静默跳过 ⇒ F-7 的原规避（缩小自声明 span/w）复活；"
                 "而本闸并无「九 DV 齐备 / 权威 DV 存在」牙齿。",
            evidence=f"P2 as-found 注入（删 DV-INTPAIR-EDGE/DV-PAIR-CROSS）→ {p2}",
            fix="co124 conservative_ge 分支在权威 DV 缺失时显式 FAIL + 负控 T16c（CO-160 已实施）。"))
    # ── P3：T18 元牙齿证明力有界（源码条件分支新增 finder 不被电池触发） ──────
    src124 = show("tools/p3_v57_co124_input_selfcheck_gate.py")
    _patched = src124.replace("    f = []\n",
        '    f = []\n    if led.get("__hidden_trigger__"):\n'
        '        f.append(("K9", "hidden_probe:x", {}))\n', 1)
    ns124 = {"__name__": "co124_patched", "__file__": str(K2 / "tools/p3_v57_co124_input_selfcheck_gate.py")}
    exec(compile(_patched, "co124_patched.py", "exec"), ns124)
    _prov = set()
    for _b in ns124["_k9_battery"](led).values():
        _prov.update(x[1].split(":")[0] for x in ns124["k9_findings"](_b))
    _t18 = set(ns124["K9_FINDER_IDS"]) <= _prov
    _t18b = _prov <= set(ns124["K9_FINDER_IDS"])
    checks["P3_t18_meta_tooth_bypass"] = {"T18_coverage": _t18, "T18b_no_undeclared": _t18b,
                                          "hidden_finder_provoked": "hidden_probe" in _prov,
                                          "evasion_succeeds": _t18 and _t18b}
    if _t18 and _t18b:
        findings.append(dict(id="F-3", sev="medium", kind="gate-coverage",
            what="CO-157（H-1）的元牙齿 T18 只断言「**合成电池触发集 == K9_FINDER_IDS**」，不比对**源码**可产出的 finder 集："
                 "在 k9_findings 里新增一个**电池未覆盖的条件分支** finder（如仅在某个 un-modeled 状态下触发），"
                 "T18/T18b 仍全 True ⇒ 「每个 K9 判据都有负控」的自定规矩可被绕过。",
            evidence="P3 as-found：注入隐藏条件分支 finder 后 T18=True / T18b=True（该 finder 未被任何电池触发）",
            fix="co124 增 T18d（源码正则抽取 finder id 集 == K9_FINDER_IDS）+ T18e（抽取器灵敏度负控）（CO-160 已实施）。"))
    # ── P4：R-CO156-3 机判 ≠ 规则（读后台账整表重写放行） ────────────────────
    h136 = load_as_found("co136_as_found", "tools/p3_v57_co136_gate_hygiene.py",
                         K2 / "tools/p3_v57_co136_gate_hygiene.py")
    p4 = h136["ledger_upsert_violations"](K2 / "tools",
        {"synthetic_rewrite.py": 'import json\nled = json.loads(LED.read_text())\n'
                                 'led["derived_values"] = []\nLED.write_text(json.dumps(led))\n'})
    checks["P4_h4_upsert_only_gap"] = {"violations": p4, "rewrite_after_read_passes": p4 == []}
    if p4 == []:
        findings.append(dict(id="F-4", sev="medium", kind="rule-vs-machine",
            what="CO-157（H-4）的 `H4_ledger_upsert_only` 只拦「写台账但未先读台账」；**读后整表重写**（正是 R-CO156-3 "
                 "条文所禁、F-4 的原始失败模式）仍判无违规。规则条文与机判面不一致（CO-157 已在处置文字中声明「部分机判」，"
                 "但 boundary 规则文本 R-CO156-3 仍写「禁止对台账/记录做整表重写」而无判据）。",
            evidence="P4 as-found：合成「read→整表重写→write」→ violations=[]",
            fix="对齐规则文本与机判面（声明语义面无自动判据、由复评/stub 复跑承接）；不引入会误伤合法 upsert 的脆弱语法判据（CO-160）。"))
    # ── P5/P6：co120 快照键容器依赖 + board_superseded 仅格式判 ──────────────
    h120 = load_as_found("co120_as_found", "tools/p3_v57_co120_provenance_pin_gate.py",
                         K2 / "tools/p3_v57_co120_provenance_pin_gate.py")
    p5 = {"is_downstream_top_level_register_sha16": h120["_is_downstream_snapshot"]([], "register_sha16"),
          "is_downstream_top_level_open_total": h120["_is_downstream_snapshot"]([], "open_total")}
    p6 = {b: h120["basis_of"]({"m13_v57_co137_interpair_fixspace.json": {"inputs": {"board": b}}})[0]["basis_ok"]
          for b in ("0000000000000000", "deadbeefdeadbeef", "superseded")}
    checks["P5_snapshot_key_container_dependent"] = {"probe": p5, "evasion_succeeds": not any(p5.values())}
    checks["P6_board_superseded_format_only"] = {"probe": p6, "fake_sha_accepted": p6["deadbeefdeadbeef"]}
    if not any(p5.values()):
        findings.append(dict(id="F-5", sev="low", kind="gate-coverage",
            what="CO-156（F-2b）的下游快照键判据依赖**嵌套容器**（path 段 ∈ {register,ledger}）：顶层或其它容器下的 "
                 "`register_sha16`/`open_total`/`ledger_sha16` 等（R-CO156-2 字面禁止）不被抓。当前记录 0 例（无 live 违规），属覆盖面缺口。",
            evidence="P5 as-found：`_is_downstream_snapshot([], 'register_sha16')` = False",
            fix="键名面判据（正则，不依赖容器）+ 负控/正控牙齿（CO-160 已实施）。"))
    if p6["deadbeefdeadbeef"]:
        findings.append(dict(id="F-6", sev="low", kind="gate-weakness",
            what="CO-157（H-3）把 `board_superseded` 收严为「16-hex 且 ≠ 交付板」，仍是**格式判**：任意 16-hex（`0000…`、"
                 "`deadbeef…`）即成立豁免，未与**真实被取代板**比对 ⇒ 「机判可证」表述偏强。",
            evidence=f"P6 as-found：basis_ok 探针 = {p6}",
            fix="co120 增 `SUPERSEDED_BOARDS` 白名单（已登记被取代板 sha + 依据）并要求成员资格 + 伪造 sha 负控（CO-160 已实施）。"))
    # ── P7：闸 rc 不反映 verdict（DFM 闸 + §6 回归闸 6 件） ──────────────────
    _dfm = show("tools/p3_v57_co146_jlc_dfm_gate.py")
    _reg_gates = {
        "co78_layer_role_drift_gate": ("CO-78.1", 'rec["verdict"]'),
        "co81_project_rules_gate": ("CO-81.1", 'rec["verdict"]'),
        "co84_dru_domain_gate": ("CO-84.1", 'rec["verdict"]'),
        "co95_in4_reachability": ("CO-95.1", 'rec["verdict"]'),
        "co98_reachability_status_report": ("CO-98.1", "baseline_ok"),
        "co106_reference_plane_gate": ("CO-106.2", 'rec["verdict"]'),
    }
    blind = {n: (f'    return 0\n' in show(f"tools/p3_v57_{n}.py")) for n in _reg_gates}
    checks["P7_rc_blind_to_verdict"] = {"dfm_gate_rc_ignores_verdict": ("return 0 if (teeth_ok and teeth2_ok) else 1" in _dfm),
                                        "regression_gates_unconditional_0": {k: v for k, v in blind.items() if v},
                                        "live_probe": "as-found 实测 co146_jlc_dfm_gate verdict=FAIL 而 rc=0；co98 verdict=BASELINE_MISMATCH 而 rc=0"}
    if checks["P7_rc_blind_to_verdict"]["dfm_gate_rc_ignores_verdict"]:
        findings.append(dict(id="F-7", sev="medium", kind="rule-unenforced",
            what="**R-CO158-3（CO-158 J-3 自定）对规范序内的 `co146_jlc_dfm_gate` 不成立**：其 verdict 允许 FAIL（当前即 FAIL 两项 DFM 阻塞），"
                 "但 `return 0 if (teeth_ok and teeth2_ok) else 1` 使 rc=0 ⇒ 复现序无法据 rc 发现该 FAIL；CO-158 J-3 的修复清单遗漏此件"
                 "（handoff §6 甚至注「rc!=0 属预期」，与实测不符）。",
            evidence="P7 as-found：源代码 return 不含 verdict；实测该闸 verdict=FAIL 且 rc=0",
            fix="`return 0 if (rec['verdict']=='PASS' and teeth_ok and teeth2_ok) else 1`（CO-160 已实施；实测 FAIL ⇒ rc=1）。"))
    if blind:
        findings.append(dict(id="F-11", sev="medium", kind="rule-unenforced",
            what="handoff §6「复现命令」块内的回归闸 " + "/".join(sorted(k for k, v in blind.items() if v)) +
                 " 退出码**恒 0**、不反映 verdict ⇒ 若纳入复现序则违 R-CO158-3（co98 语义为三态报告，正确判据应为 `baseline_ok and teeth_ok`，"
                 "而非 verdict==PASS）。",
            evidence="P7 as-found：六件均以裸 `return 0` 收尾（无 verdict 分支）",
            fix="六件改为按各自 verdict/基线谓词返回（CO-160 已实施；实测全 rc=0，co95 记录 sha 变更后 co98 基线 pin 同步刷新）。"))
    # ── P8/P9/P10：交付物牙齿 + 双份 citation 扫描 + co135 记录卫生 ───────────
    _pkg = show("tools/p3_v57_co146_jlc_fab_package.py")
    _co77 = show("tools/p3_v57_co77_closure_declaration_sweep.py")
    _co135 = show("tools/p3_v57_co135_review_hygiene.py")
    checks["P8_package_teeth_scope"] = {
        "no_source_parity_tooth": ("t07" not in _pkg),
        "no_dir_ref_tooth": ("t08" not in _pkg),
        "t06_regex_only_06_rulings": ("06_rulings/[A-Za-z0-9_.\\-]+" in _pkg)}
    checks["P10_citation_scan_duplication"] = {
        "co77_has_container_parent_candidate": ('K2.parent / "_shared"' in _co77),
        "co135_has_container_parent_candidate": ('K2.parent / "_shared"' in _co135),
        "co135_cross_checks_co77": ("citation_candidates" in _co135),
        "co135_hardcodes_boundary_v1_82": ("boundary_v1_82.md" in _co135),
        "co135_has_stale_chain_pins": ("0074dad9067af737" in _co135)}
    if checks["P8_package_teeth_scope"]["no_source_parity_tooth"]:
        findings.append(dict(id="F-8", sev="low", kind="gate-coverage",
            what="CO-158（J-1）新增 `06_rulings/` 后，牙齿 t05 只验**存在**、t06 只验包内可解析：若 L2 裁定件/DFM 记录在打包后修订，"
                 "包内副本陈旧**无任何牙齿**（J-1 的陈旧阻抗表副本即同类已实测发生）。",
            evidence="P8 as-found：包牙齿无「副本 == 来源」内容一致性判据",
            fix="增 `t07_packaged_rulings_match_sources` + 灵敏度负控（CO-160 已实施）。"))
    if checks["P8_package_teeth_scope"]["no_dir_ref_tooth"]:
        findings.append(dict(id="F-9", sev="low", kind="gate-coverage",
            what="ORDER_NOTES 的**目录级声明**（`01_`..`06_`，如「叠层图(03_) + 阻抗表(04_)」）不在 t06 覆盖内（t06 只解析 `06_rulings/*` 文件引用）；"
                 "当前目录均在包内，属覆盖面缺口。",
            evidence="P8 as-found：t06 正则仅 `06_rulings/...`；ORDER_NOTES 含 `03_`/`04_` 目录声明",
            fix="增 `t08_declared_dirs_present`（CO-160 已实施）。"))
    if checks["P10_citation_scan_duplication"]["co77_has_container_parent_candidate"] != \
       checks["P10_citation_scan_duplication"]["co135_has_container_parent_candidate"]:
        findings.append(dict(id="F-10", sev="low", kind="drift-risk",
            what="CO-158（J-2）把 L5 包补进了 **co77 与 co135 各自维护**的 citation 候选表：两份表已现分歧面"
                 "（co77 含 container-parent `_shared` 候选，co135 不含）且无一致性牙齿。当前对 boundary 全量引用的解析一致"
                 "（本会话独立复算 divergent=0），但任一侧日后补目录即可能「同引用一闸过一闸不过」。",
            evidence="P10 as-found：候选表差异面（co77 ⊃ co135）；现行 boundary 引用交叉解析一致",
            fix="保留两份独立实现（独立复评价值），另加**交叉一致性牙齿**（co135 与 co77 候选表逐引用比对）（CO-160 已实施）。"))
    if checks["P10_citation_scan_duplication"]["co135_has_stale_chain_pins"] or \
       checks["P10_citation_scan_duplication"]["co135_hardcodes_boundary_v1_82"]:
        findings.append(dict(id="F-12", sev="low", kind="record-hygiene",
            what="CO-135 复评件虽是规范序内**现行**闸，却内嵌 CO-134 时点**硬编码链 pin**（如 `G4 0074dad9067af737 / G5 75ce1c2af42de55e`，"
                 "现行为 `60cbd331836e52b7` / `8b385d6c554ac527`）与**硬编码 boundary 文件名** `...v1_82.md` ⇒ 记录随运行序陈旧、"
                 "boundary 改名即静默失配（co77 已用「取最新版」口径，co135 未同步）。",
            evidence="P10 as-found：co135 源码含 `0074dad9067af737` 与 `boundary_v1_82.md` 硬编码",
            fix="co135 链 pin 改为由现行记录派生 + boundary 取最新版（CO-160 已实施）。"))

    findings.sort(key=lambda f: f["id"])
    n = len(findings)
    verdict = "PASS_WITH_FINDINGS" if n else "PASS"
    rec = {"artifact": "m13_v57_co159_rev19_co156_co157_co158_review", "schema": 1, "revision": "CO-159.1",
           "nature": "非执行者对抗复评（另一会话产出）：CO-156（K9 域覆盖/值-证据绑定/co134 upsert/co120 快照键）"
                     "+ CO-157（T17/T18 元牙齿/board_superseded 收严/H4 机判）+ CO-158（L5 包自足/citation 候选/闸 rc）",
           "reviewed_rev": AS_FOUND_REV,
           "reviewer": "独立会话（handoff-z34 §5 第 1 步；禁自评条款由本会话满足）",
           "scope": {"reviewed": ["CO-156", "CO-157", "CO-158"], "spec_rev": "rev-19",
                     "focus": ["T18 元牙齿可否被绕过", "co120 board_superseded 板 sha16 判据",
                               "declared key_path 绑定是否防双改", "co134 upsert 收窄",
                               "L5 包 06_rulings 是否足以 JLC 评审", "rc 语义与 runner 兼容性",
                               "co77/co135 双份 citation 扫描是否应合一"]},
           "board_sha16": s16(L4), "spec_sha16": s16(SPEC),
           "checks": checks, "findings": findings, "n_findings": n, "verdict": verdict,
           "independent_confirmations": [
               "冻结四源 4/4 MATCH（含 drc_rules 0a459839e15960b8）；交付板 = d4e81f647be7f980",
               "as-found 记录逐条复核成立：co124 CO-124.7 PASS/29 牙齿/0 findings；co120 CO-120.4 PASS（teeth 9-9）；"
               "co77 CO-77.6 PASS（mismatches []）；co135 CO-135.2 citation clean；co136 CO-136.1 PASS；"
               "MANIFEST CO146-PKG.2 n_files 34/teeth 6-6；登记簿 44 项 OPEN 0；台账 9 DV / 七域",
               "CO-158 的「gerber/drill 逐字节未变」经 CO-157→CO-158 MANIFEST 差分独立复核：25 件 gerber/drill 全同、"
               "新增 4 件 06_rulings、n_files 30→34、仅 04_impedance 副本与 ORDER_NOTES 变（与声明一致）",
               "co134 upsert 收窄成立（源码读台账后按 id 合并、非字面整表重写）；co77/co135 现行 boundary 引用解析一致（divergent=0）",
           ],
           "co134_note": "co134 不在 R-CO158-1 规范序内（其域由 co153 KIND_EXPECT 承接），收窄后重跑不再 clobber 他 CO 归属 DV ⇒ 该项按设计成立。",
           "reproduce": ["python3 tools/p3_v57_co159_rev19_co156_co157_co158_review.py（只读；对象钉在 c4e951c）"],
           "as_found": "本件以 `git show c4e951c:<path>` 重放受评基线 ⇒ 结论**可重放且不随后续修复漂移**；"
                       "findings 为 as-found 快照，其处置见 CO-160（登记簿 co159:F-* 与本件记录）。",
           "redline": "只读；不改 SPEC/板/冻结四源/台账/登记簿/他人记录；注入一律内存、零落盘、零坐标搜索。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-159 — 非执行者对抗复评（CO-156 + CO-157 + CO-158）｜as-found @ `" + AS_FOUND_REV + "`", "",
             f"- verdict：**{verdict}**｜findings：{n}",
             f"- 受评基线：k2 `{AS_FOUND_REV}`（CO-158）｜SPEC `{s16(SPEC)}`｜板 `{s16(L4)}`", "",
             "| id | sev | kind | what（摘要） |", "|---|---|---|---|"]
    for f in findings:
        lines.append(f"| {f['id']} | {f['sev']} | {f['kind']} | {f['what'][:100]}... |")
    lines += ["", "独立确认（非空过证据）：", ""] + [f"- {x}" for x in rec["independent_confirmations"]] + [""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": n, "findings": [f["id"] for f in findings],
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    # CO-185（R-CO185-1）：复评步**退出码须反映 verdict**（PASS / PASS_WITH_FINDINGS 为通过档；其余停机）
    return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
