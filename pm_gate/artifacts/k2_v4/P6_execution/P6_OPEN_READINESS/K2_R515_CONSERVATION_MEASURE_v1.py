#!/usr/bin/env python3
"""K2 · R515-C —— 遵「收敛停滞」停止令：出**守恒级**读数（只读 · `Solve()` 0 次）：
**必过断面**在两层上各能并排过几根车道（pitch P 的 1-D 装箱），以及墙洞带宽 —— 用来回答
「哪层 / 哪资源 / 被谁占死 / 为何任何分配都不可能」。

方法：逐层障碍栅（在册 `build_base`）的 free 格点阵；沿**直线割**取最长连续自由段（格点数 = 该段可并排的车道数，
因格点间距恰为 P）；报告 ①各必过断面 ②墙列的自由段（= 墙洞）③按区域的最小值。
"""
import importlib, json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
R = importlib.import_module("K2_" + "R" + "514" + "_LAYERHOP_JOINT_MCF_v2")
P = R.P; NX = R.NX; NY = R.NY; X0 = R.X0; Y0 = R.Y0


def longest_run(v):
    best = cur = 0
    for x in v:
        cur = cur + 1 if x else 0
        best = max(best, cur)
    return best


def runs(v):
    out = []; cur = 0
    for x in v:
        if x:
            cur += 1
        else:
            if cur: out.append(cur)
            cur = 0
    if cur: out.append(cur)
    return out


def main():
    out = os.path.join(HERE, "K2_R515_CONSERVATION_MEASURE_v1.json")
    t0 = time.time()
    model = json.load(open("/tmp/opencode/archer/model_l8.json"))
    g2 = R.Gen2(model, l1scope="full", verbose=True)
    F = {L: g2.free_node[L].reshape(NX, NY) for L in (0, 1)}     # free[i,j] = True ⇒ 该格点可布线
    rep = {"artifact": "k2_r515_conservation_measure_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "monitor convergence-stall stop-order (must produce a binary OR a conservation-grade "
                        "blocker report: which layer / which resource / who monopolises it / why no allocation)",
           "method": "per-layer registered obstacle raster (build_base); for each straight cut, longest contiguous "
                     "free run in PITCH-P cells = max lanes that can cross side by side (cell pitch == P)",
           "P_mm": P, "layers": {}}

    def vcut(i):
        return {R.LAYER_OF[L]: longest_run(F[L][i, :]) for L in (0, 1)}

    def hcut(j):
        return {R.LAYER_OF[L]: longest_run(F[L][:, j]) for L in (0, 1)}

    COMB_COLS = list(range(0, 34))
    WALL_COL = 114
    GATE_COLS = list(range(113, 136))
    GATE_ROW, GATE_ROWS = 36, list(range(30, 39))
    MID_COLS = list(range(34, 113))
    rep["cut_vertical_comb_exit_cols0_33"] = {
        "per_col_lanes": {str(i): vcut(i) for i in COMB_COLS},
        "min_over_cols": {R.LAYER_OF[L]: int(min(vcut(i)[R.LAYER_OF[L]] for i in COMB_COLS)) for L in (0, 1)}}
    rep["cut_vertical_mid_cols34_112"] = {
        "min_over_cols": {R.LAYER_OF[L]: int(min(vcut(i)[R.LAYER_OF[L]] for i in MID_COLS)) for L in (0, 1)}}
    rep["cut_vertical_gate_cols113_135"] = {
        "min_over_cols": {R.LAYER_OF[L]: int(min(vcut(i)[R.LAYER_OF[L]] for i in GATE_COLS)) for L in (0, 1)}}
    rep["cut_horizontal_gate_band_rows30_38"] = {
        "min_over_rows": {R.LAYER_OF[L]: int(min(hcut(j)[R.LAYER_OF[L]] for j in GATE_ROWS)) for L in (0, 1)}}
    # 墙列（= 墙洞）在两层上的自由段
    rep["wall_column_free_runs"] = {R.LAYER_OF[L]: runs(F[L][WALL_COL, :]) for L in (0, 1)}
    rep["wall_gaps"] = {"col": WALL_COL, "x_mm": round(X0 + WALL_COL * P, 3)}
    # 必过断面汇总 + 与需求对比（16 根全体 / 西组 8 根）
    mins = {R.LAYER_OF[L]: int(min(vcut(i)[R.LAYER_OF[L]] for i in COMB_COLS)) for L in (0, 1)}
    gate = {R.LAYER_OF[L]: int(min(vcut(i)[R.LAYER_OF[L]] for i in GATE_COLS)) for L in (0, 1)}
    nw5 = int(min(vcut(i)["In5.Cu"] for i in COMB_COLS)); nw4 = int(min(vcut(i)["In4.Cu"] for i in COMB_COLS))
    ng5 = int(min(vcut(i)["In5.Cu"] for i in GATE_COLS)); ng4 = int(min(vcut(i)["In4.Cu"] for i in GATE_COLS))
    rep["mandatory_passages_vs_demand"] = {
        "comb_exit_min_lanes": {"In5": nw5, "In4": nw4, "sum_two_layers": nw5 + nw4, "demand_all_16": 16,
                                "slack": nw5 + nw4 - 16},
        "gate_funnel_min_lanes": {"In5": ng5, "In4": ng4, "sum_two_layers": ng5 + ng4, "demand_all_16": 16,
                                  "slack": ng5 + ng4 - 16},
        "wall_gap_count": {"In5": len(runs(F[0][WALL_COL, :])), "In4": len(runs(F[1][WALL_COL, :])),
                           "demand_west_group": 8},
    }
    rep["verdict_fields"] = {
        "which_layer": "缺口**不在某一层**：绑定点是「规定身份配对 × 跨层可解性」；窄段（梳齿出口 / 东门 / 墙洞）"
                       "才是无法支付换序的地方 —— 见 mandatory_passages_vs_demand",
        "which_resource": "资源 = **可支付的换序事件**（= 宽区内 ≥1 个格点间距的横向余量，且与过孔站点**联合**可用），"
                          "不是面积、不是总宽度",
        "monopolised_by": "被**设计自己的 16 根线**占住：每个必过断面上 16 根必须同时通过，"
                          "而该断面两层合计容量见 slack 一栏（余量即「可借来换序」的上限）",
        "why_no_allocation": "**本件不断言**任何分配不可能（见 report §四：模型是保守抽象 ⇒ UNSAT 不是证书；"
                             "R513-T4 已证所有直线割 ≥66 ⇒ 无宽度型证书）"}
    rep["boundaries"] = "read-only; Solve() 0 calls; nothing edited; frozen four sources untouched"
    rep["buildability"] = "NOT-APPLICABLE (capacity measurement for a blocker report; no construction claim)"
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("mandatory_passages_vs_demand", "wall_column_free_runs",
                                          "cut_vertical_gate_cols113_135", "cut_horizontal_gate_band_rows30_38",
                                          "verdict_fields")}, ensure_ascii=False, indent=1)[:2600])
    print("WROTE", out)


if __name__ == "__main__":
    main()
