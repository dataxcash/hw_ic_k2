# m13 v57 — G3 冻结契约 v1.1：lane 帧参数裁决（F-3 解封）

> 门控位：v2 §2 G3 行 / G3 契约 v1（`39f0c13`）§2/§3 的补丁。
> 起因：F3-LANEFRAME 卡报冲突——R1 矩阵 C-3/C-4 判 `margin/edge/band_base`
> "无权威源"，而卡要求其源自 drc_rules/G3 契约。**这是本契约的缺口，由架构补裁**；
> 不由 worker/Oracle 自行发明。
> 日期：2026-09-10｜基线 HEAD：`019de2a`（SPEC-REV-1）；数据基线 = F11 后 R1 链。

## 0. 事实基础（先取证）

`lane_kernel.build(frame)` 语义：`needed = margin + ext_lo + center + ext_hi + margin`，
其中 `ext_band=(n−1)·pitch`、`center=1.46`（两带分居 span 两端时）。`edge∈{lo,hi}` 决定
带从哪端铺设；`band_base` 不是独立入参，而是铺设起点（`y_lo+margin` 或 `y_hi−margin`）。

关键一致性：W0-R 已签 `B1.5 PASS` 的数值
`data_bands.*.centre_span_needed_mm=10.22=7×1.46`、
`joint_data_frame.centre_span_needed_mm=21.9=15×1.46` —— **正是 margin=0 的取值**。
即 W0-R 终态本身隐含 margin=0；旧 kernel 的 `0.6` 只是未清的历史默认值。

## 1. 裁决（canonical）

1. **`margin := 0`**。理由：① `usable_y_spans` 已扣边距（W0-R `edge_clearance=0.30`）与体/
   禁入投影，再加 margin 属重复计；② W0-R 已签数值恰为 m=0，改 m≠0 会推翻 `B1.5 PASS`；
   ③ `0.6` 无权威源。→ **`0.6` 作废**。
2. **`edge` := 约定固定**：`up→lo`、`dn→hi`（沿用 kernel 约定与 board-intent §3 对称铺设；
   两带分居 span 两端 → 中心隔离 gap=1.46，最大分离）。
3. **`band_base` := 派生，非独立输入**：`y_lo`（lo 带）/ `y_hi−(n−1)·pitch`（hi 带）。
4. **可行性判据**：`needed = ext_lo + center + ext_hi ≤ avail = y_hi−y_lo`；
   失败 → 量化证书 `{kind:"lane_frame", needed_mm, avail_mm, short_mm}`（沿用 kernel 口径）。
   两带联合：`(n_total−1)·pitch ≤ (y_hi−y_lo)`（16 对 → 21.9 ≤ 45.4 ✓）。
5. **`pitch = 1.46`** 权威 = `drc_rules.json`（`0.175+0.41+0.875`，W0-R 同款推导，运行时断言）。
6. **REFCLK**：`layer=F.Cu`（D0-2），不占 In2 gap；F.Cu 禁入谓词域（G3 v1 §4 R1.5）承载。

## 2. 一致性核对（本裁决复算 = W0-R 已签值）

| 量 | 本裁决 | W0-R 已签 | 一致 |
|---|---|---|---|
| 单带 needed | 7×1.46 = 10.22 | 10.22 | ✓ |
| 联合 needed | 15×1.46 = 21.9 | 21.9 | ✓ |
| avail | 78.7−33.3 = 45.4 | candidate span 长 45.4 | ✓ |

→ 裁决与 `B1.5 PASS` 完全相容，**不推翻 W0-R 终态**。

## 3. F-3 契约要求（解封）

F3 产出的 lane 帧必须记录 **authority 指纹块**：

```
frame_authority = {
  "contract": "G3-C v1.1 (this file)",
  "pitch":    {"source": "_shared/eda_core/drc_rules.json", "sha256": "0a459839…"},
  "span":     {"source": "m13_v57_big_w0r_corridor_model.json corridors.*.usable_y_spans",
               "sha256": "80ee9adb…"},
  "bands":    {"source": "m13_v57_s1_page_manifest.json", "sha256": "a8ef3ea8…"},
  "margin":   0, "edge_convention": {"up":"lo","dn":"hi"}
}
```

- `margin/edge` 不再是"无权威源"缺口：其权威 = 本契约（id + 指纹）。
- `band_base` 由 span+margin+edge 派生，逐帧记录推导式。
- 禁止读取旧 W0 的 `0.6 / 12.0`。

## 4. 逃生门（如 L2 不同意）

非零 margin、或不同 edge/band_base 约定 = **上游输入变更**（新 escape hatch）。
一旦采用，须重跑 W0-R 全链并重过 G1（因会改变 needed/feasibility）。

## 5. 状态

- **F-3 = UNBLOCKED**：F3-LANEFRAME 可开工，无需等 Oracle 发明推导规则。
- G3 冻结进度：F-1/F-2/F-5/F-6/F-7/F-9/F-10/F-11/F-12 已闭；F-3 解封；余 F-4/F-8/F-13。
