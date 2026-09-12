# CO-90（非执行者侧对抗评审 **pass 3/3**）— 对象 = rev-9 新基线（CO-88/CO-89 + 全链）

> 日期 2026-09-12｜工具 `tools/p3_v57_co90_nonexecutor_review_pass3.py`（需 AppDir pcbnew；只读 + scratch）
> 记录 `m13_v57_co90_nonexecutor_review_pass3.json` `897ff5cc371d135d`（CO-90.2）｜SPEC **rev-9** `77f5c54df88bb0ca`｜板 `0e636a67c1472462`
> 宪法依据 `L2/frozen/L2_STRUCTURE_v2.0.md:137`（重开层须重新过对抗评审）；CO-76 = pass 1/2，CO-85 = pass 2/2（旧基线）。

## 0. 评审者独立性
本会话为 context 归零续接会话，**未执行 CO-88/CO-89 或 rev-9 全链任何变更**（只加载 handoff-z2 + ledger 尾 + §8 小件）
⇒ 具非执行者资格。本件新写的 CO-90 记录/工具与 boundary v1.55 文本更正**不属评审对象**（自审不入）。
落盘复评（续接 pane16）时另发现 **F4（co88 记录可复现性）/F5（co77 引用闸行级豁免空真）**，由实测对照暴露并**同件修复**（见 §4/§5）。

## 1. 为何立本件
CO-89 把 SPEC 提升到 **rev-9** 并**重基线全链**（drawing/G5/construction/fab/G7 指纹全变）⇒ CO-85（pass 2/2）的证书
**只对旧基线有效**，其 V1「12/12 逐字节复现」结论随基线失效。handoff-z2 §7-2 与 boundary v1.54 §6-9 残余②均登记
**「新基线非执行者复评欠」**。本件即履行该义务（对象 = rev-9 交付态工件 + CO-88/CO-89 的闸与其声明）。

## 2. 方法与独立度
| 栏 | 内容 | 独立度 |
|---|---|---|
| V1 | 按 handoff §9 复跑全链 G4→G7，与 rev-9 冻结指纹**逐字节**比对 | 同代码复跑（验可复现，非独立实现）|
| V2 | 板事实**自写直解**（段/过孔/zone） | 与本链工具不同实现 |
| V3 | SPEC rev-9 事实：`pd` 外逐值比对 rev-8 / 旧 BOM 退役对数 / 解耦板实 / **ppc↔板实 pad 双射** | 独立实现（pcbnew + 自写集合运算）|
| V4 | CO-88 闸**注入突变测试**（4 合成件） | **独立于记录自述**的牙齿检验 |
| V5 | 覆盖口径：`.kicad_pro` POWER 类网 vs 生成器内置网集 | 独立实现 |
| V6 | CO-89 幂等：项目发生器 scratch 重生成 ppc 与 rev-9 逐值比对 | 独立重跑发生器 |

## 3. 复核结果（V1..V6 全过）
**V1 全链逐字节复现（12/12 交付件）**：drawing `3d452429bbc934c3` / landing `da21d0186a9c643c` / G5 `7acb3186c3b68848` /
construction `ca2ff16f6445424c` / l4val `a87b8d17bef6edca` / **板 `0e636a67c1472462`（不变）** / fab `6d85160413770fa5` /
DFM `40445f87be664f31` / SI `73f9b59ed5f6f3ce` / dru `3148703240d54420` / pro `ce2c2bf0da79a1ff`；
G4 FEASIBLE_ALL（34 页 / crossings 0 / work 546-546）、G5 PASS（G-M1..6、frozen）、G6 PASS（viol 0）、
G7 FAB ok / DFM new=0 / 在册未连 0/68 / SI skew **0.1300 ≤ 0.15**。**drift = {}**。

**V2 板事实（自写直解）**：段 **2523**（F 174 / In2 106 / In5 2204 / B 39，**In4、In6 = 0**）、via **252**、zone **4（全 ESC_ 规则域）**
⇒ 与 CO-85 V3 一致，物理交付件未动。

**V3 SPEC rev-9 事实**：`pd` 以外**顶层键 0 处变更**；`pd` 内仅 `zone_defs / decoupling / decoupling_legacy_retired`；
旧 BOM 退役对数 = **173 entries + 9 blocked**（= rev-8 原数，**显式留存**）；rev-8 孤儿 **55 entries + 2 blocked**（独立复算一致）；
rev-9 **0 孤儿 ref**；解耦 targets 全板实、vias 3→0 且旧 vias 退役留存 3；**ppc ↔ 板实 pad 双射精确成立（309 = 309，双向差集皆空）**。

