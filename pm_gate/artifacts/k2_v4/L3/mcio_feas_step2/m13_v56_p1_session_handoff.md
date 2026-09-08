# m13 v56 — P1 阶段收尾 handoff（数据形状/覆盖，方案 A）

> 承接 NEW_SESSION_PROMPT_v56.md（P0→P1）。本文件 = P1 出口记录，供 P2（登记簿接线）
> 卡片直接入场。P0 基线 = `m13_v56_p0_baseline.json`。

## P1 范围与裁决
- **方案 A（用户裁决）**：P1 只做数据形状/覆盖；chip 行不得进连接器 `landing` 表
  （net 键唯一 → 实测 U3 覆盖 J2 行致 UP7 out_J2 回归 = v52 C1-vs-C2 裁决的实证）；
  消费接线（chip_landing 命名空间喂 solve）= P2。
- 机器试跑结论：U3(EAST)/U7(WEST) corridor 锚 + 芯片域归属后**首次产出行**
  （U3 32 行；U7 6 行 + DN_OUT 全 NO_ESCAPE——西侧为 GND 球阵守恒墙，非 P1 可解）。

## 已提交（双仓 pushed，freeze locked）
- **引擎 `_shared` 6bebc1b**（E1 形状统一）：
  - `route_input.py`：`ChannelInput.nets` = band nets list 原样（单网 str 归一 [str]）；
    `extract_channels` 不再把 list 塞 str 字段。
  - `solve_pipeline.py` `_alloc_nets`：展平 str/list + 伪网名（字符串化列表/非法字符）raise。
  - 测试 +2（extract_channels list 形状 / _alloc_nets 展平+拒伪）。既有唯一失败
    `test_t5_solve_consumes_landing` 与 pristine 同，无关本改动。
- **k2 6a1b438**：
  - `SPEC_k2_v4.json`：EAST/WEST refclk band nets → `["PCIE_REFCLK0","PCIE_REFCLK1"]`
    （2 轨 2 网索引对齐，几何零动）。
  - `route_model_config.json`（L2）：U3/U7 region corridor 锚
    （U3=EAST_CHIP_TO_J2/RIGHT；U7=WEST_MCIO_TO_CHIP/LEFT；board_edge/corridor_bound=96）。
  - `tools/p3_k2_real_board_e2e.py`：删 nets_path 覆写 + 删失效 E1 WARN gap 块。
  - 新 `tools/p3_v56_p1_chip_coverage.py` + 工件 `m13_v56_p1_chip_coverage.json`
    （P2 接线输入）。

## P1 机器验收（全过）
- 谓词 7 项 PASS（无 nets_path 覆写 / 分区不相交+闭包 / corridor 锚 ∈ SPEC / U3&U7 assigned>0）。
- e2e run7≡run8 全文件字节一致（改动后确定性）；alloc/solve/capacity 剥内容哈希后
  **== P0 基线**；solve 16 SOLVED/18 INFEASIBLE **零平移**（段级 digest 全同）。
- landing 差异仅 U3/U7 region evidence 装饰字段（corridor_id/side/capacity），
  allocation 字节不变。

## P2 入场包（下一卡）
1. 消费 `m13_v56_p1_chip_coverage.json`：chip_domains 的 U3/U7 域 demands+pads 已富化
   alloc（track_y/band/corridor），行坐标在 `landing_rows`；NO_ESCAPE 网（DN_OUT 西侧
   = GND 球阵墙，P3/P4）不得回退。
2. 接线点：solve_pipeline.run_solve 现只传 `landing=landing.allocation`；hs_route_model
   原生支持独立 `chip_landing` 命名空间（`_chip_landing_by_net`，method=VIA_IN2 消费）。
   需解锁 `_shared/eda_core/solve_pipeline.py`（冻结区）→ 先交证明 → 接 `chip_landing`。
3. config U3/U7 域 demands_path 现仍指向空键（管道 landing 零漂移）；P2 改指向
   chip-coverage 工件派生或把 U3/U7 从 escape_landing.regions 挪出、另建 chip_landing
   产线（v52 架构裁决：C2 独立 EscapeTable，勿污染 landing 语义）。
4. 单调收敛对照 P0 基线（34 段），failure set 只许收缩。

## 纪律提醒
- freeze 已 lock（0/0/0）；P2 若动引擎须 unlock + 开工前证明。
- 容器 `_shared` = f15b03e+6bebc1b；k2 `_shared` 陈旧副本勿动。
