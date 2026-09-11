#!/usr/bin/env python3
"""CO-56：从 SPEC_k2_v4.spec-rev-3.json 发射版本化后继 `SPEC_k2_v4.spec-rev-4.json`（L2/SI 自裁）。

增量 = **纯加性**（不动任何引擎消费的数值；不动 corridors/layer_plan/constraints/vias/pd）：
  1. spec_version: 1.1.spec-rev-3 -> 1.1.spec-rev-4
  2. stackup: material 更新为 8L 声明（旧 6L 串移入 material_legacy_6l）+ 新增
     total_thickness_mm / dielectric_8l（= CO-55 反解逐层介质表，含 1.6mm 闭合）
  3. impedance: 新增 per_layer（F.Cu 微带 / In2.Cu 带状线 / In6.Cu 单参考）+ gap_mm_semantics
     （原标量 target_zdiff/model/width_mm/gap_mm 全部保留 → 消费方兼容）
  4. net_classes.PCIe85.diff_pair: 新增 p_gap_semantics=lower_bound + p_gap_geometry_mm_delivered=0.295
     + inter_pair_spacing_scope（不修改 p_gap/p_width/inter_pair_spacing_mm 数值）
  5. _spec_rev_4 溯源块

**零几何影响**：引擎只读 net_classes.PCIe85.{width,clearance} / vias.std.outer /
constraints.escape_transition_zone.escape_clearance_mm / corridors / layer_plan / stackup 的 *.Cu 键
⇒ 本发射应使 W3 图纸**逐字节不变**（由 CO-56 复跑核验）。
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SRC = L3 / "SPEC_k2_v4.spec-rev-3.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-4.json"
REQ = STEP2 / "m13_v57_co55_layer_impedance_requirement.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    req = json.loads(REQ.read_text(encoding="utf-8"))
    before = sha(SRC)

    # 1) 版本
    d["spec_version"] = "1.1.spec-rev-4"

    # 2) stackup（加性；保留全部 .Cu 键 ⇒ 引擎 stackup_layers 不变）
    st = d["stackup"]
    st["material_legacy_6l"] = st["material"]
    st["material"] = ("JLC 8L 1.6mm 阻抗板 JLC08161H（南亚 NP-155F；prepreg 2116*1 / 3313*1，core 0.36*2）"
                      " — 叠层分配与逐层介质厚度由 L2 CO-55 反解裁定；终判 = 板厂阻抗券")
    st["total_thickness_mm"] = 1.6
    ex = req["thickness_closure_example"]["materials"]
    st["dielectric_8l"] = {
        "d(F.Cu-In1.Cu)": {"mm": ex["d(F-In1)"], "material": "2116*1", "er": 4.16, "use": "F.Cu 微带参考"},
        "d(In1.Cu-In2.Cu)": {"mm": ex["d(In1-In2)"], "material": "core", "er": 3.99, "use": "In2 带状线上参考（对称化）"},
        "d(In2.Cu-In3.Cu)": {"mm": ex["d(In2-In3)"], "material": "core", "er": 3.99, "use": "In2 带状线下参考（对称化）"},
        "d(In3.Cu-In4.Cu)": {"mm": ex["d(In3-In4)"], "material": "1080*2", "er": 4.10, "use": "余隙"},
        "d(In4.Cu-In5.Cu)": {"mm": ex["d(In4-In5)"], "material": "1080*2", "er": 4.10, "use": "余隙"},
        "d(In5.Cu-In6.Cu)": {"mm": ex["d(In5-In6)"], "material": "3313*1", "er": 4.10, "use": "In6 单参考微带"},
        "d(In6.Cu-B.Cu)": {"mm": ex["d(In6-B)"], "material": "自由余隙（1.6mm 闭合）", "er": 4.10, "use": "余隙"},
    }
    st["dielectric_8l_basis"] = {
        "authority": "L2/SI 自裁（CO-55；LAYOUT_CONSTITUTION 第二章：叠层分配 + SI 物理承载）",
        "method": "由交付几何(w=0.205, 对内中心 0.5/0.6 → gap 0.295/0.395) 反解，使各层 Zdiff 落 85±10%",
        "model": "IPC-2141（_shared/eda_core/stackup.py；datum 85.05 vs SPEC 自陈 85.1）",
        "evidence": "CO-55 card（叠层反解裁定）+ tools/p3_v57_co55_layer_aware_zdiff.py（去环：不引用下游工件 sha）",
        "thickness_closure": "铜 0.175 + 介质 1.425 = 1.6000mm（机判 delta=0.000）",
        "verdict_first_order": {"F.Cu": "88.4–91.2Ω", "In2.Cu": "82.1–89.2Ω", "In6.Cu": "85.5–87.4Ω"},
        "signoff": "未完成：须 SI9000 + 板厂阻抗券（coupon_required=true）",
        "fallback": "若板厂标准 8L 无法给 b(In1-In3) >= 0.582 ⇒ In2 线宽按 CO-55 §4 R2 重导 ⇒ W3 re-open",
    }

    # 3) impedance（加性；保留原标量）
    imp = d["impedance"]
    imp["gap_mm_semantics"] = "lower_bound（DRC clearance 0.175）；几何真源 = per_layer[*].gap_mm_delivered"
    imp["per_layer"] = {
        "F.Cu": {"kind": "microstrip", "refs": ["In1.Cu"], "w_mm": 0.205, "gap_mm_delivered": [0.295, 0.395],
                 "h_mm": ex["d(F-In1)"], "er": 4.16, "material": "2116*1"},
        "In2.Cu": {"kind": "stripline(asym→sym)", "refs": ["In1.Cu", "In3.Cu"], "w_mm": 0.205,
                   "gap_mm_delivered": [0.295, 0.395], "b_mm": round(ex["d(In1-In2)"] + ex["d(In2-In3)"], 4),
                   "er": 3.99, "material": "core 0.36*2"},
        "In6.Cu": {"kind": "microstrip(single-ref)", "refs": ["In5.Cu"], "w_mm": 0.205,
                   "gap_mm_delivered": [0.295, 0.395], "h_mm": ex["d(In5-In6)"], "er": 4.10, "material": "3313*1"},
    }
    imp["per_layer_basis"] = ("CO-55/CO-56：单一 (w,gap) 跨层通用不成立；上表为分层口径（一阶），终判=板厂券；"
                              "B.Cu 无平面参考（参考层 In6 为信号）⇒ 非阻抗控制层")

    # 4) net_classes 语义（数值不动）
    dp = d["net_classes"]["PCIe85"]["diff_pair"]
    dp["p_gap_semantics"] = "lower_bound"
    dp["p_gap_geometry_mm_delivered"] = 0.295
    dp["p_gap_geometry_source"] = "L4 construction 实测（CO-54 card / tools/p3_v57_co54_spec_delivery_audit.py；对内中心 0.500/0.600；去环：不引用下游工件 sha）"
    d["net_classes"]["PCIe85"]["inter_pair_spacing_scope"] = (
        "0.875 = 对间铜边净空设计基线（容量/新布线口径）；as-built 走廊轨距 1.20（corridors[].bands[].tracks_y，"
        "L2 CO-10 落地）⇒ 交付对间最小铜边 0.345（In6 长平行带）；对间串扰复核 = 领域求解器/板厂券，记录见 CO-54 F2/F3")

    # 5) 溯源
    d["_spec_rev_4"] = {
        "card": "SPEC-REV-4", "at": "2026-09-12",
        "authority": "L2/SI 自裁（CO-55/CO-56；LAYOUT_CONSTITUTION 第二章）",
        "basis": ["CO-53 card", "CO-54 card", "CO-55 card",
                  "tools/p3_v57_co55_layer_aware_zdiff.py（本 ECO 只引用 card/工具，不引用下游工件 sha ⇒ 无循环重基线）"],
        "changes": [
            "spec_version: 1.1.spec-rev-3 -> 1.1.spec-rev-4",
            "stackup.material -> 8L 声明（旧值移入 material_legacy_6l）；新增 total_thickness_mm / dielectric_8l（+ basis）",
            "impedance: 新增 per_layer（F/In2/In6 分层口径）+ gap_mm_semantics",
            "net_classes.PCIe85.diff_pair: 新增 p_gap_semantics=lower_bound / p_gap_geometry_mm_delivered / "
            "inter_pair_spacing_scope（**数值均未改**）",
        ],
        "unchanged": "所有数值阈值（net_classes.PCIe85.* / impedance.target_zdiff,width_mm,gap_mm / vias / constraints）、"
                     "corridors（含 tracks_y 1.20，符合交付网格）与 layer_plan、PD、board、components；"
                     "原 SPEC_k2_v4.json / spec-rev-2 / spec-rev-3 逐字节未动",
        "geometry_impact_expected": "none（引擎消费字段未改 ⇒ W3 图纸应逐字节不变，由 CO-56 复跑核验）",
        "spec_sha256_before": before,
        "rollback": "删除本文件；引擎 F/FROZEN_SHA 与 validator 冻结集指回 spec-rev-3（2d6dbd8bd8d667d7）",
    }
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha256": sha(OUT), "sha16": sha(OUT)[:16],
                      "src_sha16": before[:16]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
