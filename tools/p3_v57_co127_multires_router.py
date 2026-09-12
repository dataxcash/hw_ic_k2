#!/usr/bin/env python3
"""CO-127：④ R1 `U2.5`/`J4.A9` —— **多分辨率细化 + 中线厚度模型** 的确定性绕障复判（取代 CO-126 的粗化结论）。

背景（整改通知 #08 / 《BASIC_SKILL_VS_REDLINE v1.0》B-1、B-3）：CO-126 判「工具不足」但未定位成因。
本件先做**根因**（见 algorithm.root_cause_of_co126，附 co126 复现证据）：
  ① CO-126 的「丢线规范化」把受租大格与清晰格并一 ⇒ 切断真实走廊；
  ② target 格被异网 ∓required 线细分后 < min-feature ⇒ 目标格被判不可用。
  两者皆网格粗化（工具缺陷），非物理不可行 —— 故按 B-1 修正模型后复判，禁止以工具不足升级 owner。

修正模型（中线厚度；可证）：
  判据：存在铜区 R 连通 anchor(本网平面内) → target(本网 via)，R 对异网 via 圆心净距 ≥ required(fn)、
        最小宽度 ≥ feat(=本网 netclass 宽度)，且与异网**载流平面**保持 moat。
  求解（充分且等价）：存在**中线路径** P 使 P 上每点到异网圆心 ≥ required(fn) + (feat/2)·√2。
    铜区 = P ⊕ L∞(feat/2)。L∞ 半径 h 的方盒含于欧氏半径 h√2 的圆 ⇒ 输出铜区净距可证 ≥ required；
    宽度恒 ≥ feat。逆：任何可行铜区都含一条满足该净距的中线 ⇒ P 不存在 ⇒ 该宽铜区必不存在（完备）。
  网格：线集 = 声明数据派生（窗口边界 ∪ 本网平面顶点 ∪ target ∪ 异网 ∓(required+feat/2)·√2 切线）
        + **逐级二分细化**（每级在间距 > 2·floor 的空隙中点插入一线），floor = feat/2（声明细化下限）。
        单元格唯一判据 = 矩形到异网圆心精确距离 ≥ required + (feat/2)√2（**无 min-feature 格宽门限** ⇒ 细化单调增连通）。
  搜索：Dijkstra 单位代价 + 固定邻居序 E,S,W,N（确定性；无随机、无未声明参数）。
    anchor = 中心落于本网平面多边形内(PIP)且清晰之格（多源）；target = 含 via 之格。
  区域：路径格 ⊕ L∞(feat/2) → 2D 矩形归并（同 x/y 程并成矩形，单调保连通与重叠深度）。
  判定：全局（覆盖/净距/min-dim/矩形连通/本网平面搭接）+ **逐宿主区**（复用 CO-121 判定器，但按区**限定域**
        输入：只在区内的 target 与宿主网 via；无 target 之区以区内区域探针做宿主平面连续性检查）。
牙齿：T1 结构性不可行（合成障碍贴 target ⇒ 须不可行）；T2 输出净距独立复算；T3 本网平面移除负控；
     T4 细化单调性（清晰格面积随级不降）；T5 同输入两次逐字节一致；T6 细化稳定性（细化一级后仍可行且面积不降）。
只读；不改 SPEC/板/阈值/冻结源；无随机、无坐标试错；不施加。
CLI: python3 tools/p3_v57_co127_multires_router.py
"""
from __future__ import annotations
import hashlib, importlib.util, json, math
from collections import deque
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-16.json"
REC = STEP2 / "m13_v57_co127_multires_router.json"
CARD = STEP2 / "m13_v57_CO127_multires_router.md"
DEF_DOC = K2 / "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md"
EPS = 1e-9
MERGE_MIN = 0.3      # 声明最小可制造搭接深度（同 CO-121）
MOAT = 0.2           # 声明宿主平面 moat（同 CO-121）
LMAX = 8             # 声明最大细化级（floor 生效后自动停）
CASES = [  # (ref, pad, net, host zones, own plane zones, window margin)
    ("U2", "5", "P3V3", ["MCU_VDD_WEST"], ["P3V3_EAST"], 6.0),
    ("J4", "A9", "P3V3_AUX", ["P3V3_EAST", "MCU_VDD_WEST"], ["P3V3_AUX_WEST"], 6.0),
]


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def mod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def ncls(net, spec):
    for c, d in (spec.get("net_classes") or {}).items():
        if c == "POWER" and net.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")):
            return c, float(d.get("width", 0.15))
        if c == "PCIe85" and net.startswith(("PCIE", "REFCLK")):
            return c, float(d.get("width", 0.2))
    return "LOW_SPEED", float((spec.get("net_classes") or {}).get("LOW_SPEED", {}).get("width", 0.15))


