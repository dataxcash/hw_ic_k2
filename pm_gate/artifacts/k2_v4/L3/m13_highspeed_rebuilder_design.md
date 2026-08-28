# M13 高速域重建器 — 架构设计（eda_core/hs_route_model.py 蓝图）

> 日期：2026-08-25 · 承接：Phase 1 预检（UP4/UP5 逐 Pin 审计）+ REFCLK 裁决（channel_alloc_v2 18/18）
> 铁律：方案即模型输出（每条设计段带 solve_ref）；DRC 只核对不驱动；结论带证明；零 revA 特判

---

## 0. 设计前提（Phase 1 预检实证）

1. **UP4/UP5 P 段缺失 = 区域密度阻断**，非漏布线：U7 左引脚区 x[85,89]×y[42,48] 塞满
   UP1-UP6 六网段/via，自网 N via 挡 P（0.15<0.175）、邻网 UP1_N 段相交。
2. **逐 Pin 补线无解** → 高速段必须**整体清场重排**：重建器障碍场排除全部高速段/via，
   只保留非高速元素（GND/P3V3/低速/zone/连接器焊盘/电容焊盘）。
3. **通道已定**：channel_alloc_v2 18/18 SOLVED（数据对 F.Cu upper/lower、REFCLK In6）——
   走廊段路径 = 通道 track_y 直线，是唯一合法坐标源。

## 1. 输入/输出

```
输入：
  --board <k2_v4.kicad_pcb>         板上真源（非高速障碍 + 高速网端点拓扑）
  --spec  <SPEC_k2_v4.json>         走廊通道（channel_alloc_v2 已落 SPEC corridors）
  --alloc <channel_alloc_v2.json>   18 对通道分配（solve_ref 协议）
  --rules <drc_rules.json>          规则库（PCIe85 语义）
输出（每对差分，落 model_solves/hs_rebuild/）：
  {net, status: SOLVED/INFEASIBLE, pairs: {P:[seg...], N:[seg...]},
   length: {lenP, lenN, skew}, solve_ref, input_fp,
   evidence: {avoided: [...], channel: "J2_TO_U/upper/k", layer}}
```

## 2. 求解架构（三段式 + 全局冲突避免）

### 2.1 障碍场构建（高速段清场）
```
field = UnifiedObstacleField(rules, layer="F.Cu")
  + 非高速 F.Cu 段（GND/P3V3/低速/STRAP/I2C/...）
  + 全部 via（异网障碍；高速 via 清出待重建）
  + 全部 pad（连接器 J2/J3/J4 + AC 电容 + U3/U7 焊盘 + 低速器件）
  + zone（F.Cu 铺铜平面）
  + mask（阻焊开窗）
```

### 2.2 差分对路径求解（P/N 对称，对中心线 + 展开）
```
每对 (P, N)：
  1. 端点拓扑：U7/U3 pin 焊盘（如 UP4_P@(88.83,44.50)）→ AC 电容焊盘 → 连接器焊盘
  2. 对中心线路径：pin 区逃逸 → 走廊通道 track_y（channel_alloc 真源）→ 连接器
     逃逸段求解：可见性图（复用 ls_route_model V-Graph，unified 场兼容）
  3. P/N 展开：中心线 ±0.19mm（P/N 中心距 0.38 = 0.205 宽 + 0.175 gap）
  4. 等长：P/N 累计长度差 <0.15mm；不足侧蛇形补偿（在走廊段内做）
```

### 2.3 全局约束（通道容量 1:1 + 对间间距）
```
- 走廊段：每对独占通道 track_y（channel_alloc 冲突图已解，重建器照抄零决策）
- 对间间距：相邻通道 pitch 1.08 → 对间净距 0.875（SPEC inter_pair_spacing，几何自洽）
- 逃逸段：U7/U3 引脚区整体重排（18 对 pin 逃逸一次求解，非逐对先到先得）
```

## 3. 引脚区重排策略（Phase 1 核心，替代逐 Pin 补线）

```
U7 左引脚区（UP0-7 输入 + U7 右输出）+ U3 对称区：
  1. 清空区内的高速段/via（障碍场已不含高速）
  2. 对每个 pin：逃逸方向候选（左/上/下，避开非高速障碍）
  3. 按 channel_alloc 先难后易序（违规密度）逐对分配逃逸走廊
  4. 逃逸段与走廊段在 x=98.83（J2_TO_U 起点）或 x=88.83（U_TO_MCIO 终点）衔接
```

## 4. 求解确定性（铁律）

- 逃逸段：Dijkstra 距离升序 + 坐标序（复用 ls_route_model 确定性协议）
- 引脚区重排序：违规密度降序 + 网名升序（channel_alloc 同协议）
- 零随机、零运行时决策（施工层照抄）

## 5. 验收（Phase 1 先导 = UP4/UP5）

```
- UP4/UP5 P/N 对称路径 SOLVED（skew <0.15mm），带 solve_ref + avoided 证据
- 重建后高速域 385 条 DRC → 目标 0（模型门禁 + DRC 复验）
- 单测：构造最小高速对场景（pin+电容+通道）断言求解/等长/证据
```

## 6. 施工层（后续，非本架构范围）

- low_speed_apply 模式：重建器输出段 → 板文件落盘（预载 + 快照规避 pcbnew SWIG 退化）
- S2 sregress → 落盘 → sadvance（正规流程）
- model_gate：每条设计段 solve_ref 校验

## 7. 铁律遵守

- 方案即模型输出：本架构全部路径由模型求解（channel_alloc + V-Graph），带 solve_ref
- DRC 只核对不驱动：重建器是方案工具，DRC 是结束时的核对
- 结论带证明：SOLVED 带路径/等长/障碍证据；INFEASIBLE 带连通分量证明
- 修订走输入：通道/走廊/规则全部入参（SPEC 真源）
- 零 revA 特判：hs_route_model 全通用（差分对语义从规则库声明读取）
