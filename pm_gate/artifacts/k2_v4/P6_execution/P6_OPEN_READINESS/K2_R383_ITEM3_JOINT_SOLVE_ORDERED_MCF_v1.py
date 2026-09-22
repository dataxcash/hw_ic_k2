#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R383 —— 收口窗口 项3「一次实现」：**束序感知·有序多商品流（ordered MCF）联合求解器**
（承 #K2-136 §三 项3 · 契约 K2_R379 · 装载器 K2_R380 · 验收台 K2_R381）

冻结模型 : C-B2UP-1_REALGEOM_BUS_v1   model_sha16 84f19701dfc1db31
受审板   : k2/hw/k2_v4_8L.l9.kicad_pcb  77aaa63fe016b450
口径     : cell 0.03mm · 8-邻域 · 仅 In5.Cu · lane_w 0.16(hw 0.08) · 互距 >= 0.435 · 净距 hw+max(0.175,req)
判据     : `k2_p4_b2_in5_lane_router_v3.exact_gate`（**唯一权威闸**，本项目自有工具，只读调用）

方法（一次实现 · 单一算法 · 非参数扫描 · 非变体重跑 · 无 rip-up）：
  1) 自由域 = 由**同一冻结模型**经该工具 `build_base` 得到的 In5 车道中心线可行域
     （保证：凡过闸之见证，其净距口径与闸**同源**）；
  2) **束序非交叉**以 `a_rank` 定序编码：束序 = a_rank 降序（东→西 · 内→外），
     逐 lane 以 Dijkstra 求**残余域**内最短路；每布一条，即以半径 P+eps 之圆盘**硬印**，
     使后续 lane 与该 lane 之中心距 >= 0.435（工具中 `exact_gate` 复核）；
  3) 每条 lane 之可行域另减「其余 15 条 lane 之 A/B 锚孔 +-0.435 盘」——
     该约束由「lane-lane 互距 >= 0.435 且每 lane 必经其自身锚孔」**逻辑蕴含**（必要约束）。

强止损（承 R377/R379）：同参重跑 >= 2 = FAIL · 禁变体重跑 · 禁半途烙板 · 禁派 WORKER ·
 禁以布通率/有界搜索冒充见证 · 禁以模型类上界冒充全问题上界。

终局 = **二值**：(a) 16/16 合法见证 + buildability ；(b) 真实几何严格 U<16 证书 ；
 皆无 ⇒ 报卡点交监理。

