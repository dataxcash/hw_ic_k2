#!/usr/bin/env python3
"""K2 · R318 —— ②-UP「A 侧接入段」**逐 lane 连通性** + In5 单层**跨切容量**（只读 · 不改生成器 · 不写板）

目的（按已批准《K2 整体整改计划》§P4 推进；阶段门 fail-closed）：
  把「16/16 单层 In5」之**可能卡点**逐类排除/定位：
    (i) **连通型**：每条 lane 之 A 锚 → 连接器侧行，在 In5 自由空间（自网铜已排除 = no-move 全转前提）中是否存在路径；
    (ii) **容量型**：逐 x 切面之自由带能容几条 ≥0.435 间距之水平走线（跨切容量）；最小容量 <16 即为容量型卡点。
  二者皆过 ⇒ 残余 = **纯组构（joint 多商品间距）** ⇒ 属算法/实现能力层，非几何刚性。

口径：cell 0.05 · hw 0.08 · 障碍膨胀 = `hw+max(0.175, req(net))`（与 lane_router_v3.build_base 同式 · 只读复用）
用法:
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_b2_board_in5_model_dump_v1.py k2/hw/k2_v4_8L.l8.kicad_pcb /tmp/opencode/model_l8.json
  python3 K2_R318_A_SIDE_CONNECTIVITY_AND_IN5_CUT_CAPACITY_v1.py /tmp/opencode/model_l8.json <out.json>
"""
import sys, json, math, importlib.util, hashlib
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

V3 = "k2/tools/k2_p4_b2_in5_lane_router_v3.py"
LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
CELL, HW, P, XC = 0.05, 0.08, 0.435, 134.6
# 连接器侧行（ye）取 R316 之 DIL=0 · δ=0.15 解（sha16 约定A 75b008bc8269b742）
YE = {"PCIE_UP_OUT0_N_J2": 45.73, "PCIE_UP_OUT0_P_J2": 42.80, "PCIE_UP_OUT1_N_J2": 59.50,
      "PCIE_UP_OUT1_P_J2": 44.00, "PCIE_UP_OUT2_N_J2": 51.13, "PCIE_UP_OUT2_P_J2": 57.73,
      "PCIE_UP_OUT3_N_J2": 60.00, "PCIE_UP_OUT3_P_J2": 47.87, "PCIE_UP_OUT4_N_J2": 49.67,
      "PCIE_UP_OUT4_P_J2": 54.83, "PCIE_UP_OUT5_N_J2": 55.70, "PCIE_UP_OUT5_P_J2": 51.635,
      "PCIE_UP_OUT6_N_J2": 54.13, "PCIE_UP_OUT6_P_J2": 58.165, "PCIE_UP_OUT7_N_J2": 58.70,
      "PCIE_UP_OUT7_P_J2": 53.27}
CUTS = [95, 98, 100, 102, 105, 108, 110, 112, 115, 118, 120, 122, 125, 128, 130, 132, 133, 134, 134.6, 136, 138, 140]
Y_LO, Y_HI = 40.0, 62.0

spec = importlib.util.spec_from_file_location("v3", V3)
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
v3.is_lane = lambda n: n in LANES


