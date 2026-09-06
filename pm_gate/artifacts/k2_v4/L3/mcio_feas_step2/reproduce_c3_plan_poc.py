#!/usr/bin/env python3
"""reproduce_c3_plan_poc.py — 复跑 C3 机制实证：⑦ per-ball 在生产 plan() 真执行。

背景：REVIEW_ADVERSARIAL_v26 条件 C3 — SPEC_k2_v4.json 仍旧 U3/U7 无 bga_escape.per_ball
→ 生产 plan() 得 ⑦=not_configured（ok=True 静默过，可验证性断裂）。本脚本 = C3 修复路径的
机制级实证（POC）：用注入 `components.redriver.DS320PR1601.bga_escape.per_ball` 的 SPEC
变体跑真实 `routing_topology_gate.plan()`，验证 ⑦ = evaluated FEASIBLE（消除假静默）。

依赖（容器根权威 _shared 引擎 v1.4）：
  SPEC_k2_v4_c3poc.json   = 生产 SPEC_k2_v4.json 副本 + DS320PR1601.per_ball 注入（本目录）
  /tmp/opencode/boards/k2_v6.kicad_pcb（卡0落位板，生产基线）
  channel_alloc_v4/channel_alloc.json（生产 alloc）

用法：python3 reproduce_c3_plan_poc.py
输出：stdout 逐约束状态；断言 ⑦ BGA_PER_BALL_ESCAPE = evaluated + FEASIBLE。
注意：本 POC 只证"机制路径打通"；SPEC 本体再生（U3/U7→DS320PR1601 全量）待真板 ECO
（见 C3_SPEC_REGEN_v27.md §3），未以 POC 冒充再生完成。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 权威 _shared = 最外含 .gitmodules 的父（容器根）
_gm = [p for p in HERE.parents if (p / ".gitmodules").exists()]
SP = _gm[-1] if _gm else HERE.parents[-1]
sys.path.insert(0, str(SP / "_shared"))

from eda_core.routing_topology_gate import RoutingTopologyGate  # noqa: E402

K2_BOARD = "/tmp/opencode/boards/k2_v6.kicad_pcb"
K2_SPEC = str(HERE / "SPEC_k2_v4_c3poc.json")
K2_ALLOC = str(HERE.parent / "model_solves" / "channel_alloc_v4" / "channel_alloc.json")
K2_RULES = str(SP / "_shared" / "eda_core" / "drc_rules.json")
K2_CONFIG = str(HERE.parent.parent / "L2" / "route_model_config.json")  # k2_v4/L2


def main() -> int:
    cfg = json.load(open(K2_CONFIG, encoding="utf-8"))
    gate = RoutingTopologyGate(K2_BOARD, K2_SPEC, K2_ALLOC, K2_RULES, config=cfg)
    r = gate.plan()
    print("version=%s verdict=%s" % (r["version"], r["verdict"]))
    c7 = r["constraints"]["BGA_PER_BALL_ESCAPE"]
    print("BGA_PER_BALL_ESCAPE ok=%s status=%s level=%s"
          % (c7["ok"], c7.get("status"), c7.get("level")))
    for ref, res in (c7.get("per_ref") or {}).items():
        print("  %s: verdict=%s ok=%s signal=%d direct=%d via=%d crossing=%d deficits=%d"
              % (ref, res.get("verdict"), res.get("ok"), res.get("signal_ball_count"),
                 res.get("direct_count"), res.get("via_count"),
                 res.get("crossing_pairs"), len(res.get("deficits", []))))
    passed = (c7.get("status") == "evaluated" and c7.get("ok")
              and any(v.get("verdict") == "FEASIBLE" for v in (c7.get("per_ref") or {}).values()))
    print("POC_PASS" if passed else "POC_FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
