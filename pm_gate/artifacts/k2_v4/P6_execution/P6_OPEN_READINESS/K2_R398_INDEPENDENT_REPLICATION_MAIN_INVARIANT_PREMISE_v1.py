#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R398 —— **主路结论之独立复核脚本**（应 #K2-139 §三.4『独立复核脚本（监理可复跑）』精神）

【O-2/O-3 强制首行自陈 · 本窗口运行清单】
  同一冻结模型内迭代：R383 · R397（主路不变量）· **本件 R398（独立复核 · 只读）**。
  变体重跑（已登记 FAIL 级）：R384 · R387 · R388。 只读普查/复核：R386/R389/R393/R394/R395/R396。
  ⇒ 本件**不建任何新方法、不跑构造器/解算器**：仅以**另一套独立算法**复核 R397 之**前提**（D 之连通性）。

复核对象（R397 §E 定理之**唯一经验前提**）：
  「32 个终端（16 A 锚 + 16 B 焊盘，吸附语义承 R383 `snap`）**全在同一个自由连通分量内**」。

独立算法（与 R397 的 `ndimage.label` 不同）：
  1. **显式栅格图**：以 scipy `csgraph.connected_components` 于**4-邻域**与**8-邻域**两种拓扑上分别求分量；
  2. **吸附半径普查**：逐终端报吸附半径（>0 即原始格点非自由 ⇒ 依赖 snap 语义）；
  3. **区带连通性**：A 簇区带与 B 簇区带是否同分量。

