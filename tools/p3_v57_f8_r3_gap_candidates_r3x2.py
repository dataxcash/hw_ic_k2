#!/usr/bin/env python3
"""P3 v57 F8-R3X2 — ROOT-17(②): 连接器落段展开（版本化域修订件，旧件不动）。

在 J2X1 基础上，把 J3/J4 每个 pad 列的多个 net 也各给**互异逃逸槽**（落段不再共线重叠）。
零搜索、零板读。
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
BASE = STEP2 / "m13_v57_f8_r3_gap_candidates.json"
OUT = STEP2 / "m13_v57_f8_r3_gap_candidates_r3x2.json"
PITCH = 0.6
INNER_X, OUTER_X = 132.65, 135.0
INNER_BASE, OUTER_BASE = 131.65, 136.0


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    d = json.load(open(BASE))
    src_rev = d.get("revision")
    conns = d["connectors"]
    # J2 (ROOT-16 A): inner col 向左, outer col 向右 唯一槽
    j2 = conns["J2"]
    for xc, col in j2["columns"].items():
        inner = abs(float(xc) - INNER_X) < 1e-6
        ents = sorted(col["entries"], key=lambda e: (e["y"], e["pol"], e["net"]))
        base, sgn = (INNER_BASE, -1.0) if inner else (OUTER_BASE, +1.0)
        for k, en in enumerate(ents):
            en["gap_candidates"] = [round(base + sgn * k * PITCH, 3)]
    # J3/J4 (ROOT-17 ②): 连接器**全局唯一**逃逸槽（0.6 网格，按 (pad 列 x, y, pol, net) 定序）
    for ref in ("J3", "J4"):
        if ref not in conns:
            continue
        flat = []
        for xc, col in conns[ref]["columns"].items():
            for en in col["entries"]:
                flat.append((float(xc), en["y"], en["pol"], en["net"], en))
        flat.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
        base = min(min(float(c) for c in en["gap_candidates"]) for *_, en in flat)
        for i, (*_, en) in enumerate(flat):
            en["gap_candidates"] = [round(base + i * PITCH, 3)]

    d["revision"] = "R3X2"
    d["supersedes"] = {"artifact": "m13_v57_f8_r3_gap_candidates", "revision": src_rev,
                       "note": "旧 F-8 件不动；J2X1 为中间版本"}
    d["r3x2_basis"] = {
        "authority": "ROOT-16 A + ROOT-17 ② (owner/监督预授权)",
        "change_j2": "J2 内列向左/外列向右唯一逃逸槽 (同 J2X1)",
        "change_j3j4": "J3/J4 每个 pad 列的多 net 各给互异槽 slot = min(cands) + rank*0.6",
        "pitch_mm": PITCH, "closed_form": "slot = base + rank*pitch (rank 由 (pad y, pol, net) 定序)",
        "zero_search": True}
    d["inputs_sha"] = dict(d.get("inputs_sha", {}))
    d["inputs_sha"]["f8_base_sha256"] = sha(BASE)
    OUT.write_text(json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT.name} sha={sha(OUT)[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
