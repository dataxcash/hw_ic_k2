#!/usr/bin/env python3
"""K2 · R381 —— 项3「一次实现」之**验收台**（契约 K2_R379 之第 2 个可运行件）
输入 = 候选线束 JSON（{net:{"pts":[[x,y],..]}}）；输出 = exact_gate 读数 + buildability + 二值分类日志。
用法: python3 K2_R381_ITEM3_ACCEPTANCE_HARNESS_v1.py <model_l8.json> <candidate_routes.json> [out.json]
只读（不改模型/板/参数）。
"""
import json, sys, math
sys.path.insert(0, "k2/tools")
from k2_p4_b2_in5_lane_router_v3 import exact_gate, lane_anchors

def accept(model_path, cand_path, pitch=0.435, hw=0.08, layer="In5.Cu"):
    M = json.load(open(model_path)); C = json.load(open(cand_path))
    routes = C.get("best", C).get("routes", C.get("routes", C))
    routes = {k: {"pts": v["pts"]} for k, v in routes.items() if isinstance(v, dict) and "pts" in v}
    ans = [a for a in lane_anchors(M) if a["net"].startswith("PCIE_UP_OUT")]
    g = exact_gate(M, routes, ans, layer, hw, frozenset(), frozenset(), pitch)
    n = len(routes)
    ok = (n == 16 and g["n_lane_pitch_viol"] == 0 and g["n_clearance_viol"] == 0 and (g["endpoint_max_dev_mm"] or 1) < 1e-6)
    build = {"mode": "no_move" if ok else "relocation_listed",
             "施工队问答": ("能" if ok else "不能") + "（照此图直接连）",
             "note": "本台只判候选线束：互距/净距/端点 + 16/16 完整性"}
    binary = ("(a) 合法 16/16 见证 + buildability（含 ②(ii) 几何核）" if ok
              else "未达 (a)；是否 (b) 须另出**真实几何**严格 U<16 证书（不得以模型类上界冒充）")
    return {"n_routed": n, "gate": {k: g[k] for k in ("lane_pitch_req_mm","lane_pitch_min_gap_mm","n_lane_pitch_viol",
            "clearance_min_mm","n_clearance_viol","endpoint_max_dev_mm")},
            "buildability": build, "binary": binary, "verdict": "PASS(a)" if ok else "NOT(a)"}

if __name__ == "__main__":
    r = accept(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 3: json.dump(r, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
