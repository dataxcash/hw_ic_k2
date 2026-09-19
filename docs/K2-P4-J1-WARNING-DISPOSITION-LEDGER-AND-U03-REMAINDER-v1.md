# K2 · P4 · **`J-1` warning 逐类处置台账** + **`U-03`/`M-09`/`J-7` 残余 9 件定位** · v1 · 2026-09-19

> 授权：**#K2-30 §2.3**（同批必闭项）· **#K2-32 §五-3**（`J-1`/`U-03`/`J-7` 未闭项）· 承 `#K2-31 §五`。
> 本件**只出证据**：**不改** `criteria/**`（判据只读；登记/阈值归 gate 属主 + 监理）· **不改**库/板/SPEC/生成器；临时仅 `/tmp/opencode`。
> ENG（ARCHER）· 2026-09-19 · 受审板 `l6 30fa849641323f98` · 判据锚 rev=2 · 装置：`kicad-cli 10.0.5 pcb drc --severity-all`（**全新 work-dir**，板+pro+lib 齐备）

---

## 1. `J-1`：DRC warning 逐类台账（受审板 `l6`，pro = `.l6.kicad_pro`（`ignore` 0/62））

**总读数**：违规 **164**（**全 warning**）· `error` **0** · `unconnected` **0**。

| # | 类型 | 计数 | 现行 manifest 登记 | ENG 建议处置（**均「不豁免」**，登记制而非 ignore） |
|---|---|---|---|---|
| 1 | `missing_courtyard` | 54 | ✅ 已登记 | 维持（图形级已知缺口 + L2 placement 项） |
| 2 | `lib_footprint_mismatch` | 20 | ✅ 已登记 | 维持（以板为准 W-8；与本件 §2 残余同源） |
| 3 | `silk_over_copper` | **37** | ❌ 未登记 | 丝印图形级：登记 + 归属 `U-05`/`J-4` 余项（丝印重排 = P5 出图前处置） |
| 4 | `track_not_centered_on_via` | **30** | ❌ 未登记 | 布线图形级：登记 + 归属**链内路由器产物**（段2 器）；逐条台账须出（本件给计数；逐条导出器可授权后做） |
| 5 | `silk_overlap` | **15** | ❌ 未登记 | 同 #3 |
| 6 | `via_dangling` | **4** | ❌ 未登记 | 逐条**已可具名**（见下）；归属 PDN/缝合孔步（段2 器） |
| 7 | `silk_edge_clearance` | **2** | ❌ 未登记 | 逐条**已可具名**（见下）；图形级（参考字段出框） |
| 8 | `track_dangling` | **1** | ❌ 未登记 | 逐条**已可具名**（见下）；归属 `mroute` 残段 |
| 9 | `copper_sliver` | **1** | ❌ 未登记 | 逐条具名（`In4.Cu` 铜箔毛刺）；归属 `In4` 分区几何（L2） |

### 1.1 小计数类逐条具名（0 剩余不可解释项）

| 类型 | 逐条 |
|---|---|
| `copper_sliver` (1) | `In4.Cu` 铜箔毛刺 ×1 |
| `track_dangling` (1) | 走线 `[GND]` (`F.Cu`) 端点悬空，段长 **0.7750 mm** |
| `silk_edge_clearance` (2) | ① `C87` 的参考字段 被板边裁剪 ② `D2` 的参考字段 被板边裁剪（均为 `Edge.Cuts` 侧） |
| `via_dangling` (4) | `[P3V3]` · `[PERSTA#]` · `[UART_TX]` · `[SWCLK_BOOT0]` 各 1 枚过孔（`F.Cu–B.Cu`），「未连接或仅单层连接」 |

> **ENG 声明**：以上 7 类**不请求豁免**；**不**以「接近 0」淡化（`copper_sliver`=1 · `track_dangling`=1 如实列 1）。登记件（`drc_warning_dispositions`）的**安装/签认归 gate 属主 + 监理**，ENG 不落 `criteria/**`。

---

## 2. `U-03` / `M-09` / `J-7`：`lib_electrical_level` 残余 **9 件**定位（受审板 `l6`）

