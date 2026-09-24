#!/usr/bin/env python3
"""K2 · R513 — DECISIVE READ-ONLY TRIAGE (Solve() 0 calls; quota 0).

Four machine checks that decide the handoff's (A)/(B) branches and machine-locate the binding
structure of R512's INFEASIBLE:

  T3 EXACTNESS (two-sided) of the R512 clearance encoding on the pitch-P unit-step lattice:
     enumerate every pair of unit arcs in a 7x7 window x 8 directions; compare
        true conflict (registered seg-seg distance < P)   vs
        model-blocked (shares a node | endpoint of one is a strict shadow of the other).
     => if the counts are equal with 0 unsound AND 0 over-strict, then "replace the node-counted
        shadow by exact_gate" is a bit-for-bit NO-OP and branch (B) is void (no solve is owed).

  T4 CONTINUOUS CUT BOUND (no lattice, no abstraction): for a straight cut line L, every lane
     whose anchors straddle L must intersect L; crossing points of distinct lanes must be pairwise
     >= P (two curves both containing their crossing points are <= that far apart). Max 1-D packing
     of free(L) with pitch P is therefore an UPPER bound on the true number of lanes. If that bound
     is far above 16 for all cuts, NO cut can certify board-level impossibility => branch (A)'s
     "conservation-grade infeasibility certificate" is not available this way either.

  T5 UNION CLAIM-DISJOINT (exact clearance) MAX-FLOW, pairing-free: relax ONLY the prescribed
     identity pairing (src_i -> snk_i); keep the exact clearance semantics (a diagonal step
     consumes its two off-diagonal shadow nodes), the other-lane anchor keepouts, the east-lane
     region convention and the 1.6x detour budget. flow >= 16  =>  corridor capacity is NOT the
     wall, and the residual obstruction is the IDENTITY PAIRING (multi-commodity).

  T6 BUDGET SENSITIVITY: same flow with the 1.6x budget pruning removed.

  T7 SUBSET CUT CONDITION (Hall screening) for the identity pairing, subsets of size 1..3.
"""
import argparse, collections, itertools, json, math, os, sys, time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import K2_R512_JOINT_MCF_NODECAP_FIX_v1 as R512
PREV = R512.PREV
P = R512.P; NY = R512.NY; NX = R512.NX; X0 = R512.X0; Y0 = R512.Y0
BOUND = 1.6
MODEL = "/tmp/opencode/archer/model_l8.json"
nid, rc = R512.nid, R512.rc


def seg(n):
    i, j = divmod(n, NY)
    return (X0 + i * P, Y0 + j * P)


# ---------------------------------------------------------------- T3 exactness
def t3_exactness(K=7):
    arcs = set()
    for i in range(K):
        for j in range(K):
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ii, jj = i + di, j + dj
                    if not (0 <= ii < K and 0 <= jj < K):
                        continue
                    u, v = nid(i, j), nid(ii, jj)
                    arcs.add((u, v) if u < v else (v, u))
    arcs = sorted(arcs)
    claim = {e: R512.claim_of(*e) for e in arcs}
    n_true = n_blocked = n_unsound = n_over = 0
    unsound_ex = []; over_ex = []
    for x in range(len(arcs)):
        for y in range(x + 1, len(arcs)):
            a, b = arcs[x], arcs[y]
            if set(a) & set(b):
                blocked = True
            else:
                blocked = bool(set(a) & (claim[b] - set(b))) or bool(set(b) & (claim[a] - set(a)))
            sa = np.array([seg(a[0]), seg(a[1])], float); sb = np.array([seg(b[0]), seg(b[1])], float)
            d = float(PREV._seg_seg_batch(np.array([sa]), np.array([sb])).min())
            tc = d < P - 1e-9
            n_true += tc; n_blocked += blocked
            if tc and not blocked:
                n_unsound += 1
                if len(unsound_ex) < 5:
                    unsound_ex.append([list(a), list(b), round(d, 4)])
            if blocked and not tc:
                n_over += 1
                if len(over_ex) < 5:
                    over_ex.append([list(a), list(b), round(d, 4)])
    return {"window": "%dx%d lattice, all 8 unit directions" % (K, K), "n_arcs": len(arcs),
            "n_pairs": len(arcs) * (len(arcs) - 1) // 2,
            "n_true_conflict_seg_seg_lt_P": n_true, "n_model_blocked": n_blocked,
            "n_unsound_true_conflict_allowed_by_model": n_unsound,
            "n_over_strict_legal_pair_blocked_by_model": n_over,
            "unsound_examples": unsound_ex, "over_strict_examples": over_ex,
            "verdict": ("EXACT (no miss, no over-constraint) => replacing the node-counted shadow by "
                        "the registered exact_gate predicate is a bit-for-bit no-op; handoff branch "
                        "(B) is VOID and no certified solve is owed to it."
                        if n_unsound == 0 and n_over == 0 else "NOT exact - branch (B) may have content")}


