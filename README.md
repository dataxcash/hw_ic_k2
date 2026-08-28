# hw_ic_k2 — 开源硬件工程（KiCad）

原理图 + PCB 设计文件（KiCad 10 格式）。

## 打开方式
1. 安装 KiCad 10
2. 打开 `*.kicad_pro` 工程文件
3. 符号库 `lib/IOCONVERT.kicad_sym` / 封装库 `lib/ForgeOS.pretty` 需在
   KiCad 符号/封装库表（sym-lib-table / fp-lib-table）中注册（或按工程内表配置）

## 内容
- `sch/` — 原理图（.kicad_sch）
- `*.kicad_pcb` — PCB
- `boards/` — 工程配置（yaml）
- `lib/` — 符号库 + 封装库（必需）
- `fab/` — BOM（CSV）

License: AGPL-3.0
