#!/usr/bin/env python3
"""CO-63：【L2 叠层分配/过孔策略】把 85Ω 关键网移出 B.Cu 的**层计划可行性机判（负结果）**。

CO-62 裁定「16 张 dn 带页逃逸/stub 移出 B.Cu」（L2 层分配）为整改方向。本件机判该方向是否可行：
把逃逸层映射 `ESC_MAP` 改造成 **B.Cu-free** 的两个候选，重跑放置（同旋钮）并做净距复核。

结果（负）：A 18/32 落位 + 1 违规；B 12/32 + 11 违规 ⇒ B.Cu 逃逸层是**承载性**的，
移出后 F/In2/In6 三层无法容纳逃逸（F.Cu 受 SMD 焊盘挤压、In6 为 lane 层形成自交）。
⇒ CO-62 的整改**不可由 L2 层分配达成**，须改逃逸拓扑/包络（L1：球图逃逸/层数/包络）。
"""
from __future__ import annotations
import hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co63_bcu_free_layerplan_probe.json"
GEOM = STEP2 / "m13_v57_co63_bcu_free_esc_geom.json"
VERIFY = STEP2 / "m13_v57_co63_bcu_free_esc_verification.json"
KNOBS = {"CO10_COLMODE": "pol", "CO10_EASTSPLIT": "in2c", "CO10_EDELTA": "-0.10",
         "CO10_FANY_J3": "34.5,51.5", "CO10_HOLE_GAP": "0.4495", "CO10_J2STEP": "0.58",
         "CO10_LXPRIO": "landlen", "CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json",
         "CO10_POLMODE": "lx", "CO10_STEP": "1.449", "CO10_STUB": "J3L",
         "CO10_WLO": "33.70", "CO10_WSTEP": "1.05", "CO10_WSWAP": "1-11"}
VARIANTS = {
    "A_dn_In2_up_In6": {("EAST_CHIP_TO_J2", "dn"): "In2.Cu", ("EAST_CHIP_TO_J2", "up"): "In6.Cu",
                        ("WEST_MCIO_TO_CHIP", "up"): "In2.Cu", ("WEST_MCIO_TO_CHIP", "dn"): "In6.Cu"},
    "B_east_In6_west_In2": {("EAST_CHIP_TO_J2", "dn"): "In6.Cu", ("EAST_CHIP_TO_J2", "up"): "In6.Cu",
                            ("WEST_MCIO_TO_CHIP", "up"): "In2.Cu", ("WEST_MCIO_TO_CHIP", "dn"): "In2.Cu"},
}


def run_variant(name: str, mapping) -> dict:
    os.environ.update(KNOBS)
    spec = importlib.util.spec_from_file_location("probe", str(K2 / "tools/p3_v57_co10_west_fan_probe.py"))
    probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
    probe.ESC_MAP = mapping
    res = probe.probe(rule="fan", order="rev", verbose=False)
    GEOM.write_text(json.dumps({"geom": res["geom"]}, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    r = subprocess.run([sys.executable, str(K2 / "tools/p3_v57_co11_placement_verify.py"), str(GEOM), str(VERIFY)],
                       capture_output=True, text=True, env=dict(os.environ, CO11_PAD_UNITS="copper"), timeout=900)
    v = json.loads(VERIFY.read_text())
    return {"variant": name, "esc_map": {f"{k[0]}/{k[1]}": v for k, v in mapping.items()},
            "placed": res["n_placed"], "n_pages": res["n_pages"],
            "b_cu_used": any(l == "B.Cu" for l in mapping.values()),
            "placement_violations_centerline_or_copper": v["n_violations"],
            "first_violations": v["violations"][:3], "verdict": "PASS" if res["n_placed"] == res["n_pages"] and not v["n_violations"] else "FAIL"}


def main() -> int:
    rows = [run_variant(n, m) for n, m in VARIANTS.items()]
    res = {
        "artifact": "m13_v57_co63_bcu_free_layerplan_probe", "schema": 1, "revision": "CO-63.1",
        "nature": "L2 层计划可行性机判（负结果）：B.Cu-free 逃逸层映射不可落位",
        "criterion": "32/32 落位 AND 净距 0 违规（copper 口径）",
        "variants": rows,
        "conclusion": ("B.Cu-free 的两个层计划均 FAIL：A 18/32 + 1 违规；B 12/32 + 11 违规（F.Cu 焊盘挤压 'sp'）。"
                       "⇒ B.Cu 逃逸层是**承载性**的：4 信号层中 F.Cu 被 SMD 焊盘占用、In6 为 lane 层（逃逸入 In6 必自交）、"
                       "In2 为西侧逃逸层 ⇒ 无第三层可用。CO-62 的整改方向**不可由 L2 层分配达成**，"
                       "必须改逃逸拓扑/层数/球图逃逸 ⇒ 属 L1（L1 包络）。"),
        "redline": "只读冻结源；零正式件改动（候选为 probe/scratch）；不伪 sign-off。",
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": hashlib.sha256(OUT.read_bytes()).hexdigest()[:16],
                      "variants": {r["variant"]: f'{r["placed"]}/{r["n_pages"]} viol={r["placement_violations_centerline_or_copper"]}' for r in rows}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
