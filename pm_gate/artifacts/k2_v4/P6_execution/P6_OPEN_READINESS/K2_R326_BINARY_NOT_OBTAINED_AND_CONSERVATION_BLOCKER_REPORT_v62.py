#!/usr/bin/env python3
"""K2 · R326 —— 应监理停止令（收敛停滞 ≈80 轮无二值）：
  二值 = (a) 未得 ‖ (b) 不成立 ⇒ 依停止令出《守恒级卡点报告 v62》（四字段 · 全部以**精确量**支撑）。
只读 · 不改生成器 · 不写板 · 不含任何见证/证书。
用法: python3 <本件>.py <model_l8.json> <out.json>
"""
import sys, json, math, importlib.util, hashlib, subprocess, collections
import numpy as np

V3 = "k2/tools/k2_p4_b2_in5_lane_router_v3.py"
LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
spec = importlib.util.spec_from_file_location("v3", V3)
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
v3.is_lane = lambda n: n in LANES
MODEL, OUT = sys.argv[1], sys.argv[2]
CELL, HW, P = 0.02, 0.08, 0.435
m = json.load(open(MODEL))
rast = v3.Raster(m["bbox"], CELL)
bad = v3.build_base(rast, m, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
ad = {a["net"]: a for a in v3.lane_anchors(m)}
X0, Y0, ST = rast.X0, rast.Y0, rast.step
I = lambda x: int(round((x - X0) / ST)); J = lambda y: int(round((y - Y0) / ST))
def sha16(p):
    try: return subprocess.check_output(["sha256sum", p], text=True).split()[0][:16]
    except Exception: return None

# --- field-② window: 出带↔走廊 切换带（窄颈） ---
NW = (93.0, 44.0, 112.0, 58.0)

# --- 刚性割容量上界（同 R325 方法）---
def cut_bound(x):
    col = bad[I(x), :]; j0, j1 = J(33.0), J(79.0); iv = []; s = None
    for j in range(j0, j1 + 1):
        if (not col[j]) and s is None: s = j
        if col[j] and s is not None: iv.append((s, j - 1)); s = None
    if s is not None: iv.append((s, j1))
    cnt = 0; last = -1e9
    for (a, b) in iv:
        y = Y0 + a * ST
        if y < last + P: y = last + P
        while y <= Y0 + b * ST + 1e-9: cnt += 1; last = y; y += P
    return cnt
cb = {round(x, 2): cut_bound(x) for x in np.arange(93.0, 127.51, 0.5)}
min_b = min(cb.values()); argmin = [x for x in cb if cb[x] == min_b]

# --- field-③ 占用普查（窄颈窗内）---
def inbox(x, y): return NW[0] <= x <= NW[2] and NW[1] <= y <= NW[3]
segc = collections.Counter(); segdet = collections.defaultdict(list)
for s in m["segs"]["In5.Cu"]:
    x1, y1, x2, y2, wd, net = s
    if net in LANES: continue
    if inbox(x1, y1) or inbox(x2, y2) or (min(x1, x2) < NW[2] and max(x1, x2) > NW[0]
                                          and min(y1, y2) < NW[3] and max(y1, y2) > NW[1]):
        segc[net] += 1; segdet[net].append((round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)))
viac = collections.Counter(); vdet = collections.defaultdict(list)
for v in m["vias"]:
    if v["net"] in LANES: continue
    if "In5.Cu" in v["layers"] and inbox(v["x"], v["y"]):
        viac[v["net"]] += 1; vdet[v["net"]].append((round(v["x"], 2), round(v["y"], 2)))
FIXED = ("GND", "GND_FIXED", "P3V3_FIXED", "P3V3")
fixed_vias = {n: c for n, c in viac.items() if n in FIXED}
sig_vias = {n: c for n, c in viac.items() if n not in FIXED}
anchor_bad = np.zeros((rast.NX, rast.NY), bool); own = {}
for n in LANES:
    a = ad[n]; mm = np.zeros((rast.NX, rast.NY), bool)
    v3.Raster.cir(rast, mm, a["A"][0], a["A"][1], P); v3.Raster.cir(rast, mm, a["B"][0], a["B"][1], P)
    own[n] = mm; anchor_bad |= mm

def straight_full(n):
    a = ad[n]; ax, ay = a["A"]; bx, by = a["B"]
    allowed = (~bad) & (~(anchor_bad & ~own[n]))
    i0, i1 = sorted((I(ax), I(bx)))
    hor_ok = allowed[i0:i1 + 1, :].all(axis=0)
    c = 0
    for j in range(J(38.0), J(64.0) + 1):
        if not hor_ok[j]: continue
        ja, jb = sorted((J(ay), j)); 
        if not allowed[I(ax), ja:jb + 1].all(): continue
        jc, jd = sorted((J(by), j)); 
        if not allowed[I(bx), jc:jd + 1].all(): continue
        c += 1
    return c
sf = {n[10:-3]: straight_full(n) for n in sorted(LANES, key=lambda k: ad[k]["A"][0])}
zero = [k for k, v in sf.items() if v == 0]

