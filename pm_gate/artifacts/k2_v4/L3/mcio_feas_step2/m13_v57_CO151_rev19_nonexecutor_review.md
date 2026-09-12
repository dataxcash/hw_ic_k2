# CO-151 — rev-19 非执行者对抗复评（独立重算/反证）

- 复评人：非执行者会话（z26；未参与 CO-142..150 施加；context 隔离）｜board `d4e81f647be7f980`｜SPEC `5f72182a2616392c`
- **verdict：PASS_WITH_FINDINGS**（findings 8）｜只读（除自身记录）

## 独立确认（逐项重算，不复用执行者断言）
- CO-146 阻抗双模型逐值复现（≤0.02Ω）；PDN 四轨 ΔV% 漂移 ≤0.0001%
- CO-146 DFM：自跑 DRC as-designed 42 / JLC 下限 43（solder_mask_bridge=1）；阻焊几何 0.0694 <0.09（回退 0.1004≥0.09）
- CO-146/147 过孔：自数 493 支 / 非通孔 220（0.05 与 DFM 表逐型一致）
- CO-147 R3 阻焊 FAIL；R1 盲埋孔『Not supported』出处 sha256 7d1d5a9193f3c212 ✓
- CO-148/149 热：手册解析 PACT=[4.7, 6.0]/[5.8, 7.0]、θJA=17.4、TJmax=120.0 ⇒ Tj 最劣 161.8°C > 120 ⇒ FAIL 成立
- CO-150 K9 两域本件自建 3 负控全触发、现行台账 0 findings（牙齿非空过）
- co120 豁免 10 条中 9 条确为陈旧（非空过）；名义多余 1 条（见 F-7）

## findings

| id | sev | kind | 内容 | 修法 |
|---|---|---|---|---|
| F-1 | low | doc/reproducibility | §6 记录 pin 为**时序快照**（记录内嵌下游 sha/状态计数）：按 §6 复现得**另一稳定不动点**，co124/co147/co148/co150 四条记录 pin 不可由 §6 复现（登记簿/台账 pin 可复现）；且 co148 重跑把 2 条已闭登记项重开（OPEN 0→2）。 | ① §6 标注「记录 pin = 时点快照，非复现目标」并给出时序；② 移交执行 CO：记录内嵌下游快照去留（登记簿 item 13 同族）。③ 复核 co120 是否需为这 4 条的 `sha16` 字段补 EXEMPT（现闸仅扫 `*_record` 键，不覆盖 → 见 F-1b） |
| F-1b | low | gate-coverage | co120 P1 正则仅抽 `"<x>_record"` 键 ⇒ 记录内 `register_sha16`/`sha16_after`/`sha16` 类**下游快照字段不在闸覆盖内**（CO-108/114 F-6 的另一半）；本件 4 条即为实例。 | co120 P1 增补白名单字段（或显式声明「非 *_record 快照不受闸管」并登记理由）。 |
| F-2 | medium | record-errata | CO-147 R2 `facts.as_built_edge_mm`=0.3294 非最劣值：本板 F.Cu 平行(≤10°)异对全量最小铜边=0.2577mm（中心 0.4627），欠 2w 达 0.1523mm；0.3294 系 CO-134 单值口径，已被 CO-141 判 UNDER_REPORTED。裁定结论（接口固有 ⇒ ACCEPT_L2）不受影响，但 R2 引文与其所引证据链（CO-141/142）自相矛盾。 | R2 facts 改列最劣 0.2577（另注 J2 侧最劣 0.2871）；doc + 记录 + boundary 同批重基线。 |
| F-3 | low | record-errata | CO-147 R3 `not_done_why` 称『0.0065mm 量级边际差距』，与其本件 `facts.shortfall_mm`=0.0205 差 3.2×（本件独立复算 shortfall=0.0205 ✓）。仅叙述，处置（ACCEPT_WITH_FAB_REVIEW）不变。 | 『0.0065mm』→『0.0205mm』。 |
| F-4 | low | advisory | CO-149 板侧路线以**表征参数 ψJB=5.9**作加性热阻；若改用同表**热阻 RθJB=6.1**，所需 h 由 [8.15, 16.38] 抬到 [8.29, 16.99]（+3.39%），θJA_eff 17.22→17.42（与手册 θJA=17.4 反而更贴合）。『两路线互校差 1.0%』因复用手册自身 ψJB + 声明 h，**非独立证据**。另：O0（自然对流）覆盖 0/4 对声明 h=8.0 敏感——h=8.5 时覆盖 1/4。结论（须系统散热）不变。 | 补 h/ψJB↔RθJB 敏感度行 + 把『互校』改称『一致性核对』。 |
| F-5 | low | advisory | CO-146 PDN `n_plane_vias` 实为**全网 via 计数**（P3V3 41、P3V3_AUX 12）而非 zone 内净匹配（本件实算 35/5）；口径未声明。因 R_plane 主导，ΔV% 影响 <0.02%（绝对），四轨 PASS 不变。 | 口径显式声明（或改用 zone 内计数 + 保守侧）。 |
| F-6 | info | advisory | CO-146 阻抗『两套独立闭式交叉核对』：M1 即 SPEC `dielectric_8l_basis.model` 同式同输入 ⇒ **非独立**（等价于复现 SPEC 一阶），真正独立第二模型仅 M2；结论（as-built ±10% PASS + 名义最宽 gap watch）仍成立（本件双模型逐值复现，差 ≤0.02Ω）。 | 标签改『一阶复现 + 单一独立模型交叉核对』。 |
| F-7 | info | registry-hygiene | co120 EXEMPT 注册表声明 10 条，闸记录 `n_exempt_historical`=9：`co110:co109_record` 的 pin 现与目标**相等**（不再陈旧）⇒ 该条为**多余登记**（清单虚高 1）。另 co111/co118 两条（登记簿 item 13 点名复核）无板级机判佐证，仅靠自由文本理由（本件佐证其 pin 确陈旧且与现引值一致 ⇒ 判**充分**）。 | 删/收紧 `co110:co109_record`；为 co111/co118 补可机判依据（如现引记录 sha 对应板/时点）。 |

## 牙齿

- `A_invariants`：{"t01_all_frozen": true, "t02_delivered_pinned": true, "t03_negative_control_detects": true}
- `B_interpair_3w`：{"t01_negative_control_catches_violation": true, "t02_nonempty_pairs": true}
- `C_impedance`：{"t01_overwide_leaves_window": true, "z_overwide": 64.06}
- `D_pdn`：{"t01_x10_current_exceeds_budget": true, "x10_pct": 6.927, "t02_within_1pct_of_record": true}
- `E_dfm_via`：{"t01_mask_below_min": true, "t02_fallback_covers": true, "t03_jlc_run_isolates_mask": true}
- `F_thermal`：{"t01_worst_over_limit": true, "t02_zero_power_passes": true, "t03_h_sensitivity_flips_nat_coverage": true}
- `G_k9_teeth`：{"neg_no_option_covers": true, "neg_asbuilt_undeclared": true, "neg_drop_over_budget": true, "pos_live_clean": true}
- `H_co120_exemption`：{"t01_nonempty": true, "t02_nonvacuous": true, "t03_basis_text_present": true}
- `I_reproduction`：{"t01_all_four_embed": true}

End of CO-151（rev-19 复评；独立重算全部复现，findings 8）。

