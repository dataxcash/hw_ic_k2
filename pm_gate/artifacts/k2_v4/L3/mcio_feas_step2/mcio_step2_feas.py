#!/usr/bin/env python3
"""
mcio_step2_feas.py — K2 MCIO 布局可行性精确求解（几何确定性）

模型（口径全声明，可复算）：
  场景：8 对 DN_OUT0-7 → U3。每线自其电容 _U3 pad（下游侧）出发，走 F.Cu
  在「两行电容间走廊」扇出至换层点（F.Cu→In2 via），In2 段至 U3 近旁，
  再经 stub 上 U3 pad（x=88.825 列）。
  任务口径：换层点必须落在电容下游且 P/N 成对；
    via 占位 0.55（keepout 半径 0.275）
    P/N via 中心距 ∈ [0.55, 2.0]mm（成对）
    对间净空 0.875（两种口径：中心距 / 铜边净距）
  换层点 x 须 ≥ 该网自己电容 _MCIO pad 的 +x 铜边 + 0.475（no_via_in_pad
  pad_edge_clearance 0.3 + via 半径 0.175，LandingRules.required 同源）。
  几何障碍 = 真板全 pad（BoardParser），via keepout 圆不得与任何 pad 铜相交。

产出：
  A. 逐网下游 x 界 + 换层点可行域（x/y 窗口、可用面积）
  B. 8 对 co-located 最小 y 跨距（单列 / 双列交错）× 两种对间口径
  C. 供给 vs 需求差量 → 判定
"""
import sys, math
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core.drc_rules import BoardParser

BOARD = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"

# 确定性规则（任务给定）
VIA_OCC = 0.55
VR = VIA_OCC / 2.0
PN_MAX = 2.0
PN_MIN = VIA_OCC
PAD_EDGE_CLR = 0.3
REQ = VIA_OCC / 2.0 + PAD_EDGE_CLR     # via 中心距 pad 铜边 = 0.475

