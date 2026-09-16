# R1/R2 落盘证据包 v1（#K2-13 五问全裁后执行）

- **依据**：监理 **#K2-13**（U1/S1、S2、S3、O2 四项裁定 + 安装重排接受 + `PWR_5V_KEY` 改判）。
- **结论**：五问全部落地；**T1 机检 PASS**；**E4 全 PASS**；ERC **0 error**（warning 已登记）；**E1 余 13 = P4 板侧补件（按 O2 登记）**。

## 1. U1/S1 —— `SPEC rev-21`（已落）

| 项 | 值 |
|---|---|
| 件 | `…/L3/SPEC_k2_v4.spec-rev-21.json` sha16 **`d46bd017aa560716`** |
| 内容变更（机器证明） | 唯一值变 = `spec_version: 1.1.spec-rev-20 → 1.1.spec-rev-21`；唯一删除 = `components.anchor_fixes.C64/C66`（6 叶子）；唯一新增 = `components.anchor_fixes_removed_v21`（留痕）+ `_spec_rev_11`（溯源卡） |
| **删除留痕（按裁定引 R1 分类）** | `C64` ∈ **A1**（32×220nF 下行 AC 耦合，8L 单颗下「耦合内置」⇒ 板上/真源均不存在）；`C66` ∈ **D 类**（`VREG` 域在单颗 `DS320PR1601` 下不存在）；`C82` 保留。依据 `K2-P2-R1-64item-classification-v1.md 7c95ca9922c5bc1f` |
| 原件不动 | rev-19 `5f72182a2616392c`、rev-20 `37dcd9cde5ceed09`（**逐字节未改**） |
| canonical 重指向 | `pm_gate/project.yaml` sha16 `b16371df27ac351c`（`spec_name → rev-21`，1 行变更）；L3 `README-canonical.md` `cf67c77bf9c486e4` 已同步（rev-21 canonical / rev-20 转前身） |
| 解析实测 | `pm_gate.config.spec_name()` → `SPEC_k2_v4.spec-rev-21.json`，`spec_version=1.1.spec-rev-21`，`anchor_fixes={C82, reason}` |

## 2. S2 —— 纸张 `A2 → A0`（已落）

- 件：`k2/hw/data/k2_sch.yaml` sha16 `dd794c54f7ce7417`；**逐字节 diff = 仅 1 行**（`-  paper: A2` / `+  paper: A0`）。
- 仅改该 1 字段；`(b)` 拆 unit 与 `(c)` 越界绘制均未采用。

## 3. S3 —— 采纳 (a) `PWR_FLAG`（已落）

- 实现（driver 内 **P9**，通用规则，禁硬编）：凡「有 `power_in` 脚且无 `power_out` 脚」的网，各放 **1 个虚拟 `PWR_FLAG`**（`in_bom no` / `on_board no`）于该网首个标签锚点。实测命中网 = `['GND']`（唯一），`flags_placed=['GND']`；未改真源任何引脚类型。
- 参考号用 **`#FLG01`**（编号形式）—— 首版用 `#FLG` 会触发 KiCad「批注错误」导出告警，已修，**导出告警归零**。
- ERC：**error = 0**。（`(b)` 已按裁定否决，未采用。）

## 4. 安装（接受重排；原件留档）

- 动作：**写** 5 件新 sheet + **覆写** root 与 `hw/lib/IOCONVERT.kicad_sym`；旧 6 件 `v5_*` 以 `git mv` 移入 **`k2/hw/sch/archive/`**（**未删**，历史保留）。
- **为何入 `archive/`**：判据侧 `criteria/adjudicate.py: measure_sch_refdes()` **glob 顶层 `*.kicad_sch`**，且 `_EXCL` 已视 `/archive/` 为归档 ⇒ 留档件若留在顶层会污染 E1（把 6L 旧件 refdes 计入）。此为实现"留档 + 判据不受污染"的**必要**处置，已在 `hw/sch/README-canonical.md` `fca6a920339225ca` 登记。
- 映射表（旧→新 sheet/文件名）与新 canonical 集合+sha：见 `k2/hw/sch/README-canonical.md`（#K2-13 §二.2「禁静默」）。
- 生成器：`k2/tools/k2_sch_gen_v1.py` sha16 **`70d84f184b5fb4e4`**（规则 P1–P10 见其头注）。
- **回退点**：`git -C k2 checkout -- hw/sch hw/lib && git clean -f hw/sch/archive`（安装前 k2 HEAD = `3aad998`）。

## 5. 落盘后机检

