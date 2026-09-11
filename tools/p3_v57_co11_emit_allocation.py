#!/usr/bin/env python3
"""CO-11：把已独立复核的 32/32 通道分配发射为**机读工件**供引擎闭式消费。

架构一致性：引擎既有契约是「离线域（F-13 pair/xorder、coherent_rows、r3_gaps）→ 闭式消费；
执行器零搜索」。本件把探针的**单遍确定性**落位（无回溯、无重试；候选按固定键序 + 可行性谓词）
固化为 `m13_v57_co11_channel_allocation.json`，引擎按 (page, pol) O(1) 取用。

只读消费：manifest / lane_frame / pair 域 v1.5 / pad field / drc_rules；不改冻结四源。
"""
from __future__ import annotations
import hashlib, json, os, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co11_channel_allocation.json"

CFG = {"CO10_PAIR": "m13_v57_f13_r1_pair_coupling_v1_5.json", "CO10_WSTEP": "1.1265", "CO10_WLO": "33.3",
       "CO10_FANY_J3": "31.5,51.5", "CO10_STUB": "J3L"}
REVISION = "CO11-ALLOC.1"


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    os.environ.update(CFG)
    import importlib.util
    spec = importlib.util.spec_from_file_location("probe", str(K2 / "tools/p3_v57_co10_west_fan_probe.py"))
    probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
    res = probe.probe(rule="fan", order="rev", verbose=False)
    if res["n_placed"] != res["n_pages"]:
        print("NOT FULLY PLACED:", res["n_failed"], res["failed"]); return 1
    G = res["geom"]
    pages = {}
    for pid, g in sorted(G.items()):
        f = probe.FACTS[pid]
        pages[pid] = {
            "page_id": pid, "corridor": f["corridor"], "conn_ref": f["conn_ref"], "band": f["band"],
            "chip_pad": {p: [round(f["pad"][p][0], 4), round(f["pad"][p][1], 4)] for p in ("P", "N")},
            "conn_pad": {p: [round(f["conn_pad"][p][0], 4), round(f["conn_pad"][p][1], 4)] for p in ("P", "N")},
            "lane_y": {p: round(probe.LANES[pid]["lane_y"] + probe.pol_off(f, p), 4) for p in ("P", "N")},
            "escape_layer": res["placed"][pid]["escape"], "stub_layer": res["placed"][pid]["stub"],
            "via1": {"P": [round(v, 4) for v in res["placed"][pid]["P_via"]],
                     "N": [round(v, 4) for v in res["placed"][pid]["N_via"]]},
            "landing": {p: [round(v, 4) for v in probe.land_meta(f)[p]] for p in ("P", "N")},
        }
    doc = {
        "artifact": "m13_v57_co11_channel_allocation", "schema": 1, "revision": REVISION,
        "status": "EMITTED", "status_kind": "VERIFIED_FULL_PLACEMENT",
        "authority": {"co11_ruling": "m13_v57_CO11_chipzone_escape_ruling.md §8（L2 四要素）"},
        "method": {"name": "single_pass_deterministic_greedy",
                   "order": "canonical reverse (corridor, conn_ref, band, page_id)",
                   "no_backtracking": True, "no_retry": True,
                   "note": "候选按固定键序；首可行即取（无回溯/无重试）。执行器（引擎）按本工件 O(1) 取用，零搜索。"},
        "config": CFG,
        "inputs_sha16": {"manifest": sha16(STEP2 / "m13_v57_s1_page_manifest.json"),
                         "lane_frame": sha16(STEP2 / "m13_v57_f3_lane_frame.json"),
                         "pair_v1_5": sha16(STEP2 / "m13_v57_f13_r1_pair_coupling_v1_5.json"),
                         "pad_field": sha16(STEP2 / "m13_v57_co09_pad_field.json")},
        "verification": {"artifact": "m13_v57_co11_placement_verification.json",
                         "sha16": sha16(STEP2 / "m13_v57_co11_placement_verification.json"),
                         "result": "n_violations=0 PASS（全对全 320 via/320 段 + 616 pad 场）"},
        "n_pages": len(pages), "pages": pages,
        "redline": "只读冻结四源；canonical W3-CN.30 未动；无 sign-off",
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"CO11-ALLOC.1: pages={len(pages)} sha16={sha16(OUT)[:16]} size={OUT.stat().st_size//1024}KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
