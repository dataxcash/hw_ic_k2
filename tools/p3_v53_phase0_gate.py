#!/usr/bin/env python3
"""v53 Phase 0 gate — ZERO BEHAVIOR CHANGE 机器验收。

步骤（全前台，一次性）：
  0. preflight   — 提取 git HEAD report（golden）；缺失 → BASELINE_MISSING
  1. e2e 重跑    — python3 tools/p3_k2_real_board_e2e.py（真实驱动，零改动）
  2. 字节门      — new report vs HEAD report 逐字节 == 0
  3. fingerprint — board sha256 / input_fp（golden vs new，须可解释）
  4. checksum 门 — AllocTable / LandingTable 子树 sha256 不变
  5. 旧路径比较  — alloc/landing/solve 三子树 dict 相等（旧结果零变化）
  6. fallback    — CountingModel 重跑 solve_all_v4，统计自搜入口 + pn_ok
                   （counting 结果与 report solve 结果须逐字节一致 = 透明性证明）
  7. fact replay — fact_validate：对 SOLVED 段几何重放，仅记录 PASS/FAIL
  8. artifact    — 写 m13_v53_p0_audit.json
PASS 条件：exit 0 且字节一致 + alloc/landing checksum 不变 + 无生产文件修改。
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]          # k2/
ROOT = REPO.parents[0]                               # ic_hw/
sys.path.insert(0, str(REPO / "tools"))

import p3_k2_real_board_e2e as E                     # noqa: E402
import p3_v53_phase0_audit as A                      # noqa: E402

REPORT_REL = "pm_gate/artifacts/k2_v4/L3/p3_real_board_e2e/p3_real_board_e2e_report.json"
REPORT_PATH = REPO / REPORT_REL
AUDIT_DIR = REPO / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
AUDIT_PATH = AUDIT_DIR / "m13_v53_p0_audit.json"


def _git_show_head_report() -> bytes:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "show", f"HEAD:{REPORT_REL}"],
            capture_output=True, check=True)
        return out.stdout
    except subprocess.CalledProcessError:
        return b""


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _run_e2e() -> int:
    print("[gate] e2e 重跑 ...", flush=True)
    r = subprocess.run([sys.executable, "tools/p3_k2_real_board_e2e.py"],
                       cwd=str(REPO), capture_output=True, text=True)
    if r.stdout:
        print(r.stdout[-2000:])
    if r.stderr:
        print("[e2e stderr]", r.stderr[-1500:], flush=True)
    return r.returncode


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "artifact": "m13_v53_p0_audit.json",
        "phase": "P0",
        "golden_source": f"git HEAD:{REPORT_REL}",
        "gate_status": "FAIL",
        "baseline_status": "PRESENT",
        "checks": {},
    }

    # ── 0. preflight：golden 必须真实存在 ──
    head_bytes = _git_show_head_report()
    if not head_bytes:
        result["baseline_status"] = "BASELINE_MISSING"
        result["gate_status"] = "BASELINE_MISSING"
        result["blocker"] = ("git HEAD report 不存在，无法建立字节基线。"
                             "须先 commit 现有报告或提供 golden。")
        json.dump(result, open(AUDIT_PATH, "w"), indent=1,
                  ensure_ascii=False, sort_keys=True)
        print("[gate] BASELINE_MISSING ->", AUDIT_PATH)
        return 2
    try:
        head_report = json.loads(head_bytes.decode("utf-8"))
    except Exception as e:                              # pragma: no cover
        result["baseline_status"] = "BASELINE_MISSING"
        result["gate_status"] = "BASELINE_MISSING"
        result["blocker"] = f"HEAD report 解析失败: {e}"
        json.dump(result, open(AUDIT_PATH, "w"), indent=1,
                  ensure_ascii=False, sort_keys=True)
        return 2
    result["golden"] = {
        "sha256": _sha256(head_bytes),
        "board_sha256": (head_report.get("board") or {}).get("sha256"),
        "input_fp": head_report.get("input_fp"),
    }
    print(f"[gate] golden sha={result['golden']['sha256'][:16]}... "
          f"input_fp={str(result['golden']['input_fp'])[:16]}...", flush=True)

    # ── 1. e2e 重跑（真实驱动）──
    rc = _run_e2e()
    result["checks"]["e2e_rc"] = rc
    if rc != 0:
        result["blocker"] = "e2e 重跑非零退出"
        json.dump(result, open(AUDIT_PATH, "w"), indent=1,
                  ensure_ascii=False, sort_keys=True)
        print("[gate] FAIL: e2e rc != 0")
        return 1
    new_bytes = REPORT_PATH.read_bytes()
    new_report = json.loads(new_bytes.decode("utf-8"))

    # ── 2. 字节门 ──
    byte_ok = (new_bytes == head_bytes)
    result["checks"]["byte_identical"] = byte_ok
    result["new_report"] = {
        "sha256": _sha256(new_bytes),
        "board_sha256": (new_report.get("board") or {}).get("sha256"),
        "input_fp": new_report.get("input_fp"),
    }
    # fingerprint 可解释性（BASELINE_MISMATCH 判据）
    fp_ok = (result["golden"]["board_sha256"]
             == result["new_report"]["board_sha256"]
             and result["golden"]["input_fp"] == result["new_report"]["input_fp"])
    result["checks"]["fingerprint_match"] = fp_ok
    if not byte_ok:
        # 不伪造 PASS：留证据，恢复 working 文件保持树净
        REPORT_PATH.write_bytes(head_bytes)
        result["baseline_status"] = "BASELINE_MISMATCH"
        result["gate_status"] = "BASELINE_MISMATCH"
        result["blocker"] = ("e2e 重跑与 HEAD report 字节不一致：引擎行为已变或"
                             "golden 过期。见 sha256 差异。已恢复 HEAD 文件。")
        json.dump(result, open(AUDIT_PATH, "w"), indent=1,
                  ensure_ascii=False, sort_keys=True)
        print("[gate] BASELINE_MISMATCH ->", AUDIT_PATH)
        return 1

    # ── 3/4/5. alloc/landing/solve 子树 checksum + dict 相等 ──
    def subtree(p):
        return (new_report.get("stages") or {}).get(p) or {}
    alloc_new = (subtree("alloc")).get("alloc")
    landing_new = (subtree("landing")).get("allocation")
    solve_new = (subtree("solve")).get("results")
    alloc_head = ((head_report.get("stages") or {}).get("alloc") or {}).get("alloc")
    landing_head = ((head_report.get("stages") or {}).get("landing")
                    or {}).get("allocation")
    solve_head = ((head_report.get("stages") or {}).get("solve")
                  or {}).get("results")
    checksums = {
        "AllocTable": {"head": A.sha256_json(alloc_head),
                       "new": A.sha256_json(alloc_new)},
        "LandingTable": {"head": A.sha256_json(landing_head),
                         "new": A.sha256_json(landing_new)},
        "SolveResults": {"head": A.sha256_json(solve_head),
                         "new": A.sha256_json(solve_new)},
    }
    result["checks"]["checksums"] = checksums
    result["checks"]["alloc_unchanged"] = alloc_head == alloc_new
    result["checks"]["landing_unchanged"] = landing_head == landing_new
    result["checks"]["solve_unchanged"] = solve_head == solve_new

    # 段级计数（route/segment 旧结果对比）
    def seg_tally(res: dict) -> dict:
        t = {"bases": len(res or {}),
             "segments": sum(len((r or {}).get("segments", []))
                             for r in (res or {}).values()),
             "solved": sum(1 for r in (res or {}).values()
                           for s in (r or {}).get("segments", [])
                           if s.get("status") == "SOLVED")}
        return t
    result["checks"]["segment_tally"] = {
        "head": seg_tally(solve_head), "new": seg_tally(solve_new)}

    # ── 6. fallback counting（CountingModel 透明性 + 计数）──
    raw, model = A.run_counting_solve(alloc_new, landing_new)
    counting_matches = (raw.get("results") == solve_new)
    result["checks"]["counting_transparent"] = counting_matches
    result["fallback"] = {
        "total_form_calls": sum(model.audit_counts.values()),
        "per_form": dict(model.audit_counts),
        "pn_ok": {k: dict(v) for k, v in model.audit_pn.items()},
        "fallback_segments": A.fallback_segments(solve_new),
    }

    # ── 7. fact replay（SOLVED 段几何重放，仅记录）──
    fv = A.fact_validate(solve_new)
    result["fact_validate"] = {
        "n_solved": fv["n_solved"],
        "all_pass": fv["all_pass"],
        "per_segment": [{"base": p["base"], "segname": p["segname"],
                         "ok": p["ok"],
                         "n_shared_segs": p["n_shared_segs"],
                         "n_shared_vias": p["n_shared_vias"],
                         "fail_checks": [c["check"] for c in p["checks"]
                                         if not c["ok"]]}
                        for p in fv["per_segment"]],
    }

    # ── 8. 裁决 ──
    prod_dirty = _production_modified()
    result["checks"]["no_production_modification"] = not prod_dirty
    passed = (byte_ok and fp_ok
              and result["checks"]["alloc_unchanged"]
              and result["checks"]["landing_unchanged"]
              and result["checks"]["solve_unchanged"]
              and counting_matches and not prod_dirty)
    result["gate_status"] = "PASS" if passed else "FAIL"
    if not passed:
        result["blocker"] = ("字节/checksum/透明性门未全过："
                             f"byte={byte_ok} fp={fp_ok} "
                             f"alloc={result['checks']['alloc_unchanged']} "
                             f"landing={result['checks']['landing_unchanged']} "
                             f"solve={result['checks']['solve_unchanged']} "
                             f"counting={counting_matches} "
                             f"prod_dirty={prod_dirty}")
    json.dump(result, open(AUDIT_PATH, "w"), indent=1,
              ensure_ascii=False, sort_keys=True)
    print(f"[gate] status={result['gate_status']} -> {AUDIT_PATH}")
    return 0 if passed else 1


def _production_modified() -> list:
    """白名单外被修改/新增的生产文件（本卡只允许 audit 目录新增产物）。

    排除：白名单 3 文件；v52 前既有 untracked 产物（??，非本卡引入）；
    `_shared` 子模块指针行（M _shared = 容器内嵌陈旧快照既有 dirty，
    v52 handoff §5 已记录，内容零变化，勿动勿 stage）。
    """
    out = []
    r = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain"],
                       capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        rel = line[3:].strip()
        if rel == "_shared":                      # 子模块指针既有 dirty
            continue
        if rel.startswith("tools/p3_v53_phase0_audit.py") or \
           rel.startswith("tools/p3_v53_phase0_gate.py") or \
           rel.startswith("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/"
                          "m13_v53_p0_audit.json"):
            continue
        if line[:2].strip() in ("M", "A", "D", "R", "C"):
            out.append(line.strip())
    return out


if __name__ == "__main__":
    raise SystemExit(main())
