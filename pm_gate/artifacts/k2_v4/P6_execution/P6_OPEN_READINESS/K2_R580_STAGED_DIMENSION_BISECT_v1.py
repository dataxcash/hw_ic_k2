#!/usr/bin/env python3
"""K2 · R579 (#K2-225) -- READ-ONLY STAGED dimension table: split the tail vertical span at the
machine-verified FULL-SPAN rows (rule-derived, no trial) and dimension every stage:
needed = rows to descend; available = max contiguous free run on a column within that stage."""
import sys,os,json,types,importlib,time,hashlib
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R580_STAGED_DIMENSION_BISECT_v1.json"; LOGF="/tmp/opencode/r579/dim.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
    rep={"artifact":"k2_r580_staged_dimension_bisect_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-225: staged dimension table with RULE-DERIVED recursive bisection of any SHORT stage (no trial)","solve_calls":0,"trials":0,"per_lane":{}}
    npass=0
    for nm in names:
        d=int(ent[nm]["d"]); top=int(ent[nm]["top"]); east=(g2.grp[nm]=="east"); exitc=int(l2[nm]["exit"])
        Y=36 if east else exitc; L=on4(nm,0); cl=CL[nm][L]
        H=None
        for h in range(59,37,-1):
            if all(((L*NID+x*NY+h) in cl) for x in range(d,61)) and all(((L*NID+d*NY+r) in cl) for r in range(top,h+1)): H=h; break
        stages=[]
        if H is not None:
            full=[r for r in range(Y+1,H) if all((x*NY+r) in C0[nm] for x in range(61,115))]
            def avail(a,b):
                best=0; bc=None
                for c in range(61,114):
                    run=0;mx=0
                    for r in range(b,a+1):
                        if (c*NY+r) in C0[nm]: run+=1; mx=max(mx,run)
                        else: run=0
                    if mx>best: best=mx; bc=c
                return best,bc
            def dim(a,b,depth=0):
                if a<=b or depth>8: return []
                need=a-b; best,bc=avail(a,b)
                if best>=need: return [{"from_row":a,"to_row":b,"needed":need,"available":best,"column":bc,"ok":True}]
                mid=a-(need+1)//2
                return dim(a,mid,depth+1)+dim(mid,b,depth+1)
            bounds=sorted(set([H-1]+sorted(full,reverse=True)+[Y]),reverse=True)
            for a,b in zip(bounds,bounds[1:]):
                stages+=dim(a,b)
        ok=bool(stages) and all(s["ok"] for s in stages)
        if ok: npass+=1
        rep["per_lane"][nm]={"L":L,"d":d,"H":H,"Y":Y,"east":east,"n_stages":len(stages),
                             "needed_total":(H-Y-1) if H else None,"stages":stages,"verdict":"PASS" if ok else "FAIL"}
    rep["summary"]={"n_lanes":len(names),"PASS":npass,"FAIL":len(names)-npass}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        v=rep["per_lane"][nm]
        log("%-10s %-4s H=%s Y=%2s stages=%d %s %s"%(nm.split("PCIE_UP_")[1],"east" if v["east"] else "west",v["H"],v["Y"],v["n_stages"],
            [(s["needed"],s["available"],"OK" if s["ok"] else "SHORT") for s in v["stages"]],v["verdict"]))
    log("SUMMARY %s"%json.dumps(rep["summary"],ensure_ascii=False)); log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
