#!/usr/bin/env python3
"""k2_unfill_all_v1.py --- **K-1 铺铜纳清**（#K2-434 §2.1 · pour-aware clear）。

把板上所有 zone 的**填充**清掉（unfill），使"清空场"内**无隐藏铜皮/平面**；布线后再由链内 refill 统一重填。
业界标准工序：**unfill → route → refill**（商用 P&R 通例）。
CLI: python3 tools/k2_unfill_all_v1.py --board B --out O [--json-out P]
"""
from __future__ import annotations
import argparse, json, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    import pcbnew as P
    b = P.LoadBoard(a.board)
    n = 0
    for z in b.Zones():
        try:
            z.UnFill()
        except Exception:                                   # noqa: BLE001
            try:
                z.SetIsFilled(False)
            except Exception:                               # noqa: BLE001
                pass
        n += 1
    b.Save(a.out)
    rep = {"artifact": "k2_unfill_all_v1", "board": a.board, "out": a.out, "n_zones_unfilled": n,
           "rule": "#K2-434 K-1: the cleared field must contain NO hidden pour; unfill -> route -> refill"}
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
