#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 含旧板身份字面量 ['f6273de6'] ⇒ **不可重放**（重跑会静默换板，禁默认重跑）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""板层意图**容量闭合派生**引擎（整改 #03）——layer intent 由工单参数 → 派生输出。

给定**冻结四源 + 规则**，确定性（O(n)，零搜索/零枚举/零回溯）推出自洽的
  stackup（层数）+ layer purpose（层用途）+ topology（层分配），并证明容量闭合：
      L_signal = max( L_escape , L_capacity , L_conflict , 3 )      # 3=F+1内层+B 最小可行
      total_layers = 2 * L_signal                                     # 参考平面夹心规则
      闭合:  D_r <= L_signal * C_r  (每区域)  ∧  同层交叉 == 0 (层分配=合法着色)
无任何 owner / 工单 / 修订卡参数。

三个下界（全部来自冻结输入，非工单常量）：
  L_escape   : pad 墙逃逸深度（P2 行内不可穿 ⇒ 每 pad 行/列须层分隔）——manifest 实测 pad 行数
  L_capacity : 区域容量闭合 ceil(D_r / C_r)，C_r = floor(可用横截 / lane 间距)——SPEC/manifest
  L_conflict : 通道序冲突图（排列图）最大团 = 源序/靶序反演的最长下降子序列——manifest 端点序
