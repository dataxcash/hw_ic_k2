# m13 v57 — G3 冻结契约 v1（架构裁决部分）

> 门控位：v2 §2 G3 行。本文冻结 G3 前置项中属**架构裁决**的部分（F-2/F-5/F-6/F-7/F-12），
> 作为 W3 与后续 worker 卡的输入契约。实现类前置项（F-3/F-4/F-8/F-11/F-13）另开 worker 卡。
> 依据：R1-REVIEW 矩阵（已签收 `1a7391e`）+ D0 裁决卡（`ad5c208`）。
> 日期：2026-09-10｜k2 HEAD：`ad5c208`。

## 1. F-2 证书 canonical schema 单一化

- **裁决**：以 W0-R validator 的 10 字段版为 **canonical**：
  `{kind, blocked, corridor, band, required, available, shortage, conflicts, canonical_core, escape_hatches}`。
- S1 设计 §4 版与 board-intent §4 版作为**映射来源**，G3 冻结后新产出的证书一律用 canonical；
  旧字段在报告中作 `legacy_mapping` 附注，不再作为新契约字段。
- 理由：W0-R 版已被 validator 咬合（变异测试 20/20），且已过 B1.5 PASS；另两版仅设计文本未落机器。

## 2. F-5 行键裁决（J2 错位 + WEST 簇简并）

- **页级 row_y 代表键 = (N.y + P.y) / 2**（差分对中点，3 位小数）。EAST J2 页 P/N 错位 0.6mm
  时以中点消歧（DN1：N55.5/P54.9 → 55.2；UP0：N43.5/P42.9 → 43.2）。
- **WEST 簇分帧**：按 `conn_ref` 分帧——J3 簇（DN0-3/out_MCIO y45.75、UP0-3/input y43.25）与
  J4 簇（DN4-7 y61.45、UP4-7 y63.95）；帧内 4 页按 **x 升序**定 lane 序（WEST 的区分维是 x，非 y）。
- W1 契约键改为 `(conn_ref, row_y)`；WEST 页禁止只用 `row_y` 定序。

## 3. F-6 两端可达性（LEG 双端谓词）

- W1 契约的 LEG 从"conn 单端预算"扩展为**双端谓词**：
  `feasible(lane_y) ⟺ leg_ok(chip_row_y → lane_y) ∧ leg_ok(lane_y → conn_row_y)`。
- 两端 LEG 预算均取 `k·1.46`（k∈{1,2,3,5}）口径，权威源 = drc_rules.json pitch 推导（与 W0-R
  一致）；旧 W0 的 12.0 单端预算作废（v1 初查已判"无锁定权威"）。
- W3 判定核必须消费双端谓词，禁止单端准入。

## 4. F-7 chip 锚侧向映射 + EAST 过渡段资源层

- **新增 manifest 字段** `chip_side`：按页 corridor 定（EAST 页=east、WEST 页=west、REFCLK=pass）。
- 事实：64 chip 锚全在 U6 体西半 x∈[84.60,93.55]（R1 S-3 实测），EAST 16 页锚→走廊入口 105.25
  隐含穿/绕芯片体过渡段。
- **裁决**：新增 **R1.5 过渡段资源层**，承载 chip 锚列 → corridor 入口（EAST 105.25 / WEST 82.35）
  的段：lane 互斥守恒 + `escape_transition_zone` 的 no_via/no_90deg 约束域 + 微净空 0.075。
  R1.5 的 x 域：EAST [93.55, 105.25]、WEST [82.35, 93.55]（以 chip 锚最大/最小 x 与走廊入口为界）。
- R1.5 由 W3 消费；旧 R1 设计文本"芯片每侧出逃列"与实测锚分布不符处，以本文为准。

## 5. F-12 chip_landing 重发射协议

- `m13_v57_s1_chip_landing_rows.json`（64 行）为 **PROVISIONAL**（baseline_correction §4）。
- **裁决**：W3 联合指派产出终值时，landing rows 必须与 34 页 drawings **原子重发射**（同一提交、
  同一 SHA 链）；禁止中间态 PROVISIONAL 行进入 S2。重发射格式沿用 landing 现有 schema，值由 W3 定。

## 6. 对 D0 裁决的契约化

- R4 出链（D0-1）：W3 输入白名单**删除** R4 相关字段（墙 pad 锚、墙隙守恒）；西页模板 =
  connector→chip 直连。SPEC-REV-1 完成后，F-11 按新 SPEC 指纹重补。
- REFCLK 层 = F.Cu（D0-2）：REFCLK 页的层字段固定 F.Cu；REFCLK lane 与数据 lane 无同层隔离约束，
  但 REFCLK 内部仍按 1.46 间距守恒（W0-R 终态）。
- corridor x-ranges（D0-3）已确认，为 W3 的 lane 入出口 bound_x。

## 7. 冻结状态

| 项 | 状态 |
|---|---|
| F-1 W0R-FIX 终态 | 已闭（条件性，条件并入 D0） |
| F-2 证书 schema | 已裁（本文 §1） |
| F-5 行键 | 已裁（本文 §2） |
| F-6 两端可达 | 已裁（本文 §3） |
| F-7 侧向+过渡段 | 已裁（本文 §4） |
| F-9 R4 出链 | 已裁（D0-1，SPEC-REV-1 待落地） |
| F-10 REFCLK 层 | 已裁（D0-2，SPEC-REV-1 待落地） |
| F-12 landing 重发射 | 已裁（本文 §5） |
| F-3/F-4/F-8/F-11/F-13 | 待 worker 卡（实现类） |
| G3 整体 | 未冻结完成——待 SPEC-REV-1 + 实现类卡验收 |

End of G3 freeze contract v1.
