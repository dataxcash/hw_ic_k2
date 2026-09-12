#!/usr/bin/env python3
"""CO-143：【L2 分析 · 只读】逃生扇「对间 3W」缺陷定位修正 + 施加可行性研究。

背景（修正 CO-141 附记2 的定位）：CO-141 把 `tool_defect:k2_router_escape_fan_omits_3w`
归因到 f13 `pair_xorder`（`p3_v57_f13_r1_pair_xorder.py` / v1_1 工件）。**该定位不成立**：
现行 G4 基线走 `--r1-5-shape co16`，其 R1 逃生列由 `co16_prepare()` **O(1) 消费
`m13_v57_co16_channel_allocation_v7.json`（CO16-ALLOC.7）**，`r1_place()` / `pair_xorder` 在 co16
路径**根本不执行**（CO-141 附记2 的两次实验因此是 no-op，其「排除/非绑定」结论无效）。

真实产生阶段（CO-142 逐条归因，24 个平行对-对）：**B.Cu 14 = 逃生竖列**（扇落位），
F.Cu 10 = J2 接口 land 段（0.6 节距 < 3w，L1 固有）。B.Cu 逃生竖列 x 由
`p3_v57_co10_west_fan_probe.py` 的**单遍贪心落位判据** `check()` 决定，而 `check()` 的
track-track 判据是 `TT = WID + CLEAR = 0.38`（净距口径）**不含 3W 下界 3*w(layer)** ⇒ 缺陷所在。

本件（只读，不改几何/板/冻结四源）：
  A. 机判缺陷存在：基线扇几何的 B.Cu 逃生竖列对间中心距最小值 < 3*w(B.Cu)=0.615。
  B. 机判「并入 3W」可单独达成（opt-in 旋钮 CO10_IP3W=1）：32/32 落位 + 对间中心距 >= 0.615。
  C. 机判「并入 3W + PDN 固定障碍」（CO10_PDN_OBS=1）在**单遍贪心**下**落位不全**（rev 31/32、
     xasc 30/32）；并给出失败页与失败原因（区分「PDN via 冲突」/「贪心夹死」）。
  D. 独立 DP（分带、按 pad-x 升序单调）机判：B.Cu 两带**存在**满足 3W + pad/PDN 合法性的
     单调列分配 ⇒ 结论 = **约束可满足，单遍贪心策略不足**（须重派生扇落位策略，非阈值参数问题）。
  E. 记录**已还原**的施加实验：把 3W 直接并入 check 并重生成 ALLOC/G4/L4 后，板出现
     +3 clearance 违规（UP0/out_J2 N corner via × GND stitch via (83.575,56.516)，铜距 0.1587 < 0.175）
     ⇒ 不做 PDN 障碍感知就落板会引入 DRC 回归。

CLI: python3 tools/p3_v57_co143_escape_fan_3w_feasibility.py（须系统 python3/numpy；本件不用 pcbnew）
"""
from __future__ import annotations
import hashlib, json, math, os, shutil, subprocess, sys, tempfile
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
ALLOC7 = STEP2 / "m13_v57_co16_channel_allocation_v7.json"
REC = STEP2 / "m13_v57_co143_escape_fan_3w_feasibility.json"
CARD = STEP2 / "m13_v57_CO143_escape_fan_3w_feasibility.md"
WBY = json.loads(SPEC.read_text(encoding="utf-8"))["impedance"]["width_mm_by_layer"]
BASE_ENV = {"CO10_STEP": "1.449", "CO10_EDELTA": "-0.10", "CO10_WLO": "33.70", "CO10_WSTEP": "1.05",
            "CO10_FANY_J3": "34.5,51.5", "CO10_STUB": "J3L", "CO10_POLMODE": "lx",
            "CO10_EASTSPLIT": "in2c", "CO10_J2STEP": "0.58", "CO10_COLMODE": "pol",
            "CO10_WSWAP": "1-11", "CO10_HOLE_GAP": "0.4495", "CO10_LXPRIO": "landlen",
            "CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json"}
PAR_DEG = 10.0


