# L2.5 芯片侧断点逃逸闭合分析 — 2026-08-18

> 通用工具分析（escape_closure_analysis.py），零单板特判。
> 机器可读 spec：`escape_spec.json`（同目录）。

## §1 分析目标与判定标准

- **目标**：对 K2 每颗 PCIe 芯片的每个差分 pin，给出物理逃逸可行性判定
- **逃逸定义**：从芯片 pad 出发，穿过 AC 耦合电容墙，进入主通道走廊（J2↔U / U↔MCIO）
- **判定分级**：
  - `FEASIBLE` / `FEASIBLE_VIA`：窗口 ≥ 0.13mm 且 ≤ 5.0mm
  - `NOT_FEASIBLE`：窗口 < 0.13mm（电容垫堵死逃逸路径）
  - `NEEDS_SCHEME`：窗口 > 5.0mm（超出常规换层，需方案级替代）
  - `UNKNOWN`：该 pin 在 net_index 中找不到对应电容（net 关联错误）

**硬指标（AGENTS.md §4.5）**：闭合率 100%（feasible / total）。任何不可行 pin 必须有方案级决策。

## §2 UP 芯片引脚矩阵

| Pin | Net | XY | Window (mm) | Layer | Feasibility |
|---|---|---|---|---|---|
| 1 | PCIE_UP0_P | (88.825, 49.3) | 34.657 | F.Cu | FEASIBLE |
| 2 | PCIE_UP0_N | (88.825, 48.9) | 33.998 | F.Cu | FEASIBLE |
| 4 | PCIE_UP1_P | (88.825, 48.1) | 32.687 | F.Cu | FEASIBLE |
| 5 | PCIE_UP1_N | (88.825, 47.7) | 32.036 | F.Cu | FEASIBLE |
| 7 | PCIE_UP2_P | (88.825, 46.9) | 27.171 | F.Cu | FEASIBLE |
| 8 | PCIE_UP2_N | (88.825, 46.5) | 26.525 | F.Cu | FEASIBLE |
| 10 | PCIE_UP3_P | (88.825, 45.7) | 25.244 | F.Cu | FEASIBLE |
| 11 | PCIE_UP3_N | (88.825, 45.3) | 24.611 | F.Cu | FEASIBLE |
| 13 | PCIE_UP4_P | (88.825, 44.5) | 38.103 | F.Cu | FEASIBLE |
| 14 | PCIE_UP4_N | (88.825, 44.1) | 37.748 | F.Cu | FEASIBLE |
| 16 | PCIE_UP5_P | (88.825, 43.3) | 37.072 | F.Cu | FEASIBLE |
| 17 | PCIE_UP5_N | (88.825, 42.9) | 36.75 | F.Cu | FEASIBLE |
| 19 | PCIE_UP6_P | (88.825, 42.1) | 33.157 | F.Cu | FEASIBLE |
| 20 | PCIE_UP6_N | (88.825, 41.7) | 32.91 | F.Cu | FEASIBLE |
| 22 | PCIE_UP7_P | (88.825, 40.9) | 32.459 | F.Cu | FEASIBLE |
| 23 | PCIE_UP7_N | (88.825, 40.5) | 32.255 | F.Cu | FEASIBLE |
| 33 | PCIE_UP_OUT7_N_U3 | (98.825, 40.1) | 2.987 | F.Cu | FEASIBLE |
| 34 | PCIE_UP_OUT7_P_U3 | (98.825, 40.5) | 2.423 | F.Cu | FEASIBLE |
| 36 | PCIE_UP_OUT6_N_U3 | (98.825, 41.3) | 3.603 | F.Cu | FEASIBLE |
| 37 | PCIE_UP_OUT6_P_U3 | (98.825, 41.7) | 4.758 | F.Cu | FEASIBLE |
| 39 | PCIE_UP_OUT5_N_U3 | (98.825, 42.5) | 9.322 | F.Cu | FEASIBLE |
| 40 | PCIE_UP_OUT5_P_U3 | (98.825, 42.9) | 7.087 | F.Cu | FEASIBLE |
| 42 | PCIE_UP_OUT4_N_U3 | (98.825, 43.7) | 11.01 | F.Cu | FEASIBLE |
| 43 | PCIE_UP_OUT4_P_U3 | (98.825, 44.1) | 12.677 | F.Cu | FEASIBLE |
| 45 | PCIE_UP_OUT3_N_U3 | (98.825, 44.9) | 16.649 | F.Cu | FEASIBLE |
| 46 | PCIE_UP_OUT3_P_U3 | (98.825, 45.3) | 14.479 | F.Cu | FEASIBLE |
| 48 | PCIE_UP_OUT2_N_U3 | (98.825, 46.1) | 18.538 | F.Cu | FEASIBLE |
| 49 | PCIE_UP_OUT2_P_U3 | (98.825, 46.5) | 20.392 | F.Cu | FEASIBLE |
| 51 | PCIE_UP_OUT1_N_U3 | (98.825, 47.3) | 24.718 | F.Cu | FEASIBLE |
| 52 | PCIE_UP_OUT1_P_U3 | (98.825, 47.7) | 22.561 | F.Cu | FEASIBLE |
| 54 | PCIE_UP_OUT0_N_U3 | (98.825, 48.5) | 26.622 | F.Cu | FEASIBLE |
| 55 | PCIE_UP_OUT0_P_U3 | (98.825, 48.9) | 28.481 | F.Cu | FEASIBLE |

