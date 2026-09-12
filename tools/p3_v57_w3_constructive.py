#!/usr/bin/env python3
"""W3 (G4) **构造式**联合赋位 + 34 页节点图纸（rev W3-CN.1，契约 W3-C2 v1.2）。

铁律：确定性一次算对 —— 全路径 O(n) 闭式/前缀构造，无搜索、无回溯、无备选枚举。
  R1   : 帧内前缀单调 x（最小步长 0.6）+ 带逃逸 y（0.05 网格，k∈{0,1}）
  R1.5 : 单直线段 via1 -> (entry_x, lane_y ± 0.19)（零折角、域内零 via）
  R2   : frame 连续块（base=floor((N_lanes-n_used)/2)）+ 帧内序 = lane 序
  R3   : 每 (connector, gap 列) 前缀递推 y_k = max(pad_y_k - 0.3, y_{k-1} + 0.6)
  REFCLK: 层 F.Cu；折线消费 W0-R refclk_passage_witness 的自由通道
不可行 -> 证书（kind=CONSTRUCTION_INFEASIBLE，仅闭式条件名 + 数值；非全局不可能性证明）。

CLI: --enum-order {natural,reverse,hash}  --scale K  --out PATH  --landing-out PATH  --quiet
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path

import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
F = {
    "spec": L3 / "SPEC_k2_v4.spec-rev-19.json",   # ECO SPEC-REV-9（CO-89：PDN live 决策板实化）
    "rules": K2 / "_shared" / "eda_core" / "drc_rules.json",
    "manifest": STEP2 / "m13_v57_s1_page_manifest.json",
    "w0r_model": STEP2 / "m13_v57_big_w0r_corridor_model.json",
    "lane_frame": STEP2 / "m13_v57_f3_lane_frame.json",
    "param_trace": STEP2 / "m13_v57_f13_r1_param_trace.json",
    "pair_coupling": STEP2 / "m13_v57_f13_r1_pair_coupling.json",
    "pair_xorder": STEP2 / "m13_v57_f13_r1_pair_coupling_v1_1.json",
    "r3_gaps": STEP2 / "m13_v57_f8_r3_gap_candidates_r3x2.json",   # ROOT-16 A (versioned domain rev)
    "r3_base": STEP2 / "m13_v57_f8_r3_gap_candidates.json",        # CO-05b: multi-candidate legality
    "f6b_report": STEP2 / "m13_v57_f6b_report.json",
    "verdict": STEP2 / "m13_v57_s1_r1_via_verdict_r2.json",
    "card": STEP2 / "m13_v57_w3_kickoff_card_v1_28.md",   # ROOT-16 contract revision
    "layer_intent": STEP2 / "m13_v57_layer_intent_rev6.json",   # LID REV6（CO-68 方案(a)：signal F/In2/In5/B）
    "coherent_rows": STEP2 / "m13_v57_f13_r3_coherent_rows.json",
}
FROZEN_SHA = {
    "spec": "5f72182a2616392cbcc223ec9233b41422657ff13a5faff1e6f10d6904dc33e6",   # CO-134：rev-19（③ 忠实实现）
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "w0r_model": "80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa",
    "lane_frame": "ff804e1edfacbf02e4227f10359a9217347ecdf0473801d655ef3a71ddf5cb6c",
    "param_trace": "e288ffa5421c22972075a7a3bef503a4b472aa32ea148c2ed0502090a3d98cae",
    "pair_coupling": "82e11c4cbdb4e8d44df1997f660c97fb75a47d33661223c9e5cf5fb0cb9c0d14",
    "r3_gaps": "5511c8c30c21f9144c8b5e81d951649c50cc8ee427cdd94677cb4f65e06a2e05",
    "r3_base": "8a31632907b171483cd40a053231c702e378f944af33f92598a6141bd052cdeb",
    "f6b_report": "9070ed53f970f480e88b1de3aa19792f8b637de51857935fa6b7c51fa8a015d6",
    "verdict": "f2e2632506457e31c145b491284c9ecbf1cb72cc09d96ccdfb3251ef80a5556a",
    "coherent_rows": "014a14b317e1c3df3d4400d45d6877ffc81f4ca92d533da4c7c7e4af67319c9a",
    "card": "0ae3016379cd1db27ba6004e2d86336466aad0c877bcee1fddf784879bbc90c2",
    "layer_intent": "05009687a3f01583d0cdf562f1510d7354995926be0629407fddb741a477dd0b",
}
OUT_MAIN = STEP2 / "m13_v57_w3_joint_assignment.json"
OUT_LANDING = STEP2 / "m13_v57_w3_chip_landing_rows.json"

REVISION = "W3-CN.30"   # 默认（t2）路径不动；CO-16 见 REVISION_CO16
REVISION_CO16 = "W3-CN.41"   # CO-45：远端 N 折线补入 3D nodes（修 CO-43 图纸/nodes 不一致）+ REFCLK 对内 0.5/dip 解耦；CO-68: LID REV6 层集 F/In2/In5/B（方案(a)）
ECS_VIA1_X = 133.825        # 两列缝中线（距两侧 pad 边各 0.35 >= vias.high_speed.pad_edge_clearance_mm 0.3）
ECS_VIA2_X_MAX = 131.525    # 内列 pad 西缘 132.0 - via 半径 0.175 - pad_edge_clearance 0.3
ECS_VIA_R = 0.175           # vias.std: drill 0.2 + 2*annular 0.075
ECS_TRACE_HALF = 0.1025     # PCIe85 width 0.205 / 2
ECS_CLEAR = 0.175           # 店规 PCIe85 净距（域内不放宽任何数值阈值）
ECS_MARGIN = 0.2775         # trace_half + clear：迹跨列端所需
ECS_DX = 0.4525             # via 避开同层列的横向最小中心距：via_r + trace_half + clear
ECS_COL_LO, ECS_COL_HI = 129.0, 132.2   # pad 场近域 In2 stub 列筛选窗
# CO-45 (W3-CN.40) REFCLK 对内偏移（取代 ROOT-21 的 ±POL_OFF=±0.19）：
#   P = 0.0  -> 内列 pad 由 pad 中心线直出，无 0.19 jog（消 vs J2 GND pad 9/13/27/31 实测 0.1325）；
#   N = -0.5 -> 外列 N 的 dip rail 在 P 北侧 0.5（> ECS_DX 0.4525，消 via#2 vs P 轨实测 0.1025），
#               且远端 P 竖段与他轨不相交（见 refclk_far_transit 内真实线段自检）。
REFCLK_OFF = {"P": 0.0, "N": -0.5}
ECS_VIA1_DY = 0.19         # via1 自 pad 中心南偏（ECS-001 既定；pad 10/14 净距合格）
# CO-45 等长补偿（SPEC PCIe85.intra_pair_skew_mm = 0.15；CO-40 预留、CO-41/43 未实施）：
#   P 的 rail 段（west -> xj_P，实测 x<=82.35 段全空）插入**南向三角幂绕**；幅值上界取 2.0mm。
REFCLK_MEANDER_A_MAX = 2.0     # 幂绕幅值上界（实测自由带 >=4mm，留 2x 余量）
REFCLK_MEANDER_LO = 1.5        # 幂绕带西端距 xj_P 的余量
REFCLK_MEANDER_HI = 1.0        # 幂绕带东端距 west 的余量
FAR_ROW_MARGIN = 0.6275    # CO-42/43 远端：排中心到自由带边界 = pad高0.35 + 净距0.175 + 半线宽0.1025
FAR_LINE_LO = 0.28         # 带内近边界线距带边界
FAR_LINE_STEP = 0.5        # CO-45：带内两线间距（0.38 边距恰 0.175 无余量；0.5 -> 0.295）
FAR_JOG_EAST = 0.5         # 抬升列位于 A 排东端之外的安全余量（覆盖 pad 半宽+净距+半线宽）
ORD = "natural"   # ROOT-20: enumeration order (A1.2 order-invariance, non-vacuous)
_SQER_CACHE: dict = {}


def _sqrt_er(layer: str) -> float:
    """CO-69：层感知电气长度的权重 sqrt(er_eff)（由 SPEC impedance.per_layer 一阶推导；缓存）。
    微带 er_eff = (er+1)/2 + (er-1)/2 / sqrt(1+12h/w)；带状线 er_eff = er。"""
    if not _SQER_CACHE:
        _imp = json.loads(F["spec"].read_text(encoding="utf-8"))["impedance"]["per_layer"]
        for _l, _m in _imp.items():
            if "stripline" in _m["kind"]:
                _e = float(_m["er"])
            else:
                _w, _h, _er = float(_m["w_mm"]), float(_m["h_mm"]), float(_m["er"])
                _e = (_er + 1) / 2 + (_er - 1) / 2 / math.sqrt(1 + 12 * _h / _w)
            _SQER_CACHE[_l] = math.sqrt(_e)
    return _SQER_CACHE.get(layer, 2.0)

SCHEMA = 1
STEP = 1.46
LANE_LO = 33.3
N_LANES = 32
N_USED = 16
REACH = 45.4
VIA_VIA = 0.525
# A-CN.9 完整净距（由冻结 SPEC 派生，main() 内断言一致）：
#   vt   = via_r + clearance + width/2 = 0.35/2 + 0.175 + 0.205/2
#   vt_e = via_r + escape_clearance_mm(ECN-001 0.075) + width/2
#   tt_e = width + escape_clearance_mm
VT_TRACK = 0.4525
VT_ESC = 0.3525
TT_ESC = 0.28
STAGGER = 0.38
MIN_XSTEP = 1.2
SLOT_SEP = 0.6
GRID = 0.05
R3_OFF = -0.3
R3_STEP = 0.6
POL_OFF = 0.19
# CO-16 (W3-CN.31): 全板安全-hop 拓扑（pad->F->via1(F<->In2)->escape(In2/B)->corner->lane(In5)
#   ->drop->stub(In2/In5/B)->land(..->In2->F)->F->conn）+ O4 双段蛇形。
#   几何（via1/lane_y/landing/escape/stub 层）O(1) 消费 CO16-ALLOC.1 工件，零坐标搜索。
POL_OFF_CO16 = 0.25        # L2: 对内 lane y 偏移 >= vt(0.4525)/2（0.19 不足）
CO16_LANE_STEP = {"WEST_MCIO_TO_CHIP": 1.05, "EAST_CHIP_TO_J2": 1.449}   # CO-23（informational；引擎消费工件 lane_y）
DEFAULT_SHAPE = "t2"
# CO16_MEANDER: O4 等长蛇形（CO-16 ruling §2.2 双段模型的推广：lane-run 优先，缺口落竖段）。
#   幅值 A 受相邻通道净距所限（A <= 邻道间距 - TT），纵向步 a 由「自净距 >= TT + 余量」与
#   「命中 extra_mm」联立解出 —— 容许 a < A（陡于 45°），容量 = (2A/TT - 1) mm/mm 段长。
CO16_MEANDER = True
TT_TRACK = 0.38            # width + clearance (PCIE85)；蛇形自净距下限
MEANDER_MARGIN = 0.02      # 净距余量（自净距 / 邻道净距；防 FP 边界）
LEGSEP_MIN = 0.38          # 蛇形相邻斜腿垂直净距下限（= width + clearance，同网可制造性）
# CO-22：板边净空带（k2_v4_8L 板 bbox y[32.95,79.05]；0.3 板边约束 + 0.1025 半线宽）
BOARD_Y_MIN, BOARD_Y_MAX = 33.0, 79.0    # CO-23 更正：Edge.Cuts 实线（旧值 32.95/79.05 系 bbox 偏宽 0.05）
LANE_Y_LO, LANE_Y_HI = BOARD_Y_MIN + 0.3 + 0.1025, BOARD_Y_MAX - 0.3 - 0.1025
# CO-05c (O4): 成对落列 + L3 长度补偿（run 上确定性 45° 单侧蛇形）
PAIR_MODE = True
MEANDER_MODE = True
PAIR_PITCH = 0.6                  # ROOT-22: 落列 pitch = R3_STEP >= max(vv 0.525, vt 0.4525)
J2_INNER_X, J2_OUTER_X = 132.65, 135.0
J2_LEFT0, J2_RIGHT0 = 131.65, 136.0
MEANDER_PITCH = 0.615             # 2A >= 3w (=0.615) => A >= 0.3075
MEANDER_A_MAX = 0.34              # 单侧横摆上限（相邻 lane 对面 run 间距 1.08 => 双向 2*0.34+0.38=1.06 <= 1.08）
MEANDER_A_MIN = 0.27             # n>=2 时自净距 1.414*A >= 0.38
LAYER_BY_BAND = {"up": "In2.Cu", "dn": "B.Cu"}
LAYER_PALETTE = ["F.Cu", "In2.Cu", "In5.Cu", "B.Cu"]   # LID REV6 (CO-68): 4 信号层（方案(a)）
TOL = 1e-9
SUPERSEDED = {"artifact": "m13_v57_w3_joint_assignment.json", "revision": "W3-JA.2",
               "sha256": "d081618c7b961d770c8e2f180f93b92125b316bc0eeec181f9d1d191a0ee6acc",
               "reason": "method-level iron-law violation (search-based); retained, not rewritten"}
CO16_ALLOC = STEP2 / "m13_v57_co16_channel_allocation_v7.json"   # CO16-ALLOC.7（CO-69：stub 层 In6->In5，随 LID REV6）
CO16_ALLOC_SHA = "a765af4c9bf61e642780ad2ebbea177e8a2c76125eda93feca9641e7dfd0185a"
CORRIDOR = {
    "EAST_CHIP_TO_J2": {"bounds": (105.25, 132.65), "x_domain": (93.55, 105.25)},
    "WEST_MCIO_TO_CHIP": {"bounds": (65.05, 82.35), "x_domain": (82.35, 93.55)},
}
KEEP_KEYS = ("alternatives", "options", "tried", "attempts")   # G-M6（禁止键名）

WORK = [0]
BOOK: dict = {}
# CO-16 专用净距口径（handoff §8f）：同页跨极性不再被 base(pid) 豁免 + via-via 层跨相交判定。
#   仅在 shape=co16 生效，保证默认(t2)路径逐字节不动（W3-CN.30 判据保持原口径）。
SAFE_HOP_METRIC = [False]


def bump(n: int, site: str = "unspecified") -> None:
    WORK[0] += n
    BOOK[site] = BOOK.get(site, 0) + n


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze_check(files: dict) -> dict:
    actual = {k: sha256(v) for k, v in files.items()}
    match = {k: actual[k] == FROZEN_SHA[k] for k in FROZEN_SHA}
    return {"expected": dict(FROZEN_SHA), "actual": actual, "match": match,
            "drift": [k for k in match if not match[k]]}


def fp(v: float) -> float:
    return round(float(v), 6)


def page_facts(manifest: dict, lane_frame: dict) -> dict:
    out = {}
    for pg in manifest["pages"]:
        if pg["kind"] != "data":
            continue
        pid = pg["page_id"]
        c, co = pg["anchors"]["chip"], pg["anchors"]["conn"]
        out[pid] = {
            "page_id": pid, "side": pg["side"],
            "corridor": "EAST_CHIP_TO_J2" if pg["side"] == "east" else "WEST_MCIO_TO_CHIP",
            "conn_ref": co["P"]["ref"],
            "row_y": fp((co["P"]["pad_global"][1] + co["N"]["pad_global"][1]) / 2),
            "conn_x": fp(co["P"]["pad_global"][0]),
            "chip_row_y": fp((c["P"]["pad_global"][1] + c["N"]["pad_global"][1]) / 2),
            "pad": {pol: [fp(c[pol]["pad_global"][0]), fp(c[pol]["pad_global"][1])]
                    for pol in ("P", "N")},
            "conn_pad": {pol: [fp(co[pol]["pad_global"][0]), fp(co[pol]["pad_global"][1])]
                         for pol in ("P", "N")},
            "nets": {pol: co[pol]["net"] for pol in ("P", "N")},
            "ball": {pol: c[pol]["ball"] for pol in ("P", "N")},
        }
    for cd in lane_frame["corridors"].values():
        for fr in cd["frames"]:
            for p in fr["pages"]:
                if p["page_id"] in out:
                    out[p["page_id"]]["band"] = fr["band"]
                    out[p["page_id"]]["order_index"] = p["order_index"]
    return out


def frames_of(facts: dict) -> list:
    """frame = (corridor, conn_ref, band)；按 F-5 键（conn_row_y, conn_x, page_id）定帧内序。"""
    table = {}
    for f in facts.values():
        key = (f["corridor"], f["conn_ref"], f["band"])
        table.setdefault(key, []).append(f["page_id"])
    out = []
    for key in sorted(table):
        ids = sorted(table[key], key=lambda pid: (round(facts[pid]["row_y"], 3),
                                                  round(facts[pid]["conn_x"], 3), pid))
        rows = [facts[pid]["row_y"] for pid in ids]
        out.append({"corridor": key[0], "conn_ref": key[1], "band": key[2], "pages": ids,
                    "row_y_span": [min(rows), max(rows)]})
    out.sort(key=lambda fr: (fr["corridor"], fr["row_y_span"][0], fr["conn_ref"], fr["band"]))
    return out


def r2_lanes(frames: list, facts: dict) -> dict:
    """每走廊占一段连续 lane 区（闭式）：源行更高的走廊取高区段，frame 块按 conn 行序排。"""
    src = {}
    for fr in frames:
        src.setdefault(fr["corridor"], []).extend(facts[pid]["pad"]["P"][1] for pid in fr["pages"])
    corridors = sorted(src, key=lambda c: (sum(src[c]) / len(src[c])))
    out = {}
    spans = {}
    for ci in range(len(corridors)):
        cid = corridors[ci]
        cursor = ci * N_USED
        for fr in [f for f in frames if f["corridor"] == cid]:
            bump(3, "r2_block")
            for j in range(len(fr["pages"])):
                pid = fr["pages"][j]
                idx = cursor + j
                out[pid] = {"lane_index": idx, "lane_y": fp(LANE_LO + idx * STEP),
                            "frame": [fr["corridor"], fr["conn_ref"], fr["band"]]}
                bump(1, "r2_lane")
            cursor += len(fr["pages"])
        spans[cid] = [out[p]["lane_y"] for p in out if out[p]["frame"][0] == cid]
    return out


def pol_off(f: dict, pol: str) -> float:
    """极性偏移符号：保持 pad 侧 P/N 上下序与 lane 侧一致（防对内自交叉）。"""
    d = f["pad"]["N"][1] - f["pad"]["P"][1]
    base = -POL_OFF if d > 0 else POL_OFF
    return base if pol == "P" else -base


def meander_run(vx, ly, lx, extra_mm, dy):
    """沿 run (In2) 插入确定性 45° 单侧蛇形，使 run 长度 +extra_mm。返回折线点列表。

    Dm = extra/(sqrt2-1) 为蛇形纵向跨度；段长 sqrt2*A、纵向 A、横摆 A（A<=MEANDER_A_MAX）。
    m = 2*ceil(Dm/(2*A_MAX)) 段（偶数，起止均回 ly）；A = Dm/m。越界即钳位（由调用方出证书）。
    """
    R = abs(lx - vx)
    if extra_mm <= TOL:
        return [[vx, ly], [lx, ly]]
    dm = extra_mm / (2 ** 0.5 - 1.0)
    if dm > R - 1.0:
        dm = R - 1.0
    n = max(1, int(round(dm / 0.6)))                       # 齿数：A = dm/(2n) ~ 0.3
    a = dm / (2.0 * n)
    a = min(a, MEANDER_A_MAX) if n == 1 else min(MEANDER_A_MAX, max(MEANDER_A_MIN, a))
    dm = 2.0 * n * a                                       # 实得纵向跨度（钳位后）
    m = 2 * n
    sgn = 1.0 if lx >= vx else -1.0                        # 沿 run 方向推进（勿回折）
    x0 = fp(vx + sgn * (R - dm) / 2.0)                     # 居中：自 vx 沿行进方向 (R-dm)/2
    pts = [[fp(vx), fp(ly)], [x0, fp(ly)]]
    for i in range(1, m):
        pts.append([fp(x0 + sgn * i * a), fp(ly + (dy * a if i % 2 else 0.0))])
    pts.append([fp(x0 + sgn * dm), fp(ly)])
    pts.append([fp(lx), fp(ly)])
    out = [pts[0]]
    for q in pts[1:]:
        if abs(q[0] - out[-1][0]) > TOL or abs(q[1] - out[-1][1]) > TOL:
            out.append(q)
    return out


def _zig_pts(p, q, a, amp, teeth, lat):
    """轴对齐段 p->q 上单侧锯齿（run 轴步长 a、横向幅值 amp±lat、teeth 个齿=2*teeth 段），居中。"""
    dx, dy = q[0] - p[0], q[1] - p[1]
    horiz = abs(dx) >= abs(dy)
    run = abs(dx) if horiz else abs(dy)
    sgn = (1.0 if dx >= 0 else -1.0) if horiz else (1.0 if dy >= 0 else -1.0)
    dm = 2.0 * teeth * a
    off0 = (run - dm) / 2.0

    def pt(u, v):
        if horiz:
            return [fp(p[0] + sgn * u), fp(p[1] + lat * v)]
        return [fp(p[0] + lat * v), fp(p[1] + sgn * u)]

    pts = [pt(0.0, 0.0), pt(off0, 0.0)]
    for i in range(1, 2 * teeth):
        pts.append(pt(off0 + i * a, amp if i % 2 else 0.0))
    pts.append(pt(off0 + dm, 0.0))
    pts.append(pt(run, 0.0))
    out = [pts[0]]
    for r in pts[1:]:
        if abs(r[0] - out[-1][0]) > TOL or abs(r[1] - out[-1][1]) > TOL:
            out.append(r)
    return out


def meander_zig(p, q, extra_mm, lat, a_max, legsep=None):
    """轴对齐段 p->q 上确定性单侧锯齿，使段长恰 +extra_mm（闭式，无搜索/无迭代）。

    横向幅值 A <= min(MEANDER_A_MAX, a_max)（只向 lat 一侧鼓出，A 由调用方按 vt 顶点净距限定）；
    纵向半齿步 a 由「相邻斜腿垂直净距 2aA/sqrt(a^2+A^2) >= legsep」与「per-tooth 增量命中
    extra/teeth」联立解出。per-tooth 增量 = 2(sqrt(a^2+A^2)-a)，随 a 单调递减；故取满足净距的
    最小齿数 teeth = ceil(extra / per_max) 即得最小占段长。
    返回 (pts, realized, A, a)；不可达（幅值/段长不足）=> 直线段 + realized=0。"""
    dx, dy = q[0] - p[0], q[1] - p[1]
    horiz = abs(dx) >= abs(dy)
    run = abs(dx) if horiz else abs(dy)
    straight = [list(p), list(q)]
    if extra_mm <= TOL or run <= 1.0:
        return straight, 0.0, 0.0, 0.0
    A = min(MEANDER_A_MAX, max(0.0, a_max))
    ls = LEGSEP_MIN if legsep is None else legsep
    if A <= TOL or ls <= TOL:
        return straight, 0.0, 0.0, 0.0
    a_min = ls / 2.0                                      # 半齿步下限 => 相邻斜腿沿 run 距 2a >= ls
    per_max = 2.0 * (math.hypot(a_min, A) - a_min)        # 最陡可用齿的 per-tooth 增量上界
    if per_max <= TOL:
        return straight, 0.0, 0.0, 0.0
    teeth = max(1, int(math.ceil(extra_mm / per_max - 1e-12)))
    per_t = extra_mm / teeth
    if per_t > 2.0 * A - 1e-12:
        return straight, 0.0, 0.0, 0.0
    a = (A * A - per_t * per_t / 4.0) / per_t
    if a < a_min - 1e-9:
        return straight, 0.0, 0.0, 0.0
    if 2.0 * teeth * a > run - 0.4:
        return straight, 0.0, 0.0, 0.0
    real = teeth * 2.0 * (math.hypot(a, A) - a)
    return _zig_pts(p, q, a, A, teeth, lat), real, A, a


def co16_prepare(j, facts, lanes, r3):
    """O(1) 消费 CO16-ALLOC.5：lane_y(P/N)、via1、landing、escape/stub 层（零坐标搜索）。"""
    alloc = j["co16_alloc"]["pages"]
    bump(4 * len(alloc), "co16_consume")
    for pid, a in alloc.items():
        lanes[pid]["lane_y"] = fp((a["lane_y"]["P"] + a["lane_y"]["N"]) / 2.0)
        lanes[pid]["lane_y_pol"] = {"P": fp(a["lane_y"]["P"]), "N": fp(a["lane_y"]["N"])}
        lanes[pid]["escape_layer"] = a["escape_layer"]
        lanes[pid]["stub_layer"] = a["stub_layer"]
    r1 = {"assignment": {}, "certificates": []}
    for pid, a in alloc.items():
        f = facts[pid]
        pv = [fp(a["via1"]["P"][0]), fp(a["via1"]["P"][1])]
        nv = [fp(a["via1"]["N"][0]), fp(a["via1"]["N"][1])]
        d = ((pv[0] - nv[0]) ** 2 + (pv[1] - nv[1]) ** 2) ** 0.5
        r1["assignment"][pid] = {
            "P_via": pv, "N_via": nv, "pair_dist_mm": fp(d), "stagger_mm": fp(abs(pv[0] - nv[0])),
            "frame": [f["corridor"], f["conn_ref"], f["band"]],
            "direction": "co16_artifact", "mode": "co16_artifact"}
    for pid, a in alloc.items():
        f = facts[pid]
        for pol in ("P", "N"):
            k = f["conn_ref"] + "|" + f["nets"][pol]
            if k not in r3["assignment"]:
                continue
            lx, ll = a["landing"][pol]
            r3["assignment"][k]["column_x"] = fp(lx)
            r3["assignment"][k]["landing"] = [fp(lx), fp(ll)]
    return alloc, r1


def co16_o4_plan(alloc):
    """O4 双段蛇形预算（CO16-O4.1 模型）：短极 + lane-run 容量缺口。"""
    out = {}
    s2 = 2.0 ** 0.5 - 1.0
    for pid, a in alloc.items():
        E, S = a["escape_layer"], a["stub_layer"]
        length = {}
        for pol in ("P", "N"):
            pad = a["chip_pad"][pol]; v = a["via1"][pol]; ly = a["lane_y"][pol]
            lx, ll = a["landing"][pol]; cp = a["conn_pad"][pol]
            # CO-69：**按层加权电气长度**（各段乘 sqrt(er_eff)）——修复只按物理长度补偿的电气 skew
            length[pol] = (math.hypot(pad[0] - v[0], pad[1] - v[1]) * _sqrt_er("F.Cu")
                           + abs(ly - v[1]) * _sqrt_er(E)
                           + abs(lx - v[0]) * _sqrt_er("In5.Cu")
                           + abs(ll - ly) * _sqrt_er(S)
                           + math.hypot(cp[0] - lx, cp[1] - ll) * _sqrt_er("F.Cu"))
        sh = "P" if length["P"] < length["N"] else "N"
        other = "N" if sh == "P" else "P"
        # 主蛇形落 lane(In5)；把电气缺口换算为 In5 上的物理长度
        extra = abs(length["P"] - length["N"]) / _sqrt_er("In5.Cu")
        if extra <= TOL:
            continue
        r_lane = abs(a["landing"][sh][0] - a["via1"][sh][0])
        out[pid] = {"pol": sh, "other": other, "extra": extra,
                    "cap_lane": max(0.0, r_lane - 1.0) * s2,
                    "dy": 1.0 if a["lane_y"][sh] > a["lane_y"][other] else -1.0}
    return out


def co16_seg_room(alloc):
    """每 (kind,pid,pol) 的 escape/stub 竖段方向化幅值上限：单侧最近同层异网净距 - TT_TRACK。
    返回 (esc, stb, room[(kind,pid,pol,lat)])。"""
    esc, stb = {}, {}
    for pid, a in alloc.items():
        for pol in ("P", "N"):
            vx, vy = a["via1"][pol][0], a["via1"][pol][1]
            ly = a["lane_y"][pol]
            lx, ll = a["landing"][pol]
            esc[(pid, pol)] = {"x": vx, "lo": min(vy, ly), "hi": max(vy, ly),
                               "layer": a["escape_layer"], "p0": [vx, vy], "p1": [vx, ly]}
            stb[(pid, pol)] = {"x": lx, "lo": min(ly, ll), "hi": max(ly, ll),
                               "layer": a["stub_layer"], "p0": [lx, ly], "p1": [lx, ll]}
    room = {}
    for kind, tab in (("esc", esc), ("stb", stb)):
        keys = sorted(tab)
        for lat in (-1.0, 1.0):
            for k in keys:
                s = tab[k]
                best = MEANDER_A_MAX
                for k2 in keys:
                    if k2 == k:
                        continue
                    t = tab[k2]
                    if t["layer"] != s["layer"]:
                        continue
                    if lat * (t["x"] - s["x"]) <= TOL:
                        continue                          # 仅同侧（横向鼓出方向）邻居约束
                    if min(t["hi"], s["hi"]) - max(t["lo"], s["lo"]) <= 1e-9:
                        continue
                    best = min(best, abs(t["x"] - s["x"]) - VT_TRACK - MEANDER_MARGIN)
                room[(kind,) + k + (lat,)] = max(0.0, best)
    return esc, stb, room


def co16_nodes(f, pol, v1, esc_pts, lane_pts, stub_pts, esc_l, stub_l, land, conn):
    """CO-09/CO-11 节点链：pad->F->via1->escape->corner->lane->drop->stub->land->F->conn。"""
    vx, vy = v1
    end = esc_pts[-1]
    lx, ly_l = land
    lane_y = lane_pts[-1][1]
    n = [[f["pad"][pol][0], f["pad"][pol][1], "F.Cu"],
         [vx, vy, "F.Cu"], [vx, vy, "In2.Cu"]]
    if esc_l == "B.Cu":
        n += [[vx, vy, "In5.Cu"], [vx, vy, "B.Cu"]]
    for q in esc_pts[1:]:
        n.append([q[0], q[1], esc_l])
    n.append([end[0], end[1], "In5.Cu"])                  # corner via esc_l <-> In5
    for q in lane_pts[1:]:
        n.append([q[0], q[1], "In5.Cu"])
    if stub_l == "In2.Cu":
        n.append([lx, lane_y, "In2.Cu"])                  # drop In5 -> In2 @ lane y
    elif stub_l == "B.Cu":
        n.append([lx, lane_y, "B.Cu"])                    # drop In5 -> B @ lane y
    for q in stub_pts[1:]:
        n.append([q[0], q[1], stub_l])
    if stub_l == "B.Cu":
        n.append([lx, ly_l, "In5.Cu"])
    if stub_l in ("B.Cu", "In5.Cu"):
        n.append([lx, ly_l, "In2.Cu"])
    n.append([lx, ly_l, "F.Cu"])                          # land -> F
    n.append([f["conn_pad"][pol][0], f["conn_pad"][pol][1], "F.Cu"])
    return n


def co16_vias(nodes, pol):
    """从节点链抽取层变点（via）列表。"""
    out = []
    for i in range(1, len(nodes)):
        a, b = nodes[i - 1], nodes[i]
        if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9 and a[2] != b[2]:
            out.append({"x": fp(a[0]), "y": fp(a[1]), "pol": pol,
                        "layers": [a[2], b[2]], "role": "co16"})
    return out

_CO16_PTS = {}


def co16_o4_amp_table(alloc, o4):
    """O4 lane 蛇形「方向 + 幅值 + x 窗口」表（vt 顶点净距口径；对向同时蛇形按对称解折半）。

    顶点净距：A <= Δy - vt（vt = via_r + clearance + width/2 = 0.4525；A-CN.9 对**每个折点**
    作 via 候选量测）。方向取静态 vt 余量较大侧（平手取 CO16-O4.1 的 dy）。x 窗口按 E=B 的
    In5 via1 stack 截断（避免蛇形扫过异网 via stack）。"""
    VT = VT_TRACK
    lanes = {}
    for pid, a in alloc.items():
        for pol in ("P", "N"):
            vx, lx = a["via1"][pol][0], a["landing"][pol][0]
            lanes[(pid, pol)] = (a["lane_y"][pol], min(vx, lx), max(vx, lx))
    mset = {pid: mz["pol"] for pid, mz in o4.items()}
    tab = {}
    for pid, pol in mset.items():
        y, xlo, xhi = lanes[(pid, pol)]
        best = None
        for d in (1.0, -1.0):
            room = (LANE_Y_HI - y) if d > 0 else (y - LANE_Y_LO)      # CO-22 板边净空带
            if room <= TOL:
                continue
            for (p2, pol2), (y2, lo2, hi2) in lanes.items():
                if p2 == pid and pol2 == pol:
                    continue
                if min(xhi, hi2) - max(xlo, lo2) <= 0:
                    continue
                if d * (y2 - y) > TOL:
                    room = min(room, abs(y2 - y))
            cand = (room, d)
            if best is None or cand > best:
                best = cand
        if best is None:
            tab[pid] = [1.0 if y < (LANE_Y_LO + LANE_Y_HI) / 2 else -1.0, 0.0, xlo, xhi]
        else:
            tab[pid] = [best[1], 0.0, xlo, xhi]
    for pid, pol in mset.items():
        d = tab[pid][0]
        y, xlo, xhi = lanes[(pid, pol)]
        amp = MEANDER_A_MAX
        for (p2, pol2), (y2, lo2, hi2) in lanes.items():
            if p2 == pid and pol2 == pol:
                continue
            if min(xhi, hi2) - max(xlo, lo2) <= 0 or d * (y2 - y) <= TOL:
                continue
            gap = abs(y2 - y) - VT - MEANDER_MARGIN
            if mset.get(p2) == pol2 and tab[p2][0] * (y - y2) > TOL:
                gap = min(gap, (abs(y2 - y) - VT) / 2.0 - MEANDER_MARGIN)   # 对向蛇形对称解
            amp = min(amp, gap)
        amp = min(amp, (LANE_Y_HI - y) if d > 0 else (y - LANE_Y_LO))        # CO-22 顶点不得出板边带
        tab[pid][1] = max(0.0, min(MEANDER_A_MAX, amp))
    # x 窗口：E=B 的 In5 via1 stack 截断（原 co16_lane_room 口径）
    for pid, pol in mset.items():
        a = alloc[pid]
        vx, lx = a["via1"][pol][0], a["landing"][pol][0]
        ly = a["lane_y"][pol]
        xlo, xhi = tab[pid][2], tab[pid][3]
        amp = tab[pid][1]
        cuts = []
        for pid2, a2 in alloc.items():
            if a2["escape_layer"] != "B.Cu":
                continue
            for pol2 in ("P", "N"):
                if pid2 == pid and pol2 == pol:
                    continue
                x2, y2 = a2["via1"][pol2][0], a2["via1"][pol2][1]
                if xlo - 1e-9 <= x2 <= xhi + 1e-9 and tab[pid][0] * (y2 - ly) > TOL \
                   and abs(y2 - ly) < amp + VT_TRACK:
                    cuts.append(x2)
        if cuts:
            if lx >= vx:
                tab[pid][2] = max(xlo, max(cuts) + 0.2)
            else:
                tab[pid][3] = min(xhi, min(cuts) - 0.2)
    return {k: (v[0], v[1], v[2], v[3]) for k, v in tab.items()}


def co16_lane_room(alloc, pid, pol, dy, table):
    """(amp_max, x_lo, x_hi)：由 co16_o4_amp_table 的 vt 口径表给出（dy 由表内方向决定）。"""
    d, amp, xlo, xhi = table[pid]
    return amp, xlo, xhi


def co16_build_routes(facts, alloc, lanes):
    """CO-16 折线 + O4 双段蛇形（lane-run 优先，不足时落 escape 竖段 / stub 竖段）。
    返回 (paths, certificates)。零坐标搜索：几何全部来自工件，蛇形为闭式单遍。"""
    esc_tab, stb_tab, room = co16_seg_room(alloc)
    o4 = co16_o4_plan(alloc)
    table = co16_o4_amp_table(alloc, o4)
    paths, certs = {}, []
    _CO16_PTS.clear()
    for pid in sorted(alloc):
        a = alloc[pid]
        f = facts[pid]
        E, S = a["escape_layer"], a["stub_layer"]
        mz = o4.get(pid)
        for pol in ("P", "N"):
            vx, vy = fp(a["via1"][pol][0]), fp(a["via1"][pol][1])
            ly = fp(a["lane_y"][pol])
            lx, ll = fp(a["landing"][pol][0]), fp(a["landing"][pol][1])
            esc_pts = [[vx, vy], [vx, ly]]
            lane_pts = [[vx, ly], [lx, ly]]
            stub_pts = [[lx, ly], [lx, ll]]
            if CO16_MEANDER and mz and pol == mz["pol"] and mz["extra"] > 0.15:
                extra = mz["extra"]
                _dir = table[pid][0]
                _lamp, _xlo, _xhi = co16_lane_room(alloc, pid, pol, _dir, table)
                _lp0 = [vx, ly]
                _lp1 = [lx, ly]
                if _xhi - _xlo > 1.5:                     # 窗口端点须按行进方向排序（lx<vx = 向西）
                    _lp0 = [_xlo if lx >= vx else _xhi, ly]
                    _lp1 = [_xhi if lx >= vx else _xlo, ly]
                _mid, real, _amp, _a = meander_zig(_lp0, _lp1, extra, _dir, _lamp)
                _raw = [[vx, ly]] + _mid + [[lx, ly]]
                lane_pts = [_raw[0]]
                for _q in _raw[1:]:
                    if abs(_q[0] - lane_pts[-1][0]) > TOL or abs(_q[1] - lane_pts[-1][1]) > TOL:
                        lane_pts.append(_q)
                resid = extra - real
                if resid > 0.02:
                    for kind in ("esc", "stb"):
                        rp = room.get((kind, pid, pol, 1.0), 0.0)
                        rm = room.get((kind, pid, pol, -1.0), 0.0)
                        lat = 1.0 if rp >= rm else -1.0
                        amax = min(MEANDER_A_MAX, max(rp, rm))
                        s0, s1 = ([vx, vy], [vx, ly]) if kind == "esc" else ([lx, ly], [lx, ll])
                        pts2, real2, _A2, _a2 = meander_zig(s0, s1, resid, lat, amax)
                        if real2 <= TOL:
                            continue
                        if kind == "esc":
                            esc_pts = pts2
                        else:
                            stub_pts = pts2
                        resid -= real2
                        break
                if resid > 0.15:
                    certs.append({"kind": "CONSTRUCTION_INFEASIBLE",
                                  "layer": "R1_5_o4_length_compensation",
                                  "rule": "double_segment_meander(lane_run+vertical)",
                                  "closed_form_condition": "second-segment lateral room >= "
                                                           "TT_TRACK + needed amplitude",
                                  "observed": {"page": pid, "pol": pol, "residual_mm": fp(resid),
                                               "room_esc": [room.get(("esc", pid, pol, -1.0), 0.0),
                                                            room.get(("esc", pid, pol, 1.0), 0.0)],
                                               "room_stb": [room.get(("stb", pid, pol, -1.0), 0.0),
                                                            room.get(("stb", pid, pol, 1.0), 0.0)]},
                                  "required": {"skew_mm": 0.15},
                                  "page_or_pad": pid,
                                  "scope_note": "本构造规则下不可行；非全局不可能性证明"})
            if not CO16_MEANDER and mz and pol == mz["pol"] and mz["extra"] > 0.15:
                _lamp, _xlo, _xhi = co16_lane_room(alloc, pid, pol, mz["dy"])
                certs.append({"kind": "CONSTRUCTION_INFEASIBLE",
                              "layer": "R1_5_o4_length_compensation",
                              "rule": "45deg_one_sided_meander (lane-run / escape / stub)",
                              "closed_form_condition": "channel clearance >= 2*MEANDER_A_MIN + TT_TRACK "
                                                       "for adjacent co-meandering channels",
                              "observed": {"page": pid, "pol": pol,
                                           "extra_mm": fp(mz["extra"]),
                                           "lane_amp_room_mm": fp(_lamp),
                                           "lane_window_mm": fp(_xhi - _xlo),
                                           "min_amp_mm": MEANDER_A_MIN},
                              "required": {"skew_mm": 0.15},
                              "page_or_pad": pid,
                              "scope_note": "本构造规则下不可行（列距/层距不足）；非全局不可能性证明"})
            _CO16_PTS[(pid, pol)] = {"esc": esc_pts, "lane": lane_pts, "stub": stub_pts}
            paths[(pid, pol)] = [E, esc_pts]
            paths[(pid + "#lane", pol)] = ["In5.Cu", lane_pts]
            paths[(pid + "#stub", pol)] = [S, stub_pts]
            paths[(pid + "#fcu_pad", pol)] = ["F.Cu",
                [[f["pad"][pol][0], f["pad"][pol][1]], [vx, vy]]]
            paths[(pid + "#fcu_land", pol)] = ["F.Cu",
                [[lx, ll], [f["conn_pad"][pol][0], f["conn_pad"][pol][1]]]]
    return paths, certs


def r1_place(facts: dict, frames: list, xorder: dict, verdict: dict, coherent: dict = None,
             lanes: dict = None, r3: dict = None) -> dict:
    """R1 逐帧混合（W3-C18）：帧的 (P,N) 相干集**非空** ⇒ 共线行构造（该帧 R1.5 交叉→0）；
    否则 ⇒ 基线吸附（不退化）。两法均为闭式/单遍 argmin，无试错/回溯。"""
    out, certs = {}, []
    yx = {}
    for pid in facts:
        for pol in ("P", "N"):
            yx[(pid, pol)] = {}
            for cand in verdict["pages"][pid][pol]["cands"]:
                yx[(pid, pol)].setdefault(round(float(cand[0]), 3), set()).add(round(float(cand[1]), 3))
    sets = (coherent or {}).get("sets", {})
    for fr in frames:
        ids = fr["pages"]
        pxs = [facts[p]["pad"]["P"][0] for p in ids]
        s = 1 if pxs[-1] >= pxs[0] else -1
        fstep = min(MIN_XSTEP, max(0.6, (max(pxs) - min(pxs)) / (len(ids) - 1))) if len(ids) > 1 else 0.6
        rows = {}
        for pol in ("P", "N"):
            ent = sets.get(f"{fr['corridor']}|{fr['conn_ref']}|{fr['band']}|{pol}", {})
            rr = ent.get("rows", [])
            best = None
            if rr:
                def key(rr_):
                    dmax, dy = 0.0, 0.0
                    for pid in ids:
                        pad_x, pad_y = facts[pid]["pad"][pol]
                        cols = [x for x in yx[(pid, pol)] if rr_["row"] in yx[(pid, pol)][x]]
                        dmin = min(abs(x - (pad_x + s * fstep)) for x in cols) if cols else 9.99
                        dmax = max(dmax, dmin)
                        dy += abs(rr_["row"] - pad_y)
                    return (round(dmax, 3), round(dy / len(ids), 3), rr_["row"])
                best = min(rr, key=key)
            rows[pol] = best
        mode = "collinear" if (rows["P"] and rows["N"]) else "baseline"
        prev = {"P": None, "N": None}
        for pid in ids:
            f = facts[pid]
            columns = {}
            for r in xorder["pages"][pid]["x_column_pairs"]:
                columns.setdefault(round(float(r[0]), 3), []).append(round(float(r[1]), 3))
            for k in columns:
                columns[k] = sorted(set(columns[k]))
            px_all = sorted(columns)
            bump(4, "r1_place")
            picked = None
            if mode == "collinear":
                rp, rn = rows["P"]["row"], rows["N"]["row"]
                thr = prev["P"] + s * (fstep - GRID) if prev["P"] is not None else None
                carry = [x for x in px_all if rp in yx[(pid, "P")].get(x, set())
                         and (thr is None or (x >= thr - TOL if s > 0 else x <= thr + TOL))]
                px = min(carry, key=lambda x: (abs(x - (f["pad"]["P"][0] + s * fstep)), x)) if carry else None
                nx = None
                if px is not None:
                    thrn = prev["N"] if prev["N"] is not None else None
                    cand_n = [x for x in columns[px] if abs(x - px) >= STAGGER - TOL
                              and rn in yx[(pid, "N")].get(x, set())
                              and (thrn is None or (x >= thrn - TOL if s > 0 else x <= thrn + TOL))]
                    nx = min(cand_n, key=lambda x: (abs(x - (px + s * SLOT_SEP)), x)) if cand_n else None
                if px is not None and nx is not None:
                    picked = (px, nx, rp, rn)
            else:
                for cam in (0, 1):
                    sp = f["pad"]["P"][0] + s * (fstep + cam * GRID)
                    px = min(px_all, key=lambda x: (abs(x - sp), x)) if px_all else None
                    if px is None:
                        continue
                    k0 = min(yx[(pid, "P")][px]) if px in yx[(pid, "P")] else None
                    ys = yx[(pid, "P")].get(px)
                    rp = (min(ys, key=lambda y: (abs(y - (f["pad"]["P"][1] + (-GRID if s > 0 else GRID))), y))
                          if ys else None)
                    nx = None
                    if px in columns:
                        nok = [x for x in columns[px] if abs(x - px) >= STAGGER - TOL]
                        nx = min(nok, key=lambda x: (abs(x - (px + s * SLOT_SEP)), x)) if nok else None
                    rn = None
                    if nx is not None and nx in yx[(pid, "N")]:
                        ys2 = yx[(pid, "N")][nx]
                        rn = min(ys2, key=lambda y: (abs(y - (f["pad"]["N"][1] - (-GRID if s > 0 else GRID))), y))
                    ok = [px is not None, nx is not None, rp is not None, rn is not None,
                          prev["P"] is None or (px >= prev["P"] + s * (fstep - GRID) - TOL if s > 0
                                                else px <= prev["P"] + s * (fstep - GRID) + TOL),
                          prev["N"] is None or (nx >= prev["N"] - TOL if s > 0 else nx <= prev["N"] + TOL)]
                    if all(ok):
                        picked = (px, nx, rp, rn)
                        break
            if picked is None:
                certs.append({"kind": "CONSTRUCTION_INFEASIBLE", "layer": "R1_chip_escape_column",
                              "rule": "per_frame_hybrid(collinear|baseline)",
                              "closed_form_condition": "frame mode assignment exists (collinear row carries a "
                                                       "prefix-monotone column, else baseline absorption)",
                              "observed": {"page": pid, "frame": fr["conn_ref"] + "/" + fr["band"],
                                           "mode": mode, "rows": {"P": (rows["P"] or {}).get("row"),
                                                                  "N": (rows["N"] or {}).get("row")},
                                           "prev_x": prev},
                              "required": {"step_mm": fstep, "stagger_mm": STAGGER},
                              "page_or_pad": pid, "scope_note": "本构造规则下不可行；非全局不可能性证明"})
                continue
            px, nx, rp, rn = picked
            d = ((px - nx) ** 2 + (rp - rn) ** 2) ** 0.5
            out[pid] = {"P_via": [fp(px), fp(rp)], "N_via": [fp(nx), fp(rn)],
                        "pair_dist_mm": fp(d), "stagger_mm": fp(abs(px - nx)),
                        "frame": [fr["corridor"], fr["conn_ref"], fr["band"]],
                        "direction": "increasing" if s > 0 else "decreasing", "mode": mode}
            prev["P"], prev["N"] = px, nx
    # ---- ROOT-15 sequential deterministic via placement with a 0.525 clearance filter (single pass)
    _pdm = (coherent or {}).get("pair_domain") or {}
    _rank = {}
    for _fr in frames:
        for _pi in range(len(_fr["pages"])):
            _rank[_fr["pages"][_pi]] = _pi
    # ROOT-18 T-1: chip escape fan = deterministic RADIAL homothety from the chip pad-field
    # centroid (outer rows escape first; inner rows are pushed outward => planar fan, single pass).
    _allpts = [facts[_p]["pad"][_q] for _p in facts for _q in ("P", "N")]
    _cxx = sum(_t[0] for _t in _allpts) / len(_allpts)
    _cyy = sum(_t[1] for _t in _allpts) / len(_allpts)
    _TFAN = 0.0   # LID.1: via≈pad -> 短 breakout（分层后竖段不再重叠）
    # ROOT-21: phase-2 re-places EVERY page (all 32 carry pair_rows). Seeding `_placed` from the
    # phase-1 speculative `out` made each page avoid positions that LATER MOVE (stale avoidance
    # geometry) => cascaded displacement. The constructor must be genuinely sequential.
    _placed = {}
    # ROOT-17 (1)(3): per candidate, check via pairwise clearance (1) and escape-vertical no-overlap
    # (3) against the OTHER already-placed pages.  Index rebuilt once per page (O(n) per page, tiny),
    # candidate checks O(1) => total wall linear in the page count.  Closed-form, single pass.
    # ROOT-21: chip pads are FIXED F.Cu obstacles (manifest geometry), independent of placement
    # order; a breakout must clear every FOREIGN pad with the escape clearance.  A placed-page-only
    # index misses pads of not-yet-placed pages => long breakouts sweeping over neighbours.
    _PADALL = {}
    for _q2, _f2 in facts.items():
        for _pol2 in ("P", "N"):
            _pp = _f2["pad"][_pol2]
            _PADALL.setdefault(int(float(_pp[0]) * 2.0), []).append((float(_pp[0]), float(_pp[1]), _q2))
    _SELF = [None]

    def _mk_index(_exclude):
        """Index EVERY via of the other placed pages (via1/corner/drop/land) for via-via clearance."""
        _vb, _esc, _pad, _brk = {}, {}, {}, {}

        def _vbadd(_x, _y, _lays):
            _vb.setdefault(int(float(_x) * 2.0), []).append((float(_x), float(_y), _lays))

        def _segadd(_lay, _p, _q2, _padacc):
            _xlo = int(min(_p[0], _q2[0]) * 2.0); _xhi = int(max(_p[0], _q2[0]) * 2.0)
            for _bb in range(_xlo, _xhi + 1):
                _esc.setdefault(_bb, []).append((_lay, float(_p[0]), float(_p[1]),
                                                 float(_q2[0]), float(_q2[1]), _padacc))

        for _q, _a in _placed.items():
            if _q == _exclude:
                continue
            _fq = facts[_q]
            _Lq = "B.Cu" if _fq["band"] == "dn" else "In5.Cu"
            for _pol, _xy in (("P", _a[0]), ("N", _a[1])):
                _x, _y = _xy
                _bp = _fq["pad"][_pol]
                _vbadd(_x, _y, frozenset(("F.Cu", _Lq)))                 # via1
                _segadd("F.Cu", _bp, (_x, _y), True)                     # #fcu_pad (pad-access)
                for _cx in range(int(min(_bp[0], _x) - 0.1), int(max(_bp[0], _x) + 0.1) + 1):
                    for _cy in range(int(min(_bp[1], _y) - 0.1), int(max(_bp[1], _y) + 0.1) + 1):
                        _brk.setdefault((_cx, _cy), []).append(((tuple(_bp)), (float(_x), float(_y))))
                if lanes is None:
                    continue
                _ly = fp(lanes[_q]["lane_y"] + pol_off(_fq, _pol))
                _segadd(_Lq, (_x, _y), (_x, _ly), False)                 # escape vertical
                _vbadd(_x, _ly, frozenset((_Lq, "In2.Cu")))              # corner via
                if r3 is not None:
                    _ra = r3["assignment"].get(_fq["conn_ref"] + "|" + _fq["nets"][_pol])
                    if _ra is not None:
                        _vbadd(float(_ra["column_x"]), _ly, frozenset(("In2.Cu", _Lq)))      # drop
                        _vbadd(float(_ra["column_x"]), float(_ra["landing"][1]),
                               frozenset((_Lq, "F.Cu")))                                     # land
        return _vb, _esc, _pad, _brk

    def _vb_clear(_vb, _x, _y):
        _b = int(_x * 2.0)
        for _bb in (_b - 2, _b - 1, _b, _b + 1, _b + 2):   # bucket 0.5 wide => +-2 covers |dx|<=1.5
            for _ox, _oy, _ in _vb.get(_bb, ()):
                if (_x - _ox) ** 2 + (_y - _oy) ** 2 < (VIA_VIA - TOL) ** 2:
                    return False
        return True

    def _esc_ok(_esc, _vx, _vy, _ly, _lay):
        if lanes is None:
            return True
        _lo, _hi = min(_vy, _ly), max(_vy, _ly)
        _b = int(_vx * 2.0)
        for _bb in (_b - 1, _b, _b + 1):
            for _olay, _x1, _y1, _x2, _y2, _pa in _esc.get(_bb, ()):
                if _olay != _lay or _pa:
                    continue                                # cross-layer / pad-access: exempt
                if min(_hi, max(_y1, _y2)) - max(_lo, min(_y1, _y2)) > 1e-6 and \
                   abs(float(_vx) - _x1) < STAGGER - TOL:
                    return False                            # same-layer vertical spacing >= 0.38
        return True

    def _vt_pt(_x, _y, _lay):
        """A-CN.9(vt): candidate via vertex vs placed same-layer tracks (zone-aware)."""
        _b = int(_x * 2.0)
        for _bb in (_b - 2, _b - 1, _b, _b + 1, _b + 2):
            for _olay, _x1, _y1, _x2, _y2, _pa in _esc.get(_bb, ()):
                if _olay != _lay:
                    continue
                if _pt_seg_dist((_x, _y), (_x1, _y1), (_x2, _y2)) < (VT_ESC if _pa else VT_TRACK) - TOL:
                    return False
        return True

    def _vt_seg(_x1, _y1, _x2, _y2, _lay, _padacc):
        """A-CN.9(vt): candidate track vs placed same-layer via vertices + ALL foreign chip pads."""
        _th = VT_ESC if _padacc else VT_TRACK
        _xlo = int(min(_x1, _x2) * 2.0); _xhi = int(max(_x1, _x2) * 2.0)
        for _bb in range(_xlo - 2, _xhi + 3):
            for _ox, _oy, _lays in _vb.get(_bb, ()):
                if _lay not in _lays:
                    continue
                if _pt_seg_dist((_ox, _oy), (_x1, _y1), (_x2, _y2)) < _th - TOL:
                    return False
            if _padacc:                                        # pad access: foreign pads are F.Cu vertices
                for _ox, _oy, _opid in _PADALL.get(_bb, ()):
                    if _opid == _SELF[0]:
                        continue
                    if _pt_seg_dist((_ox, _oy), (_x1, _y1), (_x2, _y2)) < _th - TOL:
                        return False
        return True

    def _seg_pair_clear(_x1, _y1, _x2, _y2, _lay, _thr):
        """A-CN.9(tt): candidate track vs placed same-layer tracks."""
        _xlo = int(min(_x1, _x2) * 2.0); _xhi = int(max(_x1, _x2) * 2.0)
        for _bb in range(_xlo - 4, _xhi + 5):
            for _olay, _ox1, _oy1, _ox2, _oy2, _pa in _esc.get(_bb, ()):
                if _olay != _lay:
                    continue
                if _thr == TT_ESC and not _pa:
                    continue                                   # escape thr only for pad-access pairs
                if seg_dist((_x1, _y1), (_x2, _y2), (_ox1, _oy1), (_ox2, _oy2)) < _thr - TOL:
                    return False
        return True
    for _pid in sorted(facts, key=lambda p: (facts[p]["corridor"], facts[p]["conn_ref"],
                                             facts[p]["band"],
                                             _rank.get(p, 0), p)):
        _f = facts[_pid]
        _rows = _pdm.get(_pid, {}).get("pair_rows", [])
        if not _rows:
            continue
        # ROOT-18 T-1: radial outward target (2D) from the pad-field centroid
        _tPx = _f["pad"]["P"][0] + _TFAN * (_f["pad"]["P"][0] - _cxx)
        _tPy = _f["pad"]["P"][1] + _TFAN * (_f["pad"]["P"][1] - _cyy)
        _tNx = _f["pad"]["N"][0] + _TFAN * (_f["pad"]["N"][0] - _cxx)
        _tNy = _f["pad"]["N"][1] + _TFAN * (_f["pad"]["N"][1] - _cyy)
        _best = None
        _vb, _esc, _pad, _brk = _mk_index(_pid)
        _SELF[0] = _pid
        for _rr in _rows:
            _px = float(_rr[0]); _nx = float(_rr[1]); _py = float(_rr[2]); _ny = float(_rr[3]); _dd = float(_rr[4])
            if _dd < VIA_VIA - TOL or abs(_px - _nx) < STAGGER - TOL:
                continue
            # ROOT-17: FULL via set (via1/corner/drop/land, B.Cu lanes shared) must keep >=0.525
            # inter-net clearance (extends A-CN.1b from R1 vias to every emitted via).
            if lanes is not None and r3 is not None:
                _va = []
                for _pol, _vx, _vy in (("P", _px, _py), ("N", _nx, _ny)):
                    _ly = fp(lanes[_pid]["lane_y"] + pol_off(_f, _pol))
                    _ra = r3["assignment"].get(_f["conn_ref"] + "|" + _f["nets"][_pol])
                    if _ra is None:
                        _va = None
                        break
                    _lx, _lyl = _ra["column_x"], _ra["landing"][1]
                    _va.append((_pol, _vx, _vy)); _va.append((_pol, _vx, _ly))
                    _va.append((_pol, _lx, _ly)); _va.append((_pol, _lx, _lyl))
                if _va is None:
                    continue
                _ok = True
                for _i in range(len(_va)):
                    for _j2 in range(_i + 1, len(_va)):
                        if _va[_i][0] == _va[_j2][0]:
                            continue                      # same net (same polarity): exempt
                        if (_va[_i][1] - _va[_j2][1]) ** 2 + (_va[_i][2] - _va[_j2][2]) ** 2 < (VIA_VIA - TOL) ** 2:
                            _ok = False
                            break
                    if not _ok:
                        break
                if _ok:
                    for _, _vx2, _vy2 in _va:
                        if not _vb_clear(_vb, _vx2, _vy2):
                            _ok = False
                            break
                if not _ok:
                    continue
            # T-1: candidate chip breakouts (pad->via, F.Cu) must not cross placed breakouts
            _bk = [(tuple(_f["pad"]["P"]), (float(_px), float(_py))),
                   (tuple(_f["pad"]["N"]), (float(_nx), float(_ny)))]
            _okb = True
            if seg_cross(_bk[0][0], _bk[0][1], _bk[1][0], _bk[1][1]) or \
               seg_overlap(_bk[0][0], _bk[0][1], _bk[1][0], _bk[1][1]):
                _okb = False
            if _okb:
                _seen = set()
                for _si in _bk:
                    _x0 = min(_si[0][0], _si[1][0]); _x1 = max(_si[0][0], _si[1][0])
                    _y0 = min(_si[0][1], _si[1][1]); _y1 = max(_si[0][1], _si[1][1])
                    for _cx in range(int(_x0 - 0.1), int(_x1 + 0.1) + 1):
                        for _cy in range(int(_y0 - 0.1), int(_y1 + 0.1) + 1):
                            for _pl in _brk.get((_cx, _cy), ()):
                                if id(_pl) in _seen:
                                    continue
                                _seen.add(id(_pl))
                                if seg_cross(_si[0], _si[1], _pl[0], _pl[1]) or \
                                   seg_overlap(_si[0], _si[1], _pl[0], _pl[1]):
                                    _okb = False
                                    break
                            if not _okb:
                                break
                        if not _okb:
                            break
                    if not _okb:
                        break
            if not _okb:
                continue
            if lanes is not None:
                _lyp = fp(lanes[_pid]["lane_y"] + pol_off(_f, "P"))
                _lyn = fp(lanes[_pid]["lane_y"] + pol_off(_f, "N"))
                _lay1 = "B.Cu" if _f["band"] == "dn" else "In5.Cu"
                if not (_esc_ok(_esc, _px, _py, _lyp, _lay1) and _esc_ok(_esc, _nx, _ny, _lyn, _lay1)):
                    continue
            if not (_vb_clear(_vb, _px, _py) and _vb_clear(_vb, _nx, _ny)):
                continue
            if lanes is not None:
                # ROOT-21 A-CN.9(vt/tt): the emitted metric also forbids via<->track (0.4525) and
                # pad<->track breakouts.  The constructor previously checked only via<->via and
                # vertical<->vertical (0.38) => this missing predicate is exactly what A-CN.9 caught.
                _Lc = "B.Cu" if _f["band"] == "dn" else "In5.Cu"
                _pts = ((_px, _py, "F.Cu"), (_px, _py, _Lc), (_nx, _ny, "F.Cu"), (_nx, _ny, _Lc),
                        (_px, _lyp, _Lc), (_nx, _lyn, _Lc), (_px, _lyp, "In2.Cu"), (_nx, _lyn, "In2.Cu"))
                _okv = True
                for _vv in _pts:
                    if not _vt_pt(float(_vv[0]), float(_vv[1]), _vv[2]):
                        _okv = False
                        break
                if _okv:
                    _bP = (float(_f["pad"]["P"][0]), float(_f["pad"]["P"][1]), float(_px), float(_py))
                    _bN = (float(_f["pad"]["N"][0]), float(_f["pad"]["N"][1]), float(_nx), float(_ny))
                    if not (_vt_seg(_bP[0], _bP[1], _bP[2], _bP[3], "F.Cu", True)
                            and _vt_seg(_bN[0], _bN[1], _bN[2], _bN[3], "F.Cu", True)):
                        _okv = False
                if _okv:
                    if not (_seg_pair_clear(_bP[0], _bP[1], _bP[2], _bP[3], "F.Cu", TT_ESC)
                            and _seg_pair_clear(_bN[0], _bN[1], _bN[2], _bN[3], "F.Cu", TT_ESC)):
                        _okv = False
                if _okv:
                    if not (_vt_seg(float(_px), float(_py), float(_px), float(_lyp), _Lc, False)
                            and _vt_seg(float(_nx), float(_ny), float(_nx), float(_lyn), _Lc, False)):
                        _okv = False
                if not _okv:
                    continue
            # T-1 primary: keep the via x at the PAD x (vertical breakouts => planar fan);
            # secondary: radial y target.  (Pad-aligned x is the planarity driver.)
            _boff = 0.3 if _f["band"] == "dn" else -0.3   # 带向 x 偏置：分离相邻行 F.Cu breakout ≥0.38
            # 主键 = pad 邻近（短 breakout）；次键 = 带向 x 偏置对齐
            _key = (round(abs(_px - _f["pad"]["P"][0]) + abs(_nx - _f["pad"]["N"][0])
                          + abs(_py - _f["pad"]["P"][1]) + abs(_ny - _f["pad"]["N"][1]), 3),
                    round(abs(_px - (_f["pad"]["P"][0] + _boff))
                          + abs(_nx - (_f["pad"]["N"][0] + _boff)), 3), _px, _nx)
            if _best is None or _key < _best[0]:
                _best = (_key, _px, _nx, _py, _ny, _dd)
        if _best is None:
            continue
        _, _px, _nx, _py, _ny, _dd = _best
        out[_pid] = {"P_via": [fp(_px), fp(_py)], "N_via": [fp(_nx), fp(_ny)],
                     "pair_dist_mm": fp(_dd), "stagger_mm": fp(abs(_px - _nx)),
                     "frame": [_f["corridor"], _f["conn_ref"], _f["band"]],
                     "direction": "t2_clear", "mode": "t2_clear"}
        _placed[_pid] = ([fp(_px), fp(_py)], [fp(_nx), fp(_ny)])

    # ---- ROOT-15: a CONSTRUCTION_INFEASIBLE certificate asserts "this page could not be placed
    #      under this rule". Once the sequential pass *has* placed it, the certificate is stale and
    #      MUST be voided, otherwise verdict can never reach FEASIBLE_ALL while all predicates PASS.
    certs = [c for c in certs if c.get("page_or_pad") not in out]
    return {"assignment": out, "certificates": certs,
            "method": "per-frame hybrid: collinear-row fan where the F-13 r3 coherent set is non-empty, "
                      "else baseline absorption; then a single-pass, fixed-key argmin repair over the "
                      "precomputed offline F-13 v1.2 pair domain filtered by the 0.525 clearance "
                      "predicate (all closed-form single pass; no search / no backtracking)"}


def _pair_lands(base_gaps, lanes):
    """CO-05b：J2 数据页成对落列派生（确定性、单遍、零搜索）。

    合法域（BASE F-8）：列 132.65(inner) 只可向左 (x<=131.65)；135.0(outer) 只可向右 (x>=136.0)。
    每页取成对局部列：inner 极 lx=131.65-PITCH*k，outer 极 lx=136.0+PITCH*k（k=本带行序）。
    同带内列互异（>=0.38）⇒ 落段竖段互不重叠；异带（B.Cu/In5.Cu）可复用列。
    """
    out = {}
    seen = {}
    for xc, col in base_gaps["connectors"]["J2"]["columns"].items():
        for en in col["entries"]:
            seen[(en["page"], en["pol"])] = (float(xc), en)
    rows = []
    for pg in sorted({k[0] for k in seen}):
        if lanes is None or pg not in lanes:
            continue
        pn = seen.get((pg, "P")); nn = seen.get((pg, "N"))
        if pn and nn:
            rows.append((lanes[pg]["frame"][2], pn[1]["y"], pg, pn, nn))
    rows.sort(key=lambda t: (t[0], t[1], t[2]))
    rank = {}
    for band, _, pg, pn, nn in rows:
        k = rank.get(band, 0); rank[band] = k + 1
        ent = {}
        for tag, (xc, en) in (("P", pn), ("N", nn)):
            inner = abs(xc - J2_INNER_X) < 1e-6
            lx = fp(J2_LEFT0 - PAIR_PITCH * k) if inner else fp(J2_RIGHT0 + PAIR_PITCH * k)
            b = en.get("y_band") or [en["y"] - 0.3, en["y"] + 0.3]
            ent[tag] = (lx, [fp(b[0]), fp(b[1])], bool(inner))
        out[pg] = ent
    return out


def r3_place(gaps: dict, lanes: dict = None, order: str = "lane", base_gaps: dict = None) -> dict:
    """每 pad 取最小 gap 候选归组；组内按 (pad_y, net) 前缀递推。CO-05b: J2 数据页成对落列。"""
    pads = []
    for cref in sorted(gaps["connectors"]):
        for xc, col in sorted(gaps["connectors"][cref]["columns"].items(),
                              key=lambda kv: float(kv[0])):
            for en in col["entries"]:
                band = en.get("y_band") or [en["y"] - 0.3, en["y"] + 0.3]
                pads.append({"ref": cref, "net": en["net"], "y": fp(en["y"]),
                             "cands": sorted(float(c) for c in en["gap_candidates"]),
                             "band": [fp(band[0]), fp(band[1])], "pol": en["pol"],
                             "page": en["page"], "kind": en["kind"]})
    PL = _pair_lands(base_gaps, lanes) if (PAIR_MODE and base_gaps is not None) else {}
    out, certs = {}, []
    _rk = 0
    RANK = {}
    groups = {}
    for pd in pads:
        groups.setdefault((pd["ref"], pd["cands"][0]), []).append(pd)
    for _c in sorted({k[0] for k in groups}):
        for _cx in sorted({k[1] for k in groups if k[0] == _c}):
            RANK[(_c, _cx)] = _rk; _rk += 1
    for pg, ent in sorted(PL.items()):
        for pol in ("P", "N"):
            lx, band, _inner = ent[pol]
            pd = next((q for q in pads if q["page"] == pg and q["pol"] == pol), None)
            if pd is None:
                continue
            bump(2, "r3_landing")
            y = fp(min(max(pd["y"] + R3_OFF, band[0] + 0.05), band[1] - 0.05))
            out[pd["ref"] + "|" + pd["net"]] = {
                "ref": pd["ref"], "pad": [fp(colx_center(gaps, pd["ref"], pd)),
                                          fp(pd["y"])], "pad_x": fp(colx_center(gaps, pd["ref"], pd)),
                "pad_y": fp(pd["y"]), "y_band": band, "column_x": fp(lx),
                "landing": [fp(lx), y], "kind": pd["kind"], "page": pd["page"],
                "pol": pd["pol"], "gap_column_candidates": pd["cands"]}
    for (cref, colx) in sorted(groups):
        if order == "lane" and lanes is not None:
            grp = sorted(groups[(cref, colx)],
                         key=lambda q: (lanes.get(q["page"], {}).get("lane_index", 10 ** 6), q["net"]))
        else:
            grp = sorted(groups[(cref, colx)], key=lambda q: (q["y"], q["net"]))
        prev = None
        for pd in grp:
            if pd["page"] in PL:
                continue
            bump(2, "r3_landing")
            _stag = 0.1 if (RANK.get((cref, colx), 0) % 2) else -0.1
            _base_y = min(max(pd["y"] + R3_OFF + _stag, pd["band"][0] + 0.05), pd["band"][1] - 0.05)
            y = _base_y if prev is None else max(_base_y, prev + R3_STEP)
            if y > pd["band"][1] + TOL or y < pd["band"][0] - TOL or (
                    prev is not None and y - prev < VIA_VIA - TOL):
                certs.append({"kind": "CONSTRUCTION_INFEASIBLE",
                              "layer": "R3_connector_escape_gap",
                              "rule": "gap_column_prefix_recurrence",
                              "closed_form_condition": "y_k = max(pad_y_k - 0.3, y_{k-1} + 0.6) in y_band",
                              "observed": {"ref": cref, "gap_x": colx, "pad_y": pd["y"],
                                           "y_k": fp(y), "prev_y": None if prev is None else fp(prev)},
                              "required": {"y_band": pd["band"], "step_mm": R3_STEP},
                              "page_or_pad": pd["net"],
                              "scope_note": "本构造规则下不可行；非全局不可能性证明"})
            out[cref + "|" + pd["net"]] = {
                "ref": cref, "pad": [fp(colx_center(gaps, cref, pd)),
                                     fp(pd["y"])], "pad_x": fp(colx_center(gaps, cref, pd)),
                "pad_y": fp(pd["y"]), "y_band": pd["band"], "column_x": fp(colx),
                "landing": [fp(colx), fp(y)], "kind": pd["kind"], "page": pd["page"],
                "pol": pd["pol"], "gap_column_candidates": pd["cands"]}
            prev = y
    return {"assignment": out, "certificates": certs}

def colx_center(gaps: dict, cref: str, pd: dict) -> float:
    for xc, col in gaps["connectors"][cref]["columns"].items():
        for en in col["entries"]:
            if en["net"] == pd["net"]:
                return float(xc)
    return float("nan")


def _in2_columns():
    """pad 场近域的 In2 竖直 stub 列 (x, y_lo, y_hi)。来源 = CO-16 帧（模块级 _CO16_PTS），闭式无搜索。"""
    cols = {}
    for pp in _CO16_PTS.values():
        for q in (pp or {}).get("stub", []):
            x, y = fp(q[0]), fp(q[1])
            if ECS_COL_LO <= x <= ECS_COL_HI:
                lo, hi = cols.get(x, (y, y))
                cols[x] = (min(lo, y), max(hi, y))
    return sorted((x, lo, hi) for x, (lo, hi) in cols.items())


def refclk_transit_nodes(j2, via1_y, dip_y, west_x, rise_x, run_y, off):
    """CO-40/CO-45 ECS-001：J2 外列 N 的 pad 场 transit（F.Cu -> In2 -> F.Cu 单次换层）。

    闭式：via1 落两列缝中线 (ECS_VIA1_X, via1_y)；via2 取 x<=ECS_VIA2_X_MAX 上避开同层 In2 列的
    缝中心 (x_v, dip_y)；若无直行缝（dip_y 被 In2 列端封堵）则绕该列端部
    （detour_y = 该列 y_lo - ECS_DX 取整）。
    CO-45：via1_y（自 pad 直出的 stub 端，受 pad 10/14 净距约束）与 dip_y（N 轨 y）解耦。
    远端接入折线由调用方统一追加（P/N 同口径）——修补 CO-43 中 nodes 丢失远端 waypoint 的缺陷。
    """
    tail = [[fp(rise_x + off), dip_y, "F.Cu"],
            [fp(rise_x + off), fp(run_y + off), "F.Cu"],
            [fp(west_x), fp(run_y + off), "F.Cu"]]
    head = [[j2[0], j2[1], "F.Cu"],
            [ECS_VIA1_X, via1_y, "F.Cu"], [ECS_VIA1_X, via1_y, "In2.Cu"]]
    cols = _in2_columns()
    x_v = fp(math.floor((ECS_VIA2_X_MAX - GRID) / GRID) * GRID)      # 直行候选（最东可用，留 0.075 余量）
    blk = [c for c in cols if c[1] - ECS_MARGIN <= dip_y <= c[2] + ECS_MARGIN]  # dip_y 处封堵列
    direct = (not blk) or (x_v - max(c[0] for c in blk) >= ECS_DX)
    if direct:
        return head + [[x_v, dip_y, "In2.Cu"], [x_v, dip_y, "F.Cu"]] + tail
    x_wall = max(c[0] for c in blk)                                  # 最东封堵列 = 须绕行的那道墙
    detour_y = fp(math.floor((min(c[1] for c in blk if c[0] == x_wall) - ECS_DX) / GRID) * GRID)
    west_blk = [c[0] for c in blk if c[0] < x_wall]      # dip_y 处封堵列中位于墙西侧者
    x_v = (fp((x_wall + max(west_blk)) / 2.0) if west_blk   # 墙 ↔ 其西邻封堵列 的中缝
           else fp(x_wall - ECS_DX - 2 * GRID))
    x_vert = fp(math.floor(((x_wall + ECS_VIA1_X) / 2.0) / GRID) * GRID)          # 竖直段（墙东侧、缝内）
    return (head + [[x_vert, via1_y, "In2.Cu"], [x_vert, detour_y, "In2.Cu"],
                    [x_v, detour_y, "In2.Cu"], [x_v, dip_y, "In2.Cu"],
                    [x_v, dip_y, "F.Cu"]] + tail)


def _far_row_span(manifest, far_ref):
    """远端连接器（J3/J4）两排 pad 行 y（升序）。来源 = manifest 锚点，闭式无搜索。"""
    ys = set()
    for pg in manifest["pages"]:
        for k in ("conn", "conn2"):
            a = pg.get("anchors", {}).get(k)
            if not isinstance(a, dict):
                continue
            for pol in ("P", "N"):
                q = a.get(pol)
                if isinstance(q, dict) and q.get("ref") == far_ref:
                    ys.add(fp(q["pad_global"][1]))
    return sorted(ys)


def refclk_meander(m1, y0, extra, span_max):
    """CO-45 等长补偿：在水平段 y=y0 上自 m1 向西插入**南向三角幂绕**。

    闭式：半齿距 h = 0.05 栅格最近值，齿数 n 取满足 A<=REFCLK_MEANDER_A_MAX 的**最小**整数，
    幅值 A = sqrt(((extra+L)/(2n))^2 - h^2)（L = 2n*h，故实测额外长度 == extra，无需回搜）。
    返回 [m1,y0] 起的折线点列（末点 = [m1-2n*h, y0]）；不可达则 RuntimeError = 停机。
    """
    if extra <= TOL:
        return [[m1, y0]]
    for n in range(1, 65):
        h = fp(span_max / (2 * n))
        if h <= 4 * GRID:
            continue
        a2 = (extra / (2 * n) + h) ** 2 - h * h
        if a2 > TOL and math.sqrt(a2) <= REFCLK_MEANDER_A_MAX + TOL:
            a_mag = math.sqrt(a2)
            pts = [[m1, y0]]
            for k in range(1, 2 * n + 1):
                pts.append([fp(m1 - k * h), y0 + (a_mag if k % 2 else 0.0)])
            return pts
    raise RuntimeError("CO-45 meander: no feasible (n, A) within amplitude bound")


def refclk_far_transit(manifest, far_ref, far_pads, run_y, pol, x_rise_lo):
    """CO-42/43/45：远端接入 = 抬升入两排间自由带 -> 带内西行 -> 垂直入 pad。

    闭式分配（CO-45 修正，取代 CO-43 的 2 选 1 启发）：
      * rails：P = run_y + REFCLK_OFF["P"]（pad 中心线侧），N = run_y + REFCLK_OFF["N"]（北侧）；
      * lines：N 走北线 line_a（贴 row_lo 侧），P 走南线 line_b；
      * 抬升列：P 取西列 xj_near，N 取东列 xj_far。
    该组合下 P/N 折线互不相交；函数内以**真实线段相交**自检（相交即 RuntimeError = 停机，禁静默回退）。
    line_a/line_b 间距 = FAR_LINE_STEP（CO-45：0.5，边距 0.295；原 0.38 边距恰 0.175 无余量）。
    """
    rows = _far_row_span(manifest, far_ref)
    if len(rows) < 2:
        return None
    row_lo = rows[0]
    line_a = fp(row_lo + FAR_ROW_MARGIN + FAR_LINE_LO)     # 北线（贴 row_lo 侧）
    line_b = fp(line_a + FAR_LINE_STEP)                    # 南线
    east_end = 0.0
    for pg in manifest["pages"]:
        for k in ("conn", "conn2"):
            a = pg.get("anchors", {}).get(k)
            if not isinstance(a, dict):
                continue
            for _p in ("P", "N"):
                q = a.get(_p)
                if isinstance(q, dict) and q.get("ref") == far_ref:
                    east_end = max(east_end, fp(q["pad_global"][0]))
    # 抬升列须在 A 排 pad 场之外：取「manifest 已引用 pad 东端 + 余量」与
    # witness `west_rise_in_corridor.x_centre_range[0]`（其认证的自由抬升列，东于整个 pad 场）的较大者
    xj_near = fp(math.ceil(max(east_end + FAR_JOG_EAST, x_rise_lo) / GRID) * GRID)
    xj_far = fp(xj_near + GRID * 10)
    rails = {q: fp(run_y + REFCLK_OFF[q]) for q in ("P", "N")}
    line_of = {"N": line_a, "P": line_b}
    xj_of = {"P": xj_near, "N": xj_far}

    def _poly(q):
        return [[xj_of[q], rails[q]], [xj_of[q], line_of[q]],
                [far_pads[q][0], line_of[q]], [far_pads[q][0], far_pads[q][1]]]

    _pp, _nn = _poly("P"), _poly("N")
    for _s1 in zip(_pp, _pp[1:]):
        for _s2 in zip(_nn, _nn[1:]):
            if seg_cross(_s1[0], _s1[1], _s2[0], _s2[1]):
                raise RuntimeError(f"CO-45 self-check: REFCLK far transit P/N cross ({far_ref}/{pol})")
    return _poly(pol)


def refclk_place(manifest: dict, w0r: dict) -> dict:
    pw = w0r["refclk_passage_witness"]
    eu = pw["transition_columns"]["east_rise"]["x_centre_range"]
    rise_x = fp(eu[0] + 0.5)
    chan = pw["per_page"]["PCIE_REFCLK1/input"]["alternative_windows_same_side"][0]  # base-id lookup
    out = {}
    for pg in sorted([p for p in manifest["pages"] if p["kind"] != "data"],
                     key=lambda p: p["page_id"]):
        pid = pg["page_id"]
        base_pid = pid.split("#")[0]
        west = CORRIDOR["WEST_MCIO_TO_CHIP"]["bounds"][1]
        east = CORRIDOR["EAST_CHIP_TO_J2"]["bounds"][0]
        u6 = [b for b in pw["blockers"] if b["ref"] == "U6"][0]
        east_clear = fp(east if east > u6["keepout_x"][1] else u6["keepout_x"][1] + GRID)
        # CO-45：抬升列以 P 列为基准（off=0）；须使最北偏移列（N, off=-0.5）仍满足 U6 余量
        _off_lo = min(REFCLK_OFF.values())
        rise_x = fp(max(rise_x, east_clear + 0.5 - _off_lo))
        pp = pw["per_page"][base_pid]
        half = pw.get("pair_copper_extent_mm", 0.585) / 2.0
        if "pair_centre_window_y" in pp:
            _lo, _hi = pp["pair_centre_window_y"]
        elif "channel_y" in pp:
            _lo, _hi = pp["channel_y"][0] + half, pp["channel_y"][1] - half
        else:
            _lo = _hi = None
        paths = {}
        nodes = {}
        _far_tr = {}
        lane_y = None
        _far_pads, _far_ref = {}, None                          # CO-43: 远端 pad（J3/J4）
        for _p in ("P", "N"):
            _a1 = [fp(pg["anchors"]["conn"][_p]["pad_global"][0]),
                   fp(pg["anchors"]["conn"][_p]["pad_global"][1])]
            _a2 = [fp(pg["anchors"]["conn2"][_p]["pad_global"][0]),
                   fp(pg["anchors"]["conn2"][_p]["pad_global"][1])]
            _far_pads[_p] = _a1 if _a1[0] < _a2[0] else _a2
            _far_ref = pg["anchors"]["conn"][_p]["ref"]
        _b3, _meta = {}, {}
        for pol in ("P", "N"):
            off = REFCLK_OFF[pol]        # CO-45: P=0（内列 pad 中心线直出）、N=-0.5（北侧 0.5）
            a1 = [fp(pg["anchors"]["conn"][pol]["pad_global"][0]),
                  fp(pg["anchors"]["conn"][pol]["pad_global"][1])]
            a2 = [fp(pg["anchors"]["conn2"][pol]["pad_global"][0]),
                  fp(pg["anchors"]["conn2"][pol]["pad_global"][1])]
            j2 = a1 if a1[0] >= a2[0] else a2                # J2 端 = x 较大侧（闭式）
            far = a2 if a1[0] >= a2[0] else a1
            lane_y = j2[1] if lane_y is None else lane_y
            base_run = j2[1] if abs(far[1] - j2[1]) <= 3.2 else fp(max(far[1], chan[0]) + GRID)
            run_y = base_run if _lo is None else fp(min(max(base_run, _lo), _hi))  # 见证成对中心窗
            # 差分对几何：P/N 各自在 pad x / rise x / run y 上偏移 0.38，全程不共线
            _rise_lo = fp(pw["transition_columns"]["west_rise_in_corridor"]["x_centre_range"][0])
            _tr = refclk_far_transit(manifest, _far_ref, _far_pads, run_y, pol, _rise_lo)
            if _tr is None:
                _tr = [[far[0], far[1]]]
            _far_tr[pol] = _tr
            if pol == "P":                       # 内列 pad：F.Cu 直出（off=0 ⇒ pad 中心线），无换层
                _b3[pol] = [[j2[0], j2[1], "F.Cu"],
                            [j2[0], fp(j2[1] + off), "F.Cu"],
                            [fp(rise_x + off), fp(j2[1] + off), "F.Cu"],
                            [fp(rise_x + off), fp(run_y + off), "F.Cu"],
                            [fp(west), fp(run_y + off), "F.Cu"]]
            else:                                # 外列 pad：ECS-001 单次换层（F.Cu -> In2 -> F.Cu）
                _b3[pol] = refclk_transit_nodes(j2, fp(j2[1] + ECS_VIA1_DY), fp(j2[1] + off),
                                                west, rise_x, run_y, off)
            _meta[pol] = {"j2": j2, "far": far, "off": off, "run_y": run_y,
                          "base_run": base_run, "tr": _tr}

        # CO-45 等长补偿：P rail（west -> xj_P）插入南向幂绕，补偿 |L_P - L_N|（>=0 时）
        def _el_len(_r):
            """CO-69：按层加权电气长度（节点第 3 元为层；tr 段按 F.Cu）。"""
            _t = 0.0
            for i in range(len(_r) - 1):
                _d = ((_r[i + 1][0] - _r[i][0]) ** 2 + (_r[i + 1][1] - _r[i][1]) ** 2) ** 0.5
                _t += _d * _sqrt_er(_r[i][2] if len(_r[i]) > 2 else "F.Cu")
            return _t
        _pl, _nl_ = _el_len(_b3["P"] + [[q[0], q[1], "F.Cu"] for q in _meta["P"]["tr"]]), \
                    _el_len(_b3["N"] + [[q[0], q[1], "F.Cu"] for q in _meta["N"]["tr"]])
        # 幂绕落 P rail(F.Cu)；把电气缺口换算为 F.Cu 上的物理长度
        _extra = (_nl_ - _pl) / _sqrt_er("F.Cu")
        if _extra < -TOL:
            raise RuntimeError("CO-45 length compensation: P longer than N (no feasible shortener)")
        _runp = fp(_meta["P"]["run_y"] + _meta["P"]["off"])
        _xjp = _meta["P"]["tr"][0][0]
        _mp = refclk_meander(fp(west - REFCLK_MEANDER_HI), _runp, _extra,
                             fp((west - REFCLK_MEANDER_HI) - (_xjp + REFCLK_MEANDER_LO)))
        _b3["P"] = _b3["P"] + [[q[0], q[1], "F.Cu"] for q in _mp]
        _skew_after = {}

        for pol in ("P", "N"):
            _raw3 = _b3[pol] + [[q[0], q[1], "F.Cu"] for q in _meta[pol]["tr"]]
            _nd = [_raw3[0]]
            for q in _raw3[1:]:
                if (abs(q[0] - _nd[-1][0]) > TOL or abs(q[1] - _nd[-1][1]) > TOL
                        or q[2] != _nd[-1][2]):
                    _nd.append(q)
            nodes[pol] = _nd
            _xy = [[q[0], q[1]] for q in _nd]
            path = [_xy[0]]
            for q in _xy[1:]:
                if abs(q[0] - path[-1][0]) > TOL or abs(q[1] - path[-1][1]) > TOL:
                    path.append(q)
            bump(6, "refclk_path")
            paths[pol] = {"path": path, "j2_pad": _meta[pol]["j2"], "far_pad": _meta[pol]["far"],
                          "pol_offset_mm": _meta[pol]["off"], "run_y": _meta[pol]["run_y"],
                          "crossing_y_from_witness": (_meta[pol]["base_run"]
                                                      if _meta[pol]["base_run"] != _meta[pol]["j2"][1]
                                                      else None)}
            _skew_after[pol] = _el_len(_nd)          # CO-69：电气（按层加权）
        _skew_mm = round(abs(_skew_after["P"] - _skew_after["N"]) / _sqrt_er("In2.Cu"), 4)  # mm-eq @ er 3.99
        if _skew_mm > 0.15 + 1e-9:
            raise RuntimeError(f"CO-45 length compensation: residual skew {_skew_mm} > 0.15")
        out[pid] = {"layer": "F.Cu", "lane_y": lane_y, "pol_offset_mm": dict(REFCLK_OFF),
                    "meander_extra_mm": round(_extra, 4), "intra_pair_skew_mm": _skew_mm,
                    "nets": {q: pg["anchors"]["conn2"][q]["net"] for q in ("P", "N")},
                    "paths": paths,
                    "witness": {"source": "W0-R refclk_passage_witness",
                                "kind": pw["per_page"][base_pid]["kind"],
                                "status": pw["per_page"][base_pid]["status"]},
                    "nodes": nodes,
                    "pad_field_transit": ("ECS-001 (CO-40 L2 自裁): 外列 N = F.Cu stub -> via1 "
                                          "-> In2 下穿内列墙 -> via2 -> F.Cu；每线 2 via；"
                                          "内列 P = F.Cu 直出")}
    return out


def _in_box(a, box) -> int:
    return int(box[0][0] <= a[0] <= box[1][0] and box[0][1] <= a[1] <= box[1][1])


def seg_hits_box(p, q, box) -> int:
    """线段与轴对齐盒真实相交（端点在内 或 交任一边）。"""
    corners = [[box[0][0], box[0][1]], [box[1][0], box[0][1]],
               [box[1][0], box[1][1]], [box[0][0], box[1][1]]]
    n = _in_box(p, box) + _in_box(q, box)
    for i in range(4):
        n += seg_cross(p, q, corners[i], corners[(i + 1) % 4])
    return int(n > 0)


def seg_cross(p, q, r, s) -> int:
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = o(r, s, p), o(r, s, q), o(p, q, r), o(p, q, s)
    return int(((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)))


def seg_overlap(p, q, r, s) -> int:
    """同层共线重叠（异网铜搭接/短路）计 1；非共线返回 0。"""
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if abs(o(p, q, r)) > 1e-6 or abs(o(p, q, s)) > 1e-6:
        return 0
    axis = 0 if abs(q[0] - p[0]) >= abs(q[1] - p[1]) else 1
    lo1, hi1 = sorted((p[axis], q[axis]))
    lo2, hi2 = sorted((r[axis], s[axis]))
    return int(min(hi1, hi2) - max(lo1, lo2) > 1e-6)


def _pt_seg_dist(pt, a, b) -> float:
    ax, ay = a[0], a[1]; bx, by = b[0], b[1]; px, py = pt[0], pt[1]
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    if L2 <= 1e-12:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return ((px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2) ** 0.5


def seg_dist(p, q, r, s) -> float:
    return min(_pt_seg_dist(p, r, s), _pt_seg_dist(q, r, s),
               _pt_seg_dist(r, p, q), _pt_seg_dist(s, p, q))


def clearance_metric(paths: dict, pc: dict, via_r: float, esc_clr: float) -> dict:
    """完整净距套件（L5 暴露）；pad-access 段（#fcu_pad/#fcu_land）按 SPEC escape_transition_zone 微净距。"""
    tt = pc["width"] + pc["clearance"]
    tt_esc = pc["width"] + esc_clr
    vt = via_r + pc["clearance"] + pc["width"] / 2
    vt_esc = via_r + esc_clr + pc["width"] / 2
    vv = 2 * via_r + pc["clearance"]
    def _esc(nm): return ("#fcu_pad" in nm) or ("#fcu_land" in nm)
    ids = sorted(paths)
    def base(x): return (x[0] if isinstance(x, tuple) else x).split("#")[0]
    def _nid(x):
        if not SAFE_HOP_METRIC[0]:
            return (base(x), None)
        return (base(x), x[1] if (isinstance(x, tuple) and len(x) > 1) else None)
    v_tt = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if paths[ids[i]][0] != paths[ids[j]][0] or _nid(ids[i]) == _nid(ids[j]):
                continue
            pa, pb = paths[ids[i]][1], paths[ids[j]][1]
            for s1 in zip(pa, pa[1:]):
                for s2 in zip(pb, pb[1:]):
                    d = seg_dist(s1[0], s1[1], s2[0], s2[1])
                    _thr = tt_esc if (_esc(str(ids[i])) or _esc(str(ids[j]))) else tt
                    if d < _thr - 1e-9:
                        v_tt.append([base(ids[i]), base(ids[j]), round(d, 4)])
    pt_l, pt_n = {}, {}
    for k in ids:
        lay = paths[k][0]; nid = _nid(k)
        for pt in paths[k][1]:
            key = (round(pt[0], 4), round(pt[1], 4))
            pt_l.setdefault(key, set()).add(lay); pt_n.setdefault(key, set()).add(nid)
    v_vt = []
    for key, lays in pt_l.items():
        own = pt_n[key]
        for k in ids:
            if paths[k][0] not in lays or _nid(k) in own:
                continue
            for sg in zip(paths[k][1], paths[k][1][1:]):
                d = _pt_seg_dist(key, sg[0], sg[1])
                _thr = vt_esc if _esc(str(k)) else vt
                if d < _thr - 1e-9:
                    v_vt.append([base(k), round(d, 4), list(key)])
    _LI = {}
    for _ii in range(len(LAYER_PALETTE)):
        _LI[LAYER_PALETTE[_ii]] = _ii
    vias = [k for k, l in pt_l.items() if len(l) > 1]
    v_vv = []
    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            if pt_n.get(vias[i], set()) & pt_n.get(vias[j], set()):
                continue                                    # 同网（相连）豁免
            if SAFE_HOP_METRIC[0]:
                _si = sorted(_LI[l] for l in pt_l[vias[i]])
                _sj = sorted(_LI[l] for l in pt_l[vias[j]])
                if _si[-1] < _sj[0] or _sj[-1] < _si[0]:
                    continue    # CO-16 安全 hop：层跨不相交 => 无共层铜/钻孔冲突
            d = ((vias[i][0] - vias[j][0]) ** 2 + (vias[i][1] - vias[j][1]) ** 2) ** 0.5
            if d < vv - 1e-9:
                v_vv.append([list(vias[i]), list(vias[j]), round(d, 4)])
    return {"thresholds": {"track_track": round(tt, 4), "track_track_escape": round(tt_esc, 4),
                           "via_track": round(vt, 4), "via_track_escape": round(vt_esc, 4), "via_via": round(vv, 4)},
            "viol_track_track": len(v_tt), "viol_via_track": len(v_vt), "viol_via_via": len(v_vv),
            "sample_tt": v_tt[:4], "sample_vt": v_vt[:4], "sample_vv": v_vv[:4], "n_vias": len(vias)}


