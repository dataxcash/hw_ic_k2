#!/usr/bin/env python3
"""K2 · R581 (#K2-225) -- READ-ONLY COMPLETE staged dimension table: every stage dimensioned in BOTH
the horizontal run (on its cut row) and the vertical run (on its derived column); columns derived by rule
(first-fit over a sorted candidate list), take-and-register; zero trials."""
import sys,os,json,types,importlib,time,hashlib
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R582_FULL_STAGED_TABLE_v2.json"; LOGF="/tmp/opencode/r581/dim.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
def log(m): open(LOGF,"a").write(str(m)+"\n"); print(str(m),flush=True)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM=W.NID,W.NY,W.TERM_BASE; ST=["COMB","BELT","WALL","FIELD"]
def main():
    open(LOGF,"w").close()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    master=json.load(open("K2_R529_WOVEN_COMPLETE_MASTER_v1.json"))
    ent=json.load(open("K2_R550_CONSTRUCTION_DRAWING_v1.json"))["entrance_channel_table"]
    l2=json.load(open("K2_R550_L2_SLOT_TABLE_v1.json"))["table"]
    def on4(nm,st): return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0
    adj={nm:g2.build_lane(nm)["adj"] for nm in names}
    C0={nm:set(u for u in adj[nm] if u<TERM and u//NID==0) for nm in names}
    CL={nm:{L:set(u for u in adj[nm] if u<TERM and u//NID==L) for L in (0,1)} for nm in names}
    rep={"artifact":"k2_r582_full_staged_table_v2","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-225: COMPLETE staged dimension table v2 - stage columns derived by proximity to the EXIT column (rule, no trial) so the final run is minimal","solve_calls":0,"trials":0,"per_lane":{}}
    npass=0
    for nm in names:
        d=int(ent[nm]["d"]); top=int(ent[nm]["top"]); east=(g2.grp[nm]=="east"); exitc=int(l2[nm]["exit"])
        Y=36 if east else exitc; Econ=(exitc if east else 114); L=on4(nm,0); cl=CL[nm][L]; c0=C0[nm]
        H=None
        for h in range(59,37,-1):
            if all(((L*NID+x*NY+h) in cl) for x in range(d,61)) and all(((L*NID+d*NY+r) in cl) for r in range(top,h+1)): H=h; break
        full=[r for r in range(Y+1,H) if all((x*NY+r) in c0 for x in range(61,115))] if H else []
        rows=sorted(set([H-1]+sorted(full,reverse=True)+[Y]),reverse=True)
        stages=[]; cur=60; ok=True; used=set()
        for a,b in zip(rows,rows[1:]):
            vneed=a-b
            pick=None
            # derive column by rule: first-fit over columns ordered by proximity to 110
            for X in sorted(list(range(61,114))+([Econ] if Econ<114 else []),key=lambda c:abs(c-Econ)):
                hrun=[(c,a) for c in (range(cur+1,X+1) if X>=cur else range(X,cur))]
                hok=all((c*NY+a) in c0 and (c*NY+a) not in used for (c,_) in hrun)
                vrun=[(X,r) for r in range(b+1,a+1)]
                vok=all((X*NY+r) in c0 and (X*NY+r) not in used for (_,r) in vrun)
                if hok and vok: pick=(X,hrun,vrun); break
            if pick is None:
                stages.append({"from_row":a,"to_row":b,"needed_vertical":vneed,"verdict":"NO_COLUMN"}); ok=False; break
            X,hrun,vrun=pick
            for cell in hrun+vrun: used.add(cell)
            stages.append({"from_row":a,"to_row":b,"cut_row":a,"column":X,"horizontal_span":len(hrun),
                           "vertical_needed":vneed,"vertical_available":len(vrun),"verdict":"PASS"})
            cur=X
        if ok and H is not None:
            hfin=[(c,Y) for c in (range(cur+1,Econ+1) if Econ>=cur else range(Econ,cur))]
            if all((c*NY+Y) in c0 and (c*NY+Y) not in used for (c,_) in hfin):
                for cell in hfin: used.add(cell)
                stages.append({"cut_row":Y,"column":Econ,"horizontal_span":len(hfin),"final":True,"verdict":"PASS"})
            else:
                stages.append({"cut_row":Y,"verdict":"FINAL_RUN_BLOCKED"}); ok=False
        if ok: npass+=1
        rep["per_lane"][nm]={"L":L,"H":H,"Y":Y,"east":east,"n_stages":len(stages),"stages":stages,"verdict":"PASS" if ok else "FAIL"}
    rep["summary"]={"n_lanes":len(names),"PASS":npass,"FAIL":len(names)-npass}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        v=rep["per_lane"][nm]
        log("%-10s %-4s H=%s Y=%2s stages=%2d %s"%(nm.split("PCIE_UP_")[1],"east" if v["east"] else "west",v["H"],v["Y"],v["n_stages"],
            [(s.get("horizontal_span"),s.get("vertical_needed"),s.get("column"),s["verdict"]) for s in v["stages"]][:6]))
    log("SUMMARY %s"%json.dumps(rep["summary"],ensure_ascii=False)); log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
