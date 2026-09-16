# §五 生成器源码改造 · 干跑证据 + 完整改动清单（v1；**含 1 项须监理裁的停机项**）

- **依据**：#K2-12 §五（改生成器源码**已放行**；硬约束 ①–⑥；**停机条款**：真源/符号库不足以驱动生成器 ⇒ 停线报监理，**不得硬编绕过**）。
- **方法（只读）**：`/tmp/opencode/k2p1/gen_dryrun_draft.py` —— **仅在内存**覆盖
  `BOARD`（→46mm `[33,79]`）、`SPEC_PATH`（→ rev-20）、`K2_REFS`（→ 真源 8L 板 42 refs），**未改任何源文件**，逐步观察阻断点。
- **边界**：未改生成器源码 / SPEC / 图 / 网表 / 板；草件仅 `/tmp/opencode/k2p1/`；未派 WORKER；P3 未开。

## 1. 干跑结果（三阶段，逐次收敛）

| 阶段 | 覆盖项 | 结果 |
|---|---|---|
| 0 | 无（原状） | rc=1：`[SPEC] 板框 [23,143]/[33,79] 与冻结板框 y=[33,71] 不符`（`F-8`，已知） |
| 1 | 上述 3 项（板框/SPEC 路径/`K2_REFS`） | rc=1：**`ValueError: [SPEC] anchor_fixes 含未知 ref C64`**（`k2_gen_v5.py:649`） |
| 2 | 追加：草拟 SPEC（`/tmp` 草件，仅删 `anchor_fixes.C64/C66`） | rc=1：**`KeyError: 'min_center_pitch_mm'`**（`:654`，`spec["capacitor_walls"]`） |

**阶段 2 的根因**：rev-1 的 D0 决策已把 **AC 电容墙判 `out_of_scope_for_mvp`**（原件移入 `appendix.capacitor_walls_original`）
⇒ canonical SPEC **不含** `capacitor_walls` 工作节；而生成器的 **AC 墙逻辑（`apply_spec_overrides` 段 + S7 `check_ac_pitch`）
是 6L／双颗时代死代码**（作用于 `C17–C32`/`C49–C64`，该 32 件已因「耦合内置」删除）⇒ 必须**结构性移除**，不是"补 SPEC 让旧代码继续跑"。

## 2. 完整改动清单（8 个代码点 + 1 个 SPEC 项，逐点带行号）

| # | 位置（`k2/tools/k2_gen_v5.py`） | 现状 | §五 要求 | 约束 |
|---|---|---|---|---|
| G1 | `:47 BOARD` | `y:[33,71]`（38mm） | → `[33,79]`（**46mm**） | §五 ② |
| G2 | `:40 SPEC_PATH` | 硬编码 `L3/SPEC_k2_v4.json`（6L） | → 经 `pm_gate.config.spec_name()` + `artifacts.path` 解析 | §五 ④（根因 F-14/N-05） |
| G3 | `:54–65 K2_REFS`（101 件） | 含 `U3/U7` 双颗 + `C17–C32/C49–C64` 外置耦合 + `C65–C90` | → 真源（**单颗 `U6`**，42 件；来源 = 真源导出而非字面表） | §五 ③ |
| G4 | `:114 OLD_REF_MAP`（`:238,:325` 使用） | `{"U3":"U7","U4":"U3","U6":"U4"}` 双颗命名重映射 | → 移除（单颗下 `U6` 不得被改名） | §五 ③ |
| G5 | `:355` | `REDR_DS160PR810` 热焊盘 `pad 65` 特判 | → 移除（该器件作废）；`U6`（`DS320PR1601`，354 球）如需 EP 规则另立显式规则 | §五 ③⑤ |
| G6 | `:584–598 check_ac_caps`、`:846` | 以 `C17–C32/C49–C64` 为对象的 AC 检查/遍历 | → 移除该 6L 专属检查 | §五 ③ |
| G7 | `:633–673 apply_spec_overrides`（`:789` 调用） | `anchor_fixes` 严格校验 + `capacitor_walls` 行 y 迁移 | → 保留 `anchor_fixes` 严格校验（**漂移探测，勿弱化**）；**移除** `capacitor_walls` 段 | §五 ③ |
| G8 | `:677–700 check_ac_pitch`（S7，`:800` 注册） | AC 墙中心距/冻结带检查 | → 移除 S7（对象已不存在） | §五 ③ |
| **S1** | **canonical SPEC `components.anchor_fixes`** | 含 **`C64`、`C66`**（真源/板上均不存在） | **须处置**（见 §3） | **超出 Z3 范围 ⇒ 须监理裁** |

> G1–G8 均属**源侧对齐**（删死代码 + 参数化），不含设计意图新增；**≥2 件新约束**：G3 的 refdes 集须**由真源导出**（禁字面表），G2 的解析须走 `pm_gate.config`（禁硬编码）。

## 3. **停机项（须监理裁一次，一句话）**：S1 —— SPEC `anchor_fixes` 的 2 条陈旧 ref

- **事实**：canonical `SPEC rev-20` 的 `components.anchor_fixes` = `{C64, C66, C82}`，其中 **`C64`/`C66` 在真源（板 42 / 网表 55）中均不存在**
  （`C64` = A 类外置耦合已删；`C66` = D 类 VREG 去耦已删）；`C82` 在板上存在（保留）。
- **冲突**：生成器 `:649` 对未知 ref **严格 fail**（漂移探测，**正确行为**）⇒ 不改 SPEC 则 G7 的严格校验必挡；
  若改为「记日志跳过」= **掩盖 SPEC/真源漂移 = 硬编绕过**（§五 明禁）。
- **处置二选一**：
  - **(a) ★建议：SPEC 版本 bump 新文件 `rev-21`** —— 仅删 `anchor_fixes` 的 **2 条**（`C64`/`C66`），其余**逐字节承自 rev-20**；
    `project.yaml: spec_name` 重指向 rev-21；rev-19/rev-20/6L 件**原件不动**（宪法第四条）。属 **SPEC 内容变更**（超出 Z3 的层语义范围）⇒ **须监理一句话放行**。
  - **(b) 生成器对未知 `anchor_fixes` ref 记日志并跳过** —— 不采纳：掩盖漂移，且与 §五「不得硬编绕过」冲突。
- **停机声明**：按 §五 停机条款，**在 (a)/(b) 裁定前不动生成器源码**（不自行选 (b) 绕过）。

## 4. 获准 (a) 后的实施计划（§五 + E4 判据）

1. SPEC **rev-21**（新文件）+ `project.yaml` 重指向；复出 sha 报监理。
2. 生成器改 **G1–G8**（逐点留痕：`k2/docs/` 记录 + 生成器**头注版本块**）；`criteria/` 不动。
3. **E4 判据**（§五 ⑥）：`K2_OUT_PCB` 连跑 **两次 sha 相同**；并加机检：
   产物 refdes 集 **== 42（真源板）**、边框 **46mm `[33,79]`**、器件数/网数对账。
4. 若过程中再遇「真源不足」（缺设计意图/符号库）⇒ **再次停线报监理**。

## 5. 复现

```bash
# 干跑（内存覆盖，不改源文件）
AppDir/usr/bin/python3.11 /tmp/opencode/k2p1/gen_dryrun_draft.py
# 阶段 2 草件（仅 /tmp）：SPEC 删 anchor_fixes.C64/C66
ls -l /tmp/opencode/k2p1/SPEC_dryrun_r21.json
```
