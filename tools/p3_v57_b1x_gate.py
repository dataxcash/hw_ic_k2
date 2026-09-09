#!/usr/bin/env python3
"""P3 v57 BIG — B1.2/B1.3/B1.4 门（lane 帧核心的序无关/构造即合法/单向）。

B1.2 序无关：同 frame 的 bands 以三枚举序（正/倒/密度）喂 build()，输出字节一致。
B1.3 构造即合法（独立判据，不复用核内部数学）：
  I1 全部 lane ∈ [span_lo+margin, span_hi-margin]；
  I2 任意两数据 lane |Δy| ≥ pitch−ε（构造出的帧天然满足）；
  I3 REFCLK(In2) 落点与全部数据 lane ≥ pitch；
  I4 不可行帧必有量化证书且 short_mm>0（needed/avail 自洽）。
B1.4 单向：三源文件零文件读/零引擎模块 import（纯函数白名单）。
任一 FAIL → exit 1（L7）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3_v57_big_lane_kernel as kernel  # noqa: E402

OUT = (Path(__file__).resolve().parents[1] / "pm_gate" / "artifacts" / "k2_v4" /
       "L3" / "mcio_feas_step2" / "m13_v57_b1x_report.json")
TOOLS = Path(__file__).resolve().parent
SRC = ["p3_v57_big_lane_kernel.py", "p3_v57_big_exhaustive_ref.py",
       "p3_v57_b1_gate.py"]
EPS = 1e-6


def _orders(bands):
    asc = list(bands)
    desc = list(reversed(bands))
    dens = sorted(bands, key=lambda b: (-b["n"], b["id"]))
    return asc, desc, dens


def main() -> int:
    import random
    rng = random.Random(20260909)
    viol = []
    n_ok_b12 = 0
    for _ in range(60):
        two = rng.random() < 0.6
        n1 = rng.randint(1, 2)
        n2 = rng.randint(1, 2) if two else 0
        base = 0.5 + (n1 - 1) * 1.5 + (1.5 if two else 0) + \
            (n2 - 1) * 1.5 + 0.5
        if two and rng.random() < 0.5:
            base += 1.5
        span = base + rng.choice([-1.0, -0.3, 0.0, 0.3, 1.2])
        bands = ([{"id": "up", "n": n1, "edge": "lo"}] if n1 else []) + \
                ([{"id": "dn", "n": n2, "edge": "hi"}] if n2 else [])
        ref = None if (not two and rng.random() < 0.7) else (
            None if rng.random() < 0.4 else
            {"n_pairs": 1, "layer": "In2.Cu" if (two or rng.random() < 0.3)
             else "F.Cu"})
        if ref and ref["layer"] == "In2.Cu" and not two:
            ref = {"n_pairs": 1, "layer": "F.Cu"}
        frame = {"span": [40.0, 40.0 + max(span, 1.2)], "margin": 0.5,
                 "pitch": 1.5, "bands": bands, "refclk": ref}
        outs = []
        for ob in _orders(bands):
            fr2 = dict(frame)
            fr2["bands"] = ob
            outs.append(json.dumps(kernel.build(fr2), sort_keys=True))
        if len(set(outs)) == 1:
            n_ok_b12 += 1
        else:
            viol.append({"B": "B1.2_order_dependence", "frame": frame,
                         "outs": outs})
        out = kernel.build(frame)
        if not out["feasible"]:
            c = out["certificate"]
            if not c or not (c.get("short_mm") or 0) > 0:
                viol.append({"B": "B1.3_I4_cert", "frame": frame, "cert": c})
            continue
        m = frame["margin"]
        lo, hi = frame["span"]
        for l in out["lanes"]:
            if not (lo + m - 1e-9 <= l["y"] <= hi - m + 1e-9):
                viol.append({"B": "B1.3_I1_bounds", "frame": frame,
                             "lane": l})
        ys = [l["y"] for l in out["lanes"]]
        for a in range(len(ys)):
            for b in range(a + 1, len(ys)):
                if abs(ys[a] - ys[b]) + EPS < 1.5:
                    viol.append({"B": "B1.3_I2_pitch", "frame": frame,
                                 "ys": [ys[a], ys[b]]})
        if out.get("refclk") and out["refclk"].get("layer") == "In2.Cu":
            ry = out["refclk"]["y"]
            for y in ys:
                if abs(ry - y) + EPS < 1.5:
                    viol.append({"B": "B1.3_I3_refclk_iso",
                                 "frame": frame, "ry": ry, "lane_y": y})
    b14 = []
    for fn in SRC:
        txt = (TOOLS / fn).read_text(encoding="utf-8")
        if re.search(r"open\(|read_text\(|import hs_route_model|"
                     r"import solve_pipeline|import channel_alloc|"
                     r"import escape_landing|k2_v4\.kicad_pcb", txt):
            b14.append(fn)
    report = {"artifact": "m13_v57_b1x_report",
              "predicate": "B1.2 序无关 / B1.3 构造即合法 / B1.4 单向",
              "b12_frames_ok": n_ok_b12, "b13_violations": len(viol),
              "b14_files_violating": b14, "violations": viol,
              "verdict": "PASS" if (n_ok_b12 == 60 and not viol and not b14)
              else "FAIL"}
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    print(json.dumps({"b12_ok": n_ok_b12, "b13_viol": len(viol),
                      "b14_viol": len(b14), "verdict": report["verdict"]},
                     indent=1, ensure_ascii=False))
    print("artifact:", OUT)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
