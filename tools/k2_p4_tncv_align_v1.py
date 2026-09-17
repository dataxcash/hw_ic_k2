#!/usr/bin/env python3
"""K2 P4 · tncv 对齐增量 v1 —— 清除 `track_not_centered_on_via` 残项（L2：布线/过孔策略，纯几何对齐）。

原理：违规 = 「走线端点不在过孔中心」。合法修法只有两种，且都必须保持 **0/45/90°** 与 **单腿 ≥0.05 mm**：
  ① **膝点重接**（过孔不动）：把违规走线的近端沿其**原直线**移到膝点 K，再新增一段 过孔→K；
  ② **移孔 + 全量重接**：过孔移到 V'（≤0.25 mm 网格搜索），把**所有接在该孔上的走线**各自重接到 V'。
逐案「改板 → ZONE_FILLER 重填 → kicad-cli DRC 复算 → 不合格即回退」（复用 W-7 `delta_ok`）。默认只写 work-dir。

用法：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_tncv_align_v1.py \
    --board <b.kicad_pcb> --pro <同名 pro> --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/tncv-run
"""
import argparse
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import k2_p4_w7_repair_v1 as W

NM = 1_000_000
SEED = 20260918
MIN_LEG = 50_000                 # 单腿下限（红线 0.05 mm）
END_TOL = 2_000
MAX_SHIFT = 250_000              # 移孔上限（nm）
STEP = 5_000                     # 网格步长（nm）
MAX_TRIALS = 24                  # 每孔最多试投候选数
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def v2(x, y):
    return pcbnew.VECTOR2I(int(round(x)), int(round(y)))


def dpt(a, b):
    return math.hypot(a.x - b[0], a.y - b[1])


def knee(V, P, Q):
    """V→P' 单腿 0/45/90 且 |VP'|≥MIN_LEG，P' 在 P→Q 直线上且保留段 ≥MIN_LEG。

    返回 (leg_nm, P'_tuple)；P'==V 时返回 (0.0, None)（该走线已正对，无需动作）。
    """
    if V[0] == P.x and V[1] == P.y:
        return 0.0, None
    dx, dy = Q.x - P.x, Q.y - P.y
    L = math.hypot(dx, dy)
    if L == 0:
        return None
    best = None
    for ax, ay in DIRS:
        b0, b1 = P.x - V[0], P.y - V[1]
        D = -ax * dy + dx * ay
        if D == 0:
            continue
        t = (-b0 * dy + dx * b1) / D
        s = (ax * b1 - b0 * ay) / D
        if t <= 0:
            continue
        leg = abs(t) * math.hypot(ax, ay)
        rem = L * (1.0 - s)
        if leg >= MIN_LEG - 1 and s <= 1.0 and rem >= MIN_LEG - 1:
            cand = (leg, (int(round(V[0] + ax * t)), int(round(V[1] + ay * t))))
            if best is None or cand[0] < best[0]:
                best = cand
    return best


def offenders(rep, bd):
    """{via_uuid: {'via':via, 'off':[tracks]}}（来自 DRC 的 tncv 违规项）。"""
    tr = {W.uid(t): t for t in bd.GetTracks()}
    out = collections.OrderedDict()
    for v in W.vios(rep, {"track_not_centered_on_via"}):
        via, tk = None, None
        for it in v.get("items", []):
            o = tr.get(it["uuid"])
            if o is None:
                continue
            if W.is_via(o):
                via = o
            elif W.is_track(o):
                tk = o
        if via is None or tk is None:
            continue
        g = out.setdefault(W.uid(via), {"via": via, "off": []})
        if W.uid(tk) not in [W.uid(x) for x in g["off"]]:
            g["off"].append(tk)
    return out


def touching(bd, via, extra=()):
    """所有「接在该孔上」的同网走线（端点落在孔铜内 / 穿过孔心）+ 违规走线。"""
    p, nc = via.GetPosition(), via.GetNetCode()
    out = []
    for t in bd.GetTracks():
        if not W.is_track(t) or t.GetNetCode() != nc:
            continue
        s, e = t.GetStart(), t.GetEnd()
        if (math.hypot(s.x - p.x, s.y - p.y) <= END_TOL
                or math.hypot(e.x - p.x, e.y - p.y) <= END_TOL
                or W.seg_touches(s, e, p, END_TOL)):
            out.append(t)
    for t in extra:
        if W.uid(t) not in [W.uid(x) for x in out]:
            out.append(t)
    return out


def plan_for(tracks, V):
    plan = []
    for t in tracks:
        s0, e0 = t.GetStart(), t.GetEnd()
        P = s0 if dpt(s0, V) <= dpt(e0, V) else e0
        Q = e0 if P is s0 else s0
        r = knee(V, P, Q)
        if r is None:
            return None
        plan.append((W.uid(t), "S" if P is s0 else "E", r[1], r[0]))
    return plan


