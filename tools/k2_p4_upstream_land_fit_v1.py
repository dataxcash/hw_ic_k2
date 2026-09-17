#!/usr/bin/env python3
"""K2 · P4 · 「按所命名上游封装复核实体占位」测量（只读，纯 stdlib）。

问的问题：板上的 29 件「上游库名件」用的是生成器**简化 land**；若按**所命名封装的真 land**（上游库）复核，
现有**放置**是否还成立？（本板已发现 U2/E2 的 SOIC-8 land 缩到 ±1.95，真 land 为 ±3.5875。）

方法（每件）：取上游 .kicad_mod 的 pad 外接框 / courtyard 外接框（局部坐标）→ 按板上该件的 (x,y,rot) 旋转平移 →
与**其余 58 件**的 pad 外接框、既有 courtyard 外接框比对 → 报 gap<0（重叠）。
输出：冲突清单（件对 + 重叠量 + 性质：courtyard↔courtyard / courtyard↔铜 / 铜↔铜）。

说明：外接框为**上界**（保守）；本项目 ForgeOS/裸名件无上游可比，不参与。
本件**只交测量**，不改板、不含裁定。

用法：python3 k2/tools/k2_p4_upstream_land_fit_v1.py [--json /tmp/out.json]
"""
import argparse, importlib.util, json, math, os, sys

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
HERE = os.path.dirname(os.path.abspath(__file__))
cc = _load('cc', os.path.join(HERE, 'k2_p4_courtyard_completion_v1.py'))
j8 = cc.j8
STD_ROOTS = ['AppDir/share/kicad/footprints']

def rot_box(b, deg, tx, ty):
    pts = [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]
    r = [j8.rot_pt(x, y, deg) for x, y in pts]
    xs = [tx + p[0] for p in r]; ys = [ty + p[1] for p in r]
    return (min(xs), min(ys), max(xs), max(ys))

