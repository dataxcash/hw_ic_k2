# K2 · **N-3 落件报告** —— K1 原理图侧**同源对账再生**（37→42）

- 授权：**监理 #K2-48 §一 N-3**「K1 同源对账 + 原理图侧再生（37→42 + J1/U10 footprint）＝授权；
  经单一真源再生；不新增判据维；K1 项目面」；前置 = **#K2-49 §二/§三**（M1/M2 放行 · M3 前置 BOM，
  已由前序会话落件 `c018fc7`/`4084133`/`01f4d72`）。
- 单一真源：`k1/boards/k1_board.yaml` + `k1/boards/k1_pinmap.yaml` + `k1/boards/k1_nets.yaml`
  （旧 `k1_sch.yaml` 仅作**既有符号体 + 页定义**来源）。
- **0 新判据维 / 0 新检查齿**；`criteria/`、`_shared/`、`k2/` **零改动**；交付锚 `MANIFEST 6ee7495d…` **未动**。
- 机读件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/N3_K1_SCH_REGEN_LANDING_REPORT_20260921_v1.json`
  （sha16 `a3282757d33b5092`）· 提交 `k1 9e283bf`（已推）。

## 一、落件（一笔提交 `k1 9e283bf`）

| 件 | 前 sha16 | 后 sha16 | 变更 |
|---|---|---|---|
| `k1/boards/k1_sch.yaml` | `67c2771d6ed0b81e` | `e1fdb1a1f0f6df93` | placements **37→42** · nets **46→51** · symbols 40→28（在用集） |
| `k1/boards/k1_board.yaml` | `313dfcf6477b8a07` | `1420ca9da99ac7ba` | `sch_pins` 声明 4 处订正（§三） |
| `k1/fab/k1_v1_bom.csv` | `2b7b2554f835689e` | `2ba7c2ecf5a53a7a` | refs **37→42**（真 sch netlist 机械派生 + 与真源 placements 交叉核对） |
| `k1/sch/k1_sch.kicad_sch` | `65b04e499065f976` | `4baae622ad859783` | root 指向再生 4 页（元数据沿用 K1 root） |
| `k1/sch/{connectors,mcu_sideband,power_decoupling_redriver_vcc,power_12v_dc_in_dcdc_5v_ldo_3v3}.kicad_sch` | — | `4627c476…`/`2e4d7b32…`/`8814c503…`/`e1e11b9b…` | **再生页**（42 件：3/24/1/14） |
| `k1/sch/K1_SCH.kicad_sym` | — | `263723c7baa4b9b2` | 再生符号库 |
| `k1/sch/v5_*.kicad_sch` ×4 | — | **删** | 旧命名陈旧页（root 不再引用） |

**新增工具（K1 项目面）**：`k1/tools/k1_sch_regen_v1.py`（真源→spec；dry-run 默认 · `--apply --confirm-repo-write` 双闸 ·
备份入 `/tmp/opencode`；`--sync-decl` 行内锚定订正声明）· `k1/tools/k1_sch_gen_v1.py`（薄 driver：importlib
**复用** `k2/tools/k2_sch_gen_v1.py` 作规则提供者 ⇒ 渲染规则**零复制**、K2 **零写入**；`--install` 落件）。

**纠错/新增（全部由真源推出）**
- `J1` footprint → 板真源 `…Amphenol_12401548E4-2A`（**K1-S1**）· `J10` footprint → `Connector_JST:JST_VH_B2P-VH…`（**K1-S6**）
- `U12` 符号 `TPS22919`（错件）→ **`TPS22965`**（**K1-S4**；脚名/脚号取自已 sha256 同版的手册转录件）
- 新增 `Q1=TPS22990`（②补充件）· `Q2=2N7002` · `U13=TPD2E001` · `R38/R39=R_22R`
- `U1` 补 `WORK_EN(pad9)`/`KEY_DET_EN(pad25)` —— 承 **owner 批准 L1-1（#K1-03 · `state_k1.json` ECN-007）**，非新裁决
- `strap_intents`/`links` 清空（旧内容 = **K2 模板残留**，引用 K1 不存在的 `J2/U3`；K1 判定 19 维不消费）

## 二、验证（全 PASS）

| 项 | 命令 | 读数 |
|---|---|---|
| 验收核 A–E | `k1_sch_regen_acceptance_v1.py --sch-yaml k1/boards/k1_sch.yaml --render` | **ok=true · fails=[]**：板 42 == 图 42 · symbol 全定义 · footprint 0 不符 · nets 0 不一致 · **渲染 42 件** |
| 统一入口 | `verify k1` | `preflight` PASS + **`sch_structural` / `netlist_connect` / `bom_consistent` 全 PASS**（netlist：51 网连接完整 + **反向断言 0 非声明悬空**；BOM 42 器件） |
| 提交期 hook | `k1` commit | 全局 sch 完整性 OK(7 文件) · meta-gate 完整 · k1 verify 全 PASS |
| **K1 判定锚** | `criteria/adjudicate.py --project k1 … --manifest probe_manifest.k1.yaml` | **6 OK/13 FAIL → 8 OK/11 FAIL**；翻转 = `refdes_sets_equal`（原理图 37/板 42 → **42/42**）· `net_declared_realized`（0 焊盘声明网 **3→0**）；**0 维回退** |
| 确定性 | driver 连跑两次 | 4 页 + root + symbol lib **逐字节同** |
| 幂等 | `k1_sch_regen_v1.py --check` | rc=0（盘上件已同步） |

> `pin_map_complete` **16→16 未回归**，其 16 节点**全部为 J1**（见 §四 R-1）。

## 三、声明订正（`k1_board.yaml#devices[*].sch_pins`，行内锚定 4 处）

