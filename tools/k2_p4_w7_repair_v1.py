#!/usr/bin/env python3
"""K2 · P4 · W-7 施工修复器 v2 —— dry-run 默认，**不写仓库**。

把 W-7 已登记 9 条 `ignore` 中尚未处置的 5 类（146 条）做成「可落件器」：
只在 `--work-dir` 内产出修复板 + 复算报告；仓库内（板 / pro / SPEC 原件 / criteria/）
逐字节不动。落件须监理逐条批后另行走 T-22 步骤。

组：
  via_dangling  12 条  删除孤立过孔（两端无铜 ⇒ 电气零影响）
  tncv          30 条  走线端点对孔心居中 —— 几何求解 + **逐案 DRC 复算 + 回退**
  courtyard     40 条  补 F.CrtYd（须显式 --courtyard-margin；口径属监理，默认只出测量）
  silk          64 条  位号文本移出阻焊开窗/互叠区（**真实几何**：丝印线段按胶囊、pad 按开窗外框）
                      + 6 条封装丝印线段**按开窗裁剪**（v2）

复算口径：KiCad 自身 DRC。本工具在 work-dir 的 pro 副本上把 9 条 severity
`ignore → warning`（**探针，非安装**），不改 criteria/、不产判据。
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pcbnew

NM = 1_000_000  # nm / mm
KIID_SEED = 20_260_918   # 固定种子 ⇒ 新建封装丝印线段的 uuid 可复现（两次复跑逐字节同）
RULES9 = [
    "copper_sliver", "footprint_filters_mismatch", "footprint_type_mismatch",
    "tuning_profile_track_geometries", "missing_courtyard", "silk_over_copper",
    "silk_overlap", "track_not_centered_on_via", "via_dangling",
]
SILK_TYPES = {"silk_over_copper", "silk_overlap"}
GATED_TYPES = {"lib_footprint_mismatch"}          # 不在本工具处置范围（W-8/O-2）
CASE_TYPES = {"track_not_centered_on_via"}
LINE_TOL_NM = 2                                    # 共线判定容差
END_TOL_NM = 2_000                                 # 认定「同一节点/同端点」的容差


# --------------------------------------------------------------------- helpers
def sha16(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def uid(obj) -> str:
    try:
        return obj.m_Uuid.AsString()
    except Exception:
        return str(obj.m_Uuid)


def fmm(nm: int) -> float:
    return round(nm / NM, 6)


def dist(a, b) -> float:
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def angle_ok(a, b) -> bool:
    """a→b 是否落在 0/45/90°（nm 容差 LINE_TOL_NM）。"""
    dx, dy = abs(b.x - a.x), abs(b.y - a.y)
    if dx == 0 or dy == 0:
        return True
    return abs(dx - dy) <= LINE_TOL_NM


def on_line(s, e, p, tol=LINE_TOL_NM) -> bool:
    """p 是否落在 s→e 确定的**无限直线**上（容差 tol nm）。"""
    dx, dy = e.x - s.x, e.y - s.y
    if dx == 0 and dy == 0:
        return False
    cross = (p.x - s.x) * dy - (p.y - s.y) * dx
    return abs(cross) <= tol * max(abs(dx), abs(dy))


def line_intersect(a, b, c, d):
    """a→b 与 c→d 两条无限直线交点（整数 nm 取整）；平行/重合返回 None。"""
    r = (b.x - a.x, b.y - a.y)
    s = (d.x - c.x, d.y - c.y)
    den = r[0] * s[1] - r[1] * s[0]
    if den == 0:
        return None
    t = ((c.x - a.x) * s[1] - (c.y - a.y) * s[0]) / den
    return pcbnew.VECTOR2I(int(round(a.x + t * r[0])), int(round(a.y + t * r[1])))


def is_via(o) -> bool:
    return o is not None and o.GetClass() == "PCB_VIA"


def is_track(o) -> bool:
    return o is not None and o.GetClass() in ("PCB_TRACK", "PCB_ARC")


# ----------------------------------------------------------------------- index
class Index:
    def __init__(self, board):
        self.board = board
        self.tracks, self.fps, self.owner = {}, {}, {}
        for t in board.GetTracks():
            self.tracks[uid(t)] = t
        for f in board.GetFootprints():
            self.fps[uid(f)] = f
            for it in f.GraphicalItems():
                self.owner[uid(it)] = f
            for fl in f.GetFields():
                self.owner[uid(fl)] = f

    def item(self, u):
        return self.tracks.get(u) or self.owner.get(u)

    def fp_of(self, u):
        return self.owner.get(u) or self.fps.get(u)


# ------------------------------------------------------------- drc / pro probe
def probe_pro(pro_src, dest_dir, stem, severities="warning"):
    os.makedirs(dest_dir, exist_ok=True)
    dst = os.path.join(dest_dir, stem + ".kicad_pro")
    with open(pro_src, encoding="utf-8") as fh:
        data = json.load(fh)
    sev = data["board"]["design_settings"]["rule_severities"]
    for r in RULES9:
        sev[r] = severities
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return dst


def stage(board_src, pro_src, dest_dir, stem):
    os.makedirs(dest_dir, exist_ok=True)
    bdst = os.path.join(dest_dir, stem + ".kicad_pcb")
    if os.path.abspath(board_src) != os.path.abspath(bdst):
        shutil.copy2(board_src, bdst)
    probe_pro(pro_src, dest_dir, stem)
    ft = os.path.join(os.path.dirname(os.path.abspath(board_src)), "fp-lib-table")
    if os.path.exists(ft):
        shutil.copy2(ft, os.path.join(dest_dir, "fp-lib-table"))
    lib = os.path.join(dest_dir, "lib")
    if not os.path.exists(lib):
        os.symlink(os.path.join(os.path.dirname(os.path.abspath(board_src)), "lib"), lib)
    return bdst


def run_drc(kicad_cli, board, out_json):
    cmd = [kicad_cli, "pcb", "drc", "--format", "json", "--severity-all",
           "--output", out_json, board]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 or not os.path.exists(out_json):
        raise RuntimeError(f"drc rc={p.returncode}\n{p.stdout}\n{p.stderr}")
    with open(out_json, encoding="utf-8") as fh:
        return json.load(fh)


def counts(rep):
    c = collections.Counter((v["severity"], v["type"]) for v in rep.get("violations", []))
    return {f"{a}:{b}": n for (a, b), n in sorted(c.items())}


def vios(rep, types):
    return [v for v in rep.get("violations", []) if v["type"] in types]


def unconn(rep):
    return len(rep.get("unconnected_items", []))


# ------------------------------------------------- tncv solver (per-via group)
def group_tncv(idx, rep):
    """{via_uuid: {'via':via, 'off':[(track,..)], 'coin':[track,..]}}"""
    groups = collections.defaultdict(lambda: {"via": None, "off": [], "coin": []})
    for v in vios(rep, CASE_TYPES):
        via = tk = None
        for it in v["items"]:
            o = idx.item(it["uuid"])
            if is_via(o):
                via = o
            elif is_track(o):
                tk = o
        if via is None or tk is None:
            continue
        g = groups[uid(via)]
        g["via"] = via
        if uid(tk) not in [uid(t) for t in g["off"]]:
            g["off"].append(tk)
    for k, g in groups.items():
        via = g["via"]
        vp = via.GetPosition()
        for t in idx.board.GetTracks():
            if not is_track(t) or uid(t) == k:
                continue
            for p in (t.GetStart(), t.GetEnd()):
                if dist(p, vp) <= END_TOL_NM:
                    g["coin"].append(t)
                    break
    return groups


def candidates_for_via(g, max_shift_nm=260_000, top=8):
    """按（孔不动优先, 变动对象数, 最大位移）排序返回候选 [(P,(x,y),plan), ...]。"""
    via = g["via"]
    vp = via.GetPosition()
    tracks = []
    for t in g["off"] + g["coin"]:
        if uid(t) not in [uid(x) for x in tracks]:
            tracks.append(t)
    if not tracks:
        return []
    cands = [pcbnew.VECTOR2I(vp.x, vp.y)]
    for t in tracks:
        s0, e0 = t.GetStart(), t.GetEnd()
        cands += [s0, e0]
        # v2.1：孔心到本走线**直线**的投影（端点沿自身直线微移即保持 0/45/90；
        #       原候选集只含端点/交点，会漏掉「小位移且合法」的解）
        dx, dy = e0.x - s0.x, e0.y - s0.y
        L2 = dx * dx + dy * dy
        if L2:
            tt = ((vp.x - s0.x) * dx + (vp.y - s0.y) * dy) / L2
            cands.append(pcbnew.VECTOR2I(int(round(s0.x + tt * dx)),
                                         int(round(s0.y + tt * dy))))
    for i in range(len(tracks)):
        for j in range(i + 1, len(tracks)):
            pt = line_intersect(tracks[i].GetStart(), tracks[i].GetEnd(),
                                tracks[j].GetStart(), tracks[j].GetEnd())
            if pt is not None:
                cands.append(pt)
    scored = []
    for P in cands:
        if dist(P, vp) > max_shift_nm:
            continue
        plan, ok, maxsh = {}, True, dist(P, vp)
        for t in tracks:
            s0, e0 = t.GetStart(), t.GetEnd()
            side = "S" if dist(P, s0) <= dist(P, e0) else "E"
            cur = s0 if side == "S" else e0
            other = e0 if side == "S" else s0
            if (cur.x, cur.y) == (P.x, P.y):
                continue
            if not angle_ok(other, P):
                ok = False
                break
            plan[uid(t)] = (side, (P.x, P.y))
            maxsh = max(maxsh, dist(cur, P))
        if not ok:
            continue
        moved_via = 1 if (P.x, P.y) != (vp.x, vp.y) else 0
        scored.append(((moved_via, len(plan), round(maxsh)), (P.x, P.y), plan))
    scored.sort(key=lambda z: z[0])
    return scored[:top]


def seg_touches(s, e, p, tol=LINE_TOL_NM) -> bool:
    """点 p 是否落在 s→e 线段上（含端点与中段，容差 tol nm）。"""
    dx, dy = e.x - s.x, e.y - s.y
    if dx == 0 and dy == 0:
        return abs(p.x - s.x) <= tol and abs(p.y - s.y) <= tol
    t = ((p.x - s.x) * dx + (p.y - s.y) * dy) / (dx * dx + dy * dy)
    if t < -1e-9 or t > 1 + 1e-9:
        return False
    cx, cy = s.x + t * dx, s.y + t * dy
    return abs(p.x - cx) <= tol and abs(p.y - cy) <= tol


def mutate_delete_via(vkey):
    def fn(bd, idx2):
        via = None
        for t in bd.GetTracks():
            if is_via(t) and uid(t) == vkey:
                via = t
                break
        if via is None:
            raise RuntimeError("via not found")
        vp = via.GetPosition()
        tracks = [t for t in bd.GetTracks() if is_track(t)]
        pads = [(f.GetReference() + "." + p.GetPadName(), p.GetPosition())
                for f in bd.GetFootprints() for p in f.Pads()]
        dead = set()
        frontier = [vp]
        guard = 0
        while frontier and guard < 64:
            guard += 1
            pt = frontier.pop()
            for t in tracks:
                if uid(t) in dead:
                    continue
                for p, side in ((t.GetStart(), "S"), (t.GetEnd(), "E")):
                    if p.x != pt.x or p.y != pt.y:
                        continue
                    other = t.GetEnd() if side == "S" else t.GetStart()
                    # other 处的其它铜（含**中段穿越**的 T 节点，逐步回溯的关键）
                    n_other = 0
                    for t2 in tracks:
                        if uid(t2) == uid(t) or uid(t2) in dead:
                            continue
                        if seg_touches(t2.GetStart(), t2.GetEnd(), other):
                            n_other += 1
                    n_pad = sum(1 for _, pp in pads
                                if pp.x == other.x and pp.y == other.y)
                    dead.add(uid(t))
                    # 仅「唯一后继走线且无焊盘」才继续回溯；否则此支路到此为止
                    if n_pad == 0 and n_other <= 1:
                        frontier.append(other)
                    break
        killed = []
        for t in tracks:
            if uid(t) in dead:
                killed.append([uid(t)[:8], pcbnew.LayerName(t.GetLayer())])
                bd.RemoveNative(t)
        net = via.GetNetname()
        bd.RemoveNative(via)
        return {"via": vkey[:8], "net": net, "pos": [vp.x, vp.y],
                "deleted_tracks": killed}
    return fn


def mutate_tncv(vkey, off_keys=None, gmax=6):
    """返回候选 mutate 函数列表（按优先级）。每个候选自行重算几何。"""
    off_keys = set(off_keys or [])

    def variants(bd, idx2):
        via = None
        for t in bd.GetTracks():
            if is_via(t) and uid(t) == vkey:
                via = t
                break
        if via is None:
            raise RuntimeError("via not found")
        vp = via.GetPosition()
        g = {"via": via, "off": [], "coin": []}
        for t in bd.GetTracks():
            if not is_track(t):
                continue
            if uid(t) in off_keys:
                g["off"].append(t)
                continue
            for p in (t.GetStart(), t.GetEnd()):
                if dist(p, vp) <= END_TOL_NM:
                    g["coin"].append(t)
                    break
        out = []
        for score, target, plan in candidates_for_via(g, top=gmax):
            out.append((score, target, {k: v for k, v in plan.items()}))
        return out, vp, via.GetNetname()

    def apply_plan(bd, idx2, target, plan):
        via = None
        for t in bd.GetTracks():
            if is_via(t) and uid(t) == vkey:
                via = t
                break
        vp = via.GetPosition()
        if (target[0], target[1]) != (vp.x, vp.y):
            via.SetPosition(pcbnew.VECTOR2I(*target))
        moves = []
        for tkey, (side, tgt) in plan.items():
            for t in bd.GetTracks():
                if is_track(t) and uid(t) == tkey:
                    b0 = t.GetStart() if side == "S" else t.GetEnd()
                    before = (b0.x, b0.y)
                    if side == "S":
                        t.SetStart(pcbnew.VECTOR2I(*tgt))
                    else:
                        t.SetEnd(pcbnew.VECTOR2I(*tgt))
                    moves.append({"track": tkey[:8], "side": side,
                                  "from": list(before), "to": list(tgt)})
                    break
        return {"via": vkey[:8], "net": via.GetNetname(),
                "via_from": [vp.x, vp.y], "via_to": list(target), "moves": moves}

    return variants, apply_plan


def expand(box, mm_nm):
    """BOX2I(原点, 尺寸) —— 四周各外扩 mm_nm（负值 = 收缩）。"""
    return pcbnew.BOX2I(
        pcbnew.VECTOR2I(box.GetX() - mm_nm, box.GetY() - mm_nm),
        pcbnew.VECTOR2I(box.GetWidth() + 2 * mm_nm, box.GetHeight() + 2 * mm_nm))


def boxes_intersect(a, b) -> bool:
    return not (a.GetRight() < b.GetLeft() or b.GetRight() < a.GetLeft()
                or a.GetBottom() < b.GetTop() or b.GetBottom() < a.GetTop())


def silk_field_by_uuid(bd, fuuid):
    for f in bd.GetFootprints():
        for fl in f.GetFields():
            if uid(fl) == fuuid:
                return f, fl
    return None, None


def silk_candidates(fp, old, rings=(0.05, 0.15, 0.3, 0.5, 0.75, 1.0, 1.4, 1.9, 2.5, 3.2, 4.0)):
    """环绕本体的候选落点（8 方向 × 多环），按离原位置距离升序。"""
    bb = fp.GetBoundingBox(False, False)
    cx, cy = bb.GetCenter().x, bb.GetCenter().y
    tbb = old
    tw = max(0.35 * NM, 0.75 * NM)          # 文本半宽（1.0mm 字高 ≈ 0.5mm 半高）
    th = 0.55 * NM
    hw = bb.GetWidth() / 2.0 + tw
    hh = bb.GetHeight() / 2.0 + th
    dirs = []
    for k in range(16):                      # 16 向，避免密集区被迫远移
        ang = 2 * 3.141592653589793 * k / 16
        dirs.append((round(2 * __import__("math").sin(ang), 6),
                     round(-2 * __import__("math").cos(ang), 6)))
    out = []
    for r in rings:
        for dx, dy in dirs:
            x = cx + dx * (hw + r * NM) / 2.0
            y = cy + dy * (hh + r * NM) / 2.0
            out.append(pcbnew.VECTOR2I(int(round(x)), int(round(y))))
    out.sort(key=lambda v: (v.x - old.x) ** 2 + (v.y - old.y) ** 2)
    return out


def find_fp_graphic(bd, guuid):
    for f in bd.GetFootprints():
        for g in f.GraphicalItems():
            if uid(g) == guuid:
                return f, g
    return None, None


def seg_rect_dist(sx, sy, ex, ey, r) -> float:
    """线段 ↔ 轴对齐矩形的距离（相交 = 0）。"""
    x0, y0, x1, y1 = r
    # 端点是否在矩形内
    def inside(px, py):
        return x0 <= px <= x1 and y0 <= py <= y1
    if inside(sx, sy) or inside(ex, ey):
        return 0.0
    # 线段与矩形边是否相交
    def seg_seg(p, q, r0, r1):
        d = (q[0] - p[0]) * (r1[1] - r0[1]) - (q[1] - p[1]) * (r1[0] - r0[0])
        if d == 0:
            return False
        t = ((r0[0] - p[0]) * (r1[1] - r0[1]) - (r0[1] - p[1]) * (r1[0] - r0[0])) / d
        u = ((r0[0] - p[0]) * (q[1] - p[1]) - (r0[1] - p[1]) * (q[0] - p[0])) / d
        return 0 <= t <= 1 and 0 <= u <= 1
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for i in range(4):
        if seg_seg((sx, sy), (ex, ey), corners[i], corners[(i + 1) % 4]):
            return 0.0
    best = float("inf")
    for cx, cy in corners:
        best = min(best, pt_seg_dist(cx, cy, sx, sy, ex, ey))
    for px, py in ((sx, sy), (ex, ey)):
        best = min(best, pt_rect_dist(px, py, r))
    return best


def pt_seg_dist(px, py, sx, sy, ex, ey) -> float:
    dx, dy = ex - sx, ey - sy
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return ((px - sx) ** 2 + (py - sy) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / L2))
    cx, cy = sx + t * dx, sy + t * dy
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def pt_rect_dist(px, py, r) -> float:
    x0, y0, x1, y1 = r
    dx = max(x0 - px, 0, px - x1)
    dy = max(y0 - py, 0, py - y1)
    return (dx * dx + dy * dy) ** 0.5


def rect_intersects(r1, r2) -> bool:
    return not (r1[2] <= r2[0] or r2[2] <= r1[0] or r1[3] <= r2[1] or r2[3] <= r1[1])


def obstacles(bd, skip_field_uuid=None, silk_layer=None, mask_layer=None):
    """真实几何障碍（按面）：mask = pad 开窗外框；silk = 线段胶囊 + 其它丝印外框。"""
    silk_layer = pcbnew.F_SilkS if silk_layer is None else silk_layer
    mask_layer = pcbnew.F_Mask if mask_layer is None else mask_layer
    mask, segs, boxes = [], [], []
    for f in bd.GetFootprints():
        for pad in f.Pads():
            try:
                if not pad.IsOnLayer(mask_layer):
                    continue
            except Exception:
                pass
            try:
                exp = pad.GetSolderMaskExpansion(mask_layer)
            except Exception:
                exp = 0
            bb = pad.GetBoundingBox()
            m = int(exp) + 30_000
            mask.append((bb.GetX() - m, bb.GetY() - m,
                         bb.GetX() + bb.GetWidth() + m, bb.GetY() + bb.GetHeight() + m))
        for g in f.GraphicalItems():
            if g.GetLayer() != silk_layer:
                continue
            if g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                s, e = g.GetStart(), g.GetEnd()
                segs.append((s.x, s.y, e.x, e.y, g.GetWidth() / 2.0 + 40_000))
            else:
                bb = g.GetBoundingBox()
                boxes.append((bb.GetX() - 40_000, bb.GetY() - 40_000,
                              bb.GetX() + bb.GetWidth() + 40_000,
                              bb.GetY() + bb.GetHeight() + 40_000))
        for fl in f.GetFields():
            if uid(fl) == skip_field_uuid:
                continue
            if fl.GetLayer() != silk_layer:
                continue
            bb = fl.GetBoundingBox()
            boxes.append((bb.GetX() - 40_000, bb.GetY() - 40_000,
                          bb.GetX() + bb.GetWidth() + 40_000,
                          bb.GetY() + bb.GetHeight() + 40_000))
    return mask, segs, boxes


def side_layers(silk_layer):
    if silk_layer == pcbnew.B_SilkS:
        return pcbnew.B_SilkS, pcbnew.B_Mask, pcbnew.B_Fab
    return pcbnew.F_SilkS, pcbnew.F_Mask, pcbnew.F_Fab


def text_free(tb, mask, segs, boxes) -> bool:
    x0, y0, x1, y1 = tb
    for m in mask:
        if rect_intersects(tb, m):
            return False
    for b in boxes:
        if rect_intersects(tb, b):
            return False
    for sx, sy, ex, ey, clr in segs:
        if seg_rect_dist(sx, sy, ex, ey, tb) < clr:
            return False
    return True


def clip_rect_interval(sx, sy, ex, ey, r):
    """线段对矩形的 Liang-Barsky 参数区间；无交返回 None。"""
    x0, y0, x1, y1 = r
    dx, dy = ex - sx, ey - sy
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, sx - x0), (dx, x1 - sx), (-dy, sy - y0), (dy, y1 - sy)):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return (t0, t1)


def subtract_interval(keep, cut):
    out = []
    for a, b in keep:
        if cut[1] <= a or cut[0] >= b:
            out.append((a, b))
            continue
        if cut[0] > a:
            out.append((a, cut[0]))
        if cut[1] < b:
            out.append((cut[1], b))
    return out


def mutate_silk_seg_tofab(guuid):
    """整段丝印线段移出丝印层（→ F.Fab）：非破坏性，保留文档但不印在丝印上。"""
    def fn(bd, idx):
        fp, g = find_fp_graphic(bd, guuid)
        if g is None:
            raise RuntimeError("segment not found")
        old = pcbnew.LayerName(g.GetLayer())
        _s, _m, fab = side_layers(g.GetLayer())
        g.SetLayer(fab)
        s, e = g.GetStart(), g.GetEnd()
        return {"seg": guuid[:8], "ref": fp.GetReference(), "mode": "to_fab",
                "from_layer": old, "to_layer": pcbnew.LayerName(fab),
                "len_um": round((((e.x - s.x) ** 2 + (e.y - s.y) ** 2) ** 0.5) / 1000, 1)}
    return fn


def silk_seg_variants(guuid):
    """候选顺序：按开窗裁剪（余量递增；纯非破坏 = 截断 + 追加）→ 整段移 F.Fab。"""
    out = []
    for extra in (30_000, 80_000, 150_000, 250_000):
        out.append((f"clip{extra // 1000}", mutate_silk_seg(guuid, extra_nm=extra)))
    out.append(("tofab", mutate_silk_seg_tofab(guuid)))
    return out


def mutate_silk_seg(guuid, extra_nm=30_000, min_piece_nm=50_000):
    """按阻焊开窗裁剪丝印线段：**不删项** —— 原项截为第一段，其余段以新项追加。"""
    def fn(bd, idx):
        fp, g = find_fp_graphic(bd, guuid)
        if g is None:
            raise RuntimeError("segment not found")
        s, e = g.GetStart(), g.GetEnd()
        L = ((e.x - s.x) ** 2 + (e.y - s.y) ** 2) ** 0.5
        if L == 0:
            raise RuntimeError("zero-length segment")
        silk_l, mask_l, _fab = side_layers(g.GetLayer())
        mask, _, _ = obstacles(bd, silk_layer=silk_l, mask_layer=mask_l)
        mask = [(r[0] - extra_nm, r[1] - extra_nm, r[2] + extra_nm, r[3] + extra_nm)
                for r in mask]
        keep = [(0.0, 1.0)]
        for r in mask:
            iv = clip_rect_interval(s.x, s.y, e.x, e.y, r)
            if iv is not None:
                keep = subtract_interval(keep, iv)
        keep = [(a, b) for a, b in keep if (b - a) * L >= min_piece_nm]
        if not keep:
            return {"seg": guuid[:8], "ref": fp.GetReference(),
                    "unsolved": "entire-segment-inside-mask"}
        if len(keep) == 1 and abs(keep[0][0]) < 1e-9 and abs(keep[0][1] - 1.0) < 1e-9:
            return {"seg": guuid[:8], "ref": fp.GetReference(),
                    "unsolved": "no-mask-conflict"}

        def pt(t):
            return pcbnew.VECTOR2I(int(round(s.x + t * (e.x - s.x))),
                                   int(round(s.y + t * (e.y - s.y))))

        w = g.GetWidth()
        a0, b0 = keep[0]
        g.SetStart(pt(a0))
        g.SetEnd(pt(b0))
        for a, b in keep[1:]:
            sh = pcbnew.PCB_SHAPE(fp)
            sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
            sh.SetLayer(silk_l)
            sh.SetWidth(w)
            sh.SetStart(pt(a))
            sh.SetEnd(pt(b))
            fp.Add(sh)
        return {"seg": guuid[:8], "ref": fp.GetReference(), "mode": "clip",
                "pieces": len(keep), "extra_um": extra_nm // 1000,
                "kept_um": [round((b - a) * L / 1000, 1) for a, b in keep]}
    return fn


def silk_plan(bd, fuuid):
    """算该位号的候选配置表（按打分升序）与几何上下文。返回 (cands, meta)。"""
    fp, field = silk_field_by_uuid(bd, fuuid)
    if field is None:
        raise RuntimeError("field not found")
    silk_l, mask_l, _fab = side_layers(field.GetLayer())
    mask, segs, boxes = obstacles(bd, skip_field_uuid=fuuid,
                                  silk_layer=silk_l, mask_layer=mask_l)
    outline = expand(bd.GetBoardEdgesBoundingBox(), -200_000)
    ol = (outline.GetX(), outline.GetY(),
          outline.GetX() + outline.GetWidth(), outline.GetY() + outline.GetHeight())
    op = field.GetPosition()
    old = (op.x, op.y)
    base = field.GetBoundingBox()
    W0, H0 = base.GetWidth(), base.GetHeight()
    off_x = base.GetX() + W0 / 2.0 - old[0]
    off_y = base.GetY() + H0 / 2.0 - old[1]

    def box_for(cand, size_mm, ang):
        w = W0 * size_mm + (0 if size_mm > 0.95 else 60_000)
        h = H0 * size_mm + (0 if size_mm > 0.95 else 60_000)
        if ang == 90:
            w, h = h, w
        cx, cy = cand.x + off_x, cand.y + off_y
        return (cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)

    cands = []
    for size_mm in (1.0, 0.8):
        for ang in (0, 90):
            for cand in silk_candidates(fp, pcbnew.VECTOR2I(*old)):
                tb = box_for(cand, size_mm, ang)
                if not (ol[0] <= tb[0] and tb[2] <= ol[2]
                        and ol[1] <= tb[1] and tb[3] <= ol[3]):
                    continue
                if not text_free(tb, mask, segs, boxes):
                    continue
                d = int(((cand.x - old[0]) ** 2 + (cand.y - old[1]) ** 2) ** 0.5)
                score = d + (200_000 if size_mm < 0.95 else 0) \
                    + (300_000 if ang == 90 else 0)
                cands.append({"score": score, "shift_nm": d, "text_mm": size_mm,
                              "angle_deg": ang, "pos": (cand.x, cand.y)})
    cands.sort(key=lambda c: (c["score"], c["shift_nm"]))
    meta = {"ref": fp.GetReference(), "old": list(old),
            "side": "B" if silk_l == pcbnew.B_SilkS else "F"}
    return cands, meta


def mutate_silk_cfg(fuuid, cfg):
    def fn(bd, idx):
        fp, field = silk_field_by_uuid(bd, fuuid)
        if field is None:
            raise RuntimeError("field not found")
        size_mm, ang, (x, y) = cfg["text_mm"], cfg["angle_deg"], cfg["pos"]
        old = field.GetPosition()
        field.SetTextSize(pcbnew.VECTOR2I(int(size_mm * NM), int(size_mm * NM)))
        field.SetTextThickness(int((0.15 if size_mm > 0.95 else 0.12) * NM))
        field.SetTextAngleDegrees(ang)
        field.SetPosition(pcbnew.VECTOR2I(x, y))
        return {"field": fuuid[:8], "ref": fp.GetReference(),
                "from": [old.x, old.y], "to": [x, y], "text_mm": size_mm,
                "angle_deg": ang,
                "side": "B" if field.GetLayer() == pcbnew.B_SilkS else "F",
                "shift_nm": cfg["shift_nm"]}
    return fn


BASE_TYPES = {"lib_footprint_mismatch", "missing_courtyard", "track_dangling",
              "hole_to_hole"} | SILK_TYPES | CASE_TYPES | {"via_dangling"}


def load_idx(path):
    bd = pcbnew.LoadBoard(path)
    return bd, Index(bd)


def save_with_pro(bd, board_path, probe_pro_path):
    pcbnew.SaveBoard(board_path, bd)
    stem = os.path.splitext(os.path.basename(board_path))[0]
    shutil.copy2(probe_pro_path,
                 os.path.join(os.path.dirname(board_path), stem + ".kicad_pro"))


def refill(bd):
    pcbnew.ZONE_FILLER(bd).Fill(bd.Zones())


def type_hist(rep):
    return dict(collections.Counter(v["type"] for v in rep.get("violations", [])))


def delta_ok(rep_b, rep_a):
    """无新类型 / 无类型增量 / 无 error / 未连接 0 / 总量严格下降。"""
    bad = []
    hb, ha = type_hist(rep_b), type_hist(rep_a)
    for t in sorted(set(hb) | set(ha)):
        if ha.get(t, 0) > hb.get(t, 0):
            bad.append(f"{t}:{hb.get(t, 0)}->{ha.get(t, 0)}")
    for v in rep_a.get("violations", []):
        if v["severity"] == "error":
            bad.append(f"error:{v['type']}")
    if unconn(rep_a) > 0:
        bad.append(f"unconnected:{unconn(rep_a)}")
    if sum(ha.values()) >= sum(hb.values()):
        bad.append("no-net-decrease")
    return bad


class Engine:
    """逐案「改板 → 重填 → 存盘 → DRC 复算 → 收/回退」。只写 work-dir。"""

    def __init__(self, cli, work, probe, good, rep):
        self.cli, self.work, self.probe = cli, work, probe
        self.good, self.rep = good, rep

    def attempt(self, tag, mutate):
        bd, idx = load_idx(self.good)
        try:
            rec = mutate(bd, idx) or {}
        except Exception as e:
            return False, {"tag": tag, "rejected": [f"exception:{e}"]}
        refill(bd)
        cand = os.path.join(self.work, "_cand.kicad_pcb")
        save_with_pro(bd, cand, self.probe)
        rc = run_drc(self.cli, cand, os.path.join(self.work, "drc_case.json"))
        bad = delta_ok(self.rep, rc)
        rec = dict(rec)
        rec["tag"] = tag
        if bad:
            rec["rejected"] = bad
            return False, rec
        safe = tag.replace(":", "_").replace("/", "_")
        nxt = os.path.join(self.work, f"_good_{safe}.kicad_pcb")
        shutil.copy2(cand, nxt)
        shutil.copy2(os.path.join(self.work, "_cand.kicad_pro"),
                     os.path.splitext(nxt)[0] + ".kicad_pro")
        self.good, self.rep = nxt, rc
        rec["accepted_sha16"] = sha16(nxt)
        return True, rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--pro", required=True)
    ap.add_argument("--kicad-cli", required=True)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--groups", default="via_dangling,tncv")
    ap.add_argument("--max-iters", type=int, default=8)
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)

    groups = [g for g in a.groups.split(",") if g]
    try:
        pcbnew.KIID.SeedGenerator(KIID_SEED)   # 复跑确定性（见 doc §6.1）
    except Exception:
        pass
    board_src, pro_src = os.path.abspath(a.board), os.path.abspath(a.pro)
    work = os.path.abspath(a.work_dir)
    os.makedirs(work, exist_ok=True)
    stem = os.path.splitext(os.path.basename(board_src))[0]
    rep_out = {"src": {"board": board_src, "board_sha16": sha16(board_src),
                       "pro": pro_src, "pro_sha16": sha16(pro_src)},
               "groups": groups, "work_dir": work, "log": {}}

    base = stage(board_src, pro_src, work, stem)
    probe = os.path.join(work, stem + ".kicad_pro")
    r0 = run_drc(a.kicad_cli, base, os.path.join(work, "drc_before.json"))
    rep_out["before"] = {"counts": counts(r0), "unconnected": unconn(r0)}
    eng = Engine(a.kicad_cli, work, probe, base, r0)

    if "via_dangling" in groups:
        bd, idx = load_idx(eng.good)
        keys = []
        for e in vios(eng.rep, {"via_dangling"}):
            o = idx.item(e["items"][0]["uuid"])
            if is_via(o):
                keys.append(uid(o))
        done, rejected = [], []
        for k in keys:
            ok, rec = eng.attempt(f"via_dangling:{k[:8]}", mutate_delete_via(k))
            (done if ok else rejected).append(rec)
        rep_out["log"]["via_dangling"] = {"accepted": done, "rejected": rejected}

    if "tncv" in groups:
        applied, rejected = [], []
        for it in range(a.max_iters):
            bd, idx = load_idx(eng.good)
            via_off = collections.defaultdict(set)
            for e in vios(eng.rep, CASE_TYPES):
                via = tk = None
                for it2 in e["items"]:
                    o = idx.item(it2["uuid"])
                    if is_via(o):
                        via = o
                    elif is_track(o):
                        tk = o
                if via is not None and tk is not None:
                    via_off[uid(via)].add(uid(tk))
            keys = sorted(via_off)
            if not keys:
                break
            progressed = 0
            for k in keys:
                variants, apply_plan = mutate_tncv(k, via_off[k])
                bd_t, idx_t = load_idx(eng.good)
                try:
                    cands, vp, net = variants(bd_t, idx_t)
                except Exception as e:
                    rejected.append({"via": k[:8], "rejected": [f"exception:{e}"]})
                    continue
                if not cands:
                    rejected.append({"via": k[:8], "net": net,
                                     "rejected": ["no-candidate-0/45/90+shift-cap"]})
                    continue
                okb, lastrec = False, None
                for score, target, plan in cands:
                    def fn(bd, idx2, _t=target, _p=plan):
                        return apply_plan(bd, idx2, _t, _p)
                    ok, rec = eng.attempt(f"tncv:{k[:8]}", fn)
                    if ok:
                        rec["score"] = list(score)
                        applied.append(rec)
                        progressed += 1
                        okb = True
                        break
                    lastrec = rec
                if not okb:
                    rejected.append(lastrec)
            if progressed == 0:
                break
        rep_out["log"]["tncv"] = {"applied": applied, "rejected": rejected}

    if "silk" in groups:
        f_app, s_app, rejected = [], [], []
        for it in range(a.max_iters):
            bd, idx = load_idx(eng.good)
            fkeys, skeys = [], []
            for e in vios(eng.rep, SILK_TYPES):
                for item in e["items"]:
                    fp, field = silk_field_by_uuid(bd, item["uuid"])
                    if field is not None and field.GetLayer() in (pcbnew.F_SilkS,
                                                                  pcbnew.B_SilkS):
                        if item["uuid"] not in fkeys:
                            fkeys.append(item["uuid"])
                        continue
                    gfp, g = find_fp_graphic(bd, item["uuid"])
                    if g is not None and g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) \
                            and g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                        if item["uuid"] not in skeys:
                            skeys.append(item["uuid"])
            if not fkeys and not skeys:
                break
            progressed = 0
            for k in fkeys + skeys:
                if k in fkeys:
                    bd_p, _ = load_idx(eng.good)
                    try:
                        cands, meta = silk_plan(bd_p, k)
                    except Exception as e:
                        rejected.append({"field": k[:8], "rejected": [f"exception:{e}"]})
                        continue
                    if not cands:
                        rejected.append({"field": k[:8], "ref": meta["ref"],
                                         "unsolved": "no-free-slot"})
                        continue
                    done_f, last_f = False, None
                    for cfg in cands[:4]:
                        ok, rec = eng.attempt(f"silk:{k[:8]}", mutate_silk_cfg(k, cfg))
                        if ok:
                            f_app.append(rec)
                            progressed += 1
                            done_f = True
                            break
                        last_f = rec
                    if not done_f:
                        rejected.append(last_f)
                done, last = False, None
                for tag, fn in silk_seg_variants(k):
                    ok, rec = eng.attempt(f"silkseg:{k[:8]}:{tag}", fn)
                    if ok:
                        rec["variant"] = tag
                        s_app.append(rec)
                        progressed += 1
                        done = True
                        break
                    rec.setdefault("tried", []).append(tag)
                    if last is None:
                        last = rec
                    else:
                        last.setdefault("tried", []).append(tag)
                        for kk, vv in rec.items():
                            if kk not in ("tried",):
                                last[kk] = vv
                if not done:
                    rejected.append(last)
            if progressed == 0:
                break
        rep_out["log"]["silk"] = {"applied": f_app + s_app,
                                 "applied_field": f_app, "applied_seg": s_app,
                                 "rejected": rejected}

    final = os.path.join(work, "k2_v4_8L.l5.repaired.kicad_pcb")
    bd, _ = load_idx(eng.good)
    refill(bd)
    save_with_pro(bd, final, probe)
    rf = run_drc(a.kicad_cli, final, os.path.join(work, "drc_after.json"))
    rep_out["after"] = {"counts": counts(rf), "unconnected": unconn(rf),
                        "board": final, "board_sha16": sha16(final)}
    out = a.report or os.path.join(work, "report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep_out, fh, indent=1, ensure_ascii=False)
    print(json.dumps({"before": rep_out["before"], "after": rep_out["after"]}, indent=1))
    for k, v in rep_out["log"].items():
        print(f"{k}: accepted={len(v.get('accepted', v.get('applied', [])))} "
              f"rejected={len(v.get('rejected', []))}")
    print("report:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
