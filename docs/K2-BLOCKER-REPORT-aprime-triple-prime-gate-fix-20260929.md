# 卡点报告 · A‴（放置闸补 mask-dam · 重出放置 · 落板前置）— #K2-389 §二 执行

- 授权：#K2-389（**准换法 ＋ 三条边落地**）；本窗**零 exam 跑**（配额 A′／A″ 仍花尽）；板面冻结（板只在 `/tmp`）
- 件：`L2/EXAM_A_TRIPLE_PRIME_SCENARIO_v1.json` · `L2/EXAM_A_TRIPLE_PRIME_PLACEMENT_DERIVATION_v1.json` · 见证板 `L2/refs/EXAM_A_TRIPLE_PRIME_PLACED_v1.kicad_pcb`（`32d3c644692c564d`）

## 一、闸的洞（本件机证根因）

放置闸 `mech_probe`／`mech_probe_moves` 原**只白名单 4 类** DRC（`courtyards_overlap/shorting_items/clearance/hole_clearance`）
⇒ **`solder_mask_bridge` 被整类漏掉** —— 所以 A″ 的逐件位移**通过了闸**却带着 2 处阻焊桥落进考题。
（且该闸只看 gen 板的 DRC，不消费在册阻焊规则。）

## 二、本件落地（#K2-389 §二 逐条）

| §二 | 交付 | 证据 |
|---|---|---|
| **.1 放置闸增补 mask-dam 约束（消费在册规则）** | 新增**纯几何** `route.pad_mask_dam_violations(board, clear)`（开窗矩形＝焊盘 bbox 外扩**在册** `solder_mask.pad_to_mask_clearance`＝0.05mm；异网 · 同阻焊面 · **开窗相接/重叠** ⇒ 违规）；**两个探针**都（a）**消费该规则**且（b）把类过滤由**白名单改黑名单**（仅排除库解析类）⇒ **任何新类**都在基线相对比较里被拒；规则不可读 / 检查失败 ⇒ **fail-closed** | 见 §三 |
| **.1 重新出放置** | `regen.rearrange_probe(l14, 框, 25 成员)` 重跑（**51 探针 · 1m58s**）⇒ **新见证板**：**零 mask-dam 违规 · DRC `solder_mask_bridge`＝0 · 无任何类高于闸基线** ⇒ **闸过 ⇒ 场景合法** | `L2/EXAM_A_TRIPLE_PRIME_*` |
| **.2 落板前置 fail-closed** | `wipe_resolve` 链在**判卷前**加 `landing_precondition_no_isolated_copper`：refill（＋有界孤岛处置）后**仍残留 `isolated_copper` ⇒ `W3B_REFUSED_ISOLATED_COPPER`（拒板具名）**——「无孤岛」是**落板前置**，**非事后修补** | 回归 `test_C389_the_chain_refuses_a_board_that_still_has_isolated_copper` |
| **.3 九行锁维持 ＋ C8 实测补录** | 九行锁（#K2-388）**不动**；**C8 实测＝0**（见证板／attempt3 终板）**补录**进 attempt3 记录 | `Eda_ENG_..._ATTEMPT3_RECORD_v1.json :: c8_backfill_measured` |
| **.4 新考卷新编号 · A″ 冻结归档** | 新件一律 `EXAM_A_TRIPLE_PRIME_*`（A‴）；A″ 场景/证书**保留不动** | `L2/EXAM_A_TRIPLE_PRIME_SCENARIO_v1.json :: supersedes` |

## 三、二值结论（§二.1 的判分支）

- **闸过 ⇒ 场景合法**（成立）：重出的放置 **mask-clean**（规则 0 违规、DRC 0 桥、无新类）⇒ **不触发**「场景-C2 不兼容」分支。
- **对照机证**：**旧 A″ 见证板**在闸下报 **3 处** mask-dam 违规 ⇒ 正是本次修掉的漂移；**l14 参照＝0**。

## 四、重出放置的读数（诚实 · 含未动件）

- **17/25 件**取得闸通过的 SE 位移；**8 件未动**：`U1 · J11 · D2 · R1 · R28 · D1 · R21 · C90`。
- **U1 为何一步都不可动**（U1 是**面积最大者，第 1 个试**，此时无人让位）：k=1,2 ⇒ **gen_v5 直接拒（`S1 PAD_OVERLAP` U1.12 ↔ J9.1 真铜重叠）**；k=3 ⇒ **开窗相接＝A″ 那处桥（本次修掉）**；k=4 ⇒ 桥＋clearance；k=8 ⇒ gen 失败。
- **剩余缺口（下一个能力）**：`.2` 的**处置**（把孤岛**确定性移除/重填**，使板可落）**本窗只做了前置（拒板）**，未做处置 ⇒ 若孤岛仍在，链会**拒板而非出九行**。这是**有意的 fail-closed**，也是下一窗的确定性工作项（照方案件 edge ii）。

## 五、纪律 / 边界

- 本窗**零 exam 跑**；`aprime_witness` 冻结维持；**无新授权而跑 ＝ 违规**。
- 闭包收尾脚本 `k2_delivery_closure_check_v1.py` **每收执只跑一次**（遵 #K2-389 §三）。
- 仍待裁：`regen.exam_a_chain` 未定义名 `rp`/`blocked`（既有 · 未修 · 越窗）。
