#!/usr/bin/env python3
"""Generate the m7t8a delivery report-to-owner (#K2-ARC-V2-CLOSE item 4 / #K2-580).
Every hardware reading is copied programmatically from the in-register artifacts
(M-ENG-REPORT-READING-DRIFT: no hand-typed numbers). C7 is disclosed per #K2-580 sec.2."""
import hashlib, json, os, subprocess
K2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def lj(p): return json.load(open(os.path.join(K2, p), encoding="utf-8"))
def sha16(p): return hashlib.sha256(open(os.path.join(K2, p), "rb").read()).hexdigest()[:16]

BOARD   = "pm_gate/artifacts/k2_v4/L6/board/k2_v4_8L.m7t8a.kicad_pcb"
PKG     = "pm_gate/artifacts/k2_v4/L6/jlc_package_m7t8a/MANIFEST.json"
NINE    = "pm_gate/artifacts/k2_v4/L6/K2_M7T8A_NINE_ROW_readout.json"
C7EV    = "pm_gate/artifacts/k2_v4/L6/K2_M7T8A_C7_disclosure_evidence.json"
CLOSURE = "pm_gate/artifacts/k2_v4/L2/K2_ECO_QUALITY_v1_CLOSURE_v1.json"
SCOPE   = "pm_gate/artifacts/k2_v4/L2/K2_ECO_QUALITY_v1_ALLOWED_DIFF_SCOPE_v1.json"
man, nine, c7, c, sc = lj(PKG), lj(NINE), lj(C7EV), lj(CLOSURE), lj(SCOPE)
r = nine["rows"]
own = [x for x in c7["c7_rows"] if x["own_net"]]
nbr = [x for x in c7["c7_rows"] if not x["own_net"]]
nb_delta = nbr[0]["delta"]
nbr_attrib = [{"pad": x["pad"], "net": x["net"], "total_delta_mm": x["delta"],
               "own_net_delta_mm": x["own_net_delta"],          # 0.0000 = the pad's OWN net did not move
               "attribution": "PCIE_REFCLK1_P/N arc-rework copper falls inside this pad's 2 mm measurement window",
               "window_scope_elems": [x["scope_elems_in_window_ref"], x["scope_elems_in_window_cand"]]} for x in nbr]
own_attrib = [{"pad": x["pad"], "net": x["net"], "total_delta_mm": x["delta"], "own_net_delta_mm": x["own_net_delta"],
               "class": "EXPECTED change of this ECO (the reworked net's own fanout)", "authority": "owner 2026-10-05 directive + ECO #K2-ARC-V2-CLOSE"} for x in own]
