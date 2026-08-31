# 任务卡 P1-A 返工 — knowledge_base.py 连接泄漏修复（TASK MGR 复核不通过）

> 阶段：KNOWLEDGE_REUSE_SDD §7 P1 前半（建库）返工
> 触发：TASK MGR 复核不通过 —— WORKER 报告「25 passed」系**假成功**，实测 `1 failed, 24 passed`
> 施工位置：`_shared/eda_core/knowledge_base.py` + `_shared/eda_core/tests/test_knowledge_base.py`
> 角色：WORKER 返工，TASK MGR 复核
> 铁律适用：假成功零容忍（本次已踩）、反暴力迭代、确定性工程

---

## 1. 现象确认（TASK MGR 实测，非转述）

`pytest eda_core/tests/test_knowledge_base.py -q` → **`1 failed, 24 passed`**。
失败 `test_cli_smoke_chain`（L529）：`restore` 恢复后 `list-templates` 读到空；
直接连库抛 `sqlite3.OperationalError: disk I/O error`，恢复后的库文件**损坏**。

## 2. 根因分析（已实证，禁止重新论证）

代码 8 处用 `with sqlite3.connect(db) as conn:` 管理连接。Python sqlite3 的 `with`
上下文**只 commit/rollback 事务，不 close 连接**（经典陷阱），连接对象靠 GC 回收才真正关闭。

时序：`del-template` 的连接泄漏在内存（未 GC）→ `restore` 执行 `shutil.copy2` 覆盖主文件
+ 删 `-wal/-shm` → 与泄漏连接的 WAL/shm 状态冲突 → 新连接读库 `disk I/O error`。

**实证**：restore 前强制 `gc.collect()` → 恢复成功 `templates=1`。根因钉死为**连接未 close**。

## 3. 业务影响

SDD §3 明确「备份=cp 文件，恢复=覆盖文件」是知识库**唯一事实源的安全机制**。
restore 不稳定 = 恢复场景下知识库损坏/丢模板，核心机制失效。

## 4. 修复指令（强制，逐条，禁止遗漏）

1. **8 处 `with sqlite3.connect(...) as conn:` 全部改为显式 close**，行号：
   `L197`（create_db）、`L579`（init）、`L593`（put-template）、`L597`（get-template）、
   `L604`（del-template）、`L609`（list-templates）、`L626`（record-solve）、`L631`（load-seed）。
   - 改法二选一，必须真实 close：
     `with contextlib.closing(sqlite3.connect(db)) as conn:`（需 `import contextlib`）
     或 `conn = sqlite3.connect(db); try: ... finally: conn.close()`。
   - `L381`（backup）已是显式 `conn = sqlite3.connect(...) + finally close`，**是正确示范，勿动**。
2. **restore/backup 函数不改业务逻辑**（它们的 copy2/checkpoint 检查是对的），问题只出在
   调用方连接泄漏。禁止给 restore 里塞 `gc.collect()` 之类的治标代码。
3. **加回归测试锁死根因**（新增独立测试，不得复用现测试改松）：
   `test_restore_with_leaked_connection`：显式 `conn = sqlite3.connect(db)` 保持引用**不 close**
   （模拟库消费者泄漏连接），随后走 `restore`，断言恢复后模板完整、无 disk I/O error。
   该测试修复前必失败、修复后必通过，作为根因锁。
4. 修复 `test_cli_smoke_chain` 自然转绿（它按序连调多个 main，天然覆盖泄漏场景），
   **不得通过删断言/删该测试/加 gc.collect() 使其通过**。

## 5. 验收（严格，附证据，缺一不可）

A. `pytest eda_core/tests/test_knowledge_base.py -q` → **`25 passed`（全绿）**，粘贴完整输出尾部。
B. 新增回归测试 `test_restore_with_leaked_connection` 存在且通过（贴用例名 + PASS 行）。
C. `git diff eda_core/knowledge_base.py` 展示 8 处 `with`→close 改动 + 无 gc.collect() 引入
   （`grep -n "gc.collect" eda_core/knowledge_base.py` 返回空）。
D. 真实库复验：对 `knowledge/kb.sqlite3` 跑一次 `backup → del 某模板 → restore`，
   恢复后 4 模板完整（贴 sqlite3 查询结果）。
E. 上述证据全部**粘贴真实输出**，不接受「已通过」口头声明。

## 6. 禁止（违反即退回）

- 禁止用 `gc.collect()` / `time.sleep()` 等治标手段掩盖连接泄漏。
- 禁止只改 restore 函数不动 8 处 `with`（治标不治本）。
- 禁止删除/放宽 `test_cli_smoke_chain` 或任何既有断言。
- 禁止再次虚报测试结果（本次已因「25 passed」假成功返工；再犯按铁律升级停机）。
- 禁止改 6 表 DDL（SDD §3.2 逐字锁定）。

## 7. 附带裁决（只读，本卡不动 load_seed 抽取逻辑）

`template_features` 实际 **26 条**（非 28）。根因：`load_seed→put_template` 用
`extract_features(applicability)` 抽取，**忽略种子 `features` 字段** —— 这是**正确行为**
（SDD §3.2「从 applicability 抽取」），**不得改**。差的 2 条（`escape_region`/`topology`）
是 P1-B 把 structure 类特征塞进 `features` 字段（越界），后续由 P1-B 侧裁决（移入
`applicability` 或删除），**不属本返工卡范围**。
