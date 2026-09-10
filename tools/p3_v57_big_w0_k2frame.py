#!/usr/bin/env python3
"""P3 v57 BIG — W0：真实 K2 走廊 lane 帧派生 + 证书 + 旧 SPEC 差异表。

输入白名单（单向只读）：board outline(SPEC) + 端点锚(page_manifest 连接器 pad 行)
+ 规则(pitch 1.46/margin 0.6) + 布局冻结(层栈 6L)。禁板铜扫描/禁 x-window/禁反猜。
带锚裁决(设计 §7 默认, 已文档化)：连接器行簇为刚性锚 —— 北带锚 min 行、南带锚
max 行，向走廊内以 1.46 等距铺设；带间 gap<1.46 时向北带外延(E)补足；越板框→证书。
REFCLK 行落在数据带内 → In2 无法与数据 lane 同时隔离 → 量化证书(缺独立路由资源)。
可达准入(refinement-1)：lane 与其带锚行距离 ≤ LEG(12mm, 声明预算)。
"""
import hashlib
import json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
OUT = STEP2 / "m13_v57_big_w0_k2frame.json"
P, MARGIN, LEG = 1.46, 0.6, 12.0


def main() -> int:
    spec = json.load(open(SPEC))
    mf = json.load(open(MANIFEST))
    y_lo, y_hi = spec["board"]["outline_y"]
    inner = [y_lo + 0.3, y_hi - 0.3]
    groups = {}
    for pg in mf["pages"]:
        if pg["kind"] != "data":
            continue
        c = pg["corridor"]
        g = groups.setdefault((c["id"], c["band"]), {"rows": [], "n": 0})
        g["n"] += 1
        for pol in ("P", "N"):
            g["rows"].append(pg["anchors"]["conn"][pol]["pad_global"][1])
    refclk = {pg["page_id"]: pg for pg in mf["pages"]
              if pg["kind"] == "refclk_pass"}

    frames, certs = {}, []
    for cid in ("EAST_CHIP_TO_J2", "WEST_MCIO_TO_CHIP"):
        bands = {b: groups[(cid, b)] for b in ("up", "dn")
                 if (cid, b) in groups}
        if len(bands) != 2:
            certs.append({"corridor": cid, "kind": "band_missing",
                          "have": sorted(bands)})
            continue
        up, dn = bands["up"], bands["dn"]
        north = up if min(up["rows"]) < min(dn["rows"]) else dn
        south = dn if north is up else up
        nN, nS = north["n"], south["n"]
        aN, aS = min(north["rows"]), max(south["rows"])
        lanesN = [round(aN + i * P, 3) for i in range(nN)]
        lanesS = [round(aS - i * P, 3) for i in range(nS)]
        gap = min(lanesS) - max(lanesN)
        ext = 0.0
        if gap < P - 1e-9:
            ext = round(P - gap, 3)
            lanesN = [round(y - ext, 3) for y in lanesN]
            gap = min(lanesS) - max(lanesN)
        lo_lane, hi_lane = min(lanesN + lanesS), max(lanesN + lanesS)
        if lo_lane < inner[0] or hi_lane > inner[1]:
            certs.append({"corridor": cid, "kind": "out_of_board",
                          "lo": lo_lane, "hi": hi_lane, "inner": inner})
            continue
        reach = {"north_max_row": aN, "south_min_row": aS,
                 "max_leg_mm": round(max(abs(aN - max(lanesN)),
                                         abs(aS - min(lanesS))), 3),
                 "budget_mm": LEG,
                 "ok": abs(aN - max(lanesN)) <= LEG and
                 abs(aS - min(lanesS)) <= LEG}
        frames[cid] = {"up": sorted(lanesN) if north is up
                       else sorted(lanesS),
                       "dn": sorted(lanesS) if north is up
                       else sorted(lanesN),
                       "north_band": "up" if north is up else "dn",
                       "gap_mm": round(gap, 3), "extend_north_mm": ext,
                       "reach": reach}
        # REFCLK: J2 行是否落在数据带行区(→In2 无法隔离)
        for pid, pg in sorted(refclk.items()):
            j2y = pg["anchors"]["conn2"]["P"]["pad_global"][1]
            inside = (min(min(north["rows"]), min(south["rows"])) <= j2y <=
                      max(max(north["rows"]), max(south["rows"])))
            if inside:
                certs.append({"corridor": cid, "kind": "refclk_band",
                              "page": pid, "j2_row": round(j2y, 3),
                              "reason": "REFCLK J2 行落数据带行区, In2 无 ≥1.46 "
                                        "隔离位 → 缺 1 条独立路由资源"})

    old = {}
    for c in spec["corridors"]:
        for b in c["bands"]:
            old[f"{c['id']}/{b['band']}"] = {"layer": b["layer"],
                                             "tracks_y": b["tracks_y"]}
    diff = {}
    for k, v in old.items():
        cid, band = k.split("/")
        new = frames.get(cid, {}).get(band)
        diff[k] = {"old_layer": v["layer"], "old_tracks": v["tracks_y"],
                   "new_tracks": new,
                   "old_layer_valid_6L": v["layer"] not in
                   ("In6.Cu", "In7.Cu", "In8.Cu")}
    rep = {"artifact": "m13_v57_big_w0_k2frame",
           "predicate": "W0 真实 K2 lane 帧派生 + 证书 + 旧 SPEC 差异表",
           "board_inner_y": inner, "pitch": P, "margin": MARGIN,
           "frames": frames, "certificates": certs, "diff_vs_old_spec": diff,
           "inputs_sha": {"manifest": hashlib.sha256(
               MANIFEST.read_bytes()).hexdigest()[:12]},
           "verdict": "FEASIBLE_DATA + REFCLK_CERT" if frames and certs
           else ("FEASIBLE" if frames else "CERTIFICATE")}
    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    for cid, f in frames.items():
        print(cid, "up", f["up"], "dn", f["dn"], "gap", f["gap_mm"],
              "ext", f["extend_north_mm"], "reach_ok", f["reach"]["ok"])
    for c in certs:
        print("CERT", json.dumps(c, ensure_ascii=False)[:160])
    print("verdict:", rep["verdict"], "artifact:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
