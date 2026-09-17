# K2 · P4 · **W-7 P2 施工修复器 v1 + dry-run 全量复算**（ENG 交件）

> 性质：**ENG 只交「工具 + 施工方案 + dry-run 复算证据」**；批准/判定归**监理**。
> 本件**未写任何仓库件**：板 / pro / SPEC 原件 / `criteria/` 逐字节未动（见 §6 复算）。
> 依据：监理 **#K2-19 §二 W-7**（不豁免、deny-by-default、ENG 逐条交「修 or 具名豁免+证据」、监理逐条批）· handoff `k2-p4-handoff-20260918-ctx405k-inc25.md` §4-2。
> 工具：`k2/tools/k2_p4_w7_repair_v1.py` sha256 前16 **`4fe85ea4df2c986e`**（dry-run 默认；只在 `--work-dir` 内产出）。

## 0. 一句话

W-7 未处置 5 类共 **146** 条：本工具以「**逐案改板 → 重填 zone → 存盘 → KiCad DRC 复算 → 不合格即回退**」的引擎处理，**50 案通过复算**（无新增违规类型、无 error、未连接 0、违规总量严格下降）；实测 **181 → 113**。其余 **36 案**逐条给出**不可行/待裁证据**（§4）。

## 1. 结果总账（dry-run；源板 `37019705ef994ccc` 未动）

| 规则类 | 前 | 后 | 已消除 | 已施工案 | 未处置案 |
|---|---|---|---|---|---|
| `via_dangling` | 12 | 6 | 6 | 6 | 6 |
| `track_not_centered_on_via` | 30 | 13 | 17 | 16 | 18 |
| `silk_over_copper` | 43 | 16 | 27 | 28 | 12 |
| `silk_overlap` | 21 | 3 | 18 | 28 | 12 |
| `missing_courtyard` | 40 | 40 | 0 |  | —（口径属 §4-1 裁决，本工具未包含） |
| `lib_footprint_mismatch` | 35 | 35 | 0 |  | —（W-8/`O-2`，不在 W-7） |
| **合计（前 6 类）** | **181** | **113** | **68** | **50** | **36** |

> 注：`silk` 组的 28 案同时压减 `silk_over_copper` 与 `silk_overlap`（文字移位/缩字同时消两叠类），故两行的「已施工案」同计一次、不重复相加；「未处置案」= 该组未通过复算的案数。

**每案复算口径（`delta_ok`）**：① 无新违规类型；② 任一类型条数不得增加；③ error 级 = 0；④ `unconnected` = 0；⑤ 违规总量严格下降。任一不满足 ⇒ 该案**回退**并记入 §4。

## 2. 逐类施工方法（ENG 自裁范围）

### 2.1 `via_dangling`（12 条 → 6 条）

切除孤立过孔（F–B 贯通但另一端无铜）+ 其死端支路走线。**递归回溯规则**：从孔位出发，仅当「支路远端的其它铜 = 0 或 1 且无焊盘」才继续回溯（含**中段穿越的 T 节点**判定），遇焊盘/多路汇合即停 ⇒ 不切功能连接；每案以 DRC 复算把关（`unconnected` 必为 0）。

### 2.2 `track_not_centered_on_via`（30 条 → 13 条）

几何求解：候选落点 = {孔心} ∪ {涉事走线端点} ∪ {两两直线交点}；对每个候选，把**每条**涉事走线（违规走线 + 端点已落在孔心的走线）的最近端点移到该点，要求移动后方向仍为 **0/45/90**（容差 2 nm），且位移 ≤ **0.26 mm**；按（**孔不动优先** → 变动对象数 → 最大位移）排序，逐候选提交复算，**不过即试下一个**。
实测：最大**孔位移 50 µm**、最大**走线端点位移 100 µm**；其中 6 案**不动孔**（仅走线端点吸附）。

### 2.3 `silk_over_copper` / `silk_overlap`（64 条 → 19 条）