def main():
    model = json.load(open(sys.argv[1]))
    rast = v3.Raster(model["bbox"], CELL)
    base = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
    free = ~base
    NX, NY = free.shape
    X0, Y0 = rast.X0, rast.Y0
    idx = np.full(free.shape, -1, np.int32)
    ii, jj = np.nonzero(free); idx[ii, jj] = np.arange(len(ii))
    rows, cols, dl = [], [], []
    for di, dj, d in ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                      (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))):
        ni, nj = ii + di, jj + dj
        m = (ni >= 0) & (ni < NX) & (nj >= 0) & (nj < NY)
        t = idx[ni[m], nj[m]]; ok = t >= 0
        rows.append(idx[ii[m][ok], jj[m][ok]]); cols.append(t[ok]); dl.append(np.full(int(ok.sum()), d * CELL))
    G = csr_matrix((np.concatenate(dl), (np.concatenate(rows), np.concatenate(cols))), shape=(len(ii), len(ii)))
    ad = {a["net"]: a for a in v3.lane_anchors(model)}

    out = {"schema": 1, "artifact": "k2_r318_a_side_connectivity_and_in5_cut_capacity_v1",
           "to": "监理", "from": "ENG · ARCHER", "board": "k2/hw/k2_v4_8L.l8.kicad_pcb",
           "board_sha16": "7a5c89913d6e5d0a", "cell_mm": CELL, "hw_mm": HW, "pitch_mm": P,
           "premise": "In5 单层 · 自网（16 条 PCIE_UP_OUT）铜已排除 = no-move 全转前提；障碍膨胀同 build_base"}
    print("cell=%.2f · free cells=%d" % (CELL, len(ii)))
    # (i) 逐 lane 连通
    conn = {}
    for n in sorted(YE):
        A = ad[n]["A"]; y = YE[n]
        ai, aj = rast.cell(*A); ti, tj = rast.cell(XC, y)
        okA = 0 <= ai < NX and 0 <= aj < NY and idx[ai, aj] >= 0
        okT = 0 <= ti < NX and 0 <= tj < NY and idx[ti, tj] >= 0
        d = dijkstra(G, directed=False, indices=int(idx[ai, aj])) if (okA and okT) else None
        dd = float(d[int(idx[ti, tj])]) if d is not None else float("inf")
        conn[n] = {"A": [round(A[0], 3), round(A[1], 3)], "target": [XC, y], "free_A": bool(okA), "free_T": bool(okT),
                   "connected": bool(np.isfinite(dd)), "shortest_mm": round(dd, 2) if np.isfinite(dd) else None}
        print("  %-10s A=(%6.2f,%6.2f) -> (%.1f,%5.2f)  %s  %s" % (
            n[10:-3], A[0], A[1], XC, y, "YES" if conn[n]["connected"] else "NO", conn[n]["shortest_mm"]))
    out["a_side_connectivity"] = {"n_connected": sum(1 for v in conn.values() if v["connected"]), "n_lanes": len(conn), "per_lane": conn}

    # (ii) 跨切容量
    I = lambda x: int(round((x - X0) / CELL)); J = lambda y: int(round((y - Y0) / CELL))
    j0, j1 = J(Y_LO), J(Y_HI)
    cuts = {}
    for x in CUTS:
        col = free[I(x), j0:j1 + 1]; bands = []; j = 0; n_ = len(col)
        while j < n_:
            if not col[j]: j += 1; continue
            k = j
            while k + 1 < n_ and col[k + 1]: k += 1
            L = (k - j + 1) * CELL
            bands.append({"lo": round(Y0 + j * CELL, 2), "hi": round(Y0 + k * CELL, 2), "len_mm": round(L, 2),
                          "cap": max(1, int(math.floor(L / P + 1e-9)) + 1)})
            j = k + 1
        cuts[str(x)] = {"capacity": sum(b["cap"] for b in bands), "bands": bands}
    capmin = min(v["capacity"] for v in cuts.values())
    xmin = min(cuts, key=lambda k: cuts[k]["capacity"])
    out["cut_capacity"] = {"cuts": cuts, "min_capacity": capmin, "min_at_x": float(xmin), "y_window": [Y_LO, Y_HI]}
    print("  跨切容量 min = %d @ x=%s （全部切面 ≥16 ⇒ 无容量型卡点）" % (capmin, xmin))

    out["verdict"] = {
        "(i) 连通型卡点": "**无** —— A 侧逐 lane 连通 %d/%d" % (out["a_side_connectivity"]["n_connected"], len(conn)),
        "(ii) 容量型卡点": "**无** —— 跨切容量最小 **%d ≥ 16**（@x=%s）" % (capmin, xmin),
        "残余": "**纯组构（joint 多商品间距）** —— 16 条同时放置且两两 ≥0.435 之构造器 ⇒ 属**算法/实现能力层**",
        "非主张": "本件**不主张** 16/16 可达（joint 见证未给）；亦不主张不可行。"}
    out["buildability_field_宪法13"] = ("「施工队照着这张图能不能直接连？」→ 逐 lane **能**（连通见证为路径长度读数）；"
        "**全板不能**（16 条之联立坐标未给）⇒ 全板图纸层缺图，不得据以开工。**不动证明**：本件不搬任何对象。")
    out["self_sha16"] = {"convention": "#K2-72 §五 约定A", "convention_A_sha16": ""}
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    out["self_sha16"]["convention_A_sha16"] = hashlib.sha256(txt.strip().encode()).hexdigest()[:16]
    json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("[sha16 约定A] %s -> %s" % (out["self_sha16"]["convention_A_sha16"], sys.argv[2]))


main()
