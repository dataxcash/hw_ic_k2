# CO-91（L2 自裁 · PDN 计划坐标净距）— `pdn_apply` 实落集的**权威净距闸** = **FAIL**

> 日期 2026-09-12｜工具 `tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py` `4c5c6de9e1056096`（需 AppDir pcbnew；只读 + 确定性）
> 记录 `m13_v57_co91_pdn_planned_coord_clearance_gate.json` `14307586ac0439cc`｜SPEC **rev-9** `77f5c54df88bb0ca`｜板 `0e636a67c1472462`｜规则源 `_shared/eda_core/drc_rules.json` `0a459839e15960b8`

## 1. 立件理由（覆盖缺口）
CO-88 判定 `pd.zone_defs` 机读决策的**板实性**（引用存在性 / 覆盖性 / 解耦落点），CO-89 把 SPEC 升到 rev-9 板实化，
CO-90（pass 3/3）复核 rev-9 事实与 CO-89 幂等（V6：重跑发生器 `223 entries + 86 blocked` 逐值相等）。
**但三件都只判「引用/覆盖/幂等」，从未判「计划坐标本身的几何净距」**：`pdn_apply.py` 逐字把这些坐标实落到板上
（`add_via(...)` + `add_track(..., "F.Cu", ..., width=0.5)`），而没有任何闸把「SPEC 计划坐标 × 交付板现有铜」做净距核对。
本件补该缺口：**判 = 计划坐标是否满足冻结规则源 `drc_rules.json`。**

## 2. 判定口径（不新增/不放宽任何阈值）
- `required(a,b) = max(netclass(a), netclass(b), board_min)`；同网豁免；`hole: 孔缘-铜边 ≥ min_hole_clearance(0.25)`。
  netclass 取自 `drc_rules.json`（PCIe85 `0.175` / POWER `0.2` / LOW_SPEED `0.1`）；语义核已对齐 kicad DRC **430/430 + 106/106**。
- via 尺寸取自实化器常量 `eda_core.pdn_apply.VIA_DIA=0.35 / VIA_DRILL=0.2`（本闸断言一致，非自定）。
- **层语义**（`drc_rules.layer_interaction`：两元素共享任一铜层才检）：via 可为盲/埋孔 ⇒ 判定段时必须做**层集相交**。
- 几何精确：pad = 轴对齐外接矩形、via = 圆、段 = 线段（rect-vs-seg / seg-vs-seg 精确，非采样）。

## 3. 结果（rev-9 × 交付板；verdict = **FAIL**）
| 实落集 | 目标数 | 违规 | 例（净距余量 mm） |
|---|---|---|---|
| `power_pad_connect.entries[].via_pos` | 223 | **35** | `U6.CG35` GND @(94.15,49.135) vs via `PCIE_UP7_N`：-0.2158（两 0.35 via 中心距 **0.3092 < 0.35 ⇒ 铜重叠**） |
| `gnd_stitch_via.coordinates[]`（非 blocked） | 69 | **41** | `(62.5,62.9)` GND vs F.Cu `PCIE_REFCLK1_P`：-0.41（via 中心距该走线中心线 **0.042**） |
| `power_zones[].vias[]` | 20 | **7** | `(56.2,49.8)` P3V3_AUX vs In2 `PCIE_DN_OUT5_P_MCIO`：-0.455（via 落**在走线上**） |
| `power_pad_connect` F.Cu 短段（w=0.5） | 223 | **75** | `U6.CG35` 短段 vs via `PCIE_UP7_N`：-0.30（0.5mm 宽短段与 0.35 via 铜重叠 0.125） |
**ppc via 35 例分因**：段 20 / via 15；**按 ref**：U6 20、J3 6、J4 6、J2 3。**短段 75 例按 ref**：U6 63、J4 5、J2 3、U1 3、J3 1。
**牙齿（真跑检测路径，4/4）**：已知坏位被抓、已知净位通过（via / 段各一路）。

