# CO-84（L2 可审计性 · 回归闸）— DRC 放宽域一致性（dru ↔ 域工件 ↔ 板 rule area ↔ SPEC）

> 日期 2026-09-12｜工具 `tools/p3_v57_co84_dru_domain_gate.py`｜记录 `m13_v57_co84_dru_domain_gate.json` `87cab84cf6c237de`｜boundary **v1.49**

## 1. 为何这是高风险项

`k2_v4_8L.l4.kicad_dru` 把逃逸区铜净距**放宽**到 0.075（SPEC ECN-001）。放宽类规则一旦**作用域过宽**，
就会**掩盖真实违规**；过窄则对已授权的逃逸区误报。故它必须与「授权来源」逐项一致，且可机判。

## 2. 四向一致（本件机判，PASS）

| 项 | SPEC `escape_transition_zone` | 域工件 `co37_escape_domain` | `.kicad_dru` | 板内 rule area |
|---|---|---|---|---|
| 净距 | `escape_clearance_mm` **0.075** | `escape_clearance_mm` **0.075** | `clearance (min 0.075mm)` | — |
| 域集合 | 4 区（ECN-001 授权） | `ESC_J2/J3/J4/U6` | `intersectsArea` 同名 4 区 | 同名 4 个 zone |
| 层 | F.Cu（per-pin vertical escape） | 全部 `F.Cu` | `(layer "F.Cu")` | 全部 `F.Cu` |
| 排除网 | `refclk_isolated=true` | `excluded_nets=["PCIE_REFCLK*"]` | 条件含 `!(A/B.NetName == 'PCIE_REFCLK*')` | — |
| 几何 | — | `rect_mm` ×4 | — | zone bbox **逐值一致**（tol 1e-6） |
| 溯源 | — | 文件 sha256 | 注释引用 sha256 = 实件 | — |

**结论**：净距 0.075、4 个域、F.Cu、REFCLK 排除、引用 sha256、4 个矩形 bbox —— **全部一致，0 失配**。
即 DRC 的放宽范围**恰好等于**被授权的逃逸域，无过宽/过窄。

## 3. 牙齿（4 个定点负控，各命中 1 项）

| 负控 | 篡改 | 实测 |
|---|---|---|
| 作用域过宽 | dru 域集合加 `ESC_XX` | 抓 `area_set` |
| 净距不符 | dru 0.075 → 0.1 | 抓 `clearance_mm` |
| 丢失 REFCLK 排除 | 去掉排除条件 | 抓 `refclk_exclusion` |
| 矩形漂移 | 域工件 `rect_mm` 改值 | 抓 `rect:ESC_J2` |

## 4. 过程中的一次自捕获

首版闸对 4 个域全部报 `rect:*` 失配 —— 实为**我自己的比较口径错**：域工件 `rect_mm` 序为 `[x0,y0,x1,y1]`，
而我构造的板 bbox 序为 `[min_x,max_x,min_y,max_y]`。归一为同序后 0 失配。
若不做该项复核，会把「一致」误报为「不一致」并触发无谓返工。

## 5. 残余

- ① 对间净空 0.875 仍为 **L1**；非执行者 pass 2/2、板厂券仍欠（外部）。
