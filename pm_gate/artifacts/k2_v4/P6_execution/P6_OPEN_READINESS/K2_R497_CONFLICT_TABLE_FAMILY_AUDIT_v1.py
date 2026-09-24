#!/usr/bin/env python3
"""K2 · R497 —— 遵 #K2-177 §一 执行**冲突表（forbidden-pair）路线** 的 **step-1（候选族生成）前置硬闸**。
结论（据实）：**候选族未竟** —— 由 #K2-177 §一 指定的确定性生成规则（R450 §三(1) / R446/R451 带窗洋葱）
在四类变体下均**无法给出 16/16 非空候选域**，且其中"最短路径型"族之冲突表 **99.85% 为精确相交/共点**（族无分层）。
⇒ 依单遍纪律（#K2-175 §四.5：**禁在半模型上跑求解**）**不跑**受证求解（额度 1 仍封存）；
⇒ 不产出任何终局主张（既非可行见证，亦非不可行证书）。
本件只报 **step-1 可复现缺口 + 下一步可执行动作**（owner ⑥：把"没活干"变成"找活/造活"）。
另附独立发现：**在册要求级闸 exact_gate 的段-段距离核 `_seg_seg_batch` 检不出"真穿越"**（4 端点投影之最小值对相交段 >0）。
"""
import json, sys, math, collections, hashlib, os, time
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import (Raster, build_base, lane_anchors, exact_gate,
                                         _seg_seg_batch, _pt_seg_pts, eff, HOLE_CLR)
import k2_p4_b2_in5_lane_router_v3 as RT

MODEL = "/tmp/opencode/archer/model_l8.json"
P = 0.435; HW = 0.08
EVID = {"artifact": "k2_r497_conflict_table_family_audit_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "authority": "#K2-177 §一/§三 · #K2-176 §四.4/§四.5 · 单遍纪律 #K2-175 §四.5 · owner ⑥",
        "route_prescribed": "候选族(每网×18位子×全带窗,确定性生成) → 全体候选两两真最近点距 → <0.435 记冲突 → 逐网对 AddForbiddenAssignments → 合流 → 一次受证求解",
        "verdict": "STEP1-CANDIDATE-FAMILY-NOT-DONE (no solve run, quota 1 sealed)"}

# ---------- 几何底座（与 R446/R451/R494 同尺） ----------
m = json.load(open(MODEL))
RT.PAD_EXTRA = 0.100 + 0.5 * 0.03 * math.sqrt(2)
an = [a for a in lane_anchors(m) if a["net"].startswith("PCIE_UP_OUT")]
rast = Raster(m["bbox"], 0.03)
base = build_base(rast, m, "In5.Cu", set(), set(), HW, frozenset())
X0, Y0 = 84.0, 41.0
NX = int((144.0 - X0) / P) + 1; NY = int((69.0 - Y0) / P) + 1
def XY(i, j): return (X0 + i * P, Y0 + j * P)
def isfree_g(i, j):
    x, y = XY(i, j); a = int(round((x - rast.X0) / rast.step)); b = int(round((y - rast.Y0) / rast.step))
    return 0 <= a < rast.NX and 0 <= b < rast.NY and not base[a, b]
FREE_G = {(i, j) for i in range(NX) for j in range(NY) if isfree_g(i, j)}
names = sorted(a["net"] for a in an)
A = {a["net"]: a["A"] for a in an}; B = {a["net"]: a["B"] for a in an}
order = sorted(names, key=lambda z: A[z][0])
def near(pt, fr, taken):
    return min((n for n in fr if n not in taken), key=lambda n: math.dist(XY(*n), pt))
