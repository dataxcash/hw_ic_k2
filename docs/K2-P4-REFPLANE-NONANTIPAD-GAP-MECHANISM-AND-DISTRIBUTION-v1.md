# K2 · P4 · `ref_plane_continuity` **新口径机判 + 缺口成因分离 + `max_contiguous_gap_mm` 分布** · v1 · 2026-09-19

> 授权：**#K2-31 §四**（owner 授权监理定：口径精化 `non_antipad_gap == 0` + 载体整改，不升 owner）· **§四-5**「ENG 须交付」①成因分离 ②新口径机判 + 正/负控 ③`max_contiguous_gap_mm` 实测分布 ④整改前/后读数。
> 本件交付 **①（机制）/②/③/④-前**；**④-后** 待 L2 载体整改（`#K2-31 §四-4`：反焊盘阵列/补缝合孔，改受审载体 ⇒ 与落件同批）。
> 装置：新仪器 `k2/docs/drafts/p4-refplane-nonantipad-v1/measure_non_antipad_gap.py` **`2f5591352c5974d3`**（只读；不依赖 KiCad fractured/Unfracture 表示）。
> ENG（ARCHER）· 2026-09-19 · 受审板 `l6 30fa849641323f98`（判据锚 rev=2）

## 1. 口径与判别子（具名）

| 项 | 定义 |
|---|---|
| 平面层 | 内层**已填充** zone 的填充多边形并集（同在库 V3 仪器） |
| 高速段 | 网名前缀 `PCIE_`（现行口径，同 V3） |
| 主参考层 | 每段取上/下相邻平面层中**覆盖率最高**者 |
| 缺口 | 段矩形 − 主参考层填充并集 |
| **antipad** | 缺口 ∩ **铜形闭运算包络** `closing(P, R)` ⇒ 被铜包住、可被 `closing(2R)` 填平的腔 |
| **split_or_cutout** | 缺口 − `closing(P, R)` ⇒ 平面分割 / 整片开孔 / 铜形退缩 |
| `hole_keepout` | 缺口 ∩ NPTH 孔 keepout 方框（另计；**不属反焊盘**） |
| `board_outside` | 缺口 − 平面声明域（另计） |
| `max_contiguous_gap_mm` | 段中心轴（0.01mm 细带）与缺口求交后，**各连续段在轴上投影长度之最大者** |

**主判** = `non_antipad_gap == 0`（`non_antipad_gap` := `split_or_cutout`）；面积覆盖率降为**信息项**。

**已知局限（具名）**：闭运算同时填平**外轮廓凹口** ⇒ 紧贴外轮廓凹口的缺口并入 `antipad`。

## 2. ⚠ **结论对判别半径 `R` 敏感**（本件核心发现，须监理钉死）

| `R` (mm) | 可被填平的腔尺寸 | 受审板 `non_antipad_gap` (mm²) | 主判 |
|---|---|---|---|
| 0.25 | ≤0.5mm | **20.8905** | FAIL |
| **0.5（本件默认）** | ≤1.0mm | **0.0000** | **PASS** |
| 1.0 | ≤2.0mm | **0.0000** | **PASS** |

⇒ 本板缺口腔尺度**集中在 0.5–1.0mm**（⇒ R=0.25 时全部判 split/cutout；R≥0.5 时全部判 antipad）。
**ENG 不预设 R**（C-12：不得以「接近 0」宣称归零）；两条出路供监理裁：
 1. **钉死 `R`**（如 0.5mm = 覆盖本板 pad/via 反焊盘尺度）；或
 2. **改采「成因派生」定义**（更贴字面）：反焊盘 = **每个 pad/via 按 zone clearance 外扩所得区域的并集**（`antipad = 缺口 ∩ 该并集`；`non_antipad_gap = 缺口 − 该并集`）—— 本件未实现，ENG 可在获授权后实现（**非新增检查齿**，是既有维的测量实现）。

## 3. 实测（受审板 = 链产物 `l6`；负控 = 冻结板 `l4`）

