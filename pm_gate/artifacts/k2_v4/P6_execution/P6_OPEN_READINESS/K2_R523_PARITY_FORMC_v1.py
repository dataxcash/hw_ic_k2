#!/usr/bin/env python3
"""K2 · R523 —— 丙（parity / 换位记账序变量）· **形态 C · 可机核保真版**（新版本件 · 原件 R515 只读不改）

#K2-189 §四 step 1 要求「丙版与设计解集相同」；R519/R521 已把 **A（declared order 无条件单调）** 与
**B（两线都无过孔⇒保持 declared 序）** 机证为非蕴含。本件实现 **C（翻转必由过孔承担）**，且写成
**只增不减、逐条可机核为蕴含**的形式。

## 与 R521 / HANDOFF-K2-522 字面版的**唯一差异 = 断面/区间口径**（L2 自裁项 · 走廊口径）
HANDOFF-K2-522 §0 把竖向族写成 `(60,r) 行38..57` 与 `(114,g) g∈墙洞行7..28`。**该对不可作证书**：
院列（南带内，向东走）与墙洞行（焊盘场内，向西走）之间走廊**掉头 ~180°**；两线可在**不换层**下把
「col 60 的行序」与「col 114 的行序」对调。机核反例（零过孔 · 逐层声明集互斥 · 合法 · 序翻转）见
`K2_R523_LITERAL_FORMC_COUNTEREXAMPLE_v1.json`。⇒ 按 HANDOFF §0「宁缺毋滥」，改用**走廊内相邻、
且被同一简单条带连接**的断面：
  · V 族：`col 60` ↔ `col 114`（rank = 行；区间 `x∈(x60,x114)`）；
  · H 族：`row 36`（**向南穿门**）↔ `row 30`（焊盘场入口行；rank = 列；区间 `y∈(y30,y36)`）。

## 逐条蕴含证明（前提均可机核）
**横穿定义（完备性关键）**：格点图是 **8 邻域**（R499 `NB` 八方向），刀线 `x=x_c` 恰好只经过 `col=c`
的格点 ⇒ 「本线在 In5 上横穿刀 c 于 (c,k)」⇔ 路径在 In5 上**从 `col=c∓1` 侧进、向 `col=c±1` 侧出**
（含对角进/出）。本模块**把两侧的全部 8 邻域弧都算进去**（漏掉对角就会低估横穿次数 ⇒ 唯一性判据失效）。
  · 腿（自由接入弧）长 ≤ R_REACH = 0.65mm = 1.5 格，而四把刀离任一锚点 ≥17 格 ⇒ **腿不可能横穿任何一把刀**
    （`K2_R523_FORMC_PREMISE_CHECKS_v1.py` 机核）。
1. `unique[线,刀] = (横穿次数 == 1)`。因节点容量（入度 ≤1）+ 流量守恒（入=出）⇒ 路径是**简单路**
   ⇒「两次横穿之间的 In5 子路」**整段留在条带内**（竖向条带 `60<x<114` 全行；横向条带 `30<row<36` 全列）。
2. 两条曲线各连条带两条边界、且**横向序翻转** ⇒ Jordan/中值定理 ⇒ **必相交**。
3. 交点同落在两条 In5 折线上 ⇒ 其最近格点距交点 ≤ P/√2 < P ⇒ **声明集相交** ⇒ 被 R513-T3 已机核
   「逐对等价」的在册逐层声明集约束判为**非法**。
4. ⇒ 合法解中不可能「双方 unique ∧ 序翻转 ∧ 区间内零过孔弧」⇒ 故
   `unique(a,S1)∧unique(b,S1)∧unique(a,S2)∧unique(b,S2)∧INV ⇒ Σ(区间内过孔弧) ≥ 1`
   **被蕴含**（加它不砍任何设计合法解）⇒ 本族**同解集**。
唯一性不满足的线（如：在焊盘场第二次横穿 col 114、沿刀走、贴刀转向）⇒ 该对**不施加**约束（只变弱不变错）。
所有约束挂独立假设字面量 `ASSUMP["parity_form_C"]`（#K2-187 §四.④ 非空核）。
"""
import collections

_SIDE = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def _pos(i, j, NY):
    return i * NY + j


def _ge1(mo, lst, tag, st):
    """⇒ literal ⇔ (Σ lst ≥ 1)；空列表 ⇒ None（恒 0）。"""
    if not lst:
        return None
    if len(lst) == 1:
        return lst[0]
    u = mo.NewBoolVar(tag); st["booleans"] += 1
    mo.Add(sum(lst) >= 1).OnlyEnforceIf(u)
    mo.Add(sum(lst) == 0).OnlyEnforceIf(u.Not())
    st["cons"] += 2
    return u


def _and(mo, a, b, tag, st):
    h = mo.NewBoolVar(tag); st["booleans"] += 1
    mo.AddImplication(h, a); mo.AddImplication(h, b)
    mo.AddBoolOr([a.Not(), b.Not(), h]); st["cons"] += 3
    return h


