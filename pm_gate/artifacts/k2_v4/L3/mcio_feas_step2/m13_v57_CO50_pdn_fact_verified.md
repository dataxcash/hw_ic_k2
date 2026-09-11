# CO-50 — 【L2 PDN 自裁】PI/PDN 记录事实化 + 机器核验（平面层为**保留层、尚未铺铜**）

> 2026-09-12｜性质：**签核记录事实性修复 + PDN 核验谓词化**（零几何改动、零判定变更）｜无 L1 变更
> 前置：CO-49 `6c27149fff749a1d`｜触发：写/复核 PI 记录时核对"平面"事实。

## 1. 现象（原记录不实且不可机判）
`m13_v57_l5_si_pi_emc_record.json` 的 PI 原为：
`"planes_present": bool(plane_layers)`（**仅由层名推出**）与
`"pdn_planes_untouched": "frozen board zones unmodified (L4 adds tracks only)"`（**断言字符串**）。
读者会据此认为"PDN 平面存在且已受核验"。实测（`pcbnew.LoadBoard` 统计）：
| 板 | zone 总数 | 铜铺铜 zone | 非铜 rule area |
|---|---|---|---|
| 冻结源 `k2_v4_8L.kicad_pcb` | **0** | **0** | 0 |
| L4 板 `k2_v4_8L.l4.kicad_pcb` | 4 | **0** | 4（`ESC_J2/J3/J4/U6`）|

⇒ 板内**不存在任何平面铺铜铜**：In1/In3/In5(In4) 只是 LID.1 的**保留层**；PDN 铺铜属后续阶段（phase3_plan WP2）。
故"平面未动"在字面上成立但**空真**，且 incapable 机判 ⇒ 违宪法第五章（可追溯/可验证）与"不得 partial pass / 不得夸大"。

## 2. 修正（L5 记录；不改板/图）
1. 新增 `_zone_stats(board)`：按 `GetIsRuleArea()` 区分**铜铺铜**与**非铜 rule area**，并记 `pour_layers`；
2. PI 改为事实 + 谓词：
   - `zone_counts = {"frozen_src": …, "l4": …}`（上表机器可复算）；
   - `pdn_status ∈ {"reserved_not_poured", "poured"}`（实测 = **reserved_not_poured**）；
   - `pdn_plane_copper_untouched = (frozen.copper_pour == 0 and l4.copper_pour == 0)`（= **true**，机器判定）；
   - `pdn_note`：明确"平面层为保留层、铺铜属后续阶段；L4 仅新增 4 非铜 rule area + tracks"。
3. SI/PI/EMC 记录 rev `L5-SI.2 → L5-SI.3`；G7 记录（自动重生成）同步该事实。

## 3. 验证（实测）
- `../AppDir/usr/bin/python3.11 tools/p3_v57_l5_signoff.py` ⇒ 退出码 **0**，
  `FAB ok | DFM PASS new=0 | 在册 0/68 | SI PASS skew 0.0031`（**判定全部不变**）；连跑两次 4 产出逐字节一致（幂等）。
- 指纹：l5_signoff `7b13e668d5d96a23`｜si `305c237c88762b94`（L5-SI.3）｜G7 记录 `ad1b7a174f914914`；fab `9a223923b029a1f9`、dfm `f5a691f4cda234df` 未变。

## 4. 未改物 / 红线
零几何改动：drawing `dfa1d7c4a811b0da`、板 `cdcb869e9827ec87`；四冻结源未动；无阈值/判定变更（PDN 未铺铜属阶段范围，不是缺陷）。
