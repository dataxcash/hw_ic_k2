#!/usr/bin/env python3
"""负控造件（ENG 草案自测 v2）：对当前板做**定向缺陷注入**，验证草案判据能抓住。仅在 /tmp 造件。

v2 变更（2026-09-17，增量 16 板格式适配）：
  - 板件封装头已为 KiCad 新格式 `\t(footprint "LIB:NAME"`（v1 的正则 `\t(footprint\n` 在增量 16 板上失效 => m6 未注入）；
    改为**括号匹配 + 字符串感知**定位块，与格式无关。
  - m6 由「删 pad」（会连带改变多项计数）改为「U1.11 pad 尺寸 +0.05mm」= 纯电气级几何突变，定向测 J-7。
"""
import os, re, shutil
SRC = '/home/fila/jqdDev_2025/ic_hw/k2/hw/k2_v4_8L.l5.kicad_pcb'
PRO = '/home/fila/jqdDev_2025/ic_hw/k2/hw/k2_v4_8L.l5.kicad_pro'
OUT = '/tmp/opencode/p4/draft/neg'
os.makedirs(OUT, exist_ok=True)
txt = open(SRC, encoding='utf-8').read()


def match_end(s, i):
    """i = 指向 '(' 的下标；返回配对 ')' 之后的下标（字符串感知）。"""
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
    raise ValueError('unbalanced parens')


def write(name, s):
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + '.kicad_pcb'), 'w', encoding='utf-8').write(s)
    shutil.copyfile(PRO, os.path.join(d, name + '.kicad_pro'))
    # 库解析同目录（T-8）：fp-lib-table + lib/ 一并落件，否则 ${KIPRJMOD} 指向 /tmp 落空
    tb = '/home/fila/jqdDev_2025/ic_hw/k2/hw/fp-lib-table'
    if os.path.exists(tb): shutil.copyfile(tb, os.path.join(d, 'fp-lib-table'))
    lib = '/home/fila/jqdDev_2025/ic_hw/k2/hw/lib'
    if os.path.isdir(lib): shutil.copytree(lib, os.path.join(d, 'lib'), dirs_exist_ok=True)


# M1：删 1 条 F.Cu 走线 ⇒ 未连接 ↑（J-2/V1）
m = re.search(r'\t\(segment\n(?=[\s\S]*?\(layer "F\.Cu"\))[\s\S]*?\n\t\)\n', txt)
write('m1_unconnected', txt[:m.start()] + txt[m.end():])

# M2：清空 In3.Cu GND 铜区的 filled_polygon ⇒ zone_filled 8/9（J-3/U4-A）；In1 仍在 ⇒ V3 不受影响（隔离）
def zone_spans(t):
    spans = []
    for mm in re.finditer(r'\n\t\(zone\n', t):
        e = t.find('\n\t)\n', mm.start())
        spans.append((mm.start() + 1, e + 4))
    return spans

mt = txt
for a, e in zone_spans(txt):
    blk = txt[a:e]
    if '(layer "In3.Cu")' in blk and '(keepout' not in blk:
        new = blk
        while True:
            f0 = new.find('\t\t(filled_polygon\n')
            if f0 < 0: break
            f1 = new.find('\n\t\t)\n', f0) + len('\n\t\t)\n')
            new = new[:f0] + new[f1:]
        mt = txt[:a] + new + txt[e:]
        break
write('m2_unfilled', mt)

# M3：注入 1 条 30° 走线 ⇒ non45 +1（J-5）
seg = ('\t(segment\n\t\t(start 100 40)\n\t\t(end 101 40.5774)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n'
       '\t\t(net "GND")\n\t\t(uuid "aaaaaaaa-0000-0000-0000-00000000m3aa")\n\t)\n')
i = txt.index('\t(segment\n')
write('m3_non45', txt[:i] + seg + txt[i:])

# M4：删 In6.Cu GND 平面 zone 的**外形 polygon** ⇒ B.Cu 高速段失去参考（隔离 V3）
mt4 = txt
for a, e in zone_spans(txt):
    blk = txt[a:e]
    if '(layer "In6.Cu")' in blk and '(keepout' not in blk:
        mt4 = txt[:a] + blk.replace('\t\t(polygon\n', '\t\t(xpolygon\n', 1) + txt[e:]
        break
write('m4_no_ref_in6', mt4)

# M5：改 1 个 refdes（C85→X99）⇒ 未登记件（J-6）
write('m5_refdes', txt.replace('(property "Reference" "C85"', '(property "Reference" "X99"', 1))

# M6：U1.11 pad 尺寸 +0.05mm ⇒ 封装≠库（电气级几何）（J-7）；注：U1 为**裸名**（无库链接）
#     ⇒ 对 J-7「电气级逐件比」**不可判**（并入 no_library_link 计不合格）；保留作覆盖缺口对照。
j = txt.find('(property "Reference" "U1"')
s6 = txt
if j > 0:
    z = txt.rfind('\n\t(footprint ', 0, j) + 1          # 指向 '('
    ze = match_end(txt, z)
    fp = txt[z:ze]
    p = fp.find('\n\t\t(pad "11"')
    if p >= 0:
        pe = match_end(fp, fp.index('(', p))             # 指向 pad '('
        blk = fp[p:pe]
        mm = re.search(r'\(size ([-\d.]+) ([-\d.]+)\)', blk)
        w, h = float(mm.group(1)), float(mm.group(2))
        nb = (blk[:mm.start()] + f'(size {round(w + 0.05, 4)} {h})' + blk[mm.end():])
        s6 = txt[:z] + fp[:p] + nb + fp[pe:] + txt[ze:]
        print(f'm6: U1.11 size {w}x{h} -> {round(w + 0.05, 4)}x{h}')
if s6 is txt:
    raise SystemExit('M6 注入失败（未找到 U1.11 pad）')
write('m6_u1_pad', s6)

# M7：U5 pad1 尺寸 +0.05mm —— U5 是板内**电气级与库完全一致**的 2 件之一（U4/U5）
#     ⇒ 针对 J-7 电气级实现的正/负控「定向注入」；期望：U5 被点名、差异件数 33→34。
j7 = txt.find('(property "Reference" "U5"')
if j7 <= 0: raise SystemExit('M7 注入失败（未找到 U5）')
z = txt.rfind('\n\t(footprint ', 0, j7) + 1
ze = match_end(txt, z)
fp = txt[z:ze]
p7 = fp.find('\n\t\t(pad "1"')
if p7 < 0: p7 = fp.find('\n\t\t(pad ')
pe = match_end(fp, fp.index('(', p7))
blk = fp[p7:pe]
mm = re.search(r'\(size ([\d.]+) ([\d.]+)\)', blk)
w, h = float(mm.group(1)), float(mm.group(2))
nb = blk[:mm.start()] + f'(size {round(w + 0.05, 4)} {h})' + blk[mm.end():]
print(f'm7: U5 pad size {w}x{h} -> {round(w + 0.05, 4)}x{h}')
write('m7_u5_pad', txt[:z] + fp[:p7] + nb + fp[pe:] + txt[ze:])

# M8：破坏库链接（C89 链接改指向不存在的库件）⇒ J-7 覆盖失败（fail-closed）
s8 = txt.replace('(footprint "Capacitor_SMD:C_0603_1608Metric"',
                 '(footprint "Capacitor_SMD:C_9999_NOPE"', 1)
if s8 is txt: raise SystemExit('M8 注入失败')
write('m8_link_broken', s8)
print('mutants:', sorted(d for d in os.listdir(OUT)))
