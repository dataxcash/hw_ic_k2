# CO-41 — 实施记录：ECS-001 落地（REFCLK J2 侧单次换层 transit）+ DFM 实测 60→54 + **远端 J3/J4 为主因**（新证据）

> 2026-09-12｜性质：**L2 实施**（依 CO-40 `7be78b59cdff4380` 裁定与 ECS-001 规格）｜本件记"做了什么 + 实测到什么"
> 引擎 rev **W3-CN.39**｜图纸 canonical `m13_v57_w3_joint_assignment.json` `e43c17a9cb9161d8`

## 1. 改动（3 处，皆版本化）
| 层 | 文件 | 改动 |
|---|---|---|
| 引擎 | `tools/p3_v57_w3_constructive.py` | ① `refclk_place()` 新增**3D `nodes`** 发射（`paths` 保持不动，供验证器 V7）；② 新增 `_in2_columns()` + `refclk_transit_nodes()`（ECS-001 闭式：via1 落两列缝、via2 落 In2 缝中心、被列端封堵则绕端部）；③ `refclk_place` 调用点**移到 `co16_build_routes` 之后**（须消费 `_CO16_PTS` 的 In2 stub 列）；④ spec 指针 → `spec-rev-3`、`REVISION_CO16` → `W3-CN.39` |
| L4 | `tools/p3_v57_l4_apply_drawing.py` | REFCLK 分支优先用 `nodes` → `collapse()`（复用数据页同机制，自动落 via）；无 `nodes` 时回退 2D `paths` |
| L4 验证 | `tools/p3_v57_l4_validator.py` | 同上（独立重算口径与构造一致） |
| 验证器 | `tools/p3_v57_w3_constructive_validator_v2.py` | frozen spec 指 `spec-rev-3`（`2d6dbd8bd8d667d7`） |

**已试并回退（记录在案，勿重试）**：把内 N 轨偏移由 0.19 提到 0.31（为使 via#2 距 P 轨 ≥0.4525）⇒ **A-CN.5a FAIL**（N 轨 y=46.21 落进 C80 元件体 keepout 盒）⇒ 已回退至 0.19。⇒ 该修法须先由 **witness v2** 校正 keepout（现 keepout 仅含元件体、缺铜包络）。

## 2. 门禁实测（全链本次实跑）
| 门 | 结果 |
|---|---|
| W3-CN.39（引擎） | **FEASIBLE_ALL**；`A-CN.1..9` 全 PASS（crossings 0/0、work 546/546、A-CN.9 净距套件 0）；sha `e43c17a9cb9161d8` |
| W4（独立验证器 v2） | **PASS**：G-M1..6 全 True、A1.2 序无关 True、A1.3 0 viol、A1.4 True、frozen True |
| L4（板构造 + 验证） | **PASS**：L4-A..E 全 True、viol 0；segs 2408→**2413**、vias 248→**252**（= 每 N 线 +2 via，恰合 ECS-001） |
| L5 | FAB ok｜SI **PASS**（skew 0.0031）｜DFM **FAIL**：**new 60 → 54** |

DFM 变更明细：`shorting_items 9→5`、`solder_mask_bridge 38→36`、`clearance 8→8`（+2 引入 / −2 消除相抵）、`tracks_crossing 5→5`。
明细件：`m13_v57_co41_refclk_drc_after.json`（54 条逐条坐标）。

## 3. 残余 54 的构成与根因（**关键新证据**）
54 条**全部** REFCLK 相关，但**仅 2 条在 J2 pad 场**，**52 条在远端（J3/J4）与西侧**：
- `solder_mask_bridge` **36** = REFCLK 二对 F.Cu 轨沿 **J3/J4 的 A 排（y=45.75 / 61.45）平行穿越整个 A 排 pad 场**（x≈58.3…64.9），与 J3 A1..A10 / J4 A13..A19 逐 pad 桥连 ⇒ **远端接入形态错误**（应从两排间自由带接入并垂直于排进入 A11/A12）；
- `shorting_items` **5** = REFCLK vs J3/J4 pad（A5/A2/…）+ **REFCLK0_P/N 对内短路**（对内边距 0.175 == 净距阈值，KiCad 判 shorting ⇒ 须 ≥ ~0.45）；
- `tracks_crossing` **5** = REFCLK P/N 互交（J4 端 P 跨 N）+ REFCLK vs `DN_OUT*_MCIO`（J3/J4 接入段）；
- `clearance` **8** = 含 REFCLK1_N vs **C82[P3V3]** pad、P/N 互距、**N via#2 vs P 轨**（via 需 0.4525、实测 0.38）、J2 **P 侧 0.19 jog vs GND pad 9/27**（gap 0.1325 < 0.175）。
⇒ **CO-38「J2 内列墙 = D3a 主因」不成立**：J2 侧确为真缺陷但只占少数（ECS-001 已消除 shorting −4、mask −2）；**主因是远端 J3/J4 A 排穿越**，属 CO-38/见证件**未覆盖**的接入窗口（witness v1 只有 `j2_exit` 类比项，无 J3/J4 端 `strip_window_y`/垂直接入约束，且 keepout 无铜包络）。

## 4. 下一步（L2，同一自裁范围）
1. **远端 transit**：J3/J4 端改用两排间自由带（J3 `y∈[43.8775,45.1225]`、J4 `y∈[62.0775,63.3225]`）作接入窗口，**垂直**进入 A11/A12，禁止沿 A 排平行。
2. **对内间距** 0.38 → ≥0.45（消对内 shorting）；须同时解决 REFCLK0_N 轨 y≈46.1 撞 C80 元件体 keepout ⇒ 依赖 **witness v2 keepout 校正**（含铜包络）。
3. J2 **P 侧 jog 0.19 → 0**（P 沿 pad 行直出，消 vs pad 9/27）。
4. N via#2 距 P 轨 ≥ **0.4525**（或 via 偏离轨后在 F.Cu jog 回轨）。

## 5. 回滚
引擎/构造函数/验证器回退到 `W3-CN.38`（`bf14ad0` 引擎版），`FROZEN spec` 指回 `spec-rev-2`（`0a7ad112ac4c57e3`），删 `SPEC_k2_v4.spec-rev-3.json`；冻结四源始终未动。
