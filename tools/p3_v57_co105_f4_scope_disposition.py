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
SPEC_CUR = L3 / "SPEC_k2_v4.spec-rev-18.json"
CO102P = K2 / "tools/p3_v57_co102_pdn_apply_local.py"
FROZEN = K2.parent / "_shared/eda_core/pdn_apply.py"
BASE = {"spec_current": "500f3da8179fe19c", "board": "a3ce9ab803045a0a"}


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
    # CO-132（rev-18）后：3 个 bridge zone 的几何义务已闭合（2 个 L3_DERIVED_DECLARED + 1 个 COVERED_BY_HOST_PLANE）
    # ⇒ 本项由「同桶 declared_pending_l3」改为「桶已清」断言；区分度由**历史 rev-17 正控**保住（见 teeth）。
    CLOSED_STATUS = ("L3_DERIVED_DECLARED", "COVERED_BY_HOST_PLANE")
    checks["V2_zone_vias_geometry_closed"] = {
        "ok": len(zv) == 17 and all(r["geometry_status"] in CLOSED_STATUS for r in zv),
        "n_zone_vias": len(zv), "n_in_empty_polygon_zone": n_no_geom,
        "closed_statuses": list(CLOSED_STATUS), "detail": zv,
        "note": "CO-132 已派生：P3V3_BCU_BRIDGE_IN4 / P3V3_AUX_BCU_BRIDGE_IN4 = L3_DERIVED_DECLARED；"
                "MCU_VDD_BCU_RESISTORS_IN4 = COVERED_BY_HOST_PLANE（CO-131）⇒ declared_pending_l3 桶已清"}
    hist = json.loads((L3 / "SPEC_k2_v4.spec-rev-17.json").read_text())["pd"]["zone_defs"]
    h_zv = [v for z in hist["power_zones"] for v in z.get("vias", [])
            if not (bool(z.get("polygons")) or bool(z.get("polygon")))]
    teeth["empty_geom_detector"] = (len(h_zv) == 17) and any(bool(z.get("polygon")) for z in hist["power_zones"])

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
    # CO-122b：原实现断言 ruling_pending_l1 == 6（把「当时状态」写死）。改为**更强**的交叉断言：
    #   SPEC `plane_reachability_status.unresolved` 的 pad 数 == co98 ruling_pending_l1，
    #   且**未决网均不已有显式 In4 多边形**（有则不属 L1 归属类，本闸即应报警）。
    _prs = json.loads(SPEC_CUR.read_text())["pd"]["zone_defs"]["plane_reachability_status"]
    _unr_nets = sorted(u["net"] for u in _prs["unresolved"])
    _unr_pads = sum(len(u["pads"]) for u in _prs["unresolved"])
    _in4_nets = sorted({z["net"] for z in zd["power_zones"] if isinstance(z.get("polygon"), list)})
    checks["V4_f3_r1_2_is_l1"] = {
        "ok": (co98["three_state"]["ruling_pending_l1"] == _unr_pads
               and all(n not in _in4_nets for n in _unr_nets)),
        "ruling_pending_l1": co98["three_state"]["ruling_pending_l1"],
        "declared_pending_l3": co98["three_state"]["declared_pending_l3"],
        "unresolved_nets": _unr_nets, "unresolved_pads": _unr_pads,
        "nets_with_in4_polygon": _in4_nets,
        "note": "ruling 项 = SPEC unresolved（根因=电源域/区域归属 ⇒ L1）；CO-122b 后 ② P3V3_AUX 由 L2 自裁闭合 ⇒ 余 12V_IN(3 pad)"}

    teeth["teeth_ok"] = all(v for k, v in teeth.items())
    mismatch = {k: {"expect": v, "actual": s16({"spec_current": SPEC_CUR, "board": K2 / "k2_v4_8L.l4.kicad_pcb"}[k])}
                for k, v in BASE.items() if s16({"spec_current": SPEC_CUR, "board": K2 / "k2_v4_8L.l4.kicad_pcb"}[k]) != v}
    rec = {"artifact": "m13_v57_co105_f4_scope_disposition", "schema": 1, "revision": "CO-105.1",
           "nature": "L2 自裁（PDN 建模）：CO-96 F4（可达性 requirement scope）落定 = 语义不可适用 + 几何待 L3（无需扩展动作）",
           "inputs": {"spec_current": s16(SPEC_CUR), "board": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
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
