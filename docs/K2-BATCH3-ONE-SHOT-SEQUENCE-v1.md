# K2 · **批 3 一次性施工序列（One-shot Sequence）v1** · 2026-09-20 · ENG（ARCHER）

> 用途：把 8 项未决**全部**排成**一条可执行序列**（命令 / 期望读数 / 回滚），供监理**一次批完**后按序执行、逐步留痕。
> 现状：**批 2 已落件**；**P6 交付阶段仍关闭**（本序列 = 学习环/批 3 施工，**不越阶段门**）。
> **执行前提**：S0 逐项授权到位；**任一步读数不符 ⇒ 停机**（冲突即停机，第九条）；**两跑不逐字节同者不得入库**。
> 红线：冻结四源 `d4e81f64…` 永不改 · `criteria/` **ENG 只读** · 未获批不改生成器/SPEC/原理图 · **禁派 WORKER** · 临时件仅 `/tmp/opencode`。
> 件索引：决策单 `K2-BATCH3-DECISION-SHEET-v1.md`（`ee553604d7116a51`）= **主裁定单**；每步的备料件列于其行内 sha16。

## S0 · 监理授权（前置，逐项）
| # | 事项 | 备料件 |
|---|---|---|
| ① | 板锚修 + 同伴件 同批落 | `anchors/K2V4_REAL_BOARD_absolute.diff` `310b5f80892e8f54` · `companion/K2P6_SHADOW_VERIFY_ANCHOR_TOLERANCE.diff` `0bc59be8dc154be8` |
| ③ | P6-1 `--nets` 口径 = `k1/boards/k1_sch.yaml` | `P6_1_NETS_INPUT_CALIBER_EVALUATION_v1.json` `f777b2364a7290f6` |
| ④ | P6-2 模板整改 = **O1**（含 archive 两件） | `P6_2_O1_MEASURED_v1.json` `bf7b8d91cb4f384c` · `P6_2_ACCEPTANCE_MECHANIZED_v1.json` `402385be8f89bf90` |
| ⑤ | SKIP 处置：A→S1 · B→F2 · C→S3/S4 | `BATCH3_SKIP_RETIREMENT_REGISTRY_v2.json` `d0dab2a129a2099a` |
| ⑥ | B2-4 撤 waiver（**L1 钉 sha 覆盖**） | `B2_4_WAIVER_RETRACTION_DRILL_v1.json` `42a0da4af68215ad` |
| ⑦ | B2-1/B2-2 授权 + 并入批 3 | `BATCH3_B2_1_B2_2_SCOPE_DEFINITION_v1.json` `b39739e1c29ce148` |
| ⑧ | 密度工具空集守卫 | `gc2/tool_fixes/DENSITY_EMPTY_GUARD.diff` `20faf179b3bd936f` |
| ⑨⑩ | K1 warning 登记 + refplane 口径；追认三件核对/验收器 | 决策单 §1 ①②′⑨ 行 |

## S1 · 板锚修 + 同伴件（1 行 + 1 行）
```bash
# 锚修（两处 _shared 检出；-p3 strip 后为 eda_core/tests/…）
cd ic_hw/_shared    && patch --posix -p3 < <P6X>/P6_OPEN_READINESS/anchors/K2V4_REAL_BOARD_absolute.diff
cd ic_hw/k2/_shared && patch --posix -p3 < <P6X>/P6_OPEN_READINESS/anchors/K2V4_REAL_BOARD_absolute.diff
# 同伴件（否则 D 腿 AssertionError）
cd ic_hw/k2 && patch --posix -p1 < <P6X>/P6_OPEN_READINESS/companion/K2P6_SHADOW_VERIFY_ANCHOR_TOLERANCE.diff
```
**期望**：容器根布局 `492P/28F/42S → 512P/30F/20S`（归因 22 = 20 skip→PASS + 2 skip→FAIL 具名 C1/C2 · **回退 0**）；k2 检出版**零变化**。**回滚**：3 文件 `git checkout`。

## S2 · 密度工具空集守卫（1 处）
```bash
cd ic_hw/k2 && patch --posix -p1 < <P6X>/P6_OPEN_READINESS/gc2/tool_fixes/DENSITY_EMPTY_GUARD.diff
```
**期望**：K2 `l7` 读数**逐字节同**（零扰动）；K1 由崩转可跑。**回滚**：`git checkout`。

