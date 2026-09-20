# K2 · **P6/批 2 · 影子预验证报告**（真源零改动 · 2026-09-20）

> **性质**：授权前把「批 2 补丁集」验证到**一次跑成**——在 `/tmp/opencode/shadow/` 建框架影子副本并施加补丁集，跑同一套验收 + 控制组归因。**真源仓库零改动**（只读 `k2/_shared`）。
> 机读真源：`pm_gate/artifacts/k2_v4/P6_execution/SHADOW_VERIFY_v1.json` sha256 **`844f2266…`**（**两次连跑逐字节同**）
> 复现（容器根 `ic_hw`）：
> ```bash
> PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p6_shadow_verify_v1.py
> ```

## 1. 补丁集（7 组 · 11 项；含本轮**新发现**两项）
| 组 | 载体 | 内容 |
|---|---|---|
| F-1 / B2-4 | `pm_gate/check_l1.py:193` | `RULES_DOC` → `<框架根>/docs/PCB_DESIGN_RULES.md` |
| B2-3 | `check_l2.py`(9) · `check_l3.py`(4) · `check_qa.py`(2) | `artifacts.read_text/list_dir` 注入 `project=_proj()`（T13 口径） |
| B2-3a | `check_l3.py:26` | 去硬编码 `SPEC_k2_v4.json` ⇒ `config.spec_name(_proj())` |
| B2-3b | `check_qa.py:35` | `spec_name()` 空参 ⇒ `spec_name(_proj())` |
| **B2-3c（新 F-2c）** | `check_qa.py:24` | 板路径 `board_abspath()` 空参 ⇒ `board_abspath(_proj())`（**真源基线未暴露**：G4.1 先在 SPEC 处失败，被掩盖） |
| **B2-3d（新 F-2d）** | `gates.py:141` | `scheme_closure_check` 产物读取注入项目维度（⇒ K1 G2.6 由 FAIL 转 PASS） |
| F-3 / B2-3c | `closure_check.py:110-113` | 框架相对默认值 ⇒ 项目根 + **项目 spec 名**（原路径目录**不存在**） |
> **定性**：F-2 的实际范围**大于**静态普查（`SPEC_k2_v4` 站点 43 处）——核心是**「默认项目」调用面**；本报告把闸路径内该类调用**全部**覆盖（check_l1/2/3/qa + gates + closure_check）。

## 2. 门禁增量（同套验收：真源基线 ↔ 影子）
| 项目 | 真源基线 | 影子（补丁集） | 变化 |
|---|---|---|---|
| **K1** | 5 PASS / 13 FAIL | **12 PASS / 6 FAIL** | **+7 PASS**（G1.5 · G2.1–G2.6）· **零回退** |
| **K2** | 12 PASS / 6 FAIL | **13 PASS / 5 FAIL** | **+1 PASS**（G1.5）· **零回退** |

**剩余 FAIL 已从「工具错误」转为「真实判定」**（这正是修复生效的证据）：
| 门 | K1 影子读数 | K2 影子读数 | 定性 |
|---|---|---|---|
| G3.1 | `SPEC 缺顶层字段 ['capacitor_walls']` | `SPEC.corridors 缺字段 ['J2_TO_U','U_TO_MCIO']` | **判据侧**（字段/期望集含 K2 专有键或旧名）⇒ 须监理裁定 |
| G3.2 | `executor_constraints.md 缺关键声明 'SPEC_k2_v4.json'` | PASS | **判据侧**（内容期望写死 K2 spec 名）|
| G3.5 | `无冻结签名：SPEC 缺 layer_plan.wp1_escape_nets_meta.fingerprint` | 同左 | **门已可跑** ⇒ 真实判定（K1 未到 WP1 冻结；K2 现行 rev-52 无该指纹 ⇒ 与历史 PASS 的判定源不同，**须监理确认判定源**）|
| G3.3 | 缺 `buildability.md` | PASS | **K1 真缺口**（项目侧） |
| G4.1/G4.2 | `k1_v1.kicad_pcb 尚未按 SPEC 布线` | `k2_v4.kicad_pcb 尚未按 SPEC 布线` | **真缺口/对象选择**（K2 受审板为 `l7`；G4 门用 project.yaml 的 `k2_v4.kicad_pcb` ⇒ **对象口径须监理确认**） |
| G2.6 | PASS | FAIL（`escape_closure_analysis.md` 无 PASS/PARTIAL 判定） | K2 自身状态（与真源基线一致，非回退） |

