# K2 · **P6/学习环批 2 · K1 侧只读基线 + 框架缺陷实证**（v1 · 2026-09-20）

> 性质：**只读实测记录 + 根因命名**（不改任何载体/判据/交付包）。
> 用途：① 给 B2-1..B2-4 的「改前」判据；② 把 v2 计划里的**推测性根因**换成**可复现实证**。
> 机读真源：`pm_gate/artifacts/k2_v4/P6_execution/BASELINE_pm_gate_k1_k2_readonly_v1.json`
> sha256 **`27d79e460809987c9ab6e94f7d2451ca1830f56f95da7fc05b436ef99eb25d6b`**（两次连跑逐字节同）
> 机核：`pm_gate/artifacts/k2_v4/P6_execution/INSTRUMENT_SELFCHECK.json`（13/13 锚在；负控已验：篡改 1 锚 ⇒ FAIL/退出码 1）
> 复现：`PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p6_readonly_baseline_v1.py --out /tmp/opencode/k2_p6_baseline.json`

## 0. 交付锚复核（未动）
`MANIFEST.json` `6ee7495d…` · tarball `0e88e107…`（422,709 B）· 受审板 `l7 c5a7df90…` · 冻结四源 `d4e81f64…`/`fb07d25a…`/`dd794c54…` · 判据 rev=3（ENG 只读）。

---

## 1. 三个**框架缺陷**（实证 · 均属 C-3「工具对仓库/项目布局的假设陈旧」族）

### F-1 · `RULES_DOC` 越出容器 ⇒ **G1.5 对任何项目不可 PASS**
- 载体：`_shared/pm_gate/check_l1.py:193`（`__file__` 三级上溯 + `"..", "doc", "PCB_DESIGN_RULES.md"`）。
- 实测解析：K1 → `/home/fila/jqdDev_2025/ic_hw/../doc/PCB_DESIGN_RULES.md`；K2 → `/home/fila/jqdDev_2025/ic_hw/k2/../doc/PCB_DESIGN_RULES.md` ⇒ **两者的 `exists=False`**（该路径在容器外）。
- 真源：`_shared/docs/PCB_DESIGN_RULES.md`（在库）；K1 `state_k1.json` 的 **G1.5 WAIVER 原文即如此指认**（「多退一层，越出容器」）。
- 结论：**K1/K2 双双 FAIL**（本轮实测）。K1 侧历史判定 = `WAIVER`（`is_waiver=True`，RISK-001）；**K2 的历史 G1.5 PASS 早于本次布局**，今日不可复现。
- 对应：**B2-4**。

### F-2 · L2/L3/QA 门禁**未项目化** ⇒ 非默认项目恒读错产物
- 载体：`check_l2.py` / `check_l3.py` / `check_qa.py` 的 `artifacts.read_text(...)` **未传 `project=`**（T13 只改造了 `check_l1.py`）⇒ 恒用函数默认 `DEFAULT_PROJECT="k2_v4"`。
- 独立书证：`k1/pm_gate/tools/k1_l2_gate_runner.py` docstring 明写「**L2/L3/QA 门禁对非默认项目恒不可机判**——与账本 C-3 同族」。
- 本轮实测（K1）：`G2.1` 报「缺失 `measurements.md`」，而 `k1/pm_gate/artifacts/k1/L2/measurements.md` **实际存在** ⇒ 读的是**别的项目维度**。
- 子项：
  - **F-2a**：`check_l3.py:26` 硬编码 `SPEC_k2_v4.json`（文案 `:28/:46/:53`）⇒ K1 `G3.1` 报「缺失 SPEC_k2_v4.json」，而 K1 **实有** `L3/SPEC_k1.json`。
  - **F-2b**：`check_qa.py:35` `config.spec_name()` **空参** ⇒ 取 `DEFAULT_PROJECT`（`k2_v4`）而非 active project（`_shared` 内**唯一空参点**）⇒ K1 `G4.1` 报「SPEC 缺失，无法对照」。
- 对应：**B2-3a / B2-3b**。

