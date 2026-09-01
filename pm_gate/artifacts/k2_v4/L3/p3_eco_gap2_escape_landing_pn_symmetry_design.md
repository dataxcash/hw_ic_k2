# 设计说明 P3-ECO-2 — escape_landing P/N 对级对称约束（gap2 / skew 缺口）

> 卡：`p3_eco_gap2_escape_landing_pn_symmetry_card.md`
> 施工位置：`_shared/eda_core/escape_landing.py`
> 状态：**设计待 TASK MGR 复核**（先设计后施工，禁止直接打补丁）
> 铁律：SDD 驱动禁止事件驱动、问题回模型、冲突即停机、假成功零容忍

---

## 0. 设计结论（先看这个）

**卡面字面约束「同 region（GAP+GAP）」对同行对（P 左列 / N 右列同排）在现有
`_landing_escape` 焊盘桩几何下物理不可行**——实测 14 种 GAP 落点组合全部 INFEASIBLE，
交叉点恒为 P 的 via（[133.825, 51.3]），根因是 N 的 F.Cu 短桩（pad→via_x@pad_y）必然
穿过同行 P 的 via。

**实测唯一可行解：同行对 N 锚定 OUTSIDE 且行镜像（y_N = y_P ± row_pitch）**：
- REFCLK1：INFEASIBLE → **SOLVED**（真板全链路实测，非合成）
- 36/36 全锚定不回归（26 GAP + 10 OUTSIDE，region 分布不变）
- 确定性：pair 固定序 + P 先 N 后 + first-clear-wins

**因此设计约束定义为「P/N 对级对称（镜像行）」而非卡面字面的「同 region」**。
这是问题回模型（卡面约束与物理几何冲突，须 TASK MGR 裁决后施工）。

---

## 1. 现象与根因（P3-B 实测，勿重跑论证）

- REFCLK1（P pad [132.65, 51.3] 左列 / N pad [135.0, 51.3] 右列，同行）：
  P→GAP(133.825, 51.3)，N→OUTSIDE(136.0, 51.3) → solve INFEASIBLE
  「落点驱动逃逸 P/N 相向交叉（min 边缘距 -0.2050 < 0.175）」，交叉点 [133.825, 51.3]。
- 根因链：N 的 F.Cu 短桩 `_stub` = [pad, (via_x, pad_y), via]——N pad (135.0, 51.3)
  到 via 的水平段沿 y=51.3 行进，必穿过同行 P 的 via (133.825, 51.3) 与 P 的逃逸段；
  P 在 GAP、N 在 OUTSIDE 时两 In2 段收敛交叉。这就是「逐信号独立锚定无 P/N 对称」。

## 2. 设计约束定义（P/N 对级对称，镜像行）

对每个差分对（base），P 与 N 落点绑定为对称位置：

1. **跨行对**（P/N pad 行不同，如 UP0/UP2/…）：维持现状同 region（GAP+GAP，各自
   pad 行锚定，vpdist=row_pitch=0.6≥0.525）——已满足对称，不回归。
2. **同行对**（P 左列 / N 右列同排，10 对：UP1/3/5/7, REFCLK0/1, DN0/2/4/6）：
   - P（左列，仅 GAP 可达）锚定 GAP 于自身 pad 行（物理强制）。
   - N（右列）锚定 **OUTSIDE 首 lane（136.0）且行镜像**：y_N = y_P ± row_pitch
     （确定性先 +pitch 后 -pitch，first-clear-wins）。禁止 N 与 P 同行。
   - 禁止 P 在 GAP、N 在 OUTSIDE 且同行（相向交叉根因）。
3. **镜像行方向确定性**：固定 +row_pitch 优先，first-clear；占用则 -row_pitch，
   再 +2·pitch / -2·pitch（与现有 row_relocate_max_steps 语义一致）。

> 与卡面字面「同 region（GAP 或 OUTSIDE 二选一）」的差异已实证：
> 同行对 N@GAP 任何行均 INFEASIBLE（短桩穿 P via），P@OUTSIDE 不可达（左列被
> 右列 pad 挡）——同 region 对同行对物理无解，回模型请 TASK MGR 裁决。

## 3. 落点分配算法改动（escape_landing.py）

- `allocate()` 从「逐信号」改为「**逐对**」分配：按 base 固定序（确定性），
  对内 P 先 N 后。
- 新增 pair 级预处理：判同行/跨行（|y_P − y_N| < 1e-9 → 同行）。
- 同行对候选序调整：N 的 OUTSIDE 候选**跳过 pad 行**，从 y_P ± pitch 起（镜像行），
  GAP 候选不参与 N（同行对 N 禁 GAP，防短桩交叉）；P 保持原 GAP 候选。
- 跨行对：P/N 各按原候选序（GAP 本行优先），同 region 不动。
- `_verify` / first-clear-wins / round(x,3) 不变（确定性铁律）。
- 输出 allocation 逐信号附 `pair_symmetric: true` + `mirror_row_steps` 证据。

## 4. 实证验证（真板全链路，勿重跑）

| 配置 | REFCLK1 solve | 说明 |
|---|---|---|
| 现状 P@GAP(51.3)+N@OUT(51.3) | INFEASIBLE -0.205 | 卡面现象 |
| N@GAP 任意行（14 组） | INFEASIBLE -0.205 | 短桩穿 P via，同 region 无解 |
| P@OUTSIDE 任意组合（9 组） | INFEASIBLE | 左列不可达 OUTSIDE |
| **N@OUTSIDE(136.0, 51.9) 镜像行** | **SOLVED** | 本设计 |
| 全 10 同行对镜像行（+0.6） | REFCLK1 SOLVED、REFCLK0 SOLVED | 分布 26/10 不变 |

残余：REFCLK1 skew 1.84（P 87.03 / N 88.87）——**skew_ok 仍 False**，如实记录
（禁止假成功）：本 ECO 消除「相向交叉 INFEASIBLE」，skew 收敛至走廊段可蛇形补偿
范围内由 solve 阶段处理；若 TASK MGR 要求 skew<0.15 硬门禁，需追加走廊段等长补偿
验收（另卡）。

## 5. 单测计划（对应卡面 B ①-④）

1. 同行对 P@GAP + N@OUTSIDE 同行被禁止 → N 行镜像（y 差 ≥ row_pitch）
2. REFCLK1 夹具：分配后 N 镜像行，solve 复用 _landing_escape 断言 min 边缘距 ≥ 0.175
   （或经 pipeline 全链路 SOLVED）
3. 字节级确定性（含输入乱序）
4. 既有 36/36 全锚定 + 26 GAP + 10 OUTSIDE 断言不回归（t2 保持绿）

## 6. 禁止与边界

- 不硬编码 J2 坐标/region（镜像行 = row_pitch 通用搬移，零单板特判）
- 不改真板/SPEC 数值
- 不只修 REFCLK1（约束作用于全部 10 同行对 + 通用跨行对判定）
- 不改 hs_route_model（本卡施工位置仅 escape_landing.py；skew 蛇形属 solve 既有机制）

## 7. TASK MGR 裁决点

**卡面「同 region（GAP 或 OUTSIDE 二选一）」对同行对物理不可行（§2/§4 实证）。**
选项：
- A（推荐）：采纳「镜像行对称」约束（P GAP + N OUTSIDE 镜像行）——REFCLK1 SOLVED，
  36/36 不回归，零单板特判；残余 skew 1.84 如实归因走廊段。
- B：追加 hs_route_model 短桩垂直优先改造使 GAP+GAP 可行——超本卡施工位置，需另卡。

请 TASK MGR 复核裁决（A/B），裁决后施工。
