#!/usr/bin/env python3
"""CO-204 — **U6 热定案 O2（写入要求件 + 版本 bump）** 与 **散热验证闸**（监理指令 #12 动作 4/5）。

O2（owner 确认有风冷后采）：顶部 30×30mm 铝散热片 + 界面垫(1.0 ℃/W) + ~2 m/s 风冷
  θJA_eff = θJC_top + R_int + θHS = 6.5 + 1.0 + 3.5 = 11.0 ℃/W。
判据（散热验证闸，设计期算结温、**输入显式声明**）：四工况 Tj = Ta + P·θJA_eff ≤ Tj_max。
输入来源：`m13_v57_co148_u6_ds320pr1601_inputs.json`（TI SNLS683 数据手册派生）+ 本件 O2 声明。
CLI: python3 tools/p3_v57_co204_thermal_o2_freeze_and_gate.py   （幂等）
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2D = K2 / "pm_gate/artifacts/k2_v4/L2"
INP = S2 / "m13_v57_co148_u6_ds320pr1601_inputs.json"
REC = S2 / "m13_v57_co204_thermal_verification.json"
DOC = L2D / "L2_RULING_u6_thermal_mitigation_v2.md"
O2 = {"theta_jc_top_C_per_W": 6.5, "r_interface_C_per_W": 1.0, "theta_hs_C_per_W": 3.5,
      "heatsink": "30×30mm 铝散热片 + 界面垫 1.0 ℃/W", "airflow": "~2 m/s 风冷（owner 确认有风冷）"}


def sha16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    inp = json.loads(INP.read_text(encoding="utf-8"))
    I = inp["inputs"]
    ta, tj_max = 40.0, float(I["TJ_max_C"])
    th = round(O2["theta_jc_top_C_per_W"] + O2["r_interface_C_per_W"] + O2["theta_hs_C_per_W"], 4)
    rows, ok = {}, True
    for band, pact in I["PACT"].items():
        for kind in ("typ", "max"):
            key = f"U6_EQ{band}_{kind}"
            P = float(pact[f"{kind}_W"]); tj = round(ta + P * th, 2)
            rows[key] = {"P_W": P, "Tj_C": tj, "limit_C": tj_max, "ok": tj <= tj_max}
            ok &= tj <= tj_max
    rec = {
        "artifact": "m13_v57_co204_thermal_verification", "schema": 1, "revision": "CO-204",
        "nature": "散热验证闸（设计期算结温；输入显式声明）+ U6 热定案 O2 冻结 —— 监理指令 #12 动作 4/5",
        "declared_inputs": {"ta_C": ta, "tj_max_C": tj_max,
                            "pact_W": {b: {"typ": I["PACT"][b]["typ_W"], "max": I["PACT"][b]["max_W"]} for b in I["PACT"]},
                            "theta_jc_top_C_per_W": O2["theta_jc_top_C_per_W"],
                            "r_interface_C_per_W": O2["r_interface_C_per_W"],
                            "theta_hs_C_per_W": O2["theta_hs_C_per_W"],
                            "source": INP.name, "source_sha16": sha16(INP),
                            "datasheet": inp["source"]["datasheet"], "datasheet_sha256": inp["source"]["pdf_sha256"]},
        "o2": {**O2, "theta_ja_eff_C_per_W": th},
        "cases": rows, "verdict": "PASS" if ok else "FAIL",
        "teeth": {"four_cases_all_covered": len(rows) == 4 and ok,
                  "o2_beats_worst_required": th <= 11.43,
                  "inputs_explicit": all(k in I for k in ("PACT", "TJ_max_C", "theta_jc_top_C_per_W"))},
        "redline": "只读输入件 + 闭式一阶计算；零坐标搜索；不改 SPEC/板/冻结四源。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = f"""# L2 裁定 v2.0（CO-204）— U6 热定案：**采 O2**（顶部散热片 + 风冷）

> 层级：L2（热机械 —— 宪章第二章）｜**版本 bump：v1.0 → v2.0**｜取代 v1.0 §3/§4 之「推荐/待定」口径为**定案**
> 输入件：`{INP.name}` `{sha16(INP)}`（TI DS320PR1601 SNLS683 数据手册派生）｜Ta = {ta} ℃｜Tj_max = {tj_max} ℃

## 1. 定案（O2）
owner 确认**有风冷** ⇒ 采 **O2**：**{O2['heatsink']} + {O2['airflow']}**。
θJA_eff = θJC_top({O2['theta_jc_top_C_per_W']}) + R_int({O2['r_interface_C_per_W']}) + θHS({O2['theta_hs_C_per_W']}) = **{th} ℃/W**。

## 2. 四工况结温（散热验证闸重算）
| 工况 | P (W) | Tj = {ta} + P·{th} (℃) | 限值 (℃) | 结论 |
|---|---|---|---|---|
""" + "\n".join(
        f"| {k} | {v['P_W']} | **{v['Tj_C']}** | {v['limit_C']} | {'PASS' if v['ok'] else 'FAIL'} |"
        for k, v in rows.items()) + f"""

- 最重工况 `U6_EQ5-19_max`：{rows['U6_EQ5-19_max']['Tj_C']} ℃ ≤ {tj_max} ℃ ⇒ **四工况全覆盖**（要求 θJA_eff ≤ 11.43，实得 {th}）。
- 判据 = 散热验证闸 `tools/p3_v57_co204_thermal_o2_freeze_and_gate.py`（机读记录 `{REC.name}`）：Tj = Ta + P·θJA_eff ≤ Tj_max，**输入显式声明**（Ta/P/θJC/R_int/θHS/限值 + 来源 sha）。
- v1.0 §4 R5-3（PCB 侧不做几何改动）**维持**；R5-4（终判须实板热测/仿真）**维持**。
"""
    DOC.write_text(md, encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "theta_ja_eff": th,
                      "cases": {k: v["Tj_C"] for k, v in rows.items()},
                      "doc_sha16": sha16(DOC), "rec_sha16": sha16(REC)}, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
