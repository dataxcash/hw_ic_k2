import pcbnew, shutil
SRC='/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb'
for ang in (90.0, 270.0):
    WORK='/tmp/opencode/k2_ang%d.kicad_pcb'%int(ang)
    shutil.copy(SRC, WORK)
    bd = pcbnew.LoadBoard(WORK)
    fp = pcbnew.FootprintLoad('/home/fila/jqdDev_2025/ic_hw/k2/ForgeOS.pretty', 'DS320PR1601')
    fp.SetReference('U6'); fp.SetPosition(pcbnew.VECTOR2I(int(93.8*1e6),int(53.7*1e6)))
    fp.SetOrientationDegrees(ang); bd.Add(fp); pcbnew.SaveBoard(WORK,bd)
    bd2=pcbnew.LoadBoard(WORK)
    f=[x for x in bd2.GetFootprints() if x.GetReference()=='U6'][0]
    pads={p.GetNumber():p for p in f.Pads()}
    CX,CY=93.8,53.7
    print(f'=== angle {ang} ===')
    for ball in ['A1','A35','N2','R1','M26','P29','P10','M7','CB34','CD35']:
        p=pads[ball]; print('  %-5s @(%.2f,%.2f) rel(%.2f,%.2f)'%(ball,p.GetPosition().x/1e6,p.GetPosition().y/1e6,p.GetPosition().x/1e6-CX,p.GetPosition().y/1e6-CY))
    bb=f.GetBoundingBox()
    print('  U6 bbox x[%.2f,%.2f] y[%.2f,%.2f]  envelope x[82.35,105.25] y[49.20,58.20]'%(bb.GetLeft()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6,bb.GetTop()/1e6))
