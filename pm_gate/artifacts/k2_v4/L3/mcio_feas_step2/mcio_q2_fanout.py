#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""
mcio_q2_fanout.py — K2 MCIO Q2: 走廊矩形内 16 线无交叉扇出可行性求解（几何确定性）

问题（任务定稿，勿翻案）：
  16 线（8 差分对 DN_OUT0-7 × P/N）从各自 AC 电容 _U3 pad（下游/芯片侧）出发，
  在两行电容之间的走廊（y 铜净空 [58.05,67.75]，高 9.7mm）内 F.Cu 扇出，
  汇聚到 8 个成对换层点（via 簇），再 In2→U3。判定「走廊内无交叉扇出布局
  是否存在」并给出确定数字（构造性证明 or 卡点报告）。

求解要素（全确定性，与 packing/geom 脚本同源）：
  - 源：16 个 cap _U3 pad（BoardParser 实测坐标）。上排 y=57.8 行 → 从走廊顶边
    y=58.05 下潜进入；下排 y=68.0 行 → 从走廊底边 y=67.75 上浮进入。
  - via 占位 0.55（keepout 半径 0.275）；via 中心距 pad 铜边 ≥ 0.475（engine 口径）
  - P/N via 中心距 ∈ [0.55, 2.0]（成对，P 上 N 下与 U3 pad 序一致）
  - 对间铜边净空 0.875 → 异对 via 中心距 ≥ 1.225（Oracle Q1 裁定口径，勿翻案）
  - 对级下游界：via x ≥ 该对两颗 cap 自身 _MCIO pad +x 铜边 + 0.475
    （逐对 staggered，非统一 86.875 —— 本求解器把每对簇放在自己的下游界起）
  - F.Cu 布线：走廊内 x 单调；任意两条不同 net 线不得相交、并行段中心距
    ≥ 线宽+对间铜净空 = 0.205+0.875 = 1.08（同对 P/N 内部 ≥ 0.175 铜隙即可）

方法 = 构造性求解器：显式放置 8 对 cluster（P via 上 / N via 下）→ 显式布线
（peeling 阶梯折线）→ 对真板 pad 场精确净空校验 + 全线段两两相交/间距校验。
所有违规逐一列出；全绿 = 无交叉布局存在（构造性证明，附坐标与 margin）。

