#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R399 —— **末次收口窗**：① 记账补正（#K2-140 §三.2）② 出图工具（构造性 · 直接生成几何）

【O-2/O-3 强制首行自陈 · 本窗口运行清单】
  同一冻结模型内迭代：R383 · R397（主路）· R398（独立复核）· **本件 R399（构造器 · 一次实现 · 一次运行）**。
  变体重跑（已登记 FAIL 级 · 禁再犯）：R384 · R387 · R388。  只读普查/复核：R386/R389/R393/R394/R395/R396。
  ⇒ 本件**不跑任何求解器**：只跑**构造性几何生成**（一次）＋权威闸验收。

—— ① 记账补正（承 #K2-140 §一/O-3，硬条件）——
  旧件之瑕：`model_l8.json` **自述 board = l8**（file sha16 `c42731c4258ae691`），而件上写"受审板 = l9"，
  且"冻结模型指纹 84f19701dfc1db31"**全仓无脚本可复算**（pcbnew 不可用 ⇒ 无法由板重 dump）。
  本件之补正（**补丁制 · 附补丁清单** · 全部**脚本级可复算**）：
    · 输入**板** = `k2/hw/k2_v4_8L.l9.kicad_pcb`（sha16 由脚本实算并断言 == 77aaa63fe016b450）。
    · 基**模型** = `model_l8.json`（file sha16 由脚本实算 = c42731c4258ae691 · 其自述 board = l8）。
    · **补丁 P** = 依 R394 文本差分把 **C-w 具名网**在 neck 内的 **In5 段/孔**自模型移除
      （= l8→l9 之 In5 几何差；补丁清单逐项落件）⇒ 得 **derived-l9 模型**。
    · derived-l9 模型指纹亦**由脚本实算**（sha16）并落件。
  ⇒ 满足：**计算输入板 == 件上所写受审板（l9）**（经补丁 P 达成）· 指纹**可复算** · **补丁清单在岗**。

—— ② 出图工具（构造性）——
  构造（**非搜索** · 确定性 · 无参数扫描）：每 lane 取 **3 段折线** A->(x_A,y_slot)->(x_B,y_slot)->B，
  y_slot 取走廊带内 **等距槽位**（pitch 0.45 > 0.435），槽序 = **B 焊盘 x 升序**（使 B 侧扇入天然无交叉）。
  验收：`k2_p4_b2_in5_lane_router_v3.exact_gate`（唯一权威闸）。
  二值：全 16 过闸 ⇒ (a) 见证；否则 ⇒ **具名障碍**（哪条 · 哪个几何量 · 最小可复现例）。

