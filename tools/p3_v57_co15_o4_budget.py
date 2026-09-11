#!/usr/bin/env python3
"""CO-15：O4（对内等长 ≤0.15mm）蛇形预算**重派生**（新几何下）。

模型 = 引擎 `p3_v57_w3_constructive.py` 的 O4 长度面（拓扑无关，仅几何）：
  L(pol) = |pad→via1|(F) + |escape 竖段| + |lane run| + |stub 竖段| + |landing→conn|(F)
  extra  = |L_P − L_N|；meander 置于**短极**的 lane run（R = |lx − vx|）；
  Dm = extra/(√2−1)；`meander_run` 钳位 Dm ≤ R−1 ⇒ 可吸收上限 extra_max = (R−1)(√2−1)。
  可行 ⇔ Dm ≤ R−1（等价 extra ≤ extra_max）。

只读消费 CO-15 通道分配工件；不改冻结四源。
"""
from __future__ import annotations
import json, math
from pathlib import Path

STEP2 = Path("/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2")
ALLOC = STEP2 / "m13_v57_co15_channel_allocation.json"
OUT = STEP2 / "m13_v57_co15_o4_budget.json"
S2 = math.sqrt(2) - 1.0
AMAX, AMIN, PITCH = 0.34, 0.27, 0.6


def line_len(p: dict, pol: str) -> float:
    pad = p["chip_pad"][pol]; v = p["via1"][pol]; ly = p["lane_y"][pol]
    lx, yl = p["landing"][pol]; cp = p["conn_pad"][pol]
    return (math.hypot(pad[0] - v[0], pad[1] - v[1]) + abs(ly - v[1])
            + abs(lx - v[0]) + abs(yl - ly) + math.hypot(cp[0] - lx, cp[1] - yl))


def budget(p: dict) -> dict:
    L = {q: line_len(p, q) for q in ("P", "N")}
    sh = "P" if L["P"] < L["N"] else "N"
    extra = abs(L["P"] - L["N"])
    R = abs(p["landing"][sh][0] - p["via1"][sh][0])
    dm = extra / S2
    fit = dm <= R - 1.0 + 1e-9
    n = max(1, int(round(min(dm, R - 1.0) / PITCH))) if extra > 0 else 0
    a = (min(dm, R - 1.0) / (2 * n)) if n else 0.0
    a = (min(a, AMAX) if n == 1 else min(AMAX, max(AMIN, a))) if n else 0.0
    dm_real = 2 * n * a
    absorbed = min(dm_real * S2, extra)
    return {"L_P": round(L["P"], 4), "L_N": round(L["N"], 4), "extra_mm": round(extra, 4),
            "meander_pol": sh, "R_mm": round(R, 4), "Dm_mm": round(dm, 4),
            "Dm_max_mm": round(R - 1.0, 4), "teeth_n": n, "amplitude_A": round(a, 4),
            "fit": fit, "residual_skew_mm": round(max(0.0, extra - absorbed), 6)}


def main() -> int:
    alloc = json.loads(ALLOC.read_text())
    pages, per_corr = {}, {}
    for pid, p in sorted(alloc["pages"].items()):
        b = budget(p); pages[pid] = b
        c = per_corr.setdefault(p["corridor"], {"n": 0, "max_Dm": 0.0, "min_Dm_max": 9e9,
                                                "max_extra": 0.0, "max_residual": 0.0, "all_fit": True})
        c["n"] += 1; c["max_Dm"] = max(c["max_Dm"], b["Dm_mm"])
        c["min_Dm_max"] = min(c["min_Dm_max"], b["Dm_max_mm"])
        c["max_extra"] = max(c["max_extra"], b["extra_mm"])
        c["max_residual"] = max(c["max_residual"], b["residual_skew_mm"])
        c["all_fit"] &= b["fit"]
    doc = {"artifact": "m13_v57_co15_o4_budget", "schema": 1, "revision": "CO15-O4.1",
           "threshold_intra_pair_skew_mm": 0.15,
           "model": "engine O4 length surface（拓扑无关）；meander 于短极 lane run；Dm≤R−1 判据",
           "source_allocation": {"file": ALLOC.name,
                                 "sha256": __import__("hashlib").sha256(ALLOC.read_bytes()).hexdigest()},
           "per_corridor": per_corr, "pages": pages,
           "verdict": {"WEST_MCIO_TO_CHIP": "CLOSED（预算充足）" if per_corr.get("WEST_MCIO_TO_CHIP", {}).get("all_fit") else "OPEN",
                       "EAST_CHIP_TO_J2": "CLOSED" if per_corr.get("EAST_CHIP_TO_J2", {}).get("all_fit") else "OPEN（探针模型 J2 落列过散；见 CO-15 ruling §10）"},
           "redline": "只读消费；冻结四源原件未改；无 sign-off"}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"CO15-O4.1 sha16={__import__('hashlib').sha256(OUT.read_bytes()).hexdigest()[:16]}")
    for c, v in sorted(per_corr.items()):
        print(f"  {c}: n={v['n']} all_fit={v['all_fit']} max_Dm={v['max_Dm']:.2f} min_Dm_max={v['min_Dm_max']:.2f} max_extra={v['max_extra']:.2f} max_residual={v['max_residual']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
