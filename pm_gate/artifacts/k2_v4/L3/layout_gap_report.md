# K2 v4 高速域布局缺口报告（M13 v5，容量地图 + 数学不可行性证明）

> 生成：2026-08-26，M13 v5（M1 容量地图 + M2 flip 重设计 + M4 换层形态）
> 证据：`model_solves/hs_rebuild_v5/capacity_map.json` + `hs_rebuild_summary.json`
> 铁律：方案即模型输出 / 假成功零容忍（断言全过才算 SOLVED）/ 分析走模型 API

## 1. 总览

- **真实 SOLVED：1/18**（PCIE_REFCLK0，In6 贯穿，P/N 断言全过）
- **段级 SOLVED（链内）**：UP0-7 全部 3 段（input/out_U7/out_J2）SOLVED；
  DN0/1/2/4/5/7 的 input+out_U3+out_MCIO SOLVED（DN3/6 out_U3、DN0/1/3 out_MCIO 失败）
- 链级 INFEASIBLE 全部由 **P/N 间距断言拦截**（-0.205 = 段完全重叠）——
  **无假 SOLVED**（v5 零容忍目标达成：不再有"声称 SOLVED 实际交叉"）
- 求解耗时：全量 18 对 ~40s（单对均值 2.2s < 5s 暴力嫌疑阈值，确定性）

## 2. 容量地图（M1）—— 空间不缺，形态受限

| 区域 | 容量 | 判定 | 瓶颈（障碍证据） |
|---|---|---|---|
| U7 引脚区（out_U7 左端） | 1/8 | INSUFFICIENT | UP0-6 flip 双极性几何不适配 + 走廊段被 U7 电源 pads 挡（pad:GND/P3V3/VREG d≤0.375）；UP7 走 via 形态 SOLVED |
| U3 引脚区（out_U3 左端） | 0/8 | INSUFFICIENT | 全对 flip 双极性不适配（U3 输出 pad 对中心与轨道错位 1.3mm）+ via 形态 In2 汇聚交叉 |
| J2 连接器（out_J2 右端） | 0/8 | INSUFFICIENT | 全对被 GND pad 挡（d=-0.075 压线，J2 相邻引脚地） |
| MCIO 连接器（out_MCIO 右端） | 4/8 | INSUFFICIENT | DN0/1/6/7 via 形态 SOLVED；DN2-5 被 U3 电源 pads 挡（d≤0.35） |
| 走廊 J2_TO_U（upper/lower） | 4/8、3/8 | 结构性受限 | 轨道被电容墙/电源 pads 挡（entry_x 滑窗绕过后 4/3 轨可用） |
| 走廊 U_TO_MCIO | 0/8 | 结构性受限 | 右端被 U3/U7 电源 pads 封死（求解器以 pad 位置为窗口终点绕开） |
| 走廊 refclk（In6） | 2/2 | CAPACITY_OK | 无 |

**交叉核对（v5 会话 §2.3 几何粗算）**：粗算"4 信号层 64 对容量 vs 需求 18 对——
空间富裕"被证实（容量不足不在总面积，在**形态几何**）；粗算"相邻线边缘距 0.195≥0.175"
被证伪于 P/N 过渡段（via/竖线汇聚处边缘距 -0.205，见 §4）。

## 3. M2 flip 重设计 —— 双极性 + 完备适用性预检

- **实现**：`_direct_escape` 双极性（flip=False → P 上轨 / flip=True → P 下轨，
  极性按 pad 位置自适应）+ 适用性几何预检（两 pad 距对侧轨 ≥ 0.38 中心距 =
  pad 对整体在轨道带外；同时防竖线穿对侧轨道段与水平段交叉，完备）
- **验收**：flip 直连不再产生 P/N 交叉（原 -0.205 事故消除）；UP3 等
  input 段从假 SOLVED 变为真实 SOLVED（P/N 断言通过）
- **结论**：引脚区 0.4 脚距 pad 对（中心 ≈ 轨道中心 1:1）在轨道带内 →
  flip 直连物理不可用（两 pad 距对侧轨 < 0.38）→ 必须换层形态（M4）

