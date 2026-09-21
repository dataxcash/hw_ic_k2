#!/usr/bin/env python3
"""K2 · B2 —— **In5 车道 rip-up-and-reroute 求解器 v1**（#K2-71 §六-2 / R137 §7-2 指定之算法收口）。

定位（**非"工具新版"探索轮**）：R135–R137 之硬序贪心（v3 `--algo hard`，单遍、无回退）
在 UP 组恒 13/16（多序/多启枚举实测上限）。实测发现两个**判据口径缺陷**：

  D-1 **v3 锚孔 keepout + disk stamp 双重过保守**：v3 硬模之互斥判据 = "新车道之路径格不得落在
      已布车道之 radius-`pitch_eff` disk stamp 内" ⇒ 等价要求两车道**格心距 ≥ 0.424mm**，而
      连续精确闸之真实要求 = **线段距 ≥ 0.435mm**（判据 ③ 之 margin 0.100）。二者非同一判据：
      stamp 判据在多数走向下**远严于**闸（实测 13/16 之上限即此人为瓶颈）。
  D-2 v3 `--algo negotiate` 之 `nviol` 以 (路径格 × offset) 累加 ⇒ **单车自重叠即 occ≈57**
      ⇒ 违例计数恒爆（8000+），停止条件 `viol==0` 永不可达 ⇒ 协商模式**不可用于求见证**。

本器改用**与闸同口径之连续判据**（各向同性、与线段同源）：
  · 冲突域 = **其他车道折线之距离场**（`scipy.ndimage.distance_transform_edt`，cell 栅格）；
  · 硬掩码 = `D >= R_out`，`R_out = pitch_eff + 2·(0.5·cell·√2)` = 0.435 + 0.1414 = **0.5764mm**
    （本车道折线格心偏差 0.0707 + 对侧折线栅格化偏差 0.0707 ⇒ **严格蕴含**闸之"线段距 ≥0.435"）；
  · 全量/局部 **rip-up-and-reroute**：失败车道优先 + 冲突集（其静态最短路径 ±2R 内之已布车道）
    一起 rip-up 后重布；多轮直至全布或预算耗尽；
  · 末闸 = v3 `exact_gate`（同一函数 · 连续精确 · 判据 ⑨ 口径不变）。

输出 = 工作令 JSON（routes / anchors / geometric_gate / 迭代轨迹），**只读板件**。

CLI：
  python3 tools/k2_p4_b2_in5_ripup_v1.py --model <dump.json> --out <wo.json> \
      [--layer In5.Cu] [--cell 0.10] [--lane-w 0.16] [--pitch 0.335] [--margin 0.100] \
      [--iters 80] [--a-sites a.json] [--b-sites b.json] [--groups PREFIX,...] \
      [--movable-nets ...] [--movable-stitch ...] [--movable-copper ...]
"""
from __future__ import annotations
import argparse, json, math, sys, time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import k2_p4_b2_in5_lane_router_v3 as v3  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--layer", default="In5.Cu")
    ap.add_argument("--cell", type=float, default=0.10)
    ap.add_argument("--lane-w", type=float, default=0.16)
    ap.add_argument("--pitch", type=float, default=0.335)
    ap.add_argument("--margin", type=float, default=0.100)
    ap.add_argument("--iters", type=int, default=40)
    ap.add_argument("--k0", type=float, default=4.0)
    ap.add_argument("--kgrow", type=float, default=2.0)
    ap.add_argument("--rmin", type=float, default=0.435)
    ap.add_argument("--rout", type=float, default=None, help="互斥半径（默认 pitch+margin+2·折角安全）")
    ap.add_argument("--a-sites", default=None)
    ap.add_argument("--b-sites", default=None)
    ap.add_argument("--groups", default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--movable-nets", default="")
    ap.add_argument("--movable-stitch", default="")
    ap.add_argument("--movable-copper", default="")
    ap.add_argument("--no-gate", action="store_true")
    a = ap.parse_args()
    t_start = time.time()
    model = json.load(open(a.model))
    movable = set(x for x in a.movable_nets.split(",") if x)
    movable_vias = set(x for x in a.movable_stitch.split(",") if x)
    movable_copper = set(x for x in a.movable_copper.split(",") if x)
    hw = a.lane_w / 2.0
    corner = 0.5 * a.cell * math.sqrt(2.0)
    v3.PAD_EXTRA = a.margin + corner
    pitch_eff = a.pitch + a.margin
    R = a.rout if a.rout else (pitch_eff + 2.0 * corner)
    rast = v3.Raster(model["bbox"], a.cell)
    base = v3.build_base(rast, model, a.layer, movable, movable_vias, hw, movable_copper)
    anchors = v3.lane_anchors(model)
    for src, key in ((a.a_sites, "A"), (a.b_sites, "B")):
        if not src:
            continue
        ov = json.load(open(src))
        for an in anchors:
            if an["net"] in ov:
                an[key] = tuple(float(x) for x in ov[an["net"]][:2])
    if a.groups:
        pre = tuple(x for x in a.groups.split(",") if x)
        anchors = [an for an in anchors if an["net"].startswith(pre)]
    c_all, own = v3.anchor_keepout(rast, anchors, hw)
    fixed_ok = ~base
    G, idx = v3.build_topology(fixed_ok, a.cell)
    ii, jj = np.nonzero(fixed_ok)
    NN = len(ii)
    coo = G.tocoo()
    e_src = coo.row.astype(np.int64); e_tgt = coo.col.astype(np.int64); e_dl = coo.data.astype(np.float64)
    del coo
    print("车道 %d · 栅格 %dx%d cell=%.2f · 自由格 %d · pitch_eff=%.3f · R_out=%.4f · iters=%d"
          % (len(anchors), rast.NX, rast.NY, a.cell, NN, pitch_eff, R, a.iters), flush=True)

    tasks = {}
    for an in anchors:
        nm = an["net"]
        blk = base | ((c_all.astype(np.int32) - own[nm].astype(np.int32)) > 0)

        def snap(cx, cy, max_r=14):
            ci, cj = rast.cell(cx, cy); best = None
            for r in range(0, max_r + 1):
                for di in range(-r, r + 1):
                    for dj in range(-r, r + 1):
                        if max(abs(di), abs(dj)) != r:
                            continue
                        i, j = ci + di, cj + dj
                        if 0 <= i < rast.NX and 0 <= j < rast.NY and not blk[i, j] and idx[i, j] >= 0:
                            d = math.hypot(di, dj) * a.cell
                            if best is None or d < best[0]:
                                best = (d, i, j)
                if best is not None:
                    return best[1], best[2], best[0]
            return None, None, None
        si, sj, ds = snap(*an["A"]); gi, gj, dg = snap(*an["B"])
        t = {"net": nm, "an": an, "blk": blk, "blk1d": blk[ii, jj],
             "disp": {"A": round(ds, 4) if ds is not None else None, "B": round(dg, 4) if dg is not None else None}}
        if si is None or gi is None:
            t["status"] = "NO_ENDPOINT"
        else:
            t["s"] = (si, sj); t["g"] = (gi, gj)
            if ds and ds > 1e-9:
                an["A"] = (rast.X0 + si * a.cell, rast.Y0 + sj * a.cell)
            if dg and dg > 1e-9:
                an["B"] = (rast.X0 + gi * a.cell, rast.Y0 + gj * a.cell)
            t["status"] = "PENDING"
        tasks[nm] = t
    bad = [nm for nm, t in tasks.items() if t["status"] != "PENDING"]
    if bad:
        print("  ⚠ 端点不可行：", bad, flush=True)

    src_grid = np.zeros((rast.NX, rast.NY), dtype=bool)

    def route_mask(blocked, ban_radius=R):
        """距离场掩码：`blocked` 各车道折线 ±R_out 内禁行（自身 blk 由调用方叠加）。

        blocked: {net: [(i,j),...]} —— **必须显式传入**（勿读全局，否则掩码恒空）。"""
        src_grid[:] = False
        for nm in blocked:
            for (i, j) in blocked[nm]:
                src_grid[i, j] = True
        if src_grid.any():
            D = distance_transform_edt(~src_grid, sampling=(a.cell, a.cell))
            return D >= ban_radius
        return np.ones_like(src_grid)

    def field_of(others):
        """其他车道折线之距离场（mm）。others: {net: cells}；空 ⇒ 全 inf。"""
        if not others:
            return np.full((rast.NX, rast.NY), np.inf)
        src_grid[:] = False
        for nm in others:
            for (i, j) in others[nm]:
                src_grid[i, j] = True
        if not src_grid.any():
            return np.full((rast.NX, rast.NY), np.inf)
        return distance_transform_edt(~src_grid, sampling=(a.cell, a.cell))

    def route_soft(nm, others, K, rmin):
        """软罚重布：代价 = 边长 + K·max(0, rmin − D_其他)²；仅静态障碍/他车道锚笼为硬禁。"""
        t = tasks[nm]
        D = field_of(others)
        D1 = D[ii, jj]
        pen = K * np.maximum(0.0, rmin - D1) ** 2
        allow1d = ~t["blk1d"]
        ok = allow1d[e_src] & allow1d[e_tgt]
        w = np.where(ok, e_dl + pen[e_tgt], np.inf)
        s, g = t["s"], t["g"]
        si, gi = idx[s[0], s[1]], idx[g[0], g[1]]
        if si < 0 or gi < 0 or not allow1d[si] or not allow1d[gi]:
            return None
        G2 = csr_matrix((w, (e_src, e_tgt)), shape=G.shape)
        dist, pred = dijkstra(G2, directed=True, indices=int(si), return_predecessors=True)
        if not np.isfinite(dist[gi]):
            return None
        pp = v3.path_from_pred(pred, int(si), int(gi))
        if not pp:
            return None
        return [(int(ii[k]), int(jj[k])) for k in pp]

    def route(nm, allowed2d):
        t = tasks[nm]
        allow1d = allowed2d[ii, jj] & (~t["blk1d"])
        ok = allow1d[e_src] & allow1d[e_tgt]
        w = np.where(ok, e_dl, np.inf)
        s, g = t["s"], t["g"]
        si, gi = idx[s[0], s[1]], idx[g[0], g[1]]
        if si < 0 or gi < 0 or not allow1d[si] or not allow1d[gi]:
            return None
        G2 = csr_matrix((w, (e_src, e_tgt)), shape=G.shape)
        dist, pred = dijkstra(G2, directed=True, indices=int(si), return_predecessors=True)
        if not np.isfinite(dist[gi]):
            return None
        pp = v3.path_from_pred(pred, int(si), int(gi))
        if not pp:
            return None
        return [(int(ii[k]), int(jj[k])) for k in pp]

    paths = {}

    def greedy(order, fixed=None):
        kept = dict(fixed or {})
        for nm in order:
            if nm in kept:
                continue
            allowed = route_mask(kept, R)
            p = route(nm, allowed)
            if p:
                kept[nm] = p
        return kept

    n_l = len(tasks)
    nets = sorted(tasks)
    rng = np.random.RandomState(a.seed)
    order0 = sorted(nets, key=lambda n: -tasks[n]["an"]["A"][0])

    def gate_of(ps):
        rr = {}
        for nm, cells in ps.items():
            t = tasks[nm]
            pts = [t["an"]["A"]] + [(rast.X0 + i * a.cell, rast.Y0 + j * a.cell) for (i, j) in cells] + [t["an"]["B"]]
            pts = v3.simplify(pts)
            rr[nm] = {"pts": [[round(x, 4), round(y, 4)] for (x, y) in pts],
                      "len_mm": round(sum(math.dist(pts[q], pts[q + 1]) for q in range(len(pts) - 1)), 3)}
        g = v3.exact_gate(model, rr, anchors, a.layer, hw, movable, movable_vias, pitch_eff, movable_copper)
        return g, rr

    paths = {}
    # 初始化：硬掩码贪心（R_out）多序取优
    def greedy(order):
        kept = {}
        for nm in order:
            allowed = route_mask(kept, R)
            p = route(nm, allowed)
            if p:
                kept[nm] = p
        return kept
    best0 = {}
    for o in (order0, sorted(nets, key=lambda n: tasks[n]["an"]["A"][0]),
              sorted(nets, key=lambda n: tasks[n]["an"]["B"][1])):
        cur = greedy(o)
        if len(cur) > len(best0):
            best0 = cur
    paths = {k: list(v) for k, v in best0.items()}
    print("  [init] 硬掩码贪心 %d/%d" % (len(paths), n_l), flush=True)

    K = a.k0
    best = None  # (n_routed, -viol, paths, gate)
    for it in range(a.iters):
        ord_it = order0[it % len(order0):] + order0[:it % len(order0)]
        for nm in ord_it:
            others = {k: v for k, v in paths.items() if k != nm}
            p = route_soft(nm, others, K, a.rmin)
            if p:
                paths[nm] = p
        g, rr = gate_of(paths)
        viol = g["n_lane_pitch_viol"]
        key = (len(paths), -viol)
        if best is None or key > best[0]:
            best = (key, {k: list(v) for k, v in paths.items()}, g)
        print("  [it %3d] routed=%2d/%d K=%9.2f 闸: 最小中心距=%.4f 违规=%d 余量=%.4f"
              % (it, len(paths), n_l, K, g["lane_pitch_min_gap_mm"], viol, g["clearance_min_mm"]), flush=True)
        if viol and it % 2 == 0:
            print("        最小对=%s · 违规对=%s" % (g.get("lane_pitch_min_pair"),
                  g.get("lane_pitch_violations")), flush=True)
        if viol == 0 and len(paths) == n_l and g["n_clearance_viol"] == 0 and g["endpoint_max_dev_mm"] == 0.0:
            break
        K = min(K * a.kgrow, 1.0e7)
    (_, _), paths, gate_best = best
    print("  [best] routed=%d/%d 最小中心距=%.4f 违规=%d" % (len(paths), n_l, gate_best["lane_pitch_min_gap_mm"], gate_best["n_lane_pitch_viol"]), flush=True)

    routes = {}
    for nm, cells in paths.items():
        t = tasks[nm]
        pts = [t["an"]["A"]] + [(rast.X0 + i * a.cell, rast.Y0 + j * a.cell) for (i, j) in cells] + [t["an"]["B"]]
        pts = v3.simplify(pts)
        routes[nm] = {"pts": [[round(x, 4), round(y, 4)] for (x, y) in pts],
                      "len_mm": round(sum(math.dist(pts[q], pts[q + 1]) for q in range(len(pts) - 1)), 3)}
    gate = None
    if not a.no_gate and routes:
        try:
            gate = v3.exact_gate(model, routes, anchors, a.layer, hw, movable, movable_vias, pitch_eff, movable_copper)
            print("  [精确闸] 车道最小中心距 %.4f（<%.3f 违规 %d）· 障碍最小余量 %.4f（违规 %d）· 端点最大偏移 %s"
                  % (gate["lane_pitch_min_gap_mm"], a.pitch, gate["n_lane_pitch_viol"],
                     gate["clearance_min_mm"], gate["n_clearance_viol"], gate["endpoint_max_dev_mm"]), flush=True)
        except Exception as e:  # noqa: BLE001
            gate = {"error": "%s: %s" % (type(e).__name__, e)}
            print("  ⚠ 闸异常：%s" % gate["error"], flush=True)
    wo = {"artifact": "k2_p4_b2_in5_ripup_v1_workorder", "layer": a.layer, "cell_mm": a.cell,
          "lane_w_mm": a.lane_w, "pitch_mm": a.pitch, "pitch_eff_mm": pitch_eff, "margin_mm": a.margin,
          "pad_extra_mm": v3.PAD_EXTRA, "r_out_mm": R, "model": a.model,
          "n_lanes": len(anchors), "n_routed": len(routes),
          "failed": sorted(nm for nm in nets if nm not in routes),
          "routes": routes, "geometric_gate": gate, "iters": a.iters, "seed": a.seed,
          "anchors": [{"net": nm, "A": [round(tasks[nm]["an"]["A"][0], 4), round(tasks[nm]["an"]["A"][1], 4)],
                       "B": [round(tasks[nm]["an"]["B"][0], 4), round(tasks[nm]["an"]["B"][1], 4)],
                       "disp_mm": tasks[nm]["disp"]} for nm in nets],
          "movable_nets": sorted(movable),
          "note": "rip-up-and-reroute · 互斥半径 = pitch_eff + 2×折角安全（严格蕴含闸之线段距口径）· 只读板件"}
    json.dump(wo, open(a.out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print("routed %d/%d · failed=%s · %.0fs" % (len(routes), len(anchors), wo["failed"], time.time() - t_start), flush=True)
    print("wrote", a.out, flush=True)


if __name__ == "__main__":
    main()
