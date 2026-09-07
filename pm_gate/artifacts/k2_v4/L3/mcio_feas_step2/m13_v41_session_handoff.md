# M14 v41 承接 — capacity 全绿 alloc 34 + D4 solve 逃逸形态缺口 + NEW SESSION PROMPT

> 承接 v40。v40/v41 已交付：TRACK 滑动语义（`_shared` 370e585）、TOPVIEW 能力
> （`_shared` 5ce1d2d）、capacity 假墙全拆（`k2` 5a5107b：capacity FEASIBLE + alloc 34）。
> **唯一必读 = 本文件。产出物 = 整体 EDA TOPO ENG（拓扑引擎），K2 仅验证项目；**
> **K2 实现过程必须是 ENG 的结果，不是临时脚本。能力都是 ENG 的，禁手搓零散脚本。**

---

## 0. 一句话状态（ENG 视角）

**capacity 门禁已彻底打通（FEASIBLE），alloc 34/34 全部分配** —— 通过拆除三个
"假墙"（全部源于**过期走廊名残留 + 输入声明缺失**，非物理）。剩余唯一卡点 =
solve 施工层 D4 逃逸形态（24 segments INFEASIBLE / 10 SOLVED，bases 级 0/34）。

---

## 1. 已钉死事实（勿重推）

| # | 事实 | 依据 |
|---|---|---|
| F1 | 当前板 `k2/k2_v4.kicad_pcb` sha=`f6273de6` = ENG 产出样本（rot90 只读）；**无上游/无真板/无外来基准**，K2=ENG 交付物 | AGENTS §8 + v40 |
| F2 | SPEC corridors 当前名 = `EAST_CHIP_TO_J2`(dn=PCIE_DN0-7/up=PCIE_UP_OUT0-7/refclk, x105-132) + `WEST_MCIO_TO_CHIP`(up=PCIE_UP0-7/dn=PCIE_DN_OUT0-7, x65-82)；band 名 `dn/up/refclk`。**旧名 J2_TO_U/U_TO_MCIO+upper/lower 已全部作废** | v41 实测 SPEC |
| F3 | 芯片 net 归属（escape_spec pins，确定性）：U3={PCIE_DN0-7, PCIE_DN_OUT0-7_U4} 16 对；U7={PCIE_UP0-7, PCIE_UP_OUT0-7_U3} 16 对 | v41 实测 |
| F4 | 主 SPEC 曾缺 `capacitor_walls` 段；已从 SPEC_k2_v4_c3poc 补入（count=32, C17-C32/C49-C64, mcio_side_x[75,90], j2_side_x[93,128], min_pitch 1.3） | v41 补 SPEC |
| F5 | `capacity_audit` VIA 阶段语义：per demand `via_zones`=列表逐 zone 累加（[左区,右区]，L198 注释），每 demand 可挂 2 zone（两端各 1） | 读码 L430-464 |
| F6 | **capacity = FEASIBLE**（TRACK 36/36、VIA J2 18/41+MCIO 18/65+U3 8/17+U7 8/17、CAP_WALL 16/16），**alloc solved=34/infeasible=0** | k2 5a5107b e2e |
| F7 | solve 卡点（D4）：10 segments SOLVED / 24 INFEASIBLE；失败 reason 全为 `_escape_pair` flip∈{False,True} 双极性失败：via 换层 P/N 相向交叉(min_edge -0.205) 或 落点驱动逃逸无净空 | v41 e2e report |
| F8 | **D4 可疑结构矛盾（未证实）**：PCIE_DN0 板上只有 `PCIE_DN0_P/N` 单 net（两端 pads 芯片 84.85↔J2 132.65），无 OUT 分段 net（chain_out_suffixes=_U7/_J2/_U3/_MCIO 全不匹配）→ `_chain_segments`(L614-638) 应只产 input 1 段；但 report 记 DN0=**input+out_MCIO** 两段，且 out_MCIO 与 pad 实际 J2 端(x132.65/135)**错位**。疑似 solve 段实例/段名生成残留旧走廊语义（与 capacity 假墙同源） | v41 探针对比 |
| F9 | TOPVIEW 已 ENG 化：`_shared/eda_core/topview.py`（gap_list 一次全量 + remediate 按 kind 分流 input_decl/physical/engine，fail-closed 不伪造），e2e report.topview 原生输出，单测 5 passed | _shared 5ce1d2d |
| F10 | 全局原则已入 `~/.config/opencode/AGENTS.md` §8：可行性=定性准入+可施工保证；守恒墙只能改输入；引擎对给定输入给确定答案（禁 guess/可能）；无真板/无上游，板=ENG 产物；能力都是 ENG 的 | v40-v41 裁决 |
| F11 | 单测基线 = 9 failed（7 hs_route_model + 1 routing_topology + 1 solve_pipeline，pre-existing） | /tmp/opencode/baseline_failed.txt |

