# CO-25 — 【L2 自裁】D3b 判据修正落地：独立复核器 pad 净距**双缺陷**修复 + 6 条真缺陷定域；D3c 自裁决策

> 2026-09-12｜裁判：ARCHER（续接会话 ARCHER-2）｜依据：CO-24 §2/§3｜性质：**工具判据修正 + 归因收口（不改几何、不改 DRC 判据）**

## 0. 结论
`tools/p3_v57_co11_placement_verify.py` 的 pad 净距判据有**两个独立缺陷**（CO-24 只识别了第 1 个），修复后
对 CO-23 几何给出 **6 条真缺陷**，且与 shop DRC **逐值吻合**。修正为 **opt-in**（`CO11_PAD_UNITS=copper`），
默认 `centerline` = 旧行为，**W3-CN.37 / ALLOC.4 证据仍逐字节可复现**（已实测 legacy 仍 PASS 0）。

## 1. 缺陷（实测）
| # | 缺陷 | 后果 | 证据 |
|---|---|---|---|
| 1 | **量纲**：`seg_pad_gap/pad_gap_pt` 返回**中心距**，却与 `ESC=0.075`（SPEC 逃逸区**铜距**下限）比较，少减 `width/2=0.1025`（via 少减 `via_r=0.175`） | 判据放宽 0.1025 | CO-24 §2 |
| 2 | **几何近似**：`seg_pad_gap` 用「pad 中心在段上的投影点 → pad 矩形」近似，**高估**净距；pad 中心投影非真实最近点 | 假阴性 | `DN_OUT5_N`：近似给中心距 0.2452（铜距 0.1427 PASS），真值 0.1607（铜距 **0.0582**，shop DRC 同值） |
| 3 | 层盲：via-pad 检查不判层，埋孔(In2/In6)被拿来与 F.Cu SMD pad 比 ⇒ 13 个假阳性 | 假阳性 | `via(57.4,42.9)[In2,In6]` 正压 J3 B12-B15 pad 但无共层 |
| 4 | 豁免过宽：豁免「本页 4 pad」含**对侧极性 conn pad**，掩盖同页 P/N 之间的接入侵入 | 假阴性 | shop DRC `DN_OUT5_P × J4 A6[DN_OUT5_N] 0.0582` 被漏 |

修正（copper 模式）：真值 `seg_rect_gap`（含相交判定 + 非相交段端点最小距）+ `"F.Cu" in ls` 层判 +
按段落点极性收紧豁免（自有 conn pad + 芯片 pad）。

## 2. 修正后真缺陷（6 条，全在 J4 pad 场；`m13_v57_co25_pad_clearance_audit_copper.json`）
| 页面 | pol | 铜距 mm | shop DRC 对应 |
|---|---|---|---|
| `PCIE_DN4/out_MCIO` | P / N | **-0.0833** | `shorting_items` DN_OUT4_P × DN_OUT4_N（J4 A2 侧） |
| `PCIE_DN5/out_MCIO` | P / N | **0.0582** | `clearance` A6[DN5_N]×DN5_P / A7[GND]×DN5_N（**逐值同**） |
| `PCIE_DN6/out_MCIO` | P / N | **-0.0833** | mask bridge DN_OUT6 P×N（同区） |
⇒ 均为 `y=60.2 → 61.45` 的 0.9mm 斜向接入段（`#fcu_pad`），斜穿邻 pad。
**修正方向（下一周期几何）**：改为「45° + 竖直」狗腿，竖直段落在 pad 自身 x ⇒ 邻 pad 铜距 ≈0.3475（≥0.075 与 ≥0.175 均满足）；
仅动 3 页 F.Cu 接入段，不动 via/lane（L2）。

## 3. D3c 自裁（L2，非 L1）
shop DRC（`k2_v4_8L.kicad_pro`：PCIe85 0.175 / POWER 0.2，无 `.kicad_dru`/rule area）与**冻结 SPEC** `escape_transition_zone`（ECN-001）
不一致：0.4mm 节距接入段 0.175 铜距**物理不可行**（需 0.555 包络）。此项**不属 L1**（非拓扑/接口/信号流向/电源域/球重映射）⇒ **自裁，不停 owner**：
**裁定 (a)**：以**版本化 `*.kicad_dru` 规则域**实现 SPEC 已冻结的逃逸区（铜距 0.075），scope = J2/J3/J4/U6 pad 场矩形；
域外维持 0.175/0.2。性质 = **实现 SPEC**，非放宽 SPEC（SPEC 明文 `escape_clearance_mm: 0.075`，且 2026-08-16 已冻结）。
落地放在下一周期（改动 DRC 判据须与 L5 signoff 同批版本化 + 变更单，避免与几何混批）。

## 4. 未决（下一周期顺序）
1. **上游**：`m13_v57_CO25_upstream_change_request_W0R_refclk_keepout.md`（D3a 的模型输入缺口，禁暴力迭代）；
2. **D3b 几何**：3 页（DN4/5/6 out_MCIO）接入段改狗腿（消 6）；
3. **D3a**：W0-R 补齐后重导 refclk（消 60）；
4. **D3c**：落 `.kicad_dru` 规则域 + L5 signoff 同批版本化；
5. 全链 G4→G7 → new=0 → milestone tag。

## 5. 红线 / 未改物
未改四冻结源（`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`）、未改 `k2_v4_8L.kicad_pro`、
未改引擎、未改任何板/图纸/ALLOC/引擎产物；几何零改动；引擎 AST `while=0`。

## 6. 追加（D3b 修复**位点**更正 + 设计，2026-09-12 同会话后段）
§4 第 1 项把修复位点写成「引擎接入段构造」——**不成立**。实测：
- `co16_prepare()`（引擎 L345-351）**用 alloc 工件覆写**引擎 r3 的 `column_x`/`landing`（`r3["assignment"][k]["column_x"] = fp(lx)`，`lx,ll = a["landing"][pol]`）；
- 验证器 G-M4（`p3_v57_w3_constructive_validator_v2.py` L466-471）逐页断言 `column_x == alloc.landing[pol][0]`（容差 1e-6）。
⇒ 引擎**必须 O(1) 消费 alloc 的落列**，不得自行改列。**D3b 的修复位点在 alloc 生成器**（`p3_v57_co16_emit_allocation.py` + 探针 `_pair_lands`/列派生），须出 **CO16-ALLOC.5** 后重发引擎图纸。

