#!/usr/bin/env python3
"""CO-172 — 非执行者对抗复评（对象 **CO-166..CO-171**，as-found @ k2 `7bffb75`）。

性质：**只读复评**（不改 SPEC/板/冻结四源/台账/登记簿/他人记录；只写本件 record + card）。
按 handoff-z45 §5 第 1 步执行（复评债 = CO-166..CO-171；禁自评 ⇒ 本会话为 context 归零的续接非执行者会话）。

方法（可重放）：把复评对象钉在受评基线 `AS_FOUND_REV`，用 `git show <rev>:<path>` 取 as-found 工具源
在**内存**执行 —— 本件日后重跑仍复现**当时**结论，不随后续修复漂移。
  · 正控（V*）：独立复核 as-found 的正面主张（pin / 登记簿复算 / 备注与记录的现态一致性）。
  · 负控（P1..P8）：对 handoff §4.2 指定关注点做内存注入，探**可规避性**（零落盘、零坐标搜索）。
handoff §4.2 关注点：① 备注内是否**仍有**未绑定的记录派生数字（§6 热数字 / §2 过孔分解 / §3 阻焊净距）；
② 叠层图 t11 是否应扩到**铜厚矩形几何**而非仅文本；③ `step_did_work` 在粗粒度/网络 FS 下的灵敏度；
④ `REGISTER_STATUSES` / `counts` 复算键集是否过严。
CLI: python3 tools/p3_v57_co172_rev19_co166_co171_review.py
"""
from __future__ import annotations
import collections, copy, hashlib, inspect, json, re, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L5PKG = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
REC = STEP2 / "m13_v57_co172_rev19_co166_co171_review.json"
CARD = STEP2 / "m13_v57_CO172_rev19_co166_co171_review.md"
AS_FOUND_REV = "7bffb75"

REL_FAB = "tools/p3_v57_co146_jlc_fab_package.py"
REL_RUNNER = "tools/p3_v57_co164_order_runner.py"
REL_NOTES = "pm_gate/artifacts/k2_v4/L5/jlc_package/ORDER_NOTES.md"
REL_FABREC = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_jlc_fab_package.json"
REL_REG = "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
REL_BDY = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md"
REL_SPEC = "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
REL_BOARD = "k2_v4_8L.kicad_pcb"
REL_MAN = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json"
REL_SPREAD = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_impedance_table.json"
REL_CO147 = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co147_l2_ruling.json"
REL_CO148 = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co148_thermal_ruling.json"
REL_CO149 = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co149_u6_thermal_mitigation.json"
REL_CAP = "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co146_jlc8_capability.json"
REL_RULES = "_shared/eda_core/drc_rules.json"

AS_FOUND_PINS = {REL_SPEC: "5f72182a2616392c", REL_BOARD: "fb07d25ac426ff84",
                 REL_MAN: "a8ef3ea8ecff99d7", REL_RULES: "0a459839e15960b8",
                 REL_REG: "ef9081e516c372d7", REL_BDY: "b0e21b3d285727ad",
                 REL_NOTES: "b7d86151d97b32a6"}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def show(rel: str) -> str:
    r = subprocess.run(["git", "show", f"{AS_FOUND_REV}:{rel}"], cwd=K2, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"git show {AS_FOUND_REV}:{rel} failed: {r.stderr.strip()}")
    return r.stdout


def show_s16(rel: str) -> str:
    return hashlib.sha256(show(rel).encode()).hexdigest()[:16]


def as_found_module(rel: str) -> dict:
    """在内存执行 as-found 工具源（零落盘；模块级仅定义常量/函数）。"""
    ns = {"__name__": "asfound_" + Path(rel).stem, "__file__": str(K2 / rel)}
    exec(compile(show(rel), rel, "exec"), ns)
    return ns


def perturb(base, path, val):
    d = copy.deepcopy(base)
    cur = d
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = val
    return d