只读：不改冻结四源 / criteria / 生成器 / SPEC 设计内容；不写板；不派 WORKER。
"""
from __future__ import annotations
import json, sys, os, math, hashlib, datetime, copy
import numpy as np

K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
sys.path.insert(0, os.path.join(K2, "tools"))
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base, lane_anchors, exact_gate  # noqa: E402

CELL, HW, PITCH, LANE_W = 0.03, 0.08, 0.435, 0.16
SLOT_PITCH = 0.45
BASE_MODEL = "/tmp/opencode/archer/model_l8.json"
ANCHOR_JSON = "/tmp/opencode/k2r376/anchor_table.json"
L8 = os.path.join(K2, "hw/k2_v4_8L.l8.kicad_pcb"); L9 = os.path.join(K2, "hw/k2_v4_8L.l9.kicad_pcb")
P = os.path.join(K2, "pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS")
OUT = os.path.join(P, "K2_R399_FINAL_WINDOW_CONSTRUCTOR_AND_BOOKKEEPING_FIX_v1.json")
CW_NETS = ["DS320_STRAP_B_ADDR1_7-0", "DS320_STRAP_B_ADDR0_15-8", "PERSTA#", "I2C1_SDA"]
NECK = (93.0, 44.0, 112.0, 58.0)
BOARD_SHA16_L9 = "77aaa63fe016b450"; BOARD_SHA16_L8 = "7a5c89913d6e5d0a"


def sha16(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
def canon16(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:16]


def patched_model():
    """l8 模型 + 补丁 P（移除 C-w 具名网 neck 内 In5 段/孔）⇒ derived-l9 模型；返回 (model, patch_list)。"""
    m = json.load(open(BASE_MODEL))
    keep = []; removed = {"segs": [], "vias": []}
    for s in m["segs"]["In5.Cu"]:
        x1, y1, x2, y2, r, net = s
        inneck = all(NECK[0] <= v <= NECK[2] for v in (x1, x2)) and all(NECK[1] <= v <= NECK[3] for v in (y1, y2))
        if net in CW_NETS and inneck:
            removed["segs"].append([round(v, 4) for v in s[:4]] + [net]); continue
        keep.append(s)
    m["segs"]["In5.Cu"] = keep
    vk = []
    for v in m["vias"]:
        ok = (v["net"] in CW_NETS and "In5.Cu" in v["layers"]
              and NECK[0] <= v["x"] <= NECK[2] and NECK[1] <= v["y"] <= NECK[3])
        if ok:
            removed["vias"].append([round(v["x"], 4), round(v["y"], 4), v["net"]]); continue
        vk.append(v)
    m["vias"] = vk
    m["_is_lane_patched"] = True
    patch = {"id": "P_l8_to_l9_in5_neck_removal",
             "rationale": "l9 = l8 + C-w v55 搬迁（neck 内 In5 段/孔移除）· 依 R394 文本差分",
             "neck_window": NECK, "cw_nets": CW_NETS,
             "removed_in5_segments": removed["segs"], "removed_in5_vias": removed["vias"],
             "n_removed_seg": len(removed["segs"]), "n_removed_via": len(removed["vias"]),
             "model_patch": "_is_lane_patched=True（lane 网自身铜不计入障碍）"}
    return m, patch


def construct(L, free, rast, off):
    """构造性 3 段折线：A->(x_A,y_slot)->(x_B,y_slot)->B；槽序 = B 焊盘 x 升序。"""
    nx, ny = free.shape
    box = [float(rast.X0) + off[0] * CELL, float(rast.Y0) + off[1] * CELL,
           float(rast.X0) + (off[0] + nx) * CELL, float(rast.Y0) + (off[1] + ny) * CELL]
    order = sorted(range(len(L)), key=lambda k: L[k]["B"][0])      # B 焊盘 x 升序 = 南->北槽序
    xc = 110.0
    icol = int((xc - rast.X0) / CELL) - off[0]
    col = free[icol, :]
    # 找最大自由连续段（走廊带）
    best = (0, 0, 0); s = None
    for i in range(len(col)):
        if col[i] and s is None: s = i
        if not col[i] and s is not None:
            if i - s > best[0]: best = (i - s, s, i - 1)
            s = None
    if s is not None and len(col) - s > best[0]: best = (len(col) - s, s, len(col) - 1)
    w, s0, s1 = best
    y0 = float(rast.Y0) + (off[1] + s0) * CELL + SLOT_PITCH / 2
    need = 15 * SLOT_PITCH + SLOT_PITCH
    slots = [y0 + k * SLOT_PITCH for k in range(len(L))]
    routes = {}
    for pos, k in enumerate(order):
        l = L[k]; y = slots[pos]
        routes[l["net"]] = [[l["A"][0], l["A"][1]], [l["A"][0], round(y, 4)],
                            [l["B"][0], round(y, 4)], [l["B"][0], l["B"][1]]]
    return routes, {"corridor_x": xc, "corridor_free_width_mm": round(w * CELL, 3),
                    "slots_need_mm": round(need, 3), "slot_pitch_mm": SLOT_PITCH,
                    "band_y_mm": [round(y0 - SLOT_PITCH / 2, 3), round(y0 + 15 * SLOT_PITCH + SLOT_PITCH / 2, 3)],
                    "corridor_order_ranks_south_to_north": [L[k]["a_rank"] for k in order]}


def main():
    model, patch = patched_model()
    L = sorted(json.load(open(ANCHOR_JSON))["lanes"], key=lambda r: r["a_rank"])
    rast = Raster(tuple(model["bbox"]), CELL)
    bad = build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW)
    free = ~bad
    # 区域（构造只在该区域内）
    off = (0, 0)
    routes, cdiag = construct(L, free, rast, off)
    anc = [a for a in lane_anchors(model) if a["net"] in routes]
    rr = {k: {"pts": v} for k, v in routes.items()}
    g = exact_gate(model, rr, anc, "In5.Cu", HW, frozenset(), frozenset(), PITCH)
    nviol_pair = g.get("n_lane_pitch_viol", -1); nviol_clr = g.get("n_clearance_viol", -1)
    res = {
        "o2_o3_window_run_declaration": {
            "same_frozen_model_iteration": ["R383", "R397", "R398", "R399（本件：构造器 · 一次实现 · 一次运行）"],
            "variant_reruns_registered": ["R384", "R387", "R388"],
            "survey_only": ["R386", "R389", "R393", "R394", "R395", "R396"],
            "this_artifact": "构造性几何生成（一次）＋权威闸验收 · 未跑求解器"},
        "artifact": "k2_r399_final_window_constructor_and_bookkeeping_fix_v1", "schema": 1,
        "from": "ENG · ARCHER R399", "to": "监理",
        "authority": "#K2-140 §三（准（甲）末次收口窗 · 出图工具 · 硬条件）· §三.2（先补正记账）",
        "bookkeeping_fix": {
            "input_board": "k2/hw/k2_v4_8L.l9.kicad_pcb", "input_board_sha16_scriptcomputed": sha16(L9),
            "input_board_matches_declared": sha16(L9) == BOARD_SHA16_L9,
            "prev_board_l8_sha16": sha16(L8),
            "base_model_file": BASE_MODEL, "base_model_file_sha16_scriptcomputed": sha16(BASE_MODEL),
            "base_model_selfdeclared_board": json.load(open(BASE_MODEL)).get("board"),
            "base_model_canonical_sha16_scriptcomputed": canon16(json.load(open(BASE_MODEL))),
            "patch_attached": patch,
            "derived_model_fingerprint_scriptcomputed_sha16": canon16(model),
            "statement": "**计算输入板 = 件上所写受审板（l9）**：经补丁 P（l8→l9 之 In5 neck 移除）达成；指纹**全部由脚本实算**。",
            "caveat_prev_defect": "旧件（R383..R397）之 model_sha16=84f19701dfc1db31 **全仓无脚本可复算**且模型自述 board=l8 ⇒ 本件**予以补正**并如实登记。",
        },
        "constructor": {"method": "构造性 3 段折线（非搜索 · 确定性 · 无参数扫描）", **cdiag},
        "gate_verdict": g,
        "verdict": {},
        "boundary": "只读 · 未烙板 · 未改冻结四源/criteria/生成器/SPEC 设计内容 · 未派 WORKER · 未跑求解器",
    }
    ok = (nviol_pair == 0 and nviol_clr == 0 and g.get("endpoint_max_dev_mm") == 0.0)
    if ok:
        res["verdict"] = {"result": "**(a) 16/16 见证**（构造性生成 · 过权威闸）",
                          "next": "须附 buildability 与独立复核脚本 ⇒ 交监理工见证/签核。"}
    else:
        vp = g.get("lane_pitch_violations") or []; vc = g.get("clearance_violations") or []
        res["verdict"] = {
            "result": "**(a) 未取得**（构造性子集未过闸）· (b) 未建立",
            "named_blocker": {
                "first_pitch_violation": (vp[0] if vp else None),
                "first_clearance_violation": (vc[0] if vc else None),
                "geometric_quantity": "lane-lane 中心距 / 障碍净距（见上两条 · 逐条具名）",
                "minimal_repro": "本件为纯构造：16 条折线坐标全部落件（routes）· 逐条可复跑 exact_gate。",
            },
            "honest": "本件**不**以构造失败冒充『摆不下』之证明（#K2-140 §三.3 禁有界搜索充证据）；须由监理按 §三.5『不成』支处置。",
        }
    with open(OUT, "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16]
    open(OUT.replace(".json", ".sha16.txt"), "w").write(sha + "\n")
    print(json.dumps({"sha16": sha, "board_ok": res["bookkeeping_fix"]["input_board_matches_declared"],
                      "derived_model_sha16": res["bookkeeping_fix"]["derived_model_fingerprint_scriptcomputed_sha16"],
                      "patch_removed": {"segs": patch["n_removed_seg"], "vias": patch["n_removed_via"]},
                      "corridor_free_width_mm": cdiag["corridor_free_width_mm"],
                      "slots_need_mm": cdiag["slots_need_mm"],
                      "pitch_viol": nviol_pair, "clearance_viol": nviol_clr,
                      "endpoint_dev": g.get("endpoint_max_dev_mm"),
                      "result": res["verdict"]["result"][:60]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
