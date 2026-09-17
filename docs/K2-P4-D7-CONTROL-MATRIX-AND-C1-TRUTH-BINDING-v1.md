# K2 · P4 · `D-7` **正/负控矩阵**（9 案）+ 三源变体的 **C-1 真源绑定**取舍 · v1 · 2026-09-18

> 缘起：handoff inc49 §6-3-(a)「给 `check_netlist_connect` 的 ①②③ 合读写正/负控用例，供共享层修后验收」。
> 本会话仍**无监理放行** ⇒ ENlegal 面。仪器：`/tmp/opencode/inc50`（`_shared/eda_core` 副本 + 以 `K2_NC_SOURCES` 选源的**控制仪器**）+ 3 个沙箱（`sb_e1`/`sb_e2`/`sb_bogus`）。**仓库零写入。**

## 0. 结论

1. **控制矩阵成立**：正控（三源合读 → 1 处）与**三个负控**（全不认 → 106/105 处；注入伪网 → 2 处）**同时成立** ⇒ `netlist_connect` 在 D-7 后**不空转**，正/反两向断言都仍会咬。
2. **②（真源 `sheets[].placements[].nc`）是承重项**：单独启用即把 106 处降到 **2 处**；③（`pintype`）单独启用降到 **1 处**；①（top-level `nc`）对 `errata-1` 无效（该键不存在）。
3. **建议 `D-7a = ①+②`（不启用 ③）**：`errata-1` ⇒ **2 处**，且**两处同根**（`网 'PWR_5V_KEY' 不存在` 与 `非声明悬空 C89/A_1`）⇒ **裁定 `C89/A` 一项即两处同消（→0）**。
   理由：③ 取自 **netlist 自身** ⇒ 属 **C-1「判据真源 = 被验对象自身」自证**（`_shared/eda_core/truth_binding.py::SelfSourceError`，sha `0683713df1003df3`）。① 与 ② 均落在**真源网表 yaml** 内 ⇒ 外部真源，符合 C-1。
4. 若采用 `D-7b = ①+②+③` ⇒ `errata-1` 剩 **1 处**，但**以自证换绿**，须由监理/共享层属主明示 C-1 例外，ENG **不建议**。

## 1. 控制矩阵（9 案，全部实跑；仪器 `/tmp/opencode/inc50`，`K2_NC_SOURCES` 选源）

| # | 沙箱 | 启用源 | `netlist_connect` FAIL | 首条失败 | 性质 |
|---|---|---|---|---|---|
| ① | `sb_e1`（errata-1） | ①+②+③（候选补丁行为） | **1** | `网 'PWR_5V_KEY' 在 KiCad netlist 中不存在` | 正控 |
| ② | `sb_e1` | ① only | **106** | 同上 | 源①对 errata-1 无效 |
| ③ | `sb_e1` | ② only | **2** | 同上（另 1 = `C89/A_1`） | **②承重** |
| ④ | `sb_e1` | ③ only | **1** | 同上 | ③可独覆反向断言 |
| ⑤ | `sb_e1` | **none** | **106** | 同上 | **负控（不空转）** |
| ⑥ | `sb_e2`（errata-2） | ①+②+③ | **0** | — | 正控 |
| ⑦ | `sb_e2` | ① only | **0** | — | 源①对 errata-2 足用 |
| ⑧ | `sb_e2` | **none** | **105** | `非声明悬空: C89/A_1 …` | **负控** |
| ⑨ | `sb_bogus`（errata-1 **注入伪网** `BOGUS_NEGCTL_ZZZ`） | ①+②+③ | **2** | `网 'PWR_5V_KEY' …` + `网 'BOGUS_NEGCTL_ZZZ' …` | **正向断言负控** |

读法：
- ⑤/⑧ 证明**白名单来源是承重的**（全不认即回到 105/106 误报）；
- ⑨ 证明 **D-7 不豁免正向断言**（真源声明了 netlist 没有的网 ⇒ 仍 FAIL）；
- ③/④ 交叉印证 inc49 的独立复算（② → 反向断言剩 1；③ → 反向断言剩 0），**两法同值**。

## 2. 三源变体与推荐

