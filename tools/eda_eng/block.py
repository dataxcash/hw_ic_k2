"""M0 · `eda_eng block` --- BLOCK 器件移位模型的**框选 + 三分法清册 + 块体搬运**（#K2-369 §三/§四）。

形式定义（**规则，不是经验值**）：
  R      = frame（框，mm）[x0,y0,x1,y1]
  Δ      = 块体位移
  swept  = bbox(R ∪ (R+Δ))                       # 块体运动的包络
  N*     = {net : pad ∈ R} ∪ {net : 铜 ∩ (swept ⊕ clearance)}     # **膨胀式**谓词
  三分法（逐段，对 R）：trk_in（两端在 R 内）· trk_cross（与 ∂R 相交）· trk_out（无交）
  孔：via_in（在 R 内）· via_out
  框接受判据：**FOREIGN_INSIDE == 0** —— 不得有"整段在 R 内、却属 N* 之外"的铜，
  否则块体搬运会拖动不属于块的铜（或留下会撞车的静止铜）⇒ 该框在模型上不成立。

块体搬运（step ① + M2 剪边，KiCad 一次改写）：
  · 两端在 R 内的段 ⇒ **随块刚性平移**（不重画，拓扑与相对几何都不变）
  · 与 ∂R 相交的段 ⇒ **切成两半**：块外半段**原地保留**（固定端口），块内半段**随块平移**；
    记录一条**重连作业**：端口(∂R) → 平移后的块内端点（= 端口+Δ）
  · 桥（两端在块外、中间穿 R）⇒ 中间段删掉，记录 port→port 作业（本场景实测 0 条）
  · 块外段 / 块外孔 ⇒ **零触碰**
本模块只做几何与账，不做布线；重连在 M3（`route.maze_route`）。
"""
from __future__ import annotations
import collections, hashlib, json, math, os, shutil, sys

CLEAR = 0.175

# ── 共享域层对接（#K2-370 §三.3 · 缺口 ③a）：几何原语一律取自 `_shared/eda_core/board_model`。
# 取不到时退回本模块的等价实现（纯 stdlib），但**census 会如实报告 `board_model.ok`**。
_SHARED = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "_shared")
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)
try:                                                                    # pragma: no cover - env dependent
    from eda_core.board_model.geometry import BBox as _BBox, Segment as _Segment, dist_point_segment as _dps
    import eda_core.board_model.geometry as _bm_geom
    BOARD_MODEL = True
    BOARD_MODEL_MODULE = _bm_geom.__file__
except Exception:                                                        # noqa: BLE001
    _BBox = _Segment = _dps = None
    BOARD_MODEL = False
    BOARD_MODEL_MODULE = None


def _P():
    import pcbnew as P
    return P


# ─────────────────────────────── 几何（mm float；rect = [x0,y0,x1,y1]） ───────────────────────────────
def bbox(rect):
    """rect(list) -> 共享层 BBox（取不到时退回 4 元组）。"""
    return _BBox(rect[0], rect[1], rect[2], rect[3]) if BOARD_MODEL else tuple(rect)


def inflate(rect, m):
    b = bbox(rect).inflate(m)
    return [b.x0, b.y0, b.x1, b.y1]


def union(a, b):
    return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]


def swept(rect, delta):
    """bbox(R ∪ (R+Δ))。"""
    return union(rect, [rect[0] + delta[0], rect[1] + delta[1], rect[2] + delta[0], rect[3] + delta[1]])


def pt_in(p, rect):
    return bbox(rect).contains(p[0], p[1])


def clip_interval(a, b, rect):
    """Liang-Barsky：线段 a..b 落在 rect 内的参数区间 (t0,t1)；无交返回 None。"""
    x0, y0, x1, y1 = rect
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if pp == 0:
            if qq < 0:
                return None
        else:
            t = qq / pp
            if pp < 0:
                if t > t1:
                    return None
                if t > t0:
                    t0 = t
            else:
                if t < t0:
                    return None
                if t < t1:
                    t1 = t
    return (t0, t1)


def lerp(a, b, t):
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]


def _seg_inside_parts(a, b, rect):
    """返回 (inside_parts, outside_parts)；对**凸** rect，各至多 1 / 2 段。"""
    iv = clip_interval(a, b, rect)
    if iv is None:
        return [], [(a, b)]
    t0, t1 = iv
    pin, pout = lerp(a, b, t0), lerp(a, b, t1)
    ins = [(pin, pout)] if (t1 - t0) > 1e-12 else []
    outs = []
    if t0 > 1e-9:
        outs.append((a, pin))
    if t1 < 1 - 1e-9:
        outs.append((pout, b))
    return ins, outs


def _canon(a, b):
    """线段规范化方向（端点字典序），返回扁平 4 元组（可哈希）。"""
    ta, tb = tuple(a), tuple(b)
    return ta + tb if ta <= tb else tb + ta


# ─────────────────────────────── 读板 ───────────────────────────────
def read_copper(board):
    """只读：全部 track/via 的 (net, layer, 几何, 宽)。"""
    P = _P()
    b = P.LoadBoard(board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    segs, vias = [], []
    for t in b.GetTracks():
        n = nets.get(t.GetNetCode(), "")
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            vias.append({"net": n, "at": [round(P.ToMM(pos.x), 4), round(P.ToMM(pos.y), 4)],
                         "drill": round(P.ToMM(t.GetDrill()), 4)})
        else:
            s, e = t.GetStart(), t.GetEnd()
            segs.append({"net": n, "layer": t.GetLayerName(), "width": round(P.ToMM(t.GetWidth()), 4),
                         "a": [round(P.ToMM(s.x), 4), round(P.ToMM(s.y), 4)],
                         "b": [round(P.ToMM(e.x), 4), round(P.ToMM(e.y), 4)]})
    return {"segments": segs, "vias": vias}


def pad_rect(board, refs=None):
    """给定 refs（默认全部）的**焊盘**包围盒。"""
    P = _P()
    b = P.LoadBoard(board)
    want = None if refs is None else set(refs)
    xs, ys = [], []
    for fp in b.GetFootprints():
        if want is not None and fp.GetReference() not in want:
            continue
        for p in fp.Pads():
            pos = p.GetPosition()
            xs.append(P.ToMM(pos.x)); ys.append(P.ToMM(pos.y))
    if not xs:
        return None
    return [round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)]


def refs_in_rect(board, rect, refs=None):
    """焊盘落在 rect 内的 ref（几何查询；含无网机械件）。"""
    P = _P()
    b = P.LoadBoard(board)
    want = None if refs is None else set(refs)
    out = []
    for fp in b.GetFootprints():
        if want is not None and fp.GetReference() not in want:
            continue
        for p in fp.Pads():
            pos = p.GetPosition()
            if pt_in((P.ToMM(pos.x), P.ToMM(pos.y)), rect):
                out.append(fp.GetReference())
                break
    return sorted(out)


def inside_split(board, rect, members=None):
    """把"焊盘在 rect 内"的器件分成三类：
      members        = 块体成员 C（**声明的** refs；未声明时 = 有网焊盘在 R 内者）
      mech_no_net    = R 内**无网**机械件（安装孔等）——**不搬**（板级特征，不是块的成员）
      foreign_pads   = R 内**有网**却不在 C 里的器件 —— 框接受判据之一（>0 ⇒ 该框不成立）
    """
    P = _P()
    b = P.LoadBoard(board)
    want = None if members is None else set(members)
    mem, mech, foreign = [], [], []
    for fp in b.GetFootprints():
        hit = False
        nets = set()
        for p in fp.Pads():
            pos = p.GetPosition()
            if pt_in((P.ToMM(pos.x), P.ToMM(pos.y)), rect):
                hit = True
                if p.GetNetname():
                    nets.add(p.GetNetname())
        if not hit:
            continue
        r = fp.GetReference()
        if not nets:
            mech.append(r)
        elif (want is not None and r in want) or (want is None):
            mem.append(r)
        else:
            foreign.append(r)
    return {"members": sorted(mem), "mech_no_net": sorted(mech), "foreign_pads": sorted(foreign)}


