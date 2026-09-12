#!/usr/bin/env python3
"""CO-95：【L2 PDN】power entry 的 **In4 平面可达性**机判（+ 陈旧 keepout band 取证）。

问题：`power_pad_connect.entries` 的 via 必须最终被**本网 In4 铜**覆盖，否则该「连接」是名义的（via 落到无铜处）。
判据（机判，无需 L3 几何）：
  A `in_explicit_polygon`  : via 落在本网 In4 显式 polygon 内；
  B `declared_bridge_target`: 该 (ref,pad) 在某 In4 桥区 `targets` 内（几何 = L3 确定性派生）；
  C `no_declared_path`     : 以上皆非 ⇒ **无可达路径**（子类：落在**陈旧 keepout band**内 / 本网**无 In4 区**）。
牙齿：合成注入（band 内点必须被抓、东区点必须放行）。
CLI: python3 tools/p3_v57_co95_in4_reachability.py [--spec S] [--out J]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
DEFAULT_SPEC = L3 / "SPEC_k2_v4.spec-rev-11.json"
DEFAULT_OUT = L3 / "mcio_feas_step2/m13_v57_co95_in4_reachability.json"
GND = "GND"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(DEFAULT_SPEC))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    sp = Path(a.spec)
    spec = json.loads(sp.read_text())
    zd = spec["pd"]["zone_defs"]
    ppc = zd["power_pad_connect"]
    band = zd.get("in4_pcie_keepout_band") or zd.get("retired_in4_keepout_band_6l", {}).get("band", {})
    bx = band.get("x", [1e9, -1e9]); by = band.get("y", [1e9, -1e9])

    poly = {}
    targets = {}
    for z in zd.get("power_zones", []):
        if isinstance(z.get("polygon"), list):
            poly.setdefault(z["net"], []).append((z.get("zone", "?"), z["polygon"]))
        for t in z.get("targets", []):
            key = t.split("(")[0].strip()
            targets[key] = z.get("zone", "?")
            if "." not in key:                  # 目标为**裸 ref**（如 "R29"）才以 ref 匹配；
                targets.setdefault(f"@{key}", z.get("zone", "?"))   # "U2.pad5" 不得放行 U2 其它 pad

    def _pip(pg, x, y):
        """射线法真·点在多边形内（CO-98 F6 硬化：取代 bbox 近似；现行 2 个显式 polygon 均轴对齐矩形 ⇒ 输出逐字节不变）。"""
        inside = False
        n = len(pg)
        for i in range(n):
            x1, y1 = pg[i]
            x2, y2 = pg[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
        return inside

    def in_poly(net, x, y):
        for name, pg in poly.get(net, []):
            if _pip(pg, x, y):
                return name
        return None

    def classify(ref, pad, net, x, y):
        p = in_poly(net, x, y)
        if p:
            return "covered_explicit", p
        for key in (f"{ref}.pad{pad}", f"{ref}.{pad}", f"@{ref}"):
            t = targets.get(key)
            if t:
                return "covered_bridge_target", f"{key}@{t}"
        nets_with_region = {z.get("net") for z in zd.get("power_zones", []) if z.get("vias") or z.get("targets")}
        if net not in nets_with_region:
            return "needs_region_ruling", f"no_in4_region_for_net({net})"
        if declared_status.get(net, {}).get("needs_region_ruling") and \
                (f"{ref}.{pad}" in declared_status[net]["pads"] or f"{ref}.pad{pad}" in declared_status[net]["pads"]):
            return "needs_region_ruling", f"declared:{declared_status[net]['why'][:60]}"
        if band_retired and bx[0] < x < bx[1] and by[0] < y < by[1]:
            return "l3_obligation", "band_retired_L3_derivation_obligated"
        return "l3_obligation", "outside_declared_regions_L3_obligated"

    band_retired = "retired_in4_keepout_band_6l" in zd
    declared_status = {}
    for u in zd.get("plane_reachability_status", {}).get("unresolved", []):
        declared_status[u["net"]] = {"needs_region_ruling": "需要" in u.get("why", "") or "须裁" in u.get("why", ""),
                                     "pads": set(u.get("pads", [])), "why": u.get("why", "")}
    rows = []
    for e in ppc["entries"]:
        if e["net"] == GND:
            continue
        cls, why = classify(e["ref"], str(e["pad"]), e["net"], e["via_pos"][0], e["via_pos"][1])
        rows.append({"ref": e["ref"], "pad": str(e["pad"]), "net": e["net"],
                     "via_pos": e["via_pos"], "reach": cls, "detail": why})
    rows.sort(key=lambda r: (r["reach"], r["net"], r["ref"], r["pad"]))
    gaps = [r for r in rows if r["reach"] in ("needs_region_ruling", "l3_obligation")]

    # 牙齿：合成注入（真跑 classify）
    teeth_bad = classify("T9", "1", "12V_IN", 60.0, 50.0)[0] == "needs_region_ruling"
    teeth_ok = classify("T9", "1", "P3V3", 120.0, 50.0)[0] == "covered_explicit"
    rec = {"artifact": "m13_v57_co95_in4_reachability", "schema": 1, "revision": "CO-95.1",
           "nature": "L2 PDN：power entry 的 In4 平面可达性机判（via 是否被本网 In4 铜覆盖）",
           "inputs": {"spec": sp.name, "spec_sha16": s16(sp),
                      "explicit_polygons": {k: [n for n, _ in v] for k, v in poly.items()},
                      "bridge_targets": targets,
                      "keepout_band": {"x": bx, "y": by,
                                       "status": ("RETIRED_void_premise" if "retired_in4_keepout_band_6l" in zd
                                                  else "ACTIVE")}},
           "summary": {"power_entries": len(rows),
                       "covered_explicit": sum(1 for r in rows if r["reach"] == "covered_explicit"),
                       "covered_bridge_target": sum(1 for r in rows if r["reach"] == "covered_bridge_target"),
                       "l3_obligation": sum(1 for r in rows if r["reach"] == "l3_obligation"),
                       "needs_region_ruling": sum(1 for r in rows if r["reach"] == "needs_region_ruling"),
                       "unresolved_total": len(gaps)},
           "gaps": gaps, "detail": rows,
           "teeth": {"band_point_flagged": teeth_bad, "east_point_passes": teeth_ok},
           "verdict": "COVERAGE_GAP" if gaps else "PASS",
           "non_claims": ["不改 SPEC/板/阈值/冻结源；本件为机判 + 取证",
                          "B 类（桥区 target）几何为 L3 确定性派生，本件只判『是否被声明覆盖』，不判 L3 几何是否已建"]}
    if not (teeth_bad and teeth_ok):
        rec["verdict"] = "FAIL(teeth)"
    elif rec["summary"]["needs_region_ruling"]:
        rec["verdict"] = "OPEN_needs_region_ruling"
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print("CO-95 verdict=%s %s" % (rec["verdict"], json.dumps(rec["summary"], ensure_ascii=False)))
    print("teeth:", rec["teeth"])
    for r in gaps:
        print(f"   GAP {r['net']:9s} {r['ref']}.{r['pad']} @{r['via_pos']} :: {r['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
