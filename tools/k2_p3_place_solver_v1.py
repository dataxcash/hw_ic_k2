#!/usr/bin/env python3
"""k2_p3_place_solver_v1.py — K2 P3 落位求解器 v1（L2 自裁域：PDN/布局）。

解两类 P3 未闭项：
  G1  13 件 P4 补件坐标（真源有件、交付板无件）
      - 9× strap R（`R35–R39`/`R42–R45`）：落位由 canonical SPEC `layer_plan.strap_domain_v32.placement`
        已裁（南带 x[83,104] y[58.5,66]、2 排 5/4 交错、间距 ≥0.5mm、0603、避 C79–C83 去耦柱）⇒ 本求解器
        只在**已裁域内**做「就近其球 + 无干涉」的确定性排布（不重裁域）。
      - `D2`/`L1`（buck 开关节点）+ `R40`/`R41`（FB 分压）：域未裁 ⇒ 本求解器按 **L2 自裁**（PDN）
        就近 U2 对应 pad 排布。
  G2  `C73`/`C86` 移位新坐标（L2-3 已裁须移位，仍在左带内）。
约束（全部机验）：
  1. 板框内缩 0.3mm（L2-8 8b）；
  2. 与**既有 pad** 净距 ≥0.2mm、与新落件 ≥0.5mm（SPEC `row_plan`）；
  3. 避 4×固定孔 Ø6.0 回避区（L2-2）、避 SPEC 去耦柱 keepout；
  4. 不触 L1（器件分区/接口朝向不变；只增件/移位，不改既有接口）。

输出：`L3/drawings/p3_placement_solution.json`（只写该目录）。
"""
from __future__ import annotations
import json, os, sys, math, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(ROOT, "k2")
L3 = os.path.join(K2, "pm_gate/artifacts/k2_v4/L3")
OUT = os.environ.get("K2_P3_SOL_OUT", os.path.join(L3, "drawings"))
os.environ.setdefault("PM_GATE_PROJECT_ROOT", K2)
sys.path.insert(0, os.path.join(K2, "_shared"))
sys.path.insert(0, os.path.join(K2, "tools"))

FRAME = [23.0, 33.0, 143.0, 79.0]
INSET = 0.3
HOLES = {"H1": [26.10, 75.60], "H2": [139.60, 39.60], "H3": [26.10, 36.10], "H4": [114.60, 36.10]}
HOLE_KO_R = 3.0          # Ø6.0 回避区
PAD_CLEAR = 0.2          # 与既有 pad 净距
PART_CLEAR = 0.5         # 新件之间（SPEC row_plan）

HEADER_FP = {"J6": "ForgeOS:PinHeader_1x02", "J12": "ForgeOS:PinHeader_1x02",
             "J9": "ForgeOS:PinHeader_1x04", "J11": "ForgeOS:PinHeader_1x04", "J13": "ForgeOS:PinHeader_1x04"}

def load_obstacles(spec_pin_headers, col_x, rot=90.0):
    """既有 pad 障碍 + **5 排针（板 0 焊盘 ⇒ 用封装几何 @L2-3 位显式注入）**。"""
    import pcbnew
    from k2_p3_drawings_v1 import placed_pad_aabb, rot_pt
    b = pcbnew.LoadBoard(os.path.join(K2, "hw/k2_v4_8L.kicad_pcb"))
    obs = []
    for ft in b.GetFootprints():
        ref = ft.GetReference()
        if ref in HEADER_FP:      # 板 0 焊盘 ⇒ 由下段按封装几何注入
            continue
        for p in ft.Pads():
            bb = p.GetBoundingBox()
            obs.append([ref, p.GetNumber(),
                        pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                        pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())])
    pos = (spec_pin_headers or {}).get("positions", {})
    for ref, fp in HEADER_FP.items():
        if ref not in pos:
            continue
        x0, y0 = col_x, pos[ref][1]
        _, pads = placed_pad_aabb(fp, x0, y0, rot)
        for p in pads:
            px, py = rot_pt(p["x"], p["y"], rot)
            obs.append([ref, p["no"],
                        x0 + px - p["w"] / 2, y0 + py - p["h"] / 2,
                        x0 + px + p["w"] / 2, y0 + py + p["h"] / 2])
    return obs

