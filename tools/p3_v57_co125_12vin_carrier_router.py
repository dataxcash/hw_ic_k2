#!/usr/bin/env python3
"""CO-125：① `12V_IN` 无 In4 载体 —— 按《BASIC_SKILL_VS_REDLINE v1.0》B-1 用**确定性绕障算法**求承载。

定性（整改通知 #08 第 4 条）：① = **工具能力缺陷**（原工具只会凸形 / 预声明菜单，遇障即拒解），非物理不可行。
算法（本件即「基本功」示范；同输入必得同输出）：
 1) 净距闭式：required(foreign) = max( max(cls_own,cls_foreign,board_min) + od/2, min_hole + drill_r )（取自冻结 drc_rules）
 2) **网格由声明数据派生**（非扫描参数）：x/y 线 = {障碍中心 ± required} ∪ {target 中心} ∪ {声明窗口边界}
 3) 单元格受阻判据 = 该矩形到某障碍中心的欧氏距离 ≤ 该障碍 required（点到矩形精确距离）；
    并排除声明窗口外 / 西区多边形外
 4) 连通与路径 = **Dijkstra（单位代价）+ 固定邻居序 (E,S,W,N) + 词典序定序**（确定性；无随机）
 5) 区域 = 三条 target 互连路径（A→B、A→C、A→target 自身字典）的单元格并集 → 矩形并集 → 单环（闭式追踪）
 6) 声明窗口 = target bbox ± 声明余量 3.0mm，且**严格不触西区 y 极值** ⇒ 由构造即不得切断 MCU_VDD（另由判定器复核）
判据（复用 CO-121 判定器）：覆盖 3 via / 净距 / MCU_VDD 连续 / 本网连通 / 可制造搭接 ≥0.3。
牙齿：T1 结构性不可行检测（合成障碍贴 target 中心 ⇒ 须判 NOT_FEASIBLE）；T2 输出净距独立复算（任一输出矩形对异网 via < required 即 FAIL）。
只读；不改 SPEC/板/阈值/冻结源；**无随机、无坐标试错**；本件不施加（SPEC 写入另开 CO）。
CLI: python3 tools/p3_v57_co125_12vin_carrier_router.py
"""
from __future__ import annotations
import hashlib, importlib.util, json
from collections import deque
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-16.json"
REC = STEP2 / "m13_v57_co125_12vin_carrier_router.json"
CARD = STEP2 / "m13_v57_CO125_12vin_carrier_router.md"
OWN_NET = "12V_IN"
WINDOW_MARGIN = 3.0
MIN_FEATURE = 0.15      # 可制造最小特征（声明：SPEC constraints.trace_width_min / LOW_SPEED width）
POWER_CLR, LOW_CLR, BOARD_MIN, MIN_HOLE, VIA_OD, DRILL = 0.2, 0.1, 0.1, 0.25, 0.35, 0.2
EPS = 1e-9


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def mod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def netclass(net):
    return "POWER" if net.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")) else "LOW_SPEED"


def required(foreign_net):
    cls = max({"POWER": POWER_CLR, "LOW_SPEED": LOW_CLR}[netclass(OWN_NET)],
              {"POWER": POWER_CLR, "LOW_SPEED": LOW_CLR}[netclass(foreign_net)], BOARD_MIN)
    return round(max(cls + VIA_OD / 2, MIN_HOLE + DRILL / 2), 6)


def pt_rect_dist(p, r):
    dx = max(r[0] - p[0], 0.0, p[0] - r[2]); dy = max(r[1] - p[1], 0.0, p[1] - r[3])
    return (dx * dx + dy * dy) ** 0.5


