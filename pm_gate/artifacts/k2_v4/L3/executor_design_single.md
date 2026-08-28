# L3 施工执行器设计（最小验证版 — 单差分对端到端）

> 宪法第三章：执行器是纯执行者，零运行时决策。本设计描述"单对验证"范围。
> 目标：证明脚本路径（逃逸→走廊→AC 电容桥接→等长）方法论可行，再扩展 18 对。

## 1. 施工范围（最小验证）

单对差分链路端到端：**J3 → AC 电容 → U3 → AC 电容 → J2**（一对下行）

选择：下行 DN0（PCIE_DN0_P/N）——从 J3 的 RX0 到 U3 再到 J2。

## 2. 网络拓扑事实（实测 k2_v4，2026-08-13）

链路分段（ReDriver 两侧 AC 电容断开）：

```
J2_pin ──[PCIE_DN0_P/N]─────────────┐
                                    ├ AC 电容（桥接两侧网段）
U3_pin ──[PCIE_DN_OUT0_*_U3]────────┘
J3_pin ──[PCIE_DN_IN0_*_MCIO]── AC 电容 ──[PCIE_DN_IN0_*_U3]── U3_pin
```

实测网名：
- J2 侧：`PCIE_DN0_P/N`（7 引用）
- U3 输入侧（MCIO 方向）：`PCIE_DN_IN0_P/N_MCIO` + `PCIE_DN_IN0_P/N_U3`（电容两侧分离）
- U3 输出侧（J2 方向）：`PCIE_DN_OUT0_P/N_U3` + `PCIE_DN_OUT0_P/N_J2`

## 3. 执行步骤（每步只读 SPEC + 只写坐标）

| 段 | 内容 | 输入 | 验证 |
|---|---|---|---|
| 段 0 | 逃逸预检（已完成） | measurements | 172 pin 全可布 ✓ |
| 段 1 | U3 左缘 DN0 pin → MCIO 侧 AC 电容 | SPEC.corridors + 电容坐标 | 0.4mm 节距单线 |
| 段 2 | AC 电容 → J3 上排 DN0 pin | 电容焊盘 + J3 pin | 0.6mm 节距 |
| 段 3 | U3 右缘 DN0 pin → J2 侧 AC 电容 | SPEC.corridors | 0.4mm 节距 |
| 段 4 | AC 电容 → J2 DN0 pin | 电容焊盘 + J2 pin | 走廊带 |
| 段 5 | 等长校验（对内 <0.15mm） | 段 1-4 长度 | 蛇形补偿预案 |

## 4. 执行器约束（宪法第八章）

1. 只读 `SPEC_k2_v4.json`，禁止修改
2. 坐标生成确定性（无随机/无 BFS/无 fallback）
3. 任何"放不下" → **立即停止并输出 SPEC 冲突报告**（哪段/哪个 pin/超多少），触发 ECN 回 L2，绝不自适应
4. 只操作 k2_v4.kicad_pcb 的副本（out 文件），原始板文件不动

## 5. 验证接口

- 产物：`k2_v4_single_pair.kicad_pcb`（含 1 对完整差分走线）
- QA G4.1 对照：F.Cu 上 PCIE_DN0 的 track 数 ≥2、0 过孔、板框未变
- 红队：变更 artifacts 自动触发证伪

## 6. 风险（预登记，触发即 ECN）

- R-ESCAPE-1：U3 左缘 0.4mm 节距余量 20µm，AC 电容 y 坐标若与 pin 网格错位 >20µm 即冲突
- R-CAP-1：AC 电容焊盘 0.3mm（MLCC_0201），桥接线两端对齐要求高
- R-NET-1：`PCIE_DN_IN0_*_MCIO` 与 `PCIE_DN_IN0_*_U3` 两网段靠电容桥接，KiCad netlist 需确认连通

## 版本

- v1.0（2026-08-13）
