# NEW SESSION PROMPT — v57（承接 S0 完成：S1 图纸生成器 设计细案 → 实现）

## 本卡任务
执行 m13_v57_execution_plan.md 的 **S1**：图纸生成器（构造性可行 / 守恒证书 /
禁贪婪 / 序无关）——**先交设计细案文档（开工前交付），再实现，验收 A1.1-A1.4**。
**全前台零委派（用户明确）**：禁 task()/oracle/后台。

## 必读最小集（按序，只读这四个 + 本文件；其余一律 grep 定点或按路径查工件）
1. `NEW_SESSION_PROMPT_v57.md`（本文件）
2. `m13_v57_drawing_iron_law.md`（铁律 L1-L7，最高约束）
3. `m13_v57_execution_plan.md`（S1 验收谓词 A1.1-A1.4 / 门禁纪律）
4. `m13_v57_s0_gate_record.md`（S0 结果与工件路径）
（按需定点：`tools/p3_v57_s0_endpoint_model.py`、`m13_v57_s0_endpoint_model.json`、
`m13_v57_s0_audit_derived.json`、`tools/p3_v57_s0_audit_derived.py`）

## 当前状态（已核实，勿重验）
- 引擎 `_shared` HEAD **6ab6308**（=origin/main，工作树净，freeze **locked**）；
  k2 HEAD **b6a53ea**（=origin）。Gitea 凭据已修复（~/.git-credentials, store, 600）。
- **红线已生效**：`route_model_config.json` hs_route_model.drawing_only=true →
  e2e = **1 SOLVED（REFCLK0 input 直连，无节点需求）/ 33 NO_DRAWING_NODE 打回**。
- **S0 全过（A0.1-A0.4）**：权威端点模型 = k2_sch(68 网全链名) × DS320 ballmap ×
  placement。芯片 64 数据网：期望球位 vs 板 pad 64/64 吻合 + pad#==球名 64/64；
  REFCLK 4 = 直通不经芯片。审计：escape_spec 几何**作废**（32 坐标帧错 + 32 stub
  网名不在网表）；P0 landing 行 J2 36/36 对、MCIO 6/16 对 + **10/16 错锚**（DN_OUT0-4
  锚芯片端 = max-x bug）；U3/U7 0 行。

## 关键定论（勿重推，直接使用）
- **图纸锚点唯一来源 = S0 权威端点模型**。禁 x-window/max-x 反猜；板文件/escape_spec
  只当被审派生物，永不当标准（L4 单向）。
- 施工=连连看（L1，闸门保持）；图纸正确性=生成器**构造保证**（L2）；禁贪婪/顺序耦合
  （L3）；不可行=守恒证书（最小不满足集）；验收=机器谓词，不过不进下一阶段（L7）。
- 板上 U6 = DS320PR1601，354 pad == 354 ball 1:1，at(93.8,53.7,rot90)；
  **KiCad rot ↔ 数学约定 = −rot**（已实证）。
- 链名 = k2_sch 全链名（含 `*_OUT*_MCIO/_J2`）；REFCK 无芯片端。

## 执行（S1；plan 门禁 A1 全过才 commit 并进 S2）
1. **设计细案 doc**（`m13_v57_s1_generator_design.md`，先交后码）：资源层编码
   （芯片出逃列域/via 槽/走廊 lane/连接器出逃隙 —— 全部由权威端点+规则派生）、每层
   守恒条件、**确定性构造规则（含序无关论证：同输入任意确定性枚举序 → 图纸/证书逐字
   节一致）**、证书格式（层+资源+最小需求集）、与 alloc/landing/v53-v54 簿的职责边界、
   施工消费接口形状（chip_landing 独立命名空间喂 solve）。
2. **A1.1 开工前证明**：守恒条件判定用合成反例集对照独立穷举基准（"看似有隙实无解"与
   "看似无解实可行"两族），证书=最小不满足集。
3. 实现生成器（归属引擎能力或 k2 装配按设计定；涉 `_shared` 冻结区 → unlock + 该步
   证明/验收过 → 收尾 lock）。
4. 验收 A1.1-A1.4 全过 → lock + commit + push（k2，必要时双仓）。
   任一不过 → **立即停止**，报告，整改重验，不得带病进 S2。

## 勿做 / 勿加载（省 CONTEXT，硬性）
- 勿整读 `hs_route_model`(4900+)/`solve_pipeline`/`escape_landing`/`channel_alloc`/
  `route_input` 任一全文（grep 定点）。
- 勿读 v43-v56 历史 handoff/会话报告全文；**勿重推** U6 几何/坐标系/band 语义/
  chip pad y 带等历史推导 —— 全部已被 S0 权威模型取代，直接读 S0 工件与工具。
- 勿重跑 P0/P1 历史探针；勿依赖 `/tmp/opencode/*`（新会话不保证存在）；结果均已
  commit（工件 JSON/文档）或写在本文件。
- 勿全量 pytest；勿碰 ls_route_model 既有失败与 closure_check 收集错误。
- 勿消费旧 escape_spec 坐标、旧 landing 行锚、旧 region 窗口派生（作废，authority-first）。
- 勿删 k2/_shared 陈旧副本（留专门 housekeeping）。
- **本卡边界 = 图纸生成器本身**；不属于它的（solve 几何细节/DRC/逃逸形态微调）不展开。

## 环境速查
- 容器引擎真源：`/home/fila/jqdDev_2025/ic_hw/_shared`（e2e 硬编码 sys.path）。
- 冻结控制：`k2/pm_gate/freeze_ctl.sh {status|unlock|lock}`（阶段收尾必须 lock）。
- e2e 驱动：`k2/tools/p3_k2_real_board_e2e.py`（当前红线态基线 = 1 SOLVED/33 打回）。
- 双仓 remote 干净 URL；凭据走 `~/.git-credentials`（store）。
- 真板/工件路径：`k2/k2_v4.kicad_pcb`、`k2/boards/k2_sch.yaml`、
  `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/`。
