# CO-118 — **L2 对抗一致性检查**：CO-74「B.Cu 不得铺电力铜/搭桥」↔ CO-112「3 桥区 = B.Cu 桥」+ N/A 裁定 = **声明冲突（fail-closed）**

- 判定：**`L2_DECLARATION_CONFLICT_OPEN__FAIL_CLOSED_4_TARGETS_UNCOVERED`**
- 输入：SPEC rev-15 `48d6fc7c565c8862`｜co95 `7bb1d00b697b0c6e`｜工具 `tools/p3_v57_co118_bcu_bridge_conflict_check.py`｜记录 `m13_v57_co118_bcu_bridge_conflict_check.json`
- 复现：`python3 tools/p3_v57_co118_bcu_bridge_conflict_check.py`

## 1. 机判（只读，零搜索；牙齿 4/4 含负控）

| 面 | 读数 |
|---|---|
| **A** `pd.bcu_power_copper_policy`（CO-74） | `policy=PROHIBITED`，basis 明文「B.Cu = 高速信号层…**不得铺电力铜/搭桥**」 |
| **B** 3 个 `L3_CONSTRUCTION_DERIVED` zone（CO-112 D1） | 全部 `bridge_layer="B.Cu"` 且 `bcu_bridge_bands` 非空 ⇒ **声明 B.Cu 桥** |
| **C** 同 3 个 zone 的 `carrier_change`（CO-74） | 全部 `from=B.Cu → to=In4.Cu`（「电力铜改由 In4 承载」）⇒ 与 **B 互斥** |
| **D** `plane_reachability_status.na_scope_v1.bcu_bridge_zone_targets`（CO-112 D2） | basis 明文「经 **B.Cu** 桥接 ⇒ 无需本网 In4 铜覆盖」⇒ **N/A 裁定依赖被禁止的载体** |
| **E** 受影响 target | **4** 项，且**均不在任何 In4 本网 polygon 内** |

## 2. 受影响 target（fail-closed：若 B.Cu 禁令成立 ⇒ 载体缺失）

| net | target | via_pos | 当前 In4 归属 |
|---|---|---|---|
| P3V3 | `C84.1` | (42.525, 40.0) | **落在 `MCU_VDD:MCU_VDD_WEST` 内**（异网铜包裹） |
| P3V3 | `U2.5` | (34.95, 39.83) | **落在 `MCU_VDD:MCU_VDD_WEST` 内** |
| P3V3 | `U4.3` | (40.0, 35.225) | **落在 `MCU_VDD:MCU_VDD_WEST` 内** |
| P3V3_AUX | `J4.A9` | (58.9, 62.275) | **落在 `P3V3:P3V3_EAST` 内** |

## 3. 处置选项（分层；本件只登记，不代裁）

| id | 层 | 动作 |
|---|---|---|
| **R1** | L2 | 撤 `na_scope_v1.bcu_bridge_zone_targets` 的 N/A，把 4 target 转为 **In4 覆盖义务** ⇒ rev-16 派生 In4 小区域（异网 ≥0.2、同网连通）。⚠ **受 requirement ④ 约束**：P3V3 西区 pocket 与 `P3V3_EAST` 的同网连通无 In4 通路（须横穿 `MCU_VDD_WEST`，会切断 MCU_VDD）⇒ 几何可行性须先机判，**可能不可行**。 |
| **R2** | OWNER/红线 | 为「限定桥带」开 CO-74 例外（= **放宽**「不得搭桥」红线）⇒ 须 owner/PM 明确授权；**L2 不得自放宽**。 |
| **R3** | L2 | 仅撤已过时的 `bridge_layer=B.Cu`（`MCU_VDD_BCU_RESISTORS_IN4` 的 R29/R31-R34 已被 CO-117 In4 覆盖，见 check F）——**不闭合** P3V3/P3V3_AUX 的 3 target。 |

⇒ **闭合需 R1 几何可行性判定（L2 可做）或 R2 红线例外（owner）；R1 若不可行则实质上升 L1（电源域划分）。**

## 4. 附带机判（check F）

`MCU_VDD_BCU_RESISTORS_IN4` 的 targets（R29/R31-R34）经 CO-117 扩 `MCU_VDD_WEST` 东缘至 57.75 **已被 In4 覆盖** ⇒ 该 zone 的 B.Cu 桥声明**已过时**。

## 5. 非声明

只读；不改 SPEC/板/阈值/冻结源；**不代 owner 做 R2 红线放宽**；零坐标搜索（坐标只取自声明 palette）；本件不重跑全链（无 SPEC/板改动）。
