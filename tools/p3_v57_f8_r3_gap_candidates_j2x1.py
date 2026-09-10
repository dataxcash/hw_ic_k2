#!/usr/bin/env python3
"""P3 v57 F8-J2X1 — ROOT-16(A): 增大 J2 逃逸 x 域（版本化修订件，旧件不动）。

依据 SPEC.constraints.j2_escape_topology：
  inner_escape = 内列(132.65) 向左逃逸；outer_escape = 外列(135.0) 向右逃逸 (outer_route_x=142.5)。
做法：把 J2 每个 pad 的 gap_candidates 重写为**唯一**逃逸槽（fan 展开，pitch 0.6 ≥ 0.525），
使同一 pad 列的多个 net 各得**互异 x** -> 落段不再共线重叠。零搜索、零板读。
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
SRC = STEP2 / "m13_v57_f8_r3_gap_candidates.json"
OUT = STEP2 / "m13_v57_f8_r3_gap_candidates_j2x1.json"
PITCH = 0.6
INNER_X, OUTER_X = 132.65, 135.0
INNER_BASE, OUTER_BASE = 131.65, 136.0   # 内列向左、外列向右的第一槽


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    d = json.load(open(SRC))
    src_rev = d.get("revision")
    j2 = d["connectors"]["J2"]
    for xc, col in j2["columns"].items():
        x = float(xc)
        inner = abs(x - INNER_X) < 1e-6
        ents = sorted(col["entries"], key=lambda e: (e["y"], e["pol"], e["net"]))
        base, sgn = (INNER_BASE, -1.0) if inner else (OUTER_BASE, +1.0)
        for k, en in enumerate(ents):
            en["gap_candidates"] = [round(base + sgn * k * PITCH, 3)]

    d["revision"] = "J2X1"
    d["supersedes"] = {"artifact": "m13_v57_f8_r3_gap_candidates", "revision": src_rev,
                       "note": "旧件 m13_v57_f8_r3_gap_candidates.json 不动"}
    d["j2x1_basis"] = {
        "authority": "ROOT-16 A (owner 授权代裁)",
        "spec": "SPEC.constraints.j2_escape_topology: inner_escape=left, outer_escape=right, "
                "outer_route_x=142.5",
        "change": "仅重写 J2 各 pad 的 gap_candidates 为唯一逃逸槽 (fan, pitch 0.6)；其余连接器原样",
        "pitch_mm": PITCH, "inner_base_x": INNER_BASE, "outer_base_x": OUTER_BASE,
        "closed_form": "slot_x = base + sgn * rank_in_col * 0.6; rank 由 (pad y, pol, net) 定序",
        "zero_search": True}
    d["inputs_sha"] = dict(d.get("inputs_sha", {}))
    d["inputs_sha"]["f8_base_sha256"] = sha(SRC)
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT.name}  sha={sha(OUT)[:16]}  J2 pads={sum(len(c['entries']) for c in j2['columns'].values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
