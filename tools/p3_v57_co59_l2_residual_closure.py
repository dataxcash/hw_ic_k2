#!/usr/bin/env python3
"""CO-59：【L2 自裁】残余项机器闭合 + 对间口径来自**冻结输入**的证据再基。

背景：handoff §4 列了三条"非阻塞残余"，其中 ②「B.Cu 判非阻抗控制层 ⇒ In6 阻抗关键段下方
B.Cu 不得并行铺铜/走线」是可机判的 L2 项；Q1（R3-2 0.875 时效）此前被表述为
"1.08(capacity) vs 1.580(realized)" 二选一，但当时**未读冻结输入 `route_model_config.json`**
（L2 冻结口径注入点）——本工具把它读进来作为口径的权威出处。

本工具（只读、字节确定性）：
  A. 残余②机判：L4 板 B.Cu 与 In6 阻抗关键段的**并行耦合**检查（角度/重叠/横向净距）；B.Cu zone 计数。
  B. 交付对间距机判：从 L4 板 In6 长平行带实测每条走廊的**对间距**（与冻结要求 1.46/0.875 对照）。
  C. 口径出处对账：route_model_config.json 的 capacity_audit.inter_pair_spacing / channel_alloc.pitch_fallback
     + 引擎 CO16_LANE_STEP 常量三者并排 ⇒ 判定"要求量"是铜边 0.875 还是中心距 1.46。

零几何/阈值改动；冻结源只读。
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
CFG = K2 / "pm_gate/artifacts/k2_v4/L2/route_model_config.json"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-4.json"
RULES = K2.parent / "_shared/eda_core/drc_rules.json"
ENGINE = K2 / "tools/p3_v57_w3_constructive.py"
OUT = STEP2 / "m13_v57_co59_l2_residual_closure.json"

# 冻结要求（L1 v2.0 硬约束 2 / L2 v2.0 硬约束 3；route_model_config.json 注入点）
REQ_EDGE_MM = 0.875          # R3-2 对间铜边净空（要求量）
REQ_CENTER_MM = 1.46         # = 0.585(冻结对铜跨) + 0.875 的中心距换算式
PAR_ANGLE_DEG = 10.0         # 并行判定角容差
PAR_OVERLAP_MM = 0.30        # 并行重叠下限
PAR_PERP_MM = 0.50           # 并行横向净距关注带（中心线）
W_TRACE = 0.205              # 交付差分线宽（L4 实测，SPEC 0.205）


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def parse_board(txt: str):
    segs = re.findall(
        r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*'
        r'\(width ([-\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net "([^"]+)"\)', txt)
    out = []
    for a, b, c, d, w, l, n in segs:
        x1, y1, x2, y2 = map(float, (a, b, c, d))
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        out.append(dict(x1=x1, y1=y1, x2=x2, y2=y2, w=float(w), layer=l, net=n,
                        dx=dx, dy=dy, L=L, ang=math.degrees(math.atan2(dy, dx)) % 180))
    vias = re.findall(r'\(via(?:\s+(?:blind|micro))?\s*\(at ([-\d.]+) ([-\d.]+)\)\s*'
                      r'\(size ([-\d.]+)\)\s*\(drill ([-\d.]+)\)\s*\(layers "([^"]+)" "([^"]+)"\)', txt)
    zones = re.findall(r'\(zone\s*\(layer "([^"]+)"\)\s*\(uuid "([^"]+)"\)\s*\(name "([^"]*)"\)', txt)
    return out, vias, zones


def parallel_metric(a, b):
    """返回 (重叠长度, 横向中心线距离, 夹角)。仅当夹角≤容差才算并行候选。"""
    dang = abs(a["ang"] - b["ang"])
    dang = min(dang, 180.0 - dang)
    if dang > PAR_ANGLE_DEG:
        return 0.0, None, dang
    ux, uy = a["dx"] / a["L"], a["dy"] / a["L"]

    def proj(p):
        return (p[0] - a["x1"]) * ux + (p[1] - a["y1"]) * uy

    p0, p1 = proj((b["x1"], b["y1"])), proj((b["x2"], b["y2"]))
    ov = min(a["L"], max(p0, p1)) - max(0.0, min(p0, p1))
    if ov <= 0:
        return 0.0, None, dang
    mx, my = (b["x1"] + b["x2"]) / 2, (b["y1"] + b["y2"]) / 2
    perp = abs(-uy * (mx - a["x1"]) + ux * (my - a["y1"]))
    return ov, perp, dang


def corridor_rows(segs, x_probe: float, y_lo: float, y_hi: float):
    """长水平 In6 带：取覆盖 x_probe 且 y 落带内的水平段，返回 y 行与出现网名。"""
    rows = {}
    for s in segs:
        if s["layer"] != "In6.Cu" or abs(s["y2"] - s["y1"]) > 1e-6:
            continue
        if abs(s["x2"] - s["x1"]) < 5.0:
            continue
        x_lo, x_hi = sorted((s["x1"], s["x2"]))
        if not (x_lo <= x_probe <= x_hi):
            continue
        if not (y_lo <= s["y1"] <= y_hi):
            continue
        rows.setdefault(round(s["y1"], 3), set()).add(s["net"])
    ys = sorted(rows)
    steps = [round(ys[i + 1] - ys[i], 3) for i in range(len(ys) - 1)]
    # 对间中心距 = 相邻**同极性**行间距；P/N 交替 ⇒ 2 步差
    pair_steps = sorted({v for v in steps if v >= 1.0})
    two = sorted({round(ys[i + 2] - ys[i], 3) for i in range(len(ys) - 2) if ys[i + 2] - ys[i] >= 1.0})
    intra = sorted({v for v in steps if 0.2 <= v < 1.0})
    return ys, steps, pair_steps, intra, two


def main() -> int:
    txt = BOARD.read_text(encoding="utf-8")
    segs, vias, zones = parse_board(txt)
    cfg = json.loads(CFG.read_text(encoding="utf-8"))

    # ── A. 残余②：B.Cu 与 In6 的并行耦合 ──
    in6 = [s for s in segs if s["layer"] == "In6.Cu" and s["L"] > 0.2]
    bcu = [s for s in segs if s["layer"] == "B.Cu" and s["L"] > 0.2]
    par = []
    for a in in6:
        for b in bcu:
            ov, perp, dang = parallel_metric(a, b)
            if ov > PAR_OVERLAP_MM and perp is not None and perp < PAR_PERP_MM:
                par.append((perp - (a["w"] + b["w"]) / 2, a["net"], b["net"], ov))
    # 参考量：全板 B.Cu×In6 并行对的最小横向中心线距离（不设关注带）
    min_perp = None
    for a in in6:
        for b in bcu:
            ov, perp, _ = parallel_metric(a, b)
            if ov > PAR_OVERLAP_MM and perp is not None:
                min_perp = perp if min_perp is None else min(min_perp, perp)
    bcu_zones = [z for z in zones if z[0] == "B.Cu"]

    # ── B. 交付对间距实测（In6 长平行带）──
    east = corridor_rows(segs, x_probe=120.0, y_lo=50.0, y_hi=85.0)
    west = corridor_rows(segs, x_probe=70.0, y_lo=30.0, y_hi=50.0)
    deliv = {}
    for name, (ys, steps, ps, intra, two) in (("EAST_CHIP_TO_J2", east), ("WEST_MCIO_TO_CHIP", west)):
        pitch = two[0] if len(two) == 1 else (min(two) if two else None)
        span = (min(intra) + W_TRACE) if intra else None      # 对铜跨 = 对内中心距(最紧) + 线宽
        edge = (pitch - span) if (pitch is not None and span is not None) else None
        deliv[name] = {
            "in6_long_rows_y": ys,
            "intra_pair_steps_mm": intra,
            "intra_pair_center_mm": (min(intra) if intra else None),
            "inter_pair_steps_mm": ps,
            "pair_pitch_2step_mm": two,
            "pair_span_mm": (None if span is None else round(span, 4)),
            "inter_pair_pitch_mm": pitch,
            "copper_edge_mm": (None if edge is None else round(edge, 4)),
            "vs_req_center_mm": (None if pitch is None else round(pitch - REQ_CENTER_MM, 4)),
            "vs_req_edge_mm": (None if edge is None else round(edge - REQ_EDGE_MM, 4)),
        }

    # ── C. 口径出处对账 ──
    eng = ENGINE.read_text(encoding="utf-8")
    m = re.search(r"CO16_LANE_STEP\s*=\s*(\{[^}]*\})", eng)
    provenance = {
        "route_model_config.json": {
            "path": "pm_gate/artifacts/k2_v4/L2/route_model_config.json",
            "sha16": sha16(CFG),
            "capacity_audit.inter_pair_spacing": cfg["capacity_audit"]["inter_pair_spacing"],
            "capacity_audit.note": cfg["capacity_audit"].get("note", ""),
            "channel_alloc.pitch_fallback": cfg["channel_alloc"]["pitch_fallback"],
            "channel_alloc.half_pitch": cfg["channel_alloc"]["half_pitch"],
        },
        "engine_lane_step_const": m.group(1) if m else None,
        "reading": ("冻结输入显式声明：inter_pair_spacing 语义 = R3-2 0.875 **对间铜边净空**，"
                    "1.46mm 为其在**冻结对铜跨 0.585** 下的中心距换算；config 注记要求"
                    "勿把 0.875 当中心距注入 ⇒ **要求量是铜边净空 0.875**，1.46 是换算值。"),
    }

    res = {
        "artifact": "m13_v57_co59_l2_residual_closure",
        "schema": 1,
        "revision": "CO-59.1",
        "nature": "L2 自裁：残余②机器闭合 + 对间口径证据再基（只读；零几何/阈值改动）",
        "inputs_sha": {
            "board_l4": sha16(BOARD),
            "route_model_config": sha16(CFG),
            "spec_rev4": sha16(SPEC),
            "drc_rules": sha16(RULES),
        },
        "A_bcu_in6_coupling": {
            "criterion": {"parallel_angle_deg_le": PAR_ANGLE_DEG, "overlap_mm_gt": PAR_OVERLAP_MM,
                          "centerline_perp_mm_lt": PAR_PERP_MM},
            "parallel_couplings": len(par),
            "worst_edge_gap_mm": (min(p[0] for p in par) if par else None),
            "min_centerline_perp_any_mm": (None if min_perp is None else round(min_perp, 3)),
            "b_cu_segments": len(bcu),
            "b_cu_nets": len({s["net"] for s in bcu}),
            "b_cu_zones": len(bcu_zones),
            "verdict": "PASS" if not par else "FAIL",
            "note": ("B.Cu 实体走线存在（残余②声明的非阻塞项），但**无并行**铺铜/走线落入 "
                     "In6 关键段关注带；与 In6 的关系为垂交（B.Cu 段为纵向、In6 带为横向）。"),
        },
        "B_delivered_interpair": deliv,
        "C_requirement_provenance": provenance,
        "conformance": "残余②=PASS；对间口径=待 owner 确认要求量（铜边 0.875 realized vs 中心距 1.46 换算）",
        "gate_impact": "none（零改动；G4..G7 不变）",
        "open_item": ("Q1 收窄：要求量 = **铜边净空 0.875**（冻结 config 注记原文）⇒ 交付对铜跨 0.705 下，"
                      "中心距需 ≥ 0.705+0.875 = **1.580**（realized 读数）。若 owner 认定 1.46 中心距口径"
                      "（即 0.585 跨换算）为准，则目标 = 1.46。**现交付：EAST 1.449 / WEST 1.05 ⇒ 两读数下均不达标。**"),
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(OUT.relative_to(K2)),
        "sha16": sha16(OUT),
        "bcu_par": len(par),
        "bcu_min_perp": res["A_bcu_in6_coupling"]["min_centerline_perp_any_mm"],
        "bcu_zones": len(bcu_zones),
        "east_pitch": deliv["EAST_CHIP_TO_J2"]["inter_pair_pitch_mm"],
        "west_pitch": deliv["WEST_MCIO_TO_CHIP"]["inter_pair_pitch_mm"],
        "req_center": REQ_CENTER_MM, "req_edge": REQ_EDGE_MM,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