---

## 2. 本轮已拆三假墙（勿重做，已 commit k2 5a5107b）

根因 = **e2e zone 派生仍用过期走廊名**（J2_TO_U/U_TO_MCIO+upper/lower），SPEC 已 EAST/WEST+dn/up
→ zone 全错位（U3 被塞 30 假需求）；**主 SPEC 缺 capacitor_walls** + via_cap 无差别全标 → CAP_WALL=0。

修复（数据驱动、零过期名）：
- `derive_capacity_demands(spec, corridors, escape_spec, config)`：连接器端 zone 从
  config.escape_landing.regions（kind=CONN, corridor_id 匹配）声明派生；芯片端按 base 族
  归属 escape_spec pins chip_ref；via_cap 只标 series_cap_wall corridor 的数据对（16 非 32）。
- config：J2/MCIO region corridor_id 更新 EAST/WEST 当前名。
- SPEC：补 capacitor_walls（源 c3poc count=32）。

结果：VIA U3 30假→8真(8/17)，J2 18/41、MCIO 18/65、U7 8/17；CAP_WALL 16/16 → **FEASIBLE → alloc 34**。

---

## 3. 省 CONTEXT 清单（NEW SESSION 强烈遵守）

**必读（唯一）**：本文件。

**勿读全文 / 勿重做**：
- m13_v10~v40 任一 .md 全文（事实在 §1 已钉死）。
- TRACK 滑动修复 / capacity zone 派生 / AC 墙声明修复 / D2 诊断（全部已 commit 闭环）。
- 手搓探针重读 e2e report/capacity/geometry 数据（§1 已钉死）。
- 旧走廊名（J2_TO_U/U_TO_MCIO/upper/lower）任何讨论；旧板 6c387dff。
- 全量 e2e / --all-v4（D4 需**定点** solve 段级调试，勿全量空跑）。

**勿整读源码，只 grep/定点读**：
- `hs_route_model.py` → 段实例/段名生成（D4 核心）：`_chain_segments`(L614-638)、
  `chain_in_pattern/chain_out_pattern/chain_out_suffixes` 消费处、`solve_all_v4` 段循环、
  segname="input"/out_J2/out_MCIO 的构造来源（**查 out_MCIO 名从哪来 = F8 首要动作**）、
  `_escape_pair` 失败兜底 L1480/L1493、`_landing_escape` L1611。
- `topview.py`（已 ENG 化，勿重写；只消费）。

**勿加载**：capacity_audit/channel_alloc/segment_corridor/route_input（已闭环，勿重读）。

---

## 4. 下一步（D4 solve 逃逸形态，唯一主线）

### 目标：solve 34→18 SOLVED（10 segments 已 SOLVED，剩 24 段）
1. **定位段名错位（F8 首要动作）**：找 solve 段实例生成处（谁产出 DN0 的 out_MCIO 段名，
   而 DN0 实际右端 pad 在 J2 x132.65）。grep solve_all_v4 的段循环 + segname 构造，对比
   `_chain_segments` 产出 vs report 段名。若为旧走廊语义残留（段名按旧 DN→MCIO/UP→J2
   映射），修正为按 alloc corridor 实际端侧（数据驱动，同 5a5107b 方式）。
2. **带 fail_forms 明细**：solve 记录带 flip=False 失败 reason（L2310 fail_forms 已有，
   未落 report）——确认每失败段 flip=False 为何失败（缺哪种形态 vs 纯无解）。
3. **确认后修**：段名/端侧修正 → 重跑 → 逃逸端侧正确后形态瀑布（DIRECT/VIA/LSWAP-V/
   col_stack）应能解出大量段。若仍失败 → 按 F7 失败机制给形态瀑布扩展触发。
4. **单测零回归**：baseline 9 failed 同集不变 + test_topview/test_capacity_audit 过。
5. **e2e ≤2 次** → solve 18 SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘。
6. **ECN-009**：unlock→改→单测零回归→lock→status 0/0/0→commit+push。

