#!/usr/bin/env python3
"""CO-132：【L2 自裁 · L3 确定性派生 + 施加】R1 In4 承载几何（3 桥区 + 12V_IN）→ SPEC **rev-18**。

背景：rev-17 已退役三 zone 的 B.Cu 载体声明并证 R1 可行（CO-122/CO-127/CO-128），但桥区 `polygons` 仍空
（`geometry_status=L3_CONSTRUCTION_DERIVED`）⇒ co98 `declared_pending_l3=4`（U2.5/U4.3/C84.1/J4.A9）
+ 12V_IN 3 pad（`no_in4_region_for_net`）。本件按各 zone 的 `derivation` 要求做**确定性派生**并声明。

模型（同 CO-127，已证）：中线厚度 —— 中线路径点到异网 via 圆心 ≥ `required + (feat/2)·√2`
⇒ 铜区 = 路径格 ⊕ L∞(feat/2)：净距可证 ≥ required、宽度 ≥ feat。网格 = 声明切线 + 无 min-feature 格宽门限；
搜索 = Dijkstra 固定邻居序（确定性）。**多 target 星形**：anchor 取「清晰且落本网平面内」的格中
Σtarget-距离最小者（并列取格序最小），区域 = anchor→各 target 最短路径并集（确定性且连通）。
无本网平面者（12V_IN）：root = 字典序最小 target，区域 = root→其余 target 路径并集（同 CO-128）。
MCU_VDD_BCU_RESISTORS_IN4：R29/R31-R34 已由 MCU_VDD_WEST 覆盖（CO-131 34/34）⇒ 声明 covered_by_host，不新增几何。
判据：覆盖 / 净距复算 / min-dim ≥ feat / 矩形连通 / 本网平面搭接 / 逐宿主区（限定域）CO-121 判定。
只读 SPEC/板/阈值/冻结源（只写 rev-18 新文件）；零坐标搜索、无随机。
CLI: python3 tools/p3_v57_co132_r1_in4_carrier_derive.py
"""
from __future__ import annotations
import hashlib, importlib.util, json, math
from collections import deque
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SRC = L3 / "SPEC_k2_v4.spec-rev-17.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-18.json"
REC = STEP2 / "m13_v57_co132_r1_in4_carrier_derive.json"
CARD = STEP2 / "m13_v57_CO132_r1_in4_carrier_derive.md"
EPS = 1e-9
MERGE_MIN = 0.3
CASES = [  # (zone, net, targets(pad keys), own plane zones, host zones, margin)
    ("P3V3_BCU_BRIDGE_IN4", "P3V3", ["U2.5", "U4.3", "C84.1"], ["P3V3_EAST"], ["MCU_VDD_WEST", "P3V3_EAST"], 2.0),
    ("P3V3_AUX_BCU_BRIDGE_IN4", "P3V3_AUX", ["J4.A9"], ["P3V3_AUX_WEST"], ["P3V3_EAST", "MCU_VDD_WEST"], 2.0),
    ("12V_IN_IN4_CARRIER", "12V_IN", ["C88.1", "U2.4", "U2.6"], [], ["MCU_VDD_WEST"], 3.0),
]


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def mod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def ncls_eff(spec, c127, net):
    """netclass 归属（含 SPEC `net_classes_override`；D-6：12V_IN→POWER）。"""
    ov = spec.get("net_classes_override") or {}
    if isinstance(ov, dict) and net in ov:
        cls = ov[net]
        return cls, float((spec.get("net_classes") or {}).get(cls, {}).get("width", 0.15))
    if isinstance(ov, list) and net in ov:
        return "POWER", float((spec.get("net_classes") or {}).get("POWER", {}).get("width", 0.5))
    return c127.ncls(net, spec)


def required_eff(spec, c127, own, foreign):
    """铜边→异网 via 圆心最小距离（own 侧含 override）。"""
    co, _ = ncls_eff(spec, c127, own); cf, _ = ncls_eff(spec, c127, foreign)
    clr = max({"POWER": 0.2, "LOW_SPEED": 0.1}[co], {"POWER": 0.2, "LOW_SPEED": 0.1}[cf], 0.1)
    return round(max(clr + 0.35 / 2, 0.25 + 0.2 / 2), 6)


