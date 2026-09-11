# 变更单 — SPEC-REV-2 应用记录（ECO：过孔策略口径）

> 2026-09-12｜依据 `m13_v57_co11_spec_eco_annex.json`（`b859ab84bea7836b`）+ CO-18 裁定（`930a25aa567f6332`）
> ｜权限：L2（过孔策略/过孔预算 = L2，见 CO-08 §(A)/(B)）

## 1. 应用方式（原件不动）
- **新版本化文件**：`pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-2.json`（`0a7ad112ac4c57e3`）。
- **原 `SPEC_k2_v4.json` 逐字节未动**（`0bd52ed48e720b8c`）；本 ECO 为其**版本化后继**（`_spec_rev_2` 卡内记录 `spec_sha256_before` 与 rollback）。

## 2. 增量
| path | from | to |
|---|---|---|
| `spec_version` | `1.1.spec-rev-1` | `1.1.spec-rev-2` |
| `vias.high_speed.max_per_line` | `2` | `{"bandX_escape_In2":4,"bandY_escape_B":6}` |
| `vias.high_speed_via_count` | `300` | `{"measured_probe":320, "note":..., "basis":"CO16-ALLOC.1 21ae78f8276d8df4"}` |

## 3. 同步更新（同批）
- 引擎 `tools/p3_v57_w3_constructive.py`：`F["spec"]` → spec-rev-2；`FROZEN_SHA["spec"]` → `0a7ad112ac4c57e3...`；`REVISION_CO16 = "W3-CN.34"`。
- 验证器 `tools/p3_v57_w3_constructive_validator_v2.py`：`FROZEN["spec"]`/`FROZEN_SHA_PREFIX["spec"]` → spec-rev-2；A1.3 `max_vias_per_net 5→6`（bandY 6 via/线）；A1.2 按工件 shape 跑；A1.4 修订序取值按 shape；G-M4 增 co16 消费保真分支。
- `TAG_POLICY.md` §5 的「四源期望 sha」仍以原 `SPEC_k2_v4.json 0bd52ed48e720b8c` 为准（原件未动）；引擎输入为 ECO 后继版本。

## 4. rollback
删除 `SPEC_k2_v4.spec-rev-2.json`，令引擎/验证器 `FROZEN spec` 指回 `SPEC_k2_v4.json`（`0bd52ed48e720b8c`）。
