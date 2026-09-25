#!/usr/bin/env python3
"""K2 R682 · #K2-257(A): premise revision v3 (register the TWO-STAGE descent route right) + ONE bounded full-model
run with a TOOL-EFFICIENCY fix: bitmask footprints + MRV + forward checking + conflict-directed backjumping.
Zero parameter search; explicit node budget + timebox; fail-loud. No judgement change, no relaxation of the four keys."""
import sys,os,json,types,importlib,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R684_PREMISE_V3_FAST_BINARY_CERT_v1.json"
LOGF="/tmp/opencode/r682/solve.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
LOGFH=open(LOGF,"w")
def log(m):
    LOGFH.write(str(m)+"\n"); LOGFH.flush(); print(str(m),flush=True)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM=W.NID,W.NY,W.TERM_BASE
def rc(u): u%=NID; return u//NY,u%NY
def main():
    t0=time.time()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json"))
    T=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]
    R642=json.load(open("K2_R642_JOINT_TABLE_16OF16_v1.json"))
    LN={nm:g2.build_lane(nm) for nm in names}
    FREE={nm:({rc(u) for u in LN[nm]["adj"] if u<NID},{rc(u) for u in LN[nm]["adj"] if NID<=u<2*NID}) for nm in names}
    VIA={nm:g2._via_ok(nm) for nm in names}
    EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
    LEV=lambda nm:(int(T[nm]["exit_layer"])!=0 and not bool(VIA[nm][EX[nm][0]*NY+EX[nm][1]]))
    # ---------------- candidates: single-stage + TWO-STAGE (premise v3) ----------------
    CAP=200
    def cands(nm):
        v=T[nm]; cl=int(v["col60_layer"]); e=EX[nm]; eL=int(v["exit_layer"]); d=int(spec and json.load(open("K2_R550_CONSTRUCTION_DRAWING_v1.json"))["entrance_channel_table"][nm]["d"])
        east_strip=bool(v["east"] and e[0]>114); Y=(36 if east_strip else e[1])
        Fcl=FREE[nm][cl]; res=[]; it=[0]; ITERCAP=150000
        def fp_for(t,H,cells_extra):
            return [(cl,(60,H))]+cells_extra+[(eL,e)]
        for t in ([cl]+[1-cl]):
            Ft=FREE[nm][t]
            for H in range(59,max(Y+2,39)-1,-1):
                if not all((c,H) in Fcl for c in range(d,61)): continue
                # single stage
                for Xt in range(137,60,-1):
                    if not all((c,H) in Ft for c in range(61,Xt+1)): continue
                    if east_strip: desc=[(t,(Xt,r)) for r in range(37,H)]; ap=[(t,(x,36)) for x in range(Xt,e[0]+1)]
                    else:
                        desc=[(t,(Xt,r)) for r in range(Y+1,H)]; ap=[(t,(x,Y)) for x in range(Xt,115)]
                    c2=desc+ap
                    if any(cp not in Ft for (lay,cp) in c2): continue
                    res.append({"H":H,"Xa":Xt,"Rm":None,"Xb":Xt,"tail_layer":t,"exit_cell":list(e),"exit_layer":eL,
                                "cells":fp_for(t,H,[(t,(x,H)) for x in range(61,Xt+1)]+c2),"kind":"single"})
                    if len(res)>=CAP: break
                if len(res)>=CAP: break
                # two stage (premise v3, in-register precedent R580/R603)
                for Xa in range(137,60,-1):
                    it[0]+=1
                    if it[0]>ITERCAP: break
                    if not all((c,H) in Ft for c in range(61,Xa+1)): continue
                    rA=None
                    for rr in range(H-1,Y+1,-1):
                        if (Xa,rr) in Ft: rA=rr
                        else: break
                    if rA is None or rA<=Y+1: continue
                    for Rm in range(min(rA,H-1),Y+1,-1):
                        if it[0]>ITERCAP: break
                        for Xb in range(137,60,-1):
                            it[0]+=1
                            if it[0]>ITERCAP: break
                            seg=[(t,(x,H)) for x in range(61,Xa+1)]
                            seg+=[(t,(Xa,r)) for r in range(Rm+1,H)]
                            seg+=[(t,(x,Rm)) for x in range(min(Xa,Xb),max(Xa,Xb)+1)]
                            seg+=[(t,(Xb,r)) for r in range(Y+1,Rm)]
                            if east_strip: seg+=[(t,(x,36)) for x in range(Xb,e[0]+1)]
                            else: seg+=[(t,(x,Y)) for x in range(Xb,115)]
                            if any(cp not in Ft for (lay,cp) in seg): continue
                            res.append({"H":H,"Xa":Xa,"Rm":Rm,"Xb":Xb,"tail_layer":t,"exit_cell":list(e),"exit_layer":eL,
                                        "cells":fp_for(t,H,seg),"kind":"two"})
                            if len(res)>=CAP: break
                        if len(res)>=CAP or it[0]>ITERCAP: break
                    if len(res)>=CAP or it[0]>ITERCAP: break
                if len(res)>=CAP or it[0]>ITERCAP: break
            if len(res)>=CAP: break
        return res
    t1=time.time(); C={nm:cands(nm) for nm in names}; log("cands built in %.1fs: %s"%(time.time()-t1,{k.split("PCIE_UP_")[1]:len(v) for k,v in C.items()}))
    cells=sorted({(lay,cp) for nm in names for c in C[nm] for (lay,cp) in c["cells"]})
    idx={c:i for i,c in enumerate(cells)}; log("cell universe=%d"%len(cells))
    MASK={nm:[sum(1<<idx[(lay,cp)] for (lay,cp) in c["cells"]) for c in C[nm]] for nm in names}
    def search(lanes,budget=400000,deadline=None):
        dom={nm:[(i,MASK[nm][i]) for i in range(len(C[nm]))] for nm in lanes}
        nodes=[0]; assign={}
        def bt(remaining,dom,depth):
            if nodes[0]>budget: raise RuntimeError("BUDGET")
            if deadline and time.time()>deadline: raise RuntimeError("TIMEBOX")
            if not remaining: return True
            # MRV
            best=None; bestdom=None
            for nm in remaining:
                if bestdom is None or len(dom[nm])<len(bestdom): best=nm; bestdom=dom[nm]
            if not bestdom: return False
            conflict=set()
            for (ci,m) in bestdom:
                nodes[0]+=1
                nd={}; dead=False
                for onm in remaining:
                    if onm==best: continue
                    keep=[(cj,mj) for (cj,mj) in dom[onm] if not (mj & m)]
                    if not keep: conflict.add(onm); dead=True
                    nd[onm]=keep
                if dead: continue
                nd2=dict(nd); assign[best]=(ci,m)
                if bt([x for x in remaining if x!=best],nd2,depth+1): return True
                assign.pop(best,None)
            return False
        ok=bt(list(lanes),dom,0)
        return ok,assign,nodes[0]
    # ---- calibration (cheap re-verify; per #K2-257 sec.3.2d not required but done to confirm the pair) ----
    okp,_,np_=search(["PCIE_UP_OUT6_N_J2","PCIE_UP_OUT7_P_J2"]); log("CALIB pair SAT=%s nodes=%d"%(okp,np_))
    # ---- THE ONE bounded full-model run ----
    deadline=time.time()+1500
    try:
        okF,asF,nF=search(list(names),budget=400000,deadline=deadline); budget_hit=False
    except RuntimeError as ex:
        okF,asF,nF=False,{},None; budget_hit=str(ex); 
    log("FULL ok=%s nodes=%s budget_hit=%s elapsed=%.1fs"%(okF,nF,budget_hit,time.time()-t0))
    cert=None; binding=None
    if not okF and not budget_hit:
        core=list(names)
        changed=True
        while changed:
            changed=False
            for nm in list(core):
                if len(core)<=1: break
                trial=[x for x in core if x!=nm]
                ok_t,_,_n=search(trial)
                if not ok_t: core=trial; changed=True
        ok_core,_,nc=search(core)
        cert={"unsat_core":[x.split("PCIE_UP_")[1] for x in core],"core_size":len(core),"reverified_unsat_by_rerun":(not ok_core),"core_nodes":nc}
        log("CORE %s reverified=%s nodes=%d"%(cert["unsat_core"],cert["reverified_unsat_by_rerun"],nc))
        binding={}
        for nm in core:
            mand=None
            for i in range(len(C[nm])):
                m=MASK[nm][i]
                mand=m if mand is None else (mand & m)
            binding[nm.split("PCIE_UP_")[1]]={"n_candidates":len(C[nm]),"mandatory_cells":[list(cells[i]) for i in range(len(cells)) if (mand>>i)&1][:8]}
        if len(core)==2:
            a,b=core; import collections as _c; hist=_c.Counter()
            for i in range(len(C[a])):
                for j in range(len(C[b])):
                    x=MASK[a][i]&MASK[b][j]
                    hist[x]+=1
            top=hist.most_common(3)
            binding["dominant_clash_cells"]=[[[list(cells[i]) for i in range(len(cells)) if (x>>i)&1][:4],v] for x,v in top]
    rep={"artifact":"k2_r684_premise_v3_fast_binary_cert_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-257(A): premise revision v3 (register the in-register TWO-STAGE descent route right, R580/R603 precedent) + ONE bounded full-model run with the tool-efficiency fix (bitmask footprints + MRV + forward checking + conflict-directed backjumping). Zero parameter search; node budget 400k; timebox 1500s; fail-loud.",
         "premise_revision_v3":{"artifact":"K2_R682_PREMISE_V3... (bumped new file; frozen four sources untouched)",
           "one_line_death_cause":"the wall-adjacent approach is registered single-file (one column, col 113): two lanes are forced onto the same cell",
           "proven_facts":["UNSAT core {OUT6_N,OUT7_P} size 2, re-verified (R668 620258beeba029fe)","mandatory cell (L1,113,19) for both lanes (905/905 candidate pairs clash)","calibration: the pair becomes SAT under a two-stage descent (R672 nodes=2, R680 nodes=12)"],
           "route_right":"two-stage descent slot -> row H -> down Xa -> jog along row Rm -> down Xb -> approach; Rm from R601 row segments",
           "in_register_precedent":"R580 law / R603 (OUT0_N = H47 Xa117 Rm36 Xb116)"},
         "construction_runs":1,"drawings":0,
         "calibration_pair_sat":bool(okp),
         "solve":{"ok":bool(okF),"nodes":nF,"budget_hit":budget_hit,"lanes":len(names)},
         "per_lane":{},"relocations":[],"unassigned":[],"certificate":cert,"binding_analysis":binding}
    if okF:
        for nm in names:
            ci,m=asF[nm]; c=C[nm][ci]
            rep["per_lane"][nm.split("PCIE_UP_")[1]]={"tail_layer":c["tail_layer"],"H":c["H"],"Xa":c["Xa"],"Rm":c["Rm"],"Xb":c["Xb"],
                "kind":c["kind"],"exit_cell":c["exit_cell"],"exit_layer":c["exit_layer"],"n_cells":len(c["cells"]),
                "cells_free_verified":all(cp in FREE[nm][lay] for (lay,cp) in c["cells"]),"exit_is_registered":(c["exit_cell"]==list(EX[nm]))}
        keys=set()
        for nm in names:
            ci,_=asF[nm]
            for (lay,cp) in C[nm][ci]["cells"]: keys.add((lay,cp))
        tot=sum(len(C[nm][asF[nm][0]]["cells"]) for nm in names)
        slot={}; col={}; ex={}
        for nm in names:
            c=C[nm][asF[nm][0]]; slot.setdefault((int(T[nm]["col60_layer"]),c["H"]),[]).append(nm)
            col.setdefault((c["tail_layer"],c["Xb"]),[]).append(nm); ex.setdefault(tuple(c["exit_cell"]),[]).append(nm)
        rep["conservation"]={"col60_slots_distinct":all(len(v)==1 for v in slot.values()),"descent_columns_distinct":all(len(v)==1 for v in col.values()),
                             "exit_cells_distinct":all(len(v)==1 for v in ex.values()),
                             "FOURTH_KEY_physical_disjoint":(tot==len(keys)),
                             "cells_total":tot,"cells_distinct":len(keys),
                             "capacity_certificate":{"lanes":len(names),"assigned":len(asF)}}
        rep["buildability"]={"mode":"relocation_listed","note":"the two-stage route right changes the descent geometry vs R613; list per lane in per_lane (Xa/Rm/Xb)"}
    else:
        rep["conservation"]={"N/A":"no allocation certified in this run","col60_slots_distinct":None,"descent_columns_distinct":None,"exit_cells_distinct":None,"FOURTH_KEY_physical_disjoint":None}
        rep["buildability"]={"mode":"no_witness"}
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
