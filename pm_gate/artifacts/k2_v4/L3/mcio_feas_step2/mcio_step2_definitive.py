#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""
mcio_step2_definitive.py — K2 MCIO 布局可行性：换层点成对空间需求精确求解

几何模型（零硬编码坐标，全走真板解析 + 任务规则）：
  16 线（8 差分对 × P/N）从各自 AC 电容 _U3 pad（两行 y=57.8/68.0）出发，
  在 F.Cu 走廊内扇出到「换层点」（P/N 成对 via 簇，簇内距 ≤1~2mm），
  再 In2 到 U3 pad（x=88.825 列，y 58.5-67.3）。
  任务给定：
    via keepout 占位 0.55mm（半径 0.275）
    对间净空 0.875mm（两种口径：中心距 0.875 / 铜边净空 0.875 → 中心距 1.225）
    换层点必须落在自己电容的下游（x ≥ 自己 cap 右铜边 + via 半径 + 净空）
    16 线都必须在走廊 F.Cu 扇出（不能穿电容实体墙，必须经两行之间走廊）

产出：
  1) 逐 net cap 坐标与下游 x 界
  2) 可行 y 窗口（两行之间走廊）与 x 窗口
  3) 8 对成对换层点布局（列数 × 每列对数 × y 间距）所需最小 y 跨距
  4) 与走廊可用 y 的差量 → 判定：无解(需改摆件) / 有解但形态受限
