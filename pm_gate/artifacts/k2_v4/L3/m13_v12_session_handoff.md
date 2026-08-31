# M13 v12 续接 — NEW SESSION PROMPT（2026-08-31）

> 权威承接（按序读）：
> ① `/home/fila/jqdDev_2025/ic_hw/MIGRATION_GUIDE_OLD_SESSIONS.md`（repo 拆分迁移）
> ② `/home/fila/jqdDev_2025/ic_hw/_shared/docs/EDA_EXT_SDD.md`（**北极星：通用流程分层架构**）
> ③ `/home/fila/jqdDev_2025/ic_hw/_shared/docs/KNOWLEDGE_REUSE_SDD.md`（**本 session 定调：知识复用体系，SQLite 案例库 + 匹配器 + 确定性验证**）
> ④ `/home/fila/jqdDev_2025/ic_hw/_shared/docs/SOLVE_PIPELINE_CONTRACT.md`（管道契约）
> ⑤ `/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/m13_v11_session_handoff.md`（上一代）
> ⑥ 本文档（最新状态）

---

## 0. 角色定位（工作模式，勿变）

**TASK MGR**：拆卡制定任务 → 用户转发 WORKER → 我复核 → 整体推进。
**不启动后台、不亲自施工。** 分析走模型 API，只读不改。
（唯一例外：用户明确"落盘方案/文档"时，写规划文档可亲自做，代码施工仍委托 WORKER。）

---

## 1. 开工第一动作

```bash
cd /home/fila/jqdDev_2025/ic_hw/k2 && /home/fila/jqdDev_2025/ic_hw/AppDir/sharun python3.11 \
  /home/fila/jqdDev_2025/ic_hw/_shared/pm_gate/cli.py --project k2_v4 sstatus
# + falsify list（红队 open 必查）
# + 确认知识库文件 _shared/knowledge/kb.sqlite3 是否存在（P1 里程碑）
```

---

## 2. 本 session 已完成（commit/push/tag，勿重做）

| 仓库 | commit | 内容 |
|---|---|---|
| `_shared` | `22d63d8` | solve_pipeline 阶段③ channel_alloc 真接（容量门禁 + _alloc_nets） |
| `_shared` | `e300a5b` | 阶段⑤ hs_route_model 真接 + **施工层消费 escape_landing 落点**（`_landing_escape` 落点驱动逃逸，fail-closed via==落点，17 单测全绿） |

> 契约层 **5 阶段全真接**：① feasibility ② capacity ③ alloc ④ landing ⑤ solve。
> 阶段①真接 + 阶段⑤机械接线（adapter_solve/run_solve）合并进 `e300a5b` 之前的工作区，随 3b 一并提交。

**本 session 核心转变**：从"AI 从零推导几何"转向"**案例复用 + 确定性验证**"。
已落盘 `_shared/docs/KNOWLEDGE_REUSE_SDD.md`（**尚未 commit**，见 §5）。

---

## 3. 当前状态（系统总体）

**契约层已闭环**：五阶段管道端到端跑通（合成板验证），施工层已消费落点。

**已知遗留缺口（勿重新论证）**：

| 缺口 | 根因 | 处理 |
|---|---|---|
| skew 缺口 | escape_landing 落点分配**逐信号独立锚定，无 P/N 对称约束** → P/N 跨 region（GAP vs OUTSIDE）链长差 ~4.5mm，`skew_ok=False` | 属层 3 缺陷，回 `escape_landing` 加 P/N 对级对称约束（同 region/镜像列） |
| 层 2 任务分解 | 未实现（只有规范），现**改造为"案例匹配器"**（KNOWLEDGE_REUSE_SDD P5） | 知识复用体系 |
| K2 真板端到端 | 合成板已通，真板 `k2_v4.kicad_pcb`(sha `6c387dff`) 未跑 | P3 阶段 |

---

## 4. 下一步（按 KNOWLEDGE_REUSE_SDD Roadmap）

按 SDD §7 分阶段，**SDD 驱动，禁止事件驱动**（先设计后施工，遇缺口回 SDD 改边界）：

1. **P1（🔴 最高）**：`knowledge_base.py` 建库（SQLite 单文件 `_shared/knowledge/kb.sqlite3`，schema 见 SDD §3.2）+ **把 K2 沉淀为首批案例模板**（SlimSAS x8 逃逸 / MCIO 逃逸 / AC 电容墙 / 走廊对级）。
2. **P2（🔴 最高）**：匹配器最小可用（特征提取 + SQL 检索），用 K2 自身闭环验证命中。
3. **P3（🟡）**：经验+确定性结合（模板套用 → solve_pipeline 验证）+ **K2 真板端到端**。
4. **P4（🟡）**：JLC/GitHub 数据源接入扩案例库。
5. **P5（🟢）**：层 2 改造 = 案例匹配器。

**每阶段用验收标准闭环，先 P1+P2 跑通"复用闭环"再扩量。**

---

## 5. 待办（本 session 收尾未做）

- [ ] `KNOWLEDGE_REUSE_SDD.md`（知识复用体系 SDD）**尚未 commit**——下一步先 commit（连同 handoff 本文档）。
- [ ] P1：SQLite 知识库建库 + K2 案例模板化（KNOWLEDGE_REUSE_SDD §7）。

---

## 6. 关键物理/架构事实（勿重新论证）

- K2 线性 ReDriver 拓扑：MCIO → ReDriver(U3/U7) → SlimSAS(J2)，两段级联工序（UP/DN 两条可并行分支）。
- J2 逃逸落点：列间空隙 x∈[133.295,134.355]（gap_center 133.825）+ 外侧 x>135.655，36 信号可全锚定（26 列间+10 外侧）。
- 落位板 `k2_v4.kicad_pcb` sha=`6c387dff`（唯一 board 输入）。
- 施工层已消费落点：`HSRouteModel.__init__(..., landing)` + `_landing_escape`，仅右端消费、fail-closed via==落点、左端零改动。
- 知识库唯一事实源：`_shared/knowledge/kb.sqlite3`（单文件，cp 备份/覆盖恢复），读写接口 `_shared/eda_core/knowledge_base.py`（sqlite3 标准库，零外部依赖）。

---

## 7. 铁律（继承 + 新增）

**继承（七步法）**：七步法 / 先算容量再布线 / 分析走模型API / DRC只核对不驱动 /
修订走输入 / 零revA特判 / 假成功零容忍 / 反暴力迭代 / 冲突即停机 /
可行性(定性)与施工(定量)分离 / 未明示不commit / 确定性工程 / 零单板特判 / 契约驱动。

**新增（本 session 定调）**：
- **经验确定性 > 算法确定性**：案例复用（生产验证过）优先于 AI 从零推导；未生产验证的模板（produced=false）不得作确定解法下发施工。
- **SDD 驱动，禁止事件驱动**：先设计后施工；遇缺口回 SDD 改边界，不打补丁。
- **知识库 = SQLite 单文件**：唯一事实源，备份=复制文件；禁止散落 markdown/json 作知识事实源。
- **案例复用不豁免验证**：模板只给"怎么走"，确定性算法给"对不对"；参数变了必须重跑 solve_pipeline。
