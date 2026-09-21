#!/usr/bin/env python3
"""K2 · B2 —— **逃逸带 GND 缝合孔重布放 v1**（#K2-68 §2.4 (a)-2 / §三-2 In5 路径 ①）。

目的（证据）：B2 ≤2 via/线 之路由净出口受 U6 扇出「锚孔笼」所限。敏感性实测：
  逃逸带 x∈[81,99]·y∈[48,58] 内 **38 个 GND F–B 缝合孔**移出 ⇒ **In5 路径必要通过 25/32 → 32/32**
  （P3V3 缝合孔非主因）；B.Cu 上限仅 30/32。⇒ 本工具执行**真实重布放**（非删除）。

规则：
  · 只动 **GND 网 · F–B 通孔**；他网（含 P3V3 缝合孔 / 车道锚孔 / 走线）**一律不动**。
  · 新位须**全层 span（F,In1..In6,B）净距 + 孔-孔**合规；优先沿 −y（北）/ +y（南）**最邻近合法位**。
  · 保留原孔数与 GND 缝合功能（仍在 U6 区域 GND 铜内）；输出重布放台账 + 密度/覆盖复核数据。

CLI:
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
    k2/tools/k2_p4_b2_relocate_stitch_v1.py --in <pcb> --out <pcb> --ledger <json> \
      [--band x0 x1 y0 y1] [--step 0.10] [--dry-run]
"""
from __future__ import annotations
import argparse, json, math, sys

