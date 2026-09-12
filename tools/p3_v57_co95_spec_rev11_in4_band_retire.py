#!/usr/bin/env python3
"""CO-95：【L2 PDN 自裁】SPEC rev-11 —— 退役「前提已被 CO-74 判定失效」的 In4 keepout band
+ 加显式**平面可达性要求**（不臆造几何；In4 区划几何仍为 L3 确定性派生）。

裁定（L2，自裁）：
 1. `in4_pcie_keepout_band` 的启用前提 = 「wp1_escape_nets 在 In4.Cu 有 14 段走线」——
    该前提已被 CO-74 判定失效（引擎 LAYER_PALETTE=F/In2/In5/B 无 In4；交付板 In4 段数 0；
    layer_plan 仅把 In4 声明为 PDN 平面）⇒ **退役**（连同其 void 理由留存，禁静默放弃）。
 2. `power_zones[0]`（P3V3_EAST）的西界原由该 band 推导（88.17+0.2=88.37）⇒ 西界改由
    **「与异网 In4 铜边 ≥0.2mm」** 决定，落点 = L3 确定性派生（不在此臆造新多边形）。
 3. 新增 `plane_reachability_requirement`（供 L3 派生与后续闸使用）：
    每个 power entry 的 via 必须被**本网** In4 铜覆盖；同网各区连续（无孤岛）；异网净距 ≥0.2mm。
 4. 登记残余 **12 个 entry 无可达路径**（CO-95 机判）：3× 12V_IN（本网无 In4 区）+ 6× U6 P3V3
    （落在已退役 band 内，退役后由 L3 覆盖）+ 3× P3V3_AUX 西侧（无本网区，且西区名义网为 MCU_VDD
    而 basis 文本称 P3V3_AUX+MCU_VDD 同区 ⇒ **区域归属冲突**）。
CLI: python3 tools/p3_v57_co95_spec_rev11_in4_band_retire.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
SRC = L3 / "SPEC_k2_v4.spec-rev-10.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-11.json"
REC = L3 / "m13_v57_co95_spec_rev11_band_retire.json"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    spec = json.loads(SRC.read_text())
    zd = spec["pd"]["zone_defs"]
    band = zd.pop("in4_pcie_keepout_band")
    zd["retired_in4_keepout_band_6l"] = {
        "band": {"x": band["x"], "y": band["y"], "seg_count": band.get("seg_count")},
        "retired_by": "CO-95", "premise_voided_by": "CO-74",
        "premise": band["basis"],
        "void_reason": ("引擎 LAYER_PALETTE=F/In2/In5/B（In4 非布线层）+ 交付板 In4.Cu 段数 0 + "
                        "layer_plan 仅把 In4 声明为 PDN 平面 ⇒ 『wp1_escape_nets 在 In4 有走线』前提不存在；"
                        "CO-74 carrier_change 已判该前提失效，本件把该判定传播到本约束。"),
        "effect": "退役后 In4 铜可在原 band 区内按网归属铺设（仍须满足 plane_reachability_requirement）。",
    }
    for z in zd["power_zones"]:
        if z.get("zone") == "P3V3_EAST":
            z["basis"] = ("pd 语义 P3V3=In4 一区(东侧)；**西界 = 与异网 In4 铜边 ≥0.2mm（POWER 判据）**，"
                          "落点由 L3 确定性派生（CO-95：原『左界 = In4 走线带东缘 88.17 + 0.2 = 88.37』"
                          "的 band 前提已被 CO-74 判定失效 ⇒ 该推导废止）；"
                          "覆盖 U3/U7 P3V3 pads + C65-C83 去耦 + C67/68/72 及 U6 球栅场内 P3V3 球（原被 band 排除）。")
            z["west_bound_rule"] = "inter_net_clearance>=0.2mm (boundary at L3 derivation)"
    zd["plane_reachability_requirement"] = {
        "basis": "CO-95 裁定：power entry 的 via 必须最终被**本网** In4 铜覆盖，否则该 connection 为名义的",
        "rules": ["每个 power entry 的 via 必须落在本网 In4 铜内（含 L3 派生区域）",
                  "同网各区须连续（无孤岛未连）",
                  "异网 In4 铜边净距 ≥0.2mm（POWER 判据，不得放宽）",
                  "L3 几何 = 确定性派生（非求解器、零坐标搜索）"],
        "gate": "tools/p3_v57_co95_in4_reachability.py",
    }
    zd["plane_reachability_status"] = {
        "verdict": "OPEN_12",
        "unresolved": [
            {"net": "12V_IN", "pads": ["C88.1", "U2.4", "U2.6"],
             "why": "该网**无任何 In4 区** ⇒ 需先裁其承载（In4 区域分配 = 区域/电源域划分）"},
            {"net": "P3V3", "pads": ["U6.AC17", "U6.AC20", "U6.AK17", "U6.AK20", "U6.T17", "U6.T20"],
             "why": "原落在已退役 band 内；band 退役后由 L3 派生覆盖（本件已解除阻断）"},
            {"net": "P3V3_AUX", "pads": ["C90.1", "R1.2", "U1.15"],
             "why": "P3V3_AUX 无西区 In4 区；西区名义网 = MCU_VDD 而 basis 文本称 P3V3_AUX+MCU_VDD 同区 ⇒ **区域归属冲突**，须裁"},
        ],
        "note": "本件只退役失效约束 + 立可达性要求；未臆造 In4 几何（仍属 L3 确定性派生）。",
    }
    spec["spec_version"] = "1.1.spec-rev-11"
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n")
    r10 = json.loads(SRC.read_text()); r11 = json.loads(OUT.read_text())
    outside = sorted({k for k in set(r10) | set(r11) if k != "pd" and r10.get(k) != r11.get(k)})
    rec = {"artifact": "m13_v57_co95_spec_rev11_band_retire", "schema": 1, "revision": "CO-95.1",
           "ruling": {"scope": "L2（PDN / 叠层分配）自裁",
                      "acts": ["退役 premise 已失效的 In4 keepout band（原约束留存 + void 理由）",
                               "废止 P3V3_EAST 的 band 推导西界，改由 ≥0.2mm 异网净距决定（落点 L3 派生）",
                               "新增 plane_reachability_requirement（via 须被本网 In4 铜覆盖）",
                               "登记 12 个无可达路径 entry（3 需区域裁决 / 6 已解除阻断 / 3 区域归属冲突）"]},
           "src": {"spec": SRC.name, "sha16": s16(SRC)}, "out": {"spec": OUT.name, "sha16": s16(OUT)},
           "invariants": {"outside_pd_changed": outside, "board_unchanged": True},
           "verdict": "DERIVED"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print("rev-11 sha16 =", s16(OUT), "| outside_pd_changed =", outside)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