# ─────────────────────────────── 清册（M0/M1） ───────────────────────────────
def census(board, rect, delta, clearance=CLEAR, members=None):
    """框选三分法清册 + N*（膨胀式）+ 框接受判据读数。"""
    P = _P()
    b = P.LoadBoard(board)
    nets_map = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    pad_in, pad_out = collections.Counter(), collections.Counter()
    for fp in b.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if not n:
                continue
            pos = p.GetPosition()
            (pad_in if pt_in((P.ToMM(pos.x), P.ToMM(pos.y)), rect) else pad_out)[n] += 1
    S = swept(rect, delta)
    Sg = inflate(S, clearance)
    per = collections.defaultdict(collections.Counter)
    geo_in_swept = set()
    c = read_copper(board)
    for s in c["segments"]:
        n = s["net"]
        a, b_ = s["a"], s["b"]
        iv = clip_interval(a, b_, rect)
        if iv is None:
            per[n]["trk_out"] += 1
        elif pt_in(a, rect) and pt_in(b_, rect):
            per[n]["trk_in"] += 1
        else:
            per[n]["trk_cross"] += 1
        if clip_interval(a, b_, Sg) is not None:
            geo_in_swept.add(n)
    for v in c["vias"]:
        n = v["net"]
        per[n]["via_in" if pt_in(v["at"], rect) else "via_out"] += 1
        if pt_in(v["at"], Sg):
            geo_in_swept.add(n)
    N_pad = set(pad_in)
    N_star = sorted(N_pad | geo_in_swept)
    ins = inside_split(board, rect, members)
    foreign = collections.Counter()
    for s in c["segments"]:
        if s["net"] in N_pad:
            continue
        if pt_in(s["a"], rect) and pt_in(s["b"], rect):
            foreign[s["net"]] += 1
    T = collections.Counter()
    for n in per:
        for k, v in per[n].items():
            T[k] += v
    nstar_tot = {k: sum(per[n][k] for n in N_pad) for k in ("trk_in", "trk_cross", "trk_out", "via_in", "via_out")}
    return {
        "artifact": "eda_eng_block_census", "module": "M0", "board": board,
        "rect": [round(v, 4) for v in rect], "delta_mm": list(delta), "swept": [round(v, 4) for v in S],
        "clearance_mm": clearance, "swept_plus_clearance": [round(v, 4) for v in Sg],
        "n_pads_in": sum(pad_in.values()), "n_pads_out": sum(pad_out.values()),
        "refs_in_rect": refs_in_rect(board, rect),
        "members": ins["members"], "n_members": len(ins["members"]),
        "mech_no_net_inside": ins["mech_no_net"],
        "FOREIGN_PADS_INSIDE": {"count": len(ins["foreign_pads"]), "refs": ins["foreign_pads"]},
        "nets": {n: dict(per[n]) for n in sorted(per) if n},
        "N_star": N_star, "n_N_star": len(N_star),
        "N_pad_only": sorted(N_pad), "extra_by_inflation": sorted(geo_in_swept - N_pad),
        "FOREIGN_INSIDE": {"count": sum(foreign.values()), "by_net": dict(foreign)},
        "frame_ok": sum(foreign.values()) == 0 and len(ins["foreign_pads"]) == 0,
        "totals_all_nets": {k: T[k] for k in ("trk_in", "trk_cross", "trk_out", "via_in", "via_out")},
        "totals_N_star": nstar_tot,
        "board_model": {"ok": BOARD_MODEL, "module": BOARD_MODEL_MODULE,
                        "authority": "#K2-370 sec.3.3 (gap 3a): geometry primitives come from the shared layer"},
        "rule": "#K2-369 sec.4: N* = {pad in R} union {copper ∩ (swept (+) clearance)} - an INFLATED predicate "
                "(rule, not an empirical guard value); frame acceptance: FOREIGN_INSIDE == 0 AND "
                "FOREIGN_PADS_INSIDE == 0 (no extra netted component may sit inside the frame)",
    }


# ─────────────────────────────── 块体搬运（step ① + M2 剪边） ───────────────────────────────
def move_block(board, rect, delta, out, refs=None):
    """**一次改写**完成：挪 pad ＋ 平移块内铜 ＋ 剪穿边（块外半段保留＝固定端口）。
    返回重连作业表（M3 用）+ 读数。子进程专用（改板会破坏同进程 SWIG 态）。"""
    P = _P()
    b = P.LoadBoard(board)
    nets_map = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    dx, dy = P.FromMM(delta[0]), P.FromMM(delta[1])
    jobs, to_rm, to_add = [], [], []
    mv = {"segments": 0, "vias": 0, "cross_split": 0, "bridge_split": 0, "outside_kept": 0}
    for t in list(b.GetTracks()):
        n = nets_map.get(t.GetNetCode(), "")
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            if pt_in((P.ToMM(pos.x), P.ToMM(pos.y)), rect):
                t.Move(P.VECTOR2I(dx, dy))
                mv["vias"] += 1
            continue
        s, e = t.GetStart(), t.GetEnd()
        a = [P.ToMM(s.x), P.ToMM(s.y)]; z = [P.ToMM(e.x), P.ToMM(e.y)]
        ins, outs = _seg_inside_parts(a, z, rect)
        if not ins and len(outs) == 1 and not pt_in(a, rect) and not pt_in(z, rect):
            continue                                            # 块外：零触碰
        if ins and not outs:
            t.Move(P.VECTOR2I(dx, dy))                          # 两端在块内：随块刚性平移
            mv["segments"] += 1
            continue
        to_rm.append(t)
        lay, wid, code = t.GetLayer(), t.GetWidth(), t.GetNetCode()
        for (p, q) in outs:                                     # 块外半段：原地**逐点原样**保留
            to_add.append({"code": code, "layer": lay, "width": wid, "a": p, "b": q})
            mv["outside_kept"] += 1
        inside_owner = bool(ins) and (pt_in(a, rect) or pt_in(z, rect))
        if len(ins) == 1:
            (pin, pout) = ins[0]
            # **切点** = pout（∂R 上的交点）：块外半段的**内端**停在 pout（固定端口），
            # 块内半段随块平移 ⇒ 其外端落在 pout+Δ。重连作业 = pout -> pout+Δ（恰好一个 Δ 的缺口）。
            if inside_owner:
                to_add.append({"code": code, "layer": lay, "width": wid,
                               "a": [pin[0] + delta[0], pin[1] + delta[1]],
                               "b": [pout[0] + delta[0], pout[1] + delta[1]]})
                jobs.append({"kind": "cross", "net": n, "layer": b.GetLayerName(lay),
                             "port": [round(pout[0], 4), round(pout[1], 4)],
                             "target": [round(pout[0] + delta[0], 4), round(pout[1] + delta[1], 4)],
                             "width_mm": round(P.ToMM(wid), 4)})
                mv["cross_split"] += 1
            else:
                jobs.append({"kind": "bridge", "net": n, "layer": b.GetLayerName(lay),
                             "ports": [[round(ins[0][0][0], 4), round(ins[0][0][1], 4)],
                                       [round(ins[0][1][0], 4), round(ins[0][1][1], 4)]],
                             "width_mm": round(P.ToMM(wid), 4)})
                mv["bridge_split"] += 1
    for d in to_add:
        if (d["a"][0] - d["b"][0]) ** 2 + (d["a"][1] - d["b"][1]) ** 2 <= 1e-16:
            continue
        tr = P.PCB_TRACK(b)
        tr.SetStart(P.VECTOR2I(P.FromMM(d["a"][0]), P.FromMM(d["a"][1])))
        tr.SetEnd(P.VECTOR2I(P.FromMM(d["b"][0]), P.FromMM(d["b"][1])))
        tr.SetWidth(d["width"]); tr.SetLayer(d["layer"]); tr.SetNetCode(d["code"])
        b.Add(tr)
    for t in to_rm:
        b.Remove(t)
    members = inside_split(board, rect, refs)["members"]
    for fp in b.GetFootprints():
        if fp.GetReference() in members:
            fp.Move(P.VECTOR2I(dx, dy))
    P.SaveBoard(out, b)
    copied = []
    for ext in (".kicad_pro", ".kicad_dru"):
        src = board[:-len(".kicad_pcb")] + ext if board.endswith(".kicad_pcb") else board + ext
        if os.path.isfile(src):
            shutil.copy2(src, out[:-len(".kicad_pcb")] + ext if out.endswith(".kicad_pcb") else out + ext)
            copied.append(ext)
    return {"artifact": "eda_eng_block_move", "board": board, "out": out,
            "rect": [round(v, 4) for v in rect], "delta_mm": list(delta),
            "members": members, "n_members": len(members),
            "moved": mv, "jobs": jobs, "n_jobs": len(jobs),
            "project_config_copied": copied,
            "out_sha16": hashlib.sha256(open(out, "rb").read()).hexdigest()[:16],
            "rule": "#K2-369: step 1 = move pads AND rigidly translate the in-block copper; crossing lines are "
                    "split at dR (outside half stays put = fixed port, inside half travels with the block)"}