**V4 闸突变测试（4/4 命中）**：基线 rev-9 → headline PASS；注入孤儿 ref `U99` → A=FAIL；删 1 条 entry（C89.2）→ B=FAIL（silent=1）；
清空解耦 targets+vias → C=FAIL；注入缺失解耦 ref `U99` → C=FAIL。⇒ CO-88 判据**有齿**（且见 F1 修复后回归）。

**V6 CO-89 幂等**：`pad_connect_gen` 对交付板 scratch 重生成 = **223 entries + 86 blocked**，与 rev-9 **逐值相等**（entries/blocked 两栏均 True）。

**回归闸指纹（全 PASS，未随本件改动漂移）**：co77 `PASS`（闸 **CO-77.3**；记录 `doc_sha16` 随 boundary 更新 ⇒ 按 verdict 记，同 CO-90 工具口径；原旧基线 sha `68a5ca50f1c24abb` 已随 rev-9 重基线失效）/ co78 `b736a0df7226f155` / co81 `16b262663238a60a` /
co84 `b927acbe46ec3007` / co87 `24aeb57f71a716f4` / co69 `18a86c998dd6b4de`（A1..A10 10/10）。

## 4. 发现
### F1（中｜闸内空真 / partial-pass 风险）CO-88 headline verdict 未并入判据 C
- **对象**：`p3_v57_co88_pdn_board_reality_gate.py` 的 `rec.verdict`（CO-88.1）。
- **反证（突变 m3）**：置 `decoupling_via_to_plane.targets=[]` 且 `vias=[]`（= **零板实解耦落点**）⇒ 子判据 `C_decoupling.verdict = FAIL`，
  但 headline 仍为 **PASS**（原判据只查 `orphans["decoupling_via"] == []`，**不查 targets 非空**）。记录自相矛盾 ⇒ 正是本闸要防的 partial pass。
- **修复**：headline 并入 `c_ok`（targets 非空 + 无缺失），并新增 `verdict_by_criterion` 使三判据与 headline 同源。**修复后 m3 → headline FAIL（F1 回归）**。

### F2（中｜空真牙，CO-79 同类）CO-88 自述 teeth 恒真
- **对象**：CO-88.1 `teeth.synthetic_orphan_ref_detected` / `silent_detector_control`。
- **证据**：前者 = `bool({"U99"} - board_refs)`（**只查板 ref，未运行检测器**；`syn = spec_refs(syn_spec)` 为**死代码**）；
  后者第二操作数 `{("U99","1")} - set(pads)` **恒真**。⇒ 记录自述的阳性对照**不构成对检测器的检验**。
- **修复**：改为**真跑检测路径**的注入测试（orphan / silent / 空解耦 / 缺失解耦 ref 四路，共用正式判定的同一实现）⇒ 修复后 4/4 True，且若检测器被破坏则对应牙会翻 False。

### F3（低-中｜覆盖口径 / 声明范围）CO-88/89 的「309/309 = 100%」是**口径内**声明
- **对象**：CO-88 B 判据分母与 CO-89 §1「板实覆盖 309/309 = 100%」。
- **证据（V5）**：分母 = `eda_core.pad_connect_gen.DEFAULT_PWR_NETS`（**内置常量**）。交付板 `.kicad_pro` `netclass_assignments` 的 **POWER 类**
  还含 **`PWR_5V_KEY`**（非集内）；其板实落点 = **`C89.1`（SMD，0 走线）** ⇒ 该 pad **既不在 CO-88 的 309 分母，也不在 CO-89 的 309/309 覆盖**。
  另：`pad_connect_gen` docstring 自称「PWR_NETS 从 SPEC constraints/net_classes 推导」，**实现只读内置常量**（文实不符）。
- **影响面**：v57 范围为 68 条高速网（boundary §6-4），`PWR_5V_KEY` 无走线、属 SPEC `layer_plan.low_speed_nets`，**非本阶段交付对象** ⇒
  非功能性缺陷；但**声明必须限定口径**（「= 内置网集上的板实 SMD pad」），否则读作「板全电源网 100%」。
