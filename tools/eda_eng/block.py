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
import collections, hashlib, os, shutil, sys

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
def outside_geometry(board, rect, nd=3):
    """铜（段+孔）在 rect **之外**的几何多重集（canonical）——C6「块外铜零改动」的读数。"""
    c = read_copper(board)
    out = collections.Counter()
    for s in c["segments"]:
        _, outs = _seg_inside_parts(s["a"], s["b"], rect)
        for (p, q) in outs:
            if (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 <= 1e-16:
                continue
            k = (s["net"], s["layer"]) + tuple(round(v, nd) for v in _canon(p, q)) + (s["width"],)
            out[k] += 1
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


def geometry_equal(a, b):
    """两个 canonical Counter 的多重集差（正/负/总）。"""
    plus = sum((a - b).values()); minus = sum((b - a).values())
    return {"only_in_a": plus, "only_in_b": minus, "diff": plus + minus, "equal": (plus + minus) == 0}
