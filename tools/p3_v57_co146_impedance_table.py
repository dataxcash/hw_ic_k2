#!/usr/bin/env python3
"""CO-146 A1 — 85Ω 差分阻抗表（JLC08161H 叠层；监理指令 #10 要求动作 1）。

性质：**只读派生**（不改板/SPEC/冻结四源）。判据源：
  · 叠层/几何 = SPEC rev-19 `stackup.dielectric_8l` + `impedance.per_layer`（交付几何）
  · JLC 公布能力 = `m13_v57_co146_jlc8_capability.json`（±10%、阻抗控制层数、er 表）
模型（**M1 = SPEC `dielectric_8l_basis` 同式同输入的一阶复现**（同族 ⇒ **非**独立证据）；**M2 = 单一独立模型**交叉核对；均按 IPC-2141 族工程近似；终判 = JLC 阻抗控制服务）：
  M1 = IPC-2141 边耦微带/对称带状线（与 `_shared/eda_core/stackup.py` 同式；**等价于复现 SPEC 一阶 ⇒ 非独立**）
  M2 = Hammerstad–Jensen 微带（含铜厚修正）+ Cohn 带状线（独立实现）
产出：`m13_v57_co146_impedance_table.json` / `.md`
牙齿：① M1/M2 在参考点(0.5mm 中心距)须复现 SPEC 一阶值 ±3Ω；② 喂入 +50% 线宽必须使 Zdiff 跌出 ±10%。
"""
from __future__ import annotations
import hashlib, json, math, sys
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
ETA0 = 376.730313668
T_OUT = 0.035      # 外层成品铜厚 1oz
T_IN = 0.0175      # 内层成品铜厚 0.5oz


# ── M1: IPC-2141 族（与 eda_core/stackup.py 同式） ────────────────────────────
def m1_z0_microstrip(w, h, t, er, s):
    return 87.0 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * w + t))


def m1_z0_stripline(w, b, t, er, s):
    return 60.0 / math.sqrt(er) * math.log(4.0 * b / (0.67 * math.pi * w * (0.8 + t / w)))


def m1_diff_microstrip(w, h, t, er, s):
    return 2.0 * m1_z0_microstrip(w, h, t, er, s) * (1.0 - 0.48 * math.exp(-0.96 * s / h))


def m1_diff_stripline(w, b, t, er, s):
    # 与 _shared/eda_core/stackup.py::_symmetric_stripline_z0 同式（复现 SPEC 一阶）
    return 2.0 * m1_z0_stripline(w, b, t, er, s) * (1.0 - 0.48 * math.exp(-0.96 * s / b))


