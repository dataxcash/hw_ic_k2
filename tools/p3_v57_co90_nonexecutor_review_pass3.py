#!/usr/bin/env python3
"""CO-90：[L2 可审计性] 非执行者侧对抗评审 **pass 3/3** —— 对象 = rev-9 新基线（CO-88/CO-89 + 全链）。

背景：CO-89 把 SPEC 提升到 rev-9 并重基线全链后，CO-85（pass 2/2）的**复现基线失效**（其证书只对旧图纸/SPEC 指纹有效）
⇒ handoff-z2 §7-2 登记「新基线非执行者复评欠」。本件即履行该义务。

评审者资格：本会话为 context 归零后的续接会话，未执行 CO-88/CO-89 或 rev-9 全链任何变更 ⇒ 非执行者。

方法（独立度分栏）：
  V1 同代码复跑全链 G4→G7 + 与 rev-9 冻结指纹**逐字节**比对（证明可复现，非独立实现）。
  V2 板事实**自写直解**（段/过孔/zone，独立于本链工具）。
  V3 SPEC rev-9 事实：`pd` 外逐值等于 rev-8 / 旧 BOM 退役对数 / 解耦板实 / ppc↔板实 pad 双射。
  V4 co88 闸**注入突变测试**（4 个合成件：孤儿 ref / 缺覆盖 / 空解耦 / 缺失解耦 ref）—— 检验判据牙齿，非只看记录自述。
  V5 覆盖口径：`netclass_assignments` 的 POWER 类网 vs 生成器内置网集（CO-90 F3 的证据）。
  V6 CO-89 幂等：用项目发生器在 scratch 重生成 ppc，与 rev-9 的 entries/blocked **逐值**比对。

需 pcbnew ⇒ AppDir python3.11 运行。只读交付件；scratch 即用即删；不改 SPEC/板/阈值；零 while/坐标搜索。
"""
from __future__ import annotations
import hashlib, importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
PRO = K2 / "k2_v4_8L.l4.kicad_pro"
DRU = K2 / "k2_v4_8L.l4.kicad_dru"
SPEC9 = L3 / "SPEC_k2_v4.spec-rev-9.json"
SPEC8 = L3 / "SPEC_k2_v4.spec-rev-8.json"
CO88 = K2 / "tools/p3_v57_co88_pdn_board_reality_gate.py"
REC = STEP2 / "m13_v57_co90_nonexecutor_review_pass3.json"
SCRATCH = K2 / ".co90_tmp"
PY3 = "/usr/bin/python3"
APPPY = str(K2.parent / "AppDir/usr/bin/python3.11")

CHAIN = {  # rev-9 冻结指纹（handoff-z2 §2；V1 逐字节比对基准）
    "drawing": (STEP2 / "m13_v57_w3_joint_assignment.json", "3d452429bbc934c3"),
    "landing": (STEP2 / "m13_v57_w3_chip_landing_rows.json", "da21d0186a9c643c"),
    "G5": (STEP2 / "m13_v57_w3_validation.json", "7acb3186c3b68848"),
    "construction": (STEP2 / "m13_v57_l4_construction.json", "ca2ff16f6445424c"),
    "l4val": (STEP2 / "m13_v57_l4_validation.json", "a87b8d17bef6edca"),
    "board": (BOARD, "0e636a67c1472462"),
    "fab": (STEP2 / "m13_v57_l5_fab_record.json", "6d85160413770fa5"),
    "dfm": (STEP2 / "m13_v57_l5_dfm_dft_record.json", "40445f87be664f31"),
    "si": (STEP2 / "m13_v57_l5_si_pi_emc_record.json", "73f9b59ed5f6f3ce"),
    "dru": (DRU, "3148703240d54420"),
    "pro": (PRO, "ce2c2bf0da79a1ff"),
    "co88": (STEP2 / "m13_v57_co88_pdn_board_reality_gate.json", "bf69909aa64dc494"),  # CO-88.3（F1/F2/F4 修复后；纯函数记录，可钉）
}
# 注：co77 链到**最新 boundary**（doc_sha16 随 boundary 变化），不钉 record sha，改钉 verdict。
GATES = {"co78": "b736a0df7226f155", "co81": "16b262663238a60a",
         "co84": "b927acbe46ec3007", "co87": "24aeb57f71a716f4", "co69": "18a86c998dd6b4de"}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def board_facts(txt: str) -> dict:
    seg = {}
    for m in re.finditer(r"\(segment\b", txt):
        lm = re.search(r'\(layer "([^"]+)"\)', txt[m.start():m.start() + 400])
        seg[lm.group(1)] = seg.get(lm.group(1), 0) + 1
    return {"segments_by_layer": seg, "n_segments": sum(seg.values()),
            "n_vias": len(re.findall(r"\(via\b", txt)), "n_zones": len(re.findall(r"\(zone\b", txt))}