def candidates(bd, vkey, g):
    """按（移孔量升序）返回 [(tag, V', plan)]：先试过孔不动（只重接违规线），再网格移孔。"""
    via = g["via"]
    vp = via.GetPosition()
    out = []
    p0 = plan_for(g["off"], (vp.x, vp.y))
    if p0 is not None:
        out.append(("knee", (vp.x, vp.y), p0))
    tc = touching(bd, via, g["off"])
    grid = []
    for dx in range(-MAX_SHIFT, MAX_SHIFT + 1, STEP):
        for dy in range(-MAX_SHIFT, MAX_SHIFT + 1, STEP):
            if dx == 0 and dy == 0:
                continue
            V = (vp.x + dx, vp.y + dy)
            pl = plan_for(tc, V)
            if pl is not None:
                grid.append((math.hypot(dx, dy), V, pl))
    grid.sort(key=lambda z: (z[0], z[1][0], z[1][1]))
    for ln, V, pl in grid[:MAX_TRIALS]:
        out.append(("move", V, pl))
    return out


def mutate_align(vkey, Vnew, plan, netname):
    def fn(bd, idx2):
        via = next((t for t in bd.GetTracks() if W.is_via(t) and W.uid(t) == vkey), None)
        if via is None:
            raise RuntimeError("via not found")
        ni = bd.FindNet(netname)
        if ni is None:
            raise RuntimeError(f"net not found: {netname}")
        vp = via.GetPosition()
        moved = []
        if (Vnew[0], Vnew[1]) != (vp.x, vp.y):
            via.SetPosition(v2(*Vnew))
            moved = [vp.x, vp.y, Vnew[0], Vnew[1]]
        newsegs = []
        for tkey, side, Pp, leg in plan:
            if Pp is None:
                continue
            tgt = next((t for t in bd.GetTracks() if W.is_track(t) and W.uid(t) == tkey), None)
            if tgt is None:
                raise RuntimeError(f"track gone: {tkey}")
            before = tgt.GetStart() if side == "S" else tgt.GetEnd()
            if side == "S":
                tgt.SetStart(v2(*Pp))
            else:
                tgt.SetEnd(v2(*Pp))
            nt = pcbnew.PCB_TRACK(bd)
            nt.SetStart(v2(*Vnew))
            nt.SetEnd(v2(*Pp))
            nt.SetWidth(tgt.GetWidth())
            nt.SetLayer(tgt.GetLayer())
            nt.SetNet(ni)
            bd.Add(nt)
            newsegs.append({"track": tkey[:8], "side": side, "from": [before.x, before.y],
                            "to": list(Pp), "leg_nm": int(round(leg)),
                            "layer": pcbnew.LayerName(nt.GetLayer())})
        return {"via": vkey[:8], "net": netname, "via_move": moved, "rewired": newsegs}
    return fn


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--pro", required=True)
    ap.add_argument("--kicad-cli", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--vias", default=None)
    ap.add_argument("--max-iters", type=int, default=6)
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
    only = [x for x in (a.vias.split(",") if a.vias else []) if x]

    base = W.stage(board_src, pro_src, work, stem)
    probe = os.path.join(work, stem + ".kicad_pro")
    r0 = W.run_drc(a.kicad_cli, base, os.path.join(work, "drc_before.json"))
    eng = W.Engine(a.kicad_cli, work, probe, base, r0)
    rep_out = {"src": {"board": board_src, "board_sha16": W.sha16(board_src),
                       "pro": pro_src, "pro_sha16": W.sha16(pro_src)},
               "min_leg_um": MIN_LEG // 1000, "max_shift_um": MAX_SHIFT // 1000,
               "before": {"counts": W.counts(r0), "unconnected": W.unconn(r0)},
               "accepted": [], "rejected": []}

    for _ in range(a.max_iters):
        bd, idx = W.load_idx(eng.good)
        gs = offenders(eng.rep, bd)
        keys = [k for k in gs if not only or any(k.startswith(x) for x in only)]
        if not keys:
            break
        progressed = 0
        for k in keys:
            via = gs[k]["via"]
            cands = candidates(bd, k, gs[k])
            if not cands:
                rep_out["rejected"].append({"via": k[:8], "net": via.GetNetname(),
                                            "rejected": ["no-legal-knee/move-candidate"]})
                continue
            okd, last = False, None
            for tag, V, pl in cands:
                ok, rec = eng.attempt(f"tncv:{k[:8]}:{tag}", mutate_align(k, V, pl, via.GetNetname()))
                if ok:
                    rec["variant"] = tag
                    rec["via_shift_um"] = int(round(math.hypot(V[0] - via.GetPosition().x,
                                                               V[1] - via.GetPosition().y) / 1000))
                    rep_out["accepted"].append(rec)
                    progressed += 1
                    okd = True
                    break
                last = rec
            if not okd:
                rep_out["rejected"].append(dict(last or {}, via=k[:8], net=via.GetNetname()))
        if progressed == 0:
            break

    final = os.path.join(work, stem + ".tncv-aligned.kicad_pcb")
    out = a.report or os.path.join(work, "tncv_report.json")
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
        print("  OK", r["via"], r["net"], r["variant"], f"shift={r.get('via_shift_um')}um",
              f"rewired={len(r.get('rewired', []))}",
              "legs_um=" + str([x["leg_nm"] // 1000 for x in r.get("rewired", []) if x.get("leg_nm")]))
    for r in rep_out["rejected"]:
        print("  --", r.get("via"), r.get("net"), "|", r.get("rejected"))
    print("report:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
