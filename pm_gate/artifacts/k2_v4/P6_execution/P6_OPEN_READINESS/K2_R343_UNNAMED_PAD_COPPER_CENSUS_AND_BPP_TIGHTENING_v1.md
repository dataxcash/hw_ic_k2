# K2 · R343 · **全板无号 pad 铜层普查** ⇒ (B') 成立但 **name-only 不安全** ⇒ 给 **(B'') census 收紧**

**件**：`K2_R343_UNNAMED_PAD_COPPER_CENSUS_AND_BPP_TIGHTENING_v1.json`（约定A `ce52d5b591e62478`）

## 普查
| 侧 | 无号 pad | 分布 |
|---|---|---|
| 板 | **4** | H1–H4（`MountingHole_3.2mm_M3` · `np_thru_hole` · `*.Cu *.Mask`）—— 皆 **no_library_link** ⇒ **不参与**比对 |
| 库（`ForgeOS.pretty` · 24 件） | **10** | `MCU_STM32G0_LQFP48` **9** 枚 `smd/`**`F.Paste`**（无铜）· `MountingHole_3.2mm_M3` **1** 枚 `np_thru_hole/`**`*.Cu`**（**有铜**） |

## 安全判
- 本板唯一 `pad_set` 差异 = `U1`（`lib_only=['']`），库侧 9/9 **无铜** ⇒ **(B') 在本板成立**（R340 已验 19/19）。
- **通用风险**：**无号 pad 可以是铜**（H1–H4 / MountingHole 即 `*.Cu`）⇒ **name-only (B') 会把『无号铜 pad 集合差』误判为非电气**（潜在假绿）。
- **(B'') 收紧**：加 **layer-gated census** —— 仅当该 ref 之库封装无号 pad **皆不触铜** 方可豁免；census 缺失 ⇒ 不豁免（fail-closed）。
- **验证**：(B'') 本板 **19/19 PASS**；负控（伪设 U1 触铜）**不豁免 ⇒ 18/19**（闸有效）。

## 建议（gate 属主）
首选 rev=7 采 **(B'')**；次选由审计器 `cmp_fp` 对 `pad_set` 差异附**每 pad 层集**（工具改动 ⇒ **待批**）。

## 边界
只读 · 未烙板 · 未改 `criteria/`/生成器/SPEC/原理图 · 未派 WORKER。冻结四源 4/4 未动。

---
—— ENG（ARCHER）· 2026-09-22 · owner 闸口 **0**
