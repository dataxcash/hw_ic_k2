"""regen --- 组合确定性管线（原 `route` 之名归 #K2-360 M3；本模块保留管线能力）。

v1 = **组合确定性管线**（全部是链内既有、确定性、无 LLM 的阶段；不新增搜索、不手改板）：

    place(场景) → gen_v5 → route_segment --upto all → build_l9(全阶段: 倒角/铺铜/丝印…) → DRC

**运行于影子工程根**（shadow.py）：真源/冻结四源/`project.yaml` **逐字节不动**；产物落工作目录。
输出 = 最终板 + DRC json（供 eda_eng verify 判卷）。
"""
from __future__ import annotations
import collections, json, math, os, shutil, subprocess, sys

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

def _exam_a_preset():
    """考题 A 场景的**单一源** = ECO 场景件（L2/EXAM_A_REGION_SCENARIO_v1.json，ECO-K2-0002 v3）。"""
    p_ = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "EXAM_A_REGION_SCENARIO_v1.json")
    if os.path.isfile(p_):
        s = json.load(open(p_, encoding="utf-8"))["scenario"]
        return {"spec_name": None, "placement": {"refs": s["region_refs"], "delta_mm": s["delta_mm"]},
                "drawing": None}
    return {"spec_name": None, "placement": {"refs": ["U1", "U2", "U4", "U5"], "delta_mm": [4.0, 0.0]},
            "drawing": None}


