# D-2 举证：DS320PR1601 是否「单颗双向」

- **指令来源**：#K2-07 §三（owner 裁定 D-2 =「要『单颗 · 双向』，以降复杂度」）
- **要求**：引器件手册证明；给明确结论；附原始出处（页码/表号/引用路径）；**禁猜**
- **本件性质**：只读取证 + 写文档。未改板、未改判据、未改生成器、未改 SPEC/原理图。
- **冻结件 sha**：`k2/hw/k2_v4_8L.l4.kicad_pcb` = `d4e81f647be7f9809aef72affb55fdf442a0cf743baead02d8e44fb130de18fc`（未变）

---

## 0. 结论（明确：**是**）

> **DS320PR1601 满足「单颗 · 双向」**：**一颗器件同时承载上行与下行**，无需每方向一颗。
> 本板实测亦已如此实现（见 §3）。**因此无需替代件候选**（裁定 §三-3 的分支条件"若不满足"未触发）。

**手册出处（全部可复核）**
- 器件：`DS320PR1601`（TI），数据手册 **SNLS683 – JUNE 2023**
- 手册原文 URL：`https://www.ti.com/lit/ds/symlink/ds320pr1601.pdf`
- **入库 PDF**：`k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/ref/ds320pr1601.pdf`
- **PDF sha256**：`f61599c4356edb395e07c9300999ab818898986a4adde71753bae7a080c039da`（与入库登记 `m13_v57_co148_u6_ds320pr1601_inputs.json` 一致，实测核对）
- 页数 43；引用页码按 `pdftotext -layout` 分页复算（`\f` 切分，第 N 段 = 第 N 页）

---

## 1. 证据 A —— 手册首页描述（**p1**，逐字）

```
1 Features                                                                3 Description
•     16-lane linear redriver supporting PCIe® 5.0, CXL                   The DS320PR1601 is a 32-channel (16-channel
      2.0, CCIX , and UPI 2.0                                             in each direction) or x16 (16-lane) low-power
•     Supports data rates up to 32-Gbps                                   performance linear repeater or redriver design
•     Intel retimer common footprint compatible                           to support PCIe 5.0, CXL 2.0, UPI 2.0 and othe
```

- **关键句（逐字）**：*"The DS320PR1601 is a **32-channel (16-channel in each direction)** or **x16 (16-lane)** low-power high-performance linear repeater or redriver"*
- **读法**：器件共 **32 通道**，**每个方向 16 通道**。单颗器件的通道数按"双向"计 —— 这正是"单颗双向"的手册级定义。

## 2. 证据 B —— 引脚功能表（**Table 5-1, p6–p14**，逐字 4 行）

```
 244:    M26           A_PETp0     Diff Output   Differential transmit signal, side A, channel 0, positive
 259: N2               A_PERp0         Diff Input      Differential receive signal, side A, channel 0, positive
 260: N34              B_PERn0         Diff Input      Differential receive signal, side B, channel 0, negative
 261: P10              B_PETp0         Diff Output     Differential transmit signal, side B, channel 0, positive
```

- **读法**：**side A** 与 **side B** **各自都有 receive（PER）与 transmit（PET）**。
  即：同一颗器件内，A 侧构成一条"PER 进 → PET 出"的完整单向通道组，B 侧构成另一条。
  **两颗"方向"在同一封装内并存** —— 这就是"单颗双向"的物理依据。

## 3. 证据 C —— **在本板实测**：4 个网组正好落在 A/B × PER/PET（最关键）

方法：把本板 `U6` 的 354 个焊盘（ball 坐标）经**符号映射**（`pin_name → pad_num`，取自 `hw/data/k2_sch.yaml` 的 `symbols[DS320PR1601].pins`）还原为功能脚名，再按网络分组。

| 板上网络组 | 球数 | 差分对 | 器件功能脚 | 语义 |
|---|---|---|---|---|
| `PCIE_DN*`（J2→） | 16 | 8 | **A_PER** | 侧 A 接收 |
| `PCIE_DN_OUT*`（→MCIO） | 16 | 8 | **A_PET** | 侧 A 发送 |
| `PCIE_UP*`（MCIO→） | 16 | 8 | **B_PER** | 侧 B 接收 |
| `PCIE_UP_OUT*`（→J2） | 16 | 8 | **B_PET** | 侧 B 发送 |
| **合计** | **64 球** | **32 对** | **16 通道** | 侧 A 8 通道 + 侧 B 8 通道 |

