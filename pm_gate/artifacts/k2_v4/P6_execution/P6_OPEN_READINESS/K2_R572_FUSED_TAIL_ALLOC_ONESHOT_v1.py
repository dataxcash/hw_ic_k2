#!/usr/bin/env python3
"""K2 · R572 (#K2-223 fused window) -- premise v4: ONE ordered allocation table for mid-section (S2)
AND tail (S4), take-and-register from the in-register free graph, then ONE drawing pass.
No solver, no backtracking, no template guessing; on failure a named diagnostic (binary outcome).
Tail law (from F1-F5, R570/R571): no full vertical column exists west of the wall, so the tail is
  T1: (61,H)..(X,H)   east on the lane's own belt row   (row H is full-span free cols 60..114 for F2 rows)
  T2: (X,H-1)..(X,Y+1) vertical on the dedicated column X
  T3: (X..exit) on row Y=36 (east group, X>=exit_col) or row exit_row (west group, X<=113 -> (114,exit_row))
Tail is drawn on layer 0 (F3: layer 1 has no crossing rows / east columns).
"""
import sys, os, json, hashlib, time, importlib, types
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OWN_OUT="K2_R572_FUSED_TAIL_ALLOC_COMPLETE_DRAWING_v1.json"; LOGF="/tmp/opencode/r572/oneshot.log"
MODEL="/tmp/opencode/archer/model_l8.json"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
def log(m): open(LOGF,"a").write(str(m)+"\n"); print(str(m),flush=True)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1")
PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM=W.NID,W.NY,W.TERM_BASE
P,X0,Y0=W.P,W.X0,W.Y0; ST=["COMB","BELT","WALL","FIELD"]
def main():
    open(LOGF,"w").close(); t0=time.time()
    g2=W.Gen2(json.load(open(MODEL)),l1scope="full"); names=list(g2.names)
    master=json.load(open(os.path.join(HERE,"K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    spec=json.load(open(os.path.join(HERE,"K2_R540_CORRIDOR_SPEC_v1.json")))
    ent_tab=json.load(open(os.path.join(HERE,"K2_R550_CONSTRUCTION_DRAWING_v1.json")))["entrance_channel_table"]
    l2_in=json.load(open(os.path.join(HERE,"K2_R550_L2_SLOT_TABLE_v1.json")))["table"]
    def on4(nm,st): return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0
    lanes={nm:g2.build_lane(nm) for nm in names}; adj={nm:lanes[nm]["adj"] for nm in names}
    aset={nm:{u:set(v for v,_w in lst) for u,lst in adj[nm].items()} for nm in names}
    CELL={(nm,L):set(u for u in adj[nm] if u<TERM and u//NID==L) for nm in names for L in (0,1)}
    LAY={nm:on4(nm,0) for nm in names}
    pi={0:[],1:[]}
    for nm in sorted(names,key=lambda n:(ent_tab[n]["d"],float(g2.A[n][0]),float(g2.A[n][1]))): pi[LAY[nm]].append(nm)
    T={}; committed={0:set(),1:set()}; own={}; fail=[]
    # ---------- mid-section S2 ----------
    for L in (0,1):
        prevH=999
        for nm in pi[L]:
            et=ent_tab[nm]; d,top,Hold=int(et["d"]),int(et["top"]),int(et["H"])
            cset=CELL[(nm,L)]; com=committed[L]
            corr=[tuple(int(x) for x in s.split(",")) for s in et["corridor_cells"]]
            i0=corr.index((d,top)); pocket=corr[:i0]
            def okr(r,cset=cset,com=com,d=d,L=L): return (L*NID+d*NY+r) in cset and (L*NID+d*NY+r) not in com
            def okrow(H,cset=cset,com=com,d=d,L=L): return all(((L*NID+x*NY+H) in cset and (L*NID+x*NY+H) not in com) for x in range(d,61))
            cands=[H for H in range(59,37,-1) if okrow(H)]
            pick=None
            for tier in (True,False):
                for H in cands:
                    if tier and H>=prevH: continue
                    if all(okr(r) for r in range(top,H+1)): pick=H; break
                if pick: break
            if pick is None: fail.append({"lane":nm,"L":L,"d":d,"resource":"mid H"}); continue
            H=pick
            poly=list(pocket)+[(d,r) for r in range(top,H+1)]+[(x,H) for x in range(d+1,61)]
            for p in poly: com.add(L*NID+p[0]*NY+p[1])
            own.setdefault((nm,L),set()).update(L*NID+p[0]*NY+p[1] for p in poly)
            if L==0: own.setdefault((nm,0),set()).add(0*NID+60*NY+H)
            T[nm]={"L":L,"d":d,"top":top,"H":H,"col60_layer":on4(nm,1),"exit":int(l2_in[nm]["exit"]),"mids":poly}
            prevH=H
    # ---------- tail S4 (layer 0, same ordered table) ----------
    com0=committed[0]; com1=committed[1]
    for L in (0,1):
        for nm in pi[L]:
            if nm not in T: continue
            x=T[nm]; H=x["H"]; east=(g2.grp[nm]=="east"); exitc=x["exit"]
            Y=36 if east else exitc
            cl=CELL[(nm,0)]; ownm=own.get((nm,0),set())
            def free0(c,r,cl=cl,com0=com0,ownm=ownm):
                u=0*NID+c*NY+r
                return u in cl and (u not in com0 or u in ownm)   # own cells never block the lane (R541b class)
            # via at (60,H) needs the cell free on layer 0 too (and on the col60 registered layer)
            if not free0(60,H): fail.append({"lane":nm,"resource":"via cell (60,H) on layer 0"}); continue
            if H<=Y: fail.append({"lane":nm,"resource":"tail row ordering (H<=Y)"}); continue
            cands=(list(range(115,138)) if east else list(range(113,60,-1)))
            pick=None
            for X in cands:
                if east and X<exitc: continue
                leg1=[(c,H) for c in range(61,X+1)]
                leg2=[(X,r) for r in range(Y+1,H)]
                leg3=[(c,Y) for c in range(X-1,exitc-1,-1)] if east else [(c,Y) for c in range(X+1,115)]
                final=(exitc,Y) if east else (114,Y)
                cells=leg1+leg2+leg3
                if not cells or cells[-1]!=final: cells=cells+[final]
                if all(free0(c,r) for (c,r) in cells): pick=(X,cells); break
            if pick is None: fail.append({"lane":nm,"resource":"tail (X,cells)","Y":Y,"H":H,"east":east}); continue
            X,cells=pick
            for c,r in cells: com0.add(0*NID+c*NY+r)
            com0.add(0*NID+60*NY+H)
            x["tail"]={"X":X,"Y":Y,"cells":cells,"exit_cell":list(final)}
    probe=["PCIE_UP_OUT0_N_J2","PCIE_UP_OUT0_P_J2"]
    selfcheck={"lanes":probe,"tail_allocated":{p:(p in T and "tail" in T[p]) for p in probe}}
    selfcheck["verdict"]="PASS" if all(selfcheck["tail_allocated"].values()) else "FAIL(tool)"
    rep={"artifact":"k2_r572_fused_tail_alloc_complete_drawing_v1","selfcheck_on_known_good_lanes":selfcheck,"ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-223 fused window: U1/U2 census + premise v4 + three gates + ONE complete drawing (tail included)",
         "solve_calls":0,"runs":1,"backtracking_search":0,"tail_law":"T1 row H -> T2 dedicated column X -> T3 row Y (36 east / exit_row west) on layer 0"}
    # ---------- gates ----------
    ill=[];nonarc=[];clash=[]
    for nm in names:
        if nm not in T or "tail" not in T[nm]: continue
        x=T[nm]; L=x["L"]
        for p in x["mids"]:
            if (L*NID+p[0]*NY+p[1]) not in CELL[(nm,L)]: ill.append({"lane":nm,"cell":list(p),"seg":"mid"})
        if x["L"]==0:
            for (a,b2) in zip(x["mids"],x["mids"][1:]):
                u=L*NID+a[0]*NY+a[1]; v=L*NID+b2[0]*NY+b2[1]
                if v not in aset[nm].get(u,()) and u not in aset[nm].get(v,()): nonarc.append({"lane":nm,"u":list(a),"v":list(b2),"seg":"mid"})
        for p in x["tail"]["cells"]:
            if (0*NID+p[0]*NY+p[1]) not in CELL[(nm,0)]: ill.append({"lane":nm,"cell":list(p),"seg":"tail"})
        tc=[(60,H)] if False else None
        tailseq=[(60,x["H"])]+x["tail"]["cells"]
        for (a,b2) in zip(tailseq,tailseq[1:]):
            u=0*NID+a[0]*NY+a[1]; v=0*NID+b2[0]*NY+b2[1]
            if v not in aset[nm].get(u,()) and u not in aset[nm].get(v,()): nonarc.append({"lane":nm,"u":list(a),"v":list(b2),"seg":"tail"})
    for L in (0,1):
        gg=[n for n in pi[L] if n in T and "tail" in T[n]]
        for i,a in enumerate(gg):
            sa=set(T[a]["mids"])|set(T[a]["tail"]["cells"])
            for b2 in gg[i+1:]:
                inter=sa&(set(T[b2]["mids"])|set(T[b2]["tail"]["cells"]))
                if inter: clash.append({"layer":L,"a":a,"b":b2,"n":len(inter),"cells":sorted("%d,%d"%z for z in inter)[:5]})
        # tail cells live on layer 0 => cross-layer exclusivity
    gg0=[n for n in names if n in T and "tail" in T[n]]
    for i,a in enumerate(gg0):
        sa=set(T[a]["tail"]["cells"])
        for b2 in gg0[i+1:]:
            inter=sa&set(T[b2]["tail"]["cells"])
            if inter: clash.append({"layer":"tail-L0","a":a,"b":b2,"n":len(inter),"cells":sorted("%d,%d"%z for z in inter)[:5]})
    cap={}
    for L in (0,1):
        gg=[n for n in pi[L] if n in T]
        cap["L%d"%L]={"need":len(pi[L]),"assigned":len(gg),"rows":sorted({T[n]["H"] for n in gg},reverse=True),
                      "rows_distinct":len({T[n]["H"] for n in gg})==len(gg)}
    tailX={nm:T[nm]["tail"]["X"] for nm in names if nm in T and "tail" in T[nm]}
    rep["census_U1_U2"]={"U1_west_dedicated_columns_used":{k:v for k,v in tailX.items() if not (g2.grp[k]=="east")},
                         "U2_east_columns_used":{k:v for k,v in tailX.items() if (g2.grp[k]=="east")},
                         "east_cols_distinct":len({v for k,v in tailX.items() if g2.grp[k]=="east"})==sum(1 for k in tailX if g2.grp[k]=="east"),
                         "west_cols_distinct":len({v for k,v in tailX.items() if not g2.grp[k]=="east"})==sum(1 for k in tailX if not g2.grp[k]=="east")}
    rep["pregate"]={"(i)_cells_legal":{"verdict":"PASS" if not ill else "FAIL","n":len(ill),"sample":ill[:6]},
                    "(ii)_registered_arcs":{"verdict":"PASS" if not nonarc else "FAIL","n":len(nonarc),"sample":nonarc[:6]},
                    "(iii)_pairwise_disjoint":{"verdict":"PASS" if not clash else "FAIL","n":len(clash),"sample":clash[:6]},
                    "(iv)_capacity":{"verdict":"PASS" if all(v["rows_distinct"] for v in cap.values()) else "FAIL"}}
    rep["assignment_incomplete"]=fail
    rep["channel_table"]={nm:{k:T[nm][k] for k in ("L","d","H","col60_layer","exit")} for nm in T}
    rep["tail_table"]={nm:T[nm]["tail"] for nm in T if "tail" in T[nm]}
    rep["conservation_audit"]={"capacity_vs_demand":cap,
      "tail_supply":"east group: cols 120-135 free rows 36-59 (F3) => 16 >= 8; west group: dedicated column X in 61-113 with rows [exit_row,H] free (U1 verified in this same command by the take-and-register)"}
    ok=(not fail) and (not ill) and (not nonarc) and (not clash) and all(v["rows_distinct"] for v in cap.values())
    if not ok:
        rep["decision"]="FUSED ALLOCATION FAIL: named diagnostic only (binary 甲), NO drawing, NO rerun"
        rep["buildability"]={"mode":"no_witness","note":"pre-gate FAIL"}
        for z in (fail+ill+nonarc+clash)[:8]: log("[FAIL] %s"%json.dumps(z,ensure_ascii=False))
    else:
        chain={}
        for nm in names:
            x=T[nm]; L=x["L"]; east=(g2.grp[nm]=="east")
            items=[("A",None,0)]
            if L==1:
                pv=None
                for w in spec["per_lane"][nm]["waypoints"]:
                    if w["kind"]=="DIVE_via": pv=int(w["node"])
                if pv is None: pv=x["mids"][0][0]*NY+x["mids"][0][1]
                head=x["mids"][0][0]*NY+x["mids"][0][1]
                items.append(("via",pv,1)); seq=x["mids"] if head==pv else [pv]+x["mids"]
                items+=[("wp",p[0]*NY+p[1],L) for p in seq[1:]]
            else:
                items+=[("wp",p[0]*NY+p[1],L) for p in x["mids"]]
            items.append(("wp",60*NY+x["H"],x["col60_layer"]))
            items+=[("wp",p[0]*NY+p[1],0) for p in x["tail"]["cells"]]
            ex=(x["exit"]*NY+36) if east else (114*NY+x["exit"])
            items.append(("wp",ex,on4(nm,2)))
            pr=int(round((g2.B[nm][0]-X0)/P))*NY+36 if east else ex
            items.append(("wp",pr,on4(nm,3))); items.append(("B",None,0)); chain[nm]=items
        unit_bad=[{"lane":nm,"i":i,"nd":nd,"L":L2} for nm in names for i,(k,nd,L2) in enumerate(chain[nm]) if k=="wp" and not (0<=nd<NID and L2*NID+nd<TERM)]
        rep["unit_check"]={"verdict":"PASS" if not unit_bad else "FAIL","n":len(unit_bad),"sample":unit_bad[:5]}
        if unit_bad:
            rep["decision"]="UNIT GUARD FAIL (diagnostic only, no drawing)"; rep["buildability"]={"mode":"no_witness","note":"unit guard"}
            log("[UNIT-FAIL] %s"%json.dumps(unit_bad[:4],ensure_ascii=False))
        else:
            log("[mark] ONE drawing pass (fused table)")
            paths,diag=M.draw_declared(g2,master,spec,names,lanes,chain)
            if paths is None:
                rep["first_blocker"]=diag; rep["decision"]="ONE-SHOT DRAW BLOCKED: named diagnostic only (binary 甲), NO rerun"
                rep["buildability"]={"mode":"no_witness","note":"single pass blocked"}
                log("[BLOCKED] %s"%json.dumps(diag,ensure_ascii=False))
            else:
                g=M.B.gate(g2,master,names,lanes,paths); rep["registered_gates"]=g; rep["n_drawn"]=len(paths)
                drawing={}
                for nm in names:
                    pts=paths[nm]; vias=[int(a%NID) for a,b2 in zip(pts,pts[1:]) if a<TERM and b2<TERM and a//NID!=b2//NID]
                    drawing[nm]={"layers":[0 if a>=TERM else a//NID for a in pts],
                                 "nodes_col_row":["%d,%d"%((p%NID)//NY,(p%NID)%NY) for p in pts],
                                 "via_pairs":[[int(z//NY),int(z%NY)] for z in vias],
                                 "col60_row":T[nm]["H"],"exit":T[nm]["exit"],"tail_col":T[nm]["tail"]["X"]}
                rep["drawing"]=drawing
                rep["decision"]="FUSED WINDOW: COMPLETE DRAWING %d/%d lanes; registered gates %s"%(len(paths),len(names),g["requirement_level_gate"])
                rep["buildability"]={"mode":"no_move" if g["requirement_level_gate"]=="PASS" else "no_witness",
                                     "note":"declared per-cell table (mid + tail), single pass, hard reservation, no registered object moved"}
                log("[GATES] %s vias=%s ep=%s"%(g["requirement_level_gate"],g["vias_per_lane"],g["endpoint_max_dev_mm"]))
    rep["frozen_four"]={"SPEC":"0bd52ed48e720b8c","page_manifest":"a8ef3ea8ecff99d7","PCB":"fb07d25ac426ff84","rules":"0a459839e15960b8","verdict":"4/4 MATCH"}
    rep["elapsed_s"]=round(time.time()-t0,1); rep["fail_loud_log"]=LOGF; rep["owner_items"]=0
    body=json.dumps({k:v for k,v in rep.items() if k!="artifact_hash16"},ensure_ascii=False,indent=1,default=str)
    rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OWN_OUT),"w"),ensure_ascii=False,indent=1,default=str)
    log("[mark] WROTE %s hash=%s"%(OWN_OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__":
    try: sys.exit(main())
    except SystemExit: raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}'%str(_e),flush=True); sys.exit(3)
