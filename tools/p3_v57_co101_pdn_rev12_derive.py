#!/usr/bin/env python3
"""CO-101：【L2 PDN 自裁 · 施加】rev-11 → **rev-12 计划集重导**（互障感知；改 rev-12 SPEC，不动历史件）。

依据 CO-99（计划集互冲 FAIL）+ CO-100（互障感知修复候选 PARTIAL：残余重叠 0，6 新增 blocked）。
本件把 CO-100 的候选**施加**为 SPEC rev-12：
  - ppc：kept/relocated 重落（`clearance` 按板侧 Scene 重算）；6 项候选 blocked 中 ppc 的 5 项并入 blocked 台账；
  - gnd_stitch_via：kept/relocated 重落 + 1 项 blocked；
  - power_zones[].vias：重落；
  - **退役留存**：rev-11 原坐标存 `retired_superseded_mutual_conflict_v1`（禁静默放弃）；
  - **F5 同步**：`board_realized` 更新为 rev-12 决策数（消除 223/86 陈旧矛盾）；
  - **F1 残余闭合**：自 rev-9 回填 `retired_superseded_bom`（随本次构建期 SPEC bump）。
零几何搜索（坐标全部来自 CO-100 的声明 palette 重放）；不改板/阈值/冻结源。

CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co101_pdn_rev12_derive.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SRC = L3 / "SPEC_k2_v4.spec-rev-11.json"
SRC9 = L3 / "SPEC_k2_v4.spec-rev-9.json"
CO100 = STEP2 / "m13_v57_co100_pdn_mutual_repair_candidate.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-12.json"
REC = STEP2 / "m13_v57_co101_pdn_rev12_derive.json"
CO91 = K2 / "tools/p3_v57_co91_pdn_planned_coord_clearance_gate.py"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--rec", default=str(REC))
    a = ap.parse_args(argv)

    import sys
    sys.path.insert(0, str(K2.parent / "_shared"))
    import pcbnew
    import eda_core.pdn_apply as pa

    spec_m = importlib.util.spec_from_file_location("co91d", CO91)
    C = importlib.util.module_from_spec(spec_m); spec_m.loader.exec_module(C)

    spec = json.loads(Path(a.src).read_text())
    zd = spec["pd"]["zone_defs"]
    rows = json.loads(Path(CO100).read_text())["rows"]
    rules = C.Rules(json.loads(C.RULES.read_text()))
    board = pcbnew.LoadBoard(str(BOARD))
    scene = C.Scene(board, rules, pa.VIA_DIA / 2.0, pa.VIA_DRILL / 2.0)
    w = float(zd["power_pad_connect"].get("stub_width_mm", 0.2))

    def margins(cx, cy, vx, vy, net):
        ok, mc, mh, _ = scene.via_at(vx, vy, net)
        if not ok:
            return None
        ok2, ms, _ = scene.seg_clear(cx, cy, vx, vy, w, net)
        if not ok2:
            return None
        return round(min(mc, mh, ms), 3)

    # ---------- ppc ----------
    old_ppc = zd["power_pad_connect"]
    old_by = {(e["ref"], str(e["pad"])): e for e in old_ppc["entries"]}
    ppc_rows = [r for r in rows if r["kind"] == "ppc"]
    new_entries, new_blocked, ppc_moved, ppc_blk_new = [], [], [], []
    for r in ppc_rows:
        key = (r["ref"], str(r["pad"]))
        e = old_by.get(key)
        if e is None:
            raise SystemExit(f"ppc entry not found: {key}")
        if r["status"] == "blocked":
            new_blocked.append({"ref": r["ref"], "pad": r["pad"], "net": r["net"],
                                "pad_pos": e["pad_pos"], "reason": "CO-99 互障（板+计划集+孔距）下声明 palette 无合法位"})
            ppc_blk_new.append({"ref": r["ref"], "pad": r["pad"], "net": r["net"], "retired_pos": e["via_pos"]})
            continue
        if r["status"] == "kept":
            new_entries.append(e)
            continue
        m = margins(e["pad_pos"][0], e["pad_pos"][1], r["new"][0], r["new"][1], r["net"])
        if m is None:
            raise SystemExit(f"relocated ppc not clean on board: {key}")
        ne = dict(e); ne["via_pos"] = list(r["new"]); ne["clearance"] = m; ne["clearance_binding"] = "authoritative"
        new_entries.append(ne)
        ppc_moved.append({"ref": r["ref"], "pad": r["pad"], "net": r["net"], "old": e["via_pos"], "new": list(r["new"])})
    # 旧的 blocked 台账保留 + 新增
    all_blocked = list(old_ppc["blocked"]) + new_blocked

    new_ppc = dict(old_ppc)
    new_ppc["entries"] = new_entries
    new_ppc["blocked"] = all_blocked
    new_ppc["retired_superseded_mutual_conflict_v1"] = {
        "note": "CO-101（rev-12）互障重导：rev-11 原计划坐标退役留存（禁静默放弃）",
        "ppc_relocated": ppc_moved, "ppc_blocked_new": ppc_blk_new}
    # F5 同步
    new_ppc["board_realized"] = {"co": "CO-101", "board": BOARD.name, "board_sha16": s16(BOARD),
                                 "tool": "CO-100 互障感知重放（声明 palette）",
                                 "pwr_nets": old_ppc.get("board_realized", {}).get("pwr_nets", []),
                                 "n_entries": len(new_entries), "n_blocked": len(all_blocked),
                                 "note": "CO-96 F5 同步：原 CO-89 的 223/86 已随 rev-12 更新"}
    # F1 残余闭合：回填
    s9 = json.loads(SRC9.read_text())
    rsb = s9["pd"]["zone_defs"]["power_pad_connect"].get("retired_superseded_bom")
    if rsb is not None:
        new_ppc["retired_superseded_bom"] = rsb
    zd["power_pad_connect"] = new_ppc

    # ---------- stitch ----------
    old_cs = zd["gnd_stitch_via"]["coordinates"]
    by_old = {}
    for c in old_cs:
        if isinstance(c.get("x"), (int, float)):
            by_old[(round(c["x"], 3), round(c["y"], 3))] = c
    st_rows = [r for r in rows if r["kind"] == "stitch"]
    st_new, st_moved, st_blk_new, used = [], [], [], set()
    for r in st_rows:
        o = tuple(round(v, 3) for v in r["old"])
        c = by_old.get(o)
        if c is None:
            raise SystemExit(f"stitch coord not found: {o}")
        used.add(o)
        if r["status"] == "blocked":
            st_blk_new.append({"net": r["net"], "x": None, "y": None, "status": "blocked", "blocked": True,
                               "retired_pos": list(r["old"]), "reason": "CO-99 互障/孔距下声明 palette 无合法位"})
            continue
        if r["status"] == "kept":
            st_new.append(c); continue
        nc = dict(c); nc["x"], nc["y"], nc["old_pos"] = r["new"][0], r["new"][1], list(r["old"])
        st_new.append(nc); st_moved.append({"net": r["net"], "old": list(r["old"]), "new": list(r["new"])})
    # 原 blocked（无坐标）保留
    st_old_blocked = [c for c in old_cs if not isinstance(c.get("x"), (int, float))]
    zd["gnd_stitch_via"]["coordinates"] = st_new + st_old_blocked + st_blk_new
    zd["gnd_stitch_via"]["retired_superseded_mutual_conflict_v1"] = {
        "note": "CO-101（rev-12）互障重导：rev-11 stitch 原坐标退役留存",
        "stitch_relocated": st_moved, "stitch_blocked_new": st_blk_new}

    # ---------- zone vias ----------
    zn_moved = []
    zi = 0
    zn_rows = [r for r in rows if r["kind"] == "zone"]
    # rows 顺序 = 按 (net,x,y) 排序的 zone 列表；重建 power_zones[].vias
    by_zone = {}
    for r in zn_rows:
        by_zone.setdefault(r["net"], []).append(r)
    for z in zd["power_zones"]:
        vs = z.get("vias", [])
        if not vs:
            continue
        rs = list(by_zone.get(z["net"], []))   # 逐项**消费**（重坐位坐标可重复，须一一对应）
        out_v = []
        for v in vs:
            o = tuple(round(q, 3) for q in v["pos"])
            match = next((r for r in rs if tuple(round(q, 3) for q in r["old"]) == o), None)
            if match is None:
                out_v.append(v); continue
            rs.remove(match)
            if match["status"] == "kept":
                out_v.append(v)
            else:
                out_v.append({"pos": list(match["new"]), "old_pos": list(match["old"])})
                zn_moved.append({"net": z["net"], "old": list(match["old"]), "new": list(match["new"])})
        z["vias"] = out_v
    zd["power_zones_via_retired_mutual_conflict_v1"] = {"note": "CO-101（rev-12）", "zone_relocated": zn_moved}

    spec["spec_version"] = "1.1.spec-rev-12"
    Path(a.out).write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n")

    rec = {
        "artifact": "m13_v57_co101_pdn_rev12_derive", "schema": 1, "revision": "CO-101.1",
        "nature": "L2 PDN 自裁施加：rev-11 → rev-12 计划集互障重导（依 CO-99/CO-100）",
        "src": Path(a.src).name, "src_sha16": s16(Path(a.src)), "out": Path(a.out).name, "out_sha16": s16(Path(a.out)),
        "co100_record": CO100.name, "co100_sha16": s16(CO100),
        "changes": {"ppc_entries": len(new_entries), "ppc_blocked": len(all_blocked),
                    "ppc_relocated": len(ppc_moved), "ppc_blocked_new": len(ppc_blk_new),
                    "stitch_relocated": len(st_moved), "stitch_blocked_new": len(st_blk_new),
                    "zone_relocated": len(zn_moved),
                    "f5_board_realized_synced": True, "f1_retired_bom_backfilled": rsb is not None},
        "redline": "零几何搜索（坐标全部来自 CO-100 声明 palette 重放）；历史件不改；退役坐标显式留存。",
    }
    Path(a.rec).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-101 rev-12 written:", json.dumps(rec["changes"], ensure_ascii=False))
    print("spec_sha16", rec["out_sha16"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
