# K2 · P4 · **P3「链起点改真源构造」· 证据件 v1**

> 依据：监理 **#K2-27 §五**（唯一工作包 = P3）+ **§六-2**（同批更正 P1/P2 件 §1.3 表述）。
> 判据锚 rev=1（MATCH）· 冻结四源未动 · `criteria/` 只读 · 未派 WORKER · 临时仅 `/tmp/opencode`。

## 0. 一句话结论

**构造链已建立（单件生成器，运行时零板读取）：真源 YAML + canonical SPEC + 库快照 + canonical 布局解 → 产物 PCB**；
**坐标已从 `refmap` 迁出**至 `L2/PLACEMENT_SOLUTION_v1.json`；**E-2 三臂实测**（`l4` 在场 / 移走 / 换等价空白板）产物**逐字节同** `d67c0f048f0d0423`，**无 `FileNotFoundError` / `IndexError`**；对账 **refs 54/54 · 带号 pad 672/672 · 逐件名集 0 差异**；两次连跑逐字节同。

**C-12 声明（不宣称已过）**：布局解的**内容源 = 已批准受审板**，`provenance_gap` 逐条机检 = SPEC 字段 **11** · L3 布局解 **13** · L3 陈旧 **2** · **仅板来源 28** ⇒ **「坐标源完全去板」在当前冻结输入下不可达**（守恒级见 §7），**E-2 判定归监理**。

---

## 1. 构造链（具名；逐段 sha）

| 段 | 件 | sha16 |
|---|---|---|
| 配置 | `k2/pm_gate/project.yaml` | `56583331599fab0f` |
| 真源网表 | `k2/hw/data/k2_sch.errata-2.yaml`（`project.yaml::nets_yaml`） | `61c4694e3b4df564` |
| canonical SPEC | `L3/SPEC_k2_v4.spec-rev-50.json`（经 `pm_gate.config` 解析） | `ed0950687e5aec97` |
| 库快照 | `k2/hw/lib/ForgeOS.pretty`（36 文件；快照 24 件） | `078f7dc78d980696`（快照 `efcd88b35d6d846c`） |
| 库↔板名集 | `k2/hw/lib/ForgeOS.refmap.json` | `04e16b9f6169cb2e` |
| canonical 布局解 | `L2/PLACEMENT_SOLUTION_v1.json`（**新**） | `b84cc86ec522779f` |
| **构造器** | `python3 k2/tools/k2_gen_v5.py` | `b27ce0c44bfd1afe` |
| 产物 | `K2_OUT_PCB` / `K2_OUT_JSON` / 同名 `.kicad_pro`（JLC 模板 + netclass 注入） | **`d67c0f048f0d0423`** / `3e4b0f92e0893648` / `4a0c3ac9a0e499a7` |

- 链 = **一条命令、零人工步骤、零板输入**（`k2/tools/k2_gen_v5.py` 单件）。
- 下游取证件（图纸 `k2_p3_drawings_v1.py`、BOM `k2_p4_bom_gen_v1.py`、DRC）**不是构造输入**（#K2-26 §2-2：图纸读板仅作下游取证）。

## 2. 坐标迁移（去**运行时**板读）

| 件 | 前 | 后 |
|---|---|---|
| `k2/hw/lib/ForgeOS.refmap.json` | `5a58ce727826df6c`（含 `placement_anchor`） | **`04e16b9f6169cb2e`**（**删 `placement_anchor`**，只留 `ref_to_mod`） |
| `L2/PLACEMENT_SOLUTION_v1.json` | — | **`b84cc86ec522779f`**（54 件 `at` + 逐条 `authority` + `provenance_gap`） |
| `k2_gen_v5.py` | `ef514bd3afac701f` | **`b27ce0c44bfd1afe`**（`load_placement()` 读布局解；**整段删除**陈旧 `NEW_PLACE` 表——该表含已删件 `C89` 与缺陷位 `C85=(31.5,54.5)`） |

**等价性**：迁移前后产物 sha **同为 `d67c0f048f0d0423`**（纯来源迁移，零几何副作用）。

## 3. E-2 实测（「构造链非修补链」三臂）

