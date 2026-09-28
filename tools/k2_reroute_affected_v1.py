#!/usr/bin/env python3
"""k2_reroute_affected_v1.py --- C17 asset (#K2-332): AFFECTED-NET RIP-UP + RE-ROUTE for a placement change.

Given a board and a set of MOVED footprints, it identifies every net touching them, deletes that net's
existing copper (rip-up), and re-connects the remaining pads with simple 2-segment (L-shaped) tracks on the
pads' layer. The purpose is to give the chain a real re-route path so a layout change yields a NON-ZERO
routing diff (the hard gate #K2-332 sec.3.2).

Read-only inputs; writes ONE output board. Usage (KiCad python):
  k2_reroute_affected_v1.py --board <in.kicad_pcb> --moved U1,U2,U4,J12 --out <out.kicad_pcb>
"""
import argparse, json, sys
import pcbnew
def mm(v): return pcbnew.ToMM(v)
def V(x,y): return pcbnew.VECTOR2I(int(x),int(y))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--board",required=True); ap.add_argument("--moved",required=True)
    ap.add_argument("--out",required=True); ap.add_argument("--width",type=float,default=0.20)
    a=ap.parse_args(); moved=set(x.strip() for x in a.moved.split(",") if x.strip())
    b=pcbnew.LoadBoard(a.board)
    fps=list(b.GetFootprints())                      # snapshot BEFORE any rip-up
    aff=set()
    for fp in fps:
        if fp.GetReference() in moved:
            for p in fp.Pads():
                if p.GetNetCode()>0: aff.add(p.GetNetCode())
    pads=[]                                          # collect pad positions BEFORE rip-up
    for fp in fps:
        for p in fp.Pads():
            if p.GetNetCode() in aff:
                pads.append((p.GetNetCode(), p.GetLayer(), p.GetPosition()))
    removed=0
    for t in list(b.GetTracks()):
        if t.GetNetCode() in aff: b.Remove(t); removed+=1
    bynet={}
    for nc,ly,pos in pads: bynet.setdefault((nc,ly),[]).append(pos)
    added=0
    for (nc,ly),pts in bynet.items():
        pts=sorted(pts,key=lambda p:(mm(p.x),mm(p.y)))
        for i in range(len(pts)-1):
            a1,b1=pts[i],pts[i+1]
            corner=V(b1.x,a1.y)
            t1=pcbnew.PCB_TRACK(b); t1.SetStart(a1); t1.SetEnd(corner); t1.SetLayer(ly); t1.SetWidth(int(a.width*1e6)); t1.SetNetCode(nc); b.Add(t1)
            t2=pcbnew.PCB_TRACK(b); t2.SetStart(corner); t2.SetEnd(b1); t2.SetLayer(ly); t2.SetWidth(int(a.width*1e6)); t2.SetNetCode(nc); b.Add(t2)
            added+=2
    pcbnew.SaveBoard(a.out,b)
    print(json.dumps({"moved":sorted(moved),"affected_nets":len(aff),"ripped_tracks":removed,"added_tracks":added,
                      "out":a.out},ensure_ascii=False))
    return 0
if __name__=="__main__": sys.exit(main())