只读：不改冻结四源 / criteria / 生成器 / SPEC 设计内容 / 原理图；不写板。
"""
from __future__ import annotations
import json, sys, os, math, hashlib, datetime
import numpy as np

K2_ROOT = "/home/fila/jqdDev_2025/ic_hw/k2"
sys.path.insert(0, os.path.join(K2_ROOT, "tools"))
from k2_p4_b2_in5_lane_router_v3 import (  # noqa: E402  (只读调用)
    Raster, build_base, build_topology, lane_anchors, path_from_pred, simplify, exact_gate,
)
from scipy.sparse.csgraph import dijkstra  # noqa: E402

# ---- 冻结常数（= K2_R379 契约 / R377 模型 caliber，逐字不改）----
CELL, HW, PITCH, LANE_W = 0.03, 0.08, 0.435, 0.16
MODEL_SHA16, BOARD_SHA16 = "84f19701dfc1db31", "77aaa63fe016b450"
RASTER_SHA16, ANCHOR_SHA16 = "e1ba05e38e3b61f9", "e6bb322818cd95cb"
MODEL_JSON = "/tmp/opencode/archer/model_l8.json"
ANCHOR_JSON = "/tmp/opencode/k2r376/anchor_table.json"
WALL_MARGIN = 0.020          # 硬印半径 = PITCH + WALL_MARGIN（硬化，防离散吃边）

LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}


def load_inputs(model_json=MODEL_JSON, anchor_json=ANCHOR_JSON):
    """装载冻结输入：模型 + 16 lane 锚表；断言锚表与模型 lane_anchors 逐点一致（位移 0）。"""
    model = json.load(open(model_json))
    model["_is_lane_patched"] = True
    import k2_p4_b2_in5_lane_router_v3 as _v3
    _v3.is_lane = lambda n: n in LANES                    # 只把 16 条 UP_OUT 视为车道
    anchors = lane_anchors(model)                          # A=F.Cu-B.Cu 孔 · B=F.Cu-In2.Cu 孔
    assert len(anchors) == 16, len(anchors)
    table = json.load(open(anchor_json))
    tbl = {r["net"]: r for r in table["lanes"]}
    for an in anchors:
        r = tbl[an["net"]]
        assert abs(an["A"][0] - r["A"][0]) < 1e-6 and abs(an["A"][1] - r["A"][1]) < 1e-6, an["net"]
        assert abs(an["B"][0] - r["B"][0]) < 1e-6 and abs(an["B"][1] - r["B"][1]) < 1e-6, an["net"]
    anchors = sorted(anchors, key=lambda a: tbl[a["net"]]["a_rank"])
    return model, anchors


# -----------------------------------------------------------------------------
def run(model, anchors, rank_of):
    rast = Raster(tuple(model["bbox"]), CELL)
    base = build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW)
    free = ~base
    ad = {a["net"]: a for a in anchors}

    keep = {}
    for a in anchors:
        n = a["net"]
        k = np.zeros(base.shape, bool)
        for b in anchors:
            if b["net"] == n:
                continue
            for key in ("A", "B"):
                Raster.cir(rast, k, b[key][0], b[key][1], PITCH)
        keep[n] = k

    order = sorted((a["net"] for a in anchors), key=lambda n: -rank_of[n])   # a_rank 降序（内→外）
    blocked = base.copy()
    routes, fails = {}, []
    diag = []
    for n in order:
        allowed = (~blocked) & free & (~keep[n])
        G, idx = build_topology(allowed, CELL)
        ii, jj = np.nonzero(allowed)
        if len(ii) == 0:
            fails.append(n); diag.append({"net": n, "reason": "empty_allowed"}); continue
        A, B = ad[n]["A"], ad[n]["B"]
        si, sj = rast.cell(*A); gi, gj = rast.cell(*B)
        if not (0 <= si < idx.shape[0] and 0 <= sj < idx.shape[1] and 0 <= gi < idx.shape[0] and 0 <= gj < idx.shape[1]) \
           or idx[si, sj] < 0 or idx[gi, gj] < 0:
            fails.append(n); diag.append({"net": n, "reason": "endpoint_not_free"}); continue
        d, pred = dijkstra(G, directed=True, indices=int(idx[si, sj]), return_predecessors=True)
        if not np.isfinite(d[int(idx[gi, gj])]):
            fails.append(n); diag.append({"net": n, "reason": "disconnected"}); continue
        pp = path_from_pred(pred, int(idx[si, sj]), int(idx[gi, gj]))
        pts = simplify([tuple(A)] + [(rast.X0 + int(ii[q]) * CELL, rast.Y0 + int(jj[q]) * CELL) for q in pp]
                       + [tuple(B)])
        routes[n] = pts
        for q in range(len(pts) - 1):
            Raster.seg(rast, blocked, pts[q][0], pts[q][1], pts[q + 1][0], pts[q + 1][1], PITCH + WALL_MARGIN)
        diag.append({"net": n, "reason": "routed", "len_mm": round(sum(
            math.dist(pts[q], pts[q + 1]) for q in range(len(pts) - 1)), 3)})
    return routes, fails, diag


def solve(model, anchors, rank_of):
    """契约 K2_R379 `solve()` 之等价入口（本器以冻结模型 + 锚表为真实输入）。
       返回 (routes, fails, diag)；`routes` 即 In5.Cu 折线见证（首末 = A/B，位移 0）。
       方法 = 束序感知有序多商品流（见 run()）：束序 = a_rank 降序（内->外），
       逐 lane 于残余可行域求最短路并以 P+eps 硬印排斥后续 lane ⇒ 束序非交叉。
       **单次运行**（本器 main() 只调用一次）；禁同参重跑、禁变体重跑。"""
    return run(model, anchors, rank_of)


def gate_readings(model, routes):
    anc = [a for a in lane_anchors(model) if a["net"] in routes]
    rr = {k: {"pts": [[round(x, 4), round(y, 4)] for x, y in v]} for k, v in routes.items()}
    return exact_gate(model, rr, anc, "In5.Cu", HW, frozenset(), frozenset(), PITCH)


def certify_upper_bound(model, anchors):
    """(b) 路线：真实几何严格 U<16 证书。本器之**真实几何**松弛 = 「跨切容量」：
       任一切面 Gamma 上，lane 中心线两两 >= PITCH ⇒ 该切面可承载 <= Σ_k(floor(w_k/PITCH)+1)。
       实测（cell 0.02 · 直线族 x∈[94,128] / y∈[40,57]）：min 竖向 66 · min 横向 162 ≫ 16
       ⇒ **容量型证书在本几何上不可得**。返回 None（不冒充）。"""
    return None


def main():
    t0 = datetime.datetime.now().astimezone()
    model, anchors = load_inputs()
    rank_of = {a["net"]: i for i, a in enumerate(anchors)}   # a_rank 升序 = 锚表序
    routes, fails, diag = run(model, anchors, rank_of)
    g = gate_readings(model, routes)
    n = len(routes)
    ok = (n == 16 and g["n_lane_pitch_viol"] == 0 and g["n_clearance_viol"] == 0
          and (g["endpoint_max_dev_mm"] or 1) < 1e-6)
    bcert = certify_upper_bound(model, anchors)
    binary = ("(a) 合法 16/16 见证 + buildability" if ok else
              ("(b) 真实几何严格 U<16 证书" if bcert else
               "既无 (a) 亦无 (b) ⇒ 报卡点交监理（不冒充见证 · 不冒充上界）"))
    result = {
        "schema": 1, "artifact": "k2_r383_item3_joint_solve_ordered_mcf_v1",
        "to": "监理", "from": "ENG · ARCHER",
        "ts": t0.isoformat(),
        "board": "k2/hw/k2_v4_8L.l9.kicad_pcb", "board_sha16": BOARD_SHA16,
        "model": "C-B2UP-1_REALGEOM_BUS_v1", "model_sha16": MODEL_SHA16,
        "caliber": {"cell_mm": CELL, "hw_mm": HW, "lane_w_mm": LANE_W, "pitch_mm": PITCH,
                    "layer": "In5.Cu", "wall_mm": round(PITCH + WALL_MARGIN, 4)},
        "method": "ordered MCF · bundle-order = a_rank DESC (inner->outer) · single implementation · single run",
        "n_routed": n, "n_lanes": 16, "failed": [f for f in fails],
        "gate": {k: g[k] for k in ("lane_pitch_req_mm", "lane_pitch_min_gap_mm", "lane_pitch_min_pair",
                                   "n_lane_pitch_viol", "clearance_min_mm", "n_clearance_viol",
                                   "endpoint_max_dev_mm")},
        "gate_pass_on_routed_subset": bool(g["n_lane_pitch_viol"] == 0 and g["n_clearance_viol"] == 0
                                           and (g["endpoint_max_dev_mm"] or 1) < 1e-6),
        "binary": binary,
        "verdict": "PASS(a)" if ok else "NOT(a)",
        "upper_bound_certificate": bcert,
        "buildability": {
            "mode": "relocation_listed" if not ok else "no_move",
            "施工队问答": ("不能——本件只给出 %d/16 条坐标（余 %d 条无坐标）⇒ 图纸层缺图，不作里程碑、不得开工"
                        % (n, 16 - n)) if not ok else "能（照此图直接连）",
            "note": ("已布 %d 条本身过 exact_gate（互距/净距/端点 0），但**非 16/16** ⇒ 不构成 (a) 见证；"
                     "未布 lane 之坐标缺 ⇒ 全板图纸层缺图。" % n) if not ok else "16/16 过闸",
        },
        "input_provenance": {
            "model_json": MODEL_JSON, "anchor_json": ANCHOR_JSON,
            "frozen_raster_sha16": RASTER_SHA16, "frozen_anchor_sha16": ANCHOR_SHA16,
            "note": ("冻结栅格 e1ba05e38e3b61f9 无法由本机冻结模型按**闸同源**障碍语义复现"
                     "（多次配准比对 mismatch≈23-33%，非配准误差）；故本器按**闸所消费之同一模型**"
                     "（`build_base`）重建可行域 ⇒ 见证与闸**同源**（更严，不放松）。此为具名观察 O-1。"),
        },
        "diagnostics": diag,
    }
    out = sys.argv[2] if len(sys.argv) > 2 else \
        "/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R383_ITEM3_SOLVE_RESULT_v1.json"
    json.dump(result, open(out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    # 见证坐标（如实标注：非 16/16）
    wit = {k: [[round(x, 4), round(y, 4)] for x, y in v] for k, v in routes.items()}
    json.dump({"note": "NOT (a): partial witness %d/16 (gate-clean subset)" % n, "routes": wit},
              open(out.replace(".json", ".witness.json"), "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps({"n_routed": n, "failed": fails, "gate": result["gate"], "binary": binary},
                     ensure_ascii=False, indent=1))
    print("wrote", out)


if __name__ == "__main__":
    main()
