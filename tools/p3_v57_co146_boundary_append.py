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
    # ── §39 CO-165（收敛执行器自加固） ─────────────────────────────────────
    MARK39 = "## 39. CO-165"
    _rc39 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec39 = [MARK39 + "（**L2 自裁 · 收敛执行器加固**：白名单证据 + 受控 sha 全域）", "",
             f"- 实测缺口（修前，均机判）：**G-1** CO-164 执行器的白名单只按 `rc≠0` 放行 ⇒ 白名单步（当前仅 `co146_jlc_dfm_gate`）的**任何**非零——"
             f"含崩溃/静默失败——都被当「预期 FAIL」。负控：把 DFM 闸替换为 `raise SystemExit('boom')`（rc=1、stderr 无 traceback）⇒ **旧判据放行**；"
             f"仅加 Traceback 检测**仍不足**（不打印 traceback 的失败会让盘上**陈旧** FAIL 记录充当 verdict 证据 —— 由本会话自己的端到端负控当场证伪）。"
             f"**G-2** 受控 sha 仅 7 件（漏 co106/co150/打样包件）⇒ 未受控文件的 2-循环/抖动对收敛判定**不可见**。",
             f"- 处置（**CO-165**，执行器升 **CO-164.2**）：白名单项改 `verdict/record/why` 结构化 + 纯判据 "
             f"`allowlist_decision(step, rc, stderr, verdict, record_fresh)` —— 白名单步须 **rc≠0 ∧ 无 Traceback ∧ 记录由本次执行产出（mtime 新鲜）"
             f"∧ 记录 verdict == 声明 verdict** 方判 `expected_nonzero`，否则判 `expected_step_returned_zero`/`expected_step_crashed`/"
             f"`expected_step_record_not_produced`/`expected_step_verdict_mismatch` 并**立即停机**；`watch_paths()` 覆盖 boundary + **全部**记录 + 台账/登记簿 + "
             f"打样包 MANIFEST/ORDER_NOTES；`--check` 增 **t07**（四类伪通过负控 + 恒真正控）/ **t08**（受控集覆盖记录类产物）。",
             f"- 复核：`--check` **8/8 True**；负控 A（co78 步 rc=3 合成件）⇒ abort(rc=1)；负控 B（DFM 步 `SystemExit('boom')`）⇒ "
             f"abort class=`expected_step_record_not_produced`；正控：真 DFM 闸（重写记录、verdict=FAIL）判 `expected_nonzero` 且整序 "
             f"**converged（iterations 2 / rc=0）**。登记簿 **{_rc39['total']} 项 / OPEN {_rc39['OPEN']}**（注：`co148` 登记项在序内为 OPEN、由 `co150` 收口 ⇒ 中途 OPEN 属正常，须以整序收敛后为准）。", "",
             "> **R-CO165-1**：`EXPECTED_NONZERO` 白名单步须给**双重证据** —— 期望 `verdict` **且** 记录由**本次执行产出**（mtime 新鲜）；`rc≠0` 本身不构成预期 FAIL 的证据（崩溃/静默失败不得被放行）。",
             "> **R-CO165-2**：收敛判定的受控 sha 须覆盖**全部**序内产物（boundary + 全部 `m13_v57_co*.json` + 台账/登记簿 + 打样包件）；新增产物须落入 `watch_paths()`。",
             "> **R-CO165-3**（复现序，步骤集与 R-CO164-3 相同）：规范复现序 = `co146_impedance_table → co146_pm_eval → co146_ledger_add → "
             "co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → "
             "co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
             "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → "
             "co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → "
             "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
             "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → "
             "co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → "
             "co146_boundary_append`，**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2）。",
             "", "| 工件 | sha16 |", "|---|---|"]
    _rows39 = [("工具 `p3_v57_co164_order_runner.py`（CO-164.2 / `allowlist_decision` + `watch_paths` + t07/t08）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co165_runner_hardening.py`", K2 / "tools/p3_v57_co165_runner_hardening.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc39['total']} 项 / OPEN {_rc39['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows39:
        if pth.exists():
            sec39.append(f"| {label} | `{s16(pth)}` |")
    sec39.append("")
    body39 = "\n".join(sec39)
    if MARK39 in txt:
        txt = re.sub(re.escape(MARK39) + r"[\s\S]*?(?=\n## |\Z)", body39, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body39
    txt = txt.replace("W3 Boundary **v2.10**", "W3 Boundary **v2.11**")
    # ── §40 CO-166（非执行者对抗复评 CO-159..CO-165） ───────────────────────
    MARK40 = "## 40. CO-166"
    _rc40 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord166 = ('co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append')
    sec40 = [MARK40 + "（**非执行者对抗复评**：CO-159..CO-165；as-found @ `e427909`）", "",
             "- 复评方：context 归零的续接会话（满足 handoff-z39 §5「另一会话，禁自评」）；对象钉在受评基线 commit，"
             "`git show` 内存重放 ⇒ 结论**可重放、不随后续修复漂移**。方法：正控 V0..V6 + 负控 P1..P6（内存注入、零落盘、零坐标搜索）。",
             "- 结论：verdict **PASS_WITH_FINDINGS**；findings **6**（F-1..F-6）。独立确认含：冻结四源 4/4、"
             "co124 CO-124.9（37 牙齿/0 findings）、co150 CO-150.2（5/5）、co106 CO-106.4（8/8）、co120（12/12）、co77 PASS、"
             "co135 CO-135.3、co136 PASS、打样包 CO146-PKG.4（34 件/13 牙齿）、登记簿 65 项/OPEN 0（co159:F-1..F-12 全 CLOSED）、"
             "co124 必需 DV 清单 == co153 `KIND_EXPECT`、t10 来源 pin 正控、co146_boundary_append **只读重放逐字节幂等且仅写 boundary**。",
             f"- findings 处置见 §41（CO-167）。登记簿 **{_rc40['total']} 项 / OPEN {_rc40['OPEN']}**。", "",
             "> **R-CO166-1**：复评必须由**另一会话**（context 归零）执行，且对象钉在受评基线 commit（`git show` 重放）"
             "⇒ 结论可重放、不随后续修复漂移。",
             "> **R-CO166-2**：负控须为**内存注入**（零落盘/零坐标搜索）；不得以「记录自证」充当独立证据。",
             "> **R-CO166-3**（复现序，取代 R-CO165-3；步骤集新增 co166 复评步）：规范复现序 = `" + _ord166 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows40 = [("工具 `p3_v57_co166_rev19_co159_co165_review.py`（只读复评；对象钉 `e427909`）",
                K2 / "tools/p3_v57_co166_rev19_co159_co165_review.py"),
               ("记录 `m13_v57_co166_rev19_co159_co165_review.json`（重建）",
                STEP2 / "m13_v57_co166_rev19_co159_co165_review.json"),
               ("卡 `m13_v57_CO166_rev19_co159_co165_review.md`（重建）",
                STEP2 / "m13_v57_CO166_rev19_co159_co165_review.md"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc40['total']} 项 / OPEN {_rc40['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows40:
        if pth.exists():
            sec40.append(f"| {label} | `{s16(pth)}` |")
    sec40.append("")
    body40 = "\n".join(sec40)
    if MARK40 in txt:
        txt = re.sub(re.escape(MARK40) + r"[\s\S]*?(?=\n## |\Z)", body40, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body40
    txt = txt.replace("W3 Boundary **v2.11**", "W3 Boundary **v2.12**")
    # ── §41 CO-167（CO-166 findings 处置 + 收敛判据加固） ───────────────────
    MARK41 = "## 41. CO-167"
    _rc41 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord167 = ('co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → co167_co166_findings_disposition → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append')
    sec41 = [MARK41 + "（**L2 自裁 · CO-166 findings 处置**：收敛判据加固）", "",
             "- 实测缺口（CO-166 复评，均机判内存注入）：**F-1**（medium）序解析器取「最后一条含字面量 `规范复现序` 赋值的行」"
             "⇒ 更新的 R-COxxx-3 若改措辞即被**回落到更旧序行**，t06 假通过；**F-2**（low）白名单「记录由本次执行产出」用绝对 mtime "
             "`≥ t0-1.0` ⇒ 记录 mtime 落在**未来**（时钟回拨/网络盘/异机）时，**崩溃**步仍被判 `expected_nonzero`；"
             "**F-3**（low）白名单记录 ⊆ `watch_paths()` 无牙齿；**F-4**（low）t09 无锚子串（`185Ω`/`11.6 mm` 误命中）+ 容差记号被厚度公差满足；"
             "**F-5**（low）t09 对措辞敏感（`1.6mm`/`外层1oz`）；**F-6**（low）白名单 expected verdict 允许写成 `PASS`。",
             "- 处置（**CO-167**）：① 序解析器增「末条可解析序行之后仍有其它 `规范复现序` 提及 ⇒ 返回 []」fail-closed（F-1）；"
             "② 白名单刷新判据改**变更检测** `record_refreshed(before, after)`（exists / mtime_ns / 内容 sha16，与时钟无关）（F-2）；"
             "③ `--check` 增 **t09**（白名单记录 ⊆ 受控集）（F-3）/ **t10**（刷新判据变更检测灵敏度）（F-2）；"
             "④ `binding_param_checks` 记号改**有锚正则 + 柔性空白 + 容差须在 zdiff 邻域**（F-4/F-5）；"
             "⑤ `allowlist_decision` 与 t07 禁 expected verdict = `PASS`（F-6）。打样包升 **CO146-PKG.5**；执行器升 **CO-167.1**。",
             "- 复核：`--check` **t01..t10 全 True**；`binding_param_checks` 现行备注 7/7、改排版仍 7/7、`185Ω`/`11.6 mm`/容差漂移均不通过；"
             f"整序 **converged**（rc 策略不变）。登记簿 **{_rc41['total']} 项 / OPEN {_rc41['OPEN']}**。", "",
             "> **R-CO167-1**：白名单「记录由本次执行产出」一律用**变更检测**（exists/mtime_ns/sha），**禁止**绝对时间比较（未来 mtime 可伪新鲜）。",
             "> **R-CO167-2**：白名单记录须 ⊆ `watch_paths()`；expected `verdict` 不得为 `PASS`。",
             "> **R-CO167-3**（复现序，取代 R-CO166-3）：规范复现序 = `" + _ord167 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows41 = [("工具 `p3_v57_co167_co166_findings_disposition.py`", K2 / "tools/p3_v57_co167_co166_findings_disposition.py"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-167.1 / `record_refreshed` + t09/t10 + 序解析 fail-closed）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.5 / t09 有锚正则）",
                K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("记录 `m13_v57_co146_jlc_fab_package.json`（重建）", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc41['total']} 项 / OPEN {_rc41['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows41:
        if pth.exists():
            sec41.append(f"| {label} | `{s16(pth)}` |")
    sec41.append("")
    body41 = "\n".join(sec41)
    if MARK41 in txt:
        txt = re.sub(re.escape(MARK41) + r"[\s\S]*?(?=\n## |\Z)", body41, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body41
    txt = txt.replace("W3 Boundary **v2.12**", "W3 Boundary **v2.13**")
    # ── §42 CO-168（登记簿自洽性硬化） ─────────────────────────────────────
    MARK42 = "## 42. CO-168"
    _rc42 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord168 = ('co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → co167_co166_findings_disposition → co168_register_consistency → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append')
    sec42 = [MARK42 + "（**L2 自裁 · 登记簿自洽性硬化**：status 词汇 + counts 复算）", "",
             "- 实测缺口（修前，均机判）：**G-1** 登记簿 `status` 无词汇机判 —— 任一项 status 改成 `open`/`Closed` 后 co124 仍 PASS / 0 findings，"
             "该项**静默落出** `counts` 的 OPEN 计数（未结缺陷被算作已结）⇒ handoff/§ 节引用的「OPEN 0」不可信；"
             "**G-2** `meta.counts` 为自述摘要、无闸据 `items` 复算 —— 改 `total=999` / `OPEN=7` 后仍 PASS（该摘要被当权威引用）。",
             "- 处置（**CO-168**）：co124 升 **CO-124.10** —— 增纯函数 `register_consistency(reg)` + 词汇 "
             "`REGISTER_STATUSES = (OPEN, CLOSED, PROVED)`：① status 越词汇 ⇒ `status_not_in_vocabulary`；"
             "② `meta.counts` 须与据 items 复算的（kind / OPEN / total 三元）**键集与值逐项一致**，否则 `counts_not_rederived_from_items`；"
             "任一 ⇒ `FAIL_REGISTER_STALE`（记录落 `register_stale`）。牙齿增 T21 / T21b / T21c（co124 40/40）。",
             f"- 复核：真登记簿 `register_stale == []`（{_rc42['total']} 项 / OPEN {_rc42['OPEN']} 复算一致）；"
             f"注入 status 拼写错 / counts 漂移 ⇒ 分别判 `status_not_in_vocabulary` / `counts_not_rederived_from_items`。", "",
             "> **R-CO168-1**：登记簿每项 `status` 须 ∈ `REGISTER_STATUSES`；新增状态须先入词汇（禁拼写自由文本）。",
             "> **R-CO168-2**：`meta.counts` 为**派生**字段，须与据 `items` 的复算逐项一致；写登记簿的步骤须在写后重算。",
             "> **R-CO168-3**（复现序，取代 R-CO167-3；步骤集新增 co168）：规范复现序 = `" + _ord168 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows42 = [("工具 `p3_v57_co168_register_consistency.py`", K2 / "tools/p3_v57_co168_register_consistency.py"),
               ("工具 `p3_v57_co124_input_selfcheck_gate.py`（CO-124.10 / `register_consistency` + T21 系列）",
                K2 / "tools/p3_v57_co124_input_selfcheck_gate.py"),
               ("记录 `m13_v57_co124_input_selfcheck_gate.json`（重建）", STEP2 / "m13_v57_co124_input_selfcheck_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc42['total']} 项 / OPEN {_rc42['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows42:
        if pth.exists():
            sec42.append(f"| {label} | `{s16(pth)}` |")
    sec42.append("")
    body42 = "\n".join(sec42)
    if MARK42 in txt:
        txt = re.sub(re.escape(MARK42) + r"[\s\S]*?(?=\n## |\Z)", body42, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body42
    txt = txt.replace("W3 Boundary **v2.13**", "W3 Boundary **v2.14**")
    # ── §43 CO-169（收敛判据硬化：逐步产物产出证据） ───────────────────────
    MARK43 = "## 43. CO-169"
    _rc43 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord169 = ('co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append')
    sec43 = [MARK43 + "（**L2 自裁 · 收敛判据硬化**：逐步产物产出证据）", "",
             "- 实测缺口（机判探针）：CO-165/CO-167 的「记录由本次执行产出」（`record_refreshed` 变更检测）**只作用于白名单步**；"
             "其余诸步的契约仅为 `rc == 0`。一个**不崩也不写**的步（早退分支 / 漏写 / 被改成只读检查）会因产物 sha 不变而被"
             "「sha 稳定 ⇒ 收敛」**背书**（与 CO-164 假收敛同族，故障类相反：CO-164 = 崩而 sha 不变）。",
             "- 处置（**CO-169**）：执行器升 **CO-169.1** —— 增纯判据 `step_did_work(before, after)`（受控产物集 `watch_paths()` 的 "
             "mtime_ns 快照；前进 / 新增 / 删除任一即算做事）与 `zero_rc_class`；运行循环逐步取受控快照，`rc==0` 而**零产物变动** ⇒ "
             "类 `step_wrote_nothing` 并**立即停机**；报告内逐步落 `did_work` 证据；`--check` 增 **t11**。",
             f"- 复核：真序 37 步逐步探针 `did_work` **全 True**（每步至少刷写 1 件受控产物）；合成「rc=0 不写」步 ⇒ `step_wrote_nothing` 停机；"
             f"整序 **converged**。登记簿 **{_rc43['total']} 项 / OPEN {_rc43['OPEN']}**。", "",
             "> **R-CO169-1**：规范序**每步**须写出至少一个受控产物（`watch_paths()` 覆盖内）；`rc==0` 不构成「做了事」的证据；"
             "纯只读步骤须显式登记豁免，不得默认放行。",
             "> **R-CO169-2**：新增步骤须确保其产物在 `watch_paths()` 覆盖内，否则判 `step_wrote_nothing` 停机。",
             "> **R-CO169-3**（复现序，取代 R-CO168-3；步骤集新增 co169）：规范复现序 = `" + _ord169 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows43 = [("工具 `p3_v57_co169_step_output_oracle.py`", K2 / "tools/p3_v57_co169_step_output_oracle.py"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-169.1 / `step_did_work` + t11）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc43['total']} 项 / OPEN {_rc43['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows43:
        if pth.exists():
            sec43.append(f"| {label} | `{s16(pth)}` |")
    sec43.append("")
    body43 = "\n".join(sec43)
    if MARK43 in txt:
        txt = re.sub(re.escape(MARK43) + r"[\s\S]*?(?=\n## |\Z)", body43, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body43
    txt = txt.replace("W3 Boundary **v2.14**", "W3 Boundary **v2.15**")
    # ── §44 CO-170（交付物绑定：03_stackup 叠层图 ↔ 声明定值表） ─────────────
    MARK44 = "## 44. CO-170"
    _rc44 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord170 = ('co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append')
    sec44 = [MARK44 + "（**L2 自裁 · 交付物绑定**：叠层图 ↔ 声明定值表）", "",
             "- 实测缺口（修前，机判）：**G-1** `stackup_svg(spec)` **只接收 SPEC**，其「外层 1oz / 内层 0.5oz」与铜厚矩形高度为"
             "**硬编码字面量**；声明定值表 `jlc_prototype_parameters_v1.json` 改铜厚时叠层图**不跟随**，且当时 13 项牙齿"
             "**无一项**读取该图（t09 只绑定 `ORDER_NOTES.md`）。备注 §1/§2 与叠层图**同时**随单提交 ⇒ 制造侧可能按陈旧铜厚施工"
             "（与 CO-163 G-1 同族，对象从备注扩到**制造图**）。",
             "- 处置（**CO-170**）：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.6** —— 抽出 `_tok_match`，新增纯谓词 "
             "`stackup_svg_binding_checks(svg_text, binding)`（叠层图须逐项含声明表记号：叠层码 / 成品厚 / 外层铜 / 内层铜）；"
             "牙齿 `t11_stackup_svg_declared_binding` + `t11b`（声明铜厚漂移 ⇒ 必判不通过）；记录落 `declared_binding.stackup_svg_checks`。",
             f"- 复核：现行声明 **4/4 命中**（打样包牙齿 **15/15**）；声明铜厚改 2oz ⇒ `outer_copper=False`（t11 抓住）；"
             f"叠层图 sha16 `44370475b258848f` **逐字节不变**。登记簿 **{_rc44['total']} 项 / OPEN {_rc44['OPEN']}**。", "",
             "> **R-CO170-1**：随单提交的**每一件**制造/工程输入（备注 / 叠层图 / 阻抗表 / 裁定件）内的工程定值，"
             "均须与声明定值表（或其 SPEC 来源）机判绑定；新增交付图/表须同步加绑定牙齿。",
             "> **R-CO170-2**：绑定判据一律用 CO-167 的**有锚正则**（数值边界 + 柔性空白），不得裸子串。",
             "> **R-CO170-3**（复现序，取代 R-CO169-3；步骤集新增 co170）：规范复现序 = `" + _ord170 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows44 = [("工具 `p3_v57_co170_stackup_binding.py`", K2 / "tools/p3_v57_co170_stackup_binding.py"),
               ("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.6 / `stackup_svg_binding_checks` + t11/t11b）",
                K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("叠层图 `L5/jlc_package/03_stackup/JLC08161H_stackup.svg`", L5 / "jlc_package" / "03_stackup" / "JLC08161H_stackup.svg"),
               ("记录 `m13_v57_co146_jlc_fab_package.json`（重建）", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc44['total']} 项 / OPEN {_rc44['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows44:
        if pth.exists():
            sec44.append(f"| {label} | `{s16(pth)}` |")
    sec44.append("")
    body44 = "\n".join(sec44)
    if MARK44 in txt:
        txt = re.sub(re.escape(MARK44) + r"[\s\S]*?(?=\n## |\Z)", body44, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body44
    txt = txt.replace("W3 Boundary **v2.15**", "W3 Boundary **v2.16**")
    # ── §45 CO-171（下单备注内记录派生数字的绑定） ─────────────────────────
    MARK45 = "## 45. CO-171"
    _rc45 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord171 = ('co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → co171_order_notes_record_figures → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append')
    sec45 = [MARK45 + "（**L2 自裁 · 交付物绑定**：备注内记录派生数字 ↔ 来源记录）", "",
             "- 实测缺口（修前，机判）：**G-1** `ORDER_NOTES` §5 写死「model-spread 观察值（**+11.6%**）」，该串**不存在于任何记录**"
             "（`grep 11.6` 在 L2/L3 记录零命中）；阻抗表记录自身在 s=0.395mm（设计名义最宽间距）M2(HJ)=94.94Ω 对目标 85Ω 即 **+11.69%**，"
             "且「模型间 spread」≈4.8% ⇒ 客户可见的阻抗告警数字**无源且已陈旧**，措辞亦失实（CO-163 的 t09 只绑声明定值表 7 记号，不覆盖记录派生值）。"
             "**G-2** §7 的 DRC 计数（42 项 / `lib_footprint_*` 41 / silk 1）无牙齿绑定（现态一致，但无护栏）。",
             "- 处置（**CO-171**）：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.7** —— 新增 `impedance_watch_figure(imp)`"
             "（由记录派生 watch 下模型相对目标的最大偏离）与 `order_notes_record_figures(note, imp, dfm)`；**订正备注字面量**"
             "（+11.6% → **+11.7%**，措辞订正为「模型偏离观察值（M2(HJ) 相对目标）」+ 补「模型间 spread ≈4.8%」）；"
             "牙齿 `t12_order_notes_record_figures` + `t12b`（灵敏度）；记录落 `record_figures`。",
             f"- 复核：`record_figures.impedance_watch.dev_pct = 11.69`（F.Cu / M2_HJ_Cohn / 0.395mm）；"
             f"`record_figures.drc_as_designed_n = 42`；打样包牙齿 **17/17**。登记簿 **{_rc45['total']} 项 / OPEN {_rc45['OPEN']}**。", "",
             "> **R-CO171-1**：客户可见备注/图中的**记录派生**数字（观察值/计数/边界值）须绑定其来源记录；"
             "来源记录变更而备注未同步即 FAIL。",
             "> **R-CO171-2**：订正客户可见数值须同时留下「来源记录 → 数字」的可重算路径（本件：`impedance_watch_figure` / t12）。",
             "> **R-CO171-3**（复现序，取代 R-CO170-3；步骤集新增 co171）：规范复现序 = `" + _ord171 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2）。", "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows45 = [("工具 `p3_v57_co171_order_notes_record_figures.py`", K2 / "tools/p3_v57_co171_order_notes_record_figures.py"),
               ("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.7 / `order_notes_record_figures` + t12/t12b）",
                K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("下单备注 `L5/jlc_package/ORDER_NOTES.md`（**§5 数值已订正**）", L5 / "jlc_package" / "ORDER_NOTES.md"),
               ("记录 `m13_v57_co146_jlc_fab_package.json`（重建）", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               ("阻抗表 `m13_v57_co146_impedance_table.json`（来源记录）", STEP2 / "m13_v57_co146_impedance_table.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc45['total']} 项 / OPEN {_rc45['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows45:
        if pth.exists():
            sec45.append(f"| {label} | `{s16(pth)}` |")
    sec45.append("")
    body45 = "\n".join(sec45)
    if MARK45 in txt:
        txt = re.sub(re.escape(MARK45) + r"[\s\S]*?(?=\n## |\Z)", body45, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body45
    txt = txt.replace("W3 Boundary **v2.16**", "W3 Boundary **v2.17**")
    # ── §46 CO-172 / CO-173（非执行者对抗复评 + 记录派生数字绑定补强） ──────────
    MARK46 = "## 46. CO-172 / CO-173"
    _rc46 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord172 = ("co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → co148_u6_datasheet_inputs → "
               "co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → co146_jlc_dfm_gate → co146_jlc_fab_package → "
               "co152_findings_disposition → co155_co154_findings_disposition → co156_co154_open_disposition → co157_gate_hardening_3 → "
               "co158_l5_packet_selfcontained → co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → "
               "co161_gap_hardening_4 → co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → "
               "co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → "
               "co171_order_notes_record_figures → co172_rev19_co166_co171_review → co173_co172_findings_disposition → "
               "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
               "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → "
               "co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → "
               "co106_reference_plane_gate → co146_boundary_append")
    sec46 = [MARK46 + "（**L2 自裁 · 非执行者对抗复评 + 记录派生数字绑定补强**）", "",
             "- **复评（CO-172，非执行者会话、as-found 钉在 `7bffb75`；`git show` 取源 + 内存注入、零落盘、零坐标搜索）**："
             "对象 = CO-166..CO-171；verdict **PASS_WITH_FINDINGS**（7 findings）。handoff §4.2 指定关注点逐一裁定：",
             "  **F-1**（medium）§5「模型间 spread ≈4.8%」为记录派生数字但**无来源记录串、亦无牙齿**（t12 只绑 dev% +11.7%）"
             "⇒ R-CO171-1 在本备注内**仍有未绑定项**（P1：仅改 spread、不动 dev% ⇒ as-found 判据全 True）；",
             "  **F-2**（medium）§2 非通孔过孔**逐 span 分解**（92/88/32/8）硬编码，源 = DFM 记录 `via_type_census` —— "
             "**总量绑定 ≠ 分量绑定**（P2）；",
             "  **F-3**（medium）§3 阻焊净距 0.0695 / 欠 0.0205 / 回退 0.0995 / 开窗 0.05→0.02mm 硬编码，源 = CO-147 记录 `mask_measure`（P3）；",
             "  **F-4**（medium）§6 U6 热数字（PACT 4.7–7.0W / θJA 17.4 / Tj 限 120 / 121.8–161.8 / ψJB 路线 173.6 / Ta 40°C）硬编码，"
             "源 = CO-148 + CO-149（P4）；",
             "  **F-5**（low）§4 JLC 限值散文与「板规铜-板边 0.30mm」（源 = JLC 能力记录 + **冻结** `drc_rules.manufacturing.min_copper_edge_clearance`）"
             "在**备注与 DFM 闸工具两处**均硬编码（P5/P6）；",
             "  **F-6**（medium）叠层图（03_，**随单提交的制造输入**）**铜厚矩形几何**硬编码 `0.035`/`0.0175`mm，t11 只绑**文本**（P7）"
             "⇒ 声明铜厚变更时图与声明在**几何上**脱钩、制造侧按图施工；",
             "  **F-7**（low）runner `step_did_work` 快照**单信号 mtime_ns**（P8：值为标量 int）⇒ 粗粒度/网络 FS 同刻重写、mtime 规范化/回写、"
             "时钟回拨下**假停机**（fail-closed，不致假通过）；且受控集为**全局集合、非步本地** ⇒ 并发会话写受控件可被误判为「本步做了事」（假通过方向）。"
             "　关注点④（`REGISTER_STATUSES` / `counts` 复算键集）裁定 = **不过严**（并集比对 ⇒ 多写/少写键均 fail-closed；as-found 复算逐项一致）。",
             "- **处置（CO-173）**：",
             "  ① `p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.8** —— 新增纯谓词 `impedance_spread_pct` / `via_census_figures` / "
             "`mask_clearance_figures` / `thermal_figures` 与 capability+rules 派生判据；牙齿 **t12c..t12h**（逐来源负控）与 "
             "**t11c/t11d**（叠层图**几何**正控/负控）；`stackup_svg(spec, binding)` 的铜厚矩形高度与标题 oz 改由**声明定值表**派生"
             "（1oz=0.035mm 标称；当前 1oz/0.5oz ⇒ 21.00/10.50 px）。",
             "  ② `p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.2** —— 「板规铜-板边」值由冻结 `drc_rules` 派生 + 牙齿 **t03**（正控/灵敏度）。",
             "  ③ `p3_v57_co164_order_runner.py` 升 **CO-169.2** —— `_artifact_stamp` 多信号指纹（mtime_ns + ctime_ns + size + 内容 sha16）、"
             "`_snap_watched` 返回指纹字典 + 静态齿 **t12**。",
             f"  ④ **复核**：打样包牙齿 **25/25**；`ORDER_NOTES.md` 与叠层图**输出逐字节不变**"
             f"（`{s16(L5 / 'jlc_package' / 'ORDER_NOTES.md')}` / `{s16(L5 / 'jlc_package' / '03_stackup' / 'JLC08161H_stackup.svg')}`）；"
             f"DFM 闸 rc=1（预期 FAIL）且 t01..t03 全 True；登记簿 **{_rc46['total']} 项 / OPEN {_rc46['OPEN']}**（+7 TOOL_DEFECT，全 CLOSED）。",
             "",
             "> **R-CO172-1**：客户可见交付物内**凡可由记录复算的数字**（含**导出量**：模型间 spread、分量计数、回退净距）一律绑定来源记录并配**负控**；"
             "仅绑定总量、或只绑「主」数字，**视为未绑定**。",
             "> **R-CO172-2**：随单提交的**制造输入**不仅**文本**、其**几何**亦须由声明定值派生（或至少具备几何牙齿）；"
             "「文本已绑定 ⇒ 视为已绑」不成立。",
             "> **R-CO172-3**：复现序执行器的「做了事」判据快照须为**多信号**（mtime_ns + ctime_ns + size + 内容指纹）；"
             "残余（全局受控集、非步本地归因）须**如实登记**，不得以「已硬化」掩盖。",
             "> **R-CO172-4**（复现序，取代 R-CO171-3；步骤集新增 co172/co173）：规范复现序 = `" + _ord172 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows46 = [("工具 `p3_v57_co172_rev19_co166_co171_review.py`（CO-172.1）",
                K2 / "tools/p3_v57_co172_rev19_co166_co171_review.py"),
               ("工具 `p3_v57_co173_co172_findings_disposition.py`",
                K2 / "tools/p3_v57_co173_co172_findings_disposition.py"),
               ("复评记录 `m13_v57_co172_rev19_co166_co171_review.json`",
                STEP2 / "m13_v57_co172_rev19_co166_co171_review.json"),
               ("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.8 / t12c..t12h + t11c/t11d）",
                K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("工具 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.2 / 板规铜-板边派生 + t03）",
                K2 / "tools/p3_v57_co146_jlc_dfm_gate.py"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-169.2 / 多信号快照 + t12；42 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("下单备注 `L5/jlc_package/ORDER_NOTES.md`（**逐字节不变**）", L5 / "jlc_package" / "ORDER_NOTES.md"),
               ("叠层图 `03_stackup/JLC08161H_stackup.svg`（**逐字节不变**）",
                L5 / "jlc_package" / "03_stackup" / "JLC08161H_stackup.svg"),
               ("打样包记录 `m13_v57_co146_jlc_fab_package.json`（重建 / PKG.8）",
                STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               ("DFM 闸记录 `m13_v57_co146_jlc_dfm_gate.json`（DFM.2）",
                STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc46['total']} 项 / OPEN {_rc46['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows46:
        if pth.exists():
            sec46.append(f"| {label} | `{s16(pth)}` |")
    sec46.append("")
    body46 = "\n".join(sec46)
    if MARK46 in txt:
        txt = re.sub(re.escape(MARK46) + r"[\s\S]*?(?=\n## |\Z)", body46, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body46
    txt = txt.replace("W3 Boundary **v2.17**", "W3 Boundary **v2.18**")
    # ── §47 CO-174（复现序归因硬化：did_work 步本地化） ─────────────────────────
    MARK47 = "## 47. CO-174"
    _rc47 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord174 = ("co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → "
               "co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → "
               "co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
               "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → "
               "co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → "
               "co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → "
               "co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → "
               "co171_order_notes_record_figures → co172_rev19_co166_co171_review → co173_co172_findings_disposition → "
               "co174_step_artifact_attribution → co124_input_selfcheck_gate → co150_k9_domain_gate → "
               "co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → "
               "co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → "
               "co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append")
    sec47 = [MARK47 + "（**L2 自裁 · 复现序归因硬化**）", "",
             "- **问题（CO-172 F-7 残余）**：`step_did_work` 的受控集是**全局** `watch_paths()` ⇒ 并发/他人写**任一**受控件"
             "都会被误判为「本步做了事」（假通过方向）。",
             "- **处置**：`p3_v57_co164_order_runner.py` 升 **CO-169.3** ——",
             "  ① `STEP_ARTIFACTS`：**每步主产物集**（由实测探针逐步跑 ORDER **钉定**，非猜测；42 步无一步为空）；",
             "  ② `_snap_watched(paths)` 参数化；执行循环中 `did_work` 归因**仅限本步声明集**（全局集仅保留给收敛 sha，R-CO165 不变）；",
             "  ③ 报告增 `declared_changed` / `stray_changed`（后者 = 本步窗口内**非声明**受控件的变动证据）；",
             "  ④ 牙齿 **t13**（每步声明完备 + ⊆ 全局受控集）/ **t13b**（步本地负控：非声明件变动不得归因本步）/ "
             "**t13c**（共享件残余枚举一致）。",
             "- **残余（如实登记）**：处置类 17 步的唯一主产物是**共享**登记簿（台账另被 4 步共享）⇒ 共享件上的他写仍可误判；"
             "已显式枚举于 `SHARED_ARTIFACT_RESIDUAL` 并 t13c 机判（防静默遗忘）；彻底关闭须每步独立标记件（下轮候选）。",
             f"- **登记簿**：+2（`co174:G-1/G-2`，全 CLOSED；{_rc47['total']} 项 / OPEN {_rc47['OPEN']}）。",
             "",
             "> **R-CO174-1**：复现序执行器的 `did_work` **归因**须**步本地**（仅本步声明的主产物集）；"
             "以全局受控集代为背书**不成立**。共享主产物上的他写属**已登记残余**，须**显式枚举**且机判（禁静默遗忘）。",
             "> **R-CO174-2**（复现序，取代 R-CO172-4；步骤集新增 co174）：规范复现序 = `" + _ord174 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows47 = [("工具 `p3_v57_co164_order_runner.py`（CO-169.3 / STEP_ARTIFACTS + 步本地归因 / 43 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co174_step_artifact_attribution.py`",
                K2 / "tools/p3_v57_co174_step_artifact_attribution.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc47['total']} 项 / OPEN {_rc47['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows47:
        if pth.exists():
            sec47.append(f"| {label} | `{s16(pth)}` |")
    sec47.append("")
    body47 = "\n".join(sec47)
    if MARK47 in txt:
        txt = re.sub(re.escape(MARK47) + r"[\s\S]*?(?=\n## |\Z)", body47, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body47
    txt = txt.replace("W3 Boundary **v2.18**", "W3 Boundary **v2.19**")
    # ── §48 CO-175（交付包 parity / 派生绑定补强） ─────────────────────────────
    MARK48 = "## 48. CO-175"
    _rc48 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord175 = ("co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → "
               "co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → "
               "co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
               "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → "
               "co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → "
               "co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → "
               "co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → "
               "co171_order_notes_record_figures → co172_rev19_co166_co171_review → co173_co172_findings_disposition → "
               "co174_step_artifact_attribution → co175_package_parity_binding → co124_input_selfcheck_gate → "
               "co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → "
               "co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → "
               "co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → "
               "co146_boundary_append")
    sec48 = [MARK48 + "（**L2 自裁 · 交付物绑定补强**）", "",
             "- **问题（查漏实测）**：交付包内 `04_impedance/impedance_table.{json,md}` 为**随单件**（ORDER_NOTES §1/§2 明列；"
             "板厂**据此控阻抗**），却是 `shutil.copy` 来源副本且**无 parity 牙齿**（对照 `06_rulings/*` 有 t07/t07b）⇒ "
             "包被独立提交/手改时与来源脱钩**不可见**；`05_layer_sequence.txt` 由冻结 SPEC 派生，**亦无派生一致性牙齿**。",
             "- **处置**：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.9** ——",
             "  ① 纯谓词 `copy_parity()`（缺件 fail-closed）+ 牙齿 **t15**（`04_impedance` 两副本与来源**逐字节一致**）/ "
             "**t15b**（判据灵敏度：同 True、异 False、缺件 False）；",
             "  ② 牙齿 **t16**（`05_layer_sequence.txt` == `layer_sequence(spec)` **重算**）/ **t16b**（扰动 SPEC stackup 角色 ⇒ 重算必不同）；",
             "  ③ 包记录增 `declared_refs.impedance_copy_parity` 与 `declared_refs.layer_sequence_sha16`。",
             "  ④ **如实说明**：`05_layer_sequence.txt` **不**在 ORDER_NOTES §1/§2 声明为随单件 ⇒ 本项只做**包内自洽**绑定，"
             "**不**改变下单提交口径；`ORDER_NOTES.md` **逐字节不变**。",
             f"- **登记簿**：+2（`co175:G-1/G-2`，全 CLOSED；{_rc48['total']} 项 / OPEN {_rc48['OPEN']}）。",
             "",
             "> **R-CO175-1**：交付包内凡**副本类**件（不限 `06_rulings`）须与来源**逐字节**绑定的**牙齿**；凡**派生类**件须与 "
             "来源**重算**一致。缺件一律 fail-closed；仅「在包内」**不成立**。",
             "> **R-CO175-2**（复现序，取代 R-CO174-2；步骤集新增 co175）：规范复现序 = `" + _ord175 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows48 = [("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.9 / t15/t15b + t16/t16b；29 牙齿）",
                K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("工具 `p3_v57_co175_package_parity_binding.py`",
                K2 / "tools/p3_v57_co175_package_parity_binding.py"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-169.3 / 44 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("包记录 `m13_v57_co146_jlc_fab_package.json`（CO146-PKG.9）",
                STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               ("下单备注 `L5/jlc_package/ORDER_NOTES.md`（**逐字节不变**）", L5 / "jlc_package" / "ORDER_NOTES.md"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc48['total']} 项 / OPEN {_rc48['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows48:
        if pth.exists():
            sec48.append(f"| {label} | `{s16(pth)}` |")
    sec48.append("")
    body48 = "\n".join(sec48)
    if MARK48 in txt:
        txt = re.sub(re.escape(MARK48) + r"[\s\S]*?(?=\n## |\Z)", body48, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body48
    txt = txt.replace("W3 Boundary **v2.19**", "W3 Boundary **v2.20**")
    # ── §49 CO-176（闸自检强制 + 引证可核验性） ───────────────────────────────
    MARK49 = "## 49. CO-176"
    _rc49 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord176 = ("co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → "
               "co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → "
               "co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
               "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → "
               "co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → "
               "co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → "
               "co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → "
               "co171_order_notes_record_figures → co172_rev19_co166_co171_review → co173_co172_findings_disposition → "
               "co174_step_artifact_attribution → co175_package_parity_binding → co176_gate_selfcheck_evidence → "
               "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
               "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → "
               "co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → "
               "co106_reference_plane_gate → co146_boundary_append")
    sec49 = [MARK49 + "（**L2 自裁 · 闸自检强制 + 引证可核验性**）", "",
             "- **G-1（medium）**：白名单步只核 rc/无 Traceback/记录新鲜/verdict，**不核该步 `teeth`** ⇒ 白名单步（本工程唯一 = "
             "`co146_jlc_dfm_gate`）的**自检崩坏被「预期 FAIL」掩盖**、收敛照过（CO-163「自检盲区」同族）。",
             "  **处置**：`p3_v57_co164_order_runner.py` 升 **CO-169.4** —— `EXPECTED_NONZERO.teeth_path` + 纯函数 "
             "`teeth_all_true()`（bool / 含 `ok` 的 dict；空/形状不明 ⇒ None fail-closed）+ `record_json_path()`；"
             "`allowlist_decision()` 判 **`expected_step_teeth_failed`** ⇒ 停机；静态齿 **t14**。",
             "- **G-2（medium）**：JLC 能力表 `note` 声称「逐条引用原文」，实测**10/24 非原文**（2 条**静默删改**无省略标记）"
             "⇒ DFM 判定（记录**随单进包**）的限值依据**不可独立核验**且声明失实（CO-171 同族）。",
             "  **处置**：`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.3** —— 每条增 **`anchor`**（抓取件**原文子串**，"
             "24/24 实测命中）+ `capability_citation_checks()` + 牙齿 **t04**（覆盖/非空/逐条原文/实测非原文集==声明集/"
             "理由齐备/原文数下限）/ **t05**（灵敏度）；`note` **订正**；`citation` 块（n_verbatim 14/24 + 理由）；"
             "capability 记录升 **CO146-CAP.1**。",
             f"- **登记簿**：+2（`co176:G-1/G-2`，全 CLOSED；{_rc49['total']} 项 / OPEN {_rc49['OPEN']}）。",
             "",
             "> **R-CO176-1**：白名单步的 rc≠0 **只豁免 verdict**、**不豁免自检** —— 该步记录内 `teeth` 须**机判全 True**；"
             "不可判（缺字段/形状不明）一律 **fail-closed**。",
             "> **R-CO176-2**：记录内**引证**须逐条绑定来源**原文锚点**（机判）；**非原文**引证须**显式标注**并给理由"
             "（禁静默删改/改写）；记录**不得**声称超出实际核验能力的引证口径。",
             "> **R-CO176-3**（复现序，取代 R-CO175-2；步骤集新增 co176）：规范复现序 = `" + _ord176 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows49 = [("工具 `p3_v57_co164_order_runner.py`（CO-169.4 / 白名单自检强制 + t14；45 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.3 / 引证锚点 t04/t05）",
                K2 / "tools/p3_v57_co146_jlc_dfm_gate.py"),
               ("工具 `p3_v57_co176_gate_selfcheck_evidence.py`",
                K2 / "tools/p3_v57_co176_gate_selfcheck_evidence.py"),
               ("能力表 `m13_v57_co146_jlc8_capability.json`（CO146-CAP.1 / 引证锚点）",
                STEP2 / "m13_v57_co146_jlc8_capability.json"),
               ("DFM 闸记录 `m13_v57_co146_jlc_dfm_gate.json`（DFM.3）", STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc49['total']} 项 / OPEN {_rc49['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows49:
        if pth.exists():
            sec49.append(f"| {label} | `{s16(pth)}` |")
    sec49.append("")
    body49 = "\n".join(sec49)
    if MARK49 in txt:
        txt = re.sub(re.escape(MARK49) + r"[\s\S]*?(?=\n## |\Z)", body49, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body49
    txt = txt.replace("W3 Boundary **v2.20**", "W3 Boundary **v2.21**")
    # ── §50 CO-177（能力表值的原文抽取绑定） ─────────────────────────────────
    MARK50 = "## 50. CO-177"
    _rc50 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord177 = ("co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → "
               "co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → "
               "co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
               "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → "
               "co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → "
               "co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → "
               "co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → "
               "co171_order_notes_record_figures → co172_rev19_co166_co171_review → co173_co172_findings_disposition → "
               "co174_step_artifact_attribution → co175_package_parity_binding → co176_gate_selfcheck_evidence → "
               "co177_capability_value_binding → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → "
               "co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → "
               "co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → "
               "co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append")
    sec50 = [MARK50 + "（**L2 自裁 · 引证可核验性续**）", "",
             "- **问题（CO-176 G-2 残余）**：CO-176 只绑**引证 anchor**；能力表的**数值/文本主张**（`value`/`min`/`max`/`allowed`…）"
             "仍是**手录** ⇒ 手录值与抓取件脱钩（如 0.09 误录为 0.10）时 anchor 仍命中、**不可检出**"
             "（DFM 判定随单进包，其限值依据仍不完全可核验）。",
             "- **处置**：`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.4** ——",
             "  ① `CAPABILITY_VALUE_BIND`：每条 `[(正则, [期望值…])]` 或字面量，**24/24 覆盖、29 个捕获组**；",
             "  ② 纯函数 `_val_eq()`（数值按 float 比较）/ `capability_value_bind_checks()`；",
             "  ③ 牙齿 **t06**（覆盖/非空/字面量存在/正则匹配/捕获组数一致且**逐值相等**/捕获组总数下限 25）/ "
             "**t07**（灵敏度：改期望值即判不通过）；",
             "  ④ capability 记录升 **CO146-CAP.2** + `value_bind` 块；人读卡/打印补 T6/T7。",
             f"- **登记簿**：+1（`co177:G-1`，CLOSED；{_rc50['total']} 项 / OPEN {_rc50['OPEN']}）。",
             "",
             "> **R-CO177-1**：记录内**工程值主张**须**可由来源原文抽取**得到（正则捕获 ↔ 声明值，逐值机判）；"
             "仅绑 anchor（引证）**不成立**。绑定为人工编写者须**如实登记**（能力页改版后须人工复核）。",
             "> **R-CO177-2**（复现序，取代 R-CO176-3；步骤集新增 co177）：规范复现序 = `" + _ord177 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2 + R-CO177-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows50 = [("工具 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.4 / 值绑定 t06/t07）",
                K2 / "tools/p3_v57_co146_jlc_dfm_gate.py"),
               ("工具 `p3_v57_co177_capability_value_binding.py`",
                K2 / "tools/p3_v57_co177_capability_value_binding.py"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-169.4 / 46 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("能力表 `m13_v57_co146_jlc8_capability.json`（CO146-CAP.2 / 值绑定）",
                STEP2 / "m13_v57_co146_jlc8_capability.json"),
               ("DFM 闸记录 `m13_v57_co146_jlc_dfm_gate.json`（DFM.4 / 7 牙齿）",
                STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc50['total']} 项 / OPEN {_rc50['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows50:
        if pth.exists():
            sec50.append(f"| {label} | `{s16(pth)}` |")
    sec50.append("")
    body50 = "\n".join(sec50)
    if MARK50 in txt:
        txt = re.sub(re.escape(MARK50) + r"[\s\S]*?(?=\n## |\Z)", body50, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body50
    txt = txt.replace("W3 Boundary **v2.21**", "W3 Boundary **v2.22**")
    # ── §51 CO-178（DFM 逐项限值须由能力表派生） ─────────────────────────────
    MARK51 = "## 51. CO-178"
    _rc51 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord178 = ("co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → "
               "co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → "
               "co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
               "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → "
               "co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → "
               "co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → "
               "co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → "
               "co171_order_notes_record_figures → co172_rev19_co166_co171_review → co173_co172_findings_disposition → "
               "co174_step_artifact_attribution → co175_package_parity_binding → co176_gate_selfcheck_evidence → "
               "co177_capability_value_binding → co178_drc_item_limit_derivation → co124_input_selfcheck_gate → "
               "co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → co120_provenance_pin_gate → "
               "co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → co81_project_rules_gate → "
               "co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → co106_reference_plane_gate → "
               "co146_boundary_append")
    sec51 = [MARK51 + "（**L2 自裁 · 记录派生数字绑定续**）", "",
             "- **问题（查漏实测）**：DFM 闸 `_items()` 的逐项判定表内嵌**硬编码派生值** —— 板尺寸下限 `≥3×3mm`/`3.0`、"
             "阻抗控制层集 `(4,6,…,20,32)`、最小线宽 `3.5mil`、环宽 `单边 ≥0.075mm`、表面处理 `6 层及以上`、"
             "最小过孔孔壁文本 `≥0.15mm` 而**判据实为 ≥0.2mm**（文本 ≠ 强制限）⇒ 能力表（其值已由 CO-177 绑到抓取件）"
             "与**判定表文本**脱钩。",
             "- **处置**：`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.5** ——",
             "  ① `_items(m, asd, jlcrun, j=None)` 可注入能力表；硬编码一律由 `JLC8`（+ `MIL_MM`）派生"
             "（下限取 `board_min_mm`、层集解析 `impedance_control_layers.value`、mil 由 `MIL_MM` 换算、"
             "单边环宽取 `via_annular_note.value/2`、HASL 层数解析 `surface_finish.quote`、孔壁文本明示判定口径）；",
             "  ② `ITEM_DERIVATION_CASES`（**13 情形**）+ 纯函数 `item_limit_derivation_checks()` + 牙齿 **t08**"
             "（**成分级**：扰动能力表字段 ⇒ 该项 `jlc_limit` 须**含由扰动值派生的具体成分串**，且**基线不含该串**）。",
             "     **自测加严（如实记录）**：t08 首版仅查「文本是否变化」⇒ **部分硬编码**（把 `3.5mil` 写死而 mm 段仍派生）"
             "**可逃逸**（实测发现）；改为成分级断言 + 基线否定后，该回归必被击穿（同一变异复测 ⇒ 停机）。",
             f"- **登记簿**：+1（`co178:G-1`，CLOSED；{_rc51['total']} 项 / OPEN {_rc51['OPEN']}）。",
             "",
             "> **R-CO178-1**：判定表/备注内的**限值文本**须与**判据同源**且由来源记录**派生**（禁止内嵌硬编码派生值）；"
             "派生性须有**扰动证明**（扰动来源 ⇒ 文本必变）。",
             "> **R-CO178-2**（复现序，取代 R-CO177-2；步骤集新增 co178）：规范复现序 = `" + _ord178 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows51 = [("工具 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.5 / 限值派生 t08）",
                K2 / "tools/p3_v57_co146_jlc_dfm_gate.py"),
               ("工具 `p3_v57_co178_drc_item_limit_derivation.py`",
                K2 / "tools/p3_v57_co178_drc_item_limit_derivation.py"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-169.4 / 47 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("DFM 闸记录 `m13_v57_co146_jlc_dfm_gate.json`（DFM.5 / 8 牙齿）",
                STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc51['total']} 项 / OPEN {_rc51['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows51:
        if pth.exists():
            sec51.append(f"| {label} | `{s16(pth)}` |")
    sec51.append("")
    body51 = "\n".join(sec51)
    if MARK51 in txt:
        txt = re.sub(re.escape(MARK51) + r"[\s\S]*?(?=\n## |\Z)", body51, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body51
    txt = txt.replace("W3 Boundary **v2.22**", "W3 Boundary **v2.23**")
    # ── §52 CO-179（灵敏度牙齿系统性加严） ───────────────────────────────────
    MARK52 = "## 52. CO-179"
    _rc52 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord179 = ("co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → "
               "co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → "
               "co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
               "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → "
               "co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → "
               "co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → "
               "co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → "
               "co171_order_notes_record_figures → co172_rev19_co166_co171_review → co173_co172_findings_disposition → "
               "co174_step_artifact_attribution → co175_package_parity_binding → co176_gate_selfcheck_evidence → "
               "co177_capability_value_binding → co178_drc_item_limit_derivation → co179_sensitivity_teeth_hardening → "
               "co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → co77_closure_declaration_sweep → "
               "co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → co78_layer_role_drift_gate → "
               "co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → co98_reachability_status_report → "
               "co106_reference_plane_gate → co146_boundary_append")
    sec52 = [MARK52 + "（**L2 自裁 · 灵敏度牙齿系统性加严**）", "",
             "- **G-1（medium）弱判据**：`t07b` 比较**两个不同文件**（`sha256(包内副本) != sha256(ORDER_NOTES.md)`）⇒ 恒真式，"
             "**不检验 parity 判据本身**；`t10b` 只证 `sha16(JP) != 声明 pin`（pin 非自身），**不检验 pin 判据**能否拒绝错误 pin。",
             "  **处置**：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.10** —— parity/pin 判据**函数化**"
             "（`packaged_parity_checks()` / `instruction_pin_ok()`），灵敏度牙齿改为**同件近失**证明"
             "（来源做「同长单字节翻转」临时件 / pin 做「单 hex 位翻转」）；**变异实测**：把 `copy_parity` 改为恒真 ⇒ "
             "**t07b 与 t15b 双双击穿**（rc=1）。",
             "- **G-2（low）不点名**：九处灵敏度牙齿用 `not all(...)`（不点名须翻转项）⇒ 若目标项被写死而扰动偶发翻转他项，"
             "旧形仍判通过（CO-178 教训同族）。**处置**：九处改**成分级点名**（t09b→`zdiff`；t11b→`outer_copper`；"
             "t11d→`geometry_matches_binding`；t12b→`drc_as_designed_total`；t12c→`impedance_spread_pct`；"
             "t12d→`via_census_F.Cu→In2.Cu`；t12e→`mask_gap_mm`；t12f→`thermal_Tj_best_worst`；"
             "t12g→`jlc_min_track_width_mil`；t12h→`rule_copper_edge_clearance`，逐项**实测**确认该键翻转）。",
             f"- **登记簿**：+2（`co179:G-1/G-2`，全 CLOSED；{_rc52['total']} 项 / OPEN {_rc52['OPEN']}）。",
             "",
             "> **R-CO179-1**：凡「灵敏度/负控」牙齿须对**同一被判对象**做**近失扰动**并断言判据**翻转**；"
             "禁「比较两个不同对象」「非自身」等恒真式弱判据；判据须**函数化**以便真件与近失共用同一实现。",
             "> **R-CO179-2**：灵敏度牙齿须**点名**须翻转的检查项（成分级）；不得仅用 `not all(...)`。",
             "> **R-CO179-3**（复现序，取代 R-CO178-2；步骤集新增 co179）：规范复现序 = `" + _ord179 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2 "
             "+ R-CO177-1 + R-CO178-1 + R-CO179-1/2）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows52 = [("工具 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.10 / 近失 + 点名加严；29 牙齿）",
                K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("工具 `p3_v57_co179_sensitivity_teeth_hardening.py`",
                K2 / "tools/p3_v57_co179_sensitivity_teeth_hardening.py"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-169.4 / 48 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("包记录 `m13_v57_co146_jlc_fab_package.json`（CO146-PKG.10）",
                STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc52['total']} 项 / OPEN {_rc52['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows52:
        if pth.exists():
            sec52.append(f"| {label} | `{s16(pth)}` |")
    sec52.append("")
    body52 = "\n".join(sec52)
    if MARK52 in txt:
        txt = re.sub(re.escape(MARK52) + r"[\s\S]*?(?=\n## |\Z)", body52, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body52
    txt = txt.replace("W3 Boundary **v2.23**", "W3 Boundary **v2.24**")
    # ── §53 CO-180（牙齿判决完整性） ─────────────────────────────────────────
    MARK53 = "## 53. CO-180"
    _rc53 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord180 = ("co146_impedance_table → co146_pm_eval → co146_ledger_add → co153_k9_domain_coverage → "
               "co148_u6_datasheet_inputs → co148_thermal_ruling → co149_thermal_mitigation_derive → co147_l2_ruling → "
               "co146_jlc_dfm_gate → co146_jlc_fab_package → co152_findings_disposition → co155_co154_findings_disposition → "
               "co156_co154_open_disposition → co157_gate_hardening_3 → co158_l5_packet_selfcontained → "
               "co159_rev19_co156_co157_co158_review → co160_co159_findings_disposition → co161_gap_hardening_4 → "
               "co162_verdict_binding → co163_binding_to_order_notes → co166_rev19_co159_co165_review → "
               "co167_co166_findings_disposition → co168_register_consistency → co169_step_output_oracle → co170_stackup_binding → "
               "co171_order_notes_record_figures → co172_rev19_co166_co171_review → co173_co172_findings_disposition → "
               "co174_step_artifact_attribution → co175_package_parity_binding → co176_gate_selfcheck_evidence → "
               "co177_capability_value_binding → co178_drc_item_limit_derivation → co179_sensitivity_teeth_hardening → "
               "co180_teeth_judgment_integrity → co124_input_selfcheck_gate → co150_k9_domain_gate → co146_boundary_append → "
               "co77_closure_declaration_sweep → co120_provenance_pin_gate → co135_review_hygiene → co136_gate_hygiene → "
               "co78_layer_role_drift_gate → co81_project_rules_gate → co84_dru_domain_gate → co95_in4_reachability → "
               "co98_reachability_status_report → co106_reference_plane_gate → co146_boundary_append")
    sec53 = [MARK53 + "（**L2 自裁 · 牙齿判决完整性**）", "",
             "- **G-1（medium）**：复现序只对**白名单步**强制记录 `teeth` 全 True（CO-176）；其余**含 `teeth` 的 15+ 步**"
             "（impedance_table / pm_eval / co147 / co148 / co124 / co150 / co77 / co120 / co136 / co95 / co98 / co106 / fab 包…）"
             "的**自检只记不判** ⇒ 自检崩坏时收敛照过。**处置**：`p3_v57_co164_order_runner.py` 升 **CO-169.5** —— "
             "纯函数 `step_declared_teeth(step)`（自 **CO-174 的 `STEP_ARTIFACTS`** 派生；含 `teeth` 者须全 True，"
             "无 ⇒ None，未全 True/形状不明 ⇒ False fail-closed）+ `allowlist_decision()` 非白名单分支 **`step_teeth_failed`** "
             "+ 静态齿 **t15**（含现状普查）。",
             "- **G-2（medium）**：`co106` —— ① `teeth_ok` 在**前 3 齿**后即结算 ⇒ 其后 4 齿（`baseline_pin_binding` / "
             "`fail_open_closed` / `verdict_positive_control` / `carrier_exemption_declared_only`）**记录在案但不参与判决**；"
             "② 聚合键 `teeth_ok` **混入 `teeth`**；③ 两项 `checks`（`C_realized_corroboration` / `D_acceptance_matrix_coverage`）"
             "`ok` **恒真**（记录冒充判据）。**处置**：**CO-106.5** —— 聚合移至全部齿后、聚合键移出、加不变量齿 "
             "`teeth_are_bool_only`、修 `hard` 引用顺序；C/D 标 **`judging: False`** 并自 `checks_ok` 显式排除"
             "（**行为不变**：verdict 仍 PASS；键保留以兼容 co110）。",
             "- **G-3（low）**：`co78` 的 `teeth` 为**散文串**（冒充牙齿）⇒ **CO-78.3**：归真齿 dict + 散文移 `teeth_note`。",
             f"- **登记簿**：+3（`co180:G-1/G-2/G-3`，全 CLOSED；{_rc53['total']} 项 / OPEN {_rc53['OPEN']}）。",
             "",
             "> **R-CO180-1**：记录暴露的自检牙齿**一律参与判决**（不限白名单步）；判据依**声明产物**派生（CO-174），"
             "不可判一律 fail-closed。",
             "> **R-CO180-2**：`teeth` 字段须为**布尔牙齿 dict**（散文移 `teeth_note`）；**全部自检须参与本记录判决折算**（禁提前结算/漏折）；"
             "判据项与记录项须以 `judging` 标记区分，记录项不得自 `checks_ok` 折算。",
             "> **R-CO180-3**（复现序，取代 R-CO179-3；步骤集新增 co180）：规范复现序 = `" + _ord180 + "`，**循环至 sha 稳定**"
             "（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2 "
             "+ R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows53 = [("工具 `p3_v57_co164_order_runner.py`（CO-181.1 / 声明产物牙齿纳入判决 + t15/t16；49 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co106_reference_plane_gate.py`（CO-106.5 / 判决完整性）",
                K2 / "tools/p3_v57_co106_reference_plane_gate.py"),
               ("工具 `p3_v57_co78_layer_role_drift_gate.py`（CO-78.3 / teeth 归真齿 dict）",
                K2 / "tools/p3_v57_co78_layer_role_drift_gate.py"),
               ("工具 `p3_v57_co180_teeth_judgment_integrity.py`",
                K2 / "tools/p3_v57_co180_teeth_judgment_integrity.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc53['total']} 项 / OPEN {_rc53['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows53:
        if pth.exists():
            sec53.append(f"| {label} | `{s16(pth)}` |")
    sec53.append("")
    body53 = "\n".join(sec53)
    if MARK53 in txt:
        txt = re.sub(re.escape(MARK53) + r"[\s\S]*?(?=\n## |\Z)", body53, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body53
    # ── §54 CO-181（非执行者对抗复评 CO-166..CO-180 + 判决完整性续） ──────────
    MARK54 = "## 54. CO-181"
    _rc54 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec54 = [MARK54 + "（**非执行者对抗复评 + L2 自裁处置 · 判决完整性续**）", "",
             "- **复评方**：context 归零的续接会话（满足 handoff-z46 §5「另一会话，禁自评」）；对象钉 `6bf482d`"
             "（`git show` 内存重放，结论不随后续修复漂移）。方法：正控 **V0..V9**（独立重算）+ 负控 **P1..P8**"
             "（内存注入、零落盘、零坐标搜索）。verdict **PASS_WITH_FINDINGS**｜findings **5**（F-1..F-5）。",
             "- **F-1（medium）·弱/恒真牙齿**：CO-180 G-1 已将声明齿纳入判决，但被纳入的牙齿有**非判别齿** —— "
             "`co146_pm_eval` t01 代数恒真、t02 **字面 `True`**、t03 `bool(非空 dict)` 近恒真（5 齿中 3 齿永不翻转）；"
             "`co98` `integrity_detects_miscount` = `(not A) or (not B)`（A/B 互斥）**恒真** ⇒ +1 注入检测未真正实现。"
             "**处置**：`co146_pm_eval` 升 **CO148-PM.3**（齿判据**函数化** + 近失负控必翻转）；"
             "`co98` 升 **CO-98.3**（判别式 `integrity(rows) and not integrity(rows+1)`）。",
             "- **F-2（medium）·不可判 fail-open**：`step_declared_teeth` 对**不可解析**声明 json 静默跳过 ⇒ None（不判），"
             "违 R-CO180-1「不可判一律 fail-closed」。**处置**：runner 升 **CO-181.1** —— 声明 json 缺失/不可解析/非 dict ⇒ **False**。",
             "- **F-3（low）·判据自指**：仅要求「现有齿全 True」无齿集下界 ⇒ **静默删齿/改名**可规避。"
             "**处置**：runner 增 **`EXPECTED_TEETH`**（20 件声明齿件的齿名有序集 pin）+ 静态齿 **t16**"
             "（覆盖一致 + 内存桩件负控：pin 命中⇒True；齿集漂移/不可解析/`teeth_ok` 冒充⇒False）。",
             "- **F-4（low）·漏扫**：规范序步 `co81`/`co84` 自检以 `teeth_ok` 单标量暴露、无 `teeth` 布尔齿 dict ⇒ "
             "不参与 R-CO180-1 判决（CO-180 G-3 只扫了 co78）。**处置**：`co81` 升 **CO-81.3** / `co84` 升 **CO-84.3**"
             "（归真齿 dict，`teeth_ok` 自真齿聚合）；runner 另加「`teeth_ok` 冒充齿 ⇒ False」守卫。",
             "- **F-5（low）·结构性残余**：**固有一轮 pin 滞后**（= 既有 `co180:G-4`）复现 —— 复评方实测：**未变更态**"
             "2 轮收敛且 **182/182 件逐字节幂等**；**upstream 记录变更后首轮**在 `co135_review_hygiene` 停机（`unexpected_nonzero`），"
             "重跑即收敛（本轮实测：abort → 3 轮收敛）。**如实登记为残余**（消除 = 受控 warm-up 轮 / co135 显式接受滞后 + 齿证明，下轮候选）。",
             f"- **登记簿**：+4（`co181:F-1..F-4`，全 CLOSED；{_rc54['total']} 项 / OPEN {_rc54['OPEN']}）。"
             "F-5 为既有 `co180:G-4` 残余复现，不重复登记。",
             "",
             "> **R-CO181-1**：被纳入判决的牙齿须为**可翻转判据**（函数化 + 近失/负控**必翻转**）；"
             "恒真式 / 字面 `True` / 恒 `True` 记录冒充一律视为缺陷（CO-179 R-CO179-1 的**牙齿质量面**）。",
             "> **R-CO181-2**：`step_declared_teeth` 判据**不得自指** —— 齿集须命中 `EXPECTED_TEETH` pin；"
             "声明 json 缺失/不可解析/非 dict、或以 `teeth_ok` 冒充齿，一律 **fail-closed**。",
             "> **R-CO181-3**（复现序，取代 R-CO180-3；**步骤集不变 49 步**，co181 为非执行者复评不入执行序）："
             "规范复现序 = `" + _ord180 + "`，**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 "
             "+ R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows54 = [("复评工具 `p3_v57_co181_rev19_co166_co180_review.py`（只读 as-found + 内存注入；V10/P8）",
                K2 / "tools/p3_v57_co181_rev19_co166_co180_review.py"),
               ("复评记录 `m13_v57_co181_rev19_co166_co180_review.json`",
                STEP2 / "m13_v57_co181_rev19_co166_co180_review.json"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-181.1 / fail-closed + EXPECTED_TEETH pin + t16；49 步）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co146_pm_eval.py`（CO148-PM.3 / 去恒真齿）",
                K2 / "tools/p3_v57_co146_pm_eval.py"),
               ("工具 `p3_v57_co98_reachability_status_report.py`（CO-98.3 / 判别式齿）",
                K2 / "tools/p3_v57_co98_reachability_status_report.py"),
               ("工具 `p3_v57_co81_project_rules_gate.py`（CO-81.3 / 归真齿 dict）",
                K2 / "tools/p3_v57_co81_project_rules_gate.py"),
               ("工具 `p3_v57_co84_dru_domain_gate.py`（CO-84.3 / 归真齿 dict）",
                K2 / "tools/p3_v57_co84_dru_domain_gate.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc54['total']} 项 / OPEN {_rc54['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows54:
        if pth.exists():
            sec54.append(f"| {label} | `{s16(pth)}` |")
    sec54.append("")
    body54 = "\n".join(sec54)
    if MARK54 in txt:
        txt = re.sub(re.escape(MARK54) + r"[\s\S]*?(?=\n## |\Z)", body54, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body54
    # ── §55 CO-182（结构性消除「固有一轮 pin 滞后」= co180:G-4） ────────────
    MARK55 = "## 55. CO-182"
    _rc55 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord182 = _ord180.replace("co120_provenance_pin_gate → co135_review_hygiene",
                              "co120_provenance_pin_gate → co146_boundary_append → co135_review_hygiene")
    sec55 = [MARK55 + "（**L2 自裁 · 复现序结构重排：消除一轮 pin 滞后**）", "",
             "- **G-1（medium）·固有一轮 pin 滞后（= 既有 `co180:G-4`）根因机判化**：boundary 由 "
             "`co146_boundary_append`（序内 idx 37）刷新，但其后 `co77`/`co120` **仍改写被 boundary 引用的记录**；"
             "`co135`（idx 41）读 boundary 时 co120 的 pin 已**瞬时陈旧** ⇒ `V3 citation_scan_clean=False` ⇒ rc=1 ⇒ **首轮停机**"
             "（须人工重跑）。复评/复核方**受控瞬态复现**：把 `co120` 记录回滚为 as-found（`8469fb63b19664c0`）⇒ "
             "旧序**迭代 1 即停 `co135` / `unexpected_nonzero`**（与 handoff-z46 开篇「已知特性」一致）。",
             "- **处置（纯重排，不引入容忍、不掩盖）**：在 `co120_provenance_pin_gate` 与 `co135_review_hygiene` 之间**插入**"
             " `co146_boundary_append`，使**每个 boundary citation 扫描步紧跟刷新步** —— "
             "序内出现 **50 次**（步集 distinct 不变；`co146_boundary_append` 出现 3 次）；"
             "runner 增声明 `BOUNDARY_SCAN_GUARDED`/`BOUNDARY_REFRESH_STEP` + 静态齿 **t17**（受保护步须 i>0 且 `ORDER[i-1]` = 刷新步）。",
             "- **对照实测**：同一瞬态（co120 回滚）下**旧序** abort@co135；**新序**（CO-182.1）**单次调用即收敛**"
             "（rc=0；见 R-CO182-2），不再需要「重跑」。",
             f"- **登记簿**：+1（`co182:G-1`，CLOSED；{_rc55['total']} 项 / OPEN {_rc55['OPEN']}）。",
             "",
             "> **R-CO182-1**：凡**扫描 boundary citation 的步**（`co77`/`co135`）须**紧跟** `co146_boundary_append`；"
             "t17 机判。**禁**以「容忍一轮滞后」「放宽扫描判据」代替重排（禁静默让步）。",
             "> **R-CO182-2**（复现序，取代 R-CO181-3；**步集 distinct 不变，序内出现 50 次**）：规范复现序 = `" + _ord182 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows55 = [("工具 `p3_v57_co164_order_runner.py`（CO-182.1 / boundary 扫描步紧跟刷新步 + t17；序内 50 次）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc55['total']} 项 / OPEN {_rc55['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows55:
        if pth.exists():
            sec55.append(f"| {label} | `{s16(pth)}` |")
    sec55.append("")
    body55 = "\n".join(sec55)
    if MARK55 in txt:
        txt = re.sub(re.escape(MARK55) + r"[\s\S]*?(?=\n## |\Z)", body55, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body55
    # ── §56 CO-183（全域审计机判化：牙齿卫生棘轮 + 残余裁定） ──────────────
    MARK56 = "## 56. CO-183"
    _rc56 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord183 = _ord182          # 步集/序列不变（50 次）
    sec56 = [MARK56 + "（**L2 自裁 · 审计机判化 + 残余裁定**）", "",
             "- **G-1（low）·审计无全域棘轮**：牙齿卫生（常量齿 / 提前结算 / 记录冒充判据）此前仅在 CO-180/CO-181 逐件人审；"
             "**新增工具或改齿**可再引入同类病灶而不被发现。**处置**：runner 升 **CO-183.1** —— "
             "纯函数 `teeth_hygiene_scan()`（**AST、只读**）检测 ① 常量齿（值式为纯字面量）② 提前结算"
             "（`all/any(teeth…)` 聚合后仍 `teeth[k]=…` 加齿）；静态齿 **t18**（合成正控/负控 + "
             "「聚合的是**他件** teeth」假阳排除 + 现行 **19 工具 / 182 齿 / 0 违规** + 齿数下限 ≥100）。",
             "- **本轮全域机械审计（证据）**：对全部 20 件声明齿件所属 19 个工具做 AST 扫描 ⇒ **0 违规**；"
             "并逐件复核「记录冒充判据」：`co124` 的 `\"ok\": True` 位于**合成负控电池**内（非判据）、"
             "`co106` 两项已标 `judging: False` 并从 `checks_ok` 显式排除 ⇒ **无新增病灶**。",
             "- **残余裁定 1（`co174` 共享件归因）·有据延后**：彻底闭合须为 **26 个共享件步**各写**步本地标记件**"
             "（改动覆盖每一步的写路径）。threat = **并发写者**误判 `did_work`；现行运行模式为**单写者序**，"
             "且残余已由 `SHARED_ARTIFACT_RESIDUAL` + 齿 **t13c** 机判（防静默遗忘）⇒ 收益/回归面不成比例，"
             "**裁定延后**；闭合法与规模已勘定在案，**触发条件 = 出现并发写者误判事件**。",
             "- **残余裁定 2（`co177` 值绑定为人工正则）·已足够约束**：绑定式**自带上下文原文**"
             "（如 `Min\\. Via hole size/diameter (0\\.15)mm / 0\\.25mm`），并有 t04（锚点须原文子串）+ "
             "t06（逐值相等）+ t07（灵敏度）三重判据 ⇒ **静默错值不可达**（声明值必须由原文抽出且等于原文数字）。"
             "剩余风险 = 同锚短语在页面多处出现时取**首匹配**，登记为**可接受残余**。",
             f"- **登记簿**：+1（`co183:G-1`，CLOSED；{_rc56['total']} 项 / OPEN {_rc56['OPEN']}）。",
             "",
             "> **R-CO183-1**：牙齿卫生须**机判化**（t18：常量齿 / 提前结算）；审计判据须**自证**"
             "（合成正/负控 + 假阳排除用例），禁以一次性人审代替棘轮。",
             "> **R-CO183-2**：`co174` 共享件归因残余**有据延后**（闭合法 = 26 步步本地标记件；触发 = 并发写者误判事件）；"
             "既有 `SHARED_ARTIFACT_RESIDUAL` + t13c 机判不得移除。",
             "> **R-CO183-3**：`co177` 值绑定残余**判定可接受**（绑定式自带上下文 + t04/t06/t07 三重判据 ⇒ 静默错值不可达）；"
             "若出现「同锚多处取首匹配」引发的事实偏差，须重开。",
             "> **R-CO183-4**（复现序，取代 R-CO182-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord183 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 + R-CO183-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows56 = [("工具 `p3_v57_co164_order_runner.py`（CO-183.1 / 牙齿卫生棘轮 t18；序内 50 次）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc56['total']} 项 / OPEN {_rc56['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows56:
        if pth.exists():
            sec56.append(f"| {label} | `{s16(pth)}` |")
    sec56.append("")
    body56 = "\n".join(sec56)
    if MARK56 in txt:
        txt = re.sub(re.escape(MARK56) + r"[\s\S]*?(?=\n## |\Z)", body56, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body56
    # ── §57 CO-184（能力表值绑定的上下文约束：机判闭合 CO-177 残余） ──────────
    MARK57 = "## 57. CO-184"
    _rc57 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord184 = _ord183          # 步集/序列不变（50 次）
    sec57 = [MARK57 + "（**L2 自裁 · 值绑定上下文约束**）", "",
             "- **G-1（low）·上下文无约束**：`capability_value_bind_checks()` 用 `re.search(pat, page_text)` **全页首匹配** ⇒ "
             "若某条锚短语在抓取件**多处出现**，其值可被绑定到**远处置同值数字**，而 t06（逐值相等）仍过 —— "
             "声明值确实等于「某处」原文数字，但**非该条上下文**（CO-177/`co183:G-3` 残余的具体化）。",
             "- **实测（本件证据）**：现行 24 条锚点在抓取件 `m13_v57_co146_jlc_capability_source.html` 中**均唯一出现**"
             "（`anchor_occ=1`），且全部值绑定匹配距锚点 **≤281 字符** ⇒ 现值**无事实偏差**，但判据本身**无上下文约束**。",
             "- **处置**：`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.6** —— `capability_value_bind_checks()` 增 "
             "`anchors` 参数与两判据：① **`anchor_localizes_uniquely`**（锚点须在抓取件**唯一**出现，否则 fail-closed）；"
             "② **`value_within_anchor_window`**（每条值绑定匹配须落在锚点定位处 **±400 字符**内）；两判据折入 **t06**，"
             "并加灵敏度齿 **t07b**（合成正/负控：唯一+邻近⇒True；锚点重复⇒判不唯一；值远置⇒判越窗）。DFM 闸 **9 齿**。",
             "- **结论**：`co183:G-3` 的「人工正则上下文风险」由**机判闭合**（不再依赖人审裁定）。",
             f"- **登记簿**：+1（`co184:G-1`，CLOSED；{_rc57['total']} 项 / OPEN {_rc57['OPEN']}）。",
             "",
             "> **R-CO184-1**：能力表**值绑定**须**上下文受约束**（锚点唯一定位 + 值在锚点邻域内）；判据须配"
             "**合成正/负控**（唯一+邻近 / 重复锚 / 远置值）。禁以「全页首匹配」充当上下文绑定。",
             "> **R-CO184-2**（复现序，取代 R-CO183-4；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord184 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows57 = [("工具 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.6 / 锚点唯一 + 值邻域 + t07b；9 齿）",
                K2 / "tools/p3_v57_co146_jlc_dfm_gate.py"),
               ("工具 `p3_v57_co164_order_runner.py`（CO-183.1 / EXPECTED_TEETH 含 DFM 9 齿；序内 50 次）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("DFM 闸记录 `m13_v57_co146_jlc_dfm_gate.json`（DFM.6 / 9 齿 / verdict FAIL 预期）",
                STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc57['total']} 项 / OPEN {_rc57['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows57:
        if pth.exists():
            sec57.append(f"| {label} | `{s16(pth)}` |")
    sec57.append("")
    body57 = "\n".join(sec57)
    if MARK57 in txt:
        txt = re.sub(re.escape(MARK57) + r"[\s\S]*?(?=\n## |\Z)", body57, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body57
    # ── §58 CO-185（复评步 rc↔verdict 耦合 + 非 PASS 类别显式化） ─────────────
    MARK58 = "## 58. CO-185"
    _rc58 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord185 = _ord184          # 步集/序列不变（50 次）
    sec58 = [MARK58 + "（**L2 自裁 · 退出码语义完整性**）", "",
             "- **G-1（medium）·复评步 rc 不反映 verdict**：`co159`/`co166`/`co172` 三个非执行者复评步**恒 `return 0`**"
             "（CO-159 F-11 的「退出码须反映 verdict」只落到闸，漏了复评步）⇒ 其复评结论若为 FAIL / REJECT，"
             "规范序仍判**收敛**（假通过方向）。**处置**：三件改 "
             "`return 0 if verdict in (\"PASS\", \"PASS_WITH_FINDINGS\") else 1`（与 `co135`/`co136` 同口径；"
             "现行三件均 PASS_WITH_FINDINGS，行为不变）。",
             "- **G-2（low）·「非 PASS 但 rc==0」类别静默**：`co146_pm_eval` 的热结论 verdict=**FAIL**（U6 热超限，"
             "属**已登记结论** co148）而 rc=0 —— 该类别（步自身通过、记录承载已登记缺陷）此前**无显式声明**，"
             "审阅者易误判为漏洞，且**新增同类步不会被截**。**处置**：runner 升 **CO-185.1** —— 增 "
             "`PASS_VERDICTS`（通过档）+ `DECLARED_NONPASS_OK`（**显式声明**：`why` + `register` + `key_path`）"
             "+ 纯判据 `nonpass_decision()` + 运行时停机类 **`undeclared_nonpass_verdict`** + 静态齿 **t19**"
             "（白名单/声明集**互斥**、依据齐备、合成正负控、现状全序零未声明）。",
             f"- **登记簿**：+2（`co185:G-1`/`co185:G-2`，全 CLOSED；{_rc58['total']} 项 / OPEN {_rc58['OPEN']}）。",
             "",
             "> **R-CO185-1**：**复评/结论步**的退出码须反映其 `verdict`（`PASS`/`PASS_WITH_FINDINGS` 为通过档）；"
             "禁恒 `return 0`。",
             "> **R-CO185-2**：「**非 PASS 但 rc==0**」须在 `DECLARED_NONPASS_OK` **显式声明**（须给 `why` + 登记依据 `register`）；"
             "未声明 ⇒ 停机（`undeclared_nonpass_verdict`）；t19 机判（含合成正负控）。",
             "> **R-CO185-3**（复现序，取代 R-CO184-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord185 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows58 = [("工具 `p3_v57_co164_order_runner.py`（CO-185.1 / PASS_VERDICTS + DECLARED_NONPASS_OK + nonpass_decision + t19）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co159_rev19_co156_co157_co158_review.py`（rc↔verdict）",
                K2 / "tools/p3_v57_co159_rev19_co156_co157_co158_review.py"),
               ("工具 `p3_v57_co166_rev19_co159_co165_review.py`（rc↔verdict）",
                K2 / "tools/p3_v57_co166_rev19_co159_co165_review.py"),
               ("工具 `p3_v57_co172_rev19_co166_co171_review.py`（rc↔verdict）",
                K2 / "tools/p3_v57_co172_rev19_co166_co171_review.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc58['total']} 项 / OPEN {_rc58['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows58:
        if pth.exists():
            sec58.append(f"| {label} | `{s16(pth)}` |")
    sec58.append("")
    body58 = "\n".join(sec58)
    if MARK58 in txt:
        txt = re.sub(re.escape(MARK58) + r"[\s\S]*?(?=\n## |\Z)", body58, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body58
    # ── §59 CO-186（受控集补全：规范序 md 卡片产物） ─────────────────────────
    MARK59 = "## 59. CO-186"
    _rc59 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord186 = _ord185          # 步集/序列不变（50 次）
    sec59 = [MARK59 + "（**L2 自裁 · 受控集覆盖完备性**）", "",
             "- **G-1（medium）·受控集漏 md 产物**：R-CO165 要求受控 sha 覆盖**全部产物**，但规范序实际写出的 "
             "**13 件 md 卡片**（`impedance_table`/`pm_eval`/`jlc_dfm_gate`/`CO124`/`CO135`/`CO136`/`CO150`/`CO159`/`CO166`/`CO172` 卡 + "
             "`L2_RULING_via_channel_and_interpair_domain_v1`/`L2_RULING_u6_thermal_v1`/`L2_RULING_u6_thermal_mitigation_v1`）"
             "**不在 `watch_paths()`** ⇒ 既不入收敛 sha、亦无 `did_work` 归因、也不产生 `stray` 证据 ⇒ 某步**静默停写/写坏卡片**仍判「收敛」"
             "（假通过方向）。**实测**：全序写出 **14 件 md/txt**，其中仅 boundary 在受控集。",
             "- **处置**：runner 升 **CO-186.1** —— ① 新增 `ORDER_MD_PRODUCTS`（**15 件**：13 新 + boundary + `ORDER_NOTES.md`，由实测 mtime 钉定）；"
             "② `watch_paths()` 纳入；③ 各产出步 `STEP_ARTIFACTS` **步本地声明**其 md（`did_work` 归因回到步本地）；"
             "④ 静态齿 **t20**（写上下文扫描 `md_write_scan()`：pin 步集 == 扫描步集、名集相等、pin ⊆ 受控集、件存在、步本地声明、"
             "合成正负控[写上下文必抽 / 只读引用不误报]）。",
             f"- **登记簿**：+1（`co186:G-1`，CLOSED；{_rc59['total']} 项 / OPEN {_rc59['OPEN']}）。",
             "",
             "> **R-CO186-1**：规范序各步**写出的全部产物**（含 md 卡片）须入 `watch_paths()` 并**步本地声明**；"
             "新增产物须先入 `ORDER_MD_PRODUCTS`（t20 机判），禁「产物在受控集外」。",
             "> **R-CO186-2**（复现序，取代 R-CO185-3；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord186 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows59 = [("工具 `p3_v57_co164_order_runner.py`（CO-186.1 / `ORDER_MD_PRODUCTS` + 受控集补全 + t20）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc59['total']} 项 / OPEN {_rc59['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows59:
        if pth.exists():
            sec59.append(f"| {label} | `{s16(pth)}` |")
    sec59.append("")
    body59 = "\n".join(sec59)
    if MARK59 in txt:
        txt = re.sub(re.escape(MARK59) + r"[\s\S]*?(?=\n## |\Z)", body59, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body59
    txt = txt.replace("W3 Boundary **v2.30**", "W3 Boundary **v2.31**")
    txt = txt.replace("W3 Boundary **v2.29**", "W3 Boundary **v2.30**")
    txt = txt.replace("W3 Boundary **v2.28**", "W3 Boundary **v2.29**")
    txt = txt.replace("W3 Boundary **v2.27**", "W3 Boundary **v2.28**")
    txt = txt.replace("W3 Boundary **v2.26**", "W3 Boundary **v2.27**")
    txt = txt.replace("W3 Boundary **v2.25**", "W3 Boundary **v2.26**")
    txt = txt.replace("W3 Boundary **v2.24**", "W3 Boundary **v2.25**")
    # ── §60 CO-187（非执行者对抗复评 CO-181..CO-186 + L2 自裁处置） ──────────
    MARK60 = "## 60. CO-187"
    _rc60 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord187 = _ord186          # 步集/序列不变（50 次）
    sec60 = [MARK60 + "（**非执行者对抗复评 CO-181..CO-186 + L2 自裁处置**）", "",
             "- **复评方**：context 归零的续接会话（满足 handoff-z50 §6「另一会话，禁自评」）；对象钉 `4c581c7`"
             "（`git show` 内存重放 ⇒ 结论**不随后续修复漂移**）。方法：正控 **V1..V6**（独立复算）+ 负控 **P1..P6**"
             "（内存注入、零落盘、零坐标搜索）。verdict **PASS_WITH_FINDINGS**｜findings **3**（F-1..F-3，全 low）。",
             "- **六件成立（无 medium+）**：V1 齿集 pin + fail-closed（不可解析/漂移/`teeth_ok` 冒充 ⇒ False）；"
             "V2 扫描步紧跟刷新步 **且** 刷新步做 **pin 再对齐**（`CITE.sub` + `s16(hit)` ⇒ 单调用收敛机制）；"
             "V3 卫生棘轮零违规 + 逐工具齿数 ≥ pin；V4 24 锚点唯一定位、值距 ≤281 字符 ≤ 400 窗口；"
             "V5 非 PASS 显式 + 复评步 rc↔verdict；V6 md 产物 ∈ pin ∪ 豁免。",
             "- **F-1（low）·棘轮容器形态漏计**：as-found `teeth_hygiene_scan()` 只认裸 `teeth` 下标/内联 dict ⇒ **别名容器下标**"
             "（`tooth[k]=…`；实测 co81 5 齿仅计 2）、`AnnAssign`、`dict(...)`、`.update({...})`、`.setdefault(k,v)`、"
             "字面恒真式（`1==1`）**一律漏计**（以这些形态加入常量齿不被 t18 截）。**处置**：runner 升 **CO-187.1** —— "
             "容器形态全覆盖 + t18 **逐工具齿数下限**（`n_teeth ≥ pin` 齿数，漏计即停机）+ 六类形态合成正控。",
             "- **F-2（low）·md 扫描形态漏计**：as-found `md_write_scan()` 仅认 `write_text` ⇒ `open(...,'w')` / `shutil.copy*` "
             "目的 `.md` 产物不在 pin、t20 亦不截（R-CO186-1 静默违反；实测 fab 包 `04_impedance/impedance_table.md` 副本不被旧扫描见）。"
             "**处置**：扩至 `write_text`/`write_bytes` + 写模式 `open` + `copy` 目的；新增 `ORDER_MD_PRODUCT_EXEMPT`"
             "（显式豁免 + 绑定**实存**补偿牙齿 `t15_impedance_copy_parity`）+ t20 加固。",
             "- **F-3（low）·读取者全集无机判**：`BOUNDARY_SCAN_GUARDED` 为手工枚举 ⇒ 新增读取/扫描 boundary 的步可静默绕开 t17。"
             "**处置**：新增 `BOUNDARY_READ_DECLARED`（co146_boundary_append / co166 / co172）+ `boundary_read_scan()` + 静态齿 **t21**"
             "（读取者集 == 扫描步 ∪ 声明；互斥；合成正负控）。",
             f"- **登记簿**：+3（`co187:F-1..F-3`，全 CLOSED；**{_rc60['total']} 项 / OPEN {_rc60['OPEN']}**）。",
             "- **实测**：`--check` **t01..t21 全 True（23 项）**；注入 co81 别名常量齿 ⇒ t18=False；"
             "注入 co124 写模式 open 写入 ⇒ t20=False（负控实测、已还原）。",
             "",
             "> **R-CO187-1**：牙齿卫生棘轮须覆盖**全部容器形态**（别名/AnnAssign/dict/update/setdefault/纯字面量表达式），"
             "并设**逐工具齿数下限**（漏计即停机，禁「静默少扫」）。",
             "> **R-CO187-2**：md 产物扫描须覆盖**全部写/拷形态**（write_text/write_bytes/写模式 open/copy 目的）；"
             "受控集外的 md 产物须入 `ORDER_MD_PRODUCT_EXEMPT` 并**绑定实存补偿牙齿**（t20）。",
             "> **R-CO187-3**：boundary **读取者全集**须机判（t21）：扫描步 ⇒ 紧跟刷新；非扫描步 ⇒ 入 `BOUNDARY_READ_DECLARED`。",
             "> **R-CO187-4**（复现序，取代 R-CO186-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord187 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows60 = [("工具 `p3_v57_co164_order_runner.py`（CO-187.1 / t18 齿数下限 + t20 全写形态 + t21 读取者全集）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("复评工具 `p3_v57_co187_rev19_co181_co186_review.py`",
                K2 / "tools/p3_v57_co187_rev19_co181_co186_review.py"),
               ("复评记录 `m13_v57_co187_rev19_co181_co186_review.json`",
                STEP2 / "m13_v57_co187_rev19_co181_co186_review.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc60['total']} 项 / OPEN {_rc60['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows60:
        if pth.exists():
            sec60.append(f"| {label} | `{s16(pth)}` |")
    sec60.append("")
    body60 = "\n".join(sec60)
    if MARK60 in txt:
        txt = re.sub(re.escape(MARK60) + r"[\s\S]*?(?=\n## |\Z)", body60, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body60
    txt = txt.replace("W3 Boundary **v2.31**", "W3 Boundary **v2.32**")
    txt = txt.replace("W3 Boundary **v2.30**", "W3 Boundary **v2.31**")
    # ── §61 CO-188（L2 自裁 · 越界写 fail-closed：声明↔实现绑定续） ──────────
    MARK61 = "## 61. CO-188"
    _rc61 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord188 = _ord187          # 步集/序列不变（50 次）
    sec61 = [MARK61 + "（**L2 自裁 · 越界写 fail-closed：声明↔实现绑定续**）", "",
             "- **G-1（medium）·越界写只记证据不判**：规范序步骤对**其未声明**的受控件写（= 写他步专属件，或本步**漏声明**）"
             "只记入 `stray_changed` 证据、**不参与判决** ⇒ **确定性**越界写（每轮写同内容）**不破 sha 收敛**、且 `did_work` "
             "由本步声明件决定仍 True ⇒ 该件变更**无人归因**、可**静默通过**。这是 CO-174/CO-172 F-7 的**反方向**残余："
             "CO-174 只解决「他步写**本步**件被误判 `did_work`」，未解决「**本步写他步件**无人判」。",
             "- **实测（本件证据）**：现行规范序 run（sha `87223c46e457ed51`）逐轮 `stray_changed` **全空** ⇒ 加 fail-closed "
             "对现基线零冲击；受控注入复现：向首步 `co146_impedance_table` 注入对 `m13_v57_co78_layer_role_drift_gate.json` 的写 "
             "⇒ runner **首步即停** `class=stray_write`（rc=1），已还原。",
             "- **处置**：runner 升 **CO-188.1** —— ① `STRAY_WRITE_ALLOWED`（**显式**例外表，当前为空；新增须 `why`+`paths`，"
             "且不得与该步声明件重叠）；② 纯判据 `stray_decision()`；③ 运行时：凡 `stray` 命中例外外之受控件 ⇒ 停机类 "
             "**`stray_write`**（对白名单步亦生效）；④ 静态齿 **t22**（合成正负控：空⇒ok / 越界⇒stray_write / 例外内⇒ok / "
             "部分越界⇒stray_write；例外表完备性）。",
             f"- **登记簿**：+1（`co188:G-1`，CLOSED；**{_rc61['total']} 项 / OPEN {_rc61['OPEN']}**）。",
             "",
             "> **R-CO188-1**：步骤**只可写**其 `STEP_ARTIFACTS` 声明件；对任何**未声明**受控件的写 ⇒ 运行时 `stray_write` 停机"
             "（禁「只记 stray 证据」）；例外须入 `STRAY_WRITE_ALLOWED`（显式理由），t22 机判。",
             "> **R-CO188-2**（复现序，取代 R-CO187-4；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord188 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows61 = [("工具 `p3_v57_co164_order_runner.py`（CO-188.1 / `stray_write` 停机类 + `STRAY_WRITE_ALLOWED` + t22）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc61['total']} 项 / OPEN {_rc61['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows61:
        if pth.exists():
            sec61.append(f"| {label} | `{s16(pth)}` |")
    sec61.append("")
    body61 = "\n".join(sec61)
    if MARK61 in txt:
        txt = re.sub(re.escape(MARK61) + r"[\s\S]*?(?=\n## |\Z)", body61, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body61
    txt = txt.replace("W3 Boundary **v2.32**", "W3 Boundary **v2.33**")
    txt = txt.replace("W3 Boundary **v2.31**", "W3 Boundary **v2.32**")
    # ── §62 CO-189（L2 自裁 · 受控集外写入可见性） ────────────────────────────
    MARK62 = "## 62. CO-189"
    _rc62 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord189 = _ord188          # 步集/序列不变（50 次）
    sec62 = [MARK62 + "（**L2 自裁 · 受控集外写入可见性**）", "",
             "- **G-1（medium）·承载根内写入不可见**：步骤在受控产物**承载根**（`pm_gate/artifacts/k2_v4`）内写"
             "**非受控件**（不在 `watch_paths()`、无豁免）时，既不入收敛 sha、也不产生 `stray` 证据（stray 只比较受控集）"
             "⇒ **完全不可见**。CO-186 只覆盖 md 卡片、CO-188 只覆盖受控集**内**越界 ⇒ R-CO186-1「各步写出的全部产物"
             "须入受控集」的**受控集外**方向仍无判据。",
             "- **实测钉定（本件证据）**：全序逐步 shadow 差分 ⇒ 仅 `co146_jlc_fab_package` 写受控集外 **32 件**"
             "（全在 `L5/jlc_package/`：Gerber 13 / Excellon 10 / 04_impedance 2 / `05_layer_sequence.txt` / 06_rulings 4）；"
             "其余 47 步 **0 件**。该 32 件由**受控 `MANIFEST.json` 的 `manifest` 键（34 件逐文件 sha256）**覆盖 ⇒ 豁免依据成立。",
             "- **处置**：runner 升 **CO-189.1** —— ① `WRITE_SHADOW_ROOT` + **stat 轻量 shadow**（mtime/ctime/size，不哈希；"
             "承载根 ~1.8k 件逐步快照，成本 +~3s）；② `WRITE_SHADOW_EXEMPT`（5 前缀，各带 `why` + `covered_by`）；"
             "③ 纯判据 `shadow_exempt()`/`uncontrolled_decision()`；④ 运行时停机类 **`uncontrolled_write`**（对白名单步亦生效）；"
             "⑤ 静态齿 **t23**（shadow 根 ⊇ 受控集；豁免表完备 + 正负控）。",
             f"- **登记簿**：+1（`co189:G-1`，CLOSED；**{_rc62['total']} 项 / OPEN {_rc62['OPEN']}**）。",
             "",
             "> **R-CO189-1**：步骤在承载根内的写入须**全部可见** —— 属受控集（收敛 sha/stray）或入 `WRITE_SHADOW_EXEMPT`"
             "（显式理由 + `covered_by` 受控件/牙齿）；否则运行时 `uncontrolled_write` 停机（t23 机判）。",
             "> **R-CO189-2**（复现序，取代 R-CO188-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord189 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows62 = [("工具 `p3_v57_co164_order_runner.py`（CO-189.1 / 承载根 stat shadow + `uncontrolled_write` + `WRITE_SHADOW_EXEMPT` + t23）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc62['total']} 项 / OPEN {_rc62['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows62:
        if pth.exists():
            sec62.append(f"| {label} | `{s16(pth)}` |")
    sec62.append("")
    body62 = "\n".join(sec62)
    if MARK62 in txt:
        txt = re.sub(re.escape(MARK62) + r"[\s\S]*?(?=\n## |\Z)", body62, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body62
    txt = txt.replace("W3 Boundary **v2.33**", "W3 Boundary **v2.34**")
    txt = txt.replace("W3 Boundary **v2.32**", "W3 Boundary **v2.33**")
    # ── §63 CO-190（L2 自裁 · 步骤超时 fail-closed：复现序可靠性） ────────────
    MARK63 = "## 63. CO-190"
    _rc63 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord190 = _ord189          # 步集/序列不变（50 次）
    sec63 = [MARK63 + "（**L2 自裁 · 步骤超时 fail-closed：复现序可靠性**）", "",
             "- **G-1（low）·无步骤超时**：执行器对步骤 `subprocess.run` **无 `timeout`** ⇒ 任一挂起 / 无限迭代步使 "
             "runner **永久阻塞**而非 fail-closed（违「冲突即停机」精神；「禁暴力迭代」的症状面正是长跑/挂起）；"
             "且无逐步耗时证据可判「异常长跑」。",
             "- **处置**：runner 升 **CO-190.1** —— ① `STEP_TIMEOUT_S = 300`（≫ 最慢合法步）；② `subprocess.run(timeout=)` "
             "⇒ 超时**杀子进程** + 停机类 **`step_timeout`**（对白名单步亦生效，**优先于** verdict/teeth 判据）；"
             "③ 逐步 `duration_s` / `timed_out` 证据；④ 静态齿 **t24**（超时值带 60..3600 + 正控/负控）。",
             "- **实测（本件证据）**：实现期端到端负控**抓到实现缺陷** —— 超时分支仍读未赋值的 `r.stderr` ⇒ `UnboundLocalError`"
             "（首轮负控 rc=1 但报告未写出）；已修为 `_err`。修复后负控：T=60（带内）+ 首步注入 120s 挂起 ⇒ "
             "**60.8s 后停 `class=step_timeout` / `timed_out=true`**；T=5（越带）⇒ 静态 t24 直接拒（`static_precheck_failed`），不上路。",
             f"- **登记簿**：+1（`co190:G-1`，CLOSED；**{_rc63['total']} 项 / OPEN {_rc63['OPEN']}**）。",
             "",
             "> **R-CO190-1**：规范序每一步须在 `STEP_TIMEOUT_S` 内返回；超时 ⇒ 杀子进程 + `step_timeout` 停机（禁「永久阻塞」）；"
             "逐步耗时须记录（t24 机判超时值带 + 正负控）。",
             "> **R-CO190-2**（复现序，取代 R-CO189-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord190 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows63 = [("工具 `p3_v57_co164_order_runner.py`（CO-190.1 / `STEP_TIMEOUT_S` + `step_timeout` + 逐步 `duration_s` + t24）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc63['total']} 项 / OPEN {_rc63['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows63:
        if pth.exists():
            sec63.append(f"| {label} | `{s16(pth)}` |")
    sec63.append("")
    body63 = "\n".join(sec63)
    if MARK63 in txt:
        txt = re.sub(re.escape(MARK63) + r"[\s\S]*?(?=\n## |\Z)", body63, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body63
    txt = txt.replace("W3 Boundary **v2.34**", "W3 Boundary **v2.35**")
    txt = txt.replace("W3 Boundary **v2.33**", "W3 Boundary **v2.34**")
    # ── §64 CO-191（L2 自裁 · 判定基据完备性） ────────────────────────────────
    MARK64 = "## 64. CO-191"
    _rc64 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord191 = _ord190          # 步集/序列不变（50 次）
    sec64 = [MARK64 + "（**L2 自裁 · 判定基据完备性**）", "",
             "- **G-1（low）·判定面不完备**：① `step_verdict`/`nonpass_decision` **只判首个**声明 verdict ⇒ 步骤其他声明产物"
             "（副记录 / 共享件）若含非 PASS verdict 可**静默逃逸**；② 普查 **23/48 步**「无 teeth、无 verdict」仅有 "
             "rc + `did_work` 判，其**判定基据未显式绑定**（新增此类步可静默无判 = CO-79「空真」在执行器层面的残余）。",
             "- **处置**：runner 升 **CO-191.1** —— ① `declared_verdicts()` + `all_verdicts_decision()`：**全部**声明 verdict "
             "一律判决（t19 现状 clause 同步）；② `judgment_basis()` + `JUDGMENT_DOWNSTREAM`（**显式**下游声明）+ 静态齿 **t25**"
             "（每步基据 ≠ none；下游声明须有理由且指向在序步；合成正负控）。",
             "- **实测（本件证据）**：**端到端负控（旧↔新判别）** —— 注入副声明产物 `verdict=FAIL`（precheck PASS、FAIL 于**运行期**写出）"
             "⇒ 停 `class=undeclared_nonpass_verdict`；同时实测 `step_verdict`=**PASS**（旧路径**不判**）↔ "
             "`all_verdicts_decision`=**undeclared_nonpass**（新路径判）。预写失败 verdict 则由静态 t19 更早拦下。零基线冲击"
             "（现行 3 步多 verdict 产物均为通过档，见登记簿证据）。",
             f"- **登记簿**：+1（`co191:G-1`，CLOSED；**{_rc64['total']} 项 / OPEN {_rc64['OPEN']}**）。",
             "",
             "> **R-CO191-1**：步骤判定基据须**可机判**（`teeth` / 声明产物 `verdict` / 登记簿自洽 / **显式下游** `JUDGMENT_DOWNSTREAM`）；"
             "且**全部**声明 verdict 一律判决（禁只判首个 ⇒ 隐藏非 PASS 逃逸）；t25 机判。",
             "> **R-CO191-2**（复现序，取代 R-CO190-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord191 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 + R-CO191-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows64 = [("工具 `p3_v57_co164_order_runner.py`（CO-191.1 / 全 verdict 全判 + `JUDGMENT_DOWNSTREAM` + t25）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc64['total']} 项 / OPEN {_rc64['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows64:
        if pth.exists():
            sec64.append(f"| {label} | `{s16(pth)}` |")
    sec64.append("")
    body64 = "\n".join(sec64)
    if MARK64 in txt:
        txt = re.sub(re.escape(MARK64) + r"[\s\S]*?(?=\n## |\Z)", body64, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body64
    # ── §65 CO-192（非执行者对抗复评 CO-187..CO-191 + L2 自裁处置） ────────────
    MARK65 = "## 65. CO-192"
    _rc65 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord192 = _ord190          # 步集/序列不变（50 次）
    _rev192 = STEP2 / "m13_v57_co192_rev19_co187_co191_review.json"
    sec65 = [MARK65 + "（**非执行者对抗复评 CO-187..CO-191 + L2 自裁处置**）", "",
             "- **复评方**：context 归零的续接会话（满足「复评须另一会话，禁自评」）；对象钉 `52235b5`（`git show` 内存重放 ⇒ 结论**不随处置漂移**）。"
             "方法：正控 **V1..V8**（独立复算）+ 负控 **P1..P6c**（内存注入、零落盘、零坐标搜索）。verdict **PASS_WITH_FINDINGS**｜findings **4**（F-1..F-4，全 low）。",
             "- **成立件（无 medium+）**：V1 牙齿棘轮零违规 + 逐工具齿数 ≥ pin；V2 md 产物 ∈ pin∪豁免、豁免绑实存补偿齿；"
             "V3 boundary 读取者全集 = 扫描步 ∪ 声明（互斥）；V4 越界写 fail-closed；V5 承载根 ⊇ 受控集 + 豁免完备；"
             "V6 超时 fail-closed + 子进程接线；V7 每步基据非 none + 下游声明合法；V8 冻结四源 4/4 + ORDER==boundary 序 + `--check` 全 True。",
             "- **F-1（low）·牙齿棘轮形态仍漏计**：`|=`（AugAssign）/ 嵌套下标 `rec[\"teeth\"][k]` / dict 推导 / `__setitem__` / "
             "Attribute（`self.teeth[k]`）/ 下标赋别名 一律 `n_teeth=0` ⇒ 恒真齿经这些形态加入不被 t18 截。**处置**：`teeth_hygiene_scan` "
             "容器判据改**节点形态无关** + 6 类纳扫 + t18 合成正控扩展。",
             "- **F-2（low）·md 写/拷形态仍漏计**：`Path.open(w)` / `shutil.move` / `os.replace|rename` 目的 `md_write_scan()`==[] "
             "⇒ 该类 `.md` 可落出受控集、t20 不截（实测现行 ORDER 工具 0 命中 = 潜在面）。**处置**：补 3 类 + t20 正控扩展。",
             "- **F-3（low）·boundary 读取者判据可绕过**：`D.open().read()` / `io.open(B).read()`（源内无 `read_text`/`read_bytes` 字面）判 False。"
             "**处置**：读指标补 `.read(` / `io.open(` + t21 正控扩展。",
             "- **F-4（low）·全 verdict 判决对白名单步不生效**：主循环以 `if cls == \"ok\"` 为门槛 ⇒ `expected_nonzero` 步"
             "（`co146_jlc_dfm_gate`）的**副**声明 verdict 不被运行期判决（副值 ≠ 其声明 FAIL 的非 PASS 值即逃逸），违 R-CO191-1。"
             "**处置**：`all_verdicts_gate` —— **放行档**（`ok` **与** `expected_nonzero`）一律判全 verdict + t25 正负控扩展。",
             f"- **登记簿**：+4（`co192:F-1..F-4`，全 CLOSED；**{_rc65['total']} 项 / OPEN {_rc65['OPEN']}**）。",
             "",
             "> **R-CO192-1**：静态扫描须**形态完备**（牙齿：下标/别名/AnnAssign/dict()/update/setdefault/`|=`/嵌套下标/推导/`__setitem__`/"
             "Attribute/下标赋别名；md 写：write_text/write_bytes/open(w)/`Path.open(w)`/copy*/`move`/`os.replace|rename`；boundary 读："
             "read_text/read_bytes/`.read(`/`io.open`）；且**放行档一律判全声明 verdict**（`ok` **与** `expected_nonzero`）。",
             "> **R-CO192-2**（复现序，取代 R-CO191-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord192 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows65 = [("工具 `p3_v57_co164_order_runner.py`（CO-192.1 / 扫描形态完备 + `all_verdicts_gate` + t18/t20/t21/t25 扩展）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc65['total']} 项 / OPEN {_rc65['OPEN']}）",
                L2 / "input_defect_register_v1.json"),
               ("复评件 `m13_v57_co192_rev19_co187_co191_review.json`（PASS_WITH_FINDINGS / 4）", _rev192)]
    for label, pth in _rows65:
        if pth.exists():
            sec65.append(f"| {label} | `{s16(pth)}` |")
    sec65.append("")
    body65 = "\n".join(sec65)
    if MARK65 in txt:
        txt = re.sub(re.escape(MARK65) + r"[\s\S]*?(?=\n## |\Z)", body65, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body65
    # ── §66 CO-193（L2 自裁 · 声明↔实现绑定的可执行性） ────────────────────────
    MARK66 = "## 66. CO-193"
    _rc66 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord193 = _ord190          # 步集/序列不变（50 次）
    sec66 = [MARK66 + "（**L2 自裁 · 声明↔实现绑定的可执行性**）", "",
             "- **G-1（low）·下游声明只查形状、无方向/可执行机判**：`JUDGMENT_DOWNSTREAM` 旧判据仅 `why` 非空 + `ref` 非空 list + "
             "`ref ⊆ ORDER`。实测负控：ref 改为**上游**步 `co146_impedance_table`（位 0，声明步位 37/40/49）⇒ 旧 t25 仍 True；ref 改为"
             "**不引用** boundary 的 `co136_gate_hygiene` ⇒ 旧 t25 仍 True。⇒ 任一步可被声明「由下游判」而实际**无步判它**，静默逃逸 t25。",
             "- **G-2（low）·白名单证据未本步绑定**：`record` 只须 ∈ `watch_paths()`（t09）而**不须** ∈ `STEP_ARTIFACTS[step]` ⇒ "
             "证据记录可指向**他步**产物（实测旧 t09 仍 True，步本地归因/新鲜度测错件）；`teeth_path` 只须**键存在**（t14）而不须在记录内"
             "**可解析** ⇒ 坏 key 时 `_tcand` 过滤 None 后**静默回落**到 `step_declared_teeth`（自检判据降级）。",
             "- **G-3（low）·复评件内嵌处置态 sha ⇒ 记录漂移（已闭缺陷类复发）**：CO-192 复评件 `as_found` 内嵌 `runner_current_sha16`，"
             "实测改 runner 后同命令重跑得**另一记录 sha**（`db887764c8693176` → `2e43deda4f73fd76`）；该 sha 已入 §65 pin 表 ⇒ 复跑即失配。"
             "违 CO-152 已闭规则「新记录不得再嵌下游 sha 快照」（先例 `records_snapshot_downstream_sha_causes_pin_drift`）。",
             "- **G-4（low）·守卫命名面盲区**：co120 `_is_downstream_snapshot()` 只认 `*_sha16_after` + `register/ledger` 面 ⇒ 显式现行态键"
             "（`*_current_sha16` …）漏判，使 G-3 逃逸（corpus 全扫仅此 1 处）。",
             "- **处置**：① runner 升 **CO-193.1** —— `JUDGMENT_DOWNSTREAM` 每条增 `artifact`（被judged工件 basename）；新增 "
             "`downstream_refs_after()`（多次出现**存在性**方向判据）+ `judgment_downstream_binding()`（缺件/方向错/ref 不引用工件 ⇒ fail-closed）；"
             "`artifact_readers()` 为**语法代理**（basename 字面 **或** 可 `fnmatch` 命中的 glob）；新增 `expected_nonzero_binding()`"
             "（`record` ∈ `STEP_ARTIFACTS[step]`；`teeth_path` 经 `record_json_path()` 可解析）；静态齿 **t26**（正控 + 方向/可执行/不完整/"
             "多出现/坏证据 负控）。② 复评件回归 **as-found 证据**语义（去 `runner_current_sha16`；处置态 sha 由 boundary pin 表承载），"
             "改后复评命令**幂等**（`b58a374c337d75e8`）。③ co120 升 **CO-120.6** —— 新增 `_DOWNSTREAM_LIVE_KEY_RE` + 负控/正控/对偶控"
             "（上游输入 pin 不得误报）；**残余如实登记**：键名启发式，改名仍可逃逸（触发 = 记录随复现序漂移事件）。",
             f"- **登记簿**：+4（`co193:G-1..G-4`，全 CLOSED；**{_rc66['total']} 项 / OPEN {_rc66['OPEN']}**）。",
             "- **实测（本件证据）**：修后真声明 `judgment_downstream_binding`=**ok**、`expected_nonzero_binding`=**ok**、co120.6 verdict=**PASS**"
             "（`n_snapshot_undeclared`=0）；`--check` **t01..t26 全 True（28 项）**。**实现期自捕获**：`artifact_readers` 初版按 basename 子串匹配"
             " **漏 co77**（其经 `…_v1_*.md` glob 定位最新版）⇒ 真声明被误判 `refs_not_reading_artifact`；改 glob-aware 后计入。",
             "- **注**：本件含**对既有复评件（CO-192 产物）的稳定性修正**（G-3），非对 CO-192 的复评 ⇒ CO-192 复评债**不因此清偿**。",
             "",
             "> **R-CO193-1**：`JUDGMENT_DOWNSTREAM` 下游声明须**可执行** —— 每条给被judged工件 basename，ref 须在序内**晚于**声明步"
             "（多次出现取**存在性**）且 ref 步工具**确实引用**该工件（字面或可 `fnmatch` 的 glob）；否则 fail-closed；t26 机判。",
             "> **R-CO193-2**：`EXPECTED_NONZERO` 证据须**本步绑定** —— `record` ∈ `STEP_ARTIFACTS[step]` 且 `teeth_path` 在记录内**可解析**；"
             "否则 fail-closed；t26 机判。",
             "> **R-CO193-3**：证据/复评件只钉**被评对象（as-found）**；处置态/跨件**现行** sha 一律由 boundary pin 表承载，**禁内嵌**（CO-152 规则）；"
             "复评件须**幂等**（同命令重跑逐字节相同）。",
             "> **R-CO193-4**：下游快照键的**命名面**须由 co120 判据 + 合成控覆盖（含**上游输入 pin 不得误报**对偶）；新命名形态须先入判据；"
             "键名启发式为**如实登记之残余**。",
             "> **R-CO193-5**（复现序，取代 R-CO192-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord193 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows66 = [("工具 `p3_v57_co164_order_runner.py`（CO-193.1 / 下游声明可执行 + 白名单证据本步绑定 + t26）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co120_provenance_pin_gate.py` + 记录（CO-120.6 / 现行态键判据 + 对偶控）",
                K2 / "tools/p3_v57_co120_provenance_pin_gate.py"),
               ("复评件 `m13_v57_co192_rev19_co187_co191_review.json`（去处置态 sha ⇒ as-found 幂等）",
                STEP2 / "m13_v57_co192_rev19_co187_co191_review.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc66['total']} 项 / OPEN {_rc66['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows66:
        if pth.exists():
            sec66.append(f"| {label} | `{s16(pth)}` |")
    sec66.append("")
    body66 = "\n".join(sec66)
    if MARK66 in txt:
        txt = re.sub(re.escape(MARK66) + r"[\s\S]*?(?=\n## |\Z)", body66, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body66
    # ── §67 CO-194（L2 自裁 · 基据↔判官 + 声明↔工具能力） ─────────────────────
    MARK67 = "## 67. CO-194"
    _rc67 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord194 = _ord190          # 步集/序列不变（50 次）
    sec67 = [MARK67 + "（**L2 自裁 · 基据↔判官 + 声明↔工具能力**）", "",
             "- **H-1（low，latent）·基据类别无判官绑定**：`judgment_basis()` 的 `register_consistency` 类别仅凭 `_REG ∈ STEP_ARTIFACTS[step]` "
             "认定，**未绑定任何判官**（登记簿自洽实际由 co124 机判）。实测：该分支当前**不可达** —— `judgment_basis` 分布 = "
             "{teeth:19, verdict:28, downstream:1, register_consistency:**0**}（27 个写登记簿步皆先命中 `verdict` ⇒ 死码）；且把 co124 移出 ORDER 后 "
             "`all(basis != none)` 仍 True ⇒ **无判官亦成立**。一旦该分支可达（某步只写登记簿而无 teeth/verdict），其基据即空真，"
             "违 t25「每步须有可机判基据」之目的。",
             "- **H-2（low）·白名单声明与工具能力无静态绑定**：`EXPECTED_NONZERO` 的 `verdict` 只受形状约束（非 PASS + 运行期记录一致），"
             "**不要求**该字面出现在该步**工具源**内。实测：伪造 `verdict=TOTALLY_BROKEN` / `ERROR` ⇒ 旧静态条款（t03/t07/t09/t14）**全过**"
             "（仅运行期以 `expected_step_verdict_mismatch` fail-closed ⇒ 声明面未绑定、诊断滞后到执行期）。",
             "- **处置**：runner 升 **CO-194.1** —— ① 新增 `BASIS_JUDGE_DECLARED`（每基据类别显式声明判定机制；外部判官须在序内、须**读**被judged件、"
             "且**自身有机判基据**）+ 纯函数 `basis_judge_decision()`（`register_consistency` 判官 = `co124_input_selfcheck_gate`）；② 新增 "
             "`declared_verdict_in_tool()`（声明 verdict 字面须 ∈ 该步工具源）；③ 静态齿 **t27**（正控 + 判官不在序/不读件/自身无基据/声明不完整/"
             "伪造 verdict 负控）。",
             f"- **登记簿**：+2（`co194:H-1/H-2`，全 CLOSED；**{_rc67['total']} 项 / OPEN {_rc67['OPEN']}**）。",
             "- **实测（本件证据）**：修后 `basis_judge_decision` 四类别全 **ok**、`declared_verdict_in_tool('co146_jlc_dfm_gate', FAIL)`=True"
             "（零基线冲击）；`--check` **t01..t27 全 True（29 项）**。",
             "",
             "> **R-CO194-1**：每个**基据类别**须显式声明其判定机制（`BASIS_JUDGE_DECLARED`）；外部判官须**在序内**、**读被judged件**、"
             "且**自身有机判基据**；否则 fail-closed；t27 机判。",
             "> **R-CO194-2**：`EXPECTED_NONZERO` 声明的 verdict 字面须出现在该步**工具源**（声明不得指向工具不可能产出的 verdict）；t27 机判。",
             "> **R-CO194-3**（复现序，取代 R-CO193-5；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord194 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows67 = [("工具 `p3_v57_co164_order_runner.py`（CO-194.1 / 基据↔判官 + 声明↔工具 + t27）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc67['total']} 项 / OPEN {_rc67['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows67:
        if pth.exists():
            sec67.append(f"| {label} | `{s16(pth)}` |")
    sec67.append("")
    body67 = "\n".join(sec67)
    if MARK67 in txt:
        txt = re.sub(re.escape(MARK67) + r"[\s\S]*?(?=\n## |\Z)", body67, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body67
    # ── §68 CO-195（L2 自裁 · 固定点唯一性 oracle） ──────────────────────────
    MARK68 = "## 68. CO-195"
    _rc68 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord195 = _ord190          # 步集/序列不变（50 次）
    _fx = STEP2 / "m13_v57_co195_fixpoint_uniqueness.json"
    sec68 = [MARK68 + "（**L2 自裁 · 固定点唯一性（路径无关）oracle**）", "",
             "- **I-1（low）·键名判据所欲保证的语义性质无独立闸**：co120 P5「下游快照」为**键名启发式**（`*_sha16_after` / `*_current_sha16` / "
             "register|ledger 面），其真正要防的失效模式（CO-151：按文档化序连跑两遍得**另一稳定不动点** ⇒ 提交 pin 不可复现）**无任何闸直接判**。"
             "实测**值域判据不可行**：35 条记录内嵌**受控集**未来 sha，但绝大多数是**冻结历史件 / 自身产物**的合法 pin（co16/co37/co69/co95/co98 之 record pin、"
             "各步 `doc_sha16` / `stackup_svg_sha16` / `pm_eval.sha16`）⇒ 值域判据会大面积误报，**不可机判为非法**。",
             "- **处置**：新增 `tools/p3_v57_co195_fixpoint_uniqueness_oracle.py`（**不在规范序内**）—— 直接判**语义性质**：从**扰动态**启动规范序"
             "（登记簿 `meta.counts` 注入越界值 999/OPEN 7）⇒ 要求 rc=0 + converged + `snapshot()` 复原规范 sha + 登记簿**逐字节**复原；"
             "6 牙齿 = 注入有效 / 收敛 rc=0 / 不动点复原 / 登记簿逐字节复原 / **判别力**合成控（唯一 vs 非唯一不动点模型）/"
             "**排除非空转**。"
             "工具**自我保护**：`finally` 无条件复原登记簿（绝不留在扰动态）。co120 键名判据作**廉价前置代理**保留（不倒桩），语义保证由本 oracle 承载。",
             "- **I-2（low）·oracle 记录自指 + §68 误 pin 可变件（自捕获）**：初版 oracle 的判据快照含**本记录自身** ⇒ 记录写回后自身字节即变，"
             "记录的 `sha_canon` **永不等于**其所在状态的实际 sha（实测 `2d23a14ffdc821cd` ≠ `6c282601e50911d5`）；且 §68 初版 pin 了该记录 ⇒ "
             "oracle 重跑后 `boundary_append` 以新记录 sha 重 pin ⇒ **规范序不动点随「oracle 是否刚跑」漂移**（实测 boundary `6608cd8e`→`3e5ca535`、"
             "co77 `137b4949`→`c8ffe1ce` 双件漂移）。**处置**：① oracle 判据快照**排除本记录自身**（自指防护）+ 记录声明 `snapshot_scope` + 牙齿 "
             "`t06_self_exclusion_nonvacuous`；② §68 **不 pin** 该记录（同 runner report 先例：随规范态变化的证据件不入 pin 表）。",
             f"- **登记簿**：+2（`co195:I-1` + `co195:I-2`，全 CLOSED；**{_rc68['total']} 项 / OPEN {_rc68['OPEN']}**）。",
             "- **实测（本件证据）**：`sha_canon`=`f48af2c1a41de4c6` → 注入后 `sha_perturbed`=`880d1ec8cbc27698` → 跑序后 `sha_after`=`f48af2c1a41de4c6`"
             "（**逐字节复原**、rc=0 / converged / 2 轮）。**残余如实登记**：本 oracle 只扰**一个**扰动量（登记簿 counts）⇒ 未覆盖的路径相关性"
             "（如未来新形态的自指 pin）须**扩扰动量**；触发 = 出现新的自指/链式 pin 写法。",
             "",
             "> **R-CO195-0**（I-2）：**随规范态变化的证据件不得入 pin 表**（oracle/runner 报告类）；判据快照须**排除证据件自身**（自指防护）。",
             "> **R-CO195-1**：规范序的**不动点唯一性（路径无关）**须由 `co195` oracle 直接判（扰动启动 ⇒ 收敛须复原规范态 + 逐字节复原件）；"
             "键名判据仅为**前置代理**，不得替代语义判据；新自指/链式 pin 形态须扩扰动量。",
             "> **R-CO195-2**（复现序，取代 R-CO194-3；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord195 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 + R-CO195-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    # CO-195（I-2）：记录 **不被 pin** —— 其内容随规范态（`sha_canon`/`sha_after`）变化，若入 pin 表则
    # boundary_append 会用「oracle 上次跑后的记录」重 pin ⇒ 规范序不动点随 oracle 是否刚跑而漂移
    # （实测 boundary + co77 双件漂移）。同 runner report 先例：随规范态变化的证据件一律不入 pin 表。
    _rows68 = [("工具 `p3_v57_co195_fixpoint_uniqueness_oracle.py`（扰动启动 ⇒ 复原规范态 + 7 牙齿：结算/注入/收敛/复原/逐字节/判别力/自排除）",
                K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc68['total']} 项 / OPEN {_rc68['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    _rows68_excl = [("证据件 `m13_v57_co195_fixpoint_uniqueness.json`（**不被 pin**：内容随规范态变化，同 runner report 先例）",
                     _fx)]
    for label, pth in _rows68:
        if pth.exists():
            sec68.append(f"| {label} | `{s16(pth)}` |")
    sec68.append("")
    sec68 += ["> **注（I-2）**：" + lab for lab, _ in _rows68_excl]
    sec68.append("")
    body68 = "\n".join(sec68)
    if MARK68 in txt:
        txt = re.sub(re.escape(MARK68) + r"[\s\S]*?(?=\n## |\Z)", body68, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body68
    # ── §69 CO-196（L2 自裁 · 验证循环修正 + 扩扰动量） ────────────────────────
    MARK69 = "## 69. CO-196"
    _rc69 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord196 = _ord190          # 步集/序列不变（50 次）
    _orc = K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"
    sec69 = [MARK69 + "（**L2 自裁 · 验证循环修正 + 扩扰动量**）", "",
             "- **J-1（medium）·验证循环 ⇒ 不可恢复锁死**：CO-195 的静态齿 **t28** 以 oracle **证据件的 `verdict`** 为输入，而 oracle 自身"
             "**前置「先结算」**（须规范序成功跑通），规范序的静态前置**又包含 t28** ⇒ 证据件一旦 FAIL（或损坏/缺失）即：t28 拒 ⇒ "
             "`aborted=static_precheck_failed` ⇒ oracle 无法运行 ⇒ **永久无法自愈**（须人工改记录）。**实测复现**：某次 oracle FAIL 后，"
             "`--check` t28=False、order 报 `static_precheck_failed`、oracle 连跑 **1.7s** 即 `t00_settle_converged=False`（全部案牙齿 False）。"
             "属「**验证者以被验证证据为前置**」反模式。",
             "- **J-2（low）·单扰动量覆盖面不足（触发达成）**：z60 §4 已裁定「co195 只扰一个扰动量 ⇒ 未覆盖的路径相关性须扩扰动量；"
             "触发 = 出现新的自指/链式 pin 写法」。该触发**已发生** —— CO-195 的 I-2（oracle 证据自指 + §68 误 pin 可变件）正是自指/链式 pin 实例，"
             "而单扰动量（仅登记簿 counts）无法在扰动实验内暴露该类。",
             "- **处置**：① runner 升 **CO-196.2** —— t28 改**结构性**判据 `oracle_tool_ok(path)`（**只判工具存在 + 可编译**，**不读证据件**）"
             "+ **逐分支可证伪负控**（缺件 / 语法错各一，见 J-4）；证据件 PASS 由 oracle 自身与复核清单承载。② oracle 扩为**多扰动量 3 案** —— A 登记簿 `meta.counts`；"
             "B **单个 ORDER 步自持记录**注入；C **双件同时**注入；每案独立要求「收敛 rc=0 + 目标件**逐字节**复原 + 排除自身快照复原」，"
             "**任一案失败即停**；牙齿 8 项；逐案 `finally` 无条件复原。",
             "- **J-3（low）·证据件仍含自指字段 ⇒ 非幂等（I-2 同族更深层）**：I-2 只修**判据快照**，却仍在记录里落盘 "
             "`sha_incl_self = snapshot()`（**含证据件自身**）⇒ 记录内容依赖自身字节 ⇒ **非幂等**（实测连跑 `3f1f9b37869f93ea` → `35549fe1c938139b`）；"
             "因该件不入 pin 表而不破收敛，但**证据不可复现、误导复核**。处置：移除该字段（含自身的 sha 一律不落盘），只落**布尔** `t06` 结论 ⇒ 连跑恒 `5d8f953c12dafba0`（幂等）。",
             "- **J-4（low）·t28 合成负控**恒真**（不可证伪）**（续接会话自捕获）：J-1 声称「附可证伪负控（不存在 / 语法错 ⇒ False）」，"
             "实现却是 `not oracle_tool_ok(tools/__bad_oracle__.py)` —— 该文件在任何规范态下**都不存在**（无序内步创建）⇒ 该控只**重复**"
             "「缺件 ⇒ False」分支（FileNotFoundError），**语法错分支（SyntaxError）从未被行使** ⇒ 声称的可证伪不成立。处置：新增**纯内存**判据 "
             "`src_compiles(src, name)`（`compile()`，**不触盘**），t28 改**逐返回路径**各一控：缺件 `not oracle_tool_ok(<不存在>)`、"
             "**语法错** `not src_compiles(<非法源>)`、正控 `src_compiles(<合法源>)`；`oracle_tool_ok` 复用 `src_compiles`。",
             "- **J-5（low）·处置工具注解 upsert 被存在性守卫吞掉**（续接会话自捕获）：`co196_findings_disposition.py` 以「CO-196 标记 ∈ updated_by?」"
             "为守卫追加注解 ⇒ 注解文本变更（+2 → +3）后**不重写** ⇒ `meta.updated_by` **停留在旧文本**（实测 3 条 co196 条目而注解仍称「+2」）。"
             "处置：改**可重入** upsert（trim 旧 CO-196 注解段 + append 现注解）⇒ 幂等且注解恒与 `ADD` 一致。",
             f"- **登记簿**：+5（`co196:J-1`(medium) / `J-2`,`J-3`,`J-4`,`J-5`(low)，全 CLOSED；**{_rc69['total']} 项 / OPEN {_rc69['OPEN']}**）。",
             "- **实测（本件证据）**：3 案 `injection_effective` / `order_converged` / `targets_byte_restored` / `snapshot_restored` **全 True**"
             "（`sha_canon`=`59772fb78183d518`）；修后同一 FAIL 证据件下 `--check` 全 True、order 正常跑通 ⇒ oracle **可自愈**；"
             "`--check` **t01..t28 全 True（30 项）**。证据件 `m13_v57_co195_fixpoint_uniqueness.json` 仍**不入 pin 表**（R-CO195-0）。",
             "",
             "> **R-CO196-1**（红线）：**静态闸不得以被验证证据为输入**（禁验证循环）—— `--check` 只判**结构性事实**（文件存在/可编译/集合关系）；"
             "证据件内容（verdict / sha）一律不作 `--check` 输入；否则证据 FAIL 即锁死验证链。",
             "> **R-CO196-1b**：证据/报告类工件**不得落盘任何含自身的 sha**（自指字段一律换成布尔结论），并须**逐案验证幂等**（连跑记录 sha 不变）。",
             "> **R-CO196-4**：合成正/负控须与被测判据的**每条返回路径一一对应**（缺件 / 语法错 / 类型错 各一）—— "
             "**不得以「不存在的路径」冒充某一分支**（恒真控）；且 `--check` 类静态判据须**零落盘副作用**。",
             "> **R-CO196-5**：meta 注解类 upsert 须**可重入**（先 trim 旧注解段再 append 现注解），使重复运行**幂等**且**自述恒与条目实况一致**；"
             "不得依赖「标记存在即跳过」。",
             "> **R-CO196-2**：不动点唯一性 oracle 须**多扰动量**（≥ 跨件 pin 链 + 单步自持记录 + 双件交互），逐案独立判「收敛 + 逐字节复原 + 快照复原」，"
             "任一案失败即停；新增扰动量须入 `CASES`。",
             "> **R-CO196-3**（复现序，取代 R-CO195-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord196 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 + R-CO195-0/1 + R-CO196-1/2/4/5）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows69 = [("工具 `p3_v57_co164_order_runner.py`（CO-196.2 / t28 结构性 + J-4 逐分支可控）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co195_fixpoint_uniqueness_oracle.py`（多扰动量 3 案 + 8 牙齿）", _orc),
               (f"登记簿 `input_defect_register_v1.json`（{_rc69['total']} 项 / OPEN {_rc69['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows69:
        if pth.exists():
            sec69.append(f"| {label} | `{s16(pth)}` |")
    sec69.append("")
    body69 = "\n".join(sec69)
    if MARK69 in txt:
        txt = re.sub(re.escape(MARK69) + r"[\s\S]*?(?=\n## |\Z)", body69, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body69
    # ── §70 CO-197（非执行者对抗复评 CO-192..CO-195 + L2 自裁处置） ───────────────
    MARK70 = "## 70. CO-197"
    _rc70 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    _ord197 = _ord190          # 步集/序列不变（50 次）
    sec70 = [MARK70 + "（**非执行者对抗复评 CO-192..CO-195 + L2 自裁处置**）", "",
             "- **复评方**：context 归零的续接会话（满足「复评须另一会话，禁自评」—— 本会话未参与 CO-192..CO-195 之创作）；"
             "对象钉 `5e6ddde`（CO-195 定稿件），逐件 as-found 另取 `52235b5`（CO-192）/ `3e4f747`（CO-193）/ `334ed74`（CO-194）；"
             "`git show` **内存重放** ⇒ 结论**不随后续处置漂移**。方法：正控 **V1..V8**（独立复算）+ 负控 **P1..P6c**（内存注入、"
             "**零落盘**、零坐标搜索）。verdict **PASS_WITH_FINDINGS**｜findings **2**（K-1/K-2，全 low）。",
             "- **成立件（无 medium+；CO-192..CO-195 之处置经独立复算成立）**：V1 牙齿棘轮现行零违规 + 逐工具齿数 ≥ pin + 全列形态纳扫；"
             "V2 md 产物 = pin ∪ 豁免、豁免绑实存补偿齿；V3 boundary 读取者全集 = 扫描步 ∪ 声明（互斥）；"
             "V4 放行档（`ok` **与** `expected_nonzero`）一律判**全**声明 verdict；V5 `judgment_downstream_binding` 全 ok + 方向/可执行负控；"
             "V6 `expected_nonzero_binding` 全 ok + 错件/坏键负控；V7 `basis_judge_decision` 四类别全 ok + 声明 verdict 须在**工具源**；"
             "V8 冻结四源 4/4 + ORDER==boundary 序 + `--check` 全 True + oracle 工具可编译、证据件 PASS 且 teeth 全 True、"
             "**无自指字段**（R-CO195-0 / R-CO196-1b）。负控 P1..P6c 全 True（as-found 漏 ↔ 现行抓）。",
             "- **K-1（low）·牙齿扫描漏计关键字解包形态**：`teeth_hygiene_scan` 对 `dict(**{\"t01\": True})` 与 "
             "`teeth.update(**{\"t01\": True})`（AST `keyword.arg is None`）一律 `n_teeth=0` ⇒ 经该形态加入的**恒真齿**"
             "既不被计数、亦不被 constancy 检 ⇒ t18 的「逐工具齿数下限 + 常量齿零违规」一并被绕过。R-CO192-1 列举 "
             "`dict(...)` / `.update(...)` 为受覆盖形态，其**解包子形态**未实现 ⇒ 「**全部**容器形态」为过强声明。"
             "**复评实测**：as-found `52235b5` 与 `5e6ddde` 均 `n_teeth=0`（CO-192.1 未闭合）。",
             "- **K-2（low）·md 写/拷扫描漏计同族形态**：`md_write_scan` 对 `io.open(<md>, \"w\")`、"
             "`Path(...).replace|rename(<md>)` 及**路径别名** `P = Path(...); P.replace|rename(<md>)` 一律 `==[]` ⇒ 此类 `.md` "
             "产物既不入 pin、t20 亦不截（可落出受控集）；且 `io.open` 在 **boundary 读取**侧已纳扫、**md 写**侧未覆盖（**不对称**）。"
             "**复评实测**：as-found `52235b5` 与 `5e6ddde` 均 `==[]`（CO-192.1 未闭合）。",
             "- **观察 O-1（不改判 verdict；已由 CO-196 登记关闭，不重复计数）**：as-found `5e6ddde` 的静态齿 t28 以 oracle "
             "**证据件 verdict** 为输入 ⇒ 与 oracle 前置「先结算」构成**验证循环**（证据 FAIL 即不可恢复锁死）；本次复评以负控 P4 "
             "**独立复现**（`oracle_record_ok` 存在于 as-found、现行只判结构性）。",
             "- **处置**：runner 升 **CO-197.1** —— ① `teeth_hygiene_scan` 补关键字**解包**形态（`dict(**{...})` / `.update(**{...})`）；"
             "② `md_write_scan` 补 `io.open(<md>, \"w\")` 与 `Path(...)`/路径别名 `.replace|rename(<md>)` 目的；"
             "t18/t20 合成控同步扩展（含 `\"a.md\".replace(\".md\",\"\")` **字符串操作不得误报**、只读 `io.open` 不得误报之**对偶负控**）。",
             "- **K-3（low，本件**实现期自捕获**）·注解 upsert 段边界**：J-5 把注解 upsert 改为「trim 旧段 + append」，"
             "而 trim 取 `updated_by[:index(标记)]`（**裁到末尾**）⇒ 其后另有 CO 追加注解时，重跑本 CO 的 disposition 会"
             "连同**他人注解段一并静默删除**（实测：co197 注解写入后再跑 co196 disposition ⇒ `；**CO-197（…）**` 整段消失，"
             "条目 `co197:K-1/K-2` 仍在）；且「裁掉再追加」会把本段**移到末尾** ⇒ 登记簿 sha 随「最后跑的是哪个 CO」而变"
             "（**顺序敏感、不可复现**）。处置：改**原位替换**（右界 = 下一 `；**CO-` 起点 / 末尾），两件同步落地。",
             f"- **登记簿**：+3（`co197:K-1`,`K-2`,`K-3`，全 low、全 CLOSED；**{_rc70['total']} 项 / OPEN {_rc70['OPEN']}**）。",
             "- **实测（本件证据）**：复评件**幂等**（连跑记录 sha 恒 `de625cb63e0df8f5`）；K-1 两形态修后 `n_teeth=1` 且报常量齿、"
             "K-2 三形态修后分别 `==[\"probe.md\"]` / `==[\"dst.md\"]` / `==[\"dst.md\"]`；**零误报核对**：现行 ORDER 全工具的 md 命中集"
             "与齿数**逐工具不变**；co196 ↔ co197 注解 upsert **交替重跑**（两种次序）⇒ 登记簿 sha **恒定**"
             "（顺序无关幂等）、两段注解保位；`--check` **t01..t28 全 True（30 项）**。",
             "",
             "> **R-CO197-1**：静态扫描器的「已列形态」须**逐子形态**落地并合成控覆盖 —— `keyword.arg is None`（`**` 解包）等"
             "子形态属必测集；漏计即停机（同族 R-CO192-1 之收严）。",
             "> **R-CO197-2**：md 写/拷形态须覆盖 **builtins / io / pathlib** 三族**及其别名**；新增形态须同时补"
             "**对偶负控**（字符串操作、只读引用**不得误报**）。",
             "> **R-CO197-4**：注解类 upsert 须**原位**改**本段**（右界 = 下一 `；**CO-` 注解起点 / 末尾）—— "
             "**禁**无界裁尾（删除他人注解）、**禁**「裁掉再追加」（移段 ⇒ 顺序敏感）；须以「交替重跑两 CO」验证"
             "**保位 + 顺序无关幂等**。",
             "> **R-CO197-3**（复现序，取代 R-CO196-3；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord197 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 + R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows70 = [("工具 `p3_v57_co164_order_runner.py`（CO-197.1 / 解包形态 + io·pathlib md 形态）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("复评件 `m13_v57_co197_rev19_co192_co195_review.json`（as-found 幂等）",
                STEP2 / "m13_v57_co197_rev19_co192_co195_review.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc70['total']} 项 / OPEN {_rc70['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows70:
        if pth.exists():
            sec70.append(f"| {label} | `{s16(pth)}` |")
    sec70.append("")
    body70 = "\n".join(sec70)
    if MARK70 in txt:
        txt = re.sub(re.escape(MARK70) + r"[\s\S]*?(?=\n## |\Z)", body70, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body70
    # ── §71 CO-198（L2 自裁 · 代理 ↔ 语义闸关系机判化） ────────────────────────────
    MARK71 = "## 71. CO-198"
    _rc71 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec71 = [MARK71 + "（**L2 自裁 · 代理 ↔ 语义闸关系机判化**）", "",
             "- **E-1（low）·代理判据 ↔ 语义闸的绑定只存在于散文、无机判**：co120 的 P5「下游快照」为**键名启发式**"
             "（廉价前置代理），其要保证的语义性质（复现序**不动点唯一/路径无关**）由 co195 oracle 承载 —— 但该「代理 ↔ 语义闸」"
             "关系**无机判**：判官工具被移除/改名、其语义齿被删、或代理自身 fail-closed 齿从 pin 表消失，**均无人发现**；"
             "残余（更名可逃逸）虽已如实登记（CO-193 G-4 / CO-195 I-1），却**无声明面强制**（可被误读为判据完备）。"
             "属「声明↔实现绑定」未收尾。",
             "- **处置**：runner 升 **CO-198.1** —— 新增 `PROXY_SEMANTIC_BINDING`（导出**残余**（不得宣称完备）+ 语义判官工具 "
             "+ **源内声明**的语义齿名 + 代理齿所在记录）+ 纯判据 `proxy_binding_decision()`（`tool_ok`/`src_has`/`proxy_teeth` "
             "可注入 ⇒ 合成控）+ 静态齿 **t29**（正控 + 缺声明/残余空/判官缺/齿名未声明/代理齿未 pin 之负控）。"
             "**只读判官源**，不读其证据件（R-CO196-1：禁验证循环）。",
             f"- **登记簿**：+1（`co198:E-1`，low，CLOSED；**{_rc71['total']} 项 / OPEN {_rc71['OPEN']}**）。",
             "- **实测（本件证据）**：修前改写/删除 co195 齿名或移除判官工具，`--check` **仍全 True**（无机判）；修后 "
             "`--check` **t01..t29 全 True（31 项）**，t29 四类负控均判 False ⇒ 判据**可证伪**且只涉结构性事实。",
             "",
             "> **R-CO198-1**：凡**代理判据**（启发式 / 近似 / 廉价前置）代替语义判据之处，须登记 `PROXY_SEMANTIC_BINDING` —— "
             "**残余显式**（禁宣称完备）+ **外部语义判官**（工具 + **源内声明**的齿名）+ 代理自身 fail-closed 齿**在 pin 表**；"
             "静态齿 **t29** 机判，否则 fail-closed。判官**证据件**一律不读（R-CO196-1）。",
             "> **R-CO198-2**（复现序，取代 R-CO197-3；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord190 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 + R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4 "
             "+ R-CO198-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows71 = [("工具 `p3_v57_co164_order_runner.py`（CO-198.1 / 代理↔语义闸绑定 + 静态齿 t29）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc71['total']} 项 / OPEN {_rc71['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows71:
        if pth.exists():
            sec71.append(f"| {label} | `{s16(pth)}` |")
    sec71.append("")
    body71 = "\n".join(sec71)
    if MARK71 in txt:
        txt = re.sub(re.escape(MARK71) + r"[\s\S]*?(?=\n## |\Z)", body71, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body71
    # ── §72 CO-199（L2 自裁 · 白名单 rc 类语义） ─────────────────────────────────
    MARK72 = "## 72. CO-199"
    _rc72 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec72 = [MARK72 + "（**L2 自裁 · 白名单 rc 类语义**）", "",
             "- **F-1（low）·白名单 rc 语义未声明**：`EXPECTED_NONZERO` 只声明 `verdict`（+ `record`/`teeth_path`），"
             "**不声明预期 rc 值** ⇒ `allowlist_decision()` 对白名单步仅判 `rc != 0` ⇒ **任何**非零退出"
             "（内部错误 / 参数错 / `sys.exit(2)` / 127）只要 verdict 相符、无 Traceback、牙齿全 True 即被放行 ⇒ "
             "**rc 语义被架空**：「因别的原因失败」与「预期判决 FAIL」不可区分（`why` 之『rc=1 即生效』为散文、无机判）。"
             "此前各次收严（CO-165/167/176/185/193/194）都在**同一 rc 值域**内，未约束**值本身**。",
             "- **处置**：runner 升 **CO-199.1** —— ① `EXPECTED_NONZERO` 每条须显式声明 `rc`（非零 int = 该判决的**规格化出口**）；"
             "② `allowlist_decision()` 增 `expected_step_rc_undeclared` / `expected_step_rc_mismatch` 两停机类；"
             "③ `expected_nonzero_binding()` 增 `rc_not_declared`（声明面完备性）；④ 静态齿 **t30**。",
             f"- **登记簿**：+1（`co199:F-1`，low，CLOSED；**{_rc72['total']} 项 / OPEN {_rc72['OPEN']}**）。",
             "- **实测（本件证据）**：修前 `allowlist_decision('co146_jlc_dfm_gate', 2|127, '', 'FAIL', True, True)` 均返回 "
             "`expected_nonzero`（与 rc=1 不可区分）；修后 rc=1 ⇒ `expected_nonzero`、rc=2/127 ⇒ `expected_step_rc_mismatch`、"
             "rc=0 ⇒ `expected_step_returned_zero`、声明缺失/为零 ⇒ `rc_not_declared`；`--check` **t01..t30 全 True（32 项）**、"
             "规范序收敛 rc=0（co146 步仍以 rc=1 放行）。",
             "",
             "> **R-CO199-1**：白名单类豁免须**逐项声明语义出口**（rc 值等）；「非零 / 非 PASS / 非空」等**笼统判据**"
             "不得充当豁免边界 —— 否则「因别的原因失败」与「预期判决」不可区分；t30 机判。",
             "> **R-CO199-2**（复现序，取代 R-CO198-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord190 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 + R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4 "
             "+ R-CO198-1 + R-CO199-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows72 = [("工具 `p3_v57_co164_order_runner.py`（CO-199.1 / 白名单 rc 类语义 + 静态齿 t30）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc72['total']} 项 / OPEN {_rc72['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows72:
        if pth.exists():
            sec72.append(f"| {label} | `{s16(pth)}` |")
    sec72.append("")
    body72 = "\n".join(sec72)
    if MARK72 in txt:
        txt = re.sub(re.escape(MARK72) + r"[\s\S]*?(?=\n## |\Z)", body72, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body72
    # ── §73 CO-200（L2 自裁 · 不动点 oracle 扩扰动量：受控 md 卡片产物） ─────────────
    MARK73 = "## 73. CO-200"
    _rc73 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec73 = [MARK73 + "（**L2 自裁 · 不动点 oracle 扩扰动量：受控 md 卡片产物**）", "",
             "- **G-1（low）·扰动实验覆盖面缺 md 卡片产物**：受控集自 CO-186 起把各步 **md 卡片产物**入 pin（`ORDER_MD_PRODUCTS`，t20 判），"
             "而 `co195` oracle 的三案（A 登记簿 `meta.counts` / B 单步自持 json 记录 / C 双件交互）**只扰 json 记录** ⇒ "
             "「步是否**真正全量重写**其 md 产物」**从未被扰动实验行使**（追加式/增量式写会在扰动态残留注入行而无人测）⇒ "
             "R-CO186-1「受控 sha 覆盖**全部**产物」在**语义层**存在覆盖面缺口（结构已 pin、语义未扰）。",
             "- **处置**：oracle 升 **CO-200** —— `CASES` 扩第 4 案 **D_md_card_product**（目标 = `co146_impedance_table` 的 md 卡片产物；"
             "注入**内容行**），与其余案同判「收敛 rc=0 + 目标件**逐字节**复原 + 排除自身快照复原」，**任一案失败即停**；"
             "牙齿 8 → **9**（`t08_D_md_restored`）；`CASES` 逐案显式 `tooth` 名（新增案不挤占既有齿名 ⇒ 保 CO-198 绑定名稳定）。",
             f"- **登记簿**：+1（`co200:G-1`，low，CLOSED；**{_rc73['total']} 项 / OPEN {_rc73['OPEN']}**）。",
             "- **实测（本件证据）**：4 案 `injection_effective` / `order_converged` / `targets_byte_restored` / `snapshot_restored` **全 True**；"
             "牙齿 **9 项全 True** / verdict **PASS** / rc=0；D 案证实该 md 产物为**全量重写**（注入行消失、逐字节复原）；"
             "`t07_no_residual_perturbation` 现覆盖 4 案全部目标件。",
             "",
             "> **R-CO200-1**：受控集每新增**产物类别**（md / 报告 / 图 / 二进制），oracle `CASES` 须同步增对应扰动量 —— "
             "否则该面只受**结构** pin、不受**语义**扰动（覆盖面 = 类别数）。",
             "> **R-CO200-2**（复现序，取代 R-CO199-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord190 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 + R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4 "
             "+ R-CO198-1 + R-CO199-1 + R-CO200-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows73 = [("工具 `p3_v57_co195_fixpoint_uniqueness_oracle.py`（CO-200 / 4 案 + 9 牙齿）",
                K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc73['total']} 项 / OPEN {_rc73['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows73:
        if pth.exists():
            sec73.append(f"| {label} | `{s16(pth)}` |")
    sec73.append("")
    body73 = "\n".join(sec73)
    if MARK73 in txt:
        txt = re.sub(re.escape(MARK73) + r"[\s\S]*?(?=\n## |\Z)", body73, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body73
    # ── §74 CO-201（L2 自裁 · 出口语义 + 豁免边界） ──────────────────────────────
    MARK74 = "## 74. CO-201"
    _rc74 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec74 = [MARK74 + "（**L2 自裁 · 出口语义 + 豁免边界**）", "",
             "- **G-1（low）·白名单出口语义靠文本子串代理**：`allowlist_decision()` 对白名单步的「崩溃」判据仅查 stderr 是否含 CPython 表头 "
             "`Traceback (most recent call last)`，**其余 stderr 内容一概不看** ⇒ 非表头形态的错误出口（`sys.exit('msg')`、库抛 SystemExit、"
             "解释器外错误）在与声明 rc 相同、记录已先落盘、verdict 与牙齿相符时**冒充「预期判决出口」**。仅 rc **值**已在 CO-199 收紧，"
             "该出口**是否伴生错误**仍无判据。",
             "- **G-2（low）·豁免前缀的段边界分支无合成控**：`shadow_exempt()` 实现正确（`rel == pre or rel.startswith(pre + '/')`），"
             "但 t23 只行使了**接受**分支 ⇒ 回归为裸 `rel.startswith(pre)`（兄弟目录 / 同前缀文件名被误豁免）时 `--check` **仍全 True**"
             "（判据该分支不可证伪）—— 违 R-CO197-1「合成控须逐分支覆盖」。",
             "- **处置**：runner 升 **CO-201.1** —— ① 白名单**预期非零出口须 stderr 全空**，新增停机类 `expected_step_error_output`"
             "（置于 `expected_step_crashed` 之后）+ 静态齿 **t31**；② t23 补段边界正/负控（子路径须豁免；`…06_rulingsX/`、"
             "`…05_layer_sequence.txtX` 不得豁免）。",
             f"- **登记簿**：+2（`co201:G-1`/`G-2`，low，CLOSED；**{_rc74['total']} 项 / OPEN {_rc74['OPEN']}**）。",
             "- **实测（本件证据）**：修前 `allowlist_decision('co146_jlc_dfm_gate', 1, 'Error: boom', 'FAIL', True, True)` ⇒ `expected_nonzero`（放行）；"
             "修后 ⇒ `expected_step_error_output`（Traceback 者 ⇒ `expected_step_crashed`；空/纯空白 ⇒ `expected_nonzero`）。"
             "**零基线冲击**：`co146_jlc_dfm_gate` stderr = **0 字节**（stdout 628 / rc=1）；规范序收敛 rc=0。",
             "",
             "> **R-CO201-1**：「预期出口」须同时绑定 **rc 值** 与 **无错误输出**（stderr 空）；新增白名单步须实测 stderr 为空并留证据。",
             "> **R-CO201-2**：字符串前缀 / 集合归属类判据须对**两种拒绝形态**（等长不同名 / 同前缀更长路径）各给负控；t31/t23 机判。",
             "> **R-CO201-3**（复现序，取代 R-CO200-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord190 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 + R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4 "
             "+ R-CO198-1 + R-CO199-1 + R-CO200-1 + R-CO201-1/2）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows74 = [("工具 `p3_v57_co164_order_runner.py`（CO-201.1 / 出口语义 + 边界负控 + 静态齿 t31）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc74['total']} 项 / OPEN {_rc74['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows74:
        if pth.exists():
            sec74.append(f"| {label} | `{s16(pth)}` |")
    sec74.append("")
    body74 = "\n".join(sec74)
    if MARK74 in txt:
        txt = re.sub(re.escape(MARK74) + r"[\s\S]*?(?=\n## |\Z)", body74, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body74
    # ── §75 CO-202（非执行者对抗复评 CO-196..CO-201 + L2 自裁处置） ──────────────
    MARK75 = "## 75. CO-202"
    _rc75 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec75 = [MARK75 + "（**非执行者对抗复评 CO-196..CO-201 + L2 自裁处置**）", "",
             "- **复评方**：context 归零之续接会话（本谱系 z60..z67 **之外** ⇒ 满足「复评须另一会话，禁自评」）；对象**逐件**钉 as-found"
             "（CO-196→`5e6ddde`/`2898392`；CO-197→`2898392`；CO-198→`c922116`；CO-199→`87148cb`；CO-200→`68e2952`/`3734a2f`；CO-201→`8a4cc3c`）；"
             "`git show` **内存重放** ⇒ 结论**不随后续处置漂移**。方法：正控 **V1..V8**（独立复算）+ 负控 **P1..P10**（内存注入、**零落盘**、零坐标搜索）。"
             "verdict **PASS_WITH_FINDINGS**｜findings **4**（L-1..L-4，全 low）；CO-196..CO-201 之处置**经独立复算成立**（V1..V6、P1..P6 全 True）。",
             "- **成立件（独立复算）**：V1（CO-196 J-1 验证循环已除 —— t28 只判**结构性事实**、`oracle_tool_ok` 不读证据件）；"
             "V2（CO-197 K-1/K-2 扫描族已补且**对偶负控**不误报）；V3（CO-198 代理↔语义闸绑定成立）；V4（CO-199 白名单 rc 类语义）；"
             "V5（CO-200 md 产物案已扩）；V6（CO-201 出口语义 + 豁免前缀**段边界**正/负控）；V7（登记簿卫生：counts 据 items 复算、OPEN 0、13 条 co196..co201 全 CLOSED）；"
             "V8（冻结四源 4/4 + `--check` 全 True + oracle PASS）。**另**：六件 disposition 于**全 720 排列**下均复现**逐字节同一**登记簿（顺序无关幂等、零落盘）。",
             "- **L-1（low）·t28 谓词级控欠覆盖**：R-CO196-4 明列「缺件 / 语法错 / 类型错 各一」，而 t28 对谓词 `oracle_tool_ok` 仅行使**缺件** + 正控；"
             "「语法错」控挂在**共享子程序** `src_compiles`（不证**传播**）、「类型错」**无控**（as-found 实测：谓词级 compile/type 控各 False，而实现正确 ⇒ 不可证伪）。",
             "- **L-2（low）·运行期新停机类无合成控**：CO-199 之 `expected_step_rc_undeclared` 在 runner 源内**仅出现 1 次**（其自身 return）⇒ 该 return 分支不可证伪"
             "（回归时被 `expected_step_rc_mismatch` 静默吸收，分类永不生效）。",
             "- **L-3（low）·「源内声明」为原文子串代理**：`proxy_binding_decision` 默认 `name in src` ⇒ 判官齿名仅见**注释/散文**即满足 R-CO198-1"
             "（实测注释串注入 ⇒ `ok`）⇒ 该「机判」判据本身是**文本代理**、非语义。",
             "- **L-4（low）·oracle 扰动量类别覆盖不足**：受控集类别 {.json,.md,**.svg**} 而 `CASES` 仅扰前二者 ⇒ `.svg`（图）产物（CO-174 入 pin）"
             "只受**结构** pin、**从未**被语义扰动行使 ⇒ 违 R-CO200-1「覆盖面 = 类别数」（谱系交接件 §4 之触发条件实已于 CO-174 达成）。",
             "- **处置**：runner 升 **CO-202.1** —— ① t28 补**谓词自身**之逐返回路径控（`_NONCOMPILE_PROBE` 存在但不可编译 / `oracle_tool_ok(None)` 类型错）；"
             "② `allowlist_decision(..., decl=)` 增**可注入声明面** + t30 控 `expected_step_rc_undeclared`；③ `proxy_binding_decision` 默认改 **AST 字面量集**"
             "（`_source_strings` ⇒ 注释/散文不满足）；④ 新增静态齿 **t32**（受控集类别 ⊆ oracle 扰动量类别）；report revision → CO-202.1。"
             "oracle 升 **CO-202** —— `CASES` 第 5 案 `E_svg_product`（目标 = 图/.svg 产物，注入内容行）+ 牙齿 9 → **10**。",
             f"- **登记簿**：+4（`co202:L-1`..`L-4`，low，CLOSED；**{_rc75['total']} 项 / OPEN {_rc75['OPEN']}**）。",
             "- **实测（本件证据）**：修前 as-found 记实（AST/内存复算，零落盘）—— t28 谓词级 compile/type 控 False；`expected_step_rc_undeclared` 计数 1；"
             "注释串注入 ⇒ `ok`；受控集类别 {.json,.md,.svg} ⊄ `CASES` 类别 {.json,.md}。修后 —— `--check` **t01..t32 全 True（34 项）**；"
             "oracle **5 案 / 10 牙齿全 True / verdict PASS / 幂等**（连跑记录 sha 恒定）；规范序收敛 rc=0、48 步 `did_work` 全 True、stray/uncontrolled 全空；"
             "复评件**幂等**（连跑记录 sha 恒定）。**残余如实登记（O-1）**：stdout 形态之错误出口未约束（触发 = 出现 stdout 错误外壳之白名单步）。",
             "",
             "> **R-CO202-1**：谓词级负控须覆盖**谓词自身**每条返回路径（含「存在但不可编译」「类型错」），不得仅控其共享子程序；t28 机判。",
             "> **R-CO202-2**：运行期新停机类（新 return 分支）须合成控覆盖（声明面可注入）；不得以「当前不可达」免控；t30 机判。",
             "> **R-CO202-3**：受控集产物**类别数** ⊆ oracle 扰动量类别数（逐类别 ≥1 案）；t32 机判（新增产物类别即须同步增扰动量）。",
             "> **R-CO202-4**：「源内声明的名称」类判据须以 **AST 字面量集**判（注释/散文不得满足）；原文子串 `in src` 禁作声明性判据；t29 机判。",
             "> **R-CO202-5**（复现序，取代 R-CO201-3；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord190 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 "
             "+ R-CO175-1 + R-CO176-1/2 + R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 "
             "+ R-CO183-1 + R-CO184-1 + R-CO185-1/2 + R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 "
             "+ R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 + R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4 "
             "+ R-CO198-1 + R-CO199-1 + R-CO200-1 + R-CO201-1/2 + R-CO202-1/2/3/4）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows75 = [("工具 `p3_v57_co164_order_runner.py`（CO-202.1 / t28 谓词级逐返回路径控 + decl 注入 + proxy AST 字面量集 + 静态齿 t32）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co195_fixpoint_uniqueness_oracle.py`（CO-202 / 5 案 + 10 牙齿：含 图（.svg）类别）",
                K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc75['total']} 项 / OPEN {_rc75['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows75:
        if pth.exists():
            sec75.append(f"| {label} | `{s16(pth)}` |")
    sec75.append("")
    body75 = "\n".join(sec75)
    if MARK75 in txt:
        txt = re.sub(re.escape(MARK75) + r"[\s\S]*?(?=\n## |\Z)", body75, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body75

    # ── §76 CO-203（L2 自裁 · 工具自声明修订号（自声明面）↔ 内容 同步） ──────────────
    _ord191 = _ord190          # 步集/序列不变（50 次）
    MARK76 = "## 76. CO-203"
    _rc76 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec76 = [MARK76 + "（**L2 自裁 · 自声明修订号（自声明面）↔ 内容 同步 + 机判齿 t33**）", "",
             "- **M-1（low）·工具自声明修订号面与内容不同步**：CO-202 处置已把 oracle 内容升为按 CO-202（`CASES` **5 案** / 牙齿 **10**），"
             "而其记录自声明 `revision` 仍 **CO-200**（`nature` 仍「4 案」、`trigger` 未述第 5 案、docstring 仍「3 案」）；"
             "runner 头部修订清单亦漏 CO-200/CO-202 ⇒ 下游读「oracle revision」者见 CO-200，"
             "会误判第 5 案（图/`.svg`）**未被覆盖** —— 即「声明↔实现」在**自声明面**之漂移（承 R-CO194-1/2）。",
             "- **处置**：① oracle 自声明面 sync（`revision` → **CO-202**、`nature` → **5 案**、`trigger` 补 CO-202（L-4）条款、docstring 五案化）；"
             "② runner 增 `TOOL_REVISION_DECLARED`（自声明修订号类工具之**权威声明**） + 纯判据 `tool_revision_bound()`（**AST** 抽取记录 dict 字面量之 `revision`；"
             "注释/散文不得满足 —— 承 R-CO202-4） + 静态齿 **t33**；runner 头部修订清单补 CO-200/CO-202/CO-203。report revision → CO-203.1。",
             f"- **登记簿**：+1（`co203:M-1`，low，CLOSED；**{_rc76['total']} 项 / OPEN {_rc76['OPEN']}**）。",
             "- **实测（本件证据）**：修前（AST 复算，零落盘）as-found `27e9fe3` 记录字面 `revision=\"CO-200\"` 而内容 5 案/10 牙齿 ⇒ "
             "`tool_revision_bound(<oracle>, rev=CO-200)` = `revision_mismatch`；修后抽取字面 `(True, 'CO-202')`、`rev=CO-202` ⇒ `ok`；"
             "注释/散文源 ⇒ `(False, None)`（判别力控）；`--check` **t01..t33 全 True（35）**；oracle 记录 `revision` = CO-202、5 案 / 10 牙齿 PASS。",
             "",
             "> **R-CO203-1**：凡工具**自声明 `revision`** 者，其内容升级须同 commit 同步**自声明面**（记录 `revision` / `nature` / `trigger` / 头部修订清单）；"
             "抽取一律以 **AST 字面量**判（注释/散文不得满足，承 R-CO202-4），新增此类工具须入 runner `TOOL_REVISION_DECLARED`；t33 机判。",
             "> **R-CO203-2**（复现序，取代 R-CO202-5；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord191 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2 "
             "+ R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 + R-CO183-1 + R-CO184-1 + R-CO185-1/2 "
             "+ R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 + R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 "
             "+ R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4 + R-CO198-1 + R-CO199-1 + R-CO200-1 + R-CO201-1/2 + R-CO202-1/2/3/4 + R-CO203-1）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows76 = [("工具 `p3_v57_co164_order_runner.py`（CO-203.1 / 自声明修订号绑定：`TOOL_REVISION_DECLARED` + `tool_revision_bound` + 静态齿 t33）",
                K2 / "tools/p3_v57_co164_order_runner.py"),
               ("工具 `p3_v57_co195_fixpoint_uniqueness_oracle.py`（CO-202 / 5 案 + 10 牙齿；自声明 `revision`=CO-202）",
                K2 / "tools/p3_v57_co195_fixpoint_uniqueness_oracle.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc76['total']} 项 / OPEN {_rc76['OPEN']}）",
                L2 / "input_defect_register_v1.json")]
    for label, pth in _rows76:
        if pth.exists():
            sec76.append(f"| {label} | `{s16(pth)}` |")
    sec76.append("")
    body76 = "\n".join(sec76)
    if MARK76 in txt:
        txt = re.sub(re.escape(MARK76) + r"[\s\S]*?(?=\n## |\Z)", body76, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body76

    # ── §77 CO-204（L2 自裁 · 打样渠道重绑 JLC 标准 = 通孔 + 背钻 + 层分配裁决 + 两闸 + U6 热 O2） ──
    MARK77 = "## 77. CO-204"
    _rc77 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec77 = [MARK77 + "（**L2 自裁 · 打样渠道重绑 JLC 标准 = 通孔 + 背钻 + 层分配变更裁决 + 两闸 + U6 热 O2 定案**）", "",
             "- **渠道重绑（同一抓取件）**：`m13_v57_co146_jlc_capability_source.html` 同页明文二者 —— blind/buried **Not supported**"
             "（only make through holes）与 **Backdrill 支持**（4–32 层 FR4 / 板厚 ≥0.8mm / D 0.2–0.5mm / W=D+0.2mm / **T≥0.15mm** / S≥0.2mm）。"
             "旧能力件 CO146-CAP.3 **漏** Backdrill 段 ⇒ 催生不存在的「JLC advanced/盲埋孔通道」（CO-147 R1）⇒ **已撤销**，能力件升 **CO146-CAP.4**。"
             "（**注**：本条「标准通道不含盲/埋孔」之定性已由 CO-206 §0 更正为「advanced 通道能做但贵」——见 §79。）",
             "- **设计事实（机判，板 `d4e81f647be7f980`）**：493 via = F→B 273 / F→In2 92 / F→In5 8 / **In2→In5 88** / In5→B 32 ⇒ 220 非通孔；"
             "In2↔In5 两端内层 ⇒ 最小残桩 **0.3664mm ≥ 0.15mm** ⇒ 标准通道不可制。",
             "- **层分配裁决（CO-204 时点；续见 §78）**：自写 proper-intersection 核（未 import 引擎）把图纸 2276 段投单层 ⇒ **1298 处相交** ⇒"
             "「逃逸层 == run 层」不可行；via1 列位 44 列 / 跨 9.55mm 中 **43** 处列距 <0.615（外层 3W）⇒「竖段全落单外层」容量不可行；"
             "候选 A′（竖段全落 B.Cu，run 仍 In5）实测 = `NOT FULLY PLACED`（**20/32 页不可落位 ⇒ 落位 8/32**）⇒ 竖段须分色于 ≥2 层。候选族 A/B/C 遴选，实施路由 = WORKER（禁暴力迭代）。",
             "- **U6 热定案 O2**：30×30 散热片 + 界面垫 1.0 + ~2m/s 风冷 ⇒ θJA_eff = 6.5+1.0+3.5 = **11.0** ⇒ 四工况 Tj 91.7 / 106.0 / 103.8 / **117.0 ℃** 全 ≤120；"
             "`L2_RULING_u6_thermal_mitigation_v2.md`（v1.0 → v2.0）。",
             "- **两闸入库（防再犯）**：**板厂能力绑定闸** `p3_v57_co204_fab_capability_binding_gate.py`（C0 能力源绑定 / C1 类别合法性 / C2 残桩 <0.15 / C3 背钻工艺限 / C4 禁盲埋孔；"
             "CO-205 补 **C5 端声明↔实现绑定**）—— **现行板 FAIL rc=1**（`inner_inner_via_class(88)` / `residual_stub_ge_0.15mm` / `blind_buried_required`；C5=True）；"
             "**散热验证闸** `p3_v57_co204_thermal_o2_freeze_and_gate.py` —— **PASS**（四工况 ≤120）。",
             "- **红线（本件工件内 verbatim，不代拟编号）**：能力闸 `redline` = 「只读判据（不改 SPEC/板/冻结四源）；零坐标搜索；能力值一律由 pinned 抓取件原文抽得。」；"
             "散热件 `redline` = 「只读输入件 + 闭式一阶计算；零坐标搜索；不改 SPEC/板/冻结四源。」；**R-CO205-1**（过孔端声明↔实现绑定，C5 机判）。",
             "- **记录面（如实登记）**：交接件 z71 §5 引「`R-CO204-1..4`」为 CO-204 之红线编号，但树内**无其规范文本**（CO-204 未落 § 即 §80 F-3 之因）；"
             "本 § 以工件 `redline` 字段原文代替编号，**不代拟未声明之条文**。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows77 = [("工具 `p3_v57_co204_fab_capability_binding_gate.py`（CO-205 版 / C0..C5）", K2 / "tools/p3_v57_co204_fab_capability_binding_gate.py"),
               ("记录 `m13_v57_co204_fab_capability_binding.json`（**FAIL rc=1；C5=True**）", STEP2 / "m13_v57_co204_fab_capability_binding.json"),
               ("工具 `p3_v57_co204_thermal_o2_freeze_and_gate.py`（U6 O2 闸）", K2 / "tools/p3_v57_co204_thermal_o2_freeze_and_gate.py"),
               ("记录 `m13_v57_co204_thermal_verification.json`（**PASS**；四工况 ≤120）", STEP2 / "m13_v57_co204_thermal_verification.json"),
               ("裁定 `L2_RULING_jlc_standard_through_backdrill_v1.md`（R1 定性已由 CO-206 §0 更正）", L2 / "L2_RULING_jlc_standard_through_backdrill_v1.md"),
               ("裁定 `L2_RULING_u6_thermal_mitigation_v2.md`（U6 O2 定案 v2.0）", L2 / "L2_RULING_u6_thermal_mitigation_v2.md"),
               ("能力件 `m13_v57_co146_jlc8_capability.json`（**CO146-CAP.4**，含 backdrill 段）", STEP2 / "m13_v57_co146_jlc8_capability.json"),
               ("证据 `m13_v57_co204l_candidate_Aprime_infeasible.json`（候选 A′ 20/32）", STEP2 / "m13_v57_co204l_candidate_Aprime_infeasible.json"),
               ("证据 `m13_v57_co204_l2_ruling.json`", STEP2 / "m13_v57_co204_l2_ruling.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc77['total']} 项 / OPEN {_rc77['OPEN']}）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows77:
        if pth.exists():
            sec77.append(f"| {label} | `{s16(pth)}` |")
    sec77.append("")
    body77 = "\n".join(sec77)
    if MARK77 in txt:
        txt = re.sub(re.escape(MARK77) + r"[\s\S]*?(?=\n## |\Z)", body77, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body77

    # ── §78 CO-205（L2 自裁 · 层分配族穷尽 + 工具缺陷 ①..④） ──
    MARK78 = "## 78. CO-205"
    _rc78 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec78 = [MARK78 + "（**L2 自裁 · 层分配重指派全族探索 + 工具缺陷 ①..④ 修复；族闭合 = 24/32（修正模型 23/32）**）", "",
             "- **族闭合（L2 可自裁空间内穷尽）**：拓扑族（A / A′ / B / C / D / E + escape=F 混合）× 桥孔 jog（方向/幅度 / x-含 y-侧移 / 条件修复）"
             "× 列分配（CARRYALL / 逐极性游标 / XMIN / 顺序）× 层参数（POL_OFF）⇒ **上限 24/32（含桥孔占位之修正模型 23/32）**。",
             "- **硬限论证（结构性）**：竖段须落内层（外层 3W=0.615 吃容量）、lane 亦须落内层（同理）、且二者须异层（否则竖段穿邻页 lane 产生真交叉）"
             "⇒ corner 必为内层↔内层 ⇒ 在 R3 过孔策略下不可制；**增内层不改变该结论**（每支跨内层孔仍须经 F/B 拆分）⇒ L2 叠层决策收益为零。"
             "剩余路径 = **L1**（球重映射/信号流向，owner）或外部工艺输入。",
             "- **候选复测（关键负结果）**：候选 A（run 维持 In5 + 竖段全 In2，`CO16_ALLI2`）= **17/32** INFEASIBLE；"
             "候选 B（run In5→B.Cu + 竖段 In2/In5 分色，`CO16_V2B`）= 端点层模型 32/32 且走完整链（L4 apply + co133 PDN ⇒ 501 via / 0 内层↔内层 / 能力闸 PASS）**但 KiCad DRC 抓出 7 shorting_items + 4 clearance** ⇒ **REJECTED**；"
             "候选 D（`CO16_VOUT`+`SPAN`）= **14/32**（F 逃逸撞 pad 场/PDN）。两闸 + 冻结四源回归：默认路径与 v9 逐页同，交付板 `d4e81f647be7f980` 逐字节未变。",
             "- **工具缺陷 ①（已修，默认关 `CO10_SPAN`/`CO16_SPAN` 透传）·过孔占用层 = 端点层**：探针以过孔**两端点层**建 mask/判据，而通孔+背钻实际占用**起止层之间全部层** ⇒ 假可行"
             "（候选 B 旧模型 32/32 ↔ 真板 KiCad DRC 7 short 为反证）；修后候选 B = **26/32**（失败面与 DRC 命中面一致）。",
             "- **工具缺陷 ②（已修）·lane 层标签漂移**（探针 In6 vs 真板 In5）⇒ 现行发射器工件构造器无法消费（KeyError）；修后发射器输出与 v9 逐页逐字段同、"
             "构造器产出与冻结图纸**逐字节同**（`60cbd331836e52b7`）。",
             "- **工具缺陷 ③（已修，opt-in `CO10_BRCOL` / 透传 `CO16_BRCOL`）`bridge_jog_direction_from_pad_order`**：桥孔 jog 方向原由 **pad 序**（BRAWAY/_BR_FLIP）或 band 固定推出；"
             "In2 逃逸带 3W=0.48<0.615 ⇒ `_band_carry=False` ⇒ 行内逃逸列序 (px,nx) 可与 pad 序相反 ⇒ P/N 桥孔 jog 指向彼此，`|vx_P-cx_N| = |s-BR_JOG|` 塌到 0.05–0.15"
             "（症状 = 候选 C 下 7/8 失败页 reason = `vv_intra`）。修后 `vv_intra` **7 → 0**，失败面全改跨页类（`vv_placed`/`vt_placed`/`vt2_placed`/`hh_intra`）。",
             "- **工具缺陷 ④（已修，opt-in `CO10_COLFIX`）`connector_column_coloring_ignores_bridge_hole_y`**：J2 区间图贪心着色（`r3_build`, EASTSPLIT=in2c）"
             "与 J3/J4 落列分离器（`_lx_separate`）之占位区间**只取 {lane_y, land_y}**，桥在 lane 行 ±BR_JOG 处另加一孔（落桥孔）落在区间之外 ⇒ 两页被着同色却在桥孔上撞"
             "（症状 = DN2/input `vv_placed` vs UP0/out_J2.P 0.316）。修后（含桥孔占位）最优 = **23/32** ⇒ **记录的 24/32 是欠预留之乐观值**；"
             "负控：把判据退化为「仅比 via y」⇒ 24 → **14/32**（同列两页竖段共线重叠）已回退。",
             "- **回归修复（CO-205s）**：`carryall_bridge_extent_leak`（CO-205r 提交 `3f32c0a` 内 `_BEXT` 未加 `_CARRYALL` 门控，静默改写 BRCOL 单用结果 24 → **16/32**）⇒ 修后 `candC+BRCOL` 恢复 **24/32** 且 `vv_intra = 0`。",
             "- **CO-205t（band 级逐极性游标 `CO10_CARRYP`）**：设计意图达成（跨页 via1 撞类 `vv_placed` **6 → 1**），但单调推进把 1 页挤出可行域 ⇒ 净 **−1**（23/32）⇒ 本族仍不过 24/32。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows78 = [("证据 `m13_v57_co205_candidate_layer_reassign.json`（候选 A/B/D 复测 + 结构引理）", STEP2 / "m13_v57_co205_candidate_layer_reassign.json"),
               ("证据 `m13_v57_co205r_bridge_joint_solve.json`（工具缺陷 ③ / 桥族上限 24/32）", STEP2 / "m13_v57_co205r_bridge_joint_solve.json"),
               ("证据 `m13_v57_co205s_connector_column_model.json`（工具缺陷 ④ + 回归修复 → 23/32）", STEP2 / "m13_v57_co205s_connector_column_model.json"),
               ("证据 `m13_v57_co205t_per_polarity_cursor.json`（逐极性游标 / 族闭合）", STEP2 / "m13_v57_co205t_per_polarity_cursor.json"),
               ("探针 `p3_v57_co10_west_fan_probe.py`（+11 只读旋钮，全默认关）", K2 / "tools/p3_v57_co10_west_fan_probe.py"),
               ("发射器 `p3_v57_co16_emit_allocation.py`（+9 旋钮透传）", K2 / "tools/p3_v57_co16_emit_allocation.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc78['total']} 项 / OPEN {_rc78['OPEN']}）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows78:
        if pth.exists():
            sec78.append(f"| {label} | `{s16(pth)}` |")
    sec78.append("")
    body78 = "\n".join(sec78)
    if MARK78 in txt:
        txt = re.sub(re.escape(MARK78) + r"[\s\S]*?(?=\n## |\Z)", body78, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body78

    # ── §79 CO-206（L2 自裁 · 工艺选型/性价比对比 常规功能 + A/B/C 定案 + 口径修正 + 取数留痕） ──
    MARK79 = "## 79. CO-206"
    _rc79 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec79 = [MARK79 + "（**L2 自裁 · 工艺选型/性价比对比 立为 ENG 常规功能（监理指令 #13）+ 打样路径 A/B/C 定案 + 口径修正 + 价格取数留痕**）", "",
             "- **定性更正（§0，最高优先级）**：撤销一切「JLC 无 HDI/盲埋孔通道」表述。准确三层 = ① **标准通道不支持**盲/埋孔"
             "（能力表原文 *\"Blind/Buried Vias Not supported … only make through holes\"*）；② **advanced 通道支持**盲/埋孔与 **HDI（激光孔）**"
             "（同页 FAQ 原文 *\"Advanced options such as blind/buried vias, HDI (laser vias), … typically require DFM review and may increase both cost and production time.\"*）"
             "⇒「做不了」不成立，正确命题 =「HDI 能做但贵，评估更便宜的路」；③ HDI **阶数/激光孔径/盲埋孔 DFM 限值/交期/加价** 本工程语料未获证 ⇒ `INPUT_REQUIRED`。",
             "- **常规功能入库**：判据件 `process_route_criteria_v1.json`（判据/参数与工具分离，换板换厂可替换、**零板级特判**）+ 执行器 "
             "`p3_v57_co206_process_route_select.py --criteria <json> [--board <pcb>]`；输出 可行性/成本/交期/性能/风险 + 推荐 + 所需输入清单；同输入 ⇒ 同输出（**幂等实测**：连跑同 sha）。"
             "**单一真源** = 复用能力闸之 census / layer_span / class_stub（防两处口径漂移）。",
             "- **设计事实（机判，板 `d4e81f647be7f980`）**：493 via / 通孔+背钻可制 **405** / 需盲/埋孔 **88**（全为 In2↔In5 两端内层 = 埋孔；层压次数下界 **3** ⇒ 等效 HDI 阶数 ≥2，指示性映射须板厂确认）。",
             "- **A/B/C 定案**：**A**（JLC advanced/HDI 盲埋孔）= `FEASIBLE_PENDING_DFM`（残桩 0 / SI 不变 / **零重派生**）；"
             "**B**（加层全通孔，如 10L）= `UNPROVEN`（充分条件 = 存在层分配使每支孔外层锚定；必要条件 = lane 须落外层，否则 corner 必为内层↔内层；实测未全落位）；"
             "**C**（盘中孔 via-in-pad）= `PARTIAL_INSUFFICIENT_ALONE`（仅可替盲孔 **132** 支，**埋孔 88 支不可替** —— 埋孔不在任何外层焊盘之下）。",
             "- **推荐**：**A 为默认打样路径**（唯一无需重派生；现行图纸即盲埋孔形态；SI 不变）；B 为报价驱动候选，可复现规则 "
             "`quote(10L std) + cost(重派生) < quote(HDI 8L) ⇒ B 否则 A`（已编码，填参后自动复算）；C 仅辅助，不与 A/B 并列。**成本/交期禁编造**（无验证来源 ⇒ 全 `INPUT_REQUIRED`，只出模型 + 所需输入清单）。",
             "- **CO-206b 口径修正**：B 路 lane 既须落外层，就须吃 **外层 3W = 0.615**；探针 `_V2B` 把 lane 置于**私有内层** In6（3W 取内层 0.48）所测 **26/32** 为**乐观值**；"
             "按外层口径复测（新增旋钮 `CO10_LANE_OUTER`）⇒ **24/32**（失败面 DN0/2/5/7 `out_MCIO` + UP0/2/4/6 `input`）⇒ B 相对 A 之吸引力进一步下降（非便宜快路，须整层重派生且可行性未证），**推荐 A 不变**。"
             "（裁定 v2 增 §2b；判据件 B 路 `measured` 双口径并列。）",
             "- **CO-206c 价格取数留痕**：试 5 端点（capabilities / pcb-hdi / pcb-price / advanced-pcb / cart quote；http 码与字节逐条留痕于判据件 `price_probe_log`）"
             "⇒ JLC 站点为 SPA，**服务端不返回价格**（报价器仅渲染 'Calculated Price $0.00' 占位）⇒ 三路 cost/lead_time **不可机取**，维持 `INPUT_REQUIRED`，须**人工报价**回填（留痕以免重复试探）。",
             "- **CO-208 口径同步补完（本 § 之 part）**：CO-206b 只改了主判据字段，`recommendation.basis[0]` 与判据件 `risk_catalog.B[0]` 仍滞留 26/32 ⇒ CO-208 补齐"
             "（执行器 **CO-206.2** / 判据件 **v1.3**）⇒ 明细见 §81 F-1 处置。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows79 = [("判据件 `process_route_criteria_v1.json`（**v1.3**）", L2 / "process_route_criteria_v1.json"),
               ("执行器 `p3_v57_co206_process_route_select.py`（**CO-206.2**）", K2 / "tools/p3_v57_co206_process_route_select.py"),
               ("证据 `m13_v57_co206_process_route_selection.json`", STEP2 / "m13_v57_co206_process_route_selection.json"),
               ("证据 `m13_v57_co206_process_route_selection.md`", STEP2 / "m13_v57_co206_process_route_selection.md"),
               ("裁定 `L2_RULING_process_route_selection_v2.md`（§0 更正 + §1 定案 + §2b 口径）", L2 / "L2_RULING_process_route_selection_v2.md"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc79['total']} 项 / OPEN {_rc79['OPEN']}）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows79:
        if pth.exists():
            sec79.append(f"| {label} | `{s16(pth)}` |")
    sec79.append("")
    body79 = "\n".join(sec79)
    if MARK79 in txt:
        txt = re.sub(re.escape(MARK79) + r"[\s\S]*?(?=\n## |\Z)", body79, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body79

    # ── §80 CO-207（非执行者对抗复评 CO-202..CO-206c） ──
    MARK80 = "## 80. CO-207"
    _rc80 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec80 = [MARK80 + "（**非执行者对抗复评 CO-202..CO-206c；as-found 钉 `add6e33`**）", "",
             "- **复评方**：context 归零之续接会话（本谱系 z60..z71 **之外** ⇒ 满足「复评须另一会话，禁自评」）；**as-found 快照 = `add6e33`**（CO-206c），"
             "一切「现行态」判定皆由该快照重放（`git show` 内存重放 + 自板 pcbnew 普查 / 自算术 / 自源 AST / 自跑工具与探针）。",
             "- **verdict = PASS_WITH_FINDINGS**｜findings **3**（F-1/F-2/F-3，全 low）｜观察 **2**（O-1 交接件齿数表述陈旧：称 25 / 实测 29；O-2「增内层不改变 24/32」之反证责任留在 B 路）。",
             "- **正控 V1..V9**：V1 独立 via 普查 = **False**、V2 散热复算 = True、V3 oracle 复现 = **False**、V4 runner `--check` + 登记簿 = **False**、V5 冻结四源 + 板 = True、"
             "V6 登记簿复算 = True、V7 判据件无编造数 = True、V8 打样包完整性 = **False**、V9 L2 族独立复现 = True（v9 默认 **32/32**；candC+BRCOL **24/32**；+COLFIX **23/32**；B 路 lane-outer **24/32**）。",
             "- **负控 P1..P8 全 True**（内存注入、零落盘）：修订号抽取 / 陈旧数探测 / § 存在性 / 编造探测 / stub 齿 / 热齿 / census 齿 / 键字面量抽取之判别力均成立。",
             "- **findings（三项；原文见复评件）**：**F-1** B 路口径修正不完整（同族引用滞留 26/32 + 自声明面滞留）；**F-2** R-CO203-1 登记条款与 t33 互斥（条款不可满足且无齿）；"
             "**F-3** CO-204..CO-206c 无 boundary §（本文件 §77..§79 之缺即其证）。处置 = §81（CO-208）。",
             "- **R-CO207-1**：复评件须钉**被评态快照**且一切「现行态」判定皆由该快照重放；禁内嵌处置态之 sha（承 R-CO193-3）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows80 = [("复评件 `m13_v57_co207_rev19_co202_co206_review.json`（机判证据）", STEP2 / "m13_v57_co207_rev19_co202_co206_review.json"),
               ("复评卡片 `m13_v57_CO207_rev19_co202_co206_review.md`（结论 + findings 表）", STEP2 / "m13_v57_CO207_rev19_co202_co206_review.md"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc80['total']} 项 / OPEN {_rc80['OPEN']}）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows80:
        if pth.exists():
            sec80.append(f"| {label} | `{s16(pth)}` |")
    sec80.append("")
    body80 = "\n".join(sec80)
    if MARK80 in txt:
        txt = re.sub(re.escape(MARK80) + r"[\s\S]*?(?=\n## |\Z)", body80, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body80

    # ── §81 CO-208（L2 自裁 · CO-207 复评 F-1..F-3 处置） ──
    MARK81 = "## 81. CO-208"
    _rc81 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec81 = [MARK81 + "（**L2 自裁 · CO-207 复评 F-1..F-3 处置：声明↔内容同步 + R-CO203-1 适用域收窄 + boundary 记录链收口**）", "",
             "- **F-1 处置（声明↔内容同步）**：① 执行器 `recommend()` 依据① 与判据件 `risk_catalog.B[0]` 之 26/32 → **24/32**（显式注明口径）；"
             "② 自声明面 sync：执行器 `revision` **CO-206.1 → CO-206.2**、判据件 **v1.2 → v1.3**（含 changelog）；"
             "③ 重生成 `m13_v57_co206_process_route_selection.{json,md}`（幂等实测：连跑同 sha）。**红线 R-CO208-1**。",
             "- **F-2 处置（R-CO203-1 适用域收窄）**：R-CO203-1 之登记义务**收窄**至「其自声明 `revision` 为**机判/记录消费面**者」——"
             "现域 = **不动点 oracle 单件**（其记录由 t28/t33 消费）；t33 之单件断言即该域之**显式不变量**。"
             "文义「凡自声明者皆须登记」不可实现（本会话 AST 复算：`tools/p3_v57_*.py` 含 `revision` dict 字面量者 **155 / 229**）⇒ 该文义作废。**红线 R-CO208-2**。",
             "- **F-3 处置（记录链收口）**：补 §77（CO-204）/ §78（CO-205 + r/s/t）/ §79（CO-206 + b/c）/ §80（CO-207）/ §81（本节 = CO-208）；boundary **v2.48 → v2.49**。**红线 R-CO208-3**。",
             "- **记录面（如实登记）**：§77 指出的 `R-CO204-1..4` 与承接 CO-206 之 `R-CO206-1` 均无树内规范文本；CO-208 **不代拟**该两族编号条文"
             "（CO-204 族以工件 `redline` 原文代替；CO-206 之「工艺可行性/成本须走判据件 + 工具、禁编造单价」义务由本节 R-CO208-1/本判据件承载）。",
             f"- **登记簿**：+3（`co207:F-1`/`F-2`/`F-3`，全 low，全 CLOSED；**{_rc81['total']} 项 / OPEN {_rc81['OPEN']}**）。",
             "- **实测（本件证据）**：修后 —— `--check` **t01..t33 全 True（35 项）**；规范序收敛 rc=0 / 2 轮（唯一非零 = co146 DFM rc=1 预期、**stderr 0 字节**）；"
             "co124 登记簿自检 PASS；oracle PASS 且幂等；能力闸 **FAIL 预期（C5=True）**；散热闸 PASS；打样包牙齿全 True；冻结四源 **4/4 MATCH**；交付板 `d4e81f647be7f980` 逐字节未变。",
             "",
             "> **R-CO208-1**（承 F-1）：**同一量多处引用者，改口径须逐处同步**；工具/判据件之自声明面（`revision`）随内容升级须**同 commit bump**；域内工具由 `tool_revision_bound`（t33）机判。",
             "> **R-CO208-2**（承 F-2，收窄 R-CO203-1）：R-CO203-1 之登记适用域 = 「其自声明 `revision` 为机判/记录消费面者」（现 = 不动点 oracle 单件）；"
             "域内新增工具时 `TOOL_REVISION_DECLARED` 与 t33 断言集须**同 commit 同源扩容**（禁单侧更新）；域外工具不适用该登记义务。",
             "> **R-CO208-3**（承 F-3）：**新 CO 收口即须落 boundary §（同一 commit）**；boundary 须自足到「冻结四源 + gate 链态可只读 boundary 得到」。",
             "> **R-CO208-4**（复现序，取代 R-CO203-2；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord190 + "`，"
             "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2 "
             "+ R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 + R-CO183-1 + R-CO184-1 + R-CO185-1/2 "
             "+ R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 + R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 "
             "+ R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4 + R-CO198-1 + R-CO199-1 + R-CO200-1 + R-CO201-1/2 + R-CO202-1/2/3/4 "
             "+ R-CO203-1 + R-CO207-1 + R-CO208-1/2/3）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows81 = [("执行器 `p3_v57_co206_process_route_select.py`（CO-206.2）", K2 / "tools/p3_v57_co206_process_route_select.py"),
               ("判据件 `process_route_criteria_v1.json`（v1.3）", L2 / "process_route_criteria_v1.json"),
               ("生成器 `p3_v57_co146_boundary_append.py`（本节写入器）", K2 / "tools/p3_v57_co146_boundary_append.py"),
               ("runner `p3_v57_co164_order_runner.py`（CO-203.1 / t33 域不变量）", K2 / "tools/p3_v57_co164_order_runner.py"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc81['total']} 项 / OPEN {_rc81['OPEN']}）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows81:
        if pth.exists():
            sec81.append(f"| {label} | `{s16(pth)}` |")
    sec81.append("")
    body81 = "\n".join(sec81)
    if MARK81 in txt:
        txt = re.sub(re.escape(MARK81) + r"[\s\S]*?(?=\n## |\Z)", body81, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body81

    # ── §82 CO-209（L2 自裁 · band 级「列 × 桥孔」联合求解形态之直接行使 ⇒ 族闭合复核） ──
    MARK82 = "## 82. CO-209"
    _rc82 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec82 = [MARK82 + "（**L2 自裁 · band 级「列 × 桥孔 x」联合求解之直接行使（族闭合复核）+ 发射器透传补齐**）", "",
             "- **缘起**：z71 §6.3 指「L2 内唯一未动自由度 = band 级联合求解器（列 + 桥孔 (x,y) 同解；确定性、禁回溯）」，"
             "且 CO-207 之观察 **O-2** 明记「族上限 ≤24/32 属**结构性论证**、未直接行使（未构造反例）」。本 CO 消除该「论证 vs 实测」缺口。",
             "- **行使形态（全部闭式：确定性、零回溯、零重试、零坐标搜索）**：逐极性单调游标（`CO10_CARRYP`）**并计入桥孔向外足迹**"
             "（`CO10_CARRYALL` ⇒ `_BEXT = BR_JOG`）= 「列游标与桥孔 x 同解」；另复测顺序（rev / carry / xasc / engine）"
             "与既有修复旋钮（COLFIX / BRDROP / BR2 / POL_OFF）。**不含**跨页 y 交错（该轴须改几何，非旋钮可达）。",
             "- **结果（机判，探针 `b0ef06180cda787a`；`m13_v57_co209_band_joint_solve.json`）**：v9 默认 **32/32**；"
             "候选 C+BRCOL **24/32**（族最优，未变）；+COLFIX **23/32**；`CARRYP` 单用 **23/32**；`CARRYALL` 单用 **15/32**；"
             "**JOINT 组合 19/32（rev）/ 20/32（carry·xasc·engine）/ 19/32（+COLFIX / +BRDROP / +POL_OFF 0.2625）/ 15/32（+BR2）**。",
             "- **结论**：联合游标形态**不改善族上限**（JOINT 19–20/32 < 候选 C+BRCOL 24/32）：单调游标计入桥孔足迹后**过度推进**，"
             "把失败面由 chip 侧 input 页**转嫁**到连接器/走廊侧（`out_J2` / `out_MCIO`）。与 CO-205r 之暴露度分析一致 ——"
             "8 个失败页中 **6 页 > 0 余量**（阻断来自轨道/页内约束，非 via 拥塞）⇒ x 向联合求解**触不到**瓶颈。"
             "⇒ **族闭合（≤24/32）在直接行使下成立**；路径 B 仍不可达 32/32 ⇒ **打样路径 A 之定案不变**。"
             "残余自由度 = 跨页 y 交错（须改几何）与 **L1**（球重映射 / 信号流向）。",
             "- **工具面（同 CO 补齐）**：发射器 `p3_v57_co16_emit_allocation.py` 补 `CO10_CARRYALL → CO16_CARRYALL` 透传"
             "（原仅透传 `CARRYP`）⇒ 该联合形态**可由规范分配路径表达**；回归实测：v9 默认复现仍 **32/32 / 0 page diffs**。",
             "- **登记簿**：本件为**负结果**（无缺陷可登）⇒ 不入登记簿（诚实登记，勿虚增计数）。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows82 = [("工具 `p3_v57_co209_band_joint_solve.py`（形态矩阵 + 4 牙齿）", K2 / "tools/p3_v57_co209_band_joint_solve.py"),
               ("证据 `m13_v57_co209_band_joint_solve.json`（13 案结果 + 牙齿全 True）", STEP2 / "m13_v57_co209_band_joint_solve.json"),
               ("探针 `p3_v57_co10_west_fan_probe.py`（+11 只读旋钮，全默认关）", K2 / "tools/p3_v57_co10_west_fan_probe.py"),
               ("发射器 `p3_v57_co16_emit_allocation.py`（+10 旋钮透传，含新补 `CARRYALL`）", K2 / "tools/p3_v57_co16_emit_allocation.py"),
               ("现行分配 `m13_v57_co16_channel_allocation_v9.json`（回归基准）", STEP2 / "m13_v57_co16_channel_allocation_v9.json"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc82['total']} 项 / OPEN {_rc82['OPEN']}）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows82:
        if pth.exists():
            sec82.append(f"| {label} | `{s16(pth)}` |")
    sec82.append("")
    sec82.append("> **R-CO209-1**（承 z71 §6.3 / CO-207 O-2）：**族上限之「结构性论证」不得代替直接行使** —— "
                 "凡宣示某族在给定策略下不可达 32/32 者，须附可复算的形态矩阵（确定性、禁回溯）或等价机判；"
                 "矩阵扩展须同步判据件/工具，并保持默认路径逐字节可复现。")
    sec82.append("")
    sec82.append("> **R-CO209-2**（复现序，取代 R-CO208-4；**步集/序列不变，序内出现 50 次**）：规范复现序 = `" + _ord190 + "`，"
                 "**循环至 sha 稳定**（收敛判定须遵 R-CO164-1 + R-CO165-1/2 + R-CO167-1/2 + R-CO169-1/2 + R-CO174-1 + R-CO175-1 + R-CO176-1/2 "
                 "+ R-CO177-1 + R-CO178-1 + R-CO179-1/2 + R-CO180-1/2 + R-CO181-1/2 + R-CO182-1 + R-CO183-1 + R-CO184-1 + R-CO185-1/2 "
                 "+ R-CO186-1 + R-CO187-1/2/3 + R-CO188-1 + R-CO189-1 + R-CO190-1 + R-CO191-1 + R-CO192-1 + R-CO193-1/2/3/4 + R-CO194-1/2 "
                 "+ R-CO195-0/1 + R-CO196-1/2/4/5 + R-CO197-1/2/4 + R-CO198-1 + R-CO199-1 + R-CO200-1 + R-CO201-1/2 + R-CO202-1/2/3/4 "
                 "+ R-CO203-1 + R-CO207-1 + R-CO208-1/2/3 + R-CO209-1）。")
    sec82.append("")
    body82 = "\n".join(sec82)
    if MARK82 in txt:
        txt = re.sub(re.escape(MARK82) + r"[\s\S]*?(?=\n## |\Z)", body82, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body82

    # ── §83 CO-210（L2 自裁 · 随单 NOTES 热声明滞后 ⇒ 引现行定案 + O2 数字记录绑定） ──
    MARK83 = "## 83. CO-210"
    _rc83 = json.loads((L2 / "input_defect_register_v1.json").read_text())["meta"]["counts"]
    sec83 = [MARK83 + "（**L2 自裁 · 随单 NOTES（ORDER_NOTES §6）热声明滞后于 O2 定案 ⇒ 声明↔内容修正 + 记录绑定**）", "",
             "- **缺陷（G-1，low）**：CO-204 已把 U6 热**采 O2**（30×30 铝散热片 + 界面垫 1.0 ℃/W + ~2 m/s 风冷 ⇒ θJA_eff 11.0、四工况 ≤120）"
             "并作 `L2_RULING_u6_thermal_mitigation_v2.md`（取代 v1.0 之「推荐/待定」口径），该 v2 亦**已随包**（`06_rulings/`）；"
             "但生成器 §6 仍 ① 只引 **v1** 两件、② 以「⇒ 须（a）… 或（b）…」**未定口径**叙述、③ 引「登记簿 HIGH 项」而该项已由 CO-149/CO-150 **CLOSED**、"
             "④ O2 之 θJA_eff 与最重工况 Tj **无记录绑定**（CO-172 F-4 只绑了 CO-148/CO-149 的六个数字）⇒ **板厂/装配方读到已废口径**，且与本包自带之定案自相矛盾。",
             "- **处置**：① §6 改写为「问题定性（CO-148）+ **定案 O2（CO-204）**」两段式；② 按 CO-172 F-4 原则补**记录绑定** —— "
             "`order_notes_record_figures` 增 `co204`（散热验证闸记录）源 ⇒ 新增 **`o2_theta_ja_eff`**（`θJA_eff = 11.0 ℃/W`）与 **`o2_Tj_max`**（`117.0 ℃`）"
             "两项有锚判据，并入既有 **t12** 之 `all(figures)` 面（**不新增齿**，齿数仍 29）；③ 经生成器重出打样包（37 文件 / 29 牙齿全 True）。",
             "- **负控（判别力）**：θJA_eff 注入 12.0 ⇒ `o2_theta_ja_eff`=False；最重工况 Tj 注入 99.0 ⇒ `o2_Tj_max`=False；**旧（未定）§6 文本** ⇒ 两项皆 False ⇒ 绑定非空真。",
             "- **不影响**：Gerber/钻孔/叠层图/阻抗表**逐字节未变**（仅 ORDER_NOTES 文本 + 生成器变更）；板 `d4e81f647be7f980` 未动。",
             "",
             "| 工件 | sha16 |", "|---|---|"]
    _rows83 = [("生成器 `p3_v57_co146_jlc_fab_package.py`（§6 + `co204` 记录绑定）", K2 / "tools/p3_v57_co146_jlc_fab_package.py"),
               ("随单 `jlc_package/ORDER_NOTES.md`（§6 修正后）", L5 / "jlc_package" / "ORDER_NOTES.md"),
               ("包记录 `m13_v57_co146_jlc_fab_package.json`（牙齿 29/29）", STEP2 / "m13_v57_co146_jlc_fab_package.json"),
               ("记录 `m13_v57_co204_thermal_verification.json`（O2 定案；新增绑定之源）", STEP2 / "m13_v57_co204_thermal_verification.json"),
               ("裁定 `L2_RULING_u6_thermal_mitigation_v2.md`（O2 定案 v2.0）", L2 / "L2_RULING_u6_thermal_mitigation_v2.md"),
               (f"登记簿 `input_defect_register_v1.json`（{_rc83['total']} 项 / OPEN {_rc83['OPEN']}）", L2 / "input_defect_register_v1.json")]
    for label, pth in _rows83:
        if pth.exists():
            sec83.append(f"| {label} | `{s16(pth)}` |")
    sec83.append("")
    sec83.append("> **R-CO210-1**：凡**随单提交**（交付/打样）文本所引之口径，须引**现行定案件**（不得引其被取代之前身）；"
                 "由机读记录派生的系统级数字须与板级数字**同受**有锚绑定（承 CO-172 F-4 / R-CO208-1）。")
    sec83.append("")
    sec83.append("> **序不变**：本件未改步骤集/序列（承 §82 之 R-CO209-2）。")
    sec83.append("")
    body83 = "\n".join(sec83)
    if MARK83 in txt:
        txt = re.sub(re.escape(MARK83) + r"[\s\S]*?(?=\n## |\Z)", body83, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + body83

    txt = txt.replace("W3 Boundary **v2.50**", "W3 Boundary **v2.51**")
    txt = txt.replace("W3 Boundary **v2.49**", "W3 Boundary **v2.50**")
    txt = txt.replace("W3 Boundary **v2.48**", "W3 Boundary **v2.49**")
    txt = txt.replace("W3 Boundary **v2.47**", "W3 Boundary **v2.48**")
    txt = txt.replace("W3 Boundary **v2.46**", "W3 Boundary **v2.47**")
    txt = txt.replace("W3 Boundary **v2.45**", "W3 Boundary **v2.46**")
    txt = txt.replace("W3 Boundary **v2.44**", "W3 Boundary **v2.45**")
    DOC.write_text(txt)
    print("boundary sha16:", s16(DOC), "| lines:", len(txt.splitlines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
