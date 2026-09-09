#!/usr/bin/env python3
"""P3 v57 S1 — A1.3 几何不变量套件（独立于发射器实现，防同源自证）。

输入契约（未来生成器图纸页的通用形状）：
  page = {
    "page_id": str,
    "paths": { "P": {"points": [[x,y],...], "layers": [...n-1...], "vias": [[x,y],...]},
               "N": {同型} },
    "anchor_pads": {"P": {"chip": [x,y], "conn": [x,y]},
                    "N": {同型} },        # 端点是 pad，必须钉在 path 首/末点
  }
  rules = {"width": 0.205, "p_gap": 0.175, "half_pitch": 0.19,
           "pn_min_edge": 0.155, "max_vias_per_net": 2, "via_od": 0.35}

判定（violations，逐字节确定、纯函数）：
  V1 锚定只读：path 首点 == chip pad、末点 == conn pad（容差 1e-6）
  V2 每线过孔数 ≤ max_vias_per_net
  V3 过孔必须落在 layer 翻转点（该点两侧段层不同，且 F.Cu<->In2.Cu 合法对）
  V4 段层数组长度 == points 数 - 1（节点-层连续性）
  V5 同层水平走廊段 P/N 中心距 == 0.38(2×half_pitch) ± tol（差分对保持）
  V6 同层 P/N 几何最小铜边距 ≥ pn_min_edge（中心距扣线宽）
"""
from __future__ import annotations

from typing import Dict, List

LAYER_PAIRS_OK = {("F.Cu", "In2.Cu"), ("In2.Cu", "F.Cu")}


def _center_dist(ax, ay, bx, by):
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def _horiz_run_layers(paths: Dict[str, Dict], pol: str):
    pts = paths[pol]["points"]
    lyr = paths[pol]["layers"]
    runs = []
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        if abs(y1 - y2) < 1e-9 and lyr[i] in ("F.Cu", "In2.Cu"):
            runs.append((min(x1, x2), max(x1, x2), y1, lyr[i]))
    return runs


def check_page(page: dict, rules: dict) -> List[dict]:
    tol = 1e-6
    viol = []
    for pol in ("P", "N"):
        ph = page["paths"][pol]
        pts, lyr, vias = ph["points"], ph["layers"], ph["vias"]
        ap = page["anchor_pads"][pol]
        pid = page["page_id"]
        if _center_dist(*pts[0], *ap["chip"]) > tol:
            viol.append({"id": pid, "pol": pol, "V": "V1_anchor_start",
                         "got": pts[0], "want": ap["chip"]})
        if _center_dist(*pts[-1], *ap["conn"]) > tol:
            viol.append({"id": pid, "pol": pol, "V": "V1_anchor_end",
                         "got": pts[-1], "want": ap["conn"]})
        if len(vias) > rules["max_vias_per_net"]:
            viol.append({"id": pid, "pol": pol, "V": "V2_via_count",
                         "n": len(vias)})
        if len(lyr) != len(pts) - 1:
            viol.append({"id": pid, "pol": pol, "V": "V4_layer_len",
                         "n_lyr": len(lyr), "n_seg": len(pts) - 1})
            continue
        for vx, vy in vias:
            at_turn = False
            for i in range(len(pts) - 1):
                if _center_dist(vx, vy, *pts[i]) < tol:
                    pair = (lyr[i - 1], lyr[i]) if i > 0 else None
                    if pair in LAYER_PAIRS_OK:
                        at_turn = True
                        break
            if not at_turn:
                viol.append({"id": pid, "pol": pol, "V": "V3_via_turn",
                             "via": [vx, vy]})
    pr = _horiz_run_layers(page["paths"], "P")
    nr = _horiz_run_layers(page["paths"], "N")
    for (pl, phx, py, ply) in pr:
        for (nl, nhx, ny, nly) in nr:
            if ply != nly:
                continue
            ox = min(phx, nhx)
            hx = max(pl, nl)
            if ox <= hx + 1e-9:
                continue
            if abs(abs(py - ny) - 2 * rules["half_pitch"]) > 1e-6:
                viol.append({"id": page["page_id"], "V": "V5_pair_spacing",
                             "d_y": round(abs(py - ny), 4)})
            edge = abs(py - ny) - rules["width"]
            if edge < rules["pn_min_edge"] - 1e-9:
                viol.append({"id": page["page_id"], "V": "V6_pn_min_edge",
                             "edge": round(edge, 4)})
    return viol
