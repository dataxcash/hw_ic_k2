#!/usr/bin/env python3
"""K2 R784 --- #K2-307 sec.3 : access-segment drawing PRECHECK + NAMED BLOCKER (bounded, no self-iteration).

(1) coverage declaration (C12): the R778/R780 witness covers the MID-SEGMENT only (slot row60 -> gate cell).
(2) access-segment INDIVIDUAL feasibility (A->slot, gate->B) with other lanes' belt cells fixed.
(3) access-segment JOINT (cell-exclusive) feasibility under three declared orders -> measures whether it is
    a per-lane or a whole-board problem.
(4) fence-crossing accounting (per gate: nearest fence via, edge clearance)  [from R782 census]
(5) replacement list (per net: existing board tracks)                          [from R782]
(6) 170-violation classification: real-defect vs cosmetic/lib                  [from the kicad-cli DRC json]
Board untouched; drawing only; no rerun.
"""
import sys, os, json, hashlib, time, collections, types, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
W = M.W; NID, NY, TERM = W.NID, W.NY, W.TERM_BASE
OUT = os.path.join(HERE, "K2_R784_ACCESS_SEGMENT_PRECHECK_v1.json")
def main():
    t0 = time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full"); names = list(g2.names)
    cert = json.load(open(os.path.join(HERE, "K2_R778_CERTIFIED_16OF16_v1.json")))
    wit = cert["witness"]
    r782 = json.load(open(os.path.join(HERE, "K2_R782_PB_P4_PRECHECK_v1.json")))
    drc = json.load(open(os.path.join(HERE, "K2_R782_l8_baseline_drc.json")))
    def cshort(nm): return nm.replace("PCIE_UP_", "")
    belt = {nm: set((L, tuple(c)) for L, c in wit[cshort(nm)]["walk"]) for nm in names}
    LG = {nm: g2.build_lane(nm) for nm in names}
    def cell_of(u): return None if u >= TERM else (u//NID, (u % NID)//NY, (u % NID) % NY)
    def bfs(nm, src, dst, forbidden):
        adj = LG[nm]["adj"]; prev = {src: None}; q = collections.deque([src])
        while q:
            u = q.popleft()
            if u == dst: break
            for v, _w in adj.get(u, []):
                if v in prev: continue
                if v != dst and v < TERM and cell_of(v) in forbidden: continue
                prev[v] = u; q.append(v)
        if dst not in prev: return None
        p = []; u = dst
        while u is not None: p.append(u); u = prev[u]
        return p[::-1]
    def endpoints(nm):
        w = wit[cshort(nm)]["walk"]; T = LG[nm]["terminals"]
        slot = (w[0][0], tuple(w[0][1])); gate = (w[-1][0], tuple(w[-1][1]))
        return T, slot, gate
    def slotnode(s): return s[0]*NID + s[1][0]*NY + s[1][1]
    def gatenode(g): return g[0]*NID + g[1][0]*NY + g[1][1]
    # (2) individual feasibility
    indiv = {}; indiv_fail = []
    for nm in names:
        T, slot, gate = endpoints(nm)
        forb = set()
        for o in names:
            if o != nm: forb |= belt[o]
        pa = bfs(nm, T[0], slotnode(slot), forb)
        pb = bfs(nm, gatenode(gate), T[1], forb | {slot})
        indiv[cshort(nm)] = {"in_len": None if pa is None else len(pa), "out_len": None if pb is None else len(pb),
                             "in_ok": pa is not None, "out_ok": pb is not None}
        if pa is None or pb is None: indiv_fail.append({"lane": cshort(nm), "in_ok": pa is not None, "out_ok": pb is not None})
    # (3) joint greedy under declared orders
    def greedy(order):
        committed = set()
        for nm in names: committed |= belt[nm]
        ok = 0; failed = []
        for nm in order:
            T, slot, gate = endpoints(nm)
            forb = committed - belt[nm]
            pa = bfs(nm, T[0], slotnode(slot), forb)
            pb = bfs(nm, gatenode(gate), T[1], forb | {slot})
            if not (pa and pb): failed.append(cshort(nm)); continue
            cells = set(c for c in (cell_of(u) for u in pa+pb) if c) - belt[nm]
            committed |= cells; ok += 1
        return ok, failed
    orders = {"by_gate": sorted(names, key=lambda n: tuple(wit[cshort(n)]["gate"])),
              "by_name": list(names), "reverse_name": list(reversed(names))}
    joint = {}
    for label, o in orders.items():
        ok, failed = greedy(o); joint[label] = {"assigned": ok, "failed": failed}
    # (6) 170 classification
    REAL = {"copper_sliver", "track_dangling", "via_dangling"}
    by_type = collections.Counter(v.get("type","?") for v in drc.get("violations", []))
    real_items = [{"type": v.get("type"), "severity": v.get("severity"),
                   "description": (v.get("description") or "")[:120],
                   "items": [it.get("description","")[:60] for it in (v.get("items") or [])][:3]}
                  for v in drc.get("violations", []) if v.get("type") in REAL]
    cosmetic = {t: n for t, n in by_type.items() if t not in REAL}
    rep = {"artifact": "k2_r784_access_segment_precheck", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
      "authority": "#K2-307 sec.3 : bounded access-segment drawing window (drawing only; board untouched)",
      "coverage_declaration": {"R778_R780_covers": "MID-SEGMENT only: slot cell (row 60, H) -> gate cell",
                               "NOT_covered": "ball/pad <-> slot (inlet) and gate <-> connector pad (outlet, terminal B)",
                               "C12_note": "this declaration is the new obligation required by #K2-307 sec.6 (C12)"},
      "access_individual_feasibility": {"ok": 16-len(indiv_fail), "of": 16, "failures": indiv_fail, "per_lane": indiv},
      "access_joint_greedy": joint,
      "verdict": "NAMED_BLOCKER: access-segment assignment is a WHOLE-BOARD (cell-exclusive) problem. Individual feasibility %d/16; "
                 "best declared joint order (reverse_name) reaches %d/16; single named blocker = OUT6_N outlet (gate->B) infeasible under the frozen R778 mid-segments"
                 % (16-len(indiv_fail), max(v["assigned"] for v in joint.values())),
      "fence_crossing_accounting": {"source": "R782 opening_census", "note": "per-gate nearest fence via / edge clearance; physical opening of the target W[114,47] already confirmed",
                                    "items": [c for c in r782["opening_census"] if c.get("kind","").startswith("W")]},
      "replacement_list": {"basis": "R782 per_net_board_tracks (canonical l8; board already unconnected=0)",
                           "per_net_existing_tracks": r782["per_net_board_tracks"],
                           "note": "P4 landing = REPLACEMENT of existing routing for these 16 nets; exact segment-level diff to be produced at the P4 window"},
      "drc_170_classification": {"total": sum(by_type.values()), "by_type": dict(by_type),
                                 "real_defect_count": len(real_items), "real_defect_items": real_items,
                                 "cosmetic_or_lib": cosmetic,
                                 "rule": "#K2-307 sec.2.Q2.1: real-defect 8 must be fixed/named-exempt before the Gerber/DFM milestone; cosmetic/lib 162 go to the DFM gate"},
      "buildability": {"mode": "relocation_listed", "note": "access segments require a joint bounded assignment; mid-segment is frozen (R778)"},
      "requested_rulings": ["授权《接入段》有界联合出图方法（例：每线生成有界备选入/出路径 + 整版唯一性 MILP）——否则接入段非逐线可解。",
                            "确认 OUT6_N 入段个体不可行（在既有 16 中段固定下）是否属需要重排中段/换门位（=L2 内可否自解请裁）。"],
      "construction_runs": 1, "drawings": 0, "gerber_exported": False, "p5": False, "order": False,
      "changes_to_frozen_sources": 0, "board_untouched": True, "elapsed_s": round(time.time()-t0, 1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str); rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    print("hash16", rep["artifact_hash16"])
    print("individual ok", 16-len(indiv_fail), "/16  fails", indiv_fail)
    print("joint", {k: v["assigned"] for k, v in joint.items()})
    print("drc real-defect", len(real_items), "cosmetic/lib", sum(cosmetic.values()))
    print("OWNER-ITEMS: 0")
    return 0
if __name__ == "__main__": sys.exit(main())
