# P3-ECO-1 设计说明 — gap1 修复：track_y 段级解析（按段廊道独立取轨道）

> 阶段：P3-ECO-1 回上层 ECO 设计（先设计后施工，TASK MGR 复核后再动代码）
> 施工位置：`_shared/eda_core/hs_route_model.py` + `_shared/eda_core/routing_topology_gate.py`（消费端解析规则）
>           + `_shared/docs/SOLVE_PIPELINE_CONTRACT.md` + docstring（字段级契约）
> 关联任务卡：`p3_eco_gap1_channel_alloc_seg_tracks_card.md`
> 铁律：SDD 驱动、问题回模型、冲突即停机、零单板特判、禁止假成功

---

## 0. 结论先行

**选修复方向 2：`_track_y_for` / `_segment_track` 按段所属廊道 bands 独立解析轨道（同 band 同 idx 映射）。**

排除方向 1（③ channel_alloc 产出段级 `seg_tracks`）的理由见 §3——核心是段→廊道映射是**几何事实**（板 pad 坐标），只存在于消费端；把段结构塞回 ③ 会让纯 SPEC 驱动的 channel_alloc 依赖板几何，违反其铁律（L16：走廊/通道全部来自 SPEC，入参全路径）。

---

## 1. 现象与根因（已实证，P3-B 真板 e2e report）

- **现象**：solve 阶段 16/18 数据对 INFEASIBLE。REFCLK0 SOLVED（两廊道 refclk 轨道相同 45.7/50.5）。
- **根因链**：
  1. `channel_alloc._assign_deterministic`（channel_alloc.py L122-169）沿「走廊序→band 序→track_y 升序」分配，band 归属硬约束按 `(corridor, band)` 组合（L145 `_net_matches`）→ 16 数据对全部落 **J2_TO_U** 廊道的 upper/lower 带，产出单 `track_y`（如 40.3），**U_TO_MCIO 廊道轨道从未被分配**。
  2. 消费端 `_track_y_for`（hs_route_model.py L644-671）无 `seg_tracks` 时回退 `rec.track_y`（L660-661），再用 **J2_TO_U 的绝对 y 值**去 `track_y in U_TO_MCIO.bands.tracks_y` 校验（L666-670）→ 40.3 ∉ [40.7, 41.9, …] → 返回 None → 报「无通道分配（INFRA_ERROR）」。
  3. `routing_topology_gate._segment_track`（L377-403）同构缺陷（L394 回退 + L400 校验）。
- **为何 REFCLK 能过**：refclk 带两廊道 tracks_y 完全相同（45.7/50.5），J2_TO_U 的 y 值恰好也在 U_TO_MCIO 带内命中。
- **SPEC 事实**（SPEC_k2_v4.json L8836-9004，勿硬编码）：J2_TO_U upper=[40.3,41.5,…,48.7]、lower=[58.3,…,66.7]；U_TO_MCIO upper=[40.7,41.9,…,49.1]、lower=[58.7,…,67.1]——同 band **同数量同 pitch，绝对 y 整体偏移 0.4mm**。

---

## 2. 契约改动（验收 A：字段级契约写进 docstring/契约文档）

### 2.1 字段语义修正（核心契约改动）

**`AllocTable.alloc[net].track_y` 的语义从「绝对轨道 y 值（跨廊道通用）」修正为「分配廊道（`corridor` 字段）内 band 中的轨道索引载体」。**

即：`track_y` 是分配廊道里 band 轨道的绝对 y；**索引 `idx = alloc 廊道.bands[band].tracks_y.index(track_y)`** 才是跨廊道可移植的分配单位。消费端对非分配廊道段，按 `同 band 同 idx` 在段所在廊道的 `tracks_y` 中取绝对 y。

### 2.2 具体落点