### 6.1 缺陷精确定位（实测最劣 pad，段 = `#fcu_land` F.Cu）
| 页面 | pol | 段（landing→pad） | 自身 pad | 最劣外来 pad | 铜距 mm |
|---|---|---|---|---|---|
| `PCIE_DN4/out_MCIO` | P | `(53.2,60.2)→(54.7,61.45)` | 54.7 | **J4 A1**(54.1, GND) | **-0.0833** |
| `PCIE_DN4/out_MCIO` | N | `(53.8,60.2)→(55.3,61.45)` | 55.3 | **J4 A2**(54.7, 本页对侧 P) | **-0.0833** |
| `PCIE_DN5/out_MCIO` | P | `(57.4,60.2)→(56.5,61.45)` | 56.5 | **J4 A6**(57.1, 本页对侧 N) | **0.0582** |
| `PCIE_DN5/out_MCIO` | N | `(58.0,60.2)→(57.1,61.45)` | 57.1 | **J4 A7**(57.7, GND) | **0.0582** |
| `PCIE_DN6/out_MCIO` | P | `(60.4,60.2)→(61.9,61.45)` | 61.9 | **J4 A13**(61.3, GND) | **-0.0833** |
| `PCIE_DN6/out_MCIO` | N | `(61.0,60.2)→(62.5,61.45)` | 62.5 | **J4 A14**(61.9, 本页对侧 P) | **-0.0833** |
结构：落列 `lx` 与 pad 列错位（DN4/6：−1.5；DN5：+0.9），F.Cu land 斜穿邻 pad。可用 y 跨度仅 `61.45-60.2=1.25 < 1.5`。

### 6.2 两个候选闭式规则（已算）
1. **仅改接入段狗腿（lx 不动）**：DN5（|dx|=0.9 ≤ 1.25）45°+竖直 ⇒ 邻 pad 铜距 **0.3475 ✓**（SPEC 与 shop 均过）；
   DN4/DN6（|dx|=1.5 > 1.25）只能 45° 后于 pad 行水平切入 ⇒ 最劣铜距 **≈0.0975**（≥SPEC 0.075 ✓，<shop 0.175 ✗，落 D3c 域）。⇒ 只消 DN5 的 2 条。
2. **落列对齐（推荐，alloc 层）**：西侧 MCIO 数据页取 `column_x = conn_pad.x`（land F.Cu 变为**竖直**）⇒ 邻 pad 铜距 **0.3475 **（≥0.075 且 ≥0.175，全 6 条同时满足）。
   连带核验：列距变 0.6 ⇒ via-via 中心距 0.6 ≥ 0.525 ✓；In2 竖 stub 间距 0.6 ⇒ 铜距 0.395 ✓；In2 水平 lane 端点随之平移（P/N 分别在 y=42.9/43.4，不同 y，不并线）。
   ⇒ **采用 2**；须在 ALLOC.5 重派生列 + 重跑 G-M4/等长/crossing 全链。

## 7. 追加（CO-26：D3b 根因定死 + 一条解法**实测否决**，2026-09-12 同会话第四段）
### 7.1 根因（实测，非推测）
西侧 fan（`p3_v57_co10_west_fan_probe.r3_build`）：
- 落列初值 `lx = pad_x - 0.3`（J3/J4 统一，FAN_DX 全 0）⇒ 天然 dx = **+0.3**（安全：邻 pad 铜距 ≈0.1975）。
- **`FAN_Y` 按 (ref,侧) 共享**（J3/U 34.5、J3/L 51.5、J4/U 60.2、J4/L 65.0），而 J3 与 J4 是同一 x 栅格的 MCIO ⇒ **两连接器的自然列完全重合**。
- `GS_IN2` 现状（`CO10_STUB=J3L`）：In2 承载 **J3/U + J3/L + J4/U = 12 页**；`_lx_separate` 只能按
  `d ∈ {0, ±0.6, ±1.2, …}` 整页平移避让 ⇒ 实测 dx 直方图 `{+0.3, -0.9, +1.5, -2.1}`。
  `dx=±0.9` ⇒ 铜距 0.0582；`dx=+1.5` ⇒ **-0.0833（重叠）** —— 即 6 条真缺陷的成因。
  （`dx=-2.1`(UP2) 实测不越限：J3/U 该段旁无邻 pad。）

### 7.2 解法「在 `_lx_separate` 候选验收里加 pad 铜距谓词」——**实测否决**
已实现并实测（探针临时补丁，随后**已还原**）：候选 `d` 除列避让外还须使该页 F.Cu land 对**外来 pad** 铜距 ≥ ESC(0.075)
（复刻 CO-25 真值口径：相交判定 + 非相交段端点最小距）。
结果：**落位数 32 → 29**，`PCIE_DN1/DN2/DN3 out_MCIO` 变为不可落位。⇒ 现有列平移对**其它约束是承重的**
（via/lane/交叉/间距），单加谓词 = 把问题推成不可行。**故该解法作废，勿重试。**

### 7.3 D3b 唯一可行方向（CO16-ALLOC.5）
必须**打破「同侧共享 FAN_Y + 同层 stub」**这一前提，二选一（均 L2）：
1. **per-page 落位 y 错开**（同侧内各页 y 相差 ≥ VV 0.525）⇒ 各页可各用自身 pad 列（自然 dx=+0.3）；
2. **西侧 4 组 (J3U/J3L/J4U/J4L) stub 分层**（In2/In6/B.Cu，必要时配合 1）⇒ 两连接器 stub 不再争同列。
需同批复核：via-via ≥0.525、In2/In6/B 与 lane 的 crossing=0、`hole_to_hole`（同网 ≥0.4495）、A-CN.9 全间距、O4 等长/crossing ≤ 现值。
**禁止**以坐标搜索替代（探针候选阶梯是闭式常量表，保持 `while` 无坐标搜索）。

### 7.4 复现口径补记
`CO16_OUT` 用绝对路径、`CO16_VERIFY` 须用**相对名**（脚本做 `STEP2 / VERIFY_NAME`）。
按 ALLOC.4 旋钮重发射：`pages/config/inputs_sha16/verification` **与盘上 ALLOC.4 逐字节一致**；
仅 `supersedes.reason` 因未传 `CO16_SUPERSEDES_REASON` 而不同（文档字段）。⇒ 复现/比对须传该 env。

