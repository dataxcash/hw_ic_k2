#!/usr/bin/env python3
"""8 对成对换层点 packing 参数扫描 + 供给对比（纯几何，K2 MCIO）"""
import sys, math
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core.drc_rules import BoardParser

BOARD = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"
VIA = 0.55            # via keepout 直径
VIA_R = VIA/2
PN_LO, PN_HI = VIA, 2.0     # P/N via 中心距 约束
REQ = 0.475           # via 中心到 pad 铜边
INTER = 0.875         # 对间净空

b = BoardParser(BOARD).parse()
# 墙右铜边 / U3 左铜边
wall_x1 = max(r[2] for p in b.pads if (p.footprint_ref or "").startswith("C") and 17 <= int((p.footprint_ref or "C0")[1:]) <= 32
              for r in [(p.pos[0]-p.size[0]/2, p.pos[1]-p.size[1]/2, p.pos[0]+p.size[0]/2, p.pos[1]+p.size[1]/2)])
u3x0 = min(p.pos[0]-p.size[0]/2 for p in b.pads if p.footprint_ref=="U3")
u3y0 = min(p.pos[1]-p.size[1]/2 for p in b.pads if p.footprint_ref=="U3")
u3y1 = max(p.pos[1]+p.size[1]/2 for p in b.pads if p.footprint_ref=="U3")
print(f"墙右铜边 {wall_x1:.3f}  U3 左铜 {u3x0:.3f}  U3 pad y [{u3y0:.3f},{u3y1:.3f}]")

# 走廊净空（两行电容 pad 之间），行心 57.8/68.0, pad 高 0.5
corr_y0 = 57.8 + 0.25   # 58.05 上排 pad 底
corr_y1 = 68.0 - 0.25   # 67.75 下排 pad 顶
y_avail_center = (corr_y0+REQ, corr_y1-REQ)   # via 中心可用 y
print(f"走廊 pad 间 y [{corr_y0:.2f},{corr_y1:.2f}] 高 {corr_y1-corr_y0:.2f}")
print(f"via 中心 y 可用 [{y_avail_center[0]:.3f},{y_avail_center[1]:.3f}] 高 {y_avail_center[1]-y_avail_center[0]:.2f}")

x_avail_center = (wall_x1 + REQ, u3x0 - REQ)
print(f"via 中心 x 可用 [{x_avail_center[0]:.3f},{x_avail_center[1]:.3f}] 宽 {x_avail_center[1]-x_avail_center[0]:.2f}")

N = 8
print("\n单列（8 对共享同一 x，沿 y 排布；对内 P/N 上下叠）")
print(f"{'P/N中心距':>8} {'对间口径':>14} {'每对y跨':>8} {'8对总高':>8} {'可容纳?':>7}")
for dpn in (0.55, 0.9, 1.3, 2.0):
    for label, inter_ctr in (("中心距0.875", 0.875), ("铜边净距0.875→中心1.225", INTER+0.35), ("keepout+0.875→1.425", 0.55+INTER)):
        pair_h = dpn
        total = (N-1)*inter_ctr + pair_h   # 每对占其内部 P/N 跨度；对与对之间按 inter
        ok = total <= (y_avail_center[1]-y_avail_center[0])
        print(f"{dpn:8.2f} {label:>14} {pair_h:8.2f} {total:8.2f} {'YES' if ok else 'NO':>7}")

print("\n双列交错（4+4 两列 x 错开，列间距 ≥0.55）")
# 每列 4 对；列内对间距 inter；列与列 x 需 0.55+ 分开
for dpn in (0.55, 0.9, 1.3, 2.0):
    for label, inter_ctr in (("中心距0.875", 0.875), ("铜边净距→1.225", INTER+0.35)):
        per_col_h = (4-1)*inter_ctr + dpn
        ok = per_col_h <= (y_avail_center[1]-y_avail_center[0])
        xneed = 0.55 + 0.55  # 两列各自 0.55 + 中间须分开（列内 P/N 若同列上下叠则 x 只需 0.55/列）
        print(f"{dpn:8.2f} {label:>14} 每列高 {per_col_h:6.2f} 可容纳? {'YES' if ok else 'NO':>4}  x 需 2 列 {xneed:.2f} ≤ {x_avail_center[1]-x_avail_center[0]:.2f}? {xneed<=x_avail_center[1]-x_avail_center[0]}")

print("\n走廊 y 高度需求（每对=上下P/N + 对间0.875净空，中心距口径）:",
      f"{(N-1)*INTER + PN_LO:.2f}~{(N-1)*INTER + PN_HI:.2f} mm  vs 可用 {y_avail_center[1]-y_avail_center[0]:.2f} mm")
print("走廊 y 高度需求（铜边口径 0.875+0.35=1.225）:",
      f"{(N-1)*1.225 + PN_LO:.2f}~{(N-1)*1.225 + PN_HI:.2f} mm")
print("走廊原始（pad铜边间）高度 9.70mm；若可用 P/N via 中心距需≤1~2mm 且对间0.875，"
      "y 是否够取决口径。")
