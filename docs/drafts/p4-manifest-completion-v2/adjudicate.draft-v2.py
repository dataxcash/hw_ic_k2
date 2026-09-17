#!/usr/bin/env python3
"""criteria/adjudicate.py — 判定器（ENG 起草；监理以正控/负控验收后冻结）。

归属边界（K2-RULING-criteria-ownership-v1 / K2-RULING-plan-verdict-v1 §四-2）：
  - 判据「应然值/豁免」由 manifest 提供（监理持有）。本文件**不含**任何判据阈值。
  - 本文件只实现「把测量与 manifest 比对」的机制；结论由比对派生。
  - 产物侧：测量 JSON **不含 verdict 字段**；verdict 只由本判定器输出。
  - 缺件/不可解析 = FAIL（fail-closed）。

用法：
  python3 criteria/adjudicate.py --project k2 --board <board.kicad_pcb> \
      [--pro kicad_pro] [--nets k2_sch.yaml] [--sch-dir sch/] [--gerber-dir DIR] \
      [--measure-out /tmp/opencode/measure.json] [--out /tmp/opencode/verdict.json]
退出码：0 = PASS；1 = FAIL；2 = INFRA ERROR
"""
from __future__ import annotations
import argparse, json, math, os, re, sys, glob, subprocess, tempfile
from collections import Counter, defaultdict

# ─────────────────────────── 极简 s-expr 解析（与审计取证同源） ───────────────────────────
TOKEN_RE = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
def _tok(t): return TOKEN_RE.findall(t)
def _parse(text):
    toks = _tok(text); pos = 0
    def rd():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '(':
            out = []
            while toks[pos] != ')': out.append(rd())
            pos += 1; return out
        if t.startswith('"'): return t[1:-1]
        return t
    while toks[pos] != '(': pos += 1
    return rd()
def _all(n, k): return [c for c in n if isinstance(c, list) and c and c[0] == k]
def _one(n, k):
    for c in n:
        if isinstance(c, list) and c and c[0] == k: return c
    return None
def _txt(n, k, i=1):
    c = _one(n, k); return c[i] if c and len(c) > i else None

# ─────────────────────────── 测量（只产数字，不产结论） ───────────────────────────
def measure_board(path):
    root = _parse(open(path, encoding='utf-8').read())
    fps, zones, segs, vias = _all(root, 'footprint'), _all(root, 'zone'), _all(root, 'segment'), _all(root, 'via')
    m = {}
    fp_rows, all_pads = [], []
    for fp in fps:
        ref = None
        for p in _all(fp, 'property'):
            if len(p) > 2 and p[1] == 'Reference': ref = p[2]
        at = _one(fp, 'at') or ['at', '0', '0']
        fx, fy = float(at[1]), float(at[2]); rot = float(at[3]) if len(at) > 3 else 0.0
        pads = []
        for pad in _all(fp, 'pad'):
            num, ptype = pad[1], pad[2]
            pat = _one(pad, 'at') or ['at', '0', '0']
            psz = _one(pad, 'size') or ['size', '0', '0']
            net = _one(pad, 'net')
            netname = (net[1] if net and len(net) > 1 else None)
            p = dict(ref=ref, num=num, type=ptype,
                     dx=float(pat[1]), dy=float(pat[2]),
                     rot=float(pat[3]) if len(pat) > 3 else 0.0,
                     w=float(psz[1]), h=float(psz[2]), net=netname,
                     fx=fx, fy=fy, frot=rot)
            pads.append(p); all_pads.append(p)
        fp_rows.append(dict(ref=ref, libid=fp[1] if len(fp) > 1 else '', npad=len(pads), pads=pads))
    m['n_footprints'] = len(fp_rows)
    m['footprints_without_pads'] = sorted(r['ref'] for r in fp_rows if r['npad'] == 0)
    zf = []
    for z in zones:
        lay = _txt(z, 'layer'); neto = _one(z, 'net')
        zf.append(dict(layer=lay, net=(neto[1] if neto else None),
                       filled=len(_all(z, 'filled_polygon')),
                       keepout=_one(z, 'keepout') is not None,
                       keepout_flags=[c[1:] for c in _all(z, 'keepout')[0][1:]] if _one(z, 'keepout') else []))
    m['zones'] = zf
    m['zones_total'] = len(zf)
    m['zones_filled'] = sum(1 for z in zf if z['filled'] > 0)
    m['fillable_zones'] = sum(1 for z in zf if not z['keepout'])
    m['filled_fillable_zones'] = sum(1 for z in zf if not z['keepout'] and z['filled'] > 0)
    m['keepout_all_allowed'] = sum(1 for z in zf if z['keepout'] and all(v == 'allowed' for v in z['keepout_flags']))
    tc = Counter(p['type'] for p in all_pads)
    m['pad_types'] = dict(tc)
    m['npth'] = tc.get('np_thru_hole', 0)
    m['pth'] = tc.get('thru_hole', 0)
    def ang(g):
        return math.degrees(math.atan2(g['y2'] - g['y1'], g['x2'] - g['x1'])) % 180.0
    non45 = 0; pc = 0
    for g in segs:
        st, en = _one(g, 'start'), _one(g, 'end')
        if not st or not en: continue
        a = math.degrees(math.atan2(float(en[2]) - float(st[2]), float(en[1]) - float(st[1]))) % 180.0
        if min(abs(a - k) for k in (0, 45, 90, 135, 180)) > 0.001: non45 += 1
        neto = _one(g, 'net')
        if neto and neto[1].startswith('PCIE_'): pc += 1
    m['segments'] = len(segs); m['non45_segments'] = non45
    m['vias'] = len(vias)
    m['nets_on_board'] = sorted({p['net'] for p in all_pads if p['net']})
    m['pads_total'] = len(all_pads)
    m['pads_without_net'] = sum(1 for p in all_pads if not p['net'])
    m['_fp_rows'] = fp_rows
    return m

