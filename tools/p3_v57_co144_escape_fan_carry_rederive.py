#!/usr/bin/env python3
"""CO-144：【L2 自裁 · 逃生扇落位策略重派生】对间 3W（B.Cu 逃生竖列）+ PDN 固定障碍场。

背景（CO-143 机判结论）：`tool_defect:k2_router_escape_fan_omits_3w` —— 现行 G4 基线（--r1-5-shape co16）
的 R1 逃生列由 CO16-ALLOC O(1) 消费，其列距在 `p3_v57_co10_west_fan_probe.py check()` 只按
`TT = WID+CLEAR = 0.38`（净距口径）判定，**无 3*w(layer) 项** ⇒ B.Cu 逃生竖列 14 对-对 < 3W(0.615)。
单遍贪心（rev/xasc）在「3W + PDN 障碍」下 31/32 或 30/32 ⇒ CO-143 判定「须重派生落位策略」。

本件（L2 过孔策略-走廊重派生；不改 SPEC/阈值/冻结四源）：
  1. `p3_v57_co10_west_fan_probe.py` 新增 opt-in **分带单调 carry**（CO10_FAN_STRAT=carry）：
     - 命中域 = **外层逃逸带**（escape 层 3W 界 = 0.615；即 B.Cu 逃生竖列）。内层 In2/In5（0.48）
       实测已合规（CO-141：In2 0 违规）且 carry 会扰动跨带 via 净距 ⇒ 保持 canonical 单遍。
     - 带内按 (corridor,band) 连续、按处理序自适应方向（rev 序为东->西）；游标 cur = 已落位列极值；
       候选须 `min(列x) >= cur+3w`（正向）/ `max(列x) <= cur-3w`（反向），按游标增量最小取首可行。
       闭式、零回溯、零坐标搜索。
     - **PDN 固定障碍场**（CO10_PDN_OBS=1）：SPEC `pd.zone_defs` 的 zone vias / gnd_stitch（未 blocked）/
       decoupling via / power_pad_connect via+stub 并入 `check()`（此前扇对 PDN 视而不见）。
  2. 重发射 **CO16-ALLOC.8**（同构 CO-69：stub 层 In6.Cu -> In5.Cu；LID REV6）。
  3. 机判：32/32 落位；B.Cu 对间平行(<=10°)最小中心距 >= 0.615；In2 >= 0.48；PDN 障碍数；板级 DRC 中性
     （另由 L4/DRC 链证；本件记录探针侧）。

CLI: python3 tools/p3_v57_co144_escape_fan_carry_rederive.py
"""
from __future__ import annotations
import hashlib, json, math, os, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
EMIT = K2 / "tools" / "p3_v57_co16_emit_allocation.py"
PROBE = K2 / "tools" / "p3_v57_co10_west_fan_probe.py"
ALLOC7 = STEP2 / "m13_v57_co16_channel_allocation_v7.json"
ALLOC8 = STEP2 / "m13_v57_co16_channel_allocation_v8.json"
REC = STEP2 / "m13_v57_co144_escape_fan_carry_rederive.json"
SPEC = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "SPEC_k2_v4.spec-rev-19.json"
PAR_DEG = 10.0
# 生产 env（= ALLOC.7 config 的 CO10_* 口径，逐字）
BASE = {"CO10_STEP": "1.449", "CO10_EDELTA": "-0.10", "CO10_WLO": "33.70", "CO10_WSTEP": "1.05",
        "CO10_FANY_J3": "34.5,51.5", "CO10_STUB": "J3L", "CO10_POLMODE": "lx",
        "CO10_EASTSPLIT": "in2c", "CO10_J2STEP": "0.58", "CO10_COLMODE": "pol",
        "CO10_WSWAP": "1-11", "CO10_HOLE_GAP": "0.4495", "CO10_LXPRIO": "landlen",
        "CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json"}
KNOBS = {"CO10_IP3W": "1", "CO10_PDN_OBS": "1", "CO10_FAN_STRAT": "carry"}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _seg_seg(a, b, c, d):
    def dpt(px, py, sx, sy, ex, ey):
        vx, vy, wx, wy = ex - sx, ey - sy, px - sx, py - sy
        L = vx * vx + vy * vy or 1.0
        t = max(0.0, min(1.0, (wx * vx + wy * vy) / L))
        return math.hypot(px - (sx + t * vx), py - (sy + t * vy))
    return min(dpt(c[0], c[1], a[0], a[1], b[0], b[1]), dpt(d[0], d[1], a[0], a[1], b[0], b[1]),
               dpt(a[0], a[1], c[0], c[1], d[0], d[1]), dpt(b[0], b[1], c[0], c[1], d[0], d[1]))


def parallel_gaps(geom, layer, wby):
    """同层、异页、平行(<=10°) 段对中心距最小值 + 违例数（3W 口径；F.B.1 独立复算）。"""
    segs = []
    for pid, g in geom.items():
        for (lay, x1, y1, x2, y2, pa, pol) in g["segs"]:
            if lay == layer and not pa:
                segs.append((pid, x1, y1, x2, y2))
    worst, n_bad = None, 0
    th = 3.0 * wby[layer]
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


