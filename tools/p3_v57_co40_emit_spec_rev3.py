#!/usr/bin/env python3
"""CO-40：从 SPEC_k2_v4.spec-rev-2.json 发射版本化后继 `SPEC_k2_v4.spec-rev-3.json`（L2 自裁）。

增量（仅声明字段；原 SPEC_k2_v4.json / spec-rev-2 逐字节不动）：
  1. spec_version: 1.1.spec-rev-2 -> 1.1.spec-rev-3
  2. constraints.escape_transition_zone.refclk_j2_transit：REFCLK J2 侧 pad 场 transit 的闭式规格
     （F.Cu→In2→F.Cu 单次换层；每线 2 via；via#1 落两列缝 x=133.825；via#2 x<=131.525；
      与 SPEC vias.high_speed.basis 已有的「每线<=2 过孔 = 单次换层(F→In2→F)」同一机制）
  3. constraints.escape_transition_zone.no_via 语义收窄：域内默认仍禁 via，REFCLK J2 transit 为唯一例外
  4. constraints.refclk_isolated_scope：隔离语义收窄为"J2 逃逸区外维持"
  5. corridors[EAST_CHIP_TO_J2].bands[refclk].j2_transit：指向本例外（轨 y/layer 不变）
零搜索：所有常数来自 CO-40 `m13_v57_CO40_refclk_j2_transit_l2_ruling.md` §2 闭式规格 + 冻结板实测。
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
SRC = L3 / "SPEC_k2_v4.spec-rev-2.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-3.json"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    before = sha256(SRC)

    d["spec_version"] = "1.1.spec-rev-3"
    etz = d["constraints"]["escape_transition_zone"]
    etz["no_via"] = True  # 域默认不变；REFCLK J2 transit 为显式唯一例外（见下）
    etz["refclk_j2_transit"] = {
        "authority": "CO-40 L2 自裁（LAYOUT_CONSTITUTION 第二章：走廊分配/过孔策略=L2）",
        "rule": "REFCLK-ECS-001",
        "applies_to": ["PCIE_REFCLK0_N", "PCIE_REFCLK1_N"],
        "reason": "J2 外列 pad (12/30) 被内列焊盘墙封堵：同排缝 0.6-0.35=0.25mm < 0.205+2*0.075=0.355mm（店规 0.175 更甚）⇒ F.Cu 直行物理不可能",
        "layer_seq": ["F.Cu", "In2.Cu", "F.Cu"],
        "max_vias_per_line": 2,
        "no_via": False,
        "via_std": {"drill_mm": 0.2, "annular_mm": 0.075, "outer_mm": 0.35, "back_drill": True},
        "pad_edge_clearance_mm": 0.3,
        "via1_x_mm": 133.825,
        "via1_x_basis": "两列缝中线：距内列 pad 东缘 133.3 与 外列 pad 西缘 134.35 各 0.35mm（>=0.3）",
        "via2_x_max_mm": 131.525,
        "via2_x_basis": "内列 pad 西缘 132.0 - via 半径 0.175 - pad_edge_clearance 0.3",
        "in2_channel_x_mm": [130.5925, 131.5475],
        "in2_channel_basis": "In2 竖直 stub 列 x=130.49/131.65 之间净宽 0.955mm（REFCLK1 U 形绕行用）",
        "in2_layer_basis": "In2 = stripline dual GND ref (In1/In3)；B.Cu 参考层为 In6 信号层，非定阻抗 ⇒ 不选",
        "skew_compensation": "N 增 ~2.4mm(REFCLK0)/~8.0mm(REFCLK1) ⇒ 须 P 侧幂绕补偿至 intra_pair_skew_mm <= 0.15",
        "perimeter": "域外维持 shop/netclass 判据（PCIe85 0.175 / POWER 0.2）；本例外不放宽任何数值阈值",
    }
    d["constraints"]["refclk_isolated_scope"] = (
        "J2 逃逸区外维持隔离（refclk_isolated 仍 true）；区内仅允许 ECS-001 规定的单次 F.Cu->In2->F.Cu 换层，"
        "REFCLK 不与数据扇共用走廊（数据扇在 In2 的列/走廊不因本例外改变）"
    )
    for cor in d["corridors"]:
        if cor.get("id") != "EAST_CHIP_TO_J2":
            continue
        for b in cor["bands"]:
            if b.get("band") == "refclk":
                b["j2_transit"] = "REFCLK-ECS-001 (F.Cu->In2->F.Cu 单次换层, 仅 J2 pad 场内); 轨 y/layer 不变"
    d["_spec_rev_3"] = {
        "card": "SPEC-REV-3",
        "at": "2026-09-12",
        "authority": "L2 自裁（CO-40；LAYOUT_CONSTITUTION 第二章 走廊/过孔策略 = L2）",
        "basis": "m13_v57_CO40_refclk_j2_transit_l2_ruling.md 7be78b59cdff4380",
        "changes": [
            "spec_version: 1.1.spec-rev-2 -> 1.1.spec-rev-3",
            "constraints.escape_transition_zone.refclk_j2_transit: 新增（ECS-001 闭式规格）",
            "constraints.escape_transition_zone.no_via: 语义收窄为'域默认 true + REFCLK J2 transit 唯一例外'",
            "constraints.refclk_isolated_scope: 新增（隔离=区外）",
            "corridors[EAST_CHIP_TO_J2].bands[refclk].j2_transit: 新增注记（轨 y/layer 未改）",
        ],
        "unchanged": "stackup / impedance / net_classes / vias / PD / 其他 corridors/bands（含 bands[refclk].layer=F.Cu 与 tracks_y）/ 所有其他字段；原 SPEC_k2_v4.json 与 spec-rev-2 逐字节未动",
        "spec_sha256_before": before,
        "rollback": "删除本文件；引擎/验证器 FROZEN spec 指回 SPEC_k2_v4.json（0bd52ed48e720b8c）或 spec-rev-2（0a7ad112ac4c57e3）",
    }
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{OUT.name}: sha16={sha256(OUT)[:16]} (before={before[:16]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
