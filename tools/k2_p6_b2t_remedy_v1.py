#!/usr/bin/env python3
"""k2_p6_b2t_remedy_v1.py — B2-T 13 项失败的**处置草案（甲 重基线 / 乙 具名退役）**生成器（只读）。

做法：① 在影子框架 `/tmp/opencode/shadow_b3` 上跑一次 `test_hs_route_model.py` 取**当前失败清单**；
② 只读**测量现行真源量**（走廊 x_range/bands、capacity regions、DN0 pad x 与走廊命中、solve_all_v4 解数、
   link_topology 交叉集、corridor_clear_span、probe_region_capacity）；③ 与**人工-authored 处置表**合并 ⇒ 机读件。
真源零改动（影子在 /tmp；本器只读 + 只写 --out）。

用法（容器根 ic_hw；需先由 k2_p6_shadow_verify_v1.py 生成影子）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p6_b2t_remedy_v1.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(REPO, "k2")
SH = "/tmp/opencode/shadow_b3"
DEF_OUT = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "P6_execution", "B2T_REMEDY_OPTIONS_v1.json")
TEST = os.path.join(SH, "shared/eda_core/tests/test_hs_route_model.py")

# 人工-authored 处置表（键 = 用例名）。甲=重基线草案（新期望 + 期望值来源）；乙=具名退役理由。
OPTIONS = {
 "test_probe_escape_capacity_dn0": {
   "jia": {"new_expect": "status ∈ ('SOLVED','BLOCKED','NO_CORRIDOR')",
           "source": "走廊覆盖几何：DN0 pad x=84.85 ∉ 走廊 [65.05,82.35]∪[105.25,132.65] ⇒ NO_CORRIDOR 是**合法**结论"},
   "yi": "旧代际探针期望（pad 必落某走廊）；现几何下不适用"},
 "test_probe_reports_via_gap_fact": {
   "jia": {"new_expect": "仅在 status≠NO_CORRIDOR 时校验 ends/边距事实；否则断言 ends 缺省契约",
           "source": "同上（该用例与 ① 同源）"},
   "yi": "同上；其物理事实（pn_via_edge=0.05）属旧几何"},
 "test_capacity_regions_derived": {
   "jia": {"new_expect": "regions == {'J2_region','MCIO_region'}（或经 ENG 论证后补 pin_region 推导）",
           "source": "`m._capacity_regions()` 实测 = ['J2_region','MCIO_region']（当前数据驱动推导）"},
   "yi": "期望的 U7/U3 pin_region 源自旧代际器件名/分段命名"},
 "test_capacity_map_persist": {
   "jia": {"new_expect": "len(regions) == 实测值（当前 2）；corridors 数亦按实测",
           "source": "同 ③"},
   "yi": "同 ③（4 区域/6 走廊为旧代际）"},
 "test_probe_region_capacity_structure": {
   "jia": {"new_expect": "status ∈ ('CAPACITY_OK','INSUFFICIENT')",
           "source": "独立测量：同形 region 实测 INSUFFICIENT（测试内构造仍 INFRA_ERROR ⇒ 需 ENG 定性差异）"},
   "yi": "旧代际 region 契约（含 U7 段）"},
 "test_corridor_clear_span": {
   "jia": {"new_expect": "span == x_range（无器件缩进）",
           "source": "实测 span == x_range（105.25,132.65 / 65.05,82.35）"},
   "yi": "期望的 U7/U3 器件缩进属旧代际布局"},
 "test_chain_no_pn_zero_spacing": {
   "jia": {"new_expect": "REFCLK0 链 status 允许 INFEASIBLE（并记录原因）",
           "source": "实测 solve_chain_v4('REFCLK0') = INFEASIBLE"},
   "yi": "旧代际可解性假设"},
 "test_flip_polarity_cross_rejected": {
   "jia": {"new_expect": "无（`_escape_pair` 在当前几何参数下返回 None）",
           "source": "实测 TypeError: NoneType not subscriptable（入参依赖旧代际走廊/轨道）"},
   "yi": "该用例证据锚点 = 旧事故点 (64.317,49.077)，属旧代际场景"},
 "test_drawing_only_refuses_no_node": {
   "jia": {"new_expect": "同上（返回 None ⇒ 无节点语义变化）",
           "source": "同上"},
   "yi": "同上（drawing_only 红线用例需按现行逃逸域重写）"},
 "test_correct_polarity_solves_clean": {
   "jia": {"new_expect": "DN4 段 SOLVED 前提在当前几何不成立",
           "source": "实测同族链 INFEASIBLE/None"},
   "yi": "旧代际正极性可解假设"},
 "test_escape_deterministic_byte_identical": {
   "jia": {"new_expect": "确定性断言改在**现行可解输入**上重写",
           "source": "当前入参不可解 ⇒ 无输出可比较"},
   "yi": "同上；确定性属**性质**，建议以新输入保留该性质（优先重写而非退役）"},
 "test_board_level_consistency": {
   "jia": {"new_expect": "以**现行真源可解子集**为对象（当前 8L 板：18 链 0 解）",
           "source": "实测 solve_all_v4: n_solved=0/18（bases 取自翻译后 alloc 的 PCIE_*）"},
   "yi": "整板一致性为**重要**性质；建议保留并改为「以现行真源生成输入」而非退役"},
 "test_link_topology_crossing_old_topology": {
   "jia": {"new_expect": "crossing_links == ['UP4','UP5','UP6','UP7']（4 对）",
           "source": "实测 link_topology_map: verdict=CROSSING_FOUND, crossing=['UP4','UP5','UP6','UP7'], links=18"},
   "yi": "期望的 8 对（UP4-7+DN0-3）属旧代际拓扑判定"},
}


def measure() -> dict:
    sys.path.insert(0, os.path.join(SH, "shared"))
    from eda_core.hs_route_model import HSRouteModel, pair_endpoints
    alloc = "/tmp/opencode/legacy_alloc_translated.json"
    m = HSRouteModel(f"{K2}/k2_v4_8L.kicad_pcb", f"{K2}/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json",
                     alloc, f"{REPO}/_shared/eda_core/drc_rules.json", pro_path=f"{K2}/k2_v4_8L.kicad_pro")
    px = pair_endpoints(m.board, "PCIE_DN0_P", "PCIE_DN0_N")["P"][0]["pos"][0]
    alloc_recs = json.load(open(alloc, encoding="utf-8"))["alloc"]
    bases = sorted(k for k in alloc_recs if k.startswith("PCIE_"))
    solved = [k for k, r in m.solve_all_v4(bases)["results"].items() if r.get("status") == "SOLVED"]
    topo = m.link_topology_map()
    return {
        "corridors": [{"id": c.get("id"), "x_range": c.get("x_range")} for c in m.spec["corridors"]],
        "capacity_regions": sorted(r["id"] for r in m._capacity_regions()),
        "dn0": {"pad_x": px, "corridor_for_x": m._corridor_for_x(px, px)},
        "solve_all_v4": {"n_bases": len(bases), "n_solved": len(solved)},
        "link_topology": {"verdict": topo.get("verdict"), "crossing": sorted(topo.get("crossing_links") or []),
                          "n_links": len(topo.get("links") or {})},
        "corridor_clear_span": {c["id"]: list(m._corridor_clear_span(c)) for c in m.spec["corridors"]},
    }


def failures() -> list:
    if not os.path.isfile(TEST):
        return []
    env = {k: v for k, v in os.environ.items() if k != "PM_GATE_PROJECT_ROOT"}
    env["PYTHONPATH"] = os.path.join(SH, "shared")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rf", "-p", "no:cacheprovider", TEST],
                          cwd=REPO, capture_output=True, text=True, env=env, timeout=3600)
    names = re.findall(r"^FAILED \S+::(?:\w+::)?(\w+)", proc.stdout, re.M)
    counts = re.search(r"(?:(\d+) failed, )?(\d+) passed(?:, (\d+) skipped)?", proc.stdout)
    return {"names": sorted(set(names)),
            "counts": {"failed": int(counts.group(1) or 0) if counts else None,
                       "passed": int(counts.group(2)) if counts else None,
                       "skipped": int(counts.group(3) or 0) if counts else None}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEF_OUT)
    args = ap.parse_args()
    f = failures() if os.path.isdir(SH) else {"names": [], "counts": {}}
    doc = {
        "artifact": "k2_p6_b2t_remedy_options", "schema": 1, "readonly": True,
        "context": "B2-T 13 项隐藏失败的处置草案；**命名同步不足已由实验证明**（见 B2T-EXPERIMENT 件）",
        "shadow": SH, "shadow_failure_counts": f.get("counts", {}),
        "shadow_failures": f.get("names", []),
        "measurements_current_truth": measure(),
        "options": OPTIONS,
        "option_coverage": {"measured_items": len(OPTIONS), "shadow_failures": len(f.get("names", []))},
        "note": "甲=重基线（新期望 + 期望值来源）；乙=具名退役（禁静默 skip）。**裁量权归监理**；ENG 不擅自改期望（C-12）。",
    }
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("shadow failures:", doc["shadow_failure_counts"], "| 处置表覆盖:", len(OPTIONS))
    print("→", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
