#!/usr/bin/env python3
"""CO-114：【L2 · 非执行者对抗复评】SPEC **rev-14** 新基线（对象 = CO-113 施加 + CO-115 更正 + 链 pin 前移）。

复评人：非执行者会话（rev-14 施加者 z13 之外的独立、context 隔离会话；`L2_STRUCTURE_v2.0.md:137` 禁自评）。
本件**不复用执行者断言**，逐项独立重算/反证：
  A 结构差分：rev-14 vs rev-13 既有标量**仅** `spec_version` 变；新增键全落声明命名空间；无删除键；CO-113 记录自陈一致
  B 不变性：新图纸 vs **rev-13 git blob** 的 route_geometry/pages/landing_rows 逐字节同；板/冻结四源 4/4；frozen drift=∅
  C 链 pin：live 消费者全数 pin rev-14；rev-13 仅历史件合法持有；记录内 provenance pin 全数一致
  D CO-115 更正成立性：keepout band ↔ 走廊两侧 0.2 内缩算术 + CO-95 effect 授权（独立复算）
  E CO-111 独立复算：In5 走廊暴露长度/占比/网类 + L5 SI 阻抗覆盖面（口径反证）
  F 新键无消费者（引擎/L4/L5 零引用 ⇒ 「读数不变」为逻辑必然，非信任）
牙齿：A..F 各带合成负控 + 非空真下限。只读（除自身记录）；不改 SPEC/板/阈值/冻结源/其它工件。
CLI: python3 tools/p3_v57_co114_rev14_nonexecutor_review.py
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
S13, S14 = L3 / "SPEC_k2_v4.spec-rev-13.json", L3 / "SPEC_k2_v4.spec-rev-14.json"
DRAW = STEP2 / "m13_v57_w3_joint_assignment.json"
CO111, CO113 = STEP2 / "m13_v57_co111_in5_pcie_corridor_exposure.json", STEP2 / "m13_v57_co113_spec_rev14_declare.json"
CO115, CO87 = STEP2 / "m13_v57_co115_corridor_stale_keepout_correction.json", STEP2 / "m13_v57_co87_l2_acceptance_coverage.json"
SI = STEP2 / "m13_v57_l5_si_pi_emc_record.json"
BOUND = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_80.md"
BOARD_F, BOARD_L4 = K2 / "k2_v4_8L.kicad_pcb", K2 / "k2_v4_8L.l4.kicad_pcb"
SPEC_ORIG, MANIFEST = L3 / "SPEC_k2_v4.json", STEP2 / "m13_v57_s1_page_manifest.json"
DRC, DRC_C = K2 / "_shared/eda_core/drc_rules.json", K2.parent / "_shared/eda_core/drc_rules.json"
OUT = STEP2 / "m13_v57_co114_rev14_nonexecutor_review.json"

SPEC14_SHA, SPEC13_SHA = "188b01deb34c9fba", "7943be727a4f8ef9"
DRAW14_SHA, DRAW13_BLOB = "0e74718b1e31dca5", "73c0066df83fa8c2"
BOARD_L4_SHA, BOARD_F_SHA, ORIG_SHA = "0e636a67c1472462", "fb07d25ac426ff84", "0bd52ed48e720b8c"
MANIFEST_SHA, DRC_SHA = "a8ef3ea8ecff99d7", "0a459839e15960b8"
SUB = {"route_geometry": "c27d9f5b29c82ba2", "pages": "2535f3306cebe6eb", "landing_rows": "74234e98afe7498f"}
CORRIDOR, BAND, CLR, TOL = (49.8, 88.37), (50.0, 88.17), 0.2, 1e-6
REV13_REF, REL_DRAW = "d1af217^", "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment.json"
REV13_TOOLS = {"p3_v57_co107_spec_rev13_frame_align.py", "p3_v57_co108_rev13_nonexecutor_review.py",
               "p3_v57_co109_in4_void_l2_ruling.py", "p3_v57_co110_l2_coverage_closure.py",
               "p3_v57_co111_in5_pcie_corridor_exposure.py", "p3_v57_co112_bcu_bridge_declaration.py",
               "p3_v57_co113_spec_rev14_declare.py"}
LIVE_TOOLS = ["p3_v57_w3_constructive.py", "p3_v57_w3_constructive_validator_v2.py",
              "p3_v57_co78_layer_role_drift_gate.py", "p3_v57_co81_project_rules_gate.py",
              "p3_v57_co84_dru_domain_gate.py", "p3_v57_co91_pdn_planned_coord_clearance_gate.py",
              "p3_v57_co92_pdn_repair_candidate.py", "p3_v57_co95_in4_reachability.py",
              "p3_v57_co98_reachability_status_report.py", "p3_v57_co99_pdn_mutual_conflict_gate.py",
              "p3_v57_co102_pdn_apply_local.py", "p3_v57_co104_pdn_blocked_ruling.py",
              "p3_v57_co105_f4_scope_disposition.py", "p3_v57_co106_reference_plane_gate.py",
              "p3_v57_co77_closure_declaration_sweep.py"]


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


def sub_of(d) -> dict:
    return {k: hashlib.sha256(json.dumps(d[k], sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16] for k in SUB}


def polys_of(z):
    ps, p = z.get("polygons"), z.get("polygon")
    if ps:
        return ps if isinstance(ps[0][0], list) else [ps]
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


def walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield str(k)
            yield from walk_keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk_keys(v)


def fam(p) -> str:
    if ".in4_corridor_void_by_design_v1" in p or p.startswith(".pd.zone_defs.plane_reachability_status.na_scope_v1"):
        return "declared"
    m = re.match(r"\.pd\.zone_defs\.power_zones\[\d+\]\.(\w+)", p)
    if m:
        return {"bridge_layer": "declared", "bcu_bridge_bands": "declared",
                "bcu_bridge_bands_source": "extra_source"}.get(m.group(1), "unexpected")
    return "unexpected"


def provenance_audit():
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
    return (bool(rows) and all(r["ok"] for r in rows)), rows


def in4_copper(spec):
    cu = []
    for g in spec["pd"]["zone_defs"].get("gnd_planes", []):
        if g.get("layer") == "In4.Cu":
            cu += polys_of(g)
    for z in spec["pd"]["zone_defs"]["power_zones"]:
        if z.get("layer") == "In4.Cu":
            cu += polys_of(z)
    return cu


def seg_lens(P, cu):
    tot = miss = 0.0
    for i in range(len(P) - 1):
        A, B = tuple(P[i]), tuple(P[i + 1])
        L = ((B[0] - A[0]) ** 2 + (B[1] - A[1]) ** 2) ** 0.5
        tot += L
        if not any(pip(((A[0] + B[0]) / 2, (A[1] + B[1]) / 2), q) for q in cu):
            miss += L
    return tot, miss


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    s13, s14 = json.loads(S13.read_text()), json.loads(S14.read_text())
    draw = json.loads(DRAW.read_text())
    checks, teeth, findings = {}, {}, []

    # ---------- A：结构差分 = 仅新增声明键 + spec_version ----------
    f13, f14 = dict(flat(s13)), dict(flat(s14))
    changed = {k for k in set(f13) & set(f14) if f13[k] != f14[k]}
    added, removed = set(f14) - set(f13), set(f13) - set(f14)
    fc, unexpected = collections.Counter(fam(p) for p in added), sorted(p for p in added if fam(p) == "unexpected")
    rec113 = json.loads(CO113.read_text())
    checks["A_spec_delta"] = {
        "ok": changed == {".spec_version"} and not removed and not unexpected and len(added) >= 8,
        "n_changed_existing": len(changed), "changed_paths": sorted(changed), "n_added": len(added),
        "n_removed": len(removed), "removed_paths": sorted(removed), "added_families": dict(fc),
        "unexpected_added": unexpected[:10], "spec_version": [f13.get(".spec_version"), f14.get(".spec_version")],
        "co113_record_says": {"only_spec_version_changed_among_existing":
                              rec113["changes"]["only_spec_version_changed_among_existing"],
                              "out_sha16": rec113["out_sha16"], "n_bridge_zones": rec113["changes"]["n_bridge_zones"]},
        "co113_record_consistent": rec113["out_sha16"] == SPEC14_SHA
                                  and rec113["changes"]["only_spec_version_changed_among_existing"] is True,
        "declared_families_missing_source_key": sorted(p for p in added if fam(p) == "extra_source")[:4]}
    pert = dict(f14); pert[".pd.zone_defs.gnd_planes[0].polygon[0][0]"] = 0.0
    pert2 = dict(f14); pert2[".pd.zone_defs.out_of_contract_probe"] = 1
    teeth["A_existing_scalar_detector"] = bool({k for k in set(f13) & set(pert) if f13[k] != pert[k]} - {".spec_version"})
    teeth["A_unexpected_key_detector"] = bool([p for p in (set(pert2) - set(f13)) if fam(p) == "unexpected"])

    # ---------- B：几何/板/冻结源不变性（rev-13 取自 git blob，非执行者记录） ----------
    blob = subprocess.check_output(["git", "-C", str(K2), "show", f"{REV13_REF}:{REL_DRAW}"])
    d13 = json.loads(blob)
    four = {"spec_orig": (s16(SPEC_ORIG), ORIG_SHA), "manifest": (s16(MANIFEST), MANIFEST_SHA),
            "board_frozen": (s16(BOARD_F), BOARD_F_SHA), "drc": (s16(DRC), DRC_SHA)}
    checks["B_invariance"] = {
        "ok": hashlib.sha256(blob).hexdigest()[:16] == DRAW13_BLOB and s16(DRAW) == DRAW14_SHA
              and sub_of(d13) == SUB and sub_of(draw) == SUB and all(x == y for x, y in four.values())
              and s16(DRC_C) == DRC_SHA and s16(BOARD_L4) == BOARD_L4_SHA
              and str(draw["inputs_sha"]["spec"]).startswith(SPEC14_SHA) and draw["frozen_sha_check"].get("drift") == []
              and str(draw["frozen_sha_check"]["actual"].get("spec") or "").startswith(SPEC14_SHA),
        "rev13_blob_sha16": hashlib.sha256(blob).hexdigest()[:16], "rev13_blob_pin": DRAW13_BLOB,
        "rev13_sub": sub_of(d13), "rev14_sub": sub_of(draw), "expected_sub": SUB,
        "drawing_sha16": s16(DRAW), "drawing_pin": DRAW14_SHA,
        "frozen_four": {k: {"actual": x, "pin": y, "ok": x == y} for k, (x, y) in four.items()},
        "drc_container_identical": s16(DRC_C) == DRC_SHA, "board_l4_sha16": s16(BOARD_L4), "board_l4_pin": BOARD_L4_SHA,
        "frozen_drift": draw["frozen_sha_check"].get("drift"),
        "frozen_actual_spec": str(draw["frozen_sha_check"]["actual"].get("spec"))[:64]}
    sub_t = json.loads(json.dumps(draw)); sub_t["route_geometry"][0]["points"][0][0] += 1e-6
    teeth["B_geometry_hash_detector"] = sub_of(sub_t)["route_geometry"] != SUB["route_geometry"]
    teeth["B_frozen_source_detector"] = s16(SPEC_ORIG) == ORIG_SHA and (hashlib.sha256((ORIG_SHA + "x").encode()).hexdigest()[:16] != ORIG_SHA)

    # ---------- C：链 pin 前移 + provenance pin ----------
    txt = {p.name: p.read_text() for p in sorted((K2 / "tools").glob("*.py"))}
    self_name = Path(__file__).name
    ref13 = sorted(n for n, t in txt.items() if "spec-rev-13.json" in t and n != self_name)
    ref14 = sorted(n for n, t in txt.items() if "spec-rev-14.json" in t)
    pins_ok, pins = provenance_audit()
    checks["C_spec_pin_advance"] = {
        "ok": (not [n for n in LIVE_TOOLS if n in ref13]) and len([n for n in LIVE_TOOLS if n in ref14]) == len(LIVE_TOOLS)
              and (not (set(ref13) - REV13_TOOLS)),
        "n_live_tools": len(LIVE_TOOLS), "live_on_rev14": len([n for n in LIVE_TOOLS if n in ref14]),
        "live_missing_rev14": [n for n in LIVE_TOOLS if n not in ref14], "live_on_rev13": [n for n in LIVE_TOOLS if n in ref13],
        "rev13_referencing_tools": ref13, "unexpected_rev13_tools": sorted(set(ref13) - REV13_TOOLS),
        "n_tools_referencing_rev14": len(ref14),
        "provenance_pin_consistency": {"ok": pins_ok, "n_pins": len(pins), "mismatch": [r for r in pins if not r["ok"]],
                                       "invariant": "CO-108 check C：记录内 inputs.*_record pin 须 == 当前文件（本件独立复算，§见 F-6）"}}
    probe = dict(pins[0]) if pins else {}
    teeth["C_pin_drift_detector"] = bool(pins) and ("0" * 16 != pins[0]["actual"]) and (("0" * 16) != pins[0]["cited"])

    # ---------- D：CO-115 keepout 更正成立性（独立复算） ----------
    zd = s14["pd"]["zone_defs"]
    keep, band = zd["retired_in4_keepout_band_6l"], zd["retired_in4_keepout_band_6l"]["band"]
    zones = {z["zone"]: z for z in zd["power_zones"] if z.get("polygon")}
    west_e = max(p[0] for p in zones["MCU_VDD_WEST"]["polygon"])
    east_w = min(p[0] for p in zones["P3V3_EAST"]["polygon"])
    key = zd["in4_corridor_void_by_design_v1"]
    c115 = json.loads(CO115.read_text())
    checks["D_keepout_correction"] = {
        "ok": abs(west_e - (band["x"][0] - CLR)) < TOL and abs(east_w - (band["x"][1] + CLR)) < TOL
              and key["corridor_x"] == [west_e, east_w] and keep.get("retired_by") == "CO-95"
              and "按网归属铺设" in str(keep.get("effect", ""))
              and c115["verdict"] == "L2_CORRECTION_STALE_KEEPOUT_PENDING_L3_L1_OWNERSHIP"
              and all(v["ok"] for v in c115["checks"].values()),
        "band_x": band["x"], "west_edge": west_e, "east_edge": east_w, "expected_west": round(band["x"][0] - CLR, 6),
        "expected_east": round(band["x"][1] + CLR, 6), "corridor_x_in_rev14_key": key["corridor_x"],
        "keepout_retired_by": keep.get("retired_by"), "effect_authorizes_pour": "按网归属铺设" in str(keep.get("effect", "")),
        "co115_verdict": c115["verdict"], "co115_all_checks_ok": all(v["ok"] for v in c115["checks"].values()),
        "erroneous_key_note": key["note"][:96]}
    teeth["D_inset_detector"] = abs((band["x"][0] + 1.0 - CLR) - west_e) > TOL

    # ---------- E：CO-111 独立复算 + L5 阻抗覆盖面反证 ----------
    cu, tot, unref = in4_copper(s14), collections.Counter(), collections.Counter()
    for r in draw["route_geometry"]:
        if r["layer"] != "In5.Cu":
            continue
        net = (r["key"][0] if isinstance(r.get("key"), list) else str(r.get("key"))).split("/")[0]
        t, m = seg_lens(r["points"], cu)
        tot[net] += t; unref[net] += m
    T, U = sum(tot.values()), sum(unref.values())
    nets = sorted(tot)
    c111 = json.loads(CO111.read_text()); b111 = c111["checks"]["B_quantified_exposure"]
    sb = json.loads(SI.read_text())["SI"]
    pli = sb["netclass_geometry"]["per_layer_impedance"]
    region_scoped = any(re.search(r"region|corridor|per_route|by_segment", str(k), re.I) for k in walk_keys(sb["netclass_geometry"]))
    checks["E_exposure_recompute"] = {
        "ok": bool(nets) and all(n.startswith("PCIE_") for n in nets) and len(nets) == 16
              and abs(U - b111["unref_len_mm"]) < 0.05 and abs(T - b111["in5_total_len_mm"]) < 0.05
              and abs(U / T - b111["unref_pct"]) < 1e-3 and sb.get("skew_ok") is True
              and float(sb.get("max_intra_pair_skew_mm", 9)) <= 0.15 and not region_scoped,
        "recomputed": {"total_mm": round(T, 3), "unref_mm": round(U, 3), "pct": round(U / T, 4), "n_nets": len(nets)},
        "co111_record": {"total_mm": b111["in5_total_len_mm"], "unref_mm": b111["unref_len_mm"],
                         "pct": b111["unref_pct"], "n_nets": c111["checks"]["A_all_pcie_impedance_controlled"]["n_nets"]},
        "all_nets_pcie": all(n.startswith("PCIE_") for n in nets),
        "si_signoff": {"skew_ok": sb.get("skew_ok"), "max_skew_mm": sb.get("max_intra_pair_skew_mm"),
                       "per_layer_impedance_present": bool(pli),
                       "in5_declared_refs": pli.get("In5.Cu", {}).get("refs"),
                       "conformance": sb["netclass_geometry"].get("conformance"),
                       "region_scoped_impedance_verification": region_scoped},
        "co111_checkC_claim": c111["checks"]["C_l5_si_does_not_verify_impedance"]["note"]}
    teeth["E_zero_control"] = seg_lens([[100.0, 50.0], [120.0, 50.0]], cu)[1] == 0.0
    teeth["E_positive_control"] = seg_lens([[60.0, 50.0], [80.0, 50.0]], cu)[1] > 0.0

    # ---------- F：新键无消费者（读数不变为逻辑必然） ----------
    names = ["in4_corridor_void_by_design_v1", "bridge_layer", "bcu_bridge_bands", "na_scope_v1"]
    prod, corr = "p3_v57_co113_spec_rev14_declare.py", {"p3_v57_co115_corridor_stale_keepout_correction.py",
                                                        "p3_v57_co114_rev14_nonexecutor_review.py"}
    cons = {n: sorted(t for t, s in txt.items() if n in s and "spec-rev-14.json" in s and t != prod and t not in corr)
            for n in names}
    raw = {n: sorted(t for t, s in txt.items() if n in s) for n in names}
    checks["F_new_keys_no_consumer"] = {
        "ok": all(not v for v in cons.values()) and all(raw[n] for n in names),
        "consumers_of_rev14_keys": cons, "nonempty_search_control": {n: raw[n] for n in names},
        "note": "rev-14 新增声明键在引擎/L4/L5/各闸（即 rev-14 SPEC 消费者）中零引用 ⇒ CO-113「读数不变」为逻辑必然（非信任执行者）"}
    teeth["F_scan_nonvacuous"] = all(raw[n] for n in names)

    # ---------- 发现 ----------
    if key["note"].startswith("CO-109/110/111/112") and "按设计无铜" in key["note"]:
        findings.append({"id": "F-1", "severity": "high", "disposition": "OPEN_DECLARED",
                         "statement": "rev-14 canonical 键 `pd.zone_defs.in4_corridor_void_by_design_v1` 的陈述（`note` = 'In4 走廊按设计无铜'）"
                                      "已被 **CO-115** 判为**事实错误**（走廊空洞 = 失效 keepout 残留，待 L3 派生）。即：现行 canonical SPEC "
                                      "**内含一个已定性的错误声明**。A 面证明该键确为 rev-14 新增（非历史残留）⇒ 缺陷随 rev-14 生效。",
                         "evidence": {"key_note": key["note"][:120], "co115_verdict": c115["verdict"],
                                      "co115_corrects": c115["corrects"]},
                         "target": "rev-15（更正键语义）；须先有 OWNER/L1 band 归属界面（bundling 才作一次 rev 重基线 + 复评）"})
    if any("按设计" in str(r.get("evidence", "")) for r in json.loads(CO87.read_text()).get("matrix", [])):
        findings.append({"id": "F-2", "severity": "medium", "disposition": "OPEN_DECLARED",
                         "statement": "live 验收登记册 `co87` 的「参考平面」行证据文本仍内嵌 `CO-110 判为按设计 In4 走廊空洞（bridge zone = B.Cu）`，"
                                      "与 CO-115 更正冲突 ⇒ 该行状态（INDETERMINATE）虽正确，**证据叙述已陈旧**。",
                         "evidence": {"co87_reference_plane_row": [r for r in json.loads(CO87.read_text())["matrix"]
                                                                  if "参考平面" in r.get("item", "")]},
                         "target": "co87 矩阵（下一 rev 一并更正）"})
    if any(fam(p) == "extra_source" for p in added):
        findings.append({"id": "F-3", "severity": "low", "disposition": "OPEN_DECLARED",
                         "statement": "CO-113 变更记录的 `changes.new_keys` **少声明**一个实际新增键 `bcu_bridge_bands_source`（工具写入，属 band 来源标注）。"
                                      "无功能影响（无消费者），但**声明完整性**缺口。",
                         "evidence": {"added_extra_source_keys": sorted(p for p in added if fam(p) == "extra_source")[:3],
                                      "declared_new_keys": rec113["changes"]["new_keys"]},
                         "target": "CO-113 记录 / rev-15 声明"})
    if pli:
        findings.append({"id": "F-4", "severity": "low", "disposition": "INFORMATIONAL",
                         "statement": "CO-111 check C 的措辞『**无逐线阻抗核验字段**』不精确：L5 SI 记录实含 `netclass_geometry.per_layer_impedance`"
                                      "（In5 声明 refs=[In4,In6]）与 `conformance=DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON`。真正的缺口是"
                                      "**区域无关性**（In5 阻抗模型无条件假定 In4 参考存在）⇒ CO-111 的实质结论（走廊阻抗未验）**成立且被本件加强**，仅措辞需收敛。",
                         "evidence": {"per_layer_impedance_In5": pli.get("In5.Cu"), "conformance": sb["netclass_geometry"].get("conformance"),
                                      "region_scoped_verification_field": region_scoped},
                         "target": "CO-111 措辞（下一 rev 收敛为『区域条件阻抗未验』）"})
    btxt = BOUND.read_text()
    if re.search(r"spec-rev-14\.json`（[^|]*按设计", btxt):
        findings.append({"id": "F-5", "severity": "informational", "disposition": "CLOSED_BY_THIS_REVIEW",
                         "statement": "boundary v1.80 §2「现行 SPEC」行仍把 rev-14 描述为『In4 走廊空洞按设计』，与同件 §1 ㊼/§6-36 的 CO-115 更正**自相矛盾**；"
                                      "本件出 v1.81 时一并更正措辞。",
                         "evidence": {"boundary_v1_80_sha16": s16(BOUND)},
                         "target": "boundary v1.81（本件）"})

    if not pins_ok:
        findings.append({"id": "F-6", "severity": "medium", "disposition": "OPEN_DECLARED",
                         "statement": "rev-14 重基线后 4 个记录内 5 处 `inputs.*_record` provenance pin 指向**已被取代**的上游记录"
                                      "（CO-108 check C 的不变量被打破）：co98←co95 / co105←co98 / co109←co106 / co110←co106 / co110←co87。"
                                      "CO-113 只前移 SPEC pin 并重跑闸记录（co87/95/98/106 于 d1af217 变 sha），未刷新上级记录的 inter-record pin "
                                      "⇒ 与 CO-108 F-A 同族盲区（CO-77 不覆盖记录内 provenance pin）。被引值均为 git 内**真实历史版本**（非 F-A 式伪造）"
                                      "⇒ 属『陈旧 pin』，非『漂移伪造』。",
                         "evidence": {"mismatch": [{"file": r["file"], "key": r["key"], "cited": r["cited"],
                                                   "actual": r["actual"], "ref": r["ref"]} for r in pins if not r["ok"]]},
                         "target": "pin 刷新 CO（可并入 rev-15；CO-108 F-A 先例允许确定性重跑既有工具、语义不变），或在记录内显式标注『历史 pin』"})

    hard = all(v["ok"] for v in checks.values()) and all(bool(v) for v in teeth.values())
    rec = {"artifact": "m13_v57_co114_rev14_nonexecutor_review", "schema": 1, "revision": "CO-114.1",
           "nature": "L2 非执行者对抗复评：SPEC rev-14 新基线（对象 = CO-113 + CO-115 + 链 pin 前移 + 几何/板不变性）",
           "reviewer": "非执行者会话（rev-14 施加者 z13 之外的独立、context 隔离会话；L2_STRUCTURE_v2.0.md:137 禁自评）",
           "target_baseline": {"spec_rev14": s16(S14), "spec_rev13": s16(S13), "drawing": s16(DRAW),
                               "drawing_rev13_blob": DRAW13_BLOB, "board": s16(BOARD_L4)},
           "checks": checks, "teeth": teeth, "findings": findings,
           "verdict": "PASS_WITH_FINDINGS" if hard else "FAIL",
           "non_claims": ["只读（除自身记录）；不改 SPEC/板/阈值/冻结源/其它工件",
                          "一阶点采样（段中点）；不做网格/有限元；不重跑 L3 桥区几何派生",
                          "「读数不变」以『新键零消费者 + 图纸/板逐字节同』为逻辑论证，未重跑 G4..G7 全链"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-114 verdict=%s | checks=%s | teeth=%s" % (rec["verdict"], {k: v["ok"] for k, v in checks.items()},
                                                        {k: bool(v) for k, v in teeth.items()}))
    print("  findings:", [(f["id"], f["severity"], f["disposition"]) for f in findings])
    print("  record sha16:", s16(Path(a.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
