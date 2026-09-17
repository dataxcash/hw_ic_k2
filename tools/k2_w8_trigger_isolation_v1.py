#!/usr/bin/env python3
"""K2 · W-8/J-7 · FootprintNeedsUpdate 触发字段隔离 + DRC 闭合实测（只读探针）。

用途：为监理 #K2-20 §二 / handoff §4-2 的 (甲′)/(乙) 重裁提供实测证据。
- 判定口径 = KiCad 自身 `pcbnew.FOOTPRINT.FootprintNeedsUpdate(lib_fp)`（DRC
  `lib_footprint_mismatch` 即此判定），并以 kicad-cli DRC 作地面真值交叉验证。
- 只读：不写仓库任何文件；所有中间件写入 --out-root（默认 /tmp/opencode/w8iso）。

运行（容器根目录）：
  AppDir/usr/bin/python3.11 k2/tools/k2_w8_trigger_isolation_v1.py trigger-matrix --ref U4
  AppDir/usr/bin/python3.11 k2/tools/k2_w8_trigger_isolation_v1.py drc-probe
"""
import argparse, collections, json, os, re, shutil, subprocess, sys

BOARD    = 'k2/hw/k2_v4_8L.l5.kicad_pcb'
PRO      = 'k2/hw/k2_v4_8L.l5.kicad_pro'
CLI      = 'AppDir/bin/kicad-cli'
STD_ROOTS= ['AppDir/share/kicad/footprints']
PROJ_LIB = 'k2/hw/lib'
DEF_OUT  = '/tmp/opencode/w8iso'

# ---------------------------------------------------------------- helpers
def nick_name(fp):
    fid = fp.GetFPID()
    return (str(fid.GetLibNickname()), str(fid.GetLibItemName()))

def read(path):
    return open(path, encoding='utf-8').read()

def spans(txt):
    """[(ref, start, end, block_text)] for every top-level (footprint ...) node."""
    lines = txt.splitlines(keepends=True)
    off = [0]
    for l in lines:
        off.append(off[-1] + len(l))
    out, i, n = [], 0, len(lines)
    while i < n:
        if lines[i].startswith('\t(footprint '):
            d = 0
            for j in range(i, n):
                d += lines[j].count('(') - lines[j].count(')')
                if d == 0:
                    break
            blk = ''.join(lines[i:j + 1])
            m = re.search(r'\(property "Reference" "([^"]+)"', blk)
            out.append((m.group(1) if m else None, off[i], off[j + 1], blk))
            i = j + 1
        else:
            i += 1
    return out

def edit_block(blk, newlink=None, attr=None):
    if newlink:
        blk = re.sub(r'^\t\(footprint "[^"]*"', '\t(footprint "%s"' % newlink, blk, 1, re.M)
    if attr and '(attr' not in blk:
        blk = re.sub(r'(\n\t\t\(layer "[^"]*"\)\n)', r'\1\t\t(attr %s)\n' % attr, blk, 1)
    return blk

def lib_text(blk):
    """library entry: board-authoritative content minus nets (nets are not lib content)."""
    return re.sub(r'\n\t\t\t\(net "[^"]*"\)', '', blk)

def canon_attr(fp, pcbnew):
    pads = [p for p in fp.Pads()]
    return 'smd' if pads and all(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in pads) else 'through_hole'

def load_board(path=BOARD):
    import pcbnew
    return {f.GetReference(): f for f in pcbnew.LoadBoard(path).GetFootprints()}

def load_lib(nick, name):
    import pcbnew
    d = os.path.join(PROJ_LIB, 'ForgeOS.pretty') if nick == 'ForgeOS' else None
    if d is None:
        for r in STD_ROOTS:
            if os.path.isdir(os.path.join(r, nick + '.pretty')):
                d = os.path.join(r, nick + '.pretty')
    if d is None:
        return None
    return pcbnew.FootprintLoad(d, name)

# ---------------------------------------------------------------- trigger matrix
G = lambda o, n: getattr(o, n)()

def _set_layers(pad, pcbnew, layers):
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    pad.SetLayerSet(ls)

