#!/usr/bin/env python3
"""P3 v57 BIG — 独立穷举基准（B1.1 对照方；与 lane 帧构造核心结构无关）。

同 frame 契约（见 p3_v57_big_lane_kernel.py）。独立判定：
  对 y 轴上离散候选位（从 y_lo+margin 起步长 q），用全回溯搜索给每组各 n 个
  互不相同的位（组内升序、同层任意两 lane ≥ pitch、位在 span 内），判数据带
  可行；REFCLK(In2) 再要求与全部数据 lane ≥ pitch 的独立位存在。
  无构造公式、无启发式——纯枚举，防同源自证。
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

Q = 0.1


def _cand_y(frame: Dict) -> List[float]:
    y_lo, y_hi = frame["span"]
    m = float(frame["margin"])
    out = []
    y = y_lo + m
    while y <= y_hi - m + 1e-9:
        out.append(round(y, 4))
        y += Q
    return out


def _solve_bands(frame: Dict, candidates: List[float]) -> Tuple[bool, Optional[List]]:
    p = float(frame["pitch"])
    total = sum(int(b["n"]) for b in frame["bands"])
    chosen: List[float] = []

    def rec(idx: int) -> bool:
        if len(chosen) == total:
            return True
        for i in range(idx, len(candidates)):
            y = candidates[i]
            if chosen and y - chosen[-1] + 1e-9 < p:
                continue
            chosen.append(y)
            if rec(i + 1):
                return True
            chosen.pop()
        return False

    ok = rec(0)
    return ok, (list(chosen) if ok else None)


def feasible(frame: Dict) -> Dict:
    cand = _cand_y(frame)
    p = float(frame["pitch"])
    ok_data, _ = _solve_bands(frame, cand)
    ref = frame.get("refclk")
    ref_ok = None
    if ok_data and ref is not None:
        if ref["layer"] == "In2.Cu":
            all_y = []
            _, asg = _solve_bands(frame, cand)
            if asg:
                all_y = list(asg)
            ref_ok = any(all(abs(y - c) + 1e-9 >= p for y in all_y)
                         for c in cand)
        else:
            ref_ok = True
    return {"feasible": bool(ok_data) and (ref_ok if ref_ok is not None else True),
            "data_ok": ok_data, "refclk_ok": ref_ok}
