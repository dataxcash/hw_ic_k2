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


def row_blockers(row, occupants_by_net, clearance=0.20):
    """**确定性 · 零搜索**：某排被**哪些网**围死 —— 对排内每个端点，取"膨胀后 bbox 含该点"的网 ⇒ 并集（排序）。
    这就是该排的**让位输入**（谁必须让）。`occupants_by_net`={net:[bbox,...]}。"""
    own = {p[0] for p in row}
    out = set()
    for (net, px, py, _lay) in row:
        for n, boxes in occupants_by_net.items():
            if n in own:
                continue
            for bb in boxes:
                if (bb[0] - clearance - 1e-9 <= px <= bb[2] + clearance + 1e-9
                        and bb[1] - clearance - 1e-9 <= py <= bb[3] + clearance + 1e-9):
                    out.add(n)
    return sorted(out)


def row_relayout_request(row, occupants_by_net, clearance=0.20):
    """**确定性 · 零搜索**：一排的**重排请求** ＝ { 具名堵网 → 让位量/方向 }。
    某网的让位量 ＝ `max over 该排端点( clearance − 该点到该网膨胀 bbox 的距离 )`（≥0；一个网一个数，移一次）；方向＝**背离该排中心**。"""
    import math as _m
    cy = sum(p[2] for p in row) / len(row)
    names = row_blockers(row, occupants_by_net, clearance)
    out = []
    for n in names:
        need = 0.0
        for (net, px, py, _l) in row:
            for bb in occupants_by_net.get(n, []):
                cyt = (bb[1] + bb[3]) / 2.0
                # EXACT: push the NEAR edge to clearance past the point (frees it even when covered)
                near = (bb[1] - clearance - py) if cyt >= py else (py - (bb[3] + clearance))
                need = max(need, clearance - near)
        out.append({"net": n, "move_mm": max(0.0, round(need, 4)),
                    "dir": "+y" if (sum(o["bbox"][1] + o["bbox"][3] for o in
                                        [{"bbox": bb} for bb in occupants_by_net.get(n, [])]) / (2 * max(1, len(occupants_by_net.get(n, []))))) >= cy
                                else "-y"})
    out.sort(key=lambda z: (z["move_mm"], z["net"]))
    for i, z in enumerate(out):
        z["yield_order"] = i
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


