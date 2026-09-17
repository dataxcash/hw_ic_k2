# K2 · P4 · W-8 / J-7 · `FootprintNeedsUpdate` 触发字段隔离 + (甲′) 闭合实测

| 项 | 值 |
|---|---|
| 件 | `k2/docs/K2-P4-W8-J7-TRIGGER-ISOLATION-v1.md`（ENG 交件，**待监理**） |
| 会话 | ARCHER 续接（ctx 归零；按 `k2-p4-handoff-20260918-ctx423k-inc20.md` §4-2 / §7-4） |
| 板态 | `k2/hw/k2_v4_8L.l5.kicad_pcb` = `37019705ef994ccc`（**未改**）· pro = `f68a5fb2f82bd02d`（**未改**） |
| 工具 | `k2/tools/k2_w8_trigger_isolation_v1.py`（只读探针，可复跑；sha 见 §9） |
| 裁定 | **ENG 不自行择一**。本件只交证据：触发字段表 · (甲′) 闭合实测 · (乙) 范围量化。 |

## 0. 先决复算（本会话实测，与 handoff §1/§2/§6 逐项一致）
9 项冻结源 sha 前缀全对（`5f72182a2616392c` / `a8ef3ea8ecff99d7` / `fb07d25ac426ff84` / `d4e81f647be7f980` /
`0a459839e15960b8` / `dd794c54f7ce7417` / `897e8bfde60e2cfe` / `7ce08757eff25557` / `17d540f058631a5e`）；
canonical SPEC rev-46 = `dea36093ba2b4031`、rev-45 = `47a3cae72cff7e5f` 原件未动。复跑链 ①–⑦ 全对：
DRC **35**（error 0 / warning 35 = `lib_footprint_mismatch`）· 未连接 **0** · 段/孔/总长 **4705 / 715 / 6287.3747mm** ·
非45 **0** · zone **18** · 对内等长 max **0.0788** · 冻结判定器 **PASS 6 / FAIL 4**（`zone_filled` 10/18）·
草案判定器 **PASS 13 / FAIL 5** · W-8 审计工具 `75404d706413d546` → 33/35 · strap 执行器幂等（out sha = 板 sha）·
NPTH H3=(45.1,75.1)。

## 1. 结论摘要
1. **触发字段已隔离（判定口径 = KiCad 自身判定，非自造检查齿）**：`FootprintNeedsUpdate` **比较** 封装层(F/B)、
   封装 `attr`、pad 层集合、pad 号/尺寸/局部位置/自转/形状/属性、图形项；**不比较** FPID 链接名、`Reference`/`Value`
   文本/层/可见性/位置、封装锚点 `(at)`、封装自转、pad 网络、`uuid`/`path`/`tstamp`。
2. **(甲′) 物理可行，且已实测闭合到 0 违规**：以板为准的项目封装库 + 逐 variant（或逐 refdes）**链接名**改写
   + 35 件 **`(attr …)` 元数据** 补写 ⇒ DRC **35 → 0**（`lib_footprint_mismatch` 35→0、`lib_footprint_issues` →0、
   未连接 0、schematic_parity 0）；**段/孔/zone/图形逐字节未动**，59 个封装块除「链接头行 + attr 行」外逐字节相同。
3. **但 (甲′) 有一个硬前提**：KiCad **库装载无法产出 `attr=0`**（无 `(attr)` → 1、`(attr smd)` → 2、`(attr dnp)` → 64），
   而本板恰好**违反 `lib_footprint_mismatch` 的 35 件全部是 `attr=0`**（非规范值：既非 SMD 亦非 THT）。
   ⇒ 只要板保持 `attr=0`，任何库内容都**不可能**达成 parity；`(甲′)/(乙)` 都必含这 35 件的 `(attr)` 元数据修订。
4. **共享单一库条目不足以闭合**：按上游 item name 共享条目时残留 12（35 件域）/ 21（59 件域）条
   —— 因同一 item name 在板上对应**多种不同 land pattern**（如 `C_0402_1005Metric` 同时存在 0.6×0.7@∓0.45 与
   0.4×0.5@∓0.35 两种）、顶/底面膜层变体、以及 J3/J4 镜像差异。

## 2. 方法与口径
- **判定器**：`pcbnew.FOOTPRINT.FootprintNeedsUpdate(lib_fp)`（KiCad 10.0.5；DRC `lib_footprint_mismatch` 即此判定）。
- **基线（parity base）**：把**板自身的封装文本**写入 `.kicad_mod` 再 `FootprintLoad`，并把 `attr` 对齐到板值
  ⇒ `needs_update=False`（即除 attr 外该文本与板全等）。此后**逐字段单变量扰动**，`True` ⇒ 被比较。
- **地面真值**：`/tmp` 探针目录内含**同名 pro + fp-lib-table + 板拷贝**（等价 T-8 口径），用 `kicad-cli pcb drc`
  实测；P4 结果独立复跑两次一致。
