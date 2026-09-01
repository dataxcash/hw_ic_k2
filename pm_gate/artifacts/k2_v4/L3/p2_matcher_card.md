# 任务卡 P2-A — 匹配器 matcher.py（特征 → SQL 检索 → 命中模板）

> 阶段：KNOWLEDGE_REUSE_SDD §7 P2 前半（匹配器最小可用）
> 施工位置：`_shared/eda_core/matcher.py`（公共层，零单板特判）
> 角色：WORKER 施工，TASK MGR 复核
> 与 P2-B 并行，接口契约 = 特征 dict（字段名/值格式见「接口契约」），双方锚定同一契约

## 目标

新建 `_shared/eda_core/matcher.py`：输入「特征 dict」→ 查 `template_features` 表 → 返回命中模板列表（按匹配度排序）。这是"拓扑特征匹配，不是关键词搜索"（SDD §5）。

## 权威输入（按序读）

1. `_shared/docs/KNOWLEDGE_REUSE_SDD.md` §2/§4/§5（匹配器定位 + produced 红线 + 聪明查询本质）
2. `_shared/eda_core/knowledge_base.py`（复用其 `get_template`/连接管理；特征抽取规则 `extract_features` 即 `str(v)` 字符串化）
3. `knowledge/kb.sqlite3`（已落库：4 模板 + 26 条 `template_features`，`idx_feat_kv` 索引已建）

## 已钉死事实（勿重新论证）

- `template_features` 表 26 条已就绪，`feature_key`/`feature_value`（TEXT 字符串化）已建 `idx_feat_kv(feature_key, feature_value)` 索引
- 特征值字符串化规则 = `str(v)`（`2 → '2'`、`1.35 → '1.35'`、`True → 'True'`），沿用 `knowledge_base.extract_features`
- 已落库 4 模板 produced 状态：conn_escape_slimsas_x8 / conn_escape_mcio / corridor_pair_dual_band = `produced=true`；cap_wall_ac = `produced=false`

## 设计约束

1. 零外部依赖（仅标准库），零 K2 硬编码（板名/坐标/连接器名不得写死进 matcher.py）
2. 匹配策略 = 特征交集评分（非关键词、非模糊搜索）：输入特征 dict 的每个 key-value 与
   `template_features` 表比对，命中条数越多分越高；输出按分数降序 + template_id 升序（确定性）
3. 部分匹配降级：输入只给部分特征（如仅 `connector`）也能命中（靠交集评分），不要求全字段匹配
4. 零匹配 → 返回空列表（禁止瞎猜/兜底返回无关模板）
5. **produced 红线**：命中结果必须带 `produced` 标志，`produced=false`（cap_wall_ac）标记为
   「候选参考 candidate」，`produced=true` 标记「确定解法 verified」；匹配器只输出标记，不下发施工
6. 迭代序确定性（sorted）；输出契约写进 docstring

## 接口契约（与 P2-B 对齐，禁止另立字段名）

- 输入：特征 dict，值允许标量（int/float/str/bool），字段名必须是以下已落库字段之一（26 条来源）：
  `connector` `pad_columns` `pad_pitch_x` `diff_pairs` `layer` `signal_count`
  `escape_side` `redriver` `cap_count` `cap_per_diff_pair` `footprint` `cap_value_nf`
  `band_layout` `refclk_pairs` `bands` `pairs_per_band` `refclk_layer` `corridor_count`
- 输出：`[{template_id, category, name, score, matched_fields, produced, produced_label}, ...]`
  （`score` = 命中条数，`matched_fields` = 命中的 key 列表，`produced_label` = verified/candidate）

## 验收（按序）

A. 单测：① K2 完整特征（connector=SlimSAS_x8_SFF8654 等）→ 命中 conn_escape_slimsas_x8 为 top1
   ② 部分特征（仅 connector=...）→ 仍命中且排序正确 ③ 无匹配特征 → 空列表 ④ cap_wall_ac 命中 → produced_label=candidate
   ⑤ 确定性（两跑一致）⑥ 值字符串化规则正确（int/float/bool）
B. 真实库闭环：对 `knowledge/kb.sqlite3` 用 4 组已知特征反查，各自命中自己模板（贴输出）
C. `pytest` 全绿 + 粘贴输出；零新增 pip 依赖
D. 零 K2 硬编码（grep 板名/坐标/连接器名 → 空）

## 禁止

- 禁止把 produced=false 模板当确定解法返回（红线）
- 禁止关键词/字符串模糊搜索冒充"拓扑特征匹配"
- 禁止写死 K2 板名/坐标/连接器名
- 禁止引入第三方包
