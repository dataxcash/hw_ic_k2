#!/usr/bin/env python3
"""k2_move_copper_v1.py --- **最小"平移铜段"动词**（#K2-420 §二 · 让位序列的落地件）。

按 (net, 起点) 精确命中既有**走线段/过孔**并**整段平移 (dx,dy)**；确定性 · 零搜索 · 只动被点名的件。
（`route --apply-batch` 只增不改、`move-parts` 只移器件 ⇒ 本件补上缺的第动词。）
CLI: python3 tools/k2_move_copper_v1.py --board B --moves "net:x1:y1:dx:dy,..." --out O [--json-out P]
"""
from __future__ import annotations
import argparse, json, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--moves", required=True, help="net:x1:y1:dx:dy,...  (x1,y1 = the segment's start point)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    import pcbnew as P
    b = P.LoadBoard(a.board)
    moves = []
    for it in [x for x in a.moves.split(",") if x]:
        n, x1, y1, dx, dy = it.split(":")
        moves.append((n, float(x1), float(y1), float(dx), float(dy)))
    hits, miss = [], []
    for (n, x1, y1, dx, dy) in moves:
        found = False
        for t in b.GetTracks():
            if t.GetNetname() != n:
                continue
            st = t.GetStart()
            if abs(P.ToMM(st.x) - x1) <= 0.01 and abs(P.ToMM(st.y) - y1) <= 0.01:
                en = t.GetEnd()
                t.SetStart(P.VECTOR2I(P.FromMM(P.ToMM(st.x) + dx), P.FromMM(P.ToMM(st.y) + dy)))
                t.SetEnd(P.VECTOR2I(P.FromMM(P.ToMM(en.x) + dx), P.FromMM(P.ToMM(en.y) + dy)))
                hits.append({"net": n, "at": [x1, y1], "move": [dx, dy]})
                found = True
                break
        if not found:
            miss.append({"net": n, "at": [x1, y1]})
    b.Save(a.out)
    rep = {"artifact": "k2_move_copper_v1", "board": a.board, "out": a.out,
           "moved": hits, "missing": miss, "rule": "#K2-420: deterministic copper translate for the yield sequence"}
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
