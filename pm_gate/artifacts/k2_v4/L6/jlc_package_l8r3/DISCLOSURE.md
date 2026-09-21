# K2 P5 交付包 · 具名披露（#K2-36 §三 / #K2-34 §一-7 · §5 / owner #14③）

> 本包不自称"全绿无瑕"。以下为**如实具名**项，随包交付。

## 1. DRC warning 全量披露（**不缩口径**）
在册 canonical DRC（`07_verify` 之外，源 = 册 `drc_violations_clean_workdir.json`）：
**170 条全 warning · error 0 · unconnected 0**（l8 实测；l7 = 167）**，9 类全登记：

| 类 | 条数 |
|---|---|
| missing_courtyard | 54 |
| silk_over_copper | 37 |
| track_not_centered_on_via | 34 |
| lib_footprint_mismatch | 20 |
| silk_overlap | 15 |
| via_dangling | 6 |
| silk_edge_clearance | 2 |
| track_dangling | 1 |
| copper_sliver | 1 |

> **l8 vs l7 差异（如实披露，不缩口径）**：总数 **167 → 170**（+3）—— `track_not_centered_on_via` **33→34**（+1）· `via_dangling` **4→6**（+2）。归因 = 本 rev 之 **4 条 pad→net 变更（U4/2,3 + D1/1,2）**致相关网（`P3V3`/`MCU_VDD`/`GND`/`LED_A`）局部重布、新增 5 过孔与 143 段；**error 仍 0 · unconnected 仍 0 · 类型集不变（9 类）** ⇒ 不影响可制造性判定。

> ⚠ **口径对账**：#K2-36 §三 提及「**23 条恒定 warning**」，该 23 之切分**无法由在库册复现**（册给 170/9 类）。
> 本包**按全量 170 条披露**（粒度更细、不缩口径），并**具名提请监理**确认 23 条的切分依据；若 23 为特定子集，
> 本包披露集为其**超集**，不影响可制造性判定。

## 2. OUT（具名，非本包缺陷）
`U-01` `U-02` `M-15` `F-11` `N-07` + **`U-03` 残项**（`k2_render_3d.py:29` MCIO 硬编码盒 16.0×7.0×4.6）→ **OUT #5 族**（3D 预览 = 证据层，不阻塞可制造性；#K2-36 §二 确认）。

## 3. `F-9` 走廊口径（owner 面另案，不阻 P4/P5）
L2 冻结表 0.25/0.41 与板侧实测口径两套未对账；**板侧口径权威**（#K2-34 §5：阻抗 ΔZ=0 · 制造无影响 · 两容量口径均过）。
冻结件字面更正 = **owner 另案（可选，不阻交付）**。

## 4. `L-1` 具名接受（C4）
`L2/PLACEMENT_SOLUTION_v1.json`（`086d453d23c5fbff`）性质 = **已批准落位之 canonical 捕获、非独立求解**；54 件中
**28 件属「仅板来源」**。**接受该 28 件以板侧坐标为权威来源**用于 P5 打样；**不主张独立推导**；打样件与交付文档**不得隐去**该来源限制。

## 5. 无判据类根闭（P5 须披露，#K2-34 §一-8）
`M-02` `M-14` `F-3` `N-02` `N-03`（载体已修 / 指针转写，替代防复发逐条具名；**≠ C-12**）。

## 5b. P5 出包时新增具名项（本包实测，非 P4 遗留）
1. **阻焊坝 9 处 < 0.09mm**（阈值扫描分布 4∈[0.05,0.06)·1∈[0.06,0.07)·4∈[0.08,0.09)）。JLC 能力表 0.10mm 系**最小可保证桥宽**（非必须存在桥）⇒ 板厂按「无阻焊坝」印制；处置 = **ACCEPT_L2_WITH_FAB_REVIEW**（承 CO-147 R3 先例）；影响面 = 装配焊接注意，**不阻塞 Gerber 可制造性**。**回退修法已实证（本包 `07_verify/mask_accept_fix_proof.json`）**：单参数 `pad_to_mask_clearance` 0.05→0.02mm ⇒ 阻焊坝缺口 **9→0**、总违规回 as-designed 201（无副作用）；该修法 = 改板 setup ⇒ 板 sha 变 ⇒ P4 锚失效 ⇒ **不在 P5 范围**。
2. **F.Cu 最紧真平行耦合段净距 0.2825mm < SPEC 名义窗下界 0.295mm（−4.24%）**（`PCIE_UP3` 逃逸域）。线性化 ΔZ ≈ −0.84% ⇒ **阻抗仍落 85Ω±10%**。**不主张 F.Cu 名义几何窗"全窗"**。
3. **B.Cu 无 as-built PCIE 耦合 run**（43 段 PCIE 走线存在但无成对耦合段）⇒ SPEC 之 B.Cu 行属**对称声明**，as-built 未使用；不影响阻抗判定。
5. **交付件对重铺不变（已验证）**：交付 Gerber 与 `--check-zones` 导出**14/14 逐字节同** ⇒ 存盘 zone fill 即最新（非过期填充），见 `07_verify/zone_refill_invariance.json`。
4. **正面丝印越出板框 4 处**（最大 1.848mm）：H4(fp.text, +1.848mm); R41(fp.text, +1.798mm); D2(fp.text, +1.198mm); C87(fp.text, +0.798mm)。板厂按边框裁剪 ⇒ 位号图例可能缺损（装饰/可追溯性），**不影响可制造性/功能**；**铜层越界 = 0 处**（对照：`pads_within_outline` 0/0/0、copper-edge DRC 违规 0）。修法 = 移丝印文本 ⇒ 改板 ⇒ 另开 rev（本次不做）。见 `07_verify/silk_overhang.json`。

## 6. 锚自检（本包 07_verify/anchor_selfcheck.json）
board `7a5c89913d6e5d0a` · pro `c009058005829f09` · SPEC `f3a48b866983c8db` ·
criteria rev=6（`727d0995…`/`1937a40a…`/`eb3da49f…`）· 冻结四源 `l4 d4e81f64…` 未动。