## S3 · B2-1 / B2-2（`_shared` 两处契约显式化）
1. **第 0 步**：`grep -n` 复核载体行（旧行号多为批 2 前快照；B2-2 该区 **−91 漂移**）。
2. 落补丁 → 3. 负控实跑（B2-1 真源冲突 ⇒ 显式登记；B2-2 非法维度 ⇒ 报错）→ 4. 见 S8 验收。
**期望**：`_shared` 通用（零单板特判）；K2 同输入同输出**逐字节不回退**。**回滚**：`git revert`（单提交）。

## S4 · P6-2 模板整改 O1（6 补丁 / 54 行）
```bash
cd ic_hw/k2 && for d in <P6X>/P6_OPEN_READINESS/P6_2_template_proposal/O1_fullset/{archive_6L__*,k2_v4_8L*,k2_jlc_template}*.diff; do patch --posix -p2 < "$d"; done
cd ic_hw/k1 && patch --posix -p2 < <P6X>/P6_OPEN_READINESS/P6_2_template_proposal/O1_fullset/k1_jlc_template.kicad_pro.diff
```
**期望**：k2 受控 10 件 结构差异 **3 → 0**；两模板 ignore 集 **∅ == manifest 应然集 ∅**（S8 机判）。**注意**：`-p2`（**不是** `-p3`，后者会 `File to patch:` 挂住）。**回滚**：6 文件 `git checkout`。

## S5 · B2-4 撤 K1 `G1.5` WAIVER（**L1 钉 sha 覆盖**）
```bash
# ① 重跑演练生成目标件（工具自带守卫，拒绝直接落真源）
python3 <P6X>/P6_OPEN_READINESS/apply_k1_g15_waiver_retraction_v1.py --root /tmp/opencode/b24/k1 --apply
# ② 按 sha 钉定覆盖真 k1（须先确认：7a27fdc19665334c / 05ee9799023bd5cd）
cp /tmp/opencode/b24/k1/pm_gate/tools/k1_closeout_l2_v1.py ic_hw/k1/pm_gate/tools/
cp /tmp/opencode/b24/k1/pm_gate/state_k1.json           ic_hw/k1/pm_gate/
# ③ 复核：应报 already/already
python3 <P6X>/P6_OPEN_READINESS/apply_k1_g15_waiver_retraction_v1.py --root ic_hw/k1
```
**期望**：`check_g15` + `k2_p6_readonly_baseline_v1.py` ⇒ `is_waiver` 标记消失、G1.5 真机判 PASS。**回滚**：2 文件 `git checkout`。

## S6 · ⑤ SKIP 处置登记（A→S1 · B→F2 · C→S3/S4）
落 `BATCH3_SKIP_RETIREMENT_REGISTRY_v2.json` 为**签认版**（含覆盖真空登记），并按 C 类归属补/退（须监理裁）。
**期望**：`python3 k2/tools/k2_skip_registry_check_v1.py --registry <v2> --junit <实测 junit>` ⇒ **`unregistered_skips == 0`**。**回滚**：文档级。

## S7 · G-c2 落件（**gate 属主**执行；ENG 只读 `criteria/`）
把 `P6_OPEN_READINESS/gc2/PROPOSED_manifest.k1.yaml`（`94da046bfad8f2c8`）落为 `criteria/manifest.k1.yaml`，并把 `not_countersigned` 置 `false` + 填 `countersigned_by`（**监理签认动作**）。
**期望**：`adjudicate.py --project k1` 不再 fail-closed；`provisional=false`。

## S8 · 收尾验收（**每步之后可复跑；批末必跑**）
```bash
# ① 交付链
cd ic_hw/k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2     # preflight+3 PASS
# ② canonical 19 维（全新 --drc-work-dir；两跑逐字节同；verdict sha16 须 == 190b73be0f728a56）
#    命令见 L4/E3-standard-call-l7-20260919/MANIFEST.md
# ③ 变更后验收门
AppDir/bin/python3.11 k2/tools/k2_p6_acceptance_gate_v1.py --expect-patched                          # PASS（A4/4 · C 回退0 · D hidden=2=C1/C2）
# ④ 阶段门判据（P6）
python3 k2/tools/k2_p6_1_acceptance_v1.py --verdict <k1_verdict.json> --pro k1/k1_v1.kicad_pro       # PASS（四项命中 + provisional=false）
python3 k2/tools/k2_p6_2_acceptance_v1.py --expect-zero                                              # PASS（结构差异 == 0）
python3 k2/tools/k2_skip_registry_check_v1.py --registry <v2> --junit <junit>                        # PASS（未登记 0）
```
**任一不过 ⇒ 不入库、停机报告**；**C1/C2 保持 RED**（禁改绿）；`skipped` 不充绿。

—— ENG（ARCHER）· 2026-09-20 · 计划件（**非交付件**）· 件索引 sha16 见 §S0