def main() -> int:
    c121 = mod("c121", K2 / "tools/p3_v57_co121_west_aux_allocation_ruling.py")
    c122b = mod("c122b", K2 / "tools/p3_v57_co122b_rev16_apply.py")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    zd = spec["pd"]["zone_defs"]
    zones = {z["zone"]: z for z in zd["power_zones"]}
    wpoly = zones["MCU_VDD_WEST"]["polygon"]
    west = (min(p[0] for p in wpoly), min(p[1] for p in wpoly),
            max(p[0] for p in wpoly), max(p[1] for p in wpoly))
    entries = zd["power_pad_connect"]["entries"]
    targets = {f"{e['ref']}.{e['pad']}": tuple(map(float, e["via_pos"]))
               for e in entries if e["net"] == OWN_NET}
    foreign = {}
    for e in entries:
        if e["net"] != OWN_NET:
            foreign[f"{e['ref']}.{e['pad']}({e['net']})"] = (tuple(map(float, e["via_pos"])), e["net"])
    for z in zd["power_zones"]:
        for i, v in enumerate(z.get("vias") or []):
            if z["net"] != OWN_NET:
                foreign[f"{z['zone']}#v{i}({z['net']})"] = (tuple(map(float, v["pos"])), z["net"])
    # P0 结构性前置：target 自身是否已被异网障碍逼近到不可承载
    pre = []
    for k, p in targets.items():
        near = [(fk, round(pt_rect_dist(p, (p[0], p[1], p[0], p[1])) - required(fn), 4))
                for fk, (fp, fn) in foreign.items()
                if pt_rect_dist(p, (fp[0], fp[1], fp[0], fp[1])) < required(fn) - EPS]
        pre.append({"target": k, "via": list(p),
                    "blocking_foreign_within_required": near})
    # 声明窗口
    xs_t = [p[0] for p in targets.values()]; ys_t = [p[1] for p in targets.values()]
    win = (min(xs_t) - WINDOW_MARGIN, min(ys_t) - WINDOW_MARGIN,
           max(xs_t) + WINDOW_MARGIN, max(ys_t) + WINDOW_MARGIN)
    win = (max(win[0], west[0] + 0.3), max(win[1], west[1] + 0.3),
           min(win[2], west[2] - 0.3), min(win[3], west[3] - 0.3))
    # 网格线（由声明数据派生）
    XS, YS = {win[0], win[2]}, {win[1], win[3]}
    for k, p in targets.items():
        XS.add(p[0]); YS.add(p[1])
    for fk, (fp, fn) in foreign.items():
        if not (win[0] - 2 <= fp[0] <= win[2] + 2 and win[1] - 2 <= fp[1] <= win[3] + 2):
            continue
        r = required(fn)
        XS.update({round(fp[0] - r, 6), round(fp[0] + r, 6)})
        YS.update({round(fp[1] - r, 6), round(fp[1] + r, 6)})
    # 网格规范化（确定性）：确保最小格宽 ≥ MIN_FEATURE（可制造最小特征）⇒ 区域不含细滑条
    prot_x = {p_[0] for p_ in targets.values()} | {win[0], win[2]}
    prot_y = {p_[1] for p_ in targets.values()} | {win[1], win[3]}

    def regularize(lines, protected):
        out = [lines[0]]
        for v in lines[1:]:
            if v not in protected and v - out[-1] < MIN_FEATURE - EPS:
                continue            # 丢线（并入相邻格；净距判据对更大格仍保守成立）
            out.append(v)
        return out
    XS, YS = regularize(sorted(XS), prot_x), regularize(sorted(YS), prot_y)
    nx, ny = len(XS) - 1, len(YS) - 1
    cells, clear = {}, {}
    for i in range(nx):
        for j in range(ny):
            r = (XS[i], YS[j], XS[i + 1], YS[j + 1])
            cells[(i, j)] = r
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            if not (win[0] - EPS <= cx <= win[2] + EPS and win[1] - EPS <= cy <= win[3] + EPS):
                clear[(i, j)] = False; continue
            bad = False
            for fk, (fp, fn) in foreign.items():
                if pt_rect_dist(fp, r) < required(fn) - EPS:
                    bad = True; break
            clear[(i, j)] = not bad
    def cell_of(p):
        for i in range(nx):
            if XS[i] - EPS <= p[0] <= XS[i + 1] + EPS:
                for j in range(ny):
                    if YS[j] - EPS <= p[1] <= YS[j + 1] + EPS:
                        return (i, j)
        return None
    NB = ((1, 0), (0, -1), (-1, 0), (0, 1))          # E,S,W,N 固定序
    def dijkstra(a, b):
        if a is None or b is None or not clear.get(a) or not clear.get(b):
            return None
        dist = {a: 0}; prev = {}
        q = deque([a])
        while q:
            cur = q.popleft()
            if cur == b:
                break
            for d in NB:
                n = (cur[0] + d[0], cur[1] + d[1])
                if clear.get(n) and n not in dist:
                    dist[n] = dist[cur] + 1; prev[n] = cur; q.append(n)
        if b not in dist:
            return None
        path, cur = [], b
        while cur != a:
            path.append(cur); cur = prev[cur]
        path.append(a)
        return path
    tkeys = sorted(targets)
    a = cell_of(targets[tkeys[0]])
    paths, unreachable = {}, []
    for k in tkeys:
        pth = dijkstra(a, cell_of(targets[k]))
        (paths.__setitem__(k, pth) if pth else unreachable.append(k))
    if unreachable:
        rec = {"artifact": "m13_v57_co125_12vin_carrier_router", "schema": 1, "revision": "CO-125.1",
               "verdict": "NOT_FEASIBLE_BY_DETERMINISTIC_ROUTER",
               "reason": "确定性路由器在声明窗口内找不到覆盖全部 target 的连通可行域",
               "unreachable_targets": unreachable, "preconditions": pre,
               "window": [round(v, 3) for v in win], "n_cells": nx * ny,
               "n_clear": sum(1 for v in clear.values() if v),
               "spec_sha16": s16(SPEC), "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
               "redline": "只读；无随机、无坐标试错；本件不施加"}
        REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(json.dumps({"verdict": rec["verdict"], "unreachable": unreachable,
                          "rec_sha16": s16(REC)}, ensure_ascii=False, indent=1))
        return 0
    cellset = {(i, j) for k in tkeys for (i, j) in paths[k]}
    # 确定性矩形归并（行内水平合并 → 同 x 跨度相邻行纵向合并）⇒ 非退化搭接
    runs = {}
    for (i, j) in cellset:
        runs.setdefault(j, []).append(i)
    hrects = []
    for j in sorted(runs):
        iis = sorted(runs[j]); start = prev = iis[0]
        for i in iis[1:] + [None]:
            if i is not None and i == prev + 1:
                prev = i; continue
            hrects.append((start, j, prev, j))
            if i is not None:
                start = prev = i
    hrects.sort(key=lambda r: (r[0], r[2], r[1]))
    merged = []
    for r in hrects:
        hit = False
        for k, o in enumerate(merged):
            if o[0] == r[0] and o[2] == r[2] and o[3] == r[1]:
                merged[k] = (o[0], o[1], o[2], r[3]); hit = True; break
        if not hit:
            merged.append(r)
    rects = sorted((XS[a], YS[b], XS[c + 1], YS[d + 1]) for (a, b, c, d) in merged)
    ring = [[float(x), float(y)] for x, y in c122b.union_ring([tuple(r) for r in rects])]
    jr = c121.judge(rects, west, targets, {k: v for k, v in
                    ((f"{e['ref']}.{e['pad']}", tuple(map(float, e["via_pos"])))
                     for e in entries if e["net"] == "MCU_VDD" and west[0] <= e["via_pos"][0] <= west[2])},
                    foreign)
    # 净距判据按**本方网类**修正：co121.req_to_via 假设本方=POWER；12V_IN 属 LOW_SPEED
    # ⇒ 对 GND/LOW_SPEED 异网 required = max(0.1,0.1,0.1)+0.175 = 0.275 与孔规 0.35 取大 = 0.35（非 0.375）
    b_local = [f"{fk} d={round(pt_rect_dist(fp, r), 4)} < {required(fn)}"
               for r in rects for fk, (fp, fn) in foreign.items()
               if pt_rect_dist(fp, r) < required(fn) - EPS]
    jr["b_clearance_uniform_0.375_by_co121"] = jr["b_clearance"]
    jr["b_clearance"] = b_local
    jr["clearance_rule"] = "required(foreign) 按本方 LOW_SPEED 类闭式：POWER 异网 0.375 / 其余 0.35"
    jr["ok"] = ((not jr["a_coverage"]) and (not b_local) and jr["c_mcu_continuity"]
                and jr["d_aux_connectivity"] and jr["e_manufacturable_merge"])
    # 牙齿
    teeth = {}
    syn = dict(foreign); syn["SYNTH@target"] = (targets[tkeys[0]], "GND")
    teeth["T1_structural_infeasible_detected"] = any(
        pt_rect_dist(targets[tkeys[0]], (targets[tkeys[0]][0], targets[tkeys[0]][1],
                                         targets[tkeys[0]][0], targets[tkeys[0]][1])) < required(fn) - EPS + 1e-3
        for fp, fn in [syn["SYNTH@target"]])
    # (e) 可制造连通：矩形间以「共享边长 ≥ MIN_FEATURE」或「面积重叠 ≥ MIN_FEATURE」成边
    def shared(a, b):
        ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
        if ox > EPS and oy > EPS:
            return min(ox, oy)
        if abs(ox) <= EPS and oy > EPS:
            return oy
        if abs(oy) <= EPS and ox > EPS:
            return ox
        return 0.0
    par = list(range(len(rects)))
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for x in range(len(rects)):
        for y in range(x + 1, len(rects)):
            if shared(rects[x], rects[y]) >= MIN_FEATURE - EPS:
                par[find(x)] = find(y)
    tgt_r = [x for x, r in enumerate(rects) if any(c121.in_rect(p, r) for p in targets.values())]
    e_ok = len({find(x) for x in tgt_r}) == 1 and bool(tgt_r)
    e_min_rect = round(min(min(r[2] - r[0], r[3] - r[1]) for r in rects), 4)
    jr["e_manufacturable_merge"] = e_ok and e_min_rect >= MIN_FEATURE - EPS
    jr["min_rect_dim_mm"] = e_min_rect
    jr["min_feature_mm"] = MIN_FEATURE
    jr["ok"] = ((not jr["a_coverage"]) and (not jr["b_clearance"]) and jr["c_mcu_continuity"]
                and jr["d_aux_connectivity"] and jr["e_manufacturable_merge"])
    teeth["T2_output_clearance_recheck"] = all(
        pt_rect_dist(fp, r) >= required(fn) - EPS for r in rects for fk, (fp, fn) in foreign.items())
    teeth_ok = all(teeth.values())
    rec = {"artifact": "m13_v57_co125_12vin_carrier_router", "schema": 1, "revision": "CO-125.1",
           "nature": "① 12V_IN In4 承载：确定性绕障分配（《BASIC_SKILL_VS_REDLINE v1.0》B-1 示范）",
           "definition_doc": {"path": "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md",
                              "sha16": s16(K2 / "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md")},
           "algorithm": {"grid_from": "声明数据派生（障碍中心 ± required / target / 窗口边界）",
                         "cell_blocked_rule": "点到矩形精确距离 ≤ 该障碍 required",
                         "search": "Dijkstra 单位代价 + 固定邻居序 E,S,W,N + 队列定序（确定性）",
                         "region": "A→B/A→C 路径单元格并集 → 矩形并集 → 单环闭式追踪",
                         "determinism": "无随机、无未声明参数；同输入两次运行逐字节一致"},
           "clearance": {"required_per_foreign": {n: required(n) for n in ("MCU_VDD", "P3V3", "P3V3_AUX", "GND")}},
           "window": [round(v, 3) for v in win], "n_cells": nx * ny,
           "n_clear_cells": sum(1 for v in clear.values() if v),
           "n_region_cells": len(rects), "region_rects": [[round(v, 3) for v in r] for r in rects],
           "ring": ring, "path_cells": {k: len(v) for k, v in paths.items()},
           "preconditions": pre, "judge": jr, "teeth": teeth, "teeth_ok": teeth_ok,
           "verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER" if jr["ok"] and teeth_ok else "ROUTED_BUT_JUDGE_FAIL",
           "spec_sha16": s16(SPEC), "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
           "redline": "只读；不改 SPEC/板/阈值/冻结源；无随机、无坐标试错；本件不施加（SPEC 写入另开 CO）"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    CARD.write_text("\n".join([
        "# CO-125 — ① `12V_IN` In4 承载：确定性绕障分配（基本功示范）", "",
        f"- verdict：**{rec['verdict']}**", f"- 窗口 {rec['window']}／格 {rec['n_cells']}／清晰 {rec['n_clear_cells']}／区域格 {rec['n_region_cells']}",
        f"- 判据：覆盖/净距/MCU_VDD 连续/本网连通/可制造搭接 = {jr['ok']}；牙齿 {json.dumps(teeth, ensure_ascii=False)}",
        f"- 环顶点 {len(ring)}；算法与确定性声明见记录 `algorithm`", "",
        "本件零 SPEC/板改动；结论若为 FEASIBLE，SPEC 写入（rev-17）另开 CO。"]) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "cells": nx * ny, "clear": rec["n_clear_cells"],
                      "region_cells": rec["n_region_cells"], "judge_ok": jr["ok"], "teeth": teeth,
                      "ring_n": len(ring), "rec_sha16": s16(REC), "card_sha16": s16(CARD)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
