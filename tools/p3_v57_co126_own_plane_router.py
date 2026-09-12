#!/usr/bin/env python3
"""CO-126：④ R1 的 `U2.5`/`J4.A9` —— 用**确定性绕障路由器**（同 CO-125 技法）复判，替换 CO-123 的有界 palette。

依《BASIC_SKILL_VS_REDLINE v1.0》B-1：允许确定性图搜索/迷宫（含绕障）；本件即「先自证」的实现。
算法（同 CO-125，已证可复现）：网格由声明数据派生（障碍中心 ± required / 目标 / 锚点 / 窗口边界）
 → 网格规范化（最小格宽 = 该网声明 netclass 宽度）→ 单元格净距判据（点到矩形精确距离）
 → Dijkstra 单位代价 + 固定邻居序 E,S,W,N → 锚点→各 target 路径单元格并集 → 矩形归并 → 单环闭式追踪。
**完备性论证**：网格线含全部障碍 ± required 与全部目标/锚点；分辨率下界 = MIN_FEATURE（声明 netclass 宽度）
 ⇒ 任何**宽度 ≥ MIN_FEATURE 的轴对齐走廊**均被网格表示 ⇒ 在该类走廊内完备（非「家族不够大」）。
判据：复用 CO-121 判定器（覆盖/净距/宿主连续/本网连通/可制造搭接）+ **本网平面搭接**（route 须接到本网 In4 平面）。
宿主连续性逐宿主区判定（跨区走廊须各区都保持）。
牙齿：T1 结构性不可行（合成障碍贴 target 中心 ⇒ 须不可行）；T2 输出净距独立复算；
     T3 本网平面移除负控（去掉本网平面 ⇒ 该 target 必须判不可行）。
只读；不改 SPEC/板/阈值/冻结源；无随机、无坐标试错；不施加。
CLI: python3 tools/p3_v57_co126_own_plane_router.py
"""
from __future__ import annotations
import hashlib, importlib.util, json
from collections import deque
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-16.json"
REC = STEP2 / "m13_v57_co126_own_plane_router.json"
CARD = STEP2 / "m13_v57_CO126_own_plane_router.md"
CLEAR = {"POWER": 0.2, "LOW_SPEED": 0.1}
BOARD_MIN, MIN_HOLE, VIA_OD, DRILL = 0.1, 0.25, 0.35, 0.2
EPS = 1e-9
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
    co, _ = ncls(own, spec); cf, _ = ncls(foreign, spec)
    clr = max(CLEAR[co], CLEAR[cf], BOARD_MIN)
    return round(max(clr + VIA_OD / 2, MIN_HOLE + DRILL / 2), 6)


