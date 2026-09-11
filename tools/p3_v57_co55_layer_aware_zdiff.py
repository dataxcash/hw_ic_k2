#!/usr/bin/env python3
"""CO-55：【L2/SI 自裁】层感知 Zdiff → **反向下达 8L 叠层要求**（把"等板厂输入"改为"定叠层要求"）。

问题（CO-53/CO-54）：SPEC 只有一个阻抗模型（F.Cu 微带 H1=5.0mil/Er1=4.3）与一个 (w,gap)，
却被套用到全部信号层；交付 34 对中 32 对的决定性平行段在 In2/In6（内层），且 8L 介质表缺失 ⇒ 无法判合规。

本工具（L2 职权 = 叠层分配 + SI 物理承载，LAYOUT_CONSTITUTION 第二章）：
  1. 按 LID.1 层序解析每个信号层的**参考结构**（微带 / 对称带状线 / 单参考 / 无参考）；
  2. 用交付几何（CO-54 audit 实测）反解**所需介质厚度** → 给出 8L 叠层要求（含 ±10% 带）；
  3. 校核 1.6mm 厚度闭合（用 JLC 官方 prepreg/core 标准厚度）；
  4. `--build <json>`：拿到真实板厂叠层即可判每层是否达标并产 ECO rev-4 内容。
模型：`_shared/eda_core/stackup.py`（IPC-2141）——与 SPEC 自陈基准同源（datum 85.05 vs 85.1）。
**一阶**：终判 = SI9000 + 板厂阻抗券（SPEC `coupon_required=true`）。

输出：m13_v57_co55_layer_impedance_requirement.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
ROOT = K2.parent
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-4.json"   # CO-56: 现行为 rev-4
AUDIT = STEP2 / "m13_v57_co54_spec_delivery_audit.json"
OUT = STEP2 / "m13_v57_co55_layer_impedance_requirement.json"
sys.path.insert(0, str(ROOT / "_shared"))
from eda_core.stackup import _edge_coupled_microstrip_z0 as MS, _symmetric_stripline_z0 as SL  # noqa: E402

DATUM = {"h_mm": 0.127, "er": 4.3, "t_mm": 0.035, "w_mm": 0.205, "s_mm": 0.175, "claimed": 85.1}
T_OUT, T_IN = 0.035, 0.0175
ER_PP, ER_CORE = 4.16, 3.99          # 南亚 NP-155F / JLC 官方 prepreg(2116)=4.16, core=3.99
# LID.1 层序（F/In1/In2/In3/In4/In5/In6/B）与参考结构
LAYERS = {
    "F.Cu":  {"kind": "microstrip", "refs": ["In1.Cu"], "gap_key": "d(F-In1)"},
    "In2.Cu": {"kind": "stripline", "refs": ["In1.Cu", "In3.Cu"], "gap_key": "b(In1-In3)"},
    "In6.Cu": {"kind": "microstrip", "refs": ["In5.Cu"], "gap_key": "d(In5-In6)"},
    "B.Cu":  {"kind": "unreferenced", "refs": [], "gap_key": None},
}
# JLC 官方压合后 prepreg 厚度（pcb 阻抗页实抓）
PP_2116, PP_3313 = 0.1164, 0.0994
PP = {"1080": 0.0764, "2116": PP_2116, "3313": PP_3313, "7628": 0.2008}
CORE = {"0.35": 0.35, "0.40": 0.40, "0.5133": 0.5133}
TOTAL_MM = 1.6
# ── L2 裁定目标（本工具输出；见 record CO-55）──
RULED = {
    "F.Cu":   {"gap_key": "d(F-In1)",  "var_mm": PP_2116, "er": 4.16, "t_mm": T_OUT, "kind": "microstrip",
               "material": "2116*1 (0.1164mm)"},
    "In6.Cu": {"gap_key": "d(In5-In6)", "var_mm": PP_3313, "er": 4.10, "t_mm": T_IN, "kind": "microstrip",
               "material": "3313*1 (0.0994mm)"},
    "In2.Cu": {"gap_key": "b(In1-In3)", "var_mm": 0.72, "er": 3.99, "t_mm": T_IN, "kind": "stripline",
               "material": "core 0.36 x2 (sym.)"},
}


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def zdiff(kind: str, w: float, s: float, var: float, er: float, t: float) -> float:
    return MS(w, var, t, er, s) if kind == "microstrip" else SL(w, var, t, er, s)


def solve_band(kind: str, w: float, gaps: list[float], t: float, er: float, target: float,
               tol: float = 0.10, lo: float = 0.05, hi: float = 1.60, step: float = 0.0005) -> dict:
    """求变量区间 [lo,hi] 使**全部** gap 的 Zdiff ∈ target±tol。"""
    ok = []
    n = int(round((hi - lo) / step))
    for i in range(n + 1):
        v = round(lo + i * step, 4)
        zs = [zdiff(kind, w, s, v, er, t) for s in gaps]
        if all(abs(z - target) <= tol * target for z in zs):
            ok.append(v)
    return {"var_lo_mm": ok[0] if ok else None, "var_hi_mm": ok[-1] if ok else None,
            "nonempty": bool(ok)}


def solve_var(kind: str, w: float, s: float, t: float, er: float, target: float,
              lo: float, hi: float, step: float = 0.0005) -> float | None:
    best = None
    n = int(round((hi - lo) / step))
    for i in range(n + 1):
        v = lo + i * step
        z = zdiff(kind, w, s, v, er, t)
        if best is None or abs(z - target) < abs(best[1] - target):
            best = (round(v, 4), z)
    return best[0] if best else None


def solve_w(kind: str, s: float, var: float, t: float, er: float, target: float) -> dict:
    best = None
    for i in range(4, 41):
        w = i / 100
        z = zdiff(kind, w, s, var, er, t)
        if best is None or abs(z - target) < abs(best[1] - target):
            best = (w, z)
    return {"w_mm": best[0], "zdiff_ohm": round(best[1], 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", type=Path, default=None,
                    help='真实/候选 8L 叠层 json：{"d(F-In1)":mm,"b(In1-In3)":mm,"d(In5-In6)":mm,"er_pp":..,"er_core":..}')
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    target = spec["impedance"]["target_zdiff"]
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    w = audit["delivered"]["intra_pair"]["per_layer_values_mm_counts"]
    # 交付对内 gap（中心距 − 宽）：主导值 0.295（0.5 中心）与 0.395（0.6 中心）
    # 主导对内中心距档位（按出现次数 ≥5 且属布线档 0.5/0.6）→ 得交付 gap 档
    cnt: dict[float, int] = {}
    for layer in w.values():
        for k, n in layer.items():
            cnt[float(k)] = cnt.get(float(k), 0) + n
    gaps = sorted({round(c - 0.205, 3) for c, n in cnt.items() if n >= 30 and 0.45 <= c <= 0.65})
    datum = MS(DATUM["w_mm"], DATUM["h_mm"], DATUM["t_mm"], DATUM["er"], DATUM["s_mm"])

    req, verdict = {}, {}
    for layer, meta in LAYERS.items():
        if meta["kind"] == "unreferenced":
            verdict[layer] = {"conform": None, "status": "NOT_CONTROLLED_UNREFERENCED",
                              "note": "参考层为信号层（In6），无平面参考 ⇒ 非阻抗控制层"}
            continue
        t = T_OUT if layer in ("F.Cu", "B.Cu") else T_IN
        er = ER_PP if meta["kind"] == "microstrip" else ER_CORE
        band = solve_band(meta["kind"], 0.205, gaps, t, er, target)
        lead = solve_var(meta["kind"], 0.205, max(gaps), t, er, target,
                         0.05, 1.6) if meta["kind"] == "stripline" else solve_var(
            meta["kind"], 0.205, max(gaps), t, er, target, 0.05, 0.4)
        req[meta["gap_key"]] = {"layers": layer, "kind": meta["kind"], "refs": meta["refs"],
                               "ruled_target_mm": {"d(F-In1)": PP["2116"], "b(In1-In3)": 0.72,
                                                   "d(In5-In6)": PP["2116"]}[meta["gap_key"]],
                               "var_band_mm": [band["var_lo_mm"], band["var_hi_mm"]],
                               "var_for_85_at_gap%.3f" % max(gaps): lead,
                               "gaps_mm": gaps, "er": er, "t_mm": t,
                               "basis": f"交付 w=0.205, gap∈{gaps} → Zdiff 85±10% (IPC-2141 一阶)"}
    # 参考（非判据）实况：按 SPEC 自陈 H1=5.0mil / 8L 若沿用 6L 型 b≈0.599
    for layer, var in (("F.Cu", 0.127), ("In2.Cu", 0.599), ("In6.Cu", 0.127)):
        meta, t = LAYERS[layer], (T_OUT if layer in ("F.Cu", "B.Cu") else T_IN)
        er = ER_PP if meta["kind"] == "microstrip" else ER_CORE
        verdict[layer] = {"kind": meta["kind"], "var_mm": var, "er": er,
                          "zdiff_ohm": {str(s): round(zdiff(meta["kind"], 0.205, s, var, er, t), 2) for s in gaps},
                          "pct_vs_85": {str(s): round(100 * (zdiff(meta["kind"], 0.205, s, var, er, t) / target - 1), 1) for s in gaps}}

    # 1.6mm 厚度闭合示例（标准料：F/In6 用 2116×1；In2 对称核心；余隙 1080×2 等）
    ex = {"d(F-In1)": PP_2116, "d(In1-In2)": 0.36, "d(In2-In3)": 0.36,
          "d(In3-In4)": round(2 * PP["1080"], 4), "d(In4-In5)": round(2 * PP["1080"], 4),
          "d(In5-In6)": PP_3313}
    cu = 2 * T_OUT + 6 * T_IN
    ex["d(In6-B)"] = round(TOTAL_MM - (cu + sum(ex.values())), 4)   # 自由余隙（板厂可用料微调）
    tot = round(cu + sum(ex.values()), 4)
    closure = {"copper_mm": round(cu, 4), "dielectric_mm": round(sum(ex.values()), 4),
               "total_mm": tot, "target_mm": TOTAL_MM, "delta_mm": round(tot - TOTAL_MM, 4),
               "ok": abs(tot - TOTAL_MM) <= 0.05, "materials": ex}

    rec = {
        "artifact": "m13_v57_co55_layer_impedance_requirement", "schema": 1, "revision": "CO-55.1",
        "authority": "L2/SI 自裁（LAYOUT_CONSTITUTION 第二章：叠层分配 + SI 物理承载）",
        "nature": "反向下达 8L 叠层要求（不等板厂输入）；零几何改动、不 bump SPEC",
        "model": {"source": "_shared/eda_core/stackup.py", "method": "IPC-2141 (edge-coupled microstrip / symmetric stripline)",
                  "signoff": False, "required_for_signoff": "SI9000 + 板厂阻抗券"},
        "spec_datum_check": {**DATUM, "model_zdiff_ohm": round(datum, 2)},
        "delivered": {"w_mm": 0.205, "intra_gap_mm": gaps, "source": "CO-54 audit 实测"},
        "layer_structure": LAYERS,
        "requirement": req,
        "verdict_if_spec_6L_like": verdict,
        "thickness_closure_example": closure,
        "ruling": {
            "R0": "单 (w,gap) 跨层通用不成立：0.205 是 **F.Cu 微带**解，套到 In2 带状线会低 10–25%。",
            "R1_build_requirement": "8L 叠层要求（L2 下达）：**d(F.Cu–In1.Cu) = 0.1164mm（JLC 2116×1，Er 4.16）；d(In5.Cu–In6.Cu) = 0.0994mm（JLC 3313×1，Er 4.10）**（两者带内分别见 requirement.var_band_mm，差异源于外/内层铜厚 1oz vs 0.5oz）；"
                                    "**b(In1.Cu–In3.Cu) = 0.70–0.75mm（目标 0.72，对称 d(In1–In2)=d(In2–In3)=0.36 core）**；余隙 d(In3–In4)/d(In4–In5)≈0.1528（1080×2）、d(In6–B) 为自由余隙按 1.6mm 闭合（见 thickness_closure_example）。",
            "R2_fallback": "若板厂标准 8L 无法给出 b ≥ 0.582（±10% 下限）⇒ In2 线宽须按 w*(b) 重导（见 fallback_w_table）⇒ 触发 W3/L4/L5 re-open（L2 授权；变更单 + 版本 bump）。",
            "R3_unreferenced": "B.Cu 参考层为 In6（信号）⇒ 判 **B.Cu = 非阻抗控制层**（低速/边带/铺铜）；In6 阻抗关键段下方 B.Cu 不得并行跨铺铜/走线（否则单参考假设失效）。",
            "R4_eco4": "SPEC ECO rev-4 内容：stackup 8L 逐层介质表 + **分层阻抗几何**（F/In2/In6 各层口径）+ `p_gap` 语义 = **下限**（DRC clearance 0.175）而几何真源 = 交付 (0.205, 0.295)；走廊步距 1.2 与交付网格一致（CO-54 F3）。",
            "R5_closure": "CO-53/CO-54 的**输入缺口取消**：不再索取板厂表，改为下达本要求 + 板厂券终判（SPEC coupon_required=true）。",
        },
        "conformance": "NOT_DEMONSTRATED_PENDING_BUILD_AND_COUPON",
        "gate_impact": "none（本件零几何/阈值改动；ECO rev-4 落地后按变更单重跑）",
    }
    fb = []
    for b in (0.35, 0.40, 0.45, 0.50, 0.55, 0.60):
        fb.append({"b_mm": b, **solve_w("stripline", 0.295, b, T_IN, ER_CORE, target)})
    rec["fallback_w_table"] = fb
    # 全量交付 gap 档（含少数局部档）下，对**裁定目标厚度**逐档评估（透明报告，不隐藏）
    all_gaps = sorted({round(c - 0.205, 3) for c in cnt if 0.45 <= c <= 0.70})
    rec["ruled_target_evaluation"] = {
        lyr: {"gap_key": m["gap_key"], "material": m["material"], "var_mm": m["var_mm"], "er": m["er"],
              "all_delivered_gaps_mm": all_gaps,
              "zdiff_ohm": {str(g): round(zdiff(m["kind"], 0.205, g, m["var_mm"], m["er"], m["t_mm"]), 2) for g in all_gaps},
              "within_10pct": {str(g): abs(zdiff(m["kind"], 0.205, g, m["var_mm"], m["er"], m["t_mm"]) - target) <= 0.10 * target
                               for g in all_gaps}}
        for lyr, m in RULED.items()}

    if a.build is not None:
        bd = json.loads(a.build.read_text(encoding="utf-8"))
        chk = {}
        for layer, meta in LAYERS.items():
            if meta["kind"] == "unreferenced":
                continue
            var = bd.get(meta["gap_key"])
            if var is None:
                continue
            t = T_OUT if layer in ("F.Cu", "B.Cu") else T_IN
            er = ER_PP if meta["kind"] == "microstrip" else ER_CORE
            zs = {str(s): round(zdiff(meta["kind"], 0.205, s, float(var), er, t), 2) for s in gaps}
            chk[layer] = {"var_mm": var, "zdiff_ohm": zs,
                          "within_10pct": {k: abs(v - target) <= 0.10 * target for k, v in zs.items()}}
        rec["build_evaluation"] = {"path": str(a.build), "sha16": sha16(a.build), "per_layer": chk,
                                   "all_within_10pct": all(all(v["within_10pct"].values()) for v in chk.values())}

    a.out.write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(a.out), "sha16": sha16(a.out), "datum": round(datum, 2),
                      "gaps": gaps, "requirement": {k: v["var_band_mm"] for k, v in req.items()},
                      "thickness_ok": closure["ok"], "total_mm": closure["total_mm"],
                      "fallback_w": {str(r["b_mm"]): r["w_mm"] for r in fb},
                      "build_eval": rec.get("build_evaluation", {}).get("all_within_10pct", "not_run")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
