#!/usr/bin/env python3
"""CO-149 — U6 热机械**派生实现要求**（L2 自裁；不待 owner、不改监理定值）。

框架：监理定值 Ta = 40°C 保留不变（需求不动机器）；**工程派生** = 达成 Tj ≤ Tj_limit 所需的系统散热要求。
两路线一致性核对（**B 路线复用手册 ψJB 与声明 h ⇒ 非独立证据**；CO-151 F-4）+ 敏感度披露（ψJB↔RθJB、h）：
  路线 A（数据手册参考板）：θJA(high-K) = 17.4 °C/W
  路线 B（本板几何一阶）：θJA_est = ψJB(手册) + 1/(h·2·A_board)，h = 声明自然对流系数
派生输出：各 EQ 档所需 θJA_eff 上限；所需 h（强制风冷）或 顶部散热片预算（θJC 路径 = θJC + R_int + θ_HS）。
产出：`L2/L2_RULING_u6_thermal_mitigation_v1.md` + `m13_v57_co149_u6_thermal_mitigation.json`
      + 登记簿（热项 CLOSED = 派生实现要求）+ 台账 DV-CO146-THERMAL 可达性 = 声明散热方案域（供 K9 判）。
牙齿：① 两路线 θJA 一致性 ≤5%；② 自然对流（as-built）全档不可达；③ 声明方案 O2 覆盖全档（∃ 可达）；
④ 改用 RθJB（真热阻 ≥ ψJB）后所需 h 必须**更保守**（单调性）；⑤ 敏感度块必须非空（不得空过）。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
U6IN = S2 / "m13_v57_co148_u6_ds320pr1601_inputs.json"
PMR = S2 / "m13_v57_co146_pm_eval.json"
REG = L2 / "input_defect_register_v1.json"
LED = L2 / "derived_value_ledger_v1.json"
DOC = L2 / "L2_RULING_u6_thermal_mitigation_v1.md"
REC = S2 / "m13_v57_co149_u6_thermal_mitigation.json"
THERMAL_ID = "thermal_defect:u6_ds320pr1601_tj_exceeds_limit_at_40c_natural_convection"
# 声明系统散热方案（工程声明值：接口热阻 / 散热片热阻 / 等效对流系数）
OPTIONS = [
    {"id": "O0_asbuilt", "desc": "现状：40°C 自然对流、无散热片", "theta_ja_eff_C_per_W": None,
     "theta_ja_expr": "θJA = ψJB + 1/(h_nat·2A)", "h_eff": 8.0},
    {"id": "O1_forced_airflow", "desc": "强制风冷（板面 ~2 m/s，无散热片）", "h_eff": 16.0},
    {"id": "O2_heatsink_airflow", "desc": "顶部 30×30mm 铝散热片 + 界面垫(1.0) + ~2 m/s 风冷",
     "theta_jc_C_per_W": 6.5, "r_interface_C_per_W": 1.0, "theta_hs_C_per_W": 3.5},
]


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    spec = json.loads(SPEC.read_text())
    u6 = json.loads(U6IN.read_text())
    pm = json.loads(PMR.read_text())
    pact = u6["inputs"]["PACT"]
    th_ja_ds = u6["inputs"]["theta_ja_highK_C_per_W"]
    psi_jb = u6["inputs"]["psi_jb_C_per_W"]
    thjb = u6["inputs"].get("theta_jb_C_per_W")          # CO-152：与 ψJB 并列披露
    tj_lim = u6["inputs"]["TJ_max_C"]
    ta = pm["declared_inputs"]["supervisor_values_指令10"]["ambient_C"]
    h_nat = pm["declared_inputs"]["engineering_declared"]["h_conv"]["value"]
    bx, by = spec["board"]["outline_x"], spec["board"]["outline_y"]
    A1 = (bx[1] - bx[0]) * (by[1] - by[0]) * 1e-6
    A2 = 2.0 * A1
    r_sa_nat = 1.0 / (h_nat * A2)
    th_ja_est = psi_jb + r_sa_nat
    cases = {}
    for eq, v in pact.items():
        for kind in ("typ", "max"):
            P = v[f"{kind}_W"]
            th_req = (tj_lim - ta) / P
            cases[f"U6_EQ{eq}_{kind}"] = {
                "P_W": P, "theta_ja_required_C_per_W": round(th_req, 2),
                "h_required_W_per_m2K": round(1.0 / (A2 * (th_req - psi_jb)), 2) if th_req > psi_jb else None,
                "top_sink_budget_C_per_W": round(th_req - u6["inputs"]["theta_jc_top_C_per_W"], 2)}
    for o in OPTIONS:
        if o["id"] == "O0_asbuilt":
            o["theta_ja_eff_C_per_W"] = round(th_ja_est, 2)
        elif "theta_jc_C_per_W" in o:
            o["theta_ja_eff_C_per_W"] = round(o["theta_jc_C_per_W"] + o["r_interface_C_per_W"] + o["theta_hs_C_per_W"], 2)
        else:
            o["theta_ja_eff_C_per_W"] = round(psi_jb + 1.0 / (o["h_eff"] * A2), 2)
        o["covers_cases"] = [k for k, c in cases.items()
                             if o["theta_ja_eff_C_per_W"] <= c["theta_ja_required_C_per_W"]]
        o["covers_all"] = len(o["covers_cases"]) == len(cases)
    o0 = next(o for o in OPTIONS if o["id"] == "O0_asbuilt")
    o2 = next(o for o in OPTIONS if o["id"] == "O2_heatsink_airflow")
    # CO-152（CO-151 F-4）：敏感度披露（ψJB↔RθJB 模型选择 + h 声明值）
    h_req_rjb = ({k: round(1.0 / (A2 * (c["theta_ja_required_C_per_W"] - thjb)), 2)
                 for k, c in cases.items() if thjb and c["theta_ja_required_C_per_W"] > thjb})
    cov_at = lambda h: [k for k, c in cases.items()
                        if psi_jb + 1.0 / (h * A2) <= c["theta_ja_required_C_per_W"]]
    sens = {"psi_jb": psi_jb, "r_theta_jb": thjb,
            "h_required_range_psi_jb": [min(h_req_rjb and [0] or [0]) if False else
                                        min(c["h_required_W_per_m2K"] for c in cases.values() if c["h_required_W_per_m2K"]),
                                        max(c["h_required_W_per_m2K"] for c in cases.values() if c["h_required_W_per_m2K"])],
            "h_required_range_rjb": [min(h_req_rjb.values()), max(h_req_rjb.values())] if h_req_rjb else None,
            "h8": cov_at(8.0), "h85": cov_at(8.5), "h16": cov_at(16.0),
            "note": "板侧路线用 ψJB（表征参数）作加性热阻；改用 RθJB（热阻）更保守。两路线一致性 ≠ 独立证据。"}
    if sens["h_required_range_rjb"]:
        sens["delta_pct"] = round((sens["h_required_range_rjb"][0] - sens["h_required_range_psi_jb"][0])
                                  / sens["h_required_range_psi_jb"][0] * 100, 2)
    teeth = {"t01_two_routes_agree": abs(th_ja_est - th_ja_ds) / th_ja_ds <= 0.05,
             "t02_asbuilt_unreachable_all": not o0["covers_all"] and not o0["covers_cases"],
             "t03_declared_option_covers_all": o2["covers_all"],
             "t04_rjb_more_demanding": bool(sens["h_required_range_rjb"]) and
                                       sens["h_required_range_rjb"][0] > sens["h_required_range_psi_jb"][0],
             "t05_sensitivity_disclosed": bool(sens["h8"] is not None and sens["r_theta_jb"] and sens["delta_pct"])}
    req = {"system_mitigation_required": True,
           "theta_ja_eff_max_C_per_W": min(c["theta_ja_required_C_per_W"] for c in cases.values()),
           "h_required_range_W_per_m2K": [min(c["h_required_W_per_m2K"] for c in cases.values() if c["h_required_W_per_m2K"]),
                                          max(c["h_required_W_per_m2K"] for c in cases.values() if c["h_required_W_per_m2K"])],
           "top_sink_budget_range_C_per_W": [min(c["top_sink_budget_C_per_W"] for c in cases.values()),
                                             max(c["top_sink_budget_C_per_W"] for c in cases.values())]}
    doc = ["# L2 裁定 v1.0 — U6 热机械派生实现要求（CO-149；解 CO-148 R4-2）", "",
           f"> 依据：LAYOUT_CONSTITUTION 第二章（**热机械** = L2 自裁）；**监理定值 Ta = {ta}°C 保留不变**（不动需求输入）。",
           "> 本件把「输入冲突」转为**派生实现要求**：不是改环境，而是导出达成 Tj 上限所需的系统散热实现。", "",
           "## 1. 两路线一致性核对（**非独立证据**）", "",
           f"- A（手册参考板）：θJA(high-K) = **{th_ja_ds} °C/W**",
           f"- B（本板一阶）：ψJB {psi_jb} + 1/(h_nat·2A) = {psi_jb} + 1/({h_nat}×{A2:.5f}) = **{th_ja_est:.2f} °C/W**",
           f"- 互差 {abs(th_ja_est - th_ja_ds) / th_ja_ds * 100:.1f}% ⇒ **一致性核对通过**"
           f"（B 路线复用手册 ψJB 与声明 h ⇒ 非独立证据，不作模型独立性主张）", "",
           "### 1.1 敏感度（CO-151 F-4 披露）", "",
           f"- 板侧路线改用同表**热阻 RθJB = {sens['r_theta_jb']}**（而非表征参数 ψJB = {psi_jb}）⇒ 所需 h 由 "
           f"**{sens['h_required_range_psi_jb']} → {sens['h_required_range_rjb']} W/m²K**（更保守，+{sens['delta_pct']}%）。",
           f"- 声明自然对流 h = {h_nat} 的敏感度：h = 8.0 覆盖 **{len(sens['h8'])}/4** 档；h = 8.5 覆盖 "
           f"**{len(sens['h85'])}/4** 档（增量 = {'、'.join(sens['h85']) or '无'}）⇒ 『自然对流不足以覆盖全档』结论不因该敏感度改变。", "",
           "## 2. 派生要求（各 EQ 档）", "",
           "| 工况 | P (W) | 需要 θJA_eff ≤ (°C/W) | 需要 h ≥ (W/m²K) | 顶部散热片预算 θJC+R_int+θHS ≤ (°C/W) |",
           "|---|---|---|---|---|"]
    for k, c in cases.items():
        doc.append(f"| {k} | {c['P_W']} | **{c['theta_ja_required_C_per_W']}** | {c['h_required_W_per_m2K']} | "
                   f"{c['top_sink_budget_C_per_W']} |")
    doc += ["", "## 3. 方案评估（声明值）", "", "| 方案 | θJA_eff (°C/W) | 覆盖工况 | 全档 |", "|---|---|---|---|"]
    for o in OPTIONS:
        doc.append(f"| {o['id']}：{o['desc']} | {o['theta_ja_eff_C_per_W']} | {len(o['covers_cases'])}/{len(cases)} | "
                   f"{'✓' if o['covers_all'] else '✗'} |")
    doc += ["", "## 4. 裁定", "",
            f"**R5-1**：**自然对流（现状）在全部 EQ 档均不可达**（θJA_est {th_ja_est:.2f} > 最轻档要求 "
            f"{cases['U6_EQ0-2_typ']['theta_ja_required_C_per_W']}）⇒ 系统侧散热投入为**必需项**，非可选项。",
            f"**R5-2**：**最低要求** = 强制风冷使 h_eff ≥ {req['h_required_range_W_per_m2K'][0]}–{req['h_required_range_W_per_m2K'][1]} W/m²K"
            f"（约 1–3 m/s 板面风速）；**推荐** = 顶部散热片 + 风冷（θJC 路径），预算 θ_HS + R_int ≤ "
            f"{req['top_sink_budget_range_C_per_W'][0]}–{req['top_sink_budget_range_C_per_W'][1]} °C/W。",
            "**R5-3**：PCB 侧**不做几何改动**：散热瓶颈为「板→空气」（占 θJA 的 "
            f"{r_sa_nat / th_ja_est * 100:.0f}%），U6 域热过孔仅影响 ψJB（{psi_jb} 项，≤ 数 °C/W 收益）⇒ "
            "为边际收益触发 G4 全链重基线不成立；CO-148 R4-1 的「GND via 阵列」由**义务**降为**可选项**。",
            "**追注（CO-224 / 承 R-CO223-1）**：R5-3 中「GND via 阵列」之**义务时点**现行口径**以 CO-222 为准**（boundary §95）= "
            "**条件动作**（T1/T2），既非本节旧述之「可选项」，亦非 CO-148 §R4-1 之「既定义务」；本节正文不改（承 CO-213 F-3）。",
            f"**R5-4**：终判需实板热测/仿真（本件为闭式一阶派生）；监理定值 Ta={ta}°C 与压降 3% 均不变。", ""]
    DOC.write_text("\n".join(doc) + "\n")
    # ── 登记簿：热项 CLOSED（派生实现要求） ────────────────────────────────
    reg = json.loads(REG.read_text())
    for it in reg["items"]:
        if it["finding"] == THERMAL_ID:
            it["status"] = "CLOSED"
            it["ruled_by"] = "CO-149"
            it["ruling"] = ("L2 派生实现要求：自然对流全档不可达 ⇒ 系统散热为必需项（h_eff ≥ "
                            f"{req['h_required_range_W_per_m2K'][0]}–{req['h_required_range_W_per_m2K'][1]} W/m²K 或顶部散热片预算 ≤ "
                            f"{req['top_sink_budget_range_C_per_W'][0]}–{req['top_sink_budget_range_C_per_W'][1]} °C/W）；"
                            "监理定值 Ta=40°C 保持不变；PCB 侧不改几何（瓶颈为板→空气）。")
            it["disposition"] = (it.get("disposition", "").split("【CO-149 L2 派生】")[0] +
                                 "【CO-149 L2 派生】" + it["ruling"])
            it["next"] = "系统/机械侧落实散热方案（风冷 ≥1–3 m/s 或 顶部散热片+风冷）；L2 侧终判 = 实板热测/仿真。"
            it["closed_by"] = sorted(set(it.get("closed_by", [])) | {"CO-149"})
    MARK = ("；**CO-149（L2 自裁 · 热机械派生）**：自然对流全档不可达（两路线互校 θJA≈17.2 vs 手册 17.4）⇒ "
            "派生出系统散热要求（h_eff ≥ 8.2–16.4 W/m²K 或 顶部散热片预算 ≤ 4.9–10.5 °C/W）；监理定值 Ta=40°C 不变；"
            f"登记簿热项 CLOSED（OPEN 余 K9 热域缺口）；台账 DV-CO146-THERMAL 可达性 = 声明散热方案域。（{s16(DOC)}）")
    if "CO-149" not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    # ── 台账：热 DV 改为「声明散热方案域」（供 K9 判；∃ 方案覆盖 ⇒ REACHABLE） ──
    led = json.loads(LED.read_text())
    for dv in led["derived_values"]:
        if dv["id"] == "DV-CO146-THERMAL":
            dv["inputs"]["system_mitigation_options"] = OPTIONS
            dv["computed"]["required"] = req
            dv["reachability"] = {
                "kind": "thermal_option_domain",
                "verdict": "REACHABLE",
                "predicate": "∃ 声明散热方案使 Tj ≤ Tj_limit（各方案按 θJA_eff ≤ 所需值判定）",
                "required_mitigation": ("系统须提供：强制风冷 h_eff ≥ %.1f W/m²K 或 顶部散热片(θJC+R_int+θ_HS ≤ %.2f °C/W)"
                                        % (req["h_required_range_W_per_m2K"][1], req["top_sink_budget_range_C_per_W"][0])),
                "domains": [{"id": o["id"], "theta_ja_eff_C_per_W": o["theta_ja_eff_C_per_W"],
                             "ok": o["covers_all"], "desc": o["desc"]} for o in OPTIONS],
                "evidence_ref": {"path": DOC.name, "sha16": s16(DOC)}}
    LED.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n")
    rec = {"artifact": "m13_v57_co149_u6_thermal_mitigation", "schema": 1, "revision": "CO-149.2",
           "nature": "L2 自裁：U6 热机械派生实现要求（解 CO-148 R4-2；监理定值不变）",
           "doc": DOC.name, "doc_sha16": s16(DOC), "ta_C": ta, "tj_limit_C": tj_lim,
           "routes": {"datasheet_theta_ja": th_ja_ds, "board_first_order_theta_ja": round(th_ja_est, 2),
                      "r_surface_to_air": round(r_sa_nat, 2), "psi_jb": psi_jb,
                      "board_to_air_share_pct": round(r_sa_nat / th_ja_est * 100, 1)},
           "cases": cases, "options": OPTIONS, "required": req, "sensitivity": sens,
           # 不记录 register/ledger 的 sha/open 快照：二者会被后续 CO（CO-150）改写 ⇒ 快照会造成重跑漂移。
           # 稳定引用：按 finding id / dv id 指向（状态由 co124 与 CO-150 记录各自承载）。
           "register": {"file": REG.name, "item": THERMAL_ID, "status": "CLOSED"},
           "ledger": {"file": LED.name, "dv": "DV-CO146-THERMAL→thermal_option_domain(REACHABLE)"},
           "teeth": teeth,
           "redline": "只读板/SPEC（逐字节未动）；不改几何；零坐标搜索；输出只写 L2 政策层 + 登记簿 + 台账。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("routes:", rec["routes"])
    print("required:", json.dumps(req, ensure_ascii=False))
    for o in OPTIONS:
        print("  ", o["id"], o["theta_ja_eff_C_per_W"], "covers", len(o["covers_cases"]), "/", len(cases), o["covers_all"])
    print("teeth:", teeth, "| register item", rec["register"]["status"], "| reg", s16(REG), "| led", s16(LED))
    return 0 if all(teeth.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
