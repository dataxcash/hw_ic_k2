# hw/sch canonical 指引 + 旧→新映射表（#K2-13 §二.2/§二.3）

> 本文件新增于 2026-09-16（R1/R2 落盘）。**旧 `v5_*` 原件按宪法留档，未删**。

## 1. canonical 集合（现行）

| 角色 | 文件 | sha256(16) |
|---|---|---|
| **root（canonical）** | `k2_sch.kicad_sch` | `a7cbb7a7aa54d4c3` |
| sheet | `connectors.kicad_sch` | `27da220bf5d05c2a` |
| sheet | `redriver_ds320pr1601_sideband_strap.kicad_sch` | `1825b3f0ad655c9d` |
| sheet | `mcu_sideband.kicad_sch` | `cdf94bc84d068838` |
| sheet | `power_decoupling_redriver_vcc.kicad_sch` | `a3eadcd0f4d30329` |
| sheet | `power_12v_dc_in_dcdc_5v_ldo_3v3.kicad_sch` | `cb3c2134de77cfd6` |
| 符号库 | `../lib/IOCONVERT.kicad_sym` | `84ffb7de31fbcd82` |

生成：`k2/tools/k2_sch_gen_v1.py`（R1 路径 (ii)，由真源 `hw/data/k2_sch.yaml` 再生；规则 P1–P10 见其头注）。

## 2. 旧 → 新 sheet/文件名映射（#K2-13 §二.2 要求，禁静默）

| 旧（6L/双颗，已移入 `archive/` 留档，**未删**） | 新（canonical） |
|---|---|
| `k2_sch.kicad_sch` | `k2_sch.kicad_sch（root 覆写；5 sheet 块，page 2–6）` |
| `archive/v5_connectors.kicad_sch` | `connectors.kicad_sch` |
| `archive/v5_ac-coupling_&_redriver_strap_downstream.kicad_sch` | `redriver_ds320pr1601_sideband_strap.kicad_sch（下行+上行合并为真源单页）` |
| `archive/v5_ac-coupling_&_redriver_strap_upstream.kicad_sch` | `redriver_ds320pr1601_sideband_strap.kicad_sch（同上，合并）` |
| `archive/v5_mcu_&_sideband.kicad_sch` | `mcu_sideband.kicad_sch` |
| `archive/v5_power_decoupling_redriver_vcc.kicad_sch` | `power_decoupling_redriver_vcc.kicad_sch` |
| `archive/v5_power_12v_dc-in_dcdc_5v_ldo_3v3.kicad_sch` | `power_12v_dc_in_dcdc_5v_ldo_3v3.kicad_sch` |

- **读取规则**：只读上表 §1 的 canonical 集合；`archive/v5_*` 为**版本链留档**（6L/双颗时代），禁作现行读取。
- **为何入 `archive/` 子目录**：判据侧 `criteria/adjudicate.py: measure_sch_refdes()` **glob 顶层 `*.kicad_sch`**，且仓内 `_EXCL` 已把 `/archive/` 视为归档 ⇒ 留档件必须置于 `archive/`，否则 E1 会把 6L 旧件 refdes 计入（污染判据）。`git mv` 保留历史，原件字节未改。
- root 的 5 条 `Sheetfile` 引用即 §1 的 5 件 sheet（--engine 侧自洽已机检）。
