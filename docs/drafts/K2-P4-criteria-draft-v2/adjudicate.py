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
import argparse, json, math, os, re, shutil, subprocess, sys, glob, tempfile, hashlib
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
    m['zones_keepout'] = sum(1 for z in zf if z['keepout'])
    _zc = [z for z in zf if (not z['keepout']) and z['net']]
    m['zones_total'] = len(_zc)
    m['zones_filled'] = sum(1 for z in _zc if z['filled'] > 0)
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

def measure_drc(kicad_cli, board, pro, work_dir):
    if not kicad_cli or not os.path.exists(kicad_cli) or not board or not os.path.exists(board):
        return None
    stem = os.path.splitext(os.path.basename(board))[0]
    wd = os.path.join(work_dir or os.path.join(tempfile.gettempdir(), 'adj-drc'), stem)
    os.makedirs(wd, exist_ok=True)
    b = os.path.join(wd, stem + '.kicad_pcb'); shutil.copy2(board, b)
    if pro and os.path.exists(pro):
        shutil.copy2(pro, os.path.join(wd, stem + '.kicad_pro'))
    for pat in ('fp-lib-table', 'lib'):
        src = os.path.join(os.path.dirname(os.path.abspath(board)), pat); dst = os.path.join(wd, pat)
        if os.path.exists(src) and not os.path.exists(dst):
            try: (shutil.copytree if os.path.isdir(src) else shutil.copy2)(src, dst)
            except Exception: pass
    out = os.path.join(wd, 'drc.json')
    r = subprocess.run([kicad_cli, 'pcb', 'drc', '--format', 'json', '--severity-all', '--output', out, b],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out): return None
    d = json.load(open(out, encoding='utf-8')); vios = d.get('violations', [])
    err = [v for v in vios if v.get('severity') == 'error']
    return dict(errors=len(err), total=len(vios), error_types=sorted({v['type'] for v in err}),
                warning_types=sorted({v['type'] for v in vios if v.get('severity') == 'warning'}),
                unconnected=len(d.get('unconnected_items', [])), report=out)


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

