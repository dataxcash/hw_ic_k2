#!/usr/bin/env python3
"""k2_clearance_v1.py --- **via-aware 净空闸**（#K2-448 sec.2.5(1) · 由 R1358 的教训机读化）。

WHY：R1358 查出一次**假 clean** —— 净空扫描按 `GetLayer()` **单层**过滤，**漏掉过孔**；而过孔**覆盖其层对之间的每一层**
（那个 `In2-In5` 的 HS 盲孔在 `In4` 上同样有铜）⇒ 桥线短路了它却没人发现。本模块把「**过孔覆盖哪些层**」变成**纯函数**，
供检查器与回归共用；并显式声明**未跑 DRC 不得宣称 clean**。
"""
from __future__ import annotations

STACK = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]


def via_layer_span(la, lb, stack=None):
    """**纯函数**：过孔覆盖的层 = 层对内**每一层**（含两端）。**不得**退回单层 `GetLayer()`。"""
    st = list(stack or STACK)
    i, j = st.index(la), st.index(lb)
    lo, hi = min(i, j), max(i, j)
    return st[lo:hi + 1]


def obstacle_layers(ob, stack=None):
    """障碍物覆盖的层集合：过孔 ⇒ 层对全跨；线段/焊盘 ⇒ 其层。"""
    if ob.get("kind") == "via":
        return set(via_layer_span(ob["layers"][0], ob["layers"][1], stack))
    return set(ob.get("layers") or [])


def seg_blocked(a, b, layer, obstacles, width=0.25, clearance=0.20, stack=None):
    """**纯函数**：段 `a..b` 在 `layer` 上是否被任一障碍物（**含过孔全跨**）以 `clearance+width/2` 拦住。"""
    inf = width / 2.0 + clearance
    x0, x1 = min(a[0], b[0]) - inf, max(a[0], b[0]) + inf
    y0, y1 = min(a[1], b[1]) - inf, max(a[1], b[1]) + inf
    for ob in obstacles:
        if layer not in obstacle_layers(ob, stack):
            continue
        l, t, r, bo = ob["bbox"]
        dx = max(l - x1, x0 - r, 0.0)
        dy = max(t - y1, y0 - bo, 0.0)
        if (dx * dx + dy * dy) ** 0.5 <= 1e-9:
            return True
    return False


CLEAN_CLAIM_RULE = ("a state may only be called CLEAN after an actual DRC run on the built field; "
                    "and any clearance check MUST enumerate every layer a via covers (#K2-448 sec.2.5(1)).")
