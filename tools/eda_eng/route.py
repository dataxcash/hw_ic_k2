"""M3 · `eda_eng route` --- 重布（#K2-360 §一 M3）。

合同：拆后板 + 约束（禁区 / 铜皮多边形 C22 / 间距 / 45° / 层分配）→ 布通板。
测试顺序（§一）：**先玩具用例（单网 / 双网）→ 再区域用例**，**逐网连通即时校验**。

v1 范围（如实声明 · 逐级扩）：
  * 核心 = **纯数据模型** `route_pair(...)`：端点 + 障碍集 + 约束 → 见证路径 ‖ 具名 BLOCKED（便于玩具用例）。
  * 候选族 = **确定性闭式**：直段 / L(两型) / Z(两型 × 三档) ，每型再生成 **45° 倒角**变体；逐条过**间距+禁区 oracle**；
    取**首个通过者**（零搜索 · 零随机 · 可复现）。
  * **单层**布（层由调用方指定）；**via 插入 / 多层 = 下一步**（未实现项，不冒充）。
  * 区域用例经 `obstacles_from_board()` 从真板取障碍（保守用**轴对齐包围盒**，含 pad/track/via + 禁区多边形）。
"""
from __future__ import annotations
import json, math, os

CLEAR = 0.175          # 板规则实测间距下限（mm）
BOARD_MARGIN = 0.25


# ---------------------------------------------------------------- geometry
def _seg_pt_d2(a, b, p):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    cx, cy = ax + t * dx, ay + t * dy
    return (px - cx) ** 2 + (py - cy) ** 2


def _poly_samples(poly, step=0.05):
    out = []
    for i in range(len(poly) - 1):
        a, b = poly[i], poly[i + 1]
        L = math.dist(a, b)
        n = max(2, int(L / step) + 1)
        for k in range(n + 1):
            out.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return out


def _box_pt_d2(bx, p):
    x0, y0, x1, y1 = bx
    dx = max(x0 - p[0], 0.0, p[0] - x1)
    dy = max(y0 - p[1], 0.0, p[1] - y1)
    return dx * dx + dy * dy


def poly_violations(poly, obstacles, clearance=CLEAR, step=0.05, layer=None):
    """返回 [(obstacle_id, min_dist_mm, kind)]，只含违规项（keepout 用 clearance=0 且 min_dist==0 记违规）。"""
    bad = []
    pts = _poly_samples(poly, step)
    for ob in obstacles:
        if layer and ob.get("layers") and layer not in ob["layers"]:
            continue
        min_d2 = min(_box_pt_d2(ob["bbox"], p) for p in pts)
        d = math.sqrt(min_d2)
        need = 0.0 if ob.get("kind") == "keepout" else clearance
        if d <= need + 1e-9:
            bad.append({"obstacle": ob.get("id"), "kind": ob.get("kind"), "net": ob.get("net"),
                        "min_dist_mm": round(d, 4), "required_mm": need})
    return bad


def _chamfer(poly, leg):
    """把折线里的 90° 拐角切成两段 45°（leg = 切角腿长）。"""
    if len(poly) < 3:
        return [list(p) for p in poly]
    out = [list(poly[0])]
    for i in range(1, len(poly) - 1):
        p, c, n = poly[i - 1], poly[i], poly[i + 1]
        d1 = math.dist(p, c); d2 = math.dist(c, n)
        leg_ = min(leg, d1 / 2, d2 / 2)
        if leg_ <= 1e-6:
            out.append(list(c)); continue
        u1 = ((c[0] - p[0]) / d1, (c[1] - p[1]) / d1)
        u2 = ((n[0] - c[0]) / d2, (n[1] - c[1]) / d2)
        right = abs(u1[0] * u2[1] - u1[1] * u2[0]) < 1e-6      # 共线 => 不切
        if right:
            out.append(list(c)); continue
        out.append([round(c[0] - u1[0] * leg_, 4), round(c[1] - u1[1] * leg_, 4)])
        out.append([round(c[0] + u2[0] * leg_, 4), round(c[1] + u2[1] * leg_, 4)])
    out.append(list(poly[-1]))
    return out


