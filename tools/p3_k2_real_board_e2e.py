#!/usr/bin/env python3
"""P3-B — K2 真板端到端：组装真板 SolveInput → solve_pipeline.run_all 五阶段。

任务卡：k2/pm_gate/artifacts/k2_v4/L3/p3_k2_real_board_e2e_card.md
运行真源：容器级 _shared（/home/fila/jqdDev_2025/ic_hw/_shared，含 P2 匹配器 + hs_route_model
          landing 消费 + solve_pipeline 5 阶段全真接）。k2/_shared 为陈旧子模块快照
          （84b613d，3 桩旧版，hs_route_model 无 landing 参数）——按 handoff §1 首动作
          用容器 _shared 运行，陈旧快照记为缺口。

组装原则（契约 §1 SolveInput）：
  - board_path : 真板 k2_v4.kicad_pcb（sha=6c387dff，只读，禁止改动）
  - spec       : SPEC_k2_v4.json（L3 真源）+ derived 派生段（从真板+SPEC 生成：
                 landing_demands / capacity_demands / via_zones / cap_walls）
  - rules      : drc_rules.json（drc_semantic_core）
  - config     : route_model_config.json + 声明段（capacity_audit / escape_landing /
                 channel_alloc.channels_from_spec）
  - route_input: spec_to_route_input(SPEC, escape_spec, J2 pads(真板), config)
                 + obstacles.pads 覆写为真板 J2 pad 堆（逃逸落点域 pad 堆；_extract_pads
                 的 tht/B.Cu 过滤会丢弃 J2 SMD F.Cu 焊盘，且全板 508 pad 会破坏
                 escape_landing 双列间隙锚定——缺省 pad 堆 = 右端连接器列堆，契约层零改动）

引擎零改动：solve_pipeline / 各模型只消费 SolveInput；本脚本只做输入组装与结果 dump。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]          # k2/
SHARED = Path("/home/fila/jqdDev_2025/ic_hw/_shared")   # 容器级 _shared（运行真源）
sys.path.insert(0, str(SHARED))

from eda_core.drc_rules import BoardParser            # noqa: E402
from eda_core.route_input import spec_to_route_input  # noqa: E402
from eda_core.solve_pipeline import SolveInput, SolvePipeline  # noqa: E402

# ── 路径 ─────────────────────────────────────────────────────────────
ART = REPO / "pm_gate" / "artifacts" / "k2_v4"
L2 = ART / "L2"
L3 = ART / "L3"
REAL_BOARD = REPO / "k2_v4.kicad_pcb"
SPEC_PATH = L3 / "SPEC_k2_v4.json"
ESCAPE_PATH = L2 / "escape_spec.json"
RULES_PATH = SHARED / "eda_core" / "drc_rules.json"
CONFIG_PATH = L2 / "route_model_config.json"
OUT_DIR = L3 / "p3_real_board_e2e"

J2_X_LO, J2_X_HI = 132.0, 136.0          # 真板 J2 列簇区间（只读探针，非引擎字面量）

# 逃逸落点区窗口（D1 多区，Phase B）：真板 pad 聚类只读探针（J2 双列 132.65/
# 135.0；MCIO 连接器 x∈[54,65] + 直通 x∈[75,85]；U7/U3 芯片 x∈[97,119]/[74,90]）。
# 每区独立 pad 堆/候选序（config.escape_landing.regions 声明，代码零坐标特判）。
REGION_WINDOWS = {
    "J2": (132.0, 136.0),
    "MCIO": (50.0, 90.0),
    "U7": (97.0, 119.0),
    "U3": (74.0, 90.0),
}


def _r3(v: float) -> float:
    return round(float(v), 3)


def load(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_region_pads(board_path: Path, x_lo: float, x_hi: float,
                        ref: str) -> list:
    """真板 → 区 pad 堆（{net,ref,x,y,w,h,tht,layers}，x 窗口过滤，y/x 排序）。
    真板只读（BoardParser.parse 纯解析不改文件）。"""
    b = BoardParser(str(board_path)).parse()
    pads = []
    for p in b.pads:
        if not (x_lo <= p.pos[0] <= x_hi):
            continue
        pads.append({"net": p.net, "ref": ref,
                     "x": _r3(p.pos[0]), "y": _r3(p.pos[1]),
                     "w": _r3(p.size[0]), "h": _r3(p.size[1]),
                     "tht": p.is_tht, "layers": list(p.layers)})
    pads.sort(key=lambda e: (e["y"], e["x"]))
    return pads


def extract_j2_pads(board_path: Path) -> list:
    """真板 k2_v4.kicad_pcb → J2 pad 堆（74 pad，{net,ref,x,y,w,h,tht,layers}）。

    真板只读（BoardParser.parse 纯解析不改文件）。J2 列簇 = x∈[132.0,136.0]
    （真板实测 132.65/135.0 双列，SMD 1.3x0.35，37 行）。"""
    return extract_region_pads(board_path, J2_X_LO, J2_X_HI, "J2")


def derive_landing_demands(j2_pads: list) -> list:
    """真板 J2 pad 网 → 18 对 landing 需求（base/segname/net_p/net_n/pad_p/pad_n）。

    base 提取：PCIE_UP_OUT{k}_{P|N}_J2 → PCIE_UP{k}；PCIE_DN{k}_{P|N} → PCIE_DN{k}；
    PCIE_REFCLK{k}_{P|N} → PCIE_REFCLK{k}。segname=out_J2（右端连接器逃逸段）。"""
    return derive_region_demands_from_pads(j2_pads, "J2", "out_J2")


def derive_region_demands_from_pads(pads: list, suffix: str,
                                    segname: str) -> list:
    """区 pad 网 → 差分对需求（base/segname/net_p/net_n/pad_p/pad_n）。

    base 提取：PCIE_UP_OUT{k}/PCIE_DN_OUT{k} → PCIE_UP{k}/PCIE_DN{k}；
    PCIE_REFCLK{k} → PCIE_REFCLK{k}。确定性：同 stem 同极性多 pad（跨簇）
    → 取 x 最大（右端逃逸消费端）；base 排序。"""
    by_pol: dict = {}
    for p in pads:
        n = p["net"]
        if not n.startswith(("PCIE", "REFCLK")):
            continue
        raw = n[:-(len(suffix) + 1)] if n.endswith("_" + suffix) else n
        if not (raw.endswith("_P") or raw.endswith("_N")):
            continue
        pol = raw[-1]
        stem = raw[:-2]
        prev = by_pol.setdefault(stem, {}).get(pol)
        if prev is None or p["x"] > prev["x"]:
            by_pol[stem][pol] = p
    demands = []
    for stem in sorted(by_pol):
        rec = by_pol[stem]
        if "P" not in rec or "N" not in rec:
            continue
        if stem.startswith("PCIE_UP_OUT"):
            base = "PCIE_UP" + stem[len("PCIE_UP_OUT"):]
        elif stem.startswith("PCIE_DN_OUT"):
            base = "PCIE_DN" + stem[len("PCIE_DN_OUT"):]
        else:
            base = stem
        demands.append({
            "base": base, "segname": segname,
            "net_p": rec["P"]["net"], "net_n": rec["N"]["net"],
            "pad_p": [rec["P"]["x"], rec["P"]["y"]],
            "pad_n": [rec["N"]["x"], rec["N"]["y"]],
        })
    return sorted(demands, key=lambda d: d["base"])


def derive_region_demands(real_board: Path, suffix: str,
                          suffix_only: bool = False) -> list:
    """真板 → 区差分对需求（按 REGION_WINDOWS 窗口 pad + net 后缀匹配）。

    suffix_only=True（MCIO/U7/U3）：只收该区专属后缀网（PCIE_DN_OUT*_MCIO 等）
    ——各网唯一不跨区碰撞（LandingTable.allocation[net] 契约）；False（J2）：
    含窗内全部 PCIE 网（含 DN/REFCLK 输入网，其右端逃逸在 J2 连接器侧）。"""
    x_lo, x_hi = REGION_WINDOWS[suffix]
    pads = extract_region_pads(real_board, x_lo, x_hi, suffix)
    if not suffix_only:
        return derive_region_demands_from_pads(pads, suffix, f"out_{suffix}")
    by_pol: dict = {}
    for p in pads:
        n = p["net"]
        if not n.endswith("_" + suffix):
            continue
        raw = n[:-(len(suffix) + 1)]
        if not (raw.endswith("_P") or raw.endswith("_N")):
            continue
        pol = raw[-1]
        stem = raw[:-2]
        prev = by_pol.setdefault(stem, {}).get(pol)
        if prev is None or p["x"] > prev["x"]:
            by_pol[stem][pol] = p
    demands = []
    for stem in sorted(by_pol):
        rec = by_pol[stem]
        if "P" not in rec or "N" not in rec:
            continue
        base = stem
        if stem.startswith("PCIE_UP_OUT"):
            base = "PCIE_UP" + stem[len("PCIE_UP_OUT"):]
        elif stem.startswith("PCIE_DN_OUT"):
            base = "PCIE_DN" + stem[len("PCIE_DN_OUT"):]
        demands.append({
            "base": base, "segname": f"out_{suffix}",
            "net_p": rec["P"]["net"], "net_n": rec["N"]["net"],
            "pad_p": [rec["P"]["x"], rec["P"]["y"]],
            "pad_n": [rec["N"]["x"], rec["N"]["y"]],
        })
    return sorted(demands, key=lambda d: d["base"])


def derive_capacity_demands(spec: dict, corridors: list) -> list:
    """SPEC corridors（J2_TO_U / U_TO_MCIO × upper/lower/refclk）→ 36 段容量需求。

    base = band.nets[i]（refclk band nets=['PCIE_REFCLK'] → PCIE_REFCLK{i}）；
    track_y = band.tracks_y[i]；via_zones 按段侧注入（J2 侧 / 芯片侧 U7/U3）；
    via_cap = 数据对（PCIE_UP/DN）穿越 AC 电容墙，REFCLK 否。"""
    out = []
    for c in corridors:
        for b in c.get("bands", []):
            nets = b.get("nets") or []
            tys = b.get("tracks_y") or []
            for i, ty in enumerate(tys):
                if b["band"] == "refclk":
                    base = f"PCIE_REFCLK{i}"          # 真网名（PCIE_REFCLK0/1，非带前缀）
                elif nets and i < len(nets):
                    base = nets[i]
                else:
                    base = f"PCIE_REFCLK{i}"
                # 段侧 via 区：J2_TO_U → J2 端；U_TO_MCIO → 芯片端（band 侧）
                if c["id"] == "J2_TO_U":
                    zones = ["J2_ESCAPE"]
                else:
                    zones = ["U7_ESCAPE"] if b["band"] == "upper" else \
                        (["U3_ESCAPE"] if b["band"] == "lower"
                         else ["U7_ESCAPE" if i == 0 else "U3_ESCAPE"])
                out.append({
                    "base": base, "segname": "input",
                    "corridor_id": c["id"], "band": b["band"],
                    "track_y": _r3(float(ty)),
                    "via_zones": zones,
                    "via_cap": base.startswith(("PCIE_UP", "PCIE_DN")),
                })
    return sorted(out, key=lambda d: (d["corridor_id"], d["band"], d["base"]))


def derive_via_zones(spec: dict, escape_spec: dict, j2_pads: list,
                     real_board: Path) -> list:
    """真板/escape_spec → 逃逸 via 区（id/kind/span_mm）。"""
    zones = []
    # 芯片侧：escape_spec pins 的 y bbox 跨度
    pins = escape_spec.get("pins") or []
    for chip, kind in (("U7", "CHIP"), ("U3", "CHIP")):
        cp = [p for p in pins if p.get("chip_ref") == chip]
        ys = [p["pin_xy"][1] for p in cp] if cp else []
        zones.append({"id": f"{chip}_ESCAPE", "kind": kind,
                      "span_mm": _r3(max(ys) - min(ys)) if ys else 0.0})
    # J2 连接器侧：J2 pad 堆 y 跨度
    ys = [p["y"] for p in j2_pads]
    zones.append({"id": "J2_ESCAPE", "kind": "CONN",
                  "span_mm": _r3(max(ys) - min(ys)) if ys else 0.0})
    # MCIO 连接器侧：真板 x<65 pad 簇 y 跨度（MCIO/J3/J4 区，只读探针）
    b = BoardParser(str(real_board)).parse()
    my = [p.pos[1] for p in b.pads if p.pos[0] < 65.0]
    zones.append({"id": "MCIO_ESCAPE", "kind": "CONN",
                  "span_mm": _r3(max(my) - min(my)) if my else 0.0})
    return sorted(zones, key=lambda z: z["id"])


def derive_cap_walls(spec: dict) -> list:
    """SPEC capacitor_walls → 电容墙（ac_coupling_count / side_spans_mm / min_pitch_mm）。

    side_spans：mcio_side_x / j2_side_x 区间跨度（mm）；min_pitch = min_center_pitch_mm。"""
    cw = spec.get("capacitor_walls") or {}
    ac = cw.get("ac_coupling") or {}
    ms = cw.get("mcio_side_x") or [0.0, 0.0]
    js = cw.get("j2_side_x") or [0.0, 0.0]
    return [{
        "id": "AC_CAP_WALL",
        "ac_coupling_count": int(ac.get("count", 0)),
        "side_spans_mm": [_r3(ms[1] - ms[0]), _r3(js[1] - js[0])],
        "min_pitch_mm": float(cw.get("min_center_pitch_mm", 1.3)),
    }]


def derive_cap_wall_pads(real_board: Path, spec: dict) -> list:
    """真板 → MCIO 侧串联 AC 电容 pad 集（series_cap_wall 墙位置源）。

    过滤：SPEC capacitor_walls.ac_coupling.downstream_refs（C17-C32 等
    footprint refdes）∩ net 尾 _MCIO ——每网恰 1 个墙 pad（= 该网最大 x pad，
    即 demands 锚定 pad），与 escape_landing 网级 gate 的『墙 pad ∩ 网名』
    自关联精确匹配。墙位置全走 SPEC refdes 声明 + 真板解析，代码零坐标。"""
    refs = set((spec.get("capacitor_walls") or {}).get("ac_coupling", {})
               .get("downstream_refs") or [])
    b = BoardParser(str(real_board)).parse()
    out = []
    for p in b.pads:
        if p.footprint_ref not in refs:
            continue
        if not (p.net or "").endswith("_MCIO"):
            continue
        out.append({"net": p.net, "ref": p.footprint_ref,
                    "x": _r3(p.pos[0]), "y": _r3(p.pos[1]),
                    "w": _r3(p.size[0]), "h": _r3(p.size[1])})
    return sorted(out, key=lambda e: e["net"])


def build_config(base_cfg: dict) -> dict:
    """route_model_config.json + 声明段（路径注入，非引擎硬编码）。

    escape_landing 已由 base config 声明 regions（J2/MCIO/U7/U3，D1 多区）+
    band_polarity（D3 极性硬约束）；旧单区键（demands_path/board_edge_x/
    corridor_bound_x）保留为兜底（加性，旧消费路径不破）。"""
    cfg = json.loads(json.dumps(base_cfg))
    ca = cfg.setdefault("channel_alloc", {})
    ca["channels_from_spec"] = True                      # corridors → RouteInput.channels
    ca["nets_path"] = "derived.nets"                     # 待分配网显式声明（18 base 字符串）
    cfg["capacity_audit"] = {
        "demands_path": "derived.capacity_demands",
        "via_zones_path": "derived.via_zones",
        "cap_walls_path": "derived.cap_walls",
    }
    el = cfg.setdefault("escape_landing", {})
    el.setdefault("demands_path", "derived.landing_demands")
    el.setdefault("board_edge_x", 143.0)                 # SPEC board.outline_x[1]
    el.setdefault("corridor_bound_x", 131.5)             # SPEC corridors J2_TO_U.x_range[1]
    return cfg


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 真板 sha（只读核对）
    board_sha = hashlib.sha256(REAL_BOARD.read_bytes()).hexdigest()

    # 2. 权威输入加载
    spec = load(SPEC_PATH)
    escape_spec = load(ESCAPE_PATH)
    rules = load(RULES_PATH)
    base_cfg = load(CONFIG_PATH)

    # 3. 真板 → J2 pad 堆 + 派生段（从真板 + SPEC 生成）
    j2_pads = extract_j2_pads(REAL_BOARD)
    landing_demands = derive_landing_demands(j2_pads)
    # D1 多区（Phase B）：MCIO/U7/U3 区 pad 堆 + 需求（config.escape_landing.
    # regions 声明，derived.* 路径填充）
    region_pads: dict = {}
    region_demands: dict = {}
    for rid in ("J2", "MCIO", "U7", "U3"):
        x_lo, x_hi = REGION_WINDOWS[rid]
        region_pads[rid] = extract_region_pads(REAL_BOARD, x_lo, x_hi, rid)
        region_demands[rid] = derive_region_demands(REAL_BOARD, rid,
                                                    suffix_only=(rid != "J2"))
    corridors = spec.get("corridors") or []
    capacity_demands = derive_capacity_demands(spec, corridors)
    nets = sorted({d["base"] for d in capacity_demands})   # 18 base（去重排序，确定性）
    via_zones = derive_via_zones(spec, escape_spec, j2_pads, REAL_BOARD)
    cap_walls = derive_cap_walls(spec)
    cap_wall_pads_mcio = derive_cap_wall_pads(REAL_BOARD, spec)
    spec["derived"] = {
        "nets": nets,
        "landing_demands": landing_demands,
        "landing_pads": region_pads,
        "landing_demands_J2": region_demands["J2"],
        "landing_demands_MCIO": region_demands["MCIO"],
        "landing_demands_U7": region_demands["U7"],
        "landing_demands_U3": region_demands["U3"],
        "capacity_demands": capacity_demands,
        "via_zones": via_zones,
        "cap_walls": cap_walls,
        "cap_wall_pads_MCIO": cap_wall_pads_mcio,
        "derivation_note": "从真板 k2_v4.kicad_pcb + SPEC 生成（P3-B 组装，引擎零改动）",
    }

    # 4. config 声明段
    config = build_config(base_cfg)

    # 5. route_input：复用 spec_to_route_input + obstacles.pads 覆写为 J2 pad 堆
    ri = spec_to_route_input(spec, escape_spec, j2_pads, config)
    ri.obstacles.pads = list(j2_pads)                    # 逃逸落点域 pad 堆（见 docstring）

    # 6. SolveInput 组装 + 指纹
    inp = SolveInput(route_input=ri, board_path=str(REAL_BOARD),
                     spec=spec, rules=rules, config=config)
    pipe = SolvePipeline(inp)

    # 7. run_all 五阶段（固定序 ①→②→③→④→⑤，硬依赖机器传递）
    ctx = pipe.run_all()

    # 8. 结果落盘（各阶段 dataclass asdict + trace + 缺口记录）
    report = {
        "task_card": "p3_k2_real_board_e2e_card.md",
        "board": {"path": str(REAL_BOARD), "sha256": board_sha,
                  "sha_expected": "6c387dff"},
        "assembly": {
            "route_input": {
                "channels": len(ri.channels),
                "obstacle_segs": len(ri.obstacles.segs),
                "obstacle_vias": len(ri.obstacles.vias),
                "obstacle_pads": len(ri.obstacles.pads),
                "escape_entries": len(ri.escape_entries),
                "source": "spec_to_route_input(SPEC, escape_spec, J2_pads(真板), config)",
            },
            "derived": {
                "landing_demands": len(landing_demands),
                "landing_regions": {rid: {
                    "pads": len(region_pads[rid]),
                    "demands": len(region_demands[rid]),
                } for rid in ("J2", "MCIO", "U7", "U3")},
                "capacity_demands": len(capacity_demands),
                "via_zones": [z["id"] for z in via_zones],
                "cap_walls": cap_walls,
            },
            "config_declared": {
                "capacity_audit": config["capacity_audit"],
                "escape_landing": config["escape_landing"],
                "channel_alloc": config["channel_alloc"],
            },
            "spec": str(SPEC_PATH),
            "rules": str(RULES_PATH),
        },
        "input_fp": pipe.input_fp,
        "stages": {s: asdict(ctx[s]) for s in pipe.STAGES},
        "trace": pipe.trace,
        "gaps": [],
    }

    # 缺口记录：INFEASIBLE 阶段 → reason + evidence（结构化 dict，契约 §4）
    for s in pipe.STAGES:
        out = ctx[s]
        if getattr(out, "verdict", "") == "INFEASIBLE":
            report["gaps"].append({
                "stage": s, "verdict": "INFEASIBLE",
                "reason": f"stage {s} INFEASIBLE",
                "evidence": getattr(out, "evidence", {}),
            })

    # 阶段⑤ 缺口（SolveResult 无 verdict 字段，逐 base 归因）：
    # 16 数据对 = ③→⑤ 数据流断层（channel_alloc 单轨无 seg_tracks vs _track_y_for
    # 段级双廊道；真板 SPEC upper/lower 两廊道轨道偏移 0.4mm，非"完全相同"）
    # 1 REFCLK1 = escape_landing 落点 P/N 相向交叉（已知 skew 缺口同源）
    results = ctx["solve"].results
    base_reasons: dict = {}
    for base, rec in sorted(results.items()):
        if rec.get("status") != "SOLVED":
            seg_reasons = [{"segname": s.get("name"), "status": s.get("status"),
                            "reason": s.get("reason")}
                           for s in rec.get("segments", [])]
            base_reasons[base] = {"status": rec.get("status"),
                                  "segments": seg_reasons}
    u_to_mcio_broken = sorted(b for b, r in base_reasons.items()
                              if any(x.get("status") == "INFRA_ERROR"
                                     and "无通道分配" in (x.get("reason") or "")
                                     and "U_TO_MCIO" in (x.get("reason") or "")
                                     for x in r["segments"]))
    # P/N 相向交叉归因（Phase B）：区分落点驱动（D1/D3 已闭环，fail-closed 可归因）
    # vs 芯片侧左逃逸自搜（层4 形态卡边界，D4 触发条件 (a)——landing 已提供且
    # polarity_consistent=true 仍报交叉 → _escape_pair 形态缺口）
    landing_cross = [b for b, r in base_reasons.items()
                     if any("落点驱动逃逸 P/N 相向交叉" in (x.get("reason") or "")
                            for x in r["segments"])]
    selfsearch_cross = [b for b, r in base_reasons.items()
                        if any("相向交叉" in (x.get("reason") or "")
                               and "落点驱动逃逸" not in (x.get("reason") or "")
                               for x in r["segments"])]
    if u_to_mcio_broken:
        report["gaps"].append({
            "stage": "solve", "verdict": "INFEASIBLE",
            "reason": "阶段③→⑤ 数据流断层：channel_alloc 产物每网单 track_y（落 J2_TO_U 带内），"
                      "无 seg_tracks；hs_route_model._track_y_for 假定两廊道 bands 完全相同直接复用，"
                      "但真板 SPEC upper/lower 两廊道轨道偏移 0.4mm（J2_TO_U 40.3/58.3… vs "
                      "U_TO_MCIO 40.7/58.7…）→ 段在 U_TO_MCIO 全部无通道分配（INFRA_ERROR）",
            "evidence": {
                "bases_affected": u_to_mcio_broken,
                "count": len(u_to_mcio_broken),
                "offset_mm": 0.4,
                "j2_to_u_upper_tracks": [40.3, 41.5, 42.7, 43.9, 45.1, 46.3, 47.5, 48.7],
                "u_to_mcio_upper_tracks": [40.7, 41.9, 43.1, 44.3, 45.5, 46.7, 47.9, 49.1],
                "refclk_tracks_identical": [45.7, 50.5],
                "root": "channel_alloc 无 seg_tracks 产出（M13 v5 曾有，现版本无）；"
                        "回上层 ECO：③ 需产出段级 seg_tracks 或 _track_y_for 按廊道独立解析",
            },
        })
    if landing_cross:
        report["gaps"].append({
            "stage": "solve", "verdict": "INFEASIBLE",
            "reason": "落点驱动逃逸 P/N 相向交叉（landing 已提供且 polarity_consistent="
                      "true 仍交叉）——落点 fail-closed 证据可归因（D1/D3 已闭环，"
                      "剩余属落点几何/层4 消费边界）",
            "evidence": {
                "bases_affected": landing_cross,
                "cross_evidence": next(
                    (x for r in base_reasons.values()
                     for x in r["segments"]
                     if x.get("status") == "INFEASIBLE"
                     and "落点驱动逃逸 P/N 相向交叉" in (x.get("reason") or "")),
                    None),
                "root": "落点 fail-closed 证据（非 landing 缺口）：落点几何消费边界，"
                        "D4 触发条件 (a) 候选",
            },
        })
    if selfsearch_cross:
        report["gaps"].append({
            "stage": "solve", "verdict": "INFEASIBLE",
            "reason": "芯片侧左逃逸自搜 P/N 相向交叉（landing 已提供且 polarity_consistent="
                      "true，solve 仍报『对级对称逃逸无净空/via 换层 P/N 极性不一致』）——"
                      "层4 形态卡边界（D4 触发条件 (a)：_escape_pair 形态缺口，本卡不做）",
            "evidence": {
                "bases_affected": selfsearch_cross,
                "root": "层4 引擎形态卡（D4 触发条件 (a)），Phase C 重跑后按 D4 另卡处理",
            },
        })
    # 阶段⑤ C3 归因：走廊段无净空窗口（D2 段廊道窗口验证闭环后应消失）
    c3_segments = sorted(
        (b, x.get("segname"), x.get("reason"))
        for b, r in base_reasons.items()
        for x in r["segments"]
        if "走廊段无净空窗口" in (x.get("reason") or ""))
    if c3_segments:
        report["gaps"].append({
            "stage": "solve", "verdict": "INFEASIBLE",
            "reason": "走廊段无净空窗口（通道 y 被低速/引脚占位）——alloc 段廊道窗口验证未覆盖",
            "evidence": {"segments": [
                {"base": b, "segname": s, "reason": rn}
                for b, s, rn in c3_segments]},
        })
    # 阶段⑤ 逃逸/形态归因（非 C3）——Phase B（D1 多区 + D3 极性硬约束）验收证据：
    #   C1「对级对称逃逸无净空」/ C2「via 换层 P/N 极性不一致」自搜 reason 应归零
    #   （或仅余落点驱动逃逸 fail-closed 落点证据可归因）；C4「短段直连」= 层4
    #   形态卡边界（D4 触发条件，本卡不做）。
    esc_segments = sorted(
        (b, x.get("segname"), x.get("reason"))
        for b, r in base_reasons.items()
        for x in r["segments"]
        if x.get("status") == "INFEASIBLE"
        and "走廊段无净空窗口" not in (x.get("reason") or ""))
    c1_c2_segments = [(b, s, rn) for b, s, rn in esc_segments
                      if any(k in (rn or "") for k in
                             ("对级对称逃逸无净空", "via 换层 P/N 极性不一致"))]
    landing_driven = [(b, s, rn) for b, s, rn in esc_segments
                      if any(k in (rn or "") for k in
                             ("落点驱动逃逸", "落点净空校验失败"))]
    c4_short = [(b, s, rn) for b, s, rn in esc_segments
                if "短段直连无净空" in (rn or "")]
    if esc_segments:
        report["gaps"].append({
            "stage": "solve", "verdict": "INFEASIBLE",
            "reason": "逃逸/形态段 INFEASIBLE——Phase B 验收归因：C1/C2 自搜 reason "
                      "归零证据 + 落点 fail-closed 可归因 + 层4 形态边界（D4 触发）",
            "evidence": {
                "segments": [{"base": b, "segname": s, "reason": rn}
                             for b, s, rn in esc_segments],
                "c1_c2_count": len(c1_c2_segments),
                "c1_c2_segments": [{"base": b, "segname": s}
                                   for b, s, _ in c1_c2_segments],
                "landing_driven_count": len(landing_driven),
                "landing_driven_segments": [{"base": b, "segname": s}
                                            for b, s, _ in landing_driven],
                "c4_short_count": len(c4_short),
                "c4_short_segments": [{"base": b, "segname": s}
                                      for b, s, _ in c4_short],
                "c3_eliminated": not c3_segments,
                "phase_b": {"d1_multi_region": True, "d3_polarity_hard": True,
                            "layer4_form_boundary": "D4 触发条件，另卡处理"},
            },
        })
    if base_reasons:
        report["solve_base_reasons"] = base_reasons

    # 子模块漂移缺口（k2/_shared 陈旧快照，已按 handoff 用容器 _shared）
    report["gaps"].append({
        "stage": "env", "verdict": "WARN",
        "reason": "k2/_shared 子模块(84b613d)落后容器 _shared(b48d3f4)：前者 hs_route_model 无 "
                  "landing 参数、solve_pipeline 3 桩。运行以容器 _shared 为真源（handoff §1 口径）",
        "evidence": {"k2_shared_head": "84b613d", "container_shared_head": "b48d3f4"},
    })

    # 数据形状错配缺口：SPEC band.nets 列表 vs ChannelInput.nets str（_alloc_nets 字符串化列表）。
    # 本卡以 nets_path 显式声明规避（契约层机制）；形状修正确认归属回上层 ECO，细节见 report.gaps。
    report["gaps"].append({
        "stage": "env", "verdict": "WARN",
        "reason": "SPEC corridors band.nets 为列表 vs ChannelInput.nets 声明 str："
                  "_alloc_nets 会把列表字符串化成伪网名（首跑 alloc 3 伪网全 INFEASIBLE）。"
                  "本卡经 nets_path 显式声明规避，底层形状错配记录回上层 ECO",
        "evidence": {
            "first_run_nets": ["['PCIE_DN0', 'PCIE_DN1', ...]", "['PCIE_REFCLK']",
                               "['PCIE_UP0', ...]"],
            "channel_input_nets_type": "list (SPEC band.nets)",
            "declared_field_type": "str",
            "workaround": "config.channel_alloc.nets_path -> derived.nets (18 base 字符串)",
        },
    })

    out_path = OUT_DIR / "p3_real_board_e2e_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False, sort_keys=True)

    # 摘要（stdout）
    print("=" * 68)
    print("P3-B K2 真板端到端 run_all 摘要")
    print("=" * 68)
    print(f"board sha256 : {board_sha} (expect 6c387dff...)")
    print(f"input_fp     : {pipe.input_fp}")
    for s in pipe.STAGES:
        out = ctx[s]
        keys = {k: getattr(out, k, None) for k in
                ("verdict", "resource_ok", "polarity_ok", "solved",
                 "infeasible", "bottleneck_stage", "solved_pairs")}
        print(f"[{s:>11}] {json.dumps({k: v for k, v in keys.items() if v is not None}, sort_keys=True)}")
    # Phase B 验收证据：landing 多区记录 + 极性硬约束摘要（stages.landing.evidence）
    lnd_ev = getattr(ctx["landing"], "evidence", {})
    print(f"landing regions: {json.dumps({k: {'verdict': v.get('verdict'), 'n_assigned': v.get('n_assigned'), 'used': v.get('used'), 'unassigned': v.get('unassigned')} for k, v in (lnd_ev.get('regions') or {}).items()}, sort_keys=True, ensure_ascii=False)}")
    print(f"landing polarity: {json.dumps(lnd_ev.get('polarity'), sort_keys=True)}")
    print(f"trace        : {json.dumps(pipe.trace, sort_keys=True)}")
    print(f"report       : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