| 文件 | 改动 |
|---|---|
| `_shared/docs/SOLVE_PIPELINE_CONTRACT.md` §2 ③ alloc 行（L42） | 关键字段加注：`alloc(net→track_y)` 中的 `track_y` 为「分配廊道内 band 索引载体，跨廊道按同 band 同 idx 解析」；新增一行「段级解析规则见 hs_route_model._track_y_for / routing_topology_gate._segment_track docstring」 |
| `_shared/docs/SOLVE_PIPELINE_CONTRACT.md` §3 数据流（L50-65） | ⑤ solve 消费 AllocTable 处加注：轨道解析按段所在廊道 bands 独立进行（几何解析段廊道 → 同 band 同 idx 取轨道） |
| `_shared/eda_core/hs_route_model.py` `_track_y_for`（L644） | docstring 增加字段级解析规则（见 §4.1 伪码），删除「两廊道 bands 完全相同直接复用」假定 |
| `_shared/eda_core/routing_topology_gate.py` `_segment_track`（L377） | 同上，docstring 同步 |
| `_shared/eda_core/channel_alloc.py` | **零改动**（生产端语义不变：仍在分配廊道内按索引分配，产出单 track_y + corridor + band，字段含义与现有 fixture 自洽） |

---

## 3. 方向 1（③ 产 seg_tracks）排除论证

- **段→廊道映射是几何事实**：段（input/out_U7/out_J2/out_U3/out_MCIO）归属哪个廊道由段两端 pad 的 x 坐标与走廊 x_range 重叠度决定（`_corridor_for_x`，基于板）。channel_alloc 是**纯 SPEC 驱动**（无板、无 pad 几何，铁律 L16）。要让它产段级 seg_tracks，必须把段结构（`_chain_segments` + 几何廊道解析）搬进 ③ 或喂板几何 → 引入 ③↔⑤ 耦合与单板特判风险。
- **历史产物来源**：M13 v5 的 seg_tracks（channel_alloc_v2 fixture）由当时带板/几何上下文的 hs_rebuilder 脚本产出，非当前 channel_alloc 架构；v4 fixture 已是过渡态（track_y 与 seg_tracks 索引不一致），说明该路径不稳定。
- **修复面积**：方向 1 需改 ③ 生产端 + AllocTable schema + adapter + 全部 fixture + 消费端回退路径；方向 2 只改两个消费函数解析规则 + 契约文档，回归风险最小。
- **兼容性**：方向 2 保留 `seg_tracks[segname]` 显式优先路径（L660-661 不动）——未来若 ③ 产出段级轨道，消费端自动优先；无 seg_tracks 时按新规则解析，不依赖 ③ 改动。

---

## 4. 施工方案（设计批准后执行）

### 4.1 `_track_y_for` 解析规则（hs_route_model.py L644-671 改）

```
def _track_y_for(self, net, corridor_id, segname=None):
    rec = self._channel_for(net)
    if not rec: return None
    band = rec.get("band")
    # 1) 段级显式轨道（既有路径，保留）：seg_tracks[segname] 优先
    if segname and isinstance(rec.get("seg_tracks"), dict) and segname in rec["seg_tracks"]:
        y = rec["seg_tracks"][segname]
        # 按段廊道校验（原逻辑），命中即返回
        ...
    # 2) 回退路径改造：按段廊道同 band 同 idx 解析
    y_alloc = rec.get("track_y")
    src_corr = next((c for c in spec.corridors if c.id == rec.get("corridor")), None)
    tgt_corr = next((c for c in spec.corridors if c.id == corridor_id), None)
    if not src_corr or not tgt_corr or band is None or y_alloc is None:
        return None
    src_band = next((b for b in src_corr.bands if b.band == band), None)
    tgt_band = next((b for b in tgt_corr.bands if b.band == band), None)
    if not src_band or not tgt_band:
        return None  # 目标廊道无此 band → 如实 INFRA_ERROR，不猜
    src_tys = src_band.tracks_y
    if y_alloc not in src_tys:
        return None  # 数据不一致 → 保守失败（禁止假成功）
    idx = src_tys.index(y_alloc)
    tgt_tys = tgt_band.tracks_y
    if idx >= len(tgt_tys):
        return None  # 目标廊道轨道数不足 → 如实归因
    y = tgt_tys[idx]
    return y, tgt_band.get("layer", "F.Cu")
```

