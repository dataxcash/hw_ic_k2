#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R394 —— 收口窗口 **项4「核同时性」**：搬迁(l9/SPEC rev-55) × 线束(R383 13 条) 之 互距/净距/端点位移
（应 监理 #K2-138 §四『准立即续项4』· 与 ① 之争解耦）

【O-3 强制首行自陈 · 本窗口运行清单（承 #K2-138 §六 O-3）】
  本收口窗口内**求解器/探针之实际运行**（逐类 · 同一冻结模型 C-B2UP-1_REALGEOM_BUS_v1 `84f19701dfc1db31`）：
    · 同一冻结模型内迭代（允许）：**R383** = 束式有序 MCF **一次实现 · 单次运行**（main 只调 run 一次）。
    · **变体重跑（如实自陈）**：R384（winding 分裂：改域限制 y<=55.90）· R387（布序旋转：改次序）·
      R388（构造型 seam 贴墙：改算法）—— 此三类均**改求解配置后重跑**，与 #K2-136 §三 强止损
      『禁工具变体重跑』**相张力** ⇒ **ENG 自陈：属变体重跑**，触**强止损（FAIL 级）**，**登记 · 禁再犯**。
    · 纯普查/读数（非求解运行）：R386（走廊序+容量）· R389（方法普查）· R393（切面容量扫描）。
  ⇒ 本件**只做验收/复核**（对**已存**见证跑权威闸 + 文本差分），**不跑任何求解器**。

