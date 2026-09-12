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
    txt = txt.replace("W3 Boundary **v2.00**", "W3 Boundary **v2.01**")
    txt = txt.replace("W3 Boundary **v1.99**", "W3 Boundary **v2.00**")
    txt = txt.replace("W3 Boundary **v1.98**", "W3 Boundary **v1.99**")
    txt = txt.replace("W3 Boundary **v1.97**", "W3 Boundary **v1.98**")
    txt = txt.replace("W3 Boundary **v2.01**", "W3 Boundary **v2.02**")
    txt = txt.replace("W3 Boundary **v2.02**", "W3 Boundary **v2.03**")
    DOC.write_text(txt)
    print("boundary sha16:", s16(DOC), "| lines:", len(txt.splitlines()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
