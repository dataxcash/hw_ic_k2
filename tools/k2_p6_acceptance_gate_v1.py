#!/usr/bin/env python3
"""k2_p6_acceptance_gate_v1.py — 批 2 **变更后验收门**（fail-closed，一条命令）。

三腿齐备中的第三腿：① 仪器自检 `k2_p6_instruments_selfcheck_v1.py`（锚在否）
② 变更前影子预验证 `k2_p6_shadow_verify_v1.py`（补丁集可行否）③ **本器 = 变更后验收**。

检查项（全部只读；退出码 0=PASS / 1=FAIL）：
  A 交付锚冻结：`MANIFEST.json` / tarball / 受审板 l7 / 冻结件 l4（sha256 逐字节）
  B K2 交付链门：`engine verify k2` = preflight + 3 项全 PASS
  C 框架维度读数：K1/K2 逐 gate（与只读基线 `BASELINE_pm_gate_k1_k2_readonly_v1.json` 逐条对比，报「回退」）
  D 影子验收（`--shadow`，默认开）：补丁集下 pytest 13 项隐藏失败是否清零 + 门禁增量达标

模式：
  · 默认 = **现状报告**（授权前的自我体检；FAIL 属预期，不视为错误）
  · `--expect-patched` = **变更后期望**：K1 ≥12 PASS、K2 ≥13 PASS、影子 pytest failed==0、零回退（fail-closed）

用法（容器根 ic_hw）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p6_acceptance_gate_v1.py [--expect-patched] [--no-shadow]
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

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(REPO, "k2")
P6X = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "P6_execution")
BASELINE = os.path.join(P6X, "BASELINE_pm_gate_k1_k2_readonly_v1.json")
ANCHORS = {
    "delivery_manifest": ("pm_gate/artifacts/k2_v4/L6/jlc_package/MANIFEST.json",
                          "6ee7495de61f749fba61a04a5311e17040988c322b3a17f46b6f26efd8b243b2"),
    "delivery_tarball": ("pm_gate/artifacts/k2_v4/L6/DELIVERY/k2_v4_8L.l7_gerber_package.tar.gz",
                         "0e88e107e2da81923ccdda0c20d89c7ca486bc2281a139a4a007650542f0bce0"),
    "board_reviewed_l7": ("hw/k2_v4_8L.l7.kicad_pcb", "c5a7df90aadb66e0"),
    "board_frozen_l4": ("hw/k2_v4_8L.l4.kicad_pcb", "d4e81f647be7f980"),
}


APP_PY = os.path.join(REPO, "AppDir", "bin", "python3.11")
APP_DIST = os.path.join(REPO, "AppDir", "shared", "lib", "python3.11", "dist-packages")
# AppDir 的 python 会**重写** PYTHONPATH/LD_LIBRARY_PATH（实测）⇒ 任何子进程必须用净化后的 env，
# 否则系统 python3 作为其子进程会因库/路径污染直接崩（fatal: no Python frame）。
_SANITIZE = ("PYTHONPATH", "PYTHONHOME", "LD_LIBRARY_PATH", "PYTHONSTARTUP")


def clean_env(**kw) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in _SANITIZE}
    env.update(kw)
    return env


def sha256(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check_anchors() -> dict:
    out = {}
    for name, (rel, expect) in ANCHORS.items():
        p = os.path.join(K2, rel)
        got = sha256(p) if os.path.isfile(p) else None
        ok = bool(got) and (got.startswith(expect) if len(expect) < 64 else got == expect)
        out[name] = {"path": rel, "expected": expect, "actual": (got or "")[:64], "ok": ok}
    return out


def _pipeline_python() -> str:
    """pipeline 检查用解释器 = ambient python3（与 k2/pipeline.yaml 记录一致）；
    AppDir python 不适用（会重写 PYTHONPATH）。可用 K2_PIPELINE_PYTHON 覆盖。"""
    return os.environ.get("K2_PIPELINE_PYTHON") or shutil.which("python3") or "python3"


def check_pipeline() -> dict:
    env = clean_env(PYTHONPATH=f"{K2}/_shared:{K2}")
    proc = subprocess.run([_pipeline_python(), os.path.join(K2, "_shared/eda_core/pipeline/engine.py"), "verify", "k2"],
                          cwd=K2, capture_output=True, text=True, env=env, timeout=1800)
    text = proc.stdout
    lines = [l.strip() for l in text.splitlines() if re.search(r"\[(PASS|FAIL)\]|: (PASS|FAIL)$", l.strip())]
    fails = [l for l in lines if "FAIL" in l]
    return {"interpreter": _pipeline_python(), "exit_code": proc.returncode, "checks": lines,
            "failed": fails, "ok": proc.returncode == 0 and not fails,
            "stderr_tail": (proc.stderr or "").strip().splitlines()[-2:]}


def framework_readings() -> dict:
    """现役框架下的 K1/K2 逐 gate 读数（复用只读基线工具，避免重复实现）。"""
    env = clean_env(PYTHONPATH=APP_DIST)
    tmp = "/tmp/opencode/accept_gate_baseline.json"
    subprocess.run([APP_PY, os.path.join(K2, "tools/k2_p6_readonly_baseline_v1.py"), "--out", tmp],
                   cwd=REPO, capture_output=True, text=True, env=env, timeout=1800)
    if not os.path.isfile(tmp):
        return {"error": "baseline_tool_failed"}
    now = json.load(open(tmp, encoding="utf-8"))["projects"]
    out = {}
    for proj, mods in now.items():
        gates = {}
        for mod, recs in mods.items():
            if not mod.startswith("check_") or not isinstance(recs, dict):
                continue
            for fn, rec in recs.items():
                if isinstance(rec, dict) and "passed" in rec:
                    gates[fn] = rec["passed"]
        out[proj] = {"pass": sum(1 for v in gates.values() if v is True),
                     "fail": sum(1 for v in gates.values() if v is False),
                     "gates": gates}
    return out


def regressions(now: dict) -> list:
    if not os.path.isfile(BASELINE):
        return ["baseline_missing"]
    base = json.load(open(BASELINE, encoding="utf-8"))["projects"]
    bad = []
    for proj, mods in base.items():
        for mod, gates in mods.items():
            if not isinstance(gates, dict):
                continue
            for fn, rec in gates.items():
                if not isinstance(rec, dict) or "passed" not in rec:
                    continue
                was, cur = rec["passed"], (now.get(proj, {}).get("gates", {}) or {}).get(fn)
                if was is True and cur is not True:
                    bad.append(f"{proj}.{fn}: PASS→{cur}（回退）")
    return bad


def shadow_acceptance() -> dict:
    env = clean_env(PYTHONPATH=APP_DIST)
    tmp = "/tmp/opencode/accept_gate_shadow.json"
    subprocess.run([APP_PY, os.path.join(K2, "tools/k2_p6_shadow_verify_v1.py"), "--out", tmp],
                   cwd=REPO, capture_output=True, text=True, env=env, timeout=3600)
    if not os.path.isfile(tmp):
        return {"error": "shadow_tool_failed"}
    d = json.load(open(tmp, encoding="utf-8"))
    k1 = d["gate_battery_shadow"]["k1"]
    k2v4 = d["gate_battery_shadow"]["k2_v4"]
    py = d["pytest_shadow"]["counts"]
    return {"k1_pass": sum(1 for v in k1.values() if v["status"] == "PASS"),
            "k2_pass": sum(1 for v in k2v4.values() if v["status"] == "PASS"),
            "pytest": py, "hidden_failures": len(d["pytest_shadow"]["failed_tests"]),
            "control_same": d["attribution"]["same_result"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-patched", action="store_true")
    ap.add_argument("--no-shadow", action="store_true")
    ap.add_argument("--out", default=os.path.join(P6X, "ACCEPTANCE_GATE_v1.json"))
    args = ap.parse_args()

    doc = {"artifact": "k2_p6_acceptance_gate", "schema": 1, "readonly": True,
           "mode": "expect_patched" if args.expect_patched else "status_report",
           "A_anchors": check_anchors(), "B_pipeline": check_pipeline()}
    doc["C_framework_readings"] = framework_readings()
    doc["C_regressions_vs_baseline"] = regressions(doc["C_framework_readings"])
    if not args.no_shadow:
        doc["D_shadow"] = shadow_acceptance()

    fails = []
    if not all(v["ok"] for v in doc["A_anchors"].values()):
        fails.append("A 交付锚/冻结件 sha 不符（红线：禁重建、禁改冻结件）")
    if not doc["B_pipeline"]["ok"]:
        fails.append("B `engine verify k2` 未全 PASS")
    if doc["C_regressions_vs_baseline"]:
        fails.append("C 相对只读基线出现 PASS→FAIL 回退")
    if args.expect_patched:
        c = doc["C_framework_readings"]
        if (c.get("k1", {}).get("pass", 0) < 12) or (c.get("k2_v4", {}).get("pass", 0) < 13):
            fails.append("C 变更后期望：K1 ≥12 PASS（实测 %s）、K2 ≥13 PASS（实测 %s）"
                         % (c.get("k1", {}).get("pass"), c.get("k2_v4", {}).get("pass")))
        sh = doc.get("D_shadow") or {}
        if sh.get("error"):
            fails.append(f"D 影子验收未跑成：{sh['error']}")
        elif sh.get("hidden_failures"):
            fails.append(f"D 变更后期望：13 项隐藏失败清零（实测仍 {sh['hidden_failures']} 项）")
    doc["verdict"] = "FAIL" if fails else "PASS"
    doc["failures"] = fails
    doc["note"] = ("默认模式 = 现状体检（FAIL 属预期，供授权前自查）；加 --expect-patched 才是变更后 fail-closed 验收"
                   if not args.expect_patched else "变更后验收：任一项不过即不得宣称完成（#K2-40 §四-5）")

    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    c = doc["C_framework_readings"]
    print(f"mode={doc['mode']} verdict={doc['verdict']}")
    print(f"  A anchors ok={sum(1 for v in doc['A_anchors'].values() if v['ok'])}/{len(doc['A_anchors'])}"
          f" | B verify={'PASS' if doc['B_pipeline']['ok'] else 'FAIL'}"
          f" | C K1 pass={c.get('k1', {}).get('pass')} K2 pass={c.get('k2_v4', {}).get('pass')}"
          f" | regressions={len(doc['C_regressions_vs_baseline'])}")
    if doc.get("D_shadow") and not doc["D_shadow"].get("error"):
        print(f"  D shadow: K1={doc['D_shadow']['k1_pass']} PASS / K2={doc['D_shadow']['k2_pass']} PASS"
              f" | pytest={doc['D_shadow']['pytest']} | hidden_failures={doc['D_shadow']['hidden_failures']}")
    for f in fails:
        print("  FAIL:", f)
    print("→", args.out)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
