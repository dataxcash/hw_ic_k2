#!/usr/bin/env python3
"""K2 · R269 —— **②-UP 上界证书 U≤15 之独立复核脚本**（#K2-132 §三.3(b) 要求 · 只读 · 零搜索）

复算对象（件 107e117bbc49d701）：
  ① A 侧落线序（N 自有孔位 + P 缝心/东端）  ⇒ ② 通道列序被迫 = reverse(落线序) ⇒ `7_N` = 第 2 列
  ③ 东组最先停靠 = `7_N`@(136.58,52.85)     ⇒ ④ 底带走廊（锚净距 · 物理 0.53 / 工具 0.43）
  ⑤ In5 底带共同自由（实测）                 ⇒ ⑥ 横截面容量 ⇒ **U ≤ 15**（物理口径）

复现（两步 · 全只读）：
  $ AppDir/usr/bin/python3.11 tools/k2_p4_b2_board_in5_model_dump_v1.py k2/hw/k2_v4_8L.l8.kicad_pcb /tmp/opencode/archer/model_l8.json
  $ python3 tools/k2_p4_b2_up_out_u15_certificate_recheck_v1.py /tmp/opencode/archer/model_l8.json
退出码 0 = 证书成立（U≤15）；1 = 不成立（须撤回证书）。
"""
import json, math, sys
import numpy as np

PITCH   = 0.435
KEEP    = 0.5300            # 物理锚净距（= hw 0.08 + 0.35 + margin 0.100 · 在册）
KEEP_TOOL = 0.4300          # 工具口径（v3.anchor_keepout · 不含余量）
EDGE_CLR  = 0.300           # copper_edge_clearance（模型 design）
HW        = 0.080
KEEPOUT_A = 0.5300          # A 侧球位 keepout（缝枚举用）


def lane_anchors(model):
    """A/F-B 通孔 · B/F-In2 盲孔（与 v3.lane_anchors 同构 · 独立实现）。"""
    LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
    seen = {}
    for v in model["vias"]:
        if v["net"] in LANES:
            seen.setdefault(v["net"], {})["%s-%s" % (v["top"], v["bot"])] = (v["x"], v["y"])
    out = {}
    for nm, d in seen.items():
        a, b = d.get("F.Cu-B.Cu"), d.get("F.Cu-In2.Cu")
        assert a and b, nm
        out[nm] = {"A": a, "B": b}
    return out


def drop_order(anch):
    """A 侧落线 x：N = 自有孔位 x；P = 相邻 N 缝心（i<7），7_P = 东端自由段。"""
    NX = sorted(anch[f"PCIE_UP_OUT{i}_N_J2"]["A"][0] for i in range(8))
    dx = {}
    for i in range(8):
        dx[f"PCIE_UP_OUT{i}_N_J2"] = NX[i]
    for i in range(7):
        dx[f"PCIE_UP_OUT{i}_P_J2"] = (NX[i] + NX[i + 1]) / 2.0
    dx["PCIE_UP_OUT7_P_J2"] = NX[7] + (93.70 - NX[7])   # 东端
    return dict(sorted(dx.items(), key=lambda kv: kv[1])), NX


def common_free(model, y0, y1, x0, x1, step=0.02):
    """In5 在 y∈[y0,y1] 全域共同自由的 x 区间（障碍按 hw+copper+eff(net) 膨胀 · DRC 口径）。"""
    EFF = 0.175
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
    bands = []
    cur = None
    for x, f in zip(xs, ok):
        if f and cur is None: cur = x
        if not f and cur is not None: bands.append((round(cur, 4), round(x, 4))); cur = None
    if cur is not None: bands.append((round(cur, 4), round(float(xs[-1]), 4)))
    return bands


def cap(lo, hi):
    return int(math.floor((hi - lo) / PITCH + 1e-9)) + 1 if hi >= lo else 0


def main():
    m = json.load(open(sys.argv[1], "rb"))
    anch = lane_anchors(m)
    drop, NX = drop_order(anch)
    order = list(reversed(list(drop)))                    # 通道列序 西→东
    i7n = order.index("PCIE_UP_OUT7_N_J2") + 1
    bx, by = anch["PCIE_UP_OUT7_N_J2"]["B"]
    east = {n: a["B"][1] for n, a in anch.items() if a["B"][0] >= 135.40}
    first = max(east, key=lambda n: east[n])
    bbox = m["bbox"]
    y0, y1 = by, 56.0
    bands = common_free(m, y0, y1, 135.0, bbox[2] - 0.001)
    f_lo = max(b[0] for b in bands)
    f_hi = bbox[2] - EDGE_CLR - HW
    out = {"anchor_7N_B": [bx, by], "first_parking": [first, east[first]],
           "col_index_7N": i7n, "forced_col_order": order,
           "band_y": [y0, y1], "free_bands_drc": bands,
           "f_lo_drc": f_lo, "f_hi_center_limit": round(f_hi, 4),
           "board_edge_x": bbox[2], "board_bbox": bbox}
    res = {}
    for name, K, lo, hi in (("physical", KEEP, f_lo + 0.1000, f_hi - 0.1000),
                            ("tool", KEEP_TOOL, f_lo, f_hi)):
        ce = bx + K; cw = bx - K
        west = cap(lo, cw); eastn = cap(ce, hi)
        res[name] = {"keepout": K, "corridor": [round(cw, 4), round(ce, 4)],
                     "region": [round(lo, 4), round(hi, 4)],
                     "west_cap": west, "east_cap": eastn, "total": west + eastn + 1,
                     "U": west + eastn, "need": 16}
    out["capacity"] = res
    out["certificate_U_le_15_physical"] = (res["physical"]["U"] <= 15)
    out["provenance"] = {"PITCH": PITCH, "KEEP": KEEP, "EDGE_CLR": EDGE_CLR, "HW": HW}
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    ok = (i7n == 2 and res["physical"]["U"] <= 15)
    print("\n[VERDICT] 列序被迫(&7_N=第2列)=%s ; 物理口径 U=%d <=15 : %s  => %s"
          % (i7n == 2, res["physical"]["U"], ok, "CERTIFICATE HOLDS" if ok else "CERTIFICATE FAILS"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
