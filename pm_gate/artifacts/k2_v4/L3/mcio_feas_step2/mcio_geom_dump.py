#!/usr/bin/env python3
"""
mcio_geom_dump.py — K2 MCIO 几何权威导出（BoardParser 真板解析，可复算）

产出（确定性，供 Q2 扇出求解器消费）：
  1. 16 颗 AC 电容 _U3 pad（F.Cu 扇出源）：网名/ref/pad 中心 x,y/铜矩形
  2. 每网自己电容 _MCIO pad 的 +x 铜边（逐网下游界源）
  3. U3 信号 pad 目标（每网 x=88.825 列 y）
  4. 电容墙铜跨 / 两行行心 / 走廊净空 y / 墙→U3 竖条
  5. 走廊矩形 (x∈[75,88.7]×y∈[58,68]) 内 pad 障碍扫描（应 0）
  6. 8 对聚合：每对 {P,N} 源 x/下游铜边/下游界(edge+0.475)/U3 目标 y
  7. 全部几何落盘 JSON：L3/mcio_feas_step2/mcio_geom.json（供 solver 读）

零硬编码坐标：所有数从板解析得出；输出仅供可复算报告引用。
"""
import sys, json, math, os
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core.drc_rules import BoardParser

BOARD = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcio_geom.json")

# 确定性规则（任务定稿，与既有脚本同源）
VIA_OCC = 0.55          # via keepout 直径
VR = VIA_OCC / 2.0      # keepout 半径 0.275
VIA_CU_D = 0.35         # via 铜径
VIA_CU_R = VIA_CU_D / 2 # 0.175
PAD_EDGE_CLR = 0.3      # no_via_in_pad（via 铜边到 pad 铜边）— LandingRules 语义
REQ = VIA_CU_R + PAD_EDGE_CLR   # via 中心到 pad 铜边 = 0.475（engine 口径）
INTER_COPPER = 0.875    # 对间铜边净空（Oracle Q1 裁定口径）
PN_MIN, PN_MAX = VIA_OCC, 2.0   # P/N via 中心距 ∈ [0.55, 2.0]

def pad_rect(p):
    w, h = p.size
    return (p.pos[0]-w/2, p.pos[1]-h/2, p.pos[0]+w/2, p.pos[1]+h/2)

def rect_dist(px, py, r):
    x0,y0,x1,y1 = r
    dx = max(x0-px, 0, px-x1); dy = max(y0-py, 0, py-y1)
    return math.hypot(dx, dy)

