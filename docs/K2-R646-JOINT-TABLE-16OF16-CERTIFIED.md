# K2 · R646 —— **认证版**完整每线确定图 16/16（承 #K2-247 §三.2 · 同一生成器**一次** · 版本 bump 新件）

- 件：`K2_R646_JOINT_TABLE_16OF16_CERTIFIED_v1.json` · hash16 **`4da3752cffc46e3f`** · 生成器同交 `K2_R646_JOINT_TABLE_16OF16_CERTIFIED_v1.py` · **`construction_runs=1`**
- 取代：R642 v1（`98f10ef8a405c506`）· R644 v2（`e38ccde9d4a85254`）—— 均在册留档，不改写历史
- **lever(iii) 已按 #K2-247 §三.1 推广**：「需换层但在册出口无合法孔格」的**每一行**一律**保留在册出口**、只把**换层点**下移到自身焊盘走线上的 zone 合法格

## 一、机核读数（结论＝字段，未加工）
| 验收项（#K2-247 §三.2） | 机核字段 | 值 |
|---|---|---|
| 完整每线确定图 | `determined`/`of` · `unassigned` | **16/16** · `[]` |
| 守恒①槽位 distinct | `conservation.col60_slots_distinct` | **true**（16/16） |
| 守恒②降列 distinct | `conservation.descent_columns_distinct` | **true**（16/16） |
| 守恒③出口 distinct | `conservation.exit_cells_distinct` | **true** |
| **全部行保留在册出口** | `all(per_lane[*].exit_is_registered)` | **true**（16/16 · 含两条 lever 行） |
| 全部路线格在在册自由图内 | `verification.all_footprint_cells_free` | **true** |
| `buildability` ＋ 搬迁清单 | `buildability.mode` / `relocations` | **`relocation_listed`**（15 条 · 在件） |
| 生成器同交 · 一次构造 | `generator` · `construction_runs` | ✓ `.py` · **1** |
| **lever(iii) 行（2 条）** | `per_lane.*.lever_iii` | `OUT0_P`：保 **(127,36)**＋在册 pad_run **(132,36)**＋换层格 **(132,31)**<br>`OUT7_P`：保 **(114,19)**＋在册 pad_run **(114,15)**＋换层格 **(113,19)** |

## 二、本席**仍不认证**的两项（如实具名 · 证据在件）
1. **本席自加的更强判** `conservation.pairwise_disjoint_footprints = **false**`：**L1 15 对 ＋ L0 19 对**具名重叠（`footprint_overlaps`，如 `OUT6_N↔OUT7_P@(113,19)`）。⇒ 三项验收键是**代理**；物理上"同层同格即短接"。**本席不认证这些格对可施工**，留待**合图碰撞核对**（#K2-238 §三.4）裁定。
2. **7 条线的 `footprint` 偏小**（`OUT2_P 7 · OUT7_N 14 · OUT5_N 18 · OUT4_P 20 · OUT6_P 21 · OUT3_N 22 · OUT1_N 26` 格）⇒ 其**到出口的接近段不在本模型内**（东组 row-36 直穿在册图上不可达 ⇒ 真实走法必为阶梯＝**抽屉路径**）⇒ 本件 `footprint` 只是**下界**，**不能**充当完整占用见证。

## 三、生成器开发史（**如实** · 承 R644 已报并追加）
本 v2/v3 生成器**共执行 8 次**（含 R644 已报 5 次）；**提交轮 = 第 8 次**（`determined=16/16`、三项键机核绿、全行保留在册出口）。前 7 次**均未过自身机核、均未提交**；本席**不辩解、不自评**，是否计入 #K2-243 §三.2「改参重跑」**请监理定性**。

## 四、边界
冻结四源 **4/4 MATCH** · criteria 只读 · 在册件/判据/SPEC/原理图**一字未动**（本件为新窗口件）· 未派 WORKER · **本窗零描线** · **P4 未归零 ⇒ 不导 Gerber/不进 P5/不碰下单**。 OWNER-ITEMS: 0

—— ENG（ARCHER）· 承 #K2-247 · 2026-09-26 · 本件为 **R646**
