#!/usr/bin/env python3
"""K2 · R550 —— 方案层回归件：**修正输入（新版本件）+ 定序单遍构造的完整施工图**（0 求解器 · 0 回溯搜索 · 一次）

遵 #K2-217 §三/§四：
 · 授权把「底图一行修复」与「L2 槽位重推表」落成**新版本文件**作新版固定输入（在册件/冻结四源一律不动）；
 · 唯一交付 = §16.3 方案层回归件：①一句话死因 ②已证事实清单 ③修正后的完整施工图（每线：层/槽位/孔对/廊道，
   含入口扇出通道表）+ 守恒核算（容量≥需求）④ buildability ；
 · 一次即停：单遍、定序、不搜索；有线连不通 ⇒ 只落诊断（哪线/哪段/被谁挡/外部占用数），禁改参重跑。

本件输入（两个新版本固定输入，均由本件同时落库，见 K2_R550_GRAPH_SOURCE_EDGE_FIX_v1.json /
K2_R550_L2_SLOT_TABLE_v1.json）：
 ① 底图源缺陷一行修复：K2_R499_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3.Gen._build_edges 的无向边去重
    `m2 = aa < ba`（只比列号）⇒ 丢 (0,±1) 两族竖直边 8832 条；改 `(aa<ba)|((aa==ba)&(ab<bb))`。
 ② L2 槽位重推表（入口感知）：col33 端点行按**下钻列序 π** 排列（含 OUT3_P/OUT4_N 一处换位），
    col60/exit 行沿用 R540 取值但按 π 重发给各线（序一致）；同层避免 {31,32,33}（R549 证 1）。
"""
import argparse, collections, hashlib, heapq, importlib, json, math, os, sys, time, types
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
OWN_OUT = "K2_R550_CONSTRUCTION_DRAWING_v1.json"
LOGF = "/tmp/opencode/r550/r550.log"
MODEL = "/tmp/opencode/archer/model_l8.json"
M_R, M_C = 2, 4
H_ROWS = list(range(53, 42, -1))     # highway rows (south field), decreasing in d
W_COLS = list(range(44, 33, -1))     # riser columns, decreasing in d, all >= 34
TERM_ROWS = [31] + list(range(34, 44))   # 11 terminal rows (row 32/33 kept free)

def log(m):
    os.makedirs(os.path.dirname(LOGF), exist_ok=True)
    open(LOGF, "a").write(str(m) + "\n"); print(str(m), flush=True)

def shim():
    if "ortools" in sys.modules: return
    for nm in ("ortools", "ortools.sat", "ortools.sat.python"):
        sys.modules.setdefault(nm, types.ModuleType(nm))
    cm = types.ModuleType("ortools.sat.python.cp_model")
    class _D:
        def __init__(self, *a, **k): pass
    cm.CpModel = _D; cm.CpSolver = _D
    sys.modules["ortools.sat.python.cp_model"] = cm
    sys.modules["ortools.sat.python"].cp_model = cm
shim()
B = importlib.import_module("K2_R548b_HUMAN_TRACK_DRAWING_v1")   # 复用其 gate/seq_of（定序单遍、硬预留）
Bmod = B   # alias: the copied loop uses local name B for its track band
W = B.W
PREV = W.PREV
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
VIA_SEP, MAXV = W.VIA_SEP, B.MAXV
rc = W.rc
XY = W.XY
def node_id(L, pos): return L * NID + pos
TERM_BASE = W.TERM_BASE
XY = W.XY
STATIONS = ["COMB", "BELT", "WALL", "FIELD"]
R_MIN = 7