def measure_rule_severities(pro_path):
    if not pro_path or not os.path.exists(pro_path): return None
    d = json.load(open(pro_path, encoding='utf-8'))
    rs = d.get('board', {}).get('design_settings', {}).get('rule_severities', {})
    return dict(ignored=sorted(k for k, v in rs.items() if v == 'ignore'), total=len(rs))

def measure_netlist(path):
    if not path or not os.path.exists(path): return None
    try:
        import yaml
    except Exception:
        return {'error': 'pyyaml 不可用'}
    return yaml.safe_load(open(path, encoding='utf-8'))

def measure_declared_nets_realized(nets_yaml, board_m):
    """V1：每条声明网在板上焊盘数（需符号 pin_name→ball 映射）。"""
    if not nets_yaml: return None
    S = {s['name']: s for s in nets_yaml['symbols']}
    plc = {p['ref']: p for sh in nets_yaml['sheets'] for p in sh.get('placements', [])}
    def mcio(n):
        n = int(n); return f"A{(n+1)//2}" if n % 2 else f"B{n//2}"
    fn2ball = {}
    for sym_name, sym in S.items():
        for side, arr in sym['pins'].items():
            for e in arr: fn2ball[(sym_name, e[0])] = str(e[1])
    board = {r['ref']: {p['num']: p['net'] for p in r['pads']} for r in board_m['_fp_rows']}
    rows = []
    for net, nodes in nets_yaml['nets'].items():
        hit = 0; expected = 0
        for rp in nodes:
            ref, _, pin = str(rp).partition('/')
            if ref not in plc: continue
            sym = plc[ref]['symbol']
            ball = fn2ball.get((sym, pin))
            if ball is None: continue
            if sym == 'MCIO_4i': ball = mcio(ball)
            expected += 1
            if ref in board and board[ref].get(ball) == net: hit += 1
        rows.append(dict(net=net, declared_nodes=expected, realized=hit))
    return dict(nets=rows,
                nets_with_lt2=sum(1 for r in rows if r['realized'] < 2),
                nets_with_zero=sum(1 for r in rows if r['realized'] == 0))