## 8. 追加（CO-27：stub 分层解法**全组合实测否决**；D3b 收敛为「per-page 落位 y 重派生」）
对 `GS_IN2`（西侧 4 组 stub 层）做**全 6 种分组**离线实测（探针临时改默认值，**已还原**；其余旋钮 = CO-23 口径）：
**[更正，见 §9.1]** 首版表格有 2 处数据错误（首行直方图取自「加谓词」补丁版而非 CO-23 原版；且漏扫 CO-23 实际分组 (1,1,1,0)）。**全 16 组合**实测（CO-28）见 §9.1。
⇒ **除 CO-23 现状外无 32/32 解** ⇒ stub 分层不是可行杠杆；列平移对 via/lane/crossing 仍承重（与 CO-26 §7.2 同一结论）。

**D3b 收敛（CO16-ALLOC.5 必做）**：唯一未否决的杠杆 = **把 `FAN_Y` 由 (ref,侧) 共享改为 per-page 落位 y**（同侧内各页 y 相差 ≥ VV 0.525），
使各页 stub 的 y 区间互不重叠 ⇒ 各页可回归自身 pad 列（dx=+0.3，邻 pad 铜距 0.1975 ≥0.175）：
- 该路径**不改变**连接器分配/拓扑（L1 未动），属 L2（落列/过孔策略）；
- 必须同批验证：落位 y 仍在连接器 y 带内且不压 pad 行；via-via ≥0.525；In2/In6/B 与 lane crossing=0；
  `hole_to_hole` 同网 ≥0.4495；A-CN.9；O4 等长；并复核 `FAN_Y` 共享是否被其它构造步骤（lane/escape）隐式依赖。
- 若该路径同样无 32/32 解，则 D3b 属**架构级**变更（西 fan 列资源/层资源重分配），需升级为独立架构裁定。

## 9. 追加（CO-28：§8 表格更正 + per-page 落位 y 解法**实测否决**；D3b 判为架构级）
### 9.1 §8 表格更正（**全 16 组合**实测，探针临时改默认后已还原）
| J3U | J3L | J4U | J4L | 落位 | 西侧 dx 直方图 |
|---|---|---|---|---|---|
| 1 | 1 | 1 | **0** | **32/32 ✓（唯一）** | {+0.3: 20, -2.1: 2, -0.9: 6, +1.5: 4} ← **= CO-23 现状** |
| 1 | 1 | 0 | 0 | 28 | {+0.3: 22, -0.9: 6, +1.5: 4} |
| 1 | 1 | 1 | 1 | 28 | {+0.3: 14, -2.1: 6, -0.9: 6, +1.5: 4, +2.7: 2} |
| 1 | 0 | 1 | 0 | 26 | {+0.3: 20, -0.9: 8, +1.5: 4} |
| 0 | 1 | 1 | 0 | 30 | {+0.3: 24, -0.9: 4, +1.5: 4} |
| 其余 11 组 | | | | 22–26 | 含 -2.1/+2.7 等更劣 |
结论（更正后仍成立）：**唯一 32/32 分组 = CO-23 现状**；其 dx 中含 `-0.9`(6) 与 `+1.5`(4) ⇒ 6 条 land 缺陷正是该唯一可行分组的**必然副产物**。
（更正原因：首版首行直方图误取自 CO-26 的「加谓词」补丁版；且首版漏扫 (1,1,1,0)。）

### 9.2 per-page 落位 y 解法（§8 建议的唯一杠杆）——**实测否决**
实现：`FAN_Y` 由 (ref,侧) 共享改为 per-page，按 lane_y 序做**前缀递推**（`y_i = max(y_{i-1}+0.6, max(land_{i-1},lane_{i-1})+0.525)`，方向取可用空间侧），探针临时补丁（**已还原**）。
结果：**落位 32 → 27**，失败 `DN0/DN3/DN5/DN6 out_MCIO`、`UP0/input`。
根因（实测，非推测）：`WSWAP 1-11` 后 `PCIE_UP2/input` 的 lane_y = **45.25**，落在 J3 上排 pad 行(45.75)附近 ⇒
该页 stub 的 y 跨度 [34.5, 45.25] 长达 10.75mm；把同组其它页的 land_y 推出该跨度（不与其它 stub 相交）会撞进 pad 行
（递推实测把某页推到 **45.775 ≈ J3 A 排 45.75**）⇒ 不可行。

### 9.3 D3b 定级与结论
- 两个杠杆（**stub 分层**：16 组合唯一 32/32 就是现状；**per-page 落位 y**：27/32）**均已实测否决**。
- ⇒ 6 条 land 缺陷在当前「lane 平面 + 共享落位带 + 3 可用 stub 层」架构下是**结构性必然**。
- D3b 归为**架构级**（西 fan 的**列资源/层资源/落位拓扑**需重派生，可能连带动 via 数与层使用）。
  仍属 L2（走廊分配/过孔策略，非 L1），但工作量与影响面 = 独立架构周期，**不由本会话强推**（避免半改状态）。
- 建议下一周期先做**离线架构枚举**（列资源 ≥ 每层 8 列且 |dx|≤0.3，或引入第 4 个 stub 层/改 lane 平面），再一次性落地。

### 9.4 红线
探针已还原、工作树 clean；未改冻结四源 / 未改 `k2_v4_8L.kicad_pro` / 未改任何板/图纸/引擎产物；几何零落地。

## 10. 追加（CO-29：land 45°狗腿**部分有效**；缺陷 6→2，剩 DN4/DN6 为硬核）
### 10.1 实测（探针临时补丁，**已还原**）
把 `#fcu_land` 由直线改为 **45°+竖直** 狗腿（`(lx,ll) → 45° → (px, ll+|dx|) → (px,py)`；`|dx|>可用竖直空间` 时余量水平于 pad 行），
**仅对西侧 (J3/J4) 且 |dx|>0.6 的页生效**（J2 侧与对齐页保持直线）：
| 作用域 | 落位 | CO-25 copper audit |
|---|---|---|
| 全页（无 guard） | 23/32 ✗ | — |
| 西侧 only（无 |dx| guard） | 23/32 ✗ | — |
| **西侧 ∧ \|dx\|>0.6（推荐形态）** | **30/32**，失败 `DN4/DN6 out_MCIO` | **0 违规（PASS）** |
⇒ 狗腿把 6 条 land 缺陷中 **4 条**（DN5 P/N 及其同类）转为合规（DN5 可达铜距 0.3475），
且**不改列**（placement/verification 的其余不变）。
**残余 2 条 = `DN4/DN6 out_MCIO`（|dx|=1.5）**：可用竖直空间仅 `61.45-60.2=1.25`，45° 不能覆盖；
补水平段需在 pad 行内滑动 ⇒ 探针 `check()`（`TT_E = WID+ESC = 0.28` **中心距** = 铜距 0.075，**量纲正确**）正确拒收（实测中心距 0.2 < 0.28）⇒ 该 2 页**不可落位**。

