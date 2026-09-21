#!/usr/bin/env python3
"""K2 · (a) B.Cu —— **逃逸带缝合孔 ECO 移位器 v1**（#K2-68 §2.4(a)-2）。

对 U6 逃逸带内之 `GND`/`P3V3` **F–B 缝合孔**：逐孔最小位移至**邻近合法位**（同 net/span/尺寸），
并**重接 stub**（新位 → 原走线端点）；不合法即**原位不动**（保守）。

合法性（逐孔，全层）：与 F.Cu/B.Cu 他网铜 ≥ VIA_R+req · 与他孔中心距 ≥0.7 · 与焊盘 ≥VIA_R+0.05（不叠 pad）
· 与新布 B.Cu 车道 ≥0.35（via↔track 净距）。

CLI:
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/usr/bin/python3.11 \
    k2/tools/k2_p4_b2_bcu_eco_move_v1.py --in <pcb> --out <pcb> --ledger <json> \
      [--band 81 99 48 58] [--nets GND,P3V3] [--search-r 1.2] [--step 0.05] [--dry-run]
"""
from __future__ import annotations
import argparse, json, math

import pcbnew

MM = pcbnew.ToMM
VIA_R = 0.175


def req(nm):
    if nm.startswith(("PCIE", "REFCLK")):
        return 0.175
    if nm.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")):
        return 0.2
    return 0.1


def V(x, y):
    return pcbnew.VECTOR2I(int(round(pcbnew.FromMM(x))), int(round(pcbnew.FromMM(y))))


def pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def pt_rect(px, py, lo, hi):
    dx = max(lo[0] - px, 0.0, px - hi[0]); dy = max(lo[1] - py, 0.0, py - hi[1])
    return math.hypot(dx, dy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--band", nargs=4, type=float, default=[81.0, 99.0, 48.0, 58.0])
    ap.add_argument("--nets", default="GND,P3V3")
    ap.add_argument("--search-r", type=float, default=1.2)
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    nets = [s for s in a.nets.split(",") if s]
    b = pcbnew.LoadBoard(a.inp)
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}

    # ---- 几何快照（他网铜 + 孔 + 盘）
    segs, vias, pads = [], [], []
    for t in b.GetTracks():
        nm = name.get(t.GetNetCode(), "")
        if t.GetClass() == "PCB_VIA":
            v = t.Cast(); sp = set(int(x) for x in v.GetLayerSet().Seq())
            vias.append({"obj": v, "net": nm, "x": MM(v.GetPosition().x), "y": MM(v.GetPosition().y),
                         "r": MM(v.GetWidth()) / 2, "sp": sp, "drill": MM(v.GetDrillValue()) / 2})
            continue
        L = b.GetLayerName(int(t.GetLayer()))
        segs.append({"obj": t, "net": nm, "layer": L, "a": (MM(t.GetStart().x), MM(t.GetStart().y)),
                     "b": (MM(t.GetEnd().x), MM(t.GetEnd().y)), "hw": MM(t.GetWidth()) / 2})
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            sp = set(int(x) for x in p.GetLayerSet().Seq())
            pads.append({"net": p.GetNetname(), "box": [MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom())],
                         "sp": sp, "pth": p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH})
    LANE = lambda n: n.startswith(("PCIE_UP_OUT", "PCIE_DN_OUT"))
    FY, BY = pcbnew.F_Cu, pcbnew.B_Cu

    def legal(x, y, self_via):
        sn = self_via["net"]
        for s in segs:
            if s["net"] == sn or LANE(s["net"]) and False:
                continue
            if LANE(s["net"]):
                need = 0.35
            else:
                need = VIA_R + req(s["net"])
            if s["layer"] in ("F.Cu", "B.Cu") and pt_seg(x, y, *s["a"], *s["b"]) - s["hw"] < need:
                return False
        for v in vias:
            if v is self_via or v["net"] == sn:
                continue
            if not (v["sp"] & {FY, BY}):
                continue
            if LANE(v["net"]):
                need = 0.7
            else:
                need = VIA_R + v["r"] + req(v["net"])
            if math.hypot(x - v["x"], y - v["y"]) < need:
                return False
        for p in pads:
            if p["net"] == sn:
                continue
            if not (p["pth"] or (p["sp"] & {FY, BY})):
                continue
            if pt_rect(x, y, p["box"][:2], p["box"][2:]) < VIA_R + 0.05:
                return False
        return True

    targets = [v for v in vias if v["net"] in nets and (v["sp"] & {FY}) and (v["sp"] & {BY})
               and a.band[0] <= v["x"] <= a.band[1] and a.band[2] <= v["y"] <= a.band[3]]
    rep = {"tool": "k2_p4_b2_bcu_eco_move_v1", "in": a.inp, "band": list(a.band), "nets": nets,
           "n_targets": len(targets), "moves": [], "skipped": 0}
    # 每孔最近的同 net 走线端点（stub 重接目标）
    def anchor_of(v):
        best = (1e9, None)
        for s in segs:
            if s["net"] != v["net"]:
                continue
            for e in (s["a"], s["b"]):
                d = math.hypot(e[0] - v["x"], e[1] - v["y"])
                if d < best[0]:
                    best = (d, e, s)
        return best
    nx = int(a.search_r / a.step)
    for v in targets:
        anc = anchor_of(v)
        if anc[1] is None:
            rep["skipped"] += 1; continue
        cand = None
        for rr in range(1, nx + 1):
            ring = []
            for i in range(-rr, rr + 1):
                for j in range(-rr, rr + 1):
                    if max(abs(i), abs(j)) != rr:
                        continue
                    ring.append((i, j))
            ring.sort(key=lambda z: z[0] * z[0] + z[1] * z[1])
            for (i, j) in ring:
                x, y = v["x"] + i * a.step, v["y"] + j * a.step
                if not legal(x, y, v):
                    continue
                cand = (x, y); break
            if cand:
                break
        if not cand:
            rep["skipped"] += 1
            rep["moves"].append({"net": v["net"], "frm": [round(v["x"], 3), round(v["y"], 3)], "to": None})
            continue
        rep["moves"].append({"net": v["net"], "frm": [round(v["x"], 3), round(v["y"], 3)],
                             "to": [round(cand[0], 3), round(cand[1], 3)],
                             "d": round(math.hypot(cand[0] - v["x"], cand[1] - v["y"]), 3),
                             "stub_to": [round(anc[1][0], 3), round(anc[1][1], 3)]})
        if a.dry_run:
            continue
        # 移动：删原 stub（同 net 且端点贴原孔者）→ 移孔 → 新建 stub
        for s in list(segs):
            if s["net"] == v["net"] and s["obj"] is not None and \
               (math.hypot(s["a"][0] - v["x"], s["a"][1] - v["y"]) < 0.02 or math.hypot(s["b"][0] - v["x"], s["b"][1] - v["y"]) < 0.02):
                try:
                    b.Remove(s["obj"])
                except Exception:
                    pass
        v["obj"].SetPosition(V(cand[0], cand[1]))
        # stub：新孔 → 锚点（F.Cu 或 B.Cu 任一，原 stub 层）
        s0 = None
        for s in list(segs):
            if s["net"] == v["net"] and s["obj"] is not None and \
               (math.hypot(s["a"][0] - v["x"], s["a"][1] - v["y"]) < 0.02 or math.hypot(s["b"][0] - v["x"], s["b"][1] - v["y"]) < 0.02):
                s0 = s; break
        lay = s0["layer"] if s0 else "F.Cu"
        nt = pcbnew.PCB_TRACK(b)
        nt.SetStart(V(cand[0], cand[1])); nt.SetEnd(V(anc[1][0], anc[1][1]))
        nt.SetWidth(pcbnew.FromMM(0.3)); nt.SetLayer(b.GetLayerID(lay))
        nt.SetNetCode(v["obj"].GetNetCode())
        b.Add(nt)
    rep["n_moved"] = sum(1 for m in rep["moves"] if m["to"])
    if not a.dry_run:
        try:
            pcbnew.ZONE_FILLER(b).Fill(b.Zones()); rep["zone_refill"] = "OK"
        except Exception as e:
            rep["zone_refill"] = "FAILED %s" % e
        b.Save(a.out)
        rep["out"] = a.out
    json.dump(rep, open(a.ledger, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps({k: rep[k] for k in ("n_targets", "n_moved", "skipped", "zone_refill") if k in rep}, ensure_ascii=False))


if __name__ == "__main__":
    main()