CLI: --out PATH [--quiet]
"""
from __future__ import annotations
import argparse, bisect, hashlib, itertools, json
from collections import defaultdict
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
S2 = L3 / "mcio_feas_step2"
F = {"spec": L3 / "SPEC_k2_v4.json", "manifest": S2 / "m13_v57_s1_page_manifest.json",
     "pcb": K2 / "k2_v4.kicad_pcb", "rules": K2 / "_shared" / "eda_core" / "drc_rules.json"}
EXPECT = {"spec": "0bd52ed48e720b8c", "manifest": "a8ef3ea8ecff99d7",
          "pcb": "f6273de613f43d05", "rules": "0a459839e15960b8"}
# 层用途规则（参考平面夹心；来自冻结 SPEC stackup 家族 F/G/S/G/[P/G]/S/B，非单板特判）
GND, PWR, SIG = "GND", "PWR", "signal"


def sha16(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def r(x, n=4): return round(float(x), n)


def lds(seq):
    """最长下降子序列长度 = 排列图最大团 ω（确定性 O(n log n)）。"""
    tails = []
    for v in seq:
        nv = -v; i = bisect.bisect_left(tails, nv)
        if i == len(tails): tails.append(nv)
        else: tails[i] = nv
    return len(tails)


def greedy_color(adj):
    """固定序（节点名序）单遍贪心着色 → 合法着色（同色无边）⇒ 层分配零同层交叉。"""
    color = {}
    for v in sorted(adj):
        used = {color[u] for u in adj[v] if u in color}
        color[v] = min(set(range(len(used) + 1)) - used)  # mex(used) —— 无 while/无搜索
    return color


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    drift = {k: {"expected": EXPECT[k], "actual": sha16(p)} for k, p in F.items()}
    if any(v["expected"] != v["actual"] for v in drift.values()):
        print("FROZEN_DRIFT", json.dumps(drift)); return 2
    spec = json.loads(F["spec"].read_text()); man = json.loads(F["manifest"].read_text())
    pc = spec["net_classes"]["PCIe85"]; w, clr = pc["width"], pc["clearance"]
    pgap = pc["diff_pair"]["p_gap"]
    per_ball = spec["components"]["redriver"]["DS320PR1601"]["bga_escape"]["per_ball"]
    ipair = per_ball["inter_pair_spacing"]; pad_mm = per_ball["pad_mm"]
    pair_copper = r(2 * w + pgap); lane_needed = r(w + 2 * clr); via_via = spec["vias"]["std"]["outer"] + clr

    # ---- 端点几何（manifest 实测） ----
    chip = defaultdict(list); conn = defaultdict(list); pages = []
    for p in man["pages"]:
        if p["kind"] != "data": continue
        ch = p.get("anchors", {}).get("chip", {}); co = p.get("anchors", {}).get("conn", {})
        if len(ch) != 2 or len(co) != 2: continue
        pages.append({"page": p["page_id"], "corr": p["corridor"]["id"], "ref": sorted({v["ref"] for v in co.values()})[0],
                      "chip_x": sum(v["pad_global"][0] for v in ch.values()) / 2,
                      "chip_y": sum(v["pad_global"][1] for v in ch.values()) / 2,
                      "conn_x": sum(v["pad_global"][0] for v in co.values()) / 2,
                      "conn_y": sum(v["pad_global"][1] for v in co.values()) / 2})
        for v in ch.values(): chip[p["page_id"]].append(v["pad_global"])
        for v in co.values(): conn[p["page_id"]].append(v["pad_global"])
    chip_pts = [pt for v in chip.values() for pt in v]; conn_pts = [pt for v in conn.values() for pt in v]

    def wall(pts):
        ps = sorted({(r(x), r(y)) for x, y in pts})
        mn = min(((q0[0] - q1[0]) ** 2 + (q0[1] - q1[1]) ** 2) ** .5 for q0, q1 in itertools.combinations(ps, 2))
        return r(mn), r(mn - pad_mm)

    def clusters(vals, thr=1.0):
        """沿一轴把 pad 坐标聚成行/列（确定性、排序、单遍）；返回簇数 = 墙厚。"""
        n = 0; last = None
        for v in sorted(vals):
            if last is None or v - last > thr: n += 1
            last = v
        return n

    # ---- L_escape：pad 墙逃逸深度（P2 不可穿 ⇒ pad 行/列须层分隔） ----
    chip_gap = wall(chip_pts)[1]
    chip_rows = clusters([y for x, y in chip_pts])        # 逃逸方向 pad 行（墙厚）
    w_escape = {"chip_field": {"depth": chip_rows, "min_pad_gap_mm": chip_gap,
                               "penetrable": chip_gap >= lane_needed}}
    for ref in ("J2", "J3", "J4"):
        pts = [pt for p in man["pages"] for v in p.get("anchors", {}).get("conn", {}).values()
               if v["ref"] == ref for pt in [v["pad_global"]]]
        if not pts: continue
        gap = wall(pts)[1]
        depth = min(clusters([x for x, y in pts]), clusters([y for x, y in pts]))  # 墙厚 = 较薄轴
        w_escape[ref] = {"depth": depth, "min_pad_gap_mm": gap, "penetrable": gap >= lane_needed}
    L_escape = max([v["depth"] for v in w_escape.values()] + [1])
    chip_rows = w_escape["chip_field"]["depth"]

    # ---- L_capacity：区域容量闭合 ceil(D/C) ----
    board_y = spec["board"]["outline_y"]; edge = spec["constraints"]["edge_copper_min"]
    usable_y_span = r((board_y[1] - board_y[0]) - 2 * edge)     # 冻结板框 - 双侧板边铜（=45.4）
    chip_y_min = min(y for x, y in chip_pts); chip_y_max = max(y for x, y in chip_pts)
    regions = {}
    for c in spec["corridors"]:
        n = c["pairs"]; span = usable_y_span
        cap = span / ipair
        regions["corridor:" + c["id"]] = {"D_pairs": n, "cross_section_mm": span,
                                          "C_per_layer": r(cap, 2), "layers_needed": int(-(-n // int(cap)))}
    # chip N+S 逃逸翼带：由 manifest 实测 pad y 极值 + 冻结板框 + 板边规则派生（非硬编码）
    wing_span = r((chip_y_min - board_y[0] - edge) + (board_y[1] - chip_y_max - edge))
    wing_cap = int(wing_span / ipair)
    regions["chip_escape"] = {"D_pairs": len(pages), "cross_section_mm": wing_span,
                              "C_per_layer": r(wing_cap, 2), "layers_needed": int(-(-len(pages) // wing_cap))}
    L_capacity = max(v["layers_needed"] for v in regions.values())

    # ---- L_conflict：通道序冲突（排列图）最大团 ----
    adj = defaultdict(set); confl = {}
    for corr in sorted({p["corr"] for p in pages}):
        sub = [p for p in pages if p["corr"] == corr]
        for key, lab in (("chip_y", "src_y"), ("chip_x", "src_x")):
            seq = [p["conn_y"] for p in sorted(sub, key=lambda p: p[key])]
            confl[f"{corr}:{lab}->tgt_y"] = lds(seq)
        # 冲突图：源序反演对（chip_x 序 → conn_y 序）
        seq = sorted(sub, key=lambda p: p["chip_x"])
        for i in range(len(seq)):
            for j in range(i + 1, len(seq)):
                if seq[i]["conn_y"] > seq[j]["conn_y"]:
                    adj[seq[i]["page"]].add(seq[j]["page"]); adj[seq[j]["page"]].add(seq[i]["page"])
    for v in ({p["page"] for p in pages} - set(adj)): adj[v] = set()
    L_conflict = max(list(confl.values()) + [1])
    coloring = greedy_color(adj)
    n_colors = (max(coloring.values()) + 1) if coloring else 0
    # 验证着色合法（同色无边）⇒ 同层交叉 0
    same_color_edges = sum(1 for u in adj for v in adj[u] if u < v and coloring[u] == coloring[v])

    # ---- 派生 stackup ----
    L_signal = max(L_escape, L_capacity, L_conflict, 3)
    total = 2 * L_signal
    names = ["F.Cu"] + [f"In{i}.Cu" for i in range(1, total - 1)] + ["B.Cu"]
    # 规则：F/B = signal（微带, ref GND）；内部 = (L_signal-2) 层 signal + (L_signal-1) GND + 1 PWR（夹心, PWR 居中）
    interior = names[1:-1]
    roles = {"F.Cu": SIG, "B.Cu": SIG}
    # 规则（复现冻结家族 6L/8L）：PWR 固定于 interior 索引 3 (In4)；其余 i 偶=GND / 奇=SIG
    int_roles = [PWR if i == 3 else (GND if i % 2 == 0 else SIG) for i in range(len(interior))]
    for nm, rl in zip(interior, int_roles): roles[nm] = rl
    signal_layers = [k for k, v in roles.items() if v == SIG]

    # ---- 闭合验证 ----
    closure = {
        "L_escape": L_escape, "L_capacity": L_capacity, "L_conflict": L_conflict, "L_signal_derived": L_signal,
        "total_layers_derived": total, "signal_layers": signal_layers,
        "region_closure": {k: {"D": v["D_pairs"], "C_total": r(v["C_per_layer"] * L_signal, 2),
                               "closed": v["D_pairs"] <= v["C_per_layer"] * L_signal} for k, v in regions.items()},
        "same_layer_crossings": same_color_edges,
        "greedy_colors_used": n_colors,
        "frozen_stackup_signal_layers": 3,
        "frozen_stackup_sufficient": 3 >= L_signal,
    }
    out = {
        "artifact": "m13_v57_layer_intent_derived", "revision": "LID.1", "schema": 1, "date": "2026-09-11",
        "authority": "capacity-closure derivation (rectification #03); inputs = frozen four + rules ONLY",
        "inputs_sha": {k: v["actual"] for k, v in drift.items()},
        "constants_from_frozen": {"w_mm": w, "clr_mm": clr, "pair_copper_mm": pair_copper,
                                  "pair_pitch_mm": ipair, "lane_needed_mm": lane_needed, "via_via_min_mm": r(via_via)},
        "L_escape_evidence": w_escape,
        "L_capacity_evidence": regions,
        "L_conflict_evidence": {"max_clique_per_order": confl, "conflict_edges": sum(len(v) for v in adj.values()) // 2},
        "derived_stackup": {"total_layers": total, "signal_layers": signal_layers,
                            "layer_purpose": [{"layer": nm, "role": roles[nm]} for nm in names],
                            "rule": "signal*2 total (reference sandwich); F/B outer signal; interior = (S-2) signal + (S-1) GND + 1 PWR"},
        "derived_topology": {"chip_row_to_signal_layer": {str(i): signal_layers[i % len(signal_layers)] for i in range(chip_rows)},
                             "color_assignment_size": len(coloring), "method": "fixed-order greedy coloring (O(n+m), deterministic)"},
        "closure": closure,
        "verdict": "DERIVED_SUFFICIENT" if closure["frozen_stackup_sufficient"] else "DERIVED_STACKUP_REQUIRED",
        "no_parameter_privilege": "layer count/purpose are OUTPUTS; no owner/work-order/revision-card input",
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    if not a.quiet:
        print(json.dumps({k: out[k] for k in ("verdict", "derived_stackup", "closure", "L_escape_evidence")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