### 10.2 结论（收口）
- 狗腿 = **有效的部分解**（应采纳：消 4/6，且无副作用），**但不足以闭环**：`DN4/DN6` 的 `|dx|=1.5` 是硬核。
- 该 2 页的可用 d 里 `0`/`+0.6`（⇒ dx=+0.3/-0.3，直线即合规）被 `_lx_separate` **列冲突**拒（J3U 同层同 y 带占列），
  `-0.6`（⇒ dx=+0.9，狗腿可解）亦被拒 ⇒ 只剩 `-1.2`（⇒ dx=+1.5，不可解）。
- ⇒ **结论仍为架构级**（与 §9.3 一致），但已**收窄到 2 页 × 2 pol**：
  下一周期只需为 `DN4/DN6 out_MCIO` 找到 1 个可用列（dx ∈ {+0.9, +0.3, -0.3} 且不与 J3U 冲突）或 1 个可用落位 y；
  若仍无解 ⇒ 需为 J3U 与 J4U 分列（列资源/第 4 stub 层）⇒ 正式架构裁定。
- **落地建议（下一周期一次完成）**：①`#fcu_land` 狗腿（西侧 ∧ |dx|>0.6，probe geom + 引擎同一规则）
  ②为 DN4/DN6 定点补 1 列/1 y ③重射 ALLOC.5 + 引擎 rev → G4..G7。

### 10.3 红线
探针已还原、工作树 clean；未改冻结四源 / 未改 `k2_v4_8L.kicad_pro` / 未改板/图纸/引擎产物；本批几何零落地。

## 11. 追加（CO-30：残余 2 页= **列槽不可行**，附计数证明；D3b 判为**层预算/车道面**级）
### 11.1 证明（In2 组 = J3U(4 页)+J4U(4 页)，两连接器 pad 列**完全相同**）
约束（均由前文实测/规格导出）：
1. 合法 stub 列 = `pad ± 0.3` 的 0.6 格点（pad 中心不可用：异网短路）；
2. 每页需 **2** 列（P/N 相距 0.6，且须为格点）；
3. land 需 `|dx| ≤ 0.9`（否则 45° 狗腿在 `61.45-60.2=1.25` 的竖直空间内够不到 pad，见 §10.1）；
4. 两连接器 pad 的 x 完全相同 ⇒ 8 页争夺同一批格点。
计数：4 个 pad 对（54.7/56.5/61.9/63.7，邻距 1.2/5.4/1.8）在 `|dx|≤0.9` 内的合法格点共 **14 个**，
而需求 = 8 页 × 2 = **16 槽** ⇒ **无冲突分配不存在**（穷举验证：`存在 16 槽无冲突分配 = False`）。

### 11.2 结论（D3b 定级）
⇒ `DN4/DN6 out_MCIO` 的 land 缺陷**在「In2 同时承载 J3U+J4U」的现状下不可能消除**，与 §8–§10 的三条否决一致。
要素顺序（按代价）：
- **A（车道面）**：改 lane 平面使 J3U 与 J4U 的 stub y 区间不再重叠 ⇒ 两组可共享列（L2，但触及走廊/车道派生，全链重跑）。
- **B（层预算）**：为两组之一提供第 4 个 stub 层（现 In2/In6 之外；B.Cu 已被 escape 占用）⇒ 触及 **LID.1 8L 层意图**（L2 叠层分配，需全链+层意图派生复核）。
- **C（拓扑）**：J3/J4 的 refclk/数据列的球/pad 分配重排（**L1，需 owner**）。
优先序建议：**先 A**（改动面最小、不动 L1）；A 不可行再评估 B；C 仅在 A/B 均不可行时提请 owner。
### 11.3 红线
本节为纯离线计数/推理，**未改任何文件**（探针、引擎、板、图纸、判据均未动）。

## 12. 追加（CO-31：计数证明**泛化**到任意分组 ⇒ D3b 需层资源决策）
实测（alloc 工件）：西侧 4 组的 pad-pair **x 位置互有重叠**——
J3 用 `{54.7/55.3, 56.5/57.1, 61.9/62.5, 63.7/64.3}`（两行 y=43.25/45.75，**P/N 极性与 J4 相反**），J4 用同一批 x（两行 y=61.45/63.95）。
⇒ 单组 4 页占满该组 8 个自然列（每页 2 列）；**任一层承载 2 组 ⇒ 16 槽 > 邻近可用列（≤14）⇒ 不可行**（§11.1 已穷举 16>14）。
⇒ 由 CO-28 的 16 组合扫描（唯一 32/32 = In2 承载 3 组）+ 本节 ⇒ **LID.1 现有信号层预算（F/In2/In6/B）下 D3b 无解**：
必须为 4 组各配 1 个 stub 层（含 F 或 B），或改 pad 分配（L1）。
- **F 作 stub 层**：与 F.Cu pad-access/escape 冲突（每页都有 F.Cu land）⇒ 需逐页几何核验；
- **B 作 stub 层**：与 dn-escape（`ESC_MAP: WEST dn→B.Cu`）及 J2 侧 run 争用；
- **In1/In3/In5(GND)、In4(P3V3)**：红线禁改。
**定级**：**B' = 层资源重分配（F/B 之一作第 3/4 stub 层）属 L2（叠层分配/过孔策略）但触及 LID.1 层意图**，须版本化层意图重派生 + 全链重跑；
**C = pad/球分配重排属 L1**。建议下一周期：先做 B' 的**离线可行性枚举**（F/B 作 stub 层 × 4 组分配 × 列槽计数），有解再落地。

