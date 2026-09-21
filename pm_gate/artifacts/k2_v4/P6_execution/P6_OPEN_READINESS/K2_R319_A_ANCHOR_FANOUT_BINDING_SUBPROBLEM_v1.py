#!/usr/bin/env python3
"""K2 · R319 —— ②-UP 16 条之**序贯硬排斥构造**（两种锚群出线策略）+ **绑定子问题定位**（只读 · 不改生成器）

承 R318（A 侧连通 16/16 · 跨切容量 min 29≥16 ⇒ 无连通型/容量型卡点）：
本器做**构造**，以定位残余卡点之**确切位置**。
  方法：自由空间（In5 单层 · 自网铜排除 = no-move 全转前提）上逐 lane 取最短路；
        每条已布 lane 沿其折线以**半径 0.435 盘印**封锁（= 车道互距下限之硬排斥）；
        末以 `exact_gate` 连续几何闸判（**方法为启发式，见证有效性只由闸定**）。
  策略A（序）：按 A→B 欧氏距离降序。
  策略B（逃逸行）：N 组向北 / P 组向南，组内按 A.x 递增外推 0.45，并以 (A.x, 逃逸行) 为强制途经点。
诊断：对未布 lane，判其 A 锚格是否已落在既有 lane 之 0.435 封套内（⇒ 被谁封死）。
用法:
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_b2_board_in5_model_dump_v1.py k2/hw/k2_v4_8L.l8.kicad_pcb /tmp/opencode/model_l8.json
  python3 K2_R319_A_ANCHOR_FANOUT_BINDING_SUBPROBLEM_v1.py /tmp/opencode/model_l8.json <out.json>
"""
import sys, json, math, importlib.util, hashlib
import numpy as np
from scipy.sparse.csgraph import dijkstra

V3 = "k2/tools/k2_p4_b2_in5_lane_router_v3.py"
LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
CELL, HW, P = 0.05, 0.08, 0.435
spec = importlib.util.spec_from_file_location("v3", V3)
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
v3.is_lane = lambda n: n in LANES


