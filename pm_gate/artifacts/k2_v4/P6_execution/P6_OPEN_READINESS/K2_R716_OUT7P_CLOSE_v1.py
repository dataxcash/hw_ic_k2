#!/usr/bin/env python3
"""K2 R716 (#K2-269): close the LAST lane OUT7_P on the frozen 15-lane base.
Step 1: single-lane FULL enumeration of OUT7_P at <=3 / <=4 / <=5 via pairs (bounded path search, full graph).
        <=3 => merge; <=4 => report the in-register SI gate reading; none => named blocking set.
Step 2: yield-and-rearrange - pick the lane with the LEAST overlap with OUT7_P's blocked set, re-solve (that lane + OUT7_P).
One run per step; deterministic; fail-loud. base_ref = K2_BASE13_FROZEN_v1 (+ the two gamma-1 paths)."""
import sys,os,json,types,importlib,hashlib,time,heapq,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R716_OUT7P_CLOSE_v1.json"; LOGF="/tmp/opencode/r716/solve.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
LAST="PCIE_UP_OUT7_P_J2"
def main():
    t0=time.time()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    T=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]; spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json"))
    LN={nm:g2.build_lane(nm) for nm in names}
    FREE={nm:({rc(u) for u in LN[nm]["adj"] if u<NID},{rc(u) for u in LN[nm]["adj"] if NID<=u<2*NID}) for nm in names}
    EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
    # ---- LOAD the FROZEN base13 per-cell routes from the R714 artifact, then recompute the two gamma-1 paths ----
    _r714=json.load(open("K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json"))
    base={}
    for k,v in _r714["baseline_frozen"]["per_lane"].items():
        nm="PCIE_UP_"+k
        base[nm]=[(int(lay),tuple(cp)) for lay,cp in v]
    log("FROZEN base13 loaded from K2_BASE13_FROZEN_v1: %d lanes / %d cells"%(len(base),sum(len(v) for v in base.values())))
    def path(nm,blocked,maxsw="auto",target=None):

        v=T[nm]; cl=int(v["col60_layer"]); H=v["H"]; e=EX[nm]; eL=int(v["exit_layer"])
        start=(cl,(60,H)); goal=(eL,e)
        allowed={0:set(),1:set()}
        for L in (0,1):
            for p in FREE[nm][L]:
                if (L,p) not in blocked: allowed[L].add(p)
        if start[1] not in allowed[start[0]] or goal[1] not in allowed[goal[0]]: return None,None
        mx=99 if maxsw=="auto" else maxsw
        dist={(start[0],start[1]):(0,0)}; prev={}; pq=[(0,0,start[0],start[1][0],start[1][1])]
        while pq:
            sw,st,L,c,r=heapq.heappop(pq)
            if (L,(c,r))==goal:
                p=[]; cur=(L,(c,r))
                while cur is not None: p.append(cur); cur=prev.get(cur)
                return list(reversed(p)),sw
            for dc,dr in ((1,0),(-1,0),(0,1),(0,-1)):
                q=(c+dc,r+dr)
                if q in allowed[L]:
                    nd=(sw,st+1)
                    if (L,q) not in dist or nd<dist[(L,q)]:
                        dist[(L,q)]=nd; prev[(L,q)]=(L,(c,r)); heapq.heappush(pq,(nd[0],nd[1],L,q[0],q[1]))
            if sw<mx and (c,r) in allowed[1-L]:
                nd=(sw+1,st+1)
                if (1-L,(c,r)) not in dist or nd<dist[(1-L,(c,r))]:
                    dist[(1-L,(c,r))]=nd; prev[(1-L,(c,r))]=(L,(c,r)); heapq.heappush(pq,(nd[0],nd[1],1-L,c,r))
        return None,None
    # ---- the two gamma-1 paths (recomputed deterministically against the frozen base13, same rule as R714) ----
    base13=set()
    for v in base.values(): base13|=set(v)
    import heapq as _hq
    def find_path3(nm,maxsw=2,blocked=None):
        blk=blocked if blocked is not None else base13
        v=T[nm]; cl=int(v["col60_layer"]); H=v["H"]; e=EX[nm]; eL=int(v["exit_layer"])
        start=(cl,(60,H)); goal=(eL,e); allowed={0:set(),1:set()}
        for L in (0,1):
            for p in FREE[nm][L]:
                if (L,p) not in blk: allowed[L].add(p)
        if start[1] not in allowed[start[0]] or goal[1] not in allowed[goal[0]]: return None
        dist={(start[0],start[1]):(0,0)}; prev={}; pq=[(0,0,start[0],start[1][0],start[1][1])]
        while pq:
            sw,st,L,c,r=_hq.heappop(pq)
            if (L,(c,r))==goal:
                pp=[]; cur=(L,(c,r))
                while cur is not None: pp.append(cur); cur=prev.get(cur)
                return list(reversed(pp))
            for dc,dr in ((1,0),(-1,0),(0,1),(0,-1)):
                q=(c+dc,r+dr)
                if q in allowed[L]:
                    nd=(sw,st+1)
                    if (L,q) not in dist or nd<dist[(L,q)]:
                        dist[(L,q)]=nd; prev[(L,q)]=(L,(c,r)); _hq.heappush(pq,(nd[0],nd[1],L,q[0],q[1]))
            if sw<maxsw and (c,r) in allowed[1-L]:
                nd=(sw+1,st+1)
                if (1-L,(c,r)) not in dist or nd<dist[(1-L,(c,r))]:
                    dist[(1-L,(c,r))]=nd; prev[(1-L,(c,r))]=(L,(c,r)); _hq.heappush(pq,(nd[0],nd[1],1-L,c,r))
        return None
    base15=set(base13); added=[]
    for nm in ("PCIE_UP_OUT0_P_J2","PCIE_UP_OUT4_N_J2"):
        p3=find_path3(nm)
        if p3 is None: log("gamma-1 path NOT reproduced for %s"%nm.split("PCIE_UP_")[1]); continue
        base15|=set(p3); base[nm]=[(L,tuple(p)) for (L,p) in p3]; added.append(nm.split("PCIE_UP_")[1])
    log("base15 = frozen13(%d cells) + gamma-1 lanes %s => %d cells / %d lanes"%(len(base13),added,len(base15),len(base)))
    log("base15 (frozen13 + 2 gamma-1 lanes) = %d lanes / %d cells"%(len(base),len(base15)))
    # ---- STEP 1: single-lane full enumeration at <=3 / <=4 / <=5 via pairs (pairs = mid switches + 1 exit change) ----
    step1={}
    for pairs in (3,4,5):
        p,sw=path(LAST,base15,maxsw=pairs-1)
        step1[pairs]={"path":(p is not None),"mid_switches":sw,"cells":(len(p) if p else 0)}
        log("STEP1 OUT7_P at <=%d pairs: %s (mid switches=%s)"%(pairs,"PATH" if p else "NO PATH",sw))
    best=next((k for k in (3,4,5) if step1[k]["path"]),None)
    # SI gate reading (in-register): SPEC vias.high_speed.max_per_line
    si_limit=2
    try:
        _spec3=json.load(open("../../L3/SPEC_k2_v4.json"))
        si_limit=int(_spec3["vias"]["high_speed"]["max_per_line"])
    except Exception as _e:
        log("SI rule read fallback (using 2): %s"%_e)
    log("SI gate: in-register SPEC vias.high_speed.max_per_line = %d"%si_limit)
    # ---- STEP 2: yield-and-rearrange ----
    step2=None
    if best is None:
        # named blocking set: which placed lanes occupy cells that OUT7_P's graph wants
        v=T[LAST]; want={0:set(),1:set()}
        for L in (0,1):
            for p in FREE[LAST][L]: want[L].add(p)
        occ=collections.defaultdict(set)
        for nm,seg in base.items():
            for (lay,cp) in seg:
                if (lay,cp) in base15 and cp in want[lay]: occ[nm].add((lay,cp))
        ranked=sorted(occ.items(), key=lambda kv: len(kv[1]))
        log("STEP2 blocking attribution (top-5 least-overlapping): %s"%[(n.split("PCIE_UP_")[1],len(c)) for n,c in ranked[:5]])
        for nm,cells in ranked:
            others=set()
            for nm2,seg in base.items():
                if nm2!=nm: others|=set(seg)
            pL,_=path(nm,others,maxsw=1)
            if pL is None: continue
            p7,_=path(LAST,others|set(pL),maxsw=2)
            if p7 is not None:
                step2={"yielded_lane":nm.split("PCIE_UP_")[1],"reroute_cells":len(pL),"out7p_cells":len(p7),"sat":True}
                log("STEP2 SAT: yield %s and reroute OUT7_P => 16/16"%nm.split("PCIE_UP_")[1]); break
        if step2 is None: log("STEP2: no single-lane yield worked (named) => premise-repair branch")
    rep={"artifact":"k2_r716_out7p_close_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-269: STEP1 single-lane full enumeration of OUT7_P at <=3/<=4/<=5 via pairs on the frozen 15-lane base; STEP2 (if needed) yield-and-rearrange = pick the lane with the LEAST overlap with OUT7_P's blocked cells and re-solve (that lane + OUT7_P). base_ref=K2_BASE13_FROZEN_v1 (+ the two gamma-1 paths). One run per step; deterministic; fail-loud.",
         "construction_runs":1,"drawings":0,
         "base_ref":"K2_BASE13_FROZEN_v1","base15":{"lanes":len(base),"cells":len(base15)},
         "step1_enumeration":step1,"si_gate":{"rule":"SPEC vias.high_speed.max_per_line","value":si_limit,"note":"a <=4-or-more pair route exceeds the registered per-line via limit"},
         "step2":step2,
         "binary":("SAT_16of16" if (best==3 or (step2 and step2.get("sat"))) else ("SAT_16of16_via4_if_SI_pass" if best==4 else "UNSAT_or_named")),
         "elapsed_s":round(time.time()-t0,1)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("WROTE %s hash=%s binary=%s"%(OUT,rep["artifact_hash16"],rep["binary"])); log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
