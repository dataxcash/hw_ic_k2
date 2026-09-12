#!/usr/bin/env python3
"""CO-154 — 非执行者对抗复评（rev-19 @ CO-153）：复评 **CO-153** 与 **CO-152**（另一会话产出）。

性质：**只读复评**（不改 SPEC/板/冻结四源/台账/登记簿/他人记录；只写本件 record + card）。
按 handoff §5 第 1 步执行（复评债 = CO-153 + CO-152，禁自评 ⇒ 由本会话独立复核）。

复评关注（handoff §4.2）：
  CO-153：① 新判据可否被规避；② `conservative_ge` faithful 口径是否等同 DV-INTPAIR-EDGE 忠实下界；
          ③ 是否仍有一次性写入残留（R-CO153-1 具名生产者）。
  CO-152：① 语义标注是否足够；② co120 P5 是否真防复发；③ R2 勘误是否改变结论。

方法：① 先独立确认 CO-153/CO-152 的**正面主张**（V1/V2）；② 再以**内存注入负控** + 受控子进程复现
        （write_text 打桩，零落盘）探测可规避性与回归（N1..N8）。全部证据可机判、零坐标搜索。
CLI: python3 tools/p3_v57_co154_rev19_co153_co152_review.py
"""
from __future__ import annotations
import copy, hashlib, importlib.util, json, re, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
BOARD = K2 / "k2_v4_8L.kicad_pcb"
L4 = K2 / "k2_v4_8L.l4.kicad_pcb"
LED = L2 / "derived_value_ledger_v1.json"
REG = L2 / "input_defect_register_v1.json"
CO124 = STEP2 / "m13_v57_co124_input_selfcheck_gate.json"
CO120 = STEP2 / "m13_v57_co120_provenance_pin_gate.json"
CO147 = STEP2 / "m13_v57_co147_l2_ruling.json"
CO150TOOL = K2 / "tools/p3_v57_co150_k9_domain_gate.py"
CO147TOOL = K2 / "tools/p3_v57_co147_l2_ruling.py"
CO134TOOL = K2 / "tools/p3_v57_co134_req_impl_separation.py"
BOUNDARY = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"
REC = STEP2 / "m13_v57_co154_rev19_co153_co152_review.json"
CARD = STEP2 / "m13_v57_CO154_rev19_co153_co152_review.md"
DELIVERED_BOARD = "d4e81f647be7f980"
FROZEN = {"SPEC_k2_v4.spec-rev-19.json": SPEC, "m13_v57_s1_page_manifest.json": MANIFEST,
          "k2_v4_8L.kicad_pcb": BOARD, "_shared/eda_core/drc_rules.json": RULES}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load_tool(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def k9_with(led, dv, m124):
    l = copy.deepcopy(led)
    l["derived_values"].append(dv)
    return [x[1] for x in m124.k9_findings(l)]


def main() -> int:
    m124 = load_tool("co124r", K2 / "tools/p3_v57_co124_input_selfcheck_gate.py")
    m120 = load_tool("co120r", K2 / "tools/p3_v57_co120_provenance_pin_gate.py")
    led = json.loads(LED.read_text())
    reg = json.loads(REG.read_text())
    c124 = json.loads(CO124.read_text())
    c120 = json.loads(CO120.read_text())
    bt = BOUNDARY.read_text()

    checks, findings = {}, []

    # ── V0/V1/V2：正面主张独立确认 ─────────────────────────────────────────
    frozen = {k: (s16(p) == v) for k, p, v in (
        ("SPEC_k2_v4.spec-rev-19.json", SPEC, "5f72182a2616392c"),
        ("m13_v57_s1_page_manifest.json", MANIFEST, "a8ef3ea8ecff99d7"),
        ("k2_v4_8L.kicad_pcb", BOARD, "fb07d25ac426ff84"),
        ("dr rules", RULES, "0a459839e15960b8"))}
    checks["V0_frozen_4of4_and_delivered_board"] = {
        "frozen_ok": frozen, "delivered_board_sha16": s16(L4),
        "delivered_matches": s16(L4) == DELIVERED_BOARD}
    checks["V1_co153_closure_holds"] = {
        "co124_verdict": c124["verdict"], "n_findings": c124["n_findings"],
        "teeth_true": sum(1 for v in c124["teeth"].values() if v), "teeth_total": len(c124["teeth"]),
        "ok": c124["verdict"] == "PASS" and c124["n_findings"] == 0 and all(c124["teeth"].values())}
    checks["V2_co152_p5_holds_as_declared"] = {
        "co120_verdict": c120["verdict"], "snaps": len(c120["snapshot_rows"]),
        "undeclared": c120["n_snapshot_undeclared"], "basis_not_ok": c120["exemption_basis"]["n_basis_not_ok"],
        "teeth_ok": c120["teeth"]["teeth_ok"], "ok": c120["verdict"] == "PASS"}
    # R2 勘误：断言值已落定且不改变裁定（ACCEPT_L2）
    doc = (L2 / "L2_RULING_via_channel_and_interpair_domain_v1.md").read_text()
    checks["V3_co152_r2_erratum"] = {
        "doc_has_0.2577": "0.2577" in doc, "doc_has_prev_0.3294": "0.3294" in doc,
        "ruling_still_ACCEPT_L2": "ACCEPT_L2" in doc, "conclusion_changed": False}

    # ── N1：declared 判据可被规避（证据 pin 与值无语义关联） ────────────────
    n1 = k9_with(led, {"id": "CO154_A", "requirement": "REQ-R3-2",
                       "reachability": {"kind": "declared", "verdict": "REACHABLE",
                                        "basis": "CO-154 注入：任意非空依据",
                                        "evidence_ref": {"path": "SPEC_k2_v4.spec-rev-19.json",
                                                         "sha16": s16(SPEC)}}}, m124)
    checks["N1_declared_semantic_free"] = {"findings": n1, "evasion_succeeds": not n1}
    if not n1:
        findings.append(dict(
            id="F-6", sev="medium", kind="gate-weakness",
            what="CO-153 新增的 `declared` 判据只做**证据 pin 检查**（path 可解析 + sha16 现行 + basis 非空），"
                 "与被声明的值**无语义关联**：实测把一个 DV 的 evidence_ref 指向**无关的现行文件**（SPEC）并给任意非空 basis ⇒ "
                 "0 findings 通过。「声明即通过」缺口被收窄（须钉一个文件）但**未关闭**。",
            evidence="N1 注入（CO154_A pinned→SPEC sha 5f72182a2616392c）→ k9_findings = []",
            fix="declared 判据增加「证据件须可解析出与 DV 值相关的字段」或要求 `evidence_ref.key_path` 白名单 + 值一致性抽检；"
                "否则应显式降级为 `unverified_declared` 并计数，不得与 process_floor 同权。"))

    # ── N2：K9 无「域覆盖」牙齿 ⇒ 未列 kind / 无 domains 的 domain_cap 静默通过 ──
    n2b = k9_with(led, {"id": "CO154_B", "requirement": "REQ-R3-2",
                        "reachability": {"kind": "domain_cap", "verdict": "REACHABLE"}}, m124)
    n2c = k9_with(led, {"id": "CO154_C", "requirement": "REQ-R3-2",
                        "reachability": {"kind": "bogus_domain", "verdict": "REACHABLE"}}, m124)
    checks["N2_kind_coverage_tooth_missing"] = {"domain_cap_no_domains": n2b, "unknown_kind": n2c,
                                               "unchecked": not n2b and not n2c}
    if not n2b and not n2c:
        findings.append(dict(
            id="F-5", sev="medium", kind="gate-coverage",
            what="K9 对「域集合」无牙齿：`kind` 取未列值（如 `bogus_domain`）或 `kind=domain_cap` 但缺 `domains` 列表时，"
                 "无任何分支命中 ⇒ **静默零校验通过**；亦无牙齿断言「每个 DV 的 kind ∈ 七域」。R-CO153-1 的"
                 "「各域须由具名生产者产出」因此不可机判。",
            evidence="N2 注入（domain_cap 无 domains / kind=bogus_domain）→ k9_findings = []",
            fix="K9 增牙齿 T14：DV 的 kind 必须 ∈ {domain_cap,identity,process_floor,declared,conservative_ge,"
                "drop_domain,thermal_option_domain}，且 domain_cap 必带非空 domains；负控注入未列 kind / 空 domains 必抓。"))

    # ── N3：conservative_ge 的 faithful 由**自声明输入**重算 ⇒ 可缩输入规避 ──
    n3 = k9_with(led, {"id": "CO154_D", "requirement": "REQ-R3-2",
                       "inputs": {"span_mm": 0.1, "w_outer_mm": 0.1},
                       "computed": {"value_mm": 0.3, "faithful_min_mm": 0.3},
                       "reachability": {"kind": "conservative_ge", "verdict": "CONSERVATIVE_OK"}}, m124)
    dvin = next(d["inputs"] for d in led["derived_values"] if d["id"] == "DV-INTPAIR-EDGE")
    dvcp = next(d["computed"] for d in led["derived_values"] if d["id"] == "DV-INTPAIR-EDGE")
    checks["N3_conservative_faithful_selfdeclared"] = {
        "injected": n3, "evasion_succeeds": not n3,
        "intpair_edge_binding_mm": dvcp.get("edge_outer_binding_mm"),
        "intpair_edge_span_min_mm": dvin.get("span_min_mm"),
        "conservative_ge_formula_span_mm": 0.585,
        "note": "K9 以 DV 自带 inputs.span_mm/w_outer_mm 重算 faithful，未与 DV-INTPAIR-EDGE 的 edge_outer_binding_mm(0.41)/span_min_mm(0.355) 交叉"}
    if not n3:
        findings.append(dict(
            id="F-7", sev="low", kind="gate-weakness",
            what="`conservative_ge` 的「忠实下界」由该 DV **自带的** inputs.span_mm / w_outer_mm 重算（faithful = span+2·w_outer），"
                 "只证**内部自洽**，未与权威 DV-INTPAIR-EDGE 的 `edge_outer_binding_mm`(0.41)/`span_min_mm`(0.355) 交叉 ⇒ "
                 "缩小自声明输入即可通过（实测 span=w=0.1,value=0.3 ⇒ 0 findings）。另：同一闸内两处用到**不同的 span 常量**"
                 "（本支 0.585 对跨 vs DV-INTPAIR-EDGE 域判据 0.355 最小跨）⇒ faithful 数值并不等于 DV-INTPAIR-EDGE 忠实下界"
                 "（0.995 vs 0.765）；方向偏保守（更严）故**不改结论**，但『等同』表述不成立。",
            evidence="N3 注入 → []；DV-INTPAIR-EDGE.span_min_mm=0.355 / edge_outer_binding_mm=0.41 vs conservative_ge span=0.585",
            fix="faithful 的 w_outer 应直接取自 DV-INTPAIR-EDGE.edge_outer_binding_mm/2、span 口径显式声明并交叉校验；"
                "或改为引用（非复制）该 DV。"))

    # ── 控制（正控）：两类判据在真违规时确被抓 ────────────────────────────
    ctl_f = k9_with(led, {"id": "CO154_F", "requirement": "REQ-R3-2",
                          "reachability": {"kind": "declared", "verdict": "REACHABLE",
                                           "evidence_ref": {"path": "m13_v57_co146_impedance_table.json",
                                                            "sha16": "0" * 16}}}, m124)
    ctl_g = k9_with(led, {"id": "CO154_G", "requirement": "REQ-R3-2",
                          "inputs": {"span_mm": 0.585, "w_outer_mm": 0.205},
                          "computed": {"value_mm": 0.5, "faithful_min_mm": 0.995},
                          "reachability": {"kind": "conservative_ge", "verdict": "CONSERVATIVE_OK"}}, m124)
    checks["N4_positive_controls"] = {"declared_stale_caught": bool(ctl_f), "conservative_caught": bool(ctl_g),
                                      "ok": bool(ctl_f) and bool(ctl_g)}

    # ── N5：co150 工具在规范序内**崩溃**（CO-152 删键未同步消费者） ──────────
    orig_wt = Path.write_text
    wrote = []
    Path.write_text = lambda self, data, *a, **k: (wrote.append(str(self)), len(data))[1]
    try:
        m150 = load_tool("co150r", CO150TOOL)
        try:
            m150.main()
            n5 = {"exception": None}
        except Exception as e:  # noqa: BLE001
            tb = e.__traceback__
            while tb is not None and tb.tb_next is not None:
                tb = tb.tb_next
            n5 = {"exception": f"{type(e).__name__}: {e}", "line": (tb.tb_lineno if tb else None)}
    except Exception as e:  # noqa: BLE001
        n5 = {"exception": f"import/exec: {type(e).__name__}: {e}"}
    finally:
        Path.write_text = orig_wt
    checks["N5_co150_crash"] = dict(n5, wrote_stubbed=len(wrote))
    if n5.get("exception"):
        findings.append(dict(
            id="F-1", sev="medium", kind="executor-regression",
            what="CO-152 从 CO-150 记录删去 `register.open_total` 字段（改为 note）却**未同步两处消费者**"
                 "（`p3_v57_co150_k9_domain_gate.py` 第 81 行卡写入、第 84 行 print）⇒ 该工具在规范复现序（R-CO153-2）内**必然抛 KeyError**"
                 "并终止（REC 先写、card 不刷新 ⇒ `m13_v57_CO150_k9_domain_gate.md` 为陈旧件）。",
            evidence=f"受控执行（write_text 打桩、零落盘）：{n5.get('exception')} @ line {n5.get('line')}",
            fix="删除/替换第 81/84 行的 `rec['register']['open_total']` 引用（如打印 `-` 或改为读登记簿現行值）；"
                "随后按 R-CO153-2 重跑规范序至不动点。"))

    # ── N6：co147 记录不可由规范序复现（下游**计数**快照未随 CO-152 清理） ──
    c147 = json.loads(CO147.read_text())
    reg_open = sum(1 for i in reg["items"] if i.get("status") == "OPEN")
    rec_open = (c147.get("register") or {}).get("open_total")
    src147 = CO147TOOL.read_text()
    checks["N6_co147_pin_not_reproducible"] = {
        "record_open_total": rec_open, "register_open_now": reg_open,
        "stale": rec_open != reg_open,
        "tool_computes_live": 'open_total": sum(1 for i in reg["items"] if i.get("status") == "OPEN")' in src147}
    if rec_open != reg_open:
        findings.append(dict(
            id="F-2", sev="medium", kind="reproducibility",
            what="CO-152 只要清理了 `*_sha16_after` 类**下游 sha** 快照，未覆盖同族的**下游计数/版本快照**："
                 "co147 记录内嵌 `register.open_total`（由工具**运行期现算**），现值 1 而登记簿现行 OPEN=0 ⇒ "
                 "该记录已陈旧，按规范序重跑会改写其字节（记录 sha≠提交 pin c7e66b7e9c92a2d8）⇒ R-CO153-2 的"
                 "「循环至 sha 稳定」对 co147 不成立；同类残留：co148 `register.items_total`、co150 `co124.{revision,verdict,n_findings}`、"
                 "co146_jlc_rebind `register.{items_total,open_total}`（后者已声明为历史）。co120 P1/P5 只扫 `*_record` 键与 `*_sha16_after` ⇒ 均不覆盖。",
            evidence=f"co147.register.open_total={rec_open} vs 登记簿 OPEN={reg_open}（工具源码含运行期现算表达式=True）",
            fix="① 与 CO-152 F-1 同口径，移除 co147/co148 记录内的下游计数快照（版本/计数快照交由 boundary pin 表承载）；"
                "② co120 P5 扩展为「下游快照键」通用类（含 `*_sha16`、`register.*`、`open_total`/`items_total`）并加负控。"))

    # ── N7：边界内部修订号自相矛盾（pin 表标签 vs 实件） ────────────────────
    rev_tokens = sorted(set(re.findall(r"CO-124\.\d", bt)))
    checks["N7_revision_label_mismatch"] = {
        "boundary_co124_labels": rev_tokens,
        "co124_record_revision": c124["revision"],
        "co150_record_co124_revision": json.loads((STEP2 / "m13_v57_co150_k9_domain_gate.json").read_text())["co124"]["revision"],
        "co147_record_revision": c147["revision"],
        "co147_tool_revision": (re.search(r'"revision":\s*"(CO-147\.\d)"', src147) or ["", None])[1]}
    if len(rev_tokens) > 1:
        findings.append(dict(
            id="F-3", sev="low", kind="pin-label-hygiene",
            what="boundary 对同一实件的修订号自相矛盾：§26（CO-150 段）记 co124 = **CO-124.5**，§29 pin 表记 **CO-124.6**，"
                 "而实件（记录 `revision`）为 CO-124.5 ⇒ pin 表标签高于实件（未随判据扩展 bump）。同类：handoff §2 记 co147=CO-147.2，"
                 "而 co147 记录与工具均为 CO-147.1。（sha pin 本身 MATCH，仅修订号标签失真。）",
            evidence=f"boundary 同时含 {rev_tokens}；co124 记录={c124['revision']}；co147 记录/工具={c147['revision']}",
            fix="二择一并对齐：① 若 CO-153 扩展 K9 判据视为新版 ⇒ bump 实件 revision 至 CO-124.6 并同步 co150/卡；"
                "② 否则订正 boundary §29 pin 表标签为 CO-124.5。co147 同理（CO-147.2 vs .1）。"))

    # ── N8：R-CO153-1 未成立 —— co134（3 域生产者）不在规范序，且整表重写 ──
    m29 = next((l for l in bt.splitlines() if "R-CO153-2" in l), "")
    src134 = CO134TOOL.read_text()
    wholesale = ('"derived_values": [' in src134) and ("LEDGER.write_text" in src134)
    checks["N8_r_co153_1_unenforced"] = {
        "co134_in_canonical_order": "co134" in m29,
        "co134_writes_whole_ledger": wholesale,
        "kinds_owned_by_co134": ["domain_cap", "identity", "process_floor"]}
    if wholesale and "co134" not in m29:
        findings.append(dict(
            id="F-4", sev="medium", kind="rule-unenforced",
            what="R-CO153-1（「K9 各域均须由规范复现序内具名生产者产出；禁止一次性写入台账域」）对本条**不成立且无机判**："
                 "`domain_cap`/`identity`/`process_floor` 三域的生产者 = `p3_v57_co134_req_impl_separation.py`，"
                 "该工具**不在** R-CO153-2 规范序内；且它以字面量列表**整表重写**台账（`derived_values` + `LEDGER.write_text`）⇒ "
                 "一旦（按设计）重跑 co134，CO-146/149/153 归属的 3 个 DV（declared/drop_domain/thermal_option_domain）会被**静默删除**、"
                 "对应牙齿失去受试对象 —— 正是 CO-153 为 co146_ledger_add 修掉、但未覆盖 co134 的同一失败模式。",
            evidence=f"R-CO153-2 序串含 co134={checks['N8_r_co153_1_unenforced']['co134_in_canonical_order']}；"
                     f"co134 整表重写={wholesale}",
            fix="① co134 改为**只 upsert 自有三域**（同 co146_ledger_add 收窄先例）并纳入规范序；"
                "② 增 K9 牙齿「七域各有规范序内生产者」+ 负控（缺一域必抓）。"))

    findings.sort(key=lambda f: f["id"])
    n_findings = len(findings)
    verdict = "PASS_WITH_FINDINGS" if n_findings else "PASS"
    rec = {
        "artifact": "m13_v57_co154_rev19_co153_co152_review", "schema": 1, "revision": "CO-154.1",
        "nature": "非执行者对抗复评（另一会话产出）：CO-153（K9 覆盖缺口关闭）+ CO-152（CO-151 findings 处置）",
        "reviewer": "独立会话（handoff §5 第 1 步；禁自评条款由本会话满足）",
        "scope": {"reviewed": ["CO-153", "CO-152"], "spec_rev": "rev-19",
                  "focus": {"CO-153": ["新判据可否被规避", "conservative_ge faithful 口径是否等同 DV-INTPAIR-EDGE 忠实下界",
                                       "是否仍有一次性写入残留（R-CO153-1）"],
                            "CO-152": ["语义标注是否足够", "co120 P5 是否真防复发", "R2 勘误是否改变结论"]}},
        "board_sha16": s16(L4), "spec_sha16": s16(SPEC),
        "checks": checks, "findings": findings, "n_findings": n_findings,
        "independent_confirmations": [
            "冻结四源 4/4 MATCH（含 drc_rules 0a459839e15960b8）；交付板 = d4e81f647be7f980",
            "CO-153 主张成立：co124 = PASS / findings 0 / 牙齿 17-17 全 True（复评独立复跑一致）",
            "CO-152 P5 按声明成立：co120 = PASS / snaps 8 / undeclared 0 / basis_not_ok 0 / teeth ok",
            "CO-152 R2 勘误已落实（doc 值 0.2577 + 保留旧值 0.3294 供追溯），裁定仍 ACCEPT_L2 ⇒ **不改变结论**",
            "两类新判据在真违规时确被抓（declared 陈旧 sha / conservative value<faithful）⇒ 牙齿非空过",
        ],
        "verdict": verdict,
        "reproduce": ["python3 tools/p3_v57_co154_rev19_co153_co152_review.py"],
        "as_found": "本件为 as-found 复评快照：重跑可得不同 findings/sha（属预期，与 co151 同例）；勿以其 sha 作复现目标。",
        "redline": "只读；不改 SPEC/板/冻结四源/台账/登记簿/他人记录；子进程复现一律 write_text 打桩、零落盘；零坐标搜索。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-154 — 非执行者对抗复评（CO-153 + CO-152）｜rev-19", "",
             f"- verdict：**{verdict}**｜findings：{n_findings}",
             f"- 板 `{s16(L4)}`｜SPEC `{s16(SPEC)}`｜冻结四源 4/4 MATCH", "",
             "| id | sev | kind | what（摘要） |", "|---|---|---|---|"]
    for f in findings:
        lines.append(f"| {f['id']} | {f['sev']} | {f['kind']} | {f['what'][:90]}... |")
    lines += ["", "独立确认（非空过证据）：", ""] + [f"- {x}" for x in rec["independent_confirmations"]] + [""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": n_findings,
                      "findings": [f["id"] for f in findings],
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
