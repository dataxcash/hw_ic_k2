# CO-93（L2 自裁 · PDN）— SPEC **rev-10**：PDN 计划坐标按**权威净距**重落（声明式有限 palette）

> 日期 2026-09-12｜工具 `tools/p3_v57_co93_pdn_rev10_derive.py` `86a68999bac123e2`（需 AppDir pcbnew；只读板，写 SPEC rev-10）
> 记录 `m13_v57_co93_pdn_rev10_derive.json` `663cb40e827984dd`｜**SPEC rev-10** `4416e42eed10cb8c`（rev-9 `77f5c54df88bb0ca` 原件未动）｜板 `0e636a67c1472462`（**逐字节不变**）

## 1. L2 裁定（自裁，不升 owner）
依据 LAYOUT_CONSTITUTION 第二章：**via 策略 / PDN 承载属 L2** ⇒ 本件自裁：
1. PDN 计划坐标（`power_pad_connect.entries[].via_pos` / `gnd_stitch_via` / `power_zones[].vias`）**一律按权威口径重落**：
   `required = max(netclass(a), netclass(b), board_min)` + `min_hole_clearance` + **层语义**（共享铜层才互检；支持盲/埋孔；via 亦为障碍）。
2. **无合法位者 ⇒ 显式 `blocked`**（**不放宽任何阈值**；旧坐标退役留存 `retired_superseded_clearance_v1`，禁静默放弃）。
3. **不默认采用 via-in-pad**：那属工艺能力 + SI/PI 证据问题，本件不擅采。
4. pad→via **短段宽度 0.5mm → 声明 0.2mm**（= `.kicad_pro min_track_width` 可制造下限）；短段不合法 ⇒ 该 pad 亦 `blocked`
   （`entries` 语义收紧为「**整条连接合法**」）。
5. 候选 palette（**声明固定、确定性序、无坐标搜索/无迭代**）：原位 → 4 正交点 @(VIA_RO+0.3) → 4 正交点 @0.6。

## 2. 施加（rev-9 → rev-10）
| 项 | rev-9 | rev-10 |
|---|---|---|
| `power_pad_connect` entries / blocked | 223 / 86 | **189 / 120** |
| 板实 pad 决策覆盖 | 309 / 309 | **309 / 309**（不变；blocked 亦是决策） |
| **已连接 pad 数** | 223 | **189（−34，如实登记）** |
| `gnd_stitch_via` | 69 落 / 31 blocked | **40 落（28 原位 + 12 移位）/ 60 blocked** |
| `power_zones[].vias` | 20 | **17（13 原位 + 4 移位）/ 3 blocked** |
| 短段宽度 | 0.5（隐含） | **0.2（声明 `stub_width_mm`）** |
| `pd` 以外变更 | — | **仅 `spec_version`**（`outside_pd_changed_keys=['spec_version']`） |

## 3. 验证（全部机判）
- **CO-91（权威净距闸）对 rev-10 = PASS**：via 246 目标 **0 违规**、短段 189 目标 **0 违规**、牙齿 4/4；`stub_w` 由 SPEC 声明读取。
- **CO-92（修复候选）对 rev-10 = 不动点**：ppc kept 189 / relocated 0 / blocked 0；stitch 40/0/0；zone 17/0/0 ⇒ 声明策略下**自洽且稳定**。
- **全链 G4→G7（rev-10 重基线）**：G4 `FEASIBLE_ALL`（34 页 / crossings 0 / work 546/546 / sha `9c099dd7ba0c3478`）、G5 PASS（G-M1..6、`frozen=True`）、L4 PASS（nets 68 / segs 2523 / vias 252 / viol 0）、L5 FAB ok + **DFM new=0** + **SI skew 0.1300 ≤ 0.15**。
- **回归闸**：co78 / co81 / co84 / co87（3 CLOSED / 2 open 不变）/ co88 / co69（10/10，`18a86c998dd6b4de` 不变）全 PASS。
- **板逐字节 `0e636a67c1472462` 不变**（零几何）。

## 4. 已知限制（新开，如实）
1. **已连接数 223 → 189（−34）**：34 个 pad（多为 U6 0.5mm 球栅场内的电源/地球）在**冻结 8L 通孔工艺 + 声明 palette** 下无合法连接位。
   保持连接数需 **via-in-pad**（需板厂能力 + 工艺证据）或 HDI/微孔（**属 L1：层数/叠层**）⇒ 二者本件均不擅采，登记为待裁。
2. **stitch blocked 31 → 60**：同类处置（现行 SPEC 已有 31 例显式 blocked 的既有惯例）。根因 = `gnd_stitch_gen` 障碍集只取 `layer_plan` **规划段**、不含交付板实际铜 ⇒ v57 布线后漂移。
3. **`_shared` 引擎未改（容器副本只读冻结）**：`pad_connect_gen` 仍会按 legacy 口径生成违规坐标；本件以 **k2 决策层工具**为 rev-10 的生成器。
   引擎侧通用化（含 `gnd_stitch_gen` 障碍集改实际铜 + blocked schema 对齐 `pdn_apply`）登记为后续变更（需解除冻结或改由项目内引擎承载）。
4. **`pdn_apply.py` 短段宽度 0.5 未改**（同因冻结）：施工时须以 SPEC `stub_width_mm` 为准，否则 rev-10 的 stub 判据在施工层不生效。

## 5. 非声明
不改板（逐字节同）、不改阈值（0.875 / 0.15 / 0.075 均未动）、不改历史 SPEC（rev-5..rev-9 原件留存）、不改冻结源；
`blocked` 是**诚实处置**而非 PASS；**不声称 PDN 压降/热已闭合**；不触 L1（拓扑/接口/信号流向/电源域/球重映射均未动）。
**重基线 ⇒ 非执行者复评欠（CO-94）**：本件为 rev-10 的执行者，按纪律不得自评（L2_STRUCTURE_v2.0.md:137）。
