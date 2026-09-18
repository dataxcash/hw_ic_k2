# K2 · P4 · `G10` **NPTH 段草案**（4 固定孔：逐座标 + Ø3.2 + 全层 keepout；含回归自证 + KiCad 级验证）· v1 · 2026-09-18

> 缘起：handoff inc63 §6-3-(l)「`G10` 的 **NPTH 段草案**（4 孔逐座标 + Ø3.2，与 inc55 表 B / `K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md` 同源；**仍属草案、不落件**）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**仓库零载体改动**（仅新增本证据件）。锚：受审板 `6ff49da5678c2108` · l5 pro `d5e0ca067a7b585e` · 真源 `dd794c54f7ce7417` · SPEC rev-47 `9ba09cbc148d6836` · 图纸 `21e8891ea3fc4c06`。
> 草案装置（`/tmp`，易失）：`/tmp/opencode/inc63/g10_npth_draft.py` **`56cdbef1e48e8b1e`** · 板实测件 `measure_npth.py` `184620528d3712c9` → `npth_measured.json` **`e4ae10f1e87043cb`** · 候选数据块 `npth_input.json` **`ab053d17b8580308`** · emit 产物 `npth_emit.txt` **`03ef8ef22d4525f3`**（**两次 emit 同 sha ⇒ 确定性 ✓**，T-38）。

## 0. 结论（五条）

1. **草案已成件（`/tmp`）**：① **候选输入层数据块**（4 孔：座标 / `drill` / keepout 尺寸 / 边料；值取自 L2-3 裁定＝板值，经本件**重新实测复核**）；
   ② **生成段** `emit_footprint()`（产出 KiCad `(footprint "MountingHole_3.2mm_M3" …)` 段，形状逐项对齐板内原始段，含 `np_thru_hole` pad）。
2. **与权威源逐值一致**：本件板实测（`npth_measured.json`）＝ inc55 表 B1/B2 ＝ `K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md` §2 表 —— **H1(26.10,75.60) · H2(139.60,39.60) · H3(45.10,75.10) · H4(114.60,36.10)**，drill **Ø3.2**，keepout **6.00×6.00**，**4 个 keepout bbox 精确居中于孔心（d=0.00）**。
3. **回归自证 PASS**：`emit → 解析回比` 数据块 ⇒ **4 孔、0 字段差异**（比对项：`footprint` 名 / `Reference` / `at` / pad `np_thru_hole circle` / `size` / `drill` / `layers`）。
4. **KiCad 级验证 PASS**：受审板**剥离** 4 个 NPTH footprint（`removed 4`）→ 插入 emit 结果 → `pcbnew.LoadBoard` **成功** → 量测 **4 个 NPTH pad 逐值匹配**（含 drill 3.2）→ `SaveBoard` → **重载复核 4/4 + 原 18 区仍在**。
   ⇒ 产出**语法有效、结构等价**；且**不放松**任何已裁维度。
5. **不新增检查齿（owner ②）**：NPTH 收敛复用**既有冻结晶格 `drill_count`**；本件**未**定义新阈值/新维度。**ENG 未写 SPEC、未落件、未出 Gerber。**

## 1. 候选输入层数据块（4 孔；值＝L2-3 裁定 + 本件板实测复核）

| ref | 座标 `(x,y)` | `drill` | keepout 尺寸 | keepout bbox `(x0,y0,x1,y1)` | 边料 min | footprint | `fp_uuid`（uuid5 确定性） |
|---|---|---|---|---|---|---|---|
| `H1` | (26.10, 75.60) | 3.2 | 6.00×6.00 | (23.10, 72.60, 29.10, 78.60) | 1.50 | `MountingHole_3.2mm_M3` | `cbf21d6c-742b-582b-860a-43f8bc42984d` |
| `H2` | (139.60, 39.60) | 3.2 | 6.00×6.00 | (136.60, 36.60, 142.60, 42.60) | 1.80 | 同上 | `242b91aa-f418-5c82-8741-c94d3c946919` |
| **`H3`** | **(45.10, 75.10)** | 3.2 | 6.00×6.00 | (42.10, 72.10, 48.10, 78.10) | **2.30** | 同上 | `4b31f13b-91a9-512c-ae61-dd023cfdeae5` |
| `H4` | (114.60, 36.10) | 3.2 | 6.00×6.00 | (111.60, 33.10, 117.60, 39.10) | 1.50 | 同上 | `02045cd5-b7cf-53a4-972a-ff9b8959a12c` |

