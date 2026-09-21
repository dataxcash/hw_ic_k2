#!/usr/bin/env python3
"""K2 · B2 —— 高速车道「≤2 via/线」重迁**可行性探针 v1**（只测量 · 不判定）。

问题定义（#K2-66 §六④ · 强条 R1-5/R5-1 · 见 `docs/K2-66-B2-LANE-VIA-REDUCTION-PLAN-v1.md`）：
  32 条 `PCIE_(UP|DN)_OUT` 数据车道现 = **4 via/线**（路径 F→B→In5[长走]→In2→F）。
  本板换层 span 类 = {F–In2, In2–In5, In5–B}（+F–B 通孔）⇒ 达 ≤2 via 之**唯一结构** =
  中间段**整体置于单一层** L，且两端各 1 个 F→L 孔；L ∈ {In2, B.Cu}（In5 无 F 直接 span）。

本探针只回答**必要条件**（necessary condition，非充分）：
  『在该层 L 上、以**原 A/B 锚点**为端点、且**不移动他网**之前提下，A 与 B 是否处于同一自由连通域？』
  —— 否 ⇒ 该 (车道, L) 组合**不可行**（除非移锚点/移他网/改孔 span 类）。
  是 ⇒ 仍需实际布线验证（充分性另测）。

用法：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
    k2/tools/k2_p4_b2_feasibility_probe_v1.py --board <pcb> --json-out <out.json> [--layer In2.Cu|B.Cu|both]
"""
from __future__ import annotations
import argparse, collections, json, math, sys

import pcbnew

MM = pcbnew.ToMM
F_CU, IN2_CU, B_CU = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
VIA_R = 0.175
STEP = 0.10


def is_lane(nm):
    return nm.startswith("PCIE_UP_OUT") or nm.startswith("PCIE_DN_OUT")


def cls_req(nm):
    if nm.startswith("PCIE") or nm.startswith("REFCLK"):
        return 0.175
    if nm.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")):
        return 0.2
    return 0.1


def pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def pad_dist(px, py, lo, hi):
    dx = max(lo[0] - px, 0.0, px - hi[0]); dy = max(lo[1] - py, 0.0, py - hi[1])
    return math.hypot(dx, dy)


