#!/usr/bin/env python3
"""K2 R718 (#K2-269/270 STEP 2, unconditional): YIELD-AND-REARRANGE.
Load the frozen base13 PER-CELL from the R714 artifact; recompute the two gamma-1 paths (same rule) => the 15.
Rank the 15 by overlap with OUT7_P's own corridor; the least-overlap lane YIELDS; re-solve (that lane + OUT7_P)
deterministically (bounded path searches, zero backtracking/zero parameter search); merge => 16/16 or a named UNSAT."""
import sys,os,json,types,importlib,hashlib,time,heapq,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R718_YIELD_REROUTE_16OF16_v1.json"; LOGF="/tmp/opencode/r718/solve.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
    T=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]
    LN={nm:g2.build_lane(nm) for nm in names}
    FREE={nm:({rc(u) for u in LN[nm]["adj"] if u<NID},{rc(u) for u in LN[nm]["adj"] if NID<=u<2*NID}) for nm in names}
    EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
    # --- load the frozen base13 per-cell ---
    r714=json.load(open("K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json"))
    base={}
    for k,v in r714["baseline_frozen"]["per_lane"].items():
        base["PCIE_UP_"+k]=[(int(lay),tuple(cp)) for lay,cp in v]
    base13=set()
    for v in base.values(): base13|=set(v)
    log("frozen base13 loaded: %d lanes / %d unique cells"%(len(base),len(base13)))
    def search(nm,blocked,maxmid):
        v=T[nm]; cl=int(v["col60_layer"]); H=v["H"]; e=EX[nm]; eL=int(v["exit_layer"])
        start=(cl,(60,H)); goal=(eL,e); allowed={0:set(),1:set()}
        for L in (0,1):
            for p in FREE[nm][L]:
                if (L,p) not in blocked: allowed[L].add(p)
        if start[1] not in allowed[start[0]] or goal[1] not in allowed[goal[0]]: return None
        dist={(start[0],start[1]):(0,0)}; prev={}; pq=[(0,0,start[0],start[1][0],start[1][1])]
        while pq:
            sw,st,L,c,r=heapq.heappop(pq)
            if (L,(c,r))==goal:
                out=[]; cur=(L,(c,r))
                while cur is not None: out.append(cur); cur=prev.get(cur)
                return list(reversed(out))
            for dc,dr in ((1,0),(-1,0),(0,1),(0,-1)):
                q=(c+dc,r+dr)
                if q in allowed[L]:
                    nd=(sw,st+1)
                    if (L,q) not in dist or nd<dist[(L,q)]:
                        dist[(L,q)]=nd; prev[(L,q)]=(L,(c,r)); heapq.heappush(pq,(nd[0],nd[1],L,q[0],q[1]))
            if sw<maxmid and (c,r) in allowed[1-L]:
                nd=(sw+1,st+1)
                if (1-L,(c,r)) not in dist or nd<dist[(1-L,(c,r))]:
                    dist[(1-L,(c,r))]=nd; prev[(1-L,(c,r))]=(L,(c,r)); heapq.heappush(pq,(nd[0],nd[1],1-L,c,r))
        return None
    # --- recompute the two gamma-1 paths (same rule) => base15 ---
    merged={nm:set(seg) for nm,seg in base.items()}
    ok15=True
    for nm in ("PCIE_UP_OUT0_P_J2","PCIE_UP_OUT4_N_J2"):
        p=search(nm,base13,2)
        if p is None: ok15=False; log("gamma-1 path NOT reproduced for %s"%nm.split("PCIE_UP_")[1]); continue
        merged[nm]=set(p)
    log("base15 lanes=%d cells=%d (ok15=%s)"%(len(merged),sum(len(v) for v in merged.values()),ok15))
    # --- rank the 15 by overlap with OUT7_P's corridor ---
    want={0:set(),1:set()}
    for L2 in (0,1):
        for p in FREE[LAST][L2]: want[L2].add(p)
    occ=collections.defaultdict(set)
    for nm,s3 in merged.items():
        for (lay,cp) in s3:
            if cp in want[lay]: occ[nm].add((lay,cp))
    ranked=sorted(occ.items(), key=lambda kv:(len(kv[1]),kv[0]))
    log("STEP2 ranked (least overlap first): %s"%[(n.split("PCIE_UP_")[1],len(c)) for n,c in ranked[:6]])
    # --- yield loop (deterministic) ---
    sol=None; tried=[]
    for nm,cells in ranked:
        others=set()
        for nm2,s3 in merged.items():
            if nm2!=nm: others|=s3
        pL=search(nm,others,1)                      # the yielded lane keeps <=2 pairs
        if pL is None: tried.append((nm.split("PCIE_UP_")[1],"no yield path")); continue
        p7=search(LAST,others|set(pL),2)            # OUT7_P keeps <=3 pairs
        if p7 is None: tried.append((nm.split("PCIE_UP_")[1],"OUT7_P still blocked")); continue
        sol={"yielded_lane":nm.split("PCIE_UP_")[1],"yielded_new_cells":len(pL),"out7p_cells":len(p7),
             "yielded_path":[(L,list(p)) for (L,p) in pL],"out7p_path":[(L,list(p)) for (L,p) in p7]}
        log("STEP2 SAT: yielded %s (new len=%d) + OUT7_P (len=%d) => 16/16"%(nm.split("PCIE_UP_")[1],len(pL),len(p7)))
        break
    if sol:
        for L,pL in sol["yielded_path"]: pass
        yd="PCIE_UP_"+sol["yielded_lane"]
        merged[yd]=set((L,tuple(p)) for (L,p) in sol["yielded_path"])
        merged[LAST]=set((L,tuple(p)) for (L,p) in sol["out7p_path"])
    tot=sum(len(v) for v in merged.values()); uniq=set()
    for v in merged.values(): uniq|=v
    slots={(int(T[nm]["col60_layer"]),T[nm]["H"]) for nm in merged}
    exs={tuple(EX[nm]) for nm in merged}
    cons={"lanes":len(merged),"col60_slots_distinct":len(slots)==16,"exit_cells_distinct":len(exs)==16,
          "FOURTH_KEY_physical_disjoint":(tot==len(uniq)),"cells_total":tot,"cells_distinct":len(uniq),
          "note":"path routes: the descent-column proxy is not well-defined; the PHYSICAL key is definitive"}
    ok=(len(merged)==16 and cons["FOURTH_KEY_physical_disjoint"] and cons["col60_slots_distinct"] and cons["exit_cells_distinct"])
    log("MERGED lanes=%d cells=%d uniq=%d FOURTH_KEY=%s"%(len(merged),tot,len(uniq),cons["FOURTH_KEY_physical_disjoint"]))
    rep={"artifact":"k2_r718_yield_reroute_16of16_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-269 sec.3.3 STEP2 / #K2-270: yield-and-rearrange, unconditional binary. base_ref=K2_BASE13_FROZEN_v1 (loaded per-cell from the R714 artifact) + the two gamma-1 paths recomputed (15 lanes). Least-overlap lane yields; (that lane + OUT7_P) re-solved deterministically (bounded path searches; zero backtracking, zero parameter search).",
         "construction_runs":1,"drawings":0,
         "base_ref":"K2_BASE13_FROZEN_v1","base15_lanes":15,"base15_ok":bool(ok15),
         "blocking_ranking":[(n.split("PCIE_UP_")[1],len(c)) for n,c in ranked],
         "yield_attempts":tried,"step2":sol,
         "conservation":cons,"buildability":{"mode":"relocation_listed","note":"one lane yielded and was rerouted; OUT7_P added"} if sol else {"mode":"no_witness"},
         "per_lane_cells":{n.split("PCIE_UP_")[1]:len(v) for n,v in merged.items()},
         "binary":("SAT_16of16" if ok else "UNSAT_or_named")}
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("WROTE %s hash=%s binary=%s"%(OUT,rep["artifact_hash16"],rep["binary"])); log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
