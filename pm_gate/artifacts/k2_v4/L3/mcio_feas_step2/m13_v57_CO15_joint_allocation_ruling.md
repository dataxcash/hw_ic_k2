# CO-15 — 【L2/L3】联立推导收口：西侧 **32/32 全落位**（crossing-free + clearance-clean），UP6/UP7 自叉根因消除

> 2026-09-11｜裁判：ARCHER（L2 层角色/lane 分配/过孔策略，自裁；L3 域消费）｜性质：**变更单 + 正结果**
> ｜触发：CO-11 handoff §8-1「联立推导：connector 列分配器 × chip 侧 pair 行选择，输出新 32/32 通道分配（版本 bump）」
> ｜证据（只读探针 + 非执行者独立复核；冻结四源/canonical **未动**）：
> `tools/p3_v57_co10_west_fan_probe.py`（+`CO10_POLMODE` 旋钮，默认行为不变）
> → `m13_v57_co15_placement_geom.json`（`6f37af4b99dfd0ec`）
> → `m13_v57_co15_placement_verification.json`（`667a3ba65026b688`，**PASS 0 违规**）
> → `tools/p3_v57_co15_emit_allocation.py` → `m13_v57_co15_channel_allocation.json`（`CO15-ALLOC.1`，`8d33888be689a88f`）

## 0. 结论（三句）
1. **CO-11 §13 的 30/32 已收口为 32/32**：全部 32 页（西侧 16 + 东侧 16）**既无同层真交叉（proper-intersection），
   又净距全合规**；独立复核 320 via / 320 段 + 616 pad 场 **0 违规 PASS**。
2. 余 2 页（`PCIE_UP6/UP7`）的根因是 **In6 stub × 本页对面极性 In6 lane 的自叉**（非 connector 容量）；
   修法 = **方向感知 P/N lane 排序**（L2 闭式几何规则），单参数改动即消除。
3. **逐页混合 stub 层**（J4 下行组 `UP4..UP7` stub 留 In6）经 CO-11 §13.2-4 明确授权（L2 过孔策略允许逐页混合）；
   过孔数与口径与 `m13_v57_co11_spec_eco_annex` **逐项一致**（bandX 4 / bandY 6 / 总 320）。

## 1. 根因（UP6/UP7 自叉，CO-11 §13.2 的精确机理）
- CO-11 配置：J4 下行组（`UP4..UP7`，lane_y 46.818..50.197）stub 层 = **In6**，landing `ll=65.0`（lane 块之上）。
- 引擎/探针旧 `pol_off` 规则**按 pad 侧 P/N y 上下序**定 lane 侧偏移（`p3_v57_w3_constructive.py:203` 注释「防对内自交叉」）。
  但该规则在「stub 竖直跨越 lane 块」时**反向失效**：
  - `UP6`：pad `P=(92.05,50.28)`、`N=(92.35,49.76)` ⇒ `d=N.y−P.y<0` ⇒ 旧规则令 `P_ly=ly+0.25 > N_ly=ly−0.25`；
    而 `lx_P=61.6 < lx_N=62.2`。⇒ N 的 In6 stub（x=62.2，y∈[48.821,65.0]）**穿过本页 P lane**（y=49.321，x∈[61.6,92.0]）⇒ `cross_intra`（实测）。
  - `UP7` 同理（P lane y=50.4475 穿 N stub x=64.0，y∈[49.9475,65.0]）。
- 机理总结：**当 stub 层 == lane 层（In6）时，竖直 stub 与对面极性水平 lane 必交**，其成立条件是
  `lx_对侧 ∈ [lx_本侧, vx_本侧] 且 本侧 lane y ∈ 对侧 stub y 区间`。旧规则只保证 pad 侧序一致，未保证 lane 侧「stub 在 lane 外侧」。

## 2. L2 裁定：方向感知 P/N lane 排序（`CO10_POLMODE=lx`）
**规则（闭式，仅 `WEST_MCIO_TO_CHIP`；默认关闭）**：
```
ll = FAN_Y[row_group]（本组 landing y）; ly = lane_y（R2 分配）; big = landing lx 较大的极性
若 ll > ly（stub 朝上）：pol_off(big)=+POL_OFF（上层 lane），pol_off(小)=−POL_OFF
若 ll < ly（stub 朝下）：pol_off(big)=−POL_OFF（下层 lane），pol_off(小)=+POL_OFF
```
- **几何依据**：设 `lx_big > lx_small`。stub 朝上时，big 极性的 stub（x=lx_big）会落在 small 极性 lane（x∈[lx_small, vx_small]）的 x 域内
  ⇒ 必须令 `small` 极性的 lane 位于 stub 起点**之下**（`ly_small = ly−0.25 < ly_big`）方能不相交；朝下时对偶。
- **不改 pad 侧 F.Cu 逃逸**（pad→via1 几何与极性序无关）；**不改 lane 序/O4 长度结构以外**的量。
- **stub 层保持逐页混合**：J3 上/下行组 + J4 上行组 = **In2**（CO-09 §3 规范）；J4 下行组（UP4..UP7）= **In6**（CO-11 §13.2-4
  授权的局部拓扑特例，避免 In2 stub 24-clique 容量边界）。landing 仍为 `In6↔In2↔F`（**安全 hop 不破**）。

