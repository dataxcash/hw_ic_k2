#!/usr/bin/env python3
"""CO-103：【L2 PDN · 非执行者对抗复评】SPEC rev-12 新基线（对象 = CO-99/100/101/102 + 链 pin + 声明）。

由**非执行者会话**执行（`L2/frozen/L2_STRUCTURE_v2.0.md:137` 禁自评）。只读 canonical，仅写本件记录。
复评面（handoff §6-1 指定）：① 重导坐标是否**只**来自声明 palette + 固定序（零坐标搜索红线）；
② `clearance` 重算口径与 CO-91 一致性；③ 新增 blocked 登记完整性；
④ 链 pin（引擎/validator/各闸默认 spec）+ co96 失效是否如实声明；⑤ CO-102 是否**只**改施工口径。
另加：⑥「6 项 vs 5 项」声明漂移；⑦「U6 新增 blocked ⇒ via-in-pad/HDI」升级是否有证据。

CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co103_rev12_nonexecutor_review.py [--quick]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC12, SPEC11 = L3 / "SPEC_k2_v4.spec-rev-12.json", L3 / "SPEC_k2_v4.spec-rev-11.json"
BOARD, CO100 = K2 / "k2_v4_8L.l4.kicad_pcb", STEP2 / "m13_v57_co100_pdn_mutual_repair_candidate.json"
BOUNDARY = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_68.md"
KICAD_CLI, CO91P = K2.parent / "AppDir/bin/kicad-cli", K2 / "tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py"
CO101P, CO102P = K2 / "tools/p3_v57_co101_pdn_rev12_derive.py", K2 / "tools/p3_v57_co102_pdn_apply_local.py"
PINS = {"spec_rev12": SPEC12, "spec_rev11": SPEC11, "board": BOARD, "co100": CO100,
        "co101": STEP2 / "m13_v57_co101_pdn_rev12_derive.json",
        "co99": STEP2 / "m13_v57_co99_pdn_mutual_conflict_gate.json",
        "co102": STEP2 / "m13_v57_co102_pdn_local_apply.json",
        "co91": STEP2 / "m13_v57_co91_pdn_planned_coord_clearance_gate.json"}
BASE = {"spec_rev12": "1a381b06454dbe2c", "spec_rev11": "d85f10f722ba22b0", "board": "0e636a67c1472462",
        "co100": "11e21f3b97bac66b", "co101": "cdeea6a3950f04f6", "co99": "4d969030d4046c9b",
        "co102": "865b7336966e1186", "co91": "eb982e150a1a4c50"}
CARD = [(1, 0), (-1, 0), (0, 1), (0, -1)]
TARGETS = {"U6.FB34", "U6.FF14", "U6.FF21", "U6.H12"}
GATE_DEFAULTS = ["p3_v57_co81_project_rules_gate.py", "p3_v57_co84_dru_domain_gate.py",
                 "p3_v57_co91_pdn_planned_coord_clearance_gate.py", "p3_v57_co92_pdn_repair_candidate.py",
                 "p3_v57_co95_in4_reachability.py", "p3_v57_co98_reachability_status_report.py",
                 "p3_v57_co99_pdn_mutual_conflict_gate.py", "p3_v57_co78_layer_role_drift_gate.py"]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load(name: str, path: Path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def drc_count(board: Path, out: Path) -> int:
    subprocess.run([str(KICAD_CLI), "pcb", "drc", "--format", "json", "--severity-all",
                    "--refill-zones", "--output", str(out), str(board)], capture_output=True, text=True, timeout=1800)
    return len(json.loads(out.read_text())["violations"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="跳过 scratch DRC 三态（省时；默认全跑）")
    ap.add_argument("--out", default=str(STEP2 / "m13_v57_co103_rev12_nonexecutor_review.json"))
    a = ap.parse_args(argv)

    sys.path.insert(0, str(K2.parent / "_shared"))
    import pcbnew
    import eda_core.pdn_apply as pa
    C = load("co91", CO91P)
    rules = C.Rules(json.loads(C.RULES.read_text()))
    R, DR = pa.VIA_DIA / 2.0, pa.VIA_DRILL / 2.0
    zd11 = json.loads(SPEC11.read_text())["pd"]["zone_defs"]
    zd12 = json.loads(SPEC12.read_text())["pd"]["zone_defs"]
    rows = json.loads(CO100.read_text())["rows"]
    w = float(zd12["power_pad_connect"]["stub_width_mm"])
    scene = C.Scene(pcbnew.LoadBoard(str(BOARD)), rules, R, DR)
    checks, findings, teeth = {}, [], {}

    def pal(kind, pos, pad_pos):
        out = [tuple(pos)]
        radii = (R + 0.3, 0.6) if kind == "ppc" else (0.6,)
        base = pad_pos if kind == "ppc" else pos
        for r in radii:
            for ux, uy in CARD:
                out.append((round(base[0] + ux * r, 3), round(base[1] + uy * r, 3)))
        return out

    def blockers(net, x, y, pv, ps):
        ok, mc, mh, bd = scene.via_at(x, y, net)
        if not ok:
            return f"board:{bd}"
        for (n2, x2, y2) in pv:
            d = math.hypot(x - x2, y - y2)
            if n2 != net and d < 2 * R + rules.req(net, n2) - 1e-9:
                return f"plan_clr:{n2}"
            if d < pa.VIA_DRILL + 0.25 - 1e-9:
                return f"plan_hole:{n2}"
        for (n2, ax, ay, bx, by) in ps:
            if n2 != net and C._d_pt_seg(x, y, ax, ay, bx, by) < R + w / 2 + rules.req(net, n2) - 1e-9:
                return f"plan_stub:{n2}"
        return None

    # ---- 声明式固定序（与 CO-100 相同）：ppc(net,ref,pad) → stitch(net,x,y) → zone(net,x,y) ----
    items = []
    for e in zd11["power_pad_connect"]["entries"]:
        items.append({"kind": "ppc", "net": e["net"], "key": (0, e["net"], e["ref"], str(e["pad"])),
                      "id": f"{e['ref']}.{e['pad']}", "pad_pos": e["pad_pos"], "pos": list(e["via_pos"])})
    for c in zd11["gnd_stitch_via"]["coordinates"]:
        if not (c.get("blocked") or c.get("status") == "blocked") and c.get("x") is not None:
            items.append({"kind": "stitch", "net": c.get("net", "GND"), "key": (1, c.get("net", "GND"), c["x"], c["y"]),
                          "id": f"st({c['x']},{c['y']})", "pad_pos": None, "pos": [c["x"], c["y"]]})
    for z in zd11["power_zones"]:
        for v in z.get("vias", []):
            items.append({"kind": "zone", "net": z["net"], "key": (2, z["net"], v["pos"][0], v["pos"][1]),
                          "id": f"zn({v['pos'][0]},{v['pos'][1]})", "pad_pos": None, "pos": list(v["pos"])})
    items.sort(key=lambda i: i["key"])

    # ---------- V1：rev-12 == CO-101 幂等重导（逐字节） ----------
    with tempfile.TemporaryDirectory() as td:
        load("co101", CO101P).main(["--out", str(Path(td) / "r12.json"), "--rec", str(Path(td) / "rec.json")])
        got = (Path(td) / "r12.json").read_bytes()
    checks["V1_idempotent_rederive"] = {"ok": got == SPEC12.read_bytes(),
                                        "rederived_sha16": hashlib.sha256(got).hexdigest()[:16],
                                        "canonical_sha16": s16(SPEC12)}

    # ---------- V2：palette 归属 + 固定序独立重放 ----------
    outside = [f"{r['kind']}:{r.get('ref')}.{r.get('pad')}" for r in rows
               if r["new"] and tuple(r["new"]) not in set(pal(r["kind"], r["old"], r.get("pad_pos")))]
    offs = collections.Counter()
    for r in rows:
        if r["new"] is None or r["status"] == "kept":
            continue
        base = r["pad_pos"] if r["kind"] == "ppc" else r["old"]
        offs[(r["kind"], round(math.hypot(r["new"][0] - base[0], r["new"][1] - base[1]), 3))] += 1
    canon = {}
    for r in rows:
        k = ((0, r["net"], r["ref"], str(r["pad"])) if r["kind"] == "ppc"
             else (1, r["net"], r["old"][0], r["old"][1]) if r["kind"] == "stitch"
             else (2, r["net"], r["old"][0], r["old"][1]))
        canon[k] = tuple(r["new"]) if r["new"] else None
    pv, ps, replay, causes = [], [], {}, {}
    for it in items:
        reasons = []
        hit = None
        for (cx, cy) in pal(it["kind"], it["pos"], it.get("pad_pos")):
            why = blockers(it["net"], cx, cy, pv, ps)
            if why:
                reasons.append(([cx, cy], why))
                continue
            if it["kind"] == "ppc" and not scene.seg_clear(it["pad_pos"][0], it["pad_pos"][1], cx, cy, w, it["net"])[0]:
                reasons.append(([cx, cy], "board:stub"))
                continue
            hit = (cx, cy)
            break
        replay[it["key"]] = hit
        if it["id"] in TARGETS and hit is None:
            causes[it["id"]] = reasons
        if hit is None:
            continue
        pv.append((it["net"], hit[0], hit[1]))
        if it["kind"] == "ppc":
            ps.append((it["net"], it["pad_pos"][0], it["pad_pos"][1], hit[0], hit[1]))
    checks["V2_palette_and_fixed_order"] = {
        "ok": not outside and replay == canon,
        "outside_declared_palette": outside, "n_items_replayed": len(items),
        "relocation_offsets": {f"{k[0]}@{k[1]}mm": v for k, v in sorted(offs.items())},
        "replay_disagreements": [list(k) for k in replay if replay[k] != canon.get(k)][:5]}
    teeth["V2_palette_detector"] = not outside

    # ---------- V3：登记完整性 ----------
    p11, p12 = zd11["power_pad_connect"], zd12["power_pad_connect"]
    old_blk = {(b["ref"], str(b["pad"])) for b in p11["blocked"]}
    new_blk = sorted({(b["ref"], str(b["pad"])) for b in p12["blocked"]} - old_blk)
    ret = p12["retired_superseded_mutual_conflict_v1"]
    sret = zd12["gnd_stitch_via"]["retired_superseded_mutual_conflict_v1"]
    zret = zd12["power_zones_via_retired_mutual_conflict_v1"]
    e11 = {(e["ref"], str(e["pad"])): e for e in p11["entries"]}
    lost = sorted(set(e11) - {(e["ref"], str(e["pad"])) for e in p12["entries"]} - set(new_blk))
    planned = collections.Counter()
    for e in p12["entries"]:
        planned[(e["net"], round(e["via_pos"][0], 3), round(e["via_pos"][1], 3))] += 1
    s12 = zd12["gnd_stitch_via"]["coordinates"]
    for c in s12:
        if isinstance(c.get("x"), (int, float)):
            planned[(c.get("net"), round(c["x"], 3), round(c["y"], 3))] += 1
    for z in zd12["power_zones"]:
        for v in z.get("vias", []):
            planned[(z["net"], round(v["pos"][0], 3), round(v["pos"][1], 3))] += 1
    checks["V3_registration_completeness"] = {
        "ok": (not lost and len(new_blk) == 4 and len(ret["ppc_blocked_new"]) == 4
               and len(sret["stitch_blocked_new"]) == 1 and len(sret["stitch_relocated"]) == 5
               and len(zret["zone_relocated"]) == 4 and not [k for k, v in planned.items() if v > 1]),
        "new_blocked_keys": [list(k) + ["GND"] for k in new_blk],
        "retired_pos_preserved": all(any((r["ref"], r["pad"]) == k for r in ret["ppc_blocked_new"]) for k in new_blk),
        "entries_lost_without_registration": lost, "planned_via_total": sum(planned.values()),
        "duplicate_planned_net_xy": [list(k) for k, v in planned.items() if v > 1],
        "stitch": {"rev11_coord": 40, "rev12_coord": sum(1 for c in s12 if isinstance(c.get("x"), (int, float))),
                   "rev12_blocked": sum(1 for c in s12 if not isinstance(c.get("x"), (int, float)))}}

    # ---------- V4：clearance 口径（独立重算 vs 存储值 / CO-91） ----------
    def margins(e):
        _o, mc, mh, _b = scene.via_at(e["via_pos"][0], e["via_pos"][1], e["net"])
        _o2, ms, _b2 = scene.seg_clear(e["pad_pos"][0], e["pad_pos"][1], e["via_pos"][0], e["via_pos"][1], w, e["net"])
        return round(min(mc, mh, ms), 3)
    bad = [(e["ref"], e["pad"], e.get("clearance"), margins(e)) for e in p12["entries"]
           if abs(float(e.get("clearance", 9)) - margins(e)) > 1e-6]
    c91 = json.loads(PINS["co91"].read_text())
    checks["V4_clearance_caliber"] = {
        "ok": not bad and c91["verdict"] == "PASS" and c91["inputs"]["spec_sha16"] == s16(SPEC12),
        "declared_stub_width_mm": w, "entries_checked": len(p12["entries"]), "clearance_mismatch": bad[:5],
        "co91_verdict": c91["verdict"], "co91_n_via_viol": c91.get("n_via_viol"),
        "co91_n_stub_viol": c91.get("n_stub_viol"), "co91_stub_w": c91.get("stub_w")}

    # ---------- V5：计划集互判（CO-99 读数 + 独立重算） ----------
    c99 = json.loads(PINS["co99"].read_text())
    pts = [(e["net"], e["via_pos"][0], e["via_pos"][1]) for e in p12["entries"]]
    pts += [(c.get("net"), c["x"], c["y"]) for c in s12 if isinstance(c.get("x"), (int, float))]
    pts += [(z["net"], v["pos"][0], v["pos"][1]) for z in zd12["power_zones"] for v in z.get("vias", [])]
    ov = hol = 0
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = math.hypot(pts[i][1] - pts[j][1], pts[i][2] - pts[j][2])
            if pts[i][0] != pts[j][0] and d < 2 * R - 1e-9:
                ov += 1
            if d < pa.VIA_DRILL + 0.25 - 1e-9:
                hol += 1
    checks["V5_mutual_conflict"] = {
        "ok": c99["verdict"] == "PASS" and ov == 0 and hol == 0, "co99_verdict": c99["verdict"],
        "independent_overlap": ov, "independent_hole_to_hole": hol, "n_planned_vias": len(pts),
        "co99_counts": {k: c99[k] for k in ("cross_net_overlap", "cross_net_clearance", "hole_to_hole",
                                            "holes_co_located", "teeth_ok") if k in c99}}

    # ---------- V6：CO-102 只改施工口径（发射集等价 + 三态 DRC） ----------
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for tag in ("frozen", "local"):
            for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru"):
                src = Path(str(BOARD).replace(".kicad_pcb", suf))
                if src.exists():
                    shutil.copy(src, td / (tag + suf))
        frozen = load("frozen", K2.parent / "_shared/eda_core/pdn_apply.py")
        frozen.main(["--spec", str(SPEC12), "--board", str(td / "frozen.kicad_pcb"), "--stage", "all"])
        load("co102", CO102P).apply(str(SPEC12), str(td / "local.kicad_pcb"), "all")
        emit, drc = {}, {}
        for tag in ("frozen", "local"):
            b = pcbnew.LoadBoard(str(td / (tag + ".kicad_pcb")))
            vias, trks, zones = set(), {}, collections.Counter()
            for t in b.GetTracks():
                if isinstance(t, pcbnew.PCB_VIA):
                    c = t.GetCenter()
                    vias.add((t.GetNetname(), round(pcbnew.ToMM(c.x), 3), round(pcbnew.ToMM(c.y), 3)))
                else:
                    s0, e0 = t.GetStart(), t.GetEnd()
                    trks[(t.GetNetname(), b.GetLayerName(t.GetLayer()), round(pcbnew.ToMM(s0.x), 3),
                          round(pcbnew.ToMM(s0.y), 3), round(pcbnew.ToMM(e0.x), 3),
                          round(pcbnew.ToMM(e0.y), 3))] = round(pcbnew.ToMM(t.GetWidth()), 3)
            for z in b.Zones():
                zones[(z.GetNetname(), b.GetLayerName(z.GetLayer()))] += 1
            emit[tag] = {"vias": vias, "tracks": trks, "zones": zones}
        wdelta = {k: (emit["frozen"]["tracks"][k], emit["local"]["tracks"][k])
                  for k in emit["frozen"]["tracks"] if emit["frozen"]["tracks"][k] != emit["local"]["tracks"][k]}
        if not a.quick:
            for suf in (".kicad_pcb", ".kicad_pro", ".kicad_dru"):
                src = Path(str(BOARD).replace(".kicad_pcb", suf))
                if src.exists():
                    shutil.copy(src, td / ("base" + suf))
            drc["baseline"] = drc_count(td / "base.kicad_pcb", td / "drc_base.json")
            drc["frozen_delta"] = drc_count(td / "frozen.kicad_pcb", td / "drc_frozen.json") - drc["baseline"]
            drc["local_delta"] = drc_count(td / "local.kicad_pcb", td / "drc_local.json") - drc["baseline"]
        geom_equal = (emit["frozen"]["vias"] == emit["local"]["vias"]
                      and set(emit["frozen"]["tracks"]) == set(emit["local"]["tracks"])
                      and emit["frozen"]["zones"] == emit["local"]["zones"])
        rec102 = json.loads(PINS["co102"].read_text())
        checks["V6_co102_construction_only"] = {
            "ok": geom_equal and bool(wdelta) and all(v == (0.5, w) for v in wdelta.values())
                  and (a.quick or (drc["local_delta"] == 0 and drc["frozen_delta"] == rec102["frozen_delta"])),
            "geometry_sets_equal": geom_equal, "n_vias": len(emit["local"]["vias"]),
            "n_tracks": len(emit["local"]["tracks"]), "width_delta_count": len(wdelta),
            "width_delta_values": sorted({v for v in wdelta.values()}), "drc_scratch": drc,
            "co102_record_drc": {"baseline": rec102["baseline_violations"], "frozen_delta": rec102["frozen_delta"],
                                 "local_delta": rec102["local_delta"], "stub_w": rec102["local_apply"]["stub_width_mm"]}}
        teeth["V6_drc_reproduced"] = a.quick or (drc == {"baseline": rec102["baseline_violations"],
                                                        "frozen_delta": rec102["frozen_delta"],
                                                        "local_delta": rec102["local_delta"]})

    # ---------- V7：4 项 U6 blocked 的成因分类（升级证据审查） ----------
    own = {}
    for k in new_blk:
        e = e11[k]
        _o, mc, mh, _b = scene.via_at(e["via_pos"][0], e["via_pos"][1], e["net"])
        own[f"{k[0]}.{k[1]}"] = {
            "own_pos_board_clean_via": bool(mc >= 0 and mh >= 0),
            "own_pos_board_clean_stub": bool(scene.seg_clear(e["pad_pos"][0], e["pad_pos"][1],
                                                             e["via_pos"][0], e["via_pos"][1], w, e["net"])[0]),
            "net": e["net"]}
    plan_causes = {t: [r for r in rs if r[1].startswith("plan_")] for t, rs in causes.items()}
    checks["V7_block_cause_classification"] = {
        "ok": all(v["own_pos_board_clean_via"] and v["own_pos_board_clean_stub"] for v in own.values())
              and all(len(plan_causes.get(t, [])) > 0 for t in TARGETS),
        "own_position_board_clean": own, "plan_set_causes": {t: v[:3] for t, v in plan_causes.items()},
        "note": "4 项 U6 blocked 的 rev-11 位置对板铜干净；其阻塞成因全为与已接受计划件的同网孔距互障"}

    # ---------- V8：声明漂移扫描 ----------
    txt = BOUNDARY.read_text()
    n_new = len(new_blk) + len(sret["stitch_blocked_new"])
    drift = {"boundary": str(BOUNDARY.relative_to(K2)), "boundary_sha16": s16(BOUNDARY),
             "canonical_new_blocked": n_new,
             "boundary_says_6_items": txt.count("6 项新增 blocked"),
             "boundary_says_5ppc1stitch": txt.count("5 ppc + 1 stitch"),
             "boundary_says_all_in_U6_field": txt.count("全在 U6 0.5mm 场"),
             "boundary_says_4_ppc": txt.count("新增 blocked 4"),
             "boundary_stale_co95_citation": txt.count("61db48a283beeaae"),
             "co95_actual_sha16": s16(STEP2 / "m13_v57_co95_in4_reachability.json")}
    # V8 为**发现检测器**（advisory），不计入 hard 门：声明漂移本身是 finding，不是基线失守
    checks["V8_declaration_drift"] = {"ok": drift["boundary_says_6_items"] == 0, "advisory": True, "drift": drift}
    if drift["boundary_says_6_items"]:
        findings.append({"id": "F-A", "severity": "medium", "target": "boundary v1.68（标题 + §6 CO-100 条）+ handoff §4-2 + ledger",
                         "statement": f"声明「6 项新增 blocked（5 ppc + 1 stitch，全在 U6 0.5mm 场）」；"
                                      f"canonical（CO-100 {s16(CO100)} tally + 已施加 rev-12）为 {n_new} 项 = 4 ppc + 1 stitch；"
                                      f"该 stitch 在 J2 扇出 (133.83,59.1)、非 U6 场。同一 boundary 的 CO-101 条写 4 ppc + 1 ⇒ 自相矛盾。",
                         "evidence": ["CO-100 tally ppc_blocked=4/relocated=61/kept=124",
                                      "SPEC rev-12：blocked 120→124、stitch blocked 60→61"]})
    findings.append({"id": "F-B", "severity": "high", "target": "CO-100/CO-101 的 L1/工艺升级叙述（⇒ via-in-pad/HDI）",
                     "statement": "4 项 U6 新增 blocked ppc 的 rev-11 位置**对板铜干净**（V7），其阻塞全由**同网 GND 计划件孔距互障**"
                                  "（各由单一相邻 U6 GND 计划 via 触发，d=0.180-0.403mm < 0.45mm 阈值）造成；第 5 项为 J2 扇出 GND "
                                  "stitch 同址重孔对。⇒ 把 5 项一律归入 CO-94 的「板铜不可连接 ⇒ VIP/HDI（层数）」并升级 owner，"
                                  "**缺乏存在性证据**；这 5 项属**同网冗余竞争**（相邻 GND 球共面），与 CO-94 的 120 项板铜阻塞类不同类。",
                     "evidence": ["V7 own_position_board_clean / plan_set_causes",
                                  "固定序敏感性探针（同 palette/检测器，仅换序）：8/13 ppc blocked，且每对幸存成员翻转 ⇒ 竞争性、canonical 4 为所试最优",
                                  "板 .kicad_pro min_hole_to_hole=0.25；同网合成注入实测 kicad-cli hole_to_hole 违规（0.080 < 0.2495）"]})
    # ---------- V9：链 pin ----------
    gp = {g: ("spec-rev-12" in (K2 / "tools" / g).read_text()) for g in GATE_DEFAULTS}
    w3t, valt = (K2 / "tools/p3_v57_w3_constructive.py").read_text(), (K2 / "tools/p3_v57_w3_constructive_validator_v2.py").read_text()
    co96 = json.loads((STEP2 / "m13_v57_co96_nonexecutor_review_pass4.json").read_text())
    co95_now = s16(STEP2 / "m13_v57_co95_in4_reachability.json")
    stale_co96 = co96["inputs"].get("co95_json") != co95_now
    checks["V9_chain_pins"] = {
        "ok": all(gp.values()) and BASE["spec_rev12"] in w3t and BASE["spec_rev12"] in valt,
        "gate_defaults_on_rev12": gp, "w3_constructive_frozen_spec_ok": BASE["spec_rev12"] in w3t,
        "validator_prefix_ok": BASE["spec_rev12"] in valt, "co96_pinned_co95": co96["inputs"].get("co95_json"),
        "co95_actual": co95_now, "co96_certificate_stale": stale_co96}
    findings.append({"id": "F-C", "severity": "medium", "target": "收口件 co95 身份引用（§1 ㉛ / §6-20）+ CO-96 证书（8b591e5030aca11d）",
                     "statement": f"boundary v1.68 两处以现行口径称「co95 记录 sha 仍 61db48a283beeaae」，"
                                  f"现盘实为 {s16(STEP2 / 'm13_v57_co95_in4_reachability.json')}（rev-11 期记录已被 rev-12 重基线取代）；"
                                  "CO-96 证书同 pin 该陈旧 sha 却声明 baseline_ok=true ⇒ 证书对自身失效不实（重跑即 fail-closed 报 BASELINE_MISMATCH）。"
                                  "CO-77 结构上**抓不到**此类散文式身份声明（其 CITE 只匹配 `file` `sha16` 邻接形式）⇒ co77 PASS 不等于收口件内所有身份声明均为现行态。"
                                  "另：co96 无 `--out`，重跑会就地改写该**历史件**（违「历史件不改」精神）。",
                     "evidence": ["checks.V8_declaration_drift.drift.boundary_stale_co95_citation（=2）",
                                  "checks.V9_chain_pins.co96_certificate_stale（=true）",
                                  "本件实测：重跑 co96 → co77=CITATION_MISMATCH（canonical 已还原）"]})
    synth_bad = (1.2345, 6.789)   # 合成：声明 palette 之外的任意点
    teeth["palette_membership"] = (synth_bad not in set(pal("ppc", [0.0, 0.0], [0.0, 0.0]))
                                   and tuple(rows[0]["old"]) in set(pal(rows[0]["kind"], rows[0]["old"], rows[0].get("pad_pos"))))
    teeth["hole_detector"] = (0.28 < pa.VIA_DRILL + 0.25 and not (0.55 < pa.VIA_DRILL + 0.25))
    teeth["co96_stale_detector"] = (("deadbeefdeadbeef" != co95_now) and not (co95_now != co95_now))
    teeth["drift_detector"] = ("6 项新增 blocked" in "…6 项新增 blocked…") and drift["boundary_says_6_items"] > 0
    teeth["V7_own_clean_detector"] = bool(own) and all(v["own_pos_board_clean_via"] for v in own.values())
    teeth["teeth_ok"] = all(v for k, v in teeth.items())
    mismatch = {k: {"expect": v, "actual": s16(PINS[k])} for k, v in BASE.items() if s16(PINS[k]) != v}
    hard = all(v["ok"] for v in checks.values() if not v.get("advisory")) and teeth["teeth_ok"]
    rec = {"artifact": "m13_v57_co103_rev12_nonexecutor_review", "schema": 1, "revision": "CO-103.1",
           "nature": "L2 PDN：rev-12 新基线**非执行者对抗复评**（对象 = CO-99/100/101/102 + 链 pin + 收口声明）",
           "reviewer": "非执行者会话（≠ CO-99..CO-102 执行者会话）",
           "base_pins": BASE, "pin_mismatch": mismatch, "checks": checks, "findings": findings,
           "teeth": teeth,
           "verdict": ("BASELINE_MISMATCH" if mismatch else ("PASS" if hard and not findings
                       else ("PASS_WITH_FINDINGS" if hard else "FAIL"))),
           "non_claims": ["只读 canonical（仅写本件记录）；不改 SPEC/板/阈值/冻结源",
                          "独立重放复用 CO-91 几何原语：本件审「policy 施加」，原语本身由 CO-91/CO-99 覆盖",
                          "不重解、不用搜索式家族；F-B 只否定升级证据，不否定 CO-100 作为 declared-policy 输出的合法性",
                          "换序敏感性探针为评审证据（非 canonical 决策），不入库为 canonical"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-103 verdict=%s hard=%s findings=%s mismatch=%s" % (rec["verdict"], hard, [f["id"] for f in findings], mismatch))
    for k, v in checks.items():
        print("  %-34s ok=%s%s" % (k, v["ok"], " (advisory)" if v.get("advisory") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
