#!/usr/bin/env python3
# U4-D/G-1 试点（增量 10）：按计划 JSON **落板**（逐段精确删除被替换段 + 新段 uuid5 + 区域填充子进程）。

"""U4-D 试点：把重派生几何落为板（只写 /tmp），并复跑 DRC。
用法：u4d_emit.py <src.kicad_pcb> <plan.json> <out.kicad_pcb>
"""
import importlib.util, json, math, os, re, shutil, subprocess, sys, uuid
sys.path.insert(0, '/home/fila/jqdDev_2025/ic_hw/k2/tools')
def Lp(n, f):
    sp = importlib.util.spec_from_file_location(n, '/home/fila/jqdDev_2025/ic_hw/k2/tools/' + f)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
f1 = Lp('f1', 'k2_p4_ls_local_v1.py')
SRC, PLAN, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
plan = json.load(open(PLAN, encoding='utf-8'))
txt = open(SRC, encoding='utf-8').read()
NS = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
def su(net, layer, x1, y1, x2, y2):
    return str(uuid.uuid5(NS, 'k2u4d|seg|%s|%s|%s|%s|%s|%s' % (net, layer, f1._fmt(x1), f1._fmt(y1), f1._fmt(x2), f1._fmt(y2))))
new_blocks, n_old, n_new = [], 0, 0
for net, d in plan.items():
    if not net.startswith('PCIE_'): continue
    legs, lays = [], []
    for c in d['chains']:
        if 'legs' not in c:
            print('!! %s 链未解（%s），跳过整网' % (net, c['chain'])); legs = []; break
        lay = c['layer']
        for s in c['legs']:
            if math.hypot(s[2]-s[0], s[3]-s[1]) < 1e-9: continue
            legs.append((lay, s)); lays.append(lay)
    if not legs: continue
    # 只删除**被计划链覆盖**的旧 segment（其余原样保留）
    rules = []            # (bbox, explicit_ov)
    for c in d['chains']:
        p_, q_ = c['p'], c['q']
        ov = c.get('ov')
        rules.append(((min(p_[0], q_[0]), min(p_[1], q_[1]), max(p_[0], q_[0]), max(p_[1], q_[1])), ov))
    def perp(x, y, p_, q_):
        dx, dy = q_[0] - p_[0], q_[1] - p_[1]
        L = math.hypot(dx, dy)
        return abs((x - p_[0]) * dy - (y - p_[1]) * dx) / L if L > 1e-9 else math.hypot(x - p_[0], y - p_[1])

    def covered(s):
        x1, y1, x2, y2 = s
        for (bb, ov) in rules:
            p_ = (bb[0], bb[1]) if False else None
            if ov:
                if (abs(x1-ov[0]) < 1e-6 and abs(y1-ov[1]) < 1e-6 and abs(x2-ov[2]) < 1e-6 and abs(y2-ov[3]) < 1e-6) or \
                   (abs(x2-ov[0]) < 1e-6 and abs(y2-ov[1]) < 1e-6 and abs(x1-ov[2]) < 1e-6 and abs(y1-ov[3]) < 1e-6):
                    return True
            else:
                if (min(x1, x2), min(y1, y2)) >= (bb[0] - 1e-6, bb[1] - 1e-6) and (max(x1, x2), max(y1, y2)) <= (bb[2] + 1e-6, bb[3] + 1e-6):
                    # 追加「走廊带」约束：段两端到链轴线（对角线 bbox 的近水平近似）的垂距 ≤ 3mm
                    p_ = (bb[0], min(bb[1], bb[3])); q_ = (bb[2], bb[1] if bb[1] == bb[3] else bb[3])
                    if perp(x1, y1, p_, q_) <= 3.0 and perp(x2, y2, p_, q_) <= 3.0:
                        return True
        return False
    out, i = [], 0
    for m in re.finditer(r'\t\(segment\n(.*?)\n\t\)\n', txt, re.S):
        blk = m.group(1)
        if not re.search(r'\(net "%s"\)' % re.escape(net), blk): continue
        st = re.search(r'\(start (-?[0-9.]+) (-?[0-9.]+)\)', blk); en = re.search(r'\(end (-?[0-9.]+) (-?[0-9.]+)\)', blk)
        if st and en and covered(tuple(map(float, (st.group(1), st.group(2), en.group(1), en.group(2))))):
            out.append(txt[i:m.start()]); i = m.end(); n_old += 1
    out.append(txt[i:]); txt = ''.join(out)
    for lay, s in legs:
        u = su(net, lay, s[0], s[1], s[2], s[3])
        new_blocks.append(f1.SEG_BLOCK.format(x1=f1._fmt(s[0]), y1=f1._fmt(s[1]), x2=f1._fmt(s[2]), y2=f1._fmt(s[3]),
                                              layer=lay, net=net, u=u))
        n_new += 1
print('replaced %d 旧段 → %d 新段' % (n_old, n_new))
anchor = txt.index('\t(segment\n')
tmp = OUT + '.u4d_tmp.kicad_pcb'
open(tmp, 'w', encoding='utf-8').write(txt[:anchor] + ''.join(new_blocks) + txt[anchor:])
src_pro = re.sub(r'\.kicad_pcb$', '.kicad_pro', SRC)
shutil.copyfile(src_pro, re.sub(r'\.kicad_pcb$', '.kicad_pro', tmp))
r = subprocess.run([sys.executable, '-c',
    "import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[2])", tmp, OUT],
    capture_output=True, text=True)
if r.returncode != 0:
    print('FILL FAIL', r.stderr[-400:]); sys.exit(2)
shutil.copyfile(src_pro, re.sub(r'\.kicad_pcb$', '.kicad_pro', OUT))
os.remove(tmp)
print('written', OUT)
