#!/usr/bin/env python3
"""k2_remove_copper_v1.py —— #K2-499 薄 CLI 动词：确定性删除具名铜（引擎操作 · 有界 · fail-closed）。

用法：python3 tools/k2_remove_copper_v1.py --board <in.kicad_pcb> --items <items.json> --out <out.kicad_pcb>
items.json = [{"layer":"F.Cu","net":"N","a":[x,y],"b":[x,y]}...] 或 {"tracks":[...],"vias":[{"net","at":[x,y]}]}
判据：层名 ＋ 网名 ＋ 两端点（k=3）全符才删；一物未中 ⇒ 响亮失败（fail-closed）。
落盘：在册模板（pcbnew.SaveBoard(out,b) ＋ .kicad_pro/.kicad_dru 伴生传导 · 承 route.py:487）。
"""
from __future__ import annotations
import argparse, json, os, shutil, sys
import pcbnew as P
MM = P.ToMM
def _load_items(path):
    raw = json.load(open(path, encoding="utf-8"))
    if isinstance(raw, list):
        return {"tracks": [x for x in raw if "a" in x], "vias": [x for x in raw if "at" in x]}
    return {"tracks": raw.get("tracks") or [], "vias": raw.get("vias") or []}
def remove(board_in, board_out, spec):
    b = P.LoadBoard(board_in)
    want_t = {(t["layer"], t["net"], round(float(t["a"][0]),3), round(float(t["a"][1]),3),
               round(float(t["b"][0]),3), round(float(t["b"][1]),3)) for t in spec["tracks"]}
    want_v = {(v["net"], round(float(v["at"][0]),3), round(float(v["at"][1]),3)) for v in spec["vias"]}
    nt = nv = 0
    for t in list(b.GetTracks()):
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            if (t.GetNetname(), round(MM(p.x),3), round(MM(p.y),3)) in want_v:
                b.Remove(t); nv += 1
            continue
        s, e = t.GetStart(), t.GetEnd()
        if (b.GetLayerName(t.GetLayer()), t.GetNetname(), round(MM(s.x),3), round(MM(s.y),3),
                round(MM(e.x),3), round(MM(e.y),3)) in want_t:
            b.Remove(t); nt += 1
    if not (nt or nv):
        raise RuntimeError("k2: remove-copper matched NOTHING - refusing a silent no-op (fail-closed)")
    P.SaveBoard(board_out, b)
    in_stem, out_stem = os.path.splitext(board_in)[0], os.path.splitext(board_out)[0]
    carried = []
    for ext in (".kicad_pro", ".kicad_dru"):
        if os.path.isfile(in_stem + ext):
            shutil.copy(in_stem + ext, out_stem + ext); carried.append(ext)
    return {"artifact": "k2_remove_copper_v1", "removed_tracks": nt, "removed_vias": nv,
            "n_requested": len(spec["tracks"]) + len(spec["vias"]), "sidecars_carried": carried, "out": board_out}
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--items", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    print(json.dumps(remove(a.board, a.out, _load_items(a.items)), ensure_ascii=False))
    return 0
if __name__ == "__main__":
    sys.exit(main())