# ─────────────────────────────── 保真度（C6/C7） ───────────────────────────────
def zone_fill_segments(board, rect=None, nd=3, only_outside=False):
    """**#K2-442 sec.2.7**：zone 填充多边形的**边**（canonical）—— 让「块外铜零改动」看得见 zone。
    `only_outside` 时只计矩形**之外**的边（与 `outside_geometry` 同口径）。"""
    import pcbnew as P
    out = collections.Counter()
    _b = board
    if isinstance(_b, str):                                            # accepts a path (same call style as read_copper)
        import pcbnew as _P
        _b = _P.LoadBoard(_b)
    if True:
        for z in _b.Zones():
          try:
            net = z.GetNetname()
            for lid in z.GetLayerSet().CuStack():
                layer = _b.GetLayerName(lid)
                if not layer.endswith(".Cu"):
                    continue
                lid = _b.GetLayerID(layer)             # #K2-442: GetFilledPolysList needs an id from GetLayerID,
                poly = z.GetFilledPolysList(lid)       # NOT the enum out of GetLayerSet().Seq() (that one segfaults)
                for i in range(poly.OutlineCount()):
                    ch = poly.Outline(i)
                    n = ch.PointCount()
                    for j in range(n):
                        p = ch.CPoint(j); q = ch.CPoint((j + 1) % n)
                        a = (P.ToMM(p.x), P.ToMM(p.y)); b = (P.ToMM(q.x), P.ToMM(q.y))
                        if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 <= 1e-16:
                            continue
                        if only_outside:
                            _, outs = clip_iu(a, b, rect)
                            for (pp, qq) in outs:
                                if (pp[0] - qq[0]) ** 2 + (pp[1] - qq[1]) ** 2 <= 1e-16:
                                    continue
                                out[(net, layer) + tuple(round(v, nd) for v in _canon(pp, qq))] += 1
                        else:
                            out[(net, layer) + tuple(round(v, nd) for v in _canon(a, b))] += 1
          except Exception:                                            # noqa: BLE001
            continue                                                   # per-zone: one bad zone must not void the rest
    return out


def outside_geometry(board, rect, nd=3, include_zones=False):
    """铜（段+孔[+zone]）在 rect **之外**的几何多重集（canonical）——C6「块外铜零改动」的读数。
    **#K2-442 sec.2.7**：`include_zones=True` 时把 zone 填充的界外边一并计入（补「只看段/孔」的假绿盲区）。"""
    c = read_copper(board)
    out = collections.Counter()
    for s in c["segments"]:
        _, outs = clip_iu(s["a"], s["b"], rect)
        for (p, q) in outs:
            if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 <= 1e-16:
                continue
            k = (s["net"], s["layer"]) + tuple(round(v, nd) for v in _canon(p, q)) + (s["width"],)
            out[k] += 1
    if include_zones:
        out.update(zone_fill_segments(board, rect, nd, only_outside=True))
    for v in c["vias"]:
        if not pt_in(v["at"], rect):
            out[(v["net"], "VIA", round(v["at"][0], nd), round(v["at"][1], nd), v["drill"])] += 1
    return out


def net_geometry(board, nets, nd=3):
    """指定网的**全板**铜几何多重集（canonical）——C7「HS 扇出零触碰」的读数。"""
    c = read_copper(board)
    want = set(nets)
    out = collections.Counter()
    for s in c["segments"]:
        if s["net"] in want:
            out[(s["net"], s["layer"]) + tuple(round(v, nd) for v in _canon(s["a"], s["b"])) + (s["width"],)] += 1
    for v in c["vias"]:
        if v["net"] in want:
            out[(v["net"], "VIA", round(v["at"][0], nd), round(v["at"][1], nd), v["drill"])] += 1
    return out


