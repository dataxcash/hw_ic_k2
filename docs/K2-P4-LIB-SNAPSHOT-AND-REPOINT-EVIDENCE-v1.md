# K2 · P4 · ⑦「库侧收口」—— **以板为准的封装库快照 + 全板 `lib_id` 重指** · 证据件 v1

> 依据：监理 **#K2-21 §二⑦**（「**裁定：以板为准** …… 电气级必须 0（pad 数/名/尺寸/旋转/位置逐件比）；
> 35 件逐条登记；**同时建 `fp-lib-table`**（F-12 收口）」）+ 登记册处置路线
> 「以板为准 + **库侧待按板重建并让 board `lib_id` 指向项目库**」（`K2-P4-COURTYARD-AND-LIB-REGISTER-v1.md` §3-3/§4-3）。
> 对象 = 已落件五步复合板 **`6ff49da5678c2108`**（`k2/hw/k2_v4_8L.l5.kicad_pcb`，**本件未改仓库**）。
> 本件为**候选板 + 测量 + 判据复算**；**落件归监理**（涉板 sha/SPEC 版本 bump）。

## 0. 一件工具（dry-run 默认，未落仓库）

`k2/tools/k2_p4_lib_snapshot_v1.py` sha256 前16 = **`91c9f5a1138a9825`**。三步、全确定性：

1. **按 land pattern 重建项目库快照**：59 颗 footprint → **24 个 distinct land pattern** → `lib/ForgeOS.pretty/`（含 `Reference`/`Value` 归一为 `REF**`/件名、uuid 原样）；
2. **全板 `lib_id` 重指** `ForgeOS:<快照名>`（原板上 **24 颗无 nickname**、9 颗 `R_0603_1608Metric` 裸名、9 颗
   `Resistor_SMD:R_0603_1608Metric` 双拼写 —— 一并收敛为**唯一项目库命名空间**）；
3. **硬闸 + 守恒闸 + 独立等价闸**，出候选板。

**T-41**：`--apply` 必须伴 `--confirm-repo-write`（实测缺旗标 ⇒ 拒绝，rc=2）；**T-22**：落件前备份板+库、
落件后 `dst pro` 逐字节校验；**T-38** 固定种子；**删除策略**：本器**只增/改不删**，库内 12 件快照外旧件
**列出但不删**（删除须监理另裁）。

## 1. 结果摘要

| 量 | 基线（仓库板 + 仓库库） | 候选板 `f93a1698adcf4863` + 快照库 |
|---|---|---|
| DRC `lib_footprint_mismatch` | **35** | **0** |
| DRC `error` / `unconnected` | 0 / 0 | 0 / 0 |
| DRC 其余 warning | `missing_courtyard` 40 | `missing_courtyard` 40（**不变**） |
| W-8 v1 `n_electrical_diff` + `n_pad_name_set_only` | **31 + 2 = 33** | **8 + 0**（全部为放置约定，见 §4） |
| W-8 v2（放置帧归一，草案）同项 | **31 + 2 = 33**（不变 ⇒ 不放松） | **0 + 0** |
| 独立物理等价（板件 vs 库件按板位姿放置） | 33 件物理不同 | **59/59 物理等价（0 物理差异）** |
| 草案 v4 判定器（安装件） | **15 PASS / 2 FAIL** | **15 PASS / 2 FAIL**（v1 口径）/ **16 PASS / 1 FAIL**（v2 口径） |

FAIL 集变化：基线 = `pipeline_present` + `lib_electrical_level`；候选 + W-8 v2 = **仅 `pipeline_present`**
（gate 安装项，属 gate 属主侧）。**wire 守恒**：tracks 4721 / vias 711 / zones 18 / nets 102 / fps 59 / pads 687
**逐项不变**；非 45° = 0；`column_x`（J6/J9/J11/J12/J13 = 27.94）不变；文本差异 = **55 行，全部为 footprint 头行**
（59 颗中 4 颗原本已指向 `ForgeOS:<同名>` ⇒ 不需改）。

## 2. 快照库内容（24 件）

