#!/usr/bin/env python3
# k2_p5_zone_prune_v1.py  (v2: + BuildConnectivity before Fill)  (#K2-548 sec.1.2: mechanism-level call delegated to ENG; the ENG's ruling is
#   "isolated copper => DELETE the DRC-named orphan zone", because the chain's dispose-islands only UnFills
#   it, and then ANY fresh refill recreates the island => "zero isolated copper" and "fresh fill" can never
#   be true together. This tool is the version-bumped action: DELETE those zones, then refill, then save.
#   Usage: k2_p5_zone_prune_v1.py <board_in> <drc_json_with_isolated_copper> <board_out>
import json, sys
import pcbnew

def main():
    src, drc_p, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
    j = json.load(open(drc_p, encoding="utf-8"))
    uu = []
    for x in (j.get("violations") or []):
        if x.get("type") == "isolated_copper":
            for it in (x.get("items") or []):
                if it.get("uuid"):
                    uu.append(str(it["uuid"]))
    uu = sorted(set(uu))
    b = pcbnew.LoadBoard(src)
    zmap = {}
    for z in b.Zones():
        try:
            zmap[str(z.m_Uuid.AsString())] = z
        except Exception:
            pass
    hit = [u for u in uu if u in zmap]
    for u in hit:
        z = zmap[u]
        try:
            b.Remove(z)
        except Exception:
            b.Delete(z)
    # #K2-548/#K2-549 (v2, #K2-547 gate B): a plane/large-area fill NEEDS connectivity data - without
    # `BuildConnectivity()` the standalone pcbnew path leaves the INNER PLANE layers unfilled, so the saved
    # fill != the plot-time recompute and the packager's zone gate correctly refuses (R1878: In1/In3/In4/In6).
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(out_p)
    print(json.dumps({"isolated_items": len(uu), "zone_uuids_found": len(hit), "deleted": len(hit),
                      "unmatched": [u for u in uu if u not in zmap], "out": out_p}, ensure_ascii=False))

if __name__ == "__main__":
    main()
