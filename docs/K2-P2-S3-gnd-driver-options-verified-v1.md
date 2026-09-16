# S3（GND 无驱动）两方案**均已沙箱验证** + 推荐修订 v1

- **对象**：全图**唯一 ERC error** —— `[power_pin_not_driven] ; error @ U6 引脚 AC4`（真源 GND 网内 U6 的 **152 个 `power_in` 地脚**，而 GND 网 211 节点中**无 `power_out`**）。
- **性质**：沙箱证据，**未安装**（仓内 `hw/sch`、`hw/lib`、真源 `k2_sch.yaml`、生成器**均未改**）。
- **本件目的**：把 S3 的**两个候选方案都跑到判据可验**，消除"建议无实证"，并**修订 ENG 先前推荐**。

## 1. 两方案实测结果（同一 U2 沙箱工具链，全 5 sheet + root）

| | **(a) driver 加 `PWR_FLAG`**（保留真源引脚类型） | **(b) 真源引脚类型 `power_in → passive`**（152 脚） |
|---|---|---|
| ERC error | ✅ **0**（该 error 消失） | ✅ **0**（该 error 消失） |
| ERC 其它项 | 与基线同 profile（452 off-grid / 55 lib / 15 footprint）**+1 新增 warning** `lib_symbol_mismatch`（内嵌 `power:PWR_FLAG` 定义与系统 `power` 库同名符号有差异——内嵌式定义的固有代价，非电路问题） | 与基线**完全同 profile**（无新增） |
| 网表连通性 | ✅ 与基线**完全等价**（205 网名集合相同，**节点集差异 = 0**） | ✅ 与基线**完全等价**（同上） |
| 确定性 C1 | ✅ 两次连跑逐字节同 | ✅ 两次连跑逐字节同 |
| 改动面 | 生成器 **+1 显式规则（P9，约 5 行）** + 每工程 1 个旗标图形；**真源不动** | **真源 `k2_sch.yaml` 152 处引脚类型**；生成器不动 |
| 语义代价 | 无（引脚类型仍忠实于器件手册；GND 由**载板/线束**驱动 = 与真实拓扑一致） | **弱化** `power_in` 语义（把"必须被驱动"的检查点降级）⇒ 有**"改数据让检查变绿"**的读法，与本整改"不得以删差异达成归零/不得硬编绕过"纪律**同型** |

## 2. 推荐修订：**改为推荐 (a)**

- **先前 ENG 推荐 (b)（改真源引脚类型）是基于"不动策略"的便利性判断；实测后修订为 (a)**，理由：
  1. **(a) 属 KiCad 常规做法**：`PWR_FLAG` 的语义正是"该网由板外驱动"——K2 的 GND 确实来自载板/线束，与真实拓扑一致；
  2. **(b) 有掩蔽读法**：把 152 个 `power_in` 降为 `passive` 是**降低检查强度**，正是本整改反复禁止的形态；若采 (b) 建议同时在 P4 板侧缺陷清单**独立登记**该语义弱化（防掩）；
  3. **(a) 的唯一代价**是 1 条 `lib_symbol_mismatch` **warning**（内嵌 `power:PWR_FLAG` 与系统库同名件有差异）——属**表现层**，且是"不依赖系统库"这一既有设计取向的必然结果；如监理要求零新增 warning，可另立"旗标定义对齐系统库"小项。
- **(a) 的实现细节建议**：不要硬编 `GND`，应实现为**通用规则**——"凡有 `power_in` 脚且无 `power_out` 脚的网，各加 1 个旗标（放在该网首个标签锚点）"。当前沙箱只需命中 GND（唯一命中网）。该规则按可行性论证 §5 要求**先报监理备案**。

## 3. 证据与复现（只写 `/tmp`）

| 项 | 值 |
|---|---|
| (a) 沙箱 driver | `/tmp/opencode/k2p1/k2_sch_gen_v1.s3a.draft.py` `97c7ac2174e7fd11`（230 行；= U2 driver `9aa52762444851b8` + 5 行 P9） |
| (a) 产物 / ERC | `/tmp/opencode/s3a_a/` · `/tmp/opencode/erc_s3a.rpt`（error 0；+1 `lib_symbol_mismatch` warning） |
| (b) 沙箱真源 | `/tmp/opencode/k2p1/k2_sch.s3b.draft.yaml`（U6 的 152 个 `POWER_IN→PASSIVE`；YAML 往返生成） |
| (b) 产物 / ERC | `/tmp/opencode/s3b_a/` · `/tmp/opencode/erc_s3b.rpt`（error 0，profile 与基线全同） |
| 基线对照 | `/tmp/opencode/full_a/`（error 1 = 本项） |

```bash
cd /home/fila/jqdDev_2025/ic_hw
K2_PAPER_OVERRIDE="ReDriver DS320PR1601 & Sideband Strap=A0" K2_OUT_SCH=/tmp/opencode/s3a_a AppDir/usr/bin/python3.11 /tmp/opencode/k2p1/k2_sch_gen_v1.s3a.draft.py
K2_PAPER_OVERRIDE="ReDriver DS320PR1601 & Sideband Strap=A0" K2_SCH_YAML=/tmp/opencode/k2p1/k2_sch.s3b.draft.yaml K2_OUT_SCH=/tmp/opencode/s3b_a AppDir/usr/bin/python3.11 /tmp/opencode/k2p1/k2_sch_gen_v1.draft.py
AppDir/bin/kicad-cli sch erc --severity-all -o /tmp/opencode/erc_s3a.rpt /tmp/opencode/s3a_a/k2_sch.kicad_sch
```

- 冻结件（本件未动）：交付板 `d4e81f647be7f980`、设计源板 `fb07d25ac426ff84`；U2 driver 原件 `9aa52762444851b8`（未变，S3(a) 用**独立副本**，不影响既有证据 sha）。
