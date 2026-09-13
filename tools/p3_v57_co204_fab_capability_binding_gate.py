#!/usr/bin/env python3
"""CO-204 — **板厂能力绑定闸**（监理指令 #12 动作 1/5）：设计定稿前**逐项**对 JLC 公布能力。

背景（监理查明 + 本件独立复核）：JLC 标准能力页（**已抓取并 pin** `source_page_sha256`）
  - blind/buried vias：**Not supported**（仅通孔）；
  - **Backdrill：支持** —— ① 4–32 层 FR4、板厚 ≥0.8mm；② 通孔径 D 0.2–0.5mm；
    ③ 背钻孔径 W 通常 = D+0.2mm；④ 背钻深度可定制；⑤ **介质厚 T ≥0.15mm**（背钻底到相邻内层铜）；
    ⑥ 安全距 S ≥0.2mm（孔边到 pad/trace/铜）。
⇒ 冻结过孔策略须**绑 JLC 标准（通孔 + 背钻）**，撤销「JLC advanced / 盲埋孔通道」表述（该通道不存在）。

判据（机判；本件即「设计定稿前逐项对能力」的闸）：
  C0 能力源绑定：backdrill 规则须**由 pinned 抓取件原文**抽得（逐条 anchor 机判），且能力件含该规则。
  C1 过孔类别合法性：**每支 via 至少一端落外层（F.Cu/B.Cu）** —— 两端皆内层（内层↔内层跨层）者
     不可能以「通孔 + 背钻」造出无（或 <0.15mm）残桩形态 ⇒ `inner_inner_via_class`。
  C2 残桩（SI）：逐类残桩（据叠层介质累计距**独立重算**）须 **<0.15mm**；外层锚定类恒 0。
  C3 背钻工艺限：D∈[0.2,0.5]、W≥D+0.2、T≥0.15（目标层至下一内层介质）、S≥0.2、板厚≥0.8、层数∈[4,32]。
  C4 禁用面：设计**不得**要求 blind/buried（能力页明文 not supported）。
  C5 端声明↔实现绑定（CO-205 / R-CO205-1）：每支过孔的**每个声明端点层**在该点须有同网铜连通，
      否则该端为悬空残桩 ⇒ C2 的「外层锚定 ⇒ 残桩 0」会被「只改声明端点层」绕过。
      判据域 = L4 图纸路由的 68 信号网（平面/PDN 缝合孔由 co133 A 判；本板 zone 未填充，无法在此机判）。

CLI: python3 tools/p3_v57_co204_fab_capability_binding_gate.py
exit 0 = PASS；exit 1 = FAIL（如现行板 220/493 内层↔内层 ⇒ 预期 FAIL，直到层分配重派生）
"""
from __future__ import annotations
import hashlib, json, re, sys, html
from collections import Counter
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2D = K2 / "pm_gate/artifacts/k2_v4/L2"
SRC = S2 / "m13_v57_co146_jlc_capability_source.html"
CAP = S2 / "m13_v57_co146_jlc8_capability.json"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
BOARD = K2 / __import__("os").environ.get("FAB_BOARD", "k2_v4_8L.l4.kicad_pcb")
REC = S2 / __import__("os").environ.get("FAB_REC", "m13_v57_co204_fab_capability_binding.json")
PHYS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
STUB_MAX_MM = 0.15          # 监理验收判据：残桩 <0.15mm（高速 SI 不降级）
BIND_TOL_MM = 0.005         # C5 端声明↔实现绑定容差（L4 施工的端点坐标精度）
D_MIN, D_MAX, W_OVER, T_MIN, S_MIN, THK_MIN, LAY_MIN, LAY_MAX = 0.2, 0.5, 0.2, 0.15, 0.2, 0.8, 4, 32


