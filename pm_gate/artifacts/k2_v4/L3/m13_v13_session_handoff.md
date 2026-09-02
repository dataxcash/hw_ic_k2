# M13 v13 续接 — NEW SESSION PROMPT（案例学习系统 escape_learner）

> 权威承接（按序读）：
> ① `/home/fila/jqdDev_2025/ic_hw/_shared/docs/CASE_LEARNING_SYSTEM_PLAN.md`（**本 session 定调：案例学习系统实施计划 rev2**）
> ② `/home/fila/jqdDev_2025/ic_hw/_shared/docs/KNOWLEDGE_REUSE_SDD.md`（知识复用体系 SDD）
> ③ `/home/fila/jqdDev_2025/ic_hw/_shared/docs/EDA_EXT_SDD.md`（北极星：七层架构）
> ④ `/home/fila/jqdDev_2025/ic_hw/_shared/docs/SOLVE_PIPELINE_CONTRACT.md`（管道契约）
> ⑤ 本文档（最新状态）

---

## 0. 角色定位（本 session 最重要的认知，勿再偏）

**TASK MGR**，但边界被钉死：

- **EDA 系统运行时，零 LLM。** LLM 只做一件事：**设计 + 开发 EDA 系统**（写 SDD、拆任务、开发确定性代码模块、复核）。
- LLM **不做**：读 PCB 走线、解析拓扑、匹配、套用、验证、DRC——这些全是确定性算法。
- 「学人类成功案例」= **开发一个确定性拓扑解析器**（读 PCB → 提拓扑构造），不是 LLM 去看走线/归纳意图。

> 历史教训（本 session 反复踩）：前几轮一直「spawn 子代理读代码归因缺口、从零推导修 K2 引擎」，
> 用户纠正了三次才扭过来——知识库数据来源是 **JLC 开源广场的人类成功案例**，经确定性解析器提取；
> 「选几层」是拓扑构造事实（读 PCB stackup 就知道），不是需要 LLM 理解的「意图」。

---

## 1. 当前状态（全部已 commit/push，勿重做）

| 里程碑 | 内容 | 状态 |
|---|---|---|
| P1 知识库 | `knowledge_base.py` + `kb.sqlite3`（SQLite 单文件，6 表） | ✅ |
| P2 匹配器 | `matcher.py`（特征交集评分）+ `feature_extractor.py`（契约 18 字段） | ✅ |
| P3 套用器 | `template_apply.py`（params→config, structure→spec 引导） | ✅ |
| P3 真板端到端 | `k2/tools/p3_k2_real_board_e2e.py` + 报告 | ✅ |
| gap1 修复 | `_track_y_from_alloc`（③→⑤ 数据流断层，跨廊道同 band 同 idx） | ✅ |
| gap2 修复 | `escape_landing` 镜像行（P/N 相向交叉） | ✅ |
| 层3 闭环 Phase A | `segment_corridor.py` + `channel_alloc` 段廊道窗口验证 | ✅ |
| 层3 闭环 Phase B | `escape_landing` 多区（J2/MCIO/U3/U7）+ P/N 极性硬约束 | ✅ |
| **案例学习计划 rev2** | `CASE_LEARNING_SYSTEM_PLAN.md` + `jlc_cases_raw.json`（6 个成功案例） | ✅ |

**方向修正（rev2 确立）**：Phase A/B 保留（是确定性系统能力）；Phase D（层4 形态卡）**停**（从零推导修引擎，方向错）。

---

## 2. 下一步任务（本 session 继续，核心）

### 开发 `escape_learner.py` —— 确定性拓扑解析器

**目标**：从人类成功工程的 `.kicad_pcb` **确定性提取拓扑构造**，落 `templates.structure`。纯几何判据、零 LLM、可测试、零单板特判。

**数据流（全确定性）**：
```
成功工程 .kicad_pcb → escape_learner（确定性解析）→ structure（怎么走）→ kb.sqlite3
→ matcher 匹配 → template_apply 套用 → solve_pipeline 验证
```

**要解析的拓扑构造五要素**（确定性几何判据，非 LLM 归纳）：
1. **扇出方式**：连接器焊盘 → 过孔的几何关系（直打过孔 / 引出再打 / 层切换位置）
2. **层分配**：差分对走线分布在哪些层（表层微带 / 内层带状线）
3. **等长蛇形**：走线上连续同向弯折段（几何判据：连续 N 个弯折 + 包络宽度 < 阈值）+ 位置 + 振幅
4. **AC 耦合位置**：TX 线上串联电容 footprint 的位置
5. **REFCLK 走法**：独立层 / 包地

**第一步（先做，勿跳）**：
1. 读 `_shared/eda_core/drc_rules.py` 的 `BoardParser`（已有 pad 解析），确认现有能力（pad/segment/via 解析到哪一步）
2. 基于 BoardParser 现状，写 escape_learner 的解析规则设计（docstring 字段级设计说明），TASK MGR 复核后再施工
3. 施工 + 单测（用合成小 PCB fixture 验证五要素解析正确）

**数据源**：`_shared/knowledge/jlc_cases_raw.json` 已列 6 个生产验证过的成功工程（5 oshwhub + 1 GitHub SlimSAS）。克隆工程 → escape_learner 解析 → 落库。MCIO（SFF-TA-1016）JLC 空白，需 GitHub/厂商补（后续）。

---

## 3. 关键文件

- `_shared/docs/CASE_LEARNING_SYSTEM_PLAN.md`（rev2 计划，本 session 北极星）
- `_shared/knowledge/jlc_cases_raw.json`（6 个成功案例原始数据，含 URL/验证状态/置信度）
- `_shared/knowledge/kb.sqlite3`（知识库，已 4 个 K2 模板；学到的成功案例 append 进去，勿覆盖）
- `_shared/eda_core/knowledge_base.py`（load_seed 接口 + put_template）
- `_shared/eda_core/drc_rules.py`（BoardParser，pad 解析入口）
- `_shared/eda_core/matcher.py` / `feature_extractor.py` / `template_apply.py` / `segment_corridor.py`（已就绪的确定性模块）

---

## 4. 铁律（继承 + 本 session 新增）

**继承**：确定性工程 / 零单板特判 / 契约驱动 / 假成功零容忍 / 问题回模型 / SDD 驱动禁止事件驱动。

**本 session 新增（最重要）**：
- **EDA 运行时零 LLM**：LLM 只设计+开发系统，不下场读走线/解析/匹配/验证。
- **知识库 = 学人类成功案例**：数据来源 JLC/GitHub，经确定性解析器提取拓扑构造；不放自己的失败记录当模板。
- **「学」不是「核对」**：打开成功工程 PCB 是「学怎么走」，不是「验证我的引擎对不对」。
- **拓扑构造是事实不是意图**：选几层/怎么扇出/怎么等长，都是读 PCB 确定性可得的，不需要 LLM 理解。
