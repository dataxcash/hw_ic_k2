#!/usr/bin/env python3
"""k2_pin_escape_plan_v1.py —— #K2-467／#K2-468 **引脚逃逸（pin access / escape）规划器**（纯函数 · 无 pcbnew · 零搜索）。

**补的是标准阶段**（业界每家布线器都有）：布线前给每个**未连通**端点**预留一条确定性的出线通道**（escape），
该通道随后以 `KEEPOUT`（`R1488`）**硬保留**给该网。已连通端**以其既有走线为逃逸**（`PASS-by-route` · #K2-468 §3.2）。

**owner 硬约束（绝对红线 · 写入门内）**：**禁死循环 · 禁 CPU 狂飙** ——
· 方向 **8**（正交＋45°）· 直段步梯 **20**（0.1…2.0mm）· 折线（dogleg）seg1 ≤5 步、seg2 ≤5 步、转弯 ±45°；
· **每盘候选上限 ＝ 8×20 ＋ 8×5×2×5 ＝ 560**（固定 · 无 `while` · 纯算术）；
· **局部障碍预筛（±3.5mm）** ⇒ 每候选只测邻域件 ⇒ **无 CPU 狂飙**；无外部进程 · 无后台；
· 确定性：固定方向序 ＋ 首中即取。**无候选 ⇒ 具名拒绝**（网/层/位置/已试候选数），绝不静默。
"""
from __future__ import annotations

DIRS = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
NSTEPS = 20
DSEG1 = 5
DSEG2 = 5
LOCAL_R = 3.5
CANDS_MAX = len(DIRS) * NSTEPS + len(DIRS) * DSEG1 * 2 * DSEG2      # 560


def _pt_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    qx, qy = ax + t * vx, ay + t * vy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def _seg_seg(ax, ay, bx, by, cx, cy, dx, dy):
    """**精确**线段-线段距离（相交通 ⇒ 0）。"""
    def _cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1 = _cr((ax, ay), (bx, by), (cx, cy)); d2 = _cr((ax, ay), (bx, by), (dx, dy))
    d3 = _cr((cx, cy), (dx, dy), (ax, ay)); d4 = _cr((cx, cy), (dx, dy), (bx, by))
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(_pt_seg(ax, ay, cx, cy, dx, dy), _pt_seg(bx, by, cx, cy, dx, dy),
               _pt_seg(cx, cy, ax, ay, bx, by), _pt_seg(dx, dy, ax, ay, bx, by))


def _leg_clear(net, layer, p0, p1, obstacles, clear):
    (x0, y0), (x1, y1) = p0, p1
    for (onet, olayer, ax, ay, bx, by, hw) in obstacles:
        if onet == net or olayer != layer:
            continue
        dist = _pt_seg(x0, y0, ax, ay, bx, by) if (ax == bx and ay == by) else _seg_seg(x0, y0, x1, y1, ax, ay, bx, by)
        if dist < clear + hw:
            return False
    return True


def escape_for_pad(net, layer, pad, obstacles, clear=0.30, max_escape_len=2.0, step=0.1):
    """返回 `{"asset":{...}|None, "refused":{...}|None}`。**有界 · 确定性**。"""
    x0, y0 = float(pad[0]), float(pad[1])
    lim = LOCAL_R + max_escape_len
    loc = [o for o in obstacles
           if (abs(o[2] - x0) <= lim and abs(o[3] - y0) <= lim) or (abs(o[4] - x0) <= lim and abs(o[5] - y0) <= lim)]
    nsteps = min(NSTEPS, int(max_escape_len / step))
    tried = 0
    for (dx, dy) in DIRS:                                     # ① 直段（8 向 × ≤20 步）
        for k in range(1, nsteps + 1):
            tried += 1
            d = k * step
            p1 = (x0 + dx * d, y0 + dy * d)
            if _leg_clear(net, layer, (x0, y0), p1, loc, clear):
                return {"asset": {"net": net, "layer": layer, "a": [round(x0, 4), round(y0, 4)],
                                  "b": [round(p1[0], 4), round(p1[1], 4)], "dir": [dx, dy], "d": round(d, 4),
                                  "dogleg": False}, "refused": None}
    for (dx, dy) in DIRS:                                     # ② 两段折线 dogleg（±45° 转）
        for k1 in range(1, DSEG1 + 1):
            d1 = k1 * step
            m = (x0 + dx * d1, y0 + dy * d1)
            for s in (1, -1):
                tx, ty = (dx - s * dy, dy + s * dx)
                for k2 in range(1, DSEG2 + 1):
                    tried += 1
                    d2 = k2 * step
                    p2 = (m[0] + tx * d2, m[1] + ty * d2)
                    if abs(p2[0] - x0) > max_escape_len or abs(p2[1] - y0) > max_escape_len:
                        continue
                    if _leg_clear(net, layer, (x0, y0), m, loc, clear) and _leg_clear(net, layer, m, p2, loc, clear):
                        return {"asset": {"net": net, "layer": layer, "a": [round(x0, 4), round(y0, 4)],
                                          "b": [round(p2[0], 4), round(p2[1], 4)],
                                          "bend": [round(m[0], 4), round(m[1], 4)],
                                          "dir": [dx, dy], "d": round(d1 + d2, 4), "dogleg": True}, "refused": None}
    return {"asset": None, "refused": {"net": net, "layer": layer, "at": [round(x0, 4), round(y0, 4)],
                                       "candidates_tried": tried,
                                       "why": "no free escape candidate (8dir + dogleg) within max_escape_len"}}


def plan_escapes(pads, obstacles, clear=0.30, max_escape_len=2.0, step=0.1):
    """`pads` **应仅含未连通端**（#K2-468 §3.2）。`go` ＝ 预检门（每端点皆有逃逸资产）。"""
    assets, refused = [], []
    for (net, layer, x, y) in pads:
        r = escape_for_pad(net, layer, (x, y), obstacles, clear, max_escape_len, step)
        (assets.append(r["asset"]) if r["asset"] else refused.append(r["refused"]))
    return {"assets": assets, "refused": refused, "go": not refused,
            "rule": "#K2-468: escape assets are required for UNCONNECTED endpoints only; connected ones pass by route",
            "bounds": {"dirs": len(DIRS), "max_steps": NSTEPS, "dogleg": [DSEG1, DSEG2],
                       "candidates_per_pad_max": CANDS_MAX, "local_filter_radius_mm": LOCAL_R}}
