#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""gen_chip_landing_v33.py — M14 v33: 芯片侧 per_ball VIA_IN2 落点表生成
(断裂点4 芯片侧: per_ball 落点接入 hs_route_model 施工链的数据资产)。

落点净空判定与引擎 _landing_escape 完全同构:
  fcu_field = build_hs_field(board, rules, layer="F.Cu", clear_hs_pads=True,
                             clear_hs_nets=(net,))
  esc_field = build_hs_field(board, rules, layer="In2.Cu", ...)
  via 落点须 fcu_field.point_ok + esc_field.point_ok (引擎落点净空即用此法)。

输入:
  per_ball_escape_6L_report.json  (method/bx/by 判定, L2 资产)
  真板 k2_v4.kicad_pcb (pcbnew 权威 pad 坐标 = 引擎坐标系)

输出: chip_landing_v33.json
  { "<net>": {"net","method","status","pad":[x,y],"landing":{"x","y"}} }
  仅收录 method==VIA_IN2 且能求得净空落点的网; deficits 逐条附证据。
确定性: 方向固定序(8) → 半径固定序(0.05 步) → first-clear; 零随机。
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_gm = [p for p in HERE.parents if (p / ".gitmodules").exists()]
SHARED = (_gm[-1] if _gm else HERE.parents[-1]) / "_shared"
sys.path.insert(0, str(SHARED))

import pcbnew  # noqa: E402

from eda_core.hs_route_model import (  # noqa: E402
    BoardParser, DRCRuleLibrary, build_hs_field)

PER_BALL = HERE / "per_ball_escape_6L_report.json"
BOARD_PATH = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"
RULES_PATH = SHARED / "eda_core" / "drc_rules.json"
OUT = HERE / "chip_landing_v33.json"

_DIRS = ((1.0, 0.0), (0.0, 1.0), (0.0, -1.0),
         (0.7071067811865476, 0.7071067811865476),
         (0.7071067811865476, -0.7071067811865476),
         (-0.7071067811865476, 0.7071067811865476),
         (-0.7071067811865476, -0.7071067811865476),
         (-1.0, 0.0))


def main() -> int:
    report = json.loads(PER_BALL.read_text())
    board = BoardParser(BOARD_PATH).parse()
    rules = DRCRuleLibrary(str(RULES_PATH))
    pcb = pcbnew.LoadBoard(BOARD_PATH)
    u6 = None
    for f in pcb.GetFootprints():
        if "DS320" in str(f.GetFPID().GetLibItemName()):
            u6 = f
            break
    if u6 is None:
        print("ERR: DS320 footprint 未找到")
        return 2
    pad_pos = {}
    pad_net = {}
    for p in u6.Pads():
        pp = p.GetPosition()
        pad_pos[str(p.GetPadName())] = (pp.x / 1e6, pp.y / 1e6)
        pad_net[str(p.GetPadName())] = str(p.GetNetname()).strip()

    out_map = {}
    deficits = []
    via_pts = []
    balls = [b for b in report.get("per_ball", [])
             if b.get("method") == "VIA_IN2"]
    for b in sorted(balls, key=lambda q: q["signal"]):
        pad = pad_pos.get(b["name"])
        net = pad_net.get(b["name"])
        if pad is None or not net:
            deficits.append(f"{b['name']} ({b['signal']}): pad/net 解析失败")
            continue
        fcu = build_hs_field(board, rules, layer="F.Cu",
                             clear_hs_pads=True, clear_hs_nets=(net,))
        esc = build_hs_field(board, rules, layer="In2.Cu",
                             clear_hs_pads=True, clear_hs_nets=(net,))
        best = None
        for dx, dy in _DIRS:
            for r_i in range(6, 25):
                r = r_i * 0.05
                vx = round(pad[0] + dx * r, 3)
                vy = round(pad[1] + dy * r, 3)
                if not (fcu.point_ok(net, (vx, vy))
                        and esc.point_ok(net, (vx, vy))):
                    continue
                if any(math.hypot(vx - ox, vy - oy) < 0.4
                       for ox, oy in via_pts):
                    continue
                hx = (vx, pad[1])
                if not fcu.seg_ok(net, pad, hx):
                    continue
                if not fcu.seg_ok(net, hx, (vx, vy)):
                    continue
                best = (vx, vy)
                break
            if best:
                break
        if best is None:
            deficits.append(f"{net} ({b['name']}, {b['signal']}): 8 方向"
                            f"×0.3-1.2mm 无 fcu+esc 双净空落点")
            continue
        via_pts.append(best)
        out_map[net] = {
            "net": net, "method": "VIA_IN2", "status": "ASSIGNED",
            "pad": [round(pad[0], 3), round(pad[1], 3)],
            "landing": {"x": best[0], "y": best[1]},
            "signal": b["signal"], "ball": b["name"],
        }

    out = {
        "probe": "gen_chip_landing_v33",
        "basis": "per_ball_escape_6L_report(method) + 真板 U6 pad(引擎坐标系)"
                 " + build_hs_field fcu/esc point_ok (与 _landing_escape 同构)",
        "chip_center": [93.8, 53.7],
        "count": len(out_map),
        "landing": out_map,
        "deficits": deficits,
        "verdict": "FEASIBLE" if not deficits else "PARTIAL",
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"wrote {OUT.name}: via_nets={len(out_map)} deficits={len(deficits)}")
    for d in deficits:
        print("  deficit:", d)
    return 0 if not deficits else 1


if __name__ == "__main__":
    raise SystemExit(main())
