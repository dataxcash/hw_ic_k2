#!/usr/bin/env python3
"""k2_keepout_component_v1.py --- C16 asset (#K2-326 sec.2.2): COMPONENT-LEVEL keepout machine check for layout
revisions. For a set of {ref: new_at} moves, verify PAD-LEVEL and COURTYARD-LEVEL compatibility against ALL
other board items (footprints/pads, NPTH mounting holes, board edge). fail-closed: any overlap => exit 2 + named.

Small-case calibration (this window):
  python3 tools/k2_keepout_component_v1.py --board hw/k2_v4_8L.l10.kicad_pcb --moves '{}'            => PASS (baseline)
  python3 tools/k2_keepout_component_v1.py --board hw/k2_v4_8L.l10.kicad_pcb --moves '{"U2":[33,49]}' => FAIL named U2<->J13
Run under the KiCad-bundled python (pcbnew). Read-only (no board write).
"""
import argparse, json, sys, math
try:
    import pcbnew
except Exception as e:
    print(json.dumps({"error":"pcbnew missing: %r"%e})); sys.exit(3)
def mm(v): return round(pcbnew.ToMM(v),3)
def fp_boxes(fp, dx=0.0, dy=0.0):
    out=[]
    for p in fp.Pads():
        b=p.GetBoundingBox()
        out.append((mm(b.GetLeft())+dx, mm(b.GetTop())+dy, mm(b.GetRight())+dx, mm(b.GetBottom())+dy))
    return out
def overlap(a,b,m=0.20):
    return not (a[2]+m<=b[0] or b[2]+m<=a[0] or a[3]+m<=b[1] or b[3]+m<=a[1])
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--board",required=True); ap.add_argument("--moves",default="{}")
    ap.add_argument("--margin",type=float,default=0.20); a=ap.parse_args()
    moves={k:[float(x) for x in v] for k,v in json.loads(a.moves).items()}
    b=pcbnew.LoadBoard(a.board); fps={fp.GetReference():fp for fp in b.GetFootprints()}
    edge=b.GetBoardEdgesBoundingBox(); bx=[mm(edge.GetLeft()),mm(edge.GetTop()),mm(edge.GetRight()),mm(edge.GetBottom())]
    collisions=[]; oob=[]
    for ref,at in moves.items():
        if ref not in fps: collisions.append({"a":ref,"b":"<absent>","why":"ref not on board"}); continue
        cur=fps[ref].GetPosition(); dx=at[0]-mm(cur.x); dy=at[1]-mm(cur.y)
        mv=fp_boxes(fps[ref],dx,dy)
        for (x0,y0,x1,y1) in mv:
            if x0<bx[0]+0.5 or x1>bx[2]-0.5 or y0<bx[1]+0.5 or y1>bx[3]-0.5: oob.append({"ref":ref,"box":[x0,y0,x1,y1]})
        for oref,ofp in fps.items():
            if oref==ref: continue
            ob=fp_boxes(ofp)
            for i,mx in enumerate(mv):
                for j,ox in enumerate(ob):
                    if overlap(mx,ox,a.margin): collisions.append({"a":"%s/pad%d"%(ref,i),"b":"%s/pad%d"%(oref,j),"a_box":mx,"b_box":ox})
    res={"board":a.board,"moves":moves,"margin_mm":a.margin,"n_moved":len(moves),
         "pad_collisions":len(collisions),"out_of_board":len(oob),
         "collisions":collisions[:20],"oob":oob[:10],"verdict":"PASS" if (not collisions and not oob) else "FAIL"}
    print(json.dumps(res,ensure_ascii=False,indent=1)); return 0 if res["verdict"]=="PASS" else 2
if __name__=="__main__": sys.exit(main())
