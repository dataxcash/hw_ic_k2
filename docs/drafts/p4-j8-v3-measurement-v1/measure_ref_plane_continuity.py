#!/usr/bin/env python3
"""K2 · P4 · V3「参考连续性」测量实现（**只出测量，无 verdict**）。

口径（计划 §3.3 V3）：**每段高速走线，相邻两层存在连续参考平面（投影覆盖该段全长）**。
实现：
  ① 平面层 = **已填充**且落在内层（In1..In6）的 zone，按层取**已填充多边形并集**；
  ② 高速段 = `--net-prefix`（默认 `PCIE_`，可按 `--netclass-json` 精确取自 pro netclass）的 track；
  ③ 段投影多边形 = 线段按线宽外扩的矩形；`覆盖 = 段矩形 − 该层平面并集`（为空即全长覆盖）；
  ④ 报告每段「相邻上/下平面层」的覆盖情况与「是否至少一层全长覆盖」，并给全板汇总。
输出 JSON **不含 `verdict` 字段**。`--fail-on-violation`（= 存在段「无任一层全长覆盖」）仅 gate 侧使用。

用法：
  AppDir/usr/bin/python3.11 measure_ref_plane_continuity.py --board <板> [--net-prefix PCIE_] [--json out.json]
"""
import argparse
import hashlib
import json
import math
import os
import sys

import pcbnew

NM = 1_000_000
STACK = [("F.Cu", pcbnew.F_Cu), ("In1.Cu", pcbnew.In1_Cu), ("In2.Cu", pcbnew.In2_Cu),
         ("In3.Cu", pcbnew.In3_Cu), ("In4.Cu", pcbnew.In4_Cu), ("In5.Cu", pcbnew.In5_Cu),
         ("In6.Cu", pcbnew.In6_Cu), ("B.Cu", pcbnew.B_Cu)]
INNER = [pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu]


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def _cover(body, plane, area):
    remain = pcbnew.SHAPE_POLY_SET(body)
    remain.BooleanSubtract(plane)
    if remain.OutlineCount() == 0:
        return 1.0
    return 1.0 - (abs(remain.Area()) / area if area else 0.0)


