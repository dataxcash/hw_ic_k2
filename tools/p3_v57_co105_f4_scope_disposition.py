#!/usr/bin/env python3
"""CO-105：【L2 自裁 · PDN 建模】CO-96 F4 的**落定**（可达性 requirement 的 scope 排除 = 语义不可适用 + 几何待 L3）。

CO-96 F4（中）指出 `plane_reachability_requirement` 仅覆盖 ppc 非 GND entry（55），而
`gnd_stitch_via_realized`(40) / `power_zones[].vias`(17) 无闸；CO-98 以「声明排除」处置。本件把该处置**机判化**并落定：

  (i) **语义不可适用**：requirement 判据是「via 是否落在**本网 In4 铜**内」。GND 的平面是 **In1/In3/In6**（板/SPEC 均无 In4 GND 区）
      ⇒ 对 GND 对象（130 ppc entry + 40 stitch via）该判据**不成立**（不是「未覆盖」，而是无可判定）；
  (ii) **几何待 L3 派生**：17 个 `power_zones[].vias` 全部位于 3 个 **bridge zone**，其 `polygons=[]`（几何未建、
      `geometry_status=L3_CONSTRUCTION_DERIVED`）⇒ 与 CO-98 的 `declared_pending_l3` **同桶**，
      扩大 scope 只会把这 17 项并入待派生清单，不会新增可判缺陷；
  (iii) `gnd_stitch_gen` 生成端缺陷**不在在役路径**（施工只读 SPEC `gnd_stitch_via.coordinates`，rev-12 已由 CO-101 声明重放）；
  (iv) F3 的 `R1.2` 判据根因为**电源域/区域归属**= L1（不在本件范围）。

⇒ F4 **不需 scope 扩展动作**；L2 登记余项中 F4 关闭。CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co105_f4_scope_disposition.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC_CUR = L3 / "SPEC_k2_v4.spec-rev-13.json"
CO102P = K2 / "tools/p3_v57_co102_pdn_apply_local.py"
FROZEN = K2.parent / "_shared/eda_core/pdn_apply.py"
BASE = {"spec_rev13": "7943be727a4f8ef9", "board": "0e636a67c1472462"}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(STEP2 / "m13_v57_co105_f4_scope_disposition.json"))
    a = ap.parse_args(argv)
    zd = json.loads(SPEC_CUR.read_text())["pd"]["zone_defs"]
    checks, teeth = {}, {}

    # ---------- V1：GND 无 In4 平面 ⇒ 语义不可适用 ----------
    gnd_layers = sorted({g["layer"] for g in zd.get("gnd_planes", []) if g["net"] == "GND"})
    in4_nets = sorted({z["net"] for z in zd["power_zones"] if z.get("layer") == "In4.Cu"})
    e_nets = {}
    for e in zd["power_pad_connect"]["entries"]:
        e_nets[e["net"]] = e_nets.get(e["net"], 0) + 1
    gnd_ppc = e_nets.get("GND", 0)
    non_gnd_ppc = sum(v for k, v in e_nets.items() if k != "GND")
    stitch = sum(1 for c in zd["gnd_stitch_via"]["coordinates"] if isinstance(c.get("x"), (int, float)))
    checks["V1_gnd_has_no_in4_plane"] = {
        "ok": "In4.Cu" not in gnd_layers and "GND" not in in4_nets and non_gnd_ppc == 55,
        "gnd_plane_layers": gnd_layers, "in4_nets": in4_nets,
        "semantically_out_of_scope": {"gnd_ppc_entries": gnd_ppc, "gnd_stitch_realized": stitch},
        "requirement_object": {"non_gnd_ppc_entries": non_gnd_ppc},
        "note": "判据=「落于本网 In4 铜」，GND 无 In4 区 ⇒ 对 GND 对象无可判定（非『未覆盖』）"}
    teeth["gnd_in4_detector"] = ("In4.Cu" not in gnd_layers) and ("In4.Cu" in [z.get("layer") for z in zd["power_zones"]])

    # ---------- V2：17 个 zone vias 全在几何未建的 bridge zone（与 declared_pending_l3 同桶） ----------
    zv = []
    for z in zd["power_zones"]:
        pol = z.get("polygons")
        has_geom = bool(pol) or bool(z.get("polygon"))
        for v in z.get("vias", []):
            zv.append({"net": z["net"], "zone": z.get("zone"), "pos": v["pos"],
                       "zone_has_derived_geometry": has_geom,
                       "geometry_status": z.get("geometry_status")})
    n_no_geom = sum(1 for r in zv if not r["zone_has_derived_geometry"])
    checks["V2_zone_vias_pending_l3"] = {
        "ok": len(zv) == 17 and n_no_geom == 17 and all(
            r["geometry_status"] == "L3_CONSTRUCTION_DERIVED" for r in zv),
        "n_zone_vias": len(zv), "n_in_empty_polygon_zone": n_no_geom,
        "detail": zv,
        "note": "3 个 bridge zone（P3V3_BCU_BRIDGE_IN4 / P3V3_AUX_BCU_BRIDGE_IN4 / MCU_VDD_BCU_RESISTORS_IN4）polygons=[] ⇒ 与 CO-98 declared_pending_l3 同桶"}
    teeth["empty_geom_detector"] = (n_no_geom == 17) and any(
        bool(z.get("polygon")) for z in zd["power_zones"])   # 有几何的 zone 存在 ⇒ 检测器有区分度

    # ---------- V3：gnd_stitch_gen 不在在役路径 ----------
    import re
    txt = CO102P.read_text() + FROZEN.read_text()
    # 只算**代码引用**（import / 调用），散文提及（docstring 复盘）不算在役路径
    refs = len(re.findall(r"(import\s+\S*gnd_stitch_gen|gnd_stitch_gen\s*\.\s*\w+|from\s+\S*gnd_stitch_gen)", txt))
    prose = txt.count("gnd_stitch_gen")
    cm = zd["gnd_stitch_via"].get("candidate_method")
    checks["V3_gnd_stitch_gen_not_in_path"] = {
        "ok": refs == 0 and cm is not None,
        "gnd_stitch_gen_code_refs_in_apply_path": refs,
        "gnd_stitch_gen_prose_mentions": prose,
        "spec_candidate_method": cm,
        "retired_ledger_present": "retired_superseded_mutual_conflict_v1" in zd["gnd_stitch_via"],
        "note": "施工只读 SPEC `gnd_stitch_via.coordinates`（rev-12 由 CO-101 声明 palette 重放）⇒ 生成端缺陷为 latent，若重生成须同批修"}

    # ---------- V4：F3 R1.2 根因属 L1 ----------
    co98 = json.loads((STEP2 / "m13_v57_co98_reachability_status_report.json").read_text())
    checks["V4_f3_r1_2_is_l1"] = {
        "ok": co98["three_state"]["ruling_pending_l1"] == 6,
        "ruling_pending_l1": co98["three_state"]["ruling_pending_l1"],
        "declared_pending_l3": co98["three_state"]["declared_pending_l3"],
        "note": "6 项 ruling 中 R1.2 依赖自由文本（CO-96 F3），其根因=电源域/区域归属 ⇒ L1（不在本件）"}

    teeth["teeth_ok"] = all(v for k, v in teeth.items())
    mismatch = {k: {"expect": v, "actual": s16({"spec_rev13": SPEC_CUR, "board": K2 / "k2_v4_8L.l4.kicad_pcb"}[k])}
                for k, v in BASE.items() if s16({"spec_rev13": SPEC_CUR, "board": K2 / "k2_v4_8L.l4.kicad_pcb"}[k]) != v}
    rec = {"artifact": "m13_v57_co105_f4_scope_disposition", "schema": 1, "revision": "CO-105.1",
           "nature": "L2 自裁（PDN 建模）：CO-96 F4（可达性 requirement scope）落定 = 语义不可适用 + 几何待 L3（无需扩展动作）",
           "inputs": {"spec_rev13": s16(SPEC_CUR), "board": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
                      "co98_record": s16(STEP2 / "m13_v57_co98_reachability_status_report.json")},
           "base_pins": BASE, "pin_mismatch": mismatch, "checks": checks, "teeth": teeth,
           "DISPOSITION": {"item": "CO-96 F4（可达性 scope 缺口，严重度=中）", "decision": "CLOSE_NO_SCOPE_EXTENSION",
                           "basis": "(i) GND 无 In4 平面 ⇒ 对 130 ppc + 40 stitch 语义不可适用；"
                                    "(ii) 17 zone vias 全在 polygons=[] 的 bridge zone ⇒ 与 declared_pending_l3 同桶，"
                                    "扩 scope 只并入待派生清单、不新增可判缺陷；(iii) 生成端 latent 不在在役路径；(iv) F3/R1.2 根因属 L1",
                           "effects": "零 SPEC/板/阈值/冻结源改动；不需重基线；不需新复评（本件为 L2 自裁、非几何变更）",
                           "open_after": "L1 三项（12V_IN 承载 / P3V3_AUX 西区归属 / L1① 0.875）＋外部输入（PM 压降·热 / 板厂券）"}}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-105 disposition=%s | checks ok=%s | teeth_ok=%s" % (
        rec["DISPOSITION"]["decision"], [v["ok"] for v in checks.values()], teeth["teeth_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
