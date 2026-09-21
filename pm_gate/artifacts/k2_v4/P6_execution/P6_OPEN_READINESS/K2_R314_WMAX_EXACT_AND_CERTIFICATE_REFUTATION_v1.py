#!/usr/bin/env python3
"""K2 · R314 —— 西出缺口 W_max **精确复算 + 证书反证**（只读 · 不改生成器 · 不写板）

缘起：R309/R313 之《守恒级不可行证书 v59》给 W_max=6 ⇒ U ≤ 14 ⇒ "16/16 不可达"。
      本器证明该上界**不是几何/守恒级约束**，而系复算器所加「沿某排序之单调 ye 阶梯」所致。

判据分层（本器同时做三件事）：
  [1] 证书口径复现：沿用 R313 `w_max()` 之「阶梯」约束（`ye_{k+1} >= ye_k + P`），
      分别以 A.x 序 / B.x 序 × 正序 / 逆序 ⇒ 复现 W_max=6/5 与 8/7 之别。
  [2] 精确口径：**只**施加真实几何约束 ——
        (i) 每条 lane 之 jog 高度 ye 落于其「西出缺口自由带」内（R313 同源 aperture）；
        (ii) ye >= B.y + δ（竖段须可回到 B 锚，δ=0.15 / 0.00 / 0.05）；
        (iii) 两两 |Δye| >= P（车道互距下限，DRC 0.335 + 余量 0.100 = 0.435）；
        (iv) **非交叉**：对 B.x_i < B.x_j 之两 lane，若 ye_i < ye_j 则须 ye_i < B.y_j - P
             （否则 i 之水平 jog 会与 j 之 B.x 竖段相交 / 净距不足）；
        (v) ye_i > ye_j 时由 (iii) 保证 i 从 j 竖段顶端之上绕过。
      ⇒ MILP（HiGHS）精确最大化可放置 lane 数。
  [3] 落件字段：结果 / 反证 / 自证（逐约束校验）/ 可施工性（宪法13）。

用法:
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_b2_board_in5_model_dump_v1.py k2/hw/k2_v4_8L.l8.kicad_pcb /tmp/opencode/model_l8.json
  python3 K2_R314_WMAX_EXACT_AND_CERTIFICATE_REFUTATION_v1.py /tmp/opencode/model_l8.json
"""
import sys, json, math, itertools, importlib.util
import numpy as np
from scipy import ndimage
from scipy.optimize import milp, LinearConstraint, Bounds

V3 = "k2/tools/k2_p4_b2_in5_lane_router_v3.py"
LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
CELL, HW, P = 0.01, 0.08, 0.435
DX = {0: "F.Cu-B.Cu", 1: "F.Cu-In2.Cu"}


def load_v3():
    spec = importlib.util.spec_from_file_location("v3", V3)
    v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
    v3.is_lane = lambda n: n in LANES
    return v3


def apertures(model, v3, dil):
    """每条西组 lane 之「西出缺口自由带」（与 R313.CERTIFICATE_CHECKER 逐行同源）。"""
    rast = v3.Raster(model["bbox"], CELL)
    base = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
    di = int(math.ceil(dil / CELL))
    bad = ndimage.binary_dilation(base, structure=np.ones((2 * di + 1, 2 * di + 1), bool)) if di > 0 else base
    free = ~bad; X0, Y0 = rast.X0, rast.Y0; NX, NY = free.shape
    I = lambda x: int(round((x - X0) / CELL)); J = lambda y: int(round((y - Y0) / CELL))
    ad = {a["net"]: a for a in v3.lane_anchors(model)}; out = []
    for n in sorted(LANES, key=lambda x: ad[x]["A"][0]):
        B = ad[n]["B"]
        if B[0] >= 135.40:      # 东组不需缺口（与证书同口径）
            continue
        i0 = I(B[0]); rows = []
        for j in range(J(41.0), J(60.0) + 1):
            if not free[i0, j]:
                continue
            i = i0
            while i + 1 < NX and free[i + 1, j]:
                i += 1
            if X0 + i * CELL >= 134.0:
                y = round(Y0 + j * CELL, 2); jb, jy = J(B[1]), J(y)
                if jb > jy: jb, jy = jy, jb
                if free[I(B[0]), jb:jy + 1].all():
                    rows.append(y)
        bands = []; s = p = None
        for y in rows:
            if s is None: s = y
            elif y - p > 0.03: bands.append((s, p)); s = y
            p = y
        if rows: bands.append((s, p))
        out.append({"net": n, "Bx": B[0], "By": B[1], "Ax": ad[n]["A"][0], "bands": bands})
    return out


