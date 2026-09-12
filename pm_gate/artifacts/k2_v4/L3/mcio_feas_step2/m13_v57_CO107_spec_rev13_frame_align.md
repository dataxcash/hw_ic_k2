# CO-107 L2 PDN 自裁施加：SPEC **rev-13** = 平面多边形随板框 ECO 对齐（CO-106 FAIL 的修复）

- 依据：`LAYOUT_CONSTITUTION` ch.2 —— 叠层分配 / PDN 架构属 **L2**（板框本身是 L1 冻结决策，未动）。
- 内容：把 3×GND（In1/In3/In6）+ 2×In4（`P3V3_EAST`/`MCU_VDD_WEST`）多边形的下边 **70.7 → 78.7**（= `board.outline_y` 79 − `edge_copper_min` 0.3），与各多边形**自身 basis**（「整面铺铜 + 板边内缩 0.3」）一致。
- **退役留存**：rev-12 原多边形存入 `pd.zone_defs.retired_superseded_frame_extent_v1`（`retired[]` 逐条含 old/new polygon；禁静默放弃）。
- 红线遵守：**只改 polygon 顶点 + `spec_version`**；不改阈值 / 网 / 层角色 / 坐标集 / `stub_width_mm` / blocked 台账 / 冻结源。

## 重基线结果（几何不变性 + 板逐字节不变）

| 面 | 结果 |
|---|---|
| spec | `SPEC_k2_v4.spec-rev-13.json` **`7943be727a4f8ef9`**（rev-12 `1a381b06454dbe2c` 保留未动） |
| 几何不变性 | 新图纸 `route_geometry` / `pages` / `landing_rows` 与 rev-12 基线**逐字节同**；仅 `inputs_sha.spec` 与 `frozen_sha_check` 变 |
| G4 | **FEASIBLE_ALL**（34 页 / crossings 0 / work 546/546 / certs 0）主件 **`73c0066df83fa8c2`** |
| G5 | **PASS**（frozen=True；validator 冻结集 spec 前缀 + 引擎 `FROZEN_SHA["spec"]` 同批 bump） |
| G6/L4 | **PASS**（viol 0；板 **`0e636a67c1472462` 逐字节不变**） |
| G7/L5 | FAB ok；DFM new=0；在册未连 **0/68**；SI skew **0.1300 ≤ 0.15** |
| PDN/回归 | CO-99 **PASS**(0/0/0/0)、CO-91 PASS、CO-92 不动点、CO-88 PASS(185/124/silent 0)、CO-95 OPEN(35/8/6/6 不变)、CO-98 OPEN(35/14/6 不变)、CO-97 PASS、co77 PASS(v1.72)、co78/81/84/87/69 PASS；**CO-102 verify 42 / 76(+34) / 42(+0)** 不变 |
| CO-106 | rev-12 `FAIL_DECLARED_COPPER_MISSING`（60 点/36 段）→ rev-13 **`INDETERMINATE_REGION_SCOPED`**（`declared_copper_missing` **0**） |

## 链 pin 同步（rev-12 → rev-13）

引擎 `SPEC` 路径 + `FROZEN_SHA["spec"]`｜validator `FROZEN_SHA_PREFIX["spec"]` + 内部 `FROZEN`｜闸默认 spec：co78/co81/co84/co91/co92/co95/co98/co99/co102｜co104/co105/co106 输入与 BASE 钉｜co77 声明扫描正则。
**未改（按设计）**：co100/co101/co107 的 `SRC`（输入件 = rev-11/rev-12）；**CO-103 保持 rev-12 对象**（其复评记录为 rev-12 历史件；rev-13 后的链 pin 已前移 ⇒ 重跑 CO-103 预期报 V9 不复现，语义同 CO-96 fail-closed）。

## 复现

```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
../AppDir/usr/bin/python3.11 tools/p3_v57_co107_spec_rev13_frame_align.py    # 幂等重导 rev-13（期望 spec_sha16 7943be727a4f8ef9）
python3 tools/p3_v57_w3_constructive.py --r1-5-shape co16                    # 期望 FEASIBLE_ALL 73c0066df83fa8c2
python3 tools/p3_v57_w3_constructive_validator_v2.py                         # 期望 PASS frozen=True
../AppDir/usr/bin/python3.11 tools/p3_v57_co106_reference_plane_gate.py      # 期望 INDETERMINATE_REGION_SCOPED / missing=0
python3 tools/p3_v57_co77_closure_declaration_sweep.py                       # 对象 = 最新 boundary（v1.72）⇒ 期望 PASS
```

## 非声明与债

- 本件**只**修板框一致性；In4 中段（`x≈49.8..88.37`）的铜仍属**桥区待 L3 派生**（CO-98 `declared_pending_l3` 同桶）⇒ In5 的 In4 参考连续性与 In5 阻抗模型在该带**仍不可判定**（不得声称已满足）。
- **复评债 = CO-108（非执行者）**：对象 = rev-13 新基线（CO-106/CO-107 + 链 pin 前移 + 几何不变性 + 板逐字节不变）；依 `L2_STRUCTURE_v2.0.md:137` 本件为执行者，不得自评。
- PDN 压降 / 热仍为外部输入项（CO-87 两项 NOT_DEMONSTRATED）；板厂阻抗券待补。
