# K2 · **P4 施工状态（增量 1）** v1 —— 交监理核

> **依据**：监理 **#K2-18 §五（U3 = P4 开工令）** + **§九-3（P4 施工）**；输入清单 `K2-P4-INPUT-PREREQUISITES-v1.md` v4（IN-1..IN-11）。
> **性质**：施工执行报告（ENG「交测量」，判定权归监理）。**P4 未完工**；本件 = 增量 1。
> **冻件**：`k2/hw/k2_v4_8L.l4.kicad_pcb`（`d4e81f647be7f980`）**未动**；`criteria/` 两份只读未动。

## 1. 本轮落地（增量 1）

| IN | 动作 | 实测结果 |
|---|---|---|
| **IN-4** | `U1` land pattern 补齐 | pad **33 → 58**（带号 `1..49` = LQFP48 + EP；另 9 个无名 paste-only 开窗）；`EP(49) → GND`；原 33 网按 pad 号迁移 |
| **IN-11** | 5 件接口件 pad 补齐 | `J6/J12`（1x02）+ `J9/J11/J13`（1x04）= **16 pad**（板原 **0**）；`device_has_pads` 已 PASS |
| **IN-8** | 排针列守值 | 5 件 `x: 26.5 → 27.94`（P3-4 余量 0.08 口径） |
| **IN-6** | 固定孔施工 | **4×Ø3.2 NPTH**（H1..H4，L2-2 坐标）+ **Ø6.0 keepout**（8 铜层 rule area，禁 zone_fill/via/track/pad） |
| **IN-7** | `ESC_*` 开关 | 4 个无网 `F.Cu` rule area：`zone_fills = disallow` ⇒ 每区 ≥1 非 allowed（**C5b 达成**） |
| **IN-3** | 9 铜区填充 | **9/9 铜区 `filled_polygon ≥ 1`**（C7 达成；`In1/In3/In6 = GND` + `In4×6`） |

- **件**：`k2/hw/k2_v4_8L.l5.kicad_pcb` = **`13cf989059c414ed`**（新 revision；`k2_v4_8L.l5.kicad_pro` 同批）+ 机读台账 `pm_gate/artifacts/k2_v4/L4/p4_construction_increment1.json` + 执行器 `k2/tools/k2_p4_build_l5_v1.py`。
- **复跑确定性**：**两次连跑 sha 相同**（`13cf989059c414ed`，逐字节一致）；本版绑定无 UUID setter ⇒ 执行器内置三步写盘后规范化（footprint 按 ref 排序 / 新增 keepout zone 按名排序 / 新增件 UUID 确定性派生）。

## 2. 冻结仪器实测（`criteria/adjudicate.py` `897e8bfde60e2cfe`，l5，带 `--nets/--sch-dir/--pro`）

```
--board k2/hw/k2_v4_8L.l5.kicad_pcb --manifest criteria/manifest.k2.yaml
--nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro
```

| 判据 | 结果 | 说明 |
|---|---|---|
| `device_has_pads` | **PASS** | `0 焊盘器件 = []`（IN-4/IN-11） |
| `drill_count` | **PASS** | `NPTH = 4`、`PTH = 16`（IN-6/IN-11） |
| `verdict_schema` | **PASS** | 产物无 `verdict` 字段 |
| `zone_filled` | FAIL `9/17` | **口径问题 ⇒ U4-A**（见 §3） |
| `non45_segments` | FAIL `2051/2512` | 登记册 **J-5** 已录现值 2051 ⇒ 待 45° 归一（下一增量） |
| `rule_severity_manifest` | FAIL `9/62` ignore 未登记豁免 | 登记册 **J-1/J-4**（DRC/丝印全开）⇒ 需豁免裁定或整改 |
| `net_declared_realized` | FAIL（0 焊盘网 10 / <2 焊盘网 17） | 随 **IN-5**（13 件落板 + 赋网）收敛 |
| `pin_map_complete` | FAIL（无对应焊盘 26） | 同上（IN-5） |
| `refdes_sets_equal` | FAIL（图 55 / 板 46） | 图有板无 13 = **IN-5**；板有图无 4 = **H1..H4 固定孔** ⇒ **U4-C**（见 §4） |
| `pipeline_present` | FAIL | **J-9** ⇒ 需出 `pipeline.yaml`（下一增量） |

## 3. **U4-A 实证（供 owner 批判据修正）**

- 现判据 `filled_zones == total_zones` ⇒ l5 实测 **`9/17`**（17 = 9 铜区 + **4 个无网 `ESC_*` keepout** + **4 个新增 Ø6.0 固定孔 keepout**）⇒ **结构上永久 FAIL**（keepout 不可能有 `filled_polygon`）。
- 按 **#K2-18 §六-3 待批补丁**口径（仅计**有网且非 keepout** 的铜区）⇒ **`9/9` PASS**。
- ⇒ 本件为 U4-A 提供**双口径实测证据**；`criteria/` 由 ENG **只读**，修正仍须 owner 批 + `ic_hw_gate` 属主落件。

## 4. **U4-C（新发现，请监理裁）：`refdes_sets_equal` 与「必需 NPTH 固定孔」冲突**

- **事实**：IN-6 要求板侧 4×Ø3.2 NPTH（P3-2 判据），落地后板侧 refdes 多出 `H1..H4`；而原理图 refdes 集 = 55（无 `H*`）⇒ `板有图无 4` ⇒ 判据**不可达**。
- **性质**：**判据口径**问题（非板缺陷）—— NPTH 机械孔按行业惯例**不进原理图**。
- **请裁**（二选一）：① 判据口径澄清：`refdes_sets_equal` 排除**非电气/机械件**（如 `attr board_only` 或 refdes 前缀 `H*`，须显式列名口径）；② 或要求原理图侧补 `H1..H4`（属源侧变更，须另批）。
- 现有 `device_has_pads`（每件 ≥1 pad）与 NPTH 不冲突（已 PASS）。

## 5. 下一增量（**未落地**，按序）

1. **IN-5**：13 件补件落板 + `C73/C86` 移位（消费 `p3_placement_solution.json` `15/15`）+ **按 errata 网表赋网** + 布线 ⇒ 收敛 `net_declared_realized` / `pin_map_complete` / `refdes_sets_equal`(13)；
2. **J-5**：`non45_segments 2051 → 0`（走线 45° 归一）；
3. **J-1/J-4**：DRC / 丝印 severity 全开 + 9 条 ignore 逐项裁定或整改；
4. **J-9**：`pipeline.yaml`（门禁接入）；
5. **U4-A**（owner 批后）复算 `zone_filled = 9/9`；**U4-C** 裁定后复算 `refdes_sets_equal`；
6. Gerber 出图前置：**平面层 `G36 > 0`**。

## 6. 复跑 / 边界

```bash
cd /home/fila/jqdDev_2025/ic_hw
# 施工（确定性；输出默认 /tmp/opencode/p4）
K2_P4_OUT=<dst>.kicad_pcb K2_P4_LEDGER=<dst>.json AppDir/usr/bin/python3.11 k2/tools/k2_p4_build_l5_v1.py
# 判定（监理权）
python3 criteria/adjudicate.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --manifest criteria/manifest.k2.yaml \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --measure-out /tmp/opencode/p4/meas.json --out /tmp/opencode/p4/verdict.json
```
- **边界**：未改冻结件（`d4e81f64`/`fb07d25a`/`dd794c54`/SPEC `rev-19..24` 原件/`criteria/` 两份）· 未派 WORKER · 临时仅 `/tmp/opencode` · **P4 未完工**（不得据本件宣称 P4 绿）。
