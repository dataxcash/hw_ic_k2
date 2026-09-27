# K2 · R794 回执 —— #K2-313 §三「170 处置台账 ＋ Gerber 全套 ＋ DFM ＋ 全版体检」

> 依据：#K2-313 §三「1. 170 warning 处置台账（真实缺陷 8 ⇒ 就地修复 或 **具名豁免**〔入册登记＋理由〕；外观/库 162 ⇒ DFM 闸）；2. Gerber 全套导出；3. DFM 报告；4. 全版体检报告；5. 板本体变更仅限本工单声明域 · 下单停线」。
> 纪律：**板只读**（8 条真实缺陷走**具名豁免**，不改板）· 下单停线 · 无 WORKER · 一次执行。

## 〇、结论（二值）

# **`R794_PASS`**
- **DRC**：170（**error = 0** · warning 170）· **真实缺陷 8 逐条具名豁免（登记 8/8）** · `unconnected 0` · `clearance 0` · `schematic_parity 0`。
- **Gerber 全套**：**28 件**（8 铜层 ＋ 阻焊 ×2 ＋ 丝印 ×2 ＋ 边框 ＋ job ＋ Excellon 钻孔 ×7 ＋ 钻孔图 ×7）· rc=0。
- **DFM（目标通道）**：16/16 **PASS**（via 预算 · 线宽 · 全链）。
- **下单**：**停线**（owner 闸）。

## 一、170 处置台账（在册登记制）

件 `K2_R794_WARNING_DISPOSITIONS_v1.json`（hash16 **`6a70a6d0c0b651e2`**）：**170 条逐条**登记
`type / severity / items(uuid,pos) / disposition / reason / real_defect`。

| 类 | 条数 | 处置 |
|---|---|---|
| **真实缺陷（8）** | `track_dangling` 1 · `via_dangling` 6 · `copper_sliver` 1 | **具名豁免（在册＋理由）**：全部位于 **MCU/低速/电源域（x≈29–50）**，**不在 16 条目标通道**上 |
| **外观/库（162）** | `missing_courtyard` 54 · `silk_over_copper` 37 · `track_not_centered_on_via` 34 · `lib_footprint_mismatch` 20 · `silk_overlap` 15 · `silk_edge_clearance` 2 | **归 DFM 闸**逐项登记处置 |

**为何豁免而非就地修复（离线 smoke 证据 · C13）**：`/tmp/k2dev/smoke_prims.py` 实测——**删除 dangling 件会级联产生新的 dangling 端**（删 7 件后 `track_dangling` 反成 4），且**裸存 `.kicad_pcb` 丢库上下文**产生伪 `lib_footprint_issues 54` ⇒ **板编辑不可取**，改**在册豁免**（板保持受审 l8 逐字节不变）。

## 二、Gerber 全套（#K2-313 §三.2）

件 `K2_R794_GERBER_MANIFEST_v1.json`（hash16 **`d63ff33ba52ba346`**）＋ 目录 `gerber_r794/`：
- **铜层 8**：`F/In1..In6/B.Cu`；**阻焊** `F/B.Mask`；**丝印** `F/B.Silkscreen`；**边框** `Edge.Cuts`；**job** `*.gbrjob`；
- **钻孔**：Excellon（mm）＋ 逐层 `.drl` ＋ 钻孔图 `*_drl_map.pdf`；
- 逐件 `bytes/sha16` 在 MANIFEST。**源板仍为受审 l8**（sha16 `7a5c89913d6e5d0a`）。

## 三、DFM 报告（目标通道逐项 · §三.3）

件 `K2_R794_DFM_AND_CHECKUP_v1.json`（hash16 **`2a9378c8e0d0a2d2`**）：16 条目标通道逐线 `tracks / vias / via_budget_ok / layers / min_width_ok / verdict=PASS`；
全局：`clearance 违例 0` · `unconnected 0` · `schematic_parity 0` ⇒ **DFM 目标通道 PASS**。

## 四、全版体检报告（呈 owner · §三.4）

`checkup`：板 sha16 `7a5c89913d6e5d0a` · **DRC total 170（error 0 / warning 170）** · 真实缺陷 8 **已登记 8** · **Gerber 28 件** · **下单停线**。
⇒ 供 owner 决定是否下单（花钱 = owner 五类）。

## 五、纪律 / 边界

- **板只读**（`board_untouched=true`）· 未 bump SPEC/PCB · **下单停线** · 无 WORKER · 冻结四源不动。
- **C13**：离线 smoke 覆盖「删件/存板/DRC/Gerber 导出」原语；交付脚本**恰一次执行**产出上件（其中 1 处 layer-API 笔误在**出件前**离线修毕——如实注明）。

OWNER-ITEMS: 0
