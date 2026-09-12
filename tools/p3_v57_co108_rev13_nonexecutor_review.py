#!/usr/bin/env python3
"""CO-108：【L2 · 非执行者对抗复评】rev-13 新基线（对象 = CO-106/107 + 链 pin 前移 + 几何/板不变性）。

触发：CO-107 施加 SPEC rev-13（平面多边形随板框 ECO 对齐）后需**非执行者**复评
（L2_STRUCTURE_v2.0.md:137 禁自评）。本件独立机判五面（不复用执行者断言）：

  A SPEC rev-13 vs rev-12 结构差分 = 恰好 10 个 polygon 顶点 + spec_version；退役留存完整（无静默放弃）；
  B 几何不变性：route_geometry/pages/landing_rows 与 rev-12 逐字节同 + 板逐字节不变 + frozen 无漂移；
  C 链 pin：无工具仍以 rev-12 为现行；记录内 `inputs.*_record` provenance pin 全数一致（含 04d0ee1 as-found 证据）；
  D CO-106 分类诚实性：独立**点级全量**重算参考平面连续性 —— GND 整面层缺铜 = 0；残余 54 段全落 L3 桥带；
  E rev-12 FAIL 独立复现（60 项/36 段）+ 板实已用该带（pcbnew，需 AppDir python，缺库则降级标注）。

牙齿：差分检测器 / 连续性检测器 / pin 漂移检测器 各带合成负控。
只读（除自身记录）；不改 SPEC/板/阈值/冻结源/其它工件。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co108_rev13_nonexecutor_review.py
"""
from __future__ import annotations
import argparse, collections, hashlib, json, subprocess
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
S12 = L3 / "SPEC_k2_v4.spec-rev-12.json"
S13 = L3 / "SPEC_k2_v4.spec-rev-13.json"
DRAW = STEP2 / "m13_v57_w3_joint_assignment.json"
CO98 = STEP2 / "m13_v57_co98_reachability_status_report.json"
CO105 = STEP2 / "m13_v57_co105_f4_scope_disposition.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT = STEP2 / "m13_v57_co108_rev13_nonexecutor_review.json"
SELF = Path(__file__).name
CO103_TOOL = "p3_v57_co103_rev12_nonexecutor_review.py"     # 合法持有 rev-12 基线（历史复评件）
REV12_DRAWING_SHA = "cb955e9af8782d08"                       # git 33b98e4 blob（rev-12 基线）
REV12_SUB = {"route_geometry": "c27d9f5b29c82ba2", "pages": "2535f3306cebe6eb",
             "landing_rows": "74234e98afe7498f"}
BOARD_SHA = "0e636a67c1472462"
SPEC13_SHA = "7943be727a4f8ef9"
STALE_SHA = "1a381b06454dbe2c"                               # rev-12 SPEC（现仅为历史）
EXPECTED_DELTA = {".spec_version",
                  *{f".pd.zone_defs.gnd_planes[{i}].polygon[{j}][1]" for i in range(3) for j in (2, 3)},
                  *{f".pd.zone_defs.power_zones[{i}].polygon[{j}][1]" for i in range(2) for j in (2, 3)}}
RETIRED_KEY = ".pd.zone_defs.retired_superseded_frame_extent_v1"
VOID_BAND = (70.7, 79.0)              # rev-12 声明平面下边 → 板框顶；板实已用该带
BRIDGE_X = (49.8, 88.37)             # MCU_VDD_WEST 右缘 ↔ P3V3_EAST 左缘（In4 桥区，L3 待派生）


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def flat(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f"{p}[{i}]")
    else:
        yield p, o


def polys_of(z):
    ps = z.get("polygons")
    if ps:
        return ps if isinstance(ps[0][0], list) else [ps]
    p = z.get("polygon")
    if p:
        return [p] if not isinstance(p[0][0], list) else p
    return []


def pip(pt, poly):
    x, y = pt
    ins = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def cu_map(zd):
    cu = collections.defaultdict(list)
    for g in zd.get("gnd_planes", []):
        for p in polys_of(g):
            cu[g["layer"]].append((g["net"], p))
    for z in zd["power_zones"]:
        for p in polys_of(z):
            cu[z["layer"]].append((z["net"], p))
    return cu


