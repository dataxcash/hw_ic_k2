#!/usr/bin/env python3
# U4-D/G-1 试点（增量 10）：REFCLK 两对「设计层重派生 0/45/90 + 对内等长」**计划器**（只产计划 JSON，不改板）。

"""U4-D 试点（改进版）：REFCLK 两对重派生 0/45/90° + 守恒闸 + 变体搜索（只写 /tmp）。"""
import importlib.util, json, math, os, re, shutil, subprocess, sys
sys.path.insert(0, '/home/fila/jqdDev_2025/ic_hw/k2/tools')
def L(n, f):
    sp = importlib.util.spec_from_file_location(n, '/home/fila/jqdDev_2025/ic_hw/k2/tools/' + f)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
g = L('g', 'k2_p4_ls_in2_v1.py'); f3 = g.f3
import pcbnew
F, IN2 = pcbnew.F_Cu, pcbnew.In2_Cu
SRC = sys.argv[1]; OUTJSON = sys.argv[2]
txt = open(SRC, encoding='utf-8').read()
def ang(x1, y1, x2, y2): return math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0
def is45(a): return min(abs(a - k) for k in (0, 45, 90, 135, 180)) <= 0.001
def slen(s): return math.hypot(s[2] - s[0], s[3] - s[1])

def zig_variants(p, q, L0, n0, orig_amp):
    """锯齿链 0/45/90 变体：n ∈ {n0-4..n0+4}（偶），a=min(L0/(n√2), span/n)，南/北两向，轴段分布 {首、尾、中}。"""
    out = []
    span = abs(q[0] - p[0]); sgn = 1.0 if q[0] > p[0] else -1.0
    for n in range(max(2, n0 - 4), n0 + 5, 2):
        # 长度闭合：total = span + n·a·(√2−1) ⇒ a = (L0−span)/(n(√2−1))（L0 ≥ span）；
        #          L0 < span ⇒ 取 a = span/n（该链 45° 下的**长度上限** = span·√2），差额如实登记
        if L0 >= span + 1e-9:
            a = (L0 - span) / (n * (math.sqrt(2.0) - 1.0))
        else:
            a = span / n
        a = min(a, span / n)
        for d0 in ((-1.0 if p[1] < q[1] else 1.0), (1.0 if p[1] < q[1] else -1.0)):
            for split in (0, 1, 2):      # 轴段放在 首/尾/前后各半
                axis_tot = span - n * a
                lead = [0.0, axis_tot, axis_tot / 2.0][split]
                tail = axis_tot - lead
                legs, x, y = [], p[0], p[1]
                if lead > 1e-9: legs.append((x, y, x + sgn * lead, y)); x += sgn * lead
                for i in range(n):
                    dd = d0 if i % 2 == 0 else -d0
                    legs.append((x, y, x + sgn * a, y + dd * a)); x, y = legs[-1][2], legs[-1][3]
                if tail > 1e-9: legs.append((x, y, x + sgn * tail, y))
                amp = a
                out.append(dict(legs=legs, n=n, a=round(a, 4), amp=round(amp, 4), amp_ok=amp <= orig_amp + 1e-9,
                                length=round(sum(slen(s) for s in legs), 4), split=split, dir=d0))
    return out

def tune_variants(p, q, added, m=4, amp_dir=1.0):
    """直段调长：m 对 45° 齿（每对净位移 2a·x，增补长度 2a(√2−1)）⇒ a = added/(m·2(√2−1))。"""
    span = abs(q[0] - p[0]); sgn = 1.0 if q[0] > p[0] else -1.0
    a = added / (m * 2.0 * (math.sqrt(2.0) - 1.0))
    out = []
    for d0 in (amp_dir, -amp_dir):
        legs, x, y = [], p[0], p[1]
        axis_head = (span - 2.0 * m * a) / 2.0
        if axis_head > 1e-9: legs.append((x, y, x + sgn * axis_head, y)); x += sgn * axis_head
        for i in range(m):
            legs.append((x, y, x + sgn * a, y + d0 * a)); x, y = legs[-1][2], legs[-1][3]
            legs.append((x, y, x + sgn * a, y - d0 * a)); x, y = legs[-1][2], legs[-1][3]
        if abs(q[0] - x) > 1e-9: legs.append((x, y, q[0], q[1]))
        out.append(dict(legs=[l for l in legs if slen(l) > 1e-9], a=round(a, 4), amp=round(a, 4),
                        length=round(sum(slen(s) for s in legs), 4), variant='tune m=%d dir=%+.0f' % (m, d0)))
    return out