- **只读边界**：仓库板 / pro / SPEC / `criteria/` / 真源 / 生成器 **逐字节未改**；探针中间件全在 `/tmp/opencode/w8iso/`。

## 3. 触发字段表（`--ref U4`；base `needs_update=False`）
| 字段 | 结论 | 字段 | 结论 |
|---|---|---|---|
| 封装 layer `:=B.Cu` | **比较** | `Reference`/`Value` 文本 | 不比较 |
| 封装 `attr :=` 其它 | **比较** | `Reference` 层 / 可见性 / 位置 | 不比较 |
| pad 层集合 | **比较** | 封装锚点 `(at)` 平移 | 不比较 |
| pad 尺寸 / 号 / 局部位置 / 自转 / 形状 / 属性 | **比较** | 封装自转 180° | 不比较 |
| 图形项（新增 F.SilkS 线） | **比较** | pad 网络码 | 不比较 |
| SMD pad 钻孔（本板 35 件全为 SMD） | 未触发 | `uuid` / `path` / `tstamp`（文本） | 不比较 |

注：`attr` 的比较由独立实验确证——「板自身文本 + attr 对齐」⇒ False；仅把 attr 改回装载默认值 ⇒ True。

## 4. 为什么「板 = 库逐字快照」仍 mismatch（上一会话未定论的那条）
- 库装载**归一化 `attr`**：无 `(attr)` → **1**(THT)、`(attr smd)` → **2**、`(attr through_hole)` → **1**、`(attr dnp)` → **64**；
  **无任何写法能得到 0**。板侧（`.kicad_pcb`）不归一化，故 35 件读到 0。
- 本板 59 件 `attr` 直方图 = `{0:35, 2:15, 1:5, 12:4}`；**`attr=0` 的 35 件与 DRC 报出的 35 件完全同一集合**。
- ⇒ 「图形级 vs 电气级」二分对本 case 描述不充分：**只要 attr 不同即 mismatch**，与 pad 是否同几何无关。

## 5. (甲′) 闭合实测（`drc-probe`，全在 `/tmp`）
| 变体 | 板侧改动 | DRC 违规 | 残留 mismatch |
|---|---|---|---|
| P1c `attr` 只改，链接不动 | 35 件 `(attr …)` | **35** = 29 mismatch + **6 `lib_footprint_issues`** | 29（std 名件几何仍不同） |
| P2 改链接到项目库（按上游 item name 共享条目）+ attr | 59 链接 + 35 attr | **12** mismatch | `C73…C90(部分) · J4` |
| P3 同上，链接 59 件全改 | 59 链接 + 35 attr | **21** mismatch | 同上 + `R1/R3/R21/R28/R29/R31…R34` |
| **P4 逐 refdes（每件一独立条目）+ attr** | **59 链接 + 35 attr** | **0**（未连接 0、schematic_parity 0、ignored 9 不变） | **无** |

P4 板文件与仓库板的差异（`difflib` 实测）：**仅** 59 行 `(footprint "…")` 链接头 + 35 行 `(attr …)` 插入；
**铜逐字节相同**：`segment` sha `f08fe520c4a45147`(4705) · `via` `31add10a8a63668f`(715) · `zone` `88a9e2d13090adf8`(18) ·
`gr_line` `e9ae8ed80f9c45b6`(4)；59 封装块剥除「链接头 + attr 行」后**逐字节相同**。
⇒ **(甲′) 不需要动任何 pad / 铜 / 走线**；所需板侧改动 = 链接名 + `(attr)` 元数据。

## 6. 现 `k2/hw/lib/ForgeOS.pretty` **不是** board-authoritative
- 仅 6 条目（板有 59 件）；6 件库文本与板块**均非逐字相同**（如 U4：库 1285B vs 板 1395B）。
- 关键差异（`deepdiff`）：库 pad 在 `B.Cu` + 非规范层名 `"Rescue"`（板 pad 在 `F.Cu/F.Mask/F.Paste`）；
  库带 `(attr smd)` 而板 `attr=0`；`E2` 的 pad 5–8 在 y 向**镜像**；`J2/J3/J4` 的 pad 尺寸/号名（库 1..38 vs 板 A1..A38）、
  位置、以及 8 个 Fab/Courtyard 图形项均与板不同。
- ⇒ 上一增量「已建 fp-lib-table」只完成表侧；**库内容**（板为准）尚未建立，这解释了为什么「建表即可闭合」不成立。

