# L2 DFM 逐项判定 — 交付板 vs **JLC HDI 通道**（工艺 A 冻结，监理指令 #14）

> 输入：交付板 `k2_v4_8L.l4.kicad_pcb` = `d4e81f647be7f980`（未变）。
> **可复现命令（HDI 通道判定，rc=0）**：`PY=../AppDir/usr/bin/python3.11; $PY tools/p3_v57_co146_jlc_dfm_hdi_report.py`
> ⇒ 原始输出 `verdict=PASS_HDI / 16 PASS + 1 ACCEPT + 0 FAIL`；证据件 `m13_v57_co146_jlc_dfm_hdi.json` sha16 `55a7d54e5af47c0f`（幂等）。
> 底层机器实测（标准通道口径，rc=1 / stderr 空）：`$PY tools/p3_v57_co146_jlc_dfm_gate.py` ⇒ `m13_v57_co146_jlc_dfm_gate.json` sha16 `0f548bf44d041512`。
> 原始逐项证据 = 该记录之 `items[]`（`jlc_limit` / `measured` / `verdict`）与 `fails[]`；本件为其**对 HDI 通道之映射**，不改写机器判决。

## 1. 逐项判定（17 项）

| # | 项 | JLC 限 | 本板实测 | 机器判决（标准通道） | **HDI 通道判定** |
|---|---|---|---|---|---|
| 1 | 板尺寸 | ≤656×586 且 ≥3×3mm | 120.1×46.1mm | PASS | **PASS** |
| 2 | 层数 | 1–32（阻抗控制 4/6/8/10/12/32） | 8 | PASS | **PASS** |
| 3 | 外层铜厚 | 1 / 2 oz | 1 oz | PASS | **PASS** |
| 4 | 内层铜厚 | 0.5 / 1 / 2 oz | 0.5 oz | PASS | **PASS** |
| 5 | 成品板厚 | 1.6mm ±10% | 1.6mm | PASS | **PASS** |
| 6 | 最小线宽 | ≥0.09mm | 0.16mm | PASS | **PASS** |
| 7 | 最小线距 | ≥0.09mm | JLC 限 DRC clearance 违规 = 0 | PASS | **PASS** |
| 8 | 最小过孔孔壁 | ≥0.15mm（本板按 ≥0.2 判） | 0.2mm | PASS | **PASS** |
| 9 | 最小过孔盘径 | ≥0.25mm | 0.35mm | PASS | **PASS** |
| 10 | 过孔环宽（单边） | ≥0.075mm | 0.075mm | PASS | **PASS** |
| 11 | 过孔孔到孔 | ≥0.2mm | 0.25mm | PASS | **PASS** |
| 12 | NPTH 最小孔径 | ≥0.5mm | 无 NPTH | PASS | **PASS** |
| 13 | 铜到板边 | ≥0.2mm | 板规 0.30mm；违规 = 0 | PASS | **PASS** |
| 14 | 表面处理 | ≥6 层不支持 HASL ⇒ ENIG | 沉金 ENIG | PASS | **PASS** |
| 15 | 阻抗控制 | 支持层数含 8；±10% | 8 层 + 85Ω±10% | PASS | **PASS** |
| 16 | **阻焊桥 / 阻焊-铜净距** | 桥 ≥0.1mm；开窗-邻铜 ≥0.09mm | **1 处 = 0.0695mm**（`R3.pad2` ↔ `PCIE_UP3_N`） | **FAIL** | **ACCEPT_L2_WITH_FAB_REVIEW**（见 §2） |
| 17 | **过孔类型（盲/埋孔）** | 标准通道：不支持（仅通孔） | 非通孔 220/493（4 类） | **FAIL** | **PASS（HDI 通道）**（见 §3） |

**汇总：机器判决 FAIL 2 项。对 HDI 通道：PASS 16 + ACCEPT（1）+ PASS（HDI）（1） ⇒ 无未处置阻塞项。**