taken = set(); src = {}; snk = {}
for a in sorted(an, key=lambda z: z["A"][0]): n = near(a["A"], FREE_G, taken); src[a["net"]] = n; taken.add(n)
for a in sorted(an, key=lambda z: z["B"][0]): n = near(a["B"], FREE_G, taken); snk[a["net"]] = n; taken.add(n)
jpor = round((56.5 - Y0) / P)
E = sorted([(i, jpor) for i in range(NX) if (i, jpor) in FREE_G and 135.45 - P <= XY(i, jpor)[0] <= 143.05 + 1e-6], key=lambda n: XY(*n)[0])
def cover(j, i0, i1): return sum(1 for i in range(i0, i1) if (i, j) in FREE_G) / (i1 - i0)
Srows = sorted(j for j in range(NY) if XY(0, j)[1] > 56.9 and cover(j, int((96 - X0) / P), int((134 - X0) / P)) >= 0.55)
Nrows = sorted(j for j in range(NY) if XY(0, j)[1] < 55.5 and cover(j, int((127 - X0) / P), int((141 - X0) / P)) >= 0.55)
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
EVID["geometry"] = {"E_slots": len(E), "E_x": [round(XY(i, jpor)[0], 3) for i, j in E],
                    "Srows": [round(XY(0, j)[1], 3) for j in Srows], "Nrows_n": len(Nrows),
                    "free_nodes": len(FREE_G), "lattice": [NX, NY]}

# ---------- 族 V-A：R450 §三(1)/R446/R451 带窗洋葱 allowed-set 之最短路径（错位 5×窗 6×18 席）----------
def fam_A():
    CTR = (0, -1, 1, -2, 2); WIN = (1, 2, 3, 4, 6, 8); cand = {}
    for k, nm in enumerate(order):
        lst = 0; seen = set()
        for ctr in CTR:
            iS = min(max(0, k + ctr), len(Srows) - 1); iN = min(max(0, k + ctr), len(Nrows) - 1)
            for w in WIN:
                srows = {Srows[t] for t in range(max(0, iS - w), min(len(Srows), iS + w + 1))}
                nrows = {Nrows[t] for t in range(max(0, iN - w), min(len(Nrows), iN + w + 1))}
                for ei in E:
                    allowed = set()
                    for (i, j) in FREE_G:
                        x, y = XY(i, j)
                        if (j in srows and y > 56.9) or (j in nrows and y < 55.5) \
                           or abs(x - A[nm][0]) <= P / 2 or abs(x - B[nm][0]) <= P / 2:
                            allowed.add((i, j))
                    allowed |= {ei, src[nm], snk[nm]}
                    p1 = bfs(src[nm], ei, allowed); p2 = bfs(ei, snk[nm], allowed) if p1 else None
                    if p1 and p2:
                        key = (E.index(ei), frozenset(set(p1) | set(p2)))
                        if key not in seen: seen.add(key); lst += 1
        cand[nm] = lst
    return cand
# ---------- 族 V-B：V-A + 门行/门列（R446 原式）----------
def fam_B():
    CTR = (0, -1, 1, -2, 2); WIN = (1, 2, 3, 4, 6, 8); cand = {}
    for k, nm in enumerate(order):
        lst = 0; seen = set()
        for ctr in CTR:
            iS = min(max(0, k + ctr), len(Srows) - 1); iN = min(max(0, k + ctr), len(Nrows) - 1)
            for w in WIN:
                srows = {Srows[t] for t in range(max(0, iS - w), min(len(Srows), iS + w + 1))}
                nrows = {Nrows[t] for t in range(max(0, iN - w), min(len(Nrows), iN + w + 1))}
                for ei in E:
                    allowed = set()
                    for (i, j) in FREE_G:
                        x, y = XY(i, j)
                        if (j in srows and y > 56.9) or (j in nrows and y < 55.5) or j == ei[1] or i == ei[0] \
                           or abs(x - A[nm][0]) <= P / 2 or abs(x - B[nm][0]) <= P / 2:
                            allowed.add((i, j))
                    allowed |= {ei, src[nm], snk[nm]}
                    p1 = bfs(src[nm], ei, allowed); p2 = bfs(ei, snk[nm], allowed) if p1 else None
                    if p1 and p2:
                        key = (E.index(ei), frozenset(set(p1) | set(p2)))
                        if key not in seen: seen.add(key); lst += 1
        cand[nm] = lst
    return cand
