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


def _obstacle_dist(ob, p):
    """点到**障碍真实形状**的距离（#K2-370 §三.3 · 缺口 C32 · v2 补焊盘/过孔）。
      · `a`/`b`（track 线段）→ 点-线段距离减半宽
      · `center`/`radius`（via 圆）→ 点到圆心减半径
      · `rect`（**有向**焊盘矩形）→ 旋转到局部系后的精确矩形距离（中心对称 ⇒ 旋转符号无关）
      · 其余（keepout / 合成箱 / 无法真形化的焊盘）→ AABB 距离（具名保留）
    """
    if "a" in ob:
        return max(0.0, math.sqrt(_seg_pt_d2(ob["a"], ob["b"], p)) - float(ob.get("half_w", 0.0)))
    if "center" in ob:
        return max(0.0, math.hypot(p[0] - ob["center"][0], p[1] - ob["center"][1]) - float(ob["radius"]))
    if "rect" in ob:
        r = ob["rect"]
        th = math.radians(r.get("rot", 0.0))
        dx, dy = p[0] - r["cx"], p[1] - r["cy"]
        c, sn = math.cos(-th), math.sin(-th)
        lx, ly = dx * c - dy * sn, dx * sn + dy * c
        ex = max(abs(lx) - r["sx"] / 2.0, 0.0)
        ey = max(abs(ly) - r["sy"] / 2.0, 0.0)
        return math.hypot(ex, ey)
    return math.sqrt(_box_pt_d2(ob["bbox"], p))


def _obstacle_margin(ob, clear, width, pitch, for_via=False, via_radius=0.175):
    """格子判定余量：**真形**障碍（线段/圆/有向矩形）的铜体已在距离里 ⇒ 只加 (间隙＋半格)；
    纯箱障碍仍按旧式 (宽/2 或 via 半径) 加余量（**向后兼容**，合成用例零改动）。"""
    base = (clear + via_radius + pitch / 2.0) if for_via else (clear + pitch / 2.0)
    true_shape = ("a" in ob) or ("center" in ob) or ("rect" in ob)
    return base if true_shape else base + (0.0 if for_via else width / 2.0)


