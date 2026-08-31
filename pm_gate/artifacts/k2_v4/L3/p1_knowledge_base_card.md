# 任务卡 P1-A — knowledge_base.py 建库（SQLite 单文件案例库）

> 阶段：KNOWLEDGE_REUSE_SDD §7 P1 前半（建库）
> 施工位置：`_shared`（公共层，零单板特判）
> 角色：WORKER 施工，TASK MGR 复核
> 与 P1-B 并行，无数据依赖（双方锚定同一 SDD，合并点见「合并接口」）

## 目标

新建 `_shared/eda_core/knowledge_base.py`，实现 SQLite 单文件案例库的建库 + 读写接口，
产物 `_shared/knowledge/kb.sqlite3`。schema 已由 SDD §3.2 定稿（6 表），本卡照图施工，不设计。

## 权威输入（按序读）

1. `_shared/docs/KNOWLEDGE_REUSE_SDD.md` §3（数据库设计，DDL 已写死）+ §4（五段 JSON 结构）
2. `_shared/docs/EDA_EXT_SDD.md`（北极星，理解层 2 定位）

## 已钉死事实（勿重新论证）

- schema = 6 表，DDL 见 SDD §3.2：`templates` / `template_features` / `sources` / `boards` / `board_templates` / `solves`
- 单文件 `_shared/knowledge/kb.sqlite3` + WAL；备份 = `PRAGMA wal_checkpoint(TRUNCATE)` 后 `cp`；恢复 = 覆盖文件
- 零外部依赖：只用 Python 标准库 `sqlite3`，无 ORM、无第三方包
- 五段 JSON 严格分离：`applicability`(客观事实) / `structure`(经验形态) / `params`(变量) / `validation`(证据) / `provenance`(来源)
- 检索维度抽列：`applicability` 里供检索的字段（connector/pad_columns/diff_pairs/layer…）额外落 `template_features` 建索引

## 设计约束

1. 零外部依赖（`import sqlite3` 即止），零单板特判（K2 板名/坐标不得硬编码进模型）
2. 6 表 DDL 严格照 SDD §3.2；`PRAGMA journal_mode=WAL`
3. 读写接口（库 + CLI 双用）：建库、模板 CRUD、feature 抽取（applicability→template_features）、备份/恢复、solves 记录写入
4. 迭代序确定性（sorted）；输出契约写进 docstring
5. 严禁把设计决策伪装成 applicability 塞模板（数据 vs 决策红线）

## 合并接口（与 P1-B 的接缝）

提供 `load_seed(seed_json)` 入口：吞入 P1-B 产出的五段 JSON 种子数据 → 落 `templates` + `template_features`（+ `sources`/`boards` 如种子内含）。种子 JSON 是**一次性导入源**，落库后失效，不作为长期事实源。

## 验收（按序）

A. 建库成功，6 表齐全（`PRAGMA table_info` 校验）
B. 插入一个样例模板 → 可查询；applicability 特征自动抽取落 `template_features` 正确
C. 备份→恢复闭环：wal_checkpoint 后 cp 文件，覆盖恢复后数据一致
D. 单测 `pytest _shared/eda_core/tests/test_knowledge_base.py` 全绿
E. 零第三方依赖（文件头仅标准库；无新增 pip 包）

## 禁止

- 不得用 ORM/SQLAlchemy；不得引入任何 pip 依赖
- 不得散落 markdown/json 作知识事实源（唯一事实源 = kb.sqlite3）
- 不得写死 K2 任何板名/坐标/模板内容