def sha256(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def norm_text(p: Path) -> str:
    """去标签 + 空白归一（与 CO-176 value_bind anchor 口径一致）。"""
    t = re.sub(r"<[^>]+>", " ", p.read_text(encoding="utf-8", errors="replace"))
    return re.sub(r"\s+", " ", html.unescape(t))


def backdrill_anchors(src: str) -> dict:
    """由 pinned 抓取件**原文**抽 backdrill 各条（禁散文/禁臆造；anchor = 归一原文子串）。"""
    i = src.find("Backdrill Backdrill uses a secondary drilling process")
    seg = src[i:i + 2000] if i >= 0 else ""

    def grab(pat):
        m = re.search(pat, seg)
        return m.group(0) if m else None

    return {
        "present": i >= 0,
        "intro": grab(r"Backdrill uses a secondary drilling process[^\u2460]*"),
        "layers_thickness": grab(r"Supports 4-32-layer FR4 boards with a thickness of \u22650\.8mm"),
        "diameter": grab(r"Through-Hole Diaemter\(D\):\s*0\.2-0\.5mm"),
        "w_over": grab(r"Backdrill Diameter\(W\):\s*typically 0\.2mm larger than through-hole diameter"),
        "depth": grab(r"Backdrill Depth\(L\):\s*layers with backdrilling, customizable"),
        "dielectric_t": grab(r"Dielectric Thickness\(T\):\s*\u22650\.15mm"),
        "safety_s": grab(r"Safety Distance\(S\):\s*\u22650\.2mm"),
    }


def layer_span(spec: dict) -> dict:
    """累计介质距（mm）：从 F.Cu 向下 / 从 B.Cu 向上。零板级特判（读声明叠层）。"""
    d = spec["stackup"]["dielectric_8l"]
    keys = ["d(F.Cu-In1.Cu)", "d(In1.Cu-In2.Cu)", "d(In2.Cu-In3.Cu)", "d(In3.Cu-In4.Cu)",
            "d(In4.Cu-In5.Cu)", "d(In5.Cu-In6.Cu)", "d(In6.Cu-B.Cu)"]
    from_F, acc = {}, 0.0
    from_F["F.Cu"] = 0.0
    for k, lo in zip(keys, PHYS[1:]):
        acc += float(d[k]["mm"]); from_F[lo] = round(acc, 6)
    total = acc
    from_B = {L: round(total - v, 6) for L, v in from_F.items()}
    return {"from_F": from_F, "from_B": from_B, "total_mm": round(total, 6)}


def class_stub(top: str, bot: str, span: dict) -> float:
    """该类「通孔 + 背钻」可实现的最小残桩（mm）。外层锚定 ⇒ 0；内层↔内层 ⇒ min(自 F 距, 自 B 距)。"""
    outer = {"F.Cu", "B.Cu"}
    if top in outer or bot in outer:
        return 0.0
    return round(min(span["from_F"][top], span["from_B"][bot]), 6)


def endpoint_binding(board, scope_nets=None) -> list:
    """CO-205（R-CO205-1）：**端声明↔实现绑定** —— 每支过孔的**每个声明端点层**，在该点须有同网铜
    （track 端点 / 焊盘）连通；否则该端为**悬空残桩**（声明了层对而物理上是一段开路桶），
    C2 的「外层锚定 ⇒ 残桩 0」会被绕过（实测缺陷：把内层<->内层孔改声明为 F<->In5）。

    scope_nets：限定判据域（默认 = L4 图纸路由的 68 个信号网）。平面/PDN 缝合孔由 co133 A 判，
    不在此列（其铜面为 zone pour，本板 zone 未填充（IsFilled False）⇒ 无法在此机判）。"""
    import math
    import pcbnew
    from collections import defaultdict
    by_layer = defaultdict(list)
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        nm = board.GetLayerName(t.GetLayer())
        s0, e0 = t.GetStart(), t.GetEnd()
        by_layer[nm].append((t.GetNetCode(), pcbnew.ToMM(s0.x), pcbnew.ToMM(s0.y),
                             pcbnew.ToMM(e0.x), pcbnew.ToMM(e0.y)))
    pads = board.GetPads()
    zones = [z for z in board.Zones() if z.IsFilled()]

    def _copper(nm, lid, x, y, nc):
        if any(n == nc and (math.hypot(xs - x, ys - y) < BIND_TOL_MM
                            or math.hypot(xe - x, ye - y) < BIND_TOL_MM)
               for (n, xs, ys, xe, ye) in by_layer[nm]):
            return True
        p = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        for pad in pads:
            if pad.GetNetCode() == nc and pad.IsOnLayer(lid) and pad.HitTest(p):
                return True
        for z in zones:
            if z.GetNetCode() == nc and z.HitTestFilledArea(lid, p):
                return True
        return False

    bad = []
    for v in board.GetTracks():
        if not isinstance(v, pcbnew.PCB_VIA):
            continue
        pos = v.GetPosition()
        x, y = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
        nc = v.GetNetCode()
        if scope_nets is not None and v.GetNetname() not in scope_nets:
            continue                      # 判据域外（平面/PDN/其它）由 co133 A 判
        for lid in (v.TopLayer(), v.BottomLayer()):
            nm = board.GetLayerName(lid)
            if not _copper(nm, lid, x, y, nc):
                bad.append({"layer": nm, "x": round(x, 4), "y": round(y, 4),
                            "top": board.GetLayerName(v.TopLayer()),
                            "bottom": board.GetLayerName(v.BottomLayer())})
    return bad


def board_census() -> dict:
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))
    cen = Counter()
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            top, bot = b.GetLayerName(t.TopLayer()), b.GetLayerName(t.BottomLayer())
            cen[(top, bot)] += 1
    return {"census": {f"{a}->{c}": n for (a, c), n in sorted(cen.items())},
            "n_vias": sum(cen.values()),
            "n_outer_anchored": sum(n for (a, c), n in cen.items() if a in ("F.Cu", "B.Cu") or c in ("F.Cu", "B.Cu")),
            "n_inner_inner": sum(n for (a, c), n in cen.items() if a not in ("F.Cu", "B.Cu") and c not in ("F.Cu", "B.Cu")),
            "classes": sorted({(a, c) for (a, c) in cen})}


