#!/usr/bin/env python3
"""P3 v57 BIG — W2 数据块：连接器列/簇结构（R3 候选域输入，纯 manifest 零板读）。

输出每连接器：按 x 聚列（列 x、行 y 集、网/极），供 R3 逃逸候选域推导
（J2 内/外列、J3 上簇、J4 下簇）+ AC 墙声明带（SPEC）。
"""
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
SPEC = L3 / "SPEC_k2_v4.json"
OUT = STEP2 / "m13_v57_big_w2_connector_cols.json"


def main() -> int:
    mf = json.load(open(MANIFEST))
    spec = json.load(open(SPEC))
    cols = {}
    for pg in mf["pages"]:
        if pg["kind"] != "data":
            continue
        for pol in ("P", "N"):
            a = pg["anchors"]["conn"][pol]
            ref = a["ref"]
            x, y = a["pad_global"]
            cols.setdefault(ref, {}).setdefault(round(x, 3), []).append(
                {"net": a["net"], "pin": a["pin"], "pad_num": a["pad_num"],
                 "y": round(y, 3), "pol": pol, "page": pg["page_id"]})
    out = {}
    for ref in sorted(cols):
        out[ref] = {}
        for x in sorted(cols[ref]):
            rows = sorted(e["y"] for e in cols[ref][x])
            out[ref][str(x)] = {
                "n_pads": len(cols[ref][x]),
                "y_min": rows[0], "y_max": rows[-1],
                "rows": rows,
                "entries": sorted(cols[ref][x], key=lambda e: e["y"])}
    rep = {"artifact": "m13_v57_big_w2_connector_cols",
           "basis": "page_manifest 连接器锚(pad_global) 聚列; 零板读",
           "connectors": out,
           "ac_wall_declared": {
               "mcio_side_x": spec["capacitor_walls"]["mcio_side_x"],
               "j2_side_x": spec["capacitor_walls"]["j2_side_x"],
               "upper_band_y": spec["capacitor_walls"]["upper_band_y"],
               "lower_band_y": spec["capacitor_walls"]["lower_band_y"],
               "min_center_pitch_mm": spec["capacitor_walls"][
                   "min_center_pitch_mm"]},
           "inputs_sha": {"manifest": hashlib.sha256(
               MANIFEST.read_bytes()).hexdigest()[:12]}}
    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    for ref in sorted(out):
        print(ref, "cols:", {x: (v["n_pads"], v["y_min"], v["y_max"])
                             for x, v in out[ref].items()})
    print("artifact:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
