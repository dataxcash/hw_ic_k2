#!/usr/bin/env python3
"""c1_via_reclass_review.py — C1-b 确定性复核：直出球改判 VIA+In2 stub 的 6L 容量账。

背景：REVIEW_ADVERSARIAL_v26.md 条件 C1 — B_PER row1(by≈57.12) 8 球仅 4.5~12°
南向楔形、F.Cu 全程穿线未证（首发可行 ≠ 全程可穿）。用户裁决走路径 b：
改判 VIA+In2 stub 复核（via 预算 64≤69 兜底，评审 §1/§2-D 独立复核不翻转）。

本脚本 = C1-b 的确定性容量复核（证书求解器，G3 边界：**非引擎、非模型结论，
仅几何判定证据**）。为何不 force 引擎分类：per-ball 引擎 `VIA_IN2` 语义 = A 带
西半球东穿（crossing 型）；直出球改判属 west 侧 In2 stub（不穿越），force 会把
stub 误建模为 crossing → 翼带需求翻倍错判。故 stub 型改判以独立确定性账复核，
穿越对保持引擎基线 16 对不动。

复核场景（确定性枚举，零搜索）：
  S0 基线      = 引擎现判：32 直出 / 32 via，crossing 16 对，via 32≤69
  S1 row1 改判 = B_PER row1(by 57.12±0.05) 8 球 direct→via(west-stub)
  S2 全直出改判= 32 直出全→via(west-stub)  ← 评审最坏情形 64≤69

输出：c1_via_reclass_report.json（{scenarios, verdict, ...}），可复跑禁删。

依赖：ds320pr1601_ballmap.json（真实 354 球）+ per_ball_escape_6L_report.json
（S0 引擎基线，经 reproduce_per_ball_escape.py 复跑生成）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BALLMAP = HERE / "ds320pr1601_ballmap.json"
BASE_REPORT = HERE / "per_ball_escape_6L_report.json"

CX, CY = 93.8, 53.7
VIA_CAP = 69          # In2 via 容量（desc via_zone_capacity；v22 capacity_audit 同源）
WING_N = 16.2         # In2 N 翼带可用（desc in2_wings）
WING_S = 20.8 - 2.0   # In2 S 翼带可用（REFCLK 2.0 预留后 = 18.8）
IPAIR = 1.46          # inter_pair_spacing（对中心距，v22 已裁口径）
ROW1_BY = 57.12


def load_balls() -> list:
    data = json.loads(BALLMAP.read_text(encoding="utf-8"))
    out = []
    for b in data["ballmap"]:
        m = re.match(r"^(A_PER|B_PET|A_PET|B_PER)(P|N)(\d+)$", b.get("signal", ""))
        if not m:
            continue
        lane = int(m.group(3))
        if lane >= 8:
            continue
        out.append({"name": b["name"], "signal": b["signal"], "band": m.group(1),
                    "polarity": m.group(2), "lane": lane,
                    "bx": CX + b["y_mm"], "by": CY + b["x_mm"]})
    return out


def via_balls_of(balls: list) -> list:
    """A 带（port A→east）西半球 = ball-via→In2 东穿（引擎分类语义，S0 基线）。"""
    return [p for p in balls if p["band"].startswith("A") and p["bx"] < CX]


def direct_balls_of(balls: list) -> list:
    return [p for p in balls if p["band"].startswith("B") and p["bx"] < CX]


def crossing_pairs_of(via_balls: list) -> int:
    """东穿 crossing 对数 = A 带（port A→east）via 球按 lane 去重。

    B 带球改判 via 属 west 侧 In2 stub（F→In2→F 潜行回西走廊），不东穿，
    不增 crossing 对 —— 与引擎语义差别的显式账（见模块 docstring）。
    """
    return len({p["band"] + ":" + str(p["lane"]) for p in via_balls
                if p["band"].startswith("A")})


def main() -> int:
    balls = load_balls()
    via0 = via_balls_of(balls)
    d0 = direct_balls_of(balls)
    crossing0 = crossing_pairs_of(via0)

    row1 = [p for p in d0 if p["band"] == "B_PER" and abs(p["by"] - ROW1_BY) < 0.05]
    scenarios = {}

    # S0 基线（引擎基线引用）
    base = json.loads(BASE_REPORT.read_text(encoding="utf-8"))
    scenarios["S0_baseline_engine"] = {
        "via_balls": len(via0), "direct_balls": len(d0),
        "crossing_pairs": crossing0, "via_demand": len(via0),
        "via_capacity": VIA_CAP, "via_ok": len(via0) <= VIA_CAP,
        "wing_need_mm": round((crossing0 / 2) * IPAIR, 3),
        "wing_N_ok": round((crossing0 / 2) * IPAIR, 3) <= WING_N,
        "wing_S_ok": round((crossing0 / 2) * IPAIR, 3) <= WING_S,
        "engine_verdict": base.get("verdict"),
    }

    # S1：B_PER row1 8 球 direct→via(west stub，不穿越)
    via1 = via0 + row1
    scenarios["S1_bper_row1_via"] = {
        "reclass_balls": sorted(p["name"] for p in row1),
        "reclass_count": len(row1),
        "via_demand": len(via1), "via_capacity": VIA_CAP,
        "via_ok": len(via1) <= VIA_CAP,
        "crossing_pairs_unchanged": crossing_pairs_of(via1) == crossing0,
        "note": "stub 型改判不增穿越对（west 侧 In2 stub 潜行，非东穿）",
    }

    # S2：32 直出全改判（评审最坏情形 64≤69）
    via2 = via0 + d0
    scenarios["S2_all_direct_via"] = {
        "reclass_balls": len(d0), "via_demand": len(via2),
        "via_capacity": VIA_CAP, "via_ok": len(via2) <= VIA_CAP,
        "crossing_pairs_unchanged": crossing_pairs_of(via2) == crossing0,
        "margin": VIA_CAP - len(via2),
    }

    all_ok = (scenarios["S0_baseline_engine"]["via_ok"]
              and scenarios["S1_bper_row1_via"]["via_ok"]
              and scenarios["S2_all_direct_via"]["via_ok"]
              and scenarios["S2_all_direct_via"]["crossing_pairs_unchanged"])
    report = {
        "probe": "c1_via_reclass_review",
        "level": "certificate_review",   # G3 边界：非引擎、仅几何判定证据
        "basis": "REVIEW_ADVERSARIAL_v26 C1 路径 b（用户裁决 2026-09-06）",
        "verdict": "FEASIBLE_UNCHANGED" if all_ok else "REVIEW_FAIL",
        "ok": all_ok,
        "scenarios": scenarios,
        "remaining_to_l3": [
            "B_PER row1 8 球若走 stub 的 In2 逐段落点 = L3 dogbone 级（本复核只证容量账）",
            "引擎 VIA_IN2 语义=crossing；stub 型改判以本证书复核兜底，非引擎重判",
        ],
        "numbers": {"via_capacity": VIA_CAP, "inter_pair_spacing": IPAIR,
                    "wing_N_avail": WING_N, "wing_S_avail": WING_S,
                    "b_per_row1_by": ROW1_BY},
    }
    out = HERE / "c1_via_reclass_report.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote %s : verdict=%s via_demand S0=%d S1=%d S2=%d (cap=%d)"
          % (out.name, report["verdict"], len(via0), len(via1), len(via2), VIA_CAP))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
