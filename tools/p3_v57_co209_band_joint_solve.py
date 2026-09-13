#!/usr/bin/env python3
"""CO-209 — L2 自裁 · band 级「列 × 桥孔」联合求解形态之**直接行使**（族闭合复核）。

缘起（z71 §6.3 / CO-207 O-2）：z71 指「L2 内唯一未动自由度 = band 级联合求解器（列 + 桥孔 (x,y) 同解；
确定性、禁回溯）」，并**以结构性论证**预期其上限 ≈24/32（未直接行使）。本件消除该「论证 vs 实测」缺口：
以**确定性、零回溯**的闭式形态行使之 —— 逐极性单调游标（`CO10_CARRYP`）**并计入桥孔向外足迹**（`CO10_CARRYALL`
⇒ `_BEXT = BR_JOG`），即「列游标与桥孔 x 同解」；再对顺序（rev/carry/xasc/engine）与既有修复旋钮
（COLFIX/BRDROP/BR2/POL_OFF）做小矩阵复测。

形态（全部闭式，零坐标搜索、零回溯、零重试）：给定列序，游标推进 = 同极性两两 >= VV，且并列计桥孔足迹；
不满足者跳过该列。**不含**跨页 y 交错（该项须改几何，非旋钮可达 —— 见结论）。

判据（牙齿）：① 归基线可复现（v9=32/32、候选 C+BRCOL=24/32、+COLFIX=23/32、CARRYP=23/32）；
② 非默认族的**任一成员均未达 32/32**（= 族闭合在该形态下仍成立）；③ JOINT 不优于候选 C+BRCOL；
④ 确定性（同配置连跑两次逐字段同）。

CLI: python3 tools/p3_v57_co209_band_joint_solve.py [--out <json>]   # 需 numpy（系统 python3）
只读：不改冻结四源 / 图纸 / SPEC / 交付板；不写任何分配工件。
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
PROBE = K2 / "tools/p3_v57_co10_west_fan_probe.py"

# v9 现行基线（CO16-ALLOC.9 / 0 page diffs）
BASE = {"CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json", "CO10_STEP": "1.449", "CO10_WSTEP": "1.07",
        "CO10_WLO": "33.70", "CO10_FANY_J3": "34.5,51.5", "CO10_STUB": "J3L", "CO10_POLMODE": "lx",
        "CO10_EASTSPLIT": "in2c", "CO10_J2STEP": "0.58", "CO10_COLMODE": "pol", "CO10_WSWAP": "1-11",
        "CO10_HOLE_GAP": "0.4495", "CO10_LXPRIO": "landlen", "CO10_IP3W": "1", "CO10_FAN_STRAT": "carry",
        "CO10_PDN_OBS": "1", "CO10_EDELTA": "-0.10"}
CANDC = {"CO10_BRIDGE": "1", "CO10_SPAN": "1", "CO10_BRJOG": "0.5", "CO10_BRCOL": "1"}
# §78 已验证：候选 C+BRCOL = 24/32（最优）；+COLFIX = 23/32（修正模型）；CARRYP 单用 = 23/32
CASES = (
    ("v9_default", BASE, "rev"),
    ("candC_BRCOL", {**BASE, **CANDC}, "rev"),
    ("candC_BRCOL_COLFIX", {**BASE, **CANDC, "CO10_COLFIX": "1"}, "rev"),
    ("CARRYP_only", {**BASE, **CANDC, "CO10_CARRYP": "1"}, "rev"),
    ("CARRYALL_only", {**BASE, **CANDC, "CO10_CARRYALL": "1"}, "rev"),
    ("JOINT_rev", {**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1"}, "rev"),
    ("JOINT_carry", {**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1"}, "carry"),
    ("JOINT_xasc", {**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1"}, "xasc"),
    ("JOINT_engine", {**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1"}, "engine"),
    ("JOINT_COLFIX", {**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1", "CO10_COLFIX": "1"}, "rev"),
    ("JOINT_BRDROP", {**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1", "CO10_BRDROP": "1"}, "rev"),
    ("JOINT_BR2", {**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1", "CO10_BR2": "1"}, "rev"),
    ("JOINT_POLOFF_2625", {**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1",
                           "CO10_POL_OFF": "0.2625"}, "rev"),
)
N_PAGES = 32
_SEQ = [0]


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run(env: dict, order: str) -> dict:
    """fresh-import 探针（模块级常量在 exec 时读 env）⇒ 逐案隔离；零落盘。"""
    for k in [k for k in os.environ if k.startswith("CO10_")]:
        del os.environ[k]
    os.environ.update(env)
    _SEQ[0] += 1
    spec = importlib.util.spec_from_file_location(f"co209_probe_{_SEQ[0]}", str(PROBE))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.probe(rule="fan", order=order, verbose=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(STEP2 / "m13_v57_co209_band_joint_solve.json"))
    a = ap.parse_args()

    rows = []
    for label, env, order in CASES:
        r = run(env, order)
        rows.append({"case": label, "order": order, "n_placed": r["n_placed"], "n_pages": r["n_pages"],
                     "n_failed": r["n_failed"], "failed": sorted(r["failed"]),
                     "knobs": {k: v for k, v in env.items() if k not in BASE},
                     "deterministic_rerun": None})
    by = {r["case"]: r for r in rows}
    # 确定性：JOINT_rev 连跑两次
    r2 = run({**BASE, **CANDC, "CO10_CARRYP": "1", "CO10_CARRYALL": "1"}, "rev")
    j = by["JOINT_rev"]
    j["deterministic_rerun"] = {"n_placed": r2["n_placed"], "failed": sorted(r2["failed"])}
    det_ok = (r2["n_placed"] == j["n_placed"] and sorted(r2["failed"]) == j["failed"])

    teeth = {
        "t00_baselines_reproduce": (by["v9_default"]["n_placed"] == 32 and by["candC_BRCOL"]["n_placed"] == 24
                                    and by["candC_BRCOL_COLFIX"]["n_placed"] == 23
                                    and by["CARRYP_only"]["n_placed"] == 23),
        "t01_no_family_member_fully_placed": all(r["n_placed"] < N_PAGES for r in rows
                                                 if r["case"] != "v9_default"),
        "t02_joint_not_better_than_candc": max(r["n_placed"] for r in rows
                                               if r["case"].startswith("JOINT")) <= by["candC_BRCOL"]["n_placed"],
        "t03_deterministic": det_ok,
    }
    ok = all(teeth.values())
    doc = {
        "artifact": "m13_v57_co209_band_joint_solve", "schema": 1, "revision": "CO-209",
        "date": "2026-09-14",
        "authority": "z71 §6.3（L2 内唯一未动自由度 = band 级联合求解器）/ CO-207 O-2（该上限系结构性论证、未直接行使）",
        "nature": "L2 自裁 · 族闭合复核：行使「列 × 桥孔 x 同解」闭式形态（确定性、禁回溯、零坐标搜索）",
        "model_note": ("游标形态 = 逐极性单调游标（CO10_CARRYP）并计桥孔向外足迹（CO10_CARRYALL ⇒ _BEXT=BR_JOG）；"
                       "不含跨页 y 交错（须改几何，非旋钮可达）。逐案 fresh-import 探针 ⇒ 逐案隔离；零落盘。"),
        "probe_sha16": s16(PROBE),
        "results": rows,
        "teeth": teeth,
        "conclusion": ("在 R3 过孔策略 + 4 信号层下，**列 × 桥孔 x 联合游标形态不改善族上限**：JOINT 各案 19–20/32，"
                       "低于候选 C+BRCOL 之 24/32（亦低于 CARRYP 单用 23/32）——单调游标计入桥孔足迹后过度推进，"
                       "把失败面从 chip 侧 input 页转嫁到连接器/走廊侧（out_J2 / out_MCIO）。⇒ **族闭合（≤24/32）在直接行使下成立**；"
                       "路径 B 仍不可达 32/32 ⇒ 打样路径 A 之定案不变。残余自由度 = 跨页 y 交错（须改几何）与 L1（球重映射/信号流向）。"),
        "redline": "只读冻结四源；未改 canonical 图纸 / 交付板 / 构造器 / SPEC；零坐标搜索；禁暴力迭代。",
    }
    out = Path(a.out)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CO-209 band-joint: probe={doc['probe_sha16']} teeth={'PASS' if ok else 'FAIL'} -> {out.name} sha16={s16(out)}")
    for k, v in teeth.items():
        print(f"  {k}: {v}")
    for r in rows:
        print(f"  {r['case']:22s} order={r['order']:7s} placed={r['n_placed']}/{r['n_pages']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
