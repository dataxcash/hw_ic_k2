#!/usr/bin/env python3
"""CO-68：【L2 叠层分配】执行方案(a) —— 铜厚自洽修正 + LID REV6 + SPEC rev-5 发射（版本化，原件不动）。

承接 CO-66（方案(a) 归口 L2）与 CO-67（红线张力一次性裁定 = L2）。
本件**修正 CO-66 的闭合口径**：CO-66 令 `g4 = 1.6 - 2h_o - 2b` 未扣铜厚（0.175mm），
与 CO-55 明列 `copper 0.175 + dielectric 1.425 = 1.6000` 不一致 ⇒ CO-66 的「10 组可行」为**高估**。
修正：**介质预算 = 1.6 - 0.175 = 1.425**，闭合 = 2*h_o + 2*b_s + g4 = 1.425，g4 >= 0.0764（1080 单张）。
在此口径下重解：内层可行线宽收窄到 **w_s <= ~0.165**（CO-66 的 0.19/0.205 行实为**不可行**）。

产出（全部新版本文件；`SPEC_k2_v4.json`/`spec-rev-2/3/4`、`layer_intent_rev1..5`、冻结板均**未动**）：
  1. `m13_v57_layer_intent_rev6.json`（LID REV6：signal = F/In2/In5/B；In1/In3/In6=GND，In4=P3V3）
  2. `SPEC_k2_v4.spec-rev-5.json`（叠层用途 + 逐层介质表 + `impedance.per_layer` 新线宽口径；数值阈值不变）
  3. 本件 JSON 记录（修正证明 + 设计点 + 逐层 Z 校核 + 闭合）
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
ROOT = K2.parent
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC4 = L3 / "SPEC_k2_v4.spec-rev-4.json"
LID5 = STEP2 / "m13_v57_layer_intent_rev5.json"
OUT_JSON = STEP2 / "m13_v57_co68_option_a_execute_derive.json"
OUT_MD = STEP2 / "m13_v57_CO68_L2_option_a_execute.md"
OUT_LID6 = STEP2 / "m13_v57_layer_intent_rev6.json"
OUT_SPEC5 = L3 / "SPEC_k2_v4.spec-rev-5.json"
sys.path.insert(0, str(ROOT / "_shared"))
from eda_core.stackup import _edge_coupled_microstrip_z0 as MS, _symmetric_stripline_z0 as SL  # noqa: E402

T_OUT, T_IN = 0.035, 0.0175
CU = 2 * T_OUT + 6 * T_IN                 # 0.175
TOTAL, G4_MIN = 1.6, 0.0764
ER_PP, ER_CORE = 4.16, 3.99
CENTERS = (0.5, 0.6)                     # 交付对内中心距档（CO-54）
BAND = 0.10                              # 85 ± 10%


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    spec4 = json.loads(SPEC4.read_text(encoding="utf-8"))
    lid5 = json.loads(LID5.read_text(encoding="utf-8"))
    spec4_before, lid5_before = sha16(SPEC4), sha16(LID5)

    # ── 设计点（修正口径下的标准料叠层 + 线宽）─────────────────────────────
    d = {"d(F.Cu-In1.Cu)": 0.1164, "d(In1.Cu-In2.Cu)": 0.25, "d(In2.Cu-In3.Cu)": 0.25,
         "d(In4.Cu-In5.Cu)": 0.25, "d(In5.Cu-In6.Cu)": 0.25, "d(In6.Cu-B.Cu)": 0.1164}
    d["d(In3.Cu-In4.Cu)"] = round(TOTAL - (CU + sum(d.values())), 4)     # 自由闭合余隙 g4
    h_o = d["d(F.Cu-In1.Cu)"]
    b_s = round(d["d(In1.Cu-In2.Cu)"] + d["d(In2.Cu-In3.Cu)"], 4)
    g4 = d["d(In3.Cu-In4.Cu)"]
    closure = {"copper_mm": round(CU, 4), "dielectric_mm": round(sum(d.values()), 4),
               "total_mm": round(CU + sum(d.values()), 4), "target_mm": TOTAL,
               "delta_mm": round(CU + sum(d.values()) - TOTAL, 4), "ok": abs(CU + sum(d.values()) - TOTAL) <= 0.005}
    w_outer, w_inner = 0.205, 0.16


    def z_outer(w):
        return [round(MS(w, h_o, T_OUT, ER_PP, c - w), 2) for c in CENTERS]


    def z_inner(w):
        return [round(SL(w, b_s, T_IN, ER_CORE, c - w), 2) for c in CENTERS]

    zo, zi = z_outer(w_outer), z_inner(w_inner)
    inband = lambda zs: all(abs(z - 85) <= BAND * 85 for z in zs)
    verdict = {"F.Cu/B.Cu": {"kind": "microstrip(ref In1 / In6)", "w_mm": w_outer, "h_mm": h_o,
                             "zdiff_ohm": dict(zip(map(str, CENTERS), zo)), "within_10pct": inband(zo)},
               "In2.Cu/In5.Cu": {"kind": "symmetric stripline(ref In1+In3 / In4+In6)", "w_mm": w_inner,
                                 "b_mm": b_s, "zdiff_ohm": dict(zip(map(str, CENTERS), zi)), "within_10pct": inband(zi)}}

    # ── CO-66 修正证明：铜厚扣除后扫描 ────────────────────────────────────
    def bis(f, t, lo, hi):
        for _ in range(200):
            m = (lo + hi) / 2
            if f(m) > t:
                hi = m
            else:
                lo = m
        return (lo + hi) / 2

    scan = []
    for iw in range(110, 186, 5):
        w = round(iw / 1000, 3)
        b = round(bis(lambda bb: SL(w, bb, T_IN, ER_CORE, 0.5 - w), 85.0, 0.02, 2.0), 4)
        g4x = round(TOTAL - CU - 2 * h_o - 2 * b, 4)
        zz = z_inner_b = [round(SL(w, b, T_IN, ER_CORE, c - w), 2) for c in CENTERS]
        scan.append({"w_stripline_mm": w, "b_stripline_mm": b, "g4_mm": g4x,
                     "closes_1p6_copper_incl": g4x >= G4_MIN, "zdiff_ohm": dict(zip(map(str, CENTERS), zz))})

    # ── LID REV6 ─────────────────────────────────────────────────────────
    lid6 = dict(lid5)
    lid6["artifact"] = "m13_v57_layer_intent_rev6"
    lid6["revision"] = "REV6"
    lid6["authority"] = ("k2/tools/p3_v57_co68_option_a_execute_derive.py —— L2 叠层分配执行"
                         "（CO-67 红线裁定 L2 + CO-66 方案(a)）")
    lid6["supersedes"] = "m13_v57_layer_intent_rev5.json (REV5) —— 保存于仓库，未改"
    lid6["layer_intent"] = {"F.Cu": "stub_only", "In1.Cu": "gnd_plane", "In2.Cu": "transition_eligible",
                            "In3.Cu": "gnd_plane", "In4.Cu": "power_plane(P3V3, spec)",
                            "In5.Cu": "transition_eligible", "In6.Cu": "gnd_plane",
                            "B.Cu": "transition_eligible"}
    lid6["transition_eligible_layers"] = ["In2.Cu", "In5.Cu", "B.Cu"]
    lid6["stackup"] = "8L F/In1(G)/In2(S)/In3(G)/In4(P)/In5(S)/In6(G)/B(S)  [CO-68 方案(a)：对称叠层、4 信号层全参考]"
    lid6["stackup_unchanged"] = False
    lid6["reference_sandwich"] = {"F.Cu": ["In1.Cu"], "In2.Cu": ["In1.Cu", "In3.Cu"],
                                  "In5.Cu": ["In4.Cu", "In6.Cu"], "B.Cu": ["In6.Cu"]}
    lid6["ruling"] = ("层集由容量闭合派生（L_signal=4 ⇒ 8L）不变；方案(a) 仅改**平面在位次序**："
                      "In5(GND)->信号、In6(信号)->GND；层数/平面数/电源域划分不变（CO-67 机判）。")
    lid6["domain_invariance"] = {"plane_count": 4, "nets": {"GND": 3, "P3V3": 1},
                                 "note": "平面清单与网归属不变；仅位置变更 ⇒ L2（CO-67）"}
    OUT_LID6.write_text(json.dumps(lid6, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

    # ── SPEC rev-5（自 rev-4 纯加性；数值阈值不动）────────────────────────
    s5 = json.loads(SPEC4.read_text(encoding="utf-8"))
    s5["spec_version"] = "1.1.spec-rev-5"
    st = s5["stackup"]
    st["F.Cu"] = "signal (PCIe + escape)"
    st["In1.Cu"] = "GND_PLANE (full)"
    st["In2.Cu"] = "signal (PCIe + escape)"
    st["In3.Cu"] = "GND_PLANE (full)"
    st["In4.Cu"] = "POWER_PLANE (P3V3)"
    st["In5.Cu"] = "signal (PCIe + escape)"
    st["In6.Cu"] = "GND_PLANE (full)"
    st["B.Cu"] = "signal (PCIe + escape)"
    st["basis"] = ("方案(a) 对称叠层（CO-66/CO-68，L2 叠层分配；CO-67 机判：层数/平面数/电源域不变）；"
                   "逐层介质厚度 = CO-68 铜厚自洽修正解；终判 = SI9000 + 板厂阻抗券")
    st["dielectric_8l"] = {
        "d(F.Cu-In1.Cu)": {"mm": d["d(F.Cu-In1.Cu)"], "material": "2116*1", "er": ER_PP, "use": "F.Cu 微带参考"},
        "d(In1.Cu-In2.Cu)": {"mm": d["d(In1.Cu-In2.Cu)"], "material": "core 0.25", "er": ER_CORE, "use": "In2 带状线上参考（对称化）"},
        "d(In2.Cu-In3.Cu)": {"mm": d["d(In2.Cu-In3.Cu)"], "material": "core 0.25", "er": ER_CORE, "use": "In2 带状线下参考（对称化）"},
        "d(In3.Cu-In4.Cu)": {"mm": g4, "material": "自由余隙（1080*2≈0.1528 / 2116+1080≈0.1928，按 1.6mm 闭合）", "er": 4.10, "use": "GND-P3V3 平面间余隙"},
        "d(In4.Cu-In5.Cu)": {"mm": d["d(In4.Cu-In5.Cu)"], "material": "core 0.25", "er": ER_CORE, "use": "In5 带状线上参考（对称化）"},
        "d(In5.Cu-In6.Cu)": {"mm": d["d(In5.Cu-In6.Cu)"], "material": "core 0.25", "er": ER_CORE, "use": "In5 带状线下参考（对称化）"},
        "d(In6.Cu-B.Cu)": {"mm": d["d(In6.Cu-B.Cu)"], "material": "2116*1", "er": ER_PP, "use": "B.Cu 微带参考"},
    }
    st["dielectric_8l_basis"] = {
        "authority": "L2 叠层分配自裁（CO-66 → CO-68 修正；CO-67 红线裁定 L2）",
        "method": ("**铜厚自洽修正**：介质预算 = 1.6 - copper 0.175 = 1.425；闭合 2*h_o + 2*b_s + g4 = 1.425；"
                   "外层微带 (w_o,h_o)->85Ω；内层对称带状线 (w_s,b_s)->85Ω；交付对内中心 {0.5,0.6} 均须落 85±10%"),
        "model": "IPC-2141（_shared/eda_core/stackup.py）",
        "co66_correction": ("CO-66 令 g4=1.6-2h_o-2b（未扣铜厚）⇒ 其 0.19/0.205 行实为不可行；"
                            "本件修正后内层可行线宽上界 ~0.165（见 scan）"),
        "thickness_closure": f"copper {closure['copper_mm']} + dielectric {closure['dielectric_mm']} = {closure['total_mm']}（delta {closure['delta_mm']}）",
        "verdict_first_order": verdict,
        "signoff": "未完成：须 SI9000 + 板厂阻抗券（coupon_required=true）",
    }
    imp = s5["impedance"]
    imp["per_layer"] = {
        "F.Cu": {"kind": "microstrip", "refs": ["In1.Cu"], "w_mm": w_outer, "h_mm": h_o, "er": ER_PP,
                 "gap_mm_delivered": [round(c - w_outer, 3) for c in CENTERS], "material": "2116*1"},
        "In2.Cu": {"kind": "symmetric_stripline", "refs": ["In1.Cu", "In3.Cu"], "w_mm": w_inner, "b_mm": b_s,
                   "er": ER_CORE, "gap_mm_delivered": [round(c - w_inner, 3) for c in CENTERS], "material": "core 0.25*2"},
        "In5.Cu": {"kind": "symmetric_stripline", "refs": ["In4.Cu", "In6.Cu"], "w_mm": w_inner, "b_mm": b_s,
                   "er": ER_CORE, "gap_mm_delivered": [round(c - w_inner, 3) for c in CENTERS], "material": "core 0.25*2"},
        "B.Cu": {"kind": "microstrip", "refs": ["In6.Cu"], "w_mm": w_outer, "h_mm": d["d(In6.Cu-B.Cu)"], "er": ER_PP,
                 "gap_mm_delivered": [round(c - w_outer, 3) for c in CENTERS], "material": "2116*1"},
    }
    imp["per_layer_basis"] = ("CO-68：方案(a) 下 4 信号层**全部有参考平面**（修复 CO-62 的 B.Cu 无参考）；"
                              "内层线宽 0.205→0.16（铜厚自洽闭合要求）。终判 = 板厂券。")
    imp["width_mm_by_layer"] = {"F.Cu": w_outer, "In2.Cu": w_inner, "In5.Cu": w_inner, "B.Cu": w_outer}
    dp = s5["net_classes"]["PCIe85"]["diff_pair"]
    dp["p_width_mm_by_layer"] = imp["width_mm_by_layer"]
    dp["p_width_scope"] = ("netclass 标量 p_width=0.205 保留（外层次口径）；内层交付线宽 = p_width_mm_by_layer"
                           "（CO-68 几何协同：内层 0.16 以满足对称叠层 85Ω 闭合）")
    s5["_spec_rev_5"] = {
        "card": "SPEC-REV-5", "at": "2026-09-12",
        "authority": "L2 叠层分配自裁（CO-66/CO-68；CO-67 红线张力裁定 = L2）",
        "changes": ["spec_version: 1.1.spec-rev-4 -> 1.1.spec-rev-5",
                    "stackup.*.Cu：In5 signal / In6 GND（方案(a) 平面在位次序；层数/平面数/电源域不变）",
                    "stackup.dielectric_8l -> CO-68 铜厚自洽修正解（+ basis/co66_correction）",
                    "impedance.per_layer -> F/B 微带 + In2/In5 对称带状线（新线宽 0.16 内层）；新增 width_mm_by_layer",
                    "net_classes.PCIe85.diff_pair.p_width_mm_by_layer/p_width_scope（**数值阈值未改**）"],
        "unchanged": "net_classes.PCIe85.*（宽度/净距/对内等长阈值）、vias、constraints、corridors、layer_plan、PD、board；"
                     "原 SPEC_k2_v4.json / spec-rev-2 / rev-3 / rev-4 逐字节未动",
        "geometry_impact_expected": ("内层 track 宽度 0.205->0.16（引擎图纸内层段）；F/B 不变；"
                                     "几何（走廊/落列/球位）由引擎重跑，本件不改坐标"),
        "rollback": "删除本文件；引擎 F.spec/FROZEN_SHA 指回 spec-rev-4（1c4eecb0edf4a446）；LID 指回 rev5",
    }
    OUT_SPEC5.write_text(json.dumps(s5, ensure_ascii=False, indent=1), encoding="utf-8")

    res = {
        "artifact": "m13_v57_co68_option_a_execute_derive", "schema": 1, "revision": "CO-68.1",
        "nature": "L2 叠层分配执行：CO-66 铜厚修正 + 方案(a) 设计点 + LID REV6 + SPEC rev-5（版本化）",
        "co66_correction": {"co66_closure_omitted_copper_mm": round(CU, 4),
                            "co66_g4_formula": "1.6 - 2*h_o - 2*b_s（未扣铜厚）",
                            "corrected_dielectric_budget_mm": round(TOTAL - CU, 4),
                            "corrected_feasible_w_stripline_max_mm": max(
                                r["w_stripline_mm"] for r in scan if r["closes_1p6_copper_incl"])},
        "design_point": {"stackup": "F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)",
                         "dielectric_mm": d, "copper_mm": round(CU, 4), "closure": closure,
                         "w_outer_mm": w_outer, "w_inner_mm": w_inner, "b_stripline_mm": b_s,
                         "verdict_first_order": verdict},
        "scan": scan,
        "outputs": {"lid_rev6": str(OUT_LID6.relative_to(K2)), "lid_rev6_sha16": sha16(OUT_LID6),
                    "spec_rev5": str(OUT_SPEC5.relative_to(K2)), "spec_rev5_sha16": sha16(OUT_SPEC5)},
        "unchanged_check": {"spec_rev4_sha16_before": spec4_before, "spec_rev4_sha16_after": sha16(SPEC4),
                            "lid_rev5_sha16_before": lid5_before, "lid_rev5_sha16_after": sha16(LID5)},
        "redline": "原件/历史件未动；数值阈值未改；一阶结论未经 SI9000/券。",
    }
    OUT_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

    md = f"""# CO-68 — 【L2 叠层分配】执行方案(a)：铜厚自洽修正 + LID REV6 + SPEC rev-5

