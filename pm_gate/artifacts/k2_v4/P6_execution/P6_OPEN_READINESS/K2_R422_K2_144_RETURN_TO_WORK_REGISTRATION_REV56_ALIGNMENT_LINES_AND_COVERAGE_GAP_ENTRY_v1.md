# K2 · R422 —— **#K2-144 复工登记** + 复工单 #2/#3 交付物（rev-56 变更行 · 覆盖缺口条目）

- **from** ENG·ARCHER（续接 · 应 **#K2-144 复工单**）· **to** 监理 · **owner 闸口 0**
- **authority**：**#K2-144**（Q1 权威=**In5** · Q2 声明性回填+版本 bump · Q3 准登记覆盖缺口）· #K2-68 §2.3 · #K2-69
- **边界**：文本/登记级。**未改 rev-55（冻结源）· 未改任何量化值 · 未建 rev-56 · 未出包 · 未烙板 · 未派 WORKER**。

## 1（指令1）复工登记：**In5 路线已复工** ✅
授权链：**#K2-68 §2.3**（`(F→In2→F)` = **6L 时代残留**定性）→ **#K2-68 D-1**（`F–In5` span **已在板 19 处（自 l4）**；32 条 OUT 车道**长走本就在 In5**）→ **#K2-69**（正式授权）⇒ 本轮 E 链（R393–R398 · R416 · v55 搬迁）**均在授权内**。
冻结 SPEC 之『In2』字样 **不具可执行性**（#K2-144 Q1）；既往 In5 执行**无越权**。

## 2（指令2）rev-56 变更行清单（**待下次同笔落库**，本件只列行、不建文件）
| # | JSON 路径 | 旧（逐字） | 新（逐字） |
|---|---|---|---|
| 1 | `constraints.j2_escape_topology.rule` | … UP_OUT 16 网经 **In2** 单内层走廊 (**F→In2→F** 单次换层), 不再走 B.Cu | … UP_OUT 16 网经 **In5** 单内层走廊 (**F→In5→F** 单次换层), 不再走 B.Cu（8L 信号层=F/In2/In5/B；原『In2』= 6L 残留 · 见 #K2-68 §2.3 · 本行=#K2-144 Q2 声明性回填） |
| 2 | `constraints.j2_escape_topology.outer_basis` | 8 层（LID REV6）：**In2** 独立走廊容纳全部 UP_OUT；… | 8 层（LID REV6）：**In5** 独立走廊容纳全部 UP_OUT；…（其余逐字节同） |
| 3 | `vias.high_speed.basis` | … 每线 ≤2 过孔 = 单次换层 (**F→In2→F**), 每对差分 4 过孔 | … 每线 ≤2 过孔 = 单次换层 (**F→In5→F**), 每对差分 4 过孔（同 #K2-68 §2.3） |

**候选第 4 处（请监理确认是否属『三处』）**：`layer_plan.j2_escape_nets.semantics`（内含 `PCIE_UP_OUT0-7_J2 (B_PET 带, VIA_IN2->In2 east)`）—— **ENG 不自行扩大变更面**。
**不动项（量化值 · #K2-144『禁触量化值』）**：`layer_plan.in2_width_mm = 0.205` · `vias.std{0.075,0.2,0.35}` · `vias.high_speed.max_per_line` · `impedance.*` · `stackup.*`；**rev-1..55 逐字节不动**（版本 bump 新件范式）。

## 3（指令3）覆盖缺口登记条目（呈请收录）
- **ID（建议）**：`GAP-CORRIDOR-LAYER-UNCHECKED`
- **标题**：**走廊层条款零机判** —— 质检只数过孔数量、不核对走线落在哪一层
- **类**：**覆盖缺口（自检盲区）· 非追责 · 非新增检查齿**（`criteria/` 零改动）
- **依据**：`k2_layout_quality_check_v1.py` B2 只产 `via_by_net`/`hs_hist`/`max_via`（全文无 In2/In5）⇒ 本次冲突**机器抓不住**；证据 = R421（`b68836aae57362b1`）+ 支配裁定 **#K2-144 Q3**
- **说明**：ENG 写域不含 `.omo/supervision/**` ⇒ **以项目侧件呈交**，请登记册属主收录

## 4（指令4）里程碑 tag
**已执行**：`k2-v60-p4-l9-standardcall-16ok3fail-relocation-defect-registered-corridor-layer-clarified`
范围 = R410–R421 之 P4 成果（l9 标准调用 **16 OK/3 FAIL** · 落搬迁缺陷**逐对象登记** · 项5 册证 · 落地流程缺口 · 影响面 · **二值面级分裂** · runbook · 钻孔普查 · DFM 预核 · 走廊层冲突与 **#K2-144** 口径澄清）。命名承 `k2-v<NN>-<phase>-<topic>-<state>` 范式（v59→v60）；若监理另有命名/落点偏好可重打（tag 可移动）。

—— ENG（ARCHER）· 2026-09-22 · 只读/登记 · owner 闸口 0
