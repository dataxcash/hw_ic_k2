# K2 · P4 · **路径甲（`errata-2`）不可采用性 · C-12 同型逐条对照草案** · v1 · 2026-09-18

> 缘起：handoff inc73 §6-3-**(cc)**「`errata-2`（甲）不可行性的 C-12 同型证明草案（把『删网 + 105 NC』与 C-12 判读逐条对照，纯文档）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读取证 + 纯文档**（/tmp 跑引擎），未改真源/判据/共享层/板/pro/SPEC（仅新增本证据件）。
> 锚：真源 `dd794c54f7ce7417` · `errata-1` `17d540f058631a5e` · `errata-2` 草案 `bdacbf944ca0c796` · 在库判据 `897e8bfde60e2cfe`+`7ce08757eff25557` ·
> 共享引擎 `checks.py` **`02b41e8b6d6d9b3a`**（容器）/ **`e88c70aaa56ce22f`**（k2 `_shared`，D-5 分叉；两树**同址同缺陷**，行 93）· `pm_gate/project.yaml` `9cee872bd6fbdc67`（`nets_yaml: hw/data/k2_sch.errata-1.yaml`）。
> **归属**：本件**只出证据与对照，不判**。L1（电源域 / 网范围）⇒ **owner ⑤**；C-12 定性 ⇒ **监理**。ENG 不择一、不落件。

## 0. 结论（对 handoff 命题的一处**修正**）

1. **甲不是"技术上不可行"**。实测（§2）：甲装进沙箱后 `engine verify` **3 项全 PASS**（含 `netlist_connect`），**且在原版（未修 D-7）引擎上就 PASS**。
2. 甲的问题是**程序越权**与**归因错误**，两者叠加 ⇒ **在 owner ⑤ 未裁前不可采用**：
   - **(程序)** 甲唯一改变设计真值的动作 = **删网 `PWR_5V_KEY` + 把其唯一节点 `C89/A` 声明 NC**（§1，101→100 网）。这**恰好就是 ⑤ 的裁题本身** ⇒ 执行甲 = ENG 代 owner 做 L1 裁定。
   - **(归因)** 105 条 NC 里 **104 条是真源早已声明的形态转写**（`sheets[].placements[].nc` 104/104，且 KiCad netlist 自身 105/105 带 `pintype no_connect`）。它们的"失败"是**检查器口径缺陷 D-7**，不是设计意图缺口。把 104 条写进真源 = **把判据的盲区搬进被审对象**（§3 逐条）。
3. **C-12 命中为"附条件命中"**：`104 条`命中 C-12 上半（**判据盲区未消除，只在被审对象里补白名单**）；`1 条`命中 C-12 下半（**以缩口径达成绿**）—— **当且仅当** ⑤ 裁定「`C89/A` 确为 NC ∧ `PWR_5V_KEY` 确为伪网」时，这 1 条**不**构成 C-12 同型，而是**真值修正**（此时与 ⑤ 选项① 同义）。
4. ⇒ **甲可行 ⟺ ⑤ 先裁「①」**；且 **D-7 修复后甲的 105 NC 整块冗余**（可删）。故 ENG 建议名称为 **甲′ = D-7（共享层口径修）+ ⑤①（真值裁后落件）**，甲本体不进安装链。
5. 甲**不涉** DRC 下限放松、不涉 `ignore`/豁免、不涉阈值收窄 ⇒ 违规面仅上述两项。

## 1. 甲的三项动作（实测，非叙述）

| # | 动作 | 实测数值 | 改的是"设计真值"还是"判据口径" |
|---|---|---|---|
| A1 | **删网** `PWR_5V_KEY` | 真源 `nets` **101 → 100**；该网真源仅有 **1 个节点** `C89/A` | **设计真值**（须 L1 裁定） |
| A2 | 把 `C89/A` 加入 top-level `nc` | errata-2 `nc` **105** 条 | **设计真值**（同上） |
| A3 | 把 `sheets[].placements[].nc` 的 104 条**转写**为 top-level `nc` | 真源 placements.nc **104** 条，与 `errata-1` **逐条相同（104/104）**；errata-2 top-level `nc` = 104 + 1 = **105** | **判据口径**（真值未变） |

