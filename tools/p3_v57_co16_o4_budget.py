#!/usr/bin/env python3
"""CO-16：O4 蛇形预算（**lane run + stub 双段**模型，全板）。

CO-15 模型只在 lane run 上放蛇形；CO-16 东侧在 CO-09 拓扑下 lane-run 容量不足（DN1/DN2 短 1.8~4.4mm），
故把蛇形扩展到第二段（stub 竖段）：capacity = (R_lane−1 + max(0,R_stub−1))·(√2−1)。
西侧容量充裕，双段模型不改变其结论。只读消费 CO-16 分配工件。
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path

STEP2 = Path("/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2")
ALLOC = STEP2 / "m13_v57_co16_channel_allocation.json"
OUT = STEP2 / "m13_v57_co16_o4_budget.json"
S2 = math.sqrt(2) - 1.0
AMAX, AMIN, PITCH = 0.34, 0.27, 0.6


def main() -> int:
    alloc = json.loads(ALLOC.read_text())
    pages, per_corr = {}, {}
    for pid, p in sorted(alloc["pages"].items()):
        L = {}
        for pol in ("P", "N"):
            pad = p["chip_pad"][pol]; v = p["via1"][pol]; ly = p["lane_y"][pol]
            lx, ll = p["landing"][pol]; cp = p["conn_pad"][pol]
            L[pol] = (math.hypot(pad[0] - v[0], pad[1] - v[1]) + abs(ly - v[1])
                      + abs(lx - v[0]) + abs(ll - ly) + math.hypot(cp[0] - lx, cp[1] - ll))
        sh = "P" if L["P"] < L["N"] else "N"
        extra = abs(L["P"] - L["N"])
        R_lane = abs(p["landing"][sh][0] - p["via1"][sh][0])
        R_stub = abs(p["landing"][sh][1] - p["lane_y"][sh])
        cap_lane = (R_lane - 1.0) * S2
        cap = (R_lane - 1.0 + max(0.0, R_stub - 1.0)) * S2
        rec = {"L_P": round(L["P"], 4), "L_N": round(L["N"], 4), "extra_mm": round(extra, 4),
               "meander_pol": sh, "R_lane_mm": round(R_lane, 4), "R_stub_mm": round(R_stub, 4),
               "cap_lane_only_mm": round(cap_lane, 4), "cap_lane_plus_stub_mm": round(cap, 4),
               "slack_lane_only_mm": round(cap_lane - extra, 4),
               "slack_mm": round(cap - extra, 4), "fit": cap >= extra - 1e-9}
        pages[pid] = rec
        c = per_corr.setdefault(p["corridor"], {"n": 0, "all_fit": True, "min_slack": 9e9, "max_extra": 0.0})
        c["n"] += 1; c["all_fit"] &= rec["fit"]; c["min_slack"] = min(c["min_slack"], rec["slack_mm"])
        c["max_extra"] = max(c["max_extra"], rec["extra_mm"])
    doc = {"artifact": "m13_v57_co16_o4_budget", "schema": 1, "revision": "CO16-O4.1",
           "threshold_intra_pair_skew_mm": 0.15,
           "model": "capacity = (R_lane−1 + max(0,R_stub−1))·(√2−1)；meander 置于短极 lane-run + stub 竖段",
           "source_allocation": {"file": ALLOC.name,
                                 "sha256": hashlib.sha256(ALLOC.read_bytes()).hexdigest()},
           "per_corridor": per_corr, "pages": pages,
           "verdict": {c: ("CLOSED" if v["all_fit"] else "OPEN") for c, v in per_corr.items()},
           "redline": "只读消费；冻结四源原件未改；无 sign-off"}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"CO16-O4.1 sha16={hashlib.sha256(OUT.read_bytes()).hexdigest()[:16]}")
    for c, v in sorted(per_corr.items()):
        print(f"  {c}: n={v['n']} all_fit={v['all_fit']} max_extra={v['max_extra']:.2f} min_slack={v['min_slack']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
