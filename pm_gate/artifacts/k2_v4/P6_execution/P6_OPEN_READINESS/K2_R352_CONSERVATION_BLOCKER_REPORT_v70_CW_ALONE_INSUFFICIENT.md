# K2 · R352 ·《守恒级卡点报告 **v70**》—— **C-w 单独不足**（构造仍 3/16）

**件**：`K2_R352_CONSERVATION_BLOCKER_REPORT_v70_CW_ALONE_INSUFFICIENT.json`（约定A `02da011e7c3e0791`）· 承 v69

## 两次 C-w 条件跑（movable = 可腾挪族 18 网）
| # | 设置 | placed | `exact_gate` |
|---|---|---|---|
| A | 层距 0.45 · 排除 P | 2/16 | pitch 1 · clr 3（**口径不一致**：gate 未给 movable） |
| B | 层距 **0.55** · 排除 P+2·cell·√2 · **gate 同给 movable** | **3/16** | pitch 3 · min_gap 0.0 · clr 0 · min_clr 1.065 · ep 0 |

失败模式：『端点』（waypoint/锚被已布 lane 之排除带覆盖）· 『wp』（waypoint 落于排除带）。

## 判
**C-w 释放了空间（v69：重排带均值 0.296→0.816）但不产生见证** ⇒ **C-w 单独不足；C-\* 之重排感知联合指派仍为必需**。
且**顺序贪心 + 硬排除**在层距/排除半径贴 P 时反复受**网格余量**之累（0.45 层距余量 15µm < cell 0.02）。

## 建议（监理自裁）
**(i)+(ii) 联合**：①批 C-w（`PERSTA#` 首选 + `ref_plane_continuity`）②派 C-\* **一次实现**：**互距感知候选生成**（非顺序贪心/非硬排除）+ 联合指派（连续几何层）⇒ `exact_gate` 互距 0 ∧ 净距 0 ∧ 端点 0 + `buildability`。

## 边界
只读 · 未烙板 · 未改 `criteria/`/生成器/SPEC/原理图 · 未派 WORKER。冻结四源 4/4 未动；受审板 l8 `7a5c89913d6e5d0a` 未动。

---
—— ENG（ARCHER）· 2026-09-22 · 二值 **未取得** · owner 闸口 **0**
