# K2 · R792 回执 —— #K2-312 §二 路线 A「现板铜 → 全链施工图 → P4」= **一次执行通过**

> 依据：#K2-312 §二「1. 抽取 16 网既有 track/via →《全链施工图》（源球→入段→廊道→门→目标球，逐线覆盖声明）＋相对登记 v2 的替换清单；2. **P4 判据 = 不新增违例**；3. **C13**：离线 smoke → 冻结 → 恰一次执行；二值必出」。
> 纪律：**板只读**（路线 A 采用现板铜，不改板）· 禁 Gerber/P5/下单/WORKER · 冻结四源不动。

## 〇、结论（二值）

**`FULLCHAIN_DRAWING_PASS`** ——

| 项 | 读数 |
|---|---|
| **全链覆盖** | **16/16 线**：`器件球(U6) → 入段 → 廊道 → 门 → 连接器焊盘(J2)`（两端皆落在**焊盘**上） |
| **P4 板级 DRC** | **170 违例（＝已分类基线）· 新增 = 0** · `unconnected = 0` ⇒ **过「不新增违例」判据** |
| 几何 | 16 线合计 **track / via / 总长** 见件；层 `F.Cu/In2.Cu/In5.Cu/B.Cu` |

## 一、全链施工图（路线 A：以现板铜为见证）

- 件 `K2_R792_FULLCHAIN_DRAWING_FROM_BOARD_v1.json`（hash16 **`d526347d1b1dac91`**）：逐线
  `device_pin`（U6 球）/`connector_pad`（J2 焊盘）/`n_tracks`/`n_vias`/`layers_used`/`length_mm`/`vias`/**`segments`**（完整几何）＋ **覆盖范围声明**（`FULL_CHAIN`）。
- **覆盖范围声明（C12 义务）**：源＝**器件球**（U6，非抽象格点）；目标＝**连接器焊盘**（J2）；**两端齐、逐段连续**。

## 二、替换清单（相对登记 v2 / R778 表）

- 逐线列明：`r778_planned_gate`（模型级指派）· `board_copper_full_chain` · `disposition` · 板侧 track/via 数。
- **处置口径**：路线 A 下 **16/16 线 `disposition = ADOPT BOARD COPPER`**——**模型级 R778 表未落到板上**；**本轮不做任何铜替换**（板只读）。⇒ 若后续要按 R778 表**替换**板铜，须**另件**（属板本体变更）。

## 三、P4 判据 ＋ 基线清零计划（承 #K2-307 §二.Q2.1）

- **判据 = 不新增违例**：基线 **170**（本次 kicad-cli 复算一致）· **新增 0** · `unconnected 0` ⇒ **P4 过**。
- **清零计划（分类逐条处置 · 供 DFM/Gerber 闸）**：
  - **真实缺陷 8**（`copper_sliver` 1 · `track_dangling` 1 · `via_dangling` 6）⇒ **Gerber/DFM 前逐条修复或具名豁免**；
  - **外观/库 162**（`missing_courtyard 54` · `silk_over_copper 37` · `track_not_centered_on_via 34` · `lib_footprint_mismatch 20` · `silk_overlap 15` · `silk_edge_clearance 2`）⇒ 归 **DFM 闸**逐项处置。

## 四、纪律 / 读数

- **C13 全程合规**：离线 smoke（2 线：`/tmp/k2dev/dev2.py`，确认两端焊盘齐）→ **冻结**落 `k2/` → **恰一次执行**；件内 `construction_runs=1`。
- **板只读**（`board_untouched=true`）· 未 bump SPEC/PCB · 未导 Gerber · 未进 P5 · 未下单 · 无 WORKER。
- 件：`.py/.json` ＋ 板级 DRC 原始件 `K2_R792_board_drc.json`。

OWNER-ITEMS: 0
