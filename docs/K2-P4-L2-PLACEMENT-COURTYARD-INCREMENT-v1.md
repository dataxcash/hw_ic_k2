# K2 · P4 · ⑥ **L2 placement 增量 + 40 件 courtyard 补全** · v1 · 2026-09-17

> 依据：handoff `.omo/handoffs/k2-p4-handoff-20260917-inc36-ctxlimit.md` §3（唯一 ENG 项）+ 登记册
> `K2-P4-COURTYARD-AND-LIB-REGISTER-v1.md`（`23206b83fccc43e3`）§2。
> 对象 = 落件板 `k2/hw/k2_v4_8L.l5.kicad_pcb` **`6ff49da5678c2108`**；产出 = **候选板（未落仓库；落板归监理）**。
> 判据只读：本件不含判定。冻结件（`d4e81f647be7f980` / `fb07d25ac426ff84` / 真源 yaml / SPEC / `criteria/` 两份
> `897e8bfde60e2cfe`·`7ce08757eff25557`）**未动**；未改 pro；未派 WORKER；临时仅 `/tmp/opencode`。

## 0. 一句话结论

**移 3 件（`D2`/`L1`/`U4`）+ 补 40 件 `CrtYd`** ⇒ 候选板 DRC = **error 0 · warning 仅剩 `lib_footprint_mismatch` 35 ·
`unconnected` 0 · `missing_courtyard` 0 · `courtyards_overlap` 0 · 非 45° 0**，8 项守恒闸逐项复算全过。
候选板 `b2cfb087839afd73`（**两次独立复跑逐字节相同**，`cmp` IDENTICAL）。

## 1. 动作（全部 L2，自裁勿停）

| # | 件 | 动作 | 依据 |
|---|---|---|---|
| 1 | `D2` | `(38.700,34.600) → (39.100,34.600)`（**+x 0.40**，0 rewiring：原 2 段端点仍落在新盘内） | 解 `U4↔D2` + `D2↔U2` |
| 2 | `L1` | `(33.000,40.200) → (33.000,40.500)`（**+y 0.30**，0 rewiring） | 解 `L1↔U2` |
| 3 | `U4` | `(40.000,37.000) → (40.000,37.950)`（**+y 0.95**） | 解 `U4↔D2` |
| 4 | `U4.pad3`(P3V3) | 补 **2 段 0/90°**（0.2mm）：`(40.0,37.0)→(40.0,35.98)`、`(40.0,35.98)→(40.264,35.98)` | 保连接；非 45° = 0 |
| 5 | `U4.pad2`(MCU_VDD) | **删 1 段冗余旧桩** `(40.95,37.95)→(40.95,38.775)` | 新盘已直接覆盖 via ⇒ 消 `track_dangling` |
| 6 | **40 件无 `CrtYd` 封装** | **Add-only** 按面补 `CrtYd`（F 面 35 / B 面 5）；`margin = min(KLC 0.25, 该件最大可用外扩)` | ⑥；禁 `RemoveNative`（T-37） |

- **件移动方向判据**：`D2` 不能北移（板框上边 `y=33.00` + 铜边距 0.30 ⇒ 盘顶下限 `y=33.30`，北移上限仅 0.45mm，不足以解 `U4↔D2`）；
  故 `U4` 必须南移，`D2` 东移解 `U2`（其 `+x` 上限 0.85mm 由 `P3V3` 走线/`via@43.1` 铜距定，取 0.40 留余量）。
- 补件 margin 实测：**36 件 = 0.25（KLC nominal）**；空间不足取最大可用外扩 **4 件**：
  `C80 = 0.205`、`C83 = 0.075`、`R32 = 0.05`、`R34 = 0.05`（其余 36 件 0.25；无一件落在 `margin 0`）。

## 2. ⚠️ 关键发现：登记册 §2 的「4 对碰撞」含**跨面伪对**，真集为 **9 对（0.25）/ 2 对（margin 0）**

- 登记册 §2 以 AABB/多边形实测，**未区分器件面（F/B）** ⇒ 把 `J9(B)↔U1(F)`（及 `J13(B)↔U1(F)`）计为碰撞对。
- **KiCad 实测（`kicad-cli 10.0.5` DRC，40 件全补）**：`courtyards_overlap` **不跨面比较**（F.CrtYd 只与 F.CrtYd、B 只与 B）：
  - 正控：`margin 0.25` 全补 ⇒ **`courtyards_overlap` 恰 9 对，无 `J9`/`J13`/`U1` 参与**（`U1(F)` 与 B 面排针不同面）。
  - `margin 0` 全补 ⇒ 余 **2 对**：`U4↔D2`、`D2↔U2`（7 对可由外扩收缩消解）。
- ⇒ **`J9` 无需移动、B 面 `P3V3_AUX`/`I2C2_SDA` 走线无需重排**（登记册 §2 的「J9 y+1.6~2.5mm + 重接 4 网」在本板**非必要**；
  且 DRC 实测：J9 南移 >0.24mm 即与 `P3V3_AUX @y=57.246` 冲突 ⇒ 该路线本会引入风险）。
- ⇒ **L2 最小集 = 动 3 件**（`D2`/`L1`/`U4`），非登记册所列含 `J9` 的 4 件。真冲突集（margin 0.25）：
  `U4↔D2` · `D2↔U2` · `L1↔U2`（3 对由移件解）+ `U6↔C80` · `C79↔C83` · `R42↔C83` · `R31↔R32` · `R33↔R32` · `R33↔R34`（6 对由外扩收缩解）。

