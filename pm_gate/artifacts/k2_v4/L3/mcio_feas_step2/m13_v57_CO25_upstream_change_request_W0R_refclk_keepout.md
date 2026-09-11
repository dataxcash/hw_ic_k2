# UPSTREAM CHANGE REQUEST（引擎/归因生成，非 endpoint）— W0-R refclk passage witness 缺数据扇 F.Cu 接入包络

> 2026-09-12｜提出：ARCHER（续接会话 ARCHER-2）｜性质：**模型输入缺口（禁暴力迭代）**｜触发：CO-24 §1 D3a

## 1. 事实（实测，CO-23 板 `70f3fdc4149db146`）
DFM `new=73` 中 **60 条**为 `PCIE_REFCLK0/1` 与数据扇冲突。根因**不是**布线迭代不足，而是**见证/keepout 模型缺项**：

| 项 | 引擎/见证现状 | 实际板铜（shop DRC） |
|---|---|---|
| `refclk_passage_witness.per_page["PCIE_REFCLK0/input"].kind` | `direct_channel`，note: *"both corridor band coppers lie inside one chip-zone free channel chain; **no detour required**"*，`west_band_copper_y [45.458,46.042]` | REFCLK0 于 y≈45.9 **横穿 J3 pad 行（pad y 45.4..46.1）与 5.8mm F.Cu 接入斜线**：`shorting` REFCLK0_N×J3 A1[GND]；`tracks_crossing` REFCLK0_N×DN_OUT0/1 ×4 |
| `per_page["PCIE_REFCLK1/input"]` | `alternative_windows_same_side [[64.425,78.7]]`，`chain_windows_y [[62.525,63.575]]` | REFCLK1 斜线 `(82.35,63.47)→(60.7,61.45)` **横穿 J4 扇**：`shorting` REFCLK1_P×DN_OUT6_N/P、REFCLK1_N×J4 A18[DN7_N] |
| A-CN.5「REFCLK 段与 keepout 零交」 | **PASS（0 交）** | 60 条 DRC 违规 ⇒ **keepout 集合不含数据扇 F.Cu 接入铜** |

## 2. 请求（上游 W0-R 模型）
1. `refclk_passage_witness` 的 keepout/free-channel 输入须包含**数据页 F.Cu pad-access 段**（J3/J4 各数据 pad → via 平面 y=51.5/60.2 的 5.8mm 斜线）的**铜包络（含 width/2）**；
2. 重新判定 REFCLK0 是否仍为 `direct_channel`（现结论 `no detour required` 在含上述包络后**必然翻转**）；
3. 若存在合法通道，输出 REFCLK0/1 的**连接器侧接入窗口**（pad 行南北侧 + 允许的竖直下降列），替代现 `pad_field_transit: "delegated to connector side (W2/R3-R4)"`（该字段目前只声明、无几何）。

## 3. 处置纪律
- 本请求不改变拓扑/引脚（L1 未动）：refclk 仍为 `PCIE_REFCLK0/1` 对、仍落 J3/J4 同一 pad、仍 F.Cu（`decision_contract.refclk_layer = F.Cu(D0-2)`）。
- 在 §2 输入补齐前，**不得**用坐标搜索重试 refclk 几何（引擎 AST `while=0` 红线）。
- 落地方式：W0-R 见证件版本化新文件 + 变更单；引擎 `refclk_place()` 同步修订（rev bump）。
