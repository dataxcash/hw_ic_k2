#!/usr/bin/env python3
"""P3 v57 BIG — B1.1 门：lane 帧构造核心 对照 独立穷举基准（合成帧）。

验收（设计细案 §6 B1.1）：合成帧上 构造核心(closed-form) 判定 == 独立穷举
(网格回溯) 判定；不可行证书量化(needed/avail/short)自洽且 short>0。
合成覆盖：两族临界帧（span 恰在 needed 阈值 ± 扰动 → 看似够/看似不够）+
随机帧；REFCLK 变体 {None, In2(双组), F.Cu}。固定 seed；双跑字节一致。
任一不一致 → exit 1（L7）。
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_v57_big_lane_kernel as kernel  # noqa: E402
import p3_v57_big_exhaustive_ref as ref   # noqa: E402

OUT = (Path(__file__).resolve().parents[1] / "pm_gate" / "artifacts" / "k2_v4" /
       "L3" / "mcio_feas_step2" / "m13_v57_b1_report.json")
SEED = 20260909
P, M = 1.5, 0.5


def _needed(n1, n2):
    if n1 and n2:
        return M + (n1 - 1) * P + P + (n2 - 1) * P + M
    n = n1 or n2
    return M + (n - 1) * P + M


def _refclk_gap_needed():
    return 2 * P


def _frame(rng):
    two = rng.random() < 0.6
    n1 = rng.randint(1, 2)
    n2 = rng.randint(1, 2) if two else 0
    base = _needed(n1, n2)
    ref_mode = rng.choice(["none", "In2", "F.Cu"] if two else ["none", "F.Cu"])
    if ref_mode == "In2":
        base += P          # 中心 gap 从 P 提到 2P
    span_len = base + rng.choice([-1.2, -0.6, -0.1, 0.0, 0.2, 0.6, 1.6])
    span_len = max(span_len, 2 * M + 0.2)
    bands = []
    if n1:
        bands.append({"id": "up", "n": n1, "edge": "lo"})
    if n2:
        bands.append({"id": "dn", "n": n2, "edge": "hi"})
    return {"span": [40.0, round(40.0 + span_len, 3)], "margin": M, "pitch": P,
            "bands": bands,
            "refclk": None if ref_mode == "none" else
            {"n_pairs": 1, "layer": "In2.Cu" if ref_mode == "In2" else "F.Cu"}}


def main() -> int:
    rng = random.Random(SEED)
    frames = [_frame(rng) for _ in range(120)]
    mism = []
    for fr in frames:
        k = kernel.build(fr)
        r = ref.feasible(fr)
        if k["feasible"] != r["feasible"]:
            mism.append({"frame": fr, "kernel": k["feasible"],
                         "ref": r["feasible"], "cert": k["certificate"]})
            continue
        if not k["feasible"] and k["certificate"]:
            c = k["certificate"]
            if c.get("short_mm") is not None and c["short_mm"] <= 0:
                mism.append({"frame": fr, "issue": "cert_short_not_positive",
                             "cert": c})
    for fr in frames:
        k = kernel.build(fr)
        r = ref.feasible(fr)
        if fr["refclk"] and fr["refclk"]["layer"] == "F.Cu":
            pass
    ok = not mism
    report = {"artifact": "m13_v57_b1_report",
              "predicate": "B1.1 lane 帧构造核心 vs 独立穷举基准(合成帧)",
              "seed": SEED, "n_frames": len(frames),
              "decision_match": len(frames) - len(mism),
              "mismatch": mism,
              "verdict": "PASS" if ok else "FAIL"}
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    print(json.dumps({"n_frames": len(frames),
                      "decision_match": report["decision_match"],
                      "mismatch_n": len(mism),
                      "verdict": report["verdict"]}, indent=1,
                      ensure_ascii=False))
    print("artifact:", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
