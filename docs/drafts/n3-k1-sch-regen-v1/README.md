# N-3 · K1 原理图侧再生（37→42）**可执行性判定 + 验收核**（草案 · 只读）

- 依据：handoff §8.2① / **#K2-47** / `PENDING_RULINGS_DELTA_20260921_v4`（N-3 rev）
- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/N3_K1_SCH_REGEN_EXECUTABILITY_20260921_v1.json`（sha16 `b702cc59c361d857`）
- 性质：**只读**。未写 `k1/`；未新增判据维；未改冻结源/交付锚。

## 0. 一句话
N-3 的**大部分是机械的**（网表由 `k1_nets.yaml` 重建、4 处 footprint 修正有出处），**但 `Q1`(TPS22990) 缺 2 脚定义、且仓库无其 pinout** ⇒ **N-3 当前不能在不杜撰脚位的前提下完成**。已交**验收核脚本**，对现行件实跑即 **FAIL** 并**当场暴露先前遗漏的 `J10`**。

## 1. 机械可得（无需判断）
| 面 | 结论 |
|---|---|
| `nets` | 由 `k1_nets.yaml#nets`（51 网）**机械重建**（②机械派生权威网表） |
| `placements` | 5 件可由 `k1_board.yaml#devices` + `k1_pinmap.yaml` 派生 |
| symbol 修正 | J1(K1-S1) · U10(K1-S2) · U12(K1-S4) · **J10(K1-S6·本会话新登)** ⇒ footprint 取 `k1_board.yaml` |

## 2. 逐件数据可得性
| 件 | 声明脚数 | pinmap 有网脚 | 缺口 | 判定 |
|---|---|---|---|---|
| `Q1` TPS22990 | 6 | 4 | **2 脚无出处**（仓库无 pinout） | ⛔ **N3-G1 BLOCKING** |
| `U12` TPS22965 | 6 | 4 | 2 脚（同上；现用错件 TPS22919） | ⛔ **N3-G2 高** |
| `U13` TPD2E001 | 6 | 4 | 2 脚 = **N.C.**，**手册 `pinout_6pin` 已具名** | ✅ 非阻塞 |
| `Q2` 2N7002 | 3 | 3 | 0 | ✅ |
| `R38`/`R39` 22R | 2 | 2 | 0 | ✅ |

**缺口处置（请监理择一，监理自裁·无 owner 闸口）**：
(i) 取手册（TI SLVSDK1C / SLVSBJ0F）转录 pinout + 三件套 ← ENG 建议
(ii) 监理/owner 裁定按其 4 有网脚 + 2 NC 具名落件
(iii) 部分再生（先落其余 4 件）**须监理同意**

## 3. 验收核（机判 · 本包附件）
`k1_sch_regen_acceptance_v1.py` —— 5 项检查：
`A` refdes 集合 == 板 42 · `B` symbol 已定义 · `C` footprint basename == `k1_board.yaml` · `D` nets 成员集 == `k1_nets.yaml` · `E` 渲染组件数 == 42

```bash
PYTHONPATH=_shared python3 k2/docs/drafts/n3-k1-sch-regen-v1/k1_sch_regen_acceptance_v1.py \
  --sch-yaml k1/boards/k1_sch.yaml --render        # 现行件 ⇒ FAIL(rc=1)
```
**现行件实跑（负控）**：`A` 37≠42（缺 Q1/Q2/R38/R39/U13）· `C` **4 处**不符（J1 · **J10** · U10 · U12）· `D` 13 网不一致 · `E` 渲染 37 ⇒ **FAIL**。

> ⭐ 该核**当场暴露先前遗漏**：`J10` 的 symbol（`HEADER_2PIN_12V`）footprint 仍 `ForgeOS:PinHeader_1x02`，板侧真值 = `Connector_JST:JST_VH_B2P-VH_1x02_P3.96mm_Vertical`。已具名更正为 **K1-S6**（诚实登记，不影响既有结论）。

## 4. 渲染可行性（已实测）
共享 `schlib` + `k2/tools/k2_sch_gen_v1.py`（env `K2_SCH_YAML`）**可驱动 K1**：4 页 rc=0 · 逐字节确定性 · 仅 `/tmp`。

## 5. 边界
只读；未动 `k1/`；未新增判据维/检查齿（本验收核为**该次授权变更**的验收工具，非门禁新维）。