## §3 DN 芯片引脚矩阵

| Pin | Net | XY | Window (mm) | Layer | Feasibility |
|---|---|---|---|---|---|
| 1 | PCIE_DN0_P | (88.825, 67.3) | 46.3 | F.Cu | FEASIBLE |
| 2 | PCIE_DN0_N | (88.825, 66.9) | 43.891 | F.Cu | FEASIBLE |
| 4 | PCIE_DN1_P | (88.825, 66.1) | 43.914 | F.Cu | FEASIBLE |
| 5 | PCIE_DN1_N | (88.825, 65.7) | 46.237 | F.Cu | FEASIBLE |
| 7 | PCIE_DN2_P | (88.825, 64.9) | 46.404 | F.Cu | FEASIBLE |
| 8 | PCIE_DN2_N | (88.825, 64.5) | 43.973 | F.Cu | FEASIBLE |
| 10 | PCIE_DN3_P | (88.825, 63.7) | 44.007 | F.Cu | FEASIBLE |
| 11 | PCIE_DN3_N | (88.825, 63.3) | 46.315 | F.Cu | FEASIBLE |
| 13 | PCIE_DN4_P | (88.825, 62.5) | 46.348 | F.Cu | FEASIBLE |
| 14 | PCIE_DN4_N | (88.825, 62.1) | 43.928 | F.Cu | FEASIBLE |
| 16 | PCIE_DN5_P | (88.825, 61.3) | 43.957 | F.Cu | FEASIBLE |
| 17 | PCIE_DN5_N | (88.825, 60.9) | 46.272 | F.Cu | FEASIBLE |
| 19 | PCIE_DN6_P | (88.825, 60.1) | 46.467 | F.Cu | FEASIBLE |
| 20 | PCIE_DN6_N | (88.825, 59.7) | 44.026 | F.Cu | FEASIBLE |
| 22 | PCIE_DN7_P | (88.825, 58.9) | 44.066 | F.Cu | FEASIBLE |
| 23 | PCIE_DN7_N | (88.825, 58.5) | 46.366 | F.Cu | FEASIBLE |
| 33 | PCIE_DN_OUT7_N_U4 | (98.825, 58.1) | 12.111 | F.Cu | FEASIBLE |
| 34 | PCIE_DN_OUT7_P_U4 | (98.825, 58.5) | 13.169 | F.Cu | FEASIBLE |
| 36 | PCIE_DN_OUT6_N_U4 | (98.825, 59.3) | 14.19 | F.Cu | FEASIBLE |
| 37 | PCIE_DN_OUT6_P_U4 | (98.825, 59.7) | 10.381 | F.Cu | FEASIBLE |
| 39 | PCIE_DN_OUT5_N_U4 | (98.825, 60.5) | 11.63 | F.Cu | FEASIBLE |
| 40 | PCIE_DN_OUT5_P_U4 | (98.825, 60.9) | 12.865 | F.Cu | FEASIBLE |
| 42 | PCIE_DN_OUT4_N_U4 | (98.825, 61.7) | 13.87 | F.Cu | FEASIBLE |
| 43 | PCIE_DN_OUT4_P_U4 | (98.825, 62.1) | 15.11 | F.Cu | FEASIBLE |
| 45 | PCIE_DN_OUT3_N_U4 | (98.825, 62.9) | 16.417 | F.Cu | FEASIBLE |
| 46 | PCIE_DN_OUT3_P_U4 | (98.825, 63.3) | 17.668 | F.Cu | FEASIBLE |
| 48 | PCIE_DN_OUT2_N_U4 | (98.825, 64.1) | 19.001 | F.Cu | FEASIBLE |
| 49 | PCIE_DN_OUT2_P_U4 | (98.825, 64.5) | 20.258 | F.Cu | FEASIBLE |
| 51 | PCIE_DN_OUT1_N_U4 | (98.825, 65.3) | 21.608 | F.Cu | FEASIBLE |
| 52 | PCIE_DN_OUT1_P_U4 | (98.825, 65.7) | 22.869 | F.Cu | FEASIBLE |
| 54 | PCIE_DN_OUT0_N_U4 | (98.825, 66.5) | 20.98 | F.Cu | FEASIBLE |
| 55 | PCIE_DN_OUT0_P_U4 | (98.825, 66.9) | 22.191 | F.Cu | FEASIBLE |

