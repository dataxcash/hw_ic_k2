#!/usr/bin/env python3
"""CO-92：【L2 PDN】rev-10 **修复候选**（scratch 机判，不改 canonical）。

对 CO-91 判定的违规实落集，用**声明式有限候选palette**（无 while、无坐标搜索、无优化迭代）
求「能否在权威口径下合法重落」，并量化 rev-10 的影响面（entries/blocked/覆盖/短段宽度）。

候选palette（声明固定）：
  - 当前位（优先保留，零位移）
  - 自家 pad 的 4 正交点 @ (VIA_R + 0.3)（= 生成器现行策略）
  - 自家 pad 的 4 正交点 @ 0.6mm（备用，仅当上者全不可）
  - stitch/zone：原位 4 正交点 @ 0.6mm
判定 = 复用 CO-91 的权威检测器（drc_rules 语义核 + 层语义 + 精确几何），语义单一来源。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co92_pdn_repair_candidate.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pcbnew

K2 = Path(__file__).resolve().parents[1]
CO91 = K2 / "tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py"
DEFAULT_SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-10.json"
DEFAULT_BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
DEFAULT_OUT = (K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
               / "m13_v57_co92_pdn_repair_candidate.json")
CARD = [(1, 0), (-1, 0), (0, 1), (0, -1)]
WIDTH_LADDER = [0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1]


def s16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_co91():
    spec = importlib.util.spec_from_file_location("co91check", CO91)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CO-92 PDN 修复候选")
    ap.add_argument("--spec", default=str(DEFAULT_SPEC))
    ap.add_argument("--board", default=str(DEFAULT_BOARD))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    C = load_co91()
    import eda_core.pdn_apply as pa

    rules_doc = json.loads(C.RULES.read_text())
    rules = C.Rules(rules_doc)
    con_k2, con_alt = s16(C.RULES), s16(C.RULES_ALT)
    board = pcbnew.LoadBoard(a.board)
    sp, bp = Path(a.spec), Path(a.board)
    scene = C.Scene(board, rules, pa.VIA_DIA / 2, pa.VIA_DRILL / 2)
    zd = json.loads(sp.read_text())["pd"]["zone_defs"]

    # pad 几何索引（重落候选要以自家 pad 为参照）
    padgeo = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            x0, y0, x1, y1 = C._bb(p)
            padgeo[(fp.GetReference(), str(p.GetNumber()))] = ((x0 + x1) / 2, (y0 + y1) / 2,
                                                               (x1 - x0) / 2, (y1 - y0) / 2)
    off_pad = pa.VIA_DIA / 2 + 0.3      # 生成器现行：pad 边缘 + 0.475

    def try_via(vx, vy, net):
        return scene.via_at(vx, vy, net)

    def candidates_from_pad(ref, pad, net):
        g = padgeo.get((ref, pad))
        if g is None:
            return []
        cx, cy, hw, hh = g
        out = []
        for base in (off_pad, 0.6):
            for ux, uy in CARD:
                ex = cx + (hw if ux > 0 else -hw if ux < 0 else 0)
                ey = cy + (hh if uy > 0 else -hh if uy < 0 else 0)
                out.append((round(ex + ux * base, 3), round(ey + uy * base, 3)))
        return out

    def candidates_from_point(x, y, base=0.6):
        return [(round(x + ux * base, 3), round(y + uy * base, 3)) for ux, uy in CARD]

    def best_of(cur, cands, net):
        scored = []
        for (vx, vy) in [tuple(cur)] + list(cands):
            ok, c, h, _ = try_via(vx, vy, net)
            scored.append((ok, min(c, h), [vx, vy], round(c, 3), round(h, 3)))
        ok_ones = [s for s in scored if s[0]]
        if not ok_ones:
            return None, max(scored, key=lambda s: s[1])
        # 优先原位；否则取可达且余量最大者
        for s in ok_ones:
            if s[2] == [round(cur[0], 3), round(cur[1], 3)]:
                return s, None
        return max(ok_ones, key=lambda s: s[1]), None

    res = {"ppc": [], "stitch": [], "zone": []}
    tally = {}

    for e in zd["power_pad_connect"]["entries"]:
        cur = tuple(e["via_pos"])
        cands = candidates_from_pad(e["ref"], str(e["pad"]), e["net"])
        keep, worst = best_of(cur, cands, e["net"])
        if keep:
            act = "kept" if keep[2] == [round(cur[0], 3), round(cur[1], 3)] else "relocated"
            res["ppc"].append({"ref": e["ref"], "pad": str(e["pad"]), "net": e["net"],
                               "from": [round(cur[0], 3), round(cur[1], 3)], "to": keep[2],
                               "action": act, "clr": keep[3], "hole": keep[4]})
        else:
            res["ppc"].append({"ref": e["ref"], "pad": str(e["pad"]), "net": e["net"],
                               "from": [round(cur[0], 3), round(cur[1], 3)], "to": None,
                               "action": "blocked", "best_margin": round(worst[1], 3)})
    tally["ppc"] = {k: sum(1 for r in res["ppc"] if r["action"] == k)
                    for k in ("kept", "relocated", "blocked")}

    for c in zd["gnd_stitch_via"]["coordinates"]:
        if not (isinstance(c.get("x"), (int, float)) and isinstance(c.get("y"), (int, float))):
            continue
        cur = (c["x"], c["y"])
        keep, worst = best_of(cur, candidates_from_point(*cur), "GND")
        res["stitch"].append({"net": c.get("net", "GND"), "from": [round(cur[0], 3), round(cur[1], 3)],
                              "to": keep[2] if keep else None,
                              "action": ("kept" if keep and keep[2] == [round(cur[0], 3), round(cur[1], 3)]
                                         else "relocated" if keep else "blocked")})
    tally["stitch"] = {k: sum(1 for r in res["stitch"] if r["action"] == k)
                       for k in ("kept", "relocated", "blocked")}

    for z in zd["power_zones"]:
        for v in z.get("vias", []):
            p = v.get("pos") or v.get("position")
            if not (isinstance(p, list) and len(p) == 2 and all(isinstance(q, (int, float)) for q in p)):
                continue
            cur = (p[0], p[1])
            keep, worst = best_of(cur, candidates_from_point(*cur), z.get("net", "-"))
            res["zone"].append({"net": z.get("net"), "from": [round(cur[0], 3), round(cur[1], 3)],
                                "to": keep[2] if keep else None,
                                "action": ("kept" if keep and keep[2] == [round(cur[0], 3), round(cur[1], 3)]
                                           else "relocated" if keep else "blocked")})
    tally["zone"] = {k: sum(1 for r in res["zone"] if r["action"] == k)
                     for k in ("kept", "relocated", "blocked")}

    # 短段宽度：逐级 palette 机判（同一权威口径，仅 clearance）
    widths = {}
    for w in WIDTH_LADDER:
        n_bad = 0
        for e in zd["power_pad_connect"]["entries"]:
            p0, p1 = e.get("pad_pos"), e.get("via_pos")
            if not (isinstance(p0, list) and isinstance(p1, list)):
                continue
            ok, _, _ = scene.seg_clear(p0[0], p0[1], p1[0], p1[1], w, e["net"])
            if not ok:
                n_bad += 1
        widths[str(w)] = {"n_violations": n_bad, "n_targets": len(zd["power_pad_connect"]["entries"])}

    rec = {"artifact": "m13_v57_co92_pdn_repair_candidate", "schema": 1, "revision": "CO-92.1",
           "nature": "L2 PDN rev-10 修复候选（声明式有限候选 palette；scratch 机判；不改 canonical）",
           "inputs": {"spec": sp.name, "spec_sha16": s16(sp), "board": bp.name,
                      "board_sha16": s16(bp),
                      "rules_source_consistency": {"k2_shared_sha16": con_k2,
                                                    "container_shared_sha16": con_alt,
                                                    "agree": con_k2 == con_alt}},
           "candidate_palette": {"ppc": "原位 → 4 正交点@(VIA_R+0.3) → 4 正交点@0.6",
                                 "stitch_zone": "原位 → 4 正交点@0.6",
                                 "selection": "优先原位；否则可达者中余量最大（确定性序，无搜索）"},
           "ppc_impact": tally["ppc"], "stitch_impact": tally["stitch"], "zone_impact": tally["zone"],
           "stub_width_ladder": widths, "detail": res,
           "verdict": "CANDIDATE",
           "non_claims": ["未改 SPEC/板/阈值/冻结源；未改 _shared 引擎；本件为备料，施加需 rev-10 + 全链重基线 + 重新过对抗评审",
                          "候选为有限声明 palette 的确定性择优，非坐标搜索/非迭代求解"]}
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print("CO-92 candidate:", json.dumps({"ppc": tally["ppc"], "stitch": tally["stitch"],
                                          "zone": tally["zone"]}, ensure_ascii=False))
    print("stub width ladder:", json.dumps(widths, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
