#!/usr/bin/env python3
"""CO-71：【L2 叠层分配/SI 物理承载】方案(a) 层结构下的**逐层 Zdiff 要求 + 板厂券判定接口**（rev-2）。

问题：CO-55 的 `--build` 判定 harness 绑定**旧层结构**（F 微带 / In2 带状线 / In6 单参考 / B 无参考）。
方案(a)（CO-68，LID REV6）层结构已变为 F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)：
  F 微带(ref In1) / In2 对称带状线(ref In1+In3) / In5 对称带状线(ref In4+In6) / B 微带(ref In6)
⇒ 旧 harness 对 In5/B 失效。本件给出**方案(a) 专用**要求表 + `w*(b)` 回退表 + `--build` 判定入口
（handoff §6.3「板厂给真实叠层 ⇒ 逐层判定」的可执行接口）。

只读冻结源；不改板/图纸/阈值；一阶 IPC-2141，终判 = SI9000 + 板厂券。
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
ROOT = K2.parent
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co71_layer_zdiff_requirement.json"
sys.path.insert(0, str(ROOT / "_shared"))
from eda_core.stackup import _edge_coupled_microstrip_z0 as MS, _symmetric_stripline_z0 as SL  # noqa: E402

T_OUT, T_IN = 0.035, 0.0175
CU = 2 * T_OUT + 6 * T_IN
TOTAL, G4_MIN = 1.6, 0.0764
ER_PP, ER_CORE = 4.16, 3.99
CENTERS = (0.5, 0.6)
TARGET, TOL = 85.0, 0.10
# 方案(a) 层结构（LID REV6）：signal -> kind/refs/var_key
LAYERS = {
    "F.Cu":  {"kind": "microstrip", "refs": ["In1.Cu"], "var_key": "d(F.Cu-In1.Cu)", "w": 0.205, "er": ER_PP, "t": T_OUT, "material": "2116*1"},
    "In2.Cu": {"kind": "stripline", "refs": ["In1.Cu", "In3.Cu"], "var_key": "b(In1.Cu-In3.Cu)", "w": 0.16, "er": ER_CORE, "t": T_IN, "material": "core 0.25*2"},
    "In5.Cu": {"kind": "stripline", "refs": ["In4.Cu", "In6.Cu"], "var_key": "b(In4.Cu-In6.Cu)", "w": 0.16, "er": ER_CORE, "t": T_IN, "material": "core 0.25*2"},
    "B.Cu":  {"kind": "microstrip", "refs": ["In6.Cu"], "var_key": "d(In6.Cu-B.Cu)", "w": 0.205, "er": ER_PP, "t": T_OUT, "material": "2116*1"},
}


def s16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def z(kind, w, s, var, er, t):
    return MS(w, var, t, er, s) if kind == "microstrip" else SL(w, var, t, er, s)


def var_band(meta, target=TARGET, lo=0.05, hi=1.60, step=0.0005):
    ok = []
    for i in range(int(round((hi - lo) / step)) + 1):
        v = round(lo + i * step, 4)
        if all(abs(z(meta["kind"], meta["w"], c - meta["w"], v, meta["er"], meta["t"]) - target) <= TOL * target
               for c in CENTERS):
            ok.append(v)
    return [ok[0], ok[-1]] if ok else [None, None]


def solve_w(meta, var, target=TARGET):
    best = None
    for i in range(80, 321):
        w = i / 1000
        zz = z(meta["kind"], w, 0.5 - w, var, meta["er"], meta["t"])
        if best is None or abs(zz - target) < abs(best[1] - target):
            best = (round(w, 3), zz)
    return {"w_mm": best[0], "zdiff_ohm": round(best[1], 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", type=Path, default=None,
                    help='板厂叠层 json：{"d(F.Cu-In1.Cu)":mm,"b(In1.Cu-In3.Cu)":mm,"b(In4.Cu-In6.Cu)":mm,"d(In6.Cu-B.Cu)":mm}')
    a = ap.parse_args()
    req, verdict = {}, {}
    for lyr, m in LAYERS.items():
        band = var_band(m)
        lead = max(band[1], 0.05) if band[0] is not None else None
        req[lyr] = {"kind": m["kind"], "refs": m["refs"], "var_key": m["var_key"],
                    "var_band_mm": band, "material_example": m["material"], "er": m["er"], "t_mm": m["t"],
                    "basis": f"交付 w={m['w']}, 对内中心 {CENTERS} ⇒ Zdiff {TARGET}±{int(TOL*100)}% (IPC-2141 一阶)"}
        verdict[lyr] = {"zdiff_ohm": {str(c): round(z(m["kind"], m["w"], c - m["w"], 0.1164 if m["kind"] == "microstrip" else 0.50, m["er"], m["t"]), 2)
                                      for c in CENTERS}}
    d = {"d(F.Cu-In1.Cu)": 0.1164, "d(In1.Cu-In2.Cu)": 0.25, "d(In2.Cu-In3.Cu)": 0.25,
         "d(In4.Cu-In5.Cu)": 0.25, "d(In5.Cu-In6.Cu)": 0.25, "d(In6.Cu-B.Cu)": 0.1164}
    d["d(In3.Cu-In4.Cu)"] = round(TOTAL - (CU + sum(d.values())), 4)
    closure = {"copper_mm": round(CU, 4), "dielectric_mm": round(sum(d.values()), 4),
               "total_mm": round(CU + sum(d.values()), 4), "ok": abs(CU + sum(d.values()) - TOTAL) <= 0.005,
               "dielectric": d}
    ruled = {"d(F.Cu-In1.Cu)": 0.1164, "b(In1.Cu-In3.Cu)": 0.50, "b(In4.Cu-In6.Cu)": 0.50, "d(In6.Cu-B.Cu)": 0.1164}
    fb = [{"b_mm": b, **solve_w(LAYERS["In2.Cu"], b)} for b in (0.35, 0.40, 0.45, 0.50, 0.55, 0.60)]
    rec = {"artifact": "m13_v57_co71_layer_zdiff_requirement", "schema": 1, "revision": "CO-71.1",
           "nature": "方案(a) 层结构下的逐层 Zdiff 要求 + 板厂券判定接口（CO-55 harness 的 rev-2）",
           "authority": "L2 叠层分配 + SI 物理承载（LAYOUT_CONSTITUTION 第二章；CO-67 裁定 L2）",
           "supersedes_scope": "CO-55 requirement 的**层结构**（旧 F/In2/In6/B ⇒ 新 F/In2/In5/B）；阀值/目标不变",
           "model": {"source": "_shared/eda_core/stackup.py", "method": "IPC-2141 一阶", "signoff": False,
                     "required": "SI9000 + 板厂阻抗券（coupon_required=true）"},
           "layer_structure": {k: {"kind": v["kind"], "refs": v["refs"], "w_mm": v["w"]} for k, v in LAYERS.items()},
           "requirement": req, "ruled_target_mm": ruled, "verdict_at_ruled_target": verdict,
           "fallback_w_table": fb, "thickness_closure": closure,
           "checks": {"all_layers_referenced": all(v["refs"] for v in LAYERS.values()),
                      "closure_ok": closure["ok"],
                      "all_var_band_nonempty": all(v["var_band_mm"][0] is not None for v in req.values())},
           "redline": "只读冻结源；不改板/图纸/阈值；一阶未经 SI9000/券。"}
    if a.build is not None:
        bd = json.loads(a.build.read_text(encoding="utf-8"))
        ev = {}
        for lyr, m in LAYERS.items():
            v = bd.get(m["var_key"])
            if v is None:
                ev[lyr] = {"status": "MISSING_VAR", "key": m["var_key"]}
                continue
            zs = {str(c): round(z(m["kind"], m["w"], c - m["w"], float(v), m["er"], m["t"]), 2) for c in CENTERS}
            ev[lyr] = {"var_mm": v, "zdiff_ohm": zs,
                       "within_tol": {k: abs(x - TARGET) <= TOL * TARGET for k, x in zs.items()}}
        rec["build_evaluation"] = {"path": str(a.build), "sha16": s16(a.build), "per_layer": ev,
                                   "all_within_tol": all(all(v.get("within_tol", {}).values()) for v in ev.values()
                                                         if "within_tol" in v)}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": s16(OUT),
                      "checks": rec["checks"],
                      "var_bands": {k: v["var_band_mm"] for k, v in req.items()},
                      "fallback_w": {str(r["b_mm"]): r["w_mm"] for r in fb},
                      "build": rec.get("build_evaluation", {}).get("all_within_tol", "not_run")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
