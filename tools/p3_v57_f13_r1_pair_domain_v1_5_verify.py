#!/usr/bin/env python3
"""独立复核 F-13 R1 pair 域 v1.5（非 producer）：逐行验证 pad 场合法性。
对 v1.5 与 v1.4 跑同一判据，输出 PASS/FAIL 明细（证明 v1.4 含非法行、v1.5 全合法）。
只读。"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
PADF = json.loads((STEP2 / "m13_v57_co09_pad_field.json").read_text())
MAN = json.loads((STEP2 / "m13_v57_s1_page_manifest.json").read_text())
VIA_R, ESC, TOL = 0.175, 0.075, 1e-9

PX = np.array([q["x"] for q in PADF["pads"]]); PY = np.array([q["y"] for q in PADF["pads"]])
HX = np.array([q["sx"] / 2 for q in PADF["pads"]]); HY = np.array([q["sy"] / 2 for q in PADF["pads"]])
RA = np.array([max(q["sx"], q["sy"]) / 2 for q in PADF["pads"]]); CIRC = np.array([q["shape"] == 0 for q in PADF["pads"]])

ANC = {}
for _p in MAN["pages"]:
    if _p["kind"] != "data": continue
    ch, co = _p["anchors"]["chip"], _p["anchors"]["conn"]
    ANC[_p["page_id"]] = [tuple(ch[p]["pad_global"][:2]) for p in ("P", "N")] + [tuple(co[p]["pad_global"][:2]) for p in ("P", "N")]

def seg_gap(ax, ay, bx, by, exm):
    dx, dy = bx - ax, by - ay; L2 = max(dx * dx + dy * dy, 1e-12)
    t = np.clip(((PX - ax) * dx + (PY - ay) * dy) / L2, 0, 1)
    qx, qy = ax + t * dx, ay + t * dy
    ex = np.maximum(np.abs(qx - PX) - HX, 0); ey = np.maximum(np.abs(qy - PY) - HY, 0)
    g = np.where(CIRC, np.maximum(np.hypot(qx - PX, qy - PY) - RA, 0), np.hypot(ex, ey))
    return float(np.where(exm, np.inf, g).min())

def via_gap(vx, vy, exm):
    ex = np.maximum(np.abs(vx - PX) - HX, 0); ey = np.maximum(np.abs(vy - PY) - HY, 0)
    g = np.where(CIRC, np.maximum(np.hypot(vx - PX, vy - PY) - RA, 0), np.hypot(ex, ey))
    return float(np.where(exm, np.inf, g).min())

def check(fp, label):
    doc = json.loads(Path(fp).read_text())
    nbad = 0; worst = (9e9, None)
    for pid, pg in doc["pages"].items():
        own = ANC[pid]
        exm = np.zeros(len(PX), bool)
        for x, y in own: exm |= (np.abs(PX - x) < 0.02) & (np.abs(PY - y) < 0.02)
        for r in pg["pair_rows"]:
            px, nx, py, ny = r[0], r[1], r[2], r[3]
            # own[0]=chip P, own[1]=chip N, own[2..3]=conn P/N (manifest order)
            gs = min(seg_gap(own[0][0], own[0][1], px, py, exm), seg_gap(own[1][0], own[1][1], nx, ny, exm))
            gv = min(via_gap(px, py, exm), via_gap(nx, ny, exm))
            g = min(gs, gv)
            if g < worst[0]: worst = (g, pid)
            if g < ESC - 1e-6: nbad += 1
    print(f"{label}: pages={doc['n_pages']} rows={doc['n_rows_total']} illegal_rows={nbad} worst_gap={worst[0]:.4f} at {worst[1]}")
    return {"artifact": doc["artifact"], "sha256": hashlib.sha256(Path(fp).read_bytes()).hexdigest(),
            "pages": doc["n_pages"], "rows": doc["n_rows_total"], "illegal_rows": nbad,
            "worst_gap_mm": round(worst[0], 4), "worst_page": worst[1]}

a = check(STEP2 / "m13_v57_f13_r1_pair_coupling_v1_4.json", "v1.4")
b = check(STEP2 / "m13_v57_f13_r1_pair_coupling_v1_5.json", "v1.5")
verdict = "PASS" if (a["illegal_rows"] > 0 and b["illegal_rows"] == 0) else ("FAIL(v1.5 dirty)" if b["illegal_rows"] else "INCONCLUSIVE")
out = STEP2 / "m13_v57_f13_r1_pair_domain_v1_5_verification.json"
out.write_text(json.dumps({"artifact": "m13_v57_f13_r1_pair_domain_v1_5_verification",
    "predicate": {"via_r_mm": VIA_R, "escape_clearance_mm": ESC, "own_pads_exempt": 4},
    "v1_4": a, "v1_5": b, "verdict": verdict,
    "producer": "k2/tools/p3_v57_f13_r1_pair_domain_v1_5_verify.py"}, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
print("VERDICT:", verdict, "->", out.name, hashlib.sha256(out.read_bytes()).hexdigest()[:16])
sys.exit(0 if verdict == "PASS" else 1)
