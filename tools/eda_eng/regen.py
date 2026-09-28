"""regen --- 组合确定性管线（原 `route` 之名归 #K2-360 M3；本模块保留管线能力）。

v1 = **组合确定性管线**（全部是链内既有、确定性、无 LLM 的阶段；不新增搜索、不手改板）：

    place(场景) → gen_v5 → route_segment --upto all → build_l9(全阶段: 倒角/铺铜/丝印…) → DRC

**运行于影子工程根**（shadow.py）：真源/冻结四源/`project.yaml` **逐字节不动**；产物落工作目录。
输出 = 最终板 + DRC json（供 eda_eng verify 判卷）。
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys

from . import shadow as shadow_mod

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _py():
    """KiCad python（有 pcbnew）；env 在**调用时**读，避免 import 期固化。"""
    return os.environ.get("EDA_ENG_PY") or sys.executable


def _cli():
    return os.environ.get("EDA_ENG_CLI", "kicad-cli")


def _host():
    """宿主 python（有 yaml 等常规依赖）：gen_v5 是纯 python 生成器，不需要 pcbnew。"""
    return os.environ.get("EDA_ENG_HOST_PY", "python3")

STAGES = ["place", "gen", "route", "polish", "drc"]

EXAM_PRESET = {
    # RE-POSED by #K2-361 sec.2.3 (ECO-K2-0002 v2): translation-only family, +X 4.000 mm (0.400 mm margin
    # under the measured 4.400 mm bound); the old +5.000 mm scenario is refuted by the R940 certificate.
    "A": {"spec_name": None, "placement": {"refs": ["U1", "U2", "U4", "U5"], "delta_mm": [4.0, 0.0]},
          "drawing": None},
    "B": {"spec_name": "SPEC_k2_v4.spec-rev-62.json", "placement": None,
          "drawing": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_H4CLEAR_v3.json"},
}


KICAD_ENV_KEYS = ("LD_LIBRARY_PATH", "PYTHONPATH", "PYTHONHOME")


def _host_env(env):
    """给宿主 python（gen_v5）的干净 env：剥掉 KiCad 专属的库/路径变量（否则宿主 python 起不来）。"""
    e = {k: v for k, v in env.items() if k not in KICAD_ENV_KEYS}
    return e


def _run(cmd, env, log):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, timeout=3600)
    log.append({"cmd": " ".join(cmd), "exit": p.returncode, "tail": (p.stdout or p.stderr or "")[-400:]})
    return p.returncode


def run_exam(exam_id, work, dry=False, log_only=True):
    preset = EXAM_PRESET[exam_id]
    os.makedirs(work, exist_ok=True)
    pf = None if dry else preflight(exam_id, work)      # dry 路径不设闸（避免 preflight<->run 递归）
    if (not dry) and (pf is None or not pf["ok"]):
        return {"artifact": "eda_eng_route", "exam": exam_id, "state": "REFUSED_BY_PREFLIGHT",
                "preflight": pf, "log": [], "rule": "C29 fail-closed: an illegal/stale scenario must not burn a run"}
    plan = {"artifact": "eda_eng_route", "exam": exam_id, "engine": "composed-deterministic-pipeline-v1",
            "stages": STAGES, "work": work, "dry_run": dry, "log": []}
    sh = shadow_mod.build(os.path.join(work, "shadow"), spec_name=preset["spec_name"],
                          replace=("placement", "project_yaml") if preset["spec_name"] else ("placement",))
    plan["shadow"] = sh
    if preset["placement"]:
        plan["placement_edit"] = shadow_mod.edit_placement_at(sh["shadow_root"], **preset["placement"])
    stage1 = os.path.join(work, "stage1.kicad_pcb")
    stage2 = os.path.join(work, "stage2.kicad_pcb")
    final = os.path.join(work, "final.kicad_pcb")
    env = {**os.environ, "PM_GATE_PROJECT_ROOT": sh["shadow_root"],
           "K2_OUT_PCB": stage1, "K2_OUT_JSON": os.path.join(work, "stage1.json")}
    if preset["drawing"]:
        env["L4_MAIN"] = os.path.join(ROOT, preset["drawing"])
    cmds = {
        "gen": [_host(), os.path.join(ROOT, "tools", "k2_gen_v5.py")],
        "route": [_py(), os.path.join(ROOT, "tools", "k2_route_segment_v1.py"), "--in", stage1,
                  "--out", stage2, "--upto", "all", "--drc-cli", _cli()],
        "polish": [_py(), os.path.join(ROOT, "tools", "k2_p4_build_l9_v1.py"), "--in", stage2, "--out", final,
                   "--stages", "fiducial,info,edge,tp,crtyd,silk,silkfix,chamfer,pour"],
        "drc": [_cli(), "pcb", "drc", "--format", "json", "--severity-all", "-o",
                os.path.join(work, "final_drc.json"), final],
    }
    plan["commands"] = {k: " ".join(v) for k, v in cmds.items()}
    if dry:
        plan["state"] = "PLANNED"; return plan
    for st in ("gen", "route", "polish", "drc"):
        use_env = _host_env(env) if st == "gen" else env
        rc = _run(cmds[st], use_env, plan["log"])
        plan["log"][-1]["stage"] = st
        if rc != 0:
            plan["state"] = "FAILED_AT_" + st
            return plan
    plan.update({"state": "RAN", "final_board": final,
                 "drc": os.path.join(work, "final_drc.json"),
                 "exists": {p: os.path.isfile(p) for p in (stage1, stage2, final)}})
    return plan


STATUS = {"implemented": True, "engine": "composed-deterministic-pipeline-v1",
          "entry": "route --exam A|B [--work DIR] [--dry-run]",
          "note": "runs in a shadow project root; the real tree, project.yaml and the frozen four are never touched"}


def validate_placement(refs, delta_mm, work):
    """放置可行性校验（引擎能力）：影子根 + 施加场景 + **只跑 gen_v5 的放置自检**。
    返回 {ok, reason} —— 不布线、不产板；用于在考题场景被批准前先证明"新放置本身合法"。"""
    import shutil
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work, exist_ok=True)
    sh = shadow_mod.build(os.path.join(work, "shadow"))
    shadow_mod.edit_placement_at(sh["shadow_root"], refs, delta_mm)
    env = {**os.environ, "PM_GATE_PROJECT_ROOT": sh["shadow_root"],
           "K2_OUT_PCB": os.path.join(work, "probe.kicad_pcb"), "K2_OUT_JSON": os.path.join(work, "probe.json")}
    p = subprocess.run([_host(), os.path.join(ROOT, "tools", "k2_gen_v5.py")], cwd=ROOT,
                       capture_output=True, text=True, env=_host_env(env), timeout=600)
    tail = (p.stdout or p.stderr or "").strip().splitlines()
    reason = next((l for l in reversed(tail) if "写盘阻断" in l or "S1" in l), tail[-1] if tail else "")
    return {"refs": refs, "delta_mm": delta_mm, "ok": p.returncode == 0, "reason": reason[-200:]}


def preflight(exam, work):
    """#K2-361 sec.4 (C29 补法): 开工前置闸 —— P1 场景合法性 ＋ P2 干跑计划 ＋ 输入哈希；未过即停（不跑重活）。"""
    import hashlib
    preset = EXAM_PRESET.get(exam)
    if preset is None:
        return {"ok": False, "reason": "unknown exam"}
    w = os.path.join(work, "preflight")
    p1 = {"skipped": True}
    if preset["placement"]:
        p1 = validate_placement(preset["placement"]["refs"], preset["placement"]["delta_mm"], w + "_p1")
    p2 = run(exam, work, dry=True)
    inputs = {"spec_name": preset.get("spec_name") or "SPEC_k2_v4.spec-rev-61.json",
              "drawing": preset.get("drawing") or "canonical m13_v57_w3_joint_assignment.json",
              "placement_source": "pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json"}
    hashes = {}
    for k, rel in (("placement", os.path.join(ROOT, inputs["placement_source"])),
                   ("drawing", inputs["drawing"] if preset.get("drawing") else
                    os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment.json"))):
        hashes[k] = hashlib.sha256(open(rel, "rb").read()).hexdigest()[:16] if os.path.isfile(rel) else None
    # P1' 机械/库类闸（本窗新证）：跑一次 gen（只放置）+ DRC —— 机械非法（courtyard 重叠等）场景**零重活**拦下
    p1b = {"checked": False}
    if preset["placement"] and p1.get("ok"):
        gw = os.path.join(work, "p1gen")
        shutil.rmtree(gw, ignore_errors=True)
        os.makedirs(gw, exist_ok=True)
        sh = shadow_mod.build(os.path.join(gw, "shadow"))
        shadow_mod.edit_placement_at(sh["shadow_root"], preset["placement"]["refs"], preset["placement"]["delta_mm"])
        gpcb = os.path.join(gw, "placed.kicad_pcb")
        env = {**os.environ, "PM_GATE_PROJECT_ROOT": sh["shadow_root"], "K2_OUT_PCB": gpcb,
               "K2_OUT_JSON": os.path.join(gw, "placed.json")}
        rc = subprocess.run([_host(), os.path.join(ROOT, "tools", "k2_gen_v5.py")], cwd=ROOT,
                            capture_output=True, text=True, env=_host_env(env), timeout=600).returncode
        gj = os.path.join(gw, "placed_drc.json")
        subprocess.run([_cli(), "pcb", "drc", "--format", "json", "--severity-all", "-o", gj, gpcb],
                       capture_output=True, timeout=900)
        bad = {}
        if os.path.isfile(gj):
            for v in json.load(open(gj, encoding="utf-8")).get("violations", []):
                ty = v.get("type")
                if ty in ("courtyards_overlap", "shorting_items", "clearance", "hole_clearance"):
                    bad[ty] = bad.get(ty, 0) + 1
        p1b = {"checked": True, "gen_exit": rc, "mechanical_violations": bad,
               "rule": "a placement that is pad-legal but mechanical-illegal (e.g. courtyards_overlap) must be "
                       "refused here with zero heavy runs (found by exam A attempt 1)"}
    ok = (p1.get("ok") is True or p1.get("skipped")) and p1b.get("mechanical_violations", {}) == {} \
        and bool(p2.get("commands")) and all(hashes.values())
    return {"artifact": "eda_eng_preflight", "exam": exam, "ok": ok,
            "P1_scenario_legality": p1, "P1b_mechanical_legality": p1b, "P2_dry_run_plan": {"stages": p2.get("stages"), "commands": p2.get("commands")},
            "inputs": inputs, "input_hashes_sha16": hashes,
            "rule": "#K2-361 sec.4 (C29): no heavy stage may run unless the pre-flight passes (fail-closed)"}


def run(exam=None, work=None, dry=False):
    if exam in EXAM_PRESET:
        return run_exam(exam, work or os.path.join("/tmp/opencode/eda_eng", "exam" + exam), dry=dry)
    return {"status": "NEED_EXAM", **STATUS}