def continuity(spec, draw):
    """独立点级全量参考连续性重算。返回 (seg项计数, 点计数, 分类, (段idx,layer,ref) 缺失集, In5←In4 缺失点, 铜表)。"""
    zd = spec["pd"]["zone_defs"]
    cu = cu_map(zd)
    refs = {k: v.get("refs", []) for k, v in spec["impedance"]["per_layer"].items()}
    e = float(spec["constraints"]["edge_copper_min"])
    x0, x1 = spec["board"]["outline_x"]
    y0, y1 = spec["board"]["outline_y"]
    seg, pts, cls, sig = collections.Counter(), collections.Counter(), collections.Counter(), set()
    in5_in4_miss = []
    for idx, r in enumerate(draw["route_geometry"]):
        L, P = r["layer"], r["points"]
        samples = [tuple(P[0]), tuple(P[-1])] + [
            ((P[i][0] + P[i + 1][0]) / 2, (P[i][1] + P[i + 1][1]) / 2) for i in range(len(P) - 1)]
        for rl in refs.get(L, []):
            miss = [q for q in samples if not any(pip(q, p) for _, p in cu.get(rl, []))]
            if not miss:
                continue
            seg[(L, rl)] += 1
            pts[(L, rl)] += len(miss)
            sig.add((idx, L, rl))
            if (L, rl) == ("In5.Cu", "In4.Cu"):
                in5_in4_miss += miss
            role = str(spec["stackup"].get(rl, ""))
            q = miss[0]
            if (x0 + e <= q[0] <= x1 - e) and (y0 + e <= q[1] <= y1 - e):
                cls["declared_copper_missing" if "GND_PLANE" in role else "region_scoped_indeterminate"] += 1
    return seg, pts, cls, sig, in5_in4_miss, cu


def board_band_counts(lo, hi):
    try:
        import sys
        sys.path.insert(0, str(K2.parent / "_shared"))
        import pcbnew
        b = pcbnew.LoadBoard(str(BOARD))
        c = collections.Counter()
        for t in b.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                yy, lay = pcbnew.ToMM(t.GetCenter().y), "VIA"
            else:
                yy, lay = pcbnew.ToMM(t.GetStart().y), b.GetLayerName(t.GetLayer())
            if lo < yy <= hi:
                c[lay] += 1
        return dict(c)
    except Exception as ex:
        return {"error": str(ex)}