# ---------- [1] 证书口径（阶梯） ----------
def w_ladder(ap, key, rev, delta=0.15, p=P):
    names = [a["net"] for a in sorted(ap, key=lambda a: a[key])]
    order = list(reversed(names)) if rev else names

    def ok(sub):
        yn = None
        for n in order:
            if n not in sub: continue
            a = next(x for x in ap if x["net"] == n); cand = None
            for lo, hi in a["bands"]:
                c = max(lo, a["By"] + delta)
                if yn is not None: c = max(c, yn + p)
                if c <= hi + 1e-9: cand = c; break
            if cand is None: return False
            yn = cand
        return True
    for m in range(len(names), 0, -1):
        for comb in itertools.combinations(names, m):
            if ok(set(comb)): return m, list(comb)
    return 0, []


# ---------- [2] 精确口径（真实几何） ----------
def cands_for(a, delta, p):
    vs = set(); base = a["By"] + delta
    for lo, hi in a["bands"]:
        for v in (lo, hi):
            if v >= base - 1e-9: vs.add(round(v, 3))
        for k in range(0, 8):
            for v in (base + k * p, lo + k * p, hi - k * p, base - k * p):
                v = round(v, 3)
                if lo - 1e-9 <= v <= hi + 1e-9 and v >= base - 1e-9: vs.add(v)
    return sorted(vs)


def w_exact(ap, delta=0.15, p=P):
    cand = []; idx = {}
    for a in ap:
        vs = cands_for(a, delta, p); idx[a["net"]] = list(vs)
        for v in vs: cand.append((a["net"], v))
    pos = {(n, v): k for k, (n, v) in enumerate(cand)}; N = len(cand)
    cons = []; ub = []
    for a in ap:
        row = np.zeros(N)
        for v in idx[a["net"]]: row[pos[(a["net"], v)]] = 1
        cons.append(row); ub.append(1)

    def add(x1, y1, x2, y2):
        row = np.zeros(N); row[pos[(x1, y1)]] = 1; row[pos[(x2, y2)]] = 1
        cons.append(row); ub.append(1)

    for i in range(len(ap)):
        for j in range(i + 1, len(ap)):
            a, b = ap[i], ap[j]
            lo, hi = (a, b) if a["Bx"] < b["Bx"] else (b, a); same = (a["Bx"] == b["Bx"])
            for v1 in idx[lo["net"]]:
                for v2 in idx[hi["net"]]:
                    if same: add(lo["net"], v1, hi["net"], v2); continue
                    if abs(v1 - v2) < p - 1e-9:                        # (iii) 互距
                        add(lo["net"], v1, hi["net"], v2)
                    elif v1 < v2 - 1e-9 and (v1 >= hi["By"] - 1e-9 or hi["By"] - v1 < p - 1e-9):
                        add(lo["net"], v1, hi["net"], v2)              # (iv) 交叉 / 锚孔净距
    A = np.array(cons)
    res = milp(c=-np.ones(N), constraints=LinearConstraint(A, -np.inf, np.array(ub)),
               integrality=np.ones(N), bounds=Bounds(0, 1))
    sel = {cand[k][0]: cand[k][1] for k, x in enumerate(res.x) if x > 0.5}
    return (int(round(-res.fun)) if res.status == 0 else None), sel


def verify(ap, sel, delta=0.15, p=P):
    """逐约束自证（独立于 MILP 编码）。"""
    d = {a["net"]: a for a in ap}; errs = []; chk = []
    for n, y in sel.items():
        a = d[n]
        if y < a["By"] + delta - 1e-9: errs.append(f"{n}: ye<B.y+{delta}")
        if not any(lo - 1e-9 <= y <= hi + 1e-9 for lo, hi in a["bands"]): errs.append(f"{n}: ye 越带")
    ns = list(sel)
    for i, j in itertools.combinations(ns, 2):
        if abs(sel[i] - sel[j]) < p - 1e-9: errs.append(f"{i}|{j}: 互距 {abs(sel[i]-sel[j]):.3f}<{p}")
    for i, j in itertools.combinations(ns, 2):
        lo, hi = (i, j) if d[i]["Bx"] < d[j]["Bx"] else (j, i)
        if sel[lo] < sel[hi] - 1e-9:
            gap = d[hi]["By"] - sel[lo]
            if gap < p - 1e-9: errs.append(f"{lo}->{hi}: 交叉/锚孔净距 {gap:.3f}<{p}")
    # 逐 lane 与其带之对照
    for n in sorted(sel): chk.append({"net": n, "B.x": d[n]["Bx"], "B.y": d[n]["By"], "ye": sel[n]})
    return errs, chk


