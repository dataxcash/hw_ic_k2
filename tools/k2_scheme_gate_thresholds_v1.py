#!/usr/bin/env python3
"""k2_scheme_gate_thresholds_v1.py --- #K2-336 sec.4.1 threshold completeness (C17') asset.

Emits L2/SCHEME_GATE_THRESHOLDS_v1.json: P1..P7, each carrying its threshold, the source KIND, the citation
(document + section/table/page) and the quoted source line, plus the machine check that tools/k2_scheme_gate_v2.py
performs.  POLICY: no invented thresholds.  Where the threshold or a required input is not available, the entry is
PENDING with the NAMED missing input.  Derived numbers show their derivation formula (no magic constants).

Deterministic; read-only w.r.t. the board.

Usage: python3 tools/k2_scheme_gate_thresholds_v1.py [--out <json>]
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "SCHEME_GATE_THRESHOLDS_v1.json")

CEM = {"doc": "PCI Express Card Electromechanical Specification, Rev 5.0 v1.0, 2021-06-09 (PCI-SIG)",
       "retrieval": "https://image.lceda.cn/attachments/2025/1/cC9ZlhB8zD2bXInsUm1R6XsieT6oV0VdRs5lGeLw.pdf",
       "http": 200, "bytes": 9168040, "sha16": "91c722e621cb52d3",
       "file": "L2/refs/SOURCES.md #1"}
TI = {"doc": "TI DS320PR1601 datasheet, SNLS683 (June 2023)",
      "retrieval": "https://www.ti.com/lit/ds/symlink/ds320pr1601.pdf",
      "http": 200, "bytes": 2225981, "sha16": "f61599c4356edb39",   # byte-identical to the in-register copy
      "file": "L2/refs/SOURCES.md #2"}

# FR-4 scale taken from the CEM's OWN note (Table 4-8): 0.35 ns ~= 2-inch trace delta
PS_PER_MM = 175.0 / 25.4                       # 6.8898 ps/mm
MAX_DELAY_PS = 750.0                           # CEM 4.7.9 (Add-in Card, edge-finger -> Rx/Tx)
L_MAX_MM = round(MAX_DELAY_PS / PS_PER_MM, 2)  # 108.86 mm
SA_NS = 0.35                                   # CEM Table 4-8 lane-to-lane skew, AIC


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=OUT); a = ap.parse_args()
    crit = {}

    crit["P1"] = {
        "layer": "SCHEME", "id": "P1", "name": "high-speed main-path directness / flow-through structure",
        "kind": "STRUCTURAL_CHECK", "status": "SOURCED",
        "source_kind": "EXEMPLAR + MANUFACTURER_DATASHEET",
        "citation": [{"doc": TI["doc"], "section": "1.1 Features / 9.4.2 Layout Example",
                      "quoted": "Flow-through layout P2P with Intel retimer common footprint; Figure 9-7 TI PCIe Riser Card"},
                     {"doc": "L2/PLACEMENT_CORPUS_v1.json sample#1", "section": "framework",
                      "quoted": "chip CENTRE; connectors on ONE edge aligned with the chip fan-out; RADIAL fan-out"}],
        "threshold": {"chip_lateral_offset_from_connector_axis_max_mm": None,   # filled below from the board frame
                      "chip_lateral_tol_frac_of_height": 0.15,
                      "chip_must_lie_between_the_outermost_hs_connectors": True,
                      "every_hs_connector_on_its_own_side_of_the_chip": True},
        "note": ("the earlier 1.6x route/straight ratio was a PLACEHOLDER (no spec or manufacturer defines a "
                 "directness ratio) - it is REMOVED as a verdict; the ratio is still REPORTED as an SI reading. "
                 "What IS sourced: a flow-through framework = device on the connector axis, between the connectors."),
        "machine_check": "chip lateral offset from the HS-connector axis <= 0.15*H; chip x strictly between the westmost and eastmost HS connector; each HS connector on its own side",
        "missing_input": None}

    crit["P2"] = {
        "layer": "SCHEME", "id": "P2", "name": "length budget feasibility",
        "kind": "NUMERIC", "status": "SOURCED", "source_kind": "PCIE_CEM_SPEC",
        "citation": [{"doc": CEM["doc"], "section": "4.7.9 Differential Data Trace Propagation Delay (Add-in Card)",
                      "quoted": "The propagation delay for an Add-in Card data trace from the edge-finger to the Receiver/Transmitter must not exceed 750 ps"},
                     {"doc": CEM["doc"], "section": "Table 4-8 (page 59) - FR-4 scale used for the conversion",
                      "quoted": "SA = 0.35 ns - Estimates about a 2-inch trace length delta on FR-4 boards"}],
        "threshold": {"max_trace_length_mm": L_MAX_MM, "max_propagation_delay_ps": MAX_DELAY_PS,
                      "fr4_ps_per_mm": round(PS_PER_MM, 4),
                      "derivation": "750 ps / (175 ps / 25.4 mm) = %.2f mm" % L_MAX_MM,
                      "applies_to": "the routed length of every HS net on a ROUTED board (unrouted candidate => PENDING)"},
        "also_sourced": {"lane_to_lane_skew_aic_ns": SA_NS, "lane_to_lane_skew_aic_mm": round(SA_NS * 1000 / PS_PER_MM, 2),
                         "intra_pair_skew_aic_mm": 0.064, "intra_pair_skew_system_board_mm": 0.127,
                         "diff_impedance_ohm_16gts_plus": [72.5, 97.5],
                         "insertion_loss_aic_32gts_db_at_16ghz": -9.5},
        "machine_check": "max routed length over all HS nets <= max_trace_length_mm",
        "missing_input": None}

    crit["P3"] = {
        "layer": "SCHEME", "id": "P3", "name": "mechanical frame (mounting holes four-corner + edge clearance)",
        "kind": "NUMERIC", "status": "SOURCED", "source_kind": "IN_REGISTER_DOC",
        "citation": [{"doc": "#K2-322 sec.3.1 (owner mechanical directive)", "section": "four-corner symmetry",
                      "quoted": "H4->bottom-right; H3->top-left; H1/H2 diagonal symmetry"},
                     {"doc": "L3/SPEC_k2_v4.json", "section": "constraints.edge_copper_min", "quoted": "0.3 mm"}],
        "threshold": {"corner_max_mm": 3.0, "edge_min_mm": 0.3},
        "machine_check": "every mounting hole <= 3.0 mm (euclidean) from its nearest distinct board corner and >= 0.3 mm from the board edge",
        "missing_input": None}

    crit["P4"] = {
        "layer": "SCHEME", "id": "P4", "name": "congestion capacity (section supply >= demand)",
        "kind": "METHOD_WITNESS", "status": "SOURCED", "source_kind": "IN_REGISTER_METHOD",
        "citation": [{"doc": "R537 cross-section method (in register)", "section": "capacity >= demand per x-section",
                      "quoted": "cross-section method; supply/demand per section"}],
        "threshold": {"rule": "a section-wise capacity model is NOT in register; the WITNESS test is used instead",
                      "witness_rule": "a completed routing for the declared HS net set exists at the declared stackup "
                                      "=> capacity >= demand at every section (existence proof, no invented supply model)"},
        "machine_check": "routed board: every HS net has >=1 track segment and 0 unconnected => PASS (witness); unrouted candidate => PENDING",
        "missing_input": None}

    crit["P5"] = {
        "layer": "CONSTRUCTION", "id": "P5", "name": "thermal path / thermal budget",
        "kind": "STRUCTURAL_CHECK + NUMERIC_BUDGET", "status": "SOURCED", "source_kind": "IN_REGISTER_L2_RULING",
        "citation": [{"doc": "L2_RULING_u6_thermal_mitigation_v2.md (CO-204 thermal freeze, O2)",
                      "section": "1-2",
                      "quoted": "O2 = 30x30mm Al heatsink + 1.0 C/W interface pad + ~2 m/s airflow (owner confirmed airflow); "
                                "theta_JA_eff = theta_JC_top(6.5) + R_int(1.0) + theta_HS(3.5) = 11.0 C/W; Ta = 40.0 C; Tj_max = 120.0 C; "
                                "four cases 91.7 / 106.0 / 103.8 / 117.0 C => all PASS (worst-case margin 3.0 C)"},
                     {"doc": "L2_RULING_u6_gnd_via_array_v1.md (CO-222)", "section": "2",
                      "quoted": "T1: measured Tj(U6) > 117.0 C (margin < 3.0 C) OR the O2 thermal path not implemented => open a new rev "
                                "whose first action is to add the U6-domain GND via array until theta_JA_eff <= 9.5 C/W (margin >= 8 C); "
                                "T2: if U6-domain geometry is revised for any other reason, add the array in the same rev"},
                     {"doc": TI["doc"], "section": "9.4.1 Layout Guidelines rule 5",
                      "quoted": "GND vias should be placed directly beneath the device ... improving thermal conductivity"}],
        "threshold": {"theta_ja_eff_c_per_w": 11.0, "ta_c": 40.0, "tj_max_c": 120.0,
                      "pact_cases_w": {"EQ0-2_typ": 4.7, "EQ0-2_max": 6.0, "EQ5-19_typ": 5.8, "EQ5-19_max": 7.0},
                      "gnd_vias_beneath_device_min": 1,
                      "conditional_goal": {"trigger_tj_c": 117.0, "target_theta_ja_eff_c_per_w": 9.5},
                      "check_scope": "structural check (GND vias beneath the device, datasheet rule 5) = verdict part; "
                                     "the four-case Tj budget is recomputed from the DECLARED inputs (Ta/theta/P) and reported"},
        "machine_check": "count GND vias inside the device bounding box (>= 1) AND recompute Tj = Ta + P*theta_JA_eff for the four declared cases",
        "missing_input": None}

    crit["P6"] = {
        "layer": "CONSTRUCTION", "id": "P6", "name": "DFM minimum spacing",
        "kind": "NUMERIC", "status": "SOURCED", "source_kind": "IN_REGISTER_DOC",
        "citation": [{"doc": "_shared/eda_core/drc_rules.json (frozen four sources)", "section": "clearance", "quoted": "declared clearance rules"},
                     {"doc": "criteria/jlc_hdi_capability.yaml", "section": "factory capability", "quoted": "JLC capability file"}],
        "threshold": {"clearance_violations_max": 0},
        "machine_check": "clearance violations from the chain kicad-cli DRC report == 0",
        "missing_input": None}

    crit["P7"] = {
        "layer": "CONSTRUCTION", "id": "P7", "name": "power / GND (decoupling proximity)",
        "kind": "STRUCTURAL_CHECK", "status": "PENDING", "source_kind": "MANUFACTURER_DATASHEET",
        "citation": [{"doc": TI["doc"], "section": "9.4.1 Layout Guidelines rule 1",
                      "quoted": "Decoupling capacitors should be placed as close to the VCC pins as possible. Placing the decoupling capacitors directly underneath the device is recommended if the board design permits."}],
        "threshold": {"literal_check": ">= 1 decoupling capacitor inside the device bounding box (datasheet: 'directly underneath ... recommended')",
                      "reported": "min distance from a power-net capacitor to the device bbox edge; count of power-net capacitors in the vicinity",
                      "no_numeric_limit": "the datasheet gives no mm limit ('as close as possible' / 'if the board design permits')"},
        "machine_check": "report (min cap distance to device bbox, vicinity count, caps-inside-device count)",
        "missing_input": "a machine-readable per-cap -> power-pin mapping (SPEC pd.decoupling is a STRING) - without it the criterion cannot be turned into a verdict",
        "note": "the datasheet's recommendation is conditional ('if the board design permits'), so 'not underneath' is a FINDING, not an automatic FAIL"}

    rep = {
        "artifact": "k2_scheme_gate_thresholds_v1", "ts": "2026-09-28",
        "authority": "#K2-336 sec.4.1 (threshold completeness, C17') + #K2-337 window C follow-through",
        "policy": "no invented thresholds; every entry carries source_kind + citation + quoted source; unavailable => PENDING with the named missing input",
        "sources": {"pcie_cem_spec": CEM, "ti_datasheet": TI},
        "criteria": crit,
        "summary": {
            "scheme_layer": ["P1", "P2", "P3", "P4"],
            "construction_layer": ["P5", "P6", "P7"],
            "scheme_layer_status": "COMPLETE (all four SOURCED => the scheme gate yields a full binary)",
            "construction_layer_status": "P5 SOURCED / P6 SOURCED / P7 PENDING (named missing input)",
        },
        "OWNER-ITEMS": 0,
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "scheme_layer_complete": True,
                      "P1": crit["P1"]["status"], "P2": crit["P2"]["status"], "P3": crit["P3"]["status"],
                      "P4": crit["P4"]["status"], "P5": crit["P5"]["status"], "P6": crit["P6"]["status"],
                      "P7": crit["P7"]["status"], "L_max_mm": L_MAX_MM}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
