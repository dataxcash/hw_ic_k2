# `eda_eng` —— K2 独立确定性 EDA 工程软件（#K2-358）

> **产品定义**：本软件**无 LLM 在场可完整运行**。板面变更的**唯一入口** = 本软件的命令。
> **ARCHER 岗位** = 开发本软件（写代码／跑测试／修失败）；**禁止再亲手编辑 `.kicad_pcb`**（文本级手术全数封存 · 承 #K2-347/356/358）。

## 命令

按 **#K2-360** 四模块分治（**M1→M2→M3→M4 逐个交付 · 模块绿一个收一个**）：

| 模块 | 命令 | 输入 → 输出 | 状态 |
|---|---|---|---|
| **M1** | `eda_eng netplan` | 板＋放置增量 → **受影响网清单＋待拆段/孔清单** | ✅ **绿**（收执 `EDA_ENG_M1_NETPLAN_RECEIPT_v1.json`） |
| **M2** | `eda_eng ripup` | M1 清单 → 拆后板 | ✅ **绿**（收执 `EDA_ENG_M2_RIPUP_RECEIPT_v1.json`） |
| **M3** | `eda_eng route` | 拆后板＋约束 → 布通板（多 pad 网 MST ＋ via/多层 ＋ **迷宫布线**） | ✅ **绿 v2**（收执 `EDA_ENG_M3_ROUTE_RECEIPT_v1.json`／`EDA_ENG_M3V2_SCOPE_EXPANSION_RECEIPT_v1.json`） |
| **M4** | `eda_eng verify` | 布通板 → 判卷报告（**C1–C5** · 判卷表＝ECO §6 唯一源） | ✅ **绿**（收执 `EDA_ENG_M4_VERIFY_RECEIPT_v1.json`） |

其余命令：

| 命令 | 作用 | 状态 |
|---|---|---|
| **`eda_eng relocate`** | **器件重定位六步一条命令**（#K2-366）：1 挪 pad → 2 M1 → 3 M2 → 4 迷宫重连 → 5 复敷铜 → 6 M4 判卷 | ✅ 可用（`EDA_ENG_RELOCATE_DEMO_v1.json`） |
| `eda_eng eco` | ECO 文书链**校验**（表单字段／数字判据／受控登记） | ✅ 可用 |
| `eda_eng docs` | 文档链（ECO-方案-图-记录**五环**）状态 | ✅ 可用 |
| `eda_eng verify` | **判卷**：C1 连通 · C2 DRC 零新增 · C3 等长 · C4 倒角保留 · C5 走线真变 | ✅ 可用 |
| `eda_eng exam A\|B` | 两道考题的**回归定义**（可 `--board/--drc` 直接判卷） | ✅ 定义＋判卷可用；**执行**待引擎 |
| `eda_eng place` | 放置（**声明式**：读放置源＋施加场景位移，**不碰板**） | ✅ 可用（v1） |
| `eda_eng route` | **rip-up & reroute**（`--apply-batch` 落板 ＋ 迷宫重连） | ✅ 可用（v2） |
| `eda_eng regen` | 既有组合管线（**legacy** · 仅作 `exam --chain legacy` 对照） | ⚠️ legacy |
| `eda_eng selftest` | 回归测试套件（**CI 入口**） | ✅ 可用（**51/51 PASS**） |

## 用法

```sh
k2/tools/eda_eng.sh eco
k2/tools/eda_eng.sh docs
k2/tools/eda_eng.sh verify --board <pcb> --drc <drc.json>
k2/tools/eda_eng.sh exam A
k2/tools/eda_eng.sh place --refs U1,U2,U4,U5 --delta 5,0
k2/tools/eda_eng.sh netplan --board hw/k2_v4_8L.l14.kicad_pcb --refs U1 --delta 5,0
k2/tools/eda_eng.sh relocate --refs L1 --delta 0.5,0 --work /tmp/... --max-nets 1   # 六步一条命令
k2/tools/eda_eng.sh regen --exam B --work <W> --dry-run
k2/tools/eda_eng.sh exam B --run        # 建 + 判卷（CI 口径）
k2/tools/eda_eng.sh selftest
```

- 读板几何用 KiCad 自带 python（`EDA_ENG_PY=/path/to/kicad/python3.11`）＋ `kicad-cli`；两者缺失时相关判据报 **SKIPPED**（**永不当 PASS**）。
- **CI 口径**（#K2-358 §五）：`eda_eng selftest` 全绿 ＋ `eda_eng eco/docs/verify/exam` 独立跑通 ⇒ **LLM 不在被调用链上**。
- **闸纪律**（R964／C25）：闸**绝不许经 `tee` 管道**放进 `&&` 链（退出码会被掩蔽）⇒ 直接捕获退出码再判。

## 目录

```
tools/eda_eng/{__init__,cli,verify,exams,eco,docs,place,route,regen,netplan,ripup,shadow}.py
tools/eda_eng/tests/test_eda_eng.py
tools/eda_eng.sh                 # 入口包装（设 PYTHONPATH）
```
