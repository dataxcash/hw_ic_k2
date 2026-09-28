# 卡点报告 · A″ 同因三败 ⇒ 回方案层（#K2-388 §七 · 零考跑）

- 上游：#K2-388（R1072「跑次合规 · 判卷无效（缺 C8）」⇒ §17.4 换手段 · 不换目标）
- 本窗交付：**方案层回归件 ＋ 自检补强（C36）＋ C34 §20 闸接 `wipe_resolve` ＋ §20 成品三问**；**零 exam 跑**
- 板面：**零改动**（板只在 `/tmp`）· 冻结四源 4/4 · 无 Gerber／下单／WORKER

## 一、人类工程师路径三问（大白话）

1. **信号怎么走**：把这小片器件挪几毫米 → 把它压到的铜整块清掉（615 段＋95 孔）→ 在框内用标准流程重接线 → 复敷铜 → 判分。
2. **挡路的是什么**（本次多了**机器实证**，两处都不是「布线没接好」）：
   - **2 处阻焊桥是「给定的放置」自带的**：**在任何布线之前**，那张被读回的放置板（`placed.kicad_pcb`）**就已经报同样两处桥**（U1 焊盘 11/12 ↔ J9 焊盘 1）。几何：J9.1 是 1.5×1.5 的 PTH 焊盘；挪位后 U1.11 的右边沿与 J9.1 的左边沿**只差 0.10mm**、且两者**同一 y 带** ⇒ 加上在册规则 `solder_mask.pad_to_mask_clearance = 0.05`（开窗各 +0.05），**两开窗正好相接** ⇒ 桥。**布线器碰不到焊盘对焊盘的阻焊规则**。
   - **3 处孤岛铜是「复铜后的残留」**：12V_IN 的 In4 灌注在复铜后成了孤岛；上一次的「事后就近连回」实测**无效**（检出 3 · 规划 2 · 仍报 3）。
   - 另：**22 处线头接不上**全是**端点无空位**（`no-free-start-node` 16／`no-free-goal-node` 6）。
3. **人类方案（确定性 · 禁搜参，下一次一次做）**：
   - **放置层**：把在册规则（0.05mm ⇒ 阻焊坝 0.10mm）**接进放置闸**——给出的位移图**只有满足「被挪焊盘与任何异网焊盘的阻焊开窗间隔 ≥ 0」才算合法**，否则**拒收**（对**给定图**做确定性判定，不搜索）。
     **若放置固定（A″ 正是如此）** ⇒ 该位移图**本就违规**，C2「不长新类」**结构性不可达** ⇒ 依 #K2-388 §六.4 **交监理携证书升 owner（冻结集）**。
   - **灌注层**：复铜后**把「无 `isolated_copper`」当落板硬前提**（在册语义：l14 各 zone 均 `island_removal_mode 0`＝移除孤岛）——仍残留 ⇒ **拒落板**（**不再事后修补**）。
   - **端口层**：把框边被切开的 stub **当合法端口**发进迷宫（不再跨块猜目标）。

## 二、本窗交付（逐条对表 #K2-388 §七）

| 条 | 交付 | 落点 |
|---|---|---|
| §七.1 | **方案层回归件**（§16.3 四要素：死因／已证事实／修正后完整方案／`buildability=relocation_listed`） | `L2/A_DOUBLE_PRIME_PLACEMENT_POUR_PLAN_v1.json` |
| §七.2 | **自检补强（C36 关账判据）**：判卷在**实际执行的链路径**上逐行枚举 C1–C9；**缺行 = fail-closed** | `verify.LOCKED_EXAM_ROWS` ＋ `judge(required_rows=)`；四链（`relocate_block_chain`／`relocate_relative_chain`／`relocate_relative_c17v1`／`wipe_resolve_chain`）全部带 `required_rows`；`wipe_resolve`／`relocate_block_chain` 补 C8(+C9) |
| §七.2 | 同类回归件（**路径感知**，先 RED 后 GREEN） | `test_C36_each_exam_chain_path_enumerates_the_nine_rows`（旧「整文件 grep」版**已删**，它正是误绿源头）＋ `test_C36_a_missing_row_is_fail_closed_at_runtime` |
| §七.3 | **C34 §20 闸接 `wipe_resolve` 入口** | `cli.DEFAULT_GATE_CAPABILITY["wipe_resolve"]="A_double_prime_placement_pour"` ＋ 闸在 `preflight` **之前**命中 ⇒ 不过即 `REFUSED_BY_SEC20_GATE`；回归 `test_C34_the_gate_guards_the_wipe_resolve_entry` |
| §七.4 | **§20 成品三问**（同类工具怎么处置这两类？可抄件？差异清单？） | `L2/PRODUCT_THREE_QUESTIONS_LEDGER_v1.json :: A_double_prime_placement_pour`（并引用在册成品库 `.omo/supervision/ledger/REF-CASE-LIBRARY.md`，注明其 A/A1 只覆盖同芯片**布线**、不覆盖 DFM/灌注） |

## 三、新增机器实证（本窗只读）

| 读数 | 值 |
|---|---|
| 放置板自带阻焊桥 | **2**（U1.11／U1.12 ↔ J9.1；**零布线**时即存在） |
| 放置板自带孤岛 | 0 |
| l14 参照阻焊桥 | **0** |
| **C8（成员零越框）** | **0（witness）· 0（attempt3 终板）** ⇒ 漏掉的那行**本该是 PASS** |
| 阻焊坝 | 规则值 0.05 ⇒ 坝 0.10mm；实测 X 间隙 **0.10mm** 且同 y 带 ⇒ **相接** |

## 四、结论

- **同因三败**（A′ R1028／A″ att2 R1054／A″ att3 R1072）⇒ **换手段**已落为**方案层确定性路径**（放置约束／灌注重填硬前提／端口）。
- **两条残余的层不同、修法不同**：阻焊桥＝**放置**（A″ 固定放置 ⇒ 需 owner 裁「允许修放置」或「重导 DFM-clean 见证」）；孤岛＝**灌注**（确定性 + fail-closed）。
- **本窗零考跑**；`aprime_witness` 冻结维持；**无新授权而跑 ＝ 违规**。