| ref | 前 → 后 | 依据 |
|---|---|---|
| `Q1` | 6 → **4** | 旧值系误抄 TPS22919；符号实值 4（IN/ON/VOUT/GND） |
| `U1` | 31 → **33** | 本批按 L1-1 正式绑定补 2 脚 ⇒ 符号 33 |
| `U12` | 6 → **4** | 旧值系 TPS22919 残留；符号实值 4 |
| `U13` | 6 → **4** | pinmap 声明 4 脚（1/3/4/6）；2/5 = 手册具名 N.C. |

**语义裁定（本件明确登记）**：`sch_pins` = 该器件**符号脚数**（证据：`U8` 6 vs `fp_pads` 8 · `J1` 16 vs 30 ·
`U11` 43 vs 57）⇒ **不采纳**转录件「订正为 10(+EP)/8(+EP)」的物理脚数口径（物理脚数由 `fp_pads` 承载）。

## 四、残留具名登记（含**给监理的自裁项**）

- **R-1（新登 · 拟 K1-S7）**：`pin_map_complete` 的 16 节点 = **全部 J1** —— J1 符号脚号 `1..16` ∉ 板 pad 名
  `A*/B*/SH`（K1-S1 已记『pin→pad 绑定本身正确（由 pinmap）』⇒ 本项是**脚号字段**与板 pad 命名不同构）。
  修法二选一（**监理自裁项**）：**(a)** 按 pinmap 把 J1 符号脚逐 pad 展开（本仓 `J14/U11/U9` 既有同类风格；
  J1 16→23 脚）· **(b)** 保留逻辑脚号并裁定该维口径（`adjudicate.py` 对 MCIO 有 remap 先例，但**改判据件=禁**）。
  **ENG 建议 (a)**。N-3 前后同为 16 ⇒ **无回归**。
- **R-2**：`k1_nets.yaml#nc` 留 `(U12,NC)/(U12,QOD)` 两条 TPS22919 旧件残留（继承式 nc 段）⇒ 白名单**超集**、零判据影响。
- **R-3**：`U1/PB2`（pad17）本批派生 NC（②同步后改由 PB8/PB9 承担）⇒ 与 **K1-D3「pad17 no-net 待核」**同址；
  NC 标记**不关闭 D3**。
- **R-4**：`k1_board.yaml#reconciliation` 块 = ②同步期**快照、已陈旧**（net_count 46 vs 现 51 等）⇒ 建议由
  `k1_sch_sync_v1.py` 刷新（不在本批）。**副产物**：`device_count.schematic_sch_k1=42` 由本批变**真**（**K1-S3 关闭**）。
- **R-5（可见性红线）**：`Q1` pad1(CT)/2(NC)/**4(VBIAS)**/7(PG)、`U12` pad**4(VBIAS)**/6(CT) **不进符号**
  （⇒ 也**不写 NC**）——写 NC = 宣称「有意不接」，会**掩盖 K1-D8（VBIAS 未接 = 功能级）**。
- **R-6**：**OPEN-2 未关闭** —— 只做了 sch↔板对齐；板侧 U10 footprint 本身仍是 3 pad `SOT-23`（实件 SOT-23-5）。
- **R-7**：`strap_intents`/`links` 清空（K2 残留）⇒ K1 自有意图/链路声明属另一件。

## 五、下一步（ENG 侧本批已闭）

1. R-1 修法 **(a)** 待监理自裁 ⇒ 落件后 `pin_map_complete` 可翻 PASS（+1 维）。2. C-25 tier2（`parts_electrical_truth.yaml`
   补全，现 PARTIAL 6/33）。3. K1-D1..D12 板级缺陷排期（**D8 VBIAS 为首**）。4. **P5 外部首件（V4–V7 `NOT_RUN`）= 唯一外部面，ENG 不自证**。

—— ENG（ARCHER）· 2026-09-20 · `k1 9e283bf`（已推）· 判据 **rev=6**（只读未动）· 交付锚 `6ee7495d…` 未动