def short_variants(p, q):
    """短斜段 0/45/90 变体：4 个 L 形（45° 段四象限）+ 3 段（45° 段居中）。"""
    out = []
    dx, dy = q[0] - p[0], q[1] - p[1]
    sx, sy = (1.0 if dx > 0 else -1.0), (1.0 if dy > 0 else -1.0)
    a = min(abs(dx), abs(dy))
    for ax_first in (False, True):
        for sgx in (1.0, -1.0):
            for sgy in (1.0, -1.0):
                A = (p[0], p[1]); legs = []
                if a < 1e-9:
                    legs = [(p[0], p[1], q[0], q[1])]
                elif ax_first:
                    # 轴段（x 或 y 之一）→ 45° → 轴段
                    legs = [(p[0], p[1], p[0] + sx * (abs(dx) - a), p[1]),
                            (p[0] + sx * (abs(dx) - a), p[1], p[0] + sx * (abs(dx) - a) + sgx * a, p[1] + sgy * a),
                            (p[0] + sx * (abs(dx) - a) + sgx * a, p[1] + sgy * a, q[0], q[1])]
                else:
                    legs = [(p[0], p[1], p[0] + sgx * a, p[1] + sgy * a),
                            (p[0] + sgx * a, p[1] + sgy * a, q[0], p[1] + sgy * a),
                            (q[0], p[1] + sgy * a, q[0], q[1])]
                legs = [l for l in legs if slen(l) > 1e-9]
                if legs: out.append(dict(legs=legs, a=round(a, 4), length=round(sum(slen(s) for s in legs), 4),
                                         variant=('ax_first' if ax_first else 'diag_first') + ('+x' if sgx > 0 else '-x') + ('+y' if sgy > 0 else '-y')))
    return out

PLAN = [
 ('PCIE_REFCLK0_P', [(F, 'zig', (67.05, 45.9), (81.35, 45.9), 6, 18.1758, 1.87), (F, 'axis', (81.35, 45.9), (82.35, 45.9))]),
 ('PCIE_REFCLK0_N', [(F, 'short', (135.0, 45.9), (133.825, 46.09)), (IN2, 'short', (133.825, 46.09), (131.45, 45.4))]),
 ('PCIE_REFCLK1_P', [(F, 'zig', (67.05, 63.282), (82.35, 63.282), 10, 22.6599, 1.758),
                      (F, 'tune', (82.35, 63.282), (106.825, 63.282), 0.9812, 4, 1.0, (82.35, 63.282, 106.825, 63.282))]),
 ('PCIE_REFCLK1_N', [(F, 'short', (135.0, 51.3), (133.825, 51.49))]),
]
b = pcbnew.LoadBoard(SRC); sm = g.SpanModel(f3.Ctx(b), b)
def net_segs(net):
    out = []
    for m in re.finditer(r'\t\(segment\n(.*?)\n\t\)\n', txt, re.S):
        blk = m.group(1)
        if not re.search(r'\(net "%s"\)' % re.escape(net), blk): continue
        st = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', blk); en = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', blk)
        lay = re.search(r'\(layer "([^"]+)"\)', blk).group(1)
        out.append((lay, tuple(map(float, (st.group(1), st.group(2), en.group(1), en.group(2))))))
    return out
