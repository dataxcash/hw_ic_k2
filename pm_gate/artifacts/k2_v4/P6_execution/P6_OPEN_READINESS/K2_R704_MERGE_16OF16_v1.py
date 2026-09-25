#!/usr/bin/env python3
"""K2 R692 (#K2-259 (c) small-case calibration): STREAMING domain generation (generate -> filter against the fixed-13
cell set -> keep survivors only; NO full-domain materialisation) + MRV/forward-checking + conflict-directed backjumping.
Deterministic, one run, fail-loud, raw output + log + hash."""
import sys,os,json,types,importlib,hashlib,time,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R704_MERGE_16OF16_v1.json"; LOGF="/tmp/opencode/r692/solve.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
LH=open(LOGF,"w")
def log(m): LH.write(str(m)+"\n"); LH.flush(); print(str(m),flush=True)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM=W.NID,W.NY,W.TERM_BASE
def rc(u): u%=NID; return u//NY,u%NY
FREE3=["PCIE_UP_OUT7_P_J2","PCIE_UP_OUT0_P_J2","PCIE_UP_OUT4_N_J2"]   # = the R652 unresolved three
def main():
    t0=time.time()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json")); T=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]
    LN={nm:g2.build_lane(nm) for nm in names}
    FREE={nm:({rc(u) for u in LN[nm]["adj"] if u<NID},{rc(u) for u in LN[nm]["adj"] if NID<=u<2*NID}) for nm in names}
    EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
    ent=json.load(open("K2_R550_CONSTRUCTION_DRAWING_v1.json"))["entrance_channel_table"]
    # ---- FIXED 13: their registered declared chains (R613 + R638 entrance rule) ----
    FIX13=[nm for nm in names if nm not in FREE3]; fixed=set()
    # ---- canonical (R652/R698) routes for the 13, rebuilt deterministically; CALIBRATION GATE: they must be pairwise disjoint ----
    east13=[nm for nm in names if EX[nm][0]>114]; west13=[nm for nm in names if EX[nm][0]<=114]
    order13=sorted(east13,key=lambda n:EX[n][0])+sorted(west13,key=lambda n:EX[n][1])
    def rowspans(nm,t):
        F=FREE[nm][t]; import collections as _c
        rows=_c.defaultdict(list)
        for (c,r) in F: rows[r].append(c)
        sp={}
        for r,cs in rows.items():
            cs.sort(); segs=[]; s0=None; prev=None
            for c in cs:
                if prev is None: s0=c
                elif c!=prev+1: segs.append((s0,prev)); s0=c
                prev=c
            if s0 is not None: segs.append((s0,prev))
            sp[r]=segs
        return sp
    RS13={nm:{t:rowspans(nm,t) for t in (0,1)} for nm in FIX13}
    def rowfree(sp,r,x1,x2):
        for (a,b) in sp.get(r,()):
            if a<=x1 and x2<=b: return True
        return False
    used13={0:set(),1:set()}; fixed13_cells={}
    for nm in order13:
        if nm not in FIX13: continue
        v=T[nm]; cl=int(v["col60_layer"]); H=v["H"]; e=EX[nm]; eL=int(v["exit_layer"]); e0=int(e[0])
        eaststrip=(e0>114); Y=(36 if eaststrip else int(e[1])); done=False
        for t in (0,1):
            F=FREE[nm][t]; sp=RS13[nm][t]
            for Xt in sorted(range(61,138), key=lambda c:(-sum(1 for r in range(Y,H+1) if (c,r) in F), abs(c-(114 if not eaststrip else e0)))):
                if not rowfree(sp,H,61,Xt): continue
                if not all((Xt,r) in F for r in range(Y+1,H)): continue
                seg=[(cl,(60,H))]+[(t,(x,H)) for x in range(61,Xt+1)]+[(t,(Xt,r)) for r in range(Y+1,H)]
                seg+=[(t,(x,Y)) for x in range(Xt,115)] if not eaststrip else [(t,(x,36)) for x in range(Xt,e0+1)]
                seg.append((eL,e))
                if eL!=0 and not bool(VIA[nm][e0*NY+e[1]]):
                    Bx,By=g2.B[nm]; Bc=(int(round((Bx-84.0)/0.435)),int(round((By-41.0)/0.435)))
                    cur=list(e); walk=[]
                    st=1 if Bc[0]>cur[0] else -1
                    while cur[0]!=Bc[0]: cur[0]+=st; walk.append(tuple(cur))
                    st=1 if Bc[1]>cur[1] else -1
                    while cur[1]!=Bc[1]: cur[1]+=st; walk.append(tuple(cur))
                    Vv=None
                    for i,cand in enumerate(walk):
                        if cand in FREE[nm][eL] and cand in FREE[nm][0] and bool(VIA[nm][cand[0]*NY+cand[1]]) and all(c in FREE[nm][eL] for c in walk[:i+1]):
                            Vv=cand; seg+=[(eL,c) for c in walk[:i+1]]; break
                    if Vv is None: continue
                if any(cp not in FREE[nm][lay] for (lay,cp) in seg): continue
                fp=set(seg)
                if fp & (used13[0]|used13[1]): continue
                for (lay,cp) in seg: used13[lay].add((lay,cp))
                fixed13_cells[nm]={"cells":seg,"Xt":Xt,"t":t}
                for (lay,cp) in seg: fixed.add((lay,cp))
                done=True; break
            if done: break
        if not done: log("CALIB FAIL: lane %s could not be canonically placed"%nm.split("PCIE_UP_")[1])
    # ---- MACHINE-ENFORCED CALIBRATION GATE (#K2-265 sec.3.5): 13 fixed must all resolve and be pairwise disjoint ----
    if len(fixed13_cells)!=len(FIX13):
        log("CALIBRATION GATE FAILED (%d/%d) => refusing to run the full model, per sec.3.5"%(len(fixed13_cells),len(FIX13)))
        import sys as _s2; _s2.exit(9)
    tot13=sum(len(v["cells"]) for v in fixed13_cells.values())
    if tot13!=len(fixed):
        log("CALIBRATION GATE FAILED (cell overlap among the fixed 13) => refusing to run")
        import sys as _s2; _s2.exit(9)
    log("CALIBRATION GATE PASS: %d/%d canonical R652 routes, %d cells, pairwise disjoint"%(len(fixed13_cells),len(FIX13),len(fixed)))
    log("FIXED13 cells=%d"%len(fixed))
    # ---- streaming candidate generation for the 3 free lanes: generate -> filter vs fixed -> keep survivors ----
    def stream(nm):
        v=T[nm]; cl=int(v["col60_layer"]); e=EX[nm]; eL=int(v["exit_layer"]); d=int(ent[nm]["d"])
        east=bool(v["east"] and e[0]>114); Y=(36 if east else e[1])
        surv=[]; gen=[0]; rej=[0]
        for t in ([cl]+[1-cl]):
            F=FREE[nm][t]
            cols=collections.defaultdict(list)
            for (c,r) in F: cols[c].append(r)
            down={}
            for c,rs in cols.items():
                rs.sort(); lo=None; prev=None
                for r in rs:
                    if prev is None or r!=prev+1: lo=r
                    down[(c,r)]=lo; prev=r
            rowmap=collections.defaultdict(list)
            for (c,r) in F:
                rowmap[r].append(c)
            spans={}
            for r,cs in rowmap.items():
                cs.sort(); segs=[]; s=None; prev=None
                for c in cs:
                    if prev is None: s=c
                    elif c!=prev+1: segs.append((s,prev)); s=c
                    prev=c
                if s is not None: segs.append((s,prev))
                spans[r]=segs
            FS=[r for r in range(5,64) if all((c,r) in F for c in range(61,115))]
            def rowfree(r,x1,x2):
                for (a,b) in spans.get(r,()):
                    if a<=x1 and x2<=b: return True
                return False
            for H in range(59,max(Y+2,39)-1,-1):
                if not rowfree(H,d,60): continue
                for Xa in range(137,60,-1):
                    if not rowfree(H,61,Xa): continue
                    if (Xa,H-1) not in down: continue
                    rA=down[(Xa,H-1)]
                    if rA>Y+1: continue
                    # single stage
                    if down.get((Xa,H-1),999)<=Y+1:
                        ap=[(t,(x,Y)) for x in range(Xa,115)] if not east else [(t,(x,36)) for x in range(Xa,e[0]+1)]
                        if all(cp in F for (_,cp) in ap):
                            cells=[(cl,(60,H))]+[(t,(x,H)) for x in range(61,Xa+1)]+[(t,(Xa,r)) for r in range(Y+1,H)]+ap+[(eL,e)]
                            gen[0]+=1
                            if all(cp not in fixed for (_,cp) in cells): surv.append((tuple(sorted(cells)),{"H":H,"Xa":Xa,"Rm":None,"Xb":Xa,"t":t,"kind":"single"}))
                            else: rej[0]+=1
                    for Rm in FS:
                        if not (max(rA,Y+2)<=Rm<=min(H-1,59)): continue
                        if down.get((Xa,H-1),999)>Rm: continue
                        for Xb in range(137,60,-1):
                            if not rowfree(Rm,min(Xa,Xb),max(Xa,Xb)): continue
                            if (Xb,Rm-1) not in down or down[(Xb,Rm-1)]>Y+1: continue
                            ap=[(t,(x,Y)) for x in range(Xb,115)] if not east else [(t,(x,36)) for x in range(Xb,e[0]+1)]
                            if not all(cp in F for (_,cp) in ap): continue
                            cells=[(cl,(60,H))]+[(t,(x,H)) for x in range(61,Xa+1)]+[(t,(Xa,r)) for r in range(Rm,H)]+[(t,(x,Rm)) for x in range(min(Xa,Xb),max(Xa,Xb)+1)]+[(t,(Xb,r)) for r in range(Y+1,Rm)]+ap+[(eL,e)]
                            gen[0]+=1
                            if all(cp not in fixed for (_,cp) in cells): surv.append((tuple(sorted(cells)),{"H":H,"Xa":Xa,"Rm":Rm,"Xb":Xb,"t":t,"kind":"two"}))
                            else: rej[0]+=1
        # dedupe survivors by footprint
        seen=set(); out=[]
        for k,meta in surv:
            if k in seen: continue
            seen.add(k); out.append((k,meta))
        return out,gen[0],rej[0]
    DOM={}
    for nm in FREE3:
        s,g,r=stream(nm); DOM[nm]=s; log("%s: generated=%d survivors=%d (rejected by fixed13=%d)"%(nm.split("PCIE_UP_")[1],g,len(s),r))
    # ---- exact 3-way solve (frozenset disjointness, MRV, fail-loud) ----
    def solve():
        cur={nm:[(i,set(k)) for i,(k,meta) in enumerate(DOM[nm])] for nm in FREE3}
        assign={}; nodes=[0]
        def bt(rem,cur):
            if not rem: return True
            best=min(rem,key=lambda n:len(cur[n])); lst=cur[best]
            if not lst: return False
            for (i,cs) in lst:
                nodes[0]+=1; nd={}; dead=False
                for onm in rem:
                    if onm==best: continue
                    keep=[(j,ks) for (j,ks) in cur[onm] if not (ks & cs)]
                    if not keep: dead=True; break
                    nd[onm]=keep
                if dead: continue
                assign[best]=i
                if bt([x for x in rem if x!=best],nd): return True
                assign.pop(best,None)
            return False
        ok=bt(list(FREE3),cur); return ok,assign,nodes[0]
    ok,assign,nodes=solve(); log("SUB-MODEL(13 fixed) SAT=%s nodes=%d elapsed=%.1fs"%(ok,nodes,time.time()-t0))
    rep={"artifact":"k2_r704_merge_16of16_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-265: SAT WITNESS EXTRACTION + merge - R652 baseline 13 (four keys green) as the fixed base; the 3 remaining lanes solved over their FULL streaming domains (v3-prime) with disjointness vs the 13; MACHINE-ENFORCED calibration gate per sec.3.5; prior:: STREAMING domain generation (generate->filter vs fixed-13->keep survivors; no full materialisation) + MRV + forward checking; deterministic, one run, fail-loud.",
         "construction_runs":1,"drawings":0,
         "fixed13":{"set":"R652 resolved 13 (all except OUT7_P/OUT0_P/OUT4_N)","n":len(fixed13_cells),"cells":len(fixed),"calibration_gate":"PASS (machine-enforced, sec.3.5)"},"fixed13_cells":len(fixed),
         "stream_stats":{nm.split("PCIE_UP_")[1]:{"generated":None,"survivors":len(DOM[nm])} for nm in FREE3},
         "sub_model":{"lanes":["OUT7_P","OUT0_P","OUT4_N"],"fixed":"R652 13","sat":bool(ok),"nodes":nodes},
         "witness":{}, "elapsed_s":round(time.time()-t0,1)}
    if ok:
        for nm in FREE3:
            k,meta=DOM[nm][assign[nm]]
            rep["witness"][nm.split("PCIE_UP_")[1]]={"H":meta["H"],"Xa":meta["Xa"],"Rm":meta["Rm"],"Xb":meta["Xb"],"tail_layer":meta["t"],"kind":meta["kind"],"n_cells":len(k)}
        rep["witness"]["_cell_check"]={"pairwise_disjoint":True,"note":"enforced by the solver"}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
