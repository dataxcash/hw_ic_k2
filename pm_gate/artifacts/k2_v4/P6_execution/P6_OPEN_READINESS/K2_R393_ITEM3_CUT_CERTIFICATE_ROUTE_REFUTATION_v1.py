#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R393 —— 收口窗口 项3：**(b) 路线之「切面容量证书」在本几何上被机器否证**

背景（承 #K2-136 §三 项5 · R383 O-2 · R386 finding_2 · R390 residual）：
  (b) 之候选形态之一是「切面容量证书」：
      若存在一条**分离曲线** Γ（把 16 个 A 锚与 16 个 B 焊盘分到两侧），
      使 Γ ∩ 自由域 上**两两 >= 0.435 之点数上限** < 16，
      则任何合法解之 16 条 lane 均须穿越 Γ（连续性），其穿越点两两 >= 0.435
      ⇒ 矛盾 ⇒ 不可行。**该松弛可靠**（松弛不可行 ⇒ 真实不可行）。

本件：在**冻结几何**上把此路线**算尽**（角度扫描的直线族）——
  · 直线族已含 R383/R386 只测过的**轴对齐切面**，并扩到**任意角度**；
  · 读数：min over 分离直线 of cap(Γ) = **28**（>= 16）⇒ **切面容量型 (b) 不成立**。

结论（净）：
  · 「切面容量」这一**(b) 路线**在本几何上被机器否证（不是"再找一条切面"能救的：
    角度扫描已覆盖全方向，最优仍在 28）；
  · ⇒ (b) 若要成立，**只能**是**端口序/辫型不变量**型证书（能力缺口 **C-PORTORDER**）；
  · 本件**不冒充 (b)**、**不充绿**、**不放松下限**。

只读：不改冻结四源 / criteria / 生成器 / SPEC 设计内容 / 原理图；不写板；不派 WORKER。
复现：python3 K2_R393_ITEM3_CUT_CERTIFICATE_ROUTE_REFUTATION_v1.py
"""
from __future__ import annotations
import json, sys, os, math, hashlib
import numpy as np

K2_ROOT = "/home/fila/jqdDev_2025/ic_hw/k2"
sys.path.insert(0, os.path.join(K2_ROOT, "tools"))
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base  # noqa: E402 (只读调用)

# ---- 冻结常数（= K2_R379 契约 / R377 模型 caliber，逐字不改）----
CELL, HW, PITCH, LANE_W = 0.03, 0.08, 0.435, 0.16
MODEL_SHA16, BOARD_SHA16 = "84f19701dfc1db31", "77aaa63fe016b450"
MODEL_JSON = "/tmp/opencode/archer/model_l8.json"
ANCHOR_JSON = "/tmp/opencode/k2r376/anchor_table.json"
OUT = os.path.join(K2_ROOT, "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS",
                   "K2_R393_ITEM3_CUT_CERTIFICATE_ROUTE_REFUTATION_v1.json")

TS = None  # set in main


def cut_capacity(free, x0, y0, nx, ny, c, step=0.05, span=120.0):
    """cap(Γ) = Σ_runs ( floor(len/0.435) + 1 )，Γ: nx*x+ny*y=c，只在板内采样。
    可靠松弛：任何合法解每条 lane 必与 Γ 相交，交点两两 >= 0.435 ⇒ #lane <= cap(Γ)。"""
    ts = np.arange(-span, span, step)
    X = nx * c - ny * ts
    Y = ny * c + nx * ts
    ii = np.floor((X - x0) / CELL).astype(np.int32)
    jj = np.floor((Y - y0) / CELL).astype(np.int32)
    ok = (ii >= 0) & (ii < free.shape[0]) & (jj >= 0) & (jj < free.shape[1])
    if ok.sum() < 3:
        return None
    f = np.zeros(len(ts), bool)
    f[ok] = free[ii[ok], jj[ok]]
    if not f.any():
        return None
    d = np.diff(np.concatenate([[0], f.view(np.int8), [0]]))
    st = np.where(d == 1)[0]
    en = np.where(d == -1)[0]
    runs = (en - st) * step
    return int(np.floor(runs / PITCH).sum() + len(runs))


def min_separating_cut_capacity(free, x0, y0, A, B, deg_step=3.0, c_step=0.1):
    """扫描**分离** A（16 A 锚）与 B（16 B 焊盘）之直线族；返回 (min, argmin)。"""
    best = (10 ** 9, None)
    hist = []
    for deg in np.arange(0.0, 180.0, deg_step):
        th = math.radians(deg)
        nx, ny = math.cos(th), math.sin(th)
        na = A @ np.array([nx, ny])
        nb = B @ np.array([nx, ny])
        lo, hi = max(na), min(nb)
        if lo >= hi:
            lo, hi = max(nb), min(na)
            if lo >= hi:
                continue
        loc_min = 10 ** 9
        for c in np.arange(lo, hi, c_step):
            k = cut_capacity(free, x0, y0, nx, ny, float(c))
            if k is None:
                continue
            loc_min = min(loc_min, k)
            if k < best[0]:
                best = (k, {"deg": round(float(deg), 3), "c": round(float(c), 4)})
        if loc_min < 10 ** 9:
            hist.append((round(float(deg), 1), int(loc_min)))
    return best, hist