| 臂 | `hw/k2_v4_8L.l4.kicad_pcb` 态 | rc | 产物 sha16 | `FileNotFoundError`/`IndexError` |
|---|---|---|---|---|
| 0 | 在场（基线） | 0 | `d67c0f048f0d0423` | 无 |
| A | **移走** | 0 | `d67c0f048f0d0423` | **无** |
| B | 换**等价空白板**（同框 120×46、0 器件、`068c4497ec91c15d`） | 0 | `d67c0f048f0d0423` | **无** |

- `l4` 复原后 sha16 = **`d4e81f647be7f980`**（逐字节复原 ✅）。
- 对照（历史，inc88 §3）：**旧链** `k2_p4_build_l5_v1.py` 在臂 A = `FileNotFoundError(:48)`、臂 B = `IndexError` ⇒ 该依赖**已离链**（§8）。

## 4. 产物对账（#K2-27 §五-3）

| 项 | 受审板 `dae8dc8d` | 产物 | 差 |
|---|---|---|---|
| refs（含 4 NPTH） | 58 | 58 | 0（真源器件 54/54，差集 ∅） |
| **带号** pad 合计 | **672** | **672** | **0** |
| 逐件 pad 名集 | — | — | **0 差异** |
| 原始块 pad（记录） | 685 | 676 | **−9 具名** = `U1` 9 枚**无号** `F.Paste` EP 阵列（非电气性；**D 带号口径待裁**） |

- 另 2 类既有具名项不变（#K2-27 §2.2 已裁）：5 件排针面别（THT 全层 ⇒ 铜/电 0 差异，归 **⑥**）· `U6` 354 枚 pad 朝向存储约定（W-8 v2 归零）。

## 5. 确定性（#K2-27 §五-4）

- **8 次连跑**（P2 轮 3 次 + P3 迁移前后 2 次 + E-2 三臂 3 次）PCB/JSON **逐字节同**，sha16 **`d67c0f048f0d0423`**（固定种子 `KIID.SeedGenerator` + uuid5 确定性）。
- 生成器自检 **6/6 PASS**（S1 焊盘重叠 / S2 refdes 对齐 / S4 缺失器件 / S5 坐标范围 / S6 网表一致性 / S8 排针坐标冻结）。

## 6. 守恒（#K2-27 §五-5）

| 检查 | 实测 |
|---|---|
| 冻结四源 | `d4e81f647be7f980` / `fb07d25ac426ff84` / `dd794c54f7ce7417` / `897e8bfde60e2cfe`+`7ce08757eff25557` **逐项不变** ✅ |
| 受审板 / pro | `dae8dc8d48ff5b81` / `35c8f34bde7ac00c` **未改** ✅ |
| 判定器（`--nets errata-2`） | **PASS 7 / FAIL 3**（`zone_filled` 10/18 · `refdes_sets_equal` 54/58 · `pipeline_present`）与基线**逐项同名** ⇒ 不退化 ✅ |
| DRC（受审板，同名 pro） | **69 warning / 0 error / 0 unconnected** = `missing_courtyard` **39** + `lib_footprint_mismatch` **30**；类型集**不变**、违规数**下降**（P1 落库前 = 34 ⇒ 新库使 4 件转 0）⇒ **未放松下限** ✅ |
| 非 45° | 受审板 **0/4720** ✅ |

## 7. 🔴 具名可行域 —— 「坐标源完全去板」在当前冻结输入下**不可达**（守恒级）

`PLACEMENT_SOLUTION_v1.json::provenance_gap`（**机检**，逐条 ref 列名）：

| 权威类 | 条数 | refs | 说明 |
|---|---|---|---|
| SPEC canonical 字段（**逐值一致**） | **11** | `J2 J3 J4 U1 U4 J6 J9 J11 J12 J13 C82` | `components.{connectors,mcu,oring,pin_headers,anchor_fixes}` |
| L3 布局解（**逐值一致**） | **13** | `C73 D2 L1 R35 R36 R37 R38 R39 R40 R41 R43 R44 R45` | `p3_placement_solution.json`（basis = SPEC `layer_plan.strap_domain_v32` 域/排法/0603 + 就近球求解） |
| L3 布局解 **陈旧**（板侧后修） | **2** | `C86`（解 `32.4,36.0` → 板 `31.55,58.85`）· `R42`（解 `86.6,59.55` → 板 `93.3,61.55`） | 解落后于 `K2-P4-C86-RELOCATE-FIX-v1` 等板侧修复 ⇒ **以板为准** |
| **仅板来源**（冻结输入中**无**任何非板坐标） | **28** | 其余 28 件 | 无 SPEC 字段、无布局解条目 |

