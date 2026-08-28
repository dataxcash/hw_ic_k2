# DRC-SEMANTIC-CORE M11 交付报告 — 统一障碍场升级

> 日期：2026-08-24 · 板：`k2_v4.kicad_pcb`（对齐验证用 m9demo 快照）· DRC 基线：`k2_m9demo.drc.json`（867 条，勿重跑）
> 承接 M10（§10 交付记录 PASS，四条关键语义直接引用）；本报告全部结论带数字证明，红队可审计。

---

## 0. 一句话总结

五类障碍统一膨胀场（seg/via/pad/zone/mask）建成，**7 类 DRC 规则对齐率全部 100% 零未命中**（M10 遗留 diff_pair_gap/zones_intersect/THT mask/edge==0 全部收编），全局冲突图通道分配落盘（16 SOLVED + 2 REFCLK INFEASIBLE 带证据），低速域迁移回归 point_ok 500/500 + seg_ok 400/400 两场一致。

---

## 1. M10 遗留收编 → 对齐率更新（M11-G，验收第一项）

运行：`python -m eda_core.drc_rules align --board k2_m9demo --pro --rules drc_rules.json --drc k2_m9demo.drc.json`
落盘：`artifacts/L3/drc_semantic_align_af328772.md/.json`

### 1.1 对齐率（唯一对口径，recall = |模型预测 ∩ 实际| / |实际|）

| 规则类型 | M10 recall | **M11 recall** | M10 miss | **M11 miss** | 修复 |
|---|---|---|---|---|---|
| clearance | 100.0% (430) | **100.0% (430)** | 0 | **0** | — |
| hole_clearance | 100.0% (106) | **100.0% (106)** | 0 | **0** | — |
| shorting_items | 95.2% (80/84) | **100.0% (84/84)** | 4 | **0** | edge==0 接触语义 + pad 旋转 |
| solder_mask_bridge | 98.3% (57/58) | **100.0% (58/58)** | 1 | **0** | THT mask 通配符 + pad 旋转 |
| tracks_crossing | 100.0% (46) | **100.0% (46)** | 0 | **0** | — |
| zones_intersect | 0.0% (0/2) | **100.0% (2/2)** | 2 | **0** | 多多边形 zone.polys |
| diff_pair_gap_out_of_range | 0.0% (0/1) | **100.0% (1/1)** | 1 | **0** | min gap = board_min 语义 |

**核心规则综合（clearance + hole_clearance）：100.0% → PASS**。M11 验收：M10 遗留收编后对齐率更新完毕，7 类全 100%。

### 1.2 四项修复的根因与证据

| # | 修复 | 根因 | 证据 |
|---|---|---|---|
| 1 | **shorting edge==0 接触语义** | 模型旧语义 `edge < 0` 才报 shorting；kicad 源码 `drc_test_provider_copper_clearance.cpp` 判定 `actual == 0 && testShorting → DRCE_SHORTING_ITEMS`（铜边缘接触即短路）。3 条漏报的几何 edge 恰为 0.0（GND/MCU_VDD 段 0.5-0.25-0.25、I2C1_SDA vs via 0.25-0.175-0.075） | 修复后 84/84 |
| 2 | **BoardParser pad 旋转约定** | M10 用标准数学 CCW `(x·cosθ−y·sinθ, x·sinθ+y·cosθ)`；KiCad y-down 坐标系实际 `(x·cosθ+y·sinθ, −x·sinθ+y·cosθ)`。J9 pad3 解析 (26.5,57.23) vs pcbnew 实测 (26.5,54.69)，错位 2.54mm → shorting/solder_mask 各漏 1 条 | pcbnew 实测 J9 pad1-4 逐点匹配 |
| 3 | **THT mask 通配符** | THT pad layers 用 `"*.Cu" "*.Mask"` 通配符；M10 `"F.Mask" not in p.layers` 对通配符失效 → 跳过 THT 开窗检查 → solder_mask 漏 1 条（J9 pad3） | `_pad_has_mask` 展开 `*.Mask` → 58/58 |
| 4 | **zones_intersect 多多边形** | zone 有多个 filled_polygon（308e6414: 167+189 点；8f02d0af: 1049+6+6）；M10 解析只取首个 → 1 对相交漏检。`Zone.polys` 收集全部，`_polys_list_intersect` 多对多组合 | 修复后 2/2 |
| 5 | **diff_pair_gap min gap** | kicad 报告 min gap = `bds.m_MinClearance`（板 rules.min_clearance=0.1），**非** netclass diff_pair_gap (0.175)——后者只是 Opt 目标值。实测 PCIE_UP1 P/N 段中心线 y 距 0.3 − 宽 0.205 = 边缘 0.095 < 0.1 → 违规 | librarian 抓 kicad 源码 `drc_engine.cpp:337` `SetMin(bds.m_MinClearance)` + `drc_test_provider_diff_pair_coupling.cpp` computedGap 公式；12 条预测含实际 1 条 |

