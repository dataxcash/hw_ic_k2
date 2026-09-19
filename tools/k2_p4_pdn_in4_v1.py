#!/usr/bin/env python3
"""K2 · P4 增量 12（L2 自裁，owner #14「PDN = 自裁勿停」）—— **电源面（In4）接入：F→In4 盘中孔**。

依据：SPEC `pd.power_plane_layer = In4.Cu`（分区：P3V3 东区 / P3V3_AUX_MCU_VDD 西区）·
`pd.decoupling = ... → via_to_plane`（`zone_defs.decoupling_via_to_plane.geometry_status = L3_CONSTRUCTION_DERIVED`
= 施工派生**未建**）· handoff §8-②「路径 = In4 电源面 F→In4 盘中孔/引线」。

方法（确定性，零搜索自由度）：
1. 目标 = SPEC 声明但**未接入平面**的电源岛（由 kicad-cli DRC 未连接项 + In4 点在多边形判定**机读**得到）。
2. 取 `F→In4` 盲孔（span 感知，T-10：**不触 In5/B.Cu** ⇒ 不与该两层 PCIe 走廊冲突）+ **盘中孔**（pad 中心；
   板上既有同类实践 = 增量 3 的 129 支 GND 盘中孔 F→In1）。
3. 逐孔用**全层 span 感知净距 oracle**（整数层号，T-18）复核：∈各 span 层外网铜 ≥ 视距、孔-孔 ≥0.25（无同网豁免）、
   禁布区、板边 0.3 —— 裕度 <0 则**不落孔**并登记。
4. 落板 + 区域填充（T-4）→ kicad-cli DRC 复跑。

CLI: k2_p4_pdn_in4_v1.py --in <board> --out <board> --ledger <json>
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, re, subprocess, sys, uuid

NS = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
VIA_BLOCK = ('\t(via blind\n\t\t(at {x} {y})\n\t\t(size 0.35)\n\t\t(drill 0.2)\n'
             '\t\t(layers "F.Cu" "In4.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')
# 目标：U6 的 P3V3 孤立球（DRC 未连接项机读：FF8 (104.17,55.69) / FJ6 (104.69,55.99)）
TARGETS = [("P3V3", 104.17, 55.69, "U6.FF8"), ("P3V3", 104.69, 55.99, "U6.FJ6")]
SPAN_LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"]
VR, HR = 0.175, 0.1


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def via_uuid(net, x, y):
    return str(uuid.uuid5(NS, 'k2p4pdn|via|%s|%s|%s' % (net, fmt(x), fmt(y))))


def make_ctx(src):
    import pcbnew
    here = os.path.dirname(os.path.abspath(__file__))

    def L(n, f):
        sp = importlib.util.spec_from_file_location(n, os.path.join(here, f))
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
    f3 = L('k2f3p', 'k2_p4_ls_xlayer_v1.py'); cv = L('k2cvp', 'k2_p4_converge_v1.py')
    b = pcbnew.LoadBoard(src)
    lid = {pcbnew.LayerName(i): i for i in range(pcbnew.PCB_LAYER_ID_COUNT)}
    return f3.Ctx(b), cv, lid


def via_margin(c, cv, lid, net, x, y, span_names):
    span = [lid[n] for n in span_names]
    rows = []
    for t in c.tracks:
        if t['layer'] not in span or t['net'] == net:
            continue
        # inc106(L2)：T-27 粗筛陷阱修正 —— 原按**段中点**剪枝，长走线（实测 DS320_STRAP_B_ADDR1_15-8
        #   In2 段 7.62mm，中点距孔 2.84mm > 2.6）被误跳过 ⇒ 漏判 −0.178 冲突。改用**段 bbox** 剪枝。
        if (min(t['x1'], t['x2']) - 2.6 > x or max(t['x1'], t['x2']) + 2.6 < x
                or min(t['y1'], t['y2']) - 2.6 > y or max(t['y1'], t['y2']) + 2.6 < y):
            continue
        d = cv.pt_seg_dist(x, y, t['x1'], t['y1'], t['x2'], t['y2']) - t['hw'] - VR - cv._req(net, t['net'])
        rows.append((d, 'trk/%s' % t['net']))
    for p in c.pads.values():
        if p['net'] == net or not any(Li in p['lay'] for Li in span):
            continue
        if abs(p['x'] - x) > 2.0 or abs(p['y'] - y) > 2.0:
            continue
        if p['circ']:
            d = cv.pt_seg_dist(p['x'], p['y'], x, y, x, y) - min(p['w'], p['h']) / 2 - VR - cv._req(net, p['net'])
        elif p['poly']:
            d = cv.pt_poly_dist(x, y, p['poly']) - VR - cv._req(net, p['net'])
        else:
            continue
        rows.append((d, 'pad/%s' % p['net']))
    for v in c.vias.values():
        if v['net'] == net or not any(Li in v['lay'] for Li in span):
            continue
        if abs(v['x'] - x) > 2.0 or abs(v['y'] - y) > 2.0:
            continue
        rows.append((math.hypot(x - v['x'], y - v['y']) - v['r'] - VR - cv._req(net, v['net']), 'via/%s' % v['net']))
    for (hx, hy, hr, hnet) in c.holes:
        if abs(hx - x) > 2.0 or abs(hy - y) > 2.0:
            continue
        rows.append((math.hypot(x - hx, y - hy) - HR - 0.25 - hr, 'hole/%s' % hnet))
    for i, poly in enumerate(c.keep_v):
        if cv.pt_in_poly(x, y, poly):
            rows.append((-1.0, 'keep_v#%d' % i))
    for poly in c.keep_t:
        if cv.pt_in_poly(x, y, poly):
            rows.append((-1.0, 'keep_t'))
    for e in c.edge:
        rows.append((cv.pt_seg_dist(x, y, *e) - VR - 0.3, 'edge'))
    rows.sort()
    return (rows[0] if rows else (9.0, 'none')), rows[:4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='src', required=True)
    ap.add_argument('--out', dest='out', required=True)
    ap.add_argument('--ledger', dest='ledger', required=True)
    a = ap.parse_args()
    c, cv, lid = make_ctx(a.src)
    import pcbnew
    _b = pcbnew.LoadBoard(a.src)
    existing = set()
    for t in _b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            pos = t.GetPosition()
            existing.add((t.GetNetname(), round(pcbnew.ToMM(pos.x), 3), round(pcbnew.ToMM(pos.y), 3)))
    placed, refused, skipped = [], [], []
    for net, x, y, ref in TARGETS:
        if (net, round(x, 3), round(y, 3)) in existing:
            skipped.append(dict(net=net, x=x, y=y, ref=ref, why='already-present'))
            continue
        (m, why), top = via_margin(c, cv, lid, net, x, y, SPAN_LAYERS)
        rec = dict(net=net, x=x, y=y, ref=ref, span="F.Cu..In4.Cu", margin=round(m, 4), blocker=why, top=top)
        (placed if m >= 0 else refused).append(rec)
    print('via-in-pad F→In4: placed=%d skipped=%d refused=%d' % (len(placed), len(skipped), len(refused)))
    for r in placed:
        print('  OK   %-8s (%.3f,%.3f) %s margin=%+.4f (worst=%s)' % (r['net'], r['x'], r['y'], r['ref'], r['margin'], r['blocker']))
    for r in refused:
        print('  REFU %-8s (%.3f,%.3f) %s margin=%+.4f (worst=%s)' % (r['net'], r['x'], r['y'], r['ref'], r['margin'], r['blocker']))
    txt = open(a.src, encoding='utf-8').read()
    blocks = ''.join(VIA_BLOCK.format(x=fmt(x), y=fmt(y), net=net, u=via_uuid(net, x, y))
                     for net, x, y, ref in [(r['net'], r['x'], r['y'], r['ref']) for r in placed])
    anchor = txt.index('\n\t(via\n') if '\n\t(via\n' in txt else txt.index('\t(segment\n')
    tmp = a.out + '.pdn_tmp.kicad_pcb'
    open(tmp, 'w', encoding='utf-8').write(txt[:anchor] + blocks + txt[anchor:])
    # ★ T-8/T-22：pcbnew 在**缺同名 pro** 时会回写**默认工程件**（曾把 18.8KB pro 换成 9.6KB 默认件 ⇒
    #   kicad-cli 回退默认规则 ⇒ 假象 1069 条）。故：先**备份** src pro 字节，tmp 必须配对同名 pro，
    #   落板后**无条件恢复** dst pro（含原地改板情形）。
    import shutil
    src_pro = re.sub(r'\.kicad_pcb$', '.kicad_pro', a.src)
    dst_pro = re.sub(r'\.kicad_pcb$', '.kicad_pro', a.out)
    pro_bytes = open(src_pro, 'rb').read()
    tmp_pro = re.sub(r'\.kicad_pcb$', '.kicad_pro', tmp)
    open(tmp_pro, 'wb').write(pro_bytes)
    r = subprocess.run([sys.executable, '-c',
                        "import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[2])",
                        tmp, a.out], capture_output=True, text=True)
    if r.returncode != 0:
        open(dst_pro, 'wb').write(pro_bytes)
        print('FILL FAIL', r.stderr[-500:]); return 2
    open(dst_pro, 'wb').write(pro_bytes)
    for f in (tmp, tmp_pro):
        if os.path.exists(f):
            os.remove(f)
    json.dump(dict(board_out=a.out, placed=placed, skipped=skipped, refused=refused),
              open(a.ledger, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('written', a.out)
    return 0 if not refused else 4


if __name__ == '__main__':
    sys.exit(main())
