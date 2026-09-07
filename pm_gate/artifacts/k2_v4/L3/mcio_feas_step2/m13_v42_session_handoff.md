# M14 v42 承接 — F8 证伪(命名数据驱动) + fail_forms 落报告 + D4 根因=U6 电源球挡轨行 + NEW SESSION PROMPT

> 承接 v41。产出物 = 整体 EDA TOPO ENG（拓扑引擎），K2 仅验证项目；能力都是 ENG 的。
> **唯一必读 = 本文件 + m13_v41_session_handoff.md §1/§6。** v41 事实钉死不变（capacity
> 全绿 5a5107b / alloc 34 / TRACK 36 / F1-F11）。

---

## 0. 一句话状态（ENG 视角）

F8"段名由旧走廊语义残留产生幽灵 out_* 段"**证伪**：段名由板网存在性数据驱动（`_chain_segments`
纯 net 匹配，`PCIE_DN_OUT{0-7}_*_MCIO`/`PCIE_UP_OUT{0-7}_*_J2` 均真实存在于板 f6273de6，
U6 球↔连接器 2 pad 网）。但 F8 现象背后有**两个真实结构问题**：
(a) solve base 枚举 = alloc 34 键 → 16 个 `PCIE_*_OUT*` 空链幽灵行（已修：solve_all_v4 跳
空链 base → 报告 18 lane base，确定性零解变化）；
(b) **D4 真根因 = U6 电源球（P3V3/GND 列 x≈90.2-90.9, y≈59-64）挡在特定轨行的 F.Cu
pad→corridor 直跑线上** → 逃逸形态全败（flip 双极性 -0.205 相向交叉），轨行净空与 SOLVED
逐 lane 精确相关（实测 8/8 DN lane 轨道行障碍扫描）。

本轮沉淀进 ENG（`_shared/eda_core/hs_route_model.py`）：
1. fail_forms（flip_False/flip_True 逐极性失败 reason+esc+cross 证据）落 solve INFEASIBLE 段记录
   （flip=False 曾被 last_fail 覆盖丢失，v41 L2310 提及但未落 report）。
2. solve_all_v4 空链 base 跳过（F8-a，18 base 报告语义）。

**停止（按 v41 §5 判据）**：D4 fix 全量第 2 次（fail_forms 版 + 结构修版）仍 0/18 bases
SOLVED（10/34 段）→ 立即停，带矩阵回模型层，不续命。D4 形态缺口 = 需新逃逸形态
（单障碍内层跨跃 Form-G，见 §4），属模型层形态扩展，非命名/簿记问题。

---

## 1. F8 裁决（证伪 + 定位，全部原始证据贴出）

| F8 主张 | 裁决 | 证据 |
|---|---|---|
| DN0 只有单 net 无 OUT 段，report 记 input+out_MCIO = 幽灵段 | **证伪** | 板 f6273de6 `(net "PCIE_DN_OUT0_P_MCIO")` 等 16 个 OUT 网真实存在（U6 球 M26↔J3 A2，每网 2 pad）；`_chain_segments`(L614-638) 按 `chain_in_pattern/chain_out_pattern` + 板网存在性过滤，config `chain_out_suffixes=[_U7,_J2,_U3,_MCIO]` 只有 `_MCIO`/`_J2` 命中板网 |
| out_MCIO 与 pad 实际 J2 端 x132.65 错位 | **证伪** | out_MCIO 段几何端侧 = MCIO/WEST（落点 P=(66.555,52.366)，sx 扫 66.555→64.3 = MCIO pad 列）；x132.65 是 DN0 **input** 网（chip↔J2）的右端，v41 探针拿错了 pad |
| 错位与 capacity 假墙同源（过期走廊名） | **证伪** | `_track_y_for`/`_corridor_for_x`/alloc 全按当前 corridor_id（EAST_CHIP_TO_J2/WEST_MCIO_TO_CHIP）数据驱动；零 J2_TO_U/U_TO_MCIO/upper/lower 消费（hs_route_model 内 grep 无旧名） |
| **真实问题 (a)** base 枚举 34 = 双簿记 | **证实并已修** | solve_pipeline.run_solve bases = alloc 34 SOLVED 键；16 个 OUT 键 `_chain_segments` 空 → 16 行 INFRA 幽灵行；lane base 链已把 OUT 网收为 out_* 段。修：solve_all_v4 跳空链 base → 报告 18 行 |
| **真实问题 (b)** D4 逃逸形态缺口 | **证实**（新证据见 §2-§3） | 24 失败段 flip 双极性全败；逐轨行 F.Cu 障碍扫描与 SOLVED 精确相关（DN4/6/7=行净空 SOLVED；DN1/2/3/5=P3V3 球挡行 INFEASIBLE） |

---

