#!/usr/bin/env python3
"""k2_pin_escape_plan_v1.py —— #K2-467／#K2-468 **引脚逃逸（pin access / escape）规划器**（纯函数 · 无 pcbnew · 零搜索）。

**补的是标准阶段**（业界每家布线器都有）：布线前给每个**未连通**端点**预留一条确定性的出线通道**（escape），
该通道随后以 `KEEPOUT`（`R1488`）**硬保留**给该网。已连通端**以其既有走线为逃逸**（`PASS-by-route` · #K2-468 §3.2）。

**owner 硬约束（绝对红线 · 写入门内）**：**禁死循环 · 禁 CPU 狂飙** ——
· 方向 **8**（正交＋45°）· 直段步梯 **20**（0.1…2.0mm）· 折线（dogleg）seg1 ≤5 步、seg2 ≤5 步、转弯 ±45°；
· **每盘候选上限 ＝ 8×20 ＋ 8×5×2×5 ＝ 560**（固定 · 无 `while` · 纯算术）；
· **逃逸须离焊盘自身铜皮**（#K2-472 §3.4(2)）：给定 `pad_rect` 时，候选**终点**须落在焊盘矩形**之外** —— 盘内短线不计；
· **局部障碍预筛（±3.5mm）** ⇒ 每候选只测邻域件 ⇒ **无 CPU 狂飙**；无外部进程 · 无后台；
· 确定性：固定方向序 ＋ 首中即取。**无候选 ⇒ 具名拒绝**（网/层/位置/已试候选数），绝不静默。
"""
from __future__ import annotations

import math

DIRS = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
NSTEPS = 20
DSEG1 = 5
DSEG2 = 5
LOCAL_R = 3.5
# 面内直段 8×20=160 ＋ 面内折线 8×5×2×5=400 ⇒ 560。
# 过孔分支经 #K2-472 §3.2 **据实关闭**（R1520 可证：其恒被面内分支包住 ⇒ 无判定力）。
CANDS_MAX = len(DIRS) * NSTEPS + len(DIRS) * DSEG1 * 2 * DSEG2      # 560
CANDS_MAX_LITERAL = 560        # 钉死（#K2-472 §3.4(3)：字面量入码，禁绑被测符号）
assert CANDS_MAX == CANDS_MAX_LITERAL, "CANDS_MAX 重导漂移（#K2-472 §3.4(3)）"


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


def _pt_in_rect(px, py, hx, hy):
    return abs(px) <= hx and abs(py) <= hy


def _seg_rect_dist(ax, ay, bx, by, hx, hy):
    """**精确**线段-轴对齐矩形距离（[-hx,hx]x[-hy,hy]；相交或内含 ⇒ 0）。**有界**（4 条边 · 无循环）。"""
    if _pt_in_rect(ax, ay, hx, hy) or _pt_in_rect(bx, by, hx, hy):
        return 0.0
    e = ((-hx, -hy, hx, -hy), (hx, -hy, hx, hy), (hx, hy, -hx, hy), (-hx, hy, -hx, -hy))
    return min(_seg_seg(ax, ay, bx, by, q[0], q[1], q[2], q[3]) for q in e)


def _seg_roundrect_dist(ax, ay, bx, by, hx, hy, r):
    """**精确**线段-圆角矩形距离。圆角矩形 ＝ 内矩形 `(hx-r, hy-r)` 与半径 `r` 圆盘之 **Minkowski 和**
    ⇒ 距离 ＝ `max(0, dist(线段, 内矩形) - r)`。`r=0` ⇒ 直角矩形；`hx=hy=r` ⇒ 圆；`r=min/2` ⇒ 胶囊。"""
    ix, iy = max(hx - r, 0.0), max(hy - r, 0.0)
    return max(0.0, _seg_rect_dist(ax, ay, bx, by, ix, iy) - r)


