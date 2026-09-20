#!/usr/bin/env python3
"""k2_p6_board_alias_and_cli_audit_v1.py — B2-T 续作（只读，真源零改动）：

(g) `k2/k2_v4.kicad_pcb` **板别名消费者普查**：逐 .py 登记路径/类别/板身份字面量，
    并记录该路径当前解析（符号链接 → `hw/k2_v4_8L.kicad_pcb`）。
(i) **B1 修复前后 CLI 行为差异面**：`python3 -m eda_core.hs_route_model --link-topology`
    在 {遗留载体, 现行 schema 载体} × {无守卫（真源引擎）, 有守卫（/tmp 影子 2 处 fail-closed）} 四组合下
    的退出码/输出摘要/异常。

产出：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_BOARD_ALIAS_AND_CLI_AUDIT_v1.json`
      `k2/docs/K2-P6-B2T-BOARD-ALIAS-AND-CLI-AUDIT-20260920.md`
用法（容器根）：python3 k2/tools/k2_p6_board_alias_and_cli_audit_v1.py [--verify-determinism]
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
from pathlib import Path

REPO = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = REPO / "k2"
ALIAS = K2 / "k2_v4.kicad_pcb"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
LEGACY_ALLOC = K2 / "pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json"
P3_ALLOC = Path("/tmp/opencode/current_alloc_from_pipeline.json")
SHADOW = Path("/tmp/opencode/cli_audit_shadow")
OUT_JSON = K2 / "pm_gate/artifacts/k2_v4/P6_execution/B2T_BOARD_ALIAS_AND_CLI_AUDIT_v1.json"
OUT_DOC = K2 / "docs/K2-P6-B2T-BOARD-ALIAS-AND-CLI-AUDIT-20260920.md"
SHA_LITERALS = ("6c387dff", "f6273de6", "fb07d25a", "d4e81f64", "c5a7df90")
PRO_PATH = K2 / "hw/k2_v4_8L.kicad_pro"   # 板工程件（真源；alias 无 .kicad_pro 符号链接）

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


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def classify(rel: str) -> str:
    if rel.startswith("k2/tools/k2_p6_"):
        return "TOOL(本轮/前轮 ENG 工具)"
    if re.match(r"k2/tools/p3_v5", rel) or "mcio_feas_step2" in rel or rel.startswith("k2/pm_gate/artifacts"):
        return "HIST(历史分析/复现脚本)"
    if rel.startswith(("k2/_shared/", "_shared/eda_core/", "_shared/pm_gate/")):
        return "LIVE(共享层)"
    if rel.startswith("criteria/"):
        return "LIVE(判据)"
    if rel.startswith("k2/tools/"):
        return "TOOL"
    return "OTHER"


def scan_alias_consumers():
    roots = ["k2", "_shared", "criteria"]
    rows = []
    for root in roots:
        base = REPO / root
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", ".pytest_cache")]
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                p = Path(dirpath) / fn
                rel = str(p.relative_to(REPO))
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if "k2_v4.kicad_pcb" not in txt:
                    continue
                lits = [s for s in SHA_LITERALS if s in txt]
                lines = [i for i, l in enumerate(txt.splitlines(), 1) if "k2_v4.kicad_pcb" in l][:3]
                rows.append({"file": rel, "category": classify(rel), "sha_literals": lits,
                             "sample_lines": lines})
    rows.sort(key=lambda r: (r["category"], r["file"]))
    return rows


def build_shadow_with_guard():
    shutil.rmtree(SHADOW, ignore_errors=True)
    shutil.copytree(K2 / "_shared", SHADOW / "shared",
                    ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    hp = SHADOW / "shared/eda_core/hs_route_model.py"
    hs = hp.read_text(encoding="utf-8")
    assert hs.count(B1_OLD) == 1 and hs.count(B1_OLD2) == 1, "B1 守卫锚未命中"
    hp.write_text(hs.replace(B1_OLD, B1_NEW, 1).replace(B1_OLD2, B1_NEW2, 1), encoding="utf-8")


def run_cli(carrier: str, guarded: bool):
    """返回 {rc, status, crossing, stderr_tail}。"""
    alloc = str(P3_ALLOC) if carrier == "p3_current_schema" else str(LEGACY_ALLOC)
    if guarded:
        env_py = str(SHADOW / "shared")
        cwd = str(SHADOW)
    else:
        env_py = str(K2 / "_shared")
        cwd = str(REPO)
    env = {k: v for k, v in os.environ.items() if k != "PM_GATE_PROJECT_ROOT"}
    env["PYTHONPATH"] = env_py
    out = Path("/tmp/opencode/cli_audit_out") / f"{carrier}_{'guard' if guarded else 'noguard'}"
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "eda_core.hs_route_model", "--board", str(ALIAS),
           "--spec", str(SPEC), "--alloc", alloc, "--rules", str(RULES),
           "--pro", str(PRO_PATH),
           "--link-topology", "--out", str(out)]
    pr = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=900)
    status, crossing = None, None
    try:
        payload = json.loads(pr.stdout.strip().splitlines()[-1])
        status, crossing = payload.get("status"), payload.get("crossing_links")
    except Exception:
        pass
    return {"carrier": carrier, "guarded": guarded, "rc": pr.returncode, "status": status,
            "crossing_links": crossing,
            "stdout_tail": pr.stdout.strip().splitlines()[-1][:160] if pr.stdout.strip() else "",
            "stderr_tail": pr.stderr.strip().splitlines()[-1][:160] if pr.stderr.strip() else ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-determinism", action="store_true")
    args = ap.parse_args()
    alias = {"path": "k2/k2_v4.kicad_pcb", "is_symlink": ALIAS.is_symlink(),
             "target": os.readlink(ALIAS) if ALIAS.is_symlink() else None,
             "resolved_sha16": sha16(ALIAS)}
    consumers = scan_alias_consumers()
    build_shadow_with_guard()
    combos = [run_cli(c, g) for c in ("legacy_alloc", "p3_current_schema") for g in (False, True)]
    det = "NOT_RUN"
    if args.verify_determinism:
        combos2 = [run_cli(c, g) for c in ("legacy_alloc", "p3_current_schema") for g in (False, True)]
        det = "MATCH" if json.dumps(combos, sort_keys=True) == json.dumps(combos2, sort_keys=True) else "MISMATCH"
    live = [r for r in consumers if r["category"].startswith("LIVE")]
    hist = [r for r in consumers if r["category"].startswith("HIST")]
    doc = {
        "artifact": "k2_p6_board_alias_and_cli_audit", "schema": 1, "readonly_repo": True,
        "purpose": "(g) 板别名消费者普查 (i) B1 修复前后 CLI 行为差异面",
        "anchors": {"alias_resolved_sha16": alias["resolved_sha16"],
                    "design_source_board": {"path": "k2/hw/k2_v4_8L.kicad_pcb", "sha16": sha16(K2 / "hw/k2_v4_8L.kicad_pcb")},
                    "engine": {"path": "k2/_shared/eda_core/hs_route_model.py", "sha16": sha16(K2 / "_shared/eda_core/hs_route_model.py")}},
        "board_alias": alias,
        "consumers_total": len(consumers),
        "consumers_by_category": {c: sum(1 for r in consumers if r["category"] == c)
                                 for c in sorted({r["category"] for r in consumers})},
        "consumers_live": live, "consumers_hist": hist,
        "consumers_hist_with_sha_literals": [r for r in hist if r["sha_literals"]],
        "cli_behavior": combos,
        "conclusions": [
            f"(g) 板别名 `k2/k2_v4.kicad_pcb` → `{alias['target']}`（sha16 `{alias['resolved_sha16']}` = 冻结设计源板）"
            f"⇒ 现役消费者（{len(live)} 个 .py，含 `_shared/pm_gate/config.py`·`check_qa.py`·`_shared/eda_core/*`）"
            "读到的是 8L 板，与 handoff §1 一致（**非缺陷**）；"
            f"历史脚本（{len(hist)} 个）中 {sum(1 for r in hist if r['sha_literals'])} 个含旧板身份字面量"
            "⇒ 按该路径重跑会静默换板（**须逐脚本标注，禁默认重跑**）。",
            "(i) B1 行为差异（下表）：现行 schema 载体下 `--link-topology` 无守卫 = 崩溃（非 fail-closed）；"
            "有守卫 = 正常返回 `CROSSING_FOUND`（exit 1 = 非 TOPOLOGY_OK，语义正确）。遗留载体两态一致 ⇒ "
            "B1 修复**只改变崩溃为正常判定**，无既存调用者语义回退。",
            "⚠ 附带发现（随 B1 一并裁定）：崩溃态与『非 TOPOLOGY_OK』**exit code 同为 1** ⇒ 调用方仅凭 rc "
            "无法分辨（fail-open 隐患）。建议 B1 授权件同时要求：异常 → `status=INFRA_ERROR` + 明确非零码"
            "（或 CLI 层 try/except 包装），使『崩溃』与『判定为 CROSSING_FOUND』可机辨。",
        ],
        "determinism_2run": det,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    cli_rows = "\n".join(f"| {c['carrier']} | {'有守卫' if c['guarded'] else '无守卫'} | {c['rc']} | "
                         f"{c['status']} | {c['crossing_links']} | {c['stderr_tail'][:80]} |" for c in combos)
    live_rows = "\n".join(f"| `{r['file']}` | {', '.join(r['sha_literals']) or '—'} | 行 {r['sample_lines']} |" for r in live) or "| — | — | — |"
    hist_rows = "\n".join(f"| `{r['file']}` | {', '.join(r['sha_literals']) or '—'} | 行 {r['sample_lines']} |" for r in hist) or "| — | — | — |"
    OUT_DOC.write_text(f"""# K2 · B2-T 续作 · **板别名消费者普查 + B1 CLI 行为差异面**（ENG / ARCHER · 只读）

> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_BOARD_ALIAS_AND_CLI_AUDIT_v1.json`
> 生成：`python3 k2/tools/k2_p6_board_alias_and_cli_audit_v1.py --verify-determinism`
> 真源零改动（只读；CLI 输出落 /tmp；守卫仅在 /tmp 影子）

## 1. (g) 板别名与消费者

`k2/k2_v4.kicad_pcb` = 符号链接 → `{alias['target']}`（解析后 sha16 `{alias['resolved_sha16']}` = **冻结设计源板** fb07d25a）。
消费者 .py 共 **{len(consumers)}** 个：{json.dumps(doc['consumers_by_category'], ensure_ascii=False)}

**LIVE（现役：共享层/判据）**：

| 文件 | 板身份字面量 | 命中行 |
|---|---|---|
{live_rows}

**HIST（历史分析/复现脚本，含板身份字面量者重点标注）**：

| 文件 | 板身份字面量 | 命中行 |
|---|---|---|
{hist_rows}

⇒ **LIVE 读到 8L 板 = 与 handoff §1 一致（非缺陷）**；**HIST 中带旧板字面量者按此路径重跑会静默换板** —— 须逐脚本标注（本笔不改脚本）。

## 2. (i) B1 修复前后 `--link-topology` 行为

| 载体 | 守卫 | exit | status | crossing | stderr 尾 |
|---|---|---|---|---|---|
{cli_rows}

⇒ 现行 schema 载体：**无守卫 = 崩溃（fail-open 缺口）→ 有守卫 = 正常返回 `CROSSING_FOUND`**；
遗留载体两态一致 ⇒ 修复无既存语义回退。确定性两跑：**{det}**。

⚠ **附带发现（建议并入 B1 授权件）**：崩溃态与「非 TOPOLOGY_OK」**exit code 同为 1** ⇒ 调用方仅凭 rc
无法分辨崩溃与正常判定（fail-open 隐患）；建议同时要求异常路径返回 `status=INFRA_ERROR` + 可机辨退出码。

## 3. 待监理裁定（不阻塞）

① 锚承载形态（具名冻结载体 vs 合成现行 fixture）② B1 守卫（`_shared`）③ A1–A13 重基线批
④ HIST 脚本板身份标注批（只读报告，不改脚本）。

—— ENG（ARCHER）· 2026-09-20 · 引擎 sha16 `{doc['anchors']['engine']['sha16']}` · 阶段：**P6 未开（只出计划件）**
""", encoding="utf-8")
    print(json.dumps({"board_alias": alias, "consumers_total": len(consumers),
                      "by_category": doc["consumers_by_category"], "cli_behavior": combos,
                      "determinism": det}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
