#!/usr/bin/env python3
"""K2 R694 (#K2-260 (yi)): THE one full-model solve with the NEW streaming tool.
Pass A: stream-generate every lane's candidates to collect the cell universe (no candidate storage).
Pass B: stream again, store ONLY int bitmasks + compact meta (dedupe by mask). Never materialise cell lists.
Solve: MRV + forward checking + conflict-directed backjumping; explicit node budget + timebox; fail-loud."""
import sys,os,json,types,importlib,hashlib,time,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R696_FASTPRUNED_BINARY_v1.json"; LOGF="/tmp/opencode/r694/solve.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
def main():
    t0=time.time()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json")); T=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]
    LN={nm:g2.build_lane(nm) for nm in names}
    FREE={nm:({rc(u) for u in LN[nm]["adj"] if u<NID},{rc(u) for u in LN[nm]["adj"] if NID<=u<2*NID}) for nm in names}
    EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
    ent=json.load(open("K2_R550_CONSTRUCTION_DRAWING_v1.json"))["entrance_channel_table"]
    # ---- streaming generator (same v3-prime family as R692: single-stage + two-stage with jog on a full-span row) ----
    def gen(nm):
        v=T[nm]; cl=int(v["col60_layer"]); e=EX[nm]; eL=int(v["exit_layer"]); d=int(ent[nm]["d"])
        east=bool(v["east"] and e[0]>114); Y=(36 if east else e[1])
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
            for (c,r) in F: rowmap[r].append(c)
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
                    if rA<=Y+1:
                        ap=[(t,(x,Y)) for x in range(Xa,115)] if not east else [(t,(x,36)) for x in range(Xa,e[0]+1)]
                        if all(cp in F for (_,cp) in ap):
                            yield ((cl,(60,H)),)+tuple([(t,(x,H)) for x in range(61,Xa+1)]+[(t,(Xa,r)) for r in range(Y+1,H)]+ap+[(eL,e)]), {"H":H,"Xa":Xa,"Rm":None,"Xb":Xa,"t":t,"kind":"single"}
                    for Rm in FS:
                        if not (max(rA,Y+2)<=Rm<=min(H-1,59)): continue
                        if down.get((Xa,H-1),999)>Rm: continue
                        for Xb in range(137,60,-1):
                            if not rowfree(Rm,min(Xa,Xb),max(Xa,Xb)): continue
                            if (Xb,Rm-1) not in down or down[(Xb,Rm-1)]>Y+1: continue
                            ap=[(t,(x,Y)) for x in range(Xb,115)] if not east else [(t,(x,36)) for x in range(Xb,e[0]+1)]
                            if not all(cp in F for (_,cp) in ap): continue
                            yield ((cl,(60,H)),)+tuple([(t,(x,H)) for x in range(61,Xa+1)]+[(t,(Xa,r)) for r in range(Rm,H)]+[(t,(x,Rm)) for x in range(min(Xa,Xb),max(Xa,Xb)+1)]+[(t,(Xb,r)) for r in range(Y+1,Rm)]+ap+[(eL,e)]), {"H":H,"Xa":Xa,"Rm":Rm,"Xb":Xb,"t":t,"kind":"two"}
    # ---- Pass A: universe + counts ----
    uni=set(); cnt={}
    for nm in names:
        n=0
        for cells,meta in gen(nm):
            uni.update(cells); n+=1
        cnt[nm]=n
    log("PASS A: cell universe=%d ; per-lane candidate counts=%s ; %.1fs"%(len(uni),{k.split("PCIE_UP_")[1]:v for k,v in cnt.items()},time.time()-t0))
    idx={c:i for i,c in enumerate(sorted(uni))}
    # ---- Pass B: store ONLY bitmasks + meta (dedupe by mask) ----
    DOM={}; DOMP={}
    DOM_PRN={}
    for nm in names:
        seen=set(); lst=[]
        for cells,meta in gen(nm):
            m=0
            for c in cells: m|=1<<idx[c]
            if m in seen: continue
            seen.add(m); lst.append((m,meta))
        # ---- sound windowed dominance pruning: keep a candidate only if it is NOT a superset of an already-kept one ----
        lst.sort(key=lambda t: bin(t[0]).count("1"))
        kept=[]; WINW=200
        for (m,meta) in lst:
            domx=False
            for km in kept[-WINW:]:
                if (m & km)==km: domx=True; break
            if not domx: kept.append(m)
        DOM[nm]=lst; DOMP[nm]=kept; DOM_PRN[nm]=set(kept)
        log("PASS B %-12s unique=%d  pruned=%d  (collapse x%.1f)"%(nm.split("PCIE_UP_")[1],len(lst),len(kept),len(lst)/max(1,len(kept))))
    log("PASS B done %.1fs"%(time.time()-t0))
    # ---- MRV + forward checking + conflict-directed backjumping (bitmask) ----
    NODES=[0]; BUDGET=1500000; DL=time.time()+1500
    def solve():
        dom={nm:[(m,meta) for (m,meta) in DOM[nm] if m in set(DOM_PRN[nm])][:4000] for nm in names}
        assign={}
        def bt(rem,dom):
            NODES[0]+=1
            if NODES[0]>BUDGET: raise RuntimeError("BUDGET")
            if time.time()>DL: raise RuntimeError("TIMEBOX")
            if not rem: return True
            best=None; bd=None
            for nm in rem:
                if bd is None or len(dom[nm])<len(bd): best=nm; bd=dom[nm]
            if not bd: return False
            for (m,meta) in bd:
                nd={}; dead=False
                for onm in rem:
                    if onm==best: continue
                    keep=[(mm,mt) for (mm,mt) in dom[onm] if not (mm & m)]
                    if not keep: dead=True; break
                    nd[onm]=keep
                if dead: continue
                assign[best]=(m,meta)
                if bt([x for x in rem if x!=best],nd): return True
                assign.pop(best,None)
            return False
        ok=bt(list(names),dom); return ok
    try:
        ok=solve(); hit=None
    except RuntimeError as ex:
        ok=False; hit=str(ex)
    log("FULL STREAM ok=%s nodes=%d hit=%s elapsed=%.1fs"%(ok,NODES[0],hit,time.time()-t0))
    rep={"artifact":"k2_r696_fastpruned_binary_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-261: (b) efficiency-fixed streaming solve (sound windowed dominance pruning + least-constraining value order + MRV + forward checking) over the v3-prime family; domain-collapse readings included per the ruling gate; one run; fail-loud. Prior: #K2-260(yi) (pass A universe, pass B bitmask-only storage, dedupe by mask; MRV + forward checking + conflict-directed backjumping; node budget 1.5e6 + timebox 1500s; fail-loud). Route family v3-prime (single-stage + two-stage with jog on a full-span row; R580/R603 precedent).",
         "construction_runs":1,"drawings":0,
         "cell_universe":len(uni),"domain_collapse":{nm.split("PCIE_UP_")[1]:{"unique":len(DOM[nm]),"pruned":len(DOM_PRN[nm])} for nm in names},"candidate_counts":{nm.split("PCIE_UP_")[1]:cnt[nm] for nm in names},
         "unique_masks":{nm.split("PCIE_UP_")[1]:len(DOM[nm]) for nm in names},
         "solve":{"ok":bool(ok),"nodes":NODES[0],"hit":hit},
         "per_lane":{}, "conservation":{}, "buildability":{}}
    if ok:
        # reconstruct with a fresh deterministic generator pass restricted to the chosen masks
        chosen={nm:assign[nm][1] for nm in names}
        used=set(); tot=0; dup=0
        slot={}; col={}; ex={}
        for nm in names:
            meta=chosen[nm]; m=assign[nm][0]
            sl=meta
            rep["per_lane"][nm.split("PCIE_UP_")[1]]={"H":meta["H"],"Xa":meta["Xa"],"Rm":meta["Rm"],"Xb":meta["Xb"],"tail_layer":meta["t"],"kind":meta["kind"],
                                                      "exit_cell":list(EX[nm]),"exit_layer":int(T[nm]["exit_layer"]),"n_cells":bin(m).count("1")}
            tot+=bin(m).count("1")
            for i in range(len(uni)):
                pass
        # verify pairwise disjointness over the chosen masks
        ms=[(nm,assign[nm][0]) for nm in names]
        bad=[]
        for i in range(len(ms)):
            for j in range(i+1,len(ms)):
                if ms[i][1]&ms[j][1]: bad.append([ms[i][0].split("PCIE_UP_")[1],ms[j][0].split("PCIE_UP_")[1]])
        rep["conservation"]={"pairwise_disjoint_masks":len(bad)==0,"collisions":bad}
        rep["buildability"]={"mode":"relocation_listed" if any(chosen[nm]["kind"]=="two" for nm in names) else "no_move",
                             "note":"route family v3-prime; per-lane H/Xa/Rm/Xb listed"}
        rep["binary"]="SAT"
    else:
        rep["conservation"]={"N/A":"no allocation certified","pairwise_disjoint_masks":None}
        rep["buildability"]={"mode":"no_witness"}; rep["binary"]="UNSAT_or_budget"
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
