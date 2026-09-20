#!/usr/bin/env python3
"""K1 批 6 · **端点（右端=高 x 侧）可达性上界普查**（只读；handoff §8.2-②）。

问题：TX0.input 的右端（密集焊盘场，x 侧近 pad 行）在 F.Cu 单层无对级解
      （P 单独可达、N 避 P 后不可达）⇒ 须过孔换层 or 改 alloc。本件把
      「**换层能否救**」量成一个可用/不可用问题，并给出搜索规模。

方法（**松弛 = 上界**；方向写明）：
  对每个 net X、每个候选层 L ∈ {F.Cu, In1.Cu, In2.Cu}：
    在 **L 的障碍场**（与引擎同源：build_hs_field + SPEC 冻结段）上问
    『X 的端焊盘 → 走廊落点 (corr_x, track_X)』是否可达。
      · L == F.Cu：起点 = 焊盘（直连）
      · L ≠ F.Cu：起点 = 端焊盘周围**合法 via 落点集**（离所有焊盘 ≥0.3 的 0.1 网格）
  判：
    ① 某 net 在**所有**层皆不可达 ⇒ **结构性无解** ⇒ 必须改 alloc/拓扑；
    ② ∃ 分层指派 L_P ≠ L_N 两者皆可达 ⇒ **换层不排除**（须过孔 + 引擎模板）；
    ③ 仅 {F.Cu} 可达 ⇒ 须同层对级（已证 F.Cu 不可 ⇒ 亦为结构性）。
  松弛点（刻意）：异层不计 P/N 冲突、via 只查离焊盘距离（不查 via-via / 走廊层）。
  故 ① 是**真结论**（必要条件的否定），② 只是**不排除**。
另报：引擎现行 `_k1_escape` 可用层集（`{layer_p,layer_n,F.Cu,In2.Cu}`）是否含 In1。
用法：cd <容器根> && python3 <本件> [--core <tree>]
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = ["F.Cu", "In1.Cu", "In2.Cu"]


def _grid(px, py, span=1.2, step=0.1):
    n = int(span / step)
    return [(round(px + i * step, 3), round(py + j * step, 3))
            for i in range(-n, n + 1) for j in range(-n, n + 1)]


def run(data_root, core_root):
    sys.path.insert(0, os.path.join(core_root, "_shared"))
    import eda_core
    assert os.path.abspath(eda_core.__file__).startswith(os.path.abspath(core_root)), \
        "eda_core 未解析到影子: %s" % eda_core.__file__
    from eda_core import hs_route_model as H
    from eda_core.route_input import ModelConfig, ProjectRouteConfig
    k1 = os.path.join(data_root, "k1")
    spec_p = os.path.join(k1, "pm_gate/artifacts/k1/L3/SPEC_k1.json")
    cfg = ModelConfig.from_dict(ProjectRouteConfig.load(
        os.path.join(k1, "pm_gate/artifacts/k1/L2/route_model_config.json")).hs_config())
    m = H.HSRouteModel(os.path.join(k1, "k1_v1.kicad_pcb"), spec_p,
                       os.path.join(k1, "pm_gate/artifacts/k1/L3/model_solves/"
                                    "channel_alloc/channel_alloc.json"),
                       os.path.join(core_root, "_shared/eda_core/drc_rules.json"),
                       pro_path=os.path.join(k1, "k1_v1.kicad_pro"), config=cfg)
    spec = m.spec
    w = float((spec.get("impedance") or {}).get("width_mm", 0.09))
    gap = float(((spec.get("net_classes") or {}).get("PCIe85") or {})
                .get("diff_pair", {}).get("p_gap",
                                          (spec.get("impedance") or {}).get("gap_mm", 0.1)))
    out = {"artifact": "k1_u11_right_end_bound_probe", "schema": 1, "core": core_root,
           "centerline_req_mm": round(w + gap, 4),
           "relaxation": "异层不计 P/N 冲突；via 仅查离焊盘 ≥0.3；未查 via-via / 走廊层",
           "segments": {}}
    pads_all = [(p.pos[0], p.pos[1]) for p in m.board.pads]
    chain = dict(m.config.chain_segments or {})
    for base in m.v4_bases():
        for (net_p, net_n, segname) in chain.get(base, []):
            tag = "%s/%s" % (base, segname)
            ep = H.pair_endpoints(m.board, net_p, net_n)
            if len(ep["P"]) != 2 or len(ep["N"]) != 2:
                out["segments"][tag] = {"error": "端点不全"}
                continue
            xs = [ep["P"][i]["pos"][0] for i in (0, 1)] + \
                 [ep["N"][i]["pos"][0] for i in (0, 1)]
            corridor = m._corridor_for_x(min(xs), max(xs))
            tpn, tnn = (m._track_y_for(net_p, corridor.get("id")),
                        m._track_y_for(net_n, corridor.get("id")))
            if corridor is None or tpn is None or tnn is None:
                out["segments"][tag] = {"error": "走廊/通道缺失"}
                continue
            (track_p, layer_p), (track_n, layer_n) = tpn, tnn
            pad_r_x = min(ep["P"][1]["pos"][0], ep["N"][1]["pos"][0])
            corr_x = min(pad_r_x, corridor["x_range"][1])
            rec = {"corridor": corridor.get("id"), "corr_x_right": round(corr_x, 3),
                   "track_P": track_p, "layer_P": layer_p, "track_N": track_n,
                   "layer_N": layer_n,
                   "center_dist_PN": round(abs(track_p - track_n), 4),
                   "pad_row": {"P": [round(v, 3) for v in ep["P"][1]["pos"]],
                               "N": [round(v, 3) for v in ep["N"][1]["pos"]]},
                   "engine_escape_layers": sorted({layer_p, layer_n, "F.Cu", "In2.Cu"}),
                   "engine_has_In1": "In1.Cu" in {layer_p, layer_n, "F.Cu", "In2.Cu"},
                   "reach": {}}
            fields = {}
            for L in LAYERS:
                f = H.build_hs_field(m.board, m.rules, layer=L, clear_hs_pads=True,
                                     config=cfg, clear_hs_nets=(net_p, net_n))
                for src in (cfg.frozen_obstacle_sources or []):
                    if src.get("yield"):
                        continue
                    for (en, ea, eb, el) in H.spec_frozen_segments(spec, [src]):
                        if el != L:
                            continue
                        en_base = en[:-2] if en.endswith(("_P", "_N")) else en
                        if en_base == base or en.startswith(cfg.yield_seg_prefixes):
                            continue
                        f.add_seg(en, ea, eb, 0.09, el)
                fields[L] = f
                rec.setdefault("n_obstacles", {})[L] = len(getattr(f, "obstacles", []) or [])
            for key, net, target in (("P", net_p, (corr_x, track_p)),
                                     ("N", net_n, (corr_x, track_n))):
                pad = tuple(ep[key][1]["pos"])
                rec["reach"][key] = {}
                for L in LAYERS:
                    if L == "F.Cu":
                        starts = [pad]
                    else:
                        starts = [(x, y) for (x, y) in _grid(pad[0], pad[1])
                                  if min(math.hypot(x - ax, y - ay)
                                         for ax, ay in pads_all) >= 0.3]
                    n_ok, best = 0, None
                    for s0 in starts:
                        try:
                            r = H.HSVisibilityGraph(fields[L], net, s0, {target}).solve()
                        except RuntimeError:
                            r = None
                        if r is not None:
                            n_ok += 1
                            ln = sum(math.hypot(r[0][i + 1][0] - r[0][i][0],
                                                r[0][i + 1][1] - r[0][i][1])
                                     for i in range(len(r[0]) - 1))
                            best = ln if best is None else min(best, ln)
                    rec["reach"][key][L] = {"reachable": n_ok > 0,
                                            "n_start_points": len(starts),
                                            "n_reachable_starts": n_ok,
                                            "min_path_len": None if best is None else round(best, 3)}
            RP = [L for L in LAYERS if rec["reach"]["P"][L]["reachable"]]
            RN = [L for L in LAYERS if rec["reach"]["N"][L]["reachable"]]
            split = [(a, b) for a in RP for b in RN if a != b]
            if not RP or not RN:
                concl = "结构性无解 ⇒ 须改 alloc/拓扑（任何层数皆不可救）"
            elif split:
                concl = "换层不排除 ⇒ 须过孔 + 引擎模板（另案）"
            else:
                concl = "仅同层可达 ⇒ 须同层对级（F.Cu 已证不可 ⇒ 结构性）"
            rec["relaxed_verdict"] = {
                "layers_reachable_P": RP, "layers_reachable_N": RN,
                "split_layer_assignment_exists": bool(split),
                "example_assignment": split[0] if split else None,
                "conclusion": concl,
                "via_search_space": {
                    "start_points_per_net_per_inner_layer": len(
                        [(x, y) for (x, y) in _grid(*tuple(ep["N"][1]["pos"]))
                         if min(math.hypot(x - ax, y - ay) for ax, ay in pads_all) >= 0.3]),
                    "layers": LAYERS,
                }}
            out["segments"][tag] = rec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", default="/tmp/opencode/vgscope/best_of")
    a = ap.parse_args()
    out = run(os.getcwd(), a.core)
    json.dump(out, open(os.path.join(HERE, "BATCH6_U11_RIGHT_END_BOUND_v1.json"), "w"),
              ensure_ascii=False, indent=1)
    for b, r in out["segments"].items():
        if "error" in r:
            print("%-14s ERROR %s" % (b, r["error"])); continue
        print("%-14s corr_x=%-7.3f P=%-26s N=%-26s In1_in_engine=%-5s | %s" % (
            b, r["corr_x_right"], r["relaxed_verdict"]["layers_reachable_P"] or "none",
            r["relaxed_verdict"]["layers_reachable_N"] or "none",
            r["engine_has_In1"], r["relaxed_verdict"]["conclusion"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