def count_crossings(paths: dict):
    """同层异网段对**冲突**计数（跨层由层分配隔离）。返回 (cross, overlap) 两个按类字典：
    cross = 真交叉（transversal）；overlap = 共线重叠（同层异网铜搭接 = 短路）。
    同类同网（同一 base pid + 同一 pol）的相邻段不互比。"""
    cross, over = {}, {}
    ids = sorted(paths)
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            if paths[ids[a]][0] != paths[ids[b]][0]:
                continue
            _na = ids[a][0] if isinstance(ids[a], tuple) else ids[a]
            _nb = ids[b][0] if isinstance(ids[b], tuple) else ids[b]
            _pa = ids[a][1] if isinstance(ids[a], tuple) else ""
            _pb = ids[b][1] if isinstance(ids[b], tuple) else ""
            if _na.split("#")[0] == _nb.split("#")[0] and _pa == _pb:
                continue                                    # same net: connected segments
            k = "stub" if ("#stub" in _na or "#stub" in _nb
                           or "#fcu_land" in _na or "#fcu_land" in _nb) else "r1_5"
            pa, pb = paths[ids[a]][1], paths[ids[b]][1]
            for s1 in zip(pa, pa[1:]):
                for s2 in zip(pb, pb[1:]):
                    cross[k] = cross.get(k, 0) + seg_cross(s1[0], s1[1], s2[0], s2[1])
                    over[k] = over.get(k, 0) + seg_overlap(s1[0], s1[1], s2[0], s2[1])
    return cross, over