复算：`真源 nets=101 / errata-2 nets=100 / removed=['PWR_5V_KEY'] / placements.nc 104==104 identical / top-level nc 105 == placements(104) + [('C89','A')]`。

## 2. 端到端四方矩阵（本会话**新跑**，独立复现；沙箱见 §5）

| # | `nets_yaml` | 引擎 | `netlist_connect` | 结论 |
|---|---|---|---|---|
| 1 | `errata-1`（`pm_gate` 现行值） | **原版**（容器 `02b41e8b`） | **FAIL 106 处** | D-7 缺陷现状 |
| 2 | `errata-1` | **D-7 修版** | **FAIL 1 处**（仅 `网 'PWR_5V_KEY' 在 KiCad netlist 中不存在`） | 104 条确为**误报** ⇒ 缺口在**检查器**，不在真源 |
| 3 | **`errata-2`（甲）** | **原版**（未修！） | **PASS** | **甲靠改真源让"原版判据"变绿**（判据盲区分毫未动） |
| 4 | `errata-2`（甲） | D-7 修版 | PASS | 甲在 D-7 后**冗余** |

> 对照 #2 vs #3 是本件的核心：**同一个 PASS**，路径 #2 修的是**判据**（根因载体），路径 #3 动的是**被审对象**（真源）。owner 铁律 §一 明列「以**缩口径 / 具名豁免 / 关判据**达成绿 —— **C-12 同型，禁**」。

## 3. 逐条对照（甲动作 × C-12 判读）

C-12（《能力缺口账本 v1》）：**门禁吞数 / 判据自废** —— 「判据的**判定动作**与**报告动作**分离：报告只记不判；**且判据可被被审对象一侧的配置关掉**」（K2 实证：`m13_v57_co146_jlc_dfm_gate.json` fails 仅 2 项）。

| # | 甲的动作 | 规模 | 对应 C-12 要素 | 命中？ | 证据 | 结论（ENG 陈述，判定归监理） |
|---|---|---|---|---|---|---|
| 1 | A3：104 条 placements.nc 转写进 top-level `nc` | 104 条 | 「判据盲区**未消除**，改被审对象补白名单」 | **命中** | 真源 placements.nc 104/104 与 errata-1 相同；netlist 105/105 `pintype no_connect`；`checks.py:93` 只读 top-level `nc` | 属 **D-7 口径缺陷的绕过**；正确载体 = 共享引擎（gate 侧），非真源。**建议整块删除** |
| 2 | 被审对象（真源）**自带其豁免清单** | 结构 | 「判据可被**被审对象一侧的配置**关掉」 | **命中** | 白名单来源 = `spec_data.get("nc")`，即**被审 yaml 自身** | 自证结构（与 C-1 同族）；豁免清单应由**判据侧**持阈值/白名单并留痕 |
| 3 | A1+A2：删网 `PWR_5V_KEY` + 声明 `C89/A` NC | **1 条** | 「以**缩口径达成绿**」 | **附条件命中** | 真源该网仅 1 节点 `C89/A`；`errata-2` 删网后 nets=100 | ⑤ 未裁前执行 = **ENG 代 owner 做 L1 裁定** ⇒ 不可采用；**若 ⑤ 裁定①「确为 NC 且为伪网」⇒ 转为真值修正（不构成 C-12）** |
| 4 | （对照）未改 DRC 下限 / 未动 `ignore` / 未收窄阈值 | — | — | **不命中** | 甲不涉 `.kicad_pro`；在库 `ignore` 计数不变 | 甲的问题**仅** #1–#3 两项 |
| 5 | （对照）甲在**未修**引擎上即 PASS | — | 这正是 C-12 的**症状**（"不合格/未修判据也能 PASS"） | **命中** | §2 矩阵 #3 | 证明 PASS 的来源是**真源改写**而非**判据修复** |