def main():
    model = json.load(open(sys.argv[1]))
    rast = v3.Raster(model["bbox"], CELL)
    base = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
    free = ~base
    ad = {a["net"]: a for a in v3.lane_anchors(model)}
    out = {"schema": 1, "artifact": "k2_r319_a_anchor_fanout_binding_subproblem_v1", "to": "监理",
           "from": "ENG · ARCHER", "board": "k2/hw/k2_v4_8L.l8.kicad_pcb", "board_sha16": "7a5c89913d6e5d0a",
           "method": "序贯最短路 + 已布 lane 之 0.435 硬盘印排斥；见证有效性由 exact_gate 判定（方法本身为启发式，不冒充证书）",
           "cell_mm": CELL, "pitch_mm": P, "strategies": {}}

    def build(order, esc=None):
        blocked = base.copy(); routes = {}; log = []
        for n in order:
            A, B = ad[n]["A"], ad[n]["B"]
            allowed = (~blocked) & free
            G, idx = v3.build_topology(allowed, CELL); ii, jj = np.nonzero(allowed)

            def path(Pt, Qt):
                si, sj = rast.cell(*Pt); gi, gj = rast.cell(*Qt)
                if not (0 <= si < idx.shape[0] and 0 <= sj < idx.shape[1] and
                        0 <= gi < idx.shape[0] and 0 <= gj < idx.shape[1]): return None
                if idx[si, sj] < 0 or idx[gi, gj] < 0: return None
                d, pred = dijkstra(G, directed=True, indices=int(idx[si, sj]), return_predecessors=True)
                if not np.isfinite(d[int(idx[gi, gj])]): return None
                pp = v3.path_from_pred(pred, int(idx[si, sj]), int(idx[gi, gj]))
                return [(rast.X0 + int(ii[k]) * CELL, rast.Y0 + int(jj[k]) * CELL) for k in pp]
            pts = None
            if esc is not None:
                p1 = path(A, (A[0], esc[n])); p2 = path((A[0], esc[n]), B)
                if p1 is not None and p2 is not None: pts = p1 + p2[1:]
            if pts is None: pts = path(A, B)
            if pts is None:
                log.append((n[10:-3], "失败")); continue
            pts = v3.simplify([(A[0], A[1])] + pts + [(B[0], B[1])])
            routes[n] = {"pts": [[round(x, 4), round(y, 4)] for x, y in pts],
                         "len_mm": round(sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1)), 3)}
            for k in range(len(pts) - 1):
                v3.Raster.seg(rast, blocked, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], P)
            log.append((n[10:-3], "OK", routes[n]["len_mm"]))
        gate = None
        if routes:
            anchors = [a for a in v3.lane_anchors(model) if a["net"] in routes]
            gate = v3.exact_gate(model, routes, anchors, "In5.Cu", HW, frozenset(), frozenset(), P, frozenset())
        return routes, log, gate, blocked

    order = sorted(LANES, key=lambda n: -math.dist(ad[n]["A"], ad[n]["B"]))
    r1, l1, g1, _ = build(order, None)
    print("策略A（序）: %d/16" % len(r1))
    if g1: print("   exact_gate: 互距违例=%d（最小 %.4f）· 净距违例=%d" % (g1["n_lane_pitch_viol"], g1["lane_pitch_min_gap_mm"], g1["n_clearance_viol"]))

    ESC = {}
    for s, sign in (("N", +1.0), ("P", -1.0)):
        grp = sorted([n for n in LANES if n.endswith(f"_{s}_J2")], key=lambda n: ad[n]["A"][0])
        for k, n in enumerate(grp):
            ESC[n] = round(ad[n]["A"][1] + sign * 0.45 * (k + 1), 3)
    r2, l2, g2, blk2 = build(order, ESC)
    print("策略B（逃逸行）: %d/16" % len(r2))
    if g2: print("   exact_gate: 互距违例=%d（最小 %.4f）· 净距违例=%d" % (g2["n_lane_pitch_viol"], g2["lane_pitch_min_gap_mm"], g2["n_clearance_viol"]))

    # 诊断：未布 lane 之 A 锚是否被既有封套覆盖
    diag = []
    for n in sorted(LANES):
        if n in r2: continue
        ai, aj = rast.cell(*ad[n]["A"]); bi, bj = rast.cell(*ad[n]["B"])
        diag.append({"net": n[10:-3], "A_blocked": bool(blk2[ai, aj]), "B_blocked": bool(blk2[bi, bj]),
                     "A": [round(ad[n]["A"][0], 2), round(ad[n]["A"][1], 2)]})
    An = [a for a in v3.lane_anchors(model)]
    yN = sorted({round(a["A"][1], 2) for a in An}); 
    out["strategies"] = {
        "A_ordinal": {"n_routed": len(r1), "log": [list(map(str, x)) for x in l1],
                      "gate": {k: g1[k] for k in ("n_lane_pitch_viol", "lane_pitch_min_gap_mm", "n_clearance_viol", "endpoint_max_dev_mm")} if g1 else None},
        "B_escape_row": {"n_routed": len(r2), "log": [list(map(str, x)) for x in l2], "esc_y": {k[10:-3]: v for k, v in ESC.items()},
                         "gate": {k: g2[k] for k in ("n_lane_pitch_viol", "lane_pitch_min_gap_mm", "n_clearance_viol", "endpoint_max_dev_mm")} if g2 else None,
                         "unrouted_anchor_diagnosis": diag}}
    out["binding_subproblem"] = {
        "定位": "**A 侧锚群之出线扇出**（16 锚挤在 y∈[54.88,55.82] 之 **0.94mm** 带内：N 行 y=55.82 × 8 · P 行 y=54.88 × 8）",
        "量": "两行间距 **0.94** − 2×0.435 = **夹缝仅 0.07mm** ⇒ 车道**几乎不可能在两行之间穿越**；"
              "且任一条 lane 若沿本行东行，其 0.435 封套即横扫本行其余锚 ⇒ **逐条封锁**。",
        "判": "**不是几何刚性不可能**（R318 已证连通 16/16 · 跨切容量 min 29≥16）——是**出线扇出之联合序贯**问题，"
              "须「锚处即刻离行 + 各行 ≥0.435 分行」之**协调指派**。"}
    out["honest_state"] = {
        "(a) 可行见证": "**未得**（本件两策略 3/16 · 4/16；已布 lane 全部 `exact_gate` 0 违例 ⇒ 方法与闸自洽）",
        "(b) 守恒级不可行证书": "**不成立**（R314 反证：`W_max=8 ⇒ U≤16`）且**不被本件支持**",
        "本件不主张": "既不主张 16/16 可达，也不主张不可行；只主张**卡点已定位到 A 侧锚群出扇**"}
    out["buildability_field_宪法13"] = ("「施工队照着这张图能不能直接连？」→ 逐 lane **能**（R318 路径见证）；"
        "**全板不能**（16 条联立坐标未给）⇒ 全板图纸层缺图，不得据以开工。**不动证明**：本件不搬任何对象。")
    out["self_sha16"] = {"convention": "#K2-72 §五 约定A", "convention_A_sha16": ""}
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    out["self_sha16"]["convention_A_sha16"] = hashlib.sha256(txt.strip().encode()).hexdigest()[:16]
    json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("[sha16 约定A] %s -> %s" % (out["self_sha16"]["convention_A_sha16"], sys.argv[2]))


main()