def trigger_matrix(ref, out_root):
    import pcbnew
    fp = load_board()[ref]
    os.makedirs(out_root, exist_ok=True)
    blk = [b for r, _, _, b in spans(read(BOARD)) if r == ref][0]
    d = os.path.join(out_root, 'iso.pretty')
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    def base():
        open(os.path.join(d, 'base.kicad_mod'), 'w').write(blk)
        L = pcbnew.FootprintLoad(d, 'base')
        L.SetAttributes(fp.GetAttributes())
        return L
    mm = 1000000
    V = lambda x, y: pcbnew.VECTOR2I(x, y)
    cases = [
        ('COMPARED? layer:=B.Cu',          lambda x: x.SetLayer(pcbnew.B_Cu)),
        ('attr:=2 (SMD)',                  lambda x: x.SetAttributes(pcbnew.FP_SMD)),
        ('orient:=180',                    lambda x: x.SetOrientationDegrees(180)),
        ('position:=+10,+10',              lambda x: x.SetPosition(V(x.GetPosition().x + 10 * mm, x.GetPosition().y + 10 * mm))),
        ('Reference.text:=XX',             lambda x: x.Reference().SetText('XX')),
        ('Reference.layer:=B.SilkS',       lambda x: x.Reference().SetLayer(pcbnew.B_SilkS)),
        ('Reference.visible:=False',       lambda x: x.Reference().SetVisible(False)),
        ('Reference.pos:=+1,+1',           lambda x: x.Reference().SetPosition(V(x.Reference().GetPosition().x + mm, x.Reference().GetPosition().y + mm))),
        ('Value.text:=YY',                 lambda x: x.Value().SetText('YY')),
        ('pad0.layer_set:=B.Cu',           lambda x: _set_layers(list(x.Pads())[0], pcbnew, [pcbnew.B_Cu])),
        ('pad0.size:=+0.05',               lambda x: list(x.Pads())[0].SetSize(V(int(0.65 * mm), int(0.75 * mm)))),
        ('pad0.number:="9"',               lambda x: list(x.Pads())[0].SetNumber('9')),
        ('pad0.local_pos:=+0.05,0',        lambda x: list(x.Pads())[0].SetPosition(V(x.GetPosition().x + 50000, x.GetPosition().y))),
        ('pad0.orient:=90',                lambda x: list(x.Pads())[0].SetOrientationDegrees(90)),
        ('pad0.shape:=circle',             lambda x: list(x.Pads())[0].SetShape(pcbnew.PAD_SHAPE_CIRCLE)),
        ('pad0.attr:=PTH',                 lambda x: list(x.Pads())[0].SetAttribute(pcbnew.PAD_ATTRIB_PTH)),
        ('pad0.net:=7',                    lambda x: list(x.Pads())[0].SetNetCode(7)),
        ('add gfx PCB_SHAPE(F.SilkS)',     lambda x: x.Add(pcbnew.PCB_SHAPE(x))),
    ]
    # text-level probes (fields not settable through the API)
    def text_case(label, transform):
        t = os.path.join(d, 'tx.pretty'); os.makedirs(t, exist_ok=True)
        open(os.path.join(t, 't.kicad_mod'), 'w').write(transform(blk))
        L = pcbnew.FootprintLoad(t, 't'); L.SetAttributes(fp.GetAttributes())
        r = bool(fp.FootprintNeedsUpdate(L))
        print('  %-8s %-32s %s' % ('COMPARED' if r else 'ignored', label, r))
    def _pad0_uuid(b):
        parts = b.split('\n\t\t(pad "')
        if len(parts) < 3:
            return b
        p0 = re.sub(r'\(uuid "[^"]*"\)', '(uuid "11111111-2222-3333-4444-555555555555")', parts[1], 1)
        return parts[0] + '\n\t\t(pad "' + p0 + '\n\t\t(pad "' + '\n\t\t(pad "'.join(parts[2:])
    text_case('pad0.uuid:=other',    _pad0_uuid)
    text_case('fp.uuid:=other',      lambda b: re.sub(r'(\n\t\t\(uuid )"[^"]*"', r'\1"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"', b, 1))
    text_case('fp.path:=/x (if any)',lambda b: re.sub(r'(\n\t\t\(path )"[^"]*"', r'\1"/x"', b, 1))
    text_case('fp.tstamp:=other',    lambda b: re.sub(r'(\n\t\t\(tstamp )"[^"]*"', r'\1"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"', b, 1))
    print('board %s: attr=%d layer=%s  (base needs_update=%s)' % (ref, fp.GetAttributes(), fp.GetLayerName(), bool(fp.FootprintNeedsUpdate(base()))))
    for label, fn in cases:
        x = base()
        try:
            fn(x)
        except Exception as e:
            print('  ERR      %-32s %s' % (label, type(e).__name__)); continue
        r = bool(fp.FootprintNeedsUpdate(x))
        print('  %-8s %-32s %s' % ('COMPARED' if r else 'ignored', label, r))

