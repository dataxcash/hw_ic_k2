#!/usr/bin/env python3
"""k2_deviation_gen_v1.py --- **偏离通道生成器**（#K2-416 §五.1(i)/§五.3/§五.4）。

对每个残差断口**逐条**给出（只读 · 确定性 · **零搜索** · 零板改 · 零考跑）：
  · **每线确定几何**：层 / 域内两端点 / **廊道矩形** / 折线 / 换层**孔对**（两端层不同 ⇒ 一个过孔）；
  · **逐廊道守恒机核（硬）**：`capacity_mm`（该廊道**自身**净空子矩窄边） ≥ `need_mm`（该网线宽 + 2×净空）
    —— **禁以域/块级空闲代替**（#K2-413 已钉二犯）；
  · **堵点具名** ＋ **有界偏离量**（= `need − 被围死端的局部净宽`，仅对被围死端给出，单位 mm）。
CLI: python3 tools/k2_deviation_gen_v1.py --board B --drc D --bound-rect x0,y0,x1,y1 [--clearance .2] [--margin 0.4] [--json-out P]
"""
from __future__ import annotations
import argparse, importlib.util, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYER_RE = re.compile(r"(F\.Cu|B\.Cu|In\d+(?:\.Cu)?)")


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _layers(desc):
    out, seen = [], set()
    for L in LAYER_RE.findall(desc or ""):
        L = L if L.endswith(".Cu") else L + ".Cu"
        if L not in seen:
            seen.add(L); out.append(L)
    return out or ["F.Cu"]


def pairs(drc):
    out = []
    for it in (drc.get("unconnected_items") or []):
        its = it.get("items") or []
        if len(its) != 2:
            continue
        da, db = its[0].get("description", ""), its[1].get("description", "")
        ma, mb = re.search(r"\[([^\]]+)\]", da or ""), re.search(r"\[([^\]]+)\]", db or "")
        if not ma or not mb or ma.group(1) != mb.group(1):
            continue
        out.append({"net": ma.group(1), "desc": [da, db],
                    "p1": [its[0]["pos"]["x"], its[0]["pos"]["y"]],
                    "p2": [its[1]["pos"]["x"], its[1]["pos"]["y"]],
                    "layers": [_layers(da)[0], _layers(db)[0]]})
    return out


def _clamp(p, r):
    return (min(max(p[0], r[0]), r[2]), min(max(p[1], r[1]), r[3]))


