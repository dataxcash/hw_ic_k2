#!/usr/bin/env python3
"""CO-54：SPEC ↔ 交付几何**机判漂移清单**（只读；回收 CO-53 未覆盖的字段）。

依据（非自创）：
  - handoff k2-v57-co53-impedance-open-20260912r.md §5 收口路径 (3)
    「复核走廊 PITCH = p_gap + 2·p_width + inter_pair_spacing（现 1.46 由 0.175 派生）」
  - CO-53 §3.3 同义要求；教训 ④「SPEC 字段与交付几何可能长期脱节 ⇒ 任何看起来合规的字段都要机判比对」
  - CO-53 本件亦记「对间最小平行中心 = 0.550 出现在连接器扇出密集区」⇒ 本工具对该归因做机判复核

本工具**只测量、只记录**：零几何改动、零阈值改动、不 bump SPEC、不预判门判定。
SPEC 消费 `SPEC_k2_v4.spec-rev-3.json`（引擎口径）；几何消费 `m13_v57_l4_construction.json`。

输出：m13_v57_co54_spec_delivery_audit.json
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-3.json"
REC = STEP2 / "m13_v57_l4_construction.json"
SHEET = STEP2 / "m13_v57_w3_joint_assignment.json"
OUT = STEP2 / "m13_v57_co54_spec_delivery_audit.json"

LONG_RUN_MM = 3.0          # 仅用于「交付网格」可视化，不参与最小距判定
OVL_EPS = 1e-12


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


# ── 几何：平行段最小中心距（与 tools/p3_v57_l5_signoff.py::_pair_geometry 同谓词，便于对账）──
def _norm(n: str) -> tuple[str, str | None]:
    for suf in ("_J2", "_MCIO"):
        if n.endswith(suf):
            n = n[:-len(suf)]
    return (n[:-2], n[-1]) if n.endswith(("_P", "_N")) else (n, None)


def _parallel(a: dict, b: dict) -> tuple[float, float] | None:
    """同层且平行（叉积≈0）且投影重叠 ⇒ (中心距, 重叠长度)；否则 None。"""
    if a["layer"] != b["layer"]:
        return None
    ax, ay = a["a"]; bx, by = a["b"]; cx, cy = b["a"]; dx, dy = b["b"]
    v1 = (bx - ax, by - ay); v2 = (dx - cx, dy - cy)
    if abs(v1[0] * v2[1] - v1[1] * v2[0]) > 1e-6:
        return None
    L = math.hypot(*v2)
    if L < 1e-9:
        return None
    t1 = ((ax - cx) * v2[0] + (ay - cy) * v2[1]) / L ** 2
    t2 = t1 + (v1[0] * v2[0] + v1[1] * v2[1]) / L ** 2
    ov = min(max(t1, t2), 1.0) - max(min(t1, t2), 0.0)
    if ov <= OVL_EPS:
        return None
    return abs((ax - cx) * v2[1] - (ay - cy) * v2[0]) / L, ov * L


def pairs_of(segs: dict) -> dict:
    g: dict = {}
    for n in segs:
        base, pol = _norm(n)
        if pol:
            g.setdefault(base, {})[pol] = n
    return {b: v for b, v in g.items() if "P" in v and "N" in v}


def min_parallel(segs: dict, na: str, nb: str) -> dict | None:
    best = None
    for sa in segs[na]:
        for sb in segs[nb]:
            r = _parallel(sa, sb)
            if r is None:
                continue
            if best is None or r[0] < best["center_mm"]:
                best = {"center_mm": round(r[0], 4), "overlap_mm": round(r[1], 3), "layer": sa["layer"],
                        "seg_a": [round(v, 3) for v in sa["a"] + sa["b"]],
                        "seg_b": [round(v, 3) for v in sb["a"] + sb["b"]]}
    return best


def intra_report(segs: dict, prs: dict) -> dict:
    """对内平行段中心距：全量实测（同对同层平行 + 投影重叠）。"""
    cnt: dict[float, int] = {}
    per_layer: dict[str, dict] = {}
    per_pair_min: list = []
    worst = None
    for base, g in prs.items():
        best = None
        for sa in segs[g["P"]]:
            for sb in segs[g["N"]]:
                r = _parallel(sa, sb)
                if r is None:
                    continue
                v = round(r[0], 3)
                cnt[v] = cnt.get(v, 0) + 1
                per_layer.setdefault(sa["layer"], {})
                per_layer[sa["layer"]][v] = per_layer[sa["layer"]].get(v, 0) + 1
                if best is None or r[0] < best["center_mm"]:
                    best = {"center_mm": round(r[0], 4), "overlap_mm": round(r[1], 3), "layer": sa["layer"],
                            "seg_a": [round(v2, 3) for v2 in sa["a"] + sa["b"]],
                            "seg_b": [round(v2, 3) for v2 in sb["a"] + sb["b"]]}
        if best is not None:
            per_pair_min.append(best["center_mm"])
            if worst is None or best["center_mm"] < worst["center_mm"] or (
                    best["center_mm"] == worst["center_mm"] and best["overlap_mm"] > worst["overlap_mm"]):
                worst = {**best, "nets": f'{g["P"]}|{g["N"]}'}
    vals = sorted(v for v in cnt if v <= 2.0)
    return {"pairs_measured": len(per_pair_min),
            "coupling_band_mm": [0.0, 2.0],
            "values_gt_2mm_count": sum(n for v, n in cnt.items() if v > 2.0),
            "per_pair_min_center_mm_unique": sorted(set(per_pair_min)),
            "values_mm_counts": {str(k): cnt[k] for k in vals},
            "min_center_mm": vals[0] if vals else None,
            "max_center_mm": vals[-1] if vals else None,
            "min_edge_gap_mm": round(vals[0] - 0.205, 4) if vals else None,
            "max_edge_gap_mm": round(vals[-1] - 0.205, 4) if vals else None,
            "per_layer_values_mm_counts": {k: {str(a): b for a, b in sorted(v.items()) if a <= 2.0}
                                           for k, v in sorted(per_layer.items())},
            "worst_min_center": worst}


def inter_report(segs: dict, prs: dict) -> dict:
    names = sorted(prs)
    per_layer: dict[str, float] = {}
    worst = None
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for na in prs[a].values():
                for nb in prs[b].values():
                    r = min_parallel(segs, na, nb)
                    if r is None:
                        continue
                    per_layer[r["layer"]] = min(per_layer.get(r["layer"], 1e9), r["center_mm"])
                    if worst is None or r["center_mm"] < worst["center_mm"] or (
                            r["center_mm"] == worst["center_mm"] and r["overlap_mm"] > worst["overlap_mm"]):
                        worst = {**r, "nets": f"{na}|{nb}", "pair_a": a, "pair_b": b}
    return {"min_center_mm": worst["center_mm"] if worst else None,
            "min_edge_gap_mm": round(worst["center_mm"] - 0.205, 4) if worst else None,
            "per_layer_min_center_mm": {k: round(v, 4) for k, v in sorted(per_layer.items())},
            "worst": worst}


def grid(segs: dict) -> dict:
    """交付网格：各层 |段长|≥3mm 的轴对齐走线坐标（事实可视化，非判据）。"""
    out: dict[str, dict] = {}
    for n, ss in segs.items():
        for s in ss:
            dx = abs(s["b"][0] - s["a"][0]); dy = abs(s["b"][1] - s["a"][1])
            ax = "vertical_x" if dx < 1e-6 else ("horizontal_y" if dy < 1e-6 else None)
            if ax is None:
                continue
            if math.hypot(dx, dy) < LONG_RUN_MM:
                continue
            out.setdefault(s["layer"], {}).setdefault(ax, []).append(round(s["a"][0] if ax == "vertical_x" else s["a"][1], 3))
    res = {}
    for layer, d in sorted(out.items()):
        e = {}
        for ax, vals in sorted(d.items()):
            cs = sorted(set(vals))
            diffs = sorted({round(cs[i + 1] - cs[i], 3) for i in range(len(cs) - 1)})
            e[ax] = {"coords_mm": cs, "spacings_mm": diffs}
        res[layer] = e
    return res


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    segs = json.loads(REC.read_text(encoding="utf-8"))["segments"]
    sheet = json.loads(SHEET.read_text(encoding="utf-8"))
    nc = spec["net_classes"]["PCIe85"]
    imp = spec["impedance"]
    prs = pairs_of(segs)
    intra = intra_report(segs, prs)
    inter = inter_report(segs, prs)

    spec_pitch = round(nc["diff_pair"]["p_gap"] + 2 * nc["diff_pair"]["p_width"] + nc["inter_pair_spacing_mm"], 4)
    bands = []
    for c in spec["corridors"]:
        for b in c["bands"]:
            ty = b.get("tracks_y", [])
            p = sorted({round(ty[i + 1] - ty[i], 4) for i in range(len(ty) - 1)})
            bands.append({"corridor": c["id"], "band": b["band"], "layer": b.get("layer"),
                          "pairs": b.get("pairs"), "tracks_y_pitch_mm": p})

    findings = [
        {"id": "F1", "class": "IMPEDANCE_GEOMETRY(intra-pair)",
         "spec": {"p_gap_mm": nc["diff_pair"]["p_gap"], "impedance_gap_mm": imp["gap_mm"]},
         "delivered": {"per_pair_min_center_mm_unique": intra["per_pair_min_center_mm_unique"],
                       "parallel_center_mm_counts": intra["values_mm_counts"],
                       "edge_gap_mm_min": intra["min_edge_gap_mm"], "edge_gap_mm_max": intra["max_edge_gap_mm"],
                       "per_layer": intra["per_layer_values_mm_counts"]},
         "delta": {"edge_gap_mm": round(intra["min_edge_gap_mm"] - nc["diff_pair"]["p_gap"], 4),
                   "direction": "wider_gap => lower_coupling => higher_Zdiff"},
         "judge": "L5-SI.4 netclass_geometry（CO-53 新增；下界另由 drc_semantic_core clearance 0.175 判）",
         "status": "OPEN"},
        {"id": "F2", "class": "CROSSTALK_GEOMETRY(inter-pair)",
         "spec": {"inter_pair_spacing_mm": nc["inter_pair_spacing_mm"]},
         "delivered": {"min_center_mm": inter["min_center_mm"], "min_edge_gap_mm": inter["min_edge_gap_mm"],
                       "per_layer_min_center_mm": inter["per_layer_min_center_mm"], "worst": inter["worst"]},
         "delta": {"edge_gap_mm": round(inter["min_edge_gap_mm"] - nc["inter_pair_spacing_mm"], 4)},
         "attribution_fix": ("CO-53 F2 记为「连接器扇出密集区」；机判证据显示最紧项为 "
                             f'{inter["worst"]["nets"]} @ {inter["worst"]["layer"]} '
                             f'(平行重叠 {inter["worst"]["overlap_mm"]}mm) ⇒ 归因更正为「内层长平行带」'),
         "judge": "无（inter_pair_spacing_mm 无门禁机判；本件为首个测量项）",
         "status": "OPEN"},
        {"id": "F3", "class": "SPEC_SELF_INCONSISTENCY(corridor pitch)",
         "spec": {"formula_pitch_mm": spec_pitch,
                  "corridors_tracks_y_pitch_mm": sorted({p for b in bands for p in b["tracks_y_pitch_mm"]}),
                  "formula": "p_gap + 2*p_width + inter_pair_spacing_mm"},
         "delta": {"mm": round(spec_pitch - min(p for b in bands for p in b["tracks_y_pitch_mm"]), 4)},
         "judge": "无（corridors.tracks_y 由引擎冻结折线消费，其与 net_classes 的一致性未机判）",
         "status": "OPEN"},
        {"id": "F4", "class": "MANUFACTURING_INPUT_GAP(stackup)",
         "spec": {"stackup_material": spec["stackup"]["material"]},
         "delivered": {"layers": 8, "stackup_definition_in_board": False,
                       "authority": "LID.1（F/In1(G)/In2(S)/In3(G)/In4(P)/In5(G)/In6(S)/B）"},
         "delta": {"layers": 2, "dielectric_table": "缺失(逐层介质厚度/材料)"},
         "judge": "无（板 (setup) 无 (stackup) 介质定义）",
         "status": "OPEN/BLOCKED_INPUT"},
        {"id": "F5", "class": "MODEL_INPUT_DRIFT(impedance basis)",
         "spec": {"model": imp["model"], "implied": "H1=5.0mil=0.127mm, Er1=4.3"},
         "repo_model": {"source": "_shared/eda_core/stackup.py:JLC_6L_16MM",
                        "F_Cu_h_mm": 0.1175, "er": 4.5,
                        "zdiff_at_0p205_0p175_ohm": 79.9},
         "jlc_official_prepreg_er": {"3313": 4.1, "2116": 4.16, "1080": 3.91, "7628": 4.4},
         "note": "三处「85Ω 基准」互不相同：SPEC 模型参数(H=0.127/Er=4.3)→85.1Ω；仓内 6L 叠构(H=0.1175/Er=4.5)→79.9Ω；JLC 官方 prepreg εr 与仓内注释(7628=4.6/2116=4.25/3313=4.05)亦不同",
         "judge": "无（impedance 符合性 coupon_required=true，属板厂券验证路径）",
         "status": "OPEN"},
        {"id": "F6", "class": "MODEL_LAYER_MISMATCH(impedance model applicability)",
         "spec": {"model": imp["model"], "kind": "microstrip(H1)，即 F.Cu 口径"},
         "delivered": {"intra_parallel_center_mm_counts": intra["per_layer_values_mm_counts"],
                       "note": "34 对中 32 对的决定性平行段在 In2/In6（带状线）；仅 REFCLK 2 对在 F.Cu 微带"},
         "note": "同一 p_width=0.205 同时标称 F.Cu 微带与 In2 带状线 85Ω（L2 v2.0「与 F.Cu 相同」），未经分层重导",
         "judge": "无",
         "status": "OPEN"},
        {"id": "F7", "class": "INTRA_GEOMETRY_NON_UNIFORM",
         "spec": {"p_gap_mm": nc["diff_pair"]["p_gap"], "field_count": 1},
         "delivered": {"intra_center_values_mm": intra["values_mm_counts"],
                       "basis": "In2 竖列网格 x∈[84.75..93.65]（对内 0.5 / 对间 1.2） vs x∈[53.2..65.2]（对内 0.6 / 对间 1.2）"},
         "judge": "L5-SI.4（报 min=0.5；0.6 未见单独判）",
         "status": "OPEN"},
    ]

    cover = [
        {"field": "net_classes.PCIe85.clearance=0.175", "judge": "drc_semantic_core + L4 DRC + W3 A-CN", "status": "JUDGED"},
        {"field": "net_classes.PCIe85.width/p_width=0.205", "judge": "L5-SI all_pcie_tracks_0p205", "status": "JUDGED"},
        {"field": "net_classes.PCIe85.intra_pair_skew_mm=0.15", "judge": "L5-SI max_intra_pair_skew (0.0031)", "status": "JUDGED"},
        {"field": "net_classes.PCIe85.diff_pair.p_gap=0.175(下界)", "judge": "drc_semantic_core clearance", "status": "JUDGED_LOWER_BOUND"},
        {"field": "net_classes.PCIe85.diff_pair.p_gap(上界/目标)", "judge": "L5-SI.4 netclass_geometry（CO-53 新增）", "status": "JUDGED_OPEN"},
        {"field": "net_classes.PCIe85.inter_pair_spacing_mm=0.875", "judge": "无（本件 CO-54 首次测量）", "status": "NOT_JUDGED"},
        {"field": "corridors.[].bands[].tracks_y 与 pitch 公式一致性", "judge": "无（本件 CO-54 首次测量）", "status": "NOT_JUDGED"},
        {"field": "impedance.{target_zdiff,model,width,gap}", "judge": "无（coupon_required=true，板厂券）", "status": "NOT_JUDGED"},
        {"field": "stackup.*", "judge": "无（板无 (stackup) 定义）", "status": "NOT_JUDGED"},
        {"field": "vias.* (drill/outer/annular/max_per_line/pad_edge_clearance)", "judge": "L4 validator via budget (CO-52) + FAB min 极值", "status": "JUDGED"},
        {"field": "constraints.edge_copper_min=0.3", "judge": "DFM copper_edge", "status": "JUDGED"},
        {"field": "constraints.escape_transition_zone(0.075/0.1025)", "judge": "引擎逃逸域 + L4 DRC", "status": "JUDGED"},
        {"field": "board.outline_x/outline_y", "judge": "L4 板框自检 (CO-03)", "status": "JUDGED"},
    ]

    rec = {
        "artifact": "m13_v57_co54_spec_delivery_audit", "schema": 1, "revision": "CO-54.1",
        "authority": "L2/SI（LAYOUT_CONSTITUTION 第二章）+ handoff §5(3) + CO-53 §3.3 + 教训 ④",
        "nature": "机判事实审计（只读）：零几何改动、零阈值改动、不 bump SPEC、不预判门判定",
        "inputs": {"spec": {"path": str(SPEC.relative_to(K2)), "sha16": sha16(SPEC)},
                   "l4_construction": {"path": str(REC.relative_to(K2)), "sha16": sha16(REC)},
                   "drawing": {"path": str(SHEET.relative_to(K2)), "sha16": sha16(SHEET)}},
        "spec_geometry": {"p_gap_mm": nc["diff_pair"]["p_gap"], "p_width_mm": nc["diff_pair"]["p_width"],
                          "inter_pair_spacing_mm": nc["inter_pair_spacing_mm"],
                          "intra_pair_skew_mm": nc["intra_pair_skew_mm"],
                          "impedance": imp, "stackup_material": spec["stackup"]["material"]},
        "delivered": {"intra_pair": intra, "inter_pair": inter, "grid": grid(segs)},
        "corridor_pitch": {"formula_from_net_classes_mm": spec_pitch, "spec_bands": bands},
        "findings": findings,
        "judge_coverage": cover,
        "conformance": "NOT_DEMONSTRATED",
        "gate_impact": "none（无几何/阈值改动；G4..G7 判定不变）",
        "open_item": "CO-53/CO-54（交付阻塞）：8L 介质叠层输入 → 分层 Zdiff 重导 → SPEC ECO rev-4 → 关项",
    }
    OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": sha16(OUT),
                      "intra_center_mm": intra["per_pair_min_center_mm_unique"], "intra_min_edge_mm": intra["min_edge_gap_mm"],
                      "inter_min_center_mm": inter["min_center_mm"], "inter_min_edge_mm": inter["min_edge_gap_mm"],
                      "worst_inter": inter["worst"]["nets"] + "@" + inter["worst"]["layer"],
                      "spec_formula_pitch_mm": spec_pitch,
                      "bands_pitch_mm": sorted({p for b in bands for p in b["tracks_y_pitch_mm"]}),
                      "findings": [f["id"] for f in findings]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