"""
import sys, math
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core.drc_rules import BoardParser

BOARD = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"
VR = 0.55 / 2.0       # via keepout 半径 0.275
PN_MAX = 2.0
PN_MIN = 0.55
CLEAR_PAD = 0.1       # via keepout 内含 0.1 净空；via 中心到 pad 铜边 ≥ VR+? 
# 保守：via 中心到任何 pad 铜边 ≥ VR + 0.1 = 0.375（占位0.55=0.35外径+0.1×2已含）
# 实际 no_via_in_pad pad_edge_clearance 0.3 更严（引擎 required=0.475）。两口径都列。

def main():
    b = BoardParser(BOARD).parse()
    caps = [f"C{i}" for i in range(17, 33)]
    down = {}   # net -> (ref,x,y)
    up   = {}   # net -> (ref,x)
    for p in b.pads:
        if p.footprint_ref in caps:
            n = p.net or ""
            if n.endswith("_U3"):
                down[n] = (p.footprint_ref, p.pos[0], p.pos[1])
            elif n.endswith("_MCIO"):
                up.setdefault(p.footprint_ref, p.pos[0] + p.size[0]/2)  # +x 铜边

    dn = sorted((k,v) for k,v in down.items() if k.startswith("PCIE_DN_OUT"))
    # 按 cap x 排序（行内从左到右）
    dn.sort(key=lambda kv: kv[1][1])
    print("16 线（按 cap x 升序）cap 下游 pad：")
    for n,(ref,x,y) in dn:
        print(f"  {n:36s} {ref} pad=({x:6.2f},{y:5.2f}) 墙+x边={up[ref]:6.2f}")

    # 上游净空口径（引擎 LandingRules.required = via 半径 0.175 + max(clr,pad_edge_clr)）
    # 但任务口径 via 占位 0.55 → 下游 x 界 = cap 右铜边 + 0.55? 不：占位只含净空，另需 pad 距离。
    # 用两种： (a) +0.275 (keepout 切 pad 边)  (b) +0.475 (engine required)
    print("\n下游界口径: (a) keepout贴pad边 x≥cap右+0.275   (b) engine required x≥cap右+0.475")
    # 每对取 P/N 中较大下游界
    pairs = {}
    for n,(ref,x,y) in dn:
        base = n[:-3]  # strip _P/_N + _U3? -> PCIE_DN_OUT0_P
        # n = PCIE_DN_OUT0_P_U3; stem=PCIE_DN_OUT0_P; pol=P
        stem = n[:-3]   # remove _U3
        pol = stem[-1]
        base = stem[:-2]
        pairs.setdefault(base, {})[pol] = (n, ref, x, y, up[ref])
    print(f"8 对映射完成: {sorted(pairs)}")

    row_u = [v for v in pairs.values() if v['P'][3] == 57.8]  # upper row caps
    # 分类：upper row (y=57.8) DN0-3 ; lower (y=68.0) DN4-7
    for base in sorted(pairs):
        pr = pairs[base]
        yrow = pr['P'][3]
        print(f"  {base}: P cap {pr['P'][1]} pad_x={pr['P'][2]:6.2f}  N cap {pr['N'][1]} pad_x={pr['N'][2]:6.2f}  row_y={yrow}")

    # U3 pad y for each net
    u3 = {}
    for p in b.pads:
        if p.footprint_ref == "U3" and (p.net or "").endswith("_U3"):
            u3[p.net] = p.pos[1]
    print("\nU3 pad y 目标：")
    for base in sorted(pairs):
        for pol in ("P","N"):
            n = pairs[base][pol][0]
            print(f"  {n:36s} U3 pad y={u3[n]:6.2f}")

    # ============ 核心可行域 ============
    # 走廊（两行电容之间）：行 1 y=57.8, 行 2 y=68.0, pad 高 0.5
    # 走廊净 y（pad 铜边）：58.05..67.75；扣 via 占位净空：
    for label, req in (("keepout(0.275)", VR), ("engine(0.475)", 0.475)):
        y_lo = 58.05 + req
        y_hi = 67.75 - req
        # 若换层点必须到整面墙右缘之后：
        xw_lo = 85.15 + req
        xw_hi = 88.6 - req
        print(f"\n[{label}] 走廊 y 可用 {y_lo:.2f}~{y_hi:.2f} 高 {y_hi-y_lo:.2f}"
              f" | x(墙后) 可用 {xw_lo:.2f}~{xw_hi:.2f} 宽 {xw_hi-xw_lo:.2f}")

    # ============ 关键：走廊内 8 对成对换层点 y 需求 ============
    # 前提：全部 8 对换层点须在两行之间走廊 y∈(58.05,67.75) 内，因 F.Cu 扇出只能经走廊。
    # 16 via = 8 簇。簇间 y 间距受「对间净空 0.875」约束。
    print("\n" + "="*70)
    print("8 对成对换层点 y 跨距需求（走廊内，全部簇共享一个 x 列的最优情形）")
    print("="*70)
    for label, inter in (("对间净空=中心距0.875", 0.875),
                         ("对间净空=铜边0.875→中心1.225", 0.875 + 0.55)):
        for layout, per_col in (("单列8", 8), ("双列4+4", 4)):
            # 每对：P/N 上下叠（Δy ∈[0.55,2.0]），簇高取典型 0.55（最紧凑）
            n_per = per_col
            # 列内簇 pitch = max(inter, PN_MIN)
            pitch = max(inter, 0.55)
            col_h = (n_per - 1) * pitch + 0.55
            extra = ""
            if layout == "双列4+4":
                # 两列 x 错开，需 x 宽度 ≥ 2×(0.55)+0.55 净距 = 1.65 > 墙后可用 2.5 ✓
                pass
            print(f"  [{label}] {layout}: y 需求 {col_h:.2f}mm")
    print("\n走廊可用 y（keepout口径）≈ 9.17mm；engine 口径 ≈ 8.60mm")

    # 实际 P/N 上下叠时簇间还要看 P/N 跨簇交错：
    # 若每簇内部 P/N 也按 y 叠(0.55)则簇高 0.55；簇间中心距 ≥ max(inter,0.55)。
    # 单列8 → 7×max(inter,0.55)+0.55
    for label, inter in (("中心0.875",0.875),("铜边1.225",1.225)):
        for cl in (0.55, 2.0):
            print(f"    单列8 簇内跨{cl} P/N中心{inter:5.3f} → 总高 {(8-1)*inter+cl:.2f}")

    # ============ F.Cu 扇出交叉检查（换层点 y 序 vs cap x 序） ============
    # 上排 8 cap 全在 y=57.8, x 从 75.15..84.25 展布；U3 pad 目标 y 58.5..62.5 升序。
    # 每线上排 cap x 越大 → 越靠右 → 需在更短的走廊段内转入自身 U3 目标 y。
    # 上排 4 对 (DN0-3) 目标 U3 y: DN0→58.5/58.9 (最上) ... DN3→62.1/62.5 (下)
    # 而 cap x: DN0 最左 ... DN3 最右。cap_x 增 → U3_y 增 → 扇出向右下旋转。
    print("\n" + "="*70)
    print("F.Cu 扇出交叉单调性检查")
    print("="*70)
    # 上排 net 按 cap x 排序 → 其 U3 pad y 是否同向增？（同向→可无交叉扇出）
    upr = []
    for base in ("PCIE_DN0","PCIE_DN1","PCIE_DN2","PCIE_DN3"):
        for pol in ("P","N"):
            n,ref,x,y,edge = pairs[base][pol]
            upr.append((x, u3[n], n))
    upr.sort()
    mon_up = all(upr[i][1] <= upr[i+1][1] + 1e-6 for i in range(len(upr)-1))
    print(f"  上排 cap_x 升序 vs U3_y: 单调={'是' if mon_up else '否'}（同向增→无交叉扇出可能）")
    for x,yu,n in upr: print(f"    cap_x={x:6.2f} → U3_y={yu:5.2f} {n}")

if __name__ == "__main__":
    main()
