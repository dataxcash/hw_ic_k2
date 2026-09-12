#!/usr/bin/env python3
"""CO-121：【L2 自裁 · 裁定 + 施加计划】西区 P3V3_AUX In4 承载分配（声明式有限家族机判，零搜索）。

层级裁定（L2，非 L1）：
  《宪法》ch.2：L2 = 物理承载（叠层分配 / **PDN 架构** / 走廊分配 / 过孔策略 / 等长窗口 / 热机械），
  L2 **裁判标准**含『参考平面 / PDN 压降』；L1 = 板级拓扑（器件分区 / 接口朝向 / 信号流向 / **电源域划分**）。
  冻结 L1 实测内容 = 域集合 {P3V3, P3V3_AUX, MCU_VDD}（`L1_TOPOLOGY_v2.0.md` §电源域 = 结转 v1.0；v1.0 原文仅列该三网）
  + 粗分区（`pd.power_partition`：东 = P3V3 / 西 = P3V3_AUX_MCU_VDD）。本件**不改域集合、不改粗分区**、不改层数/平面数
  ⇒ 项目判据（CO-117 写入 SPEC `in4_band_copper_allocation_v1.level_basis`；先例 CO-74）⇒ **L2**。
  ⇒ 更正 boundary v1.82 附二 ② 的『L1 待裁』归口（过高归口；同类更正先例 = CO-117 更正 CO-115/CO-116）。
  佐证：CO-95 本身已把该冲突登记为 `plane_reachability_status.unresolved`『区域归属冲突，须裁』（待裁 ≠ 已判 L1）。

分配（零搜索：**声明式有限家族**，非求解器 —— 同 CO-92/CO-94 技术）：
  目标 = P3V3_AUX 3 个声明 via（C90.1 / U1.15 / R1.2）。
  净距（闭式，取自冻结 `drc_rules.json`，非臆造）：
    P3V3_AUX 属 POWER(0.2)。铜/铜 required = max(POWER 0.2, foreign, board_min 0.1) = 0.2
    ⇒ 区域边到异网 via 圆心 ≥ required + via_od/2 = 0.2 + 0.175 = **0.375**
    孔/铜 required = min_hole_clearance 0.25 + drill_r(0.2/2) = 0.35 < 0.375 ⇒ 铜规则为约束
  ⇒ 统一判据：AUX 区域边到**任一异网 via 圆心** ≥ 0.375（含 GND，In4 无 GND 区但其孔/环仍需净距）。
  家族 = 有限候选（每条边 = 声明 via 坐标 ± 声明偏移 {0.5, 0.7}），逐一机判：
    (a) 覆盖 3 个 P3V3_AUX via；(b) 异网 via 净距 ≥ 0.375；(c) **MCU_VDD 连续性**（西区 − AUX − 0.2 moat 仍单连通）；
    (d) P3V3_AUX 三 via 互相连通。
  牙齿（负控）：K4 贯通全高候选必 FAIL(c)；K5 缺一 via 的候选必 FAIL(a)。
只读 SPEC/板/冻结源；本件**不改 SPEC、不改板、不重基线**（施加 = 后继 CO-122：SPEC rev-16 + 全链 + 全闸 + 非执行者复评）。
CLI: python3 tools/p3_v57_co121_west_aux_allocation_ruling.py
"""
from __future__ import annotations
import hashlib, json
from collections import deque
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-15.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
REC = STEP2 / "m13_v57_co121_west_aux_allocation_ruling.json"
CARD = STEP2 / "m13_v57_CO121_west_aux_allocation_ruling.md"
POWER_CLR, LOW_CLR, BOARD_MIN, MIN_HOLE = 0.2, 0.1, 0.1, 0.25
VIA_OD, DRILL = 0.35, 0.2
MOAT, EPS = 0.2, 1e-9
MERGE_MIN = 0.3       # 声明最小可制造搭接深度（块↔带↔柱↔臂；防「1µm 假连通」）
DESIGN_MARGIN = 0.1   # 声明设计余量（绕行侧额外外置）：避免「贴死 required 的 0 余量」= CO-94 family-limit 命中
X_WEST_MAX = 58.0


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def netclass(net: str) -> str:
    for pre in ("P3V3", "MCU_", "VREG", "PWR_5V"):
        if net.startswith(pre):
            return "POWER"
    return "LOW_SPEED"


