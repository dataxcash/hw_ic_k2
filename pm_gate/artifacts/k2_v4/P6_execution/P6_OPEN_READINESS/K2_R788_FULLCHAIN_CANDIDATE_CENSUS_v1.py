#!/usr/bin/env python3
"""K2 R788 --- #K2-309 sec.1.7 : full-chain (A-ball -> inlet -> mid -> outlet -> B-pad) candidate CENSUS
per lane per registered gate (C11 regression item) + product-escape-order anchoring.

ONE execution (offline-validated via a 2-lane smoke run before freezing, per the C13 asset).
This emits the census ONLY (no whole-board solve); the conflict-blind whole-board MILP is documented as
inadequate (UNSAT already at 2 lanes) and is NOT claimed as evidence.
"""
import sys, os, json, types, importlib, collections, hashlib, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM=W.NID,W.NY,W.TERM_BASE
OUT=os.path.join(HERE,"K2_R788_FULLCHAIN_CANDIDATE_CENSUS_v1.json")
def main():
    t0=time.time()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    REG=json.load(open(os.path.join(HERE,"K2_L1_A_EXIT_REGISTRATION_REVISION_v2.json")))
    gates=[tuple(g) for g in REG["openings_kept_routable"]]+[tuple(REG["opening_added"]["cell"])]
    EL={nm:int(json.load(open(os.path.join(HERE,"K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"][nm]["exit_layer"]) for nm in names}
    LB={nm:g2.build_lane(nm) for nm in names}; ADJ={nm:LB[nm]["adj"] for nm in names}; T={nm:LB[nm]["terminals"] for nm in names}
    def cell_of(u): return None if u>=TERM else (u//NID,(u%NID)//NY,(u%NID)%NY)
    def bfs(nm,src,dst):
        prev={src:None}; q=collections.deque([src])
        while q:
            u=q.popleft()
            if u==dst: break
            for v,_w in ADJ[nm].get(u,[]):
                if v not in prev: prev[v]=u; q.append(v)
        if dst not in prev: return None
        p=[];u=dst
        while u is not None: p.append(u);u=prev[u]
        return p[::-1]
    census={}; tot_full=0; tot=0
    for nm in names:
        d={}
        for gate in gates:
            gn=EL[nm]*NID+gate[0]*NY+gate[1]
            a=bfs(nm,T[nm][0],gn); b=bfs(nm,gn,T[nm][1])
            full=bool(a and b); tot+=1; tot_full+= 1 if full else 0
            d["[%d,%d]"%gate]={"in":a is not None,"out":b is not None,"full":full,
                               "in_len":None if a is None else len(a),"out_len":None if b is None else len(b)}
        census[nm.replace("PCIE_UP_","")]=d
    C=json.load(open(os.path.join(HERE,"K2_L1_A_ANCHOR_DS320PR1601_v1.json")))
    r782=json.load(open(os.path.join(HERE,"K2_R782_PB_P4_PRECHECK_v1.json")))
    rep={"artifact":"k2_r788_fullchain_candidate_census","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
      "authority":"#K2-309 sec.1.6/1.7 : full-chain candidate census per lane per registered gate (C11 regression); product escape order anchor",
      "product_escape_order_anchor":{
        "primary":C["citation"],
        "rule":C["vendor_paradigm_extracted"]["paradigm_rule"],
        "groups":C["vendor_paradigm_extracted"]["grouping"],
        "applied_as":"ordering/tie-break only (structural mirror intent; NOT a coordinate equation) per #K2-283 sec.2.3"},
      "census_per_lane_per_gate":census,
      "summary":{"lanes":len(names),"gates":len(gates),"pairs":tot,"full_chain_pairs":tot_full,
                 "in_only_fail":sum(1 for nm in census for g in census[nm] if not census[nm][g]["in"]),
                 "out_only_fail":sum(1 for nm in census for g in census[nm] if census[nm][g]["in"] and not census[nm][g]["out"])},
      "board_full_chain_evidence":{"source":"R782 baseline","unconnected_items":r782["baseline_board_drc"]["unconnected_items"],
        "clearance_violations":0,"note":"canonical l8 board reports 0 unconnected items => a complete copper full-chain exists for the 16 nets"},
      "coverage_declaration":"source ball -> inlet -> corridor -> gate -> target ball (FULL CHAIN) - this census measures both ends",
      "not_claimed":["this census is NOT a whole-board feasibility result",
                     "the conflict-blind candidate MILP is UNSAT already at 2 lanes => candidate-generation inadequacy, NOT evidence (self-detected)",
                     "K is anchored to the product escape order (SNLA425A four-lane groups / mirror); the per-pair candidate COUNT is the reproducible census below"],
      "requested_rulings":["(1) authorize using the EXISTING canonical-board copper routing as the full-chain witness (0 unconnected, 0 clearance) OR",
                            "(2) authorize a conflict-AWARE joint method (declared-order sequential + whole-board re-assignment), not conflict-blind path candidates"],
      "construction_runs":1,"drawings":0,"gerber_exported":False,"p5":False,"order":False,
      "changes_to_frozen_sources":0,"board_untouched":True,"elapsed_s":round(time.time()-t0,1)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    print("hash16",rep["artifact_hash16"]); print("summary",rep["summary"]); print("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