## 3. 硬闸复算（落件板 → 候选板；逐项）

| 闸 | 口径 | 实测 | 判 |
|---|---|---|---|
| DRC error | severity-all | **0** | PASS |
| DRC warning | severity-all | `lib_footprint_mismatch` 35（登记在案，⑦ 库侧待裁）；`missing_courtyard` **40 → 0** | PASS |
| `unconnected` | 引擎 `unconnected_items` | **0**（前 0） | PASS |
| `missing_courtyard` | DRC | **0**（前 40） | PASS |
| `courtyards_overlap` | DRC | **0**（全补 margin≥0 后） | PASS |
| 非 45° | 全板段角度（容差 2µm） | **0 / 4722**（前 0/4721；新增 2 段皆 0/90°） | PASS |
| 出框 P3-4 | 8 件接口焊盘 ⊆ 板框内缩 0.3mm | **0 出框**（框 `[23.30,33.30,142.70,78.70]`） | PASS |
| `column_x` | 5 排针列 `J6/J9/J11/J12/J13` `x=27.94` | **全 27.94，未动** | PASS |
| 走廊（P3-5/C5b） | 8 个 keepout 区各 ≥1 开关非 allowed | 未动；8/8 有效（草案判定器 `keepout_active` PASS） | PASS |
| 等长 / `85Ω±10%` | `PCIe85` 网段/via 集合 | **逐字节集合相同**（段 3653 / via 252，未增未减未改） | PASS |
| 过孔策略 | via 总数/参数 | **711 → 711**（未增未减） | PASS |
| 冗余删除登记 | 改既有铜 | 删 1 段（`U4.pad2` 旧桩，网 `MCU_VDD`，长 0.825mm，uuid `c24b2ff9`） | 登记 |

## 4. 判据侧（只读对照，判定归监理）

- **冻结判定器** `criteria/adjudicate.py` `897e8bfde60e2cfe`：候选板 **PASS 7 / FAIL 3**（FAIL 集与落件板**相同**：
  `zone_filled` 10/18 · `refdes_sets_equal`（H1–H4）· `pipeline_present`）⇒ 本增量未引入回归。
- **判据草案 v2** `7cf8a50eb832c284`：候选板 **14 PASS / 2 FAIL**（FAIL 集与落件板相同：`pipeline_present`〔gate 安装项〕·
  `lib_electrical_level`〔⑦ 库侧重建路线，待监理裁定〕）；其中 `drc_errors = 0`、`drc_warning_dispositions` 仅余 1 类
  （`lib_footprint_mismatch`）、`unconnected_zero` PASS。

## 5. 复跑链（确定性；`/tmp` 易失须重建）

```bash
cd /home/fila/jqdDev_2025/ic_hw
C=k2/hw/k2_v4_8L.l5.kicad_pcb; P=k2/hw/k2_v4_8L.l5.kicad_pro; CLI=AppDir/bin/kicad-cli
# ⑥ 干跑（期望候选板 b2cfb087839afd73；两次复跑 cmp IDENTICAL）
AppDir/usr/bin/python3.11 k2/tools/k2_p4_l2_placement_courtyard_v1.py \
  --board $C --pro $P --kicad-cli $CLI --work-dir /tmp/opencode/l2/run2
# 判据（监理权，只读对照）
python3 criteria/adjudicate.py --board /tmp/opencode/l2/run2/k2_v4_8L.l5.l2-placed.kicad_pcb \
  --manifest criteria/manifest.k2.yaml --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --pro $P
```

工具 `k2/tools/k2_p4_l2_placement_courtyard_v1.py` **`3de81e5a7f24ceff`**（新增；T-38 种子 `20260918`；T-41 双旗标；
T-22 备份 + 落板后 pro 逐字节校验）· 候选板 `b2cfb087839afd73` · 报告
`/tmp/opencode/l2/run2/l2_placement_report.json` `6b38e2e815e56ae4` · W-8 审计 `fb5b2bf168b9e5c8`。

## 6. 落板请求（**待监理放行**；ENG 未落仓库）

| 项 | 值 |
|---|---|
| 目标 | `k2/hw/k2_v4_8L.l5.kicad_pcb`（现 `6ff49da5678c2108` → 期望 **`b2cfb087839afd73`**） |
| pro | `k2/hw/k2_v4_8L.l5.kicad_pro` **`d5e0ca067a7b585e` 不变**（T-22 已由工具强校验） |
| 命令 | `… k2_p4_l2_placement_courtyard_v1.py --board $C --pro $P --kicad-cli $CLI --work-dir <wd> --apply --confirm-repo-write` |
| 性质 | **Add-only courtyard + 3 件位移 + 2 段短线 + 1 段冗余删除**；0 error / 0 unconnected / 0 overlap / 0 missing |

## 7. 边界

未改：冻结四源 · `criteria/` 两份 · SPEC rev-47 原件 · 真源 yaml · `k2/tools/k2_jlc_template.kicad_pro`（同含 9 条 ignore，属计划 §P6）·
仓库板/pro（保持 `6ff49da5678c2108` / `d5e0ca067a7b585e`）· 生成器。未派 WORKER；临时仅 `/tmp/opencode`。
**fail-closed 不变**：P4 未全绿不下单、不出交付 Gerber；P5 在 P4 关门后才开。

—— ENG（ARCHER）· 2026-09-17