### 1.3 偏差模式（precision < 1 根因，M10 已证，M11 延续）

模型保留全部几何有效对 = **保守安全语义**（约束求解不漏约束）；kicad ≤1/primary/层 是输出层报告优化（RTree 预筛 + UUID 去重 + pad 覆盖抑制）。两者并存：模型全对子用于求解，报告层对齐率证明规则翻译 == DRC 判定口径。

---

## 2. 五类障碍统一膨胀场（M11-B，验收第二项）

新模块：`eda_core/unified_field.py`（复用 drc_rules.py 几何基元，非重写）。

### 2.1 障碍类型 × 参与规则集 × 膨胀量（规则驱动，零硬编码）

| 障碍 | 参与规则集 | 膨胀量（DRC 同口径） |
|---|---|---|
| seg | clearance, hole_clearance | required = max(nc(A), nc(B), board_min)（中心线 = required + 半宽和） |
| via | clearance, hole_clearance | required；钻孔-铜 ≥0.25 |
| pad | clearance, hole_clearance, solder_mask_bridge | required；开窗==铜几何（无膨胀） |
| **zone（新增）** | clearance, zone | 铺铜平面边缘 vs 走线/焊盘净空 = required（电源地 266 条违规的根） |
| **mask（新增）** | solder_mask_bridge | 异网开窗边缘净距 < 0.05 |

### 2.2 差分对语义（M11 激活）

- **对内间距**：P/N 段边缘净距 < min_gap → 违规；min_gap = board rules.min_clearance (0.1)，p_gap 0.175 为 Opt 目标值（kicad 源码确认）
- **对间间距**：inter_pair_spacing 0.875（SPEC 声明，M13 高速域用）
- **等长**：intra_pair_skew_mm 0.15（`diff_pair_groups` 累计 P/N 长度差）
- 工具：`diff_pair_groups(board, rules)` 按 `_P/_N` 后缀分组

### 2.3 兼容层（迁移回归关键）

`circle_as_square` 开关：circle pad 方盒近似（ls_route_model 历史语义）vs 精确圆（DRC 同口径）。迁移模式=行为不变；原生模式=更精确。

---

## 3. 全局冲突图通道分配（M11-E，验收第三项）

新模块：`eda_core/channel_alloc.py`。

### 3.1 模型

- **资源节点**：SPEC corridors bands 的 tracks_y 轨道带（J2_TO_U 16 轨 + U_TO_MCIO 16 轨 = 32 通道）
- **需求**：18 网（PCIE_UP0-7 / PCIE_DN0-7 / REFCLK0-1）
- **冲突边**：物理重叠（同通道容量 1；相邻轨道 |Δy| < pitch 1.08 冲突）
- **先难后易**：按 DRC 违规密度降序（`_density_rank`），同密度网名升序
- **求解确定性**：Dijkstra 距离升序 + 坐标序，零随机

### 3.2 结果（落盘 `artifacts/L3/model_solves/channel_alloc/`）

- **16/18 SOLVED**：PCIE_UP0-7 → J2_TO_U/upper(40.92-48.48)、PCIE_DN0-7 → J2_TO_U/lower(58.92-66.48)，**band 归属硬约束**（SPEC corridors.bands.nets 真源：upper=PCIE_UP*、lower=PCIE_DN*）
- **2/18 INFEASIBLE**：REFCLK0/1——走廊 band 定义不含 REFCLK（SPEC 输入缺通道声明），模型输出 `no_free_channel` + 16 通道占用证据。**待 PM 裁决 SPEC 输入**（修订走输入，禁止硬编码）

### 3.3 确定性验证

两次运行逐网 channel/track_y 完全一致（`deterministic: True`）。

---

## 4. 低速域迁移回归（M11-F，验收第四项）

### 4.1 方法

同一 LOW_SPEED 障碍集（真实板 m9demo B.Cu 段/via/pad）分别构建 `ObstacleField`（ls_route_model）与 `UnifiedObstacleField`（unified_field），随机采样查询逐项对比。

