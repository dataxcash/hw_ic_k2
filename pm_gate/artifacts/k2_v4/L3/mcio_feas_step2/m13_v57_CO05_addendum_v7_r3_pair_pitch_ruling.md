# CO-05 追加 v7 — R1/R2 耦合收口：**成对落列 pitch=0.6(R3_STEP)** ⇒ W3 FEASIBLE_ALL

> 2026-09-11｜发起：ARCHER（L2/L3 我方可裁决，不上抛 owner）｜性质：根因定位 + 单点修复 + 全链重跑
> ｜结论：**R1/R2 耦合已解**；引擎升 **W3-CN.30**；W3(G4) FEASIBLE_ALL、A-CN.9 独立复算 `0/0/0`、
> 对内 skew **≤0.0574mm**（O4 长度侧保持闭合）；W4(G5)/L4(G6) 已重签 PASS。

## 1. 根因（决定性证据）
成对落列（CO-05b）令 **DN2/input 的 land via** 与 **UP1/out_J2 的 drop via** 相距
`(130.89,57.65)` vs `(131.27,57.93)` = **0.472 < 0.525**（dx=0.38, dy=0.28）。

- 这两点是**逐页固定**的（land=clamp(pad_y+R3_OFF) 与 drop=lane_y+pol_off 均与 pair_row 无关），
  故该页 **全部 24234 条 pair_rows 候选**都被 `_va`(via-via) 否决（探针逐条计数：`va_place=24234/24234`）。
- `phase-2 _best is None` ⇒ 静默回退到**无净距校核的 phase-1** ⇒ 派生出 A-CN.1b（0.40）、
  A-CN.4（`#fcu_pad` 自交）、A-CN.9（vt/tt/vv）。

**更深层**：CO-05c 取 `PAIR_PITCH=0.38`（= STAGGER 最小间距），但
**0.38 < VT_TRACK(0.4525) 且 < VIA_VIA(0.525)**；且 rank 按 band 独立，dn/up 的 k 相同 ⇒ 落列 x 重合。
故 (a) 相邻落列的竖段经过邻页 via（vt 违例）；(b) 异带同 k 落列 via 撞 fence（本次实测）。

## 2. 修复（单点、闭式、零搜索）
**`PAIR_PITCH = 0.6`（= R3_STEP）**；rank 维持按 band 的 (band, P.pad_y, page) 序：

1. 同侧任意两列 ⇒ `Δx = 0.6k ≥ 0.6 > max(VIA_VIA, VT_TRACK)` ⇒ **任意 y 下 vv/vt 自动达标**。
2. 同列仅由配对 (DN_i, UP_i) 共享（dx=0）⇒ 实测 8 对 via-y 集合最小间距 **≥1.74mm > 0.525** ✓。
3. 页内 P/N 落列居 J2 内/外两侧（≥4.35），land/drop 同列同网（豁免）。
4. 对称落列（P 左 / N 右等偏移）保持 O4 长度平衡；残余 run 差 `4.35+2×0.6k (≤12.75mm)`
   仍由 45° 单侧蛇形吸收（Dm ≤ 30.8mm ≤ 可用 run 35.3mm）。

**副修（探针发现，L4 会因此丢 via）**：蛇形分支 node 发射 `_mzp[1:-1]` 丢掉了末点（drop 的 In2 顶点），
导致 collapse 在 drop 处层变无 via ⇒ 32 个 via 丢失。改为 `_mzp[1:]`；修后 construction **256 via**。

## 3. 实测（canonical W3-CN.30，单次确定性运行）
| 项 | 值 |
|---|---|
| verdict | **FEASIBLE_ALL**（A-CN.1a..9 全 PASS，certificates 0）|
| 独立 A-CN.9 复算 | **tt/vt/vv = 0/0/0**（`verify_w3_acn9_independent.py`，自带几何核）|
| 同层 crossing（引擎 A-CN.4）| 0 |
| 对内 skew | **max 0.0574mm**（32/32 ≤0.15）|
| min inter-net via | 0.527898mm（256 via）|
| 序无关 | natural/reverse/hash → **byte-identical**（A1.2 PASS）|

## 4. 指纹
- 引擎 `tools/p3_v57_w3_constructive.py` rev **W3-CN.30**
- main `m13_v57_w3_joint_assignment.json` sha16 **`05f7bd10ab3b45b6`**
- landing `m13_v57_w3_chip_landing_rows.json` sha16 `8fa507a8cc765264`（authority sha == main）
- resource_gate sha16 `9b23c657dd4d72c1`（未变）
- validator `p3_v57_w3_constructive_validator_v2.py` rev **W3-VALv2.3**（R3 重导纳入成对落列契约）

## 5. 红线
冻结四源未改（`0bd52ed4/a8ef3ea8/fb07d25a/0a459839`）；单次运行（非扫描）；**未放宽** `intra_pair_skew_mm`；
探针仅落 `/tmp/o4study/`。**G7(O4 对内等长) 由本次收口**；G7 剩余阻塞见 **CO-06**（DFM 模型缺口）。