## 13. 追加（CO-32：4 层 stub 分配 **消列冲突成功**（dx 全 +0.3），但 6 页落位受阻）
实测（探针临时补丁 `_STUB4`，**已还原**）：把 4 组各配 1 个 stub 层
`{J3U→In2.Cu, J3L→In6.Cu, J4U→B.Cu, J4L→F.Cu}`：
| 指标 | 结果 |
|---|---|
| 西侧 dx 直方图 | **{+0.3: 32}** ⇒ **每页回归自然列**；land 仅 0.3 偏移（铜距 ≈0.1975 **≥ shop 0.175**）⇒ **6 条 land 缺陷全部消失** |
| 落位 | **26/32**，失败 `DN0/DN1/DN2/DN3 out_MCIO`（=J3L 组）、`UP0/UP2 input`（=J3U 组） |
⇒ 结论转换：**列资源问题已被 4 层分配解决**（计数矛盾解除，dx 全自然）；**新阻塞 = J3 两组的落位**（列变自然后 stub/escape/lane 交互失败），
**与 land 几何无关**（land 已 shop-clean）。J4 两组在 B/F 上未失败。
**下一周期（明确、有界）**：打印探针 `failed[page]["reasons"]` 定位 J3 两组（DN0-3 / UP0 / UP2）的失败谓词 →
按需微调 J3 两组的 escape 层（`ESC_MAP` 现 WEST up→In2 / dn→B.Cu）或落位带 → 期望 32/32；
随后 land 保持直线（dx=+0.3 已合规，**无需狗腿**）⇒ 直接结算 D3b（消 6/6）。
**层意图**：占用 B/F 作 stub 属 LID.1 变更（L2：叠层分配/过孔策略）⇒ 须版本化层意图 + 全链重跑；In1/In3/In5/In4 红线未动。

## 14. 追加（CO-33：J3 组失败根因 = **In2 lane-end via 间距**，与列/land 无关）
探针临时补丁（已还原）打印 `failed[page]["reasons"]`：
- `DN0/DN1/DN2/DN3 out_MCIO`（J3L 组）：`vt_placed` **距离 0.0**（via 正压他页 In2 lane）+ `vv_placed` 0.493；
- `UP0/UP2 input`（J3U 组）：`vv_placed` 0.500 / 0.522；
- 失败项**全部**指向 `(x, lane_y, pol, "In2.Cu")` 的 **lane-end via** vs 他页 In2 lane/via 间距（需 ≥0.525）。
列偏移实验：`FAN_DX(J4)=+0.6 / -0.6` ⇒ dx = `{+0.3,-0.3}` / `{+0.3,+0.9}`（**全 shop-clean ≥0.175**），
但**落位仍 26/32 且失败页完全相同**（DN0-3/UP0/UP2）⇒ **J3 组失败与 J4 列无关**。
⇒ 结论：
1. **J3L 不能上 In6**（与本仓 CO-23 选择 `CO10_STUB=J3L` 一致）：即使 stub 换层，**lane-end via 仍在 In2**，必须与他页 In2 lane 保持 ≥0.525。
2. ⇒ 真正的约束是 **(列 x, lane_y) 联合间距**，不是 stub 层或 land 形状。CO-32 的「4 层 ⇒ dx 全自然」只解了 stub 列，未解 via。
**下一周期（有界、明确）**：对 J3 两组做 **(列 x, lane_y) 联合派生**（闭式：保证每 via 与他页 In2 lane/via ≥0.525，允许 column 离开 pad 列而用 land 狗腿补偿）
⇒ 目标 32/32 且 dx ∈ {+0.3,-0.3}（shop-clean）⇒ D3b 消 6/6；随后 ALLOC.5 + 引擎 rev + G4→G7。

## 15. 追加（CO-34：碰撞对 = J4 页的**竖直 In2 段** vs J3 页的 lane-end via；列需交错）
实测（4 层配置，探针临时补丁已还原）：
- `PCIE_DN7/out_MCIO` N：In2 竖直段 `(64.0, 35.0) → (64.0, 60.2)`；
- 失败 via `(64.0, 41.3, 'P')` 正落在该竖直段上（dist 0.0）⇒ **J3 页的 lane-end via 与 J4 页的竖直 In2 段 x 重合**。
- 同类：DN4 P `(54.4, 41.85)→(54.4, 60.2)` / N `(55.0,42.35)→(55.0,60.2)`（自 4 层配置起该竖直段仍在 In2）。
- `FAN_DX(J4)=±0.6`（使 dx 交错为 `{+0.3,-0.3}`，**全 shop-clean**）后**失败页与坐标不变** ⇒ 该竖直段的 x **不由 FAN_DX 控制**
  （4 层配置下 J4 的 In2 段位置另有来源：lane-end/escape 链的 `vx`）⇒ 必须**联合**派生 (J3 via x, J4 In2 段 x)。
**下一周期（收官步骤，明确）**：
1. 定位 4 层配置下 J4 In2 竖直段的 x 来源（`vx`/escape 链），确认其与 FAN_DX/column 的耦合关系；
2. 联合派生使 **两连接器的 In2 竖直段与对方 lane-end via 的 x 差 ≥ 0.525**（可借 column + FAN_DX + land 狗腿补偿）；
3. 目标 **32/32 且 dx ∈ {+0.3,-0.3}** ⇒ D3b 消 6/6 ⇒ ALLOC.5 + 引擎 rev + G4→G7。

## 16. 追加（CO-36：D3b **收官** — connector 落列器改「land 段长升序」；32/32 + shop-clean；DFM new 73→65）
> 2026-09-12｜裁定：ARCHER（续接会话，独立复核 + 落地 gate 链）｜性质：**L2 自裁落地**（落列/过孔策略）
> §13–§15 的「4 层 stub / 联合派生 (J3 via x, J4 In2 段 x)」路线**不再需要**：本解**未动 LID.1 层意图、未动 stub 分组**（仍为 CO-23 同款 `CO10_STUB=J3L`：In2 承载 J3U+J3L+J4U、In6 承载 J4L）。

### 16.1 根因（闭式，非搜索）
`_lx_separate` 的页处理次序原为 `(stub 层, lane_y, page)`；先处理者先取自然列（`d=0`），后处理者被整页平移 `±0.6k`。
connector land 段（`#fcu_land`：`landing (lx,ll) → conn pad`）对 |dx|（= |lx − conn_pad.x|）的铜距敏感度 ∝ **段长倒数**：
- 短段（J4U 1.25mm / J4L 1.05mm）：斜度大 ⇒ |dx| 越大，段身越扫过邻 pad；实测 |dx|=0.3→铜距 **+0.2534**、0.9→**+0.0582**、1.5→**−0.0833**；
- 长段（J3U 8.75mm / J3L 5.75mm）：近竖直 ⇒ 在焊盘行处已收敛到 conn_x ⇒ 可吸收较大 |dx|（实测 |dx| 至 1.5 仍 ≥0.175）。
⇒ **短 land 段组优先取自然列，长 land 段组吸收列偏移**（`CO10_LXPRIO=landlen`，默认关 = 旧行为）。

