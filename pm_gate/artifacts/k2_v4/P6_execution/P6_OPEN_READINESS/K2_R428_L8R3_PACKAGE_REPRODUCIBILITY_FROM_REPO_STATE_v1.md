# K2 · R428 —— 在册交付包 `l8r3` **对现行 l8 之可复现性**（只读核证）

- **ts** 2026-09-23T00:17:15 · **from** ENG·ARCHER（续接 · 承 handoff R423 · 应监理巡检）· **to** 监理 · **owner 闸口 0**
- **authority**：owner ③ · **#K2-38**（交付锚冻结 · 交付闭环先例）· **R427**（包已锚 l8）· owner #14⑥ · #K2-142 §四
- **边界**：**只读**。**未重建包**（导出写 `/tmp`，包目录零写入）· 未改任何件 · 未出包 · 未烙板
- **首动作**：已读全部 `K2-RULING-*` ⇒ 最新仍 **#K2-144** · 无更晚裁定 · 无 owner 回件

## 0. 一句话
**在册包和「拿现行 l8 现导一遍」逐件一样**：Gerber **14/14**、钻孔侧 **15/15**（8 `.drl` + 6 map + report）**逐字节相同**（按包自带 date 规范化口径）。⇒ 包**未过期**、**忠实于仓内 l8**，而且**只靠仓内 board+pro 就能重生成**。

## 1. 方法（**照抄包内命令**，不吃包内自述）
| 项 | 内容 |
|---|---|
| Gerber | `kicad-cli pcb export gerbers --board-plot-params --no-x2 --layers F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts` |
| Drill | `kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format svg --generate-report` |
| 输入 | **仅仓内** `k2_v4_8L.l8.kicad_pcb`（`7a5c8991`）+ `l8.kicad_pro`（`c0090580`），复制入 `/tmp` 受控 work-dir |
| 规范化 | 按 `MANIFEST.canonicalization`（date → `2026-09-19T00:00:00+08:00`）后比 sha256 |
| 仪器 | `AppDir/bin/kicad-cli` 10.0.5（= 包内声明） |

## 2. 结果
| 组 | 一致 / 总数 |
|---|---|
| `01_gerber_rs274x/` | **14 / 14** |
| `02_drill_excellon/`（8 `.drl` + 6 map svg + report） | **15 / 15** |

## 3. 意义
1. **Q5 之关键物证**：在册包**不是**旧快照 —— 它**等于**当前 l8 的导出 ⇒ 若 owner 裁「甲」（受审板回 l8），**无需重出包**即可主张「包 = 当前受审板之产物」（正式复检仍须监理放行）。
2. **证据质量对照**：l8 交付包输入**全在仓内**且本会话**逐件复现**；而 l9 之搬迁铜有 **25/303 段来源为 `/tmp`**（R424 F8）⇒ 两条路线之**可复现/可追溯等级不同**。
3. **E-1（单链可重生成）** 在**现行仓态**下对本包依然成立。

## 4. 自检
- **未**把「重跑导出」写成「重建交付包」：导出写 `/tmp/opencode/r428/re_export/`，**包目录零写入**（承 #K2-38 §二）。
- **未**采信包内自述：本件自行重跑并逐件比 sha256。
- **未**改 `criteria/`（rev=6 MATCH）/SPEC/生成器/原理图。
- **未**把本件当交付见证：正式 DFM/交付判定仍属监理（gate 链态 **P4 HOLDS**）。

---
—— ENG（ARCHER）· 2026-09-23T00:17 · 只读 · owner 闸口 0 · sha16 `3e7823cb30440a0f`
