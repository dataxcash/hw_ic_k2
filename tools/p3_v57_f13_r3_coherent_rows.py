#!/usr/bin/env python3
"""F-13 r3 — (frame, polarity) 级「共线行 + 承载列序列」相干字段发射（owner 预授权 W3-C13/C14）。
只读消费：r2 verdict（±2.5mm 域，DRC 谓词已逐点验过）、F-3 lane frame。新文件，旧件不动。"""
import hashlib, json
from pathlib import Path
K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
S = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
V2 = S / "m13_v57_s1_r1_via_verdict_r2.json"
LF = S / "m13_v57_f3_lane_frame.json"
OUT = S / "m13_v57_f13_r3_coherent_rows.json"
v2 = json.load(V2.open()); lf = json.load(LF.open())
sets = {}
for cid, cd in lf["corridors"].items():
    for fr in cd["frames"]:
        ids = [p["page_id"] for p in sorted(fr["pages"], key=lambda q: q["order_index"])]
        for pol in ("P", "N"):
            rows = {}
            for pid in ids:
                for cand in v2["pages"][pid][pol]["cands"]:
                    rows.setdefault(round(float(cand[1]), 3), set()).add(round(float(cand[0]), 3))
            common = None
            for pid in ids:
                ys = set()
                for cand in v2["pages"][pid][pol]["cands"]:
                    ys.add(round(float(cand[1]), 3))
                common = ys if common is None else (common & ys)
            key = f"{cid}|{fr['conn_ref']}|{fr['band']}|{pol}"
            entry = []
            for r in sorted(common or []):
                cols = sorted(rows.get(r, set()))
                gaps = [round(cols[i + 1] - cols[i], 3) for i in range(len(cols) - 1)]
                entry.append({"row": r, "cols": cols, "n_cols": len(cols),
                              "max_gap_mm": (max(gaps) if gaps else None),
                              "span_mm": (round(cols[-1] - cols[0], 3) if len(cols) > 1 else 0.0)})
            sets[key] = {"corridor": cid, "conn_ref": fr["conn_ref"], "band": fr["band"],
                         "polarity": pol, "pages": ids, "n_rows": len(entry), "rows": entry}
doc = {"artifact": "m13_v57_f13_r3_coherent_rows", "schema": 1, "revision": "F13-R3.1",
       "authority": "owner via supervision work orders W3-C13/C14 (project-artifact layer, version bump)",
       "inputs_sha": {"verdict_r2": hashlib.sha256(V2.read_bytes()).hexdigest(),
                      "lane_frame": hashlib.sha256(LF.read_bytes()).hexdigest()},
       "field_spec": {"key": "(corridor|conn_ref|band|polarity)",
                      "rows": "[{row, cols[], n_cols, max_gap_mm, span_mm}] - collinear row and the "
                              "columns that carry it (all DRC-checked by the r2 verdict)",
                      "use": "W3 selects one row per (frame,polarity) by a single-pass argmin over this "
                             "constant-size set (fixed key, fixed tie-break) - no scan/trial/backtrack"},
       "n_sets": len(sets), "sets": sets}
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
print("F13-R3 sets", len(sets), "rows/set", sorted({v['n_rows'] for v in sets.values()}),
      "sha", hashlib.sha256(OUT.read_bytes()).hexdigest()[:16])