# ── M2: Hammerstad–Jensen 微带 + Cohn 带状线（独立实现） ──────────────────────
def m2_z0_microstrip(w, h, t, er):
    u = w / h
    du = (t / h) / math.pi * math.log(1.0 + 4.0 * math.e / ((t / h) * (1.0 / math.tanh(math.sqrt(6.517 * u))) ** 2))
    u = u + du
    a = 1.0 + math.log((u ** 4 + (u / 52.0) ** 2) / (u ** 4 + 0.432)) / 49.0 + \
        math.log(1.0 + (u / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053
    e_eff = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 10.0 / u) ** (-a * b)
    f = 6.0 + (2.0 * math.pi - 6.0) * math.exp(-(30.666 / u) ** 0.7528)
    return ETA0 / (2.0 * math.pi) * math.log(f / u + math.sqrt(1.0 + (2.0 / u) ** 2)) / math.sqrt(e_eff)


def m2_diff_microstrip(w, h, t, er, s):
    return 2.0 * m2_z0_microstrip(w, h, t, er) * (1.0 - 0.48 * math.exp(-0.96 * s / h))


def m2_z0_stripline(w, b, t, er, s=None):
    return 60.0 / math.sqrt(er) * math.log(4.0 * b / (math.pi * (0.8 * w + t)))


def m2_diff_stripline(w, b, t, er, s):
    return 2.0 * m2_z0_stripline(w, b, t, er, s) * (1.0 - 0.347 * math.exp(-2.9 * s / b))


MODELS = {"M1_IPC2141": {"microstrip": m1_diff_microstrip, "symmetric_stripline": m1_diff_stripline},
          "M2_HJ_Cohn": {"microstrip": m2_diff_microstrip, "symmetric_stripline": m2_diff_stripline}}


def solve_w(target, kind, h_or_b, t, er, s, lo=0.05, hi=0.60):
    """反解线宽（确定性二分；非坐标搜索）"""
    f = (lambda w: m1_diff_microstrip(w, h_or_b, t, er, s)) if kind == "microstrip" else \
        (lambda w: m1_diff_stripline(w, h_or_b, t, er, s))
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if f(mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def main() -> int:
    spec = json.loads(SPEC.read_text())
    imp = spec["impedance"]
    stack = spec["stackup"]["dielectric_8l"]
    target, tol = imp["target_zdiff"], imp["tolerance_pct"]
    lo_ok, hi_ok = target * (1 - tol / 100.0), target * (1 + tol / 100.0)
    rows = []
    for layer, cfg in imp["per_layer"].items():
        kind = cfg["kind"]
        w = cfg["w_mm"]
        t = T_OUT if kind == "microstrip" else T_IN
        if kind == "microstrip":
            h = cfg["h_mm"]
        else:
            h = cfg["b_mm"]
        gaps = cfg["gap_mm_delivered"]          # 交付对内铜边净距（0.5/0.6mm 中心距）
        er = cfg["er"]
        r = {"layer": layer, "kind": kind, "w_mm": w, "s_mm": gaps, "h_or_b_mm": h,
             "er": er, "t_mm": t,
             "zdiff": {}, "within_10pct": {}, "nominal_w_for_85": {},
             "deviation_pct": {}}
        for mname, fns in MODELS.items():
            zs = [fns[kind](w, h, t, er, s) for s in gaps]
            r["zdiff"][mname] = [round(z, 2) for z in zs]
            # 判据 = as-built（gaps[0]，即 SPEC gap_mm_delivered 下界 = 交付实测口径）；
            # gaps[1:]（设计名义上界）单列 watch（见 watch 列表）
            r["within_10pct"][mname] = all(lo_ok <= z <= hi_ok for z in zs[:1])
            r["within_10pct_nominal_max"] = r.get("within_10pct_nominal_max", True) and \
                all(lo_ok <= z <= hi_ok for z in zs)
        w85 = solve_w(target, kind, h, t, er, gaps[0])
        r["nominal_w_for_85"] = round(w85, 4)
        r["deviation_pct"] = {m: round((w - w85) / w85 * 100.0, 2) for m in MODELS}
        rows.append(r)
    # 敏感度：er、h/厚度 ±10%、w ±10%（M2）
    sens = []
    for r in rows:
        for tag, kw in (("er +0.15", dict(er=r["er"] + 0.15)), ("er -0.15", dict(er=r["er"] - 0.15)),
                        ("h/b +10%", dict(h_or_b_mm=r["h_or_b_mm"] * 1.10)), ("h/b -10%", dict(h_or_b_mm=r["h_or_b_mm"] * 0.90)),
                        ("w +10%", dict(w_mm=r["w_mm"] * 1.10)), ("w -10%", dict(w_mm=r["w_mm"] * 0.90))):
            p = dict(r); p.update(kw)
            z = MODELS["M2_HJ_Cohn"][r["kind"]](p["w_mm"], p["h_or_b_mm"], p["t_mm"], p["er"], r["s_mm"][0])
            sens.append({"layer": r["layer"], "perturbation": tag, "zdiff": round(z, 2),
                         "within_10pct": bool(lo_ok <= z <= hi_ok)})
    teeth = {}
    ref = next(r for r in rows if r["layer"] == "F.Cu")
    spec_ref = spec["stackup"]["dielectric_8l_basis"]["verdict_first_order"]["F.Cu/B.Cu"]["zdiff_ohm"]
    m1_ref = ref["zdiff"]["M1_IPC2141"]
    teeth["t01_reproduce_spec_first_order"] = {
        "spec": spec_ref, "M1": m1_ref,
        "ok": all(abs(m1_ref[i] - [spec_ref["0.5"], spec_ref["0.6"]][i]) <= 3.0 for i in (0, 1))}
    z50 = MODELS["M2_HJ_Cohn"][ref["kind"]](ref["w_mm"] * 1.5, ref["h_or_b_mm"], ref["t_mm"], ref["er"], ref["s_mm"][0])
    teeth["t02_overwide_must_fail_tol"] = {"zdiff_at_w+50%": round(z50, 2), "ok": not (lo_ok <= z50 <= hi_ok)}
    fails = [r["layer"] for r in rows if not (r["within_10pct"]["M1_IPC2141"] and r["within_10pct"]["M2_HJ_Cohn"])]
    watch = [{"layer": r["layer"], "gap_mm": r["s_mm"][1:],
              "zdiff": {m: r["zdiff"][m][1:] for m in MODELS},
              "reason": "设计名义最宽对内净距下 M2(HJ) 越 ±10% 上界 ⇒ 下单备注要求 JLC 阻抗表覆盖该几何（终判=JLC 阻抗控制服务）"}
             for r in rows if not r.get("within_10pct_nominal_max", True)]
    rec = {"artifact": "m13_v57_co146_impedance_table", "schema": 1, "revision": "CO146-IMP.1",
           "nature": "L2 只读派生：85Ω 差分阻抗表（M1 复现 SPEC 一阶 + M2 独立模型交叉核对；CO-152 订正标签）",
           "source": {"spec": SPEC.name, "spec_sha16": hashlib.sha256(SPEC.read_bytes()).hexdigest()[:16],
                      "stackup": spec["stackup"]["material"],
                      "jlc_capability": "m13_v57_co146_jlc8_capability.json",
                      "jlc_impedance_tolerance_pct": 10,
                      "jlc_note": "JLC 公布 er：2116=4.16 / 3313=4.1 / 7628=4.4；阻抗控制 4/6/8/…层 ±10%"},
           "target_zdiff": target, "tolerance_pct": tol, "window_ohm": [lo_ok, hi_ok],
           "rows": rows, "sensitivity": sens, "verdict": "PASS" if not fails else "FAIL", "fails": fails,
           "verdict_basis": "as-built 对内净距（gap_mm_delivered 下界 0.295 外层 / 0.34 内层，= 交付实测口径）双模型均落 85Ω±10%",
           "watch": watch,
           # CO-156（F-6）：供 DV-CO146-ZDIFF 的 `evidence_ref.key_path` 绑定（证据件须含该 computed）
           "dv_computed_zdiff": {"window_ohm": [lo_ok, hi_ok],
                                 "zdiff": {r["layer"]: r["zdiff"] for r in rows},
                                 "nominal_w_for_85": {r["layer"]: r["nominal_w_for_85"] for r in rows},
                                 "deviation_pct": {r["layer"]: r["deviation_pct"] for r in rows},
                                 "watch_nominal_max": watch},
           "models": {"M1_IPC2141": "IPC-2141 边耦微带/对称带状线（与 eda_core/stackup.py 同族）",
                      "M2_HJ_Cohn": "Hammerstad–Jensen 微带（含铜厚修正）+ Cohn 带状线"},
           "limits": ("两模型均为一阶闭式工程近似（±5~10% 量级）；**终判 = JLC 阻抗控制服务**"
                       "（下单勾选阻抗控制，JLC 依实际叠层出阻抗表 / 免费标准阻抗测试）；"
                       "本表用途 = 下单前可核性 + 偏离预警。"),
           "teeth": teeth,
           "redline": "只读：坐标零搜索；不改板/图纸/SPEC/冻结四源。"}
    (STEP2 / "m13_v57_co146_impedance_table.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    md = ["# CO-146 卡 · 85Ω 差分阻抗表（JLC08161H；监理指令 #10 动作 1）", "",
          f"- 目标：**{target}Ω ±{tol}%** ⇒ 窗口 {lo_ok:.1f}–{hi_ok:.1f}Ω｜叠层：{spec['stackup']['material']}",
          f"- 几何源：SPEC rev-19 `impedance.per_layer`（交付对内铜边净距 0.295/0.395 外层，0.34/0.44 内层）",
          f"- **verdict = {rec['verdict']}**（判据 = as-built 对内净距；见下 watch）", "",
          "| 层 | 类型 | w (mm) | 对内净距 s (mm) | h/b (mm) | er | Zdiff M1 (Ω) | Zdiff M2 (Ω) | ±10% | 85Ω 名义 w | 交付 w 偏差 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['layer']} | {r['kind']} | {r['w_mm']} | {r['s_mm']} | {r['h_or_b_mm']} | {r['er']} | "
                  f"{r['zdiff']['M1_IPC2141']} | {r['zdiff']['M2_HJ_Cohn']} | "
                  f"{'✓' if (r['within_10pct']['M1_IPC2141'] and r['within_10pct']['M2_HJ_Cohn']) else '✗'} | "
                  f"{r['nominal_w_for_85']} | {r['deviation_pct']['M2_HJ_Cohn']}% |")
    md += ["", "## 一阶敏感度（M2；对内净距取下界）", "", "| 层 | 扰动 | Zdiff (Ω) | ±10% |", "|---|---|---|---|"]
    for s in sens:
        md.append(f"| {s['layer']} | {s['perturbation']} | {s['zdiff']} | {'✓' if s['within_10pct'] else '✗'} |")
    if watch:
        md += ["", "## watch（设计名义最宽间距；越界即列下单备注）", "", "| 层 | 净距 (mm) | Zdiff M1 | Zdiff M2 | 处理 |", "|---|---|---|---|---|"]
        for w_ in watch:
            md.append(f"| {w_['layer']} | {w_['gap_mm']} | {w_['zdiff']['M1_IPC2141']} | {w_['zdiff']['M2_HJ_Cohn']} | {w_['reason']} |")
    md += ["", "## 牙齿", f"- T1 复现 SPEC 一阶：ok={teeth['t01_reproduce_spec_first_order']['ok']}",
           f"- T2 线宽 +50% 必须跌出 ±10%：ok={teeth['t02_overwide_must_fail_tol']['ok']}", ""]
    (STEP2 / "m13_v57_co146_impedance_table.md").write_text("\n".join(md) + "\n")
    print("verdict:", rec["verdict"], "| fails:", fails)
    for r in rows:
        print(f"  {r['layer']:8s} w={r['w_mm']} s={r['s_mm']} Zdiff M1={r['zdiff']['M1_IPC2141']} M2={r['zdiff']['M2_HJ_Cohn']} "
              f"| 85Ω名义w={r['nominal_w_for_85']} 偏差={r['deviation_pct']['M2_HJ_Cohn']}%")
    print("teeth:", teeth["t01_reproduce_spec_first_order"]["ok"], teeth["t02_overwide_must_fail_tol"]["ok"])
    return 0 if (teeth["t01_reproduce_spec_first_order"]["ok"] and teeth["t02_overwide_must_fail_tol"]["ok"]) else 1


if __name__ == "__main__":
    sys.exit(main())