def candidates(p, q):
    """确定性候选族：直 / L×2 / Z×2×3档，各带 45° 切角变体。"""
    out = []
    base = [[list(p), list(q)]]
    base.append([list(p), [q[0], p[1]], list(q)])
    base.append([list(p), [p[0], q[1]], list(q)])
    for f in (0.25, 0.5, 0.75):
        xm = round(p[0] + (q[0] - p[0]) * f, 4); ym = round(p[1] + (q[1] - p[1]) * f, 4)
        base.append([list(p), [xm, p[1]], [xm, q[1]], list(q)])
        base.append([list(p), [p[0], ym], [q[0], ym], list(q)])
    seen = set()
    for b in base:
        for leg in (0.0, 0.5, 1.0, 2.0):
            poly = _chamfer(b, leg) if leg > 0 else [list(x) for x in b]
            k = tuple(tuple(x) for x in poly)
            if k in seen:
                continue
            seen.add(k)
            out.append(poly)
    return out


# ---------------------------------------------------------------- core
def route_pair(p, q, layer, obstacles, bounds=None, clear=CLEAR, net="__route__"):
    """核心：单网两点布。返回 ROUTED（含见证 poly）‖ BLOCKED（含最佳候选的具名违规）。"""
    tried, best = 0, None
    for poly in candidates(p, q):
        tried += 1
        bad = poly_violations(poly, obstacles, clearance=clear, layer=layer)
        if bounds:
            x0, y0, x1, y1 = bounds
            for pt in poly:
                if not (x0 <= pt[0] <= x1 and y0 <= pt[1] <= y1):
                    bad.append({"obstacle": "board_bounds", "kind": "bounds", "net": None,
                                "min_dist_mm": 0.0, "required_mm": 0.0})
                    break
        if not bad:
            return {"status": "ROUTED", "net": net, "layer": layer, "poly": poly,
                    "candidates_tried": tried, "rule": "deterministic closed-form candidate family, first valid wins"}
        score = sum(b["min_dist_mm"] for b in bad) / len(bad)
        if best is None or score < best["score"]:
            best = {"score": score, "candidate": poly, "violations": bad[:4]}
    return {"status": "BLOCKED", "net": net, "layer": layer, "candidates_tried": tried,
            "best_candidate": best["candidate"], "violations": best["violations"],
            "rule": "no candidate in the deterministic family cleared the constraints - named violations above"}


def obstacles_from_board(board, ignore_nets, layer, keepout_boxes=()):
    """真板 → 障碍集（保守轴对齐包围盒）。ignore_nets = 待布网（自身旧铜已由 M2 拆掉，仍排除）。"""
    import pcbnew as P
    b = P.LoadBoard(board)
    nm = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    obs = []
    for t in b.GetTracks():
        name = nm.get(t.GetNetCode(), "")
        if name in ignore_nets:
            continue
        layers = [b.GetLayerName(l) for l in t.GetLayerSet().Seq()] if t.GetClass() == "PCB_VIA" else [t.GetLayerName()]
        if layer not in layers:
            continue
        bb = t.GetBoundingBox()
        obs.append({"id": "track@%s" % name, "kind": "copper", "net": name,
                    "bbox": [round(P.ToMM(bb.GetX()) - 0.0, 4), round(P.ToMM(bb.GetY()), 4),
                             round(P.ToMM(bb.GetRight()), 4), round(P.ToMM(bb.GetBottom()), 4)]})
    for p in b.GetPads():
        name = nm.get(p.GetNetCode(), "")
        if name in ignore_nets:
            continue
        if layer not in [b.GetLayerName(l) for l in p.GetLayerSet().Seq()]:
            continue
        bb = p.GetBoundingBox()
        obs.append({"id": "pad@%s" % (p.GetNumber()), "kind": "copper", "net": name,
                    "bbox": [round(P.ToMM(bb.GetX()), 4), round(P.ToMM(bb.GetY()), 4),
                             round(P.ToMM(bb.GetRight()), 4), round(P.ToMM(bb.GetBottom()), 4)]})
    for k in keepout_boxes:
        obs.append({"id": k.get("id", "keepout"), "kind": "keepout", "net": None, "bbox": k["bbox"]})
    eb = b.GetBoardEdgesBoundingBox()
    bounds = [round(P.ToMM(eb.GetX()) + BOARD_MARGIN, 4), round(P.ToMM(eb.GetY()) + BOARD_MARGIN, 4),
              round(P.ToMM(eb.GetRight()) - BOARD_MARGIN, 4), round(P.ToMM(eb.GetBottom()) - BOARD_MARGIN, 4)]
    return obs, bounds