def _or(mo, lst, tag, st):
    lst = [v for v in lst if v is not None]
    if not lst:
        return None
    if len(lst) == 1:
        return lst[0]
    o = mo.NewBoolVar(tag); st["booleans"] += 1
    for v in lst:
        mo.AddImplication(v, o)
    mo.AddBoolOr([v.Not() for v in lst] + [o]); st["cons"] += len(lst) + 1
    return o


def _cross_terms(mo, x, li, NX, NY, cut, tag, st):
    """[(lateral_index, cross_bool)]：本线在 In5 上横穿该刀线（8 邻域完备 · 方向按 dir 过滤）。"""
    kind, idx = cut[0], cut[1]
    d = cut[2] if len(cut) > 2 else 0
    out = []
    if not (1 <= idx <= (NX - 2 if kind == "col" else NY - 2)):
        return out
    span = range(NY) if kind == "col" else range(NX)
    for k in span:
        if kind == "col":
            c = idx
            m = _pos(c, k, NY)
            nL = lambda dj: _pos(c - 1, k + dj, NY)
            nR = lambda dj: _pos(c + 1, k + dj, NY)
            ok = lambda j: 0 <= j < NY
            inL = [x[(li, nL(dj), m)] for dj in (-1, 0, 1) if ok(k + dj) and (li, nL(dj), m) in x]
            inR = [x[(li, nR(dj), m)] for dj in (-1, 0, 1) if ok(k + dj) and (li, nR(dj), m) in x]
            outL = [x[(li, m, nL(dj))] for dj in (-1, 0, 1) if ok(k + dj) and (li, m, nL(dj)) in x]
            outR = [x[(li, m, nR(dj))] for dj in (-1, 0, 1) if ok(k + dj) and (li, m, nR(dj)) in x]
        else:
            r = idx
            m = _pos(k, r, NY)
            nD = lambda dk: _pos(k + dk, r - 1, NY)
            nU = lambda dk: _pos(k + dk, r + 1, NY)
            ok = lambda i2: 0 <= i2 < NX
            inL = [x[(li, nD(dk), m)] for dk in (-1, 0, 1) if ok(k + dk) and (li, nD(dk), m) in x]
            inR = [x[(li, nU(dk), m)] for dk in (-1, 0, 1) if ok(k + dk) and (li, nU(dk), m) in x]
            outL = [x[(li, m, nD(dk))] for dk in (-1, 0, 1) if ok(k + dk) and (li, m, nD(dk)) in x]
            outR = [x[(li, m, nU(dk))] for dk in (-1, 0, 1) if ok(k + dk) and (li, m, nU(dk)) in x]
        aL = _ge1(mo, inL, "%s_inL_%d_%d" % (tag, li, k), st)
        aR = _ge1(mo, inR, "%s_inR_%d_%d" % (tag, li, k), st)
        bL = _ge1(mo, outL, "%s_outL_%d_%d" % (tag, li, k), st)
        bR = _ge1(mo, outR, "%s_outR_%d_%d" % (tag, li, k), st)
        cand = []
        if d in (0, 1):            # 左进右出（行/列号增大方向）
            h = _and(mo, aL, bR, "%s_E_%d_%d" % (tag, li, k), st) if (aL is not None and bR is not None) else None
            if h is not None:
                cand.append(h)
        if d in (0, -1):           # 右进左出
            h = _and(mo, aR, bL, "%s_W_%d_%d" % (tag, li, k), st) if (aR is not None and bL is not None) else None
            if h is not None:
                cand.append(h)
        cr = _or(mo, cand, "%s_X_%d_%d" % (tag, li, k), st)
        if cr is not None:
            out.append((k, cr))
    return out


def _unique_literal(mo, cnt_terms, tag, st):
    """u ⇔ (Σ cross == 1)；无任何可能横穿 ⇒ None。"""
    if not cnt_terms:
        return None
    s = sum(cnt_terms)
    ug = mo.NewBoolVar(tag + "_ge1"); ul = mo.NewBoolVar(tag + "_le1")
    u = mo.NewBoolVar(tag + "_eq1"); st["booleans"] += 3
    mo.Add(s >= 1).OnlyEnforceIf(ug); mo.Add(s == 0).OnlyEnforceIf(ug.Not())
    mo.Add(s <= 1).OnlyEnforceIf(ul); mo.Add(s >= 2).OnlyEnforceIf(ul.Not())
    mo.AddImplication(u, ug); mo.AddImplication(u, ul); mo.AddBoolOr([ug.Not(), ul.Not(), u])
    st["cons"] += 6
    return u


def _via_in_interval(pos, NY, interval):
    i, j = divmod(pos, NY)
    kind, lo, hi = interval
    return (lo < i < hi) if kind == "col" else (lo < j < hi)


