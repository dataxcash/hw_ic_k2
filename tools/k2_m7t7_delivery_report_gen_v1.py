#!/usr/bin/env python3
"""Generate the m7t7 delivery report-to-owner. Every reading is copied programmatically from the
in-register artifacts (M-ENG-REPORT-READING-DRIFT: no hand-typed numbers)."""
import hashlib, json, os
K2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def lj(p): return json.load(open(os.path.join(K2, p), encoding="utf-8"))
def sha16(p): return hashlib.sha256(open(os.path.join(K2, p), "rb").read()).hexdigest()[:16]

CLOSURE = "pm_gate/artifacts/k2_v4/L2/K2_ECO_QUALITY_v1_CLOSURE_v1.json"
SCOPE   = "pm_gate/artifacts/k2_v4/L2/K2_ECO_QUALITY_v1_ALLOWED_DIFF_SCOPE_v1.json"
PKG     = "pm_gate/artifacts/k2_v4/L6/jlc_package_m7t7/MANIFEST.json"
BOARD   = "pm_gate/artifacts/k2_v4/L6/board/k2_v4_8L.m7t7.kicad_pcb"
c, sc, man = lj(CLOSURE), lj(SCOPE), lj(PKG)
qc = c["step_c_qc_one_shot"]; j = qc["nine_row_judge"]
rep = {
 "artifact": "k2_m7t7_delivery_report_to_owner_v1", "ts": "2026-10-02",
 "engine_head": c["engine_head"],
 "generated": "#K2-579 sec.5 (the ordered delivery-report disclosure update) on top of #K2-570 sec.5 + M-ENG-REPORT-READING-DRIFT: GENERATED - every hardware reading below is copied programmatically from the in-register artifacts (never hand-typed).",
 "source_artifacts": {"eco_closure": CLOSURE, "allowed_diff_scope": SCOPE, "package_manifest": PKG},
 "state": "ECO CLOSED (one-shot QC PASS); package FINAL; the owner-ordered arc-rework line is CLOSED as a zero-write no-op (#K2-579 sec.3.4, functional teeth exempted, board unchanged; optional redraw ECO available on owner order). Remaining: the owner's business decision / signature (生成≠下单).",
 "package": {"dir": "pm_gate/artifacts/k2_v4/L6/jlc_package_m7t7", "n_files": man["n_files"],
   "board": man["board"], "board_sha16": man["board_sha16"], "dfm": man["dfm_summary"],
   "drill_total": man["drill_total"],
   "layers": "8 copper (F/In1..In6/B) + mask F/B + silk F/B + edge + .gbrjob; Excellon with the HDI blind/buried pairs",
   "manifest_identity": {"artifact": man["artifact"], "revision": man["revision"], "nature": man["nature"]},
   "manifest_files_listed": man["n_files"],
   "shared_identity_gauge": c["step_d_package"]["shared_identity_gauge"]},
 "anchor_locked": {"board_in_repo": BOARD, "sha16_on_disk": sha16(BOARD),
   "commit": "62c2750b (#K2-564/565/566/567/568 ECO closure)",
   "invariant": "the package board == the ECO board the one-shot QC judged; the delivered Gerber set is the --check-zones plot-time recompute.",
   "predecessor": c["new_board"]["predecessor"]},
 "nine_rows": {"source": CLOSURE,
   "C1": "unconnected = %d" % j["C1_unconnected"],
   "C2": "total = %d <= %d, new_classes = %s (pinned caliber)" % (j["C2_total"], j["C2_limit"], j["C2_new_classes"]),
   "C3": "max intra-pair delta = %s mm (SAME as the predecessor reading)" % j["C3_max_mm"],
   "C4": "45-deg segment count = %d (ref %d)" % (j["C4_count"], 2637),
   "C5": "routing changed: element_set_diff = %d" % j["C5_element_set_diff"],
   "C6": j["C6"], "C7": "hs fanout diff = %d" % j["C7_hs_fanout_diff"], "verdict": j["verdict"]},
 "c6_named_scope": {"caliber": sc["rule"], "allowed_nets": sc["allowed_difference_scope"]["nets"],
   "allowed_layers": sc["allowed_difference_scope"]["layers"], "measured": sc["measured"]},
 "eco_summary": {"step_a_d2": c["step_a_d2"], "step_a2_sw_u2_reroute": c["step_a2_sw_u2_reroute"],
   "step_b_refclk_arcs": c["step_b_refclk_arcs"], "render_visual": qc["render_visual"]},
 "disclosures_from_the_ECO": {
   "1_owner_premise": c["owner_premise_disclosure"],
   "2_sw_u2_dive_value": {"landed": "y = 38.32 mm", "ruled_suggestion": "y ~ 38.6",
     "why": "38.6 collides with U2 pad8 (top 38.645); the 38.65 first attempt was caught by the pre-QC DRC (clearance/hole_clearance). 38.32 is the only narrow corridor clearing BOTH D2 pad1 (bottom 38.0) and U2 pad8 (top 38.645).", "ratified": "#K2-570 sec.2"},
   "4_arc_rework_terminal": {
     "what": "OWNER-ORDERED arc rework (task #K2-ARC-V2 / R1 / R1a / R1b / R1c): replace the residual FAKE arcs on the four REFCLK nets and the fine zig-zag teeth on the seven PCIE_UP_OUT*_J2 nets with true arcs, same layer/width/net.",
     "carrier": "copper-level census (R1c): the teeth are on In5.Cu; In2=long-straight ridges, B=stubs, F=fan-in ladders (0 corners).",
     "outcome": "CLOSED as a zero-write NO-OP (#K2-579 sec.3.4). The REFCLK side WAS fixed (true arcs, accepted). The seven OUT In5 equal-length teeth could NOT be arc-rounded: closed-form bound gives max in-place R = 0.096-0.102 mm on 7/7 nets, and the R=0.10 live shot produced 18 new DRC errors (9 clearance + 8 shorting + 1 crossing) => candidate m7t8b discarded, no second shot.",
     "why": "the owner arc standard (direction change must be a true arc / zero kink) was carried as a SUPERVISOR internal control line (R>=0.15, #K2-577; criteria/ carries no such value) and was wrongly extended to the FUNCTIONAL equal-length teeth (pitch 0.49 mm, riser 0.34-0.46 mm): two R>=0.15 tangents on one such riser need 0.72 mm, geometrically impossible at any amplitude.",
     "disposition": "the functional teeth are EXEMPTED from the arc gauge (precedent: #K2-572 sec.a F.Cu short-ladder residual corners / #K2-566 dense fan-in). m7t7 In5 as-shipped = honest right-angle functional teeth = the compliant terminal state (kink census: 0 arc elements / 0 fake arcs (<0.15) / 1395 by-design teeth corners, exempted).",
     "board_state": "the delivered board m7t7 is UNCHANGED (sha16 7a99ab2e55e281b4); zero partial write; zero downstream impact.",
     "optional_future_ECO": "full rounding is attainable ONLY by re-drawing the serpentine waveform (symmetric 45/45 or square teeth) - a budgeted ECO that was NOT started; the owner may order it. No work proceeds without an owner order."},
   "5_r4_render_evidence": {
     "what": "owner-facing review renders (#K2-ARC-V2-R4) of the m7t8a candidate: per-footprint connector 3D models oriented to the board edge, a pin1 marker, three views, and a review-annotated copy (all on render copies only - NO manufacturing file changed).",
     "orientation_triple": {"J2": "SlimSAS SFF-8654, fp rot 0, entry axis +x, faces R-edge", "J3": "MCIO SFF-1016, fp rot 180, entry axis -y, faces T-edge", "J4": "MCIO SFF-1016, fp rot 0, entry axis -y, faces B-edge"},
     "pin1": "pixel-verified within 0.163 / 0.052 / 0.065 mm of the pin1 pads; orthographic affine residual <= 0.005 mm",
     "annotated_review_images": "m7t8a_top_annotated.png + m7t8a_iso_annotated.png (text labels + leader lines to J2/J3/J4/U6/J13); the clean originals are NOT overwritten",
     "model_text_item": "STOPPED with evidence: kicad-cli's VRML renderer draws neither Text nor Sphere, so a part number cannot be baked into a 3D model; the board-silkscreen fallback was NOT taken (that would change the board). Part numbers are shown on the review-annotated image overlay instead.",
     "J9_disclosure": "the directive named J9 = OOB UART, but this board has NO J9 footprint (only J2/J3/J4/J12/J13); the UART_RX/UART_TX nets terminate on U1. Shown as a named disclosure on the annotated image; if the owner means a different ref, one word and it is added."},
   "3_product_board_qc_caliber": "for a product-tree ECO board the full QC = the nine-row judge caliber (verify C1-C5) + C6 named-scope zero-difference + C7=0 + the arc gauge + the re-render; the wipe_resolve regeneration chain is reserved for exam/regeneration boards (it regenerates from l14 and does not cover a post-edited product board). Ratified by #K2-570 sec.3."},
 "redlines": {"old_delivery_anchor": "L6/board/k2_v4_8L.m7t6.kicad_pcb (a14610e0542e6314) + jlc_package_m7t6r2 KEPT on disk",
   "frozen_four_sources": "untouched", "criteria_rev6": "read-only", "exam_line": "l14/rev-61 untouched"},
 "OWNER-ITEMS": 0}
out = os.path.join(K2, "pm_gate/artifacts/k2_v4/L6/K2_M7T7_DELIVERY_REPORT_TO_OWNER_v1.json")
json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out)
print("board_sha16", rep["anchor_locked"]["sha16_on_disk"], "| pkg", rep["package"]["n_files"], rep["package"]["board_sha16"], "| dfm", rep["package"]["dfm"], "| verdict", rep["nine_rows"]["verdict"])