def pads_by_net(board, layer="F.Cu"):
    """只读：{net: [(x,y), ...]}（同网多 pad 的坐标，供测试选真用例）。"""
    import pcbnew as P
    b = P.LoadBoard(board)
    out = {}
    for p in b.GetPads():
        n = p.GetNetname()
        if not n or layer not in [b.GetLayerName(l) for l in p.GetLayerSet().Seq()]:
            continue
        pos = p.GetPosition()
        out.setdefault(n, []).append((round(P.ToMM(pos.x), 4), round(P.ToMM(pos.y), 4)))
    return out


def apply_routes(board, plans, out, width_mm=0.2):
    """**批量**落板（一次改板 · 子进程专用）：plans = [{net, layer, poly|segments}, ...]。"""
    import pcbnew as P
    b = P.LoadBoard(board)
    LM = {n: getattr(P, n.replace(".", "_")) for n in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu",
                                                      "In5.Cu", "In6.Cu", "In7.Cu", "B.Cu")}
    added, vias = 0, 0
    for pl in plans:
        net = b.FindNet(pl["net"])
        code = net.GetNetCode() if net is not None else -1
        polys = pl.get("polys") or ([pl["poly"]] if pl.get("poly") else [])
        seg_layers = pl.get("layers") or [pl.get("layer")] * len(polys)
        for poly, lay in zip(polys, seg_layers + ["F.Cu"] * (len(polys) - len(seg_layers))):
            if not lay or lay not in LM:
                return {"status": "REFUSED", "reason": "unknown layer %r for net %s" % (lay, pl["net"])}
            for i in range(len(poly) - 1):
                tr = P.PCB_TRACK(b)
                tr.SetStart(P.VECTOR2I(P.FromMM(poly[i][0]), P.FromMM(poly[i][1])))
                tr.SetEnd(P.VECTOR2I(P.FromMM(poly[i + 1][0]), P.FromMM(poly[i + 1][1])))
                tr.SetWidth(P.FromMM(width_mm)); tr.SetLayer(LM[lay]); tr.SetNetCode(code)
                b.Add(tr); added += 1
        for v in pl.get("vias", []):
            vi = P.PCB_VIA(b)
            vi.SetPosition(P.VECTOR2I(P.FromMM(v["at"][0]), P.FromMM(v["at"][1])))
            vi.SetWidth(P.FromMM(0.45)); vi.SetDrill(P.FromMM(0.25))
            vi.SetLayerPair(LM[v["layers"][0]], LM[v["layers"][1]]); vi.SetNetCode(code)
            b.Add(vi); vias += 1
    P.SaveBoard(out, b)
    import shutil, hashlib
    copied = []
    for ext in (".kicad_pro", ".kicad_dru"):
        src = board[:-len(".kicad_pcb")] + ext if board.endswith(".kicad_pcb") else board + ext
        if os.path.isfile(src):
            shutil.copy2(src, out[:-len(".kicad_pcb")] + ext if out.endswith(".kicad_pcb") else out + ext)
            copied.append(ext)
    return {"artifact": "eda_eng_route_apply_batch", "nets": [p["net"] for p in plans],
            "segments_added": added, "vias_added": vias, "project_config_copied": copied, "out": out,
            "out_sha16": hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]}


