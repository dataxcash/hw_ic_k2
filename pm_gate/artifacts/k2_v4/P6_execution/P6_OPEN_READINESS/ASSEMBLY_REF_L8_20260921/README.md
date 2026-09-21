# K2 · **装配参考件（ASSEMBLY REF — 非交付级 BOM）** · l8 · 2026-09-21

> 授权：**#K2-64 §五**（有界另批授权：「ENG 可另批产**装配参考件**（由设计源导出：ref + value + footprint + CPL/旋转），
> **标注「装配参考 · 非交付级 BOM」**，**不并入交付锚、不改包**，以支撑外部装配」）。
> 源：受审板 `k2/hw/k2_v4_8L.l8.kicad_pcb` **`7a5c89913d6e5d0a`**（= 交付锚 l8r2/l8r3 之板）· 导出工具 `kicad-cli pcb export pos`。

## ⚠ 定位（**务必先读**）
- 本件 = **装配参考**，**不是**交付级 BOM，**不是**交付锚的一部分，**不得**被引作「交付件」或「可下单 BOM」。
- **交付面定义（owner #14③）= 裸板制造成套**（Gerber + 阻焊/丝印/边框/job + Excellon + 叠层图 + 阻抗表 + MANIFEST）；
  **交付级 BOM/CPL 不属该定义**（**#K2-64 §五**）。本件仅供**装配/实测方**按其自身工艺复核后使用。

## 文件
| 文件 | 内容 |
|---|---|
| `k2_assembly_ref_l8_pos_kicad.csv` | **kicad-cli 原样导出**（`Ref,Val,Package,PosX,PosY,Rot,Side`）· 54 件 · 全 `top`（`H*` 安装孔不入） |
| `k2_assembly_ref_l8_cpl_jlcstyle.csv` | **CPL 形**（`Designator,Mid X,Mid Y,Layer,Rotation`）—— 由上行**机械转换**（未改数值） |
| `k2_assembly_ref_l8_bom_refvalue_footprint.csv` | `Ref,Value,Footprint,Side`（**仅此 4 列**） |
| `MANIFEST_assembly_ref.json` | 本目录各件 sha256 + 源板锚 + 局限清单 |

## 已知局限（**不得隐去** · 使用前必须复核）
1. **无料号**：**无 `LCSC`/`MPN`/厂商料号列**（真源 `k2_sch.yaml` 中 `MPN`/`LCSC`/`part_number` 均 0 命中；`k2/fab/k2_v4_bom.csv` 为 ref 集）⇒ 采购/贴片参数须由使用方另行建立。
2. **无板厂旋转修正**：`Rotation` = **KiCad 角度**；**未做任何板厂库旋转修正**（不同板厂/库的 0° 基准不同）⇒ 首次上机**必须自校**。
3. **坐标原点**：= KiCad **drill/place origin**（本板 `PosY` 为负值属该原点口径）；**未做**板厂原点重定/镜像（全件 `top`，无底面对称问题）。
4. **不含 `H*` 安装孔**（KiCad 坐标文件不含）；**不含** 任何焊接/工艺参数（钢网、回流曲线等）。
5. 本件**不改变**任何交付锚/判据；**禁用**它替代交付包。
