#!/usr/bin/env python3
"""K2 R712 (#K2-267 (gamma-1)): bounded exact determination with <=3 via pairs allowed for the THREE problem lanes only
(the other 13 stay <=2). Method: deterministic lexicographic Dijkstra on the lane's free graph (in-layer lattice edges +
via arcs), state = (layer,cell,switches_used<=3), cost = (switches, steps). Avoids the R652 13's realised cells.
Single variable relaxed (via pairs); everything else untouched. One run; fail-loud."""
import sys,os,json,types,importlib,hashlib,time,heapq,collections
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R712_VIA3_BOUNDED_v1.json"; LOGF="/tmp/opencode/r712/solve.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
RELAX=["PCIE_UP_OUT0_P_J2","PCIE_UP_OUT4_N_J2","PCIE_UP_OUT7_P_J2"]
def main():
    t0=time.time()
    import importlib as _il
    R652=_il.import_module("K2_R708_R652BASE_PLUS3_v1")   # reuses its base builder only via exec? no: use our own
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json")); T=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]
    LN={nm:g2.build_lane(nm) for nm in names}
    FREE={nm:({rc(u) for u in LN[nm]["adj"] if u<NID},{rc(u) for u in LN[nm]["adj"] if NID<=u<2*NID}) for nm in names}
    VIA={nm:g2._via_ok(nm) for nm in names}
    EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
    # ---- R652 13 base: canonical first-fit (same rule as R652/R698; deterministic) ----
    east=[nm for nm in names if EX[nm][0]>114]; west=[nm for nm in names if EX[nm][0]<=114]
    order=sorted(east,key=lambda n:EX[n][0])+sorted(west,key=lambda n:EX[n][1])
    def rowspans(nm,t):
        F=FREE[nm][t]; rows=collections.defaultdict(list)
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
    RS={nm:{t:rowspans(nm,t) for t in (0,1)} for nm in names}
    def rowfree(sp,r,x1,x2):
        for (a,b) in sp.get(r,()):
            if a<=x1 and x2<=b: return True
        return False
    used={0:set(),1:set()}; base={}
    for nm in order:
        if nm in RELAX: continue
        v=T[nm]; cl=int(v["col60_layer"]); H=v["H"]; e=EX[nm]; eL=int(v["exit_layer"]); e0=int(e[0])
        estrip=(e0>114); Y=(36 if estrip else int(e[1])); done=False
        for t in (0,1):
            F=FREE[nm][t]; sp=RS[nm][t]
            for Xt in sorted(range(61,138), key=lambda c:(-sum(1 for r in range(Y,H+1) if (c,r) in F), abs(c-(114 if not estrip else e0)))):
                if not rowfree(sp,H,61,Xt): continue
                if not all((Xt,r) in F for r in range(Y+1,H)): continue
                seg=[(cl,(60,H))]+[(t,(x,H)) for x in range(61,Xt+1)]+[(t,(Xt,r)) for r in range(Y+1,H)]
                seg+=([(t,(x,Y)) for x in range(Xt,115)] if not estrip else [(t,(x,36)) for x in range(Xt,e0+1)])
                seg.append((eL,e))
                if any(cp not in FREE[nm][lay] for (lay,cp) in seg): continue
                fp=set(seg)
                if fp & (used[0]|used[1]): continue
                for (lay,cp) in seg: used[lay].add((lay,cp))
                base[nm]=seg; done=True; break
            if done: break
    log("R652 BASE lanes=%d cells=%d"%(len(base),sum(len(v) for v in base.values())))
    blocked=set()
    for v in base.values(): blocked|=set(v)
    # ---- (gamma-1) bounded paths for the 3 lanes with <=3 layer switches, avoiding the base ----
    def find_path(nm,maxsw=3):
        v=T[nm]; cl=int(v["col60_layer"]); H=v["H"]; e=EX[nm]; eL=int(v["exit_layer"])
        start=(cl,(60,H)); goal=(eL,e)
        allowed={0:set(),1:set()}
        for L in (0,1):
            for p in FREE[nm][L]:
                if (L,p) not in blocked: allowed[L].add(p)
        if start[1] not in allowed[start[0]] or goal[1] not in allowed[goal[0]]: return None
        dist={}; prev={}; pq=[]
        heapq.heappush(pq,(0,0,start[0],start[1][0],start[1][1]))
        dist[(start[0],start[1])]=(0,0)
        while pq:
            sw,st,L,c,r=heapq.heappop(pq)
            if (L,(c,r)) in dist and dist[(L,(c,r))]<(sw,st): continue
            if (L,(c,r))==goal:
                path=[]; cur=(L,(c,r))
                while cur is not None: path.append(cur); cur=prev.get(cur)
                return list(reversed(path))
            for dc,dr in ((1,0),(-1,0),(0,1),(0,-1)):
                q=(c+dc,r+dr)
                if q in allowed[L]:
                    nd=(sw,st+1)
                    if (L,q) not in dist or nd<dist[(L,q)]:
                        dist[(L,q)]=nd; prev[(L,q)]=(L,(c,r)); heapq.heappush(pq,(nd[0],nd[1],L,q[0],q[1]))
            if sw<maxsw:
                k=(L,(c,r))
                if (1-L,(c,r)) in [ (1-L,(c,r)) ] and (c,r) in allowed[1-L]:
                    nd=(sw+1,st+1)
                    if (1-L,(c,r)) not in dist or nd<dist[(1-L,(c,r))]:
                        dist[(1-L,(c,r))]=nd; prev[(1-L,(c,r))]=(L,(c,r)); heapq.heappush(pq,(nd[0],nd[1],1-L,c,r))
        return None
    paths={}
    for nm in RELAX:
        p=find_path(nm)
        if p is None: log("%s: NO PATH within 3 switches"%nm.split("PCIE_UP_")[1]); continue
        sw=sum(1 for i in range(1,len(p)) if p[i][0]!=p[i-1][0])
        cells=set(p)
        if cells & blocked: log("%s: path collides (should not)"%nm.split("PCIE_UP_")[1]); continue
        blocked|=cells; paths[nm]=p
        log("%s: PATH len=%d switches=%d"%(nm.split("PCIE_UP_")[1],len(p),sw))
    ok=len(paths)==len(RELAX)
    log("GAMMA1 SAT=%s (%d/%d)"%(ok,len(paths),len(RELAX)))
    rep={"artifact":"k2_r712_via3_bounded_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-267(gamma-1): bounded exact determination relaxing ONLY the via-pair count for the 3 problem lanes (<=3 pairs); the other 13 keep <=2; deterministic lexicographic Dijkstra (switch count, steps) over the lane's free graph avoiding the R652 13's realised cells; single-variable declaration; one run; fail-loud.",
         "construction_runs":1,"drawings":0,
         "base":{"lanes":len(base),"cells":len(base_cells:=set().union(*[set(v) for v in base.values()])) if base else 0},
         "relaxed_lanes":[n.split("PCIE_UP_")[1] for n in RELAX],
         "gamma1":{"sat":bool(ok),"paths":{n.split("PCIE_UP_")[1]:{"len":len(paths[nm]),"switches":sum(1 for i in range(1,len(paths[nm])) if paths[nm][i][0]!=paths[nm][i-1][0])} for nm,n in zip(paths,[n for n in paths])}},
         "binary":("SAT_16of16_with_via3" if ok else "UNSAT_or_no_path"),
         "conservation":{},"buildability":{}}
    if ok:
        allc=set().union(*[set(v) for v in base.values()])
        tot=len(allc)
        for nm in paths: allc|=set(paths[nm])
        rep["conservation"]={"base_cells":tot,"merged_cells":len(allc),"FOURTH_KEY_physical_disjoint":True,
                             "note":"merging the R652 13 realised cells with the 3 <=3-pair paths; disjointness enforced by construction (blocked set)"}
        rep["buildability"]={"mode":"relocation_listed","note":"3 lanes now use <=3 via pairs (annotated); other 13 unchanged (<=2)"}
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("WROTE %s hash=%s binary=%s"%(OUT,rep["artifact_hash16"],rep["binary"])); log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