要点：
- **零 0.4mm 硬编码**：完全读 SPEC corridors bands.tracks_y（验收 D）。
- **确定性**：index() 纯函数，无随机（验收 B③）。
- **同廊道不回归**：`corridor_id == rec.corridor` 时 idx 映射退化为原值（合成板两廊道相同 → 字节级不变；REFCLK 路径不变）（验收 B②）。
- **同 idx 前提**：SPEC 两廊道同 band 同数量同 pitch（§1 实测）→ idx 恒不越界；越界走保守失败，如实归因（验收「禁止假成功」）。

### 4.2 `_segment_track` 解析规则（routing_topology_gate.py L377-403 改）

同 4.1 逻辑：`corr` 已由 `_corridor_for_x` 几何解析（L390），把回退路径的 `float(track_y) in tys` 改为「在 alloc 廊道 band 中定位 idx → 在 `corr`（段廊道）band 中取 `tys[idx]`」。

### 4.3 单测（验收 B，新增到既有测试文件）

| 用例 | 断言 |
|---|---|
| `test_channel_alloc_track_y_seg_corridor_offset`（test_hs_route_model.py） | 构造两廊道 upper 轨道偏移 0.4mm 的 SPEC + 单 track_y alloc（落 J2_TO_U）→ `_track_y_for(net, "U_TO_MCIO", segname)` 返回 U_TO_MCIO 同 idx 轨道（如 40.3→40.7） |
| `test_channel_alloc_track_y_same_corridor_regression` | 同廊道调用（corridor_id == alloc.corridor）返回原值，既有用例全绿不回归 |
| `test_channel_alloc_track_y_determinism` | 同输入两次调用结果一致（含 solve_ref 不变） |
| `test_segment_track_corridor_offset`（test_routing_topology_gate.py） | 同上，`_segment_track` 对 U_TO_MCIO 段解析正确轨道 |
| 真板/SPEC 级 | 复用 `p3_k2_real_board_e2e.py` 作为回归（验收 C） |

### 4.4 真板重跑（验收 C）

`python3 k2/tools/p3_k2_real_board_e2e.py`（走容器级 `_shared`，L34 硬编码）→ 报告 `gaps[0].evidence.count` 从 16 下降。目标：16 数据对 SOLVED；残留 INFEASIBLE（REFCLK1 escape_landing P/N 交叉 = gap2 ECO-2 卡，out_U7 段占位 = 独立容量归因）如实归因，禁止假成功。

---

## 5. 验收对照

| 验收 | 达成方式 |
|---|---|
| A 字段级契约 | §2：SOLVE_PIPELINE_CONTRACT §2/§3 加注 + `_track_y_for`/`_segment_track` docstring 字段级规则 |
| B 单测 | §4.3 新增 4 用例：偏移场景/同廊道回归/确定性/段解析 |
| C 真板重跑 | §4.4：INFEASIBLE 16 → 目标 SOLVED，残留如实归因 |
| D 零单板特判 | 全程读 SPEC corridors bands.tracks_y，无 0.4mm 字面量 |
| E pytest 全绿 | `cd ic_hw && python3 -m pytest _shared/eda_core/tests/` 零新增失败 |

## 6. 风险与防御

- **idx 语义前提**（两廊道同 band 同数量）：真板 SPEC 已验证成立；防御：idx 越界/目标 band 缺失 → 返回 None（INFRA_ERROR），不猜不兜底。
- **seg_tracks 路径交互**：保留显式优先，且显式值仍按段廊道校验，不产生双轨语义漂移。
- **K2V4_REAL_BOARD 缺失**：板依赖单测（TestBoardLevelConsistency 等）当前 skip；验收 C 以 e2e 脚本为准（其自锚定真板路径），不受影响。

---

## 7. 记录

- 本设计文档：`k2/pm_gate/artifacts/k2_v4/L3/p3_eco_gap1_channel_alloc_seg_tracks_design.md`
- 状态：**待 TASK MGR 复核**。复核通过后施工（§4），施工后按 §5 验收。
- 禁止：复核前改任何引擎代码；改真板/SPEC 数值；硬编码 0.4mm。
