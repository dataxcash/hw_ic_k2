import json
# 6L corridor SPEC for capacity_audit — L2 frozen corridor rows + ruled 1.46 pitch.
# Obstacles = chip body (tracks run OUTSIDE chip in x, and in y they are in N/S windows above/below chip).
# Connector pads are TERMINATIONS (tracks connect to them), NOT mid-run blockers → excluded from obstacles.
chip = {"label":"U1 DS320PR1601 body","y_lo":49.2,"y_hi":58.2,"x_lo":82.35,"x_hi":105.25,"kind":"DEVICE"}
def band_tracks(center, n=8, pitch=1.46):
    return [round(center + (i-(n-1)/2)*pitch, 3) for i in range(n)]
corridors = [
  {"corridor_id":"E_J2","band":"UP_OUT","layer":"F.Cu","x_range":[105.25,132.65],"tracks_y":band_tracks(42.8),"obstacles":[chip],"needs_via_escape":False},
  {"corridor_id":"E_J2","band":"DN_IN","layer":"F.Cu","x_range":[105.25,132.65],"tracks_y":band_tracks(64.0),"obstacles":[chip],"needs_via_escape":False},
  {"corridor_id":"W_MCIO","band":"J3_N","layer":"F.Cu","x_range":[65.05,82.35],"tracks_y":band_tracks(42.0),"obstacles":[chip],"needs_via_escape":False},
  {"corridor_id":"W_MCIO","band":"J4_S","layer":"F.Cu","x_range":[65.05,82.35],"tracks_y":band_tracks(64.5),"obstacles":[chip],"needs_via_escape":False},
]
via_zones = [{"id":"WING_N","kind":"CHIP","span_mm":16.2,"obstacles":[]},{"id":"WING_S","kind":"CHIP","span_mm":20.8,"obstacles":[]}]
demands=[]
for corr,band,wings in [("E_J2","UP_OUT",["WING_N"]),("E_J2","DN_IN",["WING_S"]),("W_MCIO","J3_N",["WING_N"]),("W_MCIO","J4_S",["WING_S"])]:
    ty = (band_tracks(42.0) if band=="J3_N" else band_tracks(42.8) if band=="UP_OUT" else band_tracks(64.5) if band=="J4_S" else band_tracks(64.0))
    for i in range(8):
        demands.append({"base":f"SEG_{band}_{i}","segname":band,"corridor_id":corr,"band":band,"track_y":ty[i],"via_zones":wings,"via_cap":False})
audit={"corridors":corridors,"via_zones":via_zones,"cap_walls":[],"demands":demands}
json.dump(audit,open("k2_v4_v22_corridor_audit_input.json","w"),indent=1)
print("corridors=%d via_zones=%d demands=%d"%(len(corridors),len(via_zones),len(demands)))
