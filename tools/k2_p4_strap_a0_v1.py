#!/usr/bin/env python3
"""K2 · P4 —— **strap `DS320_STRAP_A_ADDR0_15-8` 接线（L2 走廊/placement，自裁域）**。

依据：监理 **#K2-20 §三**（`DS320_STRAP_A_ADDR0_15-8` = **L2 走廊重解域**，归 ENG）·
owner **#14**（L2 = 走廊/placement 自裁勿停）· handoff `ctx425k-inc17` §4-1/§7-1。

根因（本执行器落板前的实测，见 ledger）：
  `R42.1`(85.775,59.55) 的 F.Cu 可达域 = **封闭口袋** x[85.0,86.75]·y[59.15,60.15]
  （北 = `DS320_STRAP_A_ADDR1_15-8` 的 y=58.8 干线；南 = `P3V3` 的 y=60.55 干线；
   东 = R42.2 盘；西 = R43.2 盘+R43.1）⇒ 0.01mm 全域扫描 **0 个合法孔位**（任一 span 类）。
  ⇒ 按 handoff §4-1 **搬 R42（placement，L2）**，落入 SPEC `layer_plan.strap_domain_v32.placement.zone_mm`
  （x[83,104]·y[58.5,66]）内的空槽 **(93.3,61.55)**（row2，R45 正下方；避开 `decap_column_keepout_mm`
  x[90.25,91.75]，院界 91.775 > 91.75）。位移 6.99mm。**不改 L1**（器件集合/网络/球映射/信号流向不变）。

接线（全部**纯增铜**，0/45/90，单腿 ≥0.05；0.2mm 宽 = 板内 strap 既有宽度）：
  F.Cu  (92.4750,61.5500)->(93.2750,60.7500)   [45]      R42.1 -> 南干线上方走廊
  F.Cu  (93.2750,60.7500)->(100.0750,60.7500)  [0]
  In2.Cu(100.0750,60.7500)->(104.1704,56.6546) [45]
  In2.Cu(104.1704,56.6546)->(104.1704,56.2900) [90]
  via blind (100.0750,60.7500) F.Cu..In2.Cu   0.35/0.2  (strap)
  via blind (104.1704,56.2900) In2.Cu..F.Cu   0.35/0.2  (= U6.FF5 盘中孔)
  R42 原 GND 盘中孔 (87.5468,59.3913) F.Cu..In1.Cu **随搬** -> (94.0250,61.5500)（新 R42.2 盘中心；
  保持孔数不变、避免悬空孔）。

孔类 = 板内既有唯一类 **0.35/0.2**（SPEC `vias`：激光微孔类 0.10/0.25 因触 DRC 下限**已弃用**）。

T-22：src pro 字节备份 + out 目录配对同名 pro，落板后**双向**校验 pro 逐字节不变。
T-25：搬件/搬孔后必 ZONE_FILLER 重填。

CLI: k2_p4_strap_a0_v1.py --in <board> --out <board> --pro <pro> --ledger <json>
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, uuid

NS = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
NET = 'DS320_STRAP_A_ADDR0_15-8'
NEW_R42 = (93.3, 61.55)
OLD_VIA = (87.5468, 59.3913)
NEW_VIA_GND = (94.0250, 61.5500)
TRACKS = [('F.Cu', (92.4750, 61.5500), (93.2750, 60.7500)),
          ('F.Cu', (93.2750, 60.7500), (100.0750, 60.7500)),
          ('In2.Cu', (100.0750, 60.7500), (104.1704, 56.6546)),
          ('In2.Cu', (104.1704, 56.6546), (104.1704, 56.2900))]
VIAS = [(100.0750, 60.7500, 'F.Cu', 'In2.Cu', NET),
        (104.1704, 56.2900, 'In2.Cu', 'F.Cu', NET)]
W = 0.2


def fmt(v):
    s = '%.4f' % float(v)
    s = s.rstrip('0').rstrip('.')
    return s if s else '0'


def uid(kind, *parts):
    return str(uuid.uuid5(NS, 'k2p4strapa0|%s|%s' % (kind, '|'.join(fmt(p) if isinstance(p, float) else str(p) for p in parts))))


def seg_block(layer, a, b):
    return ('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n'
            '\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
            % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), fmt(W), layer, NET,
               uid('seg', layer, a[0], a[1], b[0], b[1])))


def via_block(x, y, top, bot, net):
    kind = 'blind' if (top, bot) not in (('F.Cu', 'B.Cu'), ('B.Cu', 'F.Cu')) else ''
    head = '\t(via blind\n' if kind == 'blind' else '\t(via\n'
    return (head + '\t\t(at %s %s)\n\t\t(size 0.35)\n\t\t(drill 0.2)\n\t\t(layers "%s" "%s")\n'
            '\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n' % (fmt(x), fmt(y), top, bot, net, uid('via', top, bot, x, y)))


VIA_RE = re.compile(r'\t\(via(?: blind)?\n(?:.*?\n)*?\t\)\n')


def via_at(t, x, y):
    """True if a via already exists at (x,y) — layer order on disk is normalized by pcbnew."""
    pat = '\t\t(at %s %s)\n' % (fmt(x), fmt(y))
    return any(pat in m.group(0) for m in VIA_RE.finditer(t))


def seg_at(t, layer, a, b):
    pat = ('\t\t(start %s %s)\n\t\t(end %s %s)\n' % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1])))
    for m in re.finditer(r'\t\(segment\n(?:.*?\n)*?\t\)\n', t):
        blk = m.group(0)
        if ('(layer "%s")' % layer) in blk and pat in blk:
            return True
    return False


def sha16(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='src', required=True)
    ap.add_argument('--out', dest='dst', required=True)
    ap.add_argument('--pro', required=True)
    ap.add_argument('--ledger', required=True)
    ap.add_argument('--pcbnew-python', default='AppDir/usr/bin/python3.11')
    a = ap.parse_args()
    t = open(a.src, encoding='utf-8').read()
    led = {'executor': 'k2_p4_strap_a0_v1', 'src': a.src, 'src_sha16': sha16(a.src),
           'pro': a.pro, 'pro_sha16_before': sha16(a.pro), 'actions': []}
    # --- 1) R42 footprint move (absolute, idempotent)
    i = t.index('(property "Reference" "R42"')
    s = t.rindex('\n\t(footprint ', 0, i)
    e = t.index('\n\t)\n', s) + len('\n\t)\n')
    blk = t[s:e]
    old_at = '\t\t(at %s %s)\n' % (fmt(86.6), fmt(59.55))
    new_at = '\t\t(at %s %s)\n' % (fmt(NEW_R42[0]), fmt(NEW_R42[1]))
    if '\t\t(at 93.3 61.55)\n' in blk:
        led['actions'].append('R42 move: already applied')
    elif old_at in blk:
        t = t[:s] + blk.replace(old_at, new_at, 1) + t[e:]
        led['actions'].append('R42 (86.6,59.55) -> (93.3,61.55)')
    else:
        raise SystemExit('R42 footprint at-line not found')
    # --- 2) relocate the old GND via-in-pad (keeps via count, avoids dangling via)
    ov = '\t\t(at %s %s)\n' % (fmt(OLD_VIA[0]), fmt(OLD_VIA[1]))
    nv = '\t\t(at %s %s)\n' % (fmt(NEW_VIA_GND[0]), fmt(NEW_VIA_GND[1]))
    if ov in t:
        # only inside the via block that also carries F.Cu/In1.Cu + GND
        k = t.index(ov)
        v0 = t.rindex('\n\t(via blind\n', 0, k)
        v1 = t.index('\n\t)\n', k) + len('\n\t)\n')
        vb = t[v0:v1]
        assert '(net "GND")' in vb and '"In1.Cu"' in vb, 'unexpected via block'
        t = t[:v0] + vb.replace(ov, nv, 1) + t[v1:]
        led['actions'].append('GND via-in-pad (87.5468,59.3913) -> (94.025,61.55)')
    else:
        led['actions'].append('GND via move: already applied')
    # --- 3) add tracks + vias (pure add, idempotent)
    add = ''
    for layer, p, q in TRACKS:
        b = seg_block(layer, p, q)
        if seg_at(t, layer, p, q):
            led['actions'].append('segment already present %s %s' % (layer, p))
        else:
            add += b
            led['actions'].append('ADD segment %s (%s,%s)->(%s,%s)' % (layer, p[0], p[1], q[0], q[1]))
    for x, y, top, bot, net in VIAS:
        b = via_block(x, y, top, bot, net)
        if via_at(t, x, y):
            led['actions'].append('via already present (%s,%s)' % (x, y))
        else:
            add += b
            led['actions'].append('ADD via blind (%s,%s) %s..%s' % (x, y, top, bot))
    anchor = '\n\t(embedded_fonts no)\n)'
    assert anchor in t, 'top-level anchor not found'
    t = t.replace(anchor, '\n' + add.rstrip('\n') + anchor, 1)
    # --- 4) write to out dir with paired same-name .pro (T-22)
    os.makedirs(os.path.dirname(os.path.abspath(a.dst)), exist_ok=True)
    pro_dst = os.path.join(os.path.dirname(os.path.abspath(a.dst)),
                           os.path.splitext(os.path.basename(a.dst))[0] + '.kicad_pro')
    shutil.copyfile(a.pro, pro_dst)
    with open(a.dst, 'w', encoding='utf-8') as f:
        f.write(t)
    # --- 5) ZONE_FILLER refill (T-25)
    code = ("import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);pcbnew.ZONE_FILLER(b).Fill(b.Zones());"
            "b.Save(sys.argv[2])")
    r = subprocess.run([a.pcbnew_python, '-c', code, a.dst, a.dst], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr, file=sys.stderr)
        raise SystemExit('zone fill failed')
    # --- 6) T-22 double-check: pro bytes unchanged (src + paired out)
    led['pro_sha16_after'] = sha16(a.pro)
    led['out_pro_sha16'] = sha16(pro_dst)
    led['pro_unchanged'] = (led['pro_sha16_before'] == led['pro_sha16_after'] == led['out_pro_sha16'])
    led['out'] = a.dst
    led['out_sha16'] = sha16(a.dst)
    os.makedirs(os.path.dirname(os.path.abspath(a.ledger)), exist_ok=True)
    with open(a.ledger, 'w', encoding='utf-8') as f:
        json.dump(led, f, ensure_ascii=False, indent=1)
    print(json.dumps(led, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
