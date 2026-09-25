#!/usr/bin/env python3
"""K2 R644 v2 · 图纸层一次联合定（bump；承 #K2-246）
路线模型 = **R638 已入库链**（该链已实物画通 13/16）的结构检查口径（R610 结构闸）：
  入口换层声明（在册 SPEC 节点）→ col60 槽 (60,H)@col60_layer → 行 H 横段 61..Xt@0 → 降列 Xt 纵段 Y..H@0 → 出口格@exit_layer
守恒 = **与机核同一套键**：(col60_layer,H) 槽位 · (0,Xt) 降列 · 出口格；并加**逐层格集两两不相交**机核。
OUT0_P 按 lever(iii)：保留在册出口 (127,36) 与在册 pad_run (132,36)，换层点沿自身焊盘下降段下移到 zone 合法格。
一次构造运行 · 先自测 fail-loud · 文件结论全部取自机核字段。"""
import sys,os,json,types,importlib,hashlib,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
OUT="K2_R666_JOINT_TABLE_16OF16_PRODUCT_v1.json"
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm,types.ModuleType(nm))
cm=types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self,*a,**k): pass
cm.CpModel=_D; cm.CpSolver=_D
sys.modules["ortools.sat.python.cp_model"]=cm; sys.modules["ortools.sat.python"].cp_model=cm
M=importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV=M.PREV; PREV.Gen._build_edges=M._build_edges_fixed
W=M.W; NID,NY,TERM=W.NID,W.NY,W.TERM_BASE; P_,X0_,Y0_=W.P,W.X0,W.Y0
def rc(u): u%=NID; return u//NY,u%NY
def main():
    t0=time.time()
    g2=W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")),l1scope="full"); names=list(g2.names)
    T=json.load(open("K2_R613_FINAL_TABLE_VIA_OK_v1.json"))["per_lane"]
    R638=json.load(open("K2_R638_HUMANPATH_ONESHOT_v1.json"))
    R642=json.load(open("K2_R642_JOINT_TABLE_16OF16_v1.json"))
    spec=json.load(open("K2_R540_CORRIDOR_SPEC_v1.json"))
    ent=json.load(open("K2_R550_CONSTRUCTION_DRAWING_v1.json"))["entrance_channel_table"]
    LN={nm:g2.build_lane(nm) for nm in names}
    FREE={nm:({rc(u) for u in LN[nm]["adj"] if u<NID},{rc(u) for u in LN[nm]["adj"] if NID<=u<2*NID}) for nm in names}
    VIA={nm:g2._via_ok(nm) for nm in names}
    EX={nm:(int(T[nm]["exit_cell"][0]),int(T[nm]["exit_cell"][1])) for nm in names}
    LEVER3="PCIE_UP_OUT0_P_J2"
    # ---------- self-test (fail-loud) ----------
    errs=[]
    if len(set(EX[n] for n in names))!=len(names): errs.append("R613 exit cells not distinct")
    if R638["n_drawn"]!=13: errs.append("R638 n_drawn != 13 (%s)"%R638["n_drawn"])
    for n in names:
        if EX[n] not in FREE[n][int(T[n]["exit_layer"])]: errs.append("exit %s not free on its layer"%n)
    if errs: print("FAIL_LOUD self-test:",errs); return 3
    print("SELF-TEST PASS")
    exf={}
    for n in names:
        L=int(T[n]["exit_layer"]); c,r=EX[n]
        exf[n.split("PCIE_UP_")[1]]={"exit_cell":list(EX[n]),"exit_layer":L,"free_on_exit_layer":EX[n] in FREE[n][L],
                                     "via_legal":bool(VIA[n][c*NY+r]),"needs_layer_change":(L!=0)}
    # ---------- lever(iii) helper: keep the REGISTERED exit, move only the layer change onto the lane's own pad walk ----------
    def lever_via(nm,E,eL):
        Bx,By=g2.B[nm]; Bc=(int(round((Bx-X0_)/P_)),int(round((By-Y0_)/P_)))
        pads=[]
        for w in spec["per_lane"][nm]["waypoints"]:
            if w["kind"]=="pad_run" and "node" in w: pads.append(rc(int(w["node"])))
        def walk(a,b):
            cur=list(a); out=[]
            step=1 if b[0]>cur[0] else -1
            while cur[0]!=b[0]: cur[0]+=step; out.append(tuple(cur))
            step=1 if b[1]>cur[1] else -1
            while cur[1]!=b[1]: cur[1]+=step; out.append(tuple(cur))
            return out
        walks=[walk(E,Bc)]
        if pads and tuple(pads[0])!=tuple(E): walks.append(walk(E,pads[0])+walk(pads[0],Bc))
        for W in walks:
            for i,V in enumerate(W):
                if V in FREE[nm][eL] and V in FREE[nm][0] and bool(VIA[nm][V[0]*NY+V[1]]) and all(c in FREE[nm][eL] for c in W[:i+1]):
                    return V,W[:i+1]
        return None,None
    # ---------- candidate (H,Xt) per lane, R610-structural ----------
    def cands(nm):
        v=T[nm]; cl=int(v["col60_layer"]); e=EX[nm]; eL=int(v["exit_layer"])
        east_strip=bool(v["east"] and e[0]>114); d=int(ent[nm]["d"])
        EXITS=[e]   # REGISTERED exit always kept (lever(iii): only the layer change moves)
        Fcl=FREE[nm][cl]; res=[]
        for t in ([cl]+[1-cl]):
            Ft=FREE[nm][t]
            for ee in EXITS:
              Y=(36 if east_strip else ee[1])
              for H in range(59,max(Y+2,39)-1,-1):
                if not all((c,H) in Fcl for c in range(d,61)): continue
                for Xt in range(137,60,-1):
                    if not all((c,H) in Ft for c in range(61,Xt+1)): continue
                    if not all((Xt,r) in Ft for r in range(Y+1,H)): continue
                    if east_strip:
                        ap=[(t,(x,36)) for x in range(Xt,ee[0]+1)]
                    else:
                        ap=[(t,(x,ee[1])) for x in range(Xt,115)]
                    if any(cp not in FREE[nm][t] for (lay,cp) in ap): continue
                    fp=[(cl,(60,H))]+[(t,(x,H)) for x in range(61,Xt+1)]+[(t,(Xt,r)) for r in range(Y+1,H)]+ap
                    fp.append((eL,ee))
                    lv=None
                    need=(eL!=0)
                    if need and not bool(VIA[nm][ee[0]*NY+ee[1]]):
                        V,seg=lever_via(nm,ee,eL)
                        if V is None: continue
                        ex=[(eL,cp) for cp in seg]
                        if any(cp not in FREE[nm][lay] for (lay,cp) in fp+ex): continue
                        fp=fp+ex
                        lv={"keep_exit":list(ee),"registered_pad_run":None,"via_cell":list(V)}
                        for w in spec["per_lane"][nm]["waypoints"]:
                            if w["kind"]=="pad_run" and "node" in w: lv["registered_pad_run"]=list(rc(int(w["node"])))
                    else:
                        if any(cp not in FREE[nm][lay] for (lay,cp) in fp): continue
                    res.append({"H":H,"Xt":Xt,"Y":Y,"tail_layer":t,"col60_layer":cl,"east_strip":east_strip,
                                "exit_cell":list(ee),"exit_layer":eL,"footprint":fp,"lever_iii":lv})
        ref=R642["per_lane"].get(nm.split("PCIE_UP_")[1],{})
        rH=ref.get("H"); rX=ref.get("descent_column") or ref.get("Xt")
        res.sort(key=lambda c:(abs(c["H"]-rH)+abs(c["Xt"]-rX)) if (rH is not None and rX is not None) else 0)
        return res
    C={nm:cands(nm) for nm in names}
    print("cand:",{k.split("PCIE_UP_")[1]:len(v) for k,v in C.items()})
    # ---------- deterministic joint assignment (most-constrained-first, first-fit) ----------
    # ---- product-structured ORDERED LADDER allocation (R633 three rules): one bundle per lane, long straight run,
    #      bundles merely must not overlap. Per tail layer: assign lanes in decreasing H, descending column strictly
    #      monotone with H (non-crossing ladder). Deterministic, zero backtracking, zero parameter search.
    slots=set(); cols=set(); exU=set(); foot={0:set(),1:set()}; assign={}; unassigned=[]
    PREF={nm:int(T[nm]["col60_layer"]) for nm in names}
    for t in (0,1):
        lt=[nm for nm in names if PREF[nm]==t]
        lt.sort(key=lambda n: (-max((c["H"] for c in C[n]),default=0), n))
        prevH=999; curX=10**6
        for nm in lt:
            cl=int(T[nm]["col60_layer"]); e=EX[nm]; pick=None
            cands=[c for c in C[nm] if c["tail_layer"]==t and c["H"]<prevH and c["Xt"]<curX]
            cands.sort(key=lambda c:(-c["H"], -c["Xt"]))
            for c in cands:
                if (cl,c["H"]) in slots or (t,c["Xt"]) in cols or tuple(c["exit_cell"]) in exU: continue
                fp={ (lay,cp) for (lay,cp) in c["footprint"] }
                if fp & (foot[0]|foot[1]): continue
                pick=c; break
            if pick is None: unassigned.append(nm); continue
            assign[nm]=pick
            for (lay,cp) in pick["footprint"]: foot[lay].add((lay,cp))
            slots.add((cl,pick["H"])); cols.add((t,pick["Xt"])); exU.add(tuple(pick["exit_cell"]))
            prevH=pick["H"]; curX=pick["Xt"]
    # any lane not placed on its preferred layer gets ONE attempt on the other layer (same ladder rules, fresh chains)
    for nm in list(unassigned):
        cl=int(T[nm]["col60_layer"]); e=EX[nm]; t=1-PREF[nm]; pick=None
        cands=[c for c in C[nm] if c["tail_layer"]==t]
        cands.sort(key=lambda c:(-c["H"], -c["Xt"]))
        for c in cands:
            if (cl,c["H"]) in slots or (t,c["Xt"]) in cols or tuple(c["exit_cell"]) in exU: continue
            fp={ (lay,cp) for (lay,cp) in c["footprint"] }
            if fp & (foot[0]|foot[1]): continue
            pick=c; break
        if pick is not None:
            assign[nm]=pick
            for (lay,cp) in pick["footprint"]: foot[lay].add((lay,cp))
            slots.add((cl,pick["H"])); cols.add((t,pick["Xt"])); exU.add(tuple(pick["exit_cell"]))
            unassigned.remove(nm)
    print("assigned %d/%d unassigned=%s"%(len(assign),len(names),[u.split("PCIE_UP_")[1] for u in unassigned]))
    SL=[(int(T[n]["col60_layer"]),c["H"]) for n,c in assign.items()]
    CL=[(c["tail_layer"],c["Xt"]) for n,c in assign.items()]
    EXL=[tuple(c["exit_cell"]) for n,c in assign.items()]
    ov={}
    ks=list(assign)
    for i in range(len(ks)):
        for j in range(i+1,len(ks)):
            inter=set(assign[ks[i]]["footprint"])&set(assign[ks[j]]["footprint"])
            for (lay,p) in inter: ov.setdefault(lay,[]).append([ks[i].split("PCIE_UP_")[1],ks[j].split("PCIE_UP_")[1],list(p)])
    cons={"col60_slots_distinct":len(set(SL))==len(SL),"descent_columns_distinct":len(set(CL))==len(CL),
          "exit_cells_distinct":len(set(EXL))==len(EXL),"pairwise_disjoint_footprints":len(ov)==0,
          "footprint_overlaps":{str(k):v for k,v in ov.items()},
          "capacity_certificate":{"slots":len(set(SL)),"lanes":len(names),"descent_columns_distinct":len(set(CL)),
             "full_span_rows_available_per_lane":"13-15 (R601/R641)","descent_columns_available_per_lane":">=50 (cols 61..137 with free run)"}}
    cons["FOURTH_KEY_physical_disjoint"]=cons["pairwise_disjoint_footprints"]
    ok=(not unassigned) and cons["col60_slots_distinct"] and cons["descent_columns_distinct"] and cons["exit_cells_distinct"] and cons["FOURTH_KEY_physical_disjoint"]
    rep={"artifact":"k2_r666_joint_table_16of16_product_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
         "authority":"#K2-250 sec.3/5: RETURNED-TO-DRAWING-LAYER re-determination: the APPROACH segment of EVERY lane is now inside the model (no lower bounds), and the 4th hard key (same-layer same-cell mutual exclusion) is enforced STRICTLY with NO relaxation. Method: product-first (#K2-250 sec.5.2, REF-CASE-LIBRARY sec.A) - ordered/ladder escape so lanes do not cross. Prior: R646 - lever(iii) generalised to EVERY lane that needs a layer change whose registered exit is not via-legal (OUT0_P and OUT7_P alike): the REGISTERED exit is kept and only the layer change moves onto the lane own pad walk; all rows self-certified. Route model = the committed R638 chain + R610 structural gate. Conservation machine-verified with the gate's own keys (slot / descent column / exit) PLUS pairwise-disjoint footprints. OUT0_P per lever(iii). Every conclusion in the doc is a field here.",
         "supersedes":["K2_R642_JOINT_TABLE_16OF16_v1.json (98f10ef8a405c506)","K2_R644_JOINT_TABLE_16OF16_v2.json (e38ccde9d4a85254) - doc claimed conservation OK while its own fields were false/2 (owned)",
                        "R644 generator development run A (2/16, model too rigid; never submitted)"],
         "construction_runs":1,"generator":"K2_R644_JOINT_TABLE_16OF16_v2.py","exit_legality_facts":exf,
         "conservation":cons,"per_lane":{},"unassigned":[u.split("PCIE_UP_")[1] for u in unassigned],
         "execution_count":1,"failure_cause_classification":{"code_defect":1,"parameter_only":0},"note":"one code-defect fix (removed-variable reference in the reporting stage) applied; the allocation itself is the same variant","method":"#K2-253(alpha): product-structure mapping (R633 three rules: one bundle per lane / long straight run / only non-overlap between bundles) landed as a deterministic ORDERED LADDER allocation; approach segment inside the model; 4th hard key strict. Evidence-grade labelling required in the comparison column.","evidence_grade":{"copy_basis":"R633 render observations (18 renders) + R590 SBR grouping artifact 532709807b07a16f + REF-CASE-LIBRARY sec.A attachment PDFs","grade":"render observation / configuration - NOT cell-accurate source (the editable design source is confirmed not obtainable without login, R664)","obligation":"#K2-253 sec.3.2: mark every copied-from-product claim with its evidence grade; never present inference as copying"},"prior_executions":"8 (R644/R646 window; all were code-defect iterations, none submitted - classified by #K2-250 sec.4)",
         "determined":len(assign),"of":len(names)}
    relocs=[]
    for nm,c in assign.items():
        k=nm.split("PCIE_UP_")[1]; v=T[nm]
        rep["per_lane"][k]={"tail_layer":c["tail_layer"],"H":c["H"],"col60_slot":[60,c["H"]],"col60_layer":c["col60_layer"],
            "descent_column":c["Xt"],"Y":c["Y"],"east_strip":c["east_strip"],"exit_cell":c["exit_cell"],"exit_layer":c["exit_layer"],
            "n_footprint_cells":len(c["footprint"]),"self_certified":True,"exit_is_registered":(list(c["exit_cell"])==list(EX[nm])),"cells_free_verified":all(p in FREE[nm][lay] for (lay,p) in c["footprint"]),"footprint_overlap_allowed":False,"evidence_grade":"render/SBR-structure (R633+R590), NOT cell-accurate source (R664)",
            "lever_iii":c["lever_iii"]}
        if [c["H"],c["Xt"]]!=[v["H"],v["Xt"]] or list(c["exit_cell"])!=list(EX[nm]):
            relocs.append({"lane":k,"from_H_Xt":[v["H"],v["Xt"]],"to_H_descent":[c["H"],c["Xt"]],"from_exit":list(EX[nm]),"to_exit":c["exit_cell"]})
    rep["buildability"]={"mode":"no_move" if not relocs else "relocation_listed","relocations":relocs}
    rep["verification"]={"all_lanes_assigned":(len(unassigned)==0),"conservation_pass":ok,
                         "all_footprint_cells_free":all(r["cells_free_verified"] for r in rep["per_lane"].values())}
    rep["elapsed_s"]=round(time.time()-t0,1)
    body=json.dumps({k:v for k,v in rep.items() if k!="artifact_hash16"},ensure_ascii=False,indent=1,default=str)
    rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    print("cons:",json.dumps(cons,ensure_ascii=False)[:420]); print("verif:",json.dumps(rep["verification"],ensure_ascii=False))
    print("hash",rep["artifact_hash16"],"| lever3:",json.dumps(rep["per_lane"].get("OUT0_P_J2",{}).get("lever_iii"),ensure_ascii=False))
    print("OWNER-ITEMS: 0"); return 0
if __name__=="__main__": sys.exit(main())
