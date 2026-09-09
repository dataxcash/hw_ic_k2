#!/usr/bin/env python3
"""P3 v57 BIG — 板级意图生成器·lane 帧构造核心（设计细案 §3；正确性=构造保证）。

frame = {
  "span":   [y_lo, y_hi],          # 走廊可用 y 跨度（权威输入：板框/禁入派生）
  "margin": 0.6,                    # 带外缘到 span 端的隔离
  "pitch":  1.46,                   # 差分对中心距（capacity_audit 注入）
  "bands":  [{"id": "up", "n": 8, "edge": "lo"},
             {"id": "dn", "n": 8, "edge": "hi"}, ...],
  "refclk": {"n_pairs": 1, "layer": "In2.Cu" | "F.Cu"} | null
}

构造规则（lane 间距是摆出来的，非检查）：
  edge=lo 组：从 y_lo+margin 起向 hi 以 pitch 连续铺设（组内多带连排）；
  edge=hi 组：从 y_hi-margin 起向 lo 以 pitch 连续铺设；
  两组中心 gap ≥ pitch（带间隔离）；REFCLK(layer=In2) 需 gap ≥ 2·pitch 并落于
  lo_max+pitch 处（确定性）；REFCLK(layer=F.Cu) 不占 In2 gap（v1 再做 F.Cu 禁入谓词）。
不可行 → 量化证书 {needed_mm, avail_mm, short_mm, kind}。纯函数，序无关。
"""
from __future__ import annotations

from typing import Dict, List, Optional


def build(frame: Dict) -> Dict:
    y_lo, y_hi = frame["span"]
    m = float(frame["margin"])
    p = float(frame["pitch"])
    bands: List[Dict] = frame["bands"]
    ref = frame.get("refclk")

    lo_bs = sorted([b for b in bands if b["edge"] == "lo"], key=lambda b: b["id"])
    hi_bs = sorted([b for b in bands if b["edge"] == "hi"], key=lambda b: b["id"])

    lanes: List[Dict] = []
    cur = y_lo + m
    lo_max = None
    for b in lo_bs:
        for i in range(int(b["n"])):
            lanes.append({"band": b["id"], "y": round(cur, 4)})
            cur += p
    if lo_bs:
        lo_max = lanes[-1]["y"]
    cur = y_hi - m
    hi_min = None
    for b in hi_bs:
        for i in range(int(b["n"])):
            lanes.append({"band": b["id"], "y": round(cur, 4)})
            cur -= p
    if hi_bs:
        hi_min = lanes[-1]["y"]

    ext_lo = (sum(int(b["n"]) for b in lo_bs) - 1) * p if lo_bs else 0.0
    ext_hi = (sum(int(b["n"]) for b in hi_bs) - 1) * p if hi_bs else 0.0
    center = p if (lo_bs and hi_bs) else 0.0
    needed = m + ext_lo + center + ext_hi + m
    avail = y_hi - y_lo
    cert = None
    if avail + 1e-9 < needed:
        return {"feasible": False, "lanes": None,
                "certificate": {"kind": "lane_frame",
                                "needed_mm": round(needed, 3),
                                "avail_mm": round(avail, 3),
                                "short_mm": round(needed - avail, 3)},
                "refclk": None}
    gap = (hi_min - lo_max) if (lo_bs and hi_bs) else None
    ref_res = None
    if ref is not None:
        if ref["layer"] == "In2.Cu":
            if gap is not None and gap + 1e-9 >= 2 * p:
                ry = lo_max + p
                ref_res = {"placed": True, "layer": "In2.Cu",
                           "y": round(ry, 4),
                           "iso_lo_mm": round(ry - lo_max, 3),
                           "iso_hi_mm": round(hi_min - ry, 3)}
            else:
                short = (2 * p - gap) if gap is not None else None
                return {"feasible": False, "lanes": None,
                        "certificate": {"kind": "refclk_band",
                                        "needed_gap_mm": round(2 * p, 3),
                                        "avail_gap_mm": round(gap, 3)
                                        if gap is not None else 0.0,
                                        "short_mm": round(short, 3)
                                        if short is not None else None},
                        "refclk": None}
        else:
            ref_res = {"placed": True, "layer": "F.Cu",
                       "note": "带外直通(v0: 不占 In2; F.Cu 禁入谓词=v1)"}
    return {"feasible": True,
            "lanes": sorted(lanes, key=lambda l: l["y"]),
            "refclk": ref_res,
            "certificate": None,
            "stats": {"needed_mm": round(needed, 3),
                      "avail_mm": round(avail, 3)}}