def derive(spec, c127, c121, c122b, net, target_keys, own_names, host_names, margin):
    zd = spec["pd"]["zone_defs"]; zones = {z["zone"]: z for z in zd["power_zones"]}
    entries = zd["power_pad_connect"]["entries"]
    by_key = {f"{e['ref']}.{e['pad']}": tuple(map(float, e["via_pos"])) for e in entries}
    targets = {k: by_key[k] for k in target_keys}
    cls, feat = ncls_eff(spec, c127, net)
    anchor_r = feat / 2 * math.sqrt(2)
    own_polys = [zones[n]["polygon"] for n in own_names if n in zones]
    foreign = {}
    for e in entries:
        if e["net"] != net:
            foreign[f"{e['ref']}.{e['pad']}({e['net']})"] = (tuple(map(float, e["via_pos"])), e["net"])
    for z in zd["power_zones"]:
        for i, v in enumerate(z.get("vias") or []):
            if z["net"] != net:
                foreign[f"{z['zone']}#v{i}({z['net']})"] = (tuple(map(float, v["pos"])), z["net"])
    R = {k: required_eff(spec, c127, net, fn) + anchor_r for k, (fp, fn) in foreign.items()}
    xs = [p[0] for p in targets.values()] + [p[0] for pg in own_polys for p in pg]
    ys = [p[1] for p in targets.values()] + [p[1] for pg in own_polys for p in pg]
    win = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
    XS = {win[0], win[2]} | {p[0] for p in targets.values()} | {p[0] for pg in own_polys for p in pg}
    YS = {win[1], win[3]} | {p[1] for p in targets.values()} | {p[1] for pg in own_polys for p in pg}
    for k, (fp, fn) in foreign.items():
        if win[0] - 2 <= fp[0] <= win[2] + 2 and win[1] - 2 <= fp[1] <= win[3] + 2:
            XS |= {round(fp[0] - R[k], 6), round(fp[0] + R[k], 6)}
            YS |= {round(fp[1] - R[k], 6), round(fp[1] + R[k], 6)}
    floor = feat / 2
    for level in range(0, 9):
        X, Y = sorted(XS), sorted(YS); nx, ny = len(X) - 1, len(Y) - 1
        clear = {}
        for i in range(nx):
            for j in range(ny):
                r = (X[i], Y[j], X[i + 1], Y[j + 1])
                clear[(i, j)] = (win[0] - EPS <= r[0] and r[2] <= win[2] + EPS
                                 and win[1] - EPS <= r[1] and r[3] <= win[3] + EPS
                                 and all(c127.p2r(fp, r) >= R[k] - EPS for k, (fp, fn) in foreign.items()))

        def cell_of(p):
            for i in range(nx):
                if X[i] - EPS <= p[0] <= X[i + 1] + EPS:
                    for j in range(ny):
                        if Y[j] - EPS <= p[1] <= Y[j + 1] + EPS:
                            return (i, j)
            return None
        tc = {k: cell_of(p) for k, p in targets.items()}
        bad = [k for k in tc if tc[k] is None or not clear.get(tc[k])]
        if bad:
            blockers = sorted(({"target": k, "foreign": fk,
                                "dist_mm": round(c127.p2r(fp, (*targets[k], *targets[k])), 4),
                                "required_mm": round(required_eff(spec, c127, net, fn), 4)}
                               for k in bad for fk, (fp, fn) in foreign.items()
                               if c127.p2r(fp, (*targets[k], *targets[k])) < required_eff(spec, c127, net, fn) - EPS),
                              key=lambda x: x["dist_mm"])
            return {"verdict": "STRUCTURALLY_INFEASIBLE" if blockers else "TOOL_INSUFFICIENT_TARGET_CELL",
                    "net": net, "structural": bool(blockers), "blocking_foreign": blockers,
                    "cleared_at_level": level, "n_cells": nx * ny,
                    "reason": ("target via 与异网 via 间距 < required ⇒ 任何合法铜区不可覆盖" if blockers else
                               "含 target 之格在净距判据下不可用（无结构性阻断）")}
        anchors = []
        if own_polys:
            anchors = [(i, j) for (i, j), ok in clear.items() if ok
                       and any(c127.pip(pg, (X[i] + X[i + 1]) / 2, (Y[j] + Y[j + 1]) / 2) for pg in own_polys)]
        dists = {}
        for k, c in tc.items():
            dd = {c: 0}; q = deque([c])
            while q:
                cur = q.popleft()
                for d in ((1, 0), (0, -1), (-1, 0), (0, 1)):
                    n = (cur[0] + d[0], cur[1] + d[1])
                    if clear.get(n) and n not in dd:
                        dd[n] = dd[cur] + 1; q.append(n)
            dists[k] = dd
        if own_polys:
            if not anchors:
                return {"verdict": "TOOL_INSUFFICIENT_NO_ANCHOR", "net": net, "cleared_at_level": level,
                        "reason": "本网平面内无可起锚清晰格"}
            cand = [a for a in anchors if all(a in dists[k] for k in tc)]
            if not cand:
                return {"verdict": "TOOL_INSUFFICIENT_NO_CORRIDOR", "net": net, "cleared_at_level": level,
                        "reason": "无单锚可同时连通全部 target（星形不成立）"}
            root = min(cand, key=lambda a: (sum(dists[k][a] for k in tc), a))
        else:
            root = tc[min(tc, key=lambda k: (targets[k][0], targets[k][1]))]
        dd = {root: 0}; prev = {}; q = deque([root])
        while q:
            cur = q.popleft()
            for d in ((1, 0), (0, -1), (-1, 0), (0, 1)):
                n = (cur[0] + d[0], cur[1] + d[1])
                if clear.get(n) and n not in dd:
                    dd[n] = dd[cur] + 1; prev[n] = cur; q.append(n)
        if not all(tc[k] in dd for k in tc):
            XS, YS = c127._bisect(XS, floor), c127._bisect(YS, floor)
            continue
        cells = set()
        for k in tc:
            cur = tc[k]
            while cur != root:
                cells.add(cur); cur = prev[cur]
            cells.add(root)
        rects = c127.merge2d([(X[i] - feat / 2, Y[j] - feat / 2, X[i + 1] + feat / 2, Y[j + 1] + feat / 2)
                              for (i, j) in cells])
        ring = [[float(x), float(y)] for x, y in c122b.union_ring([tuple(r) for r in rects])]
        jrs = {}
        for hn in host_names:
            z = zones[hn]; zr = c127.zrect(z)
            tgt_in = {k: p for k, p in targets.items() if c127.in_rect(p, zr)}
            mcu_in = {f"{e['ref']}.{e['pad']}": tuple(map(float, e["via_pos"])) for e in entries
                      if e["net"] == z["net"] and c127.in_rect(tuple(map(float, e["via_pos"])), zr)}
            probe = tgt_in or ({"__zone_probe__": c127.region_probe(rects, zr)} if c127.region_probe(rects, zr) else {})
            if not mcu_in and not probe:
                jrs[hn] = {"ok": True, "skipped": "区域与本区无交且区内无宿主网 via"}; continue
            jr = c121.judge(rects, zr, probe, mcu_in, foreign)
            jr["scoped_targets"] = sorted(probe); jr["scoped_host_vias"] = len(mcu_in)
            jrs[hn] = jr
        min_dim = min(min(r[2] - r[0], r[3] - r[1]) for r in rects)
        cov = all(any(c127.in_rect(p, r) for r in rects) for p in targets.values())
        clr = all(c127.p2r(fp, r) >= required_eff(spec, c127, net, fn) - EPS
                  for r in rects for k, (fp, fn) in foreign.items())
        attach = True
        if own_polys:
            a_rect = (X[root[0]] - feat / 2, Y[root[1]] - feat / 2, X[root[0] + 1] + feat / 2, Y[root[1] + 1] + feat / 2)
            attach = min(c127.rect_poly_area(a_rect, pg) for pg in own_polys) >= feat * MERGE_MIN - EPS
        ok = (cov and clr and min_dim >= feat - EPS and c127.rects_connected(rects) and attach
              and all(j.get("ok") for j in jrs.values()))
        return {"verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER" if ok else "ROUTED_BUT_JUDGE_FAIL",
                "net": net, "netclass": cls, "min_feature_mm": feat, "cleared_at_level": level,
                "window": [round(v, 3) for v in win], "n_cells": nx * ny,
                "n_clear": sum(1 for v in clear.values() if v), "path_cells": len(cells),
                "anchor_cell": list(root),
                "anchor": [round((X[root[0]] + X[root[0] + 1]) / 2, 3), round((Y[root[1]] + Y[root[1] + 1]) / 2, 3)],
                "region_rects": [[round(v, 3) for v in r] for r in rects], "ring": ring,
                "min_rect_dim_mm": round(min_dim, 4), "coverage": cov, "clearance_recheck_ok": clr,
                "own_plane_attach_ok": attach, "host_judge": jrs, "ok": ok}
    return {"verdict": "TOOL_INSUFFICIENT_NO_CORRIDOR", "net": net, "cleared_at_level": 8}