### F-3 · `wp1_closure_check` 默认值为**框架相对**且**目录不存在** ⇒ G3.5 对任何项目不可跑
- 载体：`_shared/pm_gate/closure_check.py:110-113`：`DEFAULT_SPEC` / `ESCAPE_SPEC_PATH` = `<pm_gate 模块目录>/artifacts/L3|L2/...`，即 `_shared/pm_gate/artifacts/...`。
- 实测：`_shared/pm_gate/artifacts` **不存在**；K1/K2 `check_g35` 均 FAIL（「SPEC 读取失败 `_shared/pm_gate/artifacts/L3/SPEC…`」）。
- 定性：M-14「基址钉死 = 项目根」**未覆盖这 2 处**（与 `check_l3` 的硬编码名叠加）。
- 对应：**B2-3c**。

---

## 2. K1 / K2 框架维度现状读数（实测；「改前」值）

| gate | K1（框架维度） | K1（项目自述 `state_k1.json`） | K2（框架维度） | K2（`state_k2_v4.json`） |
|---|---|---|---|---|
| G1.1–G1.4 | PASS | PASS | PASS | PASS |
| G1.5 | **FAIL**（F-1） | **WAIVER**（RISK-001） | **FAIL**（F-1） | PASS（2026-08-21，早于布局） |
| G2.1–G2.5 | **FAIL**（F-2，读错维度） | PASS（经 `k1_l2_gate_runner` 注入项目维度） | PASS | PASS |
| G2.6 | FAIL（同上） | PASS | FAIL（`escape_closure_analysis.md` 无明确判定） | PASS |
| G3.1 | **FAIL**（F-2a） | pending | **FAIL**（spec 解析名 + 期望集陈旧，见 §3） | PASS（2026-08-21） |
| G3.2/G3.4 | FAIL（K1 无该件 / F-2） | G3.4 PASS·G3.2 pending | PASS / PASS | PASS |
| G3.3 | FAIL（F-2） | pending | PASS | PASS |
| G3.5 | **FAIL**（F-3） | pending | **FAIL**（F-3） | PASS（2026-08-23） |
| G4.1/G4.2 | **FAIL**（F-2b） | pending | FAIL（`k2_v4.kicad_pcb` 无走线 = 对象缺失） | pending |

> **读法**：K1 的 `G2.x/G3.x` 框架 FAIL **不等于 K1 缺件**——K1 自有 runner 已 PASS；差异即 F-2。**升版验收必须**区分「项目真缺件」与「工具读错维度」。

## 3. 判据侧待裁项（**ENG 不得自定** · C-12）
1. **`SPEC_EXPECTS["corridors"]` 陈旧**：`check_l3.py:17-22` 期望 `J2_TO_U` / `U_TO_MCIO`；现行 spec（plain 与 rev-52 同）走廊 `id` 实为 **`EAST_CHIP_TO_J2` / `WEST_MCIO_TO_CHIP`** ⇒ 即使修好解析，K2 `G3.1` **仍 FAIL**。期望集属判据面 ⇒ **须监理裁定**（改名承接 / 双名兼容）。对应 **B2-3d**。
2. **撤 K1 `G1.5` waiver**（RISK-001）：修 F-1 后须**无 waiver 机判 PASS**；属判据收紧 ⇒ **须监理批**。
3. **P6-1 前置缺件**：`criteria/` 仅有 `manifest.k2.yaml`；`adjudicate.py:536` 按 `criteria/manifest.<project>.yaml` 解析 ⇒ `--project k1` **FAIL-closed**。**应然集属监理持有**（G-c2）。

## 4. SPEC 名站点普查修正（范围差异，须具名）
| 口径 | v2 计划 | 本轮实测 |
|---|---|---|
| `_shared` 内 `SPEC_k2_v4` 命中 | 「13 处」 | **43 处**（`pm_gate/` 内 **16**、`eda_core/` 内 27） |
| 新增具名（v2 未列） | — | `review.py:121` · `check_qa.py:34` · `config.py:120` · `closure_check.py:112` · 27 处 `eda_core`（含 tests） |
> **实施要求**：逐处**定性**（应项目化 / 应具名豁免），**禁**一把梭替换（C-12）；范围结论须与监理对齐。

## 6. `SPEC_k2_v4` 站点**逐处定性**（43 处 · 8 类 · 0 未定性）
真源（机读）：`pm_gate/artifacts/k2_v4/P6_execution/SPEC_SITE_CENSUS_v1.json` sha256 **`6df3d557…`**（两次连跑逐字节同）
普查器：`k2/tools/k2_p6_spec_site_census_v1.py`（只读；`_shared` 与 `k2/_shared` 两份 checkouts **一致**校验通过）

