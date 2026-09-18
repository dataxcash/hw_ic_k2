# K2 · 《**ENG 能力清单 + 可重生成证明**》· v1 · 2026-09-18

> 依据：owner 目的升级（`.omo/supervision/ledger/OWNER-PURPOSE-20260918-build-the-ENG.md`：「必须要根除问题，我们的目的是打造 ENG，不是仅仅做一个板子」）
> + 监理 **#K2-25**（§一 E-1..E-6；§二 本交付物 6 项；§三 优先序；§四 门条件）。
> **ENG 出证据，监理判**；逐项 sha + 判定器 PASS/FAIL 集合（禁「接近」）。红线照旧（冻结四源不改 · `criteria/` 只读 · 禁派 WORKER · 临时仅 `/tmp/opencode` · 不放松 DRC · 不缩口径 · 冲突即停机）。
> ENG（ARCHER）· 2026-09-18 · 受审板 `dae8dc8d48ff5b81` · SPEC rev-50 `ed0950687e5aec97` · 真源乙2 `61c4694e3b4df564`

## 0. 结论（六条，逐条对应 E-1..E-6）

| 判据 | **判定** | 依据（本件实测） |
|---|---|---|
| **E-1 单链可重生成** | **FAIL（现状不可行）** | **构造段确定性子链已存在**（真源→原理图→BOM→图纸，逐段 sha 见 §2.1，两次连跑逐字节同）；**但终点「受审板」无构造产出**：生成器产物 vs 受审板差 **421 带号 pad / 12 refs**（§2.3），且生成器**当前被 ref 锚阻断**（§2.4） |
| **E-2 构造链，非修补链** | **FAIL（双臂实测）** | 去 `l4` ⇒ 链首件 `FileNotFoundError`（`k2_p4_build_l5_v1.py:48`）；换等价空白板（同框、清器件）⇒ `IndexError`（按 ref 逐个回填旧件）⇒ **硬依赖 `l4`**（§3） |
| **E-3 载体根闭** | **未闭（台账 §4）** | 「载体未修」**19 条**（v1.4 记 29；本轮 ⑤ 执行后 3 条解禁）⇒ 逐条归属 + 修复件 + 阻塞点；**无一条可在缺 ⑦/判据装件时根闭** |
| **E-4 判据在岗 + 签认** | **未在岗** | `criteria/` 仍 **rev=1 / 9 维 / `not_countersigned:true`**；19 维 canonical 候选件齐备（§5）⇒ **装件 = owner 唯一通道** |
| **E-5 权限隔离** | **PASS（实测）** | ENG 身份 `fila`：`test -w criteria/adjudicate.py` = **1**、`test -w criteria/manifest.k2.yaml` = **1**、`test -w criteria/` = **1**（owner `ic_hw_gate`，mode `444`/`555`）；`verdict_schema` 判据在岗 **PASS**（产物中 verdict 字段 = 0）（§5.3） |
| **E-6 跨板复用** | **未测（P6 门）** | §三-5 归 P6；本件不评 |

**一句话**：ENG 的**确定性构造段是真的**（可复跑、逐字节同、且与落件 sha 一致）；**但它不通到受审板** —— 受审板目前由 `l4` 修补链产出 ⇒ 按 owner 目的「把真源换掉、把旧板丢掉，还能不能再产一块正确的板？」⇒ **现状答：不能**（守恒级缺口见 §2.3/§6）。

## 1. 能力清单（§二-1；逐件 输入 → 输出 → 判据）

