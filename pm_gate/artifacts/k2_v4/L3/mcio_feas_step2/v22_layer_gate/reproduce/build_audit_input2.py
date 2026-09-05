import json
# Non-circular window-closure: feed the FULL N/S window as dense tracks (0.1mm), engine packs at
# inter_pair_spacing=1.46 → proves how many 1.46-pitch pair-tracks the window genuinely holds.
chip = {"label":"U1 body","y_lo":49.2,"y_hi":58.2,"x_lo":82.35,"x_hi":105.25,"kind":"DEVICE"}
def dense(lo,hi,step=0.1): return [round(lo+i,3) for i in 
    [round(x,3) for x in [lo]]
    ] if False else [round(lo+step*i,3) for i in range(int((hi-lo)/step)+1)]
N=[round(33+0.1*i,3) for i in range(int((49.2-33)/0.1)+1)]
S=[round(58.2+0.1*i,3) for i in range(int((79-58.2)/0.1)+1)]
corridors=[
  {"corridor_id":"E_J2","band":"UP_OUT","layer":"F.Cu","x_range":[105.25,132.65],"tracks_y":N,"obstacles":[chip],"needs_via_escape":False},
  {"corridor_id":"E_J2","band":"DN_IN","layer":"F.Cu","x_range":[105.25,132.65],"tracks_y":S,"obstacles":[chip],"needs_via_escape":False},
  {"corridor_id":"W_MCIO","band":"J3_N","layer":"F.Cu","x_range":[65.05,82.35],"tracks_y":N,"obstacles":[chip],"needs_via_escape":False},
  {"corridor_id":"W_MCIO","band":"J4_S","layer":"F.Cu","x_range":[65.05,82.35],"tracks_y":S,"obstacles":[chip],"needs_via_escape":False},
]
via_zones=[{"id":"WING_N","kind":"CHIP","span_mm":16.2,"obstacles":[]},{"id":"WING_S","kind":"CHIP","span_mm":20.8,"obstacles":[]}]
demands=[]
for corr,band in [("E_J2","UP_OUT"),("E_J2","DN_IN"),("W_MCIO","J3_N"),("W_MCIO","J4_S")]:
    for i in range(8):
        demands.append({"base":f"SEG_{band}_{i}","segname":band,"corridor_id":corr,"band":band,"track_y":0.0,"via_zones":["WING_N" if band in("UP_OUT","J3_N") else "WING_S"],"via_cap":False})
json.dump({"corridors":corridors,"via_zones":via_zones,"cap_walls":[],"demands":demands},open("k2_v4_v22_corridor_audit_input2.json","w"),indent=1)
print("N dense tracks:",len(N),"S dense tracks:",len(S))
