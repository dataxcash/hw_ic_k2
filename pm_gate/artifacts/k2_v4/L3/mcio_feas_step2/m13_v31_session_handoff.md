# M14 v31 — scope-B gaps 闭合（A 裁决+B 去耦+C port_to_corridor ECN+D sch 真值）+ E 骨架/登记

> 状态：**本 session = m13_v30 handoff §3 open gaps A-E 承接**。承接资产 = m13_v30（裁决门/真板 ECO/
> C5 实测）+ L1/L2 v2.0 + C5 矩阵 v28(_v30 修正)。
> 结果：**A 侧带方案用户裁决定案 ✅ / B C79/C83 去耦重排净空归零 ✅ / C port_to_corridor 逐带 ECN-007
> + 回归 FEASIBLE ✅ / D k2_sch.yaml 真板对齐重建 + 逐球 parity 246/246 ✅ / E L3 施工全链 = 用户裁决
> 骨架+如实登记 open（板 0 track/0 via，需下 session 完整计划/施工）**。
> 用户/架构裁决 3 次：① gap A 侧带方案 = L2 target+MCU I2C2+按推荐 strap（本文件 §0.1）
> ② gap D 图形层 = yaml 真值闭合 + kicad_sch 生成器能力缺口登记（§0.2）
> ③ gap E 范围 = A-D 闭合 + E 骨架/登记（§0.3）。

## 0. 裁决与授权（用户/架构）

- **裁决点1（gap A 侧带方案，2026-09-06）**：DS320PR1601 侧带 17 球定案 —— MODE=L2（SMBus target，
  6.225kΩ±10% target，实取 E96 6.19k 1% 下拉）；SDA/SCL → **MCU I2C2**（复用 R33/R34 4k7 上拉，J11
  EC 头可达）；A_ADDR0/1_7-0 = L0/L0（1k/1k，地址 0x18/0x19）、B_ADDR0/1_7-0 = L0/L1（1k/8.25k，
  0x1A/0x1B）；A/B_ADDRx_15-8 无用 bank 全 L0(1k)；PD_3-0/PD_7-4→GND（lanes0-7 上电）、
  PD_11-8/PD_15-12→P3V3（lanes8-15 下电省电）；READ_EN_#/ALL_DONE_# 悬空 NC（target 模式语义）。
  依据：TI SNLS683 Table 5-1/7-3/8-1/8-2 + 板 I2C1（J2 SMB+E2+MCU）/I2C2（MCU+J11，空闲）实测。
- **裁决点2（gap D 图形层）**：kicad_sch 354pin 图形化 = schlib 生成器能力缺口（loader 强制
  pin_pitch≥2.54 + 单 body + 纸型 A2/A3/A4，DS320 354 球最小 body 高 449.6mm > A2 420mm，
  实测证书）→ **yaml 网表真值本 session 闭合 + kicad_sch 图形缺口登记**，禁伪造/禁手工千行 sheet。
- **裁决点3（gap E 范围）**：板全空（0 track/0 via/0 zone 实测）→ L3 施工全链超出本 session 可靠边界；
  **A-D 闭合 + E layer_plan 6L 骨架再生 + 全链如实登记 open**（下 session 承接）。

## 1. gap B 落地（真板物理，先备份后改）

- **C79 (91,58)→(91,61)；C83 (91,57)→(91,62)**（x=91 南条带 y61/62，位于 U6 pad 域 y≤57.49 以南
  ≥2.0mm；与既有 C80(59)/C81(60)/C82(64) 共列保去耦环语义）。
- **净空审计归零**：reproduce_eco_full_clearance.py 复跑 NON-U6=0、U6-vs-others=0（v30 时 6 违例）。
- 备份：`L3/k2_v4.kicad_pcb.bak_scopeB_v30`（sha 5237578b…）；板 sha after = f6273de6…；
  freeze unlock→pcbnew SetPosition→lock（0/0/0）。

## 2. gap C 落地（引擎 desc ECN-007，unlock→edit→lock）

- **问题**：SPEC per_ball `port_to_corridor {A:east,B:west}` 前缀键（escape_landing `band[0]`），无法表达
  修正后逐带映射 → 现引擎分类 B_PET=DIRECT(西)、A_PET=VIA(东) = 修正前语义，与 L2 v2.0 对账文本相悖。