def v1_chain_rerun() -> dict:
    cmds = [(PY3, "tools/p3_v57_w3_constructive.py", "--r1-5-shape", "co16"),
            (PY3, "tools/p3_v57_w3_constructive_validator_v2.py"),
            (APPPY, "tools/p3_v57_l4_apply_drawing.py", "--board", "--escape-domain",
             "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co37_escape_domain.json"),
            (APPPY, "tools/p3_v57_l4_validator.py"), (APPPY, "tools/p3_v57_l5_signoff.py")]
    clean = {k: v for k, v in os.environ.items() if k not in ("PYTHONHOME", "PYTHONPATH")}
    runs = []
    for c in cmds:
        env = clean if c[0] == PY3 else {**os.environ, "PYTHONPATH": str(K2.parent / "_shared")}
        r = subprocess.run(list(c), cwd=str(K2), capture_output=True, text=True, timeout=1200, env=env)
        runs.append({"cmd": " ".join(c[:2]), "rc": r.returncode})
        if r.returncode != 0:
            return {"ok": False, "runs": runs, "stderr_tail": (r.stderr or "")[-300:]}
    drift = {k: {"expected": exp, "actual": s16(p)} for k, (p, exp) in CHAIN.items()
             if exp and s16(p) != exp}
    return {"ok": not drift, "runs": runs, "drift": drift}


def v4_mutation_tests() -> dict:
    spec = importlib.util.spec_from_file_location("co88_gate", CO88)
    co88 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(co88)
    real = json.loads(SPEC9.read_text(encoding="utf-8"))
    SCRATCH.mkdir(exist_ok=True)

    def run(mut, label):
        p = SCRATCH / f"{label}.json"
        p.write_text(json.dumps(mut, ensure_ascii=False, indent=1), encoding="utf-8")
        co88.current_spec = lambda p=p: p
        co88.OUT = SCRATCH / f"{label}.rec.json"
        co88.main()
        r = json.loads(co88.OUT.read_text(encoding="utf-8"))
        return {"verdict": r["verdict"][:4], "A": r["A_refdes_existence"]["verdict"],
                "B": r["B_coverage"]["verdict"], "C": r["C_decoupling"]["verdict"],
                "headline": r["verdict"].startswith("PASS"),
                "by_criterion": r["verdict_by_criterion"], "teeth_ok": r["teeth"].get("detector_orphan_injection_caught")}

    m1 = json.loads(json.dumps(real))
    m1["pd"]["zone_defs"]["power_pad_connect"]["entries"].append({"ref": "U99", "pad": "1", "net": "GND"})
    m2 = json.loads(json.dumps(real))
    m2["pd"]["zone_defs"]["power_pad_connect"]["entries"].pop(0)
    m3 = json.loads(json.dumps(real))
    m3["pd"]["zone_defs"]["decoupling_via_to_plane"]["targets"] = []
    m3["pd"]["zone_defs"]["decoupling_via_to_plane"]["vias"] = []
    m4 = json.loads(json.dumps(real))
    m4["pd"]["zone_defs"]["decoupling_via_to_plane"]["vias"] = [{"ref": "U99", "pos": [[0.0, 0.0]]}]
    base, r1, r2, r3, r4 = run(real, "base"), run(m1, "m1"), run(m2, "m2"), run(m3, "m3"), run(m4, "m4")
    ok = (base["headline"] and r1["A"] == "FAIL" and r2["B"] == "FAIL"
          and not r3["headline"] and r3["C"] == "FAIL" and r4["C"] == "FAIL")
    shutil.rmtree(SCRATCH, ignore_errors=True)
    return {"ok": ok, "baseline": base, "orphan_injected": r1, "coverage_removed": r2,
            "empty_decoupling": r3, "missing_decoupling_ref": r4,
            "note": "F1 回归：empty_decoupling 在修复前 headline=PASS 而 C=FAIL（空真/partial pass）"}


