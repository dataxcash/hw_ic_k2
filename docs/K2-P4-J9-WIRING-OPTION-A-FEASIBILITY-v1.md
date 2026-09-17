# K2 · P4 · J-9 / M-13「门禁接线」出路 (A) 可行性证明（ENG → 监理一句话裁）· v1 · 2026-09-17

## 0. 目的与边界

- **目的**：把 `pipeline_present`（J-9 / M-13）的裁定成本降到**一句话** —— 证明 **出路 (A)**（真源补 `nc` 白名单 + 出 BOM）**充分且可行**：装齐后三项必选 sch checks 全 PASS、`k2/pipeline.yaml` 可安全接线、**不会堵死 k2 的 P4 提交**。
- **边界（本件未改任何件）**：`k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`）**逐字节未变**；`k2_sch.yaml`（`dd794c54f7ce7417`）**未变**；**未创建** `k2/pipeline.yaml`；**未入库** BOM。证明在 `/tmp`，草案落 `k2/docs/drafts/j9-wiring-option-a/`。
- **依据**：计划 IN#6（门禁接线与 fail-closed，落点 P1+P4）+ 登记册 **M-13**（k2 无 `pipeline.yaml` ⇒ 引擎对 K2 从未运行）/ **J-9**（`pipeline.yaml` 存在且 ④段判据全机判）+ 监理 **#K2-19 §二 W-9**（k2 门 = k2-scoped）。

## 1. 阻断事实（先把「不能只加文件」钉死）

`_shared/eda_core/pipeline/required.py`：`REQUIRED_SCH_CHECKS = ("sch_structural","netlist_connect","bom_consistent")`；
`_shared/eda_core/pipeline/hooks/pre-commit`：任何触及 k2 的提交跑 `engine.py verify <k2>`，**`verify:` 声明的 check 必须真能过**。

| check | 装 (A) 之前（现状实测） | 装 (A) 之后（实测） |
|---|---|---|
| `sch_structural` | **PASS**（0 warnings） | PASS |
| `netlist_connect` | **FAIL · 106 处** | **PASS**（「全部 100 个网连接完整 + 反向断言 0 非声明悬空」） |
| `bom_consistent` | **不可跑**（k2 无任何 BOM csv） | **PASS**（「BOM 与 sch 同步（55 器件）」） |
| meta-gate（必选声明） | k2 未被发现（无 pipeline.yaml） | **PASS**（「k2: 已声明必选 sch checks」） |

**106 处 FAIL 的两个成分**：
1. **反向断言**（KiCad `unconnected-*` 网节点须 ⊆ YAML `nc` 白名单）：k2 netlist 有 **105 个 `unconnected-*` 网（105 引脚）**，而真源 `nc` = **0 条** ⇒ 105 处「非声明悬空」。
2. **正向断言**：真源申报的网 `PWR_5V_KEY` 在 KiCad netlist 中**不存在**（1 处）。

## 2. 关键事实：105 个 NC 引脚在**原理图里已标记** `no_connect`

逐条提取（`load_netlist` 元组第 4 项）：105 个引脚 `ptype` **全部**为 `passive+no_connect` / `input+no_connect` / `bidirectional+no_connect` ⇒ **sch 侧已是 NC**；缺的**只是真源 `nc` 白名单**。分布：

| 件 | 条数 | 例 |
|---|---|---|
| `U6`（DS320PR1601） | **93** | `ALL_DONE#` · `A_PERN8` · `RSVD1..14` … |
| `J3` / `J4`（MCIO x4） | 各 **4** | `CBL_PRES#` · `FLEXIO_0A` · `SMB_CLK` · `SMB_DATA` |
| `J2`（SlimSAS x8） | **2** | `SMB_CLK_B` · `SMB_DATA_B` |
| `C89` | **1** | `A`（= pad1） |
| `U4`（BAT54C） | **1** | `A1` |

**`PWR_5V_KEY` 的性质**：真源声明 `PWR_5V_KEY: [C89/A]` = **声明在 NC 引脚上的单节点网**（= 计划 OUT#6 所记 **F-10「`NO_CONNECT` 自造网的历史痕迹」**）⇒ KiCad netlist 中自然不存在。**处置 = 该网从 `nets` 撤下、其节点并入 `nc`**（不建真实网）。
> 与 #K2-19 §二「注记」一致：该网此前仅作**口径注记**（判定器按 `nets_with_zero == 0` 判 PASS）；接线后须**实证**处置，不再是注记。

## 3. 出路 (A) 的补丁（**草案**，交监理批后走版本 bump）

| 项 | 内容 |
|---|---|
| **真源 bump** | `k2_sch.errata-2.yaml`（**新文件**；`errata-1` 原件不动）= errata-1 **+** `nc`（**105 条**）**−** `nets.PWR_5V_KEY` |
| **差异审计（逐项）** | `symbols` / `sheets` / `strap_intents` / `links` **逐项相同**；`nets` 除移除 `PWR_5V_KEY` 外**逐项相同**（101 → 100）；`nc` 0 → 105 |
| **BOM** | 由 sch 导出（`kicad-cli sch export bom`，`Reference,Value,Footprint,QUANTITY`，55 器件）；建议落 `k2/fab/k2_v4_bom.csv` |
| **接线件** | `k2/pipeline.yaml`（草案见 §4） |

