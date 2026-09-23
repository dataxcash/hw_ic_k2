# K2 · R468 —— v2 自设评审格 (2) **有据通过**：**16/16 网全路径逐段域非空**

- **ts** 2026-09-24T05:12:17 · **from** ENG·ARCHER · **to** 监理 · **owner 闸口 0**
- **authority**：R466 v2 自设「可核自检计划」· **#K2-164 §四.2.c**（评审格加「全路径域非空 ∧ 全局指派存在性」）

## 0. 一句话
**v2 自设评审格 (2) 有据通过**：修正 L3 参数化（`(p,s,n)`：自 `SY(s)` 竖穿至 `NY(n)`）与 L1 起点核后复算 ⇒ **16/16 网全路径逐段域非空**（逐网可用组合 10⁴–10⁵ 量级 · 合计 **3,738,626** · 21.1s · 确定性几何 · **未驱动求解器**）⇒ 与 R465（2 网域空）形成**同法对照**，证「锚侧出入交求解器」确为该 2 网域空之解药。

## 1. 方法
逐腿可行性表合成：L1 竖降(colIn,s) · L2 南横(colIn,s,seat) · **L3 竖穿(seat,s,n)** · L4 北横(colOut,n,seat) · L5 竖升(colOut,n)；采样 0.2175；判据 = 在册 `build_base` 非 lane 障碍栅格；出口列候选 = B 侧西段 120–134；**未驱动求解器**

## 2. 结果（逐网可用组合数）
- `PCIE_UP_OUT0_N_J2`: exists=True · combos=204350
- `PCIE_UP_OUT0_P_J2`: exists=True · combos=128028
- `PCIE_UP_OUT1_N_J2`: exists=True · combos=204350
- `PCIE_UP_OUT1_P_J2`: exists=True · combos=152090
- `PCIE_UP_OUT2_N_J2`: exists=True · combos=233630
- `PCIE_UP_OUT2_P_J2`: exists=True · combos=178422
- `PCIE_UP_OUT3_N_J2`: exists=True · combos=253150
- `PCIE_UP_OUT3_P_J2`: exists=True · combos=188410
- `PCIE_UP_OUT4_N_J2`: exists=True · combos=282430
- `PCIE_UP_OUT4_P_J2`: exists=True · combos=188410
- `PCIE_UP_OUT5_N_J2`: exists=True · combos=311710
- `PCIE_UP_OUT5_P_J2`: exists=True · combos=231994
- `PCIE_UP_OUT6_N_J2`: exists=True · combos=311710
- `PCIE_UP_OUT6_P_J2`: exists=True · combos=246522
- `PCIE_UP_OUT7_N_J2`: exists=True · combos=311710
- `PCIE_UP_OUT7_P_J2`: exists=True · combos=311710

- **合计 3738626** · 墙钟 21.1s

## 3. 容量对账（评审格 (3) 之据）
{
 "port_columns": "实测 17–18 槽 ≥ 16 ⇒ AllDifferent(seat) 可满足",
 "band_rows": "南/北带可用行 ≥16（各 24 候选）⇒ AllDifferent(srow/nrow) 可满足",
 "corridor_columns": "锚侧下潜/上行列候选 28 / 9 ⇒ AllDifferent(colIn/colOut) 可满足",
 "note": "评审格 (3)「全局指派存在性」之**容量对账**于此具据；其**充分性**仍由一次全量受证求解终裁（跑不通 ⇒ 含核不可行证书）"
}

## 4. R467 更正
R467 之「全 0」读数系**我自身分解缺陷**（L3 误参数化）所致，**已作废**；本件为修正后复算结果，**同法可复现**。

## 5. 边界
冻结四源 4/4 未动 · criteria/ rev=6 未动 · 未改代码/在册工具/生成器/SPEC 设计/原理图 · 未派 WORKER · 未启全量。

---
—— ENG（ARCHER）· 2026-09-24T05:12 · sha16 `60d5e4c1af8303dd`
