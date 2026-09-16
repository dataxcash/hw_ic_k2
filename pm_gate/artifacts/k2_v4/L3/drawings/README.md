# L3 施工图集索引（P3）· v1

> **本目录 = P3「施工图层重建」产出**（监理 **#K2-15 §二** 已开 P3）。生成/判据入口见下；**判据由监理核，ENG 只给测量**。
> **规范**：本目录为**只增不改**的图集留档；图纸内容由生成器确定性重出（下 §复现）；**冻结件（交付板 `d4e81f64…` / 设计源板 `fb07d25a…` / 真源 yaml）不得由本目录工具改写**。

## 1. 图册

| 文件 | sha256(16) |
|---|---|
| `01_board_frame_and_holes.svg` | `67614e57dc292825` |
| `02_device_coordinates.svg` | `48f92c6b9dd16042` |
| `03_corridor_occupancy.svg` | `e54c3b34782003db` |
| `04_layer_assignment.svg` | `124c7c3b6bc72e68` |
| `05_pour_strategy.svg` | `273910d6c820326e` |
| `06_keepouts.svg` | `6ee00985779e7d76` |
| `07_interface_pads_inframe.svg` | `0b10a71326cb3e99` |
| `p3_drawings.json` | `45b4a9ee4fdc4c4b` |
| `p3_placement_solution.json` | `faddc9de5519c5ec` |

| 图 | 内容 | 源 |
|---|---|---|
| 01 | 板框 `x[23,143] y[33,79]`（120×46）+ 4×M3 NPTH Ø3.2 与 Ø6.0 回避区 | L2-1/L2-2（审计 §十） |
| 02 | 55 真源件坐标（40 锚点/SPEC+L2-3 修正 + 15 L2 落位解） | 锚点板 + SPEC + `p3_placement_solution.json` |
| 03 | 走廊占用（逐走廊 `x_range` / 逐带 `tracks_y`），口径 = 焊盘外接框净距 | canonical SPEC `corridors` + L2-4 |
| 04 | 层分配（8L：F/In1..In6/B；逐层角色 + `kind`/参考层 + `width_mm_by_layer` + 85Ω±10%） | canonical SPEC `impedance`/`stackup` + L2-5 |
| 05 | 敷铜策略：**13 zone 台账**（`idx/net/layer/bbox/filled`）+ In4 分区 + GND 伴行 | 交付板 zones（只读）+ SPEC `pd` |
| 06 | 回避区机定几何（板边铜框 / 去耦柱 keepout / `U6` pad 场 + 逃逸区数值）+ 逐区 5 开关 | SPEC `constraints` + `strap_domain_v32` |
| 07 | 接口焊盘出框检查（内缩 0.3mm；8 件） | 板几何 + 封装几何 @L2-3 |

## 2. 复现（确定性；输出到本目录或沙箱）

```bash
cd /home/fila/jqdDev_2025/ic_hw
AppDir/usr/bin/python3.11 k2/tools/k2_p3_place_solver_v1.py   # 落位解 + 五项自检（框/净距/间距/孔/柱）
AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py      # 出图 + 判据测量（消费落位解）
# 沙箱（解与图须同目录）：
K2_P3_SOL_OUT=/tmp/opencode/p3 K2_P3_OUT=/tmp/opencode/p3 AppDir/usr/bin/python3.11 k2/tools/k2_p3_place_solver_v1.py
K2_P3_OUT=/tmp/opencode/p3 AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py
```
生成器只读输入；SPEC 经 `pm_gate.config` 解析（**禁硬编码 SPEC 文件名**）。

## 3. 判据状态（#K2-16 复判回件）

- **P3-1 ✅ / P3-2 ✅ / P3-4 ✅ / P3-5 ✅**；**P3-3 复算（§3.1/§3.2 修后）**：53/55 字面相等，U1/U2 按 #K2-11 §1-2 **有向口径**逐条登记（引 `K2-P2-E2-directed-pad-registry-v1.md`）⇒ 待复判；**P3-6 复算 PASS**（R1 = `rev-23` 落件后，stale=[]、x_range = L2-4 口径、03 图 0 处 `< ! >`）。
- **C7（P4 前置）**：**9 铜区** 全填充 = 现状 **0/9**（4 个无网 `ESC_*` keepout 排除；口径按 #K2-16 §四 监理自纠修正）。
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
