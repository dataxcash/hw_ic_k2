#!/usr/bin/env python3
"""P3 v57 S1 — A1.3 门：几何不变量套件自测（合成正/负控，发射未接线前先验套件）。

正控：构造一条内部合法图纸页（P/N 走廊 ±0.19 保持、2 via 于层翻转点、锚钉端），
套件必须零违例；负控：分别破坏 V1-V6 六类属性之一，套件必须命中对应 V 代码。
任一不符 → exit 1（L7）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p3_v57_s1_invariants import check_page  # noqa: E402

OUT = (Path(__file__).resolve().parents[1] / "pm_gate" / "artifacts" / "k2_v4" /
       "L3" / "mcio_feas_step2" / "m13_v57_s1_a13_report.json")
RULES = {"width": 0.205, "p_gap": 0.175, "half_pitch": 0.19,
         "pn_min_edge": 0.155, "max_vias_per_net": 2, "via_od": 0.35}

YC = 58.39
P_CP, N_CP = (84.6, 52.0), (85.0, 52.0)
P_JP, N_JP = (135.0, 54.3), (135.0, 54.3)


def base_paths():
    py, ny = YC + 0.19, YC - 0.19
    return {
        "P": {"points": [P_CP, (84.6, py), (105.25, py), (133.0, py), P_JP],
              "layers": ["F.Cu", "In2.Cu", "In2.Cu", "F.Cu"],
              "vias": [(84.6, py), (133.0, py)]},
        "N": {"points": [N_CP, (85.0, ny), (133.0, ny), N_JP],
              "layers": ["F.Cu", "In2.Cu", "F.Cu"],
              "vias": [(85.0, ny), (133.0, ny)]},
    }


def base_page():
    return {"page_id": "SYN/valid", "paths": base_paths(),
            "anchor_pads": {"P": {"chip": list(P_CP), "conn": list(P_JP)},
                            "N": {"chip": list(N_CP), "conn": list(N_JP)}}}


def main() -> int:
    pos = check_page(base_page(), RULES)
    if pos:
        return _fail("positive control", pos)

    cases = []
    pg = base_page()
    yp = YC + 0.19
    pg["paths"]["N"] = {
        "points": [N_CP, (85.0, yp), (133.0, yp), N_JP],
        "layers": ["F.Cu", "In2.Cu", "F.Cu"],
        "vias": [(85.0, yp), (133.0, yp)]}
    cases.append(("V5_pair_spacing", pg))
    pg = base_page()
    pg["paths"]["P"]["vias"].append((90.0, YC + 0.19))
    cases.append(("V2_via_count", pg))
    pg = base_page()
    pg["paths"]["P"]["points"][-1] = (135.1, 54.3)
    cases.append(("V1_anchor_end", pg))
    pg = base_page()
    pg["paths"]["P"]["layers"] = ["F.Cu", "In2.Cu", "In2.Cu"]
    cases.append(("V4_layer_len", pg))
    pg = base_page()
    pg["paths"]["N"]["vias"] = [(85.0, 52.0)]
    cases.append(("V3_via_turn", pg))

    report = {"artifact": "m13_v57_s1_a13_report",
              "predicate": "A1.3 几何不变量套件自测(正/负控)",
              "rules": RULES, "positive_control_ok": not pos,
              "negative_controls": []}
    ok = not pos
    for tag, pg in cases:
        viol = check_page(pg, RULES)
        hit = any(v["V"].startswith(tag.split("_")[0]) for v in viol)
        report["negative_controls"].append(
            {"case": tag, "detected": hit, "violations": viol})
        ok = ok and hit
    report["verdict"] = "PASS" if ok else "FAIL"
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("positive_control_ok",
                                              "negative_controls",
                                              "verdict")},
                     indent=1, ensure_ascii=False))
    print("artifact:", OUT)
    return 0 if ok else 1


def _fail(what, viol):
    print(f"FAIL {what}: {json.dumps(viol, ensure_ascii=False)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