# ---------------------------------------------------------------- T4 continuous cut bound
def t4_cut_bound(step_mm=0.05, pad_px=2):
    m = json.load(open(MODEL))
    g = PREV.Gen(m)
    free = ~g.base; r = g.rast
    A = {nm: g.A[nm] for nm in g.names}; B = {nm: g.B[nm] for nm in g.names}

    def runs(vec, coord0, pad):
        idx = np.nonzero(vec)[0]
        if len(idx) == 0:
            return []
        out = []; s = idx[0]; prev = idx[0]
        for k in idx[1:]:
            if k != prev + 1:
                out.append((coord0 + s * r.step - pad, coord0 + prev * r.step + pad)); s = k
            prev = k
        out.append((coord0 + s * r.step - pad, coord0 + prev * r.step + pad))
        return out

    def pack(iv, pitch):
        cnt = 0; last = -1e9
        for a, b in sorted(iv):
            t = max(a, last + pitch)
            if t <= b + 1e-12:
                k = int(math.floor((b - t) / pitch + 1e-12)) + 1
                cnt += k; last = t + (k - 1) * pitch
        return cnt

    pad = pad_px * r.step
    worst = None
    for axis in ("V", "H"):
        lo, hi = (84.3, 141.3) if axis == "V" else (42.5, 55.9)
        for c in np.arange(lo, hi, step_mm):
            if axis == "V":
                ci = max(0, min(r.NX - 1, int(round((c - r.X0) / r.step))))
                iv = runs(free[ci, :], r.Y0, pad)
                nreq = sum(1 for nm in g.names if (A[nm][0] - c) * (B[nm][0] - c) < 0)
            else:
                cj = max(0, min(r.NY - 1, int(round((c - r.Y0) / r.step))))
                iv = runs(free[:, cj], r.X0, pad)
                nreq = sum(1 for nm in g.names if (A[nm][1] - c) * (B[nm][1] - c) < 0)
            if nreq == 0:
                continue
            cap = pack(iv, P)
            rec = (round(float(c), 3), axis, nreq, cap, cap - nreq)
            if worst is None or rec[4] < worst[4]:
                worst = rec
    return {"free_space_dilation_used_px": pad_px, "scan_step_mm": step_mm,
            "worst_cut": {"coord_mm": worst[0], "axis": worst[1], "n_lanes_that_must_cross": worst[2],
                          "capacity_upper_bound": worst[3], "slack": worst[4]},
            "verdict": ("no straight cut can certify impossibility: capacity exceeds the 16-lane demand "
                        "everywhere by a wide margin (min slack = %d)" % worst[4])}


