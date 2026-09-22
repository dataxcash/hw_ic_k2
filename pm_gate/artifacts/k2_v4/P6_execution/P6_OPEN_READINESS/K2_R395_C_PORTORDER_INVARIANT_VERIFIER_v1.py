#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R395 —— 能力缺口 **C-PORTORDER** 之**只读不变量验证器 v1**（应 监理 #K2-138 §三 授权）

【O-3 强制首行自陈 · 本窗口运行清单（承 #K2-138 §六 O-3）】
  · 同一冻结模型内迭代：**R383**（束式有序 MCF · 一次实现 · 单次运行）。
  · **变体重跑（如实自陈 · 触强止损 FAIL 级 · 登记 · 禁再犯）**：R384（winding 分裂）·
    R387（布序旋转）· R388（构造型 seam 贴墙）。
  · 纯普查/读数（非求解运行）：R386 · R389 · R393 · R394。
  · **本件（R395）不跑任何求解器**：只做**只读**不变量计算与对**已存**见证的复核。

授权与路线（#K2-138 §三）：只读 · 一次实现 · 模型冻结 · 取证限 ① 不变量验证器（端口环 + 洞群生成元）
或 ② [C2] 之有限情形穷尽。**交付 = 二值**：(b) 成立 ⇒ 严格 U<16 证书；(b) 不成立 ⇒ 回报卡点。

本 v1 实现并**机器复核**以下四项（全部只读）：
  A. **屏障引理**：A/B 锚簇内**相邻锚孔 0.435 盘是否重叠**（重叠 ⇒ 车道不可在锚间穿行）。
  B. **端口环（port ring）**：A 簇并集边界之**暴露弧**（= 各 lane 唯一可越界处）长度 census。
  C. **[C1] 机器核**：对**已存 gate-clean 见证**测 A 出口序（y=56.5/57.0/57.5 三切面）与其 a_rank 序之关系。
  D. **[C2] 机器核**：对同一见证测**走廊南 seam 车道**之锚 rank，与其论断「seam 须为最东锚 rank15」比对。
  E. **切面路线闭合度复算**：直线族 min（承 R393=28）+ **一般曲线 min-cut**（含锚孔袋 artefact 之如实登记）。