> 2026-09-12｜定层 **L2**（CO-67 裁定）｜工具 `tools/p3_v57_co68_option_a_execute_derive.py`
> 记录 `{sha16(OUT_JSON)}`｜LID REV6 `{sha16(OUT_LID6)}`｜SPEC rev-5 `{sha16(OUT_SPEC5)}`
> 性质：只读冻结源；版本化新文件；`spec-rev-4`/`layer_intent_rev5` **逐字节未动**（before==after 机判）。

## 1. CO-66 修正（铜厚口径）
- CO-66 闭合式 `g4 = 1.6 - 2*h_o - 2*b_s` **未扣铜厚**（0.175mm）；与 CO-55 `copper 0.175 + dielectric 1.425 = 1.6000` 矛盾。
- 修正：**介质预算 = 1.425**，闭合 `2*h_o + 2*b_s + g4 = 1.425`，`g4 >= {G4_MIN}`（1080 单张）。
- 后果：内层带状线**可行线宽上界 ~0.165**（CO-66 表内 0.19/0.205 行实为**不可行**）。扫描见 `scan`。

## 2. 设计点（标准料、铜厚自洽）
叠层 `F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)`；逐层介质：
| 间隙 | mm | 料 |
|---|---|---|
| d(F–In1) | {d['d(F.Cu-In1.Cu)']} | 2116×1 |
| d(In1–In2) | {d['d(In1.Cu-In2.Cu)']} | core 0.25 |
| d(In2–In3) | {d['d(In2.Cu-In3.Cu)']} | core 0.25 |
| d(In3–In4) | {g4} | 自由余隙（闭合） |
| d(In4–In5) | {d['d(In4.Cu-In5.Cu)']} | core 0.25 |
| d(In5–In6) | {d['d(In5.Cu-In6.Cu)']} | core 0.25 |
| d(In6–B) | {d['d(In6.Cu-B.Cu)']} | 2116×1 |

