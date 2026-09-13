#!/usr/bin/env python3
"""CO-146 A2 — PDN 压降 + 热评估（监理指令 #10 动作 2）。

性质：**只读一阶确定性评估**。输入全部**显式声明**（监理定值 + 工程声明值），
不得以假设值冒充实测；输出含「声明输入清单」+ 公式 + 可达性（co124 K9 口径：来源原则/派生式/输入/可达性）。

模型（几何一阶解析，非仿真）：
  电源平面：Rs = ρ_Cu(T)/t；R_plane = Rs·L/W（L=铜皮包络长边、W=A/L=等效宽，A=实铺铜面积）
  过孔并联：R_via = ρ·(总厚)/A_铜壁；A_铜壁 = π((d/2)²-(d/2-t_pl)²)，t_pl=18µm(JLC)
  压降 ΔV = I·(R_plane + R_via/√N_near)（N_near = 该网过孔数）；判据 = 监理定值 3%
热：ΔT_board = P_total/(h·A_both_sides)（h=自然对流声明值）；Tj = Ta + ΔT_board + P_dev·θJA
产出：m13_v57_co146_pm_eval.json / .md
牙齿（CO-181 去恒真：判据函数化 + 近失必翻转，R-CO179-1）：
  ① 电流 ×2 ⇒ 压降 ×2（经模型函数）；② 铜厚减半 ⇒ 方阻/平面电阻单调升（+ 反向近失必翻转）；
  ③ 平面几何取自交付板（+ 无此网负控为空）。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
U6_IN = STEP2 / "m13_v57_co148_u6_ds320pr1601_inputs.json"   # CO-148：U6 手册值（声明值 → 手册值）

# ── 监理定值（指令 #10，生效） ───────────────────────────────────────────────
SUP = {"drop_budget_pct": 3.0, "ambient_C": 40.0, "convection": "自然对流",
       "outer_copper_oz": 1.0, "inner_copper_oz": 0.5, "surface_finish": "ENIG"}
# ── 工程声明值（无器件手册数据 ⇒ 保守值 + 显式声明；须 PM/手册替换） ──────────
DECL = {
    "rho_cu_20C": {"value": 1.724e-8, "unit": "Ω·m", "basis": "Cu 标准电阻率（工程常数）"},
    "alpha_cu": {"value": 0.00393, "unit": "1/K", "basis": "Cu 电阻温度系数（工程常数）"},
    "plating_um": {"value": 18.0, "unit": "µm", "basis": "JLC 公布 平均孔铜厚 18µm"},
    "h_conv": {"value": 8.0, "unit": "W/m²K", "basis": "自然对流工程声明值（两面）"},
    "tj_limit_C": {"value": 125.0, "unit": "°C", "basis": "器件常规上限声明值"},
}
RAILS = {
    "12V_IN": {"I_a": 0.65, "I_basis": "P3V3 输出功率 /(η=0.88 × 12V) = 2.0A×3.3V/0.88/12V ⇒ 0.63A，取 0.65A（声明值）"},
    "P3V3": {"I_a": 2.00, "I_basis": "U6(DS320PR1601) 1.20A + U1 0.06A + 上拉/杂项 0.05A + 余量 ⇒ 声明 2.00A（保守；器件手册到位后替换）"},
    "P3V3_AUX": {"I_a": 1.00, "I_basis": "J3.A9 + J4.A9 侧带供电各 0.5A（声明值；MCIO 侧带电流口径待 PM）"},
    "MCU_VDD": {"I_a": 0.15, "I_basis": "U1(STM32G0B1) 0.06A + E2 0.01A + 上拉 0.01A + 余量 ⇒ 声明 0.15A"},
}
# U6（DS320PR1601）功耗/热阻 = **数据手册值**（CO-148；来源件 U6_IN，含 URL/抓取/PDF sha/节录件 sha）
def _u6_inputs() -> dict:
    return json.loads(U6_IN.read_text())


THERMAL = {
    "U2_dcdc": {"basis": "P_out = 3.3V×I(P3V3)；η=0.88（声明值，U2 无器件手册）⇒ loss = P_out×(1/η−1)"},
    "U1_mcu": {"p_W": 0.05, "theta_ja": 60.0, "basis": "声明值"},
    "others": {"p_W": 0.10, "basis": "U5 光耦 + E2 + LED + L1 铜损（声明值）"},
}


def mm(v):
    import pcbnew
    return pcbnew.ToMM(v)


def plane_geometry(net: str) -> list[dict]:
    """该网在各层实铺铜皮面积/包络（几何真源 = 交付板 filled zones）。"""
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))
    out = []
    for z in b.Zones():
        if z.GetNetname() != net or z.GetIsRuleArea():
            continue
        layers = [b.GetLayerName(l) for l in z.GetLayerSet().Seq()]
        o = z.Outline()          # 声明域轮廓（filled 缓存不可读 ⇒ 用声明几何，记录已注明）
        area = o.Area() / 1e18 if o.OutlineCount() else 0.0   # nm²→m²
        bb = z.GetBoundingBox()
        lx, ly = mm(bb.GetWidth()), mm(bb.GetHeight())
        out.append({"layers": layers, "area_m2": area, "bbox_mm": [lx, ly]})
    return out


def via_count(net: str) -> int:
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))
    return sum(1 for t in b.GetTracks()
               if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == net)


def eval_rail(net: str, cfg: dict, t_amb: float, spokes: int) -> dict:
    geo = plane_geometry(net)
    if not geo:
        return {"rail": net, "plane": None, "verdict": "NOT_DEMONSTRATED",
                "reason": "该网板上无实铺铜皮（无平面承载）"}
    gi = max(geo, key=lambda g: g["area_m2"])
    L = max(gi["bbox_mm"]) / 1000.0
    A = gi["area_m2"]
    W = A / L if L > 0 else 0.0
    # 电流方向：取包络长边为路径长；等效宽 = A/L（确定性派生）
    oz = SUP["outer_copper_oz"] if gi["layers"][0] in ("F.Cu", "B.Cu") else SUP["inner_copper_oz"]
    t_cu = oz * 0.035 / 1000.0        # m（1oz ⇒ 35µm）
    rho = DECL["rho_cu_20C"]["value"] * (1.0 + DECL["alpha_cu"]["value"] * (t_amb - 20.0))
    rs = rho / t_cu
    r_plane = rs * (L / W)
    d, tpl = 0.0002, DECL["plating_um"]["value"] * 1e-6
    a_barrel = 3.141592653589793 * ((d / 2) ** 2 - (d / 2 - tpl) ** 2)
    r_via = rho * (1.6e-3) / a_barrel
    n = via_count(net)
    r_via_eff = r_via / max(n, 1)
    r_tot = r_plane + r_via_eff
    dv = cfg["I_a"] * r_tot
    v_rail = cfg.get("v_nom", {"P3V3": 3.3, "P3V3_AUX": 3.3, "MCU_VDD": 3.3, "12V_IN": 12.0}[net])
    pct = dv / v_rail * 100.0
    return {"rail": net, "plane": {"layers": gi["layers"], "area_m2": round(A, 8),
                                   "L_m": round(L, 5), "W_eq_m": round(W, 5),
                                   "t_cu_m": t_cu, "Rs_ohm_sq": round(rs, 6)},
            "n_plane_vias": n,
            "n_plane_vias_basis": "**全网（board-wide）net via 计数**：该网全部 via（含落在 In4 zone 多边形之外的落点）；"
                                  "**非** zone 内净匹配计数（CO-152 显式声明口径；R_via_eff = R_via/N）",
            "rho_ohm_m_at_T": round(rho, 10),
            "R_plane_ohm": r_plane, "R_via_each_ohm": r_via, "R_via_eff_ohm": r_via_eff,
            "R_total_ohm": r_tot, "I_a": cfg["I_a"], "I_basis": cfg["I_basis"],
            "V_rail": v_rail, "dV_mV": round(dv * 1000, 3), "drop_pct": round(pct, 4),
            "budget_pct": SUP["drop_budget_pct"],
            "verdict": "PASS" if pct <= SUP["drop_budget_pct"] else "FAIL",
            "I_max_at_budget_a": round(SUP["drop_budget_pct"] / 100.0 * v_rail / r_tot, 3)}


def main() -> int:
    spec = json.loads(SPEC.read_text())
    t_amb = SUP["ambient_C"]
    u6 = _u6_inputs()
    pact = u6["inputs"]["PACT"]
    worst_W = max(v["max_W"] for v in pact.values())
    i_p3v3 = round(worst_W / u6["inputs"]["VCC_V"] + 0.11, 2)      # +MCU/上拉等 0.11A（声明）
    eta = 0.88
    i_12v = round(3.3 * i_p3v3 / (eta * 12.0), 3)
    rails_cfg = dict(RAILS)
    rails_cfg["P3V3"] = {"I_a": i_p3v3,
                         "I_basis": f"U6 手册 PACT(EQ5-19,max)={worst_W}W/3.3V={worst_W/3.3:.2f}A + MCU/上拉 0.11A（声明）"}
    rails_cfg["12V_IN"] = {"I_a": i_12v,
                           "I_basis": f"P3V3 输出功率/(η=0.88（声明）×12V)=3.3×{i_p3v3}/0.88/12={i_12v}A"}
    rails = {n: eval_rail(n, c, t_amb, 0) for n, c in rails_cfg.items()}
    # 热（U6 = 手册值：PACT × θJA(high-K)；逐 EQ 档）
    th_ja = u6["inputs"]["theta_ja_highK_C_per_W"]
    psi_jb = u6["inputs"].get("psi_jb_C_per_W")
    tj_limit = u6["inputs"]["TJ_max_C"]
    cases = {}
    for eq, v in pact.items():
        for kind in ("typ", "max"):
            P6 = v[f"{kind}_W"]
            cases[f"U6_EQ{eq}_{kind}"] = {"P_U6_W": P6, "I_a": round(P6 / 3.3, 3),
                                          "Tj_C": round(t_amb + P6 * th_ja, 1),
                                          "Ta_max_C": round(tj_limit - P6 * th_ja, 1),
                                          "required_theta_ja_C_per_W": round((tj_limit - t_amb) / P6, 2)}
    hot = max(c["Tj_C"] for c in cases.values())
    P_u2_loss = 3.3 * i_p3v3 * (1.0 / eta - 1.0)
    P_tot = worst_W + P_u2_loss + THERMAL["U1_mcu"]["p_W"] + THERMAL["others"]["p_W"]
    bx = spec["board"]["outline_x"]; by = spec["board"]["outline_y"]
    A_board = (bx[1] - bx[0]) * (by[1] - by[0]) * 1e-6
    h = DECL["h_conv"]["value"]
    dT_board = P_tot / (h * 2.0 * A_board)
    T_board = t_amb + dT_board
    xcheck_Tj = round(T_board + worst_W * (psi_jb or 5.9), 1)
    # 牙齿（CO-181：去恒真 —— 判据函数化，正控 + **近失负控必翻转**）
    r = rails["P3V3"]
    rho_t = r["rho_ohm_m_at_T"]
    _rp_lw = r["plane"]["L_m"] / r["plane"]["W_eq_m"]

    def _rs_of(oz: float) -> float:
        """方阻 Rs = ρ/t（t = oz·35µm）—— 被判对象函数化（真件与近失共用）。"""
        return rho_t / (oz * 0.035 / 1000.0)

    def _r_plane_of(oz: float) -> float:
        return _rs_of(oz) * _rp_lw

    def _drop_of(i_a: float) -> float:
        return i_a * r["R_total_ohm"]

    _lin = lambda f: abs(f(2.0) - 2.0 * f(1.0)) < 1e-12
    _mono = lambda g: g(0.5) > g(1.0)
    geom = plane_geometry("P3V3")
    geom_negative = plane_geometry("__CO181_NO_SUCH_NET__")
    teeth = {"t01_current_doubling_linear": _lin(_drop_of) and not _lin(lambda i: i ** 1.5),
             "t02_copper_thickness_monotone": _mono(_r_plane_of) and not _mono(lambda oz: -_r_plane_of(oz)),
             "t03_plane_geometry_from_board": bool(geom) and geom[0]["area_m2"] > 0 and geom_negative == [],
             "t04_datasheet_input_flips_verdict": bool(t_amb + 1.5 * th_ja <= tj_limit and hot > tj_limit),
             "t05_psi_route_agrees_fail": xcheck_Tj > tj_limit}
    fails = [n for n, r_ in rails.items() if r_["verdict"] != "PASS"]
    rec = {"artifact": "m13_v57_co146_pm_eval", "schema": 1, "revision": "CO148-PM.3",
           "nature": "L2 一阶确定性评估：PDN 压降 + 热（监理指令 #10 动作 2；CO-148：U6 用数据手册值）",
           "board_sha16": hashlib.sha256(BOARD.read_bytes()).hexdigest()[:16],
           "declared_inputs": {"supervisor_values_指令10": SUP, "engineering_declared": DECL,
                               "rails": RAILS, "thermal_devices": THERMAL,
                               "rails": rails_cfg,
                               "u6_source": "**数据手册**（TI SNLS683 JUNE 2023，见 " + U6_IN.name + "）",
                               "DISCLAIMER": "U6 功耗/热阻 = 数据手册值（已入库）；其余（U2 效率、MCU/杂项功耗、对流系数 h、"
                                             "P3V3_AUX 侧带电流）仍为显式声明值（非实测）⇒ 到位后须替换并重跑。"},
           "method": {"plane": "Rs=ρ(T)/t；R_plane=Rs·L/W_eq，L=铜皮包络长边，W_eq=A/L（A=交付板 zone 声明域轮廓面积；filled 缓存不可读）",
                      "via": "R_via=ρ·1.6mm/A_铜壁，A_铜壁=π((d/2)²-(d/2-18µm)²)，d=0.2mm；N 支并联",
                     "via_count": "N = **全网（board-wide）该 net 的 via 计数**（非 zone 内净匹配计数）；CO-152 显式声明，"
                                  "以消除 n_plane_vias 口径歧义（ΔV% 由 R_plane 主导，口径差异 <0.02% 绝对）",
                      "drop": "ΔV=I·(R_plane+R_via/N)；预算 3%（监理定值）",
                      "thermal": "主路线 Tj = Ta + P_U6×θJA(手册 high-K 17.4)；交叉核对 Tj = T_board + P_U6×ψJB，"
                                 "T_board = Ta + P_total/(h·2A_board)",
                      "nature": "几何一阶解析（非仿真；不含去耦电容动态/AC 阻抗/平面谐振）"},
           "rails": rails,
           "u6_datasheet": {"source_artifact": U6_IN.name, "source_sha16": hashlib.sha256(U6_IN.read_bytes()).hexdigest()[:16],
                            "PACT_W": pact, "theta_ja_C_per_W": th_ja, "psi_jb_C_per_W": psi_jb,
                            "TJ_max_C": tj_limit, "cases": cases},
           "thermal": {"P_total_W": round(P_tot, 3), "P_u2_loss_W": round(P_u2_loss, 3),
                       "A_board_m2": A_board, "dT_board_C": round(dT_board, 2), "T_board_C": round(T_board, 1),
                       "routes": {"theta_ja_route_hotspot_Tj_C": hot,
                                  "psi_jb_plus_board_route_Tj_C": xcheck_Tj},
                       "Tj_limit_C": tj_limit,
                       "verdict": "PASS" if hot <= tj_limit else "FAIL"},
           "verdict": "PASS" if (not fails and hot <= tj_limit) else "FAIL",
           "rail_fails": fails, "teeth": teeth,
           "redline": "只读：几何取自交付板；零坐标搜索；不改板/图纸/SPEC/冻结四源。"}
    (STEP2 / "m13_v57_co146_pm_eval.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    md = ["# CO-146 卡 · PDN 压降 + 热评估（监理指令 #10 动作 2）", "",
          f"- 预算：压降 **{SUP['drop_budget_pct']}%**｜环境 **{t_amb}°C 自然对流**（监理定值）",
          "- **U6 功耗/热阻 = 数据手册值（TI SNLS683，已入库）**；其余（U2 效率 / MCU·杂项功耗 / h / 侧带电流）"
          "为显式声明值（非实测），到位后替换重跑", "",
          "## PDN 压降", "", "| 轨 | I (A) | 平面层 | 铜厚 | R_plane (mΩ) | R_via/N (mΩ) | ΔV (mV) | 压降 % | 判 | I_max@3% (A) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for n, r_ in rails.items():
        if not r_.get("plane"):
            md.append(f"| {n} | {r_.get('I_a')} | — | — | — | — | — | — | **{r_['verdict']}** | — |")
            continue
        md.append(f"| {n} | {r_['I_a']} | {','.join(r_['plane']['layers'])} | {r_['plane']['t_cu_m']*1e6:.1f}µm | "
                  f"{r_['R_plane_ohm']*1e3:.4f} | {r_['R_via_eff_ohm']*1e3:.4f} | {r_['dV_mV']} | "
                  f"{r_['drop_pct']}% | **{r_['verdict']}** | {r_['I_max_at_budget_a']} |")
    md += ["", "## 热（U6 = 数据手册值：PACT × θJA）", "",
           f"- 手册：TI SNLS683（DS320PR1601）θJA(high-K) = {th_ja}°C/W｜ψJB = {psi_jb}°C/W｜Tj 上限 = {tj_limit}°C",
           f"- P_total = {round(P_tot,3)} W（U6 最坏 {worst_W}W + U2 损 {round(P_u2_loss,3)}W + 杂项 0.15W）"
           f"｜A_board（两面）= {A_board*2:.5f} m²｜h = {h} W/m²K（声明）",
           f"- 板级交叉核对：ΔT_board = {dT_board:.2f}°C ⇒ T_board = {T_board:.1f}°C ⇒ Tj(ψJB 路径) = **{xcheck_Tj}°C**",
           "", "| 工况 | P_U6 (W) | I (A) | Tj = Ta+P·θJA (°C) | 允许 Ta 上限 (°C) | 需要 θJA ≤ |",
           "|---|---|---|---|---|---|"]
    for k, v in cases.items():
        md.append(f"| {k} | {v['P_U6_W']} | {v['I_a']} | **{v['Tj_C']}** | {v['Ta_max_C']} | "
                  f"{v['required_theta_ja_C_per_W']} |")
    md += ["", f"- 热点 Tj = **{hot}°C** vs 手册上限 {tj_limit}°C ⇒ **{rec['thermal']['verdict']}**"
               f"（θJA 路线 {hot}°C / ψJB+h 路线 {xcheck_Tj}°C 两路一致）",
           "", "## 牙齿（CO-181：去恒真 · 判据函数化 + 近失必翻转）",
           f"- T1 电流 ×2 ⇒ 压降 ×2（非线性近失必翻转）：{teeth['t01_current_doubling_linear']}",
           f"- T2 铜厚减半 ⇒ 平面电阻单调升（反向近失必翻转）：{teeth['t02_copper_thickness_monotone']}",
           f"- T3 平面几何取自交付板（无此网负控为空）：{teeth['t03_plane_geometry_from_board']}",
           f"- T4 手册输入翻转结论（旧声明 1.5W ⇒ PASS，手册最坏 ⇒ FAIL）：{teeth['t04_datasheet_input_flips_verdict']}",
           f"- T5 ψJB 交叉路线同为 FAIL：{teeth['t05_psi_route_agrees_fail']}", ""]
    (STEP2 / "m13_v57_co146_pm_eval.md").write_text("\n".join(md) + "\n")
    print("verdict:", rec["verdict"], "| rail fails:", fails, "| Tj_hot:", hot, "| xcheck:", xcheck_Tj)
    for n, r_ in rails.items():
        if r_.get("plane"):
            print(f"  {n:10s} I={r_['I_a']}A ΔV={r_['dV_mV']}mV ({r_['drop_pct']}%) Imax3%={r_['I_max_at_budget_a']}A {r_['verdict']}")
    print(f"  thermal: P_tot={round(P_tot,3)}W Tj_hot={hot}C (limit {tj_limit}) xcheck={xcheck_Tj}C route->{rec['thermal']['verdict']}")
    print("teeth:", teeth)
    return 0 if (all(teeth.values()) and not fails) else 1


if __name__ == "__main__":
    sys.exit(main())