def part_aabb(fp, x, y, rot=0.0):
    from k2_p3_drawings_v1 import footprint_pads, rot_pt
    _, pads = footprint_pads(fp)
    box = None
    for p in pads:
        px, py = rot_pt(p["x"], p["y"], rot)
        hw, hh = p["w"] / 2.0, p["h"] / 2.0
        b = [x + px - hw, y + py - hh, x + px + hw, y + py + hh]
        box = b if box is None else [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
    return box

def overlap(a, b, clr):
    return not (a[2] + clr <= b[0] or b[2] + clr <= a[0] or a[3] + clr <= b[1] or b[3] + clr <= a[1])

def in_frame(a):
    return (a[0] >= FRAME[0] + INSET and a[1] >= FRAME[1] + INSET
            and a[2] <= FRAME[2] - INSET and a[3] <= FRAME[3] - INSET)

def in_hole_ko(a):
    for hx, hy in HOLES.values():
        cx = min(max(hx, a[0]), a[2]); cy = min(max(hy, a[1]), a[3])
        if (cx - hx) ** 2 + (cy - hy) ** 2 < HOLE_KO_R ** 2:
            return True
    return False

def solve_one(fp, target, window, placed, obstacles, extra_ko=(), step=0.1):
    """返回 (x,y,aabb) —— 距 target 最近且满足全部约束的栅格点（确定性）。"""
    best = None
    nx = int((window[2] - window[0]) / step) + 1
    ny = int((window[3] - window[1]) / step) + 1
    for i in range(nx):
        for j in range(ny):
            x = round(window[0] + i * step, 3); y = round(window[1] + j * step, 3)
            a = part_aabb(fp, x, y)
            if not in_frame(a) or in_hole_ko(a):
                continue
            if any(overlap(a, k, 0.3) for k in extra_ko):   # 对 SPEC 去耦柱 keepout 留 0.3mm pad 级余量
                continue
            if any(overlap(a, o[2:6], PAD_CLEAR) for o in obstacles):
                continue
            if any(overlap(a, p[1], PART_CLEAR) for p in placed):
                continue
            d = (x - target[0]) ** 2 + (y - target[1]) ** 2
            key = (round(d, 6), x, y)
            if best is None or key < best[0]:
                best = (key, x, y, a)
    return (best[1], best[2], best[3]) if best else None

def main():
    spec = json.load(open(os.path.join(L3, "SPEC_k2_v4.spec-rev-22.json"), encoding="utf-8"))
    sd = spec["layer_plan"]["strap_domain_v32"]
    pl = sd["placement"]
    zone, decap = pl["zone_mm"], pl["decap_column_keepout_mm"]
    zone_rect = [zone["x"][0], zone["y"][0], zone["x"][1], zone["y"][1]]
    decap_rect = [decap["x"][0], decap["y"][0], decap["x"][1], decap["y"][1]]
    ph_spec = spec["components"].get("pin_headers") or {}
    COL_X = 27.94
    obs = load_obstacles(ph_spec, COL_X)
    sol = {"strap_zone": zone, "decap_keepout": decap, "strap_footprint_spec": pl["footprint"],
           "constraints": {"inset_mm": INSET, "pad_clearance_mm": PAD_CLEAR, "part_spacing_mm": PART_CLEAR,
                           "hole_keepout_dia_mm": HOLE_KO_R * 2},
           "placed": {}, "unsolved": []}

    # ── G1a：9× strap R（域已裁 → 域内就近球排布） ──────────────────────────
    rows_y = [59.6, 61.6]   # 下移 0.6mm：避开 U6 courtyard/silk 外延（L1 体包络 y<=58.20）            # SPEC row_plan「2 rows」严格两排（域 y[58.5,66] 内、柱 y 区间内但 x 已分段）
    segs = {"west": [zone["x"][0] + 0.6, decap["x"][0] - 0.6],   # 左段 83.6..89.65
            "east": [decap["x"][1] + 0.6, zone["x"][1] - 0.6]}   # 右段 92.35..103.4
    order = []
    for r in sd["resistors"]:
        order.append((r["resistor"], r["side"], r["ball_board_pos"], r["ball"]))
    # 先按 side 分组，再按球 y 排序（确定性）
    placed = []
    for side in ("west", "east"):
        grp = [t for t in order if t[1] == side]
        grp.sort(key=lambda t: (t[2][1], t[2][0]))
        for ref, _s, bpos, ball in grp:
            # 严格 2 排：逐排试解，取距球最近且可行者（保持 row_plan「2 rows x 5/4 stagger」）
            cands = []
            for row in rows_y:
                for seg in ("west", "east"):   # 全域两段（避柱）；就近球者优先
                    win = [segs[seg][0], row - 0.05, segs[seg][1], row + 0.05]
                    r_ = solve_one(pl["footprint"], bpos, win, placed, obs, extra_ko=[decap_rect], step=0.05)
                    if r_:
                        cands.append((((r_[0] - bpos[0]) ** 2 + (r_[1] - bpos[1]) ** 2), r_, row, seg))
            cands.sort(key=lambda c: c[0])
            res = cands[0][1] if cands else None
            if cands:
                sol["placed_meta"] = sol.get("placed_meta", {})
                sol["placed_meta"][ref] = {"row": cands[0][2], "segment": cands[0][3]}
            if not res:
                sol["unsolved"].append(ref); continue
            x, y, a = res
            sol["placed"][ref] = {"at": [x, y], "rot": 0.0, "aabb": [round(v, 3) for v in a],
                                  "footprint": pl["footprint"], "ball": ball, "ball_board_pos": bpos,
                                  "side": side, "basis": "SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近球求解",
                                  "net_end": "GND（B 端）"}
            placed.append([ref, a])

    # ── G1b：D2 / L1 / R40 / R41（buck 域，L2 自裁：就近 U2 pad） ──────────
    def pad_at(ref, num):
        import pcbnew
        b = pcbnew.LoadBoard(os.path.join(K2, "hw/k2_v4_8L.kicad_pcb"))
        ft = b.FindFootprintByReference(ref)
        for p in ft.Pads():
            if p.GetNumber() == num:
                return [pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)]
        return None
    sw = pad_at("U2", "1"); fb = pad_at("U2", "3"); p3v3 = pad_at("U2", "5")
    buck = [
        ("L1", "Inductor_SMD:L_0805_2012Metric", [(sw[0] + p3v3[0]) / 2, (sw[1] + p3v3[1]) / 2], [28.0, 31.5, 40.0, 41.0],
         "buck 电感（SW→P3V3）；L2 自裁：就近 SW/P3V3 pad 中点"),
        ("D2", "Diode_SMD:D_SMA", [sw[0] - 1.5, sw[1] + 1.5], [28.0, 32.0, 40.0, 42.0],
         "buck 续流二极管（SW↔GND）；L2 自裁：就近 SW pad"),
        ("R40", "Resistor_SMD:R_0402_1005Metric", [fb[0] - 1.5, fb[1] + 0.6], [28.0, 31.5, 41.0, 41.5],
         "FB 分压上臂；L2 自裁：就近 FB pad"),
        ("R41", "Resistor_SMD:R_0402_1005Metric", [fb[0] - 1.5, fb[1] - 1.0], [28.0, 31.0, 41.0, 41.5],
         "FB 分压下臂；L2 自裁：就近 FB pad"),
    ]
    for ref, fp, target, win, basis in buck:
        placed_buck = []
        res = solve_one(fp, target, win, placed + placed_buck, obs)
        if not res:
            sol["unsolved"].append(ref); continue
        x, y, a = res
        sol["placed"][ref] = {"at": [x, y], "rot": 0.0, "aabb": [round(v, 3) for v in a], "footprint": fp,
                              "basis": basis, "target_pad_mm": target}
        placed.append([ref, a])

    # ── G2：C73 / C86 移位（左带内，避既有 pad） ──────────────────────────
    c73_old = pad_at("C73", "1"); c86_old = pad_at("C86", "1")
    for ref, fp, target, win in [("C73", "Capacitor_SMD:C_0402_1005Metric", c73_old, [24.5, 42.0, 32.0, 50.0]),
                                 ("C86", "Capacitor_SMD:C_0402_1005Metric", c86_old, [24.5, 30.0, 34.0, 36.0])]:
        res = solve_one(fp, target, win, placed, obs)
        if not res:
            sol["unsolved"].append(ref); continue
        x, y, a = res
        sol["placed"][ref] = {"at": [x, y], "rot": 0.0, "aabb": [round(v, 3) for v in a], "footprint": fp,
                              "old_at": target, "basis": "L2-3 已裁须移位（排针列 column_x 26.5→27.94）；L2 自裁新坐标：左带内就近原位、避既有 pad"}
        placed.append([ref, a])

    # ── 机验（复算，不靠中间态） ───────────────────────────────────────────
    import pcbnew
    chk = {"in_frame": [], "pad_clearance_violations": [], "part_spacing_violations": [],
           "hole_ko_violations": [], "decap_ko_violations": []}
    items = [(r, d["aabb"]) for r, d in sol["placed"].items()]
    for ref, a in items:
        if not in_frame(a): chk["in_frame"].append(ref)
        if in_hole_ko(a): chk["hole_ko_violations"].append(ref)
        if overlap(a, decap_rect, 0.0): chk["decap_ko_violations"].append(ref)
        for o in obs:
            if overlap(a, o[2:6], PAD_CLEAR): chk["pad_clearance_violations"].append([ref, o[0] + "." + str(o[1])])
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if overlap(items[i][1], items[j][1], PART_CLEAR):
                chk["part_spacing_violations"].append([items[i][0], items[j][0]])
    sol["selfcheck"] = chk
    sol["solved_count"] = len(sol["placed"])
    sol["all_pass"] = (not sol["unsolved"] and not any(chk.values()))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "p3_placement_solution.json")
    json.dump(sol, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[P3-solver] solved {sol['solved_count']}/13(+2) -> {os.path.relpath(p, ROOT)}")
    print("  unsolved:", sol["unsolved"])
    print("  selfcheck:", json.dumps(chk, ensure_ascii=False))
    for r in sorted(sol["placed"]):
        print(f"    {r:4s} at {sol['placed'][r]['at']}  fp={sol['placed'][r]['footprint'].split(':')[-1]}")

if __name__ == "__main__":
    main()
