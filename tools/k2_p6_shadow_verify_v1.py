#!/usr/bin/env python3
"""k2_p6_shadow_verify_v1.py — 批 2 补丁集的**影子预验证**（真源零改动，授权前"一次跑成"验证）。

做三件事（全部落在 /tmp/opencode）：
  ① 在 /tmp 建影子框架（k2/_shared 拷贝）并施加**批 2 补丁集候选**（F-1/B2-3a/b/c/d + 影子专用测试锚）；
  ② 跑**同一套**验收：K1/K2 两维度 pm_gate 门禁读数 + `test_hs_route_model.py`（含解锁 22 个隐藏用例）；
  ③ 建**控制组**（零 pm_gate 补丁、仅同一测试锚）跑同一测试 ⇒ **归因**（补丁集是否引入回归）。

真源保证：只读 `k2/_shared`；所有编辑/产物在 /tmp；`--out` 缺省写 P6_execution/SHADOW_VERIFY_v1.json。
确定性：无时间戳、去墙钟 ⇒ 两次连跑逐字节同（pytest 数量类）。
用法（容器根 ic_hw）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p6_shadow_verify_v1.py
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "k2", "_shared")
SHADOW = "/tmp/opencode/shadow"
CTL = "/tmp/opencode/shadow_ctl"
BOARD_8L = os.path.join(REPO, "k2", "k2_v4_8L.kicad_pcb")
BOARD_HW = os.path.join(REPO, "k2", "hw", "k2_v4_8L.kicad_pcb")
TEST_REL = "eda_core/tests/test_hs_route_model.py"
DEF_OUT = os.path.join(REPO, "k2", "pm_gate", "artifacts", "k2_v4", "P6_execution", "SHADOW_VERIFY_v1.json")
NEW_TEST_ANCHOR_FMT = 'K2V4_REAL_BOARD = Path("{board}")  # SHADOW-ONLY'

PROJ_HELPER = '''

def _proj() -> str:
    """B2-3：当前门禁项目（T13 口径：cli 经 artifacts.set_active_project 注入）。"""
    return artifacts.active_project()
'''
CALL_RE = re.compile(r'(artifacts\.(?:read_text|list_dir|path|file_exists)\((?:[^()]|\([^()]*\))*?)\)')


def _patch(rel, old, new, patches, root):
    p = os.path.join(root, "shared", rel)
    s = open(p, encoding="utf-8").read()
    assert old in s, f"PATCH MISS {rel}"
    open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
    patches.append({"file": rel, "note": new if False else rel})


def build_shadow(root: str, board_abs: str, apply_batch2: bool) -> list:
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root, exist_ok=True)
    shutil.copytree(SRC, os.path.join(root, "shared"), ignore=shutil.ignore_patterns(".git", "__pycache__"))
    for n in ("AppDir", "k2", "criteria", "k1", ".omo"):
        os.symlink(os.path.join(REPO, n), os.path.join(root, n))
    os.symlink(os.path.join(root, "shared"), os.path.join(root, "_shared"))
    patches: list = []

    if apply_batch2:
        _patch("pm_gate/check_l1.py",
               'RULES_DOC = os.path.join(os.path.dirname(os.path.dirname(\n    os.path.dirname(os.path.abspath(__file__)))), "..", "doc",\n    "PCB_DESIGN_RULES.md")',
               'RULES_DOC = os.path.join(os.path.dirname(os.path.dirname(\n    os.path.abspath(__file__))), "docs", "PCB_DESIGN_RULES.md")',
               patches, root)
        patches[-1]["note"] = "F-1/B2-4：RULES_DOC → <框架根>/docs/PCB_DESIGN_RULES.md"
        for rel, expect, note in (("pm_gate/check_l2.py", 9, "B2-3：项目维度注入（L2 产物读取）"),
                                  ("pm_gate/check_l3.py", 4, "B2-3：项目维度注入（L3 产物读取）"),
                                  ("pm_gate/check_qa.py", 2, "B2-3：项目维度注入（QA 产物读取）")):
            p = os.path.join(root, "shared", rel)
            s = open(p, encoding="utf-8").read()
            hits = CALL_RE.findall(s)
            s = CALL_RE.sub(lambda m: m.group(0) if "project=" in m.group(1) else m.group(1) + ", project=_proj())", s)
            if "_proj() -> str" not in s:
                i = s.index("from .gates import")
                j = s.index("\n", i) + 1
                s = s[:j] + PROJ_HELPER + s[j:]
            open(p, "w", encoding="utf-8").write(s)
            assert len(hits) >= expect
            patches.append({"file": rel, "note": f"{note}（{len(hits)} 处）"})
        _patch("pm_gate/check_l3.py", 'artifacts.read_text("L3", "SPEC_k2_v4.json", project=_proj())',
               'artifacts.read_text("L3", config.spec_name(_proj()), project=_proj())', patches, root)
        patches[-1]["note"] = "B2-3a：check_l3 去硬编码 SPEC 名（经 project.yaml: spec_name）"
        _patch("pm_gate/check_l3.py", "from . import artifacts\n", "from . import artifacts, config\n", patches, root)
        patches[-1]["note"] = "B2-3a：check_l3 引入 config"
        _patch("pm_gate/check_qa.py", 'artifacts.read_text("L3", config.spec_name(), project=_proj())',
               'artifacts.read_text("L3", config.spec_name(_proj()), project=_proj())', patches, root)
        patches[-1]["note"] = "B2-3b：check_qa spec_name(active)（原空参取 DEFAULT_PROJECT）"
        _patch("pm_gate/check_qa.py", "    return config.board_abspath()", "    return config.board_abspath(_proj())", patches, root)
        patches[-1]["note"] = "B2-3c（新 F-2c）：check_qa 板路径 board_abspath(active)"
        _patch("pm_gate/gates.py", "        text = artifacts.read_text(stage, *parts)",
               "        text = artifacts.read_text(stage, *parts, project=artifacts.active_project())", patches, root)
        patches[-1]["note"] = "B2-3d（新 F-2d）：scheme_closure_check 注入项目维度"
        _patch("pm_gate/closure_check.py",
               'DEFAULT_SPEC = os.path.join(os.path.dirname(os.path.abspath(__file__)),\n                            "artifacts", "L3", "SPEC_k2_v4.json")\nESCAPE_SPEC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),\n                                "artifacts", "L2", "escape_spec.json")',
               'def _project_artifact(*parts: str) -> str:\n    """默认路径钉到当前项目根（M-14 口径）。"""\n    from pm_gate import artifacts\n    return artifacts.path(*parts, project=artifacts.active_project())\n\n\ndef _project_spec_name() -> str:\n    from pm_gate import artifacts, config\n    return config.spec_name(artifacts.active_project())\n\n\nDEFAULT_SPEC = _project_artifact("L3", _project_spec_name())\nESCAPE_SPEC_PATH = _project_artifact("L2", "escape_spec.json")',
               patches, root)
        patches[-1]["note"] = "F-3/B2-3c：closure_check 默认值 → 项目根（原指向不存在的框架 artifacts/）"

    # 影子/控制**共用**：测试板锚（真源提案另议，此处仅为跑出隐藏结果）
    p = os.path.join(root, "shared", TEST_REL)
    s = open(p, encoding="utf-8").read()
    old = 'K2V4_REAL_BOARD = REPO / "k2_v4.kicad_pcb"'
    assert old in s
    open(p, "w", encoding="utf-8").write(s.replace(old, NEW_TEST_ANCHOR_FMT.format(board=board_abs), 1))
    patches.append({"file": TEST_REL, "note": f"SHADOW-ONLY 测试板锚 → {board_abs}"})
    return patches


def gate_battery(root: str) -> dict:
    """影子框架下的 K1/K2 pm_gate 只读读数（in-process，逐项目 chdir 复原）。"""
    out = {}
    cwd0 = os.getcwd()
    for project, proj_root in (("k1", os.path.join(REPO, "k1")), ("k2_v4", os.path.join(REPO, "k2"))):
        os.environ["PM_GATE_PROJECT_ROOT"] = proj_root
        for m in [m for m in sys.modules if m == "pm_gate" or m.startswith("pm_gate.")]:
            del sys.modules[m]
        sys.path.insert(0, os.path.join(root, "shared"))
        os.chdir(proj_root)
        from pm_gate import artifacts
        artifacts.set_active_project(project)
        res = {}
        for modname in ("check_l1", "check_l2", "check_l3", "check_qa"):
            mod = importlib.import_module("pm_gate." + modname)
            for fn in sorted(n for n in dir(mod) if re.fullmatch(r"check_g\d+", n)):
                try:
                    r = getattr(mod, fn)()
                    res[fn] = {"status": "PASS" if r.passed else "FAIL",
                               "detail": (r.errors[0] if r.errors else (r.evidence or ""))[:120]}
                except BaseException as exc:
                    res[fn] = {"status": "EXC", "detail": f"{type(exc).__name__}: {exc}"}
        out[project] = res
    os.chdir(cwd0)
    return out


def run_pytest(root: str) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("PM_GATE_PROJECT_ROOT",)}
    env["PYTHONPATH"] = os.path.join(root, "shared")
    cmd = [sys.executable, "-m", "pytest", "-q", "-rf", "-p", "no:cacheprovider",
           os.path.join(root, "shared", TEST_REL)]
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, env=env, timeout=1800)
    text = re.sub(r"\s+in\s+[\d.]+s\s*$", "", proc.stdout, flags=re.M)
    m = re.search(r"(?:(\d+) failed, )?(\d+) passed(?:, (\d+) skipped)?", text)
    failed = re.findall(r"^FAILED \S+::(\S+)", text, re.M)
    reasons = sorted(set(re.findall(r"^E\s+(.{0,120})$", text, re.M)))
    counts = {"failed": int(m.group(1) or 0) if m else None, "passed": int(m.group(2)) if m else None,
              "skipped": int(m.group(3) or 0) if m else None}
    return {"counts": counts, "failed_tests": sorted(failed), "failure_lines": reasons[:40],
            "exit_code": proc.returncode}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEF_OUT)
    ap.add_argument("--board", default=BOARD_8L, help="测试板锚（默认 k2/k2_v4_8L.kicad_pcb）")
    args = ap.parse_args()

    doc = {
        "artifact": "k2_p6_shadow_verify",
        "schema": 1,
        "purpose": "批 2 补丁集的影子预验证（真源零改动）+ 22 skip 解锁实验 + 控制组归因",
        "readonly_repo": True,
        "shadow_root": SHADOW, "control_root": CTL,
        "board_anchor": os.path.relpath(args.board, REPO),
        "patch_set": build_shadow(SHADOW, args.board, apply_batch2=True),
        "gate_battery_shadow": gate_battery(SHADOW),
        "pytest_shadow": run_pytest(SHADOW),
    }
    build_shadow(CTL, args.board, apply_batch2=False)   # 控制组：零 pm_gate 补丁
    doc["pytest_control_no_patchset"] = run_pytest(CTL)
    doc["attribution"] = {
        "same_result": doc["pytest_shadow"]["counts"] == doc["pytest_control_no_patchset"]["counts"],
        "reading": "两组计数相同 ⇒ 批 2 补丁集**零测试回归**；失败为**既有隐藏缺陷**（原被 skip 掩盖）",
    }
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    gb = doc["gate_battery_shadow"]
    print("patch_set:", len(doc["patch_set"]), "项")
    for proj, res in gb.items():
        n = {s: sum(1 for v in res.values() if v["status"] == s) for s in ("PASS", "FAIL", "EXC")}
        print(f"  {proj}: {n}")
    print("pytest shadow :", doc["pytest_shadow"]["counts"])
    print("pytest control:", doc["pytest_control_no_patchset"]["counts"])
    print("→", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
