# L3 施工图集索引（P3 立件 → **P4 基线 v10**：Z4 整族刷新）

> **本目录 = P3「施工图层重建」产出**（监理 **#K2-15 §二** 已开 P3）；**v10 = P4 基线整族刷新**（监理 **#K2-23 §二-1**：Z4 权威源 = 整族刷新至 P4 真值，驳回「以受审板为准」的拓扑用法）。**判据由监理核，ENG 只给测量**。
> **规范**：图纸内容由生成器**确定性重出**（下 §2）；**冻结件（交付板 `d4e81f64…` / 设计源板 `fb07d25a…` / 真源 yaml `dd794c54…`）不得由本目录工具改写**（生成器只读输入）。
> **权威链（不可倒置，#K2-23 §二-1 红线）**：真源 yaml → SPEC（canonical，只版本 bump）→ **受审板**（**仅**作「实测/板实」类字段的**量测源**；封装图形/属性级「以板为准」= W-8）。
> **v10 基线**：SPEC **rev-49** `b8f4a7cb67b575f0` · 受审板 **l5** `6ff49da5678c2108` · 真源 **errata-1** `17d540f058631a5e` · 生成器 `k2_p3_drawings_v1.py` `eb7ea771a1645c01`。
> **v10 变更（D1–D12 归零，C1 留待 ⑤）**：D3/D4 `H3=(45.10,75.10)`/边料 `2.30`（SPEC `mounting_holes` 输入层）· D5/D6 排针 `2,4,4,2,4` / `U1` `board_pads` `33→58`（板实）· **D7 具名上报**（`C3.U1` 按 R-1 带号口径 = `49`；`58` = 原始 pad 块口径，见 §3 `count_basis`）· D8/D9 铜区 `13/0→10/10` · D10 `C5b` `4/0`（原全 `allowed`）· D11 keepout 枚举 = SPEC 输入层 8 区 + `KO-7`（规则承载）且与板实逐项一致 · D12 自指 `rev-25→rev-49`；另**附带**刷新三件 as-built 坐标（`C85`/`C86`/`R42`）。
> **验收**：四方一致（真源 ↔ SPEC rev-49 ↔ 受审板 ↔ 本图集）**34/34 PASS** + Z4 §3 五项未漂；见 `k2/docs/K2-P4-Z4-DRAWINGS-V10-REFRESH-ACCEPTANCE-v1.md`。

## 1. 图册

| 文件 | sha256(16) **v10（现行）** | sha256(16) v9（历史） |
|---|---|---|
| `01_board_frame_and_holes.svg` | `ae84c110a4d27b0e` | `096a61c81201123d` |
| `02_device_coordinates.svg` | `caddcf3fbecebff3` | `48f92c6b9dd16042` |
| `03_corridor_occupancy.svg` | `e54c3b34782003db` | 同（未漂） |
| `04_layer_assignment.svg` | `124c7c3b6bc72e68` | 同（未漂） |
| `05_pour_strategy.svg` | `41453c89f007d59e` | `273910d6c820326e` |
| `06_keepouts.svg` | `fb6d9b6aaffe187f` | `6ee00985779e7d76` |
| `07_interface_pads_inframe.svg` | `0b10a71326cb3e99` | 同（未漂） |
| `p3_drawings.json` | `d6613754a7382c99` | `21e8891ea3fc4c06` |
| `p3_placement_solution.json` | `faddc9de5519c5ec` | 同（**只读，未改写**） |

> 勘误：本表旧版曾把 `01` / `p3_drawings.json` 记为 `67614e57…` / `a6841cd7…`（更早落件值），与 v9 实际落件 sha 不符；上表「v9 历史」列为**落件实测**值。
> v9 落件备份（T-22）：`/tmp/opencode/backup-drawings-20260918T130750/`（易失，可用 v9 版生成器 + 旧基线重出）。
| 图 | 内容 | 源 |
|---|---|---|
| 01 | 板框 `x[23,143] y[33,79]`（120×46）+ 4×M3 NPTH Ø3.2 与 Ø6.0 回避区 | L2-1/L2-2（审计 §十） |
| 02 | 55 真源件坐标（**受审板 as-built**；排针列与 lib 几何 @`column_x` 逐件交叉核对 `5/5`） | 受审板（实测源）+ SPEC + `p3_placement_solution.json`（仅留约束/来源） |
| 03 | 走廊占用（逐走廊 `x_range` / 逐带 `tracks_y`），口径 = 焊盘外接框净距 | canonical SPEC `corridors` + L2-4 |
| 04 | 层分配（8L：F/In1..In6/B；逐层角色 + `kind`/参考层 + `width_mm_by_layer` + 85Ω±10%） | canonical SPEC `impedance`/`stackup` + L2-5 |
| 05 | 敷铜策略：**10/10 有网铜区台账**（`idx/net/layer/bbox/filled`）+ 8 keepout 排除登记 + In4 分区 + GND 伴行 | 受审板 zones（只读）+ SPEC `pd`（口径 `#K2-21 §一`） |
| 06 | 回避区：**SPEC 输入层 8 keepout 区**（4 孔 + 4 `ESC_*`，逐区 5 开关）+ `KO-7`（规则承载）+ 板边铜框/去耦柱/`U6` pad 场；与板实逐项交叉核对 | SPEC `keepout_geometry.zones` / `constraints` + 受审板 |
| 07 | 接口焊盘出框检查（内缩 0.3mm；8 件） | 板几何 + 封装几何 @L2-3 |

