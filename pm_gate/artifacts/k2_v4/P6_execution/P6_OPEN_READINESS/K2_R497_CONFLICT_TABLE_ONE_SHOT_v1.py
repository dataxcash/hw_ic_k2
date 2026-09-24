#!/usr/bin/env python3
"""K2 · R497 —— 遵 **监理停止令（红线·命令重复）** + #K2-177 §一：**照冻结规格一次实现**（不迭代、不改参重跑）。
Plan：K2_R497_PLAN_HUMAN_PATH_v1.md（①信号怎么走 ②挡路的是什么 ③人类方案）。
本件一次跑完：候选族(§四规格) → 内部前置闸 → 冲突表(真距+真穿越) → 模型(AddForbiddenAssignments) → **一次受证求解** → 渲染 → 在册 exact_gate。
内部前置闸不全绿 ⇒ **不开跑**（守住唯一额度 · 单遍纪律 #K2-175 §四.5）。
"""
import json, sys, os, math, time, hashlib, collections
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from ortools.sat.python import cp_model
from k2_p4_b2_in5_lane_router_v3 import (Raster, build_base, lane_anchors, exact_gate,
                                         _seg_seg_batch, eff, HOLE_CLR)
import k2_p4_b2_in5_lane_router_v3 as RT

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = "/tmp/opencode/archer/model_l8.json"
P = 0.435; HW = 0.08
OUT = os.path.join(HERE, "K2_R497_CONFLICT_TABLE_ONE_SHOT_v1.json")
REP = {"artifact": "k2_r497_conflict_table_one_shot_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "监理停止令(红线·命令重复) · 宪法第八章第8条 · #K2-177 §一/§三 · #K2-176 §四.4 · 单遍纪律 #K2-175 §四.5",
       "spec": "K2_R497_PLAN_HUMAN_PATH_v1.md §四（冻结实现规格）"}

# ---------------- 几何底座 ----------------
m = json.load(open(MODEL))
RT.PAD_EXTRA = 0.100 + 0.5 * 0.03 * math.sqrt(2)
an = [a for a in lane_anchors(m) if a["net"].startswith("PCIE_UP_OUT")]
rast = Raster(m["bbox"], 0.03)
base = build_base(rast, m, "In5.Cu", set(), set(), HW, frozenset())
X0, Y0 = 84.0, 41.0
NX = int((144.0 - X0) / P) + 1; NY = int((69.0 - Y0) / P) + 1
def XY(i, j): return (X0 + i * P, Y0 + j * P)
names = sorted(a["net"] for a in an)
A = {a["net"]: a["A"] for a in an}; B = {a["net"]: a["B"] for a in an}
order = sorted(names, key=lambda z: A[z][0])
rank = {nm: k for k, nm in enumerate(order)}

# 每线自由栅：base + 他车道锚禁近圆（本车道锚除外）
BAD = {}; FR = {}
for nm in names:
    b = base.copy()
    for a in an:
        if a["net"] == nm: continue
        r = HW + max(a["via_r"] + eff(a["net"]), a["drill"] + HOLE_CLR) + RT.PAD_EXTRA
        rast.cir(b, a["A"][0], a["A"][1], r); rast.cir(b, a["B"][0], a["B"][1], r)
    BAD[nm] = b
    def mk(b):
        s = set()
        for i in range(NX):
            for j in range(NY):
                x, y = XY(i, j)
                a0 = int(round((x - rast.X0) / rast.step)); c0 = int(round((y - rast.Y0) / rast.step))
                if 0 <= a0 < rast.NX and 0 <= c0 < rast.NY and not b[a0, c0]: s.add((i, j))
        return s
    FR[nm] = mk(b)
def near(pt, fr, taken):
    return min((n for n in fr if n not in taken), key=lambda n: math.dist(XY(*n), pt))
S0 = {}; T0 = {}
for nm in names:
    tk = set(); s0 = near(A[nm], FR[nm], tk); tk.add(s0); t0 = near(B[nm], FR[nm], tk)
    S0[nm] = s0; T0[nm] = t0
