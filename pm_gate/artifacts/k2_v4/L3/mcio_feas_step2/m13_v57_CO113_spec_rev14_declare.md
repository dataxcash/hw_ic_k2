# CO-113 — L2 施加：SPEC **rev-14** = 把 CO-105/109/110/111/112 的裁定写入 canonical SPEC（step ② 的「新 rev 重基线」）

- 判定：**施加完成**（仅新增声明键；既有标量仅 `spec_version` 变）
- 触发：CO-109 记录的 ②a「声明修正（新 rev 重基线）」
- 输入 SPEC rev-13 `7943be727a4f8ef9` → 输出 **rev-14 `188b01deb34c9fba`**
- 工具 `tools/p3_v57_co113_spec_rev14_declare.py`｜记录 `m13_v57_co113_spec_rev14_declare.json`
- 复现：`python3 tools/p3_v57_co113_spec_rev14_declare.py`

## 1. rev-14 = rev-13 + 仅新增声明键

| 新键 | 内容 |
|---|---|
| `pd.zone_defs.in4_corridor_void_by_design_v1` | In4 走廊 x∈(49.8,88.37) **按设计无铜**（PM T2-ECN-1/2）＋ In5 PCIe 量化（1094.8/2727.3mm = 40.1%，16 网） |
| `pd.zone_defs.power_zones[*].bridge_layer` | `P3V3_BCU_BRIDGE_IN4` / `P3V3_AUX_BCU_BRIDGE_IN4` / `MCU_VDD_BCU_RESISTORS_IN4` = `"B.Cu"` |
| `pd.zone_defs.power_zones[*].bcu_bridge_bands` | 声明带：basis 文本（P3V3 1 带 / P3V3_AUX 2 带）＋ MCU_VDD 取已声明 via bbox（provisional） |
| `pd.zone_defs.plane_reachability_status.na_scope_v1` | GND entry（CO-105）/ bridge zone targets（CO-112）语义 **N/A**（不删既有 `unresolved`、不改阈值） |

工具内**断言**：扁平化差分中，既有标量**只有** `.spec_version` 变化 —— 多边形/阈值/网/层角色/坐标/vias/blocked/impedance/stackup 全未动。

## 2. 不变性（重基线机判）

| 项 | 读数 |
|---|---|
| 图纸 `route_geometry`/`pages`/`landing_rows` | 与 rev-13 **逐字节同**（`c27d9f5b…`/`2535f330…`/`74234e98…`） |
| 板 | **`0e636a67c1472462` 逐字节不变** |
| G4 / G5 | **FEASIBLE_ALL**（主件 `0e74718b1e31dca5`，仅 `inputs_sha.spec` 变）/ PASS frozen=True |
| L4 / L5 | viol 0 / FAB ok + DFM new=0 + SI 0.1300 |
| PDN 闸 | co99 **0-0-0-0** PASS / co102 42-76(+34)-42 / co106 `INDETERMINATE_REGION_SCOPED` / co88 185-124-silent 0 |
| 回归闸 | co78/81/84/87/97/98/95/69 读数与 rev-13 一致（co87 字段扫描数 8506→8542 = 新键） |

## 3. 链 pin 前移（rev-13 → rev-14）
引擎 `F["spec"]`+`FROZEN_SHA["spec"]`｜validator `FROZEN["spec"]`+`FROZEN_SHA_PREFIX["spec"]`｜闸默认 spec co78/81/84/91/92/95/98/99/102/104/105/106（其中 co104/105/106 的 pin 键 `spec_rev13` → `spec_current`）｜co77 正则+路径。**历史件不动**：co107/co108/co109/co110/co111/co112 仍 pin rev-13（其时的历史复评/裁定，仿 CO-103 先例）；co100/co101 SRC 与 co103 亦不动。

## 4. 非声明
只新增声明键 + `spec_version`；不改几何/阈值/网/坐标/vias；不代填外部输入；任何后续 rev 须全链重基线 + 换会话复评。
