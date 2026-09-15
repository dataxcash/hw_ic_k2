# K2 Architecture

**English** | [简体中文](01-architecture.zh-CN.md)

## What This Is

**K2 = PCIe Gen4 converter card (Card 2)**, an 8-layer board.

- Carries **dual DS160PR810 ReDrivers** (U3 / U7) for PCIe Gen4 signal redriving/equalization.
- Takes one **x8** host link (SlimSAS, SFF-8654) and fans it out to **2× x4** MCIO 4i (SFF-1016) downlinks.
- Differential impedance target **85Ω ±10%**.
- Belongs to the IOCONVERT converter-card family alongside K1 (the gate card); K2 is the data-plane card.

## Directories and Files

```
hw/                          KiCad project (current 8L revision)
  k2_v4_8L.kicad_pro             Project file
  k2_v4_8L.kicad_pcb             Design source (frozen input)
  k2_v4_8L.l4.kicad_pcb          Fabrication release board
  k2_v4_8L.l4.kicad_dru          Design rules (board level)
  sch/                           Schematics (root page + power / connectors / MCU / AC coupling, etc.)
  lib/                           Symbol + footprint libraries
  data/                          Netlist / project configuration (yaml)
archive/k2_v4_6L/            Historical 6L revision (superseded by 8L)
docs/                        This directory
```

## Revision History

| Revision | Status | Notes |
|---|---|---|
| 6L (`k2_v4.*`) | **Historical** | Early 6-layer revision, archived under `archive/k2_v4_6L/` |
| **8L (`k2_v4_8L.*`)** | **Current** | 8-layer revision; design source + fabrication release board |

> The `.l4` suffix = L4 fabrication-stage output (derived from the design source), not an independent design.