> **H3 是唯一相对图纸的位移孔**：图纸 `mounting_holes.positions.H3 = (26.1,36.1)`（**裁决前值**）；权威＝`#K2-19 §一-3`（L2 热机械自裁）⇒ `(45.10,75.10)`（位移 43.38mm，H1/H2/H4 不动）。
> 同源的图纸刷新项＝ Z4 清单 **D3/D4**（见 `K2-P4-Z4-STALE-REFRESH-CHECKLIST-v1.md`），随 **Z4+Z2 一次投递包** 执行，本件不重复登记。
> 4 孔全部满足「边料 ≥1.5 + Ø6.0 keepout 内无 track/via 且无 pad」（`K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md` §2）；孔间最小距 `H1–H3 = 19.01mm`（≥3.45 ✓）。

## 2. 生成段（emit 形状；与板内原始段逐项对应）

- **footprint**：`(footprint "MountingHole_3.2mm_M3" (layer "F.Cu") (uuid …) (at X Y) (descr …) (property "Reference" "Hn" …) (property "Value" …) (attr exclude_from_pos_files exclude_from_bom) (fp_circle …Cmts.User Ø3.2) (fp_circle …F.CrtYd Ø3.45) (pad …))`
- **NPTH pad**（**本件实质**）：
  ```
  (pad "" np_thru_hole circle
      (at 0 0)
      (size 3.2 3.2)
      (drill 3.2)
      (layers "*.Cu" "*.Mask")
  )
  ```
  > 口径：`size`＝`drill`＝**3.2**（无环 NPTH）；层集写法＝**`"*.Cu" "*.Mask"`**（板源文本原样）。注：KiCad LSET 展开后含 **32 个铜层名**（`F.Cu/B.Cu/In1..In30.Cu`），但**源文本是通配 `*.Cu`** ⇒ 生成器应产**通配写法**，不得枚举（否则 8 层板产出 32 项枚举、与板源不逐字节一致）。
- **uuid 确定性**：`uuid5(固定 NS, f'k2/g10/npth/{ref}')` ⇒ 满足 T-38 固定种子（两次生成同 sha）。

## 3. 回归自证（round-trip，`--roundtrip`）

```
emit → (解析回来) → 与 HOLES 逐孔逐字段比对
round-trip: holes=4 mismatches=0 ⇒ PASS
```
比对字段：`footprint` 名 · `Reference` · `at`（浮点逐值）· pad 形态 `np_thru_hole circle` · `size` · `drill` · `layers`（字符串序）。⇒「数据块 → 生成段 → 解析」**无损**。

## 4. KiCad 级验证（剥离→插入→加载→量测→保存→重载）

| 步 | 结果 |
|---|---|
| 剥离受审板 4 个 `MountingHole_3.2mm_M3` footprint | `removed 4` |
| 插入 emit 结果（`board_npth_draft.kicad_pcb`） | 写入 4 个 footprint |
| `pcbnew.LoadBoard` | **成功**，NPTH pad = **4**，`match=True` |
| 量测 | `H1(26.1,75.6,3.2) · H2(139.6,39.6,3.2) · H3(45.1,75.1,3.2) · H4(114.6,36.1,3.2)`（座标 + drill） |
| `SaveBoard` → `board_npth_filled.kicad_pcb` | **成功** |
| 重载复核 | NPTH **4/4**（drill 3.2）；原板 **18 区仍在**，`K2_HOLE_KEEPOUT_H1..H4` **4/4** |