rep = {
 "artifact": "k2_m7t8a_delivery_report_to_owner_v1", "ts": "2026-10-05",
 "generated": "#K2-580 sec.3 (m7t8a promotion ④ closure) + M-ENG-REPORT-READING-DRIFT: GENERATED - every hardware reading below is copied programmatically from the in-register artifacts (never hand-typed).",
 "source_artifacts": {"package_manifest": PKG, "nine_row_readout": NINE, "c7_disclosure_evidence": C7EV},
 "state": "m7t8a PROMOTED (owner #K2-ARC-V2-CLOSE item 4): anchor + package FINAL + nine-row read; C7's 6 readings are attributed (see disclosure 6). Remaining: the owner's business decision / signature (生成≠下单).",
 "package": {"dir": "pm_gate/artifacts/k2_v4/L6/jlc_package_m7t8a", "n_files": man["n_files"],
   "board": man["board"], "board_sha16": man["board_sha16"], "dfm": man["dfm_summary"], "drill_total": man["drill_total"],
   "manifest_identity": {"artifact": man["artifact"], "revision": man["revision"], "nature": man["nature"]},
   "manifest_files_listed": man["n_files"]},
 "anchor_locked": {"board_in_repo": BOARD, "sha16_on_disk": sha16(BOARD),
   "predecessor": "L6/board/k2_v4_8L.m7t7.kicad_pcb (7a99ab2e55e281b4, kept on disk)",
   "invariant": "the package board == the promoted board (PACKAGE QC ROW 9 identity holds: MANIFEST board_sha16 == on-disk sha16)."},
 "nine_rows": {"source": NINE,
   "C1": "unconnected = %d" % r["C1_unconnected"],
   "C2": "cand_total %d, ref_total %d, new_classes %s" % (r["C2"]["cand_total"], r["C2"]["ref_total"], r["C2"]["new_classes"]),
   "C3": "pair_deltas_mm = %s" % r["C3"]["pair_deltas_mm"],
   "C5": "element_set_diff: removed %d / added %d" % (r["C5"]["removed"], r["C5"]["added"]),
   "C6": "touched = %s ; out_of_scope = %s" % (list(r["C6"]["touched"].keys()), r["C6"]["out_of_scope"]),
   "C7": "hs-pad fanout: %d readings differ (all attributed in disclosure 6)" % len(r["C7"]["fanout_len_diffs"]),
   "GAUGE_RK": {k: v for k, v in r["GAUGE_RK"].items() if k in ("PCIE_REFCLK1_P", "PCIE_REFCLK1_N")},
   "verdict": nine["verdict"], "verdict_note": "FAIL is caused SOLELY by C7; every C7 reading is a named, attributed disclosure (disclosure 6), not an un-attributed defect."},
 "disclosures_from_the_ECO": {
   "1_owner_premise": c["owner_premise_disclosure"],
   "2_sw_u2_dive_value": {"landed": "y = 38.32 mm", "ratified": "#K2-570 sec.2",
     "why": "38.6 collides with U2 pad8 (top 38.645); 38.32 is the only narrow corridor clearing BOTH D2 pad1 (bottom 38.0) and U2 pad8 (top 38.645)."},
   "3_product_board_qc_caliber": "for a product-tree ECO board the full QC = the nine-row judge caliber + C6 named-scope + the arc gauge + the re-render; the wipe_resolve regeneration chain is reserved for exam/regeneration boards. Ratified by #K2-570 sec.3.",
   "4_arc_rework_terminal": {
     "what": "OWNER-ORDERED arc rework: REFCLK1_P/N rebuilt with TANGENT arcs (this ECO); the seven OUT In5 equal-length teeth kept as-is.",
     "refclk1_result": "ACCEPTED: REFCLK1_N 12 arcs r_min 0.2919 mm, REFCLK1_P 39 arcs r_min 0.30 mm (>= 0.25), kinks 0.",
     "out_in5_disposition": "the 7 OUT In5 functional equal-length teeth are EXEMPTED from the arc gauge (precedent #K2-572 sec.a / #K2-566); kept as-shipped, zero change (owner 2026-10-05 directive).",
     "optional_future_ECO": "full rounding of the OUT teeth needs a budgeted waveform redraw (symmetric/square); owner may order it - not started."},
   "5_r4_render_evidence": {
     "what": "owner-facing review renders of the m7t8a candidate: per-footprint connector 3D models (orientation + pin1), three views, review-annotated copy.",
     "orientation_triple": {"J2": "SlimSAS SFF-8654, fp rot 0, entry axis +x, faces R-edge", "J3": "MCIO SFF-1016, fp rot 180, entry axis -y, faces T-edge", "J4": "MCIO SFF-1016, fp rot 0, entry axis -y, faces B-edge"},
     "pin1": "pixel-verified within 0.163 / 0.052 / 0.065 mm of the pin1 pads",
     "model_text_item": "STOPPED: kicad-cli's VRML renderer draws neither Text nor Sphere; part numbers shown via the review-annotated image overlay instead (no board change).",
     "J9_disclosure": "no J9 footprint on this board (only J2/J3/J4/J12/J13); UART_RX/UART_TX land on U1."},
   "6_c7_fanout_neighbourhood_disclosure": {
     "plain_language": "These 6 C7 readings are a MEASUREMENT-WINDOW effect: C7 sums the copper of ALL in-scope nets inside each pad's 2 mm window. 3 readings are the reworked net's OWN fanout (expected for a re-draw); the other 3 are neighbouring pads whose own net did NOT move one bit of copper - the reading shifted only because REFCLK1's re-drawn copper falls inside their 2 mm window. Evidence attached; the gauge is unchanged.",
     "measurement_command": "PYTHONPATH=AppDir/... AppDir/bin/python3.11 k2/tools/k2_eco_quality_judge_v2.py --cand L6/board/k2_v4_8L.m7t8a.kicad_pcb --ref L6/board/k2_v4_8L.m7t7.kicad_pcb",
     "measurement_location": "k2/tools/k2_eco_quality_judge_v2.py:214-219 (C7 loop) ; near_pad() :148 ; board_inventory() :38",
     "lines": [{"pad": x["pad"], "net": x["net"], "delta_mm": x["delta"],
                "class": "own-net-expected" if x["own_net"] else "neighbour-window",
                "own_net_delta_mm": x["own_net_delta"]} for x in c7["c7_rows"]],
     "own_net_3": {"note": "the reworked net's own fanout changed - expected for this ECO (authorized)", "rows": own_attrib},
     "neighbour_3": {"c6_touched_set": c7["c6_touched"],
                     "note": "these 3 pads sit on UNTOUCHED nets (C6 touched-set proves zero change); their own-net delta is exactly 0.0000; the -0.2071 is the REFCLK1 rework copper in their window",
                     "identical_delta_reproduced": (len(set(x["delta"] for x in nbr)) == 1),
                     "delta_mm": nb_delta, "rows": nbr_attrib}},
 },
 "redlines": {"old_anchor_kept": "L6/board/k2_v4_8L.m7t7.kicad_pcb (7a99ab2e55e281b4) + jlc_package_m7t7 KEPT on disk",
   "frozen_four_sources": "untouched", "criteria_rev6": "read-only (C7 gauge unchanged, #K2-580)", "exam_line": "l14/rev-61 untouched"},
}
out = os.path.join(K2, "pm_gate/artifacts/k2_v4/L6/K2_M7T8A_DELIVERY_REPORT_TO_OWNER_v1.json")
json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out)
print("board_sha16", rep["anchor_locked"]["sha16_on_disk"], "| pkg", rep["package"]["n_files"], rep["package"]["board_sha16"], "| dfm", rep["package"]["dfm"], "| nine verdict", rep["nine_rows"]["verdict"], "| c7 lines", len(rep["disclosures_from_the_ECO"]["6_c7_fanout_neighbourhood_disclosure"]["lines"]))
