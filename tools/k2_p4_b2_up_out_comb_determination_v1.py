#!/usr/bin/env python3
"""K2 · R272 —— ②-UP **组合判定**（精确枚举 · 只读 · 零搜索 · 零重跑布线器）

任务（handoff R271 §7.2 / #K2-132 §四）：在 **8 个东组事件的横截跨越容量约束 + 列序约束**下，
求**最大可共存子集 U** 与**具名豁免集（16 − U 网）**。

模型（#K2-132 §七 物理口径为准）：
  ① 列序被迫 = reverse(A 落线序)（单层不可交叉 + A 落线序固定 + 南通道嵌套 U 返）
  ② 每个东组事件 e@(x_B,y_B)：其停靠铜占走廊 [x_B−KE, x_B+KE]，KE=0.5300（物理）
  ③ 跨越者 = {8 西组} ∪ {东组 y_B < y_e}（承 R271 §方法）
  ④ 按列序被走廊切成西/东两组，各组条数 ≤ 该侧「共同自由容量」
     —— **共同自由** = In5 在 y∈[y_B, 56.0] 上的**交集**（固定列位模型：列须全高可用），
        按 0.435 节距计列数（本件对 R271 之「全局带 [135.92,142.67]」做了逐事件收紧）
  ⑤ 子集 S：豁免网不入通道（旧路在 In2/B.Cu · 不阻 In5）⇒ 既不计入跨越者、亦无走廊

方法：对全部 2^16 子集**精确枚举**（组合判定 · 非扫描 · 非启发式 · 非布通率）。

复现（两步 · 全只读）：
  $ AppDir/usr/bin/python3.11 k2/tools/k2_p4_b2_board_in5_model_dump_v1.py k2/hw/k2_v4_8L.l8.kicad_pcb /tmp/opencode/archer/model_l8.json
  $ python3 k2/tools/k2_p4_b2_up_out_comb_determination_v1.py /tmp/opencode/archer/model_l8.json
退出码 0 = U_max == 12（与 R271 上界一致）；1 = 不一致（须报）。
"""
import json, math, sys, itertools
import numpy as np

PITCH   = 0.435
KE      = 0.5300          # 物理锚净距（= hw 0.08 + 0.35 + margin 0.100 · 在册）
EDGE_CLR= 0.300
HW      = 0.080
EFF     = 0.175
F_Y0    = 52.85           # 东通道底带南界
F_Y1    = 56.00
CH_XLO  = 134.00


def lane_anchors(model):
    LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
    seen = {}
    for v in model["vias"]:
        if v["net"] in LANES:
            seen.setdefault(v["net"], {})["%s-%s" % (v["top"], v["bot"])] = (v["x"], v["y"])
    out = {}
    for nm, d in seen.items():
        out[nm] = {"A": d["F.Cu-B.Cu"], "B": d["F.Cu-In2.Cu"]}
    return out


def drop_order(anch):
    NX = sorted(anch[f"PCIE_UP_OUT{i}_N_J2"]["A"][0] for i in range(8))
    dx = {}
    for i in range(8):
        dx[f"PCIE_UP_OUT{i}_N_J2"] = NX[i]
    for i in range(7):
        dx[f"PCIE_UP_OUT{i}_P_J2"] = (NX[i] + NX[i + 1]) / 2.0
    dx["PCIE_UP_OUT7_P_J2"] = 93.70
    return dict(sorted(dx.items(), key=lambda kv: kv[1]))


def common_free(model, y0, y1, x0, x1, step=0.02):
    L = "In5.Cu"
    xs = np.arange(x0, x1 + 1e-9, step)
    ys = np.arange(y0, y1 + 1e-9, step)
    ok = np.ones((len(xs),), dtype=bool)
    for y in ys:
        block = np.zeros((len(xs),), dtype=bool)
        for s in model["segs"][L]:
            ax, ay, bx, by, w, net = s
            rad = HW + w + EFF
            if min(ax, bx) - rad - step > x1 or max(ax, bx) + rad + step < x0: continue
            if min(ay, by) - rad - step > y or max(ay, by) + rad + step < y: continue
            ddx, ddy = bx - ax, by - ay; l2 = ddx * ddx + ddy * ddy
            t = 0.0 if l2 == 0 else np.clip(((xs - ax) * ddx + (y - ay) * ddy) / l2, 0, 1)
            block |= np.hypot(xs - (ax + t * ddx), y - (ay + t * ddy)) < rad
        for v in model["vias"]:
            if L not in v["layers"]: continue
            if abs(v["y"] - y) > 1.0: continue
            rad = HW + max(v["r"] + EFF, v["drill"] + 0.25)
            block |= np.hypot(xs - v["x"], y - v["y"]) < rad
        for p in model["pads"]:
            if L not in p["layers"] and not p["pth"]: continue
            bx0, by0, bx1, by1 = p["box"]
            rad = HW + EFF
            if by0 - rad - step > y or by1 + rad + step < y: continue
            ddx = np.maximum(np.maximum(bx0 - xs, 0), xs - bx1)
            ddy = np.maximum(np.maximum(by0 - y, 0), y - by1)
            block |= np.hypot(ddx, ddy) < rad
        ok &= ~block
    bands, cur = [], None
    for x, f in zip(xs, ok):
        if f and cur is None: cur = x
        if not f and cur is not None: bands.append((float(cur), float(x))); cur = None
    if cur is not None: bands.append((float(cur), float(xs[-1])))
    return bands