- **状态**：**已登记**（不改分母）。改分母 = SPEC rev-10 + 全链重基线，且「哪些网计入 PDN 覆盖」属**网范围/电源域口径**（需 PM/owner 确认）⇒ 不在本件自裁。

### F4（中｜记录可复现性）co88 记录曾把「目录扫描建议清单」嵌入**哈希体**
- **对象**：`p3_v57_co88_pdn_board_reality_gate.py:rec["ripple_checklist_if_spec_bumped"]`（`ripple_checklist()` 扫描 `tools/*.py`）。
- **反证（两次对照实测）**：移走 `tools/p3_v57_co90_nonexecutor_review_pass3.py` → 记录 sha `d320c81263733158`；放回 → `b9990766698af315`。
  即 **co88 记录 sha 随无关工具文件的增删而变** ⇒ boundary 引用的 sha 在提交前即不可复现（且扰动源正是 CO-90 自身工具）。
- **修复（CO-88.3）**：ripple 清单移出哈希体（记录恢复为 **(SPEC, 板) 纯函数**；需要清单时按需调用 `ripple_checklist()`）⇒ 稳定值 **`bf69909aa64dc494`**，修复后「移走/放回 CO-90 工具」三次同值。
  零几何；修复前后 co88 判定均 PASS。

### F5（中｜引用闸空真）co77 历史豁免按**整行**判定
- **对象**：`p3_v57_co77_closure_declaration_sweep.py` 的全量引用校验（CO-77.2）。
- **反证**：co88 记录漂移到 `b9990766698af315` 后，co77 仍报 `citation_mismatch=[]`（本应报警）。根因：`STALE=("已取代","历史","原 ","应为","实为")` 按**整行**命中即豁免，
  而「**现行值** + 同行括号里记录旧值已取代」这类行（如 `…json` `d320c812…`（…；原 `f90d6536…` 已取代））把**现行值**也一并豁免。
- **修复（CO-77.3）**：豁免改为**按引用**判定（校验紧跟该 sha 之后的标记窗口，或 `→` 变更记法）。
- **负控（牙齿）**：向 boundary 副本注入现行 sha `deadbeefdeadbeef` → co77 报 **CITATION_MISMATCH**（修复前该形态漏过）；真件仍 PASS。存量历史引用按需显式标注「历史·」（v1.55 已标注 1 处）。

## 5. 修复与再基线影响
| 件 | CO-90 前 | CO-90 后 |
|---|---|---|
| `tools/p3_v57_co88_pdn_board_reality_gate.py` | CO-88.1 | **CO-88.3**（CO-90 F1/F2 修复 + F4：ripple 清单移出哈希体，零几何）|
| co88 记录 | `f90d65369cab92dc` | **`bf69909aa64dc494`**（rev-9 判定仍 PASS；F4 后为 (SPEC, 板) 纯函数，与无关工具文件无关）|
| `tools/p3_v57_co77_closure_declaration_sweep.py` | CO-77.2 | **CO-77.3**（F5：历史豁免改按引用判定；负控已证）|
| `tools/p3_v57_co90_nonexecutor_review_pass3.py` | CO-90.1 | **CO-90.2**（纳入 F4/F5 发现；V1 增钉 co88 稳定 sha）|
| co90 记录 | `3ba2ca0ce3966fe8` | **`897ff5cc371d135d`**（F4/F5 入册后重生成；V1..V6 全过 + co77 PASS）|
| 全链 12 件 / 其余闸 / SPEC rev-9 / 板 | — | **逐字节不变**（V1 + 快照比对确认）|

## 6. 非声明与残余
- **非声明**：不改 SPEC/板/图纸/阈值/冻结源；不声称 PDN 压降/热已闭合；不触 L1（拓扑/接口/信号流向/电源域集合/球重映射均未动）；
  V1/V6 为同代码复跑，非独立实现；F3 为口径发现，**未**放宽或重定义覆盖判据；F4/F5 为闸/记录缺陷修复，**未**放宽任何判定阈值或覆盖口径。
- **残余（均非本件可解）**：① **L1 ①**（对间净空 0.875，三硬限）待 owner 择 A/C；② PDN 压降 / 热 = NOT_DEMONSTRATED（缺输入）；
  ③ U6 GND 球 63/86 blocked 需 DS320PR1601 器件资料 + SI/PI；④ 板厂阻抗券；⑤ **F3** 网范围口径待 PM/owner（若纳入 ⇒ rev-10 全链重基线）。