def poly_violations(poly, obstacles, clearance=CLEAR, step=0.05, layer=None):
    """返回 [(obstacle_id, min_dist_mm, kind)]，只含违规项（keepout 用 clearance=0 且 min_dist==0 记违规）。"""
    bad = []
    pts = _poly_samples(poly, step)
    for ob in obstacles:
        if layer and ob.get("layers") and layer not in ob["layers"]:
            continue
        d = min(_obstacle_dist(ob, p) for p in pts)
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
        if t.GetClass() == "PCB_VIA":                      # 过孔 = 圆（真形）
            vp = t.GetPosition()
            obs.append({"id": "via@%s" % name, "kind": "copper", "net": name,
                        "center": [round(P.ToMM(vp.x), 4), round(P.ToMM(vp.y), 4)],
                        "radius": round(P.ToMM(t.GetWidth()) / 2.0, 4),
                        "bbox": [round(P.ToMM(bb.GetX()), 4), round(P.ToMM(bb.GetY()), 4),
                                 round(P.ToMM(bb.GetRight()), 4), round(P.ToMM(bb.GetBottom()), 4)]})
            continue
        st, en = t.GetStart(), t.GetEnd()
        obs.append({"id": "track@%s" % name, "kind": "copper", "net": name,
                    # **真形**（#K2-370 §三.3 / C32）：带线段端点与半宽，AABB 仅作粗筛窗
                    "a": [round(P.ToMM(st.x), 4), round(P.ToMM(st.y), 4)],
                    "b": [round(P.ToMM(en.x), 4), round(P.ToMM(en.y), 4)],
                    "half_w": round(P.ToMM(t.GetWidth()) / 2.0, 4),
                    "bbox": [round(P.ToMM(bb.GetX()) - 0.0, 4), round(P.ToMM(bb.GetY()), 4),
                             round(P.ToMM(bb.GetRight()), 4), round(P.ToMM(bb.GetBottom()), 4)]})
    for p in b.GetPads():
        name = nm.get(p.GetNetCode(), "")
        if name in ignore_nets:
            continue
        if layer not in [b.GetLayerName(l) for l in p.GetLayerSet().Seq()]:
            continue
        bb = p.GetBoundingBox()
        own = {"id": "pad@%s" % (p.GetNumber()), "kind": "copper", "net": name,
               "bbox": [round(P.ToMM(bb.GetX()), 4), round(P.ToMM(bb.GetY()), 4),
                        round(P.ToMM(bb.GetRight()), 4), round(P.ToMM(bb.GetBottom()), 4)]}
        # 焊盘 = **有向矩形**（真形 · C32 v2）；圆形/矩形/椭圆/圆角矩形均可（矩形是其余形状的外包，
        # 保守成立；CUSTOM/TRAPEZOID 等退回 AABB 具名保留）
        try:
            sz = p.GetSize()
            pc = p.GetPosition()
            own["rect"] = {"cx": round(P.ToMM(pc.x), 4), "cy": round(P.ToMM(pc.y), 4),
                           "sx": round(P.ToMM(sz.x), 4), "sy": round(P.ToMM(sz.y), 4),
                           "rot": round(p.GetOrientationDegrees(), 3)}
        except Exception:                                              # noqa: BLE001
            pass
        obs.append(own)
    for k in keepout_boxes:
        obs.append({"id": k.get("id", "keepout"), "kind": "keepout", "net": None, "bbox": k["bbox"]})
    eb = b.GetBoardEdgesBoundingBox()
    bounds = [round(P.ToMM(eb.GetX()) + BOARD_MARGIN, 4), round(P.ToMM(eb.GetY()) + BOARD_MARGIN, 4),
              round(P.ToMM(eb.GetRight()) - BOARD_MARGIN, 4), round(P.ToMM(eb.GetBottom()) - BOARD_MARGIN, 4)]
    return obs, bounds


def obstacles_multi(board, ignore_nets, layers, keepout_boxes=()):
    """多层障碍（**带 layers 标记**，供多层 maze 用）——逐层取真形后合并。"""
    obs = []
    for L in layers:
        for ob in obstacles_from_board(board, ignore_nets, L, keepout_boxes)[0]:
            o = dict(ob)
            o["layers"] = [L]
            obs.append(o)
    bnd = obstacles_from_board(board, ignore_nets, layers[0], keepout_boxes)[1]
    return obs, bnd


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


def mask_bridge_pairs(points, foreign_pads, clear_mm):
    """**(b) 阻焊桥预检（纯函数）**：新铜折线点到**异网焊盘**的最近距离 < clear_mm ⇒ 记为风险对。
    `foreign_pads` = [(ref, pad, x, y)]（mm）。返回 [(point, ref, pad, dist_mm)]（确定性）。"""
    out = []
    for q in points:
        for (ref, pad, px, py) in foreign_pads:
            d = math.hypot(q[0] - px, q[1] - py)
            if d < clear_mm - 1e-9:
                out.append({"point": [round(q[0], 4), round(q[1], 4)], "ref": ref, "pad": pad,
                            "dist_mm": round(d, 4), "required_mm": clear_mm})
    return out


