# CO-79（L2 验证质量）— 探针「空真通过」加固 + 守卫负控（A10）

> 日期 2026-09-12｜对象 `tools/p3_v57_co69_adversarial_probes.py`｜记录 `m13_v57_co69_adversarial_review.json` `18a86c998dd6b4de`｜boundary **v1.44**

## 1. 动机（把 CO-76 F2 / CO-78 的教训系统化）

A5 曾长期恒真 —— 它只查**带引号**字面量 `"In6.Cu"`，故无法发现未加引号的层角色文本。同一失效模式
（**断言只检查"它恰好知道的东西"，未知/未覆盖输入被静默跳过**）在本套件其余探针中被逐一审计，发现 3 处：

| # | 探针 | 空真/静默路径 |
|---|---|---|
| H1 | **A6** | `exp = wmap.get(L); if exp is not None and ...` ⇒ **线宽表里没有的层被静默跳过**（若层集误配，探针仍 PASS） |
| H2 | **A8** | `sqer()` 对未知层 `return 2.0`（伪装 er=4.0）⇒ 未知层被静默赋权；且未断言真的测到页面 |
| H3 | **A2/A4** | 无覆盖下限：键集/层集萎缩时仍可「无漂移/无违规」通过 |

## 2. 加固（守卫纯函数 + 实检共用）

新增并同时用于实检与负控的守卫：

- `width_coverage_guard(present, wmap)`：板上出现但线宽表没有的层 ⇒ 报 `uncovered`。
- `map_scope_guard(wmap)`：线宽表必须**恰好**等于 LID REV6 的 4 个信号层（多/少均失配）。
- `numeric_floor_guard(n, floor=95)`：漂移比对必须真比到足够多键。
- `unknown_layer_guard(seen, pl)`：阻抗口径表未覆盖的层清单（取代静默 fallback）。

A6 另**显式计数**被跳过的 PCIE 过孔（原实现静默跳过）⇒ 实测 **252**。

## 3. 结果（PASS，且有齿）

| 探针 | 关键证据 |
|---|---|
| A2 | 95 键比对，`floor_ok=true`，零漂移 |
| A4 | 4 层全在口径内，`scope_ok=true`，Zdiff 零违规 |
| A6 | `layers_present = {B,F,In2,In5}`、`uncovered_layers = []`、`wmap_scope_ok=true`、`pcie_vias_skipped_documented=252` |
| A8 | 独立重算 0.1300 == 记录 0.1300、`pages_measured=34`、`unknown_layers=[]` |
| **A10（新增）** | **守卫负控**：`width_coverage_guard({"F","In6"},WM) → (False,['In6.Cu'])`；`map_scope_guard` 缺/多键 → `False`；`numeric_floor_guard(10) → False`；`unknown_layer_guard({"F","In6"},pl) → ['In6.Cu']`；正向输入全 PASS |

⇒ 每个守卫**在记录中自带可执行负控**：坏输入必被抓到，好输入必通过。套件 10/10 PASS。

## 4. 性质与限制

- 只改探针工具；**零几何/阈值/工件改动**；四冻结源 4/4 MATCH 未动；本件不重跑 G4..G7（无需要）。
- A10 为**逻辑负控**（喂合成坏输入），不改板；A6 的过孔宽度仍未校验（SPEC 无过孔宽度口径）——**显式登记为已知边界**，不再静默。
- ① 对间净空仍为 **L1**；非执行者 pass 2/2、板厂券仍欠（外部）。
