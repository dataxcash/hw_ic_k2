# CO-09 — 【L2】D1 结构重裁定：CO-08(B) 的 F.Cu 长逃逸扇**证伪**；安全 hop 架构改为 **escape(inner) + lane(In6) + stub(In2)**

> 2026-09-11｜裁判：ARCHER（L2 域，自裁）｜性质：**变更单**（版本 bump；冻结四源**原件不动**）
> ｜触发：handoff §4-D1 剩余三步续做时，对 CO-08(B) 前提做结构可行性复核（只读探针）
> ｜证据：`m13_v57_co09_d1_structural_probe_result.json`（+ 复算脚本 `p3_v57_co09_structural_probe.py`）

## 0. 结论（一句话）
CO-08(B) 的『**F.Cu 长逃逸扇**：chip pad →F.Cu→ via1@(vx,lane_y)』前提**不成立**（芯片是 0.6 pitch 满场 BGA，
数据 pad 到 lane y 的 F.Cu 段必穿满行 pad 墙）。CO-08b/CO-08c 两次实测失败的**同一根因**即此。
D1 的可闭合架构改为：**escape 落内层（In2/B 分流 16/16）+ lane 落 In6 + stub 落 In2**（land 仅 In2↔F 安全），
配合 lane-y 重派生 / stub 全局唯一列 / 入口 tiny 避让 / 全跨距 via 桶谓词，**一次求解**。

## 1. 证伪：为什么 F.Cu 长逃逸扇不可行（F1+F2）
- DS320PR1601 footprint 实测：**354 pad 满场 BGA**，pad 场 `x[82.91,104.85] y[49.76,57.64]`，0.6mm pitch、直径 0.3。
  - **满行**（n=37，0.6 pitch）：`y=49.76 / 50.28 / 57.12 / 57.64`；
  - **疏行**（n=16，1.2 pitch）：`y=50.88 … 56.42`。
- 净距：0.6 pitch 相邻 pad 边距 `0.6-0.3=0.3 < 2*(0.15+0.075+0.1025)=0.6575`
  ⇒ **F.Cu 单层无法在满行 pad 间穿行**；`y=57.12/57.64` 两道满行 = 芯片下缘**完整墙**。
- east 数据页：pad `y∈[55.13,57.64]`，lane `y∈[56.66,78.56]`（**在 pad 场下方**）。
  ⇒ chip pad→lane 的 F.Cu 段**必经** `y=57.12/57.64` 满行 ⇒ 无关断；右侧绕行（x>104.85）同样被满行封死。
- CO-08b 观测（30/32、crossings 30、wall 139s）与 CO-08c（30/32、crossings 14、vv 0.15~0.5、wall 196s）
  的失败特征与"长 F.Cu 段穿 pad wall / 扇交叉"**完全一致**；无需再试。

## 2. 顺带证伪（只读数值探针，防重走）
| 方案 | 探针结果 | 判定 |
|---|---|---|
| 2 via/线 单层 river（lane+stub 同 In2） | In2 lane×stub 真交叉 **271**（改列序仍 >0） | **结构性不可行**（CO-07 candidate a / C1 与序无关否证） |
| merge river（escape+lane+stub 同层） | In6 交叉 178~301；In2 交叉 166~271（探针复算 271） | **不可行** |
| 16 网/层 fan（单 band） | 最佳列序仍 4~10 交叉 | 需专门 fan 构造（见 §4） |

## 3. 裁定：安全 hop 的层角色分配（F5）
land 只能 `In2↔F`（安全 hop 唯一）⇒ **stub 必在 In2**；lane 与 stub 同层必交（§2）⇒ **lane≠In2**；
lane 取 **In6**（到 stub 仅需 `In6↔In2` 一跳）时，escape 只能是 **In2 或 B**，且 32 网/侧必须分流（单层 32 竖段需 11.78mm(=31×0.38) > 可用 8.95mm（CO-07 口径 12.16 > 9.45））：

| band | escape 层 | lane 层 | stub 层 | via/线 | via 链 |
|---|---|---|---|---|---|
| **X**（east=dn / west=up） | **In2** | In6 | In2 | **4** | `F↔In2` → `In2↔In6` → `In6↔In2` → `In2↔F` |
| **Y**（east=up / west=dn） | **B** | In6 | In2 | **6** | `F↔In2` →`In2↔In6`→`In6↔B` →escape(B)→ `B↔In6` →lane(In6)→ `In6↔In2` → `In2↔F` |

