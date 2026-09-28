# `eda_eng` —— K2 独立确定性 EDA 工程软件（#K2-358）

> **产品定义**：本软件**无 LLM 在场可完整运行**。板面变更的**唯一入口** = 本软件的命令。
> **ARCHER 岗位** = 开发本软件（写代码／跑测试／修失败）；**禁止再亲手编辑 `.kicad_pcb`**（文本级手术全数封存 · 承 #K2-347/356/358）。

## 命令

| 命令 | 作用 | 状态 |
|---|---|---|
| `eda_eng eco` | ECO 文书链**校验**（表单字段／数字判据／受控登记） | ✅ 可用 |
| `eda_eng docs` | 文档链（ECO-方案-图-记录**五环**）状态 | ✅ 可用 |
| `eda_eng verify` | **判卷**：C1 连通 · C2 DRC 零新增 · C3 等长 · C4 倒角保留 · C5 走线真变 | ✅ 可用 |
| `eda_eng exam A\|B` | 两道考题的**回归定义**（可 `--board/--drc` 直接判卷） | ✅ 定义＋判卷可用；**执行**待引擎 |
| `eda_eng place` | 放置（**声明式**：读放置源＋施加场景位移，**不碰板**） | ✅ 可用（v1） |
| `eda_eng route` | **rip-up & reroute 引擎** | ❌ **未实现**（如实报 `NOT_IMPLEMENTED`／退出码 2） |
| `eda_eng selftest` | 回归测试套件（**CI 入口**） | ✅ 可用 |

## 用法

```sh
k2/tools/eda_eng.sh eco
k2/tools/eda_eng.sh docs
k2/tools/eda_eng.sh verify --board <pcb> --drc <drc.json>
k2/tools/eda_eng.sh exam A
k2/tools/eda_eng.sh place --refs U1,U2,U4,U5 --delta 5,0
k2/tools/eda_eng.sh route --exam B --work /tmp/opencode/eda_eng/examB
k2/tools/eda_eng.sh exam B --run        # 建 + 判卷（CI 口径）
k2/tools/eda_eng.sh selftest
```

- 读板几何用 KiCad 自带 python（`EDA_ENG_PY=/path/to/kicad/python3.11`）＋ `kicad-cli`；两者缺失时相关判据报 **SKIPPED**（**永不当 PASS**）。
- **CI 口径**（#K2-358 §五）：`eda_eng selftest` 全绿 ＋ `eda_eng eco/docs/verify/exam` 独立跑通 ⇒ **LLM 不在被调用链上**。

## 目录

```
tools/eda_eng/{__init__,cli,verify,exams,eco,docs,place,route}.py
tools/eda_eng/tests/test_eda_eng.py
tools/eda_eng.sh                 # 入口包装（设 PYTHONPATH）
```
