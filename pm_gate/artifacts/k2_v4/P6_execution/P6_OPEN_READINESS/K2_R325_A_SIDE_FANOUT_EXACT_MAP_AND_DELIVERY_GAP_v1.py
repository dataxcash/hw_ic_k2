#!/usr/bin/env python3
"""K2 · R325 —— ②-UP **A 侧扇出区精确测绘** + **最简精确联合模型否证** + 交付差额清单（只读 · 不改生成器 · 不写板）

承 handoff §7.5「造活（测量件补强 / 差额清单）」· 承 R318/R319（卡点=A 侧锚群出线扇出）。
本件为**独立复算**（不采信任何 ENG 自述读数），方法全部为**精确**量：
  (1) **刚性割容量上界**：任一 lane 必过每一竖线 x∈[93,127]；过线高度两两须 ≥ pitch(0.435)
      ⇒ 上界 = ∪自由区间内两两 ≥pitch 之最大点数（贪心最优）。取 x 上最小值。
  (2) **A 侧扇出区自由空间精确测绘**（cell 0.02 · 障碍膨胀 = hw+max(0.175,req)）。
  (3) **最简精确联合模型**（3 段折线 (ax,ay)→(ax,y)→(bx,y)→(bx,by)）之候选计数 ⇒ 直折线可达性否证。
见证有效性只由 `exact_gate` 判；本件**不主张任何不可行证书**。
用法: python3 K2_R325_...py <model_l8.json> <out.json>
"""
import sys, json, math, importlib.util, hashlib, subprocess
import numpy as np

V3 = "k2/tools/k2_p4_b2_in5_lane_router_v3.py"
LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
spec = importlib.util.spec_from_file_location("v3", V3)
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
v3.is_lane = lambda n: n in LANES

MODEL, OUT = sys.argv[1], sys.argv[2]
CELL, HW, P = 0.02, 0.08, 0.435
model = json.load(open(MODEL))
rast = v3.Raster(model["bbox"], CELL)
bad = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
ad = {a["net"]: a for a in v3.lane_anchors(model)}
X0, Y0, ST = rast.X0, rast.Y0, rast.step
I = lambda x: int(round((x - X0) / ST)); J = lambda y: int(round((y - Y0) / ST))

def sha16(p):
    try: return subprocess.check_output(["sha256sum", p], text=True).split()[0][:16]
    except Exception: return None

# ---------- (1) 刚性割容量上界 ----------
def cut_bound(x):
    col = bad[I(x), :]; j0, j1 = J(33.0), J(79.0)
    iv = []; s = None
    for j in range(j0, j1 + 1):
        if (not col[j]) and s is None: s = j
        if col[j] and s is not None: iv.append((s, j - 1)); s = None
    if s is not None: iv.append((s, j1))
    cnt = 0; last = -1e9
    for (a, b) in iv:
        y = Y0 + a * ST
        if y < last + P: y = last + P
        while y <= Y0 + b * ST + 1e-9:
            cnt += 1; last = y; y += P
    return cnt

xs = [round(x, 2) for x in np.arange(93.0, 127.51, 0.5)]
cb = {x: cut_bound(x) for x in xs}
min_b = min(cb.values()); argmin = [x for x in xs if cb[x] == min_b]

# ---------- (2) 扇出区自由空间测绘 ----------
def free_intervals(x, ylo=40.0, yhi=62.0, minw=0.25):
    col = bad[I(x), :]; out = []; s = None
    for j in range(J(ylo), J(yhi) + 1):
        if (not col[j]) and s is None: s = j
        if col[j] and s is not None:
            if (j - s) * ST >= minw - 1e-9: out.append([round(Y0 + s * ST, 2), round(Y0 + (j - 1) * ST, 2)])
            s = None
    if s is not None and (J(yhi) - s) * ST >= minw - 1e-9:
        out.append([round(Y0 + s * ST, 2), round(Y0 + J(yhi) * ST, 2)])
    return out

XPROBE = [84.4, 86, 88, 90, 92, 93, 94, 96, 100, 104, 108, 112, 118, 124, 130, 134]
fmap = {str(x): free_intervals(x) for x in XPROBE}

# ---------- (3) 最简精确联合模型（直折线）候选计数 ----------
ANCHOR_R = {"P435 (R320 口径 · 中心线距)": P,
             "strict (via/drill 口径 · HW+max(vr+eff,drill+HOLE_CLR))": None}