- **结论（板上事实）**：**同一颗 U6 同时跑上行与下行** —— 侧 A 承载 J2→MCIO 方向，侧 B 承载 MCIO→J2 方向。
- **通道预算**：器件每方向 16 通道；本板每侧用 **8 通道** ⇒ **每侧余量 50%**（这也解释了板上 108 个无乒乓球中 93 个是**未用通道**，见 §5）。

## 4. 证据 D —— 手册参考应用：单颗覆盖 x16 双向（**p31–p32**）

- **§9.2.1「PCIe x16 Lane Configuration」（p31）**：*"outlines detailed procedure and design requirement for a typical PCIe x16 lane configuration"*
- **Figure 9-2（p32）**：*"Simplified Schematic for PCIe x16 Lane Configuration in SMBus/I2C Controller Mode"*
- **读法**：TI 自己的参考应用就是用**单颗** DS320PR1601 覆盖 **x16 双向**链路；本卡为 **x8**（8 通道/方向），比参考应用更宽裕。

## 5. 顺带修正我自己的审计表述（诚实项）

审计报告 `M-03` 我写的是"U6 = 354 ball，其中 **108 ball 无网络**"——**数字成立，但表述不够准确**。按网表显式声明重新分类：

| 分类 | 数量 | 性质 |
|---|---|---|
| 网表**显式声明 NC**（`sheets.placements[U6].nc`） | **93** | **合法**（未用通道/保留球，手册标 N/C 或 RSVD） |
| 网表**声明要连但板上无网** | **15** | **缺陷**（真缺陷，非 NC） |
| 网表未提及、无法归类 | **0** | — |

那 **15 个缺陷球**为：8 个地址 strap（`A_ADDR0_7-0`/`A_ADDR1_7-0`/`B_ADDR0_7-0`/`B_ADDR1_7-0` 及其 15-8 组）+ `MODE` + `SDA` + `SCL` + 4 个电源/地球（`FJ6`/`FF8`/`FF33`/`FJ31`）。
⇒ **U6 的功能性缺陷是"15 个应连未连的球"**（strap 悬空 + I2C 未接 + 电源地未接），**不是"108 球全废"**。此修正已并入整改计划的验收项（V1/V2）。

## 6. 对 L1 的影响

- **D-2 结论为「是」⇒ L1 的「器件集合」与「球重映射」不需要变更**：维持**单颗 DS320PR1601（nfBGA-354）**。
- 因此 §⑨ 中此前挂 L1 的那一项**已由 owner 裁定 D-2 关闭**；**P2（真源归零）的器件集合前提具备**（另需 D-3 热机械口径，见计划 §⑧ L2-9 修订）。
- README / 陈旧原理图里"U7 上行 / U3 下行 = 双颗"的表述属于**陈旧件**，按 D-2 应再生为单颗（属 P2 的 Z2 动作，不在本轮）。

---

## 7. 独立复核（监理 #K2-07 §三「禁猜」要求的可复算性）

**复核人/时间**：ARCHER 续接会话，2026-09-16（只读；不引用上会结论，直接对 PDF 重算）

**命令**（可逐条复跑）
```bash
P=k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/ref/ds320pr1601.pdf
sha256sum "$P"                       # f61599c4356edb395e07c9300999ab818898986a4adde71753bae7a080c039da
pdftotext -layout "$P" /tmp/opencode/ds.txt   # 按 \f 分页：第 N 段 = 第 N 页
```

**页码命中实测**（对 `/tmp/opencode/ds.txt` 逐段检索）

| 检索串 | 命中页 | 对应结论 |
|---|---|---|
| `32-channel (16-channel` / `in each direction` | **p1** | 证据 A（单颗双向之定义） |
| `A_PETp0` | **p6** | 证据 B（侧 A 发送） |
| `A_PERp0` / `B_PERn0` / `B_PETp0` | **p7** | 证据 B（A 收、B 收、B 发） |
| `Table 5-1` | p6–p14 | 证据 B 所在表（跨 9 页） |
| `PCIe x16 Lane Configuration` | **p31, p32** | 证据 D（§9.2.1） |
| `Simplified Schematic for PCIe x16` | **p32** | 证据 D（Figure 9-2） |

