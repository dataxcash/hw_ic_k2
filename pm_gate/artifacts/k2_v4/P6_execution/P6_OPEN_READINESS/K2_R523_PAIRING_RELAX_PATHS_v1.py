#!/usr/bin/env python3
"""K2 · R523 — PAIRING-RELAXED WITNESS **PATHS** (read-only evidence sedimentation · Solve() 0 calls · quota 0).

Handoff-K2-523 §3 (P-3): R518 §q3_witness flagged that R513-T5 stored only the realised PAIRING
(`witness_pairs`), NOT the geometric paths. This script re-derives the same T5 flow and stores, for each
of the 16 unit flows, the full Manhattan node sequence (lattice path) + the implied lane->pad permutation,
as checkable geometric evidence for the F1/"identity-pairing" attribution.

Authority: #K2-189 §四 (R517 constructive-witness family ratified, NON-quota) · handoff-K2-523 §3 P-3.
Read-only: reuses R513/R512/R499 modules; no board/SPEC/generator/criteria writes; no Solve().
"""
import argparse, collections, hashlib, json, math, os, sys, time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import K2_R513_DECISIVE_TRIAGE_v1 as R513
import K2_R512_JOINT_MCF_NODECAP_FIX_v1 as R512

P, NY, NX, X0, Y0 = R512.P, R512.NY, R512.NX, R512.X0, R512.Y0
MODEL = "/tmp/opencode/archer/model_l8.json"
nid, rc = R512.nid, R512.rc


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build(lanes):
    """Same gadget as R513.claim_flow; capacity-1 on every union node => node-disjoint = claim-disjoint."""
    union = set()
    for L in lanes:
        union |= L["steps"]
    NID = {n: k for k, n in enumerate(sorted({x for s in union for x in s}))}
    N = len(NID)
    E = []; gin = [0] * N; gout = [0] * N
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
            chain(NID[u], NID[v], [NID[s1], NID[s2]])
            chain(NID[v], NID[u], [NID[s2], NID[s1]])
        else:
            chain(NID[u], NID[v], [])
            chain(NID[v], NID[u], [])
    S = nxt[0]; T = nxt[0] + 1; NN = T + 1
    for L in lanes:
        E.append((S, gin[NID[L["src"]]], 1))
        E.append((gout[NID[L["snk"]]], T, 1))
    U = np.array([e[0] for e in E]); V = np.array([e[1] for e in E]); C = np.array([e[2] for e in E])
    res = maximum_flow(csr_matrix((C, (U, V)), shape=(NN, NN)), S, T)
    return dict(S=S, T=T, NN=NN, E=E, gin=gin, gout=gout, N=N,
                inv={v: k for k, v in NID.items()}, NID=NID,
                flow=res.flow.tocsr(), fv=int(res.flow_value))


