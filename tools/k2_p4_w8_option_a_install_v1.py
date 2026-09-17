#!/usr/bin/env python3
"""K2 · P4 · W-8 选项 (甲′)「以板为准」落件器 —— **dry-run 默认；不改 SPEC / criteria / 冻结件**。

做什么（均为「不改 pad、不动铜」的文本/元数据改动 + 新库件）：
  1. 由**板自身**生成「项目 land pattern 库」（board-authoritative）：按 `FootprintNeedsUpdate`
     **等价内容**分组（pad 几何/层集合/attr/图形项/封装层），每组一条目；Reference→`REF**`，
     Value 保留；去掉 pad `(net …)`，归一 uuid/tstamp/锚点。
  2. 改 59 处封装**链接名**：`(footprint "<原链接>")` → `(footprint "ForgeOS:<组名>")`。
  3. 35 件 `attr=0`（非规范值；KiCad 库装载无法产出 0）补 `(attr smd|through_hole)`。
  另出 `fp-lib-table`（ForgeOS → ${KIPRJMOD}/<pretty 目录名>）。

不做（须获批后按既有约定另行执行）：SPEC rev bump、`pm_gate/project.yaml` bump、`criteria/` 安装、交付 Gerber。

用法（容器根）：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_w8_option_a_install_v1.py \
      --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
      --out /tmp/opencode/optiona/K2ISO.kicad_pcb \
      --pretty-dir /tmp/opencode/optiona/boardlib.pretty --table /tmp/opencode/optiona/fp-lib-table
  默认 dry-run：拒绝把 --out 指向仓库内；加 `--apply` 才允许（须守 T-22/T-25 + SPEC bump）。
"""
import argparse, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k2_w8_trigger_isolation_v1 as iso   # 复用 spans / edit_block / lib_text / canon_attr / nick_name

def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]

def norm_key(blk, attr):
    """needs_update 等价内容（分组用）：去网络、归一 ref/value/uuid/tstamp/封装锚点。"""
    t = iso.lib_text(iso.edit_block(blk, attr=attr))
    t = re.sub(r'(\(property "(?:Reference|Value)" ")[^"]*(")', r'\1X\2', t)
    t = re.sub(r'\(uuid "[^"]*"\)', '(uuid "0")', t)
    t = re.sub(r'\(tstamp "[^"]*"\)', '(tstamp "0")', t)
    m = re.search(r'\n\t\t\(at ([\d.\- ]+)\)', t)
    if m:   # 锚点：保留自转（实测 C85 rot=180 与 rot=0 同 pattern 若混组 => mismatch），仅归一 x/y
        _p = m.group(1).split(); _rot = _p[2] if len(_p) > 2 else '0'
        t = t[:m.start()] + '\n\t\t(at 0 0 %s)' % _rot + t[m.end():]
    return t

def lib_entry(blk, attr):
    t = iso.lib_text(iso.edit_block(blk, attr=attr))
    t = re.sub(r'(\(property "Reference" ")[^"]*(")', r'\1REF**\2', t, count=1)
    return t

