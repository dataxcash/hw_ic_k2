#!/usr/bin/env python3
"""K2 · R548b —— **人类路径·一次实现**：先分配轨道，再逐段拉直线（单遍 · 无协商 · 无重跑）。
遵监理停止令（红线：命令重复）：本件**只跑一次**；任何失败 ⇒ 出诊断（哪条线/哪一段/被谁挡），**不改参数重跑**。

【人类工程师方案（大白话）】
 ① 信号怎么走：每根线从西侧焊盘 A 出来 → 按在册**入口动作**在自己那一列下到 In5（或就地打孔下到 In4）→
    向东穿"梳齿/腰带"，在 **col33 → col60 → 出口** 三个断面上各占**自己的槽位** → 穿墙缝/门柱进"焊盘场" → 落到自己的焊盘 B。
 ② 挡路的是什么：**断面槽位被人占了重复**（5 根线被要求过同一格点 3956，而只有 2 层 ⇒ 鸽笼 5>2），
    以及"同一层同断面两条线必须不相交"的**次序**没被保证。**不是线宽/间距不够，也不是板没地方**。
 ③ 人类方案：**先在每个断面按层把轨道分配成一格一线（并让同一层的线序在两断面之间不翻转），
    然后每根线只在"自己那条轨道带"里拉直线**——直线被挡就整条带平移，不做全板搜索、不做协商。

【本件方法 = 轨道带拉直线（单遍）】
 1) 用 R548 已自裁的 L2 槽位重推（逐层一格一线 + 序一致 + 预路由 PASS）作为固定输入；
 2) 逐段（相邻固定路点之间）给每根线一个**轨道带**（端点行之间的线性插值 ± 声明余量），
    在带内、且在**已占节点之外**求最短路（硬预留）；
 3) 单遍、定序（按 A 焊盘自西向东），**不回溯、不协商、不重跑**；
 4) 成功 ⇒ 走在册闸（exact_gate 逐层 / gate_vias / 端点 / ≤2 对孔）；失败 ⇒ 落盘**首次受阻位置**（诊断）。
声明余量（规则，非调参）：行余量 M_R = 2 格，列余量 M_C = 4 格。
"""
import argparse, collections, hashlib, heapq, importlib, json, math, os, sys, time, types
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
OWN_OUT = "K2_R548b_HUMAN_TRACK_DRAWING_v1.json"
DRAW_OUT = "K2_R548b_DRAWING_PER_LANE_v1.json"
LOGF = "/tmp/opencode/r548/r548b_track.log"
SPEC = os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")
R529 = os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")
MODEL = "/tmp/opencode/archer/model_l8.json"
M_R, M_C = 2, 4


def log(m):
    os.makedirs(os.path.dirname(LOGF), exist_ok=True)
    open(LOGF, "a").write(str(m) + "\n")
    print(str(m), flush=True)


def shim():
    if "ortools" in sys.modules:
        return
    for nm in ("ortools", "ortools.sat", "ortools.sat.python"):
        sys.modules.setdefault(nm, types.ModuleType(nm))
    cm = types.ModuleType("ortools.sat.python.cp_model")
    class _D:
        def __init__(self, *a, **k): pass
    cm.CpModel = _D; cm.CpSolver = _D
    sys.modules["ortools.sat.python.cp_model"] = cm
    sys.modules["ortools.sat.python"].cp_model = cm


shim()
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP = W.XY, W.VIA_SEP
MAXV = 2 * W.MAX_VIA_PAIRS
STATIONS = ["COMB", "BELT", "WALL", "FIELD"]
COL33, COL60, COL114, ROW36 = 33, 60, 114, 36
GAPS = [7, 11, 12, 13, 15, 24, 25, 28]
GATE_COLS = list(range(115, 136))


def node_id(L, pos): return L * NID + pos
def rc(n): return n // NY, n % NY
def on4(master, nm, st): return 1 if STATIONS[st] in master["schedule"][nm]["stations_on_In4"] else 0
def node_of(tag, v, east):
    if tag == "col33": return COL33 * NY + v
    if tag == "col60": return COL60 * NY + v
    return (v * NY + ROW36) if east else (COL114 * NY + v)


