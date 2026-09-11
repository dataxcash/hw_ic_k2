# CO-56 — 【L2/SI 自裁】SPEC ECO **rev-4** 落地 + 全链复跑（几何不变性证明 / 不动点 / 新基线指纹）

> 2026-09-12｜定层 **L2/SI**（LAYOUT_CONSTITUTION 第二章：叠层分配 + SI 物理承载 + 记录；**无 owner 闸口**）
> 依据：CO-55 裁定（`m13_v57_CO55_layer_aware_impedance_build_ruling.md`）+ 监理自动续推。触发条件：CO-55 §4 R4 的"ECO rev-4 内容（本次不落盘）"。
> 性质：**加性 ECO 发射 + 冻结集同步 + 全链复跑验证**。不删/不改任何历史件；不伪造 sign-off。

## 1. ECO 增量（**纯加性**；发射器 `tools/p3_v57_co56_emit_spec_rev4.py`）

| # | 字段 | 变更 | 影响 |
|---|---|---|---|
| D1 | `spec_version` | `1.1.spec-rev-3` → **`1.1.spec-rev-4`** | 版本 |
| D2 | `stackup.material` | 更新为 **8L 声明**（JLC08161H / NP-155F / 2116×1 + 3313×1 + core 0.36×2）；旧 6L 串移入 `material_legacy_6l` | 仅声明 |
| D3 | `stackup.total_thickness_mm` / `stackup.dielectric_8l`(+basis) | **新增**：CO-55 反解逐层介质表（1.6mm 闭合 delta=0.000） | 仅声明（`.Cu` 键未动 ⇒ 引擎 `stackup_layers` 不变） |
| D4 | `impedance.per_layer` + `gap_mm_semantics` | **新增**：F.cu 微带 / In2.cu 带状线 / In6.cu 单参考 的分层口径；`gap_mm` 语义 = 下限 | 原标量 `target_zdiff/model/width_mm/gap_mm` 全保留 ⇒ 消费方兼容 |
| D5 | `net_classes.PCIe85.diff_pair` | **新增** `p_gap_semantics="lower_bound"` / `p_gap_geometry_mm_delivered=0.295` / `p_gap_geometry_source`；另加 `inter_pair_spacing_scope` | **数值未改**（p_gap 0.175 / p_width 0.205 / inter_pair 0.875） |
| D6 | `_spec_rev_4` | **新增**溯源块（card/工具级引用，变更清单、unchanged、回退） | 溯源 |

**未改**：所有数值阈值（`net_classes.PCIe85.*`、`impedance.target_zdiff/width_mm/gap_mm`、`vias.*`、`constraints.*`）、`corridors`（含 `tracks_y`=1.20，与交付网格一致）、`layer_plan`、`pd`、`board`、`components`；`SPEC_k2_v4.json` / `spec-rev-2` / **`spec-rev-3` 逐字节未动**。

**去环纪律（本轮教训）**：rev-4 **只引用 card 级标识与工具名，不引用任何下游工件 sha**（曾试引 audit json sha ⇒ 与 audit 内嵌 spec sha 形成 2-环；已改）。⇒ 依赖图为 DAG：`rev-4 → 引擎/记录 → audit → requirement`，可重复复跑而收敛。

## 2. 几何不变性证明（ECO 的"零几何影响"断言，机判）

对 W3-CN.40（`dfa1d7c4a811b0da`，git 内）与 rev-4 下的新图纸逐键比对：

- **逐字节相同**：`route_geometry`、`pages`、`decision_contract`、`contract`、`layers`、`method`、`gate_status`、`verdict`。
- **仅不同**：`frozen_sha_check.actual.spec` 与 `inputs_sha.spec`（图纸内嵌输入指纹，属引用而非几何）。
- ⇒ 图纸文本 sha 由 `dfa1d7c4a811b0da` 变为 **`4e7497daf97cebd1`**（**仅指纹重基线**）；**L4 板逐字节不变** `cdcb869e9827ec87`（2441 段 / 252 via / 68 网）。

## 3. 全链复跑（rev-4 下实测）