| # | 类别 | 件（sha16） | 输入 | 输出 | 判据/门 |
|---|---|---|---|---|---|
| A1 | **真源 L1 冻结** | `k2/hw/data/k2_sch.yaml` `dd794c54f7ce7417`（**冻结**） | — | 电气真值 | `criteria` 锚；**永不改** |
| A2 | 真源**乙线**（现行消费） | `k2/hw/data/k2_sch.errata-2.yaml` `61c4694e3b4df564` | A1（+owner 裁定） | 现行真源（54 件） | 与 A1 同源（差异 = owner ⑤ 删减） |
| A3 | 真源**指针** | `k2/pm_gate/project.yaml` `56583331599fab0f` | — | `spec_name` / `nets_yaml` | T-41（写入须双闸） |
| B1 | **原理图生成器** | `k2/tools/k2_sch_gen_v1.py` | A2 | `k2/hw/sch/*.kicad_sch`(6) | 确定性（两次同 sha）· 落件走 T-22 |
| B2 | **产品板生成器** | `k2/tools/k2_gen_v5.py` `796bd7a48947ec7c` | A2 + SPEC + **`PCB_REF_PATH`（锚板！）** | 产品板（`K2_OUT_PCB`） | S1/S2/S4/S5/S6/S8 自检 · **当前被 ref 锚阻断** |
| B3 | **L3 图纸生成器** | `k2/tools/k2_p3_drawings_v1.py` `00bb3245d601d775`（v11 版；上一版 `eb7ea771a1645c01`=v10） | SPEC rev-50 + A2 + **受审板（实测源）** | `L3/drawings/**`（图集 v11） | fail-closed（板 sha == SPEC 自述）· C1–C7/D1 自测 |
| B4 | **BOM 生成器** | `k2/tools/k2_p4_bom_gen_v1.py` `9921dbae67af97ce` | sch netlist（B1 产物）+ A2（交叉核对） | `k2/fab/k2_v4_bom.csv` `db081546bbe64c37` | 真 `check_bom_consistent` 正控 PASS / 负控 FAIL / 缺件 fail-closed |
| B5 | **板构造/修补链**（P4） | `k2_p4_build_l5_v1.py`（首件）· `k2_p4_composed_land_v2.py`（落件）· 30+ `k2_p4_*.py`（含本轮 ⑤ 执行 5 把：`truesource_bump` `250da380e046538c` · `del_c89_board` `eb69e42dd11c9c8a` · `del_c89_pro` `208fa76ccb700d1e` · `spec_rev50` `80b618b4c5cbdbe7` · `land` `89813b2280887cff`） | **`l4`（冻结交付板）** + A2/SPEC | 受审板 | ⛔ **E-2 证伪点**（§3） |
| C1 | **门禁引擎** | `_shared/eda_core/pipeline/{engine,checks,required,config,state,guard}.py`（`checks.py` `a33a99dfdbec7d61`） | `pipeline.yaml` + 项目树 | rc + 逐 check 明细 | 必选三联 `sch_structural/netlist_connect/bom_consistent`；**k2 无 pipeline.yaml ⇒ 对 k2 从未运行** |
| C2 | **提交钩子** | `_shared/eda_core/pipeline/hooks/pre-commit` `61331e0bb17fa477` | staged 集 | 拒绝/放行 | 全局 sch 完整性 · PCB↔SPEC 对应 · meta-gate · process_gate(opt-in) |
| D1 | **判据（冻结）** | `criteria/adjudicate.py` `897e8bfde60e2cfe` + `criteria/manifest.k2.yaml` `7ce08757eff25557`（**只读 rev=1**） | 板/pro/真源/sch | PASS/FAIL 集合 | 9 维 enabled；`not_countersigned:true` |
| D2 | **判据候选（19 维）** | `k2/docs/drafts/p4-j8-density-clearance-v1/manifest.k2.v4.yaml` `004f7ac2666da437`（16 enabled + 2 待阈值 + `rule_severity_manifest` 无条件第 19）· 控制件 `2531d4c616d855e9`· 判定器草案 `1cda68521d0e56be` | 同上 | 19P/0F 目标 | **装件 = owner 通道**（§5） |
| E1 | **权限隔离** | `criteria/**` owner `ic_hw_gate` `444/555` · `.omo/supervision/**` ENG 只读 | — | E-5 | 实测 `test -w` 全失败（§5.3） |
| F1 | **冻结四源** | `l4` `d4e81f647be7f980` · 设计源板 `fb07d25ac426ff84` · A1 `dd794c54f7ce7417` · `criteria` 两份 | — | 不可变锚 | 本件实测未变 |