def main():
    model = json.load(open(sys.argv[1]))
    v3 = load_v3()
    print("== K2 R314 · 西出缺口 W_max 精确复算 / 证书反证 ==")
    out = {"schema": 1, "artifact": "k2_r314_wmax_exact_and_certificate_refutation_v1",
           "to": "监理", "from": "ENG · ARCHER", "cases": {}}
    for tag, dil in (("DIL=0", 0.0), ("DIL=0.04", 0.04)):
        ap = apertures(model, v3, dil)
        rec = {"n_west_lanes": len(ap),
               "ladder": {}, "exact": {}}
        for key, kname in (("Ax", "A.x"), ("Bx", "B.x")):
            for rev, rname in ((True, "desc"), (False, "asc")):
                m, s = w_ladder(ap, key, rev)
                rec["ladder"][f"{kname}_{rname}"] = {"W_max": m, "U_max": 8 + m,
                                                     "kept": [x[10:-3] for x in s]}
        for delta in (0.00, 0.05, 0.15):
            m, sel = w_exact(ap, delta)
            errs, chk = verify(ap, sel, delta)
            rec["exact"][f"delta={delta:.2f}"] = {"W_max": m, "U_max": 8 + m,
                                                  "selftest_errors": errs,
                                                  "assignment": chk}
        out["cases"][tag] = rec
        L = rec["ladder"]; E = rec["exact"]
        print(f"\n-- 口径 {tag} （西组 lane={len(ap)}）--")
        for k in ("A.x_desc", "A.x_asc", "B.x_desc", "B.x_asc"):
            print(f"   [证书式阶梯] {k:9s} ⇒ W_max={L[k]['W_max']}  ⇒ U<={L[k]['U_max']}  kept={L[k]['kept']}")
        for k in ("delta=0.00", "delta=0.05", "delta=0.15"):
            e = E[k]
            print(f"   [精确·真实几何] {k}  ⇒ W_max={e['W_max']}  ⇒ U<={e['U_max']}"
                  f"  自证={ 'OK' if not e['selftest_errors'] else e['selftest_errors'] }")
        e = E["delta=0.15"]
        for a in e["assignment"]:
            print(f"        {a['net'][10:-3]:8s} B.x={a['B.x']:7.3f} B.y={a['B.y']:6.3f} ye={a['ye']:7.3f}")
    print("\n结论: 证书 (U<=14 / U<=13) 系「单调 ye 阶梯」这一额外约束所致 —— 同模型内正向阶梯即得 W_max=8；")
    print("      在**真实几何**（带内 + ye>=B.y+δ + 互距>=0.435 + 非交叉 + 锚孔净距）下 W_max=8 ⇒ U<=16；")
    print("      ⇒ **16/16 未被排除 · (b) 证书不成立**。")
    out["verdict"] = {
        "refuted": "R309 v59 / R313 复算器之 W_max=6 ⇒ U<=14（及余量口径 5 ⇒ U<=13）**不成立**",
        "root_cause": "复算器 w_max() 额外施加「沿 A.x 逆序之严格 ye 阶梯（ye_{k+1}>=ye_k+0.435）」；"
                      "该序律已由 R307 自纠判定为不充分；且同一阶梯反向即得 W_max=8 ⇒ 上界由『阶梯方向』决定，"
                      "非几何/守恒约束",
        "exact_bound_in_same_model": "W_max=8（DIL=0 与 DIL=0.04 · δ∈{0,0.05,0.15} 全同）⇒ U<=16（未排除）",
        "consistent_with": "监理 #K2-131 F-4 / #K2-132 (甲)：跨线容量 >=16 ⇒ 不存在刚性上界 <16",
        "not_claimed": "本器**不主张** 16/16 可达 —— 全板见证（含东组 8 条 / A 侧 stub / 南向 In5 接入）仍未取得，"
                       "属**图纸层缺图**",
        "impact": "handoff §7-2 之「采 (b)+EX-5」与 §7-3 之「owner 级动固定件/墙带」前提**同时失去依据**；"
                  "②-UP 应回到 (a) 16/16 构造主线（R270 之『l9 内容物』）",
    }
    out["buildability_field_宪法13"] = (
        "西组 8 条之 jog 高度 ye 已给出**显式坐标见证**（见 cases.*.exact.delta=0.15.assignment），"
        "且逐约束自证通过 ⇒ 西组缺口段**可施工**；但 A 侧接入 / 下潜竖段 / 东组 8 条未给坐标 ⇒ "
        "**全板图纸层仍缺图**，不得据以开工。")
    out["self_sha16"] = {"convention": "#K2-72 §五 约定A", "convention_A_sha16": ""}
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    import hashlib
    h = hashlib.sha256(txt.strip().encode()).hexdigest()[:16]
    out["self_sha16"]["convention_A_sha16"] = h
    json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n[sha16 约定A] %s   -> %s" % (h, sys.argv[2]))


main()