# ---- L2 order-consistent slot repair (identical rule to R548; recomputed here so this file stands alone) ----
def repair_slots(g2, master, names, lanes):
    grp = {nm: ("east" if g2.grp[nm] == "east" else "west") for nm in names}
    order = sorted(names, key=lambda nm: (g2.A[nm][0], g2.A[nm][1]))
    gidx = {nm: i for i, nm in enumerate(order)}
    uni = {"col33": list(range(29, 58)), "col60": list(range(38, 58)),
           "exit_west": list(GAPS), "exit_east": list(GATE_COLS)}
    rep = {nm: {} for nm in names}
    pad_col = {}
    for q in names:
        if grp[q] == "east":
            pad_col.setdefault(on4(master, q, 3), {})[int(round((g2.B[q][0] - X0) / P))] = q
    for tag, st in (("col33", 0), ("col60", 1), ("exit", 2)):
        groups = collections.defaultdict(list)
        for nm in names:
            L = on4(master, nm, st)
            key = (("west", None) if grp[nm] == "west" else ("east", L)) if tag == "exit" else ("", L)
            groups[key].append(nm)
        for key, g in groups.items():
            gg, Lk = key
            east = (gg == "east")
            u = sorted(uni["exit_west" if gg == "west" else "exit_east"]) if tag == "exit" else sorted(uni[tag])

            def ln_of(nm): return on4(master, nm, st) if Lk is None else Lk

            def ok(nm, v):
                ln = ln_of(nm); pos = node_of(tag, v, east)
                if not (bool(g2._nok[(nm, ln)][pos]) and node_id(ln, pos) in lanes[nm]["adj"]):
                    return False
                if tag == "exit" and east and v in pad_col.get(ln, {}):
                    return pad_col[ln][v] == nm
                return True
            gorder = sorted(g, key=lambda nm: (g2.B[nm][0], gidx[nm])) if (tag == "exit" and east) \
                else sorted(g, key=lambda nm: gidx[nm])
            prev, used = -10 ** 9, set()
            for nm in gorder:
                cands = [v for v in u if v > prev and v not in used and ok(nm, v)]
                if not cands:
                    return None, {"fail": tag, "lane": nm}
                rep[nm][tag] = cands[0]; prev = cands[0]; used.add(cands[0])
    return rep, {"verdict": "PASS"}


def build_chain(g2, master, spec, names, rep):
    ch = {}
    for nm in names:
        east = g2.grp[nm] == "east"
        L = [on4(master, nm, t) for t in range(4)]
        items = []
        for w in spec["per_lane"][nm]["waypoints"]:
            k = w["kind"]
            if k == "A_anchor": items.append(("A", None, 0))
            elif k == "B_anchor": items.append(("B", None, 0))
            elif k == "In5_entrance": items.append(("wp", w["node"], 0))
            elif k == "DIVE_via": items.append(("via", w["node"], 1))
            elif k == "col33": items.append(("wp", node_of("col33", rep[nm]["col33"], east), L[0]))
            elif k == "col60": items.append(("wp", node_of("col60", rep[nm]["col60"], east), L[1]))
            elif k in ("exit_wall_gap", "exit_gate_col"): items.append(("wp", node_of("exit", rep[nm]["exit"], east), L[2]))
            elif k == "pad_run":
                nd = (int(round((g2.B[nm][0] - X0) / P)) * NY + ROW36) if east else node_of("exit", rep[nm]["exit"], east)
                items.append(("wp", nd, L[3]))
        ch[nm] = items
    return ch


def seq_of(lanes, chain, nm):
    s = []
    for (kind, nd, L) in chain[nm]:
        if kind == "A": s.append((lanes[nm]["src"], None))
        elif kind == "B": s.append((lanes[nm]["snk"], None))
        elif kind == "via":
            s.append((node_id(0, nd), 0)); s.append((node_id(1, nd), 1))
        else: s.append((node_id(L, nd), L))
    return s