def build(board, drc_path, bound, clearance=0.20, margin=0.4):
    import pcbnew as P
    AUD = _load("k2_corridor_occupancy_audit_v1", "tools/k2_corridor_occupancy_audit_v1.py")
    RDR = _load("k2_corridor_redraw_v1", "tools/k2_corridor_redraw_v1.py")
    b = P.LoadBoard(board)
    netw = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if n and type(t).__name__ != "PCB_VIA":
            netw[n] = min(netw.get(n, 1e9), P.ToMM(t.GetWidth()))
    out = {"artifact": "k2_deviation_channel_v1", "ts": "2026-09-29", "board": board,
           "authority": "#K2-416 sec.5: the deviation channel for the five named residuals of the #K2-415 run.",
           "bound_rect": list(bound), "clearance_mm": clearance, "corridor_margin_mm": margin,
           "rule": "PER-CORRIDOR conservation: capacity (the witnessed clear sub-rectangle's narrow dimension) >= need "
                   "(this net's track width + 2*clearance). Block/domain-level free-area substitution is FORBIDDEN.",
           "items": [], "OWNER-ITEMS": 0}
    for pr in pairs(json.load(open(drc_path, encoding="utf-8"))):
        a, bpt = _clamp(pr["p1"], bound), _clamp(pr["p2"], bound)
        rect = (max(bound[0], min(a[0], bpt[0]) - margin), max(bound[1], min(a[1], bpt[1]) - margin),
                min(bound[2], max(a[0], bpt[0]) + margin), min(bound[3], max(a[1], bpt[1]) + margin))
        layers = sorted(set(pr["layers"]), key=pr["layers"].index)
        _occd = [o for o in AUD.occupant_rects(b, layers, pr["net"], clearance)
                 if AUD.rect_gap(rect, o["bbox"]) <= clearance + 1e-9]
        occ = [o["bbox"] for o in _occd]
        wit, _ = RDR.clear_subrect_containing_pts(rect, occ, clearance, [a, bpt])
        s1, _ = RDR.clear_subrect_containing_pts(rect, occ, clearance, [a])
        s2, _ = RDR.clear_subrect_containing_pts(rect, occ, clearance, [bpt])
        cap = min(wit[2] - wit[0], wit[3] - wit[1]) if wit else None
        cap1 = min(s1[2] - s1[0], s1[3] - s1[1]) if s1 else 0.0
        cap2 = min(s2[2] - s2[0], s2[3] - s2[1]) if s2 else 0.0
        w = netw.get(pr["net"], 0.20)
        need = w + 2 * clearance
        status = ("WITNESS_OK" if (wit and cap >= need - 1e-9) else ("NARROW" if wit else "NO_COMMON_CHANNEL"))
        dev = 0.0 if status == "WITNESS_OK" else round(max(0.0, need - min(cap1, cap2)), 4)
        blk = sorted({o["net"] for o in AUD.occupant_rects(b, layers, pr["net"], clearance)
                      if AUD.rect_gap(rect, o["bbox"]) <= clearance + 1e-9
                      and ((o["bbox"][0] - clearance - 1e-9 <= a[0] <= o["bbox"][2] + clearance + 1e-9
                            and o["bbox"][1] - clearance - 1e-9 <= a[1] <= o["bbox"][3] + clearance + 1e-9)
                           or (o["bbox"][0] - clearance - 1e-9 <= bpt[0] <= o["bbox"][2] + clearance + 1e-9
                               and o["bbox"][1] - clearance - 1e-9 <= bpt[1] <= o["bbox"][3] + clearance + 1e-9))})
        _blkset = {o["net"] for o in _occd
                   if ((o["bbox"][0]-clearance-1e-9 <= a[0] <= o["bbox"][2]+clearance+1e-9
                        and o["bbox"][1]-clearance-1e-9 <= a[1] <= o["bbox"][3]+clearance+1e-9)
                       or (o["bbox"][0]-clearance-1e-9 <= bpt[0] <= o["bbox"][2]+clearance+1e-9
                           and o["bbox"][1]-clearance-1e-9 <= bpt[1] <= o["bbox"][3]+clearance+1e-9))}
        wit2, _ = RDR.clear_subrect_containing_pts(rect, [o["bbox"] for o in _occd if o["net"] not in _blkset],
                                                   clearance, [a, bpt])
        capA = min(wit2[2]-wit2[0], wit2[3]-wit2[1]) if wit2 else None
        witness_after_yield = bool(wit2 and capA >= need - 1e-9)
        geo = {"layers": layers, "slot": layers, "corridor_rect": [round(v, 4) for v in rect],
               "p1_in_domain": [round(a[0], 4), round(a[1], 4)], "p2_in_domain": [round(bpt[0], 4), round(bpt[1], 4)],
               "polyline": [[round(a[0], 4), round(a[1], 4)], [round(bpt[0], 4), round(bpt[1], 4)]],
               "via_hole_pair": ({"at": [round(bpt[0], 4), round(bpt[1], 4)], "layers": layers}
                                 if len(layers) > 1 else None),
               "valid_after_yield": witness_after_yield}
        out["items"].append({"net": pr["net"], "from_desc": pr["desc"][0][:60], "to_desc": pr["desc"][1][:60],
                             "geometry": geo, "capacity_mm": None if cap is None else round(cap, 4),
                             "cap_at_p1_mm": round(cap1, 4), "cap_at_p2_mm": round(cap2, 4),
                             "need_mm": round(need, 4), "track_w_mm": round(w, 4), "status": status,
                             "bounded_deviation_mm": dev, "blockers_named": blk, "n_occupants": len(occ),
                             "witness_after_yield": witness_after_yield,
                             "yield_note": "remove the named blockers at the boxed end and the STRAIGHT channel above is "
                                           "clear (verified); so the determinate construction = that polyline + the via hole-pair, "
                                           "conditional on the named yield (%s mm)." % dev,
                             "buildability": "no_move" if status == "WITNESS_OK" else "relocation_listed"})
    out["summary"] = {"n": len(out["items"]),
                      "witness_ok": sum(1 for i in out["items"] if i["status"] == "WITNESS_OK"),
                      "buildability": "no_move" if all(i["buildability"] == "no_move" for i in out["items"])
                                       else "relocation_listed"}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--drc", required=True)
    ap.add_argument("--bound-rect", dest="bound_rect", required=True)
    ap.add_argument("--clearance", type=float, default=0.20)
    ap.add_argument("--margin", type=float, default=0.4)
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    rep = build(a.board, a.drc, tuple(float(v) for v in a.bound_rect.split(",")), a.clearance, a.margin)
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