def _leg_clear(net, layer, p0, p1, obstacles, clear):
    """某段是否与**异网同层**障碍保持 `clear` 间距。障碍两形：**胶囊** `(net,layer,ax,ay,bx,by,hw)`（走线/过孔/
    圆/椭圆盘）与**真形圆角矩形** `(net,layer,bx0,by0,bx1,by1,0.0,"rect",cx,cy,hx,hy,r,rot)`（#K2-502：焊盘之
    矩形角必须可见，否则 45° 逃逸会擦过邻盘之角 —— R1666 实测 0.1062mm 之两处 `clearance` 即此）。"""
    (x0, y0), (x1, y1) = p0, p1
    for o in obstacles:
        if o[0] == net or o[1] != layer:
            continue
        if len(o) >= 8 and o[7] == "rect":
            cx, cy, hx, hy, rr, rot = o[8], o[9], o[10], o[11], o[12], o[13]
            a = math.radians(rot)
            c_, s_ = math.cos(a), math.sin(a)
            ux0, uy0 = x0 - cx, y0 - cy
            ux1, uy1 = x1 - cx, y1 - cy
            la0, lb0 = ux0 * c_ + uy0 * s_, -ux0 * s_ + uy0 * c_      # 变到焊盘自身坐标系（同 _pad_frame）
            la1, lb1 = ux1 * c_ + uy1 * s_, -ux1 * s_ + uy1 * c_
            if _seg_roundrect_dist(la0, lb0, la1, lb1, hx, hy, rr) < clear:
                return False
            continue
        (onet, olayer, ax, ay, bx, by, hw) = o
        if ax == bx and ay == by:
            # #K2-528: a POINT obstacle (via / drill hole wall) is measured against the WHOLE leg, not its start.
            dist = _pt_seg(ax, ay, x0, y0, x1, y1)
        else:
            dist = _seg_seg(x0, y0, x1, y1, ax, ay, bx, by)
        if dist < clear + hw:
            return False
    return True


def assets_to_keepouts(assets, kept_out_nets, clear=0.30):
    """把逃逸资产变成**硬保留**串（`R1488` `KEEPOUT` 语义：具名网**不得**使用该格 · 非代价 · 非偏好）。
    每个资产 ⇒ 对**除其自身外**的每个 `kept_out_nets` 出一条 ⇒ 该走廊**为该网独占预留**。
    保护矩形 ＝ 资产段外扩 `clear`（＝冻结判据里的间距，含走线半宽）。**确定性**（排序）· 纯算术（无 `while`）。
    返回 `["net:x0,y0,x1,y1@layer", ...]`。"""
    out = []
    for a in sorted(assets, key=lambda x: (x["net"], x["layer"], x["a"][0], x["a"][1], x["b"][0], x["b"][1])):
        x0, x1 = sorted((a["a"][0], a["b"][0]))
        y0, y1 = sorted((a["a"][1], a["b"][1]))
        r = (round(x0 - clear, 4), round(y0 - clear, 4), round(x1 + clear, 4), round(y1 + clear, 4))
        for n in sorted(set(kept_out_nets) - {a["net"]}):
            out.append("%s:%s,%s,%s,%s@%s" % (n, r[0], r[1], r[2], r[3], a["layer"]))
    return out


def pad_obstacle(net, layer, cx, cy, sx, sy, rot_deg=0.0):
    """**焊盘真形建模**（#K2-472 §3.4(1)）：细长焊盘 ⇒ **沿长轴之胶囊**（段半长 `(max-min)/2` · 半宽 `min/2`）。
    方形/圆形焊盘 ⇒ **退化为点 ＋ 半径 `min/2`** —— **绝不**用各向同性 `max/2`（R1520 之病根：细长脚被当圆盘 ⇒ 短边肥 4.92× ⇒ **造出假拒绝**）。
    `rot_deg` ＝ 焊盘自身取向（度）。返回障碍元组 `(net, layer, x1,y1, x2,y2, hw)`。"""
    long_, short_ = (sx, sy) if sx >= sy else (sy, sx)
    hw = short_ / 2.0
    h = (long_ - short_) / 2.0
    a = math.radians(rot_deg)
    c_, s_ = math.cos(a), math.sin(a)
    ux, uy = (c_, s_) if sx >= sy else (-s_, c_)          # 局部长轴单位向 → 板坐标
    return (net, layer, round(cx - ux * h, 4), round(cy - uy * h, 4),
            round(cx + ux * h, 4), round(cy + uy * h, 4), round(hw, 4))