### 不再做（已闭环）
- capacity/TRACK/VIA/CAP_WALL/zone 派生/AC 墙声明（5a5107b 已全绿，勿重碰）。
- "真板/上游"框架讨论（AGENTS §8 已立：板=ENG 产物，无外来基准）。

---

## 5. 停止判据

- D4 fix 全量第 2 次仍非 18 SOLVED → 立即停，带 **fail_forms 矩阵**证据（哪些段/哪端/
  flip=False 失败 reason + pad 几何 vs track_y 偏移）回模型层定形态缺口，不续命。
- 单测回归失败 → 回查该步，不带依据不重跑全量。

---

## 6. 纪律（延续 + 强化）

全前台自跑、**禁 task() 委派**、禁后台长跑、禁暴力迭代（同参≤2 带依据）、
**禁新建独立零散脚本**（探针内联 python -c 用后即弃，且只用于验证不用于产出）、
**能力必须沉淀进 ENG（_shared/eda_core），K2 组装只消费 ENG**、禁 chmod 自解。
每步原始输出贴出不加工。

---

## 7. 资产现状（已 commit+push）

| 资产 | commit | 状态 |
|---|---|---|
| `_shared` TRACK 滑动语义 | 370e585 | push |
| `_shared` topview（TOPVIEW GAP-LIST + 处置） | 5ce1d2d | push |
| `k2` e2e 接 topview | 44a5593 | push |
| `k2` capacity 假墙全拆（FEASIBLE + alloc 34） | 5a5107b | push |
| `ic_hw` 容器指针 bump | 1d71794 / 2c35c13 | push |
| freeze | — | 0/0/0 |

---

## 8. NEW SESSION PROMPT（可直接粘贴）

---
承接 M14 v41。只读 `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v41_session_handoff.md`（唯一必读）。
**产出物 = 整体 EDA TOPO ENG（拓扑引擎），K2 仅验证项目；K2 过程必须是 ENG 的结果，不是临时脚本；能力都是 ENG 的。**

背景：capacity 门禁已全绿（k2 5a5107b：TRACK 36/36、VIA 4 zone 全 ok、CAP_WALL 16/16 → FEASIBLE，
alloc solved=34/infeasible=0）。三假墙（过期走廊名 zone 派生、SPEC 缺 capacitor_walls、via_cap 无差别）已拆。
剩余唯一卡点 = solve 施工 D4 逃逸形态：10 segments SOLVED / 24 INFEASIBLE，bases 级 0/34，
失败全为 `_escape_pair` flip 双极性全失败（via 换层 P/N 相向交叉 min_edge -0.205 / 落点驱动逃逸无净空）。

任务（唯一主线）：
1. **先证 F8 段名错位**：solve 段实例/段名生成处（谁给 PCIE_DN0 产 out_MCIO 段，而其 pad 右端在 J2 x132.65）——
   只 grep `hs_route_model.py` 的 `_chain_segments`(L614-638)/chain pattern 消费/solve_all_v4 段循环/segname 构造；
   确认是否旧走廊语义残留（同 capacity 假墙同源）。修正为按 alloc corridor 实际端侧（数据驱动）。
2. **带 fail_forms 明细**（flip=False 失败 reason，L2310 fail_forms 已存在未落 report）到验证输出。
3. 修后重跑 solve：目标 18 bases SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘。
4. 单测零回归（baseline 9 failed 同集不变 + test_topview/test_capacity_audit 过）。
5. ECN-009：unlock→备份→改→单测零回归→lock→status 0/0/0→commit+push。

省 CONTEXT：勿读 m13_v10~v40 .md 全文；勿重做 capacity/zone/AC墙/D2/TRACK（已闭环 5a5107b/370e585）；
勿读 capacity_audit/channel_alloc/segment_corridor/route_input（闭环）；勿手搓探针重读 §1 已钉死数据；
勿全量 e2e/--all-v4（D4 定点段级调试）；hs_route_model 4500 行勿整读只 grep 段生成符号。

纪律：全前台自跑、禁 task() 委派、禁后台、禁暴力迭代（同参≤2 带依据）、禁 chmod 自解、
禁新建独立零散脚本（探针内联 python -c 用后即弃）、能力沉淀进 ENG（_shared/eda_core）K2 只消费。
停止判据：D4 fix 全量第 2 次仍非 18 SOLVED → 立即停，带 fail_forms 矩阵（段/端/flip=False reason +
pad 几何 vs track_y）回模型层，不续命。每步原始输出贴出不加工。
---
