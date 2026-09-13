#!/usr/bin/env python3
"""CO-10 只读探针：CO-09 安全 hop 拓扑 + D2/D3 全 pad 障碍场的**顺序单遍**落位复算。

用途：在**不改冻结四源、不改 canonical 图纸**的前提下，独立复算
  (1) CO-09 §3 安全 hop 层角色（escape=In2/B、lane=In6、stub=In2/In6）能否一次求解；
  (2) CO-09 §4ter D3 落列规则（lx=conn pad x、ll=行间中缝）在西侧是否可行；
  (3) 剩余不可落位页的精确归因（via-via / via-track / track-track / pad 冲突）。
零搜索：候选来自冻结 F-13 pair 域 + 冻结 verdict；单遍确定性 argmin；无回溯。
CLI: --rule {d3,fan,co10}  --order {engine,fewest,laneidx}  --out PATH  --verbose
env（只读旋钮，CO-11 实测用；默认=原行为）:
  CO10_PAIR=<file>      pair 域文件名（默认 v1_4；CO-11 用 v1_5=pad 场合法域）
  CO10_STEP=<mm>        全局 lane STEP
  CO10_WDELTA=<mm>      仅西侧 lane 块整体下移
  CO10_WSTEP/CO10_WLO   仅西侧 lane 块重派生（lane_y=WLO+idx*WSTEP）
  CO10_FANDX_J3/_J4=<mm> 西侧 connector landing lx 偏置
  CO10_POLMODE=lx     方向感知 P/N lane 排序（CO-15；西侧 32/32 所必需）
  CO10_LXPRIO=landlen  CO-36：connector 落列器按 land 段长度升序处理（短段优先自然列）
                      —— D3b 收官（消 6 条 land 铜距违规）；默认 "" = 旧行为
  CO10_EASTSPLIT=1    实验性（CO-16 open）：东侧 up stub→In6；**当前会使 up In6 stub 与 In6 lane
                      跨页真交叉**（复核 FAIL）⇒ 未采用；仅用于记录东侧重派生方向，勿用于 sign-off。
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
import importlib.util
import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
_s = importlib.util.spec_from_file_location("w3", str(K2 / "tools/p3_v57_w3_constructive.py"))
W = importlib.util.module_from_spec(_s); _s.loader.exec_module(W)

J = {k: json.load(v.open()) for k, v in W.F.items() if v.suffix == ".json"}
FACTS = W.page_facts(J["manifest"], J["lane_frame"])
FRS = W.frames_of(FACTS)
W.STEP = float(__import__("os").environ.get("CO10_STEP", W.STEP))
LANES = W.r2_lanes(FRS, FACTS)
_WD = float(__import__("os").environ.get("CO10_WDELTA", "0"))
if _WD:
    for _p, _v in LANES.items():
        if FACTS[_p]["corridor"] == "WEST_MCIO_TO_CHIP":
            _v["lane_y"] = W.fp(_v["lane_y"] - _WD)
if __import__("os").environ.get("CO10_WORDER") == "upfirst":
    _west = sorted([p for p in LANES if FACTS[p]["corridor"] == "WEST_MCIO_TO_CHIP"],
                   key=lambda p: (FACTS[p]["band"] == "dn", LANES[p]["lane_index"]))
    for _r, _p in enumerate(_west):
        LANES[_p]["lane_y"] = W.fp(33.3 + _r * 1.46)
_WB = __import__("os").environ.get("CO10_WBLOCK", "")
if _WB:
    _lo1, _st1, _n1, _lo2, _st2, _n2 = (float(v) for v in _WB.split(","))
    for _p, _v in LANES.items():
        if FACTS[_p]["corridor"] == "WEST_MCIO_TO_CHIP":
            _k = _v["lane_index"]
            _v["lane_y"] = W.fp(_lo1 + _k * _st1) if _k < _n1 else W.fp(_lo2 + (_k - _n1) * _st2)
_WS = float(__import__("os").environ.get("CO10_WSTEP", "0"))
_WL = float(__import__("os").environ.get("CO10_WLO", "33.3"))
if _WS:
    for _p, _v in LANES.items():
        if FACTS[_p]["corridor"] == "WEST_MCIO_TO_CHIP":
            _v["lane_y"] = W.fp(_WL + _v["lane_index"] * _WS)
_ED = float(__import__("os").environ.get("CO10_EDELTA", "0"))
if _ED:
    for _p, _v in LANES.items():
        if FACTS[_p]["corridor"] == "EAST_CHIP_TO_J2":
            _v["lane_y"] = W.fp(_v["lane_y"] - _ED)
PADF = json.loads((SPEC / "m13_v57_co09_pad_field.json").read_text())
PAIR_ART = __import__("os").environ.get("CO10_PAIR", "m13_v57_f13_r1_pair_coupling_v1_4.json")
PAIR_DOMAIN = json.loads((SPEC / PAIR_ART).read_text())["pages"]

VIA_R, CLEAR, ESC, WID = 0.175, 0.175, 0.075, 0.205
YWIN = 0.7           # via1 只允许落在 pad_y ± 0.7 内（保 up/dn band 隔离）
_HOLE_GAP = float(__import__("os").environ.get("CO10_HOLE_GAP", "0"))   # 同网钻孔间距下限（0=关）
TT = WID + CLEAR; TT_E = WID + ESC
VT = VIA_R + CLEAR + WID / 2; VT_E = VIA_R + ESC + WID / 2
VV = 2 * VIA_R + CLEAR; TOL = 1e-9

# CO-143（L2 自裁）：逃生扇「对间 3W」并入（SPEC net_classes.PCIe85.inter_pair_derivation_v1：
#   对间中心距 >= 3*w(layer) ⇔ 对间铜边 >= 2*w）。命中域 = 同层、**异页（异对）**、双方均**非 pad-access**
#   （逃生竖列 / lane / stub 等路由骨干）且夹角 <= 10°（SPEC「长平行」口径）。pad-access（F.Cu
#   pad->via1 / landing->conn）不计 3W：那是接口固有节距（J2 0.6 < 3w，L1，路由不可消除；ECN-001 逃逸域口径）。
#   默认 "" = 旧行为（ALLOC.1..7 逐字节可复现）。
_IP3W = __import__("os").environ.get("CO10_IP3W", "") not in ("", "0")
_PAR_SIN = math.sin(math.radians(10.0))
_WBY = json.loads(W.F["spec"].read_text(encoding="utf-8"))["impedance"]["width_mm_by_layer"]

# CO-143b（L2 自裁）：把 SPEC 已声明的 **PDN 铜**（`pd.zone_defs` 的 zone vias / power_pad_connect
#   entries / 未 blocked 的 gnd_stitch via 与 ppc F.Cu 短段）作为**固定障碍**喂入落位判据。
#   背景：PDN 决策（rev-18 / CO-133）晚于本扇几何（ALLOC.5），扇此前对 PDN via 视而不见；
#   CO-143 的三排并入 3W 使 UP0 N 西移 0.30 撞上 GND stitch via（DRC clearance 0.1587<0.175）。
#   默认 "" = 旧行为（ALLOC.1..7 可复现）。
_PDN_OBS = __import__("os").environ.get("CO10_PDN_OBS", "") not in ("", "0")
PDN_LABEL = "__PDN__"

# CO-144（L2 自裁 · 逃生扇落位策略重派生）：**分带单调 carry**（opt-in）。
#   背景（CO-143）：单遍贪心 + 按 pad 邻近选列在「对间 3W + PDN 障碍」下 31/32（rev）或 30/32（xasc），
#   但分带 DP 机判两带均有合法单调解 ⇒ 缺陷在**落位策略**而非几何不可行。
#   本策略：按 (corridor, band) 分带、带内按 pad-x 升序处理；维护**带内游标** cur = 已落位列 x 的最大值；
#   候选行须满足 min(px,nx) >= cur + 3*w(escape layer)，并**按 max(px,nx) 升序**取首可行
#   ⇒ 西→东单调 carry（零回溯，确定性）。游标下界 >= 3W ⇒ 带内**任意两页**的对应竖列间距 >= 3W。
#   默认 "" = 旧行为（ALLOC.1..7 逐字节可复现）。
_STRAT = __import__("os").environ.get("CO10_FAN_STRAT", "")
_CARRY = _STRAT == "carry"
_CARRY_CUR = {}
_CARRY_DIR = {}
# 命中域（依据 co141/co142 实测）：只有**外层逃逸带**（3W 界 = 0.615）需要 carry；
# 内层 In2/In5（3W 界 = 0.48）实测对间 0 违规且 carry 会扰动跨带 via 净距 ⇒ 保持 canonical 单遍。
_CARRY_W3_MIN = 0.615 - 1e-9


def _band_key(f):
    return (f["corridor"], f["band"])


def _band_carry(f):
    """该带是否启用 carry：escape 层 3W 界 >= 0.615（外层 F/B）；CARRYALL 时全带启用。"""
    if _CARRYALL:
        return True
    return 3.0 * _WBY.get(esc_layer(f), 0.0) >= _CARRY_W3_MIN


def _pdn_obstacles():
    """SPEC pd.zone_defs -> (vias, segs)，坐标逐字取自 SPEC（与 co133 spec_expectation 同源同式）。"""
    spec = json.loads(W.F["spec"].read_text(encoding="utf-8"))
    zd = spec["pd"]["zone_defs"]
    vias = []
    for z in zd.get("power_zones", []):
        for v in z.get("vias", []):
            pos = v["pos"]; seq = pos if (pos and isinstance(pos[0], list)) else [pos]
            for x, y in seq:
                vias.append((float(x), float(y)))
    for v in zd.get("decoupling_via_to_plane", {}).get("vias", []):
        vias.append((float(v["pos"][0]), float(v["pos"][1])))
    for c in zd.get("gnd_stitch_via", {}).get("coordinates", []):
        if c.get("blocked") or c.get("status") == "blocked":
            continue
        vias.append((float(c["x"]), float(c["y"])))
    for e in zd["power_pad_connect"]["entries"]:
        vias.append((float(e["via_pos"][0]), float(e["via_pos"][1])))
    stub_w = float(zd["power_pad_connect"].get("stub_width_mm", 0.5))
    segs = []
    for e in zd["power_pad_connect"]["entries"]:
        a = (float(e["pad_pos"][0]), float(e["pad_pos"][1]))
        b = (float(e["via_pos"][0]), float(e["via_pos"][1]))
        segs.append(("F.Cu", a[0], a[1], b[0], b[1], False, "X", stub_w))
    return vias, segs


def _seed_pdn(st):
    """把 PDN 障碍写入 Store（via 全层 mask；F.Cu 短段）。"""
    import numpy as _np
    vias, segs = _pdn_obstacles()
    allmask = 0
    for l in LAYERS:
        allmask |= 1 << LI[l]
    for (x, y) in vias:
        st.vlab.append(PDN_LABEL)
        st.vx = _np.append(st.vx, x); st.vy = _np.append(st.vy, y); st.vm = _np.append(st.vm, allmask)
    for (lay, x1, y1, x2, y2, pa, pol, wid) in segs:
        st.S[lay] = _np.vstack([st.S[lay], [x1, y1, x2, y2]])
        st.SP[lay] = _np.append(st.SP[lay], False)
        st.SLAB[lay].append(PDN_LABEL)
    return {"n_pdn_vias": len(vias), "n_pdn_segs": len(segs)}
# CO-205（候选 B）：LAYERS 增列 In5.Cu（第二竖段层；对 default 路径同构 —— 空层，不产生任何命中）。
LAYERS = ["B.Cu", "In2.Cu", "In5.Cu", "In6.Cu", "F.Cu"]; LI = {l: i for i, l in enumerate(LAYERS)}

_p = PADF["pads"]
PXA = np.array([q["x"] for q in _p]); PYA = np.array([q["y"] for q in _p])
PHX = np.array([q["sx"] / 2 for q in _p]); PHY = np.array([q["sy"] / 2 for q in _p])
PRA = np.array([max(q["sx"], q["sy"]) / 2 for q in _p])
PCIRC = np.array([q["shape"] == 0 for q in _p]); PKEY = [(q["ref"], q["pad"]) for q in _p]

ESC_MAP = {("EAST_CHIP_TO_J2", "dn"): "In2.Cu", ("EAST_CHIP_TO_J2", "up"): "B.Cu",
           ("WEST_MCIO_TO_CHIP", "up"): "In2.Cu", ("WEST_MCIO_TO_CHIP", "dn"): "B.Cu"}
GAP = {"J3": 44.5, "J4": 62.7}
J2L, J2R, J2_IN, J2_OUT, J2P = 131.65, 136.0, 132.65, 135.0, 0.525


# CO-205n（L2 自裁 · 联合求解）：对内 lane y 偏移可调（默认 0.25 = 旧行为，保 ALLOC.1..9/rev-19 逐字节）。
#   判据：P/N 同 y 侧结构（桥孔/落孔）互距 = 2*POL_OFF ⇒ 需 >= VV(0.525) ⇒ POL_OFF >= 0.2625。
POL_OFF = float(__import__("os").environ.get("CO10_POL_OFF", "0.25"))
# CO-15 只读旋钮（默认 "" = 原行为）：POLMODE="lx" ⇒ 方向感知 P/N lane 排序。
# 目的：当 stub 层 == lane 层（In6）时，竖直 stub 必穿过对面极性水平 lane（CO-11 §13.2 UP6/UP7 自叉）。
# 规则（闭式，由几何推导）：stub 朝上（ll>lane_y）⇒ landing lx 较大者取上层 lane（+POL_OFF）、较小者取下（-POL_OFF）；
# 朝下（ll<lane_y）反之。仅对 WEST_MCIO_TO_CHIP 生效（stub 全 In2 时该规则不影响可行性，保留一致性）。
POLMODE = __import__("os").environ.get("CO10_POLMODE", "")
# CO-16 只读旋钮（默认关）：东侧逐带 stub 层分流 + per-page rank J2 落列（O4 闭合所需）。
#   CO10_EASTSPLIT=1 ⇒ J2 up stub→In6 / dn stub→In2（跨带列可复用）
#   !! 实验性：up In6 stub 会与 In6 lane 跨页真交叉（32/32 落位但复核 FAIL 56）⇒ 未采用。
#   CO10_J2STEP=<mm> ⇒ J2 落列步长（默认 0.525 原口径）；CO-16 用 0.55（≥VV 0.525 + 余量）
_ES = __import__("os").environ.get("CO10_EASTSPLIT", "")
EASTSPLIT = _ES if _ES not in ("", "0") else ""
J2STEP = float(__import__("os").environ.get("CO10_J2STEP", "0.525"))
# CO-22：J2 列区间图口径。默认 "" = 原口径（区间用 lane_y 基值）。
#   CO10_COLMODE=pol ⇒ 区间用**该 pad 实际极性 via y**（lane_y + pol_off），消除 P/N 偏移 0.25 造成的
#   同色列 landing/corner via 漏判（vv_placed，如 DN5_P ×  UP2_P 同列 0.2895）。
_COLMODE = __import__("os").environ.get("CO10_COLMODE", "")


def pol_off(f, pol):
    if POLMODE == "lx" and f["corridor"] == "WEST_MCIO_TO_CHIP":
        ll = FAN_Y[row_group(f)]
        ly = LANES[f["page_id"]]["lane_y"]
        big = "P" if f["conn_pad"]["P"][0] > f["conn_pad"]["N"][0] else "N"
        if ll > ly:
            return POL_OFF if pol == big else -POL_OFF
        return -POL_OFF if pol == big else POL_OFF
    if EASTSPLIT and POLMODE == "lx" and f["corridor"] == "EAST_CHIP_TO_J2":
        # 东侧 lane x-span = [vx, lx]（lx>vx）⇒ 跨 lane 的 stub 是 **lx 较小**者；其须在 stub 方向外侧。
        # 东侧 stub 朝下（ll<lane_y，conn pad 在 lane 之下）⇒ 小 lx 极性须在**下**层 lane。
        ll = f["conn_pad"][pol][1]           # landing y ≈ conn pad y（符号口径正确）
        ly = LANES[f["page_id"]]["lane_y"]
        big = "P" if f["conn_pad"]["P"][0] > f["conn_pad"]["N"][0] else "N"
        if ll > ly:
            return -POL_OFF if pol == big else POL_OFF
        return POL_OFF if pol == big else -POL_OFF
    d = f["pad"]["N"][1] - f["pad"]["P"][1]
    base = -POL_OFF if d > 0 else POL_OFF
    return base if pol == "P" else -base


_EFL = __import__("os").environ.get("CO10_EFLIP", "") not in ("", "0")
# CO-204（L2 自裁 · 监理指令 #12）：竖段层**全落 B.Cu**（候选 A′）。run 层不变（仍 In5）⇒ 阻抗/几何不变；
# 每线 via = F↔B(通孔) + B↔In5(背钻) ⇒ 全类外层锚定、残桩 0、0 盲埋孔。
_ALLB = __import__("os").environ.get("CO10_ALLB", "") not in ("", "0")
# CO-205（L2 自裁 · 候选 A）：竖段层（escape/stub）**全落 In2**（run 层由构造器改 B.Cu）。
#   与 CO10_ALLB（竖段全落 B）互斥语义；默认关 => ALLOC.1..9 逐字节可复现。
_ALLI2 = __import__("os").environ.get("CO10_ALLI2", "") not in ("", "0")
# CO-205（L2 自裁 · 候选 B）：run/lane **由 In5 改 B.Cu**、竖段 **In2/In5 分色**。
#   探针侧同构：lane = 私有层 _LANE_V2（对应真板 B.Cu），竖段 = {In2, In5}。
#   映射：v9 之「竖段 B.Cu」一律改 In5.Cu（B 让给 run）。默认关 => ALLOC.1..9 逐字节可复现。
_V2B = __import__("os").environ.get("CO10_V2B", "") not in ("", "0")
_LANE_V2 = __import__("os").environ.get("CO10_LANE_V2", "In6.Cu")   # 探针私有 lane 层（真板 = B.Cu）
_V2 = "In5.Cu"                                                       # 第二竖段层（真板 = In5.Cu）
# CO-205b（L2 自裁 · 工具缺陷修复）：过孔占用 = **起止层之间的全部层**（通孔+背钻的物理事实），
#   而非仅两端点层。原模型只取端点层 ⇒ 系统性低估冲突（co204 候选 B 实测被 KiCad DRC 抓出 7 short）。
#   默认关 => 现行模型/ALLOC.1..9 逐字节可复现；置 1 启用面跨层模型。
_SPAN = __import__("os").environ.get("CO10_SPAN", "") not in ("", "0")
_SPAN_ORDER = ["F.Cu", "In2.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
_SI = {l: i for i, l in enumerate(_SPAN_ORDER)}
# CO-205c（L2 自裁 · 候选 D）：**竖段落两外层**（up->F.Cu / dn->B.Cu）、lane 维持内层 In5.Cu。
#   由 CO-205 结构引理：仅此拓扑同时满足「span 不互砸」（straddle lane）与「corner 外层锚定」。
_VOUT = __import__("os").environ.get("CO10_VOUT", "") not in ("", "0")
# CO-205d：外层竖段**指派**（穷举结构空间用；不落交付）。格式 "eUp,eDn,sUp,sDn"，各 ∈ {F,B}。
_VA = [t.strip().upper() for t in __import__("os").environ.get(
    "CO10_VASSIGN", "F,B,F,B").split(",")]
if len(_VA) != 4:
    _VA = ["F", "B", "F", "B"]

# CO-205e（L2 自裁 · 候选 C）：双孔桥 —— 内层<->内层 corner/drop 改 In2->[In2<->B]->短B段->[B<->In5]->lane。
#   桥之 B 段 <1mm ⇒ 不入「长平行 3W」命中域 ⇒ 绕开外层竖段容量墙（A′/D 之死因）。
_BRIDGE = __import__("os").environ.get("CO10_BRIDGE", "") not in ("", "0")
_BR_JOG = float(__import__("os").environ.get("CO10_BRJOG", "0.5"))
_BR_FLIP = __import__("os").environ.get("CO10_BRFLIP", "") not in ("", "0")
# CO-205k：桥孔「**离对偶**」闭式规则（P 与 N 各自朝远离对方的方向 jog）——加宽本页 P/N 桥孔间距。
_BR_AWAY = __import__("os").environ.get("CO10_BRAWAY", "") not in ("", "0")
# CO-205f：**全部 stub 落 lane 层（In5）** ⇒ 无 drop 孔（消除 56 处内层<->内层），仅余 32 处 corner 待桥。
_STUB_LANE = __import__("os").environ.get("CO10_STUB_LANE", "") not in ("", "0")
# CO-205g：**全部 stub 落 B.Cu**（外层）⇒ drop = In5<->B（外层锚定，**不加孔**）⇒ 消 56 处内层<->内层；
#   代价 = 落列吃外层 3W=0.615。仅余 32 处 corner 待桥（孔数最少解）。
_STUB_B = __import__("os").environ.get("CO10_STUB_B", "") not in ("", "0")
# CO-205h：桥的**第二孔外移**（沿 lane/stub 按比例）——避开 chip 侧扇面局部孔拥塞。
_BRX2 = float(__import__("os").environ.get("CO10_BRX2", "0"))
# CO-205i（L2 自裁 · 拓扑 E，无桥）：**每带自持 straddle** ——
#   In2 逃逸带：escape=In2, lane=F.Cu,  stub=In2  ⇒ 全 4 孔 F<->In2（span 仅 F..In2）
#   B   逃逸带：escape=B,   lane=In5.Cu, stub=B   ⇒ 全 4 孔外层锚定（span 仅 In5..B）
#   两带 span 互不覆盖对方轨道层 ⇒ 无桥、无内层<->内层、无 3W 外层竖段代价。
_TOPOE = __import__("os").environ.get("CO10_TOPOE", "") not in ("", "0")
# 竖列分色偏移（L2 走廊/竖列分配）：up 带目标 x += BOFF，dn 带 -= BOFF（> VT 0.4525/2 两侧合计）
_BOFF = float(__import__("os").environ.get("CO10_BOFF", "0"))
# CO-205n（L2 自裁 · 联合求解）：**逐页逐极性的桥孔几何覆盖**（仅探查用；默认 {} = 关闭 ⇒ 逐字节可复现）。
#   语义：{page_id: {"cx": {"P":dx,"N":dx}, "sy": {"P":dy,"N":dy}}}
#   cx: E==In2 时角桥第二孔 x = vx + dx（dx 可负，>0 表示朝 lane 方向）；缺省回退 _jd*_BR_JOG。
#   sy: S==In2 时落桥第二孔 y = ly + dy；缺省回退 ly+_BR_JOG。
_BRMAP = json.loads(__import__("os").environ.get("CO10_BRMAP") or "{}")
# CO-205o（L2 自裁 · 联合求解 · 候选 B）：**逐页竖段层覆盖**（esc/stub 着色自由度）。
#   语义 {page_id: {"esc": "In2.Cu"|"In5.Cu"|"B.Cu", "stub": 同}}（"B.Cu" 在 _V2B 下映射为探针私有 lane 层 _V2）。
#   默认 {} = 关闭 ⇒ 逐字节可复现。
_LMAP = json.loads(__import__("os").environ.get("CO10_LMAP") or "{}")
# CO-205p（L2 自裁 · 逐页混合拓扑）：把指定页的**两条竖段**（escape+stub）整体落外层 B.Cu
#   ⇒ 该页 corner = B<->In5、drop = In5<->B、via1 = F<->B（通孔）全外层锚定，无需桥。
#   语义 pid 列表（逗号分隔）；默认 "" = 关闭 ⇒ 旧行为逐字节可复现。
_BVERT = {_t.strip() for _t in __import__("os").environ.get("CO10_BVERT", "").split(",") if _t.strip()}
# CO-205q（L2 自裁 · 工具缺陷 ③）：桥孔 jog **按列序**取远离方向（BRAWAY 按 pad 序号取，
#   In2 带不启用 carry ⇒ 行内列序可与 pad 序相反 ⇒ jog 反向互撞，vv_intra 复现）。
#   语义：P 的桥孔朝远离 N 逃逸列的方向偏 BR_JOG，N 反之 ⇒ 四种跨极性组合全部 >= ±BR_JOG。
#   默认关 ⇒ 候选 C 记录（24/32）逐字节可复现。
_BRCOL = __import__("os").environ.get("CO10_BRCOL", "") not in ("", "0")
# CO-205r（L2 自裁 · 列+桥孔联合闭式求解）：桥孔 **x 对齐逃逸列 + y 侧移**。
#   动机：候选 C 的 x 向 jog 使每页近芯片 x 足迹由 ~1.0mm 扩到 ~1.5mm > pad pitch 1.2mm
#   ⇒ 与邻页列必然互撞（vv_placed）。y 侧移把跨极性耦合解除（dy = BR_JOG + 2*POL_OFF >= VV），
#   同网孔距由 BR_JOG(0.5) 保证 ⇒ 桥孔 x 可取逃逸列 x（零 x 扩张），近芯片足迹不增。
#   同时落桥孔朝**远离 land**方向偏 ⇒ |sy-ll| >= BR_JOG（消 hh_intra，UP3 型）。默认关 ⇒ 候选 C 记录可复现。
_BR2 = __import__("os").environ.get("CO10_BR2", "") not in ("", "0")
_BR2D = __import__("os").environ.get("CO10_BR2D", "1" if _BR2 else "0") not in ("", "0")
# CO-205r：条件式落桥孔修复（仅当默认 ly+BR_JOG 与 land 孔距 < HOLE_GAP 时反向偏）⇒ 零回归修 hh_intra。
_BRDROP = __import__("os").environ.get("CO10_BRDROP", "") not in ("", "0")
# CO-205r：逃逸列间最小 x 距（默认 0.38 = 旧行为；VT=0.4525 时防 via-vs-In2 竖段 vt_intra）。
_XMIN = float(__import__("os").environ.get("CO10_XMIN", "0.38"))
# CO-205r（L2 自裁 · 列+桥孔联合闭式求解）：**band 级单调 carry 全带启用**（原仅外层 3W 带）。
#   游标间距 = max(3*w(layer), VV)；且计入桥孔向外 BR_JOG 的足迹延伸（BRCOL 时）。零回溯。
_CARRYALL = __import__("os").environ.get("CO10_CARRYALL", "") not in ("", "0")
# CO-205s（L2 自裁 · 工具缺陷 ④）：连接器侧列分配（J2 区间图着色 / J3·J4 _lx_separate）的
#   着色区间原只用 {lane_y, land_y}，漏计**桥孔 y**（lane 行 ±BR_JOG）⇒ 两页可被着同色却
#   在桥孔上撞（实测 DN2_N (141.22,57.65) × UP0/out_J2.P = 0.316）。开启后区间含桥孔 y。
#   默认关 ⇒ 候选 C 记录（24/32）逐字节可复现。
_COLFIX = __import__("os").environ.get("CO10_COLFIX", "") not in ("", "0")
_BEXT = _BR_JOG if (_CARRYALL and _BRIDGE and _BRCOL) else 0.0   # 仅 CARRYALL 生效 ⇒ 不扰动 BRCOL 单用


def _va(up_band: bool, kind: int):
    """kind 0=escape,1=stub：返回该带竖段所用的外层（F.Cu/B.Cu）。"""
    i = (0 if up_band else 1) + (0 if kind == 0 else 2)
    return "F.Cu" if _VA[i] == "F" else "B.Cu"


def esc_layer(f):
    if f["page_id"] in _BVERT:
        return "B.Cu"
    _ov = _LMAP.get(f["page_id"], {}).get("esc")
    if _ov:
        return _V2 if _ov == "B.Cu" else _ov
    if _VOUT:
        return _va(f["band"] == "up", 0)     # CO-205d 外层竖段指派
    if _ALLB:
        return "B.Cu"      # CO-204：竖段层全落 B.Cu（run 仍 In5）
    if _ALLI2:
        return "In2.Cu"    # CO-205：竖段层全落 In2（候选 A）
    # CO-16 候选：东侧 escape 层对调（up→In2 / dn→B），配合 up stub→B ⇒ 每线 via ≤6
    if _EFL and f["corridor"] == "EAST_CHIP_TO_J2":
        return "In2.Cu" if f["band"] == "up" else "B.Cu"
    if _V2B:
        _e = ESC_MAP[(f["corridor"], f["band"])]
        return _V2 if _e == "B.Cu" else _e
    return ESC_MAP[(f["corridor"], f["band"])]


def row_lower(f):
    return min(f["conn_pad"]["P"][1], f["conn_pad"]["N"][1]) >= GAP[f["conn_ref"]]


# CO-10 §3.3: 西侧 4 行组 stub 2-着色（按 y 区间，与 band 无关）
#   G0(J3 上排 43.25)->In2 ; G1(J3 下排 45.75)->In6 ; G2(J4 上排 61.45)->In2 ; G3(J4 下排 63.95)->In6
GS_IN2 = {("J3", "U"): True, ("J3", "L"): False, ("J4", "U"): True, ("J4", "L"): False}
_ST = __import__("os").environ.get("CO10_STUB", "")
if _ST == "all":
    for _g in GS_IN2: GS_IN2[_g] = True
elif _ST:
    for _t in _ST.split(","):
        if len(_t) == 3: GS_IN2[(_t[:2], _t[2])] = True


def row_group(f):
    mid = GAP[f["conn_ref"]]
    return (f["conn_ref"], "U" if min(f["conn_pad"]["P"][1], f["conn_pad"]["N"][1]) < mid else "L")


def stub_layer(f):
    if f["page_id"] in _BVERT:
        return "B.Cu"
    _ov = _LMAP.get(f["page_id"], {}).get("stub")
    if _ov:
        return _V2 if _ov == "B.Cu" else _ov
    if _TOPOE:
        return "In2.Cu" if esc_layer(f) == "In2.Cu" else "B.Cu"   # CO-205i：stub = 逃逸层
    if _STUB_B:
        return "B.Cu"      # CO-205g：stub 全落外层 B
    if _STUB_LANE:
        return "In5.Cu"    # CO-205f：stub 全落 lane 层
    if _VOUT:
        return _va(f["band"] == "up", 1)     # CO-205d 外层竖段指派
    if _ALLB:
        return "B.Cu"      # CO-204：竖段层全落 B.Cu（run 仍 In5）
    if _ALLI2:
        return "In2.Cu"    # CO-205：竖段层全落 In2（候选 A）
    if f["conn_ref"] == "J2":
        if not EASTSPLIT:
            return "In2.Cu"
        if EASTSPLIT in ("in2", "in2c"):     # CO-16 候选：东侧 stub 全 In2
            return "In2.Cu"
        if EASTSPLIT == "b2":                # CO-16 候选：up stub In2（6 via）/ dn stub B（6 via，安全 hop land）
            return "In2.Cu" if f["band"] == "up" else "B.Cu"
        if EASTSPLIT == "ub":                # CO-16 候选：up stub B（8 via 安全 land）/ dn stub In2（4 via）
            return "B.Cu" if f["band"] == "up" else "In2.Cu"
        if EASTSPLIT == "ball":              # CO-16 候选：东侧全部 stub 落 B（In2 仅剩 landing via 点）
            return "B.Cu"
        if EASTSPLIT == "b":                 # CO-16 候选：up stub In2 / dn stub B（无 In6 stub ⇒ 不穿 lane）
            return "In2.Cu" if f["band"] == "up" else "B.Cu"
        return "In6.Cu" if f["band"] == "up" else "In2.Cu"
    return "In2.Cu" if GS_IN2[row_group(f)] else (_V2 if _V2B else "In5.Cu")   # 真板 lane 层


def r3_build(rule):
    r3 = W.r3_place(J["r3_gaps"], LANES, "y", J.get("r3_base"))
    A = dict(r3["assignment"])
    j2k = [k for k, a in A.items() if a["ref"] == "J2" and a.get("page") in LANES and a.get("kind") == "data"]
    if EASTSPLIT == "in2c":
        # CO-16：J2 列 = 区间图确定性贪心着色（每侧独立；区间图 ⇒ 贪心=最优，色数=max depth）
        _ent = []
        for k in j2k:
            a = A[k]; f = FACTS[a["page"]]
            ly = LANES[a["page"]]["lane_y"]; lx0, ll = a["column_x"], a["landing"][1]
            if _COLMODE == "pol":
                ly += pol_off(f, a["pol"])
            # CO-205s（L2 自裁 · 列+桥孔联合求解）：着色区间须含**桥孔 y**。
            #   桥在 lane 行 ±BR_JOG 处另加一孔；原区间只用 {lane_y, land_y} ⇒ 桥孔落在区间外 ⇒
            #   两页可被着同色却在桥孔上撞（实测 DN2_N (141.22,57.65) × UP0/out_J2.P = 0.316）。
            _ys = [ly, ll]
            if _COLFIX and _BRIDGE and _stub_layer_of(a) == "In2.Cu":
                _dh = ly + _BR_JOG
                if _BR2D or (_BRDROP and abs(_dh - ll) < _HOLE_GAP):
                    _dh = ly - (1.0 if ll > ly else -1.0) * _BR_JOG
                _ys.append(_dh)
            _ent.append({"k": k, "side": 0 if abs(a["pad_x"] - J2_IN) < 1e-6 else 1,
                         "vx": max(f["pad"]["P"][0], f["pad"]["N"][0]), "ys": _ys,
                         "lo": min(_ys) - VV / 2.0, "hi": max(_ys) + VV / 2.0})
        def _conf(e, u):
            """同色两页是否冲突：COLFIX 用**精确 via y 集**判据（充分且必要），
            否则用旧区间重叠判据（保守过头）。"""
            # 只判 y 区间重叠（= 竖段/落段占位）；**不可**退化为「仅比 via y」——
            # 否则同列两页的竖段（lx 常量、y 跨越 [ly,ll]）会共线重叠（实测 24 -> 14）。
            return (e["lo"] < u["hi"] - TOL and u["lo"] < e["hi"] - TOL)

        _col = {}
        for side in (0, 1):
            sub = sorted([e for e in _ent if e["side"] == side], key=lambda e: (e["lo"], e["k"]))
            used = []                                     # list of (k, lo, hi, ent)
            for e in sub:
                kk = 0
                while any(abs(kk - u[0]) < 1 and _conf(e, u[3]) for u in used):
                    kk += 1
                _col[e["k"]] = kk; used.append((kk, e["lo"], e["hi"], e))
            # O4 感知：真着色对色值置换不变 ⇒ 按组内最大 pad_x 降序重排色值（大 vx 页取小 offset ⇒ R 大、ΔL 小）
            _grp = {}
            for e in sub:
                _grp.setdefault(_col[e["k"]], []).append(e)
            for _new, _old in enumerate(sorted(_grp, key=lambda g: -max(e["vx"] for e in _grp[g]))):
                for e in _grp[_old]:
                    _col[e["k"]] = _new
        for k in j2k:
            a = A[k]; _inner = abs(a["pad_x"] - J2_IN) < 1e-6
            lx = W.fp(J2L - J2STEP * _col[k]) if _inner else W.fp(J2R + J2STEP * _col[k])
            A[k] = dict(a, column_x=lx, landing=[lx, a["landing"][1]])
    elif EASTSPLIT:
        # CO-16：逐带 per-page rank + J2STEP（跨带 stub 异层 ⇒ 列可复用 ⇒ 落列收拢 ⇒ O4 可闭合）
        byb = {}
        for k in j2k:
            byb.setdefault(FACTS[A[k]["page"]]["band"], {}).setdefault(A[k]["page"], []).append(k)
        for _b, _pm in byb.items():
            _order = sorted(_pm, key=lambda q: LANES[q]["lane_index"])
            _n = len(_order)
            # CO-16 列分配口径：
            #   ub  ⇒ 压缩 8 列/侧 + 反对称配对（In2 仅 dn stub + up landing 点，y 互斥 ⇒ 可复用列）
            #   in2/b2 ⇒ 奇偶交错 16 列/侧（两带 stub 同在 In2 ⇒ 必须列互斥）
            _par = 0 if EASTSPLIT == "ub" else (1 if _b == "dn" else 0)
            for _r, _pg in enumerate(_order):
                if EASTSPLIT == "ub":
                    _kin = _r
                    _kout = (_n - 1) - _r
                else:
                    _kin = 2 * _r + _par
                    _kout = (2 * _n - 2 + _par) - 2 * _r
                for k in _pm[_pg]:
                    a = A[k]
                    _inner = abs(a["pad_x"] - J2_IN) < 1e-6
                    _off = _kin if _inner else _kout
                    lx = W.fp(J2L - J2STEP * _off) if _inner else W.fp(J2R + J2STEP * _off)
                    A[k] = dict(a, column_x=lx, landing=[lx, a["landing"][1]])
    else:
        pgs = sorted({A[k]["page"] for k in j2k}, key=lambda p: LANES[p]["lane_index"])
        rank = {p: i for i, p in enumerate(pgs)}
        for k in j2k:
            a = A[k]; r = rank[a["page"]]
            lx = W.fp(J2L - J2P * r) if abs(a["pad_x"] - J2_IN) < 1e-6 else W.fp(J2R + J2P * r)
            A[k] = dict(a, column_x=lx, landing=[lx, a["landing"][1]])
    for k, a in list(A.items()):
        if a["ref"] in ("J3", "J4"):
            mid = GAP[a["ref"]]
            if rule == "d3":            # CO-09 §4ter
                lx, ll = a["pad_x"], (mid - 0.35 if a["pad_y"] < mid else mid + 0.35)
            else:                       # CO-10: 共享 8 列 fan + 每 band 独立 breakout y
                g = (a["ref"], "U" if a["pad_y"] < mid else "L")
                lx = W.fp(a["pad_x"] - 0.3 + FAN_DX[g]); ll = FAN_Y[g]
            A[k] = dict(a, column_x=lx, landing=[lx, W.fp(ll)])
    if rule != "d3":
        _lx_separate(A)
    return {"assignment": A, "certificates": r3["certificates"]}


def _stub_layer_of(a):
    if _TOPOE:
        return "In2.Cu" if esc_layer(FACTS[a["page"]]) == "In2.Cu" else "B.Cu"   # CO-205i
    if _STUB_B:
        return "B.Cu"      # CO-205g
    if _STUB_LANE:
        return "In5.Cu"    # CO-205f
    if _VOUT:
        return _va(FACTS[a["page"]]["band"] == "up", 1)   # CO-205d 外层竖段指派
    if _ALLI2:
        return "In2.Cu"    # CO-205：竖段层全落 In2（候选 A）
    if a["ref"] == "J2":
        if not EASTSPLIT:
            return "In2.Cu"
        if EASTSPLIT in ("in2", "in2c"):
            return "In2.Cu"
        if EASTSPLIT == "b2":
            return "In2.Cu" if FACTS[a["page"]]["band"] == "up" else "B.Cu"
        if EASTSPLIT == "ub":
            return "B.Cu" if FACTS[a["page"]]["band"] == "up" else "In2.Cu"
        if EASTSPLIT == "ball":
            return "B.Cu"
        if EASTSPLIT == "b":
            return "In2.Cu" if FACTS[a["page"]]["band"] == "up" else "B.Cu"
        return "In6.Cu" if FACTS[a["page"]]["band"] == "up" else "In2.Cu"
    mid = GAP[a["ref"]]
    g = (a["ref"], "U" if a["pad_y"] < mid else "L")
    return "In2.Cu" if GS_IN2[g] else (_V2 if _V2B else "In5.Cu")   # 真板 lane 层


def _lx_separate(A):
    """CO-11 §13：connector 侧 lx 前缀分配（零搜索单遍，**按页整体偏移**）。
    - P/N 同 δ 平移 => 保持 pad 相对次序 => 不产生 land 段互叉（§12 修正项 a）。
    - δ 网格 0.6mm（=pad pitch，落另一中缝列）=> 页间 lx 净距 >=0.525。
    同层 stub/land 的 y 区间重叠时，要求页间 lx >= VV(0.525)。"""
    ents = []
    for k, a in A.items():
        if a["ref"] not in ("J3", "J4"):
            continue
        page = a.get("page")
        if page not in LANES:
            continue
        ents.append({"key": k, "a": a, "page": page, "S": _stub_layer_of(a)})
    bypage = {}
    for e in ents:
        bypage.setdefault(e["page"], []).append(e)
    _PRIO = __import__("os").environ.get("CO10_LXPRIO", "")
    if _PRIO == "landlen":
        # CO-36（D3b 收官，L2：落列/过孔策略，闭式非搜索）：
        #   connector 侧落列偏移的**容差 ∝ land 段长度 |ll - conn_y|**——短 land 段（J4U 1.25mm /
        #   J4L 1.05mm）对 |dx| 敏感：斜度大 ⇒ 段身扫过邻焊盘 ⇒ 铜距 < 0.075（D3b 6 条）；
        #   长 land 段（J3U 8.75mm / J3L 5.75mm）在焊盘行附近已收敛到 conn_x ⇒ 可吸收较大偏移。
        #   故：同 stub 层内**按 land 段长度升序**处理 ⇒ 短段先取自然列（delta=0），长段吸收偏移。
        #   确定性单遍排序，无搜索/无回溯；默认关闭（旧行为 + ALLOC.1..4 逐字节可复现）。
        def _landlen(q):
            return abs(bypage[q][0]["a"]["landing"][1] - FACTS[q]["conn_pad"]["P"][1])
        pages = sorted(bypage, key=lambda q: (bypage[q][0]["S"], round(_landlen(q), 3),
                                              round(LANES[q]["lane_y"], 3), q))
    else:
        pages = sorted(bypage, key=lambda q: (bypage[q][0]["S"], round(LANES[q]["lane_y"], 3), q))
    placed = []
    for pg in pages:
        grp = bypage[pg]
        S = grp[0]["S"]
        ly = LANES[pg]["lane_y"]
        lo = min(min(ly, g["a"]["landing"][1]) for g in grp)
        hi = max(max(ly, g["a"]["landing"][1]) for g in grp)
        if _COLFIX and _BRIDGE and _stub_layer_of(grp[0]["a"]) == "In2.Cu":   # CO-205s：含桥孔 y
            _dh = ly + _BR_JOG
            _ll0 = grp[0]["a"]["landing"][1]
            if _BR2D or (_BRDROP and abs(_dh - _ll0) < _HOLE_GAP):
                _dh = ly - (1.0 if _ll0 > ly else -1.0) * _BR_JOG
            lo = min(lo, _dh); hi = max(hi, _dh)
        best = None
        for d in (0.0, 0.6, -0.6, 1.2, -1.2, 1.8, -1.8, 2.4, -2.4, 3.0, -3.0, 3.6, -3.6):
            xs = [g["a"]["column_x"] + d for g in grp]
            okd = True
            for q in placed:
                if q["S"] != S:
                    continue
                if lo >= q["hi"] - VV or hi <= q["lo"] + VV:
                    continue
                for x in xs:
                    if abs(x - q["lx"]) < VV - TOL:
                        okd = False; break
                if not okd:
                    break
            if okd:
                best = d; break
        d = best if best is not None else 0.0
        for g in grp:
            g["a"]["column_x"] = W.fp(g["a"]["column_x"] + d)
            g["a"]["landing"] = [W.fp(g["a"]["column_x"]), g["a"]["landing"][1]]
            placed.append({"S": S, "lx": g["a"]["column_x"], "lo": lo, "hi": hi})


FAN_Y = {("J3", "U"): 42.0, ("J3", "L"): 44.2, ("J4", "U"): 60.2, ("J4", "L"): 65.0}
_FY = __import__("os").environ.get("CO10_FANY_J3", "")
if _FY:
    _u, _l = (float(v) for v in _FY.split(","))
    FAN_Y[("J3", "U")] = _u; FAN_Y[("J3", "L")] = _l
FAN_DX = {("J3", "U"): 0.0, ("J3", "L"): 0.0, ("J4", "U"): 0.0, ("J4", "L"): 0.0}
_FXG = __import__("os").environ.get("CO10_FANDX", "")
if _FXG:
    for _t in _FXG.split(","):
        _k, _val = _t.split(":"); FAN_DX[(_k[:2], _k[2])] = float(_val)
_FX = float(__import__("os").environ.get("CO10_FANDX_J4", "0"))
_FX3 = float(__import__("os").environ.get("CO10_FANDX_J3", "0"))
if _FX or _FX3:
    for _g in list(FAN_DX):
        if _g[0] == "J4": FAN_DX[_g] += _FX
        if _g[0] == "J3": FAN_DX[_g] += _FX3


# CO-23：西侧 lane 索引**约束分配**（确定性单遍贪心；非坐标搜索）。
#   机理：西侧 lane 块跨越多条 landing 行（FANY_J3/J4），而 landing 行固定于 connector 侧。
#   (1) 同页同极性：drop via(lx,lane_y) ↔ land via(lx,land_y) => 同网钻孔距 >= HOLE_GAP(0.4495)
#       （实测 DRC hole_to_hole：UP2_P lane 34.5865 vs land 34.5）。
#   (2) 共享落列（J3-U/J3-L 同 connector 共用 8 列；J4-L 与 J3 反向共用）：
#       lane via(lx,lane_y) ↔ 他页 land via(lx,land_y) => 异网 via 净距 >= VV(0.525)
#       （实测 vv_placed：DN0_P (64.0,35.0) × UP0_P land (64.0,34.5) = 0.50）。
#   规则：按 (conn row_y, conn_x) 原帧序逐页取**最小可用 lane 索引**，两个极性 lane_y 值
#   {base±POL_OFF} 均须满足上述判据；已占用索引跳过。全部约束为静态 → O(n^2) 闭式。
if __import__("os").environ.get("CO10_WORDER") == "landrow":
    _hg = float(__import__("os").environ.get("CO10_HOLE_GAP", "0.4495"))
    _westp = [q for q in LANES if FACTS[q]["corridor"] == "WEST_MCIO_TO_CHIP"]
    _landx, _landy = {}, {}
    for _q in _westp:
        _g = row_group(FACTS[_q])
        _landy[_q] = FAN_Y[_g]
        for _p2 in ("P", "N"):
            _landx[(_q, _p2)] = W.fp(FACTS[_q]["conn_pad"][_p2][0] - 0.3 + FAN_DX[_g])
    _fixed = [(_landx[(_q, _p2)], _landy[_q], _q) for _q in _westp for _p2 in ("P", "N")]
    _westp.sort(key=lambda q: (FACTS[q]["row_y"], FACTS[q]["conn_x"], q))
    _free = list(range(len(_westp)))
    _asg = {}
    for _q in _westp:
        _pick = None
        for _i in _free:
            _b = _WL + _i * _WS
            _ok = True
            for _p2 in ("P", "N"):
                _x = _landx[(_q, _p2)]
                for _v in (_b - POL_OFF, _b + POL_OFF):
                    for (_x2, _y2, _q2) in _fixed:
                        if abs(_x2 - _x) > 1e-6:
                            continue
                        _need = _hg if _q2 == _q else VV
                        if abs(_v - _y2) < _need - TOL:
                            _ok = False; break
                    if not _ok: break
                if not _ok: break
            if _ok:
                _pick = _i; break
        if _pick is None:
            _pick = _free[0]
        _asg[_q] = _pick; _free.remove(_pick)
    for _q, _i in _asg.items():
        LANES[_q]["lane_index"] = _i
        LANES[_q]["lane_y"] = W.fp(_WL + _i * _WS)


# CO-23：西侧 lane 索引**定点置换**（CO10_WSWAP="1-8,2-9"：帧序位置 ⇄ lane 索引成对交换）。
#   用途：原帧序（conn_x 升序）中位置 1 的 lane（WLO+WSTEP，pol ±0.25）恰好压在 J3-U 的
#   landing 行 FANY_J3 上（同页 drop/land via 钻孔距 < 0.4495）；把该位置与无共享落列的页
#   交换（如 J4-U 的首页）即可闭式消除，无需重排整块。
_sw = __import__("os").environ.get("CO10_WSWAP", "")
if _sw:
    _wp = sorted([q for q in LANES if FACTS[q]["corridor"] == "WEST_MCIO_TO_CHIP"],
                 key=lambda q: LANES[q]["lane_index"])
    for _pair in _sw.split(","):
        _a, _b = (int(_v) for _v in _pair.split("-"))
        _qa, _qb = _wp[_a], _wp[_b]
        _ia, _ib = LANES[_qa]["lane_index"], LANES[_qb]["lane_index"]
        LANES[_qa]["lane_index"] = _ib; LANES[_qb]["lane_index"] = _ia
        LANES[_qa]["lane_y"] = W.fp(_WL + _ib * _WS)
        LANES[_qb]["lane_y"] = W.fp(_WL + _ia * _WS)


def y_bias(f):
    """同 band 内不同 connector 的 escape 竖段在 y 上错开 0.6：
    west-up  J3(+pad_y-0.3) / J4(+pad_y+0.3) => 竖段 y 区间互斥，解耦其 x 分配。"""
    if f["corridor"] == "WEST_MCIO_TO_CHIP" and f["band"] == "up":
        return -0.3 if f["conn_ref"] == "J3" else 0.3
    return 0.0


def land_meta(f):
    out = {}
    for pol in ("P", "N"):
        a = R3["assignment"].get(f["conn_ref"] + "|" + f["nets"][pol])
        out[pol] = None if a is None else (float(a["column_x"]), float(a["landing"][1]))
    return out


def _cross_seg(a, b, c, d):
    """真交叉（proper intersection）判定（与引擎 count_crossings 同语义）。"""
    def o(p, q, r):
        v = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else 2)
    def on(p, q, r):
        return (min(p[0], r[0]) - 1e-9 <= q[0] <= max(p[0], r[0]) + 1e-9 and
                min(p[1], r[1]) - 1e-9 <= q[1] <= max(p[1], r[1]) + 1e-9)
    o1, o2, o3, o4 = o(a, b, c), o(a, b, d), o(c, d, a), o(c, d, b)
    if o1 != o2 and o3 != o4:
        return 1
    return 1 if ((o1 == 0 and on(a, c, b)) or (o2 == 0 and on(a, d, b))
                 or (o3 == 0 and on(c, a, d)) or (o4 == 0 and on(c, b, d))) else 0


def pt_seg(px_, py_, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
    L2 = np.where(L2 < 1e-12, 1.0, L2)
    t = np.clip(((px_ - x1) * dx + (py_ - y1) * dy) / L2, 0, 1)
    return np.sqrt((px_ - (x1 + t * dx)) ** 2 + (py_ - (y1 + t * dy)) ** 2)


def seg_seg(a, b, X1, Y1, X2, Y2):
    return np.minimum(np.minimum(pt_seg(a[0], a[1], X1, Y1, X2, Y2), pt_seg(b[0], b[1], X1, Y1, X2, Y2)),
                      np.minimum(pt_seg(X1, Y1, a[0], a[1], b[0], b[1]), pt_seg(X2, Y2, a[0], a[1], b[0], b[1])))


def pad_seg_edge(a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    L2 = np.where(L2 < 1e-12, 1.0, L2)
    t = np.clip(((PXA - ax) * dx + (PYA - ay) * dy) / L2, 0, 1)
    qx, qy = ax + t * dx, ay + t * dy
    ex = np.maximum(np.abs(qx - PXA) - PHX, 0.0); ey = np.maximum(np.abs(qy - PYA) - PHY, 0.0)
    return np.where(PCIRC, np.maximum(np.sqrt((qx - PXA) ** 2 + (qy - PYA) ** 2) - PRA, 0.0),
                    np.sqrt(ex * ex + ey * ey))


def pad_via_edge(x, y):
    ex = np.maximum(np.abs(x - PXA) - PHX, 0.0); ey = np.maximum(np.abs(y - PYA) - PHY, 0.0)
    return np.where(PCIRC, np.maximum(np.sqrt((x - PXA) ** 2 + (y - PYA) ** 2) - PRA, 0.0),
                    np.sqrt(ex * ex + ey * ey))


class Store:
    def __init__(self):
        self.vx = np.zeros(0); self.vy = np.zeros(0); self.vm = np.zeros(0, dtype=int)
        self.S = {l: np.zeros((0, 4)) for l in LAYERS}; self.SP = {l: np.zeros(0, dtype=bool) for l in LAYERS}
        self.vlab = []; self.SLAB = {l: [] for l in LAYERS}

    def add(self, vias, segs, pid="?"):
        for (x, y, pol, lays) in vias:
            self.vlab.append(pid + "." + pol)
            m = 0
            for l in lays: m |= 1 << LI[l]
            self.vx = np.append(self.vx, x); self.vy = np.append(self.vy, y); self.vm = np.append(self.vm, m)
        for (lay, x1, y1, x2, y2, pa, pol) in segs:
            self.S[lay] = np.vstack([self.S[lay], [x1, y1, x2, y2]])
            self.SP[lay] = np.append(self.SP[lay], pa); self.SLAB[lay].append(pid + "." + pol)


def build(f, px, py, nx, ny):
    E = esc_layer(f); S = stub_layer(f); lm = land_meta(f)
    if lm["P"] is None or lm["N"] is None:
        return None
    def _sp(a, b):
        """过孔占用层集：_SPAN 时展开为起止层之间全部信号层（物理事实）。"""
        if not _SPAN:
            return (a, b)
        i, j = _SI[a], _SI[b]
        if i > j:
            i, j = j, i
        return tuple(_SPAN_ORDER[i:j + 1])

    vias, segs, own = [], [], []
    L = _LANE_V2 if _V2B else "In5.Cu"      # 真板 lane 层（_V2B 用私有层占位）
    for pol, vx, vy in (("P", px, py), ("N", nx, ny)):
        lx, ll = lm[pol]
        ly = W.fp(LANES[f["page_id"]]["lane_y"] + pol_off(f, pol))
        own += [(round(f["pad"][pol][0], 3), round(f["pad"][pol][1], 3)),
                (round(f["conn_pad"][pol][0], 3), round(f["conn_pad"][pol][1], 3))]
        if _TOPOE:
            # 拓扑 E：lane 层按逃逸带取（In2 带 -> F.Cu；B 带 -> In5.Cu），stub = 逃逸层。
            if E == "In2.Cu":
                L, S = "F.Cu", "In2.Cu"
            else:
                L, S = "In5.Cu", "B.Cu"
            vias.append((vx, vy, pol, _sp("F.Cu", E)))
            if E != L:
                vias.append((vx, ly, pol, _sp(E, L)))
            if S != L:
                vias.append((lx, ly, pol, _sp(L, S)))
            if S != "F.Cu":
                vias.append((lx, ll, pol, _sp(S, "F.Cu")))
            segs.append(("F.Cu", f["pad"][pol][0], f["pad"][pol][1], vx, vy, True, pol))
            segs.append((E, vx, vy, vx, ly, False, pol))
            segs.append((L, vx, ly, lx, ly, False, pol))
            segs.append((S, lx, ly, lx, ll, False, pol))
            segs.append(("F.Cu", lx, ll, f["conn_pad"][pol][0], f["conn_pad"][pol][1], True, pol))
            continue
        if _BRIDGE:
            # CO-205e 候选 C：冻结层计划 + 双孔桥（仅替换内层<->内层 corner/drop）
            B, L = "B.Cu", "In5.Cu"
            up = f["band"] == "up"
            if _BRCOL:
                # 列序感知：P 朝远离 N 列方向偏，N 反之（px = P 列, nx = N 列）
                _sgn = 1.0 if px > nx else -1.0
                _jd = _sgn if pol == "P" else -_sgn
            elif _BR_AWAY:
                _sr = 1.0 if f["pad"]["P"][0] >= f["pad"]["N"][0] else -1.0
                _jd = _sr * (1.0 if pol == "P" else -1.0)
            else:
                _jd = (1.0 if pol == "P" else -1.0) if _BR_FLIP else (1.0 if up else -1.0)
            _lyo = LANES[f["page_id"]]["lane_y"] + pol_off(f, "N" if pol == "P" else "P")
            if E != "F.Cu":
                vias.append((vx, vy, pol, _sp("F.Cu", E)))             # via1（E==B 时为通孔；E==F 时无孔）
            _cy = ly
            if E == B:
                _cx = vx
                vias.append((vx, ly, pol, _sp(B, L)))                  # corner B<->In5（已外层锚定）
            elif E == "F.Cu":
                # CO-205s（L2 自裁 · 近芯片孔密度）：**逃逸段落 F**（短逃逸页；西侧 ~1.9mm）
                #   ⇒ 近芯片每极性孔数 3 -> 1（仅 F<->In5），无 via1、无 corner 桥；
                #   代价 = 逃逸 F 竖段（长度 = |pad_y - lane_y|）占用顶层走廊。
                _cx = vx
                vias.append((vx, ly, pol, _sp("F.Cu", L)))             # corner F<->In5（外层锚定）
            elif E == "In2.Cu":
                # 桥走 **F.Cu**（顶层，走廊区空闲）：In2<->F + 短 F 段 + F<->In5。
                # 关键：避免占用 B.Cu 竖列（对带 B 逃逸列与 chip pad 同 x ⇒ 必砸）。
                _ov = _BRMAP.get(f["page_id"], {}).get("cx", {}).get(pol)
                if _ov is not None:
                    _cx = vx + float(_ov)
                elif _BR2:
                    # CO-205r 闭式：桥孔 x = 逃逸列 x（零 x 扩张 ⇒ 不抢邻页列位）；
                    #   y 朝远离对面极性 lane 行方向偏 BR_JOG ⇒ 跨极性任意组合 dy >= BR_JOG + 2*POL_OFF。
                    _cx = vx
                    _cy = ly - (1.0 if _lyo > ly else -1.0) * _BR_JOG
                elif _BRX2 > 0:
                    _cx = vx + _BRX2 * (lx - vx)
                else:
                    _cx = vx + _jd * _BR_JOG
                vias.append((vx, ly, pol, _sp("In2.Cu", "F.Cu")))
                vias.append((_cx, _cy, pol, _sp("F.Cu", L)))
            else:                                                       # E == L：无 corner
                _cx = vx
            if S == "In2.Cu":
                # 桥走 F.Cu：In5<->F + 短 F 段 + F<->In2
                _ov2 = _BRMAP.get(f["page_id"], {}).get("sy", {}).get(pol)
                if _ov2 is not None:
                    _sy = ly + float(_ov2)
                elif _BR2D or (_BRDROP and abs((ly + _BR_JOG) - ll) < _HOLE_GAP):
                    # CO-205r 闭式：落桥孔朝远离 land 方向偏 ⇒ |sy - ll| >= BR_JOG、|sy - ly| = BR_JOG。
                    _sy = ly - (1.0 if ll > ly else -1.0) * _BR_JOG
                elif _BRX2 > 0:
                    _sy = ly + _BRX2 * (ll - ly)
                else:
                    _sy = ly + _BR_JOG
                vias.append((lx, ly, pol, _sp(L, "F.Cu")))
                vias.append((lx, _sy, pol, _sp("F.Cu", "In2.Cu")))
            else:
                _sy = ly
                if S != L:
                    vias.append((lx, ly, pol, _sp(L, S)))
            vias.append((lx, ll, pol, _sp(S, "F.Cu")))                  # land
            segs.append(("F.Cu", f["pad"][pol][0], f["pad"][pol][1], vx, vy, True, pol))
            segs.append((E, vx, vy, vx, ly, False, pol))
            if abs(_cx - vx) > TOL or abs(_cy - ly) > TOL:
                segs.append(("F.Cu", vx, ly, _cx, _cy, False, pol))     # 桥之 F 段
            segs.append((L, _cx, _cy, lx, ly, False, pol))
            if S == "In2.Cu":
                segs.append(("F.Cu", lx, ly, lx, _sy, False, pol))      # 桥之 F 竖段
            segs.append((S, lx, _sy, lx, ll, False, pol))
            segs.append(("F.Cu", lx, ll, f["conn_pad"][pol][0], f["conn_pad"][pol][1], True, pol))
            continue
        if _VOUT:
            # CO-205c 候选 D：竖段层 E,S ∈ {F,B}（外层），lane = In5.Cu（内层）。
            #   pad(F) -> [via1 F<->E，仅 E!=F 时] -> escape(E) -> corner E<->In5
            #   -> lane(In5) -> drop In5<->S -> stub(S) -> land S<->F -> conn(F)
            if E != "F.Cu":
                vias.append((vx, vy, pol, _sp("F.Cu", E)))
            if E != "In5.Cu":
                vias.append((vx, ly, pol, _sp(E, "In5.Cu")))
            if S != "In5.Cu":
                vias.append((lx, ly, pol, _sp("In5.Cu", S)))
            if S != "F.Cu":
                vias.append((lx, ll, pol, _sp(S, "F.Cu")))
        elif _V2B:
            # CO-205 候选 B 规范拓扑：via1 F<->E（E∈{In2,In5}，外层锚定）→ corner E<->lane
            #   → drop lane<->S → land S<->F。竖段层 = {In2, In5}；lane = 私有层（真板 B.Cu）。
            vias.append((vx, vy, pol, _sp("F.Cu", E)))
            if E != L:
                vias.append((vx, ly, pol, _sp(E, L)))
            if S != L:
                vias.append((lx, ly, pol, _sp(L, S)))
            if S != "F.Cu":
                vias.append((lx, ll, pol, _sp(S, "F.Cu")))
        else:
            vias.append((vx, vy, pol, _sp("F.Cu", "In2.Cu")))
            if E == "B.Cu":
                vias.append((vx, vy, pol, _sp("In2.Cu", "In5.Cu")))
                vias.append((vx, vy, pol, _sp("In5.Cu", "B.Cu")))
            vias.append((vx, ly, pol, _sp(E, "In5.Cu")))
            if S == "In2.Cu":                                   # lane(In6) -> drop -> In2 stub -> land
                vias.append((lx, ly, pol, _sp("In5.Cu", "In2.Cu")))
                vias.append((lx, ll, pol, _sp("In2.Cu", "F.Cu")))
            elif S == "B.Cu":                                   # lane(In6)->drop->B stub->land(B<->In6<->In2<->F，安全 hop)
                vias.append((lx, ly, pol, _sp("In5.Cu", "B.Cu")))
                vias.append((lx, ll, pol, _sp("B.Cu", "In5.Cu")))
                vias.append((lx, ll, pol, _sp("In5.Cu", "In2.Cu")))
                vias.append((lx, ll, pol, _sp("In2.Cu", "F.Cu")))
            else:                                               # lane(In6) -> In6 stub -> land stack
                vias.append((lx, ll, pol, _sp("In5.Cu", "In2.Cu")))
                vias.append((lx, ll, pol, _sp("In2.Cu", "F.Cu")))
        segs.append(("F.Cu", f["pad"][pol][0], f["pad"][pol][1], vx, vy, True, pol))
        segs.append((E, vx, vy, vx, ly, False, pol))
        segs.append((L, vx, ly, lx, ly, False, pol))
        segs.append((S, lx, ly, lx, ll, False, pol))
        segs.append(("F.Cu", lx, ll, f["conn_pad"][pol][0], f["conn_pad"][pol][1], True, pol))
    return vias, segs, np.array(own)


def check(vias, segs, own, st, pid=None):
    if _HOLE_GAP > 0:      # L2（CO-23）：同网钻孔距（同极性 via 对）=> 逃逸/落位竖段 >= HOLE_GAP
        for i in range(len(vias)):
            for j in range(i + 1, len(vias)):
                if vias[i][2] != vias[j][2]: continue
                d = math.hypot(vias[i][0] - vias[j][0], vias[i][1] - vias[j][1])
                if 1e-6 < d < _HOLE_GAP - TOL:   # d<1e-6 = 同点叠层（L4 合并为单孔）
                    return ("hh_intra", vias[i][:3], vias[j][:3], round(d, 4))
    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            if vias[i][2] == vias[j][2]: continue
            if math.hypot(vias[i][0] - vias[j][0], vias[i][1] - vias[j][1]) < VV - TOL:
                return ("vv_intra", vias[i][:3], vias[j][:3])
    nv = len(st.vx)
    if nv:
        for (x, y, pol, lays) in vias:
            m = 0
            for l in lays: m |= 1 << LI[l]
            d = np.hypot(st.vx - x, st.vy - y)
            bad = np.nonzero((d < VV - TOL) & ((st.vm & m) != 0))[0]
            if len(bad):
                return ("vv_placed", (x, y, pol), st.vlab[int(bad[0])], round(float(d[bad[0]]), 3))
    for (x, y, pol, lays) in vias:
        for l in lays:
            X = st.S[l]
            if not len(X): continue
            d = pt_seg(x, y, X[:, 0], X[:, 1], X[:, 2], X[:, 3])
            thr = np.where(st.SP[l], VT_E, VT)
            bad = np.nonzero(d < thr - TOL)[0]
            if len(bad):
                return ("vt_placed", (x, y, pol, l), st.SLAB[l][int(bad[0])], round(float(d[bad[0]]), 4))
    if nv:
        for (lay, x1, y1, x2, y2, pa, pol) in segs:
            d = pt_seg(st.vx, st.vy, x1, y1, x2, y2)
            bad = np.nonzero((d < (VT_E if pa else VT) - TOL) & ((st.vm & (1 << LI[lay])) != 0))[0]
            if len(bad):
                return ("vt2_placed", (lay, x1, y1, x2, y2, pol), st.vlab[int(bad[0])], round(float(d[bad[0]]), 4))
    for (x, y, pol, lays) in vias:                      # candidate via vs candidate tracks
        for (lay, x1, y1, x2, y2, pa, pol2) in segs:
            if pol2 == pol or lay not in lays: continue
            if pt_seg(x, y, np.array([x1]), np.array([y1]), np.array([x2]), np.array([y2]))[0] < (VT_E if pa else VT) - TOL:
                return ("vt_intra", (x, y, pol, lay))
    for (lay, x1, y1, x2, y2, pa, pol) in segs:    # candidate seg vs candidate seg（同页异极性真交叉）
        for (lay2, u1, v1, u2, v2, pa2, pol2) in segs:
            if lay != lay2 or pol == pol2:
                continue
            if (_cross_seg((x1, y1), (x2, y2), (u1, v1), (u2, v2))):
                return ("cross_intra", (lay, x1, y1, x2, y2, pol), (lay2, u1, v1, u2, v2, pol2))
    # 跨页 proper-intersection（CO-11 §12 教训：原 check() 仅同页 cross_intra + 端点距离，
    # 端点距离对「两段真交叉」恒 >0 ⇒ 漏检；独立复核器已抓出，此处补齐使探针自洽）。
    for (lay, x1, y1, x2, y2, pa, pol) in segs:
        X = st.S[lay]
        if not len(X):
            continue
        lo_x, hi_x = min(x1, x2) - 1e-9, max(x1, x2) + 1e-9
        lo_y, hi_y = min(y1, y2) - 1e-9, max(y1, y2) + 1e-9
        for _t in range(len(X)):
            u1, v1, u2, v2 = X[_t]
            if max(u1, u2) < lo_x or min(u1, u2) > hi_x or max(v1, v2) < lo_y or min(v1, v2) > hi_y:
                continue
            if _cross_seg((x1, y1), (x2, y2), (u1, v1), (u2, v2)):
                return ("cross_placed", (lay, x1, y1, x2, y2, pol), st.SLAB[lay][_t])
    for (lay, x1, y1, x2, y2, pa, pol) in segs:
        X = st.S[lay]
        if not len(X): continue
        d = seg_seg((x1, y1), (x2, y2), X[:, 0], X[:, 1], X[:, 2], X[:, 3])
        thr = np.where(st.SP[lay] | pa, TT_E, TT).astype(float)
        if _IP3W and pid is not None and (not pa) and lay in _WBY:
            cdx, cdy = x2 - x1, y2 - y1
            cl = math.hypot(cdx, cdy)
            if cl > TOL:
                sdx = X[:, 2] - X[:, 0]; sdy = X[:, 3] - X[:, 1]
                sl = np.hypot(sdx, sdy)
                cross = np.abs(sdx * cdy - sdy * cdx)
                par = (sl > TOL) & (cross <= _PAR_SIN * sl * cl + TOL)
                other = np.array([str(v).rsplit(".", 1)[0] != str(pid) for v in st.SLAB[lay]])
                thr = np.where((~st.SP[lay]) & par & other, max(TT, 3.0 * _WBY[lay]), thr)
        bad = np.nonzero(d < thr - TOL)[0]
        if len(bad):
            return ("tt_placed", (lay, x1, y1, x2, y2, pol), st.SLAB[lay][int(bad[0])], round(float(d[bad[0]]), 4))
    for (lay, x1, y1, x2, y2, pa, pol) in segs:
        if lay != "F.Cu": continue
        d = pad_seg_edge((x1, y1), (x2, y2))
        for idx in np.nonzero(d < ESC - TOL)[0]:
            if len(own) and min(abs(own[:, 0] - PXA[idx]) + abs(own[:, 1] - PYA[idx])) < 0.01: continue
            return ("pad_seg", (x1, y1, x2, y2), PKEY[idx], round(float(d[idx]), 4))
    for (x, y, pol, lays) in vias:
        d = pad_via_edge(x, y)
        for idx in np.nonzero(d < ESC - TOL)[0]:
            if len(own) and min(abs(own[:, 0] - PXA[idx]) + abs(own[:, 1] - PYA[idx])) < 0.01: continue
            return ("pad_via", (x, y, pol), PKEY[idx], round(float(d[idx]), 4))
    return None


def geom_rec(b, f):
    """(vias, segs) -> 可序列化几何（独立复核用）。"""
    vias, segs = b[0], b[1]
    return {"pad": {p: [f["pad"][p][0], f["pad"][p][1]] for p in ("P", "N")},
            "conn": {p: [f["conn_pad"][p][0], f["conn_pad"][p][1]] for p in ("P", "N")},
            "vias": [[float(x), float(y), pol, list(lays)] for (x, y, pol, lays) in vias],
            "segs": [[lay, float(x1), float(y1), float(x2), float(y2), bool(pa), pol]
                     for (lay, x1, y1, x2, y2, pa, pol) in segs]}


def band_key(f): return (f["corridor"], f["band"])


def alloc_x(verbose=False):
    """每 (corridor,band) 16 网的 escape-vertical x 前缀递推（>=0.46），
    x 取自该页 verdict 的合法 escape 窗口 [pad_x-0.35, pad_x+0.35]。"""
    VER = json.loads((SPEC / "m13_v57_s1_r1_via_verdict_r2.json").read_text())["pages"]
    need_avoid = {}                                        # west-up 长竖段须避开 east-up via1 x
    for pid, f in FACTS.items():
        if f["corridor"] == "EAST_CHIP_TO_J2" and f["band"] == "up":
            pass
    out = {}
    groups = {}
    for pid, f in FACTS.items():
        for pol in ("P", "N"):
            groups.setdefault((f["corridor"], f["band"]), []).append((f, pol))
    for key, items in groups.items():
        items.sort(key=lambda t: (t[0]["pad"][t[1]][0], t[0]["page_id"], t[1]))
        boxes = []
        for f, pol in items:
            cands = VER[f["page_id"]][pol]["cands"]
            xs = sorted({round(float(c[0]), 3) for c in cands})
            pad_x = f["pad"][pol][0]
            lo, hi = pad_x - 0.35, pad_x + 0.35
            ok = [x for x in xs if lo - TOL <= x <= hi + TOL] or [min(xs, key=lambda x: abs(x - pad_x))]
            tgt = pad_x - 0.3
            if boxes:
                tgt = max(tgt, boxes[-1] + 0.5)
            x = min(ok, key=lambda v: (abs(v - tgt), v))
            boxes.append(x)
            out[(f["page_id"], pol)] = x
    return out


def alloc_closed_form():
    """CO-11 §8.5：chip 区 via1 闭式目标（**逐页独立**，与落位顺序无关）。
    up band 目标 y 取 pad_y ∓ 0.4（下探至 dn 带之下），dn band 取 pad_y；x 取 pad_x（同页 P/N 分离由 pair 域保证）。
    选择 = pair 域中到目标最近的行（单遍 argmin，无搜索）。"""
    out = {}
    ysub = {("WEST_MCIO_TO_CHIP", "up"): ("le", 50.44), ("WEST_MCIO_TO_CHIP", "dn"): ("ge", 50.973),
            ("EAST_CHIP_TO_J2", "up"): ("le", 55.895), ("EAST_CHIP_TO_J2", "dn"): ("ge", 56.42)}
    for pid, f in FACTS.items():
        key = (f["corridor"], f["band"])
        mode, yv = ysub[key]
        for pol in ("P", "N"):
            py = f["pad"][pol][1]
            ty = py - 0.4 if f["band"] == "up" else py + 0.0
            ty = min(max(ty, py - YWIN), py + YWIN)
            ty = min(ty, yv) if mode == "le" else max(ty, yv)
            _tx = f["pad"][pol][0] + (_BOFF if f["band"] == "up" else -_BOFF)
            out[(pid, pol)] = (_tx, ty)
    return out


_IP3W_TGT = {}


def _ip3w_targets():
    """CO-143c：按 (corridor, conn_ref, band) 分带、按 pad-x 升序的**闭式单调列目标**：
    nxt_k = max(padN_k, prev_P + 3w)；pxt_k = max(padP_k, nxt_k + VT)。
    单遍、确定性、零回溯（把「对间 3W」化为列目标的 carry 而非事后搜索）。"""
    out = {}
    bands = {}
    for p, f in FACTS.items():
        bands.setdefault((f["corridor"], f["conn_ref"], f["band"]), []).append(p)
    for key, pids in bands.items():
        escL = esc_layer(FACTS[pids[0]])
        w = _WBY.get(escL)
        if w is None:
            continue
        prev_P = None
        for p in sorted(pids, key=lambda q: min(FACTS[q]["pad"]["N"][0], FACTS[q]["pad"]["P"][0])):
            f = FACTS[p]
            nxt = f["pad"]["N"][0]
            if prev_P is not None:
                nxt = max(nxt, prev_P + 3.0 * w)
            pxt = max(f["pad"]["P"][0], nxt + VT)
            out[p] = (nxt, pxt)
            prev_P = pxt
    return out


def probe(rule="d3", order="engine", verbose=False):
    global R3
    R3 = r3_build(rule)
    global _IP3W_TGT
    _IP3W_TGT = _ip3w_targets() if _IP3W else {}
    if order == "fewest":
        seq = sorted(FACTS, key=lambda p: (len(PAIR_DOMAIN[p]["pair_rows"]), p))
    elif order == "laneidx":
        seq = sorted(FACTS, key=lambda p: LANES[p]["lane_index"])
    elif order == "rev":
        seq = sorted(FACTS, key=lambda p: (FACTS[p]["corridor"], FACTS[p]["conn_ref"], FACTS[p]["band"], p), reverse=True)
    elif order == "xasc":
        # CO-143c：带内按 pad-x 升序（西->东）；带间仍按 (corridor,conn_ref,band)。
        # 依据：对间 3W 的 carry 必须从**受约束端**（窄侧）向自由端推进，否则末页被夹死。
        seq = sorted(FACTS, key=lambda p: (FACTS[p]["corridor"], FACTS[p]["conn_ref"], FACTS[p]["band"],
                                          min(FACTS[p]["pad"]["N"][0], FACTS[p]["pad"]["P"][0]), p))
    elif order == "carry":
        # CO-144：**带优先**（(corridor,band) 连续处理）+ 带内 pad-x 升序。
        # 带间次序 = (corridor,band) 规范序；同带跨 conn_ref（J3/J4）连续 ⇒ 共享游标。
        seq = sorted(FACTS, key=lambda p: (FACTS[p]["corridor"], FACTS[p]["band"], FACTS[p]["conn_ref"],
                                          min(FACTS[p]["pad"]["N"][0], FACTS[p]["pad"]["P"][0]), p))
    else:
        seq = sorted(FACTS, key=lambda p: (FACTS[p]["corridor"], FACTS[p]["conn_ref"], FACTS[p]["band"], p))
    global _CARRY_CUR, _CARRY_DIR
    _CARRY_CUR = {}; _CARRY_DIR = {}
    if _CARRY:
        _bg = {}
        for _p in seq:
            _bg.setdefault(_band_key(FACTS[_p]), []).append(_p)
        for _k, _ps in _bg.items():
            if not _band_carry(FACTS[_ps[0]]):
                continue
            _xs = [min(FACTS[_q]["pad"]["N"][0], FACTS[_q]["pad"]["P"][0]) for _q in _ps]
            _CARRY_DIR[_k] = 1 if _xs[-1] >= _xs[0] else -1
    st = Store()
    PDN_SEED = _seed_pdn(st) if _PDN_OBS else {"n_pdn_vias": 0, "n_pdn_segs": 0}
    placed = {}; failed = {}; GEOM = {}
    global ALLOC
    ALLOC = alloc_closed_form() if (rule != "co10" and __import__("os").environ.get("CO10_ALLOC")) else None
    XALLOC = alloc_x() if rule == "co10" else {}
    VER = json.loads((SPEC / "m13_v57_s1_r1_via_verdict_r2.json").read_text())["pages"] if rule == "co10" else {}
    for pid in seq:
        f = FACTS[pid]
        if rule == "co10":
            cand = []
            for pol in ("P", "N"):
                xa = XALLOC[(pid, pol)]
                pts = [c for c in VER[pid][pol]["cands"] if abs(float(c[0]) - xa) < 0.026]
                pts.sort(key=lambda c: (abs(float(c[1]) - f["pad"][pol][1]), float(c[1])))
                cand.append((pol, pts))
            hit = None; reasons = {}
            for ip in range(len(cand[0][1])):
                for jn in range(len(cand[1][1])):
                    px, py = float(cand[0][1][ip][0]), float(cand[0][1][ip][1])
                    nx, ny = float(cand[1][1][jn][0]), float(cand[1][1][jn][1])
                    if math.hypot(px - nx, py - ny) < VV - TOL: continue
                    b = build(f, px, py, nx, ny)
                    if b is None: continue
                    err = check(*b, st, pid)
                    if err is None:
                        hit = (px, py, nx, ny, b); break
                    reasons.setdefault(err[0], err)
                if hit: break
            if hit is None:
                failed[pid] = {"rule": "co10", "xalloc": [XALLOC[(pid, "P")], XALLOC[(pid, "N")]],
                               "reasons": {k: str(v)[:160] for k, v in reasons.items()}}
                if verbose: print("FAIL", pid, failed[pid]["reasons"])
                continue
            px, py, nx, ny, b = hit
            placed[pid] = {"P_via": [px, py], "N_via": [nx, ny], "escape": esc_layer(f),
                           "stub": stub_layer(f), "xalloc": [XALLOC[(pid, "P")], XALLOC[(pid, "N")]]}
            GEOM[pid] = geom_rec(b, f)
            st.add(b[0], b[1], pid)
            if verbose: print("OK  ", pid, esc_layer(f), stub_layer(f), (px, py), (nx, ny))
            continue
        _by = y_bias(f)
        _ck = _band_key(f) if _CARRY else None
        _cdir = _CARRY_DIR.get(_ck, 0) if _CARRY else 0
        if ALLOC:
            _xw = float(__import__("os").environ.get("CO10_XWIN", "0"))
            if _xw > 0:
                _all = PAIR_DOMAIN[pid]["pair_rows"]
                _flt = [r for r in _all if abs(float(r[0]) - f["pad"]["P"][0]) <= _xw
                        and abs(float(r[1]) - f["pad"]["N"][0]) <= _xw]
                if _flt:
                    PAIR_DOMAIN[pid]["pair_rows"] = _flt
            if __import__("os").environ.get("CO10_CORNER"):
                _ly = LANES[pid]["lane_y"]
                _own = np.array([list(f["pad"][q]) + list(f["conn_pad"][q]) for q in ("P", "N")], dtype=float)
                _exm = np.zeros(len(PXA), dtype=bool)
                for _q in ("P", "N"):
                    _exm |= (np.abs(PXA - f["pad"][_q][0]) < 0.02) & (np.abs(PYA - f["pad"][_q][1]) < 0.02)
                    _exm |= (np.abs(PXA - f["conn_pad"][_q][0]) < 0.02) & (np.abs(PYA - f["conn_pad"][_q][1]) < 0.02)
                _all = PAIR_DOMAIN[pid]["pair_rows"]
                _flt = []
                for r in _all:
                    ok = True
                    for _q, _x in (("P", float(r[0])), ("N", float(r[1]))):
                        _cy = _ly + pol_off(f, _q)
                        _g = pad_via_edge(np.array([_x]), np.array([_cy]))[0]
                        _gg = np.where(_exm, 999.0, pad_via_edge(np.array([_x]), np.array([_cy])))[0]
                        if min(_g, _gg) < ESC - TOL:
                            ok = False; break
                    if ok:
                        _flt.append(r)
                if _flt:
                    PAIR_DOMAIN[pid]["pair_rows"] = _flt
            rows = sorted(PAIR_DOMAIN[pid]["pair_rows"],
                          key=lambda r: (abs(float(r[0]) - ALLOC[(pid, "P")][0])
                                         + abs(float(r[1]) - ALLOC[(pid, "N")][0])
                                         + abs(float(r[2]) - ALLOC[(pid, "P")][1])
                                         + abs(float(r[3]) - ALLOC[(pid, "N")][1]),
                                         float(r[0]), float(r[1])))
            rows = rows[:2000] + [r for r in sorted(PAIR_DOMAIN[pid]["pair_rows"],
                                                    key=lambda r: (abs(float(r[2]) - ALLOC[(pid, "P")][1])
                                                                   + abs(float(r[3]) - ALLOC[(pid, "N")][1])))[:400]]
            seen = set(); rows = [r for r in rows if not (tuple(r) in seen or seen.add(tuple(r)))]
        else:
            # CO-144c：carry 带的目标由 carry 游标给出（filter+sort），不再用 _ip3w_targets 的
            # P 前缀目标（其 P=N+VT 与「P/N 不翻转」相悖，会把锚页推离 pad）。非 carry 带照旧。
            _tp = _IP3W_TGT.get(pid) if (_IP3W_TGT and not _cdir) else None
            _bx = _BOFF if f["band"] == "up" else -_BOFF     # CO-205e 竖列分色偏移
            _tx_p = (_tp[1] if _tp else f["pad"]["P"][0]) + _bx
            _tx_n = (_tp[0] if _tp else f["pad"]["N"][0]) + _bx
            rows = sorted(PAIR_DOMAIN[pid]["pair_rows"],
                          key=lambda r: (abs(float(r[0]) - _tx_p) + abs(float(r[1]) - _tx_n)
                                         + abs(float(r[2]) - (f["pad"]["P"][1] + _by))
                                         + abs(float(r[3]) - (f["pad"]["N"][1] + _by)),
                                         float(r[0]), float(r[1])))
        # 带首页（游标未建立）保持**原偏好序**（就近 pad/目标）；其后才按 carry 方向重排。
        # 理由：若首页即取极值列，会把整带锚到窗口外（CO-144 首版 DN7 N→95.6 的教训）。
        if _cdir and _CARRY_CUR.get(_ck) is not None:
            # 稳定排序：正向（西->东）以 max(列 x) 升序；反向以 max(列 x) 降序。
            # 同键保留原偏好序（稳定排序）。
            rows = sorted(rows, key=lambda r: max(float(r[0]), float(r[1])), reverse=(_cdir < 0))
        hit = None; reasons = {}
        _ccur = _CARRY_CUR.get(_ck) if _cdir else None
        _cw = ((max(3.0 * _WBY.get(esc_layer(f), 0.16), VV) if _CARRYALL
                else 3.0 * _WBY.get(esc_layer(f), 0.16))) if _cdir else 0.0
        for r in rows:
            px, nx, py, ny, dd = (float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]))
            if dd < VV - TOL or abs(px - nx) < _XMIN - TOL: continue
            if abs(py - f["pad"]["P"][1]) > YWIN or abs(ny - f["pad"]["N"][1]) > YWIN: continue
            # CO-144b：carry 只搬列**不翻转对向**（P/N 逃逸列相对 pad 的左右次序须保持）
            #   —— 翻转会改变对内走线拓扑（实测 DN7 对向翻转 => L5 SI skew 0.328 > 0.15）。
            if _cdir and (px - nx) * (f["pad"]["P"][0] - f["pad"]["N"][0]) <= 0:
                continue
            if _cdir and _ccur is not None:
                if _cdir > 0 and min(px, nx) - _BEXT < _ccur + _cw - TOL:
                    continue
                if _cdir < 0 and max(px, nx) + _BEXT > _ccur - _cw + TOL:
                    continue
            if _HOLE_GAP > 0:      # L2: 同网钻孔间距 => 逃逸竖段 >= gap（升/降段不得短到 via 钻孔相撞）
                _ly = LANES[pid]["lane_y"]
                if abs(py - (_ly + pol_off(f, "P"))) < _HOLE_GAP - TOL \
                   or abs(ny - (_ly + pol_off(f, "N"))) < _HOLE_GAP - TOL:
                    continue
            b = build(f, px, py, nx, ny)
            if b is None: continue
            err = check(*b, st, pid)
            if err is None:
                hit = (px, py, nx, ny, b); break
            reasons.setdefault(err[0], err)
        if hit is None:
            failed[pid] = {"n_rows_scanned": len(rows), "reasons": {k: str(v)[:200] for k, v in reasons.items()}}
            if verbose: print("FAIL", pid, failed[pid]["reasons"])
            continue
        px, py, nx, ny, b = hit
        placed[pid] = {"P_via": [px, py], "N_via": [nx, ny], "escape": esc_layer(f),
                       "stub": stub_layer(f), "pair_dist": dd,
                       "land": {"P": land_meta(f)["P"], "N": land_meta(f)["N"]}}
        GEOM[pid] = geom_rec(b, f)
        st.add(b[0], b[1], pid)
        if _cdir > 0:
            _CARRY_CUR[_ck] = max(px, nx) + _BEXT
        elif _cdir < 0:
            _CARRY_CUR[_ck] = min(px, nx) - _BEXT
        if verbose: print("OK  ", pid, esc_layer(f), stub_layer(f), (px, py), (nx, ny))
    return {"rule": rule, "order": order, "n_pages": len(FACTS), "n_placed": len(placed), "geom": GEOM,
            "n_failed": len(failed), "placed": placed, "failed": failed,
            "pdn_obstacles": PDN_SEED, "redline_ip3w": _IP3W, "redline_pdn_obs": _PDN_OBS,
            "redline_fan_strat": _STRAT,
            "verdict": "PROBE_PLACED_ALL" if not failed else "PROBE_RESIDUAL"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", choices=["d3", "fan", "co10"], default="d3")
    ap.add_argument("--order", choices=["engine", "fewest", "laneidx", "rev", "xasc", "carry"], default="engine")
    ap.add_argument("--out", default=None)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    res = probe(a.rule, a.order, a.verbose)
    res["producer"] = "k2/tools/p3_v57_co10_west_fan_probe.py"
    res["pad_field_sha256"] = hashlib.sha256((SPEC / "m13_v57_co09_pad_field.json").read_bytes()).hexdigest()
    res["redline"] = "只读探针：未改冻结四源；未改 canonical 图纸"
    out = Path(a.out) if a.out else (SPEC / f"m13_v57_co10_west_fan_probe_{a.rule}_{a.order}.json")
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"CO-10 probe rule={a.rule} order={a.order}: placed {res['n_placed']}/{res['n_pages']} "
          f"failed={sorted(res['failed'])} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
