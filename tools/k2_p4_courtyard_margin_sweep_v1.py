#!/usr/bin/env python3
"""K2 · P4 · `missing_courtyard` **外扩口径 → 碰撞** 曲线（只读测量；不写仓库）。

对 margin ∈ {0.00,0.05,...,0.30} mm：为缺 courtyard 的封装补 F.CrtYd 矩形（本体/pad 外框 + m），
再跑 DRC 记录 `missing_courtyard` 与 `courtyards_overlap`（error）等计数。
目的：给监理 §4-1 / 裁定项④ 一个「口径 vs 新增 error」的确定性曲线（含是否存在 m 使两者同 0）。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys

import pcbnew

RT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "k2_p4_w7_repair_v1.py")
spec = importlib.util.spec_from_file_location("rt", RT)
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default="k2/hw/k2_v4_8L.l5.kicad_pcb")
    ap.add_argument("--pro", default="k2/hw/k2_v4_8L.l5.kicad_pro")
    ap.add_argument("--kicad-cli", default="AppDir/bin/kicad-cli")
    ap.add_argument("--work-dir", default="/tmp/opencode/crtsweep")
    ap.add_argument("--margins", default="0,0.05,0.10,0.15,0.20,0.25,0.30")
    a = ap.parse_args()

    os.makedirs(a.work_dir, exist_ok=True)
    base = rt.stage(a.board, a.pro, a.work_dir, "k2_v4_8L.l5")
    probe = os.path.join(a.work_dir, "k2_v4_8L.l5.kicad_pro")
    rows = []
    for m in [float(x) for x in a.margins.split(",")]:
        bd, idx = rt.load_idx(base)
        bd = pcbnew.LoadBoard(base)
        added = 0
        for f in bd.GetFootprints():
            has = any(g.GetLayer() == pcbnew.F_CrtYd for g in f.GraphicalItems())
            if has:
                continue
            bb = f.GetBoundingBox(False, False)
            d = int(round(m * 1_000_000))
            sh = pcbnew.PCB_SHAPE(f)
            sh.SetShape(pcbnew.SHAPE_T_RECT)
            sh.SetLayer(pcbnew.F_CrtYd)
            sh.SetStart(pcbnew.VECTOR2I(bb.GetX() - d, bb.GetY() - d))
            sh.SetEnd(pcbnew.VECTOR2I(bb.GetX() + bb.GetWidth() + d,
                                      bb.GetY() + bb.GetHeight() + d))
            sh.SetWidth(50_000)
            f.Add(sh)
            added += 1
        rt.refill(bd)
        out = os.path.join(a.work_dir, f"crtyd_m{int(m*1000):03d}.kicad_pcb")
        rt.save_with_pro(bd, out, probe)
        rep = rt.run_drc(a.kicad_cli, out, out + ".json")
        h = rt.counts(rep)
        rows.append({"margin_mm": m, "added": added,
                     "missing_courtyard": h.get("warning:missing_courtyard", 0),
                     "courtyards_overlap_err": h.get("error:courtyards_overlap", 0),
                     "pth_inside_courtyard": h.get("error:pth_inside_courtyard", 0),
                     "error_total": sum(v for k, v in h.items() if k.startswith("error:")),
                     "unconnected": rt.unconn(rep), "hist": h})
        print(json.dumps(rows[-1], ensure_ascii=False))
    with open(os.path.join(a.work_dir, "sweep.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    joint = [r for r in rows if r["missing_courtyard"] == 0 and r["error_total"] == 0]
    print("\n[结论] 使 `missing_courtyard=0` 且 `error=0` 的口径：",
          [r["margin_mm"] for r in joint] or "**不存在**（两者不可同时为 0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