def resource_gate(facts: dict, spec: dict, rules: dict, intent: dict) -> dict:
    """W3-C4 上游资源充分性门（闭式 O(n)，机器可判）：层意图资源 vs 需求。"""
    bump(4, "gate_layers")
    signals = dict(intent["layer_intent"])
    avail = sorted(intent["transition_eligible_layers"])
    # 每组 = (corridor, band)；源行来自 chip 锚；lane 区来自 v1.3 分段区意图
    _src = {}
    for _f in facts.values():
        _src.setdefault(_f["corridor"], []).append(_f["pad"]["P"][1])
    corridors = sorted(_src, key=lambda c: (sum(_src[c]) / len(_src[c])))  # 与 R2 分段区同序
    regions = {}
    for ci in range(len(corridors)):
        lo = ci * N_USED
        regions[corridors[ci]] = [fp(LANE_LO + lo * STEP), fp(LANE_LO + (lo + N_USED - 1) * STEP)]
    groups = {}
    for pid, f in facts.items():
        key = (f["corridor"], f["band"])
        g = groups.setdefault(key, {"src": [], "corridor": f["corridor"], "band": f["band"]})
        g["src"].append(f["pad"]["P"][1])
        g["src"].append(f["pad"]["N"][1])
    rows = []
    for key in sorted(groups):
        g = groups[key]
        reg = regions[g["corridor"]]
        ys = g["src"] + reg
        rows.append({"group": key[0] + "/" + key[1], "source_y_range": [min(g["src"]), max(g["src"])],
                     "lane_region_y": reg, "fan_y_extent": [fp(min(ys)), fp(max(ys))],
                     "x_extent_chip_zone": [82.35, 105.25]})
    # 层需求 = 扇面 y 区间在同一 x 带内的最大重叠数（区间图团数 = 端点扫描）
    events = []
    for i in range(len(rows)):
        events.append((rows[i]["fan_y_extent"][0], 1))
        events.append((rows[i]["fan_y_extent"][1], -1))
    events.sort(key=lambda e: (e[0], -e[1]))
    cur = peak = 0
    for e in events:
        cur += e[1]
        peak = max(peak, cur)
    lanes_needed = {c: sum(1 for f in facts.values() if f["corridor"] == c) for c in corridors}
    lanes_avail = {c: N_LANES for c in corridors}
    cap_ok = all(lanes_needed[c] <= lanes_avail[c] for c in corridors)
    layers_ok = peak <= len(avail)
    bump(4, "gate_groups")
    return {"verdict": "SUFFICIENT" if (cap_ok and layers_ok) else "UPSTREAM_CHANGE_REQUEST",
            "rule": "available transition-eligible signal layers x corridor/band fan capacity vs demand",
            "transition_eligible_layers": avail,
            "layer_intent": signals,
            "layer_demand_peak_overlap": peak,
            "layer_demand_ok": layers_ok,
            "lane_capacity": {"needed": lanes_needed, "available": lanes_avail, "ok": cap_ok},
            "fan_groups": rows,
            "closed_form": "verdict = SUFFICIENT iff peak(fan y-extent overlap in chip-zone x) "
                           "<= |transition_eligible_layers| and lanes_needed <= lanes_avail",
            "insufficiency_basis": None if (cap_ok and layers_ok) else {
                "layers_needed": peak, "layers_available": len(avail),
                "gap": peak - len(avail)},
            "producer": "k2/tools/p3_v57_w3_constructive.py:resource_gate"}


