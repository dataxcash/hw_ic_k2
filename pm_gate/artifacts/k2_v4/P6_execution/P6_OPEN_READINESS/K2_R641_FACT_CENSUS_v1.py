#!/usr/bin/env python3
"""K2 R641 · ONE read-only fact census for the 3 remainder lanes (#K2-243 sec.5).
Self-test first (fail-loud), then ONE constructive pass of fact extraction. No search of solutions."""
import sys,os,json,types,importlib,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM,NX=W.NID,W.NY,W.TERM_BASE,W.NX
g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full")
names=list(g2.names)
T=json.load(open(os.path.join(HERE,"K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"]
R638=json.load(open(os.path.join(HERE,"K2_R638_HUMANPATH_ONESHOT_v1.json")))
ADJ={nm:g2.build_lane(nm)["adj"] for nm in names}
FREE={nm:({u for u in ADJ[nm] if u<NID},{u for u in ADJ[nm] if NID<=u<2*NID}) for nm in names}
VIAOK={nm:g2._via_ok(nm) for nm in ("PCIE_UP_OUT0_P_J2","PCIE_UP_OUT6_N_J2","PCIE_UP_OUT7_P_J2")}
EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
P=lambda c,r: c*NY+r
def free(nm,c,r,L): return (L*NID+P(c,r)) in FREE[nm][L]   # node id = layer*NID + col*NY + row (self-test caught the missing offset)
def via(nm,c,r): return bool(VIAOK[nm][P(c,r)])
# ---- SELF-TEST (fail-loud) ----
errs=[]
if len(set(EX[n] for n in names))!=len(names): errs.append("R613 exit cells are not distinct")
if R638["n_drawn"]!=13: errs.append("R638 n_drawn != 13")
if set(R638["blocked"])!={"OUT0_P_J2","OUT6_N_J2","OUT7_P_J2"}: errs.append("R638 blocked set unexpected")
for n in names:
    if not free(n,EX[n][0],EX[n][1],int(T[n]["exit_layer"])): errs.append("exit cell of %s not free on its exit layer"%n)
if errs:
    print("FAIL_LOUD self-test:",errs); sys.exit(3)
print("SELF-TEST PASS")
out={"artifact":"k2_r641_fact_census_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),"construction_runs":0,
     "authority":"#K2-243 sec.5: one read-only fact census feeding the single constructive determination (no solution search)","per_lane":{}}
for nm in ("PCIE_UP_OUT0_P_J2","PCIE_UP_OUT6_N_J2","PCIE_UP_OUT7_P_J2"):
    k=nm.split("PCIE_UP_")[1]; v=T[nm]; L=int(v["exit_layer"]); Y=(36 if v["east"] else int(EX[nm][1]))
    d={"east":bool(v["east"]),"Y":Y,"exit":list(EX[nm]),"exit_layer":L,"belt_layer":v["belt_layer"],
       "col60_layer":v["col60_layer"],"H613":v["H"],"Xt613":v["Xt"],
       "r638_blocked":R638["blocked"].get(k)}
    # full-span rows: cols 61..114 free on layer L
    d["full_rows_L0"]=[H for H in range(5,64) if all(free(nm,x,H,0) for x in range(61,115))]
    d["full_rows_L1"]=[H for H in range(5,64) if all(free(nm,x,H,1) for x in range(61,115))]
    # descent columns: for col in 115..137, the free rows on L0/L1 inside [min(Y,59)..max(Y,59)]
    lo,hi=(min(Y,59),max(Y,59))
    cols={}
    for c in list(range(115,138))+[61,114,116,117,118,119]:
        r0=[r for r in range(lo,hi+1) if free(nm,c,r,0)]
        r1=[r for r in range(lo,hi+1) if free(nm,c,r,1)]
        cols[c]={"n_free_L0":len(r0),"n_free_L1":len(r1)}
    d["descent_cols_summary"]={str(c):cols[c] for c in sorted(cols)}
    d["descent_cols_full_run_L0"]=[c for c in sorted(cols) if cols[c]["n_free_L0"]==hi-lo+1]
    d["descent_cols_full_run_L1"]=[c for c in sorted(cols) if cols[c]["n_free_L1"]==hi-lo+1]
    others=[EX[o] for o in names if o!=nm]
    def manh(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
    if nm.endswith("OUT0_P_J2"):
        d["row36_candidates"]=[{"cell":[c,36],"free_L0":free(nm,c,36,0),"free_L1":free(nm,c,36,1),
                                "via_legal":via(nm,c,36),"distinct":all((c,36)!=e for e in others),
                                "manh_to_613_exit":manh((c,36),(127,36))} for c in range(115,138)]
    if nm.endswith("OUT6_N_J2"):
        d["row47_status"]=[{"col":c,"free_L0":free(nm,c,47,0),"free_L1":free(nm,c,47,1)} for c in range(60,138)]
    if nm.endswith("OUT7_P_J2"):
        d["col_candidates_for_vertical"]=[{"col":c,"free_rows_L0":[r for r in range(20,41) if free(nm,c,r,0)],
                                           "full_run_L0":all(free(nm,c,r,0) for r in range(20,41)),
                                           "full_run_L1":all(free(nm,c,r,1) for r in range(20,41))} for c in list(range(61,115))+list(range(120,136))]
    out["per_lane"][k]=d
body=json.dumps(out,ensure_ascii=False,indent=1,default=str); out["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
json.dump(out,open("K2_R641_FACT_CENSUS_v1.json","w"),ensure_ascii=False,indent=1,default=str)
print("hash",out["artifact_hash16"])
for k in out["per_lane"]:
    d=out["per_lane"][k]
    print("==",k,"Y=",d["Y"],"exit=",d["exit"],"L",d["exit_layer"],"col60",d["col60_layer"],"blk",d["r638_blocked"] and (d["r638_blocked"]["segment_index"],d["r638_blocked"]["from_col_row"],d["r638_blocked"]["to_col_row"]))
    print("   full_rows_L0",d["full_rows_L0"][:14],"...n=",len(d["full_rows_L0"]))
    print("   full_rows_L1",d["full_rows_L1"][:14],"...n=",len(d["full_rows_L1"]))
    print("   descent cols full-run L0:",d["descent_cols_full_run_L0"])
    print("   descent cols full-run L1:",d["descent_cols_full_run_L1"])
print("OWNER-ITEMS: 0")
