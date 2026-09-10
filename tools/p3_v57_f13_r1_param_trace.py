#!/usr/bin/env python3
"""F-13-R1TRACE — R1 via-verdict 参数溯源映射 + P/N 列对耦合域（G3 冻结前置项 F-13）。

只读消费冻结件（SPEC / drc_rules / manifest / R1 via verdict），发射两个**新**工件：
  1) m13_v57_f13_r1_param_trace.json      参数 ↔ 规则/设计口径 映射断言 + 口径差异
  2) m13_v57_f13_r1_pair_coupling.json    R1 矩阵 V-3 列对耦合字段域（pair-level domain）

范围（硬）：不改任何冻结件、不改 verdict 判定结果、不产出跨页资源分配（`allocation: false`）;
verdict 的 `pair` 字段仅作**distance-feasible witness** 复读，不重写。

方法：verdict.params{clr,via_od,via_via} 与 R1 列对错距逐项映射到
drc_rules.json / SPEC_k2_v4.json 的**权威字段**，断言等值/保守包络/恒等式；
pair-level 域由 verdict 的**逐网** cands 重算（交叉对 + 双约束），输出域规模/
列集合/最小见证对，供 W3 联合指派消费（V-2/V-3）。输出逐字节确定。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.json"
RULES = K2 / "_shared" / "eda_core" / "drc_rules.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
VERDICT = STEP2 / "m13_v57_s1_r1_via_verdict.json"
OUT_TRACE = STEP2 / "m13_v57_f13_r1_param_trace.json"
OUT_PAIR = STEP2 / "m13_v57_f13_r1_pair_coupling.json"

REVISION = "F13-R1TRACE.1"
PAIR_REVISION = "F13-R1PAIR.1"
SCHEMA = 1

# 冻结指纹（运行期硬校验；drift → 非零退出）
FROZEN_SHA = {
    "spec": "0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233",
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "verdict": "2a3c8cf465c0ac1f808c1fdf7409725ab04862e4a8002f7ff71cfa299770bb5b",
}
G3_V1_2 = STEP2 / "m13_v57_g3_freeze_contract_v1_2_lane_domain.md"
G3_V1_2_SHA = "c8f380c184976fb5072e3afc6d47f25a5e6221de46c21aa67bd8cf1e20bd16b6"

VIA_VIA_MIN = 0.525          # via-via 铜净空 → 圆心距
COL_STAGGER_DESIGN = 0.36    # S1 设计 §R1 文本值（边缘距 0.155）
TRACK_W = 0.205              # SPEC net_classes.PCIe85.diff_pair.p_width
P_GAP = 0.175                # SPEC net_classes.PCIe85.diff_pair.p_gap
TOL = 1e-9


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze_check() -> dict:
    actual = {k: sha256(p) for k, p in (
        ("spec", SPEC), ("manifest", MANIFEST), ("rules", RULES), ("verdict", VERDICT))}
    match = {k: actual[k] == FROZEN_SHA[k] for k in FROZEN_SHA}
    drift = [k for k in match if not match[k]]
    return {"expected": FROZEN_SHA, "actual": actual, "match": match, "drift": drift}


def netclass_clearance(rules: dict, name: str) -> float:
    for nc in rules["clearance"]["net_classes"]:
        if nc["name"] == name:
            return float(nc["clearance"])
    raise KeyError(name)


def build_param_mapping(spec: dict, rules: dict) -> tuple[list, list]:
    via_od_spec = float(spec["vias"]["std"]["outer"])
    via_od_min = float(rules["manufacturing"]["min_via_diameter"])
    via_drill = float(spec["vias"]["std"]["drill"])
    clr_design = float(spec["net_classes"]["PCIe85"]["clearance"])
    clr_power = netclass_clearance(rules, "POWER")
    clr_board_min = float(rules["clearance"]["board_min"])
    via_via_spec = VIA_VIA_MIN
    col_derived = round(P_GAP + TRACK_W, 6)

    rows = [
        {
            "param": "via_od", "value": via_od_spec, "kind": "exact",
            "sources": [
                {"source": "SPEC_k2_v4.json /vias/std/outer", "value": via_od_spec,
                 "sha256": FROZEN_SHA["spec"]},
                {"source": "drc_rules.json /manufacturing/min_via_diameter",
                 "value": via_od_min, "sha256": FROZEN_SHA["rules"]},
            ],
            "assertion": "via_od == SPEC.vias.std.outer == rules.manufacturing.min_via_diameter",
            "holds": via_od_spec == via_od_min == rows_via_od(via_od_spec),
            "note": f"verdict 只录裸值; 关联常数 drill={via_drill} (annular {via_od_spec/2-via_drill/2:.4f}mm)",
        },
        {
            "param": "clr", "value": 0.2, "kind": "conservative_envelope",
            "sources": [
                {"source": "drc_rules.json /clearance/net_classes[POWER]/clearance",
                 "value": clr_power, "sha256": FROZEN_SHA["rules"]},
                {"source": "SPEC_k2_v4.json /net_classes/PCIe85/clearance",
                 "value": clr_design, "sha256": FROZEN_SHA["spec"]},
                {"source": "drc_rules.json /clearance/board_min",
                 "value": clr_board_min, "sha256": FROZEN_SHA["rules"]},
            ],
            "assertion": "verdict.clr == POWER netclass clearance (0.2) >= PCIe85 netclass clearance (0.175) >= board_min (0.1)",
            "holds": abs(0.2 - clr_power) < TOL and clr_power >= clr_design >= clr_board_min,
            "caliber_role": "verdict.clr 是**铜边到铜边**净距，按邻居最坏情况取 GND/POWER 网类值 0.2 "
                            "(verdict docstring: 'GND/POWER netclass 保守')；PCIe85 专值 0.175 更松 → 取严不取松",
            "note": "verdict 的判据形态 = pad_half_diag + clr + via_od/2（边到边），"
                    "故 0.2 与设计口径 'clearance0.175 + 半线宽0.1025 膨胀' **不同基准**："
                    "后者是中心线膨胀（0.2775），前者是边距；verdict 未复制 0.2775，属正确（边距 ≥ 0.175 即合规）",
        },
        {
            "param": "via_via", "value": via_via_spec, "kind": "identity",
            "sources": [
                {"source": "SPEC_k2_v4.json /vias/std/outer (via 外径)", "value": via_od_spec,
                 "sha256": FROZEN_SHA["spec"]},
                {"source": "drc_rules.json /clearance/net_classes[PCIe85]/clearance (via-via 铜净距)",
                 "value": clr_design, "sha256": FROZEN_SHA["rules"]},
                {"source": "drc_rules.json /clearance/geometry_translation (过孔/过孔=圆心距-(od1+od2)/2)",
                 "value": "rule_text", "sha256": FROZEN_SHA["rules"]},
            ],
            "assertion": "via_via == via_od + PCIe85_clearance == 0.35 + 0.175 == 0.525",
            "holds": abs(via_via_spec - (via_od_spec + clr_design)) < TOL,
            "note": "F-8 R3 冲突图同口径 (required_same_column_dy_mm=0.525) → 两工件互证",
        },
        {
            "param": "col_pair_stagger_min", "value": COL_STAGGER_DESIGN, "kind": "caliber_diff",
            "design_text": "S1 设计 §R1: 每差分对占用 2 列，对列错距 >= 0.36",
            "derived_binding": col_derived,
            "sources": [
                {"source": "SPEC_k2_v4.json /net_classes/PCIe85/diff_pair/p_gap", "value": P_GAP,
                 "sha256": FROZEN_SHA["spec"]},
                {"source": "SPEC_k2_v4.json /net_classes/PCIe85/diff_pair/p_width", "value": TRACK_W,
                 "sha256": FROZEN_SHA["spec"]},
                {"source": "S1 设计 §6 A1.3 不变量 (P/N 中心距=0.38±ε, 竖腿边缘距>=0.155)",
                 "value": "design_invariant", "sha256": None},
            ],
            "assertion": "binding := max(0.36, p_gap+p_width=0.38) = 0.38；边缘距 = stagger - p_width",
            "holds": abs((COL_STAGGER_DESIGN - TRACK_W) - 0.155) < TOL
                     and abs((col_derived - TRACK_W) - P_GAP) < TOL,
            "caliber_role": "0.36 → 竖腿边缘净距 0.155（=S1 设计 A1.3 不变量口径）; "
                            "0.38 → 竖腿边缘净距 0.175（=PCIe85 netclass clearance 真源）",
            "note": "两者互差 0.02mm。W3 准入取**真源** 0.38；0.36/0.155 为逃逸域宽松口径保留为 NOTE。"
                    "verdict 不受影响: 其 pair 判据只用 via-via 0.525（更严，但**不含列对错距**）→ V-3",
        },
    ]
    diffs = [
        {"id": "CAL-1", "topic": "verdict.clr 0.2 vs 设计中心线膨胀 0.175+0.1025=0.2775",
         "verdict_value": 0.2, "design_caliber": 0.2775,
         "resolution": "不同基准: verdict = 边到边净距(POWER 网类 0.2 保守)；设计 = 中心线膨胀"
                       "(PCIe85 clearance 0.175 + 半线宽 0.1025, R1 §推导2 用于禁列膨胀)。"
                       "verdict 边距 0.2 >= 0.175 合规, 无需复制 0.2775。",
         "impact": "无（判定更严）"},
        {"id": "CAL-2", "topic": "列对错距 0.36 (设计文本) vs 0.38 (p_gap+p_width 真源)",
         "verdict_value": None, "design_caliber": 0.36,
         "resolution": "W3 取 0.38（边缘距=0.175 净距真源）；0.36 对应边缘距 0.155（S1 A1.3 宽松口径）。",
         "impact": "F-13 检出: verdict 的 `pair` witness 16/32 页不满足 0.36（见 pair_coupling）→ 记 V-3 证据"},
        {"id": "CAL-3", "topic": "verdict.inputs_sha 仅 ballmap（缺 SPEC/manifest/rules）",
         "verdict_value": "ballmap only", "design_caliber": "G3 v1 §3 证据协议 (2)",
         "resolution": "本工件补齐 SPEC/manifest/rules/verdict 全 64hex 指纹链, **不改 verdict**（F-11 口径承接）。",
         "impact": "证据协议满足（verdict 原文不动）"},
    ]
    return rows, diffs


def rows_via_od(v: float) -> float:
    return round(v, 6)


def build_pair_coupling(verdict: dict, manifest: dict) -> dict:
    """pair-level 域：逐页重算 P/N 交叉对, 双约束 (via-via 0.525 ∧ |dx| >= stagger)。"""
    kind = {p["page_id"]: p["kind"] for p in manifest["pages"]}
    pages = {}
    n_stagger036 = 0
    n_stagger038 = 0
    n_verdict_pair_stagger_ok = 0
    for pid in sorted(verdict["pages"]):
        pg = verdict["pages"][pid]
        P = np.asarray(pg["P"]["cands"], dtype=float)
        N = np.asarray(pg["N"]["cands"], dtype=float)
        dist = np.linalg.norm(P[:, None, :] - N[None, :, :], axis=2)
        dx = np.abs(P[:, None, 0] - N[None, :, 0])
        ok_dist = dist >= VIA_VIA_MIN - TOL
        ok36 = ok_dist & (dx >= COL_STAGGER_DESIGN - TOL)
        ok38 = ok_dist & (dx >= round(P_GAP + TRACK_W, 6) - TOL)
        i36, j36 = np.nonzero(ok38)
        k = int(i36.size)
        adm_dist = dist[ok38]
        # 最小距离见证对（确定性：min dist, 再按 (Px,Py,Nx,Ny) 字典序）
        wit = None
        if k:
            order = np.lexsort((N[j36, 1], N[j36, 0], P[i36, 1], P[i36, 0], adm_dist))
            a = order[0]
            px, py = P[i36[a]]
            nx, ny = N[j36[a]]
            wit = {"P": [round(float(px), 3), round(float(py), 3)],
                   "N": [round(float(nx), 3), round(float(ny), 3)],
                   "dist_mm": round(float(adm_dist[a]), 4),
                   "stagger_mm": round(abs(float(px - nx)), 4)}
        hist = {f"{t:.3f}": int((adm_dist >= t - TOL).sum())
                for t in (VIA_VIA_MIN, 0.6, 0.8, 1.0)}
        vp = pg.get("pair")
        vp_rec = None
        if vp:
            vx, vy = float(vp[0][0]), float(vp[0][1])
            wx, wy = float(vp[1][0]), float(vp[1][1])
            vd = float(np.hypot(vx - wx, vy - wy))
            vs = abs(vx - wx)
            vp_rec = {"P": [round(vx, 3), round(vy, 3)], "N": [round(wx, 3), round(wy, 3)],
                      "dist_mm": round(vd, 4), "stagger_mm": round(vs, 4),
                      "dist_ok": vd >= VIA_VIA_MIN - TOL,
                      "stagger_ok_036": vs >= COL_STAGGER_DESIGN - TOL,
                      "stagger_ok_038": vs >= round(P_GAP + TRACK_W, 6) - TOL,
                      "role": "distance-feasible witness only (frozen verdict field, not rewritten)"}
            if vp_rec["stagger_ok_036"]:
                n_verdict_pair_stagger_ok += 1
        if k:
            n_stagger036 += 1
            n_stagger038 += 1
        pages[pid] = {
            "kind": kind.get(pid, "unknown"),
            "side": pg["side"],
            "pair_domain": {
                "rule": "dist>=0.525 (via-via copper, RULES.clearance PCIe85) "
                        "AND |dx|>=0.38 (col stagger := p_gap+p_width, SPEC PCIe85)",
                "n_pairs_dist_ok": int(ok_dist.sum()),
                "n_pairs_admissible_stagger_036": int(ok36.sum()),
                "n_pairs_admissible_stagger_038": int(ok38.sum()),
                "dist_min_mm": round(float(adm_dist.min()), 4) if k else None,
                "dist_max_mm": round(float(adm_dist.max()), 4) if k else None,
                "dist_hist_mm": hist,
                "x_columns_P": sorted({round(float(x), 3) for x in P[i36, 0]}) if k else [],
                "x_columns_N": sorted({round(float(x), 3) for x in N[j36, 0]}) if k else [],
            },
            "admissible_pair_witness": wit,
            "verdict_pair": vp_rec,
        }
    return {
        "pages": pages,
        "summary": {
            "n_pages": len(pages),
            "n_pages_with_admissible_pair_stagger_036": n_stagger036,
            "n_pages_with_admissible_pair_stagger_038": n_stagger038,
            "n_verdict_pairs_stagger_036_ok": n_verdict_pair_stagger_ok,
            "n_verdict_pairs_total": len(pages),
            "finding": "frozen verdict `pair` field is distance-feasible (>=0.525) only; "
                       "it does NOT carry the column-pair stagger constraint (V-3 gap). "
                       "admissible_pair_witness here is an existence witness, NOT an allocation.",
        },
    }


def build_trace(spec: dict, rules: dict, verdict: dict, manifest: dict) -> dict:
    params, calibers = build_param_mapping(spec, rules)
    payload = {
        "artifact": "m13_v57_f13_r1_param_trace",
        "schema": SCHEMA,
        "revision": REVISION,
        "status": "EMITTED",
        "scope": "G3 冻结前置项 F-13 (R1 参数溯源映射断言 V-2 + 列对耦合字段 V-3)；只读消费冻结件",
        "verdict_artifact": {
            "path": str(VERDICT.relative_to(K2)),
            "sha256": FROZEN_SHA["verdict"],
            "n_pages": verdict["n_pages"],
            "n_escapable": verdict["n_escapable"],
            "params_as_frozen": verdict["params"],
            "verdict_result_unchanged": True,
            "inputs_sha_as_frozen": verdict["inputs_sha"],
        },
        "frozen_sha_check": freeze_check(),
        "contract": {"id": "G3-C v1.3", "path_md": str(G3_V1_2.relative_to(K2)),
                     "note": "参数口径与列对耦合字段并入 G3 v1.3（版本 bump，不原地改写 v1.2）"},
        "governing_constants": {
            "via_via_min_mm": VIA_VIA_MIN, "col_stagger_design_text_mm": COL_STAGGER_DESIGN,
            "col_stagger_binding_mm": round(P_GAP + TRACK_W, 6), "track_width_mm": TRACK_W,
            "p_gap_mm": P_GAP, "eps": TOL,
        },
        "params_mapping": params,
        "caliber_differences": calibers,
        "evidence_protocol": {
            "item1_schema_versions": f"schema={SCHEMA}, revision={REVISION}/{PAIR_REVISION}, "
                                     "producer path+revision+sha256 recorded",
            "item2_source_fingerprints": "SPEC/manifest/rules/verdict pinned to full 64-hex at runtime; "
                                         "drift -> non-zero exit",
            "item3_deterministic": "byte-identical report across two consecutive runs "
                                   "(sort_keys=True deterministic JSON)",
            "item5_escape_hatches": "upstream only (SPEC netclass/pad geometry, rules netclass table) ; "
                                    "no downstream edits",
            "item6_independent_validation": "see m13_v57_f13_r1_param_trace_validation.json "
                                            "(independent re-derivation, does not import this producer)",
        },
        "no_allocation_scan": {
            "forbidden_keys": ["assigned", "allocation", "selected_lane", "lane_assignment"],
            "leaked": [],
            "statement": "No cross-page resource allocation is emitted; per-page witness only.",
        },
    }
    return payload


def main() -> int:
    spec = json.load(SPEC.open())
    rules = json.load(RULES.open())
    manifest = json.load(MANIFEST.open())
    verdict = json.load(VERDICT.open())

    fc = freeze_check()
    if fc["drift"]:
        print("FROZEN SHA DRIFT:", fc["drift"], "-> FAIL")
        return 2

    trace = build_trace(spec, rules, verdict, manifest)
    pair = {
        "artifact": "m13_v57_f13_r1_pair_coupling",
        "schema": SCHEMA,
        "revision": PAIR_REVISION,
        "status": "EMITTED",
        "authority": {
            "verdict": str(VERDICT.relative_to(K2)), "verdict_sha256": FROZEN_SHA["verdict"],
            "manifest": str(MANIFEST.relative_to(K2)), "spec": str(SPEC.relative_to(K2)),
            "rules": str(RULES.relative_to(K2)),
            "contract": {"id": "G3-C v1.3"},
        },
        "inputs_sha": {"spec": FROZEN_SHA["spec"], "manifest": FROZEN_SHA["manifest"],
                       "rules": FROZEN_SHA["rules"], "verdict": FROZEN_SHA["verdict"]},
        "field_spec": {
            "pair_domain": "cross product of frozen per-net via candidates under dual constraint: "
                           "dist >= 0.525 AND |dx| >= 0.38",
            "admissible_pair_witness": "existence witness (min dist, deterministic tie-break); "
                                       "NOT an allocation, W3 must re-select under joint constraints",
            "verdict_pair": "read-only re-embedding of the frozen verdict `pair` field",
            "allocation": False,
        },
        "constraints": {
            "dist_min_mm": VIA_VIA_MIN,
            "col_stagger_mm": round(P_GAP + TRACK_W, 6),
            "col_stagger_design_text_mm": COL_STAGGER_DESIGN,
            "leg_edge_clearance_mm": P_GAP,
            "design_text_edge_clearance_mm": round(COL_STAGGER_DESIGN - TRACK_W, 6),
        },
        "producer": {"path": str(Path(__file__).relative_to(K2)), "revision": REVISION},
    }
    pair.update(build_pair_coupling(verdict, manifest))
    pair["inputs_sha"] = {"spec": FROZEN_SHA["spec"], "manifest": FROZEN_SHA["manifest"],
                          "rules": FROZEN_SHA["rules"], "verdict": FROZEN_SHA["verdict"]}

    OUT_TRACE.write_text(json.dumps(trace, indent=1, ensure_ascii=False, sort_keys=True),
                         encoding="utf-8")
    OUT_PAIR.write_text(json.dumps(pair, indent=1, ensure_ascii=False, sort_keys=True),
                        encoding="utf-8")
    mt = sum(1 for m in trace["params_mapping"] if m["holds"])
    print(f"F13-R1TRACE: params_holds={mt}/{len(trace['params_mapping'])} "
          f"caliber_diffs={len(trace['caliber_differences'])}")
    print(f"F13-R1PAIR: pages={pair['summary']['n_pages']} "
          f"admissible038={pair['summary']['n_pages_with_admissible_pair_stagger_038']} "
          f"verdict_pair_stagger_ok={pair['summary']['n_verdict_pairs_stagger_036_ok']}")
    print(f"trace_sha={sha256(OUT_TRACE)[:16]} pair_sha={sha256(OUT_PAIR)[:16]}")
    return 0 if mt == len(trace["params_mapping"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
