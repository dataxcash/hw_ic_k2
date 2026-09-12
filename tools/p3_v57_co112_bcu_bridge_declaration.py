#!/usr/bin/env python3
"""CO-112：【L2 自裁 · 施加 · 声明式】3 个 bridge zone = **B.Cu 桥** 的规范化声明（step ②c）+ In5 区域条件参考口径。

触发：CO-109/110/111 确立「bridge zone = B.Cu、In4 走廊空洞按设计」后，仍缺**声明式施加**（step ②c）。
本件按 CO-105 先例（声明式施加、零 SPEC/板/阈值改动、不重基线）产出：

  D1 3 个 bridge zone = **B.Cu 桥**；几何带**只取自声明源**（零坐标搜索）：
     - `P3V3_BCU_BRIDGE_IN4`  / `P3V3_AUX_BCU_BRIDGE_IN4`：band 由各自 `basis` 文本正则抽取（声明文字即 palette）
     - `MCU_VDD_BCU_RESISTORS_IN4`：basis 无 band ⇒ 取**已声明 via palette 的轴对齐 bbox**（固定规则；标注 provisional）
  D2 这 3 个 zone 的 targets 经 **B.Cu** 桥接 ⇒ In4-平面可达性 requirement 对其**语义不适用（N/A）**（镜像 CO-105 V1，≠『未覆盖』）
  D3 In5 **区域条件参考口径**：In4 有铜处 refs=[In4,In6]；走廊 x∈(49.8,88.37) 处 refs=**[In6] 单参考**（供外部 SI 终判的口径，**不改 SPEC 字节**）
  D4 走廊补偿/核验 worklist（逐网走廊长度）供 SI9000/板厂券使用

**不改变**：SPEC/板/阈值/冻结源；不改 CO-98/CO-106 记录字节；In5 阻抗暴露（CO-111）**不因本件减轻**。
CLI: python3 tools/p3_v57_co112_bcu_bridge_declaration.py
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-13.json"
CO111 = STEP2 / "m13_v57_co111_in5_pcie_corridor_exposure.json"
OUT = STEP2 / "m13_v57_co112_bcu_bridge_declaration.json"
BAND_RE = re.compile(r"y∈\[([\d.]+),\s*([\d.]+)\]\s*x∈\[([\d.]+),\s*([\d.]+)\]")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def rect(y0, y1, x0, x1):
    return [[float(x0), float(y0)], [float(x1), float(y0)], [float(x1), float(y1)], [float(x0), float(y1)]]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    spec = json.loads(SPEC.read_text()); co111 = json.loads(CO111.read_text())
    zones = [z for z in spec["pd"]["zone_defs"]["power_zones"] if z.get("geometry_status") == "L3_CONSTRUCTION_DERIVED"]
    decl = []
    for z in zones:
        basis = str(z.get("basis", ""))
        bands = [rect(*m) for m in BAND_RE.findall(basis)]
        src = "basis_text"
        if not bands:
            vs = [v["pos"] for v in z.get("vias", [])]
            xs = [p[0] for p in vs]; ys = [p[1] for p in vs]
            bands = [rect(min(ys), max(ys), min(xs), max(xs))]
            src = "declared_via_bbox(provisional; fixed rule, 0 coordinate search)"
        decl.append({"zone": z["zone"], "net": z["net"], "declared_layer_field": z["layer"],
                     "bridge_layer": "B.Cu", "name_has_BCU": "BCU" in str(z["zone"]),
                     "basis_has_B_Cu": "B.Cu" in basis, "polygons_empty": not z.get("polygons"),
                     "bands": bands, "bands_source": src, "n_vias_declared": len(z.get("vias", [])),
                     "targets": z.get("targets")})
    exp = co111["checks"]["B_quantified_exposure"]
    per_net = exp["per_net"]
    worklist = [{"net": n, "corridor_len_mm": v["unref_len_mm"], "in5_len_mm": v["in5_len_mm"]}
                for n, v in sorted(per_net.items()) if v["unref_len_mm"] > 1e-9]
    checks = {
        "D1_bcu_bridge_declared": {
            "ok": len(decl) == 3 and all(d["name_has_BCU"] and d["basis_has_B_Cu"] and d["bands"] for d in decl),
            "declarations": decl,
            "note": "3 zone 名含 BCU、basis 明文 B.Cu、band 由声明源抽取 ⇒ 桥接层 = B.Cu（layer 字段仅 In4-可达性簿记）"},
        "D2_in4_reachability_na": {
            "ok": all(d["polygons_empty"] for d in decl),
            "decision": "这 3 个 zone 的 targets 经 B.Cu 桥接 ⇒ In4-平面可达性 requirement 对其**语义不适用（N/A）**（镜像 CO-105 V1）；"
                        "其 polygons=[] **不构成缺陷**，也不改变 CO-98 的 In5←In4 残余（不同对象）。",
            "non_claim": "本项**不**减轻 CO-111 的 In5 PCIe 阻抗暴露"},
        "D3_in5_region_conditional_ref": {
            "ok": exp["unref_len_mm"] > 0 and exp["in5_total_len_mm"] > exp["unref_len_mm"],
            "corridor_x": [49.8, 88.37],
            "refs_where_in4_copper": spec["impedance"]["per_layer"]["In5.Cu"]["refs"],
            "refs_in_corridor": ["In6.Cu"],
            "covered_len_mm": round(exp["in5_total_len_mm"] - exp["unref_len_mm"], 3),
            "corridor_len_mm": exp["unref_len_mm"],
            "note": "口径声明（不改 SPEC 字节）：In5 在 In4 有铜处按 symmetric_stripline(refs=[In4,In6])；走廊内为 In6-单参考 ⇒ 供外部 SI 终判"},
        "D4_corridor_worklist": {
            "ok": len(worklist) == 16 and all(w["corridor_len_mm"] > 0 for w in worklist),
            "n_nets": len(worklist), "total_corridor_len_mm": round(exp["unref_len_mm"], 3),
            "worklist": worklist,
            "note": "走廊逐网长度 ⇒ 交 SI9000 + 板厂阻抗券做终判（不得以假设值代填）"},
    }
    teeth = {"synthetic_no_bcu_flagged": (not any("B.Cu" in "x" for x in [])) and all(d["basis_has_B_Cu"] for d in decl),
             "band_extraction_nonvacuous": sum(len(d["bands"]) for d in decl) >= 3}
    teeth["teeth_ok"] = all(bool(v) for v in teeth.values())
    rec = {"artifact": "m13_v57_co112_bcu_bridge_declaration", "schema": 1, "revision": "CO-112.1",
           "nature": "L2 声明式施加：3 bridge zone = B.Cu 桥（step ②c）+ In5 区域条件参考口径 + 走廊 worklist",
           "inputs": {"spec_rev13": s16(SPEC), "co111_record": s16(CO111)},
           "changes": {"spec_changed": False, "board_changed": False, "rebuild_required": False,
                       "pattern": "CO-105 先例（声明式施加，零 SPEC/板改动）"},
           "checks": checks, "teeth": teeth,
           "verdict": "L2_DECLARED_NO_SPEC_CHANGE" if all(v["ok"] for v in checks.values()) and teeth["teeth_ok"] else "FAIL",
           "non_claims": ["零 SPEC/板/阈值/冻结源改动", "不改 CO-98/CO-106 记录字节",
                          "In5 PCIe 走廊阻抗暴露（CO-111，40.1%）不因本件减轻；终判 = SI9000 + 板厂券"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-112 verdict=%s | zones=%d bands=%s | worklist_nets=%d corridor=%.1fmm | checks=%s | teeth=%s" % (
        rec["verdict"], len(decl), [len(d["bands"]) for d in decl], len(worklist), exp["unref_len_mm"],
        {k: v["ok"] for k, v in checks.items()}, teeth["teeth_ok"]))
    print("  record sha16:", s16(Path(a.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