def pad_obstacle_shape(net, layer, cx, cy, sx, sy, rot_deg=0.0, round_r=0.0):
    """#K2-502 ENGINE CAPABILITY —— **真形（圆角矩形）焊盘障碍**（`pad_obstacle` 之胶囊**内切**于焊盘 ⇒
    焊盘**矩形角**对间隙判定**隐形**：45° 逃逸步会擦过邻盘之角；实测 `MCU_VDD` 逃逸擦 `C86:2[GND]` 角，
    **精确几何 ＝ 0.1062mm ＝ KiCad DRC 自身读数**，而胶囊模型读 0.250 ⇒ 误判为净）。

    圆角矩形 ＝ 内矩形 `(hx-r, hy-r)` 与半径 `r` 圆盘之 **Minkowski 和** ⇒ `_seg_roundrect_dist` 可**精确**
    算间距；`CIRCLE/OVAL`（`r=min/2`）与 `RECT`（`r=0`）皆为其特例 ⇒ **同一表示精确覆盖全部常见焊盘形**。

    元组：`(net, layer, bx0,by0,bx1,by1, 0.0, "rect", cx, cy, hx, hy, round_r, rot_deg)` —— 2..5 为该矩形
    之 **AABB**（调用方之局部预筛沿用），7 为形状标签，`_leg_clear` 据 8..13 精确复算。间距口径与胶囊一致：
    线段到**铜皮**之距 `< clear` 即拒（`clear` 已含走线自身半宽）。**纯函数 · 无循环 · 确定性。**
    """
    hx, hy = sx / 2.0, sy / 2.0
    r = max(0.0, min(min(hx, hy), float(round_r)))
    a = math.radians(rot_deg)
    c_, s_ = math.cos(a), math.sin(a)
    ex, ey = abs(hx * c_) + abs(hy * s_), abs(hx * s_) + abs(hy * c_)
    return (net, layer, round(cx - ex, 4), round(cy - ey, 4), round(cx + ex, 4), round(cy + ey, 4), 0.0,
            "rect", cx, cy, hx, hy, r, rot_deg)


def _pad_frame(pad_rect):
    cx, cy, hx, hy = float(pad_rect[0]), float(pad_rect[1]), float(pad_rect[2]), float(pad_rect[3])
    rot = float(pad_rect[4]) if len(pad_rect) > 4 else 0.0
    a = math.radians(rot)
    return cx, cy, hx, hy, math.cos(a), math.sin(a)


def _outside_pad(pad_rect, px, py, tol=1e-9):
    """**逃逸须离焊盘自身铜皮**（#K2-472 §3.4(2)）：终点须在焊盘矩形（其自身坐标系）**之外**。"""
    cx, cy, hx, hy, c, s = _pad_frame(pad_rect)
    ux, uy = px - cx, py - cy
    u, v = ux * c + uy * s, -ux * s + uy * c
    return abs(u) > hx + tol or abs(v) > hy + tol


