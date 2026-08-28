# Card 1.0 修复归属声明 — _shared/schlib/loader/yamlloader.py (ref,card) 泛化

> 归属声明（AGENTS.md §2.2 铁律 3：修复归属声明，先声明后动手）
> 日期：2026-08-26

## 归属
- **ECO 任务**: M13 v8 Card 1 阻塞点（阻塞解除卡）
- **修复类型**: 模型层缺口修复（非产物修复，不涉及任何 .kicad_sch/.yaml/artifacts 修改）
- **文件**: `_shared/schlib/loader/yamlloader.py`（+ 新增测试文件）
- **发现**: M-E 网表回退后全链重生成，生成器于输入解析阶段 fail-fast
  （`ValueError: Component 'U1': extra net mapping for unknown pin 'PB8'`）

## 已钉死的事实（勿重验）
1. `component.py` L32-42 fail-fast：网的引脚键不在符号引脚集 → raise。**该机制是对的，保留，禁止弱化。**
2. `yamlloader.py` 组件构建单维：`ref_nets` 跨卡并集（~L248-252）、`ref_to_sym` 同 ref 后写覆盖（~L255-262）；
   而引脚唯一性已是 (ref,card,pin) 三维（~L220-234 + `_strip_card_suffix` ~L94）——泛化做了一半。
3. 数据模型已有卡维度：网脚 @N 后缀（U1/PB8@1）、placements 带 card 字段、双符号
   （MCU_STM32G0 QFN-32 含 PB8 / MCU_STM32G0_C2 LQFP-48 无 PB8）。
4. 三版 yaml（worktree/HEAD/dfc76cb）同样崩 → 与 32 网回退无关；自 8-21 起生成器必崩，
   sch/ 产物停在 8-20 —— 此后一切门禁以真实重跑为准。

## 设计约束
1. 通用 (base_ref, card) 成分量：组件 = 每卡实例一份（自己的符号 + 自己卡域的网集）；
   卡实例解析沿用既有 @N 约定 + placements.card 字段；"card: both" 且两卡符号不同的 placement
   必须展开为逐卡解析。
2. 同 (ref,card) 出现冲突/缺失符号指派 → 明确 raise（冲突即停机），禁止静默后写覆盖、禁止猜。
3. 零 revA 特判：不得出现任何 ref 名/符号名/卡名/网名硬编码；单卡 yaml、双卡同符号等
   既有形态行为不变（向后兼容）。
4. 迭代序确定性（sorted）；输出契约写进 docstring。
5. 接口先审下游消费方，选最小且稳定变更。

## 验收（按序）
A. 单测：① 双卡同 ref 双符号正确构建两份分量 ② 单卡行为不变 ③ 真·未知引脚仍 raise
   ④ 冲突符号指派 raise ⑤ 确定性（两跑一致）
B. 既有回归：schlib/loader 相关测试套件，前后清单对照，零新增失败
C. `cd strix-halo-ioconvert/revA && python3 generate_sch_v5.py` → exit 0（仅此一步，不跑 split/ERC/gate）
D. `AppDir/sharun python3.11 -m eda_core.eco_gate.cli run ECO-S0`（生成器可跑断言复证）→ 记录输出；不 advance

## 停机报告原文
见同目录 `m13_v8_card1_stop_report.md`