| 判据 | 结果 |
|---|---|
| **C1 确定性** | ✅ 两次独立连跑：5 sheet + root + `IOCONVERT.kicad_sym` **逐字节相同**（root `a7cbb7a7aa54d4c3`、lib `84ffb7de31fbcd82`） |
| **T1 并网 32 对（#K2-12 §二.1 机检）** | ✅ **退役名（`*_U3`/`*_U7`）= ∅**；**32/32 保留名并网且球映射与 T3 表一致**（例 `PCIE_DN_OUT0_P_MCIO` → J3/3 + U6 **M26**=`A_PETP0`；`PCIE_UP_OUT0_P_J2` → J2/2 + U6 **P10**=`B_PETP0`）。T3 表：`k2/docs/K2-P2-R1-T3-pin-ball-remap-draft-v1.json` |
| **T2 图注留痕** | 路径 (ii) 形态：`R4/R9/R26/R27` 未出现于再生图（真源不含）；删据 = 冻结 SPEC `strap_domain_v32.non_strap_sideband`（`ALL_DONE`/`READ_EN` = **NC no-action**）+ R1 **C 类**分类。**以文档留痕替代编辑级图注**（(ii) 不产编辑注），已此处登记 |
| **C3 ERC** | ✅ **error = 0**；warning profile = `endpoint_off_grid 452` / `lib_symbol_issues 55` / `footprint_link_issues 15` / `lib_symbol_mismatch 1`（**豁免登记见 §6**） |
| **C4 结构** | ✅ 括号平衡 0；每 sheet 实例数 == yaml placements（3/10/21/12/9 = 55）；root 5 sheet（page 2–6） |
| **E1 复算（冻结仪器）** | 板 **42** / 原理图 **55** / 网表 **55**；**板-图 = 0**（原 3：`C88/C89/U6` 已入图）；**图-板 = 13** = `D2,L1,R35–R39,R40,R41,R42–R45` ⇒ **= P4 板侧补件（按 O2 登记），非不一致**；**不等于「接近 0」式宣称归零** |
| **E4（§五 ⑥）** | ✅ ① 两次连跑 sha 同（`k2_v6.kicad_pcb f615ffe6b83b88a3` / layout `a48778b818211e96` / pro `aed49832c39d2ad1`）；② refs **42**；③ 边框 **120×46mm** `[23,143]×[33,79]`；④ 自检 **6/6 PASS**（S3/S7 已按 G6/G8 移除）。生成器 `k2/tools/k2_gen_v5.py` sha16 **`d8d15a31061f450f`**（G1–G8 已落；G2 自定位 `PM_GATE_PROJECT_ROOT`） |

## 6. ERC warning **豁免登记**（#K2-13 S3 附条件「禁静默」）

| 类型 | 数 | 性质 / 豁免判据 |
|---|---|---|
| `endpoint_off_grid` | 452 | **真源符号几何**：多处 `body_width` 非 1.27 倍数（19.8/23.3/32.7…）+ 354 脚符号，引脚端点天然 off-grid，wire 与 pin tip 坐标精确重合 ⇒ **连接不受影响**。基线（旧图）同型 304 条 ⇒ 非本次引入 |
| `lib_symbol_issues` | 55 | **环境**：本机未把 `IOCONVERT` 注册进 sym-lib-table（旧图基线同型 103 条） |
| `footprint_link_issues` | 15 | **环境**：本机 fp-lib-table 未注册（旧图基线同型 14 条） |
| `lib_symbol_mismatch` | 1 | **PWR_FLAG 内嵌定义**与系统 `power` 库同名件有差异（本生成器刻意不依赖系统库）⇒ 按裁定**登记豁免**，不静默 |

## 7. O2 口径登记（防「42 通过」被读成终局合格）

- 本阶段判据：**refs == 42**（对齐真源板）。
- **`final_target: 55 @P4`** —— 差 **13** = `D2, L1, R35–R39, R40, R41, R42–R45`。已写进生成器头注（`E4_STAGE_REFS = 42` / `E4_FINAL_TARGET_REFS = 55   # @P4`）并落 P4 缺陷清单。

## 8. 关键件 sha16（本包一次性对账）

rev-21 `d46bd017aa560716` · rev-20（未改）`37dcd9cde5ceed09` · L3-README `cf67c77bf9c486e4` · project.yaml `b16371df27ac351c` · yaml `dd794c54f7ce7417` · driver `70d84f184b5fb4e4` · gen `d8d15a31061f450f` · root `a7cbb7a7aa54d4c3` · lib `84ffb7de31fbcd82` · sch-README `fca6a920339225ca` · 交付板（未改）`d4e81f647be7f980`

## 9. 图侧对板侧缺陷的**可见性**（禁静默 · #K2-13 §三）

- **真源侧**：7 网中**仅 `PWR_5V_KEY` 是单节点**（`{C89/A}`）；其余 6 网在真源有 2–3 节点
  （`SW_U2={U2/SW, L1/B, D2/A}` · `FB_U2={U2/FB, R40/B, R41/A}` · `PWR_CTRL_OUT={U5/COLLECTOR, J6/PWR_BTN#}` ·
  `UART_RX/TX={U1, J9}` · `SWCLK_BOOT0={U1, R28/A, J13/RX}`）—— 故「板上单节点」是**板侧未接/缺件**，非图侧缺网。
- **图侧表现（显式、非抹平）**：`PWR_5V_KEY` 因真源单节点，C89/A 脚由共享路由既定策略标
  **`(no_connect)`** ⇒ 网表中呈 `unconnected-(C89-A-Pad1)`；**真源该网未被删除**（遵 #K2-13 §三 ②）。
  该标记使缺陷在图上**可见**，并已在 P4 清单 §2 独立登记。
- 其余 6 网在图上**正常标签/走线**渲染（不缺网），其"单节点"仅存在于板侧统计。