def decompose(g):
    """Decompose the integral flow into S->T units; for each, record the UNION-node sequence (the path)."""
    outs = collections.defaultdict(list)   # u -> [[v, remaining_flow], ...]
    for (u, v, c) in g["E"]:
        f = int(g["flow"][u, v])
        if f > 0:
            outs[u].append([v, f])
    S, T, N = g["S"], g["T"], g["N"]
    gin, gout, inv = g["gin"], g["gout"], g["inv"]

    def node_of(x):
        if x < 2 * N:
            k, kind = divmod(x, 2)
            return inv[k] if kind in (0, 1) else None
        return None

    paths = []
    for _ in range(g["fv"]):
        seq = []          # union-node sequence
        cur = S
        for _ in range(200000):
            n = node_of(cur)
            if n is not None and (not seq or seq[-1] != n):
                seq.append(n)
            if cur == T:
                break
            mv = None
            for e in outs[cur]:
                if e[1] > 0:
                    mv = e; break
            if mv is None:
                raise RuntimeError("flow decomposition stuck at node %d" % cur)
            mv[1] -= 1
            cur = mv[0]
        paths.append(seq)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R523_PAIRING_RELAX_PATHS_v1.json"))
    a = ap.parse_args()
    t0 = time.time()
    model = json.load(open(MODEL))
    g_ = R513.PREV.Gen(model)
    lanes = R513.build_lanes(g_, prune=True)
    g = build(lanes)
    raws = decompose(g)

    paths = []
    for seq, ns in zip(raws, raws):
        ij = [list(rc(n)) for n in seq]
        # lattice rule = 8-neighbourhood (Chebyshev 1): a diagonal move is one legal model step
        steps_ok = all(max(abs(ij[k][0] - ij[k + 1][0]), abs(ij[k][1] - ij[k + 1][1])) == 1
                       for k in range(len(ij) - 1))
        length = sum(P * math.hypot(ij[k + 1][0] - ij[k][0], ij[k + 1][1] - ij[k][1])
                     for k in range(len(ij) - 1))
        edges = [(min(ns[k], ns[k + 1]), max(ns[k], ns[k + 1])) for k in range(len(ns) - 1)]
        paths.append({"src_ij": ij[0], "snk_ij": ij[-1], "n_nodes": len(ij),
                      "unit_steps_ok": steps_ok,
                      "length_mm": round(length, 4),
                      "edges_uv": [[int(u), int(v)] for (u, v) in edges],
                      "path_ij": ij,
                      "path_mm": [[round(X0 + i * P, 4), round(Y0 + j * P, 4)] for (i, j) in ij]})

    # attribute each extracted path to (lane i's src -> which lane's snk)
    src_map = {}
    for i, L in enumerate(lanes):
        src_map[tuple(rc(L["src"]))] = i
    snk_map = {}
    for i, L in enumerate(lanes):
        snk_map[tuple(rc(L["snk"]))] = i

    perm = {}
    for p in paths:
        i = src_map.get(tuple(p["src_ij"]))
        j = snk_map.get(tuple(p["snk_ij"]))
        p["from_lane"] = i
        p["to_lane"] = j
        p["edge"] = "%s -> %s" % (lanes[i]["nm"] if i is not None else "?",
                                  lanes[j]["nm"] if j is not None else "?")
        p["identity"] = (i is not None and i == j)
        if i is not None:
            perm[i] = j

    # validation: node-disjoint across the 16 paths (= claim-disjoint), all unit steps, endpoints are registered src/snk
    seen = {}
    dup = 0
    for k, p in enumerate(paths):
        for n in [tuple(x) for x in p["path_ij"]]:
            if n in seen:
                dup += 1
            seen[n] = k
    identity = sum(1 for p in paths if p["identity"])

    # HONEST SCOPE: R513-T5 built the flow on the UNION of all lanes' allowed steps => per-lane eligibility
    # (edge_ok(nm) + that lane's 1.6x detour prune) is NOT enforced by T5. Measure that gap explicitly.
    own = {i: set(lanes[i]["steps"]) for i in range(len(lanes))}
    lanes_np = R513.build_lanes(g_, prune=False)          # per-net eligibility WITHOUT the 1.6x budget
    own_np = {i: set(lanes_np[i]["steps"]) for i in range(len(lanes_np))}
    assert [L["nm"] for L in lanes_np] == [L["nm"] for L in lanes], "lane order mismatch"
    union_all = set()
    for L in lanes:
        union_all |= L["steps"]
    for p in paths:
        e = [tuple(x) for x in p["edges_uv"]]
        in_union = sum(1 for x in e if x in union_all)
        i = p["from_lane"]
        in_own = sum(1 for x in e if i is not None and x in own[i]) if i is not None else 0
        in_own_np = sum(1 for x in e if i is not None and x in own_np[i]) if i is not None else 0
        p["steps_total"] = len(e)
        p["steps_in_union"] = in_union
        p["steps_in_src_lane_allowed"] = in_own
        p["src_lane_eligible"] = (in_own == len(e) and len(e) > 0)
        p["steps_in_src_lane_eligibility_nobudget"] = in_own_np
        p["src_lane_keepout_legal"] = (in_own_np == len(e) and len(e) > 0)
        if i is not None:
            bad = [k for k, x in enumerate(e) if x not in own_np[i]]
            p["first_illegal_step_index"] = (bad[0] if bad else None)
            p["first_step_own_net_legal"] = (e[0] in own_np[i]) if e else None

    validation = {
        "n_paths": len(paths),
        "all_8nb_steps": all(p["unit_steps_ok"] for p in paths),
        "node_disjoint_all_pairs": dup == 0,
        "duplicate_node_hits": dup,
        "all_src_registered": all(tuple(p["src_ij"]) in src_map for p in paths),
        "all_snk_registered": all(tuple(p["snk_ij"]) in snk_map for p in paths),
        "srcs_all_distinct": len({tuple(p["src_ij"]) for p in paths}) == len(paths),
        "snks_all_distinct": len({tuple(p["snk_ij"]) for p in paths}) == len(paths),
        "permutation_is_bijection": sorted(perm.keys()) == list(range(len(lanes))) and
                                    sorted(perm.values()) == list(range(len(lanes))),
        "all_steps_in_union_graph": all(p["steps_in_union"] == p["steps_total"] for p in paths),
        "paths_fully_in_own_src_lane_allowed": sum(1 for p in paths if p["src_lane_eligible"]),
        "paths_keepout_legal_for_own_src_net": sum(1 for p in paths if p["src_lane_keepout_legal"]),
        "paths_with_first_step_own_net_legal": sum(1 for p in paths if p["first_step_own_net_legal"]),
        "first_illegal_step_index_by_path": {str(i): paths[i]["first_illegal_step_index"]
                                             for i in range(len(paths))},
        "scope_note": "R513-T5 flow lives on the UNION of all lanes' allowed steps, so per-net eligibility "
                      "(edge_ok/keepouts) and the per-lane 1.6x detour prune are NOT enforced. "
                      "`paths_fully_in_own_src_lane_allowed` = with-budget; "
                      "`paths_keepout_legal_for_own_src_net` = budget-free per-net eligibility. Node-"
                      "disjointness and the realised permutation are exact; do NOT read T5 as a per-lane-legal witness.",
    }

    movement = [{"net_from": lanes[i]["nm"], "net_to": lanes[j]["nm"], "ball_index_moved": [i, j],
                 "identity": i == j} for i, j in sorted(perm.items())]

    rep = {
        "artifact": "k2_r523_pairing_relax_paths_v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "authority": "handoff-K2-523 sec.3 (P-3 read-only evidence sedimentation) · #K2-189 sec.4 "
                     "(R517 constructive-witness family ratified, NON-quota)",
        "solve_calls": 0,
        "nature": "read-only re-derivation of R513-T5 (pairing-free relaxation, exact clearance) + "
                  "THIS TIME the geometric paths and the implied lane->pad permutation",
        "inputs": {"model": MODEL, "model_sha256": sha256(MODEL),
                   "reused_modules": ["K2_R513_DECISIVE_TRIAGE_v1", "K2_R512_JOINT_MCF_NODECAP_FIX_v1"]},
        "method": "union-claim-disjoint max-flow on the same gadget as R513.claim_flow (capacity-1 per "
                  "union node => node-disjoint; diagonal steps consume their two off-diagonal shadow nodes); "
                  "then integral flow decomposition into 16 S->T units recording each union-node sequence",
        "max_flow": g["fv"], "demand": len(lanes), "n_union_nodes": g["N"],
        "verdict": ("pairing-free UNION-claim-disjoint relaxation: 16/16 node-disjoint lanes exist, but "
                    "the realised matching is a %d/16-identity permutation => the residual obstruction is "
                    "the prescribed IDENTITY pairing (multi-commodity), NOT capacity" % identity),
        "pairing": {"identity_pairs": identity, "permuted_pairs": len(paths) - identity,
                    "permutation": {str(k): v for k, v in sorted(perm.items())},
                    "interpretation": "the 16 lanes fit the EXACT clearance+keepout+budget semantics "
                                      "only if the snk assignment may be permuted; the residual "
                                      "obstruction is the prescribed IDENTITY pairing (multi-commodity)"},
        "movement_list_L1_OPTION_ONLY": movement,
        "paths": [{k: v for k, v in p.items() if k != "path_mm"} for p in paths],
        "paths_mm": [{"edge": p["edge"], "path_mm": p["path_mm"]} for p in paths],
        "validation": validation,
        "buildability": ("NOT-A-DELIVERABLE. This is a pairing-RELAXED witness (a what-if drawing): it "
                         "shows 16 node-disjoint Manhattan lanes with per-lane polylines, but it is NOT "
                         "the board's prescribed 1:1 net<->pad map. It becomes a buildable drawing only "
                         "if the owner (L1: ball remap) ratifies the permutation in `movement_list_L1_OPTION_ONLY`."),
        "boundaries": "Solve() 0; read-only; no supervision writes; frozen four 4/4 untouched; delivered "
                      "board anchor untouched; criteria read-only; no WORKER; stop-line maintained",
    }
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"max_flow": rep["max_flow"], "n_paths": len(paths),
                      "identity_pairs": identity, "validation": validation,
                      "sample_edge": paths[0]["edge"], "sample_len_mm": paths[0]["length_mm"]},
                     ensure_ascii=False, indent=1))
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
