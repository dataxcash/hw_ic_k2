# CO-16 — 【L2/L3】东侧重派生收口：**全板 32/32 有效**（safe-hop / crossing-free / clearance-clean / O4 闭合）；**无需 ECO 修订**

> 2026-09-12｜裁判：ARCHER（L2 层角色/走廊/过孔策略/等长，自裁）｜性质：**变更单 + 正结果**
> ｜触发：CO-15 §10/§11 判「东侧在 CO-09 拓扑下 O4 不闭合」后，续做东侧联合重派生（handoff 路径 B）。
> ｜证据（只读探针 + 非执行者独立复核；冻结四源/canonical/引擎 **未动**）：
> 探针 `tools/p3_v57_co10_west_fan_probe.py`（`CO10_EASTSPLIT=in2c` + `CO10_J2STEP=0.6`）
> → `m13_v57_co16_placement_geom.json`（`e640f0a26c7ff112`）
> → `m13_v57_co16_placement_verification.json`（`c6bb5b0ea430d0c7`，**PASS 0 违规**）
> → `tools/p3_v57_co16_emit_allocation.py` → `m13_v57_co16_channel_allocation.json`（`CO16-ALLOC.1`，`21ae78f8276d8df4`）
> → `tools/p3_v57_co16_o4_budget.py` → `m13_v57_co16_o4_budget.json`（`CO16-O4.1`，`c33e035a2d3c8939`）

## 0. 结论（四句）
1. **全板 32/32 有效**：西侧 CO-15 + 东侧 CO-16 几何，`n_vias=320 / n_segs=320 / n_violations=0 PASS`（含 proper-intersection + 616 pad 场）。
2. **全 via 安全 hop**：0 条越层（全部 ∈ {F↔In2, In2↔In6, In6↔B}）⇒ 消除 CO-09 §4bis 的 via-barrel×跨层 track 结构根因。
3. **过孔口径不变**：bandX=4 / bandY=6 / 总 320（与 `m13_v57_co11_spec_eco_annex` **逐项一致**）⇒ **无需 ECO 修订**。
4. **O4 双段蛇形闭合**：lane-run + stub 双段 meander ⇒ 东侧 slack ≥1.91mm、西侧 ≥8.55mm（`CO16-O4.1` 两走廊 CLOSED）。

## 1. 东侧根因（CO-15 §10 的精确化）
- CO-09 §3 令东侧 **stub 亦落 In2**（land 必须 `In2↔F`）。东侧 up/dn stub 的 y 区间**跨带重叠**
  ⇒ 32 个 In2 stub 的**区间图最大深度 22 / 每侧色数 11**。J2 落列被展开 ⇒ `|ΔL|` 超蛇形容量（DN3..DN7 短 0.65–7.71mm）。
- 单纯换层（up stub→In6）不成立：东侧 lane x-span = `[vx,lx]`（lx>vx）⇒ 该 stub 落在所有 `lx_p>lx_q` 的 lane x 域内，**跨页必交**
  （探针修正 `cross_placed` 后 25/32；独立复核 FAIL 56）。up stub→B 亦不成立：`B↔In2` land 越 In6（不安全 hop），
  改 `B↔In6↔In2↔F` 则需 8 via/线。

## 2. L2 裁定（两件，均闭式/单遍）
1. **东侧 stub 全留 In2（CO-09 §3 规范，不改层）**；改用 **J2 列 = 区间图确定性贪心着色**
   （`CO10_EASTSPLIT=in2c`）：每侧独立，按 y 区间左端排序贪心着色 ⇒ 色数 = **11**（每侧），
   列 x = `131.65−0.6k`（inner 侧）/ `136.0+0.6k`（outer 侧）。
   - 判据修正（本会话）：着色区间须按 `±VV/2` 扩张，否则「两条 landing via 同列且 Δy<0.525」会被漏判（实测 DN3/DN5 失败根因）。
   - **O4 感知色值重排**：真着色对色值**置换不变**，按组内最大 chip-pad x 降序重排 ⇒ 大 vx 页取小 offset（R 大、ΔL 小）。实测 tightest 由 +8.03 → +4.39（Dm 单位）。
2. **O4 双段蛇形**：东侧 lane-run 容量不足（DN1 短 1.82mm），把 45° 单侧蛇形扩展到**第二段 stub 竖段**：
   `capacity = (R_lane−1 + max(0,R_stub−1))·(√2−1)` ⇒ 东侧 16 页全闭合（min slack 1.91mm）。西侧容量充裕，双段模型不改变其结论。
   - 属 L3 蛇形预算（L2 等长窗口已裁），实现期须与引擎 `meander_run` 双段化同批。

## 3. 结果与独立复核
| 项 | 值 |
|---|---|
| 落位 | **32/32**（rev/engine/laneidx 三序一致） |
| via/线 | bandX(In2 escape/stub)=**4**、bandY(B escape/In2 stub)=**6**、west J4L(In2 escape/In6 stub)=**4**；总 **320** |
| 安全 hop | 越层 via = **0** |
| 复核 | `n_vias=320, n_segs=320, n_violations=0, PASS` |
| 同层真交叉 | **0**（含跨页） |
| O4 | 东侧 min slack **+1.91mm**；西侧 **+8.55mm**（`CO16-O4.1`） |
| 序鲁棒 | `rev`(canonical)/`engine`/`laneidx` = 32/32 |

## 4. 与 CO-15 / ECO 的关系
- **西侧**：CO-15 几何**逐字节不变**（探针改动对 CO-15 行为保持；`m13_v57_co15_*` 四件 sha16 未变）。CO-16 全板工件**取代** CO-15 全板工件（CO-15 的东侧页为过渡模型）。
- **ECO**：CO-16 的 4/6/320 与 `m13_v57_co11_spec_eco_annex`（bandX 4 / bandY 6 / via 320）**完全一致** ⇒ 引擎 rev bump 只需**同批应用该附件**，无需再改数值。
- **POL_OFF=0.25** 已在探针落地；引擎落地须同批。

## 5. 红线遵守
只读探针 + 只读消费；冻结四源**原件未改**；canonical `m13_v57_w3_joint_assignment.json`（W3-CN.30 `05f7bd10ab3b45b6`）**未动**；引擎**未改**；零坐标搜索（着色为闭式贪心、O4 重排为置换）；未放宽任何阈值；无 partial pass；无 sign-off。

## 6. 下一周期输入（引擎 + 门控）
引擎 rev bump（西 CO-15 + 东 CO-16 拓扑 + 工件消费 + 双段蛇形）→ ECO 同批 → 一次求解
（`FEASIBLE_ALL ∧ crossings=0 ∧ A-CN.9 0/0/0 ∧ skew≤0.15 ∧ wall≤120s`）→ G4→G5→G6→G7（目标 DFM new=0）。
