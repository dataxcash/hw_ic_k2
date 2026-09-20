#!/usr/bin/env python3
"""k2_p6_readonly_baseline_v1.py — P6/学习环批 2「改前」基线捕获器（只读）。

目的（#K2-40 §四-1 的「可复现验收命令」+ inc119 handoff §7-1 的 before/after 判据）：
  在 **不修改任何载体**（不 set_gate / 不 save state / 不重建包 / 不触 criteria）的前提下，
  实测并固化 **pm_gate 各 check 在 K1 / K2 两个项目维度的现状读数**，供 B2-1..B2-4 升版后对比。

只读保证：
  - 仅调用 `pm_gate.check_*` 的纯函数（返回 GateResult），**不调用** cli 的 cmd_run/cmd_run_all
    （后者会 st.save 写 state_*.json）；
  - 仅读文件；唯一写盘动作是 `--out` 指定的输出件（默认 stdout）；
  - `os.chdir` 仅用于满足项目根探测（M-14 基址口径），退出时复原。

确定性：输出无时间戳、键排序、列表排序 ⇒ **同一输入两次连跑逐字节同**（可入库判据）。

标准复现命令（容器根 ic_hw）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
      k2/tools/k2_p6_readonly_baseline_v1.py --out /tmp/opencode/k2_p6_k1_baseline.json
  # pcbnew 属 KiCad python，只有 AppDir 解释器可用 ⇒ G3.5 等项须用上解释器才不是 ENV 缺件
退出码：0 = 基线已产出（**不代表门禁全绿**）；2 = 基础设施错误（找不到项目/框架）。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECTS = (("k1", os.path.join(REPO, "k1")), ("k2_v4", os.path.join(REPO, "k2")))
GATE_MODULES = ("check_l1", "check_l2", "check_l3", "check_qa")
GATE_RE = re.compile(r"check_g\d+$")
PYTESTERS = ("_shared/eda_core/tests/test_hs_route_model.py",)
COMPILE_TARGETS = (
    "_shared/eda_core/hs_route_model.py",
    "_shared/pm_gate/check_l1.py",
    "_shared/pm_gate/check_l2.py",
    "_shared/pm_gate/check_l3.py",
    "_shared/pm_gate/check_qa.py",
)
ANCHOR_FILES = {
    "board_l4_frozen": "k2/hw/k2_v4_8L.l4.kicad_pcb",
    "board_design_source": "k2/hw/k2_v4_8L.kicad_pcb",
    "nets_source": "k2/hw/data/k2_sch.yaml",
    "board_reviewed_l7": "k2/hw/k2_v4_8L.l7.kicad_pcb",
    "delivery_manifest": "k2/pm_gate/artifacts/k2_v4/L6/jlc_package/MANIFEST.json",
    "delivery_tarball": "k2/pm_gate/artifacts/k2_v4/L6/DELIVERY/k2_v4_8L.l7_gerber_package.tar.gz",
}


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_hits(root: str, needle: str, exts=(".py",)) -> list:
    hits = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for fn in sorted(files):
            if not fn.endswith(exts):
                continue
            p = os.path.join(base, fn)
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh, 1):
                        if needle in line:
                            hits.append(f"{os.path.relpath(p, REPO)}:{i}")
            except OSError:
                continue
    return sorted(hits)


def _purge_pm_gate_modules() -> None:
    for name in [m for m in sys.modules if m == "pm_gate" or m.startswith("pm_gate.")]:
        del sys.modules[name]


def probe_project(project: str, proj_root: str, framework_root: str) -> dict:
    """只读探测单个项目维度；返回确定性 dict。"""
    cwd0 = os.getcwd()
    os.environ["PM_GATE_PROJECT_ROOT"] = proj_root
    _purge_pm_gate_modules()
    for extra in (framework_root, proj_root):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    out: dict = {"project": project, "project_root": os.path.relpath(proj_root, REPO)}
    try:
        os.chdir(proj_root)
        artifacts = importlib.import_module("pm_gate.artifacts")
        config = importlib.import_module("pm_gate.config")
        artifacts.set_active_project(project)
        out["active_project"] = artifacts.active_project()
        try:
            out["discovered_project_root"] = artifacts.discover_project_root()
        except Exception as exc:  # pragma: no cover
            out["discovered_project_root"] = f"EXC {type(exc).__name__}: {exc}"

        # ── SPEC 名解析探针（B2-3：硬编码 vs 项目配置）──
        spec_active = config.spec_name(project)
        out["spec_name_probe"] = {
            "default_call": config.spec_name(),          # check_qa.py:35 的调用形式
            "active_call": spec_active,                  # 应然形式
            "active_spec_artifact": f"pm_gate/artifacts/{project}/L3/{spec_active}",
            "active_spec_artifact_exists": os.path.isfile(
                os.path.join(proj_root, "pm_gate", "artifacts", project, "L3", spec_active)),
            "k2_spec_artifact": f"pm_gate/artifacts/{project}/L3/SPEC_k2_v4.json",
            "k2_spec_artifact_exists": os.path.isfile(
                os.path.join(proj_root, "pm_gate", "artifacts", project, "L3", "SPEC_k2_v4.json")),
        }

        # ── G1.5 规则文档路径探针（B2-4）──
        l1 = importlib.import_module("pm_gate.check_l1")
        resolved = getattr(l1, "RULES_DOC", None)
        out["rules_doc_probe"] = {
            "resolved": resolved,
            "exists": bool(resolved) and os.path.isfile(resolved),
        }

        # ── 闭包门（G3.5）默认路径探针（B2-3：框架相对默认值 = M-14 违反）──
        try:
            cc = importlib.import_module("pm_gate.closure_check")
            out["closure_check_defaults_probe"] = {
                "DEFAULT_SPEC": getattr(cc, "DEFAULT_SPEC", None),
                "DEFAULT_SPEC_exists": os.path.isfile(getattr(cc, "DEFAULT_SPEC", "") or ""),
                "ESCAPE_SPEC_PATH": getattr(cc, "ESCAPE_SPEC_PATH", None),
                "ESCAPE_SPEC_PATH_exists": os.path.isfile(getattr(cc, "ESCAPE_SPEC_PATH", "") or ""),
            }
        except Exception as exc:
            out["closure_check_defaults_probe"] = {"exception": f"{type(exc).__name__}: {exc}"}

        # ── 已记录的 state_*.json 读数（before/after：B2-4 撤 waiver 的判据）──
        state_path = os.path.join(proj_root, "pm_gate", f"state_{project}.json")
        recorded: dict = {"path": os.path.relpath(state_path, REPO), "exists": os.path.isfile(state_path)}
        if recorded["exists"]:
            st = json.load(open(state_path, encoding="utf-8"))
            gates: dict = {}
            for stage, sv in sorted(st.get("stages", {}).items()):
                for gid, g in sorted(sv.get("gates", {}).items()):
                    ev = str(g.get("evidence") or "")
                    gates[gid] = {"stage": stage, "status": g.get("status"),
                                  "is_waiver": ev.startswith("WAIVER"),
                                  "checked_at": g.get("checked_at"),
                                  "evidence_head": ev[:160]}
            recorded["gates"] = gates
            recorded["waived_gates"] = sorted(k for k, v in gates.items() if v["is_waiver"])
        out["recorded_state"] = recorded

        # ── 各门禁 check 现状读数（纯函数，不写 state）──
        for modname in GATE_MODULES:
            mod = importlib.import_module("pm_gate." + modname)
            gates: dict = {}
            for fn in sorted(n for n in dir(mod) if GATE_RE.match(n)):
                try:
                    res = getattr(mod, fn)()
                    gates[fn] = {
                        "passed": bool(res.passed),
                        "evidence": res.evidence or "",
                        "errors": list(res.errors or []),
                    }
                except BaseException as exc:  # 记录而非崩溃：ENV 缺件须可见（fail-closed 可见性）
                    gates[fn] = {
                        "passed": None,
                        "evidence": "",
                        "errors": [],
                        "exception": f"{type(exc).__name__}: {exc}",
                    }
            out[modname] = gates
        return out
    finally:
        os.chdir(cwd0)


def run_pytest() -> dict:
    py = os.environ.get("K2_BASELINE_PYTEST_PYTHON") or sys.executable
    cmd = [py, "-m", "pytest", "-q", *PYTESTERS]
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PM_GATE_PROJECT_ROOT")}
    try:
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=1800, env=env)
        tail = (proc.stdout + proc.stderr).strip().splitlines()
        # 去易变项（墙钟耗时）⇒ 输出可逐字节复现
        tail = [re.sub(r"\s+in\s+[\d.]+s\s*$", "", line) for line in tail]
        counts = {"passed": 0, "skipped": 0, "failed": 0, "error": 0}
        for line in tail:
            for key in counts:
                m = re.search(rf"(\d+) {key}\b", line)
                if m:
                    counts[key] = int(m.group(1))
        if proc.returncode != 0:
            counts = dict(counts, crash_tail=" | ".join(tail[-3:]))
        return {"cmd": " ".join(cmd), "interpreter": py, "exit_code": proc.returncode,
                "counts": counts, "last_line": tail[-1] if tail else ""}
    except Exception as exc:
        return {"cmd": " ".join(cmd), "exit_code": None, "counts": {}, "error": f"{type(exc).__name__}: {exc}"}


def run_py_compile() -> dict:
    cmd = [sys.executable, "-m", "py_compile", *COMPILE_TARGETS]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    return {"cmd": "python3 -m py_compile " + " ".join(COMPILE_TARGETS),
            "exit_code": proc.returncode,
            "ok": f"{len(COMPILE_TARGETS)}/{len(COMPILE_TARGETS)}" if proc.returncode == 0 else "FAIL",
            "stderr_tail": proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ""}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="输出 JSON 路径（缺省 = stdout）")
    ap.add_argument("--project", default=None, help="仅探某项目（k1 / k2_v4；缺省 = 两个都探）")
    args = ap.parse_args()

    framework_root = os.path.join(REPO, "_shared")
    if not os.path.isdir(os.path.join(framework_root, "pm_gate")):
        print(f"INFRA ERROR: 框架根不存在 {framework_root}/pm_gate", file=sys.stderr)
        return 2

    doc: dict = {
        "artifact": "k2_p6_readonly_pm_gate_baseline",
        "schema": 1,
        "purpose": "P6/学习环批2 的改前基线（#K2-40 §四-1 可复现验收命令；inc119 §7-1 before/after）",
        "readonly": True,
        "writes": "仅 --out 输出件；不 set_gate / 不 save state / 不触 criteria / 不重建包",
        "interpreter": {"sys_executable": sys.executable, "version": sys.version.split()[0],
                        "pcbnew_available": _has_pcbnew()},
        "framework_root": os.path.relpath(framework_root, REPO),
        "anchors": {},
    }

    for name, rel in sorted(ANCHOR_FILES.items()):
        abs_p = os.path.join(REPO, rel)
        doc["anchors"][name] = {
            "path": rel,
            "exists": os.path.isfile(abs_p),
            "sha256": sha256_of(abs_p) if os.path.isfile(abs_p) else None,
        }

    doc["spec_k2_v4_census"] = {
        "needle": "SPEC_k2_v4",
        "scope": "_shared (py, no __pycache__)",
        "count": None,
        "hits": [],
    }
    hits = walk_hits(framework_root, "SPEC_k2_v4")
    doc["spec_k2_v4_census"]["hits"] = hits
    doc["spec_k2_v4_census"]["count"] = len(hits)
    doc["spec_k2_v4_census"]["count_pm_gate_only"] = len([h for h in hits if "pm_gate/" in h])

    doc["pytest_baseline"] = run_pytest()
    doc["py_compile_baseline"] = run_py_compile()

    projects = {}
    for project, proj_root in PROJECTS:
        if args.project and project != args.project:
            continue
        projects[project] = probe_project(project, proj_root, framework_root)
    doc["projects"] = projects

    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"written {args.out} ({len(text)} B)")
    else:
        sys.stdout.write(text)
    return 0


def _has_pcbnew() -> bool:
    try:
        import pcbnew  # noqa: F401
        return True
    except BaseException:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
