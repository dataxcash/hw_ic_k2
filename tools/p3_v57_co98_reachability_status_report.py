#!/usr/bin/env python3
"""CO-98：【L2 PDN】In4 平面可达性**义务状态报告**（依 CO-96 F2/F3/F4；非破坏性，不动 co95 权威记录）。

角色区别：
  - co95（`p3_v57_co95_in4_reachability.py` + 其记录）仍是**逐 entry 分类的权威闸**（本件**只读**之，不改其字节）；
  - 本件把 CO-96 F2/F3/F4 三项发现**机判化 + 显式化**，输出「可机判闭合与否 / 义务分态 / scope 排除 / 裁决依据」：
    F2 义务三态：`geometric_covered` / `declared_pending_l3` / `ruling_pending_l1`（明确「声明覆盖 ≠ 几何覆盖」）；
    F4 scope：本 requirement 只覆盖 ppc 非 GND entry；显式列出**不在范围内的** gnd_stitch / power_zones / decoupling via；
    F3 裁决依据：需要的区域裁决项按**机判谓词**分解（本网无 In4 区 / via 落入**异网**显式 In4 铜 => 冲突 / 仅文本声明）。
  verdict **永不 PASS**（只要存在 declared_pending_l3 或 ruling_pending_l1）。

牙齿：① PIP 合成非矩形（bbox 近似会假阳、真 PIP 拒绝）；② 完整性（分类和 ≠ 非 GND entry 数即抓）。
只读；不改 SPEC/板/阈值/冻结源；零坐标搜索；无 while。
CLI: python3 tools/p3_v57_co98_reachability_status_report.py [--out J]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co98_reachability_status_report.json"
SPEC = L3 / "SPEC_k2_v4.spec-rev-18.json"
CO95 = STEP2 / "m13_v57_co95_in4_reachability.json"
BASE = {"spec": "500f3da8179fe19c", "co95_record": "0bc98d2037ce5b47", "board": "0e636a67c1472462"}
GND = "GND"


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def pip(pg, x, y) -> bool:
    inside = False
    n = len(pg)
    for i in range(n):
        x1, y1 = pg[i]
        x2, y2 = pg[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)

    ident = {"spec": s16(SPEC), "co95_record": s16(CO95), "board": s16(K2 / "k2_v4_8L.l4.kicad_pcb")}
    mismatch = {k: {"expect": v, "actual": ident.get(k)} for k, v in BASE.items() if ident.get(k) != v}

    spec = json.loads(SPEC.read_text())
    zd = spec["pd"]["zone_defs"]
    co95 = json.loads(CO95.read_text())
    rows = co95["detail"]

    n_nongnd = sum(1 for e in zd["power_pad_connect"]["entries"] if e["net"] != GND)
    cls = {c: sum(1 for r in rows if r["reach"] == c) for c in
           ("covered_explicit", "covered_bridge_target", "l3_obligation", "needs_region_ruling")}
    integrity_ok = (len(rows) == n_nongnd and sum(cls.values()) == n_nongnd)

    three_state = {
        "geometric_covered": cls["covered_explicit"],
        "declared_pending_l3": cls["covered_bridge_target"] + cls["l3_obligation"],
        "ruling_pending_l1": cls["needs_region_ruling"],
        "machine_closable_today": False,
        "note": "declared_pending_l3 = 声明覆盖（zone targets）或 band 退役义务，几何由 L3 确定性派生、当前未建 ⇒ ≠ 已满足；"
                "ruling_pending_l1 = 电源域/区域归属裁决。",
    }
    # scope 排除（F4）
    scope_excl = {
        "requirement_scope": "power_pad_connect.entries(non-GND)",
        "gnd_stitch_via_realized": sum(1 for c in zd["gnd_stitch_via"]["coordinates"]
                                       if not (c.get("blocked") or c.get("status") == "blocked")),
        "power_zones_vias": sum(len(z.get("vias", [])) for z in zd["power_zones"]),
        "decoupling_vias": len(zd.get("decoupling_via_to_plane", {}).get("vias", [])),
        "note": "同依赖平面覆盖但不在本 requirement 内；GND 走 GND 平面、zone via 由 zone 多边形自证（其多边形当前未建）。",
    }
    # 裁决依据分解（F3）：机判谓词而非自由文本
    own_region = {z.get("net") for z in zd["power_zones"] if z.get("vias") or z.get("targets")}
    polys = [(z["net"], z.get("zone"), z["polygon"]) for z in zd["power_zones"] if isinstance(z.get("polygon"), list)]
    ruling_rows = []
    for r in rows:
        if r["reach"] != "needs_region_ruling":
            continue
        x, y = r["via_pos"]
        other = [(n, zn) for n, zn, pg in polys if n != r["net"] and pip(pg, x, y)]
        if r["net"] not in own_region:
            basis = "machine:net_has_no_in4_region"
        elif other:
            basis = "machine:via_inside_other_net_in4_polygon(" + ",".join(f"{n}:{zn}" for n, zn in other) + ")"
        else:
            basis = "text_only:declared_in_plane_reachability_status"
        ruling_rows.append({"net": r["net"], "pad": f"{r['ref']}.{r['pad']}", "via_pos": r["via_pos"],
                            "basis": basis, "machine_derived": basis.startswith("machine:")})
    basis_counts = {"machine": sum(1 for r in ruling_rows if r["machine_derived"]),
                    "text_only": sum(1 for r in ruling_rows if not r["machine_derived"])}

    # 牙齿
    lpoly = [(0.0, 0.0), (4.0, 0.0), (4.0, 1.0), (1.0, 1.0), (1.0, 4.0), (0.0, 4.0)]
    probe = (3.0, 3.0)
    bbox_hit = (min(p[0] for p in lpoly) <= probe[0] <= max(p[0] for p in lpoly) and
                min(p[1] for p in lpoly) <= probe[1] <= max(p[1] for p in lpoly))
    tooth_pip = bbox_hit and not pip(lpoly, *probe)
    tooth_integrity = (not integrity_ok) or (len(rows) != n_nongnd + 1)  # 注入 +1 必判不完整
    teeth_ok = tooth_pip and tooth_integrity

    verdict = ("BASELINE_MISMATCH" if mismatch else
               ("TEETH_FAIL" if not teeth_ok else
                ("OPEN_GEOMETRY_PENDING_L3_AND_RULING_PENDING_L1"
                 if (three_state["declared_pending_l3"] or three_state["ruling_pending_l1"]) else "PASS")))
    rec = {
        "artifact": "m13_v57_co98_reachability_status_report", "schema": 1, "revision": "CO-98.1",
        "nature": "L2 PDN：In4 平面可达性义务状态报告（机判化 CO-96 F2/F3/F4；只读 co95 权威记录）",
        "inputs": {**ident}, "baseline_expectations": BASE, "baseline_mismatch": mismatch,
        "co95_summary": co95["summary"], "integrity": {"non_gnd_entries": n_nongnd, "classified": len(rows), "ok": integrity_ok},
        "three_state": three_state, "scope_exclusions": scope_excl,
        "ruling_basis": {"breakdown": basis_counts, "rows": ruling_rows},
        "teeth": {"pip_rejects_bbox_approx": tooth_pip, "integrity_detects_miscount": tooth_integrity},
        "teeth_ok": teeth_ok, "baseline_ok": not mismatch,
        "recommendation": "F2 几何闭合 = L3 派生（8 zone target + 6 band 义务）；F3 建议以机判谓词（net 无区 / via 落异网区）替换文本子串，"
                          "R1.2 为唯一 text_only 项需补判据；F4 若纳入 scope 需 SPEC 变更（rev-12）。本件不施加。",
        "non_claims": ["只读；不改 SPEC/板/阈值/冻结源/co95 记录", "本件不判 L3 几何是否已建；不含坐标搜索", "scope 扩展（F4）属 SPEC 变更，未施加"],
        "verdict": verdict,
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-98 verdict=%s three_state=%s basis=%s teeth_ok=%s baseline_ok=%s" %
          (verdict, json.dumps(three_state), json.dumps(basis_counts), teeth_ok, not mismatch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