def sha16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def run_probe(ip3w: str, pdn: str, order: str, out: Path) -> dict:
    env = dict(os.environ); env.update(BASE_ENV)
    env.update({"CO10_IP3W": ip3w, "CO10_PDN_OBS": pdn})
    for _k in ("PYTHONHOME", "PYTHONPATH"):        # 防宿主 AppDir python 环境泄漏到系统 python3 子进程
        env.pop(_k, None)
    pyp = os.environ.get("CO143_PY") or shutil.which("python3") or sys.executable
    r = subprocess.run([pyp, str(K2 / "tools/p3_v57_co10_west_fan_probe.py"),
                    "--rule", "fan", "--order", order, "--out", str(out)],
                   env=env, cwd=str(K2), capture_output=True, text=True)
    if not Path(out).exists():
        raise RuntimeError(f"probe run failed (ip3w={ip3w} pdn={pdn} order={order}): {r.stdout[-500:]}{r.stderr[-800:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def parallel_gaps(geom, layer):
    """同层、异页、平行(<=10°) 段对中心距最小值 + 违例数（3W 口径）。"""
    segs = []
    for pid, g in geom.items():
        for (lay, x1, y1, x2, y2, pa, pol) in g["segs"]:
            if lay == layer:
                segs.append((pid, x1, y1, x2, y2))
    worst, n_bad = None, 0
    th = 3.0 * WBY[layer]
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            a, b = segs[i], segs[j]
            if a[0] == b[0]:
                continue
            ax, ay = a[3] - a[1], a[4] - a[2]
            bx, by = b[3] - b[1], b[4] - b[2]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            if la < 1e-9 or lb < 1e-9:
                continue
            if abs(ax * by - ay * bx) / (la * lb) > math.sin(math.radians(PAR_DEG)):
                continue
            d = _seg_seg((a[1], a[2]), (a[3], a[4]), (b[1], b[2]), (b[3], b[4]))
            if worst is None or d < worst[0]:
                worst = (round(d, 4), a[0], b[0])
            if d < th - 1e-9:
                n_bad += 1
    return {"min_center_mm": worst[0] if worst else None, "min_pair": [worst[1], worst[2]] if worst else None,
            "n_below_3w": n_bad, "three_w_mm": round(th, 4)}


def _d_pt_seg(px, py, sx, sy, ex, ey):
    vx, vy, wx, wy = ex - sx, ey - sy, px - sx, py - sy
    L = vx * vx + vy * vy
    t = 0.0 if L == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L))
    return math.hypot(px - (sx + t * vx), py - (sy + t * vy))


def _seg_seg(a, b, c, d):
    return min(_d_pt_seg(c[0], c[1], a[0], a[1], b[0], b[1]), _d_pt_seg(d[0], d[1], a[0], a[1], b[0], b[1]),
               _d_pt_seg(a[0], a[1], c[0], c[1], d[0], d[1]), _d_pt_seg(b[0], b[1], c[0], c[1], d[0], d[1]))