| 快照件 | 成员数 | 板上成员 | mod sha16 |
|---|---|---|---|
| `C_0402_1005Metric__1` | 10 | C74, C75, C76, C77, C79, C80, C81, C82, C87, C90 | `2021fa5f607bcc60` |
| `C_0402_1005Metric__2` | 1 | C85 | `89f0c9305e90fddc` |
| `C_0402_1005Metric__3` | 1 | C73 | `0aebf136d594b235` |
| `C_0603_1608Metric` | 5 | C78, C83, C86, C88, C89 | `ae0a429fab63d4a1` |
| `C_0805_2012Metric` | 1 | C84 | `10273c7ee9b3b518` |
| `DS320PR1601` | 1 | U6 | `1324764bef246e75` |
| `D_SMA` | 1 | D2 | `e0ff540df8e5b557` |
| `LED_0603_1608Metric` | 1 | D1 | `d95ac97423b014a5` |
| `L_0805_2012Metric` | 1 | L1 | `d64733648b86ba4a` |
| `MCIO_4i_SFF-1016_RASide__1` | 1 | J3 | `57503b10f912e967` |
| `MCIO_4i_SFF-1016_RASide__2` | 1 | J4 | `fe055dcf47c72758` |
| `MCU_STM32G0_LQFP48` | 1 | U1 | `34685950abec100a` |
| `MountingHole_3.2mm_M3` | 4 | H1, H2, H3, H4 | `79b364f077d00446` |
| `OPTO_LTV356T` | 1 | U5 | `ac52d63d2fd78c6a` |
| `PinHeader_1x02` | 2 | J12, J6 | `fbbc084f1a076bcd` |
| `PinHeader_1x04` | 3 | J11, J13, J9 | `a521058d3c785222` |
| `R_0402_1005Metric__1` | 1 | R41 | `6fa7750e352e99ca` |
| `R_0402_1005Metric__2` | 1 | R40 | `8af93e4681bd5f44` |
| `R_0603_1608Metric__1` | 9 | R1, R21, R28, R29, R3, R31, R32, R33, R34 | `9c6853b31411ca2c` |
| `R_0603_1608Metric__2` | 9 | R35, R36, R37, R38, R39, R42, R43, R44, R45 | `d8c2a084040578a5` |
| `SOIC-8_5.3x5.3mm_P1.27mm` | 1 | U2 | `a0b0852025cd708e` |
| `SOIC8_FRU` | 1 | E2 | `c26fac5adfc84bbf` |
| `SOT23_BAT54C` | 1 | U4 | `77f166bf26a2d7bb` |
| `SlimSAS_x8_SFF-8654_74pin_RASide` | 1 | J2 | `3993f29479ae59a2` |

**同件名但 land pattern 不同者（本板真实差异，重组后各自成件）**：
`C_0402_1005Metric` × 3（C73 单独 / C85 单独 / 其余 10 件）；`R_0603_1608Metric` × 2（
`Resistor_SMD:*` 9 件 vs 裸名 `R_0603_1608Metric` 9 件 —— **同名两种拼写下 pad 几何确实不同**）；
`R_0402_1005Metric` × 2（R40 / R41）；`MCIO_4i_SFF-1016_RASide` × 2（J3 / J4）。

## 3. 复跑链（确定性；`/tmp` 易失须重建）

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; CLI=AppDir/bin/kicad-cli; B=k2/hw/k2_v4_8L.l5.kicad_pcb; P=k2/hw/k2_v4_8L.l5.kicad_pro
# ① 候选板（dry-run；期望 sha16 f93a1698adcf4863，两次复跑逐字节同）
$K k2/tools/k2_p4_lib_snapshot_v1.py --board $B --pro $P --kicad-cli $CLI --work-dir /tmp/opencode/lib7/run
# ② 电气级审计（v1 安装口径 / v2 放置帧归一草案）
$K k2/tools/k2_w8_footprint_audit_v1.py --board <CAND> --proj-lib <WORK>/lib --out-json <W8>.json --out-md <W8>.md
$K k2/docs/drafts/p4-j7b-w8-pose-normalized-v1/w8_audit.draft-v2.py --board <CAND> --proj-lib <WORK>/lib \
      --out-json <W8v2>.json --out-md <W8v2>.md
# ③ 判定（v4 安装件）
$K k2/docs/drafts/p4-j8-v3-measurement-v1/measure_pads_within_outline.py --board <CAND> --json <PADS>.json
python3 k2/docs/drafts/p4-j8-density-clearance-v1/adjudicate.draft-v4.py --board <CAND> \
  --manifest k2/docs/drafts/p4-j8-density-clearance-v1/manifest.k2.v4.yaml --pro $P \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --drc-cli $CLI --drc-work-dir <WD> \
  --w8-audit-json <W8|W8v2>.json --pads-outline-json <PADS>.json --out <VERDICT>.json
