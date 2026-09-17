#!/usr/bin/env python3
"""K2 · P4 · J-8 余项测量件（只读、纯 stdlib）：器件重叠 / 密度分布 / 工艺极限（关键间距侧证据）。

背景：J-8（器件位置合理性：重叠/出框/密度分布/关键间距/固定孔/回避区）中，出框与回避区已由草案
`board_frame_and_keepout` 覆盖、固定孔由 `drill_count` 覆盖；余项 = 重叠 / 密度分布 / 关键间距
（`density_and_spacing` 阈值为 null ⇒ fail-closed，待监理填）。本件**只交测量**，不含判定阈值。

关键实测事实（本板）：**40/59 件封装无 courtyard 图形** ⇒ DRC `courtyards_overlap` 对这 40 件
**结构上不可判**（无 courtyard 可重叠）⇒ 「重叠 = 0 由 DRC 覆盖」为**过宽陈述**，本件以
「封装 AABB（铜+图形）」做 courtyard-free 的**上界**复核，并区分同网/异网 pad 交叠。

用法：
  python3 k2/tools/k2_p4_j8_measure_v1.py [--board k2/hw/k2_v4_8L.l5.kicad_pcb] [--pro ...] [--json /tmp/out.json]
"""
import argparse, collections, json, math, re, sys

TOKEN_RE = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')

def parse(text):
    toks = TOKEN_RE.findall(text); pos = 0
    def rd():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '(':
            out = []
            while toks[pos] != ')': out.append(rd())
            pos += 1; return out
        return t[1:-1] if t.startswith('"') else t
    while toks[pos] != '(': pos += 1
    return rd()

def one(n, k):
    for c in n:
        if isinstance(c, list) and c and c[0] == k: return c
    return None

def all_(n, k):
    return [c for c in n if isinstance(c, list) and c and c[0] == k]

def nums(node, i=1):
    return [float(x) for x in node[i:]]

def rot_pt(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)

def rect_aabb(cx, cy, w, h, deg):
    pts = [rot_pt(sx * w / 2, sy * h / 2, deg) for sx in (-1, 1) for sy in (-1, 1)]
    xs = [cx + p[0] for p in pts]; ys = [cy + p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

def circle_aabb(cx, cy, r):
    return cx - r, cy - r, cx + r, cy + r

def union(boxes):
    if not boxes: return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))

def inter(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0]); dy = min(a[3], b[3]) - max(a[1], b[1])
    return (dx, dy) if dx > 0 and dy > 0 else None