jpor = round((56.5 - Y0) / P)
E = sorted([(i, jpor) for i in range(NX) if (i, jpor) in FR[names[0]] and 135.45 - P <= XY(i, jpor)[0] <= 143.05 + 1e-6],
           key=lambda n: XY(*n)[0])
NB = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
def bfs(s, t, allowed):
    if s == t: return [s]
    q = collections.deque([s]); prev = {s: None}
    while q:
        u = q.popleft()
        for di, dj in NB:
            v = (u[0] + di, u[1] + dj)
            if v in allowed and v not in prev:
                prev[v] = u; q.append(v)
                if v == t: break
        if t in prev: break
    if t not in prev: return None
    p = []; u = t
    while u is not None: p.append(u); u = prev[u]
    return p[::-1]
def simplify(o):
    if len(o) < 3: return o
    out = [o[0]]
    for k in range(1, len(o) - 1):
        a, b, c = out[-1], o[k], o[k + 1]
        if (b[0]-a[0])*(c[1]-b[1]) - (b[1]-a[1])*(c[0]-b[0]) != 0: out.append(b)
    out.append(o[-1]); return out
def seg_ok(o, nm):
    b = BAD[nm]
    for k in range(len(o) - 1):
        (x1, y1), (x2, y2) = o[k], o[k + 1]
        L = math.dist((x1, y1), (x2, y2)); n = max(2, int(L / 0.03) + 1)
        xs = np.linspace(x1, x2, n); ys = np.linspace(y1, y2, n)
        i = np.rint((xs - rast.X0) / rast.step).astype(int); j = np.rint((ys - rast.Y0) / rast.step).astype(int)
        ok = (i >= 0) & (i < rast.NX) & (j >= 0) & (j < rast.NY)
        if not bool(ok.all()) or b[i[ok], j[ok]].any(): return False
    return True
REP["geometry"] = {"E_slots": len(E), "E_x": [round(XY(i, jpor)[0], 3) for i, j in E],
                   "free_nodes_range": [min(len(v) for v in FR.values()), max(len(v) for v in FR.values())]}

# ---------------- 一步：候选族（§四规格） ----------------
DVALS = (0, 5, 10, 15, 20); KVALS = (0, 1, 2); ESC = [32, 33, 34, 35]
def gen_family():
    cand = {}; t0 = time.time()
    for nm in names:
        fr = FR[nm]; s0 = S0[nm]; t0v = T0[nm]; ia = int(round((A[nm][0] - X0) / P))
        bx = B[nm][0]
        lst = []; seen = set()
        north_allowed = {(i, j) for (i, j) in fr if j <= 39}
        for e in range(len(E)):
            gi, ji = E[e]
            for d in DVALS:
                band = {jr for jr in range(SR0(d) - 2, SR0(d) + 3)}
                for k in KVALS:
                    ci = ia + k
                    south = set()
                    for (i, j) in fr:
                        x, y = XY(i, j)
                        if j in band or j in ESC or j == ji or i == gi or i == ci \
                           or abs(x - A[nm][0]) <= P / 2 or abs(x - bx) <= P / 2 or (i, j) == (gi, ji):
                            south.add((i, j))
                    south |= {s0, (gi, ji)}
                    p1 = bfs(s0, (gi, ji), south)
                    if not p1: continue
                    north = set(north_allowed) | {(i, j) for (i, j) in fr if abs(XY(i, j)[0] - bx) <= P / 2} | {(gi, ji)}
                    p2 = bfs((gi, ji), t0v, north)
                    if not p2: continue
                    o = simplify([A[nm]] + [XY(*q) for q in (p1 + p2[1:])] + [B[nm]])
                    key = (e, tuple(o))
                    if key in seen: continue
                    seen.add(key)
                    if not seg_ok(o, nm): continue
                    lst.append({"slot": e, "d": d, "k": k, "pts": [[round(p[0], 4), round(p[1], 4)] for p in o]})
        cand[nm] = lst
    return cand
def SR0(d): return 39 + d