import pcbnew
MM = pcbnew.ToMM
def V(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

VIA_R = 0.175
HOLE_R = 0.10
REQ = 0.1          # GND vs GND/默认类 净距下限（LOW_SPEED 0.1）
BAND = (81.0, 99.0, 48.0, 58.0)


def cls_req(a, b):
    def c(nm):
        if nm.startswith("PCIE") or nm.startswith("REFCLK"):
            return 0.175
        if nm.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")):
            return 0.2
        return 0.1
    return max(c(a), c(b), 0.1)


def pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def gather(b):
    """逐层障碍：段(含 hw,net)、圆(孔/盘)、矩形(盘)。"""
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    lay_seg, lay_cir, lay_rect, holes = {}, {}, {}, []
    inspan = [b.GetLayerID(x) for x in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu")]
    ls = set(inspan)
    for t in b.GetTracks():
        nm = name.get(t.GetNetCode(), "")
        if t.GetClass() == "PCB_VIA":
            v = t.Cast()
            sp = set(v.GetLayerSet().Seq())
            p = (MM(v.GetPosition().x), MM(v.GetPosition().y))
            w = MM(v.GetWidth()); d = MM(v.GetDrillValue())
            holes.append((p[0], p[1], d / 2.0, nm, sp, "via"))
            if not (sp & ls):
                continue
            for L in (sp & ls):
                lay_cir.setdefault(L, []).append((p[0], p[1], w / 2.0, nm))
            continue
        L = t.GetLayer()
        if L not in ls:
            continue
        lay_seg.setdefault(L, []).append((MM(t.GetStart().x), MM(t.GetStart().y),
                                          MM(t.GetEnd().x), MM(t.GetEnd().y), MM(t.GetWidth()) / 2.0, nm))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            nm = p.GetNetname()
            pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            sp = set(p.GetLayerSet().Seq())
            if not (sp & ls) and not pth:
                continue
            bx = p.GetBoundingBox()
            for L in (sp & ls):
                lay_rect.setdefault(L, []).append((MM(bx.GetX()), MM(bx.GetY()), MM(bx.GetRight()), MM(bx.GetBottom()), nm))
            if pth:
                sz = p.GetDrillSize()
                holes.append((MM(p.GetPosition().x), MM(p.GetPosition().y), MM(sz.x) / 2.0, nm, ls, "pad"))
    return lay_seg, lay_cir, lay_rect, holes


def via_ok(lay_seg, lay_cir, lay_rect, holes, x, y, netname, span_layers, skip_self=None):
    """新孔 (x,y) 在 span_layers 上是否合法（净距 + 孔-孔）。"""
    for L in span_layers:
        for (ax, ay, bx, by, hw, nm) in lay_seg.get(L, ()):  # noqa: E741
            if nm == netname:
                continue
            if pt_seg(x, y, ax, ay, bx, by) - hw < VIA_R + cls_req(netname, nm):
                return False, "seg:%s" % nm
        for (cx, cy, r, nm) in lay_cir.get(L, ()):
            if nm == netname:
                continue
            if math.hypot(x - cx, y - cy) - r < VIA_R + cls_req(netname, nm):
                return False, "via:%s" % nm
        for (x0, y0, x1, y1, nm) in lay_rect.get(L, ()):
            if nm == netname:
                continue
            dx = max(x0 - x, 0.0, x - x1); dy = max(y0 - y, 0.0, y - y1)
            if math.hypot(dx, dy) < VIA_R + cls_req(netname, nm):
                return False, "pad:%s" % nm
    for (hx, hy, hr, nm, sp, kind) in holes:
        if skip_self is not None and (hx, hy) == skip_self:
            continue
        if not (set(span_layers) & set(sp)):
            continue
        if math.hypot(x - hx, y - hy) < HOLE_R + 0.25 + hr:
            return False, "hole:%s" % nm
    return True, ""


def find_spot(lay_seg, lay_cir, lay_rect, holes, x0, y0, span_layers, step=0.1, rmax=40, band=None):
    """由近及远搜合法位（八向环）。"""
    for r in range(0, rmax + 1):
        cand = []
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if max(abs(di), abs(dj)) != r:
                    continue
                x, y = x0 + di * step, y0 + dj * step
                if not (23.5 < x < 142.5 and 33.5 < y < 78.5):
                    continue
                if band and (band[0] <= x <= band[1] and band[2] <= y <= band[3]):
                    continue            # 新位必须**离开**逃逸带
                cand.append((math.hypot(di, dj), x, y))
        cand.sort()
        for _d, x, y in cand:
            ok, _why = via_ok(lay_seg, lay_cir, lay_rect, holes, x, y, "GND", span_layers)
            if ok:
                return x, y
    return None


def run(src, out_path, ledger_path, band, step, dry):
    b = pcbnew.LoadBoard(src)
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    INSPAN = [b.GetLayerID(x) for x in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu")]
    targets = []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        v = t.Cast(); nm = name.get(t.GetNetCode(), "")
        if nm != "GND":
            continue
        x, y = MM(v.GetPosition().x), MM(v.GetPosition().y)
        if not (band[0] <= x <= band[1] and band[2] <= y <= band[3]):
            continue
        if not (int(v.TopLayer()) == F and int(v.BottomLayer()) == B):
            continue
        targets.append((t, x, y))
    led = {"tool": "k2_p4_b2_relocate_stitch_v1", "src": src, "band": list(band),
           "n_candidates": len(targets), "moved": [], "failed": []}
    # 逐个搬：先把原孔移出棋盘语义 = 收集 + 重布放（按离带心远近排序，减小互扰）
    cx = (band[0] + band[1]) / 2.0; cy = (band[2] + band[3]) / 2.0
    targets.sort(key=lambda z: math.hypot(z[1] - cx, z[2] - cy))
    lay_seg, lay_cir, lay_rect, holes = gather(b)
    # 先把目标孔从障碍表里"摘掉"（它们将被移动）
    tgt_xy = {(round(x, 3), round(y, 3)) for _t, x, y in targets}
    for L, lst in lay_cir.items():
        lay_cir[L] = [o for o in lst if not (o[3] == "GND" and (round(o[0], 3), round(o[1], 3)) in tgt_xy)]
    holes = [h for h in holes if not (h[3] == "GND" and (round(h[0], 3), round(h[1], 3)) in tgt_xy)]
    for t, x, y in targets:
        spot = find_spot(lay_seg, lay_cir, lay_rect, holes, x, y, INSPAN, step=step, band=band)
        if spot is None:
            led["failed"].append({"from": [x, y]})
            continue
        nx, ny = spot
        led["moved"].append({"from": [round(x, 3), round(y, 3)], "to": [round(nx, 3), round(ny, 3)],
                             "d_mm": round(math.hypot(nx - x, ny - y), 3)})
        if not dry:
            t.SetPosition(V(nx, ny))
        # 把新孔加入障碍表（后续孔须与之相容）
        lay_cir.setdefault(F, []).append((nx, ny, VIA_R, "GND"))
        lay_cir.setdefault(pcbnew.In1_Cu, []).append((nx, ny, VIA_R, "GND"))
        lay_cir.setdefault(pcbnew.In2_Cu, []).append((nx, ny, VIA_R, "GND"))
        lay_cir.setdefault(pcbnew.In3_Cu, []).append((nx, ny, VIA_R, "GND"))
        lay_cir.setdefault(pcbnew.In4_Cu, []).append((nx, ny, VIA_R, "GND"))
        lay_cir.setdefault(pcbnew.In5_Cu, []).append((nx, ny, VIA_R, "GND"))
        lay_cir.setdefault(pcbnew.In6_Cu, []).append((nx, ny, VIA_R, "GND"))
        lay_cir.setdefault(B, []).append((nx, ny, VIA_R, "GND"))
        holes.append((nx, ny, HOLE_R, "GND", set(INSPAN), "via"))
    led["summary"] = {"candidates": len(targets), "moved": len(led["moved"]), "failed": len(led["failed"]),
                      "max_d_mm": max([m["d_mm"] for m in led["moved"]] or [0])}
    if not dry:
        try:
            pcbnew.ZONE_FILLER(b).Fill(list(b.Zones()))
            led["zone_refilled"] = True
        except Exception as e:  # noqa: BLE001
            led["zone_refilled"] = "ERR:%s" % e
        b.Save(out_path)
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=1, sort_keys=True)
    return led


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="out")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--band", nargs=4, type=float, default=list(BAND))
    ap.add_argument("--step", type=float, default=0.10)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    led = run(a.src, a.out or a.src, a.ledger, a.band, a.step, a.dry_run)
    print(json.dumps(led["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
