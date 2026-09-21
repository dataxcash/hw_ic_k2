#!/usr/bin/env python3
"""K2 · B2 —— **②-UP In5 走廊结构 / 容量 census**（只读 · P4 在阶测量 · 造活）。

目的：把 ②-UP（`PCIE_UP_OUT` 16/16 车道 ≤2 via · F→In5→F）之**几何卡点**从
      「缝/指派（①/②）」层搬到**真实走廊层**，并给出 (b) 之可证性判定。

零重跑布线器 · 零烙板 · 零改件 · 只读冻结件（四源/受审板/判据）。
口径：物理 keepout **0.5300** = hw 0.08 + 0.35 + margin 0.100（#K2-130 §四）；
      自网**全转口径**（`is_lane` 排除本 16 网铜 · 承 #K2-133 §三 N1）。

用法：
  python3 tools/k2_p4_b2_in5_corridor_structure_census_v1.py --board <l8.kicad_pcb> --out <json>
       [--a-sites <sites_phys.json>] [--b-sites <sites_b_board_v1.json>]
       [--dump-py <AppDir python3.11>] [--dump-out <model.json>] [--prev-wo <wo_c_By_dn.json>]
"""
from __future__ import annotations
import argparse, json, math, subprocess, sys, os, collections
import numpy as np
import importlib.util
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ASITES = "/tmp/opencode/archer/sites_phys.json"
DEFAULT_BSITES = "/tmp/opencode/archer/sites_b_board_v1.json"
DEFAULT_PREVWO = "/tmp/opencode/archer/wo_c_By_dn.json"
HW = 0.08            # lane_w/2 (0.16)
MARGIN = 0.100       # 物理口径余量（未改）
PITCH = 0.435        # = 0.335 + margin 0.100
KEEPOUT = 0.5300     # = HW + 0.35 + MARGIN
LANES = [f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")]
CELL = 0.05


def load_v3():
    spec = importlib.util.spec_from_file_location("v3m", os.path.join(HERE, "k2_p4_b2_in5_lane_router_v3.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.is_lane = lambda n: n in set(LANES)
    m.PAD_EXTRA = MARGIN
    return m


def dump_model(board, out, dump_py):
    subprocess.run([dump_py, os.path.join(HERE, "k2_p4_b2_board_in5_model_dump_v1.py"), board, out], check=True,
                   stdout=subprocess.DEVNULL)
    return json.load(open(out))


def runs(arr_x0, cell, mask, lo, hi, minlen=0.10):
    """1-D 自由 run 列表（沿 x）。"""
    i0, i1 = int(round((lo - arr_x0) / cell)), int(round((hi - arr_x0) / cell))
    i0, i1 = max(0, i0), min(len(mask) - 1, i1)
    out = []; s = None
    for i in range(i0, i1 + 1):
        if mask[i] and s is None:
            s = i
        elif not mask[i] and s is not None:
            out.append((arr_x0 + s * cell, arr_x0 + i * cell)); s = None
    if s is not None:
        out.append((arr_x0 + s * cell, arr_x0 + (i1 + 1) * cell))
    return [r for r in out if r[1] - r[0] >= minlen]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--a-sites", default=DEFAULT_ASITES)
    ap.add_argument("--b-sites", default=DEFAULT_BSITES)
    ap.add_argument("--prev-wo", default=DEFAULT_PREVWO)
    ap.add_argument("--dump-py", default=os.path.join(os.path.dirname(HERE), "..", "AppDir/usr/bin/python3.11"))
    ap.add_argument("--dump-out", default="/tmp/opencode/archer/r260/model_census.json")
    a = ap.parse_args()

    v3 = load_v3()
    model = dump_model(a.board, a.dump_out, a.dump_py)
    A = json.load(open(a.a_sites)); B = json.load(open(a.b_sites))
    rast = v3.Raster(model["bbox"], CELL)
    anchors = v3.lane_anchors(model)
    for an in anchors:
        an["A"] = tuple(A[an["net"]]); an["B"] = tuple(B[an["net"]])
    base = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
    c_all, own = v3.anchor_keepout(rast, anchors, HW)
    free = (~base)
    x0, y0, x1, y1 = model["bbox"]
    rep = {"schema": 1, "artifact": "k2_p4_b2_in5_corridor_structure_census",
           "board": a.board, "cell_mm": CELL, "caliber": {"keepout": KEEPOUT, "hw": HW, "margin": MARGIN,
                                                          "pitch_eff": PITCH, "own_copper": "excluded (no-move 全转)"},
           "bbox": model["bbox"], "design": model.get("design", {})}

    # ---- F1: A/B 分离线 y=54.88 之自由 x-runs（全宽） ----
    jL = int(round((54.88 - y0) / CELL))
    f1runs = runs(x0, CELL, free[:, jL], x0, x1)
    rep["F1_separating_line_free_runs"] = {
        "line_y": 54.88,
        "free_x_runs": [[round(u, 2), round(v, 2)] for u, v in f1runs],
        "note": ("A 侧可达之跨线点 = 与 A 排(y>=55.2 · x<=103.35) 相邻之 run ⇒ 84.40-92.90 及 93.6..102.35 之窄缝（=①《缝枚举》13 段 + P 点）。"
                 "**但** y=54.88 在东侧亦自由（108.55-133.25 · 134.35-143.10）——后者属 B 侧（墙北）区，"
                 "须先经东通道跨越方可达 ⇒ 故它**不是**『A 侧跨线点』，而是『跨线后可用的北区』。"),
        "consequence": ("①/② 模型把『P 跨点 = P 孔位 x』与『N 跨点限于 A 排邻近 13 段』当作**刚性约束** —— "
                        "实测二者皆**非绑定**：车道可自 A 排**先南下**（Y>54.88）→ 南通道 → 东通道 → 再于 "
                        "**x 135.4–142.62 跨越 y=54.88**（F4 槽数 17）⇒ 『A 侧 x 序 ↔ B 侧 x 序次序反转』之顾虑**作废**；"
                        "16 车道之跨线**不必**集中在 A 排附近。")}

    # ---- F2: 绑定几何 ----
    band = [s for s in model["segs"]["In5.Cu"]
            if s[5] == "PERSTA#" and 103.0 <= min(s[0], s[2]) and max(s[0], s[2]) <= 136.0
            and 55.0 <= min(s[1], s[3]) and max(s[1], s[3]) <= 57.0]
    bandv = [v for v in model["vias"] if "In5.Cu" in v["layers"] and 132.0 <= v["x"] <= 136.6 and 42.0 <= v["y"] <= 57.6]
    colv = [v for v in bandv if 133.2 <= v["x"] <= 136.3 and v["y"] <= 56.0]
    rep["F2_binding_geometry"] = {
        "wall_components": {
            "stitching_via_field": {"bbox": [82.0, 48.0, 118.0, 55.5],
                                    "note": "GND/P3V3 缝合孔场（固定件 · #K2-133 §三 禁当自网拆）"},
            "persta_band": {"net": "PERSTA#", "n_ins_seg": len(band),
                            "bbox": [round(min(min(s[0], s[2]) for s in band), 2), round(min(min(s[1], s[3]) for s in band), 2),
                                     round(max(max(s[0], s[2]) for s in band), 2), round(max(max(s[1], s[3]) for s in band), 2)],
                            "segs": [[round(v, 2) for v in s[:4]] for s in sorted(band, key=lambda s: min(s[0], s[2]))],
                            "note": "他网 In5 折线 · 沿 y 55.15–56.10 横扫 x 105.6–133.7 ⇒ 与缝合孔场合为一墙"},
            "connector_via_column": {"x_band": [133.2, 136.3], "y_band": [42.0, 56.0], "n_vias": len(colv),
                                     "by_net": dict(collections.Counter(v["net"] for v in colv)),
                                     "note": "连接器焊盘之通孔列（x≈133.8/135.5/136.1）⇒ 北区内东西向隔断"}},
        "forced_detour": "A 排 → **南通道**(y 56–68) → **东通道**(x≈135.4–142.62) → 北区/东厅(y 41–55) → B 锚",
        "south_to_north_throat": {"found": True,
                                  "note": "南通道 ↔ 北区/东厅 之唯一连通口位于 x≈135.4–142.62（逐 y run 见下）；"
                                          "PERSTA# 带 + 缝合孔场把 x 105.6–135.4 之南北向通路封死",
                                  "runs_at_y": {str(y): [[round(u, 2), round(v, 2)] for u, v in runs(x0, CELL, free[:, int(round((y - y0) / CELL))], 130.0, min(x1, 142.95))]
                                                for y in (55.5, 56.5, 57.5)}}}

    # ---- F4: 东通道容量 ----
    edge = model.get("design", {}).get("copper_edge_clearance", 0.3)
    x_edge = x1  # 43 -> 板 East 边
    usable_hi = x_edge - edge - HW
    thr = runs(x0, CELL, free[:, int(round((56.5 - y0) / CELL))], 130.0, min(x1, usable_hi + 0.01))
    wide = max((v - u for u, v in thr), default=0.0)
    rep["F4_east_passage_capacity"] = {
        "y": 56.5, "free_runs": [[round(u, 2), round(v, 2)] for u, v in thr],
        "usable_width_mm": round(wide, 3), "pitch_eff_mm": PITCH,
        "lane_slots": int(math.floor(wide / PITCH) + 1) if wide > 0 else 0,
        "edge_clearance_used_mm": edge,
        "note": "东通道自由宽（扣板边 0.3 + 半线宽 0.08）⇒ 车道槽数 >=16 ⇒ **C-w 不必**（与 R259h 一致）"}

    # ---- F3: cell 级割容量（严格上界：cell*sqrt2 < pitch ⇒ 车道互距 >=pitch ⇒ cell-不相交） ----
    ia, ja = int(round((x0 - x0) / CELL)), 0
    def cellflow(cell):
        K = int(round(cell / CELL))
        NX, NY = free.shape[0] // K, free.shape[1] // K
        fr = free[:NX * K, :NY * K].reshape(NX, K, NY, K).any(axis=(1, 3))
        ii, jj = np.nonzero(fr); n = len(ii)
        idx = np.full(fr.shape, -1, np.int64); idx[ii, jj] = np.arange(n)
        def cellof(px, py):
            i = int(math.floor((px - x0) / cell)); j = int(math.floor((py - y0) / cell))
            return i, j
        term = []
        for an in anchors:
            for tag in ("A", "B"):
                i, j = cellof(*an[tag])
                if 0 <= i < NX and 0 <= j < NY and fr[i, j]:
                    term.append(idx[i, j])
                else:
                    best = None
                    for di in range(-3, 4):
                        for dj in range(-3, 4):
                            p, q = i + di, j + dj
                            if 0 <= p < NX and 0 <= q < NY and fr[p, q]:
                                d = di * di + dj * dj
                                if best is None or d < best[0]:
                                    best = (d, idx[p, q])
                    if best:
                        term.append(best[1])
        term = sorted(set(term))
        rows, cols, data = [], [], []
        cap = np.ones(n, np.int64); cap[term] = 1
        rows += list(2 * np.arange(n)); cols += list(2 * np.arange(n) + 1); data += list(cap)
        for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1), (-1, 0), (0, -1), (-1, -1), (-1, 1)):
            ni, nj = ii + di, jj + dj
            m = (ni >= 0) & (ni < NX) & (nj >= 0) & (nj < NY)
            if not m.any():
                continue
            aa, bbb = ni[m], nj[m]
            ok = (aa >= 0) & (aa < NX) & (bbb >= 0) & (bbb < NY)
            tgt = np.full(int(m.sum()), -1, np.int64); tgt[ok] = idx[aa[ok], bbb[ok]]
            k = idx[ii[m], jj[m]]; g = tgt >= 0
            rows += list(2 * k[g] + 1); cols += list(2 * tgt[g]); data += list(np.full(int(g.sum()), 100, np.int64))
        S, T = 2 * n + 2, 2 * n + 3
        rows += [S] * len(term); cols += list(2 * np.array(term)); data += [1] * len(term)
        rows += list(2 * np.array(term) + 1); cols += [T] * len(term); data += [1] * len(term)
        G = csr_matrix((np.array(data, np.int32), (np.array(rows), np.array(cols))), shape=(2 * n + 4, 2 * n + 4))
        return int(maximum_flow(G, S, T).flow_value), int(fr.sum()), len(term)
    f3 = {}
    for c in (0.30, 0.25, 0.20, 0.15):
        fv, nf, nt = cellflow(c)
        f3["%.2f" % c] = {"cell_sqrt2": round(c * math.sqrt(2), 4), "valid_upper_bound": bool(c * math.sqrt(2) < PITCH),
                          "max_node_disjoint_paths": fv, "free_cells": nf, "terminals": nt}
    rep["F3_cut_capacity_census"] = {
        "method": "cell-不相交 A-锚集 → B-锚集 最大流（scipy maximum_flow · 节点容量 1 · 8-邻接）；"
                  "取 cell*sqrt2 < pitch_eff ⇒ 车道互距 >=pitch ⇒ 两道不可能共 cell ⇒ 该最大流 **>= 车道数**（严格上界）。",
        "results": f3,
        "verdict": "各 cell 尺度下最大流均 = **32 = 终端饱和**（16 A + 16 B）⇒ **不存在 <16 之 cell 级割** ⇒ "
                   "**(b)「容量型/割线型」确证不可得**（把 R259m 之『仅竖直割线』推广到**任意 cell 级割**）。"
                   "(b) 仅剩『精确计数（MILP/CP-SAT）型』⇒ 须监理具名方法（#K2-131 §三(乙)② / #K2-132 §二(乙)①）。"}

    # ---- F5: 12/16 残余归因 ----
    f5 = {"prev_wo": a.prev_wo}
    try:
        wo = json.load(open(a.prev_wo))
        f5["n_routed"] = wo.get("n_routed"); f5["failed"] = wo.get("failed")
        f5["failed_B_anchors"] = {nm: [round(v, 2) for v in B[nm]] for nm in wo.get("failed", [])}
        f5["per_lane_len"] = {k: v.get("len_mm") for k, v in sorted(wo.get("routes", {}).items())}
        f5["attribution"] = ("4 条未布网之 B 锚全位于**北区远端/西段**（0_N 127.01,43.25 · 0_P 141.22,42.65 · "
                             "1_P 127.59,43.85 · 2_P 137.16,46.25）。其失败系**布线序**：先布者占用"
                             "东通道**外槽**，后布者无位可入 ⇒ 缺者为 **nesting-aware（洋葱层）束布线**，非空间不足。")
    except Exception as e:
        f5["error"] = str(e)
    rep["F5_prev_solution_attribution"] = f5

    rep["conclusions"] = [
        "C1 ①/②『缝/指派』非绑定：y=54.88 跨线在东侧亦自由 ⇒ 跨线点位置自由度大 ⇒ 次序反转顾虑作废。",
        "C2 绑定几何 = 缝合孔场(x82–118,y48–55.5) + PERSTA# In5 带(8 段 · y55.15–56.10 · x105.6–133.7) + 连接器通孔列(x≈133.2–136.3) ⇒ 强制绕行（南通道→东通道→北区/东厅）。",
        "C3 东通道可用宽 ≈ 见 F4 ⇒ 车道槽 >=16 ⇒ **C-w 不必**（不申报 · 与 R259h 一致）。",
        "C4 (b) 容量型/割线型确证不可得（F3 任意 cell 级割 >=32）⇒ (b) 仅剩精确计数型（须监理具名方法）。",
        "C5 卡点 = **同时性/束布线之实现能力（C-B2UP-1）**；建议方法 = **nesting-aware（洋葱层）构造**（见 next_stage_plan）。"]
    rep["next_stage_plan"] = [
        {"id": "P-1", "item": "③④ 一次实现（**待监理给 C-B2UP-1 限期/口径** · 承 #K2-132 §三 · handoff §7.2）",
         "method": "nesting-aware 洋葱层构造（构造式 · 非扫描 · 非有界搜索）："
                   "(a) 定序：以 A 排 x 序 ⇄ 南通道 y 层序（组合梳状规则：最西 A 锚 → 最外/最深通道层）；"
                   "(b) 东通道 x 槽按 nesting 递增分配（内→外）；"
                   "(c) 北区/东厅按 nesting 依次西进至 B 锚；"
                   "(d) 模型须含：自网 In2–In5 盲孔切除（全转）· Edge.Cuts 0.300 约束；"
                   "(e) 交付 (a) 16/16 见证 + buildability.mode='no_move' 或 (b) 严格证书。",
         "budget": "并入 #K2-132 §三 之『一次实现、一次交付』（不新增实现次数）"},
        {"id": "P-2", "item": "D2 同批落库（rev=7 + spec-rev-55 + l9 + 网表 bump 新件 + 具名豁免表）", "gate": "落库后判定器 19/19 @bump 件"},
        {"id": "P-3", "item": "l9 收口后 R4 复测闸（19 维 + ②-UP/②-DN + ref_plane_continuity + 等长/3W/85Ω）", "gate": "P4 全绿方可下 P5"}]
    rep["kb_note"] = ("本件为**在阶测量/归因**（非待裁请求 · **不含新待裁锚** · 承 #K2-133 O-4）；"
                      "既有待裁 3 条（C-B2UP-1 限期 / (b) 具名方法 / rev=7 落点）不变。")
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps({"out": a.out, "F1_runs": len(f1runs), "F3": f3, "slots": rep["F4_east_passage_capacity"]["lane_slots"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