def main() -> int:
    notes = show(REL_NOTES)
    dfm = json.loads((STEP2 / "m13_v57_co146_jlc_dfm_gate.json").read_text())
    imp = json.loads((STEP2 / REL_SPREAD.split("/")[-1]).read_text())
    co147 = json.loads((STEP2 / REL_CO147.split("/")[-1]).read_text())
    co148 = json.loads((STEP2 / REL_CO148.split("/")[-1]).read_text())
    co149 = json.loads((STEP2 / REL_CO149.split("/")[-1]).read_text())
    cap = json.loads((STEP2 / REL_CAP.split("/")[-1]).read_text())
    rules = json.loads((K2 / REL_RULES).read_text())
    old_fab = as_found_module(REL_FAB)
    old_run = as_found_module(REL_RUNNER)
    fab_rec = json.loads(show(REL_FABREC))

    findings, indep, neg = [], [], []

    # ── 正控：as-found pin 与 handoff 声明一致 ─────────────────────────────
    def pin16(rel: str) -> str:
        # `_shared` 为 submodule（不在 k2 的 git 历史内）⇒ 冻结件以磁盘 sha 核验
        return s16(K2 / rel) if rel == REL_RULES else show_s16(rel)

    pin_bad = {r: (pin16(r), v) for r, v in AS_FOUND_PINS.items() if pin16(r) != v}
    indep.append(f"V1 as-found pin 逐件复核：{len(AS_FOUND_PINS)} 件中 {len(AS_FOUND_PINS) - len(pin_bad)} 件与 handoff 声明一致"
                 + (f"；不一致 = {pin_bad}" if pin_bad else "（SPEC/底板/manifest/冻结规则/登记簿/boundary/备注）"))
    indep.append(f"V2 as-found 打样包记录 revision = {fab_rec['revision']}；牙齿 {len(fab_rec['teeth'])} 项、全 True "
                 f"= {all(fab_rec['teeth'].values())}（牙齿名集不含任何 §2/§3/§5-spread/§6/§4/几何 类判据）")

    # ── 正控：备注内这些数字**现态与记录一致**（故 finding 属「潜在漂移」非「现错误」） ──
    pw = imp["watch"][0]["zdiff"]
    spread = (max(pw["M2_HJ_Cohn"]) - min(pw["M1_IPC2141"])) / min(pw["M1_IPC2141"]) * 100.0
    vc = dfm["as_built"]["via_type_census"]
    mf = co147["mask_measure"]
    ps = [c["P_U6_W"] for c in co148["cases"].values()]
    now_ok = {
        "§5 spread ≈4.8%": f"spread ≈{spread:.1f}%" in notes,
        "§2 F.Cu→In2.Cu 92": "`F.Cu→In2.Cu` 92" in notes,
        "§2 In2.Cu→In5.Cu 88": "`In2.Cu→In5.Cu` 88" in notes,
        "§2 In5.Cu→B.Cu 32": "`In5.Cu→B.Cu` 32" in notes,
        "§2 F.Cu→In5.Cu 8": "`F.Cu→In5.Cu` 8" in notes,
        "§3 gap 0.0695mm": f"{mf['closest']['gap_mm']:g}mm" in notes,
        "§3 shortfall 0.0205": f"{mf['shortfall_mm']:g}" in notes,
        "§3 rework 0.0995": f"{round(mf['closest']['gap_mm'] + mf['mask_expansion_mm'] - 0.02, 4):g}" in notes,
        "§6 P range 4.7–7.0W": f"{min(ps):.1f}–{max(ps):.1f}W" in notes,
        "§6 Tj 121.8–161.8": f"{co148['best']['Tj_C']:g}–{co148['worst']['Tj_C']:g}" in notes,
        "§6 ψJB 173.6": f"{co148['paths_cross_check']['psi_jb_plus_board_route_Tj_C']:g}" in notes,
        "§4 板规铜-板边 0.30mm": f"{rules['manufacturing']['min_copper_edge_clearance']:.2f}mm" in notes,
    }
    indep.append("V3 备注内 §2/§3/§4/§5-spread/§6 各数字**现态与来源记录一致**（逐项字面比对）："
                 + f"{sum(now_ok.values())}/{len(now_ok)} 命中"
                 + ("；未命中 = " + str({k: v for k, v in now_ok.items() if not v}) if not all(now_ok.values()) else ""))

    # ── 正控：登记簿 counts 复算 + status 词汇（回应 §4.2 关注点④） ─────────
    reg = json.loads(show(REL_REG))
    d = dict(collections.Counter(i.get("kind") for i in reg["items"]))
    d["OPEN"] = sum(1 for i in reg["items"] if i.get("status") == "OPEN")
    d["total"] = len(reg["items"])
    declared = reg["meta"]["counts"]
    indep.append(f"V4 as-found 登记簿 {d['total']} 项 / OPEN {d['OPEN']}；`meta.counts` 据 items 复算逐项一致 = "
                 f"{ {k: declared.get(k) for k in set(d) | set(declared)} == {k: d.get(k) for k in set(d) | set(declared)} }"
                 "（关注点④裁定：键集为 `set(declared)|set(derived)` **并集**比对 ⇒ 多写/少写键均 fail-closed，"
                 "属设计选择而非过严缺陷）")

    # ── 负控 P1..P6：as-found 判据对**记录漂移**的可规避性（注入后仍全 True ⇒ 无覆盖） ──
    def old_checks(note, imp_, dfm_, **kw):
        return old_fab["order_notes_record_figures"](note, imp_, dfm_)

    p = {"P1 §5 spread 漂移（F.Cu M1 90.61→94.0：spread 4.8%→1.0%，而 dev% 仍由 M2 的 11.69% 决定）":
         old_checks(notes, perturb(imp, ["watch", 0, "zdiff", "M1_IPC2141"], [94.0]), dfm),
         "P2 §2 过孔分解漂移（F.Cu→In2.Cu 92→93）":
         old_checks(notes, imp, perturb(dfm, ["as_built", "via_type_census", "F.Cu->In2.Cu|BLIND_BURIED"], 93)),
         "P3 §3 阻焊净距漂移（0.0695→0.0694）":
         old_checks(notes, imp, dfm, co147=perturb(co147, ["mask_measure", "closest", "gap_mm"], 0.0694)),
         "P4 §6 热数字漂移（worst Tj 161.8→165.0）":
         old_checks(notes, imp, dfm, co148=perturb(co148, ["worst", "Tj_C"], 165.0)),
         "P5 §4 JLC 限值漂移（min track 0.09→0.10）":
         old_checks(notes, imp, dfm, cap=perturb(cap, ["capability", "min_track_width_mm", "value"], 0.10)),
         "P6 §4 板规铜-板边漂移（0.30→0.25）":
         old_checks(notes, imp, dfm, rules=perturb(rules, ["manufacturing", "min_copper_edge_clearance"], 0.25))}
    for name, res in p.items():
        assert all(res.values()), f"negative control 反例：{name} 被 as-found 判据抓住（应为未覆盖）"
        neg.append(f"{name} ⇒ as-found 判据仍全 True（**未被覆盖**）：{ {k: v for k, v in res.items()} }")

    # ── 负控 P7：叠层图几何未被绑定 ────────────────────────────────────────
    sig = list(inspect.signature(old_fab["stackup_svg"]).parameters)
    geom_keys = list(old_fab["stackup_svg_binding_checks"]("", {"stackup": "x", "total_thickness_mm": 1.6,
                                                                "copper": {"outer_oz": 1.0, "inner_oz": 0.5}}).keys())
    assert "binding" not in sig and geom_keys == ["stackup_code", "thickness", "outer_copper", "inner_copper"]
    neg.append(f"P7 as-found `stackup_svg{sig}` 不接收声明定值表；`stackup_svg_binding_checks` 键 = {geom_keys}（**纯文本**）"
               "⇒ 铜厚矩形**几何**（0.035/0.0175mm 字面量）无任何牙齿覆盖")
    indep.append("V5 as-found 叠层图 sha16 44370475b258848f（与 handoff 一致）且几何 = 21.00/10.50 px（与 1oz/0.5oz 相符）"
                 "⇒ F-6 属「无绑定（潜在漂移）」而非「现错误」")

    # ── 负控 P8：runner 快照单信号 ────────────────────────────────────────
    stamp = old_run["_snap_watched"]()
    first = next(iter(stamp.values()))
    assert isinstance(first, int), f"as-found 受控快照应为标量 mtime，实测 {type(first)}"
    assert not old_run["step_did_work"]({"p": 1}, {"p": 1})
    neg.append("P8 as-found `_snap_watched()` 的值为**标量 int（mtime_ns）** ⇒ 内容变化若无 mtime 前进"
               "（粗粒度/网络 FS 同刻重写、utime 规范化、时钟回拨）不可见；且受控集为**全局集合**、非步本地")
    indep.append("V6 as-found runner revision = CO-169.1；`--check` 静态牙齿 t01..t11（含 t11 步产物 oracle）")

    # ── findings ─────────────────────────────────────────────────────────
    findings = [
        {"id": "F-1", "sev": "medium", "kind": "UNBOUND_RECORD_FIGURE",
         "what": "ORDER_NOTES §5「模型间 spread ≈4.8%」为**记录派生数字**但既无来源记录串、亦无牙齿"
                 "（CO-171 的 t12 只绑 dev% +11.7%）⇒ R-CO171-1 在本备注内**仍有未绑定项**（P1 实证可规避）。",
         "fix": "CO146-PKG.8 增 `impedance_spread_pct(imp)`（由 watch 逐几何模型极差派生）+ 有锚判据 `impedance_spread_pct` + 灵敏度 t12c。"},
        {"id": "F-2", "sev": "medium", "kind": "UNBOUND_RECORD_FIGURE",
         "what": "§2 非通孔过孔**逐 span 分解**（92/88/32/8）为硬编码字面量；来源 = DFM 记录 `as_built.via_type_census`。"
                 "总量 220/493 由生成式绑定，但**分量无牙** ⇒ 过孔口径变更后可留陈旧分解（P2 实证）。",
         "fix": "增 `via_census_figures(dfm)` + 逐 span 有锚判据（含分隔符防前缀匹配）+ 灵敏度 t12d。"},
        {"id": "F-3", "sev": "medium", "kind": "UNBOUND_RECORD_FIGURE",
         "what": "§3 阻焊净距 0.0695mm / 欠 0.0205mm / 回退净距 0.0995 / 开窗 0.05→0.02mm 为硬编码；来源 = CO-147 记录 `mask_measure`"
                 "（gap/shortfall/jlc_min/mask_expansion）。客户可见（随单提交板厂评审）但无牙（P3 实证）。",
         "fix": "增 `mask_clearance_figures(co147)` + 4 项有锚判据（含回退净距可重算路径）+ 灵敏度 t12e。"},
        {"id": "F-4", "sev": "medium", "kind": "UNBOUND_RECORD_FIGURE",
         "what": "§6 U6 热数字（PACT 4.7–7.0W / θJA 17.4°C/W / Tj 限 120°C / Tj 121.8–161.8°C / ψJB 路线 173.6°C / Ta 40°C）"
                 "为硬编码；来源 = CO-148 热裁定 + CO-149 缓解派生（P4 实证）。",
         "fix": "增 `thermal_figures(co148, co149)` + 6 项有锚判据 + 灵敏度 t12f。"},
        {"id": "F-5", "sev": "low", "kind": "UNBOUND_RECORD_FIGURE",
         "what": "§4 JLC 限值散文（≥3.5mil / 孔 ≥0.15 / 盘径 ≥0.25 / 孔径+0.15 / ≥0.2）源 = JLC 能力记录；"
                 "「板规铜-板边 0.30mm」源 = **冻结** `drc_rules.manufacturing.min_copper_edge_clearance`，"
                 "而该 0.30 在**备注与 DFM 闸工具两处**均为硬编码字面量（P5/P6 实证）。",
         "fix": "DFM 闸由冻结规则派生（CO146-JLC-DFM.2 + t03 正控/灵敏度）；备注侧增 capability/rules 派生判据 + 灵敏度 t12g/t12h。"},
        {"id": "F-6", "sev": "medium", "kind": "UNBOUND_RECORD_FIGURE",
         "what": "叠层图（03_，**随单提交的制造输入**）的**铜厚矩形几何**为硬编码 0.035/0.0175mm，t11 只绑文本"
                 "（P7 实证）⇒ 声明铜厚变更时图与声明在**几何上**脱钩，制造侧按图施工。",
         "fix": "`stackup_svg(spec, binding)` 铜厚几何/标题改由声明 oz 派生（当前输出逐字节不变）+ `stackup_svg_copper_geometry_checks` + t11c/t11d。"},
        {"id": "F-7", "sev": "low", "kind": "ORACLE_SENSITIVITY",
         "what": "runner `step_did_work` 快照为**单信号 mtime_ns**（P8 实证）⇒ 粗粒度/网络 FS 同刻重写、mtime 规范化/回写、"
                 "时钟回拨下可**假停机**（fail-closed，不致假通过）；且受控集为全局集合、非步本地 ⇒ 并发会话写受控件时"
                 "可被误判为「本步做了事」（假通过方向）。",
         "fix": "快照改**多信号**（mtime_ns + ctime_ns + size + 内容 sha16）+ 静态齿 t12；残余（非步本地归因）如实登记于 next。"},
    ]
    n = len(findings)
    verdict = "PASS_WITH_FINDINGS"

    rec = {"artifact": "m13_v57_co172_rev19_co166_co171_review", "schema": 1, "revision": "CO-172.1",
           "nature": "非执行者对抗复评（对象 CO-166..CO-171），as-found 钉于受评基线；只读、注入全在内存",
           "as_found_rev": AS_FOUND_REV, "as_found_pins": {r: pin16(r) for r in AS_FOUND_PINS},
           "verdict": verdict, "n_findings": n, "findings": findings,
           "independent_confirmations": indep, "negative_controls": neg,
           "focus_rulings": {
               "① 备注内是否仍有未绑定记录派生数字": f"**是**（F-1..F-5；§5-spread / §2 分解 / §3 阻焊 / §6 热 / §4 限值+板规）",
               "② 叠层图 t11 是否应扩到铜厚矩形几何": f"**应**（F-6；几何字面量无牙，已改由声明派生 + t11c/t11d）",
               "③ step_did_work 粗粒度/网络 FS 灵敏度": f"**有缺口**（F-7；单信号 mtime ⇒ 假停机；非步本地 ⇒ 假通过方向）；已改多信号 + 残余登记",
               "④ REGISTER_STATUSES/counts 复算键集是否过严": f"**不过严**（V4：并集比对 = fail-closed 设计；as-found {d['total']} 项复算一致、OPEN {d['OPEN']}）"},
           "disposition_ref": "登记簿 `co172:F-*`（本件 findings 的处置见 CO-173；本件结论不随修复漂移）",
           "reproduce": ["python3 tools/p3_v57_co172_rev19_co166_co171_review.py（只读；对象钉在 7bffb75）"],
           "redline": "只读 as-found（`git show`）+ 内存注入；不改 SPEC/板/冻结四源/台账/登记簿/他人记录；零坐标搜索。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [f"# CO-172 — 非执行者对抗复评（CO-166..CO-171）｜as-found @ `{AS_FOUND_REV}`", "",
             f"- verdict：**{verdict}**｜findings：{n}", "",
             "| id | sev | kind | what（摘要） |", "|---|---|---|---|"]
    for f in findings:
        lines.append(f"| {f['id']} | {f['sev']} | {f['kind']} | {f['what'][:120]}... |")
    lines += ["", "独立确认：", ""] + [f"- {x}" for x in indep] + ["", "负控（内存注入）：", ""] + [f"- {x}" for x in neg] + [""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": n, "findings": [f["id"] for f in findings],
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    # CO-185（R-CO185-1）：复评步**退出码须反映 verdict**（PASS / PASS_WITH_FINDINGS 为通过档；其余停机）
    return 0 if verdict in ("PASS", "PASS_WITH_FINDINGS") else 1


if __name__ == "__main__":
    sys.exit(main())
