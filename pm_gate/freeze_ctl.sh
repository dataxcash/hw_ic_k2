#!/bin/bash
# freeze_ctl.sh — 宪法冻结区锁管理（EXECUTION_PROCESS.md §5 解锁通道）
# 用法: freeze_ctl.sh {lock|unlock|status}
#   lock   冻结区全锁(文件444+目录555) — 默认态
#   unlock 冻结区解锁(git 操作/立法修订前) — 完成后必须 lock
#   status 显示冻结区写位状态
# 冻结清单与 guard_constitution.py / EXECUTION_PROCESS.md 同步维护。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"   # ic_hw 容器根
DIRS="
_shared/docs
_shared/eda_core
_shared/knowledge
k2/pm_gate/artifacts/k2_v4/L1/frozen
k2/pm_gate/artifacts/k2_v4/L2/frozen
"
FILES="
k2/pm_gate/EXECUTION_PROCESS.md
k2/pm_gate/EXECUTION_GATES.md
k2/k2_v4.kicad_pcb
"
cd "$ROOT" || exit 1
case "${1:-}" in
  lock)
    for d in $DIRS; do
      [ -d "$d" ] && find "$d" -type f -exec chmod 444 {} + 2>/dev/null
      [ -d "$d" ] && find "$d" -type d -exec chmod 555 {} + 2>/dev/null
    done
    for f in $FILES; do [ -f "$f" ] && chmod 444 "$f" 2>/dev/null; done
    echo "locked: 冻结区 444/555"
    ;;
  unlock)
    for d in $DIRS; do
      [ -d "$d" ] && chmod -R u+w "$d" 2>/dev/null
    done
    for f in $FILES; do [ -f "$f" ] && chmod u+w "$f" 2>/dev/null; done
    echo "unlocked: 冻结区可写(git/修订用) — 完成后请 lock"
    ;;
  status)
    nf=$(find $DIRS -type f -perm /222 2>/dev/null | wc -l)
    nd=$(find $DIRS -type d -perm /222 2>/dev/null | wc -l)
    ff=0; for f in $FILES; do [ -f "$f" ] && [ -w "$f" ] && ff=$((ff+1)); done
    echo "带写位文件=$nf 带写位目录=$nd 顶层文件可写=$ff (0/0/0 = 全锁)"
    ;;
  *) echo "用法: freeze_ctl.sh {lock|unlock|status}"; exit 1;;
esac