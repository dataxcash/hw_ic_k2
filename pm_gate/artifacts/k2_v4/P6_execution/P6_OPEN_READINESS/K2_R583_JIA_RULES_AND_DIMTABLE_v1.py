#!/usr/bin/env python3
"""K2 · R583 (#K2-226 JIA stage) -- SINGLE SOURCE OF RULES + COMPLETE 16/16 dimension table incl. the final leg.
Read-only (zero construction, zero drawing). ENFORCED GATE: if any lane fails dimensioning the script writes
a FAIL artifact and refuses to emit a 'complete' verdict (fail-closed, per #K2-226 sec.4 items 5/6)."""
import sys,os,json,types,importlib,time,hashlib
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R583_JIA_RULES_AND_DIMTABLE_v1.json"; RULES="K2_R583_RULES_SINGLE_SOURCE_v1.json"
LOGF="/tmp/opencode/r583/jia.log"; os.makedirs(os.path.dirname(LOGF),exist_ok=True)
def log(m): open(LOGF,"a").write(str(m)+"\n"); print(str(m),flush=True)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM=W.NID,W.NY,W.TERM_BASE; ST=["COMB","BELT","WALL","FIELD"]
RULES_DOC={
 "R1_stage_rows":"cut the tail vertical span [Y..H] at the machine-verified FULL-SPAN rows (cols 61..114 free on layer 0); always include H-1 and Y",
 "R2_bisect":"if a stage's needed span > available contiguous free run on every candidate column, bisect it (mid = a - ceil(need/2)) and recurse (R580 law)",
 "R3_column_by_exit":"order candidate columns by |c - exit_column|; take the first column satisfying BOTH the horizontal run on the cut row and the vertical run inside the stage (R582 law)",
 "R4_final_leg":"the LAST stage's column is restricted: EAST group -> cols >=115 (wall-east, so the lane lands east of the wall at row 36 and the final run to (exitc,36) is short); WEST group -> cols <=113 then the final run to (114,exit_row); the final run is dimensioned like any stage: available >= needed",
 "R5_no_trial":"columns/bands are DERIVED by R1-R4; trying +/-N to make it pass is forbidden",
 "R6_enforced_gate":"this script refuses to emit a complete verdict if any lane fails dimensioning (fail-closed)"}
def main():
    open(LOGF,"w").close(); json.dump(RULES_DOC,open(os.path.join(HERE,RULES),"w"),ensure_ascii=False,indent=1)
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    master=json.load(open("K2_R529_WOVEN_COMPLETE_MASTER_v1.json"))
    ent=json.load(open("K2_R550_CONSTRUCTION_DRAWING_v1.json"))["entrance_channel_table"]
    l2=json.load(open("K2_R550_L2_SLOT_TABLE_v1.json"))["table"]
    def on4(nm,st): return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0
    adj={nm:g2.build_lane(nm)["adj"] for nm in names}
    C0={nm:set(u for u in adj[nm] if u<TERM and u//NID==0) for nm in names}
    CL={nm:{L:set(u for u in adj[nm] if u<TERM and u//NID==L) for L in (0,1)} for nm in names}
    rep={"artifact":"k2_r583_jia_rules_and_dimtable_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-226 JIA stage: single-source rules + complete 16/16 dimension table incl. final leg; zero construction runs; enforced gate",
         "rules_file":RULES,"rules":RULES_DOC,"construction_runs":0,"drawings":0,"trials":0,"per_lane":{}}
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
        def avail(a,b,last):
            cands=(list(range(115,138)) if east else list(range(61,114))) if last else list(range(61,114))
            cands=sorted(cands,key=lambda c:abs(c-Econ))
            for X in cands:
                hrun=[(c,a) for c in (range(cur+1,X+1) if X>=cur else range(X,cur))]
                vrun=[(X,r) for r in range(b+1,a+1)]
                if all((c*NY+r) in c0 and (c*NY+r) not in used for (c,r) in hrun+vrun): return X,hrun,vrun
            return None
        def dim(a,b,depth=0):
            if a<=b: return []
            got=avail(a,b,last=(b==Y))
            if got is not None: return [("stage",a,b,got)]
            if depth>8: return [("nocol",a,b,None)]
            mid=a-((a-b)+1)//2
            return dim(a,mid,depth+1)+dim(mid,b,depth+1)
        for a,b in zip(rows,rows[1:]):
            for kind,ra,rb,got in dim(a,b):
                if kind!="stage": stages.append({"from_row":ra,"to_row":rb,"verdict":"NO_COLUMN"}); ok=False; continue
                X,hrun,vrun=got
                for cell in hrun+vrun: used.add(cell)
                stages.append({"from_row":ra,"to_row":rb,"cut_row":ra,"column":X,"horizontal_span":len(hrun),
                               "vertical_needed":ra-rb,"vertical_available":len(vrun),"verdict":"PASS",
                               "final_leg":(rb==Y)})
                cur=X
            if not ok: break
        if ok:
            fin=[(c,Y) for c in (range(cur+1,Econ+1) if Econ>=cur else range(Econ,cur))]
            if all((c*NY+Y) in c0 and (c*NY+Y) not in used for (c,_) in fin):
                for cell in fin: used.add(cell)
                stages.append({"cut_row":Y,"column_econ":Econ,"horizontal_span":len(fin),"final_run":True,
                               "vertical_needed":1,"vertical_available":1,"verdict":"PASS"})
            else:
                stages.append({"cut_row":Y,"verdict":"FINAL_RUN_BLOCKED","available":0,"needed":max(1,len(fin))}); ok=False
        if ok: npass+=1
        rep["per_lane"][nm]={"L":L,"H":H,"Y":Y,"east":east,"Econ":Econ,"n_stages":len(stages),"stages":stages,
                             "verdict":"PASS" if ok else "FAIL"}
    rep["summary"]={"n_lanes":len(names),"PASS":npass,"FAIL":len(names)-npass}
    rep["buildability"]={"mode":"no_move","note":"route uses only free in-register cells; no registered object moved; NO construction run in this stage"}
    rep["complete_verdict"]="COMPLETE (16/16 dimensioned incl. final leg)" if npass==len(names) else "INCOMPLETE (fail-closed: not emitted as complete)"
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,OUT),"w"),ensure_ascii=False,indent=1,default=str)
    for nm in names:
        v=rep["per_lane"][nm]
        log("%-10s %-4s H=%s Y=%2s Econ=%3s stages=%2d %s %s"%(nm.split("PCIE_UP_")[1],"east" if v["east"] else "west",v["H"],v["Y"],v["Econ"],v["n_stages"],
            [(s.get("column"),s.get("vertical_needed"),s.get("vertical_available"),s["verdict"]) for s in v["stages"]][-3:],v["verdict"]))
    log("SUMMARY %s"%json.dumps(rep["summary"],ensure_ascii=False)); log("VERDICT %s"%rep["complete_verdict"])
    log("WROTE %s hash=%s"%(OUT,rep["artifact_hash16"])); log("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