## 5. 与「G10 全量」的差距（本件只覆盖 NPTH 半边）

| G10 组成 | 状态 |
|---|---|
| **NPTH 4 孔段**（H1–H4 逐座标 + Ø3.2） | **本件已成件**（§1/§2/§3/§4） |
| **keepout 段**（8 区：4 全层孔 keepout + 4 F.Cu ESC） | 见 `K2-P4-Z2-G10-KEEPOUT-ZONE-DRAFT-v1.md`（已成件；回归 18/0 PASS；KiCad 级全绿） |
| **有网铜区段**（10 区） | 同上（已成件） |
| **出图前 `ZONE_FILLER`** | 既有（P4 板侧已 10/10） |
| 判据在岗（`drill_count`（冻结）/`keepout_active`/`zone_filled`） | 待 `criteria/` 安装 + manifest 签认（**与 Z4/⑤ 同批**） |

**口径差（属 Z2 待裁，本件不择一）**：图纸 `KO-1..4`（Ø6.0，count=4）为**五开关全 blocked**；板 4 个 `K2_HOLE_KEEPOUT_H1..H4` 为 `tracks`/`vias`/`copperpour` `not_allowed`、**`pads`/`footprints` `allowed`**（因孔 pad 自身落在 keepout 内）。⇒ 与 inc55 表 **B3** 同一待裁项，**「以板为准」（W-8 式）裁后本件数据块即可直接投递**。

## 6. `G10` 裁定后的执行序（与 Z2 段合批，一次投递）

```
Step 0  裁 G10/Z2：keepout/zone/NPTH 是否「以板为准」（＋是否触 C-1 的说明）
Step 1  把 §1 数据块写入**输入层**（SPEC `mounting_holes` / `pd.npth_defs`；SPEC bump）
        ※ 孔参数（Ø3.2 / keepout Ø6.0 / 边料 ≥1.5）已在输入层与板一致 ⇒ 仅 H3 座标须随 Z4-D3/D4 刷新
Step 2  生成器加 §2 生成段（消费 Step 1 输入；**禁读板**）
Step 3  /tmp 复跑：emit → round-trip（§3）→ KiCad 剥离/插入/加载/量测（§4）全绿
Step 4  与 keepout/zone 段（inc62）、G9/G11 合批落库（须放行）+ 判据安装 + 落件板 sha 复算
```

## 7. 复跑（每处实测；仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw; W=/tmp/opencode/inc63
# ① 板实测复核（4 NPTH + 4 孔 keepout；输出含 board_sha16）
AppDir/usr/bin/python3.11 $W/measure_npth.py | head -40
# ② 回归自证（期望 holes=4 mismatches=0 PASS）
AppDir/usr/bin/python3.11 $W/g10_npth_draft.py --roundtrip; echo "rc=$?"
# ③ 导出候选数据块 + emit（期望 emit sha16 = 03ef8ef22d4525f3）
AppDir/usr/bin/python3.11 $W/g10_npth_draft.py --json $W/npth_input.json --emit $W/npth_emit.txt
sha256sum $W/npth_emit.txt | cut -c1-16
# ④ KiCad 级：剥 4 footprint → 插 emit → Load → 量测 → Save → 重载
cp k2/hw/k2_v4_8L.l5.kicad_pro $W/board_npth_draft.kicad_pro   # T-8：DRC/加载取同名 pro
AppDir/usr/bin/python3.11 $W/g10_npth_draft.py --kicad --work $W
```

## 8. 边界

本件**只读 + `/tmp` 草案/变体板**：未改 SPEC/板/pro/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/真源/图纸/`criteria/**`/`_shared/**`；
未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc63`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · 草案 `56cdbef1e48e8b1e` · emit `03ef8ef22d4525f3`
