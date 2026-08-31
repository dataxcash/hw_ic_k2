# M13 v11 续接 — NEW SESSION PROMPT（2026-08-30）

> 权威承接（按序读）：
> ① `/home/fila/jqdDev_2025/ic_hw/MIGRATION_GUIDE_OLD_SESSIONS.md`（repo 拆分迁移）
> ② `/home/fila/jqdDev_2025/ic_hw/_shared/docs/EDA_EXT_SDD.md`（**北极星：通用流程分层架构**）
> ③ `/home/fila/jqdDev_2025/ic_hw/_shared/docs/SOLVE_PIPELINE_CONTRACT.md`（管道契约）
> ④ `/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/m13_v10_session_handoff.md`（上一代）
> ⑤ 本文档（最新状态）

---

## 0. 角色定位（工作模式，勿变）

**TASK MGR**：拆卡制定任务 → 用户转发 WORKER → 我复核 → 整体推进。
**不启动后台、不亲自施工。** 分析走模型 API，只读不改。

## 1. 开工第一动作

```bash
cd /home/fila/jqdDev_2025/ic_hw/k2 && /home/fila/jqdDev_2025/ic_hw/AppDir/sharun python3.11 \
  /home/fila/jqdDev_2025/ic_hw/_shared/pm_gate/cli.py --project k2_v4 sstatus
# + falsify list（红队 open 必查）
```

## 2. 本 session 已完成（commit/push/tag，勿重做）

| 仓库 | commit | 内容 |
|---|---|---|
| `_shared` | `d24eb0b` | W6-D 竖排层换位形态（LSWAP_V，解 UP0 out_J2，零回归） |
| `_shared` | `d183cd0` | 差分容量审计引擎 `capacity_audit` + 逃逸落点分配器 `escape_landing`（11 单测） |
| `_shared` | `d183cd0` | 3 份架构文档（工序控制 / 任务分解 / 契约盘点） |
| `_shared` | `84b613d` | 求解管道契约层 `solve_pipeline`（6 dataclass + 5 阶段编排 + adapter 2真3桩，9 单测）+ `SOLVE_PIPELINE_CONTRACT.md` |
| `_shared` | **tag `v6.16-k2-m13-solve-pipeline-contract`** | 契约层里程碑 |
| 容器根 | `ca58cc9` | _shared 指针 → 84b613d |
| `k2` | `0dbab2e` | _shared 指针 → 84b613d |

> 另有 `EDA_EXT_SDD.md`（北极星）刚写，**尚未 commit**（见 §5）。

## 3. 当前状态（系统总体）

**核心转变**：从"施工层打地鼠"转向"分层 + 契约 + 确定性工程"。

**已就位**：
- 契约层 `solve_pipeline`（5 阶段管道：feasibility→capacity→alloc→landing→solve，2 真接 3 桩）
- 两个新引擎：`capacity_audit`（容量审计）+ `escape_landing`（落点分配，J2 36/36 证明可行）
- 诊断已定位真缺口：K2 16 对卡在 **J2 逃逸落点**，**非物理极限、可修**

**缺口（按 SDD 分层）**：
| 层 | 缺口 | 优先级 |
|---|---|---|
| 1 可行性 | 桩待接（routing_topology_gate + capacity_audit） | 高 |
| 2 任务分解 | ❌ 未实现（只有规范 `TASK_DECOMPOSITION_ENGINE_SPEC.md`） | 低（排最后） |
| 3 分配 | 桩待接；channel_alloc 未消费容量 | 高 |
| 4 施工 | hs_route_model 绕过契约 + 未消费落点 | 高（最大断点） |
| 6 编排 | 3 桩待接（feasibility/alloc/solve） | 高 |

## 4. 下一步（按 SDD Roadmap）

1. **接契约层 3 桩**（feasibility / alloc / solve）——已有引擎纳进管道。
2. **接 solve 桩时让 hs_route_model 消费 escape_landing 落点**——同时推进 K2 16 对 SOLVED。
3. **层 2（任务分解引擎）最后补**。

**每补一层，用 K2 端到端验证一次。** 补完 = 通用流程成型，K1/未来板卡直接复用。

## 5. 待办（本 session 收尾未做）

- [ ] `EDA_EXT_SDD.md`（北极星）尚未 commit——**下一步先 commit 它**（连同 handoff 本文档）。
- [ ] 接契约层 3 桩（feasibility/alloc/solve），先接简单的 feasibility+alloc，再接 solve（最难+主线关键）。

## 6. 关键物理事实（勿重新论证）

- U7@(93.825,44.7)rot0 TX列 x=98.85 竖排 P/N；U3@(93.825,62.7)rot180；J2@(133.825,53.7) 双列 x=132.65/135.0
- 落位板 `k2_v4.kicad_pcb` sha=`6c387dff`（唯一 board 输入）
- J2 逃逸落点：列间空隙 x∈[133.295,134.355]（gap_center 133.825）+ 外侧 x>135.655，36 信号可全锚定（26 列间+10 外侧）

## 7. 铁律（继承）

七步法 / 先算容量再布线 / 分析走模型API / DRC只核对不驱动 / 修订走输入 / 零revA特判 /
假成功零容忍 / 反暴力迭代 / 冲突即停机 / 可行性(定性)与施工(定量)分离 / 未明示不commit。
**新增（本 session 定调）**：确定性工程（算清再干一次对，禁 MCTS/重搜）/
零单板特判（通用机制进代码，板卡数据进 SPEC/config）/ 契约驱动（类型化数据流，禁 markdown 证据）。