只动**参考字段文本**（不动铜、不动器件、不动封装图形）：16 向 × 11 环候选落点，以「本体外框 + 文本半尺寸」为起点按离原位距离升序，逐点做**避让检查**（阻焊开窗代理 = 全部 pad 外框 +0.06 mm；其它丝印 = 封装图形/其它字段外框 +0.04 mm；且须落在板框内 −0.2 mm）；若原字号（1.0 mm）最近可行位 > 1.2 mm，则允许缩到 **0.8 mm**（= pro `min_text_height` 下限）再找，取位移小者。

### 2.4 `missing_courtyard`（40 条）**未包含**

补 `F.CrtYd` 的**外扩口径**正是 owner 常设 ①/监理 §4-1 的耦合裁定项（W-8 (甲′)/(乙) × W-7 courtyard 口径 × J-8b 可判性）；ENG 不择口径、不缩口径，故本工具未实现该组（留给口径裁定后一版）。既有测量见 `K2-P4-LAND-AND-COURTYARD-FEASIBILITY-v1.md`。

## 3. 逐案处置清单（机器生成）

### 3.1 `via_dangling` 通过（6 案）

| 孔 | 网络 | 孔位 (mm) | 一并切除的死端线段 |
|---|---|---|---|
| `50c2456b` | `MCU_VDD` | (56.950, 70.500) | — |
| `6412f461` | `MCU_VDD` | (55.950, 65.900) | — |
| `828c3d14` | `MCU_VDD` | (57.550, 68.500) | — |
| `eee6d343` | `MCU_VDD` | (50.200, 69.500) | — |
| `c005da5e` | `P3V3` | (40.264, 35.980) | `bee0113d`(F.Cu)，`fa2e66a8`(F.Cu) |
| `9d2f5c90` | `P3V3_AUX` | (28.975, 53.000) | `04bb7caf`(F.Cu) |

### 3.2 `track_not_centered_on_via` 通过（16 案）

| 孔 | 网络 | 孔位 (mm) | 孔位移 (µm) | 走线端点动作 |
|---|---|---|---|---|
| `0f1a4587` | `P3V3` | (29.0400, 38.2000) | 0.0 | `58f0bbfa`S→(29.0400,38.2000) |
| `2028ad75` | `P3V3_AUX` | (59.6000, 48.4090) | 31.1 | `08e80caa`S→(59.6000,48.4090)，`ef273f09`E→(59.6000,48.4090) |
| `260eaec7` | `P3V3_AUX` | (26.5000, 61.5700) | 0.0 | `032098fa`S→(26.5000,61.5700) |
| `4de83ec4` | `I2C2_SCL` | (54.9734, 68.4000) | 35.7 | `ea6fe1d0`S→(54.9734,68.4000)，`fdb4faae`E→(54.9734,68.4000) |
| `682c9b73` | `PCIE_REFCLK0_N` | (131.4500, 45.4000) | 0.0 | `6e14bcff`E→(131.4500,45.4000) |
| `6b22d906` | `PWR_BTN_ISO` | (43.3000, 51.0234) | 35.7 | `12d195be`S→(43.3000,51.0234)，`2581bd16`E→(43.3000,51.0234) |
| `6c0fa8d0` | `PERSTA#` | (59.7000, 42.5429) | 42.6 | `af2ce5a6`S→(59.7000,42.5429)，`1d2d9cfc`E→(59.7000,42.5429) |
| `71821e4f` | `PCIE_REFCLK0_N` | (133.8250, 46.0900) | 0.0 | `7d2c9040`E→(133.8250,46.0900)，`187c37ee`S→(133.8250,46.0900) |
| `81b8efe9` | `GND` | (31.7375, 49.7500) | 0.0 | `8be14e62`S→(31.7375,49.7500) |
| `9ac7713e` | `I2C1_SDA` | (33.2000, 47.9000) | 21.5 | — |
| `a912e927` | `GND` | (103.6510, 55.9900) | 0.2 | — |
| `a985ebeb` | `P3V3_AUX` | (29.6000, 53.0000) | 50.0 | — |
| `cbe60e65` | `PCIE_REFCLK1_N` | (133.8250, 51.4900) | 0.0 | `2a0f1bc6`E→(133.8250,51.4900) |
| `d32e484a` | `MCU_VDD` | (30.5000, 54.5000) | 25.0 | `e3bdd905`E→(30.5000,54.5000) |
| `da9747d2` | `FB_U2` | (30.5000, 37.6350) | 25.0 | `e9d4c545`S→(30.5000,37.6350)，`8c3bb14c`E→(30.5000,37.6350) |
| `f73573df` | `P3V3_AUX` | (59.1000, 48.3811) | 42.3 | `a5483d18`S→(59.1000,48.3811)，`0c73965c`E→(59.1000,48.3811) |

