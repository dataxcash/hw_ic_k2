#!/usr/bin/env python3
# U4-D/G-1 守恒基线**测量器**（只读；增量 10 起）：每条高速网的段数/链数/总长/非45角度直方图 + 对内(±)等长基线。
# 用法：python3 k2/tools/k2_p4_hs_baseline_v1.py <board.kicad_pcb> <out.json>（纯 stdlib）

"""U4-D（G-1）阶段 H · 步骤 1：**冻结折线只读取证 + 守恒基线**（ENG 草案；不改板）。
输出：每条高速网的 段数/链数/总长/角度直方图 + 对内(±)与对间长度基线 ⇒ 重解（0/45/90°）的守恒输入。
守恒闸（#K2-20 §一）：85Ω±10%（宽/叠层不变 ⇒ 不受重解影响）· 对内 ≤0.15 · 对间 ≤1.0 ·
逃逸不退化 · 非 45° = 0。
"""
import json, math, re, sys
from collections import defaultdict
BOARD = sys.argv[1] if len(sys.argv) > 1 else 'k2/hw/k2_v4_8L.l5.kicad_pcb'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/opencode/p4/draft/u4d_baseline.json'
txt = open(BOARD, encoding='utf-8').read()
segs = []
for m in re.finditer(r'\t\(segment\n(.*?)\n\t\)\n', txt, re.S):
    b = m.group(1)
    g = lambda k: re.search(r'\(%s "?([^")\s]+)"?\)' % k, b)
    st = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b); en = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
    segs.append(dict(net=(g('net').group(1) if g('net') else ''), layer=(g('layer').group(1) if g('layer') else ''),
                     x1=float(st.group(1)), y1=float(st.group(2)), x2=float(en.group(1)), y2=float(en.group(2))))
def ang(s):
    a = math.degrees(math.atan2(s['y2'] - s['y1'], s['x2'] - s['x1'])) % 180.0
    return a
def is45(a): return min(abs(a - k) for k in (0, 45, 90, 135, 180)) <= 0.001
def key(p): return (round(p[0], 4), round(p[1], 4))
per_net = defaultdict(list)
for s in segs:
    if s['net'].startswith(('PCIE_', 'REFCLK')): per_net[s['net']].append(s)
rows, hist = [], defaultdict(int)
for net, ss in sorted(per_net.items()):
    L = sum(math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']) for s in ss)
    nb = sum(1 for s in ss if not is45(ang(s)))
    for s in ss:
        if not is45(ang(s)): hist[round(ang(s), 1)] += 1
    # 简单链数（按端点连通分量数）
    adj = defaultdict(set)
    for s in ss:
        a, b2 = key((s['x1'], s['y1'])), key((s['x2'], s['y2']))
        adj[a].add(b2); adj[b2].add(a)
    seen, chains = set(), 0
    for v in adj:
        if v in seen: continue
        chains += 1; stack = [v]
        while stack:
            u = stack.pop()
            if u in seen: continue
            seen.add(u); stack += [w for w in adj[u] if w not in seen]
    rows.append(dict(net=net, layer=ss[0]['layer'], n_segments=len(ss), n_non45=nb,
                     chains=chains, length_mm=round(L, 4), net_class_width_mm=0.16 if ss[0]['layer'] in ('In2.Cu', 'In5.Cu') else 0.205))
pairs = {}
for r in rows:
    base = re.sub(r'_[PN]$', '', r['net'])
    pairs.setdefault(base, {})['P' if r['net'].endswith('_P') else ('N' if r['net'].endswith('_N') else '?')] = r['length_mm']
skew = {k: round(abs(v.get('P', 0) - v.get('N', 0)), 4) for k, v in pairs.items() if 'P' in v and 'N' in v}
doc = dict(board=BOARD, hs_nets=len(rows), hs_segments=sum(r['n_segments'] for r in rows),
           hs_non45_segments=sum(r['n_non45'] for r in rows),
           total_length_mm=round(sum(r['length_mm'] for r in rows), 4),
           angle_histogram_non45={str(k): v for k, v in sorted(hist.items())},
           intra_pair_skew_mm=skew, intra_pair_max_mm=(max(skew.values()) if skew else None),
           nets=rows)
json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: doc[k] for k in ('hs_nets', 'hs_segments', 'hs_non45_segments', 'total_length_mm', 'intra_pair_max_mm')}, ensure_ascii=False))
print('角度直方图（非 45° 段, top10）:', dict(sorted(hist.items(), key=lambda kv: -kv[1])[:10]))