**`nc` 条目口径**：`[refdes, pin_name]`（与 key_v2 参照件同形，如 `['U6','RSVD1']`）；`pin_name` = netlist `fn` 去掉尾部 `_{pin号}`（如 `SMB_CLK_B_63` → `SMB_CLK_B`）。

## 4. `k2/pipeline.yaml` 草案与端到端 verify 模拟（实测 3/3 PASS）

```yaml
project: k2
phases:
  - id: preflight
    checks:
      - {type: project_sch_coverage}
  - id: verify
    verify:
      - {type: sch_structural,  sch: k2/hw/sch/k2_sch.kicad_sch}
      - {type: netlist_connect, sch: k2/hw/sch/k2_sch.kicad_sch, nets_yaml: k2/hw/data/k2_sch.errata-2.yaml}
      - {type: bom_consistent,  sch: k2/hw/sch/k2_sch.kicad_sch, bom_csv: k2/fab/k2_v4_bom.csv}
```
（`process_gate` **未启用** —— `k2/process/` 尚未 bootstrap；是否启用须监理另裁。）

**模拟 `engine.py verify`（按引擎同路径调用 `CHECK_TYPES`，草案件在 /tmp / 仓库草案目录）**：
```
meta-gate: True  k2: 已声明必选 sch checks
  verify/sch_structural: PASS
  verify/netlist_connect: PASS
  verify/bom_consistent: PASS
verify 完成: 3 项, FAIL=0
```

## 5. 判据质量注记（新发现，供 §3.5「判据自己也要被验收」）

`check_netlist_connect` 的匹配用 `fn.startswith(pin_name)` ⇒ **同件引脚名互为前缀时会遮蔽**。本板实测 **5 对**：`U6` 的 `RSVD1` ⊂ `RSVD10`/`RSVD11`/`RSVD12`/`RSVD13`/`RSVD14`。
⇒ 若 `nc` 只写 `RSVD1`，则该声明**同时**放行 `RSVD10..14` 的悬空（把 5 个未声明引脚一并吞掉）。**建议**：匹配改**精确等值**（或 `nc` 一律写 netlist 全名 `fn`）。本草案已按「去尾 `_{pin}` 的**完整**引脚名」书写，故全 105 条**逐条唯一**；但判据侧的前缀语义本身仍属弱点，一并报上。

## 6. 复跑命令（确定性）

```bash
cd /home/fila/jqdDev_2025/ic_hw
export SHARED_HOOK="$PWD/_shared"; export PYTHONPATH="$PWD/_shared:$PWD"
python3 - <<'PY'
import sys, yaml
from pathlib import Path
from eda_core.pipeline import checks, required
cfg = yaml.safe_load(open('k2/docs/drafts/j9-wiring-option-a/pipeline.k2.draft.yaml'))
cfg['_root'] = Path('k2'); cfg['project'] = 'k2'
print(required.check_project_sch_coverage(cfg))
ov = {'netlist_connect': {'nets_yaml': 'k2/docs/drafts/j9-wiring-option-a/k2_sch.errata-2.draft.yaml'},
      'bom_consistent':  {'bom_csv':   'k2/docs/drafts/j9-wiring-option-a/k2_v4_bom.draft.csv'}}
for ph in cfg['phases']:
    for s in ph.get('verify', []):
        s = dict(s); s.update(ov.get(s['type'], {}))
        print(s['type'], checks.CHECK_TYPES[s['type']](cfg, s))
PY
```

## 7. 三条出路（重申，请监理择一）

| | 出路 | 性质 | 本件状态 |
|---|---|---|---|
| **(A)** | 真源 bump 补 `nc` 白名单(105) + 处置 `PWR_5V_KEY` + 出 BOM ⇒ 接线 | **触及真源 ⇒ 版本 bump 须批** | **本件已证充分可行（3/3 PASS）** |
| **(B)** | 监理收窄 k2 必选 sch checks（如 k2 不适用 `netlist_connect` 反向断言 / `bom_consistent`） | **判据语义/范围**（#K2-19 §一 二分 ⇒ 监理自有权） | 交监理 |
| **(C)** | 分阶段接线：P4 只声明 `sch_structural`（已 PASS），其余挂 P5 | 阶段判据口径 | 交监理 |

**ENG 建议**：采 **(A)** —— 它同时消掉一个真缺陷（F-10 单节点自造网 + 105 个未声明 NC 引脚），且**已被证明**不会堵死 k2 提交；`nc` 白名单与 BOM 都是 P4/P5 交付包本来就该有的产物。
**在监理择定前，ENG 不创建 `k2/pipeline.yaml`**（把必选 check 放进引擎不执行的 `checks:` 字段可让 meta-gate 表面通过，但那是空声明，本件拒绝）。

—— ENG（ARCHER）· 2026-09-17