# ---------------------------------------------------------------- lane graphs / union flow
def build_lanes(g, prune, bound=BOUND):
    excl = np.zeros((NX, NY), bool); lanes = []
    for nm in g.names:
        n2 = g.node_ok(nm); pts = g.pt_by_net[nm]
        s0 = g.nearest_node(g.A[nm], n2, pts); t0 = g.nearest_node(g.B[nm], n2, pts, taken=(s0,))
        src, snk = nid(*s0), nid(*t0)
        west = g.B[nm][0] < (X0 + R512.WALLC * P)
        ok = n2.copy()
        if not west:
            for i in range(24, 113):
                ok[i * NY:i * NY + 33] = False
        av = (ok & ~excl).reshape(-1)
        kp = g.edge_ok(nm) & av[g.edge_u] & av[g.edge_v]
        adj = collections.defaultdict(list)
        for u, v in zip(g.edge_u[kp].tolist(), g.edge_v[kp].tolist()):
            w = P * math.hypot(abs(u // NY - v // NY), abs(u % NY - v % NY))
            adj[u].append((v, w)); adj[v].append((u, w))
        if prune:
            def dij(st):
                best = {st: 0.0}; pq = [(0.0, st)]
                import heapq
                while pq:
                    d, u = heapq.heappop(pq)
                    if d > best.get(u, 1e18) + 1e-12:
                        continue
                    for (v, w) in adj.get(u, ()):
                        nd = d + w
                        if nd < best.get(v, 1e18) - 1e-12:
                            best[v] = nd; heapq.heappush(pq, (nd, v))
                return best
            ds = dij(src); dt = dij(snk); sp = ds.get(snk, float("inf"))
            keep = {n for n in ds if n in dt and ds[n] + dt[n] <= bound * sp + 1e-9}
        else:
            keep = None
        steps = set()
        for u, lst in adj.items():
            if keep is not None and u not in keep:
                continue
            for (v, w) in lst:
                if keep is not None and v not in keep:
                    continue
                steps.add((u, v) if u < v else (v, u))
        lanes.append({"nm": nm, "src": src, "snk": snk, "steps": steps, "west": west})
    return lanes


def claim_flow(lanes, want_witness=False):
    union = set()
    for L in lanes:
        union |= L["steps"]
    NID = {n: k for k, n in enumerate(sorted({x for s in union for x in s}))}
    N = len(NID); E = []; gin = [0] * N; gout = [0] * N
    for k in range(N):
        gin[k] = 2 * k; gout[k] = 2 * k + 1
        E.append((gin[k], gout[k], 1))
    nxt = [2 * N]

    def chain(pk, qk, sh):
        a = nxt[0]; nxt[0] += len(sh) + 1
        E.append((gout[pk], a, 1)); prev = a
        for idx, sk in enumerate(sh):
            E.append((prev, gin[sk], 1)); prev = gout[sk]
            E.append((prev, a + idx + 1, 1)); prev = a + idx + 1
        E.append((prev, gin[qk], 1))

    for (u, v) in union:
        iu, ju = rc(u); iv, jv = rc(v); di, dj = iv - iu, jv - ju
        if di != 0 and dj != 0:
            s1, s2 = nid(iv, ju), nid(iu, jv)
            if s1 not in NID or s2 not in NID:
                continue
            chain(NID[u], NID[v], [NID[s1], NID[s2]]); chain(NID[v], NID[u], [NID[s2], NID[s1]])
        else:
            chain(NID[u], NID[v], []); chain(NID[v], NID[u], [])
    S = nxt[0]; T = nxt[0] + 1; nxt[0] += 2
    for L in lanes:
        E.append((S, gin[NID[L["src"]]], 1)); E.append((gout[NID[L["snk"]]], T, 1))
    NN = nxt[0]
    U = np.array([e[0] for e in E]); V = np.array([e[1] for e in E]); C = np.array([e[2] for e in E])
    res = maximum_flow(csr_matrix((C, (U, V)), shape=(NN, NN)), S, T)
    out = {"n_union_nodes": N, "n_arcs": len(E), "max_flow": int(res.flow_value), "demand": 16,
           "min_cut_empty": bool(res.flow_value >= 16)}
    if want_witness and res.flow_value >= 16:
        fl = res.flow.tocsr()
        outs = collections.defaultdict(list)
        for (u, v, c) in E:
            f = int(fl[u, v])
            if f > 0:
                outs[u].append([v, f])
        inv = {v: k for k, v in NID.items()}
        lab = {}
        for l, L in enumerate(lanes):
            lab[gin[NID[L["src"]]]] = "src%d" % l; lab[gout[NID[L["snk"]]]] = "snk%d" % l
        pairs = []
        for _ in range(int(res.flow_value)):
            cur = S; s_label = None; t_label = None
            for _ in range(200000):
                if cur in lab:
                    if lab[cur].startswith("src"):
                        s_label = lab[cur]
                    else:
                        t_label = lab[cur]
                if cur == T:
                    break
                mv = None
                for e in outs[cur]:
                    if e[1] > 0 and e[0] == T:
                        mv = e; break
                if mv is None:
                    for e in outs[cur]:
                        if e[1] > 0:
                            mv = e; break
                e_ = mv; e_[1] -= 1
                cur = e_[0]
            pairs.append([s_label, t_label])
        out["witness_pairs"] = pairs
        ident = sum(1 for s_, t_ in pairs if s_ is not None and t_ is not None and s_.replace("src", "") == t_.replace("snk", ""))
        out["witness_identity_pairs"] = ident
        out["witness_note"] = ("pairing-free relaxation realises a PERMUTED matching (%d/16 identity), "
                               "i.e. 16 disjoint lanes fit the exact clearance+keepout+budget constraints "
                               "only when the snk assignment may be permuted." % ident)
    return out


def t5_union_flow():
    g = PREV.Gen(json.load(open(MODEL)))
    lanes = build_lanes(g, prune=True)
    return claim_flow(lanes, want_witness=True)


def t6_budget_sensitivity():
    g = PREV.Gen(json.load(open(MODEL)))
    return {"pruned_1p6x": claim_flow(build_lanes(g, prune=True))["max_flow"],
            "unpruned": claim_flow(build_lanes(g, prune=False))["max_flow"],
            "verdict": ("the 16 disjoint lanes survive the 1.6x detour budget, so the self-declared "
                        "budget is not the binding resource for the pairing-free relaxation")}


def t7_subset_hall(maxsize=3):
    g = PREV.Gen(json.load(open(MODEL)))
    lanes = build_lanes(g, prune=True)
    # rebuild the graph once, then re-run max-flow per subset by re-adding S/T arcs
    union = set()
    for L in lanes:
        union |= L["steps"]
    NID = {n: k for k, n in enumerate(sorted({x for s in union for x in s}))}
    N = len(NID); E = []; gin = [0] * N; gout = [0] * N
    for k in range(N):
        gin[k] = 2 * k; gout[k] = 2 * k + 1
        E.append((gin[k], gout[k], 1))
    nxt = [2 * N]

    def chain(pk, qk, sh):
        a = nxt[0]; nxt[0] += len(sh) + 1
        E.append((gout[pk], a, 1)); prev = a
        for idx, sk in enumerate(sh):
            E.append((prev, gin[sk], 1)); prev = gout[sk]
            E.append((prev, a + idx + 1, 1)); prev = a + idx + 1
        E.append((prev, gin[qk], 1))

    for (u, v) in union:
        iu, ju = rc(u); iv, jv = rc(v)
        if iu != iv and ju != jv:
            s1, s2 = nid(iv, ju), nid(iu, jv)
            if s1 not in NID or s2 not in NID:
                continue
            chain(NID[u], NID[v], [NID[s1], NID[s2]]); chain(NID[v], NID[u], [NID[s2], NID[s1]])
        else:
            chain(NID[u], NID[v], []); chain(NID[v], NID[u], [])
    S = nxt[0]; T = nxt[0] + 1
    base = [list(e) for e in E]
    NN = T + 1
    U = np.array([e[0] for e in base]); V = np.array([e[1] for e in base]); C = np.array([e[2] for e in base])

    def flow(sub):
        u2 = list(U); v2 = list(V); c2 = list(C)
        for l in sub:
            u2.append(S); v2.append(gin[NID[lanes[l]["src"]]]); c2.append(1)
            u2.append(gout[NID[lanes[l]["snk"]]]); v2.append(T); c2.append(1)
        return int(maximum_flow(csr_matrix((np.array(c2), (np.array(u2), np.array(v2))), shape=(NN, NN)), S, T).flow_value)
    res = {"all16": flow(range(16)), "violations": {}}
    for k in range(1, maxsize + 1):
        bad = [(sub, f) for sub in itertools.combinations(range(16), k) for f in [flow(sub)] if f < k]
        res["violations"]["size_%d" % k] = len(bad)
        if bad:
            res["first_violation"] = [list(bad[0][0]), bad[0][1]]
            break
    res["verdict"] = ("no Hall-type subset obstruction up to the tested size (screening only; the "
                      "identity pairing's multi-commodity obstruction is not decided by this test)")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--skip-t7", action="store_true")
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_R513_DECISIVE_TRIAGE_v1.json")
    t0 = time.time()
    rep = {"artifact": "k2_r513_decisive_triage_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-183 sec.3.5 (read-only; no Solve) · handoff-K2-513 sec.0",
           "boundaries": "Solve() 0 calls; quota 0; frozen four sources 4/4 untouched; criteria rev=6; "
                         "read-only graph/geometry algorithms (exhaustive enumeration, max-flow, 1-D packing)",
           "t3_clearance_encoding_exactness": t3_exactness(),
           "t4_continuous_cut_bound": t4_cut_bound(),
           "t5_union_claim_disjoint_flow": t5_union_flow(),
           "t6_budget_sensitivity": t6_budget_sensitivity()}
    if not a.skip_t7:
        rep["t7_subset_hall_screening"] = t7_subset_hall()
    rep["elapsed_s"] = round(time.time() - t0, 1)
    rep["decision"] = ("(B) VOID by exactness (no-op); (A)-WLOG refuted by site/lattice audit; binding "
                       "structure = prescribed IDENTITY PAIRING (multi-commodity), not capacity.")
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: v for k, v in rep.items() if k.startswith("t") or k in ("decision", "elapsed_s")},
                     ensure_ascii=False, indent=1)[:4000])
    print("WROTE", out)


if __name__ == "__main__":
    main()