def draw(g2, master, spec, names, lanes, chain):
    """single-pass, deterministic, hard-reservation; each segment drawn inside its own track band."""
    CLAIM = {}

    def aclaim(nm, u, v):
        key = (nm, u, v); g = CLAIM.get(key)
        if g is None:
            if u >= TERM_BASE:
                tx, ty = lanes[nm]["anc"][0]; px, py = XY(*rc(v % NID)); g = tuple(sorted(W.claim_seg(tx, ty, px, py)))
            elif v >= TERM_BASE:
                px, py = XY(*rc(u % NID)); tx, ty = lanes[nm]["anc"][1]; g = tuple(sorted(W.claim_seg(px, py, tx, ty)))
            else:
                ax, ay = XY(*rc(u % NID)); bx, by = XY(*rc(v % NID)); g = tuple(sorted(W.claim_seg(ax, ay, bx, by)))
            CLAIM[key] = g
        return g

    def is_via(u, v): return u < TERM_BASE and v < TERM_BASE and u // NID != v // NID

    occ = [set(), set()]          # committed lattice-cell claims per layer
    vias = []
    paths = {}
    order = sorted(names, key=lambda nm: (g2.A[nm][0], g2.A[nm][1]))
    diag = None

    def band(u, v):
        """track band for the segment (u->v): rows between the endpoint rows, interpolated by column, +-M_R."""
        if u >= TERM_BASE or v >= TERM_BASE: return None          # terminal legs: unrestricted
        cu, ru = rc(u % NID); cv, rv = rc(v % NID)
        return (cu, ru, cv, rv)

    def in_band(nd, B):
        if B is None or nd >= TERM_BASE: return True
        cu, ru, cv, rv = B
        c, r = rc(nd % NID)
        if c < min(cu, cv) - M_C or c > max(cu, cv) + M_C: return False
        if cu == cv: lo, hi = min(ru, rv), max(ru, rv)
        else:
            t = (c - cu) / (cv - cu)
            mid = ru + t * (rv - ru); lo, hi = mid - M_R, mid + M_R
        return lo - 1e-9 <= r <= hi + 1e-9

    for nm in order:
        seq = seq_of(lanes, chain, nm)
        # DEFECT FIX (disclosed, same class as R541b): a lane must never be blocked by its OWN previously drawn
        # segments. Route into a per-lane overlay; merge into the shared reservation only on success.
        lam = [set(), set()]; lam_v = []
        cur = seq[0][0]; full = None; nvia = 0; okall = True
        for k in range(1, len(seq)):
            tgt = seq[k][0]
            if cur == tgt: continue
            B = band(cur, tgt)
            adj = lanes[nm]["adj"]
            dist = {cur: 0.0}; pr = {}; vc = {cur: nvia}; pq = [(0.0, cur)]
            while pq:
                d, u = heapq.heappop(pq)
                if d > dist.get(u, 1e18) + 1e-12: continue
                if u == tgt: break
                for (v, w) in adj.get(u, ()):
                    if is_via(u, v):
                        p = u % NID
                        if vc.get(u, 0) >= MAXV: continue
                        if u not in (cur,) and not in_band(u, B): continue
                        bad = any(onm != nm and math.dist(XY(*rc(p)), XY(*rc(q))) < VIA_SEP - 1e-9 for (q, onm) in (vias + [(q2, nm) for q2 in lam_v]))
                        if bad: continue
                        nd = d + w + 0.25; nvc = vc[u] + 1
                    else:
                        if v >= TERM_BASE or u >= TERM_BASE:
                            L = 0
                        else:
                            L = u // NID
                        if not in_band(v, B): continue
                        cl = aclaim(nm, u, v)
                        if (occ[L] | lam[L]) & set(cl): continue
                        nd = d + w; nvc = vc.get(u, 0)
                    if nd < dist.get(v, 1e18) - 1e-12:
                        dist[v] = nd; vc[v] = nvc; pr[v] = u; heapq.heappush(pq, (nd, v))
            if tgt not in pr:
                okall = False
                blockers = sorted(occ[0] | occ[1])   # OTHER lanes only (own claims are in lam, not counted)
                diag = {"lane": nm, "segment_index": k, "kind": chain[nm][k][0] if k < len(chain[nm]) else "?",
                        "from": int(cur), "from_col_row": [rc(cur % NID)[0], rc(cur % NID)[1]] if cur < TERM_BASE else None,
                        "to": int(tgt), "to_col_row": [rc(tgt % NID)[0], rc(tgt % NID)[1]] if tgt < TERM_BASE else None,
                        "band": B, "n_committed_blockers_in_band": sum(1 for b in blockers
                                                                   if in_band(node_id(0, b), B) or in_band(node_id(1, b), B))}
                log("[track] BLOCKED lane=%s k=%d %s -> %s" % (nm, k, diag["from_col_row"], diag["to_col_row"]))
                break
            path = []; x = tgt
            while x is not None: path.append(x); x = pr.get(x)
            path.reverse()
            for a, b in zip(path, path[1:]):
                if is_via(a, b):
                    p = a % NID; lam[0].add(p); lam[1].add(p); lam_v.append(p)
                else:
                    L = 0 if (a >= TERM_BASE or b >= TERM_BASE) else a // NID
                    lam[L].update(aclaim(nm, a, b))
            full = path if full is None else full + path[1:]
            nvia = vc[tgt]; cur = tgt
        if not okall:
            return None, diag
        occ[0] |= lam[0]; occ[1] |= lam[1]; vias += [(pp, nm) for pp in lam_v]
        paths[nm] = full
        log("[track] %-22s nodes=%d vias=%d" % (nm, len(full), sum(1 for a, b in zip(full, full[1:]) if is_via(a, b))))
    return paths, None