def apply_routes(board, plans, out, width_mm=0.2, bound_rect=None, mask_clear_mm=None):
    """**批量**落板（一次改板 · 子进程专用）：plans = [{net, layer, poly|segments}, ...]。
    `bound_rect`（#K2-380 §二.3 收尾道 · **新增可选参数，默认不改老行为**）：落板前**框外坐标检查** ——
    任何折线/过孔越出声明域 ⇒ **fail-closed 拒收并具名**，绝不落板。"""
    import pcbnew as P
    if bound_rect:
        _x0, _y0, _x1, _y1 = [float(v) for v in bound_rect]
        _eps = 1e-6
        for _pl in plans:
            _pts = []
            for _poly in (_pl.get("polys") or ([_pl["poly"]] if _pl.get("poly") else [])):
                _pts += [list(_q) for _q in _poly]
            _pts += [list(_v["at"]) for _v in (_pl.get("vias") or [])]
            for _q in _pts:
                if not (_x0 - _eps <= _q[0] <= _x1 + _eps and _y0 - _eps <= _q[1] <= _y1 + _eps):
                    return {"artifact": "eda_eng_route_apply_batch", "status": "REFUSED_OUT_OF_BOUND",
                            "net": _pl.get("net"), "point": [round(_q[0], 4), round(_q[1], 4)],
                            "bound_rect": [_x0, _y0, _x1, _y1],
                            "rule": "#K2-380 sec.2.3: the work domain is a HARD bound - a plan that leaves it "
                                    "must never land (fail-closed)"}
    b = P.LoadBoard(board)
    LM = {n: getattr(P, n.replace(".", "_")) for n in ("F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu",
                                                      "In5.Cu", "In6.Cu", "In7.Cu", "B.Cu")}
    if mask_clear_mm:
        # (b) **阻焊桥预检**（#K2-385 §五.2）：落铜前，新铜与**异网焊盘**太近 ⇒ fail-closed 具名拒收
        # （对"挪位后焊盘太近"这类后果，引擎**拒绝**而不是默默造桥 —— 逼出放置层修正）
        _pads = []
        for _fp in b.GetFootprints():
            for _pd in _fp.Pads():
                _n = _pd.GetNetname()
                _pos = _pd.GetPosition()
                _pads.append((_fp.GetReference(), _pd.GetNumber(), _n,
                              P.ToMM(_pos.x), P.ToMM(_pos.y)))
        for _pl in plans:
            _pts = []
            for _poly in (_pl.get("polys") or ([_pl["poly"]] if _pl.get("poly") else [])):
                _pts += [list(_q) for _q in _poly]
            _pts += [list(_v["at"]) for _v in (_pl.get("vias") or [])]
            _f = [(r_, p_, x_, y_) for (r_, p_, n_, x_, y_) in _pads if n_ != _pl.get("net")]
            _risk = mask_bridge_pairs(_pts, [(r_, p_, x_, y_) for (r_, p_, x_, y_) in _f], mask_clear_mm)
            if _risk:
                return {"artifact": "eda_eng_route_apply_batch", "status": "REFUSED_MASK_BRIDGE_RISK",
                        "net": _pl.get("net"), "risk": _risk[:3],
                        "rule": "#K2-385 sec.5.2(b): the landing guard refuses copper that would bridge the "
                                "solder mask to a foreign pad (fail-closed; the placement, not the router, must change)"}
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
    # 复敷铜（#K2-366 sec.2 step 5 · #K2-369 sec.3.2/4）：**批路径此前从未调用 ZONE_FILLER**
    # => 「复敷铜」是空操作。此处真接线；失败即具名返回（fail-closed）。
    zones = b.Zones()
    refilled = 0
    if len(zones):
        try:
            P.ZONE_FILLER(b).Fill(zones)
            refilled = len(zones)
        except Exception as e:                                 # noqa: BLE001
            return {"artifact": "eda_eng_route_apply_batch", "status": "REFILL_FAILED",
                    "reason": "ZONE_FILLER raised: %s" % e, "nets": [p["net"] for p in plans],
                    "segments_added": added, "vias_added": vias, "zones_refilled": -1}
    P.SaveBoard(out, b)
    import shutil, hashlib
    copied = []
    for ext in (".kicad_pro", ".kicad_dru"):
        src = board[:-len(".kicad_pcb")] + ext if board.endswith(".kicad_pcb") else board + ext
        if os.path.isfile(src):
            shutil.copy2(src, out[:-len(".kicad_pcb")] + ext if out.endswith(".kicad_pcb") else out + ext)
            copied.append(ext)
    return {"artifact": "eda_eng_route_apply_batch", "status": "APPLIED",
            "nets": [p["net"] for p in plans],
            "segments_added": added, "vias_added": vias, "zones_refilled": refilled,
            "project_config_copied": copied, "out": out,
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


# ─────────────────────────────────────────────────────────────────────────────
# #K2-366 · 教科书级基础算法：**迷宫布线器（Lee / A\*）**
# 连接图形 = (层, i, j) 格点；**8 邻域**（含对角 ⇒ 45°）；**换层 = 过孔**（须先净场，计惩罚）。
# 确定性：f 相同者按 (g, 层, i, j) 破平局；不通 ⇒ **具名阻断**（禁绕行糊弄）。
# 间距/禁区：按 (clearance + width/2 + pitch/2) **保守膨胀**障碍后整格占用。
# ─────────────────────────────────────────────────────────────────────────────
def grid_of(obstacles, bounds, layer, pitch=0.5, clear=CLEAR, width=0.2, via_radius=0.175,
            for_via=False):
    """返回 (nx, ny, x0, y0, blocked) 的布尔网格（True=占用）。"""
    x0b, y0b, x1b, y1b = bounds
    nx = max(2, int((x1b - x0b) / pitch) + 1)
    ny = max(2, int((y1b - y0b) / pitch) + 1)
    # 索引 0..nx-1 ↔ x0b + i*pitch ≤ x1b
    blocked = bytearray(nx * ny)
    for ob in obstacles:
        if layer and ob.get("layers") and layer not in ob["layers"]:
            continue
        inflate = _obstacle_margin(ob, clear, width, pitch, for_via=for_via, via_radius=via_radius)
        bx0, by0, bx1, by1 = ob["bbox"]
        i0 = max(0, int((bx0 - inflate - x0b) / pitch) - 1)
        i1 = min(nx - 1, int((bx1 + inflate - x0b) / pitch) + 1)
        j0 = max(0, int((by0 - inflate - y0b) / pitch) - 1)
        j1 = min(ny - 1, int((by1 + inflate - y0b) / pitch) + 1)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                cx, cy = x0b + i * pitch, y0b + j * pitch
                if _obstacle_dist(ob, (cx, cy)) <= inflate + 1e-9:
                    blocked[i * ny + j] = 1
    return {"nx": nx, "ny": ny, "x0": x0b, "y0": y0b, "pitch": pitch, "blocked": blocked}


def _snap(g, pt, free_of=None):
    """最近的可走格（确定性：按 (距离, i, j) 取最小）。"""
    nx, ny, x0, y0, pitch, blk = g["nx"], g["ny"], g["x0"], g["y0"], g["pitch"], g["blocked"]
    i0 = min(nx - 1, max(0, int(round((pt[0] - x0) / pitch))))
    j0 = min(ny - 1, max(0, int(round((pt[1] - y0) / pitch))))
    best, bestd = None, None
    for rad in range(0, max(nx, ny)):
        for i in range(max(0, i0 - rad), min(nx - 1, i0 + rad) + 1):
            for j in range(max(0, j0 - rad), min(ny - 1, j0 + rad) + 1):
                if max(abs(i - i0), abs(j - j0)) != rad:
                    continue
                if blk[i * ny + j] or (free_of and (i * ny + j) in free_of):
                    continue
                d = math.hypot(x0 + i * pitch - pt[0], y0 + j * pitch - pt[1])
                if bestd is None or d < bestd - 1e-9:
                    best, bestd = (i, j), d
        if best and rad >= 1:
            break
    return best


def maze_route(p, q, layers, obstacles, bounds, pitch=0.5, clear=CLEAR, width=0.2, via_penalty=8.0,
               endpoint_clear=None, snap_cells=2):
    """Lee/A* 迷宫布线：p→q，可换层（过孔），8 邻域（45°）。不通 ⇒ 具名阻断。
    endpoint_clear：端点"埋在别人铜里"判据所用间隙（默认 = clear）。障碍是**保守 AABB**，
    故块内重连把端点判据放宽到 0（只拒"真的埋在别人铜里"的点）——正确性由健全判卷器 M4 兜底。"""
    import heapq
    ec = clear if endpoint_clear is None else endpoint_clear
    # 端点自身必须在净场里（否则不是"布线"问题，而是"目标点落在别人铜上"）
    badpts = [{"which": w, "violations": poly_violations([[pt[0], pt[1]], [pt[0], pt[1]]], obstacles,
                                                         clearance=ec, layer=layers[0])}
              for w, pt in (("p", p), ("q", q))]
    badpts = [b for b in badpts if b["violations"]]
    if badpts:
        return {"status": "BLOCKED", "semantics": "DECIDABLE_INFEASIBLE_FOR_THIS_PAIR",
                "reason": "an endpoint lies inside foreign copper / a keepout",
                "endpoint_violations": badpts,
                "rule": "#K2-366: the maze is not allowed to teleport an endpoint out of an obstacle"}
    grids = {L: grid_of(obstacles, bounds, L, pitch, clear, width) for L in layers}
    gv = {L: grid_of(obstacles, bounds, L, pitch, clear, width, for_via=True) for L in layers}
    # **物理**：端点住在 layers[0]（焊盘所在层）⇒ 布线**必须**从 layers[0] 起、回 layers[0] 止；
    # 任何去别的层的行程都要在换层处落 via（_path_to_polys 负责记账）。
    L0 = layers[0]
    starts, goals = {}, {}
    s, t = _snap(grids[L0], p), _snap(grids[L0], q)
    cap = snap_cells * pitch
    if s and math.hypot(s[0] * pitch + grids[L0]["x0"] - p[0], s[1] * pitch + grids[L0]["y0"] - p[1]) > cap:
        s = None
    if t and math.hypot(t[0] * pitch + grids[L0]["x0"] - q[0], t[1] * pitch + grids[L0]["y0"] - q[1]) > cap:
        t = None
    if s:
        starts[L0] = s
    if t:
        goals[L0] = t
    if not starts:
        return {"status": "BLOCKED", "reason": "no free start cell on any allowed layer",
                "layers": list(layers), "rule": "#K2-366: the start point is boxed in"}
    if not goals:
        # R970-fix: the goal (q) could not be snapped to a free cell on the PAD layer, so GOAL would be empty and
        # the heuristic would raise on min(()) - return a NAMED blockage instead (semantic discipline: NOT FOUND).
        return {"status": "BLOCKED", "semantics": "NOT_FOUND",
                "reason": "no free goal cell on the pad layer (the target pad is boxed in / not snappable)",
                "layers": list(layers),
                "rule": "#K2-367 sec.2: NOT FOUND != IMPOSSIBLE; the maze may not invent a target that is boxed in"}
    GOAL = {(L0, goals[L0][0], goals[L0][1])} if L0 in goals else set()   # 目标必须在**焊盘层**上
    dist = {}
    pq = []
    for L, s in starts.items():
        d0 = math.hypot(s[0] - min(goals.values(), key=lambda t: abs(t[0] - s[0]) + abs(t[1] - s[1]))[0],
                        s[1] - min(goals.values(), key=lambda t: abs(t[0] - s[0]) + abs(t[1] - s[1]))[1]) * pitch
        dist[(L, s[0], s[1])] = 0.0
        heapq.heappush(pq, (d0, 0.0, L, s[0], s[1]))
    prev, seen = {}, set()
    NEI = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
           (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    reached = 0
    while pq:
        f, g_, L, i, j = heapq.heappop(pq)
        key = (L, i, j)
        if key in seen:
            continue
        seen.add(key); reached += 1
        if (L, i, j) in GOAL:
            # 回溯
            path = [(L, i, j)]
            while key in prev:
                key = prev[key]; path.append(key)
            path.reverse()
            return _path_to_polys(path, grids, p, q)
        gr = grids[L]
        for di, dj, cost in NEI:
            ni, nj = i + di, j + dj
            if not (0 <= ni < gr["nx"] and 0 <= nj < gr["ny"]):
                continue
            if gr["blocked"][ni * gr["ny"] + nj]:
                continue
            if di and dj and (gr["blocked"][(i + di) * gr["ny"] + j] or gr["blocked"][i * gr["ny"] + (j + dj)]):
                continue                                   # 禁切角
            nk = (L, ni, nj)
            nd = g_ + cost
            if nd < dist.get(nk, 1e18) - 1e-9:
                dist[nk] = nd
                prev[nk] = key
                h = min(math.hypot(ni - t[0], nj - t[1]) for t in goals.values()) * pitch
                heapq.heappush(pq, (nd + h, nd, L, ni, nj))
        # 换层（过孔）—— **棱柱语义**（#K2-369 sec.3 / gap C31）：via 必须穿透 span 内**每一层**，
        # 而不是只查两端层；跨 >2 层的 via（如 F.Cu->In4.Cu 途经 In1/In2/In3）此前漏检。
        iL = layers.index(L)
        for L2 in layers:
            if L2 == L:
                continue
            iL2 = layers.index(L2)
            lo, hi = (iL, iL2) if iL < iL2 else (iL2, iL)
            if any(gv[layers[k]]["blocked"][i * gv[layers[k]]["ny"] + j] for k in range(lo, hi + 1)):
                continue                                   # via 站点须 span 内每一层净场网格都空
            nk = (L2, i, j)
            nd = g_ + via_penalty
            if nd < dist.get(nk, 1e18) - 1e-9:
                dist[nk] = nd
                prev[nk] = key
                h = min(math.hypot(i - t[0], j - t[1]) for t in goals.values()) * pitch
                heapq.heappush(pq, (nd + h, nd, L2, i, j))
    near = None
    for t in goals.values():
        d = min((math.hypot(t[0] - k[1], t[1] - k[2]) for k in seen), default=None)
        near = d if near is None else min(near, d)
    return {"status": "BLOCKED",
            "semantics": "NOT_FOUND",           # 语义纪律（#K2-367 §二）：**未找到 ≠ 不存在**
            "semantics_rule": "this result must be read as NOT FOUND, never as IMPOSSIBLE; an impossibility claim "
                              "requires an infeasibility certificate on a bounded instance",
            "reason": "the search exhausted every reachable cell without reaching the target",
            "layers": list(layers), "cells_expanded": reached,
            "closest_approach_cells": near,
            "rule": "#K2-366/#K2-367: an unroutable net is reported with its blockage - no fudged detour"}


def _path_to_polys(path, grids, p, q):
    """(层,i,j) 路径 → 逐层折线 ＋ 过孔表（端点精确接到 p/q）。"""
    polys, vias = [], []
    cur_layer = path[0][0]
    cur = [list(p)]
    for idx in range(1, len(path)):
        L, i, j = path[idx]
        pt = [grids[L]["x0"] + i * grids[L]["pitch"], grids[L]["y0"] + j * grids[L]["pitch"]]
        if L != cur_layer:
            vias.append({"at": list(pt), "layers": [cur_layer, L]})
            cur.append(pt)
            polys.append({"layer": cur_layer, "poly": cur})
            cur_layer, cur = L, [list(pt)]
        else:
            if cur and abs(cur[-1][0] - pt[0]) < 1e-9 and abs(cur[-1][1] - pt[1]) < 1e-9:
                continue
            cur.append(pt)
    cur.append(list(q))
    polys.append({"layer": cur_layer, "poly": cur})
    return {"status": "ROUTED", "polys": polys, "vias": vias, "layer": polys[0]["layer"],
            "cells": len(path),
            "rule": "#K2-366 maze router (Lee/A*): 8-neighbour (45 degrees), layer change = via, deterministic tie-break"}