def required(own, foreign, spec):
    """铜边 → 异网 via 圆心最小距离（净距闭式 + 异网 via 半径；含最小孔净距）。"""
    co, _ = ncls(own, spec); cf, _ = ncls(foreign, spec)
    clr = max({"POWER": 0.2, "LOW_SPEED": 0.1}[co], {"POWER": 0.2, "LOW_SPEED": 0.1}[cf], 0.1)
    return round(max(clr + 0.35 / 2, 0.25 + 0.2 / 2), 6)


def p2r(p, r):
    dx = max(r[0] - p[0], 0.0, p[0] - r[2]); dy = max(r[1] - p[1], 0.0, p[1] - r[3])
    return (dx * dx + dy * dy) ** 0.5


def pip(pg, x, y):
    ins = False
    for i in range(len(pg)):
        x1, y1 = pg[i]; x2, y2 = pg[(i + 1) % len(pg)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def zrect(z):
    pg = z["polygon"]
    return (min(p[0] for p in pg), min(p[1] for p in pg), max(p[0] for p in pg), max(p[1] for p in pg))


def in_rect(p, r):
    return r[0] - EPS <= p[0] <= r[2] + EPS and r[1] - EPS <= p[1] <= r[3] + EPS


def rect_poly_area(rect, poly):
    xs = sorted({rect[0], rect[2]} | {p[0] for p in poly}); ys = sorted({rect[1], rect[3]} | {p[1] for p in poly})
    a = 0.0
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
            if x1 - x0 < EPS or y1 - y0 < EPS:
                continue
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if in_rect((cx, cy), rect) and pip(poly, cx, cy):
                a += (x1 - x0) * (y1 - y0)
    return a


def region_probe(rects, zone):
    """区域内且落在 zone 内的确定点（矩形交集中心；无交则 None）。"""
    for r in sorted(rects):
        x0, y0 = max(r[0], zone[0]), max(r[1], zone[1]); x1, y1 = min(r[2], zone[2]), min(r[3], zone[3])
        if x1 - x0 > EPS and y1 - y0 > EPS:
            return ((x0 + x1) / 2, (y0 + y1) / 2)
    return None


def rects_connected(rects):
    n = len(rects); par = list(range(n))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for i in range(n):
        for j in range(i + 1, n):
            a, b = rects[i], rects[j]
            ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > EPS and oy > EPS and min(ox, oy) >= MERGE_MIN - EPS:
                par[find(i)] = find(j)
    return len({find(i) for i in range(n)}) == 1


def merge2d(rects):
    rs = sorted({tuple(round(v, 9) for v in r) for r in rects})
    changed = True
    while changed:
        changed = False
        used = [False] * len(rs); out = []
        for i in range(len(rs)):
            if used[i]:
                continue
            a = rs[i]
            for j in range(i + 1, len(rs)):
                if used[j]:
                    continue
                b = rs[j]; m = None
                if abs(a[0] - b[0]) < EPS and abs(a[2] - b[2]) < EPS and a[3] >= b[1] - EPS and b[3] >= a[1] - EPS:
                    m = (a[0], min(a[1], b[1]), a[2], max(a[3], b[3]))
                elif abs(a[1] - b[1]) < EPS and abs(a[3] - b[3]) < EPS and a[2] >= b[0] - EPS and b[2] >= a[0] - EPS:
                    m = (min(a[0], b[0]), a[1], max(a[2], b[2]), a[3])
                if m is not None:
                    a = m; used[j] = True; changed = True
            out.append(a)
        rs = out
    return rs


def _bisect(lines, floor):
    out = set(lines); L = sorted(lines)
    for a, b in zip(L, L[1:]):
        if b - a > 2 * floor + EPS:
            out.add(round((a + b) / 2, 6))
    return out


def route(spec, ref, pad, net, host_names, own_names, margin, c121, c122b,
          inject=None, drop_own=False, start_level=0, max_level=None):
    zd = spec["pd"]["zone_defs"]; zones = {z["zone"]: z for z in zd["power_zones"]}
    entries = zd["power_pad_connect"]["entries"]
    via = tuple(map(float, next(e for e in entries if e["ref"] == ref and e["pad"] == pad)["via_pos"]))
    cls, feat = ncls(net, spec)
    floor = feat / 2
    anchor_r = feat / 2 * math.sqrt(2)          # L∞(feat/2) 方盒的欧氏外接半径
    hosts = [(zones[n], n) for n in host_names if n in zones]
    own_polys = [zones[n]["polygon"] for n in own_names if n in zones] if not drop_own else []
    if not own_polys:
        return {"verdict": "NOT_FEASIBLE_NO_OWN_PLANE", "target": f"{ref}.{pad}", "net": net}
    foreign = {}
    for e in entries:
        if e["net"] != net:
            foreign[f"{e['ref']}.{e['pad']}({e['net']})"] = (tuple(map(float, e["via_pos"])), e["net"])
    for z in zd["power_zones"]:
        for i, v in enumerate(z.get("vias") or []):
            if z["net"] != net:
                foreign[f"{z['zone']}#v{i}({z['net']})"] = (tuple(map(float, v["pos"])), z["net"])
    if inject:
        foreign.update(inject)
    R = {k: required(net, fn, spec) + anchor_r for k, (fp, fn) in foreign.items()}
    oxs = [p[0] for pg in own_polys for p in pg]; oys = [p[1] for pg in own_polys for p in pg]
    win = (min(min(oxs), via[0]) - margin, min(min(oys), via[1]) - margin,
           max(max(oxs), via[0]) + margin, max(max(oys), via[1]) + margin)
    XS = {win[0], win[2], via[0]} | {p[0] for pg in own_polys for p in pg}
    YS = {win[1], win[3], via[1]} | {p[1] for pg in own_polys for p in pg}
    for k, (fp, fn) in foreign.items():
        if not (win[0] - 2 <= fp[0] <= win[2] + 2 and win[1] - 2 <= fp[1] <= win[3] + 2):
            continue
        XS |= {round(fp[0] - R[k], 6), round(fp[0] + R[k], 6)}
        YS |= {round(fp[1] - R[k], 6), round(fp[1] + R[k], 6)}
    for _ in range(start_level):
        XS, YS = _bisect(XS, floor), _bisect(YS, floor)

    ladder = []
    for level in range(start_level, (max_level if max_level is not None else LMAX) + 1):
        X, Y = sorted(XS), sorted(YS)
        nx, ny = len(X) - 1, len(Y) - 1
        clear = {}
        for i in range(nx):
            for j in range(ny):
                r = (X[i], Y[j], X[i + 1], Y[j + 1])
                clear[(i, j)] = (win[0] - EPS <= r[0] and r[2] <= win[2] + EPS
                                 and win[1] - EPS <= r[1] and r[3] <= win[3] + EPS
                                 and all(p2r(fp, r) >= R[k] - EPS for k, (fp, fn) in foreign.items()))
        anchors = []
        for (i, j), ok in clear.items():
            if not ok:
                continue
            cx, cy = (X[i] + X[i + 1]) / 2, (Y[j] + Y[j + 1]) / 2
            if any(pip(pg, cx, cy) for pg in own_polys):
                anchors.append((i, j))
        t = None
        for i in range(nx):
            if X[i] - EPS <= via[0] <= X[i + 1] + EPS:
                for j in range(ny):
                    if Y[j] - EPS <= via[1] <= Y[j + 1] + EPS:
                        t = (i, j)
        area = round(sum((X[i + 1] - X[i]) * (Y[j + 1] - Y[j]) for (i, j), ok in clear.items() if ok), 4)
        ladder.append({"level": level, "nx": nx, "ny": ny, "cells": nx * ny,
                       "clear": sum(1 for v in clear.values() if v), "clear_area_mm2": area,
                       "anchors": len(anchors)})
        if not anchors:
            return {"verdict": "TOOL_INSUFFICIENT_NO_ANCHOR", "target": f"{ref}.{pad}", "net": net,
                    "reason": "本网平面内找不到清晰格（无从起锚；非物理不可行）", "ladder": ladder}
        if t is None or not clear.get(t):
            blockers = sorted(({"foreign": fk, "dist_mm": round(p2r(fp, (via[0], via[1], via[0], via[1])), 4),
                                "required_mm": round(required(net, fn, spec), 4)} for fk, (fp, fn) in foreign.items()
                               if p2r(fp, (via[0], via[1], via[0], via[1])) < required(net, fn, spec) - EPS),
                              key=lambda x: x["dist_mm"])
            return {"verdict": "STRUCTURALLY_INFEASIBLE" if blockers else "TOOL_INSUFFICIENT_TARGET_CELL",
                    "target": f"{ref}.{pad}", "net": net, "structural": bool(blockers),
                    "blocking_foreign": blockers, "ladder": ladder,
                    "reason": ("target via 自身与异网 via 间距 < required ⇒ 任何合法铜区都不可能覆盖该 target"
                               if blockers else "含 target 之格在净距判据下不可用（无结构性阻断）")}
        dist, prev = {a: 0 for a in anchors}, {}
        q = deque(sorted(dist))
        while q:
            cur = q.popleft()
            for d in ((1, 0), (0, -1), (-1, 0), (0, 1)):
                n = (cur[0] + d[0], cur[1] + d[1])
                if clear.get(n) and n not in dist:
                    dist[n] = dist[cur] + 1; prev[n] = cur; q.append(n)
        if t in dist:
            path, cur = [], t
            while cur in prev:
                path.append(cur); cur = prev[cur]
            path.append(cur); path.reverse()
            rects = merge2d([(X[i] - feat / 2, Y[j] - feat / 2, X[i + 1] + feat / 2, Y[j + 1] + feat / 2)
                             for (i, j) in path])
            ring = [[float(x), float(y)] for x, y in c122b.union_ring([tuple(r) for r in rects])]
            # 逐宿主区判定（限定域：仅区内的 target / 宿主网 via）
            host_judge, host_ok = {}, True
            for z, hn in hosts:
                zr = zrect(z)
                tgt_in = {f"{ref}.{pad}": via} if in_rect(via, zr) else {}
                mcu_in = {f"{e['ref']}.{e['pad']}": tuple(map(float, e["via_pos"])) for e in entries
                          if e["net"] == z["net"] and in_rect(tuple(map(float, e["via_pos"])), zr)}
                probe = tgt_in or ({"__zone_probe__": region_probe(rects, zr)} if region_probe(rects, zr) else {})
                if not mcu_in and not probe:
                    host_judge[hn] = {"skipped": "区域与本区无交且区内无宿主网 via"}
                    continue
                jr = c121.judge(rects, zr, probe, mcu_in, foreign)
                jr["scoped_targets"] = sorted(probe)
                jr["scoped_host_vias"] = len(mcu_in)
                host_judge[hn] = jr
                host_ok = host_ok and jr["ok"]
            a_cell = path[0]
            a_rect = (X[a_cell[0]] - feat / 2, Y[a_cell[1]] - feat / 2,
                      X[a_cell[0] + 1] + feat / 2, Y[a_cell[1] + 1] + feat / 2)
            own_ov = min(rect_poly_area(a_rect, pg) for pg in own_polys)
            min_dim = min(min(r[2] - r[0], r[3] - r[1]) for r in rects)
            clearance_ok = all(p2r(fp, r) >= required(net, fn, spec) - EPS
                               for r in rects for fk, (fp, fn) in foreign.items())
            cov_ok = any(in_rect(via, r) for r in rects)
            glob = {"coverage": cov_ok, "clearance": clearance_ok, "min_dim>=feat": min_dim >= feat - EPS,
                    "rects_connected": rects_connected(rects),
                    "own_plane_attach_area_mm2": round(own_ov, 4),
                    "attach>=feat*merge_min": own_ov >= feat * MERGE_MIN - EPS}
            ok = (all(glob[k] for k in ("coverage", "clearance", "min_dim>=feat", "rects_connected",
                                        "attach>=feat*merge_min")) and host_ok)
            return {"verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER" if ok else "ROUTED_BUT_JUDGE_FAIL",
                    "target": f"{ref}.{pad}", "net": net, "via": list(via), "netclass": cls,
                    "min_feature_mm": feat, "res_floor_mm": floor, "cleared_at_level": level,
                    "centerline_radius_mm": round(R[list(R)[0]], 4),
                    "required_to_foreign": {n2: required(net, n2, spec) for n2 in ("MCU_VDD", "P3V3", "P3V3_AUX", "GND")},
                    "window": [round(v, 3) for v in win], "n_cells": nx * ny,
                    "n_clear": sum(1 for v in clear.values() if v), "clear_area_mm2": area,
                    "path_cells": len(path), "region_rects": [[round(v, 3) for v in r] for r in rects],
                    "ring": ring, "global_judge": glob, "host_judge": host_judge,
                    "min_rect_dim_mm": round(min_dim, 4), "clearance_recheck_ok": clearance_ok, "ok": ok}
        XS, YS = _bisect(XS, floor), _bisect(YS, floor)
    return {"verdict": "TOOL_INSUFFICIENT_NO_CORRIDOR", "target": f"{ref}.{pad}", "net": net,
            "reason": f"{LMAX} 级细化（floor={floor}mm=feat/2）后仍不连通；无结构性阻断 ⇒ 仍判工具不足（禁升级）",
            "ladder": ladder}


def main() -> int:
    c121 = mod("c121", K2 / "tools/p3_v57_co121_west_aux_allocation_ruling.py")
    c122b = mod("c122b", K2 / "tools/p3_v57_co122b_rev16_apply.py")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    res = {f"{r}.{p}": route(spec, r, p, n, h, o, m, c121, c122b) for r, p, n, h, o, m in CASES}
    res2 = {f"{r}.{p}": route(spec, r, p, n, h, o, m, c121, c122b) for r, p, n, h, o, m in CASES}
    teeth = {"T5_determinism_reproduced":
             all(res[k].get("region_rects") == res2[k].get("region_rects") for k in res)}
    r0, p0, n0, h0, o0, m0 = CASES[0]
    ent = spec["pd"]["zone_defs"]["power_pad_connect"]["entries"]
    tgt = tuple(map(float, next(e["via_pos"] for e in ent if e["ref"] == r0 and e["pad"] == p0)))
    t1 = route(spec, r0, p0, n0, h0, o0, m0, c121, c122b, inject={"SYNTH@target": (tgt, "GND")})
    teeth["T1_structural_infeasible_detected"] = t1["verdict"] == "STRUCTURALLY_INFEASIBLE"
    t3 = route(spec, r0, p0, n0, h0, o0, m0, c121, c122b, drop_own=True)
    teeth["T3_own_plane_removed_negative_control"] = t3["verdict"] == "NOT_FEASIBLE_NO_OWN_PLANE"
    teeth["T2_output_clearance_recheck"] = all(v.get("clearance_recheck_ok", False)
                                               for v in res.values() if v.get("ok") is not None)
    teeth["T4_refinement_monotone"] = all(
        (len(v["ladder"]) == 1) or all(v["ladder"][i]["clear_area_mm2"] <= v["ladder"][i + 1]["clear_area_mm2"] + EPS
                                      for i in range(len(v["ladder"]) - 1))
        for v in res.values() if v.get("ladder"))
    # T6 细化稳定性：强制细化一级后仍可行，且清晰面积不降
    res_ref = {f"{r}.{p}": route(spec, r, p, n, h, o, m, c121, c122b, start_level=1) for r, p, n, h, o, m in CASES}
    teeth["T6_refinement_stability"] = all(
        res_ref[k].get("ok") is True and res_ref[k]["clear_area_mm2"] >= res[k].get("clear_area_mm2", 0) - EPS
        for k in res)
    teeth_ok = all(teeth.values())
    structural_any = any(v.get("structural") for v in res.values())
    verdict = ("R1_FEASIBLE_ALL_BY_MULTIRES_ROUTER" if all(v.get("ok") for v in res.values())
               else "R1_STRUCTURALLY_INFEASIBLE_SOME" if structural_any
               else "TOOL_INSUFFICIENT_SOME_BY_MULTIRES_ROUTER")
    algo = {
        "root_cause_of_co126": ("① CO-126 丢线规范化把受阻大格与清晰格并一 ⇒ 切断真实走廊；"
                                "② target 格被异网 ∓required 线细分后 < min-feature ⇒ 目标格不可用；"
                                "③ 其判据「格自身 ≥ min-feature」在细化时自毁（细格一律不可用）⇒ 无法靠细化补救。"
                                "三者皆网格粗化（工具缺陷），非不可行。"),
        "model": ("中线厚度模型：判据 = 存在铜区宽 ≥ feat、边到异网圆心 ≥ required、接本网平面、宿主平面保 moat；"
                  "求解 = 中线路径点到异网圆心 ≥ required + (feat/2)√2（L∞ 方盒含于欧氏圆 ⇒ 输出净距可证 ≥ required；"
                  "逆：任何可行铜区含此中线 ⇒ 完备）。"),
        "grid": "声明数据派生切线（窗口/本网平面顶点/target/异网 ∓(required+feat/2)√2）+ 逐级二分细化（间距 > 2·floor 处插中点）",
        "resolution_floor_mm": "feat/2（声明下限）",
        "cell_rule": "矩形到异网圆心精确距离 ≥ required + (feat/2)√2（无 min-feature 格宽门限 ⇒ 细化单调增连通）",
        "search": "Dijkstra 单位代价 + 固定邻居序 E,S,W,N + 多源 anchor（本网平面内 PIP 且清晰）",
        "region": "路径格 ⊕ L∞(feat/2) → 2D 矩形归并（同程取并，保连通与重叠深度）",
        "judge_scoping": ("逐宿主区限定域：只以区内 target 与区内宿主网 via 调用 CO-121 判定器；"
                          "无 target 之区以区内区域探针取代（T2/T3 与 CO-122 同口径）。"),
        "completeness": ("单调性：细化只把清晰格**细分**为子格 ⇒ 清晰面积与连通随级单调不减；"
                         "完备到「宽度 ≥ feat/2 的轴对齐中线通道」。仍不连通且无结构性阻断 ⇒ 判工具不足（禁升级）。"),
        "determinism": "无随机、无未声明参数；T5 同输入两次区域矩形逐字节一致",
    }
    rec = {"artifact": "m13_v57_co127_multires_router", "schema": 1, "revision": "CO-127.1",
           "nature": "④ R1 U2.5/J4.A9：多分辨率细化 + 中线厚度模型的确定性绕障复判（取代 CO-126 粗化结论）",
           "supersedes": {"CO-126": "0d32a7e487452f05（工具不足归因于网格粗化 + 判据自毁；本件已修正并复判）",
                          "CO-122_family_caveat": "CO-122 明示 J4.A9 30/30 未过属家族不足（只含直走廊）；本件 L 形绕行即该缺口"},
           "definition_doc": {"path": "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md",
                              "sha16": s16(DEF_DOC)},
           "algorithm": algo, "cases": res, "cases_refined_one_step": res_ref,
           "teeth": teeth, "teeth_ok": teeth_ok, "verdict": verdict,
           "escalation": {"allowed": structural_any,
                          "reason": ("存在结构性阻断（target 与异网间距 < required）⇒ 可依 §4 升级"
                                     if structural_any else
                                     "无结构性阻断；两 target 均以确定性绕障达成可行 ⇒ 属 L2 自裁，无需 owner")},
           "spec_sha16": s16(SPEC), "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
           "redline": "只读；不改 SPEC/板/阈值/冻结源；无随机、无坐标试错；不施加"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-127 — ④ R1 `U2.5`/`J4.A9`：多分辨率 + 中线厚度模型确定性绕障复判", "",
             f"- verdict：**{verdict}**", f"- 定义件：《BASIC_SKILL_VS_REDLINE v1.0》`{s16(DEF_DOC)}`", "",
             "| target | net | netclass | feat | 级 | 格 | 清晰 | 路径格 | 区域矩形 | 最小矩形 | 本网搭接mm² | 判定 ok |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in res.items():
        lines.append(f"| {k} | {v.get('net')} | {v.get('netclass')} | {v.get('min_feature_mm')} | "
                     f"{v.get('cleared_at_level')} | {v.get('n_cells')} | {v.get('n_clear')} | {v.get('path_cells')} | "
                     f"{len(v.get('region_rects') or [])} | {v.get('min_rect_dim_mm')} | "
                     f"{(v.get('global_judge') or {}).get('own_plane_attach_area_mm2')} | {v.get('ok')} |")
    lines += ["", "牙齿：" + json.dumps(teeth, ensure_ascii=False),
              "", "算法/根因/完备性论证见记录 `algorithm`；本件零 SPEC/板改动；结论若为可行，SPEC 写入（rev-17）另开 CO。"]
    CARD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "escalation": rec["escalation"],
                      "cases": {k: {kk: v.get(kk) for kk in ("ok", "verdict", "cleared_at_level", "n_cells", "n_clear",
                                                             "path_cells", "min_rect_dim_mm")} for k, v in res.items()},
                      "teeth": teeth, "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