def measure_pin_map(nets_yaml, board_m):
    """V2：每个 (ref,pin) 是否有对应焊盘；每器件 pad 数 vs 符号引脚数。"""
    if not nets_yaml: return None
    S = {s['name']: s for s in nets_yaml['symbols']}
    plc = {p['ref']: p for sh in nets_yaml['sheets'] for p in sh.get('placements', [])}
    def mcio(n):
        n = int(n); return f"A{(n+1)//2}" if n % 2 else f"B{n//2}"
    fn2ball = {}
    for sym_name, sym in S.items():
        for side, arr in sym['pins'].items():
            for e in arr: fn2ball[(sym_name, e[0])] = str(e[1])
    board = {r['ref']: r for r in board_m['_fp_rows']}
    missing = []
    for net, nodes in nets_yaml['nets'].items():
        for rp in nodes:
            ref, _, pin = str(rp).partition('/')
            if ref not in plc: continue
            sym = plc[ref]['symbol']; ball = fn2ball.get((sym, pin))
            if ball is None: continue
            if sym == 'MCIO_4i': ball = mcio(ball)
            if ref not in board or ball not in {p['num'] for p in board[ref]['pads']}:
                missing.append(dict(net=net, ref=ref, pin=pin, ball=ball))
    return dict(missing_nodes=len(missing), samples=missing[:10])

def measure_sch_refdes(sch_dir):
    if not sch_dir or not os.path.isdir(sch_dir): return None
    out = set()
    for f in glob.glob(os.path.join(sch_dir, '*.kicad_sch')):
        for mm in re.finditer(r'\(property "Reference" "([^"]+)"', open(f, encoding='utf-8').read()):
            r = mm.group(1)
            if r and not r.startswith('#') and '?' not in r: out.add(r)
    return sorted(out)

def measure_gerber_planes(gerber_dir):
    if not gerber_dir or not os.path.isdir(gerber_dir): return None
    rows = []
    for f in sorted(glob.glob(os.path.join(gerber_dir, '*.gbr'))):
        n = sum(1 for ln in open(f, encoding='utf-8', errors='replace') if ln.startswith('G36'))
        rows.append(dict(file=os.path.basename(f), g36=n))
    return rows

def find_project_pipelines(root='.'):
    return [p for p in glob.glob(os.path.join(root, '**', 'pipeline.yaml'), recursive=True)
            if '/.git/' not in p and '/archive/' not in p and '/node_modules/' not in p]

_EXCL = ('/.git/', '/archive/', '/_shared/', '/AppDir/', 'squashfs-root', '/demos/', '/template/', '/jlc_package/')
def find_sch_projects(root='.'):
    seen = set()
    for p in glob.glob(os.path.join(root, '*', '**', '*.kicad_sch'), recursive=True):
        if any(x in p for x in _EXCL): continue
        seen.add(p)
    return sorted(seen)


# ───────── #K2-20 §二 补齐转写：新增测量（ENG 草案；监理正/负控后版本 bump 安装） ─────────
REF_LAYERS = {'F.Cu': ('In1.Cu',), 'In2.Cu': ('In1.Cu', 'In3.Cu'),
              'In5.Cu': ('In4.Cu', 'In6.Cu'), 'B.Cu': ('In6.Cu',)}
HS_PREFIX = ('PCIE_', 'REFCLK')


