#!/usr/bin/env python3
"""K2 · R570 -- READ-ONLY tail (S4) free-band census for premise v4 (tail allocation law).
No construction, no drawing, no rerun."""
import sys, os, json, types, importlib, time, hashlib
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R570_TAIL_BAND_CENSUS_v1.json"; LOGF="/tmp/opencode/r570/census.log"
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
    rep={"artifact":"k2_r570_tail_band_census_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"read-only S4 tail band census for premise v4; no construction run","per_lane":{}}
    for nm in names:
        Lt=on4(nm,1); Lx=on4(nm,2); east=(g2.grp[nm]=="east")
        ex=(int(l2[nm]["exit"])*NY+36) if east else (114*NY+int(l2[nm]["exit"]))
        d={}
        for tag,L in (("col60_layer",Lt),("exit_layer",Lx)):
            cs=CELL[(nm,L)]
            rows_full=[r for r in range(7,60) if all((x*NY+r) in cs for x in range(60,115))]
            cols_full=[c for c in range(61,114) if all((c*NY+r) in cs for r in range(7,60))]
            rows_hi=[r for r in range(36,60) if all((x*NY+r) in cs for x in range(60,115))]
            d[tag]={"rows_free_60_114":rows_full,"n":len(rows_full),
                    "cols_free_7_59":cols_full[:14],"n_cols":len(cols_full),
                    "rows_hi_36_59":rows_hi}
        d.update({"east":east,"exit_col_row":[ex//NY,ex%NY],"B_col_row":[int(round((g2.B[nm][0]-W.X0)/W.P)),int(round((g2.B[nm][1]-W.Y0)/W.P))],
                  "exit_cell_free_Lx":(ex in CELL[(nm,Lx)]),"exit_cell_free_Lt":(ex in CELL[(nm,Lt)])})
        rep["per_lane"][nm]=d
    for L in (0,1):
        gg=[n for n in names if on4(n,1)==L]
        rep.setdefault("per_layer",{})["L%d"%L]={"lanes":[n.split("PCIE_UP_")[1] for n in gg],
            "union_cols_free_7_59":sorted({c for n in gg for c in rep["per_lane"][n]["col60_layer"]["cols_free_7_59"]})}
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        p=rep["per_lane"][nm]
        log("%-10s Lt=%d Lx=%d %-4s exit=%s B=%s | rows60_114=%2d %s | cols7_59=%2d %s | hi=%2d"%(
            nm.split("PCIE_UP_")[1],on4(nm,1),on4(nm,2),"east" if p["east"] else "west",p["exit_col_row"],p["B_col_row"],
            p["col60_layer"]["n"],p["col60_layer"]["rows_free_60_114"][:5],p["col60_layer"]["n_cols"],
            p["col60_layer"]["cols_free_7_59"][:5],len(p["col60_layer"]["rows_hi_36_59"])))
    for L in (0,1):
        log("L%d union_cols_free_7_59=%s"%(L,rep["per_layer"]["L%d"%L]["union_cols_free_7_59"][:24]))
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