```

## 4. ⚠️ **关键发现（判据语义，监理裁定点）**：W-8 未做「放置帧归一」

基线 33 件电气差异**全部为真实 land pattern 差异**（独立等价检查 33/33 物理不同）；重指后仅余 **8 件**，
且 **8/8 物理等价** —— 即被 W-8 v1 误报的**纯约定差异**：

| ref | 面 | `fp_rot` | 误报字段 | 成因 |
|---|---|---|---|---|
| `U6` | F | 90° | `rot`×354 | 板存 pad 朝向为**绝对**、.kicad_mod 存**局部**（FootprintSave 已按 -fp_rot 归一） |
| `C85` | F | 180° | `rot`×2 | 同上 |
| `J3` | F | 180° | `rot`×38 | 同上 |
| `J9` `J11` `J13` | B | 90° | `dy`,`rot` | 背面**镜像**后偏移/朝向按板坐标系存储，与库局部坐标系异号 |
| `J6` `J12` | B | 90° | `dy`,`rot` | 同上 |

**证明方法（独立于 DRC/W-8）**：把库件 `FootprintLoad` 后**按板上位姿放置**（`SetOrientation` /
`SetPosition` / 背面 `Flip`），逐 pad 比**绝对**坐标 + 朝向 + 形状尺寸钻径 ⇒ **59/59 全等**；
同一方法在基线上 ⇒ 33 件**物理不同**（说明该方法不虚）。

⇒ **判据语义提案**（ENG 起草，**未安装、未触 `tools/` 安装件**）：W-8 v2 = 在**放置帧**内比电气几何
（草案 `k2/docs/drafts/p4-j7b-w8-pose-normalized-v1/`，sha256 前16 = `34b83cff5fe8ade7`）。
**正负控**：
- 基线：v2 = **31 + 2**（与 v1 逐件相同 ⇒ **不放松判据**）；
- 落件候选：v2 = **0 + 0**（J-7b ⇒ PASS）；
- **负控**（合成板：C73 pad1 宽度 +0.05mm）：v1 = 9（8 伪 + 1 真）· **v2 = 1（恰命中 C73）** ⇒ 真差异仍被抓。

## 5. 待监理裁定 / 落件前置

1. **⑦ 落件放行**：候选板 `f93a1698adcf4863` + 快照库 24 件 + `fp-lib-table`（**仓库未动**）。
   - **SPEC 前置**：板 sha 变更 ⇒ 须 **SPEC 版本 bump**（pre-commit `check_pcb_spec_correlation` 要求
     `.kicad_pcb` 变更伴随同笔 SPEC 变更）；本器**不代做** SPEC bump（属落件运行手册）。
   - **库内 12 件快照外旧件**（`MCIO_4i_…_RASide`（裸名）/`MCU_STM32G0_QFN32`/`OCuLink_SFF8612`/
     `PI3DBS16412`/`TLV61046_*`×2/`TPD6E05U06_RVZ`/`TPS22919`/`TS3USB221A_UQFN10`/`USB3_TYPEA_90`/
     `USB_A_MUSBR`/`WQFN-64_10x5.5mm_P0.4mm`）**保留未删**，是否清理由监理裁。
2. **W-8 放置帧归一**：采纳 ⇒ `lib_electrical_level` 判 PASS（P4 仅余 `pipeline_present`）；不采纳 ⇒
   该维**维持在册**（差异 8 件均为约定，须监理另定口径）。
3. 沙箱 **`--apply` 全链已实证**（仓外全树副本）：板 → `f93a1698adcf4863`、`pro` 逐字节不变
   （`d5e0ca067a7b585e`）、库 24 件、备份目录生成、落件后 DRC 复跑同。

## 6. 边界（本笔未动）

仓库板 `6ff49da5678c2108` / pro `d5e0ca067a7b585e` / `hw/lib/ForgeOS.pretty`（20 件）/ `hw/fp-lib-table`
`d731638859be9a08` / 冻结件 `d4e81f647be7f980`·`fb07d25ac426ff84` / 真源 yaml / SPEC rev-19..47 / `criteria/`
两份 `897e8bfde60e2cfe`·`7ce08757eff25557` / v2 `7cf8a50eb832c284` / v3 `b77eacb11a261925` / v4 安装件
`004f7ac2666da437` / `tools/k2_w8_footprint_audit_v1.py` `75404d706413d546` **均未改**；未派 WORKER；
临时仅 `/tmp/opencode`。

**旁证（本笔只读发现，未处理）**：`git -C k2 status` 显示 `hw/k2_v4_8L.l5.kicad_pcb` **相对 HEAD 仍是未提交修改**
（HEAD 版 = `37019705ef994ccc` 预复合板，工作树 = 已批准落件的 `6ff49da5678c2108`）；`pm_gate/project.yaml`
与 `SPEC_k2_v4.spec-rev-47.json` 同为未提交/未跟踪 ⇒ **P4 唯一落件板目前只存在于工作树**，`git checkout`
即回退。建议监理裁定是否补一笔提交（ENG 未擅自代提交）。

—— ENG（ARCHER）· 2026-09-18 · 工具 `91c9f5a1138a9825` · 候选板 `f93a1698adcf4863`
