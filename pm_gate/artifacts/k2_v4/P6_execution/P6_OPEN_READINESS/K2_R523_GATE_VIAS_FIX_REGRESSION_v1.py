#!/usr/bin/env python3
"""K2 · R523 —— 在册闸 `gate_vias` 崩溃修复的**回归判据**（只读 · Solve() 0 次）。

缺陷（R515/R517 实测）：`gate_vias` 里过孔—焊盘距离用
  `_seg_rect_dists(np.stack([V[:,None,:], V[:,None,:]], 1), PB2)`（形状 (n,2,1,2)）
喂给期望 (n,2,2) 的 `_seg_rect_dists` ⇒ `_pt_seg_pts` 广播 ValueError（全尺寸 50 过孔时必崩）。
修法（R523 版本件内）：`np.stack([V, V], 1)`（(n,2,2) 退化段，点=零长段）。

三条回归判据（本条 = 正面/负面/规模）：
  R1 规模：≥50 根过孔的批调用**不抛异常**（原缺陷的复现条件）；
  R2 负面（必须命中）：把过孔放在某在册焊盘**盒内** ⇒ 必须报 `via-obstacle-pad`；
  R3 正面（必须干净）：把过孔放在远离一切障碍与锚点的空点 ⇒ 不得报任何 pad 类违规。
"""
import importlib, json, sys, math, time

HERE = "."
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
import K2_R523_LAYERHOP_PARITY_FORMC_v1 as M       # 修复后的版本件
RT = M.RT

model = json.load(open("/tmp/opencode/archer/model_l8.json"))
P, X0, Y0 = M.P, M.X0, M.Y0

# 取一个在册非车道焊盘做负面控制
pad = None
for p in model["pads"]:
    if RT.is_lane(p["net"]) or p.get("pth"):
        continue
    if not (("In5.Cu" in p["layers"]) or ("In4.Cu" in p["layers"])):
        continue                                   # 必须是 In5/In4 上的在册障碍（否则本层被跳过）
    pad = p
    break
assert pad is not None, "no non-lane In5/In4 pad found"
cx, cy = pad["cx"], pad["cy"]

far = (X0 + 30 * P, Y0 + 61 * P)      # 板内空点（网格上，离锚点/焊盘远）
res = {"artifact": "k2_r523_gate_vias_fix_regression_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "HANDOFF-K2-522 sec.1 'gate_vias() full-size crash is the signing prerequisite; "
                    "a gate fix must be a new version number plus regression criteria'",
       "solve_calls": 0, "defect": "numpy broadcast ValueError in gate_vias via-vs-pad term (shape (n,2,1,2) vs (n,2,2))",
       "fix": "np.stack([V, V], 1) => (n,2,2) degenerate segments", "pad_probe": {"net": pad["net"], "cx": cx, "cy": cy},
       "far_probe": list(far)}

# R1 规模：50 根过孔，不得抛异常
big = [(X0 + (10 + i) * P, Y0 + (50 + (i % 8)) * P, "TST_%d" % i) for i in range(50)]
try:
    g = M.gate_vias(model, big, {}, [], hw=M.HW)
    res["R1_scale_50_vias"] = {"raised": False, "n_vias": g["n_vias"], "n_via_viol": g["n_via_viol"],
                               "pass": (g["n_vias"] == 50)}
except Exception as e:                                  # pragma: no cover
    res["R1_scale_50_vias"] = {"raised": True, "error": "%s: %s" % (type(e).__name__, e), "pass": False}

# R2 负面：过孔落在焊盘盒内 ⇒ 必报 via-obstacle-pad
try:
    g2 = M.gate_vias(model, [(cx, cy, "TST_PAD")], {}, [], hw=M.HW)
    kinds = [v[0] for v in g2["via_violations"]]
    res["R2_via_inside_pad_must_flag"] = {"n_via_viol": g2["n_via_viol"], "kinds": kinds,
                                          "pad_flagged": ("via-obstacle-pad" in kinds),
                                          "pass": "via-obstacle-pad" in kinds}
except Exception as e:                                  # pragma: no cover
    res["R2_via_inside_pad_must_flag"] = {"raised": True, "error": str(e), "pass": False}

# R3 正面：空点 ⇒ 不得报 pad 类
try:
    g3 = M.gate_vias(model, [(far[0], far[1], "TST_FAR")], {}, [], hw=M.HW)
    kinds3 = [v[0] for v in g3["via_violations"]]
    res["R3_far_via_clean"] = {"n_via_viol": g3["n_via_viol"], "kinds": kinds3,
                               "pass": not any(k.startswith("via-obstacle-pad") for k in kinds3)}
except Exception as e:                                  # pragma: no cover
    res["R3_far_via_clean"] = {"raised": True, "error": str(e), "pass": False}

res["all_pass"] = all(res[k].get("pass") for k in ("R1_scale_50_vias", "R2_via_inside_pad_must_flag", "R3_far_via_clean"))
res["verdict"] = ("FIXED (R1/R2/R3 pass)" if res["all_pass"] else "FAIL")
res["boundaries"] = "read-only; Solve() 0; no model/parameter/board/SPEC/tools/criteria change; no WORKER; no supervision writes"
res["buildability"] = "NOT-APPLICABLE (gate regression; no construction/feasibility claim; nothing moved)"
json.dump(res, open("K2_R523_GATE_VIAS_FIX_REGRESSION_v1.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=1))
print("WROTE K2_R523_GATE_VIAS_FIX_REGRESSION_v1.json")
