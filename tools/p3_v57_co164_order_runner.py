#!/usr/bin/env python3
"""CO-164 — **规范复现序机判执行器**（R-CO164-1）：以 rc 为准判定收敛，禁「sha 稳定即收敛」。

缘起（实测事故，CO-163）：`co146_boundary_append.py` 因 §37 文本里的 f-string 花括号语法错误**每次崩溃（rc=1）**，
但收敛判定只看 boundary/记录 sha ⇒ sha 恒不变 ⇒ 报「CONVERGED」，边界 §37 实际从未写入、pin 表陈旧（co77/co135/co136 判 FAIL）。
即「以 sha 稳定替代 rc 检查」会产生**假收敛**（本会话由一个独立 rc 复核才发现）。

本器（**不在**规范序内运行，避免自递归；其报告落在 `.archer_tmp/`，**不被 boundary 引用** ⇒ 不构成下游快照/不动点）：
  ① 依 R-CO163-3 顺序逐步执行（子进程），rc 策略：`EXPECTED_NONZERO = {co146_jlc_dfm_gate}`（verdict=FAIL 属预期），
     其余任一步非零 ⇒ **立即停机**并报出门名/rc/stderr 尾（fail-fast，禁"继续跑完再说"）；
  ② 每轮迭代后比对受控 sha（boundary + 关键记录 + 台账/登记簿）；**仅当** rc 全合规**且** sha 逐轮稳定 ⇒ 判 CONVERGED；
  ③ `--check` 只做静态体检：步骤文件存在 + 可编译 + rc 策略声明完备（零执行、零落盘），可作轻量 sanity。
CLI:
  python3 tools/p3_v57_co164_order_runner.py [--check] [--max-iter 5]
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, time
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
PY = K2.parent / "AppDir" / "usr" / "bin" / "python3.11"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REPORT = K2 / ".archer_tmp/co164_order_report.json"
# R-CO163-3 规范复现序（与 boundary §37 同步；末步 boundary_append 为 pin 再对齐）
ORDER = ["co146_impedance_table", "co146_pm_eval", "co146_ledger_add", "co153_k9_domain_coverage",
         "co148_u6_datasheet_inputs", "co148_thermal_ruling", "co149_thermal_mitigation_derive", "co147_l2_ruling",
         "co146_jlc_dfm_gate", "co146_jlc_fab_package", "co152_findings_disposition", "co155_co154_findings_disposition",
         "co156_co154_open_disposition", "co157_gate_hardening_3", "co158_l5_packet_selfcontained",
         "co159_rev19_co156_co157_co158_review", "co160_co159_findings_disposition", "co161_gap_hardening_4",
         "co162_verdict_binding", "co163_binding_to_order_notes", "co124_input_selfcheck_gate", "co150_k9_domain_gate",
         "co146_boundary_append", "co77_closure_declaration_sweep", "co120_provenance_pin_gate", "co135_review_hygiene",
         "co136_gate_hygiene", "co78_layer_role_drift_gate", "co81_project_rules_gate", "co84_dru_domain_gate",
         "co95_in4_reachability", "co98_reachability_status_report", "co106_reference_plane_gate", "co146_boundary_append"]
# 允许非零的步骤（**须带 verdict 证据**：rc≠0 不等于预期 FAIL —— CO-165）
EXPECTED_NONZERO = {
    "co146_jlc_dfm_gate": {"verdict": "FAIL", "record": str(STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
                           "why": "verdict=FAIL（DFM 两项阻塞）属预期；rc=1 即 R-CO158-3/R-CO159-4 生效"},
}


def watch_paths() -> list:
    """CO-165（t08）：受控 sha 覆盖**全部**规范序会写入的产物（边界 + 全部 co*.json 记录 + 台账/登记簿 + 打样包件）。"""
    out = [STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md",
           L2 / "input_defect_register_v1.json", L2 / "derived_value_ledger_v1.json",
           K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/MANIFEST.json",
           K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package/ORDER_NOTES.md"]
    out += sorted(STEP2.glob("m13_v57_co*.json"))
    return out


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def record_verdict(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")).get("verdict")
    except Exception:
        return None


def allowlist_decision(step: str, rc: int, stderr: str, verdict, record_fresh: bool = True) -> str:
    """CO-165 核心判据（纯函数）：
    非白名单步：rc==0 ⇒ ok，否则 unexpected_nonzero；
    白名单步：须 rc≠0 **且** 无 Traceback **且** 记录由**本次执行**产出（mtime 新鲜）
              **且** 记录 verdict == 声明 verdict ⇒ expected_nonzero；
    其余 ⇒ expected_step_* 失败（**不得把崩溃 / 未产出记录（陈旧 verdict 从盘上读取）/ 错误判决当预期 FAIL**）。"""
    if step not in EXPECTED_NONZERO:
        return "ok" if rc == 0 else "unexpected_nonzero"
    exp = EXPECTED_NONZERO[step]
    if rc == 0:
        return "expected_step_returned_zero"
    if "Traceback (most recent call last)" in (stderr or ""):
        return "expected_step_crashed"
    if not record_fresh:
        return "expected_step_record_not_produced"
    if verdict != exp.get("verdict"):
        return "expected_step_verdict_mismatch"
    return "expected_nonzero"


def stable(prev: str, cur: str) -> bool:
    return bool(prev) and prev == cur


BOUNDARY = STEP2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"


def boundary_order_steps() -> list:
    """CO-164（t06）：从 boundary 最后一条 R-COxxx-3「规范复现序」行抽取步骤名（防文档序与执行器 ORDER 漂移）。"""
    if not BOUNDARY.exists():
        return []
    lines = [l for l in BOUNDARY.read_text(encoding="utf-8").splitlines() if "规范复现序 =" in l]
    if not lines:
        return []
    seg = lines[-1].split("规范复现序 =", 1)[1]
    out = []
    for tok in seg.replace("`", "").replace("**", "").split("→"):
        m = re.match(r"^([a-z0-9_]+)", tok.strip())   # 切掉尾注（如「，循环至 sha 稳定。」）
        t = m.group(1) if m else ""
        if re.match(r"^co\d", t):
            out.append(t)   # 不去重：`co146_boundary_append` 在序内合法出现两次
    return out


def tool_path(step: str) -> Path | None:
    direct = K2 / "tools" / f"p3_v57_{step}.py"
    if direct.exists():
        return direct
    cands = sorted((K2 / "tools").glob(f"p3_v57_{step}*.py"))
    return cands[0] if len(cands) == 1 else None


def snapshot() -> str:
    h = hashlib.sha256()
    for p in watch_paths():
        h.update(p.read_bytes() if p.exists() else b"<missing>")
    return h.hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="静态体检（不执行、不落盘）")
    ap.add_argument("--max-iter", type=int, default=5)
    a = ap.parse_args(argv)
    checks = {}
    # 静态体检：步骤文件存在 + 可编译 + rc 策略声明齐备
    missing, uncompilable = [], []
    for step in sorted(set(ORDER)):
        p = tool_path(step)
        if p is None:
            missing.append(step); continue
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except SyntaxError as e:
            uncompilable.append(f"{step}: {e}")
    checks["t01_steps_exist"] = not missing
    checks["t02_steps_compile"] = not uncompilable
    checks["t03_expected_nonzero_policy_declared"] = set(EXPECTED_NONZERO) <= set(ORDER)
    checks["t04_unexpected_nonzero_detected"] = (
        allowlist_decision("co78_layer_role_drift_gate", 1, "", None) == "unexpected_nonzero"
        and allowlist_decision("co77_closure_declaration_sweep", 0, "", "PASS") == "ok")
    # CO-165（t07）：白名单步的**伪通过**必须被拒（崩溃 / 意外归零 / verdict 不符 / 缺证据）
    checks["t07_allowlist_evidence_enforced"] = (
        allowlist_decision("co146_jlc_dfm_gate", 1, "Traceback (most recent call last):\n", "FAIL", True) == "expected_step_crashed"
        and allowlist_decision("co146_jlc_dfm_gate", 0, "", "FAIL", True) == "expected_step_returned_zero"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "PASS", True) == "expected_step_verdict_mismatch"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", False) == "expected_step_record_not_produced"
        and allowlist_decision("co146_jlc_dfm_gate", 1, "", "FAIL", True) == "expected_nonzero"
        and all(("verdict" in v and "record" in v) for v in EXPECTED_NONZERO.values()))
    # CO-165（t08）：受控 sha 覆盖全部记录类产物（非窄清单）
    _w = [p.as_posix() for p in watch_paths()]
    checks["t08_watch_covers_records"] = (len(_w) >= 20
                                          and any(p.endswith("m13_v57_co106_reference_plane_gate.json") for p in _w)
                                          and any(p.endswith("jlc_package/MANIFEST.json") for p in _w))
    checks["t05_stability_oracle"] = (stable("x", "x") and not stable("x", "y") and not stable("", ""))
    # CO-164（t06）：执行器 ORDER 必须与 boundary 规范复现序**有序一致**（文档↔执行器防漂移）
    _bdy = boundary_order_steps()
    checks["t06_order_matches_boundary"] = bool(_bdy) and _bdy == ORDER
    static_ok = all(checks.values())
    if a.check:
        print(json.dumps({"mode": "check", "checks": checks, "missing": missing,
                          "uncompilable": uncompilable, "ok": static_ok}, ensure_ascii=False, indent=1))
        return 0 if static_ok else 1
    if not static_ok:
        print(json.dumps({"mode": "run", "aborted": "static_precheck_failed", "checks": checks,
                          "missing": missing, "uncompilable": uncompilable}, ensure_ascii=False, indent=1))
        return 1
    # ── 执行：每轮逐步跑，rc 不合规立即停机 ─────────────────────────────────
    iterations, abort = [], None
    prev = ""
    converged = False
    for it in range(1, a.max_iter + 1):
        rcs, unexpected = {}, None
        for step in ORDER:
            p = tool_path(step)
            t0 = time.time()
            _exp = EXPECTED_NONZERO.get(step) or {}
            r = subprocess.run([str(PY), str(p)], cwd=K2, capture_output=True, text=True)
            _fresh = False
            if _exp.get("record"):
                try:
                    _fresh = Path(_exp["record"]).stat().st_mtime >= (t0 - 1.0)   # CO-165：记录须由本次执行产出
                except OSError:
                    _fresh = False
            cls = allowlist_decision(step, r.returncode, r.stderr, record_verdict(_exp.get("record")), _fresh)
            rcs[step] = {"rc": r.returncode, "class": cls}
            if cls not in ("ok", "expected_nonzero"):
                unexpected = {"step": step, "rc": r.returncode, "class": cls,
                              "stderr_tail": (r.stderr or "")[-600:]}
                break
        cur = snapshot()
        iterations.append({"iter": it, "rcs": rcs, "sha": cur, "unexpected": unexpected})
        if unexpected:
            abort = unexpected
            break
        if stable(prev, cur):
            converged = True
            break
        prev = cur
    report = {"artifact": "m13_v57_co164_order_runner_report", "schema": 1, "revision": "CO-164.2",
              "nature": "规范复现序机判执行器（rc 策略 + 真收敛判定）；报告落 .archer_tmp/ 且**不被 boundary 引用**（避免不动点）",
              "order": ORDER, "expected_nonzero": EXPECTED_NONZERO,
              "checks": checks, "iterations": iterations, "abort": abort, "converged": converged,
              "watched": [str(p.relative_to(K2)) for p in watch_paths()],
              "redline": "只读工具源；执行序内写记录/边界（即规范序本身）；本报告不参与 pin 表。"}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"mode": "run", "converged": converged, "abort": abort,
                      "iterations": len(iterations), "checks": checks,
                      "report": str(REPORT.relative_to(K2))}, ensure_ascii=False, indent=1))
    return 0 if (converged and not abort) else 1


if __name__ == "__main__":
    sys.exit(main())
