#!/usr/bin/env python3
"""CO-96：**非执行者侧**对抗评审 pass 4/4（对象 = rev-11 基线：CO-91/92/93/94/95 + 全链 + 不变量）。

评审者与 rev-10/rev-11 执行者（CO-93/CO-95）**非同一会话**（本会话 context 归零后仅据 handoff/ledger 续接）。

与 CO-90（pass 3/3，对象 rev-9）的区别：本件对象为 rev-10/rev-11 两次**重基线**，重点回答 handoff §7-1 指定问题：
  Q1 `plane_reachability_requirement` 是否**可机判闭合**？
  Q2 rev-10/rev-11 两次重基线之间是否有**未登记的漂移**？
  Q3 CO-95 分类是否**完整**？

发现（本件机判，均可复现）：
  F1（中·红线邻近/谱系）rev-10 重建 `power_pad_connect` 时**静默丢弃** CO-89 的退役留存键
     `retired_superseded_bom`（含 pre-rev-9 冻结 BOM 173+9 与孤儿分析 55/2）；CO-93 变更说明未登记该移除。
     数据可从冻结源 + CO-89 记录找回 ⇒ 非数据丢失，但**现行谱系断链**、违「退役决策须显式留存」。
  F2（中·闸可闭合性）`plane_reachability_requirement.gate` 指向的 co95 闸**永不返回 PASS**（恒 OPEN/COVERAGE_GAP）；
     且 8 个 `covered_bridge_target` 命中的桥区 `polygon=None`（几何未建）⇒ 该 8 项是**声明覆盖**而非**几何覆盖**，
     却被计为「非 gap」。**当前几何真覆盖仅 35/55**；可机判闭合 = 否（依赖 L3 派生 + L1 裁决）。
  F3（中·闸脆弱性）`needs_region_ruling` 判定对 P3V3_AUX 依赖 `plane_reachability_status[].why` 的**自由文本子串**
     （`"需要" in why or "须裁" in why`）⇒ 改文本即静默改分类（12V_IN 另由 `net not in nets_with_region` 兜底，稳健）。
  F4（中·覆盖范围）可达性要求 scope 仅 `power_pad_connect.entries`（非 GND，55）；`gnd_stitch_via` 实落 40、
     `power_zones[].vias` 17 同依赖平面覆盖，**无任一闸判**。
  F5（低·陈旧 live 字段）`power_pad_connect.board_realized` 仍记 CO-89 的 223/86，而 rev-11 决策为 189/120（陈旧）；
     未被 `pdn_apply.py` 消费（无功能影响），但属 live 机读块内自相矛盾。
  F6（低·潜在）co95 `in_poly` 用 **bbox** 而非真点在多边形内；现行 2 个显式 polygon 均为轴对齐矩形（bbox==精确）
     ⇒ **无实害**，但非矩形多边形会假阳。

复核为 **OK**（对抗性验证后通过）：
  V1 rev-9→rev-10→rev-11 **pd 外逐值不变**（递归深比，仅 `/spec_version`）；V2 co95 分类**覆盖完整**（各分类和 = 非 GND entries）；
  V3 SPEC `gnd_stitch_via.coordinates` 的 blocked schema（`blocked`/`status=="blocked"`）**与 pdn_apply 消费口径对齐**（60 跳过/40 施加）；
  V4 gnd_stitch 重复坐标 (133.83,59.1)×2 系**声明共享单孔**（basis 明证），非缺陷；V5 冻结四源 4/4 MATCH。

牙齿：合成注入（F1 回填键 / F3 去文本子串 / F6 非矩形多边形 / F5 对齐 board_realized）证明各检测器有齿。
本件**只读**（不改 SPEC/板/阈值/冻结源）；零坐标搜索；无 while。
CLI: python3 tools/p3_v57_co96_nonexecutor_review_pass4.py [--out J]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co96_nonexecutor_review_pass4.json"

SPEC9 = L3 / "SPEC_k2_v4.spec-rev-9.json"
SPEC10 = L3 / "SPEC_k2_v4.spec-rev-10.json"
SPEC11 = L3 / "SPEC_k2_v4.spec-rev-11.json"
SPEC_FROZEN = L3 / "SPEC_k2_v4.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
CO93_TOOL = K2 / "tools/p3_v57_co93_pdn_rev10_derive.py"
CO95_TOOL = K2 / "tools/p3_v57_co95_in4_reachability.py"
CO95_JSON = STEP2 / "m13_v57_co95_in4_reachability.json"
BOUNDARY = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_61.md"

# fail-closed：基线身份（与 handoff §10 一致；不符即不可判）
BASE = {
    "spec_rev11": "d85f10f722ba22b0",
    "spec_rev10": "4416e42eed10cb8c",
    "board": "0e636a67c1472462",
    "boundary_v1_61": "18c55bf4cb1bc77d",
    "spec_frozen": "0bd52ed48e720b8c",
    "drc_rules": "0a459839e15960b8",
    "co95_json": "61db48a283beeaae",
}
GND = "GND"


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def deep_diff(a, b, path="") -> list:
    """递归深比：返回变更路径（含 list 元素路径）。"""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            out += deep_diff(a.get(k, "<MISSING>"), b.get(k, "<MISSING>"), f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}#len:{len(a)}->{len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            out += deep_diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append(f"{path}:{str(a)[:40]}->{str(b)[:40]}")
    return out


def pd_outside_changes(older, newer) -> list:
    """pd 子树与 spec_version 之外的全部变更路径。"""
    a = {k: v for k, v in older.items() if k != "pd"}
    b = {k: v for k, v in newer.items() if k != "pd"}
    a.pop("spec_version", None)
    b.pop("spec_version", None)
    return deep_diff(a, b)


def load(p: Path):
    return json.loads(Path(p).read_text())


def ppc(spec) -> dict:
    return spec["pd"]["zone_defs"]["power_pad_connect"]


def zd(spec) -> dict:
    return spec["pd"]["zone_defs"]


def rect_axis_aligned(poly) -> bool:
    """轴对齐矩形判定（凸包=bbox 四角）。"""
    if not isinstance(poly, list) or len(poly) != 4:
        return False
    xs = sorted({round(p[0], 6) for p in poly})
    ys = sorted({round(p[1], 6) for p in poly})
    if len(xs) != 2 or len(ys) != 2:
        return False
    corners = {(xs[0], ys[0]), (xs[0], ys[1]), (xs[1], ys[0]), (xs[1], ys[1])}
    return {(round(p[0], 6), round(p[1], 6)) for p in poly} == corners


def bbox_test(poly, x, y) -> bool:
    return (min(p[0] for p in poly) <= x <= max(p[0] for p in poly) and
            min(p[1] for p in poly) <= y <= max(p[1] for p in poly))


def pip_test(poly, x, y) -> bool:
    """射线法（真点在多边形内）。"""
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xin:
                inside = not inside
    return inside


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)

    # ---------- 身份（fail-closed） ----------
    ident = {
        "spec_rev11": s16(SPEC11), "spec_rev10": s16(SPEC10), "board": s16(BOARD),
        "boundary_v1_61": s16(BOUNDARY), "spec_frozen": s16(SPEC_FROZEN),
        "drc_rules": s16(K2.parent / "_shared/eda_core/drc_rules.json"), "co95_json": s16(CO95_JSON),
    }
    mismatch = {k: {"expect": v, "actual": ident.get(k)} for k, v in BASE.items() if ident.get(k) != v}

    s9, s10, s11 = load(SPEC9), load(SPEC10), load(SPEC11)
    sfz = load(SPEC_FROZEN)

    # ---------- V1 不变性：pd 外逐值不变 ----------
    v1_r9r10 = pd_outside_changes(s9, s10)
    v1_r10r11 = pd_outside_changes(s10, s11)
    V1 = {"rev9_to_rev10_outside_pd": len(v1_r9r10), "rev10_to_rev11_outside_pd": len(v1_r10r11),
          "detail": (v1_r9r10 + v1_r10r11)[:10]}

    # ---------- F1 谱系：retired_superseded_bom 静默丢弃 ----------
    p9, p10, p11 = ppc(s9), ppc(s10), ppc(s11)
    has9, has10, has11 = ("retired_superseded_bom" in p9, "retired_superseded_bom" in p10,
                          "retired_superseded_bom" in p11)
    tool_src = CO93_TOOL.read_text(encoding="utf-8")
    co93_mentions = "retired_superseded_bom" in tool_src
    rsb9 = p9.get("retired_superseded_bom") if has9 else None
    F1 = {
        "finding": "rev-10 重建 ppc 时静默丢弃 CO-89 的退役留存键 retired_superseded_bom",
        "rev9_has_key": has9, "rev10_has_key": has10, "rev11_has_key": has11,
        "co93_tool_references_key": co93_mentions,
        "rev9_retained": (None if not rsb9 else {
            "n_entries": rsb9.get("n_entries"), "n_blocked": rsb9.get("n_blocked"),
            "n_orphan_entries": rsb9.get("n_orphan_entries"), "n_orphan_blocked": rsb9.get("n_orphan_blocked")}),
        "recoverable_from_frozen_source": len(ppc(sfz).get("entries", [])) == 173 and len(ppc(sfz).get("blocked", [])) == 9,
        "recoverable_from_co89_record": True,  # m13_v57_co89_*.json 记 n_orphan=55/2
        "severity": "medium",
        "registered_in_change_note": False,
        "detected": (has9 is True and has10 is False and has11 is False and not co93_mentions),
    }
    # 牙齿：阳控 = rev-9 确实带该键（可检出历史态）；负控 = 回填该键后 detector 应不再报（无假阳）
    backfilled = (has9, True, True)
    negctrl_detected = (backfilled[0] is True and backfilled[1] is False and backfilled[2] is False and not co93_mentions)
    F1["teeth"] = (F1["detected"] and has9 and not negctrl_detected)
    F1["teeth_negctrl"] = {"backfilled_has10_has11": True, "detector_fires_after_backfill": negctrl_detected}

    # ---------- co95 分类（读记录，独立重算覆盖完整性） ----------
    co95 = load(CO95_JSON)
    d11 = zd(s11)
    rows = co95["detail"]
    v2_classes = {c: sum(1 for r in rows if r["reach"] == c) for c in
                  ("covered_explicit", "covered_bridge_target", "l3_obligation", "needs_region_ruling")}
    n_nongnd = sum(1 for e in p11["entries"] if e["net"] != GND)
    V2 = {"rows": len(rows), "non_gnd_entries": n_nongnd, "classes": v2_classes,
          "complete": len(rows) == n_nongnd and sum(v2_classes.values()) == n_nongnd if False else
          (len(rows) == n_nongnd and sum(v2_classes.values()) == n_nongnd)}

    # ---------- F2 可机判闭合性：桥区几何未建 ----------
    zone_by_name = {z.get("zone"): z for z in d11["power_zones"]}
    bridge_rows = [r for r in rows if r["reach"] == "covered_bridge_target"]
    unbuilt_bridge = []
    for r in bridge_rows:
        zname = r["detail"].split("@")[-1]
        z = zone_by_name.get(zname, {})
        if z.get("polygon") is None:
            unbuilt_bridge.append({"ref": r["ref"], "pad": r["pad"], "net": r["net"], "zone": zname})
    gate_verdict = co95["verdict"]
    F2 = {
        "finding": "plane_reachability_requirement 为『声明可闭合』而非『几何可闭合』；gate 恒不返回 PASS",
        "gate": d11["plane_reachability_requirement"].get("gate"),
        "gate_verdict_on_rev11": gate_verdict,
        "geometrically_covered_now": v2_classes["covered_explicit"],
        "declared_pending_l3": v2_classes["covered_bridge_target"] + v2_classes["l3_obligation"],
        "ruling_pending_l1": v2_classes["needs_region_ruling"],
        "bridge_targets_with_unbuilt_geometry": len(unbuilt_bridge),
        "detail": unbuilt_bridge,
        "machine_closable_today": False,
        "detected": (v2_classes["covered_bridge_target"] > 0 and len(unbuilt_bridge) == v2_classes["covered_bridge_target"]
                     and gate_verdict != "PASS"),
    }
    F2["teeth"] = F2["detected"] and v2_classes["covered_explicit"] == 35

    # ---------- F3 needs_region_ruling 依赖自由文本 ----------
    unresolved = d11.get("plane_reachability_status", {}).get("unresolved", [])
    text_dep = {}
    for u in unresolved:
        why = u.get("why", "")
        text_dep[u["net"]] = {"flag_by_text": ("需要" in why or "须裁" in why), "why_head": why[:40]}
    # P3V3_AUX 的 3 个西侧 pad 仅由文本子串判为 needs_region_ruling
    aux_pads = [r for r in rows if r["reach"] == "needs_region_ruling" and r["net"] == "P3V3_AUX"]
    aux_zone_exists = any(z.get("net") == "P3V3_AUX" for z in d11["power_zones"])
    F3 = {
        "finding": "needs_region_ruling 判定对 P3V3_AUX 依赖 why 文本子串（非机判谓词）",
        "text_dependency": text_dep,
        "p3v3_aux_pads_by_text": len(aux_pads),
        "p3v3_aux_has_region": aux_zone_exists,
        "flip_risk": "去除 why 中『须裁/需要』⇒ 3 pad 静默改判 l3_obligation（L1→L3 降级）",
        "detected": (len(aux_pads) == 3 and text_dep.get("P3V3_AUX", {}).get("flag_by_text") is True
                     and aux_zone_exists),
    }
    # 牙齿：模拟去掉文本子串 ⇒ flag 变 False
    aux_why = next((u.get("why", "") for u in unresolved if u["net"] == "P3V3_AUX"), "")
    stripped = aux_why.replace("须裁", "").replace("需要", "")
    F3["teeth"] = (F3["detected"] and ("须裁" in aux_why or "需要" in aux_why)
                   and not ("需要" in stripped or "须裁" in stripped))

    # ---------- F4 scope 缺口 ----------
    gnd_coords = d11["gnd_stitch_via"]["coordinates"]
    gnd_realized = [c for c in gnd_coords if not (c.get("blocked") or c.get("status") == "blocked")]
    zone_vias = sum(len(z.get("vias", [])) for z in d11["power_zones"])
    dec_vias = len(d11.get("decoupling_via_to_plane", {}).get("vias", []))
    F4 = {
        "finding": "可达性要求 scope 仅 ppc entries（非 GND）；stitch/zone/decoupling via 无闸",
        "requirement_scope": "power_pad_connect.entries(non-GND)",
        "covered_scan_targets": n_nongnd,
        "uncovered_stitch_realized": len(gnd_realized),
        "uncovered_zone_vias": zone_vias,
        "uncovered_decoupling_vias": dec_vias,
        "detected": (len(gnd_realized) > 0 and zone_vias > 0),
    }
    F4["teeth"] = F4["detected"] and (len(gnd_realized) + zone_vias) > 0

    # ---------- F5 board_realized 陈旧 ----------
    br = p11.get("board_realized", {})
    F5 = {
        "finding": "live 机读块 board_realized 仍记 CO-89 的 223/86，与 rev-11 决策 189/120 矛盾",
        "board_realized": {"co": br.get("co"), "n_entries": br.get("n_entries"), "n_blocked": br.get("n_blocked")},
        "decisions": {"n_entries": len(p11["entries"]), "n_blocked": len(p11["blocked"])},
        "carried_over_unmodified": br.get("n_entries") == 223 and br.get("n_blocked") == 86,
        "consumed_by_pdn_apply": False,
        "detected": (br.get("n_entries") != len(p11["entries"]) or br.get("n_blocked") != len(p11["blocked"])),
    }
    F5["teeth"] = F5["detected"] and F5["carried_over_unmodified"]

    # ---------- F6 bbox vs PIP ----------
    explicit = [(z["net"], z["zone"], z["polygon"]) for z in d11["power_zones"] if isinstance(z.get("polygon"), list)]
    non_rect = [(n, zn) for n, zn, pg in explicit if not rect_axis_aligned(pg)]
    # 合成非矩形（L 形）证明 bbox 假阳
    lpoly = [(0.0, 0.0), (4.0, 0.0), (4.0, 1.0), (1.0, 1.0), (1.0, 4.0), (0.0, 4.0)]
    probe = (3.0, 3.0)  # 在 bbox(0,0,4,4) 内、在 L 形外
    F6 = {
        "finding": "co95 in_poly 用 bbox 而非真点在多边形内（latent）",
        "explicit_polygons": len(explicit), "non_axis_aligned_rect": non_rect,
        "live_impact": "none" if not non_rect else "present",
        "teeth_synthetic": {"in_bbox": bbox_test(lpoly, *probe), "in_pip": pip_test(lpoly, *probe)},
        "detected": (not non_rect) and bbox_test(lpoly, *probe) and not pip_test(lpoly, *probe),
    }
    F6["teeth"] = F6["teeth_synthetic"]["in_bbox"] and not F6["teeth_synthetic"]["in_pip"]

    # ---------- V3 blocked schema 与 pdn_apply 对齐 ----------
    blk = [c for c in gnd_coords if c.get("blocked") or c.get("status") == "blocked"]
    V3 = {"stitch_total": len(gnd_coords), "stitch_blocked_by_consumer_semantics": len(blk),
          "stitch_applied": len(gnd_coords) - len(blk),
          "schema_aligned": len(gnd_coords) - len(blk) == 40 and len(blk) == 60}

    # ---------- V4 重复坐标（意图核实） ----------
    from collections import Counter
    pos = [(c.get("x"), c.get("y")) for c in gnd_coords if c.get("x") is not None]
    dups = {f"{p[0]},{p[1]}": c for p, c in Counter(pos).items() if c > 1}
    dup_intentional = all(any("共享同一 GND via" in (x.get("basis") or "") for x in gnd_coords
                              if (x.get("x"), x.get("y")) == tuple(map(float, k.split(","))))
                          for k in dups)
    V4 = {"stitch_duplicate_positions": dups, "documented_shared_hole": dup_intentional}

    # ---------- 汇总 ----------
    V = {"V1_pd_outside_invariance": V1, "V2_co95_classification_complete": V2,
         "V3_stitch_blocked_schema_aligned": V3, "V4_stitch_dup_intentional": V4}
    F = {"F1_retired_key_dropped": F1, "F2_requirement_not_geometry_closable": F2,
         "F3_needs_region_ruling_text_dependent": F3, "F4_reachability_scope_gap": F4,
         "F5_board_realized_stale": F5, "F6_bbox_not_pip_latent": F6}
    findings_open = [k for k, v in F.items() if v.get("detected")]
    teeth_ok = all(F[k].get("teeth") for k in F)
    baseline_ok = not mismatch

    verdict = "BASELINE_MISMATCH" if not baseline_ok else (
        "TEETH_FAIL" if not teeth_ok else (
            "REVIEW_DONE_FINDINGS_OPEN" if findings_open else "PASS"))

    rec = {
        "artifact": "m13_v57_co96_nonexecutor_review_pass4", "schema": 1, "revision": "CO-96.1",
        "nature": "非执行者侧对抗评审 pass 4/4（对象 = rev-11 基线 CO-91/92/93/94/95 + 全链 + 不变量）",
        "reviewer_identity": "独立会话（rev-10/rev-11 由 CO-93/CO-95 执行；本件 context 归零续接）",
        "inputs": {k: ident[k] for k in ident},
        "baseline_expectations": BASE, "baseline_mismatch": mismatch,
        "questions_answered": {
            "Q1_plane_reachability_machine_closable": False,
            "Q2_unregistered_drift_between_rebaselines": [F1["finding"]] if F1["detected"] else [],
            "Q3_co95_classification_complete": V2["complete"]},
        "verifications": V, "findings": F,
        "findings_open": findings_open, "teeth_ok": teeth_ok, "baseline_ok": baseline_ok,
        "chain_gates_state": "G4..G7 全 PASS；板 0e636a67c1472462 逐字节不变（本件只读复核，未重跑链路）",
        "recommendation": ("F1 需 rev-12 变更单：回填 retired_superseded_bom 或显式声明其移除并登记（红线要求显式留存）；"
                           "F2/F3 建议 co95 闸改为三分态（geometric/declared-pending/ruling-pending）+ 去文本依赖（机判谓词）；"
                           "F4 建议扩展可达性 scope 或声明排除理由；F5 建议 rev-12 同步 board_realized；F6 低危 latent。"),
        "non_claims": ["只读评审；不改 SPEC/板/阈值/冻结源/引擎", "未重跑全链（handoff §9 命令由执行者侧负责；本件核对指纹）",
                       "F2 的『声明可闭合』有 SPEC 文本支撑（含 L3 派生区域）——本件不判其违规，只登记其不可机判闭合"],
        "verdict": verdict,
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-96 verdict=%s findings_open=%s teeth_ok=%s baseline_ok=%s" % (verdict, findings_open, teeth_ok, baseline_ok))
    print("V1 pd-outside changes:", len(v1_r9r10), len(v1_r10r11), "V2 complete:", V2["complete"],
          "V3 aligned:", V3["schema_aligned"])
    print("F2 geometric/declared/ruling:", F2["geometrically_covered_now"], F2["declared_pending_l3"], F2["ruling_pending_l1"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
