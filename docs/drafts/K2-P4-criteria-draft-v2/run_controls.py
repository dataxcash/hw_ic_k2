import json, os, shutil, subprocess, sys
CWD='/home/fila/jqdDev_2025/ic_hw'; D='/tmp/opencode/criteria-draft'
AD=['python3', os.path.join(D,'adjudicate.py')]
PROBE='/tmp/opencode/c86-6/_cand_31p55_58p85_off775_d1_s0.kicad_pro'   # 9 条 ignore→warning
LANDED='k2/hw/k2_v4_8L.l5.kicad_pcb'; LPRO='k2/hw/k2_v4_8L.l5.kicad_pro'

# 负控板：X99（非机械件多余位号）
xb=os.path.join(D,'neg-refdes.kicad_pcb')
if not os.path.exists(xb):
    subprocess.run(['AppDir/usr/bin/python3.11','-c',
      "import pcbnew;b=pcbnew.LoadBoard('%s');f=b.GetFootprints()[0];f.SetReference('X99');pcbnew.SaveBoard('%s',b)"%(os.path.join(CWD,LANDED),xb)],check=True)
    shutil.copy2(os.path.join(CWD,PROBE), os.path.join(D,'neg-refdes.kicad_pro'))
# 负控 pro：missing_courtyard→error
po=os.path.join(D,'neg-drc.kicad_pro')
if not os.path.exists(po):
    d=json.load(open(os.path.join(CWD,LPRO))); d['board']['design_settings']['rule_severities']['missing_courtyard']='error'
    json.dump(d,open(po,'w'),indent=2)

def run(tag, board, pro, root, man=None, wd=None):
    man=man or os.path.join(D,'manifest.k2.yaml'); out=os.path.join(D,'v-%s.json'%tag)
    cmd=AD+['--project','k2','--manifest',man,'--board',board,'--pro',pro,
            '--nets','k2/hw/data/k2_sch.yaml','--sch-dir','k2/hw/sch','--root',root,
            '--drc-cli','AppDir/bin/kicad-cli','--drc-work-dir',wd or os.path.join(D,'drc'),'--out',out]
    r=subprocess.run(cmd,capture_output=True,text=True,cwd=CWD)
    if not os.path.exists(out): return tag,'NO-VERDICT',r.stdout[-200:]+r.stderr[-200:],[]
    v=json.load(open(out)); det={x['check']:x for x in v['oks']+v['fails']}
    return tag,'%dP/%dF'%(v['n_pass'],v['n_fail']),'',det

CASES=[
 ('POS-main',      LANDED,             LPRO,      '.', None, None),
 ('POS-pipe-k2scope', LANDED,          LPRO,      os.path.join(D,'root-pos'), None, None),
 ('NEG-pipe-nok2yaml', LANDED,         LPRO,      os.path.join(D,'root-neg'), None, None),
 ('NEG-zone-l4',   'k2/hw/k2_v4_8L.l4.kicad_pcb', LPRO, '.', None, None),
 ('NEG-refdes-X99',xb,                 os.path.join(D,'neg-refdes.kicad_pro'), '.', None, None),
 ('NEG-drc-errors',LANDED,             po,        '.', None, None),
 ('NEG-warn-empty',LANDED,             LPRO,      '.', os.path.join(D,'manifest-nowarn.yaml'), None),
]
KEY=['zone_filled','drill_count','refdes_sets_equal','pipeline_present','drc_errors','drc_warning_dispositions','unconnected_zero','fp_lib_table_present','keepout_active']
for tag,b,p,root,man,wd in CASES:
    t,res,err,det=run(tag,b,p,root,man,wd)
    print('== %-18s %s %s'%(t,res,err[:120]))
    for k in KEY:
        if k in det: print('     %-24s %s | %s'%(k,'OK ' if det[k]['ok'] else 'FAIL',det[k]['detail'][:120]))