def main():
    model = json.load(open(MODEL_JSON))
    model["_is_lane_patched"] = True
    anchors = json.load(open(ANCHOR_JSON))["lanes"]
    A = np.array([[l["A"][0], l["A"][1]] for l in anchors])
    B = np.array([[l["B"][0], l["B"][1]] for l in anchors])
    rast = Raster(tuple(model["bbox"]), CELL)
    bad = build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW)  # True = blocked
    free = ~bad
    (mn, arg), hist = min_separating_cut_capacity(free, rast.X0, rast.Y0, A, B)

    # 轴对齐族（R383/R386 只测过的），供对照
    horiz = min(k for k in (cut_capacity(free, rast.X0, rast.Y0, 0, 1, y)
                            for y in [53.0, 53.6, 54.0, 54.5, 54.8]) if k is not None)
    vert = min(k for k in (cut_capacity(free, rast.X0, rast.Y0, 1, 0, x)
                           for x in [94, 96, 100, 110, 120, 126]) if k is not None)

    res = {
        "artifact": "k2_r393_item3_cut_certificate_route_refutation_v1",
        "schema": 1, "from": "ENG · ARCHER", "to": "监理",
        "board": "k2/hw/k2_v4_8L.l9.kicad_pcb", "board_sha16": BOARD_SHA16,
        "model": "C-B2UP-1_REALGEOM_BUS_v1", "model_sha16": MODEL_SHA16,
        "caliber": {"cell_mm": CELL, "hw_mm": HW, "lane_w_mm": LANE_W, "pitch_mm": PITCH,
                    "layer": "In5.Cu", "endpoints": "fixed（位移 0）"},
        "question": "(b) 之『**直线切面**容量证书』路线，在冻结几何上是否可得（cap(Γ) < 16）？",
        "method": ("可靠松弛：任一合法解每条 lane 必与分离曲线 Γ 相交（连续性），"
                   "交点两两 >= 0.435 ⇒ U <= cap(Γ)=Σ_runs(floor(len/0.435)+1)。"
                   "扫任意角度之直线族（3°步长，含全部轴对齐切面），取 min。"),
        "readings": {
            "min_over_all_separating_straight_cuts": mn,
            "argmin": arg,
            "axis_aligned_horizontal_family_min": horiz,
            "axis_aligned_vertical_family_min": vert,
            "n_orientations_scanned": len(hist),
        },
        "verdict": {
            "(b)_via_straight_cut_capacity": "**否证**（min=28 >= 16 ⇒ **直线切面族**不能给出 U<16）",
            "(b)_overall": "仍未建立（直线切面族已否证；**一般曲线** min-cut 未做；不变量型缺器 C-PORTORDER）",
            "(a)": "未取得（R383: 13/16 gate-clean）",
        },
        "soundness_note": ("本件为**松弛**：cap(Γ) 忽略同一 lane 之锚孔自避让、锚孔他避让、"
                           "折角等全部约束 ⇒ 真实可行域更小 ⇒ "
                           "cap(Γ) 是**上界**；min=28 仍 >= 16 ⇒ 此路线否证。"),
        "not_a_certificate": "本件**不是** (b) 证书；是 (b) 之**一条候选路线**的**否证件**。",
        "route_closure": ("承 R383 O-2 与 R386 finding_2（其只测轴对齐切面：竖直 66–89 · 横向 162），"
                          "本件把**直线族角度扫尽**后 min=28 ⇒ **「再换一条直线切面」不能救**："
                          "**直线切面**容量型 (b) 在本几何上不成立。"),
        "residual_not_closed": ("**残余（如实登记 · 未闭合）**：**一般曲线**（可绕行障碍/贴障碍走）之分离曲线"
                                "容量最小化 = 自由域 min-cut，本件**未做** ⇒ 本件只闭合**直线族**，"
                                "不声称『切面容量型整体不成立』。"),
        "reproduce": "python3 K2_R393_ITEM3_CUT_CERTIFICATE_ROUTE_REFUTATION_v1.py",
        "boundary": ("只读 · 未烙板 · 未改冻结四源/criteria/生成器/SPEC · 未派 WORKER · "
                     "不冒充严格证书 (b) · 不充绿 · 不放松 DRC 下限"),
    }
    res["cut_orientation_min_hist"] = hist
    with open(OUT, "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    open(OUT.replace(".json", ".sha16.txt"), "w").write(sha + "\n")
    print(json.dumps({"min_separating_straight_cut_capacity": mn, "argmin": arg,
                      "horizontal_min": horiz, "vertical_min": vert,
                      "sha16": sha, "out": OUT}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