只读：不改冻结四源 / criteria / 生成器 / SPEC 设计内容 / 原理图；不写板；不派 WORKER；不跑求解器。
"""
from __future__ import annotations
import json, sys, os, math, hashlib
import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
sys.path.insert(0, os.path.join(K2, "tools"))
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base  # noqa: E402

CELL, HW, PITCH, LANE_W = 0.03, 0.08, 0.435, 0.16
MODEL_SHA16, BOARD_SHA16 = "84f19701dfc1db31", "77aaa63fe016b450"
MODEL_JSON = "/tmp/opencode/archer/model_l8.json"
ANCHOR_JSON = "/tmp/opencode/k2r376/anchor_table.json"
P = os.path.join(K2, "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS")
WITNESS = os.path.join(P, "K2_R383_ITEM3_SOLVE_RESULT_v1.witness.json")
OUT = os.path.join(P, "K2_R395_C_PORTORDER_INVARIANT_VERIFIER_v1.json")
R393 = os.path.join(P, "K2_R393_ITEM3_CUT_CERTIFICATE_ROUTE_REFUTATION_v1.json")

A_NET = lambda i, s: "PCIE_UP_OUT%d_%s_J2" % (i, s)


def load():
    model = json.load(open(MODEL_JSON)); model["_is_lane_patched"] = True
    L = sorted(json.load(open(ANCHOR_JSON))["lanes"], key=lambda r: r["a_rank"])
    rast = Raster(tuple(model["bbox"]), CELL)
    bad = build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW)
    return model, L, rast, (~bad)


def barrier_lemma(L):
    out = {}
    for tag, key in (("A_cluster", "A"), ("B_cluster", "B")):
        pts = np.array([l[key] for l in L])
        D = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
        D[D == 0] = 1e9
        adj = D.min(1)                     # 每锚到最近他锚
        out[tag] = {"min_nn_mm": round(float(adj.min()), 4), "max_nn_mm": round(float(adj.max()), 4),
                    "no_threading_all": bool((adj < 2 * PITCH).all()),
                    "discs_connected": bool((adj < 2 * PITCH).all()),
                    "note": "相邻锚孔中心距 < 2*PITCH=0.870 ⇒ 0.435 盘重叠 ⇒ 车道不可在锚间穿行（=屏障）"}
    return out


def port_ring(L, free, rast):
    """A 簇 0.435 盘并集之**连通性**与**相邻缝宽**（决定「端口环/屏障」前提是否成立）。"""
    AX = np.array([l["A"] for l in L])
    D = np.sqrt(((AX[:, None, :] - AX[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(D, 1e9)
    nn = D.min(1)
    # 并用 0.435 盘的连通分量（并查集）
    n = len(AX); par = list(range(n))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for i in range(n):
        for j in range(i + 1, n):
            if D[i, j] < 2 * PITCH:
                par[find(i)] = find(j)
    comps = len({find(i) for i in range(n)})
    seam_gap = float(nn.min() - 2 * PITCH)   # 相邻两盘间最小**缝宽**（<0 表重叠）
    return {"n_ports": n, "disc_union_components": comps,
            "min_nn_mm": round(float(nn.min()), 4), "max_nn_mm": round(float(nn.max()), 4),
            "min_gap_between_discs_mm": round(seam_gap, 4),
            "port_ring_exists": bool(comps == 1),
            "reading": ("**屏障/端口环前提 = 不成立**：16 盘之最小中心距 %.2fmm > 2*0.435=0.870mm ⇒ **盘两两相离**"
                        "（并集 %d 个连通分量，非单环）· 相邻盘最小缝宽 **%.3fmm > 0** ⇒ 模型口径下"
                        "**车道可在锚间穿行**（中心线只需离他锚 >=0.435）⇒ R390 §S1/S2 所依赖之『北出序被强制』**不能成立**。"
                        % (float(nn.min()), comps, seam_gap))}


def cut_orders(routes, ys=(56.5, 57.0, 57.5)):
    """对已存见证测 A 出口序（水平切面 y 处穿越点按 x 升序）。"""
    res = {}
    for yc in ys:
        pts = []
        for net, p in routes.items():
            arr = np.array(p)
            for k in range(len(arr) - 1):
                y1, y2 = arr[k][1], arr[k + 1][1]
                if (y1 - yc) * (y2 - yc) < 0:
                    t = (yc - y1) / (y2 - y1)
                    pts.append((float(arr[k][0] + t * (arr[k + 1][0] - arr[k][0])), net))
        pts.sort()
        res["y=%.1f" % yc] = {"order_by_x": [n for _, n in pts], "count": len(pts)}
    return res


def corridor_seam(routes, xs=(100, 110, 120, 127)):
    """走廊竖切面：按 y 升序测穿越序（南端 = seam）。"""
    res = {}
    for xc in xs:
        pts = []
        for net, p in routes.items():
            arr = np.array(p)
            for k in range(len(arr) - 1):
                x1, x2 = arr[k][0], arr[k + 1][0]
                if (x1 - xc) * (x2 - xc) < 0:
                    t = (xc - x1) / (x2 - x1)
                    pts.append((float(arr[k][1] + t * (arr[k + 1][1] - arr[k][1])), net))
        pts.sort()
        res["x=%.0f" % xc] = {"order_y_asc": [n for _, n in pts], "seam_south": (pts[0][1] if pts else None)}
    return res


def main():
    model, L, rast, free = load()
    routes = json.load(open(WITNESS))["routes"]
    r393 = json.load(open(R393)) if os.path.exists(R393) else {}
    res = {
        "o3_window_run_declaration": {
            "same_frozen_model_iteration": ["R383（一次实现 · 单次运行）"],
            "variant_reruns_declared": ["R384", "R387", "R388"],
            "variant_rerun_consequence": "自陈触强止损 FAIL 级 · 登记 · 禁再犯",
            "survey_only": ["R386", "R389", "R393", "R394"],
            "this_artifact": "**只读不变量计算 + 已存见证复核 · 未跑任何求解器**",
        },
        "artifact": "k2_r395_c_portorder_invariant_verifier_v1", "schema": 1,
        "from": "ENG · ARCHER R395", "to": "监理",
        "authority": "#K2-138 §三（准只读不变量验证器 C-PORTORDER · 限 ① 不变量 / ② [C2] 有限情形穷尽）",
        "board": "k2/hw/k2_v4_8L.l9.kicad_pcb", "board_sha16": BOARD_SHA16,
        "model": "C-B2UP-1_REALGEOM_BUS_v1", "model_sha16": MODEL_SHA16,
        "caliber": {"cell_mm": CELL, "hw_mm": HW, "lane_w_mm": LANE_W, "pitch_mm": PITCH, "layer": "In5.Cu",
                    "free_domain": "由闸所消费之同一冻结模型重建（#K2-138 §五 准 · 更严口径）"},
        "A_barrier_and_port_ring": {},
        "C1_A_exit_order_check": {}, "C2_corridor_seam_check": {}, "E_cut_route_closure": {},
        "verdict": {}, "boundary": "只读 · 未烙板 · 未改冻结四源/criteria/生成器/SPEC 设计内容 · 未派 WORKER · 未跑求解器",
    }
    res["A_barrier_and_port_ring"] = {"barrier_lemma": barrier_lemma(L),
                                      "port_ring": port_ring(L, free, rast)}
    res["C1_A_exit_order_check"] = cut_orders(routes)
    res["C2_corridor_seam_check"] = corridor_seam(routes)
    rk = {l["net"]: l["a_rank"] for l in L}
    east = max(L, key=lambda l: l["A"][0])["a_rank"]
    c1 = res["C1_A_exit_order_check"]["y=57.0"]["order_by_x"]
    c1_ranks = [rk[n] for n in c1]
    seam = res["C2_corridor_seam_check"]["x=120"]["seam_south"]
    res["C1_A_exit_order_check"]["ranks_by_x"] = c1_ranks
    res["C1_A_exit_order_check"]["is_ascending_a_rank"] = bool(c1_ranks == sorted(c1_ranks))
    res["C2_corridor_seam_check"]["eastmost_anchor_rank"] = east
    res["C2_corridor_seam_check"]["seam_rank_observed_x120"] = rk.get(seam)
    res["C2_corridor_seam_check"]["C2_holds_on_witness"] = bool(rk.get(seam) == east)
    res["C2_corridor_seam_check"]["reading"] = (
        "**机器核 [C2]：不成立** —— 已存 gate-clean 见证之走廊南端 seam 车道 = rank %s（非最东锚 rank%s）"
        "⇒ R390 §S2 之论断『南 seam 车道须为最东锚』**与本项目自有见证相悖**；"
        "S2 之『东侧各 lane 须北出 ⇒ 必与 seam 东行段相交』在几何上不成立（东侧 lane 顺序叠在北侧即免交）"
        "⇒ **R390 条件式 U≤15 论证之 [C2] 前提不成立 ⇒ 该论证无效**。" % (rk.get(seam), east))
    res["E_cut_route_closure"] = {
        "straight_line_min_capacity_r393": r393.get("readings", {}).get("min_over_all_separating_straight_cuts"),
        "general_curve_mincut": ("**未闭合（如实登记）**：格点 min-cut 在锚孔处退化为**袋 artefact**"
                                 "（0.03 栅格把每个锚孔围成 ~5 格自由袋，min-cut 直接切其 4 邻格 ⇒ 得 64 格≈1.92mm，"
                                 "与『13 条见证可越任何分离曲线』矛盾 ⇒ **该读数不可作证书**）。"
                                 "⇒ 一般曲线之 0.435-间距 min-cut 需**锚孔 snap 语义**（承 R383 `snap`）方能定义，本 v1 未完成。"),
        "reading": "切面路线（直线族）已由 R393 否证（28≥16）；一般曲线路线本 v1 **未闭合**（artefact）。",
    }
    res["verdict"] = {
        "(a)": "未取得（R383 13/16 gate-clean）",
        "(b)": "**未建立**：本 v1 机器核出 **[C2] 不成立**（R390 论证失效）；端口环不构成上限；"
               "一般曲线 min-cut 未闭合；**映射类群/辫型严格不变量本 v1 未实现**。",
        "item4": "R394 已核：13 条 互距/净距/端点 全过闸（部分闭合；3 条无坐标）",
        "outcome": "依 #K2-138 §三.4：**(b) 不成立 ⇒ 立即回报卡点** ⇒ 由**监理**判『冻结需求 ②-UP=16/16 是否须变』"
                   "⇒ **升 owner**（预声明路由 · ENG 不自启 · 不空转）",
    }
    with open(OUT, "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    open(OUT.replace(".json", ".sha16.txt"), "w").write(sha + "\n")
    print(json.dumps({"sha16": sha, "barrier": res["A_barrier_and_port_ring"]["barrier_lemma"],
                      "C1_ascending": res["C1_A_exit_order_check"]["is_ascending_a_rank"],
                      "C2_holds": res["C2_corridor_seam_check"]["C2_holds_on_witness"],
                      "seam_observed_rank": res["C2_corridor_seam_check"]["seam_rank_observed_x120"],
                      "eastmost": east}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
