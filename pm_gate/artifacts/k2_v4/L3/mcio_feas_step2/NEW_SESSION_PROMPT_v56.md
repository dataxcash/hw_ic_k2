# NEW SESSION PROMPT — v56（承接 v55 复查：施工方案模块结构性修复，P0 收尾 + P1）

## 本卡任务
执行 m13_v56_remediation_plan.md（P0 收尾 → P1 开工前证明 → P1 主体）。
**不是几何 bugfix 卡，是结构修复第一棒。** 前置定论见 m13_v55_construction_module_review.md
（缺陷 A1/A2/B1/B2/C1/C2/D1/D2/E1/E2/E3）——**勿重新推导，勿加回已被证伪的修复**。

## 必读最小集（按序，只读这三个 + 本 prompt；勿读 v43-v55 handoff 全文）
1. `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/NEW_SESSION_PROMPT_v56.md`（本文件）
2. `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v55_construction_module_review.md`
3. `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v56_remediation_plan.md`
（其余工程文件一律 grep 定点，禁止整读。）

## 当前状态（已核实，勿重验）
- **引擎 `_shared` = pristine f15b03e**（v55 fallback 已整体回滚；模式位已恢复；
  `.bak_v33_perball` 已移出到 /tmp/opencode/p0_archive/；`git status` 全净）。
- **活动引擎单源**：仅容器 `_shared`（e2e 硬编码 sys.path）；k2/_shared 陈旧副本
  无活动 import（仅注释残留），物理删除留待专门 housekeeping，不在本卡。
- e2e 驱动：`k2/tools/p3_k2_real_board_e2e.py`（`E.main()`，OUT_DIR 默认
  `L3/p3_real_board_e2e/`）。pre-fix 基线 report 已在盘上（16/18 失败集）。
- 冻结态：freeze_ctl 当前 **unlocked**（前卡遗留），本卡工作前先确认/保持解锁，
  阶段收尾必须 **lock**。
- 单测基线：test_hs_route_model 37 passed/33 skipped；v53/v54 指定文件全绿；
  ls_route_model 8 条既有失败（与本卡无关，勿碰）；closure_check 收集期
  ModuleNotFoundError(pm_gate)，既有环境问题，勿碰。

## 证据/数字速查（复查定论，直接用）
- Pre-fix：34 段 = 16 SOLVED / 18 INFEASIBLE（12×-0.205 + 5×pn0.6 无净空 + 1×DN7
  落点 133.825）。芯片侧（U6/cap→U3，x≈84-93）出逃列**无 landing 登记**。
- landing 覆盖：J2=36/MCIO=16/**U3=0/U7=0**（U3/U7 region corridor_id=null）。
- 133.825 同列：DN0_P/DN6_P/DN7_P 被 landing 分到同一 via 列（y 差 0.6/0.9）。
- D3 极性：52 ASSIGNED 中 48 行 polarity_consistent=None。
- A2 反证（勿重做、勿加回）：串行贪心顺序耦合 → 任何"先解占位"的几何补丁必扰动
  后序 lane（实测转化 7 翻车 4+漂移 2）。**解药 = P2 登记簿接线 + P3 全局层，不是
  再修几何。**

## 施工顺序（本卡范围：P0 收尾 → P1）
### P0 收尾（无逻辑改动，先做）
1. `E.main()` 连跑两次（容器 `_shared`），比对两次 report 的
   `stages.solve.results` 逐 base/segment 逐字节一致（确定性）。
2. 存档 `m13_v56_p0_baseline.json`（34 段 status/reason + board sha + input_fp +
   双跑一致标志）至 `mcio_feas_step2/`。
3. 报告文件若随跑变化（时间戳/hash），不提交为代码改动（属运行产物）。

### P1（下一步，本卡主体，见 plan P1）
- **开工前证明（先做，编码前必须交）**：U3/U7 region 补 corridor 锚 + 区域
  不相交归属的 landing **试跑实验**（在 k2 装配层/派生层做最小改动跑通），
  预期芯片侧 failing 网（UP0-7 input/out_MCIO 等）**首次产出 landing 行**。
  证明可行后才正式改契约。
- 正式改：① SPEC band.nets(list) vs ChannelInput.nets(str) 形状统一 + 删
  nets_path 覆写；② MCIO/U3 重叠窗口（x∈[74,90]）→ 不相交所有权分区（pad 归属
  断言，重复/遗漏即 raise）；③ U3/U7 region corridor 锚（映射 EAST_CHIP_TO_J2 /
  WEST_MCIO_TO_CHIP 正确 band）。
- **触及面提示**：k2 装配工具/route_model_config.json/SPEC derived 派生为主；
  若涉 `_shared/eda_core/channel_alloc.py`（冻结区）须 unlock 且先交证明再动。
- 验收谓词：U3/U7 assigned>0；无 pad 归属二义；无 nets_path 覆写；全 34 网
  pad 归属闭包完备。全局失败集与 P0 基线对比**只许收缩**（至少不因 P1 平移）。

## 纪律（硬性）
- **全前台零委派**：禁 task()/禁 oracle/禁后台。
- 每阶段：开工前证明 → 编码 → 机器验收谓词 → lock → commit（双仓按需）→ push。
- 单调收敛：结束状态失败集单调不增；禁止以"已知账/另卡处理"作为出口。
- 冻结边界：L1/L2 frozen、k2_v4.kicad_pcb、SPEC 物理几何/净空值不动；引擎
  hs_route_model 几何在 P2 前冻结（本卡不碰）。

## 勿做 / 勿加载
- 勿整读 hs_route_model/solve_pipeline/channel_alloc/escape_* 任一文件（grep 定点）。
- 勿读 v43-v55 handoff 全文；勿重新推导 18 条失败几何。
- 勿重跑历史 diag1-12 探针（针对已废弃 fallback 假设）；勿加回 fallback。
- 勿全量 pytest；勿碰 ls_route_model 既有失败与 closure_check 收集错误。
- 勿提交 mcio_feas_step2 里与本卡无关的历史 untracked 杂物（v52 审计/探针脚本等）。
- 勿删 k2/_shared 物理目录（留专门 housekeeping）。
