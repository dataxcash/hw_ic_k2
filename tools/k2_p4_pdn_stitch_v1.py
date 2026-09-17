#!/usr/bin/env python3
"""K2 P4 · PDN 接线增量 v1 —— 让「承重支路」dangling 过孔与**同网平面/铜**建立第二层连接。

性质：**纯增**（只追加 0/45/90 短线，不改既有铜、不动 L1）；每案「改板 → ZONE_FILLER 重填 →
kicad-cli DRC 复算 → 不合格即回退」，复用 W-7 修复器的 Engine/delta_ok 复算闸。
默认**只写 work-dir**（不碰仓库）。裁定：#K2-20 / 裁定单 §项2（via_dangling 正解 = PDN 增量，L2 自裁域）。

用法：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_pdn_stitch_v1.py \
    --board <board.kicad_pcb> --pro <同目录同名 pro> --kicad-cli AppDir/bin/kicad-cli \
    --work-dir /tmp/opencode/pdn-run [--radius-mm 6] [--vias uuid1,uuid2]
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import k2_p4_w7_repair_v1 as W

NM = 1_000_000
SEED = 20260918
STUB_W = 200_000          # 0.20 mm（与既有电源支路同宽；≥ 合法下限）
MIN_LEG = 50_000          # 单腿 ≥ 0.05 mm（红线）
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
END_TOL = 2_000           # 2 µm：认定「已与该过孔相接」


def cu_layers(bd):
    return list(bd.GetEnabledLayers().CuStack())


def v2(x, y):
    return pcbnew.VECTOR2I(int(round(x)), int(round(y)))


def seg_dist_point(s, e, p):
    """点 p 到线段 s→e 的最短距离（nm）与最近点。"""
    dx, dy = e.x - s.x, e.y - s.y
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(p.x - s.x, p.y - s.y), (s.x, s.y)
    t = ((p.x - s.x) * dx + (p.y - s.y) * dy) / L2
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    qx, qy = s.x + t * dx, s.y + t * dy
    return math.hypot(p.x - qx, p.y - qy), (qx, qy)


def path_2leg(p0, p1):
    """p0→p1 的 ≤2 段路径，每段 0/45/90°；任一段 < MIN_LEG 则返回 None。"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    if dx == 0 and dy == 0:
        return None
    if dx == 0 or dy == 0 or abs(dx) == abs(dy):
        legs = [(p0, p1)]
    else:
        m = min(abs(dx), abs(dy))
        q = (p0[0] + (m if dx > 0 else -m), p0[1] + (m if dy > 0 else -m))
        legs = [(p0, q), (q, p1)]
    out = []
    for a, b in legs:
        if math.hypot(b[0] - a[0], b[1] - a[1]) < MIN_LEG:
            return None
        out.append((a, b))
    return out


def connected_layers(bd, via, cu):
    """该过孔当前已建立连接的铜层集合（几何：同网线段相接 / 落在同网已填平面 / 同网焊盘）。"""
    p, nc = via.GetPosition(), via.GetNetCode()
    out = set()
    for t in bd.GetTracks():
        if W.is_track(t) and t.GetNetCode() == nc and W.seg_touches(t.GetStart(), t.GetEnd(), p):
            out.add(t.GetLayer())
    for z in bd.Zones():
        if z.GetNetCode() != nc or not z.IsFilled():
            continue
        for l in cu:
            try:
                if z.HasFilledPolysForLayer(l) and z.HitTestFilledArea(l, p, 0):
                    out.add(l)
            except Exception:
                pass
    for f in bd.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetCode() != nc:
                continue
            pp = pad.GetPosition()
            if abs(pp.x - p.x) <= END_TOL and abs(pp.y - p.y) <= END_TOL:
                for l in cu:
                    try:
                        if pad.IsOnLayer(l):
                            out.add(l)
                    except Exception:
                        pass
    return out


