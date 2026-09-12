#!/usr/bin/env python3
"""CO-94：【L2 PDN 自裁】rev-10 blocked 电源/地 pad 的**可连接性闭合判定**（分析，不改 canonical）。

问题：rev-10 有 120 个 blocked，其中 34 个原为 entries（权威口径下被转 blocked）。
L2 需自裁：这 34 个在 **L2 允许的手段（外部通孔 + F.Cu 短段，无 via-in-pad/无 HDI）** 下是否**真的不可连接**？
方法（分析用）：
  - **宽松有限家族**（比决策 palette 宽，用于存在性判定；不用于决策）：8 向 × r=0.30..1.80 step 0.05；
  - 判据 = 与 CO-91 同一权威检测器：via 合法（净距+hole+层语义）**且** pad→via 短段合法（宽 0.2）。
  - 结论二值化：可连接（给出最小 r 与方向）/ 不可连接（给出绑定障碍与差额）⇒ 后者为 **L1/工艺** 升级证据。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co94_blocked_recoverability.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pcbnew

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
CO91 = K2 / "tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py"
SPEC = L3 / "SPEC_k2_v4.spec-rev-10.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT = L3 / "mcio_feas_step2/m13_v57_co94_blocked_recoverability.json"
STUB_W = 0.2
DIRS8 = [(1, 0), (0, 1), (-1, 0), (0, -1),
         (0.70710678, 0.70710678), (-0.70710678, 0.70710678),
         (0.70710678, -0.70710678), (-0.70710678, -0.70710678)]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--rmax", type=float, default=1.80)
    a = ap.parse_args(argv)
    sp = importlib.util.spec_from_file_location("co91check", CO91)
    C = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(C)
    sys.path.insert(0, str(K2.parent / "_shared"))
    import eda_core.pdn_apply as pa

    rules = C.Rules(json.loads(C.RULES.read_text()))
    board = pcbnew.LoadBoard(a.board)
    scene = C.Scene(board, rules, pa.VIA_DIA / 2, pa.VIA_DRILL / 2)
    zd = json.loads(Path(a.spec).read_text())["pd"]["zone_defs"]
    ppc = zd["power_pad_connect"]
    blocked = ppc["blocked"]
    rev9_entries = {(e["ref"], str(e["pad"]))
                    for e in ppc.get("retired_superseded_clearance_v1", {}).get("entries", [])}
    padgeo = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            x0, y0, x1, y1 = C._bb(p)
            padgeo[(fp.GetReference(), str(p.GetNumber()))] = ((x0 + x1) / 2, (y0 + y1) / 2)

    steps = int(round((a.rmax - 0.30) / 0.05)) + 1
    rows = []
    for b in sorted(blocked, key=lambda e: (e["ref"], str(e["pad"]))):
        key = (b["ref"], str(b["pad"]))
        cx, cy = padgeo[key]
        net = b["net"]
        hit, tried = None, 0
        for k in range(steps):
            r = round(0.30 + 0.05 * k, 3)
            cands = sorted((round(cx + ux * r, 3), round(cy + uy * r, 3)) for ux, uy in DIRS8
                           if 23.5 <= cx + ux * r <= 142.5 and 33.5 <= cy + uy * r <= 70.5)
            for (vx, vy) in cands:
                tried += 1
                ok_v, mv, hv, _ = scene.via_at(vx, vy, net)
                if not ok_v:
                    continue
                ok_s, ms, _ = scene.seg_clear(cx, cy, vx, vy, STUB_W, net)
                if ok_s:
                    hit = {"r": r, "via": [vx, vy], "via_margin": min(mv, hv), "stub_margin": ms}
                    break
            if hit:
                break
        if hit:
            rows.append({"ref": b["ref"], "pad": str(b["pad"]), "net": net,
                         "was_rev9_entry": key in rev9_entries, "recoverable": True, **hit})
        else:
            ok_v, mv, hv, bind = scene.via_at(cx + 0.475, cy, net)
            rows.append({"ref": b["ref"], "pad": str(b["pad"]), "net": net,
                         "was_rev9_entry": key in rev9_entries, "recoverable": False,
                         "probe_binding": bind, "probe_margin": min(mv, hv),
                         "candidates_tested": tried})

    rec9 = [r for r in rows if r["was_rev9_entry"]]
    rec = {"artifact": "m13_v57_co94_blocked_recoverability", "schema": 1, "revision": "CO-94.1",
           "nature": "L2 PDN 自裁：rev-10 blocked pad 在 L2 手段（外部通孔+短段，无 VIP/HDI）下可连接性闭合判定",
           "inputs": {"spec": Path(a.spec).name, "spec_sha16": s16(a.spec),
                      "board": Path(a.board).name, "board_sha16": s16(a.board),
                      "family": f"8 向 × r=0.30..{a.rmax} step 0.05（分析用宽松有限家族）",
                      "stub_width_mm": STUB_W},
           "summary": {"blocked_total": len(rows),
                       "recoverable": sum(1 for r in rows if r["recoverable"]),
                       "irreducible": sum(1 for r in rows if not r["recoverable"]),
                       "rev9_entries_blocked": len(rec9),
                       "rev9_entries_recoverable": sum(1 for r in rec9 if r["recoverable"]),
                       "rev9_entries_irreducible": sum(1 for r in rec9 if not r["recoverable"])},
           "rev9_entries_detail": rec9, "detail": rows,
           "verdict": "IRREDUCIBLE" if not any(r["recoverable"] for r in rec9) else "PARTIALLY_RECOVERABLE"}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(rec["summary"], ensure_ascii=False))
    print("rev9-entry blocked 中不可连接样例:",
          [(r["ref"] + "." + r["pad"], r["net"], r["probe_binding"]) for r in rec9 if not r["recoverable"]][:6])
    print("可恢复样例:", [(r["ref"] + "." + r["pad"], r["r"], r["via"]) for r in rec9 if r["recoverable"]][:6])
    return 0


if __name__ == "__main__":
    sys.exit(main())