### 4.2 结果（测试 `test_ls_migration.py`，5 条全绿）

| 查询 | 采样数 | 两场一致 | mismatch |
|---|---|---|---|
| point_ok | 500 | 500 | **0** |
| seg_ok | 400 | 400 | **0** |
| 数学等价 | — | SEG_SEG=0.25/SEG_VIA=0.35/SEG_PAD=0.175 逐项 = 规则驱动膨胀 | — |
| 同网豁免 | — | 段/via 同网可穿 | — |

### 4.3 过程中发现并修复的 unified_field bug（迁移回归的价值）

1. **point_ok 漏查询半宽**：seg 障碍膨胀量只加障碍半宽，漏查询段半宽 → 首轮 3/200 mismatch（ls False uni True）
2. **point_ok 双扣**：修 1 后 seg 障碍 req 重复加障碍半宽（edge_dist_to_point 已扣）→ 反方向 mismatch
3. **circle pad 方盒 vs 圆**：ls 用 `point_to_rect_dist` 方盒近似 circle pad；unified 精确圆。5000 采样 0.06% 差异 → `circle_as_square` 兼容开关解决（ls 历史语义 vs DRC 精确语义）

**结论**：低速域迁移到新障碍场后行为不变（同障碍同判定），迁移过程中暴露的 unified_field 半宽/双扣缺陷已修复并固化为回归测试。

---

## 5. 测试清单（全绿）

| 测试文件 | 条数 | 覆盖 |
|---|---|---|
| test_drc_rules.py | 28 | M10 规则翻译 + pad 旋转修复（原 1 条断言更新为 pcbnew 实证值） |
| test_unified_field.py | 15 | zone 边缘净空 / mask 阻焊桥几何 / diff_pair 语义 / 收编遗留 / 规则驱动膨胀 / 确定性 |
| test_channel_alloc.py | 7 | 通道提取 / band 硬约束 / 确定性 / solve_ref / INFEASIBLE 证据 / 密度排序 |
| test_ls_migration.py | 5 | 迁移回归（point_ok 500 + seg_ok 400 + 数学等价 + 同网豁免） |

**合计 55 条全绿**（`pytest eda_core/tests/test_drc_rules.py test_unified_field.py test_channel_alloc.py test_ls_migration.py`）。

---

## 6. 交付物清单

| 产物 | 路径 |
|---|---|
| 统一障碍场 | `eda_core/unified_field.py`（五类障碍 + 规则驱动膨胀 + circle_as_square 兼容） |
| 通道分配 | `eda_core/channel_alloc.py`（冲突图 + 先难后易 + 确定性 Dijkstra） |
| 规则库扩展 | `eda_core/drc_rules.json`（diff_pair 激活 / zone 规则 / mask THT 通配符声明） |
| 规则库实现 | `eda_core/drc_rules.py`（shorting edge==0 / THT mask / zones_intersect / diff_pair_gap / pad 旋转修复 / Zone.polys） |
| 对齐报告 | `artifacts/L3/drc_semantic_align_af328772.md/.json`（7 类 100% 零未命中） |
| 通道分配表 | `artifacts/L3/model_solves/channel_alloc/`（18 网逐网文件 + channel_alloc.json + summary.json） |
| 单测 | `eda_core/tests/test_unified_field.py` / `test_channel_alloc.py` / `test_ls_migration.py`（+ test_drc_rules.py 更新） |

---

## 7. 铁律遵守

- **DRC 只核对不驱动**：对齐率是质量度量；0 手工改走线（不碰任何 locked 高速段）
- **方案即模型输出**：通道分配全出自 channel_alloc 模型，带 solve_ref + input_fp + 确定性证据
- **结论带证明**：SOLVED 带通道坐标；INFEASIBLE 带占用证据清单；对齐率带逐类型数字
- **修订走输入**：REFCLK 通道缺口 → INFEASIBLE 证据输出，待 PM 裁决 SPEC 输入（未硬编码）
- **零 revA 特判**：unified_field/channel_alloc 全通用，入参全路径；规则全声明式
- **红队可审计**：本报告 + 求解记录 + 对齐 JSON 全部落盘

## 8. M12 衔接（非本 M 范围）

- `drc_locator`（M12）：7 类 100% 对齐后，867 条每条可定位到"元素+规则+根因"
- 高速域重建（M13）：unified_field 差分对语义 + 通道分配表是输入
- 电源地铺铜（M13）：zone 障碍语义已就绪（266 条违规的根）
