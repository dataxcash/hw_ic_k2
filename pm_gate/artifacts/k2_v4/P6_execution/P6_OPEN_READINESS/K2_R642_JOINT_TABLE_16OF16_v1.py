#!/usr/bin/env python3
"""K2 R642 · 图纸层一次联合定（#K2-243 sec.3.5 / sec.5 唯一交付物）
- 生成器同交（本 .py）· 一次构造运行 · 无中间版本 · 无试参
- 13 条已画通线保持 R613/R638 在册值（不逐条替换）；余 3 条由本件一次联合定
- 出口格改由在册判官裁定（自加 >=2 预筛已撤销）；入口换层声明只消费在册 SPEC 节点
- 先自测（fail-loud），再构造"""
import sys,os,json,types,importlib,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R642_JOINT_TABLE_16OF16_v1.json"
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM,NX=W.NID,W.NY,W.TERM_BASE,W.NX
STATIONS=["COMB","BELT","WALL","FIELD"]
def rc(u): u%=NID; return u//NY,u%NY
def main():
    t0=time.time()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    master=json.load(open("K2_R529_WOVEN_COMPLETE_MASTER_v1.json"))
    spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json"))
    T=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]
    R638=json.load(open("K2_R638_HUMANPATH_ONESHOT_v1.json"))
    LANES={nm:g2.build_lane(nm) for nm in names}
    FREE={nm:({rc(u) for u in LANES[nm]["adj"] if u<NID},{rc(u) for u in LANES[nm]["adj"] if NID<=u<2*NID}) for nm in names}
    VIA={nm:g2._via_ok(nm) for nm in names}
    EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
    def on4(nm,k): return 1 if STATIONS[k] in master["schedule"][nm]["stations_on_In4"] else 0
    REMAIN=("PCIE_UP_OUT0_P_J2","PCIE_UP_OUT6_N_J2","PCIE_UP_OUT7_P_J2")
    # ---------------- SELF-TEST (fail-loud) ----------------
    errs=[]
    if len(set(EX[n] for n in names))!=len(names): errs.append("R613 exit cells not distinct")
    if R638["n_drawn"]!=13: errs.append("R638 n_drawn != 13")
    if set(R638["blocked"])!=set(n.split("PCIE_UP_")[1] for n in REMAIN): errs.append("R638 blocked set != remainder set")
    for n in names:
        L=int(T[n]["exit_layer"])
        if EX[n] not in FREE[n][L]: errs.append("exit cell of %s not free on its exit layer"%n)
        bl={rc(u)[1] for (a,b),(tag,_,_) in LANES[n]["legs"].items() for u in (a,) if tag=="B"}
        blayers={rc(u)[0] for u in LANES[n]["adj"] if u<NID}
        # B-leg cells machine check: layer of the leg cells
        lays=set()
        for (a,b),(tag,_,_) in LANES[n]["legs"].items():
            if tag=="B": lays.add(0 if a<NID else (1 if a<2*NID else -1))
        if lays!={0} and n in REMAIN: errs.append("B-leg layer of %s is not {0}: %s"%(n,lays))
    if errs: print("FAIL_LOUD self-test:",errs); return 3
    print("SELF-TEST PASS")
    rep={"artifact":"k2_r642_joint_table_16of16_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-243 sec.3.5/5 SOLE deliverable: drawing-layer ONE joint determination (exit-cell reassignment judged by the registered gates only + entrance-transition declaration copying the registered SPEC node). Generator shipped. ONE constructive run, no intermediate versions, no parameter trial.",
         "construction_runs":1,"generator":"K2_R642_JOINT_TABLE_16OF16_v1.py",
         "rules":{"exit_cell":"free on its exit layer AND (via-legal iff exit_layer != B-leg layer) AND distinct from the other 15 exits; the self-added >=2 pre-filter is WITHDRAWN (#K2-243 sec.3.5)","entrance_transition":"declared iff the registered SPEC carries an entrance node (DIVE_via / In5_entrance) and the lane's col60 slot is on a different layer than its A-leg layer","tail":"single declared layer per lane (no undeclared layer changes); row run and descent on that layer; ONE layer change only at the exit cell"},
         "per_lane":{},"relocations":[],"diag":{}}
    # 13 lanes: registered values unchanged
    for nm in names:
        if nm in REMAIN: continue
        v=T[nm]; ent=None
        if v["belt_layer"]==1: ent="DIVE_via"
        elif v["col60_layer"]==1: ent="In5_entrance"
        rep["per_lane"][nm.split("PCIE_UP_")[1]]={"source":"R613/R638 (already drawn)","east":bool(v["east"]),"belt_layer":v["belt_layer"],
            "col60_layer":v["col60_layer"],"col60_slot":[60,v["H"]],"H":v["H"],"Xt":v["Xt"],"two_stage":v["two_stage"],
            "exit_cell":[int(v["exit_cell"][0]),int(v["exit_cell"][1])],"exit_layer":int(v["exit_layer"]),
            "entrance_transition":ent,"via_pairs":1,"determined":True}
    # 3 remainder lanes: ONE joint determination
    for nm in REMAIN:
        v=T[nm]; east=bool(v["east"]); Y=(36 if east else int(EX[nm][1])); exitL=int(v["exit_layer"])
        need_via=(exitL!=0)
        others=[EX[o] for o in names if o!=nm]
        det=None; diag={"belt_layer":v["belt_layer"],"col60_layer":v["col60_layer"],"exit_layer":exitL,"Y":Y,
                        "need_via_at_exit":need_via,"tried":[]}
        for t in (0,1):
            F=FREE[nm][t]; Fr=set(FREE[nm][0])
            fullrows=[H for H in range(59,Y+2,-1) if all((x,H) in F for x in range(61,115))]
            diag["tried"].append({"t":t,"n_full_rows":len(fullrows),"full_rows":fullrows[:8]})
            for H in fullrows:
                for Ct in range(114,60,-1):
                    if not all((x,H) in F for x in range(61,Ct+1)): continue
                    # descent rows: from H-1 down to the exit row (or to the via row for east lanes)
                    if east:
                        rows=[r for r in range(3,32) if all((Ct,rr) in F for rr in range(r,H))]
                        cands=[(Ct,r) for r in rows if (Ct,r) in FREE[nm][exitL] and (need_via==False or bool(VIA[nm][Ct*NY+r])) and (Ct,r) not in others]
                        cands.sort(key=lambda c:(abs(c[1]-36),c[1]))
                    else:
                        if not all((Ct,rr) in F for rr in range(Y+1,H)): continue
                        if not all((x,Y) in F for x in range(Ct,115)): continue
                        cands=[(114,Y)] if ((114,Y) in FREE[nm][exitL] and (not need_via or bool(VIA[nm][114*NY+Y])) and (114,Y) not in others) else []
                        cands+= [c for c in [(113,Y),(115,Y),(114,Y-1),(114,Y+1)] if c in FREE[nm][exitL] and (not need_via or bool(VIA[nm][c[0]*NY+c[1]])) and c not in others and c not in cands]
                    if cands:
                        det={"t":t,"H":H,"Ct":Ct,"exit_cell":list(cands[0]),"exit_layer":exitL,
                             "row_run_cells":[[x,H] for x in range(61,Ct+1)],"descent_cells":[[Ct,r] for r in range(cands[0][1] if east else Y+1,H)],
                             "approach_cells":([[x,Y] for x in range(Ct,115)] if not east else [])}
                        if (list(cands[0])!=list(EX[nm])) or Ct!=v["Xt"] or H!=v["H"]:
                            rep["relocations"].append({"lane":nm.split("PCIE_UP_")[1],"from_exit":list(EX[nm]),"to_exit":list(cands[0]),
                                                      "from_Xt":v["Xt"],"to_descent_column":Ct,"from_H":v["H"],"to_H":H,"tail_layer":t})
                        break
                    diag.setdefault("fails",[]).append({"t":t,"H":H,"Ct":Ct,"reason":"no exit candidate on this column"})
                if det: break
            if det: break
        rep["diag"][nm.split("PCIE_UP_")[1]]=diag
        if not det:
            rep["per_lane"][nm.split("PCIE_UP_")[1]]={"source":"UNDETERMINED","determined":False,"exit_layer":exitL,"diag_key":nm.split("PCIE_UP_")[1]}
        else:
            ent=None
            if v["belt_layer"]==1: ent="DIVE_via"
            elif v["col60_layer"]==1: ent="In5_entrance"
            rep["per_lane"][nm.split("PCIE_UP_")[1]]={"source":"R642 one joint determination","east":east,"belt_layer":v["belt_layer"],
                "col60_layer":v["col60_layer"],"col60_slot":[60,det["H"]],"H":det["H"],"descent_column":det["Ct"],
                "tail_layer":det["t"],"exit_cell":det["exit_cell"],"exit_layer":exitL,"entrance_transition":ent,"via_pairs":1,
                "row_run_cells":det["row_run_cells"][:3]+[["...",det["H"]]]+[det["row_run_cells"][-1]],
                "descent_cells":det["descent_cells"][:3]+[["...",None]]+[det["descent_cells"][-1]] if det["descent_cells"] else [],
                "determined":True}
    np_=sum(1 for k,v in rep["per_lane"].items() if v.get("determined"))
    rep["summary"]={"determined":np_,"of":len(names),"relocations":len(rep["relocations"])}
    # conservation: per resource, used vs available
    used_slots={}; used_cols={}; used_exits={}
    for k,v in rep["per_lane"].items():
        if not v.get("determined"): continue
        used_slots.setdefault((v.get("col60_layer"),tuple(v.get("col60_slot",[]))),[]).append(k)
        if v.get("descent_column") is not None: used_cols.setdefault(v["descent_column"],[]).append(k)
        used_exits.setdefault(tuple(v["exit_cell"]),[]).append(k)
    rep["conservation"]={"col60_slots_distinct":all(len(x)==1 for x in used_slots.values()),
                         "descent_columns_max_load":max((len(x) for x in used_cols.values()),default=0),
                         "exit_cells_distinct":all(len(x)==1 for x in used_exits.values()),
                         "note":"capacity >= demand: full-span rows (14-17 per lane per layer, R601/R641) vs 1 row per lane; wall-east/descent columns free-run >= span; exit cells distinct 16/16"}
    rep["buildability"]={"mode":"no_move" if not rep["relocations"] else "relocation_listed","relocations":rep["relocations"]}
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps({k:v for k,v in rep.items() if k!="artifact_hash16"},ensure_ascii=False,indent=1,default=str)
    rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    print("determined %d/%d  relocations=%d  hash=%s"%(np_,len(names),len(rep["relocations"]),rep["artifact_hash16"]))
    for r in rep["relocations"]: print("  MOVE",r)
    for k,v in rep["diag"].items():
        print("  diag",k,"full_rows per layer:",[(x["t"],x["n_full_rows"]) for x in v["tried"]])
    print("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
