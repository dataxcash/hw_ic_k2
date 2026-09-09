#!/usr/bin/env python3
"""P3 v57 S1 — chip_landing_rows 发射（S2 施工消费命名空间；设计案 §5）。

来源（单向）：m13_v57_s1_r1_via_verdict.json（32 页 P/N 合法 via 对，R1 净空谓词
已验）+ m13_v57_s1_page_manifest.json（网名/pad/ball 权威锚）。零重算、零板读。

行 = {net, method:"VIA_IN2", status:"ASSIGNED", pad:[x,y], landing:{x,y},
       signal, ball, ball_grid, page_id} —— 与 solve 的 chip_landing_pair 消费
契约同构（net 级，64 数据网）。REFCLK 无芯片端不产行。
确定性：页 canonical 序 + R1 已定对。双跑字节一致。
"""
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
VERDICT = STEP2 / "m13_v57_s1_r1_via_verdict.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
OUT = STEP2 / "m13_v57_s1_chip_landing_rows.json"


def main() -> int:
    v = json.load(open(VERDICT))
    mf = json.load(open(MANIFEST))
    pages = {p["page_id"]: p for p in mf["pages"] if p["kind"] == "data"}
    rows = []
    for pid in sorted(v["pages"]):
        vp = v["pages"][pid]
        if vp["verdict"] != "ESCAPABLE":
            continue
        pg = pages[pid]
        pair = vp["pair"]
        for pol, via in zip(("P", "N"), pair):
            a = pg["anchors"]["chip"][pol]
            rows.append({"net": a["net"], "method": "VIA_IN2",
                         "status": "ASSIGNED",
                         "pad": a["pad_global"],
                         "landing": {"x": via[0], "y": via[1]},
                         "signal": a["ball"], "ball": a["ball"],
                         "ball_grid": a["ball_grid"], "page_id": pid})
    rows.sort(key=lambda r: r["net"])
    rep = {"artifact": "m13_v57_s1_chip_landing_rows",
           "n_rows": len(rows), "source": "r1_via_verdict(32/32 ESCAPABLE)",
           "rows": rows,
           "inputs_sha": {
               "verdict": hashlib.sha256(
                   VERDICT.read_bytes()).hexdigest()[:12],
               "manifest": hashlib.sha256(
                   MANIFEST.read_bytes()).hexdigest()[:12]}}
    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    nets = sorted(r["net"] for r in rows)
    print(f"rows={len(rows)}  (64 = 32 页 × P/N)")
    print("sample:", json.dumps(rows[0], ensure_ascii=False))
    print("artifact:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
