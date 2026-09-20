# K2 · **N-4 批 6 v4 落件报告**（#K2-48 放行）

- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/BATCH6_N4_LANDING_REPORT_20260921_v1.json`（sha16 `aeb171ea979dea5a`）
- 放行件：**#K2-48** N-4 · 补丁 `BATCH6_LANDING_CANDIDATE_v4.patch`（sha16 `3ded8584bb74461f`）
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 一句话
批 6 v4 **已落件**：`_shared/eda_core/hs_route_model.py` `dcd1f65f…` → **`c9e1c3b4ca208482`**（= 落件目标，逐字节命中）；**一笔提交 `ea2b746`**（`ic_hw_eda` main，已推 origin）；**双 `_shared` 树同 commit id**；**四验全 PASS**；**K1 真值 1/8 → 2/8**。

## 1. 落件与回滚
| 项 | 值 |
|---|---|
| 提交 | `ea2b746241d85fdd…`（`_shared` / main / 已推） |
| 回滚点 | **`02459f5`**（父提交）；`git -C _shared checkout -- eda_core/hs_route_model.py` 或 revert |
| 变更面 | **仅** `eda_core/hs_route_model.py`（+164/−14） |
| k2 指针 | `11d72b8`（chore(batch6): 共享层落件）· 容器根 `7073e27` |

## 2. 四验读数（#K2-48 收尾四验）
| # | 验 | 读数 |
|---|---|---|
| ① | `verify k2` | **preflight + 3 PASS** |
| ② | canonical 19（全新 `--drc-work-dir` ×2） | **19 OK / 0 FAIL · PASS** · verdict **`190b73be0f728a56`** · 两跑**逐字节同** · 且与**在册签认件逐字节同** |
| ③ | `--expect-patched` | **PASS** · A 4/4 · B verify PASS · C K1 14/K2 14 **回退 0** · D 14/14 · pytest 2F/61P/12S · hidden=2(=C1/C2) |
| ④ | K2 零回归 | ✓（C 回退 0 · D 与 pristine 逐项同） |

## 3. K1 真值（增益兑现）
| 段 | 落件前 | 落件后 |
|---|---|---|
| `TX0/output` | SOLVED | SOLVED |
| **`RX0/input`** | INFEASIBLE | **SOLVED**（track_P 21.01 / track_N 20.51） |
| 合计 | **1/8** | **2/8** |

**层合法违规 0**（`k1_layer_legality_audit_v1.py`：`solved_segments=2` · `violations=[]`）。

## 4. 偏差与诚实登记
1. **`git apply` 层级**：runbook 写 `-p1` ⇒ 在 `_shared` 内解析为 `_shared/_shared/…` **必失败**（dry-run 实测）⇒ **正确为 `-p2`**，已按 `-p2` 落件。
2. **runbook 未载『双树同步』**：`k2/_shared` 是**独立树**（非 symlink）⇒ 以『root 提交 → k2 `fetch`+`checkout` 同 commit』实现 **双树同 `ea2b746`**（逐文件同）。
3. **确定性口径**：K1 求解 summary 两跑**仅 `solve_time_s` 不同**（墙钟），其余（`input_fp`·`shared_seg_count`·各段结果）**逐字节同** ⇒ 求解输出确定性成立；该 timing 字段为**工具既有**（落件前复跑亦记录），非本批引入。canonical 19 verdict 两跑**全字节同**。
4. **未做**（依放行边界）：未改 `criteria/`／SPEC／原理图／生成器；**未重建交付包**（交付锚未动）；未新增检查齿；未派 WORKER。