## 4. 根因（引擎侧，均已定位到行）
1. **via 从不被当作障碍**：`pad_connect_gen.clear_via_from_obstacles` 对 `PCB_VIA` 直接 `continue` ⇒ 计划 via 可与**既有 via 铜重叠**（本件 15 例）。
2. **净距用扁平常数**（pad `0.1` / 段 `0.05`）而非 netclass 派生的 `required` ⇒ 与 PCIe（0.175）/POWER（0.2）网冲突（本件 20 例段因）。
3. **无 `min_hole_clearance`（0.25）概念**：对 GND 而言孔距常是**绑定约束**（需 0.35 > 引擎的 0.275）。
4. **stitch / zone via 是更早阶段落盘、之后未随布线复核**：`gnd_stitch_via` 各 `basis` 自述「逐障碍网级净距校验…余量 0.250」为 **2026-08-23 wp1** 时点结论；
   v57 布线（如 REFCLK/MCIO）随后穿过这些孔位 ⇒ 漂移（本件 41 + 7 例）。
5. 短段宽度 `0.5mm`（`pdn_apply` 默认）在 0.5–0.6mm 节距 ball field 内不可能合法（本件 75 例）。

## 5. 修复候选（**只登记，未施加**；施加 = SPEC rev-10 + 全链重基线 + 重新过对抗评审）
- **ppc 35 例：可重定位 35/35、无新增 blocked** ⇒ 修引擎（补 via 障碍 + netclass/hole 口径 + 受控候选集）后 **PDN 覆盖不退化**。
- **stitch 41 例 / zone 7 例：不能只靠重定位** ⇒ 须以当前交付板**重派生** StitchSet / power-zone vias（并保留退役集），属独立变更单。
- **短段宽度**：须由「0.5mm 全宽」改为与节距相称的口径或改由平面直连 ⇒ 与（1）同批。
- 门禁：本件（CO-91）即为该缺口的**回归闸**（现判 FAIL；修复后可转 PASS）。

## 6. 自我捕获（本件自查两处检测器缺陷，均在发布前修正）
- 首版**忽略层语义**（`layer_interaction`）⇒ 把 F.Cu 短段与 B.Cu 走线误判为冲突：短段违规 107 → **75**（29 例假阳）。
- 进一步发现障碍可为**盲孔**（例：`PCIE_UP_OUT0_N_J2` 为 In5→B.Cu）⇒ 对 F.Cu 短段**无共享层**、不构成冲突；补层集相交后 78 → **75**。
- 独立交叉验证：**`kicad-cli pcb drc` 对交付板 = 42 条（全部 lib_footprint_* / silk_edge），铜层违规 0** ⇒ 交付板本身干净，本件判的是**计划坐标**，不是已交付板。

## 7. 非声明 / 残余
- **非声明**：不改 SPEC / 板 / 阈值 / 冻结源；**不改 `_shared` 引擎模型**（只登记修复候选）；不触 L1（拓扑/接口/信号流向/电源域/球重映射均未动）；
  不声称 PDN 压降/热已闭合；不声称「交付板不合格」（板逐字节 `0e636a67c1472462`、铜层违规 0）。
- **残余（非本件可解）**：
  1. **L1 ①**（对间净空 0.875，三硬限）待 owner 择 A/C。
  2. **U6 63 blocked**：本件独立复核 = **在引擎自述设计政策（异网铜边 ≥0.3）下不可解**（8 向 × r≤2.0mm 仅 8/63 可解；纯 DRC 口径 39/63）⇒ CO-89 §4.1 的「硬阻塞」结论**成立**；
     但其所述依赖 **「需 DS320PR1601 器件资料」不成立** —— 354 球图 `ds320pr1601_ballmap.json` / 数据手册 `ref/ds320pr1601.pdf` **已在仓内**（v22 layer gate 已消费）；
     真实瓶颈 = **工艺/口径裁决**（via-in-pad 能力 或 放宽判定域），不是缺数据。
  3. PDN 压降 / 热 = NOT_DEMONSTRATED（缺输入）。
  4. 板厂阻抗券。
- **CO-90 集成说明**：CO-90（pass 3/3）由并行会话完成但**未及提交**（其 boundary v1.55 引用 co90 记录 `897ff5cc…`，实际记录已重生成为 `badba5d9…` ⇒ co77 报 `CITATION_MISMATCH`）。
  本会话核过 co77/co78/co81/co84/co87/co88 后**完成其集成**，并在 boundary **v1.56** 中修正该引用（v1.55 原样留存，不静默改动）。

## 8. 复现
```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
../AppDir/usr/bin/python3.11 tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py   # 期望 FAIL（修复前）
../AppDir/bin/kicad-cli pcb drc --format json --severity-all --refill-zones --output /tmp/drc.json k2_v4_8L.l4.kicad_pcb
python3 tools/p3_v57_co77_closure_declaration_sweep.py
```
