#!/usr/bin/env python3
"""K2 · P4 增量 11（L2 自裁，owner #14 / #K2-19 / #K2-20）—— **U4-D/G-1 规模化**：
把高速网全部**非 45° 段**在**设计层**确定性重派生为 0/45/90°，保持端点/层/线宽/对内等长。

动因（T-14 + 本轮取证）：冻结折线 2032 条非 45° 段分两类——
 (a) **蛇形调长段 band run**（31 条：In5 1906 腿 / In2 12 / B.Cu 6）：腿长恒定、垂直分量正负交替、
     首尾同边 ⇒ 可精确刻画「带」。长度/跨度比 ρ=L/S 实测 ≤2.05 **> √2** ⇒ 纯 45° 锯齿**数学不可能**
     （T-14 上限 S·√2）⇒ 用 **45° 斜腿 + 90° 竖腿「梳齿」**（ρ 上限 1+√2；齿高 p ≤ 带宽 h
     ⇒ 铜包络**不越原包络** ⇒ 不新增净距风险）。
 (b) **孤立斜腿 single**（108 条：F.Cu 逃逸/扇出短斜段）：45° 腿 + 轴腿三腿式，全程含于原 bbox。

守恒口径（**禁缩口径**）：
 - 端点/层/线宽逐段保持；新段一律 0/45/90° 且**单腿 ≥0.05mm**；**逐段精确替换**（T-13，方向无关匹配）。
 - **整数纳米网格**：KiCad 内部单位 = 1nm ⇒ 全部几何在 1e-6mm 整数域构造，保证 45° 腿 |Δx|≡|Δy|，
   角度偏差 ~1e-12°（判据容差 1e-3°），且端点**逐位闭合**（无 dangling）。
 - 对内(±)长度：以该对「有蛇形段的一侧」为调长器，Δrun = Δsingle(partner) − Δsingle(tuner)
   ⇒ 两侧净值各变 Δsingle(partner)，**对内偏斜逐位守恒**；无配对网 Δrun=−Δsingle ⇒ 总长**不变**。
 - ρ>1+√2 / 单腿<0.05 ⇒ **不落板 + 登记 fail**（fail-closed）。

CLI：k2_p4_u4d_scale_v1.py --in <board> --out <board> --plan <plan.json> [--dry-run]
"""
from __future__ import annotations
import argparse, json, math, os, re, shutil, subprocess, sys, uuid
from collections import defaultdict

NS = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
CTX, CV, LAYERID = None, None, {}
INV = 1000000                      # 1 mm = 1e6 nm（KiCad 内部单位）
LEG_MIN = int(0.05 * INV)          # 单腿下限 0.05mm
TOL = 1e-3
R2 = math.sqrt(2.0)
SEG_BLOCK = ('\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width {w})\n'
             '\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')
NET_RE = re.compile(r'\(net "?([^")\s]+)"?\)')


def _copy_pro(a, b):
    """复制同名 .kicad_pro（同文件则跳过，支持原地改板）。"""
    if os.path.abspath(a) == os.path.abspath(b):
        return
    shutil.copyfile(a, b)


def fmt6(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return s if s else '0'


def seg_uuid(net, layer, w, x1, y1, x2, y2):
    return str(uuid.uuid5(NS, 'k2u4ds|seg|%s|%s|%s|%s|%s|%s|%s' % (
        net, layer, w, x1, y1, x2, y2)))


def ang(p):
    return math.degrees(math.atan2(p[3] - p[1], p[2] - p[0])) % 180.0


def is45(p):
    return min(abs(ang(p) - k) for k in (0, 45, 90, 135, 180)) <= 1e-3


def slen(p):
    return math.hypot(p[2] - p[0], p[3] - p[1])


def kk(x, y):
    return (round(x, 4), round(y, 4))


def parse_board(txt):
    out = []
    for m in re.finditer(r'\t\(segment\n(.*?)\n\t\)\n', txt, re.S):
        b = m.group(1)
        n = NET_RE.search(b)
        lay = re.search(r'\(layer "([^"]+)"\)', b)
        w = re.search(r'\(width ([-\d.]+)\)', b)
        st = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b)
        en = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
        if not (st and en and lay):
            continue
        out.append(dict(s0=m.start(), s1=m.end(), net=(n.group(1) if n else ''),
                        layer=lay.group(1), width=(w.group(1) if w else '0.2'),
                        p=(float(st.group(1)), float(st.group(2)), float(en.group(1)), float(en.group(2)))))
    return out