规则真源：全部口径来自任务/既有脚本；坐标全走 k2_v4.kicad_pcb 解析。
"""
from __future__ import annotations
import sys, math, json, os, itertools
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core.drc_rules import BoardParser

BOARD = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"
HERE = os.path.dirname(os.path.abspath(__file__))

# ── 确定性规则（任务口径，与既有脚本同源）──────────────
VIA_OCC   = 0.55                  # via keepout 直径
VR        = VIA_OCC/2.0           # keepout 半径 0.275
VIA_CU_R  = 0.175                 # via 铜半径 (0.35/2)
REQ       = 0.475                 # via 中心距 pad 铜边（engine）
INTER_CU  = 0.875                 # 对间铜边净空（Oracle Q1 裁定）
PN_LO, PN_HI = 0.55, 2.0          # P/N via 中心距
TR_W      = 0.205                 # 差分线宽
DIFF_GAP  = 0.175                 # 同对 P/N 铜隙
CROSS_MIN = 1e-9                  # 相交容差
LINE_PAD_CLEAR = 0.2              # 线铜边到异网 pad 铜边（保守取 0.2）
DIFF_SEP  = TR_W + INTER_CU       # 异对线中心距 ≥ 1.08
PAIR_SEP  = DIFF_GAP              # 同对 P/N 线中心距 ≥ 0.175（相对自身线宽另校）
# 走廊（真板解析得到，勿改）
COR_Y0, COR_Y1 = 58.05, 67.75
VIA_Y0, VIA_Y1 = COR_Y0 + REQ, COR_Y1 - REQ   # 58.525 / 67.275

# ═══════════════════════════════════════════════════════════════
# 基础几何
# ═══════════════════════════════════════════════════════════════
def pt(x, y): return (x, y)

def seg_dist(a, b, c, d):
    """线段 a-b 与 c-d 最近距离（2D，含端点）。"""
    def p2seg(p, q, r):
        vx, vy = r[0]-q[0], r[1]-q[1]
        wx, wy = p[0]-q[0], p[1]-q[1]
        L2 = vx*vx + vy*vy
        t = 0.0 if L2 < 1e-14 else max(0.0, min(1.0, (wx*vx+wy*vy)/L2))
        return math.hypot(p[0]-(q[0]+t*vx), p[1]-(q[1]+t*vy))
    return min(p2seg(a,c,d), p2seg(b,c,d), p2seg(c,a,b), p2seg(d,a,b))

def seg_cross(a, b, c, d):
    """真穿越判定（严格相交，含端点视为触碰=违规）。"""
    ax, ay = a; bx, by = b; cx, cy = c; dx, dy = d
    def cr(o, p, q): return (p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0])
    d1 = cr(c, d, a); d2 = cr(c, d, b); d3 = cr(a, b, c); d4 = cr(a, b, d)
    # 端点重合 → 违规（触碰）
    def touch(p, q): return abs(p[0]-q[0]) < CROSS_MIN and abs(p[1]-q[1]) < CROSS_MIN
    for e in (a, b):
        for f in (c, d):
            if touch(e, f): return True
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) or \
           ((d1 < 0) != (d2 < 0)) and ((d3 < 0) != (d4 < 0))

def poly_pairs(segments, others):
    """segments(本 net 的折线段) 与 others(异 net 折线段) 相交/过近检查。
    返回 (min_center_dist, violating_pairs)"""
    min_d = 1e9; bad = []
    for s in segments:
        for o in others:
            d = seg_dist(s[0], s[1], o[0], o[1])
            min_d = min(min_d, d)
    return min_d

def rect_dist(px, py, r):
    x0, y0, x1, y1 = r
    dx = max(x0-px, 0.0, px-x1); dy = max(y0-py, 0.0, py-y1)
    return math.hypot(dx, dy)

# ═══════════════════════════════════════════════════════════════
# 真板解析（BoardParser 唯一几何真源）
# ═══════════════════════════════════════════════════════════════
def load_geometry():
    b = BoardParser(BOARD).parse()
    cap_refs = {f"C{i}" for i in range(17, 33)}
    cap_u3, cap_mcio, cap_rects = {}, {}, []
    u3_rects = []
    all_rects = []
    for p in b.pads:
        x, y = p.pos
        w, h = p.size
        r = (x-w/2, y-h/2, x+w/2, y+h/2)
        all_rects.append((p.footprint_ref, r))
        if p.footprint_ref in cap_refs:
            cap_rects.append(r)
            n = p.net or ""
            if n.endswith("_U3"):
                cap_u3[n] = dict(ref=p.footprint_ref, x=x, y=y, rect=r)
            elif n.endswith("_MCIO"):
                cap_mcio[p.footprint_ref] = dict(x=x, y=y, rect=r)
        elif p.footprint_ref == "U3":
            u3_rects.append(r)
    u3_left = min(r[0] for r in u3_rects)
    wall_x1 = max(r[2] for r in cap_rects)
    # U3 信号 pad y（逐网目标，仅报告用）
    u3_sig = {}
    for p in b.pads:
        if p.footprint_ref == "U3":
            n = p.net or ""
            if n.startswith("PCIE_DN_OUT") and n.endswith("_U3"):
                u3_sig[n] = p.pos[1]
    return dict(cap_u3=cap_u3, cap_mcio=cap_mcio, u3_sig=u3_sig,
                u3_left=u3_left, wall_x1=wall_x1,
                all_rects=all_rects)

def build_nets(geo):
    """16 网 → dict[net] = {pair, pol, ref, src_x, src_y, via_minx, u3y}"""
    nets = {}
    for n, d in geo["cap_u3"].items():
        if not n.startswith("PCIE_DN_OUT"):
            continue
        stem = n[:-3]          # ..._P / ..._N  (去掉 _U3)
        pol = stem[-1]
        base = stem[:-2]       # PCIE_DN_OUT0
        m = geo["cap_mcio"][d["ref"]]
        edge = m["rect"][2]    # 该 cap 自身 _MCIO pad +x 铜边（对级下游界源）
        nets[n] = dict(netname=n, pair=base, pol=pol, ref=d["ref"],
                       src_x=d["x"], src_y=d["y"],
                       via_minx=edge + REQ,
                       u3y=geo["u3_sig"].get(n))
    return nets

def pair_meta(nets):
    """pair → {row, nets, via_minx(pair=max), src 范围, u3y 范围}"""
    pm = {}
    for n, d in nets.items():
        pm.setdefault(d["pair"], []).append(d)
    meta = {}
    for base, ms in pm.items():
        row_y = ms[0]["src_y"]
        edge = max(m["via_minx"] - REQ for m in ms)   # pair 最大 cap 铜边
        meta[base] = dict(nets=ms, row_y=row_y,
                          via_minx=edge + REQ,
                          src_xmin=min(m["src_x"] for m in ms),
                          src_xmax=max(m["src_x"] for m in ms),
                          u3_top=min(m["u3y"] for m in ms if m["u3y"]),
                          u3_bot=max(m["u3y"] for m in ms if m["u3y"]))
    return meta

# ═══════════════════════════════════════════════════════════════
# 布局构造：给定每对 (cluster_x, P via y)，P 上 N 下 Δy=pn_dy
# 布线 = 阶梯折线（peeling），随后全约束精确校验
# ═══════════════════════════════════════════════════════════════
def route_upper(net, nets, geo):
    """上排 net：源 pad 底口 (src_x, 58.05) 下潜进入走廊 → via。
    阶梯: (sx,58.05) → (sx, vy) → (vx, vy)。 其中 vx≥sx 恒成立（下游界>源x）。
    """
    sx, vy, vx = net["src_x"], net["via_y"], net["via_x"]
    return [(sx, COR_Y0), (sx, vy), (vx, vy)]

def route_lower(net, nets, geo):
    """下排 net：源 pad 顶口 (src_x, 67.75) 上浮进入走廊 → via。"""
    sx, vy, vx = net["src_x"], net["via_y"], net["via_x"]
    return [(sx, COR_Y1), (sx, vy), (vx, vy)]

def build_layout(geo, nets, pmeta, params):
    """params: dict pair -> dict(cluster_x, yP, yN, ) 生成布局并布线。
    P via (cluster_x, yP), N via (cluster_x, yN), yN=yP+pn_dy.
    """
    L = dict(vias={}, routes={})
    for base, pr in pmeta.items():
        cx = params[base]["cluster_x"]
        yP = params[base]["yP"]
        yN = params[base]["yN"]
        for m in pr["nets"]:
            if m["pol"] == "P":
                L["vias"][m["netname"]] = (cx, yP)
            else:
                L["vias"][m["netname"]] = (cx, yN)
    # 布线
    for n, d in nets.items():
        dd = dict(d)
        dd["via_x"], dd["via_y"] = L["vias"][n]
        dd["netname"] = n
        L["routes"][n] = route_upper(dd, nets, geo) if dd["src_y"] < 67.0 \
                         else route_lower(dd, nets, geo)
    return L

# ═══════════════════════════════════════════════════════════════
# 全约束校验（返回 violation 列表 + 最小 margin 统计）
# ═══════════════════════════════════════════════════════════════
def verify(L, geo, nets, pmeta, report=False):
    vio = []
    # (A) via 中心 vs 全 pad 铜边 ≥ REQ
    for n, (x, y) in L["vias"].items():
        for ref, r in geo["all_rects"]:
            d = rect_dist(x, y, r)
            if d < REQ - 1e-9:
                vio.append(f"via {n}({x:.2f},{y:.2f}) 距 {ref} pad 铜 {d:.3f}<{REQ}")
    # (B) via 自身窗口（y 走廊窗口; x 仅下限下游界 + 上限 U3 左缘）
    for base, pr in pmeta.items():
        for m in pr["nets"]:
            x, y = L["vias"][m["netname"]]
            if y < VIA_Y0 - 1e-9 or y > VIA_Y1 + 1e-9:
                vio.append(f"via {m['net']} y={y:.3f} 出走廊窗口"
                           f"[{VIA_Y0:.3f},{VIA_Y1:.3f}]")
            if x < m["via_minx"] - 1e-9:
                vio.append(f"via {m['net']} x={x:.3f} < 自身下游界 {m['via_minx']:.3f}")
            if x > geo["u3_left"] - REQ + 1e-9:
                vio.append(f"via {m['net']} x={x:.3f} 越过 U3 左缘净空")
    # (C) P/N 对内 via 中心距 ∈[0.55,2.0]
    for base, pr in pmeta.items():
        vp = [L["vias"][m["netname"]] for m in pr["nets"] if m["pol"] == "P"]
        vn = [L["vias"][m["netname"]] for m in pr["nets"] if m["pol"] == "N"]
        if vp and vn:
            d = math.hypot(vp[0][0]-vn[0][0], vp[0][1]-vn[0][1])
            if d < PN_LO - 1e-9 or d > PN_HI + 1e-9:
                vio.append(f"pair {base} P/N dist {d:.3f} ∉[{PN_LO},{PN_HI}]")
    # (D) 异对 via 中心距 ≥ 1.225
    vl = list(L["vias"].items())
    for i in range(len(vl)):
        for j in range(i+1, len(vl)):
            n1, p1 = vl[i]; n2, p2 = vl[j]
            if nets[n1]["pair"] == nets[n2]["pair"]:
                continue
            d = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
            need = VIA_CU_R*2 + INTER_CU
            if d < need - 1e-9:
                vio.append(f"异对 via {nets[n1]['pair']}-{nets[n2]['pair']} "
                           f"中心距 {d:.3f}<{need:.3f}")
    # (E) 折线两两：相交 或 中心距不足（异对 1.08 / 同对线 0.175 铜隙→0.38 中心）
    segs = {}
    for n, poly in L["routes"].items():
        segs[n] = list(zip(poly, poly[1:]))
    names = list(segs)
    min_d_map = {}
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            n1, n2 = names[i], names[j]
            same_pair = nets[n1]["pair"] == nets[n2]["pair"]
            need = PAIR_SEP if same_pair else DIFF_SEP
            dmin = 1e9
            for s1 in segs[n1]:
                for s2 in segs[n2]:
                    if seg_cross(s1[0], s1[1], s2[0], s2[1]):
                        dmin = 0.0
                        break
                    dmin = min(dmin, seg_dist(s1[0], s1[1], s2[0], s2[1]))
                if dmin == 0.0:
                    break
            if dmin < need - 1e-6:
                vio.append(f"线 {n1}-{n2} 中心距 {dmin:.3f}<{need:.3f}"
                           + ("(同对)" if same_pair else "(异对)"))
            min_d_map[(n1, n2)] = dmin
    # (F) 折线与 pad 铜（异网）净空：线铜边到 pad ≥ LINE_PAD_CLEAR
    for n, segs_n in segs.items():
        my_refs = {d["ref"] for d in nets.values() if d["netname"] == n}
        for s in segs_n:
            for ref, r in geo["all_rects"]:
                # 起点在自己 pad 上允许（连接点），其余段不得侵入
                d = min(seg_dist(s[0], s[1], (r[0], r[1]), (r[2], r[1])),
                        seg_dist(s[0], s[1], (r[2], r[1]), (r[2], r[3])),
                        seg_dist(s[0], s[1], (r[2], r[3]), (r[0], r[3])),
                        seg_dist(s[0], s[1], (r[0], r[3]), (r[0], r[1])))
                if d < LINE_PAD_CLEAR - 1e-6:
                    # 只允许：该 pad 属于本网 且 是首段连接
                    own = n in geo["cap_u3"] and ref == geo["cap_u3"][n]["ref"]
                    vio.append(f"线 {n} 距 {ref} pad {d:.3f}<{LINE_PAD_CLEAR}"
                               f" (own={own})")
    return vio

# ═══════════════════════════════════════════════════════════════
# 构造搜索：默认参数字典来自「自然错列」设计；可微调
# ═══════════════════════════════════════════════════════════════
def default_params(pmeta, x_off=None, y_off=None, pn_dy=0.7):
    """自然错列：每对 cluster_x = 自身下游界 + 裕量；yP 贴近 U3 P pad y（上排）
    并在可行窗口内；P 上 N 下。
    """
    prm = {}
    for base in sorted(pmeta, key=lambda b: pmeta[b]["src_xmin"]):
        pr = pmeta[base]
        top = pr["row_y"] < 67.0
        # U3 P pad y = u3_top（P 上 N 下: P y 小）
        u3p = min(m["u3y"] for m in pr["nets"] if m["pol"] == "P")
        # 下排 y 往大走（贴底）窗口：让 yP ∈ [58.525, 67.275]
        yP = u3p
        if yP < VIA_Y0:
            yP = VIA_Y0
        yN = yP + pn_dy
        if yN > VIA_Y1:
            # 压缩 Δ 使 N 也进窗口
            yN = VIA_Y1
            yP = yN - pn_dy
        xoff = (x_off or {}).get(base, 0.0)
        yo = (y_off or {}).get(base, 0.0)
        prm[base] = dict(cluster_x=pr["via_minx"] + xoff,
                         yP=yP + yo, yN=yN + yo)
    return prm

if __name__ == "__main__":
    geo = load_geometry()
    nets = build_nets(geo)
    pmeta = pair_meta(nets)
    print("对元数据（BoardParser 实测）：")
    for base in sorted(pmeta, key=lambda b: pmeta[b]["src_xmin"]):
        pr = pmeta[base]
        print(f"  {base:14s} row={pr['row_y']:5.1f} via_x≥{pr['via_minx']:6.2f} "
              f"src x[{pr['src_xmin']:6.2f},{pr['src_xmax']:6.2f}] "
              f"U3y[{pr['u3_top']:.2f},{pr['u3_bot']:.2f}]")
    print(f"\n走廊 y=[{COR_Y0},{COR_Y1}] via y 窗口=[{VIA_Y0:.3f},{VIA_Y1:.3f}]")
    print(f"墙右铜边={geo['wall_x1']:.3f} U3 左缘={geo['u3_left']:.3f} "
          f"via x≤{geo['u3_left']-REQ:.3f}")
    prm = default_params(pmeta)
    L = build_layout(geo, nets, pmeta, prm)
    vio = verify(L, geo, nets, pmeta)
    print("\n默认布局违规:", len(vio))
    for v in vio[:40]:
        print("  ✗", v)