| 量 | **POS 受审板 `l6 30fa849641323f98`** | **NEG 冻结 `l4 d4e81f647be7f980`（zone 全未填充）** |
|---|---|---|
| 段数 / 严格全长覆盖 | 3795 / **3176（83.689%）** | 2327 / **0（0%）** |
| `A_total` / `A_covered` / `A_gap` (mm²) | 799.97 / 779.0148 / 20.9552（守恒差 0.0） | 798.1724 / 0.0 / 798.1724（守恒差 0.0） |
| `antipad` / `split_or_cutout` / `keepout` / `outside` (mm²) | 20.9552 / **0.0** / 0.0062 / 0.0 | 0.0 / **798.1724** / 0.0342 / 0.352 |
| **`non_antipad_gap` (mm²)** | **0.0**（含 keepout/板外 0.006168） | **798.172376**（含 798.558611） |
| 主判 | **PASS**（`0.0`；若 keepout 亦计入 ⇒ `0.006168` mm² ≠ 0） | **FAIL** |

**正/负控**：
- **正控（in-run）** = 严格全长覆盖段集合 n=**3176** ⇒ `non_antipad_gap = 0` **且** `max_contiguous_gap = 0`（命中）✅
- **负控** = 冻结 `l4`（zone 全未填充）⇒ `non_antipad_gap = 798.172376` mm²（≈ 段形总面积）、`max_contiguous_gap` **max = 57.13 mm**、严格覆盖 0% ⇒ 判 FAIL（命中）✅

## 4. `max_contiguous_gap_mm` 实测分布（③；受审板 `l6`）

| 群体 | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| **仅有缺口段**（n=619） | 0.0938 | 0.3755 | 0.3755 | — | **0.611** |
| 全 3795 段（含全覆盖段 = 0） | 0.0 | 0.0599 | 0.2687 | 0.3755 | 0.611 |

**逐网 top-5（按 `non_antipad_mm2` 现行默认 R=0.5，全为 0；列 `max_contiguous_gap_mm`）**：
- `PCIE_DN_OUT4_P_MCIO`：`non_antipad`=0.0 mm² · `max_contiguous_gap`=**0.3755 mm**（n_gap=10）
- `PCIE_DN_OUT4_N_MCIO`：`non_antipad`=0.0 mm² · `max_contiguous_gap`=**0.3755 mm**（n_gap=12）
- `PCIE_DN_OUT5_P_MCIO`：`non_antipad`=0.0 mm² · `max_contiguous_gap`=**0.3755 mm**（n_gap=10）
- `PCIE_DN_OUT5_N_MCIO`：`non_antipad`=0.0 mm² · `max_contiguous_gap`=**0.3755 mm**（n_gap=12）
- `PCIE_REFCLK1_N`：`non_antipad`=0.0 mm² · `max_contiguous_gap`=**0.3755 mm**（n_gap=3）

> **阈值归监理**（#K2-31 §四-5-③：不预设）：本件只出分布。**注**：`max_contiguous_gap` 的 max 段（0.611mm）在现行 R=0.5 下仍属 `antipad` 类 ⇒ 若采「域口径/缝合孔」以外的路，须与 R 一并定。

## 5. 交付状态

| # | 项 | 状态 |
|---|---|---|
| ① | 缺口成因分离（拆 `antipad` / `split_or_cutout`） | **机制已成 + 实测出数**；⚠ 结论对 `R` 敏感（§2）⇒ 判别半径/定义须监理钉死 |
| ② | 新口径机判（`non_antipad_gap == 0`）+ 正/负控 | **成**：正控 3176 段 0/0；负控 `l4` 798.17mm² / max 57.13mm ⇒ FAIL |
| ③ | `max_contiguous_gap_mm` 实测分布 | **成**（§4） |
| ④ | 整改前/后读数 | **前 = 本件**；**后** 待 `#K2-31 §四-4` L2 载体整改（改受审载体 ⇒ 与落件同批） |

**红线遵守**：本件只读，未改板/SPEC/判据/`_shared`/生成器；**未**放松任何下限；**未**以「接近 0」宣称归零（R=0.25 下为 20.9442mm²，如实并列）；临时仅 `/tmp/opencode`；未派 WORKER。