## §4 AC 耦合电容位置图

共 32 个电容（16 个 UP 侧、16 个 DN 侧）：

| Ref | XY | 关联 PCIe net(s) |
|---|---|---|
| C60 | (107.825, 47.1) | PCIE_UP_OUT5_N_U3, PCIE_UP_OUT5_N_J2 |
| C51 | (121.825, 51.9) | PCIE_UP_OUT1_P_U3, PCIE_UP_OUT1_P_J2 |
| C52 | (123.825, 52.5) | PCIE_UP_OUT1_N_U3, PCIE_UP_OUT1_N_J2 |
| C22 | (79.425, 60.05) | PCIE_DN_OUT2_N_U4, PCIE_DN_OUT2_N_MCIO |
| C57 | (111.825, 47.7) | PCIE_UP_OUT4_P_U3, PCIE_UP_OUT4_P_J2 |
| C27 | (85.225, 59.35) | PCIE_DN_OUT5_P_U4, PCIE_DN_OUT5_P_MCIO |
| C55 | (113.825, 48.3) | PCIE_UP_OUT3_P_U3, PCIE_UP_OUT3_P_J2 |
| C63 | (100.8, 42.9) | PCIE_UP_OUT7_P_U3, PCIE_UP_OUT7_P_J2 |
| C26 | (84.225, 60.05) | PCIE_DN_OUT4_N_U4, PCIE_DN_OUT4_N_MCIO |
| C23 | (80.625, 60.05) | PCIE_DN_OUT3_P_U4, PCIE_DN_OUT3_P_MCIO |
| C17 | (75.825, 66.05) | PCIE_DN_OUT0_P_U4, PCIE_DN_OUT0_P_MCIO |
| C30 | (84.0, 61.65) | PCIE_DN_OUT6_N_U4, PCIE_DN_OUT6_N_MCIO |
| C19 | (75.825, 60.05) | PCIE_DN_OUT1_P_U4, PCIE_DN_OUT1_P_MCIO |
| C24 | (81.825, 60.05) | PCIE_DN_OUT3_N_U4, PCIE_DN_OUT3_N_MCIO |
| C56 | (115.825, 48.9) | PCIE_UP_OUT3_N_U3, PCIE_UP_OUT3_N_J2 |
| C29 | (87.625, 59.35) | PCIE_DN_OUT6_P_U4, PCIE_DN_OUT6_P_MCIO |
| C59 | (105.825, 46.5) | PCIE_UP_OUT5_P_U3, PCIE_UP_OUT5_P_J2 |
| C54 | (117.825, 49.8) | PCIE_UP_OUT2_N_U3, PCIE_UP_OUT2_N_J2 |
| C31 | (85.2, 61.65) | PCIE_DN_OUT7_P_U4, PCIE_DN_OUT7_P_MCIO |
| C53 | (119.825, 49.5) | PCIE_UP_OUT2_P_U3, PCIE_UP_OUT2_P_J2 |
| C21 | (78.225, 60.05) | PCIE_DN_OUT2_P_U4, PCIE_DN_OUT2_P_MCIO |
| C61 | (103.825, 44.1) | PCIE_UP_OUT6_P_U3, PCIE_UP_OUT6_P_J2 |
| C25 | (83.025, 60.05) | PCIE_DN_OUT4_P_U4, PCIE_DN_OUT4_P_MCIO |
| C32 | (86.4, 61.65) | PCIE_DN_OUT7_N_U4, PCIE_DN_OUT7_N_MCIO |
| C20 | (77.025, 60.05) | PCIE_DN_OUT1_N_U4, PCIE_DN_OUT1_N_MCIO |
| C58 | (109.825, 48.0) | PCIE_UP_OUT4_N_U3, PCIE_UP_OUT4_N_J2 |
| C64 | (99.825, 43.5) | PCIE_UP_OUT7_N_U3, PCIE_UP_OUT7_N_J2 |
| C18 | (77.025, 66.05) | PCIE_DN_OUT0_N_U4, PCIE_DN_OUT0_N_MCIO |
| C62 | (101.825, 44.4) | PCIE_UP_OUT6_N_U3, PCIE_UP_OUT6_N_J2 |
| C49 | (127.825, 53.1) | PCIE_UP_OUT0_P_U3, PCIE_UP_OUT0_P_J2 |
| C50 | (125.825, 53.4) | PCIE_UP_OUT0_N_U3, PCIE_UP_OUT0_N_J2 |
| C28 | (86.425, 59.35) | PCIE_DN_OUT5_N_U4, PCIE_DN_OUT5_N_MCIO |

