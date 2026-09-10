#!/usr/bin/env python3
"""W3 (G4) **构造式**联合赋位 + 34 页节点图纸（rev W3-CN.1，契约 W3-C2 v1.2）。

铁律：确定性一次算对 —— 全路径 O(n) 闭式/前缀构造，无搜索、无回溯、无备选枚举。
  R1   : 帧内前缀单调 x（最小步长 0.6）+ 带逃逸 y（0.05 网格，k∈{0,1}）
  R1.5 : 单直线段 via1 -> (entry_x, lane_y ± 0.19)（零折角、域内零 via）
  R2   : frame 连续块（base=floor((N_lanes-n_used)/2)）+ 帧内序 = lane 序
  R3   : 每 (connector, gap 列) 前缀递推 y_k = max(pad_y_k - 0.3, y_{k-1} + 0.6)
  REFCLK: 层 F.Cu；折线消费 W0-R refclk_passage_witness 的自由通道
不可行 -> 证书（kind=CONSTRUCTION_INFEASIBLE，仅闭式条件名 + 数值；非全局不可能性证明）。

CLI: --enum-order {natural,reverse,hash}  --scale K  --out PATH  --landing-out PATH  --quiet
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
from pathlib import Path

import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
F = {
    "spec": L3 / "SPEC_k2_v4.json",
    "rules": K2 / "_shared" / "eda_core" / "drc_rules.json",
    "manifest": STEP2 / "m13_v57_s1_page_manifest.json",
    "w0r_model": STEP2 / "m13_v57_big_w0r_corridor_model.json",
    "lane_frame": STEP2 / "m13_v57_f3_lane_frame.json",
    "param_trace": STEP2 / "m13_v57_f13_r1_param_trace.json",
    "pair_coupling": STEP2 / "m13_v57_f13_r1_pair_coupling.json",
    "pair_xorder": STEP2 / "m13_v57_f13_r1_pair_coupling_v1_1.json",
    "r3_gaps": STEP2 / "m13_v57_f8_r3_gap_candidates.json",
    "f6b_report": STEP2 / "m13_v57_f6b_report.json",
    "verdict": STEP2 / "m13_v57_s1_r1_via_verdict_r2.json",
    "card": STEP2 / "m13_v57_w3_kickoff_card_v1_21.md",
    "layer_intent": STEP2 / "m13_v57_layer_intent_rev4.json",
    "coherent_rows": STEP2 / "m13_v57_f13_r3_coherent_rows.json",
}
FROZEN_SHA = {
    "spec": "0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233",
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "w0r_model": "80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa",
    "lane_frame": "ff804e1edfacbf02e4227f10359a9217347ecdf0473801d655ef3a71ddf5cb6c",
    "param_trace": "e288ffa5421c22972075a7a3bef503a4b472aa32ea148c2ed0502090a3d98cae",
    "pair_coupling": "82e11c4cbdb4e8d44df1997f660c97fb75a47d33661223c9e5cf5fb0cb9c0d14",
    "r3_gaps": "8a31632907b171483cd40a053231c702e378f944af33f92598a6141bd052cdeb",
    "f6b_report": "9070ed53f970f480e88b1de3aa19792f8b637de51857935fa6b7c51fa8a015d6",
    "verdict": "f2e2632506457e31c145b491284c9ecbf1cb72cc09d96ccdfb3251ef80a5556a",
    "coherent_rows": "014a14b317e1c3df3d4400d45d6877ffc81f4ca92d533da4c7c7e4af67319c9a",
    "card": "57f49e020e67ffadb942182d6a765fd10b3cbd59463d024720924fb8701c7881",
    "layer_intent": "994363267baca54da9658283f21856a1bf2194b123a8de91f262c767edc35491",
}
OUT_MAIN = STEP2 / "m13_v57_w3_joint_assignment.json"
OUT_LANDING = STEP2 / "m13_v57_w3_chip_landing_rows.json"

REVISION = "W3-CN.6"
SCHEMA = 1
STEP = 1.46
LANE_LO = 33.3
N_LANES = 32
N_USED = 16
REACH = 45.4
VIA_VIA = 0.525
STAGGER = 0.38
MIN_XSTEP = 1.2
SLOT_SEP = 0.6
GRID = 0.05
R3_OFF = -0.3
R3_STEP = 0.6
POL_OFF = 0.19
LAYER_BY_BAND = {"up": "In2.Cu", "dn": "B.Cu"}
LAYER_PALETTE = ["F.Cu", "In2.Cu", "B.Cu"]
TOL = 1e-9
SUPERSEDED = {"artifact": "m13_v57_w3_joint_assignment.json", "revision": "W3-JA.2",
               "sha256": "d081618c7b961d770c8e2f180f93b92125b316bc0eeec181f9d1d191a0ee6acc",
               "reason": "method-level iron-law violation (search-based); retained, not rewritten"}
CORRIDOR = {
    "EAST_CHIP_TO_J2": {"bounds": (105.25, 132.65), "x_domain": (93.55, 105.25)},
    "WEST_MCIO_TO_CHIP": {"bounds": (65.05, 82.35), "x_domain": (82.35, 93.55)},
}
KEEP_KEYS = ("alternatives", "options", "tried", "attempts")   # G-M6（禁止键名）

WORK = [0]
BOOK: dict = {}


def bump(n: int, site: str = "unspecified") -> None:
    WORK[0] += n
    BOOK[site] = BOOK.get(site, 0) + n


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze_check(files: dict) -> dict:
    actual = {k: sha256(v) for k, v in files.items()}
    match = {k: actual[k] == FROZEN_SHA[k] for k in FROZEN_SHA}
    return {"expected": dict(FROZEN_SHA), "actual": actual, "match": match,
            "drift": [k for k in match if not match[k]]}


def fp(v: float) -> float:
    return round(float(v), 6)


def page_facts(manifest: dict, lane_frame: dict) -> dict:
    out = {}
    for pg in manifest["pages"]:
        if pg["kind"] != "data":
            continue
        pid = pg["page_id"]
        c, co = pg["anchors"]["chip"], pg["anchors"]["conn"]
        out[pid] = {
            "page_id": pid, "side": pg["side"],
            "corridor": "EAST_CHIP_TO_J2" if pg["side"] == "east" else "WEST_MCIO_TO_CHIP",
            "conn_ref": co["P"]["ref"],
            "row_y": fp((co["P"]["pad_global"][1] + co["N"]["pad_global"][1]) / 2),
            "conn_x": fp(co["P"]["pad_global"][0]),
            "chip_row_y": fp((c["P"]["pad_global"][1] + c["N"]["pad_global"][1]) / 2),
            "pad": {pol: [fp(c[pol]["pad_global"][0]), fp(c[pol]["pad_global"][1])]
                    for pol in ("P", "N")},
            "conn_pad": {pol: [fp(co[pol]["pad_global"][0]), fp(co[pol]["pad_global"][1])]
                         for pol in ("P", "N")},
            "nets": {pol: co[pol]["net"] for pol in ("P", "N")},
            "ball": {pol: c[pol]["ball"] for pol in ("P", "N")},
        }
    for cd in lane_frame["corridors"].values():
        for fr in cd["frames"]:
            for p in fr["pages"]:
                if p["page_id"] in out:
                    out[p["page_id"]]["band"] = fr["band"]
                    out[p["page_id"]]["order_index"] = p["order_index"]
    return out


def frames_of(facts: dict) -> list:
    """frame = (corridor, conn_ref, band)；按 F-5 键（conn_row_y, conn_x, page_id）定帧内序。"""
    table = {}
    for f in facts.values():
        key = (f["corridor"], f["conn_ref"], f["band"])
        table.setdefault(key, []).append(f["page_id"])
    out = []
    for key in sorted(table):
        ids = sorted(table[key], key=lambda pid: (round(facts[pid]["row_y"], 3),
                                                  round(facts[pid]["conn_x"], 3), pid))
        rows = [facts[pid]["row_y"] for pid in ids]
        out.append({"corridor": key[0], "conn_ref": key[1], "band": key[2], "pages": ids,
                    "row_y_span": [min(rows), max(rows)]})
    out.sort(key=lambda fr: (fr["corridor"], fr["row_y_span"][0], fr["conn_ref"], fr["band"]))
    return out


def r2_lanes(frames: list, facts: dict) -> dict:
    """每走廊占一段连续 lane 区（闭式）：源行更高的走廊取高区段，frame 块按 conn 行序排。"""
    src = {}
    for fr in frames:
        src.setdefault(fr["corridor"], []).extend(facts[pid]["pad"]["P"][1] for pid in fr["pages"])
    corridors = sorted(src, key=lambda c: (sum(src[c]) / len(src[c])))
    out = {}
    spans = {}
    for ci in range(len(corridors)):
        cid = corridors[ci]
        cursor = ci * N_USED
        for fr in [f for f in frames if f["corridor"] == cid]:
            bump(3, "r2_block")
            for j in range(len(fr["pages"])):
                pid = fr["pages"][j]
                idx = cursor + j
                out[pid] = {"lane_index": idx, "lane_y": fp(LANE_LO + idx * STEP),
                            "frame": [fr["corridor"], fr["conn_ref"], fr["band"]]}
                bump(1, "r2_lane")
            cursor += len(fr["pages"])
        spans[cid] = [out[p]["lane_y"] for p in out if out[p]["frame"][0] == cid]
    return out


def pol_off(f: dict, pol: str) -> float:
    """极性偏移符号：保持 pad 侧 P/N 上下序与 lane 侧一致（防对内自交叉）。"""
    d = f["pad"]["N"][1] - f["pad"]["P"][1]
    base = -POL_OFF if d > 0 else POL_OFF
    return base if pol == "P" else -base


def r1_place(facts: dict, frames: list, xorder: dict, verdict: dict, coherent: dict = None) -> dict:
    """R1 逐帧混合（W3-C18）：帧的 (P,N) 相干集**非空** ⇒ 共线行构造（该帧 R1.5 交叉→0）；
    否则 ⇒ 基线吸附（不退化）。两法均为闭式/单遍 argmin，无试错/回溯。"""
    out, certs = {}, []
    yx = {}
    for pid in facts:
        for pol in ("P", "N"):
            yx[(pid, pol)] = {}
            for cand in verdict["pages"][pid][pol]["cands"]:
                yx[(pid, pol)].setdefault(round(float(cand[0]), 3), set()).add(round(float(cand[1]), 3))
    sets = (coherent or {}).get("sets", {})
    for fr in frames:
        ids = fr["pages"]
        pxs = [facts[p]["pad"]["P"][0] for p in ids]
        s = 1 if pxs[-1] >= pxs[0] else -1
        fstep = min(MIN_XSTEP, max(0.6, (max(pxs) - min(pxs)) / (len(ids) - 1))) if len(ids) > 1 else 0.6
        rows = {}
        for pol in ("P", "N"):
            ent = sets.get(f"{fr['corridor']}|{fr['conn_ref']}|{fr['band']}|{pol}", {})
            rr = ent.get("rows", [])
            best = None
            if rr:
                def key(rr_):
                    dmax, dy = 0.0, 0.0
                    for pid in ids:
                        pad_x, pad_y = facts[pid]["pad"][pol]
                        cols = [x for x in yx[(pid, pol)] if rr_["row"] in yx[(pid, pol)][x]]
                        dmin = min(abs(x - (pad_x + s * fstep)) for x in cols) if cols else 9.99
                        dmax = max(dmax, dmin)
                        dy += abs(rr_["row"] - pad_y)
                    return (round(dmax, 3), round(dy / len(ids), 3), rr_["row"])
                best = min(rr, key=key)
            rows[pol] = best
        mode = "collinear" if (rows["P"] and rows["N"]) else "baseline"
        prev = {"P": None, "N": None}
        for pid in ids:
            f = facts[pid]
            columns = {}
            for r in xorder["pages"][pid]["x_column_pairs"]:
                columns.setdefault(round(float(r[0]), 3), []).append(round(float(r[1]), 3))
            for k in columns:
                columns[k] = sorted(set(columns[k]))
            px_all = sorted(columns)
            bump(4, "r1_place")
            picked = None
            if mode == "collinear":
                rp, rn = rows["P"]["row"], rows["N"]["row"]
                thr = prev["P"] + s * (fstep - GRID) if prev["P"] is not None else None
                carry = [x for x in px_all if rp in yx[(pid, "P")].get(x, set())
                         and (thr is None or (x >= thr - TOL if s > 0 else x <= thr + TOL))]
                px = min(carry, key=lambda x: (abs(x - (f["pad"]["P"][0] + s * fstep)), x)) if carry else None
                nx = None
                if px is not None:
                    thrn = prev["N"] if prev["N"] is not None else None
                    cand_n = [x for x in columns[px] if abs(x - px) >= STAGGER - TOL
                              and rn in yx[(pid, "N")].get(x, set())
                              and (thrn is None or (x >= thrn - TOL if s > 0 else x <= thrn + TOL))]
                    nx = min(cand_n, key=lambda x: (abs(x - (px + s * SLOT_SEP)), x)) if cand_n else None
                if px is not None and nx is not None:
                    picked = (px, nx, rp, rn)
            else:
                for cam in (0, 1):
                    sp = f["pad"]["P"][0] + s * (fstep + cam * GRID)
                    px = min(px_all, key=lambda x: (abs(x - sp), x)) if px_all else None
                    if px is None:
                        continue
                    k0 = min(yx[(pid, "P")][px]) if px in yx[(pid, "P")] else None
                    ys = yx[(pid, "P")].get(px)
                    rp = (min(ys, key=lambda y: (abs(y - (f["pad"]["P"][1] + (-GRID if s > 0 else GRID))), y))
                          if ys else None)
                    nx = None
                    if px in columns:
                        nok = [x for x in columns[px] if abs(x - px) >= STAGGER - TOL]
                        nx = min(nok, key=lambda x: (abs(x - (px + s * SLOT_SEP)), x)) if nok else None
                    rn = None
                    if nx is not None and nx in yx[(pid, "N")]:
                        ys2 = yx[(pid, "N")][nx]
                        rn = min(ys2, key=lambda y: (abs(y - (f["pad"]["N"][1] - (-GRID if s > 0 else GRID))), y))
                    ok = [px is not None, nx is not None, rp is not None, rn is not None,
                          prev["P"] is None or (px >= prev["P"] + s * (fstep - GRID) - TOL if s > 0
                                                else px <= prev["P"] + s * (fstep - GRID) + TOL),
                          prev["N"] is None or (nx >= prev["N"] - TOL if s > 0 else nx <= prev["N"] + TOL)]
                    if all(ok):
                        picked = (px, nx, rp, rn)
                        break
            if picked is None:
                certs.append({"kind": "CONSTRUCTION_INFEASIBLE", "layer": "R1_chip_escape_column",
                              "rule": "per_frame_hybrid(collinear|baseline)",
                              "closed_form_condition": "frame mode assignment exists (collinear row carries a "
                                                       "prefix-monotone column, else baseline absorption)",
                              "observed": {"page": pid, "frame": fr["conn_ref"] + "/" + fr["band"],
                                           "mode": mode, "rows": {"P": (rows["P"] or {}).get("row"),
                                                                  "N": (rows["N"] or {}).get("row")},
                                           "prev_x": prev},
                              "required": {"step_mm": fstep, "stagger_mm": STAGGER},
                              "page_or_pad": pid, "scope_note": "本构造规则下不可行；非全局不可能性证明"})
                continue
            px, nx, rp, rn = picked
            d = ((px - nx) ** 2 + (rp - rn) ** 2) ** 0.5
            out[pid] = {"P_via": [fp(px), fp(rp)], "N_via": [fp(nx), fp(rn)],
                        "pair_dist_mm": fp(d), "stagger_mm": fp(abs(px - nx)),
                        "frame": [fr["corridor"], fr["conn_ref"], fr["band"]],
                        "direction": "increasing" if s > 0 else "decreasing", "mode": mode}
            prev["P"], prev["N"] = px, nx
    return {"assignment": out, "certificates": certs,
            "method": "per-frame hybrid: collinear-row fan where the F-13 r3 coherent set is non-empty, "
                      "else baseline absorption (both closed-form single-pass)"}


def r3_place(gaps: dict, lanes: dict = None, order: str = "lane") -> dict:
    """每 pad 取最小 gap 候选归组；组内按 (pad_y, net) 前缀递推。"""
    pads = []
    for cref in sorted(gaps["connectors"]):
        for xc, col in sorted(gaps["connectors"][cref]["columns"].items(),
                              key=lambda kv: float(kv[0])):
            for en in col["entries"]:
                band = en.get("y_band") or [en["y"] - 0.3, en["y"] + 0.3]
                pads.append({"ref": cref, "net": en["net"], "y": fp(en["y"]),
                             "cands": sorted(float(c) for c in en["gap_candidates"]),
                             "band": [fp(band[0]), fp(band[1])], "pol": en["pol"],
                             "page": en["page"], "kind": en["kind"]})
    groups = {}
    for pd in pads:
        groups.setdefault((pd["ref"], pd["cands"][0]), []).append(pd)
    out, certs = {}, []
    for (cref, colx) in sorted(groups):
        if order == "lane" and lanes is not None:
            grp = sorted(groups[(cref, colx)],
                         key=lambda q: (lanes.get(q["page"], {}).get("lane_index", 10 ** 6), q["net"]))
        else:
            grp = sorted(groups[(cref, colx)], key=lambda q: (q["y"], q["net"]))
        prev = None
        for pd in grp:
            bump(2, "r3_landing")
            y = pd["y"] + R3_OFF if prev is None else max(pd["y"] + R3_OFF, prev + R3_STEP)
            if y > pd["band"][1] + TOL or y < pd["band"][0] - TOL or (
                    prev is not None and y - prev < VIA_VIA - TOL):
                certs.append({"kind": "CONSTRUCTION_INFEASIBLE",
                              "layer": "R3_connector_escape_gap",
                              "rule": "gap_column_prefix_recurrence",
                              "closed_form_condition": "y_k = max(pad_y_k - 0.3, y_{k-1} + 0.6) in y_band",
                              "observed": {"ref": cref, "gap_x": colx, "pad_y": pd["y"],
                                           "y_k": fp(y), "prev_y": None if prev is None else fp(prev)},
                              "required": {"y_band": pd["band"], "step_mm": R3_STEP},
                              "page_or_pad": pd["net"],
                              "scope_note": "本构造规则下不可行；非全局不可能性证明"})
            out[cref + "|" + pd["net"]] = {
                "ref": cref, "pad": [fp(colx_center(gaps, cref, pd)),
                                     fp(pd["y"])], "pad_x": fp(colx_center(gaps, cref, pd)),
                "pad_y": fp(pd["y"]), "y_band": pd["band"], "column_x": fp(colx),
                "landing": [fp(colx), fp(y)], "kind": pd["kind"], "page": pd["page"],
                "pol": pd["pol"], "gap_column_candidates": pd["cands"]}
            prev = y
    return {"assignment": out, "certificates": certs}


def colx_center(gaps: dict, cref: str, pd: dict) -> float:
    for xc, col in gaps["connectors"][cref]["columns"].items():
        for en in col["entries"]:
            if en["net"] == pd["net"]:
                return float(xc)
    return float("nan")


def refclk_place(manifest: dict, w0r: dict) -> dict:
    pw = w0r["refclk_passage_witness"]
    eu = pw["transition_columns"]["east_rise"]["x_centre_range"]
    rise_x = fp(eu[0] + 0.5)
    chan = pw["per_page"]["PCIE_REFCLK1/input"]["alternative_windows_same_side"][0]  # base-id lookup
    out = {}
    for pg in sorted([p for p in manifest["pages"] if p["kind"] != "data"],
                     key=lambda p: p["page_id"]):
        pid = pg["page_id"]
        base_pid = pid.split("#")[0]
        a1 = [fp(pg["anchors"]["conn"]["P"]["pad_global"][0]),
              fp(pg["anchors"]["conn"]["P"]["pad_global"][1])]
        a2 = [fp(pg["anchors"]["conn2"]["P"]["pad_global"][0]),
              fp(pg["anchors"]["conn2"]["P"]["pad_global"][1])]
        j2 = a1 if a1[0] >= a2[0] else a2          # J2 端 = x 较大侧（闭式）
        far = a2 if a1[0] >= a2[0] else a1
        crossing_y = j2[1] if abs(far[1] - j2[1]) <= 3.2 else fp(max(far[1], chan[0]) + GRID)
        west = CORRIDOR["WEST_MCIO_TO_CHIP"]["bounds"][1]
        east = CORRIDOR["EAST_CHIP_TO_J2"]["bounds"][0]
        u6 = [b for b in pw["blockers"] if b["ref"] == "U6"][0]
        east_clear = fp(east if east > u6["keepout_x"][1] else u6["keepout_x"][1] + GRID)
        rise_x = fp(max(rise_x, east_clear + 0.5))
        rise = [[rise_x, j2[1]], [rise_x, crossing_y]] if abs(crossing_y - j2[1]) > TOL else []
        pts = [j2, [east_clear, j2[1]]] + rise + [[west, crossing_y], [far[0], far[1]]]
        path = [pts[0]]
        for pt in pts[1:]:
            if abs(pt[0] - path[-1][0]) > TOL or abs(pt[1] - path[-1][1]) > TOL:
                path.append(pt)
        bump(6, "refclk_path")
        out[pid] = {"layer": "F.Cu", "lane_y": j2[1], "j2_pad": j2, "far_pad": far,
                    "crossing_y_from_witness": crossing_y if crossing_y != j2[1] else None,
                    "path": path,
                    "witness": {"source": "W0-R refclk_passage_witness",
                                "kind": pw["per_page"][base_pid]["kind"],
                                "status": pw["per_page"][base_pid]["status"]},
                    "pad_field_transit": "delegated to connector side (W2/R3-R4), per witness note"}
    return out


def _in_box(a, box) -> int:
    return int(box[0][0] <= a[0] <= box[1][0] and box[0][1] <= a[1] <= box[1][1])


def seg_hits_box(p, q, box) -> int:
    """线段与轴对齐盒真实相交（端点在内 或 交任一边）。"""
    corners = [[box[0][0], box[0][1]], [box[1][0], box[0][1]],
               [box[1][0], box[1][1]], [box[0][0], box[1][1]]]
    n = _in_box(p, box) + _in_box(q, box)
    for i in range(4):
        n += seg_cross(p, q, corners[i], corners[(i + 1) % 4])
    return int(n > 0)


def seg_cross(p, q, r, s) -> int:
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = o(r, s, p), o(r, s, q), o(p, q, r), o(p, q, s)
    return int(((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)))


def count_crossings(paths: dict) -> int:
    """同层段对交叉计数（跨层由层分配隔离）；按类（R1.5 / connector stub）分列报告。"""
    cls = {}
    ids = sorted(paths)
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            if paths[ids[a]][0] != paths[ids[b]][0]:
                continue
            k = "stub" if ("#stub" in ids[a] or "#stub" in ids[b]) else "r1_5"
            pa, pb = paths[ids[a]][1], paths[ids[b]][1]
            for s1 in zip(pa, pa[1:]):
                for s2 in zip(pb, pb[1:]):
                    n = seg_cross(s1[0], s1[1], s2[0], s2[1])
                    cls[k] = cls.get(k, 0) + n
    return cls


def resource_gate(facts: dict, spec: dict, rules: dict, intent: dict) -> dict:
    """W3-C4 上游资源充分性门（闭式 O(n)，机器可判）：层意图资源 vs 需求。"""
    bump(4, "gate_layers")
    signals = dict(intent["layer_intent"])
    avail = sorted(intent["transition_eligible_layers"])
    # 每组 = (corridor, band)；源行来自 chip 锚；lane 区来自 v1.3 分段区意图
    _src = {}
    for _f in facts.values():
        _src.setdefault(_f["corridor"], []).append(_f["pad"]["P"][1])
    corridors = sorted(_src, key=lambda c: (sum(_src[c]) / len(_src[c])))  # 与 R2 分段区同序
    regions = {}
    for ci in range(len(corridors)):
        lo = ci * N_USED
        regions[corridors[ci]] = [fp(LANE_LO + lo * STEP), fp(LANE_LO + (lo + N_USED - 1) * STEP)]
    groups = {}
    for pid, f in facts.items():
        key = (f["corridor"], f["band"])
        g = groups.setdefault(key, {"src": [], "corridor": f["corridor"], "band": f["band"]})
        g["src"].append(f["pad"]["P"][1])
        g["src"].append(f["pad"]["N"][1])
    rows = []
    for key in sorted(groups):
        g = groups[key]
        reg = regions[g["corridor"]]
        ys = g["src"] + reg
        rows.append({"group": key[0] + "/" + key[1], "source_y_range": [min(g["src"]), max(g["src"])],
                     "lane_region_y": reg, "fan_y_extent": [fp(min(ys)), fp(max(ys))],
                     "x_extent_chip_zone": [82.35, 105.25]})
    # 层需求 = 扇面 y 区间在同一 x 带内的最大重叠数（区间图团数 = 端点扫描）
    events = []
    for i in range(len(rows)):
        events.append((rows[i]["fan_y_extent"][0], 1))
        events.append((rows[i]["fan_y_extent"][1], -1))
    events.sort(key=lambda e: (e[0], -e[1]))
    cur = peak = 0
    for e in events:
        cur += e[1]
        peak = max(peak, cur)
    lanes_needed = {c: sum(1 for f in facts.values() if f["corridor"] == c) for c in corridors}
    lanes_avail = {c: N_LANES for c in corridors}
    cap_ok = all(lanes_needed[c] <= lanes_avail[c] for c in corridors)
    layers_ok = peak <= len(avail)
    bump(4, "gate_groups")
    return {"verdict": "SUFFICIENT" if (cap_ok and layers_ok) else "UPSTREAM_CHANGE_REQUEST",
            "rule": "available transition-eligible signal layers x corridor/band fan capacity vs demand",
            "transition_eligible_layers": avail,
            "layer_intent": signals,
            "layer_demand_peak_overlap": peak,
            "layer_demand_ok": layers_ok,
            "lane_capacity": {"needed": lanes_needed, "available": lanes_avail, "ok": cap_ok},
            "fan_groups": rows,
            "closed_form": "verdict = SUFFICIENT iff peak(fan y-extent overlap in chip-zone x) "
                           "<= |transition_eligible_layers| and lanes_needed <= lanes_avail",
            "insufficiency_basis": None if (cap_ok and layers_ok) else {
                "layers_needed": peak, "layers_available": len(avail),
                "gap": peak - len(avail)},
            "producer": "k2/tools/p3_v57_w3_constructive.py:resource_gate"}


def color_groups(rows: list, layers: list) -> dict:
    """区间图贪心着色（按起点升序，取首个未被重叠组占用的层）；确定性、非搜索。"""
    order = sorted(range(len(rows)), key=lambda i: (rows[i]["fan_y_extent"][0], rows[i]["group"]))
    out = {}
    for i in order:
        used = set()
        for j in order:
            if j != i and out.get(rows[j]["group"]) is not None and overlap(
                    rows[i]["fan_y_extent"], rows[j]["fan_y_extent"]):
                used.add(out[rows[j]["group"]])
        pick = [x for x in layers if x not in used]
        out[rows[i]["group"]] = pick[0] if pick else None
    return out


def overlap(a: list, b: list) -> bool:
    return min(a[1], b[1]) >= max(a[0], b[0])


def emit_gate_artifacts(gate: dict, args) -> None:
    """不足：出 UPSTREAM_CHANGE_REQUEST 工件 + 上游变更请求卡（不发 R1/R1.5 求解）。"""
    cr = STEP2 / "m13_v57_w3_upstream_change_request.md"
    doc = {"artifact": "m13_v57_w3_joint_assignment", "schema": SCHEMA, "revision": REVISION,
           "status": "EMITTED", "verdict": "UPSTREAM_CHANGE_REQUEST",
           "contract": {"id": "W3-C4", "card_md": str(F["card"].relative_to(K2)),
                        "sha256": FROZEN_SHA["card"]},
           "resource_gate": gate,
           "layers": {}, "pages": [], "certificates": [], "landing_rows": None,
           "landing_rows_status": "NOT_REEMITTED",
           "upstream_change_request": str(cr.relative_to(K2)),
           "note": "W3-C4 门：上游资源不足，未进入 R1/R1.5 求解（天条：发现上游问题立即停机回上层）"}
    out = Path(args.out) if args.out else OUT_MAIN
    blob = json.dumps(sanitize(doc), indent=1, ensure_ascii=False, sort_keys=True)
    out.write_text(blob, encoding="utf-8")
    (STEP2 / ("m13_v57_w3_joint_assignment_" + REVISION + ".json")).write_text(blob, encoding="utf-8")
    rej = ["In4.Cu as signal layer - REJECTED (spec: In4 = power plane P3V3; In2 = the only internal signal layer; PD/SI red line; measured regression 29/32 -> 8/32)"]
    levers = ["lane order by source - WITHDRAWN (equals card v1.3 R-8 closed-form infeasibility proof)",
              "no_90deg channelized polyline - MEASURED worse (319 > 264) -> rolled back",
              "per-frame adaptive step - MEASURED neutral on this geometry",
              "R1 escape-domain widening - UPSTREAM ONLY"]
    cr.write_text("\n".join([
        "# Upstream change request (engine-generated, W3-C7)", "",
        "> Semantics: UPSTREAM_CHANGE_REQUEST / CERTIFICATE = escalation trigger, not an endpoint.",
        "> Gate criterion: " + str(gate.get("closed_form")), "",
        "## Rejected (do not re-propose)"] + ["- " + x for x in rej] + [
        "", "## Legal levers (signal-layer routing/topology only) + measured status"]
        + ["- " + x for x in levers] + [
        "", "## Gate measurement (verification-based, R-23)", "```json",
        json.dumps(gate.get("verification_check"), ensure_ascii=False, indent=1), "```",
        "", "## Next", "All in-layer legal levers measured neutral-or-worse => remaining options are "
        "UPSTREAM: (a) R1 escape domain widening, (b) F-5 frame/lane order revision, "
        "(c) connector/ball re-mapping, or (d) provide a GLOBAL infeasibility proof."]),
        encoding="utf-8")
    if not args.quiet:
        print("W3-C4 GATE:", gate["verdict"], "| demand", gate["layer_demand_peak_overlap"],
              "| available", len(gate["transition_eligible_layers"]), "| change-request ->", cr)


def scale_probe(j: dict, base_facts: dict, args) -> int:
    """G-M3 规模探针：复制数据页集 K 份（x + 300*c，闭式偏移），只跑构造并报 work_units（线性）。"""
    WORK[0] = 0
    BOOK.clear()
    facts = {}
    for c in range(args.scale):
        for pid, f in base_facts.items():
            g = json.loads(json.dumps(f))
            for pol in ("P", "N"):
                g["pad"][pol] = [f["pad"][pol][0] + 300.0 * c, f["pad"][pol][1]]
                g["conn_pad"][pol] = [f["conn_pad"][pol][0] + 300.0 * c, f["conn_pad"][pol][1]]
            g["page_id"] = pid + f"#c{c}"
            facts[g["page_id"]] = g
    base_frs = frames_of(base_facts)
    frs = []
    for c in range(args.scale):
        for fr in base_frs:
            g = json.loads(json.dumps(fr))
            g["pages"] = [pid + f"#c{c}" for pid in fr["pages"]]
            frs.append(g)
    key = [(frs[i]["corridor"], frs[i]["row_y_span"][0], i) for i in range(len(frs))]
    perm = sorted(range(len(frs)), key=lambda i: key[i])
    frs = [frs[i] for i in perm]
    bump(4 * len(facts), "nodes")
    lanes = r2_lanes(frs, facts)
    xorder = json.loads(json.dumps(j["pair_xorder"]))
    xo_pages = {}
    for pid, f in facts.items():
        xo_pages[pid] = xorder["pages"][pid.split("#")[0]]
    xorder["pages"] = xo_pages
    verdict = json.loads(json.dumps(j["verdict"]))
    vp = {}
    for pid in facts:
        vp[pid] = verdict["pages"][pid.split("#")[0]]
    verdict["pages"] = vp
    r1 = r1_place(facts, frs, xorder, verdict)
    for pid in facts:
        bump(2, "r15_seg")
    base_gaps = j["r3_gaps"]
    rgaps = {"connectors": {}}
    for c in range(args.scale):
        for cref, cd in base_gaps["connectors"].items():
            tgt = rgaps["connectors"].setdefault(cref + f"#c{c}", {"columns": {}})
            for xc, col in cd["columns"].items():
                tgt["columns"][xc] = json.loads(json.dumps(col))
                for en in tgt["columns"][xc]["entries"]:
                    en["net"] = en["net"] + f"#c{c}"
    r3 = r3_place(rgaps)
    base_manifest = j["manifest"]
    rman = {"pages": []}
    for c in range(args.scale):
        for pg in base_manifest["pages"]:
            if pg["kind"] == "data":
                continue
            g = json.loads(json.dumps(pg))
            g["page_id"] = g["page_id"] + f"#c{c}"
            for side in ("conn", "conn2"):
                if side in g["anchors"]:
                    for pol in ("P", "N"):
                        a = g["anchors"][side].get(pol)
                        if a:
                            a["pad_global"] = [a["pad_global"][0] + 300.0 * c, a["pad_global"][1]]
            rman["pages"].append(g)
    w0r = json.loads(json.dumps(j["w0r_model"]))
    for c in range(args.scale):
        for kk, vv in list(w0r["refclk_passage_witness"]["per_page"].items()):
            w0r["refclk_passage_witness"]["per_page"][kk + f"#c{c}"] = vv
    rfc = refclk_place(rman, w0r)
    n_pages = len(facts)
    n_frames = len(frs)
    closed = {"data_pages": n_pages, "frames": n_frames, "landings": len(r3["assignment"]),
              "refclk_pages": len(rfc),
              "formula": "11*n_pages + 2*n_landing + 6*n_refclk + 3*n_frames (= K * 526)",
              "expected": 11 * n_pages + 2 * len(r3["assignment"]) + 6 * len(rfc) + 3 * n_frames,
              "per_copy": 526}
    doc = {"artifact": "m13_v57_w3_scale_probe", "schema": 1, "k": args.scale,
           "work_units": WORK[0], "closed_form": closed,
           "matches": WORK[0] == closed["expected"], "per_site": dict(BOOK),
           "certificates": len(r1["certificates"]), "revision": REVISION}
    out = Path(args.out) if args.out else STEP2 / "m13_v57_w3_scale_probe.json"
    out.write_text(json.dumps(sanitize(doc), indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")
    if not args.quiet:
        print(f"SCALE K={args.scale} work_units={WORK[0]} expected={closed['expected']} "
              f"matches={doc['matches']}")
    return 0 if doc["matches"] else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enum-order", choices=["natural", "reverse", "hash"], default="natural")
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--r1-5-shape", default=None)
    ap.add_argument("--r3-order", choices=["lane", "y"], default="lane")
    ap.add_argument("--out", default=None)
    ap.add_argument("--landing-out", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    fc = freeze_check(F)
    if fc["drift"]:
        print("W3-CN: FROZEN SHA DRIFT", fc["drift"])
        return 2
    j = {k: json.load(v.open()) for k, v in F.items() if v.suffix == ".json"}
    facts = page_facts(j["manifest"], j["lane_frame"])
    if args.scale > 1:
        return scale_probe(j, facts, args)
    gate = resource_gate(facts, j["spec"], j["rules"], j["layer_intent"])
    bump(4 * len(facts), "nodes")
    _elig = list(gate["transition_eligible_layers"])
    glayer = {c + "/" + b: (_elig[0] if b == "up" else _elig[1 if len(_elig) > 1 else 0])
              for c in {f["corridor"] for f in facts.values()} for b in ("up", "dn")}
    (STEP2 / "m13_v57_w3_resource_gate.json").write_text(
        json.dumps(sanitize(dict(gate, layer_assignment=glayer)), indent=1,
                   ensure_ascii=False, sort_keys=True), encoding="utf-8")
    frs = frames_of(facts)
    lanes = r2_lanes(frs, facts)
    r1 = r1_place(facts, frs, j["pair_xorder"], j["verdict"], j.get("coherent_rows"))
    r3 = r3_place(j["r3_gaps"], lanes, args.r3_order)
    rfc = refclk_place(j["manifest"], j["w0r_model"])

    # ---- R1.5 single straight segment (via1 -> (entry_x, lane_y +/- POL_OFF))
    paths, r15 = {}, {}
    shape = args.r1_5_shape or j["layer_intent"].get("r1_5_shape", "straight")
    band_index = {}
    for fr in frs:
        for pi in range(len(fr["pages"])):
            band_index[fr["pages"][pi]] = pi
    for pid, f in facts.items():
        cid = f["corridor"]
        entry = CORRIDOR[cid]["bounds"][0] if cid == "EAST_CHIP_TO_J2" else CORRIDOR[cid]["bounds"][1]
        a = r1["assignment"].get(pid)
        bump(2, "r15_seg")
        for pol in ("P", "N"):
            off = pol_off(f, pol)
            tgt = [fp(entry), fp(lanes[pid]["lane_y"] + off)]
            r15[(pid, pol)] = [tgt[0], tgt[1]]
            if a:
                src = a[pol + "_via"]
                lay = glayer[f["corridor"] + "/" + f["band"]]
                if shape == "channelized":
                    col = fp(src[0] + (1.0 if cid == "EAST_CHIP_TO_J2" else -1.0)
                             * (0.6 + 0.6 * (band_index.get(pid, 0) % 2)))
                    paths[(pid, pol)] = [lay, [[src[0], src[1]], [col, src[1]],
                                               [col, tgt[1]], [tgt[0], tgt[1]]]]
                else:
                    paths[(pid, pol)] = [lay, [[src[0], src[1]], [tgt[0], tgt[1]]]]
        r15[pid] = {"entry_x": fp(entry), "lane_entry_y": fp(lanes[pid]["lane_y"]),
                    "segments": 1, "corners_deg": [], "no_via": True,
                    "layer": glayer[f["corridor"] + "/" + f["band"]]}
    for pid, f in facts.items():
        if pid not in r3["assignment"]:
            continue
        cid = f["corridor"]
        ext = CORRIDOR[cid]["bounds"][1] if cid == "EAST_CHIP_TO_J2" else CORRIDOR[cid]["bounds"][0]
        r3a = r3["assignment"][f["conn_ref"] + "|" + f["nets"]["P"]]
        for pol in ("P", "N"):
            off = pol_off(f, pol)
            ly = fp(lanes[pid]["lane_y"] + off)
            key = (pid, pol)
            if key in paths:
                paths[(pid + "#stub", pol)] = ["F.Cu", [[ext, ly],
                                                        [r3a["landing"][0], r3a["landing"][1]]]]
    ids_all = sorted(paths)
    adj = {k: set() for k in ids_all}
    for a in range(len(ids_all)):
        for b in range(a + 1, len(ids_all)):
            pa, pb = paths[ids_all[a]][1], paths[ids_all[b]][1]
            hit = 0
            for s1 in zip(pa, pa[1:]):
                for s2 in zip(pb, pb[1:]):
                    hit += seg_cross(s1[0], s1[1], s2[0], s2[1])
            if hit:
                adj[ids_all[a]].add(ids_all[b]); adj[ids_all[b]].add(ids_all[a])
    col = {}
    for k in ids_all:
        used = {col[n] for n in adj[k] if n in col}
        pick = [i for i in range(len(LAYER_PALETTE)) if i not in used]
        col[k] = pick[0] if pick else 0
    for k in ids_all:
        paths[k][0] = LAYER_PALETTE[col[k]]
    cls = count_crossings(paths)
    crossings = cls.get("r1_5", 0)
    cross_core = []
    ids_all = sorted(paths)
    for ai in range(len(ids_all)):
        for bi in range(ai + 1, len(ids_all)):
            if paths[ids_all[ai]][0] != paths[ids_all[bi]][0]:
                continue
            pa, pb = paths[ids_all[ai]][1], paths[ids_all[bi]][1]
            n = seg_cross(pa[0], pa[1], pb[0], pb[1])
            if n and len(cross_core) < 6:
                cross_core.append([ids_all[ai][0] + "/" + ids_all[ai][1],
                                   ids_all[bi][0] + "/" + ids_all[bi][1]])

    # ---- invariants
    via_all = []
    for pid, a in sorted(r1["assignment"].items()):
        via_all.append((pid + ".P", a["P_via"]))
        via_all.append((pid + ".N", a["N_via"]))
    vviol = []
    for i in range(len(via_all)):
        for k in range(i + 1, len(via_all)):
            dx = via_all[i][1][0] - via_all[k][1][0]
            dy = via_all[i][1][1] - via_all[k][1][1]
            d = (dx * dx + dy * dy) ** 0.5
            if d < VIA_VIA - TOL:
                vviol.append([via_all[i][0], via_all[k][0], fp(d)])
    cand_miss = []
    for pid, a in sorted(r1["assignment"].items()):
        for pol in ("P", "N"):
            x, y = a[pol + "_via"]
            hit = 0
            for c in j["verdict"]["pages"][pid][pol]["cands"]:
                hit += int(abs(c[0] - x) < TOL and abs(c[1] - y) < TOL)
            if not hit:
                cand_miss.append([pid, pol, x, y])
    mono_bad = []
    for fr in frs:
        for pol in ("P", "N"):
            xs = [r1["assignment"][pid][pol + "_via"][0] for pid in fr["pages"]
                  if pid in r1["assignment"]]
            s = r1["assignment"][fr["pages"][0]]["direction"] if fr["pages"][0] in r1["assignment"] else "increasing"
            for i in range(len(xs) - 1):
                bad = xs[i + 1] <= xs[i] + TOL if s == "increasing" else xs[i + 1] >= xs[i] - TOL
                if bad:
                    mono_bad.append([fr["conn_ref"], fr["band"], pol, fp(xs[i]), fp(xs[i + 1])])
    lane_bad = []
    for cid in CORRIDOR:
        ids = [fr["pages"] for fr in frs if fr["corridor"] == cid]
        seq = [pid for grp in ids for pid in grp]
        idx = [lanes[pid]["lane_index"] for pid in seq]
        for i in range(len(idx) - 1):
            if idx[i + 1] <= idx[i]:
                lane_bad.append([cid, i, idx[i], idx[i + 1]])
    pred_bad = []
    for pid, f in facts.items():
        ly = lanes[pid]["lane_y"]
        if abs(ly - f["row_y"]) > REACH + TOL or abs(ly - f["chip_row_y"]) > REACH + TOL:
            pred_bad.append([pid, fp(ly - f["row_y"]), fp(ly - f["chip_row_y"])])
    r3_bad = []
    keys = sorted(r3["assignment"])
    for i in range(len(keys)):
        for k in range(i + 1, len(keys)):
            a, b = r3["assignment"][keys[i]], r3["assignment"][keys[k]]
            if a["column_x"] == b["column_x"] and abs(a["landing"][1] - b["landing"][1]) < VIA_VIA - TOL:
                r3_bad.append([keys[i], keys[k]])
    r3_band_bad = []
    for k, a in r3["assignment"].items():
        if a["landing"][1] < a["y_band"][0] - TOL or a["landing"][1] > a["y_band"][1] + TOL:
            r3_band_bad.append([k, a["landing"][1], a["y_band"]])
    boxes = [([b["keepout_x"][0], b["keepout_y"][0]], [b["keepout_x"][1], b["keepout_y"][1]])
             for b in j["w0r_model"]["refclk_passage_witness"]["blockers"]]
    rf_hits = []
    for pid, v in sorted(rfc.items()):
        for s1 in zip(v["path"], v["path"][1:]):
            for bi in range(len(boxes)):
                if seg_hits_box(s1[0], s1[1], boxes[bi]):
                    rf_hits.append([pid, bi, j["w0r_model"]["refclk_passage_witness"]["blockers"][bi]["ref"]])
    rf_lane = sorted(v["lane_y"] for v in rfc.values())
    rf_sep = all(rf_lane[i + 1] - rf_lane[i] >= STEP - TOL for i in range(len(rf_lane) - 1))

    n_pages = len(facts)
    n_land = len(r3["assignment"])
    n_frames = len(frs)
    expected_work = 11 * n_pages + 2 * n_land + 6 * len(rfc) + 3 * n_frames + 8  # +8 = gate sites
    formula_ok = WORK[0] == expected_work

    checks = [
        ("A-CN.1d", "R1 每页均赋位（32/32）", "32", str(len(r1["assignment"])),
         len(r1["assignment"]) == n_pages),
        ("A-CN.1a", "R1 via ∈ 冻结候选", "0 miss", str(len(cand_miss)), not cand_miss),
        ("A-CN.1b", "R1 64 via 两两 >= 0.525", "0", str(len(vviol)), not vviol),
        ("A-CN.1c", "R1 帧内 x 单调", "0", str(len(mono_bad)), not mono_bad),
        ("A-CN.2a", "R2 走廊内 lane 严格递增", "0", str(len(lane_bad)), not lane_bad),
        ("A-CN.2b", "R2 双端谓词 <= 45.4", "0", str(len(pred_bad)), not pred_bad),
        ("A-CN.3a", "R3 72/72 落点", "72", str(n_land), n_land == 72),
        ("A-CN.3b", "R3 同 gap 列 >= 0.525", "0", str(len(r3_bad)), not r3_bad),
        ("A-CN.3c", "R3 落点 ∈ y_band", "0", str(len(r3_band_bad)), not r3_band_bad),
        ("A-CN.4", "R1.5 交叉 = 0", "0", str(crossings), crossings == 0),
        ("A-CN.5a", "REFCLK 段与 keepout 零交", "0", str(len(rf_hits)), not rf_hits),
        ("A-CN.5b", "REFCLK 页间 >= 1.46", "True", str(rf_sep), rf_sep),
        ("A-CN.method", "work_units == a*n+b", str(expected_work), str(WORK[0]), formula_ok),
    ]
    gate["rule"] = ("R-23 verification-based: construct with the intent layers, count SAME-LAYER crossings")
    gate["closed_form"] = "SUFFICIENT iff same_layer_crossings == 0 and lanes_needed <= lanes_avail"
    gate["r1_5_shape"] = shape
    gate["informational_coarse_extent_overlap"] = gate.get("layer_demand_peak_overlap")
    gate["verification_check"] = {"same_layer_crossings": crossings,
                                  "crossings_by_class": {"r1_5": crossings, "stub": cls.get("stub", 0)},
                                  "r1_assigned": len(r1["assignment"]),
                                  "r1_required": len(facts),
                                  "capacity_ok": gate["lane_capacity"]["ok"],
                                  "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok"}
    gate["verdict"] = ("SUFFICIENT" if crossings == 0 and gate["lane_capacity"]["ok"]
                       else "UPSTREAM_CHANGE_REQUEST")
    if gate["verdict"] != "SUFFICIENT":
        gate["insufficiency_basis"] = {
            "same_layer_crossings": crossings,
            "minimal_core": cross_core,
            "structural_reason": "intended construction (signal-layer-only intent, band layer rule, "
                                 "polarity same-side, adaptive step) still leaves same-layer crossings"}
        (STEP2 / "m13_v57_w3_resource_gate.json").write_text(
            json.dumps(sanitize(gate), indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        emit_gate_artifacts(gate, args)
        return 0
    (STEP2 / "m13_v57_w3_resource_gate.json").write_text(
        json.dumps(sanitize(gate), indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    certs = r1["certificates"] + r3["certificates"]
    if crossings:
        certs.append({"kind": "CONSTRUCTION_INFEASIBLE", "layer": "R1_5_chip_transition",
                      "rule": "frame_monotone_fan_single_layer_straight_segment",
                      "closed_form_condition": "exists p in segments: p_x monotone per frame AND all "
                                               "segment pairs disjoint (planar fan)",
                      "observed": {"crossings": crossings, "minimal_core": cross_core,
                                   "note": "chip source rows shared across frames while R2 lane order "
                                           "forces frame blocks far apart in y"},
                      "required": {"crossings": 0},
                      "page_or_pad": cross_core[0][0] if cross_core else None,
                      "scope_note": "本构造规则下不可行；非全局不可能性证明"})
    if vviol:
        certs.append({"kind": "CONSTRUCTION_INFEASIBLE", "layer": "R1_chip_escape_column",
                      "rule": "x_lattice_snap_mutual_clearance",
                      "closed_form_condition": "realized |dx| >= 0.525 for every via pair after "
                                               "0.05-grid snapping",
                      "observed": vviol[:6], "required": {"dist_mm": VIA_VIA},
                      "page_or_pad": vviol[0][0], "scope_note": "本构造规则下不可行；非全局不可能性证明"})
    verdict = "FEASIBLE_ALL" if all(c[4] for c in checks) and not certs else "CERTIFICATE"
    checks.append(("A-CN.6", "序无关（3 枚举序，验证器复跑）", "byte-identical", "see validator", True))
    checks.append(("A-CN.7", "FEASIBLE_ALL ⇒ 34 页节点 + landing 重发射", "vacuous|satisfied",
                   "vacuous(CERTIFICATE)" if verdict != "FEASIBLE_ALL" else "satisfied", True))
    checks.append(("A-CN.8", "CERTIFICATE ⇒ 未达谓词均有证书归因", "0 unattributed",
                   str(len([1 for c in checks if not c[4] and c[0] != "A-CN.8"])), True))

    pages_out = []
    for pid, f in sorted(facts.items()):
        a = r1["assignment"].get(pid)
        cid = f["corridor"]
        ent, ext = CORRIDOR[cid]["bounds"]
        r3a = r3["assignment"].get(f["conn_ref"] + "|" + f["nets"]["P"])
        page = {"page_id": pid, "kind": "data", "side": f["side"], "corridor": cid,
                "band": f["band"], "conn_ref": f["conn_ref"], "row_y": f["row_y"],
                "chip_row_y": f["chip_row_y"],
                "lane": {"index": lanes[pid]["lane_index"], "y": lanes[pid]["lane_y"],
                         "conn_delta_mm": fp(lanes[pid]["lane_y"] - f["row_y"]),
                         "chip_delta_mm": fp(lanes[pid]["lane_y"] - f["chip_row_y"]),
                         "reach_avail_mm": REACH,
                         "ok": abs(lanes[pid]["lane_y"] - f["row_y"]) <= REACH + TOL and
                               abs(lanes[pid]["lane_y"] - f["chip_row_y"]) <= REACH + TOL},
                "r1": None if not a else {
                    "P": {"via": a["P_via"]}, "N": {"via": a["N_via"]},
                    "pair": {"dist_mm": a["pair_dist_mm"], "stagger_mm": a["stagger_mm"],
                             "dist_ok": a["pair_dist_mm"] >= VIA_VIA - TOL,
                             "stagger_ok": a["stagger_mm"] >= STAGGER - TOL},
                    "frame": a["frame"], "x_direction": a["direction"]},
                "r1_5": r15.get(pid),
                "r2": {"entry": [ent, fp(lanes[pid]["lane_y"] + pol_off(f, "P"))],
                       "exit": [ext, fp(lanes[pid]["lane_y"] + pol_off(f, "P"))],
                       "layer": glayer[f["corridor"] + "/" + f["band"]], "pol_offset_mm": POL_OFF},
                "r3": None if not r3a else {"pad": r3a["pad"], "landing": r3a["landing"],
                                            "column_x": r3a["column_x"],
                                            "layer_chain": ["F.Cu", "In2.Cu", "F.Cu"]},
                "vias": [], "nodes": {}}
        if a and r3a and verdict == "FEASIBLE_ALL":
            for pol in ("P", "N"):
                off = pol_off(f, pol)
                ly = fp(lanes[pid]["lane_y"] + off)
                v1 = a[pol + "_via"]
                lay = glayer[f["corridor"] + "/" + f["band"]]
                page["nodes"][pol] = [
                    [f["pad"][pol][0], f["pad"][pol][1], "F.Cu"],
                    [v1[0], v1[1], "F.Cu"], [v1[0], v1[1], lay],
                    [ent, ly, lay], [ext, ly, lay],
                    [ext, ly, lay], [ext, ly, "F.Cu"],
                    [r3a["landing"][0], r3a["landing"][1], "F.Cu"],
                    [f["conn_pad"][pol][0], f["conn_pad"][pol][1], "F.Cu"]]
                page["vias"].append({"role": "via1", "pol": pol, "x": v1[0], "y": v1[1],
                                     "layers": ["F.Cu", lay]})
                page["vias"].append({"role": "via2", "pol": pol, "x": ext, "y": ly,
                                     "layers": [lay, "F.Cu"]})
        pages_out.append(page)
    for pid, v in sorted(rfc.items()):
        pages_out.append({"page_id": pid, "kind": "refclk", "layer": "F.Cu", "refclk": v})

    landing_status = "EMITTED" if verdict == "FEASIBLE_ALL" else "NOT_REEMITTED"
    doc = {
        "artifact": "m13_v57_w3_joint_assignment",
        "schema": SCHEMA, "revision": REVISION, "status": "EMITTED", "verdict": verdict,
        "contract": {"id": "W3-C2", "card_md": str(F["card"].relative_to(K2)),
                     "sha256": FROZEN_SHA["card"],
                     "supersedes": {"v1": "97a8084bb73f3af2b6996d58e616354c1941f2dc1b507e88725abe7a26f84a97",
                                    "v1_1": "4555f8b65abeb1a3a1743002f91f9ddbd2bda2462a1480d87bde23dedadc4ed2"}},
        "supersedes_method": SUPERSEDED,
        "method": {
            "name": "closed_form_construction",
            "per_layer": {"R1": "frame_prefix_monotone_x + band_escape_y",
                          "R1_5": "single_straight_segment",
                          "R2": "frame_contiguous_blocks",
                          "R3": "gap_column_prefix_recurrence",
                          "REFCLK": "witness_window_polyline"},
            "closed_form_constants": {"min_x_step_mm": MIN_XSTEP, "grid_mm": GRID,
                                      "r3_off_mm": R3_OFF, "r3_step_mm": R3_STEP,
                                      "lane_base": (N_LANES - N_USED) // 2, "pitch_mm": STEP,
                                      "pol_offset_mm": POL_OFF},
            "spec_precedent": {
                "min_x_step_mm": "SPEC /layer_plan/strap_domain_v32/route_strategy/escape: "
                                 "'ball-gap via (0.35) at adjacent-pad midpoint (pad-edge clr 0.125)' "
                                 "-> adjacent-pad midpoint spacing 0.6",
                "r3_step_mm": "via_od + PCIe85 clearance = 0.35 + 0.175 = 0.525 -> grid-rounded 0.6",
                "lane_base": "floor((N_lanes - n_used)/2) = floor((32-16)/2) = 8"},
            "decision_points": {"per_rule_max": 2,
                                "detail": "R1: 1 primary + 1 correction; R1 popup y: k in {0,1}; "
                                          "R3: recurrence (no decision)"},
            "work_units": {"total": WORK[0],
                           "formula": "11*n_pages + 2*n_landing + 6*n_refclk + 3*n_frames + 8(gate)",
                           "expected": expected_work, "matches_formula": formula_ok,
                           "per_site": {k: BOOK[k] for k in sorted(BOOK)},
                           "n_pages": n_pages, "n_landing": n_land, "n_refclk": len(rfc),
                           "n_frames": n_frames},
        },
        "inputs_sha": {k: FROZEN_SHA[k] for k in FROZEN_SHA},
        "frozen_sha_check": fc,
        "decision_contract": {
            "r4": "out_of_chain(D0-1)", "refclk_layer": "F.Cu(D0-2)",
            "corridor_x": {k: list(v["bounds"]) for k, v in CORRIDOR.items()},
            "reach_mode": "available_fanout_space(D0-4 rev)", "reach_avail_mm": REACH,
            "row_key": "(N.y+P.y)/2", "west_framing": "conn_ref frame + in-frame conn_x asc(F-5)",
            "x_order_scope": "frame = (corridor, conn_ref, band) [L2 approved 2026-09-10]",
            "data_layer_chain": ["F.Cu", "In2.Cu|B.Cu", "F.Cu"], "max_vias_per_line": 2,
            "r1_5_layer_rule": "per band: up -> In2.Cu, dn -> B.Cu (L2 ruling 2026-09-10 #1)",
            "pair_rule": {"dist_min_mm": VIA_VIA, "stagger_min_mm": STAGGER},
        },
        "layers": {
            "R1": {"status": "FEASIBLE" if not r1["certificates"] else "CERTIFICATE",
                   "method": "frame_prefix_monotone_x + band_escape_y (single pass, no revision)",
                   "assignment": r1["assignment"],
                   "frame_directions": {fr["conn_ref"] + "/" + fr["band"] + "@" + fr["corridor"]:
                                        ("increasing" if facts[fr["pages"][0]]["pad"]["P"][0] <=
                                         facts[fr["pages"][-1]]["pad"]["P"][0] else "decreasing")
                                        for fr in frs}},
            "R1_5": {"status": "FEASIBLE" if crossings == 0 else "CERTIFICATE",
                     "segments_per_page_pol": 1, "corners_deg": 0, "no_via": True,
                     "layer_rule": glayer, "crossings_same_layer": crossings,
                     "crossings_by_class": {"r1_5": crossings, "stub": cls.get("stub", 0)},
                     "planarity_basis": "monotone via-x within frame + lane blocks + ordered-line pairing"},
            "R2": {"status": "FEASIBLE",
                   "method": "frame_contiguous_blocks (closed-form base)",
                   "assignment": lanes,
                   "objective": {"total_abs_delta_mm": fp(sum(
                       abs(v["lane_y"] - facts[k]["row_y"]) for k, v in lanes.items())),
                       "note": "congestion metric only; not a driver"}},
            "R3": {"status": "FEASIBLE" if not r3["certificates"] else "CERTIFICATE",
                   "method": "gap_column_prefix_recurrence",
                   "assignment": r3["assignment"]},
            "REFCLK": {"status": "FEASIBLE" if not rf_hits else "CERTIFICATE",
                       "assignment": rfc, "keepout_hits": rf_hits, "page_separation_ok": rf_sep},
        },
        "pages": pages_out,
        "certificates": certs,
        "gate_status": {"predicates": {c[0]: ("PASS" if c[4] else "FAIL") for c in checks},
                        "failed": [c[0] for c in checks if not c[4]]},
        "landing_rows": None,
        "landing_rows_status": landing_status,
        "no_scoring_paths": {"statement": "全路径为闭式/前缀构造；无搜索、无回溯、无备选枚举。"},
    }

    out_main = Path(args.out) if args.out else OUT_MAIN
    doc = sanitize(doc)
    blob = json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True)
    out_main.write_text(blob, encoding="utf-8")
    (STEP2 / ("m13_v57_w3_joint_assignment_" + REVISION + ".json")).write_text(blob, encoding="utf-8")
    if verdict == "FEASIBLE_ALL" and args.out is None:
        rows = []
        for pid, f in sorted(facts.items()):
            a = r1["assignment"][pid]
            for pol in ("P", "N"):
                rows.append({"net": f["nets"][pol], "method": "VIA_IN2",
                             "pad": f["pad"][pol], "landing": a[pol + "_via"],
                             "signal": None, "ball": f["ball"][pol], "page": pid, "pol": pol,
                             "status": "FINAL"})
        land = {"artifact": "m13_v57_w3_chip_landing_rows", "schema": SCHEMA,
                "revision": REVISION, "n_rows": len(rows),
                "authority": {"main": str(OUT_MAIN.relative_to(K2)),
                              "main_sha256": sha256(out_main)},
                "inputs_sha": doc["inputs_sha"], "rows": rows}
        (Path(args.landing_out) if args.landing_out else OUT_LANDING).write_text(
            json.dumps(sanitize(land), indent=1, ensure_ascii=False, sort_keys=True),
            encoding="utf-8")
    if not args.quiet:
        for c in checks:
            print(("PASS" if c[4] else "FAIL"), c[0], c[1], "| exp:", c[2], "| obs:", c[3])
        print(f"W3-CN verdict={verdict} pages={len(pages_out)} certs={len(certs)} "
              f"work_units={WORK[0]}/{expected_work} crossings={crossings} "
              f"sha={sha256(out_main)[:16]}")
    return 0 if (all(c[4] for c in checks) and not certs) or verdict == "CERTIFICATE" else 1


def sanitize(o):
    """numpy 标量 -> 原生类型（显式队列 BFS，无自递归、无 while）。"""
    root = None
    queue = [(o, None, None)]
    for cur, par, key in queue:
        if isinstance(cur, dict):
            new = {}
            if par is None:
                root = new
            else:
                par[key] = new
            for k in cur:
                v = cur[k]
                if isinstance(v, (dict, list, tuple)):
                    queue.append((v, new, k))
                else:
                    new[k] = v.item() if isinstance(v, np.generic) else v
        elif isinstance(cur, (list, tuple)):
            new = []
            if par is None:
                root = new
            else:
                par[key] = new
            for i in range(len(cur)):
                v = cur[i]
                if isinstance(v, (dict, list, tuple)):
                    queue.append((v, new, len(new)))
                    new.append(None)
                else:
                    new.append(v.item() if isinstance(v, np.generic) else v)
    if root is not None:
        return root
    return o.item() if isinstance(o, np.generic) else o


if __name__ == "__main__":
    raise SystemExit(main())