def zone_ray(bd, netcode, layer, p, rmax):
    """沿 8 向 0/45/90 射线找「首个落在同网已填平面内」的点（单一合法腿）。

    以**整数轴向偏移 a** 步进 ⇒ 交点恒为精确 0/45/90；对角向上真实距离 = a·√2。
    """
    out = []
    zones = [z for z in bd.Zones()
             if z.GetNetCode() == netcode and z.IsFilled() and z.HasFilledPolysForLayer(layer)]
    if not zones:
        return out
    step = 10_000  # 0.01 mm 轴向步长
    for dx, dy in DIRS:
        a = 50_000
        while True:
            dist = a if (dx == 0 or dy == 0) else a * math.sqrt(2)
            if dist > rmax:
                break
            q = (p.x + dx * a, p.y + dy * a)
            hit = False
            for z in zones:
                try:
                    if z.HitTestFilledArea(layer, v2(*q), 0):
                        hit = True
                        break
                except Exception:
                    pass
            if hit:
                out.append((dist, layer, [((p.x, p.y), q)]))
                break
            a += step
    return out


def pdn_candidates(bd, vkey, radius):
    """该过孔的 PDN 接线候选 [(length_nm, layer, legs)]，升序。"""
    via = next((t for t in bd.GetTracks() if W.is_via(t) and W.uid(t) == vkey), None)
    if via is None:
        return [], {}
    p, nc, net = via.GetPosition(), via.GetNetCode(), via.GetNetname()
    p0 = (p.x, p.y)
    cu = cu_layers(bd)
    conn = connected_layers(bd, via, cu)
    cands = []
    for l in cu:
        if l in conn:
            continue                      # 只补「尚未连接的层」
        cands += zone_ray(bd, nc, l, p, radius)
        # 同网线段（最近点）
        for t in bd.GetTracks():
            if not W.is_track(t) or t.GetLayer() != l or t.GetNetCode() != nc:
                continue
            d, q = seg_dist_point(t.GetStart(), t.GetEnd(), p)
            if 0 < d <= radius:
                legs = path_2leg(p0, q)
                if legs:
                    cands.append((sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in legs), l, legs))
        # 同网过孔
        for t in bd.GetTracks():
            if t is via or not W.is_via(t) or t.GetNetCode() != nc:
                continue
            q = t.GetPosition()
            d = math.hypot(q.x - p.x, q.y - p.y)
            if 0 < d <= radius:
                legs = path_2leg(p0, (q.x, q.y))
                if legs:
                    cands.append((sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in legs), l, legs))
        # 同网焊盘（最近点取 bbox 边界）
        for f in bd.GetFootprints():
            for pad in f.Pads():
                if pad.GetNetCode() != nc:
                    continue
                try:
                    if not pad.IsOnLayer(l):
                        continue
                except Exception:
                    continue
                bb = pad.GetBoundingBox()
                qx = min(max(p.x, bb.GetX()), bb.GetX() + bb.GetWidth())
                qy = min(max(p.y, bb.GetY()), bb.GetY() + bb.GetHeight())
                d = math.hypot(qx - p.x, qy - p.y)
                if 0 < d <= radius:
                    legs = path_2leg(p0, (qx, qy))
                    if legs:
                        cands.append((sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in legs), l, legs))
    # 去重 + 升序（同长优先内层平面）
    seen, uniq = set(), []
    for ln, l, legs in sorted(cands, key=lambda z: (z[0], 0 if pcbnew.LayerName(z[1]).startswith("In") else 1)):
        sig = (l, tuple((int(a[0]), int(a[1]), int(b[0]), int(b[1])) for a, b in legs))
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append((ln, l, legs))
    return uniq, {"via": vkey[:8], "net": net, "pos": [p.x, p.y],
                  "connected_layers": [pcbnew.LayerName(x) for x in sorted(conn)]}


def mutate_pdn(vkey, layer, legs, netname):
    def fn(bd, idx2):
        via = next((t for t in bd.GetTracks() if W.is_via(t) and W.uid(t) == vkey), None)
        if via is None:
            raise RuntimeError("via not found")
        ni = bd.FindNet(netname)
        if ni is None:
            raise RuntimeError(f"net not found: {netname}")
        made = []
        for a, b in legs:
            tr = pcbnew.PCB_TRACK(bd)
            tr.SetStart(v2(*a))
            tr.SetEnd(v2(*b))
            tr.SetWidth(STUB_W)
            tr.SetLayer(layer)
            tr.SetNet(ni)
            bd.Add(tr)
            made.append([int(a[0]), int(a[1]), int(b[0]), int(b[1])])
        return {"via": vkey[:8], "net": netname, "layer": pcbnew.LayerName(layer),
                "stub_nm": int(sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in legs)),
                "legs": made}
    return fn


