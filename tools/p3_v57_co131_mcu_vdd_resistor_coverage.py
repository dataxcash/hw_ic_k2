#!/usr/bin/env python3
"""CO-131：`MCU_VDD_BCU_RESISTORS_IN4` 退载体前置 —— R29/R31-R34 是否已在 `MCU_VDD_WEST` 覆盖内（确定性机判）。

登记项 `bcu_policy_vs_zone_carrier:MCU_VDD_BCU_RESISTORS_IN4` 的处置要求：**先核** R29/R31-R34 落点是否已在
MCU_VDD_WEST 覆盖内，是则退役该 zone 的 B.Cu 载体声明（rev-17 已退役 —— 本件补该前置证据）。
判据（零坐标搜索，闭式）：
  1) MCU_VDD_WEST polygon（CO-117 定：x_range [49.8,57.75]，basis = 覆盖 R29/R31-R34 东缘 57.55 + POWER 0.2）；
  2) 各 target 声明 via（ppc MCU_VDD entry）/ 该 zone 声明 via / pad_pos 均须 PIP 于该 polygon，且距边 ≥ 0.2（POWER 净距）。
只读；不改 SPEC/阈值/板；本件只做覆盖机判。
CLI: python3 tools/p3_v57_co131_mcu_vdd_resistor_coverage.py
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-17.json"
REC = STEP2 / "m13_v57_co131_mcu_vdd_resistor_coverage.json"
ZONE_TGT = "MCU_VDD_BCU_RESISTORS_IN4"
HOST = "MCU_VDD_WEST"
MARGIN = 0.2
TARGETS = ("R29", "R31", "R32", "R33", "R34")


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def pip(pg, x, y):
    ins = False
    for i in range(len(pg)):
        x1, y1 = pg[i]; x2, y2 = pg[(i + 1) % len(pg)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def _host_basis(zd):
    """从 in4_band_copper_allocation_v1 里取 MCU_VDD_WEST 的归属依据（结构容错；缺则 None）。"""
    alloc = zd.get("in4_band_copper_allocation_v1") or {}
    if isinstance(alloc, dict):
        for key in ("bands", "band_allocations", "zones"):
            for item in alloc.get(key) or []:
                if isinstance(item, dict) and item.get("zone") == HOST:
                    return item.get("basis")
        for v in alloc.values():
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and item.get("zone") == HOST:
                        return item.get("basis")
    return None


def edge_dist(pg, x, y):
    best = None
    for i in range(len(pg)):
        x1, y1 = pg[i]; x2, y2 = pg[(i + 1) % len(pg)]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        d = ((x - (x1 + t * dx)) ** 2 + (y - (y1 + t * dy)) ** 2) ** 0.5
        best = d if best is None else min(best, d)
    return best


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    zd = spec["pd"]["zone_defs"]
    poly = next(z for z in zd["power_zones"] if z["zone"] == HOST)["polygon"]
    zone = next(z for z in zd["power_zones"] if z["zone"] == ZONE_TGT)
    # 收集全部『声明位置』：SPEC 内任何带 ref∈TARGETS 的 pad_pos/via_pos（含 ppc、blocked/ruling 记录）
    # + 本 zone 声明 vias。确定性遍历（键序固定），非搜索。
    pts = []

    def walk(o, path=""):
        if isinstance(o, dict):
            ref = o.get("ref")
            if ref in TARGETS:
                for key, kind in (("pad_pos", "pad"), ("via_pos", "via")):
                    v = o.get(key)
                    if isinstance(v, list) and len(v) == 2:
                        pts.append({"target": ref, "kind": f"{path}:{key}".lstrip(":"),
                                    "pos": list(map(float, v))})
            for k, v in o.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
    walk(spec)
    for i, v in enumerate(zone.get("vias") or []):
        pts.append({"target": f"zone#v{i}", "kind": "zone_via", "pos": list(map(float, v["pos"]))})
    seen, uniq = set(), []
    for r in pts:
        t = (r["target"], r["kind"], tuple(r["pos"]))
        if t not in seen:
            seen.add(t); uniq.append(r)
    pts = uniq
    missing = [ref for ref in TARGETS if not any(r["target"] == ref for r in pts)]
    for ref in missing:
        pts.append({"target": ref, "kind": "no_declared_position", "pos": None})
    rows = []
    for p in pts:
        if p["pos"] is None:
            rows.append({**p, "inside": False, "edge_mm": None, "ok": False}); continue
        x, y = p["pos"]
        ins, ed = pip(poly, x, y), edge_dist(poly, x, y)
        rows.append({**p, "inside": bool(ins), "edge_mm": round(ed, 4),
                     "ok": bool(ins and ed >= MARGIN - 1e-9)})
    teeth = {
        "T1_negative_control_outside": not pip(poly, 60.0, 40.0),
        "T2_covered_floor": len([r for r in rows if r["pos"] is not None and not r["kind"].startswith("zone")]) >= 8,
        "T3_margin_binding": MARGIN == 0.2,
    }
    ok = all(r["ok"] for r in rows) and all(teeth.values())
    verdict = ("MCU_VDD_RESISTOR_TARGETS_COVERED_BY_WEST" if ok else "COVERAGE_GAP")
    rec = {"artifact": "m13_v57_co131_mcu_vdd_resistor_coverage", "schema": 1, "revision": "CO-131.1",
           "nature": "MCU_VDD_BCU_RESISTORS_IN4 退载体前置：R29/R31-R34 是否已在 MCU_VDD_WEST 覆盖内（确定性机判）",
           "host_zone": HOST, "host_polygon": poly, "host_basis": _host_basis(zd),
           "targets": list(TARGETS), "margin_mm": MARGIN, "rows": rows,
           "n_rows": len(rows), "n_ok": sum(1 for r in rows if r["ok"]),
           "teeth": teeth, "teeth_ok": all(teeth.values()), "verdict": verdict,
           "purpose": "为 rev-17 退役该 zone 的 B.Cu 载体声明提供登记项要求的『先核覆盖』证据",
           "spec_sha16": s16(SPEC), "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
           "redline": "只读；不改 SPEC/阈值/板/冻结源；零坐标搜索"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_ok": rec["n_ok"], "n_rows": rec["n_rows"],
                      "min_edge_mm": min((r["edge_mm"] for r in rows if r["edge_mm"] is not None), default=None),
                      "teeth": teeth, "rec_sha16": s16(REC)}, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
