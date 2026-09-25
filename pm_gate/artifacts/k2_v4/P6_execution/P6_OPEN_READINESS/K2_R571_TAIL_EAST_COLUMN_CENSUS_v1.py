#!/usr/bin/env python3
"""K2 · R571 -- READ-ONLY census of the east-of-wall columns (cols 115..137) needed to complete
the premise-v4 tail allocation law. No construction, no drawing, no rerun."""
import sys, os, json, types, importlib, time, hashlib
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R571_TAIL_EAST_COLUMN_CENSUS_v1.json"; LOGF="/tmp/opencode/r571/census.log"
os.makedirs(os.path.dirname(LOGF),exist_ok=True)
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
ST=["COMB","BELT","WALL","FIELD"]
def main():
    open(LOGF,"w").close(); t0=time.time()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full")
    names=list(g2.names)
    master=json.load(open(os.path.join(HERE,"K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    l2=json.load(open(os.path.join(HERE,"K2_R550_L2_SLOT_TABLE_v1.json")))["table"]
    def on4(nm,st): return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0
    adj={nm:g2.build_lane(nm)["adj"] for nm in names}
    CELL={(nm,L):set(u for u in adj[nm] if u<TERM and u//NID==L) for nm in names for L in (0,1)}
    rep={"artifact":"k2_r571_tail_east_column_census_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"read-only east-of-wall column census for premise v4; no construction run","per_lane":{}}
    for nm in names:
        east=(g2.grp[nm]=="east"); exitc=int(l2[nm]["exit"])
        row_t=36 if east else exitc
        d={"east":east,"exit_col_row":[(exitc if east else 114),row_t]}
        for L in (0,1):
            cs=CELL[(nm,L)]
            cols_north=[c for c in range(115,138) if all((c*NY+r) in cs for r in range(row_t,60))]
            cols_full=[c for c in range(115,138) if all((c*NY+r) in cs for r in range(row_t,60)) and all((c*NY+r) in cs for r in range(row_t,37))]
            rows_west=[r for r in range(7,37) if all((x*NY+r) in cs for x in range(114,exitc+1))] if east else []
            d["L%d"%L]={"cols_115_137_free_rowT_59":cols_north,"n":len(cols_north),
                        "rows_7_36_free_114_exit":rows_west}
        rep["per_lane"][nm]=d
    for L in (0,1):
        gg=[n for n in names]
        rep.setdefault("union",{})["L%d"%L]=sorted({c for n in gg for c in rep["per_lane"][n]["L%d"%L]["cols_115_137_free_rowT_59"]})
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        p=rep["per_lane"][nm]
        log("%-10s %-4s exit=%s | L0 cols=%2d %s | L1 cols=%2d %s | rows_7_36_free=%s"%(
            nm.split("PCIE_UP_")[1],"east" if p["east"] else "west",p["exit_col_row"],
            p["L0"]["n"],p["L0"]["cols_115_137_free_rowT_59"][:6],p["L1"]["n"],p["L1"]["cols_115_137_free_rowT_59"][:6],
            p["L0"]["rows_7_36_free_114_exit"][:4]))
    log("union L0=%s"%rep["union"]["L0"][:24]); log("union L1=%s"%rep["union"]["L1"][:24])
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
