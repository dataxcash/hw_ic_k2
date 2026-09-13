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
    DOC.write_text(txt)
    print("boundary sha16:", s16(DOC), "| lines:", len(txt.splitlines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