装置：`k2/tools/k2_w8_footprint_audit_v1.py --board k2/hw/k2_v4_8L.l6.kicad_pcb --proj-lib k2/hw/lib`（58 件；审计板 sha16 = 受审板 sha16 = `30fa849641323f98` ⇒ 非陈旧）。

**汇总**：`identical 49` / `electrical_diff **5**` / `no_library_link 4` / `unloadable 0`（前值 `l5` = 4 / 28 / 24 / 2 ⇒ 显著收敛）。

| ref | `lib_id` | 板/库 pad | 差 pad 数 | `rel_geom_same` | 均匀平移 | 最大差 | **物理判读** |
|---|---|---|---|---|---|---|---|
| `U6` | `ForgeOS:DS320PR1601` | 354 / 354 | 166 | False | – | **dx 0.4 µm** | **亚微米级 pad 偏移**（数值/舍入级），非电气拓扑差 |
| `U1` | `ForgeOS:MCU_STM32G0_LQFP48` | **49 / 50** | 48 | – | – | **dx/dy 0.5 µm** + `pad_name_set`：库侧多 1 个**无名 pad** | 亚微米偏移 + 库侧 EP 无名 pad（`M-16` 已具名：板 49 带号 pad + 9 枚无号 `F.Paste`） |
| `L1` | `ForgeOS:L_0805_2012Metric` | 2 / 2 | 2 | False | – | **dx 0.5 µm** | 亚微米偏移 |
| `J3` | `ForgeOS:MCIO_4i_SFF-1016_RASide__1` | 38 / 38 | 38 | **True** | **True** | rot 表示差（180°） | **物理等价**（几何全等；仅旋转/原点约定） |
| `C85` | `ForgeOS:C_0402_1005Metric__2` | 2 / 2 | 2 | **True** | **True** | rot 表示差（180°） | **物理等价**（几何全等；仅旋转/原点约定） |
| `H1`–`H4` | `MountingHole_3.2mm_M3`（无库昵称） | 1 / – | 0 | – | – | `diffs: []` | **纯机械件**（无库链接；`refdes_sets_equal` 已排除 `H*`） |

**判据状态（不缩口径）**：`lib_electrical_level` 的现行 expect = `n_electrical_diff == 0 且 n_pad_name_set_only == 0`（**逐字节/精确等值**口径）⇒ 本板仍 **FAIL**（5 ≠ 0）。**ENG 不主张**「亚微米 ⇒ 等价 ⇒ 过」。

### 2.1 三条收口路径（**供监理裁；ENG 不择一**）

| 路径 | 内容 | 代价/边界 |
|---|---|---|
| (i) **载体侧对齐** | 库快照按板重建到**逐字节同**（或把板侧坐标改为库侧值）⇒ `n_electrical_diff → 0` | 改**库/生成器坐标** ⇒ 须授权；且 `U6` 166 pad 的 dx 差须逐一定位来源 |
| (ii) **判据侧具名容差** | 为 `lib_electrical_level` 引入**具名容差**（如 ≤0.5 µm 视同一致）+ `pad_name_set` 的 `H*`/EP 无名 pad 具名豁免 | = **改判据** ⇒ 判据只读 ⇒ 须 **版本 bump + 监理签认**；**不得**以容差掩盖真实差异（C-12） |
| (iii) **维持 FAIL** | 保持严格口径，`U-03`/`M-09`/`J-7` 维持未闭 | P4 关门被阻 |

> **ENG 观察（供参考，不构成主张）**：残余 5 件中 **2 件已证物理等价（`rel_geom_same=True` + 均匀平移）**、**3 件为 ≤0.5 µm 数值差**；`H1..H4` 为纯机械件、`diffs: []`。真实「电气级差异」的**数量级**已从 28 降至「≤0.5 µm × 3 件 + 表示差 × 2 件」。

---

## 3. 边界

未改 `criteria/**` · 板 · SPEC · 冻结件 · `_shared/**` · 生成器 · 库快照；未派 WORKER；未新增检查齿；未以「接近 0」宣称归零。