def main():
    m = json.load(open(sys.argv[1], "rb"))
    anch = lane_anchors(m)
    drop = drop_order(anch)
    order = list(reversed(list(drop)))                      # 通道列序 西→东（被迫）
    LANES = list(drop)                                      # 16
    xhi = m["bbox"][2] - EDGE_CLR - HW
    EAST = [n for n in LANES if anch[n]["B"][0] >= 135.40]
    WEST = [n for n in LANES if anch[n]["B"][0] < 135.40]

    def cap(lo, hi):
        hi = min(hi, xhi)
        return 0 if hi < lo else int(math.floor((hi - lo) / PITCH + 1e-9)) + 1

    CAP = {}
    BANDS = {}
    for n in EAST:
        yb = anch[n]["B"][1]; xb = anch[n]["B"][0]
        bands = [(a, b) for a, b in common_free(m, yb, F_Y1, CH_XLO, m["bbox"][2] - 0.001) if b > CH_XLO]
        cw, ce = xb - KE, xb + KE
        w = sum(cap(max(a, CH_XLO), min(b, cw)) for a, b in bands if a < cw)
        e = sum(cap(max(a, ce), b) for a, b in bands if b > ce)
        CAP[n] = (w, e); BANDS[n] = [(round(a, 3), round(b, 3)) for a, b in bands]

    def check(S):
        Ss = set(S); o = [n for n in order if n in Ss]; r = {n: i for i, n in enumerate(o)}
        for e in EAST:
            if e not in Ss: continue
            ye = anch[e]["B"][1]
            cors = [j for j in Ss if j != e and (j in WEST or anch[j]["B"][1] < ye - 1e-9)]
            w = sum(1 for j in cors if r[j] < r[e])
            ea = sum(1 for j in cors if r[j] > r[e])
            wc, ec = CAP[e]
            if w > wc or ea > ec:
                return False
        return True

    # 全 16 的逐事件读数（须与 R271 表一致）
    ev_rows = []
    for e in sorted(EAST, key=lambda n: -anch[n]["B"][1]):
        ye = anch[e]["B"][1]
        cors = [j for j in LANES if j != e and (j in WEST or anch[j]["B"][1] < ye - 1e-9)]
        rr = {n: i for i, n in enumerate(order)}
        w = sum(1 for j in cors if rr[j] < rr[e]); ea = sum(1 for j in cors if rr[j] > rr[e])
        wc, ec = CAP[e]
        ev_rows.append({"event": e, "xB": anch[e]["B"][0], "yB": ye, "col": rr[e] + 1,
                        "west_need": w, "west_cap": wc, "east_need": ea, "east_cap": ec,
                        "violation": [w - wc, ea - ec]})

    best, exsets = -1, set()
    for mask in range(1 << 16):
        S = [LANES[i] for i in range(16) if mask >> i & 1]
        if len(S) < best: continue
        if check(S):
            if len(S) > best: best = len(S); exsets = set()
            exsets.add(tuple(sorted(n for n in LANES if n not in S)))

    out = {
        "tool": "k2_p4_b2_up_out_comb_determination_v1",
        "caliber": {"keepout_physical": KE, "pitch": PITCH, "edge_clr": EDGE_CLR,
                    "lane_fixed_column": True, "free_y_span": [F_Y0, F_Y1],
                    "free_x_lo": CH_XLO, "x_center_hi": round(xhi, 4)},
        "forced_col_order_west_to_east": order,
        "east_group": EAST, "west_group": WEST,
        "per_event_capacity": {n: CAP[n] for n in EAST},
        "per_event_free_bands": BANDS,
        "full16_event_table": ev_rows,
        "full16_feasible": check(LANES),
        "U_max": best,
        "n_max_exemption_sets": len(exsets),
        "max_exemption_sets": [list(s) for s in sorted(exsets)],
    }
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    print("\n[VERDICT] U_max = %d (期望 12) ; 全16可行=%s ; 最大豁免集数=%d => %s"
          % (best, check(LANES), len(exsets), "HOLDS" if best == 12 else "MISMATCH"))
    sys.exit(0 if best == 12 else 1)


if __name__ == "__main__":
    main()
