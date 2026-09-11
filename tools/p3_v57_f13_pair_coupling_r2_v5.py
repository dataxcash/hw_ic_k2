#!/usr/bin/env python3
"""F-13 R1 pair 域 **v1.5**（CO-10 §10 落地）：在 v1.4 的行域基础上，以
`m13_v57_co09_pad_field.json`（全 616 pad 障碍场）为过滤场，剔除**非法近 pad 候选**。

背景（CO-10 §9）：冻结 pair 域 v1.4 只约束 `dist>=0.525 ∧ dx>=0.38`，不约束
chip 侧 `F.Cu` 逃逸段 / via1 与 pad 场的净距 ⇒ 含非法候选
（实测 `pad_seg (92.35,49.76->94.3,49.16) ↔ U6 BY35 0.0265`）。
本件按**单候选可分解**（via1/pad 逃逸段的合法性只依赖该候选自身）先算 P/N 合法掩码，
再在 pair 域上做同 v1.4 的 min-dist / max-dist / pad-proximate 归约，发射 v1.5。

判据与 W3 运行时谓词一致（`p3_v57_w3_constructive.py` A-CN.9 全跨距口径）：
  - `F.Cu` 段 (pad_global -> via) 与任一 pad 的**边距** >= escape_clearance(ECN-001 0.075)；
  - via1 圆 (r=0.175) 与任一 pad 的**边距** >= 0.075；
  - 豁免本页自身 4 pad（chip P/N + conn P/N）。

只读消费：冻结 verdict r2、manifest、CO-09 pad field、v1.4（域统计对照）。
发射**新**文件 `m13_v57_f13_r1_pair_coupling_v1_5.json`；v1.4 与冻结四源**不动**。
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
VERDICT = STEP2 / "m13_v57_s1_r1_via_verdict_r2.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
PADFIELD = STEP2 / "m13_v57_co09_pad_field.json"
PAIR_V14 = STEP2 / "m13_v57_f13_r1_pair_coupling_v1_4.json"
OUT = STEP2 / "m13_v57_f13_r1_pair_coupling_v1_5.json"

REVISION = "F13-R1PAIR.7"
VV, ST, TOL = 0.525, 0.38, 1e-9
VIA_R = 0.175
ESC = 0.075


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pad_arrays(pads: list) -> dict:
    return {
        "x": np.array([q["x"] for q in pads], dtype=float),
        "y": np.array([q["y"] for q in pads], dtype=float),
        "hx": np.array([q["sx"] / 2.0 for q in pads], dtype=float),
        "hy": np.array([q["sy"] / 2.0 for q in pads], dtype=float),
        "r": np.array([max(q["sx"], q["sy"]) / 2.0 for q in pads], dtype=float),
        "circ": np.array([q["shape"] == 0 for q in pads]),
    }


def seg_edge_gap(ax, ay, bx, by, PA, exempt: np.ndarray) -> np.ndarray:
    """线段 (a->b) 到每个 pad 的**边距**（probe pad_seg_edge 同式，向量化于候选广播后）。"""
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    L2 = np.where(L2 < 1e-12, 1.0, L2)
    PX, PY, HX, HY, R, CIRC = PA["x"], PA["y"], PA["hx"], PA["hy"], PA["r"], PA["circ"]
    t = np.clip(((PX[None, :] - ax[:, None]) * dx[:, None] + (PY[None, :] - ay[:, None]) * dy[:, None]) / L2[:, None], 0.0, 1.0)
    qx = ax[:, None] + t * dx[:, None]
    qy = ay[:, None] + t * dy[:, None]
    ex = np.maximum(np.abs(qx - PX[None, :]) - HX[None, :], 0.0)
    ey = np.maximum(np.abs(qy - PY[None, :]) - HY[None, :], 0.0)
    rect = np.sqrt(ex * ex + ey * ey)
    circ = np.maximum(np.sqrt((qx - PX[None, :]) ** 2 + (qy - PY[None, :]) ** 2) - R[None, :], 0.0)
    g = np.where(CIRC[None, :], circ, rect)
    g = np.where(exempt, np.inf, g)
    return g.min(axis=1)


def via_edge_gap(vx, vy, PA, exempt: np.ndarray) -> np.ndarray:
    PX, PY, HX, HY, R, CIRC = PA["x"], PA["y"], PA["hx"], PA["hy"], PA["r"], PA["circ"]
    ex = np.maximum(np.abs(vx[:, None] - PX[None, :]) - HX[None, :], 0.0)
    ey = np.maximum(np.abs(vy[:, None] - PY[None, :]) - HY[None, :], 0.0)
    rect = np.sqrt(ex * ex + ey * ey)
    circ = np.maximum(np.sqrt((vx[:, None] - PX[None, :]) ** 2 + (vy[:, None] - PY[None, :]) ** 2) - R[None, :], 0.0)
    g = np.where(CIRC[None, :], circ, rect)
    g = np.where(exempt, np.inf, g)
    return g.min(axis=1)


def main() -> int:
    t0 = time.monotonic()
    v2 = json.loads(VERDICT.read_text())
    man = json.loads(MANIFEST.read_text())
    padf = json.loads(PADFIELD.read_text())
    PA = pad_arrays(padf["pads"])
    PXX, PYY = PA["x"], PA["y"]

    anchors = {}
    for _p in man["pages"]:
        if _p["kind"] != "data":
            continue
        ch, co = _p["anchors"]["chip"], _p["anchors"]["conn"]
        anchors[_p["page_id"]] = {
            "pad": {pol: (ch[pol]["pad_global"][0], ch[pol]["pad_global"][1]) for pol in ("P", "N")},
            "conn": {pol: (co[pol]["pad_global"][0], co[pol]["pad_global"][1]) for pol in ("P", "N")},
            "pady": (ch["P"]["pad_global"][1], ch["N"]["pad_global"][1]),
        }

    pages, dropped = {}, {}
    n_raw = n_kept = 0
    for pid in sorted(v2["pages"]):
        anc = anchors[pid]
        exempt = np.zeros(len(PXX), dtype=bool)
        for x, y in list(anc["pad"].values()) + list(anc["conn"].values()):
            exempt |= (np.abs(PXX - x) < 0.02) & (np.abs(PYY - y) < 0.02)  # manifest 坐标 2 位小数 vs pad field 全精度
        P = np.asarray(v2["pages"][pid]["P"]["cands"], dtype=float)
        N = np.asarray(v2["pages"][pid]["N"]["cands"], dtype=float)
        # --- 单候选合法掩码（可分解：只依赖该候选自身）---
        def legal(C, pad_xy):
            g_seg = seg_edge_gap(np.full(len(C), pad_xy[0]), np.full(len(C), pad_xy[1]),
                                 C[:, 0], C[:, 1], PA, exempt)
            g_via = via_edge_gap(C[:, 0], C[:, 1], PA, exempt)
            return (g_seg >= ESC - TOL) & (g_via >= ESC - TOL)
        lp = legal(P, anc["pad"]["P"])
        ln = legal(N, anc["pad"]["N"])
        # --- pair 域 ---
        d = np.linalg.norm(P[:, None, :] - N[None, :, :], axis=2)
        dx = np.abs(P[:, None, 0] - N[None, :, 0])
        ok = (d >= VV - TOL) & (dx >= ST - TOL) & lp[:, None] & ln[None, :]
        i, j = np.nonzero(ok)
        n_raw += int(len(i))
        if len(i) == 0:
            pages[pid] = {"pair_rows": [], "n_rows": 0}
            dropped[pid] = {"n_cand_P": int(len(P)), "n_cand_P_legal": int(lp.sum()),
                            "n_cand_N": int(len(N)), "n_cand_N_legal": int(ln.sum())}
            continue
        dd = d[i, j]
        code = (np.round(P[i, 0] * 1000).astype(np.int64) * 1000003
                + np.round(N[j, 0] * 1000).astype(np.int64))
        order = np.lexsort((dd, code))
        cs = code[order]
        first = np.flatnonzero(np.concatenate([[True], np.diff(cs) != 0]))
        last = np.flatnonzero(np.concatenate([np.diff(cs) != 0, [True]]))
        ppy, pny = anc["pady"]
        k3 = np.abs(P[i, 1] - ppy) + np.abs(N[j, 1] - pny)
        o3 = np.lexsort((k3, code)); c3 = code[o3]
        f3 = np.flatnonzero(np.concatenate([[True], np.diff(c3) != 0]))
        idx = np.unique(np.concatenate([order[first], order[last], o3[f3]]))
        rows = np.column_stack([P[i[idx], 0], N[j[idx], 0], P[i[idx], 1], N[j[idx], 1], dd[idx]])
        pages[pid] = {"pair_rows": [[round(float(a), 4) for a in r] for r in rows], "n_rows": int(len(rows))}
        n_kept += int(len(rows))
        dropped[pid] = {"n_cand_P": int(len(P)), "n_cand_P_legal": int(lp.sum()),
                        "n_cand_N": int(len(N)), "n_cand_N_legal": int(ln.sum()),
                        "n_pairs_raw": int(len(i))}

    v14 = json.loads(PAIR_V14.read_text())
    doc = {
        "artifact": "m13_v57_f13_r1_pair_coupling_v1_5",
        "schema": 1, "revision": REVISION, "status": "EMITTED",
        "status_kind": "PAD_FIELD_LEGALISE",
        "supersedes": {"artifact": "m13_v57_f13_r1_pair_coupling_v1_4",
                       "sha256": sha16(PAIR_V14), "scope": "同域定义/归约；新增全 616 pad 障碍场合法性过滤"},
        "authority": {"co10_ruling": "CO-10 §10：pair 域候选未含全 pad 障碍场；须以 pad field 重派生（L3）",
                      "co09_ruling": "CO-09 §4bis：D3 主项 = 连接器/芯片 pad 未入障碍场"},
        "method": "per-candidate legality mask (decomposable) then v1.4-identical pair reduction (min-dist/max-dist/pad-proximate)",
        "inputs_sha": {"verdict_r2": sha16(VERDICT), "manifest": sha16(MANIFEST),
                       "pad_field": sha16(PADFIELD), "pair_v1_4": sha16(PAIR_V14)},
        "predicate": {"via_r_mm": VIA_R, "escape_clearance_mm": ESC,
                      "F_Cu_seg_vs_pad": "pad_seg_edge >= ESC", "via1_vs_pad": "pad_via_edge >= ESC",
                      "own_pads_exempt": "4 (chip P/N + conn P/N)",
                      "consistency": "与 p3_v57_w3_constructive.py 运行时 A-CN.9 全跨距口径同式"},
        "field_spec": {"pair_rows": "[[P_x,N_x,P_y,N_y,dist], ...] min-dist + max-dist + pad-proximate realisation per (P_x,N_x) column pair"},
        "n_pages": len(pages), "n_rows_total": sum(p["n_rows"] for p in pages.values()),
        "n_pairs_raw_legal": int(n_raw),
        "v1_4_n_rows_total": v14["n_rows_total"],
        "per_page_legality": dropped,
        "pages": pages,
        "producer": {"path": "k2/tools/p3_v57_f13_pair_coupling_r2_v5.py", "revision": REVISION},
        "redline": "只读冻结四源；v1.4 未动；无跨页资源分配（仅每页域）",
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"F13-R1PAIR.7 v1.5: pages={len(pages)} rows_total={doc['n_rows_total']} (v1.4={v14['n_rows_total']}) "
          f"raw_legal_pairs={n_raw} wall_s={round(time.monotonic() - t0, 3)} sha16={sha16(OUT)[:16]}")
    return 0 if doc["n_rows_total"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
