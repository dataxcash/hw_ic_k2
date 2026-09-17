#!/usr/bin/env python3
"""H3 最小位移扫描（只读）—— K2-P4-H3-MECHANICAL-INPUT-GAP-v1.md §4 的实现。

对候选孔心 (x,y) 与 keepout 半径 r 判定（模型边界见文档 §4）：
  1) 孔边(1.6) 到板边 ≥1.5（边料）· 2) Ø3.2 孔对 pad 铜 ≥0.25（保守=pad 外接半对角）
  3) 孔-孔 ≥0.25（对 4 个 NPTH 与所有带孔 pad）· 4) keepout 圆内无任何层 track、无 via
  （copperpour 由 KiCad 自动避让，不计：现板 4 区即如此且无 items_not_allowed）
输出：每个 r 在 x∈[24.6,30.0] / y∈[36.1,76.0] 内的最近可行 y 与最小位移。
用法： python3 h3_scan.py [board.kicad_pcb]
"""
import re, math, sys

BOARD = sys.argv[1] if len(sys.argv) > 1 else 'k2/hw/k2_v4_8L.l5.kicad_pcb'
t = open(BOARD, encoding='utf-8').read()


def be(s, i):
    d = 0; ins = False; esc = False
    while i < len(s):
        c = s[i]
        if ins:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': ins = False
        else:
            if c == '"': ins = True
            elif c == '(': d += 1
            elif c == ')':
                d -= 1
                if d == 0: return i + 1
        i += 1
    raise ValueError('unbalanced')


segs = []
for m in re.finditer(r'\n\t\(segment\n', t):
    s = m.start() + 1; e = t.find('\n\t)\n', s); b = t[s:e + 4]
    st = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)', b); en = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', b)
    segs.append(tuple(map(float, st.groups() + en.groups())))

vias = []
for m in re.finditer(r'\n\t\(via( blind)?\n', t):
    s = m.start() + 1; e = t.find('\n\t)\n', s); b = t[s:e + 4]
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', b); sz = re.search(r'\(size ([-\d.]+) ([-\d.]+)\)', b)
    vias.append((float(at.group(1)), float(at.group(2)), float(sz.group(1)) / 2 if sz else 0.35))

pads = []
for m in re.finditer(r'\n\t\(footprint ', t):
    z = m.start() + 1; ze = be(t, z); blk = t[z:ze]
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)', blk)
    if not at: continue
    fx, fy = float(at.group(1)), float(at.group(2))
    for pm in re.finditer(r'\n\t\t\(pad ', blk):
        ps = pm.start() + 1; pe = be(blk, ps); pb = blk[ps:pe]
        pat = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', pb)
        psz = re.search(r'\(size ([-\d.]+) ([-\d.]+)\)', pb)
        dr = re.search(r'\(drill ([-\d.]+)\)', pb)
        if not pat: continue
        pads.append((fx + float(pat.group(1)), fy + float(pat.group(2)),
                     float(psz.group(1)) / 2 if psz else 0.3,
                     float(psz.group(2)) / 2 if psz else 0.3,
                     float(dr.group(1)) / 2 if dr else 0.0))

X0, X1, Y0, Y1 = 24.6, 30.0, 36.1, 76.0
segs2 = [s for s in segs if min(s[0], s[2]) < X1 + 3.2 and max(s[0], s[2]) > X0 - 3.2
         and min(s[1], s[3]) < Y1 + 3.2 and max(s[1], s[3]) > Y0 - 3.2]
vias2 = [v for v in vias if X0 - 3.2 < v[0] < X1 + 3.2 and Y0 - 3.2 < v[1] < Y1 + 3.2]
pads2 = [p for p in pads if X0 - 4 < p[0] < X1 + 4 and Y0 - 4 < p[1] < Y1 + 4]
holes2 = [p for p in pads if p[4] > 0]


def dseg(px, py, s):
    x1, y1, x2, y2 = s; dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    tt = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + tt * dx), py - (y1 + tt * dy))


def ok(x, y, r):
    if not (x - 23 >= 3.1 and 143 - x >= 3.1 and y - 33 >= 3.1 and 79 - y >= 3.1): return False
    for px, py, w, h, dr in pads:
        if dr > 0: continue
        if math.hypot(px - x, py - y) < math.hypot(w, h) + 0.25 + 1.6: return False
    for px, py, w, h, dr in holes2:
        if math.hypot(px - x, py - y) < 1.6 + dr + 0.25: return False
    for s in segs2:
        if dseg(x, y, s) < r: return False
    for vx, vy, vr in vias2:
        if math.hypot(vx - x, vy - y) < r + vr: return False
    return True


print(f'域: x[{X0},{X1}] y[{Y0},{Y1}]  参考孔 H3=(26.1,36.1)')
for r in (3.0, 2.5, 2.0, 1.6):
    ys = []
    y = Y0
    while y <= Y1 + 1e-6:
        x = X0
        while x <= X1 + 1e-6:
            if ok(round(x, 2), round(y, 2), r):
                ys.append(y); break
            x += 0.1
        y += 0.1
    if ys:
        print(f'  r={r}  (Ø{r*2:.1f})  最近可行 y={min(ys):.1f}  最小位移={min(ys)-36.1:.1f}mm')
    else:
        print(f'  r={r}  (Ø{r*2:.1f})  该 x 带内无可行位')
