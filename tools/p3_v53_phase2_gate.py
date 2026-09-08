#!/usr/bin/env python3
"""v53 Phase 2 gate — EscapeAllocator（out_MCIO 芯片侧局部列分配）真实板验收。

执行（全前台，一次性 ≤2）：
  1. 反演 pinned EscapeTable（16 行，P1 同源：几何 = report solve SOLVED path）
     → ColumnBook 只读预载（保锚 + DN5/6 已解列）
  2. 组装 DN0-7 out_MCIO 未 pinned 段请求（chip pad 从真板 U6 pad 探针；
     corridor/track/层 从 report alloc + SPEC corridor 注入）
  3. EscapeAllocator.mrv_allocate → 新 EscapeTable 行 {ASSIGNED, NO_ESCAPE}
  4. 验收：
     - EscapeTable 输出：DN5/6 out_MCIO = ASSIGNED(pinned 直填)；
       DN0-7 out_MCIO 全 ∈ {ASSIGNED, NO_ESCAPE(reason/evidence 齐)}
     - ColumnBook pinned 写操作计数 == 0
     - 无 stacked 同列 via 新登记（133.825 类列外 + 不重合 pinned via 坐标）
     - 已解 16 段字节保集合零变更（report sha == P0 golden；alloc/landing
       checksum == P0）——本 gate 不重跑引擎，只读报告比对
     - 段级真解 ≥17（DN0/1/3 ≥+1 加分非硬指标，IRG §7 P2）
  5. 产出 m13_v53_p2_audit.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]          # k2/
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(Path("/home/fila/jqdDev_2025/ic_hw/_shared")))

import p3_v53_phase0_audit as A                          # noqa: E402
import p3_v53_phase1_gate as P1                          # noqa: E402
from eda_core.column_book import ColumnBook, ObstacleBall   # noqa: E402
from eda_core.escape_allocator import (                 # noqa: E402
    EscapeAllocator, EscapeRequest,
)
from eda_core.escape_table import (                     # noqa: E402
    EscapeStatus, EscapeTable,
)
from eda_core.drc_rules import BoardParser, DRCRuleLibrary   # noqa: E402

REPORT_PATH = P1.REPORT_PATH
AUDIT_DIR = P1.AUDIT_DIR
P0_AUDIT_PATH = P1.P0_AUDIT_PATH
SPEC_PATH = P1.SPEC_PATH
AUDIT_PATH = AUDIT_DIR / "m13_v53_p2_audit.json"
PAIR_HALF = 0.19
POWER_NETS = ("GND", "P3V3", "MCU_", "VREG", "PWR_5V", "1V8", "3V3")


def _spec_corridor(spec: dict, cid: str) -> dict:
    for c in spec.get("corridors", []):
        if c.get("id") == cid:
            return c
    return {}


def _chip_pad(board, net: str) -> dict:
    for p in board.pads:
        if p.net == net and p.footprint_ref == "U6" and not p.is_tht:
            return {"x": float(p.pos[0]), "y": float(p.pos[1]),
                    "w": float(p.size[0]), "h": float(p.size[1]), "net": net}
    raise KeyError(f"U6 pad not found: {net}")


def shared_occupancy(solve_results: dict) -> list:
    """SOLVED 段几何注入（build_hs_field 清 hs 网后重建障碍，replay 口径）。"""
    out: list = []
    for base, rec in sorted(solve_results.items(),
                            key=lambda kv: A.k2_base_key(kv[0])):
        for seg in (rec or {}).get("segments", []):
            if seg.get("status") != "SOLVED":
                continue
            for pol in ("P", "N"):
                s = (seg.get(pol) or {})
                net, pts, layers = s.get("net"), s.get("path", []), \
                    s.get("layers", [])
                if not pts:
                    continue
                for i in range(len(layers) - 1):
                    if layers[i] != layers[i + 1]:
                        out.append({"kind": "via", "net": net,
                                    "x": pts[i + 1][0], "y": pts[i + 1][1]})
                for i in range(len(pts) - 1):
                    if i < len(layers):
                        out.append({"kind": "seg", "net": net,
                                    "a": pts[i], "b": pts[i + 1],
                                    "layer": layers[i]})
    return out


def build_requests(board, report, spec) -> list:
    """DN0-7 out_MCIO 未 pinned 段 → EscapeRequest（几何全注入）。"""
    stages = report.get("stages") or {}
    alloc = (stages.get("alloc") or {}).get("alloc") or {}
    solve = (stages.get("solve") or {}).get("results") or {}
    corr = _spec_corridor(spec, "WEST_MCIO_TO_CHIP")
    xr = corr.get("x_range") or [0.0, 0.0]
    edge = float(max(xr))          # 芯片侧入口边
    lo = float(min(xr))
    band_layer = corr.get("layer", "In2.Cu")
    reqs: list = []
    for k in range(8):
        rec = solve.get(f"PCIE_DN{k}") or {}
        segs = rec.get("segments", [])
        seg = next((s for s in segs if s.get("name") == "out_MCIO"), None)
        if seg is None:
            continue
        if seg.get("status") == "SOLVED":
            continue                       # DN5/6 pinned 直填，不重分
        alloc_rec = alloc.get(f"PCIE_DN_OUT{k}") or {}
        track_y = float(alloc_rec.get("track_y")
                        if alloc_rec.get("track_y") is not None
                        else seg.get("track_y", 0.0))
        net_p = (seg.get("P") or {}).get("net", f"PCIE_DN_OUT{k}_P_MCIO")
        net_n = (seg.get("N") or {}).get("net", f"PCIE_DN_OUT{k}_N_MCIO")
        reqs.append(EscapeRequest(
            base=f"DN{k}", segment="out_MCIO", net_p=net_p, net_n=net_n,
            corridor_id="WEST_MCIO_TO_CHIP", corr_edge=edge,
            corridor_lo=lo, corridor_hi=edge, track_y=track_y,
            layer_band=band_layer, layer_leg="In1.Cu", stub_layer="F.Cu",
            pad_p=_chip_pad(board, net_p), pad_n=_chip_pad(board, net_n),
            source_path=f"stages.solve.results[PCIE_DN{k}]."
                        f"segments[out_MCIO]",
            solve_ref=(seg.get("P") or {}).get("solve_ref", "")))
    return sorted(reqs, key=lambda r: r.base_num)


def preload_gnd_balls(board) -> list:
    """U6 GND/PWR ball 只读障碍（列域窗口内，逐 pad 唯一 ref）。"""
    balls = []
    for i, p in enumerate(board.pads):
        if p.footprint_ref != "U6" or p.is_tht:
            continue
        if not any(p.net.startswith(n) for n in POWER_NETS):
            continue
        if not (80.0 <= p.pos[0] <= 96.0 and 50.0 <= p.pos[1] <= 56.0):
            continue
        balls.append(ObstacleBall(
            ref=f"U6-{p.net}-{i}",
            kind="gnd_ball" if p.net.startswith("GND") else "pwr_ball",
            x=float(p.pos[0]), y=float(p.pos[1]),
            radius_mm=max(p.size) / 2.0))
    return balls


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    report = json.load(open(REPORT_PATH))
    p0 = json.load(open(P0_AUDIT_PATH))
    spec = json.load(open(SPEC_PATH))
    result = {"artifact": "m13_v53_p2_audit.json", "phase": "P2",
              "gate_status": "FAIL", "checks": {}}
    checks = result["checks"]

    # ── 0. 报告字节 == P0 golden（16 段保集合零变更的 proxy）────────
    sha_now = hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest()
    p0_sha = (p0.get("new_report") or {}).get("sha256")
    checks["report_byte_identical_p0"] = (sha_now == p0_sha)
    checks["report_sha256"] = sha_now

    # ── 1. pinned 反演（P1 同源）+ ColumnBook 预载 ─────────────────
    stages = report.get("stages") or {}
    solve_results = (stages.get("solve") or {}).get("results") or {}
    alloc_table = (stages.get("alloc") or {}).get("alloc") or {}
    landing_allocation = (stages.get("landing") or {}).get("allocation") or {}
    derived = P1.reverse_derive(solve_results, alloc_table,
                                landing_allocation, spec)
    pinned = EscapeTable(derived["rows"])
    n_solved = sum(1 for r in solve_results.values()
                   for s in (r or {}).get("segments", [])
                   if s.get("status") == "SOLVED")
    checks["pinned_rows_reverse_derived"] = len(pinned)
    checks["n_solved_report"] = n_solved

    # ── 2. allocator（真板只读探针）────────────────────────────────
    board = BoardParser(str(A.REAL_BOARD)).parse()
    rules = DRCRuleLibrary(str(A.RULES_PATH))
    mcfg = A.make_config()
    book = ColumnBook()
    for b in preload_gnd_balls(board):
        book.add_ball(b)
    occ = shared_occupancy(solve_results)
    allocator = EscapeAllocator(
        board, spec, rules, mcfg, alloc_table, landing_allocation,
        pinned, column_book=book, shared_occupancy=occ)
    allocator.requests = build_requests(board, report, spec)

    summary = allocator.mrv_allocate()
    checks["requests"] = [{"base": r.base, "segment": r.segment,
                           "net_p": r.net_p, "net_n": r.net_n,
                           "escape_id": r.escape_id}
                          for r in allocator.requests]
    checks["pinned_write_count"] = book.pinned_write_count

    # ── 3. 验收核对 ────────────────────────────────────────────────
    final_rows = {r.escape_id: r for r in pinned}         # pinned 直填
    final_rows.update(allocator.records)                  # 新产出（ASSIGNED/NO_ESCAPE）
    dn_rows = {f"ESC-DN{k}-out_MCIO": final_rows.get(f"ESC-DN{k}-out_MCIO")
               for k in range(8)}
    missing = [k for k, r in dn_rows.items() if r is None]
    checks["dn07_out_mcio_present"] = {k: (r is not None) for k, r in
                                       dn_rows.items()}
    status_ok = all(
        (r is not None and r.status in (EscapeStatus.ASSIGNED,
                                        EscapeStatus.NO_ESCAPE))
        for r in dn_rows.values())
    checks["dn07_status_in_enum"] = status_ok
    dn_detail = {}
    for k, r in dn_rows.items():
        if r is None:
            continue
        if r.status == EscapeStatus.ASSIGNED:
            dn_detail[k] = {"status": "ASSIGNED",
                            "pinned": bool(r.pinned),
                            "kind": r.chip_side.get("kind"),
                            "escape_column": r.chip_side.get(
                                "escape_column"),
                            "via1": (r.chip_side.get("landing") or {})
                            .get("via1")}
        else:
            ner = r.no_escape_reason
            dn_detail[k] = {"status": "NO_ESCAPE",
                            "reason": str(ner.reason.value),
                            "detail_code": str(ner.detail_code.value),
                            "evidence": ner.evidence.to_dict()}
    checks["dn07_outcomes"] = dn_detail
    no_esc_bad = [k for k, d in dn_detail.items()
                  if d["status"] == "NO_ESCAPE"
                  and (not d.get("reason")
                       or (d.get("evidence") or {}).get("attempted_domain")
                       is None)]
    checks["no_escape_evidence_complete"] = (not no_esc_bad)

    # DN5/6 pinned 直填保持 ASSIGNED + pinned=True
    dn56 = [dn_rows.get(f"ESC-DN{k}-out_MCIO") for k in (5, 6)]
    checks["dn56_pinned_assigned"] = all(
        r is not None and r.status == EscapeStatus.ASSIGNED and r.pinned
        for r in dn56)
    # 保锚/DN5/6 pinned 列 ColumnBook 写操作计数 == 0
    checks["pinned_write_zero"] = book.pinned_write_count == 0
    # 无 stacked 同列 via 新登记：新 via 不与 pinned via 坐标重合且列域外无登记
    pinned_via_pts = []
    for r in pinned:
        lnd = (r.chip_side or {}).get("landing") or {}
        for vk in ("via1", "via2"):
            for pol in ("P", "N"):
                c = ((lnd.get(vk) or {}).get(pol))
                if c:
                    pinned_via_pts.append((round(c[0], 4), round(c[1], 4)))
    new_vias = []
    for r in allocator.records.values():
        if r.status != EscapeStatus.ASSIGNED:
            continue
        lnd = (r.chip_side or {}).get("landing") or {}
        for vk in ("via1", "via2"):
            for pol in ("P", "N"):
                c = (lnd.get(vk) or {}).get(pol)
                if c:
                    new_vias.append({"escape_id": r.escape_id,
                                     "x": round(c[0], 4),
                                     "y": round(c[1], 4)})
    stacked_dup = [v for v in new_vias
                   if any(abs(v["x"] - px) < 1e-3 and abs(v["y"] - py) < 1e-3
                          for (px, py) in pinned_via_pts)]
    checks["new_via_count"] = len(new_vias)
    checks["no_stacked_via_on_pinned"] = (not stacked_dup)
    checks["no_133825_col_via"] = all(
        abs(v["x"] - 133.825) > 1e-6 for v in new_vias)

    # alloc/landing checksum == P0（report 只读 → 恒真，佐证零引擎改动）
    ck = {"AllocTable": A.sha256_json((stages.get("alloc") or {}).get("alloc")),
          "LandingTable": A.sha256_json(
              (stages.get("landing") or {}).get("allocation"))}
    checks["alloc_checksum_unchanged"] = ck["AllocTable"] == (
        (p0.get("checks", {}).get("checksums") or {}).get("AllocTable", {})
        .get("new"))
    checks["landing_checksum_unchanged"] = ck["LandingTable"] == (
        (p0.get("checks", {}).get("checksums") or {}).get("LandingTable", {})
        .get("new"))

    # 段级真解合计（pinned 16 + 新 ASSIGNED；≥17 加分非硬指标，IRG §7 P2）
    new_assigned = [k for k, d in dn_detail.items()
                    if d["status"] == "ASSIGNED" and not d.get("pinned")]
    checks["total_solved_ge17_info"] = {
        "pinned": len(pinned), "new_assigned": len(new_assigned),
        "total": len(pinned) + len(new_assigned)}
    checks["new_assigned"] = new_assigned

    # roundtrip + 确定性
    blob = pinned.serialize()
    blob["records"] += [r.to_dict() for r in allocator.records.values()]
    table2 = EscapeTable.deserialize(blob)
    checks["escape_table_roundtrip"] = (table2.serialize() == blob)
    try:
        checks["deterministic_assert"] = allocator.deterministic_assert()
    except Exception as e:
        checks["deterministic_assert"] = False
        checks["deterministic_error"] = f"{type(e).__name__}: {e}"

    passed = (checks["report_byte_identical_p0"]
              and len(pinned) == n_solved
              and checks["pinned_write_zero"]
              and status_ok and not missing
              and checks["no_escape_evidence_complete"]
              and checks["dn56_pinned_assigned"]
              and checks["no_stacked_via_on_pinned"]
              and checks["no_133825_col_via"]
              and checks["alloc_checksum_unchanged"]
              and checks["landing_checksum_unchanged"]
              and checks["escape_table_roundtrip"]
              and checks["deterministic_assert"])
    result["gate_status"] = "PASS" if passed else "FAIL"
    result["checksums"] = ck
    result["report_sha256"] = sha_now
    json.dump(result, open(AUDIT_PATH, "w"), indent=1,
              ensure_ascii=False, sort_keys=True)
    print(f"[gate] P2 status={result['gate_status']} -> {AUDIT_PATH}")
    for k, d in sorted(dn_detail.items()):
        print(f"  {k}: {d['status']} {d.get('kind') or d.get('reason') or ''}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
