#!/usr/bin/env python3
"""reproduce_direct_escape_wedge.py — 复跑 v26 对抗评审补查：直出球 F.Cu 首发楔形判定。

背景：REVIEW_ADVERSARIAL_v26.md 物理性检查 D 中，两路独立评审均卡在"32 个 DIRECT_F.CU
分类球是否真能 F.Cu 穿出密集球阵"未闭合；本脚本 = 执行者对开放问题的**有界确定性补查**
（独立楔形几何，非引擎自证）。结论：32/32 直出球均有合法首发楔形（无一 pad-locked）；
但 B_PER row1（by≈57.12，上数第二排）8 球仅 4.5~12° 向南楔形——首发可行≠全程可穿，
全程穿线（C1 条件）留给 L3 dogbone 逐段验证。

几何规则（与 PCB_DESIGN_RULES 对齐）：
  trace 宽 0.205 + 净距 0.1 + pad 半径 0.1525 → trace 中心线须距邻球中心 ≥0.355mm。
  对每颗球：把邻球（2.5mm 内）对以球心为原点的角度轴投影为"阻断弧"
  [φ−asin(0.355/r), φ+asin(0.355/r)]；合并后若存在空隙 → 该方向可发出一条 0.205 走线。
  对全 354 球（含 GND/VCC/NC 非信号球）求最近邻，修正引擎只测 128 信号球的测量口径缺陷。

用法：python3 reproduce_direct_escape_wedge.py
输出：direct_escape_wedge_report.json（逐直出球: has_first_move / 最宽楔形中心/角宽/方向扇区）
依赖：_shared 与 ds320pr1601_ballmap.json（路径向上定位，权威 = 容器根 _shared）。
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_gm = [p for p in HERE.parents if (p / ".gitmodules").exists()]
SP = _gm[-1] if _gm else HERE.parents[-1]
sys.path.insert(0, str(SP / "_shared"))

BALLMAP = HERE / "ds320pr1601_ballmap.json"
CX, CY = 93.8, 53.7          # U1 板中心（板 x = 93.8 + y_mm；板 y = 53.7 + x_mm）
TRACE_HALF = 0.1025          # 0.205/2
CLR = 0.10
PAD_R = 0.305 / 2
REQ = PAD_R + CLR + TRACE_HALF   # 0.355：trace 中心线距邻球中心最小距
RMAX = 2.5                        # 首发近场半径


def band_of(sig: str):
    for k in ("A_PER", "B_PET", "A_PET", "B_PER"):
        if sig.startswith(k):
            return k
    return None


def load():
    data = json.loads(BALLMAP.read_text(encoding="utf-8"))
    out = []
    for p in data["ballmap"]:
        b = band_of(p["signal"])
        m = re.search(r"(\d+)$", p["signal"]) if b else None
        out.append({"name": p["name"], "sig": p["signal"], "band": b,
                    "lane": int(m.group(1)) if m else None,
                    "bx": CX + p["y_mm"], "by": CY + p["x_mm"]})
    return out


def wedge(ball, balls):
    """(has_gap, gap_rad, gap_center_deg, gap_zone) — 最宽可行楔形（角度轴 0=bx+E,90=by+N）。"""
    intr = []
    for o in balls:
        if o["name"] == ball["name"]:
            continue
        dx, dy = o["bx"] - ball["bx"], o["by"] - ball["by"]
        r = math.hypot(dx, dy)
        if r > RMAX:
            continue
        phi = math.atan2(dy, dx)
        hw = math.pi if r <= REQ else math.asin(REQ / r)
        intr.append((phi - hw, phi + hw))
    if not intr:
        return True, math.inf, 90.0, "OPEN"
    intr.sort()
    merged = [list(intr[0])]
    for s, e in intr[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    worst = None
    for i in range(len(merged) - 1):
        g = merged[i + 1][0] - merged[i][1]
        if g > 1e-6 and (worst is None or g > worst[0]):
            worst = (g, merged[i][1], merged[i + 1][0])
    wg = (merged[0][0] + 2 * math.pi) - merged[-1][1]
    if wg > 1e-6 and (worst is None or wg > worst[0]):
        worst = (wg, merged[-1][1], merged[0][0] + 2 * math.pi)
    if worst is None:
        return False, 0.0, 0.0, "LOCKED"
    w, s, e = worst
    c = math.degrees((s + e) / 2) % 360
    zone = ("N" if 60 <= c <= 120 else
            "S" if 240 <= c <= 300 else
            "W" if 135 < c < 225 else
            "E" if c < 45 or c > 315 else "DIAG")
    return True, math.degrees(w), c, zone


def main() -> int:
    balls = load()
    allb = balls  # 全 354 球（含非信号）作障碍
    k2 = [p for p in balls if p["band"] and p["lane"] is not None and p["lane"] in range(8)]
    direct = [p for p in k2
              if (p["band"][0] == "B" and p["bx"] < CX) or (p["band"][0] == "A" and p["bx"] > CX)]
    per = []
    for p in sorted(direct, key=lambda q: (q["band"], q["lane"] or 0)):
        has, wdeg, cdeg, zone = wedge(p, allb)
        per.append({"name": p["name"], "signal": p["sig"], "band": p["band"],
                    "lane": p["lane"], "bx_mm": round(p["bx"], 3), "by_mm": round(p["by"], 3),
                    "has_first_move": has, "widest_wedge_deg": round(wdeg, 2),
                    "wedge_center_deg": round(cdeg, 2), "wedge_zone": zone})
    n_ok = sum(1 for x in per if x["has_first_move"])
    bper_r1 = [x for x in per if x["band"] == "B_PER" and abs(x["by_mm"] - 57.12) < 0.05]
    bper_r2 = [x for x in per if x["band"] == "B_PER" and abs(x["by_mm"] - 57.64) < 0.05]
    summary = {
        "direct_ball_count": len(direct),
        "direct_with_legal_first_move": n_ok,
        "direct_pad_locked": len(direct) - n_ok,
        "b_per_row1_by57_12": {"n": len(bper_r1),
                               "wedge_deg": sorted(x["widest_wedge_deg"] for x in bper_r1),
                               "zone": sorted(set(x["wedge_zone"] for x in bper_r1))},
        "b_per_row2_by57_64": {"n": len(bper_r2),
                               "wedge_deg": sorted(x["widest_wedge_deg"] for x in bper_r2),
                               "zone": sorted(set(x["wedge_zone"] for x in bper_r2))},
        "note": "首发楔形可行≠全程 F.Cu 穿线可行（后者 = L3 dogbone 逐段验证 / C1 条件）",
    }
    out = HERE / "direct_escape_wedge_report.json"
    out.write_text(json.dumps({"summary": summary, "per_ball": per},
                              indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote %s : direct=%d first_move_ok=%d/%d" % (out.name, len(direct), n_ok, len(direct)))
    print("B_PER row1(by57.12): wedge=%s zone=%s" % (summary["b_per_row1_by57_12"]["wedge_deg"],
                                                     summary["b_per_row1_by57_12"]["zone"]))
    print("B_PER row2(by57.64): wedge=%s zone=%s" % (summary["b_per_row2_by57_64"]["wedge_deg"],
                                                     summary["b_per_row2_by57_64"]["zone"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