⇒ **可用权威覆盖 26/54，且其中 2 条陈旧** ⇒ 以现有冻结输入**无法构造**完全非板来源的 54 件坐标；本件**不**把「以板为准」的落位记作「已构造」。

**请监/owner 裁（三选一，ENG 不择一）**：
- **(a)** 认可 `L2/PLACEMENT_SOLUTION_v1.json` 为「**真源 layout 方案**」（先例：`#K2-26 §3-1` 库快照「以板为准」重建 + 「库↔板名集」）；
- **(b)** 另派 **placement 求解器**工作包（由 SPEC 域/规则真构造 54 件坐标）；
- **(c)** 授权 **bump SPEC canonical 几何字段**承载该表（版本 bump + 监理签认）。

**未裁前**：ENG 不主张 E-2 已过、不刷新登记簿、不以本件宣告任何缺陷已消。

## 8. 修补链退役（#K2-27 §五 尾：「收敛或退役」）

- 构造链**不含任何 `k2_p4_*` 脚本**；`k2_p4_build_l5_v1.py`（读 `l4`）与 `k2_p4_composed_land_v2.py`（板→板）**已离链**（E-2 三臂实测为证）。
- 仓库内 44 个 `k2_p4_*` 工具均为**一次性载体操作/取证**（各自有 ruling 授权留痕），**非构造输入**；**本件未删除任何文件**（删除须监另裁；如需物理退役至 `retired/` 请裁）。

## 9. 复跑链（确定性）
```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# 构造链（期望 rc=0 · 自检 6/6 · 器件 54 · pads 672 · G10 8-10-4）
K2_OUT_PCB=/tmp/opencode/p3a.kicad_pcb K2_OUT_JSON=/tmp/opencode/p3a.json python3 k2/tools/k2_gen_v5.py
K2_OUT_PCB=/tmp/opencode/p3b.kicad_pcb K2_OUT_JSON=/tmp/opencode/p3b.json python3 k2/tools/k2_gen_v5.py
cmp /tmp/opencode/p3a.kicad_pcb /tmp/opencode/p3b.kicad_pcb        # 期望 IDENTICAL（sha16 d67c0f048f0d0423）
# E-2 臂 A：移走 l4（先备份！）再跑 → 期望同 sha；臂 B：换等价空白板 → 期望同 sha；跑完逐字节复原 l4
# 对账（带号 672/672、逐件名集 0）见 §4；守恒（判定器/DRC）见 §6
python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l5.kicad_pcb \
  --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro --root k2
```
**fail-closed**：P4 未全绿不下单、不出交付 Gerber；P5 未开。

## 10. 边界

**本件已改（#K2-27 §五 授权）**：`k2/tools/k2_gen_v5.py` · `k2/hw/lib/ForgeOS.refmap.json` · **新增** `k2/pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json` · 本件 · P1/P2 件**勘误**（§1.3 表述 + DRC 读数，同批）。
**未改**：受审板 / pro · 冻结四源 · SPEC 原件（rev-47..50）· 真源 yaml（三件）· `criteria/**` · `_shared/**` · `fp-lib-table` · 模板 · `project.yaml` · 库快照文件 · L5 旧包 · `.omo/supervision/**`；**未装 `k2/pipeline.yaml`**；**未出 Gerber**；**未动 §四 排队项**（E-4 / E-3 / ⑥ / refplane / 其余闭环表未闭项）；未派 WORKER；未新增检查齿。

—— ENG（ARCHER）· 2026-09-18 · P3 证据件 · 构造器 `b27ce0c44bfd1afe` · 布局解 `b84cc86ec522779f` · 产物 `d67c0f048f0d0423` · 受审板 `dae8dc8d48ff5b81`（未动）