def flat(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f"{p}[{i}]")
    else:
        yield p, o


def main() -> int:
    c127 = mod("c127", K2 / "tools/p3_v57_co127_multires_router.py")
    c121 = mod("c121", K2 / "tools/p3_v57_co121_west_aux_allocation_ruling.py")
    c122b = mod("c122b", K2 / "tools/p3_v57_co122b_rev16_apply.py")
    src = json.loads(SRC.read_text(encoding="utf-8"))
    derivations = {zone: derive(src, c127, c121, c122b, net, tks, own, hosts, m)
                   for zone, net, tks, own, hosts, m in CASES}
    all_ok = all(d.get("ok") for d in derivations.values())
    out = json.loads(json.dumps(src))
    zd = out["pd"]["zone_defs"]
    byname = {z["zone"]: z for z in zd["power_zones"]}
    for zone, net, tks, own, hosts, m in CASES:
        d = derivations[zone]
        if not d.get("ok"):
            continue
        if zone == "12V_IN_IN4_CARRIER":
            zd["power_zones"].append({
                "net": "12V_IN", "zone": zone, "layer": "In4.Cu", "polygon": d["ring"], "vias": [],
                "fill_priority": 1,
                "declared_rects": d["region_rects"],
                "basis": "CO-132【L2 自裁】12V_IN In4 承载（CO-128 D-6 后按 POWER/feat 0.5 确定性绕障；环 = 声明矩形闭式并集）",
                "refs": ["CO-124", "CO-128", "CO-132"]})
        else:
            z = byname[zone]
            z["polygon"] = d["ring"]; z["declared_rects"] = d["region_rects"]
            z["fill_priority"] = 1          # 与同网宿主平面多边形重叠 ⇒ 需不同填充优先级（施工侧 add_zone 消费）
            z["geometry_status"] = "L3_DERIVED_DECLARED"
            z["r1_carrier_derive_v1"] = {
                "co": "CO-132", "model": "CO-127 中线厚度 + 多分辨率（确定性绕障）",
                "netclass": d["netclass"], "min_feature_mm": d["min_feature_mm"],
                "min_rect_dim_mm": d["min_rect_dim_mm"], "n_rects": len(d["region_rects"]),
                "coverage": d["coverage"], "clearance_recheck_ok": d["clearance_recheck_ok"],
                "own_plane_attach_ok": d["own_plane_attach_ok"],
                "host_ok": {k: v.get("ok") for k, v in (d.get("host_judge") or {}).items()},
                "note": "实体多边形 = 施工确定性派生（贯通孔反焊盘净距 + 异网净距 moat）；本件只声明几何与归属"}
    zr = byname["MCU_VDD_BCU_RESISTORS_IN4"]
    zr["geometry_status"] = "COVERED_BY_HOST_PLANE"
    zr["r1_carrier_derive_v1"] = {
        "co": "CO-132", "decision": "covered_by_host_plane",
        "basis": "R29/R31-R34 已由 MCU_VDD_WEST 覆盖（CO-131 机判 34/34 声明位置在内、距边 ≥0.2）⇒ 无需新增本区几何",
        "evidence": "m13_v57_co131_mcu_vdd_resistor_coverage.json 4b8213942dc20872"}
    prs = out["pd"]["zone_defs"]["plane_reachability_status"]
    prs["unresolved"] = [u for u in prs["unresolved"] if u["net"] != "12V_IN"]
    prs["resolved_by_co132"] = [
        {"net": "P3V3", "pads": ["U2.5", "U4.3", "C84.1"],
         "how": "P3V3_BCU_BRIDGE_IN4 In4 承载 = CO-132 确定性派生（多 target 星形，anchor 于 P3V3_EAST）"},
        {"net": "P3V3_AUX", "pads": ["J4.A9"],
         "how": "P3V3_AUX_BCU_BRIDGE_IN4 In4 承载 = CO-132 确定性派生（锚于 P3V3_AUX_WEST；CO-127 同模型）"},
        {"net": "12V_IN", "pads": ["C88.1", "U2.4", "U2.6"],
         "how": "12V_IN_IN4_CARRIER = CO-132 确定性派生（CO-128 D-6 POWER 口径；root = 字典序最小 target）"},
    ]
    zd["r1_in4_carrier_derive_v1"] = {
        "note": "CO-132【L2 自裁 · L3 确定性派生 + 施加 rev-18】：R1 In4 承载几何（3 桥区 + 12V_IN）",
        "level_basis": "《宪法》ch.2：PDN 架构/走廊分配/过孔策略 = L2；不改网名/域集合/层数 ⇒ 无 L1 面",
        "model_ref": "CO-127（中线厚度 + 多分辨率细化，确定性绕障）；CO-128（D-6 POWER 口径）",
        "board_expectation": "仅声明键变更，不改任何板坐标 ⇒ L4 板期望逐字节不变",
        "refs": ["CO-95", "CO-98", "CO-122", "CO-127", "CO-128", "CO-131"],
    }
    out["stackup"]["In4.Cu"] = "POWER_PLANE (P3V3 east / MCU_VDD west / P3V3_AUX island / 12V_IN carrier)"
    out["spec_version"] = "1.1.spec-rev-18"
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    a, b = dict(flat(src)), dict(flat(out))
    changed = sorted({k for k in set(a) | set(b) if a.get(k) != b.get(k)})
    allowed_pref = (".spec_version", ".stackup.In4.Cu", ".pd.zone_defs.r1_in4_carrier_derive_v1.",
                    ".pd.zone_defs.plane_reachability_status.unresolved",
                    ".pd.zone_defs.plane_reachability_status.resolved_by_co132")
    zone_pref = tuple(f".pd.zone_defs.power_zones[{i}]" for i in range(len(zd["power_zones"])))
    unexpected = [k for k in changed if not k.startswith(allowed_pref)
                  and not any(k.startswith(p) for p in zone_pref)]
    rec = {"artifact": "m13_v57_co132_r1_in4_carrier_derive", "schema": 1, "revision": "CO-132.1",
           "nature": "L2 自裁 · L3 确定性派生 + 施加：R1 In4 承载几何（3 桥区 + 12V_IN）→ SPEC rev-18",
           "src": SRC.name, "src_sha16": s16(SRC), "out": OUT.name, "out_sha16": s16(OUT),
           "derivations": derivations, "all_ok": all_ok,
           "changed_paths": len(changed), "unexpected_changed_paths": unexpected, "whitelist_ok": not unexpected,
           "board_untouched": True, "board_sha16_l4": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
           "redline": "不改板/阈值/冻结源；历史 SPEC 不改（新文件 bump）；零坐标搜索、无随机"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    CARD.write_text("\n".join([
        "# CO-132 — R1 In4 承载几何派生 + 施加 rev-18（L2 自裁）", "",
        f"- out：`{OUT.name}` `{rec['out_sha16']}`；src `{SRC.name}` `{rec['src_sha16']}`",
        f"- whitelist_ok={rec['whitelist_ok']}（changed_paths {len(changed)}，unexpected {len(unexpected)}）", "",
        "| zone | net | 区域矩形 | verdict | 级 | min-dim | 覆盖 | 净距复算 | 本网搭接 | 宿主 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ] + [f"| {z} | {d.get('net')} | {len(d.get('region_rects') or [])} | {d['verdict']} | {d.get('cleared_at_level')} | "
         f"{d.get('min_rect_dim_mm')} | {d.get('coverage')} | {d.get('clearance_recheck_ok')} | "
         f"{d.get('own_plane_attach_ok')} | { {k: v.get('ok') for k, v in (d.get('host_judge') or {}).items()} } |"
         for z, d in derivations.items()]
        + ["", "模型/白名单见记录；期望 L4 板逐字节不变。"]), encoding="utf-8")
    print(json.dumps({"out_sha16": rec["out_sha16"], "all_ok": all_ok,
                      "cases": {z: {"verdict": d["verdict"], "rects": len(d.get("region_rects") or []),
                                    "ring": len(d.get("ring") or []), "min_dim": d.get("min_rect_dim_mm")}
                                for z, d in derivations.items()},
                      "n_changed": len(changed), "unexpected": unexpected[:6], "whitelist_ok": rec["whitelist_ok"],
                      "rec_sha16": s16(REC)}, ensure_ascii=False, indent=1))
    return 0 if (all_ok and rec["whitelist_ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
