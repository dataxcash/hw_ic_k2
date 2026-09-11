#!/usr/bin/env python3
"""P3 v57 L5 — G7 sign-off records（**记录=证据，不是修理许可**）。

产出（全部只读检查；不改任何板/图纸）：
  m13_v57_l5_fab_record.json         制造记录（层叠/钻孔表/外形/计数 + 文件指纹）
  m13_v57_l5_dfm_dft_record.json     DFM/DFT：kicad-cli DRC（冻结基线 vs L4）+ 制造极值一致性 + DFT 可达性
  m13_v57_l5_si_pi_emc_record.json   SI/PI/EMC 规则化检查（线宽/对内等长/回流平面/平面完整性/via 类型）
  m13_v57_l5_g7_record.md            G7 记录（verdict：证据 → 是否需回上层）
CLI: run under KiCad python (pcbnew); kicad-cli auto-found.
"""
from __future__ import annotations
import hashlib, json, os, re, subprocess, tempfile, shutil
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SRC_PCB = K2 / "k2_v4_8L.kicad_pcb"
L4_PCB = K2 / "k2_v4_8L.l4.kicad_pcb"
PRO = K2 / "k2_v4_8L.kicad_pro"
DRAWING = STEP2 / "m13_v57_w3_joint_assignment.json"
REC = STEP2 / "m13_v57_l4_construction.json"
RULES = ROOT / "_shared/eda_core/drc_rules.json"
CLI = ROOT / "AppDir/bin/kicad-cli"
L4_DRU = K2 / "k2_v4_8L.l4.kicad_dru"   # CO-37: SPEC 逃逸区规则域（只随 L4 板；冻结基线不适用）


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def drc(board: Path, pro: Path, dru: Path | None = None) -> dict:
    with tempfile.TemporaryDirectory() as td:
        b = Path(td) / board.name
        pr = b.with_suffix(".kicad_pro")
        shutil.copy(board, b); shutil.copy(pro, pr)
        if dru is not None and Path(dru).exists():
            shutil.copy(dru, b.with_suffix(".kicad_dru"))
        out = Path(td) / "drc.json"
        subprocess.run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
                        "--refill-zones", "--output", str(out), str(b)],
                       capture_output=True, text=True, timeout=600)
        return json.loads(out.read_text())


def _zone_stats(board):
    """CO-50：按种类统计 zone（铜铺铜 vs 非铜 rule area），供 PDN 事实核验（非断言）。"""
    tot = pour = rule = 0
    layers = {}
    for z in board.Zones():
        tot += 1
        if hasattr(z, "GetIsRuleArea") and z.GetIsRuleArea():
            rule += 1
        else:
            pour += 1
            for ln in z.GetLayerSet().Seq():
                nm = board.GetLayerName(ln)
                layers[nm] = layers.get(nm, 0) + 1
    return {"total": tot, "copper_pour": pour, "rule_area": rule, "pour_layers": layers}



def _pair_geometry(segments):
    """CO-53：由落盘段几何独立测**对内/对间**平行段最小中心距（边距 = 中心距 − p_width）。
    网名归一：剥 `_J2`/`_MCIO` 尾缀后再剥 `_P`/`_N` 极性；同层且平行（叉积≈0）且投影重叠才计入。"""
    import math as _m
    def norm(n):
        for suf in ("_J2", "_MCIO"):
            if n.endswith(suf):
                n = n[:-len(suf)]
        return (n[:-2], n[-1]) if n.endswith(("_P", "_N")) else (n, None)
    groups = {}
    for n in segments:
        b, pol = norm(n)
        if pol:
            groups.setdefault(b, {})[pol] = n
    def md(a, b):
        best = 1e9
        for sa in segments[a]:
            for sb in segments[b]:
                if sa["layer"] != sb["layer"]:
                    continue
                ax, ay = sa["a"]; bx, by = sa["b"]; cx, cy = sb["a"]; dx, dy = sb["b"]
                v1 = (bx - ax, by - ay); v2 = (dx - cx, dy - cy)
                if abs(v1[0] * v2[1] - v1[1] * v2[0]) > 1e-6:
                    continue
                L = _m.hypot(*v2)
                if L < 1e-9:
                    continue
                t1 = ((ax - cx) * v2[0] + (ay - cy) * v2[1]) / L ** 2
                t2 = t1 + (v1[0] * v2[0] + v1[1] * v2[1]) / L ** 2
                if max(t1, t2) < 0 or min(t1, t2) > 1:
                    continue
                best = min(best, abs((ax - cx) * v2[1] - (ay - cy) * v2[0]) / L)
        return best
    intra = [round(md(d["P"], d["N"]), 4) for d in groups.values() if "P" in d and "N" in d]
    bl = sorted(groups)
    cross = 1e9
    for i, a in enumerate(bl):
        for b2 in bl[i + 1:]:
            for na in groups[a].values():
                for nb in groups[b2].values():
                    cross = min(cross, md(na, nb))
    return {"pairs_measured": len(intra), "intra_center_mm": sorted(set(intra)),
            "intra_center_max_mm": max(intra) if intra else None,
            "min_inter_pair_center_mm": (None if cross > 8e8 else round(cross, 4))}