def main():
    b = BoardParser(BOARD).parse()
    cap_refs = {f"C{i}" for i in range(17, 33)}
    # 收集：电容墙 pad、U3 pad、走廊障碍（x 66-92, y 40-75 内全部 pad）
    wall_rects, u3_rects, obs_rects = [], [], []
    cap_down = {}   # net -> (ref, x, y)  cap 的 _U3 pad（下游/芯片侧）
    cap_upx  = {}   # ref -> 该 cap _MCIO pad 的 +x 铜边（墙位置源）
    for p in b.pads:
        x, y = p.pos
        r = (x-p.size[0]/2, y-p.size[1]/2, x+p.size[0]/2, y+p.size[1]/2)
        net = p.net or ""
        if p.footprint_ref in cap_refs:
            wall_rects.append(r)
            if net.endswith("_U3"):
                cap_down.setdefault(net, (p.footprint_ref, x, y))
            if net.endswith("_MCIO"):
                cap_upx[p.footprint_ref] = r[2]   # pad +x 铜边
        elif p.footprint_ref == "U3":
            u3_rects.append(r)
        if 66.0 <= x <= 92.0 and 40.0 <= y <= 76.0:
            obs_rects.append(r)

    # U3 左铜缘（信号列 x=88.825 pad 左缘）
    u3_left = min(r[0] for r in u3_rects)
    u3_sig = sorted([r for r in u3_rects if abs(r[0]-88.825) < 0.3], key=lambda r: r[1])
    # 墙右铜边
    wall_right = max(r[2] for r in wall_rects)
    # 两行电容行心
    rows = sorted({round(p.pos[1], 3) for p in b.pads if p.footprint_ref in cap_refs})
    print(f"墙行 y = {rows}  墙右铜边 x = {wall_right:.3f}  U3 左铜缘 x = {u3_left:.3f}")

    # 下游 8 对 (DN_OUT0-7)
    dn = sorted(n for n in cap_down if n.startswith("PCIE_DN_OUT") and n.endswith("_U3"))
    pairs = {}
    for n in dn:
        stem = n[:-3]            # PCIE_DN_OUT0_P
        base = stem[:-2]         # PCIE_DN_OUT0
        pol = stem[-1]
        pairs.setdefault(base, {})[pol] = (n, cap_down[n])
    print(f"\n下游对: {len(pairs)}")
    assert len(pairs) == 8

    # A. 逐网换层点下游 x 界
    print("\n[A] 每网：自己电容墙 pad +x 铜边 → 换层点 x 下界 (≥edge+0.475)")
    per_net_min_x = {}
    for base in sorted(pairs):
        for pol in ("P", "N"):
            n, (ref, px, py) = pairs[base][pol]
            edge = cap_upx[ref]
            per_net_min_x[n] = edge + REQ
    # 每对取两网中较大下游界 = 该对换层点 x 下界（P/N 成对 → 都要越过各自电容）
    pair_min_x = {}
    for base in sorted(pairs):
        pair_min_x[base] = max(per_net_min_x[pairs[base]["P"][0]],
                               per_net_min_x[pairs[base]["N"][0]])

    # B. 走廊可用 y（两行电容 pad 铜边之间，扣 via 净空）
    row_lo = min(rows) - 0.25          # 上排 pad 底 (57.55? no: 行心-0.25=57.55 → pad 底 58.05)
    row_hi = max(rows) + 0.25
    # 用真实 pad rect 求走廊净空 y
    def row_span(ry):
        ys = [r[1] for r in wall_rects if abs((r[1]+r[3])/2 - ry) < 0.001]
        return min(ys), max([r[3] for r in wall_rects if abs((r[1]+r[3])/2 - ry) < 0.001])
    ys = {}
    for ry in rows:
        y0, y1 = row_span(ry)
        ys[ry] = (y0, y1)             # pad 铜 y 跨度
    corridor_y0 = max(v[1] for v in ys.values())   # 上排 pad 底边（最大 y1 在上排）
    # 分开：上排底边 vs 下排顶边
    yspans = sorted(ys.items())
    top_bot = yspans[0][1][1]         # 上排 pad 底
    bot_top = yspans[1][1][0]         # 下排 pad 顶
    corr_cu_lo, corr_cu_hi = top_bot, bot_top
    via_y_lo = corr_cu_lo + REQ
    via_y_hi = corr_cu_hi - REQ
    print(f"\n[B] 走廊净空 y 铜边: [{corr_cu_lo:.3f}, {corr_cu_hi:.3f}]"
          f" 高 {corr_cu_hi-corr_cu_lo:.3f}")
    print(f"    via 中心 y 可行: [{via_y_lo:.3f}, {via_y_hi:.3f}] 高 {via_y_hi-via_y_lo:.3f}")

    # C. 供给矩形（任务口径）：x = 墙右缘→U3左缘, y = 走廊(行心距)
    sup_x = (wall_right, u3_left)
    sup_xw = sup_x[1] - sup_x[0]
    sup_yh = max(rows) - min(rows)
    print(f"\n[C] 供给（任务口径）: x=[{sup_x[0]:.2f},{sup_x[1]:.2f}] 宽 {sup_xw:.2f}mm"
          f" × 走廊(行心) {sup_yh:.2f}mm")

    # D. 8 对 co-located 换层点最小空间需求
    #  布局 1：单列（所有对 x 相同，P/N 沿 y 上下叠 0.55，对间 y 距 INTER）
    #  布局 2：双列交错（奇偶对 x 错开 0.55+，对间 y 距可减半）
    print(f"\n[D] 8 对成对换层点最小空间需求（P/N 中心距取 {PN_MIN}~{PN_MAX}mm）")
    for label, inter in (("对间=中心距0.875", 0.875),
                         ("对间=铜边净距0.875(via中心1.225)", 0.875 + VIA_OCC)):
        # 单列：对叠 y：每对 1 via 高 + 对间
        single = (8 - 1) * max(inter, VIA_OCC) + VIA_OCC
        # 双列交错：4+4
        double = (4 - 1) * max(inter, VIA_OCC) + VIA_OCC
        print(f"    [{label}] 单列需求 {single:.3f}mm | 双列需求 {double:.3f}mm"
              f" | 走廊可用 {via_y_hi-via_y_lo:.3f}mm")

    # E. 换层点可行域真实计算（走廊内逐点净空 + 下游界 + U3 净空）
    print("\n[E] 换层点真实可行域（走廊带，逐 0.1mm 采样，全障碍净空）")
    xw = (wall_right + REQ, u3_left - REQ)     # x 绝对界
    # y 界：全走廊（含两行电容间 + 由 U3 pad 列上下缘约束）
    yw = (via_y_lo, via_y_hi)
    def clear(px, py):
        for r in obs_rects:
            # 点到矩形最近距离
            dx = max(r[0]-px, 0, px-r[2]); dy = max(r[1]-py, 0, py-r[3])
            if math.hypot(dx, dy) < VR:
                return False
        return True
    # 网格采样可行域
    free = []
    xs = [round(xw[0] + 0.1*i, 3) for i in range(int((xw[1]-xw[0])/0.1)+1)]
    yg = [round(yw[0] + 0.1*i, 3) for i in range(int((yw[1]-yw[0])/0.1)+1)]
    for px in xs:
        for py in yg:
            if clear(px, py):
                free.append((px, py))
    if free:
        fx = [p[0] for p in free]; fy = [p[1] for p in free]
        print(f"    x∈[{min(fx):.2f},{max(fx):.2f}] w={max(fx)-min(fx):.2f}"
              f"  y∈[{min(fy):.2f},{max(fy):.2f}] h={max(fy)-min(fy):.2f}"
              f"  自由格点 {len(free)}/{len(xs)*len(yg)}")
    else:
        print("    走廊 x 窗口内无可放点（!!）")

    # F. 判定摘要
    print("\n" + "="*70)
    print("判定口径见正文；关键数字：")
    print(f"  换层点 x 可行 {xw[0]:.2f}~{xw[1]:.2f} (宽 {xw[1]-xw[0]:.2f})")
    print(f"  8 对单列 y 需求（对间中心0.875）: {(8-1)*0.875+VIA_OCC:.2f}mm"
          f" / 走廊可用 {via_y_hi-via_y_lo:.2f}mm")
    print("="*70)

if __name__ == "__main__":
    main()
