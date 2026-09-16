# L3 SPEC canonical 指引（#K2-12 §四 立；#K2-13 U1/S1 → rev-21；**#K2-14 2-A′ → rev-22**）

> 本文件**新增**于 2026-09-16（监理 #K2-12 §四）。**不动任何既有 SPEC 字节**。

## 1. canonical 是哪一个

| 角色 | 文件 | sha256（前 16） | 说明 |
|---|---|---|---|
| **canonical（现行，8L）** | `SPEC_k2_v4.spec-rev-22.json` | `9f0179e2afb7d766` | 由 `pm_gate/project.yaml: spec_name` **指向**；引擎据 `pm_gate.config.spec_name()` 解析 |
| 前身（8L） | `SPEC_k2_v4.spec-rev-21.json` | `d46bd017aa560716` | rev-22 = 本件 + （`components.mcu.U1` 两字段 QFN32/KBU6 → LQFP48/CBT6）+ `spec_version` + `_spec_rev_12` 卡 + `components.mcu_entry_fix_v22` 留痕；**原件逐字节不动** |
| 前身（8L） | `SPEC_k2_v4.spec-rev-20.json` | `37dcd9cde5ceed09` | rev-21 = 本件 − `anchor_fixes.C64/C66`（引 R1 分类留痕）+ `spec_version` + `_spec_rev_11` 卡；**原件逐字节不动** |
| 冻结源（8L，前身） | `SPEC_k2_v4.spec-rev-19.json` | `5f72182a2616392c` | rev-20 = 本件 + 2 处（`spec_version` + `_spec_rev_10` 卡）；**原件不动** |
| **历史 6L 件 —— 禁直接读取** | `SPEC_k2_v4.json` | `0bd52ed48e720b8c` | **6 层**（层键 F/In1..In4/B；`stackup.In2.Cu` 仍写 *"only internal signal layer"*），**已非 canonical**；仅在溯源时引用 |

## 2. 读取规则（强制）

1. **禁止硬编码** `SPEC_k2_v4.json`（或任何 SPEC 文件名）——一律经
   `pm_gate.config.spec_name(project)` + `pm_gate.artifacts.path("L3", <name>)` 解析。
   > 根因登记：`F-14` / `N-05`（生成器硬编码 `SPEC_PATH` 直指 6L 件）。
2. 任何工具/会话读到 `SPEC_k2_v4.json`（`0bd52ed4…`）即视为**陈旧读取**，须改用 canonical 并告警。
3. 本目录下 `SPEC_k2_v4.spec-rev-*.json` 为**版本链留档**（rev-2 … rev-20），只增不改：新修订一律**版本 bump 新文件**
   （宪法第四条），旧件**逐字节不动**。
4. 判据侧（`criteria/`，只读）与冻结锚比对时，**以 `project.yaml` 解析结果为准**。

## 3. 变更史（近三件）

| rev | 件 | at | 摘要 |
|---|---|---|---|
| **rev-22** | `spec-rev-22` `9f0179e2…` | **2026-09-16** | **#K2-14 §二（2-A′ 裁「是」）**：`components.mcu.U1` = `{ForgeOS:MCU_STM32G0_QFN32, STM32G0B1KBU6}` → **`{ForgeOS:MCU_STM32G0_LQFP48, STM32G0B1CBT6}`**（陈旧条目更正）+ `spec_version` bump + `_spec_rev_12` 卡 + `mcu_entry_fix_v22` 留痕 + `project.yaml` 重指向；**无器件集合/几何/走廊/PDN 变更**（板侧 U1 补齐 34..48 归 P4） |
| **rev-21** | `spec-rev-21` `d46bd017…` | **2026-09-16** | **#K2-13 U1/S1**：删 `anchor_fixes.C64/C66`（引 R1 分类：C64=A1 耦合内置 / C66=D 类 VREG 域不存在）+ `spec_version` bump + `_spec_rev_11` 卡 + `anchor_fixes_removed_v21` 留痕 |
| rev-20 | `spec-rev-20` `37dcd9cd…` | 2026-09-16 | canonical 归零（Z3）：`spec_version` bump + `_spec_rev_10` 溯源卡；其余逐字节承自 rev-19 |
| rev-19 | `spec-rev-19` `5f72182a…` | 2026-09-12 | 8L 收口（含 `_spec_rev_9` PDN 板实化）；冻结源 |
| **rev-20** | `spec-rev-20` `37dcd9cd…` | **2026-09-16** | **canonical 归零**（Z3）：`spec_version` bump + `_spec_rev_10` 溯源卡；其余逐字节承自 rev-19 |
| — | `SPEC_k2_v4.json` `0bd52ed4…` | 2026-08–09 | **历史 6L**，禁读 |
