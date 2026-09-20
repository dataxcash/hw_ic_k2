# K2 · P6 跨板复用（造活）：**K1 板级缺陷工作清单**（2026-09-21 · 监理自动续推轮）

**性质**：只读工作清单**提案**（供 K1 项目排期）。**未动 `k1/`**；**不新增判据维/检查齿**（owner ②）。
**读数来源**：ENG 本会话直跑 `criteria/adjudicate.py --project k1`（`drc.json` 逐条读出）+ pcbnew-free 解析交叉复核。

## 0. K1 板基线事实
板框 **80×38**（原点 0,0）· 42 器件 · 306 pad · PTH **28** / NPTH **2** · 铜区 **0** / keepout **0** · 走线 **0**（未布线）
DRC：**error 13 / warning 17**（clearance 1 · shorting_items 2 · pth_inside_courtyard 4 · copper_edge_clearance 3 · solder_mask_bridge 3 · silk_edge_clearance 3 · nonmirrored_text_on_back_layer 14）
未连接项 **156**（51 网 / 42 器件）

## 1. 工作清单（按优先级）
| # | 级别 | 项 | 具名读数 | K2 判据映射 | 修法族 |
|---|---|---|---|---|---|
| **K1-D2** | **高** | J13 pad4(`MCU_VDD`) 与 U1 pad31/32 实质短路 | `shorting_items` 2：**MCU_VDD↔SBU_SEL**（J13 pad4 @8.81,8.0 ↔ U1 pad31 @9.3,8.75）· **MCU_VDD↔SWCLK_BOOT0**（↔ U1 pad32 @9.3,8.25）；同址另 2× mask bridge | **J-1** | J13 移位 / U1 移位·旋转（placement）——**电气级，必功能失败** |
| **K1-D1** | **高** | J1（换装 Amphenol 24-pin 后）SH/NPTH 焊盘压板左边框 | `copper_edge_clearance` 3：NPTH(@1.2,23.36) **0.2692** · SH(@0.67,22.11) **0.2700** · SH(@0.31,16.16) **0.0000** mm（要求 ≥0.30）；`pads_within_outline` 2 pad（`J1`/`SH`，AABB x∈[−0.03,1.37]） | **J-8**（K2 同族已 0/0/0） | J1 向板内移位（OPEN-1 换件后**落位未复算**） |
| **K1-D3** | 高 | J6 pad1 与 U1 pad17 铜间距 0.0000mm | `clearance` 1：J6 pad1 `PWR_CTRL_OUT`(@14.53,13.0) ↔ U1 pad17 `<no net>`(@13.75,12.7)；同址 1× mask bridge | **J-1** | J6 移位；并核实 pad17 no-net 归属（输入面） |
| **K1-D4** | 中 | J9 全部 4 个 PTH 落在 J1 courtyard 内 | `pth_inside_courtyard` 4：J9 pad1..4 (@1.19/3.73/6.27/8.81, y=13.0) | **J-8** | J9 移位 / J1 courtyard 核正 |
| K1-D7 | 中 | 固定孔不足 + 无铺铜/回避区 | NPTH **2** < 4 · zones **0** · keepout **0**（K2 对照：4×Ø3.2 · 10 filled · 8 keepout） | **J-8** + 缺陷册 **M-11**/**M-05** | K1 板级设计推进（可直接参照 K2 判据值） |
| K1-D6 | 信息 | 17 条 warning | silk_edge_clearance 3 · nonmirrored_text_on_back_layer 14 —— **K1 manifest 已登记** ⇒ 判据维 PASS | **J-1** | 登记制、不豁免、保持可见（现状合规） |
| ~~K1-D5~~ | **非缺陷** | 156 条未连接项（51 网/42 器件；GND 100 · P3V3_AUX 26 · VBUS 22 · MCU_VDD 18 · PWR_5V_MAIN 14 …） | `unconnected_items` 156 | **J-2** | **计划 §1.3 #7：K1 未布线状态本身不是缺陷** ⇒ 属 K1 布线推进，不计入机制包 |

## 2. 与已交机制包的关系
- **机制类**（模板/门禁/接线）= 已提案并**镜像实测**：`K1_MECHANISM_COVERAGE_BUNDLE_PROPOSAL_v1.json`（3 件 ⇒ n_pass **5→8**，0 副作用）。
- **输入/来源类** = 已提案：`K1_SOURCE_RECONCILIATION_AND_SCH_SIDE_RESIDUAL_20260921_v1.json`（原理图侧缺 5 件 + J1/U10 footprint 陈旧）。
- **本件 = 板级类**（placement/设计推进）：**6 项开放**，最高优先 **K1-D2 · K1-D1 · K1-D3**。

## 3. 边界
只读清单；修法均属 K1 项目改动（placement/板级设计）⇒ 需 K1 授权；本件未动 k1 任何文件，未新增检查齿。

## 4. 交件
`K1_BOARD_LEVEL_DEFECT_WORKLIST_20260921_v1.json`（`3360e838db2be5e2`）