## 3. 联立构造（确定性单遍，零搜索/零回溯；引擎 O(1) 消费）
| 子问题 | 实现 | 性质 |
|---|---|---|
| **connector 列分配器** | `_lx_separate`：按 (stub 层, lane_y) 序，对 y 区间重叠的同层 stub 贪心取最小 \|δ\|（δ 网格 0.6）使页间 lx ≥0.525 | 区间图贪心着色（色板=中缝列），闭式单遍 |
| **chip 侧 pair 行选择** | pair 域 v1.5（`6662e0089c88b091`）+ 固定键序（到闭式目标 `pair_dist/pad_y` 的 L1）取首可行行 | 单遍 argmin + 可行性谓词 |
| **联立** | 二者共享**同一 `check()` 谓词**（vv/vt/tt/全跨距 via 桶/proper-intersection/616 pad），一页仅在**两侧同时可行**时落位 | 谓词即耦合 |
| **落位序** | canonical 逆序 `(corridor, conn_ref, band, page_id)`（A1.2 引擎内部规范序） | 序无关性由引擎排序保证 |

- 探针 `--order rev` = canonical；`CO10_POLMODE=lx` 为唯一新增旋钮（默认 "" 复现 CO-11 的 30/32，**行为不变**）。

## 4. 结果与独立复核
| 项 | 值 |
|---|---|
| 落位 | **32/32**（`PROBE_PLACED_ALL`） |
| 几何产物 | `m13_v57_co15_placement_geom.json`（`6f37af4b99dfd0ec`） |
| 复核器 | `tools/p3_v57_co11_placement_verify.py`（非 producer，全对全重算） |
| 复核结果 | `n_vias=320, n_segs=320, n_violations=0, verdict=PASS`（`667a3ba65026b688`） |
| 判据含 | vv/vt/tt（含 pad 邻接阈值）/via×pad/seg×pad（616 场，豁免本页 4 pad）/**proper-intersection 交叉**（§12 教训） |
| 同层真交叉计数 | **0** |

## 5. 余量（诚实，供 DFM 门参考）
| 量 | 实测最小 | 判据 | 余量 |
|---|---|---|---|
| via↔via（异网/同页异极性） | 0.5323（UP7 P/N） | 0.525 | +0.0073 |
| via↔track（非 pad 邻） | 0.5000（UP5 J2 P/N In6） | 0.4525 | +0.0475 |
| via↔track（pad 邻） | 0.3841（DN4 P/N F.Cu） | 0.3525 | +0.0316 |
| track↔track | 0.3841（DN4 P/N F.Cu） | 0.38 | +0.0041 |
| via/seg↔pad（非本页） | 0.0830（UP0 J2 N via） | 0.075 | +0.0080 |
- **tt/vv/pad 余量偏薄**（+0.004…+0.008）；不违判据，但 DFM 门（G7）须以 shop 口径复核（可能触发 DRC 边际规则）。
  东侧几何**未受本次西侧改动影响**（`CO10_POLMODE` 仅西侧生效），故东侧余量不变。

## 6. 序鲁棒性（A1.2 相关）
| 探针序 | 落位 |
|---|---|
| `rev`（canonical） | **32/32** |
| `engine`（canonical 正序） | **32/32** |
| `laneidx` | **32/32** |
| `fewest`（非 canonical，启发式） | 31/32（UP0/out_J2） |
⇒ canonical 序（引擎内部强制序）为 32/32；非 canonical 启发式序不是引擎口径，不作验收。

## 7. 与 ECO 的一致性（`m13_v57_co11_spec_eco_annex`）
| 项 | ECO 目标 | CO-15 实测 |
|---|---|---|
| bandX（west-up / east-dn）via/线 | 4 | **4** |
| bandY（west-dn / east-up）via/线 | 6 | **6** |
| via 总数 | 320 | **320** |
⇒ ECO 的 4/6/320 与 CO-15 几何**逐项一致**；引擎 rev bump 须**同批**应用 ECO（SPEC v-bump + validator 5→6 + 引擎阈值），否则被冻结断言挡下。

## 8. 红线遵守
只读探针 + 只读消费（manifest/lane_frame/pair v1.5/pad field/drc_rules）；冻结四源**原件未改**；
canonical `m13_v57_w3_joint_assignment.json`（W3-CN.30 `05f7bd10ab3b45b6`）**未动**；引擎**未改**；零坐标搜索；
未放宽任何阈值（A-CN.9 vt 0.4525 / vv 0.525 / tt 0.38 / skew）；POL_OFF=0.25 已在探针落地（引擎落地须同批）；无 partial pass；无 sign-off。

## 9. 下一周期输入（不变）
O4 蛇形预算重派生（新 lane_y 分布）→ ECO 同批应用 → 引擎 rev bump（CO-10 §10.3 八项 + CO-15 拓扑/工件消费）→
一次求解（`FEASIBLE_ALL ∧ crossings=0 ∧ A-CN.9 0/0/0 ∧ skew≤0.15 ∧ wall≤120s`）→ G4→G5→G6→G7（目标 DFM new=0）。
