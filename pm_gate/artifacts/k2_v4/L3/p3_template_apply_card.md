# 任务卡 P3-A — 模板套用器 template_apply.py（命中模板 → 套参数化结构 → SolveInput）

> 阶段：KNOWLEDGE_REUSE_SDD §7 P3 前半（经验+确定性结合·模板套用）
> 施工位置：`_shared/eda_core/template_apply.py`（公共层，零单板特判）
> 角色：WORKER 施工，TASK MGR 复核
> 与 P3-B 并行：本卡开发套用器，P3-B 验证真板，合并点见「合并接口」

## 目标

新建 `template_apply.py`：把命中模板（五段 JSON）套用到 `SolveInput`，落地「经验提供怎么走（structure）+ 参数（params），确定性算法验证对不对（solve_pipeline）」——SDD §6「经验确定性 > 算法确定性」的代码实现。

## 权威输入（按序读）

1. `_shared/docs/KNOWLEDGE_REUSE_SDD.md` §4（五段 JSON）+ §6（经验+确定性结合铁律）
2. `_shared/docs/SOLVE_PIPELINE_CONTRACT.md` §1（SolveInput 定义）
3. `_shared/eda_core/solve_pipeline.py`（SolveInput 消费方式 + run_all）
4. `_shared/eda_core/matcher.py`（命中模板产出格式，P2-A 已就绪）

## 已钉死事实（勿重新论证）

- `SolveInput` = route_input + board_path + spec + rules + config（dataclass，契约 §1）
- 模板五段 JSON：applicability（客观事实）/ structure（怎么走）/ params（变量）/ validation（证据）/ provenance（来源）
- **模板只给形态不给坐标**：`params.gap_center_mm=null` 等坐标类参数必须运行时从实际板算，不写死（SDD §6.5）
- `produced=false`（cap_wall_ac）不得作确定解法，套用只作候选参考（SDD §4 红线）

## 设计约束（映射契约先写 docstring，字段级映射表）

1. 映射方向（params → config，structure → 求解引导）：
   - `params` 数值（track_pitch/track_width/clearance/pair_half_pitch 等）→ `SolveInput.config`
   - `structure` 经验形态（escape_strategy/landing_regions/via_layers/corridor_topology）→ 求解引导（经验提示，非强制，确定性引擎仍做主）
   - 坐标类 params（gap_center/outside_x_min 等 null）→ 运行时从 board/spec 算，禁止复制模板 null
2. 零单板特判：套用器通用，模板/板数据由调用方传入
3. 零外部依赖（仅标准库 + eda_core 内部）
4. `produced=false` → 套用结果标 candidate，不下发施工（沿用 P2-A 口径）
5. 迭代序确定性；映射契约以**字段级映射表**写进 docstring（模板字段 → SolveInput 字段）

## 合并接口（与 P3-B 对齐）

`apply_template(template: dict, base: SolveInput) -> SolveInput`：输入命中模板 + 基础 SolveInput，
输出增强 SolveInput（config 注入 params，spec/引导注入 structure）。
P3-B 验证的真板 SolveInput 作 base，套用后跑 run_all = 「模板驱动 K2 真板重跑」（P3 完整验收）。

## 验收（按序）

A. 单测：① params 数值正确注入 config ② structure 形态正确映射引导 ③ 坐标类 params 运行时算（不复制 null）
   ④ produced=false 标 candidate ⑤ 确定性（两跑一致）⑥ 零单板特判
B. 套用 4 模板（slimsas/mcio/cap_wall/corridor）→ 各自产出增强 SolveInput，结构合法（贴输出）
C. 套用后 SolveInput 跑 `solve_pipeline.run_all`（合成板）→ 五阶段不崩（贴结果）
D. `pytest` 全绿 + 粘贴输出；零新增 pip 依赖
E. 零单板特判（grep `k2_v4`/板坐标/连接器名 → 空）

## 禁止

- 禁止把模板坐标写死/复制到新板（模板只给形态，坐标运行时算）
- 禁止 produced=false 模板作确定解法下发
- 禁止写死 K2 板名/坐标/连接器名
- 禁止引入第三方包