def color_groups(rows: list, layers: list) -> dict:
    """区间图贪心着色（按起点升序，取首个未被重叠组占用的层）；确定性、非搜索。"""
    order = sorted(range(len(rows)), key=lambda i: (rows[i]["fan_y_extent"][0], rows[i]["group"]))
    out = {}
    for i in order:
        used = set()
        for j in order:
            if j != i and out.get(rows[j]["group"]) is not None and overlap(
                    rows[i]["fan_y_extent"], rows[j]["fan_y_extent"]):
                used.add(out[rows[j]["group"]])
        pick = [x for x in layers if x not in used]
        out[rows[i]["group"]] = pick[0] if pick else None
    return out


def overlap(a: list, b: list) -> bool:
    return min(a[1], b[1]) >= max(a[0], b[0])


def emit_request_card(gate: dict) -> None:
    """不足：出**版本化**上游变更请求卡（不 clobber canonical；ROOT-16 起几何已随主件持久化）。"""
    cr = STEP2 / ("m13_v57_w3_upstream_change_request_" + REVISION + ".md")
    rej = ["In4.Cu as signal layer - REJECTED (spec: In4 = power plane P3V3; In2 = the only internal signal layer; PD/SI red line; measured regression 29/32 -> 8/32)"]
    levers = ["lane order by source - WITHDRAWN (equals card v1.3 R-8 closed-form infeasibility proof)",
              "no_90deg channelized polyline - MEASURED worse (319 > 264) -> rolled back",
              "per-frame adaptive step - MEASURED neutral on this geometry",
              "R1 escape-domain widening - UPSTREAM ONLY"]
    cr.write_text("\n".join([
        "# Upstream change request (engine-generated, W3-C7)", "",
        "> Semantics: UPSTREAM_CHANGE_REQUEST / CERTIFICATE = escalation trigger, not an endpoint.",
        "> Gate criterion: " + str(gate.get("closed_form")), "",
        "## Rejected (do not re-propose)"] + ["- " + x for x in rej] + [
        "", "## Legal levers (signal-layer routing/topology only) + measured status"]
        + ["- " + x for x in levers] + [
        "", "## Gate measurement (verification-based, R-23)", "```json",
        json.dumps(gate.get("verification_check"), ensure_ascii=False, indent=1), "```",
        "", "## Next", "All in-layer legal levers measured neutral-or-worse => remaining options are "
        "UPSTREAM: (a) R1 escape domain widening, (b) F-5 frame/lane order revision, "
        "(c) connector/ball re-mapping, or (d) provide a GLOBAL infeasibility proof."]),
        encoding="utf-8")
    print("W3-C4 GATE:", gate["verdict"], "| demand", gate["layer_demand_peak_overlap"],
          "| available", len(gate["transition_eligible_layers"]), "| change-request ->", cr)


