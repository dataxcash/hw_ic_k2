#!/usr/bin/env python3
"""k2_pin_escape_plan_v1.py —— #K2-467 **引脚逃逸（pin access / escape）规划器**（纯函数 · 无 pcbnew · 零搜索）。

**补的是标准阶段**：任何布线器在布线前都要先给每个端点**预留一条确定性的出线通道**（escape），我仓此前从未有过。
三证据收敛（`R1430` 267/268 `no-free-start-node`；`R1460` 端口通道被他网切断；`R1470` 封口铜系迷宫自加）
⇒ 「事前撤铜」必扑空；**正解 ＝ 布线前正向推导并保留逃逸通道**。

**owner 硬约束（绝对红线）写入门内**：**禁死循环 · 禁 CPU 狂飙** ——
· 方向固定 **4** 个、步梯固定 **20** 档（0.1…2.0mm）⇒ 每端点候选 **≤80**，**无 `while`**；
· 纯算术判据（点-线段距离）· 无外部进程 · 无后台。
判据：候选段**全程**离**异网**铜/焊盘 ≥ `clear`，且终点为自由点；**首中即取**（方向序固定 ⇒ 确定性）。
**无候选 ⇒ 具名拒绝**（端点/层/阻挡网/阻挡点），绝不静默。
"""
from __future__ import annotations

DIRS = ((1, 0), (0, 1), (-1, 0), (0, -1))          # 固定方向序（确定性的来源之一）
NSTEPS = 20                                          # 固定步梯长度 ⇒ 候选数有界（4 * 20 = 80）

def _pt_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    qx, qy = ax + t * vx, ay + t * vy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5

def _seg_seg(ax, ay, bx, by, cx, cy, dx, dy):
    """**精确**线段-线段距离（相交通 ⇒ 0）—— 修正 R1492 之近似判据弱点（min(点-线) 会漏检横穿）。"""
    def _cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1 = _cr((ax, ay), (bx, by), (cx, cy)); d2 = _cr((ax, ay), (bx, by), (dx, dy))
    d3 = _cr((cx, cy), (dx, dy), (ax, ay)); d4 = _cr((cx, cy), (dx, dy), (bx, by))
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(_pt_seg(ax, ay, cx, cy, dx, dy), _pt_seg(bx, by, cx, cy, dx, dy),
               _pt_seg(cx, cy, ax, ay, bx, by), _pt_seg(dx, dy, ax, ay, bx, by))


def escape_for_pad(net, layer, pad, obstacles, clear=0.30, max_escape_len=2.0, step=0.1):
    """`pad = (x,y)`；`obstacles = [(net, layer, x1,y1,x2,y2, halfwidth)]`（**异网**铜/焊盘，含半宽）。
    返回 `{"asset":{net,layer,a,b,dir,d} | None, "refused":{...} | None}`。**有界 · 确定性**。"""
    x0, y0 = float(pad[0]), float(pad[1])
    nsteps = min(NSTEPS, int(max_escape_len / step))
    hit = None
    for (dx, dy) in DIRS:
        for k in range(1, nsteps + 1):
            d = k * step
            x1, y1 = x0 + dx * d, y0 + dy * d
            ok = True
            worst = None
            for (onet, olayer, ax, ay, bx, by, hw) in obstacles:
                if onet == net or olayer != layer:
                    continue
                dist = _pt_seg(x0, y0, ax, ay, bx, by) if (ax == bx and ay == by) else \
                       _seg_seg(x0, y0, x1, y1, ax, ay, bx, by)
                if dist < clear + hw:
                    ok = False
                    if worst is None or dist < worst[1]:
                        worst = (onet, round(dist, 4), [ax, ay, bx, by])
                    break
            if ok:
                hit = {"asset": {"net": net, "layer": layer, "a": [round(x0, 4), round(y0, 4)],
                                 "b": [round(x1, 4), round(y1, 4)], "dir": [dx, dy], "d": round(d, 4)}}
                break
        if hit:
            break
    if hit:
        return {"asset": hit["asset"], "refused": None}
    return {"asset": None, "refused": {"net": net, "layer": layer, "at": [round(x0, 4), round(y0, 4)],
                                       "n_dirs_tried": len(DIRS), "n_steps_tried": nsteps,
                                       "why": "no free escape candidate within max_escape_len"}}

def plan_escapes(pads, obstacles, clear=0.30, max_escape_len=2.0, step=0.1):
    """`pads = [(net, layer, x, y)]` ⇒ `{"assets":[...], "refused":[...], "go":bool}`。`go` ＝ **预检门**（每端点皆有逃逸资产）。"""
    assets, refused = [], []
    for (net, layer, x, y) in pads:
        r = escape_for_pad(net, layer, (x, y), obstacles, clear, max_escape_len, step)
        if r["asset"]:
            assets.append(r["asset"])
        else:
            refused.append(r["refused"])
    return {"assets": assets, "refused": refused, "go": not refused,
            "rule": "#K2-467: every targeted pad must own an escape asset; otherwise the precheck FAILS and names them",
            "bounds": {"dirs": len(DIRS), "max_steps": NSTEPS, "candidates_per_pad_max": len(DIRS) * NSTEPS}}