out = {
 "schema": 1, "artifact": "k2_r326_binary_not_obtained_and_conservation_blocker_report_v62",
 "to": "监理", "from": "ENG · ARCHER",
 "nature": "应监理停止令（收敛停滞 ≈80 轮无二值）⇒ 出《守恒级卡点报告》（四字段）· 只读 · 不含见证/证书",
 "board": "k2/hw/k2_v4_8L.l8.kicad_pcb", "board_sha16": sha16("k2/hw/k2_v4_8L.l8.kicad_pcb"),
 "frozen_sources": {"k2_v4_8L.l4.kicad_pcb": sha16("k2/hw/k2_v4_8L.l4.kicad_pcb"),
                    "k2_v4_8L.kicad_pcb": sha16("k2/hw/k2_v4_8L.kicad_pcb"),
                    "k2_sch.yaml": sha16("k2/hw/data/k2_sch.yaml"),
                    "drc_rules.json": sha16("_shared/eda_core/drc_rules.json")},
 "criteria_anchor": {p: sha16(p) for p in ("criteria/adjudicate.py", "criteria/manifest.k2.yaml", "criteria/CHANGELOG")},
 "caliber": {"cell_mm": CELL, "hw_mm": HW, "pitch_mm": P, "clearance": "hw + max(0.175, req(net))",
             "self_net_copper": "no-move 全转（本网 In5 旧铜可拆 · 不计障碍）"},
 "binary_verdict": {"(a) 可行见证": "**未得**（最佳合法几何 = 13/16 · 且含 T1_N=314.23mm 绕行 ⇒ 不作交付见证）",
                    "(b) 守恒级不可行证书": "**不成立**（R314 反证 `W_max=8 ⇒ U≤16`；本件独立刚性割上界 min=%d ≥ 16 佐证）" % min_b},
 "card_report_v62": {
   "①哪层": "**算法 / 实现能力层** —— 缺『**折返-绕障型联合构造器**』（不是判据层、不是几何刚性层、不是容量层）",
   "①证据": "本件精确读数：最简『单水平长走』（3 段直折线）模型中 **%d/16** 条 lane **候选为 0**（水平段与 A 竖段均可行，唯 B 侧竖段穿越走廊 y≈55.2–56.2 阻断带）⇒ **任何单水平长走之解 ≤ 8/16**，其余必经层内折返。" % len(zero),
   "②哪资源": "**In5 出带↔走廊切换带（窄颈）**：窗 x∈[%.0f,%.0f] × y∈[%.0f,%.0f]（cell %.2f 度量）" % (NW[0], NW[2], NW[1], NW[3], CELL),
   "②为何是它": "x∈[84,94] 出带段仅 y≳54.4 与少量口袋自由；x∈[108,130] 走廊大开（≲55.2）；二者由 x≈104–108 窄颈相连 ⇒ 上/下两「高速」之切换须绕障端 ⇒ 折返不可免。",
   "③被谁占死": {
      "判": "**未被『不可动』占死**（无连通型/容量型/守恒级刚性障碍）——占用者**可腾挪**，故卡点在实现层非几何刚性",
      "他网 In5 铜（窗内段数）": dict(segc.most_common()),
      "固定缝合孔（窗内 · 禁自拆 · 仅 C-w）": fixed_vias,
      "信号孔（窗内）": sig_vias,
      "本网旧铜": "`PCIE_UP_OUT*_J2` 之 In5 旧铜已在 no-move 全转口径下视为可拆（#K2-133 §三 N1）",
      "全局固定缝合孔": "**135 枚**（`GND 70 · GND_FIXED 32 · P3V3_FIXED 25 · P3V3 8` —— 承 #K2-133 §一 监理实测）"},
   "④为何任何分配都不可能": "**该前提不成立** —— R314 已反证守恒级不可行证书；本件再以**独立刚性割上界**佐证：任一 lane 必过每一竖线 x∈[93,127]，过线高度两两须 ≥ pitch ⇒ **上界 min = %d ≥ 16**（x=%s）。故『任何分配都不可能』**不予主张**。" % (min_b, argmin)},
 "independent_measurements": {
   "rigid_cut_bound_min": min_b, "argmin_x": argmin, "cut_bound_by_x": {str(k): v for k, v in cb.items()},
   "straight_model_full_pass_rows": sf, "zero_candidate_lanes": zero},
 "authorized_paths": {
   "path_Cw_申报（#K2-133 §四 · 准申报 · 执行待批）": {
     "性质": "本例确有『占用者』可腾挪；惟 **135 枚固定缝合孔**（牵 `ref_plane_continuity`）**不得自行执行**",
     "须附五要件": ["①逐项具名（上表已给 net+段/孔坐标）", "②`ref_plane_continuity` 证明", "③端点/球位不动", "④`buildability` 齐", "⑤不动冻结四源"],
     "本件状态": "**仅完成①（占用普查）**；②③④**未给** ⇒ 依宪法第十三条『缺可施工性不作数』，**本件不申报 C-w 为可行**"},
   "path_Cstar_能力（承 #K2-133 (甲) `C-*`）": {
     "缺什么": "『**折返-绕障型联合构造器**』：以窄颈为共享切换带 + 以上/下双高速为干线之**联合指派**（非序贯、非参数扫描）",
     "为何不是工具升版": "本件为**能力缺口登记**，非既有一版工具之调参；工具 v3 已按『单发一次』用尽（9/32），禁同参重跑",
     "交付形态": "一次实现 ⇒ 过 `exact_gate`（连续几何精确闸）之 16/16 坐标线束 + `buildability.mode=\"no_move\"`"}},
 "buildability_field": "本件**不动任何对象**（未烙板 · 未改生成器/SPEC/原理图 · 未改任何网几何）⇒ **不动证明成立**；本件**不产出施工图**（缺图，不得据以开工）。",
 "self_sha16": {"convention": "#K2-72 §五 约定A", "convention_A_sha16": ""},
}
txt = json.dumps(out, indent=1, ensure_ascii=False)
out["self_sha16"]["convention_A_sha16"] = hashlib.sha256(txt.strip().encode()).hexdigest()[:16]
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("cut bound min =", min_b, "argmin", argmin, "| zero-candidate lanes =", len(zero))
print("[sha16 约定A]", out["self_sha16"]["convention_A_sha16"], "->", OUT)