def true_clearance_mm(board, layer, exclude_net, points):
    """**真形**净距（#K2-370 §三.3 对接 ＋ 缺口 C32 的第一步）：
    用 `eda_core.board_model.geometry.dist_point_segment`（共享层）量「点到**异网真实线段**」的最短距离。
    范围：该层上的 track 段（**真形**）；via 按点、pad 未纳入（仍是 AABB 近似）——如实报告 scope。"""
    P = _P()
    b = P.LoadBoard(board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    segs = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        n = nets.get(t.GetNetCode(), "")
        if n == exclude_net or t.GetLayerName() != layer:
            continue
        s, e = t.GetStart(), t.GetEnd()
        segs.append((n, P.ToMM(s.x), P.ToMM(s.y), P.ToMM(e.x), P.ToMM(e.y)))
    out = []
    for p in points:
        best, who = None, None
        for (n, x1, y1, x2, y2) in segs:
            d = _dps(p[0], p[1], x1, y1, x2, y2)
            if best is None or d < best:
                best, who = d, n
        out.append({"point": [round(p[0], 4), round(p[1], 4)], "min_mm": None if best is None else round(best, 4),
                    "nearest_net": who})
    return {"scope": "foreign track segments on the layer (true shapes); pads/vias still AABB/point",
            "clearance_mm": out}


def true_clearance_for_jobs(board, jobs):
    """批量真形净距（一次读板）：对每个作业，量其端点对**异网真实线段**的最短距离。
    用途：把 M3 的 `BLOCKED` 逐条分类为「真紧」还是「AABB 假阳」（缺口 C32 的机证）。"""
    P = _P()
    b = P.LoadBoard(board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    by_layer = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        s, e = t.GetStart(), t.GetEnd()
        by_layer[t.GetLayerName()].append((nets.get(t.GetNetCode(), ""), P.ToMM(s.x), P.ToMM(s.y),
                                           P.ToMM(e.x), P.ToMM(e.y)))
    out = []
    for j in jobs:
        L, ex = j["layer"], j["net"]
        pts = [j["port"], j["target"]] if j.get("kind") == "cross" else j.get("ports", [])
        best, who = None, None
        for (n, x1, y1, x2, y2) in by_layer.get(L, []):
            if n == ex:
                continue
            for p in pts:
                d = _dps(p[0], p[1], x1, y1, x2, y2)
                if best is None or d < best:
                    best, who = d, n
        out.append({"net": ex, "layer": L, "min_mm": None if best is None else round(best, 4),
                    "nearest_net": who})
    return out


# ─────────────────────── 方案层：刚体平移的**净距冲突**判定（#K2-371 §三 · §16 方案层回归件） ───────────────────────
# 问题层级：**框/位移怎么定**（方案层），不是"怎么布线"（施工层）。
# 判定：把**块内铜（含成员焊盘）**按 Δ 平移后，与**块外固定铜**（异网）逐对量**真形**净距；
#       任何一对 < clearance ⇒ 该 Δ 在冻结框下**净距冲突**（该冲突布线器无法修 —— 它是"方案"错了）。


IU = 1000000.0


def clip_iu(a, b, rect, tol_iu=1):
    """**IU（纳米）整数域**切分：与写板/读板同一量化 ⇒ 「块外半段」在前后两板上**逐点一致**（C6 的取整来源）。
    rect 允许 tol_iu 的边界容差（端点恰在 ∂R 上时不重复切）。返回 (inside, outside) 两组 (p,q)（mm 浮点）。"""
    def to_iu(v):
        return [int(round(v[0] * IU)), int(round(v[1] * IU))]
    A, B = to_iu(a), to_iu(b)
    r = [int(round(rect[0] * IU)) - tol_iu, int(round(rect[1] * IU)) - tol_iu,
         int(round(rect[2] * IU)) + tol_iu, int(round(rect[3] * IU)) + tol_iu]
    dx, dy = B[0] - A[0], B[1] - A[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, A[0] - r[0]), (dx, r[2] - A[0]), (-dy, A[1] - r[1]), (dy, r[3] - A[1])):
        if pp == 0:
            if qq < 0:
                return [], [(a, b)]
        else:
            t = qq / pp
            if pp < 0:
                if t > t1:
                    return [], [(a, b)]
                if t > t0:
                    t0 = t
            else:
                if t < t0:
                    return [], [(a, b)]
                if t < t1:
                    t1 = t
    def at(t):
        return [int(round(A[0] + t * dx)) / IU, int(round(A[1] + t * dy)) / IU]
    pin, pout = at(t0), at(t1)
    ins = [(pin, pout)] if (t1 - t0) * math.hypot(dx, dy) > 1.0 else []
    outs = []
    if t0 > 1e-9:
        outs.append((a, pin))
    if t1 < 1 - 1e-9:
        outs.append((pout, b))
    return ins, outs


def _pt_seg_d2(a, b, p):
    """点到线段距离平方（本模块自足，不依赖 route）。"""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    cx, cy = ax + t * dx, ay + t * dy
    return (p[0] - cx) ** 2 + (p[1] - cy) ** 2


def _seg_seg_d(a1, a2, b1, b2):
    """两线段最短距离（精确）。"""
    def d_pt_seg(p, a, b):
        return math.sqrt(_pt_seg_d2(a, b, p))
    # 相交 => 0
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1, d2 = cross(b1, b2, a1), cross(b1, b2, a2)
    d3, d4 = cross(a1, a2, b1), cross(a1, a2, b2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(d_pt_seg(a1, b1, b2), d_pt_seg(a2, b1, b2), d_pt_seg(b1, a1, a2), d_pt_seg(b2, a1, a2))


def _pt_rect_d(p, r):
    """点到**有向矩形**（cx,cy,sx,sy,rot）的距离（精确）。"""
    th = math.radians(r.get("rot", 0.0))
    dx, dy = p[0] - r["cx"], p[1] - r["cy"]
    c, sn = math.cos(-th), math.sin(-th)
    lx, ly = dx * c - dy * sn, dx * sn + dy * c
    ex = max(abs(lx) - r["sx"] / 2.0, 0.0)
    ey = max(abs(ly) - r["sy"] / 2.0, 0.0)
    return math.hypot(ex, ey)


def _rect_corners(r):
    th = math.radians(r.get("rot", 0.0))
    c, sn = math.cos(th), math.sin(th)
    hx, hy = r["sx"] / 2.0, r["sy"] / 2.0
    return [(r["cx"] + c * ux - sn * uy, r["cy"] + sn * ux + c * uy)
            for (ux, uy) in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


def _seg_rect_d(a, b, r):
    if _pt_rect_d(a, r) <= 1e-9 or _pt_rect_d(b, r) <= 1e-9:
        return 0.0
    cs = _rect_corners(r)
    return min(_seg_seg_d(a, b, cs[i], cs[(i + 1) % 4]) for i in range(4))


def _rect_rect_d(r1, r2):
    c1, c2 = _rect_corners(r1), _rect_corners(r2)
    if any(_pt_rect_d(p, r2) <= 1e-9 for p in c1) or any(_pt_rect_d(p, r1) <= 1e-9 for p in c2):
        return 0.0
    return min(_seg_seg_d(c1[i], c1[(i + 1) % 4], c2[j], c2[(j + 1) % 4]) for i in range(4) for j in range(4))


def prim_dist(p1, p2):
    """任意两个**真形**基元的最短距离（seg: a/b/half_w · rect: rect · circle: center/radius）。"""
    t1 = "seg" if "a" in p1 else ("rect" if "rect" in p1 else "circle")
    t2 = "seg" if "a" in p2 else ("rect" if "rect" in p2 else "circle")

    def base(t1, q1, t2, q2):
        if t1 == "seg" and t2 == "seg":
            return _seg_seg_d(q1["a"], q1["b"], q2["a"], q2["b"])
        if t1 == "seg" and t2 == "rect":
            return _seg_rect_d(q1["a"], q1["b"], q2["rect"])
        if t1 == "rect" and t2 == "seg":
            return _seg_rect_d(q2["a"], q2["b"], q1["rect"])
        if t1 == "rect" and t2 == "rect":
            return _rect_rect_d(q1["rect"], q2["rect"])
        if t1 == "circle" and t2 == "circle":
            return math.hypot(q1["center"][0] - q2["center"][0], q1["center"][1] - q2["center"][1])
        if t1 == "circle" and t2 == "seg":
            return math.sqrt(_pt_seg_d2(q2["a"], q2["b"], q1["center"]))
        if t1 == "seg" and t2 == "circle":
            return math.sqrt(_pt_seg_d2(q1["a"], q1["b"], q2["center"]))
        if t1 == "circle" and t2 == "rect":
            return _pt_rect_d(q1["center"], q2["rect"])
        if t1 == "rect" and t2 == "circle":
            return _pt_rect_d(q2["center"], q1["rect"])
        raise ValueError("unknown primitive pair %s/%s" % (t1, t2))

    d = base(t1, p1, t2, p2)
    r = p1.get("half_w", 0.0) + p2.get("half_w", 0.0)
    if t1 == "circle":
        r += p1.get("radius", 0.0)
    if t2 == "circle":
        r += p2.get("radius", 0.0)
    return max(0.0, d - r)


def _translate(p, delta):
    q = dict(p)
    if "a" in p:
        q["a"] = [p["a"][0] + delta[0], p["a"][1] + delta[1]]
        q["b"] = [p["b"][0] + delta[0], p["b"][1] + delta[1]]
        q["bbox"] = [p["bbox"][0] + delta[0], p["bbox"][1] + delta[1],
                     p["bbox"][2] + delta[0], p["bbox"][3] + delta[1]]
    elif "rect" in p:
        q["rect"] = dict(p["rect"]); q["rect"]["cx"] += delta[0]; q["rect"]["cy"] += delta[1]
        q["bbox"] = [p["bbox"][0] + delta[0], p["bbox"][1] + delta[1],
                     p["bbox"][2] + delta[0], p["bbox"][3] + delta[1]]
    else:
        q["center"] = [p["center"][0] + delta[0], p["center"][1] + delta[1]]
        q["bbox"] = [p["bbox"][0] + delta[0], p["bbox"][1] + delta[1],
                     p["bbox"][2] + delta[0], p["bbox"][3] + delta[1]]
    return q


def _pad_prim(p, P):
    bb = p.GetBoundingBox()
    own = {"kind": "copper", "net": p.GetNetname(),
           "bbox": [round(P.ToMM(bb.GetX()), 4), round(P.ToMM(bb.GetY()), 4),
                    round(P.ToMM(bb.GetRight()), 4), round(P.ToMM(bb.GetBottom()), 4)]}
    try:
        sz, pc = p.GetSize(), p.GetPosition()
        own["rect"] = {"cx": round(P.ToMM(pc.x), 4), "cy": round(P.ToMM(pc.y), 4),
                       "sx": round(P.ToMM(sz.x), 4), "sy": round(P.ToMM(sz.y), 4),
                       "rot": round(p.GetOrientationDegrees(), 3)}
    except Exception:                                          # noqa: BLE001
        pass
    return own


def classify_primitives(board, rect, members):
    """按 BLOCK 分类产出 (moved@Δ=0, fixed) 两组**真形**基元（含成员焊盘）。"""
    P = _P()
    b = P.LoadBoard(board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    mem = set(members or [])
    moved, fixed = [], []
    for fp in b.GetFootprints():
        tgt = moved if fp.GetReference() in mem else fixed
        for p in fp.Pads():
            tgt.append(_pad_prim(p, P))
    for t in b.GetTracks():
        net = nets.get(t.GetNetCode(), "")
        if t.GetClass() == "PCB_VIA":
            vp = t.GetPosition(); bb = t.GetBoundingBox()
            pr = {"kind": "copper", "net": net,
                  "center": [round(P.ToMM(vp.x), 4), round(P.ToMM(vp.y), 4)],
                  "radius": round(P.ToMM(t.GetWidth()) / 2.0, 4),
                  "bbox": [round(P.ToMM(bb.GetX()), 4), round(P.ToMM(bb.GetY()), 4),
                           round(P.ToMM(bb.GetRight()), 4), round(P.ToMM(bb.GetBottom()), 4)]}
            (moved if pt_in(pr["center"], rect) else fixed).append(pr)
            continue
        st, en = t.GetStart(), t.GetEnd()
        a = [round(P.ToMM(st.x), 4), round(P.ToMM(st.y), 4)]
        z = [round(P.ToMM(en.x), 4), round(P.ToMM(en.y), 4)]
        hw = round(P.ToMM(t.GetWidth()) / 2.0, 4)
        def mk(p, q):
            return {"kind": "copper", "net": net, "a": p, "b": q, "half_w": hw,
                    "bbox": [min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1])]}
        ins, outs = _seg_inside_parts(a, z, rect)
        if ins and not outs:
            moved.append(mk(ins[0][0], ins[0][1]))
            continue
        for (p, q) in outs:
            if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 1e-16:
                fixed.append(mk(p, q))
        if not ins:
            continue
        if pt_in(a, rect) or pt_in(z, rect):
            moved.append(mk(ins[0][0], ins[0][1]))
        # 桥的块内中段会被删除（非移动）⇒ 不计入任一侧
    return moved, fixed


def clearance_conflicts(board, rect, members, delta, clearance=CLEAR, cap=12, cell=1.0):
    """按 Δ 平移**块内铜**，与**异网固定铜**逐对真形量距；返回具名冲突清单（方案层读数）。"""
    moved, fixed = classify_primitives(board, rect, members)
    buckets = collections.defaultdict(list)
    for f in fixed:
        bb = f["bbox"]
        for i in range(int(bb[0] // cell), int(bb[2] // cell) + 1):
            for j in range(int(bb[1] // cell), int(bb[3] // cell) + 1):
                buckets[(i, j)].append(f)
    conf, best = [], None
    for m0 in moved:
        m = _translate(m0, delta)
        bb = m["bbox"]
        cand = []
        for i in range(int((bb[0] - clearance) // cell), int((bb[2] + clearance) // cell) + 1):
            for j in range(int((bb[1] - clearance) // cell), int((bb[3] + clearance) // cell) + 1):
                cand += buckets.get((i, j), [])
        for f in cand:
            if f["net"] == m["net"]:
                continue
            d = prim_dist(m, f)
            if best is None or d < best[0]:
                best = (d, m["net"], f["net"])
            if d < clearance - 1e-9:
                if len(conf) < cap:
                    conf.append({"moved_net": m["net"], "fixed_net": f["net"], "dist_mm": round(d, 4),
                                 "at": [round(bb[0], 3), round(bb[1], 3)]})
                if len(conf) >= cap:
                    break
        if len(conf) >= cap:
            break
    return {"delta_mm": [round(delta[0], 3), round(delta[1], 3)], "n_moved": len(moved), "n_fixed": len(fixed),
            "conflicts": conf, "n_conflicts_shown": len(conf), "min_pair_mm": None if best is None else round(best[0], 4),
            "min_pair": None if best is None else {"moved_net": best[1], "fixed_net": best[2]},
            "clearance_mm": clearance}


def geometric_digest(board, nd=3):
    """**规范几何摘要**（#K2-371 §五）：对几何（非字节）做 canonical 量化后取 SHA256 ⇒ 同几何必同摘要。"""
    c = read_copper(board)
    segs = sorted((s["net"], s["layer"], round(s["width"], nd)) + tuple(round(v, nd) for v in _canon(s["a"], s["b"]))
                  for s in c["segments"])
    vias = sorted((v["net"], "VIA", round(v["drill"], nd), round(v["at"][0], nd), round(v["at"][1], nd))
                  for v in c["vias"])
    h = hashlib.sha256(json.dumps({"segments": segs, "vias": vias, "nd": nd},
                                  ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {"sha256_16": h[:16], "n_segments": len(segs), "n_vias": len(vias), "nd": nd,
            "rule": "canonical geometric digest over (net, layer, quantized geometry, width); byte-level SHA is NOT a criterion"}


def move_parts(board, rect, moves, out, keep_nets=None):
    """**A′（#K2-372 §二.1）逐件位移 ＋ 块内铜重铺**：
      · 成员 footprint 按**各自** Δ 移动（pad 随动）；
      · 块内铜（两端在 rect 内）与**穿边线的块内半段** ⇒ **删除**（相对重排后不可整块平移 ⇒ 必须重连）；
      · 穿边线的**块外半段** ⇒ 原地**逐点原样**保留（固定端口），记 `port`。
    返回 {ports: {net:[pt]}, pads_in: {net:[[x,y]]}, deleted_*, moved}。子进程专用。"""
    P = _P()
    b = P.LoadBoard(board)
    nets_map = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    mmap = {r: (float(dx), float(dy)) for (r, dx, dy) in moves}
    ports = collections.defaultdict(list)
    port_layer = collections.defaultdict(list)
    KEEP = frozenset(keep_nets or ())                 # #K2-418: these nets keep their accepted routing (not wiped)
    to_rm, to_add = [], []
    del_seg = del_via = 0
    for t in list(b.GetTracks()):
        net = nets_map.get(t.GetNetCode(), "")
        if net in KEEP:
            continue                                  # #K2-418 sec.3: U1's nets 原线保留不 wipe
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            xx, yy = P.ToMM(pos.x), P.ToMM(pos.y)
            if pt_in((xx, yy), rect):
                to_rm.append(t); del_via += 1
            continue
        st, en = t.GetStart(), t.GetEnd()
        a = [P.ToMM(st.x), P.ToMM(st.y)]
        z = [P.ToMM(en.x), P.ToMM(en.y)]
        hw = round(P.ToMM(t.GetWidth()) / 2.0, 4)
        lay, wid, code = t.GetLayer(), t.GetWidth(), t.GetNetCode()
        ins, outs = clip_iu(a, z, rect)                          # IU 整数域切分（C6 取整来源的对齐）
        if not ins:
            continue                                            # 块外：零触碰
        to_rm.append(t)
        del_seg += len(ins)
        for (p, q) in outs:
            if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 1e-16:
                to_add.append({"code": code, "layer": lay, "width": wid, "a": p, "b": q})
                ports[net].append([round(p[0], 4), round(p[1], 4)])
                ports[net].append([round(q[0], 4), round(q[1], 4)])
                port_layer[net].append(b.GetLayerName(lay))
    for d in to_add:
        tr = P.PCB_TRACK(b)
        tr.SetStart(P.VECTOR2I(P.FromMM(d["a"][0]), P.FromMM(d["a"][1])))
        tr.SetEnd(P.VECTOR2I(P.FromMM(d["b"][0]), P.FromMM(d["b"][1])))
        tr.SetWidth(d["width"]); tr.SetLayer(d["layer"]); tr.SetNetCode(d["code"])
        b.Add(tr)
    for t in to_rm:
        b.Remove(t)
    moved = []
    for fp in b.GetFootprints():
        d = mmap.get(fp.GetReference())
        if not d:
            continue
        fp.Move(P.VECTOR2I(P.FromMM(d[0]), P.FromMM(d[1])))
        moved.append({"ref": fp.GetReference(), "delta_mm": [d[0], d[1]]})
    pads_in = collections.defaultdict(list)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            pos = p.GetPosition()
            pt = (P.ToMM(pos.x), P.ToMM(pos.y))
            if n and pt_in(pt, rect):
                pads_in[n].append([round(pt[0], 4), round(pt[1], 4)])
    P.SaveBoard(out, b)
    copied = []
    for ext in (".kicad_pro", ".kicad_dru"):
        src = board[:-len(".kicad_pcb")] + ext if board.endswith(".kicad_pcb") else board + ext
        if os.path.isfile(src):
            shutil.copy2(src, out[:-len(".kicad_pcb")] + ext if out.endswith(".kicad_pcb") else out + ext)
            copied.append(ext)
    # 端口去重（同一穿边线的两端只留落在 ∂R 上的那个）
    def on_boundary(p):
        """**在 ∂R 的实际线段上**（不是它所在的无限直线）——否则角外的远端会被误当端口（A′ attempt1 的真缺陷）。"""
        eps = 1e-6
        on_x = (abs(p[0] - rect[0]) < eps or abs(p[0] - rect[2]) < eps) and (rect[1] - eps <= p[1] <= rect[3] + eps)
        on_y = (abs(p[1] - rect[1]) < eps or abs(p[1] - rect[3]) < eps) and (rect[0] - eps <= p[0] <= rect[2] + eps)
        return bool(on_x or on_y)
    ports = {n: sorted({tuple(p) for p in pts if on_boundary(p)}) for n, pts in ports.items()}
    ports = {n: [list(p) for p in v] for n, v in ports.items() if v}
    return {"artifact": "eda_eng_move_parts", "board": board, "out": out, "rect": list(rect),
            "moved": moved, "n_moved": len(moved),
            "deleted_segments": del_seg, "deleted_vias": del_via, "outside_halves_kept": len(to_add),
            "ports": ports, "pads_in": {n: v for n, v in pads_in.items()}, "port_layers": {k: sorted(set(v)) for k, v in port_layer.items()},
            "project_config_copied": copied,
            "out_sha16": hashlib.sha256(open(out, "rb").read()).hexdigest()[:16],
            "rule": "#K2-372 sec.2.1: A-prime = per-part offsets; the in-block copper CANNOT be rigidly translated "
                    "(relative positions changed) so it is RE-LAID; the outside halves of crossing lines stay put as "
                    "fixed ports on dR"}


def moves_from_board(base_board, placed_board, refs, tol=0.001):
    """**口径对齐**（#K2-375 §四.3 secondary）：把**闸所验的那块板**（gen 生成板）的摆放**逐件读回来**，
    作为 A′ 的逐件位移图 —— 这样「链上用的放置」与「闸验过的放置」**是同一个**（同板同读数）。
    返回 (moves, unchanged, missing)；moves=[(ref,dx,dy), ...]（|Δ|>tol 者）。"""
    P = _P()
    def pos(bd):
        b = P.LoadBoard(bd)
        return {fp.GetReference(): [P.ToMM(fp.GetPosition().x), P.ToMM(fp.GetPosition().y)]
                for fp in b.GetFootprints()}
    a, c = pos(base_board), pos(placed_board)
    moves, unch, miss = [], [], []
    for r in refs:
        if r not in a or r not in c:
            miss.append(r); continue
        dx = round(c[r][0] - a[r][0], 4); dy = round(c[r][1] - a[r][1], 4)
        (moves if (abs(dx) > tol or abs(dy) > tol) else unch).append(
            (r, dx, dy) if (abs(dx) > tol or abs(dy) > tol) else r)
    return moves, unch, miss


def bound_outside(base_board, final_board, rect, out):
    """**C35 薄封装**（#K2-377 §二.3）：框外铜**恢复为原板逐点几何**。
    **两趟分离**（改板会破坏同进程 SWIG 态，承 R964）：先只读原板把"沾框外"的基元取成**纯数据**，
    再加载并改写产物板。框内作业不动 ⇒ C6 按构造为 0。"""
    P = _P()
    def read_outside(bd):
        b = P.LoadBoard(bd)
        nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
        segs, vias = [], []
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA":
                pos = t.GetPosition()
                if pt_in((P.ToMM(pos.x), P.ToMM(pos.y)), rect):
                    continue
                lset = list(t.GetLayerSet().Seq())
                l1, l2 = lset[0], lset[-1]
                vias.append({"x": pos.x, "y": pos.y, "drill": t.GetDrill(),
                             "l1": l1, "l2": l2, "net": nets.get(t.GetNetCode(), ""),
                             "w": t.GetWidth(l1)})
                continue
            st, en = t.GetStart(), t.GetEnd()
            a = [P.ToMM(st.x), P.ToMM(st.y)]; z = [P.ToMM(en.x), P.ToMM(en.y)]
            if not _seg_inside_parts(a, z, rect)[1]:
                continue                                    # 全在框内：不动
            segs.append({"x1": st.x, "y1": st.y, "x2": en.x, "y2": en.y, "layer": t.GetLayer(),
                         "w": t.GetWidth(), "net": nets.get(t.GetNetCode(), "")})
        return segs, vias

    keep_segs, keep_vias = read_outside(base_board)          # ① 只读（纯数据）
    fb = P.LoadBoard(final_board)                            # ② 再改写产物板
    netmap = {n.GetNetname(): n.GetNetCode() for n in fb.GetNetsByName().values()}
    removed = added = 0
    for t in list(fb.GetTracks()):
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            if not pt_in((P.ToMM(pos.x), P.ToMM(pos.y)), rect):
                fb.Remove(t); removed += 1
            continue
        st, en = t.GetStart(), t.GetEnd()
        if _seg_inside_parts([P.ToMM(st.x), P.ToMM(st.y)], [P.ToMM(en.x), P.ToMM(en.y)], rect)[1]:
            fb.Remove(t); removed += 1
    for d in keep_segs:
        tr = P.PCB_TRACK(fb)
        tr.SetStart(P.VECTOR2I(d["x1"], d["y1"])); tr.SetEnd(P.VECTOR2I(d["x2"], d["y2"]))
        tr.SetWidth(d["w"]); tr.SetLayer(d["layer"]); tr.SetNetCode(netmap.get(d["net"], -1))
        fb.Add(tr); added += 1
    for d in keep_vias:
        vi = P.PCB_VIA(fb)
        vi.SetPosition(P.VECTOR2I(d["x"], d["y"])); vi.SetWidth(d["w"]); vi.SetDrill(d["drill"])
        vi.SetLayerPair(d["l1"], d["l2"]); vi.SetNetCode(netmap.get(d["net"], -1))
        fb.Add(vi); added += 1
    P.SaveBoard(out, fb)
    import shutil
    for ext in (".kicad_pro", ".kicad_dru"):
        src = final_board[:-len(".kicad_pcb")] + ext if final_board.endswith(".kicad_pcb") else final_board + ext
        if os.path.isfile(src):
            shutil.copy2(src, out[:-len(".kicad_pcb")] + ext if out.endswith(".kicad_pcb") else out + ext)
    return {"artifact": "eda_eng_bound_outside", "base": base_board, "final": final_board, "out": out,
            "removed_outside_tracks": removed, "restored_outside_tracks": added, "rect": list(rect),
            "out_sha16": hashlib.sha256(open(out, "rb").read()).hexdigest()[:16],
            "rule": "#K2-377 sec.2.3 (C35): a thin wrapper that clamps the work domain - the copied method keeps "
                    "its in-frame work; the outside copper is restored to the base geometry point for point"}


def geometry_equal(a, b):
    """两个 canonical Counter 的多重集差（正/负/总）。"""
    plus = sum((a - b).values()); minus = sum((b - a).values())
    return {"only_in_a": plus, "only_in_b": minus, "diff": plus + minus, "equal": (plus + minus) == 0}


def attribute_delta(cur, ref, zone_keys=()):
    """#K2-503 ENGINE CAPABILITY（纯函数 · 确定性 · 有界）：把 canonical Counter 之差**逐件归因**。

    C6 的读数是一个数（例：819），但一个数**不可行动**：**灌铜重填的边**与**真铜被增删**是两种完全不同的
    发现，混在一个数字里会同时误导判读与修法（R1676：819 里 817 是灌铜边、仅 2 是真铜）。本函数把它拆开：
    `added_by_kind / removed_by_kind`（ZONE / SEG / VIA）、`added_by_net_layer`、`zone_edges`、以及
    **`real_items`（非灌铜之逐件清单）**。`zone_keys` ＝ 属灌铜填充边之键集（由 `zone_fill_segments` 给出）。
    零搜索 · 无循环以外的循环 · 确定性排序。
    """
    add, rem, by_nl = collections.Counter(), collections.Counter(), collections.Counter()
    real = []
    for k, n in (cur - ref).items():
        if n <= 0:
            continue
        kind = "ZONE" if k in zone_keys else ("VIA" if k[1] == "VIA" else "SEG")
        add[kind] += n
        by_nl[(k[0], k[1])] += n
        if kind != "ZONE":
            real.append({"dir": "added", "key": list(k), "n": n})
    for k, n in (ref - cur).items():
        if n <= 0:
            continue
        kind = "ZONE" if k in zone_keys else ("VIA" if k[1] == "VIA" else "SEG")
        rem[kind] += n
        if kind != "ZONE":
            real.append({"dir": "removed", "key": list(k), "n": n})
    real.sort(key=lambda r: (r["dir"], str(r["key"])))
    return {"added_by_kind": dict(sorted(add.items())), "removed_by_kind": dict(sorted(rem.items())),
            "added_by_net_layer": {"%s|%s" % k: v for k, v in sorted(by_nl.items(), key=lambda t: (-t[1], str(t[0])))},
            "total": sum(add.values()) + sum(rem.values()),
            "zone_edges": add.get("ZONE", 0) + rem.get("ZONE", 0),
            "real_items": real, "n_real": len(real),
            "rule": "#K2-503: an outside-copper delta must be NAMEABLE - a zone-fill re-polygonisation and a real "
                    "copper change are different findings and must never be reported as one number."}


def _poly_area_mm2(pts):
    """鞋带公式之**绝对**面积（mm²）。确定性 · 有界。"""
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def _clip_poly_rect(pts, rect):
    """Sutherland–Hodgman：简单多边形 × 凸矩形（4 半平面 · 固定次数 · 无 while）。返回多边形点列（可空）。"""
    x0, y0, x1, y1 = [float(v) for v in rect]
    planes = ((lambda p: p[0] >= x0, 0, x0), (lambda p: p[0] <= x1, 0, x1),
              (lambda p: p[1] >= y0, 1, y0), (lambda p: p[1] <= y1, 1, y1))
    for (inside, axis, lim) in planes:
        if not pts:
            return []
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            ia, ib = inside(a), inside(b)
            if ia:
                out.append(a)
            if ia != ib:
                da, db = a[axis], b[axis]
                t = 0.0 if abs(db - da) < 1e-15 else (lim - da) / (db - da)
                out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        pts = out
    return pts


def zone_outside_area(board, rect):
    """#K2-504 ENGINE CAPABILITY：zone 填充在 rect **之外**的**铜面积**（mm² · 按 `(net,layer)` 聚合）。

    **为什么是面积**：灌铜**重多边形化**会换掉顶点集而**覆盖域不变**；`zone_fill_segments` 的逐边比对
    会把这种**非变更**报成变更（R1676：819 里 817 是这种）。面积是覆盖域之**不变量**（重分解不变），
    因此是「框外铜不变」的正确读数。**只读 · 确定性 · 有界**（无搜索 · 无 while）。
    """
    import pcbnew as P
    _b = board
    if isinstance(_b, str):
        _b = P.LoadBoard(_b)
    acc = collections.defaultdict(float)
    for z in _b.Zones():
        try:
            net = z.GetNetname()
            for lid in z.GetLayerSet().CuStack():
                layer = _b.GetLayerName(lid)
                if not layer.endswith(".Cu"):
                    continue
                lid = _b.GetLayerID(layer)                # 与 zone_fill_segments 同注：必须用 GetLayerID
                poly = z.GetFilledPolysList(lid)
                for i in range(poly.OutlineCount()):
                    ch = poly.Outline(i)
                    n = ch.PointCount()
                    pts = [(P.ToMM(ch.CPoint(j).x), P.ToMM(ch.CPoint(j).y)) for j in range(n)]
                    tot = _poly_area_mm2(pts) - _poly_area_mm2(_clip_poly_rect(pts, rect))
                    try:
                        for h in range(poly.HoleCount(i)):
                            hc = poly.Hole(i, h)
                            hn = hc.PointCount()
                            hp = [(P.ToMM(hc.CPoint(j).x), P.ToMM(hc.CPoint(j).y)) for j in range(hn)]
                            tot -= _poly_area_mm2(hp) - _poly_area_mm2(_clip_poly_rect(hp, rect))
                    except Exception:                     # noqa: BLE001
                        pass
                    acc[(net, layer)] += tot
        except Exception:                                 # noqa: BLE001
            continue                                      # per-zone: one bad zone must not void the rest
    return {k: round(v, 6) for k, v in acc.items() if abs(v) > 1e-9}


def declared_outside_keys(spec_paths, rect, nd=3, default_via_drill=0.25):
    """#K2-505 ENGINE CAPABILITY：在册图纸之**授权框外铜**（声明感知量具之事实源）。

    带 `allow_outside_dR: true` 的线条 ＝ **已裁·已画·已过闸** 的框端跨接件（#K2-442 sec.2.7），**是授权铜，
    不是泄漏**（#K2-505 §一）。本函数把每条声明件的**框外几何**转成与 `outside_geometry` **同形**之键，
    于是 diff 里的每一项都能被**指认其授权出处**（文件名＋行号＋原由）。
    **fail-closed by construction**：只认**显式声明**且**文件在册**者；无匹配之一律照报。
    """
    out = {}
    for p in (spec_paths or []):
        if not p or not os.path.isfile(p):
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:                                          # noqa: BLE001
            continue
        lines = d.get("lines") or (d.get("spec") or {}).get("lines") or []
        for i, L in enumerate(lines):
            if not L.get("allow_outside_dR"):
                continue
            src = {"source": os.path.basename(p), "line": L.get("n", i + 1), "kind": L.get("kind"),
                   "net": L.get("net"), "why": (L.get("why") or "")[:180]}
            if L.get("kind") == "via":
                at = [float(v) for v in L.get("at") or []]
                if len(at) == 2:
                    out[(L.get("net"), "VIA", round(at[0], nd), round(at[1], nd),
                         float(L.get("drill", default_via_drill)))] = src
                continue
            if L.get("kind") == "zone":
                r = [float(v) for v in (L.get("rect") or [])]
                if len(r) == 4:
                    out[("ZONE", L.get("net"), L.get("layer"), tuple(r))] = src
                continue
            a = [float(v) for v in (L.get("a") or [])]; b = [float(v) for v in (L.get("b") or [])]
            ly = L.get("layer") or (L.get("layers") or [None])[0]
            if len(a) != 2 or len(b) != 2 or ly is None:
                continue
            for (pp, qq) in clip_iu(a, b, rect)[1]:
                if (pp[0] - qq[0]) ** 2 + (pp[1] - qq[1]) ** 2 <= 1e-16:
                    continue
                out[(L.get("net"), ly) + tuple(round(v, nd) for v in _canon(pp, qq))
                    + (float(L.get("width", 0.25)),)] = src
    return out


def zone_area_tolerance(ref_area_mm2, clear_mm=0.30, exposure_mm=147.2, rel_cap=1e-3):
    """#K2-516 sec.2 item 1 ENGINE CAPABILITY: the C6 zone-row **calibrated tolerance** (DERIVED, never hand-picked).

    `geom` = `clear_mm` x `exposure_mm` - the AVOIDANCE RING: a fill boundary can recede at most `clear` along the
             boundary length exposed to newly laid copper.  `clear_mm` = 0.20 (the in-register DRC clearance) + 0.10
             (the in-register track half width).  `exposure_mm` defaults to the FRAME PERIMETER = 2*((51.5-22.95) +
             (78.0-32.95)) = 147.2 mm, i.e. the largest exposure any frame-edge zone can have - a true upper bound.
    `rel`  = `rel_cap` x reference area - the relative cap ordered by #K2-516 sec.2 item 1 (<= 0.1% of the reference).
    `tol`  = **min(geom, rel)**, exactly as ordered. Everything is reported so each number has a source; the relative
             arm is expected to bind on the small-area zones, which is the ruling's intent (tight on small planes).
    """
    geom = float(clear_mm) * float(exposure_mm)
    rel = float(rel_cap) * max(0.0, float(ref_area_mm2))
    return {"tol_mm2": round(min(geom, rel), 6), "geom_bound_mm2": round(geom, 6), "rel_cap_mm2": round(rel, 6),
            "binding": ("geom" if geom <= rel else "rel_cap"), "clear_mm": clear_mm, "exposure_mm": exposure_mm,
            "rel_cap": rel_cap,
            "sources": {"clear_mm": "#K2-516: DRC clearance 0.20 + track half-width 0.10 (both in-register)",
                        "exposure_mm": "frame perimeter 2*((51.5-22.95)+(78.0-32.95)) = 147.2 mm (derived upper bound)",
                        "rel_cap": "#K2-516 sec.2 item 1: relative cap <= 0.1% of the reference coverage"}}


def outside_area_moved(before, after, tol=1e-3):
    """#K2-507 sec.3 item 2 ENGINE CAPABILITY（**纯函数**）：两个 `(net,layer)->框外面积` 图之**差**（|Δ| > tol 者具名）。

    **为什么需要一个纯函数**：「处置/重填**不得改动框外覆盖**」这条纪律的判据必须**可单测**；而"重多边形化"与
    "真实覆盖伸入"之分在此**一望可辨**（前者面积为 0，后者面积非 0）。确定性 · 有界 · 无副作用。
    """
    out = {}
    b0 = before or {}
    a0 = after or {}
    for k in sorted(set(b0) | set(a0), key=lambda t: (str(t[0]), str(t[1]))):
        d = round(a0.get(k, 0.0) - b0.get(k, 0.0), 6)
        if abs(d) > tol:
            out["%s|%s" % k] = d
    return out


def outside_copper_equivalent(final, ref, rect, tol_area=1e-3, nd=3, declared=None):
    """#K2-504/#K2-505 ENGINE CAPABILITY：C6「框外铜不变」之**几何等价 × 声明感知**口径。

    `真实铜`（段＋孔）＝ 精确多重集（**不变**）；但其中命中**在册声明件**（`declared_outside_keys`）者＝
    **授权铜 ⇒ 不计为变更**，且**逐件具名其授权出处**；**未声明者一律照报**（fail-closed）。`灌铜` ＝
    框外**覆盖面积**按 `(net,layer)` 等价（重多边形化不计）。判据表语义与阈值**零触碰**：
    "框外铜不变" 仍严格 ＝ **无未授权真实铜变更** ∧ **灌铜覆盖不变**。
    """
    declared = declared or {}
    cur = outside_geometry(final, rect, nd=nd)
    r0 = outside_geometry(ref, rect, nd=nd)
    add = {k: v for k, v in (cur - r0).items() if v > 0}
    rem = {k: v for k, v in (r0 - cur).items() if v > 0}
    auth, unauth = [], []
    for k, v in sorted(add.items(), key=lambda t: (str(t[0][0]), str(t[0][1]), str(t[0][2:]))):
        (auth if k in declared else unauth).append({"key": list(k), "n": v, "authority": declared.get(k)})
    rm = [{"key": list(k), "n": v} for k, v in sorted(rem.items(), key=lambda t: (str(t[0][0]), str(t[0][1])))]
    af, ar = zone_outside_area(final, rect), zone_outside_area(ref, rect)
    rows = {}
    for k in sorted(set(af) | set(ar), key=lambda t: (str(t[0]), str(t[1]))):
        d = round(af.get(k, 0.0) - ar.get(k, 0.0), 6)
        if abs(d) <= tol_area:
            continue
        _tv = zone_area_tolerance(ar.get(k, 0.0))            # #K2-516 sec.2 item 1: derived, per-row
        _pass = abs(d) <= _tv["tol_mm2"]
        rows["%s|%s" % k] = {"final": af.get(k, 0.0), "ref": ar.get(k, 0.0), "delta": d,
                             "tol_mm2": _tv["tol_mm2"], "pass": _pass, "caliber": "calibrated zone tolerance",
                             "tol_derivation": _tv}
    _zone_bad = [k for k, v in rows.items() if not v.get("pass")]
    return {"equivalent": (not unauth) and (not rm) and (not _zone_bad),
            "real_diff": sum(u["n"] for u in unauth) + sum(u["n"] for u in rm),
            "real_only_in_final": sum(a["n"] for a in auth) + sum(u["n"] for u in unauth),
            "real_only_in_ref": sum(u["n"] for u in rm),
            "unauthorized": unauth, "authorized": auth, "removed": rm,
            "n_authorized": len(auth), "n_unauthorized": len(unauth), "n_removed": len(rm),
            "zone_area_delta": rows, "n_zone_delta": len(rows), "tol_area_mm2": tol_area,
            "rule": "#K2-504/#K2-505: 'outside copper unchanged' is GEOMETRIC and DECLARATION-AWARE - a zone fill "
                    "covering the same domain is unchanged, and copper that an in-register drawing explicitly "
                    "authorises (allow_outside_dR) is NAMED as authorised rather than reported as a leak. Anything "
                    "without a declaration match is reported exactly as before (fail-closed)."}


def outside_copper_delta(final, ref, rect, nd=3):
    """#K2-503 ENGINE CAPABILITY：C6「块外铜零改动」读数的**具名分解**（zone-aware 口径，判据不动）。

    引擎自己对**自己的**块外铜差做归因：`attribute_delta(outside_geometry(...,include_zones=True), ...)`，
    并给出 `legacy_total`（只算段＋孔之口径）以便同时看到两种口径。**只读 · 不开判据 · 不改判据表。**
    """
    cur = outside_geometry(final, rect, nd=nd, include_zones=True)
    r = outside_geometry(ref, rect, nd=nd, include_zones=True)
    zk = set(zone_fill_segments(final, rect, nd=nd, only_outside=True)) | \
         set(zone_fill_segments(ref, rect, nd=nd, only_outside=True))
    out = attribute_delta(cur, r, zk)
    out["legacy_total"] = geometry_equal(outside_geometry(final, rect, nd=nd),
                                         outside_geometry(ref, rect, nd=nd))["diff"]
    return out
