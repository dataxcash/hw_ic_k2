# R930 · `eda_eng` 基线落地（#K2-358）：**产品可独立运行 · ARCHER 转岗程序员**

日期 2026-09-28 · 件 `L2/EDA_ENG_CLI_DEMO_v1.json`（`1ab6f224e68fb9e3`）

## 〇、验收线（#K2-358 §二.1）

> **无 LLM 在场可完整运行 —— 这是验收线。** 本窗以**冻结 KiCad python**（真实 EDA 工具链）**从 shell 直接跑**，全程**无 LLM 参与调用链**，读数落件。

## 一、产品 = `eda_eng`（`k2/tools/eda_eng/` ＋ 入口 `k2/tools/eda_eng.sh`）

| 子命令 | 作用 | 状态 |
|---|---|---|
| `eda_eng eco` | ECO 文书链**校验**（字段／数字判据／受控登记） | ✅ |
| `eda_eng docs` | 文档链（ECO-方案-图-记录）状态 | ✅ |
| `eda_eng verify` | **判卷**：C1 连通 · C2 DRC 零新增 · C3 等长 · C4 倒角 · C5 走线真变 | ✅ |
| `eda_eng exam A\|B` | 两考题回归定义（可直接 `--board/--drc` 判卷） | ✅ 定义／判卷可用 · 执行待引擎 |
| `eda_eng place` | 放置（**声明式**：读放置源＋场景位移 · **不碰板**） | ✅ v1 |
| `eda_eng route` | **rip-up & reroute 引擎** | ❌ **未实现**（如实 `NOT_IMPLEMENTED` · 退出码 2） |
| `eda_eng selftest` | **回归测试**（CI 入口） | ✅ |

## 二、本窗实测读数（机器产生的件 · 非手写声明）

| 命令 | 退出码 | 判定 |
|---|---|---|
| `selftest` | 0 | **11 tests / 0 failures / 0 errors / PASS** |
| `eco` | 0 | **PASS**（骨架齐 · 三单表单 complete ＋ 全在册） |
| `docs` | 0 | **PASS**（五环状态在册） |
| `verify`（受审 = attempt2 FAILED 板） | 1 | **FAIL**（C1 连通 · C2 DRC · C4 倒角 三项不过 ⇒ 与在册判定一致） |
| `exam B` | 1 | 定义在册 ＋ **引擎未实现** ⇒ 今日**不可能通过**（如实） |
| `place`（U1/U2/U4/U5 +5mm） | 0 | 声明式位移 ×4 · `board_touched=false` |
| `route --exam B` | **2** | **NOT_IMPLEMENTED**（能力不存在，不许冒充） |

## 三、岗位与纪律（#K2-358 §二.3 / §三）

- **ARCHER 岗位 = 开发 `eda_eng`**：写代码 · 跑测试 · 修失败；
- **禁 LLM 亲手编辑 `.kicad_pcb`**：文本级手术全数封存（承 #K2-347/356）；**板面变更唯一入口 = `eda_eng` 命令**（本窗**零板面改动**）；
- **考题 = 回归测试**：`eda_eng exam A|B` 已可 CI 重复执行；**考不过 = 功能不存在**；
- **存量一次性脚本**（C17 v1／文本剪辑等）**逐步收编或废弃**；收编前**禁新增使用**（本窗未使用任何存量一次性脚本改板）；
- 承 #K2-356/357：考不过禁上板 · 无 ECO 不动板 · 冻结四源 **4/4** · C13 · 无 WORKER · Gerber/下单停线。

## 四、下一步（引擎本体）

`eda_eng route` 是**唯一缺口**，也是整个专项的目标：按 #K2-356 §二.1 合同（入＝新放置＋约束；出＝全连通＋DRC 零新增＋倒角/等长保持）实现，并以 `exam A|B` 为**CI 回归**验收。**引擎过闸前不上板。**

LEGAL-ESCALATION: none
OWNER-ITEMS: 0