def add_form_c(mo, x, lanes, NID, NX, NY, ASSUMP, lit_par, verbose=False):
    """形态 C：V = col60↔col114（rank=行）· H = row36(向南)↔row30（rank=列）。返回统计。"""
    st = {"booleans": 0, "cons": 0}
    pairs = [("V", [("col", 60, 0), ("col", 114, 0)], ("col", 60, 114)),
             ("H", [("row", 36, -1), ("row", 30, 0)], ("row", 30, 36))]
    extra = {"H": [("row", 36, 1)]}
    rep = {"families": {}, "n_pairs": 0, "n_constraints": 0}
    nL = len(lanes)
    for fam, cuts, interval in pairs:
        probes = [(cuts[0], "A"), (cuts[1], "B")] + [(e, "X%d" % i) for i, e in enumerate(extra.get(fam, []))]
        cross, uni, rank = {}, {}, {}
        for li in range(nL):
            for (c, tg) in probes:
                t = _cross_terms(mo, x, li, NX, NY, c, "%s%s_%d" % (fam, tg, li), st)
                cross[(li, c, tg)] = t
                uni[(li, c, tg)] = _unique_literal(mo, [v for _k, v in t], "%s%s_%d" % (fam, tg, li), st)
                rank[(li, c, tg)] = sum(k * v for k, v in t)
        via_in = {}
        for li in range(nL):
            lst = []
            for (u, v) in lanes[li]["vias"]:
                tagv, p = lanes[li]["via_arcs"][(u, v)]
                if _via_in_interval(p, NY, interval):
                    lst.append(x[(li, u, v)])
            via_in[li] = lst
        nact = 0
        for a in range(nL):
            for b in range(a + 1, nL):
                A0, A1 = cuts[0], cuts[1]
                hyps = []
                ok = True
                for (cc, tg) in probes:
                    ha = uni[(a, cc, tg)]; hb = uni[(b, cc, tg)]
                    if ha is None or hb is None:
                        ok = False; break
                    hyps += [ha, hb]
                if not ok:
                    continue
                ltA = mo.NewBoolVar("%s_ltA_%d_%d" % (fam, a, b))
                ltB = mo.NewBoolVar("%s_ltB_%d_%d" % (fam, a, b))
                st["booleans"] += 2
                mo.Add(rank[(a, A0, "A")] <= rank[(b, A0, "A")] - 1).OnlyEnforceIf(ltA)
                mo.Add(rank[(a, A0, "A")] >= rank[(b, A0, "A")] + 1).OnlyEnforceIf(ltA.Not())
                mo.Add(rank[(a, A1, "B")] <= rank[(b, A1, "B")] - 1).OnlyEnforceIf(ltB)
                mo.Add(rank[(a, A1, "B")] >= rank[(b, A1, "B")] + 1).OnlyEnforceIf(ltB.Not())
                st["cons"] += 4
                t1 = mo.NewBoolVar("%s_inv1_%d_%d" % (fam, a, b))
                t2 = mo.NewBoolVar("%s_inv2_%d_%d" % (fam, a, b))
                inv = mo.NewBoolVar("%s_inv_%d_%d" % (fam, a, b))
                fire = mo.NewBoolVar("%s_fire_%d_%d" % (fam, a, b))
                st["booleans"] += 4
                mo.AddImplication(t1, ltA); mo.AddImplication(t1, ltB.Not())
                mo.AddBoolOr([ltA.Not(), ltB, t1])
                mo.AddImplication(t2, ltA.Not()); mo.AddImplication(t2, ltB)
                mo.AddBoolOr([ltA, ltB.Not(), t2])
                mo.AddImplication(t1, inv); mo.AddImplication(t2, inv)
                mo.AddBoolOr([t1.Not(), t2.Not(), inv])
                for h in hyps:
                    mo.AddImplication(fire, h)
                mo.AddImplication(fire, inv)
                mo.AddBoolOr([h.Not() for h in hyps] + [inv.Not(), fire])
                st["cons"] += 2 * len(hyps) + 8
                via = via_in[a] + via_in[b]
                if via:
                    mo.Add(sum(via) >= 1).OnlyEnforceIf([fire, lit_par])
                else:
                    mo.Add(fire == 0).OnlyEnforceIf(lit_par)
                st["cons"] += 1
                nact += 1
        rep["families"][fam] = {
            "cuts": [list(c) for c in cuts], "extra_uniqueness_cuts": [list(c) for c in extra.get(fam, [])],
            "interval": list(interval), "pairs_constrained": nact,
            "lanes_with_any_A_crossing": sum(1 for li in range(nL) if uni[(li, cuts[0], "A")] is not None),
            "lanes_with_any_B_crossing": sum(1 for li in range(nL) if uni[(li, cuts[1], "B")] is not None),
            "crossing_options_A_per_lane": [len(cross[(li, cuts[0], "A")]) for li in range(nL)],
            "crossing_options_B_per_lane": [len(cross[(li, cuts[1], "B")]) for li in range(nL)],
            "via_arcs_in_interval_total": sum(len(v) for v in via_in.values()),
        }
        rep["n_pairs"] += nact
    rep["n_constraints"] = st["cons"]
    rep["n_booleans"] = st["booleans"]
    return rep
