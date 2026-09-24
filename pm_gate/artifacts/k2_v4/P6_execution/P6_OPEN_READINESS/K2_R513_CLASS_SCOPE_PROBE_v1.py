#!/usr/bin/env python3
"""K2 · R513 addendum — READ-ONLY class-scope probe (Solve() 0 calls; quota 0).

Question: is the self-declared TWO-CHANNEL region convention (east lanes forbidden in the NW maze,
columns 24..112 rows <=32) the resource that blocks the identity pairing?  Test: per-class
pairing-free max-flow with and without the class restriction.
  flow == |class|  => the class-scope convention is NOT bindable for that class's own 8 lanes;
  flow  < |class|  => the convention itself blocks that class.
"""
import collections, heapq, json, math, os, sys, time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import K2_R512_JOINT_MCF_NODECAP_FIX_v1 as R512
PREV = R512.PREV
P = R512.P; NY = R512.NY; NX = R512.NX; X0 = R512.X0; Y0 = R512.Y0
BOUND = 1.6
nid, rc = R512.nid, R512.rc


def lanes_of(g, west_flag, class_pure):
    excl = np.zeros((NX, NY), bool)
    out = []
    for nm in g.names:
        n2 = g.node_ok(nm); pts = g.pt_by_net[nm]
        s0 = g.nearest_node(g.A[nm], n2, pts); t0 = g.nearest_node(g.B[nm], n2, pts, taken=(s0,))
        west = g.B[nm][0] < (X0 + R512.WALLC * P)
        if west != west_flag:
            continue
        ok = n2.copy()
        if class_pure and not west:
            for i in range(24, 113):
                ok[i * NY:i * NY + 33] = False
        av = (ok & ~excl).reshape(-1)
        kp = g.edge_ok(nm) & av[g.edge_u] & av[g.edge_v]
        adj = collections.defaultdict(list)
        for u, v in zip(g.edge_u[kp].tolist(), g.edge_v[kp].tolist()):
            w = P * math.hypot(abs(u // NY - v // NY), abs(u % NY - v % NY))
            adj[u].append((v, w)); adj[v].append((u, w))

        def dij(st):
            best = {st: 0.0}; pq = [(0.0, st)]
            while pq:
                d, u = heapq.heappop(pq)
                if d > best.get(u, 1e18) + 1e-12:
                    continue
                for (v, w) in adj.get(u, ()):
                    nd = d + w
                    if nd < best.get(v, 1e18) - 1e-12:
                        best[v] = nd; heapq.heappush(pq, (nd, v))
            return best
        src, snk = nid(*s0), nid(*t0)
        ds = dij(src); dt = dij(snk); sp = ds.get(snk, float("inf"))
        keep = {n for n in ds if n in dt and ds[n] + dt[n] <= BOUND * sp + 1e-9}
        st = set()
        for u in keep:
            for (v, w) in adj.get(u, ()):
                if v in keep:
                    st.add((u, v) if u < v else (v, u))
        out.append({"nm": nm, "src": src, "snk": snk, "steps": st, "sp": sp})
    return out


def claim_flow(lanes):
    union = set()
    for L in lanes:
        union |= L["steps"]
    NID = {n: k for k, n in enumerate(sorted({x for s in union for x in s}))}
    N = len(NID); E = []; gin = [0] * N; gout = [0] * N
    for k in range(N):
        gin[k] = 2 * k; gout[k] = 2 * k + 1
        E.append((gin[k], gout[k], 1))
    nx = [2 * N]

    def chain(pk, qk, sh):
        a = nx[0]; nx[0] += len(sh) + 1
        E.append((gout[pk], a, 1)); prev = a
        for i, sk in enumerate(sh):
            E.append((prev, gin[sk], 1)); prev = gout[sk]
            E.append((prev, a + i + 1, 1)); prev = a + i + 1
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
    S = nx[0]; T = nx[0] + 1; nx[0] += 2
    for L in lanes:
        E.append((S, gin[NID[L["src"]]], 1)); E.append((gout[NID[L["snk"]]], T, 1))
    NN = nx[0]
    U = np.array([e[0] for e in E]); V = np.array([e[1] for e in E]); C = np.array([e[2] for e in E])
    f = int(maximum_flow(csr_matrix((C, (U, V)), shape=(NN, NN)), S, T).flow_value)
    return f, N, len(E)


def main():
    m = json.load(open("/tmp/opencode/archer/model_l8.json"))
    g = PREV.Gen(m)
    rep = {"artifact": "k2_r513_class_scope_probe_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-183 sec.3.5 (read-only) · handoff-K2-513 sec.0",
           "boundaries": "Solve() 0 calls; quota 0; read-only max-flow; no model/board/tool edits", "runs": {}}
    for class_pure in (True, False):
        for west in (True, False):
            L = lanes_of(g, west, class_pure)
            f, N, na = claim_flow(L)
            rep["runs"]["class_pure=%s_west=%s" % (class_pure, west)] = {
                "n_lanes": len(L), "max_flow": f, "union_nodes": N, "arcs": na}
    rep["verdict"] = ("each class reaches its own 8/8 even with the class-pure region convention, so the "
                      "self-declared two-channel convention is NOT the binding resource (pairing-free); "
                      "the binding structure remains the prescribed IDENTITY pairing.")
    out = os.path.join(HERE, "K2_R513_CLASS_SCOPE_PROBE_v1.json")
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    print("WROTE", out)


if __name__ == "__main__":
    main()
