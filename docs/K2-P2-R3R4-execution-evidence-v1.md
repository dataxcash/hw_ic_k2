# P2 · R3/R4 执行证据 v1（监理 #K2-11 §三/§五 回件 3；**已落盘**）

- **性质**：执行 + 取证。动的是**已放行面**：R3（SPEC 版本 bump 新文件 + canonical 指针）、R4（E4 输入迁位）。
  未动三源（原理图 / 网表 / 板）、生成器源码、`criteria/`、`.omo/supervision/**`。
- **依据**：#K2-11 §三（R3 放行：版本 bump 新文件、原件 `5f72182a2616392c` 不动、重出 sha；R4 放行：E4 输入迁位，改生成器源码另案）
  + 计划 §4.2 Z3 + `K2-P2-Z1-true-source-declaration-v1.md` §3（陈旧件清单）。
- **冻结件复核（本件动作后实测）**：SPEC rev-19 `5f72182a2616392c…` **逐字节未动**；canonical `SPEC_k2_v4.json` = `0bd52ed48e720b8c…` **逐字节未动**；设计板 `fb07d25ac426ff84…`、交付板 `d4e81f647be7f980…` **逐字节未动**；网表 `70448241caa6f04a…`、原理图 **未动**。

## 1. R3 —— Z3「SPEC 归零」（canonical 由 6L 提升为 8L）

| # | 动作 | 对象 | 结果 |
|---|---|---|---|
| R3-a | **版本 bump 新文件**（rev-19 的版本化后继） | `k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-20.json` | 新建，**sha256 = `37dcd9cde5ceed090ffbdaafc131f379f1b8cc60a5904032e18c7645293599e9`**（392963 B） |
| R3-b | **canonical 指针**：引擎 canonical 指向 8L | `k2/pm_gate/project.yaml`：`spec_name: SPEC_k2_v4.json` → `SPEC_k2_v4.spec-rev-20.json` | 已改（另 `board_path: k2_v4.kicad_pcb` 因 R4 现可解析） |

**rev-20 与 rev-19 的差 = 仅 2 处**（`difflib` 逐行实测，共 48 diff 行）：
1. 顶层 `spec_version: 1.1.spec-rev-19 → 1.1.spec-rev-20`；
2. 末尾追加 `_spec_rev_10` 溯源卡（`card: SPEC-REV-10`，含 authority / basis / changes / unchanged / rollback / evidence_probes）。
其余**逐字节相同**（`stackup` / `impedance` 等对象 `==` 实测相等）—— 本件只做 canonical **层语义**归零，不含器件集、几何、走廊、PDN 任何变更。

**Z3 判据实测（双条，全 PASS）**

| 判据 | 实测 | 值 |
|---|---|---|
| ① SPEC 叠层键 = 8 层 | rev-20 `stackup` Cu 键 | `F / In1 / In2 / In3 / In4 / In5 / In6 / B`（8）；信号层 = `F/In2/In5/B`，平面 = `In1/In3/In6`，电源 = `In4` |
| ② 板走走线层 ⊆ SPEC 信号层集合 | 交付板 `d4e81f64…`（唯一带布线的板；`pcbnew` 实测 2512 track / 493 via）层级直方图 = `{F.Cu:359, In2.Cu:106, B.Cu:39, In5.Cu:2008}` ⊆ `{F,In2,In5,B}` | 超出集 = **∅ ⇒ PASS** |

**引擎视角独立验证**（非采信自述；`PM_GATE_PROJECT_ROOT=k2`，走 `pm_gate.config` + `pm_gate.artifacts`）：
```
spec_name -> SPEC_k2_v4.spec-rev-20.json
resolved  -> .../L3/SPEC_k2_v4.spec-rev-20.json   exists: True
spec_version: 1.1.spec-rev-20 | stackup Cu keys: 8
board_path -> k2_v4.kicad_pcb                      exists: True
```
> 对照：改前 canonical（`0bd52ed4`）为 **6L**（层键 6 = `F/In1..In4/B`；`stackup.In2.Cu` 仍写 *"only internal signal layer"*）⇒ Z3 判据①在原状下**不成立**。

**残留（须监理明确口径，本件未动冻结字节）**：canonical 的**物理文件名** `L3/SPEC_k2_v4.json`（`0bd52ed4`）内容仍是 6L —— 本件按 K2-11 §三「版本 bump 新文件 / 原件不动」**只改指针**，未覆盖该历史件。
若监理口径要求**该路径本身**承载 8L，可实现方式为：`git mv` 该件至版本化留档名（**字节不变**，sha 不变）+ 该路径置符号链接 → rev-20；请监理裁。