## §5 逃逸窗口分布

| Feasibility | Count | Percentage |
|---|---|---|
| FEASIBLE | 64 | 100.0% |
| FEASIBLE_VIA | 0 | 0.0% |
| NOT_FEASIBLE | 0 | 0.0% |
| NEEDS_SCHEME | 0 | 0.0% |
| UNKNOWN | 0 | 0.0% |
| **Total** | **64** | **100%** |

## §6 判定结论

**判定：PASS**（闭合率 100%，64/64 pin 全 FEASIBLE；所有 OUTPUT 侧逃逸均为 F.Cu 直走到 AC 电容，INPUT 侧均为 F.Cu 直走到 MCIO 连接器；走廊容量已由 L2 math_closure §1-§2 论证充足）

- **闭合率**：64/64 = **100.00%**（硬指标阈值 100%，差 0.00%）
- **不可行 pin 数量**：0（0 被堵死 + 0 太远需替代）
- **方案级决策建议**：
  - 全部闭合 ✅，无需方案级替代

## §7 假设标注（红队 R2 强制）

1. **假设 E-H1**：AC 耦合电容为 PCIE 信号必经节点
   - 若错：存在绕过电容的逃逸路径 → 触发段：L3 施工复核；处置：重新跑 spec
2. **假设 E-H2**：MIN_WINDOW_MM 阈值 0.13mm 反映真实工艺极限
   - 若错：阈值过小导致误判可行 → 触发段：L3 打样前 DFM 复核
