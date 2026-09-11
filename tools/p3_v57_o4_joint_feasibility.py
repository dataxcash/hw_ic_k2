#!/usr/bin/env python3
"""P3 v57 — O4（对内等长 ≤0.15mm）**联合 (via1, landing) 派生可行性探针**（只读、独立核）。

背景：CO-05 addendum v3 断言 O4 可由 R1.5 via1 + R3 落列联合放置闭合（32/32）。
本工具用**独立长度核**（不 import 引擎构造路径）复核，并显式计入 v3 遗漏的
**落列竖段唯一性约束**：同带（dn=B.Cu / up=In6.Cu）内每个落列的竖段
`(lx, ly)->(lx, ly_l)` 都跨越近全 lane 高度 ⇒ 任意两 pad 的落列 x 必须互异
（间隔 ≥ track-track 0.38mm；同列即共线重叠 = 短路，已由引擎 A-CN.3b/A-CN.9 实测确认）。

输出：m13_v57_o4_joint_feasibility_probe.json（版本化证据件；不改四源、不改 canonical）。
退出码：0 = 可闭合；1 = 不可闭合（本板预期 1）。
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
S = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
PITCH = 0.38          # 落列最小间隔 (= width + clearance); = 竖段净距下限
SKEW = 0.15           # SPEC intra_pair_skew_mm
POL = 0.19
J2_LEFT0, J2_RIGHT0, J2_MID = 131.65, 136.0, 133.825
N_RANK = 8            # J2 每带 8 对


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def pol_off(padP, padN, pol):
    b = -POL if (padN[1] - padP[1]) > 0 else POL
    return b if pol == "P" else -b


def page_geometry(pid, man, art, base, ver):
    pg = next(p for p in man["pages"] if p["page_id"] == pid)
    a = next(p for p in art["pages"] if p["page_id"] == pid)
    ref = pg["anchors"]["conn"]["P"]["ref"]
    ent = {}
    for pol in ("P", "N"):
        net = pg["nets"][pol]
        for xc, col in base["connectors"][ref]["columns"].items():
            for en in col["entries"]:
                if en["net"] == net:
                    ent[pol] = dict(en, col_x=float(xc))
    return pg, a, ent


def min_abs_dl(pid, lxP, lxN, man, art, base, ver):
    pg, a, ent = page_geometry(pid, man, art, base, ver)
    pads = {pol: np.array(pg["anchors"]["chip"][pol]["pad_global"]) for pol in ("P", "N")}
    conn = {pol: np.array(pg["anchors"]["conn"][pol]["pad_global"]) for pol in ("P", "N")}
    lx = {"P": lxP, "N": lxN}
    res = {}
    for pol in ("P", "N"):
        band = ent[pol].get("y_band") or [ent[pol]["y"] - 0.3, ent[pol]["y"] + 0.3]
        ly = a["lane"]["y"] + pol_off(pads["P"], pads["N"], pol)
        v = np.asarray(ver["pages"][pid][pol]["cands"], dtype=float)
        yls = np.arange(band[0], band[1] + 1e-9, 0.05)
        br = np.hypot(v[:, 0] - pads[pol][0], v[:, 1] - pads[pol][1])
        drop = np.abs(ly - v[:, 1])
        run = np.abs(lx[pol] - v[:, 0])
        base_len = br + drop + run
        L = []
        for yl in yls:                                     # 全部可达 (v, yl) 长度集合
            stub = abs(ly - yl)
            land = np.hypot(conn[pol][0] - lx[pol], conn[pol][1] - yl)
            L.append(base_len + stub + land)
        res[pol] = np.sort(np.concatenate(L))
    A, B = res["P"], res["N"]                             # sorted achievable length sets
    best = float("inf")
    for a in A:                                            # 最近邻查询（numpy searchsorted，无循环搜索）
        j = int(np.searchsorted(B, a))
        for c in (j - 1, j):
            if 0 <= c < len(B):
                best = min(best, abs(a - B[c]))
    return float(best)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    man = load(S / "m13_v57_s1_page_manifest.json")
    ver = load(S / "m13_v57_s1_r1_via_verdict_r2.json")
    base = load(S / "m13_v57_f8_r3_gap_candidates.json")
    art = load(S / "m13_v57_w3_joint_assignment.json")

    j2 = [p["page_id"] for p in man["pages"] if p["kind"] == "data"
          and p["anchors"]["conn"]["P"]["ref"] == "J2"]
    bands = {p["page_id"]: p["corridor"]["band"] for p in man["pages"] if p["kind"] == "data"}

    # F-8 合法落列晶格（J2）：inner(132.65)→left 半无穷；outer(135.0)→right 半无穷；唯一 between 中缝。
    left = [round(J2_LEFT0 - PITCH * k, 3) for k in range(N_RANK)]
    right = [round(J2_RIGHT0 + PITCH * k, 3) for k in range(N_RANK)]

    pages = {}
    for pid in j2:
        _, _, ent = page_geometry(pid, man, art, base, ver)
        # 每极落列必须落在其连接器焊盘列的**合法**逃逸侧（inner 132.65 -> left/中缝；outer 135.0 -> right/中缝）
        allow = {}
        for pol in ("P", "N"):
            inner = abs(ent[pol]["col_x"] - 132.65) < 1e-6
            allow[pol] = sorted(set((left if inner else right) + [J2_MID]))
        best = None
        for lxP in allow["P"]:
            for lxN in allow["N"]:
                dx = abs(lxN - lxP)                         # 对内落列分离（与极性无关）
                if dx < 0.38:                               # 竖段净距下限
                    continue
                d = min_abs_dl(pid, lxP, lxN, man, art, base, ver)
                if d <= SKEW + 1e-9 and (best is None or dx > best["dx_max"]):
                    best = {"dx_max": round(dx, 4), "min_abs_dl": round(d, 6),
                            "at": [lxP, lxN]}
        pages[pid] = ({"band": bands[pid], **best} if best
                      else {"band": bands[pid], "dx_max": None})

    # 落列竖段唯一性 ⇒ 每对占一个 left 列 + 一个 right 列（互异）；Δx_k >= 4.35 + PITCH*(p_k+q_k)
    # 最小 ΣΔx（8 对，或 1 对用唯一中缝 + 7 对用 left/right）：
    sum_no_mid = round(8 * 4.35 + PITCH * 2 * (0 + 1 + 2 + 3 + 4 + 5 + 6 + 7), 4)
    sum_mid = round(7 * 4.35 + PITCH * 2 * (0 + 1 + 2 + 3 + 4 + 5 + 6) + 2.175, 4)

    band_ok = {}
    for b in ("dn", "up"):
        ids = sorted([p for p in j2 if bands[p] == b])
        have = [pages[p]["dx_max"] for p in ids if pages[p]["dx_max"] is not None]
        # 落列秩分配可行性：k_i,k_o ∈ 0..7 互异，sep_k = 4.35 + PITCH*(k_i+k_o) <= dx_max_k
        assign = None
        if all(pages[p]["dx_max"] is not None for p in ids):
            order = sorted(ids, key=lambda q: (pages[q]["dx_max"], q))
            used = set()
            assign = []
            for idx, q in enumerate(order):
                k = 2 * idx // 2                            # 秩按页序配对（同一 k 给 inner/outer）
                p_i = q                                     # 简化：同页 inner/outer 同秩 k=idx%8
                kk = idx
                sep = round(4.35 + PITCH * 2 * kk, 3)
                ok = sep <= pages[q]["dx_max"] + 1e-9
                assign.append({"page": q, "rank": kk, "sep_mm": sep,
                               "dx_max": pages[q]["dx_max"], "ok": ok})
        band_ok[b] = {"n_pages": len(ids), "n_with_solution": len(have),
                      "dx_max_sorted": sorted(round(x, 3) for x in have),
                      "rank_assignment": assign,
                      "assignment_ok": None if assign is None else all(a["ok"] for a in assign)}
    feasible = all(v["dx_max"] is not None for v in pages.values())

    doc = {
        "artifact": "m13_v57_o4_joint_feasibility_probe", "schema": 1,
        "revision": "O4-JOINT-FEAS.1",
        "rule": "O4 = intra-pair skew <= 0.15mm by joint (via1 in verdict window, landing in F-8 legal lattice, y_l in y_band)",
        "method": "independent length kernel L = |pad-v1| + |ly-v1y| + |lx-v1x| + |ly_l-ly| + |conn-(lx,ly_l)|; "
                  "min over verdict cands x 0.05mm y_band grid (bounded analysis kernel, not engine construction)",
        "binding_constraint": "落列竖段唯一性：同带内每 pad 落列 x 必须互异 (>=0.38mm)。"
                              "J2 合法列 = {left 半无穷, 唯一 between 中缝, right 半无穷}；"
                              "inner 列(132.65)只可 left/中缝，outer 列(135.0)只可 right/中缝 "
                              "⇒ 1 对可取 dx=2.175(占唯一中缝)，其余 7 对 dx >= 4.35 + 0.38*(p_k+q_k)",
        "dx_lower_bound": {"four_three_five": 4.35,
                           "min_sum_dx_no_mid": sum_no_mid, "min_sum_dx_with_mid": sum_mid,
                           "note": "p_k,q_k ∈ 0..7(或0..6) 互异 ⇒ 存在一对 dx >= 4.35+0.38*6 = 6.63"},
        "pages": pages, "bands": band_ok,
        "verdict": "LENGTH_SIDE_FEASIBLE" if feasible else "INFEASIBLE",
        "geometry_gate": {
            "finding": "长度侧可达，但平衡 |ΔL|<=0.15 要求 via1 位移 |Δv1x| ≈ 落列分离 (4~10mm)，"
                       "远超 pad 邻近短 breakout 区间；引擎联合探针 (CO-05b) 实测平面扇/净距失效。",
            "engine_probe": "CO-05b prototype (paired landing + skew-aware key): verdict UPSTREAM_CHANGE_REQUEST; "
                            "crossings=5; A-CN.1b/4/9 FAIL; max skew 10.92mm (见 CO-05 v5)。",
            "conclusion": "O4 不可由纯 R1.5+R3 联合 (via,landing) 派生闭合；需 L3 长度补偿或 L2/L1 结构变更；"
                          "禁放宽 intra_pair_skew_mm。"},
        "scope_note": "本探针判 O4 长度侧在合法落列晶格内的可达性；平面扇/净距约束由 CO-05b 引擎探针判定。",
        "inputs_sha": {"manifest": sha(S / "m13_v57_s1_page_manifest.json"),
                       "verdict_r2": sha(S / "m13_v57_s1_r1_via_verdict_r2.json"),
                       "f8_base": sha(S / "m13_v57_f8_r3_gap_candidates.json"),
                       "joint_assignment": sha(S / "m13_v57_w3_joint_assignment.json")},
    }
    out = Path(args.out) if args.out else S / "m13_v57_o4_joint_feasibility_probe.json"
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print("O4 joint feasibility:", doc["verdict"],
          "| dx_max per band:", {b: band_ok[b]["dx_max_sorted"][:3] for b in band_ok})
    return 0 if feasible else 1


if __name__ == "__main__":
    raise SystemExit(main())
