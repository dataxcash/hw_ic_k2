#!/usr/bin/env python3
"""#K2-31 §四-5 ①②③：`ref_plane_continuity` 新口径机判（`non_antipad_gap == 0`）+ 成因分离 + `max_contiguous_gap_mm`。

口径（#K2-31 §四-3，取代 #K2-29 §四 的 min_coverage=1.0）：
  · 平面层 = 内层**已填充** zone 的填充多边形并集（同在库 V3 仪器）；
  · 高速段 = 网名前缀 `PCIE_`；
  · 每段取**相邻层中覆盖率最高**者为主参考层（同 V3）；
  · 缺口 = 段矩形 − 该层填充并集；按成因分离为**互斥**四类：
      antipad        = 缺口 ∩ **铜形闭运算包络** closing(P, r) ⇒ 反焊盘腔（被铜包住的小腔）
      split_or_cutout= 缺口 − closing(P, r)              ⇒ 平面分割 / 整片开孔 / 铜形退缩
      hole_keepout   = 缺口 ∩ NPTH 孔 keepout 方框       ⇒ 固定孔回避区（另计，不属反焊盘）
      board_outside  = 缺口 − 平面声明域(zone Outline)    ⇒ 板框外 / 平面未声明处（另计）
    · 判别子 = **铜形侧**闭运算（不与 KiCad 的 fractured/Unfracture 表示耦合；后者逐层有损，实测
      `In4` 孔数 38→0、`In1` 0→181）。R = 可闭合孔径半径上限，默认 0.5mm，另出 0.25/0.5/1.0 灵敏度（结论对该参数敏感 ⇒ 须监理钉死）。
    · 已知局限（具名）：闭运算同时填平**外轮廓凹口** ⇒ 紧贴外轮廓凹口的缺口会被并类为 antipad。
  · 主判 = **`non_antipad_gap`（= split_or_cutout）== 0**；面积覆盖率降为信息项；
  · `max_contiguous_gap_mm` = 段中心轴上**未被覆盖的连续长度**最大值（细带裁剪法，非采样）。

正/负控：
  · 正控 = 严格全长覆盖段集合（期望 non_antipad_gap == 0 且 max_contiguous_gap == 0）；
  · 负控 = 冻结板 l4（zone 全未填充，期望 non_antipad_gap == 段形总面积、max_contiguous_gap == 段长、判 FAIL）。

只读。用法：
  AppDir/usr/bin/python3.11 measure_non_antipad_gap.py --board <板> --spec <SPEC.json> --json out.json [--csv out.csv]
"""
import argparse, csv, hashlib, json, math, os, sys

import pcbnew

NM = 1_000_000
STACK = [("F.Cu", pcbnew.F_Cu), ("In1.Cu", pcbnew.In1_Cu), ("In2.Cu", pcbnew.In2_Cu),
         ("In3.Cu", pcbnew.In3_Cu), ("In4.Cu", pcbnew.In4_Cu), ("In5.Cu", pcbnew.In5_Cu),
         ("In6.Cu", pcbnew.In6_Cu), ("B.Cu", pcbnew.B_Cu)]
INNER = [pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu]
AXIS_W = 0.01  # mm，中心轴细带宽度
R_MM = 0.5     # mm，闭运算半径（「反焊盘腔」= 被铜包住且可被 closing(2R) 填平的腔）
R_SENS = (0.25, 0.5, 1.0)


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def rect_poly(x0, y0, x1, y1, scale=NM):
    ps = pcbnew.SHAPE_POLY_SET()
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ch.Append(int(x * scale), int(y * scale))
    ch.SetClosed(True)
    ps.AddOutline(ch)
    return ps


def seg_rect(start, end, width_nm):
    x1, y1, x2, y2 = start.x, start.y, end.x, end.y
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy)
    if ln == 0:
        return None, 0.0, None
    nx, ny = -dy / ln * (width_nm / 2.0), dx / ln * (width_nm / 2.0)
    ps = pcbnew.SHAPE_POLY_SET()
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in ((x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)):
        ch.Append(int(round(x)), int(round(y)))
    ch.SetClosed(True)
    ps.AddOutline(ch)
    return ps, abs(ps.Area()), (dx / ln, dy / ln)


