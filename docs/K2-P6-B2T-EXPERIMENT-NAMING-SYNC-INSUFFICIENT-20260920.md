# K2 · **B2-T 实验：命名同步不足（13 项隐藏失败 = 几何/代际漂移）** · 2026-09-20（只读 · 真源零改动）

> 实验件：`k2/tools/k2_p6_b2t_naming_sync_experiment_v1.py`（全部落在 `/tmp/opencode/shadow_b3`）
> 前件：`K2-P6-SHADOW-VERIFICATION-BATCH2-20260920.md` §4（13 项清单）· `HIDDEN_FAILURES_TRIAGE_v1.json`（命名分歧实证）

## 1. 假设与做法（最小修复稿）
假设 = 「13 项失败系走廊命名漂移（测试/alloc 用旧 id，SPEC 用新 id）⇒ 同步命名即可清」。
草案（**仅影子**）：① 把遗留 `channel_alloc_v2` 的走廊串**整体翻译**为现行 id（`J2_TO_U→EAST_CHIP_TO_J2`、`U_TO_MCIO→WEST_MCIO_TO_CHIP`，含 `channel` 串，旧 id 残留 **0**）；
② 把测试里 **5 处**真实 SPEC 的走廊查找改为**按角色解析**（`_corr(m, role)` / `_cid(role)`，兼容双名）；③ 断言中的旧 id 字符串改为兼容集。

## 2. 结果：**命名同步不足**（13 → 13，逐项不变）
```
13 failed, 43 passed, 12 skipped      ← 与未做命名同步时**完全相同**
```
（对照：未打草案时同为 13 failed / 43 passed / 12 skipped ⇒ 该 13 项**不是**命名/查找问题。）

## 3. 决定性证据：**几何代际漂移**
现行 `SPEC_k2_v4.json` 两条走廊的 `x_range`：
| 走廊 | x_range | bands |
|---|---|---|
| `WEST_MCIO_TO_CHIP` | **[65.05, 82.35]** | 3 |
| `EAST_CHIP_TO_J2` | **[105.25, 132.65]** | 3 |

而**当前 8L 板的 `PCIE_DN0_P` pad 位于 x = 84.85** —— **正落在两走廊之间的空隙**（82.35 … 105.25）。
模型按**几何**选走廊（`probe_escape_capacity` → `_corridor_for_x(x_min, x_max)`），该 x **无走廊命中** ⇒ 返回 `NO_CORRIDOR`
⇒ 断言 `status in ("SOLVED","BLOCKED")` 必失败；其余同族失败（`KeyError:'left'`、`StopIteration` 之外仍存、`INFRA_ERROR`、`未全解` 等）同源。

## 4. 结论与归属
1. **13 项失败 ≠ 命名问题**：是**遗留测试期望（旧代际板/走廊几何）与新真源（现行板 + 现行 SPEC）不兼容**。
2. 该 13 项覆盖的是**旧探针/旧拓扑代际**的能力面；在新几何上要么**重基线**（改期望值 = 判据动作），要么**具名退役**（明确"不适用"）——**两条路都属监理自裁**（C-12：禁为变绿缩口径）。
3. 因此 B2-T 的正确提法不是"同步命名"，而是**「13 项 legacy-regime 测试的处置裁定」**：
   - (甲) **重基线**：按现行板+SPEC 重写期望（需给出"期望值来源"与覆盖度论证）；
   - (乙) **具名退役**：标注为 legacy regime、不计入回归网（并在 `results_template.json` 具名记录）；
   - (丙) **混合**：逐项择一（附清单）。
4. 命名分歧（§8/影响面件）**仍然成立且已定位**，但它是**另一个**问题（测试输入/判据期望集/遗留件），**不足以解释**这 13 项。

## 5. 复现
```
python3 /tmp/opencode/b3_draft.py                                  # 建 shadow_b3（翻译 alloc + 角色解析）
PYTHONPATH=/tmp/opencode/shadow_b3/shared AppDir/bin/python3.11 -m pytest -q \
    /tmp/opencode/shadow_b3/shared/eda_core/tests/test_hs_route_model.py
```
（真源零改动：`_shared`/`criteria/`/冻结四源/交付锚均未触；临时仅 `/tmp/opencode`。）
