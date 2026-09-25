#!/usr/bin/env python3
"""K2 · R609 (#K2-233 drawing-layer fix): H itself staggered >=2 per layer (col60 slot row == H),
Xt chosen per lane by first-fit on the register free graph; then the narrowed de-dup gate. Read-only."""
import sys,os,json,types,importlib,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R609_H_STAGGERED_TABLE_v1.json"; LOGF="/tmp/opencode/r609/h.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
    r607=json.load(open("K2_R607_EXIT_SLOT_REASSIGNMENT_v1.json"))["assignment"]
    def on4(nm,st): return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0
    adj={nm:g2.build_lane(nm)["adj"] for nm in names}
    CL={nm:{L:set(u for u in adj[nm] if u<TERM and u//NID==L) for L in (0,1)} for nm in names}
    C0={nm:set(u for u in adj[nm] if u<TERM and u//NID==0) for nm in names}
    rep={"artifact":"k2_r609_h_staggered_table_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-233 fix: H itself staggered >=2 per layer (col60 slot row == H); Xt by first-fit on the register free graph; zero trials","construction_runs":0,"per_lane":{}}
    usedH={}; npass=0
    for nm in names:
        d=int(ent[nm]["d"]); east=(g2.grp[nm]=="east"); Y=(36 if east else int(l2[nm]["exit"])); L=on4(nm,0)
        cl=CL[nm][L]; cs=C0[nm]; Ly=on4(nm,1)
        ok=None
        for H in range(59,max(Y+2,39)-1,-1):
            if any(abs(H-h)<2 for h in usedH.get(L,[])): continue
            if not all(((L*NID+x*NY+H) in cl) for x in range(d,61)): continue
            cands=sorted(range(61,138), key=lambda c: -sum(1 for r in range(Y,H+1) if (c*NY+r) in cs))
            for Xt in cands:
                if not all((xx*NY+H) in cs for xx in range(61,Xt+1)): continue
                if not all((Xt*NY+rr) in cs for rr in range(Y+1,H)): continue
                ok=(H,Xt); break
            if ok: break
        if ok: usedH.setdefault(L,[]).append(ok[0]); npass+=1
        rep["per_lane"][nm]={"east":east,"Y":Y,"belt_layer":L,"col60_layer":Ly,"H":(ok[0] if ok else None),
                             "Xt":(ok[1] if ok else None),"via_ok":(on4(nm,0)!=on4(nm,1)),
                             "exit_cell":r607[nm.split("PCIE_UP_")[1]]["cell"],"verdict":("PASS" if ok else "NO_CHANNEL")}
    # de-dup gate (narrowed)
    g={}
    for nm,v in rep["per_lane"].items():
        g.setdefault(("col60",v["col60_layer"],v["H"]),[]).append(nm)
        g.setdefault(("exit",tuple(v["exit_cell"])),[]).append(nm)
    clash={str(k):[n.split("PCIE_UP_")[1] for n in v] for k,v in g.items() if len(v)>1}
    rep["dedup_gate"]={"verdict":("PASS" if not clash else "FAIL"),"clash":clash}
    rep["summary"]={"PASS":npass,"FAIL":len(names)-npass}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        v=rep["per_lane"][nm]
        log("%-10s %-4s Y=%2s L=%d H=%s Xt=%s exit=%s %s"%(nm.split("PCIE_UP_")[1],"east" if v["east"] else "west",v["Y"],v["belt_layer"],v["H"],v["Xt"],v["exit_cell"],v["verdict"]))
    log("DE-DUP %s %s"%(rep["dedup_gate"]["verdict"],json.dumps(clash,ensure_ascii=False)))
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