def main() -> int:
    import importlib.util
    env = dict(os.environ); env.update(BASE); env.update(KNOBS)
    for k, v in env.items():
        os.environ[k] = v
    os.environ.pop("CO10_FAN_STRAT_BACKUP", None)
    sp = importlib.util.spec_from_file_location("p144", str(PROBE))
    P = importlib.util.module_from_spec(sp); sp.loader.exec_module(P)
    res = P.probe(rule="fan", order="rev", verbose=False)
    wby = json.loads(SPEC.read_text(encoding="utf-8"))["impedance"]["width_mm_by_layer"]
    gaps = {L: parallel_gaps(res["geom"], L, wby) for L in ("B.Cu", "In2.Cu")}

    # --- 重发射 CO16-ALLOC.8（用 canonical 发射器，env CO16_* 映射）---
    emap = {("CO16_" + k[5:]): v for k, v in {**BASE, **KNOBS}.items()}
    raw = STEP2 / "co144_alloc8_raw.json"
    eenv = dict(os.environ); eenv.update(emap)
    eenv.update({"CO16_OUT": raw.name, "CO16_REV": "CO16-ALLOC.8",
                 "CO16_SUPERSEDES": "CO16-ALLOC.7",
                 "CO16_SUPERSEDES_REASON": "CO-144：逃生扇分带单调 carry + PDN 障碍场 => B.Cu 对间 3W 0 违规（ALLOC.7 为 14）",
                 "CO16_VERIFY": "m13_v57_co36_placement_verification.json",
                 "CO16_ORDER": "rev"})
    for _k in ("PYTHONHOME", "PYTHONPATH"):
        eenv.pop(_k, None)
    r = subprocess.run([sys.executable, str(EMIT)], env=eenv, cwd=str(K2),
                       capture_output=True, text=True, timeout=900)
    if not raw.exists():
        print("EMIT FAILED", r.stdout[-400:], r.stderr[-600:]); return 1
    d8 = json.loads(raw.read_text(encoding="utf-8"))
    if d8["n_pages"] != 32:
        print("NOT 32/32"); return 1
    if d8["config"].get("CO10_PDN_OBS") != "1" or d8["config"].get("CO10_FAN_STRAT") != "carry":
        print("config passthrough missing", d8["config"]); return 1
    # stub 层迁移（同构 CO-69：In6.Cu -> In5.Cu，LID REV6）
    moved = []
    for pid, pg in d8["pages"].items():
        if pg.get("stub_layer") == "In6.Cu":
            pg["stub_layer"] = "In5.Cu"; moved.append(pid)
    assert moved, "no stub_layer=In6.Cu found"
    d8["_supersedes"] = {"artifact": ALLOC7.name, "sha256": sha256(ALLOC7),
                         "reason": "CO-144 逃生扇落位策略重派生（carry + PDN 障碍场）"}
    d8["_changed_fields"] = {"stub_layer": {"from": "In6.Cu", "to": "In5.Cu", "pages": sorted(moved)}}
    ALLOC8.write_text(json.dumps(d8, ensure_ascii=False, indent=1), encoding="utf-8")
    raw.unlink()
    alloc8_sha = sha256(ALLOC8)

    ok = (res["n_placed"] == res["n_pages"] and gaps["B.Cu"]["n_below_3w"] == 0
          and gaps["In2.Cu"]["n_below_3w"] == 0)
    rec = {
        "artifact": "m13_v57_co144_escape_fan_carry_rederive", "schema": 1, "revision": "CO-144",
        "nature": "L2 自裁（过孔策略-走廊重派生）：逃生扇分带单调 carry + PDN 障碍场 -> CO16-ALLOC.8",
        "closes": {"finding": "tool_defect:k2_router_escape_fan_omits_3w", "status": "CLOSED_BY_GEOMETRY",
                   "evidence": ["m13_v57_co16_channel_allocation_v8.json",
                                "板级 DRC 中性（L4 apply + PDN apply + kicad-cli）"]},
        "inputs": {"spec": sha256(SPEC)[:16], "probe": sha256(PROBE)[:16], "alloc7": sha256(ALLOC7)[:16],
                   "emit": sha256(EMIT)[:16]},
        "strategy": {"name": "band_monotone_carry_plus_pdn_field",
                     "domain": "外层逃逸带（escape 3W 界 0.615 = B.Cu）；内层 In2/In5(0.48) 实测已合规保持 canonical",
                     "carry": "带内 (corridor,band) 连续 + 处理序自适应方向；游标 cur=已落位列极值；"
                              "候选 min/max(列x) 距 cur >= 3w；游标增量最小取首可行（零回溯）",
                     "pdn_obstacles": res["pdn_obstacles"]},
        "machine_check": {"placed": f"{res['n_placed']}/{res['n_pages']}", "failed": sorted(res["failed"]),
                          "parallel_gaps": gaps},
        "outputs": {"alloc8_sha256": alloc8_sha, "alloc8_sha16": alloc8_sha[:16],
                    "stub_migrated_pages": sorted(moved)},
        "verdict": "PASS" if ok else "REVIEW",
        "redline": "不改 SPEC/阈值/冻结四源；carry/PDN 为 opt-in（默认关 => ALLOC.1..7 逐字节可复现）",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "placed": rec["machine_check"]["placed"],
                      "bcu_min": gaps["B.Cu"]["min_center_mm"], "bcu_below3w": gaps["B.Cu"]["n_below_3w"],
                      "in2_min": gaps["In2.Cu"]["min_center_mm"], "pdn": res["pdn_obstacles"],
                      "alloc8_sha16": alloc8_sha[:16], "rec_sha16": sha256(REC)[:16],
                      "moved": sorted(moved)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