# ---------------------------------------------------------------- DRC probe
def drc_run(d):
    out = os.path.join(d, 'drc.json')
    subprocess.run([CLI, 'pcb', 'drc', '--format', 'json', '--severity-error', '--severity-warning',
                    '--output', out, os.path.join(d, 'K2ISO.kicad_pcb')], capture_output=True)
    j = json.load(open(out))
    c = collections.Counter(x['type'] for x in j['violations'])
    refs = sorted(re.sub(r'^封装 ', '', x['items'][0].get('description', ''))
                  for x in j['violations'] if x['type'] == 'lib_footprint_mismatch')
    return len(j['violations']), dict(c), len(j['unconnected_items']), refs

def build(variant, out_root, fps, targets, relink, attr_policy, naming='per-item'):
    import pcbnew
    txt = read(BOARD)
    d = os.path.join(out_root, variant)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, 'boardlib.pretty'))
    out, prev, entries = [], 0, []
    for ref, s, e, blk in spans(txt):
        out.append(txt[prev:s]); prev = e
        if ref in targets:
            name = nick_name(fps[ref])[1]
            if relink and naming == 'per-ref':
                name = 'K2_' + ref
            nb = edit_block(blk, newlink=('ForgeOS:' + name) if relink else None,
                            attr=canon_attr(fps[ref], pcbnew) if attr_policy else None)
            if relink:
                entries.append((name, lib_text(edit_block(blk, attr=canon_attr(fps[ref], pcbnew) if attr_policy else None))))
            out.append(nb)
        else:
            out.append(blk)
    out.append(txt[prev:])
    open(os.path.join(d, 'K2ISO.kicad_pcb'), 'w').write(''.join(out))
    shutil.copy(PRO, os.path.join(d, 'K2ISO.kicad_pro'))
    open(os.path.join(d, 'fp-lib-table'), 'w').write(
        '(fp_lib_table\n\t(version 7)\n\t(lib (name "ForgeOS") (type "KiCad") (uri "${KIPRJMOD}/boardlib.pretty") (options "") (descr "probe"))\n)\n')
    seen = set()
    for name, content in entries:
        if name in seen:
            continue
        seen.add(name)
        open(os.path.join(d, 'boardlib.pretty', name + '.kicad_mod'), 'w').write(content)
    return d

def drc_probe(out_root):
    fps = load_board()
    import pcbnew
    base_drc = json.load(open('/tmp/d.json')) if os.path.exists('/tmp/d.json') else None
    if base_drc:
        bad = sorted(re.sub(r'^封装 ', '', x['items'][0].get('description', ''))
                     for x in base_drc['violations'] if x['type'] == 'lib_footprint_mismatch')
    else:
        d = build('P0', out_root, fps, [], False, False)
        bad = drc_run(d)[3]
    allrefs = sorted(fps)
    plan = [
        ('P1c', bad,    False, True,  'per-item'),
        ('P2',  bad,    True,  True,  'per-item'),
        ('P3',  allrefs, True, True,  'per-item'),
        ('P4',  allrefs, True, True,  'per-ref'),
    ]
    print('targets: %d mismatching refdes (from /tmp/d.json DRC); %d footprints on board' % (len(bad), len(allrefs)))
    for v, tgt, rel, at, nm in plan:
        d = build(v, out_root, fps, tgt, rel, at, nm)
        n, c, unc, refs = drc_run(d)
        print('%-4s relink=%-5s attr=%-5s naming=%-8s -> violations=%d %s unconnected=%d' % (v, rel, at, nm, n, c, unc))
        if refs:
            print('       still lib_footprint_mismatch (%d): %s' % (len(refs), refs))

# ---------------------------------------------------------------- main
if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['trigger-matrix', 'drc-probe'])
    ap.add_argument('--ref', default='U4')
    ap.add_argument('--out-root', default=DEF_OUT)
    a = ap.parse_args()
    if a.cmd == 'trigger-matrix':
        trigger_matrix(a.ref, a.out_root)
    else:
        drc_probe(a.out_root)