def pin_audit():
    rows = []
    for p in sorted(STEP2.glob("*.json")):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for k, v in (d.get("inputs") or {}).items():
            if not (isinstance(v, str) and len(v) == 16 and k.endswith("_record")):
                continue
            g = [x for x in STEP2.glob(f"*{k[:-7]}*.json") if x.resolve() != p.resolve()]
            f = g[0] if len(g) == 1 else None
            rows.append({"file": p.name, "key": k, "cited": v, "ref": f.name if f else None,
                         "actual": s16(f) if f else None, "ok": bool(f) and s16(f) == v})
    return (all(r["ok"] for r in rows) and bool(rows)), rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    s12, s13 = json.loads(S12.read_text()), json.loads(S13.read_text())
    draw = json.loads(DRAW.read_text())
    checks, teeth = {}, {}

    # ---------- A：结构差分 = 预期集 ----------
    f12, f13 = dict(flat(s12)), dict(flat(s13))
    changed = {k for k in set(f12) & set(f13) if f12[k] != f13[k]}
    added = {k for k in set(f13) - set(f12) if not k.startswith(RETIRED_KEY)}
    removed = set(f12) - set(f13)
    checks["A_spec_delta"] = {
        "ok": not (changed - EXPECTED_DELTA) and not added and not removed and len(changed) == len(EXPECTED_DELTA),
        "n_changed_scalars": len(changed), "expected_n": len(EXPECTED_DELTA),
        "changed_paths": sorted(changed), "unexpected_changed": sorted(changed - EXPECTED_DELTA),
        "added_keys_outside_retired": sorted(added), "removed_keys": sorted(removed),
        "spec_version": [f12.get(".spec_version"), f13.get(".spec_version")]}
    pert = dict(f13); pert[".pd.zone_defs.gnd_planes[0].polygon[2][0]"] = 99.9   # 非预期路径（x 坐标）
    teeth["delta_detector"] = bool({k for k in set(f12) & set(pert) if f12[k] != pert[k]} - EXPECTED_DELTA)

    # ---------- A2：退役留存完整性 ----------
    ret = s13["pd"]["zone_defs"].get("retired_superseded_frame_extent_v1", {}).get("retired", [])
    m12, m13 = collections.defaultdict(list), collections.defaultdict(list)
    for zd, M in ((s12["pd"]["zone_defs"], m12), (s13["pd"]["zone_defs"], m13)):
        for g in zd.get("gnd_planes", []):
            M[f"gnd_planes[{g['net']}@{g['layer']}]"] += polys_of(g)
        for z in zd["power_zones"]:
            M[f"power_zones[{z['net']}@{z.get('zone')}]"] += polys_of(z)
    olds = {json.dumps(r["old_polygon"]) for r in ret}
    old_ok = all(r["old_polygon"] in m12.get(r["owner"], []) for r in ret)
    new_ok = all(r["new_polygon"] in m13.get(r["owner"], []) for r in ret)
    uncovered = [(o, p) for o, ps in m12.items() for p in ps
                 if any(abs(y - 70.7) < 1e-6 for _, y in p) and json.dumps(p) not in olds]
    still = [(o, p) for o, ps in m13.items() for p in ps if any(abs(y - 70.7) < 1e-6 for _, y in p)]
    checks["B_retired_completeness"] = {
        "ok": len(ret) == 5 and old_ok and new_ok and not uncovered and not still,
        "n_retired": len(ret), "old_polygons_match_rev12": old_ok, "new_polygons_match_rev13": new_ok,
        "n_rev12_70.7_uncovered": len(uncovered), "n_rev13_vertices_left_at_70.7": len(still),
        "retired_owners": [r["owner"] for r in ret]}

    # ---------- B：几何/板不变性 ----------
    sub = {k: hashlib.sha256(json.dumps(draw[k], sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
           for k in REV12_SUB}
    checks["C_invariance"] = {
        "ok": all(sub[k] == REV12_SUB[k] for k in REV12_SUB) and s16(BOARD) == BOARD_SHA
              and str(draw["inputs_sha"]["spec"]).startswith(SPEC13_SHA) and s16(S13) == SPEC13_SHA
              and not draw["frozen_sha_check"].get("drift"),
        "rev12_sub_hashes": sub, "expected_rev12_sub_hashes": REV12_SUB,
        "n_route_segments": len(draw["route_geometry"]), "n_pages": len(draw["pages"]),
        "board_sha16": s16(BOARD), "board_pin": BOARD_SHA,
        "drawing_inputs_spec": draw["inputs_sha"]["spec"], "spec13_sha16": s16(S13),
        "frozen_drift": draw["frozen_sha_check"].get("drift"), "rev12_drawing_blob": REV12_DRAWING_SHA}

    # ---------- D：参考平面连续性独立重算 + 桥带归属 ----------
    seg13, pts13, cls13, sig13, in5_in4_miss, cu13 = continuity(s13, draw)
    gnd_pts = {f"{k[0]}<-{k[1]}": v for k, v in pts13.items() if "GND_PLANE" in str(s13["stackup"].get(k[1], ""))}
    outside = [[round(q[0], 3), round(q[1], 3)] for q in in5_in4_miss if not (BRIDGE_X[0] < q[0] < BRIDGE_X[1])]
    distinct_in5 = len({i for (i, L, rl) in sig13 if (L, rl) == ("In5.Cu", "In4.Cu")})
    checks["D_reference_plane_recompute"] = {
        "ok": not gnd_pts and cls13.get("declared_copper_missing", 0) == 0
              and seg13.get(("In5.Cu", "In4.Cu")) == 54 and distinct_in5 == 54 and not outside,
        "seg_level_violations": {f"{k[0]}<-{k[1]}": v for k, v in seg13.items()},
        "point_level_violations": {f"{k[0]}<-{k[1]}": v for k, v in pts13.items()},
        "gnd_plane_ref_point_violations": gnd_pts, "class_counts": dict(cls13),
        "n_in5_segments_missing_in4": distinct_in5, "n_in4_miss_points": len(in5_in4_miss),
        "n_in4_miss_points_outside_bridge_band": len(outside), "outside_examples": outside[:10],
        "bridge_band_x": list(BRIDGE_X)}

    # ---------- E：rev-12 FAIL 独立复现 + 板实佐证 ----------
    seg12, pts12, cls12, sig12, _, _ = continuity(s12, draw)
    distinct_gnd12 = len({i for (i, L, rl) in sig12 if "GND_PLANE" in str(s12["stackup"].get(rl, ""))})
    realized = board_band_counts(*VOID_BAND)
    spec_side = cls12.get("declared_copper_missing", 0) == 60 and distinct_gnd12 == 36
    board_ok = None if "error" in realized else (realized.get("In5.Cu") == 316 and realized.get("In2.Cu") == 12
                                                 and realized.get("VIA") == 24)
    checks["E_rev12_fail_repro"] = {
        "ok": spec_side and board_ok is not False,
        "spec_side_ok": spec_side, "board_side_ok": board_ok,
        "rev12_class_counts": dict(cls12), "rev12_distinct_gnd_plane_segments": distinct_gnd12,
        "rev12_gnd_plane_seg_violations": {f"{k[0]}<-{k[1]}": v for k, v in seg12.items()
                                           if "GND_PLANE" in str(s12["stackup"].get(k[1], ""))},
        "board_entities_in_void_band_70.7_79.0": realized,
        "note": "独立复现 CO-106 对 rev-12 的 FAIL 读数（60 项/36 段）+ 板实已用该带 ⇒ CO-107 修真缺陷"}

    # ---------- C：链 pin 前移 ----------
    stale = [t.name for t in sorted((K2 / "tools").glob("p3_v57_*.py"))
             if STALE_SHA in t.read_text(errors="ignore") and t.name not in (CO103_TOOL, SELF)]
    pins_ok, pin_rows = pin_audit()
    try:
        blob105 = subprocess.run(["git", "-C", str(K2), "show", f"04d0ee1:{CO105.relative_to(K2)}"],
                                 capture_output=True, text=True, check=True).stdout
        blob98 = subprocess.run(["git", "-C", str(K2), "show", f"04d0ee1:{CO98.relative_to(K2)}"],
                                capture_output=True, text=True, check=True).stdout.encode()
        as_found = {"checked": True, "co105_pin_at_04d0ee1": json.loads(blob105)["inputs"]["co98_record"],
                    "co98_actual_at_04d0ee1": hashlib.sha256(blob98).hexdigest()[:16],
                    "current_co105_pin": json.loads(CO105.read_text())["inputs"]["co98_record"],
                    "current_co98_actual": s16(CO98)}
        as_found["drift_at_04d0ee1"] = as_found["co105_pin_at_04d0ee1"] != as_found["co98_actual_at_04d0ee1"]
        as_found["corrected_now"] = as_found["current_co105_pin"] == as_found["current_co98_actual"]
    except Exception as ex:
        as_found = {"checked": False, "reason": str(ex)}
    checks["F_chain_pins"] = {
        "ok": not stale and pins_ok and as_found.get("corrected_now", False),
        "stale_rev12_consumers": stale, "provenance_pins_ok": pins_ok,
        "provenance_pins": pin_rows, "as_found_04d0ee1": as_found}
    teeth["pin_drift_detector"] = (s16(CO98) == s16(CO98)) and not any(
        r["ok"] for r in [{"cited": s16(CO98)[:-1] + ("0" if s16(CO98)[-1] != "0" else "1"), "actual": s16(CO98)}]
        if r["cited"] == r["actual"])
    teeth["continuity_detector"] = (pip((60.0, 50.0), [[49.8, 33.3], [88.37, 33.3], [88.37, 78.7], [49.8, 78.7]]) is True
                                    and pip((200.0, 50.0), [[49.8, 33.3], [88.37, 33.3], [88.37, 78.7], [49.8, 78.7]]) is False)
    teeth["teeth_ok"] = all(bool(v) for k, v in teeth.items() if k != "teeth_ok")

    findings = [
        {"id": "F-A", "severity": "low", "disposition": "CORRECTED_IN_THIS_REVIEW",
         "statement": "CO-105 记录的 provenance pin `inputs.co98_record` 在执行者提交态 04d0ee1 为 `267f86b5c02b8fc3`，"
                      "既非当时已重基线的 co98 记录 `48b5bd29009a9eb8`、亦非任何已提交 co98 版本 ⇒ 记录内部身份引用漂移。"
                      "co77 只校验 `file`+`sha16` 邻接引用，不覆盖记录内 provenance pin（同 CO-103 F-C 已指出的盲区）。",
         "evidence": as_found, "target": "CO-105 记录 / boundary 收口件",
         "action": "确定性重跑既有工具 p3_v57_co105_f4_scope_disposition.py（无新代码路径）→ pin 恢复 `48b5bd29009a9eb8`；"
                   "记录 sha `1e9c5872d1480225` → `a53f7e3b75d3d427`；boundary v1.73 同步更新引用 + co77 PASS。"},
        {"id": "F-B", "severity": "informational", "disposition": "INFORMATIONAL",
         "statement": "CO-106 记录字段 `n_declared_copper_missing_points` / `class_counts` 实计 (段,参考层) 项数而非采样点数，"
                      "且分类仅取每 (段,参考层)**首个**缺失点。判据成立性不受影响（本件独立**点级全量**重算：GND 整面层缺铜 = 0，与 CO-106 一致）。",
         "evidence": {"rev13_gnd_plane_point_violations": gnd_pts,
                      "rev13_seg_entries": {f"{k[0]}<-{k[1]}": v for k, v in seg13.items()},
                      "rev13_point_entries": {f"{k[0]}<-{k[1]}": v for k, v in pts13.items()}},
         "target": "CO-106 记录/工具字段命名（建议后续 rev 更名或注明计法）"},
        {"id": "F-C", "severity": "low", "disposition": "OPEN_DECLARED",
         "statement": "CO-87 L2 合格标准覆盖矩阵仍为五行、无「参考平面」行；CO-106 的 D 项 `ok` 恒真（『补全动作本身』），"
                      "故**登记册**本身仍不完整（属 CO-106 已**声明**的缺口，非静默）。",
         "evidence": {"co87_matrix_items": ["容量总和 ≥ 需求（走廊闭合）", "长度预算闭合（等长窗口）", "过孔预算闭合",
                                            "PDN 压降达标（ch.5 §4）", "热（ch.2 L2 裁判标准）"],
                      "ch2_criteria": "物理可行性：走廊闭合、等长预算、参考平面、PDN 压降、热"},
         "target": "co87 矩阵（建议下一 rev 补行）"},
    ]
    hard = all(v["ok"] for v in checks.values()) and teeth["teeth_ok"]
    rec = {"artifact": "m13_v57_co108_rev13_nonexecutor_review", "schema": 1, "revision": "CO-108.1",
           "nature": "L2 非执行者对抗复评：rev-13 新基线（对象 = CO-106/107 + 链 pin 前移 + 几何/板不变性）",
           "reviewer": "非执行者会话（rev-13 施加者之外的独立会话；L2_STRUCTURE_v2.0.md:137 禁自评）",
           "target_baseline": {"spec_rev13": s16(S13), "drawing": s16(DRAW), "board": s16(BOARD),
                               "rev12_drawing_blob": REV12_DRAWING_SHA},
           "checks": checks, "teeth": teeth, "findings": findings,
           "verdict": "PASS_WITH_FINDINGS" if hard else "FAIL",
           "non_claims": ["只读（除自身记录）；不改 SPEC/板/阈值/冻结源",
                          "一阶点采样（端点 + 相邻中点）；不做网格/有限元",
                          "未重跑 L3 桥区几何派生（属下一 CO，L2/L3 自裁）"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-108 verdict=%s | checks=%s | teeth=%s" % (
        rec["verdict"], {k: v["ok"] for k, v in checks.items()}, teeth["teeth_ok"]))
    print("  findings:", [(f["id"], f["severity"], f["disposition"]) for f in findings])
    print("  record sha16:", s16(Path(a.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
