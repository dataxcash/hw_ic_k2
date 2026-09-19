#!/bin/bash
# k2_wait_pid.sh —— 后台任务等待器（**按 PID 判活**；#K2-33 §四 合规实现）
#
# 背景（#K2-33 实证）：`for i in $(seq …); do pgrep -f <脚本名> >/dev/null || break; sleep 20; done`
#   ⇒ `pgrep -f` 匹配**完整命令行**，而轮询命令**自身**（及其父 `bash -c …`）cmdline 也含该 pattern
#   ⇒ **自匹配** ⇒ `|| break` 永不触发 ⇒ 每次白等满窗（实测 60×20s = 20 分钟）。
#
# 本器做法：**先在解析阶段把 PID 定死**（解析时排除自身与全部祖先进程），之后**只查 /proc/<pid>**，
#   不再对 pattern 做任何重复匹配 ⇒ 结构上不可能自匹配。
#
# 用法：
#   k2_wait_pid.sh --pid <PID> [--pid <PID>…] [--poll 5] [--timeout 3600] [--label 名]
#   k2_wait_pid.sh --pattern '<regex>' [--poll 5] [--timeout 3600] [--label 名]
# 退出码：0 = 全部结束（含 timeout 内正常结束）；124 = 超时仍在跑（由 timeout 语义沿用）
set -u

PIDS=(); PATTERN=""; POLL=5; TIMEOUT=3600; LABEL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pid) PIDS+=("$2"); shift 2;;
    --pattern) PATTERN="$2"; shift 2;;
    --poll) POLL="$2"; shift 2;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --label) LABEL="$2"; shift 2;;
    *) echo "未知参数: $1" >&2; exit 2;;
  esac
done

ancestors() {           # 自身 + 全部祖先进程 pid（用于排除自匹配）
  echo $$
  local p=$$; local i=0
  while [ "$p" -gt 1 ] && [ "$i" -lt 64 ]; do
    p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
    [ -z "$p" ] && break
    echo "$p"; i=$((i+1))
  done
}

if [ -n "$PATTERN" ]; then
  ANC=" $(ancestors | tr '\n' ' ') "
  for pid in $(pgrep -f "$PATTERN" 2>/dev/null); do
    case "$ANC" in *" $pid "*) continue;; esac   # 排除自身/祖先进程（防自匹配）
    PIDS+=("$pid")
  done
fi

[ "${#PIDS[@]}" -eq 0 ] && { echo "[wait] ${LABEL:-任务}: 无目标 PID ⇒ 立即返回"; exit 0; }
echo "[wait] ${LABEL:-任务}: 目标 PID = ${PIDS[*]}（poll=${POLL}s, timeout=${TIMEOUT}s）"

deadline=$(( $(date +%s) + TIMEOUT ))
while :; do
  alive=()
  for pid in "${PIDS[@]}"; do [ -d "/proc/$pid" ] && alive+=("$pid"); done
  if [ "${#alive[@]}" -eq 0 ]; then
    echo "[wait] ${LABEL:-任务}: 全部结束（用时 $(( $(date +%s) - (deadline - TIMEOUT) ))s）"
    exit 0
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "[wait] ${LABEL:-任务}: 超时 ${TIMEOUT}s，仍在跑: ${alive[*]}（判 124）" >&2
    exit 124
  fi
  sleep "$POLL"
done