- **ECN-007**（pm_gate cli，cwd=k2）：新建+ruled（批准不回退，裁决全文见 state_k2_v4.json ecns）。
- **引擎**：`_shared/eda_core/escape_landing.py` 新增 `_corridor_of_band`（全名键优先 + 前缀回退兼容），
  per-ball side（L1076）+ per_band side（L1110）改走该函数；docstring 契约更新。
- **数据**：SPEC_k2_v4.json（备份 .bak_v30）+ SPEC_k2_v4_c3poc.json + reproduce_per_ball_escape.py
  `port_to_corridor` → {A_PER:east, B_PET:east, A_PET:west, B_PER:west}。
- **回归**：per_ball_escape_6L_report.json 重生成 —— verdict **FEASIBLE 不变**，direct=32（A_PET+B_PER）、
  via=32（A_PER+B_PET）、crossing 16（N/S 各 8）＝ 修正语义（v30 前方法拆分翻转）；eda_core
  test_escape_landing.py 19 passed；生产 plan() v1.4 = FEASIBLE_WITH_MORPH_GAP + ⑦ evaluated FEASIBLE
  （POC_PASS）＝ 无回归。

## 3. gap D 落地（k2_sch.yaml 真板对齐重建，schlib loader + 真板 parity 机器闭合）

- **k2_sch_v31_rebuild.py**（可复跑，资产入库）：REDR_DS160PR810 符号删 → DS320PR1601 354pin 符号
  （name=signal 唯一；重复信号 GND/N/C/VCC1-4 name=ball）；U3/U7 + C17-C32/C49-C64/C65-C72 +
  旧 strap（R4-R7/R9-R12/R17-R20/R22-R27）全清（nets/sheets/links/strap_intents）；64 差分网按修正后
  C5 矩阵逐球重连（A_PER→PCIE_DN*、B_PET→PCIE_UP_OUT*_J2、A_PET→PCIE_DN_OUT*_MCIO、
  B_PER→PCIE_UP*；J3=lane0-3/J4=4-7）；P3V3 += 30 VCC + PD_11-8/15-12；GND += 152 GND + PD_3-0/7-4；
  I2C2_SDA/SCL += U6 SDA/SCL；新增 strap 网 ×9 + R35-R39/R42-R45（R_1K/R_6K19/R_8K25 符号）；U6
  NC 清单 93（RSVD15+N/C12+lanes8-15 64+READ_EN_#/ALL_DONE#）自动生成防 loader dangling。
- **校验**：schlib load_board_spec PASS（55 components / U6 ×1 / U3 U7 0 残留 / 42 symbols / 101 nets）；
  **reproduce_k2_sch_v31_parity.py：真板 U6 246 已接球逐球比对 0 fails + 侧带 17 球 yaml 映射全对
  （READ_EN_#/ALL_DONE# 预期 NC）→ PASS**。
- 备份：`L3/boards_k2_sch.yaml.bak_v30`；sch 生成器链路（generate_sch_v5.py）loader-可读，
  图形再生 = §0.2 裁决登记缺口。

## 4. gap E 骨架再生（SPEC layer_plan/corridors 6L 单芯片语义）

- 清 stale 8L/U3-U7 施工数据（j2_escape_nets/wp1_escape_nets/in2_crossing_nets/u3_side_bridges/
  in6_usage/wp1_escape_nets_meta/wp6 折线段 — 网已不存在于真板 v30 ECO）。
- 注入修正语义骨架：in2_crossing = A_PER+B_PET 16 对（VIA_IN2 east）N/S 各 8；j2_escape（东）=
  PCIE_DN0-7+UP_OUT0-7_J2；wp1_escape（西）= PCIE_UP0-7+DN_OUT0-7_MCIO（DIRECT F.Cu west）；
  low_speed nets 名表（自 v31 yaml，含 I2C2 侧带）；corridors 重建 EAST_CHIP_TO_J2 /
  WEST_MCIO_TO_CHIP（16 data + REFCLK 2，band 网列表按修正语义）。
- SPEC sha16 after = 2c024beed007412c（备份 .bak_v30）；plan() POC 复跑 PASS（FEASIBLE_WITH_MORPH_GAP
  + ⑦ evaluated FEASIBLE）。
- **open（下 session）**：逐网 dogbone/via/In2 坐标 + 翼带 lane 指派 + 低速/侧带布线计划 = L3 施工
  （引擎链 escape_connect_gen 等既有链，禁新写求解器）→ pcbnew DRC 归零 → QA 门禁 → S 状态机
  srun/sadvance（S0→S5）。真板侧带 17 球物理接线 + 9 strap 件落位随 L3。

