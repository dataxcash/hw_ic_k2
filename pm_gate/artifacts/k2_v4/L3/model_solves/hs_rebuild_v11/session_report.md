# W6-C 停机报告 — hs_route_model --all-v4 真板求解（k2_v4, v11）

> 结论：**停机条件触发 — 17/18 INFEASIBLE**。按停机条款：证据表已落盘
> （`INFEASIBLE_evidence_table.md/.json`），**同输入禁重跑（仅 1 次求解）**。
> 零交叉契约（edge≥0.155）在全部 11 个 SOLVED 段上成立（0 违规）——类 A
> 修复有效性在真板再次确认；16 数据对全 SOLVED 未达成，缺口为预存逃逸构造
> 能力缺口（详见 §4/§5）。

---

## 1. 执行记录（单次，禁 -m，脚本路径）

- 求解器：`/home/fila/jqdDev_2025/ic_hw/_shared/eda_core/hs_route_model.py`
  （W6-B 后版本，含 `_layer_swap_escape`/`_dip_side`/`_escape_pair` LSWAP 形态）
- 执行：`cd /home/fila/jqdDev_2025/ic_hw/k2 && AppDir/sharun python3.11 /tmp/opencode/w6c_hs_rebuild_v11.py`
  —— 与 CLI `--all-v4` 分支逐字等价（同构造/同固定序/同累积障碍），额外每 base
  perf_counter 落盘 `per_pair_timing.json`（v10 per_pair_timing 同法：sum==global
  单进程证明，见 §3.3）。**进程 1 次，每对 1 次 `solve_chain_v4`。**
- 落盘：`hs_rebuild_summary.json` + `hs_rebuild/`（逐对 + 逐段 P/N json）+
  `per_pair_timing.json` + `INFEASIBLE_evidence_table.md/.json` + 本报告

## 2. 输入指纹（sha256 前 16）

| 输入 | 指纹 |
|---|---|
| 板 k2/k2_v4.kicad_pcb（**落位板 6c387dff**，卡0.5 电容墙复摆 32/32） | `6c387dff2d7ebdde`（= input_fp） |
| SPEC_k2_v4.json（走廊已修订 J2_TO_U[98.83,131.5]） | `7eaad223cf691f7c` |
| channel_alloc_v4/channel_alloc.json（18 键，未动） | `3f8fb6fc57715f0d` |
| drc_rules.json | `0a459839e15960b8` |
| route_model_config.json（chain_segments=None → alloc 分支） | `54b187f7e78254fc` |
| 求解器 hs_route_model.py（W6-B 后） | `049e0eec3373c6b0` |

## 3. 验收核对

### 3.1 16 数据对 SOLVED — **未达成（停机）**

- 18 对求解：SOLVED 仅 `PCIE_REFCLK0`（时钟对）；**16 数据对 + REFCLK1 全部
  INFEASIBLE**（UP0-7 ×8 + DN0-7 ×8 + REFCLK1 = 17）。
- 39 个 INFEASIBLE 段：30 极性交叉（flip=True 相向交叉，min_edge −0.205 < req
  0.175）+ 9 净空失败（对级对称逃逸无净空）。

### 3.2 P/N edge≥0.155（零交叉契约）— **通过**

- 全部 11 个 SOLVED 段经 `_path_pn_min_edge_pt`（width=0.205，spec 同源）复检：
  **0 违规**，最小 0.1553（DN2/DN4 input）。类 A 极性双几何门在真板再次成立
  （假 SOLVED 归零，交叉在构造期被拒）。

### 3.3 单对<5s（per_pair_timing.json）— **通过**

- max = 4.19s（UP6），18/18 对 < 5s；sum 46.929s == total 46.929s（单进程
  单次证明，无隐藏重跑）。确定性结构（固定候选序 + VGraph 兜底单次），无暴力求解。

### 3.4 等长<0.15 — **不适用（链级契约需整链 SOLVED）**

- 无整链 SOLVED 数据对 → 链级等长无从判定。SOLVED 段内 skew（0.44~2.21）为
  段级不完全信息，不作链级结论；REFCLK0 skew 2.21 等长不达标 = 既有事实
  （v10 同口径）。

## 4. 证据表（详见 INFEASIBLE_evidence_table.md，39 段逐条）

| 域 | 段数 | 类型 | 归属 |
|---|---|---|---|
| UP out_J2 左逃逸（cap 墙侧） | 7（UP0-6） | 极性交叉 @ 墙行 y≈39.3-40.2, x∈[100.99,116.88] | **预存 cap-wall 逃逸缺口**（W6-B 已知遗留，非新引入） |
| UP input（MCIO 侧） | 8（UP0-7） | 极性交叉 @ x∈[55,64], y∈[43,63] | 预存类A 逃逸构造缺口（v10 同构） |
| UP out_U7 | 8（UP0-7） | 净空失败 vs GND/P3V3/VREG1/2_U7 pad（pn_dist 0.375~0.4） | 预存（v10 同构） |
| DN out_U3 | 7（DN1-6 极性 + DN7 净空） | 极性交叉 @ U3 TX 列 | 预存类A（v10 同构） |
| DN out_MCIO | 8（DN0-7） | 极性交叉 @ MCIO 区 | 预存类A（v10 同构） |
| REFCLK1 input | 1 | 极性交叉 vs 已解 REFCLK0 段（In6.Cu） | 预存（v10 同构） |

> 归属判据：失败模式/坐标域与 v10（修复前 k2_v6 同模式：input 极性、out_U7
> 净空、out_J2 极性、out_U3/out_MCIO 极性）逐域一致；W6-B 新增形态未破坏既有
> 判定（REFCLK0 仍 SOLVED edge 0.1749 与 v10 0.175 一致）。**无 W6-B 回归证据。**

## 5. W6-B 生效证据（如实记录）

- **UP7 out_J2 右（J2 侧）逃逸 = LSWAP**（`escape.right.P.kind == "LSWAP"`，
  via (131.7,53.1)→(131.57,40.11) / N (134.05,53.1)→(132.17,40.49)，
  edge 0.1732，skew 0.4435）。v10 时代 UP0-7 out_J2 **全** INFEASIBLE → W6-B
  层换位为 UP7 解锁 J2 侧逃逸。**其余 UP0-6 out_J2 命中预存 cap-wall 缺口**（墙
  侧左逃逸，LSWAP 触发条件 |p.x−n.x|≥0.5 针对水平主导 pad 对，U7 TX 竖排
  P/N 对不满足 → 走 VIA 形态 → 极性交叉 @ 墙行）。**建议单独评估另开卡**
  （cap-wall 侧逃逸形态扩展）。

## 6. MUST NOT 合规

- ✅ 同输入仅跑 1 次（无 ≥2 次暴力迭代）；INFEASIBLE → 证据表落盘后停机
- ✅ 未改求解器/SPEC/alloc/config；未手补走线
- ✅ 未触碰 git，未 commit
- ✅ 执行用脚本路径（禁 -m 遵守）