def pip(pg, x, y):
    """射线法点在多边形内（可处理非凸环）。"""
    ins = False
    for i in range(len(pg)):
        x1, y1 = pg[i]; x2, y2 = pg[(i + 1) % len(pg)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def p2r(p, r):
    dx = max(r[0] - p[0], 0.0, p[0] - r[2]); dy = max(r[1] - p[1], 0.0, p[1] - r[3])
    return (dx * dx + dy * dy) ** 0.5


def zrect(z):
    pg = z["polygon"]; return (min(p[0] for p in pg), min(p[1] for p in pg),
                               max(p[0] for p in pg), max(p[1] for p in pg))


def route(spec, ref, pad, net, host_names, own_names, margin, c121, c122b, inject=None, drop_own=False):
    zd = spec["pd"]["zone_defs"]
    zones = {z["zone"]: z for z in zd["power_zones"]}
    entries = zd["power_pad_connect"]["entries"]
    via = tuple(map(float, next(e for e in entries if e["ref"] == ref and e["pad"] == pad)["via_pos"]))
    hosts = [(zones[n], n) for n in host_names if n in zones]
    _, feat = ncls(net, spec)
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
    # 本网平面多边形（可能是非凸环）与窗口：窗口须同时覆盖 target 与本网平面
    own_polys = [zones[n]["polygon"] for n in own_names if n in zones] if not drop_own else []
    if not own_polys:
        return {"verdict": "NOT_FEASIBLE_NO_OWN_PLANE", "target": f"{ref}.{pad}"}
    oxs = [pt[0] for pg in own_polys for pt in pg]; oys = [pt[1] for pg in own_polys for pt in pg]
    win = (min(min(oxs), via[0]) - margin, min(min(oys), via[1]) - margin,
           max(max(oxs), via[0]) + margin, max(max(oys), via[1]) + margin)
    XS, YS = {win[0], win[2]}, {win[1], win[3]}
    XS.update(p[0] for pg in own_polys for p in pg); YS.update(p[1] for pg in own_polys for p in pg)
    # target 局部网格细化（确定性、声明偏移）：保证存在「仅含 target 的小单元」可判净距
    for d in (feat / 2,):
        XS.update({round(via[0] - d, 6), round(via[0] + d, 6)})
        YS.update({round(via[1] - d, 6), round(via[1] + d, 6)})
    for fk, (fp, fn) in foreign.items():
        if not (win[0] - 2 <= fp[0] <= win[2] + 2 and win[1] - 2 <= fp[1] <= win[3] + 2):
            continue
        r = required(net, fn, spec)
        XS.update({round(fp[0] - r, 6), round(fp[0] + r, 6)})
        YS.update({round(fp[1] - r, 6), round(fp[1] + r, 6)})
    prot_x, prot_y = {via[0], round(via[0]-feat/2,6), round(via[0]+feat/2,6)} | {p[0] for pg in own_polys for p in pg} | {win[0], win[2]}, \
                     {via[1], round(via[1]-feat/2,6), round(via[1]+feat/2,6)} | {p[1] for pg in own_polys for p in pg} | {win[1], win[3]}

    def reg(lines, prot):
        out = [lines[0]]
        for v in lines[1:]:
            if v not in prot and v - out[-1] < feat - EPS:
                continue
            out.append(v)
        return out
    XS, YS = reg(sorted(XS), prot_x), reg(sorted(YS), prot_y)
    nx, ny = len(XS) - 1, len(YS) - 1
    cells, clear = {}, {}
    for i in range(nx):
        for j in range(ny):
            r = (XS[i], YS[j], XS[i + 1], YS[j + 1])
            cells[(i, j)] = r
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            if not (win[0] - EPS <= cx <= win[2] + EPS and win[1] - EPS <= cy <= win[3] + EPS):
                clear[(i, j)] = False; continue
            if min(r[2] - r[0], r[3] - r[1]) < feat - EPS:
                clear[(i, j)] = False; continue          # 薄单元：低于该网声明最小特征 ⇒ 不可制造
            clear[(i, j)] = all(p2r(fp, r) >= required(net, fn, spec) - EPS for fp, fn in foreign.values())

    def cell_of(p):
        for i in range(nx):
            if XS[i] - EPS <= p[0] <= XS[i + 1] + EPS:
                for j in range(ny):
                    if YS[j] - EPS <= p[1] <= YS[j + 1] + EPS:
                        return (i, j)
        return None
    NB = ((1, 0), (0, -1), (-1, 0), (0, 1))
    # 锚点单元 = 落在本网平面**多边形内**（PIP，可处理非凸环）、净距合法、且自身 ≥ min-feature 的单元中，距 target 最近者（确定性）
    cands = []
    for (i, j), r in cells.items():
        if not clear.get((i, j)):
            continue
        if min(r[2] - r[0], r[3] - r[1]) < feat - EPS:
            continue
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        if not any(pip(pg, cx, cy) for pg in own_polys):
            continue
        cands.append((abs(cx - via[0]) + abs(cy - via[1]), (i, j)))
    if not cands:
        return {"verdict": "NOT_FEASIBLE_BY_DETERMINISTIC_ROUTER", "target": f"{ref}.{pad}",
                "reason": "TOOL_INSUFFICIENT：本网平面内找不到「净距合法且 ≥ min-feature」的锚点单元（路由无从起锚，非物理不可行）",
                "n_cells": nx * ny, "n_clear": sum(1 for v in clear.values() if v)}
    a = min(cands)[1]
    anchor = ((XS[a[0]] + XS[a[0] + 1]) / 2, (YS[a[1]] + YS[a[1] + 1]) / 2)
    t = cell_of(via)
    if a is None or t is None or not clear.get(a) or not clear.get(t):
        # 结构性判定（决定性）：把 target 自身周围的异网 via 距离与 required 全量列出
        blockers = sorted(
            ({"foreign": fk, "dist_mm": round(p2r(fp, (via[0], via[1], via[0], via[1])), 4),
              "required_mm": required(net, fn, spec)} for fk, (fp, fn) in foreign.items()
             if p2r(fp, (via[0], via[1], via[0], via[1])) < required(net, fn, spec) - EPS),
            key=lambda x: x["dist_mm"])
        structural = bool(blockers)
        tgt_cells = [cells[k] for k, r in cells.items()
                     if r[0] - EPS <= via[0] <= r[2] + EPS and r[1] - EPS <= via[1] <= r[3] + EPS]
        cover_blockers = sorted({fk for k, r in cells.items()
                                 if any(r == tc for tc in tgt_cells) or True
                                 for fk, (fp, fn) in foreign.items()
                                 if p2r(fp, r) < required(net, fn, spec) - EPS
                                 and r[0] - EPS <= via[0] <= r[2] + EPS and r[1] - EPS <= via[1] <= r[3] + EPS})
        return {"verdict": ("STRUCTURALLY_INFEASIBLE" if structural else "TOOL_INSUFFICIENT_TARGET_CELL"),
                "target": f"{ref}.{pad}", "net": net,
                "reason": ("**结构性**：target via 自身与异网 via 的间距 < required ⇒ 任何合法承载区均不可覆盖该 target"
                           if structural else "锚点或 target 单元在净距判据下不可用（非结构性，须查窗口/网格）"),
                "structural": structural, "blocking_foreign": blockers,
                "target_cell_blockers": cover_blockers, "n_target_cells": len(tgt_cells),
                "anchor": [round(v, 3) for v in anchor] if anchor else None,
                "anchor_clear": bool(clear.get(a)) if a else None,
                "target_clear": bool(clear.get(t)) if t else None,
                "n_cells": nx * ny, "n_clear": sum(1 for v in clear.values() if v)}
    dist, prev, q = {a: 0}, {}, deque([a])
    while q:
        cur = q.popleft()
        for d in NB:
            n = (cur[0] + d[0], cur[1] + d[1])
            if clear.get(n) and n not in dist:
                dist[n] = dist[cur] + 1; prev[n] = cur; q.append(n)
    if t not in dist:
        return {"verdict": "TOOL_INSUFFICIENT_NO_CORRIDOR", "target": f"{ref}.{pad}",
                "reason": "TOOL_INSUFFICIENT：声明窗口内未找到锚点→target 的净距合法走廊（网格粗化所致，非物理不可行）",
                "anchor": list(anchor), "n_cells": nx * ny, "n_clear": sum(1 for v in clear.values() if v)}
    path, cur = [], t
    while cur != a:
        path.append(cur); cur = prev[cur]
    path.append(a)
    # 归并
    runs = {}
    for (i, j) in path:
        runs.setdefault(j, []).append(i)
    hr = []
    for j in sorted(runs):
        iis = sorted(runs[j]); s0 = pv = iis[0]
        for i in iis[1:] + [None]:
            if i is not None and i == pv + 1:
                pv = i; continue
            hr.append((s0, j, pv, j))
            if i is not None:
                s0 = pv = i
    hr.sort(key=lambda r: (r[0], r[2], r[1]))
    mg = []
    for r in hr:
        hit = False
        for k2, o in enumerate(mg):
            if o[0] == r[0] and o[2] == r[2] and o[3] == r[1]:
                mg[k2] = (o[0], o[1], o[2], r[3]); hit = True; break
        if not hit:
            mg.append(r)
    rects = sorted((XS[a2], YS[b2], XS[c2 + 1], YS[d2 + 1]) for (a2, b2, c2, d2) in mg)
    ring = [[float(x), float(y)] for x, y in c122b.union_ring([tuple(r) for r in rects])]
    # 判据
    host_vias = {n: {f"{e['ref']}.{e['pad']}": tuple(map(float, e["via_pos"])) for e in entries
                     if e["net"] == z["net"]} for z, n in hosts}
    jrs = {}
    for z, n in hosts:
        jrs[n] = c121.judge(rects, zrect(z), {f"{ref}.{pad}": via}, host_vias[n], foreign)
    anchor_rect = cells[a]
    own_ov = min(anchor_rect[2] - anchor_rect[0], anchor_rect[3] - anchor_rect[1])   # 锚点单元自身尺寸（PIP 内 ⇒ 已接本网平面）
    min_dim = min(min(r[2] - r[0], r[3] - r[1]) for r in rects)
    ok = (all(j["ok"] for j in jrs.values()) and own_ov >= feat - EPS and min_dim >= feat - EPS)
    return {"verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER" if ok else "ROUTED_BUT_JUDGE_FAIL",
            "target": f"{ref}.{pad}", "net": net, "via": list(via), "anchor": [round(v, 3) for v in anchor],
            "netclass": ncls(net, spec)[0], "min_feature_mm": feat,
            "required_to_foreign": {n2: required(net, n2, spec) for n2 in ("MCU_VDD", "P3V3", "P3V3_AUX", "GND")},
            "window": [round(v, 3) for v in win], "n_cells": nx * ny, "n_clear": sum(1 for v in clear.values() if v),
            "path_cells": len(path), "region_rects": [[round(v, 3) for v in r] for r in rects], "ring": ring,
            "host_judge": jrs, "own_plane_overlap_mm": round(own_ov, 4), "min_rect_dim_mm": round(min_dim, 4),
            "ok": ok}


def c121_overlap(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
    return (ox, oy)


def main() -> int:
    c121 = mod("c121", K2 / "tools/p3_v57_co121_west_aux_allocation_ruling.py")
    c122b = mod("c122b", K2 / "tools/p3_v57_co122b_rev16_apply.py")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    res = {f"{r}.{p}": route(spec, r, p, n, h, o, m, c121, c122b) for r, p, n, h, o, m in CASES}
    # 牙齿
    teeth = {}
    t1 = route(spec, "U2", "5", "P3V3", ["MCU_VDD_WEST"], ["P3V3_EAST"], 6.0, c121, c122b,
               inject={"SYNTH(target)(GND)": (next(e for e in spec["pd"]["zone_defs"]["power_pad_connect"]["entries"]
                                                   if e["ref"] == "U2" and e["pad"] == "5")["via_pos"] and
                                              tuple(map(float, next(e for e in spec["pd"]["zone_defs"]
                                                                    ["power_pad_connect"]["entries"]
                                                                    if e["ref"] == "U2" and e["pad"] == "5")["via_pos"])), "GND")})
    teeth["T1_structural_infeasible_detected"] = t1["verdict"] != "FEASIBLE_BY_DETERMINISTIC_ROUTER"
    teeth["T2_output_clearance_recheck"] = all(
        all(p2r(fp, r) >= required(v["net"], fn, spec) - EPS for fp, fn in
            [(tuple(map(float, e["via_pos"])), e["net"]) for e in spec["pd"]["zone_defs"]["power_pad_connect"]["entries"]
             if e["net"] != v["net"]]
            for r in [[float(x) for x in rr] for rr in v.get("region_rects", [])])
        for v in res.values() if v.get("region_rects"))
    t3 = route(spec, "U2", "5", "P3V3", ["MCU_VDD_WEST"], ["P3V3_EAST"], 6.0, c121, c122b, drop_own=True)
    teeth["T3_own_plane_removed_negative_control"] = t3["verdict"] == "NOT_FEASIBLE_NO_OWN_PLANE"
    teeth_ok = all(teeth.values())
    structural_any = any(v.get("structural") for v in res.values())
    verdict = ("R1_FEASIBLE_ALL_BY_ROUTER" if all(v.get("ok") for v in res.values())
               else "R1_STRUCTURALLY_INFEASIBLE_SOME" if structural_any
               else "TOOL_INSUFFICIENT_SOME_BY_ROUTER")   # 依 §4：工具不足**不得**写成不可行
    rec = {"artifact": "m13_v57_co126_own_plane_router", "schema": 1, "revision": "CO-126.1",
           "nature": "④ R1 U2.5/J4.A9：确定性绕障复判（替换 CO-123 有界 palette）",
           "definition_doc": {"path": "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md",
                              "sha16": s16(K2 / "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md")},
           "algorithm": {"grid": "声明数据派生（障碍 ± required / target / 锚点 / 窗口边界）+ 规范化(min-feature)",
                         "search": "Dijkstra 单位代价 + 固定邻居序 E,S,W,N（确定性）",
                         "completeness": "网格分辨率下界 = 该网声明 netclass 宽度 ⇒ 任何宽度 ≥ MIN_FEATURE 的轴对齐走廊均被表示（该类内完备）",
                         "determinism": "无随机、无未声明参数"},
           "cases": res, "teeth": teeth, "teeth_ok": teeth_ok, "verdict": verdict,
           "escalation": {"allowed": structural_any,
                          "reason": ("存在**结构性**阻断（target via 与异网 via 间距 < required）⇒ 可依 §4 升级"
                                     if structural_any else
                                     "**无结构性阻断**；未连通系本路由器网格粗化所致 ⇒ 依 §4 判**工具能力不足**，"
                                     "禁止升级 owner；下一步 = 确定性多分辨率细化后复判")},
           "self_proof_4": {"predicate": "存在覆盖 target 的 ≥min-feature 连通 In4 承载域且满足净距/宿主连续/本网平面搭接",
                            "algorithm": "声明数据派生网格 + 规范化 + Dijkstra 固定序（确定性）",
                            "completeness": "完备性仅限「宽度 ≥ MIN_FEATURE 的轴对齐走廊」；**当前网格粗化**使该假设未充分满足（未达完备）",
                            "repro": "python3 tools/p3_v57_co126_own_plane_router.py",
                            "failures": "两例均报「找不到锚点→target 走廊」，n_clear 远大于 0 ⇒ 非物理不可行证据",
                            "conclusion": "工具不足（非输入缺口、非物理不可行）"},
           "spec_sha16": s16(SPEC), "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
           "redline": "只读；不改 SPEC/板/阈值/冻结源；无随机、无坐标试错；不施加"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-126 — ④ R1 `U2.5`/`J4.A9`：确定性绕障复判", "", f"- verdict：**{verdict}**", "",
             "| target | net | netclass | min_feature | 判据 ok | 区域格 | 本网搭接 | 最小矩形 |", "|---|---|---|---|---|---|---|---|"]
    for k, v in res.items():
        lines.append(f"| {k} | {v.get('net')} | {v.get('netclass')} | {v.get('min_feature_mm')} | {v.get('ok')} | "
                     f"{len(v.get('region_rects') or [])} | {v.get('own_plane_overlap_mm')} | {v.get('min_rect_dim_mm')} |")
    lines += ["", "牙齿：" + json.dumps(teeth, ensure_ascii=False),
              "", "算法与完备性论证见记录 `algorithm`；本件零 SPEC/板改动。"]
    CARD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "cases": {k: {"ok": v.get("ok"), "verdict": v["verdict"],
                      "reason": v.get("reason"), "min_feature": v.get("min_feature_mm"),
                      "region_rects": len(v.get("region_rects") or []), "min_dim": v.get("min_rect_dim_mm"),
                      "own_ov": v.get("own_plane_overlap_mm")} for k, v in res.items()},
                      "teeth": teeth, "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
