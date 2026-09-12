#!/usr/bin/env python3
"""CO-146 — boundary 收口件登记（§23）+ 现行态 pin 再对齐（co77 口径）。

幂等：§23 已存在则整段替换；pin 重对齐按「文件→当前 sha16」表逐条替换**非历史**引用。
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L5 = K2 / "pm_gate/artifacts/k2_v4/L5"
STEP2 = L3 / "mcio_feas_step2"
DOC = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"
MARK = "## 23. CO-146"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    txt = DOC.read_text()
    # ── 1. 现行态 pin 再对齐（只改「文件 <-> 旧 sha」这种当前态引用） ─────────
    realign_files = None   # None = 全量（现行态引用一律对齐当前实件 sha16；历史引用跳过）
    CITE = re.compile(r"`([A-Za-z0-9][A-Za-z0-9_./\-]*\.(?:json|md|py|kicad_pcb|kicad_pro|kicad_dru))`"
                      r"(?:[^|`\n]*\|\s*|\s+)`([0-9a-f]{16})`")
    HIST_AFTER = re.compile(r"^[\s）)】,，、/]*[（(]?\s*(已取代|历史|应为|实为)")

    def _fix(m: re.Match) -> str:
        name, sha = m.group(1), m.group(2)
        if realign_files is not None and Path(name).name not in realign_files:
            return m.group(0)
        nxt = txt[m.end():m.end() + 16]
        if HIST_AFTER.match(nxt) or "→" in txt[m.end():m.end() + 8] or "->" in txt[m.end():m.end() + 8]:
            return m.group(0)
        cands = [Path(name), STEP2 / Path(name).name, L3 / Path(name).name, L2 / Path(name).name,
                 K2 / "tools" / Path(name).name, K2 / Path(name).name,
                 K2 / "_shared" / "eda_core" / Path(name).name,
                 K2.parent / "_shared" / "eda_core" / Path(name).name]
        hit = next((c for c in cands if c.exists()), None)
        if hit is None:
            return m.group(0)
        cur = s16(hit)
        return m.group(0).replace(sha, cur) if cur != sha else m.group(0)

    txt = CITE.sub(_fix, txt)
    # ── 2. §23 替换/追加 ────────────────────────────────────────────────────
    rows = [("冻结 SPEC `SPEC_k2_v4.spec-rev-19.json`(未变)", L3 / "SPEC_k2_v4.spec-rev-19.json"),
            ("交付板 `k2_v4_8L.l4.kicad_pcb`(未变)", K2 / "k2_v4_8L.l4.kicad_pcb"),
            ("阻抗表 `m13_v57_co146_impedance_table.json`", STEP2 / "m13_v57_co146_impedance_table.json"),
            ("PM 评估 `m13_v57_co146_pm_eval.json`", STEP2 / "m13_v57_co146_pm_eval.json"),
            ("DFM 闸 `m13_v57_co146_jlc_dfm_gate.json`", STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
            ("JLC 能力表 `m13_v57_co146_jlc8_capability.json`", STEP2 / "m13_v57_co146_jlc8_capability.json"),
            ("通孔化反证 `m13_v57_co146_through_via_probe.json`", STEP2 / "m13_v57_co146_through_via_probe.json"),
            ("打样包记录 `m13_v57_co146_jlc_fab_package.json`", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
            ("定性更正 `m13_v57_co146_jlc_rebind.json`", STEP2 / "m13_v57_co146_jlc_rebind.json"),
            ("L2 定值绑定 `jlc_prototype_parameters_v1.json`", L2 / "jlc_prototype_parameters_v1.json"),
            ("登记簿 `input_defect_register_v1.json`(+2 OPEN)", L2 / "input_defect_register_v1.json"),
            ("co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
            ("工具 `p3_v57_co146_jlc_dfm_gate.py`", K2 / "tools/p3_v57_co146_jlc_dfm_gate.py"),
            ("工具 `p3_v57_co146_impedance_table.py`", K2 / "tools/p3_v57_co146_impedance_table.py"),
            ("工具 `p3_v57_co146_pm_eval.py`", K2 / "tools/p3_v57_co146_pm_eval.py"),
            ("工具 `p3_v57_co146_jlc_fab_package.py`", K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
            ("工具 `p3_v57_co146_through_via_probe.py`", K2 / "tools/p3_v57_co146_through_via_probe.py"),
            ("工具 `p3_v57_co146_closeout.py`", K2 / "tools/p3_v57_co146_closeout.py")]
    sec = [MARK + "（L2 · 监理指令 #10「JLC 8 层打样就绪」）：阻抗表 / PM 评估 / 打样包 / DFM 闸 / 定性更正", "",
           "> 依据：`instruction-10-jlc-prototype-ready.md`（监理定值：JLC08161H 1.6mm / 外层 1oz 内层 0.5oz / "
           "85Ω±10% 勾阻抗控制 / ENIG / 压降 3% / 40°C 自然对流）。冻结四源 **逐字节未动**（SPEC `5f72182a2616392c`、"
           "板 `d4e81f647be7f980`）。", "",
           "**动作 1 阻抗表**：JLC08161H 交付几何双模型（IPC-2141 族 / Hammerstad–Jensen+Cohn）交叉核对 ⇒ "
           "as-built 对内净距下 85Ω±10% **PASS**；设计名义最宽间距（0.6mm 中心）下有 1 项 model-spread 越界 "
           "⇒ 列入下单备注（请 JLC 阻抗表覆盖该几何）。终判 = JLC 阻抗控制服务。", "",
           "**动作 2 PM 评估**：一阶确定性（平面 Rs·L/W + 过孔并联 + 热 ΔT=P/(h·2A)）。四轨压降 "
           "0.007%–0.69%（预算 3%）全 PASS；热 ΔT_board 29.0°C ⇒ T_board 69.0°C、热点 Tj(U6) 106.5°C < 125°C。"
           "**电流/功耗/θJA/对流系数为显式声明值（非实测）**，器件手册到位后替换重跑。", "",
           "**动作 3 打样包**：`L5/jlc_package/`（Gerber RS-274X ×13 含 8 铜层 + Excellon 钻孔 ×5 + 叠层图 SVG + "
           "阻抗表 + 层序 + 下单备注 + MANIFEST）；命令+sha 可复现（时间戳规范化；重跑逐字节同）。", "",
           "**动作 4 DFM 闸（对照 JLC 公布能力）**：**FAIL** —— ① **盲/埋孔**：交付板 **220/493** 支非通孔"
           "（含 `In2.Cu→In5.Cu` **埋孔 88**），而 JLC 标准服务 *Blind/Buried Vias Not supported*；原地改通孔实测 "
           "**111 项 shorting_items** ⇒ 现行 W3 派生**结构依赖盲/埋孔**；② **阻焊桥 1 处**（JLC 0.09mm 下限，"
           "`PCIE_UP3_N`×`R3.pad2(PWR_BTN_ISO)`）。其余项（线宽 0.16≥0.09、孔 0.2/盘 0.35、环宽 0.075、孔距 0.25、"
           "板边 0.30、尺寸/层数/铜厚/板厚/表面处理）全 PASS。", "",
           "**动作 5 定性更正**：**撤回「外部输入阻塞」**（阻抗终判改绑 JLC 阻抗控制服务；PM 改绑监理定值 + 本件评估）；"
           "SPEC `impedance.coupon_required=true` **字段不动**（改绑的是解释与签署路径）；登记簿 **+2 OPEN**"
           "（盲/埋孔 = 结构/工艺类别 ⇒ 需 owner 一句话；阻焊桥 = 可修）。", "",
           "**残留（如实）**：① owner：盲/埋孔出路 (a) 走 JLC advanced 盲埋孔通道 / (b) 重开 W3 通孔化派生；"
           "② owner：J2 接口 3W 适用域（既有 L1）；③ 复评债 CO-142..145 + **CO-146 全部产物**（另一会话，禁自评）。", "",
           "| 工件 | sha16 |", "|---|---|"]
    for label, p in rows:
        if p.exists():
            sec.append(f"| {label} | `{s16(p)}` |")
    sec.append("")
    body = "\n".join(sec)
    if MARK in txt:
        txt = re.sub(re.escape(MARK) + r"[\s\S]*?(?=\n## |\Z)", body, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body
    MARK24 = "## 24. CO-147"
    sec24 = [MARK24 + "（**L2 自裁** · 过孔策略/打样渠道 · J2 对间适用域 · 阻焊桥）：三题裁定 + 登记簿 3 项转 CLOSED", "",
             "> 依据：LAYOUT_CONSTITUTION 第二章（L2 = 叠层分配/PDN/走廊分配/**过孔策略**/等长窗口/热机械 ⇒ ARCHER 自裁；"
             "L1 仅 器件分区/接口朝向/信号流向/电源域划分/球重映射）。需求（目的/原则）未变更；板/SPEC 逐字节未动。", "",
             "**R1 过孔策略/渠道**：交付板 220/493 支盲/埋孔为现行 W3 派生**结构必需**（原地通孔化实测 "
             f"{json.loads((STEP2 / 'm13_v57_co146_through_via_probe.json').read_text())['delta_by_type'].get('shorting_items')} "
             "项 shorting_items）⇒ 维持策略、下单渠道绑定 **JLC advanced/盲埋孔**（DFM review + 重报价）；如需通孔板 ⇒ 另开 W3 "
             "通孔化重派生（L2 候选，前置 = 引擎通孔模型 + 可行性证明）。**不涉层数变更 ⇒ 属 L2（过孔策略），非 L1（HDI/层数）。**", "",
             "**R2 J2 landing 对间 3W**：连接器 0.6 节距 ⇒ 接口固有不可路由（F.Cu 实测铜边 0.3294 vs 0.41）⇒ "
             "**ACCEPT_L2（声明偏差 + hash-pin 依据）**，需求目的「对间不串扰」不变，终判 = SI/JLC 阻抗控制服务；"
             "域声明与既有 ECN-001 逃逸豁免同族、口径一致。", "",
             "**R3 阻焊桥 1 处**：`R3.pad2(PWR_BTN_ISO)` 开窗缘 ↔ `PCIE_UP3_N` 铜缘 **0.0695mm** < JLC 0.09mm（欠 0.0205）⇒ "
             "**ACCEPT_L2_WITH_FAB_REVIEW**（并入同一工程评审；不触铜几何）；回退修法 = R3 开窗 0.05→0.02mm。", "",
             "| 工件 | sha16 |", "|---|---|"]
    for label, pth in [("L2 裁定件 `L2_RULING_via_channel_and_interpair_domain_v1.md`",
                        L2 / "L2_RULING_via_channel_and_interpair_domain_v1.md"),
                       ("记录 `m13_v57_co147_l2_ruling.json`", STEP2 / "m13_v57_co147_l2_ruling.json"),
                       ("登记簿 `input_defect_register_v1.json`(3 项 CLOSED / OPEN 0)", L2 / "input_defect_register_v1.json"),
                       ("DFM 闸 `m13_v57_co146_jlc_dfm_gate.json`", STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
                       ("通孔化反证 `m13_v57_co146_through_via_probe.json`", STEP2 / "m13_v57_co146_through_via_probe.json"),
                       ("打样包记录 `m13_v57_co146_jlc_fab_package.json`", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
                       ("工具 `p3_v57_co147_l2_ruling.py`", K2 / "tools/p3_v57_co147_l2_ruling.py")]:
        if pth.exists():
            sec24.append(f"| {label} | `{s16(pth)}` |")
    sec24.append("")
    body24 = "\n".join(sec24)
    if MARK24 in txt:
        txt = re.sub(re.escape(MARK24) + r"[\s\S]*?(?=\n## |\Z)", body24, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body24
    # ── §25 CO-148（U6 手册输入 → 热超限） ────────────────────────────────
    MARK25 = "## 25. CO-148"
    u6 = json.loads((STEP2 / "m13_v57_co148_u6_ds320pr1601_inputs.json").read_text())
    pm = json.loads((STEP2 / "m13_v57_co146_pm_eval.json").read_text())
    tr = json.loads((STEP2 / "m13_v57_co148_thermal_ruling.json").read_text())
    _regc25 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec25 = [MARK25 + "（L2 · **PM 输入升级为器件手册值** ⇒ U6 热超限）：热裁定 + 登记 + 台账", "",
             "> 触发：监理指令 #10 要求「各轨电流由设计/器件手册导出」。U6 = DS320PR1601，手册 **TI SNLS683（JUNE 2023）**"
             f"已抓取入库（节录件 + PDF sha256；`{STEP2.name}/m13_v57_co148_ds320pr1601_snls683_excerpt.txt` `{s16(STEP2 / 'm13_v57_co148_ds320pr1601_snls683_excerpt.txt')}`）。", "",
             f"**事实（机判）**：手册 PACT = {u6['inputs']['PACT']['0-2']['typ_W']}–{u6['inputs']['PACT']['5-19']['max_W']}W、"
             f"θJA(high-K) = {u6['inputs']['theta_ja_highK_C_per_W']}°C/W、ψJB = {u6['inputs'].get('psi_jb_C_per_W')}、"
             f"Tj 上限 **{tr['Tj_limit_C']}°C**；按监理定值 40°C 自然对流 ⇒ **Tj {tr['best']['Tj_C']}°C"
             f"（{tr['best']['case']}）～{tr['worst']['Tj_C']}°C（{tr['worst']['case']}）全档超限**，"
             f"ψJB+h 交叉路线 {pm['thermal']['routes']['psi_jb_plus_board_route_Tj_C']}°C 同判 FAIL。"
             f"散热路径：U6 {tr['thermal_path']['gnd_balls']} GND 球 / 域内 GND via 仅 {tr['thermal_path']['gnd_vias_in_u6_bbox']}。"
             "（CO-146 的 U6 声明功耗 1.5W 偏低 3–4.7 倍 = PM 输入缺陷，已替换。）", "",
             f"**L2 裁定**：R4-1 PCB 散热路径义务（U6 域 GND via 阵列补强 / GND 平面覆盖 / 铜面最大化，随下一轮几何修订 + G4 重基线）；"
             f"R4-2 **输入冲突上报**：40°C 自然对流与手册不相容 ⇒ 须重裁环境/风冷输入（选项：a 强制风冷/散热片使 θJA_eff ≤ "
             f"{tr['worst']['required_theta_ja_cur_placeholder'] if False else tr['cases'][tr['worst']['case']]['required_theta_ja_C_per_W']}–"
             f"{tr['cases'][tr['best']['case']]['required_theta_ja_C_per_W']}°C/W；b 环境 ≤ {tr['cases'][tr['best']['case']]['Ta_max_C']}°C；c 复核 EQ/功耗假设）。"
             "**PDN 侧不受影响**：手册电流（P3V3 2.23A）下四轨压降 0.007–0.69% ≪ 3%（I_max@3% 4.3–62.6A）。", "",
             f"**登记**：+2（`{tr['co148_items'][0]}` HIGH；`{tr['co148_items'][1]}` MED）"
             f"⇒ 登记簿 {_regc25['total']} 项（现行值，CO-155 去下游快照后改读登记簿）；台账 DV-CO146-THERMAL = `UNREACHABLE_REGISTERED`。", "",
             "| 工件 | sha16 |", "|---|---|"]
    for label, pth in [("L2 裁定件 `L2_RULING_u6_thermal_v1.md`", L2 / "L2_RULING_u6_thermal_v1.md"),
                       ("记录 `m13_v57_co148_thermal_ruling.json`", STEP2 / "m13_v57_co148_thermal_ruling.json"),
                       ("手册输入 `m13_v57_co148_u6_ds320pr1601_inputs.json`", STEP2 / "m13_v57_co148_u6_ds320pr1601_inputs.json"),
                       ("PM 评估 `m13_v57_co146_pm_eval.json`（手册输入）", STEP2 / "m13_v57_co146_pm_eval.json"),
                       ("登记簿 `input_defect_register_v1.json`", L2 / "input_defect_register_v1.json"),
                       ("台账 `derived_value_ledger_v1.json`", L2 / "derived_value_ledger_v1.json"),
                       ("工具 `p3_v57_co148_u6_datasheet_inputs.py`", K2 / "tools/p3_v57_co148_u6_datasheet_inputs.py"),
                       ("工具 `p3_v57_co148_thermal_ruling.py`", K2 / "tools/p3_v57_co148_thermal_ruling.py")]:
        if pth.exists():
            sec25.append(f"| {label} | `{s16(pth)}` |")
    sec25.append("")
    body25 = "\n".join(sec25)
    if MARK25 in txt:
        txt = re.sub(re.escape(MARK25) + r"[\s\S]*?(?=\n## |\Z)", body25, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body25
    # ── §26 CO-149/CO-150（热机械派生要求 + K9 扩域） ─────────────────────
    MARK26 = "## 26. CO-149"
    m = json.loads((STEP2 / "m13_v57_co149_u6_thermal_mitigation.json").read_text())
    k = json.loads((STEP2 / "m13_v57_co150_k9_domain_gate.json").read_text())
    c124 = json.loads((STEP2 / "m13_v57_co124_input_selfcheck_gate.json").read_text())
    sec26 = [MARK26 + " / CO-150（L2 自裁 · 热机械派生实现要求 + K9 热/压降域扩闸）：U6 散热要求 + 闸硬化", "",
             f"**CO-149（热机械派生，解 CO-148 R4-2；监理定值 Ta = {m['ta_C']}°C 不变）**：",
             f"- 两路线互校：手册 θJA(high-K) {m['routes']['datasheet_theta_ja']} °C/W vs 本板一阶 "
             f"ψJB+1/(h·2A) = **{m['routes']['board_first_order_theta_ja']} °C/W**（差 1.0%，模型可信）；"
             f"其中**板→空气占 {m['routes']['board_to_air_share_pct']}%** ⇒ 瓶颈不在走线/via。",
             f"- 派生要求：θJA_eff ≤ **{m['required']['theta_ja_eff_max_C_per_W']}**（最重档）～"
             f"{m['cases']['U6_EQ0-2_typ']['theta_ja_required_C_per_W']} °C/W；"
             f"或强制风冷 h_eff ≥ **{m['required']['h_required_range_W_per_m2K'][0]}–{m['required']['h_required_range_W_per_m2K'][1]} W/m²K**；"
             f"或顶部散热片预算 θJC+R_int+θ_HS ≤ **{m['required']['top_sink_budget_range_C_per_W'][0]}–{m['required']['top_sink_budget_range_C_per_W'][1]} °C/W**。",
             "- 方案（声明值）：O0 现状 17.22（0/4 档）、O1 风冷 11.56（3/4 档）、**O2 散热片+风冷 11.0（4/4 档 ✓）**"
             "⇒ **自然对流全档不可达 ⇒ 系统散热为必需项**（非可选项）。",
             "- **R5-3**：PCB 侧**不改几何**（瓶颈为板→空气；U6 域热过孔仅影响 ψJB 项）⇒ CO-148 R4-1「GND via 阵列」"
             "由义务降为**可选**，避免为边际收益触发 G4 全链重基线。终判 = 实板热测/仿真。", "",
             f"**CO-150（闸硬化）**：co124 K9 扩 `thermal_option_domain`（∃ 声明散热方案覆盖最重工况；现状不达标须显式声明 "
             f"required_mitigation）与 `drop_domain`（每轨 ΔV% ≤ 预算%）+ 负控 T10/T10b/T11/T11b ⇒ "
             f"co124 rev **{c124['revision']}** verdict {c124['verdict']} findings {c124['n_findings']}；"
             f"关闭 CO-148 登记的 K9 缺口项 ⇒ **登记簿 OPEN 0**。", "",
             "| 工件 | sha16 |", "|---|---|"]
    for label, pth in [("L2 裁定件 `L2_RULING_u6_thermal_mitigation_v1.md`", L2 / "L2_RULING_u6_thermal_mitigation_v1.md"),
                       ("记录 `m13_v57_co149_u6_thermal_mitigation.json`", STEP2 / "m13_v57_co149_u6_thermal_mitigation.json"),
                       ("记录 `m13_v57_co150_k9_domain_gate.json`", STEP2 / "m13_v57_co150_k9_domain_gate.json"),
                       ("co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
                       ("登记簿 `input_defect_register_v1.json`(OPEN 0)", L2 / "input_defect_register_v1.json"),
                       ("台账 `derived_value_ledger_v1.json`", L2 / "derived_value_ledger_v1.json"),
                       ("工具 `p3_v57_co149_thermal_mitigation_derive.py`", K2 / "tools/p3_v57_co149_thermal_mitigation_derive.py"),
                       ("工具 `p3_v57_co150_k9_domain_gate.py`", K2 / "tools/p3_v57_co150_k9_domain_gate.py")]:
        if pth.exists():
            sec26.append(f"| {label} | `{s16(pth)}` |")
    sec26.append("")
    body26 = "\n".join(sec26)
    if MARK26 in txt:
        txt = re.sub(re.escape(MARK26) + r"[\s\S]*?(?=\n## |\Z)", body26, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body26
    # ── §27 CO-151（非执行者对抗复评 rev-19 + CO-142..150） ────────────────
    MARK27 = "## 27. CO-151"
    r151 = json.loads((STEP2 / "m13_v57_co151_rev19_nonexecutor_review.json").read_text())
    sec27 = [MARK27 + "（**非执行者对抗复评** · rev-19 + CO-142..CO-150）：独立重算全复现 + findings 8", "",
             f"**复评人 = 非执行者会话**（未参与 CO-142..150 施加；context 隔离）；**verdict = {r151['verdict']}**；"
             f"只读（除自身记录）。冻结四源 4/4 + 交付板 `{r151['board_sha16']}` 逐字节不变。", "",
             "**独立确认（不复用执行者断言，自一次源重算）**："]
    sec27 += [f"- {x}" for x in r151["independent_confirmations"]]
    sec27 += ["", "**findings**：", "", "| id | sev | kind | 内容 | 修法 |", "|---|---|---|---|---|"]
    sec27 += [f"| {f['id']} | {f['sev']} | {f['kind']} | {f['what']} | {f['fix']} |" for f in r151["findings"]]
    sec27 += ["", "> 复评**只读**：findings **未**写入登记簿（登记簿 scope = SPEC/drc_rules；本类属记录/闸/注册表卫生）"
                  "⇒ 由后续执行 CO 决定登记与重基线（同 CO-108/114 先例）。", "", "| 工件 | sha16 |", "|---|---|"]
    for label, pth in [("工具 `p3_v57_co151_rev19_nonexecutor_review.py`",
                        K2 / "tools/p3_v57_co151_rev19_nonexecutor_review.py"),
                       ("记录 `m13_v57_co151_rev19_nonexecutor_review.json`",
                        STEP2 / "m13_v57_co151_rev19_nonexecutor_review.json"),
                       ("卡 `m13_v57_CO151_rev19_nonexecutor_review.md`",
                        STEP2 / "m13_v57_CO151_rev19_nonexecutor_review.md"),
                       ("co120 provenance 闸 `m13_v57_co120_provenance_pin_gate.json`",
                        STEP2 / "m13_v57_co120_provenance_pin_gate.json"),
                       ("登记簿 `input_defect_register_v1.json`(复评未改)", L2 / "input_defect_register_v1.json"),
                       ("台账 `derived_value_ledger_v1.json`(复评未改)", L2 / "derived_value_ledger_v1.json")]:
        if pth.exists():
            sec27.append(f"| {label} | `{s16(pth)}` |")
    sec27.append("")
    body27 = "\n".join(sec27)
    if MARK27 in txt:
        txt = re.sub(re.escape(MARK27) + r"[\s\S]*?(?=\n## |\Z)", body27, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body27
    # ── §28 CO-152（CO-151 findings 处置 · executor） ─────────────────────────
    MARK28 = "## 28. CO-152"
    sec28 = [MARK28 + "（**L2 自裁 · executor**：CO-151 findings 处置 = 记录/闸/语义卫生 + 2 项勘误）", "",
             "来源 = CO-151 非执行者对抗复评（`PASS_WITH_FINDINGS`，findings 8）。本件**全部在 L2 内自裁**"
             "（记录/闸/派生物语义，非 L1 拓扑/接口/信号流向/球重映射）。**板 / SPEC / 冻结四源逐字节不变**。", "",
             "| CO-151 finding | 处置 | 落点 |", "|---|---|---|",
             "| F-1（low）记录内嵌下游 sha ⇒ pin 不可复现 | **修**：移除 co124/co147/co148/co150 的下游快照"
             "（现行 sha 一律走本 boundary pin 表）；复核 §6/规范序连跑，4 件记录逐字节稳定 | co124/co147/co148/co150 工具 |",
             "| F-1b（low）co120 不覆盖 `*_sha16` 快照键 | **修**：co120 → **CO-120.2** 新增 P5『下游快照声明册』"
             "（`*_sha16_after` 未声明即 FAIL + 负控/正控牙齿）；`SNAPSHOT_DECLARED` 声明 8 件历史件 | co120 |",
             "| F-7（info）豁免注册表 10 条 vs 闸 9 条、2 条依据不可机判 | **修**：删多余豁免（co110←co109）；"
             "EXEMPT 增 `exemption_basis` 分级 → `board_superseded`（机判可证，4 条）/ `declared_historical`"
             "（计数明示，5 条）；依据不成立即 FAIL | co120 |",
             "| F-2（**medium**）CO-147 R2 `as_built_edge_mm` 0.3294 非最劣 | **勘误** → **0.2577**（全量平行≤10°最小铜边；"
             "J2 侧最劣 0.2871；原值留 `as_built_edge_cited_prev`）。裁定结论（接口固有 ⇒ ACCEPT_L2）不变 | CO-147 工具/裁定件 |",
             "| F-3（low）CO-147 R3 叙述 0.0065mm 与本件 `shortfall_mm` 0.0205 矛盾 | **勘误** → 0.0205（与 facts 一致） | CO-147 工具/裁定件 |",
             "| F-4（low）ψJB 作加性热阻/『互校』措辞/ h 敏感度未披露 | **补**：CO-149 增 `sensitivity` 块"
             "（ψJB↔RθJB：所需 h [8.15,16.38]→[8.29,16.99]，更保守 +3.4%；h 敏感度：8.0→0/4、8.5→1/4、16→3/4）"
             "＋牙齿 t04/t05；文档 §1 改称『一致性核对（非独立证据）』；co148 解析器补 RθJB（七值牙齿） | CO-149 / co148 解析器 |",
             "| F-5（low）`n_plane_vias` 口径未声明 | **标注**：增 `n_plane_vias_basis` + `method.via_count`"
             "（= 全网 net via 计数，非 zone 内净匹配；ΔV% 由 R_plane 主导，差异 <0.02% 绝对） | CO-146 PM 评估 |",
             "| F-6（info）阻抗『两套独立』名不副实 | **正名**：『M1 = SPEC `dielectric_8l_basis` 同式同输入一阶复现"
             "（非独立）+ M2 单一独立模型交叉核对』 | CO-146 阻抗表 |",
             "", "**本件新增约束（自本版起生效）**：", "",
             "1. **R-CO152-1**：记录**不得**内嵌其**下游**工件 sha（`register_sha16` / `register.sha16_after` / "
             "`ledger.sha16_after` / 后续 CO 记录 sha）⇒ 现行 sha 一律由本 boundary pin 表单一承载。",
             "2. **R-CO152-2**：任何记录若出现 `*_sha16_after` 类键，必须在 co120 `SNAPSHOT_DECLARED` 明文声明"
             "（未声明即 FAIL_UNDECLARED_DOWNSTREAM_SNAPSHOT）；现声明 8 件历史件（CO-68/72/73/74/80/82/133/146-rebind）。",
             "3. **R-CO152-3**：co120 豁免必须择一依据类并成立（`board_superseded` 机判可证 / `declared_historical` 计数明示）。",
             "4. **R-CO152-4**（复现序）：规范序 = `co146_imp → co146_pm_eval → co148_inputs → co148_thermal_ruling → "
             "co149 → co147 → co146_dfm → co152_register → co124 → co150 → boundary_append → co77 → co120 → co135 → "
             "co136 → boundary_append`，**循环 2–3 次至 sha 稳定**（boundary pin 表 ⊃ 闸记录 sha，闸记录 ⊃ boundary sha ⇒ "
             "系统不动点，非缺陷；实测 2 轮收敛）。",
             "", "**登记簿**：+3 项 TOOL_DEFECT（`records_snapshot_downstream_sha_causes_pin_drift` / "
             "`co120_pin_scope_omits_sha16_snapshot_keys` / `record_derived_value_semantics_unlabeled`）**全部 CLOSED**；"
             "`meta.counts` 复位（总 27 / OPEN 0）。F-2/F-3 属 L2 裁定件勘误，不在登记簿 scope，记于本 §28。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows28 = [("co152 处置工具 `p3_v57_co152_findings_disposition.py`",
                K2 / "tools/p3_v57_co152_findings_disposition.py"),
               ("co120 闸 `m13_v57_co120_provenance_pin_gate.json`（CO-120.2）",
                STEP2 / "m13_v57_co120_provenance_pin_gate.json"),
               ("co124 `m13_v57_co124_input_selfcheck_gate.json`", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
               ("co147 `m13_v57_co147_l2_ruling.json`", STEP2 / "m13_v57_co147_l2_ruling.json"),
               ("co148 `m13_v57_co148_thermal_ruling.json`", STEP2 / "m13_v57_co148_thermal_ruling.json"),
               ("co149 `m13_v57_co149_u6_thermal_mitigation.json`", STEP2 / "m13_v57_co149_u6_thermal_mitigation.json"),
               ("co150 `m13_v57_co150_k9_domain_gate.json`", STEP2 / "m13_v57_co150_k9_domain_gate.json"),
               ("co146 阻抗表 `m13_v57_co146_impedance_table.json`", STEP2 / "m13_v57_co146_impedance_table.json"),
               ("co146 PM 评估 `m13_v57_co146_pm_eval.json`", STEP2 / "m13_v57_co146_pm_eval.json"),
               ("手册输入 `m13_v57_co148_u6_ds320pr1601_inputs.json`", STEP2 / "m13_v57_co148_u6_ds320pr1601_inputs.json"),
               ("L2 裁定件 `L2_RULING_via_channel_and_interpair_domain_v1.md`",
                L2 / "L2_RULING_via_channel_and_interpair_domain_v1.md"),
               ("L2 裁定件 `L2_RULING_u6_thermal_mitigation_v1.md`", L2 / "L2_RULING_u6_thermal_mitigation_v1.md"),
               ("登记簿 `input_defect_register_v1.json`（27 项 / OPEN 0）", L2 / "input_defect_register_v1.json"),
               ("台账 `derived_value_ledger_v1.json`", L2 / "derived_value_ledger_v1.json")]
    for label, pth in _rows28:
        if pth.exists():
            sec28.append(f"| {label} | `{s16(pth)}` |")
    sec28 += ["", "> **复评债**：本件（CO-152）自身须由**另一会话**复评（禁自评）：重点 = 三处语义标注是否足够、"
                  "co120 P5 是否真能防复发、R2 最劣值勘误是否改变 R2 结论（预期不变）。", ""]
    body28 = "\n".join(sec28)
    if MARK28 in txt:
        txt = re.sub(re.escape(MARK28) + r"[\s\S]*?(?=\n## |\Z)", body28, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body28
    # ── §29 CO-153（K9 覆盖缺口关闭 · 闸硬化） ───────────────────────────────
    MARK29 = "## 29. CO-153"
    sec29 = [MARK29 + "（**L2 自裁 · 闸硬化**：K9 `declared`/`conservative_ge` 判据 + 域生产者归一）", "",
             "**执行前实测缺口**（证据）：co124 K9 对 `kind == \"declared\"`（含无 kind 的默认值）**无任何判据** ⇒ 9 个派生值中 "
             "**2 个零校验通过**（「声明即通过」）：`derived_value_declared_unpinned:DV-ENGINE-INT_PAIR_PITCH` 与 "
             "`...:DV-CO146-ZDIFF`（后者 `evidence_ref.sha16` 自 CO-146 起再未刷新，CO-152 改阻抗表记录后实测陈旧）。", "",
             "**本件处置**：", "",
             "1. **K9 新增 `declared` 判据**：`evidence_ref` 须可解析 + `sha16` 与现行一致 + `basis` 非空"
             "（与 `process_floor` 同口径）⇒ 陈旧/缺失证据必然被抓。",
             "2. **K9 新增 `conservative_ge` 判据**：闭式重算 `faithful = span + 2·w_outer` 并证 `value ≥ faithful`、"
             "`cited` 一致 ⇒ 「保守实现」由断言升级为**证明**。",
             "3. **台账域生产者归一**：`DV-ENGINE-INT_PAIR_PITCH.kind = conservative_ge`（生产者亦已同步："
             "`p3_v57_co134_req_impl_separation.py` 直出该 kind）；`DV-CO146-PDN-DROP.kind = drop_domain` 改由 "
             "`p3_v57_co153_k9_domain_coverage.py` **具名产出**（此前系一次性写入、规范序内无生产者 ⇒ 任何台账重写即"
             "静默丢失、`T11_drop_domain_teeth` 失效）。",
             "4. **`p3_v57_co146_ledger_add.py` 收窄**为**仅** upsert `DV-CO146-ZDIFF`（原三 DV 一并重写会 clobber "
             "CO-149/CO-150/CO-153 的归属），并**并入规范复现序** ⇒ 阻抗表记录变更即自动刷新证据 pin"
             "（此为其 pin 陈旧的根因）。",
             "5. **牙齿**：`T12/T12b`（声明未锚定必抓 / 无假阳）、`T13/T13b`（保守未证明必抓 / 无假阳）；"
             "`T11_drop_domain_teeth` 回归恢复为 True。co124 牙齿总数 17，全 True。", "",
             "**闭合复核**：co124 = **PASS / findings 0 / 牙齿 17/17 True**（执行前 = FAIL_UNREGISTERED_INPUT_DEFECT / findings 2）。"
             "**登记簿**：+3 TOOL_DEFECT（`co124_k9_declared_kind_has_no_evidence_check` / "
             "`co146_ledger_add_schema_drift_and_out_of_order` / `k9_drop_domain_has_no_producer_in_reproduction_order`）"
             "**全部 CLOSED** ⇒ 30 项 / OPEN 0。", "",
             "> **R-CO153-1**：K9 各域（`domain_cap` / `identity` / `process_floor` / `declared` / `conservative_ge` / "
             "`drop_domain` / `thermal_option_domain`）均须由规范复现序内**具名生产者**产出；**禁止一次性写入台账域**"
             "（否则任何台账重写会静默削掉机判覆盖面）。", "",
             "> **R-CO153-2**（取代 R-CO152-4 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → "
             "**co146_ledger_add** → **co153_k9_domain_coverage** → co148_u6_datasheet_inputs → co148_thermal_ruling → "
             "co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co152_findings_disposition → "
             "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
             "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co146_boundary_append`，**循环 2–3 次至 sha 稳定**"
             "（实测 3 轮收敛：co124/co120/co135/co136/register/ledger 自第 2 轮起稳定，co77/boundary 第 3 轮稳定）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows29 = [("工具 `p3_v57_co153_k9_domain_coverage.py`", K2 / "tools/p3_v57_co153_k9_domain_coverage.py"),
               ("工具 `p3_v57_co146_ledger_add.py`（收窄）", K2 / "tools/p3_v57_co146_ledger_add.py"),
               ("工具 `p3_v57_co134_req_impl_separation.py`（生产者直出 kind）",
                K2 / "tools/p3_v57_co134_req_impl_separation.py"),
               ("co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`（CO-124.6）",
                STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
               ("co120 闸 `m13_v57_co120_provenance_pin_gate.json`", STEP2 / "m13_v57_co120_provenance_pin_gate.json"),
               ("台账 `derived_value_ledger_v1.json`（9 DV 全域覆盖）", L2 / "derived_value_ledger_v1.json"),
               ("登记簿 `input_defect_register_v1.json`（30 项 / OPEN 0）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows29:
        if pth.exists():
            sec29.append(f"| {label} | `{s16(pth)}` |")
    sec29 += ["", "> **复评债**：本件（CO-153）自身须由**另一会话**复评（禁自评）：重点 = 新判据是否可被规避、"
                  "`conservative_ge` 的 faithful 口径是否等同于 DV-INTPAIR-EDGE 的忠实下界、"
                  "域生产者归一后是否仍存在「一次性写入」残留。", ""]
    body29 = "\n".join(sec29)
    if MARK29 in txt:
        txt = re.sub(re.escape(MARK29) + r"[\s\S]*?(?=\n## |\Z)", body29, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body29
    # ── §30 CO-154/CO-155（非执行者复评 + findings 处置） ────────────────────
    MARK30 = "## 30. CO-154 / CO-155"
    _c154 = STEP2 / "m13_v57_co154_rev19_co153_co152_review.json"
    r154 = json.loads(_c154.read_text()) if _c154.exists() else {}
    rcounts = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec30 = [MARK30 + "（**CO-154 非执行者对抗复评** · 另一会话 + **CO-155 findings 处置** · executor · L2 自裁）", "",
             f"- CO-154 verdict = **{r154.get('verdict')}**｜findings = {r154.get('n_findings')}"
             "（**as-found**：重跑可得不同 findings/sha，勿作复现目标）",
             "- 独立确认（非空过）：co124 = PASS / 0 findings / 牙齿 17-17；co120 = PASS（snaps 8 / undeclared 0 / basis_not_ok 0）；"
             "CO-152 R2 勘误已落实（0.2577，旧值 0.3294 留存）且**不改变结论**；两类新判据正控确抓（declared 陈旧 sha / "
             "conservative value<faithful）。", "",
             "- CO-154 findings 与 CO-155 处置：", "",
             "| # | sev | 摘要 | 状态 |", "|---|---|---|---|",
             "| F-1 | medium | CO-152 删 co150 记录 `register.open_total` 未同步消费者 ⇒ 规范序内崩溃 | **CLOSED**（CO-155 修） |",
             "| F-2 | medium | 下游**计数/版本**快照未随 CO-152 清理（co147 `open_total` 使提交 pin 不可复现） | 工件侧已修；**闸覆盖侧 OPEN** |",
             "| F-3 | low | 修订号标签失真（§29 pin 表 co124=CO-124.6 vs 实件 .5；CO-147.2 vs .1） | OPEN |",
             "| F-4 | medium | R-CO153-1 不成立：三域生产者 co134 不在规范序、且整表重写台账 | OPEN |",
             "| F-5 | medium | K9 无「域覆盖」牙齿：未列 kind / `domain_cap` 缺 `domains` 静默通过 | OPEN |",
             "| F-6 | medium | CO-153 `declared` 判据只做证据 pin、与值无语义关联 ⇒ 钉无关文件即规避 | OPEN |",
             "| F-7 | low | `conservative_ge` faithful 由自声明 inputs 重算、未与 DV-INTPAIR-EDGE 交叉 | OPEN |", "",
             "> **R-CO154-1**：复评件（非执行者、另一会话）为**独立件**且为 **as-found** 快照，不作复现目标（同 CO-151 例）。",
             "> **R-CO155-1**（取代 R-CO153-2 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co152_findings_disposition → **co155_co154_findings_disposition** → "
             "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
             "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co146_boundary_append`，**循环至 sha 稳定**。",
             "> **R-CO155-2**：记录**不得**内嵌其下游工件的 sha **或下游计数/版本快照**（现行 sha/计数一律由本 boundary pin 表承载）；"
             "新增此类键须在 co120 `SNAPSHOT_DECLARED` 声明。⚠ 闸覆盖面（`*_sha16` / `register.*` / `open_total` / `items_total` / "
             "嵌套 `sha16`）**尚未**机判化 ⇒ 列 OPEN 项 F-2b，实施前以人工复核承接（**不得**据此宣称已机判覆盖）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows30 = [("复评件 `m13_v57_co154_rev19_co153_co152_review.json`", _c154),
               ("工具 `p3_v57_co154_rev19_co153_co152_review.py`", K2 / "tools/p3_v57_co154_rev19_co153_co152_review.py"),
               ("工具 `p3_v57_co155_co154_findings_disposition.py`", K2 / "tools/p3_v57_co155_co154_findings_disposition.py"),
               ("工具 `p3_v57_co150_k9_domain_gate.py`（修崩溃）", K2 / "tools/p3_v57_co150_k9_domain_gate.py"),
               ("工具 `p3_v57_co147_l2_ruling.py`（去计数快照）", K2 / "tools/p3_v57_co147_l2_ruling.py"),
               ("工具 `p3_v57_co148_thermal_ruling.py`（去计数快照）", K2 / "tools/p3_v57_co148_thermal_ruling.py"),
               ("co147 裁定 `m13_v57_co147_l2_ruling.json`（修订号实件 CO-147.1）", STEP2 / "m13_v57_co147_l2_ruling.json"),
               ("co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`（修订号实件 CO-124.5）", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{rcounts['total']} 项 / OPEN {rcounts['OPEN']}）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows30:
        if pth.exists():
            sec30.append(f"| {label} | `{s16(pth)}` |")
    sec30.append("")
    body30 = "\n".join(sec30)
    if MARK30 in txt:
        txt = re.sub(re.escape(MARK30) + r"[\s\S]*?(?=\n## |\Z)", body30, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body30
    # ── §31 CO-156（CO-154 剩余 OPEN 处置 · 闸硬化） ─────────────────────────
    MARK31 = "## 31. CO-156"
    _rc31 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec31 = [MARK31 + "（**L2 自裁 · 闸硬化**：CO-154 剩余 OPEN 6 项全部处置）", "",
             "| # | 处置 | 判据/牙齿 | 状态 |", "|---|---|---|---|",
             "| F-5 | K9 **域覆盖**：`kind` ∈ 七域白名单 + `domain_cap` 必带非空 `domains` | "
             "`T14_unknown_kind_teeth` / `T14b_empty_domain_cap_teeth` / `T14c_..._no_false_positive` | **CLOSED** |",
             "| F-6 | `declared` 升级为**值-证据绑定**：须带 `evidence_ref.key_path`，证据件在该路径须**递归包含** DV `computed` | "
             "`T15_declared_binding_teeth` / `T15b_..._no_false_positive`；生产者 `co146_impedance_table`(`dv_computed_zdiff`) + `co146_ledger_add` | **CLOSED** |",
             "| F-7 | `conservative_ge` 的 faithful **引用权威 DV**（`span_src`/`w_outer_src` + 数值交叉 DV-PAIR-CROSS / DV-INTPAIR-EDGE） | "
             "`T16_faithful_provenance_teeth` / `T16b_..._no_false_positive`；生产者 `co153` | **CLOSED** |",
             "| F-4 | `co134` 改**只 upsert 自有条目**（stub 复跑：9 DV 全保留）；`co153` 扩为**七域 kind 的规范序内具名生产者**（`KIND_EXPECT`） | R-CO153-1 成立 | **CLOSED** |",
             "| F-2 | co120 升 **CO-120.3**：下游快照键 = `*_sha16_after` ∪ `register.*`/`ledger.*` 下的 `sha16*`/`items_total`/`open_total`/`n_items`，未声明即 FAIL | "
             "新增 register-snapshot 负控/正控牙齿 | **CLOSED** |",
             "| F-3 | co124 实件 revision **CO-124.6**（与 §29 pin 表标签一致，§26 `CO-124.5` 为历史陈述）；co147 以实件 **CO-147.1** 记 | — | **CLOSED** |", "",
             f"- 复核：co124 = **PASS / findings 0 / 牙齿 24/24**；co120 = **PASS**（snaps 8 / undeclared 0 / teeth 7-7）；登记簿 "
             f"**{_rc31['total']} 项 / OPEN {_rc31['OPEN']}**。", "",
             "> **R-CO156-1**（取代 R-CO155-1 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co152_findings_disposition → co155_co154_findings_disposition → "
             "**co156_co154_open_disposition** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → "
             "co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → "
             "co146_boundary_append`，**循环至 sha 稳定**。",
             "> **R-CO156-2**（取代 R-CO155-2 的闸覆盖缺口项）：下游快照键（sha **与**计数/版本）由 co120 CO-120.3 **机判**；"
             "记录不得内嵌下游 sha/计数/版本快照，新增须在 `SNAPSHOT_DECLARED` 声明。",
             "> **R-CO156-3**：单板派生物（computed/domains/几何）的生产者**只准 upsert 自有条目**；禁止对台账/记录做整表重写"
             "（先例：co134 整表重写会静默删除他 CO 归属 DV）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows31 = [("工具 `p3_v57_co156_co154_open_disposition.py`", K2 / "tools/p3_v57_co156_co154_open_disposition.py"),
               ("工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.6 / 牙齿 24）", K2 / "tools/p3_v57_co124_input_selfcheck_gate.py"),
               ("工具 `p3_v57_co120_provenance_pin_gate.py`（CO-120.3）", K2 / "tools/p3_v57_co120_provenance_pin_gate.py"),
               ("工具 `p3_v57_co134_req_impl_separation.py`（只 upsert）", K2 / "tools/p3_v57_co134_req_impl_separation.py"),
               ("工具 `p3_v57_co153_k9_domain_coverage.py`（七域 kind 生产者）", K2 / "tools/p3_v57_co153_k9_domain_coverage.py"),
               ("工具 `p3_v57_co146_impedance_table.py`（+dv_computed_zdiff）", K2 / "tools/p3_v57_co146_impedance_table.py"),
               ("工具 `p3_v57_co146_ledger_add.py`（key_path 绑定）", K2 / "tools/p3_v57_co146_ledger_add.py"),
               ("co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`（CO-124.6）", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
               ("co120 闸 `m13_v57_co120_provenance_pin_gate.json`（CO-120.3）", STEP2 / "m13_v57_co120_provenance_pin_gate.json"),
               ("co147 裁定 `m13_v57_co147_l2_ruling.json`（CO-147.1 实件）", STEP2 / "m13_v57_co147_l2_ruling.json"),
               ("台账 `derived_value_ledger_v1.json`（9 DV 全域覆盖）", L2 / "derived_value_ledger_v1.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc31['total']} 项 / OPEN {_rc31['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows31:
        if pth.exists():
            sec31.append(f"| {label} | `{s16(pth)}` |")
    sec31.append("")
    body31 = "\n".join(sec31)
    if MARK31 in txt:
        txt = re.sub(re.escape(MARK31) + r"[\s\S]*?(?=\n## |\Z)", body31, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body31
    # ── §32 CO-157（查漏型闸硬化 3） ────────────────────────────────────────
    MARK32 = "## 32. CO-157"
    _rc32 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec32 = [MARK32 + "（**L2 自裁 · 查漏型闸硬化（第 3 轮）**：4 项实测缺口 H-1..H-4 全处置）", "",
             "| # | 实测缺口（修前） | 处置 | 状态 |", "|---|---|---|---|",
             "| H-1 | K9 `process_floor`（`derived_value_evidence_bad`）与 `identity_unparsable` **无负控牙齿**（判据存在但无回归保护） | "
             "T17/T17b + **元牙齿** T18（逐 finder id 注入，断言全覆盖）/T18b/T18c ⇒ 牙齿 24→**29** | **CLOSED** |",
             "| H-2 | 判据声明失实：CO-153 称 `declared`「与 process_floor 同口径」，实际后者不验 basis/key_path | "
             "co124 注释就地订正（declared **严于** process_floor）+ 本 §32 记录 | **CLOSED** |",
             "| H-3 | co120 `board_superseded` 弱判：任意自由文本（`board=\"superseded\"`）即可成立豁免 | "
             "收严为**板 sha16 格式**（`[0-9a-f]{16}`）且 ≠ 交付板 + 负控/正控牙齿；co120 升 **CO-120.4** | **CLOSED** |",
             "| H-4 | R-CO156-3（禁整表重写台账）**无机判**（仅声明） | co136 增源码守卫 `H4_ledger_upsert_only`（写台账须先读）+ 正负控；co136 升 **CO-136.1** | **CLOSED** |", "",
             f"- 复核：co124 = **PASS / findings 0 / 牙齿 29/29**；co120 = **PASS**（basis_not_ok 0 / teeth 9-9）；co136 = **PASS**；登记簿 "
             f"**{_rc32['total']} 项 / OPEN {_rc32['OPEN']}**。", "",
             "> **R-CO157-1**（取代 R-CO156-1 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co152_findings_disposition → co155_co154_findings_disposition → "
             "co156_co154_open_disposition → **co157_gate_hardening_3** → co124_input_selfcheck_gate → co150_k9_domain_gate → "
             "co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → "
             "co136_gate_hygiene → co146_boundary_append`，**循环至 sha 稳定**。",
             "> **R-CO157-2**：新增 K9 判据须同时登记进 `K9_FINDER_IDS` 并提供负控（由元牙齿 T18 机判）；"
             "`board_superseded` 豁免须给可比对的板 sha16。",
             "> **R-CO157-3**（R-CO156-3 的机判面）：台账写者必须先读台账 —— 由 co136 `H4_ledger_upsert_only` **源码级**把关；"
             "⚠ 该守卫为静态启发式（**部分机判**），不替代语义审查；整表重写须在 boundary 显式豁免。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows32 = [("工具 `p3_v57_co157_gate_hardening_3.py`", K2 / "tools/p3_v57_co157_gate_hardening_3.py"),
               ("工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.7 / 牙齿 29 / T18 元牙齿）", K2 / "tools/p3_v57_co124_input_selfcheck_gate.py"),
               ("工具 `p3_v57_co120_provenance_pin_gate.py`（CO-120.4）", K2 / "tools/p3_v57_co120_provenance_pin_gate.py"),
               ("工具 `p3_v57_co136_gate_hygiene.py`（CO-136.1 / H4 源码守卫）", K2 / "tools/p3_v57_co136_gate_hygiene.py"),
               ("co124 输入自检 `m13_v57_co124_input_selfcheck_gate.json`（CO-124.7）", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
               ("co120 闸 `m13_v57_co120_provenance_pin_gate.json`（CO-120.4）", STEP2 / "m13_v57_co120_provenance_pin_gate.json"),
               ("co136 闸卫生 `m13_v57_co136_gate_hygiene.json`（CO-136.1）", STEP2 / "m13_v57_co136_gate_hygiene.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc32['total']} 项 / OPEN {_rc32['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows32:
        if pth.exists():
            sec32.append(f"| {label} | `{s16(pth)}` |")
    sec32.append("")
    body32 = "\n".join(sec32)
    if MARK32 in txt:
        txt = re.sub(re.escape(MARK32) + r"[\s\S]*?(?=\n## |\Z)", body32, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body32
    # ── §33 CO-158（L5 打样包自足性） ───────────────────────────────────────
    MARK33 = "## 33. CO-158"
    _rc33 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _pkg = L5 / "jlc_package" / "MANIFEST.json"
    _pk = json.loads(_pkg.read_text()) if _pkg.exists() else {}
    sec33 = [MARK33 + "（**L2 自裁 · 交付物完整性**：L5 打样包自足）", "",
             f"- 实测缺口（修前）：`ORDER_NOTES.md` §2 声明「随单提交 … L2 裁定件」，§3/§6 另引 DFM 记录与 U6 热裁定，"
             f"但 `jlc_package/` 内**均无该等文件**（in-package=False）⇒ 下单时 silent omission；包内阻抗表副本亦为 CO-156 前陈旧件。",
             f"- 处置（**CO146-PKG.2**）：新增 `06_rulings/`（3 份 L2 裁定件 + DFM 记录）+ ORDER_NOTES 引用改**包内路径** + "
             f"牙齿 `t05_declared_rulings_packaged` / `t06_order_notes_refs_resolve_in_package`；打包工具**并入规范序**。",
             f"- 复核：**全 gerber/drill 逐字节未变**（纯增量）；MANIFEST n_files = **{_pk.get('n_files')}**，"
             f"teeth = {json.dumps(_pk.get('teeth', {}), ensure_ascii=False)}；登记簿 **{_rc33['total']} 项 / OPEN {_rc33['OPEN']}**。", "",
             "**同 CO 另处置 2 项闸卫生**（实测缺陷）：", "",
             "- **J-2**：co77 的 citation 候选目录**不含 L5 打样包** ⇒ §33 一类引用必被误判 CITATION_MISMATCH（实测 mismatches = "
             "`['L5/jlc_package/MANIFEST.json','L5/jlc_package/ORDER_NOTES.md']`，并连带把 co135/co136 判 FAIL）⇒ **CO-77.6** 抽出 "
             "`citation_candidates()` 补入 L5 包 + 正控牙齿 `l5_packet_citation_resolvable`；复核 co77 = PASS（mismatches []）。",
             "- **J-3**：**闸退出码不反映 verdict** —— co77（恒 0）/co124/co135/co136 无条件 `return 0` ⇒ shell/CI 复现序无法据 rc 发现 FAIL"
             "（实测 co136 FAIL 时 rc 仍 0）⇒ 四件改为 `PASS ⇒ 0 否则 1`（co135：`PASS`/`PASS_WITH_FINDINGS` ⇒ 0；对照 co120/co150/l4/l5 本已正确）。", "",
             "> **R-CO158-1**（取代 R-CO157-1 的复现序）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → **co146_jlc_fab_package** → co152_findings_disposition → "
             "co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → **co158_l5_packet_selfcontained** → "
             "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
             "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co146_boundary_append`，**循环至 sha 稳定**。",
             "> **R-CO158-2**：交付物（L5 打样包）内**声明随单提交的附件必须落包内**，且记录内引用须用**包内路径**；"
             "新增此类声明由 t05/t06 把关（声明与包内容不一致即 FAIL）。",
             "> **R-CO158-3**：凡规范序内的闸，**退出码必须反映 verdict**（FAIL/不一致 ⇒ 非 0），使复现序可 fail-fast；"
             "被 boundary 引用的交付物目录须在 co77 citation 候选目录内。", "",
             "> **附记（记录卫生·非工件缺陷）**：历次 handoff 称「工作树仅 `_shared` 模式位 dirty」**归因有误** —— "
             "经查 k2 侧 `_shared` 的 dirty 实为 `k2/_shared/knowledge/kb.sqlite3-{wal,shm}`（未跟踪 SQLite 运行时件）；"
             "而「模式位」（`eda_core/escape_closure_analysis.py` 100755→100644）在**容器侧 `_shared` 的独立 checkout** 内。"
             "二者均属共享子模块边界、非 k2 工件；本件不修改（跨仓/运行时件），仅订正归因以免后续会话误追。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows33 = [("工具 `p3_v57_co158_l5_packet_selfcontained.py`", K2 / "tools/p3_v57_co158_l5_packet_selfcontained.py"),
               ("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.2 / 06_rulings + t05/t06）", K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("工具 `p3_v57_co77_closure_declaration_sweep.py`（CO-77.6 / L5 citation + rc）", K2 / "tools/p3_v57_co77_closure_declaration_sweep.py"),
               ("工具 `p3_v57_co124_input_selfcheck_gate.py`（rc 反映 verdict）", K2 / "tools/p3_v57_co124_input_selfcheck_gate.py"),
               ("工具 `p3_v57_co135_review_hygiene.py`（rc）", K2 / "tools/p3_v57_co135_review_hygiene.py"),
               ("工具 `p3_v57_co136_gate_hygiene.py`（rc）", K2 / "tools/p3_v57_co136_gate_hygiene.py"),
               ("打样包 MANIFEST `L5/jlc_package/MANIFEST.json`", _pkg),
               ("下单备注 `L5/jlc_package/ORDER_NOTES.md`", L5 / "jlc_package" / "ORDER_NOTES.md"),
               ("打样包记录 `m13_v57_co146_jlc_fab_package.json`", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc33['total']} 项 / OPEN {_rc33['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows33:
        if pth.exists():
            sec33.append(f"| {label} | `{s16(pth)}` |")
    sec33.append("")
    body33 = "\n".join(sec33)
    if MARK33 in txt:
        txt = re.sub(re.escape(MARK33) + r"[\s\S]*?(?=\n## |\Z)", body33, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body33
    txt = txt.replace("W3 Boundary **v2.00**", "W3 Boundary **v2.01**")
    txt = txt.replace("W3 Boundary **v1.99**", "W3 Boundary **v2.00**")
    txt = txt.replace("W3 Boundary **v1.98**", "W3 Boundary **v1.99**")
    txt = txt.replace("W3 Boundary **v1.97**", "W3 Boundary **v1.98**")
    txt = txt.replace("W3 Boundary **v2.01**", "W3 Boundary **v2.02**")
    txt = txt.replace("W3 Boundary **v2.02**", "W3 Boundary **v2.03**")
    txt = txt.replace("W3 Boundary **v2.03**", "W3 Boundary **v2.04**")
    txt = txt.replace("W3 Boundary **v2.04**", "W3 Boundary **v2.05**")
    # ── §34 CO-159 / CO-160（非执行者对抗复评 + 处置） ─────────────────────
    MARK34 = "## 34. CO-159 / CO-160"
    _rc34 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec34 = [MARK34 + "（**非执行者对抗复评 CO-156/157/158 + L2 自裁处置**）", "",
             f"- 复评（**CO-159**，as-found 钉在 k2 `c4e951c`；`git show` 重放受评基线 ⇒ 不随后续修复漂移）：**12 findings**（F-1..F-12）——"
             f"① K9 `declared` 空 `computed` 绕过值-证据绑定；② `conservative_ge` 权威 DV 缺失即跳过交叉校验；③ T18 元牙齿只比电池触发集、"
             f"源码条件分支 finder 可绕过；④ R-CO156-3「禁整表重写」无机判（H4 只拦未读即写）；⑤ co120 快照键判据依赖嵌套容器；"
             f"⑥ `board_superseded` 仅格式判（任意 16-hex 成立）；⑦ **co146_jlc_dfm_gate verdict=FAIL 而 rc=0**（违 R-CO158-3）；"
             f"⑧ 打样包 `06_rulings/` 无来源一致性牙齿；⑨ ORDER_NOTES 目录级声明未覆盖；⑩ co77/co135 候选表已现分歧面无一致性牙齿；"
             f"⑪ §6 回归块 co78/co81/co84/co95/co98/co106 rc 恒 0；⑫ co135 内嵌 CO-134 时点链 pin + 硬编码 boundary 文件名。",
             f"- 处置（**CO-160**，逐项）：co124 牙齿 29→**33**（T15c/T16c/T18d/T18e，升 **CO-124.8**）；co120 升 **CO-120.5**"
             f"（快照键名面判据 + `SUPERSEDED_BOARDS` 白名单 + 伪造 sha 负控）；co146_jlc_dfm_gate **rc 反映 verdict**（FAIL ⇒ rc=1）；"
             f"co146_jlc_fab_package 升 **CO146-PKG.3**（`t07` 副本来源一致性 + `t08` 目录级声明）；co135 升 **CO-135.3**"
             f"（co77 候选表交叉一致性 + 链 pin 由现行记录派生 + boundary 取最新版）；六件回归闸 rc 反映 verdict"
             f"（CO-78.2/81.2/84.2/95.2/98.2/106.3，co98 按 `baseline_ok and teeth_ok`）。",
             f"- 复核：co124 = **PASS / findings 0 / 牙齿 33/33**；co120 = PASS（teeth 12-12）；co77 = PASS（mismatches []）；"
             f"co135 = PASS_WITH_FINDINGS（候选表一致）；co136 = PASS；DFM 闸 rc=1（FAIL 属预期）；打样包 teeth **9/9**；"
             f"登记簿 **{_rc34['total']} 项 / OPEN {_rc34['OPEN']}**。", "",
             "> **R-CO159-1**：K9 `declared` 派生值须带**非空** `computed`（值-证据绑定不得空过）；`conservative_ge` 的权威 DV"
             "（`DV-INTPAIR-EDGE` / `DV-PAIR-CROSS`）缺失即 FAIL（不得静默降级）；K9 判据集另由 `T18d` 以**源码**面机判"
             "（新增 finder 未登记 `K9_FINDER_IDS` 即 FAIL）。",
             "> **R-CO159-2**：R-CO156-3 的**机判面** = co136 `H4`（写台账须先读台账）+ CO-156 的 co134 stub 复跑证据；"
             "「整表重写」的**语义面**无自动判据（已声明，由复评/登记承接）——规则文本不得表述为已机判。",
             "> **R-CO159-3**：下游快照键判据取**键名面**（`*_sha16_after` ∪ `register|ledger[_…]_sha16|items_total|open_total|n_items`），"
             "与嵌套位置无关；`board_superseded` 的板 sha16 须在 `SUPERSEDED_BOARDS` 白名单（未登记 16-hex 不成立）。",
             "> **R-CO159-4**：复现序内**所有**闸（含 `co146_jlc_dfm_gate` 与 §6 回归块 co78/co81/co84/co95/co98/co106）退出码须反映 verdict/基线；"
             "`co98` 按 `baseline_ok and teeth_ok` 判定（三态报告不因 OPEN 状态返回非 0）。",
             "> **R-CO159-5**（复现序，取代 R-CO158-1）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
             "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → **co159_rev19_co156_co157_co158_review** → "
             "**co160_co159_findings_disposition** → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → "
             "co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → "
             "co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → "
             "co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**。",
             "", "| 工件 | sha16 |", "|---|---|"]
    _rows34 = [("工具 `p3_v57_co159_rev19_co156_co157_co158_review.py`（as-found 复评）",
                K2 / "tools/p3_v57_co159_rev19_co156_co157_co158_review.py"),
               ("记录 `m13_v57_co159_rev19_co156_co157_co158_review.json`",
                STEP2 / "m13_v57_co159_rev19_co156_co157_co158_review.json"),
               ("工具 `p3_v57_co160_co159_findings_disposition.py`",
                K2 / "tools/p3_v57_co160_co159_findings_disposition.py"),
               ("工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.8 / T15c+T16c+T18d+T18e）",
                K2 / "tools/p3_v57_co124_input_selfcheck_gate.py"),
               ("工具 `p3_v57_co120_provenance_pin_gate.py`（CO-120.5 / 键名面 + SUPERSEDED_BOARDS）",
                K2 / "tools/p3_v57_co120_provenance_pin_gate.py"),
               ("工具 `p3_v57_co135_review_hygiene.py`（CO-135.3 / 候选表交叉一致性 + 链 pin 派生）",
                K2 / "tools/p3_v57_co135_review_hygiene.py"),
               ("工具 `p3_v57_co146_jlc_dfm_gate.py`（rc 反映 verdict）", K2 / "tools/p3_v57_co146_jlc_dfm_gate.py"),
               ("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.3 / t07+t08）",
                K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc34['total']} 项 / OPEN {_rc34['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows34:
        if pth.exists():
            sec34.append(f"| {label} | `{s16(pth)}` |")
    sec34.append("")
    body34 = "\n".join(sec34)
    if MARK34 in txt:
        txt = re.sub(re.escape(MARK34) + r"[\s\S]*?(?=\n## |\Z)", body34, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body34
    txt = txt.replace("W3 Boundary **v2.05**", "W3 Boundary **v2.06**")
    # ── §35 CO-161（查漏型 L2 闸硬化 4） ───────────────────────────────────
    MARK35 = "## 35. CO-161"
    _rc35 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec35 = [MARK35 + "（**L2 自裁 · 查漏型闸硬化 4**：K9 覆盖完备性 + identity fail-closed）", "",
             f"- 实测缺口（修前，均机判）：**G-1** K9 无「必需 DV 清单」牙齿 —— 台账删 `DV-CO146-THERMAL` / `DV-CO146-PDN-DROP` / "
             f"`DV-ENGINE-INT_PAIR_PITCH` 任一项时 co124 K9 = 0 findings、co150 `t01` 仍 True（T10/T11 负控用合成注入，不依赖真 DV 存在）"
             f"⇒ 热/压降/保守实现三域覆盖可被一次 upsert 误删**无声**抹掉；**G-2** `identity` 类 fail-open —— `form` 未识别（如 `q = a + b`）"
             f"或缺失时无判据命中、静默通过。",
             f"- 处置（**CO-161**）：① co124 增 `REQUIRED_DV_IDS`（9 项）与 `derived_value_inventory_missing` 判据 + 负控 T19/T19b；"
             f"② `co153.KIND_EXPECT` **提为模块级**（必需 DV 清单的单一真值）；③ co150 增 `t03`（两域 kind 断言）/`t04`"
             f"（co124 `required_dv_ids` == co153 `KIND_EXPECT` 键集）/`t05`（漂移可辨）；④ co124 `identity` 改 **fail-closed**"
             f"（缺 `form` ⇒ unparsable；未识别 ⇒ 新判据 `derived_value_identity_unhandled_form`，并入 `K9_FINDER_IDS`）+ 负控 T20/T20b。",
             f"- 复核：co124 升 **CO-124.9**（牙齿 33→**37/37**，PASS/0 findings）；co150 升 **CO-150.2**（5 牙齿 True，rc=0）；"
             f"co153 升 **CO-153.2**；登记簿 **{_rc35['total']} 项 / OPEN {_rc35['OPEN']}**。",
             f"- 修订号对账：§30 的 CO-150 条与 §34 所记 `CO-124.8` 为各自时点陈述；co124 **现行 = CO-124.9**（本 §35）。", "",
             "> **R-CO161-1**：K9 **必需 DV 清单**完备性 —— 台账须含全部 9 项必需 DV（`co153.KIND_EXPECT` 键集为**单一真值**）；"
             "缺任一项即 `derived_value_inventory_missing` FAIL；co124 的 `required_dv_ids` 须与 co153 `KIND_EXPECT` 逐项一致（co150 `t04`）。",
             "> **R-CO161-2**：`identity` 类派生式 **fail-closed** —— `form` 缺失 ⇒ `derived_value_identity_unparsable`；"
             "`form` 未被重算分支识别 ⇒ `derived_value_identity_unhandled_form`（不得静默通过）；新增 identity 形式须同时提供机判重算分支。",
             "> **R-CO161-3**（复现序，取代 R-CO159-5）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
             "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → "
             "co160_co159_findings_disposition → **co161_gap_hardening_4** → co124_input_selfcheck_gate → co150_k9_domain_gate → "
             "co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → "
             "co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → "
             "co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**。",
             "", "| 工件 | sha16 |", "|---|---|"]
    _rows35 = [("工具 `p3_v57_co161_gap_hardening_4.py`", K2 / "tools/p3_v57_co161_gap_hardening_4.py"),
               ("工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.9 / REQUIRED_DV_IDS + identity fail-closed）",
                K2 / "tools/p3_v57_co124_input_selfcheck_gate.py"),
               ("工具 `p3_v57_co153_k9_domain_coverage.py`（CO-153.2 / KIND_EXPECT 模块级）",
                K2 / "tools/p3_v57_co153_k9_domain_coverage.py"),
               ("工具 `p3_v57_co150_k9_domain_gate.py`（CO-150.2 / t03+t04+t05）", K2 / "tools/p3_v57_co150_k9_domain_gate.py"),
               ("记录 `m13_v57_co124_input_selfcheck_gate.json`", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
               ("记录 `m13_v57_co150_k9_domain_gate.json`", STEP2 / "m13_v57_co150_k9_domain_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc35['total']} 项 / OPEN {_rc35['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows35:
        if pth.exists():
            sec35.append(f"| {label} | `{s16(pth)}` |")
    sec35.append("")
    body35 = "\n".join(sec35)
    if MARK35 in txt:
        txt = re.sub(re.escape(MARK35) + r"[\s\S]*?(?=\n## |\Z)", body35, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body35
    txt = txt.replace("W3 Boundary **v2.06**", "W3 Boundary **v2.07**")
    # ── §36 CO-162（查漏型 L2 闸硬化 5） ───────────────────────────────────
    MARK36 = "## 36. CO-162"
    _rc36 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec36 = [MARK36 + "（**L2 自裁 · 查漏型闸硬化 5**：verdict 基线约束 + 已声明承载区豁免）", "",
             f"- 实测缺口（修前，均机判）：**G-1** co106 的 verdict 阶梯 `PASS if hard else (... else PASS)` 在 `hard=False ∧ cls_count 空` 时"
             f"仍判 **PASS** —— 记录自身即 `A_frame_inset_consistency.ok = False`（2 处内缩偏差）而 verdict=PASS；且把 `BASE['spec_current']` "
             f"改成伪值（基线 pin 漂移）后仍 verdict=PASS / rc=0（`pin_mismatch` 只记录、不参与判定）⇒ 「基线可复现」与「检查通过」同时失效。"
             f"**G-2** 桥接承载区（`P3V3_BCU_BRIDGE_IN4` / `P3V3_AUX_BCU_BRIDGE_IN4`，T2-ECN-1/2 PM 裁决的局部承载 pour）被算作内缩偏差却"
             f"只记录不判定 ⇒ 偏差被静默容忍（既无登记也无 pin，违 CO-139 口径）。",
             f"- 处置（**CO-162**）：① 抽纯函数 `verdict_of(checks_ok, teeth_ok, pin_mismatch, cls_count)` —— `pin_mismatch` 非空 ⇒ "
             f"`BASELINE_MISMATCH`；`teeth_ok=False` ⇒ `FAIL(teeth)`；任一 check 失败 ⇒ `FAIL_DECLARED_COPPER_MISSING` / "
             f"`INDETERMINATE_REGION_SCOPED` / `FAIL_CHECKS`（**不再回落 PASS**）；增牙齿 `baseline_pin_binding` / `fail_open_closed` / "
             f"`verdict_positive_control`；② 增 `DECLARED_NON_FULL_PLANE` 注册表 + **冻结 SPEC pin 锚定**（SPEC pin 不成立则豁免自动失效）"
             f"+ 牙齿 `carrier_exemption_declared_only`。co106 升 **CO-106.4**。",
             f"- 复核：真基线 **verdict=PASS / rc=0**（A dev=0、豁免 4 条：2 内岛 + 2 桥接承载、牙齿 8/8）；注入伪 spec pin ⇒ "
             f"**verdict=BASELINE_MISMATCH / rc=1**。登记簿 **{_rc36['total']} 项 / OPEN {_rc36['OPEN']}**。", "",
             "> **R-CO162-1**：凡记录内带 `base_pins` 的闸，其 verdict **必须显式消费 pin 漂移**（不等即 `BASELINE_MISMATCH`，非 PASS）；"
             "任一 check 失败不得回落 PASS（由 co106 `verdict_of` 纯函数 + 牙齿 `baseline_pin_binding`/`fail_open_closed` 机判）。",
             "> **R-CO162-2**：非整面承载区（桥接/局部 pour）的板框内缩豁免须**登记进注册表**（`DECLARED_NON_FULL_PLANE`）并**锚定冻结源 pin**，"
             "豁免逐条入记录；不得静默容忍偏差（违者按 G-2 同族处理）。",
             "> **R-CO162-3**（复现序，取代 R-CO161-3）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
             "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → "
             "co160_co159_findings_disposition → co161_gap_hardening_4 → **co162_verdict_binding** → co124_input_selfcheck_gate → "
             "co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → "
             "co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → "
             "co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append`，**循环至 sha 稳定**。",
             "", "| 工件 | sha16 |", "|---|---|"]
    _rows36 = [("工具 `p3_v57_co162_verdict_binding.py`", K2 / "tools/p3_v57_co162_verdict_binding.py"),
               ("工具 `p3_v57_co106_reference_plane_gate.py`（CO-106.4 / verdict_of + DECLARED_NON_FULL_PLANE）",
                K2 / "tools/p3_v57_co106_reference_plane_gate.py"),
               ("记录 `m13_v57_co106_reference_plane_gate.json`", STEP2 / "m13_v57_co106_reference_plane_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc36['total']} 项 / OPEN {_rc36['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows36:
        if pth.exists():
            sec36.append(f"| {label} | `{s16(pth)}` |")
    sec36.append("")
    body36 = "\n".join(sec36)
    if MARK36 in txt:
        txt = re.sub(re.escape(MARK36) + r"[\s\S]*?(?=\n## |\Z)", body36, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body36
    txt = txt.replace("W3 Boundary **v2.07**", "W3 Boundary **v2.08**")
    # ── §37 CO-163（查漏型 L2 闸硬化 6） ───────────────────────────────────
    MARK37 = "## 37. CO-163"
    _rc37 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec37 = [MARK37 + "（**L2 自裁 · 查漏型闸硬化 6**：下单备注↔声明定值表绑定）", "",
             f"- 实测缺口（修前，均机判）：**G-1** `ORDER_NOTES.md` 的「下单参数」表把 `85Ω 差分 ±10%` / `JLC08161H` / `1.6 mm` / "
             f"`外层 1oz 内层 0.5oz` / `沉金 ENIG` 写为**字面量**，与 L2 政策件 `jlc_prototype_parameters_v1.json`（监理指令 #10 定值绑定）"
             f"无绑定、无牙齿 —— 实测把目标阻抗改成 100Ω 后重生成的备注**仍写 85Ω** ⇒ 定值变更会静默产出**客户可见**的陈旧下单备注；"
             f"**G-2** 该定值表的 `supervisor_instruction.sha16` 声明链从未被核验。",
             f"- 处置（**CO-163**）：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.4** —— 载入声明定值表 + 纯谓词 "
             f"`binding_params_in_note`/`binding_tokens`；牙齿 `t09_order_notes_binding_params`（备注须逐项命中叠层码/厚度/外内层铜/目标阻抗/"
             f"容差/表面处理）+ `t09b` 漂移灵敏度 + `t10_declared_binding_source_pinned`（定值表来源 sha16 == 监理指令件 sha16 `35aafe268ff52f89`）"
             f"+ `t10b` 判据可辨；记录落 `declared_binding`（含 `source_instruction`: path/available/declared_sha16）。",
             f"- 复核：打样包 teeth **13/13**（t01..t10b 全 True），订单备注正文与 gerber/drill 逐字节不变；"
             f"注入定值漂移（100Ω/2.0mm）⇒ t09 立即 FAIL。登记簿 **{_rc37['total']} 项 / OPEN {_rc37['OPEN']}**。", "",
             "> **R-CO163-1**：客户可见交付物（L5 打样包/下单备注）内的**工程定值**必须与**声明定值表**逐项一致，由 t09/t09b 机判；"
             "定值表变更而备注未同步即 FAIL（禁止字面量单向复制导致静默陈旧）。",
             "> **R-CO163-2**：声明定值表的**来源 pin**（`supervisor_instruction.sha16`）必须可核验（t10/t10b）；"
             "跨仓来源不可达时 fail-closed 并在记录内显式登记 `available=false`。",
             "> **R-CO163-3**（复现序，取代 R-CO162-3）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
             "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → "
             "co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → **co163_binding_to_order_notes** → "
             "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
             "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → "
             "co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → "
             "co146_boundary_append`，**循环至 sha 稳定**。",
             "", "| 工件 | sha16 |", "|---|---|"]
    _rows37 = [("工具 `p3_v57_co163_binding_to_order_notes.py`", K2 / "tools/p3_v57_co163_binding_to_order_notes.py"),
               ("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.4 / t09+t09b+t10+t10b）",
                K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("打样包 MANIFEST `L5/jlc_package/MANIFEST.json`", L5 / "jlc_package" / "MANIFEST.json"),
               ("下单备注 `L5/jlc_package/ORDER_NOTES.md`", L5 / "jlc_package" / "ORDER_NOTES.md"),
               ("记录 `m13_v57_co146_jlc_fab_package.json`", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc37['total']} 项 / OPEN {_rc37['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows37:
        if pth.exists():
            sec37.append(f"| {label} | `{s16(pth)}` |")
    sec37.append("")
    body37 = "\n".join(sec37)
    if MARK37 in txt:
        txt = re.sub(re.escape(MARK37) + r"[\s\S]*?(?=\n## |\Z)", body37, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body37
    txt = txt.replace("W3 Boundary **v2.08**", "W3 Boundary **v2.09**")
    # ── §38 CO-164（收敛判定硬化） ─────────────────────────────────────────
    MARK38 = "## 38. CO-164"
    _rc38 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec38 = [MARK38 + "（**L2 自裁 · 收敛判定硬化**：规范复现序 rc 机判执行器）", "",
             f"- 实测事故（CO-163 期间，机判）：`p3_v57_co146_boundary_append.py` 因 §37 文本内 f-string 花括号语法错误**每轮 rc=1 崩溃** ⇒ 第 37 节从未写入、"
             f"boundary 停在 v2.08、pin 表陈旧（co77 = CITATION_MISMATCH、co135/co136 = FAIL）；而「幂等循环」只看 boundary/记录 sha ⇒ 报 CONVERGED。"
             f"即 **「以 sha 稳定替代 rc 检查」= 假收敛**；本会话由一个独立 rc 复核发现（自查也据此复现并修复）。",
             f"- 处置（**CO-164**）：新增 `p3_v57_co164_order_runner.py`（**不在**规范序内运行，避免自递归；报告落 `.archer_tmp/`，**不被 boundary 引用** ⇒ 不构成下游快照/不动点）："
             f"① rc 策略 `EXPECTED_NONZERO = {{co146_jlc_dfm_gate}}`（verdict=FAIL 属预期），其余任一步非零 ⇒ **立即停机**并报门名/rc/stderr 尾；"
             f"② **真收敛** = rc 全合规 ∧ 受控 sha 逐轮稳定；③ `--check` 静态体检 t01..t06（步骤存在/可编译/rc 策略/判据灵敏度/稳定性判据/序文本一致）。",
             f"- 复核：`--check` **6/6 True**（t06 当场抓到本文档序与执行器 ORDER 的短别名漂移 `co159_rev19_review`，已改为实际步骤名）；"
             f"端到端负控：把 `co78` 步替换为 rc=3 合成件 ⇒ **abort（rc=1，iterations=1）不报收敛**；登记簿 **{_rc38['total']} 项 / OPEN {_rc38['OPEN']}**。", "",
             "> **R-CO164-1**：复现序收敛判定**rc 优先** —— 除 `EXPECTED_NONZERO` 白名单（当前仅 `co146_jlc_dfm_gate`，其 verdict=FAIL 属预期）外，"
             "任一步 rc≠0 即**立即停机**；**禁止**以「sha 稳定」单独判收敛。",
             "> **R-CO164-2**：规范序**文本**与执行器 `ORDER` 须**有序一致**（由 runner `--check` t06 机判）；新增/变更步骤须同步 runner 与本 boundary。",
             "> **R-CO164-3**（复现序，取代 R-CO163-3；步骤集不变）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
             "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → "
             "co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → "
             "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
             "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → "
             "co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → "
             "co146_boundary_append`，**循环至 sha 稳定**（收敛判定须遵 R-CO164-1：以 rc 为准）。",
             "", "| 工件 | sha16 |", "|---|---|"]
    _rows38 = [("工具 `p3_v57_co164_order_runner.py`（rc 策略 + 真收敛 + `--check` t01..t06）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co164_disposition.py`", K2 / "tools/p3_v57_co164_disposition.py"),
               ("工具 `p3_v57_co146_boundary_append.py`（§38 + 序文本订正）", K2 / "tools/p3_v57_co146_boundary_append.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc38['total']} 项 / OPEN {_rc38['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows38:
        if pth.exists():
            sec38.append(f"| {label} | `{s16(pth)}` |")
    sec38.append("")
    body38 = "\n".join(sec38)
    if MARK38 in txt:
        txt = re.sub(re.escape(MARK38) + r"[\s\S]*?(?=\n## |\Z)", body38, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body38
    txt = txt.replace("W3 Boundary **v2.09**", "W3 Boundary **v2.10**")
    DOC.write_text(txt)
    print("boundary sha16:", s16(DOC), "| lines:", len(txt.splitlines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