def sanitize(s):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', s) or 'FP'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', default='k2/hw/k2_v4_8L.l5.kicad_pcb')
    ap.add_argument('--pro',   default='k2/hw/k2_v4_8L.l5.kicad_pro')
    ap.add_argument('--out',   default='/tmp/opencode/optiona/K2ISO.kicad_pcb')
    ap.add_argument('--pretty-dir', default='/tmp/opencode/optiona/boardlib.pretty')
    ap.add_argument('--table', default='/tmp/opencode/optiona/fp-lib-table')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--table-uri', default=None,
                    help='fp-lib-table 的 uri（默认 ${KIPRJMOD}/<pretty 目录名>）；仓库落件须写 ${KIPRJMOD}/lib/ForgeOS.pretty')
    ap.add_argument('--report', default=None)
    a = ap.parse_args()

    REPO = os.path.abspath('.')
    if not a.apply and os.path.abspath(a.out).startswith(REPO + os.sep):
        print('[FAIL] dry-run 拒绝写入仓库内 --out（加 --apply 才允许）：%s' % a.out); return 2
    pro_before = sha16(a.pro)
    import pcbnew
    fps = {f.GetReference(): f for f in pcbnew.LoadBoard(a.board).GetFootprints()}
    txt = iso.read(a.board)

    # ── pass 1：收集 + 分组 ──────────────────────────────────────────────
    items = [(ref, s, e, blk) for ref, s, e, blk in iso.spans(txt) if ref in fps]
    key_of, info = {}, {}
    for ref, s, e, blk in items:
        fp = fps[ref]
        attr = iso.canon_attr(fp, pcbnew)
        k = norm_key(blk, attr)
        key_of[ref] = k
        info[ref] = dict(blk=blk, orig=iso.nick_name(fp)[1], attr=attr,
                         cur_attr=int(fp.GetAttributes()), layer=fp.GetLayerName())
    order = sorted(set(key_of.values()))
    name_of = {}
    for i, k in enumerate(order, 1):
        first = min(r for r in key_of if key_of[r] == k)
        name_of[k] = 'K2_%s_%s_v%d' % (sanitize(info[first]['orig']),
                                       sanitize(info[first]['layer']).replace('.', ''), i)

    # ── pass 2：重写板文本（仅链接头 + attr 行）─────────────────────────
    out, prev, stats = [], 0, dict(footprints=0, links_rewritten=0, attr_added=0, groups=len(order), sides={})
    for ref, s, e, blk in iso.spans(txt):
        out.append(txt[prev:s]); prev = e
        if ref in info:
            i = info[ref]
            nb = iso.edit_block(blk, newlink='ForgeOS:' + name_of[key_of[ref]],
                                attr=i['attr'] if i['cur_attr'] == 0 else None)
            if i['cur_attr'] == 0: stats['attr_added'] += 1
            stats['links_rewritten'] += 1; stats['footprints'] += 1
            stats['sides'][i['layer']] = stats['sides'].get(i['layer'], 0) + 1
            out.append(nb)
        else:
            out.append(blk)
    out.append(txt[prev:])

    # ── 写库 + 表 + 板 ─────────────────────────────────────────────────
    os.makedirs(a.pretty_dir, exist_ok=True)
    # 幂等：只清本器自己的产物（K2_*.kicad_mod），不动目录内其它既有文件
    import glob as _glob
    for f in _glob.glob(os.path.join(a.pretty_dir, 'K2_*.kicad_mod')):
        os.remove(f)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.table)), exist_ok=True)
    written = 0
    for k, nm in name_of.items():
        first = min(r for r in key_of if key_of[r] == k)
        open(os.path.join(a.pretty_dir, nm + '.kicad_mod'), 'w').write(lib_entry(info[first]['blk'], info[first]['attr']))
        written += 1
    open(a.out, 'w').write(''.join(out))
    uri = a.table_uri or '${KIPRJMOD}/%s' % os.path.basename(a.pretty_dir.rstrip('/'))
    open(a.table, 'w').write(
        '(fp_lib_table\n\t(version 7)\n\t(lib (name "ForgeOS") (type "KiCad") '
        '(uri "%s") (options "") '
        '(descr "K2 board-authoritative land pattern library (W-8 option A)"))\n)\n' % uri)
    pro_after = sha16(a.pro)
    rep = dict(board_in=a.board, out=a.out, pretty=a.pretty_dir, table=a.table, table_uri=uri,
               footprints=stats['footprints'], groups=stats['groups'], entries_written=written,
               links_rewritten=stats['links_rewritten'], attr_added=stats['attr_added'],
               sides=stats['sides'], pro_unchanged=(pro_before == pro_after), pro_sha16=pro_after,
               spec_note='未改 SPEC：落件时须按既有约定出 SPEC rev-N 新文件 + bump pm_gate/project.yaml（获批后执行）')
    if a.report: json.dump(rep, open(a.report, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0

if __name__ == '__main__':
    sys.exit(main())
