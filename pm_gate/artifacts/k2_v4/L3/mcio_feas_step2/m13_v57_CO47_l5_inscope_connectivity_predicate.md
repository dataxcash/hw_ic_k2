# CO-47 — 【L2/L3 自裁】L5 施工连通性闭合谓词（在册 68 网 0 未连项）+ 签核退出码修正（L5-DFM.4）

> 2026-09-12｜性质：**签核/验证机制强化**（零几何改动、零阈值放宽）｜无 L1 变更
> 前置：CO-46 `bf7431bc6559ea98`（G5 冻结集校正）｜触发：闸口自查 L5 记录仍存显式「待」（`dft.note = "完整 DFT 规矩待 L5 深化"`）。

## 1. 现象（两处缺陷）
1. `m13_v57_l5_dfm_dft_record.json` 的 `dft` 原只有 `unconnected_items`（348，**全板**计数）+ 一句「待深化」注释：
   属**声明**而非**谓词** —— 无法回答「本阶段在册的 68 条网是否真的连通」，也无法进门禁（宪法第五章第 3 条可验证性）。
2. `tools/p3_v57_l5_signoff.py` 的 `main()` **无条件 `return 0`**：即使 DFM/SI 判定 FAIL，退出码仍为 0 ⇒ 无法作为 CI/监理门禁使用。

## 2. 方法（解析口径，非发明判据）
`kicad-cli pcb drc --format json` 的 `unconnected_items[].items[].description` 无独立 `net` 键，
网名位于描述尾部 `[...]`（例：`F.Cu 上 C88 的焊盘 2 [GND]`）。故：
1. 正则取每子项尾部 `[NET]`；2. 与 `m13_v57_l4_construction.json: nets`（68 条在册施工网）取交集；
3. 谓词：**在册网未连项 = 0**（范围外网不计）。

## 3. 实测（一次性判定的闭合证据）
| 板 | 未连项总数 | 在册网未连 | 范围外网 |
|---|---|---|---|
| 冻结基线 `k2_v4_8L.kicad_pcb` | 416 | **68 个网**（68 条在册网全部未布） | 17 网 |
| L4 施工板 `k2_v4_8L.l4.kicad_pcb` | 348 | **0 个网 / 0 项** | 17 网（GND 492 pins、P3V3 84、NO_CONNECT 52、MCU_VDD 20、PERSTA# 10、P3V3_AUX 8、I2C1_SDA/SCL 4 …） |

⇒ **L4 施工对在册 68 条网 100% 连通**；348 残余全部落在 v57 范围外网（本阶段不布），与 boundary §6.4 声明一致。

## 4. 实施（`tools/p3_v57_l5_signoff.py`，L5-DFM.3 → **L5-DFM.4**）
1. 新增在册连通性谓词，落 `dft.{in_scope_nets, in_scope_unconnected_nets, in_scope_unconnected_items,
   in_scope_violating_nets, unconnected_items_total, rule}`；
2. `dfm.verdict = PASS iff (new_total == 0 且 在册未连项 == 0)`（判据**只增不减**）；
3. `main()` 退出码 = `0 iff (DFM PASS 且 SI PASS) else 1`（修「恒 0」缺陷）；
4. 摘要行增印 `in_scope_unconnected=N/68`。

## 5. 验证（实测）
`../AppDir/usr/bin/python3.11 tools/p3_v57_l5_signoff.py` ⇒
`L5: FAB ok | DFM verdict=PASS new=0 {} | in_scope_unconnected=0/68 nets | SI verdict=PASS skew=0.0031`，**退出码 0**。
指纹：l5_signoff `d1b4c568c65cb20a`｜dfm 记录 `f5a691f4cda234df`（rev L5-DFM.4）；
fab `12d1f3944944550a`、si `a3187aed93c48b6b` **未变**（同板同图）。

## 6. 未改物 / 红线
零几何改动：drawing 仍 `dfa1d7c4a811b0da`、板仍 `4d36212f6492262b`；G4/G5/G6 未触碰；四冻结源未动；无搜索/迭代。

## 7. 备注
本件把 L5 的「待深化」标注转为**可机判谓词**，但**不代表**整板 DFT 已完备：
范围外网（GND/P3V3/低速）布线尚未开始，其 DFT/连通性属后续阶段；本谓词仅覆盖 v57 在册集。
