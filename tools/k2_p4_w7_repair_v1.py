#!/usr/bin/env python3
"""K2 · P4 · W-7 施工修复器 v1 —— dry-run 默认，**不写仓库**。

把 W-7 已登记 9 条 `ignore` 中尚未处置的 5 类（146 条）做成「可落件器」：
只在 `--work-dir` 内产出修复板 + 复算报告；仓库内（板 / pro / SPEC 原件 / criteria/）
逐字节不动。落件须监理逐条批后另行走 T-22 步骤。

组：
  via_dangling  12 条  删除孤立过孔（两端无铜 ⇒ 电气零影响）
  tncv          30 条  走线端点对孔心居中 —— 几何求解 + **逐案 DRC 复算 + 回退**
  courtyard     40 条  补 F.CrtYd（须显式 --courtyard-margin；口径属监理，默认只出测量）
  silk          64 条  参考字段文本移出阻焊开窗/互叠区（v2 实现）

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


def candidates_for_via(g, max_shift_nm=260_000, top=6):
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
        cands += [t.GetStart(), t.GetEnd()]
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


def mutate_silk(fuuid):
    def fn(bd, idx):
        fp, field = silk_field_by_uuid(bd, fuuid)
        if field is None:
            raise RuntimeError("field not found")
        mask, silk = [], []
        for f in bd.GetFootprints():
            for pad in f.Pads():
                mask.append(expand(pad.GetBoundingBox(), 60_000))
            for g in f.GraphicalItems():
                if g.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                    silk.append(expand(g.GetBoundingBox(), 40_000))
            for fl in f.GetFields():
                if uid(fl) == fuuid:
                    continue
                if fl.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                    silk.append(expand(fl.GetBoundingBox(), 40_000))
        outline = expand(bd.GetBoardEdgesBoundingBox(), -200_000)
        op = field.GetPosition()
        old = (op.x, op.y)
        base = field.GetBoundingBox()          # 原位的真实文本外框
        bx0, by0 = base.GetX(), base.GetY()

        def box_at(cand):
            return expand(pcbnew.BOX2I(pcbnew.VECTOR2I(bx0 + cand.x - old[0],
                                                       by0 + cand.y - old[1]),
                                       pcbnew.VECTOR2I(base.GetWidth(),
                                                       base.GetHeight())), 40_000)

        # 先按原字号找位；若最近可行位 > 1.2mm，则允许缩到 0.8mm（= pro min_text_height）再找
        chosen = None
        for size_mm in (None, 0.8):
            if size_mm is not None:
                field.SetTextSize(pcbnew.VECTOR2I(int(size_mm * NM), int(size_mm * NM)))
                field.SetTextThickness(int(0.12 * NM))
                base = field.GetBoundingBox()
                bx0, by0 = base.GetX(), base.GetY()

                def box_at(cand, _b=(bx0, by0), _w=base.GetWidth(), _h=base.GetHeight()):
                    return expand(pcbnew.BOX2I(
                        pcbnew.VECTOR2I(_b[0] + cand.x - old[0], _b[1] + cand.y - old[1]),
                        pcbnew.VECTOR2I(_w, _h)), 40_000)
            best = None
            for cand in silk_candidates(fp, pcbnew.VECTOR2I(*old)):
                tb = box_at(cand)
                if not boxes_intersect(tb, outline):
                    continue
                if any(boxes_intersect(tb, b) for b in mask):
                    continue
                if any(boxes_intersect(tb, b) for b in silk):
                    continue
                d = int(((cand.x - old[0]) ** 2 + (cand.y - old[1]) ** 2) ** 0.5)
                if best is None or d < best[0]:
                    best = (d, cand)
                    if size_mm is None and d <= 1_200_000:
                        break
            if best is not None:
                if size_mm is None and best[0] <= 1_200_000:
                    chosen = (best[0], best[1], 1.0)
                    break
                if chosen is None or best[0] < chosen[0]:
                    chosen = (best[0], best[1], size_mm or 1.0)
        if chosen is not None:
            d, cand, size_mm = chosen
            field.SetTextSize(pcbnew.VECTOR2I(int(size_mm * NM), int(size_mm * NM)))
            field.SetTextThickness(int((0.15 if size_mm > 0.9 else 0.12) * NM))
            field.SetPosition(cand)
            return {"field": fuuid[:8], "ref": fp.GetReference(),
                    "from": list(old), "to": [cand.x, cand.y], "text_mm": size_mm,
                    "shift_nm": d}
        field.SetPosition(pcbnew.VECTOR2I(*old))
        field.SetTextSize(pcbnew.VECTOR2I(int(1.0 * NM), int(1.0 * NM)))
        field.SetTextThickness(int(0.15 * NM))
        return {"field": fuuid[:8], "ref": fp.GetReference(), "unsolved": "no-free-slot"}
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
        applied, rejected = [], []
        for it in range(a.max_iters):
            bd, idx = load_idx(eng.good)
            keys, kinds = [], {}
            for e in vios(eng.rep, SILK_TYPES):
                for item in e["items"]:
                    fp, field = silk_field_by_uuid(bd, item["uuid"])
                    if field is None or field.GetLayer() != pcbnew.F_SilkS:
                        kinds[item["uuid"]] = "not-ref-field"
                        continue
                    kinds[item["uuid"]] = "ref"
                    if item["uuid"] not in keys:
                        keys.append(item["uuid"])
            if not keys:
                break
            progressed = 0
            for k in keys:
                ok, rec = eng.attempt(f"silk:{k[:8]}", mutate_silk(k))
                if ok:
                    applied.append(rec)
                    progressed += 1
                else:
                    rejected.append(rec)
            if progressed == 0:
                break
        rep_out["log"]["silk"] = {"applied": applied, "rejected": rejected}

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
