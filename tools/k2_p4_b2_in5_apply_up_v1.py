#!/usr/bin/env python3
"""K2 · UP_OUT 批 In5 套用器（#K2-73 §七-2 · **仅 PCIE_UP_OUT** · DN_OUT 零改动）。
六步：①删 In2–In5 孔与该网 In2/B.Cu/旧 In5 腿 ②A 孔移新锚位 + span F–In5 ③B 孔同位换 span F–In5
④F.Cu 扇出重布（旧 A 孔位→新 A 孔 · 子步骤 F 之简化段）⑤铺新 In5 折线 ⑥ZONE_FILLER。
只读输入：工作令 JSON + A 笼 JSON。不改冻结四源。
"""
import argparse, json, math
import pcbnew
MM = pcbnew.ToMM
PFX = "PCIE_UP_OUT"
W_IN5 = 0.16
W_FCU = 0.205

def V(x, y): return pcbnew.VECTOR2I(int(round(pcbnew.FromMM(x))), int(round(pcbnew.FromMM(y))))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--workorder", required=True)
    ap.add_argument("--a-sites", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    wo = json.load(open(a.workorder)); routes = wo["routes"]
    A = json.load(open(a.a_sites))
    b = pcbnew.LoadBoard(a.inp)
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    code = {v: k for k, v in name.items()}
    MID = {b.GetLayerID("In2.Cu"), b.GetLayerID("B.Cu"), b.GetLayerID("In5.Cu")}
    per = {}
    for t in b.GetTracks():
        nm = name.get(t.GetNetCode(), "")
        if not nm.startswith(PFX):
            continue
        d = per.setdefault(nm, {"vias": {}, "trk": []})
        if t.GetClass() == "PCB_VIA":
            v = t.Cast()
            d["vias"]["%s-%s" % (b.GetLayerName(int(v.TopLayer())), b.GetLayerName(int(v.BottomLayer())))] = v
        else:
            d["trk"].append(t)
    rep = {"in": a.inp, "workorder": a.workorder, "a_sites": a.a_sites, "n_up": len(per),
           "del_vias": 0, "del_mid_tracks": 0, "moved_A": 0, "swap_B": 0, "add_runs": 0, "add_stub_fcu": 0}
    plan = []
    for nm, d in per.items():
        if nm not in routes or nm not in A:
            continue
        vA = d["vias"].get("F.Cu-B.Cu")          # A 侧（U6 侧）
        vB = d["vias"].get("F.Cu-In2.Cu")        # B 侧（J2 侧）
        dels = [d["vias"][k] for k in ("In2.Cu-In5.Cu", "In5.Cu-B.Cu") if k in d["vias"]]
        plan.append((nm, vA, vB, dels, [t for t in d["trk"] if int(t.GetLayer()) in MID]))
    rep["del_vias"] = sum(len(p[3]) for p in plan)
    rep["del_mid_tracks"] = sum(len(p[4]) for p in plan)
    rep["moved_A"] = sum(1 for p in plan if p[1]); rep["swap_B"] = sum(1 for p in plan if p[2])
    if a.dry_run:
        print(json.dumps(rep, ensure_ascii=False, indent=1)); return
    for nm, vA, vB, dels, trk in plan:
        newA = A[nm]
        if vA:
            old = (MM(vA.GetPosition().x), MM(vA.GetPosition().y))
            vA.SetPosition(V(newA[0], newA[1])); vA.SetLayerPair(pcbnew.F_Cu, pcbnew.In5_Cu)
            if math.hypot(old[0]-newA[0], old[1]-newA[1]) > 1e-6:   # 子步骤 F（简化：旧 A 位 → 新 A 位）
                s = pcbnew.PCB_TRACK(b); s.SetStart(V(*old)); s.SetEnd(V(newA[0], newA[1]))
                s.SetWidth(pcbnew.FromMM(W_FCU)); s.SetLayer(b.GetLayerID("F.Cu")); s.SetNetCode(code[nm])
                b.Add(s); rep["add_stub_fcu"] += 1
        if vB: vB.SetLayerPair(pcbnew.F_Cu, pcbnew.In5_Cu)
        for v in dels: b.Remove(v)
        for t in trk: b.Remove(t)
        pts = [(float(p[0]), float(p[1])) for p in routes[nm]["pts"]]
        bid = b.GetLayerID("In5.Cu")
        for k in range(len(pts)-1):
            s = pcbnew.PCB_TRACK(b); s.SetStart(V(*pts[k])); s.SetEnd(V(*pts[k+1]))
            s.SetWidth(pcbnew.FromMM(W_IN5)); s.SetLayer(bid); s.SetNetCode(code[nm]); b.Add(s); rep["add_runs"] += 1
    try:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones()); rep["zone_refill"] = "OK"
    except Exception as e:
        rep["zone_refill"] = "FAILED: %s" % e
    b.Save(a.out); rep["out"] = a.out
    if a.ledger: json.dump(rep, open(a.ledger, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps(rep, ensure_ascii=False))

if __name__ == "__main__":
    main()
