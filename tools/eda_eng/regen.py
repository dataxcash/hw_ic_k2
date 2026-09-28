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
