# CO-68 — 【L2 叠层分配】执行方案(a)：铜厚自洽修正 + LID REV6 + SPEC rev-5

> 2026-09-12｜定层 **L2**（CO-67 裁定）｜工具 `tools/p3_v57_co68_option_a_execute_derive.py`
> 记录 `cab5ce0e6cbd5e38`｜LID REV6 `05009687a3f01583`｜SPEC rev-5 `1f351194b3e22b7e`
> 性质：只读冻结源；版本化新文件；`spec-rev-4`/`layer_intent_rev5` **逐字节未动**（before==after 机判）。

## 1. CO-66 修正（铜厚口径）
- CO-66 闭合式 `g4 = 1.6 - 2*h_o - 2*b_s` **未扣铜厚**（0.175mm）；与 CO-55 `copper 0.175 + dielectric 1.425 = 1.6000` 矛盾。
- 修正：**介质预算 = 1.425**，闭合 `2*h_o + 2*b_s + g4 = 1.425`，`g4 >= 0.0764`（1080 单张）。
- 后果：内层带状线**可行线宽上界 ~0.165**（CO-66 表内 0.19/0.205 行实为**不可行**）。扫描见 `scan`。

## 2. 设计点（标准料、铜厚自洽）
叠层 `F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)`；逐层介质：
| 间隙 | mm | 料 |
|---|---|---|
| d(F–In1) | 0.1164 | 2116×1 |
| d(In1–In2) | 0.25 | core 0.25 |
| d(In2–In3) | 0.25 | core 0.25 |
| d(In3–In4) | 0.1922 | 自由余隙（闭合） |
| d(In4–In5) | 0.25 | core 0.25 |
| d(In5–In6) | 0.25 | core 0.25 |
| d(In6–B) | 0.1164 | 2116×1 |

闭合：copper `0.175` + dielectric `1.425` = **1.6**（delta 0.0）⇒ `True`。
线宽：外层 **0.205**（F/B，微带，Z [88.43, 90.61]），内层 **0.16**（In2/In5，对称带状线 b=0.5，Z [84.56, 89.48]），
交付对内中心 {0.5, 0.6} 均落 85±10% ⇒ `True`。

## 3. 版本化产出
- **LID REV6** `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_layer_intent_rev6.json` `05009687a3f01583`：signal = F/In2/**In5**/B；In1/In3/**In6**=GND，In4=P3V3；参考夹心全信号层有参考。
- **SPEC rev-5** `pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-5.json` `1f351194b3e22b7e`：stackup 用途 + `dielectric_8l` + `impedance.per_layer` + `p_width_mm_by_layer`；**数值阈值未改**。

## 4. 下一步（CO-69 起）
引擎 bump（`LAYER_PALETTE` F/In2/In5/B；In6→In5；`F.spec`→rev-5、`F.layer_intent`→rev6、冻结集）
→ G4..G7 全链 → SI 判据按层加权电气长度 → 重新对抗评审。

## 5. 指纹
`spec-rev-4 1c4eecb0edf4a446` 未变｜`layer_intent_rev5 da4c3e4da37c6f94` 未变。