## 2. R4 —— E4 输入迁位（生成器三输入）

沿用 `k2/` 根**既有 8L 符号链接约定**（2026-09-14 owner A 目录重构时建立：`k2_v4_8L*.kicad_pcb` 已为同类链接），以链接迁位（零副本、零漂移风险）：

| 生成器期望 | 实际真源 | 动作 |
|---|---|---|
| `boards/k2_sch.yaml`（网表权威，I1） | `k2/hw/data/k2_sch.yaml`（`70448241caa6f04a…`） | 新建 `k2/boards/k2_sch.yaml -> ../hw/data/k2_sch.yaml` |
| `k2_v4.kicad_pcb`（坐标锚点，I3） | `k2/hw/k2_v4_8L.kicad_pcb`（`fb07d25ac426ff84…`） | 新建 `k2/k2_v4.kicad_pcb -> hw/k2_v4_8L.kicad_pcb` |
| `L3/SPEC_k2_v4.json`（几何权威，I2） | **生成器内硬编码** | **未动**（属改生成器源码 ⇒ 另案） |

**效果**：`FileNotFoundError`（I1/I3）消解 ⇒ E4 由「不可跑」前进到**下一阻断**；附带修复 `project.yaml: board_path`（此前失效 = 审计 M-14）。

**E4 复算（改后实测，两次连跑）**
```
❌ 写盘阻断 (fail-fast): [SPEC] 板框 [23.0,143.0]/[33.0,79.0] 与冻结板框 {'x':[23.0,143.0],'y':[33.0,71.0]} 不符
run1 rc=1 ; run2 rc=1   # 两次一致（确定性），但 E4 ≠ 归零
```

**E4 未归零的三项根因 —— 全在生成器源码，均属另案（禁由输入侧绕过）**

| # | 根因 | 实测证据 | 登记号 |
|---|---|---|---|
| 1 | 生成器硬编码板框 y=[33,71]（**38mm**）与 L1 冻结/SPEC 的 **46mm** `[33,79]` 冲突 | 上述阻断消息（SPEC 侧 `[33,79]`；生成器常量 `BOARD`） | F-8 |
| 2 | 生成器硬编码 SPEC 路径为 6L canonical | `k2_gen_v5.py:40 SPEC_PATH`（本件 R3 只改引擎 canonical 指针，**不动源码**） | F-14 / N-05 |
| 3 | 生成器 `K2_REFS` = **101** 件（含 `U3/U7` 双颗 `DS160PR810` + `C17–C32/C49–C64` 外置耦合），与真源（单颗 `DS320PR1601`）冲突：8L 板 42 件，生成器要而板上无 **60** 件、板有而生成器不识 **1** 件（`U6`） | `pcbnew` + 模块导入实测 | F-1/F-7/F-8 同族 |

> ⇒ **E4（Z4「生成器可复跑」）不可由输入迁位单独达成**；须**另案放行**改生成器源码（板框/输入路径/refdes 集与单颗架构对齐）。本件**未越界**改源码。

## 3. 未做（明确边界）

- **R1/R2 未落盘**：仍待监理复核「64 件逐条分类表」（`k2/docs/K2-P2-R1-64item-classification-v1.md`，`7c95ca99…`）——**8×100nF（`C65–C72`）定性未决者不得删**。
- E1–E4 全量复算未做（E1 依赖 R1；E2/E3 板侧列 `board_pending: true` 延 P4）。
- 未派 WORKER；未写 `.omo/supervision/**`；临时件仅 `/tmp/opencode/k2p1/`；**P3 未开**。

## 4. 复现命令

```bash
# R3 校验：canonical 指针 + 8 层键 + 交付板走线层 ⊆ 信号层
cd k2 && PM_GATE_PROJECT_ROOT=$PWD python3 -c "import sys;sys.path.insert(0,'_shared');\
from pm_gate import config,artifacts;import json;p=artifacts.path('L3',config.spec_name('k2_v4'),project='k2_v4');\
print(p,json.load(open(p))['spec_version'])"
sha256sum k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-{19,20}.json k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json
# R4/E4 复算
cd /home/fila/jqdDev_2025/ic_hw && python3 k2/tools/k2_gen_v5.py ; echo rc=$?
```