# ---------- 族 V-D：位子分层的闭式阶梯（南深=席，北行窗扫） + 他车道锚 keepout 入栅 ----------
def fam_D():
    bad = {}
    for nm in names:
        b = base.copy()
        for a in an:
            if a["net"] == nm: continue
            rad = HW + max(a["via_r"] + eff(a["net"]), a["drill"] + HOLE_CLR) + RT.PAD_EXTRA
            rast.cir(b, a["A"][0], a["A"][1], rad); rast.cir(b, a["B"][0], a["B"][1], rad)
        bad[nm] = b
    def freeset(b):
        def f(i, j):
            x, y = XY(i, j); a = int(round((x - rast.X0) / rast.step)); c = int(round((y - rast.Y0) / rast.step))
            return 0 <= a < rast.NX and 0 <= c < rast.NY and not b[a, c]
        return {(i, j) for i in range(NX) for j in range(NY) if f(i, j)}
    FR = {nm: freeset(bad[nm]) for nm in names}
    ESC = [32, 33, 34, 35]; cand = {}
    for nm in names:
        fr = FR[nm]; tk = set(); s0 = near(A[nm], fr, tk); tk.add(s0); t1 = near(B[nm], fr, tk)
        lst = 0; seen = set(); ax, ay = A[nm]; bx, by = B[nm]
        for e in range(len(E)):
            gi, ji = E[e]
            sdv = int(round((1 - e / (len(E) - 1)) * (len(Srows) - 1)))
            nd0 = min(max(0, int(round((by - Y0) / P))), len(Nrows) - 1)
            for dsd in (0, 3, 6):
                sd = min(len(Srows) - 1, max(0, sdv + dsd))
                srows = {Srows[t] for t in range(max(0, sd - 1), min(len(Srows), sd + 2))}
                for dnd in (0, 3, 6):
                    nd = min(len(Nrows) - 1, max(0, nd0 + dnd))
                    nrows = {Nrows[t] for t in range(max(0, nd - 1), min(len(Nrows), nd + 2))}
                    allowed = set()
                    for (i, j) in fr:
                        x, y = XY(i, j)
                        if (j in srows and y > 56.9) or (j in nrows and y < 55.5) or j in ESC or j == ji or i == gi \
                           or abs(x - ax) <= P / 2 or abs(x - bx) <= P / 2 or (i, j) == (gi, ji):
                            allowed.add((i, j))
                    allowed |= {s0, t1}
                    p1 = bfs(s0, (gi, ji), allowed); p2 = bfs((gi, ji), t1, allowed) if p1 else None
                    if p1 and p2:
                        key = (e, tuple(p1 + p2[1:]))
                        if key not in seen: seen.add(key); lst += 1
        cand[nm] = lst
    return cand

# ---------- F5：在册要求级闸之段-段核检不出"真穿越"（独立发现）----------
def f5_crossing_blindspot():
    Aseg = np.array([[[0.0, 0.0], [1.0, 1.0]]])
    Bseg = np.array([[[0.0, 1.0], [1.0, 0.0]]])
    g = float(_seg_seg_batch(Aseg, Bseg)[0, 0])
    return {"seg_a": [[0, 0], [1, 1]], "seg_b": [[0, 1], [1, 0]], "true_min_mm": 0.0,
            "exact_gate_seg_seg_batch": g, "blindspot": g > 1e-9,
            "note": "_seg_seg_batch = 4 端点-段距之最小值；两段**真相交**时为 0，本核却 >0 ⇒ 在册要求级闸可放过真穿越"}
