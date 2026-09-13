# CO-219 — 非执行者对抗复评 **CO-213..CO-218**（+ 同会话处置）

复评者 = **z79..z84 谱系之外**之 context 归零续接会话（as-found 逐件钉 `3d68891`；扰动一律内存注入、零落盘）。
判决 = **PASS_WITH_FINDINGS**（findings 2，皆 low；负控 6 全触发；正控 11 全 True）。**未**改动冻结四源/板/SPEC。

## 1. as-found（逐件 sha16，`git show 3d68891:<path>` 复核）
| 件 | sha16 |
|---|---|
| runner `p3_v57_co164_order_runner.py` | `d91631edf5b1d251` |
| oracle `p3_v57_co195_fixpoint_uniqueness_oracle.py` | `58f76ff56df5b368` |
| co120 闸 `p3_v57_co120_provenance_pin_gate.py` | `6deb36e1845ebb83` |
| 登记簿 / boundary / 判据件 / 交付板 | `886ec25e2eb840df` / `9b001d4e8ab10168` / `e4654aeda2cab72d` / `d4e81f647be7f980` |

## 2. 正控（自跑闸，皆通过）
冻结四源 **4/4 MATCH**；交付板逐字节未变；`--check` **36/36 True**；序 `--max-iter` **收敛 rc=0 / 2 轮 / 零 diff**；
oracle **PASS 11/11 齿** 且幂等；co120 **PASS（19 齿 / `l5_bad=0`）**；l5_signoff `spec_src_ok/board_pin_ok` 与二者**判别力**皆 True；
co206 A=FEASIBLE_PENDING_DFM、B=UNPROVEN、**7/7 齿**；登记簿 **159 / OPEN 0**（co124 PASS 40/40）。

## 3. findings

### F-1（TOOL_DEFECT · low）**表项未名集钉定 ⇒ 删项即空真**
`frozen_sources_decision()` / `proxy_coverage_decision()` / `l5_board_binding()` 皆**只遍历已登记项** ⇒
`FROZEN_SOURCES={}`、**删单枚 SPEC pin**、`PROXY_HELPERS_PINNED={}`、`L5_RECORD_JSON={}` 时对应齿仍 **True**。
实测最重后果：**删 SPEC pin 后，注入 SPEC 漂移仍返回 `ok`**（该源不变性之检出率**归零**）。
同档 t27（`set(BASIS_JUDGE_DECLARED) == {…}`）/ t21（读者集等式）/ t16（齿集 pin）**已有该制** ⇒ 此三处为遗漏。
**处置**：三表各加**名集等式**（**不新增齿**，齿数仍 36）；runner `CO-203.1→CO-203.2`、co120 `CO-120.7→CO-120.8`。
**修后**：同一批注入 ⇒ 对应齿**全 False**；`--check` 仍 36/36 True。

### F-2（TOOL_DEFECT · low）**oracle 前置未达不阻断 + 基线重锚 + 污染不自愈**
t00（先结算）不成立时 oracle **仍注入/度量**，并把 `sha_canon` 取自**当下污染态**（实测 `914b65197ad76b19` ≠ as-found `3b02b97dc9f1f4bc`）；
逐案 `finally` 只复原到**案前（污染）态** ⇒ 污染不自愈。实测后果：某已闭合登记项被重开为 OPEN 而 `counts.OPEN=0` ⇒
**co124 随即 FAIL_REGISTER_STALE**（`T21c=false`），人工复原 HEAD 后全绿。上游写入者**未根因定位**（疑并发/带外写者交叠），故只据**可复现之工具行为**立据。
**处置**：增**前置 fail-fast**（`FAIL_SETTLE_NOT_CONVERGED` + `how_to_recover`，不注入/不度量/不重锚，rc=1）；oracle `CO-202→CO-219`（runner `TOOL_REVISION_DECLARED` 双侧同步）。

## 4. observations
- **O-1（诚实边界）**：`drc_rules.json` 容器内实存 **5 份**（k2/k1/pciesw4/key_v2 + 根 `_shared`，5/5 同字节），CO-218 只钉 **2/5**；K2 各闸仅消费 K2 份 ⇒ 非缺陷，触发 = 改读他份或副本分歧。
- **O-2（处置卫生）**：复评中一度出现非规范树（F-2），处置 = 立即 `git checkout` 复原并**复核 pin 吻合**后再续（先复原、后立据）。
- **O-3（诚实边界）**：未复核 B 路 10L 实做（须 L1/几何）与外部报价面（外部输入）；CO-219 自身须下一轮复评（禁自评）。

## 5. 红线
F-1 ⇒ 承 **R-CO215-1 / R-CO218-1**（覆盖面/锚点须**名集**机判，非「已登记项自洽」）；F-2 ⇒ 承 **R-CO195-0/1**（前置须 fail-closed，禁以污染态为基线）。
