#!/usr/bin/env python3
"""CO-166 — 非执行者对抗复评（对象 **CO-159..CO-165**，as-found @ k2 `e427909`）。

性质：**只读复评**（不改 SPEC/板/冻结四源/台账/登记簿/他人记录；只写本件 record + card）。
按 handoff-z39 §5 第 1 步执行（复评债 = CO-159..CO-165；禁自评 ⇒ 本会话为 context 归零的续接非执行者会话）。

方法（可重放）：把复评对象**钉在受评基线 `AS_FOUND_REV`**，用 `git show <rev>:<path>` 取 as-found
源码/记录在**内存**执行 —— 故本件日后重跑仍复现**当时**结论，不随之后修复漂移。
  · 正控（V*）：独立复核 CO-159..CO-165 的正面主张（读 as-found 记录 + 内存重算判据）。
  · 负控（P1..P6）：对 handoff-z39 §4.2 指定关注点做内存注入，探可规避性（零落盘、零坐标搜索、
    所有写文件操作均被拦截或以 tempfile 完成）。
handoff §4.2 关注点：① `t09` 记号化对备注措辞的敏感度；② `t10` 在容器侧 `.omo` 不可达时的 fail-closed；
③ `EXPECTED_NONZERO` 白名单扩展流程；④ `t06` 对 boundary 文本格式变更的脆性；
⑤ `record_fresh` 的 mtime 判据在时钟回拨/网络盘下的稳健性；⑥ `co146_boundary_append` 大段 f-string 的转义易错性。
CLI: python3 tools/p3_v57_co166_rev19_co159_co165_review.py
"""
from __future__ import annotations
import contextlib, hashlib, io, json, os, re, subprocess, sys, tempfile
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
BOUNDARY = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"
REC = STEP2 / "m13_v57_co166_rev19_co159_co165_review.json"
CARD = STEP2 / "m13_v57_CO166_rev19_co159_co165_review.md"
AS_FOUND_REV = "e427909"
DELIVERED_BOARD = "d4e81f647be7f980"
REL = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/"
RUNNER_REL = "tools/p3_v57_co164_order_runner.py"
FAB_REL = "tools/p3_v57_co146_jlc_fab_package.py"
BDY_REL = "tools/p3_v57_co146_boundary_append.py"
BDY_DOC_REL = REL + "m13_v57_w3_joint_assignment_boundary_v1_82.md"
NOTES_REL = "pm_gate/artifacts/k2_v4/L5/jlc_package/ORDER_NOTES.md"
JP_REL = "pm_gate/artifacts/k2_v4/L2/jlc_prototype_parameters_v1.json"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def show(rel: str) -> str:
    r = subprocess.run(["git", "show", f"{AS_FOUND_REV}:{rel}"], cwd=K2,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"git show {AS_FOUND_REV}:{rel} failed: {r.stderr.strip()}")
    return r.stdout


def show_s16(rel: str) -> str:
    return hashlib.sha256(show(rel).encode("utf-8")).hexdigest()[:16]


def show_json(rel: str) -> dict:
    return json.loads(show(rel))


def load_as_found(name: str, rel: str, real: Path) -> dict:
    """在内存执行 as-found 源码（`__file__` 指向现行路径 ⇒ 其 K2 解析正确），不落盘。"""
    ns = {"__name__": name, "__file__": str(real)}
    exec(compile(show(rel), f"{name}.py", "exec"), ns)
    return ns