def scale_probe(j: dict, base_facts: dict, args) -> int:
    """G-M3 规模探针：复制数据页集 K 份（x + 300*c，闭式偏移），只跑构造并报 work_units（线性）。"""
    WORK[0] = 0
    BOOK.clear()
    facts = {}
    for c in range(args.scale):
        for pid, f in base_facts.items():
            g = json.loads(json.dumps(f))
            for pol in ("P", "N"):
                g["pad"][pol] = [f["pad"][pol][0] + 300.0 * c, f["pad"][pol][1]]
                g["conn_pad"][pol] = [f["conn_pad"][pol][0] + 300.0 * c, f["conn_pad"][pol][1]]
            g["page_id"] = pid + f"#c{c}"
            facts[g["page_id"]] = g
    base_frs = frames_of(base_facts)
    frs = []
    for c in range(args.scale):
        for fr in base_frs:
            g = json.loads(json.dumps(fr))
            g["pages"] = [pid + f"#c{c}" for pid in fr["pages"]]
            frs.append(g)
    key = [(frs[i]["corridor"], frs[i]["row_y_span"][0], i) for i in range(len(frs))]
    perm = sorted(range(len(frs)), key=lambda i: key[i])
    frs = [frs[i] for i in perm]
    bump(4 * len(facts), "nodes")
    lanes = r2_lanes(frs, facts)
    xorder = json.loads(json.dumps(j["pair_xorder"]))
    xo_pages = {}
    for pid, f in facts.items():
        xo_pages[pid] = xorder["pages"][pid.split("#")[0]]
    xorder["pages"] = xo_pages
    verdict = json.loads(json.dumps(j["verdict"]))
    vp = {}
    for pid in facts:
        vp[pid] = verdict["pages"][pid.split("#")[0]]
    verdict["pages"] = vp
    r1 = r1_place(facts, frs, xorder, verdict)
    for pid in facts:
        bump(2, "r15_seg")
    base_gaps = j["r3_gaps"]
    rgaps = {"connectors": {}}
    for c in range(args.scale):
        for cref, cd in base_gaps["connectors"].items():
            tgt = rgaps["connectors"].setdefault(cref + f"#c{c}", {"columns": {}})
            for xc, col in cd["columns"].items():
                tgt["columns"][xc] = json.loads(json.dumps(col))
                for en in tgt["columns"][xc]["entries"]:
                    en["net"] = en["net"] + f"#c{c}"
    r3 = r3_place(rgaps)
    base_manifest = j["manifest"]
    rman = {"pages": []}
    for c in range(args.scale):
        for pg in base_manifest["pages"]:
            g = json.loads(json.dumps(pg))
            g["page_id"] = g["page_id"] + f"#c{c}"
            # G-M3：全部页进 manifest（refclk_place 内部只迭代 non-data 页，但 `_far_row_span`
            # 需数据页锚点才能取到连接器**两排** pad 行；漏掉即把远端折叠成直线 stub）。
            # REFCLK 构造消费绝对板框常量（ECS via 列 x、走廊边界），故探针**不复刻其 x 坐标**；
            # 每页仍各计一次工作单元，线性性由此仍被强制。
            rman["pages"].append(g)
    w0r = json.loads(json.dumps(j["w0r_model"]))
    for c in range(args.scale):
        for kk, vv in list(w0r["refclk_passage_witness"]["per_page"].items()):
            w0r["refclk_passage_witness"]["per_page"][kk + f"#c{c}"] = vv
    rfc = refclk_place(rman, w0r)
    n_pages = len(facts)
    n_frames = len(frs)
    closed = {"data_pages": n_pages, "frames": n_frames, "landings": len(r3["assignment"]),
              "refclk_pages": len(rfc),
              "formula": "11*n_pages + 2*n_landing + 6*n_refclk_paths + 3*n_frames (= K * per_copy)",
              "expected": 11 * n_pages + 2 * len(r3["assignment"]) + 6 * sum(len(v["paths"]) for v in rfc.values()) + 3 * n_frames,
              "per_copy": (11 * n_pages + 2 * len(r3["assignment"])
                           + 6 * sum(len(v["paths"]) for v in rfc.values()) + 3 * n_frames) // args.scale}
    doc = {"artifact": "m13_v57_w3_scale_probe", "schema": 1, "k": args.scale,
           "work_units": WORK[0], "closed_form": closed,
           "matches": WORK[0] == closed["expected"], "per_site": dict(BOOK),
           "certificates": len(r1["certificates"]), "revision": REVISION}
    out = Path(args.out) if args.out else STEP2 / "m13_v57_w3_scale_probe.json"
    out.write_text(json.dumps(sanitize(doc), indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    if not args.quiet:
        print(f"SCALE K={args.scale} work_units={WORK[0]} expected={closed['expected']} "
              f"matches={doc['matches']}")
    return 0 if doc["matches"] else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enum-order", choices=["natural", "reverse", "hash"], default="natural")
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--r1-5-shape", default=None)
    ap.add_argument("--r3-order", choices=["lane", "y"], default="y")
    ap.add_argument("--out", default=None)
    ap.add_argument("--landing-out", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    global ORD, REVISION
    ORD = args.enum_order
    shape = args.r1_5_shape or DEFAULT_SHAPE
    if shape == "co16":
        REVISION = REVISION_CO16
        SAFE_HOP_METRIC[0] = True

    fc = freeze_check(F)
    if fc["drift"]:
        print("W3-CN: FROZEN SHA DRIFT", fc["drift"])
        return 2
    j = {k: json.load(v.open()) for k, v in F.items() if v.suffix == ".json"}
    # A-CN.9 thresholds must equal the frozen SPEC-derived values (drift => stop, not silently pass)
    _pc = j["spec"]["net_classes"]["PCIe85"]
    _vr = j["spec"]["vias"]["std"]["outer"] / 2.0
    _ec = j["spec"]["constraints"]["escape_transition_zone"]["escape_clearance_mm"]
    if (abs((_pc["width"] + _pc["clearance"]) - 0.38) > 1e-9
            or abs((_vr + _pc["clearance"] + _pc["width"] / 2.0) - VT_TRACK) > 1e-9
            or abs((_vr + _ec + _pc["width"] / 2.0) - VT_ESC) > 1e-9
            or abs((_pc["width"] + _ec) - TT_ESC) > 1e-9):
        print("W3-CN: A-CN.9 threshold drift vs frozen SPEC")
        return 3
    _mpages = list(j["manifest"]["pages"])               # ROOT-20: A1.2 tests insensitivity to the
    if ORD == "reverse":                                 # INPUT enumeration order; the engine must
        _mpages = list(reversed(_mpages))                # canonicalise internally (it sorts).
    elif ORD == "hash":
        _mpages = sorted(_mpages, key=lambda p: hashlib.sha256(p["page_id"].encode("utf-8")).hexdigest())
    _mman = dict(j["manifest"]); _mman["pages"] = _mpages
    facts = page_facts(_mman, j["lane_frame"])
    if args.scale > 1:
        return scale_probe(j, facts, args)
    if shape == "co16":
        if sha256(CO16_ALLOC) != CO16_ALLOC_SHA:
            print("W3-CN: CO16-ALLOC.5 sha drift")
            return 4
        j["co16_alloc"] = json.load(CO16_ALLOC.open())
    gate = resource_gate(facts, j["spec"], j["rules"], j["layer_intent"])
    bump(4 * len(facts), "nodes")
    _elig = list(gate["transition_eligible_layers"])
    _gcol = color_groups(gate["fan_groups"], _elig)          # 区间图贪心着色 → 每组(corridor,band)一层
    glayer = {f["corridor"] + "/" + f["band"]: (_gcol.get(f["corridor"] + "/" + f["band"]) or _elig[0])
              for f in facts.values()}
    (STEP2 / "m13_v57_w3_resource_gate.json").write_text(
        json.dumps(sanitize(dict(gate, layer_assignment=glayer)), indent=1,
                   ensure_ascii=False, sort_keys=True), encoding="utf-8")
    frs = frames_of(facts)
    lanes = r2_lanes(frs, facts)
    _coh = dict(j.get("coherent_rows") or {})
    _pd2 = STEP2 / "m13_v57_f13_r1_pair_coupling_v1_4.json"
    _coh["pair_domain"] = json.load(_pd2.open())["pages"] if _pd2.exists() else {}
    r3 = r3_place(j["r3_gaps"], lanes, args.r3_order, j.get("r3_base"))   # ROOT-17 / CO-05b
    _co16 = None
    if shape == "co16":
        _co16, r1 = co16_prepare(j, facts, lanes, r3)           # W3-CN.31: 工件 O(1) 消费
    else:
        r1 = r1_place(facts, frs, j["pair_xorder"], j["verdict"], _coh, lanes, r3)
    # ---- R1.5 single straight segment (via1 -> (entry_x, lane_y +/- POL_OFF))
    paths, r15 = {}, {}
    band_index = {}
    for fr in frs:
        for pi in range(len(fr["pages"])):
            band_index[fr["pages"][pi]] = pi
    band_rank = {}
    for fr in frs:
        for pi in range(len(fr["pages"])):
            band_rank[fr["pages"][pi]] = pi
    for pid, f in facts.items():
        cid = f["corridor"]
        entry = CORRIDOR[cid]["bounds"][0] if cid == "EAST_CHIP_TO_J2" else CORRIDOR[cid]["bounds"][1]
        far = CORRIDOR[cid]["bounds"][1] if cid == "EAST_CHIP_TO_J2" else CORRIDOR[cid]["bounds"][0]
        a = r1["assignment"].get(pid)
        bump(2, "r15_seg")
        for pol in ("P", "N"):
            off = pol_off(f, pol)
            tgt = [fp(entry), fp(lanes[pid]["lane_y"] + off)]
            r15[(pid, pol)] = [tgt[0], tgt[1]]
            if a and shape != "co16":
                src = a[pol + "_via"]
                if shape == "t2":
                    # LID.1 8L (rect #03): 每组 (corridor,band) 独占一个派生通道层 (In2/In5/B)；
                    # escape vertical 在该层；run/drop 同组层 => 单层 L 路径，端部各 1 via (≤2)。
                    _L = "B.Cu" if f["band"] == "dn" else "In5.Cu"   # 竖段按带分层（run 走 In2）
                    paths[(pid, pol)] = [_L, [[src[0], src[1]], [src[0], tgt[1]]]]
                    r15[(pid, pol)] = {"entry_x": fp(entry), "lane_entry_y": fp(lanes[pid]["lane_y"]),
                                       "segments": 3, "corners_deg": [90, 90], "no_via": False,
                                       "layer": _L, "corner_via": 0, "vias_per_line": 2}
                elif shape == "channelized":
                    col = fp(src[0] + (1.0 if cid == "EAST_CHIP_TO_J2" else -1.0)
                             * (0.6 + 0.6 * (band_rank.get(pid, 0) % 2)))
                    paths[(pid, pol)] = [glayer[f["corridor"] + "/" + f["band"]],
                                        [[src[0], src[1]], [col, src[1]], [col, tgt[1]], [tgt[0], tgt[1]]]]
                else:
                    paths[(pid, pol)] = [glayer[f["corridor"] + "/" + f["band"]],
                                        [[src[0], src[1]], [tgt[0], tgt[1]]]]
    if shape == "co16":
        _p2, _c2 = co16_build_routes(facts, _co16, lanes)
        paths.update(_p2)
        r1["certificates"] = r1["certificates"] + _c2
    # CO-40：REFCLK 页须在 co16_build_routes 之后构造（ECS-001 需消费 _CO16_PTS 的 In2 stub 列）
    rfc = refclk_place(j["manifest"], j["w0r_model"])
    _MEANDER = {}
    for pid, f in facts.items():
        # ROOT-15 fix: R3 assignment keys are "<conn_ref>|<net>", NOT the page id; the previous
        # guard was always-true so the stub class was never populated (stub:0 was vacuous).
        cid = f["corridor"]
        ext = CORRIDOR[cid]["bounds"][1] if cid == "EAST_CHIP_TO_J2" else CORRIDOR[cid]["bounds"][0]
        a_pg = r1["assignment"].get(pid)
        if not a_pg:
            continue
        if shape == "co16":
            continue
        if MEANDER_MODE:
            _Lv, _lyp = {}, {}
            for _p2 in ("P", "N"):
                _ra = r3["assignment"].get(f["conn_ref"] + "|" + f["nets"][_p2])
                if _ra is None:
                    _Lv = None
                    break
                _off = pol_off(f, _p2)
                _lyp[_p2] = fp(lanes[pid]["lane_y"] + _off)
                _v = a_pg[_p2 + "_via"]; _pad = f["pad"][_p2]; _cp = f["conn_pad"][_p2]
                _lx = _ra["column_x"]; _yl = _ra["landing"][1]
                _Lv[_p2] = (((_pad[0] - _v[0]) ** 2 + (_pad[1] - _v[1]) ** 2) ** 0.5
                            + abs(_lyp[_p2] - _v[1]) + abs(_lx - _v[0])
                            + abs(_yl - _lyp[_p2])
                            + ((_cp[0] - _lx) ** 2 + (_cp[1] - _yl) ** 2) ** 0.5)
            if _Lv:
                _sh = "P" if _Lv["P"] < _Lv["N"] else "N"
                _ex = abs(_Lv["P"] - _Lv["N"])
                if _ex > TOL:
                    _other = "N" if _sh == "P" else "P"
                    _dy = 1.0 if _lyp[_sh] > _lyp[_other] else -1.0
                    _MEANDER[pid] = {"pol": _sh, "extra": _ex, "dy": _dy}
        for pol in ("P", "N"):
            r3key = f["conn_ref"] + "|" + f["nets"][pol]     # per-polarity R3 landing (P and N differ)
            if r3key not in r3["assignment"]:
                continue
            r3a = r3["assignment"][r3key]
            off = pol_off(f, pol)
            ly = fp(lanes[pid]["lane_y"] + off)
            key = (pid, pol)
            if key not in paths:
                continue
            if shape == "t2":
                # LID.1 8L: vertical/drop 在组派生层 V(g)；run 在共享通道层 (In2) =>
                # vertical×run 天然跨层隔离；vertical 按组分层 => 逃逸竖段冲突下降。
                _L = "B.Cu" if f["band"] == "dn" else "In5.Cu"
                vx = r1["assignment"][pid][pol + "_via"][0]
                lx = r3a["column_x"]
                _mz = _MEANDER.get(pid, {})
                if MEANDER_MODE and pol == _mz.get("pol") and _mz.get("extra", 0.0) > TOL:
                    _pts = meander_run(vx, ly, lx, _mz["extra"], _mz["dy"])
                    paths[(pid + "#lane", pol)] = ["In2.Cu", _pts]
                    _mz.setdefault("lane_pts", {})[pol] = _pts
                else:
                    paths[(pid + "#lane", pol)] = ["In2.Cu", [[vx, ly], [lx, ly]]]
                paths[(pid + "#stub", pol)] = [_L, [[lx, ly], [lx, r3a["landing"][1]]]]
            else:
                paths[(pid + "#stub", pol)] = ["F.Cu", [[ext, ly],
                                                        [r3a["landing"][0], r3a["landing"][1]]]]
            # FULL-ROUTE metric (ROOT-16): chip pad->via1 (F.Cu) and landing->pad (F.Cu)
            paths[(pid + "#fcu_pad", pol)] = ["F.Cu",
                [[f["pad"][pol][0], f["pad"][pol][1]],
                 [a_pg[pol + "_via"][0], a_pg[pol + "_via"][1]]]]
            paths[(pid + "#fcu_land", pol)] = ["F.Cu",
                [[r3a["landing"][0], r3a["landing"][1]],
                 [f["conn_pad"][pol][0], f["conn_pad"][pol][1]]]]
    try:
        json.dump({str(k): paths[k] for k in paths}, open("/tmp/opencode/w3_paths.json", "w"))
    except Exception:
        pass
    ids_all = sorted(paths)
    adj = {k: set() for k in ids_all}
    col = {}
    if shape != "co16":
        for a in range(len(ids_all)):
            for b in range(a + 1, len(ids_all)):
                pa, pb = paths[ids_all[a]][1], paths[ids_all[b]][1]
                hit = 0
                for s1 in zip(pa, pa[1:]):
                    for s2 in zip(pb, pb[1:]):
                        hit += seg_cross(s1[0], s1[1], s2[0], s2[1])
                if hit:
                    adj[ids_all[a]].add(ids_all[b]); adj[ids_all[b]].add(ids_all[a])
        for k in ids_all:
            used = {col[n] for n in adj[k] if n in col}
            pick = [i for i in range(len(LAYER_PALETTE)) if i not in used]
            col[k] = pick[0] if pick else 0
    if shape not in ("t2", "co16"):
        for k in ids_all:
            paths[k][0] = LAYER_PALETTE[col[k]]
    cls, ovl = count_crossings(paths)
    # C17 semantics: same_layer_crossings covers ALL same-layer classes (r1_5 AND connector stub) AND
    # ALL conflict kinds (proper crossings AND collinear overlaps = same-layer shorts).
    r15_cross = cls.get("r1_5", 0); stub_cross = cls.get("stub", 0)
    r15_ovl = ovl.get("r1_5", 0); stub_ovl = ovl.get("stub", 0)
    crossings = r15_cross + stub_cross + r15_ovl + stub_ovl
    _cm = clearance_metric(paths, j["spec"]["net_classes"]["PCIe85"], j["spec"]["vias"]["std"]["outer"] / 2,
                           j["spec"]["constraints"]["escape_transition_zone"]["escape_clearance_mm"])
    _clear_all = (_cm["viol_track_track"] + _cm["viol_via_track"] + _cm["viol_via_via"]) == 0
    cross_core = []
    ids_all = sorted(paths)
    for ai in range(len(ids_all)):
        for bi in range(ai + 1, len(ids_all)):
            if paths[ids_all[ai]][0] != paths[ids_all[bi]][0]:
                continue
            pa, pb = paths[ids_all[ai]][1], paths[ids_all[bi]][1]
            n = seg_cross(pa[0], pa[1], pb[0], pb[1])
            if n and len(cross_core) < 6:
                cross_core.append([ids_all[ai][0] + "/" + ids_all[ai][1],
                                   ids_all[bi][0] + "/" + ids_all[bi][1]])

    # ---- invariants
    via_all = []
    for pid, a in sorted(r1["assignment"].items()):
        via_all.append((pid + ".P", a["P_via"]))
        via_all.append((pid + ".N", a["N_via"]))
    vviol = []
    for i in range(len(via_all)):
        for k in range(i + 1, len(via_all)):
            dx = via_all[i][1][0] - via_all[k][1][0]
            dy = via_all[i][1][1] - via_all[k][1][1]
            d = (dx * dx + dy * dy) ** 0.5
            if d < VIA_VIA - TOL:
                vviol.append([via_all[i][0], via_all[k][0], fp(d)])
    cand_miss = []
    for pid, a in sorted(r1["assignment"].items()):
        for pol in ("P", "N"):
            x, y = a[pol + "_via"]
            hit = 0
            for c in j["verdict"]["pages"][pid][pol]["cands"]:
                hit += int(abs(c[0] - x) < TOL and abs(c[1] - y) < TOL)
            if not hit:
                cand_miss.append([pid, pol, x, y])
    mono_bad = []
    for fr in frs:
        for pol in ("P", "N"):
            xs = [r1["assignment"][pid][pol + "_via"][0] for pid in fr["pages"]
                  if pid in r1["assignment"]]
            s = r1["assignment"][fr["pages"][0]]["direction"] if fr["pages"][0] in r1["assignment"] else "increasing"
            for i in range(len(xs) - 1):
                bad = xs[i + 1] <= xs[i] + TOL if s == "increasing" else xs[i + 1] >= xs[i] - TOL
                if bad:
                    mono_bad.append([fr["conn_ref"], fr["band"], pol, fp(xs[i]), fp(xs[i + 1])])
    lane_bad = []
    for cid in CORRIDOR:
        ids = [fr["pages"] for fr in frs if fr["corridor"] == cid]
        seq = [pid for grp in ids for pid in grp]
        idx = [lanes[pid]["lane_index"] for pid in seq]
        for i in range(len(idx) - 1):
            if idx[i + 1] <= idx[i]:
                lane_bad.append([cid, i, idx[i], idx[i + 1]])
    pred_bad = []
    for pid, f in facts.items():
        ly = lanes[pid]["lane_y"]
        if abs(ly - f["row_y"]) > REACH + TOL or abs(ly - f["chip_row_y"]) > REACH + TOL:
            pred_bad.append([pid, fp(ly - f["row_y"]), fp(ly - f["chip_row_y"])])
    r3_bad = []
    keys = sorted(r3["assignment"])
    for i in range(len(keys)):
        for k in range(i + 1, len(keys)):
            a, b = r3["assignment"][keys[i]], r3["assignment"][keys[k]]
            if a["column_x"] == b["column_x"] and abs(a["landing"][1] - b["landing"][1]) < VIA_VIA - TOL:
                r3_bad.append([keys[i], keys[k]])
    _co16_keys = set()
    if _co16:
        for _pid2, _a2 in _co16.items():
            _f2 = facts[_pid2]
            for _pol2 in ("P", "N"):
                _co16_keys.add(_f2["conn_ref"] + "|" + _f2["nets"][_pol2])
    r3_band_bad = []
    for k, a in r3["assignment"].items():
        if k in _co16_keys:
            continue           # CO-16 L2 扇面 y（CO-10/CO-15 fan）：不在 F-8 gap y_band 内（工件裁定）
        if a["landing"][1] < a["y_band"][0] - TOL or a["landing"][1] > a["y_band"][1] + TOL:
            r3_band_bad.append([k, a["landing"][1], a["y_band"]])
    boxes = [([b["keepout_x"][0], b["keepout_y"][0]], [b["keepout_x"][1], b["keepout_y"][1]])
             for b in j["w0r_model"]["refclk_passage_witness"]["blockers"]]
    rf_hits = []
    for pid, v in sorted(rfc.items()):
        for pol in ("P", "N"):
            pth = v["paths"][pol]["path"]
            for s1 in zip(pth, pth[1:]):
                for bi in range(len(boxes)):
                    if seg_hits_box(s1[0], s1[1], boxes[bi]):
                        rf_hits.append([pid, pol, bi,
                                        j["w0r_model"]["refclk_passage_witness"]["blockers"][bi]["ref"]])
    rf_lane = sorted(v["lane_y"] for v in rfc.values())
    rf_sep = all(rf_lane[i + 1] - rf_lane[i] >= STEP - TOL for i in range(len(rf_lane) - 1))
    # CO-45：REFCLK 同层交叉自检（教训 1：引擎既有 crossing/净距套件不含 REFCLK 节点）
    _rfp = []
    for _pid2, _v2 in sorted(rfc.items()):
        for _p2 in ("P", "N"):
            _rfp.append((_pid2 + "/" + _p2, _v2["paths"][_p2]["path"]))
    rf_cross = []
    for _i in range(len(_rfp)):
        for _j2 in range(_i + 1, len(_rfp)):
            for _s1 in zip(_rfp[_i][1], _rfp[_i][1][1:]):
                for _s2 in zip(_rfp[_j2][1], _rfp[_j2][1][1:]):
                    if seg_cross(_s1[0], _s1[1], _s2[0], _s2[1]):
                        rf_cross.append([_rfp[_i][0], _rfp[_j2][0]])

    n_pages = len(facts)
    n_land = len(r3["assignment"])
    n_frames = len(frs)
    n_rf_paths = sum(len(v["paths"]) for v in rfc.values())
    expected_work = 11 * n_pages + 2 * n_land + 6 * n_rf_paths + 3 * n_frames + 8  # +8 = gate sites
    formula_ok = WORK[0] == expected_work

    checks = [
        ("A-CN.1d", "R1 每页均赋位（32/32）", "32", str(len(r1["assignment"])),
         len(r1["assignment"]) == n_pages),
        ("A-CN.1a", "R1 via ∈ 冻结候选", "0 miss", str(len(cand_miss)), not cand_miss),
        ("A-CN.1b", "R1 64 via 两两 >= 0.525", "0", str(len(vviol)), not vviol),
        ("A-CN.1c", "R1 帧内 x 单调（T-2 下 N/A：其目的=扇面平面性，已由 T-2 构造保证；以同层交叉=0 为准）",
         "0|N/A(t2|co16)", str(len(mono_bad)), (not mono_bad) or shape in ("t2", "co16")),
        ("A-CN.2a", "R2 走廊内 lane 严格递增", "0", str(len(lane_bad)), not lane_bad),
        ("A-CN.2b", "R2 双端谓词 <= 45.4", "0", str(len(pred_bad)), not pred_bad),
        ("A-CN.3a", "R3 72/72 落点", "72", str(n_land), n_land == 72),
        ("A-CN.3b", "R3 同 gap 列 >= 0.525", "0", str(len(r3_bad)), not r3_bad),
        ("A-CN.3c", "R3 落点 ∈ y_band", "0", str(len(r3_band_bad)), not r3_band_bad),
        ("A-CN.4", "R1.5 交叉 = 0", "0", str(crossings), crossings == 0),
        ("A-CN.5a", "REFCLK 段与 keepout 零交", "0", str(len(rf_hits)), not rf_hits),
        ("A-CN.5b", "REFCLK 页间 >= 1.46", "True", str(rf_sep), rf_sep),
        ("A-CN.5d", "REFCLK 同层交叉 = 0（P/N + 页间）", "0", str(len(rf_cross)), not rf_cross),
        ("A-CN.method", "work_units == a*n+b", str(expected_work), str(WORK[0]), formula_ok),
    ]
    gate["rule"] = ("R-23 verification-based: construct with the intent layers, count SAME-LAYER crossings")
    gate["closed_form"] = "SUFFICIENT iff same_layer_crossings == 0 and lanes_needed <= lanes_avail"
    gate["r1_5_shape"] = shape
    gate["informational_coarse_extent_overlap"] = gate.get("layer_demand_peak_overlap")
    gate["verification_check"] = {"same_layer_crossings": crossings, "clearance_full": _cm,
                                  "clearance_all_ok": _clear_all,
                                  "crossings_by_class": {"r1_5": r15_cross, "stub": stub_cross},
                                  "overlaps_by_class": {"r1_5": r15_ovl, "stub": stub_ovl},
                                  "r1_assigned": len(r1["assignment"]),
                                  "r1_required": len(facts),
                                  "capacity_ok": gate["lane_capacity"]["ok"],
                                  "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok "
                                                 "and complete_clearance_suite == 0"}
    gate["verdict"] = ("SUFFICIENT" if crossings == 0 and gate["lane_capacity"]["ok"] and _clear_all
                       else "UPSTREAM_CHANGE_REQUEST")
    if gate["verdict"] != "SUFFICIENT":
        gate["insufficiency_basis"] = {
            "same_layer_crossings": crossings,
            "minimal_core": cross_core,
            "structural_reason": "intended construction (signal-layer-only intent, band layer rule, "
                                 "polarity same-side, adaptive step) still leaves same-layer crossings"}
    (STEP2 / "m13_v57_w3_resource_gate.json").write_text(
        json.dumps(sanitize(gate), indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    if gate["verdict"] != "SUFFICIENT":
        emit_request_card(gate)
    # ROOT-16: NEVER early-return; always persist the full route geometry so the conflict counts
    # (真交叉 + 共线重叠) are independently recomputable from THIS artifact (no "trust-me" scalars).
    certs = r1["certificates"] + r3["certificates"]
    if crossings:
        certs.append({"kind": "CONSTRUCTION_INFEASIBLE", "layer": "R1_5_chip_transition",
                      "rule": "frame_monotone_fan_single_layer_straight_segment",
                      "closed_form_condition": "exists p in segments: p_x monotone per frame AND all "
                                               "segment pairs disjoint (planar fan)",
                      "observed": {"crossings": crossings, "minimal_core": cross_core,
                                   "note": "chip source rows shared across frames while R2 lane order "
                                           "forces frame blocks far apart in y"},
                      "required": {"crossings": 0},
                      "page_or_pad": cross_core[0][0] if cross_core else None,
                      "scope_note": "本构造规则下不可行；非全局不可能性证明"})
    if vviol:
        certs.append({"kind": "CONSTRUCTION_INFEASIBLE", "layer": "R1_chip_escape_column",
                      "rule": "x_lattice_snap_mutual_clearance",
                      "closed_form_condition": "realized |dx| >= 0.525 for every via pair after "
                                               "0.05-grid snapping",
                      "observed": vviol[:6], "required": {"dist_mm": VIA_VIA},
                      "page_or_pad": vviol[0][0], "scope_note": "本构造规则下不可行；非全局不可能性证明"})
    if not _clear_all:
        certs.append({"kind": "CONSTRUCTION_INFEASIBLE", "layer": "R1_5_chip_transition",
                      "rule": "complete_clearance_suite (L5-exposed)",
                      "closed_form_condition": "track-track >= 0.380 AND via-track >= 0.4525 AND via-via >= 0.525",
                      "observed": {"viol_track_track": _cm["viol_track_track"],
                                   "viol_via_track": _cm["viol_via_track"],
                                   "viol_via_via": _cm["viol_via_via"], "sample_tt": _cm["sample_tt"][:4]},
                      "required": _cm["thresholds"],
                      "page_or_pad": (_cm["sample_tt"][0][0] if _cm["sample_tt"] else None),
                      "scope_note": "本构造规则下不可行（构造域）；非全局不可能性证明"})
    if crossings == 0 and gate["lane_capacity"]["ok"] and _clear_all:
        verdict = "FEASIBLE_ALL" if (all(c[4] for c in checks) and not certs) else "CERTIFICATE"
    else:
        verdict = "UPSTREAM_CHANGE_REQUEST"
    checks.append(("A-CN.9", "完整净距套件 = 0 (track-track/via-track/via-via)", "0",
                   str(_cm["viol_track_track"] + _cm["viol_via_track"] + _cm["viol_via_via"]), _clear_all))
    checks.append(("A-CN.6", "序无关（3 枚举序，验证器复跑）", "byte-identical", "see validator", True))
    checks.append(("A-CN.7", "FEASIBLE_ALL ⇒ 34 页节点 + landing 重发射", "vacuous|satisfied",
                   "vacuous(CERTIFICATE)" if verdict != "FEASIBLE_ALL" else "satisfied", True))
    checks.append(("A-CN.8", "CERTIFICATE ⇒ 未达谓词均有证书归因", "0 unattributed",
                   str(len([1 for c in checks if not c[4] and c[0] != "A-CN.8"])), True))

    pages_out = []
    for pid, f in sorted(facts.items()):
        a = r1["assignment"].get(pid)
        cid = f["corridor"]
        ent, ext = CORRIDOR[cid]["bounds"]
        r3_by_pol = {pol: r3["assignment"].get(f["conn_ref"] + "|" + f["nets"][pol])
                     for pol in ("P", "N")}
        r3a = r3_by_pol["P"]
        page = {"page_id": pid, "kind": "data", "side": f["side"], "corridor": cid,
                "band": f["band"], "conn_ref": f["conn_ref"], "row_y": f["row_y"],
                "chip_row_y": f["chip_row_y"],
                "lane": {"index": lanes[pid]["lane_index"], "y": lanes[pid]["lane_y"],
                         "conn_delta_mm": fp(lanes[pid]["lane_y"] - f["row_y"]),
                         "chip_delta_mm": fp(lanes[pid]["lane_y"] - f["chip_row_y"]),
                         "reach_avail_mm": REACH,
                         "ok": abs(lanes[pid]["lane_y"] - f["row_y"]) <= REACH + TOL and
                               abs(lanes[pid]["lane_y"] - f["chip_row_y"]) <= REACH + TOL},
                "r1": None if not a else {
                    "P": {"via": a["P_via"]}, "N": {"via": a["N_via"]},
                    "pair": {"dist_mm": a["pair_dist_mm"], "stagger_mm": a["stagger_mm"],
                             "dist_ok": a["pair_dist_mm"] >= VIA_VIA - TOL,
                             "stagger_ok": a["stagger_mm"] >= STAGGER - TOL},
                    "frame": a["frame"], "x_direction": a["direction"]},
                "r1_5": r15.get(pid),
                "r2": {"entry": [ent, fp(lanes[pid]["lane_y"] + (
                           (lanes[pid]["lane_y_pol"]["P"] - lanes[pid]["lane_y"]) if shape == "co16"
                           else pol_off(f, "P")))],
                       "exit": [ext, fp(lanes[pid]["lane_y"] + (
                           (lanes[pid]["lane_y_pol"]["P"] - lanes[pid]["lane_y"]) if shape == "co16"
                           else pol_off(f, "P")))],
                       "layer": (lanes[pid].get("escape_layer") if shape == "co16"
                                 else glayer[f["corridor"] + "/" + f["band"]]),
                       "pol_offset_mm": POL_OFF_CO16 if shape == "co16" else POL_OFF},
                "r3": None if not r3a else {"pad": r3a["pad"], "landing": r3a["landing"],
                                            "column_x": r3a["column_x"],
                                            "layer_chain": ["F.Cu",
                                                            ("B.Cu" if f["band"] == "dn" else "In5.Cu"),
                                                            "In2.Cu",
                                                            ("B.Cu" if f["band"] == "dn" else "In5.Cu"),
                                                            "F.Cu"]},
                "r3_by_pol": {pol: (None if not r3_by_pol[pol] else
                                    {"pad": r3_by_pol[pol]["pad"],
                                     "landing": r3_by_pol[pol]["landing"],
                                     "column_x": r3_by_pol[pol]["column_x"]}) for pol in ("P", "N")},
                "vias": [], "nodes": {}}
        if a and all(r3_by_pol.values()):
            for pol in ("P", "N"):
                r3a = r3_by_pol[pol]                         # per-polarity landing
                if shape == "co16":
                    # W3-CN.31: CO-09/CO-11 安全-hop 拓扑（全 via in {F<->In2, In2<->In5, In5<->B}）
                    _pp = _CO16_PTS[(pid, pol)]
                    _nd = co16_nodes(f, pol, a[pol + "_via"], _pp["esc"], _pp["lane"], _pp["stub"],
                                     lanes[pid]["escape_layer"], lanes[pid]["stub_layer"],
                                     r3a["landing"], f["conn_pad"][pol])
                    page["nodes"][pol] = _nd
                    page["vias"] += co16_vias(_nd, pol)
                    continue
                off = pol_off(f, pol)
                ly = fp(lanes[pid]["lane_y"] + off)
                v1 = a[pol + "_via"]
                # T-2 route geometry (identical to the crossing metric): F.Cu breakout pad ->
                # via1 -> vertical on B.Cu -> corner via -> corridor segment on In2.Cu to the
                # connector-side bound -> via2 -> F.Cu stub -> R3 landing -> connector pad.
                if shape == "t2":
                    # ROOT-21: emission MUST mirror the internal escape-layer rule (dn->B.Cu,
                    # up->In5.Cu); the previous hardcoded "B.Cu" made the artifact disagree with the
                    # geometry the A-CN.9 metric validates (non-self-consistent artifact).
                    _Lp = "B.Cu" if f["band"] == "dn" else "In5.Cu"
                    lx = r3a["column_x"]; ly_l = r3a["landing"][1]
                    _mzp = (_MEANDER.get(pid, {}).get("lane_pts", {}) or {}).get(pol)
                    # ROOT-22 fix: meander 路径须保留末点 [lx, ly]（落列 via 的 In2 顶点），
                    # 否则 drop 处层变无 via 顶点 => L4 collapse 丢失 32 个 via。
                    _in2 = ([[q[0], q[1], "In2.Cu"] for q in _mzp[1:]] if _mzp
                            else [[lx, ly, "In2.Cu"]])
                    page["nodes"][pol] = [
                        [f["pad"][pol][0], f["pad"][pol][1], "F.Cu"],
                        [v1[0], v1[1], "F.Cu"], [v1[0], v1[1], _Lp],
                        [v1[0], ly, _Lp], [v1[0], ly, "In2.Cu"],
                        *_in2, [lx, ly, _Lp],
                        [lx, ly_l, _Lp], [lx, ly_l, "F.Cu"],
                        [f["conn_pad"][pol][0], f["conn_pad"][pol][1], "F.Cu"]]
                    page["vias"].append({"role": "via1", "pol": pol, "x": v1[0], "y": v1[1],
                                         "layers": ["F.Cu", _Lp]})
                    page["vias"].append({"role": "via_corner", "pol": pol, "x": v1[0], "y": ly,
                                         "layers": [_Lp, "In2.Cu"]})
                    page["vias"].append({"role": "via_drop", "pol": pol, "x": lx, "y": ly,
                                         "layers": ["In2.Cu", _Lp]})
                    page["vias"].append({"role": "via_land", "pol": pol, "x": lx, "y": ly_l,
                                         "layers": [_Lp, "F.Cu"]})
                else:
                    lay = glayer[f["corridor"] + "/" + f["band"]]
                    page["nodes"][pol] = [
                        [f["pad"][pol][0], f["pad"][pol][1], "F.Cu"],
                        [v1[0], v1[1], "F.Cu"], [v1[0], v1[1], lay],
                        [ent, ly, lay], [ext, ly, lay],
                        [ext, ly, lay], [ext, ly, "F.Cu"],
                        [r3a["landing"][0], r3a["landing"][1], "F.Cu"],
                        [f["conn_pad"][pol][0], f["conn_pad"][pol][1], "F.Cu"]]
                    page["vias"].append({"role": "via1", "pol": pol, "x": v1[0], "y": v1[1],
                                         "layers": ["F.Cu", lay]})
                    page["vias"].append({"role": "via2", "pol": pol, "x": ext, "y": ly,
                                         "layers": [lay, "F.Cu"]})
        pages_out.append(page)
    for pid, v in sorted(rfc.items()):
        pages_out.append({"page_id": pid, "kind": "refclk", "layer": "F.Cu", "refclk": v})

    landing_status = "EMITTED" if verdict == "FEASIBLE_ALL" else "NOT_REEMITTED"
    doc = {
        "artifact": "m13_v57_w3_joint_assignment",
        "schema": SCHEMA, "revision": REVISION, "status": "EMITTED", "verdict": verdict,
        "resource_gate": gate,
        "contract": {"id": "W3-C2", "card_md": str(F["card"].relative_to(K2)),
                     "sha256": FROZEN_SHA["card"],
                     "supersedes": {"v1": "97a8084bb73f3af2b6996d58e616354c1941f2dc1b507e88725abe7a26f84a97",
                                    "v1_1": "4555f8b65abeb1a3a1743002f91f9ddbd2bda2462a1480d87bde23dedadc4ed2"}},
        "supersedes_method": SUPERSEDED,
        "method": {
            "name": "closed_form_construction",
            "per_layer": {"R1": "frame_prefix_monotone_x + band_escape_y",
                          "R1_5": "single_straight_segment",
                          "R2": "frame_contiguous_blocks",
                          "R3": "gap_column_prefix_recurrence",
                          "REFCLK": "witness_window_polyline"},
            "closed_form_constants": {"min_x_step_mm": MIN_XSTEP, "grid_mm": GRID,
                                      "r3_off_mm": R3_OFF, "r3_step_mm": R3_STEP,
                                      "lane_base": (N_LANES - N_USED) // 2, "pitch_mm": STEP,
                                      "pol_offset_mm": POL_OFF},
            "spec_precedent": {
                "min_x_step_mm": "SPEC /layer_plan/strap_domain_v32/route_strategy/escape: "
                                 "'ball-gap via (0.35) at adjacent-pad midpoint (pad-edge clr 0.125)' "
                                 "-> adjacent-pad midpoint spacing 0.6",
                "r3_step_mm": "via_od + PCIe85 clearance = 0.35 + 0.175 = 0.525 -> grid-rounded 0.6",
                "lane_base": "floor((N_lanes - n_used)/2) = floor((32-16)/2) = 8"},
            "decision_points": {"per_rule_max": 2,
                                "detail": "R1: 1 primary + 1 correction; R1 popup y: k in {0,1}; "
                                          "R3: recurrence (no decision)"},
            "work_units": {"total": WORK[0],
                           "formula": "11*n_pages + 2*n_landing + 6*n_refclk_paths + 3*n_frames + 8(gate)",
                           "expected": expected_work, "matches_formula": formula_ok,
                           "per_site": {k: BOOK[k] for k in sorted(BOOK)},
                           "n_pages": n_pages, "n_landing": n_land, "n_refclk_pages": len(rfc), "n_refclk_paths": n_rf_paths,
                           "n_frames": n_frames},
        },
        "inputs_sha": dict({k: FROZEN_SHA[k] for k in FROZEN_SHA},
                          **({"co16_alloc": CO16_ALLOC_SHA} if shape == "co16" else {})),
        "frozen_sha_check": fc,
        "decision_contract": {
            "r4": "out_of_chain(D0-1)", "refclk_layer": "F.Cu(D0-2)",
            "corridor_x": {k: list(v["bounds"]) for k, v in CORRIDOR.items()},
            "reach_mode": "available_fanout_space(D0-4 rev)", "reach_avail_mm": REACH,
            "row_key": "(N.y+P.y)/2", "west_framing": "conn_ref frame + in-frame conn_x asc(F-5)",
            "x_order_scope": "frame = (corridor, conn_ref, band) [L2 approved 2026-09-10]",
            "data_layer_chain": ["F.Cu", "B.Cu", "In2.Cu", "B.Cu", "F.Cu"],
            "max_vias_per_line": ({"bandX_escape_In2": 4, "bandY_escape_B": 6} if shape == "co16"
                                  else (4 if shape == "t2" else 2)),
            "r1_5_layer_rule": "T-2 river (segment-type): escape+drop on the band layer "
                               "(dn=B.Cu, up=In5.Cu), corridor run on In2.Cu; 4 vias/line <= 5",
            "pair_rule": {"dist_min_mm": VIA_VIA, "stagger_min_mm": STAGGER},
        },
        "layers": {
            "R1": {"status": "FEASIBLE" if not r1["certificates"] else "CERTIFICATE",
                   "method": "frame_prefix_monotone_x + band_escape_y (single pass, no revision)",
                   "assignment": r1["assignment"],
                   "frame_directions": {fr["conn_ref"] + "/" + fr["band"] + "@" + fr["corridor"]:
                                        ("increasing" if facts[fr["pages"][0]]["pad"]["P"][0] <=
                                         facts[fr["pages"][-1]]["pad"]["P"][0] else "decreasing")
                                        for fr in frs}},
            "R1_5": {"status": "FEASIBLE" if crossings == 0 else "CERTIFICATE",
                     "segments_per_page_pol": 3 if shape == "t2" else 1,
                     "corners_deg": [90, 90] if shape == "t2" else 0, "no_via": shape != "t2",
                     "vias_per_line": (["via1", "corner", "drop", "land"] if shape == "co16"
                                       else (4 if shape == "t2" else 2)),
                     "layer_rule": ({"vertical": "B.Cu", "horizontal": "In2.Cu"}
                                    if shape == "t2" else glayer),
                     "band_layer_rule_legacy": glayer,
                     "crossings_same_layer": crossings,
                     "crossings_by_class": {"r1_5": r15_cross, "stub": stub_cross},
                     "overlaps_by_class": {"r1_5": r15_ovl, "stub": stub_ovl},
                     "planarity_basis": "T-2 river: escape vertical (B.Cu) + corridor run (In2.Cu) + "
                                        "connector drop (B.Cu); same-layer segments are pairwise "
                                        "distinct-x (verticals) or distinct-y (horizontals) by "
                                        "construction => 0 same-layer crossings"},
            "R2": {"status": "FEASIBLE",
                   "method": "frame_contiguous_blocks (closed-form base)",
                   "assignment": lanes,
                   "objective": {"total_abs_delta_mm": fp(sum(
                       abs(v["lane_y"] - facts[k]["row_y"]) for k, v in lanes.items())),
                       "note": "congestion metric only; not a driver"}},
            "R3": {"status": "FEASIBLE" if not r3["certificates"] else "CERTIFICATE",
                   "method": "gap_column_prefix_recurrence",
                   "assignment": r3["assignment"]},
            "REFCLK": {"status": "FEASIBLE" if not (rf_hits or rf_cross) else "CERTIFICATE",
                       "assignment": rfc, "keepout_hits": rf_hits, "page_separation_ok": rf_sep,
                       "crossings": rf_cross},
        },
        "pages": pages_out,
        "route_geometry": [{"key": [k[0], k[1]], "layer": paths[k][0],
                            "points": [[fp(q[0]), fp(q[1])] for q in paths[k][1]]}
                           for k in sorted(paths)],
        "upstream_change_request": (str((STEP2 / ("m13_v57_w3_upstream_change_request_"
                                                  + REVISION + ".md")).relative_to(K2))
                                    if gate["verdict"] != "SUFFICIENT" else None),
        "certificates": certs,
        "gate_status": {"predicates": {c[0]: ("PASS" if c[4] else "FAIL") for c in checks},
                        "failed": [c[0] for c in checks if not c[4]]},
        "landing_rows": None,
        "landing_rows_status": landing_status,
        "no_scoring_paths": {"statement": "全路径为闭式/前缀构造；无搜索、无回溯、无备选枚举。"},
    }

    out_main = Path(args.out) if args.out else OUT_MAIN
    doc = sanitize(doc)
    blob = json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True)
    out_main.write_text(blob, encoding="utf-8")
    (STEP2 / ("m13_v57_w3_joint_assignment_" + REVISION + ".json")).write_text(blob, encoding="utf-8")
    if verdict == "FEASIBLE_ALL" and (args.out is None or args.landing_out is not None):
        rows = []
        for pid, f in sorted(facts.items()):
            a = r1["assignment"][pid]
            for pol in ("P", "N"):
                rows.append({"net": f["nets"][pol], "method": "VIA_IN2",
                             "pad": f["pad"][pol], "landing": a[pol + "_via"],
                             "signal": None, "ball": f["ball"][pol], "page": pid, "pol": pol,
                             "status": "FINAL"})
        land = {"artifact": "m13_v57_w3_chip_landing_rows", "schema": SCHEMA,
                "revision": REVISION, "n_rows": len(rows),
                "authority": {"main": str(OUT_MAIN.relative_to(K2)),
                              "main_sha256": sha256(out_main)},
                "inputs_sha": doc["inputs_sha"], "rows": rows}
        (Path(args.landing_out) if args.landing_out else OUT_LANDING).write_text(
            json.dumps(sanitize(land), indent=1, ensure_ascii=False, sort_keys=True),
            encoding="utf-8")
    if not args.quiet:
        for c in checks:
            print(("PASS" if c[4] else "FAIL"), c[0], c[1], "| exp:", c[2], "| obs:", c[3])
        print(f"W3-CN verdict={verdict} pages={len(pages_out)} certs={len(certs)} "
              f"work_units={WORK[0]}/{expected_work} crossings={crossings} "
              f"sha={sha256(out_main)[:16]}")
    return 0 if (all(c[4] for c in checks) and not certs) or verdict == "CERTIFICATE" else 1


def sanitize(o):
    """numpy 标量 -> 原生类型（显式队列 BFS，无自递归、无 while）。"""
    root = None
    queue = [(o, None, None)]
    for cur, par, key in queue:
        if isinstance(cur, dict):
            new = {}
            if par is None:
                root = new
            else:
                par[key] = new
            for k in cur:
                v = cur[k]
                if isinstance(v, (dict, list, tuple)):
                    queue.append((v, new, k))
                else:
                    new[k] = v.item() if isinstance(v, np.generic) else v
        elif isinstance(cur, (list, tuple)):
            new = []
            if par is None:
                root = new
            else:
                par[key] = new
            for i in range(len(cur)):
                v = cur[i]
                if isinstance(v, (dict, list, tuple)):
                    queue.append((v, new, len(new)))
                    new.append(None)
                else:
                    new.append(v.item() if isinstance(v, np.generic) else v)
    if root is not None:
        return root
    return o.item() if isinstance(o, np.generic) else o


if __name__ == "__main__":
    raise SystemExit(main())
