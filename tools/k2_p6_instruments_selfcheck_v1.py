#!/usr/bin/env python3
"""k2_p6_instruments_selfcheck_v1.py — P6/学习环批 2 仪器的**只读机核**（fail-closed）。

机核四类（任一 FAIL ⇒ 退出码 1，并写入 INSTRUMENT_SELFCHECK.json）：
  ① 行号/符号锚：计划所引载体行此刻是否**真的是**那个符号（防「计划引旧行号」空转）；
  ② 工具可加载：pm_gate * / eda_core.hs_route_model 可 import；
  ③ 基线可复现：重跑捕获器 ⇒ 与在库基线**逐字节同** + 与 results_template 记录的 sha 一致；
  ④ 前置门事实：P5 外部回件是否仍 NOT_RUN / 判据应然集（manifest.k1.yaml）是否仍缺（不得臆造）。

只读：不改任何载体/判据/交付包；仅写 `--out`（缺省 = P6_execution/INSTRUMENT_SELFCHECK.json）。
确定性：无时间戳、键排序 ⇒ 两次连跑逐字节同。

用法（容器根 ic_hw）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
      k2/tools/k2_p6_instruments_selfcheck_v1.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

K2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(K2)
DEF_OUT = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "P6_execution",
                       "INSTRUMENT_SELFCHECK.json")
BASELINE = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "P6_execution",
                        "BASELINE_pm_gate_k1_k2_readonly_v1.json")
RESULTS = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "P6_execution",
                       "results_template.json")
GEN = os.path.join(K2, "tools", "k2_p6_readonly_baseline_v1.py")

# (相对 _shared 的路径, 行号, 该行必须包含的符号子串, 说明)
LINE_ANCHORS = [
    ("eda_core/hs_route_model.py", 892, "_escape_smd_via", "B2-1 调用点"),
    ("eda_core/hs_route_model.py", 4406, "def solve_all_v4", "B2-2 定义"),
    ("eda_core/hs_route_model.py", 4513, "def _escape_smd_via", "B2-1 定义"),
    ("eda_core/hs_route_model.py", 4796, "if args.all_v4", "B2-2 CLI 开关"),
    ("eda_core/hs_route_model.py", 4800, "m.config.chain_segments", "B2-2 分派（K1 链基）"),
    ("eda_core/hs_route_model.py", 4806, "solve_all_v4(bases)", "B2-2 调用"),
    ("eda_core/hs_route_model.py", 4842, "m.config.chain_segments", "B2-2 第二路径"),
    ("eda_core/routing_topology_gate.py", 43, "--all-v4", "B2-2 同步点（docstring）"),
    ("pm_gate/check_l1.py", 193, "RULES_DOC", "B2-4 规则文档路径"),
    ("pm_gate/check_l3.py", 26, 'SPEC_k2_v4.json', "B2-3a 硬编码 SPEC 名"),
    ("pm_gate/check_l3.py", 46, 'SPEC_k2_v4.json', "B2-3a 证据文案"),
    ("pm_gate/check_qa.py", 35, "config.spec_name()", "B2-3b 空参调用"),
]
CLOSURE_RANGE = ("pm_gate/closure_check.py", 110, 113, ("DEFAULT_SPEC", "ESCAPE_SPEC_PATH"), "B2-3c 框架相对默认值")


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_line_anchors() -> dict:
    out = {}
    for rel, lineno, needle, why in LINE_ANCHORS:
        rel_repo = "k2/_shared/" + rel if os.path.exists(os.path.join(K2, "_shared", rel)) else "_shared/" + rel
        path = os.path.join(REPO, rel_repo)
        entry = {"rel": rel_repo, "claimed_line": lineno, "needle": needle, "why": why, "ok": False}
        if not os.path.isfile(path):
            entry["error"] = "file_missing"
            out[f"{rel}:{lineno}"] = entry
            continue
        lines = open(path, encoding="utf-8").read().splitlines()
        entry["line_count"] = len(lines)
        entry["line_text"] = lines[lineno - 1].strip() if 0 < lineno <= len(lines) else None
        entry["ok"] = bool(entry["line_text"] and needle in entry["line_text"])
        if not entry["ok"]:  # 找实际位置（便于修订计划，不静默）
            found = [i for i, t in enumerate(lines, 1) if needle in t]
            entry["actual_lines"] = found[:8]
        out[f"{rel}:{lineno}"] = entry
    # 区间锚（closure_check 110-113）
    rel, lo, hi, needles, why = CLOSURE_RANGE
    path = os.path.join(REPO, "_shared", rel)
    blob = "\n".join(open(path, encoding="utf-8").read().splitlines()[lo - 1:hi]) if os.path.isfile(path) else ""
    out[f"{rel}:{lo}-{hi}"] = {"rel": "_shared/" + rel, "claimed_line": f"{lo}-{hi}",
                               "needle": list(needles), "why": why,
                               "ok": all(n in blob for n in needles),
                               "text": blob.replace("\n", " ⏎ ")[:200]}
    return out


def check_tooling() -> dict:
    sys.path.insert(0, os.path.join(REPO, "_shared"))
    out = {}
    for mod in ("pm_gate.check_l1", "pm_gate.check_l2", "pm_gate.check_l3", "pm_gate.check_qa",
                "pm_gate.closure_check", "eda_core.hs_route_model"):
        try:
            __import__(mod)
            out[mod] = True
        except BaseException as exc:
            out[mod] = f"IMPORT_FAIL {type(exc).__name__}: {exc}"
    out["rules_doc_truth_exists"] = os.path.isfile(os.path.join(REPO, "_shared", "docs", "PCB_DESIGN_RULES.md"))
    return out


CHECKLIST = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "P6_execution", "CHECKLIST.md")
REQUIRED_ITEM_FIELDS = ("title", "carrier", "owner", "action", "commands",
                        "fail_closed_gates", "negative_controls", "authorization", "status")


def check_checklist_consistency() -> dict:
    """人读检查表（CHECKLIST.md 表格行）↔ 机读结果表（results_template.json items）**逐项一致**。

    防「人/机两套清单漂移」——本轮即发现一次标签冲突（B2-3c/3d 被重复占用），故设为 fail-closed 门。
    """
    # 行形如 `| **B2-3e（F-2c）** | ...`（粗体内可带补充文字）⇒ 取粗体内 B2- 前缀
    rows = [m.group(1) for m in re.finditer(r"^\|\s*\*\*(B2-[A-Za-z0-9\-]+)[^*]*\*\*\s*\|",
                                            open(CHECKLIST, encoding="utf-8").read(), re.M)]
    doc = json.load(open(RESULTS, encoding="utf-8"))
    items = doc.get("items", {})
    missing_in_machine = sorted(set(rows) - set(items))
    missing_in_checklist = sorted(set(items) - set(rows))
    field_gaps = {k: [f for f in REQUIRED_ITEM_FIELDS if f not in v] for k, v in items.items()
                  if isinstance(v, dict) and [f for f in REQUIRED_ITEM_FIELDS if f not in v]}
    return {"checklist_rows": rows, "machine_items": sorted(items), "counts": {"checklist": len(rows), "machine": len(items)},
            "missing_in_machine": missing_in_machine, "missing_in_checklist": missing_in_checklist,
            "field_gaps": field_gaps,
            "ok": not (missing_in_machine or missing_in_checklist or field_gaps) and len(rows) == len(items) > 0}


def check_baseline() -> dict:
    out = {"path": os.path.relpath(BASELINE, REPO)}
    if not os.path.isfile(BASELINE):
        out.update({"ok": False, "error": "baseline_missing"})
        return out
    out["sha256_stored"] = sha256_of(BASELINE)
    recorded = json.load(open(RESULTS, encoding="utf-8"))["baseline"]["sha256"]
    out["sha256_recorded_in_results"] = recorded
    out["sha_matches_results"] = (recorded == out["sha256_stored"])
    tmp = "/tmp/opencode/p6_selfcheck_baseline.json"
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", os.path.join(REPO, "AppDir", "shared", "lib", "python3.11", "dist-packages"))
    proc = subprocess.run([sys.executable, GEN, "--out", tmp], cwd=REPO, capture_output=True,
                          text=True, env=env, timeout=1800)
    out["regen_exit_code"] = proc.returncode
    if proc.returncode == 0 and os.path.isfile(tmp):
        out["sha256_regenerated"] = sha256_of(tmp)
        out["byte_identical_to_stored"] = (out["sha256_regenerated"] == out["sha256_stored"])
    else:
        out["byte_identical_to_stored"] = False
        out["regen_stderr_tail"] = (proc.stderr or "").strip().splitlines()[-3:]
    out["ok"] = bool(out["sha_matches_results"] and out["byte_identical_to_stored"])
    return out


def check_prerequisites() -> dict:
    fa = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "L6", "first_article_l8", "results_template.json")
    out = {}
    if os.path.isfile(fa):
        items = json.load(open(fa, encoding="utf-8")).get("items", {})
        statuses = {k: (v.get("status") if isinstance(v, dict) else None) for k, v in items.items()}
        out["first_article_statuses"] = statuses
        out["p5_external_all_not_run"] = bool(statuses) and all(s == "NOT_RUN" for s in statuses.values())
    else:
        out["p5_external_all_not_run"] = None
    out["criteria_manifest_k1_exists"] = os.path.isfile(os.path.join(REPO, "criteria", "manifest.k1.yaml"))
    out["criteria_manifest_k2_exists"] = os.path.isfile(os.path.join(REPO, "criteria", "manifest.k2.yaml"))
    out["p6_1_blocked_on_supervisor_artifact"] = not out["criteria_manifest_k1_exists"]
    out["ok"] = True  # 事实记录项（不构成 fail）；结论由 prerequisites 判读
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEF_OUT)
    args = ap.parse_args()

    doc = {
        "artifact": "k2_p6_instruments_selfcheck",
        "schema": 1,
        "scope": "P6/学习环批2 仪器机核（只读）",
        "readonly": True,
        "covers": {
            "checklist": "pm_gate/artifacts/k2_v4/P6_execution/CHECKLIST.md",
            "results_template": "pm_gate/artifacts/k2_v4/P6_execution/results_template.json",
            "baseline": "pm_gate/artifacts/k2_v4/P6_execution/BASELINE_pm_gate_k1_k2_readonly_v1.json",
        },
        "line_anchors": check_line_anchors(),
        "tooling": check_tooling(),
        "checklist_consistency": check_checklist_consistency(),
        "baseline_reproducibility": check_baseline(),
        "prerequisites_facts": check_prerequisites(),
    }

    anchors_ok = all(v["ok"] for v in doc["line_anchors"].values())
    tooling_ok = all(v is True for k, v in doc["tooling"].items() if k != "rules_doc_truth_exists")
    rules_ok = doc["tooling"]["rules_doc_truth_exists"]
    base_ok = doc["baseline_reproducibility"]["ok"]
    cl_ok = doc["checklist_consistency"]["ok"]
    failed = []
    if not anchors_ok:
        failed.append("line_anchors（计划所引行号/符号与载体不符 ⇒ 须修订计划，禁携旧行号施工）")
    if not tooling_ok:
        failed.append("tooling_import")
    if not rules_ok:
        failed.append("rules_doc_truth_missing（_shared/docs/PCB_DESIGN_RULES.md 不在 ⇒ B2-4 无判据真源）")
    if not base_ok:
        failed.append("baseline_reproducibility（基线不可复现或 sha 与 results_template 不一致）")
    if not cl_ok:
        c = doc["checklist_consistency"]
        failed.append("checklist_consistency（人/机清单漂移：缺于机读 %s / 缺于检查表 %s / 字段缺口 %s）"
                      % (c["missing_in_machine"], c["missing_in_checklist"], list(c["field_gaps"])))
    doc["summary"] = {"checks": 5, "anchor_count": len(doc["line_anchors"]), "failed": failed}
    doc["verdict"] = "FAIL" if failed else "PASS"
    doc["fail_closed"] = ("PASS ⇒ 仪器与载体锚一致、基线可复现；**不代表授权已给**（施工另需 prerequisites 全绿）")

    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"verdict={doc['verdict']} anchors={sum(1 for v in doc['line_anchors'].values() if v['ok'])}/"
          f"{len(doc['line_anchors'])} baseline_ok={base_ok} checklist_ok={cl_ok} → {args.out}")
    if failed:
        for f in failed:
            print("  FAIL:", f)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