def escape_for_pad(net, layer, pad, obstacles, clear=0.30, max_escape_len=2.0, step=0.1, pad_rect=None):
    """返回 `{"asset":{...}|None, "refused":{...}|None}`。**有界 · 确定性**。
    `pad_rect=(cx,cy,hx,hy[,rot_deg])`：给定时，候选**终点**须落在焊盘自身铜皮**之外**（#K2-472 §3.4(2)）。"""
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
            if _leg_clear(net, layer, (x0, y0), p1, loc, clear) and (pad_rect is None or _outside_pad(pad_rect, p1[0], p1[1])):
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
                    if (_leg_clear(net, layer, (x0, y0), m, loc, clear) and _leg_clear(net, layer, m, p2, loc, clear)
                            and (pad_rect is None or _outside_pad(pad_rect, p2[0], p2[1]))):
                        return {"asset": {"net": net, "layer": layer, "a": [round(x0, 4), round(y0, 4)],
                                          "b": [round(p2[0], 4), round(p2[1], 4)],
                                          "bend": [round(m[0], 4), round(m[1], 4)],
                                          "dir": [dx, dy], "d": round(d1 + d2, 4), "dogleg": True}, "refused": None}
    return {"asset": None, "refused": {"net": net, "layer": layer, "at": [round(x0, 4), round(y0, 4)],
                                       "candidates_tried": tried,
                                       "why": "no free escape candidate (8dir + dogleg) within max_escape_len"}}


def join_for_end(net, layer, end, obstacles, targets, clear=0.30, max_len=2.0, step=0.1, tol=0.02, own=None):
    """#K2-508 ENGINE CAPABILITY —— **join 半（同层）**：把一根**单端悬空**之铜，**有界同网缝合**接上。

    `end` ＝ 该悬空端 `(x,y)`；`targets` ＝ **同网同层**之铜 `[(x1,y1,x2,y2), ...]`（点 ＝ 零长段）。
    在 **8 方向 × ≤⌊max_len/step⌋ 步**内找**直线腿**：**远端须落在某个 target 上**（≤`tol`），且**整条腿**与
    **每一个异网障碍**保持 `clear`（用**真形**间距模型 `_leg_clear`；同网障碍自动放行 ⇒ 可穿过自家铜）。
    **首中即取**（确定性）· **无候选 ⇒ 具名拒绝**（网/层/位置/已试候选数）—— 绝不静默放弃。
    这是 `R1652` 在册设计「接上或不铺」之**另一半**（prune ＝ 不铺；join ＝ 接上）。**非新机制**
    （与逃逸规划器同一套方向序与间距口径）。
    """
    x0, y0 = float(end[0]), float(end[1])
    n = min(NSTEPS, int(max_len / step))
    tried = 0
    for (dx, dy) in DIRS:
        for k in range(1, n + 1):
            tried += 1
            d = k * step
            px, py = x0 + dx * d, y0 + dy * d
            hit = None
            for (tx1, ty1, tx2, ty2) in targets:
                if _pt_seg(px, py, tx1, ty1, tx2, ty2) <= tol:
                    hit = [round(tx1, 4), round(ty1, 4), round(tx2, 4), round(ty2, 4)]
                    break
            if hit is None:
                continue
            if own is not None and _pt_seg(px, py, own[0], own[1], own[2], own[3]) <= tol:
                continue        # #K2-507(a): the far end must NOT lie on the piece we are extending from -
                                # otherwise the leg re-lays copper that is already there (a DEGENERATE join).
            if _leg_clear(net, layer, (x0, y0), (px, py), obstacles, clear):
                return {"join": {"kind": "track", "net": net, "layer": layer, "a": [round(x0, 4), round(y0, 4)],
                                 "b": [round(px, 4), round(py, 4)], "d": round(d, 4), "dir": [dx, dy], "to": hit},
                        "refused": None}
    return {"join": None, "refused": {"net": net, "layer": layer, "at": [round(x0, 4), round(y0, 4)],
                                      "candidates_tried": tried,
                                      "why": "no clear same-layer join candidate (8dir x <=%d steps)" % n}}


