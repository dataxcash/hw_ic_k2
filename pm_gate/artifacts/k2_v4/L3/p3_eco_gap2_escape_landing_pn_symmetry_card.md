# 任务卡 P3-ECO-2 — 修复 gap2：escape_landing P/N 对级对称约束（skew 缺口）

> 阶段：P3 验证暴露缺口 gap2 的回上层 ECO（层 3 escape_landing 边界改动）
> 施工位置：`_shared/eda_core/escape_landing.py`
> 角色：WORKER 施工，TASK MGR 复核
> 与 P3-ECO-1 并行（不同引擎：本卡 escape_landing，ECO-1 channel_alloc）
> 铁律：SDD 驱动禁止事件驱动（先设计后施工）、问题回模型、冲突即停机
> 关联：handoff §3 已知遗留缺口「skew 缺口」同源

## 现象（P3-B 真板端到端实测 + handoff §3 已知，勿重跑论证）

- **gap2**：REFCLK1 落点驱动逃逸 P/N **相向交叉**（min 边缘距 -0.2050 < 0.175）→ INFEASIBLE
- **handoff §3 skew 缺口**：escape_landing 落点分配**逐信号独立锚定，无 P/N 对称约束**
  → P/N 跨 region（GAP vs OUTSIDE）链长差 ~4.5mm，`skew_ok=false`

## 根因（已实证）

`escape_landing` 对每个信号独立锚定落点（列间 GAP / 外侧 OUTSIDE），未把同一差分对的 P 与 N
绑定到对称位置（同 region / 镜像列），导致 P/N 落点相向交叉、链长不对称。

## 业务影响

差分对 P/N 链长失配 → 高速信号 skew 超标、REFCLK 逃逸交叉。违反高速差分对物理约束，
是 K2 高速段可制造性的确定性障碍。

## 修复方向（先设计后施工）

回 SDD 改边界：`escape_landing` 增加 **P/N 对级对称约束**——同一差分对 P/N 必须落同 region
（GAP 或 OUTSIDE 二选一，禁止 P 在 GAP、N 在 OUTSIDE），且落镜像列（列间锚定对称）。

**必须先写设计说明（约束定义 + 落点分配算法改动），TASK MGR 复核设计后再施工。禁止直接打补丁。**

## 验收（按序）

A. 设计说明：P/N 对级对称约束定义（同 region + 镜像列）+ 分配算法改动写进 docstring
B. 单测：① P/N 跨 region（GAP vs OUTSIDE）被禁止 → 同 region 锚定 ② REFCLK1 不交叉（min 边缘距 ≥ 0.175）
   ③ 确定性 ④ 既有 36/36 全锚定不回归（26 列间 + 10 外侧）
C. 真板重跑：REFCLK1 从 INFEASIBLE → SOLVED，skew 缺口缓解（P/N 同 region 链长差收敛）
D. 零单板特判（对称约束通用，不硬编码 J2 坐标/region）
E. `pytest` 相关套件全绿 + 零新增失败

## 禁止

- 禁止把 J2 列间/外侧坐标硬编码（对称约束须通用）
- 禁止改真板/SPEC 数值绕过交叉（问题回模型）
- 禁止只修 REFCLK1 特判（须通用 P/N 对级约束，零单板特判）
- 禁止假成功（skew/交叉如实记录）