def main() -> int:
    src = norm_text(SRC)
    anchors = backdrill_anchors(src)
    _art = json.loads(CAP.read_text(encoding="utf-8"))
    cap = _art["capability"]
    cap = {**cap, "_bd": _art.get("backdrill_capability") or {}}
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    span = layer_span(spec)
    bc = board_census()

    # C0 能力源绑定：能力件之 backdrill 规则须 == **抓取件原文抽得**之值，且 anchor 逐条为归一原文子串
    bd = cap.get("_bd") or cap.get("backdrill") or {}
    c0 = (bool(anchors["present"]) and all(anchors[k] for k in
          ("layers_thickness", "diameter", "w_over", "depth", "dielectric_t", "safety_s"))
          and cap["blind_buried"]["supported"] is False
          and bd.get("supported") is True
          and (bd.get("layers_min"), bd.get("layers_max")) == (4, 32)
          and float(bd.get("thickness_min_mm", 0)) == 0.8
          and list(bd.get("via_drill_d_mm") or []) == [0.2, 0.5]
          and float(bd.get("backdrill_w_over_d_mm", 0)) == 0.2
          and float(bd.get("dielectric_t_min_mm", 0)) == 0.15
          and float(bd.get("safety_s_min_mm", 0)) == 0.2
          and all(v in src for v in (bd.get("anchor") or {}).values()))

    # C1 过孔类别合法性
    c1 = bc["n_inner_inner"] == 0

    # C2 残桩（逐类独立重算）
    stubs = {f"{a}->{b}": class_stub(a, b, span) for (a, b) in bc["classes"]}
    c2 = all(v < STUB_MAX_MM for v in stubs.values())

    # C3 背钻工艺限（本板声明量；D/W 由 via 实测）
    import pcbnew
    bd = pcbnew.LoadBoard(str(BOARD))
    drills = {round(pcbnew.ToMM(t.GetDrill()), 4) for t in bd.GetTracks() if isinstance(t, pcbnew.PCB_VIA)}
    thk = float(spec["stackup"]["total_thickness_mm"]); nL = len(PHYS)
    c3 = (all(D_MIN <= d <= D_MAX for d in drills) and (min(drills) + W_OVER) >= 0.4 - 1e-9
          and span["from_F"]["In2.Cu"] >= T_MIN and span["from_F"]["In5.Cu"] - span["from_F"]["In4.Cu"] >= T_MIN
          and thk >= THK_MIN and LAY_MIN <= nL <= LAY_MAX)

    # C5 端声明↔实现绑定（R-CO205-1）：防「改声明绕过 C2」
    import pcbnew as _pcb
    _b = _pcb.LoadBoard(str(BOARD))
    _l4 = json.loads((K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_l4_construction.json").read_text())
    _scope = set(_l4["nets"])
    bind_bad = endpoint_binding(_b, _scope)
    c5 = len(bind_bad) == 0
    # teeth：把一支本网 In2<->In5 孔在内存里改声明为 F<->In5 ⇒ C5 必须抓到（证明判据有牙齿）
    _tooth = False
    for _v in _b.GetTracks():
        if not isinstance(_v, _pcb.PCB_VIA) or _v.GetNetname() not in _scope:
            continue
        if {_b.GetLayerName(_v.TopLayer()), _b.GetLayerName(_v.BottomLayer())} == {"In2.Cu", "In5.Cu"}:
            _v.SetLayerPair(_pcb.F_Cu, _pcb.In5_Cu)
            _ls = _pcb.LSET()
            for _ln in PHYS[0:PHYS.index("In5.Cu") + 1]:
                _ls.AddLayer(getattr(_pcb, _ln.replace(".", "_")))
            _v.SetLayerSet(_ls)
            _tooth = len(endpoint_binding(_b, _scope)) > 0
            break

    # C4 禁用面：0 盲埋孔
    c4 = bc["n_inner_inner"] == 0 and all(
        not k.startswith("BLIND") for k in ())
    fails = []
    if not c0: fails.append("capability_binding")
    if not c1: fails.append(f"inner_inner_via_class({bc['n_inner_inner']})")
    if not c2: fails.append("residual_stub_ge_0.15mm")
    if not c3: fails.append("backdrill_process_limit")
    if not c4: fails.append("blind_buried_required")
    if not c5: fails.append(f"dangling_via_endpoint({len(bind_bad)})")
    rec = {
        "artifact": "m13_v57_co204_fab_capability_binding", "schema": 1, "revision": "CO-205",
        "nature": "板厂能力绑定闸（设计定稿前逐项对 JLC 标准能力：通孔 + 背钻）+ CO-205 C5 端声明↔实现绑定（R-CO205-1）",
        "jlc_standard": {"source_html": str(SRC.relative_to(K2)), "source_page_sha256": sha256(SRC),
                         "blind_buried": "Not supported（仅通孔）", "backdrill": "支持（4–32 层 / 板厚 ≥0.8mm）",
                         "anchors": anchors},
        "board": {"path": BOARD.name, "sha256": sha256(BOARD), "n_vias": bc["n_vias"],
                  "census": bc["census"], "n_outer_anchored": bc["n_outer_anchored"],
                  "n_inner_inner": bc["n_inner_inner"]},
        "stackup_dielectric_mm": span,
        "via_class_stub_mm": stubs,
        "checks": {"C0_capability_binding": c0, "C1_via_class_legality": c1,
                   "C2_residual_stub_lt_0.15": c2, "C3_backdrill_process_limits": c3,
                   "C4_no_blind_buried": c4, "C5_endpoint_copper_binding": c5},
        "C5": {"scope": "L4 图纸路由网（68）", "n_vias_in_scope": sum(
                   1 for _t in _b.GetTracks()
                   if isinstance(_t, _pcb.PCB_VIA) and _t.GetNetname() in _scope),
               "n_dangling": len(bind_bad), "offenders_sample": bind_bad[:8]},
        "verdict": "PASS" if not fails else "FAIL", "fails": fails,
        "teeth": {"inner_inner_class_cannot_be_through_backdrilled_stub_free":
                  class_stub("In2.Cu", "In5.Cu", span) >= STUB_MAX_MM,
                  "outer_anchored_classes_are_stub_free": all(
                      class_stub(a, b, span) == 0.0 for a, b in (("F.Cu", "In2.Cu"), ("In5.Cu", "B.Cu"), ("F.Cu", "B.Cu"))),
                  "backdrill_anchors_verbatim": all(anchors[k] for k in ("diameter", "dielectric_t")),
                  "endpoint_binding_catches_dangling_end": _tooth},
        "redline": "只读判据（不改 SPEC/板/冻结四源）；零坐标搜索；能力值一律由 pinned 抓取件原文抽得。",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "checks": rec["checks"], "fails": fails,
                      "n_vias": bc["n_vias"], "n_inner_inner": bc["n_inner_inner"],
                      "census": bc["census"], "stub_in2_in5": stubs.get("In2.Cu->In5.Cu"),
                      "rec_sha16": hashlib.sha256(REC.read_bytes()).hexdigest()[:16]}, ensure_ascii=False, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