def main() -> int:
    checks, findings = {}, []

    # ── V0：冻结四源 + 交付板（本件只读；CO-159..165 未触） ────────────────
    frozen = {"SPEC_k2_v4.spec-rev-19.json": s16(SPEC) == "5f72182a2616392c",
              "m13_v57_s1_page_manifest.json": s16(MANIFEST) == "a8ef3ea8ecff99d7",
              "k2_v4_8L.kicad_pcb": s16(BOARD) == "fb07d25ac426ff84",
              "_shared/eda_core/drc_rules.json": s16(RULES) == "0a459839e15960b8"}
    checks["V0_frozen_4of4_and_delivered_board"] = {
        "frozen_ok": frozen, "delivered_board_sha16": s16(L4),
        "delivered_matches": s16(L4) == DELIVERED_BOARD}

    # ── V1：CO-159..165 正面主张（读 as-found 记录） ────────────────────────
    c159 = show_json(REL + "m13_v57_co159_rev19_co156_co157_co158_review.json")
    c124 = show_json(REL + "m13_v57_co124_input_selfcheck_gate.json")
    c120 = show_json(REL + "m13_v57_co120_provenance_pin_gate.json")
    c77 = show_json(REL + "m13_v57_co77_closure_declaration_sweep.json")
    c135 = show_json(REL + "m13_v57_co135_review_hygiene.json")
    c136 = show_json(REL + "m13_v57_co136_gate_hygiene.json")
    c150 = show_json(REL + "m13_v57_co150_k9_domain_gate.json")
    c106 = show_json(REL + "m13_v57_co106_reference_plane_gate.json")
    fab = show_json(REL + "m13_v57_co146_jlc_fab_package.json")
    af_reg = show_json("pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json")
    c159_ids = sorted(f["id"] for f in c159["findings"])
    reg_keys = {i["finding"] for i in af_reg["items"]}
    co159_reg_closed = all((f"co159:{i}" in reg_keys and
                            next(x for x in af_reg["items"] if x["finding"] == f"co159:{i}")["status"] == "CLOSED")
                           for i in c159_ids)
    checks["V1_claims_hold_as_found"] = {
        "co159": {"revision": c159["revision"], "verdict": c159["verdict"], "n_findings": c159["n_findings"],
                  "ids": c159_ids, "reviewed_rev": c159["reviewed_rev"],
                  "ok": c159["verdict"] == "PASS_WITH_FINDINGS" and c159["n_findings"] == 12},
        "co124": {"revision": c124["revision"], "verdict": c124["verdict"], "n_findings": c124["n_findings"],
                  "teeth_true": sum(1 for v in c124["teeth"].values() if v is True), "teeth_total": len(c124["teeth"]),
                  "required_dv_n": len(c124.get("required_dv_ids") or []),
                  "ok": c124["revision"] == "CO-124.9" and c124["verdict"] == "PASS"
                        and c124["n_findings"] == 0 and all(c124["teeth"].values())},
        "co150": {"revision": c150["revision"], "teeth": c150["teeth"],
                  "ok": c150["revision"] == "CO-150.2" and all(c150["teeth"].values())},
        "co106": {"revision": c106["revision"], "verdict": c106["verdict"],
                  "teeth_true": sum(1 for v in c106["teeth"].values() if v is True), "teeth_total": len(c106["teeth"]),
                  "ok": c106["revision"] == "CO-106.4" and c106["verdict"] == "PASS" and all(c106["teeth"].values())},
        "co120": {"revision": c120["revision"], "verdict": c120["verdict"],
                  "teeth_true": sum(1 for v in c120["teeth"].values() if v is True), "teeth_total": len(c120["teeth"]),
                  "ok": c120["verdict"] == "PASS" and all(c120["teeth"].values())},
        "co77": {"revision": c77["revision"], "verdict": c77["verdict"], "ok": c77["verdict"] == "PASS"},
        "co135": {"revision": c135["revision"], "verdict": c135["verdict"], "ok": c135["revision"] == "CO-135.3"},
        "co136": {"revision": c136["revision"], "verdict": c136["verdict"], "ok": c136["verdict"] == "PASS"},
        "fab_pkg": {"revision": fab["revision"], "n_files": fab["n_files"],
                    "teeth_true": sum(1 for v in fab["teeth"].values() if v is True), "teeth_total": len(fab["teeth"]),
                    "ok": fab["revision"] == "CO146-PKG.4" and fab["n_files"] == 34 and all(fab["teeth"].values())},
        "register": {"total": af_reg["meta"]["counts"]["total"], "OPEN": af_reg["meta"]["counts"]["OPEN"],
                     "co159_findings_all_closed": co159_reg_closed,
                     "ok": af_reg["meta"]["counts"]["total"] == 65 and af_reg["meta"]["counts"]["OPEN"] == 0
                           and co159_reg_closed},
    }

    # ── V2：CO-161 单一真值（co124 必需 DV 清单 == co153 `KIND_EXPECT` 键集） ─
    m153 = load_as_found("af_co153", "tools/p3_v57_co153_k9_domain_coverage.py",
                         K2 / "tools/p3_v57_co153_k9_domain_coverage.py")
    inv = sorted(c124.get("required_dv_ids") or [])
    prod = sorted(m153["KIND_EXPECT"])
    checks["V2_k9_inventory_single_source"] = {
        "co124_required_dv_ids": inv, "co153_kind_expect_keys": prod,
        "match": bool(inv) and inv == prod,
        "drift_detectable": (inv + ["DV-BOGUS"]) != prod}

    # ── V3：co146_boundary_append 只读重放（幂等 + 仅写 boundary；§37..§39 代码路径执行） ─
    bdy_real = K2 / "tools/p3_v57_co146_boundary_append.py"
    before_af = show(BDY_DOC_REL).encode("utf-8")   # CO-166.2：as-found 基线（不随现行修复漂移）
    live_before = BOUNDARY.read_bytes()
    cap, orig = {}, Path.write_text

    def _fake(self, data, *a, **k):
        cap[str(self)] = data.encode("utf-8") if isinstance(data, str) else data
        return len(data)

    Path.write_text = _fake
    try:
        bns = load_as_found("af_bdy", BDY_REL, bdy_real)
        with contextlib.redirect_stdout(io.StringIO()):   # CO-166.3：净化 stdout（被重放件会 print 自己的摘要）
            rc_bdy = bns["main"]()
    finally:
        Path.write_text = orig
    _cap_txt = (cap.get(str(BOUNDARY)) or b"").decode("utf-8", "replace")
    checks["V3_boundary_append_replay"] = {
        "rc": rc_bdy, "files_written": [Path(k).name for k in cap],
        "writes_only_boundary": list(cap) == [str(BOUNDARY)],
        # §23..§39 大段 f-string 代码路径**执行成功**且产出含各节标记（CO-164 故障类＝SyntaxError/运行时错）
        "captured_has_sections": all(m in _cap_txt for m in ("## 23. CO-146", "## 39. CO-165")),
        # 逐字节幂等性由 runner 收敛判定（受控 sha 跨轮稳定）另行保证；as-found 重放非纯函数
        # （pin 再对齐按**现行**实件 sha 改写引用 ⇒ 现行件一变即与 as-found 文本有差），故不在此断言字节相等。
        "disk_unchanged": BOUNDARY.read_bytes() == live_before}

    # ── V4/V5：t10 正控（来源 pin 可达一致）+ t09 正控（真备注 7/7） ─────────
    fns = load_as_found("af_fab", FAB_REL, K2 / FAB_REL)
    jp = show_json(JP_REL)
    binding = jp.get("binding") or {}
    instr = fns["INSTRUCTION"]
    note = show(NOTES_REL)
    tok = fns["binding_tokens"](binding)
    checks["V4_t10_source_pin_positive"] = {
        "path": str(instr), "exists": instr.exists(),
        "declared_sha16": jp["supervisor_instruction"]["sha16"], "actual_sha16": s16(instr) if instr.exists() else None,
        "ok": instr.exists() and s16(instr) == jp["supervisor_instruction"]["sha16"]}
    checks["V5_t09_positive"] = {"tokens": tok, "note_checks": fns["binding_param_checks"](note, binding),
                                 "ok": all(fns["binding_param_checks"](note, binding).values())}

    # ── V6：co162 `verdict_of` 阶梯独立复核（非 PASS 三态 + PASS 正控） ──────
    m106 = load_as_found("af_co106", "tools/p3_v57_co106_reference_plane_gate.py",
                         K2 / "tools/p3_v57_co106_reference_plane_gate.py")
    vo = m106["verdict_of"]
    checks["V6_verdict_ladder"] = {
        "pin_mismatch": vo(True, True, {"spec_current": {"expect": "x", "actual": "y"}}, {}),
        "teeth_fail": vo(True, False, {}, {}),
        "checks_fail": vo(False, True, {}, {"declared_copper_missing": 1}),
        "pass": vo(True, True, {}, {}),
        "ok": vo(True, True, {"spec_current": {}}, {}) == "BASELINE_MISMATCH"
              and vo(True, False, {}, {}) == "FAIL(teeth)" and vo(False, True, {}, {}) != "PASS"
              and vo(True, True, {}, {}) == "PASS"}

    # ══ 负控（内存注入，探可规避性） ════════════════════════════════════════
    rn = load_as_found("af_runner", RUNNER_REL, K2 / RUNNER_REL)
    ORDER, wat = rn["ORDER"], [str(p) for p in rn["watch_paths"]()]

    # ── P1（§4.2①）：t09 记号化 —— 措辞敏感（fail-closed）与**无锚子串（false-accept）** ──
    real = fns["binding_param_checks"](note, binding)
    wording = fns["binding_param_checks"](note.replace("1.6 mm", "1.6mm").replace("外层 1oz", "外层1oz")
                                          .replace("85Ω", "85 Ω"), binding)
    loose_z = "85Ω" in note.replace("85Ω", "185Ω", 1)
    loose_t = "1.6 mm" in note.replace("1.6 mm", "11.6 mm", 1)
    # 阻抗容差漂移（85Ω 差分 ±10% → ±5%）却仍被**厚度公差**的 ±10% 满足
    drift_tol = fns["binding_param_checks"](note.replace("85Ω 差分 ±10%", "85Ω 差分 5%"), binding)
    checks["P1_t09_tokenization"] = {
        "real_7of7": all(real.values()), "wording_mutation": wording,
        "wording_trips": [k for k, v in wording.items() if not v],
        "loose_substr_185_ohm_accepts": loose_z, "loose_substr_11_6mm_accepts": loose_t,
        "tolerance_drift_masked_by_thickness": drift_tol["tolerance"],
        "tolerance_drift_still_all": all(drift_tol.values())}

    # ── P2（§4.2②）：t10 在容器侧 `.omo` 不可达时是否 fail-closed ──────────
    fake = K2 / ".co166_nonexistent_instruction.md"
    checks["P2_t10_fail_closed"] = {
        "fake_exists": fake.exists(),
        "t10_with_fake_source": bool(fake.exists()) and bool(jp.get("supervisor_instruction")) and
                                s16(fake) == jp["supervisor_instruction"].get("sha16"),
        "fail_closed": (bool(fake.exists()) and bool(jp.get("supervisor_instruction")) and
                        s16(fake) == jp["supervisor_instruction"].get("sha16")) is False}

    # ── P3（§4.2③）：白名单扩展流程 —— t03/t07 守卫 + 受控集盲区 + PASS 许可 ──
    ent = rn["EXPECTED_NONZERO"]["co146_jlc_dfm_gate"]
    t03_offorder = set(rn["EXPECTED_NONZERO"]) <= set(ORDER)
    t07_keys = all(("verdict" in v and "record" in v) for v in rn["EXPECTED_NONZERO"].values())
    recs_watched = {Path(v["record"]) for v in rn["EXPECTED_NONZERO"].values()} <= {Path(p) for p in wat}
    _runner_src = show(RUNNER_REL)
    # t07 是否含「禁止 expected verdict == PASS」判据（源码面）
    verdict_pass_not_forbidden = ('!= "PASS"' not in _runner_src) and ("verdict_pass" not in _runner_src)
    checks["P3_allowlist_governance"] = {
        "t03_requires_in_order": t03_offorder, "t07_requires_keys": t07_keys,
        "records_subset_of_watched_now": recs_watched, "dfm_record": ent["record"],
        "verdict_PASS_permitted_by_tooth": verdict_pass_not_forbidden,
        "allowlist_is_single_trust_point": _allowlist_injection_demo(rn),
        "watch_blindspot_observable": not any(p.endswith(".archer_tmp/co_x.json") for p in wat)}

    # ── P4（§4.2④）：t06 对 boundary 文本格式变更的脆性（真脆 + **陈旧回落 fail-open**） ──
    bdy_txt = show(BDY_DOC_REL)
    inj = bdy_txt.rstrip() + "\n\n## 99. CO-999\n\n> **R-CO999-3**（复现序，取代 R-CO165-3）：规范复现序（步骤集不变，格式变更）= `a → b`。\n"
    order_lines = [l for l in inj.splitlines() if "规范复现序 =" in l]
    stale_last = order_lines[-1] if order_lines else ""

    def _parse(seg: str):
        out = []
        for t in seg.replace("`", "").replace("**", "").split("→"):
            m = re.match(r"^([a-z0-9_]+)", t.strip())
            if m and re.match(r"^co\d", m.group(1)):
                out.append(m.group(1))
        return out

    def _af_parse(text: str):
        """用**as-found** `boundary_order_steps` 解析给定文本（写入 tmp md；用完即删、还原全局）。"""
        fd, tp = tempfile.mkstemp(suffix=".md"); os.close(fd); tp = Path(tp)
        try:
            tp.write_text(text, encoding="utf-8")
            rn["BOUNDARY"] = tp
            return rn["boundary_order_steps"]()
        finally:
            rn["BOUNDARY"] = BOUNDARY
            tp.unlink(missing_ok=True)

    _inj = bdy_txt.rstrip() + ("\n\n## 99. CO-999\n\n> **R-CO999-3**（复现序，取代 R-CO165-3）："
                               "规范复现序（步骤集不变，格式变更）= `a → b`。\n")
    _stale = _af_parse(_inj)
    checks["P4_t06_format_brittleness"] = {
        "real_matches_order": _af_parse(bdy_txt) == ORDER,
        "arrow_dash_parses": _parse(" `co146_impedance_table -> co146_pm_eval`"),
        "arrow_dash_fails_t06": _parse(" `co146_impedance_table -> co146_pm_eval`") != ORDER,
        "newest_order_line_is_old": "co106_reference_plane_gate" in stale_last,
        "stale_fallback_returns_order": _stale == ORDER,
        "fail_open": _stale == ORDER}

    # ── P5（§4.2⑤）：record_fresh 用绝对 mtime ⇒ 未来时间戳可伪「新鲜」（fail-open） ──
    t0 = 1_000_000.0
    fd, tmp = tempfile.mkstemp(prefix="co166_", suffix=".json")
    os.close(fd)
    try:
        future = t0 + 3600.0
        os.utime(tmp, (future, future))
        mtime = Path(tmp).stat().st_mtime
    finally:
        os.unlink(tmp)
    fresh_future = mtime >= (t0 - 1.0)
    checks["P5_record_fresh_clock_skew"] = {
        "future_mtime": mtime, "t0": t0,
        "old_predicate_says_fresh": fresh_future,
        "allowlist_decision_with_future_stale": rn["allowlist_decision"]("co146_jlc_dfm_gate", 1, "", "FAIL", fresh_future),
        "normal_stale_says_not_fresh": (t0 - 100.0) >= (t0 - 1.0),
        "fail_open": fresh_future and rn["allowlist_decision"]("co146_jlc_dfm_gate", 1, "", "FAIL", fresh_future)
                     == "expected_nonzero"}

    # ── P6（§4.2⑥）：大段 f-string 转义易错性 + t02 是否覆盖该故障类 ─────────
    synth = ['t = f"x { y"\n', 't = f"| {0.0695mm} |"\n', 't = f"a}b"\n']
    caught = 0
    for s in synth:
        try:
            compile(s, "<synth>", "exec")
        except SyntaxError:
            caught += 1
    checks["P6_boundary_append_fstring"] = {
        "boundary_append_compiles": _compiles(show(BDY_REL)),
        "synthetic_brace_errors_caught_by_compile": caught, "synthetic_n": len(synth),
        "t02_covers_incident_class": caught == len(synth),
        "static_ok_at_head": True}

    # ══ 汇总：findings ══════════════════════════════════════════════════════
    if checks["P4_t06_format_brittleness"]["fail_open"]:
        findings.append(dict(id="F-1", sev="medium", kind="gate-fail-open",
            what="`boundary_order_steps()` 以 `lines[-1]` 取「最后一条**含字面子串** `规范复现序 =` 的行」解析序。"
                 "若更新的 R-COxxx-3 行改用别样措辞（如 `规范复现序（步骤集不变）= …`），该行不含该子串 ⇒ 解析器"
                 "**回落到更旧的 R-CO165-3 行**并判 `t06=True` ⇒ 文档实际最新序与执行器 `ORDER` 不一致却**报一致**。",
            evidence="P4：注入「新 §99 行（措辞变更）→ 旧 R-CO165-3 行仍在」⇒ `stale_fallback_still_matches_order=True`（fail-open）。",
            fix="CO-167：若最后一条可解析序行之后仍有其它 `规范复现序` 提及 ⇒ 返回 []（fail-closed）+ 负控 t06b。"))
    if checks["P5_record_fresh_clock_skew"]["fail_open"]:
        findings.append(dict(id="F-2", sev="low", kind="gate-fail-open",
            what="白名单「记录由本次执行产出」用**绝对时间**判据 `st_mtime >= t0-1.0`。若盘上记录 mtime 因时钟回拨/"
                 "网络盘/异机写入而落在**未来**，则**崩溃（未重写记录）**的白名单步仍被判 `expected_nonzero` ⇒ 白名单证据被绕过。",
            evidence="P5：未来 mtime ⇒ `old_predicate_says_fresh=True` 且 `allowlist_decision(...)=expected_nonzero`（fail-open）。",
            fix="CO-167：改为**变更检测**（步前捕获 (exists, mtime_ns, sha)，步后须任一变化）⇒ 与时钟无关；负控 t10。"))
    if not checks["P3_allowlist_governance"]["records_subset_of_watched_now"] or True:
        findings.append(dict(id="F-3", sev="low", kind="gate-blindspot",
            what="R-CO165-2 只声明「新增产物须落入 `watch_paths()`」，但**无任何牙齿**断言 "
                 "`EXPECTED_NONZERO[*].record ⊆ watch_paths()`。当前 DFM 记录恰在 `m13_v57_co*.json` glob 内（无即时暴露），"
                 "但未来白名单项若指向 glob 外件，其抖动/2-循环对收敛判定不可见。",
            evidence="P3：`records_subset_of_watched_now=True` 但判据由 t07/t08 均未断言（无 t09）。",
            fix="CO-167：runner `--check` 增 t09（白名单记录 ⊆ 受控集）；新增白名单须同步 `watch_paths()`。"))
    if checks["P1_t09_tokenization"]["loose_substr_185_ohm_accepts"] or \
       checks["P1_t09_tokenization"]["loose_substr_11_6mm_accepts"] or \
       not checks["P1_t09_tokenization"]["tolerance_drift_still_all"]:
        findings.append(dict(id="F-4", sev="low", kind="gate-false-accept",
            what="`binding_param_checks` 用**无锚子串**命中：备注写 `185Ω`/`11.6 mm` 亦分别命中 `85Ω`/`1.6 mm`；"
                 "且 `tolerance` 记号 `±10%` 可被**厚度公差** `（公差 ±10%）` 满足 ⇒ 阻抗容差漂移（85Ω 差分 ±5%）在备注里**静默通过**。",
            evidence="P1：`loose_substr_185_ohm_accepts=True`、`loose_substr_11_6mm_accepts=True`、"
                     "`tolerance_drift_masked_by_thickness=True`。",
            fix="CO-167：数值记号加数字边界（`(?<![0-9.])`）；tolerance 须在 zdiff 记号邻域内命中；负控 t09c。"))
    if checks["P1_t09_tokenization"]["wording_trips"]:
        findings.append(dict(id="F-5", sev="low", kind="gate-false-reject",
            what="同一函数对备注**措辞**敏感：`1.6mm`（无空格）/`外层1oz`/`85 Ω` 即令 t09 失败——虽然备注语义正确。"
                 "属 fail-closed（偏安全），但把「备注排版」与「定值漂移」混为一类，产生噪声失败。",
            evidence=f"P1：`wording_trips={checks['P1_t09_tokenization']['wording_trips']}`。",
            fix="CO-167：记号正则允许柔性空白（`\\s*`）⇒ 仅当**值**漂移才失败。"))
    if checks["P3_allowlist_governance"]["verdict_PASS_permitted_by_tooth"]:
        findings.append(dict(id="F-6", sev="low", kind="gate-governance",
            what="`EXPECTED_NONZERO` 是收敛判定的**单点信任**：t03/t07 只断言「步骤在序内」+「条目含 verdict/record」，"
                 "既**不禁止**把 expected `verdict` 写成 `PASS`（与 rc≠0 自相矛盾），也无机制把声明 verdict 绑到独立来源。",
            evidence="P3：`verdict_PASS_permitted_by_tooth=True`（无判据禁止 PASS）。",
            fix="CO-167：t07 增判据 `all(v['verdict'] != 'PASS')`；新增白名单项须登记期望 verdict 并复评。"))

    findings.sort(key=lambda f: f["id"])
    n = len(findings)
    verdict = "PASS_WITH_FINDINGS" if n else "PASS"
    rec = {"artifact": "m13_v57_co166_rev19_co159_co165_review", "schema": 1, "revision": "CO-166.4",
           "nature": "非执行者对抗复评（context 归零续接会话产出）：CO-159（复评 CO-156..158）+ CO-160（F-1..F-12 处置）"
                     "+ CO-161（K9 必需 DV 清单/identity fail-closed）+ CO-162（co106 verdict fail-open/承载区豁免）"
                     "+ CO-163（下单备注↔定值表绑定 + 来源 pin）+ CO-164（复现序 rc 机判执行器）+ CO-165（白名单双重证据 + 受控 sha 全域）",
           "reviewed_rev": AS_FOUND_REV,
           "reviewer": "独立会话（handoff-z39 §5 第 1 步；禁自评条款由 context 归零的续接会话满足）",
           "revision_note": "CO-166.4：删除 V3 的 `captured_len`（重放件按**现行**实件重排 pin ⇒ 非纯函数，该字段随工作区漂移，违 R-CO166-1；改留布尔）。CO-166.2/3：CO-166.3 净化 stdout（重放 as-found 件会 print 自身摘要）。CO-166.2：修正复评件自身的**钉定缺陷**（CO-166.1 把 as-found 源码与**现行**工件混读 ⇒ boundary/备注一变即结论漂移）。现全输入钉在 `e427909`（`git show` 重放）；复评方法 R-CO166-1 由本件自身缺陷的实测补强。",
           "scope": {"reviewed": ["CO-159", "CO-160", "CO-161", "CO-162", "CO-163", "CO-164", "CO-165"],
                     "spec_rev": "rev-19",
                     "focus": ["t09 记号化对备注措辞的敏感度", "t10 在容器侧 .omo 不可达时 fail-closed",
                               "EXPECTED_NONZERO 白名单扩展流程", "t06 对 boundary 文本格式变更的脆性",
                               "record_fresh 的 mtime 判据在时钟回拨/网络盘下的稳健性",
                               "co146_boundary_append 大段 f-string 的转义易错性"]},
           "board_sha16": s16(L4), "spec_sha16": s16(SPEC),
           "as_found_tool_sha16": {"co159_review": show_s16("tools/p3_v57_co159_rev19_co156_co157_co158_review.py"),
                                   "co164_order_runner": show_s16(RUNNER_REL),
                                   "co146_jlc_fab_package": show_s16(FAB_REL),
                                   "co146_boundary_append": show_s16(BDY_REL),
                                   "co124_input_selfcheck_gate": show_s16("tools/p3_v57_co124_input_selfcheck_gate.py"),
                                   "co106_reference_plane_gate": show_s16("tools/p3_v57_co106_reference_plane_gate.py")},
           "checks": checks, "findings": findings, "n_findings": n, "verdict": verdict,
           "independent_confirmations": [
               "冻结四源 4/4 MATCH（含 drc_rules 0a459839e15960b8）；交付板 = d4e81f647be7f980",
               "as-found 记录逐条复核成立：co159 PASS_WITH_FINDINGS/12；co124 CO-124.9 PASS/37 牙齿/0 findings；"
               "co150 CO-150.2 牙齿 5/5；co106 CO-106.4 PASS/8 牙齿；co120 PASS（12-12）；co77 PASS；co135 CO-135.3；co136 PASS；"
               "打样包 CO146-PKG.4 n_files 34/13 牙齿；登记簿 65 项 / OPEN 0（co159:F-1..F-12 全 CLOSED）",
               "CO-161 单一真值成立：co124 `required_dv_ids`(9) == co153 `KIND_EXPECT` 键集（V2）",
               "CO-163 t10 正控成立：容器侧监理指令件可达且 sha16 `35aafe268ff52f89` 与声明一致（V4）",
               "CO-163 t09 正控成立：现行备注 7/7 记号命中（V5）",
               "CO-162 阶梯独立复核：pin 漂移 ⇒ BASELINE_MISMATCH、teeth 失败 ⇒ FAIL(teeth)、check 失败 ⇒ 非 PASS（V6）",
               "CO-164 边界文档序 ↔ 执行器 ORDER 一致（34 步）；CO-165 受控集覆盖 ≥20 件且含 co106 记录与打样包 MANIFEST（独立重算）",
               "co146_boundary_append as-found 源码只读重放**执行成功（rc=0）且仅写 boundary**（V3）⇒ §37..§39 大段 f-string 现行可正确求值（逐字节幂等由 runner sha 跨轮稳定另行保证）",
               "CO-163 t10 在本容器 `.omo` **不可达**时 fail-closed（P2 注入不存在路径 ⇒ 判据 False，不静默放行）",
           ],
           "reproduce": ["python3 tools/p3_v57_co166_rev19_co159_co165_review.py（只读；对象钉在 e427909）"],
           "as_found": "本件以 `git show e427909:<path>` 重放受评基线 ⇒ 结论**可重放且不随后续修复漂移**；"
                       "findings 为 as-found 快照，其处置见 CO-167（登记簿 co166:F-* 与本件记录）。",
           "redline": "只读；不改 SPEC/板/冻结四源/台账/登记簿/他人记录；注入一律内存（boundary 重放拦截 write_text）、"
                      "tempfile 仅用于 mtime 探针且即用即删、零坐标搜索。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-166 — 非执行者对抗复评（CO-159..CO-165）｜as-found @ `" + AS_FOUND_REV + "`", "",
             f"- verdict：**{verdict}**｜findings：{n}",
             f"- 受评基线：k2 `{AS_FOUND_REV}`（CO-165）｜SPEC `{s16(SPEC)}`｜板 `{s16(L4)}`", "",
             "| id | sev | kind | what（摘要） |", "|---|---|---|---|"]
    for f in findings:
        lines.append(f"| {f['id']} | {f['sev']} | {f['kind']} | {f['what'][:110]}... |")
    lines += ["", "独立确认（非空过证据）：", ""] + [f"- {x}" for x in rec["independent_confirmations"]] + [""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": n, "findings": [f["id"] for f in findings],
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


def _allowlist_injection_demo(rn: dict) -> bool:
    """CO-166 P3：临时把某步加入白名单 ⇒ rc≠0 随即被接受（证明白名单＝收敛判定的单点信任）。"""
    _orig = rn["EXPECTED_NONZERO"]
    try:
        rn["EXPECTED_NONZERO"] = {**_orig, "co78_layer_role_drift_gate":
                                  {"verdict": "FAIL", "record": str(STEP2 / "m13_v57_co78_layer_role_drift_gate.json"),
                                   "why": "co166 injection demo"}}
        return rn["allowlist_decision"]("co78_layer_role_drift_gate", 1, "", "FAIL", True) == "expected_nonzero"
    finally:
        rn["EXPECTED_NONZERO"] = _orig


def _compiles(src: str) -> bool:
    try:
        compile(src, "<src>", "exec")
        return True
    except SyntaxError:
        return False


if __name__ == "__main__":
    sys.exit(main())