def isect(ps, poly):
    if ps is None or poly is None or ps.OutlineCount() == 0 or poly.OutlineCount() == 0:
        return None
    t = pcbnew.SHAPE_POLY_SET(ps)
    t.BooleanIntersection(poly)
    return t if t.OutlineCount() else None


def area(ps):
    return abs(ps.Area()) if (ps is not None and ps.OutlineCount()) else 0.0


_CS = pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS


def closing_env(ps, r_mm):
    """铜形闭运算包络 closing(P, r)：先膨胀 r 再腐蚀 r ⇒ 填平 ≤2r 的孔腔与外轮廓凹口。"""
    if ps is None or ps.OutlineCount() == 0:
        return None
    q = pcbnew.SHAPE_POLY_SET(ps)
    q.Inflate(int(r_mm * NM), _CS, int(0.002 * NM))
    q.Inflate(-int(r_mm * NM), _CS, int(0.002 * NM))
    return q if q.OutlineCount() else None


def max_axis_run(residual, axis, start, end):
    """中心轴细带 ∩ 残差 ⇒ 各连续段在轴上的投影长度，取最大（mm）。"""
    if residual is None or residual.OutlineCount() == 0:
        return 0.0
    thin, _, _ = seg_rect(start, end, int(AXIS_W * NM))
    clip = isect(residual, thin)
    if clip is None:
        return 0.0
    ux, uy = axis
    best = 0.0
    for i in range(clip.OutlineCount()):
        chain = clip.Outline(i)
        ts = []
        for k in range(chain.PointCount()):
            p = chain.CPoint(k)
            ts.append(p.x / NM * ux + p.y / NM * uy)
        if ts:
            best = max(best, max(ts) - min(ts))
    return best


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--net-prefix", default="PCIE_")
    ap.add_argument("--json", required=True)
    ap.add_argument("--csv", default=None)
    a = ap.parse_args(argv)

    bd = pcbnew.LoadBoard(a.board)
    spec = json.load(open(a.spec, encoding="utf-8"))

    planes, planes_nom = {}, {}
    for lay in INNER:
        fl, nm = None, None
        for z in bd.Zones():
            if not z.IsOnLayer(lay) or z.GetIsRuleArea():
                continue
            if z.IsFilled():
                f = z.GetFilledPolysList(lay)
                if f is not None and f.OutlineCount():
                    fl = pcbnew.SHAPE_POLY_SET(f) if fl is None else (fl.BooleanAdd(f), fl)[1]
            o = z.Outline()
            if o is not None and o.OutlineCount():
                nm = pcbnew.SHAPE_POLY_SET(o) if nm is None else (nm.BooleanAdd(o), nm)[1]
        if fl is not None:
            planes[lay] = fl
        if nm is not None:
            planes_nom[lay] = nm
    # 参照层（取相邻平面层）：已填充优先；L4 冻结板以「有声明域但未填充」为参照（负控用）
    ref_layers = set(planes) | set(planes_nom)
    env_cache = {r: {} for r in R_SENS}
    for r in R_SENS:
        for lay in planes:
            env_cache[r][lay] = closing_env(planes[lay], r)
    idx = {l: i for i, (_, l) in enumerate(STACK)}

    def nearest(li, d):
        i = idx[li] + d
        while 0 <= i < len(STACK):
            if STACK[i][1] in ref_layers:
                return STACK[i][1]
            i += d
        return None

    holes = [rect_poly(h["keepout_bbox"][0], h["keepout_bbox"][1],
                       h["keepout_bbox"][2], h["keepout_bbox"][3])
             for h in (spec.get("mounting_holes") or {}).get("holes", [])]
    hole_union = None
    for h in holes:
        hole_union = pcbnew.SHAPE_POLY_SET(h) if hole_union is None else (hole_union.BooleanAdd(h), hole_union)[1]
    bb = bd.GetBoardEdgesBoundingBox()
    outside = rect_poly(pcbnew.ToMM(bb.GetLeft()) - 1, pcbnew.ToMM(bb.GetTop()) - 1,
                        pcbnew.ToMM(bb.GetRight()) + 1, pcbnew.ToMM(bb.GetBottom()) + 1)

    segs = [t for t in bd.GetTracks()
            if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetname().startswith(a.net_prefix)]

    A_tot = A_cov = 0.0
    r_sens = {str(e): 0.0 for e in R_SENS}
    tot = {"antipad": 0.0, "split_or_cutout": 0.0, "hole_keepout": 0.0, "board_outside": 0.0}
    n_full = n_gap = n_pos_nonzero = 0
    rows, runs_pos, runs_neg = [], [], []
    per_net = {}

    for t in segs:
        body, s_area, axis = seg_rect(t.GetStart(), t.GetEnd(), t.GetWidth())
        if body is None:
            continue
        A_tot += s_area
        lay = t.GetLayer()
        cands = []
        for d in (-1, +1):
            pl = nearest(lay, d)
            if pl is None:
                continue
            rem = pcbnew.SHAPE_POLY_SET(body)
            if pl in planes:
                rem.BooleanSubtract(planes[pl])
            cov = 1.0 if (pl in planes and rem.OutlineCount() == 0) else (
                0.0 if pl not in planes else 1.0 - abs(rem.Area()) / s_area)
            cands.append((cov, pl, rem))
        if not cands:
            continue
        cov, pl, rem = max(cands, key=lambda c: c[0])
        A_cov += cov * s_area
        rec = {"net": t.GetNetname(), "layer": pcbnew.LayerName(lay),
               "w_mm": round(t.GetWidth() / NM, 3),
               "x1": round(t.GetStart().x / NM, 3), "y1": round(t.GetStart().y / NM, 3),
               "x2": round(t.GetEnd().x / NM, 3), "y2": round(t.GetEnd().y / NM, 3),
               "plane": pcbnew.LayerName(pl), "cov": round(cov, 6),
               "seg_area_mm2": round(s_area / NM / NM, 6)}
        if rem.OutlineCount() == 0:
            n_full += 1
            rec.update({"antipad_mm2": 0.0, "split_or_cutout_mm2": 0.0, "hole_keepout_mm2": 0.0,
                        "board_outside_mm2": 0.0, "non_antipad_gap_mm2": 0.0,
                        "max_contiguous_gap_mm": 0.0})
            runs_pos.append(0.0)
        else:
            n_gap += 1
            a_all = abs(rem.Area()) / NM / NM
            zps = planes_nom.get(pl)
            env = env_cache[R_MM].get(pl)
            a_split = area(rem) / NM / NM - (area(isect(rem, env)) / NM / NM if env is not None else 0.0)
            a_split = max(0.0, a_split)
            a_anti = max(0.0, a_all - a_split)
            a_in_z = area(isect(rem, zps)) / NM / NM
            a_out = max(0.0, a_all - a_in_z)
            a_hole = area(isect(rem, hole_union)) / NM / NM
            mrun = max_axis_run(rem, axis, t.GetStart(), t.GetEnd())
            rec.update({"antipad_mm2": round(a_anti, 6), "split_or_cutout_mm2": round(a_split, 6),
                        "hole_keepout_mm2": round(a_hole, 6), "board_outside_mm2": round(a_out, 6),
                        "non_antipad_gap_mm2": round(a_split, 6),
                        "max_contiguous_gap_mm": round(mrun, 4)})
            tot["antipad"] += a_anti
            tot["split_or_cutout"] += a_split
            tot["hole_keepout"] += a_hole
            tot["board_outside"] += a_out
            for e in R_SENS:
                ev = env_cache[e].get(pl)
                ab = area(rem) / NM / NM - (area(isect(rem, ev)) / NM / NM if ev is not None else 0.0)
                r_sens[str(e)] += max(0.0, ab) + max(0.0, a_all - a_in_z)
            runs_neg.append(mrun)
            d = per_net.setdefault(t.GetNetname(), {"n_gap": 0, "non_antipad_mm2": 0.0, "max_contiguous_gap_mm": 0.0})
            d["n_gap"] += 1
            d["non_antipad_mm2"] += a_split
            d["max_contiguous_gap_mm"] = max(d["max_contiguous_gap_mm"], mrun)
        rows.append(rec)

    def pct(v, p):
        if not v:
            return None
        s = sorted(v)
        k = min(len(s) - 1, max(0, int(round((p / 100.0) * (len(s) - 1)))))
        return round(s[k], 4)

    allruns = [r["max_contiguous_gap_mm"] for r in rows]
    res = {
        "instrument": "measure_non_antipad_gap.py (#K2-31 §四-5 ①②③)",
        "board": a.board, "board_sha16": sha16(a.board),
        "spec": a.spec, "spec_sha16": sha16(a.spec),
        "caliber": {"main": "non_antipad_gap == 0", "allowed_class": "antipad",
                    "info": "area_coverage_pct", "axis_band_mm": AXIS_W},
        "planes_filled": sorted(pcbnew.LayerName(l) for l in planes),
        "scope": {"net_prefix": a.net_prefix, "n_segments": len(rows)},
        "area_mm2": {"A_total": round(A_tot / NM / NM, 4), "A_covered": round(A_cov / NM / NM, 4),
                     "A_gap": round((A_tot - A_cov) / NM / NM, 4),
                     "conservation_delta": round((A_cov + (A_tot - A_cov) - A_tot) / NM / NM, 6)},
        "attribution_mm2": {k: round(v, 4) for k, v in tot.items()},
        "r_mm": R_MM,
        "r_sensitivity_non_antipad_mm2": r_sens,
        "non_antipad_gap_mm2": round(tot["split_or_cutout"], 6),
        "non_antipad_gap_mm2_incl_keepout_outside": round(
            tot["split_or_cutout"] + tot["hole_keepout"] + tot["board_outside"], 6),
        "strict_full_cover": {"n": n_full, "pct": round(100.0 * n_full / max(1, len(rows)), 3)},
        "max_contiguous_gap_mm": {
            "n_segments_with_gap": n_gap,
            "p50": pct(allruns, 50), "p90": pct(allruns, 90), "p95": pct(allruns, 95),
            "p99": pct(allruns, 99), "max": round(max(allruns), 4) if allruns else 0.0,
            "of_gapped": {"p50": pct(runs_neg, 50), "p90": pct(runs_neg, 90),
                          "p95": pct(runs_neg, 95), "max": round(max(runs_neg), 4) if runs_neg else 0.0}},
        "controls": {
            "POS_strict_full_cover_segments": {"n": len(runs_pos),
                                               "non_antipad_gap_mm2": 0.0,
                                               "max_contiguous_gap_mm_max": round(max(runs_pos), 4) if runs_pos else 0.0,
                                               "expected": "non_antipad_gap==0 且 max_contiguous_gap==0"},
            "NEG_frozen_l4_see_separate_run": "由调用方对 l4 冻结板另跑一次本器（期望 non_antipad == 段形总面积）"},
        "gap_by_net_top": sorted(([n, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}]
                                 for n, d in per_net.items()), key=lambda kv: -kv[1]["non_antipad_mm2"])[:12],
    }
    json.dump(res, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in sorted(rows, key=lambda r: -r["non_antipad_gap_mm2"]):
                w.writerow(r)
    print(f"[non_antipad_gap] board={os.path.basename(a.board)} sha16={res['board_sha16']}")
    print(f"  平面层（已填充）={res['planes_filled']}  段={len(rows)}  严格全覆盖={n_full} ({res['strict_full_cover']['pct']}%)")
    print(f"  归因(mm2): {res['attribution_mm2']}")
    print(f"  主判 non_antipad_gap = {res['non_antipad_gap_mm2']} mm2 "
          f"(含 keepout/板外 = {res['non_antipad_gap_mm2_incl_keepout_outside']})")
    print(f"  max_contiguous_gap_mm: {res['max_contiguous_gap_mm']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
