#!/usr/bin/env python3
"""k2_reroute_router_floor_v1.py --- thin wrapper around the in-register maze router (k2_p4_mroute_v1.py) that
raises the exact gate's inter-net clearance model to the kicad-cli netclass floor.

WHY: the ACCEPTANCE authority is kicad-cli DRC (project netclass clearance 0.20 mm), while the frozen
drc_rules.json model says 0.10 mm for LOW_SPEED/GND (registered M-ENG-CLEARANCE-MODEL-DIVERGENCE).  The router
must be at least as strict as the acceptance authority, otherwise it emits copper that kicad-cli flags.
The in-register asset is NOT modified - the patch is applied at import time in this wrapper.

Usage: k2_reroute_router_floor_v1.py --in <board> --drc <drc.json> --out <board> --ledger <json>
        [--margin 3.0] [--floor 0.20] [--only-net NET] [--dry-run]
"""
import argparse, importlib.util, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MROUTE = os.path.join(ROOT, "tools", "k2_p4_mroute_v1.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--margin", type=float, default=3.0)
    ap.add_argument("--floor", type=float, default=0.20)
    ap.add_argument("--only-net", default=None)
    ap.add_argument("--bound-rect", dest="bound_rect", default=None,
                    help="C35 in-loop wall x0,y0,x1,y1 (mm) - set on the maze module so out-of-domain cells "
                         "are never selectable (forwarded, not repaired afterwards)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sp = importlib.util.spec_from_file_location("k2mrfloor", MROUTE)
    mr = importlib.util.module_from_spec(sp); sp.loader.exec_module(mr)
    cv = mr.cv
    orig = cv._req
    cv._req = lambda x, y: max(orig(x, y), a.floor)
    if a.bound_rect:                                  # C35：把域作为**搜索约束**注入（不改迷宫本体）
        mr.WALL_RECT = tuple(float(v) for v in a.bound_rect.split(","))
    s = mr.run(a.src, a.drc, a.out, a.ledger, a.margin, a.only_net, a.dry_run, "dist_asc", None)
    print(json_dumps(s))
    return 0


def json_dumps(o):
    import json
    return json.dumps(o, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
