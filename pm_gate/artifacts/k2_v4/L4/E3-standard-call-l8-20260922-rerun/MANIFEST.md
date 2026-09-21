# E3 标准调用复跑 · l8 · 2026-09-22（K2 R259）

**目的**：独立复跑 `criteria/adjudicate.py`（rev=6 · countersigned）确认 l8 判定器结论，
并**分列**两种网表输入之差异（`k2_sch.yaml` 冻结原件 vs `k2_sch.errata-3.yaml` 监理授权真源）。

## 受审对象
- 板：`k2/hw/k2_v4_8L.l8.kicad_pcb` · **sha16 `7a5c89913d6e5d0a`**（未动）
- 判定器：`criteria/adjudicate.py`（rev=6 · countersigned=True · ENG 只读执行）
- 运行时刻（真实时钟）：2026-09-22T01:13+0800 · **全新 `--drc-work-dir`** /tmp/opencode/rev9/adj_drc
- DRC：`AppDir/bin/kicad-cli 10.0.5 pcb drc --severity-all --format json` ⇒ error=0 / 违规总 170 / unconnected=0

## 网表输入分列（**本件唯二自变量**）
| 输入 | sha16 | 结果 |
|---|---|---|
| `hw/data/k2_sch.yaml`（**冻结原件** · 逐字节未动） | `dd794c54f7ce7417` | **17 OK / 2 FAIL** ⇒ `verdict_19dim_rev6_frozen_netlist_board_l8_7a5c8991.json` |
| `hw/data/k2_sch.errata-3.yaml`（**#K2-24 + #K2-57 授权真源链**） | `5dc7b82a901d11c8` | **19 OK / 0 FAIL** ⇒ `verdict_19dim_rev6_errata3_netlist_board_l8_7a5c8991.json` |

冻结网表之 2 FAIL（**逐条**）：
- `net_declared_realized`：`LED_A`（声明 2 / 实际 1）· `PWR_5V_KEY`（声明 1 / 实际 0）
- `pin_map_complete`：2 个网表节点无对应焊盘 = `(GND, C89/B@2)` · `(PWR_5V_KEY, C89/A@1)`

⇒ 2 FAIL **恰为**已授权 errata 项：`C89/PWR_5V_KEY` 删减（owner ⑤ 裁定 + 监理 #K2-24）与
`LED`/`BAT54C_ORING` pin 号订正（监理 #K2-57 CR-26/CR-27）。⇒ **非缺陷、系冻结原件未随 errata 提升**。

## 件
- `measure_raw_board_l8_7a5c8991_frozen_netlist.json`（冻结网表之原始测量 · 2.2 MB）
- `verdict_19dim_rev6_frozen_netlist_board_l8_7a5c8991.json`（17/19 PASS=False）
- `verdict_19dim_rev6_errata3_netlist_board_l8_7a5c8991.json`（19/19 PASS=True · 与在册
  `L4/E3-standard-call-l8-20260921/verdict_19dim_rev6_board_l8_7a5c8991.json` 之 OK 集逐项同）

## 保真
ENG 本次**只读**执行；未改冻结四源/判据/生成器/SPEC/原理图；未重建或覆盖 l4..l8 任何旧包。