def gap(a, b):
    return (max(a[0]-b[2], b[0]-a[2]), max(a[1]-b[3], b[1]-a[3]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', default='k2/hw/k2_v4_8L.l5.kicad_pcb')
    ap.add_argument('--std-roots', nargs='*', default=STD_ROOTS)
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    root = j8.parse(open(a.board, encoding='utf-8').read())
    rows = {}
    for fp in j8.all_(root, 'footprint'):
        pads, fab, crt, ref, at = cc.fp_boxes(fp)
        rows[ref] = dict(pad=j8.union(pads), crt=j8.union(crt), fab=j8.union(fab), at=at, link=str(j8.one(fp, 'footprint_at') or ''))
        # link 从节点第 2 项取
    # 重新取 link（fp[1]）
    for fp in j8.all_(root, 'footprint'):
        ref = None
        for p in j8.all_(fp, 'property'):
            if len(p) > 2 and p[1] == 'Reference': ref = p[2]
        if ref in rows: rows[ref]['link'] = fp[1]
    # 上游库解析
    libdirs = {}
    for nick in {r['link'].split(':')[0] for r in rows.values() if ':' in r['link'] and r['link'].split(':')[0]}:
        for rt in a.std_roots:
            d = os.path.join(rt, nick + '.pretty')
            if os.path.isdir(d): libdirs[nick] = d
    def pad_polys(node, fx, fy, fr):
        out = []
        for pad in j8.all_(node, 'pad'):
            pat = j8.nums(j8.one(pad, 'at') or ['at', 0, 0])
            sz = j8.nums(j8.one(pad, 'size') or ['size', 0, 0])
            pr = pat[2] if len(pat) > 2 else 0.0
            px, py = j8.rot_pt(pat[0], pat[1], fr)
            cx, cy = fx + px, fy + py
            deg = fr + pr
            # 角点须按凸多边形顺序（逆时针）：(-1,-1)→(1,-1)→(1,1)→(-1,1)，否则 SAT 边法线错误
            out.append([ (cx + rx, cy + ry) for rx, ry in
                         [j8.rot_pt(sx*sz[0]/2, sy*sz[1]/2, deg)
                          for sx, sy in ((-1,-1), (1,-1), (1,1), (-1,1))] ])
        return out

    def sat(a, b):
        for poly in (a, b):
            for i in range(len(poly)):
                x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
                nx, ny = -(y2-y1), (x2-x1)
                pa = [nx*x+ny*y for x, y in a]; pb = [nx*x+ny*y for x, y in b]
                if max(pa) <= min(pb) or max(pb) <= min(pa): return False
        return True

    board_pads = {}
    for ref, r in rows.items():
        fx, fy, fr = r['at']
        node = next(fp for fp in j8.all_(root, 'footprint')
                    if any(len(p) > 2 and p[1] == 'Reference' and p[2] == ref for p in j8.all_(fp, 'property')))
        board_pads[ref] = pad_polys(node, fx, fy, fr)

    res, copper, boxconf = {}, [], []
    for ref, r in rows.items():
        nick, _, name = r['link'].partition(':')
        if not nick or nick == 'ForgeOS':
            continue
        d = libdirs.get(nick)
        if not d: continue
        p = os.path.join(d, name + '.kicad_mod')
        if not os.path.exists(p): continue
        up = j8.parse(open(p, encoding='utf-8').read())
        padsl, _, crtl, _, _ = cc.fp_boxes(up)
        padb, crtb = j8.union(padsl), j8.union(crtl)
        if not padb: continue
        fx, fy, frot = r['at']
        new_pad = rot_box(padb, frot, fx, fy)
        new_crt = rot_box(crtb, frot, fx, fy) if crtb else None
        res[ref] = dict(up_pad_local=tuple(round(v, 3) for v in padb),
                        placed_pad=tuple(round(v, 3) for v in new_pad),
                        placed_crt=None if not new_crt else tuple(round(v, 3) for v in new_crt),
                        cur_pad=None if not r['pad'] else tuple(round(v, 3) for v in r['pad']))
        # ① 精确铜↔铜（逐 pad、SAT）
        up_pads = pad_polys(up, fx, fy, frot)
        for other in rows:
            if other == ref: continue
            n = 0
            for up_poly in up_pads:
                for cur_poly in board_pads[other]:
                    if sat(up_poly, cur_poly): n += 1
            if n: copper.append((ref, other, n, 'upstream铜↔现铜(逐pad精确)'))
        # ② 外接框上界（本体/图形/courtyard）
        for other, o in rows.items():
            if other == ref: continue
            if new_crt and o['crt']:
                g = gap(new_crt, o['crt'])
                if g[0] < 0 and g[1] < 0: boxconf.append((ref, other, round(g[0], 3), round(g[1], 3), '真 courtyard框↔现 courtyard框(上界)'))
            if new_crt and o['pad']:
                g = gap(new_crt, o['pad'])
                if g[0] < 0 and g[1] < 0: boxconf.append((ref, other, round(g[0], 3), round(g[1], 3), '真 courtyard框↔现铜框(上界)'))
            if o['pad']:
                g = gap(new_pad, o['pad'])
                if g[0] < 0 and g[1] < 0: boxconf.append((ref, other, round(g[0], 3), round(g[1], 3), '真 land外接框↔现铜框(上界)'))
    conflicts = copper + boxconf
    print(f"[1] 参与复核（上游库名可解析）件数 = {len(res)}")
    for ref in sorted(res):
        d = res[ref]
        grew = ''
        if d['cur_pad']:
            dx = round((d['placed_pad'][2]-d['placed_pad'][0]) - (d['cur_pad'][2]-d['cur_pad'][0]), 2)
            dy = round((d['placed_pad'][3]-d['placed_pad'][1]) - (d['cur_pad'][3]-d['cur_pad'][1]), 2)
            grew = f" | 现铜框 {d['cur_pad']} → 真 land 框 {d['placed_pad']}（Δ {dx}×{dy}mm）"
        print(f"  {ref:5s} {d['up_pad_local']} -> {d['placed_pad']}{grew}")
    print(f"\n[2] **精确铜↔铜冲突**（逐 pad SAT，硬证据）: {len(copper)} 条")
    for c in sorted(copper): print(f"    {c[0]:5s} ↔ {c[1]:5s}  重合 pad 对 = {c[2]:3d}  [{c[3]}]")
    print(f"\n[3] 外接框上界候选（真 land/courtyard 外接框 vs 现铜/courtyard 外接框；**上界，非精确**）: {len(boxconf)} 条")
    for c in sorted(boxconf)[:20]: print(f"    {c[0]:5s} ↔ {c[1]:5s}  dx={c[2]:7.2f} dy={c[3]:7.2f}  [{c[4]}]")
    if len(boxconf) > 20: print(f"    ... 共 {len(boxconf)} 条（全量见 --json）")
    if a.json: json.dump(dict(placed=res, conflicts=conflicts), open(a.json, 'w'), ensure_ascii=False, indent=1)
    return 0

if __name__ == '__main__':
    sys.exit(main())
