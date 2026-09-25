#!/usr/bin/env python3
"""K2 · R602 (#K2-231 item (a)) -- READ-ONLY per-line CHANNEL table: choose (H, Xt) JOINTLY so that
the horizontal run on row H from col 60 to Xt and the vertical run on column Xt from H to Y are BOTH
legal, using the machine-verified free cells (no trials, no arithmetic guessing)."""
import sys,os,json,types,importlib,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R602_PERLINE_CHANNEL_TABLE_v1.json"; LOGF="/tmp/opencode/r602/ch.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
    CL={nm:{L:set(u for u in adj[nm] if u<TERM and u//NID==L) for L in (0,1)} for nm in names}
    C0={nm:set(u for u in adj[nm] if u<TERM and u//NID==0) for nm in names}
    rep={"artifact":"k2_r602_perline_channel_table_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-231 (a): per-line channel table; (H,Xt) jointly verified on the register free graph; zero trials","construction_runs":0,"per_lane":{}}
    npass=0
    for nm in names:
        d=int(ent[nm]["d"]); east=(g2.grp[nm]=="east"); Y=(36 if east else int(l2[nm]["exit"])); L=on4(nm,0)
        cl=CL[nm][L]; cs=C0[nm]
        best=None
        for H in range(59, max(Y,37), -1):
            if not all(((L*NID+x*NY+H) in cl) for x in range(d,61)): continue
            cands=sorted(range(61,138), key=lambda c: -sum(1 for r in range(Y,H+1) if (c*NY+r) in cs))
            for Xt in cands:
                if not all((xx*NY+H) in cs for xx in range(61,Xt+1)): continue     # horizontal on row H
                if not all((Xt*NY+rr) in cs for rr in range(Y+1,H)): continue       # vertical on col Xt
                best=(H,Xt); break
            if best: break
        if best: npass+=1
        rep["per_lane"][nm]={"east":east,"Y":Y,"belt_layer":L,"H":(best[0] if best else None),
                             "Xt":(best[1] if best else None),"verdict":("PASS" if best else "NO_CHANNEL")}
    rep["summary"]={"n_lanes":len(names),"PASS":npass,"FAIL":len(names)-npass}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        v=rep["per_lane"][nm]
        log("%-10s %-4s Y=%2s L=%d H=%s Xt=%s %s"%(nm.split("PCIE_UP_")[1],"east" if v["east"] else "west",v["Y"],v["belt_layer"],v["H"],v["Xt"],v["verdict"]))
    log("SUMMARY %s"%json.dumps(rep["summary"],ensure_ascii=False)); log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