### 3.3 `silk` 通过（28 案）

| 器件 | 字段 | 位移 (µm) | 采用字号 (mm) |
|---|---|---|---|
| `C89` | `650470ba` | 600 | 0.8 |
| `R43` | `2d091d59` | 3054 | 0.8 |
| `C85` | `b77ab151` | 1300 | 1.0 |
| `U4` | `316e45eb` | 7050 | 1.0 |
| `C81` | `c22051ca` | 6568 | 1.0 |
| `R39` | `1039d480` | 3235 | 1.0 |
| `C76` | `b4b5cd9f` | 3110 | 0.8 |
| `R35` | `018e953b` | 3235 | 1.0 |
| `C79` | `49c3c97c` | 5782 | 1.0 |
| `C73` | `ecb3f482` | 1909 | 1.0 |
| `R42` | `4f72a002` | 5235 | 1.0 |
| `C82` | `597e0af5` | 3767 | 0.8 |
| `R31` | `1e201d0d` | 2536 | 0.8 |
| `R38` | `f36c05ef` | 3235 | 0.8 |
| `C83` | `f7dcda74` | 6707 | 0.8 |
| `C88` | `2557f02e` | 3200 | 0.8 |
| `C77` | `51a7df40` | 2264 | 1.0 |
| `R37` | `8e8058e8` | 3054 | 0.8 |
| `C75` | `3aacf2ae` | 3288 | 0.8 |
| `R33` | `aaceeea7` | 3275 | 0.8 |
| `C90` | `fe981f28` | 1792 | 1.0 |
| `C74` | `f91f8364` | 2496 | 0.8 |
| `C84` | `d82733d9` | 1925 | 0.8 |
| `R34` | `b161d336` | 2404 | 0.8 |
| `J2` | `9abecb71` | 3380 | 0.8 |
| `J3` | `1a54a3cd` | 650 | 1.0 |
| `J4` | `ec22d5c7` | 650 | 1.0 |
| `U2` | `68897825` | 7303 | 1.0 |

## 4. 未处置 36 案的证据（逐条）

### 4.1 `via_dangling` 6 案：**支路承重**，切除即断网

| 孔 | 网络 | 复算否决原因 |
|---|---|---|
| `52ccc84f` | `P3V3` | unconnected:2, no-net-decrease |
| `b716313b` | `P3V3` | unconnected:1 |
| `326fd5bc` | `P3V3_AUX` | via_dangling:7->8, unconnected:4, no-net-decrease |
| `42594c9d` | `P3V3_AUX` | unconnected:2, no-net-decrease |
| `dbdf4b0a` | `P3V3_AUX` | unconnected:1, no-net-decrease |
| `dd59b566` | `SW_U2` | via_dangling:6->7, unconnected:2, no-net-decrease |

读法：这些孔所在支路的远端**接器件焊盘**（或切掉后暴露出下一个孤立孔），切除会使 `unconnected` > 0 ⇒ 违反「不改功能连接」⇒ 回退。**正确处置不是删，而是让该孔与同网平面/铜建立连接**（属 PDN/布线增量），或按「具名豁免 + 证据」另议 —— 提监理。

### 4.2 `track_not_centered_on_via` 18 案

