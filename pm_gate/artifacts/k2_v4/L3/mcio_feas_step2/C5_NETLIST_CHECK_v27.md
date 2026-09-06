# C5 核对记录 — lanes 0-7 ↔ J3/J4(MCIO)/ASIC 真板网表（2026-09-06）

> 状态：**部分可核 + 缺口登记**。评审条件 C5「lanes 0-7 ↔ J3/J4(MCIO)/ASIC 真板网表核对；
> 若映射不同 → 引擎单次重跑修正 lane 子集（禁暴力）」。核对源 = `k2/k2_v4.kicad_pcb`
> （真板 L0，BoardParser 读 pad→net，非手抄）+ `sch/*.kicad_sch`（真源）。

## 1. 可核对部分（真板 MCIO 连接器 ↔ lane 分配）✅

| 连接器 | 位置（L1 冻结） | 实测 pad 网名（BoardParser，L0） | lane 归属 |
|---|---|---|---|
| J3 MCIO x4 | 北带 y43-46 | `PCIE_DN_OUT0-3_*_MCIO`（DN 出）+ `PCIE_UP0-3_*`（UP 入）+ REFCLK0 | **lanes 0-3** |
| J4 MCIO x4 | 南带 y61-64 | `PCIE_DN_OUT4-7_*_MCIO` + `PCIE_UP4-7_*` + REFCLK1 | **lanes 4-7** |
| J2 SlimSAS | 东 | `PCIE_DN0-7_*` / `PCIE_UP0-7_*`（+ OUT*_J2 段） | lanes 0-7 host 侧 |

**核对结论**：真板 MCIO 侧 lane↔连接器分配 = **J3:0-3 / J4:4-7**，与 L1 frozen
（J3=0-3、J4=4-7）及 v26 引擎 `selected_lanes=[0..7]` **一致，映射无差异** → 引擎
无需因 lane 子集重跑。REFCLK0=J3、REFCLK1=J4 亦与 L1 REFCLK 分配一致。

## 2. 不可核对部分（登记缺口）⏳

- **DS320PR1601 芯片 ball→ASIC 内部 lane 映射**：现行真板 `k2_v4.kicad_pcb` + 全部 sch
  仍为 **U3/U7（WQFN-64 DS160PR810）双芯片旧布局**（网名 `PCIE_DN*_U3/_U7`、
  `ForgeOS:WQFN-64_10x5.5mm_P0.4mm` footprint、DS320PR1601 在 sch 0 命中）——
  **DS320PR1601 原理图/网表尚未落地**（L1/L2 v2.0 冻结的是规划，真板 ECO 未执行）。
- 因此「DS320PR1601 A_PER/B_PER/A_PET/B_PET band ↔ PCIe lane 0-7 ↔ J3/J4 引脚」的
  **芯片级映射无法在现行真板核对**（无该芯片网表对象）。
- **处置**：登记为 L3 前置（与 C3 同根：DS320PR1601 原理图 ECO 落地后一次核对）。
  v26 评审已背书「引擎对 lane 子集不敏感（最坏 64≤69）」，即使将来映射微调，引擎
  单次重跑即可修正（禁暴力）。

## 3. 证据

- 真板 = `k2/k2_v4.kicad_pcb`（read-only，BoardParser L0 解析，508 pads）。
- J3/J4/J2 pad→net 全表见本记录 §1（`PCIE_*` 前缀唯一化，P/N 各 8 lane + 2 REFCLK）。
- sch 真源 = `k2/sch/k2_sch.kicad_sch` + v5_* 子页（DS320PR1601 0 命中、DS160PR810 旧符号）。

## 4. v28 ECO 执行补记（2026-09-06，用户授权路径 b 范围 A）——C5 芯片级（范围 A）闭合

- **芯片级核对（范围 A）**：DS320PR1601 网表未落地前，芯片级核对 = per_ball 注入 vs
  `c5_chip_level_expect_matrix_v28.json`（期望矩阵，派生自已冻结 L1 v2.0 信号流 + 同源
  354 ballmap）**机器比对一致**：64 球全名/signal 逐球匹配、`selected_lanes=[0..7]`、
  `port_to_corridor {A:east}` = A 端口=host/J2 侧（L1 穿越语义）、ballmap 无 REFCLK 球
  （REFCLK 直通断言）→ **C5_SCOPE_A_MATCH**。
- **C5 闭合（范围 A）**：连接器级真板实测一致（§1，v27）+ 芯片级注入/期望矩阵一致
  （本补记）。scope-B：真板物理 ECO 落地后按期望矩阵一次实测核对（5 条 check_items），
  禁运行时改判。
