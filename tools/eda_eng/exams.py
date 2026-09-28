"""exams --- 考题 A/B 的回归测试定义（#K2-356 §二.2 · #K2-358 §三）。

考题 A：左簇 U1/U2/U4/U5 平移 +5.000mm(X)  ⇒ 引擎重布
考题 B：H4 精确落角                      ⇒ 引擎局部 rip-up & reroute
两题都用同一把尺（verify.judge）。本模块只**定义场景**；执行走 place/route（引擎未建前明确报 NOT_IMPLEMENTED）。
"""
from __future__ import annotations

EXAMS = {
    "A": {"id": "A", "scenario": "translate U1/U2/U4/U5 by +5.000 mm in X",
          "refs": ["U1", "U2", "U4", "U5"], "delta_mm": [5.0, 0.0],
          "reuse": "place + route", "affected_nets": 21},
    "B": {"id": "B", "scenario": "H4 lands exactly in its corner [140.9287,76.9287] (SPEC rev-62)",
          "refs": ["H4"], "reuse": "place + route (local rip-up)",
          "affected_nets": ["PCIE_DN4_N", "PCIE_DN4_P", "PCIE_DN5_N", "PCIE_DN5_P",
                            "PCIE_DN6_N", "PCIE_DN6_P", "PCIE_DN7_N", "PCIE_DN7_P"],
          "occupants": ["PCIE_UP_OUT1_N_J2", "PCIE_UP_OUT2_P_J2", "PCIE_UP_OUT3_N_J2", "PCIE_UP_OUT4_P_J2",
                        "PCIE_UP_OUT5_N_J2", "PCIE_UP_OUT6_P_J2", "PCIE_UP_OUT7_N_J2", "J2_pad_grid"]},
}
JUDGING_TABLE = {"C1": "unconnected == 0", "C2": "DRC total <= 168 and no new class",
                 "C3": "max per-pair copper-length delta <= 0.15 mm", "C4": "45-degree segments >= 2637",
                 "C5": "segment-level element-set difference != 0", "C6(B only)": "C21 four corners all PASS"}
