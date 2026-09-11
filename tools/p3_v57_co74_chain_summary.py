#!/usr/bin/env python3
"""CO-74：全链重基线汇总（G4..G7 @ SPEC rev-8）—— 只读产物，不改板/图纸。

独立断言：G4 图纸的几何键（route_geometry/pages/decision_contract/layers）与
CO-73 rev-7 基线（drawing 3cc123056a7319ff @ git 46e30e5）**逐字节同**；板字节同 0e636a67c1472462。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co74_chain.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
GEOM_KEYS = ["route_geometry", "pages", "decision_contract", "layers"]
REF_GEOM = {"route_geometry": "d39becad4f51f3af", "pages": "e659edaa6608f3d2",
            "decision_contract": "c0e018ec4102fa72", "layers": "db2ee692c03204da"}
REF_DRAWING = "3cc123056a7319ff"
REF_BOARD = "0e636a67c1472462"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def khash(o) -> str:
    return hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def main() -> int:
    g4 = json.loads((STEP2 / "m13_v57_w3_joint_assignment.json").read_text(encoding="utf-8"))
    g5 = json.loads((STEP2 / "m13_v57_w3_validation.json").read_text(encoding="utf-8"))
    l4c = json.loads((STEP2 / "m13_v57_l4_construction.json").read_text(encoding="utf-8"))
    l4v = json.loads((STEP2 / "m13_v57_l4_validation.json").read_text(encoding="utf-8"))
    fab = json.loads((STEP2 / "m13_v57_l5_fab_record.json").read_text(encoding="utf-8"))
    dfm = json.loads((STEP2 / "m13_v57_l5_dfm_dft_record.json").read_text(encoding="utf-8"))
    si = json.loads((STEP2 / "m13_v57_l5_si_pi_emc_record.json").read_text(encoding="utf-8"))

    geom = {k: khash(g4.get(k)) for k in GEOM_KEYS}
    geom_ok = all(geom[k] == REF_GEOM[k] for k in GEOM_KEYS)
    board_ok = s16(BOARD) == REF_BOARD
    assert geom_ok, geom
    assert board_ok, s16(BOARD)

    rec = {
        "artifact": "m13_v57_co74_chain", "schema": 1, "revision": "CO-74.1",
        "nature": "L2 PDN：SPEC rev-8 下全链重基线（G4..G7）",
        "inputs": {"spec_rev8_sha16": s16(L3 / "SPEC_k2_v4.spec-rev-8.json"),
                   "layer_intent": s16(STEP2 / "m13_v57_layer_intent_rev6.json")},
        "gates": {
            "G4": {"verdict": g4.get("verdict"), "revision": g4.get("revision"),
                   "pages": len(g4.get("pages") or []),
                   "crossings": g4.get("same_layer_crossings"),
                   "drawing_sha16": s16(STEP2 / "m13_v57_w3_joint_assignment.json")},
            "G5": {"verdict": g5.get("verdict"), "frozen": g5.get("frozen"),
                   "method_gates": g5.get("method_gates", {}).get("G-M")},
            "G6": {"verdict": l4v.get("verdict"), "checks": l4v.get("checks"),
                   "n_nets": l4c["tally"]["n_nets"], "n_segments": l4c["tally"]["n_segments"],
                   "n_vias": l4c["tally"]["n_vias"], "board_sha16": s16(BOARD)},
            "G7": {"fab_ok": bool(fab), "dfm_verdict": dfm.get("verdict"),
                   "dfm_new_total": dfm["drc"]["new_total"],
                   "in_scope_unconnected": dfm["dft"]["in_scope_unconnected_nets"],
                   "si_verdict": si.get("verdict"), "si_skew_ok": si["SI"]["skew_ok"],
                   "si_skew_max": si["SI"]["max_intra_pair_skew_mm"],
                   "si_skew_pages": si["SI"]["skew_pages_checked"],
                   "pi_plane_layers_reserved": si["PI"]["plane_layers_reserved"]},
        },
        "invariance": {
            "reference_rev7_drawing_sha16": REF_DRAWING,
            "reference_git": "46e30e5 (CO-73)",
            "geometry_key_hashes": geom, "all_geometry_identical": geom_ok,
            "board_sha16": s16(BOARD), "board_identical": board_ok,
            "differing_top_level_keys": ["frozen_sha_check", "inputs_sha"],
        },
        "redline": "四冻结源未动；阈值未放宽；零几何改动（几何键逐字节同）；while=0/零坐标搜索。",
    }
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"chain": s16(OUT), "geom_identical": geom_ok, "board": s16(BOARD),
                      "G4": rec["gates"]["G4"]["verdict"], "G5": rec["gates"]["G5"]["verdict"],
                      "G6": rec["gates"]["G6"]["verdict"], "G7_dfm": rec["gates"]["G7"]["dfm_verdict"],
                      "G7_si": rec["gates"]["G7"]["si_skew_max"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
