# K2 · R340 · **残余 1 项电气差异已具名 = U1（无号无铜 F.Paste）** ⇒ **补 (B') 后 P4 = 19/19 PASS**（只读 · `criteria/` 未碰）

**件**：`K2_R340_RESIDUAL_ELECTRICAL_DIFF_NAMED_AND_P4_19OF19_VERIFICATION_v1.json`（约定A `4a4673678e3dfa46`）
承 R339（R317 两条修正 ⇒ 电气差异 7→1 · 仍 18/19）。本件把**残余 1 项具名**并给出**可达 19/19** 之最小非缩口径修正。

## 读数（同一 measure · 三种判定器副本）
| 运行 | n_pass | n_fail | passed | `lib_electrical_level` |
|---|---|---|---|---|
| 基线 rev=6 原样 | 18 | 1 | False | 电气级差异 **7**（豁免 0） |
| rev=6 + R317(A)(B) | 18 | 1 | False | 电气级差异 **1**（豁免 6）= 复现 R339 |
| rev=6 + R317(A)(B) + **本件 (B')** | **19** | **0** | **True** | 电气级差异 **0**（豁免 7） |

## 残余 1 项具名（决定性）
- **ref = `U1`**（`ForgeOS:MCU_STM32G0_LQFP48`）；record `verdict=electrical_diff` · `diffs=[{kind:"pad_set", board_only:[], lib_only:[""]}]`。
- **性质 = 非电气**：库封装含 **9 枚无号(`""`) `smd`、层集仅 `F.Paste`（无铜层）** 钢网孔径；板上实例无此 9 枚 ⇒ 审计器以 pad 名为键折叠成单个空名 `""` 之集合差。
- **独立取证**：`MCU_STM32G0_LQFP48.kicad_mod` 9 枚无号 pad 全为 `F.Paste`；板上 U1 `49` 枚 pad 全有号、无号 `0`；命名集合两侧**相等**。
- ⇒ **非几何/电气真差异**；与已核定 #K2-34 §一-6(B)『无号 F.Paste ⇒ 非电气』**同类**。

## 报监理之最小修法（(B') · 属 gate 属主写域）
把**已核定**之 (B) 规则由 `pad_name_set_only` 桶**扩展到 `electrical_diff` 桶**：
`kind ∈ {pad_set,pad_name_set} ∧ board_only==[] ∧ lib_only 全为 ""` ⇒ 非电气豁免。
**非缩口径**：几何零变更（对象无铜层）· 未改容差 · 未改圆规则 · 非新增齿 · 负控 B/C/D 未过度豁免。
**根因**：审计器 `cmp_fp` 只发 `kind='pad_set'`（无 `pad_name_set_only` verdict）⇒ rev=6 之 `pad_name_set_only` 分支**从不触发**，R317-(B) 落在死通道。

## 对 P4 之意义
rev=7 **须含 (B')** 方可达 19/19（R317/R324 §4『落定后 19/19』之预期**仅在补 (B') 后成立**）。此为**判据侧测量/验证**，裁定归**监理**。

## 边界
只读 · **未改 `criteria/`**（副本在 /tmp）· 未烙板 · 未改生成器/SPEC/原理图 · 未派 WORKER · 未写 `.omo/supervision/**` · 冻结四源 4/4 未动 · 受审板 l8 `7a5c89913d6e5d0a` 未动。

---
—— ENG（ARCHER）· 2026-09-22 · owner 闸口 **0**
