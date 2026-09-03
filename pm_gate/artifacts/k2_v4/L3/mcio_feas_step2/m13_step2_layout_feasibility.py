#!/usr/bin/env python3
"""
m13_step2_layout_feasibility.py — K2 MCIO 布局可行性几何求解（四层框架第 2 步）

权威输入：
  - 真板 k2_v4.kicad_pcb（BoardParser 解析，几何唯一真源）
  - 任务给定求解要素（全确定性，勿改）：
      via 占位 0.55mm（外径0.35 + 净空0.1×2）
      差分对成对约束：P/N via 中心距 ≤ 1~2mm
      对间净空 0.875mm
      换层点必须落在电容下游且 P/N 成对
  - SPEC vias.high_speed.pad_edge_clearance_mm = 0.3（no_via_in_pad，via 中心到 pad 边）

求解内容（可复算）：
  1. 换层点可行域（每线下游 x 界 + 走廊 y 界 + 障碍净空）
  2. 8 对差分线换层点最小空间需求（最小 x 列数 / 最小 y 跨距）
  3. 与摆件供给（电容右缘→U3 左缘 x 宽、两行电容间走廊 y 高）的差量
"""
from __future__ import annotations
import sys, math, json
from dataclasses import dataclass, field

SHARED = "/home/fila/jqdDev_2025/ic_hw/_shared"
sys.path.insert(0, SHARED)
from eda_core.drc_rules import BoardParser

BOARD = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"

# ── 任务给定规则（确定性）────────────────────────────
VIA_OCC = 0.55          # via 占位直径（含 clearance）
VIA_R = VIA_OCC / 2     # via keepout 半径 0.275
PN_MAX = 2.0            # 差分对成对：P/N via 中心距上限
PN_MIN = VIA_OCC        # P/N via 中心距下限（keepout 不重叠）
INTER_PAIR = 0.875      # 对间净空
PAD_EDGE_CLR = 0.3      # SPEC no_via_in_pad：via 边缘距 pad ≥ 0.3
# via 中心到 pad 边 = via 半径 + pad_edge_clearance（LandingRules.required 同源）
VIA_CENTER_PAD = VIA_OCC / 2 + PAD_EDGE_CLR   # 0.175 + 0.3 = 0.475

# 几何对象
def pad_rect(p):
    """pad → (x0,y0,x1,y1) 铜矩形（含旋转近似：0402 全 0 度，pad 0.4×0.5 无旋转）"""
    w, h = p.size
    return (p.pos[0] - w/2, p.pos[1] - h/2, p.pos[0] + w/2, p.pos[1] + h/2)

def rect_clear_dist(px, py, r):
    """点到矩形距离（点在外为正，内为负）"""
    x0,y0,x1,y1 = r
    dx = max(x0 - px, 0, px - x1)
    dy = max(y0 - py, 0, py - y1)
    return math.hypot(dx, dy)