| 类别 | 数 | 含义 / 处置 |
|---|---|---|
| **STALE_LEGACY_BASE** | **4** | 基址仍是拆分前 `revA/pcb` 布局 ⇒ 路径**恒不存在**：`eda_core/cap_wall_apply.py:56` · `eda_core/cap_wall_solver.py:608` · `pm_gate/closure_check.py:112`（F-3） · `pm_gate/wp1_semantics_check.py:45`（注释自承 `revA/pcb`）⇒ **M-14 基址钉子须扩到这些处** |
| **NAME_ONLY_HARDCODE** | 6 | 基址正确、仅文件名写死 ⇒ 改 `config.spec_name(active)`：`check_l3.py:26`（B2-3a）· `check_l3.py:53`（check_g32 内容期望）· `freeze_wp1.py:45` · `review.py:105` · `review.py:121` · `tools_escape_predict.py:39` |
| **TEST_ANCHOR** | 13 | 测试锚（`conftest.py:46` fixture 副本 / `test_hs_route_model.py:164,324` 绝对锚 / `test_routing_topology_gate.py:31` / `test_topology_gate.py:25` 旧路径 …）⇒ 随批 2 项目参数化 **或具名 K2-only** |
| **DOCSTRING_MESSAGE** | 9 | 注释/报错证据文案（零行为）⇒ **具名豁免** |
| **CLI_CONTRACT** | 7 | CLI 用法/参数 help（路径由调用方传）⇒ 可留名，**须具名** |
| **NEGATIVE_CONTROL** | 2 | `test_feature_extractor.py` 的「零单板特判」禁令测试（**仅扫 1 个模块**）⇒ 不改；**注意**：该禁令门未覆盖其余模块 ⇒ 与 B2-3 同批扩面**须监理批** |
| **PROJECT_CONFIG** | 1 | `pm_gate/config.py:27`（PROJECTS 兜底字典 k2_v4 条目）= 正当 |
| **LEGACY_OTHER_PROJECT** | 1 | `eda_core/env_fingerprint.py:69`（候选含 `strix-halo-ioconvert/revA` 路径）= 与 K2 判据无关 |

## 7. 34 个 skip 的**归因**（「回归网弱于表面」的拆解）
| 组 | 数 | 常量 / 现状 | 补救 |
|---|---|---|---|
| **A** | **22** | `K2V4_REAL_BOARD = REPO/"k2_v4.kicad_pcb"`（`REPO`=容器根 ⇒ **恒缺**；真板在 `k2/k2_v4.kicad_pcb`，**在库**） | **一行锚修正**（同文件 `SPEC/ALLOC` 已用绝对锚示范）⇒ 22 项**由 skip 转实跑**（B2-1/B2-2 的「skipped 不得充绿」即可满足） |
| **B** | 12 | `BASELINE_PCB = /tmp/opencode/boards/k2_m9demo.kicad_pcb`（**/tmp 生成物，不在库**） | 补 fixture 生成步骤 **或具名接受** ⇒ 与 **N-05「生成器不可复跑」同族** |
> 归因完整：`34 = 22 + 12`（`unattributed = 0`，机读见 census 件）。

## 8. K1 `G1.5` WAIVER **实质条件复算**（只读 · 撤 waiver 前置）
| 陈述（waiver 原文） | 复算结果 |
|---|---|
| 真实规则件在 `_shared/docs/PCB_DESIGN_RULES.md` | ✅ 在库 |
| 工艺常识强条文档在库 | ✅ 4 份 checkout 全含「强条」 |
| K1 precheck 章节齐 | ✅ `precheck_{A,B,C}.md` 各含「G2 焊盘墙穿透」+「汇总判定」 |
| 候选含「蛇形」 | ✅ `candidate_{A,B,C}.md` 各含 |
⇒ **`substantive_conditions_met = true`**：F-1 修好后 K1 `G1.5` 应可**机判 PASS**，届时**撤 waiver**（B2-4 的验收判据已就绪）。

## 5. 不改动声明
本件与两份工具**零载体改动**：未触 `_shared`（除只读 import）· 未触 `criteria/` · 未触冻结四源 · **未重建交付包** · 未触 `.omo/supervision/**`。临时件仅在 `/tmp/opencode`。

—— ENG（ARCHER）· 2026-09-20 · k2 HEAD 见提交 · 最新裁定 **#K2-40**