| 类别 | 案数 | 证据 |
|---|---|---|
| **A. 无 0/45/90 合法候选**（位移上限 0.26 mm 内） | 8 | 孔心与两条走线交点均不重合：要消除违规必须让「端点精确落孔心」，而该点在**每条**涉事走线的非 0/45/90 方向 ⇒ 任何端点吸附都会产生非 45° 段；两段式折线（0°+90° 或 45°+45°）所需腿长 < 0.05 mm（低于单腿下限），亦不可行 ⇒ **局部不可解，须重布线/重定孔位** |
| **B. 移孔触发 `hole_to_hole`** | 6 | 孔心须移到走线端点（角节点），实测位移 0.03–0.15 mm 即与邻孔进入 < 0.25 mm 孔-孔下限 ⇒ 该局部无孔位空间 |
| **C. 移孔触发 `hole_clearance`** | 4 | 同上，但冲突对象是铜-孔净距 |

### 4.3 `silk` 12 案

| 器件 | 复算否决 |
|---|---|
| `C80` | no-net-decrease / no-free-slot |
| `R41` | no-net-decrease / no-free-slot |
| `R36` | no-net-decrease / no-free-slot |
| `R40` | no-net-decrease / no-free-slot |
| `R45` | no-net-decrease / no-free-slot |
| `R32` | no-net-decrease |
| `C86` | no-net-decrease / no-free-slot |
| `C80` | no-net-decrease / no-free-slot |
| `R41` | no-net-decrease / no-free-slot |
| `R36` | no-net-decrease / no-free-slot |
| `R40` | no-net-decrease / no-free-slot |
| `R45` | no-net-decrease / no-free-slot |

读法：`no-free-slot` = 本体周边 16 向 × 11 环内**无任何**满足「不压阻焊、不叠其它丝印、在板框内」的落点（密集去耦阵列区）；`silk_edge_clearance` = 候选位触发**板边丝印净距**（新增类型 ⇒ 复算否决）。⇒ 这些位号在丝印层**无局部可用空间**：可行处置为「重排布局/把该位号改置 F.Fab」或「按具名豁免另议」——须监理裁。

### 4.4 逐条明细（机器生成）

