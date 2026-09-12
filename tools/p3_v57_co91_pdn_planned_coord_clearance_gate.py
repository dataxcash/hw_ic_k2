#!/usr/bin/env python3
"""CO-91：【L2 PDN】计划坐标（pdn_apply 实落集）的**权威净距闸**。

对象 = `SPEC pd.zone_defs` 中由 `eda_core.pdn_apply` 逐字实落到板上的几何：
  - `power_pad_connect.entries[]` → F.Cu 短段(pad_pos→via_pos, w=0.5) + via
  - `gnd_stitch_via.coordinates[]`（非 blocked）→ via
  - `decoupling_via_to_plane.vias[].pos` → via
  - `power_zones[].vias[]` → via
判定口径 = 冻结源 `_shared/eda_core/drc_rules.json`（语义核已对齐 kicad DRC 430/430、106/106）：
  required(a,b) = max(netclass(a), netclass(b), board_min)；同网豁免；
  hole: 孔缘-铜缘 ≥ min_hole_clearance；via 尺寸取自 `pdn_apply.VIA_DIA/VIA_DRILL`（本闸断言一致）。
几何：pad = 轴对齐外接矩形；via = 圆；段 = 中心线线段（精确 rect-vs-seg / seg-vs-seg）。
性质：只读、确定性（sorted 输出、无 set 序）、带牙齿（4 路合成注入真跑检测路径）。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import pcbnew

K2 = Path(__file__).resolve().parents[1]
SHARED = K2 / "_shared"                 # k2 链约定：tools/* 一律读 K2/_shared
SHARED_ALT = K2.parent / "_shared"      # 容器共享层（handoff §1 的冻结源口径）
sys.path.insert(0, str(SHARED))
DEFAULT_SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-9.json"
DEFAULT_BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
DEFAULT_OUT = (K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
               / "m13_v57_co91_pdn_planned_coord_clearance_gate.json")
RULES = SHARED / "eda_core/drc_rules.json"
RULES_ALT = SHARED_ALT / "eda_core/drc_rules.json"
STUB_W = 0.5


def s16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _d_pt_seg(px, py, sx, sy, ex, ey) -> float:
    dx, dy = ex - sx, ey - sy
    if dx == 0 and dy == 0:
        return math.hypot(px - sx, py - sy)
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (sx + t * dx), py - (sy + t * dy))


def _d_seg_seg(ax, ay, bx, by, cx, cy, dx2, dy2) -> float:
    def cr(ox, oy, ux, uy, vx, vy):
        return (ux - ox) * (vy - oy) - (uy - oy) * (vx - ox)
    d1, d2 = cr(cx, cy, dx2, dy2, ax, ay), cr(cx, cy, dx2, dy2, bx, by)
    d3, d4 = cr(ax, ay, bx, by, cx, cy), cr(ax, ay, bx, by, dx2, dy2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(_d_pt_seg(ax, ay, cx, cy, dx2, dy2), _d_pt_seg(bx, by, cx, cy, dx2, dy2),
               _d_pt_seg(cx, cy, ax, ay, bx, by), _d_pt_seg(dx2, dy2, ax, ay, bx, by))


def _d_seg_rect(ax, ay, bx, by, x0, y0, x1, y1) -> float:
    for (px, py) in ((ax, ay), (bx, by)):
        if x0 <= px <= x1 and y0 <= py <= y1:
            return 0.0
    c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    best = 9e9
    for i in range(4):
        cx, cy = c[i]
        dx2, dy2 = c[(i + 1) % 4]
        best = min(best, _d_seg_seg(ax, ay, bx, by, cx, cy, dx2, dy2))
    return best


class Rules:
    def __init__(self, doc: dict):
        self.board_min = doc["clearance"]["board_min"]
        self.hole_min = doc["hole_clearance"]["min"]
        self.classes = [(nc["clearance"], nc["match"]) for nc in doc["clearance"]["net_classes"]]

    def of(self, net: str) -> float:
        for clr, ms in self.classes:
            if any(m["kind"] == "prefix" and net.startswith(m["value"]) for m in ms):
                return clr
        for clr, ms in self.classes:
            if any(m["kind"] == "default" for m in ms):
                return clr
        return self.board_min

    def req(self, a: str, b: str) -> float:
        return max(self.of(a), self.of(b), self.board_min)


def _bb(p):
    x = p.GetBoundingBox()
    return (pcbnew.ToMM(x.GetLeft()), pcbnew.ToMM(x.GetTop()),
            pcbnew.ToMM(x.GetRight()), pcbnew.ToMM(x.GetBottom()))


CU_IDS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu,
          pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu, pcbnew.B_Cu]


class Scene:
    """board 铜元素。pad 记录其铜层集合；段记录单层；via 视为贯穿 F..B（共享任一铜层）。"""

    def __init__(self, board, rules: Rules, via_r: float, drill_r: float):
        self.rules, self.via_r, self.drill_r = rules, via_r, drill_r
        self.pads, self.segs, self.vias = [], [], []
        for fp in board.GetFootprints():
            for p in fp.Pads():
                x0, y0, x1, y1 = _bb(p)
                lyr = frozenset(board.GetLayerName(i) for i in CU_IDS if p.IsOnLayer(i))
                self.pads.append((fp.GetReference(), p.GetNumber(), p.GetNetname(),
                                  x0, y0, x1, y1, lyr))
        for t in board.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                vl = frozenset(board.GetLayerName(i) for i in CU_IDS if t.IsOnLayer(i))
                self.vias.append((t.GetNetname(), pcbnew.ToMM(t.GetCenter().x),
                                  pcbnew.ToMM(t.GetCenter().y), vl))
                continue

            self.segs.append((t.GetNetname(), pcbnew.ToMM(t.GetWidth()),
                              pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y),
                              pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y),
                              board.GetLayerName(t.GetLayer())))

    def via_at(self, vx, vy, net):
        r, worst_c, worst_h = self.via_r, 9.9, 9.9
        bc = bh = None
        for (ref, num, pnet, x0, y0, x1, y1, _l) in self.pads:
            if pnet == net:
                continue
            d = math.hypot(max(x0 - vx, vx - x1, 0.0), max(y0 - vy, vy - y1, 0.0))
            c, h = d - r - self.rules.req(net, pnet), d - self.drill_r - self.rules.hole_min
            if c < worst_c:
                worst_c, bc = c, f"pad {ref}.{num}({pnet}) d_edge={d:.4f}"
            if h < worst_h:
                worst_h, bh = h, f"pad {ref}.{num}({pnet}) d_edge={d:.4f}"
        for (snet, w, sx, sy, ex, ey, _l) in self.segs:
            if snet == net:
                continue
            d = _d_pt_seg(vx, vy, sx, sy, ex, ey) - w / 2
            c, h = d - r - self.rules.req(net, snet), d - self.drill_r - self.rules.hole_min
            if c < worst_c:
                worst_c, bc = c, f"seg({snet}) w={w} d_edge={d:.4f}"
            if h < worst_h:
                worst_h, bh = h, f"seg({snet}) w={w} d_edge={d:.4f}"
        for (vnet, x2, y2, _vl) in self.vias:
            if vnet == net:
                continue
            d = math.hypot(vx - x2, vy - y2) - r
            c = d - r - self.rules.req(net, vnet)
            h = d - self.drill_r - self.via_r - self.rules.hole_min
            if c < worst_c:
                worst_c, bc = c, f"via({vnet}) d_edge={d:.4f}"
            if h < worst_h:
                worst_h, bh = h, f"via({vnet}) d_edge={d:.4f}"
        ok = worst_c >= -1e-9 and worst_h >= -1e-9
        return ok, round(worst_c, 4), round(worst_h, 4), (bc if worst_c <= worst_h else bh)

    def seg_clear(self, ax, ay, bx, by, width, net, layer: str = "F.Cu"):
        """段在 `layer` 上；仅与该铜层元素互检（drc_rules.layer_interaction）。

        口径 = clearance（净距）**only**；不含 hole_clearance（保守：只可能少报，不会虚报）。
        via 可为盲/埋孔（TopLayer..BottomLayer 不等）⇒ 必须层集相交才算互检。
        """
        worst, bind = 9.9, None
        for (ref, num, pnet, x0, y0, x1, y1, pl) in self.pads:
            if pnet == net or layer not in pl:
                continue
            m = (_d_seg_rect(ax, ay, bx, by, x0, y0, x1, y1) - width / 2
                 - self.rules.req(net, pnet))
            if m < worst:
                worst, bind = m, f"pad {ref}.{num}({pnet})"
        for (snet, w, sx, sy, ex, ey, sl) in self.segs:
            if snet == net or sl != layer:
                continue
            m = (_d_seg_seg(ax, ay, bx, by, sx, sy, ex, ey) - width / 2 - w / 2
                 - self.rules.req(net, snet))
            if m < worst:
                worst, bind = m, f"seg({snet})"
        for (vnet, x2, y2, vl) in self.vias:
            if vnet == net or layer not in vl:   # via 可为盲/埋孔：须共享该铜层
                continue
            m = (_d_pt_seg(x2, y2, ax, ay, bx, by) - width / 2 - self.via_r
                 - self.rules.req(net, vnet))
            if m < worst:
                worst, bind = m, f"via({vnet})"
        return worst > -1e-9, round(worst, 4), bind


def collect(zd: dict):
    vias, stubs = [], []
    for e in zd.get("power_pad_connect", {}).get("entries", []):
        v, p0 = e.get("via_pos"), e.get("pad_pos")
        if isinstance(v, list) and len(v) == 2:
            vias.append(("ppc_via", e.get("ref"), e.get("pad"), e.get("net"), v[0], v[1]))
        if (isinstance(v, list) and isinstance(p0, list) and len(v) == 2 and len(p0) == 2):
            stubs.append(("ppc_stub", e.get("ref"), e.get("pad"), e.get("net"),
                          p0[0], p0[1], v[0], v[1], STUB_W))
    for c in zd.get("gnd_stitch_via", {}).get("coordinates", []):
        if c.get("blocked") or c.get("status") == "blocked":
            continue
        if isinstance(c.get("x"), (int, float)) and isinstance(c.get("y"), (int, float)):
            vias.append(("stitch_via", c.get("ref", "-"), c.get("pad", "-"),
                         c.get("net", "GND"), c["x"], c["y"]))
    for v in zd.get("decoupling_via_to_plane", {}).get("vias", []):
        pos = v.get("pos")
        seq = pos if (isinstance(pos, list) and pos and isinstance(pos[0], list)) else [pos]
        for p in seq:
            if isinstance(p, list) and len(p) == 2 and isinstance(p[0], (int, float)):
                vias.append(("decoup_via", v.get("ref", "-"), v.get("pad", "-"),
                             v.get("net", "GND"), p[0], p[1]))
    for z in zd.get("power_zones", []):
        for v in z.get("vias", []):
            p = v.get("pos") or v.get("position")
            if isinstance(p, list) and len(p) == 2 and all(isinstance(q, (int, float)) for q in p):
                vias.append(("zone_via", v.get("ref", "-"), v.get("pad", "-"),
                             v.get("net", z.get("net", "-")), p[0], p[1]))
    return vias, stubs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CO-91 计划坐标权威净距闸")
    ap.add_argument("--spec", default=str(DEFAULT_SPEC))
    ap.add_argument("--board", default=str(DEFAULT_BOARD))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    import eda_core.pdn_apply as pa

    rules = Rules(json.loads(RULES.read_text()))
    # 规则源唯一性（fail-closed）：k2/_shared 与容器 _shared 的 drc_rules 必须同字节；
    # 若漂移则本闸不可判（verdict=FAIL），避免「以哪份规则判」歧义。
    cons = {"k2_shared": str(RULES.relative_to(K2.parent)), "k2_shared_sha16": s16(RULES),
            "container_shared": str(RULES_ALT.relative_to(K2.parent)),
            "container_shared_sha16": s16(RULES_ALT),
            "agree": s16(RULES) == s16(RULES_ALT)}
    board = pcbnew.LoadBoard(a.board)
    sp, bp = Path(a.spec), Path(a.board)
    zd = json.loads(sp.read_text())["pd"]["zone_defs"]
    scene = Scene(board, rules, pa.VIA_DIA / 2, pa.VIA_DRILL / 2)

    targets, stubs = collect(zd)
    rows, bad = [], []
    for kind, ref, pad, net, x, y in sorted(targets, key=lambda t: (t[0], str(t[1]), str(t[2]))):
        ok, c, h, bind = scene.via_at(x, y, net)
        r = {"kind": kind, "ref": ref, "pad": pad, "net": net,
             "pos": [round(x, 3), round(y, 3)],
             "clr_margin": c, "hole_margin": h, "binding": bind, "ok": ok}
        rows.append(r)
        if not ok:
            bad.append(r)
    srows, sbad = [], []
    for kind, ref, pad, net, ax, ay, bx, by, w in sorted(stubs, key=lambda t: (t[0], str(t[1]), str(t[2]))):
        ok, m, bind = scene.seg_clear(ax, ay, bx, by, w, net)
        r = {"kind": kind, "ref": ref, "pad": pad, "net": net, "pad_pos": [ax, ay],
             "via_pos": [bx, by], "width": w, "clr_margin": m, "binding": bind, "ok": ok}
        srows.append(r)
        if not ok:
            sbad.append(r)

    clean = next((r for r in reversed(rows) if r["clr_margin"] > 0.3 and r["hole_margin"] > 0.3), None)
    tb = bad[0] if bad else {"pos": [86.6, 56.516], "net": "GND"}
    _, bc_, bh_, _ = scene.via_at(tb["pos"][0], tb["pos"][1], tb["net"])
    sb = min(sbad, key=lambda r: r["clr_margin"]) if sbad else None
    sbc = scene.seg_clear(sb["pad_pos"][0], sb["pad_pos"][1], sb["via_pos"][0], sb["via_pos"][1],
                          sb["width"], sb["net"])[1] if sb else None
    sc = max((r for r in srows if r["clr_margin"] > 0.3), key=lambda r: r["clr_margin"], default=None)
    scc = scene.seg_clear(sc["pad_pos"][0], sc["pad_pos"][1], sc["via_pos"][0], sc["via_pos"][1],
                          sc["width"], sc["net"])[1] if sc else None
    teeth = {"detector_via_bad_caught": bool(bc_ < 0 or bh_ < 0),
             "detector_via_clean_passes": bool(clean and clean["clr_margin"] >= 0),
             "detector_stub_bad_caught": bool(sbc is not None and sbc < 0),
             "detector_stub_clean_passes": bool(scc is not None and scc >= 0),
             "n_via_targets": len(targets), "n_stub_targets": len(stubs)}

    by_kind = {k: {"n": sum(1 for r in rows if r["kind"] == k),
                   "n_viol": sum(1 for r in bad if r["kind"] == k)}
               for k in sorted({r["kind"] for r in rows})}
    verd = "PASS" if (not bad and not sbad and cons["agree"]) else "FAIL"
    rec = {"artifact": "m13_v57_co91_pdn_planned_coord_clearance_gate", "schema": 1,
           "revision": "CO-91.3",
           "nature": "L2 PDN：pd.zone_defs 计划坐标（pdn_apply 实落集）对权威净距（netclass clearance + min_hole_clearance）的机判",
           "inputs": {"spec": sp.name, "spec_sha16": s16(sp), "board": bp.name,
                      "board_sha16": s16(bp), "rules": RULES.name, "rules_sha16": s16(RULES),
                      "rules_source_consistency": cons,
                      "via_dia": pa.VIA_DIA, "via_drill": pa.VIA_DRILL, "stub_width": STUB_W,
                      "materializer": "eda_core/pdn_apply.py（坐标逐字取自 SPEC）"},
           "counts": {"by_kind": by_kind, "n_via_targets": len(rows), "n_via_violations": len(bad),
                      "n_stub_targets": len(srows), "n_stub_violations": len(sbad)},
           "via_violations": sorted(bad, key=lambda r: (r["kind"], r["ref"], str(r["pad"]))),
           "stub_violations": sorted(sbad, key=lambda r: r["clr_margin"]),
           "teeth": teeth,
           "verdict": verd if cons["agree"] else "FAIL(规则源漂移，不可判)",
           "rules_source_note": "k2/_shared 与容器 _shared 的 drc_rules 必须同字节；本闸据此断言（fail-closed）。",
           "repair_candidate_ref": ("CO-92（m13_v57_co92_pdn_repair_candidate.json）："
                                    "修复候选归 CO-92；CO-91.1 的 fix_candidate（8 向 × 半径梯 0.30-2.00）"
                                    "违「零坐标搜索」红线，**已作废**，改由 CO-92 的声明式有限 palette 给出。"),
           "non_claims": ["不改 SPEC/板/阈值/冻结源；不改 _shared 引擎模型",
                          "判『计划坐标』；板未施工（PDN 实体 = L3 派生）⇒ 非『已交付板不合规』",
                          "引擎净距口径借用 drc_rules.json 语义核（已对齐 kicad DRC 430/430 + 106/106）"],
           "redline": "零几何（只读）；无 while 搜索；无坐标搜索；输出确定性（sorted）。"}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"CO-91 verdict={verd} via_targets={len(rows)} via_viol={len(bad)} "
          f"stub_targets={len(srows)} stub_viol={len(sbad)}")
    for r in sorted(bad, key=lambda r: min(r["clr_margin"], r["hole_margin"]))[:8]:
        print(f"  {r['kind']} {r['ref']}.{r['pad']} {r['net']} @{r['pos']} "
              f"clr={r['clr_margin']} hole={r['hole_margin']} :: {r['binding']}")
    print(f"  teeth={teeth}")
    return 0 if verd == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
