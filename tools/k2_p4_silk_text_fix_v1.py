#!/usr/bin/env python3
"""K2 · P4 · ③ 丝印位号残余修复器 v1 —— 字形级几何判定；DRC 只作末检；不写仓库。

对象：复合板上残余 `silk_over_copper` / `silk_overlap`（`--refs` 指定，或 `--auto` 几何自检）。
手法：把位号文本移到**无冲突落点**；**不缩字、不降层**（降层 F.Fab / 缩字属监理口径）。
判定（与 KiCad DRC 同几何语义，故 DRC 只作核对）：
  * 文本 = `PCB_FIELD.GetEffectiveTextShape()`（真实笔画，非外框）
  * 阻焊障碍 = pad 的 `GetEffectiveShape(F_Mask/B_Mask)` + `GetSolderMaskExpansion`；via/track 的 mask 开窗同构
  * 丝印障碍 = **可见**丝印图元/字段笔画（隐藏字段 DRC 亦不计）；间隙用 DRC 默认 0
求解：本体外框中心环采样（0→6mm 步 0.05mm × 24 向）+ 本体中心 + 局部 ±0.2mm/0.01mm 精修；
      打分 = 位移 + 0° 优先 + 上下位优先；多目标按可行落点数升序贪心、互让；`--max-shift-mm` 限可读性。
输出：仅 `--work-dir`（`--apply` 才写板）；输出路径若在仓库内强制 `--confirm-repo-write`（T-41）。
不改孔径/铜/叠层/丝印层归属，不碰 criteria/，不新增检查齿（owner ① ②）。
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import re
import shutil
import subprocess

import pcbnew

NM = 1_000_000
SILK = (pcbnew.F_SilkS, pcbnew.B_SilkS)
RING_STEP, RING_MAX, DIRS = 50_000, 6_500_000, 24
REFINE, REFINE_STEP = 200_000, 10_000
ANG_PENALTY, SIDE_PENALTY = 300_000, 100_000
COARSE_STEP, COARSE_DIRS, COARSE_MAX = 250_000, 12, 5_000_000


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def uid(obj):
    return obj.m_Uuid.AsString()


def sides(layer):
    return (pcbnew.B_SilkS, pcbnew.B_Mask) if layer == pcbnew.B_SilkS else (pcbnew.F_SilkS, pcbnew.F_Mask)


def collect(bd, silk_l, mask_l, skip_uuids):
    """(mask[(shape,clearance)], silk[(tag,shape)])；skip_uuids = 待移动字段（互让后另加）。"""
    mask, silk = [], []
    for fp in bd.GetFootprints():
        for pd in fp.Pads():
            if pd.IsOnLayer(mask_l):
                mask.append((pd.GetEffectiveShape(mask_l), int(pd.GetSolderMaskExpansion(mask_l))))
        for g in fp.GraphicalItems():
            if g.GetLayer() == silk_l:
                silk.append((None, g.GetEffectiveShape()))
        for fl in fp.GetFields():
            if fl.GetLayer() == silk_l and fl.IsVisible() and uid(fl) not in skip_uuids:
                silk.append((uid(fl), fl.GetEffectiveTextShape()))
    for t in bd.GetTracks():
        if t.GetLayer() == mask_l:
            try:
                exp = int(t.GetSolderMaskExpansion())
            except Exception:
                exp = 0
            try:
                mask.append((t.GetEffectiveShape(), exp))
            except Exception:
                pass
    for d in bd.GetDrawings():
        if d.GetLayer() == silk_l:
            silk.append((None, d.GetEffectiveShape()))
    return mask, silk


def outline_of(bd):
    b = bd.GetBoardEdgesBoundingBox()
    m = 200_000
    return (b.GetX() + m, b.GetY() + m, b.GetX() + b.GetWidth() - m, b.GetY() + b.GetHeight() - m)


def make_eval(field, mask, silk, outline=None):
    def ev(px, py, ang):
        field.SetTextAngleDegrees(ang)
        field.SetPosition(pcbnew.VECTOR2I(int(round(px)), int(round(py))))
        ts = field.GetEffectiveTextShape()
        bb = ts.BBox()
        if outline is not None and not (
                outline[0] <= bb.GetX() and bb.GetX() + bb.GetWidth() <= outline[2]
                and outline[1] <= bb.GetY() and bb.GetY() + bb.GetHeight() <= outline[3]):
            return False
        for sh, clr in mask:
            if ts.Collide(sh, clr):
                return False
        for _tag, sh in silk:
            if ts.Collide(sh, 0):
                return False
        return True
    return ev


def cand_positions(fp, w, h, step=RING_STEP, ndir=DIRS, rmax=RING_MAX):
    bb = fp.GetBoundingBox(False, False)
    cx, cy = bb.GetCenter().x, bb.GetCenter().y
    hw, hh = bb.GetWidth() / 2.0 + w / 2.0, bb.GetHeight() / 2.0 + h / 2.0
    pts = [(cx, cy)]
    r = 0
    while r <= rmax:
        for k in range(ndir):
            a = 2 * math.pi * k / ndir
            pts.append((cx + math.sin(a) * (hw + r), cy - math.cos(a) * (hh + r)))
        r += step
    return pts


def solve(field, fp, ev, old, w, h, step=RING_STEP, ndir=DIRS, rmax=RING_MAX, max_shift=None):
    free = 0
    best = None
    for ang in (0, 90):
        for px, py in cand_positions(fp, w, h, step, ndir, rmax):
            d = math.hypot(px - old[0], py - old[1])
            if max_shift and d > max_shift:
                continue
            if not ev(px, py, ang):
                continue
            free += 1
            dx, dy = px - fp.GetPosition().x, py - fp.GetPosition().y
            score = d + (ANG_PENALTY if ang == 90 else 0) + (SIDE_PENALTY if abs(dx) > abs(dy) else 0)
            if best is None or score < best[0]:
                best = (score, d, ang, px, py)
    if best is None:
        return None, free
    _s, _d, ang, bx, by = best
    # 局部精修：最优解邻域内取「更近原位」的可行点
    ref = None
    n = int(REFINE / REFINE_STEP)
    for ix in range(-n, n + 1):
        for iy in range(-n, n + 1):
            px, py = bx + ix * REFINE_STEP, by + iy * REFINE_STEP
            if not ev(px, py, ang):
                continue
            key = (math.hypot(px - old[0], py - old[1]), abs(ix) + abs(iy))
            if ref is None or key < ref[0]:
                ref = (key, px, py)
    px, py = (ref[1], ref[2]) if ref else (bx, by)
    ev(px, py, ang)
    return {"ang": ang, "pos": (int(round(px)), int(round(py))),
            "shift_nm": int(math.hypot(px - old[0], py - old[1])), "n_free": free}, free


def text_wh(field):
    bb = field.GetBoundingBox()
    w, h = bb.GetWidth(), bb.GetHeight()
    if int(round(field.GetTextAngleDegrees())) % 180 == 90:
        w, h = h, w
    return w, h


def targets_of(bd, refs):
    out = {}
    for fp in bd.GetFootprints():
        r = fp.GetReference()
        if refs and r not in refs:
            continue
        for fl in fp.GetFields():
            if fl.GetLayer() in SILK and fl.GetText() == r:
                out[r] = (fp, fl)
    return out


def refs_from_drc(path):
    """从 DRC 报告（探针语义）取 silk_over_copper/silk_overlap 涉及的位号。"""
    d = json.load(open(path, encoding="utf-8"))
    out = set()
    for v in d.get("violations", []):
        if v.get("type") in ("silk_over_copper", "silk_overlap"):
            for it in v.get("items", []):
                m = re.match(r"\s*([A-Za-z]+\d+)\s*的", it.get("description", ""))
                if m:
                    out.add(m.group(1))
    return out


def geo_offenders(bd):
    """几何自检（字形级，仅碰撞语义）出的丝印位号冲突件。"""
    bad = []
    for fp in bd.GetFootprints():
        for fl in fp.GetFields():
            if fl.GetLayer() not in SILK or fl.GetText() != fp.GetReference() or not fl.IsVisible():
                continue
            silk_l, mask_l = sides(fl.GetLayer())
            mask, silk = collect(bd, silk_l, mask_l, {uid(fl)})
            ev = make_eval(fl, mask, silk, None)   # 仅碰撞语义 = DRC
            p = fl.GetPosition()
            if not ev(p.x, p.y, int(round(fl.GetTextAngleDegrees())) % 180):
                bad.append(fp.GetReference())
    return sorted(set(bad))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--refs", default="")
    ap.add_argument("--auto", action="store_true", help="几何自检（可能含板框类噪声，仅诊断用）")
    ap.add_argument("--drc-report", default="", help="探针语义 DRC JSON：从中取待修位号（= DRC 定位）")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--expect-sha16", default="")
    ap.add_argument("--out-name", default="silk-fixed")
    ap.add_argument("--max-shift-mm", type=float, default=3.0)
    ap.add_argument("--confirm-repo-write", action="store_true")
    ap.add_argument("--drc-cli", default="")
    ap.add_argument("--drc-pro", default="")
    ap.add_argument("--fp-lib-table", default="")
    ap.add_argument("--lib-dir", default="")
    ap.add_argument("--baseline-report", default="")
    a = ap.parse_args(argv)

    src, wd = os.path.abspath(a.board), os.path.abspath(a.work_dir)
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    if (wd == repo or wd.startswith(repo + os.sep)) and not a.confirm_repo_write:
        print(f"REFUSE: work-dir 在仓库内（{wd}）且无 --confirm-repo-write（T-41）")
        return 3
    if a.expect_sha16 and sha16(src) != a.expect_sha16:
        print(f"REFUSE: 输入板 sha16={sha16(src)} != 期望 {a.expect_sha16}")
        return 4
    os.makedirs(wd, exist_ok=True)

    bd = pcbnew.LoadBoard(src)
    print(f"输入板 {os.path.basename(src)} sha16={sha16(src)}（{len(bd.GetFootprints())} 颗）")
    refs = {s for s in a.refs.split(",") if s}
    if a.drc_report and os.path.exists(a.drc_report):
        got = refs_from_drc(a.drc_report)
        print(f"DRC 报告的丝印冲突位号：{sorted(got)}")
        refs |= got
    if a.auto:
        geo = geo_offenders(bd)
        print(f"几何自检（字形级）冲突位号：{geo}")
        refs |= set(geo)
    targets = targets_of(bd, refs)
    print(f"求解目标：{sorted(targets)}")
    if not targets:
        print("无目标（输入板该口径下已无丝印位号冲突）")
        return 0

    mask_shift = int(a.max_shift_mm * NM)
    snap = {r: ((targets[r][1].GetPosition().x, targets[r][1].GetPosition().y),
                int(round(targets[r][1].GetTextAngleDegrees()))) for r in targets}
    # 先粗算可行落点数 → 少者先解（粗算只读：前后快照复位）
    order = []
    for r in sorted(targets):
        fp, fl = targets[r]
        silk_l, mask_l = sides(fl.GetLayer())
        skip = {uid(targets[x][1]) for x in targets}
        mask, silk = collect(bd, silk_l, mask_l, skip)
        ev = make_eval(fl, mask, silk, outline_of(bd))
        _sol, free = solve(fl, fp, ev, snap[r][0], *text_wh(fl),
                           step=COARSE_STEP, ndir=COARSE_DIRS, rmax=COARSE_MAX)
        order.append((free, r))
    for r in targets:
        fl = targets[r][1]
        fl.SetTextAngleDegrees(snap[r][1])
        fl.SetPosition(pcbnew.VECTOR2I(*snap[r][0]))
    order.sort()

    rep = {"input": src, "input_sha16": sha16(src), "refs": sorted(targets), "moves": [], "unplaced": []}
    placed = collections.defaultdict(list)
    for _free, r in order:
        fp, fl = targets[r]
        silk_l, mask_l = sides(fl.GetLayer())
        skip = {uid(targets[x][1]) for x in targets}
        mask, silk = collect(bd, silk_l, mask_l, skip)
        silk = silk + [(None, s) for s in placed[silk_l]]
        ev = make_eval(fl, mask, silk, outline_of(bd))
        old = snap[r][0]
        sol, free = solve(fl, fp, ev, old, *text_wh(fl), max_shift=mask_shift)
        if sol is None:
            fl.SetPosition(pcbnew.VECTOR2I(*old))
            rep["unplaced"].append({"ref": r, "why": f"{a.max_shift_mm}mm/0-90° 内无落点"})
            print(f"  [UNPLACED] {r}（粗算免费落点 {free}）")
            continue
        fl.SetTextAngleDegrees(sol["ang"])
        fl.SetPosition(pcbnew.VECTOR2I(*sol["pos"]))
        placed[silk_l].append(fl.GetEffectiveTextShape())
        mv = {"ref": r, "from": list(old), "to": list(sol["pos"]), "angle": sol["ang"],
              "shift_mm": round(sol["shift_nm"] / NM, 3), "n_free": sol["n_free"],
              "side": "B" if silk_l == pcbnew.B_SilkS else "F"}
        rep["moves"].append(mv)
        print(f"  [MOVE] {r}: {mv['from']} -> {mv['to']} ang={mv['angle']} shift={mv['shift_mm']}mm")

    rep["after_geo_offenders"] = geo_offenders(bd)
    out = os.path.join(wd, a.out_name + ".kicad_pcb")
    if a.apply and rep["moves"]:
        pcbnew.SaveBoard(out, bd)
        rep["out"], rep["out_sha16"] = out, sha16(out)
        print(f"写出 {out} sha16={rep['out_sha16']}")
    else:
        print("dry-run：未写板（--apply 才写）")

    if a.drc_cli and a.drc_pro and rep.get("out"):
        vd = os.path.join(wd, "verify")
        os.makedirs(vd, exist_ok=True)
        stem = a.out_name
        shutil.copy2(out, os.path.join(vd, stem + ".kicad_pcb"))
        shutil.copy2(a.drc_pro, os.path.join(vd, stem + ".kicad_pro"))
        if a.fp_lib_table:
            shutil.copy2(a.fp_lib_table, os.path.join(vd, "fp-lib-table"))
        if a.lib_dir and not os.path.exists(os.path.join(vd, "lib")):
            os.symlink(os.path.abspath(a.lib_dir), os.path.join(vd, "lib"))
        dj = os.path.join(vd, "drc.json")
        p = subprocess.run([a.drc_cli, "pcb", "drc", "--format", "json", "--severity-all",
                            "--output", dj, os.path.join(vd, stem + ".kicad_pcb")],
                           capture_output=True, text=True)
        if p.returncode != 0 or not os.path.exists(dj):
            print(f"DRC 失败 rc={p.returncode}\n{p.stdout}\n{p.stderr}")
            return 6
        d = json.load(open(dj, encoding="utf-8"))
        c = collections.Counter(v["type"] for v in d["violations"])
        print(f"DRC（探针语义）violations={len(d['violations'])} 未连接={len(d.get('unconnected_items', []))}")
        for k, n in sorted(c.items()):
            print(f"   {n:4d} {k}")
        rep["drc_counts"] = dict(c)
        rep["drc_unconnected"] = len(d.get("unconnected_items", []))
        if a.baseline_report and os.path.exists(a.baseline_report):
            b = json.load(open(a.baseline_report, encoding="utf-8"))
            cb = collections.Counter(v["type"] for v in b["violations"])
            rep["drc_delta"] = {k: c.get(k, 0) - cb.get(k, 0) for k in set(c) | set(cb)}
            print(f"   对基线差值：{rep['drc_delta']}")

    with open(os.path.join(wd, "silk_fix_report.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2, ensure_ascii=False)
    print(f"几何剩余冲突：{rep['after_geo_offenders']}；未落位：{[u['ref'] for u in rep['unplaced']]}")
    return 0 if not rep["unplaced"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
