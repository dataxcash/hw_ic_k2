# M13 高速域重建器 v1 — 进度报告（含 v2 计划）

> 日期：2026-08-25 · 承接：m13_highspeed_plan.md（方案论证）+ phase1_pin_audit.md（逐 Pin 预检）
> 三域联动授权：PERSTB# 让道 + PDN 让位 + 重建器实现（用户 2026-08-25 同意）

---

## 0. 一句话总结

重建器 v1（`eda_core/hs_route_model.py`）核心算法**全部建成并单段验证可靠**：
V-Graph（unified 规则膨胀）+ 三域清场 + 差分对内豁免 + 焊盘边缘候选 + 链路识别 + 蛇形等长。
**单段求解已验证**（UP4/DN0 输入段 SOLVED 带路径证据）；链路级未收敛——输出段 V-Graph
超时 + P/N 独立最短路路径不对称（skew 大），v2 改造方向明确。

---

## 1. 交付物（本轮）

| 产物 | 路径 | 状态 |
|---|---|---|
| 重建器 v1 | `eda_core/hs_route_model.py` | 核心算法建成 |
| 对内豁免 | `eda_core/unified_field.py` `_req_for`（P/N 同 base → min_gap 0.1） | M11 55 测试零回归 |
| 单测 | `eda_core/tests/test_hs_route_model.py` | 8 条全绿 |
| REFCLK 裁决 | SPEC corridors refclk band(In6) + `channel_alloc.py` layer 支持 | 18/18 SOLVED |
| 通道表 v2 | `artifacts/L3/model_solves/channel_alloc_v2/` | 含 REFCLK In6 |
| 预检报告 | `artifacts/L3/m13_highspeed_phase1_pin_audit.md` | 落盘 |
| 架构蓝图 | `artifacts/L3/m13_highspeed_rebuilder_design.md` | 落盘 |
| 方案论证 | `artifacts/L3/m13_highspeed_plan.md` | 落盘 |

## 2. 已验证能力（带证据）

| 能力 | 证据 |
|---|---|
| 三域障碍场（高速清场 + PDN 让位 + 刚性保留） | build_hs_field 单测 + 实测（刚性段 99） |
| 差分对内豁免（P/N 焊盘净距 0.15 用 min_gap 0.1 非 clearance 0.175） | UP0 从 INFEASIBLE → SOLVED（skew 0.053） |
| 焊盘边缘候选（连接器密集区边缘接入） | DN0/DN1 从 INFEASIBLE → SOLVED |
| V-Graph 确定性 Dijkstra（零随机） | 单测 test_solve_deterministic |
| 链路识别（input + OUT 段） | _chain_segments（v1 命名模式修复后） |
| 蛇形等长（amp 0.05-0.25 粒度扫描） | _snake_compensate |

**单段求解实测**（k2_m9demo，V-Graph）：
- UP4 输入段 P 46.0mm / N 46.3mm（MCIO→U7，绕 PERSTB# 走 x<54.5）
- DN0 输入段 P 33.4mm / N 49.3mm（J2→U3，cv 边缘接入）

## 3. 未收敛项与根因（v2 改造清单）

| # | 问题 | 根因 | v2 方案 |
|---|---|---|---|
| 1 | 输出段（U7→电容→J2）V-Graph 超时/无解 | 走廊区障碍密集（U7 输出 + 电容墙 + GND via）→ 节点数千 → O(n²) 查询超限 | **走廊段确定性折线**：channel_alloc 通道 track_y 直线 + seg_ok 验证（走廊内障碍少）；仅逃逸段用 V-Graph |
| 2 | 链路 skew 巨大（DN0 11-14mm） | P/N **独立最短路** → 路径不对称（P 直连 N 绕行） | **对中心线求解**：P/N 焊盘对中点 → 中心线 V-Graph → ±0.19mm 对称展开（P/N 必然并排等长） |
| 3 | REFCLK 未解 | REFCLK 通道在 In6.Cu（非 F.Cu 场） | v2 支持层参数场（build_hs_field(layer='In6.Cu')） |
| 4 | 全量 16 对未收敛 | 依赖 #1/#2 修复 | v2 后全量重跑 + solve_ref 落盘 |

## 4. v2 里程碑（下一轮）

1. 走廊段确定性折线（通道直线 + 验证，零 V-Graph）→ 解决输出段超时
2. 对中心线求解 + P/N 对称展开（差分对本质建模）→ 解决 skew
3. REFCLK In6 场求解
4. 全量 18 对 → solve_ref + input_fp 落盘 `model_solves/hs_rebuild/`
5. model_gate 验证（100% 模型来源）→ S2 sregress/sadvance → DRC 复验（高速 385 目标）

## 5. 铁律遵守

- **方案即模型输出**：全部路径出自 hs_route_model（V-Graph 确定性），施工层照抄
- **DRC 只核对不驱动**：0 改走线（本报告纯模型/分析产物）
- **结论带证明**：SOLVED 带路径证据；INFEASIBLE 带连通分量/障碍（v1 已验证 component 方法）
- **修订走输入**：REFCLK 通道/PDN 让位/PERSTB# 让道全部入 SPEC 或入参
- **零 revA 特判**：hs_route_model 全通用（差分对/通道/规则全部入参）
- **不预先拍板**：重建范围由模型判定（v1 单段可靠 → v2 链路收敛）

## 6. 测试

`test_hs_route_model.py` 8 条全绿（障碍场/端点/可见性图确定性/区域裁剪/基线 UP4 单段）；
`test_unified_field.py` 等 M11 55 条零回归（_req_for 默认不激活）。
