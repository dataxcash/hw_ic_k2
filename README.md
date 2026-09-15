# K2 — PCIe Gen4 Converter Card (Card 2)

**English** | [简体中文](README.zh-CN.md)

KiCad hardware project (**8 layers**). Carries dual DS160PR810 ReDrivers (U3/U7); 85Ω differential impedance.

## Directory Guide

| Directory | Contents |
|---|---|
| `hw/` | **KiCad project (current 8L revision)** |
| `hw/sch/` | Schematics (`.kicad_sch`) |
| `hw/lib/` | Symbol + footprint libraries |
| `hw/data/` | Netlist / project configuration (yaml) |
| `archive/k2_v4_6L/` | Historical 6L revision (legacy) |
| `docs/` | Documentation |
| `pm_gate/` · `tools/` · `_shared/` | ENG toolchain (**not published**) |

## Opening the Project

1. Install **KiCad 10**
2. Open `hw/k2_v4_8L.kicad_pro`
3. Symbol library `hw/lib/DS320PR1601.kicad_sym`, footprint library `hw/lib/ForgeOS.pretty`

## Key Files

| File | Meaning |
|---|---|
| `hw/k2_v4_8L.kicad_pcb` | **Design source** (frozen input) |
| `hw/k2_v4_8L.l4.kicad_pcb` | **Fabrication release board** (ready to order) |

## Documentation

- [`docs/01-architecture.md`](docs/01-architecture.md) — What this card is
- [`docs/02-manufacturing.md`](docs/02-manufacturing.md) — Stackup / process / delivery

License: AGPL-3.0

---

*Part of the IOCONVERT V2.0 family: [hw_ic_k1](https://github.com/dataxcash/hw_ic_k1) (master gate card) · [hw_ic_key](https://github.com/dataxcash/hw_ic_key) (secure key vault)*
