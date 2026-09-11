# CO-60 — 【L2 走廊分配】对间净空目标可达性机判（**负结果**）⇒ **L1 冲突报告**

> 2026-09-12｜定层：**L2 自裁范围内**的可达性机判（《LAYOUT_CONSTITUTION》第二章：走廊分配 = L2）
> 工具：`tools/p3_v57_co60_corridor_pitch_frontier.py` → `m13_v57_co60_corridor_pitch_frontier.json` `e2d74c7afaae0d45`
> 性质：只读冻结源；**canonical 零改动（候选件已回滚）**；不伪 sign-off。

## 1. 前提：lane 步距是合法 L2 旋钮（机判保真）
以 CO16 发射器旋钮重发 ALLOC.5，**逐字节复现** `0bf6cdc203887a48`（`baseline_faithful=true`）⇒ 旋钮口径可信、扫描可复现。

## 2. 目标与前沿（冻结 L1 包络内）
要求（`route_model_config.json` `capacity_audit.note`：要求量 = R3-2 **铜边净空 0.875**）在交付对铜跨 0.705 下 ⇒ 对中心距 ≥ **1.580**。

| 用例 | 东侧 step | 西侧 step | 32/32 落位 |
|---|---|---|---|
| 基线 ALLOC.5 | 1.449 | 1.050 | **是** |
| 仅东侧 → 1.580 | 1.580 | 1.050 | **是** |
| 仅西侧 → 1.100 | 1.449 | 1.100 | 否 |
| 仅西侧 → 1.150 / 1.200 / 1.460 / 1.580 | 1.449 | 上列 | 否 |
| 双侧 1.460 / 1.580 | 同值 | 同值 | 否 |

- **西侧**：>1.05 即失败（**余量 < 0.05**），失败集中在**芯片逃逸区**（x≈93.2、y≈50.5，`PCIE_UP6/UP7 input`，行扫描 15148~15150 耗尽）⇒ 受**球栅逃逸/球图**约束。
- **东侧**：1.580 可落位 32/32，且独立复核 320 via/320 段 **0 违规**（centerline 与 copper 双口径）。

## 3. 东侧 1.580 的全链实测（本次执行，随后回滚）
| 门 | 结果 |
|---|---|
| G4 | PASS `FEASIBLE_ALL` 34 页 / crossings 0 / work 546/546，图纸 `a6eed335dd61f536` |
| G5 | PASS G-M1..6 True / A1.2-1.4 True / frozen=True，`5fc44fadd59f5784` |
| G6 | PASS L4-A..F True / viol 0，板 `35c33b26693d37c0` |
| G7 | **DFM FAIL new=84 {clearance 1, copper_edge_clearance 83}**，disappeared 0，在册未连 0/68，SI PASS skew 0.0031 |

⇒ 东侧加宽使走廊带外扩（7×0.131≈0.92mm）**突破板边铜距** ⇒ **不可交付**；命令同 §7，正式件已回滚。

## 4. 备选：恢复冻结模板对铜跨 0.585
`POL_OFF 0.25→0.19`（对内中心 0.5→0.38）：**0/32 落位**（两配置均 0），复现 CO-16 原注「0.19 不足 vt 0.4525」⇒ **不可行**。

## 5. 结论：**L1 冲突**（阈值 vs 包络）
在冻结 L1 包络（板轮廓/板边铜距 + 球图/逃逸网格）内，R3-2 的 realized 铜边 0.875（⇒ 1.580）**不可达**：
- 西侧受球栅逃逸锁死在 ≤~1.05（+0.05 即崩）；
- 东侧可放置但破板边铜距（83 项 DFM）；
- 恢复冻结对铜跨的备选直接落位 0/32。

⇒ 三条 L2 路径全部机判否决；该冲突的两端都是 L1 决策（R3-2 阈值 ∈ owner 冻结阈值；板轮廓/球图 ∈ L1 包络）。
依《LAYOUT_CONSTITUTION》第三章第 2 条（下层无权私下妥协，须升级上层裁决）⇒ **升 owner**。

## 6. owner 选项（择一）
- **A（修订阈值/范围）**：明示 R3-2 realized 0.875 不适用于本包络（以现交付 1.449/1.05、铜边 0.744/0.345 交付，串扰由 SI 求解器 + 板厂券判）。
- **B（放行包络变更）**：授权改板轮廓/板边铜距或球图逃逸（球重映射），再按 1.580 全链重导。
- **C（改阻抗换空间）**：恢复对铜跨 0.585 需同时重定 8L 叠层（CO-53..56 部分重开）；初判受 vt 净距限制（§4）。

## 7. 复现 / 红线 / 指纹
```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
python3 tools/p3_v57_co60_corridor_pitch_frontier.py          # 前沿（含基线保真断言）
# 东侧 1.580 全链（候选，需临时改引擎 pin 到 v6）：
#   引擎 CO16_ALLOC→m13_v57_co16_channel_allocation_v6.json；CO16_ALLOC_SHA→2ebda54c…
#   → python3 tools/p3_v57_w3_constructive.py --r1-5-shape co16 → validator_v2 → l4_apply_drawing --board → l4_validator → l5_signoff
```
- **回滚确认**：图纸 `4e7497daf97cebd1` / 板 `cdcb869e9827ec87` / validation `95ec1af12f6edae3` / landing `54c44b6a5aa54f40`（＝CO-59 基线，未变）；引擎 pin 已还原；四冻结源 4/4 MATCH。
- 保留为**已评估并否决**的候选证据：`m13_v57_co16_channel_allocation_v6.json` `2ebda54c7b917ef9`、`m13_v57_co60_alloc6_placement_geom.json`、`m13_v57_co60_alloc6_placement_verification{,_copper}.json`（放置层通过 ≠ 可交付，DFM 已否决）。
- 指纹：frontier json `e2d74c7afaae0d45`｜v6 alloc `2ebda54c7b917ef9`｜boundary → v1.29。