def main():
    b = BoardParser(BOARD).parse()
    # ── 1. 电容墙 pad（C17-C32 全 16 颗 0402，每颗 2 pad：_U3 下游 / _MCIO 上游）
    #    下游 pad = net 尾 _U3（信号穿电容后向 U3 行进侧）
    cap_down = {}   # ref -> (net, x, y)
    cap_up   = {}
    cap_refs = [f"C{i}" for i in range(17, 33)]
    for p in b.pads:
        if p.footprint_ref in cap_refs:
            n = p.net or ""
            if n.endswith("_U3"):
                cap_down[p.footprint_ref] = (n, p.pos[0], p.pos[1])
            elif n.endswith("_MCIO"):
                cap_up[p.footprint_ref] = (n, p.pos[0], p.pos[1])
    print(f"[1] 电容墙下游(_U3) pad 数: {len(cap_down)} / 16")
    # 网 → cap 映射
    net2cap = {v[0]: (k, v[1], v[2]) for k, v in cap_down.items()}
    dn_nets = sorted(n for n in net2cap if n.startswith("PCIE_DN_OUT"))
    print(f"[1] DN_OUT 下游网数: {len(dn_nets)}")
    for n in dn_nets:
        ref, x, y = net2cap[n]
        print(f"      {n:34s} cap {ref} down_pad=({x:.3f},{y:.3f})")

    # ── 2. 电容墙整体下游 x 界（wall +x 铜边缘 = 全部 pad 的 +x 铜边最大）
    wall_x1 = 0.0
    cap_rects = []
    for p in b.pads:
        if p.footprint_ref in cap_refs:
            r = pad_rect(p)
            cap_rects.append(r)
            wall_x1 = max(wall_x1, r[2])
    wall_x0 = min(r[0] for r in cap_rects)
    print(f"\n[2] 电容墙 x 跨度铜边: [{wall_x0:.3f}, {wall_x1:.3f}]  宽 {wall_x1-wall_x0:.3f} mm")

    # U3 左侧信号列 pad（PCIE_DN_OUT*_U3 在 U3 上 = x=88.825 列）
    u3_rects = []
    for p in b.pads:
        if p.footprint_ref == "U3":
            r = pad_rect(p)
            u3_rects.append(r)
    u3_x0 = min(r[0] for r in u3_rects)     # U3 铜左缘
    u3_y0 = min(r[1] for r in u3_rects)
    u3_y1 = max(r[3] for r in u3_rects)
    print(f"[2] U3 铜: 左缘 x={u3_x0:.3f}  y 跨度 [{u3_y0:.3f},{u3_y1:.3f}]")

    # 两行电容：行 y（57.8 上 C17-24 / 68.0 下 C25-32）与走廊
    row1_y = 57.8; row2_y = 68.0
    # pad 0.5 高 → 行 1 pad y ∈ [57.55,58.05], 行 2 [67.75,68.25]
    # 走廊净空 y（pad 铜边到 pad 铜边）
    corr_y0 = row1_y + 0.25   # 58.05
    corr_y1 = row2_y - 0.25   # 67.75
    print(f"[2] 两行电容之间走廊 y(铜边净空): [{corr_y0:.3f}, {corr_y1:.3f}] 高 {corr_y1-corr_y0:.3f} mm"
          f"（行心距 {row2_y-row1_y:.1f}）")

    # ── 3. 换层点可行域（via 中心）
    #   x：下游须 ≥ 墙右铜边 + via_center_pad；且 ≤ U3 左缘 - via_center_pad
    x_lo = wall_x1 + VIA_CENTER_PAD     # 85.15 + 0.475
    x_hi = u3_x0 - VIA_CENTER_PAD       # 88.6 - 0.475
    print(f"\n[3] 换层点 x 可行域: via 中心 ∈ [{x_lo:.3f}, {x_hi:.3f}]  宽 {x_hi-x_lo:.3f} mm")
    print(f"    （任务供给口径 电容右缘85.15→U3左缘88.6 = 3.45mm；净空后 {x_hi-x_lo:.2f}mm）")

    #   y：走廊内，避开两行电容 pad（0.5 高）via keepout + clearance
    #     via 中心须距上排 pad 底边 ≥ 0.275+... 用 VIA_CENTER_PAD 保守（pad_edge_clearance 语义）
    y_lo = corr_y0 + VIA_CENTER_PAD   # 58.05+0.475
    y_hi = corr_y1 - VIA_CENTER_PAD   # 67.75-0.475
    print(f"[3] 换层点 y 可行域（走廊内两行电容 pad 净空）: via 中心 ∈ [{y_lo:.3f}, {y_hi:.3f}]"
          f"  高 {y_hi-y_lo:.3f} mm")

    # ── 4. 需求：8 对差分线，每对 P/N 各一换层点（成对 ≤1~2mm）
    #   对级最小 y 跨距需求（同 x 列堆叠）：每对占 (P,N 两 via 叠置) 高 PN_MIN，
    #   对间净空 INTER_PAIR（中心距口径，最保守按 edge+od 展开在下行验算）
    #   先按"中心距≥0.875"口径算下界；再给 edge 口径（含 0.35 铜径 → 中心距1.225）上界
    n_pairs = 8
    for label, eff_pitch in (("中心距口径(0.875)", 0.875),
                             ("铜边净空口径(0.875+0.35)", 0.875 + 0.35)):
        # 单列：对 i 中心 y = y0 + i*P，每对两 via 上下叠(0.55)，总高 = (n-1)P + 0.55
        single_h = (n_pairs - 1) * eff_pitch + VIA_OCC
        # 双列交错：奇偶对分两列，每列 n/2 对
        col_n = n_pairs / 2
        double_h = (col_n - 1) * eff_pitch + VIA_OCC
        print(f"[4] {label}: 8 对单列最小 y 跨距 = {single_h:.3f} mm |"
              f" 双列交错 = {double_h:.3f} mm | 走廊可用 {y_hi-y_lo:.3f} mm")

    # x 需求：若所有对同 x 列 → x 占位 0.55（一列宽）；若 P/N 并排(Δx≤2) 需 ~2 列宽
    # 但 P/N 中心距 ≤2mm 时，x 方向两 via 并排 → 该对 x 跨度 ≤ 2+0.55；多对需错列
    # 关键：单列可容纳 8 对（y 叠放），故 x 方向 1 列 (0.55) 即够 — 前提 y 够
    # 走廊 y 可用 {y_hi-y_lo} 与 8 对 y 需求对比
    print(f"\n[4] x 方向：8 对同列时仅需 1 列 {VIA_OCC:.2f}mm < x 可用 {x_hi-x_lo:.3f}mm → x 充足"
          if (y_hi-y_lo) >= 7*0.875+VIA_OCC else "[4] x 方向见下（y 不足则需双列交错）")

    # ── 5. 逐网下游界（每线自己电容 pad 的 +x 下游缘 —— 网级 staggered gate 语义）
    print("\n[5] 逐网换层点最小 x（自己电容 pad +x 下游缘 + via_center_pad）：")
    # cap ref 中心 x（下游 pad 的右侧 + 0.275 占位）
    for n in dn_nets:
        ref, x, y = net2cap[n]
        # 该网自己电容 = ref；墙 pad = 该网 _MCIO pad（x = 该 cap +x pad，见 cap_up）
        up_x = cap_up[ref][1] if ref in cap_up else x
        own_min = up_x + 0.2 + VIA_CENTER_PAD  # pad 半宽0.2 + required
        print(f"      {n:34s} own_min_x={own_min:.3f}")

    # ── 6. 供给 vs 需求 汇总判定
    print("\n" + "="*66)
    print("判定（口径在报告正文展开）")
    print("="*66)

if __name__ == "__main__":
    main()
