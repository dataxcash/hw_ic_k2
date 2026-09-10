#!/usr/bin/env python3
"""F-13 对域 v1.2（向量化归约版，ROOT-13）：由 r2 verdict(±2.5mm) 一次性生成紧凑列对域 + 存量实现。
全 numpy 广播/lexsort/unique；无逐对 Python 循环；wall 线性。只读 verdict，不改四源。"""
import hashlib, json, time
from pathlib import Path
import numpy as np
K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2"); S = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
V2 = S / "m13_v57_s1_r1_via_verdict_r2.json"; OUT = S / "m13_v57_f13_r1_pair_coupling_v1_2.json"
t0 = time.monotonic()
v2 = json.load(V2.open())
VV, ST, TOL = 0.525, 0.38, 1e-9
pages = {}
for pid in sorted(v2["pages"]):
    P = np.asarray(v2["pages"][pid]["P"]["cands"], dtype=float)
    N = np.asarray(v2["pages"][pid]["N"]["cands"], dtype=float)
    d = np.linalg.norm(P[:, None, :] - N[None, :, :], axis=2)
    dx = np.abs(P[:, None, 0] - N[None, :, 0])
    ok = (d >= VV - TOL) & (dx >= ST - TOL)
    i, j = np.nonzero(ok)
    dd = d[ok]
    if len(i) == 0:
        pages[pid] = {"pair_rows": [], "n_rows": 0}; continue
    code = (np.round(P[i, 0] * 1000).astype(np.int64) * 1000003
            + np.round(N[j, 0] * 1000).astype(np.int64))
    order = np.lexsort((dd, code))
    cs, cds = code[order], dd[order]
    last = np.flatnonzero(np.concatenate([np.diff(cs) != 0, [True]]))
    idx = order[last]
    rows = np.column_stack([P[i[idx], 0], N[j[idx], 0], P[i[idx], 1], N[j[idx], 1], dd[idx]])
    pages[pid] = {"pair_rows": [[round(float(a), 4) for a in r] for r in rows], "n_rows": int(len(rows))}
doc = {"artifact": "m13_v57_f13_r1_pair_coupling_v1_2", "schema": 1, "revision": "F13-R1PAIR.4",
       "authority": "ROOT-13 (project-artifact layer, pre-authorized per ROOT-1 policy)",
       "method": "fully vectorised (broadcast + lexsort + run-end reduce); no per-pair Python loop",
       "inputs_sha": {"verdict_r2": hashlib.sha256(V2.read_bytes()).hexdigest()},
       "field_spec": {"pair_rows": "[[P_x, N_x, P_y, N_y, dist_mm], ...] one max-dist realisation per (P_x,N_x) column pair",
                      "use": "engine consumes via O(1)-bounded fixed-key argmin (no derivation in the solve path)"},
       "n_pages": len(pages), "n_rows_total": sum(p["n_rows"] for p in pages.values()), "pages": pages}
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
print("v1.2 rows", doc["n_rows_total"], "wall_s", round(time.monotonic() - t0, 3),
      "sha", hashlib.sha256(OUT.read_bytes()).hexdigest()[:16])
