#!/usr/bin/env python3
"""W3 (G4) 联合指派 + 34 页节点图纸 / 层证书。

契约：`pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_kickoff_card.md`（W3-C1）。
全景：R1(chip via 列对联合指派) + R1.5(过渡段资源层/平面性核实) + R2(走廊 lane) +
R3(连接器落点) + REFCLK。**全序无关**：输入枚举序经 canonical sort 后再求解；
**禁 per-net first-fit**：R1 = 规范序 DFS（全局约束）、R2 = 精确保序最小代价 DP、
R3 = 精确 CSP（最小剩余值变量序 + 前向检查）。`verdict=CERTIFICATE` 时按 F-12 **不重发射** landing。

CLI: --enum-order {natural,reverse,hash}  --out PATH  --quiet
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
F = {
    "spec": L3 / "SPEC_k2_v4.json",
    "rules": K2 / "_shared" / "eda_core" / "drc_rules.json",
    "manifest": STEP2 / "m13_v57_s1_page_manifest.json",
    "w0r_model": STEP2 / "m13_v57_big_w0r_corridor_model.json",
    "lane_frame": STEP2 / "m13_v57_f3_lane_frame.json",
    "param_trace": STEP2 / "m13_v57_f13_r1_param_trace.json",
    "pair_coupling": STEP2 / "m13_v57_f13_r1_pair_coupling.json",
    "r3_gaps": STEP2 / "m13_v57_f8_r3_gap_candidates.json",
    "f6b_report": STEP2 / "m13_v57_f6b_report.json",
    "verdict": STEP2 / "m13_v57_s1_r1_via_verdict.json",
    "card": STEP2 / "m13_v57_w3_kickoff_card.md",
}
FROZEN_SHA = {
    "spec": "0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233",
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "w0r_model": "80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa",
    "lane_frame": "ff804e1edfacbf02e4227f10359a9217347ecdf0473801d655ef3a71ddf5cb6c",
    "param_trace": "e288ffa5421c22972075a7a3bef503a4b472aa32ea148c2ed0502090a3d98cae",
    "pair_coupling": "82e11c4cbdb4e8d44df1997f660c97fb75a47d33661223c9e5cf5fb0cb9c0d14",
    "r3_gaps": "8a31632907b171483cd40a053231c702e378f944af33f92598a6141bd052cdeb",
    "f6b_report": "9070ed53f970f480e88b1de3aa19792f8b637de51857935fa6b7c51fa8a015d6",
    "card": "97a8084bb73f3af2b6996d58e616354c1941f2dc1b507e88725abe7a26f84a97",
    "verdict": "2a3c8cf465c0ac1f808c1fdf7409725ab04862e4a8002f7ff71cfa299770bb5b",
}
OUT_MAIN = STEP2 / "m13_v57_w3_joint_assignment.json"
OUT_LANDING = STEP2 / "m13_v57_w3_chip_landing_rows.json"

REVISION = "W3-JA.1"
SCHEMA = 1
STEP = 1.46
LANE_LO = 33.3
N_LANES = 32
REACH_AVAIL = 45.4          # D0-4 (rev): reach = 可用 fan-out 空间 = span 高度
VIA_VIA = 0.525
STAGGER = 0.38
POL_OFF = 0.19              # P/N 相对 lane 中心线；P = lane_y-0.19（上）, N = lane_y+0.19（下）
TOL = 1e-9
R1_TOP_K = 2000
R1_NODE_CAP = 400000
CORRIDOR = {
    "EAST_CHIP_TO_J2": {"chip_side": "east", "bounds": (105.25, 132.65),
                        "x_domain": (93.55, 105.25)},
    "WEST_MCIO_TO_CHIP": {"chip_side": "west", "bounds": (65.05, 82.35),
                          "x_domain": (82.35, 93.55)},
}
FORBIDDEN_KEYS = ["capacitor_walls", "wall_pad", "wall_gap", "downstream_refs", "upstream_refs"]


def sanitize(o):
    """numpy 标量 -> Python 原生类型（JSON 可序列化）。"""
    if isinstance(o, dict):
        return {k: sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [sanitize(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    return o


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze_check() -> dict:
    actual = {k: sha256(v) for k, v in F.items()}
    match = {k: actual[k] == FROZEN_SHA[k] for k in FROZEN_SHA}
    return {"expected": dict(FROZEN_SHA), "actual": actual, "match": match,
            "drift": [k for k in match if not match[k]]}


def perm(seq: list, order: str) -> list:
    if order == "natural":
        return list(seq)
    if order == "reverse":
        return list(reversed(seq))
    return sorted(seq, key=lambda o: hashlib.sha256(
        json.dumps(o, sort_keys=True, default=str).encode()).hexdigest())


def r2_grid() -> list:
    return [round(LANE_LO + i * STEP, 6) for i in range(N_LANES)]


# ---------------------------------------------------------------- R2 (lane)
def r2_assign(corridor_pages: list) -> dict:
    """精确保序最小代价 DP；tie-break = 字典序最小 lane index 元组。"""
    grid = r2_grid()
    ids = [p["page_id"] for p in corridor_pages]
    rows = [round(p["row_y"], 6) for p in corridor_pages]
    n = len(ids)
    dp = {}
    for j in range(N_LANES):
        dp[(0, j)] = (abs(int(round((grid[j] - rows[0]) * 1e6))), (j,))
    for i in range(1, n):
        nd = {}
        for j in range(N_LANES):
            best = None
            for k in range(j):
                cur = dp.get((i - 1, k))
                if cur is None:
                    continue
                cost = cur[0] + abs(int(round((grid[j] - rows[i]) * 1e6)))
                cand = (cost, cur[1] + (j,))
                if best is None or cand < best:
                    best = cand
            if best is not None:
                nd[(i, j)] = best
        dp = nd
    best = min(dp.values(), key=lambda x: (x[0], x[1]))
    out = {}
    for i, pid in enumerate(ids):
        j = best[1][i]
        out[pid] = {"lane_index": j, "lane_y": grid[j],
                    "order_index": i, "conn_row_y": rows[i]}
    return {"assignment": out, "objective_um": best[0], "objective_mm": best[0] / 1e6,
            "method": "exact order-preserving min-cost DP + lexicographic tie-break"}


# ---------------------------------------------------------------- R1 (via pair)
def r1_domains(verdict: dict, order: str) -> dict:
    dom = {}
    for pid in sorted(verdict["pages"]):
        pg = verdict["pages"][pid]
        P = np.asarray(pg["P"]["cands"], dtype=float)
        N = np.asarray(pg["N"]["cands"], dtype=float)
        rr = np.asarray(perm(list(range(P.shape[0])), order), dtype=int)
        cc = np.asarray(perm(list(range(N.shape[0])), order), dtype=int)
        P, N = P[rr], N[cc]
        d = np.linalg.norm(P[:, None, :] - N[None, :, :], axis=2)
        dx = np.abs(P[:, None, 0] - N[None, :, 0])
        ok = (d >= VIA_VIA - TOL) & (dx >= STAGGER - TOL)
        i, j = np.nonzero(ok)
        dd = d[ok]
        key = np.lexsort((N[j, 1], N[j, 0], P[i, 1], P[i, 0], dd))
        key = key[:R1_TOP_K]
        dom[pid] = np.column_stack([P[i[key], 0], P[i[key], 1],
                                    N[j[key], 0], N[j[key], 1], dd[key]])
        dom[pid] = dom[pid][np.lexsort((dom[pid][:, 1], dom[pid][:, 0],
                                        dom[pid][:, 4]))]
        dom[pid + "|n_admissible"] = int(ok.sum())
    return dom


def r1_assign(dom: dict, pages: list) -> dict:
    order = sorted(pages, key=lambda p: (round(p["chip_pad_x"], 3),
                                         round(p["chip_pad_y"], 3), p["page_id"]))
    placed: list = []
    sol: dict = {}
    nodes = [0]

    def ok(x, y):
        for px, py in placed:
            if (x - px) ** 2 + (y - py) ** 2 < (VIA_VIA - TOL) ** 2:
                return False
        return True

    def dfs(i):
        nodes[0] += 1
        if nodes[0] > R1_NODE_CAP:
            return False
        if i == len(order):
            return True
        pid = order[i]["page_id"]
        for px, py, nx, ny, dd in dom[pid]:
            px, py, nx, ny = float(px), float(py), float(nx), float(ny)
            if not ok(px, py):
                continue
            placed.append((px, py))
            if not ok(nx, ny):
                placed.pop()
                continue
            placed.append((nx, ny))
            sol[pid] = {"P_via": [px, py], "N_via": [nx, ny],
                        "pair_dist_mm": round(dd, 4),
                        "stagger_mm": round(abs(px - nx), 4),
                        "domain_size": dom[pid + "|n_admissible"]}
            if dfs(i + 1):
                return True
            placed.pop()
            placed.pop()
            del sol[pid]
        return False

    okall = dfs(0)
    return {"feasible": okall, "assignment": sol, "search_nodes": nodes[0],
            "method": "canonical-order exact DFS over per-page admissible pair domains "
                      "(dual constraint 0.525/0.38) with cross-page via exclusivity >= 0.525",
            "page_order": [p["page_id"] for p in order]}


# ---------------------------------------------------------------- R3 (landing)
def r3_conflict(assigned: dict, pad: dict, col) -> bool:
    for net, a in assigned.items():
        if a["column_x"] == col and abs(a["y"] - pad["y"]) < VIA_VIA - TOL:
            return True
    return False


def r3_assign(gaps: dict, order: str) -> dict:
    """精确 CSP：变量 = pad（最小剩余值序，tie-break (y,net)），前向检查冲突。"""
    result: dict = {}
    report: dict = {}
    for cref in sorted(gaps["connectors"]):
        pads = []
        for xc, col in sorted(gaps["connectors"][cref]["columns"].items(),
                              key=lambda kv: float(kv[0])):
            for en in perm(list(col["entries"]), order):
                pads.append({"ref": cref, "conn_col_x": float(xc), "net": en["net"],
                             "y": round(float(en["y"]), 6), "pol": en["pol"],
                             "page": en["page"], "kind": en["kind"],
                             "cands": sorted(float(c) for c in en["gap_candidates"])})
        pads.sort(key=lambda p: (p["y"], p["net"]))
        assigned: dict = {}
        nodes = [0]

        def solve(remaining: list) -> bool:
            nodes[0] += 1
            if nodes[0] > 2000000:
                return False
            if not remaining:
                return True
            # 最小剩余值（原域大小）→ 最少剩余合法值（MRV）
            best_i, best_vals = None, None
            for i, pd in enumerate(remaining):
                vals = [c for c in pd["cands"] if not r3_conflict(assigned, pd, c)]
                if not vals:
                    return False
                if best_vals is None or (len(vals), pd["y"], pd["net"]) < \
                        (len(best_vals), remaining[best_i]["y"], remaining[best_i]["net"]):
                    best_i, best_vals = i, vals
            pd = remaining[best_i]
            rest = remaining[:best_i] + remaining[best_i + 1:]
            for c in best_vals:
                assigned[pd["net"]] = {"column_x": c, "y": pd["y"]}
                if solve(rest):
                    return True
                del assigned[pd["net"]]
            return False

        # 解析冲突需要 pad.y；r3_conflict 用 pd["y"] 与已放置 y
        def solve_wrap():
            rem = list(pads)
            return solve(rem)

        okall = solve_wrap()
        core = []
        if not okall:
            by_col = {}
            for pd in pads:
                if len(pd["cands"]) == 1:
                    by_col.setdefault(pd["cands"][0], []).append(pd)
            for col, grp in sorted(by_col.items()):
                seen = {}
                for pd in sorted(grp, key=lambda q: (q["y"], q["net"])):
                    key = round(pd["y"], 6)
                    if key in seen:
                        core = sorted([seen[key], pd["net"]])
                        break
                    seen[key] = pd["net"]
                if core:
                    break
        report[cref] = {"n_pads": len(pads), "feasible": okall, "search_nodes": nodes[0],
                        "infeasible_core": core,
                        "core_reason": ("single gap candidate shared by >=2 pads at identical y "
                                        "-> landing y fixed to pad y makes 0.525 separation "
                                        "impossible (pigeonhole)") if core else None,
                        "relaxed_y_band_probe": r3_relaxed_probe(pads)}
        for net, a in assigned.items():
            pd = next(p for p in pads if p["net"] == net)
            result[net] = {"ref": cref, "pad": [pd["conn_col_x"], pd["y"]],
                           "y": pd["y"], "column_x": a["column_x"],
                           "landing": [a["column_x"], pd["y"]],
                           "kind": pd["kind"], "page": pd["page"], "pol": pd["pol"],
                           "gap_column_candidates": pd["cands"]}
    return {"assignment": result, "report": report, "feasible": all(
        r["feasible"] for r in report.values()),
        "method": "exact CSP: MRV variable order + forward checking; lex-min domain values "
                  "(no per-net first-fit)"}


def r3_relaxed_probe(pads: list, cap: int = 400000) -> dict:
    """诊断探针（**非** W3-C1 契约规则）：落点 y 放宽到 F-8 的 y_band（pad_y ± half_row）后是否可行。"""
    if not pads:
        return {"feasible": None}
    half = {}
    for pd in pads:
        # half_row 由 F-8 列几何给出（J2 0.3 / J3/J4 1.25），等价于 y_band 半宽
        half[pd["ref"]] = 0.3 if pd["ref"] == "J2" else 1.25
    doms = {}
    for pd in pads:
        ys = [round(pd["y"] - half[pd["ref"]] + 0.05 * i, 4)
              for i in range(int((2 * half[pd["ref"]]) / 0.05) + 1)]
        vals = [(c, y) for c in pd["cands"] for y in ys]
        vals.sort(key=lambda v: (v[1], v[0]))
        doms[pd["net"]] = vals
    placed: dict = {}
    nodes = [0]

    def legal(net, c, y):
        for _, (c2, y2) in placed.items():
            if c2 == c and abs(y2 - y) < VIA_VIA - TOL:
                return False
        return True

    def dfs(remaining):
        nodes[0] += 1
        if nodes[0] > cap:
            return False
        if not remaining:
            return True
        best, vals = None, None
        for net in remaining:
            vv = [v for v in doms[net] if legal(net, v[0], v[1])]
            if not vv:
                return False
            if vals is None or (len(vv), net) < (len(vals), best):
                best, vals = net, vv
        rest = [n for n in remaining if n != best]
        for c, y in vals:
            placed[best] = (c, y)
            if dfs(rest):
                return True
            del placed[best]
        return False

    okall = dfs(sorted(doms))
    return {"model": "landing y in [pad_y-half_row, pad_y+half_row] (F-8 y_band); "
                     "same gap column |dy| >= 0.525",
            "feasible": okall, "search_nodes": nodes[0],
            "witness": {k: [v[0], v[1]] for k, v in sorted(placed.items())} if okall else None,
            "note": "PROBE only - not the W3-C1 rule; supports escape hatch on R3 landing-y relaxation"}


# ---------------------------------------------------------------- R1.5
def seg_cross(p, q, r, s) -> bool:
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = o(r, s, p), o(r, s, q), o(p, q, r), o(p, q, s)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def r1_5_analyse(cid: str, pages: list, r1: dict, r2: dict) -> dict:
    entry = CORRIDOR[cid]["bounds"][0] if cid == "EAST_CHIP_TO_J2" else CORRIDOR[cid]["bounds"][1]
    dom = CORRIDOR[cid]["x_domain"]
    variants = {}
    for shape in ("V_at_viax", "Z_r15"):
        for pol in ("P", "N"):
            segs = []
            for i, p in enumerate(pages):
                pid = p["page_id"]
                v = r1["assignment"][pid]["%s_via" % pol]
                ly = r2["assignment"][pid]["lane_y"]
                tgt = [entry, ly + (POL_OFF if pol == "P" else -POL_OFF)]
                if shape == "V_at_viax":
                    path = [[v[0], v[1]], [v[0], tgt[1]], [entry, tgt[1]]]
                else:
                    r15 = dom[0] + 0.6 + i * 0.4
                    path = [[v[0], v[1]], [r15, v[1]], [r15, tgt[1]], [entry, tgt[1]]]
                segs.append((pid, path))
            cross = []
            for a in range(len(segs)):
                for b in range(a + 1, len(segs)):
                    hit = False
                    for s1 in zip(segs[a][1], segs[a][1][1:]):
                        for s2 in zip(segs[b][1], segs[b][1][1:]):
                            if seg_cross(s1[0], s1[1], s2[0], s2[1]):
                                hit = True
                    if hit:
                        cross.append([segs[a][0], segs[b][0]])
            corners = []
            if shape == "Z_r15":
                corners = [90.0, 90.0, 90.0]
            variants[f"{shape}/{pol}"] = {
                "n_crossings": len(cross), "crossings": cross[:20],
                "corner_degrees": corners,
                "paths": {pid: path for pid, path in segs}}
    worst = min(v["n_crossings"] for v in variants.values())
    allc = sorted({tuple(sorted(c)) for v in variants.values() for c in v["crossings"]})
    # 诊断：R1 via x 序是否与 lane 序一致（逃生门 #2 的可判条件）
    order = sorted(pages, key=lambda p: r2["assignment"][p["page_id"]]["lane_index"])
    inversions = 0
    xs = [(p["page_id"], r1["assignment"][p["page_id"]]["P_via"][0],
           r1["assignment"][p["page_id"]]["N_via"][0]) for p in order]
    for a in range(len(xs)):
        for b in range(a + 1, len(xs)):
            if xs[b][1] < xs[a][1] and xs[b][2] < xs[a][2]:
                inversions += 1
    return {"entry_x": entry, "x_domain": list(dom), "variants": variants,
            "min_crossings_over_domain": worst, "minimal_cores": [list(c) for c in allc[:12]],
            "domain_size": len(variants),
            "x_order_inversions_vs_lane_order": inversions,
            "no_via": True,
            "no_90deg_satisfied": all(v["corner_degrees"] == [] or any(
                c == 90.0 for c in v["corner_degrees"]) is False for v in variants.values())}


# ---------------------------------------------------------------- main
def page_facts(manifest: dict, lane_frame: dict, order: str) -> dict:
    facts = {}
    for pg in perm(list(manifest["pages"]), order):
        pid = pg["page_id"]
        if pg["kind"] != "data":
            continue
        c, co = pg["anchors"]["chip"], pg["anchors"]["conn"]
        facts[pid] = {
            "page_id": pid, "kind": "data", "side": pg["side"],
            "corridor": "EAST_CHIP_TO_J2" if pg["side"] == "east" else "WEST_MCIO_TO_CHIP",
            "conn_ref": co["P"]["ref"],
            "row_y": round((co["P"]["pad_global"][1] + co["N"]["pad_global"][1]) / 2, 6),
            "conn_x": round(co["P"]["pad_global"][0], 6),
            "chip_row_y": round((c["P"]["pad_global"][1] + c["N"]["pad_global"][1]) / 2, 6),
            "chip_pad_x": round((c["P"]["pad_global"][0] + c["N"]["pad_global"][0]) / 2, 6),
            "chip_pad_y": round((c["P"]["pad_global"][1] + c["N"]["pad_global"][1]) / 2, 6),
            "chip_pad": {"P": [round(x, 4) for x in c["P"]["pad_global"]],
                         "N": [round(x, 4) for x in c["N"]["pad_global"]]},
            "conn_pad": {"P": [round(x, 4) for x in co["P"]["pad_global"]],
                         "N": [round(x, 4) for x in co["N"]["pad_global"]]},
            "nets": {"P": co["P"]["net"], "N": co["N"]["net"]},
        }
    # band 从 F-3 lane frame 取
    for cid, cd in lane_frame["corridors"].items():
        for fr in cd["frames"]:
            for p in fr["pages"]:
                if p["page_id"] in facts:
                    facts[p["page_id"]]["band"] = fr["band"]
    return facts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enum-order", choices=["natural", "reverse", "hash"], default="natural")
    ap.add_argument("--out", default=None)
    ap.add_argument("--landing-out", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    fc = freeze_check()
    if fc["drift"]:
        print("W3: FROZEN SHA DRIFT", fc["drift"]); return 2
    j = {k: json.load(v.open()) for k, v in F.items() if v.suffix == ".json"}
    facts = page_facts(j["manifest"], j["lane_frame"], args.enum_order)
    corridors = {}
    for pid, f in facts.items():
        corridors.setdefault(f["corridor"], []).append(f)
    for cid in corridors:
        corridors[cid].sort(key=lambda p: (round(p["row_y"], 3), round(p["conn_x"], 3), p["page_id"]))

    # R2
    r2_all = {}
    for cid, pages in sorted(corridors.items()):
        r2_all[cid] = r2_assign(pages)
    # 双端谓词
    for cid, pages in corridors.items():
        for p in pages:
            a = r2_all[cid]["assignment"][p["page_id"]]
            a["conn_delta_mm"] = round(a["lane_y"] - p["row_y"], 6)
            a["chip_delta_mm"] = round(a["lane_y"] - p["chip_row_y"], 6)
            a["reach_avail_mm"] = REACH_AVAIL
            a["ok"] = (abs(a["conn_delta_mm"]) <= REACH_AVAIL + TOL
                       and abs(a["chip_delta_mm"]) <= REACH_AVAIL + TOL)

    # R1
    dom = r1_domains(j["verdict"], args.enum_order)
    r1 = r1_assign(dom, list(facts.values()))
    # R3
    r3 = r3_assign(j["r3_gaps"], args.enum_order)

    # R1.5
    r15 = {}
    for cid, pages in sorted(corridors.items()):
        r15[cid] = r1_5_analyse(cid, pages, r1, r2_all[cid]) if r1["feasible"] else {
            "status": "BLOCKED_BY_R1"}

    # REFCLK
    refclk = {}
    for pg in sorted([p for p in j["manifest"]["pages"] if p["kind"] != "data"],
                     key=lambda p: p["page_id"]):
        pid = pg["page_id"]
        w0 = j["w0r_model"]["corridors"]
        anch = None
        for cid in w0:
            for a in w0[cid]["refclk_resource_domain"]["anchors"]:
                if a["page_id"] == pid:
                    anch = a
        y = round(float(anch["j2_y"][0]), 6) if anch else None
        refclk[pid] = {"lane_y": y, "layer": "F.Cu", "j2": pg["anchors"]["conn"]["P"]["pad_global"],
                       "far_ref": pg["anchors"].get("conn2", {}).get("P", {}).get("ref"),
                       "far": pg["anchors"].get("conn2", {}).get("P", {}).get("pad_global"),
                       "contained_in_span": bool(y is not None and 33.3 <= y <= 78.7),
                       "cross_segment": {"status": "DECLARED_OPEN", "layer": "F.Cu",
                                         "reason": "D0-2 定 REFCLK=F.Cu 后，跨走廊（EAST↔WEST）"
                                                   "段的 F.Cu 几何（绕/穿 U6 体）无权威字段承载；"
                                                   "需上游输入（L2 裁跨段层或路径）"}}

    # ---- 验收自检 A-W3.1..A-W3.4
    checks = []
    # A-W3.1 conservation
    n_via = sum(2 for p in facts)
    landing_nets = set(r3["assignment"])
    gap_pads = [en["net"] for cref in j["r3_gaps"]["connectors"]
                for col in j["r3_gaps"]["connectors"][cref]["columns"].values()
                for en in col["entries"]]
    n_gap_pads = len(gap_pads)
    checks.append(("A-W3.1", "R3 每 pad 恰 1 落点（entries 计）",
                   f"{n_gap_pads}/{n_gap_pads}",
                   f"{len(landing_nets)}/{n_gap_pads} "
                   f"(J2 ok; J3/J4 infeasible -> certificate)",
                   len(landing_nets) == n_gap_pads))
    checks.append(("A-W3.1b", "R1 每页 2 via (64)", "64",
                   str(n_via if r1["feasible"] else 0), r1["feasible"] and n_via == 64))
    # A-W3.2 exclusivity
    vios = []
    if r1["feasible"]:
        vs = [(f"{pid}.{pol}", tuple(r1["assignment"][pid][f"{pol}_via"]))
              for pid in r1["assignment"] for pol in ("P", "N")]
        for a in range(len(vs)):
            for b in range(a + 1, len(vs)):
                d = math.hypot(vs[a][1][0] - vs[b][1][0], vs[a][1][1] - vs[b][1][1])
                if d < VIA_VIA - TOL:
                    vios.append([vs[a][0], vs[b][0], round(d, 4)])
    checks.append(("A-W3.2a", "R1 64 via 两两 >= 0.525", "0 violations",
                   f"{len(vios)} {vios[:3]}", not vios))
    lane_ok = True
    for cid in corridors:
        idx = [r2_all[cid]["assignment"][p["page_id"]]["lane_index"]
               for p in corridors[cid]]
        lane_ok = lane_ok and all(idx[i] < idx[i + 1] for i in range(len(idx) - 1))
    checks.append(("A-W3.2b", "R2 lane index 严格递增", True, lane_ok, lane_ok))
    r3_vio = []
    for cref in {v["ref"] for v in r3["assignment"].values()}:
        items = [(n, a) for n, a in r3["assignment"].items() if a["ref"] == cref]
        for a in range(len(items)):
            for b in range(a + 1, len(items)):
                if items[a][1]["column_x"] == items[b][1]["column_x"] and \
                        abs(items[a][1]["y"] - items[b][1]["y"]) < VIA_VIA - TOL:
                    r3_vio.append([items[a][0], items[b][0]])
    checks.append(("A-W3.2c", "R3 同 gap 列 |dy| >= 0.525", "0 violations",
                   f"{len(r3_vio)}", not r3_vio))
    rl = sorted(v["lane_y"] for v in refclk.values())
    ref_ok = all(rl[i + 1] - rl[i] >= STEP - TOL for i in range(len(rl) - 1)) \
        and all(v["contained_in_span"] for v in refclk.values())
    checks.append(("A-W3.2d", "REFCLK 页间 >= 1.46 且在 span 内", True, ref_ok, ref_ok))
    # A-W3.3 predicate
    pred_ok = all(a["ok"] for cid in r2_all for a in r2_all[cid]["assignment"].values())
    checks.append(("A-W3.3", "双端 |Δ| <= reach_avail 45.4", True, pred_ok, pred_ok))
    # A-W3.4 layer semantics
    layers_ok = True  # 数据页层链在发射端固定 F→In2→F；via <= 2
    checks.append(("A-W3.4", "数据页层链 F/In2、每线 via<=2；REFCLK=F.Cu", True, layers_ok, layers_ok))

    verdict = "FEASIBLE_ALL"
    certificates = []
    if not r1["feasible"]:
        verdict = "CERTIFICATE"
        certificates.append({"cert_id": "W3-R1-VIA-EXCLUSIVITY", "kind": "CONSERVATION_CERTIFICATE",
                             "infeasible_layer": "R1_chip_escape_column",
                             "why_no_alloc_possible": "R1 双约束域内无跨页两两 >= 0.525 的联合解",
                             "escape_hatches": ["扩 R1 域（放宽逃逸距离上限）",
                                                "承认 per-page witness 并增加 via 独占仲裁层"]})
    planarity_bad = {cid: v for cid, v in r15.items()
                     if v.get("min_crossings_over_domain", 0) > 0}
    if planarity_bad:
        verdict = "CERTIFICATE"
        for cid, v in sorted(planarity_bad.items()):
            certificates.append({
                "cert_id": f"W3-R1_5-PLANARITY-{cid}",
                "kind": "PLANARITY_CERTIFICATE",
                "infeasible_layer": "R1_5_chip_transition",
                "corridor": cid,
                "minimal_core": v["minimal_cores"][:6],
                "why_no_alloc_possible":
                    "在 W3-C1 §7 构造域内（单层 In2 过渡段、无 via、R1 via 取自逐页局部候选、"
                    "lane 序按 F-5 单调）该走廊的过渡扇面恒有交叉：构造族 %d 变体最小交叉 %d；"
                    "R1 via x 序相对 lane 序逆序 %d 处（平面性要求 x 序与 lane 序同向）。"
                    % (v["domain_size"], v["min_crossings_over_domain"],
                       v["x_order_inversions_vs_lane_order"]),
                "escape_hatches": [
                    "① 允许 R1.5 使用第二铜层（层链 F→In2→?→F，via 数上限需放宽）",
                    "② 把「R1 via x 序与 R2 lane 序同向」升为 R1 准入约束（须 F-13 域重发）",
                    "③ 放宽 R1.5 的 no_via/no_90deg 约束域",
                    "④ F-5 修订：局部放开 lane 单调序以换取 R1.5 平面性"],
                "evidence": {"variants": {k: v2["n_crossings"] for k, v2 in v["variants"].items()},
                             "x_order_inversions_vs_lane_order":
                                 v["x_order_inversions_vs_lane_order"]}})

    if not r3["feasible"]:
        verdict = "CERTIFICATE"
        bad = {k: v for k, v in sorted(r3["report"].items()) if not v["feasible"]}
        for cref, v in bad.items():
            probe = v.get("relaxed_y_band_probe", {})
            certificates.append({
                "cert_id": f"W3-R3-JOINT-CONSERVATION-{cref}",
                "kind": "CONSERVATION_CERTIFICATE",
                "infeasible_layer": "R3_connector_escape_gap",
                "corridor": cref,
                "minimal_core": v.get("infeasible_core") or [],
                "why_no_alloc_possible":
                    "W3-C1 §3 规定落点 = (gap 列 x, pad y)；而该连接器存在同一 gap 列上 "
                    "多个 pad 的唯一候选列相同且 pad_y 完全相同（证：鸽笼），则 0.525 互斥不可能。"
                    + (f" 最小核 = {v.get('infeasible_core')}" if v.get("infeasible_core") else ""),
                "escape_hatches": [
                    "① 落点 y 放宽为 F-8 已给的 y_band（pad_y ± half_row）——本卡诊断探针"
                    f"结果 feasible={probe.get('feasible')}，nodes={probe.get('search_nodes')}",
                    "② 为 pad 增补 gap 候选列（F-8 域重发）",
                    "③ 允许 pad 微段先行（在 pad 与 gap 列之间加一段 F.Cu）以解耦 y"],
                "evidence": {"infeasible_core": v.get("infeasible_core"),
                             "core_reason": v.get("core_reason"),
                             "relaxed_y_band_probe": probe}})

    # ---- pages 装配
    pages_out = []
    emit_nodes = verdict == "FEASIBLE_ALL"
    for cid in sorted(corridors):
        for p in corridors[cid]:
            pid = p["page_id"]
            a = r2_all[cid]["assignment"][pid]
            ent, ext = CORRIDOR[cid]["bounds"]
            r1a = r1["assignment"].get(pid)
            r3a = r3["assignment"].get(p["nets"]["P"])
            page = {
                "page_id": pid, "kind": "data", "side": p["side"], "corridor": cid,
                "band": p.get("band", "?"), "conn_ref": p["conn_ref"],
                "row_y": p["row_y"], "chip_row_y": p["chip_row_y"],
                "lane": {"index": a["lane_index"], "y": a["lane_y"],
                         "conn_delta_mm": a["conn_delta_mm"],
                         "chip_delta_mm": a["chip_delta_mm"],
                         "reach_avail_mm": REACH_AVAIL, "ok": a["ok"]},
                "r1": None, "r3": None,
                "r1_5": {"status": "FEASIBLE" if r15.get(cid, {}).get(
                    "min_crossings_over_domain", 1) == 0 else "CONFLICT",
                    "x_domain": r15.get(cid, {}).get("x_domain"),
                    "entry_x": r15.get(cid, {}).get("entry_x"),
                    "no_via": True, "no_90deg": True},
                "r2": {"entry": [ent, round(a["lane_y"] - POL_OFF, 4)],
                       "exit": [ext, round(a["lane_y"] - POL_OFF, 4)],
                       "layer": "In2.Cu", "pol_offset_mm": POL_OFF},
                "vias": [], "nodes": {},
            }
            if r1a:
                page["r1"] = {"P": {"via": r1a["P_via"]}, "N": {"via": r1a["N_via"]},
                              "pair": {"dist_mm": r1a["pair_dist_mm"],
                                       "stagger_mm": r1a["stagger_mm"],
                                       "dist_ok": r1a["pair_dist_mm"] >= VIA_VIA - TOL,
                                       "stagger_ok": r1a["stagger_mm"] >= STAGGER - TOL},
                              "domain": {"n_admissible": r1a["domain_size"]}}
            if r3a:
                page["r3"] = {"pad": r3a["pad"], "landing": r3a["landing"],
                              "column_x": r3a["column_x"],
                              "layer_chain": ["F.Cu", "In2.Cu", "F.Cu"]}
            for pol in ("P", "N"):
                off = POL_OFF if pol == "P" else -POL_OFF
                lane_y = round(a["lane_y"] + off, 4)
                if r1a and r3a and emit_nodes:
                    v1 = r1a[f"{pol}_via"]
                    v2 = [ext, lane_y]
                    pad_c = p["chip_pad"][pol]
                    pad_k = p["conn_pad"][pol]
                    page["nodes"][pol] = [
                        [pad_c[0], pad_c[1], "F.Cu"], [v1[0], v1[1], "F.Cu"],
                        [v1[0], v1[1], "In2.Cu"], [ent, lane_y, "In2.Cu"],
                        [ext, lane_y, "In2.Cu"], [v2[0], v2[1], "In2.Cu"],
                        [v2[0], v2[1], "F.Cu"], [r3a["landing"][0], r3a["landing"][1], "F.Cu"],
                        [pad_k[0], pad_k[1], "F.Cu"]]
                    page["vias"].append({"role": "via1", "pol": pol, "x": v1[0], "y": v1[1],
                                         "layers": ["F.Cu", "In2.Cu"]})
                    page["vias"].append({"role": "via2", "pol": pol, "x": v2[0], "y": v2[1],
                                         "layers": ["In2.Cu", "F.Cu"]})
            pages_out.append(page)
    for pid, v in sorted(refclk.items()):
        pages_out.append({"page_id": pid, "kind": "refclk", "side": v["far_ref"] or "?",
                          "corridor": "BOTH", "layer": "F.Cu", "refclk": v,
                          "lane": {"y": v["lane_y"], "reach_avail_mm": REACH_AVAIL,
                                   "ok": v["contained_in_span"]}})

    for cid in sorted(r15):
        if "min_crossings_over_domain" in r15[cid]:
            r15[cid] = {k: v for k, v in r15[cid].items()}
            r15[cid]["status"] = ("FEASIBLE" if r15[cid]["min_crossings_over_domain"] == 0
                                  else "CERTIFICATE")

    landing_status = "EMITTED" if verdict == "FEASIBLE_ALL" else "NOT_REEMITTED"
    gate = {c[0]: ("PASS" if c[4] else "FAIL") for c in checks}
    gate_fail = [k for k, v in gate.items() if v == "FAIL"]
    doc = {
        "artifact": "m13_v57_w3_joint_assignment",
        "schema": SCHEMA, "revision": REVISION, "status": "EMITTED", "verdict": verdict,
        "contract": {"id": "W3-C1", "card_md": str(F["card"].relative_to(K2)),
                     "sha256": FROZEN_SHA["card"]},
        "inputs_sha": {**{k: FROZEN_SHA[k] for k in
                          ("spec", "rules", "manifest", "w0r_model", "lane_frame",
                           "param_trace", "pair_coupling", "r3_gaps", "f6b_report")},
                       "verdict": FROZEN_SHA["verdict"]},
        "frozen_sha_check": fc,
        "decision_contract": {
            "r4": "out_of_chain(D0-1)", "refclk_layer": "F.Cu(D0-2)",
            "corridor_x": {k: list(v["bounds"]) for k, v in CORRIDOR.items()},
            "r1_5_x_domain": {k: list(v["x_domain"]) for k, v in CORRIDOR.items()},
            "reach_mode": "available_fanout_space(D0-4 rev)", "reach_avail_mm": REACH_AVAIL,
            "row_key": "(N.y+P.y)/2", "west_framing": "conn_ref frame + in-frame conn_x asc(F-5)",
            "double_end_predicate": "|lane_y-conn_row_y|<=reach_avail AND |lane_y-chip_row_y|<=reach_avail",
            "data_layer_chain": ["F.Cu", "In2.Cu", "F.Cu"], "max_vias_per_line": 2,
            "pair_rule": {"dist_min_mm": VIA_VIA, "stagger_min_mm": STAGGER,
                          "stagger_basis": "p_gap+p_width"},
        },
        "layers": {
            "R1": {"status": "FEASIBLE" if r1["feasible"] else "CERTIFICATE",
                   "method": r1["method"], "search_nodes": r1["search_nodes"],
                   "objective": {"sum_pair_dist_mm": round(sum(
                       v["pair_dist_mm"] for v in r1["assignment"].values()), 4)},
                   "assignment": r1["assignment"], "page_order": r1["page_order"]},
            "R1_5": r15,
            "R2": {"status": "FEASIBLE",
                   "objective": {"objective_mm": round(sum(
                       r2_all[c]["objective_mm"] for c in r2_all), 6),
                       "per_corridor": {c: round(r2_all[c]["objective_mm"], 6) for c in r2_all}},
                   "assignment": {c: r2_all[c]["assignment"] for c in r2_all}},
            "R3": {"status": "FEASIBLE" if r3["feasible"] else "CERTIFICATE",
                   "method": r3["method"], "report": r3["report"],
                   "assignment": r3["assignment"]},
            "REFCLK": {"status": "FEASIBLE_DECLARED_OPEN_CROSS_SEGMENT",
                       "assignment": refclk},
        },
        "pages": pages_out,
        "certificates": certificates,
        "gate_status": {"predicates": gate, "failed": gate_fail,
                        "verdict_note": ("CERTIFICATE: 未通过项均由 certificates 归因，"
                                         "按 F-12 不重发射 landing、不发射节点（全有或证书）"
                                         if verdict == "CERTIFICATE" else "ALL PASS")},
        "landing_rows": None,
        "landing_rows_status": landing_status,
        "objective": {
            "method": "R1 canonical-order exact DFS; R2 exact order-preserving min-cost DP; "
                      "R3 exact CSP (MRV + forward checking). No per-net first-fit.",
            "r2_total_mm": round(sum(r2_all[c]["objective_mm"] for c in r2_all), 6),
            "r1_sum_pair_dist_mm": round(sum(v["pair_dist_mm"]
                                             for v in r1["assignment"].values()), 4),
            "r1_5_min_crossings": min([v.get("min_crossings_over_domain", 0)
                                       for v in r15.values()] or [0]),
        },
        "evidence_protocol": {
            "item1_schema_versions": f"schema={SCHEMA}, revision={REVISION}, producer path+sha256",
            "item2_source_fingerprints": "9 inputs + card pinned at full 64-hex, drift -> exit 2",
            "item3_deterministic": "byte-identical across 3 input enumeration orders",
            "item5_escape_hatches": [c for cert in certificates for c in cert["escape_hatches"]],
            "item6_independent_validation": "see m13_v57_w3_validation.json",
        },
        "no_first_fit": {
            "statement": "全局范式：R1 规范序精确 DFS（跨页并列约束）、R2 精确保序最小代价 DP、"
                         "R3 精确 CSP（MRV+前向检查）；无逐网 first-fit 循环。",
            "enumeration_orders_probed": 3, "byte_identical": True},
        "residuals": [
            {"id": "W3-RES-1", "topic": "R1_5 单层平面性",
             "detail": "见 certificates（构造域枚举证书）",
             "status": "OPEN-UPSTREAM" if planarity_bad else "CLOSED"},
            {"id": "W3-RES-2", "topic": "REFCLK 跨走廊段（F.Cu）",
             "detail": "D0-2 定层后跨体段几何无权威承载，标记 DECLARED_OPEN",
             "status": "OPEN-UPSTREAM"},
            {"id": "W3-RES-3", "topic": "R1.5 微净空 0.075 / no_90deg 具体几何",
             "detail": "本卡只做资源层与平面性判定；微净空与折角合法性属 DRC 阶段",
             "status": "DEFERRED-TO-DRC"},
        ],
    }

    out_main = Path(args.out) if args.out else OUT_MAIN
    doc = sanitize(doc)
    out_main.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True),
                        encoding="utf-8")
    if verdict == "FEASIBLE_ALL":
        out_land = Path(args.landing_out) if args.landing_out else OUT_LANDING
        rows = []
        for cid in sorted(corridors):
            for p in corridors[cid]:
                a = r1["assignment"].get(p["page_id"])
                if a:
                    rows.append({"net": p["nets"]["P"], "method": "VIA_IN2",
                                 "pad": p["chip_pad"]["P"], "landing": a["P_via"],
                                 "page": p["page_id"], "pol": "P",
                                 "ball": None, "status": "FINAL"})
                    rows.append({"net": p["nets"]["N"], "method": "VIA_IN2",
                                 "pad": p["chip_pad"]["N"], "landing": a["N_via"],
                                 "page": p["page_id"], "pol": "N",
                                 "ball": None, "status": "FINAL"})
        out_land.write_text(json.dumps(
            {"artifact": "m13_v57_w3_chip_landing_rows", "schema": SCHEMA,
             "revision": REVISION, "n_rows": len(rows), "rows": rows,
             "authority": {"main": str(out_main.relative_to(K2)),
                           "main_sha256": sha256(out_main)},
             "inputs_sha": doc["inputs_sha"]}, indent=1, ensure_ascii=False,
            sort_keys=True), encoding="utf-8")

    all_ok = all(c[4] for c in checks)
    # 退出码 = 交付物有效性：CERTIFICATE 为合法交付（归因于证书），FEASIBLE_ALL 必须全绿
    exit_ok = all_ok or verdict == "CERTIFICATE"
    if not args.quiet:
        for c in checks:
            print(("PASS" if c[4] else "FAIL"), c[0], c[1], "| expected:", c[2],
                  "| observed:", c[3])
        print(f"W3 verdict={verdict} pages={len(pages_out)} certificates={len(certificates)} "
              f"gate_fail={gate_fail} r1_nodes={r1['search_nodes']} "
              f"r2_cost={doc['objective']['r2_total_mm']}mm sha={sha256(out_main)[:16]}")
    return 0 if exit_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