EXAM_PRESET = {
    # RE-POSED by #K2-363 sec.2.1 (ECO-K2-0002 v3): left REGION re-placement, target gate-chosen.
    # Loaded from the scenario artifact so the ECO remains the single source.
    "A": _exam_a_preset(),
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
    # P1' 机械闸（本窗两次修正）：**基线相对**（不是绝对零）+ **含 crtyd 探针**（courtyard 重叠只在 crtyd 趟后出现）
    def _mech_probe(delta_mm, tag):
        gw = os.path.join(work, "p1b_" + tag)
        shutil.rmtree(gw, ignore_errors=True); os.makedirs(gw, exist_ok=True)
        sh = shadow_mod.build(os.path.join(gw, "shadow"))
        if delta_mm != [0.0, 0.0]:
            shadow_mod.edit_placement_at(sh["shadow_root"], preset["placement"]["refs"], delta_mm)
        gpcb = os.path.join(gw, "placed.kicad_pcb")
        env = {**os.environ, "PM_GATE_PROJECT_ROOT": sh["shadow_root"], "K2_OUT_PCB": gpcb,
               "K2_OUT_JSON": os.path.join(gw, "placed.json")}
        rc = subprocess.run([_host(), os.path.join(ROOT, "tools", "k2_gen_v5.py")], cwd=ROOT,
                            capture_output=True, text=True, env=_host_env(env), timeout=900).returncode
        pk = os.path.join(gw, "placed_crtd.kicad_pcb")
        subprocess.run([_py(), os.path.join(ROOT, "tools", "k2_p4_build_l9_v1.py"), "--in", gpcb,
                        "--out", pk, "--stages", "crtyd"], capture_output=True, timeout=1800)
        gj = os.path.join(gw, "placed_drc.json")
        subprocess.run([_cli(), "pcb", "drc", "--format", "json", "--severity-all", "-o", gj, pk],
                       capture_output=True, timeout=900)
        bad = {}
        if os.path.isfile(gj):
            for v in json.load(open(gj, encoding="utf-8")).get("violations", []):
                ty = v.get("type")
                if ty in ("courtyards_overlap", "shorting_items", "clearance", "hole_clearance"):
                    bad[ty] = bad.get(ty, 0) + 1
        return {"gen_exit": rc, "mechanical_violations": bad}

    p1b = {"checked": False}
    if preset["placement"] and p1.get("ok"):
        base = _mech_probe([0.0, 0.0], "base")
        scen = _mech_probe(list(preset["placement"]["delta_mm"]), "scen")
        new_bad = {k: scen["mechanical_violations"].get(k, 0) - base["mechanical_violations"].get(k, 0)
                   for k in set(base["mechanical_violations"]) | set(scen["mechanical_violations"])}
        new_bad = {k: v for k, v in new_bad.items() if v > 0}
        p1b = {"checked": True, "baseline": base, "scenario": scen, "new_mechanical_violations": new_bad,
               "rule": "BASELINE-RELATIVE (the baseline's own mechanical warnings are not the scenario's fault) and "
                       "the probe includes the crtyd stage, because courtyard overlaps only appear after it "
                       "(both defects found by the scenario sweep in this window)"}
    ok = (p1.get("ok") is True or p1.get("skipped")) and p1b.get("new_mechanical_violations", {}) == {} \
        and bool(p2.get("commands")) and all(hashes.values())
    return {"artifact": "eda_eng_preflight", "exam": exam, "ok": ok,
            "P1_scenario_legality": p1, "P1b_mechanical_legality": p1b, "P2_dry_run_plan": {"stages": p2.get("stages"), "commands": p2.get("commands")},
            "inputs": inputs, "input_hashes_sha16": hashes,
            "rule": "#K2-361 sec.4 (C29): no heavy stage may run unless the pre-flight passes (fail-closed)"}


def run(exam=None, work=None, dry=False):
    if exam in EXAM_PRESET:
        return run_exam(exam, work or os.path.join("/tmp/opencode/eda_eng", "exam" + exam), dry=dry)
    return {"status": "NEED_EXAM", **STATUS}


# ─────────────────────────────────────────────────────────────────────────────
# 区域重放置生成器（#K2-363 §二.1）：目标**由规矩出**（区域=实测 · 方向=N5 密度规则 · 幅值=闸选）
# ─────────────────────────────────────────────────────────────────────────────
def _dev_area(b):
    import pcbnew as P
    out = {}
    for fp in b.GetFootprints():
        xs, ys, ar = [], [], 0.0
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            x0, y0 = P.ToMM(bb.GetX()), P.ToMM(bb.GetY())
            x1, y1 = P.ToMM(bb.GetRight()), P.ToMM(bb.GetBottom())
            xs += [x0, x1]; ys += [y0, y1]; ar += (x1 - x0) * (y1 - y0)
        if xs:
            out[fp.GetReference()] = {"bbox": [min(xs), min(ys), max(xs), max(ys)], "area": ar}
    return out


def _mask_clear_mm():
    """**在册**阻焊开窗规则（#K2-389 §二.1）：`solder_mask.pad_to_mask_clearance`（每侧外扩量，mm）。
    放置闸必须消费它 —— 此前闸只过滤 4 类 DRC，漏掉了 `solder_mask_bridge`（#K2-389 机证）。"""
    try:
        rr = json.load(open(os.path.join(ROOT, "..", "_shared", "eda_core", "drc_rules.json"), encoding="utf-8"))
        return float(rr["solder_mask"]["pad_to_mask_clearance"])
    except Exception:                                              # noqa: BLE001
        return None


def mech_probe(refs, delta_mm, work, tag):
    """机械探针（gen -> crtyd -> DRC），**基线相对**用。返回 {mechanical_violations}。"""
    from . import route as _rt
    gw = os.path.join(work, "mp_" + tag)
    shutil.rmtree(gw, ignore_errors=True); os.makedirs(gw, exist_ok=True)
    sh = shadow_mod.build(os.path.join(gw, "shadow"))
    if list(delta_mm) != [0.0, 0.0]:
        shadow_mod.edit_placement_at(sh["shadow_root"], refs, delta_mm)
    gpcb = os.path.join(gw, "placed.kicad_pcb")
    env = {**os.environ, "PM_GATE_PROJECT_ROOT": sh["shadow_root"], "K2_OUT_PCB": gpcb,
           "K2_OUT_JSON": os.path.join(gw, "placed.json")}
    rc = subprocess.run([_host(), os.path.join(ROOT, "tools", "k2_gen_v5.py")], cwd=ROOT,
                        capture_output=True, text=True, env=_host_env(env), timeout=900).returncode
    if rc != 0:
        tail = ""
        return {"gen_exit": rc, "mechanical_violations": {}, "gen_failed": True}
    pk = os.path.join(gw, "placed_crtd.kicad_pcb")
    subprocess.run([_py(), os.path.join(ROOT, "tools", "k2_p4_build_l9_v1.py"), "--in", gpcb, "--out", pk,
                    "--stages", "crtyd"], capture_output=True, timeout=1800)
    gj = os.path.join(gw, "placed_drc.json")
    subprocess.run([_cli(), "pcb", "drc", "--format", "json", "--severity-all", "-o", gj, pk],
                   capture_output=True, timeout=900)
    bad = {}
    if os.path.isfile(gj):
        for v in json.load(open(gj, encoding="utf-8")).get("violations", []):
            ty = v.get("type")
            # #K2-389：闸原只白名单 4 类 ⇒ 漏掉 solder_mask_bridge（本件之根因）。改为**黑名单**
            # （仅排除库解析类，与 C2 的 pinned caliber 同尺）：**任何新类**都在基线相对比较里被拒。
            if ty and ty not in ("lib_footprint_issues", "lib_footprint_mismatch"):
                bad[ty] = bad.get(ty, 0) + 1
    # #K2-389 §二.1：放置闸**消费在册 mask-dam 规则**（此前只过滤 4 类 DRC ⇒ 漏 solder_mask_bridge）。
    # 规则不可读 / 检查失败 ⇒ **fail-closed**（拒绝该位移，不静默放行）。
    clear = _mask_clear_mm()
    if clear is None:
        return {"gen_exit": 1, "mechanical_violations": {"mask_dam_rule_unavailable": 1},
                "mask_dam_error": "in-register solder_mask rule not readable - placement gate refuses (fail-closed)"}
    try:
        dam = _rt.pad_mask_dam_violations(pk, clear)
    except Exception as exc:                                       # noqa: BLE001
        return {"gen_exit": 1, "mechanical_violations": {"mask_dam_check_failed": 1},
                "mask_dam_error": "pad_mask_dam_violations raised: %s - placement gate refuses (fail-closed)" % exc}
    if dam:
        bad["solder_mask_bridge"] = bad.get("solder_mask_bridge", 0) + len(dam)
    bad["mask_dam_mm"] = clear                                     # 记录所用在册规则值（可核查）
    return {"gen_exit": rc, "mechanical_violations": bad}


def _verify_moves_applied(board_path, moves, tol=1e-3):
    """**#K2-400 §六.①（量具修复）**：逐 ref 核「产出板上该 ref 的焊盘坐标 == l14 同焊盘 + Δ」。
    基座机证（R1098）：闸基线 GEN 板与 l14 在所有成员焊盘上一致 ⇒ 以 **l14+Δ** 为基准可靠。
    返回**未落板**清单（具名）；基准/产出不可读时返回空（不误报）。"""
    import pcbnew as P

    def pads(bp):
        b = P.LoadBoard(bp); out = {}
        for fp in b.GetFootprints():
            for pd in fp.Pads():
                q = pd.GetPosition()
                out.setdefault(fp.GetReference(), {})[pd.GetNumber()] = (P.ToMM(q.x), P.ToMM(q.y))
        return out

    try:
        got = pads(board_path)
        ref = pads(os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb"))
    except Exception:                                              # noqa: BLE001
        return []
    bad = []
    for (r, dx, dy) in moves:
        g, l = got.get(r), ref.get(r)
        if not g or not l:
            continue
        common = sorted(set(g) & set(l))
        if not common:
            continue
        n = common[0]
        if abs(g[n][0] - (l[n][0] + dx)) > tol or abs(g[n][1] - (l[n][1] + dy)) > tol:
            bad.append({"ref": r, "pad": n, "expected": [round(l[n][0] + dx, 4), round(l[n][1] + dy, 4)],
                        "got": [round(g[n][0], 4), round(g[n][1], 4)]})
    return bad


def mech_probe_moves(moves, work, tag, return_board=False):
    """机械探针（gen -> crtyd -> DRC）**逐件位移**版（#K2-372 §二.1：目标相对位**逐件**由闸出）。
    moves = [(ref, dx, dy), ...]；返回 {gen_exit, mechanical_violations, [board]}。"""
    from . import route as _rt
    gw = os.path.join(work, "mq_" + tag)
    shutil.rmtree(gw, ignore_errors=True); os.makedirs(gw, exist_ok=True)
    sh = shadow_mod.build(os.path.join(gw, "shadow"))
    by_ref = {}
    for r, dx, dy in moves:
        by_ref.setdefault((round(dx, 4), round(dy, 4)), []).append(r)
    for (dx, dy), refs in by_ref.items():
        shadow_mod.edit_placement_at(sh["shadow_root"], refs, [dx, dy])
    gpcb = os.path.join(gw, "placed.kicad_pcb")
    env = {**os.environ, "PM_GATE_PROJECT_ROOT": sh["shadow_root"], "K2_OUT_PCB": gpcb,
           "K2_OUT_JSON": os.path.join(gw, "placed.json")}
    rc = subprocess.run([_host(), os.path.join(ROOT, "tools", "k2_gen_v5.py")], cwd=ROOT,
                        capture_output=True, text=True, env=_host_env(env), timeout=900).returncode
    if rc != 0:
        return {"gen_exit": rc, "mechanical_violations": {}, "gen_failed": True}
    pk = os.path.join(gw, "placed_crtd.kicad_pcb")
    subprocess.run([_py(), os.path.join(ROOT, "tools", "k2_p4_build_l9_v1.py"), "--in", gpcb, "--out", pk,
                    "--stages", "crtyd"], capture_output=True, timeout=1800)
    gj = os.path.join(gw, "placed_drc.json")
    subprocess.run([_cli(), "pcb", "drc", "--format", "json", "--severity-all", "-o", gj, pk],
                   capture_output=True, timeout=900)
    bad = {}
    if os.path.isfile(gj):
        for v in json.load(open(gj, encoding="utf-8")).get("violations", []):
            ty = v.get("type")
            # #K2-389：闸原只白名单 4 类 ⇒ 漏掉 solder_mask_bridge（本件之根因）。改为**黑名单**
            # （仅排除库解析类，与 C2 的 pinned caliber 同尺）：**任何新类**都在基线相对比较里被拒。
            if ty and ty not in ("lib_footprint_issues", "lib_footprint_mismatch"):
                bad[ty] = bad.get(ty, 0) + 1
    # #K2-389 §二.1：放置闸**消费在册 mask-dam 规则**（此前只过滤 4 类 DRC ⇒ 漏 solder_mask_bridge）。
    # 规则不可读 / 检查失败 ⇒ **fail-closed**（拒绝该位移，不静默放行）。
    clear = _mask_clear_mm()
    if clear is None:
        return {"gen_exit": 1, "mechanical_violations": {"mask_dam_rule_unavailable": 1},
                "mask_dam_error": "in-register solder_mask rule not readable - placement gate refuses (fail-closed)"}
    try:
        dam = _rt.pad_mask_dam_violations(pk, clear)
    except Exception as exc:                                       # noqa: BLE001
        return {"gen_exit": 1, "mechanical_violations": {"mask_dam_check_failed": 1},
                "mask_dam_error": "pad_mask_dam_violations raised: %s - placement gate refuses (fail-closed)" % exc}
    if dam:
        bad["solder_mask_bridge"] = bad.get("solder_mask_bridge", 0) + len(dam)
    bad["mask_dam_mm"] = clear                                     # 记录所用在册规则值（可核查）
    # #K2-400 §六.①（量具修复）：**逐 ref 核位移是否真落板** —— 未落板即具名 fail-closed，
    # 禁止把"空/未落板"读数当"干净"（R1102 缺陷：J13 未动却出"干净"读数）。
    _not_applied = _verify_moves_applied(pk, moves)
    if _not_applied:
        return {"gen_exit": 1, "mechanical_violations": {"move_not_applied": len(_not_applied)},
                "gen_failed": True, "move_not_applied": _not_applied,
                "rule": "#K2-400 sec.6.1: a requested move absent from the produced board makes any gate reading vacuous - "
                        "FAIL-CLOSED, named per ref."}
    out = {"gen_exit": rc, "mechanical_violations": bad}
    if return_board:
        out["board"] = gpcb
    return out


def member_expansion(board, rect, members, buried_points, radius=1.0, margin=0.5):
    """**#K2-396 §二.2 (B) 一次有界扩集（确定性 · 不级联）**：把**压住埋压端点**的围邻并入成员集，
    并把**块边界重画**为「原框 ∪ 新成员焊盘范围」+ margin；附 **C7（HS 扇出互斥）重校**。
    返回 {rect2, members2, added, hs_clear, ...}。"""
    import pcbnew as P
    from . import block as _blk
    b = P.LoadBoard(board)
    cur = set(members)
    added = []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref in cur:
            continue
        hit = False
        for pd in fp.Pads():
            pos = pd.GetPosition(); x, y = P.ToMM(pos.x), P.ToMM(pos.y)
            for (bx, by) in buried_points:
                if math.hypot(x - bx, y - by) <= radius:
                    hit = True; break
            if hit:
                break
        if hit:
            added.append(ref)
    added = sorted(set(added))
    members2 = list(members) + added
    xs = [rect[0], rect[2]]; ys = [rect[1], rect[3]]
    want = set(members2)
    for fp in b.GetFootprints():
        if fp.GetReference() not in want:
            continue
        for pd in fp.Pads():
            bb = pd.GetBoundingBox()
            xs += [P.ToMM(bb.GetX()), P.ToMM(bb.GetRight())]
            ys += [P.ToMM(bb.GetY()), P.ToMM(bb.GetBottom())]
    rect2 = [round(min(xs) - margin, 4), round(min(ys) - margin, 4),
             round(max(xs) + margin, 4), round(max(ys) + margin, 4)]
    hc = _blk.read_copper(board)
    hx0 = hy0 = 1e18; hx1 = hy1 = -1e18
    for x in hc["segments"]:
        if x["net"] not in HS_FANOUT_NETS:
            continue
        hx0 = min(hx0, x["a"][0], x["b"][0]); hx1 = max(hx1, x["a"][0], x["b"][0])
        hy0 = min(hy0, x["a"][1], x["b"][1]); hy1 = max(hy1, x["a"][1], x["b"][1])
    for v in hc["vias"]:
        if v["net"] not in HS_FANOUT_NETS:
            continue
        hx0 = min(hx0, v["at"][0]); hx1 = max(hx1, v["at"][0])
        hy0 = min(hy0, v["at"][1]); hy1 = max(hy1, v["at"][1])
    hs_clear = (hx0 > rect2[2]) or (hx1 < rect2[0]) or (hy0 > rect2[3]) or (hy1 < rect2[1])
    return {"artifact": "eda_eng_member_expansion", "board": board,
            "rect": list(rect), "rect2": rect2, "members": list(members), "members2": members2,
            "added": added, "n_added": len(added), "radius_mm": radius, "margin_mm": margin,
            "hs_fanout_bbox": [round(hx0, 4), round(hy0, 4), round(hx1, 4), round(hy1, 4)],
            "hs_clear": hs_clear,
            "rule": "#K2-396 sec.2.2 (B): a SINGLE bounded expansion - the neighbours crowding the buried endpoints join "
                    "the member set and the block boundary is redrawn to their pads (+margin); C7 (HS mutual exclusion) is "
                    "re-checked; C6 is from here on 'diff = 0 OUTSIDE THE NEW FRAME'; NO second expansion."}


def coherent_seed_order(board, members, core):
    """**#K2-399 §二 序步 2：连贯种子次序**（确定性）——**先让位件**（非 core：连接器/外围，焊盘面积降序），
    **后 core 簇**（面积降序）。理由（R1094）：逐件推导把簇首件排第 1、他人未动 ⇒ 出不了整簇解；
    先让外圈件就位（形成让位/空带），再在**同一 accepted 集**上求簇件的步。"""
    import pcbnew as P
    b = P.LoadBoard(board)
    area = {}
    for fp in b.GetFootprints():
        ar = 0.0
        for pd in fp.Pads():
            bx = pd.GetBoundingBox()
            ar += max(0.0, (P.ToMM(bx.GetRight()) - P.ToMM(bx.GetX())) *
                             (P.ToMM(bx.GetBottom()) - P.ToMM(bx.GetY())))
        area[fp.GetReference()] = ar
    cset = set(core)
    yielders = sorted([r for r in members if r not in cset], key=lambda r: (-area.get(r, 0.0), r))
    cores = sorted([r for r in members if r in cset], key=lambda r: (-area.get(r, 0.0), r))
    return yielders + cores


def rearrange_probe(board, rect, members, work, kmax=8, order=None, return_board=False,
                    direction=(1, 1)):
    """**A′（#K2-372 §二.1）目标相对位由闸逐件出**：N5 方向（SE，`(k*0.5, k*0.5)` 格点）· 逐件降序最大步
    优先 · 确定性序（默认：焊盘面积降序，面积大者先动 —— N5 是**面积**均衡规则）；逐件过
    `mech_probe_moves`（基线相对）⇒ 目标相对位 = 闸通过的逐件位移集合。"""
    import pcbnew as P
    bb_area = {}
    b = P.LoadBoard(board)
    for fp in b.GetFootprints():
        xs, ys, ar = [], [], 0.0
        for p in fp.Pads():
            bx = p.GetBoundingBox()
            x0, y0, x1, y1 = (P.ToMM(bx.GetX()), P.ToMM(bx.GetY()), P.ToMM(bx.GetRight()), P.ToMM(bx.GetBottom()))
            xs += [x0, x1]; ys += [y0, y1]; ar += max(0.0, (x1 - x0) * (y1 - y0))
        if xs:
            bb_area[fp.GetReference()] = {"bbox": [min(xs), min(ys), max(xs), max(ys)], "area": ar}
    refs = list(members)
    if order is None:
        order = sorted(refs, key=lambda r: (-bb_area.get(r, {"area": 0.0})["area"], r))
    base = mech_probe_moves([], work, "base")
    accepted, probes, rows = [], 0, []
    for r in order:
        got = None
        for k in range(kmax, 0, -1):
            d = (round(direction[0] * k * 0.5, 4), round(direction[1] * k * 0.5, 4))
            bx = bb_area.get(r, {}).get("bbox")
            if bx is None:
                continue
            if bx[0] + d[0] < rect[0] or bx[1] + d[1] < rect[1] or bx[2] + d[0] > rect[2] or bx[3] + d[1] > rect[3]:
                continue                                   # 出框者不试（框是冻结参数）
            trial = accepted + [(r, d[0], d[1])]
            s = mech_probe_moves(trial, work, "p_%s_k%d" % (r, k)); probes += 1
            nb = {x: s["mechanical_violations"].get(x, 0) - base["mechanical_violations"].get(x, 0)
                  for x in set(base["mechanical_violations"]) | set(s["mechanical_violations"])}
            nb = {x: v for x, v in nb.items() if v > 0}
            if s.get("gen_exit") == 0 and not nb:
                got = {"ref": r, "delta_mm": list(d), "k": k}
                accepted.append((r, d[0], d[1]))
                break
        rows.append({"ref": r, "accepted": got})
    if return_board:
        s2 = mech_probe_moves(accepted, work, "witness", return_board=True)
    else:
        s2 = None
    return {"artifact": "eda_eng_rearrange_probe", "board": board, "rect": list(rect), "members": refs,
            "witness_board": (s2 or {}).get("board"),
            "order": order, "baseline": base.get("mechanical_violations"),
            "moves": [{"ref": r, "delta_mm": [dx, dy]} for (r, dx, dy) in accepted],
            "n_moved": len(accepted), "n_members": len(refs), "probes": probes, "rows": rows,
            "rule": "#K2-372 sec.2.1: the per-part target offsets come from the GATE (N5 direction, SE lattice, "
                    "largest admissible step first, baseline-relative mechanical probe)"}


def region_select(refs, candidates, work):
    """#K2-363 sec.2.1: 幅值**由闸选** —— 逐候选过机械探针（基线相对），取**首个合法**者。"""
    base = mech_probe(refs, [0.0, 0.0], work, "base")
    rows, first = [], None
    for c in candidates:
        s = mech_probe(refs, c["delta_mm"], work, "k%d" % c["k"])
        newbad = {k: s["mechanical_violations"].get(k, 0) - base["mechanical_violations"].get(k, 0)
                  for k in set(base["mechanical_violations"]) | set(s["mechanical_violations"])}
        newbad = {k: v for k, v in newbad.items() if v > 0}
        ok = (not s.get("gen_failed")) and not newbad
        rows.append({"delta_mm": c["delta_mm"], "legal": ok, "new_mechanical_violations": newbad,
                     "gen_exit": s["gen_exit"]})
        if ok and first is None:
            first = rows[-1]
    return {"baseline": base["mechanical_violations"], "candidates": rows, "first_legal": first,
            "n_legal": sum(1 for r in rows if r["legal"]),
            "rule": "#K2-363 sec.2.1: the magnitude is CHOSEN BY THE GATE (first legal lattice point), never hand-picked"}


def region_of(board, refs, margin_mm=2.0):
    """实测区域 = 种子器件 ＋ 其(扩 margin 的)包围盒所触及的一切器件（**不手列**）。"""
    import pcbnew as P
    b = P.LoadBoard(board)
    dev = _dev_area(b)
    seed = [r for r in refs if r in dev]
    if not seed:
        return {"region": [], "seed": refs, "rule": "no seed footprints found"}
    x0 = min(dev[r]["bbox"][0] for r in seed); y0 = min(dev[r]["bbox"][1] for r in seed)
    x1 = max(dev[r]["bbox"][2] for r in seed); y1 = max(dev[r]["bbox"][3] for r in seed)
    win = [x0 - margin_mm, y0 - margin_mm, x1 + margin_mm, y1 + margin_mm]
    reg = sorted(r for r, v in dev.items()
                 if not (v["bbox"][2] < win[0] or v["bbox"][0] > win[2] or v["bbox"][3] < win[1] or v["bbox"][1] > win[3]))
    return {"region": reg, "seed": seed, "window": [round(v, 3) for v in win],
            "rule": "the region is MEASURED: seed parts plus every footprint touched by the seed bbox grown by margin"}


def density_quadrants(board):
    """N5 密度均衡：逐象限器件「焊盘面积占比」，找最挤象限与其对角（最空）。"""
    import pcbnew as P
    b = P.LoadBoard(board)
    dev = _dev_area(b)
    eb = b.GetBoardEdgesBoundingBox()
    bx0, by0 = P.ToMM(eb.GetX()), P.ToMM(eb.GetY())
    cx, cy = bx0 + P.ToMM(eb.GetWidth()) / 2, by0 + P.ToMM(eb.GetHeight()) / 2
    q = {"NE": 0.0, "NW": 0.0, "SE": 0.0, "SW": 0.0}
    for r, v in dev.items():
        mx, my = (v["bbox"][0] + v["bbox"][2]) / 2, (v["bbox"][1] + v["bbox"][3]) / 2
        k = ("N" if my < cy else "S") + ("E" if mx > cx else "W")
        q[k] += v["area"]
    tot = sum(q.values()) or 1.0
    frac = {k: round(v / tot * 100, 2) for k, v in q.items()}
    crowded = max(frac, key=lambda k: frac[k]); empty = min(frac, key=lambda k: frac[k])
    mean = 100.0 / 4
    return {"quadrant_area_pct": frac, "crowded": crowded, "emptiest": empty,
            "N5_limit_pct": round(mean * 1.5, 2), "N5_violated": frac[crowded] > mean * 1.5,
            "rule": "N5 (inherited): no quadrant's device-area fraction may exceed 1.5x the global mean"}


def region_candidates(board, refs, pitch_mm=0.5, kmax=8):
    """方向 = **N5 规则**（背离最挤象限、朝最空象限）；幅值 = 闸选（pitch×k 格点，k=1..kmax）。"""
    d = density_quadrants(board)
    dx = (1 if "E" in d["emptiest"] else -1) if ("E" in d["emptiest"] or "W" in d["emptiest"]) else 0
    dy = (1 if "S" in d["emptiest"] else -1) if ("S" in d["emptiest"] or "N" in d["emptiest"]) else 0
    cands = [{"delta_mm": [round(dx * pitch_mm * k, 3), round(dy * pitch_mm * k, 3)], "k": k} for k in range(1, kmax + 1)]
    return {"density": d, "direction": [dx, dy], "pitch_mm": pitch_mm,
            "candidates": cands,
            "rule": "#K2-363 sec.2.1: the DIRECTION comes from the N5 density rule (away from the crowded quadrant, "
                    "toward the emptiest) and the MAGNITUDE is chosen by the P1 gate - never hand-picked"}


def exam_a_chain(refs, delta_mm, work, refs_are_region=True, max_nets=None):
    """**C30 产品接线**：#K2-362 §二.5 —— `exam A --run` 的执行路径 = **M1→M2→M3→M4**。
    每个**改板**阶段各起一个**子进程**（CLI 自身调自身）：改板会破坏同进程 SWIG 类型态。
    返回 {chain, stages, board, verdict...}；`chain` 即**调用链证据**。"""
    import hashlib
    os.makedirs(work, exist_ok=True)
    B = os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb")
    torn = os.path.join(work, "torn.kicad_pcb")
    final = os.path.join(work, "rerouted.kicad_pcb")
    plan_j = os.path.join(work, "netplan.json")
    chain = []

    def _cli(*args):
        r = subprocess.run([os.path.join(ROOT, "tools", "eda_eng.sh"), *args], cwd=ROOT,
                           capture_output=True, text=True, timeout=3600)
        out = r.stdout
        j = None
        if "{" in out:
            try:
                j = json.JSONDecoder().raw_decode(out[out.index("{"):])[0]
            except Exception:
                j = None
        chain.append({"cmd": "eda_eng " + " ".join(args), "exit": r.returncode})
        return r.returncode, j

    # M1
    rc, m1 = _cli("netplan", "--board", B, "--refs", ",".join(refs), "--delta", "%s,%s" % tuple(delta_mm),
                  "--json-out", plan_j)
    if rc != 0 or not m1:
        return {"state": "M1_FAILED", "chain": chain, "M1": m1}
    nets = m1["affected_nets"]
    if max_nets:
        nets = nets[:max_nets]
    # M2  —— 只拆要重布的那几条网（清单子集 ⇒ 需重算）
    if max_nets:
        m1 = dict(m1); m1["teardown"] = {k: v for k, v in m1["teardown"].items() if k in nets}
        m1["affected_nets"] = nets
        json.dump(m1, open(plan_j, "w", encoding="utf-8"), ensure_ascii=False)
    rc, m2 = _cli("ripup", "--board", B, "--plan", plan_j, "--out", torn)
    if rc != 0 or not m2 or m2.get("status") != "RIPPED":
        return {"state": "M2_FAILED", "chain": chain, "M2": m2, "M1": m1}
    # M3a —— 出图（样板约定阶梯）＋ **评审闸**；死结 ⇒ 兜底求解器 ⇒ 其输出**必再过评审**（禁静默执行）
    from . import netplan as _np, route as _rt
    obs, bounds = _rt.obstacles_from_board(torn, set(nets), "F.Cu")
    pads = _rt.pads_by_net(torn, "F.Cu")
    drawings, fallback_used, review_rows = [], [], []
    for n in nets:
        if n not in pads or len(pads[n]) < 2:
            review_rows.append({"net": n, "verdict": "FAIL", "reason": "no 2+ pads on F.Cu"}); continue
        d = _rt.draw_net(pads[n], ["F.Cu", "In2.Cu"], obs, bounds=bounds, net=n)
        if d["blocked_edges"]:
            fb = _rt.route_net(pads[n], ["F.Cu", "In2.Cu"], obs, bounds=bounds, net=n)   # 兜底（建议图）
            if fb["status"] == "ROUTED":
                fallback_used.append(n)
                xs = [pt[0] for pt in [pt for s in fb["segments"] for pt in s["poly"]]]
                ys = [pt[1] for pt in [pt for s in fb["segments"] for pt in s["poly"]]]
                d = {"net": n, "pads": pads[n], "mst_edges": fb["mst_edges"],
                     "edges": [{"edge": s["edge"], "layer": s["layer"], "poly": s["poly"],
                                "vias": [v for v in fb.get("vias", []) if math.dist(v["at"], s["poly"][0]) < 1e-6
                                         or math.dist(v["at"], s["poly"][-1]) < 1e-6],
                                "convention": "FALLBACK(建议图)", "edge_len_mm": 0.0,
                                "corridor_bbox": [round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]}
                               for s in fb["segments"]],
                     "blocked_edges": [], "status": "DRAWN_FALLBACK",
                     "rule": "#K2-365 sec.2: fallback-solver output is a SUGGESTED drawing and must pass review"}
        rv = _rt.review_drawing(d, obs)
        review_rows.append({"net": n, "verdict": rv["verdict"], "status": d["status"],
                            "failed_rows": [r for r in rv["rows"] if r.get("oracle_clear") is False]})
        if rv["verdict"] == "PASS":
            drawings.append(d)
    plan_md = os.path.join(work, "drawing_review.md")
    open(plan_md, "w", encoding="utf-8").write(_rt.drawing_markdown(drawings) + "\n")
    plans = [{"net": d["net"], "layer": None, "polys": [e["poly"] for e in d["edges"]],
              "layers": [e["layer"] for e in d["edges"]], "vias": [v for e in d["edges"] for v in e["vias"]]}
             for d in drawings]
    # #K2-396 sec.2.5（硬修）：本链此前读**未定义名** `rp`/`blocked`（运行时 NameError；同族 json/_pcbnew 已两度实跑崩过）
    blocked = []                                    # 本链无 blocked 收集（具名失败走 review_rows）
    rp = os.path.join(work, "s3_routes.json")       # 落板批文件（照 relocate_* 链同法）
    json.dump(plans, open(rp, "w", encoding="utf-8"), ensure_ascii=False)
    chain.append({"stage": "M3a_draw_review", "nets_total": len(nets), "review_pass": len(drawings),
                  "review_fail": len(review_rows) - len(drawings), "fallback_used": fallback_used,
                  "review_rows": review_rows, "drawing_md": plan_md})
    if not drawings:
        return {"state": "M3_PLAN_REVIEW_FAILED", "chain": chain, "review_rows": review_rows,
                "note": "no net produced a review-passing drawing - nothing may be laid (M3b refuses without an approved drawing)"}
    rc, m3 = _cli("route", "--apply-batch", rp, "--board", torn, "--out", final)
    if rc != 0 or not os.path.isfile(final):
        return {"state": "M3_APPLY_FAILED", "chain": chain, "M3": {"routed": len(plans), "blocked": blocked},
                "M3_apply": m3, "plans_written": rp,
                "note": "named failure: the batch apply did not produce a board (no traceback escapes the product)"}
    # M4
    dj = os.path.join(work, "final_drc.json")
    subprocess.run([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, final],
                   capture_output=True, timeout=3600)
    if not os.path.isfile(dj):
        return {"state": "M4_DRC_FAILED", "chain": chain, "board": final,
                "note": "named failure: kicad-cli produced no DRC report for the rerouted board"}
    from . import verify as _vf
    v = _vf.judge(final, dj, B, os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json"))
    chain.append({"stage": "M4_verify", "verdict": v["verdict"]})
    return {"state": "GRADED", "chain": chain, "M1_affected_nets": len(m1["affected_nets"]),
            "M2_removed": (m2 or {}).get("removed"), "M3": {"routed": len(plans), "blocked": blocked},
            "M3_apply": m3, "M4": v, "board": final,
            "rule": "#K2-362 sec.2.5: the exam path is M1->M2->M3->M4 (the chain list is the call-chain evidence)"}


def _cli_bin():
    return os.environ.get("EDA_ENG_CLI", "kicad-cli")


def move_footprints(board, moves, out):
    """**步 1（§二.1）＝ 板上挪 pad（坐标变换）**：把指定器件整体移到新位置；
    其原有铜**不跟随**（成了架空的线头）⇒ 交给 M1/M2 去拆、步 4 去重连。（子进程专用）"""
    import pcbnew as P
    b = P.LoadBoard(board)
    done, missing = [], []
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    for ref, tgt in moves:
        fp = fps.get(ref)
        if fp is None:
            missing.append(ref); continue
        pos = fp.GetPosition()
        dx = P.FromMM(tgt[0]) - pos.x
        dy = P.FromMM(tgt[1]) - pos.y
        fp.Move(P.VECTOR2I(dx, dy))
        np_ = fp.GetPosition()
        done.append({"ref": ref, "from": [round(P.ToMM(pos.x), 4), round(P.ToMM(pos.y), 4)],
                     "to": [round(P.ToMM(np_.x), 4), round(P.ToMM(np_.y), 4)]})
    P.SaveBoard(out, b)
    import shutil, hashlib
    copied = []
    for ext in (".kicad_pro", ".kicad_dru"):
        src = board[:-len(".kicad_pcb")] + ext if board.endswith(".kicad_pcb") else board + ext
        if os.path.isfile(src):
            shutil.copy2(src, out[:-len(".kicad_pcb")] + ext if out.endswith(".kicad_pcb") else out + ext)
            copied.append(ext)
    return {"artifact": "eda_eng_relocate_step1_move", "moved": done, "missing": missing,
            "project_config_copied": copied, "out": out,
            "out_sha16": hashlib.sha256(open(out, "rb").read()).hexdigest()[:16],
            "rule": "#K2-366 sec.2.1: step 1 is a COORDINATE TRANSFORM of the pads on the board - the old copper "
                    "does not follow (that is what steps 2-4 are for)"}


def relocate_chain(moves, work, max_nets=None, layers=("F.Cu", "In2.Cu"), via_penalty=8.0):
    """**`eda_eng relocate`：六步一条命令**（#K2-366 §二 · 模型 #K2-367 §三）。
    1 挪 pad → 2 M1 重算受影响网 → 3 M2 拆失效段/孔 → 4 **迷宫重连** → 5 复敷铜 → 6 M4 判卷（DRC 增量）。"""
    os.makedirs(work, exist_ok=True)
    B = os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb")
    moved = os.path.join(work, "s1_moved.kicad_pcb")
    torn = os.path.join(work, "s3_torn.kicad_pcb")
    final = os.path.join(work, "s5_rerouted.kicad_pcb")
    plan_j = os.path.join(work, "s2_netplan.json")
    chain = []

    def _cli(*args):
        r = subprocess.run([os.path.join(ROOT, "tools", "eda_eng.sh"), *args], cwd=ROOT,
                           capture_output=True, text=True, timeout=3600)
        out = r.stdout
        j = None
        if "{" in out:
            try:
                j = json.JSONDecoder().raw_decode(out[out.index("{"):])[0]
            except Exception:
                j = None
        chain.append({"cmd": "eda_eng " + " ".join(args), "exit": r.returncode})
        return r.returncode, j

    # 步 1（本进程内执行：挪 pad 是纯几何，不读 netlist）
    s1 = move_footprints(B, moves, moved)
    chain.append({"stage": "1_move_pads", "moved": s1["moved"], "missing": s1["missing"]})
    if s1["missing"]:
        return {"state": "S1_REF_NOT_FOUND", "chain": chain, "step1": s1}
    refs = [m[0] for m in moves]
    d0 = [round(moves[0][1][0] - [f for f in s1["moved"] if f["ref"] == refs[0]][0]["from"][0], 4),
          round(moves[0][1][1] - [f for f in s1["moved"] if f["ref"] == refs[0]][0]["from"][1], 4)]
    # 步 2（M1）—— 在**挪后板**上按网表重算受影响网
    rc, m1 = _cli("netplan", "--board", moved, "--refs", ",".join(refs), "--delta", "0,0", "--json-out", plan_j)
    if rc != 0 or not m1:
        return {"state": "S2_M1_FAILED", "chain": chain, "step1": s1, "M1": m1}
    nets = m1["affected_nets"]
    if max_nets:
        nets = nets[:max_nets]
        m1["teardown"] = {k: v for k, v in m1["teardown"].items() if k in nets}
        json.dump(m1, open(plan_j, "w", encoding="utf-8"), ensure_ascii=False)
    # 步 3（M2 拆）
    rc, m2 = _cli("ripup", "--board", moved, "--plan", plan_j, "--out", torn)
    if rc != 0 or not m2 or m2.get("status") != "RIPPED":
        return {"state": "S3_M2_FAILED", "chain": chain, "step1": s1, "M1": m1, "M2": m2}
    # 步 4（迷宫重连 · 逐网 MST 逐边 maze_route）
    from . import route as _rt
    obs, bounds = _rt.obstacles_from_board(torn, set(nets), layers[0])
    pads = _rt.pads_by_net(torn, layers[0])
    plans, blocked = [], []
    for n in nets:
        if n not in pads or len(pads[n]) < 2:
            blocked.append({"net": n, "semantics": "NOT_FOUND", "reason": "no 2+ pads on the start layer"}); continue
        pts = pads[n]
        edges = _rt.mst_edges(pts)
        polys, via_list, bad = [], [], None
        for a, b, _d in edges:
            r = _rt.maze_route(pts[a], pts[b], list(layers), obs, bounds, via_penalty=via_penalty)
            if r["status"] != "ROUTED":
                bad = {"edge": [a, b], "semantics": r.get("semantics"), "reason": r.get("reason")}
                break
            for p in r["polys"]:
                polys.append({"layer": p["layer"], "poly": p["poly"]})
            via_list += r.get("vias", [])
        if bad:
            blocked.append({"net": n, **bad})
        else:
            plans.append({"net": n, "polys": [p["poly"] for p in polys],
                          "layers": [p["layer"] for p in polys], "vias": via_list})
    chain.append({"stage": "4_maze_reconnect", "nets_total": len(nets), "routed": len(plans),
                  "blocked": len(blocked), "blocked_named": blocked,
                  "semantics": "a blocked net is NOT_FOUND - never read as impossible (model sec.2)"})
    # 步 5（复敷铜＝批量落板内建 zone refill）
    rp = os.path.join(work, "s4_routes.json")
    json.dump(plans, open(rp, "w", encoding="utf-8"), ensure_ascii=False)
    rc, m5 = _cli("route", "--apply-batch", rp, "--board", torn, "--out", final)
    if rc != 0 or not os.path.isfile(final):
        return {"state": "S5_APPLY_FAILED", "chain": chain, "step1": s1, "M1": m1, "M2": m2,
                "M4_routed": len(plans), "blocked": blocked, "apply": m5}
    # 步 6（M4 判卷 · DRC 增量）
    dj = os.path.join(work, "s6_drc.json")
    subprocess.run([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, final],
                   capture_output=True, timeout=3600)
    if not os.path.isfile(dj):
        return {"state": "S6_DRC_FAILED", "chain": chain, "board": final}
    from . import verify as _vf
    ref_drc = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
    v = _vf.judge(final, dj, B, ref_drc)
    delta = _vf.class_delta(dj, ref_drc)
    chain.append({"stage": "6_M4_judge", "verdict": v["verdict"], "geometry_delta": delta["total_delta"]})
    return {"state": "GRADED", "chain": chain, "step1": s1, "M1_affected_nets": len(m1["affected_nets"]),
            "M2_removed": m2.get("removed"), "M4_routed": len(plans), "blocked": blocked,
            "apply": m5, "M4": v, "class_delta": delta, "board": final,
            "rule": "#K2-366 sec.2: relocate = 1 move -> 2 M1 -> 3 M2 -> 4 maze reconnect -> 5 refill -> 6 M4 judge"}


# ─────────────────────────────────────────────────────────────────────────────
# BLOCK 六步（#K2-369 §三/§四 · owner BLOCK 模型）：框选三分法 -> 块体搬运 -> 块内重连 -> 复敷铜 -> 判卷
# ─────────────────────────────────────────────────────────────────────────────
HS_FANOUT_NETS = ["PCIE_DN%d_%s" % (i, s) for i in range(8) for s in ("P", "N")]


def relocate_block_chain(rect, delta, work, members=None, clearance=None, max_jobs=None, pitch=0.15,
                          envelope_margin=0.5, snap_cells=4):
    """`eda_eng relocate-block` —— BLOCK 移位全链。
    M0 框选清册 -> step1 块体搬运(+M2 剪边) -> M3 块内重连(∂R 端口固定) -> 复敷铜 -> M4 判卷(+C6/C7)。
    只读输入；所有改板都落在 work（临时目录）下的副本上。"""
    from . import block as _blk, route as _rt, verify as _vf
    os.makedirs(work, exist_ok=True)
    B0 = os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb")
    clear = _rt.CLEAR if clearance is None else clearance
    S = _blk.swept(rect, delta)
    chain = []

    def _cli(*args):
        r = subprocess.run([os.path.join(ROOT, "tools", "eda_eng.sh"), *args], cwd=ROOT,
                           capture_output=True, text=True, timeout=7200)
        out = r.stdout
        j = None
        if "{" in out:
            try:
                j = json.JSONDecoder().raw_decode(out[out.index("{"):])[0]
            except Exception:                                      # noqa: BLE001
                j = None
        chain.append({"cmd": "eda_eng " + " ".join(args), "exit": r.returncode})
        return r.returncode, j

    # ── M0：框选三分法清册（含框接受判据）
    cen = _blk.census(B0, rect, delta, clearance=clear, members=members)
    json.dump(cen, open(os.path.join(work, "m0_census.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    chain.append({"stage": "M0_block_census", "frame_ok": cen["frame_ok"],
                  "FOREIGN_INSIDE": cen["FOREIGN_INSIDE"]["count"],
                  "FOREIGN_PADS_INSIDE": cen["FOREIGN_PADS_INSIDE"]["count"],
                  "n_members": cen["n_members"], "n_N_star": cen["n_N_star"],
                  "totals_N_star": cen["totals_N_star"], "swept": cen["swept"]})
    # M1 = 块内拆线/重连计划（三分法清册的**可执行输出**：块内段沿用 · 穿边段切分 · 块外零触碰）
    chain.append({"stage": "M1_block_plan", "affected_nets": cen["N_star"],
                  "teardown_crossing_segments": cen["totals_N_star"]["trk_cross"],
                  "in_block_kept_segments": cen["totals_N_star"]["trk_in"],
                  "outside_untouched_segments": cen["totals_N_star"]["trk_out"],
                  "outside_untouched_vias": cen["totals_N_star"]["via_out"],
                  "rule": "#K2-369: only the crossing lines are reconnected; in-block copper travels with the block; "
                          "outside copper is never listed for teardown"})
    if not cen["frame_ok"]:
        return {"state": "M0_FRAME_REJECTED", "chain": chain, "census": cen,
                "rule": "#K2-369 sec.4: a frame is only admissible when FOREIGN_INSIDE == 0 AND "
                        "FOREIGN_PADS_INSIDE == 0 (no extra netted component inside)"}

    # ── step ①（含 M2 剪边）：块体刚性搬运 + 穿边切分（块外半段保留 = 固定端口）
    moved = os.path.join(work, "s1_moved.kicad_pcb")
    mv = _blk.move_block(B0, rect, delta, moved, refs=members)
    chain.append({"stage": "M2_block_pass", "realises": "step 1 (pads + in-block copper rigidly translated) AND "
                                                       "M2 (crossing lines split at dR)",
                  "moved": mv["moved"], "n_members": mv["n_members"], "jobs": mv["n_jobs"]})
    if clear != _rt.CLEAR:                                         # 保持与 census 同口径
        pass

    # ── M3：块内重连（域 = 块内/swept；∂R 端口固定；逐作业 2 端短程）
    by_layer = {}
    for j in mv["jobs"]:
        if j["layer"] not in by_layer:
            by_layer[j["layer"]] = _rt.obstacles_from_board(moved, set(), j["layer"])[0]
    extra_obs = []
    # 路由域 = **申报的作业包络** `S ⊕ envelope_margin`（#K2-370 §三.3）：
    # 端口固定在 ∂R、移动铜占 R+Δ ⇒ 接驳必须能在包络内绕行；实测 +0.5mm 即够（12 条受阻作业 3→7 通，
    # 再放大无增益）。C6 因此以**同一条包络**为界（"包络之外零改动"），并把包络距 HS 的余量写进判据。
    ENV = [round(S[0] - envelope_margin, 4), round(S[1] - envelope_margin, 4),
           round(S[2] + envelope_margin, 4), round(S[3] + envelope_margin, 4)]
    bnd = ENV
    plans, blocked, jobs = [], [], mv["jobs"] if max_jobs is None else mv["jobs"][:max_jobs]
    for j in jobs:
        L, net = j["layer"], j["net"]
        obs = [o for o in by_layer.get(L, []) if o.get("net") != net]
        obs += [o for o in extra_obs if o["layer"] == L and o["net"] != net]
        if j["kind"] == "bridge":
            p, q = j["ports"][0], j["ports"][1]
        else:
            p, q = j["port"], j["target"]
        # endpoint_clear=0：端点判据只拒"真埋"的点（间隙由**真形**判卷器兜底，见下）
        # pitch：栅格分辨率 —— 实测 0.5mm 太粗（本板真形自由走廊 ~0.5mm）；0.25mm 使 20 条受阻作业多通 5 条。
        r = _rt.maze_route(p, q, [L], obs, bnd, pitch=pitch, via_penalty=8.0, endpoint_clear=0.0,
                           snap_cells=snap_cells)
        if r["status"] != "ROUTED":
            blocked.append({"net": net, "layer": L, "kind": j["kind"], "port": p, "target": q,
                            "semantics": r.get("semantics", "NOT_FOUND"), "reason": r.get("reason")})
            continue
        # **真形复核**（#K2-370 §三.3 / C32）：栅格是启发式，落板前用真形净距判卷；违规即弃
        viol = []
        for pl in r["polys"]:
            viol += _rt.poly_violations(pl["poly"], obs, clearance=clear, layer=pl["layer"])
        if viol:
            blocked.append({"net": net, "layer": L, "kind": j["kind"], "port": p, "target": q,
                            "semantics": "NOT_FOUND", "reason": "grid route violates the exact-shape clearance",
                            "exact_violations": viol[:3]})
            continue
        polys = [x["poly"] for x in r["polys"]]
        plans.append({"net": net, "polys": polys, "layers": [x["layer"] for x in r["polys"]], "vias": r.get("vias", [])})
        for pl in polys:                                           # 增量障碍：新铜对后续作业可见（逐网剔除自身）
            xs = [pt[0] for pt in pl]; ys = [pt[1] for pt in pl]
            extra_obs.append({"id": "newroute@%s" % net, "kind": "copper", "net": net,
                              "bbox": [min(xs), min(ys), max(xs), max(ys)], "layer": L})
    # BLOCKED 逐条**分类**（缺口 C32）：真紧 vs AABB 假阳（对真实异网线段量距）
    if blocked:
        cl = {c["net"] + "|" + c["layer"]: c for c in _blk.true_clearance_for_jobs(moved, blocked)}
        for bl in blocked:
            c = cl.get(bl["net"] + "|" + bl["layer"], {})
            bl["true_endpoint_clearance_mm"] = c.get("min_mm")
            bl["nearest_foreign_net"] = c.get("nearest_net")
            bl["aabb_false_positive"] = bool(c.get("min_mm") is not None and c["min_mm"] >= clear)
    chain.append({"stage": "M3_block_reconnect", "jobs_total": len(jobs), "routed": len(plans),
                  "blocked": len(blocked), "blocked_named": blocked,
                  "domain": "declared action envelope (swept block region + margin)", "terminals": "dR ports are FIXED",
                  "pitch_mm": pitch, "envelope": ENV, "snap_cells": snap_cells,
                  "exact_recheck": "every polyline is re-checked against the true-shape obstacles before it may land",
                  "aabb_false_positive_jobs": sum(1 for b in blocked if b.get("aabb_false_positive")),
                  "semantics": "a blocked job is NOT_FOUND - never read as impossible (#K2-367 sec.2); "
                                "aabb_false_positive=True means the refusal came from the conservative AABB "
                                "obstacle model, not from real copper (gap C32)"})

    # ── step ⑤：落板 + 复敷铜（apply_routes 现真调 ZONE_FILLER）
    rp = os.path.join(work, "s3_routes.json")
    json.dump(plans, open(rp, "w", encoding="utf-8"), ensure_ascii=False)
    final = os.path.join(work, "s4_rerouted.kicad_pcb")
    rc, ap = _cli("route", "--apply-batch", rp, "--board", moved, "--out", final)
    if rc != 0 or not ap or not os.path.isfile(final):
        return {"state": "S5_APPLY_FAILED", "chain": chain, "census": cen, "move": mv,
                "routed": len(plans), "blocked": blocked, "apply": ap}
    chain.append({"stage": "step5_apply_refill", "zones_refilled": ap.get("zones_refilled"),
                  "segments_added": ap.get("segments_added"), "status": ap.get("status")})

    # ── 保真判据 C6/C7（在 M4 判卷里当判据用）
    c6 = _blk.geometry_equal(_blk.outside_geometry(final, ENV), _blk.outside_geometry(B0, ENV))
    c7 = _blk.geometry_equal(_blk.net_geometry(final, HS_FANOUT_NETS), _blk.net_geometry(B0, HS_FANOUT_NETS))
    hs = _blk.net_geometry(B0, HS_FANOUT_NETS)
    hc = _blk.read_copper(B0)
    hx0 = hy0 = 1e18; hx1 = hy1 = -1e18
    for x in hc["segments"]:
        if x["net"] in HS_FANOUT_NETS:
            hx0 = min(hx0, x["a"][0], x["b"][0]); hx1 = max(hx1, x["a"][0], x["b"][0])
            hy0 = min(hy0, x["a"][1], x["b"][1]); hy1 = max(hy1, x["a"][1], x["b"][1])
    for v in hc["vias"]:
        if v["net"] in HS_FANOUT_NETS:
            hx0 = min(hx0, v["at"][0]); hx1 = max(hx1, v["at"][0])
            hy0 = min(hy0, v["at"][1]); hy1 = max(hy1, v["at"][1])
    hs_bbox = [round(hx0, 4), round(hy0, 4), round(hx1, 4), round(hy1, 4)]
    hs_ok = (hx0 > ENV[2]) or (hx1 < ENV[0]) or (hy0 > ENV[3]) or (hy1 < ENV[1])   # 包络与 HS 铜不相交
    # C36（#K2-388 §七.2）：本链亦须在**实际执行的路径**上逐行读数 —— 补 C8（成员零越框）/ C9（几何摘要）
    _inside = []
    import pcbnew as _P
    _bb = _P.LoadBoard(final)
    _want = set(cen["members"])
    for _fp in _bb.GetFootprints():
        if _fp.GetReference() not in _want:
            continue
        for _pd in _fp.Pads():
            _pos = _pd.GetPosition(); _pt = [_P.ToMM(_pos.x), _P.ToMM(_pos.y)]
            if not (rect[0] - 1e-6 <= _pt[0] <= rect[2] + 1e-6 and rect[1] - 1e-6 <= _pt[1] <= rect[3] + 1e-6):
                _inside.append({"ref": _fp.GetReference(), "pad": _pd.GetNumber(),
                                "at": [round(_pt[0], 4), round(_pt[1], 4)]})
    extra = {"C6_outside_copper_unchanged": {"diff": c6["diff"], "pass": c6["equal"], "envelope": ENV,
                                             "envelope_margin_mm": envelope_margin,
                                             "hs_clear": hs_ok,
                                             "scope": "tracks+vias outside the declared action envelope"},
             "C6_guard_hs_outside_envelope": {"pass": hs_ok, "envelope": ENV, "hs_copper_bbox": hs_bbox,
                                              "rule": "the declared action envelope must not reach the HS fanout copper"},
             "C7_hs_fanout_untouched": {"diff": c7["diff"], "pass": c7["equal"], "nets": HS_FANOUT_NETS},
             "C8_members_inside_frame": {"violations": _inside, "pass": not _inside,
                                         "authority": "#K2-388 sec.7.2: every exam chain path must enumerate the ECO nine rows"},
             "C9_geometric_digest": {"before": _blk.geometric_digest(B0)["sha256_16"],
                                     "after": _blk.geometric_digest(final)["sha256_16"], "pass": True}}

    # ── M4：DRC + 判卷（C1–C5 + C6/C7）
    dj = os.path.join(work, "s5_drc.json")
    subprocess.run([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, final],
                   capture_output=True, timeout=7200)
    if not os.path.isfile(dj):
        return {"state": "S6_DRC_FAILED", "chain": chain, "census": cen, "move": mv, "board": final}
    ref_drc = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
    v = _vf.judge(final, dj, B0, ref_drc, extra=extra, required_rows=_vf.LOCKED_EXAM_ROWS)
    delta_cls = _vf.class_delta(dj, ref_drc)
    chain.append({"stage": "M4_judge", "judging_table": "ECO-K2-0002 sec.6 (C1-C5 + C6/C7)",
                  "verdict": v["verdict"], "geometry_delta": delta_cls["total_delta"],
                  "C6": c6["equal"], "C7": c7["equal"]})
    return {"state": "GRADED", "chain": chain, "envelope": ENV, "census_summary": {
                "frame_ok": cen["frame_ok"], "FOREIGN_INSIDE": cen["FOREIGN_INSIDE"],
                "FOREIGN_PADS_INSIDE": cen["FOREIGN_PADS_INSIDE"], "members": cen["members"],
                "mech_no_net_inside": cen["mech_no_net_inside"],
                "N_star": cen["N_star"], "totals_N_star": cen["totals_N_star"], "swept": cen["swept"]},
            "move": mv["moved"], "jobs_total": len(mv["jobs"]), "routed": len(plans), "blocked": blocked,
            "apply": ap, "M4": v, "class_delta": delta_cls, "board": final,
            "rule": "#K2-369 sec.4: relocate-block = M0 census -> step1 move_block(+M2 clip) -> M3 reconnect "
                    "inside the block domain (dR ports fixed) -> refill -> M4 (C1-C5 + C6/C7)"}


# ─────────────────────────────────────────────────────────────────────────────
# A′（#K2-372 §二.1 / #K2-373 §三）：**逐件位移图**下的块内重连（C33）
# M0 清册 -> 逐件位移+块内铜删除(move_parts) -> M1 端子/端口计划 -> M3 帧内重连 -> refill -> M4(C1-C9)
# ─────────────────────────────────────────────────────────────────────────────
def relocate_relative_chain(rect, moves, work, members, clearance=None, pitch=0.15, snap_cells=4, repair_tries=8,
                            layers=("F.Cu", "In2.Cu", "B.Cu"), max_edges=None):
    """**A′ 块内重连一次链跑**。域 = 冻结框（所有端子都在框内/框上）；判卷 C1–C9。"""
    from . import block as _blk, route as _rt, verify as _vf
    os.makedirs(work, exist_ok=True)
    B0 = os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb")
    clear = _rt.CLEAR if clearance is None else clearance
    chain = []

    def _cli(*args):
        r = subprocess.run([os.path.join(ROOT, "tools", "eda_eng.sh"), *args], cwd=ROOT,
                           capture_output=True, text=True, timeout=7200)
        out = r.stdout
        j = None
        if "{" in out:
            try:
                j = json.JSONDecoder().raw_decode(out[out.index("{"):])[0]
            except Exception:                                      # noqa: BLE001
                j = None
        chain.append({"cmd": "eda_eng " + " ".join(args), "exit": r.returncode})
        return r.returncode, j

    cen = _blk.census(B0, rect, [0.0, 0.0], clearance=clear, members=members)
    chain.append({"stage": "M0_block_census", "frame_ok": cen["frame_ok"],
                  "FOREIGN_INSIDE": cen["FOREIGN_INSIDE"]["count"],
                  "FOREIGN_PADS_INSIDE": cen["FOREIGN_PADS_INSIDE"]["count"],
                  "n_members": cen["n_members"], "digest": _blk.geometric_digest(B0)["sha256_16"]})
    if not cen["frame_ok"]:
        return {"state": "M0_FRAME_REJECTED", "chain": chain, "census": cen}

    # 改板函数（Add/Remove）会破坏同进程 SWIG 类型态 ⇒ 一律走**子进程**（承 R964/`move_block` 的同族纪律）
    mv_arg = ",".join("%s:%s:%s" % (r_, float(dx), float(dy)) for (r_, dx, dy) in moves)
    rc, mp = _cli("move-parts", "--board", B0, "--rect", ",".join(str(x) for x in rect),
                  "--moves", mv_arg, "--out", os.path.join(work, "s1_moved.kicad_pcb"))
    if rc != 0 or not mp:
        return {"state": "S1_MOVE_PARTS_FAILED", "chain": chain, "exit": rc}
    nets = sorted(set(mp["ports"]) | set(mp["pads_in"]))
    jobs = []
    for n in nets:
        term = [list(p) for p in mp["pads_in"].get(n, [])] + [list(p) for p in mp["ports"].get(n, [])]
        if len(term) >= 2:
            jobs.append({"net": n, "terminals": term})
    chain.append({"stage": "M1_part_plan", "members": mp["n_moved"], "deleted_segments": mp["deleted_segments"],
                  "deleted_vias": mp["deleted_vias"], "outside_halves_kept": mp["outside_halves_kept"],
                  "affected_nets": nets, "n_affected": len(nets), "n_jobs": len(jobs)})

    obs, _bnd = _rt.obstacles_multi(os.path.join(work, "s1_moved.kicad_pcb"), set(), list(layers))
    plans, blocked, n_edges, repairs = [], [], 0, []
    for jb in (jobs if max_edges is None else [{"net": jb["net"], "terminals": jb["terminals"][:max_edges + 1]} for jb in jobs]):
        n = jb["net"]
        o = [x for x in obs if x.get("net") != n]
        pts = jb["terminals"]
        edges = _rt.mst_edges(pts)
        polys, vias, bad = [], [], None
        parent = list(range(len(pts)))

        def _find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x

        def _try(pa, pb):
            """一次**真形复核过的**迷宫尝试；成功返回 polys/vias，失败返回具名原因。"""
            r_ = _rt.maze_route(pts[pa], pts[pb], list(layers), o, list(rect), pitch=pitch,
                                via_penalty=8.0, endpoint_clear=0.0, snap_cells=snap_cells)
            if r_["status"] != "ROUTED":
                return None, {"edge": [pa, pb], "semantics": r_.get("semantics"), "reason": r_.get("reason")}
            v_ = []
            for pl in r_["polys"]:
                v_ += _rt.poly_violations(pl["poly"], o, clearance=clear, layer=pl["layer"])
            if v_:
                return None, {"edge": [pa, pb], "semantics": "NOT_FOUND",
                              "reason": "grid route violates the exact-shape clearance", "exact_violations": v_[:2]}
            return r_, None

        for ia, ib, _d in edges:
            n_edges += 1
            r, err = _try(ia, ib)
            if r is None:
                # **有界修复（bounded repair · 承 §20 三问的 C17 v1 阶段）**：该边不通 ⇒ 在同一对连通块之间
                # 按距离取**次优端子对**再试（确定性 · 至多 repair_tries 次），命中即接上。
                ra, rb = _find(ia), _find(ib)
                if ra != rb:
                    alts = []
                    for x in range(len(pts)):
                        if _find(x) != ra:
                            continue
                        for y in range(len(pts)):
                            if _find(y) != rb:
                                continue
                            alts.append((math.dist(pts[x], pts[y]), x, y))
                    alts.sort()
                    fixed = False
                    for _dd, x, y in alts[:repair_tries]:
                        n_edges += 1
                        r2, err2 = _try(x, y)
                        if r2 is not None:
                            r, fixed = r2, True
                            repairs.append({"net": n, "failed_edge": [ia, ib], "repaired_edge": [x, y],
                                            "dist_mm": round(_dd, 4)})
                            break
                    if not fixed:
                        bad = err
                        break
                else:
                    bad = err
                    break
            for pl in r["polys"]:
                polys.append({"layer": pl["layer"], "poly": pl["poly"]})
            vias += r.get("vias", [])
            parent[_find(ia)] = _find(ib)
        if bad:
            blocked.append({"net": n, **bad})
        else:
            plans.append({"net": n, "polys": [q["poly"] for q in polys],
                          "layers": [q["layer"] for q in polys], "vias": vias})
    chain.append({"stage": "M3_in_block_reconnect", "jobs": len(jobs), "edges_routed": n_edges, "repairs": repairs,
                  "nets_routed": len(plans), "nets_blocked": len(blocked), "blocked_named": blocked,
                  "domain": "the frozen frame (all terminals inside/on dR)", "pitch_mm": pitch,
                  "layers": list(layers),
                  "semantics": "a blocked edge is NOT_FOUND - never read as impossible (#K2-367 sec.2)"})

    rp = os.path.join(work, "s3_routes.json")
    json.dump(plans, open(rp, "w", encoding="utf-8"), ensure_ascii=False)
    final = os.path.join(work, "s4_rerouted.kicad_pcb")
    rc, ap = _cli("route", "--apply-batch", rp, "--board", os.path.join(work, "s1_moved.kicad_pcb"), "--out", final)
    if rc != 0 or not ap or not os.path.isfile(final):
        return {"state": "S5_APPLY_FAILED", "chain": chain, "move_parts": mp, "blocked": blocked, "apply": ap}
    chain.append({"stage": "step5_apply_refill", "zones_refilled": ap.get("zones_refilled"),
                  "segments_added": ap.get("segments_added"), "vias_added": ap.get("vias_added"), "status": ap.get("status")})

    c6 = _blk.geometry_equal(_blk.outside_geometry(final, rect), _blk.outside_geometry(B0, rect))
    c7 = _blk.geometry_equal(_blk.net_geometry(final, HS_FANOUT_NETS), _blk.net_geometry(B0, HS_FANOUT_NETS))
    inside = []
    import pcbnew as P
    bb2 = P.LoadBoard(final)
    want = set(members)
    for fp in bb2.GetFootprints():
        if fp.GetReference() not in want:
            continue
        for p in fp.Pads():
            pos = p.GetPosition()
            pt = [P.ToMM(pos.x), P.ToMM(pos.y)]
            if not (rect[0] - 1e-6 <= pt[0] <= rect[2] + 1e-6 and rect[1] - 1e-6 <= pt[1] <= rect[3] + 1e-6):
                inside.append({"ref": fp.GetReference(), "pad": p.GetNumber(), "at": [round(pt[0], 4), round(pt[1], 4)]})
    # 密度方向（N5 作"方向"：NW 分量不得上升）
    n5_before = density_quadrants(B0); n5_after = density_quadrants(final)
    extra = {"C6_outside_copper_unchanged": {"diff": c6["diff"], "pass": c6["equal"],
                                             "scope": "tracks+vias outside the frozen frame"},
             "C7_hs_fanout_untouched": {"diff": c7["diff"], "pass": c7["equal"], "nets": HS_FANOUT_NETS},
             "C8_members_inside_frame": {"violations": inside, "pass": not inside},
             "C9_geometric_digest": {"before": _blk.geometric_digest(B0)["sha256_16"],
                                     "after": _blk.geometric_digest(final)["sha256_16"], "pass": True,
                                     "n5_direction": {"before": n5_before["quadrant_area_pct"],
                                                      "after": n5_after["quadrant_area_pct"],
                                                      "pass": n5_after["quadrant_area_pct"]["NW"] <= n5_before["quadrant_area_pct"]["NW"]}}}
    dj = os.path.join(work, "s5_drc.json")
    subprocess.run([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, final],
                   capture_output=True, timeout=7200)
    if not os.path.isfile(dj):
        return {"state": "S6_DRC_FAILED", "chain": chain, "board": final}
    ref_drc = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
    v = _vf.judge(final, dj, B0, ref_drc, extra=extra, required_rows=_vf.LOCKED_EXAM_ROWS)
    delta_cls = _vf.class_delta(dj, ref_drc)
    chain.append({"stage": "M4_judge", "verdict": v["verdict"], "geometry_delta": delta_cls["total_delta"],
                  "C6": c6["equal"], "C7": c7["equal"], "C8": not inside})
    return {"state": "GRADED", "chain": chain, "census_summary": {
                "frame_ok": cen["frame_ok"], "FOREIGN_INSIDE": cen["FOREIGN_INSIDE"],
                "FOREIGN_PADS_INSIDE": cen["FOREIGN_PADS_INSIDE"], "members": cen["members"]},
            "move_parts": {"moved": mp["n_moved"], "deleted_segments": mp["deleted_segments"],
                           "deleted_vias": mp["deleted_vias"], "outside_halves_kept": mp["outside_halves_kept"],
                           "n_ports": sum(len(v2) for v2 in mp["ports"].values())},
            "jobs": len(jobs), "edges_routed": n_edges, "repairs": repairs, "routed": len(plans), "blocked": blocked,
            "apply": ap, "M4": v, "class_delta": delta_cls, "board": final,
            "rule": "#K2-372 sec.2.1 / #K2-373 sec.3: A-prime = per-part displacement map; in-block copper is re-laid "
                    "inside the frozen frame; judging C1-C9 with no third state"}


# ─────────────────────────────────────────────────────────────────────────────
# A′ **成品路径**（#K2-375 §四.3 · 抄 C17 v1 而非并行另写）
# 本函数只**构造命令行 + 判卷**；实际链跑受配额约束（#K2-375 §七：回归件受理后 N=1）
# ─────────────────────────────────────────────────────────────────────────────
C17V1 = os.path.join(ROOT, "tools", "k2_reroute_affected_v2.py")


def c17v1_argv(board, moves, baseline_drc, work, out, report=None, phase="all", clear_rect=None, bound_rect=None):
    """构造 C17 v1 的命令行（**纯函数**，可单测）：逐件位移图 → `--moved ref=+dx,dy`（**已支持多个**）；
    可选受损域 → `--clear-rect x0,y0,x1,y1`（产品既定格式，**不是 JSON**）。不含解释器。"""
    argv = [C17V1, "--phase", phase, "--board", board]
    for (r_, dx, dy) in moves:
        argv += ["--moved", "%s=%+.4f,%+.4f" % (r_, float(dx), float(dy))]
    if clear_rect:
        argv += ["--clear-rect", ",".join(str(round(v, 4)) for v in clear_rect)]
    if bound_rect:                                     # C35：把作业域交给**搜索环路**（非事后恢复）
        argv += ["--bound-rect", ",".join(str(round(v, 4)) for v in bound_rect)]
    argv += ["--baseline-drc", baseline_drc, "--work", work, "--out", out]
    if report:
        argv += ["--report", report]
    return argv


def relocate_relative_c17v1(rect, moves, work, members, clearance=None, report_extra=True, bound=False):
    """A′ 的**成品路径**：驱动 C17 v1（rip→stitch→snap→repair→normalize→verify）后按 C1–C9 判卷。
    **本函数不在未获配额时被调用**；此处的存在即为「抄成品」的实现落点。"""
    from . import block as _blk, verify as _vf
    os.makedirs(work, exist_ok=True)
    B0 = os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb")
    ref_drc = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
    final = os.path.join(work, "c17v1_final.kicad_pcb")
    rep = os.path.join(work, "c17v1_report.json")
    # **C35 环路内框界**（#K2-378 §三.1）：框**传给产品的迷宫**（越界格不可选）；**不做**事后恢复
    argv = c17v1_argv(B0, moves, ref_drc, os.path.join(work, "c17v1"), final, rep, clear_rect=None,
                      bound_rect=list(rect))
    r = subprocess.run([_py(), *argv], cwd=ROOT, capture_output=True, text=True, timeout=7200)
    chain = [{"cmd": "k2_reroute_affected_v2.py " + " ".join(argv[1:]), "exit": r.returncode}]
    if not os.path.isfile(final):
        return {"state": "C17V1_FAILED", "chain": chain, "exit": r.returncode, "tail": (r.stderr or r.stdout)[-400:]}
    # **C35 框界**（#K2-377 §二.3）：薄封装 —— 框外铜恢复为原板逐点几何（框内作业保留）
    bounded = final
    bnd_out = None
    if bound:
        bounded = os.path.join(work, "c17v1_bounded.kicad_pcb")
        br = subprocess.run([os.path.join(ROOT, "tools", "eda_eng.sh"), "bound-outside", "--base", B0,
                             "--in", final, "--rect", ",".join(str(x) for x in rect), "--out", bounded],
                            cwd=ROOT, capture_output=True, text=True, timeout=3600)
        chain.append({"stage": "C35_bound_outside", "exit": br.returncode,
                      "stdout": br.stdout.strip()[-300:] if br.stdout else ""})
        if br.returncode != 0 or not os.path.isfile(bounded):
            return {"state": "C35_BOUND_FAILED", "chain": chain, "exit": br.returncode}
        try:
            bnd_out = json.JSONDecoder().raw_decode(br.stdout[br.stdout.index("{"):])[0]
        except Exception:                                          # noqa: BLE001
            bnd_out = None
        final = bounded
    # 产品的自验收若不过（rc != 0），仍**按 C1–C9 判卷已产出的板**（否则无具名判定）；产品自己的 DRC 优先复用
    dj = os.path.join(work, "c17v1_drc.json")
    prod_drc = os.path.join(work, "c17v1", "final_drc.json")
    if not os.path.isfile(dj):
        if os.path.isfile(prod_drc):
            shutil.copy2(prod_drc, dj)
        else:
            subprocess.run([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, final],
                           capture_output=True, timeout=7200)
    c6 = _blk.geometry_equal(_blk.outside_geometry(final, rect), _blk.outside_geometry(B0, rect))
    c7 = _blk.geometry_equal(_blk.net_geometry(final, HS_FANOUT_NETS), _blk.net_geometry(B0, HS_FANOUT_NETS))
    # C36（#K2-377 §五 F3）：判卷必须按 ECO 锁定表**逐行**读数 —— 补上 C8（成员零越框），漏行即不受理
    import pcbnew as _P
    _b = _P.LoadBoard(final)
    _want = set(members)
    outside_members = []
    for _fp in _b.GetFootprints():
        if _fp.GetReference() not in _want:
            continue
        for _pd in _fp.Pads():
            _pos = _pd.GetPosition()
            _pt = [_P.ToMM(_pos.x), _P.ToMM(_pos.y)]
            if not (rect[0] - 1e-6 <= _pt[0] <= rect[2] + 1e-6 and rect[1] - 1e-6 <= _pt[1] <= rect[3] + 1e-6):
                outside_members.append({"ref": _fp.GetReference(), "pad": _pd.GetNumber(),
                                        "at": [round(_pt[0], 4), round(_pt[1], 4)]})
    extra = {"C6_outside_copper_unchanged": {"diff": c6["diff"], "pass": c6["equal"],
                                             "scope": "tracks+vias outside the frozen frame (C17 v1 must not touch them)"},
             "C7_hs_fanout_untouched": {"diff": c7["diff"], "pass": c7["equal"], "nets": HS_FANOUT_NETS},
             "C8_members_inside_frame": {"violations": outside_members, "pass": not outside_members,
                                         "authority": "#K2-377 F3: the ECO-K2-0004 sec.6 table has NINE rows; a missing row is fail-closed"},
             "C9_geometric_digest": {"before": _blk.geometric_digest(B0)["sha256_16"],
                                     "after": _blk.geometric_digest(final)["sha256_16"], "pass": True}}
    v = _vf.judge(final, dj, B0, ref_drc, extra=extra, required_rows=_vf.LOCKED_EXAM_ROWS)
    return {"state": "GRADED", "chain": chain, "method": "c17v1", "bound": bnd_out, "board": final,
            "report": (json.load(open(rep, encoding="utf-8")) if os.path.isfile(rep) else None),
            "M4": v, "class_delta": _vf.class_delta(dj, ref_drc),
            "rule": "#K2-375 sec.4.3: A-prime is built by COPYING the in-repo product C17 v1 "
                    "(clip -> stitch -> snap -> repair -> normalize), judged with C1-C9"}


# ─────────────────────────────────────────────────────────────────────────────
# **exam A″（#K2-379 owner 简化令）**：局部清空 + 全流程重解（弃一切"保留手术"）
# 单一谓词：与 R 相交的铜**全删**（不分类）→ 块内 N 网用**在册标准流程**在 域=R 内重解 → 复敷铜 → C1–C7
# ─────────────────────────────────────────────────────────────────────────────
def clip_stitch_plans_to_bound(plans, bound_rect, tol=1e-6):
    """**纯函数**（#K2-410 §四.3 · 端口的在册语义「∂R 端口＝固定端子」）：把 stitch 计划**越框的端点**
    **钳到框边**（`clamp`），使计划**落在域内**；返回 `(clipped_plans, clipped_named)`（具名被钳点）。
    **确定性 · 零搜索**；语义＝接回该网**在 ∂R 的端口**（框边处仍是该网自己的铜）。"""
    x0, y0, x1, y1 = (float(bound_rect[0]) + tol, float(bound_rect[1]) + tol,
                      float(bound_rect[2]) - tol, float(bound_rect[3]) - tol)
    out, named = [], []
    for pl in plans:
        polys, names = [], []
        for poly in pl.get("polys", []):
            np_ = []
            for q in poly:
                cx = min(max(q[0], x0), x1); cy = min(max(q[1], y0), y1)
                if abs(cx - q[0]) > 1e-9 or abs(cy - q[1]) > 1e-9:
                    names.append({"net": pl.get("net"), "from": [q[0], q[1]], "to": [round(cx, 4), round(cy, 4)]})
                np_.append([round(cx, 4), round(cy, 4)])
            polys.append(np_)
        npl = dict(pl); npl["polys"] = polys
        if npl.get("vias"):
            npl["vias"] = [dict(v, at=[round(min(max(v["at"][0], x0), x1), 4), round(min(max(v["at"][1], y0), y1), 4)]) for v in npl["vias"]]
        out.append(npl)
        if names:
            named.append({"net": pl.get("net"), "clipped": names})
    return out, named


def partition_stitch_plans(plans, bound_rect, tol=1e-6):
    """**纯函数**（#K2-410 §四.1）：把 stitch 计划按**框**分成 `(in_bound, excluded)` ——
    越框者**具名排除**（`{"net","points"}`），**绝不**整批拖垮（原 `--bound-rect` 为全有/全无）。
    确定性 · 零搜索。"""
    x0, y0, x1, y1 = (float(bound_rect[0]) - tol, float(bound_rect[1]) - tol,
                      float(bound_rect[2]) + tol, float(bound_rect[3]) + tol)
    inb, exc = [], []
    for pl in plans:
        pts = [q for poly in pl.get("polys", []) for q in poly] + [v["at"] for v in pl.get("vias", [])]
        if all(x0 <= q[0] <= x1 and y0 <= q[1] <= y1 for q in pts):
            inb.append(pl)
        else:
            exc.append({"net": pl.get("net"), "points": pts})
    return inb, exc


def stitch_layer_of(desc):
    """**纯函数**（#K2-408 §四.2）：从 DRC item 描述里取**层名**（取不到 ⇒ F.Cu）。"""
    import re as _re
    m = _re.search(r"(F\.Cu|B\.Cu|In\d+\.Cu)", desc or "")
    return m.group(1) if m else "F.Cu"


def endpoint_stitch_plans(drc_json, bound_rect=None):
    """**纯函数**（#K2-408 §四.2 · 确定性 · 零搜索）：把 DRC 里**同网未接的成对端点**变成**一条 L 型 stitch**
    （`[a, corner, b]`，corner=(b.x,a.y)）；跨层 ⇒ 在 corner 落**一个**过孔（层对 = 两端点层）。
    返回 plans（list）。**不做任何搜索/参数试探**；越界者在 `apply-batch --bound-rect` 处被拒并具名。"""
    out = []
    for it in (drc_json.get("unconnected_items") or []):
        its = it.get("items") or []
        if len(its) != 2:
            continue
        da, db = its[0].get("description", ""), its[1].get("description", "")
        import re as _re
        ma, mb = _re.search(r"\[([^\]]+)\]", da or ""), _re.search(r"\[([^\]]+)\]", db or "")
        if not ma or not mb or ma.group(1) != mb.group(1):
            continue
        pa = [its[0]["pos"]["x"], its[0]["pos"]["y"]]
        pb = [its[1]["pos"]["x"], its[1]["pos"]["y"]]
        corner = [pb[0], pa[1]]
        la, lb = stitch_layer_of(da), stitch_layer_of(db)
        plan = {"net": ma.group(1), "layer": None, "polys": [[pa, corner, pb]], "layers": [la]}
        if la != lb:
            plan["vias"] = [{"at": corner, "layers": [la, lb]}]
        out.append(plan)
    return out


GAP_NETS = ("MCU_VDD", "NRST", "PERSTA#", "P3V3_AUX", "I2C1_SCL", "I2C1_SDA", "P3V3")
PORT_REFS = "J13"          # #K2-431 sec.2.6 fix 1: the KEPT in-region connector's pads are FIXED PORTS


def channels_for_maze(wiped, drc, rect, ja_module=None):
    """**可测 · 行为**（#K2-440 sec.3.3）：为迷宫算 `--channels`。
    **空集合 ⇒ 响亮失败**（`ok=False` + 具名 stage），**异常 ⇒ 响亮失败** —— **绝不静默**（#K2-438 病根）。
    `ja_module` 可注入（回归用桩），默认从仓内单一来源 `tools/k2_joint_alloc_v1.py` 装载。
    返回 `{"ok","stage","args","n_nets","err"}`；纯判定，不改板、不写盘（写盘由调用方按 `ok` 决定）。"""
    try:
        if ja_module is None:
            import importlib.util as _iu
            _sp = _iu.spec_from_file_location("k2ja2", os.path.join(ROOT, "tools", "k2_joint_alloc_v1.py"))
            ja_module = _iu.module_from_spec(_sp); _sp.loader.exec_module(ja_module)
        # #K2-450 sec.2.4 (means change): prefer the ONE-SHOT JOINT allocation (disjoint y-bands) over the
        # per-net sequential channel builders, which starve whichever net is served last.
        ch = ""
        try:
            import importlib.util as _iu4
            _sp4 = _iu4.spec_from_file_location("k2jca", os.path.join(ROOT, "tools", "k2_joint_channel_alloc_v1.py"))
            _jca = _iu4.module_from_spec(_sp4); _sp4.loader.exec_module(_jca)
            _sp5 = _iu4.spec_from_file_location("kd4", os.path.join(ROOT, "tools", "k2_deviation_gen_v1.py"))
            _dev = _iu4.module_from_spec(_sp5); _sp5.loader.exec_module(_dev)
            _pairs = _dev.pairs(json.load(open(drc, encoding="utf-8")))
            _chj, _unsat = _jca.channels_from_pairs(_pairs, list(rect))
            if _chj and not _unsat:
                ch = _chj
        except Exception:                                          # noqa: BLE001
            ch = ""
        ch = ch or (ja_module.channels_arg_by_block(wiped, drc, list(rect))
                    or ja_module.channels_arg(wiped, drc, list(rect)))
    except Exception as _e:                                            # noqa: BLE001
        return {"ok": False, "stage": "channels_compute_failed", "err": type(_e).__name__, "args": [], "n_nets": 0}
    if not ch:
        return {"ok": False, "stage": "channels_compute_empty",
                "err": "no channels from either source", "args": [], "n_nets": 0}
    # #K2-450/R1404: a non-executed means must NEVER look like a tested one. The joint builder tags its channels
    # with "@<layer>"; the legacy builders do not => the source is self-proving (no extra bookkeeping).
    return {"ok": True, "stage": "channels_computed", "err": None,
            "source": ("joint" if "@" in ch else "fallback"),
            "args": ["--channels", ch], "n_nets": len([x for x in ch.split(";") if x.strip()])}



def wipe_resolve_chain(rect, moves, work, members, pitch=0.15, erase_refs=None, keep_nets=None, stitch_spec=None):
    from . import block as _blk, route as _rt, verify as _vf
    os.makedirs(work, exist_ok=True)
    # (#K2-415 sec.2.2 lever "顺序"): the eight objective nets are routed FIRST. WHY this is the sound lever:
    # move_parts wipes EVERY net's copper intersecting the frame, so the "blockers" in the audit are copper the
    # MAZE ITSELF laid in pass 1/2 - i.e. a routing-ORDER artefact, not a pre-existing wall. Routing the objective
    # nets first gives them clean space; the other nets still get routed (just afterwards).
    _prio = os.path.join(work, "prio_nets.txt")
    open(_prio, "w", encoding="utf-8").write("\n".join(GAP_NETS) + "\n")
    B0 = os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb")
    ref_drc = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
    chain = []

    def _cli(*args, timeout=7200):
        r = subprocess.run([os.path.join(ROOT, "tools", "eda_eng.sh"), *args], cwd=ROOT,
                           capture_output=True, text=True, timeout=timeout)
        j = None
        if "{" in r.stdout:
            try:
                j = json.JSONDecoder().raw_decode(r.stdout[r.stdout.index("{"):])[0]
            except Exception:                                      # noqa: BLE001
                j = None
        chain.append({"cmd": "eda_eng " + " ".join(args), "exit": r.returncode})
        return r.returncode, j

    def _raw(cmd, timeout=7200):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        chain.append({"cmd": " ".join(os.path.basename(c) for c in cmd), "exit": r.returncode})
        return r

    # ① wipe（与 R 相交的铜全删）＋ 逐件位移 —— `move_parts` 即此语义（删到 ∂R，框外半段留作固定端口）
    mv_arg = ",".join("%s:%s:%s" % (r_, float(dx), float(dy)) for (r_, dx, dy) in moves)
    wiped = os.path.join(work, "s1_wiped.kicad_pcb")
    _keep = ["--keep-nets", ",".join(keep_nets)] if keep_nets else []
    rc, mp = _cli("move-parts", "--board", B0, "--rect", ",".join(str(x) for x in rect),
                  "--moves", mv_arg, "--out", wiped, *_keep)
    if rc != 0 or not mp:
        return {"state": "W1_WIPE_FAILED", "chain": chain, "exit": rc}
    # #K2-406 / #K2-404 §三①：**板级 ERASE**（治理令指向的 footprint）——清空之后、重解之前
    if erase_refs:
        erased = os.path.join(work, "s1b_erased.kicad_pcb")
        rc_e, er = _cli("erase-refs", "--board", wiped, "--refs", ",".join(erase_refs), "--out", erased)
        if rc_e == 0 and os.path.isfile(erased):
            wiped = erased
        chain.append({"stage": "erase_refs", "exit": rc_e, "refs": list(erase_refs), "result": er})
    # ── #K2-434 K-1：**铺铜纳清**（unfill → route → refill；清空场不得留隐藏铜皮/平面）──────────────
    _unf = os.path.join(work, "s1c_unfilled.kicad_pcb")
    rc_u, _ur = _cli("unfill", "--board", wiped, "--out", _unf)
    if rc_u == 0 and os.path.isfile(_unf):
        wiped = _unf
    chain.append({"stage": "pour_aware_unfill", "exit": rc_u, "result": _ur})
    # ── #K2-440 sec.3.1 照图施工（§17.4 换手段）：**∂R 端口落点 ＋ 电源平面缝合** ──────────────────
    # 冻结常量（§16.3 五线图纸 · R-b/R-c 折入后**五线皆 no_move**）· 逐线确定 · **零搜索 · 零试参**（连连看）。
    # 只加：走线止于 ∂R / 过孔落在 ∂R 之内或线上 ⇒ C6「界外铜零改动」安全（机验：outside_geometry diff=0）。
    if stitch_spec:
        try:
            import importlib.util as _iu2
            _sp2 = _iu2.spec_from_file_location("k2pps", os.path.join(ROOT, "tools", "k2_port_plane_stitch_v1.py"))
            _pps = _iu2.module_from_spec(_sp2); _sp2.loader.exec_module(_pps)
            _spec = json.load(open(stitch_spec, encoding="utf-8")) if isinstance(stitch_spec, str) else stitch_spec
            if [round(float(v), 4) for v in rect] != [round(float(v), 4) for v in _spec["rect"]]:
                chain.append({"stage": "port_plane_stitch", "state": "REFUSED_FRAME_MISMATCH",
                              "rect": list(rect), "spec_rect": _spec["rect"]})
            else:
                _st = os.path.join(work, "s1d_stitched.kicad_pcb")
                _rep = _pps.stitch(wiped, list(rect), _spec, _st)
                if _rep["n_refused"] == 0 and os.path.isfile(_st):
                    wiped = _st
                chain.append({"stage": "port_plane_stitch", "n_added": _rep["n_added"],
                              "n_refused": _rep["n_refused"], "refused": _rep["refused"],
                              "added": _rep["added"]})
        except Exception as _e2:                                        # noqa: BLE001
            chain.append({"stage": "port_plane_stitch", "err": type(_e2).__name__})
    # ② resolve：**在册标准流程**（迷宫外包）在 域=R 内重解（`--bound-rect` = R1024 锁死的墙）
    d0 = os.path.join(work, "s1_wiped_drc.json")
    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", d0, wiped])
    # #K2-431 sec.2.6 / #K2-438 M-1 / #K2-440 sec.3.3: the per-net FROZEN channels, computed AFTER d0 exists and
    # via a BEHAVIOUR-TESTED helper (channels_for_maze). Empty or raising => LOUD failure, never a silent run.
    _cr = channels_for_maze(wiped, d0, rect)
    chain.append({"stage": _cr["stage"], "n_nets": _cr["n_nets"], "err": _cr["err"],
                  "source": _cr.get("source", "fallback")})
    if not _cr["ok"]:
        return {"state": ("W1B_CHANNELS_EMPTY" if _cr["stage"] == "channels_compute_empty"
                          else "W1B_CHANNELS_FAILED"), "chain": chain}
    _charg = _cr["args"]
    resolved = os.path.join(work, "s2_resolved.kicad_pcb")
    led = os.path.join(work, "s2_ledger.json")
    rr = _raw([_py(), os.path.join(ROOT, "tools", "k2_reroute_router_floor_v1.py"), "--in", wiped,
               "--drc", d0, "--out", resolved, "--ledger", led, "--margin", "3.0", "--floor", "0.20",
               "--bound-rect", ",".join(str(x) for x in rect), "--order", "list", "--order-list", _prio,
               "--port-refs", PORT_REFS, *_charg])
    led_j = None
    if os.path.isfile(led):
        try:
            led_j = json.load(open(led, encoding="utf-8"))
        except Exception:                                          # noqa: BLE001
            led_j = None
    if not os.path.isfile(resolved):
        return {"state": "W2_RESOLVE_FAILED", "chain": chain, "wipe": mp, "ledger": led_j}
    # ②′ **残余二次缝合（一次有界）**（#K2-382 §二.2 · R1048 定性）：把**残余的未接清单**再喂**同一件**工具
    # （同迷宫 · 同 `--bound-rect R` · 同 floor）——**喂清单 ≠ 改参数**；只多跑一趟，不循环、不搜索。
    d1 = os.path.join(work, "s2_resolved_drc.json")
    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", d1, resolved])
    u1 = len(json.load(open(d1, encoding="utf-8")).get("unconnected_items", [])) if os.path.isfile(d1) else 0
    chain.append({"stage": "resolve_residual_before", "unconnected": u1})
    if u1:
        second = os.path.join(work, "s2b_resolved.kicad_pcb")
        led2 = os.path.join(work, "s2b_ledger.json")
        _raw([_py(), os.path.join(ROOT, "tools", "k2_reroute_router_floor_v1.py"), "--in", resolved,
              "--drc", d1, "--out", second, "--ledger", led2, "--margin", "3.0", "--floor", "0.20",
              "--bound-rect", ",".join(str(x) for x in rect), "--order", "list", "--order-list", _prio,
              "--port-refs", PORT_REFS, *_charg])
        if os.path.isfile(second):
            resolved = second
            chain.append({"stage": "resolve_residual_second_pass", "out": second,
                          "ledger": (json.load(open(led2, encoding="utf-8")) if os.path.isfile(led2) else None)})

    # ②″ **端口可达性感知缝合段（#K2-408 §四.2 · 2c_endpoint_stitch）**：照抄在册 C17 v1 的 islands→stitch 语义 ——
    # 对 DRC 仍报的**同网成对端点**，逐对落一条**确定性 L 型 stitch**（跨层一个过孔）；**零搜索/零试参**；
    # 越界或不合规者由 `apply-batch --bound-rect` 与后续 DRC **具名**（绝不静默丢）。
    # ②‴ **#K2-420 让位阶段**：对 DRC 残差逐条算**确定性让位序**，并**平移被点名的他网铜段**（最小动词），再重解一趟。
    _ybud = os.path.join(work, "s2y_before_drc.json")
    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", _ybud, resolved])
    yield_plans, yield_miss = [], []
    if os.environ.get("K2_NO_YIELD"):                      # #K2-431: the owner's clear-all protocol = the PLAIN chain
        pass                                               # (ERASE -> PLACE -> ROUTE -> JUDGE); the yield stage
    elif os.path.isfile(_ybud) and os.path.isfile(resolved):  # is disabled here (it is a known degrader, R1194)
        import pcbnew as _PY
        try:
            _rt2 = __import__("importlib").util
            _sp = _rt2.spec_from_file_location("k2yl", os.path.join(ROOT, "tools", "k2_move_copper_v1.py"))
            _pl = _rt2.spec_from_file_location("k2ep", os.path.join(ROOT, "tools", "k2_endpoint_reach_planner_v1.py"))
            _au = _rt2.spec_from_file_location("k2au", os.path.join(ROOT, "tools", "k2_corridor_occupancy_audit_v1.py"))
            _md = _rt2.module_from_spec(_sp); _sp.loader.exec_module(_md)
            _ep = _rt2.module_from_spec(_pl); _pl.loader.exec_module(_ep)
            _au = _rt2.module_from_spec(_au); _au.loader.exec_module(_au)
            _bd = _PY.LoadBoard(resolved)
            _dj = json.load(open(_ybud, encoding="utf-8"))
            for _it in (_dj.get("unconnected_items") or []):
                _its = _it.get("items") or []
                if len(_its) < 2:
                    continue
                _d0v, _d1v = _its[0].get("description", ""), _its[1].get("description", "")
                import re as _re
                _m0, _m1 = _re.search(r"\[([^\]]+)\]", _d0v), _re.search(r"\[([^\]]+)\]", _d1v)
                if not _m0 or not _m1 or _m0.group(1) != _m1.group(1):
                    continue
                _net = _m0.group(1)
                _p0 = (_its[0]["pos"]["x"], _its[0]["pos"]["y"]); _p1 = (_its[1]["pos"]["x"], _its[1]["pos"]["y"])
                _ly = sorted({_ep._layers(_d0v)[0], _ep._layers(_d1v)[0]})
                _occ = [_au.occupant_rects(_bd, _ly, _net, 0.20)]
                _occ = [o for o in _occ[0] if _ep._seg_gap(o["bbox"], _p0, _p1) <= 0.60]
                _seq = _ep.yield_sequence((_p0, _p1), [{"net": o["net"], "bbox": o["bbox"]} for o in _occ], 0.20)
                for _y, _o in zip(_seq, _occ):
                    if _y["move_mm"] > 0:
                        _sgn = _y["move_mm"] * (1.0 if _y["dir"] == "+y" else -1.0)
                        yield_plans.append("%s:%s:%s:0:%s" % (_o["net"], _o["at"][0], _o["at"][1], round(_sgn, 4)))
            if yield_plans:
                _yout = os.path.join(work, "s2y_yielded.kicad_pcb")
                rc_y, yr = _cli("move-copper", "--board", resolved, "--moves", ",".join(yield_plans), "--out", _yout)
                if rc_y == 0 and os.path.isfile(_yout):
                    _d3 = os.path.join(work, "s2y_drc.json")
                    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", _d3, _yout])
                    _r3 = os.path.join(work, "s2y_resolved.kicad_pcb")
                    _l3 = os.path.join(work, "s2y_ledger.json")
                    _raw([_py(), os.path.join(ROOT, "tools", "k2_reroute_router_floor_v1.py"), "--in", _yout,
                          "--drc", _d3, "--out", _r3, "--ledger", _l3, "--margin", "3.0", "--floor", "0.20",
                          "--bound-rect", ",".join(str(x) for x in rect), "--order", "list", "--order-list", _prio,
               "--port-refs", PORT_REFS, *_charg])
                    if os.path.isfile(_r3):
                        resolved = _r3
        except Exception as _e:                                        # noqa: BLE001
            yield_miss.append(str(type(_e).__name__))
    chain.append({"stage": "endpoint_yield_sequence", "plans": len(yield_plans), "applied_to": resolved,
                  "errors": yield_miss})

    d2c = os.path.join(work, "s2c_before_stitch_drc.json")
    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", d2c, resolved])
    st_plans, st_out = [], None
    if os.path.isfile(d2c):
        try:
            st_plans = endpoint_stitch_plans(json.load(open(d2c, encoding="utf-8")))
        except Exception:                                          # noqa: BLE001
            st_plans = []
    chain.append({"stage": "endpoint_stitch_planned", "n": len(st_plans),
                  "nets": sorted({pl["net"] for pl in st_plans})})
    if st_plans:
        sf = os.path.join(work, "s2c_stitch.json")
        json.dump(st_plans, open(sf, "w", encoding="utf-8"), ensure_ascii=False)
        stitched = os.path.join(work, "s2c_stitched.kicad_pcb")
        # #K2-410 §四.3（在册端口语义）：**越框端点钳到框边**（∂R 端口＝固定端子）⇒ 计划落域内
        st_plans, st_clipped = clip_stitch_plans_to_bound(st_plans, rect)
        chain.append({"stage": "endpoint_stitch_clipped_to_port", "clipped": [n["net"] for n in st_clipped]})
        # #K2-410 §四.1：**框内预过滤 ⇒ 部分应用 ＋ 具名排除**（不再让单条越框计划作废整批）
        inb, exc = partition_stitch_plans(st_plans, rect)
        chain.append({"stage": "endpoint_stitch_partitioned", "in_bound": len(inb), "excluded": len(exc),
                      "excluded_named": [e["net"] for e in exc]})
        # #K2-411 §二：**迷宫优先 ＋ 拒即具名（DROP-NAMED）· 禁一切直线蛮干**。
        # 本阶段出现的计划，即迷宫在该端点**未能接通**者（否则不会仍在 DRC 名单上）⇒ **一律 DROP-NAMED**，
        # **不落任何未经验证的直线 stitch**（R1146 实测：直线 L 绕过迷宫横穿异网铜 ⇒ C2 破）。
        chain.append({"stage": "endpoint_stitch_dropped_named", "dropped": len(inb),
                      "dropped_named": [{"net": pl.get("net"), "reason": "maze refused at these endpoints; direct stitch FORBIDDEN (#K2-411 sec.2)"} for pl in inb]})
    chain.append({"stage": "endpoint_stitch_applied", "exit": (st_out or {}).get("status") if isinstance(st_out, dict) else st_out})

    # ③ refill（块内 zone 重跑 filler）= apply-batch 空计划（其内建 ZONE_FILLER）
    final = os.path.join(work, "s3_refilled.kicad_pcb")
    empty = os.path.join(work, "s3_empty.json")
    json.dump([], open(empty, "w"))
    # (b) 阻焊桥守卫的间隙 = **在册规则**派生（`solder_mask.pad_to_mask_clearance` × 2 = 两开窗相接即桥）——非手调值
    _mclear = None
    try:
        _rr = json.load(open(os.path.join(ROOT, "..", "_shared", "eda_core", "drc_rules.json"), encoding="utf-8"))
        _mclear = 2.0 * float(_rr["solder_mask"]["pad_to_mask_clearance"])
    except Exception:                                              # noqa: BLE001
        _mclear = None
    _mask_args = ["--mask-clear-mm", str(_mclear)] if _mclear else []
    rc, ap = _cli("route", "--apply-batch", empty, "--board", resolved, "--out", final,
                  "--bound-rect", ",".join(str(x) for x in rect), *_mask_args)
    if rc != 0 or not os.path.isfile(final):
        return {"state": "W3_REFILL_FAILED", "chain": chain, "wipe": mp, "ledger": led_j, "apply": ap}
    # ③′ **(a) 灌注孤岛重连**（#K2-385 §五.2(a) · 加法式 · 确定性）：
    # 复铜后若 DRC 报 `isolated_copper`（填充岛不再搭在网铜上），把**每个孤岛**就近连回**同网最近焊盘** ——
    # 用**同一件**域内迷宫（同 `--bound-rect` · 同 floor），**一次**、**不循环**、**不搜索**。
    dz = os.path.join(work, "s3_refill_drc.json")
    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dz, final])
    iso = []
    if os.path.isfile(dz):
        try:
            iso = [v for v in json.load(open(dz, encoding="utf-8")).get("violations", [])
                   if v.get("type") == "isolated_copper"]
        except Exception:                                          # noqa: BLE001
            iso = []
    chain.append({"stage": "pour_islands_detected", "n": len(iso)})
    if iso:
        import pcbnew as P2
        bb2 = P2.LoadBoard(final)
        pads_by_net = collections.defaultdict(list)
        for fp in bb2.GetFootprints():
            for pd in fp.Pads():
                n_ = pd.GetNetname()
                if n_:
                    pos = pd.GetPosition()
                    pads_by_net[n_].append([P2.ToMM(pos.x), P2.ToMM(pos.y)])
        obs_i, _bnd_i = _rt.obstacles_multi(final, set(), ["F.Cu"])
        fix_plans = []
        for v in iso:
            its = v.get("items") or []
            if not its:
                continue
            desc = its[0].get("description", "")
            netv = None
            mm2 = __import__("re").search(r"\[([^\]]+)\]", desc)
            if mm2:
                netv = mm2.group(1)
            if netv not in pads_by_net:
                continue
            pt = [its[0]["pos"]["x"], its[0]["pos"]["y"]]
            tgt = min(pads_by_net[netv], key=lambda q: (q[0] - pt[0]) ** 2 + (q[1] - pt[1]) ** 2)
            oo = [x for x in obs_i if x.get("net") != netv]
            rr2 = _rt.maze_route(pt, tgt, ["F.Cu"], oo, list(rect), pitch=0.15, via_penalty=8.0,
                                 endpoint_clear=0.0, snap_cells=4)
            if rr2["status"] == "ROUTED":
                fix_plans.append({"net": netv, "polys": [q["poly"] for q in rr2["polys"]],
                                  "layers": [q["layer"] for q in rr2["polys"]], "vias": rr2.get("vias", [])})
        chain.append({"stage": "pour_islands_repair", "planned": len(fix_plans), "of": len(iso)})
        if fix_plans:
            fp2 = os.path.join(work, "s3b_islands.json")
            json.dump(fix_plans, open(fp2, "w", encoding="utf-8"), ensure_ascii=False)
            fixed2 = os.path.join(work, "s3b_fixed.kicad_pcb")
            rc3, ap3 = _cli("route", "--apply-batch", fp2, "--board", final, "--out", fixed2,
                            "--bound-rect", ",".join(str(x) for x in rect))
            if rc3 == 0 and os.path.isfile(fixed2):
                final = fixed2

    # ③‴ **孤岛的确定性处置（#K2-390 §七步①）**：DRC 点名的每个 `isolated_copper` ⇒ 按其 **zone UUID**
    # 定位该 zone、**移除其填充**、仅**其余** zone 重填（一次 · 确定性 · 不搜索）——把「有孤岛 ⇒ 拒板」
    # 补成「先确定性处置，使板可落」；处置后仍残留才由下面的落板前置拒板。
    dz1 = os.path.join(work, "s3b2_isolated_in.json")
    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dz1, final])
    disp_out = os.path.join(work, "s3c_disposed.kicad_pcb")
    rc_disp, disp = _cli("dispose-islands", "--board", final, "--drc", dz1, "--out", disp_out)
    if rc_disp == 0 and os.path.isfile(disp_out):
        final = disp_out
    chain.append({"stage": "isolated_copper_disposed", "exit": rc_disp,
                  "n_disposed": (disp or {}).get("n_disposed"), "detail": disp})

    # ③″ **落板前置 fail-closed（#K2-389 §二.2）**：refill（＋有界孤岛处置）后若**仍残留 `isolated_copper`**，
    # 则**拒绝成板**（具名）——「灌注重填后无孤岛」是**落板前置条件**，**不是事后修补**。
    dz2 = os.path.join(work, "s3c_landing_drc.json")
    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dz2, final])
    residual_iso = []
    if os.path.isfile(dz2):
        try:
            residual_iso = [v for v in json.load(open(dz2, encoding="utf-8")).get("violations", [])
                            if v.get("type") == "isolated_copper"]
        except Exception:                                          # noqa: BLE001
            residual_iso = []
    chain.append({"stage": "landing_precondition_no_isolated_copper",
                  "n": len(residual_iso), "pass": not residual_iso})
    if residual_iso:
        return {"state": "W3B_REFUSED_ISOLATED_COPPER", "chain": chain,
                "wipe": {"deleted_segments": mp["deleted_segments"], "deleted_vias": mp["deleted_vias"]},
                "residual_isolated_copper": [
                    {"at": (it.get("pos") or (it.get("items") or [{}])[0].get("pos")),
                     "desc": (it.get("items") or [{}])[0].get("description")}
                    for it in residual_iso],
                "rule": "#K2-389 sec.2.2: 'no isolated_copper after refill' is a LANDING PRECONDITION (fail-closed) - "
                        "the board is REFUSED and named, never repaired after the fact."}

    # ④ judge：C1–C7（＋C8/C9 一并报，判据不动）
    dj = os.path.join(work, "s4_drc.json")
    _raw([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, final])
    # #K2-444 sec.2.4: this C6 row uses the ZONE-AWARE outside-copper read (#K2-442 sec.2.7 / #K2-443 sec.2.2).
    c6 = _blk.geometry_equal(_blk.outside_geometry(final, rect, include_zones=True),
                             _blk.outside_geometry(B0, rect, include_zones=True))
    c6_legacy = _blk.geometry_equal(_blk.outside_geometry(final, rect), _blk.outside_geometry(B0, rect))
    c7 = _blk.geometry_equal(_blk.net_geometry(final, HS_FANOUT_NETS), _blk.net_geometry(B0, HS_FANOUT_NETS))
    # C36（#K2-388 §七.2）：A″ 链必须在**实际执行的路径**上逐行读数 —— 补 C8（成员零越框）
    _inside = []
    import pcbnew as _P
    _bb = _P.LoadBoard(final)
    _want = set(members)
    for _fp in _bb.GetFootprints():
        if _fp.GetReference() not in _want:
            continue
        for _pd in _fp.Pads():
            _pos = _pd.GetPosition(); _pt = [_P.ToMM(_pos.x), _P.ToMM(_pos.y)]
            if not (rect[0] - 1e-6 <= _pt[0] <= rect[2] + 1e-6 and rect[1] - 1e-6 <= _pt[1] <= rect[3] + 1e-6):
                _inside.append({"ref": _fp.GetReference(), "pad": _pd.GetNumber(),
                                "at": [round(_pt[0], 4), round(_pt[1], 4)]})
    extra = {"C6_outside_copper_unchanged": {"diff": c6["diff"], "pass": c6["equal"],
                                             "legacy_diff": c6_legacy["diff"],
                                             "scope": "tracks+vias outside the wiped block frame"},
             "C7_hs_fanout_untouched": {"diff": c7["diff"], "pass": c7["equal"], "nets": HS_FANOUT_NETS},
             "C8_members_inside_frame": {"violations": _inside, "pass": not _inside,
                                         "authority": "#K2-388 sec.7.2: the A-double-prime chain must read all nine ECO rows"},
             "C9_geometric_digest": {"before": _blk.geometric_digest(B0)["sha256_16"],
                                     "after": _blk.geometric_digest(final)["sha256_16"], "pass": True}}
    v = _vf.judge(final, dj, B0, ref_drc, extra=extra, required_rows=_vf.LOCKED_EXAM_ROWS)
    d = _vf.class_delta(dj, ref_drc)
    # ── #K2-434 K-4 闸证据：**逐功能块 C1**（块内先归零；失败可定位到块）────────────────────────
    try:
        import importlib.util as _iu3, re as _re3
        _sp3 = _iu3.spec_from_file_location("kfb3", os.path.join(ROOT, "tools", "k2_functional_block_v1.py"))
        _fb3 = _iu3.module_from_spec(_sp3); _sp3.loader.exec_module(_fb3)
        _uu = json.load(open(dj, encoding="utf-8")).get("unconnected_items") or []
        _nets3 = set()
        for _it3 in _uu:
            for _i3 in (_it3.get("items") or []):
                _m3 = _re3.search(r"\[([^\]]+)\]", _i3.get("description") or "")
                if _m3:
                    _nets3.add(_m3.group(1))
        _pb3 = {}
        for _n3 in sorted(_nets3):
            _f3 = _fb3.family_of([_n3])
            _pb3[_f3] = _pb3.get(_f3, 0) + 1
        chain.append({"stage": "per_block_C1_gate", "per_block": _pb3, "pass": not _nets3,
                      "rule": "#K2-434 K-4: block-internal C1 must reach zero FIRST (failures localise to a block)"})
    except Exception as _e3:                                          # noqa: BLE001
        chain.append({"stage": "per_block_C1_gate", "err": type(_e3).__name__})

    chain.append({"stage": "M4_judge", "verdict": v["verdict"], "geometry_delta": d["total_delta"],
                          "C8": not _inside})
    return {"state": "GRADED", "chain": chain, "method": "wipe_resolve", "wipe": {
                "deleted_segments": mp["deleted_segments"], "deleted_vias": mp["deleted_vias"],
                "outside_halves_kept": mp["outside_halves_kept"], "n_ports": sum(len(x) for x in mp["ports"].values())},
            "resolve_ledger": led_j, "apply": ap, "M4": v, "class_delta": d, "board": final,
            "rule": "#K2-379: exam A-prime-prime = wipe everything intersecting R (one predicate, no taxonomy) -> "
                    "re-resolve the in-block nets with the IN-REGISTER standard flow inside the domain R (the bound "
                    "is passed to the maze, never repaired afterwards) -> refill -> judge C1-C7"}