**复核结论**：§1–§4 的引文与页码**逐条复现一致**；§0 结论「**是（单颗双向）**」**维持**，无需替代件候选（裁定 §三-3 之"若不满足"分支未触发）。

---

## 8. 出处归档（Sources of Record · 监理 #K2-08 §一-3 要求）

**owner 明示（2026-09-16）**：*器件本来就是单颗双向，这个是调整过的，README 没有更新。*
⇒ `U6 = DS320PR1601` **单颗、双向，设计正确，保持不变**；#K2-07 §三-3 的替代件举证**作废**。

**归档清单（全部 in-repo 且 `git ls-files` 命中，可逐件复算）**

| # | 件 | 路径（相对 `k2/`） | sha256 | bytes | tracked | 证明什么 |
|---|---|---|---|---|---|---|
| S1 | 器件手册 PDF（**SNLS683**） | `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/ref/ds320pr1601.pdf` | `f61599c4…c039da` | 2225981 | 是 | p1 定义 + Table 5-1（p6–14）+ §9.2.1／Fig 9-2（p31–32） |
| S2 | **vendor 球映射资产** | `…/mcio_feas_step2/ds320pr1601_ballmap.json` | `3f096af1…bdbd7` | 30724 | 是 | 单封装内 A/B × PER/PET **四带**（机判级，见下） |
| S3 | 354 球名表（球重映射用） | `…/mcio_feas_step2/v22_layer_gate/ds320pr1601_ballmap_354name.json` | `df9bfee4…ccd42` | 14180 | 是 | 球位 ↔ 脚名映射 |
| S4 | 入库登记（PDF sha 绑定） | `…/mcio_feas_step2/m13_v57_co148_u6_ds320pr1601_inputs.json` | `d98677fd…9299` | 1493 | 是 | 其 `pdf_sha256` 与 S1 实测**相符** |
| S5 | 手册节录（抓取命令 + 正文） | `…/mcio_feas_step2/m13_v57_co148_ds320pr1601_snls683_excerpt.txt` | `623b562c…489e` | 17450 | 是 | S1 的可搜索副本 |

**S2 内部机判证据（不依赖人工阅读）**：`validation.band_cols`

| 带 | 球数 | x 列区间（mm） | 语义 |
|---|---|---|---|
| `A_PER` | 32 | −3.94 ／ −3.42 | 侧 A **接收** |
| `A_PET` | 32 | +1.334 ／ +2.027 | 侧 A **发送** |
| `B_PER` | 32 | +3.42 ／ +3.94 | 侧 B **接收** |
| `B_PET` | 32 | −2.123 ／ −1.43 | 侧 B **发送** |
| **合计** | **128 == `signal_balls`** | 阵列 x∈[−3.94, +3.94]；body 8.89 × 22.86 | 四带同处**一颗**封装 |

**读法**：四带 x 区间**全部落在同一 body（8.89 × 22.86 mm）之内** ⇒ **一颗器件同时含 A 侧收发与 B 侧收发**。
⇒ 「单颗双向」有**两条互不依赖**的出处：S1（手册正文）与 S2（vendor 足迹库资产）。

**复算命令（可逐条复核）**
```bash
cd k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2
sha256sum ref/ds320pr1601.pdf ds320pr1601_ballmap.json
python3 -c "import json;v=json.load(open('ds320pr1601_ballmap.json'))['validation'];print(v['band_cols'], v['signal_balls'], v['n_balls'])"
pdftotext -layout ref/ds320pr1601.pdf /tmp/opencode/ds.txt   # 第 N 段 = 第 N 页
```

**陈旧件（**不**据此改设计）**
- `README*.md` 与 `hw/sch/*.kicad_sch` 中「U3/U7 双 DS160PR810」「U7 上行 / U3 下行 = 双颗」表述 = **陈旧件**，按真源**再生**（计划 §L2-10 / Z2），属 **P2 动作**。
- **不得**为"要一致"反过来改设计迁就陈旧件（owner 明示）。

**归档内的过时陈述（如实标注，不回改）**
- S4 `source.note` 写「PDF 未入库（体积）」——**已过时**：S1 现已在库且 tracked；S4 的 `pdf_sha256` 与 S1 实测一致，**绑定仍有效**。S4 属受 pin 的过程记录，**不回改**（避免破坏审计链）。
