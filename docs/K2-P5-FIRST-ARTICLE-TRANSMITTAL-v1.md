# K2 · P5 首件实测 **投递说明（单一入口）** · v1（2026-09-21）

> **用途**：外部实测方执行 P5（打样首件 bring-up）时，本件为**唯一入口索引**：受审对象、随单件锚、逐项规程、回件格式、边界与责任人。
> **性质**：ENG 侧文档（**未改交付包** · 交付锚 `6ee7495de61f749f` 未动）。

## 1. 受审对象（实测对象 = 唯一）
| 项 | 值 |
|---|---|
| 板 | `k2/hw/k2_v4_8L.l7.kicad_pcb`（revision **l7**） |
| 板 sha16 | **`c5a7df90aadb66e0`** |
| 层数/工艺 | 8 铜层 · JLC HDI（盲埋孔 · 阶数≥2） |

## 2. 随单件（**冻结 · 只读 · 本件不重建**）
| 项 | 路径 | 锚 |
|---|---|---|
| 交付包 MANIFEST | `k2/pm_gate/artifacts/k2_v4/L6/jlc_package/MANIFEST.json` | `6ee7495de61f749f` |
| 打包件 | `k2/pm_gate/artifacts/k2_v4/L6/DELIVERY/k2_v4_8L.l7_gerber_package.tar.gz` | `0e88e107e2da8192` |
| 完整性 | `sha256sum -c DELIVERY/SHA256SUMS.txt`（自 `L6/` 运行） | **55/55 OK** |
| DFM | `pass 16 / accept 1（阻焊坝 · 已 L2 裁 ACCEPT_WITH_FAB_REVIEW + 有确定性修法证明）/ fail 0` | 见 `06_rulings/mask_accept_fix_proof.json` |

> **随单件 ≠ 可用性证明**：可用性只能由 P5 实测（V4–V7）证明。

## 3. 逐项规程与回件（**权威件**）
| 件 | 路径 | sha16 |
|---|---|---|
| 逐项操作规程（V4·V5·V6-1..5·V7 + 通用要求 + 回件格式） | `k2/pm_gate/artifacts/k2_v4/L6/first_article/RULES.md` | `8bee09616020d5a9` |
| 现场检查表 | `k2/pm_gate/artifacts/k2_v4/L6/first_article/CHECKLIST.md` | `d7dda9a82c5d06f3` |
| 回填模板（8 项 · criterion/measured/evidence/status） | `k2/pm_gate/artifacts/k2_v4/L6/first_article/results_template.json` | `c688b7daf9953b30` |
| 测点自查（pcbnew 直读 · 11/11 通过） | `k2/pm_gate/artifacts/k2_v4/L6/first_article/INSTRUMENT_SELFCHECK.json` | `3f89dec1a6481fe5` |
| 验收计划（阈值来源） | `k2/docs/K2-P5-FIRST-ARTICLE-ACCEPTANCE-PLAN-v1.md` | `43795d2def07152b` |

**8 项与阈值**：V4 阻抗券 **85.0Ω ±10%**（须覆盖 0.6mm 中心几何 + 最紧 0.2825mm `PCIE_UP3`）· V5 PDN 压降 **≤3%** · V6-1 各轨 **±5%** · V6-2 SWD device ID（二值）· V6-3 FRU I2C 地址应答（二值）· V6-4 **双路 x4 Gen4 训练成功**（二值 + LTSSM 终态）· V6-5 **30min AER = 0** · V7 热 **Tj ≤ 120.0℃**（四工况；`Tj(U6) > 117.0℃` 或未按 O2 实施 ⇒ **T1 触发**开新 rev，目标 `θJA_eff ≤ 9.5℃/W`）。

## 4. 回件与判定
- 回件 = 回填后的 `results_template.json`（`status ∈ {NOT_RUN, PASS, FAIL, INCONCLUSIVE}` + `measured` + `evidence[]`，每项附**原始件 + sha256**；二值项禁「基本正常」类表述）。
- 责任：**实测方**填写（`measured_by`）· **监理**判定（`judged_by`）· **ENG 不得自证**。

## 5. 商务面（**非 ENG 任务** · owner #14④）
- 阻抗券（V4）**索取动作在下单页**注明（#K2-48 N-1 (a)：接受 + 随单注明，**不动交付锚**）。

## 6. 已知具名观察（**不新增判据** · 见 RULES §已知具名项）
- 阻焊坝 9 处（`U1` pad23/24 · `U6` FG1 · `J13` pad1/2 等）：焊接后桥连检查；若证实桥连 ⇒ **T1 触发**（修法 `pad_to_mask_clearance=0.02mm`，须**另开 rev**）。
- 正面丝印 4 处越框（`H4`/`R41`/`D2`/`C87`）：确认位号可读性（预期缺损 · 非缺陷）。

## 7. 红线
ENG 不参与自证 · 禁改冻结随单件/重建包 · 禁为变绿改阈值（C-12）· 结果未经监理判定不得宣称 P5 通过。
