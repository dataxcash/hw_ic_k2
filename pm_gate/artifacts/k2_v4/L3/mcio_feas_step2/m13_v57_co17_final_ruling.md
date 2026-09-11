# CO-17 —【L2/L3 更正】CO-16 O4 蛇形**可闭合**（陡腿单侧 + 腿距约束）；唯一剩余 L2 阻塞 = **西 J3 fan 出板**

> 2026-09-12｜裁判：ARCHER（L2 走廊/等长/过孔策略，自裁；无 owner 闸口）｜性质：**更正裁定**（取代 `m13_v57_CO17_o4_meander_geometry_gap.md` 的否定结论 `524bb54a3b444bb7`）
> 触发：监理巡检；并核实工作区引擎的 `meander_zig` 已为「腿距约束（`LEGSEP_MIN=0.38`）+ 陡腿（a < A）」闭式模型。

## 0. 更正要点
先前否定裁定的**前提**是「锯齿不陡于 45°（a ≥ A）」。该前提过强：允许 **陡腿（a < A）** 并约束
**相邻斜腿垂直净距 `2aA/sqrt(a²+A²) ≥ 0.38`** 时，单侧容量 `≈ (2A/TT − 1)` mm/mm 段长，远高于 45° 的 `√2−1`。
于是 `CO16-ALLOC.1` 的通道净距（西 lane 1.1265 → 同向轨距 0.6265）**足以**容纳 O4 补偿。

## 1. 实测（引擎 `--r1-5-shape co16`，工作区当前态）
| 项 | 值 |
|---|---|
| verdict | **FEASIBLE_ALL**，certs=0 |
| `same_layer_crossings` / A-CN.9 | **0 / 0** |
| 独立复核 `tools/p3_v57_co11_placement_verify.py`（引擎输出→geom） | **320 via / 1685 段 / 0 违规 PASS** |
| 对内 skew（L5 口径：nodes 路径长） | **max 0.0031 mm** ≤ 0.15 ✓ |
| 图纸 sha16 | `87caba88508ae70a` |

## 2. 唯一剩余 L2 阻塞：西 J3 fan landing 出板
- 板形 bbox（`m13_v57_l5_fab_record.json`）= y ∈ **[32.95, 79.05]**。
- `CO16-ALLOC.1` 用 `CO10_FANY_J3=31.5,51.5` ⇒ 西 J3 上排 8 个 landing 在 **y=31.5（出板）**，其 F.Cu land 段与 In2 stub 同出板。
- 探针扫描（只读，其余 CO-16 旋钮不变）：

| `CO10_FANY_J3` U | 结果 |
|---|---|
| **33.5 / 34.5 / 35.5 / 36.5**（L 取 47.0 / 49.0 / 51.5 任一） | **32/32 placed, failed=[]** |
| 38.0 | 31/32（失 `PCIE_DN3/out_MCIO`） |
| 40.0 | 31/32（失 `PCIE_DN1/out_MCIO`） |
| 42.0（默认） | 31/32（失 `PCIE_UP3/input`） |

- **已验证起手几何**：`CO10_WSTEP=1.1265 CO10_WLO=33.3 CO10_FANY_J3=34.5,51.5 CO10_STUB=J3L CO10_POLMODE=lx
  CO10_EASTSPLIT=in2c CO10_J2STEP=0.6 CO10_PAIR=m13_v57_f13_r1_pair_coupling_v1_5.json`
  → 32/32；`p3_v57_co11_placement_verify.py` → **320/320, 0 违规 PASS**（**在板内**）。

## 3. DFM（co16 蛇形图纸实测；kicad-cli 10.0.5 + shop `k2_v4_8L.kicad_pro`）
`new_total 426 → 172`，分解与归属：

| 簇 | new | 归属 / 处置 |
|---|---|---|
| `solder_mask_bridge` 42 + `clearance` 18 + `shorting_items` 9 + `tracks_crossing` 1 | **70** | **PCIE_REFCLK0/1** 与 J2/J3/J4 pad / GND / P3V3 冲突（既有 refclk 路线，非 CO-16 拓扑）→ 单独整改 |
| `copper_edge_clearance` | **29** | **§2 西 J3 fan 出板** → CO-17 可直接修（已给板内窗口） |
| `holes_co_located` 72(warning) + `hole_to_hole` 1(warning) | **73** | L4 同点叠层 via 未合并 → 应合并为**单支贯通 via**（F↔B / In6↔F 等）后重测 |
| `clearance`/`hole_clearance` 自 CO-16 拓扑 | 0 | 拓扑已消除 shorting 108→9、hole_clearance 24→0 |

## 4. 下一步（CO-17 收口）
1. **落地板内 fan**：`CO10_FANY_J3 ∈ [33.5,36.5]` 重派生 `CO16-ALLOC.2` → 探针+复核 PASS → 引擎 `CO16_ALLOC_SHA` 同步 → one-shot。
2. **L4 叠层合并**：同点 (E=B / S=B) 的层对 via 合并为单支贯通 via（消除 holes_co_located 72 + hole_to_hole 1）。
3. **REFCLK 路线**单独整改（70 项）。
4. 再跑 **ECO（SPEC bump + validator）→ G4→G5→G6→G7**，目标 **DFM new=0**；milestone 按 `pm_gate/TAG_POLICY.md` 打 tag。

## 5. 红线
只读消费冻结四源（未改）；canonical W3-CN.30 `05f7bd10ab3b45b6` 未 promotion；默认 t2 路径逐字节不动；
零坐标搜索；未放宽阈值；无 partial pass；无 sign-off；结论以实测为准（否定裁定已更正）。