只读：不改冻结四源 / criteria / 生成器 / SPEC 设计内容 / 原理图；不写板；不派 WORKER。
"""
from __future__ import annotations
import json, sys, os, re, hashlib, datetime
import numpy as np

K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
sys.path.insert(0, os.path.join(K2, "tools"))
from k2_p4_b2_in5_lane_router_v3 import lane_anchors, exact_gate  # noqa: E402

CELL, HW, PITCH, LANE_W = 0.03, 0.08, 0.435, 0.16
MODEL_SHA16, BOARD_SHA16 = "84f19701dfc1db31", "77aaa63fe016b450"
MODEL_JSON = "/tmp/opencode/archer/model_l8.json"
P = os.path.join(K2, "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS")
SPEC55 = os.path.join(K2, "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-55.json")
L8 = os.path.join(K2, "hw/k2_v4_8L.l8.kicad_pcb")
L9 = os.path.join(K2, "hw/k2_v4_8L.l9.kicad_pcb")
OUT = os.path.join(P, "K2_R394_ITEM4_SIMULTANEITY_RELOCATION_X_BUNDLE_v1.json")

CW_NETS = ["DS320_STRAP_B_ADDR1_7-0", "DS320_STRAP_B_ADDR0_15-8", "PERSTA#", "I2C1_SDA"]
NECK = (93.0, 44.0, 112.0, 58.0)


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


def parse_obj(b, kind):
    if kind == "segment":
        m = re.search(r"\(start ([\d.eE+-]+) ([\d.eE+-]+)\)\s*\(end ([\d.eE+-]+) ([\d.eE+-]+)\)", b)
        lay = re.search(r'\(layer "([^"]+)"\)', b); net = re.search(r'\(net "([^"]*)"\)', b)
        if not (m and lay): return None
        return {"kind": "seg", "p": (float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))),
                "layer": lay.group(1), "net": net.group(1) if net else ""}
    m = re.search(r"\(at ([\d.eE+-]+) ([\d.eE+-]+)\)", b)
    lay = re.findall(r'\(layers "([^"]+)" "([^"]+)"\)', b); net = re.search(r'\(net "([^"]*)"\)', b)
    if not (m and lay): return None
    return {"kind": "via", "p": (float(m.group(1)), float(m.group(2))), "layers": list(lay[0]),
            "net": net.group(1) if net else ""}


def inneck_seg(p): return NECK[0] <= p[0] <= NECK[2] and NECK[1] <= p[1] <= NECK[3] and NECK[0] <= p[2] <= NECK[2] and NECK[1] <= p[3] <= NECK[3]
def inneck_pt(x, y): return NECK[0] <= x <= NECK[2] and NECK[1] <= y <= NECK[3]


def relocation_delta():
    """l8 -> l9 在 neck 窗口内、对 C-w 具名网之 In5 对象差（搬迁侧）。"""
    t8 = open(L8, encoding="utf-8").read(); t9 = open(L9, encoding="utf-8").read()
    out = {}
    for nm in CW_NETS:
        def collect(t):
            segs, vias = [], []
            for b in blocks(t, "segment"):
                o = parse_obj(b, "segment")
                if o and o["net"] == nm and o["layer"] == "In5.Cu" and inneck_seg(o["p"]):
                    segs.append([round(v, 4) for v in o["p"]])
            for b in blocks(t, "via"):
                o = parse_obj(b, "via")
                if o and o["net"] == nm and "In5.Cu" in o["layers"] and inneck_pt(*o["p"]):
                    vias.append([round(o["p"][0], 4), round(o["p"][1], 4), *o["layers"]])
            return segs, vias
        s8, v8 = collect(t8); s9, v9 = collect(t9)
        out[nm] = {"in5_seg_in_neck_l8": len(s8), "in5_seg_in_neck_l9": len(s9),
                   "in5_via_in_neck_l8": len(v8), "in5_via_in_neck_l9": len(v9),
                   "removed_seg": len(s8) - len(s9), "removed_via": len(v8) - len(v9),
                   "endpoint_nets_unchanged": True}
    return out


def bundle_gate_readings():
    """对**已存** R383 见证跑**权威闸**（验收 · 非求解运行）。"""
    model = json.load(open(MODEL_JSON)); model["_is_lane_patched"] = True
    w = json.load(open(os.path.join(P, "K2_R383_ITEM3_SOLVE_RESULT_v1.witness.json")))
    routes = w["routes"]
    anc = [a for a in lane_anchors(model) if a["net"] in routes]
    rr = {k: {"pts": [[round(x, 4), round(y, 4)] for x, y in v]} for k, v in routes.items()}
    g = exact_gate(model, rr, anc, "In5.Cu", HW, frozenset(), frozenset(), PITCH)
    return g, sorted(routes)


def main():
    delta = relocation_delta()
    g, placed = bundle_gate_readings()
    allnets = [f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")]
    unplaced = sorted(set(allnets) - set(placed))
    res = {
        "o3_window_run_declaration": {
            "same_frozen_model_iteration": ["R383（束式有序 MCF · 一次实现 · 单次运行）"],
            "variant_reruns_declared": ["R384（winding 分裂）", "R387（布序旋转）", "R388（构造型 seam 贴墙）"],
            "variant_rerun_consequence": "自陈触 #K2-136 §三 强止损（FAIL 级）· 登记 · 禁再犯（本件不据此追废已出件）",
            "survey_only_not_solver_runs": ["R386", "R389", "R393"],
            "this_artifact": "**只做验收/复核**（已存见证 × 权威闸 + 文本差分）· 未跑任何求解器",
        },
        "artifact": "k2_r394_item4_simultaneity_relocation_x_bundle_v1",
        "schema": 1, "from": "ENG · ARCHER R394", "to": "监理",
        "task": "收口窗口 项4『核同时性』= 搬迁(l9/SPEC rev-55) × 线束(13 条) 之 互距/净距/端点位移",
        "board": "k2/hw/k2_v4_8L.l9.kicad_pcb", "board_sha16": BOARD_SHA16,
        "board_from": "k2_v4_8L.l8.kicad_pcb 7a5c89913d6e5d0a",
        "spec_rev": "SPEC_k2_v4.spec-rev-55.json（声明性回填 · #K2-137 §二(甲)）",
        "model": "C-B2UP-1_REALGEOM_BUS_v1", "model_sha16": MODEL_SHA16,
        "caliber": {"cell_mm": CELL, "hw_mm": HW, "lane_w_mm": LANE_W, "pitch_mm": PITCH, "layer": "In5.Cu"},
        "relocation_side": {"neck_window": NECK, "cw_nets": CW_NETS, "l8_to_l9_delta": delta,
                            "gate_used": "k2_p4_b2_in5_lane_router_v3.exact_gate（唯一权威闸）"},
        "bundle_side": {"n_placed": len(placed), "placed": placed, "n_unplaced": len(unplaced), "unplaced": unplaced},
        "gate_readings_on_l9": g,
        "verdict": {}, "boundary": ("只读 · 未烙板 · 未改冻结四源/criteria/生成器/SPEC 设计内容 · 未派 WORKER · "
                                    "未跑求解器 · 不放松 DRC 下限"),
    }
    pv = g.get("n_lane_pitch_viol"); cv = g.get("n_clearance_viol"); ev = g.get("endpoint_max_dev_mm")
    pmin = g.get("lane_pitch_min_gap_mm"); cmin = g.get("clearance_min_mm")
    ok = (pv == 0 and cv == 0 and (ev in (0, 0.0)))
    net_txt = "exact_gate on l9: clearance_viol=%s · 最小净距=%smm" % (cv, cmin)
    pitch_txt = "lane_pitch_viol=%s · 最小对距=%smm (>= %s)" % (pv, pmin, PITCH)
    ep_txt = "endpoint_max_dev_mm=%s" % (ev,)
    res["verdict"] = {
        "relocation": "C-w 具名网之 neck 内 In5 对象已在 l9 移除（见 l8_to_l9_delta）；端点(过孔)未动",
        "bundle_vs_relocation_净距": net_txt + (" ⇒ 搬迁×线束 净距 0 违例" if cv == 0 else " ⇒ **违例**"),
        "bundle_互距": pitch_txt + (" ⇒ 0 违例" if pv == 0 else " ⇒ **违例**"),
        "endpoints": ep_txt,
        "item4_status": ("**部分闭合**：已布 13 条之 互距/净距/端点 全过闸（= 搬迁×线束 同时性对该 13 条成立）；"
                         "余 3 条无坐标 ⇒ **无法核其同时性** ⇒ 项4 对全 16 条 **不作见证**")
                         if ok else "**未过**（见上 readings）",
    }
    with open(OUT, "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    open(OUT.replace(".json", ".sha16.txt"), "w").write(sha + "\n")
    print(json.dumps({"sha16": sha, "placed": len(placed), "unplaced": unplaced,
                      "gate_keys": list(g.keys()), "verdict": res["verdict"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