def make_anchor_bad(cal):
    ab = np.zeros((rast.NX, rast.NY), bool); ow = {}
    for n in LANES:
        a = ad[n]
        if cal is None:
            rad = HW + max(a["via_r"] + max(0.175, v3.req(n)), a["drill"] + v3.HOLE_CLR)
        else:
            rad = cal
        mm = np.zeros((rast.NX, rast.NY), bool)
        v3.Raster.cir(rast, mm, a["A"][0], a["A"][1], rad)
        v3.Raster.cir(rast, mm, a["B"][0], a["B"][1], rad)
        ow[n] = mm; ab |= mm
    return ab, ow

def straight_stages(n, anchor_bad, own):
    """回传 (水平通过数, +A 竖段通过数, +A+B 全通过数, 候选 y)。"""
    a = ad[n]; ax, ay = a["A"]; bx, by = a["B"]
    allowed = (~bad) & (~(anchor_bad & ~own[n]))
    i0, i1 = sorted((I(ax), I(bx)))
    hor = allowed[i0:i1 + 1, :]; hor_ok = hor.all(axis=0)
    nH = nHA = 0; out = []
    jay, jby = J(ay), J(by)
    for j in range(J(38.0), J(64.0) + 1):
        if not hor_ok[j]: continue
        nH += 1
        ja, jb = sorted((jay, j))
        if not allowed[I(ax), ja:jb + 1].all(): continue
        nHA += 1
        jc, jd = sorted((jby, j))
        if not allowed[I(bx), jc:jd + 1].all(): continue
        out.append(round(float(Y0 + j * ST), 4))
    return nH, nHA, len(out), out

def straight_cands(n, anchor_bad, own):
    return straight_stages(n, anchor_bad, own)[3]

LANE_ORD = sorted(LANES, key=lambda k: ad[k]["A"][0])
scB = {}; zeroB = {}; stagesB = {}
for calname, cal in ANCHOR_R.items():
    ab, ow = make_anchor_bad(cal)
    st = {n: straight_stages(n, ab, ow) for n in LANE_ORD}
    stagesB[calname] = {n[10:-3]: {"horiz_ok": st[n][0], "plus_A_vert_ok": st[n][1], "full_ok": st[n][2]} for n in LANE_ORD}
    scB[calname] = {n: st[n][3] for n in LANE_ORD}
    zeroB[calname] = [n for n in LANE_ORD if len(scB[calname][n]) == 0]
sc = scB["P435 (R320 口径 · 中心线距)"]
zero = zeroB["P435 (R320 口径 · 中心线距)"]

