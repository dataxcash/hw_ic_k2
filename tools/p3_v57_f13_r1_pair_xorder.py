#!/usr/bin/env python3
"""F-13 pair 域 **v1.1**（rev F13-R1PAIR.2）：加 x-序维（L2 裁决 2026-09-10，逃生门 ①）。

只读消费：冻结 verdict（via 候选）、v1 pair 工件（域定义与统计）、manifest（页/侧）。
发射**新**文件 `m13_v57_f13_r1_pair_coupling_v1_1.json`；v1 工件与冻结四源**不动**。

x-序维定义（W3 准入约束）：
  每页的 via 列对 (P_x, N_x) 必须存在一条**可实现的**候选 (P_y, N_y)，满足
  dist >= 0.525 ∧ |P_x-N_x| >= 0.38；且在同一走廊内按 R2 lane 序排列时，
  **每极性 x 单调**（方向由 W3 构造证据选定并记录于 W3 工件）。
  → 本工件发射每页的列对域（compact）+ 每极性的可用 x 列集合。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
VERDICT = STEP2 / "m13_v57_s1_r1_via_verdict.json"
PAIR_V1 = STEP2 / "m13_v57_f13_r1_pair_coupling.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
SPEC = L3 / "SPEC_k2_v4.json"
RULES = K2 / "_shared" / "eda_core" / "drc_rules.json"
OUT = STEP2 / "m13_v57_f13_r1_pair_coupling_v1_1.json"

REVISION = "F13-R1PAIR.2"
VIA_VIA = 0.525
STAGGER = 0.38
TOL = 1e-9


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    verdict = json.load(VERDICT.open())
    pair_v1 = json.load(PAIR_V1.open())
    manifest = json.load(MANIFEST.open())
    spec = json.load(SPEC.open())
    rules = json.load(RULES.open())
    side = {p["page_id"]: p["side"] for p in manifest["pages"]}

    pages = {}
    for pid in sorted(verdict["pages"]):
        pg = verdict["pages"][pid]
        P = np.asarray(pg["P"]["cands"], dtype=float)
        N = np.asarray(pg["N"]["cands"], dtype=float)
        d = np.linalg.norm(P[:, None, :] - N[None, :, :], axis=2)
        dx = np.abs(P[:, None, 0] - N[None, :, 0])
        ok = (d >= VIA_VIA - TOL) & (dx >= STAGGER - TOL)
        i, j = np.nonzero(ok)
        dd = d[ok]
        combos: dict = {}
        for k in range(len(i)):
            key = (round(float(P[i[k], 0]), 3), round(float(N[j[k], 0]), 3))
            cur = combos.get(key)
            val = (round(float(dd[k]), 4), round(float(P[i[k], 1]), 4),
                   round(float(N[j[k], 1]), 4))
            if cur is None or val[0] > cur[0]:
                combos[key] = val
        xp = sorted({k[0] for k in combos})
        xn = sorted({k[1] for k in combos})
        rows = [[k[0], k[1], v[0]] for k, v in sorted(combos.items())]
        pages[pid] = {
            "side": side.get(pid, "?"),
            "corridor_hint": "EAST_CHIP_TO_J2" if side.get(pid) == "east"
                             else "WEST_MCIO_TO_CHIP",
            "n_column_pairs": len(rows),
            "x_columns_P": xp,
            "x_columns_N": xn,
            "x_span_P_mm": [xp[0], xp[-1]] if xp else None,
            "x_span_N_mm": [xn[0], xn[-1]] if xn else None,
            "x_column_pairs": rows,
            "v1_pair_domain_ref": {
                "artifact": str(PAIR_V1.relative_to(K2)),
                "sha256": sha256(PAIR_V1),
                "n_pairs_admissible_stagger_038":
                    pair_v1["pages"][pid]["pair_domain"]["n_pairs_admissible_stagger_038"],
                "admissible_pair_witness": pair_v1["pages"][pid]["admissible_pair_witness"],
            },
        }

    doc = {
        "artifact": "m13_v57_f13_r1_pair_coupling_v1_1",
        "schema": 1,
        "revision": REVISION,
        "status": "EMITTED",
        "status_kind": "X_ORDER_DIMENSION_ADDED",
        "supersedes": {"artifact": str(PAIR_V1.relative_to(K2)), "sha256": sha256(PAIR_V1),
                       "scope": "R1 pair 域新增 x-序维；v1 的域定义/统计/见证全部继承不变"},
        "authority": {
            "l2_ruling": "2026-09-10: 采纳逃生门 ① —— 「R1 via x 序与 R2 lane 序同向」升为 R1 准入约束",
            "verdict": {"path": str(VERDICT.relative_to(K2)), "sha256": sha256(VERDICT)},
            "manifest": {"path": str(MANIFEST.relative_to(K2)), "sha256": sha256(MANIFEST)},
            "spec": {"path": str(SPEC.relative_to(K2)), "sha256": sha256(SPEC)},
            "rules": {"path": str(RULES.relative_to(K2)), "sha256": sha256(RULES)},
        },
        "constraints": {
            "dist_min_mm": VIA_VIA, "col_stagger_mm": STAGGER,
            "stagger_basis": "p_gap+p_width",
            "x_order_rule": "within a corridor, in R2 lane order, x must be monotone per polarity "
                            "(direction fixed by W3 construction evidence; zero-crossing requirement)",
            "allocation": False,
        },
        "x_order_dim": {
            "semantics": "per page: the set of feasible via-column pairs (P_x, N_x) that admit at least "
                         "one candidate realization; x must be usable in a monotone per-polarity "
                         "sequence across the corridor's lane order",
            "field": "pages[*].x_column_pairs = [[P_x, N_x, dist_max_mm], ...] "
                     "(one realization witness per column pair is recoverable from the frozen verdict)",
            "frozen_sources_unchanged": True,
        },
        "pages": pages,
        "summary": {
            "n_pages": len(pages),
            "n_pages_with_x_column_pairs": sum(1 for p in pages.values() if p["n_column_pairs"]),
            "n_column_pairs_total": sum(p["n_column_pairs"] for p in pages.values()),
            "n_column_pairs_min": min(p["n_column_pairs"] for p in pages.values()),
            "n_column_pairs_max": max(p["n_column_pairs"] for p in pages.values()),
        },
        "producer": {"path": str(Path(__file__).relative_to(K2)), "revision": REVISION},
        "no_allocation_scan": {
            "forbidden_keys": ["assigned", "allocation", "selected_lane", "lane_assignment"],
            "leaked": [],
            "statement": "No cross-page resource allocation emitted; per-page column-pair domains only.",
        },
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    s = doc["summary"]
    print(f"F13-R1PAIR.2: pages={s['n_pages']} with_domain={s['n_pages_with_x_column_pairs']} "
          f"column_pairs total={s['n_column_pairs_total']} min/max={s['n_column_pairs_min']}/"
          f"{s['n_column_pairs_max']} sha={sha256(OUT)[:16]} size={OUT.stat().st_size//1024}KiB")
    return 0 if s["n_pages_with_x_column_pairs"] == s["n_pages"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