def apply_route(board, plan, out, layer=None, width_mm=0.2):
    """把 ROUTED 见证落板（**子进程专用**：改板会破坏同进程 SWIG 类型态）。"""
    import pcbnew as P
    b = P.LoadBoard(board)
    layer = layer or plan["layer"]
    LM = {n: getattr(P, n.replace(".", "_")) for n in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu",
                                                      "In5.Cu", "In6.Cu", "In7.Cu", "B.Cu")}
    net = b.FindNet(plan["net"])
    code = net.GetNetCode() if net is not None else -1
    poly = plan["poly"]
    added = 0
    for i in range(len(poly) - 1):
        t = P.PCB_TRACK(b)
        t.SetStart(P.VECTOR2I(P.FromMM(poly[i][0]), P.FromMM(poly[i][1])))
        t.SetEnd(P.VECTOR2I(P.FromMM(poly[i + 1][0]), P.FromMM(poly[i + 1][1])))
        t.SetWidth(P.FromMM(width_mm))
        t.SetLayer(LM[layer])
        t.SetNetCode(code)
        b.Add(t); added += 1
    # 铺铜重灌：否则落板会把既有 zone 填充态带偏（M3 具名残留 168->202 的首要嫌疑）
    zones = b.Zones()
    refilled = 0
    if len(zones):
        try:
            P.ZONE_FILLER(b).Fill(zones)
            refilled = len(zones)
        except Exception:                                     # noqa: BLE001
            refilled = -1
    P.SaveBoard(out, b)
    # 传导工程配置（.kicad_pro / .kicad_dru）：否则 DRC 的**库类口径**漂移
    # （实测：lib_footprint_issues +54 / lib_footprint_mismatch -20 ⇒ 总数 +34 假升）
    import shutil
    copied = []
    for ext in (".kicad_pro", ".kicad_dru"):
        src = board[:-len(".kicad_pcb")] + ext if board.endswith(".kicad_pcb") else board + ext
        if os.path.isfile(src):
            shutil.copy2(src, out[:-len(".kicad_pcb")] + ext if out.endswith(".kicad_pcb") else out + ext)
            copied.append(ext)
    import hashlib
    return {"artifact": "eda_eng_route_apply", "net": plan["net"], "layer": layer, "segments_added": added,
            "width_mm": width_mm, "zones_refilled": refilled, "project_config_copied": copied, "out": out,
            "out_sha16": hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]}


# ─────────────────────────────────────────────────────────────────────────────
# M3 v2 扩面（#K2-362 §二.5 / #K2-363）：多 pad 网（确定性 MST）＋ via/多层回退
# 三问 Q3 的「差异项」＝**解路器**（本仓路由器是图纸驱动，只会铺已知折线）
# ─────────────────────────────────────────────────────────────────────────────
def mst_edges(points):
    """确定性最小生成树（Prim · 平局按索引）—— 起点 = 索引 0（按坐标排序后）。"""
    n = len(points)
    if n < 2:
        return []
    idx = sorted(range(n), key=lambda i: (points[i][0], points[i][1]))
    inside = [idx[0]]
    outside = idx[1:]
    edges = []
    while outside:
        best = None
        for a in inside:
            for b in outside:
                d = math.dist(points[a], points[b])
                if best is None or d < best[0] - 1e-12 or (abs(d - best[0]) < 1e-12 and (a, b) < (best[1], best[2])):
                    best = (d, a, b)
        d, a, b = best
        edges.append((a, b, round(d, 4)))
        inside.append(b)
        outside.remove(b)
    return edges


def via_sites_clear(p, q, obstacles, clear=CLEAR, via_radius=0.175):
    """via 站点是否清场（保守：站点周围 clear+via_radius 内无外网障碍）。"""
    bad = []
    for site, tag in ((p, "p"), (q, "q")):
        for ob in obstacles:
            d = math.sqrt(_box_pt_d2(ob["bbox"], site))
            need = (0.0 if ob.get("kind") == "keepout" else clear) + (0.0 if ob.get("kind") == "keepout" else via_radius)
            if d <= need + 1e-9:
                bad.append({"site": tag, "obstacle": ob.get("id"), "kind": ob.get("kind"), "min_dist_mm": round(d, 4)})
    return bad


