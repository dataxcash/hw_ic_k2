# CO-18 — 【L2/L3】O4 等长蛇形有界幅值裁定：**全板 FEASIBLE_ALL**（推翻 CO-17「几何不可行」）

> 2026-09-12｜裁判：ARCHER（L2：走廊分配/等长/过孔策略/列距，自裁）｜性质：**变更单 + 正结果（取代 CO-17 否定结论）**
> ｜输入：`CO16-ALLOC.1`（`21ae78f8276d8df4`）｜引擎 rev：**W3-CN.34**｜canonical：`cf60e9dd167e739c`

## 0. 结论
1. **O4 可闭合**：在 **CO16-ALLOC.1 现有几何**下，32 页对内等长全部可达；canonical `FEASIBLE_ALL`（certs=0）。
2. **CO-17 §3.2「O4 蛇形无解」= 构造规则限定，非几何不可能性**：其三个隐含约束过强（见 §1）。
3. **一次求解验收**：`FEASIBLE_ALL ∧ crossings=0 ∧ A-CN.9 0/0/0 ∧ max|skew|=0.00306mm ≤0.15 ∧ wall 9.99s ≤120s ∧ 三序逐字节一致`。
4. **ECO 同批**：`SPEC-REV-2`（版本化新文件 `0a7ad112ac4c57e3`；原 `SPEC_k2_v4.json` 逐字节未动 `0bd52ed48e720b8c`）。

## 1. CO-17 过约束的三处根因
| # | CO-17 隐含约束 | 实况 | 后果 |
|---|---|---|---|
| (a) | 强制 `a >= A`（≤45° 陡度）⇒ 容量 = `(R-1)(√2-1)` | 同网斜腿间净距**无 DRC 要求**（`drc_rules.clearance.same_net_exempt=true`）⇒ 容许 `a < A`（陡） | 容量被低估约 2× |
| (b) | 要求同网自净距 ≥ TT(0.38) ⇒ `A ≥ TT/√2 = 0.269` | 同网豁免；只需**异网**净距 | 无解判定主因 |
| (c) | 横向余量按 **tt(0.38)** 取 | A-CN.9 对**每个折点**作 via 候选量测（`vt = 0.4525`） | 余量口径错侧 |

## 2. 本裁定的构造（闭式、零搜索、零迭代）
- 幅值：`A <= min(MEANDER_A_MAX, Δy - vt)`（`vt = via_r + clearance + width/2 = 0.4525`）；对向同时蛇形按对称解 `(Δy-vt)/2` 折半。
- 半齿步：`a >= LEGSEP_MIN/2 = 0.19`（相邻斜腿沿 run 距 ≥0.38；可制造性）。
- 命中：`teeth = ceil(extra / per_max)`，`per_max = 2(√(a_min²+A²) - a_min)`，`a = (A² - per_t²/4)/per_t` ⇒ **段长增量恰 = extra**（残差 0）。
- 结果：30 条需补偿线**全部 lane-only 闭合**（无需第二段/竖段）；320 via 保持 {F↔In2, In2↔In6, In6↔B}。

## 3. 验收数值（canonical `cf60e9dd167e739c`）
| 项 | 值 |
|---|---|
| verdict | **FEASIBLE_ALL**（certs=0，gate failed=[]） |
| 同层真交叉/重叠 | 0 / 0（含跨页 proper-intersection） |
| A-CN.9 净距套件 | tt 0 / vt 0 / vv 0 |
| 对内 skew | max **0.00306 mm**（阈值 0.15） |
| via / 段 | 320 / 320（>bandX 4、bandY 6，与 ECO 附件逐项一致） |
| 复现序 | `natural/reverse/hash` 三序 **逐字节一致**（A1.2 PASS） |
| wall | 9.99 s（≤120 s）；AST while=0 |

## 4. 遗留风险 / 待 G7 确认（不掩盖）
1. **对内 lane 中心距 = 0.5 mm**（`POL_OFF_CO16=0.25`，全 32 页）：CO-16 安全-hop 拓扑强制 `laney 距 >= vt = 0.4525`（P lane 须离 N 的 corner/drop via ≥ vt）。
   SPEC `impedance` 名义 `gap 0.175`（中心 0.38）+`alt_gap 0.2` ⇒ **差分阻抗模型偏离**，须由 **G7 SI / coupon**（`coupon_required=true`，`tolerance_pct=10`）确认或作为 owner-visible 偏差处理。
2. **4 对 via 异网间距 0.331–0.455 mm**：层跨**不相交**（{F,In2} vs {B,In6}）⇒ 引擎/CO-16 口径豁免（无共层铜、无重叠钻孔深度）；验证器 `via_min_inter` 为 span-blind legacy，须按 CO-16 口径或 **G7 KiCad DRC** 复核。
3. 验证器 co16 遗留口径（须同步，非豁免）：A-CN.3c `y_band`（CO-16 扇面 y，CO-10/CO-15 裁定）、V5 对内中心距（0.5 取代 0.38）。

## 5. 门控结果（本会话实跑）
| 门 | 判定 | 证据 |
|---|---|---|
| G4 / W3 | **PASS** | canonical `W3-CN.34 FEASIBLE_ALL`（`cf60e9dd167e739c`），certs=0，landing `092fb36eae7b9de3`（64 行） |
| G5 / W4 | **PASS** | `m13_v57_w3_validation.json` = W3-VALv2.3 PASS：G-M1..M6 全 True；A1.2 三序逐字节；A1.3 0 viol；A1.4 True；frozen True；metric 0；via_viol 0 |
| G6 / L4 | **PASS** | `p3_v57_l4_apply_drawing.py` → l4 板（68 网/1703 段/**248 via**，同点叠层合并）；`p3_v57_l4_validator.py` L4-A..E 全 True，viol=0 |
| G7 / L5 | **SI PASS / DFM FAIL(new=103)** | SI skew **0.0031 mm**；DFM 基线 42→L4 145（new 103：clearance 19 / shorting 11 / tracks_crossing 1 / copper_edge 29 / solder_mask_bridge 42 / hole_to_hole 1；**holes_co_located 72→0**） |

**同点叠层 via 合并（L4）**：CO-17 §4-2(D) 已落地——同 XY 层变点合并为单支 via（`layers=[min,max]`），物理等价且消除 `holes_co_located`（172→103）。
G7 DFM new=0 未达：残留 clearance/shorting/mask_bridge/copper_edge 为**平面反焊盘/板边/阻焊**类问题（非 O4/几何可行性），属 DFM 收口独立工作流。

## 6. 红线遵守
冻结四源**原件未动**（SPEC 版本化为新文件 + 变更单）；零坐标搜索（AST while=0）；未放宽任何净距/等长阈值；
无 partial pass；无 sign-off；证据落 ledger。
