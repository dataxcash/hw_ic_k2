#!/usr/bin/env python3
"""k2_block_relayout_gen_v1.py --- **整块重布生成器**（#K2-421 §四 · 承 #K2-419 §五）。

取代「挪一格」：把**被占端点所属的整块**按**同芯片成品布局政策**确定性重排 ——
**分组 → 每组一条廊道 → 组内长段直走 → 只在组扇出处换层一次**（`REF-CASE-LIBRARY §A1` 政策）。
**确定性 · 零搜索**：廊道按**给定的组序**等分切块（不相交、保序）；组内按**沿排坐标**保序扇出。
"""
from __future__ import annotations
import argparse, json, os, sys


def group_by_row(points, band=2.0):
    """**确定性 · 零搜索**：把端点按**沿排坐标**聚成**连续 y 带**（相邻差 > band 即断带）⇒ 组＝可扇出的"一排"。
    `points`=[(net,x,y,layer)...]；返回 `[[p,...],...]`（组内按 (y,x,net) 保序）。"""
    pts = sorted(points, key=lambda p: (p[2], p[1], p[0]))
    groups, cur = [], []
    for p in pts:
        if cur and (p[2] - cur[-1][2]) > band:
            groups.append(cur); cur = []
        cur.append(p)
    if cur:
        groups.append(cur)
    return groups


def slice_corridors(block_rect, groups, gap=0.2):
    """**确定性**：按**组序**把块沿 x **等分切廊道**（扣 gap）⇒ 廊道**两两不相交、按序覆盖全块**（样板政策）。"""
    x0, y0, x1, y1 = [float(v) for v in block_rect]
    n = len(groups)
    if n <= 0:
        return []
    w = ((x1 - x0) - (n - 1) * gap) / n
    out = []
    for i, g in enumerate(groups):
        cx0 = x0 + i * (w + gap)
        out.append({"group": g, "corridor": [round(cx0, 4), round(y0, 4), round(cx0 + w, 4), round(y1, 4)]})
    return out


def escape_into_corridor(points, corridor, pitch=0.25):
    """**确定性 · 零搜索**：组内端点按**沿排坐标保序**扇出；每条 = 直段入廊道 ＋ **恰一次**换层（若需）。"""
    x0, y0, x1, y1 = corridor
    pts = sorted(points, key=lambda p: (p[2], p[1], p[0]))          # (net,x,y,layer) -> along-row order
    n = len(pts)
    out = []
    for k, (net, px, py, lay) in enumerate(pts):
        ty = round(min(max(py + (k - (n - 1) / 2.0) * pitch, y0), y1), 4)
        out.append({"net": net, "order": k, "from": [px, py], "to": [round(x0, 4), ty],
                    "via": {"at": [round(x0, 4), ty], "layers": [lay, "In5.Cu"]}})
    return out


def row_corridors(rows, occupants, clearance=0.20, pad=0.4):
    """**内容感知 · 确定性 · 零搜索**：每排的廊道 ＝ 含**该排全部端点**、且避开（占位者⊕净空）的**最大净空子矩**；
    取不到 ⇒ **UNPLACEABLE（具名）**（绝不硬塞）。取代等分切片（后者在真板 4/6 容量为 0）。"""
    import importlib.util, os as _os
    _sp = importlib.util.spec_from_file_location(
        "k2rd", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "k2_corridor_redraw_v1.py"))
    rd = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(rd)
    out = []
    for i, row in enumerate(rows):
        xs = [p[1] for p in row]; ys = [p[2] for p in row]
        box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
        pts = [(p[1], p[2]) for p in row]
        sub, _ = rd.clear_subrect_containing_pts(box, occupants, clearance, pts)
        out.append({"row": i, "bbox": [round(v, 4) for v in box],
                    "corridor": list(sub) if sub else None,
                    "status": "OK" if sub else "UNPLACEABLE"})
    return out


def corridor_conservation(corridor, occupants, clearance=0.20, need_mm=0.60):
    """**逐廊道守恒机核（硬）**：`capacity` ＝ 该廊道**自身**的净空子矩窄边（**禁用域/块级空闲代替**）；
    返回 `{capacity_mm, need_mm, pass}`（capacity ≥ need ⇒ 该廊道承载力足）。确定性 · 零搜索。"""
    import importlib.util, os as _os
    _sp = importlib.util.spec_from_file_location(
        "k2rd", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "k2_corridor_redraw_v1.py"))
    rd = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(rd)
    cx, cy = (corridor[0] + corridor[2]) / 2.0, (corridor[1] + corridor[3]) / 2.0
    sub, _ = rd.clear_subrect_containing_pts(corridor, occupants, clearance, [(cx, cy)])
    cap = min(sub[2] - sub[0], sub[3] - sub[1]) if sub else 0.0
    return {"capacity_mm": round(cap, 4), "need_mm": round(need_mm, 4), "pass": cap >= need_mm - 1e-9}


def relayout(block_rect, groups, points_by_group, pitch=0.25, gap=0.2):
    corr = slice_corridors(block_rect, groups, gap)
    out = []
    for c in corr:
        out.append({"group": c["group"], "corridor": c["corridor"],
                    "escapes": escape_into_corridor(points_by_group.get(c["group"], []), c["corridor"], pitch)})
    return {"artifact": "k2_block_relayout_v1", "block_rect": list(block_rect), "corridors": out,
            "policy": "group fanout / long straight runs / exactly ONE layer change per escape / corridors per group (REF-CASE-LIBRARY A1)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    p = json.load(open(a.params, encoding="utf-8"))
    rep = relayout(p["block_rect"], p["groups"], p.get("points_by_group", {}),
                   float(p.get("pitch", 0.25)), float(p.get("gap", 0.2)))
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
