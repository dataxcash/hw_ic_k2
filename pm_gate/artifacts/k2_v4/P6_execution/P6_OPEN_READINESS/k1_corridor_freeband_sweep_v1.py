import sys, json
sys.path.insert(0,"/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core.hs_route_model import HSRouteModel, build_hs_field, spec_frozen_segments
from eda_core.route_input import ModelConfig, ProjectRouteConfig
K1="/home/fila/jqdDev_2025/ic_hw/k1"; DATA="/home/fila/jqdDev_2025/ic_hw"
cfg=ModelConfig.from_dict(ProjectRouteConfig.load(f"{K1}/pm_gate/artifacts/k1/L2/route_model_config.json").hs_config())
m=HSRouteModel(f"{K1}/k1_v1.kicad_pcb", f"{K1}/pm_gate/artifacts/k1/L3/SPEC_k1.json",
               f"{K1}/pm_gate/artifacts/k1/L3/model_solves/channel_alloc/channel_alloc.json",
               f"{DATA}/_shared/eda_core/drc_rules.json", pro_path=f"{K1}/k1_v1.kicad_pro", config=cfg)
def make_field(layer):
    f=build_hs_field(m.board, m.rules, layer=layer, clear_hs_pads=True, config=cfg)
    n=0
    for src in (cfg.frozen_obstacle_sources or []):
        if src.get("yield"): continue
        for (en,ea,eb,el) in spec_frozen_segments(m.spec,[src]):
            if el!=layer or en.startswith(cfg.yield_seg_prefixes): continue
            f.add_seg(en,ea,eb,0.09,el); n+=1
    return f,n
def runs(ys, step=0.05):
    out=[]; 
    for y in ys:
        if out and abs(y-out[-1][1]-step)<1e-6: out[-1][1]=y
        else: out.append([y,y])
    return [[round(a,2),round(b,2),round(b-a+step,2)] for a,b in out]
SPANS={"left":(5.3,38.3125),"right":(41.6875,74.2)}
res={}
for l in ["F.Cu","In1","In2","B.Cu"]:
    f,n=make_field(l)
    res[l]={"frozen_segs":n}
    for sname,(x0,x1) in SPANS.items():
        ys=[round(12.0+i*0.05,4) for i in range(int((27.0-12.0)/0.05)+1)]
        free=[y for y in ys if f.seg_ok("PCIE_TX1_P",(x0,y),(x1,y))]
        res[l][sname]={"n_free":len(free),"free_runs_y_runlen":[a for a in runs(free)]}
print(json.dumps(res,ensure_ascii=False,indent=1))
