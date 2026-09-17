#!/usr/bin/env python3
"""K2 · P4 · courtyard 补全可行性测量（只读，纯 stdlib；W-7 `missing_courtyard` 40 件 + J-8b 联动）。

问的问题：给 40 件无 courtyard 的封装补 courtyard，会遇到什么？
  - 候选 courtyard = ∪(pad 外接框, Fab 层图形外接框) + margin（KLC nominal 0.25mm；另报 0.10/0.50 敏感性）
  - 与**全板 59 件**（19 件既有 courtyard 用其真实图形外接框）做两两碰撞检查
  - 输出：可安全补件数 / 会触发 DRC `courtyards_overlap`（severity=error）的件与对（附重叠量）

结论用途：W-7「missing_courtyard 修 or 具名豁免」+ J-8b「器件重叠」口径（补 courtyard 后 DRC 才可判重叠）。
本件**只交测量**，不含裁定；不改板。

用法：python3 k2/tools/k2_p4_courtyard_completion_v1.py [--margins 0.10,0.25,0.50] [--json /tmp/out.json]
"""
import argparse, importlib.util, json, os, sys

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

j8 = _load('j8', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'k2_p4_j8_measure_v1.py'))

def fp_boxes(fp):
    """返回 (pad_boxes, fab_boxes, courtyard_boxes, ref, at)"""
    at = j8.nums(j8.one(fp, 'at') or ['at', 0, 0]); fx, fy = (at + [0, 0])[:2]; frot = at[2] if len(at) > 2 else 0.0
    ref = None
    for p in j8.all_(fp, 'property'):
        if len(p) > 2 and p[1] == 'Reference': ref = p[2]
    pads, fab, crt = [], [], []
    for pad in j8.all_(fp, 'pad'):
        pat = j8.nums(j8.one(pad, 'at') or ['at', 0, 0]); psz = j8.nums(j8.one(pad, 'size') or ['size', 0, 0])
        prot = pat[2] if len(pat) > 2 else 0.0
        px, py = j8.rot_pt(pat[0], pat[1], frot)
        pads.append(j8.rect_aabb(fx + px, fy + py, psz[0], psz[1], frot + prot))
    for g in j8.all_(fp, 'fp_line') + j8.all_(fp, 'fp_rect') + j8.all_(fp, 'fp_circle') + j8.all_(fp, 'fp_arc') + j8.all_(fp, 'fp_poly'):
        layers = str(j8.one(g, 'layer') or j8.one(g, 'layers') or '')
        b = None
        if g[0] == 'fp_line':
            a = j8.one(g, 'start'); c = j8.one(g, 'end')
            pa = j8.rot_pt(float(a[1]), float(a[2]), frot); pc = j8.rot_pt(float(c[1]), float(c[2]), frot)
            b = (min(fx+pa[0], fx+pc[0]), min(fy+pa[1], fy+pc[1]), max(fx+pa[0], fx+pc[0]), max(fy+pa[1], fy+pc[1]))
        elif g[0] == 'fp_rect':
            a = j8.one(g, 'start'); c = j8.one(g, 'end')
            pa = j8.rot_pt(float(a[1]), float(a[2]), frot); pc = j8.rot_pt(float(c[1]), float(c[2]), frot)
            b = (min(fx+pa[0], fx+pc[0]), min(fy+pa[1], fy+pc[1]), max(fx+pa[0], fx+pc[0]), max(fy+pa[1], fy+pc[1]))
        elif g[0] == 'fp_circle':
            c = j8.one(g, 'center'); e = j8.one(g, 'end')
            pc = j8.rot_pt(float(c[1]), float(c[2]), frot); pe = j8.rot_pt(float(e[1]), float(e[2]), frot)
            b = j8.circle_aabb(fx+pc[0], fy+pc[1], ((pe[0]-pc[0])**2 + (pe[1]-pc[1])**2) ** .5)
        if b:
            if 'CrtYd' in layers or 'Courtyard' in layers: crt.append(b)
            elif 'Fab' in layers: fab.append(b)
    return pads, fab, crt, ref, (fx, fy, frot)

def grow(b, m):
    return (b[0]-m, b[1]-m, b[2]+m, b[3]+m)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', default='k2/hw/k2_v4_8L.l5.kicad_pcb')
    ap.add_argument('--margins', default='0.10,0.25,0.50')
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    root = j8.parse(open(a.board, encoding='utf-8').read())
    rows = []
    for fp in j8.all_(root, 'footprint'):
        pads, fab, crt, ref, at = fp_boxes(fp)
        rows.append(dict(ref=ref, at=at, npad=len(pads), pad_union=j8.union(pads), fab_union=j8.union(fab),
                         courtyard_union=j8.union(crt), n_courtyard_items=len(crt)))
    have = [r for r in rows if r['courtyard_union']]
    lack = [r for r in rows if not r['courtyard_union']]
    res = dict(n_total=len(rows), n_with=len(have), n_without=len(lack), without=sorted(r['ref'] for r in lack), by_margin={})
    print(f"[0] courtyard 覆盖：有 {len(have)} / 无 {len(lack)}（共 {len(rows)}）")
    print(f"    无 courtyard：{sorted(r['ref'] for r in lack)}")
    for ms in a.margins.split(','):
        m = float(ms)
        # 候选：有者用真实 courtyard；无者用 ∪(pad, fab) + margin
        eff = []
        for r in rows:
            base = r['courtyard_union'] if r['courtyard_union'] else j8.union([b for b in (r['pad_union'], r['fab_union']) if b])
            if base is None: continue
            eff.append((r['ref'], grow(base, m) if not r['courtyard_union'] else base, bool(r['courtyard_union'])))
        coll = []
        for i in range(len(eff)):
            for j in range(i+1, len(eff)):
                ov = j8.inter(eff[i][1], eff[j][1])
                if ov: coll.append((eff[i][0], eff[j][0], round(ov[0], 3), round(ov[1], 3),
                                    'both-existing' if (eff[i][2] and eff[j][2]) else ('new-vs-new' if not (eff[i][2] or eff[j][2]) else 'new-vs-existing')))
        bad = sorted({x for c in coll for x in c[:2]})
        res['by_margin'][ms] = dict(n_collisions=len(coll), n_refs_involved=len(bad), refs=bad, pairs=coll)
        print(f"[1] margin {m}mm：courtyard 碰撞 {len(coll)} 对 / 涉 {len(bad)} 件 —— 涉件 {bad}")
        for c in coll[:10]: print(f"      {c[0]} ↔ {c[1]}  dx={c[2]} dy={c[3]}  [{c[4]}]")
    if a.json: json.dump(res, open(a.json, 'w'), ensure_ascii=False, indent=1)
    return 0

if __name__ == '__main__':
    sys.exit(main())