def route_pair_multi(p, q, layers, obstacles, bounds=None, clear=CLEAR, net="__route__"):
    """两点布 · 多层（**物理语义修正**）：`layers[0]` = 端点所在层 ⇒ 可**无 via** 直布；
    其余层**必须**在换层点落 via ⇒ 只走「端点上落两支 via、中间走该层」这一条确定性方案。
    """
    tried = []
    r0 = route_pair(p, q, layers[0], obstacles, bounds=bounds, clear=clear, net=net)
    tried.append({"layer": layers[0], "status": r0["status"]})
    if r0["status"] == "ROUTED":
        r0["vias"] = []
        r0["layers_tried"] = tried
        return r0
    for L in layers[1:]:
        bad = via_sites_clear(p, q, obstacles, clear=clear)
        if bad:
            tried.append({"layer": L, "status": "BLOCKED_VIA_SITES", "via_site_violations": bad})
            continue
        r = route_pair(p, q, L, obstacles, bounds=bounds, clear=clear, net=net)
        tried.append({"layer": L, "status": r["status"]})
        if r["status"] == "ROUTED":
            r["layer"] = L
            r["vias"] = [{"at": list(p), "layers": [layers[0], L]}, {"at": list(q), "layers": [layers[0], L]}]
            r["layers_tried"] = tried
            r["rule"] = "layer change requires vias: both endpoints carry a via and the middle runs on the new layer"
            return r
    return {"status": "BLOCKED", "net": net, "layer": layers[0], "layers_tried": tried,
            "violations": (r0.get("violations") if isinstance(r0, dict) else None),
            "rule": "the endpoint layer is blocked and no layer change (via at both endpoints) was legal"}


def route_net(pads, layers, obstacles, bounds=None, clear=CLEAR, net="__route__", via_radius=0.175):
    """**多 pad 网**：确定性 MST ⇒ 逐边布（同网铜不视为障碍）⇒ 全边通 ⇒ ROUTED（含逐边见证 ＋ 全部 via）。"""
    pads = [list(p) for p in pads]
    edges = mst_edges(pads)
    segs, vias, tried = [], [], []
    for a, b, d in edges:
        r = route_pair_multi(pads[a], pads[b], layers, obstacles, bounds=bounds, clear=clear, net=net)
        tried.append({"edge": [a, b], "len_mm": d, "status": r["status"]})
        if r["status"] != "ROUTED":
            return {"status": "BLOCKED", "net": net, "blocked_edge": [a, b], "edge_len_mm": d,
                    "edge_violations": r.get("violations"), "edges_tried": tried,
                    "rule": "a multi-pad net is routed over a deterministic MST; one blocked edge blocks the net"}
        segs.append({"edge": [a, b], "layer": r["layer"], "poly": r["poly"]})
        vias += r.get("vias", [])
    return {"status": "ROUTED", "net": net, "mst_edges": edges, "segments": segs, "vias": vias,
            "n_vias": len(vias), "edges_tried": tried,
            "rule": "deterministic MST (Prim, ties by index) over the net's pads; each edge by the layered candidate family"}


# ─────────────────────────────────────────────────────────────────────────────
# M3a · 施工图生成 ＋ 评审闸（#K2-365 §二：AI 画图 · 机器描线 · 机器判卷）
# 图 = 逐网「拓扑(MST)/走廊/层/过孔」计划 ＋ 每边的**约定编号**（样板规律），人机皆可读；
# 评审闸 = 图**先过**下列五项，M3b（照图执行）**无批图不许落板**。
# ─────────────────────────────────────────────────────────────────────────────
CONVENTION_LADDER = ["straight", "L-x", "L-y", "Z-x", "Z-y", "chamfer-0.5", "chamfer-1.0",
                     "chamfer-2.0"]          # 约定序（可读 · 固定 · 非搜索：先直后折再切角）


def _convention_of(poly):
    n = len(poly)
    bends = [abs((poly[i][0] - poly[i - 1][0]) * (poly[i + 1][1] - poly[i][1])
                 - (poly[i][1] - poly[i - 1][1]) * (poly[i + 1][0] - poly[i][0])) < 1e-9
             for i in range(1, n - 1)]
    if n == 2:
        return "straight"
    if n == 3:
        return "L"
    if n == 4:
        return "Z"
    return "chamfer(%d pts)" % n


def bends_are_45_or_90(poly, tol=0.02):
    """45° 工艺：每段折角只能是 0/45/90/135（即方向向量成 45° 的整数倍）。"""
    for i in range(1, len(poly) - 1):
        for a, b in (((poly[i - 1], poly[i])), ((poly[i], poly[i + 1]))):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            if L < 1e-9:
                continue
            ang = math.degrees(math.atan2(dy, dx)) % 45.0
            if min(ang, 45.0 - ang) > tol:
                return False
    return True


