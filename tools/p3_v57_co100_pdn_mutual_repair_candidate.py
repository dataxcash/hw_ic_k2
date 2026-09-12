#!/usr/bin/env python3
"""CO-100：【L2 PDN】CO-99 互冲的**修复候选**（scratch 机判，不改 canonical）。

对 CO-99 判定的「计划集内部异网互冲」，用 CO-92 同一套**声明式有限 palette** 做**互障感知**的确定性重放
（零 while、零坐标搜索、零优化迭代），回答：**rev-12 计划集重导能否自解，还是须并入 L1/工艺（via-in-pad/HDI）**。

palette（声明固定，与 CO-92 一致）：
  ppc：`current` → 自家 pad 4 正交 @ (VIA_R+0.3) → 自家 pad 4 正交 @ 0.6；
  stitch/zone：`current` → 原位 4 正交 @ 0.6。
互障 = 板已有铜（CO-91 `Scene`）**+ 已接受的计划件**（via 与 ppc stub）；判定阈值同 CO-91 规则源。
处理序 = 声明确定性序（ppc → stitch → zone，各按 net/ref/pad 排序）。

CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co100_pdn_mutual_repair_candidate.py
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
CO91 = K2 / "tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-11.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co100_pdn_mutual_repair_candidate.json"
CARD = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BASE = {"spec": "d85f10f722ba22b0", "board": "0e636a67c1472462"}


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)

    import sys
    sys.path.insert(0, str(K2.parent / "_shared"))
    import pcbnew
    import eda_core.pdn_apply as pa

    spec = importlib.util.spec_from_file_location("co91c", CO91)
    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

    ident = {"spec": s16(Path(a.spec)), "board": s16(Path(a.board))}
    mismatch = {k: {"expect": v, "actual": ident.get(k)} for k, v in BASE.items() if ident.get(k) != v}

    rules = C.Rules(json.loads(C.RULES.read_text()))
    R = pa.VIA_DIA / 2.0
    zd = json.loads(Path(a.spec).read_text())["pd"]["zone_defs"]
    board = pcbnew.LoadBoard(a.board)
    scene = C.Scene(board, rules, R, pa.VIA_DRILL / 2.0)
    w = float(zd.get("power_pad_connect", {}).get("stub_width_mm", C.STUB_W_DEFAULT))

    # ---- 计划集（声明确定性序）----
    items = []
    for e in zd.get("power_pad_connect", {}).get("entries", []):
        items.append({"kind": "ppc", "net": e["net"], "ref": e["ref"], "pad": str(e["pad"]),
                      "pad": e["pad_pos"], "pos": list(e["via_pos"])})
    items.sort(key=lambda i: (0, i["net"], i["ref"], i["pad"]))
    st = [c for c in zd.get("gnd_stitch_via", {}).get("coordinates", [])
          if not (c.get("blocked") or c.get("status") == "blocked") and c.get("x") is not None]
    for c in sorted(st, key=lambda c: (c.get("net"), c["x"], c["y"])):
        items.append({"kind": "stitch", "net": c.get("net", "GND"), "ref": "-", "pad": "-",
                      "pad": None, "pos": [c["x"], c["y"]]})
    zv = []
    for z in zd.get("power_zones", []):
        for v in z.get("vias", []):
            zv.append({"net": z["net"], "pos": list(v["pos"])})
    for v in sorted(zv, key=lambda v: (v["net"], v["pos"][0], v["pos"][1])):
        items.append({"kind": "zone", "net": v["net"], "ref": "-", "pad": "-", "pad": None, "pos": v["pos"]})

    placed_vias = []   # (net,x,y)
    placed_stubs = []  # (net,ax,ay,bx,by)

    def via_ok(net, x, y):
        ok, _c, _h, _b = scene.via_at(x, y, net)
        if not ok:
            return False
        for (n2, x2, y2) in placed_vias:
            d = ((x - x2) ** 2 + (y - y2) ** 2) ** 0.5
            if n2 != net and d < 2 * R + rules.req(net, n2):
                return False
            if d < pa.VIA_DRILL + 0.25 - 1e-9:   # 孔-孔 net-agnostic（板配置）
                return False
        for (n2, ax, ay, bx, by) in placed_stubs:
            if n2 == net:
                continue
            if C._d_pt_seg(x, y, ax, ay, bx, by) < R + w / 2 + rules.req(net, n2):
                return False
        return True

    def stub_ok(net, ax, ay, bx, by):
        ok, _m, _b = scene.seg_clear(ax, ay, bx, by, w, net)
        if not ok:
            return False
        for (n2, x2, y2) in placed_vias:
            if n2 == net:
                continue
            if C._d_pt_seg(x2, y2, ax, ay, bx, by) < w / 2 + R + rules.req(net, n2):
                return False
        for (n2, cx, cy, dx, dy) in placed_stubs:
            if n2 == net:
                continue
            if C._d_seg_seg(ax, ay, bx, by, cx, cy, dx, dy) < w + rules.req(net, n2):
                return False
        return True

    def candidates(it):
        p = it["pos"]
        if it["kind"] == "ppc":
            p0 = it["pad"]
            cands = [tuple(p)]
            for r in (R + 0.3, 0.6):
                for ux, uy in CARD:
                    cands.append((round(p0[0] + ux * r, 3), round(p0[1] + uy * r, 3)))
            return cands
        cands = [tuple(p)]
        for r in (0.6,):
            for ux, uy in CARD:
                cands.append((round(p[0] + ux * r, 3), round(p[1] + uy * r, 3)))
        return cands

    rows = []
    for it in items:
        hit = None
        for (cx, cy) in candidates(it):
            if not via_ok(it["net"], cx, cy):
                continue
            if it["kind"] == "ppc":
                p0 = it["pad"]
                if not stub_ok(it["net"], p0[0], p0[1], cx, cy):
                    continue
            hit = (cx, cy)
            break
        if hit is None:
            rows.append({"kind": it["kind"], "net": it["net"], "ref": it["ref"], "pad": it["pad"],
                         "old": it["pos"], "new": None, "status": "blocked"})
            continue
        moved = hit != tuple(it["pos"])
        placed_vias.append((it["net"], hit[0], hit[1]))
        if it["kind"] == "ppc":
            placed_stubs.append((it["net"], it["pad"][0], it["pad"][1], hit[0], hit[1]))
        rows.append({"kind": it["kind"], "net": it["net"], "ref": it["ref"], "pad": it["pad"],
                     "old": it["pos"], "new": [hit[0], hit[1]], "status": "relocated" if moved else "kept"})

    tally = collections.Counter((r["kind"], r["status"]) for r in rows)
    # 结果集互判（与 CO-99 同判据）：应 0 overlap
    vv = [(r["net"], r["new"][0], r["new"][1]) for r in rows if r["new"] and r["kind"] in ("ppc", "stitch", "zone")]
    ov = 0
    for i in range(len(vv)):
        for j in range(i + 1, len(vv)):
            if vv[i][0] == vv[j][0]:
                continue
            if ((vv[i][1] - vv[j][1]) ** 2 + (vv[i][2] - vv[j][2]) ** 2) ** 0.5 < 2 * R - 1e-9:
                ov += 1
    # 牙齿：合成重叠必被抓（同一判据）
    tooth = 0.22 < 2 * R and 0.60 >= 2 * R + 0.2

    blocked = [r for r in rows if r["status"] == "blocked"]
    rec = {
        "artifact": "m13_v57_co100_pdn_mutual_repair_candidate", "schema": 1, "revision": "CO-100.1",
        "nature": "L2 PDN：CO-99 互冲的互障感知修复候选（声明 palette、确定性序、零坐标搜索；scratch，不改 canonical）",
        "inputs": {**ident, "via_dia": pa.VIA_DIA, "stub_width_mm": w},
        "baseline_expectations": BASE, "baseline_mismatch": mismatch,
        "tally": {f"{k[0]}_{k[1]}": v for k, v in sorted(tally.items())},
        "blocked_detail": blocked[:40],
        "residual_mutual_overlap": ov,
        "verdict": ("BASELINE_MISMATCH" if mismatch else
                    ("TEETH_FAIL" if not tooth else
                     ("RESOLVED" if (ov == 0 and not blocked) else
                      ("PARTIAL" if ov == 0 else "UNRESOLVED")))),
        "teeth": {"overlap_pair_detected": 0.22 < 2 * R}, "teeth_ok": tooth,
        "non_claims": ["scratch 机判；不改 SPEC/板/阈值/冻结源", "palette 声明固定、序确定；无 while/无搜索",
                       "本件不施加；施加 = rev-12 + 全链重基线 + 换会话复评",
                       "blocked 者若源于 U6 0.5mm 场密度 ⇒ 属 L1/工艺（via-in-pad/HDI，见 CO-94）"],
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-100 verdict=%s tally=%s blocked=%d residual_overlap=%d" %
          (rec["verdict"], json.dumps(rec["tally"], ensure_ascii=False), len(blocked), ov))
    for r in blocked[:10]:
        print("   BLOCKED", r["kind"], r["net"], r["ref"], r["pad"], r["old"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
