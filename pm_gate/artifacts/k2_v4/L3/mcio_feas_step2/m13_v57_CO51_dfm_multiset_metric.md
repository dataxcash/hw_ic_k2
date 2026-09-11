# CO-51 — 【L2/L3 自裁】DFM `new` 升级为**多重集差** + 基线消失项机判（消除同类型对调掩盖）

> 2026-09-12｜性质：**签核判据强化**（零几何改动、零阈值放宽、零判定变更）｜无 L1 变更
> 前置：CO-50 `311e98163d49ac82`｜触发：boundary §6.3 记载的最后一项已记录限制；且验收项「无 <0.075 项消失」此前从未机判。

## 1. 现象（两处弱判据）
1. `l5_signoff` 的 `new` 原为 `{k: tl[k]-tb[k] for k in tl}`（**按类型计数差**）⇒ 若某类型"少 1 条 + 多 1 条"
   （同类型对调），`new_total` 仍为 0 ⇒ **掩盖**。
2. 里程碑验收明确要求「**无 <0.075 项消失**」（不得靠移除几何/放宽判据使违规消失），但记录只报 `new`，
   **不报基线中消失的项**，该验收项无法机判。

## 2. 修正（判据只增不减）
在 `dbase`/`dl4` 上各建**多重集**，键 = `(type, tuple(sorted(items[].description)))`（description 含 refdes/pad/net，
是物理参与者的稳定身份；DRC `pos` 为锚点故不用）：
- `_new_ms = cl - cb` ⇒ `new_total = Σ`；`new_items_by_type`；
- `_gone_ms = cb - cl` ⇒ `disappeared_total` / `disappeared_by_type`（**基线消失**，L4=tracks-only ⇒ 须为 0）；
- `dfm.verdict = PASS iff (new_total == 0 且 **disappeared_total == 0** 且 在册未连项 == 0)`；
- DFM 记录 rev `L5-DFM.4 → L5-DFM.5`，新增 `metric` 字段说明口径；G7 记录同步。

## 3. 验证（实测）
`../AppDir/usr/bin/python3.11 tools/p3_v57_l5_signoff.py` ⇒ 退出码 **0**；
`L5: FAB ok | DFM verdict=PASS new=0 (disappeared=0) {} | in_scope_unconnected=0/68 nets | SI verdict=PASS skew=0.0031`。
即：**新增 0、基线消失 0**（42 条 lib/silk 全部在册）、在册网 0/68 未连。连跑两次 4 产出逐字节一致（幂等）。
指纹：l5_signoff `e8ca79f440175b65`｜dfm `de14f887a7819c11`（L5-DFM.5）｜G7 记录 `382fe0df4c05632c`；fab `9a223923b029a1f9`、si `305c237c88762b94` 未变。

## 4. 未改物 / 红线
零几何改动：drawing `dfa1d7c4a811b0da`、板 `cdcb869e9827ec87`；四冻结源未动；无阈值放宽（`.kicad_dru` 未改）。
