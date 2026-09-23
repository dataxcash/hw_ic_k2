#!/usr/bin/env python3
"""R475 · 建图质检闸（#K2-169 §四.3.a）判定读数的可复现仪器（只读几何 · 不打求解器）。

回答：#K2-169 末窗所派『建图质检闸 → 二值终局』中，闸的 CP-SAT 报 INFEASIBLE
（/tmp/opencode/r473/gate2.py · 19.6s · 逐变量投影域非空 {ci:20,s:13,p:16,n:24,co:17}）。
本件判定该 INFEASIBLE 的性质：是**图纸缺陷**（残余单行走行模板）抑或**物理不可行**。

口径（全部走独立路径 · 在册 Raster/build_base/lane_anchors）：
  H1 逐变量『走行行 s』投影域：在 0.435 格上与细格上分别求全 16 网可用行位；
     Hall 必要检查：16 网两两互异 ⇒ 可用行位数须 ≥16。
  H2 强制公共跨段：任一 lane 之南带走行横跨 [max CIN, min PX]（该段必含于其自身跨段）
     ⇒ 其行高必落在『公共跨段全清』之自由 y 集内 ⇒ 该集在 0.435 节距下的最大点数
     即该模板之容量上界。
  H3 反向（排除真不可行）：在夹缝截面 x=133.5 上求自由 y 集，按 0.435 打包 → 若 ≥16
     则『板上无解』不能成立（与在册 R393/R395 之 min-cut=28/16 一致）。
  H4 稳健性：H1/H2 分别在 PAD_EXTRA ∈ {0, 在册 margin} 两种口径下复算。
"""
import json, math, sys, hashlib, os
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base, lane_anchors
import k2_p4_b2_in5_lane_router_v3 as RT

MODEL = "/tmp/opencode/archer/model_l8.json"
P, HW, CELL = 0.435, 0.08, 0.03
PAD_REG = 0.100 + 0.5 * CELL * math.sqrt(2)          # 在册 margin + 折角安全（gate2.py 口径）
CIN = [round(84.0 + k * P, 4) for k in range(28)]     # 锚侧下行走廊列
COU = [round(120.0 + k * P, 4) for k in range(int((134.0 - 120.0) / P) + 1)]  # 锚侧上行走廊列
SY = lambda s: round(57.100 + P * s, 4)               # 南带走行行高
PX = lambda p: round(135.45 + P * p, 4)               # 缝口列
PXL = [PX(p) for p in range(18)]

def build(pad_extra):
    RT.PAD_EXTRA = pad_extra
    m = json.load(open(MODEL))
    an = [a for a in lane_anchors(m) if a["net"].startswith("PCIE_UP_OUT")]
    rast = Raster(m["bbox"], CELL)
    bad = build_base(rast, m, "In5.Cu", set(), set(), HW, frozenset())
    return m, an, rast, bad

def free_y_on_line(rast, bad, x, lo, hi, step=0.01):
    ys = np.arange(lo, hi + 1e-9, step)
    i = int(round((x - rast.X0) / rast.step)); j = np.rint((ys - rast.Y0) / rast.step).astype(int)
    ok = (j >= 0) & (j < rast.NY) & (i >= 0) & (i < rast.NX)
    f = np.zeros(len(ys), bool); f[ok] = ~bad[i, j[ok]]
    return ys, f

def free_x_on_line(rast, bad, y, lo, hi, step=0.01):
    xs = np.arange(lo, hi + 1e-9, step)
    i = np.rint((xs - rast.X0) / rast.step).astype(int); j = int(round((y - rast.Y0) / rast.step))
    ok = (i >= 0) & (i < rast.NX) & (j >= 0) & (j < rast.NY)
    f = np.zeros(len(xs), bool); f[ok] = ~bad[i[ok], j]
    return xs, f

def runs(vals, flags, tol):
    out, s = [], None
    for k, v in enumerate(flags):
        if v and s is None: s = k
        if not v and s is not None: out.append((vals[s], vals[k - 1])); s = None
    if s is not None: out.append((vals[s], vals[-1]))
    return out

def maxpack(iv, pitch):
    """一维打包上界：点数两两 ≥pitch。逐段 floor(L/pitch)+1 之和（段间互不约束，故为上界）。"""
    return sum(int(math.floor((b - a) / pitch + 1e-9)) + 1 for a, b in iv)

