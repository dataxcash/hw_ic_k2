#!/usr/bin/env python3
"""K2 · R587 (#K2-227 class C) -- READ-ONLY attribution: for every lane print the SPEC exit/pad waypoint
node ids and, if terminal, their adjacent lattice cells (layer/col/row) + the lane's src/snk terminals.
Purpose: learn the true ACCESS GEOMETRY of the registered exit (cell vs leg, which layer, where)."""
import sys,os,json,types,importlib,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R587_EXIT_ACCESS_CENSUS_v1.json"; LOGF="/tmp/opencode/r587/ex.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
def log(m): open(LOGF,"a").write(str(m)+"\n"); print(str(m),flush=True)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM=W.NID,W.NY,W.TERM_BASE
def main():
    open(LOGF,"w").close()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json")); l2=json.load(open("K2_R550_L2_SLOT_TABLE_v1.json"))["table"]
    adj={nm:g2.build_lane(nm)["adj"] for nm in names}
    rep={"artifact":"k2_r587_exit_access_census_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-227 class C layered read-only attribution: exit access geometry","construction_runs":0,"per_lane":{}}
    for nm in names:
        A=adj[nm]; east=(g2.grp[nm]=="east")
        def desc(u):
            if u<TERM: return {"node":int(u),"kind":"lattice","col":int((u%NID)//NY),"row":int((u%NID)%NY),"layer":int(u//NID)}
            kids=[v%NID for (v,_w) in A.get(u,()) if v<TERM]
            return {"node":int(u),"kind":"terminal","idx":int(u-TERM),
                    "adj_cells":sorted((int(c//NY),int(c%NY),int((A and 0) or 0)) for c in kids)[:6],
                    "adj_cols":sorted(set(int(c//NY) for c in kids))[:6],
                    "adj_rows":sorted(set(int(c%NY) for c in kids))[:6]}
        wp={}
        for w in spec["per_lane"][nm]["waypoints"]:
            if w.get("node") is not None: wp[w["kind"]]=int(w["node"])
        ex=(int(l2[nm]["exit"])*NY+36) if east else (114*NY+int(l2[nm]["exit"]))
        rep["per_lane"][nm]={"east":east,"src":desc(A and g2.build_lane(nm)["src"]),"snk":desc(g2.build_lane(nm)["snk"]),
            "spec_nodes":{k:desc(v) for k,v in wp.items()},
            "l2_exit_cell":{"col":int(ex//NY),"row":int(ex%NY),"in_L0":(ex in {u%NID for u in A if u<TERM and u//NID==0}),
                            "in_L1":(ex in {u%NID for u in A if u<TERM and u//NID==1})}}
    rep["elapsed_s"]=round(time.time()-time.time()+time.time()-time.time(),1)
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        p=rep["per_lane"][nm]; ex=p["l2_exit_cell"]
        log("%-10s %-4s l2_exit=(%d,%d) inL0=%s inL1=%s | exit_wp=%s | pad_wp=%s | snk_adj_cols=%s snk_adj_rows=%s"%(
            nm.split("PCIE_UP_")[1],"east" if p["east"] else "west",ex["col"],ex["row"],ex["in_L0"],ex["in_L1"],
            json.dumps(p["spec_nodes"].get("exit_wall_gap") or p["spec_nodes"].get("exit_gate_col"),ensure_ascii=False),
            json.dumps(p["spec_nodes"].get("pad_run"),ensure_ascii=False),
            p["snk"]["adj_cols"][:5] if p["snk"]["kind"]=="terminal" else "-",
            p["snk"]["adj_rows"][:5] if p["snk"]["kind"]=="terminal" else "-"))
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
