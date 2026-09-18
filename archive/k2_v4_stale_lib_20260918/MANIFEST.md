# K2 · ForgeOS.pretty **stale 件退役清单**（MANIFEST）

> 授权：监理 **#K2-28 §三-1**（授权**退役＝移动，非删除**，ENG 具名的 12 件 → `k2/archive/k2_v4_stale_lib_20260918/`）。
> 退役判定依据：`k2/tools/k2_p4_lib_snapshot_v1.py`（`afa9be4bf599626b`，`--lib-only`）以**受审板 `dae8dc8d48ff5b81` 为权威**重建库快照后的 `stale_mods`；
> 即「快照外旧件」——**不被任何活跃 ref/map 引用**（`k2/hw/lib/ForgeOS.refmap.json` 引用 mod = 23 件）。
> **保留件**：`MountingHole_3.2mm_M3.kicad_mod`（其名被生成器 `NPTH_FP_NAME` 用作 4 枚 NPTH 的 footprint 名 ⇒ **不属退役集**，见 #K2-28 §三-2）。

| # | 文件 | sha16 | 退役理由 |
|---|---|---|---|
| 1 | `MCIO_4i_SFF-1016_RASide.kicad_mod` | `44e4b57c83c8a5e0` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 2 | `MCU_STM32G0_QFN32.kicad_mod` | `a3759eabf62a9786` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 3 | `OCuLink_SFF8612.kicad_mod` | `6ae37f5d0e1c4f67` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 4 | `PI3DBS16412.kicad_mod` | `4137b715a3e9eab2` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 5 | `TLV61046_SOT235.kicad_mod` | `abe9cf1138f1f03a` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 6 | `TLV61046_SOT23_6.kicad_mod` | `5f55d32f01bea9ae` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 7 | `TPD6E05U06_RVZ.kicad_mod` | `3bbc22ab7aff3295` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 8 | `TPS22919.kicad_mod` | `b19489b180addc8d` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 9 | `TS3USB221A_UQFN10.kicad_mod` | `8f823dc2445522d9` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 10 | `USB3_TYPEA_90.kicad_mod` | `d120c7e8ea506466` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 11 | `USB_A_MUSBR.kicad_mod` | `5a92041b795bc355` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |
| 12 | `WQFN-64_10x5.5mm_P0.4mm.kicad_mod` | `23d768db93543692` | 快照外旧件（不被 refmap/生成器引用；以板为准的快照件已取代） |

## 库目录 digest（前/后）

| 时点 | 文件数 | digest |
|---|---|---|
| 退役前 | 36 | `078f7dc78d980696` |
| **退役后** | **24** | **`efcd88b35d6d846c`** |
| 归档目录 `k2/archive/k2_v4_stale_lib_20260918/` | 12 | `57449737c18a9794` |

**未动**：被 `refmap` 引用的 23 件 mod + `MountingHole_3.2mm_M3`（活跃 24 件）。
**可追溯**：本退役为移动（`k2/archive/**` 内逐字节保留，sha 见上表），非删除。

—— ENG（ARCHER）· 2026-09-18 · #K2-28 §三 · 工具 `afa9be4bf599626b`
