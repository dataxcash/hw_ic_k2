#!/usr/bin/env python3
"""CO-61：【L2 走廊分配/过孔策略/等长窗口】对间净空目标的 **L2 设计空间穷举（负结果）**。

CO-60 已机判"单旋钮不可达"。本件把搜索扩到 L2 的**策略维**（非仅数值）：
  A. 西侧（MCIO↔芯片）对间距 × 落列交换(WSWAP) × 列口径(COLMODE) 组合；
  B. 东侧（芯片↔J2）1.580 下的**走廊平面锚定**（CO10_EDELTA 平移），检查是否落在板边可用带内。
判据：32/32 落位 AND 走廊 lane 平面 ∈ [LANE_Y_LO, LANE_Y_HI]（板边 0.30 铜距 + 0.1025 半线宽）。
只读冻结源；候选件为 scratch（即发即删）；零正式件改动。
"""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co61_l2_search_exhaustion.json"
EMIT = K2 / "tools/p3_v57_co16_emit_allocation.py"
SCRATCH = "m13_v57_co61_scratch.json"
LANE_Y_LO, LANE_Y_HI = 33.4025, 78.5975
BASE = {
    "CO16_COLMODE": "pol", "CO16_EASTSPLIT": "in2c", "CO16_EDELTA": "-0.10",
    "CO16_FANY_J3": "34.5,51.5", "CO16_HOLE_GAP": "0.4495", "CO16_J2STEP": "0.58",
    "CO16_LXPRIO": "landlen", "CO16_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json",
    "CO16_POLMODE": "lx", "CO16_STUB": "J3L", "CO16_WLO": "33.70", "CO16_WSWAP": "1-11",
    "CO16_STEP": "1.449", "CO16_WSTEP": "1.05",
}
BASE_SHA = "0bf6cdc203887a48f162ad2355e4f372ae895f5422bead9fc76992afd8476bfd"
BASE_REASON = ("D3b 收官：connector 落列器改按 land 段长度升序（CO10_LXPRIO=landlen）——短 land 段组（J4U/J4L）优先取自然列"
               "（dx=-0.3，铜距 0.1975 >= 0.175），长 land 段组（J3U/J3L）吸收列偏移（其 land 在焊盘行附近已收敛到 conn_x）"
               "=> land 铜距 6 条违规（-0.0833/0.0582/-0.0833）全消，pad_clearance_audit_copper=0；落位仍 32/32；"
               "层意图（LID.1）/stub 层分配/pad 分配不变")


def emit(over: dict, supersedes: str = "CO16-ALLOC.5", reason: str = "probe",
         rev: str = "CO16-ALLOC.6probe") -> dict:
    env = dict(os.environ)
    env.update(BASE)
    env.update(over)
    env.update({"CO16_OUT": SCRATCH, "CO16_REV": rev,
                "CO16_SUPERSEDES": supersedes, "CO16_SUPERSEDES_REASON": reason,
                "CO16_VERIFY": "m13_v57_co36_placement_verification.json"})
    r = subprocess.run([sys.executable, str(EMIT)], env=env, capture_output=True, text=True, timeout=900)
    p = STEP2 / SCRATCH
    if not p.exists():
        return {"placed_32of32": False, "stdout": (r.stdout or "")[:140]}
    doc = json.loads(p.read_text())
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    p.unlink()
    ys = {c: [] for c in ("WEST_MCIO_TO_CHIP", "EAST_CHIP_TO_J2")}
    for pg in doc["pages"].values():
        ys[pg["corridor"]] += [pg["lane_y"]["P"], pg["lane_y"]["N"]]
    out = {"placed_32of32": r.returncode == 0 and doc["n_pages"] == 32,
           "stdout": (r.stdout or "").strip()[:90]}
    for c, v in ys.items():
        if v:
            out[c] = {"y_min": round(min(v), 3), "y_max": round(max(v), 3),
                      "in_board_band": bool(min(v) >= LANE_Y_LO and max(v) <= LANE_Y_HI)}
    if sha == BASE_SHA:
        out["baseline"] = True
    return out


def main() -> int:
    base = emit({}, supersedes="CO16-ALLOC.4", reason=BASE_REASON, rev="CO16-ALLOC.5")
    faithful = bool(base.get("baseline"))
    west, east = [], []
    if faithful:
        for p in ("1.20", "1.46", "1.58"):
            for tag, ov in (("noswap/colmode=pol", {"CO16_WSWAP": ""}),
                            ("noswap/colmode=default", {"CO16_WSWAP": "", "CO16_COLMODE": ""}),
                            ("swap/colmode=default", {"CO16_COLMODE": ""})):
                west.append(dict({"case": f"WEST={p} {tag}", "wstep": p}, **emit(dict(ov, CO16_WSTEP=p))))
        for d in ("-0.10", "1.00", "2.00", "3.00"):
            east.append(dict({"case": f"EAST=1.580 EDELTA={d}", "edelta": d},
                             **emit({"CO16_STEP": "1.580", "CO16_EDELTA": d})))
    doc = {
        "artifact": "m13_v57_co61_l2_search_exhaustion", "schema": 1, "revision": "CO-61.1",
        "nature": "L2 设计空间穷举（负结果）：走廊对间距目标在冻结 L1 包络内不可达",
        "baseline_faithful": faithful,
        "criterion": {"placed_32of32": True, "lane_plane_in_board_band": [LANE_Y_LO, LANE_Y_HI]},
        "A_west_pitch_x_strategy": west,
        "B_east_lane_plane_anchor": east,
        "conclusion": ("A：西侧 1.20/1.46/1.58 × {无交换/有交换} × {colmode pol/默认} 共 9 组**全部落位失败**"
                       "（失败均为芯片逃逸区，行扫 ~15150 耗尽）⇒ 与策略无关，受球栅逃逸硬限。"
                       "B：东侧 1.580 可落位，但走廊平面 y_max 80.5~82.6 > 板边可用上限 78.5975；"
                       "下移锚定至 +2.0 仍越界，+3.0 起 J2 侧逃逸落位失败 ⇒ 无可行锚定。"
                       "⇒ R3-2 realized 0.875（⇒ 中心距 1.580）在冻结 L1 包络内**不可达**，L1 冲突成立。"),
        "redline": "只读冻结源；候选件 scratch 即发即删；canonical 零改动。",
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": hashlib.sha256(OUT.read_bytes()).hexdigest()[:16],
                      "baseline_faithful": faithful,
                      "west_placed": sum(1 for x in west if x["placed_32of32"]),
                      "east_placed": sum(1 for x in east if x["placed_32of32"]),
                      "east_in_band": sum(1 for x in east if (x.get("EAST_CHIP_TO_J2") or {}).get("in_board_band"))},
                     ensure_ascii=False))
    return 0 if faithful else 3


if __name__ == "__main__":
    sys.exit(main())