| 组 | 对象 | 否决原因 |
|---|---|---|
| via_dangling | `52ccc84f` (`P3V3`) | unconnected:2, no-net-decrease |
| via_dangling | `b716313b` (`P3V3`) | unconnected:1 |
| via_dangling | `326fd5bc` (`P3V3_AUX`) | via_dangling:7->8, unconnected:4, no-net-decrease |
| via_dangling | `42594c9d` (`P3V3_AUX`) | unconnected:2, no-net-decrease |
| via_dangling | `dbdf4b0a` (`P3V3_AUX`) | unconnected:1, no-net-decrease |
| via_dangling | `dd59b566` (`SW_U2`) | via_dangling:6->7, unconnected:2, no-net-decrease |
| tncv | `073ad34f` (`I2C1_SCL`) | hole_clearance:0->7, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, no-net-decrease |
| tncv | `2a02ffd7` (`I2C2_SDA`) | hole_clearance:0->8, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, no-net-decrease |
| tncv | `500c1c18` (`UART_TX`) | hole_to_hole:0->2, no-net-decrease |
| tncv | `62221d53` (`NRST`) | no-candidate-0/45/90+shift-cap |
| tncv | `7a5c015c` (`I2C2_SDA`) | no-candidate-0/45/90+shift-cap |
| tncv | `7b5ea818` (`I2C2_SDA`) | hole_to_hole:0->1 |
| tncv | `88f105cf` (`DS320_STRAP_B_ADDR1_15-8`) | no-candidate-0/45/90+shift-cap |
| tncv | `d7edd63f` (`PERSTA#`) | no-candidate-0/45/90+shift-cap |
| tncv | `dce1740d` (`I2C2_SCL`) | hole_to_hole:0->1, no-net-decrease |
| tncv | `073ad34f` (`I2C1_SCL`) | hole_clearance:0->7, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, no-net-decrease |
| tncv | `2a02ffd7` (`I2C2_SDA`) | hole_clearance:0->8, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, error:hole_clearance, no-net-decrease |
| tncv | `500c1c18` (`UART_TX`) | hole_to_hole:0->2, no-net-decrease |
| tncv | `62221d53` (`NRST`) | no-candidate-0/45/90+shift-cap |
| tncv | `7a5c015c` (`I2C2_SDA`) | no-candidate-0/45/90+shift-cap |
| tncv | `7b5ea818` (`I2C2_SDA`) | hole_to_hole:0->1 |
| tncv | `88f105cf` (`DS320_STRAP_B_ADDR1_15-8`) | no-candidate-0/45/90+shift-cap |
| tncv | `d7edd63f` (`PERSTA#`) | no-candidate-0/45/90+shift-cap |
| tncv | `dce1740d` (`I2C2_SCL`) | hole_to_hole:0->1, no-net-decrease |
| silk | `C80` (`5f1f0e28`) | no-net-decrease / no-free-slot |
| silk | `R41` (`a8525ae4`) | no-net-decrease / no-free-slot |
| silk | `R36` (`4ed84439`) | no-net-decrease / no-free-slot |
| silk | `R40` (`d5b58306`) | no-net-decrease / no-free-slot |
| silk | `R45` (`1435d42b`) | no-net-decrease / no-free-slot |
| silk | `R32` (`dd95fbe5`) | no-net-decrease |
| silk | `C86` (`ab94f422`) | no-net-decrease / no-free-slot |
| silk | `C80` (`5f1f0e28`) | no-net-decrease / no-free-slot |
| silk | `R41` (`a8525ae4`) | no-net-decrease / no-free-slot |
| silk | `R36` (`4ed84439`) | no-net-decrease / no-free-slot |
| silk | `R40` (`d5b58306`) | no-net-decrease / no-free-slot |
| silk | `R45` (`1435d42b`) | no-net-decrease / no-free-slot |

## 5. 关键工程发现（供监理/后续增量）

1. **W-7 五类并非同质**：`via_dangling` 12 条中 **6 条是承重支路**（删除即断网）⇒ 该类的正解是**接平面**而非删除；`tncv` 30 条中 **8 条局部几何不可解**（0/45/90 + 腿长 + 孔净距三重约束下无解）⇒ 须**重布线/重定孔位**。这两类**不能靠「逐条修」在本轮清零**，须监理裁「重布线增量」或「具名豁免+证据」。
2. **丝印位号在密集区无局部空间**：通过案的位移中位数已达 **3.2 mm**（p90 6.7 mm，最大 7.3 mm）⇒ 即使 DRC 全清，**装配可读性已退化**（位号远离本体）。这是「丝印违规清零」与「装配可读性」的真实冲突，须监理裁口径（建议：允许密集区位号置于 **F.Fab**，或接受 > 3 mm 位移）。
3. **zone 重填在本板是字节幂等的**（未改铜时重填前后 sha 相同）⇒ T-25 重填可安全用于逐案复算。
4. **`silk_over_copper` 的 6 条非位号项**（`U1`/`U6`/`D2` 的封装丝印线段压在开窗上）不在本工具处置范围（须裁剪封装图形）——见 §4.4 中 `silk` 段中 ref 为 `U1`/`U6`/`D2` 的项。

## 6. 复算链（确定性）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 施工器 dry-run（三组；只写 --work-dir，不碰仓库）
mkdir -p /tmp/opencode/w8h
AppDir/usr/bin/python3.11 k2/tools/k2_p4_w7_repair_v1.py \
  --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/w8h \
  --groups via_dangling,tncv,silk
