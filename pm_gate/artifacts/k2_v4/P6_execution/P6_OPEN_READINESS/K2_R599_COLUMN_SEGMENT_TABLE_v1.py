#!/usr/bin/env python3
"""K2 · R599 (#K2-231 drawing layer) -- READ-ONLY per-line AVAILABLE COLUMN-SEGMENT table:
for each lane, for each candidate column, the maximal contiguous FREE row segments on layer 0
(and on the lane's own mid layer), so that G1'' windows can be DERIVED (no arithmetic guessing)."""
import sys,os,json,types,importlib,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R599_COLUMN_SEGMENT_TABLE_v1.json"; LOGF="/tmp/opencode/r599/seg.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
    rep={"artifact":"k2_r599_column_segment_table_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-231 drawing layer: per-line available column-segment table (col x free row-segment, machine-checked)","construction_runs":0,"per_lane":{}}
    for nm in names:
        d=int(ent[nm]["d"]); east=(g2.grp[nm]=="east"); Y=(36 if east else int(l2[nm]["exit"]))
        # belt row H (S2 rule): largest row <=59 free across [d,60] on the COMB layer with a free descent
        L=on4(nm,0)
        H=None
        for h in range(59,37,-1):
            if all(((L*NID+x*NY+h) in (lambda s: s)(set(u for u in adj[nm] if u<TERM and u//NID==L))) for x in range(d,61)): H=h; break
        cs=C0[nm]; segs={}
        for c in range(61,138):
            run=[]
            for r in range(Y, (H or 59)+1):
                if (c*NY+r) in cs: run.append(r)
                else:
                    if run: segs.setdefault(c,[]).append((run[0],run[-1]))
                    run=[]
            if run: segs.setdefault(c,[]).append((run[0],run[-1]))
        best=sorted(((c,max((b-a+1) for a,b in v)) for c,v in segs.items()), key=lambda t:-t[1])[:3]
        rep["per_lane"][nm]={"east":east,"Y":Y,"H":H,"n_cols_with_segment":len(segs),
                             "top3_col_maxseglen":[[c,l] for c,l in best]}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        v=rep["per_lane"][nm]
        log("%-10s %-4s Y=%2s H=%s ncols=%3d top3(col,maxseg)=%s"%(nm.split("PCIE_UP_")[1],"east" if v["east"] else "west",v["Y"],v["H"],v["n_cols_with_segment"],v["top3_col_maxseglen"]))
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