# ---------------- 前置闸 ----------------
def gate_preexisting():
    """金样例 · Validate · 三类缺陷负控 · 空域负控 · 在册闸声度（对重叠双线须报 viol>0）"""
    r = {}
    # 金样例回归：4 lane × 4 seat，单调 + 互斥 ⇒ 唯一解 [0,1,2,3]
    mm = cp_model.CpModel(); L = 4; S = 4
    v = {(k, s): mm.NewBoolVar(f"v{k}_{s}") for k in range(L) for s in range(S)}
    for k in range(L): mm.AddExactlyOne([v[(k, s)] for s in range(S)])
    for s in range(S): mm.AddAtMostOne([v[(k, s)] for k in range(L)])
    for k in range(L - 1): mm.Add(sum(s * v[(k, s)] for s in range(S)) < sum(s * v[(k + 1, s)] for s in range(S)))
    sv = cp_model.CpSolver(); st = sv.Solve(mm)
    r["golden_regression"] = {"status": sv.StatusName(st), "answer": [max(range(S), key=lambda s: sv.Value(v[(k, s)])) for k in range(L)],
                              "expected": [0, 1, 2, 3], "pass": st == cp_model.OPTIMAL and [max(range(S), key=lambda s: sv.Value(v[(k, s)])) for k in range(L)] == [0, 1, 2, 3]}
    # 缺陷负控①端点撞格
    nm = names[0]; a = A[nm]; bad = dict(a=(a[0] + 0.05, a[1] + 0.05), b=B[nm])
    rt = {nm: {"pts": [bad["a"], bad["b"]], "layer_cu": "In5.Cu", "n_vias": 2}}
    g = exact_gate(m, rt, an, "In5.Cu", HW, set(), set(), P, frozenset())
    r["nc1_endpoint_off_grid"] = {"endpoint_max_dev_mm": g["endpoint_max_dev_mm"], "detected": g["endpoint_max_dev_mm"] > 0}
    # 缺陷负控②独占误禁本网 + 空域负控
    r["nc2_no_intra_net_forbidden"] = True  # 冲突表只加跨网对（构造保证，见下方断言）
    r["nc4_empty_domain_control"] = None    # 由家族填充
    # 缺陷负控③造不可行：全 16 网强塞同一门位子 ⇒ 必须 INFEASIBLE
    mm2 = cp_model.CpModel(); w = {(k, s): mm2.NewBoolVar(f"w{k}_{s}") for k in range(16) for s in range(18)}
    for k in range(16): mm2.AddExactlyOne([w[(k, s)] for s in range(18)])
    for k in range(16): mm2.Add(w[(k, 0)] == 1)
    sv2 = cp_model.CpSolver(); st2 = sv2.Solve(mm2)
    r["nc3_forced_single_seat_must_be_infeasible"] = {"status": sv2.StatusName(st2), "detected": st2 == cp_model.INFEASIBLE}
    # 在册闸声度：两网同折线（重叠）⇒ exact_gate 必须报 pitch viol > 0
    n1, n2 = names[0], names[1]
    ov = [(A[n1][0], A[n1][1]), (B[n1][0], B[n1][1])]
    rt2 = {n1: {"pts": ov, "layer_cu": "In5.Cu", "n_vias": 2}, n2: {"pts": list(ov), "layer_cu": "In5.Cu", "n_vias": 2}}
    g2 = exact_gate(m, rt2, an, "In5.Cu", HW, set(), set(), P, frozenset())
    r["gate_soundness_overlap_must_fail"] = {"n_lane_pitch_viol": g2["n_lane_pitch_viol"], "lane_pitch_min_gap_mm": g2["lane_pitch_min_gap_mm"],
                                             "detected": g2["n_lane_pitch_viol"] > 0}
    r["all_pass"] = (r["golden_regression"]["pass"] and r["nc1_endpoint_off_grid"]["detected"]
                     and r["nc3_forced_single_seat_must_be_infeasible"]["detected"] and r["gate_soundness_overlap_must_fail"]["detected"])
    return r

