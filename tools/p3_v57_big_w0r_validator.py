#!/usr/bin/env python3
"""Independent W0-R validator (rev W0R-FIX.1): no import of the W0-R generator.

It reparses the frozen upstream sources and recomputes, independently:
  - the accepted W0-R claims: source fingerprints, y-span subtraction, data band
    capacity/coverage, REFCLK anchor rows, certificate schema;
  - W0R-G3: the full projection enumeration evidence (42-footprint census,
    predicate flags, endpoint overlaps, empty-result justification consistency);
  - W0R-G1: the per-page per-corridor REFCLK conservation certificate (row
    bands, single-span containment, pitch separations, conflicting-resource
    numbers, minimal-core consistency) and the chip-zone passage witness
    (blockers, slices, channels, transition columns, per-page resolution),
    including direct freeness checks of every claimed window;
  - W0R-G2: terminal verdict derivation (B1.5 PASS / B1.5 INFEASIBLE_CERT) and
    the v1 §3 evidence-protocol field presence;
  - producer pairing: generator and validator source fingerprints recorded in
    the model must match the tools on disk (stale-pair detection).

Geometry arithmetic mirrors the model's integer half-micron convention
(1 mm = 2000 hm) so recomputed values are byte-comparable.
"""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path

K2=Path(__file__).resolve().parents[1]
STEP=K2/"pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
INPUT=STEP/"m13_v57_big_w0r_inputs.json"
MODEL=STEP/"m13_v57_big_w0r_corridor_model.json"
OUT=STEP/"m13_v57_big_w0r_validation.json"
SPEC=K2/"pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"
BOARD=K2/"k2_v4.kicad_pcb"
MANIFEST=STEP/"m13_v57_s1_page_manifest.json"
RULES=K2/"_shared/eda_core/drc_rules.json"
GENERATOR_TOOL=Path(__file__).resolve().with_name("p3_v57_big_w0r_corridor_model.py")
SELF=Path(__file__).resolve()
REV="W0R-FIX.1"
PITCH=1.46
BODY=0.175
EXCL={"J2","J3","J4","U6"}
ANCHOR_SIDE={"EAST_CHIP_TO_J2":"conn2","WEST_MCIO_TO_CHIP":"conn"}
TERMINAL_VERDICTS={"B1.5 PASS","B1.5 INFEASIBLE_CERT"}

def H(v): return int(round(v*2000))
def M(h): return round(h/2000.0,3)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def sx(t, start):
    d=0
    for i in range(start,len(t)):
        if t[i]=='(': d+=1
        elif t[i]==')':
            d-=1
            if d==0: return t[start:i+1]
    raise ValueError('unclosed expression')

def xy(x,y,at):
    a=math.radians(-at[2]); return (at[0]+x*math.cos(a)-y*math.sin(a),at[1]+x*math.sin(a)+y*math.cos(a))

def parse_footprints(text):
    """Own full parse: every footprint with at-position, body-proxy bbox,
    pad-only bbox, library and primitive scan.  Geometry-less entries kept."""
    entries=[]; circle_arc=0
    for m in re.finditer(r'\(footprint ',text):
        b=sx(text,m.start())
        prop=dict(re.findall(r'\(property "([^"]+)" "([^"]*)"',b))
        ref=prop.get('Reference','?')
        lib=re.search(r'\(footprint "([^"]*)"',b)
        am=re.search(r'\(at ([\-\d.]+) ([\-\d.]+)(?: ([\-\d.]+))?\)',b)
        at=[float(v or 0) for v in am.groups()] if am else None
        circle_arc+=len(re.findall(r'\(fp_(?:circle|arc)\b',b))
        at_t=tuple(at) if at else (0.0,0.0,0.0)
        pts=[]; padpts=[]
        for lm in re.finditer(r'\(fp_(?:line|rect|poly)\b',b):
            g=sx(b,lm.start())
            for q in re.finditer(r'\((?:start|end|xy) ([\-\d.]+) ([\-\d.]+)\)',g):
                pts.append(xy(float(q.group(1)),float(q.group(2)),at_t))
        for pm in re.finditer(r'\(pad ',b):
            p=sx(b,pm.start()); a2=re.search(r'\(at ([\-\d.]+) ([\-\d.]+)',p); z=re.search(r'\(size ([\-\d.]+) ([\-\d.]+)\)',p)
            if a2 and z:
                px,py=float(a2.group(1)),float(a2.group(2)); dx,dy=float(z.group(1))/2,float(z.group(2))/2
                for u,v in ((-dx,-dy),(-dx,dy),(dx,-dy),(dx,dy)):
                    q=xy(px+u,py+v,at_t); pts.append(q); padpts.append(q)
        bbox=padbox=None
        if pts:
            xs,ys=zip(*pts); bbox=[round(min(xs),3),round(min(ys),3),round(max(xs),3),round(max(ys),3)]
        if padpts:
            xs,ys=zip(*padpts); padbox=[round(min(xs),3),round(min(ys),3),round(max(xs),3),round(max(ys),3)]
        entries.append({"ref":ref,"library":lib.group(1) if lib else "?","at":at,"bbox":bbox,"pad_bbox":padbox})
    entries.sort(key=lambda e:e["ref"])
    return entries, circle_arc

def bodies():
    """Accepted W0-R independent body reparse (unchanged semantics)."""
    text=BOARD.read_text(); ans=[]
    for m in re.finditer(r'\(footprint ',text):
        b=sx(text,m.start()); prop=dict(re.findall(r'\(property "([^"]+)" "([^"]*)"',b)); am=re.search(r'\(at ([\-\d.]+) ([\-\d.]+)(?: ([\-\d.]+))?\)',b)
        if not am: continue
        at=tuple(float(v or 0) for v in am.groups()); pts=[]
        for lm in re.finditer(r'\(fp_(?:line|rect|poly)\b',b):
            g=sx(b,lm.start())
            for q in re.finditer(r'\((?:start|end|xy) ([\-\d.]+) ([\-\d.]+)\)',g): pts.append(xy(float(q.group(1)),float(q.group(2)),at))
        for pm in re.finditer(r'\(pad ',b):
            p=sx(b,pm.start()); a=re.search(r'\(at ([\-\d.]+) ([\-\d.]+)',p); z=re.search(r'\(size ([\-\d.]+) ([\-\d.]+)\)',p)
            if a and z:
                px,py=float(a.group(1)),float(a.group(2)); dx,dy=float(z.group(1))/2,float(z.group(2))/2
                pts += [xy(px+u,py+v,at) for u,v in ((-dx,-dy),(-dx,dy),(dx,-dy),(dx,dy))]
        if pts:
            xs,ys=zip(*pts); ans.append((prop.get('Reference','?'),min(xs),min(ys),max(xs),max(ys)))
    return ans

