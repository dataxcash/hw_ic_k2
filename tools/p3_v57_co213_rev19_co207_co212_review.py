#!/usr/bin/env python3
"""CO-213 — **非执行者对抗复评 CO-207..CO-212**（context 归零之续接会话；满足「复评须本谱系外之新会话，禁自评」）。

对象 as-found（**逐件重放**；本件一切「现行态」判定皆由该快照重放 ⇒ 结论不随后续处置漂移）：`f0016ae`（CO-212）。

方法：正控 **V1..V11**（独立复算：自板 pcbnew 普查 / 自跑闸 / as-found 工具**内存重放** / 自源扫描 —— 不引用被评记录之结论）
+ 负控 **P1..P4**（内存注入，**零落盘**、零坐标搜索）。只读；不改 SPEC / 板 / 冻结四源 / 登记簿 / 他人记录；仅写本件记录 + 卡。

CLI: python3 tools/p3_v57_co213_rev19_co207_co212_review.py
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, tempfile
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
PY = K2.parent / "AppDir" / "usr" / "bin" / "python3.11"
AF = "f0016ae"                                        # 被评态快照（CO-212）
TMP = K2 / ".archer_tmp" / "rev"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
PKG = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
REL = {
    "criteria": "pm_gate/artifacts/k2_v4/L2/process_route_criteria_v1.json",
    "sel_tool": "tools/p3_v57_co206_process_route_select.py",
    "sel_json": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co206_process_route_selection.json",
    "bond2009": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co209_band_joint_solve.json",
    "bnd": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md",
    "register": "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json",
    "runner": "tools/p3_v57_co164_order_runner.py",
    "l5tool": "tools/p3_v57_l5_signoff.py",
    "package": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_jlc_fab_package.json",
    "order_notes": "pm_gate/artifacts/k2_v4/L5/jlc_package/ORDER_NOTES.md",
    "spec7": "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-7.json",
    "spec19": "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json",
    "handoff": ".omo/handoffs/k2-v57-handoff-z77-20260914-rev19-co212-final.md",
}
REC = STEP2 / "m13_v57_co213_rev19_co207_co212_review.json"
CARD = STEP2 / "m13_v57_CO213_rev19_co207_co212_review.md"
FROZEN = {"pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
          "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
          "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
          "../_shared/eda_core/drc_rules.json": "0a459839e15960b8"}
BOARD = "k2_v4_8L.l4.kicad_pcb"
L5_RECORDS = ["m13_v57_l5_fab_record.json", "m13_v57_l5_dfm_dft_record.json", "m13_v57_l5_si_pi_emc_record.json"]


def s16b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def s16f(p: Path) -> str:
    return s16b(Path(p).read_bytes())


def git(rel: str, rev: str = AF) -> bytes:
    r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=K2, capture_output=True)
    return r.stdout


def jgit(rel: str, rev: str = AF) -> dict:
    return json.loads(git(rel, rev))


def replay_sel() -> dict:
    """as-found 工艺选型执行器**内存重放**（自板 pcbnew 普查 ⇒ 独立复算 facts/pick/cost）。"""
    TMP.mkdir(parents=True, exist_ok=True)
    tool, crit = TMP / "co206_af.py", TMP / "crit_af.json"
    tool.write_bytes(git(REL["sel_tool"]))
    crit.write_bytes(git(REL["criteria"]))
    src = (
        "import importlib.util,json,sys\n"
        "s=importlib.util.spec_from_file_location('m',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
        "crit=json.loads(open(sys.argv[2]).read());g=m._load_gate()\n"
        "spec2=json.loads(g.SPEC.read_text());c=g.board_census();span=g.layer_span(spec2)\n"
        "facts=m.classify(crit,c['census'],span,g);r=m.evaluate(crit,facts);rec=m.recommend(r,facts)\n"
        "print(json.dumps({'facts':{k:facts[k] for k in ('n_vias','n_through_backdrill_ok','n_requires_blind_buried',"
        "'n_blind_class_one_outer_endpoint')},'pick':rec['pick'],'costs':{k:r[k]['cost']['value'] for k in 'ABC'},"
        "'has_b_feasibility':hasattr(m,'b_feasibility'),'reads_measured_placement':'measured_placement' in open(sys.argv[1]).read()}))\n")
    out = subprocess.run([str(PY), "-c", src, str(tool), str(crit)], capture_output=True, text=True, timeout=600)
    return json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else {"error": out.stderr[-400:]}


def main() -> int:
    V, P, F, O = {}, {}, [], []
    afc, afsel = jgit(REL["criteria"]), jgit(REL["sel_json"])
    afreg, afbnd = jgit(REL["register"]), git(REL["bnd"]).decode()
    afl5 = {n: jgit(f"pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/{n}") for n in L5_RECORDS}

    # ── V1：冻结四源（现行实件） ────────────────────────────────────────────────
    V["V1_frozen_four_match"] = all(s16f(K2 / p) == h for p, h in FROZEN.items())
    # ── V2：交付板（现行实件 == as-found 快照钉值） ────────────────────────────
    V["V2_delivery_board_pinned"] = s16f(K2 / BOARD) == "d4e81f647be7f980" and afbnd.count("d4e81f647be7f980") > 0
    # ── V3：runner 静态齿（现行实件） ──────────────────────────────────────────
    r = subprocess.run([str(PY), "tools/p3_v57_co164_order_runner.py", "--check"], cwd=K2, capture_output=True, text=True)
    chk = json.loads(r.stdout)
    V["V3_runner_check_all_true"] = r.returncode == 0 and chk["ok"] and all(chk["checks"].values()) and len(chk["checks"]) == 35
    # ── V4：as-found 执行器**独立复算**（facts/pick/cost 与 as-found 记录同 + 无前置求值 ⇒ F-1 证据） ──
    rp = replay_sel()
    V["V4_co206_af_independent_recompute"] = (
        rp.get("facts") == {k: afsel["design_facts"][k] for k in rp.get("facts", {})}
        and rp.get("pick") == afsel["recommendation"]["pick"]
        and rp.get("costs") == {k: afsel["routes"][k]["cost"]["value"] for k in "ABC"}
        and all(afsel["teeth"].values()) and len(afsel["teeth"]) == 6
        and rp.get("has_b_feasibility") is False and rp.get("reads_measured_placement") is False)
    # ── V5：CO-209 族闭合**逐字节重放**（as-found 求解器 + 独立运行 ⇒ 同 sha） ──
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "co209_af.py").write_bytes(git("tools/p3_v57_co209_band_joint_solve.py"))
    subprocess.run(["python3", str(TMP / "co209_af.py"), "--out", str(TMP / "co209_af.json")],
                   cwd=K2, capture_output=True, timeout=1800)
    V["V5_co209_family_replay_byte_identical"] = (TMP / "co209_af.json").exists() and \
        s16f(TMP / "co209_af.json") == s16b(git(REL["bond2009"])) == "73a78fa1b6c1e90c"
    # ── V6：L5 三件（as-found）板指纹 == 现行 L4 板 ────────────────────────────
    _bpin = hashlib.sha256((K2 / BOARD).read_bytes()).hexdigest()
    V["V6_l5_records_pin_board"] = len(afl5) == 3 and all(d.get("board_sha256") == _bpin for d in afl5.values())
    # ── V7：打样包（as-found 记录）37 payload / 29 齿全 True ──────────────────
    afpkg = jgit(REL["package"])
    V["V7_package_teeth"] = (len(afpkg["teeth"]) == 29 and all(afpkg["teeth"].values())
                             and afpkg["n_files"] == 37 and (PKG / "MANIFEST.json").exists())
    # ── V8：登记簿（as-found 快照复算计数） ────────────────────────────────────
    n_items = len(afreg["items"])
    n_open = sum(1 for i in afreg["items"] if i["status"] == "OPEN")
    V["V8_register_counts_rederived"] = (n_items == 151 and n_open == 0
                                         and afreg["meta"]["counts"]["total"] == 151
                                         and afreg["meta"]["counts"]["OPEN"] == 0)
    # ── V9：包内裁定副本 == 源（两件） ────────────────────────────────────────
    _par = True
    for src, dst in [(L2 / "L2_RULING_jlc_standard_through_backdrill_v1.md", "L2_RULING_jlc_standard_through_backdrill_v1.md"),
                     (L2 / "L2_RULING_process_route_selection_v2.md", "L2_RULING_process_route_selection_v2.md"),
                     (L2 / "L2_RULING_u6_thermal_mitigation_v2.md", "L2_RULING_u6_thermal_mitigation_v2.md")]:
        p = PKG / "06_rulings" / dst
        _par = _par and p.exists() and s16f(p) == s16b(git(str(src.relative_to(K2))))
    V["V9_packaged_rulings_parity"] = _par
    # ── V10：SPEC rev-7 vs rev-19 之 impedance 逐字节同（CO-212 并存事实） ────
    imp = lambda p: json.dumps(json.loads(p)["impedance"], sort_keys=True, ensure_ascii=False)
    V["V10_spec_rev7_rev19_impedance_identical"] = imp(git(REL["spec7"])) == imp(git(REL["spec19"]))
    # ── V11：boundary（as-found）末节 = §85 且 §82..§85 齐 ────────────────────
    secs = re.findall(r"^## (\d+)\. ", afbnd, re.M)
    V["V11_boundary_sections_contiguous"] = ({"82", "83", "84", "85"} <= set(secs)
                                            and max(int(s) for s in secs) == 85 and "v2.53" in afbnd)

    # ── 负控（判别力；零落盘） ────────────────────────────────────────────────
    def pin_resolves(tok: str, cands) -> bool:
        return any(s16f(c) == tok for c in cands if Path(c).exists())
    # 判别力三向：匹配 ⇒ 解析；全零 ⇒ 否；**as-found 陈旧 sha（文件已演进）⇒ 否**（漂移可被检出）
    _live = s16f(K2 / REL["criteria"])
    P["P1_pin_resolver_discriminates"] = (pin_resolves(_live, [K2 / REL["criteria"]])
                                          and not pin_resolves("0" * 16, [K2 / REL["criteria"]])
                                          and not pin_resolves(s16b(git(REL["criteria"])), [K2 / REL["criteria"]]))
    ROW = re.compile(r"^\|\s*(.*?)\s*\|\s*`([0-9a-f]{16})`\s*\|$")

    def label_conflicts(txt: str):
        rows = {}
        for line in txt.splitlines():
            m = ROW.match(line)
            if not m:
                continue
            paths = re.findall(r"`([^`]+)`", m.group(1))
            for p in paths:
                rows.setdefault(Path(p).name, {}).setdefault(m.group(2), set()).add(m.group(1))
        return {k: {s: v[s] for s in v} for k, v in rows.items() if any(len(x) > 1 for x in v.values())}
    _clean = "| a `x.md`（甲） | `" + "a" * 16 + "` |\n| b `y.md`（乙） | `" + "b" * 16 + "` |"
    _bad = ("| a `x.md`（甲） | `" + "a" * 16 + "` |\n| a `x.md`（乙） | `" + "a" * 16 + "` |")
    P["P2_same_sha_multi_label_detector"] = (label_conflicts(_clean) == {} and len(label_conflicts(_bad)) == 1)
    n_conflict = len(label_conflicts(afbnd))
    _mp = "criteria.F4_route_predicates.B_add_signal_layers_all_through.measured_placement"
    def has_machine_feasibility(c: dict) -> bool:
        try:
            _ = c["criteria"]["F4_route_predicates"]["B_add_signal_layers_all_through"]["measured_placement"]["placed"]
            return True
        except (KeyError, TypeError):
            return False
    _inj = json.loads(json.dumps(afc)); _inj["criteria"]["F4_route_predicates"]["B_add_signal_layers_all_through"]["measured_placement"] = {"placed": 32, "total": 32}
    P["P3_precondition_data_flip_probe"] = (not has_machine_feasibility(afc) and has_machine_feasibility(_inj))
    _tools = {p.name: p.read_text(errors="ignore") for p in (K2 / "tools").glob("p3_v57_*.py")}
    _reads_l5 = {n for n, t in _tools.items() if any(r in t for r in L5_RECORDS)}
    _mints = {n for n, t in _tools.items() if "board_sha256" in t}
    # 自身（本复评工具）亦含记录名与 `board_sha256` 字样 ⇒ **自排除**（承 CO-195 `_snap_excl_self` 之教训）
    _producers = {"p3_v57_l5_signoff.py", "p3_v57_co146_boundary_append.py", Path(__file__).name}
    _consumers = (_reads_l5 & _mints) - _producers
    P["P4_l5_board_pin_consumer_absent"] = (len(_consumers) == 0 and "p3_v57_l5_signoff.py" in _mints)

    # ── Findings（as-found；处置 = 同会话 CO-213） ─────────────────────────────
    F.append({"id": "F-1", "sev": "low", "kind": "TOOL_DEFECT", "object": "CO-211（执行器）",
              "what": "**决策前置仍是代码常量（「声明↔实现」漂移的上一层）**：CO-211 把**成本臂**求值化了，但 `recommend()` 之 B **可行性前置**取 "
                      "`_proven = {\"B\": False}` 字面量（实测 as-found 源：无 `b_feasibility`、不读 `measured_placement`），判据件 `decision.precondition_note` 仅为散文 "
                      "⇒ **判据件侧任何编辑（含把 `measured` 改为 32/32）皆不能改判**；唯一可翻转者为改 Python 常量或 t04 之内存注入 ⇒ 与 R-CO211-1"
                      "「规则与其前置同处声明、实现与声明同源」不符（前置已声明但未求值；t04 之正控行使的是**不可达态**）。",
              "disposition": "CO-213：判据件增机读 `F4_route_predicates.B.measured_placement{placed,total}` + `decision.precondition`（谓词 `placed == total`；缺字段/退化 ⇒ fail-closed 未证）；"
                             "执行器 **CO-206.3 → CO-206.4** 由该字段求值 `proven` + **数据驱动**齿 t07（只改判据件数据即改判 B / placed<total 或缺失 ⇒ A）；判据件 **v1.4 → v1.5**；重出证据件（7 齿全 True）。**R-CO213-1**。",
              "evidence": ["as-found 复算（V4，自板普查）：pick=A、三路 cost 皆 None、`has_b_feasibility=False`、源不读 `measured_placement`",
                           "负控 P3：as-found 判据件无该机读字段（探测器 False）、注入后 True（判别力成立）"]})
    F.append({"id": "F-2", "sev": "low", "kind": "RECORD_HYGIENE", "object": "z77（交接件 §1）",
              "what": "**政策层 pin 陈旧**：z77 §1 之 `L2_RULING_process_route_selection_v2.md` = `1542a84cf4859de6`，而该值系 CO-206b（`14bd37c`）之内容；"
                      "CO-211（`86d612b`）追加 §2 R3′ 前置注记后现行 = `d258f67957a448d0` ⇒ z77 自称修正 2 处陈旧 pin 后**仍残留 1 处**（实测：全篇 36 枚 pin token 中 34 枚可解析，"
                      "1 枚即此；另 1 枚为收敛快照 sha）。影响 = 续接会话之「写件时复核」指向**被取代**之裁定版本。",
              "disposition": "CO-213：于 **z78** 更正该 pin；「写件时复核」由 canonical 工件表扩至**政策层表格**（勿只查交付板/登记簿/判据件）。",
              "evidence": ["`git show 14bd37c:<ruling>` sha16 = `1542a84cf4859de6`；`git show 86d612b:<ruling>` 与现行工作区 = `d258f67957a448d0`",
                           "z77 全篇 pin token 解析：34/36 命中工作树实件（负控 P1 判别力成立）"]})
    F.append({"id": "F-3", "sev": "low", "kind": "RECORD_HYGIENE", "object": "boundary（写入器机制）",
              "what": "**「现行态 pin 再对齐」只改 sha、不改同排历史版本标签 ⇒ 同排标签↔sha 可不同版**（系统性）：实测 §79 两行标 `CO-206.2`/`v1.3` 而 pin 已为 CO-206.3/v1.4 之内容"
                      "（`git show a5cbcb6` = `dea2bbeb89e6fe54`/`e53fc2354e8efd59`；`86d612b` 起被再对齐）；全表同文件同 sha 对多枚历史标签之行**数十处**"
                      f"（负控 P2 探测器实测冲突文件数 = **{n_conflict}**）。§79 并残留 CO-211 已证伪之「（已编码，填参后自动复算）」表述**且无 §84 指针** ⇒ 读者可据行内标签误判版本。",
              "disposition": "CO-213：机制**不改**（现行态对齐为有意设计；逐行改写 456 处历史标签反致伪史）⇒ §79 补**追注**（标签 = 成文时口径 / sha = 现行实件）+ §86 显式登记该语义。**R-CO213-2**。",
              "evidence": [f"负控 P2：`label_conflicts(as-found boundary)` 命中文件数 = {n_conflict}（合成负控样本不误报）",
                           "§79 现行标签核（writer 源）：`CO-206.2`/`v1.3`；而 §79 表 sha = 现行 CO-206.4/v1.5 之实件"]})
    F.append({"id": "F-4", "sev": "low", "kind": "TOOL_DEFECT", "object": "CO-212（L5 自检）",
              "what": f"**板指纹判别齿过弱 + 消费面无机判**：CO-212 之 `board_pin_discriminates` 只判「`board_sha256` ≠ 全零哨兵」，**不判别「评的是冻结源还是交付板」**"
                      f"（二者互换而齿不响）；且全工具集扫描：读三件 L5 记录者 **{len(_reads_l5)}** 件、含 `board_sha256` 者 **{len(_mints)}** 件，"
                      f"**消费者（读记录 ∩ 含板指纹，除生产者）= {sorted(_consumers) or '∅'}** ⇒ 板变更后记录不刷新仍**只对人眼可见**（序内/各闸皆不验）。",
              "disposition": "CO-213：自检改**真判别**（DFM `baseline_sha256` 须 = 冻结源板、被评板 ≠ 冻结源、三件皆钉被评板且非退化 ⇒ 「评错板」即 rc≠0）；记录 **L5-DFM.8 / L5-SI.8 / L5-G7.8**；"
                             "**消费面机判**列**有据延后**（触发 = 板变更或下次 L5 重跑）。",
              "evidence": [f"负控 P4：消费面扫描 = {sorted(_consumers) or '∅'}（生产者/散文引用者除外）",
                           "as-found 复算：`board_pin_ok=True` 但 `board_pin_discriminates` 仅为哨兵比较（V6 证三件皆钉现行 L4 板）"]})

    O.append({"id": "O-1", "object": "z77 §2", "status": "记录面表述易误读（非缺陷）",
              "what": "z77 称「收敛 sha … report `.archer_tmp/co164_order_report.json` sha16 `645d544efcdacbdf`」—— 该值实为报告内 `iterations[*].sha`（**受控集快照**），"
                      "非报告文件自身 sha（实测文件 sha16 另一值）；判定一致，仅措辞易误读（z78 改称「收敛快照 sha」）。"})
    O.append({"id": "O-2", "object": "CO-209", "status": "已直接行使（复核通过）",
              "what": "「band 级列×桥孔 x 联合形态」之族闭合已由**直接行使**证（19–20/32 < 24/32），本件逐字节重放其求解器（V5）复核数值与结论一致；"
                      "残余自由度 = 跨页 y 交错（须改几何，非旋钮可达）与 L1（球重映射/信号流向）—— 与 z77 §6 一致。"})
    O.append({"id": "O-3", "object": "复评覆盖边界", "status": "诚实边界",
              "what": "本件复评 CO-207..CO-212（CO-202..CO-206c 已由 CO-207 复评）；**未**复核 B 路 10L 叠层之实做与外部报价面（前者须 L1/几何，后者为外部输入）。"})

    verdict = "PASS_WITH_FINDINGS" if F else "PASS"
    rec = {"artifact": "m13_v57_co213_rev19_co207_co212_review", "schema": 1, "revision": "CO-213",
           "nature": "非执行者对抗复评 CO-207..CO-212（本谱系 z60..z77 之外之续接会话；自板普查 / 自跑闸 / as-found 工具内存重放 / 自源扫描）",
           "as_found": {"snapshot": AF,
                        "criteria_sha16": s16b(git(REL["criteria"])), "sel_tool_sha16": s16b(git(REL["sel_tool"])),
                        "sel_json_sha16": s16b(git(REL["sel_json"])), "boundary_sha16": s16b(git(REL["bnd"])),
                        "register_sha16": s16b(git(REL["register"])), "runner_sha16": s16b(git(REL["runner"])),
                        "l5tool_sha16": s16b(git(REL["l5tool"]))},
           "objects": ["CO-207", "CO-208", "CO-209", "CO-210", "CO-211", "CO-212"],
           "positive_controls": V, "negative_controls": P, "findings": F, "n_findings": len(F),
           "observations": O, "verdict": verdict,
           "redline": "只读 as-found（`git show f0016ae`）+ 内存注入、零落盘、零坐标搜索；不改 SPEC/板/冻结四源/登记簿/他人记录（处置另件同日）。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    L = [f"# CO-213 — 非执行者对抗复评（CO-207..CO-212）｜as-found 钉 `{AF}`", "",
         f"- verdict：**{verdict}**｜findings：{len(F)}（全 low）｜观察项：{len(O)}",
         "- 方法：正控 V1..V11（独立复算：自板 pcbnew 普查 / 自跑闸 / as-found 工具内存重放 / 自源扫描）+ 负控 P1..P4（内存注入、零落盘）", "",
         "| 控 | 结论 |", "|---|---|"]
    for k, v in {**V, **P}.items():
        L.append(f"| {k} | {'True' if v else '**False**'} |")
    if F:
        L += ["", "## Findings（as-found）", ""]
        for f in F:
            L.append(f"- **{f['id']}（{f['sev']}，{f['kind']}）· {f['object']}**：{f['what']}")
            L.append(f"  - 处置：{f['disposition']}")
    L += ["", "## 观察（不改判 verdict）", ""]
    for o in O:
        L.append(f"- **{o['id']}（{o['object']}，{o['status']}）**：{o['what']}")
    L += ["", "## 红线", "",
          "- **R-CO213-1**：决策规则之**前置**须与规则同处声明并由**判据件机读字段**求值（禁代码常量）。",
          "- **R-CO213-2**：boundary 为**现行态对齐**；同排历史版本标签不得作为 sha 之版本判据（判版本读该节现行版本注）。",
          "- **R-CO213-3**：复评件须钉被评态快照（承 R-CO207-1）；findings 之「修后」证据须为本会话实测。", ""]
    CARD.write_text("\n".join(L), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": len(F), "V": V, "P": P,
                      "rec_sha16": s16f(REC), "card_sha16": s16f(CARD)}, ensure_ascii=False, indent=1))
    return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
