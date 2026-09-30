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