def subtract(span, blocks):
    out=[span]
    for lo,hi in sorted(blocks):
        nxt=[]
        for a,b in out:
            if hi<=a or lo>=b: nxt.append([a,b])
            else:
                if a<lo: nxt.append([a,min(lo,b)])
                if hi<b: nxt.append([max(a,hi),b])
        out=nxt
    return [[round(a,3),round(b,3)] for a,b in out if b-a>1e-9]

def isub(span, blocks):
    out=[tuple(span)]
    for lo,hi in sorted(blocks):
        nxt=[]
        for a,b in out:
            if hi<=a or lo>=b: nxt.append((a,b))
            else:
                if a<lo: nxt.append((a,min(lo,b)))
                if hi<b: nxt.append((max(a,hi),b))
        out=nxt
    return [(a,b) for a,b in out if b-a>0]

def main() -> int:
    failures=[]
    def bad(label):
        if label not in failures: failures.append(label)
    def eq(got, exp, label):
        if got != exp: bad(label)

    inp=json.load(open(INPUT)); model=json.load(open(MODEL))
    spec=json.load(open(SPEC)); manifest=json.load(open(MANIFEST)); rules=json.load(open(RULES))
    text=BOARD.read_text()

    # ---------- accepted W0-R checks (fingerprints, envelope) ----------
    layers=inp["board"]["stackup_layers"]
    if model["input_artifact_sha256"] != sha(INPUT): bad("input_hash")
    for label,path in (("spec",SPEC),("board",BOARD),("manifest",MANIFEST),("rules",RULES)):
        if inp["inputs_sha256"].get(label) != sha(path): bad(f"source_hash:{label}")
    y0,y1=spec["board"]["outline_y"]; inner=[round(y0+.3,3),round(y1-.3,3)]
    inner_hm=(H(inner[0]),H(inner[1]))
    if inp["keepouts"]["m3_clearance_mm"] != spec["constraints"]["m3_keepout_mm"]: bad("m3_clearance_source")
    m3_present = "MountingHole" in text
    if inp["keepouts"]["m3_holes_present"] != m3_present: bad("m3_presence")

    # ---------- schema / producer pairing (W0R-G2 evidence protocol item 1) ----------
    eq(model.get("schema"), 2, "schema")
    eq(model.get("revision"), REV, "revision")
    prod=model.get("producer",{})
    if prod.get("generator",{}).get("sha256") != sha(GENERATOR_TOOL): bad("producer_generator_hash_stale")
    if prod.get("validator",{}).get("sha256") != sha(SELF): bad("producer_validator_hash_stale")
    if not (model.get("revision")==prod.get("generator",{}).get("revision")==prod.get("validator",{}).get("revision")):
        bad("producer_revision_mismatch")
    eprot=model.get("evidence_protocol_v1_s3",{})
    for i in range(1,7):
        vals=[v for k,v in eprot.items() if k.startswith(f"item{i}")]
        if not vals: bad(f"evidence_protocol_item{i}_missing")
        elif not all(isinstance(v,str) and v.strip() for v in vals): bad(f"evidence_protocol_item{i}_empty")
    hatches=model.get("legal_escape_hatches",{}).get("hatches",[])
    if not hatches: bad("escape_hatches_missing")
    for h in hatches:
        if h.get("target_layer") not in ("L0","L1","L2"): bad("escape_hatch_not_upstream")

    # ---------- rule metrics (declared rules authority, drift = hard fail) ----------
    dp=rules["diff_pair"]
    pg,pw,ip=H(dp["p_gap"]),H(dp["p_width"]),H(dp["inter_pair_spacing"])
    EXT=pg+2*pw; EXT2=EXT//2; PITCH_HM=EXT+ip
    if PITCH_HM != H(PITCH): bad("rule_drift_pitch")
    CLE=None
    for nc in rules["clearance"]["net_classes"]:
        if nc["name"]=="PCIe85": CLE=H(nc["clearance"])
    if CLE != H(BODY): bad("rule_drift_clearance")

    # ---------- own census + manifest expectations ----------
    census, circle_arc = parse_footprints(text)
    expected_pages={}
    for p in manifest["pages"]:
        if p["kind"]=="data": expected_pages.setdefault((p["corridor"]["id"],p["corridor"]["band"]),[]).append(p["page_id"])
    expected_ref=[]
    refpages=sorted([p for p in manifest["pages"] if p["kind"]=="refclk_pass"], key=lambda p:p["page_id"])
    for p in refpages:
        a=p["anchors"]; expected_ref.append({"page_id":p["page_id"],"j2_y":[a["conn2"][q]["pad_global"][1] for q in ("P","N")],"far_ref":a["conn"]["P"]["ref"],"far_y":[a["conn"][q]["pad_global"][1] for q in ("P","N")]})

    # ---------- own J2 face facts ----------
    j2_pads=[]
    for e_line in re.finditer(r'\(footprint ',text):
        b=sx(text,e_line.start())
        prop=dict(re.findall(r'\(property "([^"]+)" "([^"]*)"',b))
        if prop.get('Reference')!='J2': continue
        am=re.search(r'\(at ([\-\d.]+) ([\-\d.]+)(?: ([\-\d.]+))?\)',b)
        at=tuple(float(v or 0) for v in am.groups())
        for pm in re.finditer(r'\(pad ',b):
            p=sx(b,pm.start()); num=re.search(r'\(pad "([^"]*)"',p)
            a2=re.search(r'\(at ([\-\d.]+) ([\-\d.]+)',p); z=re.search(r'\(size ([\-\d.]+) ([\-\d.]+)\)',p)
            if a2 and z:
                gx,gy=xy(float(a2.group(1)),float(a2.group(2)),at)
                j2_pads.append({"num":num.group(1) if num else "?","x":gx,"y":gy,"w":float(z.group(1)),"h":float(z.group(2))})
    j2_west=sorted([p for p in j2_pads if H(p["x"])<H(133.5)], key=lambda p:(H(p["y"]),p["num"]))
    j2_east=sorted([p for p in j2_pads if H(p["x"])>=H(133.5)], key=lambda p:(H(p["y"]),p["num"]))
    jys=[H(p["y"]) for p in j2_west]
    face_pitch=min(b-a for a,b in zip(jys,jys[1:]))
    pad_w,pad_h=H(j2_west[0]["w"]),H(j2_west[0]["h"])
    j2_entry=next(e for e in census if e["ref"]=="J2")

    # ---------- own witness inputs: chip-zone blockers/slices/columns ----------
    CORR=inp["corridor_x_ranges_pending_l2_ruling"]
    cz=(H(CORR["WEST_MCIO_TO_CHIP"][1]),H(CORR["EAST_CHIP_TO_J2"][0]))
    blockers=[]
    for e in census:
        if e["bbox"] is None: continue
        x0,y0b,x1,y1b=e["bbox"]
        if x0 < M(cz[1]) and x1 > M(cz[0]):
            blockers.append({"ref":e["ref"],"bbox":e["bbox"],
                             "kx":(H(x0)-CLE,H(x1)+CLE),"ky":(H(y0b)-CLE,H(y1b)+CLE)})
    blockers.sort(key=lambda b:b["ref"])
    edges=sorted({cz[0],cz[1]} | {v for b in blockers for v in b["kx"] if cz[0]<v<cz[1]})
    slices=[]
    for a,b in zip(edges,edges[1:]):
        bl=[q for q in blockers if q["kx"][0]<b and q["kx"][1]>a]
        free=isub(inner_hm,[q["ky"] for q in bl])
        slices.append({"x_range":(a,b),"blockers":[q["ref"] for q in bl],
                       "channels":[w for w in free if w[1]-w[0]>=EXT],
                       "sealed":[w for w in free if 0<w[1]-w[0]<EXT]})
    sealed_pairs=[]
    for i in range(len(blockers)):
        for j in range(i+1,len(blockers)):
            A,B=blockers[i],blockers[j]
            if not (A["kx"][0]<B["kx"][1] and B["kx"][0]<A["kx"][1]): continue
            lo,hi=sorted([A,B],key=lambda q:(q["ky"][0],q["ref"]))
            gap=hi["ky"][0]-lo["ky"][1]
            if gap<EXT:
                sealed_pairs.append({"pair":[lo["ref"],hi["ref"]],"gap_mm":M(gap),
                                     "reason":"keepouts overlap (negative gap)" if gap<0 else "gap < pair_copper_extent"})
    sealed_pairs.sort(key=lambda s:(s["pair"][0],s["pair"][1]))
    u6=next(b for b in blockers if b["ref"]=="U6")
    cap_kx_lo=min(b["kx"][0] for b in blockers if b["ref"]!="U6")
    j2_kx0=H(j2_entry["pad_bbox"][0])-CLE
    east_rise=(u6["kx"][1]+EXT2, j2_kx0-EXT2)
    west_descent=(slices[0]["x_range"][0]+EXT2, cap_kx_lo-EXT2)
    j34_kx0=min(H(e["bbox"][0])-CLE for e in census if e["ref"] in ("J3","J4") and e["bbox"] is not None)
    j34_kx1=max(H(e["bbox"][2])+CLE for e in census if e["ref"] in ("J3","J4") and e["bbox"] is not None)
    west_rise=(j34_kx1+EXT2, u6["kx"][0]-EXT2)
    def free_y_in(xlo,xhi):
        bl=[q for q in blockers if q["kx"][0]<xhi and q["kx"][1]>xlo]
        return isub(inner_hm,[q["ky"] for q in bl])
    east_rise_free=free_y_in(east_rise[0]-EXT2,east_rise[1]+EXT2)
    west_rise_free=free_y_in(west_rise[0]-EXT2,west_rise[1]+EXT2)
    def chain_west(start):
        run=start
        for sl in slices[-2::-1]:
            inter=[(max(run[0],c[0]),min(run[1],c[1])) for c in sl["channels"]]
            inter=[w for w in inter if w[1]-w[0]>=EXT]
            if not inter: return None
            run=sorted(inter,key=lambda w:(-(w[1]-w[0]),w[0]))[0]
        return run if run[1]-run[0]>=EXT else None
    def contains(win,cop): return win[0]<=cop[0] and cop[1]<=win[1]

    # ---------- own per-corridor derivation ----------
    allb=bodies()
    own={}
    for cid,c in model["corridors"].items():
        lo,hi=inner
        spans=c["usable_y_spans"]
        # accepted span checks
        if any(a < lo or b > hi or b <= a for a,b in spans): bad(f"{cid}:span_bounds")
        if any(spans[i][1] > spans[i+1][0] for i in range(len(spans)-1)): bad(f"{cid}:span_overlap")
        xr=CORR[cid]
        eq(c["x_range"], xr, f"{cid}:x_range")
        expected_blocks=[]
        for ref,x0,yy0,x1,yy1 in allb:
            if x0<xr[1] and x1>xr[0] and ref not in EXCL:
                expected_blocks.append({"ref":ref,"y":[round(yy0-BODY,3),round(yy1+BODY,3)]})
        if c["blocked_component_projections"] != expected_blocks: bad(f"{cid}:body_projection")
        if spans != subtract(inner,[x["y"] for x in expected_blocks]): bad(f"{cid}:span_derivation")
        ka=c["keepout_application"]
        if ka["m3_holes_present"] != inp["keepouts"]["m3_holes_present"] or ka["m3_projected"] != False or ka["component_body_clearance_mm"] != BODY: bad(f"{cid}:keepout_application")
        if c["data_layer"] not in layers: bad(f"{cid}:data_layer")
        for band,b in c["data_bands"].items():
            need=(b["n_pairs"]-1)*PITCH
            expected=[s for s in spans if s[1]-s[0]+1e-9 >= need]
            if b["candidate_spans"] != expected or b["feasible"] != bool(expected): bad(f"{cid}:{band}:capacity")
            if len(b["page_ids"]) != b["n_pairs"]: bad(f"{cid}:{band}:coverage")
            if b["page_ids"] != expected_pages[(cid,band)]: bad(f"{cid}:{band}:manifest_anchors")
        joint=c["joint_data_frame"]; n=sum(c["data_bands"][b]["n_pairs"] for b in ("up","dn")); need=(n-1)*PITCH
        expected=[s for s in spans if s[1]-s[0]+1e-9 >= need]
        if joint["band_order"] != ["up","dn"] or joint["n_pairs"] != n or joint["candidate_spans"] != expected or joint["feasible"] != bool(expected): bad(f"{cid}:joint_capacity")

        # ---------- W0R-G3: projection evidence ----------
        pe=c.get("projection_evidence")
        if not pe: bad(f"{cid}:projection_evidence_missing"); continue
        eq(pe["source"]["sha256"], sha(BOARD), f"{cid}:pe_source_hash")
        eq(pe["predicate"]["endpoint_exclusions"], sorted(EXCL), f"{cid}:pe_predicate_exclusions")
        eq(pe["predicate"]["y_inflation_mm"], BODY, f"{cid}:pe_predicate_inflation")
        eq(pe["predicate"]["primitive_coverage"], {"fp_circle_or_arc_primitives_in_source": circle_arc}, f"{cid}:pe_primitive_coverage")
        enum=pe["enumeration"]
        eq(enum["footprints_total"], len(census), f"{cid}:pe_total")
        eq(enum["with_geometry"], sum(1 for e in census if e["bbox"] is not None), f"{cid}:pe_with_geometry")
        eq(len(enum["checked"]), len(census), f"{cid}:pe_checked_count")
        own_checked=[]; own_overlaps=[]
        for e in census:
            if e["bbox"] is None:
                own_checked.append((e["ref"],"none",None,False,False,False))
                continue
            x0,_,x1,_=e["bbox"]
            ov = x0 < xr[1] and x1 > xr[0]
            excl = ov and e["ref"] in EXCL
            own_checked.append((e["ref"],"present",tuple(e["bbox"]),ov,excl,ov and not excl))
            if ov:
                slab=[round(max(x0,xr[0]),3),round(min(x1,xr[1]),3)]
                pb=e["pad_bbox"]
                pad_free = pb is None or slab[1]<=pb[0] or slab[0]>=pb[2]
                own_overlaps.append({"ref":e["ref"],"slab_x":slab,"overhang_mm":round(slab[1]-slab[0],3),
                                     "endpoint_excluded":excl,"slab_pad_free":pad_free,
                                     "kind":"courtyard_only_pad_free" if pad_free else "pad_field"})
        got_checked=[(k["ref"],k["geometry"],tuple(k["bbox"]) if k.get("bbox") else None,
                      k["x_overlaps_corridor"],k["endpoint_excluded"],k["intruder"]) for k in enum["checked"]]
        eq(got_checked, own_checked, f"{cid}:pe_checked_flags")
        got_nogeo=sorted((k["ref"],tuple(k["at"])) for k in enum["without_geometry"])
        own_nogeo=sorted((e["ref"],tuple(e["at"])) for e in census if e["bbox"] is None)
        eq(got_nogeo, own_nogeo, f"{cid}:pe_without_geometry")
        got_ov=[{k:v for k,v in o.items() if k in ("ref","slab_x","overhang_mm","endpoint_excluded","slab_pad_free","kind")}
                for o in pe["endpoint_overlaps"]]
        eq(sorted(got_ov,key=lambda o:o["ref"]), own_overlaps, f"{cid}:pe_endpoint_overlaps")
        res=pe["result"]
        eq(res["intruder_count"], len(expected_blocks), f"{cid}:pe_intruder_count")
        if res["census_agrees_with_subtraction_input"] is not True: bad(f"{cid}:pe_census_disagrees")
        if len(expected_blocks)==0:
            if not res.get("empty_justification"): bad(f"{cid}:pe_empty_justification_missing")
            if res.get("non_empty_detail") is not None: bad(f"{cid}:pe_nonempty_detail_should_be_null")
        else:
            if res.get("empty_justification") is not None: bad(f"{cid}:pe_justification_should_be_null")
            eq(res.get("non_empty_detail"), expected_blocks, f"{cid}:pe_nonempty_detail")

        # ---------- W0R-G1: REFCLK conservation certificate ----------
        rd=c["refclk_resource_domain"]
        if rd["layer"] not in layers or rd["layer"] == c["data_layer"]: bad(f"{cid}:refclk_layer")
        if rd.get("resource_kind") != "conservation_certificate": bad(f"{cid}:refclk_not_conservation_certificate")
        for f in ("status","required","available","shortage","conflicting_resources","minimal_core"):
            if f not in rd: bad(f"{cid}:refclk_certificate_field:{f}")
        if rd["anchors"] != expected_ref: bad(f"{cid}:refclk_anchors")
        eq(rd["x_range"], xr, f"{cid}:refclk_x_range")
        side=ANCHOR_SIDE[cid]
        eq(rd["required"]["band_pitch_mm"], PITCH, f"{cid}:refclk_pitch")
        eq(rd["required"]["pair_copper_extent_mm"], M(EXT), f"{cid}:refclk_extent")
        eq(rd["required"]["rows"], len(refpages), f"{cid}:refclk_rows")
        rows=rd["required"]["per_page"]
        eq([r["page_id"] for r in rows], [p["page_id"] for p in refpages], f"{cid}:refclk_page_set")
        own_rows={}
        for r,p in zip(rows,refpages):
            a=p["anchors"][side]
            yP,yN=a["P"]["pad_global"][1],a["N"]["pad_global"][1]
            centre=H((yP+yN)/2)
            band=(centre-PITCH_HM//2,centre+PITCH_HM//2)
            cop=(centre-EXT2,centre+EXT2)
            cont=[s for s in spans if H(s[0])<=band[0] and band[1]<=H(s[1])]
            eq(r["anchor_side_key"], side, f"{cid}:refclk_anchor_side")
            eq(r["manifest_corridor_id"], p["corridor"]["id"], f"{cid}:refclk_manifest_corridor")
            eq(r["anchor_ref"], a["P"]["ref"], f"{cid}:refclk_anchor_ref")
            eq(r["anchor_pads"]["P"]["y"], yP, f"{cid}:refclk_anchor_padP")
            eq(r["anchor_pads"]["N"]["y"], yN, f"{cid}:refclk_anchor_padN")
            eq(r["anchor_dy_mm"], round(abs(yP-yN),3), f"{cid}:refclk_anchor_dy")
            eq(r["band_centre_y"], M(centre), f"{cid}:refclk_band_centre")
            eq(r["band_y"], [M(band[0]),M(band[1])], f"{cid}:refclk_band")
            eq(r["copper_y"], [M(cop[0]),M(cop[1])], f"{cid}:refclk_copper")
            eq(r["containment"]["contained"], bool(cont), f"{cid}:refclk_containment_flag")
            eq(r["containment"]["containing_span"], cont[0] if cont else None, f"{cid}:refclk_containing_span")
            own_rows[p["page_id"]]=(centre,band,cop,bool(cont))
        # separations
        own_seps=[]
        ids=sorted(own_rows)
        for i in range(len(ids)):
            for j in range(i+1,len(ids)):
                d=abs(own_rows[ids[i]][0]-own_rows[ids[j]][0])
                own_seps.append({"pages":[ids[i],ids[j]],"separation_mm":M(d),"required_mm":PITCH,"ok":d>=PITCH_HM})
        eq(rd["available"]["pairwise_separations"], own_seps, f"{cid}:refclk_separations")
        eq(rd["available"]["usable_y_spans_fcu_mm"], spans, f"{cid}:refclk_available_spans")
        containment_ok=all(v[3] for v in own_rows.values())
        separation_ok=all(s["ok"] for s in own_seps)
        if len(spans)==1:
            cap=(H(spans[0][1])-H(spans[0][0]))//PITCH_HM+1
            if str(cap) not in rd["available"]["row_band_capacity_note"]: bad(f"{cid}:refclk_capacity_note")
        sh=rd["shortage"]
        eq(sh["unsatisfied_rows"], sum(1 for v in own_rows.values() if not v[3]), f"{cid}:refclk_shortage_rows")
        eq(sh["separation_violations"], sum(1 for s in own_seps if not s["ok"]), f"{cid}:refclk_shortage_seps")
        eq(sh["containment_violations"], sum(1 for v in own_rows.values() if not v[3]), f"{cid}:refclk_shortage_containment")
        # conflicting resources
        classes={cc["class"]:cc for cc in rd["conflicting_resources"]}
        need_classes={"refclk_rows_same_corridor_same_layer","non_endpoint_body_projections","m3_keepout",
                      "data_bands_cross_layer","endpoint_body_overhang","connector_pad_field_transit_and_n_escape"}
        if not need_classes <= set(classes): bad(f"{cid}:refclk_conflict_classes_missing")
        if cid=="EAST_CHIP_TO_J2" and "connector_face_row_compression" not in classes: bad(f"{cid}:refclk_face_class_missing")
        cc=classes.get("refclk_rows_same_corridor_same_layer",{})
        eq(cc.get("separations"), own_seps, f"{cid}:conflict_rows_separations")
        eq(cc.get("outcome"), "DISJOINT" if separation_ok else "VIOLATION", f"{cid}:conflict_rows_outcome")
        cc=classes.get("non_endpoint_body_projections",{})
        eq(cc.get("count"), len(expected_blocks), f"{cid}:conflict_bodies_count")
        eq(cc.get("outcome"), "NONE_IN_CORRIDOR" if not expected_blocks else "PRESENT", f"{cid}:conflict_bodies_outcome")
        cc=classes.get("m3_keepout",{})
        eq(cc.get("m3_holes_present"), m3_present, f"{cid}:conflict_m3")
        eq(cc.get("outcome"), "ABSENT" if not m3_present else "PRESENT", f"{cid}:conflict_m3_outcome")
        cc=classes.get("data_bands_cross_layer",{})
        eq(cc.get("outcome"), "NO_SHARED_COPPER_LAYER", f"{cid}:conflict_cross_layer_outcome")
        eq(cc.get("refclk_layer"), rd["layer"], f"{cid}:conflict_cross_layer_refclk")
        eq(cc.get("data_layer"), c["data_layer"], f"{cid}:conflict_cross_layer_data")
        if cc.get("refclk_layer") == cc.get("data_layer"): bad(f"{cid}:conflict_cross_layer_same")
        cc=classes.get("endpoint_body_overhang",{})
        got_entries=sorted(({k:v for k,v in o.items() if k in ("ref","slab_x","overhang_mm","endpoint_excluded","slab_pad_free","kind")}
                            for o in cc.get("entries",[])), key=lambda o:o["ref"])
        eq(got_entries, own_overlaps, f"{cid}:conflict_overhang_entries")
        if cid=="EAST_CHIP_TO_J2":
            fc=classes.get("connector_face_row_compression",{})
            eq(fc.get("face_row_pitch_mm"), M(face_pitch), f"{cid}:face_pitch")
            eq(fc.get("pad_size_mm"), [M(pad_w),M(pad_h)], f"{cid}:face_pad_size")
            fclear=face_pitch-pad_h//2-pw//2
            eq(fc.get("row_copper_edge_to_neighbour_pad_mm"), M(fclear), f"{cid}:face_clearance_value")
            eq(fc.get("clearance_ok"), fclear>=CLE, f"{cid}:face_clearance_ok")
            eq(fc.get("outcome"), "QUANTIFIED_OK" if fclear>=CLE else "VIOLATION", f"{cid}:face_outcome")
            own_adj={}
            for pid,(centre,band,cop,_) in own_rows.items():
                inband=sorted([p["num"] for p in j2_west if band[0]<=H(p["y"])<=band[1]], key=lambda n:(len(n),n))
                own_adj[pid]=inband
            eq(fc.get("band_neighbour_pads"), own_adj, f"{cid}:face_adjacent_pads")
            ne=classes.get("connector_pad_field_transit_and_n_escape",{})
            transit_req=pw+2*CLE
            west_xhi=max(H(p["x"])+pad_w//2 for p in j2_west)
            east_xlo=min(H(p["x"])-pad_w//2 for p in j2_east)
            eq(ne.get("inter_column_gap_x"), [M(west_xhi),M(east_xlo)], f"{cid}:nescape_gap_x")
            eq(ne.get("inter_column_gap_width_mm"), M(east_xlo-west_xhi), f"{cid}:nescape_gap_width")
            eq(ne.get("single_trace_transit_required_mm"), M(transit_req), f"{cid}:nescape_transit_req")
            eq(ne.get("inter_column_transit_ok"), east_xlo-west_xhi>=transit_req, f"{cid}:nescape_transit_ok")
            eq(ne.get("inter_pad_window_mm"), M(face_pitch-pad_h), f"{cid}:nescape_interpad")
            eq(ne.get("inter_pad_transit"), "BLOCKED (window < single-trace transit requirement)" if (face_pitch-pad_h)<transit_req else "OPEN", f"{cid}:nescape_interpad_transit")
            eq(ne.get("outcome"), "DELEGATED_QUANTIFIED", f"{cid}:nescape_outcome")
            pfy=[H(j2_entry["pad_bbox"][1]),H(j2_entry["pad_bbox"][3])]
            eq(ne.get("vertical_bypass_windows_y"),
               {"below":[M(inner_hm[0]),M(pfy[0]-CLE-pw//2)],"above":[M(pfy[1]+CLE+pw//2),M(inner_hm[1])]},
               f"{cid}:nescape_bypass_windows")
        else:
            ne=classes.get("connector_pad_field_transit_and_n_escape",{})
            eq(ne.get("connectors"), ["J3","J4"], f"{cid}:west_transit_connectors")
            eq(ne.get("outcome"), "DELEGATED_QUANTIFIED", f"{cid}:west_transit_outcome")
        # minimal core consistency
        mc=rd["minimal_core"]
        witness_ok = True  # refined after witness checks below
        own[cid]={"spans":spans,"rows":own_rows,"domain_ok":containment_ok and separation_ok,"rd":rd}

    # ---------- W0R-G1: passage witness verification ----------
    w=model.get("refclk_passage_witness")
    witness_all_ok=False
    if len(own) != len(model["corridors"]): bad("corridor_checks_incomplete")
    if not w:
        bad("witness_missing")
    elif "EAST_CHIP_TO_J2" not in own or "WEST_MCIO_TO_CHIP" not in own:
        bad("witness_inputs_incomplete")
    else:
        eq(w["chip_zone_x"], [M(cz[0]),M(cz[1])], "witness:chip_zone")
        eq(w["pair_copper_extent_mm"], M(EXT), "witness:extent")
        eq(w["min_channel_height_mm"], M(EXT), "witness:min_channel")
        eq(w["keepout_inflation_mm"], BODY, "witness:inflation")
        eq([{k:b[k] for k in ("ref","bbox","keepout_x","keepout_y")} for b in w["blockers"]],
           [{"ref":b["ref"],"bbox":b["bbox"],"keepout_x":[M(b["kx"][0]),M(b["kx"][1])],"keepout_y":[M(b["ky"][0]),M(b["ky"][1])]} for b in blockers],
           "witness:blockers")
        got_slices=[(tuple(s["x_range"]),sorted(s["blockers"]),[tuple(ch) for ch in s["free_channels_ge_extent"]],[tuple(x) for x in s["sealed_windows_lt_extent"]]) for s in w["slices"]]
        own_slices=[((M(s["x_range"][0]),M(s["x_range"][1])),sorted(s["blockers"]),[(M(a),M(b)) for a,b in s["channels"]],[(M(a),M(b)) for a,b in s["sealed"]]) for s in slices]
        eq(got_slices, own_slices, "witness:slices")
        eq(w["sealed_or_merged_keepout_pairs"], sealed_pairs, "witness:sealed_pairs")
        # independent freeness of every emitted slice channel
        for s_model, s_own in zip(w["slices"], slices):
            xr2=(H(s_model["x_range"][0]),H(s_model["x_range"][1]))
            for ch in s_model["free_channels_ge_extent"]:
                ch_h=(H(ch[0]),H(ch[1]))
                if ch_h[1]-ch_h[0] < EXT: bad("witness:channel_too_small")
                if ch_h[0] < inner_hm[0] or ch_h[1] > inner_hm[1]: bad("witness:channel_outside_span")
                for b in blockers:
                    if b["kx"][0] < xr2[1] and b["kx"][1] > xr2[0]:
                        if b["ky"][0] < ch_h[1] and b["ky"][1] > ch_h[0]: bad(f"witness:channel_blocked@{ch}")
        tc=w["transition_columns"]
        eq(tc["east_rise"]["x_centre_range"], [M(east_rise[0]),M(east_rise[1])], "witness:east_rise_x")
        eq(tc["east_rise"]["free_y"], [[M(a),M(b)] for a,b in east_rise_free], "witness:east_rise_free")
        eq(tc["west_descent"]["x_centre_range"], [M(west_descent[0]),M(west_descent[1])], "witness:west_descent_x")
        eq(tc["west_descent"]["free_y_channels"], [[M(a),M(b)] for a,b in slices[0]["channels"]], "witness:west_descent_channels")
        eq(tc["west_rise_in_corridor"]["x_centre_range"], [M(west_rise[0]),M(west_rise[1])], "witness:west_rise_x")
        eq(tc["west_rise_in_corridor"]["free_y"], [[M(a),M(b)] for a,b in west_rise_free], "witness:west_rise_free")
        if east_rise[0] >= east_rise[1]: bad("witness:east_rise_column_empty")
        if west_descent[0] >= west_descent[1]: bad("witness:west_descent_column_empty")

        # own per-page resolution, then compare
        east_rows=own["EAST_CHIP_TO_J2"]["rows"]; west_rows=own["WEST_MCIO_TO_CHIP"]["rows"]
        per_ok=True
        for pid in sorted(east_rows):
            ce=east_rows[pid][0]; cw=west_rows[pid][0]
            ecop=east_rows[pid][2]; wcop=west_rows[pid][2]
            others=[(east_rows[o][0],west_rows[o][0]) for o in sorted(east_rows) if o!=pid]
            mw=w["per_page"].get(pid)
            if not mw: bad(f"witness:page_missing:{pid}"); per_ok=False; continue
            direct=None
            for c0 in sorted(c for c in slices[-1]["channels"] if contains(c,ecop)):
                run=chain_west(c0)
                if run is not None and contains(run,ecop) and contains(run,wcop):
                    direct=run; break
            if direct is not None:
                if mw.get("kind")!="direct_channel" or mw.get("status")!="WITNESSED": bad(f"witness:kind:{pid}"); per_ok=False; continue
                eq(mw["channel_y"], [M(direct[0]),M(direct[1])], f"witness:channel:{pid}")
                eq(mw["east_band_copper_y"], [M(ecop[0]),M(ecop[1])], f"witness:east_copper:{pid}")
                eq(mw["west_band_copper_y"], [M(wcop[0]),M(wcop[1])], f"witness:west_copper:{pid}")
                eq(mw["margins_mm"], {"east_copper_to_channel":[M(ecop[0]-direct[0]),M(direct[1]-ecop[1])],
                                      "west_copper_to_channel":[M(wcop[0]-direct[0]),M(direct[1]-wcop[1])]},
                   f"witness:margins:{pid}")
                # independent containment re-check
                if not (direct[0]<=ecop[0] and ecop[1]<=direct[1] and direct[0]<=wcop[0] and wcop[1]<=direct[1]):
                    bad(f"witness:direct_containment:{pid}"); per_ok=False
                continue
            # detour: recompute candidates
            candidates=[]
            for c0 in sorted(slices[-1]["channels"]):
                states=[(c0,[c0])]
                for sl in slices[-2::-1]:
                    nxt=[]
                    for wv,pth in states:
                        for c2 in sorted(sl["channels"]):
                            inter=(max(wv[0],c2[0]),min(wv[1],c2[1]))
                            if inter[1]-inter[0]>=EXT: nxt.append((inter,pth+[inter]))
                    seen={}
                    for wv,pth in nxt:
                        if wv not in seen: seen[wv]=pth
                    states=[(wv,seen[wv]) for wv in sorted(seen)]
                    if not states: break
                for wv,pth in states:
                    exit_mode=None
                    if contains(wv,wcop): exit_mode="direct_exit"
                    else:
                        ch1=[c2 for c2 in slices[0]["channels"] if contains(c2,wv) and contains(c2,wcop)]
                        if ch1 and west_descent[0]<west_descent[1]: exit_mode="descent_in_west_slice"
                    if exit_mode:
                        dist=max(0,wv[0]-wcop[1],wcop[0]-wv[1])
                        bound=sorted({b["ref"] for b in blockers
                                      if (wv[0]-EXT<=b["ky"][1]<=wv[1]+EXT) or (wv[0]-EXT<=b["ky"][0]<=wv[1]+EXT)})
                        candidates.append({"window":wv,"dist":dist,"exit_mode":exit_mode,
                                           "bounding_keepouts":bound,"chain":pth,
                                           "side":"north" if wv[0]>=u6["ky"][1] else "south"})
            candidates.sort(key=lambda c3:(c3["dist"],c3["window"][0]))
            if not candidates:
                if mw.get("status")!="NO_WITNESS": bad(f"witness:expected_no_witness:{pid}"); per_ok=False
                continue
            if mw.get("kind")!="detour" or mw.get("status")!="WITNESSED": bad(f"witness:kind:{pid}"); per_ok=False; continue
            best=candidates[0]; wv=best["window"]
            eq(mw["side"], best["side"], f"witness:side:{pid}")
            eq(mw["traverse_window_y"], [M(wv[0]),M(wv[1])], f"witness:window:{pid}")
            eq(mw["pair_centre_window_y"], [M(wv[0]+EXT2),M(wv[1]-EXT2)], f"witness:centre_window:{pid}")
            eq(mw["window_height_mm"], M(wv[1]-wv[0]), f"witness:window_height:{pid}")
            eq(mw["min_required_height_mm"], M(EXT), f"witness:min_height:{pid}")
            eq(mw["bounding_keepouts"], best["bounding_keepouts"], f"witness:bounding:{pid}")
            eq(mw["chain_windows_y"], [[M(a),M(b)] for a,b in best["chain"]], f"witness:chain:{pid}")
            eq(mw["exit"]["mode"], best["exit_mode"], f"witness:exit_mode:{pid}")
            eq(mw["exit"]["to_band_centre_y"], M(cw), f"witness:exit_centre:{pid}")
            eq(mw["exit"]["descent_distance_mm"], M(best["dist"]), f"witness:descent_dist:{pid}")
            if best["exit_mode"]=="descent_in_west_slice":
                eq(mw["exit"]["descent_column_x"], [M(west_descent[0]),M(west_descent[1])], f"witness:descent_col:{pid}")
            eq(mw["alternative_windows_same_side"], [[M(a),M(b)] for c2 in candidates[1:] for a,b in [c2["window"]] if c2["side"]==best["side"]], f"witness:alt_windows:{pid}")
            eq(mw["entry"]["x_centre_range"], [M(east_rise[0]),M(east_rise[1])], f"witness:entry_x:{pid}")
            eq(mw["entry"]["from_band_centre_y"], M(ce), f"witness:entry_centre:{pid}")
            if not any(a<=ce<=b for a,b in east_rise_free): bad(f"witness:entry_centre_not_free:{pid}"); per_ok=False
            # independent freeness of the traverse window across the whole chip zone
            win=(wv[0],wv[1])
            if win[1]-win[0] < EXT: bad(f"witness:window_too_small:{pid}"); per_ok=False
            for b in blockers:
                if b["ky"][0] < win[1] and b["ky"][1] > win[0]: bad(f"witness:window_blocked:{pid}:{b['ref']}"); per_ok=False
            if best["exit_mode"]=="descent_in_west_slice":
                if not any(contains(c2,win) and contains(c2,wcop) for c2 in slices[0]["channels"]):
                    bad(f"witness:descent_channel:{pid}"); per_ok=False
            else:
                if not contains(win,wcop): bad(f"witness:direct_exit_containment:{pid}"); per_ok=False
            # coexistence alternative (if emitted, verify; if derivable, require)
            alt=None
            for c0 in sorted(slices[-1]["channels"]):
                run=chain_west(c0)
                if run is None or contains(run,wcop): continue
                if any(contains(c2,run) and contains(c2,wcop) for c2 in slices[0]["channels"]): continue
                alo,ahi=run[0]+EXT2,run[1]-EXT2
                if ahi<alo: continue
                forbid=[]
                for oe,ow in others:
                    forbid+=[(oe-PITCH_HM,oe+PITCH_HM),(ow-PITCH_HM,ow+PITCH_HM)]
                allowed=isub((alo,ahi),forbid)
                if not allowed: continue
                rise_span=(min(run[0],wcop[0]),max(run[1],wcop[1]))
                crosses=any(ow+PITCH_HM//2>rise_span[0] and ow-PITCH_HM//2<rise_span[1] for oe,ow in others)
                alt=(run,allowed,crosses); break
            malt=mw.get("coexistence_alternative")
            if alt and not malt: bad(f"witness:coexistence_alt_missing:{pid}"); per_ok=False
            if alt and malt:
                run,allowed,crosses=alt
                eq(malt["physical_channel_y"], [M(run[0]),M(run[1])], f"witness:alt_channel:{pid}")
                eq(malt["coexistence_feasible_centre_windows_y"], [[M(a),M(b)] for a,b in allowed], f"witness:coex_windows:{pid}")
                eq(malt["west_rise_in_corridor_x"], [M(west_rise[0]),M(west_rise[1])], f"witness:alt_rise_x:{pid}")
                eq(malt["west_rise_in_corridor_crossing"].startswith("FORBIDDEN"), crosses, f"witness:alt_crossing:{pid}")
                eq(malt["crossing_free_rise_x_le"], M(j34_kx0-EXT2), f"witness:alt_crossing_free:{pid}")
                # independent check: coexistence windows keep pitch distance from other pages' bands
                for win2 in allowed:
                    for oe,ow in others:
                        for oc in (oe,ow):
                            if win2[0] < oc + PITCH_HM and win2[1] > oc - PITCH_HM:
                                bad(f"witness:alt_window_separation:{pid}")
            if not malt and alt is None:
                pass  # no alternative derivable; none emitted — consistent
        witness_all_ok=per_ok and all(w["per_page"][p].get("status")=="WITNESSED" for p in w["per_page"])
        eq(w["all_pages_witnessed"], witness_all_ok, "witness:all_pages_flag")

    # ---------- status / minimal core / verdict (W0R-G2) ----------
    for cid, o in own.items():
        rd=o["rd"]
        expect_status = "SATISFIED" if (o["domain_ok"] and witness_all_ok) else "INFEASIBLE"
        eq(rd["status"], expect_status, f"{cid}:refclk_status")
        if rd["status"]=="SATISFIED":
            if rd["minimal_core"]["members"] != []: bad(f"{cid}:minimal_core_should_be_empty")
            if any(v!=0 for v in (rd["shortage"]["unsatisfied_rows"],rd["shortage"]["separation_violations"],rd["shortage"]["containment_violations"])):
                bad(f"{cid}:shortage_nonzero_but_satisfied")
        else:
            if not rd["minimal_core"]["members"]: bad(f"{cid}:minimal_core_empty_but_infeasible")
            if not (rd["shortage"]["unsatisfied_rows"] or rd["shortage"]["separation_violations"]
                    or rd["shortage"]["containment_violations"] or rd["shortage"]["passage_witness"]=="MISSING"):
                bad(f"{cid}:infeasible_without_shortage_detail")
            if not rd["shortage"]["detail"]: bad(f"{cid}:infeasible_shortage_detail_empty")
            matching=[cert for cert in model["certificates"]
                      if cert.get("kind")=="B1.5_INFEASIBLE_CERT"
                      and cert.get("blocked") in ("REFCLK_resource_domain","REFCLK_passage")
                      and (cert.get("corridor")==cid or cert.get("blocked")=="REFCLK_passage")
                      and cert.get("canonical_core")==rd["minimal_core"]["members"]]
            if not matching: bad(f"{cid}:infeasible_certificate_core_mismatch")
        st={pid:s for pid,s in rd.get("per_page_passage_status",{}).items()}
        eq(st, {p:w["per_page"][p]["status"] for p in w["per_page"]} if w else {}, f"{cid}:passage_status_map")
    data_ok = all(b["feasible"] for c in model["corridors"].values() for b in c["data_bands"].values()) \
              and all(c["joint_data_frame"]["feasible"] for c in model["corridors"].values())
    refclk_ok = all(o["rd"]["status"]=="SATISFIED" for o in own.values())
    expected_verdict = "B1.5 PASS" if (not model["certificates"] and refclk_ok and data_ok and witness_all_ok) else "B1.5 INFEASIBLE_CERT"
    if model["verdict"] not in TERMINAL_VERDICTS: bad("verdict_not_terminal")
    eq(model["verdict"], expected_verdict, "verdict_mismatch")
    for cert in model["certificates"]:
        required={"kind","blocked","corridor","required","available","shortage","conflicts","canonical_core","escape_hatches"}
        required_b15={"kind","blocked","corridor","required","available","shortage","conflicting_resources","canonical_core","escape_hatches"}
        if cert.get("kind")=="B1.5_INFEASIBLE_CERT":
            if not required_b15 <= set(cert): bad("certificate_schema_b15")
        else:
            if set(cert) != required: bad("certificate_schema")
        if not cert.get("canonical_core"): bad("certificate_empty_core")

    verdict="PASS" if not failures else "FAIL"
    OUT.write_text(json.dumps({"artifact":"m13_v57_big_w0r_validation","schema":1,
        "model_sha256":sha(MODEL),"model_revision":model.get("revision"),
        "validator":{"path":str(SELF.relative_to(K2)),"revision":REV,"sha256":sha(SELF)},
        "generator_sha256":sha(GENERATOR_TOOL),
        "failures":failures,"verdict":verdict},indent=1,sort_keys=True)+"\n")
    print(json.dumps({"verdict":verdict,"failures":failures},indent=1))
    return 0 if not failures else 1

if __name__ == "__main__": raise SystemExit(main())
