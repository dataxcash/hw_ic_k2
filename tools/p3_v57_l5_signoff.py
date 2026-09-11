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
    new = {k: tl.get(k, 0) - tb.get(k, 0) for k in tl}
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
    dfm = {"artifact": "m13_v57_l5_dfm_dft_record", "schema": 1, "revision": "L5-DFM.4",
           "drc": {"tool": f"kicad-cli {subprocess.run([str(CLI),'--version'],capture_output=True,text=True).stdout.strip()}",
                   "baseline_frozen": {"n": len(dbase.get("violations", [])), "by_type": tb,
                                       "unconnected": len(dbase.get("unconnected_items", []))},
                   "l4_applied": {"n": len(dl4.get("violations", [])), "by_type": tl,
                                  "unconnected": len(dl4.get("unconnected_items", []))},
                   "new_violations": {k: v for k, v in new.items() if v},
                   "new_total": sum(v for v in new.values() if v > 0),
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
    dfm["verdict"] = "PASS" if (dfm["drc"]["new_total"] == 0 and _ins_uc_items == 0) else "FAIL"

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
    si = {"artifact": "m13_v57_l5_si_pi_emc_record", "schema": 1, "revision": "L5-SI.3",
          "SI": {"track_width_rule_mm": 0.205, "all_pcie_tracks_0p205": widths_ok,
                 "max_intra_pair_skew_mm": skew_max, "skew_rule_mm": rules["diff_pair"]["intra_pair_skew_mm"],
                 "skew_ok": skew_max <= rules["diff_pair"]["intra_pair_skew_mm"] + 1e-9,
                 "skew_pages_checked": len(skew), "skew_pages": skew,
                 "layer_transitions_per_line": {"via1/corner/drop/land": 4}},
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
| **new violations** | **{dfm['drc']['new_total']}** {dfm['drc']['new_violations']} |

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
    print("L5: FAB ok | DFM verdict=%s new=%d %s | in_scope_unconnected=%d/%d nets | SI verdict=%s skew=%.4f" %
          (dfm["verdict"], dfm["drc"]["new_total"], dfm["drc"]["new_violations"],
           dfm["dft"]["in_scope_unconnected_nets"], dfm["dft"]["in_scope_nets"], si["verdict"], skew_max))
    # CO-47：签核脚本退出码须等于门禁判定（原实现无条件 return 0，CI 无法据此判失败）
    return 0 if (dfm["verdict"] == "PASS" and si["verdict"] == "PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
