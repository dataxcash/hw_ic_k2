#!/usr/bin/env python3
"""P3 v57 F8 — R3 connector escape-gap candidate domain generator (W2 successor).

R3 definition (S1 design §R3): connector pad wall -> corridor landing row gap.
  - gap candidate = x columns where a via can land within pad-row y ± half row
    pitch (via pad/adjacent-pad copper + clearance criterion);
  - conservation = each pad exactly 1 landing; same-column adjacent landings
    y-distance >= via_od + clearance.

Input authority: page manifest + SPEC + drc_rules (zero board read). Connector pad
sizes are named constants (frozen from the footprint at authoring time; the tool
itself never reads the board). No allocation, no W3 output. R4 is out of chain
(D0-1), so no wall-pad anchors are generated.
"""
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
SPEC = L3 / "SPEC_k2_v4.json"
RULES = K2 / "_shared" / "eda_core" / "drc_rules.json"
OUT = STEP2 / "m13_v57_f8_r3_gap_candidates.json"
GENERATOR = Path(__file__).resolve()
REV = "R3GEN-F8.1"

# Named pad constants (frozen footprint geometry; zero board read at runtime).
PAD_CONSTANTS = {
    "J2": {"w": 1.3, "h": 0.35,
           "authority": "SPEC.constraints.j2_escape_topology '0.6 pitch/0.35 高' "
                        "+ frozen footprint SlimSAS_x8_SFF-8654_74pin (1.3x0.35)"},
    "J3": {"w": 0.3, "h": 0.7,
           "authority": "frozen footprint MCIO_4i_SFF-1016 (0.3x0.7)"},
    "J4": {"w": 0.3, "h": 0.7,
           "authority": "frozen footprint MCIO_4i_SFF-1016 (0.3x0.7)"},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def r3(v: float) -> float:
    return round(v, 3)


def gather_pads(manifest: dict) -> list[dict]:
    pads = []
    for pg in manifest["pages"]:
        if pg["kind"] == "data":
            for pol in ("P", "N"):
                a = pg["anchors"]["conn"][pol]
                pads.append({"ref": a["ref"], "x": r3(a["pad_global"][0]),
                             "y": r3(a["pad_global"][1]), "net": a["net"],
                             "pin": a.get("pin"), "pad_num": a["pad_num"],
                             "pol": pol, "page": pg["page_id"], "kind": "data",
                             "side": "conn"})
        else:
            for side in ("conn", "conn2"):
                for pol in ("P", "N"):
                    a = pg["anchors"][side][pol]
                    pads.append({"ref": a["ref"], "x": r3(a["pad_global"][0]),
                                 "y": r3(a["pad_global"][1]), "net": a["net"],
                                 "pin": a.get("pin"), "pad_num": a["pad_num"],
                                 "pol": pol, "page": pg["page_id"], "kind": "refclk",
                                 "side": side})
    return pads


def row_pitch(ys: list[float]) -> float | None:
    s = sorted(set(ys))
    gaps = [round(b - a, 3) for a, b in zip(s, s[1:])]
    return min(gaps) if gaps else None


def escape_topology(spec: dict, refs: list[str]) -> dict:
    j2 = spec["constraints"]["j2_escape_topology"]
    topo = {}
    for ref in refs:
        if ref == "J2":
            topo[ref] = {"inner_col_x": j2["inner_col_x"],
                         "outer_col_x": j2["outer_col_x"],
                         "inner_escape": "left", "outer_escape": "right",
                         "source": "SPEC.constraints.j2_escape_topology"}
        else:
            topo[ref] = {"escape": "east",
                         "source": "S1 design §R3 (MCIO A column toward corridor; "
                                   "corridor WEST lies east of the connector)"}
    return topo


def derive_gaps(cols: list[float], w: float, need: float, clr: float,
                via_od: float) -> list[dict]:
    gaps = [{"x": r3(cols[0] - (w / 2 + clr + via_od / 2)), "side": "left",
             "between": [None, cols[0]], "feasible": True, "basis": "outside"}]
    for a, b in zip(cols, cols[1:]):
        gapw = round((b - a) - w, 3)
        gaps.append({"x": r3((a + b) / 2), "side": "between", "between": [a, b],
                     "gap_width_mm": gapw, "feasible": gapw >= need - 1e-9})
    gaps.append({"x": r3(cols[-1] + (w / 2 + clr + via_od / 2)), "side": "right",
                 "between": [cols[-1], None], "feasible": True, "basis": "outside"})
    return gaps


def main() -> int:
    mf = json.load(open(MANIFEST))
    spec = json.load(open(SPEC))
    rules = json.load(open(RULES))
    via_od = spec["vias"]["std"]["outer"]
    clr = next(nc["clearance"] for nc in rules["clearance"]["net_classes"]
               if nc["name"] == "PCIe85")
    need = via_od + 2 * clr
    required_dy = round(via_od + clr, 3)

    pads = gather_pads(mf)
    refs = sorted({p["ref"] for p in pads})
    topo = escape_topology(spec, refs)

    connectors, refclk_pads = {}, []
    cons_per_pad, conflict_edges = [], []
    for ref in refs:
        rp = [p for p in pads if p["ref"] == ref]
        w = PAD_CONSTANTS[ref]["w"]
        pitch = row_pitch([p["y"] for p in rp])
        half = round(pitch / 2, 3) if pitch else None
        cols = sorted({p["x"] for p in rp})
        gaps = derive_gaps(cols, w, need, clr, via_od)
        col_gaps = {c: [g for g in gaps if c in g["between"]] for c in cols}

        col_out = {}
        for c in cols:
            cpads = sorted([p for p in rp if p["x"] == c],
                           key=lambda p: (p["y"], p["pol"], p["net"]))
            entries = []
            for p in cpads:
                cand = [g["x"] for g in col_gaps[c] if g["feasible"]]
                band = [r3(p["y"] - half), r3(p["y"] + half)] if half else None
                entries.append({"net": p["net"], "pin": p["pin"],
                                "pad_num": p["pad_num"], "pol": p["pol"],
                                "page": p["page"], "kind": p["kind"],
                                "y": p["y"], "y_band": band,
                                "gap_candidates": cand})
                cons_per_pad.append({"ref": ref, "column_x": c, "net": p["net"],
                                     "pol": p["pol"], "kind": p["kind"],
                                     "n_gap_candidates": len(cand),
                                     "ok": len(cand) >= 1})
            if ref == "J2":
                role = "inner" if c == topo["J2"]["inner_col_x"] else "outer"
                edir = topo["J2"][f"{role}_escape"]
            else:
                role, edir = "MCIO", "east"
            col_out[str(c)] = {
                "x": c, "role": role, "escape_dir": edir,
                "n_pads": len(cpads),
                "rows": sorted({p["y"] for p in cpads}),
                "y_min": min(p["y"] for p in cpads),
                "y_max": max(p["y"] for p in cpads),
                "gap_columns": [{"x": g["x"], "side": g["side"],
                                 "feasible": g["feasible"],
                                 "gap_width_mm": g.get("gap_width_mm"),
                                 "basis": g.get("basis")} for g in col_gaps[c]],
                "entries": entries}
        connectors[ref] = {"row_pitch_mm": pitch, "half_row_pitch_mm": half,
                           "n_pads": len(rp), "columns": col_out}

        for g in gaps:
            if not g["feasible"]:
                continue
            gp = [p for p in rp if p["x"] in g["between"]]
            for i in range(len(gp)):
                for j in range(i + 1, len(gp)):
                    dy = round(abs(gp[i]["y"] - gp[j]["y"]), 3)
                    if dy < required_dy - 1e-9:
                        conflict_edges.append(
                            {"gap_x": g["x"], "pad_a": gp[i]["net"],
                             "pad_b": gp[j]["net"], "dy_mm": dy,
                             "required_mm": required_dy, "conflict": True})

        for p in rp:
            if p["kind"] == "refclk":
                refclk_pads.append({k: p[k] for k in
                                    ("page", "side", "ref", "pol", "pad_num",
                                     "net", "x", "y")})
    refclk_pads.sort(key=lambda p: (p["ref"], p["y"], p["x"], p["pol"]))

    n_pads = len(cons_per_pad)
    viol = [c for c in cons_per_pad if not c["ok"]]
    cons = {"rule": "each pad exactly 1 landing (>=1 candidate gap column)",
            "n_pads": n_pads,
            "n_with_candidate": n_pads - len(viol),
            "n_without_candidate": len(viol),
            "violations": viol,
            "verdict": "FEASIBLE" if not viol else "INFEASIBLE"}
    cg = {"rule": "same-column adjacent landings y-distance >= via_od + clearance",
          "required_mm": required_dy, "n_edges": len(conflict_edges),
          "edges": conflict_edges,
          "verdict": "COMPLETE"}

    rep = {"artifact": "m13_v57_f8_r3_gap_candidates", "schema": 1,
           "revision": REV,
           "basis": "S1 design §R3 + SPEC.constraints.j2_escape_topology + "
                    "manifest connector anchors; zero board read",
           "authority": {"manifest": MANIFEST.name, "spec": SPEC.name,
                         "rules": str(RULES.relative_to(K2)),
                         "pad_constants": "frozen footprint geometry (named "
                                          "constants; zero board read at runtime)"},
           "inputs_sha": {"manifest": sha(MANIFEST), "spec": sha(SPEC),
                          "rules": sha(RULES)},
           "producer": {"generator": {"path": str(GENERATOR.relative_to(K2)),
                                      "revision": REV, "sha256": sha(GENERATOR)}},
           "params": {"via_od": via_od, "clearance": clr,
                      "via_via_min_mm": required_dy,
                      "required_same_column_dy_mm": required_dy,
                      "gap_fit_mm": round(need, 3),
                      "pad_constants": PAD_CONSTANTS},
           "escape_topology": topo, "connectors": connectors,
           "refclk_pads": refclk_pads, "conservation": cons,
           "conflict_graph": cg}
    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    for ref in refs:
        c = connectors[ref]
        print(f"{ref}: pitch={c['row_pitch_mm']} n_pads={c['n_pads']} "
              f"cols={list(c['columns'])}")
    print("refclk_pads:", len(refclk_pads),
          "conservation:", cons["verdict"],
          "conflict_edges:", len(conflict_edges))
    print("artifact:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
