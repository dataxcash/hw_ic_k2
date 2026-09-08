# M14 v50 承接 — DN out_MCIO 归因推翻（v49「单一 landing→corridor 形态缺」不成立）；零代码停机，v51 按新定案施工

> 承接 v49。任务（NEW_SESSION_PROMPT_v50.md）：把 DN out_MCIO ×7 的「落点驱动逃逸无净空」做 ENG 形态补全 → ≈+7。
> **v50 结论：目标前提被实测推翻** — 不是单一 landing→corridor In2 衔接形态缺，而是 **alloc 锚错端点(B1) + 消费侧锁死(A) + alloc 缺 F.Cu stub 可达性门(B2) 三层叠加，且芯片侧本身还需新逃逸形态**。本轮零代码改动（probe 仅走 ENG API，无临时脚本），产出 = 归因定案 + v51 施工 prompt。

---

## 1. 钉死事实（v50 增量；勿重推）

| # | 事实 | 依据（ENG probe / 模型真实求解，非手推） |
|---|---|---|
| F1 | DN0 out_MCIO 段端点：ep[0]=J3 连接器 pad P(64.3,45.75)/N(63.7,45.75)（西），ep[1]=U6 芯片 pad P(84.6,52.366)/N(85.0,51.673)（东）；corridor WEST_MCIO_TO_CHIP x∈[65.05,82.35]，In2，track 58.7（P/N 行 58.89/58.51） | report + pair_endpoints |
| F2 | 落点表记录 `pad` 锚 = **芯片 pad** [85.0,51.673]/[84.6,52.366]（region MCIO 窗口 [50,90] 吞入 U6 芯片列 84.6-90 + 派生取 max-x pad）；落点 via 却落在走廊西隙 x=66.555（GAP，全部 8 net 同列）→ pad↔via 相距 18mm | report landing.allocation + escape_landing 派生逻辑 |
| F3 | 失败腿 = **F.Cu stub**（芯片 pad x≈84.6/85 → 落点 x66.555 横向 18mm），首个障碍 GND pad dist 0.05/-0.04（req 0.175）；**In2 走廊自落点全净空**（P/N 行 57.6-59.5，sx 66.555→82.35 全 CLEAR）→ C（缺载体层）排除 | probe_path_clearance / 场 API |
| F4 | 消费侧：`_solve_pair_centerline_v4` L3368-3377 把 `landing_pair` **只传 idx1/右逃逸**；东走廊（connector=J2=idx1 高 x）正确，西走廊 out_MCIO（connector=J3=idx0 低 x）**倒置** → 芯片侧被迫消费芯片锚落点 → 18mm stub 必死；`_escape_pair` L1305 一旦有有效记录即 fail-closed，**芯片侧 col_stack 自搜被压制** | 代码定点 + probe6 调用实况 |
| F5 | 决定性反证：**剥离全部 *_MCIO 落点** → 芯片侧自搜仍 INFEASIBLE（col_stack 两 flip 返 None，终报 VIA 交叉 @(84.66,52.92)）→ 芯片侧需要**新逃逸形态**（非 col_stack 既有形态可达） | 模型 solve_chain_v4('DN0') + _col_stack_escape patch |
| F6 | 可行几何（probe 已证净空）：(a) 芯片侧 pad-row dip：芯片 pad → F.Cu stub 西 0.3-0.6 → via@pad 行（84.3/84.0 或 84.7/84.4/84.1）→ In2 沿 pad 行西行至 corridor 东界 82.35 → 下钻至轨道行：全 CLEAR；(b) 连接器侧 V-jog：J3 pad → pad 列竖爬 46.5-49 → 横走至 (66.555,jog) → via → In2 上行至 58.89/58.51：全 CLEAR（45.75 本行横走被 GND -0.075 挡，须先竖爬） | 场 API 逐段 seg_ok |
| F7 | 已解字节锚（v51 施工不得破坏）：DN0-4/6/7 input 东向 col_stack（pad 84.85/85.15 y57 行，dir=+1 corr 105.25，腿 (84.85,56.67)→(84.85,58.11) 等）；REFCLK0/1；UP0-3/6/7 out_J2 LANDING（如 via 136.0,54.9/133.825,54.3）；J2 chip_landing per-ball | report solved 段 |

## 2. 根因定案（三层，v50 首次完整归因）

- **B1（生成性）**：region MCIO 落点 demand 锚 **max-x pad**（窗口 [50,90] 与芯片列 84.6-90 重叠）→ 记录 pad 字段 = 芯片 pad，落点却在连接器侧隙列 66.555。分配器把"连接器侧落点"锚到了该网对侧端点。
- **B2（契约性）**：alloc `_verify` 只查落点净空 + corridor_window_ok，**从不查 F.Cu pad→via stub** —— 产生 ASSIGN 但物理不可消费的记录（18mm stub 首段即被 GND 挡）。
- **A（消费侧）**：landing_pair 硬编码只到 idx1/右逃逸 + 无 pad 归属匹配。西走廊 connector=idx0 → 记录永远到不了左逃逸；芯片侧被迫消费并 fail-closed，压制了 col_stack 自搜。
- **补充**：即使修好 A+B，芯片侧 col_stack 在该 pad 行（y51.67/52.37，dy→行 ≈6.2-7.4mm，dir=-1）本身造不出（F5）→ 需**新形态 F6(a)**。

## 3. 停机上报（v50 纪律：缺形态不现场试）

- 本轮未落 kb / 未改 ENG / 未跑 e2e（净指标不变，solved=2 仍是 v49 证据）。
- v51 目标改为**最小可证两件套**（见 NEW_SESSION_PROMPT_v51.md），先合成板单测再 e2e ≤2 实测净增（DN7 北行 68.95/71.45 垂直翻转 + 同列 via 堆叠为高风险，勿预设全通）。

## 4. G5 自检

- 消费资产：v50 prompt + e2e 报告段级/落点表 + ENG 定点符号（_landing_escape/_escape_pair/_col_stack_escape/_solve_pair_centerline_v4/escape_landing.allocate）+ 两轮 Oracle 裁决（已蒸馏进本 handoff + v51 prompt）。
- 未消费：v43-v49 handoff 全文、kb 模板全文、m14 除 §2.8、topview、Oracle 长文原文。
- 熔断：无第 3 次 Oracle / 无暴力迭代 / 无临时脚本消融（全部净空证据走 ENG 场 API）。
- 零 commit：_shared/k2 工作树 dirty（escape_closure_analysis.py、hooks、.bak_v33_perball 等）均为 v49 前既有残留，非本卡产物，未动。