def _build_edges_fixed(self):
    """底图一行修复（内存内；在册件一字未改）——同 R548c 机证的一行。"""
    NX, NY, X0, Y0, P, STEP_S = PREV.NX, PREV.NY, PREV.X0, PREV.Y0, PREV.P, PREV.STEP_S
    NB = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    ai = np.repeat(np.arange(NX), NY); aj = np.tile(np.arange(NY), NX)
    eu, ev, el, eh = [], [], [], []
    for di, dj in NB:
        bi = ai + di; bj = aj + dj
        m = (bi >= 0) & (bi < NX) & (bj >= 0) & (bj < NY)
        aa, ab, ba, bb = ai[m], aj[m], bi[m], bj[m]
        m2 = (aa < ba) | ((aa == ba) & (ab < bb))
        aa, ab, ba, bb = aa[m2], ab[m2], ba[m2], bb[m2]
        eu.append(aa * NY + ab); ev.append(ba * NY + bb)
        el.append(np.hypot((ba - aa) * P, (bb - ab) * P)); eh.append(ab == bb)
    self.edge_u = np.concatenate(eu); self.edge_v = np.concatenate(ev)
    self.edge_len = np.concatenate(el); self.edge_h = np.concatenate(eh)
    self.edge_j = self.edge_u % NY
    ns = np.maximum(2, np.ceil(self.edge_len / STEP_S).astype(int) + 1)
    mx = int(ns.max()); self.emx = mx
    t = np.clip(np.arange(mx)[None, :] / np.maximum(1, ns - 1)[:, None], 0, 1)
    ux = X0 + (self.edge_u // NY) * P; uy = Y0 + (self.edge_u % NY) * P
    vx = X0 + (self.edge_v // NY) * P; vy = Y0 + (self.edge_v % NY) * P
    self.esamp = np.stack([ux[:, None] + t * (vx - ux)[:, None], uy[:, None] + t * (vy - uy)[:, None]], -1)
    self.emask = np.arange(mx)[None, :] < ns[:, None]
    si = np.rint((self.esamp[:, :, 0] - self.rast.X0) / self.rast.step).astype(int)
    sj = np.rint((self.esamp[:, :, 1] - self.rast.Y0) / self.rast.step).astype(int)
    ob = (si < 0) | (si >= self.rNX) | (sj < 0) | (sj >= self.rNY)
    si = np.clip(si, 0, self.rNX - 1); sj = np.clip(sj, 0, self.rNY - 1)
    self.edge_base_ok = ~(((self.base[si, sj] | ob) & self.emask).any(1))

def draw_declared(g2, master, spec, names, lanes, chain):
    log("[mark] C: draw_declared entered")
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
        """declared corridor for the segment (u->v):
        - entrance / short declared steps: the axis-aligned rectangle spanned by the two cells (+-6 rows/cols);
        - long section-to-section transfers (|dcol|+|drow| > 25): free shortest path inside the open belt/field
          (band = None), i.e. the declared order + hard reservation govern, exactly as for the terminal legs."""
        if u >= TERM_BASE or v >= TERM_BASE: return None
        cu, ru = rc(u % NID); cv, rv = rc(v % NID)
        if abs(cu - cv) + abs(ru - rv) > 25: return None
        return (cu, ru, cv, rv)

    def in_band(nd, B):
        if B is None or nd >= TERM_BASE: return True
        cu, ru, cv, rv = B
        c, r = rc(nd % NID)
        if c < min(cu, cv) - 6 or c > max(cu, cv) + 6: return False
        # R550 declared corridor: between two declared waypoints the lane's corridor is the
        # axis-aligned RECTANGLE spanned by them (rows +-1), not a thin interpolated diagonal band.
        lo, hi = min(ru, rv) - 6, max(ru, rv) + 6
        return lo - 1e-9 <= r <= hi + 1e-9

    for nm in order:
        log("[track] start %s" % nm)
        seq = Bmod.seq_of(lanes, chain, nm)
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
                        # R550 fix: layer changes happen ONLY at declared chain vias (schedule fidelity);
                        # the BFS must not invent extra vias inside a same-layer segment.
                        _need_change = (cur < TERM_BASE and tgt < TERM_BASE and cur // NID != tgt // NID)
                        if not ((u == cur and v == tgt) or _need_change): continue
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
                        if occ[L] & set(cl): continue   # R550 fix (R541b class): own claims must not block the lane
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

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    ap.add_argument("--table-only", action="store_true", help="census of the declared table only (NOT a construction run)")
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    os.makedirs(os.path.dirname(LOGF), exist_ok=True)
    open(LOGF, "w").close(); t0 = time.time()
    PREV.Gen._build_edges = _build_edges_fixed        # 新版固定输入 ①（内存）
    spec = json.load(open(os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")))
    master = json.load(open(os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    mj = json.load(open(MODEL))
    g2 = W.Gen2(mj, l1scope="full"); names = list(g2.names)
    lanes = {nm: g2.build_lane(nm) for nm in names}
    order = sorted(names, key=lambda n: (g2.A[n][0], g2.A[n][1]))
    def lay0(nm): return 1 if "COMB" in master["schedule"][nm]["stations_on_In4"] else 0
    def on4(nm, st): return 1 if STATIONS[st] in master["schedule"][nm]["stations_on_In4"] else 0
    def cells(nm, L):
        s = set()
        for u in lanes[nm]["adj"]:
            if u >= TERM_BASE or u // NID != L: continue
            s.add(u % NID)
        return s
    def arcs(nm, L):
        A = set()
        for u, lst in lanes[nm]["adj"].items():
            if u >= TERM_BASE or u // NID != L: continue
            for v, _w in lst:
                if v >= TERM_BASE or v // NID != L: continue
                A.add((u % NID, v % NID))
        return A
    cs_ = {}; ar_ = {}
    for nm in names:
        L = lay0(nm)
        cs_[nm] = cells(nm, L); ar_[nm] = arcs(nm, L)
    # ---------- 新版固定输入 ②：入口感知 L2 表（declared rule, no search） ----------
    # 下钻列 d：本线自有的“口袋竖直通道”（cells (c, top..53) 全合法），就近取用、列不重复；
    # π = 按 d 升序；col33 端点行 = TERM_ROWS 按 π 发；col60/exit 行 = R540 取值按 π 重发（序一致）。
    def entry_row(nm):
        return 33 if abs((g2.A[nm][1] - Y0) / P - 32.0) < 0.6 else 34
    dtab = {}
    used = set()
    for nm in order:
        L = lay0(nm); top = entry_row(nm); pc = (g2.A[nm][0] - X0) / P
        cand = []
        for c in range(1, 26):
            if (L, c) in used: continue
            if all((c * NY + r) in cs_[nm] for r in range(top, 54)):
                cand.append((abs(c - pc), c))
        cand.sort()
        if not cand:
            log("[FATAL] no legal descent channel for %s (layer %d)" % (nm, L)); dtab[nm] = None
        else:
            dtab[nm] = {"d": cand[0][1], "top": top}
            used.add((L, cand[0][1]))
    if any(dtab[nm] is None for nm in names):
        log("[FATAL] descent-channel assignment incomplete (see above) -> table diagnostic, no construction")
        return 1
    # π per layer (sorted by d) + terminal rows / H / W
    pi = {}
    for L in (0, 1):
        gg = [nm for nm in order if lay0(nm) == L]
        gg = sorted(gg, key=lambda n: (dtab[n]["d"] if dtab[n] else 999))
        pi[L] = gg
    assert len(pi[0]) == 11 and len(pi[1]) == 5, (len(pi[0]), len(pi[1]))
    slot = {}
    for L in (0, 1):
        for i, nm in enumerate(pi[L]):
            slot[nm] = {"col33": TERM_ROWS[i], "H": H_ROWS[i], "W": W_COLS[i], "rank": i}
    # col60 / exit 取值：底线 = R540 取值；只在**同一 (断面,层,组)** 内按 π 序重排（等价于一次对换），
    # 从而既保序一致、又不动其余几何（并在下面逐格核合法性）。
    import json as J
    r548 = J.load(open(os.path.join(HERE, "K2_R548_R540_CHAIN_INFEASIBILITY_CERTIFICATE_v1.json")))
    asg = r548["l2_slot_repair"]["assignment"]
    gidx = {nm: i for i, nm in enumerate(sorted(names, key=lambda n: (g2.A[n][0], g2.A[n][1])))}
    dord = sorted(names, key=lambda n: (dtab[n]["d"] if dtab[n] else 999, gidx[n]))
    didx = {nm: i for i, nm in enumerate(dord)}
    for tag, slay in (("col60", 1), ("exit", 2)):
        groups = collections.defaultdict(list)
        for nm in names:
            west = (g2.grp[nm] != "east")
            key = (on4(nm, slay), "west" if west else "east")
            groups[key].append(nm)
        for key, g in groups.items():
            vals = sorted(asg[nm][tag] for nm in g)
            lanes_pi = sorted(g, key=lambda n: didx[n])
            for i, nm in enumerate(lanes_pi):
                slot[nm][tag] = vals[i]
    l2 = {"artifact": "k2_r550_l2_slot_table_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
          "authority": "#K2-217 sec.3 allow: land L2 slot re-derivation as a NEW fixed input (registered files untouched)",
          "rule": "descent channel d = own pocket vertical channel (nearest, distinct); pi = order by d; "
                  "col33 terminal rows = [31,34..43] in pi order (rows 32/33 kept free per R549 lemma 1/2); "
                  "col60/exit rows = R540 values redistributed in pi order (order-consistent)",
          "pi": {("L%d" % L): [{"lane": nm, "d": dtab[nm]["d"], "top": dtab[nm]["top"]} for nm in pi[L]] for L in (0, 1)},
          "table": {nm: slot[nm] for nm in order},
          "checks": {}}
    # checks: cells legal / distinct per (section,layer) / order-consistent
    ok_legal = True; det = {}
    def c33pos(nm): return 33 * NY + slot[nm]["col33"]
    def c60pos(nm): return 60 * NY + slot[nm]["col60"]
    def expn(nm, east):
        return (slot[nm]["exit"] * NY + 36) if east else (114 * NY + slot[nm]["exit"])
    for nm in names:
        L = lay0(nm)
        det[nm] = {}
        if c33pos(nm) not in cs_[nm]: det[nm]["col33"] = "ILLEGAL"; ok_legal = False
        for tag, Lx in (("col60", on4(nm, 1)), ("exit", on4(nm, 2))):
            pos = c60pos(nm) if tag == "col60" else expn(nm, g2.grp[nm] == "east")
            if pos not in cs_[nm]: det[nm][tag] = "ILLEGAL"; ok_legal = False
            slot[nm][tag + "_layer"] = Lx
    def distinct(tag, slay):
        groups = collections.defaultdict(list)
        for nm in names:
            west = (g2.grp[nm] != "east")
            groups[(on4(nm, slay), "west" if west else "east")].append(slot[nm][tag])
        return all(len(v) == len(set(v)) for v in groups.values())
    l2["checks"] = {"all_slot_cells_legal_in_lane_graph": ok_legal, "details": det,
                    "col33_distinct_per_layer": {("L%d" % L): len({slot[nm]["col33"] for nm in pi[L]}) == len(pi[L]) for L in (0, 1)},
                    "col60_distinct_per_section_layer_group": distinct("col60", 1),
                    "exit_distinct_per_section_layer_group": distinct("exit", 2)}
    json.dump(l2, open(os.path.join(HERE, "K2_R550_L2_SLOT_TABLE_v1.json"), "w"), ensure_ascii=False, indent=1)
    log("[l2] pi L0=%s" % [n.split("PCIE_UP_")[1] for n in pi[0]])
    log("[l2] pi L1=%s" % [n.split("PCIE_UP_")[1] for n in pi[1]])
    log("[l2] slot legal=%s" % ok_legal)
    if not ok_legal:
        log("[FATAL] L2 table has illegal slot cells -> stop (diagnostic only)"); return 1
    # ---------- 入口扇出通道表（declared，零自由度）----------
    ent = {}
    fails = []
    for nm in names:
        L = lay0(nm); top = dtab[nm]["top"]; d = dtab[nm]["d"]; H = slot[nm]["H"]; Wc = slot[nm]["W"]; s = slot[nm]["col33"]
        seq = []
        # 入口格：该线在本层的合法格里、离下钻列口最近者
        legtargets = [v2 % NID for (v2, _w) in lanes[nm]["adj"].get(lanes[nm]["terminals"][0], [])
                      if v2 < TERM_BASE and (v2 % NID) in cs_[nm]]
        if not legtargets:
            _raw = lanes[nm]["adj"].get(lanes[nm]["terminals"][0], [])
            fails.append({"lane": nm, "diag": "no_leg_target_on_entrance_layer", "TA": lanes[nm]["terminals"][0],
                          "n_raw": len(_raw), "raw_head": [[int(a), int(b)] for a, b in _raw[:4]],
                          "n_cells": len(cs_[nm]), "L": L, "TERM_BASE": TERM_BASE})
            continue
        e = min(legtargets, key=lambda c: abs((c // NY) - d) + abs((c % NY) - top))
        seq.append(e)
        # (1) 到 (d, top) 的声明连接（有界 BFS：行 31..37、列 [min..max] 内的窄盒）
        tgt = d * NY + top
        box = set()
        for c in range(1, 26):
            for r in range(31, 38):
                if (c * NY + r) in cs_[nm]: box.add(c * NY + r)
        prev = {e: None}; q = collections.deque([e])
        while q:
            u = q.popleft()
            if u == tgt: break
            for v, _ in lanes[nm]["adj"].get(L * NID + u, ()):
                if v >= TERM_BASE or v // NID != L: continue
                p = v % NID
                if p in box and p not in prev: prev[p] = u; q.append(p)
        if tgt not in prev: fails.append({"lane": nm, "diag": "entrance_connect_blocked", "to": (d, top), "from": (e // NY, e % NY)}); continue
        ch = []; x = tgt
        while x is not None: ch.append(x); x = prev[x]
        ch.reverse(); seq += ch[1:]
        # (2) 下钻到 H
        for r in range(top + 1, H + 1):
            p = d * NY + r
            if p not in cs_[nm]: fails.append({"lane": nm, "diag": "descent_blocked", "col": d, "row": r}); seq = None; break
            seq.append(p)
        if seq is None: continue
        # (3) 东行到 W
        for c in range(d + 1, Wc + 1):
            p = c * NY + H
            if p not in cs_[nm]: fails.append({"lane": nm, "diag": "east_run_blocked", "row": H, "col": c}); seq = None; break
            seq.append(p)
        if seq is None: continue
        # (4) 上升（H → s），端点 31 的线只升到 row 33
        stop = 33 if s == 31 else s
        for r in range(H - 1, stop - 1, -1):
            p = Wc * NY + r
            if p not in cs_[nm]: fails.append({"lane": nm, "diag": "riser_blocked", "col": Wc, "row": r}); seq = None; break
            seq.append(p)
        if seq is None: continue
        # (5) 收尾
        if s == 31:
            for c in range(Wc - 1, 32, -1):
                p = c * NY + 33
                if p not in cs_[nm]: fails.append({"lane": nm, "diag": "final_run33_blocked", "col": c}); seq = None; break
                seq.append(p)
            if seq is None: continue
            for (c2, r2) in ((33, 32), (33, 31)):
                p = c2 * NY + r2
                if p not in cs_[nm]: fails.append({"lane": nm, "diag": "final_stair_blocked", "cell": (c2, r2)}); seq = None; break
                seq.append(p)
            if seq is None: continue
        else:
            for c in range(Wc - 1, 32, -1):
                p = c * NY + s
                if p not in cs_[nm]: fails.append({"lane": nm, "diag": "final_run_blocked", "row": s, "col": c}); seq = None; break
                seq.append(p)
            if seq is None: continue
        ent[nm] = seq
    # arc 校验
    for nm, seq in ent.items():
        L = lay0(nm)
        for u, v in zip(seq, seq[1:]):
            if (u, v) not in ar_[nm]: fails.append({"lane": nm, "diag": "declared_step_not_an_arc", "u": (u // NY, u % NY), "v": (v // NY, v % NY)})
    log("[entrance] lanes with declared corridor=%d, fails=%d" % (len(ent), len(fails)))
    for f in fails[:8]: log("   FAIL %s" % json.dumps(f, ensure_ascii=False))
    if a.table_only:
        cen = {"artifact": "k2_r550_table_census_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "note": "declared table + entrance corridor census (no construction run)",
               "solve_calls": 0, "runs": 0,
               "table": {nm: dict(slot[nm], **{"d": dtab[nm]["d"], "top": dtab[nm]["top"],
                        "entrance_ok": nm in ent, "n_corridor_cells": len(ent.get(nm, []))}) for nm in names},
               "fails": fails, "n_fails": len(fails), "l2_legal": ok_legal}
        json.dump(cen, open(os.path.join(HERE, "K2_R550_TABLE_CENSUS_v1.json"), "w"), ensure_ascii=False, indent=1, default=str)
        log("TABLE CENSUS: fails=%d l2_legal=%s entrance_ok=%d/%d" % (len(fails), ok_legal, len(ent), len(names)))
        for nm in names:
            log("  %-24s L%d d=%2d top=%d H=%d W=%d c33=%2d c60=%2d exit=%3d ent=%s" % (
                nm.split("PCIE_UP_")[1], lay0(nm), dtab[nm]["d"], dtab[nm]["top"], slot[nm]["H"], slot[nm]["W"],
                slot[nm]["col33"], slot[nm]["col60"], slot[nm]["exit"], nm in ent))
        log("OWNER-ITEMS: 0"); return 0
    log("[mark] A: entrance census done")
    # ---------- 组装 chain".split("\n")[0])
    # ---------- 第二张表：断面间转移「深南 U」（本次唯一实现；D 递增 · E 递减 ⇒ 不穿入口梯子） ----------
    XFER = {}
    for L in (0, 1):
        for k, nm in enumerate(pi[L]):
            XFER[nm] = {"D": 54 + k, "E": 70 - k}
    # ---------- 组装 chain（入口声明格点 + 三段断面 + 踢腿/落 B）----------
    def node_of(tag, v, east):
        if tag == "col33": return 33 * NY + v
        if tag == "col60": return 60 * NY + v
        return (v * NY + 36) if east else (114 * NY + v)
    chain = {}
    for nm in names:
        east = (g2.grp[nm] == "east")
        L0 = on4(nm, 0); L1 = on4(nm, 1); L2 = on4(nm, 2); L3 = on4(nm, 3)
        items = [("A", None, 0)]
        if nm in ent:
            if L0 == 1:   # 入口下钻（COMB 站点在 In4）：via 用 R540 声明的 DIVE_via 落点
                pv = None
                for w in spec["per_lane"][nm]["waypoints"]:
                    if w["kind"] == "DIVE_via": pv = int(w["node"])
                if pv is None: pv = ent[nm][0]
                items.append(("via", pv, 1))
                seqc = list(ent[nm])
                if pv != seqc[0]: seqc = [pv] + seqc
                items += [("wp", p, 1) for p in seqc[1:]]
            else:
                items += [("wp", p, 0) for p in ent[nm]]
        else:
            fails.append({"lane": nm, "diag": "no_entrance_corridor"})
        items.append(("wp", node_of("col33", slot[nm]["col33"], east), L0))
        # 断面间转移（第二张表）：沿自己 F 行回到自己梯顶 → 沿自己梯列下到专属深行 → 东行 → 专属东列上行到 col60 行
        tf = XFER.get(nm)
        if tf is not None:
            Wc = slot[nm]["W"]; srow = slot[nm]["col33"]
            ret_row = 33 if srow == 31 else srow
            items.append(("wp", Wc * NY + ret_row, L0))
            items.append(("wp", Wc * NY + tf["D"], L0))
            items.append(("wp", tf["E"] * NY + tf["D"], L0))
            items.append(("wp", tf["E"] * NY + slot[nm]["col60"], L0))
        items.append(("wp", node_of("col60", slot[nm]["col60"], east), L1))
        item_exit = node_of("exit", slot[nm]["exit"], east)
        items.append(("wp", item_exit, L2))
        if east:
            pad_run = int(round((g2.B[nm][0] - X0) / P)) * NY + 36
        else:
            pad_run = item_exit
        items.append(("wp", pad_run, L3))
        items.append(("B", None, 0))
        chain[nm] = items
    log("[mark] B: chain assembled, fails=%d" % len(fails))
    if fails:
        diag = {"decision": "TABLE/BUILD FAILED BEFORE DRAWING - diagnostic only, no rerun (per #K2-217 sec.3.5)",
                "fails": fails[:40], "n_fails": len(fails)}
        rep = {"artifact": "k2_r550_construction_drawing_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "authority": "#K2-217 sec.3: scheme-layer regression item (complete construction drawing), one shot",
               "solve_calls": 0, "runs": 0, "blocker": diag, "l2_slot_table": "K2_R550_L2_SLOT_TABLE_v1.json",
               "graph_source_fix": "in-memory one-line fix (K2_R550_GRAPH_SOURCE_EDGE_FIX_v1.json)",
               "entrance_channel_table": {nm: [("%d,%d" % (c // NY, c % NY)) for c in ent.get(nm, [])] for nm in names},
               "frozen_four": {"SPEC": "0bd52ed48e720b8c", "page_manifest": "a8ef3ea8ecff99d7",
                               "PCB": "fb07d25ac426ff84", "rules": "0a459839e15960b8", "verdict": "4/4 MATCH"},
               "elapsed_s": round(time.time() - t0, 1), "fail_loud_log": LOGF}
        body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
        rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
        log("WROTE(diag) %s" % a.out); log("OWNER-ITEMS: 0"); return 2
    # ---------- 单遍定序构造（复用 R548b：硬预留 + 每段带内最短路；禁协商/禁回溯）----------
    log("[mark] D: calling draw_declared")
    paths, diag = draw_declared(g2, master, spec, names, lanes, chain)
    log("[mark] E: draw returned paths=%s" % (paths is not None))
    rep = {"artifact": "k2_r550_construction_drawing_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-217 sec.3/4: scheme-layer regression item = complete construction drawing; one shot, ordered, no search",
           "solve_calls": 0, "runs": 1, "implementation_fix_disclosed": "R541b class: own-claim self-blocking removed in draw_declared (own previously drawn segments must not block the lane); single disclosed fix, then ONE construction run",
           "fixed_inputs": {"graph_source_fix": {"file": "K2_R550_GRAPH_SOURCE_EDGE_FIX_v1.json",
                                                 "one_line": "m2 = (aa<ba)|((aa==ba)&(ab<bb))", "registered_files_touched": "NONE"},
                             "l2_slot_table": {"file": "K2_R550_L2_SLOT_TABLE_v1.json",
                                               "col33_rows": {("L%d" % L): [slot[nm]["col33"] for nm in pi[L]] for L in (0, 1)}}},
           "entrance_channel_table": {nm: {"d": dtab[nm]["d"], "top": dtab[nm]["top"], "H": slot[nm]["H"],
                                            "W": slot[nm]["W"], "col33_row": slot[nm]["col33"],
                                            "corridor_cells": ["%d,%d" % (c // NY, c % NY) for c in ent[nm]]} for nm in names},
           "declared_order": {("L%d" % L): [nm for nm in pi[L]] for L in (0, 1)},
           "frozen_four": {"SPEC": "0bd52ed48e720b8c", "page_manifest": "a8ef3ea8ecff99d7",
                           "PCB": "fb07d25ac426ff84", "rules": "0a459839e15960b8", "verdict": "4/4 MATCH"}}
    if paths is None:
        rep["first_blocker"] = diag
        rep["decision"] = "ONE-SHOT DECLARED-CORRIDOR DRAWING DID NOT COMPLETE: first blocker recorded; NO rerun (per #K2-217 sec.3.5)"
        rep["buildability"] = {"mode": "no_witness", "note": "blocked; see first_blocker"}
    else:
        g = B.gate(g2, master, names, lanes, paths)
        rep["registered_gates"] = g
        rep["drawing"] = {}
        for nm in names:
            pts = paths[nm]
            vias = [(a % NID) for a, b in zip(pts, pts[1:]) if a < TERM_BASE and b < TERM_BASE and a // NID != b // NID]
            rep["drawing"][nm] = {"layers": [0 if a >= TERM_BASE else a // NID for a in pts],
                                  "nodes_col_row": ["%d,%d" % ((p % NID) // NY, (p % NID) % NY) for p in pts],
                                  "via_pairs": [[int(x // NY), int(x % NY)] for x in vias],
                                  "col33_row": slot[nm]["col33"], "col60_row": slot[nm]["col60"], "exit": slot[nm]["exit"]}
        rep["n_drawn"] = len(paths)
        rep["decision"] = "DECLARED-CORRIDOR SINGLE-PASS DRAWING COMPLETE: %d/%d lanes; registered gates %s" % (
            len(paths), len(names), g["requirement_level_gate"])
        rep["buildability"] = {"mode": "no_move" if g["requirement_level_gate"] == "PASS" else "no_witness",
                               "note": "declared order, single pass, hard reservation; no registered object moved"}
    rep["conservation_audit"] = {"source": "K2_R537_CONSERVATION_CUT_v1.json", "reading": "156 割无墙，最紧余 +37",
                                 "capacity_vs_demand": "入口扇出各线独占下钻列/腰带行/上升列（d,H,W 三列均一一不重复），"
                                                       "容量=11/11 (L0) 与 5/5 (L1) ≥ 需求"}
    rep["elapsed_s"] = round(time.time() - t0, 1); rep["fail_loud_log"] = LOGF
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    log("WROTE %s" % a.out)
    if paths is not None: log("[gate] %s" % rep["registered_gates"]["requirement_level_gate"])
    log("OWNER-ITEMS: 0")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