## 2. fail_forms 矩阵（v42 e2e report 原生，stages.solve.results[*].segments[*].fail_forms）

每段 flip_False/True 双极性失败 reason + 几何证据已落 report（此前仅 flip=True 幸存）。
18 lane base / 34 段：10 SOLVED / 24 INFEASIBLE；bases SOLVED = 0/18。**两类失败形态**：

### 形态 ①：via 换层 P/N 相向交叉（min_edge 恒 -0.2050 = 中心线交叉一个线宽）
段清单（chip 侧左逃逸为主）：DN0-3/5 input、UP2/UP4/UP7 input、UP0-3/5/6 out_J2、
DN2/4/5 out_MCIO（connector 侧）、REFCLK0/1 input。
- 例 DN1 input flip_False @(86.446,57.669) / flip_True @(95.696,59.500)。
- **根因（实证）**：轨行 F.Cu 直跑线被 U6 P3V3 球列阻挡。逐 lane 扫描（0.15 步，
  轨行 ty±0.19 从 pad x 到走廊入口 105.25/82.35）：

| DN lane | alloc ty | P3V3/GND 球命中（F.Cu 轨行） | solve |
|---|---|---|---|
| 0 | 58.3 | 行净空（fail 属 lane0 自身 pad 几何，见注） | INFEASIBLE |
| 1 | 59.5 | @(90.55, 59.31/59.69) | INFEASIBLE |
| 2 | 60.7 | @(90.40, 60.89) | INFEASIBLE |
| 3 | 61.9 | @(90.25, 62.09) | INFEASIBLE |
| 4 | 63.1 | CLEAR | **SOLVED** |
| 5 | 64.3 | @(90.85, 64.11) | INFEASIBLE |
| 6 | 65.5 | CLEAR | **SOLVED** |
| 7 | 66.7 | CLEAR | **SOLVED** |

注：DN0 行净空但失败 —— lane0 在最西球列 x84.85，P/N pad 对角（dx0.3/dy0.52），
交叉点在其自身 N pad 旁 (85.28,57.66)——flip=False P 上轨构造 pad 爬升即交叉；UP 侧同
类（UP2/4/7 input @MCIO pad 区 / UP0-3,5,6 out_J2 chip 侧）。UP_OUT/UP input 有另
GND 球列障碍（同扫描法可复现，轨行 y40-49 区）。