def probe_layer(b, layer_name, lane_w, anchors, lane_nets):
    """返回 {net: {A:cell, B:cell, same_component:bool, compA:int, compB:int}}"""
    lid = b.GetLayerID(layer_name)
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    hw = lane_w / 2.0
    segs, circs, rects, polys = [], [], [], []
    for t in b.GetTracks():
        nm = name.get(t.GetNetCode(), "")
        if is_lane(nm):
            continue                                  # 车道自身在重迁中会被拆
        if t.GetClass() == "PCB_VIA":
            v = t.Cast()
            if lid in set(v.GetLayerSet().Seq()):
                circs.append((MM(v.GetPosition().x), MM(v.GetPosition().y), VIA_R, nm))
            continue
        if b.GetLayerName(t.GetLayer()) != layer_name:
            continue
        segs.append((MM(t.GetStart().x), MM(t.GetStart().y),
                     MM(t.GetEnd().x), MM(t.GetEnd().y), MM(t.GetWidth()) / 2.0, nm))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            nm = p.GetNetname()
            if is_lane(nm):
                continue
            pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            if lid not in set(p.GetLayerSet().Seq()) and not pth:
                continue
            bx = p.GetBoundingBox()
            rects.append((MM(bx.GetX()), MM(bx.GetY()), MM(bx.GetRight()), MM(bx.GetBottom()), nm))
    for z in b.Zones():
        try:
            if not z.GetIsRuleArea() or not z.GetDoNotAllowTracks():
                continue
        except Exception:
            continue
        o = z.Outline()
        for i in range(o.OutlineCount()):
            ch = o.Outline(i)
            polys.append([(MM(ch.CPoint(j).x), MM(ch.CPoint(j).y)) for j in range(ch.PointCount())])

    bb = b.GetBoardEdgesBoundingBox()
    x0, y0 = MM(bb.GetLeft()), MM(bb.GetTop())
    x1, y1 = MM(bb.GetRight()), MM(bb.GetBottom())
    nx = int((x1 - x0) / STEP) + 1
    ny = int((y1 - y0) / STEP) + 1
    bad = bytearray(nx * ny)

    def blend(ax, ay, bx, by, rad):
        i0 = max(0, int((min(ax, bx) - rad - x0) / STEP)); i1 = min(nx - 1, int((max(ax, bx) + rad - x0) / STEP) + 1)
        j0 = max(0, int((min(ay, by) - rad - y0) / STEP)); j1 = min(ny - 1, int((max(ay, by) + rad - y0) / STEP) + 1)
        for i in range(i0, i1 + 1):
            px = x0 + i * STEP
            for j in range(j0, j1 + 1):
                if pt_seg(px, y0 + j * STEP, ax, ay, bx, by) < rad:
                    bad[i * ny + j] = 1

    for (ax, ay, bx, by, shw, nm) in segs:
        blend(ax, ay, bx, by, hw + shw + cls_req(nm))
    for (cx, cy, r, nm) in circs:
        rad = hw + r + cls_req(nm)
        i0 = max(0, int((cx - rad - x0) / STEP)); i1 = min(nx - 1, int((cx + rad - x0) / STEP) + 1)
        j0 = max(0, int((cy - rad - y0) / STEP)); j1 = min(ny - 1, int((cy + rad - y0) / STEP) + 1)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                if math.hypot(x0 + i * STEP - cx, y0 + j * STEP - cy) < rad:
                    bad[i * ny + j] = 1
    for (rx0, ry0, rx1, ry1, nm) in rects:
        rad = hw + cls_req(nm)
        i0 = max(0, int((rx0 - rad - x0) / STEP)); i1 = min(nx - 1, int((rx1 + rad - x0) / STEP) + 1)
        j0 = max(0, int((ry0 - rad - y0) / STEP)); j1 = min(ny - 1, int((ry1 + rad - y0) / STEP) + 1)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                if pad_dist(x0 + i * STEP, y0 + j * STEP, (rx0, ry0), (rx1, ry1)) < rad:
                    bad[i * ny + j] = 1

    def in_poly(px, py, poly):
        ins, n = False, len(poly)
        for i in range(n):
            xa, ya = poly[i]; xb, yb = poly[(i + 1) % n]
            if (ya > py) != (yb > py):
                xx = xa + (py - ya) * (xb - xa) / (yb - ya)
                if px < xx:
                    ins = not ins
        return ins

    for poly in polys:
        xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
        i0 = max(0, int((min(xs) - x0) / STEP)); i1 = min(nx - 1, int((max(xs) - x0) / STEP) + 1)
        j0 = max(0, int((min(ys) - y0) / STEP)); j1 = min(ny - 1, int((max(ys) - y0) / STEP) + 1)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                if in_poly(x0 + i * STEP, y0 + j * STEP, poly):
                    bad[i * ny + j] = 1

    # 车道**他网**锚孔（每车道 A/B 在真实方案中都会是 L 终止孔）—— 计入障碍
    for nm, (A, B) in anchors.items():
        for c in (A, B):
            if c is None:
                continue
            rad = VIA_R + hw + 0.175
            i0 = max(0, int((c[0] - rad - x0) / STEP)); i1 = min(nx - 1, int((c[0] + rad - x0) / STEP) + 1)
            j0 = max(0, int((c[1] - rad - y0) / STEP)); j1 = min(ny - 1, int((c[1] + rad - y0) / STEP) + 1)
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    if math.hypot(x0 + i * STEP - c[0], y0 + j * STEP - c[1]) < rad:
                        bad[i * ny + j] = 1

    out = {}
    for nm in sorted(lane_nets):
        A, B = anchors[nm]
        res = {"A": A, "B": B}
        if A is None or B is None:
            res["status"] = "NO_ANCHOR"
            out[nm] = res
            continue

        def nearest_free(c):
            i0 = int(round((c[0] - x0) / STEP)); j0 = int(round((c[1] - y0) / STEP))
            for r in range(0, 40):
                best = None
                for di in range(-r, r + 1):
                    for dj in range(-r, r + 1):
                        if max(abs(di), abs(dj)) != r:
                            continue
                        i, j = i0 + di, j0 + dj
                        if 0 <= i < nx and 0 <= j < ny and not bad[i * ny + j]:
                            d = math.hypot(di, dj)
                            if best is None or d < best[0]:
                                best = (d, i, j)
                if best is not None:
                    return best
            return None

        sa, sb = nearest_free(A), nearest_free(B)
        if sa is None or sb is None:
            res["status"] = "ANCHOR_IN_WALL"
            out[nm] = res
            continue
        res["A_off_mm"] = round(sa[0] * STEP, 3)
        res["B_off_mm"] = round(sb[0] * STEP, 3)

        def comp(s):
            seen = bytearray(nx * ny)
            q = collections.deque([(s[1], s[2])]); seen[s[1] * ny + s[2]] = 1
            cnt = 0; xs = []; ys = []
            while q:
                i, j = q.popleft(); cnt += 1
                xs.append(x0 + i * STEP); ys.append(y0 + j * STEP)
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < nx and 0 <= nj < ny and not seen[ni * ny + nj] and not bad[ni * ny + nj]:
                        seen[ni * ny + nj] = 1; q.append((ni, nj))
            return cnt, (min(xs), max(xs), min(ys), max(ys)), seen
        ca, bba, seen = comp(sa)
        sb_cell = sa[1], sa[2]
        res["compA_cells"] = ca
        res["compA_bbox"] = [round(v, 2) for v in bba]
        # 仅当 B 与 A 同域时 B 才可达（用 A 的 seen 直接判定）
        same = bool(seen[sb[1] * ny + sb[2]])
        res["same_component"] = same
        if not same:
            cb, bbb, _ = comp(sb)
            res["compB_cells"] = cb
            res["compB_bbox"] = [round(v, 2) for v in bbb]
        res["status"] = "PASS_NECESSARY" if same else "FAIL_NECESSARY"
        out[nm] = res
    return out