## 3. **22 个 skip 解锁实验**（关键结论：**不是一行就能白捡**）
`test_hs_route_model.py` 原 34 skipped 中 22 个由 `K2V4_REAL_BOARD` 恒缺导致。实验：影子内只改该锚，跑同一测试。

| 锚候选 | 结果 | 说明 |
|---|---|---|
| `k2/k2_v4.kicad_pcb`（名字最直观） | **1 failed / 21 errors / 13 passed** | 缺兄弟件 `k2_v4.kicad_pro` ⇒ 模型构造即抛 `FileNotFoundError` |
| `k2/k2_v4_8L.kicad_pcb` | **13 failed / 43 passed / 12 skipped** | 有 `.kicad_pro` 兄弟件 ⇒ 用例**真跑** |
| `k2/hw/k2_v4_8L.kicad_pcb`（冻结设计源） | **13 failed / 43 passed / 12 skipped** | 与上行**完全一致** ⇒ 失败**与锚选择无关** |

⇒ **22 个 skip 里 9 个真通过、13 个失败**；「解锁 22 ⇒ 白得 22 项回归覆盖」的假设**被实测否证**。
（余 12 个 skip = `/tmp` fixture `k2_m9demo`，与本议题无关。）

## 4. 13 项**既有隐藏失败**（原被 skip 掩盖 · 均属 `hs_route_model` 域）
| # | 用例 | 失败形态 |
|---|---|---|
| 1 | `test_probe_escape_capacity_dn0` | 期望 `NO_CORRIDOR`，实得 `SOLVED/BLOCKED`（**契约漂移**） |
| 2 | `test_probe_reports_via_gap_fact` | `KeyError: 'left'`（**返回结构漂移**） |
| 3 | `test_capacity_regions_derived` | 区域集 `{J2_region, MCIO_region}` ≠ 期望含 `U7_region` |
| 4 | `test_probe_region_capacity_structure` | `INFRA_ERROR` 不在 `(CAPACITY_OK, INSUFFICIENT)` |
| 5 | `test_corridor_clear_span` | `assert 2 == 4`（走廊计数） |
| 6 | `test_capacity_map_persist` | `StopIteration`（持久化/查询无返回） |
| 7 | `test_chain_no_pn_zero_spacing` | 期望 `SOLVED`，实得 `INFEASIBLE` |
| 8–11 | `test_flip_polarity_cross_rejected` · `test_drawing_only_refuses_no_node` · `test_correct_polarity_solves_clean` · `test_escape_deterministic_byte_identical` | 多次 `StopIteration`（flip/逃逸几何查询无返回） |
| 12 | `test_board_level_consistency` | `未全解`：`solve_all_v4` 在 8L 板上 **18 条链一条未解**（另含落板→DRC 硬关卡） |
| 13 | `test_link_topology_crossing_old_topology` | 链路集合 `['UP4'..'UP7']` ≠ 期望集（拓扑/链接口径） |

## 5. 控制组**归因**（防"修出来的回归"）
控制组 = **零 pm_gate 补丁**、仅同一测试锚 ⇒ **13 failed / 43 passed / 12 skipped**，与补丁组**逐计数相同**
⇒ **批 2 补丁集引入 0 个测试回归**；13 项失败是**在此之前就存在、被 skip 掩盖**的缺陷。

## 6. 结论与处置
1. **补丁集可施工性已验证**：K1 +7 PASS、K2 +1 PASS、**零回退**、**零测试回归**；授权到位后可照此实施。
2. **`skipped 不得充绿` 门必须保留**（B2-1/B2-2 fail-closed 条款）：本实验正是该条款的价值证明。
3. **13 项隐藏失败纳入批 2 triage**：定为「引擎真缺陷」还是「期望漂移」——**期望值类归监理裁定**（C-12 禁为变绿缩口径）。
4. **新增两项须并入 B2-3**：F-2c（板路径空参）、F-2d（`scheme_closure_check` 项目维度）。
5. **须监理裁定的判定源/期望值**：G3.1 字段集与走廊期望 · G3.2 内容期望 · G3.5 判定源（rev-52 vs plain）· G4 施工对象（`l7` vs `k2_v4.kicad_pcb`）。

## 7. 红线与零改动声明
真源 `_shared`/`criteria/`/冻结四源/交付锚 **未动**（影子仅在 `/tmp/opencode`）；未派 WORKER；未改生成器/SPEC/原理图；`k2/_shared` 工作树洁净。
