# hw_ic_k2 — K2 Worker Data-Plane Card (PCIe Gen4 x8)

Open-source hardware — KiCad design files for the **K2 Worker Data-Plane Card**,
the worker-side converter card in the IOCONVERT V2.0 1-Master-to-4-Worker
chained NTB cluster. Tested 120 × 38 mm (JLC delivery baseline).

## Overview

K2 connects a Halo worker's M.2 slot to the cluster's PCIe Gen4 fabric.
Two MCIO connectors carry the Halo M.2 signals through DS160PR810 linear
ReDrivers and fold them into a single SlimSAS x8 uplink (≈16 GB/s) to the
master's PCIe switch.

```
Halo worker (2× M.2)
        │ MCIO 4i (J3/J4)
        ▼
   U3/U7 DS160PR810 ReDrivers ──► J2 SlimSAS x8 ──► Master PEX switch
        │
   STM32G0B1 MCU: SMBus OOB (J2 sideband) + PERST# sense/drive
```

## Key Features

- **Form factor**: 120 × 38 mm, 8-layer PCB
- **Data path**: PCIe Gen4 x8 (SlimSAS SFF-8654 uplink), 2× MCIO 4i (SFF-1016)
- **ReDriver**: 2× DS160PR810 linear ReDriver (signal conditioning, not retimer)
- **MCU**: STM32G0B1CBT6 — SMBus OOB (J2 sideband), PERST# sense/drive,
  Halo EC telemetry (J11 header → I2C2), FRU identity (E2 EEPROM)
- **Power**: ORing max(P3V3_AUX, 3V3_DCDC), independent rail
- **AC coupling**: 220 nF on all PCIe differential pairs (32×)

## Repository Contents

| Path | Description |
|---|---|
| `k2_v4.kicad_pro` / `.kicad_pcb` | KiCad 10 project + PCB (self-contained) |
| `sch/` | Schematics: connectors, AC-coupling & redriver strap (up/down), MCU & sideband, power |
| `lib/IOCONVERT.kicad_sym` | Symbol library (80 symbols) — required for schematics |
| `lib/ForgeOS.pretty/` | Footprint library (19 footprints) |
| `boards/` | Nets configuration (YAML) |

## Getting Started

1. Install [KiCad](https://www.kicad.org/) 10.x
2. Clone this repository
3. Open `k2_v4.kicad_pro`
4. If symbols/footprints show as missing, add `lib/IOCONVERT.kicad_sym`
   to the symbol library table and `lib/ForgeOS.pretty/` to the footprint
   library table (global or project-level)

## License

AGPL-3.0 (see `LICENSE`)

---

*Part of the IOCONVERT V2.0 family: [hw_ic_k1](https://github.com/dataxcash/hw_ic_k1) (master gate card) · [hw_ic_key](https://github.com/dataxcash/hw_ic_key) (secure key vault)*