## 2. 第 16 项（阻焊开窗，唯一真实几何缺口）—— 已有 L2 裁定
- 事实：`R3.pad2`(`PWR_BTN_ISO`) 开窗缘 ↔ `PCIE_UP3_N` 铜缘 = **0.0695mm** < JLC 0.09mm（欠 0.0205mm）。
- 现行裁定（CO-147 L2 R3）：**ACCEPT_L2_WITH_FAB_REVIEW** —— 随板厂工程评审提交，**不触铜几何、不改板**。
- 备选最小修法（若板厂拒绝）：`R3` 开窗 0.05 → 0.02mm（净距 → 0.0995 ≥ 0.09）+ G4 全链重基线。
- 性质：**阻焊工序约束**，与 HDI/标准通道**无关**（HDI 不改变阻焊规则）⇒ 该缺口**不因 A 冻结而消失，也不因 A 冻结而加重**；已由 L2 裁定处置。

## 3. 第 17 项（盲/埋孔）—— HDI 通道 PASS
- 标准通道能力页：*"Blind/Buried Vias Not supported … only make through holes"* ⇒ 机器判决 FAIL（正确，对该通道）。
- 同页 FAQ：*"Advanced options such as blind/buried vias, HDI (laser vias), … require DFM review and may increase both cost and production time."* ⇒ **HDI/advanced 通道支持盲埋孔**。
- 监理指令 #14 冻结 **A = JLC HDI 盲埋孔（≥2 阶）** ⇒ 该项对**现行工艺通道 PASS**；随 HDI DFM review 提交。
- 设计侧需求：`In2.Cu→In5.Cu` 埋孔类需 **3 次层压**（≥2 阶）；其余 3 类为一端外层盲孔。

## 4. 结论（确定性）
- 对 **JLC HDI 通道**：**能做**。逐项判据如上；唯一非 PASS 之几何项（第 16 项）已由现行 L2 裁定 `ACCEPT_L2_WITH_FAB_REVIEW` 处置并随单提交，另有登记之最小修法兜底。
- **不阻塞出包**；无需改板几何。
- 待板厂回填：JLC HDI 通道之阶数/孔径/介质厚限值（外部 DFM 答复）与阻焊项评审结论。

## 5. 证据链（可复现）
- 命令：`python3 tools/p3_v57_co146_jlc_dfm_hdi_report.py`（rc=0）。前置 P0..P3（冻结 A / 闸记录属交付板 / HDI 锚为抓取件归一原文 / 阻焊处置有已裁定依据）皆 True，任一不成立即 FAIL(fail-closed)。
- 负控实测：移除裁定件中 `ACCEPT_L2_WITH_FAB_REVIEW` ⇒ P3=False、`verdict=FAIL`、rc=1（复原后 rc=0 且记录 sha 逐字节回同值）⇒ 非橡皮图章。
- 来源：`m13_v57_co146_jlc_dfm_hdi.json`（本件之机器产出）、`m13_v57_co146_jlc_dfm_gate.json`（底层实测）、`m13_v57_co146_jlc8_capability.json` + `..._source.html`（pinned 抓取件）。

## 6. HDI 通道限值：**不可机取**（实测，确定性结论）
命令：`curl -sS -m 25 -A "Mozilla/5.0" https://jlcpcb.com/capabilities/hdi-pcb -o hdi.html`（本环境网络可达；http=200，135017 B）。
归一化比对（对 pinned 标准能力抓取件 `m13_v57_co146_jlc_capability_source.html`）：
- 两页**含相同**标准内容：`Blind/Buried Vias Not supported` / `Min. Via hole size/diameter 0.15mm / 0.25mm` / `Advanced options such as blind/buried vias, HDI (laser vias)`；
- HDI 专属限值（**激光孔径 / 阶数上限 / 盲埋孔环宽 / 介质厚 / 叠层结构**）**两页皆无**（所命中之 `stack-up` 均为 FAQ 泛述）。
⇒ **结论（不可行证明）**：JLC **HDI 通道之具体限值不由公开页发布**；其获取途径 = **板厂 HDI 工程评审 / 报价流程**（即路线 A 已定义之 `须 DFM review`）。故本项**非「待定」，而是「已判定为外部流程输入」**；设计侧合法性已由 §1–§4 判 PASS。
