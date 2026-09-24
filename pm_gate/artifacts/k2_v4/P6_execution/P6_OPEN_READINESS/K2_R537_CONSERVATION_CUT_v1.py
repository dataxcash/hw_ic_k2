#!/usr/bin/env python3
"""K2 · R537 —— **闭式守恒核算 / 割证书**（#K2-203 §三.4 / §四② · **0 受证配额** · 纯计数 · 不用求解器）。
对最小冲突三元 T={OUT0_P,OUT4_P,OUT2_P}：枚举**全部在册格点割**（每列/每行，两层的节点集），
对每割算**容量上界** = 该割上(两层)可为这几条线所用的格点里、**同层 >=2 格间距** 的最大并行数之和；
与**需求**（该割把几条线的 A 锚与 B 锚分开 ⇒ 这几条必须都过割）比较：
  · 若存在割使 `容量上界 < 需求` ⇒ **硬墙证书**（逐割可核：割号 + 可用位 + 需求）；
  · 若所有割都 `容量上界 >= 需求` ⇒ 单割容量**不构成**墙 ⇒ 张力方向（附最小放开清单候选）。
`容量上界` 是**上界**（真实可用 ≤ 上界），故 `上界 < 需求` 是**充分**的硬墙证明（不需要求解器）。"""
import argparse, importlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
OWN_OUT = "K2_R537_CONSERVATION_CUT_v1.json"
T = ["PCIE_UP_OUT0_P_J2", "PCIE_UP_OUT4_P_J2", "PCIE_UP_OUT2_P_J2"]


def pack2(sorted_unique):
    """max count of positions pairwise >= 2 apart (greedy is optimal for this constraint)."""
    last = None; n = 0
    for p in sorted_unique:
        if last is None or p - last >= 2:
            n += 1; last = p
    return n


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    t0 = time.time()
    rep = {"artifact": "k2_r537_conservation_cut_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-203 sec.3.4 / sec.4 (closed-form conservation audit + cut certificate; ZERO quota; "
                        "counting only, NO solver)",
           "certified_solve_calls": 0, "triple": T}
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    own = {nm: {L: g2._nok[(nm, L)] for L in (0, 1)} for nm in T}
    anc = {nm: {"A": (int(round((g2.A[nm][0] - X0) / P)), int(round((g2.A[nm][1] - Y0) / P))),
                "B": (int(round((g2.B[nm][0] - X0) / P)), int(round((g2.B[nm][1] - Y0) / P)))} for nm in T}
    rep["anchors_lattice"] = anc
    findings = []
    best = None   # tightest slack = capacity_ub - demand
    for axis in ("col", "row"):
        rng = range(NX) if axis == "col" else range(NY)
        for idx_ in rng:
            sep = []
            for nm in T:
                a1 = anc[nm]["A"][0 if axis == "col" else 1]; b1 = anc[nm]["B"][0 if axis == "col" else 1]
                if (a1 - idx_) * (b1 - idx_) < 0:
                    sep.append(nm)
            if not sep:
                continue
            cap = 0; pos_lists = {}
            for L in (0, 1):
                pts = set()
                for nm in sep:
                    if axis == "col":
                        for j in range(NY):
                            if own[nm][L][idx_ * NY + j]:
                                pts.add(j)
                    else:
                        for i in range(NX):
                            if own[nm][L][i * NY + idx_]:
                                pts.add(i)
                pos_lists["L%d_n_positions" % L] = len(pts)
                cap += pack2(sorted(pts))
            row = {"axis": axis, "index": idx_, "separated_lanes": sep, "demand": len(sep),
                   "capacity_upper_bound": cap, "slack": cap - len(sep), "positions": pos_lists}
            findings.append(row)
            if best is None or row["slack"] < best["slack"]:
                best = row
    rep["n_cuts_checked"] = len(findings)
    rep["tightest_cut"] = best
    walls = [f for f in findings if f["slack"] < 0]
    rep["cut_certificates_of_wall"] = walls[:20]
    rep["verdict"] = {
        "hard_wall_certificate_found": bool(walls),
        "binary": ("HARD WALL (certified: some cut has capacity_upper_bound < demand)" if walls
                   else "NO single-cut wall found => TENSION DIRECTION (movable/reroutable): all %d lattice cuts "
                        "have capacity_upper_bound >= demand" % len(findings)),
        "note": ("capacity_upper_bound is an UPPER bound (real capacity <= it), so wall evidence is sound; the "
                 "absence of a single-cut wall does NOT by itself prove routability (multi-cut/joint effects), "
                 "it only rules out the single-cut conservation wall and points to the tension class."),
        "min_slack_over_cuts": best}
    rep["minimal_relaxation_candidates"] = {
        "note": "for the supervisor only (NOT self-applied); in-register authorisations must be cited",
        "candidates": ["per-lane via budget (in-register MAX_VIA_PAIRS = 2) raised for this triple",
                       "the section slots of the R529 complete master for these lanes slid/reselected",
                       "the allowed via-zone set (in-register: the four wide zones) widened for this triple"]}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] cuts checked:", len(findings), "| tightest:", json.dumps(best, ensure_ascii=False)[:300], flush=True)
    print("[stage] wall certs:", len(walls), "| verdict:", rep["verdict"]["binary"][:160], flush=True)
    print("WROTE", a.out, flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc()
        print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True)
        sys.exit(3)