def dp_feasible():
    """分带 DP：B.Cu 带内按 pad-x 升序，寻找满足 pad/PDN 合法性 + 单调 + 3W + VT 的列分配。"""
    import importlib.util, numpy as np  # noqa
    env = dict(os.environ); env.update(BASE_ENV)
    env.update({"CO10_IP3W": "1", "CO10_PDN_OBS": "1"})
    for k, v in env.items():
        os.environ[k] = v
    sp = importlib.util.spec_from_file_location("probe143", str(K2 / "tools/p3_v57_co10_west_fan_probe.py"))
    P = importlib.util.module_from_spec(sp); sp.loader.exec_module(P)
    pdn_vias, _ = P._pdn_obstacles()
    out = {}
    bands = {}
    for p, f in P.FACTS.items():
        if P.esc_layer(f) == "B.Cu":
            bands.setdefault((f["corridor"], f["band"]), []).append(p)
    for key, pids in sorted(bands.items()):
        pids = sorted(pids)
        cand = {}
        for p in pids:
            f = P.FACTS[p]
            rows = []
            for r in P.PAIR_DOMAIN[p]["pair_rows"]:
                px, nx, py, ny, dd = (float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]))
                if dd < P.VV - 1e-9 or abs(px - nx) < P.VT - 1e-9:
                    continue
                if abs(py - f["pad"]["P"][1]) > P.YWIN or abs(ny - f["pad"]["N"][1]) > P.YWIN:
                    continue
                ok = True
                for pol, vx, vy, ly in (("P", px, py, P.W.fp(P.LANES[p]["lane_y"] + P.pol_off(f, "P"))),
                                        ("N", nx, ny, P.W.fp(P.LANES[p]["lane_y"] + P.pol_off(f, "N")))):
                    if float(P.pad_via_edge(vx, vy).min()) < P.ESC - 1e-12 or \
                       float(P.pad_via_edge(vx, ly).min()) < P.ESC - 1e-12:
                        ok = False; break
                    for gx, gy in pdn_vias:
                        if math.hypot(vx - gx, vy - gy) < P.VV - 1e-12 or \
                           math.hypot(vx - gx, ly - gy) < P.VV - 1e-12:
                            ok = False; break
                    if not ok:
                        break
                if ok:
                    rows.append((px, nx))
            cand[p] = sorted(set(rows))
        th = 3.0 * WBY["B.Cu"]
        states = set()
        for k2, p in enumerate(pids):
            nxt = set()
            for r in cand[p]:
                if k2 == 0:
                    nxt.add(r); continue
                for (ppx, pnx) in states:
                    if r[0] - ppx >= th - 1e-9 and ppx < r[0] and pnx < r[1]:
                        nxt.add(r); break
            states = nxt
            if not states:
                break
        out[str(key)] = {"pages": len(pids), "legal_rows_total": sum(len(v) for v in cand.values()),
                         "dp_end_states": len(states), "feasible": bool(states)}
    return out


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="co143_"))
    alloc7 = json.loads(ALLOC7.read_text(encoding="utf-8"))["pages"]
    g0 = run_probe("0", "0", "rev", tmp / "c0.json")
    base_bcu = parallel_gaps(g0["geom"], "B.Cu")
    # A: 基线（= ALLOC.7 的扇几何）是否含 <3W 的对间平行
    A = {"baseline_placed": f"{g0['n_placed']}/{g0['n_pages']}", "bcu": base_bcu,
         "alloc7_match": all(abs(alloc7[p]["via1"][q][0] - g0["placed"][p][q + "_via"][0]) < 1e-6
                             and abs(alloc7[p]["via1"][q][1] - g0["placed"][p][q + "_via"][1]) < 1e-6
                             for p in alloc7 for q in ("P", "N")),
         "fan_check_3w_term": "ABSENT（check() track-track 判据 = TT=WID+CLEAR=0.38；无 3*w(layer) 项）"}
    # B/C
    gB = run_probe("1", "0", "rev", tmp / "cb.json")
    gC1 = run_probe("1", "1", "rev", tmp / "cc1.json")
    gC2 = run_probe("1", "1", "xasc", tmp / "cc2.json")
    B = {"placed": f"{gB['n_placed']}/{gB['n_pages']}", "bcu": parallel_gaps(gB["geom"], "B.Cu")}
    C = {"rev_pdn": {"placed": f"{gC1['n_placed']}/{gC1['n_pages']}", "failed": sorted(gC1["failed"]),
                     "bcu": parallel_gaps(gC1["geom"], "B.Cu")},
         "xasc_pdn": {"placed": f"{gC2['n_placed']}/{gC2['n_pages']}", "failed": sorted(gC2["failed"]),
                      "bcu": parallel_gaps(gC2["geom"], "B.Cu")},
         "failure_reasons": {p: list(v["reasons"]) for p, v in {**gC1["failed"], **gC2["failed"]}.items()}}
    D = dp_feasible()
    rec = {"artifact": "m13_v57_co143_escape_fan_3w_feasibility", "schema": 1, "revision": "CO-143",
           "nature": "L2 分析（只读）：逃生扇对间 3W 缺陷**定位修正** + 施加可行性研究",
           "corrects": {"prior_localization": "CO-141 附记2：f13 pair_xorder / p3_v57_f13_r1_pair_xorder.py",
                        "why_invalid": "co16 形状的 R1 逃生列 = co16_prepare() O(1) 消费 CO16-ALLOC.7；"
                                       "r1_place()/pair_xorder 在 co16 路径不执行 ⇒ 附记2 两次实验为 no-op",
                        "true_locus": "p3_v57_co10_west_fan_probe.py check()（逃生竖列落位判据）"
                                      " → CO16-ALLOC → G4(co16) → L4"},
           "inputs": {"spec": sha16(SPEC), "alloc7": sha16(ALLOC7),
                      "probe": sha16(K2 / "tools/p3_v57_co10_west_fan_probe.py")},
           "A_defect_present": A, "B_3w_only": B, "C_3w_plus_pdn": C, "D_dp_feasibility": D,
           "E_applied_experiment_reverted": {
               "what": "把 3W 并入 check（CO10_IP3W=1）并重生成 ALLOC.8 → G4 → L4 板 → co133 --apply",
               "drc_before_after": {"baseline": 42, "after": 45},
               "new_violations": "3× clearance：UP0/out_J2 N corner via × GND stitch via (83.575,56.516)，"
                                 "铜距 0.1587 < 0.175（= 中心距 0.5087 < VV 0.525）",
               "disposition": "**已还原**：ALLOC.8/v8_raw/板 全部回退到 rev-19 基线（板 a3ce9ab803045a0a；"
                              "G4 0074dad9067af737）；本实验工件不保留",
               "lesson": "3W 并入后扇列西移 0.30 ⇒ 撞上 PDN GND stitch via ⇒ 必须同时做 PDN 障碍感知"},
           "verdict": ("FEASIBLE_BUT_REQUIRES_FAN_REDERIVATION"
                       if D and all(v["feasible"] for v in D.values()) else "NEEDS_REVIEW"),
           "conclusion": "对间 3W 约束**可满足**（DP 机判两带均有合法单调解；单独并入 3W 亦 32/32）。"
                         "但**单遍贪心 + 按 pad 邻近选列**的策略在「3W + PDN 障碍」下无法 32/32，"
                         "且存在「差分仅 0.0025mm 而候选网格 0.05mm」的网格夹死 ⇒ 关闭本 TOOL_DEFECT "
                         "须**重派生扇落位策略**（闭式单调 carry / 分带次序 / PDN 障碍场），"
                         "属 L2 过孔策略-走廊重派生，非阈值参数追加。",
           "redline": "只读分析；不改板/SPEC/冻结四源；DP 仅为分析证据（生产器仍为单遍闭式）"}

    io = {"artifact": rec["artifact"], "schema": 1, "revision": "CO-143"}
    (STEP2 / "m13_v57_co143_escape_fan_3w_feasibility.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=False), encoding="utf-8")
    lines = ["# CO-143 — 逃生扇对间 3W：定位修正 + 施加可行性研究（L2 只读）", "",
             f"- verdict：**{rec['verdict']}**", "",
             "## 定位修正", f"- 旧（CO-141 附记2）：{rec['corrects']['prior_localization']}",
             f"- 不成立原因：{rec['corrects']['why_invalid']}", f"- 真实所在：{rec['corrects']['true_locus']}", "",
             "## 机判", "| 配置 | 落位 | B.Cu 对间最小中心距 | <3W 对数 |", "|---|---|---|---|",
             f"| A 基线 | {A['baseline_placed']} | {A['bcu']['min_center_mm']} | {A['bcu']['n_below_3w']} |",
             f"| B 仅并 3W | {B['placed']} | {B['bcu']['min_center_mm']} | {B['bcu']['n_below_3w']} |",
             f"| C rev+3W+PDN | {C['rev_pdn']['placed']} | {C['rev_pdn']['bcu']['min_center_mm']} | "
             f"{C['rev_pdn']['bcu']['n_below_3w']} |",
             f"| C xasc+3W+PDN | {C['xasc_pdn']['placed']} | {C['xasc_pdn']['bcu']['min_center_mm']} | "
             f"{C['xasc_pdn']['bcu']['n_below_3w']} |", "",
             f"- DP 分带可满足：{json.dumps(D, ensure_ascii=False)}", "",
             "## 施加实验（已还原）",
             f"- {rec['E_applied_experiment_reverted']['what']}",
             f"- DRC：{rec['E_applied_experiment_reverted']['drc_before_after']}；{rec['E_applied_experiment_reverted']['new_violations']}",
             f"- {rec['E_applied_experiment_reverted']['disposition']}", "",
             "## 结论", rec["conclusion"], ""]
    (STEP2 / "m13_v57_CO143_escape_fan_3w_feasibility.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "A_min": base_bcu["min_center_mm"],
                      "A_below3w": base_bcu["n_below_3w"], "B_min": B["bcu"]["min_center_mm"],
                      "B_below3w": B["bcu"]["n_below_3w"], "C_rev": C["rev_pdn"]["placed"],
                      "C_xasc": C["xasc_pdn"]["placed"], "C_failed": C["failure_reasons"],
                      "DP": D, "rec_sha16": sha16(REC), "card_sha16": sha16(CARD)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