def plan_from_board(board, drc, rect, clearance=0.20, need=0.60, band=2.0, pad=0.4):
    """**一条命令端到端**（#K2-423 §三.①）：真板 → 分组 → 内容感知廊道 → 逐廊道守恒 → 每排重排请求 → **每线确定图**。
    返回 rep（含 `buildability` 与 `closing` 判据状态）。只读 · 确定性 · 零搜索。"""
    import importlib.util as _iu, os as _os, collections as _c, json as _j
    _R = _os.path.dirname(_os.path.abspath(__file__))
    def _m(n, f):
        sp = _iu.spec_from_file_location(n, _os.path.join(_R, f)); m = _iu.module_from_spec(sp); sp.loader.exec_module(m); return m
    AUD, DEV, RD = _m("ka", "k2_corridor_occupancy_audit_v1.py"), _m("kd", "k2_deviation_gen_v1.py"), _m("kr", "k2_corridor_redraw_v1.py")
    import pcbnew as P
    b = P.LoadBoard(board)
    eps = []
    for pr in DEV.pairs(_j.load(open(drc, encoding="utf-8"))):
        for p_ in (pr["p1"], pr["p2"]):
            c = DEV._clamp(p_, rect); eps.append((pr["net"], c[0], c[1], pr["layers"][0]))
    rows = group_by_row(eps, band)
    byn = _c.defaultdict(list)
    for o in AUD.occupant_rects(b, ["F.Cu", "In5.Cu"], "__x__", clearance):
        byn[o["net"]].append(o["bbox"])
    out = []
    for i, rw in enumerate(rows):
        own = {p[0] for p in rw}
        occ = [bb for n, bbs in byn.items() if n not in own for bb in bbs]
        xs = [p[1] for p in rw]; ys = [p[2] for p in rw]
        box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
        sub, _ = RD.clear_subrect_containing_pts(box, occ, clearance, [(p[1], p[2]) for p in rw])
        cons = corridor_conservation(sub, occ, clearance, need) if sub else {"capacity_mm": 0.0, "need_mm": need, "pass": False}
        _obn = {n: byn[n] for n in byn if n not in own}
        req = row_relayout_request(rw, _obn, clearance)
        # **内容感知分配版**：先应用本排的确定性让位，再重建廊道（若由不通转通 ⇒ 记 OK_BY_YIELD）
        # **联合让位（有界多趟 · 确定性 · 非搜索）**：每趟在当前（已让位）场上重算请求并再让；固定 2 趟。
        _state = {n: [list(b) for b in bbs] for n, bbs in _obn.items()}
        for _pass in range(2):
            _rq = row_relayout_request(rw, _state, clearance)
            if not any(z["move_mm"] > 0 for z in _rq):
                break
            for _z in _rq:
                _s = 1.0 if _z["dir"] == "+y" else -1.0
                _state[_z["net"]] = [[b[0], b[1] + _s * _z["move_mm"], b[2], b[3] + _s * _z["move_mm"]] for b in _state.get(_z["net"], [])]
        _occ2 = [bb for n, bbs in _state.items() if n not in own for bb in bbs]
        # **廊道重画（有界 pad 阶梯 · 确定性 · 非搜索）**：先小盒，不过则按固定阶梯放大搜索盒
        sub2, cons2, _pad = None, {"capacity_mm": 0.0, "need_mm": need, "pass": False}, pad
        for _pd in (pad, pad * 2, pad * 4):
            _box = (min(xs) - _pd, min(ys) - _pd, max(xs) + _pd, max(ys) + _pd)
            _s, _ = RD.clear_subrect_containing_pts(_box, _occ2, clearance, [(p[1], p[2]) for p in rw])
            _c = corridor_conservation(_s, _occ2, clearance, need) if _s else {"capacity_mm": 0.0, "need_mm": need, "pass": False}
            sub2, cons2, _pad = _s, _c, _pd
            if _c["pass"]:
                break
        esc = escape_into_corridor(rw, sub2 or sub) if (sub2 or sub) else []
        out.append({"row": i, "nets": sorted(own), "n_points": len(rw),
                    "corridor": list(sub) if sub else None, "conservation": cons,
                    "corridor_after_yield": list(sub2) if sub2 else None, "conservation_after_yield": cons2,
                    "status": ("OK" if (sub and cons["pass"]) else ("OK_BY_YIELD" if cons2["pass"] else "BLOCKED")),
                    "pad_used": round(_pad, 3),
                    "relayout_request": req, "per_line": esc,
                    "buildability": "no_move" if (sub and cons["pass"]) else "relocation_listed"})
    rep = {"artifact": "k2_block_relayout_plan_v1", "board": board, "rect": list(rect), "rows": len(rows),
           "corridors": out, "policy": "REF-CASE-LIBRARY A1: group fanout / straight runs / one layer change per escape",
           "closing": {"1_one_command_end_to_end": True,
                       "2_per_line_geometry": sum(1 for o in out if o["per_line"]),
                       "3_conservation_pass": sum(1 for o in out if o["conservation"]["pass"]),
                       "3b_conservation_pass_after_yield": sum(1 for o in out if o["conservation_after_yield"]["pass"]),
                       "4_buildability": "no_move" if all(o["buildability"] == "no_move" for o in out) else "relocation_listed",
                       "n_rows": len(rows)}, "OWNER-ITEMS": 0}
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board"); ap.add_argument("--drc"); ap.add_argument("--rect")
    ap.add_argument("--params")
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    if a.board and a.drc and a.rect:
        rep = plan_from_board(a.board, a.drc, tuple(float(v) for v in a.rect.split(",")))
    else:
        p = json.load(open(a.params, encoding="utf-8"))
        rep = relayout(p["block_rect"], p["groups"], p.get("points_by_group", {}),
                       float(p.get("pitch", 0.25)), float(p.get("gap", 0.2)))
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
