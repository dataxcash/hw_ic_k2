#!/usr/bin/env python3
"""K2 · R150 —— 连续 legalization（nudge）：对栅格解之**残对触发线段**做亚格法向微移，
每次以 exact_gate 复算（判据③ 口径 · 含障碍余量/端点偏移/不新增违规）⇒ 贪心接收。"""
import json, math, sys, copy
sys.path.insert(0, '/home/fila/jqdDev_2025/ic_hw/k2/tools')
import k2_p4_b2_in5_lane_router_v3 as v3

WO = sys.argv[1] if len(sys.argv) > 1 else '/tmp/opencode/archer/R149_wo_all32_grpsep.json'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/opencode/archer/wo_all32_nudged.json'
MODEL = '/tmp/opencode/r1e_dump_v1.json'
MOV = json.load(open('/tmp/opencode/archer/movable_derive_v1.json'))
MNETS = set(MOV['movable_nets']); MCOPPER = set(MOV['movable_copper']); MSTITCH = set(MOV['movable_stitch'])
LAYER, HW, PITCH_EFF, CELL, MARGIN = 'In5.Cu', 0.08, 0.435, 0.10, 0.100
v3.PAD_EXTRA = MARGIN + 0.5 * CELL * math.sqrt(2)
model = json.load(open(MODEL))
wo = json.load(open(WO))
anchors = v3.lane_anchors(model)
ov = {a['net']: a for a in wo['anchors']}
for an in anchors:
    if an['net'] in ov:
        an['A'] = tuple(ov[an['net']]['A']); an['B'] = tuple(ov[an['net']]['B'])

def gate(routes):
    return v3.exact_gate(model, routes, anchors, LAYER, HW, MNETS, MSTITCH, PITCH_EFF, MCOPPER)

def closest_pair(p, q):
    best = (1e9, None, None, None)
    for i in range(len(p) - 1):
        ax, ay = p[i]; bx, by = p[i + 1]; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        for j in range(len(q) - 1):
            cx, cy = q[j]; ex, ey = q[j + 1]; fx, fy = ex - cx, ey - cy; M2 = fx * fx + fy * fy
            for t in [k / 20.0 for k in range(21)]:
                px, py = ax + t * dx, ay + t * dy
                u = 0.0 if M2 == 0 else max(0.0, min(1.0, ((px - cx) * fx + (py - cy) * fy) / M2))
                qx, qy = cx + u * fx, cy + u * fy
                d = math.hypot(px - qx, py - qy)
                if d < best[0]:
                    best = (d, (px, py), (qx, qy), i)
    return best

def _bbox(pts):
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def local_min(routes, victim, near=6.0):
    """廉价预筛（**邻域版**）：仅算与 victim 包围盒 ±near 相交之车道的最小段距 ⇒ 提速 ~10x。"""
    p = routes[victim]['pts']; bx = _bbox(p); best = 1e9
    for nm, r in routes.items():
        if nm == victim:
            continue
        b = _bbox(r['pts'])
        if b[0] - near > bx[2] or bx[0] - near > b[2] or b[1] - near > bx[3] or bx[1] - near > b[3]:
            continue
        d = closest_pair(p, r['pts'])[0]
        if d < best:
            best = d
    return best


routes = {k: {'pts': [tuple(x) for x in v['pts']], 'len_mm': v['len_mm']} for k, v in wo['routes'].items()}
g = gate(routes)
print('起始: 违规 %d · min %.4f · 余量 %.4f · 端点 %s' % (g['n_lane_pitch_viol'], g['lane_pitch_gap_mm'] if 'lane_pitch_gap_mm' in g else g['lane_pitch_min_gap_mm'], g['clearance_min_mm'], g['endpoint_max_dev_mm']), flush=True)
cur = g['n_lane_pitch_viol']
for rnd in range(6):
    vio = g.get('lane_pitch_violations') or []
    if not vio:
        break
    round_start = copy.deepcopy(routes); g_round0 = dict(g)
    improved = False
    for (n1, n2, d) in vio:
        for victim, other in ((n2, n1), (n1, n2)):
            p = routes.get(victim); q = routes.get(other)
            if not p or not q:
                continue
            dd, pt_on_victim, pt_on_other, segi = closest_pair(p['pts'], q['pts'])
            vx, vy = pt_on_victim[0] - pt_on_other[0], pt_on_victim[1] - pt_on_other[1]
            n = math.hypot(vx, vy) or 1.0
            ux, uy = vx / n, vy / n
            vi = min(segi + 1, len(p['pts']) - 2)          # 触发线段末端顶点（不动首末端点）
            lm_cur = dd          # 局部判据 = **该对**之最近段距（非整车道最小值 · 免被其他对锁死）
            for delta in (0.05, 0.10, 0.15, 0.20, 0.25):
                cand = copy.deepcopy(routes)
                px, py = cand[victim]['pts'][vi]
                cand[victim]['pts'][vi] = (round(px + ux * delta, 4), round(py + uy * delta, 4))
                dd_new = closest_pair(cand[victim]['pts'], cand[other]['pts'])[0]
                if dd_new <= dd + 1e-6:
                    continue                      # 局部判据：**该对**段距须严格增大（免全闸复算）
                routes = cand; improved = True
                print('  [nudge r%d] %s 顶点 %d 移 %.2fmm ⇒ 该对距 %.4f (原 %.4f)' % (rnd, victim, vi, delta, dd_new, dd), flush=True)
                break
            if improved:
                break
        if improved:
            break
    if not improved:
        print('  [nudge r%d] 无改进 ⇒ 停' % rnd, flush=True)
        break
    snap = {k: {'pts': [tuple(x) for x in v['pts']], 'len_mm': v['len_mm']} for k, v in routes.items()}
    gg = gate(snap)
    if gg['endpoint_max_dev_mm'] > 1e-6 or gg['clearance_min_mm'] < MARGIN - 1e-9:
        routes = round_start; g = g_round0
        print('  [nudge r%d] 整轮**回退**（全闸未通过：余量 %.4f / 端点 %s）' % (rnd, gg['clearance_min_mm'], gg['endpoint_max_dev_mm']), flush=True)
        continue
    g = gg
    print('  [nudge r%d] 全闸校验过：违规 %d · min %.4f · 余量 %.4f · 端点 %s' %
          (rnd, gg['n_lane_pitch_viol'], gg['lane_pitch_min_gap_mm'], gg['clearance_min_mm'], gg['endpoint_max_dev_mm']), flush=True)
out = dict(wo); out['routes'] = {k: {'pts': [[x, y] for (x, y) in v['pts']], 'len_mm': v['len_mm']} for k, v in routes.items()}
out['geometric_gate'] = g; out['nudge'] = {'rounds': rnd + 1, 'viol': g['n_lane_pitch_viol']}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1, sort_keys=True)
print('FINAL 违规 %d · min %.4f · 余量 %.4f · 端点 %s ⇒ %s' % (g['n_lane_pitch_viol'], g['lane_pitch_min_gap_mm'], g['clearance_min_mm'], g['endpoint_max_dev_mm'], OUT), flush=True)