## 4. 判据侧的正确修法（替代甲）

| 项 | 内容 | 归属 | 现状 |
|---|---|---|---|
| **D-7** | `check_netlist_connect` 的 `nc_declared` 扩为三来源：① top-level `nc` ② `sheets[].placements[].nc` ③ netlist 节点 `pintype` 含 `no_connect` | **共享层**（gate 侧）· 已入共享层 5 修包（D-7） | 修版实测 106→1（§2 #2） |
| **⑤** | `C89/A` 与 `PWR_5V_KEY` 的**一次具名裁定**（① 删网+NC / ② 接既有轨） | **owner（L1）** | **待裁（唯一 owner 闸口）** |
| BOM / 真源 | 落件前置（`k2/fab/k2_v4_bom.csv`、真源） | 监理/放行 | 待裁 |

⇒ 正确链 = **先 D-7（修载体）→ 再 ⑤（裁真值）→ 后装 `pipeline.yaml`**。此链下**甲 A3 全部冗余、A1/A2 由 ⑤ 裁后按裁定执行**（不是由 ENG 借"过判据"之名执行）。

## 5. 复跑（确定性；/tmp 易失须重建）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 甲的三项动作计数
python3 - <<'PY'
import yaml
L=lambda p: yaml.safe_load(open(p,encoding='utf-8'))
t=L('k2/hw/data/k2_sch.yaml'); e1=L('k2/hw/data/k2_sch.errata-1.yaml')
e2=L('k2/docs/drafts/j9-wiring-option-a/k2_sch.errata-2.draft.yaml')
pl=lambda d:[(p['ref'],str(x)) for sh in d.get('sheets') or [] for p in sh.get('placements') or [] for x in p.get('nc') or []]
print('nets',len(t['nets']),len(e1['nets']),len(e2['nets']),'removed',sorted(set(t['nets'])-set(e2['nets'])))
print('placements.nc 真源/errata-1/errata-2 =',len(pl(t)),len(pl(e1)),len(pl(e2)),'真源==errata-1:',set(pl(t))==set(pl(e1)))
print('top-level nc errata-1/errata-2 =',len(e1.get('nc') or []),len(e2.get('nc') or []))
PY
# ② 四方矩阵（沙箱 = 本会话新建 /tmp/opencode/inc74/cc/sb_*；D-7 引擎 = /tmp/opencode/inc49/shared）
export SHARUN=$PWD/AppDir/sharun
E(){ ( cd "$1" && PYTHONPATH="$2" python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))" 2>&1 | grep -E 'verify/netlist_connect|失败' ); }
E /tmp/opencode/inc74/cc/sb_e1   $PWD/_shared                     # 期望 FAIL 106
E /tmp/opencode/inc74/cc/sb_e1d7 /tmp/opencode/inc49/shared       # 期望 FAIL 1
E /tmp/opencode/inc74/cc/sb_e2   $PWD/_shared                     # 期望 PASS（甲在原版引擎上即绿）
E /tmp/opencode/inc74/cc/sb_e2d7 /tmp/opencode/inc49/shared       # 期望 PASS
```

## 6. 边界

本件**只读取证 + 纯文档 + `/tmp` 沙箱**：未改真源 / `errata-1` / `errata-2` 草案 / 板 / pro / SPEC / 生成器 / 模板 / 图纸 / `criteria/**` / `_shared/**`（D-7 补丁仅作用于 `/tmp` 副本）；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**（沙箱内副本不属仓库）；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增检查齿**（owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 真源 `dd794c54f7ce7417` · `errata-2` 草案 `bdacbf944ca0c796` · 判定器 `897e8bfde60e2cfe`
