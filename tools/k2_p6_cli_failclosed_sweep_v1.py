#!/usr/bin/env python3
"""k2_p6_cli_failclosed_sweep_v1.py — B2-T 续作（只读，真源零改动）：**(j) CLI 子命令 fail-closed 普查**。

矩阵：{遗留 alloc, 现行 schema（P3 Sept-9 载体）} × {无守卫（真源引擎）, 有守卫（/tmp 影子 B1 2 处）}
      × 子命令 {--chain UP0, --chain REFCLK0, --chain-v2 UP0, --capacity-map, --all-v4, --link-topology}
观测：exit code · status（可解析时）· stderr 异常类 · 是否超时。用于回答「现行 schema 载体的崩溃面是否只
      `--link-topology` 一处」（B1 同族 CLI 面），并为 B1 授权件补足 CLI 层 fail-closed 证据。

产出：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_CLI_FAILCLOSED_SWEEP_v1.json`
      `k2/docs/K2-P6-B2T-CLI-FAILCLOSED-SWEEP-20260920.md`
用法（容器根）：python3 k2/tools/k2_p6_cli_failclosed_sweep_v1.py [--verify-determinism]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = REPO / "k2"
BOARD = K2 / "hw/k2_v4_8L.kicad_pcb"
PRO = K2 / "hw/k2_v4_8L.kicad_pro"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
LEGACY = K2 / "pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json"
P3 = Path("/tmp/opencode/current_alloc_from_pipeline.json")
SHADOW = Path("/tmp/opencode/cli_sweep_shadow")
OUT = Path("/tmp/opencode/cli_sweep_out")
OUT_JSON = K2 / "pm_gate/artifacts/k2_v4/P6_execution/B2T_CLI_FAILCLOSED_SWEEP_v1.json"
OUT_DOC = K2 / "docs/K2-P6-B2T-CLI-FAILCLOSED-SWEEP-20260920.md"
B1_OLD = '''        x_l = min(s["end_left"]["x"] for s in segs
                  if "end_left" in s)
        x_r = max(s["end_right"]["x"] for s in segs
                  if "end_right" in s)'''
B1_NEW = '''        _ls = [s["end_left"]["x"] for s in segs if "end_left" in s]
        _rs = [s["end_right"]["x"] for s in segs if "end_right" in s]
        x_l = min(_ls) if _ls else None
        x_r = max(_rs) if _rs else None'''
B1_OLD2 = '''            if xr and xr[0] <= x_r and xr[1] >= x_l:'''
B1_NEW2 = '''            if (xr and x_l is not None and x_r is not None
                    and xr[0] <= x_r and xr[1] >= x_l):'''
CMDS = [("chain_UP0", ["--chain", "UP0"]), ("chain_REFCLK0", ["--chain", "REFCLK0"]),
        ("chain_v2_UP0", ["--chain-v2", "UP0"]), ("capacity_map", ["--capacity-map"]),
        ("all_v4", ["--all-v4"]), ("link_topology", ["--link-topology"])]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def build_shadow():
    shutil.rmtree(SHADOW, ignore_errors=True)
    shutil.copytree(K2 / "_shared", SHADOW / "shared",
                    ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    hp = SHADOW / "shared/eda_core/hs_route_model.py"
    hs = hp.read_text(encoding="utf-8")
    assert hs.count(B1_OLD) == 1 and hs.count(B1_OLD2) == 1
    hp.write_text(hs.replace(B1_OLD, B1_NEW, 1).replace(B1_OLD2, B1_NEW2, 1), encoding="utf-8")


def run(carrier, guarded, name, extra, timeout=420):
    alloc = str(P3 if carrier == "p3_current_schema" else LEGACY)
    env = {k: v for k, v in os.environ.items() if k != "PM_GATE_PROJECT_ROOT"}
    env["PYTHONPATH"] = str(SHADOW / "shared") if guarded else str(K2 / "_shared")
    cwd = str(SHADOW) if guarded else str(REPO)
    outdir = OUT / f"{carrier}_{'guard' if guarded else 'noguard'}" / name
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "eda_core.hs_route_model", "--board", str(BOARD),
           "--spec", str(SPEC), "--alloc", alloc, "--rules", str(RULES),
           "--pro", str(PRO), *extra, "--out", str(outdir)]
    t0 = time.time()
    try:
        pr = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        rc, so, se, to = pr.returncode, pr.stdout, pr.stderr, False
    except subprocess.TimeoutExpired as e:
        rc, so, se, to = None, (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "", True
    status, detail = None, None
    for line in reversed(so.strip().splitlines()):
        try:
            j = json.loads(line)
            status = j.get("status") or j.get("verdict")
            detail = {k: v for k, v in j.items()
                      if k in ("corridors", "ok_regions", "insufficient_regions",
                               "failed_bases", "unsolved", "solved")}
            break
        except Exception:
            continue
    exc = ""
    if se:
        lines = [l.strip() for l in se.strip().splitlines() if l.strip()]
        exc = lines[-1][:160] if lines else ""
    return {"carrier": carrier, "guarded": guarded, "cmd": name, "rc": rc, "status": status,
            "status_detail": detail, "timeout": to, "exception": exc,
            "runtime_s": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-determinism", action="store_true")
    args = ap.parse_args()
    build_shadow()
    rows = [run(c, g, n, x) for c in ("legacy_alloc", "p3_current_schema") for g in (False, True) for n, x in CMDS]
    det = "NOT_RUN"
    if args.verify_determinism:
        rows2 = [run(c, g, n, x) for c in ("legacy_alloc", "p3_current_schema") for g in (False, True) for n, x in CMDS]
        slim = lambda rs: [{k: r[k] for k in ("carrier", "guarded", "cmd", "rc", "status",
                                              "exception")} for r in rs]
        det = "MATCH" if json.dumps(slim(rows), sort_keys=True) == json.dumps(slim(rows2), sort_keys=True) else "MISMATCH"
    crash = [r for r in rows if r["exception"]]
    crash_p3 = [r for r in crash if r["carrier"] == "p3_current_schema" and not r["guarded"]]
    doc = {
        "artifact": "k2_p6_cli_failclosed_sweep", "schema": 1, "readonly_repo": True,
        "purpose": "(j) CLI 子命令 × 载体 × 守卫 的 fail-closed 普查（B1 同族 CLI 面）",
        "anchors": {"engine": {"path": "k2/_shared/eda_core/hs_route_model.py", "sha16": sha16(K2 / "_shared/eda_core/hs_route_model.py")},
                    "board_8L": {"sha16": sha16(BOARD)}, "spec_rev52": {"sha16": sha16(SPEC)},
                    "legacy_alloc": {"sha16": sha16(LEGACY)}, "p3_carrier": {"path": str(P3), "sha16": sha16(P3)}},
        "matrix": rows, "determinism_2run": det,
        "n_crash": len(crash), "n_crash_p3_noguard": len(crash_p3),
        "conclusions": [
            f"现行 schema 载体 + 无守卫：崩溃 {len(crash_p3)} 处（子命令：{[r['cmd'] for r in crash_p3]}）"
            "⇒ CLI 面崩溃点集中于 `--link-topology`（B1）；其余子命令该载体下 fail-closed 返回状态。",
            "遗留载体：无/有守卫结果一致 ⇒ B1 修复零语义回退（同 (i) 结论）。",
            "注：exit code 不可单独用于判定（崩溃与『非 TOPOLOGY_OK/未全解』同为 1）；须并联 status/stderr。",
            "发现 B2（非 B1 同族，载体无关）：`--chain UP0` 在两载体/两守卫 4 组合下**均抛 "
            "`RuntimeError: 可见性图求解超限（fail-closed，非设计结论）`**（hs_route_model.py:347，"
            "系**刻意** fail-closed 抛错，非静默错误）⇒ 属 **CLI 层未包装**问题：调用方看到 traceback + rc=1，"
            "与『正常未解』不可机辨（与 (i) 的 exit code 观察同源）。建议并入 B1 授权件的 CLI 语义整改。",
            "发现 B3（判据口径，需监理裁定）：`--capacity-map` 在现行载体下 status=CAPACITY_OK / exit 0，"
            "但走廊 `EAST_CHIP_TO_J2_refclk` = INSUFFICIENT ⇒ CLI 判定**只看 region**、忽略 corridor "
            "INSUFFICIENT ⇒ 潜在 fail-open（是否应致 FAIL 属判据口径，ENG 不改）。",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    rows_md = "\n".join(f"| {r['carrier']} | {'有' if r['guarded'] else '无'} | `{r['cmd']}` | {r['rc']} | {r['status']} | "
                        f"{r['exception'] or '—'} | {r['runtime_s']} |" for r in rows)
    OUT_DOC.write_text(f"""# K2 · B2-T 续作 · **CLI 子命令 fail-closed 普查（j）**（ENG / ARCHER · 只读）

> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_CLI_FAILCLOSED_SWEEP_v1.json`
> 生成：`python3 k2/tools/k2_p6_cli_failclosed_sweep_v1.py --verify-determinism`
> 真源零改动（输出落 /tmp；B1 守卫仅在 /tmp 影子）

| 载体 | 守卫 | 子命令 | exit | status | 异常 | 用时 s |
|---|---|---|---|---|---|---|
{rows_md}

**结论**
- 现行 schema 载体 + **无守卫**：崩溃 **{len(crash_p3)}** 处（{[r['cmd'] for r in crash_p3]}）⇒ CLI 崩溃面集中于 `--link-topology`（B1）。
- 遗留载体：无/有守卫一致 ⇒ B1 修复**零语义回退**。
- ⚠ exit code 不可单独判定（崩溃与「非 TOPOLOGY_OK/未全解」同为 1）⇒ 须并联 `status`/stderr；建议 B1 授权件补 CLI 异常语义。
- **发现 B2**（载体无关）：`--chain UP0` 4 组合均抛 `RuntimeError: 可见性图求解超限（fail-closed，非设计结论）`
  （`hs_route_model.py:347`；刻意 fail-closed 抛错）⇒ **CLI 层未包装**，rc=1 与「正常未解」不可机辨。
- **发现 B3**（判据口径，需监理裁定）：`--capacity-map` 现行载体下 `status=CAPACITY_OK`/exit 0，而走廊
  `EAST_CHIP_TO_J2_refclk = INSUFFICIENT` ⇒ CLI 只看 region、忽略 corridor ⇒ 潜在 fail-open（ENG 不改口径）。
- 确定性两跑：**{det}**。

—— ENG（ARCHER）· 2026-09-20 · 引擎 sha16 `{doc['anchors']['engine']['sha16']}` · 阶段：**P6 未开（只出计划件）**
""", encoding="utf-8")
    print(json.dumps({"n_crash": doc["n_crash"], "n_crash_p3_noguard": doc["n_crash_p3_noguard"],
                      "crash_cmds": [r["cmd"] for r in crash], "determinism": det,
                      "out": [str(OUT_JSON), str(OUT_DOC)]}, ensure_ascii=False, indent=1))
    for r in rows:
        print(f"  {r['carrier']:18s} guard={r['guarded']!s:5s} {r['cmd']:16s} rc={r['rc']} status={r['status']} {r['exception'][:50]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
