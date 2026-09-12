#!/usr/bin/env python3
"""CO-93：【L2 PDN 自裁】SPEC rev-10 —— PDN 计划坐标按**权威净距**重落（声明式有限 palette）。

裁定（L2，自裁）：via 策略/PDN 承载属 L2 ⇒
  (1) 一律按权威口径（drc_rules.json：netclass max + min_hole_clearance + 层语义）重落；
  (2) 无合法位者转 `blocked`（**不放宽任何阈值**；不默认采用 via-in-pad —— 那需工艺证据）；
  (3) pad→via 短段宽度由 0.5 改为**声明口径 0.2mm**（= .kicad_pro min_track_width，可制造下限）；
      短段不合法 ⇒ 该 pad 亦转 blocked（entries 语义 = **整条连接合法**）。
候选 palette（声明固定，确定性序，无坐标搜索/无迭代）：原位 → 4 正交点 @(VIA_R+0.3) → 4 正交点 @0.6。
判定器 = 复用 CO-91 权威检测器（单一语义来源）。冻结 `_shared` 引擎不改（容器副本只读冻结；
其 legacy 口径保留供 rev-9 逐字节复现）。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co93_pdn_rev10_derive.py
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
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
CO91 = K2 / "tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py"
SRC = L3 / "SPEC_k2_v4.spec-rev-9.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-10.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
REC = L3 / "m13_v57_co93_pdn_rev10_derive.json"
STUB_W = 0.2
CARD = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="CO-93 SPEC rev-10 PDN 重落")
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--board", default=str(BOARD))
    a = ap.parse_args(argv)
    sp = importlib.util.spec_from_file_location("co91check", CO91)
    C = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(C)
    sys.path.insert(0, str(K2.parent / "_shared"))
    from eda_core.pad_connect_gen import DEFAULT_PWR_NETS
    import eda_core.pdn_apply as pa

    rules = C.Rules(json.loads(C.RULES.read_text()))
    board = pcbnew.LoadBoard(a.board)
    scene = C.Scene(board, rules, pa.VIA_DIA / 2, pa.VIA_DRILL / 2)
    via_r, drill_r = pa.VIA_DIA / 2, pa.VIA_DRILL / 2
    spec = json.loads(Path(a.src).read_text())
    zd = spec["pd"]["zone_defs"]
    old = zd["power_pad_connect"]

    padgeo, pads = {}, []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            x0, y0, x1, y1 = C._bb(p)
            key = (fp.GetReference(), str(p.GetNumber()))
            padgeo[key] = ((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2)
            if p.GetNetname() in DEFAULT_PWR_NETS:
                pads.append((fp.GetReference(), str(p.GetNumber()), p.GetNetname()))
    pads.sort()

    old_pos = {(e["ref"], str(e["pad"])): tuple(e["via_pos"]) for e in old["entries"]}

    def pal(ref, pad):
        cx, cy, hw, hh = padgeo[(ref, pad)]
        out = []
        if (ref, pad) in old_pos:
            out.append(tuple(old_pos[(ref, pad)]))
        for base in (via_r + 0.3, 0.6):
            for ux, uy in CARD:
                out.append((round(cx + (hw if ux > 0 else -hw if ux < 0 else 0) + ux * base, 3),
                            round(cy + (hh if uy > 0 else -hh if uy < 0 else 0) + uy * base, 3)))
        return out

    entries, blocked = [], []
    for (ref, pad, net) in pads:
        cx, cy, _, _ = padgeo[(ref, pad)]
        best, reasons = None, []
        for (vx, vy) in pal(ref, pad):
            ok_v, mv, hv, bv = scene.via_at(vx, vy, net)
            if not ok_v:
                reasons.append(f"via {bv} {min(mv, hv)}")
                continue
            ok_s, ms, bs = scene.seg_clear(cx, cy, vx, vy, STUB_W, net)
            if not ok_s:
                reasons.append(f"stub {bs} {ms}")
                continue
            best = (vx, vy, min(mv, hv), ms)
            break
        if best:
            entries.append({"ref": ref, "pad": pad, "net": net,
                            "pad_pos": [round(cx, 3), round(cy, 3)],
                            "via_pos": [best[0], best[1]],
                            "clearance": round(min(best[2], best[3]), 3),
                            "clearance_binding": "authoritative"})
        else:
            blocked.append({"ref": ref, "pad": pad, "net": net,
                            "pad_pos": [round(cx, 3), round(cy, 3)],
                            "reason": ("权威净距下声明 palette 无合法位（via 或短段）："
                                       + ("；".join(reasons[:3]) if reasons else "n/a"))})

    def repoint(coords, net_default):
        kept, moved, blk = [], [], []
        for c in coords:
            if not (isinstance(c.get("x"), (int, float)) and isinstance(c.get("y"), (int, float))):
                blk.append(c)
                continue
            net = c.get("net", net_default)
            cands = [(c["x"], c["y"])] + [(round(c["x"] + ux * 0.6, 3), round(c["y"] + uy * 0.6, 3))
                                          for ux, uy in CARD]
            hit = None
            for (vx, vy) in cands:
                ok, m, h, _ = scene.via_at(vx, vy, net)
                if ok:
                    hit = (vx, vy, min(m, h))
                    break
            if hit is None:
                blk.append({"net": net, "x": None, "y": None, "status": "blocked",
                            "blocked": True, "retired_pos": [c["x"], c["y"]],
                            "reason": "权威净距下声明 palette 无合法位"})
            elif (hit[0], hit[1]) == (c["x"], c["y"]):
                kept.append(c)
            else:
                n = dict(c)
                n["x"], n["y"], n["old_pos"] = hit[0], hit[1], [c["x"], c["y"]]
                moved.append(n)
        return kept, moved, blk

    st_kept, st_moved, st_blk = repoint([c for c in zd["gnd_stitch_via"]["coordinates"]
                                        if isinstance(c.get("x"), (int, float))], "GND")
    st_already = [c for c in zd["gnd_stitch_via"]["coordinates"]
                  if not isinstance(c.get("x"), (int, float))]
    retired_st = [{"net": c.get("net", "GND"), "pos": [c["retired_pos"][0], c["retired_pos"][1]],
                   "reason": c["reason"]} for c in st_blk]

    zn_kept, zn_moved, zn_blk = [], [], []
    for z in zd["power_zones"]:
        vias = []
        for v in z.get("vias", []):
            p = v.get("pos")
            if not (isinstance(p, list) and len(p) == 2):
                continue
            net = z.get("net", "-")
            cands = [(p[0], p[1])] + [(round(p[0] + ux * 0.6, 3), round(p[1] + uy * 0.6, 3))
                                      for ux, uy in CARD]
            hit = None
            for (vx, vy) in cands:
                ok, m, h, _ = scene.via_at(vx, vy, net)
                if ok:
                    hit = (vx, vy)
                    break
            if hit is None:
                zn_blk.append({"net": net, "retired_pos": [p[0], p[1]],
                               "reason": "权威净距下声明 palette 无合法位"})
            else:
                vias.append({"pos": [hit[0], hit[1]]})
                if (hit[0], hit[1]) != (p[0], p[1]):
                    zn_moved.append({"net": net, "old_pos": [p[0], p[1]], "new_pos": [hit[0], hit[1]]})
        z["vias"] = vias

    zd["power_pad_connect"] = {
        "rule": ("SMD 电源/地 pad → via 直连（F.Cu 短段 + 通孔 via drill 0.2/outer 0.35）；"
                 f"**权威净距口径**（drc_rules.json: netclass max + min_hole_clearance + 层语义）；"
                 f"短段宽 = {STUB_W}mm（声明，= min_track_width 可制造下限）；"
                 "候选 palette（声明固定）：原位 → 4 正交 @(via_r+0.3) → 4 正交 @0.6；"
                 "palette 内无合法位 ⇒ 显式 blocked（不放宽阈值）"),
        "clearance_policy": "authoritative",
        "stub_width_mm": STUB_W,
        "candidate_palette": ["current", "4cardinal@(via_r+0.3)", "4cardinal@0.6"],
        "entries": entries, "blocked": blocked,
        "retired_superseded_clearance_v1": {
            "note": "rev-9 计划坐标在权威口径下违规者（CO-91）退役留存，禁静默放弃",
            "entries": old["entries"], "blocked": old["blocked"]},
        "board_realized": old.get("board_realized"),
        "frozen_at": "CO-93 权威净距重落（rev-10）",
    }
    zd["gnd_stitch_via"]["coordinates"] = st_kept + st_moved + st_already + [
        {"net": c["net"], "x": None, "y": None, "status": "blocked", "blocked": True,
         "reason": c["reason"]} for c in st_blk]
    zd["gnd_stitch_via"]["rule"] = (zd["gnd_stitch_via"].get("rule", "") +
                                    " | CO-93：净距口径 = 权威（netclass+hole+层语义，障碍含交付板实际铜）；"
                                    "无合法位 ⇒ status=blocked（消费者可识别）")
    zd["gnd_stitch_via"]["retired_superseded_clearance_v1"] = retired_st
    zd["power_zones_via_retired_clearance_v1"] = zn_blk

    spec["spec_version"] = "1.1.spec-rev-10"
    Path(a.out).write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n")

    # 不变性：pd 以外逐值等于 rev-9
    r9, r10 = json.loads(Path(a.src).read_text()), json.loads(Path(a.out).read_text())
    outside = {k for k in set(r9) | set(r10) if k != "pd" and r9.get(k) != r10.get(k)}

    rec = {"artifact": "m13_v57_co93_pdn_rev10_derive", "schema": 1, "revision": "CO-93.1",
           "nature": "L2 PDN 自裁：按权威净距重落 PDN 计划坐标 → SPEC rev-10（声明式有限 palette）",
           "ruling": {"scope": "L2（via 策略/PDN 承载）自裁", "decisions":
                      ["一律按权威净距重落（netclass max + min_hole_clearance + 层语义）",
                       "无合法位 ⇒ 转 blocked（不放宽任何阈值）",
                       "不默认采用 via-in-pad（需工艺证据）",
                       f"pad→via 短段宽度 0.5 → {STUB_W}mm（可制造下限）"]},
           "src": {"spec": Path(a.src).name, "sha16": s16(a.src)},
           "out": {"spec": Path(a.out).name, "sha16": s16(a.out)},
           "board": {"name": Path(a.board).name, "sha16": s16(a.board)},
           "delta": {"pad_targets": len(pads), "entries": len(entries), "blocked": len(blocked),
                     "rev9_entries": len(old["entries"]), "rev9_blocked": len(old["blocked"]),
                     "connected_delta": len(entries) - len(old["entries"]),
                     "stitch": {"kept": len(st_kept), "moved": len(st_moved),
                                "blocked_new": len(st_blk), "already_blocked": len(st_already)},
                     "zone_via_moved": len(zn_moved), "zone_via_blocked_new": len(zn_blk)},
           "invariants": {"outside_pd_changed_keys": sorted(outside),
                          "board_unchanged": True},
           "verdict": "DERIVED"}
    Path(REC).write_text(json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(rec["delta"], ensure_ascii=False, indent=1))
    print("outside_pd_changed_keys =", sorted(outside))
    print("rev10 sha16 =", s16(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