## 7. (乙) 范围量化 + ENG 观察（**不自行择一**）
| 上游链接名 | 件数 | 板 land（pad 尺寸 @ 中心） | 上游 std land | 趾外伸(板) | 内间隙(板) |
|---|---|---|---|---|---|
| `Capacitor_SMD:C_0402_1005Metric` | 1 | 0.6×0.7 @∓0.45 | 0.56×0.62 @∓0.48 | +0.25 | 0.3 |
| 同上 | 11 | 0.4×0.5 @∓0.35 | 同上 | +0.05 | 0.3 |
| `Capacitor_SMD:C_0603_1608Metric` | 5 | 0.6×0.7 @∓0.45 | 0.9×0.95 @∓0.775 | **−0.05** | 0.3 |
| `Capacitor_SMD:C_0805_2012Metric` | 1 | 0.8×0.9 @∓0.6 | 1.0×1.45 @∓0.95 | 0.0 | 0.4 |
| `Resistor_SMD:R_0603_1608Metric` | 9 | 0.6×0.7 @∓0.45 | 0.8×0.95 @∓0.825 | **−0.05** | 0.3 |
| `LED_SMD:LED_0603_1608Metric` | 1 | 0.6×0.7 @∓0.45 | 0.875×0.95 @∓0.7875 | **−0.05** | 0.3 |
| `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm` | 1 | 0.6×0.9 @ x∓1.95（y 距 1.27 ✔） | 1.625×0.65 @ x∓3.5875 | — | — |
| `ForgeOS:*`（U4/U5/E2/J2/J3/J4） | 6 | 项目自定（非上游库） | 无上游可比 | — | — |

**ENG 观察（供裁定参考，非裁定）**：上表 29 件「上游名件」的板 land 是生成器简化版，而非所冠包名的实际 land：
- SOIC-8：板上焊盘 x 域 [1.65,2.25] 完全落在 5.3mm 体宽（半宽 2.65）**之内**，而该封装鸥翼引脚落点约 x∓3.5875
  ⇒ 引脚与焊盘**x 域无交集**（该件按所冠包名不可焊）。
- 0603 件（15 件）：趾外伸 **−0.05mm**（上游 nominal ≈ +0.43…+0.5）、内间隙 **0.3mm**（上游 0.7–0.85）
  ⇒ 体下窄间隙有桥连/立碑风险，且无趾部焊角。
- 图形项普查：59 件中 **40 件图形项 = 0**（无 Fab/Courtyard/Silk）——恰为「35 件 attr=0（即报出 mismatch 者）+ 5 件裸露 THT 排针
  J6/J9/J11/J12/J13」，与 W-7 清单 `missing_courtyard` **40 项**同数同源；其余 19 件（真实 land 的裸名件：U1/U6/H1–H4/
  R35–R45/L1/D2）带 Fab/Courtyard/Silk。⇒ (甲′) 会把「无图形」一并固化为库内容，(乙) 则随上游图案补齐。
- 反面对照：**裸名**（无库链接）24 件是真实 land（如 `U1` LQFP48 pad 跨 ±4.162 与 KiCad LQFP-48 上游一致）。
  ⇒ 该偏差**局限于「上游库名 + 生成器简化 land」的 29 件**，非全板系统性。

## 8. 待监理裁定（ENG 不改口径）
1. **(甲′)/(乙) 择一**：本件给出两者的量级——(甲′) = 59 链接头 + 35 `(attr)` + 新项目库（铜 0 改动，但保留简化 land）；
   (乙) = 29 件 pad 尺寸/位置改写（+E2/J2/J3/J4 结构差异）⇒ 铜/走线/DRC 级联。
2. 若择 (甲′)：需批准 (i) 逐 variant/逐 refdes 命名（**单一上游 item name 共享条目不够**，见 §1-4）、
   (ii) 35 件 `(attr)` 元数据修订（1 件 1 行，属板文本改动，须 T-22/T-25 纪律 + SPEC bump）、(iii) 项目库耐久件落库。
3. 草案判据 `lib_footprint_link_policy`（现为 `null` ⇒ fail-closed）：口径应指向「按 fp-lib-table 解析的项目库」(甲′) 还是
   「上游 std roots」(乙)——这是 `lib_footprint_electrical` 的唯一开关。
4. 35 条 `lib_footprint_mismatch` 的 `drc_warning_disposition` 登记（现空 ⇒ 有 warning 即 FAIL）。
5. 本件**未安装**任何改动；P4 仍**未全绿**（判定器仍 PASS 6/FAIL 4），不宣称 P4 完工、不出 Gerber。

## 9. 复跑（确定性）
```bash
cd /home/fila/jqdDev_2025/ic_hw
AppDir/usr/bin/python3.11 k2/tools/k2_w8_trigger_isolation_v1.py trigger-matrix --ref U4   # 触发字段表；base=False
AppDir/usr/bin/python3.11 k2/tools/k2_w8_trigger_isolation_v1.py drc-probe                 # P1c 35 / P2 12 / P3 21 / P4 0
```
工件：工具 sha256(16) = `83d4036090b125c3`（本件自身 sha 记录于 ledger，避免自引用）。

## 10. 边界
未改板（`37019705ef994ccc`）/ pro（`f68a5fb2f82bd02d`）/ SPEC / 真源 / 生成器 / `criteria/`；未新增检查齿（owner ②）；
未派 WORKER；未写 `.omo/supervision/**`；临时件仅 `/tmp/opencode/w8iso/`；未安装探针结论（fail-closed，未越阶段）。