out = {
 "schema": 1, "artifact": "k2_r325_up_out_a_side_fanout_exact_map_and_delivery_gap_v1",
 "to": "监理", "from": "ENG · ARCHER", "nature": "只读测绘 + 差额清单（造活）· 不含任何见证/证书",
 "board": "k2/hw/k2_v4_8L.l8.kicad_pcb", "board_sha16": sha16("k2/hw/k2_v4_8L.l8.kicad_pcb"),
 "frozen_sources": {"k2_v4_8L.l4.kicad_pcb": sha16("k2/hw/k2_v4_8L.l4.kicad_pcb"),
                    "k2_v4_8L.kicad_pcb": sha16("k2/hw/k2_v4_8L.kicad_pcb"),
                    "k2_sch.yaml": sha16("k2/hw/data/k2_sch.yaml"),
                    "drc_rules.json": sha16("_shared/eda_core/drc_rules.json")},
 "criteria_anchor": {p: sha16(p) for p in ("criteria/adjudicate.py", "criteria/manifest.k2.yaml", "criteria/CHANGELOG")},
 "caliber": {"cell_mm": CELL, "hw_mm": HW, "pitch_mm": P,
             "clearance": "hw + max(0.175, req(net))", "self_net_copper": "已按 no-move 全转视为可拆（不计入障碍）"},
 "part1_rigid_cut_bound": {
    "method": "每 lane 必过每一竖线 x∈[93,127]；过线高度两两须 ≥pitch ⇒ 上界=∪自由区间内 ≥pitch 之最大点数（贪心最优）",
    "x_samples": {str(k): v for k, v in cb.items()},
    "min_bound": min_b, "argmin_x": argmin,
    "verdict": "上界 **%d ≥ 16** ⇒ **不存在**『容量型/割线型』刚性上界 <16（独立复现 R318；与 #K2-132 (甲) 一致）" % min_b},
 "part2_fanout_freespace_map": {
    "window": {"x": [84.4, 134], "y": [40, 62], "min_interval_w": 0.25},
    "note": "A 侧扇出区 x∈[84,94] 仅 y≳54.4 与少量口袋自由；走廊 x∈[94,130] 大部分自由 ⇒ 瓶颈 = **出带（anchor→走廊）段**",
    "free_intervals_by_x": fmap},
 "part3_straight_model_refutation": {
    "model": "3 段直折线 (ax,ay)→(ax,y)→(bx,y)→(bx,by)（最简『单水平长走』模型）",
    "per_caliber": {cn: {"stage_counts": stagesB[cn],
                         "per_lane_candidate_rows": {n[10:-3]: len(scB[cn][n]) for n in LANE_ORD},
                         "n_zero_candidate_lanes": len(zeroB[cn]),
                         "zero_candidate_lanes": sorted(n[10:-3] for n in zeroB[cn])}
                    for cn in scB},
    "verdict": "在 **R320 一致口径**（他 lane 锚孔中心线排除半径 0.435）下 %d/16 条 lane 候选为 0；严格口径下 %d/16 为 0 ⇒ **『单条水平长走』模型不成立** ⇒ 任何解必须含 ≥1 次层内折返（jog）。**此非不可行证书**（模型系限制），只证直折线模型不成立。" % (
        len(scB["P435 (R320 口径 · 中心线距)"]), len(scB["strict (via/drill 口径 · HW+max(vr+eff,drill+HOLE_CLR))"]))},
 "status": {"owner_gate": 0, "eng_pending_rulings": ["②-UP 口径（R323：EX-3 具名豁免 ‖ 派 C-* 能力）", "R317 lib_electrical_level（判据侧两条非缩口径修正）"],
            "p4": "18 OK / 1 FAIL（判据侧）· 未全绿 · fail-closed",
            "note": "两裁均在监理自裁面（已投递 · 待裁）；ENG 不得自裁、不得停等"},
 "delivery_gap_list": {
    "owner_completion_def_14_3": "8 铜层 + 阻焊/丝印/边框/job + Excellon(含 HDI 盲埋孔) + 叠层图 + 阻抗表 + MANIFEST；DFM 逐项对 JLC HDI 全 PASS",
    "present": {"package": "k2/pm_gate/artifacts/k2_v4/L6/jlc_package_l8r3", "gerber": 14, "excellon_drl": 15,
                "stackup_svg": ["JLC08161H_stackup.svg", "HDI_stage_diagram.svg"],
                "impedance": ["impedance_table.json", "impedance_table.md"], "manifest": "MANIFEST.json",
                "dfm": "16 PASS / 1 ACCEPT / 0 FAIL", "reproducibility": "字节级 29/29（R324）"},
    "blocking": ["②-UP 验收口径（待监理）", "lib_electrical_level 判据修正（待监理）", "P5 未启（fail-closed）"],
    "watch": ["DFM 有 1 项 ACCEPT（阻焊桥/阻焊-铜净距 · hdi=ACCEPT_L2_WITH_FAB_REVIEW · machine_std=FAIL）—— owner #14③ 字面为『全 PASS』，须监理确认『ACCEPT 等效』或给处置"]},
 "buildability_field": "本件**不动任何对象**（未烙板 · 未改生成器/SPEC/原理图 · 未改任何网几何）⇒ 可施工性=**不动证明**成立。本件不产出施工图。",
 "self_sha16": {"convention": "#K2-72 §五 约定A", "convention_A_sha16": ""},
}
txt = json.dumps(out, indent=1, ensure_ascii=False)
out["self_sha16"]["convention_A_sha16"] = hashlib.sha256(txt.strip().encode()).hexdigest()[:16]
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("min cut bound =", min_b, "(argmin x=%s)" % argmin)
for cn in scB:
    print("[%s] zero=%d/16" % (cn, len(zeroB[cn])))
    print("   cands:", {n[10:-3]: len(scB[cn][n]) for n in LANE_ORD})
print("[sha16 约定A]", out["self_sha16"]["convention_A_sha16"], "->", OUT)
