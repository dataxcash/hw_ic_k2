#!/usr/bin/env python3
"""reproduce_per_ball_escape.py — 复跑 m14 v26 per-ball BGA 逃逸判定（层数定案闸执行器）。

消费 ds320pr1601_ballmap.json（v25 真实 354 球 vendor-validated 坐标），构造
bga_escape.per_ball 描述符，经 _shared/eda_core 的 per-ball 引擎（路径 a ECN 新增：
escape_landing.bga_per_ball_escape + routing_topology_gate._check_bga_per_ball_escape）
做确定性逐球逃逸判定（一次对，禁暴力迭代）。

用法：python3 reproduce_per_ball_escape.py
输出：per_ball_escape_6L_report.json（{verdict, per_band, per_wing, per_ball, deficits}）
依赖：_shared（本仓库子模块）在容器根，发行路径按 sys.path 注入。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 权威 _shared = 最外 superproject(ic_hw 容器根) 下的 _shared；避免命中 k2 内嵌陈旧副本。
# 注：k2 自身也是 superproject(含 .gitmodules 指向其内嵌 _shared)，故取「最远含 .gitmodules」的父。
_gm = [p for p in HERE.parents if (p / ".gitmodules").exists()]
SP = _gm[-1] if _gm else HERE.parents[-1]
SHARED = SP / "_shared"
sys.path.insert(0, str(SHARED))

from eda_core.escape_landing import bga_per_ball_escape  # noqa: E402

BALLMAP = HERE / "ds320pr1601_ballmap.json"


def build_desc() -> dict:
    data = json.loads(BALLMAP.read_text(encoding="utf-8"))
    ballmap = data["ballmap"]
    return {
        "package": "nfBGA-354 (ZDG)", "pitch_mm": 0.6, "array_mm": [8.9, 22.8],
        "ball_count": 354,
        "group_bands": [
            {"name": "A_PER", "method": "crossing", "pairs": 8, "escape_slots": 8},
            {"name": "B_PET", "method": "via",      "pairs": 8, "escape_slots": 8},
            {"name": "A_PET", "method": "via",      "pairs": 8, "escape_slots": 8},
            {"name": "B_PER", "method": "direct",   "pairs": 8, "escape_slots": 8},
        ],
        "per_ball": {
            "ballmap": ballmap,
            "chip_center": [93.8, 53.7],
            "axis": {"board_x": "ball_y", "board_y": "ball_x"},
            "selected_lanes": list(range(8)),
            "inter_pair_spacing": 1.46,
            "port_to_corridor": {"A_PER": "east", "B_PET": "east",
                                 "A_PET": "west", "B_PER": "west"},  # ECN-007: band-keyed
            "corridor_edge": {"east": 105.25, "west": 82.35},
            "band_corridor_capacity": {"east": 16, "west": 16},
            "via_zone_capacity": 69,
            "in2_wings": [{"name": "N", "in2_mm": 16.2, "refclk_mm": 0.0},
                          {"name": "S", "in2_mm": 20.8, "refclk_mm": 2.0}],
            "pair_pitch_mm": 0.6,
            "pad_mm": 0.305, "via_mm": 0.35, "clearance_mm": 0.10,
            "signal_bands": ["A_PER", "B_PET", "A_PET", "B_PER"],
        },
    }


def main() -> int:
    desc = build_desc()
    report = bga_per_ball_escape(desc)
    out = HERE / "per_ball_escape_6L_report.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out.name} : verdict={report['verdict']} "
          f"signal_balls={report['signal_ball_count']} "
          f"direct={report['direct_count']} via={report['via_count']} "
          f"crossing_pairs={report['crossing_pairs']} deficits={len(report['deficits'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