res = {}
for net, chains in PLAN:
    old = net_segs(net)
    old_total = sum(slen(s[1]) for s in old)
    chains_old = []
    chosen = []
    for (lay, kind, p, q, *rest) in chains:
        ov = rest[3] if (kind == 'tune' and len(rest) > 3) else None
        if ov:
            old_len = sum(slen(s[1]) for s in old
                          if (abs(s[1][0] - ov[0]) < 1e-6 and abs(s[1][1] - ov[1]) < 1e-6 and abs(s[1][2] - ov[2]) < 1e-6 and abs(s[1][3] - ov[3]) < 1e-6)
                          or (abs(s[1][0] - ov[2]) < 1e-6 and abs(s[1][1] - ov[3]) < 1e-6 and abs(s[1][2] - ov[0]) < 1e-6 and abs(s[1][3] - ov[1]) < 1e-6))
        else:
            old_len = sum(slen(s[1]) for s in old
                          if (min(s[1][0], s[1][2]), min(s[1][1], s[1][3])) >= (min(p[0], q[0]) - 1e-6, min(p[1], q[1]) - 1e-6)
                          and (max(s[1][0], s[1][2]), max(s[1][1], s[1][3])) <= (max(p[0], q[0]) + 1e-6, max(p[1], q[1]) + 1e-6))
        cands = tune_variants(p, q, rest[0], rest[1], rest[2]) if kind == 'tune' else (
            zig_variants(p, q, rest[1], rest[0], rest[2]) if kind == 'zig' else (
            [dict(legs=[(p[0], p[1], q[0], q[1])], length=round(slen((p[0], p[1], q[0], q[1])), 4), a=0, amp_ok=True, variant='axis')] if kind == 'axis'
            else short_variants(p, q)))
        best = None
        for c in cands:
            oks = all(is45(ang(*s)) and sm.seg_ok(lay, net, *s) for s in c['legs'])
            score = (abs(c['length'] - old_len), 0 if c.get('amp_ok', True) else 1)
            if oks and (best is None or score < best[0]): best = (score, c)
        if best is None:
            # 记录：所有变体均不通（列第一个失败原因）
            chosen.append(dict(chain=kind, p=p, q=q, layer=pcbnew.LayerName(lay), old_len=round(old_len, 4), fail='no-variant-passed'))
        else:
            chosen.append(dict(chain=kind, p=p, q=q, layer=pcbnew.LayerName(lay), old_len=round(old_len, 4),
                               new_len=best[1]['length'], delta=round(best[1]['length'] - old_len, 4),
                               n_legs=len(best[1]['legs']), a=best[1].get('a'), amp=best[1].get('amp'),
                               variant=best[1].get('variant') or ('n=%d split=%d dir=%d' % (best[1]['n'], best[1]['split'], best[1]['dir'])),
                               angles=[round(ang(*s), 2) for s in best[1]['legs']], legs=best[1]['legs']))
    res[net] = dict(old_total=round(old_total, 4), chains=chosen)
# 新净长 = 旧净长 - Σ链旧长 + Σ链新长（无变体者保持原样）
for net, chains in PLAN:
    d = res[net]; delta = 0.0
    for c in d['chains']:
        delta += (c['new_len'] - c['old_len']) if 'new_len' in c else 0.0
    d['new_total'] = round(d['old_total'] + delta, 4); d['delta_total'] = round(delta, 4)
for a, bb in (('PCIE_REFCLK0_P', 'PCIE_REFCLK0_N'), ('PCIE_REFCLK1_P', 'PCIE_REFCLK1_N')):
    res['SKEW ' + a.replace('PCIE_', '')] = dict(old=round(abs(res[a]['old_total'] - res[bb]['old_total']), 4),
                                                new=round(abs(res[a]['new_total'] - res[bb]['new_total']), 4))
json.dump(res, open(OUTJSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if k.startswith('SKEW') else {kk: v[kk] for kk in ('old_total', 'new_total', 'delta_total')}) for k, v in res.items()}, ensure_ascii=False, indent=1))
print('--- 链明细 ---')
for net, chains in PLAN:
    for c in res[net]['chains']:
        print('%-18s %-7s %-14s old=%8.4f new=%s %s angles=%s' % (net, c['chain'], c['variant'], c['old_len'],
              c.get('new_len', 'FAIL'), ('Δ=%+.4f' % c['delta']) if 'delta' in c else '', c.get('angles')))