- 全部 hop ∈ {`F↔In2`,`In2↔In6`,`In6↔B`}（**不穿透其它信号层**）⇒ 消除 108 跨层 shorting 的结构根因。
- **几何可复用**：W3-CN.30 的 escape 竖段 / lane 水平段 / stub 竖段 / F.Cu breakout **折线几何不变**，仅**层标签**
  与 **via 定义**变更（+ bandY 入口 tiny）。故本单是"层角色 + via 集 + 列布局 + lane y"重派生，不是全新几何。
- SPEC `vias/high_speed/max_per_line` 须以 ECO 标注 **4→6**（bandY）；本单为 L2 自裁（过孔策略）。

## 4. 一次求解前必须一并重派生的 L2 子问题（F6）
1. **lane y 布局**：lane y 与任一 pad 行 y 须 ≥0.38（bandY 的 In6 入口 tiny 是 x≈pad_x 的短段，会被路过的 lane 切）。
   现 `LANE_LO=33.3 / STEP=1.46` 下 `lane#13 y=52.28`、`lane#15 y=55.2` 落入 `pad_y±0.38` 禁带 ⇒ 重派生 `LANE_LO/STEP`
   （32 lane 需容纳 5.47mm 禁带，可用 45.26mm ⇒ STEP ≈1.28）。**但**：若走 §4-3(b) x-band 分离，
  lane y 无需改（入口 tiny 只在 In2 短段，不落 lane 层）⇒ **优先 (b) 以免扰动 O4 等长**。
2. **stub 列全局唯一**：32 网/侧列须互异（现 per-band rank 复用列 ⇒ In2 stub 共线 tt 0.0）：
   16 inner（`≤131.65`）+ 16 outer（`≥136.0`），间距 ≥0.38。
3. **入口 tiny 与 escape 竖段同层避让（两种手段，任选其一，优先 (b)）**：
   (a) **y-域分离**：east 取 X=dn（竖段 57.12→向下）、Y=up（tiny ≤56.42）；west 取 X=up（需 lane 0-7 低区）、
       Y=dn（tiny 51.673~52.97）。**代价**：west 须把 up/dn 改成"band-clean 区块"⇒ 动到 R2 lane 序，
       **连带影响 O4 对内等长闭合**（须一并复核 meander 预算），故非首选。
   (b) **x-band 分离（首选，免动 lane 序）**：In2 是**自由内层**（可穿行于 chip pad 之下），
       把 bandX 的 escape 竖段经由 45° 横移搬到**另一 x-band**（west 可移至 x<82.9 或 chip 下方 x≈84~95 之外；
       east 移至 x>94），与 bandY 的入口 tiny（x≈pad_x 84.6~93.55）**异 x-band** 同层不交；
       横移段须为平面扇（16 条、按源 x 序单调）。
4. **谓词升级**：via = 其跨距内**所有信号层**的圆障碍（全跨距桶）+ 同页跨极性 `via↔track`（= CO-06 D2/D3），
      否则仅"端点层口径"会再次放过跨层相碰（108 shorting 的真身）。
5. `bandY` escape 若因 B 层可用性受阻，可将 bandX/bandY 对调后再证（结构对称）。
6. **落地顺序建议**：先 (b) x-band 分离版（不动 lane y / 不动 R2 序 ⇒ O4 等长不受扰），
      若 16 条横移扇证不出平面性，再退 (a) 并一并复核等长。
7. **诚实边界（尚未证，实现前须先证）**：
   - (b) 的整体横移若达 ~10mm x-band：相邻竖段 0.4mm 间距在 45° 下横向净距仅 `0.4·cos45°=0.28 < 0.38`
     ⇒ 需 ≤18° 浅角（长度换横移）或先加密 x 间距；否则横移扇自身不满足 0.38。
   - west 若保留 canonical lane 序，up 高 lane(50.82~55.2) 的 escape 竖段会下探穿过 dn 入口 tiny(51.673~52.97)
     的 y 域 ⇒ (a) 需 lane 重排（等长连带）；否则须 **逐页混合分配**（按 lane 段决定该页 escape 落 In2 或 B）。
   - 本单的"层角色"已定，"具体分配/横移几何"须在实现期以数值证过再落盘。

## 5. 验收
- 一次求解须同时满足：`FEASIBLE_ALL ∧ same_layer_crossings=0 ∧ A-CN.9 0/0/0（含全跨距口径）∧ 对内 skew ≤0.15 ∧ wall ≤120s`；
- 重跑 G4→G5→G6→G7（shop 口径 `k2_v4_8L.kicad_pro`），目标 **DFM new=0**（含 D2–D6）；
- 本裁定可复核（§1 结构 + §2 数值 + 探针 JSON）。
