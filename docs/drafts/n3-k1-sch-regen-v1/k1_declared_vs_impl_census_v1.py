#!/usr/bin/env python3
"""k1_declared_vs_impl_census_v1 — K1『声明值 vs 实现符号』漂移普查（只读）。

动机：`k1_sch_sync_v1.py` 只改 **真源 yaml**（`k1_board.yaml`/`k1_nets.yaml`），不改
`k1/boards/k1_sch.yaml` 的原理图符号 ⇒ 声明值被更新而**实现未跟随**时产生静默漂移。
本脚本逐件比对：`k1_board.yaml#devices[ref].value` ↔ 该 ref 所用 symbol 的 `value`
（footprint 另列），并输出漂移清单。
用法：python3 k1_declared_vs_impl_census_v1.py [--json]
返回码：0（普查工具；不判 gate）。
"""
from __future__ import annotations
import argparse, json, os, sys, yaml

ROOT = "/home/fila/jqdDev_2025/ic_hw"


def bn(x):
    return str(x or "").split(":")[-1]


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    dev = (yaml.safe_load(open(f"{ROOT}/k1/boards/k1_board.yaml", encoding="utf-8")) or {}).get("devices") or {}
    sch = yaml.safe_load(open(f"{ROOT}/k1/boards/k1_sch.yaml", encoding="utf-8")) or {}
    sym = {s.get("name"): s for s in (sch.get("symbols") or [])}
    pl = {}
    for sh in sch.get("sheets") or []:
        for p in sh.get("placements") or []:
            pl[p.get("ref")] = p.get("symbol")
    rows = []
    for ref in sorted(dev):
        sname = pl.get(ref)
        s = sym.get(sname) if sname else None
        dv, sv = str(dev[ref].get("value")), (str(s.get("value")) if s else None)
        dfp, sfp = bn(dev[ref].get("footprint")), (bn(s.get("footprint")) if s else None)
        if dv != sv or dfp != sfp:
            rows.append({"ref": ref, "declared_value": dv, "impl_symbol": sname, "impl_value": sv,
                         "declared_fp": dfp, "impl_fp": sfp,
                         "value_mismatch": dv != sv, "fp_mismatch": dfp != sfp,
                         "missing_placement": sname is None})
    out = {"n_devices": len(dev), "n_mismatch": len(rows), "rows": rows}
    print(json.dumps(out, ensure_ascii=False, indent=1) if a.json else
          f"声明/实现漂移 {len(rows)}/{len(dev)} 件：{ [r['ref'] for r in rows] }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
