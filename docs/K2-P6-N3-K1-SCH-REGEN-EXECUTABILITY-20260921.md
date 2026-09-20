# K2 · P6 · **N-3 可执行性判定**（K1 原理图侧再生 37→42）+ 验收核

- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/N3_K1_SCH_REGEN_EXECUTABILITY_20260921_v1.json`（sha16 `9a7e6aff4ee7b0c1`）
- 草案包：`k2/docs/drafts/n3-k1-sch-regen-v1/`（`README.md` + 验收核脚本）
- 性质：**只读**。未写 `k1/`；未新增判据维；未动冻结源/交付锚。
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 一句话
N-3 再生**大部分机械可得**，但 **`Q1`(TPS22990) 缺 2 脚且仓库无其 pinout**、`U12`(TPS22965) 同族 ⇒ **不可在不杜撰脚位的前提下完成**；缺口处置请监理择一。另交**验收核脚本**（5 项机判），对现行件实跑 **FAIL** 并**当场暴露先前遗漏的 `J10`**（已具名更正为 K1-S6）。

## 1. 机械可得 vs 数据缺口
| 面 | 判定 |
|---|---|
| `nets` | ✅ 由 `k1_nets.yaml#nets`（51 网）机械重建 |
| `placements`（5 件） | ✅ 由 `k1_board.yaml#devices` + `k1_pinmap.yaml` 派生 |
| footprint 修正 | ✅ 有出处：J1(S1) · U10(S2) · U12(S4) · **J10(S6·新登)** |
| `Q1` TPS22990 | ⛔ **缺 2 脚 + 无 pinout** ⇒ N3-G1 BLOCKING |
| `U12` TPS22965 | ⛔ 同族（N3-G2） |
| `U13` TPD2E001 | ✅ 手册 `pinout_6pin` 已具名（2 脚 = N.C.） |
| `Q2` / `R38` / `R39` | ✅ 完全派生 |

**缺口处置（监理自裁·无 owner 闸口）**：(i) 取手册转录 pinout + 三件套（ENG 建议）· (ii) 裁定 4 有网脚 + 2 NC 具名 · (iii) 部分再生（须监理同意）。

## 2. 验收核（机判）
`k1_sch_regen_acceptance_v1.py`：`A` refdes 集合==板 42 · `B` symbol 已定义 · `C` footprint==`k1_board.yaml` · `D` nets==`k1_nets.yaml` · `E` 渲染组件数==42。
**现行件实跑 = FAIL**：`A` 37≠42 · `C` **4 处**不符（含 **J10**）· `D` 13 网不一致 · `E` 渲染 37。

## 3. 【更正】K1-S6
`J10` symbol `HEADER_2PIN_12V` footprint 陈旧（`ForgeOS:PinHeader_1x02` vs 板 `JST_VH_B2P-VH_1x02_P3.96mm_Vertical`）——由本验收核暴露，属 ENG 先前审计**遗漏**，已具名更正；不影响既有结论。

## 4. 边界
只读；未动 `k1/`；验收核为该次**授权变更**的验收工具，非门禁新维（owner #14②）。
