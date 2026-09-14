#!/usr/bin/env python3
"""CO-205n（L2 自裁）：层分配重指派 **联合求解器**（候选 C 家族 + 逐页桥孔几何自由度）。

回答 handoff z70 §6(A)：在现行 4 信号层内、候选 C（F 桥）拓扑族里是否存在 32/32 联合解？
单遍逐行首可行贪心卡在 24/32（8 个 E=In2 页：桥孔拥塞）。本件把「列（pair row）×
桥孔错位（cx 角桥 / sy 落桥，逐页逐极性）」作为**联合变量**，用真实判据（probe.check，
含 span 面跨层 + PDN 固定障碍）做 **ejection-chain 邻域修复**（确定性键序，零随机）。

  - seed = probe 现行贪心（24/32），保留其 carry 列序语义。
  - 对未落位页：先试候选 (row × pattern)；失败则驱逐空间最近邻并把「被驱逐页 + 本页」
    一起重解，深度受限（确定性，最近邻优先）。
  - 只读消费冻结四源；零 canonical 修改。CO10_BRMAP 为探针只读旋钮（默认 {} 关闭）。
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, time
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")

BASE_ENV = {
    "CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json", "CO10_STEP": "1.449",
    "CO10_WSTEP": "1.07", "CO10_WLO": "33.70", "CO10_FANY_J3": "34.5,51.5",
    "CO10_STUB": "J3L", "CO10_POLMODE": "lx", "CO10_EASTSPLIT": "in2c",
    "CO10_J2STEP": "0.58", "CO10_COLMODE": "pol", "CO10_WSWAP": "1-11",
    "CO10_HOLE_GAP": "0.4495", "CO10_LXPRIO": "landlen", "CO10_IP3W": "1",
    "CO10_FAN_STRAT": "carry", "CO10_PDN_OBS": "1", "CO10_EDELTA": "-0.10",
    "CO10_BRIDGE": "1", "CO10_SPAN": "1", "CO10_BRJOG": "0.5",
}

CX_PATS = [None, (-0.7, -0.7), (-0.35, -0.35), (0.35, 0.35), (0.7, 0.7),
           (0.7, -0.7), (-0.7, 0.7), (-0.7, 0.0), (0.0, -0.7), (0.7, 0.0), (0.0, 0.7),
           (-0.5, 0.5), (0.5, -0.5), (-0.2, -0.7), (-0.7, -0.2), (0.2, 0.7), (0.7, 0.2)]
SY_PATS = [None, (-0.7, -0.7), (-0.35, -0.35), (0.35, 0.35), (0.7, 0.7),
           (0.7, -0.7), (-0.7, 0.7), (-0.2, -0.2), (0.5, 0.5), (-0.7, 0.0), (0.0, -0.7),
           (0.7, 0.0), (0.0, 0.7)]


_BUILD_LOG = None


def load_probe(env_over: dict | None = None):
    for k, v in BASE_ENV.items():
        os.environ.setdefault(k, v)
    if env_over:
        os.environ.update({k: str(v) for k, v in env_over.items()})
    spec = importlib.util.spec_from_file_location("probe", str(K2 / "tools/p3_v57_co10_west_fan_probe.py"))
    P = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(P)
    P.R3 = P.r3_build("d3")
    P.ALLOC = P.alloc_closed_form()
    P._IP3W_TGT = P._ip3w_targets() if P._IP3W else {}
    P._BRMAP = {}
    _orig_build = P.build

    def _logged_build(f, px, py, nx, ny):
        b = _orig_build(f, px, py, nx, ny)
        if _BUILD_LOG is not None:
            _BUILD_LOG.setdefault(f["page_id"], []).append((px, nx, py, ny))
        return b

    P.build = _logged_build
    return P


def static_rows(P, pid, cap):
    f = P.FACTS[pid]
    VV, TOL, YWIN = P.VV, P.TOL, P.YWIN
    out = []
    for r in P.PAIR_DOMAIN[pid]["pair_rows"]:
        px, nx, py, ny, dd = (float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]))
        if dd < VV - TOL or abs(px - nx) < 0.38 - TOL:
            continue
        if abs(py - f["pad"]["P"][1]) > YWIN or abs(ny - f["pad"]["N"][1]) > YWIN:
            continue
        out.append((px, nx, py, ny))
    by = P.y_bias(f)
    out.sort(key=lambda t: (abs(t[0] - f["pad"]["P"][0]) + abs(t[1] - f["pad"]["N"][0])
                            + abs(t[2] - (f["pad"]["P"][1] + by)) + abs(t[3] - (f["pad"]["N"][1] + by)),
                            t[0], t[1]))
    return out[:cap]


def patterns_for(P, f, mode):
    """mode='C'：候选 C（run=In5）桥孔错位自由度；mode='B'：候选 B（run=B.Cu）竖段着色自由度。"""
    if mode == "B":
        out = [{}]
        for esc in ("In2.Cu", "In5.Cu"):
            for stub in ("In2.Cu", "In5.Cu"):
                out.append({"lmap": {"esc": esc, "stub": stub}})
        return out
    need_c = P.esc_layer(f) == "In2.Cu"
    need_s = P.stub_layer(f) == "In2.Cu"
    cg = CX_PATS if need_c else [None]
    sg = SY_PATS if need_s else [None]
    out = []
    for cp in cg:
        for sp in sg:
            m = {}
            if cp is not None:
                m["cx"] = {"P": cp[0], "N": cp[1]}
            if sp is not None:
                m["sy"] = {"P": sp[0], "N": sp[1]}
            out.append({"brmap": m} if m else {})
    return out


def rebuild(P, placed):
    st = P.Store(); P._seed_pdn(st)
    for pid, c in placed.items():
        st.add(c["b"][0], c["b"][1], pid)
    return st


def _apply(P, pid, pat):
    P._BRMAP = {pid: pat["brmap"]} if pat.get("brmap") else {}
    P._LMAP = {pid: pat["lmap"]} if pat.get("lmap") else {}


def try_page(P, st, pid, rows, pats, max_attempts):
    f = P.FACTS[pid]
    n = 0
    for row in rows:
        for pat in pats:
            _apply(P, pid, pat)
            b = P.build(f, row[0], row[2], row[1], row[3])
            if b is None:
                continue
            n += 1
            if P.check(*b, st, pid) is None:
                return {"row": row, "pat": pat, "b": b}
            if n >= max_attempts:
                return None
    return None


def neighbors(P, pid, placed, radius):
    f = P.FACTS[pid]; cx, cy = f["pad"]["P"]
    lst = []
    for q in placed:
        g = P.FACTS[q]; qx, qy = g["pad"]["P"]
        d = math.hypot(qx - cx, qy - cy)
        if d < radius:
            lst.append((round(d, 6), q))
    lst.sort()
    return [q for _, q in lst]


def eject(P, pid, placed, depth, rows, pats, max_attempts, deadline, stats):
    stats["nodes"] += 1
    if time.time() > deadline:
        return None
    cfg = try_page(P, rebuild(P, placed), pid, rows[pid], pats[pid], max_attempts)
    if cfg is not None:
        out = dict(placed); out[pid] = cfg
        return out
    if depth <= 0:
        return None
    for q in neighbors(P, pid, placed, 2.2)[:6]:
        sub = {k: v for k, v in placed.items() if k != q}
        stats["eject"] += 1
        cfg = try_page(P, rebuild(P, sub), pid, rows[pid], pats[pid], max_attempts)
        if cfg is None:
            continue
        sub[pid] = cfg
        got = eject(P, q, sub, depth - 1, rows, pats, max_attempts, deadline, stats)
        if got is not None:
            return got
    return None


def solve(order, cap, time_budget, max_attempts, depth, mode="C", verbose=True):
    global _BUILD_LOG
    P = load_probe()
    t0 = time.time(); deadline = t0 + time_budget
    # seed = 现行贪心（记录其**实际尝试序**，即含 carry 列序语义的候选序）
    _BUILD_LOG = {}
    res = P.probe("fan", order, False)
    logged = _BUILD_LOG
    _BUILD_LOG = None
    rows = {}
    for p in P.FACTS:
        cand = []
        seen = set()
        for r in logged.get(p, []):
            if r not in seen:
                seen.add(r); cand.append(r)
        if len(cand) < 20:
            cand = cand + [r for r in static_rows(P, p, cap) if r not in seen]
        rows[p] = cand[:cap]
    pats = {p: patterns_for(P, P.FACTS[p], mode) for p in P.FACTS}
    placed = {}
    for pid in order:
        if pid not in res["placed"]:
            continue
        pl = res["placed"][pid]
        row = (pl["P_via"][0], pl["N_via"][0], pl["P_via"][1], pl["N_via"][1])
        P._BRMAP = {}; P._LMAP = {}
        b = P.build(P.FACTS[pid], row[0], row[2], row[1], row[3])
        if b is not None:      # seed 由 probe 自身校验过，成对一致 ⇒ 直接入 store
            placed[pid] = {"row": row, "pat": {}, "b": b}
    P._BRMAP = {}; P._LMAP = {}
    if verbose:
        print(f"[seed] {len(placed)}/{len(order)} ({time.time()-t0:.0f}s)", flush=True)
    best = dict(placed); stats = {"nodes": 0, "eject": 0}
    for rnd in range(1, 200):
        if len(placed) >= len(order) or time.time() > deadline:
            break
        unpl = [p for p in order if p not in placed]
        delta = 0
        for pid in unpl:
            if time.time() > deadline:
                break
            got = eject(P, pid, placed, depth, rows, pats, max_attempts, deadline, stats)
            if got is not None:
                placed = got; delta += 1
        if len(placed) > len(best):
            best = dict(placed)
            if verbose:
                print(f"[round {rnd}] {len(placed)}/{len(order)} "
                      f"residual={[p for p in order if p not in placed]} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        if delta == 0:
            if verbose:
                print(f"[round {rnd}] stuck at {len(placed)}/{len(order)} "
                      f"({time.time()-t0:.0f}s)", flush=True)
            break
    P._BRMAP = {}; P._LMAP = {}
    return best, round(time.time() - t0, 1), stats


def default_order(P):
    return sorted(P.FACTS, key=lambda p: (P.FACTS[p]["corridor"], P.FACTS[p]["conn_ref"],
                                          P.FACTS[p]["band"], p), reverse=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", default="rev")
    ap.add_argument("--cap", type=int, default=80)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--max-attempts", type=int, default=20000)
    ap.add_argument("--time-budget", type=float, default=600.0)
    ap.add_argument("--mode", default="C", choices=["B", "C"])
    ap.add_argument("--out", default="/tmp/co205_joint_solve.json")
    a = ap.parse_args()
    P0 = load_probe({"CO10_V2B": "1"} if a.mode == "B" else {})
    if a.order == "rev":
        order = default_order(P0)
    elif a.order == "band_x":
        order = sorted(P0.FACTS, key=lambda p: (P0.FACTS[p]["corridor"], P0.FACTS[p]["band"],
                                                P0.FACTS[p]["pad"]["N"][0], p))
    elif a.order == "carry":
        order = sorted(P0.FACTS, key=lambda p: (P0.FACTS[p]["corridor"], P0.FACTS[p]["band"],
                                                P0.FACTS[p]["conn_ref"],
                                                min(P0.FACTS[p]["pad"]["N"][0], P0.FACTS[p]["pad"]["P"][0]), p))
    else:
        order = sorted(P0.FACTS, key=lambda p: (P0.FACTS[p]["corridor"], P0.FACTS[p]["conn_ref"],
                                                P0.FACTS[p]["band"], P0.FACTS[p]["pad"]["N"][0], p))
    best, el, stats = solve(order, a.cap, a.time_budget, a.max_attempts, a.depth, a.mode)
    doc = {"solver": "CO-205n joint layer-reassign (ejection-chain)", "n_placed": len(best),
           "n_pages": len(order), "residual": [p for p in order if p not in best],
           "elapsed_s": el, "nodes": stats["nodes"], "ejections": stats["eject"], "order": order,
           "assignment": {p: {"row": [round(v, 4) for v in c["row"]], "pat": c.get("pat", {})}
                          for p, c in best.items()}}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"CO-205n joint solve: placed {len(best)}/{len(order)} residual={doc['residual']} "
          f"ejections={stats['eject']} {el}s -> {a.out}")
    return 0 if len(best) == len(order) else 1


if __name__ == "__main__":
    raise SystemExit(main())