def _pt_in_poly(px, py, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xin = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xin: inside = not inside
    return inside


def _seg_covered(x1, y1, x2, y2, polys):
    """段投影是否被（参考层）平面多边形覆盖全长：0.20mm 步长采样，每点须落在 ≥1 多边形内。"""
    L = math.hypot(x2 - x1, y2 - y1)
    n = max(2, int(L / 0.2) + 1)
    for k in range(n + 1):
        t = k / n
        px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        if not any(_pt_in_poly(px, py, poly) for poly in polys): return False
    return True


def run_drc(kicad_cli, board_path):
    """判定器**自跑** DRC（首选：provenance = 判定器自身；防伪造绿）。T-8：板与同名 .kicad_pro 必须同目录。"""
    if not kicad_cli or not os.path.exists(kicad_cli): return None
    fd, tmp = tempfile.mkstemp(suffix='.drc.json'); os.close(fd)
    cmd = [kicad_cli, 'pcb', 'drc', '--format', 'json', '--severity-error', '--severity-warning',
           '--output', tmp, board_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(tmp): return None
        return tmp
    except Exception:
        return None


def measure_drc(report_path, board_path=None):
    """J-1 / J-2 / J-7 数据源 = kicad-cli pcb drc --format json 原始报告（T-8 口径：仓库路径 + 同名 .kicad_pro）。"""
    if not report_path or not os.path.exists(report_path): return None
    try:
        d = json.load(open(report_path, encoding='utf-8'))
    except Exception:
        return None
    vs = d.get('violations') or []; us = d.get('unconnected_items') or []
    by = Counter(v.get('type') for v in vs)
    rows = [dict(type=v.get('type'), severity=v.get('severity'), description=v.get('description'),
                 items=[i.get('description') for i in (v.get('items') or [])]) for v in vs]
    src = d.get('source') or ''
    return dict(errors=sum(1 for v in vs if (v.get('severity') or 'error') == 'error'),
                source_matches=(board_path is None or os.path.basename(str(src)) == os.path.basename(board_path)),
                warnings=sum(1 for v in vs if v.get('severity') == 'warning'),
                unconnected=len(us), by_type=dict(by), violations=rows,
                lib_footprint_mismatch=int(by.get('lib_footprint_mismatch', 0)),
                lib_footprint_issues=int(by.get('lib_footprint_issues', 0)),
                source=d.get('source'), kicad_version=d.get('kicad_version'))


def measure_fp_lib_table(paths):
    found = [p for p in (paths or []) if os.path.exists(p)]
    return dict(present=bool(found), found=found, checked=list(paths or []))


def measure_extras(board_path, fp_lib_paths):
    """J-8 出框/回避区 + 密度（可量化部分） + V3 参考连续性。"""
    root = _parse(open(board_path, encoding='utf-8').read())
    xs, ys = [], []
    for g in _all(root, 'gr_line'):
        if _txt(g, 'layer') != 'Edge.Cuts': continue
        st, en = _one(g, 'start'), _one(g, 'end')
        if st and en: xs += [float(st[1]), float(en[1])]; ys += [float(st[2]), float(en[2])]
    bbox = (min(xs), min(ys), max(xs), max(ys)) if xs else None
    # 器件（含 pad）bbox vs 板框；器件原点入栅格做密度
    outside, cell = [], Counter()
    for fp in _all(root, 'footprint'):
        ref = None
        for p in _all(fp, 'property'):
            if len(p) > 2 and p[1] == 'Reference': ref = p[2]
        at = _one(fp, 'at'); fx, fy = float(at[1]), float(at[2])
        xs2, ys2 = [fx], [fy]
        for pad in _all(fp, 'pad'):
            pat = _one(pad, 'at') or ['at', '0', '0']; psz = _one(pad, 'size') or ['size', '0', '0']
            xs2 += [fx + float(pat[1]) - float(psz[1]) / 2, fx + float(pat[1]) + float(psz[1]) / 2]
            ys2 += [fy + float(pat[2]) - float(psz[2]) / 2, fy + float(pat[2]) + float(psz[2]) / 2]
        if bbox and (min(xs2) < bbox[0] or max(xs2) > bbox[2] or min(ys2) < bbox[1] or max(ys2) > bbox[3]):
            outside.append(ref)
        cell[(int(fx // 10), int(fy // 10))] += 1
    # keepout：多边形 + 开关（回避区 / IN-7）
    keepouts, all_allowed, esc_unrestricted, ko_rows = [], 0, 0, []
    for z in _all(root, 'zone'):
        ko = _one(z, 'keepout')
        if ko is None: continue
        fl = {c[0]: (c[1] if len(c) > 1 else None) for c in ko[1:]}
        if fl and all(v == 'allowed' for v in fl.values()): all_allowed += 1
        name = _txt(z, 'name') or ''
        if name.startswith('ESC_') and all(fl.get(k) == 'allowed' for k in ('tracks', 'vias', 'pads', 'footprints')):
            esc_unrestricted += 1
        ko_rows.append(dict(name=name, flags=fl))
        for poly in _all(z, 'polygon'):
            pts = _one(poly, 'pts')
            pl = [(float(xy[1]), float(xy[2])) for xy in _all(pts, 'xy')] if pts else []
            if len(pl) >= 3: keepouts.append(pl)
    # 平面（zone 外形）多边形按层
    planes = defaultdict(list)
    for z in _all(root, 'zone'):
        if _one(z, 'keepout') is not None: continue
        if not _all(z, 'filled_polygon'): continue          # 未填充的 zone 不算平面
        for poly in _all(z, 'polygon'):
            pts = _one(poly, 'pts')
            pl = [(float(xy[1]), float(xy[2])) for xy in _all(pts, 'xy')] if pts else []
            if len(pl) >= 3: planes[_txt(z, 'layer')].append(pl)
    # V3：高速段逐段投影覆盖
    hs_total, unreferenced = 0, []
    for g in _all(root, 'segment'):
        net = _txt(g, 'net') or ''
        if not net.startswith(HS_PREFIX): continue
        hs_total += 1
        lay = _txt(g, 'layer'); st, en = _one(g, 'start'), _one(g, 'end')
        if not (lay in REF_LAYERS and st and en): continue
        if not any(_seg_covered(float(st[1]), float(st[2]), float(en[1]), float(en[2]), planes.get(r, []))
                   for r in REF_LAYERS[lay]):
            unreferenced.append(dict(net=net, layer=lay, start=[float(st[1]), float(st[2])],
                                     end=[float(en[1]), float(en[2])]))
    return dict(outline_bbox=bbox, footprints_outside=sorted(r for r in outside if r),
                keepout_polygons=len(keepouts), keepout_regions_all_allowed=all_allowed,
                esc_unrestricted=esc_unrestricted, keepout_rows=ko_rows,
                density_max_per_10mm_cell=(max(cell.values()) if cell else 0),
                density_cells=len(cell), hs_segments=hs_total,
                unreferenced_hs_segments=len(unreferenced), v3_samples=unreferenced[:5],
                fp_lib_table=measure_fp_lib_table(fp_lib_paths),
                plane_polygons_by_layer={k: len(v) for k, v in planes.items()})

# ─────────────────────────── 判定（唯一产出 verdict 的地方） ───────────────────────────
def adjudicate(manifest, meas, args):
    fails, oks = [], []
    C = manifest.get('checks', {})
    def chk(name, cond, detail):
        (oks if cond else fails).append(dict(check=name, ok=bool(cond), detail=detail))

    if C.get('zone_filled', {}).get('enabled'):
        # U4-A 修实现：keepout/rule-area 结构上不可能有 filled_polygon（P3-5/C5b 要求其存在且限制），
        # 分母 = 可填充 zone（非 keepout）；分子 = 其中已填充者。 依据 K2-RULING-p3-closure-and-p4-open-v1 §C7 注。
        ok_z = meas['fillable_zones'] > 0 and meas['filled_fillable_zones'] == meas['fillable_zones']
        chk('zone_filled', ok_z,
            f"已填充 {meas['filled_fillable_zones']}/{meas['fillable_zones']}（可填充=非 keepout；keepout {meas['zones_total'] - meas['fillable_zones']} 个结构不可填）")
    if C.get('device_has_pads', {}).get('enabled'):
        chk('device_has_pads', not meas['footprints_without_pads'],
            f"0 焊盘器件 {len(meas['footprints_without_pads'])}: {meas['footprints_without_pads']}")
    if C.get('drill_count', {}).get('enabled'):
        # 转写补正（#K2-20 §二）：npth >= 1 → npth >= 4（计划 §P4「钻孔前置 NPTH ≥ 4」+ 审计 §10.8 L2-8 8e）
        spec_npth = int(manifest.get('drill_npth_min') or 4)
        _pth = manifest.get('drill_pth_min')
        spec_pth = 0 if _pth is None else int(_pth)   # null = 待监理给算式（ENG 不代填）
        chk('drill_count', meas['npth'] >= spec_npth and meas['pth'] >= spec_pth,
            f"NPTH={meas['npth']}（要求 ≥{spec_npth}）PTH={meas['pth']}（要求 ≥{spec_pth}）")
    if C.get('non45_segments', {}).get('enabled'):
        chk('non45_segments', meas['non45_segments'] == 0,
            f"非 45° 段 {meas['non45_segments']}/{meas['segments']}")

    rs = meas.get('rule_severities')
    if rs is None:
        chk('rule_severity_manifest', False, "缺少 .kicad_pro（fail-closed）")
    else:
        exempt = set(manifest.get('rule_severity_exemptions') or [])
        bad = [k for k in rs['ignored'] if k not in exempt]
        chk('rule_severity_manifest', not bad,
            f"未登记豁免的 ignore {len(bad)}/{rs['total']}: {bad}")

    nr = meas.get('declared_nets')
    if C.get('net_declared_realized', {}).get('enabled'):
        if nr is None: chk('net_declared_realized', False, "缺少网表（fail-closed）")
        else: chk('net_declared_realized', nr['nets_with_zero'] == 0,
                  f"板上 0 焊盘的声明网 = {nr['nets_with_zero']}；<2 焊盘 = {nr['nets_with_lt2']}")
    pm = meas.get('pin_map')
    if C.get('pin_map_complete', {}).get('enabled'):
        if pm is None: chk('pin_map_complete', False, "缺少网表（fail-closed）")
        else: chk('pin_map_complete', pm['missing_nodes'] == 0,
                  f"网表节点无对应焊盘 = {pm['missing_nodes']}")

    if C.get('refdes_sets_equal', {}).get('enabled'):
        sr = meas.get('sch_refdes')
        if sr is None: chk('refdes_sets_equal', False, "缺少原理图（fail-closed）")
        else:
            S = set(sr)
            mech = set(manifest.get('mechanical_refdes') or [])
            Bd = set(r['ref'] for r in meas['_fp_rows'] if r['ref'])
            extra = Bd - S
            chk('refdes_sets_equal', S == Bd - extra.intersection(mech) and not extra - mech,
                f"原理图 {len(S)} / 板 {len(Bd)}；图有板无 {len(S-Bd)}；板有图无 {len(extra)}（其中机械件已登记 {len(extra_mech := sorted(extra.intersection(mech)))} 件: {extra_mech}）；未登记 {sorted(extra - mech)}")

    if C.get('pipeline_present', {}).get('enabled'):
        schs = find_sch_projects(args.root)
        # W-9（监理 #K2-19 §二）：k2 门 = k2-scoped —— 只判 manifest.pipeline_scope 列出的项目
        # 目录；其余项目（k1 / pciesw4 …）在各自阶段门判。空/缺省 ⇒ 全仓（保守）。
        _scope = [str(x).strip('/') for x in (manifest.get('pipeline_scope') or []) if str(x).strip('/')]
        if _scope:
            _pre = tuple(s_ + '/' for s_ in _scope)
            schs = [f for f in schs
                    if os.path.relpath(os.path.abspath(f), os.path.abspath(args.root)).replace(os.sep, '/')
                    .startswith(_pre)]
        uncovered = []
        for f in schs:
            d = os.path.dirname(os.path.abspath(f)); found = False
            for _ in range(4):                      # 自身 + 最多 3 层祖先
                if os.path.exists(os.path.join(d, 'pipeline.yaml')): found = True; break
                nd = os.path.dirname(d)
                if nd == d: break
                d = nd
            if not found: uncovered.append(os.path.dirname(os.path.relpath(f, args.root)))
        uniq = sorted(set(uncovered))
        chk('pipeline_present', not uniq,
            f"含 .kicad_sch 但无 pipeline.yaml 的目录 {len(uniq)} 个（fail-closed）: {uniq[:5]}")

    drc = meas.get('drc')
    if C.get('drc_errors', {}).get('enabled'):
        if drc is None: chk('drc_errors', False, "缺少 DRC 实跑报告（fail-closed；须 kicad-cli 仓库路径 + 同名 .kicad_pro 口径）")
        elif not drc['source_matches']: chk('drc_errors', False, f"DRC 报告 source 与板不一致（fail-closed，防伪造绿）: {drc['source']}")
        else: chk('drc_errors', drc['errors'] == 0, f"DRC error = {drc['errors']}（类型: {drc['by_type']}；自跑={drc.get('self_run')}）")
    if C.get('drc_warning_disposition', {}).get('enabled'):
        if drc is None: chk('drc_warning_disposition', False, "缺少 DRC 实跑报告（fail-closed）")
        else:
            disp = manifest.get('drc_warning_dispositions') or []
            und = [r for r in drc['violations'] if r['severity'] == 'warning' and r['type'] not in disp]
            chk('drc_warning_disposition', not und,
                f"未登记处置的 warning = {len(und)}/{drc['warnings']}（类型: {sorted({r['type'] for r in und})}）")
    if C.get('unconnected_zero', {}).get('enabled'):
        if drc is None: chk('unconnected_zero', False, "缺少 DRC 实跑报告（fail-closed；V1 要求 DRC 实跑、范围=权威网表全集）")
        elif not drc['source_matches']: chk('unconnected_zero', False, f"DRC 报告 source 与板不一致（fail-closed）: {drc['source']}")
        else: chk('unconnected_zero', drc['unconnected'] == 0, f"未连接 = {drc['unconnected']}（全量，禁裁剪）")
    if C.get('lib_footprint_electrical', {}).get('enabled'):
        if drc is None: chk('lib_footprint_electrical', False, "缺少 DRC 实跑报告（fail-closed）")
        else:
            n = drc['lib_footprint_mismatch'] + drc['lib_footprint_issues']
            chk('lib_footprint_electrical', n == 0,
                f"封装≠库 = mismatch {drc['lib_footprint_mismatch']} + issues {drc['lib_footprint_issues']} = {n}")
    if C.get('fp_lib_table_present', {}).get('enabled'):
        fx = meas.get('extras', {}).get('fp_lib_table')
        if not fx: chk('fp_lib_table_present', False, "缺少几何测量（fail-closed）")
        else: chk('fp_lib_table_present', fx['present'],
                  f"fp-lib-table 存在 = {fx['present']}（查: {fx['checked']}，命中: {fx['found']}）")
    ex = meas.get('extras')
    if C.get('board_frame_and_keepout', {}).get('enabled'):
        if ex is None: chk('board_frame_and_keepout', False, "缺少几何测量（fail-closed）")
        else:
            chk('board_frame_and_keepout',
                not ex['footprints_outside'] and ex['esc_unrestricted'] == 0,
                f"出框器件 {len(ex['footprints_outside'])} {ex['footprints_outside'][:6]}；"
                f"ESC_* 回避区空操作（tracks/vias/pads/footprints 全 allowed）= {ex['esc_unrestricted']}"
                f"（C5b/IN-7 要求每区 ≥1 非 allowed）；全 allowed keepout 区数（含 copperpour）= {ex['keepout_regions_all_allowed']}")
    if C.get('density_and_spacing', {}).get('enabled'):
        if ex is None: chk('density_and_spacing', False, "缺少几何测量（fail-closed）")
        else:
            thr = manifest.get('thresholds') or {}
            mx = thr.get('density_max_per_10mm_cell')
            chk('density_and_spacing', mx is not None and ex['density_max_per_10mm_cell'] <= mx,
                f"密度峰值 {ex['density_max_per_10mm_cell']} 件/10mm 格（阈值 {mx} 待监理填）")
    if C.get('v3_reference_continuity', {}).get('enabled'):
        if ex is None: chk('v3_reference_continuity', False, "缺少几何测量（fail-closed）")
        else:
            chk('v3_reference_continuity', ex['unreferenced_hs_segments'] == 0,
                f"参考平面未覆盖高速段 = {ex['unreferenced_hs_segments']}/{ex['hs_segments']}（逐段投影采样 0.2mm）")

    vs = meas.get('verdict_keys_found')
    if C.get('verdict_schema', {}).get('enabled'):
        chk('verdict_schema', not vs, f"产物中出现 verdict 字段的文件: {vs}")

    return dict(passed=not fails, n_pass=len(oks), n_fail=len(fails), fails=fails, oks=oks)

def scan_verdict_keys(paths):
    bad = []
    for p in paths:
        try:
            if p.endswith('.json'):
                txt = open(p, encoding='utf-8', errors='replace').read()
                if re.search(r'"verdict"\s*:', txt): bad.append(os.path.basename(p))
        except Exception: pass
    return bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', default='k2')
    ap.add_argument('--manifest', default=None)
    ap.add_argument('--board', default=None)
    ap.add_argument('--pro', default=None)
    ap.add_argument('--nets', default=None)
    ap.add_argument('--sch-dir', default=None)
    ap.add_argument('--gerber-dir', default=None)
    ap.add_argument('--drc', default=None, help='外部 kicad-cli DRC 报告（J-1/J-2/J-7 数据源；T-8 口径）')
    ap.add_argument('--kicad-cli', default=None, help='**判定器自跑 DRC**（首选，防伪造绿）：kicad-cli 可执行路径')
    ap.add_argument('--artifacts', nargs='*', default=[])
    ap.add_argument('--root', default='.')
    ap.add_argument('--measure-out', default=None)
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    mpath = args.manifest or os.path.join(here, f'manifest.{args.project}.yaml')
    if not os.path.exists(mpath):
        print(f"[FAIL] manifest 缺失: {mpath}（fail-closed）"); return 1
    try:
        import yaml; manifest = yaml.safe_load(open(mpath, encoding='utf-8'))
    except Exception as e:
        print(f"[FAIL] manifest 不可解析: {e}（fail-closed）"); return 1
    if args.board is None or not os.path.exists(args.board):
        print(f"[FAIL] board 缺失: {args.board}（fail-closed）"); return 1
    try:
        bm = measure_board(args.board)
    except Exception as e:
        print(f"[INFRA] board 解析失败: {e}"); return 2
    nets_yaml = measure_netlist(args.nets)
    meas = {k: v for k, v in bm.items() if k != '_fp_rows'}
    meas['rule_severities'] = measure_rule_severities(args.pro)
    meas['declared_nets'] = measure_declared_nets_realized(nets_yaml, bm)
    meas['pin_map'] = measure_pin_map(nets_yaml, bm)
    meas['sch_refdes'] = measure_sch_refdes(args.sch_dir)
    meas['gerber_planes'] = measure_gerber_planes(args.gerber_dir)
    drc_path = args.drc
    self_run = False
    if args.kicad_cli:
        got = run_drc(args.kicad_cli, args.board)
        if got:
            drc_path = got; self_run = True
    meas['drc'] = measure_drc(drc_path, args.board)
    if isinstance(meas['drc'], dict):
        meas['drc']['self_run'] = self_run
        meas['drc']['report_path'] = drc_path
    manifest_probe = {}
    try:
        import yaml as _y; manifest_probe = _y.safe_load(open(mpath, encoding='utf-8')) or {}
    except Exception:
        manifest_probe = {}
    meas['extras'] = measure_extras(args.board, manifest_probe.get('fp_lib_table_paths'))
    meas['verdict_keys_found'] = scan_verdict_keys(args.artifacts)
    meas['_note'] = '测量件：不含 verdict 字段（C4）'
    bm['_fp_rows'] = bm['_fp_rows']
    if args.measure_out:
        json.dump(meas, open(args.measure_out, 'w'), ensure_ascii=False, indent=1)
    verdict = adjudicate(manifest, {**meas, '_fp_rows': bm['_fp_rows']}, args)
    verdict['provisional'] = bool(manifest.get('not_countersigned'))
    verdict['manifest'] = os.path.basename(mpath)
    verdict['board'] = os.path.basename(args.board)
    print(f"=== 判定 {args.project} @ {os.path.basename(args.board)} ===")
    print(f"  manifest: {os.path.basename(mpath)}  countersigned={not manifest.get('not_countersigned')}")
    for r in verdict['oks']:   print(f"  [OK]   {r['check']}: {r['detail']}")
    for r in verdict['fails']: print(f"  [FAIL] {r['check']}: {r['detail']}")
    print(f"  => {'PASS' if verdict['passed'] else 'FAIL'}"
          + ("（PROVISIONAL：manifest 未经监理签认）" if verdict['provisional'] else ""))
    if args.out: json.dump(verdict, open(args.out, 'w'), ensure_ascii=False, indent=1)
    return 0 if verdict['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