### 16.2 变更（ALLOC.4 → ALLOC.5，仅 6 处 `landing` 字段）
| 页面 | ALLOC.4 landing P/N | ALLOC.5 landing P/N | dx(P) |
|---|---|---|---|
| `DN1/out_MCIO`(J3L) | 62.2 / 61.6 | **61.0 / 60.4** | +0.9 |
| `DN2/out_MCIO`(J3L) | 56.8 / 56.2 | **58.0 / 57.4** | −1.5 |
| `DN3/out_MCIO`(J3L) | 55.0 / 54.4 | **53.8 / 53.2** | +0.9 |
| `DN4/out_MCIO`(J4U) | 53.2 / 53.8 | **54.4 / 55.0** | **−0.3（自然列）** |
| `DN5/out_MCIO`(J4U) | 57.4 / 58.0 | **56.2 / 56.8** | **−0.3（自然列）** |
| `DN6/out_MCIO`(J4U) | 60.4 / 61.0 | **61.6 / 62.2** | **−0.3（自然列）** |
其余 26 页（含 J4L、J3U、东侧、refclk）**逐字节不变**；`config`/`inputs_sha16` 仅新增 `CO10_LXPRIO=landlen`。

### 16.3 量（实测）
| 指标 | CO-23（ALLOC.4） | CO-36（ALLOC.5） |
|---|---|---|
| 落位（探针 `check` 全谓词） | 32/32 | **32/32** |
| CO-25 真值 pad 铜距（`CO11_PAD_UNITS=copper`） | **6 违规**（−0.0833 / 0.0582 / −0.0833） | **0 违规**（该 6 页最劣 **+0.2534**；全 32 页最劣 +0.1211 ≥ SPEC 0.075） |
| 落位/复核 320 via + 320 段 | 0 违规 | **0 违规**（centerline 与 copper 双口径均 PASS） |
| 层意图（LID.1 8L） | F/In2/In6/B（stub: In2×3 组 + In6×1 组） | **同上（未变）** |
| DFM new（shop `k2_v4_8L.kicad_pro`） | 73 | **65** |

### 16.4 独立复核（本会话重放，非信任上游）
- **几何阶段**（ALLOC.5 + probe 补丁 + `co36_*` 复核件）系中断会话遗留于工作树的未提交产物；本会话**逐字节重放**后收口：ALLOC.5 `0bf6cdc203887a48`、geom `6610557070a37960`、verify `add6f9918a17ea3d`、copper audit `03fad029e6709f28`（均与盘上一致）。
- **旧证据保真**：ALLOC.4 按原旋钮重发射仍 `e5d30cd4eac83e16` 逐字节同（仅 `supersedes.reason/revision` 文档字段，因未传 `CO16_SUPERSEDES*`）；t2 默认路径重跑仍 `c2d201f030b49efd`（既有偏差 #1 未变）；冻结四源 4/4 MATCH；引擎 AST `while=0`。
- **逐对 DRC 差分**（CO-23 L4 板 = `git HEAD:k2_v4_8L.l4.kicad_pcb` `70f3fdc4149db146` vs W3-CN.38 L4 `5e8d88d405126014`，同一 `kicad-cli 10.0.5` 口径，含位置键）：
  **消 14 / 增 6，净 −8**，且：
  1. **消 8 = D3b 全部数据件**：`DN4 P×N` shorting、`DN4_N 盲孔 × DN4_P` clearance、`DN5_N×GND` 与 `DN5_P×DN5_N` clearance、`DN4_P×GND`/`DN4_P×N`/`DN6_P×GND`/`DN6_P×N` mask bridge ⇒ J4 焊盘场 **数据件 0 残留**；
  2. **消/增各 4 = 同一 REFCLK 冲突点随 land 列平移**（`DN1 P/N × REFCLK0_N` crossing、`DN6 P/N × REFCLK1_P` shorting：类型与网对不变，位置随 landing 由 62.2/61.6↔60.4/61.0、60.4/61.0↔61.6/62.2 平移）；
  3. **消/增各 2 = J2 逃逸区 REFCLK 报类重归属**（`REFCLK*_N (28.243mm) × J2 pad 14/32 [UP_OUT*_P]` clearance ↔ `× J2 pad 11/29 [REFCLK*_P]` shorting）。**已证 REFCLK 铜几何两版完全相同**（18 基元逐项一致）⇒ 报类差异来自 KiCad 分组/归属，**非新缺陷**。
- **归因计数闭合**：13 → 5 数据/其他（= 8 条 D3b 消）；REFCLK 族 60 = 11 仅 REFCLK + 49 REFCLK×数据（与 D3a 口径一致）。
- **新增 D3a 证据**（供上游变更单）：J2 `REFCLK0_P` pad 11 与 `REFCLK0_N` 逃逸段（`(135.0,46.09)→(106.757,46.09)`）真值铜距 **−0.0875mm（实铜重叠）**，`REFCLK1_P` pad 29 同值；两版板相同 ⇒ 既有缺陷，非本批引入。

### 16.5 gate 链（W3-CN.38，ALLOC.5 消费）
| 门 | 判定 | 证据（sha16） |
|---|---|---|
| G4/W3 | **FEASIBLE_ALL** | 引擎 `W3-CN.38`：canonical `0261e0b0a598df6d`（certs=0, crossings 0/0, work 546/546, A-CN.1..9 全 PASS）；landing `6a42a329a0e75a31` |
| G5/W4 | **PASS** | `m13_v57_w3_validation.json` `b0ff500448e7b54b`（W3-VALv2.4；G-M1..6 全 True）＋ A1.2 序无关 `454df5b5abb905ee`（三枚举序同 sha） |
| G6/L4 | **PASS** | `m13_v57_l4_construction.json` `512192df1f1e8f84`（68 网/2408 段/248 via）；`m13_v57_l4_validation.json` `efc07c52a93c08a4`（L4-A..E viol=0）；板 `k2_v4_8L.l4.kicad_pcb` `5e8d88d405126014` |
| G7/L5 | **SI PASS / DFM FAIL** | SI `03cc5b67430fb3e8`（skew 0.0031 ≤0.15）；fab `3b91202b1e5dd1a4`；dfm `9f7158f2634df815` = **new 65**（`clearance 13` / `tracks_crossing 5` / `shorting 9` / `mask 38`），`copper_edge 0` / `hole_to_hole 0`；`m13_v57_l5_g7_record.md` `3830f8f6db0f7c14`（L5-G7.4，本会话重写至 W3-CN.38/new=65 口径） |

