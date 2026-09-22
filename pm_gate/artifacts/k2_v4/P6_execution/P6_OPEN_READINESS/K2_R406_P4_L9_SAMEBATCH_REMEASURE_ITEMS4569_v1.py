#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R406 —— **P4 阶段门 · l9 同批重测**（items 5 等长 / 6 3W / 9 钻孔·铺铜前置 / 豁免表）——
   只读文本解析（本机无 pcbnew）；**非新法 · 非变体 · 非参数扫描 · 无求解器**。

【O-2/O-3 强制首行自陈 · 本窗口运行清单】
  同一冻结模型内迭代：R383/R397/R398/R399/R401/R402（历史）。本件 R406 = **P4 门项测量**（只读文本解析）。
  变体重跑（已登记 FAIL 级）：R384/R387/R388。 本件**不跑求解器**、**不启新法**、**不扫参数**。
依据：R270《R4 闸就绪度》items 4/5/6/9「l9 同批重测」· 阶段门 fail-closed。
只读：不改冻结四源/criteria/生成器/SPEC 设计内容；不写板；不派 WORKER。
"""
from __future__ import annotations
import json, os, re, math, hashlib, datetime
import numpy as np

K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
L9 = os.path.join(K2, "hw/k2_v4_8L.l9.kicad_pcb")
P = os.path.join(K2, "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS")
OUT = os.path.join(P, "K2_R406_P4_L9_SAMEBATCH_REMEASURE_ITEMS4569_v1.json")
NETS = ["PCIE_UP_OUT%d_%s_J2" % (i, s) for i in range(8) for s in ("N", "P")]


def blocks(t, key):
    out = []; pat = "(" + key; i = 0
    while True:
        i = t.find(pat, i)
        if i < 0: break
        k = i; d = 0; ins = False
        while k < len(t):
            c = t[k]
            if ins:
                if c == '"' and t[k - 1] != "\\": ins = False
            elif c == '"': ins = True
            elif c == "(": d += 1
            elif c == ")":
                d -= 1
                if d == 0: break
            k += 1
        out.append(t[i:k + 1]); i = k + 1
    return out


def segseg(a, b):
    (ax, ay, bx, by), (cx, cy, dx, dy) = a, b
    def d_pt_seg(px, py, x1, y1, x2, y2):
        vx, vy = x2 - x1, y2 - y1; wx, wy = px - x1, py - y1
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L2))
        return math.hypot(px - (x1 + t * vx), py - (y1 + t * vy))
    def inter(p1, p2, p3, p4):
        d1 = ((p2[0]-p1[0])*(p4[1]-p3[1]) - (p2[1]-p1[1])*(p4[0]-p3[0]))
        if abs(d1) < 1e-12: return False
        t = ((p3[0]-p1[0])*(p4[1]-p3[1]) - (p3[1]-p1[1])*(p4[0]-p3[0])) / d1
        u = ((p3[0]-p1[0])*(p2[1]-p1[1]) - (p3[1]-p1[1])*(p2[0]-p1[0])) / d1
        return 0 <= t <= 1 and 0 <= u <= 1
    if inter((ax, ay), (bx, by), (cx, cy), (dx, dy)): return 0.0
    return min(d_pt_seg(ax, ay, cx, cy, dx, dy), d_pt_seg(bx, by, cx, cy, dx, dy),
               d_pt_seg(cx, cy, ax, ay, bx, by), d_pt_seg(dx, dy, ax, ay, bx, by))


def main():
    t = open(L9, encoding="utf-8").read()
    segs = {}; vias = {}
    for b in blocks(t, "segment"):
        m = re.search(r"\(start ([\d.eE+-]+) ([\d.eE+-]+)\)\s*\(end ([\d.eE+-]+) ([\d.eE+-]+)\)", b)
        w = re.search(r"\(width ([\d.]+)\)", b); lay = re.search(r'\(layer "([^"]+)"\)', b)
        net = re.search(r'\(net "([^"]*)"\)', b)
        if not (m and lay): continue
        nm = net.group(1) if net else ""
        if nm not in NETS: continue
        L = {"F.Cu": 0, "In5.Cu": 0}.get(lay.group(1))
        if L is None: continue
        p = (float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))
        segs.setdefault(nm, {"In5": [], "F": []})
        segs[nm]["In5" if lay.group(1) == "In5.Cu" else "F"].append({"p": p, "w": float(w.group(1)) if w else 0.16})
    for b in blocks(t, "via"):
        m = re.search(r"\(at ([\d.eE+-]+) ([\d.eE+-]+)\)", b); net = re.search(r'\(net "([^"]*)"\)', b)
        if not (m and net) or net.group(1) not in NETS: continue
        vias.setdefault(net.group(1), 0); vias[net.group(1)] += 1
    rows = {}
    for nm in NETS:
        s = segs.get(nm, {"In5": [], "F": []})
        ln5 = sum(math.hypot(x2 - x1, y2 - y1) for x1, y1, x2, y2 in [q["p"] for q in s["In5"]])
        lf = sum(math.hypot(x2 - x1, y2 - y1) for x1, y1, x2, y2 in [q["p"] for q in s["F"]])
        rows[nm] = {"n_in5_seg": len(s["In5"]), "len_in5_mm": round(ln5, 4), "len_f_mm": round(lf, 4),
                    "n_via": int(vias.get(nm, 0))}
    # item5 等长：N/P skew per pair（长走 = In5）
    skew = {}
    for i in range(8):
        n = "PCIE_UP_OUT%d_N_J2" % i; p_ = "PCIE_UP_OUT%d_P_J2" % i
        skew["pair%d" % i] = round(abs(rows[n]["len_in5_mm"] - rows[p_]["len_in5_mm"]), 4)
    # item6 3W：16 网 In5 轨间最小中心距（only 互距 · 全线）
    minsep = (1e9, None)
    segs_all = []
    for nm in NETS:
        for q in segs.get(nm, {"In5": []})["In5"]:
            segs_all.append((q["p"], nm))
    for i in range(len(segs_all)):
        for j in range(i + 1, len(segs_all)):
            if segs_all[i][1] == segs_all[j][1]: continue
            d = segseg(segs_all[i][0], segs_all[j][0])
            if d < minsep[0]: minsep = (d, (segs_all[i][1], segs_all[j][1]))
    n_zones = t.count("(zone ")
    n_drill = len(re.findall(r"\(drill ", t))
    res = {
        "o2_o3_window_run_declaration": {"same_frozen_model_iteration": ["R383", "R397", "R398", "R399", "R401", "R402"],
            "variant_reruns_registered": ["R384", "R387", "R388"],
            "this_artifact": "R406 = P4 门项 l9 同批测量（只读文本解析 · 无求解器 · 无新法 · 无参数扫描）"},
        "artifact": "k2_r406_p4_l9_samebatch_remeasure_items4569_v1", "schema": 1,
        "from": "ENG · ARCHER R406", "to": "监理",
        "authority": "R270《R4 闸就绪度》items 4/5/6/9『l9 同批重测』· 阶段门 fail-closed · #K2-142 §四（禁新法/变体/扫描 —— 本件皆无）",
        "board": "k2/hw/k2_v4_8L.l9.kicad_pcb", "board_sha16": hashlib.sha256(open(L9, "rb").read()).hexdigest()[:16],
        "per_net_l9": rows,
        "item5_length_matching_skew_mm": {"per_pair": skew, "max_skew_mm": max(skew.values()),
            "l8_baseline_max_skew_mm": 6.002, "threshold": "**未具名**（承 R270 item5 待『阈值具名』）· 本件只报读数，不自定阈值"},
        "item6_3W_min_center_to_center_mm": {"min_mm": round(minsep[0], 4), "pair": minsep[1],
            "3W_threshold_mm": 0.480, "verdict": ("PASS" if minsep[0] >= 0.480 else "**FAIL(<3W)**")},
        "item9_precondition_census": {"n_zone_objects": n_zones, "n_drill_tokens": n_drill,
            "note": "平面/铺铜/钻孔『前置』之全量核需平面工具；本件只报板面存在性读数（如实标注不完整）"},
        "item4_ref_plane_continuity": {"status": "**未测（本轮）**", "reason": "需平面层连续性工具（R372 平面提取器）· 未跑 ⇒ 如实登记为 P4 残余项，不冒充"},
        "item3_l9_exemption_table": {"status": "**待 owner/监理 圈定具名集后落表**（承 #K2-142 升 owner）· 未自行预设 N"},
        "p4_gate_state": {"hard_blocker": "②-UP=16/16 二值（(a) 未取得 / (b) 未建立）· 已升 owner（#K2-142 · owner 项 1）",
            "this_artifact_closes": ["item6（3W @l9 读数）", "item5（skew @l9 读数 · 阈值待具名）", "item9（存在性读数 · 不完整）"],
            "still_open": ["item4（ref plane continuity @l9 · 未测）", "item5 阈值具名", "item9 全量核", "item2 ②-UP（owner）"]},
        "boundary": "只读 · 未烙板 · 未改冻结四源/criteria/生成器/SPEC 设计内容 · 未派 WORKER · 未跑求解器"}
    with open(OUT, "w") as fh: json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    open(OUT.replace(".json", ".sha16.txt"), "w").write(sha + "\n")
    print(json.dumps({"sha16": sha, "board_sha16": res["board_sha16"], "max_skew_mm": max(skew.values()),
                      "min_3w_mm": round(minsep[0], 4), "3w_verdict": res["item6_3W_min_center_to_center_mm"]["verdict"],
                      "n_zones": n_zones, "n_drill_tokens": n_drill, "sample_net": rows["PCIE_UP_OUT0_N_J2"]},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