def measure(board):
    root = parse(open(board, encoding='utf-8').read())
    fps, out = all_(root, 'footprint'), []
    for fp in fps:
        ref = None
        for p in all_(fp, 'property'):
            if len(p) > 2 and p[1] == 'Reference': ref = p[2]
        at = nums(one(fp, 'at') or ['at', 0, 0]); fx, fy = (at + [0, 0])[:2]; frot = at[2] if len(at) > 2 else 0.0
        boxes, pads, courtyard, gfx = [], [], [], 0
        for pad in all_(fp, 'pad'):
            num, ptype = pad[1], pad[2]
            pat = nums(one(pad, 'at') or ['at', 0, 0]); psz = nums(one(pad, 'size') or ['size', 0, 0])
            prot = pat[2] if len(pat) > 2 else 0.0
            px, py = rot_pt(pat[0], pat[1], frot)
            ax, ay = fx + px, fy + py
            box = rect_aabb(ax, ay, psz[0], psz[1], frot + prot)
            netn = one(pad, 'net')
            pads.append(dict(ref=ref, num=num, type=ptype, net=(netn[1] if netn and len(netn) > 1 else None),
                             x=ax, y=ay, w=psz[0], h=psz[1], rot=frot + prot, box=box, layers=str(one(pad, 'layers') or '')))
            boxes.append(box)
        for g in all_(fp, 'fp_line') + all_(fp, 'fp_rect') + all_(fp, 'fp_circle') + all_(fp, 'fp_arc') + all_(fp, 'fp_poly'):
            layers = str(one(g, 'layer') or one(g, 'layers') or '')
            if 'CrtYd' in layers or 'Courtyard' in layers: courtyard.append(layers)
            gfx += 1
            if g[0] == 'fp_line':
                a = one(g, 'start') or one(g, 'end'); b = one(g, 'end') or one(g, 'start')
                pa = rot_pt(float(a[1]), float(a[2]), frot); pb = rot_pt(float(b[1]), float(b[2]), frot)
                boxes.append((min(fx+pa[0], fx+pb[0]), min(fy+pa[1], fy+pb[1]), max(fx+pa[0], fx+pb[0]), max(fy+pa[1], fy+pb[1])))
            elif g[0] == 'fp_rect':
                c = one(g, 'start'); e = one(g, 'end')
                pc = rot_pt(float(c[1]), float(c[2]), frot); pe = rot_pt(float(e[1]), float(e[2]), frot)
                boxes.append((min(fx+pc[0], fx+pe[0]), min(fy+pc[1], fy+pe[1]), max(fx+pc[0], fx+pe[0]), max(fy+pc[1], fy+pe[1])))
            elif g[0] == 'fp_circle':
                c = one(g, 'center'); e = one(g, 'end')
                pc = rot_pt(float(c[1]), float(c[2]), frot); pe = rot_pt(float(e[1]), float(e[2]), frot)
                r = math.hypot(pe[0]-pc[0], pe[1]-pc[1])
                boxes.append(circle_aabb(fx+pc[0], fy+pc[1], r))
        out.append(dict(ref=ref, at=(fx, fy, frot), npad=len(pads), pads=pads,
                        courtyard=sorted(set(courtyard)), ngfx=gfx, box=union(boxes)))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', default='k2/hw/k2_v4_8L.l5.kicad_pcb')
    ap.add_argument('--pro', default='k2/hw/k2_v4_8L.l5.kicad_pro')
    ap.add_argument('--json', default=None)
    ap.add_argument('--grid', type=float, default=10.0)
    a = ap.parse_args()
    fps = measure(a.board)
    res = {}

    # 1) courtyard 覆盖
    withc = [f['ref'] for f in fps if f['courtyard']]
    without = [f['ref'] for f in fps if not f['courtyard']]
    res['courtyard'] = dict(n_with=len(withc), n_without=len(without), without=without)
    print(f"[1] courtyard 覆盖: 有 {len(withc)} / 无 {len(without)}（共 {len(fps)}）")
    print(f"    无 courtyard: {without}")

    # 2) 封装 AABB 重叠候选（courtyard-free 上界）
    pairs = []
    for i in range(len(fps)):
        for j in range(i+1, len(fps)):
            A, B = fps[i]['box'], fps[j]['box']
            if not A or not B: continue
            ov = inter(A, B)
            if ov: pairs.append((fps[i]['ref'], fps[j]['ref'], round(ov[0], 3), round(ov[1], 3)))
    res['aabb_overlaps'] = pairs
    hasc = {f['ref'] for f in fps if f['courtyard']}
    both = [p for p in pairs if p[0] in hasc and p[1] in hasc]
    res['aabb_overlap_both_courtyard'] = both
    print(f"[2] 封装 AABB 重叠候选（铜+图形上界）: {len(pairs)} 对；其中**两侧皆有 courtyard**（可用 DRC courtyards_overlap 判真重叠）= {len(both)}")
    for p in pairs[:8]:
        tag = 'both-courtyard' if (p[0] in hasc and p[1] in hasc) else '不可判(至少一侧无 courtyard)'
        print(f"    {p[0]} ↔ {p[1]}  dx={p[2]}mm dy={p[3]}mm  [{tag}]")

    # 3) 跨封装 pad 交叠（同网/异网）
    allp = [(f['ref'], p) for f in fps for p in f['pads']]
    same, diff = [], []
    for i in range(len(allp)):
        for j in range(i+1, len(allp)):
            (r1, p1), (r2, p2) = allp[i], allp[j]
            if r1 == r2: continue
            ov = inter(p1['box'], p2['box'])
            if ov:
                (same if (p1['net'] and p1['net'] == p2['net']) else diff).append(
                    (r1, p1['num'], r2, p2['num'], p1['net'], p2['net'], round(ov[0], 3), round(ov[1], 3)))
    res['pad_overlap'] = dict(same_net=len(same), diff_net=len(diff), diff_samples=diff[:10])
    print(f"[3] 跨封装 pad AABB 交叠: 同网 {len(same)} 对 · 异网 {len(diff)} 对")
    for s in diff[:5]: print(f"    {s[0]}.{s[1]} ({s[4]}) ↔ {s[2]}.{s[3]} ({s[5]}) dx={s[6]} dy={s[7]}")

    # 4) 密度分布（grid mm 网格）
    g = a.grid
    fcells = collections.Counter(); pcells = collections.Counter()
    for f in fps:
        if f['box']:
            fcells[(int(f['at'][0] // g), int(f['at'][1] // g))] += 1
        for p in f['pads']:
            pcells[(int(p['x'] // g), int(p['y'] // g))] += 1
    def top(c, n=3):
        return [dict(cell=[k[0]*g, k[1]*g], n=v) for k, v in c.most_common(n)]
    res['density'] = dict(grid_mm=g, fp_peak=max(fcells.values()), fp_top=top(fcells), pad_peak=max(pcells.values()),
                          pad_top=top(pcells), fp_hist=dict(collections.Counter(fcells.values())))
    print(f"[4] 密度（{g:g}mm 格）: 封装峰值 {max(fcells.values())} 件/格 {top(fcells,3)}")
    print(f"    pad 峰值 {max(pcells.values())} pad/格 {top(pcells,2)}；封装直方图 {res['density']['fp_hist']}")

    # 5) 工艺极限（板实达到值）
    segs, vias, holes = all_(parse(open(a.board, encoding='utf-8').read()), 'segment'), \
                        all_(parse(open(a.board, encoding='utf-8').read()), 'via'), \
                        all_(parse(open(a.board, encoding='utf-8').read()), 'footprint')
    tw = [float(one(s, 'width')[1]) for s in segs if one(s, 'width')]
    vd = [float(one(v, 'size')[1]) for v in vias if one(v, 'size')]
    vdr = [float(one(v, 'drill')[1]) for v in vias if one(v, 'drill')]
    holes = [p for f in holes for p in all_(f, 'pad') if p[2] in ('thru_hole', 'np_thru_hole')]
    hd = [float(one(h, 'drill')[1]) for h in holes if one(h, 'drill')]
    res['process_min'] = dict(min_track_width=min(tw), n_track_widths=len(tw), min_via_diameter=min(vd),
                              min_via_drill=min(vdr), min_via_annular=round((min(vd)-min(vdr))/2, 4),
                              n_vias=len(vd), min_hole_drill=min(hd), n_holes=len(hd))
    try:
        pro = json.load(open(a.pro, encoding='utf-8'))
        rr = pro['board']['design_settings'].get('rules', {})
        res['rules'] = {k: rr.get(k) for k in ('min_track_width','min_via_diameter','min_through_hole_diameter',
                                               'min_via_annular_width','min_clearance','min_hole_to_hole','min_copper_edge_clearance')}
    except Exception as e:
        res['rules'] = f'unreadable: {type(e).__name__}'
    pm = res['process_min']
    print(f"[5] 工艺极限: 最小线宽 {pm['min_track_width']}mm · 最小过孔 Ø{pm['min_via_diameter']}/钻 {pm['min_via_drill']}"
          f" ⇒ 孔环 {pm['min_via_annular']}mm · 最小孔钻 {pm['min_hole_drill']}mm（孔 {pm['n_holes']} 个）")
    print(f"    板规 {res['rules']}")
    if a.json: json.dump(res, open(a.json, 'w'), ensure_ascii=False, indent=1)
    return 0

if __name__ == '__main__':
    sys.exit(main())