def draw_net(pads, layers, obstacles, bounds=None, clear=CLEAR, net="__route__"):
    """出**单网施工图**：拓扑(MST) + 每边 {约定 · 层 · 折线 · 过孔} + 走廊(包围盒)。"""
    pads = [list(p) for p in pads]
    edges = mst_edges(pads)
    rows, blocked = [], []
    for a, b, d in edges:
        r = route_pair_multi(pads[a], pads[b], layers, obstacles, bounds=bounds, clear=clear, net=net)
        if r["status"] != "ROUTED":
            blocked.append({"edge": [a, b], "violations": (r.get("violations") or [])[:2],
                            "via_sites": r.get("layers_tried")})
            continue
        xs = [pt[0] for pt in r["poly"]]; ys = [pt[1] for pt in r["poly"]]
        rows.append({"edge": [a, b], "edge_len_mm": d, "convention": _convention_of(r["poly"]),
                     "layer": r["layer"], "poly": r["poly"],
                     "vias": [{"at": list(v["at"]), "layers": list(v["layers"])} for v in r.get("vias", [])],
                     "corridor_bbox": [round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3)]})
    return {"net": net, "pads": pads, "mst_edges": edges, "edges": rows, "blocked_edges": blocked,
            "status": "DRAWN" if not blocked else "DEAD_END(部分边不可出图 ⇒ 需兜底求解器 → 必走评审)",
            "rule": "#K2-365 sec.2 M3a: the drawing comes from the sample-convention ladder (topology=MST, "
                    "corridor=declared bbox, layer=declared per edge, vias=declared) - NOT from a geometric crawl"}


def review_drawing(drawing, obstacles, clear=CLEAR, layers_allowed=("F.Cu", "In2.Cu")):
    """**评审闸**（人机皆可读）：逐边核 端点/层/45°/净距/走廊 ⇒ PASS ‖ FAIL(具名行)。M3b 无过闸之图不许落板。"""
    rows, ok = [], True
    for ed in drawing["edges"]:
        poly, lay = ed["poly"], ed["layer"]
        checks = {
            "endpoints_match": math.dist(poly[0], drawing["pads"][ed["edge"][0]]) < 1e-6 and
                               math.dist(poly[-1], drawing["pads"][ed["edge"][1]]) < 1e-6,
            "layer_declared": lay in layers_allowed,
            "bends_45_or_90": bends_are_45_or_90(poly),
            "oracle_clear": not poly_violations(poly, obstacles, clearance=clear, layer=lay),
            "corridor_declared": bool(ed.get("corridor_bbox")),
        }
        if not all(checks.values()):
            ok = False
        rows.append({"net": drawing["net"], "edge": ed["edge"], "convention": ed["convention"],
                     "layer": lay, **checks})
    for be in drawing["blocked_edges"]:
        ok = False
        rows.append({"net": drawing["net"], "edge": be["edge"], "convention": None, "layer": None,
                     "endpoints_match": None, "layer_declared": None, "bends_45_or_90": None,
                     "oracle_clear": False, "corridor_declared": None, "blocked": True})
    return {"net": drawing["net"], "rows": rows, "verdict": "PASS" if ok else "FAIL",
            "rule": "#K2-365 sec.2: the drawing must pass review (endpoints / declared layer / 45-degree convention / "
                    "clearance oracle / declared corridor) BEFORE the executor may lay copper"}


def drawing_markdown(drawings):
    """人可读版（评审用）。"""
    L = ["| 网 | 边 | 约定 | 层 | 折点数 | 过孔 | 走廊包围盒 |", "|---|---|---|---|---|---|---|"]
    for d in drawings:
        for ed in d["edges"]:
            L.append("| %s | %s | %s | %s | %d | %d | %s |" % (
                d["net"], ed["edge"], ed["convention"], ed["layer"], len(ed["poly"]),
                len(ed["vias"]), ed["corridor_bbox"]))
        for be in d["blocked_edges"]:
            L.append("| %s | %s | **死结** | — | — | — | — |" % (d["net"], be["edge"]))
    return "\n".join(L)