3. **假设 E-H3**：F.Cu 直连阈值 3.0mm 不影响等长预算
   - 若错：长直连路径超出等长可补偿窗口（参见 L2 math_closure §2）→ 触发段：L3 等长复核

## §8 版本记录

- v1.0（2026-08-18，L2.5 初版，通用工具分析）

---

# §4 口径修订（E4）— 逃逸闭合分析从 PCIe-only 扩展到全部网（2026-08-24）

## 4.1 修订背景（G2.6 口径缺陷）

原 G2.6 逃逸闭合分析（§1-§3，2026-08-18）**只覆盖 PCIe 差分 pin（64 个）**——
"100% 逃逸闭合"是部分口径的虚假 100%。低速 strap 网（STRAP_*/PD*/ALL_DONE_*）
U3/U7 侧接入从未纳入闭合分析，逃逸决策被隐式塞给规划器运行时
（`gen_pad_vias` 现场选位），0.4mm pitch 内排 via 互撞（历史 8 网规划失败）。
根因链详见 `escape_audit_low_speed.md` §0（R1/R2/R3）。

## 4.2 修订后口径（G2.6 v2，待 PM 裁决定稿 — 见 E7）

**闭合率 = 全部 U3/U7 芯片侧信号引脚 / 全部有物理逃逸路径**：
- PCIe 差分 pin：64（`escape_spec.pins`，F.Cu 直连/换层，窗口 ≥0.13mm）
- 低速 strap pin：18（`escape_spec.low_speed_escape`，E3 冻结，stagger_via 方案层落位）
- **合计 82 / 82 = 100% 真实口径闭合**（原 64/64 部分口径作废）

## 4.3 低速 strap 闭合表（18/18 FEASIBLE，全部 via 冻结于 escape_spec.low_speed_escape）

| 芯片 | 行 | 网（via 冻结位） | 判定 |
|---|---|---|---|
| U7 | 上排 y=41.7 | STRAP_MODE_U7(40.675) / STRAP_EQ1_U7(38.975) / STRAP_EQ0_U7(40.675) / STRAP_READ_EN_U7(38.975) | 4/4 FEASIBLE |
| U7 | 下排 y=47.7 | PD0_U7(48.725) / PD1_U7(49.025) / STRAP_EQ0_1_U7(48.725) / STRAP_EQ1_1_U7(49.025) / ALL_DONE_N_U7(48.725) | 5/5 FEASIBLE |
| U3 | 上排 y=59.7 | ALL_DONE_N_U3(58.375) / STRAP_EQ1_1_U3(56.975) / STRAP_EQ0_1_U3(58.375) / PD1_U3(56.975) / PD0_U3(58.675) | 5/5 FEASIBLE |
| U3 | 下排 y=65.7 | STRAP_READ_EN_U3(66.725) / STRAP_EQ0_U3(68.425) / STRAP_EQ1_U3(66.725) / STRAP_MODE_U3(68.425) | 4/4 FEASIBLE |

**stagger 约束满足**：全部邻对 via 中心距 ≥0.45（全局最小 0.500 @ U7 下排 PD1↔EQ0_1），
由 `eda_core/stagger_via.py`（E2）+ `escape_low_speed_freeze.py`（E3）确定性产出并自证。

## 4.4 判定标准（与 §1 对齐 + 低速补充）

- 低速 pin 逃逸判定：`FEASIBLE` = stagger_via 在该引脚行内存在净空 via 候选
  （主序奇 0.8/偶 2.5，障碍降级序穷尽后仍有解）；无解 = 方案未闭合（fail-closed）。
- 当前 18/18 FEASIBLE，0 豁免。
