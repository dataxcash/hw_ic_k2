# K2 Manufacturing Notes

**English** | [简体中文](02-manufacturing.zh-CN.md)

## Stackup (8 Layers)

| Layer | Contents |
|---|---|
| `F.Cu` | High-speed differential + escape routing + surrounding low-speed |
| `In1`–`In6` | Inner layers (signal / plane) |
| `B.Cu` | Low-speed / sideband |

## Process

| Item | Value |
|---|---|
| Differential impedance | **85Ω ±10%** (impedance control + test coupon required) |
| Minimum trace width / spacing | 0.09mm / 0.10mm |
| Board-edge copper / annular ring | 0.30mm / 0.075mm |
| Vias | Standard 0.20mm drill / 0.35mm outer diameter |
| Fab house / channel | JLC — **HDI blind/buried via channel (≥2 stage)** |

## Delivery

- **Release board**: `hw/k2_v4_8L.l4.kicad_pcb`
- **Deliverables**: Gerber package = 8 copper layers + solder mask / silkscreen / outline / job + Excellon drill (incl. HDI blind/buried vias) + stackup drawing + impedance table + MANIFEST (per-file sha256)

## Known Dispositions (Disclosed With the Order)

| Item | Disposition |
|---|---|
| Solder mask sliver `R3.pad2 ↔ PCIE_UP3_N` = 0.0695mm < 0.09mm | Accepted at L2 (`ACCEPT_L2_WITH_FAB_REVIEW`, submitted with the order, fab review) |
| Impedance compliance | This project does not self-certify; final judgment by the fab house's impedance control service |
