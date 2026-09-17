#!/usr/bin/env python3
"""K2 · P4 · 两个只读缺陷扫描器（不写仓库）。

① `nested` —— 封装**嵌套碰撞**扫描：某封装 padCu 包络严格内嵌于另一封装 padCu 包络（外层 ≥4 pad）
   ⇒ 双排封装「两排焊盘之间 = 本体」被小件占据，属**实体碰撞**（`courtyards_overlap` 因缺 courtyard 而无法触发）。
② `courtyard` —— `missing_courtyard` **口径→碰撞**曲线，按**面**补 F/B.CrtYd（修正「一律 F.CrtYd」的幻影重叠）。

用法：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_defect_scan_v1.py nested --board <b.kicad_pcb>
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_defect_scan_v1.py courtyard --board <b.kicad_pcb> --pro <同名 pro> \
      --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/scan --margins 0,0.05,0.10,0.15,0.20,0.25,0.30
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import k2_p4_w7_repair_v1 as W

NM = 1_000_000


def env(f):
    xs, ys = [], []
    for p in f.Pads():
        pp, sz = p.GetPosition(), p.GetSize()
        xs += [pp.x / NM - sz.x / NM / 2, pp.x / NM + sz.x / NM / 2]
        ys += [pp.y / NM - sz.y / NM / 2, pp.y / NM + sz.y / NM / 2]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def cmd_nested(a):
    bd = pcbnew.LoadBoard(a.board)
    fps = list(bd.GetFootprints())
    E = {f.GetReference(): env(f) for f in fps}
    padn = {f.GetReference(): len(list(f.Pads())) for f in fps}
    hits = []
    for f in fps:
        ea = E[f.GetReference()]
        if not ea:
            continue
        for g in fps:
            eb = E[g.GetReference()]
            if not eb or f is g or padn[g.GetReference()] < 4:
                continue
            if eb[0] < ea[0] and eb[1] < ea[1] and eb[2] > ea[2] and eb[3] > ea[3]:
                hits.append({"inner": f.GetReference(), "inner_pads": padn[f.GetReference()],
                             "outer": g.GetReference(), "outer_pads": padn[g.GetReference()],
                             "outer_lib": str(g.GetFPID().GetLibItemName())})
    print(json.dumps({"board": a.board, "nested_hits": len(hits), "hits": hits}, ensure_ascii=False, indent=1))
    return 0


def cmd_courtyard(a):
    os.makedirs(a.work_dir, exist_ok=True)
    base = W.stage(a.board, a.pro, a.work_dir, "scan")
    probe = os.path.join(a.work_dir, "scan.kicad_pro")
    rows = []
    for m in [float(x) for x in a.margins.split(",")]:
        bd = pcbnew.LoadBoard(base)
        add = 0
        for f in bd.GetFootprints():
            if any(g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd) for g in f.GraphicalItems()):
                continue
            lay = pcbnew.F_CrtYd if f.GetLayer() == pcbnew.F_Cu else pcbnew.B_CrtYd
            bb = f.GetBoundingBox(False, False)
            d = int(round(m * NM))
            sh = pcbnew.PCB_SHAPE(f)
            sh.SetShape(pcbnew.SHAPE_T_RECT)
            sh.SetLayer(lay)
            sh.SetStart(pcbnew.VECTOR2I(bb.GetX() - d, bb.GetY() - d))
            sh.SetEnd(pcbnew.VECTOR2I(bb.GetX() + bb.GetWidth() + d, bb.GetY() + bb.GetHeight() + d))
            sh.SetWidth(50_000)
            f.Add(sh)
            add += 1
        W.refill(bd)
        out = os.path.join(a.work_dir, f"m{int(m*1000):03d}.kicad_pcb")
        W.save_with_pro(bd, out, probe)
        rep = W.run_drc(a.kicad_cli, out, out + ".json")
        h = W.counts(rep)
        rows.append({"margin_mm": m, "added": add,
                     "missing_courtyard": h.get("warning:missing_courtyard", 0),
                     "courtyards_overlap_err": h.get("error:courtyards_overlap", 0),
                     "error_total": sum(v for k, v in h.items() if k.startswith("error:")),
                     "unconnected": W.unconn(rep)})
        print(json.dumps(rows[-1], ensure_ascii=False))
    joint = [r["margin_mm"] for r in rows if r["missing_courtyard"] == 0 and r["error_total"] == 0]
    print("[结论] missing=0 且 error=0 的口径:", joint or "**不存在**")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("nested")
    n.add_argument("--board", required=True)
    c = sub.add_parser("courtyard")
    c.add_argument("--board", required=True)
    c.add_argument("--pro", required=True)
    c.add_argument("--kicad-cli", required=True)
    c.add_argument("--work-dir", required=True)
    c.add_argument("--margins", default="0,0.05,0.10,0.15,0.20,0.25,0.30")
    a = ap.parse_args()
    return cmd_nested(a) if a.cmd == "nested" else cmd_courtyard(a)


if __name__ == "__main__":
    sys.exit(main())