### 16.6 未决（下一周期）
1. **D3a（60，REFCLK 族）**：仍需上游 W0-R 见证件补齐（版本化）+ 引擎 `refclk_place()` 修订（见 `m13_v57_CO25_upstream_change_request_W0R_refclk_keepout.md`）；**本批新增证据**：J2 侧 REFCLK P pad × N 逃逸段实铜重叠 −0.0875（连接器侧接入窗口缺陷，须并入该变更单 scope）。
2. **数据/其他 5**（J2 pad 19[GND]×UP_OUT4_N、J2 pad 70[DN6_N]×DN7_P、J2 pad 71[GND]×DN7_N、J2 pad 16[GND]×UP_OUT3_N、R3 pad 2[PWR_BTN_ISO]×UP3_N）：非 D3b（非 J4 land 场），留待 D3c 域判定后处置。
3. **D3c**：`.kicad_dru` 规则域（SPEC 逃逸区 0.075）+ L5 signoff 同批版本化（CO-25 §3 自裁，L2）。
4. 全链 G4→G7 重跑 → `new=0` → milestone tag（`pm_gate/TAG_POLICY.md`）。

### 16.7 红线 / 指纹
未改四冻结源（`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`）、未改 `k2_v4_8L.kicad_pro`、
未放宽 `intra_pair_skew_mm`/净距阈值、未动 GND/PWR 平面（In1/In3/In5=GND、In4=P3V3）、未改 pad/球分配（**L1 未动**）。
引擎 AST `while=0`；`_lx_separate` 仍为**闭式候选表 + 单遍首可行**（仅改页次序，无坐标搜索/无回溯）。
复现：
```
CO16_REV=CO16-ALLOC.5 CO16_OUT=<abs>/…_v5.json CO16_VERIFY=m13_v57_co36_placement_verification.json \
CO16_SUPERSEDES=CO16-ALLOC.4 CO16_SUPERSEDES_REASON="<见工件>" \
CO16_STEP=1.449 CO16_EDELTA=-0.10 CO16_WLO=33.70 CO16_WSTEP=1.05 CO16_FANY_J3=34.5,51.5 CO16_STUB=J3L \
CO16_POLMODE=lx CO16_EASTSPLIT=in2c CO16_J2STEP=0.58 CO16_COLMODE=pol CO16_WSWAP=1-11 CO16_HOLE_GAP=0.4495 \
CO16_LXPRIO=landlen CO16_PAIR=m13_v57_f13_r1_pair_coupling_v1_5.json python3 tools/p3_v57_co16_emit_allocation.py
python3 tools/p3_v57_w3_constructive.py --r1-5-shape co16          # ⇒ W3-CN.38 0261e0b0a598df6d
python3 tools/p3_v57_w3_constructive_validator_v2.py
AppDir/bin/python3.11 tools/p3_v57_l4_apply_drawing.py --board && AppDir/bin/python3.11 tools/p3_v57_l4_validator.py
AppDir/bin/python3.11 tools/p3_v57_l5_signoff.py                    # ⇒ DFM new=65
```
指纹：ALLOC.5 `0bf6cdc203887a48`｜CO-36 geom `6610557070a37960`｜CO-36 verify `add6f9918a17ea3d`｜CO-36 copper audit `03fad029e6709f28`
｜W3-CN.38 `0261e0b0a598df6d`｜landing `6a42a329a0e75a31`｜W4 `b0ff500448e7b54b`｜L4 `512192df1f1e8f84` / 板 `5e8d88d405126014`
｜fab `3b91202b1e5dd1a4`｜dfm `9f7158f2634df815`｜si `03cc5b67430fb3e8`

## 17. 追加（CO-37：D3c **落地** — SPEC 逃逸区规则域（`.kicad_dru` + 板内具名 rule area）；DFM new 65→60；残余 = 100% REFCLK）
> 2026-09-12｜裁定：ARCHER（续接会话）｜性质：**判据实现**（L2 自裁；实现冻结 SPEC `escape_transition_zone`/ECN-001，**非放宽**）｜**几何零改动**（canonical/landing/W4 指纹不变）

### 17.1 结论
以**版本化规则文件 + 版内具名 rule area**实现 SPEC `escape_transition_zone.escape_clearance_mm = 0.075`（域 = J2/J3/J4/U6 pad 场，F.Cu），
**并排除 REFCLK 网**（`SPEC.constraints.refclk_isolated=true`）。落地后 DFM `new 65 → 60`（稳定）；
**残余 60 条 = 100% `PCIE_REFCLK0/1` 路线族**（D3a）⇒ 里程碑路径唯一化：**只差 D3a 几何重派生**。
与前两版一致：`copper_edge 0` / `hole_to_hole 0`；`unconnected` 348 不变。

### 17.2 域与判据（全部版本化；零搜索）
| 件 | sha16 | 说明 |
|---|---|---|
| `m13_v57_co37_escape_domain.json` | `5616a9f873c9b844` | 域工件（CO37-ESC.1）：`ESC_J2` x[131.50,136.15] y[42.23,65.18]；`ESC_J3` x[53.45,65.55] y[42.40,46.60]；`ESC_J4` x[53.45,65.55] y[60.60,64.80]；`ESC_U6` x[82.10,105.34] y[49.11,58.29]（pad 场 bbox 外扩 `MARGIN=0.5mm`，层 = F.Cu）|
| `k2_v4_8L.l4.kicad_dru` | `3148703240d54420` | 规则：`(constraint clearance (min 0.075mm))` + `(layer "F.Cu")` + 条件 `(A∩域 ∨ B∩域) && !REFCLK(A) && !REFCLK(B)` |
| L4 板 rule areas | 4（非铜） | `ESC_J2/ESC_J3/ESC_J4/ESC_U6`，由 `p3_v57_l4_apply_drawing.py --escape-domain <工件>` 注入 |
| L5 判据输入 | — | `p3_v57_l5_signoff.py` 把 `.kicad_dru` 一并复制进 DRC 沙箱；**仅 `l4_applied` 适用**（冻结基线无 `.kicad_dru`）|
生成器：`tools/p3_v57_co37_emit_escape_domain.py`（域派生，闭式 bbox）与 `tools/p3_v57_co37_emit_dru.py`（规则文件发射，O(1) 消费域工件）。

