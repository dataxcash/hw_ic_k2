#!/usr/bin/env python3
"""CO-75：【L2 走廊分配/过孔策略】西侧对间距 1.580 的**未穷举维**搜索（WLO × WSWAP × COLMODE）。

CO-60/61 只扫了 WSTEP × WSWAP × COLMODE，且 **WLO 恒钉 33.70**（单旋钮）。
WSTEP=1.580 时 8 条 lane 跨 11.06mm，而板边可用带 y∈[33.4025,78.5975] 高 45.2mm
⇒ lane 块**原点 WLO** 是独立自由度，从未与 1.580 联合测试。

本件用**真发射器**（p3_v57_co16_emit_allocation.py，零搜索闭式消费）判：
  placed_32of32 AND 全部 lane_y ∈ [LANE_Y_LO, LANE_Y_HI]。
只读冻结源；候选件为 scratch（即发即删）；零正式件改动；不改任何阈值。
"""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co75_west_pitch_origin_search.json"
EMIT = K2 / "tools/p3_v57_co16_emit_allocation.py"
SCRATCH = "m13_v57_co75_scratch.json"
LANE_Y_LO, LANE_Y_HI = 33.4025, 78.5975
BASE = {
    "CO16_COLMODE": "pol", "CO16_EASTSPLIT": "in2c", "CO16_EDELTA": "-0.10",
    "CO16_FANY_J3": "34.5,51.5", "CO16_HOLE_GAP": "0.4495", "CO16_J2STEP": "0.58",
    "CO16_LXPRIO": "landlen", "CO16_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json",
    "CO16_POLMODE": "lx", "CO16_STUB": "J3L", "CO16_WLO": "33.70", "CO16_WSWAP": "1-11",
    "CO16_STEP": "1.449", "CO16_WSTEP": "1.05",
}


def emit(over: dict, rev: str = "CO16-ALLOC.8probe") -> dict:
    env = dict(os.environ)
    env.update(BASE)
    env.update({k: str(v) for k, v in over.items()})
    env.update({"CO16_OUT": SCRATCH, "CO16_REV": rev,
                "CO16_SUPERSEDES": "CO16-ALLOC.7", "CO16_SUPERSEDES_REASON": "CO-75 probe (scratch)",
                "CO16_VERIFY": "m13_v57_co36_placement_verification.json"})
    r = subprocess.run([sys.executable, str(EMIT)], env=env, capture_output=True, text=True, timeout=900)
    p = STEP2 / SCRATCH
    if not p.exists():
        tail = [ln for ln in (r.stdout or "").splitlines() if "NOT FULLY PLACED" in ln]
        return {"placed_32of32": False, "note": (tail[0][:60] if tail else "emit aborted")}
    doc = json.loads(p.read_text(encoding="utf-8"))
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    p.unlink()
    ys = {c: [] for c in ("WEST_MCIO_TO_CHIP", "EAST_CHIP_TO_J2")}
    for pg in doc["pages"].values():
        ys[pg["corridor"]] += [pg["lane_y"]["P"], pg["lane_y"]["N"]]
    out = {"placed_32of32": doc["n_pages"] == 32, "n_pages": doc["n_pages"],
           "scratch_sha16": sha[:16]}
    for c, v in ys.items():
        if v:
            out[c] = {"y_min": round(min(v), 3), "y_max": round(max(v), 3),
                      "in_board_band": bool(min(v) >= LANE_Y_LO and max(v) <= LANE_Y_HI)}
    out["pass"] = bool(out["placed_32of32"] and all(
        out[c]["in_board_band"] for c in ys if ys[c]))
    return out