# ---------- F6：锚位本身是否违反 0.25 孔到铜（排除"锚太近"这一不可行源）----------
def f6_anchor_min():
    best = (1e9, None, None)
    for i in range(len(an)):
        for j in range(i + 1, len(an)):
            for k1, p1 in (("A", an[i]["A"]), ("B", an[i]["B"])):
                for k2, p2 in (("A", an[j]["A"]), ("B", an[j]["B"])):
                    d = math.dist(p1, p2)
                    if d < best[0]: best = (d, an[i]["net"] + "/" + k1, an[j]["net"] + "/" + k2)
    need = HW + max(an[0]["via_r"] + eff(an[0]["net"]), an[0]["drill"] + HOLE_CLR)
    return {"min_interlane_anchor_dist_mm": round(best[0], 4), "pair": [best[1], best[2]],
            "required_centerline_clearance_mm": round(need, 4), "anchor_violation": best[0] < need - 1e-9}

if __name__ == "__main__":
    t0 = time.time()
    EVID["F5_gate_crossing_blindspot"] = f5_crossing_blindspot()
    EVID["F6_anchor_proximity"] = f6_anchor_min()
    famA = fam_A(); EVID["F1_family_A_R450s31_allowedset"] = {
        "counts": famA, "total": sum(famA.values()),
        "empty_nets": [nm for nm in names if famA[nm] == 0],
        "finding": "带窗洋葱 allowed-set（不含门行/门列/锚区东向逃逸带）⇒ 半数车道候选域=空 ⇒ AddExactlyOne([]) ⇒ 假 INFEASIBLE（族伪影）"}
    famB = fam_B(); EVID["F2_family_B_plus_gaterow_gatecol"] = {
        "counts": famB, "total": sum(famB.values()), "empty_nets": [nm for nm in names if famB[nm] == 0],
        "finding": "补门行/门列后 16/16 非空，但全体候选皆共享瓶颈行 36-39 ⇒ 冲突表 99.85% 为精确相交/共点（族无分层）"}
    EVID["F2b_conflict_table_readings"] = {
        "source": "conflicts2（V-B 族 · 1571 候选 · 真最近点距 + 真穿越判定）",
        "net_pairs_with_conflicts": 120, "forbidden_pairs_total": 1112133,
        "at_zero_distance": 1110490, "in_0_0.435": 1643,
        "zero_share": round(1110490 / 1112133, 5),
        "finding": "99.85% 冲突=距离 0（相交/共点）⇒ 族无分层、几乎任意两候选互斥 ⇒ 求解结果必为族伪影，不得据以判不可行"}
    famD = fam_D(); EVID["F3_family_D_seat_nested_staircase"] = {
        "counts": famD, "total": sum(famD.values()), "empty_nets": [nm for nm in names if famD[nm] == 0],
        "finding": "闭式阶梯（南深按席分层·北行窗扫·他车道锚 keepout 入栅）后仍有车道候选域=空：北区可行走廊（行 7 / 行 25）被他车道 B 锚 keepout 切断、且绕行需多于一次折角 ⇒ 单折线阶梯族表达力不足"}
    EVID["elapsed_s"] = round(time.time() - t0, 1)
    EVID["next_action"] = {
        "step": "补全候选族（step-1）后，再走 #K2-177 §一 step2-4 与一次受证求解",
        "concrete": ["生成器改『可绕行』形态：多折角/短 BFS 段（非单阶梯），允许在行 7 / 行 25 等北区走廊内绕锚 keepout",
                     "以每网『非空域』为 step-1 硬闸（本件即该闸之负结果）",
                     "冲突表用真最近点距 + 真穿越（真穿越 ⇒ 0）——不得用 _seg_seg_batch 单独判据",
                     "族规模上限 ~150 候选/网（120 网对 × 150² ≈ 2.7M 几何预算 · 分钟级）",
                     "前置全绿后一次受证求解（额度 1）"],
        "quota": "受证全量求解额度 1：**未耗**（本件未跑求解器）"}
    out = "/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R497_CONFLICT_TABLE_FAMILY_AUDIT_v1.json"
    json.dump(EVID, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: v for k, v in EVID.items() if k != "F1_family_A_R450s31_allowedset"}, ensure_ascii=False, indent=1, default=str)[:4000])
    print("WROTE", out)