def via_placeable(vx, vy, via_r, existing_vias, hole_clear=0.25, reach=1.0):
    """#K2-509 sec.2 item 2 ENGINE CAPABILITY（**纯函数** · 确定性）：**新过孔可置否**。

    真短路实证（`R1702`）：join 之 `P3V3_AUX` 盲孔 `@(51.4,39.0)` **短到**既有 `PWR_BTN_OUT` 铜，且与既有
    过孔 `@(51.65,39.1)` **孔距仅 0.0193mm**（限 0.2495）——因为**钻径/孔距完全未建模**。本函数把两件事一次
    装上：**新孔之铜（半径 `via_r`）不得与既有过孔之铜（`hw`）重叠，且两者之孔壁至少留 `hole_clear`**。
    `existing_vias` ＝ 场上**全部**过孔项（元组第 6 位 ＝ 其焊盘半径）。**保守、无搜索**。
    """
    for o in (existing_vias or ()):
        if o[0] != "VIA":
            continue
        d = math.hypot(float(o[2]) - vx, float(o[3]) - vy)
        if d <= reach and d < via_r + float(o[6]) + hole_clear:
            return False
    return True


def via_join_for_end(net, layer, other_layer, end, target_pt, obstacles, span_layers,
                     clear=0.30, via_r=0.175, step=0.05, tol=0.02, existing_vias=None, hole_clear=0.25):
    """#K2-508 ENGINE CAPABILITY —— **join 半（跨层）**：以**一枚过孔**把 `end`（在 `layer`）与 `target_pt`
    （在 `other_layer`）接上。过孔位置沿 `end→target_pt` **定步长采样**（有界 · 确定性 · 首中即取）：
    须**同时搭到两端之铜**（≤`via_r+tol`）且**在所跨每一层**（`span_layers`）与**每一个异网障碍**保持净距 ——
    过孔比走线多出的半径 `max(0, via_r-0.10)` **计入**所需间距（走线自身半宽 0.10 已在 `clear` 里）。
    **无候选 ⇒ 具名拒绝。**
    """
    (x0, y0), (x1, y1) = (float(end[0]), float(end[1])), (float(target_pt[0]), float(target_pt[1]))
    L = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(math.ceil(L / max(step, 1e-6))))
    need = clear + max(0.0, via_r - 0.10)
    tried = 0
    for k in range(n + 1):
        t = k / float(n)
        vx, vy = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
        tried += 1
        if math.hypot(vx - x0, vy - y0) > via_r + tol or math.hypot(vx - x1, vy - y1) > via_r + tol:
            continue
        if not via_placeable(vx, vy, via_r, existing_vias, hole_clear):
            continue                                    # #K2-509: drill/pad proximity - never place a via too close
        if all(_leg_clear(net, LZ, (vx, vy), (vx, vy), obstacles, need) for LZ in (span_layers or (layer, other_layer))):
            return {"join": {"kind": "via", "net": net, "at": [round(vx, 4), round(vy, 4)],
                             "layers": [layer, other_layer], "from": [round(x0, 4), round(y0, 4)],
                             "to": [round(x1, 4), round(y1, 4)], "radius": via_r},
                    "refused": None}
    return {"join": None, "refused": {"net": net, "layers": [layer, other_layer],
                                      "at": [round(x0, 4), round(y0, 4)], "candidates_tried": tried,
                                      "why": "no clear via position joining %s -> %s" % (layer, other_layer)}}


