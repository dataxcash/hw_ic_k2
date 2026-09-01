# 任务卡 P3-B — K2 真板端到端（真板 k2_v4.kicad_pcb 跑 solve_pipeline 五阶段）

> 阶段：KNOWLEDGE_REUSE_SDD §7 P3 后半（经验+确定性结合·真板端到端验证）
> 施工位置：`k2` 项目（真板验证，组装 SolveInput 跑管道）+ 缺口归 _shared 补
> 角色：WORKER 施工，TASK MGR 复核
> 与 P3-A 并行：本卡验证真板物理可行性（手工配置），不依赖模板套用器

## 目标

组装真板 `SolveInput`（board_path=真板 + SPEC + rules + config + route_input），跑
`solve_pipeline.run_all` 五阶段，验证真板物理可行性；缺口明确记录（INFEASIBLE 带 evidence）。

## 权威输入（按序读）

1. `_shared/docs/SOLVE_PIPELINE_CONTRACT.md` §1-§2（SolveInput + 五阶段 I/O）
2. `k2/pm_gate/artifacts/k2_v4/L3/m13_v12_session_handoff.md` §6（真板 sha + 物理事实）
3. `k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json`
4. `_shared/eda_core/solve_pipeline.py`（run_all 接口 + SolveInput 消费）

## 已钉死事实（勿重新论证）

- 真板 `k2_v4.kicad_pcb` sha=`6c387dff`（唯一 board 输入）
- 合成板已通端到端，真板未跑（handoff §3）
- solve_pipeline 五阶段全真接；`SolveInput.board_path` 空则不崩溃（软依赖）

## 工作（按序）

1. 盘点真板 SolveInput 缺口：route_input / config / rules / spec 是否已就绪；缺则从真板 + SPEC 生成或复用既有机制
2. 组装真板 SolveInput（board_path 指向真板 k2_v4.kicad_pcb）
3. 跑 `run_all` 五阶段，记录各阶段 dataclass 输出（verdict + 关键字段）
4. 缺口明确记录：INFEASIBLE 必带 `reason` + `evidence`（契约 §4）

## 验收（按序）

A. 真板 SolveInput 组装完成（board_path=真板 + route_input/config/rules/spec 齐全，贴组装清单）
B. `run_all` 五阶段跑通或明确记录缺口（每阶段 verdict + 关键字段，贴输出）
C. INFEASIBLE 带 `reason`+`evidence`（结构化 dict，非 markdown 字符串）
D. 结果可追溯（solve_ref + input_fp 非空）

## 禁止

- 禁止绕过契约手工补丁（遇缺口回上层 ECO，不施工层越权）
- 禁止假成功（INFEASIBLE 如实记录，不粉饰）
- 禁止改 solve_pipeline 业务逻辑（缺口只记录，不改引擎）
- 禁止改真板 k2_v4.kicad_pcb（只读输入）