只读：不改冻结四源 / criteria / 生成器 / SPEC 设计内容；不写板；不派 WORKER。
复跑：python3 K2_R398_INDEPENDENT_REPLICATION_MAIN_INVARIANT_PREMISE_v1.py
"""
from __future__ import annotations
import json, sys, os, hashlib, datetime
import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
sys.path.insert(0, os.path.join(K2, "tools"))
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base  # noqa: E402

CELL, HW, PITCH, LANE_W = 0.03, 0.08, 0.435, 0.16
MODEL_SHA16, BOARD_SHA16 = "84f19701dfc1db31", "77aaa63fe016b450"
MODEL_JSON = "/tmp/opencode/archer/model_l8.json"
ANCHOR_JSON = "/tmp/opencode/k2r376/anchor_table.json"
P = os.path.join(K2, "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS")
OUT = os.path.join(P, "K2_R398_INDEPENDENT_REPLICATION_MAIN_INVARIANT_PREMISE_v1.json")
BOX = (81.0, 39.0, 145.0, 79.0)
SNAP_R = 12


def snap(free, x, y, rast, off, max_r=SNAP_R):
    i = int((x - rast.X0) / CELL) - off[0]; j = int((y - rast.Y0) / CELL) - off[1]
    nx, ny = free.shape
    i = min(max(i, 0), nx - 1); j = min(max(j, 0), ny - 1)
    if free[i, j]: return (i, j), 0
    for r in range(1, max_r + 1):
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if max(abs(di), abs(dj)) != r: continue
                a, b = i + di, j + dj
                if 0 <= a < nx and 0 <= b < ny and free[a, b]: return (a, b), r
    return None, None


def comps(free, conn8):
    nx, ny = free.shape
    ii, jj = np.where(free)
    idx = -np.ones((nx, ny), np.int64); idx[ii, jj] = np.arange(len(ii))
    offs = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    if conn8: offs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    R = []; C = []
    for di, dj in offs:
        a2 = ii + di; b2 = jj + dj
        m = (a2 >= 0) & (a2 < nx) & (b2 >= 0) & (b2 < ny)
        a, b, a2, b2 = ii[m], jj[m], a2[m], b2[m]
        m2 = free[a2, b2]
        a, b, a2, b2 = a[m2], b[m2], a2[m2], b2[m2]
        R.append(idx[a, b]); C.append(idx[a2, b2])
    rows = np.concatenate(R); cols = np.concatenate(C)
    g = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(ii), len(ii)))
    n, lab = connected_components(g, directed=False)
    return n, lab, idx, (ii, jj)


def main():
    model = json.load(open(MODEL_JSON)); model["_is_lane_patched"] = True
    L = sorted(json.load(open(ANCHOR_JSON))["lanes"], key=lambda r: r["a_rank"])
    rast = Raster(tuple(model["bbox"]), CELL)
    bad = build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW)
    i0 = int((BOX[0] - rast.X0) / CELL); i1 = int((BOX[2] - rast.X0) / CELL)
    j0 = int((BOX[1] - rast.Y0) / CELL); j1 = int((BOX[3] - rast.Y0) / CELL)
    free = (~bad)[i0:i1, j0:j1].copy()
    off = (i0, j0)
    terms = [(l["net"], tag, l[key]) for l in L for tag, key in (("A", "A"), ("B", "B"))]
    reps = {}
    snaps = []
    for net, tag, pt in terms:
        c, r = snap(free, pt[0], pt[1], rast, off)
        reps[(net, tag)] = c; snaps.append({"net": net, "tag": tag, "snap_r_cells": r})
    out = {"artifact": "k2_r398_independent_replication_main_invariant_premise_v1", "schema": 1,
           "from": "ENG · ARCHER R398", "to": "监理",
           "authority": "#K2-139 §三.4（独立复核脚本）· 复核 R397 §E 定理之经验前提",
           "board_sha16": BOARD_SHA16, "model_sha16": MODEL_SHA16,
           "caliber": {"cell_mm": CELL, "hw_mm": HW, "box": list(BOX), "snap_r_cells": SNAP_R},
           "replicated_claim": "32 终端（16 A / 16 B，snap 语义）全在同一自由连通分量内 ⇒ R397 §E 定理前提成立",
           "methods": {}}
    for tag, conn8 in (("4-neighbour", False), ("8-neighbour", True)):
        n, lab, idx, (ii, jj) = comps(free, conn8)
        labs = []
        for net, tg, pt in terms:
            c = reps[(net, tg)]
            labs.append(int(lab[idx[c]]) if c else -1)
        uniq = sorted(set(labs))
        out["methods"][tag] = {"n_components": int(n), "terminal_component_count": len(uniq),
                               "all_terminals_same_component": len(uniq) == 1 and -1 not in uniq,
                               "component_label": (uniq[0] if len(uniq) == 1 else None),
                               "component_size": (int((lab == uniq[0]).sum()) if len(uniq) == 1 else None)}
    lab2, n2 = ndimage.label(free)
    labs2 = [int(lab2[reps[(n_, t)]]) for n_, t, _ in terms if reps[(n_, t)]]
    out["methods"]["ndimage-label(cross)"] = {"n_components": int(n2),
                                              "terminal_component_count": len(set(labs2)),
                                              "all_terminals_same_component": len(set(labs2)) == 1}
    out["snap_census"] = {"max_snap_r_cells": max(s["snap_r_cells"] for s in snaps),
                          "n_terminals_needing_snap": sum(1 for s in snaps if s["snap_r_cells"] > 0),
                          "per_terminal": snaps}
    agree = all(v["all_terminals_same_component"] for v in out["methods"].values())
    out["verdict"] = {
        "replicated": bool(agree),
        "reading": ("**独立复核一致：32 终端全在同一自由分量内**（4-邻域 / 8-邻域 / ndimage 三法一致）"
                    "⇒ R397 §E 定理之经验前提**成立**。" if agree else
                    "**三法不一致** ⇒ R397 §E 前提**存疑**，须回报。"),
        "scope": "本件只复核**前提**（连通性）；**不**复核也不主张任何 (a)/(b) 结论。",
    }
    out["boundary"] = "只读 · 未烙板 · 未改冻结四源/criteria/生成器/SPEC 设计内容 · 未派 WORKER · 未跑构造器/解算器"
    with open(OUT, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    open(OUT.replace(".json", ".sha16.txt"), "w").write(sha + "\n")
    print(json.dumps({"sha16": sha, "methods": out["methods"], "replicated": agree,
                      "max_snap_r_cells": out["snap_census"]["max_snap_r_cells"],
                      "n_needing_snap": out["snap_census"]["n_terminals_needing_snap"]},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
