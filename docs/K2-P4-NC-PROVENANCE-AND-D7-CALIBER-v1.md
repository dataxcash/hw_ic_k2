# K2 · P4 · **NC 声明来源核验**（F-10 定量的）⇒ 105 条中 **104 为判据口径误报** + **新登记 D-7** + 补丁端到端验证 · v1 · 2026-09-18

> 缘起：handoff inc48 §6-3-(d)「errata-1/2 的 105 条 nc 逐条来源核验（供监理定设计意图）」。本会话仍**无监理放行** ⇒ ENlegal 面。
> 仪器：`kicad-cli sch export netlist`（`AppDir/sharun`）取真实 netlist + 引擎自带 `eda_core.sch_gate.checks.netlist.load_netlist`（**与判据同源，不复用自造解析**）+ `/tmp/opencode/inc49/shared/` 的 `checks.py` 补丁副本。**仓库零写入。**

## 0. 结论（一表定案）

| 反查对象 | 「非声明悬空」数 | 判 |
|---|---|---|
| `errata-1`（= `pm_gate/project.yaml` 现行 `nets_yaml`）**按现行判据** | **105** | ❌ **误报**：104 条在**冻结真源**内已声明，1 条在 **netlist 自身 `pintype`** 内已声明 |
| 真源权威形态 `sheets[].placements[].nc` **单独**作为白名单 | **1** | 仅剩 `C89/A_1`（真源未声明的唯一一条） |
| **netlist `pintype` 含 `no_connect`** 单独作为白名单 | **0** | **105/105 全带 `no_connect`** |
| `errata-2`（top-level `nc`） | 0 | 但见 §4 的 C-12 风险 |

**结论 1（F-10 重定性）**：F-10 **不是**「105 个引脚的设计意图问题」，而是 **(a) 判据口径缺陷（新登记 D-7）104 条 + (b) 唯一一处真源↔图不一致 1 条（`C89/A` ↔ 网 `PWR_5V_KEY`）**。
**结论 2**：`errata-1` 的 `sheets[].placements[].nc` 与冻结真源**逐条相同（104/104）** ⇒ errata-1 **并非**「缺 NC 声明」的坏件；它缺的只是判据所读的那个 key。
**结论 3**：给定 D-7 补丁，`errata-1` 的 `netlist_connect` 由 **106 处 → 1 处**（唯一残余 = `网 'PWR_5V_KEY' 在 KiCad netlist 中不存在`），**已端到端实跑验证**（§2）。
**结论 4**：`errata-2` 之所以 0 FAIL，靠的是「删掉真源声明的网 `PWR_5V_KEY` + 把真源唯一连接的引脚 `C89/A` 声明为 NC」⇒ 属**为过判据而动真源**（owner 铁律 §一「以缩口径达成绿 = C-12 同型，禁」）⇒ **请监理按 C-12 口径审视路径甲**，勿默认其为正解。

## 1. 三种 NC 声明来源（实测）

| # | 来源 | 位置 | 实测 |
|---|---|---|---|
| ① | **真源权威形态** | `k2_sch.yaml` → `sheets[].placements[].nc` | **104 条**，涉 5 器件 `J2/J3/J4/U4/U6`；例 `{"ref":"J2","symbol":"SlimSAS_x8","nc":["SMB_CLK_B","SMB_DATA_B"]}`。**`errata-1` 与之逐条相同（104/104）**；`errata-2` 亦相同 |
| ② | **top-level 形态** | 同 yaml 顶层 `nc: [[ref,pin], …]` | 真源/`errata-1`：**无该键**；`errata-2`：**105 条**（= ① 的 104 + `C89/A`） |
| ③ | **KiCad 侧声明** | netlist 节点 `pintype` | 105 个 unconnected 节点 **全部**含 `no_connect`：`bidirectional+no_connect` 70 · `passive+no_connect` 21 · `no_connect` 12 · `input+no_connect` 2 |

现行 `check_netlist_connect` 的反向断言**只读 ②**（`spec_data.get("nc")`，`checks.py:91`）⇒ ①③ 被完全忽略 ⇒ 产生 105 条误报。

## 2. 新登记 **D-7**（共享引擎判据口径缺陷）+ 补丁 + 端到端验证

**D-7**：`_shared/eda_core/pipeline/checks.py::check_netlist_connect` 的 NC 白名单**仅取 top-level `nc`**，忽略
(a) 真源权威形态 `sheets[].placements[].nc` 与 (b) netlist 自带 `pintype` 的 `no_connect` ⇒ 对**合规真源**产生批量误报（本板 105 条）。
与 D-2 同族（共享引擎、fail-closed/口径面），**非本板补丁**（计划 §⑥-4）。

**候选补丁（仅 `/tmp`，未落库）**：

```diff
     spec_data = yaml.safe_load(nets_yaml.read_text(encoding="utf-8"))
     want = spec_data.get("nets") or {}
+    # D-7: NC 声明三种规范来源 ①top-level nc ②sheets[].placements[].nc ③netlist pintype no_connect
     nc_declared = {(r, p) for r, p in spec_data.get("nc") or []}
+    for _sh in spec_data.get("sheets") or []:
+        for _pl in _sh.get("placements") or []:
+            for _pin in _pl.get("nc") or []:
+                nc_declared.add((_pl["ref"], str(_pin)))
@@ 反向断言
         for ref, _p, fn, _pt in n["nodes"]:
             fn = fn or ""
+            if "no_connect" in (_pt or ""):        # ③ KiCad 侧已声明 no_connect
+                continue
             if not any(ref == r and fn.startswith(p) for r, p in nc_declared):
```