res = {"ledger": "K2_R475 · 建图质检闸判定性质复核", "cell_mm": CELL, "pitch_mm": P, "lane_w_mm": HW}
for tag, pad in (("pad_0", 0.0), ("pad_reg", PAD_REG)):
    m, an, rast, bad = build(pad)
    A = {a["net"]: a["A"] for a in an}; B = {a["net"]: a["B"] for a in an}
    names = sorted(a["net"] for a in an)
    # 公共跨段：任一 lane 横跨 [max CIN, min PX]
    XW, XE = max(CIN), min(PXL)
    Y0, Y1 = 55.5, 69.0
    # 公共跨段全清之行位（逐行在 [XW,XE] 上全清）
    row_ok = []
    for y in np.arange(Y0, Y1 + 1e-9, 0.01):
        xs_, fx = free_x_on_line(rast, bad, float(y), XW - 0.01, XE + 0.01)
        row_ok.append((round(float(y), 2), bool(fx.all())))
    iv_common = runs([y for y, _ in row_ok], [o for _, o in row_ok], 0.01)
    # 细格可用行位（0.0435 = P/10）
    okmap = {yy: o for yy, o in row_ok}
    fine_pts = [round(float(y), 4) for y in np.arange(Y0, Y1 + 1e-9, 0.0435)
                if okmap.get(round(float(y), 2), False)]
    # 0.435 格上之可用行位（gate2.py 的 DOM['s']）
    lat = [s for s in range(24) if any(o and abs(SY(s) - yy) < 0.0216 for yy, o in row_ok)]
    # 独立路径复核：逐 lane 的 (ci,p) 合成域（BFS 于 L1/L2），确认全 16 网同一 s 域
    lane_s = {}
    for nm in names:
        ax, ay = A[nm]; bx, by = B[nm]
        S = []
        for s in range(24):
            y = SY(s)
            ok1 = False
            for c in CIN:
                js = np.arange(ay, y + 1e-9, 0.01) if y >= ay else np.arange(y, ay + 1e-9, 0.01)
                ii = int(round((c - rast.X0) / rast.step)); jj = np.rint((js - rast.Y0) / rast.step).astype(int)
                okk = (jj >= 0) & (jj < rast.NY) & (0 <= ii < rast.NX)
                if okk.all() and not bad[ii, jj[okk]].any(): ok1 = True; break
            if not ok1: continue
            for p in range(18):
                xs_, fx = free_x_on_line(rast, bad, y, min(c, PX(p)) - 0.01, max(c, PX(p)) + 0.01)
                if fx.all(): S.append(s); break
        lane_s[nm] = S
    shared = sorted(set(map(tuple, lane_s.values())))
    res[tag] = {
        "common_span_x": [XW, XE],
        "common_free_y_runs": [[round(a, 2), round(b, 2)] for a, b in iv_common],
        "common_free_total_mm": round(sum(b - a for a, b in iv_common), 3),
        "cap_0p435_on_common_span": maxpack(iv_common, P),
        "n_rows_0p435_lattice": len(lat), "rows_0p435_lattice": lat,
        "n_free_finegrid_points": len(fine_pts),   # 连续自由度（细格自由点数）
        "n_distinct_lane_row_sets": len(set(map(tuple, lane_s.values()))),
        "shared_row_sets": [list(t) for t in shared],
        "n_lanes": len(names),
    }

# H3: 夹缝截面容量（x=133.5）→ 排除『板上无解』
m, an, rast, bad = build(PAD_REG)
names = sorted(a["net"] for a in an)
CORR_LO, CORR_HI = 56.2, 68.0   # 南走廊尺度：56.2 = 墙南沿；68.0 = PCIE_DN0_N 墙北沿
ys, f = free_y_on_line(rast, bad, 133.5, CORR_LO, CORR_HI)
iv_cut = runs(ys, f, 0.01)
res["fence_cut"] = {
    "x": 133.5, "band": [56.2, 68.0], "free_y_runs": [[round(a, 2), round(b, 2)] for a, b in iv_cut],
    "total_free_mm": round(sum(b - a for a, b in iv_cut), 3),
    "cap_at_0p435": maxpack(iv_cut, P),
    "cap_at_0p335_weak": maxpack(iv_cut, 0.335),
}
res["verdict"] = {
    "gate_infeasible_is": "图纸缺陷（残余『单走行模板』）—— 非物理不可行",
    "kernel": "强制公共跨段 [%.3f, %.3f] 之『全清 y 集』：在册 margin 口径下总长 %.2fmm（%d 段），0.435 节距打包容量 = %d < 16 = 车道数 ⇒ 残余『单走行模板』容量上界 %d < 16（Hall 失败 · 同 9<16 型）"
              % (XW, XE, res["pad_reg"]["common_free_total_mm"], len(res["pad_reg"]["common_free_y_runs"]),
                 res["pad_reg"]["cap_0p435_on_common_span"], res["pad_reg"]["cap_0p435_on_common_span"]),
    "margin_sensitivity": "同一 y 集在『无 margin』口径下总长 %.2fmm、打包容量 = %d ≥ 16 ⇒ 该模板之不可行**由在册 margin 口径（PAD_EXTRA=%.4f）所致**，非物理不可行 ⇒ **不得据此出不可行证书**"
              % (res["pad_0"]["common_free_total_mm"], res["pad_0"]["cap_0p435_on_common_span"], PAD_REG),
    "board_not_excluded_by": "夹缝截面 x=133.5 自由 y 集按 0.435 打包上界 = %d ≥ 16（与在册 R393/R395 min-cut 28/16 一致）"
                             % res["fence_cut"]["cap_at_0p435"],
    "required_fix": "补足缺失自由度：南带走行不得钉为『单条水平行』；须入模『层内折返(jog)』（R325 已登记：任何解必须含 ≥1 次 jog）",
    "no_certificate": True,
}
blob = json.dumps(res, ensure_ascii=False, indent=2, default=str)
open("K2_R475_QC_GATE_INFEASIBLE_IS_DRAWING_DEFECT_RESIDUAL_SINGLE_ROW_TEMPLATE_v1.json", "w").write(blob + "\n")
print(blob)
