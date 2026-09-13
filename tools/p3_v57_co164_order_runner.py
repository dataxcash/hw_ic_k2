#!/usr/bin/env python3
"""CO-164/CO-167/CO-169/CO-174/CO-180/CO-181/CO-182/CO-183 — **规范复现序机判执行器**（R-CO164-1 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1）：以 rc 为准判定收敛，禁「sha 稳定即收敛」。

缘起（实测事故，CO-163）：`co146_boundary_append.py` 因 §37 文本里的 f-string 花括号语法错误**每次崩溃（rc=1）**，
但收敛判定只看 boundary/记录 sha ⇒ sha 恒不变 ⇒ 报「CONVERGED」，边界 §37 实际从未写入、pin 表陈旧（co77/co135/co136 判 FAIL）。
即「以 sha 稳定替代 rc 检查」会产生**假收敛**（本会话由一个独立 rc 复核才发现）。

本器（**不在**规范序内运行，避免自递归；其报告落在 `.archer_tmp/`，**不被 boundary 引用** ⇒ 不构成下游快照/不动点）：
  ① 依 R-CO163-3 顺序逐步执行（子进程），rc 策略：`EXPECTED_NONZERO = {co146_jlc_dfm_gate}`（verdict=FAIL 属预期），
     其余任一步非零 ⇒ **立即停机**并报出门名/rc/stderr 尾（fail-fast，禁"继续跑完再说"）；
  ② 每轮迭代后比对受控 sha（boundary + 关键记录 + 台账/登记簿）；**仅当** rc 全合规**且** sha 逐轮稳定 ⇒ 判 CONVERGED；
  ③ `--check` 只做静态体检：步骤文件存在 + 可编译 + rc 策略声明完备（零执行、零落盘），可作轻量 sanity；
  ④ CO-174（R-CO174-1）：`did_work` 归因**仅限本步声明的主产物集**（非全局受控集）⇒ 并发/他人写**其它**受控件
     不再被误判为「本步做了事」（关闭 CO-172 F-7 的假通过方向）；报告另记 `declared_changed` / `stray_changed` 证据。
     全局受控集仍保留用于收敛 sha（R-CO165）；**残余如实登记**：共享主产物（台账/登记簿）上的并发写仍可误判。
CLI:
  python3 tools/p3_v57_co164_order_runner.py [--check] [--max-iter 5]
"""
from __future__ import annotations
import argparse, ast, hashlib, json, re, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
PY = K2.parent / "AppDir" / "usr" / "bin" / "python3.11"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REPORT = K2 / ".archer_tmp/co164_order_report.json"
# R-CO163-3 规范复现序（与 boundary §37 同步；末步 boundary_append 为 pin 再对齐）
ORDER = ["co146_impedance_table", "co146_pm_eval", "co146_ledger_add", "co153_k9_domain_coverage",
         "co148_u6_datasheet_inputs", "co148_thermal_ruling", "co149_thermal_mitigation_derive", "co147_l2_ruling",
         "co146_jlc_dfm_gate", "co146_jlc_fab_package", "co152_findings_disposition", "co155_co154_findings_disposition",
         "co156_co154_open_disposition", "co157_gate_hardening_3", "co158_l5_packet_selfcontained",
         "co159_rev19_co156_co157_co158_review", "co160_co159_findings_disposition", "co161_gap_hardening_4",
         "co162_verdict_binding", "co163_binding_to_order_notes", "co166_rev19_co159_co165_review",
         "co167_co166_findings_disposition", "co168_register_consistency", "co169_step_output_oracle", "co170_stackup_binding", "co171_order_notes_record_figures",
         "co172_rev19_co166_co171_review", "co173_co172_findings_disposition", "co174_step_artifact_attribution", "co175_package_parity_binding", "co176_gate_selfcheck_evidence", "co177_capability_value_binding", "co178_drc_item_limit_derivation", "co179_sensitivity_teeth_hardening", "co180_teeth_judgment_integrity",
         "co124_input_selfcheck_gate", "co150_k9_domain_gate",
         "co146_boundary_append", "co77_closure_declaration_sweep", "co120_provenance_pin_gate", "co146_boundary_append", "co135_review_hygiene",
         "co136_gate_hygiene", "co78_layer_role_drift_gate", "co81_project_rules_gate", "co84_dru_domain_gate",
         "co95_in4_reachability", "co98_reachability_status_report", "co106_reference_plane_gate", "co146_boundary_append"]
# CO-182（R-CO182-1）：**扫描 boundary citation 的步**须**紧跟 boundary 刷新步**（原滞后根因：
# 刷新步在其前、co77/co120 在其后改写被引记录 ⇒ co135 见 pin 瞬时陈旧 ⇒ 首轮停机）。
BOUNDARY_SCAN_GUARDED = ("co77_closure_declaration_sweep", "co135_review_hygiene")
BOUNDARY_REFRESH_STEP = "co146_boundary_append"

