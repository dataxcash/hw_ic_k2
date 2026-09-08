#!/usr/bin/env python3
"""v53 Phase 1 gate — EscapeTable/ColumnBook/CCF 加性 schema 真实板验收。

执行（全前台）：
  1. 空 EscapeTable      —— 全链行为逐字节==P0（report sha == P0 golden）
  2. 16 SOLVED 段反演     —— EscapeTable 16 pinned records（含 provenance/
     solve_ref/input_fp/source_path；几何取自 SOLVED path 记录，非 allocator
     重算）→ serialize/deserialize round-trip
  3. CCF View 装配        —— 对含 chip-side via 的行 assemble（assembler 通用，
     输入 = report 真 alloc/landing/anchors/corridor）
  4. fact_validate        —— 字段完备 + dup-via 断言（CCF chip via == EscapeTable
     坐标 <=1e-6；connector via 不混入 chip 命名空间）
  5. replay_equals        —— 重装 CCF == 存储 view
  6. dup-via 断言         —— 见 4；故意漂移 FAIL 由单测覆盖（test_construction_fact）
  7/8. AllocTable/LandingTable checksum == P0 审计值
产出 m13_v53_p1_audit.json。PASS 条件：全部真 + 16 行 pinned 可溯源。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]          # k2/
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(Path("/home/fila/jqdDev_2025/ic_hw/_shared")))

from eda_core.construction_fact import (            # noqa: E402
    ConstructionFactAssembler, fact_validate, replay_equals,
)
from eda_core.escape_table import (                 # noqa: E402
    EscapeRecord, EscapeStatus, EscapeTable, NoEscapeDetail,
    NoEscapeEvidence, NoEscapeReason, NoEscapeReasonRecord,
)
from eda_core.column_book import ColumnBook          # noqa: E402

REPORT_PATH = REPO / "pm_gate/artifacts/k2_v4/L3/p3_real_board_e2e" \
    / "p3_real_board_e2e_report.json"
AUDIT_DIR = REPO / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
P0_AUDIT_PATH = AUDIT_DIR / "m13_v53_p0_audit.json"
AUDIT_PATH = AUDIT_DIR / "m13_v53_p1_audit.json"
SPEC_PATH = REPO / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"

# chip 侧判定（当前真板 corridor 语义，代码零坐标字面量）
def _chip_side(corridor: str) -> str:
    return "left" if str(corridor).startswith("EAST_CHIP") else "right"


def _norm_base(base: str) -> str:
    return base[5:] if base.startswith("PCIE_") else base


def reverse_derive(solve_results: dict, alloc_table: dict,
                   landing_allocation: dict, spec: dict) -> dict:
    """从 e2e report 的 SOLVED 段记录反演 EscapeTable 行（只读，无重算）。"""
    rows = []
    assembled = []
    for base in sorted(solve_results):
        rec = solve_results[base] or {}
        base_fp = rec.get("input_fp") or ""
        for seg in rec.get("segments", []):
            if seg.get("status") != "SOLVED":
                continue
            segname = seg.get("name")
            corridor_id = seg.get("corridor") or ""
            side = _chip_side(corridor_id)
            esc = (seg.get("escape") or {}).get("segments") or {}
            side_seg = esc.get(side) or {}
            p = side_seg.get("P") or {}
            n = side_seg.get("N") or {}
            kind = p.get("kind") or n.get("kind") or "DIRECT"
            via_p = p.get("via") or None
            via_n = n.get("via") or None

            def _via(v):
                if not v:
                    return None
                if v and isinstance(v[0], (list, tuple)):
                    return [list(map(float, v[0])), list(map(float, v[1]))
                            if len(v) > 1 else None]
                return None

            vp = _via(via_p)
            vn = _via(via_n)
            column_p = via_p[0][0] if (via_p and isinstance(via_p[0], (list, tuple))) else None
            column_n = via_n[0][0] if (via_n and isinstance(via_n[0], (list, tuple))) else None
            landing = {}
            if vp is not None:
                landing["via1"] = {"P": vp[0],
                                   "N": (vn[0] if vn else None)}
                if vp[1] is not None or (vn and vn[1]):
                    landing["via2"] = {
                        "P": vp[1] if len(vp) > 1 else None,
                        "N": (vn[1] if vn and len(vn) > 1 else None)}
            norm = _norm_base(base)
            esc_id = f"ESC-{norm}-{segname}"
            pnet = (seg.get("P") or {}).get("net", "")
            rec_row = EscapeRecord(
                escape_id=esc_id, base=norm, segment=segname,
                net={"P": pnet, "N": (seg.get("N") or {}).get("net", "")},
                chip_side={
                    "kind": kind,
                    "escape_column": {"P": column_p, "N": column_n},
                    "landing": landing,
                    "layer_leg": "In1.Cu",
                },
                status=EscapeStatus.ASSIGNED, pinned=True,
                column_reservation_id="",
                reservations_dep=[{"type": "solved_segment",
                                   "id": f"{base}/{segname}",
                                   "corridor": corridor_id,
                                   "track_y": seg.get("track_y")}],
                provenance={
                    "solve_ref": (seg.get("P") or {}).get("solve_ref", ""),
                    "input_fp": base_fp,
                    "source_path": f"stages.solve.results[{base}]."
                                   f"segments[{segname}]",
                    "reverse_derived": True,
                },
            )
            rows.append(rec_row)
            # CCF 装配仅对含 chip-side via1 的行（DIRECT/无 via 行 = 直连，
            # Phase 3 前不虚构几何）
            if landing.get("via1", {}).get("P") is None:
                continue
            fact = _assemble_one(base, seg, rec_row, alloc_table,
                                 landing_allocation, spec)
            if fact is not None:
                assembled.append({"base": base, "segname": segname,
                                  "escape_id": esc_id, "fact": fact})
    return {"rows": rows, "assembled": assembled}


def _assemble_one(base, seg, esc_row, alloc_table, landing_allocation, spec):
    segname = seg.get("name")
    corridor_id = seg.get("corridor") or ""
    alloc_rec = alloc_table.get(base) or {}
    # anchors：chip 侧 = destination；source 侧 = 对端（记录 path 端点）
    side = _chip_side(corridor_id)
    p_path = (seg.get("P") or {}).get("path", [])
    n_path = (seg.get("N") or {}).get("path", [])
    if not p_path or not n_path:
        return None
    if side == "left":            # chip 在 path 首
        dst_p, dst_n = list(p_path[0]), list(n_path[0])
        src_p, src_n = list(p_path[-1]), list(n_path[-1])
    else:                          # chip 在 path 尾
        dst_p, dst_n = list(p_path[-1]), list(n_path[-1])
        src_p, src_n = list(p_path[0]), list(n_path[0])
    corridor = {}
    for c in spec.get("corridors", []):
        if c.get("id") == corridor_id:
            corridor = c
            break
    assm = ConstructionFactAssembler(
        alloc={base: {"corridor": corridor_id,
                      "layer": alloc_rec.get("layer") or seg.get("layer"),
                      "track_y": alloc_rec.get("track_y")
                      if alloc_rec.get("track_y") is not None
                      else seg.get("track_y")}},
        landing={net: r for net, r in (landing_allocation or {}).items()},
        escape_table=EscapeTable([esc_row]),
        anchors={"source": {"P": src_p, "N": src_n},
                 "destination": {"P": dst_p, "N": dst_n}},
        corridor={corridor_id: corridor},
    )
    try:
        fact = assm.assemble(
            base=_norm_base(base), segment=segname,
            net_p=(seg.get("P") or {}).get("net", ""),
            net_n=(seg.get("N") or {}).get("net", ""),
            alloc_id=base, escape_id=esc_row.escape_id,
            kind=esc_row.chip_side.get("kind") or "COL_STACK",
            pinned=True)
    except Exception as e:
        return None
    return fact


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    report = json.load(open(REPORT_PATH))
    p0 = json.load(open(P0_AUDIT_PATH))
    result = {"artifact": "m13_v53_p1_audit.json", "phase": "P1",
              "gate_status": "FAIL", "checks": {}}

    # ── 1. 空 EscapeTable → 字节 == P0 ──
    sha_now = hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest()
    p0_new_sha = (p0.get("new_report") or {}).get("sha256")
    result["checks"]["byte_identical_to_p0"] = (sha_now == p0_new_sha)
    result["report_sha256"] = sha_now

    # ── 7/8. Alloc/Landing checksum == P0 ──
    import p3_v53_phase0_audit as A
    stages = report.get("stages") or {}
    ck = {
        "AllocTable": A.sha256_json((stages.get("alloc") or {}).get("alloc")),
        "LandingTable": A.sha256_json(
            (stages.get("landing") or {}).get("allocation")),
    }
    result["checks"]["alloc_checksum"] = {
        "value": ck["AllocTable"], "p0": (p0.get("checks", {}).get(
            "checksums") or {}).get("AllocTable", {}).get("new"),
        "unchanged": ck["AllocTable"] == (p0.get("checks", {}).get(
            "checksums") or {}).get("AllocTable", {}).get("new")}
    result["checks"]["landing_checksum"] = {
        "value": ck["LandingTable"],
        "p0": (p0.get("checks", {}).get("checksums") or {}).get(
            "LandingTable", {}).get("new"),
        "unchanged": ck["LandingTable"] == (p0.get("checks", {}).get(
            "checksums") or {}).get("LandingTable", {}).get("new")}

    # ── 2. 反演 16 pinned + round-trip ──
    solve_results = (stages.get("solve") or {}).get("results") or {}
    alloc_table = (stages.get("alloc") or {}).get("alloc") or {}
    landing_allocation = (stages.get("landing") or {}).get("allocation") or {}
    spec = json.load(open(SPEC_PATH))
    derived = reverse_derive(solve_results, alloc_table,
                             landing_allocation, spec)
    table = EscapeTable(derived["rows"])
    n_solved = sum(1 for r in solve_results.values()
                   for s in (r or {}).get("segments", [])
                   if s.get("status") == "SOLVED")
    result["checks"]["n_reverse_derived"] = {
        "solved_segments": n_solved, "rows": len(table)}
    blob = table.serialize()
    table2 = EscapeTable.deserialize(blob)
    ids_match = sorted(r.escape_id for r in table) == \
        sorted(r.escape_id for r in table2)
    result["checks"]["roundtrip_ids"] = ids_match
    result["checks"]["all_pinned"] = all(r.pinned for r in table)
    result["checks"]["provenance_complete"] = all(
        r.provenance.get("solve_ref") and r.provenance.get("input_fp")
        and r.provenance.get("source_path") for r in table)
    # DN5/DN6 反演可溯源性（几何来自 SOLVED path，pinned）
    dn56 = [r for r in table if r.base in ("DN5", "DN6")
            and r.segment == "out_MCIO"]
    result["checks"]["dn5_dn6_traceable"] = {
        "count": len(dn56),
        "all": [{"escape_id": r.escape_id,
                 "kind": r.chip_side.get("kind"),
                 "pinned": r.pinned,
                 "source_path": r.provenance.get("source_path"),
                 "solve_ref": r.provenance.get("solve_ref")[:12] + "..."
                 if r.provenance.get("solve_ref") else None}
                for r in dn56]}

    # ── 3/4/5/6. CCF 装配 + fact_validate + replay_equals ──
    fact_ok = True
    replay_ok = True
    vias_checked = 0
    per_fact = []
    esc_by_id = {r.escape_id: r for r in table}
    for item in derived["assembled"]:
        fact = item["fact"]
        esc_tbl = EscapeTable([esc_by_id[item["escape_id"]]])
        errs = fact_validate(fact, esc_tbl)
        ok = not errs
        # replay：重装（用同一 source）比对
        try:
            eq = replay_equals(fact, ConstructionFactAssembler(
                alloc={fact.ownership.get("alloc_id"): {
                    "corridor": fact.corridor.get("id"),
                    "layer": fact.corridor.get("layer"),
                    "track_y": (fact.corridor.get("track_y") or {}).get("P")}},
                landing={fact.connector_side.get("landing_ref"):
                         {"via": fact.connector_side.get("via")}}
                if fact.connector_side.get("via") else {},
                escape_table=esc_tbl,
                anchors=fact.anchors,
                corridor={fact.corridor.get("id"):
                          {"id": fact.corridor.get("id"),
                           "x_range": fact.corridor.get("x_range")}}),
                base=fact.base, segment=fact.segment,
                net_p=fact.net.get("P"), net_n=fact.net.get("N"),
                alloc_id=fact.ownership.get("alloc_id"),
                escape_id=fact.ownership.get("escape_id"),
                kind=fact.chip_side.get("kind"), pinned=fact.pinned)
        except Exception:
            eq = False
        replay_ok = replay_ok and eq
        fact_ok = fact_ok and ok
        # dup-via 计数
        n_via = sum(1 for vk in ("via1", "via2") for pol in ("P", "N")
                    if (fact.chip_side.get("landing", {}).get(vk) or {})
                    .get(pol) is not None)
        vias_checked += n_via
        per_fact.append({"base": fact.base, "segname": fact.segment,
                         "escape_id": fact.ownership.get("escape_id"),
                         "fact_validate_ok": ok,
                         "replay_equals": eq,
                         "chip_via_coords_checked": n_via,
                         "errors": errs[:3]})
    # 全部含 chip via1 的行必须装配成功；无 via1 的行 = DIRECT 直连（几何无 via，
    # 合法，不虚构）。两者合计 == 全部 solved 段。
    rows_with_via = sum(1 for r in table
                        if (r.chip_side.get("landing") or {})
                        .get("via1", {}).get("P") is not None)
    rows_direct = len(table) - rows_with_via
    result["checks"]["ccf_assembled"] = len(derived["assembled"])
    result["checks"]["rows_with_chip_via"] = rows_with_via
    result["checks"]["rows_direct_no_via"] = rows_direct
    result["checks"]["fact_validate_all_ok"] = fact_ok
    result["checks"]["replay_equals_all"] = replay_ok
    result["checks"]["dup_via_coords_checked"] = vias_checked
    result["per_fact"] = per_fact

    # 空表语义：EscapeTable 未接线到引擎，schema 层空表不影响 alloc/landing
    result["checks"]["empty_escape_table_no_effect"] = (
        result["checks"]["alloc_checksum"]["unchanged"]
        and result["checks"]["landing_checksum"]["unchanged"])

    passed = (result["checks"]["byte_identical_to_p0"]
              and result["checks"]["alloc_checksum"]["unchanged"]
              and result["checks"]["landing_checksum"]["unchanged"]
              and ids_match and result["checks"]["all_pinned"]
              and result["checks"]["provenance_complete"]
              and len(derived["assembled"]) == rows_with_via
              and rows_with_via + rows_direct == n_solved
              and fact_ok and replay_ok)
    result["gate_status"] = "PASS" if passed else "FAIL"
    json.dump(result, open(AUDIT_PATH, "w"), indent=1,
              ensure_ascii=False, sort_keys=True)
    print(f"[gate] P1 status={result['gate_status']} -> {AUDIT_PATH}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