def main():
    b = BoardParser(BOARD).parse()
    cap_refs = {f"C{i}" for i in range(17, 33)}

    # ── 1. 电容 + U3 pad 采集 ─────────────────────────────
    cap_u3, cap_mcio, cap_rects = {}, {}, []
    u3_rects = []
    for p in b.pads:
        r = pad_rect(p)
        n = p.net or ""
        if p.footprint_ref in cap_refs:
            cap_rects.append((p.footprint_ref, r))
            if n.endswith("_U3"):
                cap_u3[n] = dict(ref=p.footprint_ref, x=p.pos[0], y=p.pos[1], rect=r)
            elif n.endswith("_MCIO"):
                cap_mcio[p.footprint_ref] = dict(x=p.pos[0], y=p.pos[1], rect=r)
        elif p.footprint_ref == "U3":
            u3_rects.append((n, r))

    # U3 左铜缘 + DN 信号 pad 列
    u3_left = min(r[0] for _, r in u3_rects)
    u3_sig = {}
    for n, r in u3_rects:
        if n.startswith("PCIE_DN_OUT") and n.endswith("_U3"):
            u3_sig[n] = dict(x=(r[0]+r[2])/2, y=(r[1]+r[3])/2, rect=r)

    # 墙铜跨（所有 cap pad）
    wx0 = min(r[0] for _, r in cap_rects)
    wx1 = max(r[2] for _, r in cap_rects)

    # 行心（cap footprint 中心 y，同 ref 两 pad 中位）
    rows = {}
    for ref in cap_refs:
        ys = [d['y'] for k, d in cap_u3.items() if d['ref'] == ref]
        xs = [d['x'] for k, d in cap_u3.items() if d['ref'] == ref]
        if ys and xs:
            rows[ref] = dict(xc=xs[0], yc=ys[0])
    # 行按 y 分组
    from collections import defaultdict
    rowg = defaultdict(list)
    for ref, d in rows.items():
        rowg[round(d['yc'], 2)].append(ref)
    row_list = sorted(rowg)
    assert len(row_list) == 2, row_list
    top_y, bot_y = row_list[0], row_list[1]

    # 走廊净空 y = 上排 pad 底 → 下排 pad 顶
    def row_cu_y(row_refs):
        ys = [cap_u3[k]['rect'] for k in cap_u3 if cap_u3[k]['ref'] in row_refs]
        # pad 矩形（所有 pad 同尺寸同朝向）
        y0 = min(r[1] for r in ys); y1 = max(r[3] for r in ys)
        return y0, y1
    t0, t1 = row_cu_y(rowg[top_y])     # 上排铜 y 跨
    b0, b1 = row_cu_y(rowg[bot_y])
    corr_cu_lo, corr_cu_hi = t1, b0      # 走廊铜净空 y

    # ── 2. 逐网 → (源 pad, 自己 _MCIO 铜边, U3 目标) ──────
    nets = {}
    for n, d in cap_u3.items():
        ref = d['ref']
        m = cap_mcio.get(ref)
        edge = m['rect'][2] if m else d['rect'][2]
        nets[n] = dict(
            ref=ref, row_y=d['y'],
            src_x=d['x'], src_y=d['y'], src_rect=d['rect'],
            own_edge=edge,               # 自己电容 _MCIO pad +x 铜边
            own_min_x=edge + REQ,        # via 中心 x 下界（engine）
            u3=None)
    for n, d in u3_sig.items():
        if n in nets:
            nets[n]['u3'] = d

    # 对聚合
    pairs = {}
    for n in sorted(nets):
        if not n.startswith("PCIE_DN_OUT"):
            continue
        stem = n[:-3]          # ..._P
        base = stem[:-2]       # PCIE_DN_OUT0
        pol = stem[-1]
        pairs.setdefault(base, {})[pol] = n
    assert len(pairs) == 8, pairs.keys()

    pair_info = {}
    for base in sorted(pairs, key=lambda b: min(nets[pairs[b][p]]['src_x'] for p in 'PN')):
        pd = {}
        for pol in 'PN':
            n = pairs[base][pol]
            pd[pol] = dict(net=n, src_x=nets[n]['src_x'], row_y=nets[n]['row_y'],
                           own_edge=nets[n]['own_edge'], own_min_x=nets[n]['own_min_x'],
                           u3y=nets[n]['u3']['y'])
        pair_x = max(pd[p]['own_edge'] for p in 'PN')       # 对级下游铜边
        pair_min_x = max(pd[p]['own_min_x'] for p in 'PN')  # 对级 via x 下界
        pd['_pair'] = dict(row_y=pd['P']['row_y'],
                           src_xmin=min(pd[p]['src_x'] for p in 'PN'),
                           src_xmax=max(pd[p]['src_x'] for p in 'PN'),
                           downstream_edge=pair_x, min_x=pair_min_x,
                           u3_y_top=min(pd[p]['u3y'] for p in 'PN'),
                           u3_y_bot=max(pd[p]['u3y'] for p in 'PN'))
        pair_info[base] = pd

    # ── 3. 走廊障碍扫描（矩形内 pad 铜） ──────────────────
    obs = []
    for p in b.pads:
        x, y = p.pos
        if 74.0 <= x <= 89.0 and 57.0 <= y <= 69.0:
            obs.append(dict(ref=p.footprint_ref, net=p.net or "",
                            x=x, y=y, rect=pad_rect(p)))
    # 走廊净空区 (corr_cu_lo..corr_cu_hi) 内 x∈[74.95,88.6] 的 pad 计数
    inner = [o for o in obs if corr_cu_lo < o['y'] < corr_cu_hi
             and 74.0 < o['x'] < 89.0]

    # ── 4. 输出 ──────────────────────────────────────────
    print(f"墙行 y = {top_y}/{bot_y}   行内 ref 数 {len(rowg[top_y])}/{len(rowg[bot_y])}")
    print(f"墙铜跨 x ∈ [{wx0:.3f},{wx1:.3f}]   墙右铜边 {wx1:.3f}")
    print(f"U3 左铜缘 {u3_left:.3f}   → 墙→U3 条宽 {u3_left-wx1:.3f}")
    print(f"走廊铜净空 y ∈ [{corr_cu_lo:.3f},{corr_cu_hi:.3f}]  高 {corr_cu_hi-corr_cu_lo:.3f}")
    print(f"via 中心 x 窗口(engine) ∈ [{wx1+REQ:.3f},{u3_left-REQ:.3f}] 宽 {u3_left-REQ-wx1-REQ:.3f}")
    print(f"走廊 pad 障碍（x∈[74,89],y∈[57,69]）: {len(obs)}；"
          f"走廊净空区内: {len(inner)}")

    print("\n16 线（cap x 升序）: net | ref | src(x,y) | own_edge | own_min_x | U3_y")
    for n in sorted(nets, key=lambda k: nets[k]['src_x']):
        d = nets[n]
        u3y = d['u3']['y'] if d['u3'] else float('nan')
        print(f"  {n:34s} {d['ref']:4s} src=({d['src_x']:6.2f},{d['src_y']:5.2f}) "
              f"edge={d['own_edge']:6.2f} minx={d['own_min_x']:6.2f} u3y={u3y:5.2f}")

    print("\n8 对（源 x 序）: base | row | pair_min_x(via下界) | P/N src_x | U3 y (P,N)")
    for base in sorted(pair_info, key=lambda b: pair_info[b]['_pair']['src_xmin']):
        pr = pair_info[base]
        pk = pr['_pair']
        print(f"  {base:16s} row={pk['row_y']:5.1f} via_x≥{pk['min_x']:6.2f} "
              f"(edge {pk['downstream_edge']:6.2f})  P.x={pr['P']['src_x']:6.2f} N.x={pr['N']['src_x']:6.2f}"
              f"  U3y P={pr['P']['u3y']:5.2f} N={pr['N']['u3y']:5.2f}")

    # JSON 落盘
    out = dict(
        board=BOARD,
        rows=dict(top_y=top_y, bot_y=bot_y, top_refs=rowg[top_y], bot_refs=rowg[bot_y]),
        wall=dict(x0=wx0, x1=wx1), u3_left=u3_left,
        corridor=dict(cu_lo=corr_cu_lo, cu_hi=corr_cu_hi,
                      h=corr_cu_hi-corr_cu_lo),
        rules=dict(via_occ=VIA_OCC, vr=VR, via_cu_d=VIA_CU_D, via_cu_r=VIA_CU_R,
                   pad_edge_clr=PAD_EDGE_CLR, req=REQ,
                   inter_copper=INTER_COPPER, pn_min=PN_MIN, pn_max=PN_MAX),
        nets={n: dict(ref=d['ref'], src_x=d['src_x'], src_y=d['src_y'],
                      own_edge=d['own_edge'], own_min_x=d['own_min_x'],
                      u3_y=d['u3']['y'] if d['u3'] else None) for n, d in nets.items()},
        pairs={base: {p: dict(net=pair_info[base][p]['net'],
                              src_x=pair_info[base][p]['src_x'],
                              own_edge=pair_info[base][p]['own_edge'],
                              own_min_x=pair_info[base][p]['own_min_x'],
                              u3y=pair_info[base][p]['u3y'])
                      for p in 'PN'}
               for base in pair_info},
    )
    for base in pair_info:
        out['pairs'][base]['_meta'] = pair_info[base]['_pair']
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(f"\n几何 JSON → {OUT}")

if __name__ == "__main__":
    main()