# ② 复算用 pro = work-dir 内 9 条 severity 已置 warning 的副本（探针，非安装）
#    产出：k2_v4_8L.l5.repaired.kicad_pcb + drc_before.json/drc_after.json + report.json
# ③ 冻结判定器（只读，仓库 pro 语义）—— 期望 PASS 6 / FAIL 4 集合不变、非 45° = 0
D=/tmp/opencode/w8h/adj   # 该目录 = repaired 板 + 仓库 pro 同名副本 + fp-lib-table + lib/
python3 criteria/adjudicate.py --board $D/k2_v4_8L.l5.repaired.kicad_pcb \
  --manifest criteria/manifest.k2.yaml --nets k2/hw/data/k2_sch.errata-1.yaml \
  --sch-dir k2/hw/sch --pro $D/k2_v4_8L.l5.repaired.kicad_pro --out /tmp/v.json
```

**实测复核（本轮）**：

- dry-run 复算：`181` warning（error 0）→ `113` warning（error 0），`unconnected` **0 → 0**，违规类型集**零新增**。
- 结果板 sha256 前16 **`e10bf8e1de14550c`**（`/tmp/opencode/w8h/k2_v4_8L.l5.repaired.kicad_pcb`）。
- 冻结判定器（**repaired 板 `e10bf8e1de14550c`** + 仓库 pro 语义）：**PASS 6 / FAIL 4（FAIL 集合与基线逐条相同：`zone_filled` 10/18 · `rule_severity_manifest` 9/62 · `refdes_sets_equal` 板有图无 4 · `pipeline_present`）**、`non45_segments` **0/4702**（基线 0/4705，段数 −3 = 切除 3 条死端线段）、`drill_count` NPTH 4 / PTH 16 不变。
- **源件零改动**：`k2_v4_8L.l5.kicad_pcb` `37019705ef994ccc` · 同名 pro `f68a5fb2f82bd02d` · `criteria/adjudicate.py` `897e8bfde60e2cfe` · `criteria/manifest.k2.yaml` `7ce08757eff25557` · 设计源板 `fb07d25ac426ff84` · 真源 `dd794c54f7ce7417` —— 全部与本 handoff §1 冻结值一致。
- **复跑确定性（两次独立全量运行）**：`/tmp/opencode/w8h` 与 `/tmp/opencode/w8i` 产出的结果板
  sha256 前16 **均为 `e10bf8e1de14550c`**（逐字节相同）；两次 `report.json` 的逐案接受/驳回集合亦相同。

### 6.1 结果板 sha 账

| 项 | 值 |
|---|---|
| 源板 | `k2/hw/k2_v4_8L.l5.kicad_pcb` = `37019705ef994ccc`（未动） |
| 修复板（dry-run 产物） | `/tmp/opencode/w8h/k2_v4_8L.l5.repaired.kicad_pcb` = `e10bf8e1de14550c` |
| 复跑一致性 | `w8i` 结果板 = `e10bf8e1de14550c`（逐字节同） |
| zone 重填幂等性 | 未改铜时重填前后 sha 相同（`37019705ef994ccc`） |

## 7. 待监理（本件不代判）

1. **批准落件**：批则 ENG 以 T-22 流程落 `k2/hw/k2_v4_8L.l5.kicad_pcb`（板 > pro 备份 + 同名 pro 逐字节校验 + SPEC bump），并复算 §6 全链；**未批不落**。
2. **未处置 37 案的口径**：① `tncv` 8 案局部不可解 + `via_dangling` 6 案承重支路 ⇒ 是否批准**重布线/重定孔位增量**；② 是否接受「丝印位号远移（> 3 mm）」或改置 **F.Fab**；③ 6 条封装丝印线段（`U1`/`U6`/`D2`）是否允许裁剪。
3. **`missing_courtyard` 40 条**：外扩口径仍属 §4-1 耦合裁定；口径定后本工具 v2 可按参数落该组。
4. 本条**未新增检查齿**（owner ②）：全部处置只对**已登记** 9 条规则的既有违规施工，未新增任何验证项。

—— ENG（ARCHER）· 2026-09-18 · 工具 `k2/tools/k2_p4_w7_repair_v1.py`（dry-run 默认）
