#!/usr/bin/env python3
"""K2 · R515 第一步（遵 #K2-187 §三.6「第一步：只读 · 不占额度」）—— **保真自检**：
机器可核地写明**本模型保留了什么 / 丢弃了什么**（尤以**设计自身坐标**为据），并自证
「不可行属**设计性质**还是**模型自造**」。

判据（#K2-187 §四）：
  「假不可行」= 模型自造不可行（保真缺失 / 过约束）；**判别指纹** = 不可行核为空 + 前提含「吸附丢解」。
形式化：本模型是**保守**抽象（只排除合法解、不放行非法解）⇒ **模型解集 ⊂ 连续解集** ⇒
  **模型 UNSAT ⇏ 设计 UNSAT** ⇒ 其不可行**不构成证书**（承 R513 §二「抽象缝真实存在」）。
本件 `Solve()` **0 次** · 不改任何东西 · 只读测量。
"""
import importlib, json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
R = importlib.import_module("K2_" + "R" + "514" + "_LAYERHOP_JOINT_MCF_v2")
P = R.P; HW = R.HW; XY = R.XY; NID = R.NID


def main():
    out = os.path.join(HERE, "K2_R515_FIDELITY_SELFCHECK_v1.json")
    t0 = time.time()
    model = json.load(open("/tmp/opencode/archer/model_l8.json"))
    g2 = R.Gen2(model, l1scope="full", verbose=True)
    g = g2.g0
    rep = {"artifact": "k2_r515_fidelity_selfcheck_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-187 sec.3.6 step-1 (read-only fidelity self-check; Solve() 0 calls; quota 0)",
           "question": "what does this model PRESERVE and what does it DISCARD (esp. the design's own coordinates), "
                       "and is the R514 INFEASIBLE a DESIGN property or MODEL-SELF-INFLICTED?",
           "P_mm": P, "HW_mm": HW}

    # ---------------- 保留（preserved） ----------------
    rep["preserved"] = {
        "clearance_criterion": "registered ruler, pairwise-exact (R513-T3: 1408 true conflicts <-> 1408 forbidden, "
                               "0 missed / 0 over-strict) on the pitch-P unit-arc class",
        "clearance_realisation": "R514-v2 head-arc occupancy => y in {0,1} (the v2 repair; v1 was defective)",
        "obstacle_sets": {ln: len(model["segs"][ln]) for ln in model["segs"]},
        "obstacles_detail": "per-layer build_base (other-net copper + pth pads + ruleareas) + other-lane A/B anchor "
                            "keepout HW+max(via_r+eff, drill+HOLE_CLR); lane copper treated as 'movable' (baseline convention)",
        "cross_layer": "no clearance between In5 and In4 (different layers do not conflict) -- physically correct; "
                       "a via occupies the SAME node on both layers (capacity on both layers)",
        "via_rules": {"r": R.VIA_R, "drill": R.VIA_DRILL, "VR": R.VR, "pair_min_mm": R.VIA_SEP,
                      "via_zone_boxes": R.ZONES, "max_pairs_per_lane": R.MAX_VIA_PAIRS},
        "flow_structure": "unit flow per lane (identity pairing) + per-layer node capacity (heads + src <= 1) + "
                          "per-layer shadow-disjointness, all linear"}

    # ---------------- 丢弃（discarded）· 逐条附机器读数 ----------------
    names = g2.names
    snapA, snapB, alt, pairtrue, pairsnap = {}, {}, {}, [], []
    radii = [0.5 * P, 0.75 * P, 1.0 * P, 1.5 * P]
    altcount = {nm: {("A", r): 0 for r in radii} for nm in names}
    altcount.update({nm: {("B", r): 0 for r in radii} for nm in names})
    snapped = {}
    for nm in names:
        n2d = g.node_ok(nm); pts = g.pt_by_net[nm]
        a = tuple(g2.A[nm]); b = tuple(g2.B[nm])
        s0 = g.nearest_node(a, n2d, pts); b0 = g.nearest_node(b, n2d, pts, taken=() if s0 is None else (s0,))
        snapped[nm] = (s0, b0)
        snapA[nm] = round(math.dist(a, XY(*s0)), 4); snapB[nm] = round(math.dist(b, XY(*b0)), 4)
        # 备选落点（模型**丢掉**的落点自由度）：半径内、且"直腿"全程合法（在册尺）的格点数
        for tag, anc in (("A", a), ("B", b)):
            idx = np.argwhere(n2d)
            xy = np.stack([R.X0 + idx[:, 0] * P, R.Y0 + idx[:, 1] * P], 1)
            dd = np.hypot(xy[:, 0] - anc[0], xy[:, 1] - anc[1])
            for r in radii:
                cand = idx[dd <= r]
                cnt = 0
                for (i, j) in cand.tolist():
                    if g.seg_ok(anc, XY(i, j), pts):
                        cnt += 1
                altcount[nm][(tag, r)] = cnt
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a1, a2 = g2.A[names[i]], g2.A[names[j]]
            n1 = XY(*snapped[names[i]][0]); n2 = XY(*snapped[names[j]][0])
            pairtrue.append(math.dist(a1, a2)); pairsnap.append(math.dist(n1, n2))
    pt = np.array(pairtrue); ps = np.array(pairsnap)
    # 设计自身坐标：A 站点 x 间距 + y 行（对格点的偏移）
    ax = sorted(round(float(g2.A[nm][0]), 4) for nm in names)
    ay = sorted(set(round(float(g2.A[nm][1]), 4) for nm in names))
    pitch = sorted(round(ax[k + 1] - ax[k], 4) for k in range(len(ax) - 1))
    yrows = [{"y_mm": y, "lattice_row_float": round((y - R.Y0) / P, 3),
              "offset_mm": round((y - R.Y0) / P - round((y - R.Y0) / P), 4) * P} for y in ay]
    repp = np.array(list(snapA.values()) + list(snapB.values()))
    rep["discarded"] = [
        {"id": "D-1", "what": "锚点吸附：模型把车道端点**钉在**一个 0.435 格点上（真锚点不在格上）",
         "machine_reading": {"snapA_max_mm": max(snapA.values()), "snapA_mean_mm": round(float(np.mean(list(snapA.values()))), 4),
                             "snapB_max_mm": max(snapB.values()), "snap_max_mm": round(float(repp.max()), 4),
                             "snap_max_in_P": round(float(repp.max()) / P, 4)},
         "dropped": "真几何里「锚点 → 第一个格点」那一腿是**长度可到 0.247mm、方向自由**的真实铜；模型把它**整根丢掉**（既不约束也不利用）",
         "direction": "过约束（只排除合法解）⇒ **丢解**；R513 §二.1 已实测（吸附位移 0.033–0.247mm）"},
        {"id": "D-2", "what": "设计自身坐标未保留：A 站点 x 间距 0.50/0.65mm = 1.149P / 1.494P（**非 P 整数倍**），y 落 4 个浮点行",
         "machine_reading": {"A_x_pitch_mm": pitch, "A_x_pitch_in_P": [round(v / P, 4) for v in pitch],
                             "A_y_rows": yrows,
                             "n_pairs_with_integer_P_pitch": int(sum(1 for v in pitch if abs(v / P - round(v / P)) < 1e-3))},
         "dropped": "梳齿的**内部相对几何**在 P 格上**不可表示**（0.50/0.65 不是 0.435 的整数倍）",
         "direction": "过约束（只排除合法解）⇒ **丢解**"},
        {"id": "D-3", "what": "端点落点自由度被**确定化**：nearest_node 只取**一个**最近格点",
         "machine_reading": {"legal_alt_nodes_per_endpoint": {str(int(r / P * 100)) + "pctP": {
             "min": int(min(altcount[nm][(t, r)] for nm in names)), "max": int(max(altcount[nm][(t, r)] for nm in names)),
             "n_endpoints_with_ge2": int(sum(1 for nm in names if altcount[nm][(t, r)] >= 2))}
             for t in ("A", "B") for r in radii}},
         "dropped": "半径 r 内「直腿合法」的备选落点被**全部丢弃**（只留最靠近的那一个）",
         "direction": "过约束 ⇒ **丢解**（r≥1.0P 时每个端点普遍有 ≥2 个合法备选）"},
        {"id": "D-4", "what": "吸附**扰动了两两相对距离**（梳齿被压/撑）",
         "machine_reading": {"n_pairs": len(pairtrue),
                             "max_compression_mm": round(float((pt - ps).max()), 4),
                             "max_expansion_mm": round(float((ps - pt).min()), 4),
                             "n_pairs_compressed": int((ps < pt - 1e-9).sum()),
                             "n_pairs_below_P_after_snap": int((ps < P - 1e-9).sum()),
                             "min_true_mm": round(float(pt.min()), 4), "min_snapped_mm": round(float(ps.min()), 4)},
         "dropped": "模型里的**起点几何 ≠ 设计几何**（逐对最多偏移 0.13mm 级）",
         "direction": "过约束 + 几何失真 ⇒ **丢解**（且失真量与 P 同阶）"},
        {"id": "D-5", "what": "格点上「16 条**节点不相交**路径」= 比物理要求**更强**",
         "machine_reading": {"note": "连续曲线**不必**经过格点；把曲线吸到格点上会**制造**共点冲突 ⇒ "
                                     "「格点节点不相交」是**离散化产物**，不是物理要求",
                             "physical_requirement": "仅要求两两中心距 >= P"},
         "direction": "过约束 ⇒ **丢解**；正是 #K2-187 §四.①「假不可行」的机制"},
        {"id": "D-6", "what": "自定放宽/约定（非物理）", 
         "machine_reading": {"detour_budget": R.BOUND, "region_convention": "east lanes excluded from NW maze on In5 only",
                             "via_zones": "4 wide boxes only", "max_via_pairs": R.MAX_VIA_PAIRS},
         "direction": "过约束（T6/T8 已证对**流**非绑定；对**配对**问题未证）"}]
    rep["verdict"] = {
        "formal": "本模型是保守抽象（模型解集 ⊂ 连续解集）⇒ **模型 UNSAT ⇏ 设计 UNSAT** ⇒ "
                  "其不可行**不构成证书**（这一点在 R513 §二 已具名，本次以**五项丢弃台账**逐条量化）",
        "fingerprint_match": "#K2-187 §四.① 的判别指纹**命中**：(a) 不可行**核为空**；(b) 自列前提含**「吸附丢解」**(D-1/D-2/D-4)。"
                             "⇒ 该 UNSAT 属**模型自造（假不可行）之嫌疑**，**不是**设计级不可行。",
        "what_is_needed": "要把它变成**可用**的二值，必须**先补保真**：让「设计自身坐标」进入模型（见 next_window_spec F1/F2），"
                          "并让不可行结论落成**非空核**（F3）。",
        "ENG_accepts_k2_187": "**接受** #K2-187 §三.5：R514 之 INFEASIBLE **不作终局二值**、不作里程碑 ⇒ 结论只能是**未完成**。"}
    rep["next_window_spec"] = {
        "F1_free_access_leg": "每根车道的真锚点 A/B 提升为**虚拟端子**（位于设计自身坐标）；端子 → 半径 r_reach 内"
                              "**所有直腿合法**的格点之间加**真实弧**（腿的**声明集**按「格点到腿段真距 < P」逐条算出，"
                              "进 v2 已修好的 head-arc + shadow 机制）⇒ **设计自身坐标进入模型**，吸附丢解被消除。",
        "F2_no_fixed_pitch_snap": "端点**不再**被钉到唯一格点（承 #K2-187 §四.②「不以丢失设计自身坐标的固定节距重离散」）。",
        "F3_non_empty_core": "把**每一组硬约束**（节点容量 / 过孔对上限 / 过孔间距 / 长度界 / 净距组）各自挂在**独立假设字面量**上 "
                             "⇒ 解不出时必须返回**非空核**（#K2-187 §四.④ 的硬判据）。",
        "F4_unchanged": "其余（逐层在册净距、跨层/过孔判据、四宽区、<=2 对、冻结四源/判据）**一字不改**。"}
    rep["boundaries"] = "read-only; Solve() 0 calls; quota 0; nothing edited; frozen four sources untouched"
    rep["buildability"] = "NOT-APPLICABLE (diagnostic fidelity ledger; no construction/feasibility claim; no object moved)"
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"discarded": [{k: d[k] for k in ("id", "what", "machine_reading")} for d in rep["discarded"]],
                      "verdict": rep["verdict"]}, ensure_ascii=False, indent=1)[:3000])
    print("WROTE", out)


if __name__ == "__main__":
    main()
