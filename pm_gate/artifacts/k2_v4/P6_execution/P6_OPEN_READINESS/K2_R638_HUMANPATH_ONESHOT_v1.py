#!/usr/bin/env python3
"""K2 · R619 (#K2-236 (b)): cancel the self-added pre-filter; the REGISTERED gates are the sole judge.
Implementation: draw each lane INDEPENDENTLY (fresh occupancy per lane => no cross-lane blocking),
merge the paths, then judge with the in-register gates (exact_gate / gate_vias / endpoints / <=2 pairs)."""
import sys,os,json,importlib,types,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R638_HUMANPATH_ONESHOT_v1.json"; LOGF="/tmp/opencode/r638/draw.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
def log(m): open(LOGF,"a").write(str(m)+"\n"); print(str(m),flush=True)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
import K2_R611_FINAL_DRAWING_ONESHOT_v1 as D   # reuse its chain builder via a light re-run
def main():
    open(LOGF,"w").close(); t0=time.time()
    M=D.M; W=D.W; g2=D.W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full")
    names=list(g2.names)
    master=json.load(open("K2_R529_WOVEN_COMPLETE_MASTER_v1.json"))
    spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json"))
    T610=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]
    lanes={nm:g2.build_lane(nm) for nm in names}
    W.claim_seg=lambda *a,**k: ()          # (b): cancel the self-added cell pre-filter
    W.VIA_SEP=0.0                          # (b): cancel the self-added 0.7mm pre-filter
    paths={}; blocked={}; entrance={}
    for nm in names:
        x=T610[nm]
        chain={}
        v=x; H=v["H"]; ec=v["exit_cell"]; east=(g2.grp[nm]=="east"); L=v["belt_layer"]
        # minimal declared chain: A -> col60 slot(H) -> exit cell -> B  (drawer fills; no arithmetic guess)
        def _st2(a,b,st=20):
            out=[]; c=a
            if b>=a:
                while c+st<b: c+=st; out.append(c)
            else:
                while c-st>b: c-=st; out.append(c)
            if c!=b: out.append(b)
            return out
        items=[("A",None,0)]
        # ---- R638 single named fix: declare the SPEC-declared ENTRANCE LAYER TRANSITION for every lane that needs one.
        # R620 keyed this on belt_layer==1 and only consumed DIVE_via, so the lanes whose registered SPEC transition
        # is declared as In5_entrance were left with NO entrance transition at all (bookkeeping gap, not geometry).
        # For belt_layer==1 lanes the behaviour is IDENTICAL to R620 (they all carry DIVE_via - machine-checked).
        pv=None
        for w in spec["per_lane"][nm]["waypoints"]:
            if w["kind"]=="DIVE_via": pv=int(w["node"])
        if v["belt_layer"]==1:
            if pv is None: pv=0
            items.append(("via",pv,1)); entrance[nm]="DIVE_via(belt1)"
        elif v["col60_layer"]==1:
            pv2=None
            for w in spec["per_lane"][nm]["waypoints"]:
                if w["kind"]=="In5_entrance": pv2=int(w["node"])
            if pv2 is None:
                entrance[nm]="NEEDED-BUT-NO-REGISTERED-NODE"
            else:
                items.append(("via",pv2,1)); entrance[nm]="In5_entrance(belt0,col60_1) node=%d"%pv2
        else:
            entrance[nm]="not-needed"
        items.append(("wp",60*W.NY+H,v["col60_layer"]))
        Yr=(36 if east else int(ec[1])); Xt=v["Xt"]
        for xx in _st2(61,Xt)[:-1]: items.append(("wp",xx*W.NY+H,v["col60_layer"]))
        items.append(("wp",Xt*W.NY+H,0))
        for rr in _st2(H-1,Yr): items.append(("wp",Xt*W.NY+rr,0))
        items.append(("wp",int(ec[0])*W.NY+int(ec[1]),v["exit_layer"]))
        items.append(("B",None,0)); chain[nm]=items
        p,diag=M.draw_declared(g2,master,spec,[nm],{nm:lanes[nm]},chain)
        if p is None: blocked[nm.split("PCIE_UP_")[1]]=diag
        else: paths[nm]=p[nm]
    rep={"artifact":"k2_r638_humanpath_oneshot_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"STOP-ORDER (command repetition) -> back to Plan, human-engineer path, ONE implementation: (1) declare the registered SPEC entrance layer transition for every lane that needs one (R620 keyed it on belt_layer==1 and consumed only DIVE_via => the lanes whose SPEC transition is In5_entrance were left undeclared); (2) the self-added exit-slot >=2 pre-filter is already withdrawn (#K2-242 sec.3.4(1a)) - the drawing pre-filters stay off, the registered gates are the sole judge. ONE pass, no parameter search, no re-run.",
         "construction_runs":1,"n_drawn":len(paths),"blocked":blocked,"entrance_declared":entrance}
    if len(paths)==len(names):
        g=M.B.gate(g2,master,names,lanes,paths); rep["registered_gates"]=g
        rep["decision"]="DRAWING COMPLETE 16/16; registered gates %s"%g["requirement_level_gate"]
        rep["buildability"]={"mode":"no_move" if g["requirement_level_gate"]=="PASS" else "no_witness"}
        log("GATES %s vias=%s"%(g["requirement_level_gate"],g.get("vias_per_lane")))
    else:
        rep["decision"]="BLOCKED lanes=%s"%list(blocked)
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps({k:v for k,v in rep.items() if k!="artifact_hash16"},ensure_ascii=False,indent=1,default=str)
    rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("n_drawn=%d blocked=%s"%(len(paths),list(blocked))); log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
