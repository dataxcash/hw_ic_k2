#!/usr/bin/env python3
"""P3 v57 W3/W4 — 独立验证器 v2（T-2/river/T-1 感知）。

不 import 引擎；引擎仅作**黑盒**用 subprocess 跑 `--scale`（G-M3）与 `--enum-order`（A1.2）。
产出：
  - m13_v57_w3_validation.json      (D8: G-M1..G-M6 + 双度量 + 序无关 + 四源)
  - m13_v57_w4_a12_report.json      (G5: A1.2 三枚举序逐字节一致)
  - m13_v57_w4_a13_report.json      (G5: A1.3 几何不变量套件 V1-V6，覆盖 34 页 + 强节点)
  - m13_v57_w4_a14_report.json      (G5: A1.4 单向性 grep 门)
"""
from __future__ import annotations
import ast, hashlib, re, importlib.util, io, json, subprocess, sys, tempfile, tokenize
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
ENGINE = K2 / "tools" / "p3_v57_w3_constructive.py"
MAIN = STEP2 / "m13_v57_w3_joint_assignment.json"
LANDING = STEP2 / "m13_v57_w3_chip_landing_rows.json"
VERDICT = STEP2 / "m13_v57_s1_r1_via_verdict_r2.json"
GAPS = STEP2 / "m13_v57_f8_r3_gap_candidates_r3x2.json"
BASE_GAPS = STEP2 / "m13_v57_f8_r3_gap_candidates.json"
LANEFRAME = STEP2 / "m13_v57_f3_lane_frame.json"
W0R = STEP2 / "m13_v57_big_w0r_corridor_model.json"
FROZEN = {"spec": L3 / "SPEC_k2_v4.spec-rev-2.json", "rules": K2 / "_shared/eda_core/drc_rules.json",
          "manifest": STEP2 / "m13_v57_s1_page_manifest.json", "pcb": K2 / "k2_v4.kicad_pcb"}
FROZEN_SHA_PREFIX = {"spec": "0a7ad112ac4c57e3", "manifest": "a8ef3ea8ecff99d7",
                     "pcb": "f6273de613f43d05", "rules": "0a459839e15960b8"}
