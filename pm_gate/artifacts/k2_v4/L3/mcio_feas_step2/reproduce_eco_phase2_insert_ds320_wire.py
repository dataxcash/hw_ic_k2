# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
import pcbnew, json
BOARD='/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb'
LIBDIR='/home/fila/jqdDev_2025/ic_hw/k2/ForgeOS.pretty'
BALLMAP=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/ds320pr1601_ballmap.json'))['ballmap']
C5=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/c5_chip_level_expect_matrix_v28.json'))
def ball_signal(name):
    for b in BALLMAP:
        if b['name']==name: return b['signal']
    return None
bd = pcbnew.LoadBoard(BOARD)
fp = pcbnew.FootprintLoad(LIBDIR, 'DS320PR1601')
assert fp is not None, 'fp load fail'
fp.SetReference('U6'); fp.SetValue('DS320PR1601')
fp.SetPosition(pcbnew.VECTOR2I(int(93.8*1e6), int(53.7*1e6)))
fp.SetOrientationDegrees(90.0)
bd.Add(fp)
def net(nm):
    n=bd.GetNetInfo().GetNetItem(nm)
    if n is None: raise SystemExit('NET MISSING: '+nm)
    return n
eb=C5['expect_ball_by_band']
assign={}
for lane in range(8):
    a=eb['A_PER'][str(lane)]; assign[a['P']]=f'PCIE_DN{lane}_P';         assign[a['N']]=f'PCIE_DN{lane}_N'
    b=eb['B_PET'][str(lane)]; assign[b['P']]=f'PCIE_UP_OUT{lane}_P_J2';   assign[b['N']]=f'PCIE_UP_OUT{lane}_N_J2'
    c=eb['A_PET'][str(lane)]; assign[c['P']]=f'PCIE_DN_OUT{lane}_P_MCIO'; assign[c['N']]=f'PCIE_DN_OUT{lane}_N_MCIO'
    d=eb['B_PER'][str(lane)]; assign[d['P']]=f'PCIE_UP{lane}_P';          assign[d['N']]=f'PCIE_UP{lane}_N'
n_sig=n_vcc=n_gnd=n_other=0; unwired=[]
for p in fp.Pads():
    ball=p.GetNumber(); sig=ball_signal(ball)
    if ball in assign: p.SetNet(net(assign[ball])); n_sig+=1
    elif sig=='GND': p.SetNet(net('GND')); n_gnd+=1
    elif sig and sig.startswith('VCC'): p.SetNet(net('P3V3')); n_vcc+=1
    else: unwired.append((ball,sig)); n_other+=1
print(f'wired sig={n_sig} vcc={n_vcc} gnd={n_gnd} other={n_other}')
# board outline y33->79
chg=0
for d in bd.GetDrawings():
    if d.GetLayerName()!='Edge.Cuts': continue
    s,e=d.GetStart(),d.GetEnd()
    sx,sy,ex,ey=s.x/1e6,s.y/1e6,e.x/1e6,e.y/1e6
    nsx,nsy,nex,ney=sx,sy,ex,ey
    if abs(sy-71)<0.01 and abs(ey-71)<0.01: nsy=ney=79.0
    if abs(sx-23)<0.01 and abs(ex-23)<0.01 and abs(ey-71)<0.01: ney=79.0
    if abs(sx-143)<0.01 and abs(ex-143)<0.01 and abs(ey-71)<0.01: ney=79.0
    d.SetStart(pcbnew.VECTOR2I(int(nsx*1e6),int(nsy*1e6)))
    d.SetEnd(pcbnew.VECTOR2I(int(nex*1e6),int(ney*1e6)))
    chg+=1
print('edge updated:', chg)
print('copper layers:', bd.GetCopperLayerCount(), '->', end=' ')
bd.SetCopperLayerCount(6)
print(bd.GetCopperLayerCount())
ok=pcbnew.SaveBoard(BOARD, bd)
print('saved:', ok)
