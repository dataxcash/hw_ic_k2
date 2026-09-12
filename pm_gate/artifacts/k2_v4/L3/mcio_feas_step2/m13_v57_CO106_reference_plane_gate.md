# CO-106 L2 合格标准覆盖性补全：参考平面判据 + 参考平面连续性机判（判定 `INDETERMINATE_REGION_SCOPED`）

- 依据：`LAYOUT_CONSTITUTION` ch.2 —— L2 裁判标准 =「走廊闭合、等长预算、**参考平面**、PDN 压降、热」；ch.5 §1 覆盖性 / §3 可验证性。
- 触发：CO-87 的记录**自报**判据集含「参考平面」，但其覆盖矩阵只有 容量/长度/过孔/PDN压降/热 五行 ⇒ **参考平面无决策行、无闸**。本件补上该判据。
- 性质：L2 自裁 · 只读；不改 SPEC/板/阈值/冻结源。

## 判据与结果（在 **rev-13** 上）

| 面 | 判据 | 结果 |
|---|---|---|
| A 板框一致性 | 声明平面多边形 = 冻结板框 `board.outline_x/y` 按 `edge_copper_min` 内缩（GND 层逐边；In4 电源区因按分区裁剪仅校 y 跨度） | **PASS**（0 偏差） |
| B 参考平面连续性 | 每条规划走线每点（端点+相邻中点）须落在其 `impedance.per_layer[layer].refs` 所指**任一**参考层的声明铜内；分类：`declared_copper_missing`（GND 整面层缺铜，缺陷）vs `region_scoped_indeterminate`（In4 电源区裁剪 / 桥区几何待 L3 派生） | **INDETERMINATE**：`declared_copper_missing` **0**；`region_scoped_indeterminate` 54 段（In5←In4） |
| C 板实佐证 | 已施工铜落在"声明平面范围外"的实体计数 | rev-13 后 **0**（rev-12 时 = In5 **316** + In2 12 + via 24） |
| D 覆盖性补全 | CO-87 矩阵是否含「参考平面」行 | 矩阵无该行（`has_reference_plane_row=False`）⇒ 本闸补上；本项 ok 恒真（补全动作本身） |

牙齿 3/3（**合成**负控/正控，不依赖数据状态）：内缩检测器抓"错内缩 8.0mm"；连续性检测器对同一合成点（60,50）在 In4 判"无铜"、在 In1 判"有铜"；分类器按 `stackup` 角色分派。

## rev-12 时的判定与根因（本闸发现，已由 CO-107 施加修复）

- **判定 = `FAIL_DECLARED_COPPER_MISSING`**：`declared_copper_missing` **60** 点 / 36 段（In2 24 + In5 12），且 A 面 5 个多边形**下边一律差 8.0mm**。
- **根因（机证）**：3×GND（In1/In3/In6）+ 2×In4（`P3V3_EAST`/`MCU_VDD_WEST`）多边形下边 = **70.7** = `33 + 38 − 0.3` ⇒ 仍按**旧 38mm 板框**；而现行板框 = `board.outline_y [33,79]`（`note_v28_eco`：y 38mm→46mm，v20 用户裁决 H1）⇒ 按同一 basis（「整面铺铜 + 板边内缩 0.3」）应为 **78.7**。
- **后果**：板框内、平面外 **8.3mm 带状区**无参考平面，而施工已大量用该带 —— 实测板实 **In5 316 段 + In2 12 段 + 24 via**；PCIe 差分对 `PCIE_DN2..DN7` 的**等长蛇形恰好布在该带**（如 In5 `y=70.824/71.324` 蛇形）⇒ 蛇形段参考平面不连续。
- 修复 = **CO-107**（rev-13 平面随板框对齐）。

## 复现

```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
../AppDir/usr/bin/python3.11 tools/p3_v57_co106_reference_plane_gate.py   # 期望 INDETERMINATE_REGION_SCOPED / A dev=0 / declared_copper_missing=0 / teeth
```

## 非声明

- 桥区 `polygons=[]` 的缺铜归 CO-98 `declared_pending_l3` 桶，不在本件重复计缺陷；本件只把「参考平面」这一 ch.2 判据补进覆盖面。
- 一阶判据：点采样（端点 + 相邻中点）；不做网格/有限元、不判阻抗数值。
- In5 的 In4 参考连续性在桥区几何派生之前**不可判定**（≠ 已满足）——这是 CO-98 已登记的同一依赖在「参考平面」面的投影。
