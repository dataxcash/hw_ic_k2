# K2 — PCIe Gen4 转换卡（卡 2）

[English](README.md) | **简体中文**

KiCad 硬件工程（**8 层**）。板载双 DS160PR810 ReDriver（U3/U7），差分阻抗 85Ω。

## 目录导航

| 目录 | 内容 |
|---|---|
| `hw/` | **KiCad 工程（当前版 8L）** |
| `hw/sch/` | 原理图（`.kicad_sch`） |
| `hw/lib/` | 符号库 + 封装库 |
| `hw/data/` | 网表 / 工程配置（yaml） |
| `archive/k2_v4_6L/` | 历史 6L 版（旧） |
| `docs/` | 说明文档 |
| `pm_gate/` · `tools/` · `_shared/` | ENG 工具链（**不对外发布**） |

## 打开方式

1. 安装 **KiCad 10**
2. 打开 `hw/k2_v4_8L.kicad_pro`
3. 符号库 `hw/lib/DS320PR1601.kicad_sym`、封装库 `hw/lib/ForgeOS.pretty`

## 关键文件

| 文件 | 含义 |
|---|---|
| `hw/k2_v4_8L.kicad_pcb` | **设计源**（冻结输入） |
| `hw/k2_v4_8L.l4.kicad_pcb` | **施工交付板**（可打样） |

## 文档

- [`docs/01-architecture.zh-CN.md`](docs/01-architecture.zh-CN.md) — 这是什么卡
- [`docs/02-manufacturing.zh-CN.md`](docs/02-manufacturing.zh-CN.md) — 叠层 / 工艺 / 交付

License: AGPL-3.0

---

*IOCONVERT V2.0 家族成员：[hw_ic_k1](https://github.com/dataxcash/hw_ic_k1)（主控门禁卡）· [hw_ic_key](https://github.com/dataxcash/hw_ic_key)（安全钥）*