## 2. E-1 可重生成（§二-2）

### 2.1 已存在的**构造段**：一条具名命令链 + 逐段 sha + 两次连跑逐字节同（实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# ① 真源 → 原理图
K2_SCH_YAML=k2/hw/data/k2_sch.errata-2.yaml K2_OUT_SCH=/tmp/opencode/e1/s1 python3 k2/tools/k2_sch_gen_v1.py
# ② 原理图 netlist → BOM
python3 k2/tools/k2_p4_bom_gen_v1.py --out /tmp/opencode/e1/b1.csv
# ③ canonical SPEC + 真源 + 受审板 → L3 图集 v11
K2_P3_OUT=/tmp/opencode/e1/d1 AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py
```

| 段 | 产物 | 两次连跑 | 与**落件**一致 |
|---|---|---|---|
| ① 真源→原理图 | `k2_sch.kicad_sch` `a7cbb7a7aa54d4c3` · `power_12v…` `dbaa989e0688cd53` · `redriver…` `c7099e2fae642bdd` | **逐字节同** ✅ | ✅（= 本仓落件） |
| ② sch→BOM | `db081546bbe64c37`（54 refs） | **逐字节同** ✅ | ✅ |
| ③ SPEC+真源→图集 | `p3_drawings.json` `e284e9afd9054408`（54 件） | **逐字节同** ✅ | ✅ |
| ④ 生成器→产品板 | （`k2_gen_v5.py`） | 前一版可跑时同 sha（`1252bd2e74957d82`） | ❌ 产物 ≠ 受审板（见 2.3）；**现被阻断**（2.4） |
| ⑤ 受审板（链的**终点**） | `dae8dc8d48ff5b81` | — | **无构造产出**（由 `l4` 修补链产出，见 §3） |

### 2.2 起点/输入面（具名，含一处**循环**）
- 起点（真源）= A1 冻结 + A2 乙2 + D1 canonical SPEC + （#K2-25 列的）「L3 图纸」。
- ⚠ **循环具名**：本仓 **L3 图集是板的*下游***（`k2_p3_drawings_v1.py` 以受审板为实测源）⇒ **不能同时充当板的*输入***。#K2-25 §一 E-1 把 L3 图纸列为链输入，与现行实现**互为因果** ⇒ 若要以图纸为输入，须先定义**图纸的上游**（例如由 SPEC 的 canonical 几何字段直接出图，不读板）；否则 E-1 的输入面不闭合。

### 2.3 **守恒级缺口**：生成器产物 ↔ 受审板（带号 pad 逐件对账）

| 量 | 生成器产物 | 受审板 | 缺口 |
|---|---|---|---|
| refs | 46 | **58** | 12（含 `H1..H4` 4 件 NPTH 与 8 件未生成） |
| 带号 pad 合计 | 266 | **685** | **421** |
| 缺口构成（top） | `U6` 0（板 354）**354** · `U1` 33（板 58）**25** · 排针 `J6/J9/J11/J12/J13` 0（板 2/4/4/2/4）**16** · `R42–R45` 0（板 2 各）**8** · 其余 18 | — | Σ **421** |

⇒ **`∑ 产物 pad + 缺口 pad = 板 pad`（精确对账）**；缺口**全部**来自「生成器 pad 几何取自锚板」= **G-ROOT-1**（#K2-22 §一）。

### 2.4 当前阻断（与 #K2-24 执行件 §4 同一项，具名）
`k2_gen_v5.py` 的 ref 清单取自**冻结锚板**（`:54 PCB_REF_PATH` → symlink → 设计源板；`:68-77` 解析、`:79 K2_REFS`、`:830-835` 断言）⇒ owner ⑤ 删 `C89` 后 **fail-fast**：
`❌ 写盘阻断 [YAML] K2 清单含 YAML sheets 不存在 ref: ['C89']` ⇒ **第 ④ 段当前不可跑**。

## 3. E-2 去 `l4` 依赖（§二-3；**双臂实测**）

装置：`rsync` 沙箱 k2 树（`/tmp/opencode/eng_e2b/k2`，含 `AppDir` 外链）；链首件 = `k2/tools/k2_p4_build_l5_v1.py`（`:34 SRC = hw/k2_v4_8L.l4.kicad_pcb`，`:277 LoadBoard(SRC)`）。

| 臂 | 输入 | 结果 | 结论 |
|---|---|---|---|
| **A** | `l4` 在场（原样） | 产出板 sha16 **`522027437d034995`**（自检：fps 59 / zones 17 / filled 9） | 产物 **≠ 受审板** `dae8dc8d48ff5b81` ⇒ **链不跟真源走**（owner ⑤ 删 C89 后仍产带 C89 的板） |
| **B1** | **移除 `l4`** | **`FileNotFoundError`**（`:48` `sha16(SRC)` 第一步即读 `l4`）⇒ **无产物** | 依赖 `l4` 为**硬前置** |
| **B2** | **换等价空白板**（同框、清 42 件 + 13 zone） | **`IndexError`**（`OLD[ref] = by_ref(ref)[0]`：按 ref 逐个回填旧件，缺件即崩） | 链是**按旧板器件逐个修补**，**非构造** |

⇒ **E-2 = FAIL（明确）**：`l4` 一撤即无板；替换空白板即崩 ⇒ 现行链为**修补链**。

## 4. E-3 载体根闭台账（§二-4；「载体未修」19 条逐条：归属 → 修复件 → 阻塞点）

> 计数口径：闭环表 §13（v1.5）= **根闭 0 / OUT 5 / 未闭 54**（载体已修 25 /「判据已实现待安装」10 /「**载体未修 19**」）。
> v1.4 记 29 条；本轮 **#K2-24（owner ⑤ 删）已执行** ⇒ ⑤ 系 3 条（`M-03` `M-17` `F-10`）**解禁为「载体已修、待判据装件」**。

| 组 | 条 | 归属 | 修复件（须做什么） | 阻塞点 |
|---|---|---|---|---|
| **G-ROOT-1 家族** | `U-03` `U-04` `U-07` `M-09` `F-1` `F-7` `M-11` `F-14`(PCB_REF_PATH 侧) `N-05`(同侧) = **9** | 🔴 **监理：⑦ 库快照重建 + 落件 + 库↔板名集** | 库 27 件候选（`ForgeOS.pretty` 20 → 27）；生成器 pad 几何改由**具名外部源（库）**取；`U2` SOIC-8 补库件；`J3/J4` 库 pad 名集改 `A1..A19/B1..B19` | 未经 ⑦ ⇒ 生成器 pad 几何无正确外部源（§2.3 缺口 421） |
| **阈值/口径系** | `M-12` `U-09` `M-05` `F-2` `M-02` = **5** | 监理 | 密度/间距应然阈值（`cell 10/frame_origin/max_fp 8/min_clear 0.100` 已裁 ⇒ 待装件）；`refplane` 阈值（本会话已交缺口清单 + 守恒证明）；`M-02`「无判据类」根闭口径 | 阈值/口径未签 ⇒ 判据不可启用 |
| **原理图/pro 系** | `N-03` = **1** | 监理**排程**（ENG 可执行） | pro `schematic.top_level_sheets` 一行键值（指向不存在的 `k2_v4_8L.l4.kicad_sch`） | 改 pro = 改受审载体 ⇒ 须与落件排程（勿自发） |
| **交付面** | `N-01` = **1** | P5 | 出交付 Gerber（P4 未关门不得出） | 阶段门 |
| **⑤ 系（本轮解禁）** | `M-03` `M-17` `F-10` = **3** | 已由 owner ⑤ + `D-7a` 处置 | 真源删减已落（`errata-2`）+ 判据读取口径 `D-7a` 已落 `_shared a266851` | **只差 E-4 装件** ⇒ 装件后即具根闭资格 |
| 合计 | **19** | — | — | — |

## 5. E-4/E-5 判据在岗台账（§二-5）

### 5.1 现状（实测）
`criteria/adjudicate.py` `897e8bfde60e2cfe` · `criteria/manifest.k2.yaml` `7ce08757eff25557`（**rev=1**）· enabled **9 维** · `not_countersigned: **true**` · `k2/pipeline.yaml` **不存在** ⇒ **④ 在岗 = 0 条**（#K2-22 §二：未签认不算在岗）。

### 5.2 19 维装件包（候选件齐备，**装件 = owner 唯一通道**）
| 件 | sha16 | 内容 |
|---|---|---|
| `manifest.k2.v4.yaml` | `004f7ac2666da437` | 18 维（**16 enabled** + `density_and_clearance`/`ref_plane_continuity` 待阈值）+ **`rule_severity_manifest` 为无条件第 19** |
| `manifest.k2.control-v4.yaml` | `2531d4c616d855e9` | 控制件（正/负控） |
| `adjudicate.draft-v4.py` | `1cda68521d0e56be` | 19 维判定器草案（v3 严格超集） |
| 仪器 | `measure_ref_plane_continuity.py` `7a3cc545c1447b04` · `measure_density_and_clearance.py` `dccaaa476c807def` · `measure_min_clearance_drc.py` · `measure_pads_within_outline.py` · `run_controls_v4.py` | 各维测量 + 七案控制 |
| 别名钉死 | `lib_footprint_electrical→lib_electrical_level` · `density_and_spacing→density_and_clearance` · `v3_reference_continuity→ref_plane_continuity` · `drc_warning_disposition→drc_warning_dispositions` | #K2-23 §二-9 |
| 锚 | 安装后 **`rev=2`** 登记 | #K2-23 §二-9 |

**请求（§二-5）**：① 按上表装 `criteria/`（owner 通道）→ ② 监理签认（`not_countersigned:false`）+ 锚 `rev=2` → ③ ENG 立即可复算 **19P/0F** 并报 PASS/FAIL 集合。
**预警（本会话实测，非「接近」）**：19 维下仍预计余 **3 处 FAIL** —— `refdes_sets_equal`（原理图 54 / 板 58；`H1..H4` 非器件，口径待裁）· `pipeline_present`（须装 `k2/pipeline.yaml`，且**先解生成器阻断** §2.4）· `ref_plane_continuity`（严口径 **83.52%**，与 `min_coverage=1.0` **不相容** ⇒ 须裁阈值或域口径；本会话已交 602 段缺口清单 + 守恒证明）。

### 5.3 E-5 权限隔离（实测原始输出）
```
whoami → fila
test -w criteria/adjudicate.py        => 1   （不可写 ✓）
test -w criteria/manifest.k2.yaml     => 1   （不可写 ✓）
test -w criteria                      => 1   （目录不可写 ✓）
stat: criteria owner=ic_hw_gate mode=555 · adjudicate.py mode=444 · manifest.k2.yaml mode=444
判定器 verdict_schema：OK（产物中出现 verdict 字段的文件 = []）⇒ 机器 verdict 不可被 ENG 重写 ✓
```
⇒ **E-5 = PASS（ENG 侧）**。

## 6. 可行域与所需输入（§二-6；**守恒级，不含「可能/取决于/待定」**）

**E-1/E-2 现状 FAIL 的根因 = 3 项具名输入/改造缺失**（缺一即永久 FAIL）：

| # | 缺项 | 缺了什么（量） | 归属/前置 |
|---|---|---|---|
| **P1** | **库快照重建（⑦）** | `ForgeOS.pretty` **20 → 27** 件（含 `U2` SOIC-8 库件）；`J3/J4` 库 pad 名集 `1..38` → `A1..A19/B1..B19` | 🔴 监理（G-ROOT-1 硬前置） |
| **P2** | **生成器去锚板** | ① ref 清单改由**真源**导出（现取锚板 ⇒ 阻断，§2.4）② pad 几何改由**库**取（现取锚板 ⇒ 缺口 **421** pad，§2.3） | 须批（红线：未获批不改生成器；⑦ 未落则 ② 无正确外部源） |
| **P3** | **链起点改真源构造** | 现首件读 `l4`（§3）；须改为「真源 + SPEC + 库」构造，且**不读 `l4`/锚板** | 须批 + P1/P2 |

**已具备（可复用，不需要新的裁定）**：真源解析（A1/A2/A3）· 原理图/BOM/图纸三段确定性构造（§2.1）· 门禁引擎与钩子（C1/C2，已修 D-2/D-3/D-4/D-4b/D-7a）· 判据候选 19 维包（§5.2）· 权限隔离（E-5）。
**⇒ 结论（可判定，无「待定」）**：在上述 P1–P3 落地前，**E-1/E-2 恒 FAIL**；落地后按 §2.1 同法复跑即可判定（判据 = 两次连跑逐字节同 + 与受审板 sha 相同 + `l4` 撤除/空白化不影响产物）。

## 7. 复跑链（本件各实测点）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# E-1 §2.1（三段确定性 + 逐段 sha；期望与落件一致）
K2_SCH_YAML=k2/hw/data/k2_sch.errata-2.yaml K2_OUT_SCH=/tmp/opencode/e1/s1 python3 k2/tools/k2_sch_gen_v1.py
python3 k2/tools/k2_p4_bom_gen_v1.py --out /tmp/opencode/e1/b1.csv
mkdir -p /tmp/opencode/e1/d1 && cp k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json /tmp/opencode/e1/d1/
K2_P3_OUT=/tmp/opencode/e1/d1 AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py
# E-1 §2.4（阻断复现）
K2_OUT_PCB=/tmp/opencode/g.kicad_pcb K2_OUT_JSON=/tmp/opencode/g.json python3 k2/tools/k2_gen_v5.py   # ❌ [YAML] …ref: ['C89']
# E-2 §3（双臂）
mkdir -p /tmp/opencode/eng_e2b && rsync -a --exclude '.git' --exclude '__pycache__' k2/ /tmp/opencode/eng_e2b/k2/
ln -sfn $PWD/AppDir /tmp/opencode/eng_e2b/AppDir
K2_P4_OUT=/tmp/opencode/eng_e2b/armA_l5.kicad_pcb AppDir/usr/bin/python3.11 /tmp/opencode/eng_e2b/k2/tools/k2_p4_build_l5_v1.py   # 臂A → 522027437d034995
mv /tmp/opencode/eng_e2b/k2/hw/k2_v4_8L.l4.kicad_pcb /tmp/opencode/eng_e2b/hidden_l4.kicad_pcb
K2_P4_OUT=/tmp/opencode/eng_e2b/armB_l5.kicad_pcb AppDir/usr/bin/python3.11 /tmp/opencode/eng_e2b/k2/tools/k2_p4_build_l5_v1.py   # 臂B1 → FileNotFoundError(:48)
# 臂B2：用 hidden_l4 清空 footprints/zones 后写回同一路径，再跑 ⇒ IndexError（OLD[ref]）
# E-5 §5.3
whoami; test -w criteria/adjudicate.py; echo $?; stat -c '%U %a' criteria criteria/adjudicate.py
```

## 8. 边界 + 未做项

**本件为只读取证 + 新增本件**：未改板/pro/真源/SPEC/库/生成器/`criteria/**`/`_shared/**`/冻结件；未派 WORKER；**未新增检查齿**（本件是清单与证明，判据仍由 `criteria/` 承）；**未修改生成器**（§2.4/§6-P2 只给提案）。
**未做（具名）**：P1 库快照重建（⑦）· P2 生成器去锚改造（须批）· P3 链起点改造（须批）· E-4 装件/签认（owner 通道）· 19 维复算（待装件）· E-6（P6）。
**C-12 声明**：本件**不宣称**任何未闭条目已消；判定器集合仍 **PASS 7 / FAIL 3**（`zone_filled` 10/18 · `refdes_sets_equal` 54/58 · `pipeline_present`）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `dae8dc8d48ff5b81` · 判定器 `897e8bfde60e2cfe`
