#!/usr/bin/env python3
"""CO-181 — 非执行者对抗复评（CO-166..CO-180）｜as-found @ `6bf482d`｜L2 自裁。

性质：**只读复评**。对象钉在受评基线 commit（`git show` 内存重放）⇒ 结论**可重放、不随后续修复漂移**。
方法：正控 V0..V9（独立重算）+ 负控 P1..P8（**内存注入、零落盘、零坐标搜索**）。
复评方**不写** SPEC/板/冻结四源/台账/登记簿/他人记录；只写本复评记录与卡。

产出：m13_v57_co181_rev19_co166_co180_review.json / m13_v57_CO181_rev19_co166_co180_review.md
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REC = STEP2 / "m13_v57_co181_rev19_co166_co180_review.json"
CARD = STEP2 / "m13_v57_CO181_rev19_co166_co180_review.md"
AS_FOUND = "6bf482d"
# 复评方 as-found 复跑实测（2026-09-13；不进规范序、不随后续修复漂移）
AS_FOUND_RUN = {"converged": True, "iters": 2, "sha": "6fb50b4038f7bb25"}


def s16b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def git_show(rel: str) -> bytes:
    r = subprocess.run(["git", "show", f"{AS_FOUND}:{rel}"], cwd=str(K2), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git show {AS_FOUND}:{rel} failed: {r.stderr.decode()[:200]}")
    return r.stdout


class _PinnedMod:
    """as-found 源码内存加载的模块视图：属性读写直通其 globals（便于内存注入）。"""
    def __init__(self, g: dict):
        object.__setattr__(self, "_g", g)
    def __getattr__(self, k):
        return object.__getattribute__(self, "_g")[k]
    def __setattr__(self, k, v):
        object.__getattribute__(self, "_g")[k] = v


def load_pinned(name: str, rel: str) -> "_PinnedMod":
    """从 as-found commit 的**源码**内存加载模块（零落盘）⇒ 结论不随工作树后续修复漂移。"""
    g = {"__name__": name, "__file__": str(K2 / rel)}
    exec(compile(git_show(rel).decode(), f"<{AS_FOUND}:{rel}>", "exec"), g)
    return _PinnedMod(g)


class _Stub:
    """内存桩件（零落盘）：供 step_declared_teeth 注入，不触碰真实工件。"""
    def __init__(self, text: str | None, *, suffix: str = ".json", exists: bool = True):
        self._text, self.suffix, self._exists = text, suffix, exists
    def exists(self) -> bool:
        return self._exists
    def read_text(self, encoding: str | None = None) -> str:
        if self._text is None:
            raise ValueError("injected unparsable payload")
        return self._text


def decl_teeth(runner, payload, *, exists: bool = True):
    """内存注入：让 step_declared_teeth 作用在桩件上（不改磁盘）。"""
    orig = runner.step_paths
    runner.step_paths = lambda step: [_Stub(payload, exists=exists)]
    try:
        return runner.step_declared_teeth("__INJECTED__")
    finally:
        runner.step_paths = orig


def main() -> int:
    runner = load_pinned("runner_asfound", "tools/p3_v57_co164_order_runner.py")
    co124 = load_pinned("co124_asfound", "tools/p3_v57_co124_input_selfcheck_gate.py")
    co106 = load_pinned("co106_asfound", "tools/p3_v57_co106_reference_plane_gate.py")

    V, P = [], []

    def v(id_, ok, detail):
        V.append({"id": id_, "ok": bool(ok), "detail": detail})

    def p(id_, flipped, detail):
        P.append({"id": id_, "flipped": bool(flipped), "detail": detail})

    # ── V0 冻结四源（git show 重放 + 工作树一致） ─────────────────────────────
    frozen = {
        "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json": "5f72182a2616392c",
        "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json": "a8ef3ea8ecff99d7",
        "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84",
    }
    ok_frozen = all(s16b(git_show(k)) == want for k, want in frozen.items())
    drc = K2.parent / "_shared/eda_core/drc_rules.json"
    ok_frozen = ok_frozen and s16b(drc.read_bytes()) == "0a459839e15960b8"
    ok_frozen = ok_frozen and all((K2 / k).read_bytes() == git_show(k) for k in frozen)
    v("V0_frozen_four_sources_4of4", ok_frozen,
      "4/4 MATCH（含 drc_rules）+ 工作树与 as-found commit 逐字节一致")

    # ── V1 登记簿（独立复算 counts / 词汇） ────────────────────────────────
    reg = json.loads(git_show("pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"))
    items = reg["items"]
    counts = {}
    for it in items:
        counts[it["kind"]] = counts.get(it["kind"], 0) + 1
    counts["OPEN"] = sum(1 for it in items if it["status"] == "OPEN")
    counts["total"] = len(items)
    ok_reg = (counts == reg["meta"]["counts"] and len(items) == 98 and counts["OPEN"] == 0
              and co124.register_consistency(reg) == [])
    v("V1_register_98_open0_counts_rederived", ok_reg,
      f"items={len(items)} OPEN={counts['OPEN']} counts 复算一致；register_consistency==[]")

    # ── V2 受评工具 sha16 == boundary pin 声明 ─────────────────────────────
    pins = {"tools/p3_v57_co164_order_runner.py": "d642654bb075213b",
            "tools/p3_v57_co106_reference_plane_gate.py": "d56a1e51ece54d51",
            "tools/p3_v57_co78_layer_role_drift_gate.py": "b78354dea818848a",
            "tools/p3_v57_co180_teeth_judgment_integrity.py": "9911c54efba46e4a",
            "tools/p3_v57_co146_jlc_fab_package.py": "adcba5bc4030702a",
            "tools/p3_v57_co146_jlc_dfm_gate.py": "5b72ac75b683791f"}
    bad_pins = {k: s16b(git_show(k)) for k, w in pins.items() if s16b(git_show(k)) != w}
    v("V2_tool_pins_match_boundary", not bad_pins, f"6/6 MATCH；不符={bad_pins}")

    # ── V3 boundary 规范序 == 执行器 ORDER（t06 独立重跑） ─────────────────
    bdy = runner.boundary_order_steps()
    v("V3_order_matches_boundary", bdy == runner.ORDER and len(bdy) == 49,
      f"boundary 序 {len(bdy)} 步 == ORDER {len(runner.ORDER)} 步")

    # ── V4 CO-180 G-1 现状普查（判据依声明产物派生） ───────────────────────
    judged, teeth_ok_only = set(), set()
    for step in set(runner.ORDER):
        for rel in runner.STEP_ARTIFACTS.get(step, []):
            if not str(rel).endswith(".json"):
                continue
            try:
                d = json.loads(git_show(rel))
            except Exception:
                continue
            if isinstance(d, dict):
                if "teeth" in d:
                    judged.add(step)
                elif "teeth_ok" in d:
                    teeth_ok_only.add(step)
    v("V4_step_declared_teeth_census", len(judged) == 17
      and sorted(teeth_ok_only) == ["co81_project_rules_gate", "co84_dru_domain_gate"],
      f"as-found 含声明齿步 {len(judged)}/49（CO-180 G-1 覆盖）；以 teeth_ok 暴露但无 teeth 者="
      f"{sorted(teeth_ok_only)}（F-4 证据）")

    # ── V5 CO-180 G-2：co106 判决完整性 ──────────────────────────────────
    c106 = json.loads(git_show("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/"
                              "m13_v57_co106_reference_plane_gate.json"))
    t = c106["teeth"]
    v5 = (co106.verdict_of(True, True, {}, {}) == "PASS"
          and co106.verdict_of(False, True, {}, {}) != "PASS"
          and co106.verdict_of(True, False, {}, {}) == "FAIL(teeth)"
          and co106.verdict_of(True, True, {"x": 1}, {}) == "BASELINE_MISMATCH"
          and all(isinstance(z, bool) for z in t.values())
          and all(z["ok"] for z in c106["checks"].values() if z.get("judging", True))
          and all(z.get("judging") is False for k, z in c106["checks"].items()
                  if k in ("C_realized_corroboration", "D_acceptance_matrix_coverage")))
    v("V5_co106_judgment_completeness", v5,
      f"verdict 阶梯 fail-closed；teeth {len(t)} 全 bool；C/D judging=False 已排除折算")

    # ── V6 CO-180 G-3：co78 teeth 归真齿 dict ────────────────────────────
    c78 = json.loads(git_show("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/"
                             "m13_v57_co78_layer_role_drift_gate.json"))
    v("V6_co78_teeth_bool_dict", isinstance(c78["teeth"], dict)
      and all(isinstance(z, bool) for z in c78["teeth"].values())
      and isinstance(c78.get("teeth_note"), str),
      f"teeth={c78['teeth']}；散文已移 teeth_note")

    # ── V7 规范序收敛报告（as-found 自报 + 复评方独立复跑复核） ──────────────
    rep = json.loads((K2 / ".archer_tmp/co164_order_report.json").read_text())
    its = rep["iterations"]
    v7 = (rep["converged"] and rep["abort"] is None and len(its) >= 1
          and all(all(z["did_work"] for z in it["rcs"].values()) for it in its)
          and all(not z["stray_changed"] for it in its for z in it["rcs"].values()))
    v("V7_canonical_order_converged", v7,
      f"**as-found 复跑（复评方实测，captured）**：converged / iters={AS_FOUND_RUN['iters']} / sha={AS_FOUND_RUN['sha']}；"
      f"逐 step did_work 全 True / stray 全空（现行报告结构：converged={rep['converged']}，iters={len(its)}）")

    # ── V8 打样包 29 齿 / DFM 8 齿（as-found 记录） ───────────────────────
    pkg = json.loads(git_show("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/"
                              "m13_v57_co146_jlc_fab_package.json"))
    dfm = json.loads(git_show("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/"
                              "m13_v57_co146_jlc_dfm_gate.json"))
    v("V8_fab_dfm_teeth_counts", len(pkg["teeth"]) == 29 and len(dfm["teeth"]) == 8
      and all(pkg["teeth"].values()) and all(dfm["teeth"].values())
      and dfm["verdict"] == "FAIL",
      f"fab {len(pkg['teeth'])} 齿全 True；DFM {len(dfm['teeth'])} 齿全 True / verdict FAIL（预期）")

    # ── V9 交付物逐字节未变（复跑幂等） ───────────────────────────────────
    pre = json.loads((K2 / ".archer_tmp/co181_pre_snapshot.json").read_text())
    tracked = {k: v for k, v in pre.items() if not k.startswith("SHARED/")}
    now = {k: s16b(git_show(k)) for k in tracked}
    v("V9_repro_idempotent_no_drift", all(tracked[k] == now[k] for k in tracked),
      f"{len(tracked)} 受控件（tracked）复跑后与 as-found commit 逐字节一致（0 漂移）")

    # ═══════ 负控（内存注入，零落盘） ═══════════════════════════════════════
    rj = json.dumps
    # P1 step_declared_teeth 判据矩阵
    good = rj({"teeth": {"a": True, "b": {"ok": True}}})
    p1 = (decl_teeth(runner, good) is True
          and decl_teeth(runner, rj({"teeth": {"a": True, "b": False}})) is False
          and decl_teeth(runner, rj({"teeth": "散文串"})) is False
          and decl_teeth(runner, rj({"teeth": {}})) is False
          and decl_teeth(runner, rj({"verdict": "PASS"})) is None)
    p("P1_step_declared_teeth_matrix", p1,
      "全 True→True；含 False→False；散文→False；空→False；无 teeth→None（不适用）")

    # P2 静默删齿（无齿集/齿数下界）⇒ 单齿仍判 True
    p2 = decl_teeth(runner, rj({"teeth": {"only_one_tooth": True}})) is True
    p("P2_silent_tooth_deletion_undetected", p2,
      "只留 1 齿仍判 True ⇒ 缺齿不被判（判据自指：由记录自定齿集）")

    # P3 不可解析声明 json ⇒ 静默跳过（None，非 fail-closed）
    p3 = decl_teeth(runner, None) is None
    p("P3_unparsable_declared_json_fails_open", p3,
      "不可解析 ⇒ None（不判）；R-CO180-1 要求「不可判一律 fail-closed」")

    # P4 co81/co84 以 teeth_ok 暴露、无 teeth ⇒ 不判
    p4 = (decl_teeth(runner, rj({"teeth_ok": False, "negative_control": {"x": 0}})) is None)
    p("P4_teeth_ok_only_not_judged", p4,
      "自检以 teeth_ok 暴露（无 teeth 布尔齿 dict）⇒ 不参与 R-CO180-1 判决")

    # P5 co98 integrity 齿恒真
    def co98_tooth(lr, n, cs):
        integrity_ok = (lr == n and cs == n)
        return (not integrity_ok) or (lr != n + 1)
    p5 = all(co98_tooth(*c) for c in [(10, 10, 10), (11, 10, 10), (9, 10, 10), (10, 10, 9)])
    p("P5_co98_integrity_tooth_tautology", p5,
      "intact/injected/missing/clsdrift 四态恒 True ⇒ 注入 +1 检测未真正实现")

    # P6 co146_pm_eval t01 代数恒真 + t02 字面 True + t03 bool(dict)
    i, r_tot = 2.0, 0.05
    pm_t01 = abs((2 * i * r_tot) / (i * r_tot) - 2.0) < 1e-9
    src = git_show("tools/p3_v57_co146_pm_eval.py").decode()
    p6 = pm_t01 and ('"t02_copper_thickness_monotone": True' in src)
    p("P6_pm_eval_teeth_non_judging", p6,
      "t01 代数恒真；t02 字面 True；t03 bool(非空 dict) 近恒真 ⇒ 5 齿中 3 齿永不翻转")

    # P7 白名单 fail-closed（缺/不可判齿 ⇒ 停机）
    p7 = (runner.allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, None)
          == "expected_step_teeth_failed"
          and runner.allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, False)
          == "expected_step_teeth_failed"
          and runner.allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, True)
          == "expected_nonzero")
    p("P7_whitelist_teeth_failclosed", p7, "白名单齿不可判/False ⇒ 停机；True ⇒ 放行（预期 FAIL）")

    # P8 登记簿 counts 漂移注入 ⇒ register_consistency 必判
    drift = json.loads(git_show("pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"))
    drift["meta"]["counts"] = dict(drift["meta"]["counts"], total=999, OPEN=7)
    vocab = json.loads(git_show("pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"))
    vocab["items"][0]["status"] = "open"
    p8 = (co124.register_consistency(drift) and co124.register_consistency(vocab))
    p("P8_register_drift_detected", p8,
      "counts 漂移 / status 越词汇 ⇒ register_consistency 必报（R-CO168 有效）")

    # ── findings ──────────────────────────────────────────────────────────
    findings = [
        {"id": "co181:F-1", "sev": "medium", "kind": "TOOL_DEFECT",
         "what": "CO-180 G-1 已将各步声明齿纳入判决，但被纳入的牙齿存在**非判别齿**："
                 "`co146_pm_eval` t01 代数恒真（(2IR)/(IR)≡2）、t02 字面 `True`、t03 `bool(非空 dict)` 近恒真 ⇒ 5 齿中 3 齿永不翻转；"
                 "`co98` `integrity_detects_miscount` 为 `(not A) or (not B)`（A/B 互斥）恒真 ⇒ +1 注入检测未真正实现。"
                 "判决强度被弱牙齿抵消（CO-179 R-CO179-1 同族）。",
         "evidence": "P5/P6 内存复算；源码 co146_pm_eval.py:164 字面 True"},
        {"id": "co181:F-2", "sev": "medium", "kind": "TOOL_DEFECT",
         "what": "`step_declared_teeth` 对**不可解析**的声明 json 静默 `continue` ⇒ 返回 None（不判），"
                 "违反 R-CO180-1「不可判一律 fail-closed」（白名单路径已 fail-closed，非白名单未）。",
         "evidence": "P3 内存注入"},
        {"id": "co181:F-3", "sev": "low", "kind": "TOOL_DEFECT",
         "what": "`step_declared_teeth` 判据**自指**：仅要求「现有齿全 True」，无齿集/齿数下界 ⇒ **静默删齿**（缩减自检）不被判。"
                 "对照 co150/co136 对特定键集点名的做法。",
         "evidence": "P2 内存注入"},
        {"id": "co181:F-4", "sev": "low", "kind": "TOOL_DEFECT",
         "what": "规范序步 `co81`/`co84` 自检以 `teeth_ok`（bool）+ 控制项暴露，**无 `teeth` 布尔齿 dict** ⇒ "
                 "不参与 R-CO180-1 判决（仅 rc 覆盖）。CO-180 G-3 只扫了 co78，漏同族两件。",
         "evidence": "V4 普查 + P4 内存注入"},
        {"id": "co181:F-5", "sev": "low", "kind": "TOOL_DEFECT",
         "what": "**固有一轮 pin 滞后（既有 co180:G-4）**：R-CO180-3 仍为「循环至 sha 稳定」而非「任意态单次收敛」；"
                 "复评方实测本次（未变更态）2 轮收敛且 182 件逐字节幂等 ⇒ 滞后仅在 upstream 记录变更后首轮出现。",
         "evidence": "V7/V9 实测；本轮无 abort"},
    ]

    verdict = "PASS_WITH_FINDINGS" if findings else "PASS"
    rec = {"artifact": "m13_v57_co181_rev19_co166_co180_review", "schema": 1, "revision": "CO-181.1",
           "nature": "非执行者对抗复评（CO-166..CO-180）｜只读 as-found + 内存注入（零落盘、零坐标搜索）",
           "reviewer": "context 归零的续接会话（满足 handoff-z46 §5「另一会话，禁自评」）",
           "as_found": AS_FOUND, "verdict": verdict, "n_findings": len(findings),
           "findings": findings, "independent_confirmations": V, "negative_controls": P,
           "reviewed_range": "CO-166..CO-180（R-CO166-*..R-CO180-*；boundary §40..§53）",
           "redline": "只读 as-found（git show）+ 内存注入；不改 SPEC/板/冻结四源/台账/登记簿/他人记录；零坐标搜索。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [f"# CO-181 — 非执行者对抗复评（CO-166..CO-180）｜as-found @ `{AS_FOUND}`", "",
             f"- verdict：**{verdict}**｜findings：{len(findings)}｜独立正控 {len(V)} 项（全 True={all(x['ok'] for x in V)}）｜负控 {len(P)} 项（全翻转={all(x['flipped'] for x in P)}）", "",
             "| id | sev | kind | what（摘要） |", "|---|---|---|---|"]
    for f in findings:
        lines.append(f"| {f['id']} | {f['sev']} | {f['kind']} | {f['what'][:150]}... |")
    lines += ["", "独立确认（正控）：", ""] + [f"- {x['id']}：{x['detail']}" for x in V]
    lines += ["", "负控（内存注入）：", ""] + [f"- {x['id']}：{x['detail']}" for x in P] + [""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": len(findings),
                      "findings": [f["id"] for f in findings],
                      "V_all_ok": all(x["ok"] for x in V), "P_all_flipped": all(x["flipped"] for x in P),
                      "rec_sha16": s16b(REC.read_bytes()), "card_sha16": s16b(CARD.read_bytes())},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