def req_to_via(foreign_net: str) -> float:
    """AUX 区域铜边 → 异网 via 圆心 的最小距离（闭式，取自冻结 rules）。"""
    clr = max(POWER_CLR, LOW_CLR if netclass(foreign_net) == "LOW_SPEED" else POWER_CLR, BOARD_MIN)
    return round(max(clr + VIA_OD / 2, MIN_HOLE + DRILL / 2), 6)


def pt_rect_dist(p, r) -> float:
    dx = max(r[0] - p[0], 0.0, p[0] - r[2])
    dy = max(r[1] - p[1], 0.0, p[1] - r[3])
    return (dx * dx + dy * dy) ** 0.5


def dist_to_rects(p, rects) -> float:
    return min(pt_rect_dist(p, r) for r in rects)


def in_rect(p, r, strict=True) -> bool:
    e = EPS if strict else -EPS
    return r[0] - e <= p[0] <= r[2] + e and r[1] - e <= p[1] <= r[3] + e


def load():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    zd = spec["pd"]["zone_defs"]
    entries = zd["power_pad_connect"]["entries"]
    zs = zd["power_zones"]
    west = next(z for z in zs if z["zone"] == "MCU_VDD_WEST")
    poly = west["polygon"]
    zone = (min(p[0] for p in poly), min(p[1] for p in poly),
            max(p[0] for p in poly), max(p[1] for p in poly))
    targets = {f"{e['ref']}.{e['pad']}": tuple(e["via_pos"])
               for e in entries if e["net"] == "P3V3_AUX" and e["via_pos"][0] < X_WEST_MAX}
    mcu = {f"{e['ref']}.{e['pad']}": tuple(e["via_pos"])
           for e in entries if e["net"] == "MCU_VDD" and e["via_pos"][0] < X_WEST_MAX}
    foreign = {}
    for e in entries:
        if e["net"] == "P3V3_AUX":
            continue
        foreign[f"{e['ref']}.{e['pad']}({e['net']})"] = (tuple(e["via_pos"]), e["net"])
    for z in zs:                       # 桥区声明 via（同 CO-118 口径）
        for i, v in enumerate(z.get("vias") or []):
            if z["net"] == "P3V3_AUX":
                continue
            foreign[f"{z['zone']}#v{i}({z['net']})"] = (tuple(v["pos"]), z["net"])
    return spec, rules, zone, targets, mcu, foreign


def build_family(t, hw):
    """声明式有限家族：每条边 = 声明 via 坐标 ± 声明偏移 hw。"""
    c90, u115, r12 = t["C90.1"], t["U1.15"], t["R1.2"]
    def sq(p):  return (p[0] - hw, p[1] - hw, p[0] + hw, p[1] + hw)
    band = (min(c90[0], u115[0]) - hw, min(c90[1], u115[1]) - hw,
            max(c90[0], u115[0]) + hw, max(c90[1], u115[1]) + hw)
    band_e = (band[0], band[1], max(band[2], r12[0] + hw), band[3])
    conn = (r12[0] - hw, r12[1] - hw, r12[0] + hw, band[3])
    return {
        f"K0_islands_hw{hw}": [sq(c90), sq(u115), sq(r12)],
        f"K1_band+island_hw{hw}": [band, sq(r12)],
        f"K2_Lshape_hw{hw}": [band_e, conn],
    }


