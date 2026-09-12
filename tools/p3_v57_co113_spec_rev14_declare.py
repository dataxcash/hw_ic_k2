#!/usr/bin/env python3
"""CO-113：【L2 自裁 · 施加】SPEC rev-14 = 把 CO-105/109/110/111/112 的裁定**写入 canonical SPEC**（step ② 的「新 rev 重基线」）。

rev-14 = rev-13 + **仅新增声明键**（不改任何既有标量/多边形/阈值/网/层角色/坐标/vias/blocked/impedance/stackup）：
  1. `pd.zone_defs.in4_corridor_void_by_design_v1`：In4 走廊 x∈(49.8,88.37) 按设计无铜（PM T2-ECN-1/2）+ CO-111 量化
  2. 3 个 `L3_CONSTRUCTION_DERIVED` power_zone：`bridge_layer = "B.Cu"` + `bcu_bridge_bands`（band 只取自声明源）
  3. `pd.zone_defs.plane_reachability_status.na_scope_v1`：GND entries（CO-105）与 bridge zone targets（CO-112）语义 **N/A**

新键**无任何消费者** ⇒ 引擎/L4/L5/各闸读数不变；仅 SPEC sha 及各处 pin 前移。
CLI: python3 tools/p3_v57_co113_spec_rev14_declare.py
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SRC = L3 / "SPEC_k2_v4.spec-rev-13.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-14.json"
REC = STEP2 / "m13_v57_co113_spec_rev14_declare.json"
CO111 = STEP2 / "m13_v57_co111_in5_pcie_corridor_exposure.json"
BAND_RE = re.compile(r"y∈\[([\d.]+),\s*([\d.]+)\]\s*x∈\[([\d.]+),\s*([\d.]+)\]")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def flat(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f"{p}[{i}]")
    else:
        yield p, o


def rect(y0, y1, x0, x1):
    return [[float(x0), float(y0)], [float(x1), float(y0)], [float(x1), float(y1)], [float(x0), float(y1)]]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC)); ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.src).read_text()); before = dict(flat(spec))
    co111 = json.loads(CO111.read_text())
    ev = co111["checks"]["B_quantified_exposure"]
    zd = spec["pd"]["zone_defs"]
    zd["in4_corridor_void_by_design_v1"] = {
        "note": "CO-109/110/111/112：In4 走廊按设计无铜（PM T2-ECN-1/2『In4 走线带不跨』；bridge = B.Cu）",
        "corridor_x": [49.8, 88.37], "frame_y": [33.3, 78.7],
        "in4_declared_copper_x_ranges": {z["zone"]: [min(p[0] for p in z["polygon"]), max(p[0] for p in z["polygon"])]
                                         for z in zd["power_zones"] if z.get("layer") == "In4.Cu" and z.get("polygon")},
        "evidence_in5_pcie": {"unref_len_mm": ev["unref_len_mm"], "in5_len_mm": ev["in5_total_len_mm"],
                              "unref_pct": ev["unref_pct"], "n_nets": len(ev["per_net"])},
        "disposition": "In5 在该带 refs=[In6.Cu] 单参考；终判 = SI9000 + 板厂阻抗券（不得以假设值代填）",
        "refs": ["CO-109", "CO-110", "CO-111", "CO-112"]}
    bridges = []
    for z in zd["power_zones"]:
        if z.get("geometry_status") != "L3_CONSTRUCTION_DERIVED":
            continue
        basis = str(z.get("basis", ""))
        bands = [rect(*m) for m in BAND_RE.findall(basis)]
        src = "basis_text"
        if not bands:
            vs = [v["pos"] for v in z.get("vias", [])]
            bands = [rect(min(p[1] for p in vs), max(p[1] for p in vs), min(p[0] for p in vs), max(p[0] for p in vs))]
            src = "declared_via_bbox(provisional)"
        z["bridge_layer"] = "B.Cu"; z["bcu_bridge_bands"] = bands; z["bcu_bridge_bands_source"] = src
        bridges.append({"zone": z["zone"], "bands": bands, "source": src, "targets": z.get("targets")})
    zd["plane_reachability_status"]["na_scope_v1"] = {
        "note": "语义不适用（N/A）≠『未覆盖』；不改既有 unresolved 列表与阈值",
        "gnd_entries": {"basis": "GND 平面层 = In1/In3/In6，In4 仅 P3V3/MCU_VDD/P3V3_AUX ⇒ requirement 对 GND entry 不可判定",
                        "ref": "CO-105", "ruling": "CLOSE_NO_SCOPE_EXTENSION"},
        "bcu_bridge_zone_targets": {"zones": [b["zone"] for b in bridges],
                                    "basis": "经 B.Cu 桥接 ⇒ 无需本网 In4 铜覆盖", "ref": "CO-112"},
        "in5_corridor_reference": {"ref": "CO-111", "note": "In5 走廊带 refs=[In6] 单参考（终判外部）"}}
    spec["spec_version"] = "1.1.spec-rev-14"
    after = dict(flat(spec))
    changed = {k for k in set(before) & set(after) if before[k] != after[k]}
    assert changed == {".spec_version"}, f"unexpected changed paths: {sorted(changed)}"
    Path(a.out).write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n")
    rec = {"artifact": "m13_v57_co113_spec_rev14_declare", "schema": 1, "revision": "CO-113.1",
           "nature": "L2 施加：CO-105/109/110/111/112 裁定写入 canonical SPEC（rev-14，仅新增声明键）",
           "src": Path(a.src).name, "src_sha16": s16(Path(a.src)), "out": Path(a.out).name, "out_sha16": s16(Path(a.out)),
           "changes": {"only_spec_version_changed_among_existing": True, "new_keys": ["pd.zone_defs.in4_corridor_void_by_design_v1",
                       "pd.zone_defs.power_zones[*].bridge_layer", "pd.zone_defs.power_zones[*].bcu_bridge_bands",
                       "pd.zone_defs.plane_reachability_status.na_scope_v1"],
                       "engine_consumes_new_keys": False, "l4_consumes_new_keys": False, "l5_consumes_new_keys": False,
                       "rebuild_required": True, "n_bridge_zones": len(bridges), "bridges": bridges,
                       "vias_unchanged": True, "polygons_unchanged": True, "thresholds_unchanged": True},
           "redline": "只新增声明键 + spec_version；不改多边形/阈值/网/层角色/坐标/vias/blocked/impedance/stackup"}
    Path(REC).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-113 rev-14 written:", json.dumps(rec["changes"]["new_keys"], ensure_ascii=False))
    print("spec_rev14_sha16", rec["out_sha16"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