### 形态 ②：落点驱动逃逸无净空（LANDING，MCIO connector 侧）
DN0-3/6/7 out_MCIO：落点 P=(66.555, y) N=(66.555, y') sx 扫 66.555→64.3/62.5/55.3。
- **pad 几何 vs track_y 偏移**：MCIO DN_OUT pad 行 y45.75(J3)/61.45(J4)；落点行
  y52.4-71.5（x66.555 列）；轨道 ty 58.7-67.1。落点与轨行/ pad 行三者不共线 →
  In2 段在 (66.5,y落点)→(sx,ty) 竖爬段无净空（fail-closed 不改落点）。
- 实证：DN6 落点 P=(66.555,58.95) N=(66.555,66.45) —— P/N 落点垂距 7.5mm，非差分
  对级落点（landing 分配按网独立，两网落点未按对级成对约束）。

---

## 3. v42 变更（ENG `_shared/eda_core/hs_route_model.py`，commit 见 §6）

1. `_solve_pair_centerline_v4`：`fail_forms={flip_False, flip_True}` 逐极性累积
   （左/右逃逸、走廊 seg_ok、layers 计数、段组装交叉 4 失败点 _note_fail），INFEASIBLE
   返回携带 `fail_forms`（reason+esc+cross）。flip=False 失败不再被 last_fail 覆盖丢失。
2. `solve_all_v4`：`if not self._chain_segments(stem): continue` —— 空链 base（16 个
   OUT 键）跳过，报告 = 18 lane base。确定性：段解序/共享累积零变化（10 SOLVED 不变）。

单测零回归：baseline 9 failed 同集不变（7 hs_route_model + 1 routing_topology + 1
solve_pipeline）+ test_topview/test_capacity_audit/test_channel_alloc 过（33 passed）。

e2e（第 2 次全量，2m29）：capacity FEASIBLE / alloc 34 / landing FEASIBLE 不变；
solve bases 行 34→18，seg 10/34 SOLVED 不变（确定性引擎，结构修零行为扰动）。

---

## 4. 模型层缺口（下次主线 = D4 Form-G，非命名/簿记）

**结论：24 段失败 = 逃逸形态缺"单障碍内层跨跃"（mid-field hop），列堆/落点/竖排形态
均无法表达「轨行 F.Cu 直跑被单颗电源球中断 → In2 同轨行跨球 → 回 F.Cu」形态。**

- 触发面（实测，数据驱动可枚举）：chip 侧 DN input 轨行 y58.3-66.7 ∩ U6 P3V3/GND
  球列 x90.2-90.9（4 lane）+ lane0 极西 pad 几何；UP out_J2/input 同族（GND 球列
  y40-49）；MCIO connector 侧 LANDING 落点未按对级成对（DN6 P/N 落点垂距 7.5mm）。
- Form-G 建议（ENG 形态，零 revA）：pad→F.Cu 短 stub→via₁（障碍前缘-0.175）→
  In2 同轨行跨球窗→via₂（障碍后缘+0.175）→F.Cu 续行到走廊入口；P/N 平行 ±0.19，
  全候选 _pn_ok≥0.155 fail-closed。确定性固定序（x 窗口扫描 0.15 步）。
- LANDING 侧：对级落点成对约束（landing 分配已 D3 极性硬约束，缺 P/N 落点几何成对）。

**停止依据**：v41 §5 —— D4 fix 全量第 2 次仍非 18 SOLVED → 立即停带矩阵回模型层。
本轮 2 次全量（fail_forms 版 2m31 + 结构修版 2m29）均为 10/34 段、0/18 bases。

---

## 5. 省 CONTEXT 清单（NEW SESSION）

- **必读**：本文件 + v41 §1（F1-F11 钉死事实）。
- 勿重做：capacity/alloc/landing（全绿不动）；F8 命名调查（§1 已证伪钉死）；
  通道/轨行障碍扫描（§2 矩阵已全）。
- 勿读全文：m13_v10~v40 .md（v41 §1 已钉死）。
- hs_route_model 只 grep 定点：`_escape_pair`/`_landing_escape`/`_col_stack_escape`/
  `_solve_pair_centerline_v4`/`solve_all_v4`/`fail_forms`。
- 全量 e2e ≤2 次（Form-G 实现后验收用）；探针内联 python -c 用后即弃。

---

## 6. 资产（ECN-009 已 lock 0/0/0，commit+push）

| 资产 | repo | commit |
|---|---|---|
| `_shared` hs_route_model.py（fail_forms + 空链 base 跳过） | ic_hw_eda | v42 |
| `k2` e2e report（18 base + fail_forms 矩阵原生） | ic_hw-k2 | v42 |
| `ic_hw` 容器指针 bump | ic_hw | v42 |
| freeze | — | 0/0/0 |

---

## 7. NEW SESSION PROMPT（可直接粘贴）

---
承接 M14 v42。只读 `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v42_session_handoff.md` +
v41 §1（唯一必读）。

背景：capacity/alloc/landing 全绿（勿碰）。F8 已证伪钉死：段名数据驱动（板网存在性），
无旧走廊语义；已修 solve base 双簿记（34→18 报告行，fail_forms 落 report，ENG 已 commit）。
**唯一卡点（实证根因）= D4 逃逸形态缺 mid-field hop**：U6 P3V3/GND 球列（x90.2-90.9,
y59-64 & y40-49）挡 24 段中 chip 侧轨行 F.Cu 直跑；MCIO connector 侧 LANDING 落点
P/N 未对级成对（DN6 垂距 7.5mm）。10/34 段 SOLVED、0/18 bases，轨行净空与 SOLVED
逐 lane 精确相关（§2 矩阵）。

任务（唯一主线）：
1. ENG 实现 Form-G（单障碍内层跨跃形态）：pad→F.Cu stub→via₁(障碍前缘-0.175)→
   In2 同轨行跨球窗→via₂(后缘+0.175)→F.Cu 续行到走廊入口；P/N 平行 ±0.19，全候选
   _pn_ok≥0.155 fail-closed，确定性固定序（x 窗 0.15 步）。触发数据驱动（轨行 F.Cu
   段被单 pad 挡，两 via 点净空可证），零 revA。形态瀑布序：插在现有 VIA 形态后、
   LSWAP/col_stack 前（或按形态语义并入 col_stack 扩展）。
2. LANDING 对级成对：落点分配 P/N 几何成对约束（或 _landing_escape 落点对级校验扩展）。
3. 单测零回归（baseline 9 同集 + topview/capacity_audit 过）+ 新增 Form-G 单测
   （构造 轨行单球障碍用例：同参双跑确定性 + 净空断言）。
4. e2e ≤2 次 → 目标 18 bases SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘。
5. ECN-009：unlock→改→单测零回归→lock→status 0/0/0→commit+push。

纪律同 v41 §6：全前台自跑、禁 task() 委派、禁后台、同参≤2 带依据、禁独立零散脚本、
能力进 ENG K2 只消费、每步原始输出贴出不加工。
停止判据：Form-G 全量第 2 次仍非 18 SOLVED → 停，带 fail_forms 矩阵 + 障碍窗几何
（球窗坐标 vs Form-G 候选 via 点）回模型层，不续命。
---