# ─────────────────────────── 判定（唯一产出 verdict 的地方） ───────────────────────────
def adjudicate(manifest, meas, args):
    fails, oks = [], []
    C = manifest.get('checks', {})
    def chk(name, cond, detail):
        (oks if cond else fails).append(dict(check=name, ok=bool(cond), detail=detail))

    if C.get('zone_filled', {}).get('enabled'):
        chk('zone_filled', meas['zones_filled'] == meas['zones_total'] and meas['zones_total'] > 0,
            f"铜区（有网非 keepout）已填充 {meas['zones_filled']}/{meas['zones_total']}；keepout 规则区 {meas.get('zones_keepout')} 个另计（不入分母）")
    if C.get('device_has_pads', {}).get('enabled'):
        chk('device_has_pads', not meas['footprints_without_pads'],
            f"0 焊盘器件 {len(meas['footprints_without_pads'])}: {meas['footprints_without_pads']}")
    if C.get('drill_count', {}).get('enabled'):
        _need = int(C['drill_count'].get('npth_min', 1))
        chk('drill_count', meas['npth'] >= _need, f"NPTH={meas['npth']}（应 ≥{_need}）PTH={meas['pth']}")
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
            _ball = set(r['ref'] for r in meas['_fp_rows'] if r['ref'])
            _mech = sorted(r for r in (set(sr) | _ball) if re.fullmatch(r'H\d+', r))
            S, Bd = set(sr) - set(_mech), _ball - set(_mech)
            chk('refdes_sets_equal', S == Bd,
                f"排除纯机械件 H*（{len(_mech)} 条逐条列名: {_mech}）⇒ 原理图 {len(S)} / 板 {len(Bd)}；图有板无 {sorted(S-Bd)}，板有图无 {sorted(Bd-S)}")

    if C.get('pipeline_present', {}).get('enabled'):
        schs_all = find_sch_projects(args.root)
        _scope = C['pipeline_present'].get('scope')
        if _scope:
            _base = os.path.abspath(os.path.join(args.root, _scope)) + os.sep
            schs = [f for f in schs_all if os.path.abspath(f).startswith(_base)]
            _outside = sorted({os.path.dirname(os.path.relpath(f, args.root)) for f in schs_all if f not in set(schs)})
        else:
            schs, _outside = schs_all, []
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
            f"scope={_scope or 'ALL'}：含 .kicad_sch 但无 pipeline.yaml 的目录 {len(uniq)} 个（fail-closed）: {uniq[:5]}"
            + (f"；范围外（他项目阶段门判）{len(_outside)} 个: {_outside[:5]}" if _outside else ""))

    drc = meas.get('drc')
    if C.get('drc_errors', {}).get('enabled'):
        if drc is None:
            chk('drc_errors', False, "缺 DRC 实跑（--drc-cli）⇒ fail-closed")
        else:
            chk('drc_errors', drc['errors'] == 0, f"DRC error={drc['errors']}（违规总 {drc['total']}）: {drc['error_types']}")
    if C.get('drc_warning_dispositions', {}).get('enabled'):
        if drc is None:
            chk('drc_warning_dispositions', False, "缺 DRC 实跑 ⇒ fail-closed")
        else:
            _reg = {d.get('type') for d in (manifest.get('drc_warning_dispositions') or [])}
            _live = set(drc['warning_types'])
            chk('drc_warning_dispositions', not (_live - _reg),
                f"未登记 warning 类型 {len(_live - _reg)}/{len(_live)}: {sorted(_live - _reg)}；已登记 {sorted(_live & _reg)}")
    if C.get('unconnected_zero', {}).get('enabled'):
        if drc is None:
            chk('unconnected_zero', False, "缺 DRC 实跑 ⇒ fail-closed")
        else:
            chk('unconnected_zero', drc['unconnected'] == 0, f"unconnected_items = {drc['unconnected']}")
    if C.get('fp_lib_table_present', {}).get('enabled'):
        _d = os.path.dirname(os.path.abspath(args.board)) if args.board else None
        _ok = bool(_d) and os.path.exists(os.path.join(_d, 'fp-lib-table'))
        chk('fp_lib_table_present', _ok, f"fp-lib-table @ {_d or '(未给板)'}: {'存在' if _ok else '缺失'}")
    if C.get('lib_electrical_level', {}).get('enabled'):
        aud = meas.get('w8_audit')
        if aud is None:
            chk('lib_electrical_level', False, "缺 W-8 电气级审计 JSON（--w8-audit-json）⇒ fail-closed")
        else:
            _sm = aud.get('summary', {})
            _bsha = None
            if args.board and os.path.exists(args.board):
                _bsha = hashlib.sha256(open(args.board, 'rb').read()).hexdigest()[:16]
            _fresh = (_bsha is not None and _sm.get('board_sha16') == _bsha)
            _nd = _sm.get('n_electrical_diff', -1); _np = _sm.get('n_pad_name_set_only', -1)
            chk('lib_electrical_level', bool(_fresh) and _nd == 0 and _np == 0,
                f"电气级差异 {_nd} + 仅 pad 名差异 {_np}（须 0）；审计板 sha16={_sm.get('board_sha16')} vs 受审板 {_bsha}"
                f" ⇒ {'一致' if _fresh else '不一致（证据陈旧，fail-closed）'}")
    if C.get('keepout_active', {}).get('enabled'):
        _zk = [z for z in meas['zones'] if z['keepout']]
        _bad = [z for z in _zk if not z['keepout_flags'] or all(v == 'allowed' for v in z['keepout_flags'])]
        chk('keepout_active', bool(_zk) and not _bad,
            f"keepout 区 {len(_zk)} 个；其中无生效开关（全 allowed / 无 flag）{len(_bad)} 个")

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
    ap.add_argument('--artifacts', nargs='*', default=[])
    ap.add_argument('--root', default='.')
    ap.add_argument('--measure-out', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--drc-cli', default=None)
    ap.add_argument('--drc-work-dir', default=None)
    ap.add_argument('--w8-audit-json', default=None)
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
    meas['drc'] = measure_drc(args.drc_cli, args.board, args.pro, args.drc_work_dir)
    if args.w8_audit_json and os.path.exists(args.w8_audit_json):
        meas['w8_audit'] = json.load(open(args.w8_audit_json, encoding='utf-8'))
    else:
        meas['w8_audit'] = None
    meas['declared_nets'] = measure_declared_nets_realized(nets_yaml, bm)
    meas['pin_map'] = measure_pin_map(nets_yaml, bm)
    meas['sch_refdes'] = measure_sch_refdes(args.sch_dir)
    meas['gerber_planes'] = measure_gerber_planes(args.gerber_dir)
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
