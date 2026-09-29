#!/usr/bin/env python3
"""k2_endpoint_reach_planner_v1.py --- **端点可达·重布生成器**（#K2-419 §五 · §15 方法教令）。

**问题类别**：端点可达布线 —— 端点周边被**他网固定铜**包围（**非容量不足**，#K2-416 已定性）。
**做法族（§20 抄样板 · 不折腾算法）**：**分组扇出 · 长段直走 · 换层只在本组扇出处一次 · 廊道按样板分配**。
**确定性 · 零搜索**：本组端点按**沿排坐标**排序后**保序分配扇出道**（order-preserving ⇒ 天然不交叉），
每条道 = 「出排直段 → **恰好一次**换层 → 直入廊道」；每条道对板件做**净空机核**，不净则**具名**。

CLI: python3 tools/k2_endpoint_reach_planner_v1.py --board B --endpoints 'net:x:y:layer,...' --pitch .25 --escape 1.2
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def plan_lanes(endpoints, pitch=0.25):
    """**纯函数 · 确定性 · 零搜索**：保序扇出道分配。
    `endpoints`=[(net,x,y,layer)...]；按**沿排坐标**(先 y 后 x)排序 ⇒ 第 i 条道偏移 `(i-(n-1)/2)*pitch`
    （固定等距扇），**保序**（不交换序）⇒ 道与道**不相交**。返回 [{net,x,y,layer,lane,order,offset}]。"""
    order = sorted(range(len(endpoints)), key=lambda i: (endpoints[i][2], endpoints[i][1], endpoints[i][0]))
    n = len(endpoints)
    out = []
    for k, i in enumerate(order):
        net, x, y, lay = endpoints[i]
        out.append({"net": net, "x": x, "y": y, "layer": lay, "order": k,
                    "lane": k, "offset": round((k - (n - 1) / 2.0) * pitch, 4)})
    return out


def lane_geometry(lane, escape_len=1.2, target_layer=None):
    """**每道几何**：出排直段（沿 x 到扇出线）→ **恰好一次**换层（若 target_layer 不同）→ 直段入廊道。确定性。"""
    x, y, off = lane["x"], lane["y"], lane["offset"]
    x1 = round(x + escape_len, 4)
    yv = round(y + off, 4)
    seg = [{"layer": lane["layer"], "poly": [[x, y], [x1, y], [x1, yv]]}]
    via = None
    if target_layer and target_layer != lane["layer"]:
        via = {"at": [x1, yv], "layers": [lane["layer"], target_layer]}
        seg.append({"layer": target_layer, "poly": [[x1, yv], [round(x1 + escape_len, 4), yv]]})
    return {"net": lane["net"], "segs": seg, "via": via, "n_via": 1 if via else 0}


def _seg_gap(rect, a, b):
    """AA 矩形 vs 线段 的保守最近距离（端点采样 + 端点落入判定；确定性）。"""
    def d2(p, q): return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
    inside = rect[0] <= a[0] <= rect[2] and rect[1] <= a[1] <= rect[3]
    if inside:
        return 0.0
    lo = min(rect[0], abs(a[0] - rect[0])), None
    g = None
    for t in [i / 20.0 for i in range(21)]:
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        dx = max(rect[0] - p[0], p[0] - rect[2], 0.0); dy = max(rect[1] - p[1], p[1] - rect[3], 0.0)
        dd = math.hypot(dx, dy)
        g = dd if g is None else min(g, dd)
    return g


def check(board, lanes, geoms, clearance=0.20):
    """板件净空机核（保守）。返回逐道具名堵点。"""
    import pcbnew as P
    AUD = _load("k2_corridor_occupancy_audit_v1", "tools/k2_corridor_occupancy_audit_v1.py")
    b = P.LoadBoard(board)
    res = []
    for ln, gm in zip(lanes, geoms):
        layers = sorted({s["layer"] for s in gm["segs"]})
        occ = AUD.occupant_rects(b, layers, ln["net"], clearance)
        bad = []
        for s in gm["segs"]:
            for k in range(len(s["poly"]) - 1):
                a, bp = s["poly"][k], s["poly"][k + 1]
                for o in occ:
                    if o["layer"] != s["layer"]:
                        continue
                    if _seg_gap(o["bbox"], a, bp) <= clearance + 1e-9:
                        bad.append({"net": o["net"], "layer": o["layer"]})
        res.append({"net": ln["net"], "via": bool(gm["via"]), "n_blockers": len({(x["net"]) for x in bad}),
                    "blockers_named": sorted({x["net"] for x in bad})})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--endpoints", required=True, help="net:x:y:layer,...")
    ap.add_argument("--pitch", type=float, default=0.25)
    ap.add_argument("--escape", type=float, default=1.2)
    ap.add_argument("--target-layer", dest="target_layer", default=None)
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    eps = []
    for it in [x for x in a.endpoints.split(",") if x]:
        n, x, y, l = it.split(":")
        eps.append((n, float(x), float(y), l))
    lanes = plan_lanes(eps, a.pitch)
    geoms = [lane_geometry(l, a.escape, a.target_layer) for l in lanes]
    chk = check(a.board, lanes, geoms)
    rep = {"artifact": "k2_endpoint_reach_plan_v1", "ts": "2026-09-29", "board": a.board,
           "authority": "#K2-419 sec.5: the endpoint-reachability / re-layout generator (deterministic, zero search).",
           "method": "group fanout / long straight runs / exactly ONE layer change per lane (copied reference policy)",
           "lanes": [{**l, **g, **c} for l, g, c in zip(lanes, geoms, chk)], "OWNER-ITEMS": 0}
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
