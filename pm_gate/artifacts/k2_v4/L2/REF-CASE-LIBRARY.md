# REF-CASE-LIBRARY (K2 成品案例库 · #K2-456 sec.2.5 要求回填)

> 用途：§20「先查成品、再落算法」。本文件为**成品案例库**；本条目由 `R1448` 建立（此前仓库内**无**同名文件，各裁定引用的「REF-CASE-LIBRARY」即指本库）。

## A. 器件/板级成品锚（在仓）
- `pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_L1_A_ANCHOR_EVM_SNLU300A_v1.json`（TI DS320PR1601 EVM 锚）
- `.../K2_L1_A_ANCHOR_DS320PR1601_v1.json`（同芯片本体锚）
- 同芯片**开源双卡**（见 P6_OPEN_READINESS 诸件）
- TI `SNLA425 §1.1` **成组扇出/共享廊道**政策（参照：走线成组、共享干线）

## B. 引擎（重布线/消解）成品锚（在仓 · 可抄形状与纪律）
| 件 | 抄什么 |
|---|---|
| `tools/eda_eng/ripup.py` | **清单式拆除纪律**：逐件（网＋层＋几何）匹配，不做「顺手清理」，清单陈旧即 fail-fast |
| `tools/k2_p4_b2_in5_ripup_v1.py` | 全量/局部 rip-up-and-reroute 的形状 ＋ **两条口径教训**（判据须与验收闸同口径；协商计数须同口径，否则「违例=0」永不可达） |
| `tools/k2_p4_b2_in5_pf2_pathfinder_v1.py` | **成本面**范式：present 代价 ＋ history 代价（本仓迷宫已落「软引导代价面」） |
| `tools/k2_ripup_reroute_gen_v1.py` | 确定性「拆哪些／在哪布」计划生成（本板残差专用） |
| `tools/k2_p4_mroute_v1.py` | 本仓迷宫：`_unwind()` 快照 ＋ 阻断边优先之**一次重排**（`R1446`/`R1448` 落） |

## C. 外部（**许可受阻 · 只引形不抄**）
- freeRouting（AGPL）：rip-up & reroute 自动布线
- KiCad 交互布线器（GPL）：shove／walk-around
- 经典方法：协商拥塞 / PathFinder（McMurchie & Ebeling, 1995）

## D. 使用规则
1. **先查本库**：新子问题先在此登记「同类成品存在？」「可抄件？」「差异清单？」（§20 三问）；
2. **只抄形状与纪律**，不抄许可受限代码；
3. 找不到成品时**才**谈自研算法，并在 §20 件中写明「已查、无成品」。

## E. 引脚逃逸 / pin access（#K2-467 · 2026-09-30 增补）

- **在仓（机制类）**：
  - `tools/k2_pin_escape_plan_v1.py` —— 本仓**新落**：确定性（固定 4 方向序 · 首中即取）· **有界**（20 档步梯 ⇒ 每端点 ≤80 候选 · 无 while）· **具名拒绝**；
  - `tools/k2_lane_draft_v1.py` —— 同源确定性起草纪律（照图起草 · 放行闸 · 零搜索）；
  - `tools/k2_port_plane_stitch_v1.py` —— landing / `port_stub` 施加路径（逃逸资产属同类确定性件）；
  - `tools/k2_anchor_audit_v1.py` —— 锚定闸（每条加入件须有锚）；
  - `R1488 KEEPOUT` 硬保留 —— 逃逸资产之**载体**（保留区来源须为**焊盘正向推导**，非跑后普查）。
- **成品（判据类 · 只引形不抄）**：TI `DS320PR1601` EVM 引脚区/成组扇出实践（`SNLA425 §1.1`）· IPC-7351（焊盘几何/land pattern）· 业界 fanout/escape pass（KiCad fanout · FreeRouting · 商用工具 —— **许可受限**）。
- **用途与禁令**：为本仓**缺失的「布线前逃逸预留阶段」**提供**判据来源**（长度／净空／落层）；**禁止**把判据纯 ad-hoc 自设后硬试；判据修订须先引本库成品实践（§20.5）。
- **本窗读数**：真板预检 `go=FALSE` · 8 条具名拒绝聚集 `x≈31.8375` 致密引脚区（`go` 名单即争用消解图输入）。
