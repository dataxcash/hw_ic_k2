# m13 v57 — G3 冻结契约 v1.2：容量帧 vs lane 域 + D0-4 开启

> 补丁来源：F4-INDVER 上报的口径事实（真问题）。
> 基线 HEAD：`019de2a`｜日期：2026-09-10。

## 1. 澄清：G3 v1.1 §1 是容量帧，不是 lane 域

- G3 v1.1 §1 定义的 `band_base = y_lo / y_hi−(n−1)·pitch`（span 端 flush-pack）是
  **容量判据**：证 `(n−1)·pitch ≤ span`（单带）/ `(n_total−1)·pitch ≤ span`（联合）。
  **它不是 R2 指派的候选 lane 域**（用它会得到 lane 贴 span 端、页行在中段、reach 9.6–19.8mm
  的退化结果，全 k 不可行）。
- **R2 指派 lane 域 := `usable_y_spans` 上的 pitch 网格**（W0-R `candidate_spans`；
  step=1.46、margin=0、范围 33.3–78.7）。ratify F4-INDVER 边界声明 §2。
- 指派谓词（W1 单端）：`pages sorted by (row_y,id) → strictly increasing lane index`
  且 `|lane_y − row_y| ≤ leg`，`row_y=(N.y+P.y)/2`（v1 §2）。

## 2. F-6b（新）：双端谓词未覆盖

- G3 v1 §3 / F-6 裁的谓词是**双端**：`leg_ok(chip_row_y→lane_y) ∧ leg_ok(lane_y→conn_row_y)`。
- F4-INDVER 实现的是**单端**（conn 端，W1 同款）。双端版验证**尚未交付** → 记 **F-6b**，
  在 W3 契约冻结前补齐。

## 3. D0-4（新，请 L2 裁决）：LEG 预算 `k`

- 事实：`k`（leg = k·1.46mm）**无权威源**（R1 W1-3）。真实可行性随 `k` 翻转：

| 帧 | k=1 | k=2 | k=3 | k=5 |
|---|---|---|---|---|
| EAST up/dn (8) | T | T | T | T |
| EAST joint (16) | F | T | T | T |
| WEST up/dn (8) | F | T | T | T |
| WEST joint (16) | F | F | F | T |

- 影响：若最终 `k ≤ 3`，**WEST joint (n=16) 不可行** → G4 需 L2 改输入（加走廊 y /
  减对 / 允许分层）；若 `k = 5`，全部可行。
- 裁决需求：给出 `k` 的权威值**或**物理依据（chip/conn 两端锚到 lane 的最大竖直 leg 来源）。
- 在 `k` 定前：F4 表 = 灵敏度分析，非终判；W3 不得以之为准入结论。

## 4. 状态

- G3 冻结：F-1/F-2/F-5/F-6/F-7/F-9/F-10/F-11/F-12 已闭；F-4 通过（单端范围）；
  **F-3（lane 域/帧发射契约）与 F-6b（双端谓词）仍待**；D0-4 待裁。
- W3（G4）**未解封**。

## 5. D0-4 裁决（架构师代裁，2026-09-10）

**裁决：`k := 5`（leg = 5 × 1.46 = 7.3 mm）为项目标准工作预算。**

理由：

1. **权威一致性**：W0-R 容量帧已签 `B1.5 PASS`（全帧可行）。`k` 无权威源，用无源紧预算
   推翻已签结论违反"最低上游层才可改因"原则。
2. **最佳实践**：escape/breakout 的竖直 leg 非先验预算量；真实绑定约束是**非交叉序兼容 +
   lane 容量**（F4 已精确判定）。leg 预算只作为拥塞代理，取项目已定义的**最宽值**。
3. **不新造常数**：`k∈{1,2,3,5}`（R1 W1-3）中取 5；k<5 的紧口径无几何依据。
4. **可回退**：若将来 L2 规则收紧 leg → 上游输入变更（escape hatch），重跑全链。

结论：`k=5` 下 F4 单端表全 T（EAST/WEST × up/dn/joint），与容量帧一致；WEST joint 不再是阻塞项。

**D0-4 = 关闭。**

## 6. F-6b 定义（双端谓词，下一张卡）

单端（W1/F4）谓词 `|lane_y − conn_row_y| ≤ leg` 是**不完整**的。G3 v1 §3/F-6 的正确谓词为
**双端**：`|lane_y − conn_row_y| ≤ leg ∧ |lane_y − chip_row_y| ≤ leg`。必须实现并重判——
尤其 WEST chip 锚聚于 y≈49.8–52.4（窄带），可能成为真正的绑定约束。