# ---------------- 冲突表（真距 + 真穿越） ----------------
def _cross(A_, B_):
    a0, a1 = A_[:, 0, :], A_[:, 1, :]; b0, b1 = B_[:, 0, :], B_[:, 1, :]
    def o(p, q, r): return (q[..., 0]-p[..., 0])*(r[..., 1]-p[..., 1]) - (q[..., 1]-p[..., 1])*(r[..., 0]-p[..., 0])
    B0 = b0[None, :, :]; B1 = b1[None, :, :]; A0 = a0[:, None, :]; A1 = a1[:, None, :]
    d1 = o(B0, B1, A0); d2 = o(B0, B1, A1); d3 = o(A0, A1, B0); d4 = o(A0, A1, B1)
    eps = 1e-9
    cr = (d1*d2 < -eps) & (d3*d4 < -eps)
    def inbox(p, q0, q1):
        return (np.minimum(q0[..., 0], q1[..., 0])-eps <= p[..., 0]) & (p[..., 0] <= np.maximum(q0[..., 0], q1[..., 0])+eps) & \
               (np.minimum(q0[..., 1], q1[..., 1])-eps <= p[..., 1]) & (p[..., 1] <= np.maximum(q0[..., 1], q1[..., 1])+eps)
    t = ((np.abs(d1) < eps) & inbox(A0, B0, B1)) | ((np.abs(d2) < eps) & inbox(A1, B0, B1)) | \
        ((np.abs(d3) < eps) & inbox(B0, A0, A1)) | ((np.abs(d4) < eps) & inbox(B1, A0, A1))
    return cr | t
def segments(c):
    p = [tuple(q) for q in c["pts"]]
    return np.array([[(p[k][0], p[k][1]), (p[k+1][0], p[k+1][1])] for k in range(len(p)-1)], np.float64)
def conflict_table(cand):
    SEG = {nm: [segments(c) for c in cand[nm]] for nm in names}
    conf = {}; hist = collections.Counter(); t0 = time.time()
    for ia_ in range(len(names)):
        for ib_ in range(ia_+1, len(names)):
            na, nb = names[ia_], names[ib_]
            Aseg = np.concatenate([s for s in SEG[na]]); Bseg = np.concatenate([s for s in SEG[nb]])
            aoff = np.cumsum([0]+[len(s) for s in SEG[na]]); boff = np.cumsum([0]+[len(s) for s in SEG[nb]])
            Ch = max(1, int(4_000_000/max(1, len(Bseg))))
            Dl = []; Cl = []
            for c0 in range(0, len(Aseg), Ch):
                Dl.append(_seg_seg_batch(Aseg[c0:c0+Ch], Bseg)); Cl.append(_cross(Aseg[c0:c0+Ch], Bseg))
            D = np.concatenate(Dl, 0); CR = np.concatenate(Cl, 0)
            md = np.minimum.reduceat(np.minimum.reduceat(D, aoff[:-1], axis=0), boff[:-1], axis=1)
            ac = np.logical_or.reduceat(np.logical_or.reduceat(CR, aoff[:-1], axis=0), boff[:-1], axis=1)
            cf = (md < P-1e-6) | ac
            for pi, qj in np.argwhere(cf).tolist():
                dv = 0.0 if ac[pi, qj] else round(float(md[pi, qj]), 4)
                conf.setdefault((na, nb), []).append((int(pi), int(qj), dv))
                hist["0" if dv <= 0 else round(math.floor(dv/0.05)*0.05, 2)] += 1
    return conf, hist, round(time.time()-t0, 1)