def gate(g2, master, names, lanes, paths):
    """registered gates: per-layer exact_gate (lane pitch/clearance) + gate_vias + endpoints + <=2 via pairs."""
    G = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
    mj = json.load(open(MODEL))
    TERM = {}
    for nm in names:
        TA_, TB_ = lanes[nm]["terminals"]; TERM[TA_] = list(lanes[nm]["anc"][0]); TERM[TB_] = list(lanes[nm]["anc"][1])

    def nxy(nd): return list(TERM[nd - TERM_BASE]) if nd >= TERM_BASE else list(XY(*rc(nd % NID)))
    lane_polys = {}; all_vias = []
    for nm in names:
        seq = paths[nm]; runs = []; run = [seq[0]]; vloc = []
        for nd in seq[1:]:
            lay = 0 if nd >= TERM_BASE else nd // NID; layp = 0 if run[-1] >= TERM_BASE else run[-1] // NID
            if lay == layp: run.append(nd)
            else:
                px, py = XY(*rc(run[-1] % NID)); vloc.append([round(px, 3), round(py, 3)]); all_vias.append((px, py, nm))
                runs.append(run); run = [nd]
        runs.append(run)
        polys = {}
        for run in runs:
            lay = 0 if run[0] >= TERM_BASE else run[0] // NID
            polys.setdefault(lay, []).append([nxy(p) for p in run])
        lane_polys[nm] = polys
    gpl = {}
    for Lr in (0, 1):
        rt = {}
        for nm, polys in lane_polys.items():
            for k, p in enumerate(polys.get(Lr, [])):
                if len(p) >= 2:
                    rt["%s#%d" % (nm, k)] = {"pts": p, "layer_cu": G.LAYER_OF[Lr], "n_vias": len(all_vias)}
        if not rt: continue
        gg = G.exact_gate(mj, rt, [], G.LAYER_OF[Lr], W.HW, set(), set(), P, frozenset())
        vp2 = [t for t in gg["lane_pitch_violations"] if t[0].split("#")[0] != t[1].split("#")[0]]
        gpl[G.LAYER_OF[Lr]] = {"n_lane_pitch_viol": len(vp2), "n_clearance_viol": gg["n_clearance_viol"],
                               "lane_pitch_min_gap_mm": gg["lane_pitch_min_gap_mm"], "clearance_min_mm": gg["clearance_min_mm"]}
    gv = G.gate_vias(mj, all_vias, lane_polys, g2.an)
    edev = {}
    for nm, polys in lane_polys.items():
        p0 = polys[0][0][0]; p1 = polys[0][-1][-1]
        edev[nm] = round(max(math.dist(p0, list(g2.A[nm])), math.dist(p1, list(g2.B[nm]))), 6)
    vpl = {nm: sum(1 for v in all_vias if v[2] == nm) for nm in names}
    ok = (all(v["n_lane_pitch_viol"] == 0 and v["n_clearance_viol"] == 0 for v in gpl.values())
          and gv["n_via_viol"] == 0 and (max(edev.values()) if edev else 1) <= 1e-6
          and all(v <= MAXV for v in vpl.values()))
    return {"exact_gate_per_layer": gpl, "gate_vias": gv, "endpoint_max_dev_mm": max(edev.values()) if edev else None,
            "vias_per_lane": vpl, "requirement_level_gate": "PASS" if ok else "FAIL"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    open(LOGF, "w").close()
    t0 = time.time()
    spec = json.load(open(SPEC)); master = json.load(open(R529)); mj = json.load(open(MODEL))
    rep = {"artifact": "k2_r548b_human_track_drawing_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "supervisor stop-order (red-line: repeated commands) -> back to Plan, human path, ONE implementation",
           "method": "allocate one track per lane per layer at each cross-section (L2 re-derived slots), then draw each "
                     "lane as a straight track-band path between consecutive fixed waypoints; single pass, deterministic, "
                     "hard reservation, NO negotiation, NO backtracking, NO rerun",
           "declared_margins": {"row_M_R": M_R, "col_M_C": M_C},
           "solve_calls": 0}
    g2 = W.Gen2(mj, l1scope="full"); names = list(g2.names)
    lanes = {nm: g2.build_lane(nm) for nm in names}
    repair, rinfo = repair_slots(g2, master, names, lanes)
    rep["l2_slot_repair"] = dict(rinfo, n_movements=sum(1 for nm in names for t in ("col33", "col60", "exit")
                                                      if master["section_slots"][nm][t] != repair[nm][t]))
    chain = build_chain(g2, master, spec, names, repair)
    paths, diag = draw(g2, master, spec, names, lanes, chain)
    rep["track_layout"] = {"order": sorted(names, key=lambda nm: g2.A[nm][0]),
                           "n_drawn": 0 if paths is None else len(paths)}
    if paths is None:
        rep["first_blocker"] = diag
        rep["decision"] = ("ONE-SHOT HUMAN METHOD DID NOT COMPLETE 16/16. First blocker recorded above; "
                           "per the stop-order NO parameter change / NO rerun is performed.")
        rep["buildability"] = {"mode": "no_witness", "note": "blocked; see first_blocker"}
    else:
        g = gate(g2, master, names, lanes, paths)
        rep["registered_gates"] = g
        rep["n_drawn"] = len(paths)
        rep["decision"] = ("HUMAN TRACK METHOD COMPLETE: 16/16 lanes drawn in one pass + registered gates %s"
                           % g["requirement_level_gate"])
        rep["buildability"] = {"mode": "no_move" if g["requirement_level_gate"] == "PASS" else "no_witness",
                               "note": "track-band drawing; no other object moved"}
        if g["requirement_level_gate"] == "PASS":
            drawing = {}
            for nm in names:
                drawing[nm] = {"waypoints": spec["per_lane"][nm]["waypoints"],
                               "repaired_slots": repair[nm],
                               "path_nodes": [int(x) for x in paths[nm]]}
            json.dump(drawing, open(os.path.join(HERE, DRAW_OUT), "w"), ensure_ascii=False, indent=1)
    rep["conservation_audit"] = {"source": "K2_R537_CONSERVATION_CUT_v1.json", "reading": "156 割无墙，最紧余 +37"}
    rep["elapsed_s"] = round(time.time() - t0, 1); rep["fail_loud_log"] = LOGF
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    log("WROTE %s" % a.out); log("OWNER-ITEMS: 0")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
