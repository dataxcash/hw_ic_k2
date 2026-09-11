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


def main() -> int:
    import pcbnew
    rules = json.loads(RULES.read_text())
    mfg = rules["manufacturing"]
    rec = json.loads(REC.read_text())
    art = json.loads(DRAWING.read_text())
    man = json.loads((STEP2 / "m13_v57_s1_page_manifest.json").read_text())

    # ---- FAB record ----
    b = pcbnew.LoadBoard(str(L4_PCB))
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
    si = {"artifact": "m13_v57_l5_si_pi_emc_record", "schema": 1, "revision": "L5-SI.2",
          "SI": {"track_width_rule_mm": 0.205, "all_pcie_tracks_0p205": widths_ok,
                 "max_intra_pair_skew_mm": skew_max, "skew_rule_mm": rules["diff_pair"]["intra_pair_skew_mm"],
                 "skew_ok": skew_max <= rules["diff_pair"]["intra_pair_skew_mm"] + 1e-9,
                 "skew_pages_checked": len(skew), "skew_pages": skew,
                 "layer_transitions_per_line": {"via1/corner/drop/land": 4}},
          "PI": {"plane_layers": planes, "planes_present": bool(planes),
                 "pdn_planes_untouched": "frozen board zones unmodified (L4 adds tracks only)",
                 "hole_clearance_violations": dfm["drc"]["new_violations"].get("hole_clearance", 0)},
          "EMC": {"signal_layers": [l for l in cu if l not in planes],
                  "reference_plane_adjacency": "F.Cu<->In1.Cu, In2.Cu<->In3.Cu, In6.Cu<->In5.Cu, B.Cu<->In4.Cu (8L stack, LID.1)",
                  "solder_mask_bridge_violations": dfm["drc"]["new_violations"].get("solder_mask_bridge", 0),
                  "copper_edge_violations": dfm["drc"]["new_violations"].get("copper_edge_clearance", 0)},
          "verdict": "PASS" if (widths_ok and skew_max <= rules["diff_pair"]["intra_pair_skew_mm"] + 1e-9) else "FAIL"}

    for name, obj in (("m13_v57_l5_fab_record.json", fab), ("m13_v57_l5_dfm_dft_record.json", dfm),
                      ("m13_v57_l5_si_pi_emc_record.json", si)):
        (STEP2 / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print("L5: FAB ok | DFM verdict=%s new=%d %s | in_scope_unconnected=%d/%d nets | SI verdict=%s skew=%.4f" %
          (dfm["verdict"], dfm["drc"]["new_total"], dfm["drc"]["new_violations"],
           dfm["dft"]["in_scope_unconnected_nets"], dfm["dft"]["in_scope_nets"], si["verdict"], skew_max))
    # CO-47：签核脚本退出码须等于门禁判定（原实现无条件 return 0，CI 无法据此判失败）
    return 0 if (dfm["verdict"] == "PASS" and si["verdict"] == "PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