def build_chains(segs):
    by = defaultdict(list)
    for s in segs:
        by[(s['net'], s['layer'])].append(s)
    chains = {}
    for key, ss in by.items():
        adj = defaultdict(list)
        for i, s in enumerate(ss):
            adj[kk(s['p'][0], s['p'][1])].append(i)
            adj[kk(s['p'][2], s['p'][3])].append(i)
        used = set()
        for i in range(len(ss)):
            if i in used:
                continue
            comp, stack = [], [i]
            while stack:
                j = stack.pop()
                if j in used:
                    continue
                used.add(j); comp.append(j)
                for e in (kk(ss[j]['p'][0], ss[j]['p'][1]), kk(ss[j]['p'][2], ss[j]['p'][3])):
                    stack += [t for t in adj[e] if t not in used]
            deg = defaultdict(int)
            for j in comp:
                deg[kk(ss[j]['p'][0], ss[j]['p'][1])] += 1
                deg[kk(ss[j]['p'][2], ss[j]['p'][3])] += 1
            ends = [q for q, d in deg.items() if d == 1]
            cur = ends[0] if ends else kk(ss[comp[0]]['p'][0], ss[comp[0]]['p'][1])
            rem, seq = set(comp), []
            while rem:
                hit = None
                for j in sorted(rem):
                    q1, q2 = kk(ss[j]['p'][0], ss[j]['p'][1]), kk(ss[j]['p'][2], ss[j]['p'][3])
                    if q1 == cur:
                        hit = (j, q2, ss[j]); break
                    if q2 == cur:
                        pa = ss[j]['p']
                        hit = (j, q1, dict(ss[j], p=(pa[2], pa[3], pa[0], pa[1]))); break
                if not hit:
                    break
                j, cur, sj = hit
                rem.discard(j); seq.append(sj)
            chains.setdefault(key, []).append(seq)
    return chains


class Replace:
    def __init__(self, kind, net, layer, width, old, new_legs, old_len, new_len, meta=None):
        self.kind, self.net, self.layer, self.width = kind, net, layer, width
        self.old, self.new_legs, self.old_len, self.new_len = old, new_legs, old_len, new_len
        self.meta = meta or {}


def ints(p):
    return tuple(int(round(v * INV)) for v in p)


AMIN = int(math.ceil(LEG_MIN / R2))     # 45° 腿单分量下限（腿长 = a·√2 ≥ 0.05）