def board_span_set(b):
    """自板解析 via span 集（D-1 修正：禁手列）。"""
    import collections as _c
    sp = _c.Counter()
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        v = t.Cast()
        sp[(b.GetLayerName(int(v.TopLayer())), b.GetLayerName(int(v.BottomLayer())))] += 1
    return {"pairs": {"%s-%s" % k: v for k, v in sorted(sp.items(), key=lambda z: -z[1])},
            "total_vias": sum(sp.values())}


def admissible_L(spans, lane_w):
    """由**板实际 span 集**推可达单层 L 集：须存在 F–L 直接 span 且 L 为信号层。"""
    have = set(spans["pairs"])
    return [L for L in ("In2.Cu", "In5.Cu", "B.Cu") if ("F.Cu-%s" % L) in have or ("%s-F.Cu" % L) in have]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--json-out", required=True)
    ap.add_argument("--layer", default="both")
    ap.add_argument("--width", type=float, default=None)
    a = ap.parse_args(argv)
    b = pcbnew.LoadBoard(a.board)
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    anchors = {}
    for t in b.GetTracks():
        nm = name.get(t.GetNetCode(), "")
        if not is_lane(nm) or t.GetClass() != "PCB_VIA":
            continue
        v = t.Cast(); top, bot = int(v.TopLayer()), int(v.BottomLayer())
        p = (MM(v.GetPosition().x), MM(v.GetPosition().y))
        d = anchors.setdefault(nm, {"A": None, "B": None})
        if top == F_CU and bot == B_CU:
            d["A"] = p
        if top == F_CU and bot == IN2_CU:
            d["B"] = p
    lanes = sorted(anchors)
    width = {"In2.Cu": 0.16, "In5.Cu": 0.16, "B.Cu": 0.205}
    layers = ["In2.Cu", "In5.Cu", "B.Cu"] if a.layer == "both" else [a.layer]
    spans = board_span_set(b)
    rep = {"tool": "k2_p4_b2_feasibility_probe_v1", "board": a.board, "step_mm": STEP,
           "span_classes_board_actual": spans, "admissible_L": admissible_L(spans, None),
           "n_lanes": len(lanes), "lanes": {nm: {"A": anchors[nm]["A"], "B": anchors[nm]["B"]} for nm in lanes},
           "layers": {}}
    for L in layers:
        res = probe_layer(b, L, width[L], {k: (v["A"], v["B"]) for k, v in anchors.items()}, lanes)
        ok = [n for n in lanes if res[n].get("same_component")]
        rep["layers"][L] = {
            "width_mm": width[L],
            "pass_necessary": len(ok), "fail_necessary": len(lanes) - len(ok),
            "pass_nets": ok,
            "per_net": res,
        }
        sys.stderr.write("[%s] PASS_necessary=%d/%d\n" % (L, len(ok), len(lanes)))
    with open(a.json_out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps({L: {"pass": rep["layers"][L]["pass_necessary"],
                          "fail": rep["layers"][L]["fail_necessary"]} for L in layers}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
