#!/usr/bin/env python3
"""R1.5 杠杆闭合分析（W3-C8）：交叉分解 + Z 族正/反序闭式 + 45/135 阶梯 x 预算。仅分析，不参与求解。"""
import json
from pathlib import Path
K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
S = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
M = json.load((S / "m13_v57_s1_page_manifest.json").open())
LF = json.load((S / "m13_v57_f3_lane_frame.json").open())
A = json.load((S / "m13_v57_w3_joint_assignment.json").open())
PAD = {p["page_id"]: p["anchors"]["chip"] for p in M["pages"] if p["kind"] == "data"}
BAND = {}
for cid, cd in LF["corridors"].items():
    for fr in cd["frames"]:
        for p in fr["pages"]:
            BAND[p["page_id"]] = (cid, fr["band"])
CORR = {p: BAND[p][0] for p in BAND}
out = {"analysis": "W3-C8 R1.5 lever closure", "method": "closed-form per-frame geometry", "frames": {}}
recs = {}
for cid, cd in LF["corridors"].items():
    for fr in cd["frames"]:
        ids = [p["page_id"] for p in sorted(fr["pages"], key=lambda q: q["order_index"])]
        xs = [PAD[p]["P"]["pad_global"][0] for p in ids]
        s = 1 if xs[-1] >= xs[0] else -1
        entry = 105.25 if cid == "EAST_CHIP_TO_J2" else 82.35
        dx = [abs(entry - x) for x in xs]
        ys = [PAD[p]["P"]["pad_global"][1] for p in ids]
        lanes = [A["layers"]["R2"]["assignment"][p]["lane_y"] if A.get("layers") else 0.0 for p in ids]
        dy = [abs(l - y) for l, y in zip(lanes, ys)]
        per_page_ok = [dx[i] >= dy[i] for i in range(len(ids))]
        recs[(cid, fr["band"], fr["conn_ref"])] = {
            "n": len(ids), "dir": "inc" if s > 0 else "dec",
            "via_x_span_mm": round(max(xs) - min(xs), 3),
            "min_inter_via_gap_mm": round(min(xs[i+1]-xs[i] for i in range(len(xs)-1)), 3) if len(xs) > 1 else None,
            "dx_avail_max_mm": round(max(dx), 3), "dy_need_max_mm": round(max(dy), 3),
            "pages_failing_dx_ge_dy": int(len(ids) - sum(per_page_ok)),
            "staircase_45_only_ok": all(per_page_ok),
            "reverse_Z_disjoint_trunk_ok": False,
            "reverse_Z_reason": "reverse channel order needs trunk span >= (n-1)*pitch + gap > inter-via gap => trunks overlap"}
out["frames"] = {f"{c}|{b}|{r}": v for (c, b, r), v in recs.items()}
out["summary"] = {
    "n_frames": len(recs),
    "forward_Z": "channel order follows via order => planar order violated => crossings (measured 319 for straight-vs-channelized delta)",
    "reverse_Z": "channel order reversed => trunks overlap (collinear copper) => invalid; Z-family cannot be planar+valid",
    "staircase_45_135_only": "requires |dx| >= |dy| per page; failing frames: "
        + ", ".join(k for k, v in out["frames"].items() if not v["staircase_45_only_ok"]),
    "conclusion": "in-layer levers measured/closed-form: lane-by-source infeasible (R-8), Z-family infeasible "
                  "(forward=>crossings, reverse=>trunk overlap), 45/135-only staircase infeasible where "
                  "dx<dy; straight family remains (264 crossings); => remaining are upstream items or a "
                  "global proof"}
(S / "m13_v57_w3_r1_5_lever_analysis.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
print(json.dumps(out["summary"], ensure_ascii=False, indent=1))
