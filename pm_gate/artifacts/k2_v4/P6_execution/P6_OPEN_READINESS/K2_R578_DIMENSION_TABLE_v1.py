#!/usr/bin/env python3
"""K2 · R578 (#K2-225) -- READ-ONLY per-line DIMENSIONED capacity table (constitution art.16 sec.3 item 3'):
for every lane, the binding tail leg's REQUIRED span vs the AVAILABLE contiguous free run (derived by rule,
not by trial). No construction, no drawing."""
import sys,os,json,types,importlib,time,hashlib
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R578_DIMENSION_TABLE_v1.json"; LOGF="/tmp/opencode/r578/dim.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
    rep={"artifact":"k2_r578_dimension_table_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-225: per-line dimensioned capacity table (available >= required, derived by rule, no trial)",
         "rule":"for each lane: H = own belt row (S2); horizontal span = Xt-60 (Xt=110 east / 106 west); vertical span rows [Y+1..H-1] -> needed = H-Y-1; AVAILABLE = max contiguous free run on layer 0 over columns 61..113 (derived, not tried)","solve_calls":0,"per_lane":{}}
    npass=0
    for nm in names:
        d=int(ent[nm]["d"]); top=int(ent[nm]["top"]); east=(g2.grp[nm]=="east"); exitc=int(l2[nm]["exit"])
        Y=36 if east else exitc; L=on4(nm,0); cl=CL[nm][L]
        H=None
        for h in range(59,37,-1):
            if all(((L*NID+x*NY+h) in cl) for x in range(d,61)) and all(((L*NID+d*NY+r) in cl) for r in range(top,h+1)): H=h; break
        need=(H-Y-1) if H else None
        best=0; bestc=None
        if need is not None and need>0:
            for c in range(61,114):
                run=0; mx=0
                for r in range(Y+1,H):
                    if (0*NID+c*NY+r) in C0[nm]: run+=1; mx=max(mx,run)
                    else: run=0
                if mx>best: best=mx; bestc=c
        ok=(need is not None and need>0 and best>=need)
        if ok: npass+=1
        rep["per_lane"][nm]={"L":L,"d":d,"H":H,"Y":Y,"east":east,"required_vertical_span":need,
                             "available_max_contiguous_free_run":best,"column":bestc,"margin":(best-need if need else None),
                             "verdict":"PASS" if ok else "FAIL"}
    rep["summary"]={"n_lanes":len(names),"PASS":npass,"FAIL":len(names)-npass,
                    "note":"FAIL = available < required for the single-column vertical sub-route; a multi-stage staircase would split the span (not yet dimensioned)"}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        v=rep["per_lane"][nm]
        log("%-10s %-4s H=%s Y=%2s req=%3s avail=%3s col=%s margin=%s %s"%(nm.split("PCIE_UP_")[1],"east" if v["east"] else "west",v["H"],v["Y"],v["required_vertical_span"],v["available_max_contiguous_free_run"],v["column"],v["margin"],v["verdict"]))
    log("SUMMARY %s"%json.dumps(rep["summary"],ensure_ascii=False))
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
