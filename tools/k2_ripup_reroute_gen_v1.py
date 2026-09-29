#!/usr/bin/env python3
"""k2_ripup_reroute_gen_v1.py --- **定点单网先拆后布（新手段 · #K2-416 §五.1(ii)/#K2-417 R1174 已报）**的第一半：
**确定"拆哪些 + 在哪布线"计划**（只读 · 确定性 · 零搜索 · 零板改 · 零考跑）。

对每个残差断口，给出：
  · `rip_set`：落在该廊道内、属于**他网**的**具体铜件**（net/layer/包围盒/**起点**）——即"先拆"对象；
  · `route_request`：该残差的**有界域布线请求**（net / 域内两端点 / 层对 / 廊道矩形 / 目标：先迷宫通，再回补被拆网）；
  · `after_rip_clear`：**把 rip_set 移除后**该廊道是否立刻出现"含两端点的净空子矩"（＝该计划可成的**机验前件**）。
CLI: python3 tools/k2_ripup_reroute_gen_v1.py --board B --drc D --bound-rect x0,y0,x1,y1 [--clearance .2] [--margin 0.4] [--json-out P]
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def plan(board, drc_path, bound, clearance=0.20, margin=0.4):
    import pcbnew as P
    AUD = _load("k2_corridor_occupancy_audit_v1", "tools/k2_corridor_occupancy_audit_v1.py")
    RDR = _load("k2_corridor_redraw_v1", "tools/k2_corridor_redraw_v1.py")
    DEV = _load("k2_deviation_gen_v1", "tools/k2_deviation_gen_v1.py")
    b = P.LoadBoard(board)
    out = {"artifact": "k2_ripup_reroute_plan_v1", "ts": "2026-09-29", "board": board,
           "authority": "#K2-416 sec.5.1(ii) new means (reported in R1174): targeted single-net rip-up + re-route.",
           "bound_rect": list(bound), "clearance_mm": clearance, "corridor_margin_mm": margin,
           "items": [], "OWNER-ITEMS": 0}
    for pr in DEV.pairs(json.load(open(drc_path, encoding="utf-8"))):
        a, bp = DEV._clamp(pr["p1"], bound), DEV._clamp(pr["p2"], bound)
        rect = (max(bound[0], min(a[0], bp[0]) - margin), max(bound[1], min(a[1], bp[1]) - margin),
                min(bound[2], max(a[0], bp[0]) + margin), min(bound[3], max(a[1], bp[1]) + margin))
        layers = sorted(set(pr["layers"]), key=pr["layers"].index)
        occ = [o for o in AUD.occupant_rects(b, layers, pr["net"], clearance)
               if AUD.rect_gap(rect, o["bbox"]) <= clearance + 1e-9]
        wit, _ = RDR.clear_subrect_containing_pts(rect, occ and [o["bbox"] for o in occ], clearance, [a, bp])
        wit_after, _ = RDR.clear_subrect_containing_pts(rect, [], clearance, [a, bp])
        out["items"].append({
            "net": pr["net"], "from_desc": pr["desc"][0][:56], "to_desc": pr["desc"][1][:56],
            "corridor_rect": [round(v, 4) for v in rect], "layers": layers,
            "route_request": {"net": pr["net"], "p1_in_domain": [round(a[0], 4), round(a[1], 4)],
                              "p2_in_domain": [round(bp[0], 4), round(bp[1], 4)],
                              "layers": layers, "bound_rect": [round(v, 4) for v in rect],
                              "goal": "maze-first inside the corridor; then re-route the ripped net(s)"},
            "rip_set": [{"net": o["net"], "layer": o["layer"], "kind": o["kind"], "bbox": [round(v, 4) for v in o["bbox"]],
                         "at": o.get("at")} for o in occ],
            "n_rip": len(occ),
            "rip_nets": sorted({o["net"] for o in occ}),
            "after_rip_clear": bool(wit_after),
            "witness_now": bool(wit)})
    out["summary"] = {"n": len(out["items"]),
                      "n_rip_total": sum(i["n_rip"] for i in out["items"]),
                      "all_clear_after_rip": all(i["after_rip_clear"] for i in out["items"])}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--drc", required=True)
    ap.add_argument("--bound-rect", dest="bound_rect", required=True)
    ap.add_argument("--clearance", type=float, default=0.20)
    ap.add_argument("--margin", type=float, default=0.4)
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    rep = plan(a.board, a.drc, tuple(float(v) for v in a.bound_rect.split(",")), a.clearance, a.margin)
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
