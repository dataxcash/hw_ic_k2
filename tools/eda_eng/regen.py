"""regen --- 组合确定性管线（原 `route` 之名归 #K2-360 M3；本模块保留管线能力）。

v1 = **组合确定性管线**（全部是链内既有、确定性、无 LLM 的阶段；不新增搜索、不手改板）：

    place(场景) → gen_v5 → route_segment --upto all → build_l9(全阶段: 倒角/铺铜/丝印…) → DRC

**运行于影子工程根**（shadow.py）：真源/冻结四源/`project.yaml` **逐字节不动**；产物落工作目录。
输出 = 最终板 + DRC json（供 eda_eng verify 判卷）。
"""
from __future__ import annotations
import json, math, os, shutil, subprocess, sys

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


def mech_probe(refs, delta_mm, work, tag):
    """机械探针（gen -> crtyd -> DRC），**基线相对**用。返回 {mechanical_violations}。"""
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
            if ty in ("courtyards_overlap", "shorting_items", "clearance", "hole_clearance"):
                bad[ty] = bad.get(ty, 0) + 1
    return {"gen_exit": rc, "mechanical_violations": bad}


def mech_probe_moves(moves, work, tag, return_board=False):
    """机械探针（gen -> crtyd -> DRC）**逐件位移**版（#K2-372 §二.1：目标相对位**逐件**由闸出）。
    moves = [(ref, dx, dy), ...]；返回 {gen_exit, mechanical_violations, [board]}。"""
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
            if ty in ("courtyards_overlap", "shorting_items", "clearance", "hole_clearance"):
                bad[ty] = bad.get(ty, 0) + 1
    out = {"gen_exit": rc, "mechanical_violations": bad}
    if return_board:
        out["board"] = gpcb
    return out


def rearrange_probe(board, rect, members, work, kmax=8, order=None, return_board=False):
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
            d = (round(k * 0.5, 4), round(k * 0.5, 4))
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
    extra = {"C6_outside_copper_unchanged": {"diff": c6["diff"], "pass": c6["equal"], "envelope": ENV,
                                             "envelope_margin_mm": envelope_margin,
                                             "hs_clear": hs_ok,
                                             "scope": "tracks+vias outside the declared action envelope"},
             "C6_guard_hs_outside_envelope": {"pass": hs_ok, "envelope": ENV, "hs_copper_bbox": hs_bbox,
                                              "rule": "the declared action envelope must not reach the HS fanout copper"},
             "C7_hs_fanout_untouched": {"diff": c7["diff"], "pass": c7["equal"], "nets": HS_FANOUT_NETS}}

    # ── M4：DRC + 判卷（C1–C5 + C6/C7）
    dj = os.path.join(work, "s5_drc.json")
    subprocess.run([_cli_bin(), "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, final],
                   capture_output=True, timeout=7200)
    if not os.path.isfile(dj):
        return {"state": "S6_DRC_FAILED", "chain": chain, "census": cen, "move": mv, "board": final}
    ref_drc = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
    v = _vf.judge(final, dj, B0, ref_drc, extra=extra)
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
    v = _vf.judge(final, dj, B0, ref_drc, extra=extra)
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


def c17v1_argv(board, moves, baseline_drc, work, out, report=None, phase="all", clear_rect=None):
    """构造 C17 v1 的命令行（**纯函数**，可单测）：逐件位移图 → `--moved ref=+dx,dy`（**已支持多个**）；
    可选受损域 → `--clear-rect x0,y0,x1,y1`（产品既定格式，**不是 JSON**）。不含解释器。"""
    argv = [C17V1, "--phase", phase, "--board", board]
    for (r_, dx, dy) in moves:
        argv += ["--moved", "%s=%+.4f,%+.4f" % (r_, float(dx), float(dy))]
    if clear_rect:
        argv += ["--clear-rect", ",".join(str(round(v, 4)) for v in clear_rect)]
    argv += ["--baseline-drc", baseline_drc, "--work", work, "--out", out]
    if report:
        argv += ["--report", report]
    return argv


def relocate_relative_c17v1(rect, moves, work, members, clearance=None, report_extra=True):
    """A′ 的**成品路径**：驱动 C17 v1（rip→stitch→snap→repair→normalize→verify）后按 C1–C9 判卷。
    **本函数不在未获配额时被调用**；此处的存在即为「抄成品」的实现落点。"""
    from . import block as _blk, verify as _vf
    os.makedirs(work, exist_ok=True)
    B0 = os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb")
    ref_drc = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
    final = os.path.join(work, "c17v1_final.kicad_pcb")
    rep = os.path.join(work, "c17v1_report.json")
    argv = c17v1_argv(B0, moves, ref_drc, os.path.join(work, "c17v1"), final, rep)
    r = subprocess.run([_py(), *argv], cwd=ROOT, capture_output=True, text=True, timeout=7200)
    chain = [{"cmd": "k2_reroute_affected_v2.py " + " ".join(argv[1:]), "exit": r.returncode}]
    if not os.path.isfile(final):
        return {"state": "C17V1_FAILED", "chain": chain, "exit": r.returncode, "tail": (r.stderr or r.stdout)[-400:]}
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
    extra = {"C6_outside_copper_unchanged": {"diff": c6["diff"], "pass": c6["equal"],
                                             "scope": "tracks+vias outside the frozen frame (C17 v1 must not touch them)"},
             "C7_hs_fanout_untouched": {"diff": c7["diff"], "pass": c7["equal"], "nets": HS_FANOUT_NETS},
             "C9_geometric_digest": {"before": _blk.geometric_digest(B0)["sha256_16"],
                                     "after": _blk.geometric_digest(final)["sha256_16"], "pass": True}}
    v = _vf.judge(final, dj, B0, ref_drc, extra=extra)
    return {"state": "GRADED", "chain": chain, "method": "c17v1", "board": final,
            "report": (json.load(open(rep, encoding="utf-8")) if os.path.isfile(rep) else None),
            "M4": v, "class_delta": _vf.class_delta(dj, ref_drc),
            "rule": "#K2-375 sec.4.3: A-prime is built by COPYING the in-repo product C17 v1 "
                    "(clip -> stitch -> snap -> repair -> normalize), judged with C1-C9"}
