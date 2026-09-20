# K2 · P6 · **K1『声明/实现漂移』系统普查**（D10/D11/D12）

- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K1_BOARD_LEVEL_DEFECT_WORKLIST_20260921_v1.json`（sha16 `0cebbb501a4303f0` · +K1-D10/D11/D12）
- 裁决件：`PENDING_RULINGS_DELTA_20260921_v6.json`（`9bbec1980b359e34`）
- 工具：`k2/docs/drafts/n3-k1-sch-regen-v1/k1_declared_vs_impl_census_v1.py`（可复现）
- 性质：**只读**。未动 `k1/`、`criteria/`、冻结源、交付锚。
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 一句话
系统普查「`k1_board.yaml#devices[*].value/footprint` ↔ 原理图所用 symbol 的 value/footprint」⇒ **11/42 件漂移**；其中 **2 件为本次新发现且此前未登**：**U8（声明 TPS54628 裸 IC vs 实现 6 脚模块）** 与 **R35/R36（声明 10K vs 实现 56K，影响 Type-C CC 电流宣告）**；并归纳出**机制性根因 K1-D12**。

## 1. 普查结果（11/42）
| ref | 声明值 | 实现符号值 | 声明 fp | 实现 fp | 备注 |
|---|---|---|---|---|---|
| J1 | USB_C_RECEPT | USB_C_RECEPT | Amphenol 24-pin | HRO 16-pin | K1-S1 |
| J10 | JST_VH_B2P-VH | J_12V_IN | JST VH | PinHeader_1x02 | K1-S6 |
| U12 | TPS22965 | TPS22919 | DSG WSON-8 | TPS22919 | K1-S4 |
| **U8** | **TPS54628** | **DCDC_12V_5V** | SOIC-8 | SOIC-8 | **K1-D10（新）** |
| **R35/R36** | **10K** | **56K** | R_0402 | R_0402 | **K1-D11（新）** |
| Q1/Q2/R38/R39/U13 | — | （无 placement） | — | — | 缺件（N-3 目标） |

## 2. K1-D10 · U8 声明/实现不符
- 声明：`value=TPS54628`、`function=『…TPS54628, 6A 同步, 650kHz, SO PowerPAD-8』`。
- 实现：symbol `DCDC_12V_5V`（**6 脚** VIN/VOUT/GND/EN/SW/FB，`nc=[SW,FB]`）+ 通用 `SOIC-8`（**无 PowerPAD**）。
- 手册（sha256 `638ae7d8504d9b44…` 与在册同版）：TPS54628 DDA = **8 脚 + EP**：`1 EN · 2 VFB · 3 VREG5 · 4 SS · 5 GND · 6 SW · 7 VBST · 8 VIN`，EP→GND。
- **若按裸 IC 判定，板映射严重不符**：pad `5`=**GND** 却接在 **`PWR_5V_MAIN`** · pad `8`=**VIN** **未接** · pad `1`=EN 未上拉（不使能）· pad `2`=VFB 短地 · pad `4`=SS 接 `12V_IN` · pad `6`=SW 接 `12V_IN`；且**缺 VBST/SS/VREG5 外围**。
- ⇒ **二择一为真**：(a) 实装 TPS54628 ⇒ buck 不工作（含地脚接输出轨）；(b) 实装模块 ⇒ **声明/功能/BOM 与实件不符**。**属选件决策 ⇒ 交监理裁定。**

## 3. K1-D11 · R35/R36 = 10K vs 56K（接口级）
- 声明/生成器：**10K**，且 `PWR_NEW` 明写 *『CC1/CC2 经 R35/R36 (**10K**) Rp 上拉 → **3A 宣告**』*（`PWR_OLD` 为 56K）。
- 实现：symbol **`R_56K`（56K）**。
- Type-C：Rp **10K ⇒ 3A**；**56K ⇒ 默认电流档** ⇒ 与需求冻结不符。

## 4. K1-D12 · 机制性根因（**元缺陷**）
`k1_sch_sync_v1.py` docstring 自述**只写** `k1_board.yaml`/`k1_nets.yaml`；全仓**无工具写 `k1/sch/*.kicad_sch`**（K1-S5）⇒ **每次 ②同步（改 value/footprint）都会静默留下原理图侧陈旧**。
**K1-S1 · K1-S2 · K1-S4 · K1-S6 · K1-D10 · K1-D11 皆此机制的表现。**
修法：K1 引入**同构再生器**（共享 `schlib` 已实测可驱动 K1）+ 把「声明/实现一致」纳入已备的 N-3 验收核。

## 5. 方法学登记
- 普查**只比 value/footprint**，不比电气净表（净表由 `k1_nets.yaml` 覆盖，见 N-3）。
- 先前审计**只比 footprint basename** ⇒ **必然漏掉 R35/R36 这类纯 value 漂移**；本普查补上该维度（这也是 K1-D11 直到本轮才被发现的原因）。
- 手册取件均**先验 sha256 == 在册 `doc_sha256`** 才引用（同版保证）。

## 6. 边界
只读发现；未改 `k1/`；未新增判据维/检查齿；未动 `criteria`/冻结源/交付锚。**U8 选件、R35/R36 修正均须授权（监理自裁，无 owner 闸口；U8 若涉拓扑选件则按 L1 上报）**。