# 允许非零的步骤（**须带 verdict 证据**：rc≠0 不等于预期 FAIL —— CO-165）
EXPECTED_NONZERO = {
    "co146_jlc_dfm_gate": {"verdict": "FAIL", "record": str(STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
                           # CO-176（G-1）：rc≠0 只豁免 **verdict**，不豁免该步**自检牙齿**（须全 True）
                           "teeth_path": ["teeth"],
                           "why": "verdict=FAIL（DFM 两项阻塞）属预期；rc=1 即 R-CO158-3/R-CO159-4 生效"},
}

# ── CO-174（R-CO174-1）：**每步主产物集**（步本地归因；集合由实测探针逐步跑 ORDER 钉定，非猜测） ──
_A = "pm_gate/artifacts/k2_v4/"
_S2 = _A + "L3/mcio_feas_step2/"
_A2 = _A + "L2/"
_A5 = _A + "L5/jlc_package/"
_REG = _A2 + "input_defect_register_v1.json"
_LED = _A2 + "derived_value_ledger_v1.json"
_SVG = _A5 + "03_stackup/JLC08161H_stackup.svg"
STEP_ARTIFACTS = {
    "co146_impedance_table": [_S2 + "m13_v57_co146_impedance_table.json"],
    "co146_pm_eval": [_S2 + "m13_v57_co146_pm_eval.json"],
    "co146_ledger_add": [_LED],
    "co153_k9_domain_coverage": [_LED, _REG],
    "co148_u6_datasheet_inputs": [_S2 + "m13_v57_co148_u6_ds320pr1601_inputs.json"],
    "co148_thermal_ruling": [_LED, _REG, _S2 + "m13_v57_co148_thermal_ruling.json"],
    "co149_thermal_mitigation_derive": [_LED, _REG, _S2 + "m13_v57_co149_u6_thermal_mitigation.json"],
    "co147_l2_ruling": [_REG, _S2 + "m13_v57_co147_l2_ruling.json"],
    "co146_jlc_dfm_gate": [_S2 + "m13_v57_co146_jlc8_capability.json", _S2 + "m13_v57_co146_jlc_dfm_gate.json"],
    "co146_jlc_fab_package": [_S2 + "m13_v57_co146_jlc_fab_package.json",
                              _A5 + "MANIFEST.json", _A5 + "ORDER_NOTES.md", _SVG],
    "co152_findings_disposition": [_REG],
    "co155_co154_findings_disposition": [_REG],
    "co156_co154_open_disposition": [_REG],
    "co157_gate_hardening_3": [_REG],
    "co158_l5_packet_selfcontained": [_REG],
    "co159_rev19_co156_co157_co158_review": [_S2 + "m13_v57_co159_rev19_co156_co157_co158_review.json"],
    "co160_co159_findings_disposition": [_REG],
    "co161_gap_hardening_4": [_REG],
    "co162_verdict_binding": [_REG],
    "co163_binding_to_order_notes": [_REG],
    "co166_rev19_co159_co165_review": [_S2 + "m13_v57_co166_rev19_co159_co165_review.json"],
    "co167_co166_findings_disposition": [_REG],
    "co168_register_consistency": [_REG],
    "co169_step_output_oracle": [_REG],
    "co170_stackup_binding": [_REG],
    "co171_order_notes_record_figures": [_REG],
    "co172_rev19_co166_co171_review": [_S2 + "m13_v57_co172_rev19_co166_co171_review.json"],
    "co173_co172_findings_disposition": [_REG],
    "co174_step_artifact_attribution": [_REG],
    "co175_package_parity_binding": [_REG],
    "co176_gate_selfcheck_evidence": [_REG],
    "co177_capability_value_binding": [_REG],
    "co178_drc_item_limit_derivation": [_REG],
    "co179_sensitivity_teeth_hardening": [_REG],
    "co180_teeth_judgment_integrity": [_REG],
    "co124_input_selfcheck_gate": [_S2 + "m13_v57_co124_input_selfcheck_gate.json"],
    "co150_k9_domain_gate": [_REG, _S2 + "m13_v57_co150_k9_domain_gate.json"],
    "co146_boundary_append": [_S2 + "m13_v57_w3_joint_assignment_boundary_v1_82.md"],
    "co77_closure_declaration_sweep": [_S2 + "m13_v57_co77_closure_declaration_sweep.json"],
    "co120_provenance_pin_gate": [_S2 + "m13_v57_co120_provenance_pin_gate.json"],
    "co135_review_hygiene": [_S2 + "m13_v57_co135_review_hygiene.json"],
    "co136_gate_hygiene": [_S2 + "m13_v57_co136_gate_hygiene.json"],
    "co78_layer_role_drift_gate": [_S2 + "m13_v57_co78_layer_role_drift_gate.json"],
    "co81_project_rules_gate": [_S2 + "m13_v57_co81_project_rules_gate.json"],
    "co84_dru_domain_gate": [_S2 + "m13_v57_co84_dru_domain_gate.json"],
    "co95_in4_reachability": [_S2 + "m13_v57_co95_in4_reachability.json"],
    "co98_reachability_status_report": [_S2 + "m13_v57_co98_reachability_status_report.json"],
    "co106_reference_plane_gate": [_S2 + "m13_v57_co106_reference_plane_gate.json"],
}
# CO-174 残余（如实登记）：主产物**被多步共享**时，他人对该件的写仍会被误判为「本步做了事」。
# 彻底关闭须每步写独立标记件（未做）；本表即该残余的**显式枚举**，t13c 机判防其被静默遗忘。
SHARED_ARTIFACT_RESIDUAL = {
    _LED: "共享主产物（co146_ledger_add / co153 / co148_thermal / co149）：他人写台账仍可误判",
    _REG: "共享主产物（co152..co174 处置类 17 步）：他人写登记簿仍可误判",
}

# CO-181（F-3）：**声明产物齿集 pin**（键 = 工件 basename；值 = 齿名有序集）——
# 判据不得自指：记录自定齿集 ⇒ 静默删齿/改名即可规避。任一漂移 ⇒ 该步 fail-closed（t16 机判）。
EXPECTED_TEETH = {
    "MANIFEST.json": ['t01_idempotent', 't02_8_copper_gerbers', 't03_drill_present', 't04_all_hashed', 't05_declared_rulings_packaged', 't06_order_notes_refs_resolve_in_package', 't07_packaged_rulings_match_sources', 't07b_parity_detector_sensitivity', 't08_declared_dirs_present', 't09_order_notes_binding_params', 't09b_binding_param_detector_sensitivity', 't10_declared_binding_source_pinned', 't10b_binding_source_pin_discriminates', 't11_stackup_svg_declared_binding', 't11b_stackup_svg_binding_sensitivity', 't11c_stackup_svg_copper_geometry_binding', 't11d_stackup_svg_copper_geometry_sensitivity', 't12_order_notes_record_figures', 't12b_record_figure_binding_sensitivity', 't12c_impedance_spread_binding_sensitivity', 't12d_via_census_binding_sensitivity', 't12e_mask_facts_binding_sensitivity', 't12f_thermal_figures_binding_sensitivity', 't12g_jlc_capability_binding_sensitivity', 't12h_drc_rules_edge_binding_sensitivity', 't15_impedance_copy_parity', 't15b_impedance_copy_parity_sensitivity', 't16_layer_sequence_derivation', 't16b_layer_sequence_sensitivity'],
    "m13_v57_co106_reference_plane_gate.json": ['baseline_pin_binding', 'carrier_exemption_declared_only', 'classifier_detector', 'continuity_detector', 'fail_open_closed', 'frame_inset_detector', 'teeth_are_bool_only', 'teeth_ok', 'verdict_positive_control'],
    "m13_v57_co120_provenance_pin_gate.json": ['negative_control_freetext_board_basis_rejected', 'negative_control_register_snapshot_caught', 'negative_control_top_level_register_snapshot_caught', 'negative_control_undeclared_snapshot_caught', 'negative_control_undeclared_stale_caught', 'negative_control_unregistered_board_sha_rejected', 'positive_control_board_sha_basis_accepted', 'positive_control_declared_register_snapshot_passes', 'positive_control_declared_snapshot_passes', 'positive_control_matching_pin_passes', 'positive_control_note_key_not_snapshot', 'teeth_ok'],
    "m13_v57_co124_input_selfcheck_gate.json": ['T10_thermal_option_domain_teeth', 'T10b_thermal_domain_no_false_positive', 'T11_drop_domain_teeth', 'T11b_drop_domain_no_false_positive', 'T12_declared_unpinned_teeth', 'T12b_declared_no_false_positive', 'T13_conservative_unproved_teeth', 'T13b_conservative_no_false_positive', 'T14_unknown_kind_teeth', 'T14b_empty_domain_cap_teeth', 'T14c_kind_coverage_no_false_positive', 'T15_declared_binding_teeth', 'T15b_declared_binding_no_false_positive', 'T15c_declared_empty_computed_teeth', 'T16_faithful_provenance_teeth', 'T16b_faithful_provenance_no_false_positive', 'T16c_authoritative_dv_missing_teeth', 'T17_process_floor_evidence_teeth', 'T17b_process_floor_no_false_positive', 'T18_k9_finder_id_coverage', 'T18b_k9_finder_id_no_undeclared', 'T18c_k9_finder_battery_nonempty', 'T18d_k9_finder_ids_source_complete', 'T18e_k9_finder_id_extractor_sensitivity', 'T19_dv_inventory_teeth', 'T19b_dv_inventory_no_false_positive', 'T1_netclass_drift', 'T20_identity_unhandled_form_teeth', 'T20b_identity_unhandled_no_false_positive', 'T21_register_status_vocabulary', 'T21b_register_counts_rederived', 'T21c_register_consistency_no_false_positive', 'T2_unregistered_finding_detected', 'T3_threshold_unregistered', 'T4_doc_anchor_missing', 'T5_derived_without_principle', 'T6_unreachable_derived', 'T7_requirement_carries_value', 'T8_identity_drift', 'T9_exemption_unpinned'],
    "m13_v57_co136_gate_hygiene.json": ['H4_negative_control_write_only_caught', 'H4_positive_control_upsert_ok'],
    "m13_v57_co146_impedance_table.json": ['t01_reproduce_spec_first_order', 't02_overwide_must_fail_tol'],
    "m13_v57_co146_jlc_dfm_gate.json": ['t01_track_width_limit_teeth', 't02_blind_via_item_fails', 't03_board_rule_edge_bound', 't04_capability_citation_bound', 't05_capability_citation_sensitivity', 't06_capability_value_bound', 't07_capability_value_bind_sensitivity', 't07b_anchor_localization_sensitivity', 't08_drc_item_limits_derived'],
    "m13_v57_co146_jlc_fab_package.json": ['t01_idempotent', 't02_8_copper_gerbers', 't03_drill_present', 't04_all_hashed', 't05_declared_rulings_packaged', 't06_order_notes_refs_resolve_in_package', 't07_packaged_rulings_match_sources', 't07b_parity_detector_sensitivity', 't08_declared_dirs_present', 't09_order_notes_binding_params', 't09b_binding_param_detector_sensitivity', 't10_declared_binding_source_pinned', 't10b_binding_source_pin_discriminates', 't11_stackup_svg_declared_binding', 't11b_stackup_svg_binding_sensitivity', 't11c_stackup_svg_copper_geometry_binding', 't11d_stackup_svg_copper_geometry_sensitivity', 't12_order_notes_record_figures', 't12b_record_figure_binding_sensitivity', 't12c_impedance_spread_binding_sensitivity', 't12d_via_census_binding_sensitivity', 't12e_mask_facts_binding_sensitivity', 't12f_thermal_figures_binding_sensitivity', 't12g_jlc_capability_binding_sensitivity', 't12h_drc_rules_edge_binding_sensitivity', 't15_impedance_copy_parity', 't15b_impedance_copy_parity_sensitivity', 't16_layer_sequence_derivation', 't16b_layer_sequence_sensitivity'],
    "m13_v57_co146_pm_eval.json": ['t01_current_doubling_linear', 't02_copper_thickness_monotone', 't03_plane_geometry_from_board', 't04_datasheet_input_flips_verdict', 't05_psi_route_agrees_fail'],
    "m13_v57_co147_l2_ruling.json": ['t01_mask_measured_below_jlc'],
    "m13_v57_co148_thermal_ruling.json": ['t01_worst_tj_over_limit', 't02_gnd_via_deficit'],
    "m13_v57_co148_u6_ds320pr1601_inputs.json": ['t01_seven_values', 't02_all_pact_rows'],
    "m13_v57_co149_u6_thermal_mitigation.json": ['t01_two_routes_agree', 't02_asbuilt_unreachable_all', 't03_declared_option_covers_all', 't04_rjb_more_demanding', 't05_sensitivity_disclosed'],
    "m13_v57_co150_k9_domain_gate.json": ['t01_k9_teeth_all_true', 't02_register_item_closed', 't03_ledger_domain_kinds_expected', 't04_dv_inventory_matches_producer', 't05_inventory_drift_detectable'],
    "m13_v57_co77_closure_declaration_sweep.json": ['l5_packet_citation_resolvable', 'table_row_citation_detected'],
    "m13_v57_co78_layer_role_drift_gate.json": ['control_historical_detected'],
    "m13_v57_co81_project_rules_gate.json": ['hist_netclass_detected', 'hist_rules_detected', 'min_track_width_negative_control', 'positive_control_clean', 'spec_drift_detected'],
    "m13_v57_co84_dru_domain_gate.json": ['clearance_off_detected', 'extra_area_detected', 'no_refclk_exclusion_detected', 'rect_drift_detected'],
    "m13_v57_co95_in4_reachability.json": ['band_point_flagged', 'east_point_passes'],
    "m13_v57_co98_reachability_status_report.json": ['integrity_detects_miscount', 'pip_rejects_bbox_approx'],
}


def watch_paths() -> list:
    """CO-165（t08）：受控 sha 覆盖**全部**规范序会写入的产物（边界 + 全部 co*.json 记录 + 台账/登记簿 + 打样包件）。

    CO-174：补入 `03_stackup` 叠层图 —— fab 包**直接生成**的制造输入件（此前仅被 boundary 表计 sha，
    **未**纳入收敛受控集 ⇒ fab 步静默停写该图时收敛不可见）。文本副本（04/05/06_*，均为已受控源的拷贝）
    不纳入，其一致性由 fab 牙齿 t07/t07b 把关。
    """
    out = [STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md",
           L2 / "input_defect_register_v1.json", L2 / "derived_value_ledger_v1.json",
           K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/MANIFEST.json",
           K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/ORDER_NOTES.md",
           K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/03_stackup/JLC08161H_stackup.svg"]
    out += sorted(STEP2.glob("m13_v57_co*.json"))
    return out


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def _declared_pass_forbidden() -> bool:
    """CO-167（F-6）负控：把白名单项期望 verdict 临时改为 PASS ⇒ 必须返回 expected_verdict_pass_forbidden。"""
    key = "co146_jlc_dfm_gate"
    orig = EXPECTED_NONZERO[key]
    try:
        EXPECTED_NONZERO[key] = {**orig, "verdict": "PASS"}
        return allowlist_decision(key, 1, "", "PASS", True) == "expected_verdict_pass_forbidden"
    finally:
        EXPECTED_NONZERO[key] = orig


def _record_snap(rec_path) -> dict:
    """CO-167（F-2）：捕获记录的产生态（存在性 + mtime_ns + 内容 sha16）。"""
    try:
        st = Path(rec_path).stat()
        return {"exists": True, "mtime_ns": st.st_mtime_ns, "sha": s16(rec_path)}
    except OSError:
        return {"exists": False, "mtime_ns": None, "sha": None}


def record_refreshed(before: dict, after: dict) -> bool:
    """CO-167（F-2）：记录须由**本次执行**产出 —— 以**变更检测**替代绝对时间比较：
    步前不存在，或 mtime_ns / 内容 sha16 任一变化即视为刷新。与时钟回拨/网络盘/异机写入无关，
    ⇒ 崩溃（未重写记录）恒判 `expected_step_record_not_produced`，不可被未来 mtime 伪「新鲜」。"""
    if not after.get("exists"):
        return False
    if not before.get("exists"):
        return True
    return after.get("mtime_ns") != before.get("mtime_ns") or after.get("sha") != before.get("sha")


def _artifact_stamp(p) -> dict | None:
    """CO-172（F-7）：受控产物的**多信号**指纹（mtime_ns + ctime_ns + size + 内容 sha16）。

    缘起（CO-169 单用 mtime_ns 的灵敏度缺口）：① 粗粒度/网络 FS 上同一时刻内重写可能**不前进**；
    ② 某步把 mtime 回写/规范化为定值（utime）而内容已变 ⇒ mtime 不变 ⇒ 被误判「未做事」而假停机；
    ③ mtime 易受系统时钟回拨/异机写入影响。加入 ctime/size/内容指纹后上述三类仍可判「做了事」。
    残余（如实登记）：**字节完全相同**的重写在粗粒度 FS 上仍与 no-op 不可分 —— 该残余只会导致
    **假停机（fail-closed）**，不会造成假通过；且收敛另由「循环至 sha 稳定」判定（R-CO164-1）。
    """
    try:
        st = p.stat()
    except OSError:
        return None
    try:
        sha = s16(p)
    except OSError:
        sha = None
    return {"mtime_ns": st.st_mtime_ns, "ctime_ns": st.st_ctime_ns, "size": st.st_size, "sha16": sha}


def _snap_watched(paths=None) -> dict:
    """CO-169/CO-172/CO-174：产物集 (路径 -> 多信号指纹) 快照。

    `paths=None` ⇒ 全局受控集（收敛 sha 用，R-CO165）；传入步本地主产物集 ⇒ 步本地归因（R-CO174-1）。
    """
    ps = watch_paths() if paths is None else paths
    return {str(p): _artifact_stamp(p) for p in ps}


def step_paths(step: str) -> list:
    """CO-174（R-CO174-1）：该步**主产物集**（步本地归因用；由实测探针钉定，非猜测）。"""
    return [K2 / rel for rel in STEP_ARTIFACTS.get(step, [])]


def step_did_work(before: dict, after: dict) -> bool:
    """CO-169/CO-172：该步须**写出**至少一个受控产物（新增 / 删除 / 任一指纹信号变化）。

    `rc == 0` 本身不证明「做了事」：一个静默返回的步（早退/漏写）会因产物 sha 不变而被
    「sha 稳定 ⇒ 收敛」**背书**（与 CO-164 的教训同族，但故障类是「不崩也不写」）。
    """
    keys = set(before) | set(after)
    return any(after.get(k) != before.get(k) for k in keys)


def zero_rc_class(did_work: bool) -> str:
    """CO-169：非白名单步在 rc==0 时的分类（须真正写出受控产物）。"""
    return "ok" if did_work else "step_wrote_nothing"


def record_json_path(rec_path, keys) -> object:
    """CO-176（G-1）：从记录文件按 keys 逐层取值（缺文件/缺键/不可解析 ⇒ None）。"""
    try:
        node = json.loads(Path(rec_path).read_text(encoding="utf-8"))
    except Exception:
        return None
    for k in keys:
        if isinstance(node, dict) and k in node:
            node = node[k]
        else:
            return None
    return node


def teeth_all_true(node) -> bool | None:
    """CO-176（G-1）：记录内自检牙齿须**全 True**（值为 bool，或为含 `ok` 的 dict）。

    空/形状不明 ⇒ None（**fail-closed**：不可判即不通过）。
    """
    if not isinstance(node, dict) or not node:
        return None
    vals = []
    for v in node.values():
        if isinstance(v, bool):
            vals.append(v)
        elif isinstance(v, dict) and isinstance(v.get("ok"), bool):
            vals.append(v["ok"])
        else:
            return None
    return all(vals)


def _teeth_pin_negative_controls() -> bool:
    """CO-181（F-3）负控（**内存桩件、零落盘**）：pin 命中⇒True；齿集漂移 / 不可解析 / teeth_ok 冒充 ⇒ False。"""
    global step_paths
    _name = sorted(EXPECTED_TEETH)[0]
    _keys = EXPECTED_TEETH[_name]

    class _P:
        suffix = ".json"
        def __init__(self, text):
            self._t, self.name = text, _name
        def exists(self) -> bool:
            return True
        def read_text(self, encoding: str | None = None) -> str:
            if self._t is None:
                raise ValueError("injected unparsable payload")
            return self._t

    orig = step_paths
    try:
        step_paths = lambda step: [_P(json.dumps({"teeth": {k: True for k in _keys}}))]
        ok_hit = step_declared_teeth("__nc__") is True
        step_paths = lambda step: [_P(json.dumps({"teeth": {k: True for k in _keys[:-1]}}))]
        drift = step_declared_teeth("__nc__") is False
        step_paths = lambda step: [_P(None)]
        unparsable = step_declared_teeth("__nc__") is False
        step_paths = lambda step: [_P(json.dumps({"teeth_ok": True, "verdict": "PASS"}))]
        fake = step_declared_teeth("__nc__") is False
    finally:
        step_paths = orig
    return ok_hit and drift and unparsable and fake


def step_declared_teeth(step: str) -> bool | None:
    """CO-180/CO-181：该步**声明产物**中凡含 `teeth` 键者，须机判**全 True**（R-CO180-1）。

    CO-181 加固（F-2/F-3/F-4）：
      ① 声明 json **缺失 / 不可解析 / 非 dict** ⇒ **False**（`不可判一律 fail-closed`，禁静默跳过）；
      ② 齿集须**命中 `EXPECTED_TEETH` pin**（防**静默删齿 / 改名**——判据不得自指）；
      ③ 以 `teeth_ok` 冒充齿（无 `teeth` 布尔齿 dict）⇒ False（R-CO180-2 形状）。
    返回 True = 有声明齿且全 True；None = 无任何声明产物含 teeth（不适用）。
    """
    seen = False
    for p in step_paths(step):
        if getattr(p, "suffix", "") != ".json":
            continue
        if not p.exists():
            return False
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return False
        if not isinstance(d, dict):
            return False
        if "teeth" not in d:
            if "teeth_ok" in d:
                return False
            continue
        seen = True
        if EXPECTED_TEETH.get(p.name) != sorted(d["teeth"]):
            return False
        if teeth_all_true(d["teeth"]) is not True:
            return False
    return True if seen else None


def record_verdict(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")).get("verdict")
    except Exception:
        return None


def allowlist_decision(step: str, rc: int, stderr: str, verdict, record_fresh: bool = True,
                       teeth_ok: bool | None = None) -> str:
    """CO-165 核心判据（纯函数）：
    非白名单步：rc==0 ⇒ ok，否则 unexpected_nonzero；
    白名单步：须 rc≠0 **且** 无 Traceback **且** 记录由**本次执行**产出（mtime 新鲜）
              **且** 记录 verdict == 声明 verdict
              **且** （CO-176 G-1）该步**自检牙齿全 True** ⇒ expected_nonzero；
    其余 ⇒ expected_step_* 失败（**不得把崩溃 / 未产出记录（陈旧 verdict 从盘上读取）/ 错误判决 / 自检失败当预期 FAIL**）。"""
    if step not in EXPECTED_NONZERO:
        if rc != 0:
            return "unexpected_nonzero"
        # CO-180：非白名单步亦须**声明产物内牙齿全 True**（此前只记不判）
        if teeth_ok is False:
            return "step_teeth_failed"
        return "ok"
    exp = EXPECTED_NONZERO[step]
    if rc == 0:
        return "expected_step_returned_zero"
    if "Traceback (most recent call last)" in (stderr or ""):
        return "expected_step_crashed"
    if not record_fresh:
        return "expected_step_record_not_produced"
    # CO-167（F-6）：白名单不得把「成功」当预期 —— 声明的 expected verdict 为 PASS，或记录 verdict 为 PASS，
    # 均与 rc≠0 自相矛盾 ⇒ 一律停机（不得作为「预期 FAIL」放行）。
    if str(exp.get("verdict", "")).upper() == "PASS" or str(verdict or "").upper() == "PASS":
        return "expected_verdict_pass_forbidden"
    if verdict != exp.get("verdict"):
        return "expected_step_verdict_mismatch"
    # CO-176（G-1）：白名单豁免的是 **verdict**，不是该步**自检**；牙齿未全 True（含不可判）⇒ 停机
    if exp.get("teeth_path") and teeth_ok is not True:
        return "expected_step_teeth_failed"
    return "expected_nonzero"


def stable(prev: str, cur: str) -> bool:
    return bool(prev) and prev == cur


BOUNDARY = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"


def boundary_order_steps() -> list:
    """CO-164（t06）：从 boundary 最后一条 R-COxxx-3「规范复现序」行抽取步骤名（防文档序与执行器 ORDER 漂移）。"""
    if not BOUNDARY.exists():
        return []
    _lines = BOUNDARY.read_text(encoding="utf-8").splitlines()
    _idx = [i for i, l in enumerate(_lines) if "规范复现序 =" in l]
    if not _idx:
        return []
    # CO-167（F-1）：若在最后一条可解析序行**之后**仍有其它 `规范复现序` 提及（措辞/格式变更的新式写法），
    # 说明最新序陈述不可解析 ⇒ fail-closed 返回 []（**禁止回落到更旧的序行** ⇒ 防 t06 假通过）。
    if any("规范复现序" in l for l in _lines[_idx[-1] + 1:]):
        return []
    lines = [_lines[_idx[-1]]]
    seg = lines[-1].split("规范复现序 =", 1)[1]
    out = []
    for tok in seg.replace("`", "").replace("**", "").split("→"):
        m = re.match(r"^([a-z0-9_]+)", tok.strip())   # 切掉尾注（如「，循环至 sha 稳定。」）
        t = m.group(1) if m else ""
        if re.match(r"^co\d", t):
            out.append(t)   # 不去重：`co146_boundary_append` 在序内合法出现两次
    return out



_VARISH_NODES = ("Name", "Attribute", "Subscript", "Call", "Compare", "BoolOp", "BinOp",
                 "IfExp", "GeneratorExp", "ListComp", "DictComp", "SetComp")


def teeth_hygiene_scan(src: str) -> dict:
    """CO-183：牙齿卫生静态扫描（AST、**只读**）——
    ① **常量齿**：牙齿值式为纯字面量（无变量/调用/下标）⇒ 恒真/恒假齿候选；
    ② **提前结算**：`all/any(teeth…)` 聚合之后**仍**向同一容器 `teeth[k]=…` 加齿。
    返回 {"n_teeth": int, "constant_teeth": [...], "premature_agg": [...]}。
    """
    tree = ast.parse(src)
    tooth_vars = set()          # {'teeth': <Name>} ⇒ 该 Name 亦为牙齿容器（co81/co84 风格）
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "teeth" and isinstance(v, ast.Name):
                    tooth_vars.add(v.id)
    pairs, stores = [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == "teeth":
                    if isinstance(t.slice, ast.Constant):
                        pairs.append((t.slice.value, n.value)); stores.append(n.lineno)
                elif isinstance(t, ast.Name) and isinstance(n.value, ast.Dict) and (t.id == "teeth" or t.id in tooth_vars):
                    for k, v in zip(n.value.keys, n.value.values):
                        if isinstance(k, ast.Constant):
                            pairs.append((k.value, v))
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "teeth" and isinstance(v, ast.Dict):
                    for k2, v2 in zip(v.keys, v.values):
                        if isinstance(k2, ast.Constant):
                            pairs.append((k2.value, v2))
    constant_teeth = [{"key": k, "expr": ast.unparse(v)[:60]} for k, v in pairs
                      if not ({type(x).__name__ for x in ast.walk(v)} & set(_VARISH_NODES))]
    tooth_ids = {id(v) for _, v in pairs}
    premature_agg = []
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("all", "any")
                and any(isinstance(x, ast.Name) and x.id == "teeth" for x in ast.walk(n))
                and id(n) not in tooth_ids):
            later = [ln for ln in stores if ln > n.lineno]
            if later:
                premature_agg.append({"line": n.lineno, "later_tooth_line": min(later)})
    return {"n_teeth": len(pairs), "constant_teeth": constant_teeth, "premature_agg": premature_agg}


def tool_path(step: str) -> Path | None:
    direct = K2 / "tools" / f"p3_v57_{step}.py"
    if direct.exists():
        return direct
    cands = sorted((K2 / "tools").glob(f"p3_v57_{step}*.py"))
    return cands[0] if len(cands) == 1 else None


def snapshot() -> str:
    h = hashlib.sha256()
    for p in watch_paths():
        h.update(p.read_bytes() if p.exists() else b"<missing>")
    return h.hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="静态体检（不执行、不落盘）")
    ap.add_argument("--max-iter", type=int, default=5)
    a = ap.parse_args(argv)
    checks = {}
    # 静态体检：步骤文件存在 + 可编译 + rc 策略声明齐备
    missing, uncompilable = [], []
    for step in sorted(set(ORDER)):
        p = tool_path(step)
        if p is None:
            missing.append(step); continue
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except SyntaxError as e:
            uncompilable.append(f"{step}: {e}")
    checks["t01_steps_exist"] = not missing
    checks["t02_steps_compile"] = not uncompilable
    checks["t03_expected_nonzero_policy_declared"] = set(EXPECTED_NONZERO) <= set(ORDER)
    checks["t04_unexpected_nonzero_detected"] = (
        allowlist_decision("co78_layer_role_drift_gate", 1, "", None) == "unexpected_nonzero"
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", "PASS") == "ok")
    # CO-165（t07）：白名单步的**伪通过**必须被拒（崩溃 / 意外归零 / verdict 不符 / 缺证据）
    checks["t07_allowlist_evidence_enforced"] = (
        allowlist_decision("co146_jlc_dfm_gate", 1, "Traceback (most recent call last):\n", "FAIL", True) == "expected_step_crashed"
        and allowlist_decision("co146_jlc_dfm_gate", 0, "", "FAIL", True) == "expected_step_returned_zero"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "INDETERMINATE", True) == "expected_step_verdict_mismatch"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "PASS", True) == "expected_verdict_pass_forbidden"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", False) == "expected_step_record_not_produced"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, True) == "expected_nonzero"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "PASS", True) == "expected_verdict_pass_forbidden"
        and all(("verdict" in v and "record" in v) for v in EXPECTED_NONZERO.values())
        and all(str(v.get("verdict", "")).upper() != "PASS" for v in EXPECTED_NONZERO.values())
        # 注入「声明 PASS」的临时白名单项 ⇒ 必须被禁（F-6 声明面）
        and _declared_pass_forbidden())
    # CO-165（t08）：受控 sha 覆盖全部记录类产物（非窄清单）
    _w = [p.as_posix() for p in watch_paths()]
    checks["t08_watch_covers_records"] = (len(_w) >= 20
                                          and any(p.endswith("m13_v57_co106_reference_plane_gate.json") for p in _w)
                                          and any(p.endswith("jlc_package/MANIFEST.json") for p in _w)
                                          # CO-174：fab 直接生成的制造输入件（叠层图）亦须在受控集内
                                          and any(p.endswith("03_stackup/JLC08161H_stackup.svg") for p in _w))
    # CO-167（F-3）：白名单记录必须 ⊆ 受控集（防未来白名单项指向 glob 外件 ⇒ 收敛盲区）
    checks["t09_allowlist_records_watched"] = (
        bool(EXPECTED_NONZERO)
        and {Path(v["record"]).resolve() for v in EXPECTED_NONZERO.values()}
            <= {p.resolve() for p in watch_paths()})
    # CO-167（F-2）：刷新判据为**变更检测**（拒未重写的陈旧记录，含未来 mtime）
    checks["t10_record_refresh_change_detection"] = (
        record_refreshed({"exists": False, "mtime_ns": None, "sha": None}, {"exists": True, "mtime_ns": 5, "sha": "a"})
        and record_refreshed({"exists": True, "mtime_ns": 1, "sha": "a"}, {"exists": True, "mtime_ns": 2, "sha": "a"})
        and not record_refreshed({"exists": True, "mtime_ns": 1, "sha": "a"}, {"exists": True, "mtime_ns": 1, "sha": "a"})
        and not record_refreshed({"exists": True, "mtime_ns": 1, "sha": "a"}, {"exists": False, "mtime_ns": None, "sha": None}))
    # CO-169（G-1）：非白名单步 rc==0 亦须**真正写出**受控产物（禁「静默 no-op 步」被收敛背书）
    checks["t11_step_output_oracle"] = (
        step_did_work({"a": 1}, {"a": 2})                  # mtime 前进 ⇒ 做了事
        and (not step_did_work({"a": 1}, {"a": 1}))        # 零变动 ⇒ 未做事
        and step_did_work({"a": 1}, {"a": 1, "b": 7})      # 新增受控产物
        and step_did_work({"a": 1}, {"a": None})           # 产物被删/失联
        and zero_rc_class(True) == "ok" and zero_rc_class(False) == "step_wrote_nothing")
    # CO-172（F-7）：快照须为**多信号**（mtime 不变而内容/ctime/size 变 ⇒ 仍须判「做了事」）
    _s0 = {"mtime_ns": 1, "ctime_ns": 1, "size": 5, "sha16": "a"}
    checks["t12_watched_snapshot_multisignal"] = (
        step_did_work({"p": _s0}, {"p": {**_s0, "sha16": "b"}})                    # 内容变、mtime 未动
        and step_did_work({"p": _s0}, {"p": {**_s0, "ctime_ns": 9}})              # ctime 前进
        and step_did_work({"p": _s0}, {"p": {**_s0, "size": 6}})                  # size 变
        and not step_did_work({"p": _s0}, {"p": dict(_s0)}))                      # 全同 ⇒ 未做事
    # CO-174（G-1）：每步须声明**主产物集**（步本地归因；禁全局集合代为背书）
    _watch = {p.resolve() for p in watch_paths()}
    checks["t13_step_artifacts_declared"] = (
        set(ORDER) <= set(STEP_ARTIFACTS)
        and all(STEP_ARTIFACTS[s] for s in set(ORDER))
        and all((K2 / rel).resolve() in _watch for s in STEP_ARTIFACTS for rel in STEP_ARTIFACTS[s]))
    # CO-174（G-1）负控：快照**只含**本步声明集 —— 非声明受控件的变动**不得**归因于本步
    _demo = next(s for s in ORDER if len(step_paths(s)) == 1)
    _dp = step_paths(_demo)
    _dps = {str(q) for q in _dp}
    _other = {str(q) for q in watch_paths() if str(q) not in _dps}
    _s0 = {"mtime_ns": 1, "ctime_ns": 1, "size": 5, "sha16": "a"}
    checks["t13b_step_local_attribution"] = (
        bool(_dp) and bool(_other)
        and set(_snap_watched(_dp)) == _dps                                  # 快照仅声明集 ⇒ 无 strays
        and not (set(_snap_watched(_dp)) & _other)
        and step_did_work({_dp[0].as_posix(): _s0}, {_dp[0].as_posix(): {**_s0, "sha16": "b"}})
        and not step_did_work({_dp[0].as_posix(): _s0}, {_dp[0].as_posix(): dict(_s0)}))
    # CO-174（G-1）残余如实登记：共享主产物须**显式枚举**（防静默遗忘；新增共享件即 fail）
    _shared = [rel for s in STEP_ARTIFACTS for rel in STEP_ARTIFACTS[s]]
    _multi = sorted({rel for rel in _shared if _shared.count(rel) > 1})
    checks["t13c_shared_artifact_residual_enumerated"] = (_multi == sorted(SHARED_ARTIFACT_RESIDUAL))
    # CO-176（G-1）：白名单步**自检牙齿**须机判全 True —— 正控/负控/形状不明 fail-closed
    checks["t14_allowlist_teeth_enforced"] = (
        allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True,
                           teeth_all_true({"t01": {"ok": True}})) == "expected_nonzero"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True,
                               teeth_all_true({"t01": {"ok": False}})) == "expected_step_teeth_failed"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True, None) == "expected_step_teeth_failed"
        and all("teeth_path" in v for v in EXPECTED_NONZERO.values())
        and teeth_all_true({"t": True, "u": {"ok": True}}) is True
        and teeth_all_true({"t": True, "u": {"ok": False}}) is False
        and teeth_all_true({}) is None and teeth_all_true({"t": 1}) is None and teeth_all_true("x") is None)
    # CO-180：步骤**声明产物牙齿**须纳入判决（含非白名单步）—— 正控/负控/不适用（None）
    checks["t15_step_declared_teeth_enforced"] = (
        allowlist_decision("co77_closure_declaration_sweep", 0, "", None, True, False) == "step_teeth_failed"
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", None, True, True) == "ok"
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", None, True, None) == "ok"
        and allowlist_decision("co77_closure_declaration_sweep", 1, "", None, True, False) == "unexpected_nonzero"
        # 现状普查：声明产物含 teeth 的步骤须**全为 True**（co78 散文 teeth 之类即在此被抓）
        and step_declared_teeth("co146_jlc_fab_package") is True
        and step_declared_teeth("co146_boundary_append") is None
        and step_declared_teeth("co146_ledger_add") is None
        and sum(1 for s in set(ORDER) if step_declared_teeth(s) is True) >= 13
        and sum(1 for s in set(ORDER) if step_declared_teeth(s) is False) == 0)
    # CO-181（F-3）：齿集 pin 覆盖一致 + fail-closed（不可判/删齿/改名/teeth_ok 冒充一律不通过）
    _decl_teeth = set()
    for _s in set(ORDER):
        for _r in STEP_ARTIFACTS.get(_s, []):
            if not str(_r).endswith(".json"):
                continue
            try:
                _d = json.loads((K2 / _r).read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(_d, dict) and "teeth" in _d:
                _decl_teeth.add(Path(_r).name)
    checks["t16_teeth_set_pinned"] = (
        set(EXPECTED_TEETH) == _decl_teeth
        and all(step_declared_teeth(s) is not False for s in set(ORDER))
        and step_declared_teeth("__UNKNOWN__") is None
        and _teeth_pin_negative_controls())
    # CO-182（R-CO182-1）：boundary citation 扫描步须**紧跟**boundary 刷新步（消除一轮 pin 滞后）
    _gi = [i for i, s in enumerate(ORDER) if s in BOUNDARY_SCAN_GUARDED]
    checks["t17_boundary_scan_follows_refresh"] = (
        len(_gi) == len(BOUNDARY_SCAN_GUARDED)
        and all(i > 0 and ORDER[i - 1] == BOUNDARY_REFRESH_STEP for i in _gi))
    # CO-183（R-CO183-1）：牙齿卫生**棘轮**（常量齿 / 提前结算）—— 合成正负控 + 现行零违规 + 齿数下限
    _p_good = 'def f(d):\n    teeth={}\n    teeth["t01"]=d["a"]>0\n    teeth["t02"]=all(isinstance(v,bool) for v in teeth.values())\n    return all(teeth.values())\n'
    _p_const = 'def f(d):\n    teeth={"t01":True,"t02":d["a"]>0}\n    return all(teeth.values())\n'
    _p_prem = 'def f(d):\n    teeth={"t01":d["a"]>0}\n    ok=all(teeth.values())\n    teeth["t02"]=d["b"]>0\n    return ok\n'
    _p_foreign = 'def f(c):\n    teeth=c.get("teeth",{})\n    ok=all(teeth.get(k) is True for k in ("a",))\n    rec={"teeth":{"t01":ok}}\n    return rec\n'
    _g, _c, _m, _f = (teeth_hygiene_scan(_p_good), teeth_hygiene_scan(_p_const),
                      teeth_hygiene_scan(_p_prem), teeth_hygiene_scan(_p_foreign))
    _scan_ok = (not _g["constant_teeth"] and not _g["premature_agg"]
                and len(_c["constant_teeth"]) == 1 and not _c["premature_agg"]
                and len(_m["premature_agg"]) == 1 and not _f["constant_teeth"] and not _f["premature_agg"])
    _own = {}
    for _s in set(ORDER):
        for _r in STEP_ARTIFACTS.get(_s, []):
            if Path(_r).name in EXPECTED_TEETH:
                _tp = tool_path(_s)
                if _tp is not None:
                    _own[Path(_r).name] = _tp
    _live = [teeth_hygiene_scan(q.read_text(encoding="utf-8")) for q in set(_own.values())]
    checks["t18_teeth_hygiene_ratchet"] = (
        _scan_ok and set(_own) == set(EXPECTED_TEETH)
        and sum(v["n_teeth"] for v in _live) >= 100
        and all(not v["constant_teeth"] and not v["premature_agg"] for v in _live))
    checks["t05_stability_oracle"] = (stable("x", "x") and not stable("x", "y") and not stable("", ""))
    # CO-164（t06）：执行器 ORDER 必须与 boundary 规范复现序**有序一致**（文档↔执行器防漂移）
    _bdy = boundary_order_steps()
    checks["t06_order_matches_boundary"] = bool(_bdy) and _bdy == ORDER
    static_ok = all(checks.values())
    if a.check:
        print(json.dumps({"mode": "check", "checks": checks, "missing": missing,
                          "uncompilable": uncompilable, "ok": static_ok}, ensure_ascii=False, indent=1))
        return 0 if static_ok else 1
    if not static_ok:
        print(json.dumps({"mode": "run", "aborted": "static_precheck_failed", "checks": checks,
                          "missing": missing, "uncompilable": uncompilable}, ensure_ascii=False, indent=1))
        return 1
    # ── 执行：每轮逐步跑，rc 不合规立即停机 ─────────────────────────────────
    iterations, abort = [], None
    prev = ""
    converged = False
    for it in range(1, a.max_iter + 1):
        rcs, unexpected = {}, None
        for step in ORDER:
            p = tool_path(step)
            _exp = EXPECTED_NONZERO.get(step) or {}
            _before = _record_snap(_exp["record"]) if _exp.get("record") else None
            # CO-174（G-1）：did_work 归因**仅限本步主产物集**（禁全局集合代为背书）
            _decl_set = {str(q) for q in step_paths(step)}
            _ball = _snap_watched()                                            # 全局：仅用于 stray 证据
            _w_before = {k: _ball.get(k) for k in _decl_set}
            r = subprocess.run([str(PY), str(p)], cwd=K2, capture_output=True, text=True)
            _aall = _snap_watched()
            _w_after = {k: _aall.get(k) for k in _decl_set}
            _did = step_did_work(_w_before, _w_after)                          # 步本地归因（CO-174）
            # CO-167（F-2）：变更检测（非绝对 mtime）
            _fresh = record_refreshed(_before, _record_snap(_exp["record"])) if _exp.get("record") else True
            # CO-176（G-1）：白名单步**自检牙齿**须机判全 True；CO-180：**全部步骤**的**声明产物牙齿**亦然
            _tcand = []
            if _exp.get("teeth_path"):
                _tcand.append(teeth_all_true(record_json_path(_exp["record"], _exp["teeth_path"])))
            _tcand.append(step_declared_teeth(step))
            _tcand = [c for c in _tcand if c is not None]
            _teeth_ok = all(_tcand) if _tcand else None
            cls = allowlist_decision(step, r.returncode, r.stderr, record_verdict(_exp.get("record")),
                                     _fresh, _teeth_ok)
            if cls == "ok" and not _did:
                cls = zero_rc_class(False)     # CO-169（G-1）：rc==0 但未写出任何受控产物 ⇒ 立即停机
            rcs[step] = {"rc": r.returncode, "class": cls, "did_work": _did,
                         "declared_changed": sorted(Path(k).relative_to(K2).as_posix()
                                                    for k in _decl_set if _w_before.get(k) != _w_after.get(k)),
                         "stray_changed": sorted(Path(k).relative_to(K2).as_posix()
                                                 for k in set(_ball) | set(_aall)
                                                 if k not in _decl_set and _ball.get(k) != _aall.get(k))}
            if cls not in ("ok", "expected_nonzero"):
                unexpected = {"step": step, "rc": r.returncode, "class": cls,
                              "stderr_tail": (r.stderr or "")[-600:]}
                break
        cur = snapshot()
        iterations.append({"iter": it, "rcs": rcs, "sha": cur, "unexpected": unexpected})
        if unexpected:
            abort = unexpected
            break
        if stable(prev, cur):
            converged = True
            break
        prev = cur
    report = {"artifact": "m13_v57_co164_order_runner_report", "schema": 1, "revision": "CO-183.1",
              "nature": "规范复现序机判执行器（rc 策略 + 真收敛判定）；报告落 .archer_tmp/ 且**不被 boundary 引用**（避免不动点）",
              "order": ORDER, "expected_nonzero": EXPECTED_NONZERO,
              "checks": checks, "iterations": iterations, "abort": abort, "converged": converged,
              "watched": [str(p.relative_to(K2)) for p in watch_paths()],
              "redline": "只读工具源；执行序内写记录/边界（即规范序本身）；本报告不参与 pin 表。"}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"mode": "run", "converged": converged, "abort": abort,
                      "iterations": len(iterations), "checks": checks,
                      "report": str(REPORT.relative_to(K2))}, ensure_ascii=False, indent=1))
    return 0 if (converged and not abort) else 1


if __name__ == "__main__":
    sys.exit(main())
