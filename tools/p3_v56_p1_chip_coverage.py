#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""P3 v56 P1 — 芯片侧 landing 覆盖工件 + 机器验收谓词（独立于求解管道）。

P1 = 数据形状/覆盖（图纸输入无歧义），消费接线（chip_landing → solve）留 P2。
本工具产出 spec.derived 之外的独立工件（P2 接线输入）+ 谓词机检：
  P-① 无 nets_path 覆写（config.channel_alloc 断言）；引擎 _alloc_nets 已统一
      band.nets(list) 契约 + 伪网名 fail-closed（引擎单测覆盖）。
  P-② pad 归属不相交 + 闭包完备：真板 PCIE/REFCLK pad 按 ref 分类
      (U6→chip 域 EAST/WEST by alloc corridor；J2/J3/J4/C*→连接器域)，
      每 pad 恰一域（重复/遗漏即 raise）。
  P-③ U3/U7 region corridor 锚：config 声明非空且 ∈ SPEC corridors。
  P-④ 芯片域 landing 试分配（escape_landing.allocate_regions，管道外）：
      U3(EAST)/U7(WEST) 各自 assigned>0（或带守恒证据的 NO_ESCAPE 归因）。

引擎零改动；真板只读；全前台零委派。输出 m13_v56_p1_chip_coverage.json。
"""
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SHARED = Path("/home/fila/jqdDev_2025/ic_hw/_shared")
sys.path.insert(0, str(SHARED))

sp = importlib.util.spec_from_file_location(
    "e2e", str(REPO / "tools" / "p3_k2_real_board_e2e.py"))
m = importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)

from eda_core.drc_rules import BoardParser                    # noqa: E402
from eda_core.escape_landing import (                        # noqa: E402
    EscapeLandingAllocator, LandingRules, landing_regions_from_config)
from eda_core.route_input import spec_to_route_input         # noqa: E402
from eda_core.solve_pipeline import SolveInput, SolvePipeline  # noqa: E402

ART = REPO / "pm_gate" / "artifacts" / "k2_v4"
L2, L3 = ART / "L2", ART / "L3"
REAL_BOARD = REPO / "k2_v4.kicad_pcb"
CFG_PATH = L2 / "route_model_config.json"
OUT = L3 / "mcio_feas_step2" / "m13_v56_p1_chip_coverage.json"


def alloc_key(net: str) -> str:
    n = net
    for suf in ("_J2", "_MCIO", "_U3", "_U4"):
        if n.endswith(suf):
            n = n[:-len(suf)]
            break
    for suf in ("_P", "_N"):
        if n.endswith(suf):
            return n[:-2]
    return n


def pol_of(net: str) -> str:
    return "P" if "_P" in net else "N"


def corridor_of(key: str) -> str:
    k = key.replace("PCIE_", "")
    if k.startswith("UP_OUT"):
        return "EAST_CHIP_TO_J2"
    if k.startswith("UP"):
        return "WEST_MCIO_TO_CHIP"
    if k.startswith("DN_OUT"):
        return "WEST_MCIO_TO_CHIP"
    if k.startswith("DN"):
        return "EAST_CHIP_TO_J2"
    if k.startswith("REFCLK"):
        return "EAST_CHIP_TO_J2"
    raise ValueError(f"unknown alloc key {key}")


def to_pad(p) -> dict:
    return {"net": p.net, "ref": p.footprint_ref,
            "x": round(float(p.pos[0]), 3), "y": round(float(p.pos[1]), 3),
            "w": round(float(p.size[0]), 3), "h": round(float(p.size[1]), 3),
            "tht": p.is_tht, "layers": list(p.layers)}


def build_region_demands(pads):
    by_key = defaultdict(dict)
    for p in pads:
        by_key[alloc_key(p["net"])][pol_of(p["net"])] = p
    dems = []
    for key in sorted(by_key):
        rec = by_key[key]
        if "P" not in rec or "N" not in rec:
            continue
        dems.append({"base": key, "segname": "chip",
                     "net_p": rec["P"]["net"], "net_n": rec["N"]["net"],
                     "pad_p": [rec["P"]["x"], rec["P"]["y"]],
                     "pad_n": [rec["N"]["x"], rec["N"]["y"]]})
    return dems


def main() -> int:
    spec = json.load(open(L3 / "SPEC_k2_v4.json"))
    escape_spec = json.load(open(L2 / "escape_spec.json"))
    rules = json.load(open(SHARED / "eda_core" / "drc_rules.json"))
    base_cfg = json.load(open(CFG_PATH))
    config = m.build_config(base_cfg)

    pred = {}

    # P-① 无 nets_path 覆写
    pred["P1_no_nets_path_override"] = (
        "nets_path" not in (config.get("channel_alloc") or {}))

    # P-③ region corridor 锚（正式 config 声明）
    spec_corrs = {c["id"] for c in spec.get("corridors", [])}
    anchors = {}
    for rc in (config.get("escape_landing") or {}).get("regions", []):
        if rc.get("id") in ("U3", "U7"):
            cid = rc.get("corridor_id")
            anchors[rc["id"]] = {"corridor_id": cid,
                                 "valid": cid in spec_corrs,
                                 "side": rc.get("side"),
                                 "board_edge_x": rc.get("board_edge_x"),
                                 "corridor_bound_x": rc.get("corridor_bound_x")}
    pred["P3_region_corridor_anchors"] = (
        len(anchors) == 2 and all(v["valid"] for v in anchors.values()))

    # ── 装配（复刻 e2e main 前段，取 alloc）────────────
    j2_pads = m.extract_j2_pads(REAL_BOARD)
    landing_demands = m.derive_landing_demands(j2_pads)
    corridors = spec.get("corridors") or []
    capacity_demands = m.derive_capacity_demands(spec, corridors, escape_spec,
                                                 config)
    via_zones = m.derive_via_zones(spec, escape_spec, j2_pads, REAL_BOARD)
    cap_walls = m.derive_cap_walls(spec)
    cap_wall_pads_mcio = m.derive_cap_wall_pads(REAL_BOARD, spec)
    spec["derived"] = {
        "nets": sorted({d["base"] for d in capacity_demands}),
        "landing_demands": landing_demands,
        "landing_demands_J2": m.derive_region_demands(REAL_BOARD, "J2", False),
        "landing_demands_MCIO": m.derive_region_demands(REAL_BOARD, "MCIO",
                                                        True),
        "capacity_demands": capacity_demands,
        "via_zones": via_zones, "cap_walls": cap_walls,
        "cap_wall_pads_MCIO": cap_wall_pads_mcio,
    }
    ri = spec_to_route_input(spec, escape_spec, j2_pads, config)
    ri.obstacles.pads = list(j2_pads)
    inp = SolveInput(route_input=ri, board_path=str(REAL_BOARD),
                     spec=spec, rules=rules, config=config)
    pipe = SolvePipeline(inp)
    cap = pipe.run_capacity()
    alloc_t = pipe.run_alloc(cap)
    alloc = alloc_t.alloc

    # ── P-② 真板 pad 归属分区（闭包 + 不相交）──────────
    b = BoardParser(str(REAL_BOARD)).parse()
    sig = [to_pad(p) for p in b.pads
           if (p.net or "").startswith(("PCIE", "REFCLK"))]
    classes = defaultdict(int)
    chip_domains = {"EAST_CHIP_TO_J2": [], "WEST_MCIO_TO_CHIP": []}
    for p in sig:
        if p["ref"] == "U6":
            corr = corridor_of(alloc_key(p["net"]))
            chip_domains[corr].append(p)
            classes["chip:" + corr] += 1
        elif p["ref"] == "J2":
            classes["conn:J2"] += 1
        elif p["ref"] in ("J3", "J4"):
            classes["conn:J3_J4"] += 1
        elif p["ref"].startswith("C"):
            classes["cap_wall"] += 1
        else:
            classes["UNCLASSIFIED:" + str(p["ref"])] += 1
            raise AssertionError(
                f"pad 归属遗漏: {p['ref']} {p['net']} (x={p['x']},y={p['y']})")
    n_unclassified = sum(v for k, v in classes.items()
                         if k.startswith("UNCLASSIFIED"))
    pred["P2_disjoint_no_unclassified"] = n_unclassified == 0

    def closure_check(pads):
        by_key = defaultdict(set)
        for p in pads:
            by_key[alloc_key(p["net"])].add(pol_of(p["net"]))
        keys = sorted(k for k, v in by_key.items() if v == {"P", "N"})
        return keys, sorted(by_key)

    east_keys, east_all = closure_check(chip_domains["EAST_CHIP_TO_J2"])
    west_keys, west_all = closure_check(chip_domains["WEST_MCIO_TO_CHIP"])
    expect_east = sorted(k for k in alloc if alloc[k]["corridor"]
                         == "EAST_CHIP_TO_J2" and not k.startswith("PCIE_REFCLK"))
    expect_west = sorted(k for k in alloc if alloc[k]["corridor"]
                         == "WEST_MCIO_TO_CHIP")
    chip_keys = set(east_keys) | set(west_keys)
    pad_keys = set(east_all) | set(west_all)
    pred["P2_chip_domain_pairs_complete"] = (
        chip_keys == set(expect_east) | set(expect_west))
    pred["P2_no_partial_pairs"] = (set(east_all) == set(east_keys)
                                   and set(west_all) == set(west_keys))
    dup = {k for k in set(east_all) & set(west_all)}
    pred["P2_no_domain_duplicate"] = not dup

    # ── P-④ 芯片域 landing 试分配（管道外，独立命名空间）──
    u6_all = [to_pad(p) for p in b.pads if p.footprint_ref == "U6"]
    # alloc 机器富化（与 solve_pipeline landing_regions_from_config 同语义：
    # demand.base → alloc key → track_y/band/corridor）
    def enrich(demands):
        for d in demands:
            rec = alloc.get(d["base"]) or alloc.get(d.get("net_p"))
            d["track_y"] = (rec.get("track_y") if rec else None)
            d["band"] = rec.get("band") if rec else None
            d["corridor"] = rec.get("corridor") if rec else None
        return demands

    chip_regions_cfg = [
        {"id": "U3", "kind": "CHIP", "side": "RIGHT",
         "corridor_id": "EAST_CHIP_TO_J2", "corridor_bound_x": 96.0,
         "board_edge_x": 96.0, "pads": u6_all,
         "demands": enrich(build_region_demands(chip_domains["EAST_CHIP_TO_J2"]))},
        {"id": "U7", "kind": "CHIP", "side": "LEFT",
         "corridor_id": "WEST_MCIO_TO_CHIP", "corridor_bound_x": 96.0,
         "board_edge_x": 96.0, "pads": u6_all,
         "demands": enrich(build_region_demands(chip_domains["WEST_MCIO_TO_CHIP"]))},
    ]
    rules_lib = LandingRules.from_sources(config, rules)
    raw = EscapeLandingAllocator(rules_lib).allocate_regions(
        chip_regions_cfg, spec=spec, config=config)
    reg_ev = raw.get("regions") or {}
    chip_assigned = {}
    for rid, ev in sorted(reg_ev.items()):
        chip_assigned[rid] = {
            "corridor_id": ev.get("corridor_id"),
            "n_signals": ev.get("n_signals"),
            "n_assigned": ev.get("n_assigned"),
            "unassigned": ev.get("unassigned"),
            "verdict": ev.get("verdict"),
        }
    pred["P4_U3_U7_assigned_gt0"] = (
        chip_assigned.get("U3", {}).get("n_assigned", 0) > 0
        and chip_assigned.get("U7", {}).get("n_assigned", 0) > 0)

    row_coverage = {}
    for net, rec in sorted((raw.get("allocation") or {}).items()):
        lnd = (rec.get("landing") or {})
        row_coverage[net] = {"region": rec.get("region"),
                             "status": rec.get("status"),
                             "x": lnd.get("x"), "y": lnd.get("y")}

    report = {
        "artifact": "m13_v56_p1_chip_coverage",
        "phase": "P1 数据形状/覆盖（v56 plan P1，方案 A：管道外工件，消费接线 P2）",
        "engine": "container _shared pristine f15b03e + P1 E1 契约改动（route_input/"
                  "solve_pipeline，见引擎 commit）",
        "board_sha256": m.hashlib.sha256(REAL_BOARD.read_bytes()).hexdigest(),
        "predicates": pred,
        "chip_domains": {
            "U3_EAST": {"corridor": "EAST_CHIP_TO_J2",
                        "keys": east_keys, "pads": len(chip_domains["EAST_CHIP_TO_J2"])},
            "U7_WEST": {"corridor": "WEST_MCIO_TO_CHIP",
                        "keys": west_keys, "pads": len(chip_domains["WEST_MCIO_TO_CHIP"])},
        },
        "pad_classification": dict(classes),
        "landing_regions": chip_assigned,
        "landing_rows": row_coverage,
        "pipeline_parity_note": "本工件独立于求解管道；管道 landing 仍只含连接器域"
                                "（J2/MCIO），solve 失败集 == P0 基线（不因 P1 平移），"
                                "见 e2e report 双跑比对",
        "p2_consumption": "P2 把本工件 chip_domains 域 rows 接成 chip_landing 命名空间"
                          "喂 solve；NO_ESCAPE（DN_OUT 西侧）移交 P3/P4 守恒级容量",
    }
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    print(json.dumps({"predicates": pred, "chip_assigned": chip_assigned},
                     indent=1, ensure_ascii=False, sort_keys=True))
    print("artifact:", OUT)
    ok = all(v is True for v in pred.values())
    print("P1 机器验收谓词:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