## 5. G5 收尾自检

- **消费资产**：m13_v30 handoff（§0 裁决/§3 gaps A-E）；L1/L2 v2.0 frozen（穿越/走廊/硬约束）；
  c5_chip_level_expect_matrix_v28.json（_v30_scopeB_correction，64 网接线唯一基准）；ds320pr1601_ballmap.json
  + DS320PR1601.kicad_sym（354pin 符号/引脚源）；eco_scopeB_physical_record.json +
  reproduce_eco_c5_verify.py + reproduce_eco_full_clearance.py + reproduce_per_ball_escape.py（复跑链）；
  TI SNLS683 主源（/tmp/opencode，侧带 strap 语义）；_shared/eda_core/escape_landing.py（ECN-007 消费）；
  schlib loader/renderer（yaml 校验 + 生成器能力判定）；EXECUTION_PROCESS/GATES/宪法（G0-G5 纪律）。
- **未消费/缺口**：kicad_sch 图形再生（生成器 354pin 能力缺口，§0.2 登记）；gap E L3 施工全链
  （§4 open，用户裁决登记）；真板侧带物理接线 + strap 件（随 L3）；SPEC layer_plan 逐网施工数据
  （同 gap E）；kb.sqlite3 未更新（引擎改动已 ECN-007 全记录于 state ecns，无新形态模板增量，零 _shared
  知识资产变化）。
- **停止/熔断**：G4 未触发。2 次用户裁决问询（A 方案、D 图形层、E 范围 = 3 次裁决）均为 L0-L3 无据
  设计决策/超界处置，非 L0-L3 已有答案抛回。一次 k2_sch rebuild 脚本非幂等重复运行 → 恢复备份重跑单次
  （技术性修正，非盲试）。一次 loader dangling 报错 → 按 loader 契约（NC 必须显式）补 U6 nc 清单后
  单次通过。
- **禁违反项**：✅ 冻结区写全走 freeze_ctl unlock→edit→lock（真板移件 gap B、_shared 引擎 ECN-007、
  均先备份+记录，锁回 0/0/0）；未 chmod 自解；未伪造 kicad_sch 图形/未手工千行 sheet；未运行时设计
  决策（gap A/B 先裁决/先算净空后落位）；E 未假闭合（板 0 track 如实登记）；未翻 8L；引擎改动仅走
  ECN-007 + 回归证据链全绿（c5 130 / clearance 0 / per_ball FEASIBLE / parity 246 / plan POC / tests 19）。

## 6. commit 预备

- `_shared`（容器根 ic_hw_eda）：eda_core/escape_landing.py（ECN-007 _corridor_of_band 全名键）→ commit。
- `k2`：k2_v4.kicad_pcb（C79/C83 移件，已锁）+ L3/k2_v4.kicad_pcb.bak_scopeB_v30 + L3/boards_k2_sch
  .yaml.bak_v30 + L3/SPEC_k2_v4.json.bak_v30 + boards/k2_sch.yaml（重建）+ SPEC_k2_v4.json（layer_plan
  骨架 + port_to_corridor 带键）→ commit。
- `k2` 证据资产（L3/mcio_feas_step2/）：k2_sch_v31_rebuild.py + reproduce_k2_sch_v31_parity.py +
  ds320_symbol_pins.json + per_ball_escape_6L_report.json（重生成）+ eco_clearance_report.json（更新）+
  eco_scopeB_physical_record.json（_v31 全量）+ SPEC_k2_v4_c3poc.json + m13_v31_session_handoff.md →
  commit。pm_gate state_k2_v4.json（ECN-007）→ 随 k2 commit。
- 容器根：bump _shared + k2 gitlink。冻结区 git 前 unlock、后 lock（0/0/0）。

## 7. 边界声明

6L = 判定流程终定不变（未触发 8L 重入；ECN-007 容量账中性复核）。scope-B 进展 = gaps A（裁决）/
B（物理）✅ / C（ECN-007+回归）✅ / D（yaml 真值 parity 246/246）✅ / E = layer_plan 6L 骨架 + 全链
open 如实登记（用户裁决）。真板现 = 6L/46mm/U6 rot90 全信号接线 + 去耦重排净空归零 + **0 走线待 L3**。
下 session 承接：gap E L3 施工全链（含侧带物理接线 + 9 strap 件）→ DRC 归零 → QA → S 状态机；
kicad_sch 图形再生待 schlib 生成器扩展裁决（multi-unit/自定纸型 ECN）。
