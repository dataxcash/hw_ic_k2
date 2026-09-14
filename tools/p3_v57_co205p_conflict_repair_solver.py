#!/usr/bin/env python3
"""CO-205p（L2 自裁 · 层分配重指派联合求解）—— **冲突导向修复**（conflict-directed ejection）。

回答 handoff z70 §6(A)：候选 C（F 双孔桥，lane 保持 In5）在 4 信号层内是否存在 32/32 联合解？
与 CO-205n（逐行首可行贪心 + **空间最近邻**驱逐）的关键差异：
  1. 驱逐目标是 **check() 实际报出的冲突页**（err 标签），非空间最近邻；冲突集随每次试放累积。
  2. 候选 = 行（pair_rows）× **桥孔几何模式**（cx：P/N 同向 / 离对偶 / 向对偶；sy：落桥竖直 jog）。
  3. 递归深度受限、确定性键序、零随机；每次试放用增量 Store（push/pop），不整表重建。

只读消费冻结四源；canonical 工件零改动。探针侧新增只读旋钮 CO10_BRMAP / CO10_LMAP（默认 {} ⇒ 逐字节可复现）。
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, sys, time
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
BASE_ENV = {
    "CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json", "CO10_STEP": "1.449",
    "CO10_WSTEP": "1.07", "CO10_WLO": "33.70", "CO10_FANY_J3": "34.5,51.5",
    "CO10_STUB": "J3L", "CO10_POLMODE": "lx", "CO10_EASTSPLIT": "in2c",
    "CO10_J2STEP": "0.58", "CO10_COLMODE": "pol", "CO10_WSWAP": "1-11",
    "CO10_HOLE_GAP": "0.4495", "CO10_LXPRIO": "landlen", "CO10_IP3W": "1",
    "CO10_FAN_STRAT": "carry", "CO10_PDN_OBS": "1", "CO10_EDELTA": "-0.10",
}

P = None
_BRMAP_BACKUP = {}


def load_probe(over=None):
    env = dict(BASE_ENV)
    if over:
        env.update({k: str(v) for k, v in over.items()})
    os.environ.update(env)
    spec = importlib.util.spec_from_file_location("probe", str(K2 / "tools/p3_v57_co10_west_fan_probe.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.R3 = m.r3_build("d3")
    m.ALLOC = m.alloc_closed_form()
    m._IP3W_TGT = m._ip3w_targets() if m._IP3W else {}
    return m


def mark(st):
    return (len(st.vx), len(st.vlab), {l: len(st.S[l]) for l in st.LAYERS},
            {l: len(st.SLAB[l]) for l in st.LAYERS})


def rollback(st, mk):
    nv, nl, ns, nsl = mk
    st.vx = st.vx[:nv]; st.vy = st.vy[:nv]; st.vm = st.vm[:nv]
    st.vlab = st.vlab[:nl]
    for l in st.LAYERS:
        st.S[l] = st.S[l][:ns[l]]
        st.SP[l] = st.SP[l][:ns[l]]
        st.SLAB[l] = st.SLAB[l][:nsl[l]]


def rows_for(P, pid, cap):
    f = P.FACTS[pid]
    tgt = P.ALLOC.get((pid, "P")), P.ALLOC.get((pid, "N"))
    txp, typ = (tgt[0] if tgt[0] else (f["pad"]["P"][0], f["pad"]["P"][1]))
    txn, tyn = (tgt[1] if tgt[1] else (f["pad"]["N"][0], f["pad"]["N"][1]))
    out = []
    for r in P.PAIR_DOMAIN[pid]["pair_rows"]:
        px, nx, py, ny, dd = (float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]))
        if dd < P.VV - P.TOL or abs(px - nx) < 0.38 - P.TOL:
            continue
        if abs(py - f["pad"]["P"][1]) > P.YWIN or abs(ny - f["pad"]["N"][1]) > P.YWIN:
            continue
        out.append((px, nx, py, ny))
    out.sort(key=lambda t: (abs(t[0] - txp) + abs(t[1] - txn) + abs(t[2] - typ) + abs(t[3] - tyn),
                            t[0], t[1]))
    return out[:cap]


def static_rows(P, pid):
    f = P.FACTS[pid]
    tp = P._IP3W_TGT.get(pid)
    bx = P._BOFF if f["band"] == "up" else -P._BOFF
    txp = (tp[1] if tp else f["pad"]["P"][0]) + bx
    txn = (tp[0] if tp else f["pad"]["N"][0]) + bx
    by = P.y_bias(f)
    out = []
    for r in P.PAIR_DOMAIN[pid]["pair_rows"]:
        px, nx, py, ny, dd = (float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]))
        if dd < P.VV - P.TOL or abs(px - nx) < 0.38 - P.TOL:
            continue
        if abs(py - f["pad"]["P"][1]) > P.YWIN or abs(ny - f["pad"]["N"][1]) > P.YWIN:
            continue
        out.append((px, nx, py, ny))
    out.sort(key=lambda t: (abs(t[0] - txp) + abs(t[1] - txn)
                            + abs(t[2] - (f["pad"]["P"][1] + by))
                            + abs(t[3] - (f["pad"]["N"][1] + by)), t[0], t[1]))
    return out


def probe_rows(P, order_name, cap):
    """用探针自身的落位顺序（含 carry 列序语义）作候选序：首可行 ⇒ 与探针逐页同解。"""
    log = {}
    orig = P.build

    def logged(f, px, py, nx, ny):
        b = orig(f, px, py, nx, ny)
        log.setdefault(f["page_id"], []).append((px, nx, py, ny))
        return b

    P.build = logged
    try:
        res = P.probe("fan", order_name, False)
    finally:
        P.build = orig
    rows = {}
    for pid in P.FACTS:
        seq, seen = [], set()
        pl = res["placed"].get(pid)          # 探针本页所取行 ⇒ 置首（保证种子与探针逐页同解）
        if pl is not None:
            seq.append((pl["P_via"][0], pl["N_via"][0], pl["P_via"][1], pl["N_via"][1]))
            seen.add(seq[0])
        for r in log.get(pid, []):
            if r not in seen:
                seen.add(r); seq.append(r)
        for r in static_rows(P, pid):
            if r not in seen:
                seen.add(r); seq.append(r)
        rows[pid] = seq[:cap]
    return rows, res


def patterns_for(P, pid):
    """桥孔几何自由度（仅当该页 E==In2 / S==In2 时生效；否则无害）。确定性序。"""
    f = P.FACTS[pid]
    need_c = P.esc_layer(f) == "In2.Cu"
    need_s = P.stub_layer(f) == "In2.Cu"
    cx_modes = []
    if need_c:
        cx_modes = [(None, None), (0.5, -0.5), (-0.5, 0.5), (0.7, -0.7), (-0.7, 0.7)]
    else:
        cx_modes = [(None, None)]
    sy_modes = []
    if need_s:
        sy_modes = [(None, None), (0.5, -0.5), (-0.5, 0.5), (0.7, -0.7), (-0.7, 0.7)]
    else:
        sy_modes = [(None, None)]
    out = []
    for cp, cn in cx_modes:
        for sp, sn in sy_modes:
            m = {}
            if cp is not None:
                m["cx"] = {"P": cp, "N": cn}
            if sp is not None:
                m["sy"] = {"P": sp, "N": sn}
            out.append(m)
    return out


def page_of(label):
    s = str(label)
    i = s.rfind(".")
    return s[:i] if i > 0 else s


def build_at(P, pid, row, pat):
    P._BRMAP = {pid: pat} if pat else {}
    b = P.build(P.FACTS[pid], row[0], row[2], row[1], row[3])
    P._BRMAP = {}
    return b


def try_place(P, st, pid, rows, pats, max_probe):
    """返回 (cfg, conflicts)。cfg=(row,pat,b) 首个可行；否则 conflicts=冲突页集合。"""
    conflicts = set()
    n = 0
    for pat in pats:            # 模式外层：首选 = 探针默认几何（保种子与探针逐页同解），几何变体为后备
        for row in rows:
            b = build_at(P, pid, row, pat)
            if b is None:
                continue
            n += 1
            err = P.check(*b, st, pid)
            if err is None:
                return (row, pat, b), conflicts
            try:
                conflicts.add(page_of(err[-2]))
            except Exception:
                pass
            if n >= max_probe:
                return None, conflicts
    return None, conflicts


def push(st, cfg, pid):
    st.add(cfg[2][0], cfg[2][1], pid)


def default_orders(P):
    F = P.FACTS
    return {
        "rev": sorted(F, key=lambda p: (F[p]["corridor"], F[p]["conn_ref"], F[p]["band"], p), reverse=True),
        "carry": sorted(F, key=lambda p: (F[p]["corridor"], F[p]["band"], F[p]["conn_ref"], p)),
        "xasc": sorted(F, key=lambda p: (F[p]["corridor"], F[p]["conn_ref"], F[p]["band"],
                                         min(F[p]["pad"]["N"][0], F[p]["pad"]["P"][0]), p)),
        "fewest": sorted(F, key=lambda p: (len(P.PAIR_DOMAIN[p]["pair_rows"]), p)),
    }


def greedy(P, order, rows, pats, max_probe):
    st = P.Store()
    if P._PDN_OBS:
        P._seed_pdn(st)
    placed, failed = {}, {}
    for pid in order:
        cfg, conf = try_place(P, st, pid, rows[pid], pats[pid], max_probe)
        if cfg is None:
            failed[pid] = sorted(conf)
            continue
        placed[pid] = cfg
        push(st, cfg, pid)
    return st, placed, failed


def attempt_add(P, order, rows, pats, sel, pid, d, max_probe, deadline, stat):
    """把 pid 放入 sel；冲突时**定向驱逐**冲突页（深度 d）。返回新 sel 或 None。"""
    if time.time() > deadline:
        return None
    st = P.Store()
    if P._PDN_OBS:
        P._seed_pdn(st)
    for q in order:
        if q in sel:
            push(st, sel[q], q)
    stat["try"] += 1
    cfg, conf = try_place(P, st, pid, rows[pid], pats[pid], max_probe)
    if cfg is not None:
        out = dict(sel); out[pid] = cfg
        return out
    if d <= 0:
        return None
    cand = [q for q in order if q in sel and q in conf and q != pid]
    for q in cand:
        sub = {k: v for k, v in sel.items() if k != q}
        stat["eject"] += 1
        got = attempt_add(P, order, rows, pats, sub, pid, d - 1, max_probe, deadline, stat)
        if got is not None:
            return got
    return None


def solve(P, order, rows, pats, depth, max_probe, budget, verbose=True):
    t0 = time.time(); deadline = t0 + budget
    stat = {"try": 0, "eject": 0}
    st = P.Store()
    if P._PDN_OBS:
        P._seed_pdn(st)
    placed, failed = {}, {}
    for pid in order:
        cfg, conf = try_place(P, st, pid, rows[pid], pats[pid], max_probe)
        if cfg is None:
            failed[pid] = sorted(conf)
            continue
        placed[pid] = cfg
        push(st, cfg, pid)
    best = dict(placed)
    if verbose:
        print(f"[seed] {len(placed)}/{len(order)} failed={sorted(failed)} ({time.time()-t0:.0f}s)", flush=True)
    stagnant = 0
    for rnd in range(1, 80):
        if len(placed) >= len(order) or time.time() > deadline:
            break
        residual = [p for p in order if p not in placed]
        # 最难优先：候选少/先失败者先放（确定性键序）
        residual.sort(key=lambda q: (len(rows[q]) * len(pats[q]), q))
        progressed = False
        for pid in residual:
            if time.time() > deadline:
                break
            if pid in placed:
                continue
            got = attempt_add(P, order, rows, pats, placed, pid, depth, max_probe, deadline, stat)
            if got is None:
                continue
            if len(got) > len(placed):
                progressed = True
            placed = got
        if len(placed) > len(best):
            best = dict(placed)
            if verbose:
                print(f"[round {rnd}] {len(placed)}/{len(order)} "
                      f"residual={[p for p in order if p not in placed]} "
                      f"({time.time()-t0:.0f}s try={stat['try']} ej={stat['eject']})", flush=True)
        if not progressed:
            stagnant += 1
            if stagnant >= 2:
                if verbose:
                    print(f"[round {rnd}] stagnant at {len(placed)}/{len(order)} "
                          f"({time.time()-t0:.0f}s try={stat['try']} ej={stat['eject']})", flush=True)
                break
        else:
            stagnant = 0
    return best, round(time.time() - t0, 1), stat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="C", choices=["C", "B"])
    ap.add_argument("--orders", default="rev,carry,xasc,fewest")
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--max-probe", type=int, default=4000)
    ap.add_argument("--budget", type=float, default=180.0)
    ap.add_argument("--out", default="/tmp/co205p_solve.json")
    a = ap.parse_args()
    over = {"CO10_BRIDGE": "1", "CO10_SPAN": "1", "CO10_BRJOG": "0.5"}
    if a.mode == "B":
        over["CO10_V2B"] = "1"
        over.pop("CO10_BRIDGE", None)
    global P
    P = load_probe(over)
    rows_all = {}; pats = {}
    t0 = time.time()
    orders = default_orders(P)
    probe_name = {"rev": "rev", "carry": "carry", "xasc": "xasc", "fewest": "fewest"}
    for name in [s.strip() for s in a.orders.split(",") if s.strip()]:
        pn = probe_name.get(name)
        if pn is None:
            continue
        rr, _res = probe_rows(P, pn, a.cap)
        rows_all[name] = rr
    if not rows_all:
        rows_all["rev"], _ = probe_rows(P, "rev", a.cap)
        orders = {"rev": orders["rev"]}
    for pid in P.FACTS:
        pats[pid] = patterns_for(P, pid)
    rows = rows_all
    if not os.environ.get("CO205P_QUIET"):
        _k = next(iter(rows))
        print(f"[prep] orders={sorted(rows)} rows/pat avg={sum(len(rows[_k][p]) for p in rows[_k])/len(rows[_k]):.0f}/"
              f"{sum(len(pats[p]) for p in pats)/len(pats):.1f} ({time.time()-t0:.0f}s)", flush=True)
    best_all = None
    for name in [s.strip() for s in a.orders.split(",") if s.strip()]:
        order = orders.get(name)
        if order is None or name not in rows:
            continue
        b, el, syn = solve(P, order, rows[name], pats, a.depth, a.max_probe, a.budget)
        n = len(b)
        print(f"[{name}] {n}/{len(order)} ({el}s syn={syn})", flush=True)
        if best_all is None or n > best_all[1]:
            best_all = (name, n, order, b)
        if n == len(order):
            break
    name, n, order, b = best_all
    doc = {"solver": "CO-205p conflict-directed repair", "mode": a.mode, "order": name,
           "n_placed": n, "n_pages": len(order), "residual": [p for p in order if p not in b],
           "assignment": {p: {"row": [round(v, 4) for v in b[p][0]], "brmap": b[p][1]} for p in b}}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"CO-205p {a.mode}: best {n}/{len(order)} order={name} residual={doc['residual']} -> {a.out}")
    return 0 if n == len(order) else 1


if __name__ == "__main__":
    raise SystemExit(main())