def k_feasible(ax, ay):
    """可行步数上限（两腿都 ≥ 下限、45° 腿分量 ≥ AMIN）。"""
    if ax >= ay:
        return max(1, min(ay // AMIN, (ax - ay) // LEG_MIN))
    return max(1, min(ax // AMIN, (ay - ax) // LEG_MIN))


def staircase(ax, ay, sx, sy, lead_axis, kmax=None):
    """A→B 的 0/45/90 阶梯（整数 nm）：**贴合原直线**（偏差 ≤ min(ax,ay)/k）。
    ax ≥ ay：45° 爬升腿 + 0° 推进腿；ay > ax：45° 横移腿 + 90° 推进腿。"""
    kf = k_feasible(ax, ay)
    k = kf if kmax is None else max(1, min(int(kmax), kf))
    legs = []
    if ax >= ay:
        ab, r = divmod(ay, k)
        rises = [ab + 1] * r + [ab] * (k - r)
        cb, cr = divmod(ax - ay, k)
        runs = [cb + 1] * cr + [cb] * (k - cr)
        for i in range(k):
            if lead_axis:
                legs.append((sx * runs[i], 0)); legs.append((sx * rises[i], sy * rises[i]))
            else:
                legs.append((sx * rises[i], sy * rises[i])); legs.append((sx * runs[i], 0))
    else:
        ab, r = divmod(ax, k)
        dips = [ab + 1] * r + [ab] * (k - r)
        cb, cr = divmod(ay - ax, k)
        runs = [cb + 1] * cr + [cb] * (k - cr)
        for i in range(k):
            if lead_axis:
                legs.append((0, sy * runs[i])); legs.append((sx * dips[i], sy * dips[i]))
            else:
                legs.append((sx * dips[i], sy * dips[i])); legs.append((0, sy * runs[i]))
    return legs


def build_single(p, lead_axis=False, kmax=None):
    """孤立斜腿 → 贴合直线阶梯（整数 nm；端点逐位闭合）。"""
    X1, Y1, X2, Y2 = ints(p)
    dx, dy = X2 - X1, Y2 - Y1
    ax, ay = abs(dx), abs(dy)
    sx = 1 if dx >= 0 else -1
    sy = 1 if dy >= 0 else -1
    deltas = staircase(ax, ay, sx, sy, lead_axis, kmax)
    pts = [(X1, Y1)]
    x, y = X1, Y1
    for ddx, ddy in deltas:
        x += ddx; y += ddy; pts.append((x, y))
    if (x, y) != (X2, Y2):
        return None, 'endpoint-drift %d,%d' % (x - X2, y - Y2)
    gl = [(px / INV, py / INV) for px, py in pts]
    legs = [(gl[i][0], gl[i][1], gl[i + 1][0], gl[i + 1][1]) for i in range(len(gl) - 1)]
    legs = [l for l in legs if slen(l) > 1e-12]
    if any(slen(l) < 0.05 - 1e-9 for l in legs):
        return None, 'leg<0.05'
    if any(not is45(l) for l in legs):
        return None, 'angle'
    return legs, None


def max_deviation(legs, A, B):
    """阶梯相对原直线 A→B 的最大垂距（mm）——守恒/包络自检。"""
    dx, dy = B[0] - A[0], B[1] - A[1]
    L = math.hypot(dx, dy)
    if L < 1e-12:
        return 0.0
    m = 0.0
    for l in legs:
        for (px, py) in ((l[0], l[1]), (l[2], l[3])):
            m = max(m, abs((px - A[0]) * dy - (py - A[1]) * dx) / L)
    return m


def analyze_run(run):
    if len(run) == 1:
        return dict(kind='single')
    legs = [r['p'] for r in run]
    A = (legs[0][0], legs[0][1]); B = (legs[-1][2], legs[-1][3])
    dT = (B[0] - A[0], B[1] - A[1])
    if abs(dT[1]) <= 1e-6 and abs(dT[0]) > 1e-9:
        us = (1.0 if dT[0] > 0 else -1.0, 0.0)
    elif abs(dT[0]) <= 1e-6 and abs(dT[1]) > 1e-9:
        us = (0.0, 1.0 if dT[1] > 0 else -1.0)
    else:
        return dict(kind='run', why='spine-not-axis')
    vs = (-us[1], us[0])
    du = [(p[2] - p[0]) * us[0] + (p[3] - p[1]) * us[1] for p in legs]
    dv = [(p[2] - p[0]) * vs[0] + (p[3] - p[1]) * vs[1] for p in legs]
    h, cstep = abs(dv[0]), abs(du[0])
    ws = {r['width'] for r in run}
    why = None
    if h < 1e-5 or cstep < 1e-5:
        why = 'degenerate'
    elif any(abs(abs(d) - h) > TOL for d in dv):
        why = 'dv-not-uniform'
    elif any(abs(abs(d) - cstep) > TOL for d in du):
        why = 'du-not-uniform'
    elif any(du[k] * du[k + 1] < 0 for k in range(len(du) - 1)):
        why = 'du-not-monotone'
    elif any(dv[k] * dv[k + 1] > 0 for k in range(len(dv) - 1)):
        why = 'dv-not-alternating'
    elif abs(sum(dv)) > 1e-6:
        why = 'net-dv-nonzero'
    elif len(ws) != 1:
        why = 'mixed-width'
    if why:
        return dict(kind='run', why=why, A=A, B=B, n=len(run))
    return dict(kind='band', A=A, B=B, us=us, vs=vs, h=h, cstep=cstep,
                vdir=1.0 if dv[0] > 0 else -1.0,
                U=abs(round(sum(du) * INV)), L=sum(slen(p) for p in legs),
                width=run[0]['width'], n=len(run), legs=legs)


def build_band(info, L_target):
    """蛇形 band run → 45°+90° 梳齿（整数 nm 局部 (u,v) 系；齿高 p ≤ h；端点逐位闭合）。"""
    A, us, vs = info['A'], info['us'], info['vs']
    h_int = int(round(info['h'] * INV))
    U = info['U']
    vdir = int(round(info['vdir']))
    if U < 1:
        return None, 'span=0'
    sp_ideal = (L_target - U / INV) / R2 * INV
    if sp_ideal < -LEG_MIN:
        return None, 'L<span'
    if sp_ideal > U + LEG_MIN:
        return None, 'rho>1+sqrt2(%.4f)' % (L_target / (U / INV))
    sp_ideal = max(sp_ideal, 0.0)
    if sp_ideal < LEG_MIN:
        m, p_int = (1, LEG_MIN) if sp_ideal > 1 else (0, 0)
    else:
        m = int(math.ceil(sp_ideal / h_int - 1e-12))
        p_int = int(round(sp_ideal / m))
        p_int = max(LEG_MIN, min(h_int, p_int))
    sp_int = m * p_int
    c_int = U - sp_int
    if c_int < 0:
        return None, 'axis<0'
    if c_int == 0:
        style, ngap = 'none', 0
    elif c_int >= (m + 1) * LEG_MIN:
        style, ngap = 'even', m + 1
    elif c_int >= 2 * LEG_MIN:
        style, ngap = 'ends', 2
    else:
        style, ngap = 'lead', 1
    g_int, rem = (c_int // ngap, c_int % ngap) if ngap else (0, 0)
    Ax, Ay = int(round(A[0] * INV)), int(round(A[1] * INV))
    ux, uy = int(round(us[0])), int(round(us[1]))
    vx, vy = int(round(vs[0])), int(round(vs[1]))
    pts = [(Ax, Ay)]
    s, t = 0, 0
    gno = 0

    def gap(g):
        nonlocal s, gno
        gno += 1
        g = g + (rem if gno == ngap else 0)
        if g > 0:
            s += g; pts.append((Ax + ux * s + vx * t, Ay + uy * s + vy * t))
    for i in range(m):
        if style == 'even':
            gap(g_int)
        elif style == 'ends' and i == 0:
            gap(c_int // 2)
        elif style == 'lead' and i == 0:
            gap(c_int)
        s += p_int; t += vdir * p_int
        pts.append((Ax + ux * s + vx * t, Ay + uy * s + vy * t))
        t -= vdir * p_int
        pts.append((Ax + ux * s + vx * t, Ay + uy * s + vy * t))
    if style == 'even':
        gap(g_int)
    elif style == 'ends':
        gap(c_int - c_int // 2)
    if abs(s - U) > 1 or abs(t) > 1:
        return None, 'endpoint-drift %d,%d' % (s - U, t)
    gl = [(x / INV, y / INV) for x, y in pts]
    legs = [(gl[i][0], gl[i][1], gl[i + 1][0], gl[i + 1][1]) for i in range(len(gl) - 1)]
    legs = [l for l in legs if slen(l) > 1e-12]
    if any(slen(l) < 0.05 - 1e-9 for l in legs):
        return None, 'leg<0.05'
    if any(not is45(l) for l in legs):
        return None, 'angle'
    return legs, None


def make_ctx(src):
    """复用本项目 Ctx（障碍层感知精确模型）。失败则返回 (None, None)（退化为纯几何选择）。"""
    try:
        import importlib.util, pcbnew
        here = os.path.dirname(os.path.abspath(__file__))

        def L(n, f):
            sp = importlib.util.spec_from_file_location(n, os.path.join(here, f))
            m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
        f3 = L('k2f3o', 'k2_p4_ls_xlayer_v1.py'); cv = L('k2cvo', 'k2_p4_converge_v1.py')
        global LAYERID
        LAYERID = {pcbnew.LayerName(i): i for i in range(pcbnew.PCB_LAYER_ID_COUNT)}
        return f3.Ctx(pcbnew.LoadBoard(src)), cv
    except Exception as e:
        sys.stderr.write('WARN: 无几何 oracle（%s）\n' % e)
        return None, None


def leg_eval(c, cv, net, layer, hw, seg):
    """腿对**全部外网障碍**的最小净距裕度（mm；<0 = 违规）。口径 = converge_v1 / drc_rules.json。"""
    x1, y1, x2, y2 = seg
    li = LAYERID.get(layer, -9999)
    best = 1e9

    def upd(v):
        nonlocal best
        if v < best:
            best = v
    for e in c.edge:
        upd(cv.seg_seg_dist(x1, y1, x2, y2, *e) - (0.3 + hw))
    for poly in c.keep_t:
        upd(cv.seg_poly_dist(x1, y1, x2, y2, poly))
    for t in c.tracks:
        if t['layer'] != li or t['net'] == net:
            continue
        need = hw + t['hw'] + cv._req(net, t['net'])
        if max(x1, x2) + need < min(t['x1'], t['x2']) or min(x1, x2) - need > max(t['x1'], t['x2']):
            continue
        if max(y1, y2) + need < min(t['y1'], t['y2']) or min(y1, y2) - need > max(t['y1'], t['y2']):
            continue
        upd(cv.seg_seg_dist(x1, y1, x2, y2, t['x1'], t['y1'], t['x2'], t['y2']) - need)
    for p in c.pads.values():
        if p['net'] == net or li not in p['lay']:
            continue
        need = hw + cv._req(net, p['net'])
        if max(x1, x2) + need < p['x'] - p['w'] / 2 or min(x1, x2) - need > p['x'] + p['w'] / 2:
            continue
        if max(y1, y2) + need < p['y'] - p['h'] / 2 or min(y1, y2) - need > p['y'] + p['h'] / 2:
            continue
        if p['circ']:
            upd(cv.pt_seg_dist(p['x'], p['y'], x1, y1, x2, y2) - min(p['w'], p['h']) / 2 - need)
        elif p['poly']:
            upd(cv.seg_poly_dist(x1, y1, x2, y2, p['poly']) - need)
    for v in c.vias.values():
        if v['net'] == net or li not in v['lay']:
            continue
        upd(cv.pt_seg_dist(v['x'], v['y'], x1, y1, x2, y2) - v['r'] - hw - cv._req(net, v['net']))
    # T-28（inc110 · L2 口径修正）：孔-铜**仅计穿过本层（li）的孔**。
    # 原式用 `c.holes`（含全部孔，无层信息）⇒ 对**非本层**孔误报：实测 In2..In5 埋孔的
    # `PCIE_UP7_P`(93.25,49.5) 在 F.Cu 腿旁被误判 −0.0530，逼 u4d 放弃能避开
    # `GND(F→In1)` 盲孔(94.15,49.76)的变体 ⇒ 落成 DRC −0.0053（error 2 之一）。
    for v in c.vias.values():
        if v['net'] == net or v['hole'] <= 0 or li not in v['lay']:
            continue
        upd(cv.pt_seg_dist(v['x'], v['y'], x1, y1, x2, y2) - hw - 0.25 - v['hole'])
    for p in c.pads.values():
        if p['net'] == net or p['hole'] <= 0 or li not in p['lay']:
            continue
        upd(cv.pt_seg_dist(p['x'], p['y'], x1, y1, x2, y2) - hw - 0.25 - p['hole'])
    return best


def legs_eval(c, cv, net, layer, hw, legs):
    """⇒ (违规腿数, 最小裕度)"""
    nv, mm = 0, 1e9
    for l in legs:
        m = leg_eval(c, cv, net, layer, hw, l)
        if m < 0:
            nv += 1
        mm = min(mm, m)
    return nv, mm


def pair_key(net):
    for a, b in (('_P_MCIO', '_MCIO'), ('_N_MCIO', '_MCIO'), ('_P_J2', '_J2'), ('_N_J2', '_J2')):
        if net.endswith(a):
            return net[:-len(a)] + b
    if net.endswith('_P') or net.endswith('_N'):
        return net[:-2]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='src', required=True)
    ap.add_argument('--out', dest='out', default=None)
    ap.add_argument('--plan', dest='plan', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    global CTX, CV
    txt = open(args.src, encoding='utf-8').read()
    segs = parse_board(txt)
    if not args.dry_run and args.out:
        CTX, CV = make_ctx(args.src)
    chains = build_chains(segs)
    net_total, net_single_delta, net_runs = defaultdict(float), defaultdict(float), defaultdict(list)
    for s in segs:
        net_total[s['net']] += slen(s['p'])

    repl, fails = [], []
    for (net, layer), chs in sorted(chains.items()):
        for ch in chs:
            i = 0
            while i < len(ch):
                if is45(ch[i]['p']):
                    i += 1; continue
                j = i
                while j < len(ch) and not is45(ch[j]['p']):
                    j += 1
                run = ch[i:j]
                if len(run) == 1:
                    hw = float(run[0]['width']) / 2.0
                    pl = run[0]['p']
                    A = (pl[0], pl[1]); B = (pl[2], pl[3])
                    axn, ayn = abs(pl[2] - pl[0]), abs(pl[3] - pl[1])
                    kf = k_feasible(int(round(axn * INV)), int(round(ayn * INV)))
                    cands = []
                    chosen = None

                    def _try(nk, la):
                        legs, err = build_single(pl, la, nk)
                        if err:
                            return None
                        dev = max_deviation(legs, A, B)
                        if CTX and CV:
                            nv, mm = legs_eval(CTX, CV, net, layer, hw, legs)
                        else:
                            nv, mm = 0, -dev
                        return (nv, -round(mm, 6), dev, la, nk, legs)

                    # 候选序固定（k 从大到小 = 偏差最小优先；每 k 先 False 后 True），取**首个无违规者**
                    for nk in range(kf, max(0, kf - 12), -1):
                        for la in (False, True):
                            c = _try(nk, la)
                            if c:
                                cands.append(c)
                                if c[0] == 0 and chosen is None:
                                    chosen = c
                        if chosen is not None:
                            break
                    if chosen is None and cands:
                        chosen = sorted(cands)[0]
                    if not cands:
                        _, err = build_single(run[0]['p'], False)
                        fails.append(dict(net=net, layer=layer, kind='single', why=err, p=list(run[0]['p'])))
                    else:
                        nv, nmm, dev, la, nk, legs = chosen
                        ol = slen(run[0]['p']); nl = sum(slen(l) for l in legs)
                        net_single_delta[net] += nl - ol
                        repl.append(Replace('single', net, layer, run[0]['width'], [run[0]['p']], legs, ol, nl,
                                            dict(lead_axis=la, dev=round(dev, 4), k=nk, n_cand=len(cands),
                                                 oracle_viol=nv, oracle_margin=round(-nmm, 4))))
                else:
                    info = analyze_run(run)
                    if info.get('why'):
                        fails.append(dict(net=net, layer=layer, kind='run', why=info['why'],
                                          n=len(run), A=list(info.get('A') or []), B=list(info.get('B') or [])))
                    else:
                        info['net'], info['layer'] = net, layer
                        net_runs[net].append(info)
                i = j

    pair_adj = {}
    for net in sorted(net_runs):
        pk = pair_key(net)
        partner = None
        if pk:
            for cand in net_total:
                if cand != net and pair_key(cand) == pk:
                    partner = cand; break
        if partner is None:
            pair_adj[net] = -net_single_delta[net]
        else:
            pair_adj[net] = net_single_delta.get(partner, 0.0) - net_single_delta[net]
        if partner is not None and partner in net_runs:
            pair_adj[net] = None

    for net in sorted(net_runs):
        runs = net_runs[net]
        cap = sum(max(r['L'] - r['U'] / INV, 0.0) for r in runs) or 1.0
        adj = pair_adj.get(net)
        for r in runs:
            share = (max(r['L'] - r['U'] / INV, 0.0) / cap) if adj is not None else 0.0
            L_target = r['L'] + (adj * share if adj is not None else 0.0)
            legs, err = build_band(r, L_target)
            if err:
                fails.append(dict(net=net, layer=r['layer'], kind='band', why=err, n=r['n'],
                                  A=list(r['A']), B=list(r['B']), L=r['L'], L_target=L_target))
                continue
            repl.append(Replace('band', net, r['layer'], r['width'], r['legs'], legs,
                                r['L'], sum(slen(l) for l in legs),
                                dict(n=r['n'], h=r['h'], U=r['U'] / INV, cstep=r['cstep'],
                                     L_target=round(L_target, 4), rho=round(r['L'] / (r['U'] / INV), 5),
                                     adj=None if adj is None else round(adj, 4))))

    new_total = dict(net_total)
    for r in repl:
        new_total[r.net] = new_total.get(r.net, 0.0) - r.old_len + r.new_len
    pairs = {}
    for net, tot in sorted(net_total.items()):
        pk = pair_key(net)
        if pk:
            pairs.setdefault(pk, {})[net] = (round(tot, 4), round(new_total[net], 4))
    skew_old, skew_new = {}, {}
    for pk, d in pairs.items():
        if len(d) == 2:
            (_, v1), (_, v2) = list(d.items())
            skew_old[pk] = round(abs(v1[0] - v2[0]), 4)
            skew_new[pk] = round(abs(v1[1] - v2[1]), 4)
    n_old = sum(len(r.old) for r in repl)
    n_new = sum(len(r.new_legs) for r in repl)
    plan = dict(src=args.src, src_bytes=len(txt),
                replaced_band_runs=sum(1 for r in repl if r.kind == 'band'),
                replaced_singles=sum(1 for r in repl if r.kind == 'single'),
                legs_old=n_old, legs_new=n_new, fails=fails,
                nets_touched=sorted({r.net for r in repl}),
                delta_by_net={n: round(new_total[n] - net_total[n], 4) for n in sorted(new_total)
                              if abs(new_total[n] - net_total[n]) > 1e-9},
                skew_old=skew_old, skew_new=skew_new,
                skew_old_max=(max(skew_old.values()) if skew_old else None),
                skew_new_max=(max(skew_new.values()) if skew_new else None),
                details=[dict(kind=r.kind, net=r.net, layer=r.layer, width=r.width, n_old=len(r.old),
                              old_len=round(r.old_len, 4), new_len=round(r.new_len, 4),
                              delta=round(r.new_len - r.old_len, 4), n_new=len(r.new_legs),
                              angles=sorted({round(ang(l), 3) for l in r.new_legs}), meta=r.meta)
                         for r in repl])
    json.dump(plan, open(args.plan, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('legs %d → %d · band runs %d · singles %d · fails %d' % (
        n_old, n_new, plan['replaced_band_runs'], plan['replaced_singles'], len(fails)))
    print('对内偏斜 max: %s → %s' % (plan['skew_old_max'], plan['skew_new_max']))
    if fails:
        print('!! FAILS:')
        for f in fails[:20]:
            print('   ', f)
        return 3
    if args.dry_run or not args.out:
        return 0

    covered = set()
    for r in repl:
        for p in r.old:
            q1, q2 = kk(p[0], p[1]), kk(p[2], p[3])
            covered.add((r.net, r.layer) + ((q1, q2) if q1 <= q2 else (q2, q1)))
    out, i, n_cut = [], 0, 0
    for s in segs:
        p = s['p']
        q1, q2 = kk(p[0], p[1]), kk(p[2], p[3])
        if (s['net'], s['layer']) + ((q1, q2) if q1 <= q2 else (q2, q1)) in covered:
            out.append(txt[i:s['s0']]); i = s['s1']; n_cut += 1
    out.append(txt[i:])
    body = ''.join(out)
    assert n_cut == n_old, 'cut %d != %d' % (n_cut, n_old)
    blocks = []
    for r in repl:
        for l in r.new_legs:
            u = seg_uuid(r.net, r.layer, r.width, l[0], l[1], l[2], l[3])
            blocks.append(SEG_BLOCK.format(x1=fmt6(l[0]), y1=fmt6(l[1]), x2=fmt6(l[2]), y2=fmt6(l[3]),
                                           w=r.width, layer=r.layer, net=r.net, u=u))
    anchor = body.index('\t(segment\n')
    tmp = args.out + '.u4ds_tmp.kicad_pcb'
    open(tmp, 'w', encoding='utf-8').write(body[:anchor] + ''.join(blocks) + body[anchor:])
    src_pro = re.sub(r'\.kicad_pcb$', '.kicad_pro', args.src)
    _copy_pro(src_pro, re.sub(r'\.kicad_pcb$', '.kicad_pro', tmp))
    r = subprocess.run([sys.executable, '-c',
                        "import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[2])",
                        tmp, args.out], capture_output=True, text=True)
    if r.returncode != 0:
        print('FILL FAIL', r.stderr[-500:]); return 2
    _copy_pro(src_pro, re.sub(r'\.kicad_pcb$', '.kicad_pro', args.out))
    os.remove(tmp)
    print('written', args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