| 门 | 判定 | 证据（sha16） |
|---|---|---|
| G4/W3 | **PASS（FEASIBLE_ALL，34 页，crossings 0，work 546/546）** | 图纸 **`4e7497daf97cebd1`**；landing `54c44b6a5aa54f40` |
| G5/W4 | **PASS**（G-M1..6 True、A1.2/1.3/1.4 True、**frozen=True**） | `m13_v57_w3_validation.json` `95ec1af12f6edae3` |
| G6/L4 | **PASS**（L4-A..F True、viol 0；板**逐字节不变**） | 板 `cdcb869e9827ec87`；l4val `b15c6432a3da3e39`；l4constr `758314dc01814701` |
| G7/L5 | **PASS**（DFM new=0 / disappeared=0；在册未连 **0/68**；SI skew 0.0031） | fab `cc20edd45406db6b`；dfm `de14f887a7819c11`；**si `12bab1f0152b5e0e`（rev L5-SI.5）**；G7 `38c63392b29459d5` |

L5-SI.5 记录已换轨：`netclass_geometry.conformance = DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON`、`p_gap_semantics = lower_bound`、
`per_layer_impedance` 与 `stackup_build` 直接引用 rev-4 的 `impedance.per_layer` / `stackup.dielectric_8l`。

## 4. 不动点验证（零漂移）

在 rev-4 定稿后，**完整重跑** G4→G5→G6→G7 + CO-54 audit：

```
重跑前 sha16 == 重跑后 sha16   （w3 图纸 / w3 validation / l4_construction / si / g7 / audit 六件）
board 重跑后仍 = cdcb869e9827ec87
```
⇒ 新基线是**不动点**（重跑零 tracked 漂移），与本仓"全链字节可复现"（CO-49）口径一致。

## 5. 收口结论

1. **CO-53/CO-54/CO-55 的阻抗几何项**：由"输入缺口 + NOT_DEMONSTRATED"→ **`DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON`**（一阶：F 88.4–91.2Ω / In2 82.1–89.2Ω / In6 85.5–87.4Ω，全部落 85Ω±10%）；SPEC 现已携带所需 8L 叠层表与分层口径。
2. **残余（如实声明，不在本 ECO 内关闭）**：
   - **对间串扰**：交付对间最小铜边 0.345（In6 长平行带）vs 基线 0.875 ⇒ 需领域求解器/板厂券复核（已写入 `net_classes.PCIe85.inter_pair_spacing_scope`；CO-54 F2/F3）。
   - **B.Cu 非阻抗控制层**（参考层为 In6 信号层）⇒ 其不得承载阻抗关键网；In6 下方 B.Cu 不得并行铺铜/走线。
   - **板厂券**：叠层与阻抗的最终确认（SPEC `coupon_required=true` 既有路径）。
3. **回退**：删除 rev-4；引擎 `F`/`FROZEN_SHA` 与 validator 冻结集指回 `spec-rev-3`（`2d6dbd8bd8d667d7`）⇒ 复跑即回到 W3-CN.40 基线（`dfa1d7c4a811b0da` / 板 `cdcb869e9827ec87`）。

## 6. 红线 / 未改物 / 指纹

- 四冻结源 **4/4 MATCH**（`0bd52ed4 / a8ef3ea8 / fb07d25a / 0a459839`）；原 `SPEC_k2_v4.json`、`spec-rev-2`、`spec-rev-3` 未动；不改阈值；不改平面层用途；零几何改动。
- 变更工具：`tools/p3_v57_co56_emit_spec_rev4.py`（发射）、`tools/p3_v57_w3_constructive.py`（`F.spec`+`FROZEN_SHA`→rev-4）、`tools/p3_v57_w3_constructive_validator_v2.py`（冻结集→rev-4）、`tools/p3_v57_l5_signoff.py`（rev L5-SI.5 + rev-4 口径）。
- 指纹：rev-4 **`1c4eecb0edf4a446`**｜图纸 `4e7497daf97cebd1`｜landing `54c44b6a5aa54f40`｜G5 `95ec1af12f6edae3`｜板 `cdcb869e9827ec87`（不变）｜l4val `b15c6432a3da3e39`｜l4constr `758314dc01814701`｜fab `cc20edd45406db6b`｜dfm `de14f887a7819c11`（不变）｜si `12bab1f0152b5e0e`｜G7 `38c63392b29459d5`｜audit `69fcbcdd19025874`｜requirement `e9e1268b8e9bf312`（不变）。
