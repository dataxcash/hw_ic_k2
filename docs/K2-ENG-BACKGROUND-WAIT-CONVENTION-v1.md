# K2 · ENG · **后台等待规约**（禁自匹配轮询）· v1 · 2026-09-19

> 缘起：监理 **#K2-33**（owner 观察「ARCHER 后台运行时间过久」；监理以本会话 arm3 等待链实证）。
> 本件 = ENG 侧纠错落地（**#K2-33 §四 要求动作 + §五 验收判据**）；本笔即「下一笔提交」（§六）。

## 1. 缺陷（#K2-33 §一/§二 复述 + 本会话实证）

**禁用写法**（ENG 上轮实际使用者）：
```bash
for i in $(seq 1 60); do pgrep -f run_arm3.sh >/dev/null || break; sleep 20; done
```
`pgrep -f` 匹配**完整命令行**；轮询命令**自身**（及外层 `bash -c …`）cmdline 含该 pattern ⇒ **自匹配** ⇒ `|| break` 永不触发 ⇒ **每次白等满 60×20s = 20 分钟**（`pgrep` 只排除自己的 pid，不排除父 bash）。

## 2. 规约（ENG 强制）

1. **一律按 PID 判活**：`while [ -d /proc/$PID ]; do sleep N; done`（或 `kill -0 $PID`）；
2. 需要按 pattern 定位时，**解析一次**并在解析阶段**排除自身与全部祖先进程**，之后只查 `/proc/<pid>`；
3. **禁止** `pgrep -f <脚本名>` 轮询模式（含 `pgrep -f k2_*.py` 等同类写法）；
4. 等待器须带 `--timeout`（缺省 1h）并在退出时打印**用时**与目标 PID，便于事后审计。

## 3. 落件：`k2/tools/k2_wait_pid.sh` **`bb2803e72cd15f0e`**

```bash
# 按 PID（首选）
k2/tools/k2_wait_pid.sh --pid $BG_PID --poll 5 --timeout 3600 --label 'arm3'
# 按 pattern（解析期排除自身+祖先；之后纯 /proc 判活，结构上不可能自匹配）
k2/tools/k2_wait_pid.sh --pattern 'run_arm3\.sh' --poll 5 --timeout 3600 --label 'arm3'
```
退出码：`0` = 全部结束（含 timeout 内正常结束）；`124` = 超时仍在跑。

## 4. 验收（#K2-33 §五）—— 本会话对照实验实录

| 臂 | 命令 | 任务 | 结果 |
|---|---|---|---|
| **OLD（禁用）** | `timeout 32 bash -c 'for i in $(seq 1 60); do pgrep -f "sleep 20" >/dev/null \|\| break; sleep 2; done'` | `sleep 20` | 任务 20s 即结束，循环**仍死等**到 32s 被 `timeout` 杀 ⇒ **rc=124**；`pgrep -af` 复现命中**轮询自身**（`bash -c … pgrep -f "sleep 20" …`）❌ |
| **NEW（按 PID）** | `k2_wait_pid.sh --pid $TASK2 --poll 3` | `sleep 15` | **`用时 15s` → rc=0**：任务一结束即返回（≤1 个 poll 周期）✅ |
| **NEW2（pattern）** | `k2_wait_pid.sh --pattern 'sleep 12' --poll 3` | `sleep 12` | **`用时 12s` → rc=0**：解析期排除自身/祖先进程后纯 `/proc` 判活 ✅ |

⇒ 验收判据「任一次后台等待，在后台任务结束后 ≤20s 内轮询退出」**满足**（实测 ≤3s 粒度）。

## 5. 影响与边界

- 消除每次后台等待 **13–20 分钟**的系统性白耗（#K2-33 §三）；亦减少哨兵长静默噪声。
- 本件**只**新增 ENG 侧工具 + 本规约文档；**未改**板/SPEC/判据/`_shared`/生成器/冻结件；未派 WORKER；临时仅 `/tmp/opencode`。
