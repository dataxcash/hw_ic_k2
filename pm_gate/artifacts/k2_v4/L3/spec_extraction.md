# L3 SPEC 提取说明（G3.1 产物）

> 宪法第三章：SPEC 从 L2 冻结文档**单向提取**，禁止反向，禁止人工脑补。
> 提取物：`SPEC_k2_v4.json`（机器可校验，执行器与验证器共用）。

## 提取规则

1. 每条 SPEC 项必须可追溯到 L2_STRUCTURE_v1.0.md 或 prereq_closure.md 的原始裁决
2. SPEC 是**数据**，不包含任何执行决策（无 fallback、无自适应、无"如果"）
3. 执行器（布线脚本）只能读取 SPEC，不得修改 SPEC

## 溯源映射（SPEC 字段 → 冻结文档条款）

| SPEC 字段 | 来源 |
|---|---|
| stackup.* | L2 叠层分配（In1/In3 GND、In4 电源） |
| impedance.* | prereq_closure 风险 1 裁决（w=0.205/g=0.175） |
| net_classes.* | L2 阻抗参数 + ECO #12（对内 0.15、对间 0.5） |
| vias.* | prereq_closure 风险 2 裁决（0.20/0.35）+ L2 过孔策略 |
| corridors.* | L2 走廊分配（上下带各 4 对、带距 1.104、间隔 ≥2mm） |
| capacitor_walls.* | L1 冻结（对称电容墙，修正对角缺陷） |
| constraints.* | L2 硬约束 + checklist B.7/A.3 + JLC 工艺 |
| pd.* | L2 PDN 冻结（In4 分区、去耦直连） |

## 可验证性（宪法第五章第 3 条）

- 每个数值字段都可写成机器断言：
  - `assert board.outline == [23,143]×[33,71]`
  - `assert PCIe85.width == 0.205`
  - `assert corridors.J2_TO_U.bands == [upper,lower] × 4 pairs`
  - `assert vias.high_speed_via_count == 0`
- 验证器（L3 施工后 QA 用）将逐条核对

## 版本

- v1.0（2026-08-13）