闭合：copper `{closure['copper_mm']}` + dielectric `{closure['dielectric_mm']}` = **{closure['total_mm']}**（delta {closure['delta_mm']}）⇒ `{closure['ok']}`。
线宽：外层 **{w_outer}**（F/B，微带，Z {zo}），内层 **{w_inner}**（In2/In5，对称带状线 b={b_s}，Z {zi}），
交付对内中心 {{0.5, 0.6}} 均落 85±10% ⇒ `{inband(zo) and inband(zi)}`。

## 3. 版本化产出
- **LID REV6** `{str(OUT_LID6.relative_to(K2))}` `{sha16(OUT_LID6)}`：signal = F/In2/**In5**/B；In1/In3/**In6**=GND，In4=P3V3；参考夹心全信号层有参考。
- **SPEC rev-5** `{str(OUT_SPEC5.relative_to(K2))}` `{sha16(OUT_SPEC5)}`：stackup 用途 + `dielectric_8l` + `impedance.per_layer` + `p_width_mm_by_layer`；**数值阈值未改**。

## 4. 下一步（CO-69 起）
引擎 bump（`LAYER_PALETTE` F/In2/In5/B；In6→In5；`F.spec`→rev-5、`F.layer_intent`→rev6、冻结集）
→ G4..G7 全链 → SI 判据按层加权电气长度 → 重新对抗评审。

## 5. 指纹
`spec-rev-4 {sha16(OUT_SPEC5) and spec4_before}` 未变｜`layer_intent_rev5 {lid5_before}` 未变。
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(json.dumps({"json_sha16": sha16(OUT_JSON), "md_sha16": sha16(OUT_MD),
                      "lid_rev6_sha16": sha16(OUT_LID6), "spec_rev5_sha16": sha16(OUT_SPEC5),
                      "closure_total": closure["total_mm"], "closure_ok": closure["ok"],
                      "w_inner": w_inner, "z_inner": zi, "z_outer": zo,
                      "inband": inband(zo) and inband(zi),
                      "design_point_ok": inband(zo) and inband(zi) and closure["ok"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