| 变体 | 源 | errata-1 结果 | C-1 契合 | 评价 |
|---|---|---|---|---|
| **D-7a（推荐）** | ①+② | **2 处（同根 `C89/A`）** | ✅ 真源网表 yaml 为外部真源 | 修口径 + 暴露**唯一真项**，不掩盖 |
| D-7b | ①+②+③ | 1 处 | ⚠️ ③ = netlist 自证 | 以自证换绿，须明示例外 |
| 现状 | ① | 106 处 | ✅ 但源①在真源侧不存在 | 批量误报（D-7 本体） |

**② 的语义**：`sheets[].placements[].nc` 是**设计侧**逐器件 NC 声明（本板 104 条，`errata-1` 与冻结真源逐条相同）⇒ 与 `nets` 同源同文件，属**方案真源**而非产物 ⇒ C-1 允许。
**③ 的语义**：netlist 节点 `pintype` 含 `no_connect` 是 **KiCad 从原理图回吐的产物自述** ⇒ 判据以其为准 = 自己给自己打分（C-1 现象原文：「验收清单读**方案自己的声明**——自己给自己打分」）⇒ 即使本板 105/105 全带该标记，也**不宜**作为白名单主源。

## 3. C-1 依据（引用）

`_shared/eda_core/truth_binding.py`（sha `0683713df1003df3`）：
- 模块头：「现象：验收清单读**方案自己的声明**（方案说 6A，检查器就确认 6A）—— 自己给自己打分。根因：判据真源绑在**被验对象自己**身上」
- `SelfSourceError`：「自证：判据真源 = 被验对象自身（C-1 铁律禁止）」
- `assert_external()`：「**自证即拦**：真源 = 被验对象 ⇒ raise（拒绝，非告警）」

⇒ D-7 的实现选择**不是纯口味问题**，而是 C-1 的直接适用面 ⇒ **请共享层属主/监理裁 D-7a / D-7b**（ENG 建议 D-7a）。

## 4. 对 F-10 / 路径 甲·乙 的收敛表述（**取代 inc49 §4 与 inc46 证据件 §2**）

- **`pipeline_present` 的闸口 = 「D-7a 口径修正」+「`C89/A` 一次具名裁定」**；两项皆闭 ⇒ **路径乙（`errata-1` + D-7a）可达 0 FAIL，且不涉真源新增**。
- `errata-2`（路径甲）**仍是工作解**，但属「删真源声明的网 + 把真源唯一连接的引脚声明为 NC」⇒ **C-12 同型（以缩口径达成绿）**，须先证 `C89/A` 确为 NC、`PWR_5V_KEY` 确为伪网；否则**不得**采用（owner 铁律 §一）。
- 量级对比（同一件事的两种表述）：现行判据口径 **106 处** → D-7a **2 处（同根）** → 裁定后 **0 处**。

## 5. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw
export SHARUN=/home/fila/jqdDev_2025/ic_hw/AppDir/sharun
# 仪器：/tmp/opencode/inc50 = _shared/eda_core 副本 + K2_NC_SOURCES 选源补丁（易失可重建）
S=/tmp/opencode/inc50
for cfg in "sb_e1 top,placements,pintype" "sb_e1 top" "sb_e1 placements" "sb_e1 pintype" "sb_e1 none" \
           "sb_e2 top,placements,pintype" "sb_e2 top" "sb_e2 none" "sb_bogus top,placements,pintype"; do
  set -- $cfg
  (cd $S/$1 && K2_NC_SOURCES="$2" PYTHONPATH=$S python3 -c "
import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))" 2>&1 | grep -E 'netlist_connect:|连接校验失败|非声明悬空' | head -2)
done
# 期望：①1 ②106 ③2 ④1 ⑤106 ⑥0 ⑦0 ⑧105 ⑨2
```

## 6. 边界

本件**只读 + `/tmp` 副本/仪器（未落库）**：未改 `_shared/**`（D-7 仅作用于 `/tmp` 副本）、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；未新增仓库内判据/脚本（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 真源 `dd794c54f7ce7417` · 容器 `_shared` HEAD `0ec324b`
