#!/usr/bin/env python3
"""K2 · (a) B.Cu 收紧版 —— **套用器**（pcbnew）：把 router 工作令落到板件。

做（确定性 · 逐车道）：
  1. V4（F.Cu–In2.Cu）→ **同位换 span 为 F.Cu–B.Cu**；V1（F.Cu–B.Cu）原地保留；
  2. 删 V2（In5–B）/ V3（In2–In5）及其腿（车道自身 In5 长走 / In2 腿 / 旧 B.Cu 腿）；
  3. 新布 B.Cu 长走（工作令折线）+ **端点 stub**（via ↔ 最近栅格格）；
  4. 铺铜重灌 ZONE_FILLER。
只读输入 = 工作令 JSON（router 产出）。**不改**冻结四源 · 不碰判据/生成器/SPEC。

CLI:
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/usr/bin/python3.11 \
    k2/tools/k2_p4_b2_bcu_apply_v1.py --in <pcb> --workorder <json> --out <pcb> [--ledger <json>] [--dry-run]
"""
from __future__ import annotations
import argparse, json, math

import pcbnew

MM = pcbnew.ToMM
LANE_PREFIX = ("PCIE_UP_OUT", "PCIE_DN_OUT")
B_W = 0.205           # B.Cu 车道线宽（= 探针口径）


def is_lane(nm):
    return nm.startswith(LANE_PREFIX)


def V(x, y):
    return pcbnew.VECTOR2I(int(round(pcbnew.FromMM(x))), int(round(pcbnew.FromMM(y))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--workorder", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    wo = json.load(open(a.workorder))
    routes = wo["routes"]
    b = pcbnew.LoadBoard(a.inp)
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    code = {v: k for k, v in name.items()}
    # 1) 收集车道对象
    track = list(b.GetTracks())
    del_vias, swap_vias, legs = [], [], []
    seen = {}
    for t in track:
        nm = name.get(t.GetNetCode(), "")
        if not is_lane(nm):
            continue
        if t.GetClass() == "PCB_VIA":
            v = t.Cast()
            key = "%s-%s" % (b.GetLayerName(int(v.TopLayer())), b.GetLayerName(int(v.BottomLayer())))
            seen.setdefault(nm, {})[key] = v
        else:
            legs.append(t)
    for nm, d in seen.items():
        if "F.Cu-In2.Cu" in d:
            swap_vias.append((nm, d["F.Cu-In2.Cu"]))
        for k in ("In5.Cu-B.Cu", "In2.Cu-In5.Cu"):
            if k in d:
                del_vias.append((nm, d[k]))
    # **只删中段腿**（B.Cu / In5 / In2）；**保留 F.Cu 扇出**（车道两端 F 侧连接）
    MID = {b.GetLayerID("B.Cu"), b.GetLayerID("In5.Cu"), b.GetLayerID("In2.Cu")}
    del_tracks = [t for t in legs if int(t.GetLayer()) in MID]
    rep = {"in": a.inp, "workorder": a.workorder, "n_lanes": wo["n_lanes"],
           "swap_via_FIn2_to_FB": len(swap_vias), "del_vias": len(del_vias),
           "del_lane_tracks": len(del_tracks), "add_runs": 0, "add_stubs": 0}
    if a.dry_run:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return
    # 2) 换 span + 删
    for nm, v in swap_vias:
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    for nm, v in del_vias:
        b.Remove(v)
    for t in del_tracks:
        b.Remove(t)
    # 3) 新布 B.Cu 长走 + 端点 stub（stub = 原锚位 → 折线首/末点）
    bid = b.GetLayerID("B.Cu")
    for nm, r in routes.items():
        nc = code.get(nm)
        if nc is None:
            continue
        pts = [(float(p[0]), float(p[1])) for p in r["pts"]]
        # 端点 stub：用该车道原 V1/V4 位置接首末点
        d = seen.get(nm, {})
        if "F.Cu-B.Cu" in d:
            v1 = d["F.Cu-B.Cu"]; p1 = (MM(v1.GetPosition().x), MM(v1.GetPosition().y))
            if math.hypot(p1[0] - pts[0][0], p1[1] - pts[0][1]) > 1e-6:
                pts = [p1] + pts; rep["add_stubs"] += 1
        if "F.Cu-In2.Cu" in d:
            v4 = d["F.Cu-In2.Cu"]; p4 = (MM(v4.GetPosition().x), MM(v4.GetPosition().y))
            if math.hypot(p4[0] - pts[-1][0], p4[1] - pts[-1][1]) > 1e-6:
                pts = pts + [p4]; rep["add_stubs"] += 1
        for k in range(len(pts) - 1):
            s = pcbnew.PCB_TRACK(b)
            s.SetStart(V(*pts[k])); s.SetEnd(V(*pts[k + 1]))
            s.SetWidth(pcbnew.FromMM(B_W)); s.SetLayer(bid); s.SetNetCode(nc)
            b.Add(s); rep["add_runs"] += 1
    # 4) 铺铜重灌
    try:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        rep["zone_refill"] = "ZONE_FILLER OK"
    except Exception as e:
        rep["zone_refill"] = "FAILED: %s" % e
    b.Save(a.out)
    rep["out"] = a.out
    if a.ledger:
        json.dump(rep, open(a.ledger, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