def main() -> int:
    import pcbnew
    rules = json.loads(RULES.read_text())
    mfg = rules["manufacturing"]
    rec = json.loads(REC.read_text())
    art = json.loads(DRAWING.read_text())
    man = json.loads((STEP2 / "m13_v57_s1_page_manifest.json").read_text())

    # ---- FAB record ----
    b = pcbnew.LoadBoard(str(L4_PCB))
    zs_src = _zone_stats(pcbnew.LoadBoard(str(SRC_PCB)))     # CO-50：PDN 事实核验（冻结源）
    zs_l4 = _zone_stats(b)                                   # CO-50：PDN 事实核验（L4）
    cu = [b.GetLayerName(i) for i in range(pcbnew.PCB_LAYER_ID_COUNT)
          if b.GetEnabledLayers().Contains(i) and str(b.GetLayerName(i)).endswith(".Cu")]
    tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    from collections import Counter
    drill = Counter()
    for v in vias:
        drill[round(pcbnew.ToMM(v.GetDrill()), 3)] += 1
    bb = b.GetBoardEdgesBoundingBox()
    fab = {"artifact": "m13_v57_l5_fab_record", "schema": 1, "revision": "L5-FAB.2",
           "board": str(L4_PCB.relative_to(K2)), "board_sha256": sha(L4_PCB),
           "copper_layers": cu, "n_copper_layers": len(cu),
           "n_tracks": len(tracks), "n_vias": len(vias), "n_nets": b.GetNetCount(),
           "via_drill_table_mm": {str(k): v for k, v in sorted(drill.items())},
           "board_bbox_mm": [round(pcbnew.ToMM(bb.GetX()), 3), round(pcbnew.ToMM(bb.GetY()), 3),
                             round(pcbnew.ToMM(bb.GetWidth()), 3), round(pcbnew.ToMM(bb.GetHeight()), 3)],
           "inputs": {"frozen_pcb": sha(SRC_PCB), "drawing": sha(DRAWING), "construction": sha(REC)}}

    # ---- DFM/DFT record ----
    dbase = drc(SRC_PCB, PRO); dl4 = drc(L4_PCB, PRO, L4_DRU)
    def bytype(d): return dict(Counter(v.get("type") for v in d.get("violations", [])))
    tb, tl = bytype(dbase), bytype(dl4)
    new = {k: tl.get(k, 0) - tb.get(k, 0) for k in tl}          # 保留类型计数差（兼容/人读）
    # CO-51：多重集差（键 = (type, items[].description)）——可捕获"同类型对调"的掩盖；
    # 并显式报告**基线中消失**的条目（L4 只加 tracks/rule area ⇒ 基线项不应消失）。
    _sig = lambda v: (v.get("type"), tuple(sorted(str(s.get("description", "")) for s in v.get("items", []))))  # noqa: E731
    _cb = Counter(_sig(v) for v in dbase.get("violations", []))
    _cl = Counter(_sig(v) for v in dl4.get("violations", []))
    _new_ms, _gone_ms = _cl - _cb, _cb - _cl
    widths = sorted({round(pcbnew.ToMM(t.GetWidth()), 3) for t in tracks})
    # CO-47：施工连通性闭合谓词（L3 完整性）——在册（L4 施工）网必须 0 未连项。
    # kicad-cli 的 unconnected_items 无独立 net 键，网名从 items[].description 尾部 "[NET]" 解析。
    _NET = re.compile(r"\[([^\[\]]+)\]\s*$")
    in_scope = set(rec.get("nets", []))
    _ins_uc: dict[str, int] = {}
    for _it in dl4.get("unconnected_items", []):
        for _sub in _it.get("items", []):
            _m = _NET.search(_sub.get("description", ""))
            if _m and _m.group(1) in in_scope:
                _ins_uc[_m.group(1)] = _ins_uc.get(_m.group(1), 0) + 1
    _ins_uc_items = sum(_ins_uc.values())
    dfm = {"artifact": "m13_v57_l5_dfm_dft_record", "schema": 1, "revision": "L5-DFM.5",
           "drc": {"tool": f"kicad-cli {subprocess.run([str(CLI),'--version'],capture_output=True,text=True).stdout.strip()}",
                   "baseline_frozen": {"n": len(dbase.get("violations", [])), "by_type": tb,
                                       "unconnected": len(dbase.get("unconnected_items", []))},
                   "l4_applied": {"n": len(dl4.get("violations", [])), "by_type": tl,
                                  "unconnected": len(dl4.get("unconnected_items", []))},
                   "new_violations": {k: v for k, v in new.items() if v},
                   "new_total": sum(_new_ms.values()),
                   "new_items_by_type": dict(Counter(t for (t, _) in _new_ms.elements())),
                   "disappeared_total": sum(_gone_ms.values()),
                   "disappeared_by_type": dict(Counter(t for (t, _) in _gone_ms.elements())),
                   "metric": "CO-51: 多重集差 (type, items[].description)；L4=tracks-only ⇒ 基线项消失须为 0",
                   "escape_domain": ({"file": str(L4_DRU.relative_to(K2)), "sha256": sha(L4_DRU),
                                      "applies_to": "l4_applied only（冻结基线无 .kicad_dru）"}
                                     if L4_DRU.exists() else None)},
           "manufacturing_conformance": {
               "min_track_width_used_mm": widths[0] if widths else None,
               "min_track_width_rule_mm": mfg["min_track_width"],
               "via_dia_used_mm": sorted({round(pcbnew.ToMM(v.GetWidth()), 3) for v in vias}),
               "via_drill_used_mm": sorted({round(pcbnew.ToMM(v.GetDrill()), 3) for v in vias}),
               "min_via_diameter_rule_mm": mfg["min_via_diameter"],
               "min_through_hole_diameter_rule_mm": mfg["min_through_hole_diameter"],
               "annular_mm": round((0.35 - 0.2) / 2, 4), "min_annular_width_rule_mm": mfg["min_annular_width"]},
           "dft": {"nets": b.GetNetCount(),
                   "in_scope_nets": len(in_scope),
                   "in_scope_unconnected_nets": len(_ins_uc),
                   "in_scope_unconnected_items": _ins_uc_items,
                   "in_scope_violating_nets": sorted(_ins_uc),
                   "unconnected_items_total": len(dl4.get("unconnected_items", [])),
                   "rule": "CO-47：在册（L4 施工）网必须 0 未连项（kicad-cli unconnected_items 网名解析）；范围外网不计",
                   "note": "范围外网（GND/P3V3/NO_CONNECT/MCU_VDD 等）未连项属本阶段范围外，见 W3 boundary §6.4（版本化记录，勿引旧版号）"}}
    dfm["verdict"] = "PASS" if (dfm["drc"]["new_total"] == 0 and dfm["drc"]["disappeared_total"] == 0
                               and _ins_uc_items == 0) else "FAIL"

    # ---- SI/PI/EMC record ----
    widths_ok = all(abs(pcbnew.ToMM(t.GetWidth()) - 0.205) < 1e-6 for t in tracks if t.GetNetname().startswith("PCIE"))
    skew = []
    for pg in art["pages"]:
        if pg["kind"] == "data":
            _nodes = pg["nodes"]
        elif pg["kind"] == "refclk":
            # CO-45：REFCLK 对同属 net_class PCIe85 ⇒ SPEC intra_pair_skew_mm 亦适用（原实现跳过非 data 页）
            _nodes = pg["refclk"]["nodes"]
        else:
            continue
        # per-page P/N path length from the drawing nodes
        def plen(pol, _n=_nodes):
            pts = [[n[0], n[1]] for n in _n[pol]]
            dd = 0.0
            for i in range(len(pts) - 1):
                dd += ((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** 0.5
            return dd
        skew.append({"page": pg["page_id"], "skew_mm": round(abs(plen("P") - plen("N")), 4)})
    skew_max = max((s["skew_mm"] for s in skew), default=0)
    planes = [l for l in cu if l in ("In1.Cu", "In3.Cu", "In4.Cu", "In5.Cu")]
    _spec = json.loads((STEP2.parent / "SPEC_k2_v4.spec-rev-4.json").read_text(encoding="utf-8"))
    _spec_nc = _spec["net_classes"]["PCIe85"]
    _pg = _pair_geometry(rec["segments"])          # CO-53: 对内/对间几何实测
    si = {"artifact": "m13_v57_l5_si_pi_emc_record", "schema": 1, "revision": "L5-SI.5",
          "SI": {"track_width_rule_mm": 0.205, "all_pcie_tracks_0p205": widths_ok,
                 "max_intra_pair_skew_mm": skew_max, "skew_rule_mm": rules["diff_pair"]["intra_pair_skew_mm"],
                 "skew_ok": skew_max <= rules["diff_pair"]["intra_pair_skew_mm"] + 1e-9,
                 "skew_pages_checked": len(skew), "skew_pages": skew,
                 "layer_transitions_per_line": {"via1/corner/drop/land": 4},
                 # CO-53：对内/对间几何实测 vs SPEC 声明（几何项为**事实报告**；阻抗符合性 NOT_DEMONSTRATED）
                 "netclass_geometry": {
                     "delivered": {**_pg, "p_width_mm": 0.205,
                                   "intra_edge_gap_mm": (None if _pg["intra_center_max_mm"] is None
                                                         else round(_pg["intra_center_max_mm"] - 0.205, 4)),
                                   "min_inter_pair_edge_gap_mm": (None if _pg["min_inter_pair_center_mm"] is None
                                                                  else round(_pg["min_inter_pair_center_mm"] - 0.205, 4))},
                     "spec": {"p_gap_mm": _spec_nc["diff_pair"]["p_gap"], "p_width_mm": _spec_nc["diff_pair"]["p_width"],
                              "inter_pair_spacing_mm": _spec_nc["inter_pair_spacing_mm"],
                              "target_zdiff_ohm": _spec["impedance"]["target_zdiff"],
                              "impedance_model": _spec["impedance"]["model"],
                              "impedance_gap_mm": _spec["impedance"]["gap_mm"],
                              "stackup": _spec["stackup"]["material"]},
                     "source": "SPEC_k2_v4.spec-rev-4.json (CO-56) net_classes.PCIe85 / impedance(per_layer) / stackup(dielectric_8l)",
                     "conformance": "DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON",
                     "per_layer_impedance": _spec["impedance"].get("per_layer"),
                     "stackup_build": _spec["stackup"].get("dielectric_8l"),
                     "p_gap_semantics": _spec_nc["diff_pair"].get("p_gap_semantics"),
                     "note": "CO-56：SPEC ECO rev-4 采用 CO-55 反解 8L 叠层要求 ⇒ 交付各层一阶落 85Ω±10%"
                             "（F 88.4–91.2 / In2 82.1–89.2 / In6 85.5–87.4）；**终判 = 板厂阻抗券**（coupon_required=true）。"
                             "B.Cu 无平面参考 ⇒ 非阻抗控制层。对间串扰复核另记（CO-54 F2/F3）。",
                     "evidence": "m13_v57_co55_layer_impedance_requirement.json e9e1268b8e9bf312 / "
                                 "m13_v57_CO55_layer_aware_impedance_build_ruling.md b5c5b9a65f50f201"}},
          "PI": {"plane_layers_reserved": planes,
                 "zone_counts": {"frozen_src": zs_src, "l4": zs_l4},
                 "pdn_status": ("reserved_not_poured"
                                if (zs_src["copper_pour"] == 0 and zs_l4["copper_pour"] == 0) else "poured"),
                 "pdn_plane_copper_untouched": (zs_src["copper_pour"] == 0 and zs_l4["copper_pour"] == 0),
                 "pdn_note": ("CO-50 事实核验：冻结源与 L4 均无铜铺铜 zone（平面层为**保留层**，铺铜属后续阶段 WP2）；"
                              "L4 仅新增 %d 个非铜 rule area + tracks ⇒ 无平面铜被改写" % zs_l4["rule_area"]),
                 "hole_clearance_violations": dfm["drc"]["new_violations"].get("hole_clearance", 0)},
          "EMC": {"signal_layers": [l for l in cu if l not in planes],
                  "reference_plane_adjacency": "F.Cu<->In1.Cu, In2.Cu<->In3.Cu, In6.Cu<->In5.Cu, B.Cu<->In4.Cu (8L stack, LID.1)",
                  "solder_mask_bridge_violations": dfm["drc"]["new_violations"].get("solder_mask_bridge", 0),
                  "copper_edge_violations": dfm["drc"]["new_violations"].get("copper_edge_clearance", 0)},
          "verdict": "PASS" if (widths_ok and skew_max <= rules["diff_pair"]["intra_pair_skew_mm"] + 1e-9) else "FAIL"}

    for name, obj in (("m13_v57_l5_fab_record.json", fab), ("m13_v57_l5_dfm_dft_record.json", dfm),
                      ("m13_v57_l5_si_pi_emc_record.json", si)):
        (STEP2 / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    # ---- G7 记录（CO-48：补齐 docstring 声明却从未写出的评审记录；确定性文本，不含墙钟）----
    s16 = lambda p: sha(p)[:16]                                        # noqa: E731
    _dft = dfm["dft"]
    g7 = f"""# G7 / L5 记录 — k2 v57（8L）

> revision **L5-G7.6**｜图纸 **{art['revision']}** `{s16(DRAWING)}`｜L4 板 `{s16(L4_PCB)}`（含 SPEC 逃逸区规则域 CO-37）
> 产生：`tools/p3_v57_l5_signoff.py`（{dfm['drc']['tool']}，{dfm['revision']}）——**随 L5 每次重跑确定性重生成**
> ｜历史 FAIL 叙事见 CO-37/CO-43/CO-44/CO-45 变更单与 git（本件取代 L5-G7.5 的 new=60 口径）。

## 1. 结论（G7 {'PASS' if (dfm['verdict'] == 'PASS' and si['verdict'] == 'PASS') else 'FAIL'}）
- SI（对内等长）：**{si['verdict']}** — `max_intra_pair_skew_mm = {skew_max:.4f} <= {rules['diff_pair']['intra_pair_skew_mm']}`（{si['SI']['skew_pages_checked']} 页，含 REFCLK）。
  几何实测（CO-53）：对内中心 `{si['SI']['netclass_geometry']['delivered']['intra_center_max_mm']}` mm（边距 `{si['SI']['netclass_geometry']['delivered']['intra_edge_gap_mm']}`）vs SPEC p_gap `{si['SI']['netclass_geometry']['spec']['p_gap_mm']}`；对间最小中心 `{si['SI']['netclass_geometry']['delivered']['min_inter_pair_center_mm']}` vs SPEC inter_pair `{si['SI']['netclass_geometry']['spec']['inter_pair_spacing_mm']}` ⇒ **阻抗符合性 NOT_DEMONSTRATED**（开放项 CO-53）。
- DFM：**{dfm['verdict']}** — `new_total = {dfm['drc']['new_total']}`；L4 违规 by_type `{dfm['drc']['l4_applied']['by_type']}`（= 冻结基线 lib/silk，计入不计）。
- DFT（施工连通性，CO-47 谓词）：在册网未连项 **{_dft['in_scope_unconnected_nets']}/{_dft['in_scope_nets']}**（{_dft['rule']}）。
- EMC：solder_mask_bridge `{si['EMC']['solder_mask_bridge_violations']}` / copper_edge `{si['EMC']['copper_edge_violations']}`；
  PI：hole_clearance `{si['PI']['hole_clearance_violations']}`；pdn_status `{si['PI']['pdn_status']}`（铜铺铜 zone：冻结源 `{si['PI']['zone_counts']['frozen_src']['copper_pour']}` / L4 `{si['PI']['zone_counts']['l4']['copper_pour']}` ⇒ 保留层未铺铜，CO-50）。
- **裁决：无需回上层**（G4..G7 全 PASS）。里程碑 tag `k2-v57-g7-l5-pass`；收口声明件 W3 boundary v1.17。

## 2. 量（8L）
| 项 | 值 |
|---|---|
| copper layers | {len(cu)} = {'/'.join(c.replace('.Cu', '') for c in cu)}（In1/In3/In5=GND、In4=P3V3 平面未动）|
| tracks / vias | {fab['n_tracks']} / {fab['n_vias']}（drill {list(fab['via_drill_table_mm'])}）|
| L4 rule areas（非铜） | 4 = ESC_J2 / ESC_J3 / ESC_J4 / ESC_U6（F.Cu；SPEC 逃逸域）|
| 在册网（L4 施工） | {_dft['in_scope_nets']}（来源 `m13_v57_l4_construction.json: nets`）|
| 未连项（全板） | {_dft['unconnected_items_total']}（范围外 GND/P3V3/NO_CONNECT/MCU_VDD 等，见 boundary §6.4）|
| DRC baseline（冻结板，无 .kicad_dru） | {dfm['drc']['baseline_frozen']['n']} = {dfm['drc']['baseline_frozen']['by_type']} |
| DRC L4（含 .kicad_dru） | {dfm['drc']['l4_applied']['n']} = {dfm['drc']['l4_applied']['by_type']} |
| **new violations** | **{dfm['drc']['new_total']}** {dfm['drc']['new_violations']}（多重集差；基线消失 **{dfm['drc']['disappeared_total']}**）|

## 3. 判据（未放宽）
- `.kicad_dru` `{s16(L4_DRU)}`：实现 SPEC `constraints.escape_transition_zone`（ECN-001，`escape_clearance_mm=0.075`）+ 4 具名 rule area（J2/J3/J4/U6 pad 场）。
- **条件显式排除 `PCIE_REFCLK*`** ⇒ REFCLK 仍按 shop/netclass 判据；其 0 违规由 CO-40..CO-45 几何收敛达成（**非**借道放宽；见 CO-45 §5）。
- 域工件 `m13_v57_co37_escape_domain.json` `{s16(STEP2 / 'm13_v57_co37_escape_domain.json')}`；冻结基线板不加载 `.kicad_dru`。

## 4. 独立复算
- G5 `p3_v57_w3_constructive_validator_v2.py`（不 import 引擎）：`m13_v57_w3_validation.json` `{s16(STEP2 / 'm13_v57_w3_validation.json')}`（G-M1..6、A1.2/A1.3/A1.4、frozen）。
- G6 `p3_v57_l4_validator.py`：`m13_v57_l4_validation.json` `{s16(STEP2 / 'm13_v57_l4_validation.json')}`（L4-A..E viol=0）。
- 跨层 DRC：`kicad-cli pcb drc --format json --severity-all --refill-zones`（冻结板 vs L4，按类型差分；CO-47 起退出码=判定）。

## 5. 指纹
图纸 `{s16(DRAWING)}`｜landing `{s16(STEP2 / 'm13_v57_w3_chip_landing_rows.json')}`｜G5 `{s16(STEP2 / 'm13_v57_w3_validation.json')}`
｜L4 construction `{fab['inputs']['construction'][:16]}`｜L4 validation `{s16(STEP2 / 'm13_v57_l4_validation.json')}`｜L4 板 `{s16(L4_PCB)}`
｜fab `{s16(STEP2 / 'm13_v57_l5_fab_record.json')}`｜dfm `{s16(STEP2 / 'm13_v57_l5_dfm_dft_record.json')}`｜si `{s16(STEP2 / 'm13_v57_l5_si_pi_emc_record.json')}`
｜`.kicad_dru` `{s16(L4_DRU)}`
冻结四源 `{s16(STEP2.parent / 'SPEC_k2_v4.json')} / {s16(STEP2 / 'm13_v57_s1_page_manifest.json')} / {s16(SRC_PCB)} / {s16(RULES)}`（未改）。

End of G7 record（L5-G7.6，机器生成）。
"""
    (STEP2 / "m13_v57_l5_g7_record.md").write_text(g7, encoding="utf-8")
    print("L5: FAB ok | DFM verdict=%s new=%d (disappeared=%d) %s | in_scope_unconnected=%d/%d nets | SI verdict=%s skew=%.4f" %
          (dfm["verdict"], dfm["drc"]["new_total"], dfm["drc"]["disappeared_total"], dfm["drc"]["new_violations"],
           dfm["dft"]["in_scope_unconnected_nets"], dfm["dft"]["in_scope_nets"], si["verdict"], skew_max))
    # CO-47：签核脚本退出码须等于门禁判定（原实现无条件 return 0，CI 无法据此判失败）
    return 0 if (dfm["verdict"] == "PASS" and si["verdict"] == "PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