## 2. 复现（确定性；沙箱默认 dry-run，写本目录须 T-41 双闸）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# 沙箱（解与图须同目录）：
mkdir -p /tmp/opencode/p3 && cp k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json /tmp/opencode/p3/
K2_P3_OUT=/tmp/opencode/p3 AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py
# 落盘（写仓库图集目录；T-41 双闸 + T-22 自动备份旧件并打印旧 sha）：
AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py --apply --confirm-repo-write
```
- 输入全只读：SPEC 经 `pm_gate.config` 解析（**禁硬编码 SPEC 文件名**）；真源经 `project.yaml::nets_yaml`；**受审板**默认 `k2/hw/k2_v4_8L.l5.kicad_pcb`（`--board` / `K2_P4_BOARD` 可覆写）。
- **fail-closed**：板 sha16 须 == SPEC 输入层自述 `board_sha16`（`mounting_holes` / `keepout_geometry`），否则拒绝出图（陈旧板 = 陈旧测量）。
- 落位解自 v10 起**只读不覆写坐标**（坐标权威 = 受审板 as-built）；解位与板实差异逐件登记于 `placement_solution.solution_vs_board_drift`。

## 3. 判据状态（#K2-16 复判回件；**v10 值见括号**）

- **P3-1 ✅ / P3-2 ✅ / P3-4 ✅（v10 最小余量仍 `0.08 @J9`）/ P3-5（图侧，v10 = SPEC 输入层 8 区 + `KO-7`）✅**；**C5b（板侧 ESC 4 区 5 开关全 allowed）⇒ P4 施工项**（#K2-17 §三）；**P3-3 复算（§3.1/§3.2 修后）**：53/55 字面相等，U1/U2 按 #K2-11 §1-2 **有向口径**逐条登记（引 `K2-P2-E2-directed-pad-registry-v1.md`）⇒ 待复判；**P3-6 复算 PASS**（R1 = `rev-23` 落件后，stale=[]、x_range = L2-4 口径、03 图 0 处 `< ! >`）。
- **C7（P4 前置）**：口径 = **有网非 keepout 铜区**（#K2-21 §一）。v9 记 9 铜区 0/9（l4 交付板）；**v10 = 受审板 `10/10` 全填充**（D8/D9）。
- **C5b（板侧 ESC 5 开关）**：v9 记 4 区**全 `allowed`**（空操作）；**v10 = 4 区 `copperpour=not_allowed`、其余 4 开关 `allowed` ⇒ `4/0`**（D10；P4 施工项 IN-11 已落）。
- **pad 计数口径（R-1 / #K2-18 §二-1）**：`C3.count_basis` 逐件登记 `numbered`（**判据比较口径**）与 `blocks_total`，v10 起并登记板侧 `board_pads_raw`/`board_pads_numbered` ⇒ `U1` 库/板皆 `58` 块 = `49` 带号 + `9` `F.Paste`（EP 钢网阵列，无电气性）⇒ 带号口径 `49`，库↔板逐值一致（D7 具名上报见验收件）。
- **D1**：排针列位移干涉 = 位移前 4 处 → 位移后 **0**。
- **errata/前置**：R2 yaml errata `k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`）· R3 `L2/L2-ERRATA-8L-v1.md`（`eb9354a6b8ffd535`，含 **In5/In6 角色待裁**）· P4 输入前置 `k2/docs/K2-P4-INPUT-PREREQUISITES-v1.md`（`59091b72304bfdd5`）。
- **courtyard/丝印级相邻 6 组**（非 P3 判据项）登记给 P4 布线前复核。

## 3b. 历史（本节原为「待监理裁/放行」；R1/R2/R3 已由 #K2-16 裁定并落地）

1. **SPEC `rev-23`**：走廊口径回写（去 `corridors[].note` 的 `17.30/27.40`，`x_range` 改 82.60/104.84）⇒ 解 **P3-6 未达**；
2. **strap 封装**：SPEC `R_0603` vs 真源 yaml `R_0402`（9 件中 6 件裸名）；
3. **L1/L2 文档 6L 文本 vs canonical 8L**（errata / 版本 bump）。

## 4. 判据与自检（详见 `k2/docs/K2-P3-DRAWING-SET-v1.md`）

- P3-1 板框 ✅ / P3-2 固定孔 ✅ / P3-3 pad==引脚（53/55 + 2 有向口径登记项）/ P3-4 接口出框 0（最小余量 0.08mm@`J9`）/ P3-5 回避区 4 区 ✅ / **P3-6 未达**（源数据未回写）。
- 附加：**C7（P4 前置）** 13 zone 全填充 = 现状 0/13；**D1** 排针列位移干涉 = 位移前 4 处 → 位移后 0。
- **courtyard/丝印级相邻 6 组**（非 P3 判据项）登记给 P4 布线前复核。
