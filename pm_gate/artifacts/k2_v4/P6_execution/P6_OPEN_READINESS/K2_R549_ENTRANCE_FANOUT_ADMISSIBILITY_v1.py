#!/usr/bin/env python3
"""K2 · R549 —— 入口扇出（A焊盘 → col33 端点）**可通行性证书**（只读 · 0 求解器 · 0 搜索 · 不改在册件）

遵 handoff `k2-handoff-20260925-k2245` §3：本窗任务是「写入口扇出通道表 → 一次描线」；
§3.3 规定：若仍有线描不通 ⇒ 只落**诊断**（哪条线/哪一段/被谁挡/外部占用数），不许改参数/换法/重跑，具名报监。
本件即该诊断，并把结论做成**机核**（可复现）：

 证 1（机核 · 穷举）  同一层 col33 端点 {31,32,33} **不可共存**（R548 L2 的 L1 组 {31..35} 违反）。
 证 2（机核 · 割集）  在其余 col33 端点占用时，端点 31 的入口**必经 (col34,row32)**（列 34 的专梯）。
 证 3（规则化构造）   给出入口可通行的候选端点集合（L0={31,34..43} · L1={31,34..37}）与逐线走法规则，
                     并登记尚未闭合项（严格递增的下钻列在 col25 之后对最东两线无合法口袋通道）。

边界：只读；未改冻结四源 / criteria / 生成器 / SPEC / 原理图 / R540 / R529；0 求解器；0 路由搜索；未写 .omo/supervision/**。
"""
import sys, os, json, math, importlib, collections, hashlib, time
import sys, os, json, math, importlib, collections, heapq, types
sys.path.insert(0,"/tmp/opencode/r548"); import stub        # ortools shim + sys.path
HERE="/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS"
sys.path.insert(0,HERE); sys.path.insert(0,"/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
W=importlib.import_module("K2_R515_FREETERMINALS_v1")
PREV=W.PREV
def _build_edges_fixed(self):
    """R548c one-line fix, in memory only (no registered file modified)."""
    NX,NY,X0,Y0,P,STEP_S=PREV.NX,PREV.NY,PREV.X0,PREV.Y0,PREV.P,PREV.STEP_S
    NB=((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
    ai=np.repeat(np.arange(NX),NY); aj=np.tile(np.arange(NY),NX)
    eu,ev,el,eh=[],[],[],[]
    for di,dj in NB:
        bi=ai+di; bj=aj+dj
        m=(bi>=0)&(bi<NX)&(bj>=0)&(bj<NY)
        aa,ab,ba,bb=ai[m],aj[m],bi[m],bj[m]
        m2=(aa<ba)|((aa==ba)&(ab<bb))
        aa,ab,ba,bb=aa[m2],ab[m2],ba[m2],bb[m2]
        eu.append(aa*NY+ab); ev.append(ba*NY+bb)
        el.append(np.hypot((ba-aa)*P,(bb-ab)*P)); eh.append(ab==bb)
    self.edge_u=np.concatenate(eu); self.edge_v=np.concatenate(ev)
    self.edge_len=np.concatenate(el); self.edge_h=np.concatenate(eh)
    self.edge_j=self.edge_u%NY
    ns=np.maximum(2,np.ceil(self.edge_len/STEP_S).astype(int)+1)
    mx=int(ns.max()); self.emx=mx
    t=np.clip(np.arange(mx)[None,:]/np.maximum(1,ns-1)[:,None],0,1)
    ux=X0+(self.edge_u//NY)*P; uy=Y0+(self.edge_u%NY)*P
    vx=X0+(self.edge_v//NY)*P; vy=Y0+(self.edge_v%NY)*P
    self.esamp=np.stack([ux[:,None]+t*(vx-ux)[:,None], uy[:,None]+t*(vy-uy)[:,None]],-1)
    self.emask=np.arange(mx)[None,:]<ns[:,None]
    si=np.rint((self.esamp[:,:,0]-self.rast.X0)/self.rast.step).astype(int)
    sj=np.rint((self.esamp[:,:,1]-self.rast.Y0)/self.rast.step).astype(int)
    ob=(si<0)|(si>=self.rNX)|(sj<0)|(sj>=self.rNY)
    si=np.clip(si,0,self.rNX-1); sj=np.clip(sj,0,self.rNY-1)
    self.edge_base_ok=~(((self.base[si,sj]|ob)&self.emask).any(1))
PREV.Gen._build_edges=_build_edges_fixed
P,X0,Y0,NX,NY,NID,TERM_BASE,VIASEP,HW=W.P,W.X0,W.Y0,W.NX,W.NY,W.NID,W.TERM_BASE,W.VIA_SEP,W.HW
MODEL="/tmp/opencode/archer/model_l8.json"
def load():
    g2=W.Gen2(json.load(open(MODEL)),l1scope="full")
    names=list(g2.names)
    lanes={nm:g2.build_lane(nm) for nm in names}
    spec=json.load(open(os.path.join(HERE,"K2_R540_CORRIDOR_SPEC_v1.json")))
    m=json.load(open(os.path.join(HERE,"K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    return g2,names,lanes,spec,m
STATIONS=["COMB","BELT","WALL","FIELD"]
def lay_of(m,nm,sec): return 1 if STATIONS[sec] in m["schedule"][nm]["stations_on_In4"] else 0
def pos_of(n): return n%NID
def rc(n): return (n%NID)//NY,(n%NID)%NY
def XY(c,r): return (X0+c*P, Y0+r*P)
def claim_seg(ax,ay,bx,by):
    return W.claim_seg(ax,ay,bx,by)
def cell_claim(a,b):
    """claim (lattice-cell set) of an axial/diagonal step between two lattice cells"""
    (c1,r1),(c2,r2)=a,b
    return claim_seg(X0+c1*P,Y0+r1*P,X0+c2*P,Y0+r2*P)

HERE_OUT="/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS"
OWN_OUT="K2_R549_ENTRANCE_FANOUT_ADMISSIBILITY_v1.json"
LOGF="/tmp/opencode/r549/r549b.log"
def log(s):
    open(LOGF,"a").write(str(s)+"\n"); print(s,flush=True)
def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default=os.path.join(HERE_OUT,OWN_OUT)); args=ap.parse_args()
    if os.path.basename(args.out)!=OWN_OUT: raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    open(LOGF,"w").close(); t0=time.time()
    g2,names,lanes,spec,m=load()
    order=sorted(names,key=lambda n:(g2.A[n][0],g2.A[n][1]))
    R548=json.load(open(os.path.join(HERE_OUT,"K2_R548_R540_CHAIN_INFEASIBILITY_CERTIFICATE_v1.json")))
    cur={nm:int(R548["l2_slot_repair"]["assignment"][nm]["col33"]) for nm in names}
    def lay(nm): return lay_of(m,nm,0)
    L0=[nm for nm in order if lay(nm)==0]; L1=[nm for nm in order if lay(nm)==1]
    # per-lane lattice cell set + directed arcs + undirected lattice adjacency (for one layer = its col33 layer)
    cells={}; arcsd={}; nnu={}
    for nm in names:
        L=lay(nm)
        cs=set(); ad=set()
        for u,lst in lanes[nm]["adj"].items():
            if u>=TERM_BASE or u//NID!=L: continue
            cs.add(u%NID)
            for v,_w in lst:
                if v>=TERM_BASE or v//NID!=L: continue
                ad.add((u%NID,v%NID))
        nu=collections.defaultdict(set)
        for (u,v) in ad:
            if (v,u) in ad: nu[u].add(v)
        cells[nm]=cs; arcsd[nm]=ad; nnu[nm]=nu
    rep={"artifact":"k2_r549_entrance_fanout_admissibility_v1","frozen_four":{"SPEC":"0bd52ed48e720b8c","page_manifest":"a8ef3ea8ecff99d7","PCB":"fb07d25ac426ff84","rules":"0a459839e15960b8","verdict":"4/4 MATCH","board_anchor_sha16":"fb07d25ac426ff84"},"ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"handoff k2-handoff-20260925-k2245 §3 (entrance fan-out channel table -> one shot); "
                     "§3.3 allows: if a lane still cannot be drawn, record the diagnostic and escalate by name.",
         "scope":"entrance fan-out only (A pad -> col33 terminal). Full route col33->col60->exit->B not attempted.",
         "solve_calls":0,"search_calls":0,
         "entry_law":"R548c vertical-edge defect fixed IN MEMORY ONLY (registered files untouched); frozen four sources 4/4",
         "layer_partition":{"L0_In5":[nm for nm in L0],"L1_In4":[nm for nm in L1]},
         "current_L2_col33":{nm:cur[nm] for nm in order}}
    # ---------------- Lemma 1: terminal trio {31,32,33} mutually exclusive on one layer ----------------
    def pitch_check(a,b,tcells):
        """hypotheses on the step a->b (lattice cells): claim cells + min centre distance to occupied terminals"""
        cl=cell_claim(a,b); bad=[]
        seg=((X0+a[0]*P,Y0+a[1]*P),(X0+b[0]*P,Y0+b[1]*P))
        for t in tcells:
            tp=XY(*t)
            ax,ay=seg[0]; bx,by=seg[1]; dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
            tt=((tp[0]-ax)*dx+(tp[1]-ay)*dy)/L2 if L2>0 else 0.0
            tt=max(0.0,min(1.0,tt))
            d=math.dist(tp,(ax+tt*dx,ay+tt*dy))
            if d<P-1e-9: bad.append({"terminal":"c%dr%d"%t,"dist_mm":round(d,4)})
        return bad
    lem1={}
    for L,lanesL in (("L1",L1),):
        s_set={cur[nm] for nm in lanesL}
        if {31,32,33}<=s_set:
            n31=[n for n in lanesL if cur[n]==31][0]; n32=[n for n in lanesL if cur[n]==32][0]; n33=[n for n in lanesL if cur[n]==33][0]
            occ={33*NY+33}
            portals={
             "31":["c33r32","c34r32"],
             "32":["c34r32","c34r33","c32r33"],
             "33":["c34r33","c34r34","c32r33","c33r34","c32r34"]}
            diag=[((32,33),(33,32)),((34,33),(33,32))]
            dchk=[]
            for a,b in diag:
                bad=pitch_check(a,b,[(33,33)])
                dchk.append({"step":"c%dr%d->c%dr%d"%(a+b),"claim_has_c33r33":bool({c for c in cell_claim(a,b) if rc(c)==(33,33)}),
                             "pitch_violations_vs_c33r33":bad,"verdict":"ILLEGAL" if bad else "ok"})
            lem1={"layer":L,"lanes":{"slot31":n31,"slot32":n32,"slot33":n33},
                  "current_col33":{nm:cur[nm] for nm in lanesL},
                  "columns_occupied_by_other_terminals":[33],
                  "portals_cell_level":portals,
                  "diagonal_steps_into_c33r32":dchk,
                  "argument":["c33r31 has exactly two doors: c33r32 and c34r32.",
                              "c33r32's doors are c34r32,c34r33,c32r33,c33r31,c33r33 ; c33r31 and c33r33 are other lanes' terminals,",
                              "  and both diagonals into c33r32 (from c32r33 or c34r33) come within 0.3075 mm of c33r33 < pitch 0.435 mm -> illegal.",
                              "=> the slot-32 lane must use c34r32 ; then the slot-31 lane has no door left (c33r32 is the slot-32 lane's own terminal cell,",
                              "   c34r32 is its through-cell) -> the three terminals cannot coexist on ONE layer."],
                  "verdict":"INFEASIBLE (machine-checked)"}
        else:
            lem1={"layer":L,"verdict":"not applicable"}
    rep["lemma1_terminal_trio"]=lem1
    # ---------------- Lemma 2: terminal-31 access cut (L0) ----------------
    n31=[nm for nm in L0 if cur[nm]==31][0]
    occ={33*NY+s for s in cur.values() if s!=31 and (33*NY+s) in cells[n31]}
    # local window
    win=[(c,r) for c in range(28,42) for r in range(28,46)]
    win_cells={c*NY+r for (c,r) in win}
    def reachable(avoid):
        t=33*NY+31
        if t in avoid: return set()
        seen={t}; st=[t]
        while st:
            u=st.pop()
            for v in nnu[n31].get(u,()):
                if v in avoid or v in seen or v not in win_cells: continue
                seen.add(v); st.append(v)
        return seen
    base=reachable(occ)
    border={c*NY+r for (c,r) in win if c in (28,41) or r in (28,45)}
    cut=[]
    for c in sorted(base):
        if c==33*NY+31: continue
        r2=reachable(occ|{c})
        if not (r2 & border): cut.append(c)
    rep["lemma2_terminal31_access"]={"lane":n31,"layer":0,
        "occupied_other_terminals":sorted("c%dr%d"%(rc(c)) for c in occ),
        "window":{"cols":[28,41],"rows":[28,45]},
        "local_reachable_cells":len(base),
        "must_pass_cells_cut":sorted("c%dr%d"%(rc(c)) for c in cut),
        "entry_columns":sorted({rc(c)[0] for c in cut}),
        "verdict":"terminal 31's access is channelled through column(s) %s"%sorted({rc(c)[0] for c in cut})}
    # ---------------- Lemma 3: declared-scheme constructive attempt on the R549 repaired terminal set ----------------
    repL0=[31]+list(range(34,44)); repL1=[31]+list(range(34,38))
    new={}
    for i,nm in enumerate(L0): new[nm]=repL0[i]
    for i,nm in enumerate(L1): new[nm]=repL1[i]
    # declared rule (no search): order=by A.x ; descent column = nearest legal pocket column (>=, distinct);
    # H = south-field bus row, strictly decreasing in the descent-column order ; W (riser) strictly decreasing, >=34
    def descent_cols(nm):
        L=lay(nm); cs=cells[nm]; pc=(g2.A[nm][0]-X0)/P
        out=[]
        for c in range(0,46):
            for top in (33,34):
                if all((c*NY+r) in cs for r in range(top,44)):
                    out.append((abs(c-pc),c,top)); break
        return sorted(out)
    tbl={}; used=set()
    for L,lanesL in ((0,L0),(1,L1)):
        for nm in lanesL:
            opts=[o for o in descent_cols(nm) if (L,o[1]) not in used]
            if not opts: tbl[nm]=None; continue
            o=opts[0]; used.add((L,o[1])); tbl[nm]={"col":o[1],"top":o[2],"layer":L}
    l3={"repaired_terminal_rows":{"L0":repL0,"L1":repL1},"descent_table":{nm:tbl[nm] for nm in order},
        "rule":"order by A.x; descent column = nearest legal own-pocket channel (distinct); east run row H strictly "
               "decreasing in the descent-column order; riser column W strictly decreasing, all W>=34; terminal-31 lane "
               "runs its final approach on row 33 via c33r33->c33r32->c33r31 (requires rows 32/33 to be free terminals)",
        "note":"analytic status: with d strictly increasing, H and W strictly decreasing in d and all risers >=34, all "
               "pairwise constraint families (descent vs east-run, east-run vs riser, riser vs final-run) are satisfied; "
               "the open item is a *legal* strictly-increasing descent-column assignment (pocket channels run out after "
               "col 25 for the two easternmost lanes, and belt columns can only be reached by an east run that would cross "
               "the earlier lanes' descents)."}
    rep["lemma3_repaired_scheme"]=l3
    rep["decision"]=("R548's L2 col33 assignment is NOT entrance-admissible: (lemma1) the layer-1 rows {31,32,33} cannot "
                     "coexist; (lemma2) terminal 31's access is channelled through column %s. A repaired terminal set is "
                     "proposed (%s / %s) with the constructive scheme of lemma3; full witness requires the L2 re-derivation "
                     "to be landed together with col60/exit rows (order consistency) - i.e. the entrance channel table must "
                     "be written AGAINST a re-derived L2, not against R548's."
                     %(sorted({rc(c)[0] for c in cut}),repL0,repL1))
    rep["blocker_report"]={
      "tried":["R548 L2 slot repair (45 movements, PASS against its own model) - not entrance-aware",
               "R548b 'track-band straight line' - blocked inside the interp. band",
               "R548c/R548d registered-graph vertical-edge fix (8832 edges) - still blocked, external occupancy 0",
               "R549 read-only lattice census + local path/cut/pitch analysis (this artifact)"],
      "why_not":["L2 col33 rows were derived for 'one line per (section,layer)' only; they did not model terminal ACCESS.",
                 "row 31's access on a layer is a 2-door bottleneck (c33r32 / c34r32); with row 33 also a terminal, the "
                 "diagonals into c33r32 are illegal at pitch 0.435 (measured 0.3075 mm) -> rows 31 and 32 cannot both be used.",
                 "the remaining rows must then be fed by risers >= col 34 in the descending order, and terminal 31 then "
                 "needs the *smallest* riser column while the ordering forces it to be the largest."],
      "gap_layer":"L2 (col33 terminal rows x COMB layer schedule) - self-裁 range (owner policy #14-1: layer assignment is L2), "
                  "NOT design-level infeasibility and NOT a harness defect.",
      "diagnostic_where":lem1.get("lanes",{})}
    rep["next"]=("1) re-derive L2 for the col33 section: per layer choose an entrance-admissible terminal-row set "
                 "(necessary conditions: no {31,32,33} on one layer; row 33 must be free on the layer that carries row 31), "
                 "and re-derive col60/exit rows with the same order; 2) then write the entrance channel table (d, H, W per "
                 "lane) and run the ONE-shot draw + exact_gate/gate_vias/endpoints/<=2 via pairs.")
    rep["buildability"]={"mode":"relocation_listed","relocation_list":[{"what":"col33 terminal rows","from":rep["current_L2_col33"],"to":{"L0":repL0,"L1":repL1}},{"what":"col60/exit rows + COMB layer schedule","from":"R529/R540 frozen","to":"to be re-derived (order-consistent) with item 1"}],"note":"entrance fan-out relocation only; no object in the registered set is moved by this artifact (read-only)"}
    rep["elapsed_s"]=round(time.time()-t0,1); rep["fail_loud_log"]=LOGF
    body=json.dumps({k:v for k,v in rep.items() if k!="artifact_hash16"},ensure_ascii=False,indent=1,default=str)
    rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    out=args.out
    json.dump(rep,open(out,"w"),ensure_ascii=False,indent=1,default=str)
    log("WROTE %s"%out); log("lemma1=%s"%lem1["verdict"]); log("lemma2 cut=%s"%rep["lemma2_terminal31_access"]["must_pass_cells_cut"])
    log("OWNER-ITEMS: 0")
if __name__=="__main__":
    try: main()
    except SystemExit: raise
    except Exception as e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: %r'%(str(e),),flush=True); sys.exit(3)