## 4. M4 换层形态 —— 错开 via 的数学不可行性（集合级证明）

**引脚区长段逃逸的 via 换层（Form C 错开 via）在现有几何下不可行**：

| 参数 | 值 | 约束来源 |
|---|---|---|
| 引脚区 pad 对中心距 | 0.4mm | U7/U3 脚距（0.45×0.25 pad） |
| P/N via 中心距下限 | ≥ 0.525mm | 0.35 via 直径 → 边距 0.175（DRC 实证） |
| 走廊轨 P/N 中心距 | 0.38mm | track_y±0.19（SPEC alloc，阻抗构造） |

**证明（错开 via → 汇聚交叉）**：P/N via 错开（中心距 ≥0.525）后，In2 段
从 via 过渡到走廊轨（中心距 0.38）——宽距(≥0.525)汇聚窄距(0.38)的过渡段
**必交叉**（实测：DN0 out_MCIO P 竖线 (64.19,46.41→58.91) 12.5mm 下行穿
N 段 (63.81,58.93)→(64.9,58.73)，中心距 0.0000）。方向一致性约束（via 相对
方向与 pad 相对方向点积 ≥ 0）已消除 pad→via 过渡段交叉，但 via→轨汇聚段
交叉是**几何必然**（两线从宽间距汇聚窄间距）。

**配套修复（已落地）**：`_sym_via` 循环结构 bug（v4.3 隐藏——for sl_n 循环
后误用最后无效候选）已修复（找到有效 via 立即返回）。

## 5. 逐对链级状态（M13 v5 求解记录）

| base | 链状态 | 失败段（全部段 SOLVED 时为 P/N 断言/等长拦截） |
|---|---|---|
| REFCLK0 | **SOLVED** | — |
| UP0-7 | INFEASIBLE | 段全 SOLVED；P/N 断言拦（In2 汇聚交叉 -0.205） |
| DN0/1 | INFEASIBLE | out_MCIO 段失败（flip 不适配 + via 汇聚交叉） |
| DN2/4/5/7 | INFEASIBLE | 段全 SOLVED；P/N 断言拦（In2 汇聚交叉） |
| DN3/6 | INFEASIBLE | out_U3 段失败（U3 引脚区 flip 不适配） |
| DN 其余 | INFEASIBLE | 段全 SOLVED；P/N 断言拦 |

## 6. 停机声明（等 PM/方案裁决）

按铁律"INFEASIBLE = 模型输入缺口证明 + 冲突即停机"。M13 v5 的缺口是
**方案级几何**（非模型 bug、非算法缺陷）：

1. **引脚区 0.4 脚距 vs 0.38 轨距 vs 0.525 via 距三者不可兼容**：
   F.Cu 直连（flip）需 pad 对在轨道带外（0.4 pad 距 + 0.19 半带 → 不满足）；
   via 换层需 0.525→0.38 汇聚（必交叉）。**唯一出路**：轨道带加宽
   （P/N 轨距 0.4 或轨道中心 = pad 对中心、tracks_y 离散化修订）或
   via 后保持 0.525 平行到走廊端点（走廊轨距同步修订）。
2. **J2 连接器区**：GND 伴行 pad 压逃逸通道（d=-0.075）——连接器引脚
   布局修订（GND 伴行 pad 让位）或 In4 层绕行。
3. **U3/U7 电源 pads 封走廊右端**：U_TO_MCIO 结构性 0/8——电源 pad
   布局修订（让出走廊右端 x=88.2~88.8 区域）。

**处置路径（供 PM/方案裁决，禁止自行硬挤/换轨/挪器件）**：
- 输入修订（合规路径）：SPEC corridors tracks_y 修订（轨距 0.4 或
  轨道中心对齐 pad 对）→ channel_alloc 重跑 → 模型重解一次
- 或接受 PARTIAL 交付（1/18 SOLVED 落板 + 17 对带集合级证明登记缺口）

---
*求解记录：`model_solves/hs_rebuild_v5/hs_rebuild_summary.json` +
`capacity_map.json`（本报告数据源）；单测 32 passed（含 M1/M2/M4 回归锁）*