### 17.3 域外/排除项（**不放宽**）
- **REFCLK 不享受放宽**（`refclk_isolated`；其冲突是外来布线侵入 pad 场 ⇒ D3a 几何缺陷）。实测：8 条 REFCLK clearance（含 `0.0600` 与 C82×REFCLK1_N `0.1755`）**全部保持违规**。
- 域外维持 shop/netclass（PCIe85 **0.175** / POWER **0.2**）；短接/交叉/阻焊桥类判据不变（放宽仅限 clearance 且仅在域内）。
- 量纲与制造：准入项实测铜距 **0.1211–0.1522mm**（≥ SPEC 0.075 且 ≥ JLC 线距极限 0.10）。

### 17.4 接受判据（实测，逐项；本会话执行）
1. **净效果**：`new 65 → 60`（域板连跑 2 次均 60；同旋钮无域重建板连跑 2 次均 65 ⇒ 差值 5 稳定）。
2. **恰好 5 条、0 新增**：逐对差分（含位置键）显示消 5 条 clearance = `J2 19[GND]×UP_OUT4_N_J2`、`J2 16[GND]×UP_OUT3_N_J2`、`J2 70[DN6_N]×DN7_P`、`J2 71[GND]×DN7_N`、`R3.2[PWR_BTN_ISO]×UP3_N`（全部为 pad 场逃逸段；非 REFCLK 对）。
3. **无越界清除**：无 `actual < 0.075` 项消失；无短接/交叉/阻焊桥项消失；`tracks_crossing 5` 与 `solder_mask_bridge 38` 不变。
4. **无新增违规**：域板 `unconnected` 348 不变；rule area 本身不产生 DRC 项。
5. **REFCLK 计数不变**（60）：其条目/报类归属随 KiCad 分组抖动（同一几何下 ±4，clearance↔shorting；已证 REFCLK 铜几何两版 18 基元逐项相同）。
6. **几何零改动**：canonical `0261e0b0a598df6d`、landing `6a42a329a0e75a31`、W4 `b0ff500448e7b54b`、probe 复核 `add6f9918a17ea3d`/`03fad029e6709f28` 与 CO-36 **逐字节同**。

### 17.5 附带发现（上游 SPEC 文本一致性，供 owner/SPEC 维护）
实测 pad 节距：**J2 0.6 / J3 0.6 / J4 0.6 / U6 0.5 mm**（pad 尺寸 1.3×0.35 / 0.3×0.7 / 0.3×0.3）；SPEC `escape_transition_zone.pitch_mm = 0.4` 与本板实测**不一致**（文本前提陈旧）。
但**结论仍成立**：0.6 节距 + 0.205 线宽的单边净距 = `0.6−0.3−0.205 = 0.095mm < 0.175`（U6: `0.5−0.3−0.205 = −0.005` 居中不可行 ⇒ 须错列逃逸）⇒ pad 墙内逃逸段**必然**落在 `(0, 0.175)` 区间，逃逸区 0.075 判据有实测依据。
建议：SPEC 文本把 `pitch_mm` 更正为实测值（或注明为「接入段包络」口径），以免后续会话据陈旧前提质疑/误用 D3c。

### 17.6 gate / 指纹（D3c 批次 = 判据批，几何指纹沿用 CO-36）
| 门 | 判定 | 证据 |
|---|---|---|
| G4/W3 | 不变（几何零改动） | `0261e0b0a598df6d` / landing `6a42a329a0e75a31` |
| G5/W4 | 不变 | `b0ff500448e7b54b` |
| G6/L4 | **PASS（重跑，板含 rule area）** | construction `d65cbcf8a993f2c5`（68/2408/248 + 4 rule areas）；validation `9bbb15fc88b2723f`（L4-A..E viol=0）；板 `9e6b4839669e941a` |
| G7/L5 | **SI PASS / DFM FAIL（new 60）** | `L5-DFM.3` `7790f0eb2f4c256b` = `clearance 8` / `tracks_crossing 5` / `shorting 9` / `mask 38`；`b572226abd5bb8ea`（fab）；`03cc5b67430fb3e8`（si）；`m13_v57_l5_g7_record.md` `6cb9b1a75778a1d9`（L5-G7.5）|

### 17.7 未决（下一周期）
1. **D3a（60，唯一残余）**：W0-R 见证件补齐（版本化）+ 引擎 `refclk_place()` 修订 → rev bump → 重跑 G4..G7 → `new=0` → **milestone**。
2. **数据/其他**：**0 残留**（CO-37 §17.4 已消 5/5）⇒ 该项关闭。
3. SPEC 文本更正建议：见 §17.5（`pitch_mm`）——不影响本批判据效力。

### 17.8 红线 / 复现
未改四冻结源、未改 `k2_v4_8L.kicad_pro`、未放宽 `intra_pair_skew_mm`；放宽仅限 SPEC 明文逃逸区（0.075）且**排除 REFCLK**、**仅随 L4 板**（冻结基线判据不变）；GND/PWR 平面未动；L1（拓扑/接口/流向/球重映射）未动。
```
python3 tools/p3_v57_co37_emit_escape_domain.py
python3 tools/p3_v57_co37_emit_dru.py
AppDir/bin/python3.11 tools/p3_v57_l4_apply_drawing.py --board \
  --escape-domain pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co37_escape_domain.json
AppDir/bin/python3.11 tools/p3_v57_l4_validator.py
AppDir/bin/python3.11 tools/p3_v57_l5_signoff.py      # ⇒ DFM new=60（clearance 8 全为 REFCLK）
```
指纹：域工件 `5616a9f873c9b844`｜`.kicad_dru` `3148703240d54420`｜L4 `d65cbcf8a993f2c5` / val `9bbb15fc88b2723f` / 板 `9e6b4839669e941a`
｜fab `b572226abd5bb8ea`｜dfm `7790f0eb2f4c256b`（new 60）｜si `03cc5b67430fb3e8`｜g7 `6cb9b1a75778a1d9`