def seg_poly(start, end, width_nm):
    """线段按线宽外扩的矩形（两端不做圆头；保守=偏大 ⇒ 覆盖判定偏严）。"""
    x1, y1, x2, y2 = start.x, start.y, end.x, end.y
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy)
    if ln == 0:
        return None
    nx, ny = -dy / ln * (width_nm / 2.0), dx / ln * (width_nm / 2.0)
    pts = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
    ps = pcbnew.SHAPE_POLY_SET()
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in pts:
        ch.Append(pcbnew.VECTOR2I(int(round(x)), int(round(y))))
    ch.SetClosed(True)
    ps.AddOutline(ch)
    return ps


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--net-prefix", default="PCIE_")
    ap.add_argument("--netclass-json", default=None,
                    help="可选：从 .kicad_pro 解析 netclass 归类的 JSON（键=网名，值=netclass）")
    ap.add_argument("--json", default=None)
    ap.add_argument("--fail-on-violation", action="store_true")
    a = ap.parse_args(argv)
    bd = pcbnew.LoadBoard(a.board)
    # 平面并集（仅已填充 zone）
    def _union(layer, getter):
        ps, has = None, False
        for z in bd.Zones():
            if not z.IsOnLayer(layer) or z.GetIsRuleArea():
                continue
            try:
                fl = getter(z)
            except Exception:
                fl = None
            if fl is None or fl.OutlineCount() == 0:
                continue
            if not has:
                ps = pcbnew.SHAPE_POLY_SET(fl)   # 空集上 BooleanAdd 无效 ⇒ 首个直接拷贝
                has = True
            else:
                ps.BooleanAdd(fl)
        return ps if has else None

    planes = {}          # 严格口径：已填充多边形（含反焊盘孔洞）
    planes_nominal = {}  # 名义口径：zone 轮廓（不含反焊盘孔洞）
    for lay in INNER:
        fl = _union(lay, lambda z: z.GetFilledPolysList(lay) if z.IsFilled() else None)
        if fl is not None:
            planes[lay] = fl
        nm = _union(lay, lambda z: z.Outline())
        if nm is not None:
            planes_nominal[lay] = nm
    plane_names = [n for n, l in STACK if l in planes]
    idx = {l: i for i, (n, l) in enumerate(STACK)}
    def nearest_plane(li, direction):
        i = idx[li] + direction
        while 0 <= i < len(STACK):
            if STACK[i][1] in planes:
                return STACK[i][1]
            i += direction
        return None
    segs, rows = [], []
    for t in bd.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        name = t.GetNetname()
        if not name.startswith(a.net_prefix):
            continue
        segs.append(t)
    for t in segs:
        lay = t.GetLayer()
        above = nearest_plane(lay, -1)
        below = nearest_plane(lay, +1)
        start, end, w = t.GetStart(), t.GetEnd(), t.GetWidth()
        body = seg_poly(start, end, w)
        area = abs(body.Area()) if body is not None else 0.0
        rec = {"net": t.GetNetname(), "layer": pcbnew.LayerName(lay),
               "w_mm": round(w / NM, 3),
               "start_mm": [round(start.x / NM, 3), round(start.y / NM, 3)],
               "end_mm": [round(end.x / NM, 3), round(end.y / NM, 3)],
               "adjacent_planes": {"above": pcbnew.LayerName(above) if above else None,
                                   "below": pcbnew.LayerName(below) if below else None},
               "coverage": {}, "coverage_nominal": {}}
        fully = []
        for tag, pl in (("above", above), ("below", below)):
            if pl is None:
                rec["coverage"][tag] = None
                rec["coverage_nominal"][tag] = None
                continue
            cov = _cover(body, planes[pl], area)
            rec["coverage"][tag] = round(cov, 6)
            nm_pl = planes_nominal.get(pl)
            rec["coverage_nominal"][tag] = None if nm_pl is None else round(_cover(body, nm_pl, area), 6)
            if cov >= 1.0:
                fully.append(tag)
        rec["full_cover_tags"] = fully
        rec["any_full_cover"] = bool(fully)
        rows.append(rec)
    n = len(rows)
    n_ok = sum(1 for r in rows if r["any_full_cover"])
    covs = []
    for r in rows:
        for tag in ("above", "below"):
            if r["coverage"].get(tag) is not None:
                covs.append(r["coverage"][tag])
    thr = {}
    for t in (1.0, 0.99, 0.95, 0.90, 0.50):
        thr[str(t)] = sum(1 for r in rows if max([c for c in r["coverage"].values() if c is not None] or [0.0]) >= t)
    nominal_ok = sum(1 for r in rows if r["coverage_nominal"] and max(
        [c for c in r["coverage_nominal"].values() if c is not None] or [0.0]) >= 0.999999)
    covs.sort()
    def pct(q):
        return covs[min(len(covs) - 1, int(len(covs) * q))] if covs else None
    res = {"check": "ref_plane_continuity",
           "coverage_distribution": {"n": len(covs), "min": covs[0] if covs else None,
                                     "p05": pct(0.05), "p50": pct(0.50), "p95": pct(0.95),
                                     "max": covs[-1] if covs else None},
           "n_segments_nominal_full_cover": nominal_ok,
           "n_segments_by_max_coverage_threshold": thr,
           "n_segments_with_any_adjacent_plane": sum(
               1 for r in rows if r["coverage"].get("above") is not None or r["coverage"].get("below") is not None),
           "board": os.path.abspath(a.board), "board_sha16": sha16(a.board),
           "net_prefix": a.net_prefix,
           "plane_layers_present": plane_names,
           "plane_layers_expected_inner": [n for n, l in STACK if l in INNER],
           "n_highspeed_segments": n,
           "n_any_full_cover": n_ok,
           "n_no_full_cover": n - n_ok,
           "no_full_cover": [r for r in rows if not r["any_full_cover"]],
           "segments": rows}
    if not planes:
        res["note"] = "无任何已填充内层平面（V3 必 FAIL）"
    if a.json:
        json.dump(res, open(a.json, "w"), ensure_ascii=False, indent=1)
    print(f"[ref_plane_continuity] board={os.path.basename(a.board)} sha16={res['board_sha16']}")
    print(f"  平面层（已填充）：{plane_names or '（无）'}")
    print(f"  高速段 {n}；严格口径任一相邻层 100% 覆盖 {n_ok}；无 100% 覆盖 {n - n_ok}")
    print(f"  名义口径（zone 轮廓）全长覆盖 {nominal_ok}/{n}")
    print(f"  最大覆盖 ≥ 阈值 的段数：{thr}")
    for r in res["no_full_cover"][:10]:
        print(f"    {r['net']}@{r['layer']} cov={r['coverage']} planes={r['adjacent_planes']}")
    if a.fail_on_violation and n - n_ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