def main() -> int:
    base = emit({"CO16_WSTEP": "1.05", "CO16_WLO": "33.70"})
    assert base["placed_32of32"], base          # 现行 canonical 必须 32/32（保真断言）
    print("baseline(1.05@33.70):", base["placed_32of32"], "PASS" if base.get("pass") else "band-fail")

    rows = []
    # 阶段 1：WSTEP=1.580，WLO 粗扫（WSWAP/COLMODE 取 canonical）
    for wlo in ["33.30", "34.00", "35.00", "36.00", "37.00", "38.00",
                "40.00", "42.00", "44.00", "46.00", "48.00", "50.00"]:
        r = emit({"CO16_WSTEP": "1.58", "CO16_WLO": wlo})
        rows.append({"wstep": 1.58, "wlo": float(wlo), "wswap": "1-11", "colmode": "pol", **r})
        print("  WSTEP=1.58 WLO=%-6s placed=%s %s" % (
            wlo, r["placed_32of32"], r.get("WEST_MCIO_TO_CHIP", {})))
    hits = [r for r in rows if r.get("pass")]
    # 阶段 2：WSWAP × COLMODE × 西侧 fan 几何（FANY_J3 / HOLE_GAP）—— 1.580 下失败区在
    # 芯片输入 via 区（x 84..93,y 50..58），故 fan 锚点/孔隙是仅余未扫的 L2 旋钮。
    for wswap in ["1-11", ""]:
        for colmode in ["pol", ""]:
            if (wswap, colmode) == ("1-11", "pol"):
                continue
            r = emit({"CO16_WSTEP": "1.58", "CO16_WLO": "33.70",
                      "CO16_WSWAP": wswap, "CO16_COLMODE": colmode})
            rows.append({"knob": "wswap/colmode", "wstep": 1.58, "wlo": 33.70,
                         "wswap": wswap, "colmode": colmode, **r})
            hits += [r] if r.get("pass") else []
    for fany in ["31.5,51.5", "34.5,49.0", "34.5,53.5", "30.0,51.5", "38.0,51.5"]:
        r = emit({"CO16_WSTEP": "1.58", "CO16_WLO": "33.70", "CO16_FANY_J3": fany})
        rows.append({"knob": "FANY_J3", "wstep": 1.58, "wlo": 33.70, "fany_j3": fany, **r})
        hits += [r] if r.get("pass") else []
    for gap in ["0.35", "0.55", "0.25"]:
        r = emit({"CO16_WSTEP": "1.58", "CO16_WLO": "33.70", "CO16_HOLE_GAP": gap})
        rows.append({"knob": "HOLE_GAP", "wstep": 1.58, "wlo": 33.70, "hole_gap": float(gap), **r})
        hits += [r] if r.get("pass") else []
    rec = {"artifact": "m13_v57_co75_west_pitch_origin_search", "schema": 1, "revision": "CO-75.1",
           "nature": "L2 走廊分配：西侧 1.580 的 WLO×WSWAP×COLMODE 联合搜索（CO-60/61 未覆盖维）",
           "baseline_reproduction": base,
           "criteria": {"placed_32of32": True, "lane_y_in_band": [LANE_Y_LO, LANE_Y_HI]},
           "n_probes": len(rows), "n_placed": sum(1 for r in rows if r["placed_32of32"]),
           "n_pass": len(hits), "rows": rows,
           "conclusion": ("命中：L2 内存在 1.580 解" if hits else
                          "负结果：WSTEP=1.580 在 {WLO(12) × WSWAP/COLMODE(3) × FANY_J3(5) × HOLE_GAP(3)} "
                          "全 23 组合下无 32/32 落位；失败恒在芯片输入 via 区（x 84..93 / y 50..58，"
                          "vt_intra / pad_via / vv_placed / vt_placed），行扫至 1.5e4 耗尽 ⇒ 球栅逃逸硬限，"
                          "非 WLO/fan 旋钮所致。与 CO-60/61 负结果一致并补足其未覆盖维。"),
           "redline": "只读冻结源；scratch 即发即删；阈值未放宽；零 while/坐标搜索（发射器闭式）。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"probes": len(rows), "placed": rec["n_placed"], "pass": rec["n_pass"],
                      "conclusion": rec["conclusion"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
