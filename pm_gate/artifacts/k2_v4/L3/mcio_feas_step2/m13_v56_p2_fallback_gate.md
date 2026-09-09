# m13 v56 — 流程红线落地记录：施工禁自搜（drawing_only fail-closed）

> 用户裁决（2026-09-09）：施工不能靠连连看解决 → 禁止现场修改设计/自搜兜底；
> 直接不干、打回施工图。违例即停机。本记录 = 该红线落地 + 诚实基线（打回清单）。

## 红线语义（从此生效）
- 施工层（hs_route_model 阶段⑤）只做**按图连线**（连连看）。
- 每段逃逸端必须有图纸节点（连接器端 = `landing` ASSIGNED 行；芯片端 =
  `chip_landing` VIA_IN2 ASSIGNED 行）。
- 缺节点 → **当场拒绝**（INFEASIBLE, kind=NO_DRAWING_NODE，理由指明缺
  chip_landing/landing 行）→ **打回图纸层**。绝不自搜、不枚举形态、不现场改设计。
- 图纸层职责：把图补全（每段双端节点 + 轨道）。图纸层画不出 → 带守恒证据交输入决策。

## 代码
- 引擎 `_shared` 6ab6308（push 待 Gitea 恢复）：
  - `route_input.py` ModelConfig 新增 `drawing_only: bool=False`（缺省=旧行为，其他
    项目/测试字节不变；K2 配置显式开）。
  - `hs_route_model._escape_pair`：两个落点驱动分支（landing/chip_landing）消费失败后、
    形态自搜枚举前，`drawing_only=True` → 返回 NO_DRAWING_NODE（带双行有无证据）。
  - 新 helper `_lnd_pair_ok`（判定语义与消费分支同源，chip 侧须 method==VIA_IN2）。
  - 单测 +1（真板类，环境板路径缺时 skip；板在位环境生效）。
- k2 `route_model_config.json`：`hs_route_model.drawing_only: true`（K2 永久激活红线）。

## 诚实基线（drawing_only=true 后 e2e run9，对照 P0=16 SOLVED/18 INFEASIBLE）
- **34 段 → 1 SOLVED / 33 打回（NO_DRAWING_NODE）**。
- 仍 SOLVED：`PCIE_REFCLK0 input`（真·直连，无需逃逸枚举）。
- 曾靠**自搜假合格**的 15 条已清零：DN0-6/7 input、DN5/6 out_MCIO、UP0-3/6/7 out_J2、
  REFCLK1 input 等（自搜成功 ≠ 图纸合格，按红线一律不作数）。
- 打回 = 缺芯片端图纸节点（chip_landing）为主；连接器端 `landing` 行部分已存在但
  芯片端缺失仍整段打回（双端齐全才算合格）。

## 图纸层工作队列（下一步，33 段）
1. 每段补齐芯片端出逃节点（chip_landing：escape_column/via 坐标）——v53/v54 已建
   ColumnBook/EscapeTable/EscapeAllocator/ConstructionFact，**未接线**（v55 B1/B2）。
2. 补一张复活一段：construction 只消费图节点，图齐 → 连连看 SOLVED；图画不出
   （如 DN_OUT 西侧 GND 球阵墙）→ NO_ESCAPE 守恒证据，上全局统筹或交输入决策。
3. 消费接线点：solve_pipeline.run_solve 现只传 `landing=landing.allocation`；
   引擎原生支持独立 `chip_landing` 命名空间（`_chip_landing_by_net`）——P2 接入。
4. 单调收敛口径（红线后）：**真图纸合格数**（34 段中连连看 SOLVED 数），不再是
   含自搜的旧口径。

## 纪律
- freeze lock；引擎 `_shared` = f15b03e+6bebc1b+6ab6308（6ab6308 push 待服务器恢复）。
- 红线为最高优先：任何"缺图自搜/现场将就"路径发现即停机上报。