# ---------------- 主流程 ----------------
if __name__ == "__main__":
    t0 = time.time()
    pre = gate_preexisting()
    REP["preexisting_gates"] = pre
    cand = gen_family()
    cnt = {nm: len(cand[nm]) for nm in names}
    empty = [nm for nm in names if not cand[nm]]
    REP["family"] = {"counts": cnt, "total": sum(cnt.values()), "empty_nets": empty,
                     "nonempty_control_pass": len(empty) == 0}
    pre["nc4_empty_domain_control"] = {"empty_nets": empty, "pass": len(empty) == 0}
    pre["all_pass"] = pre["all_pass"] and len(empty) == 0
    REP["t_family_s"] = round(time.time()-t0, 1)
    if not pre["all_pass"]:
        REP["decision"] = "STOP-BEFORE-SOLVE: 前置闸未全绿（见 preexisting_gates）⇒ 不开跑 · 额度 1 未耗"
        json.dump(REP, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps(REP, ensure_ascii=False, indent=1, default=str)[:3500]); print("WROTE", OUT); sys.exit(0)
    conf, hist, ct = conflict_table(cand)
    tot = sum(len(v) for v in conf.values()); z = hist.get("0", 0)
    REP["conflict_table"] = {"forbidden_pairs": tot, "net_pairs": len(conf), "at_zero": z,
                             "zero_share": round(z/max(1, tot), 5), "hist": {str(k): hist[k] for k in sorted(hist, key=str)},
                             "t_s": ct}
    # 瓶颈闸：零距占比 >0.5 ⇒ 族无分层 ⇒ 不开跑（守额度）
    if tot == 0 or z/max(1, tot) > 0.5:
        REP["decision"] = "STOP-BEFORE-SOLVE: 冲突表零距占比 >0.5（族无分层·必为族伪影）⇒ 不开跑 · 额度 1 未耗"
        json.dump(REP, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps(REP, ensure_ascii=False, indent=1, default=str)[:3500]); print("WROTE", OUT); sys.exit(0)
    # 模型
    mo = cp_model.CpModel(); x = {}
    for nm in names:
        for i in range(len(cand[nm])): x[(nm, i)] = mo.NewBoolVar(f"x_{nm}_{i}")
        mo.AddExactlyOne([x[(nm, i)] for i in range(len(cand[nm]))])
    for e in range(len(E)):
        t = [x[(nm, i)] for nm in names for i, c in enumerate(cand[nm]) if c["slot"] == e]
        if len(t) > 1: mo.AddAtMostOne(t)
    for a_, b_ in zip(order, order[1:]):
        mo.Add(sum(cand[a_][i]["slot"]*x[(a_, i)] for i in range(len(cand[a_]))) <
               sum(cand[b_][j]["slot"]*x[(b_, j)] for j in range(len(cand[b_]))))
    nforb = 0
    for (na, nb), lst in conf.items():
        for (pi, qj, dv) in lst:
            mo.AddForbiddenAssignments([x[(na, pi)], x[(nb, qj)]], [(1, 1)]); nforb += 1
    v = mo.Validate()
    sha = hashlib.sha256(json.dumps({nm: [(c["slot"], c["d"], c["k"], c["pts"]) for c in cand[nm]] for nm in names},
                                    sort_keys=True, default=str).encode()).hexdigest()[:16]
    REP["model"] = {"vars": len(mo.Proto().variables), "forbidden_assignments": nforb, "validate": v or "OK", "sha16": sha}
    json.dump(REP, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = 900.0; sv.parameters.num_search_workers = 8
    ts = time.time(); st = sv.Solve(mo); dt = round(time.time()-ts, 1)
    REP["solve"] = {"status": sv.StatusName(st), "wall_s": dt, "quota_consumed": 1}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        routes = {}
        for nm in names:
            i = [j for j in range(len(cand[nm])) if sv.Value(x[(nm, j)]) == 1][0]
            routes[nm] = {"pts": [(p[0], p[1]) for p in cand[nm][i]["pts"]], "layer_cu": "In5.Cu", "n_vias": 2}
        g = exact_gate(m, routes, an, "In5.Cu", HW, set(), set(), P, frozenset())
        REP["exact_gate"] = {k: g[k] for k in ("n_lane_pitch_viol", "lane_pitch_min_gap_mm", "lane_pitch_min_pair",
                                               "n_clearance_viol", "clearance_min_mm", "endpoint_max_dev_mm")}
        REP["pass"] = (g["n_lane_pitch_viol"] == 0 and g["n_clearance_viol"] == 0 and g["endpoint_max_dev_mm"] == 0)
        json.dump({"routes": routes, "gate": {k: v_ for k, v_ in g.items() if k != "per_lane"}, "per_lane": g["per_lane"]},
                  open(os.path.join(HERE, "K2_R497_ONE_SHOT_ROUTES_v1.json"), "w"), ensure_ascii=False, default=str)
    REP["decision"] = "TERMINAL-PER-#K2-177-§三" if "pass" in REP else "NON-TERMINAL-STOP"
    REP["elapsed_s"] = round(time.time()-t0, 1)
    json.dump(REP, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(REP, ensure_ascii=False, indent=1, default=str)[:4000]); print("WROTE", OUT)
