# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
import pcbnew, json, re
BOARD='/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb'
C5=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/c5_chip_level_expect_matrix_v28.json'))
BALLMAP=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/ds320pr1601_ballmap.json'))['ballmap']
def ball_signal(name):
    for b in BALLMAP:
        if b['name']==name: return b['signal']
    return None
bd=pcbnew.LoadBoard(BOARD)
u6=[fp for fp in bd.GetFootprints() if fp.GetReference()=='U6'][0]
pads={p.GetNumber():p.GetNetname() for p in u6.Pads()}
eb=C5['expect_ball_by_band']
fails=[]; checks=0
def chk(cond,msg):
    global checks
    checks+=1
    if not cond: fails.append(msg)
# item1: A_PER lane L P/N -> PCIE_DN{L}_{P,N}
for lane in range(8):
    a=eb['A_PER'][str(lane)]
    chk(pads[a['P']]==f'PCIE_DN{lane}_P', f'A_PER L{lane} P {a["P"]} net={pads[a["P"]]}')
    chk(pads[a['N']]==f'PCIE_DN{lane}_N', f'A_PER L{lane} N {a["N"]} net={pads[a["N"]]}')
# item2: B_PET -> PCIE_UP_OUT{lane}_{P,N}_J2
for lane in range(8):
    b=eb['B_PET'][str(lane)]
    chk(pads[b['P']]==f'PCIE_UP_OUT{lane}_P_J2', f'B_PET L{lane} P {b["P"]} net={pads[b["P"]]}')
    chk(pads[b['N']]==f'PCIE_UP_OUT{lane}_N_J2', f'B_PET L{lane} N {b["N"]} net={pads[b["N"]]}')
# item3: A_PET -> PCIE_DN_OUT{lane}_{P,N}_MCIO
for lane in range(8):
    c=eb['A_PET'][str(lane)]
    chk(pads[c['P']]==f'PCIE_DN_OUT{lane}_P_MCIO', f'A_PET L{lane} P {c["P"]} net={pads[c["P"]]}')
    chk(pads[c['N']]==f'PCIE_DN_OUT{lane}_N_MCIO', f'A_PET L{lane} N {c["N"]} net={pads[c["N"]]}')
# item4: B_PER -> PCIE_UP{lane}_{P,N}
for lane in range(8):
    d=eb['B_PER'][str(lane)]
    chk(pads[d['P']]==f'PCIE_UP{lane}_P', f'B_PER L{lane} P {d["P"]} net={pads[d["P"]]}')
    chk(pads[d['N']]==f'PCIE_UP{lane}_N', f'B_PER L{lane} N {d["N"]} net={pads[d["N"]]}')
# item5(REFCLK): no REFCLK on U6
ref=[k for k,v in pads.items() if v.startswith('PCIE_REFCLK')]
chk(len(ref)==0, f'REFCLK balls on U6: {ref}')
# item6: lane-P/N ball exists on both connector and U6 (shared net): sample P of each lane from J2 & J3/J4 pads
def fp_pads(ref):
    for fp in bd.GetFootprints():
        if fp.GetReference()==ref:
            return {p.GetNumber():p.GetNetname() for p in fp.Pads()}
    return {}
j2=fp_pads('J2'); j3=fp_pads('J3'); j4=fp_pads('J4')
# J2 DN lane0..7 P/N + UP_OUT P/N
for lane in range(8):
    for pn in ['P','N']:
        chk(f'PCIE_DN{lane}_{pn}' in set(j2.values()), f'J2 lacks PCIE_DN{lane}_{pn}')
        chk(f'PCIE_UP_OUT{lane}_{pn}_J2' in set(j2.values()), f'J2 lacks PCIE_UP_OUT{lane}_{pn}_J2')
for lane in range(4):
    for pn in ['P','N']:
        chk(f'PCIE_DN_OUT{lane}_{pn}_MCIO' in set(j3.values()), f'J3 lacks DN_OUT{lane}_{pn}')
        chk(f'PCIE_UP{lane}_{pn}' in set(j3.values()), f'J3 lacks UP{lane}_{pn}')
for lane in range(4,8):
    for pn in ['P','N']:
        chk(f'PCIE_DN_OUT{lane}_{pn}_MCIO' in set(j4.values()), f'J4 lacks DN_OUT{lane}_{pn}')
        chk(f'PCIE_UP{lane}_{pn}' in set(j4.values()), f'J4 lacks UP{lane}_{pn}')
# 极性双端一致: 每 lane A_PER P 网 == J2 DN P 网（共享）自动成立 if same name; count connectivity via netcode on both
netcodes={}
for fp in bd.GetFootprints():
    r=fp.GetReference()
    if r in ('J2','J3','J4','U6'):
        for p in fp.Pads():
            netcodes.setdefault(p.GetNetname(), set()).add(r)
# assert diff nets shared between expected ends only
problems=[]
for nm, refs in netcodes.items():
    if nm.startswith('PCIE_DN') and not nm.startswith('PCIE_DN_OUT'):
        if refs!={'J2','U6'}: problems.append((nm,refs))
    if nm.startswith('PCIE_DN_OUT') and nm.endswith('_MCIO'):
        lane=int(re.search(r'DN_OUT(\d+)_',nm).group(1))
        want = {'U6','J3'} if lane<4 else {'U6','J4'}
        if refs!=want: problems.append((nm,refs))
    if nm.startswith('PCIE_UP') and nm.endswith('_J2'):
        if refs!={'J2','U6'}: problems.append((nm,refs))
    if nm.startswith('PCIE_UP') and not nm.endswith('_J2'):
        lane=int(re.search(r'UP(\d+)_',nm).group(1)); want={'U6','J3'} if lane<4 else {'U6','J4'}
        if refs!=want: problems.append((nm,refs))
chk(len(problems)==0, f'net shared-end mismatch: {problems[:6]}')
print(f'C5 CHECK: {checks} assertions, {len(fails)} fails')
for f in fails[:20]: print('  FAIL:', f)
print('RESULT:', 'PASS' if not fails else 'FAIL')
