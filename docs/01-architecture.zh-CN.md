# K2 架构

[English](01-architecture.md) | **简体中文**

## 这是什么

**K2 = PCIe Gen4 转换卡（卡 2）**，8 层板。

- 板载**双 DS160PR810 ReDriver**（U3 / U7），用于 PCIe Gen4 信号中继/均衡。
- 一路 **x8** 主机链路（SlimSAS，SFF-8654）扇出为 **2× x4** MCIO 4i（SFF-1016）下行。
- 差分阻抗目标 **85Ω ±10%**。
- 与 K1（门禁卡）同属 IOCONVERT 转换卡家族；K2 为数据面卡。

## 目录与文件

```
hw/                          KiCad 工程（当前版 8L）
  k2_v4_8L.kicad_pro             工程文件
  k2_v4_8L.kicad_pcb             设计源（冻结输入）
  k2_v4_8L.l4.kicad_pcb          施工交付板
  k2_v4_8L.l4.kicad_dru          设计规则（板级）
  sch/                           原理图（根页 + 电源/连接器/MCU/AC 耦合 等）
  lib/                           符号库 + 封装库
  data/                          网表 / 工程配置（yaml）
archive/k2_v4_6L/            历史 6L 版（被 8L 取代）
docs/                        本目录
```

## 版本沿革

| 版本 | 状态 | 说明 |
|---|---|---|
| 6L（`k2_v4.*`） | **历史** | 早期 6 层版，已归档 `archive/k2_v4_6L/` |
| **8L（`k2_v4_8L.*`）** | **当前** | 8 层版；设计源 + 施工交付板 |

> `.l4` 后缀 = L4 施工阶段输出（由设计源派生），非独立设计。