def via_hop_join(net, layer, other_layer, end, target_pt, obstacles, span_layers,
                 clear=0.30, via_r=0.175, step=0.1, max_len=2.0, tol=0.02,
                 existing_vias=None, hole_clear=0.25):
    """#K2-519 sec.2 item 1 ENGINE CAPABILITY —— **双跳连接器**（`legal alt path`）。

    `R1740` 已**闭式证明**该桩（`P3V3_AUX` · `E=(51.35,39.0)` F.Cu ↔ `T=(51.55,39.0)` In5 · 既有埋孔
    `X=(51.65,39.1)`）之**单过孔族 0 解**（搭接透镜任一点距 `X` 上界 `0.39102 < ` 孔距闸 `0.65`）。
    本函数走**双跳**：`E --leg(F.Cu)--> V --via--> V --leg(In5)--> T`。

    **定序枚举**（`DIRS` × ≤`max_len/step` 步 · **首中即取** ⇒ **确定性**），每站点须**双门齐过**：
      A **孔距门** `via_placeable(V)`（距**每一**既有过孔 ≥ `via_r+hw+hole_clear`）；
      B **过孔自身净距**（所跨**每一层** · 真形 `_leg_clear` · 过孔半径差计入）；
    再验**两腿**：`leg1 = _leg_clear(layer, E→V)` · `leg2 = _leg_clear(other_layer, V→T)`（皆真形间距）。
    **无解 ⇒ 具名 fail-loud**（禁带短/带险连通充数）。
    """
    x0, y0 = float(end[0]), float(end[1])
    tx, ty = float(target_pt[0]), float(target_pt[1])
    need = clear + max(0.0, via_r - 0.10)
    n = min(NSTEPS, int(max_len / step))
    layers = tuple(span_layers or (layer, other_layer))
    for _di, (dx, dy) in enumerate(DIRS):
        for k in range(1, n + 1):
            vx, vy = x0 + dx * k * step, y0 + dy * k * step
            if not via_placeable(vx, vy, via_r, existing_vias, hole_clear):
                continue                                                     # gate A
            if not all(_leg_clear(net, LZ, (vx, vy), (vx, vy), obstacles, need) for LZ in layers):
                continue                                                     # gate B
            if not _leg_clear(net, layer, (x0, y0), (vx, vy), obstacles, clear):
                continue                                                     # leg 1
            if not _leg_clear(net, other_layer, (vx, vy), (tx, ty), obstacles, clear):
                continue                                                     # leg 2
            return {"join": {"kind": "multi", "net": net,
                             "via": {"at": [round(vx, 4), round(vy, 4)], "layers": [layer, other_layer],
                                     "radius": via_r},
                             "legs": [{"layer": layer, "a": [round(x0, 4), round(y0, 4)], "b": [round(vx, 4), round(vy, 4)]},
                                      {"layer": other_layer, "a": [round(vx, 4), round(vy, 4)], "b": [round(tx, 4), round(ty, 4)]}],
                             "candidate_index": _di * n + k},
                    "refused": None}
    return {"join": None, "refused": {"net": net, "layers": [layer, other_layer], "at": [round(x0, 4), round(y0, 4)],
                                      "why": "two-hop family exhausted: no site passes the hole gate, the all-layer "
                                             "clearance and both legs"}}


def plan_escapes(pads, obstacles, clear=0.30, max_escape_len=2.0, step=0.1):
    """`pads` **应仅含未连通端**（#K2-468 §3.2）。`go` ＝ 预检门（每端点皆有逃逸资产）。
    每条 pad ＝ `(net, layer, x, y)` 或 `(net, layer, x, y, hx, hy[, rot_deg])`（后三者＝焊盘真形半宽/半长/旋转）。"""
    assets, refused = [], []
    for pad in pads:
        net, layer, x, y = pad[0], pad[1], pad[2], pad[3]
        rect = (float(x), float(y), float(pad[4]), float(pad[5]),
                (float(pad[6]) if len(pad) > 6 else 0.0)) if len(pad) >= 6 else None
        r = escape_for_pad(net, layer, (x, y), obstacles, clear, max_escape_len, step, rect)
        (assets.append(r["asset"]) if r["asset"] else refused.append(r["refused"]))
    return {"assets": assets, "refused": refused, "go": not refused,
            "rule": "#K2-468: escape assets are required for UNCONNECTED endpoints only; connected ones pass by route",
            "bounds": {"dirs": len(DIRS), "max_steps": NSTEPS, "dogleg": [DSEG1, DSEG2],
                       "candidates_per_pad_max": CANDS_MAX, "local_filter_radius_mm": LOCAL_R,
                       "escape_must_leave_pad": True}}