def main() -> int:
    SCRATCH.mkdir(exist_ok=True)
    rev8 = json.loads(SPEC8.read_text(encoding="utf-8"))
    rev9 = json.loads(SPEC9.read_text(encoding="utf-8"))
    spec9_sha = s16(SPEC9)
    txt = BOARD.read_text(encoding="utf-8", errors="replace")

    v1 = v1_chain_rerun()
    v2 = {"board_sha16": s16(BOARD), "facts": board_facts(txt)}
    # V3 事实
    # CO-90 F6：set 迭代序随 PYTHONHASHSEED 变 ⇒ 任何 set→list 必须 sorted()，否则本记录 sha 不可复现。
    outside = sorted(k for k in set(rev8) | set(rev9)
                     if k not in ("pd", "spec_version", "_spec_rev_9")
                     and json.dumps(rev8.get(k), sort_keys=True) != json.dumps(rev9.get(k), sort_keys=True))
    pd_delta = sorted(k for k in set(rev8["pd"]) | set(rev9["pd"])
                      if json.dumps(rev8["pd"].get(k), sort_keys=True) != json.dumps(rev9["pd"].get(k), sort_keys=True))
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))
    board_refs = {fp.GetReference() for fp in b.GetFootprints()}
    refs9 = {str(e["ref"]) for e in rev9["pd"]["zone_defs"]["power_pad_connect"]["entries"]} | \
            {str(e["ref"]) for e in rev9["pd"]["zone_defs"]["power_pad_connect"]["blocked"]}
    orphans9 = sorted(refs9 - board_refs)
    orphan8_e = sum(1 for e in rev8["pd"]["zone_defs"]["power_pad_connect"]["entries"] if str(e["ref"]) not in board_refs)
    orphan8_b = sum(1 for e in rev8["pd"]["zone_defs"]["power_pad_connect"]["blocked"] if str(e["ref"]) not in board_refs)
    retired = rev9["pd"]["zone_defs"]["power_pad_connect"]["retired_superseded_bom"]
    dv9 = rev9["pd"]["zone_defs"]["decoupling_via_to_plane"]
    board_net_refs = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            board_net_refs.setdefault(p.GetNetname(), set()).add(fp.GetReference())
    dec_missing = sorted(set(dv9.get("targets", [])) - board_refs)
    v3 = {"outside_pd_changed_top_level_keys": outside, "pd_changed_subkeys": pd_delta,
          "retired_entries_blocked": [retired["n_entries"], retired["n_blocked"]],
          "rev8_orphans_entries_blocked": [orphan8_e, orphan8_b],
          "rev9_orphan_refs": orphans9, "rev9_decoupling_targets_missing": dec_missing,
          "rev8_decoupling_vias": len(rev8["pd"]["zone_defs"]["decoupling_via_to_plane"].get("vias", [])),
          "rev9_decoupling_vias": len(dv9.get("vias", [])),
          "retired_vias": len(dv9.get("retired_vias_superseded_bom", {}).get("vias", []))}
    # V3b ppc ↔ 板实 pad 双射（独立于 CO-88）
    sys.path.insert(0, str(K2.parent / "_shared"))
    from eda_core.pad_connect_gen import DEFAULT_PWR_NETS
    pads = {(fp.GetReference(), str(p.GetNumber()))
            for fp in b.GetFootprints() for p in fp.Pads()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetNetname() in DEFAULT_PWR_NETS}
    ppc9 = rev9["pd"]["zone_defs"]["power_pad_connect"]
    dec = {(str(e["ref"]), str(e["pad"])) for e in ppc9["entries"]} | \
          {(str(e["ref"]), str(e["pad"])) for e in ppc9["blocked"]}
    v3["bijection_board_pads_vs_decisions"] = {"board_pads": len(pads), "decisions": len(dec),
                                               "only_board": sorted(pads - dec)[:5], "only_spec": sorted(dec - pads)[:5],
                                               "exact": pads == dec}
    # V4 突变测试
    v4 = v4_mutation_tests()
    # V5 覆盖口径
    pro = json.loads(PRO.read_text(encoding="utf-8"))
    ns = pro["board"]["net_settings"] if "net_settings" in pro.get("board", {}) else pro["net_settings"]
    asg = ns.get("netclass_assignments", {})
    power_nets = sorted(n for n, v in asg.items() if "POWER" in v)
    outside_scope = [n for n in power_nets if n not in DEFAULT_PWR_NETS]
    smd_by_net = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                smd_by_net[p.GetNetname()] = smd_by_net.get(p.GetNetname(), 0) + 1
    v5 = {"pwr_nets_source": "eda_core.pad_connect_gen.DEFAULT_PWR_NETS（内置常量）",
          "power_class_nets_not_in_scope": outside_scope,
          "power_class_pads_outside_scope": {n: smd_by_net.get(n, 0) for n in outside_scope},
          "note": "B 判据分母 309 = 内置网集上的板实 SMD pad；板 POWER 类另有 1 个 SMD pad 不在集内 ⇒ 100% 为口径内声明"}
    # V6 CO-89 幂等（scratch 重生成比对）
    SCRATCH.mkdir(exist_ok=True)
    cand = SCRATCH / "regen.json"
    shutil.copy(SPEC9, cand)
    r = subprocess.run([APPPY, "-m", "eda_core.pad_connect_gen", "--spec", str(cand), "--board", str(BOARD)],
                       cwd=str(K2.parent), capture_output=True, text=True, timeout=600,
                       env={**__import__("os").environ, "PYTHONPATH": str(K2.parent / "_shared")})
    gen = json.loads(cand.read_text(encoding="utf-8"))["pd"]["zone_defs"]["power_pad_connect"]
    v6 = {"rc": r.returncode, "regen_entries_blocked": [len(gen["entries"]), len(gen["blocked"])],
          "entries_equal_to_rev9": gen["entries"] == ppc9["entries"],
          "blocked_equal_to_rev9": gen["blocked"] == ppc9["blocked"]}
    shutil.rmtree(SCRATCH, ignore_errors=True)

    gate_suffix = {"co77": "closure_declaration_sweep.json", "co78": "layer_role_drift_gate.json",
                   "co81": "project_rules_gate.json", "co84": "dru_domain_gate.json",
                   "co87": "l2_acceptance_coverage.json", "co69": "adversarial_review.json"}
    gates = {k: {"expected": v, "actual": s16(STEP2 / ("m13_v57_" + k + "_" + gate_suffix[k]))}
             for k, v in GATES.items()}
    # co77 链到最新 boundary（记录内 doc_sha16 随 boundary 变）。为保本记录**逐字可复现**，
    # 只留 verdict（PASS），不存 doc/doc_sha16（否则记录 sha 随 boundary 变化 ⇒ boundary 引用成死结）。
    co77 = json.loads((STEP2 / "m13_v57_co77_closure_declaration_sweep.json").read_text(encoding="utf-8"))
    gates["co77"] = {"expected": "PASS", "actual": co77["verdict"]}
    gates_ok = all(g["expected"] == g["actual"] for g in gates.values())

    findings = [
        {"id": "F4", "sev": "中", "class": "记录可复现性（哈希体含目录扫描）",
         "what": "co88 记录曾嵌 `ripple_checklist()`（扫描 tools/*.py）⇒ 记录 sha 随**无关工具文件**增删而变：移走 CO-90 工具 → `d320c81263733158`；放回 → `b9990766698af315`（实测两次对照）",
         "evidence": "两次对照实测 + 修复后「移走/放回 CO-90 工具」三次同值 `bf69909aa64dc494`",
         "status": "FIXED（CO-88.3：ripple 移出哈希体；记录 = (SPEC, 板) 纯函数）"},
        {"id": "F6", "sev": "中", "class": "记录确定性（set 迭代序）",
         "what": "本评审记录自身含 `[k for k in set(...)]`（`outside_pd_changed_top_level_keys` / `pd_changed_subkeys`）⇒ list 序随 PYTHONHASHSEED 变 ⇒ 记录 sha 不可复现（实测同输入两次运行不一致）",
         "evidence": "4 个 seed 实测 `pd_changed_subkeys` 出现 4 种排列；修复后（sorted）跨 seed 同值",
         "status": "FIXED（CO-90.3：set→list 一律 sorted；记录为输入的纯函数）"},
        {"id": "F5", "sev": "中", "class": "引用闸空真（行级历史豁免）",
         "what": "co77 历史豁免按**整行**判定 ⇒ 「现行值 + 同行括号记录旧值已取代」的**现行值**被一并豁免：co88 记录漂移后 co77 仍报 citation_mismatch=[]",
         "evidence": "负控：注入 `deadbeefdeadbeef` 现行 sha → co77 报 CITATION_MISMATCH（修复前该形态漏过）",
         "status": "FIXED（CO-77.3：豁免改为按引用判定——校验紧跟该 sha 之后的标记窗口）"},
        {"id": "F1", "sev": "中", "class": "闸内空真/partial pass",
         "what": "CO-88 headline verdict 未并入判据 C 的『目标非空』测试 ⇒ 构造态（targets=[] 且 vias=[]）下 C=FAIL 而 headline=PASS",
         "evidence": "mutation m3（修复前 headline=PASS / C=FAIL）", "status": "FIXED（CO-88.2）"},
        {"id": "F2", "sev": "中", "class": "空真牙（CO-79 同类）",
         "what": "CO-88 自述 teeth 恒真：synthetic_orphan_ref_detected=false 只查 board_refs、syn 为死代码；silent_detector_control 第二操作数恒真",
         "evidence": "源码 129-131 行（修复前）；4 个注入突变在修复后全 True", "status": "FIXED（CO-88.2）"},
        {"id": "F3", "sev": "低-中", "class": "覆盖口径/声明范围",
         "what": "CO-88/89『板实 SMD 电源地 pad 309/309 = 100%』的分母 = 内置 DEFAULT_PWR_NETS；板 POWER 类尚含 C89.1 PWR_5V_KEY（SMD, 0 走线）不在集内",
         "evidence": "V5：power_class_nets_not_in_scope=['PWR_5V_KEY']，1 个 SMD pad；pad_connect_gen docstring 自称『从 SPEC 推导』但实现只读内置常量",
         "status": "已登记（不改分母：涉及网范围=需 PM/owner 确认，改则 SPEC rev-10 + 全链重基线）"},
    ]
    rec = {"artifact": "m13_v57_co90_nonexecutor_review_pass3", "schema": 1, "revision": "CO-90.3",
           "nature": "L2 可审计性：rev-9 新基线的非执行者对抗评审 pass 3/3（对象 CO-88/CO-89 + 全链）",
           "reviewer_independence": "context 归零续接会话；未执行 CO-88/CO-89/rev-9 全链变更",
           "rev9_baseline": {"spec_rev9_sha16": spec9_sha, "board_sha16": s16(BOARD), "drawing_sha16": s16(CHAIN["drawing"][0])},
           "V1_chain_rerun_byte_identical": v1,
           "V2_board_facts_selfparsed": v2,
           "V3_spec_rev9_facts": v3,
           "V4_gate_mutation_tests": v4,
           "V5_coverage_scope": v5,
           "V6_co89_idempotent_regeneration": v6,
           "regression_gates": {"fingerprints": gates, "ok": gates_ok},
           "findings": findings,
           "verdict": ("PASS（rev-9 新基线可复现 + CO-88/89 事实独立复核通过；F1/F2/F4 已修，F3/F5 已登记）"
                       if (v1.get("ok") and v3["outside_pd_changed_top_level_keys"] == []
                           and orphans9 == [] and not dec_missing and v3["bijection_board_pads_vs_decisions"]["exact"]
                           and v4["ok"] and v6["entries_equal_to_rev9"] and v6["blocked_equal_to_rev9"] and gates_ok)
                       else "FAIL（见各 V 栏）"),
           "non_claims": "不改 SPEC/板/图纸/阈值；不声称 PDN 压降/热；不触 L1；V1 为同代码复跑非独立实现。",
           "redline": "零几何；scratch 即用即删；不改历史件；无 while/坐标搜索。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"][:40], "V1_ok": v1.get("ok"),
                      "V3_outside": outside, "V3_orphans": orphans9,
                      "V4_ok": v4["ok"], "V5_outside_scope": outside_scope,
                      "V6_equal": [v6["entries_equal_to_rev9"], v6["blocked_equal_to_rev9"]],
                      "gates_ok": gates_ok}, ensure_ascii=False))
    return 0 if rec["verdict"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
