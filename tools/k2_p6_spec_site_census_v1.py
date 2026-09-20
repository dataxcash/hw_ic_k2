#!/usr/bin/env python3
"""k2_p6_spec_site_census_v1.py — P6/批 2 的**只读**普查器（B2-3 范围定性 + 34 skip 归因 + K1 waiver 复算）。

产出三块（确定性 JSON；两次连跑逐字节同）：
  ① `spec_k2_v4_sites`：`SPEC_k2_v4` 站点全量普查 + **逐处定性**（B2-3 要求「逐处定性，禁一把梭」）；
  ② `skip_decomposition`：`test_hs_route_model.py` 的 **34 skip 归因**（按 skip 常量分组 + 每条可执行补救）；
  ③ `k1_g15_waiver_recompute`：K1 `G1.5` WAIVER 的**实质条件机核复算**（撤 waiver 的前置证据）。

只读：不改任何载体；仅写 `--out`。标准命令（容器根 ic_hw）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
      k2/tools/k2_p6_spec_site_census_v1.py
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys

K2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(K2)
DEF_OUT = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "P6_execution", "SPEC_SITE_CENSUS_v1.json")
NEEDLE = "SPEC_k2_v4"
TEST_FILE = "_shared/eda_core/tests/test_hs_route_model.py"

# B2-3「逐处定性」：rel:line → (类别, 理由)
SITE_CLASS = {
    # ── STALE_LEGACY_BASE：基址仍是拆分前 `revA/pcb` 布局（M-14 未覆盖）⇒ 路径恒不存在 ──
    "eda_core/cap_wall_apply.py:56": ("STALE_LEGACY_BASE", "SPEC_PATH=_PCB_ROOT/pm_gate/artifacts/L3/…，_PCB_ROOT 解析到 _shared（非项目根）"),
    "eda_core/cap_wall_solver.py:608": ("STALE_LEGACY_BASE", "--spec 默认值走 _PCB_ROOT/pm_gate/artifacts/k2_v4/…（恒缺）"),
    "pm_gate/closure_check.py:112": ("STALE_LEGACY_BASE", "F-3：DEFAULT_SPEC=模块目录/artifacts/…（恒缺）"),
    "pm_gate/wp1_semantics_check.py:45": ("STALE_LEGACY_BASE", "注释自承 _PCB_ROOT='revA/pcb' 旧布局；DEFAULT_SPEC 恒缺"),
    # ── NAME_ONLY_HARDCODE：基址正确（artifacts API / 项目根），仅文件名写死 ──
    "pm_gate/check_l3.py:26": ("NAME_ONLY_HARDCODE", "B2-3a：读 SPEC 名写死 ⇒ 非默认项目/新版 spec 恒读错"),
    "pm_gate/check_l3.py:53": ("NAME_ONLY_HARDCODE", "check_g32 内容期望写死 'SPEC_k2_v4.json'（判据内容，须项目化）"),
    "pm_gate/freeze_wp1.py:45": ("NAME_ONLY_HARDCODE", "DEFAULT_SPEC=artifacts_dir('L3')+写死名"),
    "pm_gate/review.py:105": ("NAME_ONLY_HARDCODE", "L3 复核读 artifacts_dir('L3')+写死名"),
    "pm_gate/review.py:121": ("NAME_ONLY_HARDCODE", "G3* 断言源 artifacts_dir('L3')+写死名"),
    "pm_gate/tools_escape_predict.py:39": ("NAME_ONLY_HARDCODE", "artifacts_dir('L3')+写死名"),
    # ── CLI_CONTRACT：CLI 参数/帮助/用法文案（调用方传路径；不改名亦可，但须具名） ──
    "eda_core/board_low_speed_sync.py:32": ("CLI_CONTRACT", "usage 文案"),
    "eda_core/board_spec_consistency.py:35": ("CLI_CONTRACT", "usage 文案"),
    "eda_core/escape_connect_gen.py:25": ("CLI_CONTRACT", "usage 文案"),
    "eda_core/escape_low_speed_freeze.py:19": ("CLI_CONTRACT", "usage 文案"),
    "eda_core/escape_low_speed_spec_write.py:16": ("CLI_CONTRACT", "usage 文案"),
    "eda_core/escape_stub_replanner.py:19": ("CLI_CONTRACT", "usage 文案"),
    "eda_core/escape_stub_replanner.py:204": ("CLI_CONTRACT", "--spec-l3 必填参数 help 文案"),
    # ── DOCSTRING_MESSAGE：注释/报错文案（零行为；具名豁免） ──
    "pm_gate/check_l3.py:3": ("DOCSTRING_MESSAGE", "docstring"),
    "pm_gate/check_l3.py:28": ("DOCSTRING_MESSAGE", "报错文案"),
    "pm_gate/check_l3.py:46": ("DOCSTRING_MESSAGE", "evidence 文案"),
    "pm_gate/check_qa.py:34": ("DOCSTRING_MESSAGE", "注释（该行为 B2-3b 缺陷点）"),
    "pm_gate/config.py:120": ("DOCSTRING_MESSAGE", "docstring"),
    "pm_gate/red_team.py:49": ("DOCSTRING_MESSAGE", "docstring"),
    "pm_gate/tools_escape_predict.py:15": ("DOCSTRING_MESSAGE", "docstring"),
    "eda_core/closure_check.py:413": ("DOCSTRING_MESSAGE", "报错文案"),
    "eda_core/verify_checks.py:17": ("DOCSTRING_MESSAGE", "docstring"),
    # ── TEST_ANCHOR：测试锚（随 B2-1/B2-2 同批：项目参数化 or 具名 K2-only） ──
    "eda_core/tests/conftest.py:10": ("TEST_ANCHOR", "fixture docstring"),
    "eda_core/tests/conftest.py:42": ("TEST_ANCHOR", "fixture docstring"),
    "eda_core/tests/conftest.py:46": ("TEST_ANCHOR", "fixtures/SPEC_k2_v4.json 副本 ⇒ 需 per-project fixture"),
    "eda_core/tests/conftest.py:65": ("TEST_ANCHOR", "fixture docstring"),
    "eda_core/tests/test_cap_wall_upgrade.py:107": ("TEST_ANCHOR", "注释"),
    "eda_core/tests/test_cap_wall_upgrade.py:113": ("TEST_ANCHOR", "真源路径"),
    "eda_core/tests/test_closure_check.py:184": ("TEST_ANCHOR", "真源路径"),
    "eda_core/tests/test_escape_landing.py:683": ("TEST_ANCHOR", "真源路径"),
    "eda_core/tests/test_hs_route_model.py:164": ("TEST_ANCHOR", "BASELINE_SPEC 绝对锚（已修法示范）"),
    "eda_core/tests/test_hs_route_model.py:324": ("TEST_ANCHOR", "K2V4_SPEC 绝对锚（已修法示范）"),
    "eda_core/tests/test_redteam_evidence.py:37": ("TEST_ANCHOR", "REAL_SPEC 路径"),
    "eda_core/tests/test_routing_topology_gate.py:31": ("TEST_ANCHOR", "K2_SPEC 绝对锚"),
    "eda_core/tests/test_topology_gate.py:25": ("TEST_ANCHOR", "legacy ioconvert revA 路径"),
    # ── NEGATIVE_CONTROL：既有的「零单板特判」禁令测试（不改） ──
    "eda_core/tests/test_feature_extractor.py:15": ("NEGATIVE_CONTROL", "禁令测试 docstring"),
    "eda_core/tests/test_feature_extractor.py:262": ("NEGATIVE_CONTROL", "forbidden 令牌（仅扫 feature_extractor 一个模块）"),
    # ── PROJECT_CONFIG：项目配置条目本身（正当） ──
    "pm_gate/config.py:27": ("PROJECT_CONFIG", "PROJECTS 兜底字典 k2_v4 条目 = 正当默认"),
    # ── LEGACY_OTHER_PROJECT：指向别的项目的候选路径 ──
    "eda_core/env_fingerprint.py:69": ("LEGACY_OTHER_PROJECT", "候选含 strix-halo-ioconvert/revA 路径（与 K2 判据无关）"),
}

SKIP_CONSTANTS = [
    {"constant": "K2V4_REAL_BOARD", "expr": 'REPO / "k2_v4.kicad_pcb"', "reason_match": ["真板缺失"],
     "resolve": lambda: (os.path.join(REPO, "k2_v4.kicad_pcb"), os.path.join(REPO, "k2", "k2_v4.kicad_pcb")),
     "remedy": "锚改为 REPO/'k2'/'k2_v4.kicad_pcb'（同文件 SPEC/ALLOC 已用绝对锚；一行可修）⇒ 22 项可由 skip 转**实跑**"},
    {"constant": "BASELINE_PCB", "expr": 'Path("/tmp/opencode/boards/k2_m9demo.kicad_pcb")', "reason_match": ["基线板不存在"],
     "resolve": lambda: None, "remedy": "依赖 /tmp 生成物（不在库）= N-05「生成器不可复跑」同族 ⇒ 需补 fixture 生成步骤或**具名接受**"},
]


def scan_sites(root: str) -> list:
    hits = []
    base_root = os.path.join(REPO, root)
    for base, dirs, files in os.walk(base_root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(base, fn)
            for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                if NEEDLE in line:
                    hits.append({"rel": os.path.relpath(p, base_root).replace(os.sep, "/"),
                                 "line": i, "text": line.strip()[:160]})
    return hits


def collect_sites() -> dict:
    out = {"needle": NEEDLE, "roots": {}}
    per_root = {}
    for root in ("_shared", "k2/_shared"):
        if os.path.isdir(os.path.join(REPO, root)):
            per_root[root] = scan_sites(root)
    out["roots"] = {k: len(v) for k, v in per_root.items()}
    out["roots_agree"] = len(set(json.dumps(v, sort_keys=True) for v in per_root.values())) == 1
    primary = per_root.get("_shared") or next(iter(per_root.values()), [])
    sites = []
    for h in primary:
        key = f"{h['rel']}:{h['line']}"
        cls, why = SITE_CLASS.get(key, ("UNCLASSIFIED", "须补定性"))
        sites.append(dict(h, site_class=cls, rationale=why, key=key))
    sites.sort(key=lambda s: (s["site_class"], s["rel"], s["line"]))
    out["count"] = len(sites)
    out["classes"] = dict(sorted(collections.Counter(s["site_class"] for s in sites).items()))
    out["unclassified"] = [s["key"] for s in sites if s["site_class"] == "UNCLASSIFIED"]
    out["sites"] = sites
    return out


def decompose_skips() -> dict:
    path = os.path.join(REPO, TEST_FILE)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PM_GATE_PROJECT_ROOT")}
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rs", TEST_FILE],
                          cwd=REPO, capture_output=True, text=True, env=env, timeout=1800)
    text = re.sub(r"\s+in\s+[\d.]+s\s*$", "", proc.stdout, flags=re.M)
    reasons = collections.Counter(m.group(1).strip() for m in re.finditer(r"^SKIPPED \[\d+\] .*?: (.*)$", text, re.M))
    summary = re.search(r"(\d+) passed, (\d+) skipped", text)
    groups = []
    for sc in SKIP_CONSTANTS:
        r = sc["resolve"]()
        g = {"constant": sc["constant"], "expr": sc["expr"], "remedy": sc["remedy"]}
        if r:
            cur, good = r
            g.update({"resolved_exists": os.path.isfile(cur), "correct_anchor": os.path.relpath(good, REPO),
                      "correct_anchor_exists": os.path.isfile(good)})
        g["skip_reasons"] = sorted(r for r in reasons
                                   if any(m in r for m in sc.get("reason_match", [])))
        g["skip_count"] = sum(reasons[r] for r in g["skip_reasons"])
        groups.append(g)
    return {"test_file": TEST_FILE, "exit_code": proc.returncode,
            "passed": int(summary.group(1)) if summary else None,
            "skipped": int(summary.group(2)) if summary else None,
            "reasons": dict(sorted(reasons.items())), "groups": groups,
            "unattributed_skips": (int(summary.group(2)) - sum(g["skip_count"] for g in groups)) if summary else None}


def recompute_k1_waiver() -> dict:
    """K1 G1.5 WAIVER 实质条件机核复算（只读）。"""
    truth = os.path.join(REPO, "_shared", "docs", "PCB_DESIGN_RULES.md")
    checkouts = []
    for name in ("_shared", "k2/_shared", "key_v2/_shared", "pciesw4/_shared"):
        p = os.path.join(REPO, name, "docs", "PCB_DESIGN_RULES.md")
        if os.path.isfile(p):
            txt = open(p, encoding="utf-8", errors="replace").read()
            checkouts.append({"path": f"{name}/docs/PCB_DESIGN_RULES.md", "has_strong_clause": "强条" in txt})
    k1_root = os.path.join(REPO, "k1")
    pre_dir = os.path.join(k1_root, "pm_gate", "artifacts", "k1", "L1", "precheck")
    prechecks = []
    for fn in sorted(os.listdir(pre_dir)) if os.path.isdir(pre_dir) else []:
        if fn.startswith("precheck_") and fn.endswith(".md"):
            txt = open(os.path.join(pre_dir, fn), encoding="utf-8", errors="replace").read()
            prechecks.append({"file": fn,
                              "has_G2_padwall": "G2 焊盘墙穿透" in txt,
                              "has_verdict": "汇总判定" in txt})
    cand_dir = os.path.join(k1_root, "pm_gate", "artifacts", "k1", "L1", "candidates")
    candidates = []
    for fn in sorted(os.listdir(cand_dir)) if os.path.isdir(cand_dir) else []:
        if fn.endswith(".md"):
            txt = open(os.path.join(cand_dir, fn), encoding="utf-8", errors="replace").read()
            candidates.append({"file": fn, "has_keyword_serpentine": "蛇形" in txt})
    ok = (os.path.isfile(truth) and all(c["has_strong_clause"] for c in checkouts)
          and len(prechecks) >= 1 and all(p["has_G2_padwall"] and p["has_verdict"] for p in prechecks)
          and len(candidates) >= 1 and all(c["has_keyword_serpentine"] for c in candidates))
    return {"claim": "waiver 原文：规则件在 _shared/docs；工艺常识强条文档在库；3 份 precheck 章节齐；候选含「蛇形」",
            "truth_path": "_shared/docs/PCB_DESIGN_RULES.md", "truth_path_exists": os.path.isfile(truth),
            "rules_doc_checkouts": checkouts, "prechecks": prechecks, "candidates": candidates,
            "substantive_conditions_met": bool(ok),
            "note": "本项为**复核既有 WAIVER 的实质陈述**，非新增检查齿；F-1 修好后应转机判 PASS 并撤 waiver（B2-4）"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEF_OUT)
    args = ap.parse_args()
    doc = {
        "artifact": "k2_p6_spec_site_census",
        "schema": 1,
        "purpose": "P6/批2 只读普查：B2-3 站点定性 + 34 skip 归因 + K1 G1.5 waiver 复算",
        "readonly": True,
        "spec_k2_v4_sites": collect_sites(),
        "skip_decomposition": decompose_skips(),
        "k1_g15_waiver_recompute": recompute_k1_waiver(),
    }
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    s = doc["spec_k2_v4_sites"]
    sk = doc["skip_decomposition"]
    print(f"sites={s['count']} classes={s['classes']} unclassified={len(s['unclassified'])}"
          f" | skips={sk['skipped']} (unattributed={sk['unattributed_skips']})"
          f" | waiver_met={doc['k1_g15_waiver_recompute']['substantive_conditions_met']} → {args.out}")
    return 1 if s["unclassified"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
