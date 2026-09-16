# R1/R2 安装-回退清单（安装预演，**未安装**）v1

- **用途**：把批准的「R1/R2 落盘」中的 **安装步**做成可照抄、可回退的操作单；本件为 `/tmp` 预演证据。
- **性质**：**未安装**。预演在 `/tmp/opencode/inst/` 镜像内完成；仓内 `k2/hw/sch`、`k2/hw/lib` **一字未改**。
- **前置**：须先收 **U2（(ii) 批准）** + **S2（ReDriver 纸张）**；未批不动图（#K2-12 §三）。

## 1. 安装文件操作（精确）

| 动作 | 对象 | 说明 |
|---|---|---|
| **删** 6 件 | `k2/hw/sch/v5_connectors.kicad_sch`、`v5_ac-coupling_&_redriver_strap_downstream.kicad_sch`、`v5_ac-coupling_&_redriver_strap_upstream.kicad_sch`、`v5_mcu_&_sideband.kicad_sch`、`v5_power_decoupling_redriver_vcc.kicad_sch`、`v5_power_12v_dc-in_dcdc_5v_ldo_3v3.kicad_sch` | 6L/双颗时代的分区，真源已并为 5 页 |
| **写** 5 件 | `connectors.kicad_sch`、`redriver_ds320pr1601_sideband_strap.kicad_sch`、`mcu_sideband.kicad_sch`、`power_decoupling_redriver_vcc.kicad_sch`、`power_12v_dc_in_dcdc_5v_ldo_3v3.kicad_sch` | 文件名 = `slug(真源 sheet title)`（驱动器内显式规则 P7） |
| **覆写** 2 件 | `k2/hw/sch/k2_sch.kicad_sch`（root，5 sheet 块）、`k2/hw/lib/IOCONVERT.kicad_sym`（由 yaml `symbols` 再生） | root 元数据（title/paper/uuid）取自已存 root（只读） |

净结果：`hw/sch` **7 件 → 6 件**。

## 2. 回退（精确，安装后任意时刻可执行）

```bash
cd /home/fila/jqdDev_2025/ic_hw
git -C k2 checkout -- hw/sch hw/lib        # 恢复 6 件被删/被覆写的跟踪件
git -C k2 clean -f hw/sch                  # 删除 5 件新增未跟踪件（该目录当前无其它未跟踪件）
git -C k2 status --porcelain hw/sch hw/lib # 期望：空
```
> 注意：**不要**用 `git clean -fd k2` 或全仓 clean（会误删他处未跟踪件）。回退后应核对 `hw/sch`/`hw/lib` 与安装前 sha 一致。

## 3. `/tmp` 预演结果（本件证据）

| 检查 | 结果 |
|---|---|
| 镜像安装后 `hw/sch` 文件数 | 6（删 6、写 6，含 root） |
| root 的 `Sheetfile` 引用（5 条）是否都存在 | ✅ 5/5 存在（自洽） |
| `kicad-cli sch export netlist`（安装后集合） | ✅ rc=0，204,452 B |
| `kicad-cli sch erc`（安装后集合） | ✅ 与安装前**同 profile**：`endpoint_off_grid 452 / lib_symbol_issues 55 / footprint_link_issues 15 / power_pin_not_driven 1`（该 1 error 即 **S3**，与安装无关） |

## 4. **结构变更警示（须监理确认）**

- 安装**不只是内容改动**：sheet **分区与文件名重排**（7→6 件、全部改名为真源 title 派生名、sheet UUID 全变），这是「由真源再生」的**结构性**结果。
- 与批准清单（"删 60 + 并网 32 对 + 重映 + 补 12 + 新增网 10"）相比，**多出"sheet 分区/文件名重排"**这一项。ENG 判断其属 (ii) 路径的必然后果（真源 `sheets` 即 5 页），但**是否接受交付态原理图文件集变化，请监理一句话确认**（若要求保持 6 件旧文件名，则须另立"文件名映射"规则，ENG 不自行决定）。

## 5. 预演中发现的既有缺陷（**非本安装引入**，登记不阻塞）

- `k2/hw/k2_v4_8L.kicad_pro`：`schematic.top_level_sheets = [{filename: "k2_eco22.kicad_sch", …}]` ⇒ 指向**不存在的文件**；
- `k2/hw/k2_v4_8L.l4.kicad_pro`：`top_level_sheets = []`。
- 即：**工程 ↔ 原理图的顶层链接已是陈旧/空态**（与 R1/R2 无关，装/不装都一样）。故本次安装**无需**改 `.kicad_pro`；该项宜另案登记。

## 6. 复现（只写 `/tmp`）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 镜像现状 → ② 施加 §1 的文件操作 → ③ 跑 kicad-cli netlist/erc
# 预演脚本与产物：/tmp/opencode/inst/{sch,lib,board.net,erc.rpt}
```

- 预演产物：`/tmp/opencode/inst/board.net`、`/tmp/opencode/inst/erc.rpt`；生成件源 `/tmp/opencode/full_a/`（driver `k2_sch_gen_v1.draft.py` `9aa52762444851b8`）。
- 冻结件：交付板 `d4e81f647be7f980`、设计源板 `fb07d25ac426ff84` 未变。