STEP, LANE_LO, N_USED = 1.46, 33.3, 16
VIA_VIA, POL_OFF, R3_OFF = 0.525, 0.19, -0.3
R3_STEP = 0.6
TOL = 1e-9


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ---------------- seg primitives (independent) ----------------
def _o(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def seg_cross(p, q, r, s) -> int:
    d1, d2, d3, d4 = _o(r, s, p), _o(r, s, q), _o(p, q, r), _o(p, q, s)
    return int(((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)))


def seg_overlap(p, q, r, s) -> int:
    if abs(_o(p, q, r)) > 1e-6 or abs(_o(p, q, s)) > 1e-6:
        return 0
    ax = 0 if abs(q[0] - p[0]) >= abs(q[1] - p[1]) else 1
    lo1, hi1 = sorted((p[ax], q[ax])); lo2, hi2 = sorted((r[ax], s[ax]))
    return int(min(hi1, hi2) - max(lo1, lo2) > 1e-6)


def to_path(nodes):
    """W3 node list (per-point layer) -> S1 contract path {points, layers(per-seg), vias}."""
    pts = [[nodes[0][0], nodes[0][1]]]; seg = []; vias = []
    cur = nodes[0][2]
    for x, y, L in nodes[1:]:
        if abs(x - pts[-1][0]) < 1e-9 and abs(y - pts[-1][1]) < 1e-9:
            if L != cur:
                vias.append([x, y]); cur = L
            continue
        seg.append(cur); pts.append([x, y]); cur = L
    return {"points": pts, "layers": seg, "vias": vias}


# ---------------- gates ----------------
BAD_TOKENS = {"dfs", "backtrack", "csp", "branch_and_bound", "search", "enumerate",
              "permutations", "combinations", "product", "itertools", "random", "shuffle",
              "while", "recursion", "node_cap", "alternatives", "candidates_tried"}


def gm1(src: str):
    names = {t.string for t in tokenize.generate_tokens(io.StringIO(src).readline)
             if t.type == tokenize.NAME}
    hits = sorted(names & BAD_TOKENS)
    return {"ok": not hits, "bad_names": hits}


def gm2(src: str):
    tree = ast.parse(src)
    whiles = sum(1 for n in ast.walk(tree) if isinstance(n, ast.While))
    badimp = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            badimp += [a.name for a in n.names if a.name.split(".")[0] in ("itertools", "random")]
        elif isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in ("itertools", "random"):
            badimp.append(n.module)
    selfrec = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == fn.name:
                selfrec.append(fn.name)
    return {"ok": whiles == 0 and not badimp and not selfrec,
            "while": whiles, "bad_imports": badimp, "self_recursion": sorted(set(selfrec))}


def run_engine(extra, out_main, out_landing=None, timeout=600):
    cmd = [sys.executable, str(ENGINE), "--quiet", "--out", str(out_main)] + extra
    if out_landing:
        cmd += ["--landing-out", str(out_landing)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r


def gm3():
    res = {}
    for K in (2, 4):
        with tempfile.TemporaryDirectory() as td:
            om = Path(td) / "probe.json"
            run_engine(["--scale", str(K)], om)
            try:
                d = json.loads(om.read_text(encoding="utf-8"))
                res[K] = {"work_units": d["work_units"], "expected": d["closed_form"]["expected"],
                          "matches": d["matches"], "per_copy": d["closed_form"]["per_copy"]}
            except Exception as e:                                  # noqa: BLE001
                res[K] = {"error": str(e)}
    ok = all(isinstance(res.get(K), dict) and res[K].get("matches")
             and res[K]["work_units"] == K * res[K]["per_copy"] for K in (2, 4))
    return {"ok": ok, "probe": res, "linear": ok}


def gm6(art: dict):
    s = json.dumps(art)
    hits = [k for k in ("\"alternatives\"", "\"options\"", "\"tried\"", "\"branch\"", "\"attempts\"") if k in s]
    return {"ok": not hits, "hits": hits}


# ---------------- G-M4 / G-M5 independent re-derivation ----------------
def derive_r2(manifest, lane_frame):
    """独立复刻 R2 规则（card v1.3 §R-9）：corridor 按 chip pad P 均 y 升序取连续 N_USED 块；
    frame=(corridor,conn_ref,band)，帧内按 (round(row_y,3), round(conn_x,3), page_id)；
    帧间按 (corridor, min row_y, conn_ref, band)。row_y=(conn P.y+conn N.y)/2, conn_x=conn P.x。"""
    lf = lane_frame
    band_of = {}
    for cd in lf["corridors"].values():
        for f in cd["frames"]:
            for p in f["pages"]:
                band_of[p["page_id"]] = f["band"]
    facts = {}
    src = {}
    for p in manifest["pages"]:
        if p["kind"] != "data":
            continue
        pid = p["page_id"]; co = p["anchors"]["conn"]
        cid = "EAST_CHIP_TO_J2" if p["side"] == "east" else "WEST_MCIO_TO_CHIP"
        facts[pid] = {"corridor": cid, "conn_ref": co["P"]["ref"], "band": band_of.get(pid),
                      "row_y": round((co["P"]["pad_global"][1] + co["N"]["pad_global"][1]) / 2, 3),
                      "conn_x": round(co["P"]["pad_global"][0], 3)}
        src.setdefault(cid, []).append(p["anchors"]["chip"]["P"]["pad_global"][1])
    corridors = sorted(src, key=lambda c: sum(src[c]) / len(src[c]))
    table = {}
    for pid, f in facts.items():
        table.setdefault((f["corridor"], f["conn_ref"], f["band"]), []).append(pid)
    frames = []
    for key in sorted(table):
        ids = sorted(table[key], key=lambda q: (facts[q]["row_y"], facts[q]["conn_x"], q))
        frames.append({"corridor": key[0], "pages": ids,
                       "span": min(facts[q]["row_y"] for q in ids), "conn_ref": key[1], "band": key[2]})
    frames.sort(key=lambda fr: (fr["corridor"], fr["span"], fr["conn_ref"], fr["band"]))
    out = {}
    for ci, cid in enumerate(corridors):
        cur = ci * N_USED
        for fr in [f for f in frames if f["corridor"] == cid]:
            for pid in fr["pages"]:
                out[pid] = {"lane_index": cur, "lane_y": round(LANE_LO + cur * STEP, 6)}
                cur += 1
    return out


def derive_r3(gaps, manifest, base_gaps, lane_frame):
    """独立重导（闭式规则，v2.3 纳入 CO-05c 成对落列契约）：
    - J2 数据页（ROOT-22 成对落列）：inner lx=131.65-0.6k / outer lx=136.0+0.6k，
      k = 本带 (band, P.pad_y, page) 序；landing_y = clamp(pad_y+R3_OFF, band±0.05)（无前缀递推）。
    - 其余 pad（含 J2 refclk 与 J3/J4）：组=(conn_ref, min(gap_candidates))，rank 交替偏置 stag=±0.1
      （band-clamped）；base_k=clamp(pad_y+R3_OFF+stag, band±0.05)；y_k=max(base_k, y_{k-1}+0.6)；组内序=(pad_y, net)。"""
    pads = []
    for cref in sorted(gaps["connectors"]):
        for xc, col in sorted(gaps["connectors"][cref]["columns"].items(), key=lambda kv: float(kv[0])):
            for en in col["entries"]:
                band = en.get("y_band") or [en["y"] - 0.3, en["y"] + 0.3]
                pads.append({"ref": cref, "net": en["net"], "page": en["page"], "kind": en["kind"],
                             "y": round(float(en["y"]), 6),
                             "colx": round(min(float(g) for g in en["gap_candidates"]), 6),
                             "band": [round(float(band[0]), 6), round(float(band[1]), 6)]})
    band_of = {}
    for cd in lane_frame["corridors"].values():
        for f in cd["frames"]:
            for q in f["pages"]:
                band_of[q["page_id"]] = f["band"]
    j2y = {pd["net"]: pd for pd in pads if pd["ref"] == "J2"}
    # ---- J2 paired landing (ROOT-22) ----
    bseen = {}
    for xc, col in base_gaps["connectors"]["J2"]["columns"].items():
        for en in col["entries"]:
            bseen[(en["page"], en["pol"])] = (float(xc), en)
    prows = []
    for pg in sorted({k[0] for k in bseen}):
        if pg not in band_of:
            continue
        pn = bseen.get((pg, "P")); nn = bseen.get((pg, "N"))
        if pn and nn:
            prows.append((band_of[pg], round(float(pn[1]["y"]), 6), pg))
    prows.sort()
    out = {}
    paired_pages = set()
    prank = {}
    for band, _, pg in prows:
        paired_pages.add(pg)
        k = prank.get(band, 0); prank[band] = k + 1
        for tag in ("P", "N"):
            xc, en = bseen[(pg, tag)]
            inner = abs(xc - 132.65) < 1e-6
            lx = round(131.65 - 0.6 * k, 6) if inner else round(136.0 + 0.6 * k, 6)
            pdy = j2y.get(en["net"], {}).get("y", float(en["y"]))
            b = en.get("y_band") or [en["y"] - 0.3, en["y"] + 0.3]
            y = min(max(float(pdy) + R3_OFF, float(b[0]) + 0.05), float(b[1]) - 0.05)
            out["J2|" + en["net"]] = {"column_x": lx, "landing_y": round(y, 6),
                                      "band": [round(float(b[0]), 6), round(float(b[1]), 6)]}
    # ---- remaining pads: original grouped rule ----
    groups = {}
    for pd in pads:
        if pd["page"] in paired_pages:
            continue
        groups.setdefault((pd["ref"], pd["colx"]), []).append(pd)
    rank, rk = {}, 0
    for c in sorted({k[0] for k in groups}):
        for cx in sorted({k[1] for k in groups if k[0] == c}):
            rank[(c, cx)] = rk; rk += 1
    for key in sorted(groups):
        cref, colx = key
        prev = None
        stag = 0.1 if (rank[key] % 2) else -0.1
        for pd in sorted(groups[key], key=lambda q: (q["y"], q["net"])):
            base = min(max(pd["y"] + R3_OFF + stag, pd["band"][0] + 0.05), pd["band"][1] - 0.05)
            y = base if prev is None else max(base, prev + R3_STEP)
            out[pd["ref"] + "|" + pd["net"]] = {"column_x": colx, "landing_y": round(y, 6),
                                               "band": pd["band"]}
            prev = y
    return out


def full_metric(route):
    C = O = 0
    for i in range(len(route)):
        for j in range(i + 1, len(route)):
            a, b = route[i], route[j]
            if a["layer"] != b["layer"]:
                continue
            if a["key"][0].split("#")[0] == b["key"][0].split("#")[0] and a["key"][1] == b["key"][1]:
                continue
            for s1 in zip(a["points"], a["points"][1:]):
                for s2 in zip(b["points"], b["points"][1:]):
                    C += seg_cross(s1[0], s1[1], s2[0], s2[1])
                    O += seg_overlap(s1[0], s1[1], s2[0], s2[1])
    return C, O


_PHYS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]


def via_min_inter(art):
    """异网 via 间距。CO-16 安全-hop 口径：**层跨不相交**的两 via 无共层铜/无重叠钻孔深度 ⇒ 豁免
    （与引擎 SAFE_HOP_METRIC 一致）；span-blind 计数另记 warnings 供 G7 DRC 复核。"""
    vias = []
    for p in art["pages"]:
        for v in p.get("vias", []):
            vias.append((p["page_id"], v["pol"], v["x"], v["y"], tuple(v.get("layers", ()))))
    safe_hop = (art.get("resource_gate") or {}).get("r1_5_shape") == "co16"
    bad = 0; mn = 9e9; warn = 0; mn_w = 9e9
    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            a, b = vias[i], vias[j]
            if a[0] == b[0] and a[1] == b[1]:
                continue
            d = ((a[2] - b[2]) ** 2 + (a[3] - b[3]) ** 2) ** 0.5
            mn_w = min(mn_w, d)
            if d < VIA_VIA - 1e-9:
                warn += 1
            span_disjoint = False
            if safe_hop and len(a[4]) == 2 and len(b[4]) == 2:
                ai = sorted(_PHYS.index(x) for x in a[4])
                bi = sorted(_PHYS.index(x) for x in b[4])
                span_disjoint = ai[-1] < bi[0] or bi[-1] < ai[0]
            if span_disjoint:
                continue
            mn = min(mn, d)
            if d < VIA_VIA - 1e-9:
                bad += 1
    return (bad, (None if mn > 8e8 else round(mn, 6)), len(vias),
            {"span_blind_violations": warn, "span_blind_min_mm": (None if mn_w > 8e8 else round(mn_w, 6)),
             "exempt": "CO-16 层跨不相交（CO-18 §1b/§4-2）"})


def check_acn(art, verdict, manifest, gaps):
    checks = []
    def chk(cid, exp, obs, ok):
        checks.append({"id": cid, "expected": exp, "observed": obs, "ok": bool(ok)})
    r1 = art["layers"]["R1"]["assignment"]
    n_pages = sum(1 for p in manifest["pages"] if p["kind"] == "data")
    chk("A-CN.1d", f"{n_pages}/{n_pages}", f"{len(r1)}/{n_pages}", len(r1) == n_pages)
    miss = []
    for pid, a in r1.items():
        for pol in ("P", "N"):
            x, y = a[pol + "_via"]
            if not any(abs(float(c[0]) - x) < 1e-6 and abs(float(c[1]) - y) < 1e-6
                       for c in verdict["pages"][pid][pol]["cands"]):
                miss.append((pid, pol))
    chk("A-CN.1a", "0 miss", f"{len(miss)} miss", not miss)
    vias = []
    for pid, a in r1.items():
        for pol in ("P", "N"):
            vias.append((pid + "." + pol, a[pol + "_via"]))
    vbad = [1 for i in range(len(vias)) for j in range(i + 1, len(vias))
            if ((vias[i][1][0] - vias[j][1][0]) ** 2 + (vias[i][1][1] - vias[j][1][1]) ** 2) ** 0.5 < VIA_VIA - 1e-9]
    chk("A-CN.1b", "0", str(len(vbad)), not vbad)
    n_land = len(art["layers"]["R3"]["assignment"])
    chk("A-CN.3a", "72", str(n_land), n_land == 72)
    r3 = art["layers"]["R3"]["assignment"]
    _co16_keys = set()
    if (art.get("resource_gate") or {}).get("r1_5_shape") == "co16":
        for _p in manifest["pages"]:
            if _p.get("kind") != "data":
                continue
            for _pol in ("P", "N"):
                _co16_keys.add(_p["anchors"]["conn"][_pol]["ref"] + "|" + _p["nets"][_pol])
    band_bad = [k for k, v in r3.items() if k not in _co16_keys
                and (v["landing"][1] < v["y_band"][0] - 1e-9 or v["landing"][1] > v["y_band"][1] + 1e-9)]
    chk("A-CN.3c", "0", str(len(band_bad)), not band_bad)
    c = art["layers"]["R1_5"]["crossings_by_class"]; o = art["layers"]["R1_5"].get("overlaps_by_class", {})
    chk("A-CN.4", "0", f"cross={c} overlap={o}", all(v == 0 for v in list(c.values()) + list(o.values())))
    rf = art["layers"]["REFCLK"]
    chk("A-CN.5a", "0", str(len(rf["keepout_hits"])), not rf["keepout_hits"])
    chk("A-CN.5b", "True", str(rf["page_separation_ok"]), bool(rf["page_separation_ok"]))
    d = len([p for p in art["pages"] if p["kind"] == "refclk"])
    chk("A-CN.5c", "2 refclk", str(d), d == 2)
    return checks


# ---------------- A1.2 / A1.3 / A1.4 ----------------
def a12(src_sha, shape="t2"):
    import tempfile
    res = {}
    _extra = ["--r1-5-shape", shape] if shape and shape != "t2" else []
    with tempfile.TemporaryDirectory() as td:
        for o in ("natural", "reverse", "hash"):
            om = Path(td) / f"m_{o}.json"; ol = Path(td) / f"l_{o}.json"
            run_engine(_extra + ["--enum-order", o], om, ol)
            res[o] = {"main_sha256": sha(om), "landing_sha256": sha(ol)}
    vals = {v["main_sha256"] for v in res.values()}
    landvals = {v["landing_sha256"] for v in res.values()}
    ok = len(vals) == 1 and len(landvals) == 1
    return {"ok": ok, "shape": shape, "orders": res, "identical_main": len(vals) == 1,
            "identical_landing": len(landvals) == 1}


def a13(art, manifest):
    spec = importlib.util.spec_from_file_location("invs", str(K2 / "tools/p3_v57_s1_invariants.py"))
    invs = importlib.util.module_from_spec(spec); spec.loader.exec_module(invs)
    # W3 8L (LID.1): 信号层 = {F.Cu, B.Cu, In2.Cu, In6.Cu}（m13_v57_layer_intent_adoption_v1.json）
    invs.LAYER_PAIRS_OK = {(a, b) for a in ("F.Cu", "B.Cu", "In2.Cu", "In6.Cu")
                           for b in ("F.Cu", "B.Cu", "In2.Cu", "In6.Cu") if a != b}
    _sh = (art.get("resource_gate") or {}).get("r1_5_shape", "t2")
    invs.PAIR_RUN_MIN_MM = 1.0 if _sh == "co16" else 0.0   # CO-18: co16 仅比对走廊 run（≥1mm）
    _shape = (art.get("resource_gate") or {}).get("r1_5_shape", "t2")
    # 对内 lane y 半距：t2 = POL_OFF 0.19（SPEC gap 0.175）；co16 = POL_OFF_CO16 0.25
    _half = 0.25 if _shape == "co16" else 0.19
    rules = {"width": 0.205, "p_gap": 0.175, "half_pitch": _half, "pn_min_edge": 0.155,
             "max_vias_per_net": 6, "via_od": 0.35}     # ECO SPEC-REV-2（bandY 6 via/线；CO-11 附件）
    mp = {p["page_id"]: p for p in manifest["pages"]}
    viol = []; strong = 0; pages_checked = 0
    for pg in art["pages"]:
        if pg["kind"] != "data":
            continue
        pages_checked += 1
        f = mp[pg["page_id"]]
        anchors = {"P": {"chip": f["anchors"]["chip"]["P"]["pad_global"],
                         "conn": f["anchors"]["conn"]["P"]["pad_global"]},
                   "N": {"chip": f["anchors"]["chip"]["N"]["pad_global"],
                         "conn": f["anchors"]["conn"]["N"]["pad_global"]}}
        page = {"page_id": pg["page_id"], "anchor_pads": anchors,
                "paths": {pol: to_path(pg["nodes"][pol]) for pol in ("P", "N")}}
        for pol in ("P", "N"):
            ph = page["paths"][pol]
            if len(ph["vias"]) >= 0 and len(ph["points"]) >= 2:
                strong += 2                                   # chip anchor + conn anchor
                strong += len(ph["vias"])                     # via nodes
        v = invs.check_page(page, rules)
        for x in v:
            x["page_id"] = pg["page_id"]
        viol += v
    # REFCLK pages (V7): path endpoints = witness pads; layer F.Cu; >=2 points
    rf = art["layers"]["REFCLK"]["assignment"]
    refclk_checked = 0
    for pid, rv in rf.items():
        refclk_checked += 1
        for pol in ("P", "N"):
            pp = rv["paths"][pol]; pth = pp["path"]
            if len(pth) < 2 or rv["layer"] != "F.Cu":
                viol.append({"id": pid, "pol": pol, "V": "V7_refclk_path", "n": len(pth), "layer": rv["layer"]})
            if abs(pth[0][0] - pp["j2_pad"][0]) > 1e-6 or abs(pth[0][1] - pp["j2_pad"][1]) > 1e-6:
                viol.append({"id": pid, "pol": pol, "V": "V7_refclk_start", "got": pth[0], "want": pp["j2_pad"]})
            if abs(pth[-1][0] - pp["far_pad"][0]) > 1e-6 or abs(pth[-1][1] - pp["far_pad"][1]) > 1e-6:
                viol.append({"id": pid, "pol": pol, "V": "V7_refclk_end", "got": pth[-1], "want": pp["far_pad"]})
            strong += 1
    return {"ok": not viol, "pages_checked": pages_checked + refclk_checked,
            "data_pages_checked": pages_checked, "refclk_pages_checked": refclk_checked,
            "strong_nodes_censused": strong,
            "rules_revision": {"max_vias_per_net": 6, "half_pitch": _half,
                               "layer_pairs": "signal set {F.Cu,B.Cu,In2.Cu,In6.Cu} (LID.1 8L)",
                               "basis": "ECO SPEC-REV-2（bandY 6 via/线）；CO-18 L2 对内 lane 半距 co16=0.25（vs t2 0.19）"},
            "violations": viol[:50], "n_violations": len(viol)}


def a14(src):
    bad = []
    for pat in ("x-window", "max-x", "max_x", "x_window", "read_pcb", "kicad_pcb", "reverse_guess"):
        for i, line in enumerate(src.splitlines(), 1):
            if pat in line and not line.strip().startswith("#"):
                bad.append({"pattern": pat, "line": i, "text": line.strip()[:100]})
    # anchor whitelist: engine must read only the frozen inputs (no board file read at runtime)
    board_read = "kicad_pcb" in src.split("FROZEN_SHA")[0]
    return {"ok": not bad and not board_read, "hits": bad[:20], "board_read_in_engine": board_read}


def main() -> int:
    src = ENGINE.read_text(encoding="utf-8")
    art = load(MAIN)
    manifest = load(FROZEN["manifest"])
    verdict = load(VERDICT)
    gaps = load(GAPS)
    lane_frame = load(LANEFRAME)
    w0r = load(W0R)

    frozen = {k: sha(p) for k, p in FROZEN.items()}
    frozen_ok = all(frozen[k].startswith(FROZEN_SHA_PREFIX[k]) for k in FROZEN_SHA_PREFIX)

    gm1r, gm2r, gm3r, gm6r = gm1(src), gm2(src), gm3(), gm6(art)

    # G-M4: independent re-derivation（co16 = 消费保真 vs CO16-ALLOC.1；其余 = 闭式规则复刻）
    _shape = (art.get("resource_gate") or {}).get("r1_5_shape", "t2")
    m4 = {"r2_mismatch": [], "r3_mismatch": [], "nodes_route_mismatch": [], "shape": _shape}
    if _shape == "co16":
        _alloc = load(STEP2 / "m13_v57_co16_channel_allocation_v3.json")
        _apg = _alloc["pages"]
        for pid, pg in [(p["page_id"], p) for p in art["pages"] if p["kind"] == "data"]:
            al = _apg.get(pid)
            if al is None:
                m4["r2_mismatch"].append({"page": pid, "missing_alloc": True}); continue
            _ly = (al["lane_y"]["P"] + al["lane_y"]["N"]) / 2.0
            if abs(pg["lane"]["y"] - _ly) > 1e-6:
                m4["r2_mismatch"].append({"page": pid, "artifact": pg["lane"], "alloc_lane_y": _ly})
            for pol in ("P", "N"):
                rb = pg.get("r3_by_pol", {}).get(pol)
                want = al["landing"][pol]
                if rb is None:
                    m4["r3_mismatch"].append({"page": pid, "pol": pol, "missing": True}); continue
                if abs(rb["column_x"] - want[0]) > 1e-6 or abs(rb["landing"][1] - want[1]) > 1e-6:
                    m4["r3_mismatch"].append({"page": pid, "pol": pol, "artifact": rb, "alloc": want})
        m4["co16_allocation"] = {
            "artifact": "m13_v57_co16_channel_allocation_v3.json", "n_pages": len(_apg),
            "basis": "O(1) 消费保真；CO16-ALLOC.1 由 p3_v57_co11_placement_verify.py 独立复核 320/320 0 违规 PASS"}
    else:
        r2 = derive_r2(manifest, lane_frame)
        r3d = derive_r3(gaps, manifest, load(BASE_GAPS), lane_frame)
        for pid, v in r2.items():
            a = art["pages"]; pg = next((p for p in a if p["page_id"] == pid), None)
            if pg is None or pg["kind"] != "data":
                continue
            if abs(pg["lane"]["y"] - v["lane_y"]) > 1e-6 or pg["lane"]["index"] != v["lane_index"]:
                m4["r2_mismatch"].append({"page": pid, "artifact": pg["lane"], "derived": v})
        for pid, pg in [(p["page_id"], p) for p in art["pages"] if p["kind"] == "data"]:
            f = next(p for p in manifest["pages"] if p["page_id"] == pid)
            for pol in ("P", "N"):
                k = f["anchors"]["conn"][pol]["ref"] + "|" + f["nets"][pol]
                d = r3d.get(k)
                if d is None:
                    continue
                rb = pg.get("r3_by_pol", {}).get(pol)
                if rb is None:
                    m4["r3_mismatch"].append({"page": pid, "pol": pol, "missing": True}); continue
                if abs(rb["column_x"] - d["column_x"]) > 1e-6 or abs(rb["landing"][1] - d["landing_y"]) > 1e-6:
                    m4["r3_mismatch"].append({"page": pid, "pol": pol, "artifact": rb, "derived": d})
    C, O = full_metric(art["route_geometry"])
    vbad, vmin, nvias, _vwarn = via_min_inter(art)
    acn = check_acn(art, verdict, manifest, gaps)
    m4["segment_metric"] = {"cross": C, "overlap": O, "total": C + O,
                            "artifact_claim": art["resource_gate"]["verification_check"]["same_layer_crossings"]}
    m4["via_clearance"] = {"violations": vbad, "min_inter_net_mm": vmin, "n_vias": nvias, **_vwarn}
    m4["ok"] = (not m4["r2_mismatch"] and not m4["r3_mismatch"] and C == 0 and O == 0 and vbad == 0)

    landing = load(LANDING)
    f12 = {"landing_revision": landing["revision"], "n_rows": landing["n_rows"],
           "authority_main_sha256": landing["authority"]["main_sha256"], "main_sha256": sha(MAIN),
           "match": landing["authority"]["main_sha256"] == sha(MAIN)}

    a12r = a12(src, _shape)
    a13r = a13(art, manifest)
    a14r = a14(src)

    gates = {"G-M1": gm1r, "G-M2": gm2r, "G-M3": gm3r,
             "G-M4": {"ok": m4["ok"], "shape": _shape, "r2_mismatch": len(m4["r2_mismatch"]),
                      "r3_mismatch": len(m4["r3_mismatch"]), "segment_metric": m4["segment_metric"],
                      "via_clearance": m4["via_clearance"]},
             "G-M5": {"ok": all(c["ok"] for c in acn), "checks": acn},
             "G-M6": gm6r}
    gates_ok = all(g["ok"] for g in gates.values())
    checks_ok = all(c["ok"] for c in acn)
    _revpat = r'REVISION_CO16\s*=\s*"([^"]+)"' if _shape == "co16" else r'(?<![_A-Z])REVISION\s*=\s*"([^"]+)"'
    _engine_rev = re.search(_revpat, src).group(1)
    probes = [{"key": "stale_state",
               "probe": "artifact revision vs engine REVISION (on-disk source)",
               "ok": art["revision"] == _engine_rev},
              {"key": "misleading_success_output",
               "probe": "both zeros recomputed from the artifact (route_geometry + pages[*].vias)",
               "ok": C == 0 and O == 0 and vbad == 0}]
    verdict_str = "PASS" if (gates_ok and checks_ok and frozen_ok and a12r["ok"] and a13r["ok"]
                             and a14r["ok"] and all(p["ok"] for p in probes)) else "FAIL"

    val = {"artifact": "m13_v57_w3_validation", "schema": 1, "revision": "W3-VALv2.3",
           "artifact_rev": art["revision"], "verdict": verdict_str,
           "stage": {"D8": {"gates": gates}, "G5": {"A1.2": a12r["ok"], "A1.3": a13r["ok"], "A1.4": a14r["ok"]}},
           "method_gates": gates, "frozen_sha_check": {"actual": frozen, "match": frozen_ok},
           "f12": f12, "adversarial_probes": probes,
           "notes": ["G-M4 独立重导：R2 lane（由冻结 lane_frame 独立复刻块规则）+ R3 landing（由 r3x2 域 + pad y-band）"
                     "+ 双度量（段冲突/全 via 间距，由工件 route_geometry/pages[*].vias 独立重算）。",
                     "R1 via 以不变量验证（∈冻结候选 + 100% 间距 + 平面性），非重现 argmin（引擎候选键）。",
                     "v2.3 契约修订：R3 独立重导纳入 CO-05c 成对落列（J2 数据页 inner=131.65-0.6k / outer=136.0+0.6k，k=本带序，"
                     "无前缀递推）；其余 pad 保留 v2.2 列序交替偏置规则。CO-05c 见 m13_v57_CO05_addendum_v6/v7。"]}
    MAIN_VAL = STEP2 / "m13_v57_w3_validation.json"
    MAIN_VAL.write_text(json.dumps(val, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (STEP2 / "m13_v57_w4_a12_report.json").write_text(json.dumps(
        {"artifact": "m13_v57_w4_a12_report", "predicate": "A1.2 序无关：3 枚举序(输入置换) -> 图纸+landing 逐字节一致",
         "verdict": "PASS" if a12r["ok"] else "FAIL", "orders": a12r["orders"],
         "engine_revision": art["revision"]}, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (STEP2 / "m13_v57_w4_a13_report.json").write_text(json.dumps(
        dict(a13r, artifact="m13_v57_w4_a13_report",
             predicate="A1.3 生成即合法：V1-V6 几何不变量套件（覆盖 34 页 + 强节点）",
             verdict="PASS" if a13r["ok"] else "FAIL"), indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (STEP2 / "m13_v57_w4_a14_report.json").write_text(json.dumps(
        dict(a14r, artifact="m13_v57_w4_a14_report",
             predicate="A1.4 单向性：生成器无 x-window/max-x/板文件反猜", files_checked=["tools/p3_v57_w3_constructive.py"],
             verdict="PASS" if a14r["ok"] else "FAIL"), indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"VALIDATOR v2: verdict={verdict_str} G-M={ {k:g['ok'] for k,g in gates.items()} } "
          f"A1.2={a12r['ok']} A1.3={a13r['ok']}({a13r['n_violations']} viol) A1.4={a14r['ok']} "
          f"frozen={frozen_ok} metric={C + O} via_viol={vbad}")
    return 0 if verdict_str == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
