# 变更单 CO-03 — 叠层基线对齐（6L 陈旧骨架 → 派生 8L 版本化基线）

> 2026-09-11｜发起：ARCHER｜依据：**整改通知 #06**（UC-01 定层纠正 / 撤销越权升级）｜级别：**L2（物理承载设计）**
> ｜裁判：SI/PI（L2，无需 owner）｜状态：**已实施**（G6/L4 已重跑 PASS；G7 待 O4 并入）

## 1. 撤销 owner 升级（#06 动作 1）
- UC-01（v1 / v2 / addendum v2 / v3 / v4）中"提交 owner 二选一（A/B 或 A′/B′）"的**升级请求撤回**；
  其技术内容保留为证据链，但**不再作为 owner 闸口**。
- 定层依据：`_shared/docs/LAYOUT_CONSTITUTION.md` 第二章 —— 叠层分配属 **L2 物理承载设计**，裁判权 = 高速信号/电源完整性工程师；
  非 L1 架构（owner）。
- 时间序：`0db5183`（M14 v30 物理 ECO，6L，2026-09-06）**早于** 整改 #03（`ba16057` / `558b0ce`，2026-09-11）；
  #03 明文裁定：**层数/层用途 = 容量闭合派生输出，无 owner/工单参数特权**，并撤销 R-03 的 owner 参数裁决。⇒ #03 优先。
- 冲突性质：**工件不一致**（LID.1 自载 `frozen_stackup_sufficient=false`；冻结板 6L 未随派生重推导），**非设计取舍**。§9 架构红线不适用。

## 2. L2 裁定（#06 动作 2：依容量闭合）
- **派生叠层 binding**（LID.1）：8L = `F(sig)/In1(GND)/In2(sig)/In3(GND)/In4(PWR)/In5(GND)/In6(sig)/B(sig)`，
  信号层 = `{F.Cu, In2.Cu, In6.Cu, B.Cu}`；依据 `L_escape=4`（chip_field depth=4）⇒ `L_signal_derived=4`、`total=8`。
- 该裁定为**派生输出**，无 owner/工单参数介入；`m13_v57_layer_intent_rev5.json` 载 8L 层用途（引擎消费件）。
- 版本化采纳件：`SPEC_k2_v4_8L_LID1.json`（`_stackup_derivation.total_layers=8`、`signal_layers=[F,B,In2,In6]`）。
  **阈值为同一性**：其 `net_classes.PCIe85` / `constraints.escape_transition_zone` / `vias` / `board` 与原 SPEC **逐项相等**（已核）。

## 3. 变更内容（#06 动作 3：版本 bump 新文件，原件不动）
| 项 | 内容 |
|---|---|
| 新基线 | `k2/k2_v4_8L.kicad_pcb`（sha16 `fb07d25ac426ff84`）；**原 `k2/k2_v4.kicad_pcb`（`f6273de6…`）原封不动** |
| 生成工具 | `k2/tools/p3_v57_stackup_realign_8L.py`（确定性 + fail-fast：锚点缺失即非零退出；可复现） |
| D1 层表 | 插入 `In5.Cu(12)` / `In6.Cu(14)`（与权威生成器 `k2_gen_v5.py:427-434` HEADER 及 LID.1 逐层一致） |
| D2 板框 | Edge.Cuts 左边 `(23,71)->(23,33)` 修为 `(23,79)->(23,33)` ⇒ 闭合；依 SPEC `board.outline_y=[33,79]`（原板框左 y=71 vs 右/底 y=79 撕裂） |
| 举证件 | `m13_v57_co03_stackup_realign.json`（sha / 子串断言 / 8 层 / 闭合自检） |
| 工具适配 | L4 工具 `SRC_PCB`→`k2_v4_8L.kicad_pcb`、`DST_PCB`→`k2_v4_8L.l4.kicad_pcb`；L4-A 期望 sha 更新 |

**KiCad 装载自检**（`AppDir/bin/python3.11` + pcbnew）：`CopperLayerCount=8`、`footprints=42`、`tracks=0`、`zones=0`、板框 bbox `22.95/32.95 → 143.05/79.05`（含线宽）。

## 4. 结果（#06 验收：新板 L4-A..E 全 True）
```
$ AppDir/bin/python3.11 tools/p3_v57_l4_apply_drawing.py --board
L4: nets=68 segs=338 vias=256 board=k2_v4_8L.l4.kicad_pcb
$ AppDir/bin/python3.11 tools/p3_v57_l4_validator.py
L4 VAL: verdict=PASS checks={'L4-A': True, 'L4-B': True, 'L4-C': True, 'L4-D': True, 'L4-E': True} viol=0
```
⇒ **G6(L4) 由 BLOCKED 转 PASS**（L4-E `board != record` 的根因即冻结 6L 板无 In5/In6，本轮以版本化 8L 基线消除）。

## 5. 四源版本化（#06 验收：4/4 MATCH）
新四源集（仅 PCB 项版本化；其余三源原件不动）：
| 源 | 路径 | sha16 |
|---|---|---|
| SPEC | `pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json` | `0bd52ed48e720b8c`（不变） |
| manifest | `…/mcio_feas_step2/m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7`（不变） |
| **PCB** | **`k2/k2_v4_8L.kicad_pcb`** | **`fb07d25ac426ff84`（新）** |
| rules | `_shared/eda_core/drc_rules.json` | `0a459839e15960b8`（不变） |

- 叠层权威 = `SPEC_k2_v4_8L_LID1.json` + `m13_v57_layer_intent_rev5.json`（#03 采纳件）；
  `SPEC_k2_v4.json` 的 `layer_plan` **文本**仍记 6L 判定（已被版本化 8L SPEC 取代），其**阈值不变且与 8L SPEC 逐项相等**。
  如需四源文本层亦全自洽，建议下一步对 SPEC 做纯文案版本 bump（非本轮阻塞项）。
- 监理侧 `watch.py:FROZEN` 的 PCB 项需同步改为 `k2/k2_v4_8L.kicad_pcb` + `fb07d25ac426ff84`（监理资产，ARCHER 不越权改）。

## 6. 后续（#06 动作 3 尾段 + 验收 4）
**O4（对内等长）并入同一次修订**：pair-aware 落列（L2 落地方案）⇒ 重跑 **W3 → W4(G5) → L4(G6) → L5(G7)**，
G7 重签**必须含 O4**（现况：32/32 对超差，最差 24.539mm ≫ 0.150mm）。

## 7. 红线
原冻结四源原件**未改**（仅新增版本化文件）；canonical W3 图纸未动；零搜索；无 owner/工单参数特权；
L2 裁定依据可追溯（#03 + 宪法第二章 + LID.1 派生）。
