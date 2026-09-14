# CO-235 — 非执行者对抗复评 **CO-231..CO-234**（+ 同会话处置）

复评者 = **非执行者**（context 归零之**新会话**；**未参与 CO-231..CO-234 之任何撰写** ⇒ 四节全在对象内，无自评豁免面）；as-found 逐件钉 `03f8d39`；扰动 = 实件注入 + 字节复原（零残留）。
判决 = **PASS_WITH_FINDINGS**（findings 2：F-1 mid / F-2 low；正控 V1..V6 全 True）。**未**改动冻结四源/板/SPEC。

## 0. 复评范围补正（F-2）

复评链上一段 = **CO-230 覆盖 CO-225..CO-229**；其**后**新增 `c1a880b`（CO-231）**未入任何复评声明面** （z96 之复评债仅声 CO-232/233/234）⇒ 枚举面缺项。**本件补足：复评范围 = CO-231..CO-234**（承 R-CO219-1 / R-CO230-1）。

## 1. as-found（逐件 sha16，`git show 03f8d39` 重放）

| 件 | as-found sha16 | 重放 |
|---|---|---|
| `tools/p3_v57_co164_order_runner.py` | `08c104cda26d2940` | MATCH |
| `tools/p3_v57_co146_boundary_append.py` | `f8ad3b96c289ce51` | MATCH |
| `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md` | `17924a8d4a0246e7` | MATCH |
| `pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json` | `b6477520967efafc` | MATCH |
| `tools/p3_v57_co195_fixpoint_uniqueness_oracle.py` | `585b983de844603d` | MATCH |
| `tools/p3_v57_co120_provenance_pin_gate.py` | `28d6211f32318d9b` | MATCH |
| `k2_v4_8L.l4.kicad_pcb` | `d4e81f647be7f980` | MATCH |

## 2. 正控（本会话独立实测）

- 冻结四源 **4/4 MATCH**；`drc_rules` 副本同字节 = **True**；交付板 `d4e81f647be7f980` 逐字节未变 = **True**
- 静态面（runner `--check`）由 runner 自承载，**结果不内嵌**（承 R-CO193-3）；根因两式（V4）：as-found `CITE`/pin 正则对粗体行 = **False/False**，修复后 = **True/True**（**同域**）
- 行普查（V5）：含 16-hex 之表行 **578**；as-found 非 2 列者 **18**；修复后仍不在 pin 面者 **4**（['G4/W3', 'G5/W4', 'G6/L4', 'G7/L5']）

## 3. findings

### F-1（TOOL_DEFECT · mid · CLOSED）**pin 行值之判据面/realign 面各自由格式隐式给定 ⇒ `**`sha`**` 变体静默逃逸**

注入实测**不入记录**（自指：记录**被 pin** ⇒ 记 `--check` 读数即污染下次运行；承 R-CO193-3）；判别力由 runner 之 **t40/t43**（各含合成正/负控）承载：
- 粗体行值伪造 ⇒ t40（值核）/t41（生成器差分）/t43（格式核）任一可检出；**整行删除**（§1..§22 手工面）⇒ **残余**（行集完备性不判；CO-231 已声明）
**处置**：生成器 `CITE` 扩 `(?:\*\*)?`（realign **同域**）+ runner **声明格式集** `PIN_ROW_FORMATS_DECLARED`（`pin2`/`pin3`，`boundary_pin_rows()` 遍历之 ⇒ **t40 值核覆盖 §2 全 14 行**）+ 静态齿 **t43_pin_row_format_covered**（未声明之新形态 **fail-closed**）+ §3 G7/L5 **口径同步**（历史快照 vs 现行 L5-SI.11）。**R-CO235-1**。

### F-2（RECORD_HYGIENE · low · CLOSED）**复评债声明面漏 CO-231**

复评链谱（§82..§107）无一段含 CO-231 ⇒ 本件补足范围；叙述类**不入登记簿**（承 CO-213 F-2 先例）；handoff z97 更正。

## 4. 观测

- O-1（被评记录之声明诚实性）：CO-232 之残余「生成器只拥有各 § 区段」经独立复算 —— §23..§107 = 1710 行受权威、§1..§22 = 686 行**手工面**（约 28%）⇒ 残余声明**量级属实**；惟其后果（手工面内值不可核/不自愈）在本件 F-1 之 E3 实测中被具体化。
- O-2（CO-233 相容性）：oracle 之 realign（注入后 + finally）使扰动协议与新增状态齿相容；本件 V3 之 `--check` 与 oracle 记录（PASS / 5 案）**不含**互相替代之证据 —— 相容性由 oracle 全跑承载，本件不重跑（其受控件扰动 ~4 min，避并发）。
- O-3（CO-234 残余之界定）：`.md` 受控件以**显式域名**排除（其受控性由 t20 承接），且 7 枚 md 卡片在 pin 面**无 pin**、§2 表内亦**零次**出现 —— 属**已声明**之域排除（R-CO234-1 允许「显式域名除外」），**非**本件缺陷；域缩水仅由下限（25）部分拦阻（z96 已登记为残余）。
- O-4（诚实边界）：本件**不**复评 B 路 10L 实做、外部工艺/报价面（外部输入）；**不**判 boundary 节内叙述之完备性；**CO-235 自身须下一轮复评**（禁自评）。

## 5. 红线

**R-CO235-1**：**判据面与 realign 面须同域** —— 凡以「行的形态」界定判定域者，须**显式声明格式名集**（非由单一行正则隐式给定），并以**覆盖面臂**保证「域外无 carrying-同语义之对象」（未声明之新形态 ⇒ **fail-closed**）；且**值面**（现行 sha）之 realign 面须与判据面**同域** —— 不得一方覆盖、另一方漏过（漏过即**静默陈旧**）。承 R-CO230-1 / R-CO231-1 / R-CO152-1。