def judge(rects, zone, targets, mcu, foreign, moat=MOAT):
    """机判 (a) 覆盖 (b) 净距 (c) MCU_VDD 连续性 (d) AUX 连通性。"""
    f = {"a_coverage": [], "b_clearance": [], "c_mcu_continuity": False, "d_aux_connectivity": False}
    for name, p in targets.items():
        if not any(in_rect(p, r) for r in rects):
            f["a_coverage"].append(f"{name} 未被覆盖")
    worst = None
    for name, (p, net) in foreign.items():
        d, need = dist_to_rects(p, rects), req_to_via(net)
        if d < need - EPS:
            f["b_clearance"].append(f"{name} d={d:.3f} < {need:.3f}")
        if worst is None or d - need < worst[1]:
            worst = (name, d - need)
    # 网格（坐标仅取自声明源：区域边 ± moat、zone 边、via 坐标）
    xs, ys = set(), set()
    for r in rects:
        for v in (r[0], r[2]):
            xs.update((v - moat, v, v + moat))
        for v in (r[1], r[3]):
            ys.update((v - moat, v, v + moat))
    xs.update((zone[0], zone[2])); ys.update((zone[1], zone[3]))
    for p in list(targets.values()) + list(mcu.values()):
        xs.add(p[0]); ys.add(p[1])
    xs, ys = sorted(xs), sorted(ys)
    nx, ny = len(xs) - 1, len(ys) - 1
    cls = {}
    for i in range(nx):
        for j in range(ny):
            c = ((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2)
            if not in_rect(c, zone):
                continue
            d = dist_to_rects(c, rects)
            cls[(i, j)] = "AUX" if d <= EPS else ("MOAT" if d < moat - EPS else "FREE")

    def comps(kind):
        seen, out = set(), []
        for k, v in cls.items():
            if v != kind or k in seen:
                continue
            q, cur = deque([k]), []
            seen.add(k)
            while q:
                i, j = q.popleft()
                cur.append((i, j))
                for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                    if cls.get(n) == kind and n not in seen:
                        seen.add(n); q.append(n)
            out.append(cur)
        return out

    def cell_of(p):
        for i in range(nx):
            if xs[i] <= p[0] <= xs[i + 1]:
                for j in range(ny):
                    if ys[j] <= p[1] <= ys[j + 1]:
                        return (i, j)
        return None

    aux = comps("AUX"); free = comps("FREE")
    aux_big = max(aux, key=len) if aux else []
    aux_set = set(aux_big)
    f["d_aux_connectivity"] = all(cell_of(p) in aux_set for p in targets.values())
    free_big = set(max(free, key=len)) if free else set()
    f["c_mcu_continuity"] = all(cell_of(p) in free_big for p in mcu.values())
    f["n_aux_cells"] = sum(len(c) for c in aux)
    f["n_free_components"] = len(free)
    f["worst_margin"] = {"via": worst[0], "margin_mm": round(worst[1], 4)} if worst else None
    # (e) 可制造搭接：连通必须由「面积搭接深度 ≥ MERGE_MIN」的边承担（排除 1µm 假连通）
    n = len(rects)
    edges = {}
    for i in range(n):
        for j in range(i + 1, n):
            a, b = rects[i], rects[j]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > EPS and oy > EPS:
                edges[(i, j)] = min(ox, oy)
    good = {k for k, d in edges.items() if d >= MERGE_MIN - EPS}
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i, j in good:
        parent[find(i)] = find(j)
    tgt_idx = [i for i, r in enumerate(rects) if any(in_rect(p, r) for p in targets.values())]
    roots = {find(i) for i in tgt_idx}
    f["e_manufacturable_merge"] = len(roots) == 1 and bool(tgt_idx)
    f["min_merge_depth_mm"] = round(min(edges.values()), 4) if edges else None
    f["ok"] = ((not f["a_coverage"]) and (not f["b_clearance"]) and f["c_mcu_continuity"]
               and f["d_aux_connectivity"] and f["e_manufacturable_merge"])
    return f


def family(t):
    """声明式有限家族（系统性网格，**无求解器**）：连接带所在侧 × 带高 × 柱内缩 × 柱位声明偏移。

    构造规则（全部由声明坐标 + 冻结净距闭式派生）：
      块 = target via ± 声明外扩 0.5；
      带 = 沿 target 行的三种声明侧：direct（行中）/ above（y_max+0.375）/ below（y_min−0.375）× 带高 h ∈ {0.5,0.7}；
      柱 = R1.2 via 的声明偏移位 cx ∈ {0, ±(0.375+cw)}（**按声明序**，用于绕开同 x 的异网 via）× 内缩 cw ∈ {0.3,0.2}；
      臂 = 在 R1.2 行 y 上连接 R1.2 块与柱（保证连通，且不贴近任何异网 via）。
    取用规则 = **声明序取首个四测全过者**；全不过 ⇒ 显式 blocked（不放宽阈值；同 CO-92/CO-100 palette 语义）。
    """
    c90, u115, r12 = t["C90.1"], t["U1.15"], t["R1.2"]
    req = req_to_via("MCU_VDD")
    B = 0.5
    ylo, yhi = min(c90[1], u115[1]), max(c90[1], u115[1])
    xlo, xhi = min(c90[0], u115[0]), max(c90[0], u115[0])

    out = {}
    for cw in (0.3, 0.2):
        out[f"K0_islands_cw{cw}"] = [(c90[0] - B, c90[1] - B, c90[0] + B, c90[1] + B),
                                     (u115[0] - B, u115[1] - B, u115[0] + B, u115[1] + B),
                                     (r12[0] - B, r12[1] - B, r12[0] + B, r12[1] + B)]
        for off in (0.0, req + DESIGN_MARGIN + cw, -(req + DESIGN_MARGIN + cw)):
            cx = r12[0] + off
            for side in ("direct", "below", "above"):
                for h in (0.5, 0.7):
                    half = h / 2.0
                    off_side = DESIGN_MARGIN if side != "direct" else 0.0
                    yc = ((ylo + yhi) / 2.0 if side == "direct"
                          else (yhi + req + off_side + half if side == "above"
                                else ylo - req - off_side - half))
                    b_top = yc + half
                    # 块外扩 = 声明 0.5 与「到带的必要重叠」取大（闭式派生，非调参）
                    bb = max(B, yhi - b_top + MERGE_MIN)
                    def blk(pt, w=bb):
                        return (pt[0] - w, pt[1] - w, pt[0] + w, pt[1] + w)
                    br = blk(r12)
                    col = (cx - cw, r12[1] - B, cx + cw, b_top)
                    arm = (min(br[0], col[0]), r12[1] - B, max(br[2], col[2]), r12[1] + B)
                    band = (xlo - bb, yc - half, max(xhi + bb, col[2]), b_top)
                    out[f"K1_{side}_h{h}_cw{cw}_off{off:+.3f}"] = [blk(c90), blk(u115), band, br, arm, col]
    # K6 牙齿：块仅「贴合」带（搭接深度 0）⇒ 必须 FAIL (e) 可制造搭接（CO-121.1 修复前缺陷类）
    h6, cw6 = 0.5, 0.2
    off6 = req + DESIGN_MARGIN + cw6
    half6 = h6 / 2.0
    b_top6 = ylo - req - DESIGN_MARGIN - half6 + half6
    bb6 = yhi - b_top6
    cx6 = r12[0] + off6

    def blk6(pt, w=bb6):
        return (pt[0] - w, pt[1] - w, pt[0] + w, pt[1] + w)

    br6 = blk6(r12)
    col6 = (cx6 - cw6, r12[1] - B, cx6 + cw6, b_top6)
    arm6 = (min(br6[0], col6[0]), r12[1] - B, max(br6[2], col6[2]), r12[1] + B)
    band6 = (xlo - bb6, b_top6 - h6, max(xhi + bb6, col6[2]), b_top6)
    out["K6_thin_merge_NEGCTRL"] = [blk6(c90), blk6(u115), band6, br6, arm6, col6]
    out["K4_fullheight_NEGCTRL"] = [(c90[0] - B, 33.3, r12[0] + B, 78.7)]
    out["K5_missing_U1.15_NEGCTRL"] = [(c90[0] - B, c90[1] - B, c90[0] + B, c90[1] + B),
                                        (r12[0] - B, r12[1] - B, r12[0] + B, r12[1] + B)]
    return out


def main() -> int:
    spec, rules, zone, targets, mcu, foreign = load()
    fam = family(targets)
    # 负控（牙齿）已由 family() 声明：K4 贯通全高（必破 MCU_VDD 连续）；K5 缺 U1.15（必破覆盖）
    t = targets
    res = {k: judge(v, zone, targets, mcu, foreign) for k, v in fam.items()}
    cands = {k: v for k, v in res.items() if not k.endswith("NEGCTRL")}
    fea = sorted([k for k, v in cands.items() if v["ok"]])
    teeth = {"K4_fullheight_NEGCTRL": res["K4_fullheight_NEGCTRL"],
             "K5_missing_U1.15_NEGCTRL": res["K5_missing_U1.15_NEGCTRL"],
             "K6_thin_merge_NEGCTRL": res["K6_thin_merge_NEGCTRL"]}
    t_ok = {"K6": not teeth["K6_thin_merge_NEGCTRL"]["e_manufacturable_merge"],
            "K4": not teeth["K4_fullheight_NEGCTRL"]["ok"]
            and not teeth["K4_fullheight_NEGCTRL"]["c_mcu_continuity"],
            "K5": not teeth["K5_missing_U1.15_NEGCTRL"]["ok"]
            and bool(teeth["K5_missing_U1.15_NEGCTRL"]["a_coverage"])}
    verdict = "FEASIBLE_WITHIN_DECLARED_FAMILY" if fea else "NOT_FEASIBLE_WITHIN_DECLARED_FAMILY"
    rec = {
        "artifact": "m13_v57_co121_west_aux_allocation_ruling",
        "schema": 1,
        "nature": "L2 自裁 · 裁定（+ 施加计划）：西区 P3V3_AUX In4 承载归属分配",
        "level": {
            "ruling": "L2",
            "basis": "《宪法》ch.2：L2=PDN 架构/走廊分配，L2 裁判标准含『参考平面』；冻结 L1=域集合+粗分区，本件二者不变 ⇒ L2（先例 CO-74；判据同 CO-117 level_basis）",
            "supersedes": "boundary v1.82 附二 ②『L1 待裁』归口（过高）",
        },
        "inputs": {
            "spec": str(SPEC.relative_to(K2)), "spec_sha16": s16(SPEC),
            "rules_sha16": s16(RULES),
            "co95_flag": "plane_reachability_status.unresolved[P3V3_AUX]『区域归属冲突，须裁』",
        },
        "clearance": {
            "derivation": "冻结 drc_rules.json：铜/铜 required=max(netclass,board_min)，P3V3_AUX=POWER 0.2；"
                          "区域边→异网 via 圆心 ≥ required + via_od/2 = 0.375；"
                          "孔/铜 = min_hole_clearance 0.25 + drill_r 0.1 = 0.35 < 0.375 ⇒ 铜规则约束",
            "required_mm": req_to_via("MCU_VDD"), "uniform": True,
            "note": "P3V3_AUX 自身 POWER ⇒ 对任何异网 required 均为 0.2 ⇒ 统一 0.375（含 GND：In4 无 GND 区，但其孔/环需净距）",
        },
        "zone": {"name": "MCU_VDD_WEST", "rect": [round(v, 3) for v in zone]},
        "targets": {k: list(v) for k, v in targets.items()},
        "mcu_vdd_vias_west": {k: list(v) for k, v in mcu.items()},
        "foreign_vias_n": len(foreign),
        "family": {k: [[round(c, 3) for c in r] for r in v] for k, v in fam.items()},
        "family_results": res,
        "feasible_candidates": fea,
        "teeth": {"negative_controls": t_ok, "detail": teeth},
        "verdict": verdict,
        "chosen": fea[0] if fea else None,
        "declared_design_margin_mm": DESIGN_MARGIN,
        "merge_min_mm": MERGE_MIN,
        "zero_margin_note": "若无声明余量（m=0），绕行带顶正好 = required（余量 0.000）= CO-94 family-limit 命中；本件按声明余量 0.1 施加，避免贴死阈值",
        "apply_plan_co122": {
            "scope": "SPEC rev-16（新增 `in4_west_aux_allocation_v1` + P3V3_AUX 由 unresolved → resolved_by_co121）+ 全链重基线",
            "spec_keys": [".spec_version", ".pd.zone_defs.in4_west_aux_allocation_v1",
                          ".pd.zone_defs.plane_reachability_status.unresolved",
                          ".pd.zone_defs.plane_reachability_status.resolved_by_co121"],
            "chain_tool_coord_updates": ["p3_v57_w3_constructive.py (F['spec'] + FROZEN_SHA['spec'])",
                                         "p3_v57_w3_constructive_validator_v2.py",
                                         "co77/co78/co81/co84/co91/co92/co95/co98/co99/co102/co104/co105/co106/co118"],
            "must_rerun": "全链 G4→G7 + 全部回归闸 + PDN 闸（§7 复现命令）",
            "board_must_stay": s16(K2 / "k2_v4_8L.kicad_pcb"),
            "review_debt": "非执行者半程复评（另一会话，禁自评）",
        },
        "redline": "本件只读；未改 SPEC/板/阈值/冻结源；零坐标搜索（有限声明家族，无求解器）；不改历史工件",
        "board_sha16": s16(K2 / "k2_v4_8L.kicad_pcb"),
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [
        "# CO-121 — L2 自裁 · 裁定：西区 P3V3_AUX In4 承载归属（+ 施加计划）",
        "",
        f"- 判定层级：**L2**（PDN 架构/走廊分配；冻结 L1 的域集合与粗分区均不变）",
        f"- 更正：boundary v1.82 附二 ②『L1 待裁』归口 = 过高归口",
        f"- 机判 verdict：**{verdict}**",
        f"- 净距判据：区域边 → 异网 via 圆心 ≥ **{req_to_via('MCU_VDD')}** mm（闭式取自冻结 drc_rules）",
        f"- 可制造搭接判据：块↔带↔柱↔臂 面积搭接深度 ≥ **{MERGE_MIN}** mm",
        f"- 可行候选：{fea if fea else '无'}",
        f"- 牙齿：{t_ok}",
        "",
        "## 家族机判（(a) 覆盖 / (b) 净距 / (c) MCU_VDD 连续 / (d) AUX 连通）",
        "",
        "| 候选 | a | b | c | d | ok |",
        "|---|---|---|---|---|---|",
    ]
    for k, v in res.items():
        lines.append(f"| {k} | {'PASS' if not v['a_coverage'] else 'FAIL'} | "
                     f"{'PASS' if not v['b_clearance'] else 'FAIL'} | "
                     f"{'PASS' if v['c_mcu_continuity'] else 'FAIL'} | "
                     f"{'PASS' if v['d_aux_connectivity'] else 'FAIL'} | {'OK' if v['ok'] else 'NG'} |")
    lines += ["", "## 施加计划（后继 CO-122，本件未施加）", "",
              "SPEC rev-16 + 全链 G4→G7 + 全部回归闸 + PDN 闸 + 非执行者复评。本件零 SPEC/板改动、不重基线。"]
    CARD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "feasible": fea, "teeth": t_ok,
                      "worst_margin": res.get(fea[0], {}).get("worst_margin") if fea else None,
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0 if (fea and all(t_ok.values())) else 1


if __name__ == "__main__":
    raise SystemExit(main())