**端到端验证**（沙箱 `/tmp/opencode/inc49/d7`：`pipeline.yaml` 指向 `errata-1`，同一 `--root`）：

| 引擎 | `verify/netlist_connect` | 首条失败 |
|---|---|---|
| 原版 `_shared` | **FAIL 106 处** | `非声明悬空: C89/A_1 …` |
| **D-7 补丁副本** | **FAIL 1 处** | `网 'PWR_5V_KEY' 在 KiCad netlist 中不存在` |

⇒ 105 条误报**全部消失**（104 由 ①、1 由 ③），残余**仅 1 条真项**（§3）。`sch_structural` 两项均 PASS。

## 3. 唯一真项：`C89/A` ↔ 网 `PWR_5V_KEY`（真源↔图不一致，须一次裁定）

| 侧 | 声明 |
|---|---|
| 真源 `nets` | `PWR_5V_KEY` 只含 **1 个节点：`C89/A`**（`nets` 键数 101，该网仅 1 节点 ⇒ **孤立单节点网**） |
| 原理图 netlist | `C89` pin1 = `unconnected-(C89-A-Pad1)`，`pintype = passive+no_connect`（`pinfunction = A_1`） |
| `errata-2` 的处理 | **删** `PWR_5V_KEY`（nets 101→100）+ **加** `C89/A` 到 top-level `nc` |

⇒ 二者互斥，须**一次具名裁定**（ENG 不判）：`C89/A` 应连到 `PWR_5V_KEY`（则修**原理图/生成链**）**或**确为 NC（则修**真源 `nets`**，属真源改动须放行）。
**旁证**：`PWR_5V_KEY` 是**单节点网**（仅 C89/A 一个节点；`net_declared_realized` 类判据要求每声明网 ≥2 pad）⇒ 该网本身很可能就是「声明未落地」的伪网，与 l4 期 `PWR_5V_KEY` 遗留有关。此点支持「修真源 nets」一侧，但**判定归监理**。

## 4. 对既有结论的修正（**取代** inc46 证据件 §2 的定性；数值不变）

| inc46 原表述 | 本件修正后 |
|---|---|
| 「`errata-2 = 真源 − PWR_5V_KEY + 105 nc` ⇒ 该真源修正是 `netlist_connect` PASS 的**唯一**原因」 | ✅ 数值成立，但**性质**是「把①形态**转写**为②形态 + 删 1 网 + 加 1 NC」；其中 **104/105 属转写**（真源早已声明），**非**新增设计意图 |
| 「F-10（nc 声明 / 真源侧新增）是 `pipeline_present` 的实质闸口」 | 修正为：闸口 = **D-7 口径修正** + **`C89/A` 一次具名裁定**；「105 条 nc 是否设计意图」**不再是问题**（真源已声明 104，netlist 自带 105） |
| 「路径乙（改 check 参数指向现存产物）不可行（106 处 FAIL）」 | 修正为：**乙在 D-7 修复后仅剩 1 处**；乙不再因「105 误报」而不可行，**且不涉真源新增** |
| 路径甲 = 「先提升 errata-2 + BOM 再装」 | **保留但加风险标注**：errata-2 同时**删除真源声明的网**并**把真源唯一连接的引脚声明为 NC** ⇒ 若采用，须先证明 `C89/A` 确为 NC 且 `PWR_5V_KEY` 确为伪网；否则**属 C-12 同型「以缩口径达成绿」**（owner 铁律 §一 / §二） |

## 5. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① NC 三来源计数
python3 -c "
import yaml
L=lambda p:yaml.safe_load(open(p,encoding='utf-8'))
t=L('k2/hw/data/k2_sch.yaml'); e1=L('k2/hw/data/k2_sch.errata-1.yaml'); e2=L('k2/docs/drafts/j9-wiring-option-a/k2_sch.errata-2.draft.yaml')
pl=lambda d:[(p['ref'],str(pin)) for sh in d.get('sheets') or [] for p in sh.get('placements') or [] for pin in p.get('nc') or []]
print('真源 placements nc',len(pl(t)),' errata-1',len(pl(e1)),'相同',set(pl(t))==set(pl(e1)))
print('errata-1 top-level nc',len(e1.get('nc') or []),' errata-2 top-level nc',len(e2['nc']),' nets',len(t['nets']),len(e1['nets']),len(e2['nets']))"
# ② 反向断言复算（三种白名单，含 pintype）
#    见本件 §0 表；核心 = load_netlist + 对 unconnected- 节点核 fn.startswith(p)
# ③ D-7 端到端（沙箱；期望 106 → 1）
S=/tmp/opencode/inc49/d7; export SHARUN=/home/fila/jqdDev_2025/ic_hw/AppDir/sharun
(cd $S && PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))" 2>&1 | grep -E 'verify/|失败')
(cd $S && PYTHONPATH=/tmp/opencode/inc49/shared python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))" 2>&1 | grep -E 'verify/|失败|网 ')
```
（`/tmp/opencode/inc49/shared/eda_core` = `_shared/eda_core` 副本 + D-7 补丁；易失可重建）

## 6. 边界

本件**只读 + `/tmp` 副本/补丁（未落库）**：未改 `_shared/**`（补丁仅作用于 `/tmp` 副本）、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；未新增仓库内判据/脚本（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 真源 `dd794c54f7ce7417` · 受审板 `6ff49da5678c2108`