def dangling_keys(rep, bd):
    out = []
    for e in W.vios(rep, {"via_dangling"}):
        for it in e.get("items", []):
            o = None
            try:
                o = next((t for t in bd.GetTracks() if W.uid(t) == it["uuid"]), None)
            except Exception:
                pass
            if o is not None and W.is_via(o):
                out.append(W.uid(o))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--pro", required=True)
    ap.add_argument("--kicad-cli", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--radius-mm", type=float, default=6.0)
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--vias", default=None, help="逗号分隔 uuid 前缀（限缩目标）")
    ap.add_argument("--max-iters", type=int, default=4)
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)

    try:
        pcbnew.KIID.SeedGenerator(SEED)
    except Exception:
        pass
    board_src, pro_src = os.path.abspath(a.board), os.path.abspath(a.pro)
    work = os.path.abspath(a.work_dir)
    os.makedirs(work, exist_ok=True)
    stem = os.path.splitext(os.path.basename(board_src))[0]
    radius = int(a.radius_mm * NM)
    only = [x for x in (a.vias.split(",") if a.vias else []) if x]

    base = W.stage(board_src, pro_src, work, stem)
    probe = os.path.join(work, stem + ".kicad_pro")
    r0 = W.run_drc(a.kicad_cli, base, os.path.join(work, "drc_before.json"))
    eng = W.Engine(a.kicad_cli, work, probe, base, r0)
    rep_out = {"src": {"board": board_src, "board_sha16": W.sha16(board_src),
                       "pro": pro_src, "pro_sha16": W.sha16(pro_src)},
               "radius_mm": a.radius_mm, "stub_w_um": STUB_W // 1000,
               "before": {"counts": W.counts(r0), "unconnected": W.unconn(r0)},
               "accepted": [], "rejected": []}

    for _ in range(a.max_iters):
        bd, idx = W.load_idx(eng.good)
        keys = dangling_keys(eng.rep, bd)
        if only:
            keys = [k for k in keys if any(k.startswith(x) for x in only)]
        if not keys:
            break
        progressed = 0
        for k in keys:
            cands, meta = pdn_candidates(bd, k, radius)
            if not cands:
                rep_out["rejected"].append(dict(meta, rejected=["no-same-net-attach-within-radius"]))
                continue
            okd, last = False, None
            for ln, layer, legs in cands[:a.top]:
                ok, rec = eng.attempt(f"pdn:{k[:8]}:{pcbnew.LayerName(layer)}",
                                      mutate_pdn(k, layer, legs, meta["net"]))
                if ok:
                    rec["variant"] = "pdn-stub"
                    rec["len_um"] = int(round(ln / 1000))
                    rep_out["accepted"].append(rec)
                    progressed += 1
                    okd = True
                    break
                last = rec
            if not okd:
                rep_out["rejected"].append(dict(last or {}, via=k[:8]))
        if progressed == 0:
            break

    final = os.path.join(work, stem + ".pdn-stitched.kicad_pcb")
    out = a.report or os.path.join(work, "pdn_report.json")
    bd, _ = W.load_idx(eng.good)
    W.refill(bd)
    W.save_with_pro(bd, final, probe)
    rf = W.run_drc(a.kicad_cli, final, os.path.join(work, "drc_after.json"))
    rep_out["after"] = {"counts": W.counts(rf), "unconnected": W.unconn(rf),
                        "board": final, "board_sha16": W.sha16(final)}
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep_out, fh, indent=1, ensure_ascii=False)
    print(json.dumps({"before": rep_out["before"], "after": rep_out["after"],
                      "accepted": len(rep_out["accepted"]),
                      "rejected": len(rep_out["rejected"])}, indent=1, ensure_ascii=False))
    for r in rep_out["accepted"]:
        print("  OK", r["via"], r["net"], r["layer"], f"{r.get('len_um')}um", r.get("stub_nm", 0) // 1000, "um")
    for r in rep_out["rejected"]:
        print("  --", r.get("via"), r.get("net"), "|", r.get("rejected", r.get("unsolved")))
    print("report:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
