# m13 v57 — **L5/G7 开工卡 v1**（sign-off 记录 + 知识提升评审）

> 2026-09-11｜依 `EDA_AUTONOMOUS_EXECUTION_PLAN_v2.md` G7 行｜DOR：L4 完成
> DOD：**SI/PI/EMC、DFM/DFT、制造记录 + 知识提升评审**｜验证：**记录是证据，不是修理许可**｜
> rollback：**reopen owning layer**（不得在 L5 就地修）

## 1. 语义
- L5 **只读取证**：对 L4 产物（`k2_v4.l4.kicad_pcb`）+ 冻结基线（`k2_v4.kicad_pcb`）做**只读**检查/对拍。
- 不修任何板/图纸/工件；发现违例 = **记录**，并据 rollback **回上层**（W3/L4）重开。

## 2. 交付（记录集）
| # | 文件 | 内容 |
|---|---|---|
| R1 | `m13_v57_l5_fab_record.json` | 制造记录：层叠/铜层、钻孔表、外形 bbox、track/via/net 计数、输入指纹 |
| R2 | `m13_v57_l5_dfm_dft_record.json` | DFM/DFT：kicad-cli DRC（冻结基线 vs L4，逐类新增）+ 制造极值一致性 + DFT 可达性 |
| R3 | `m13_v57_l5_si_pi_emc_record.json` | SI/PI/EMC：线宽（阻抗 85Ω/0.205）、对内等长（≤0.15mm）、回流平面、平面完整性、via 类型 |
| R4 | `m13_v57_l5_knowledge_promotion.md` | 知识提升评审：规则注册表 + 生命周期政策 + 拓扑样板库 + 本轮教训 |
| R5 | `m13_v57_l5_g7_record.md` | G7 记录（verdict + 是否需回上层） |

## 3. 判定
- 三记录 + 复核**全 PASS** ⇒ **G7 PASS**（sign-off）。
- 任一 FAIL ⇒ **G7 = FAIL/REOPEN**：按宪法回 owning layer（W3/L4），**不得在 L5 修理**。
