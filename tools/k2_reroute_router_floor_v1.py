#!/usr/bin/env python3
"""k2_reroute_router_floor_v1.py --- thin wrapper around the in-register maze router (k2_p4_mroute_v1.py) that
raises the exact gate's inter-net clearance model to the kicad-cli netclass floor.

WHY: the ACCEPTANCE authority is kicad-cli DRC (project netclass clearance 0.20 mm), while the frozen
drc_rules.json model says 0.10 mm for LOW_SPEED/GND (registered M-ENG-CLEARANCE-MODEL-DIVERGENCE).  The router
must be at least as strict as the acceptance authority, otherwise it emits copper that kicad-cli flags.
The in-register asset is NOT modified - the patch is applied at import time in this wrapper.

Usage: k2_reroute_router_floor_v1.py --in <board> --drc <drc.json> --out <board> --ledger <json>
        [--margin 3.0] [--floor 0.20] [--only-net NET] [--dry-run]
"""
import argparse, importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MROUTE = os.path.join(ROOT, "tools", "k2_p4_mroute_v1.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--drc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--margin", type=float, default=3.0)
    ap.add_argument("--floor", type=float, default=0.20)
    ap.add_argument("--only-net", default=None)
    ap.add_argument("--bound-rect", dest="bound_rect", default=None,
                    help="C35 in-loop wall x0,y0,x1,y1 (mm) - set on the maze module so out-of-domain cells "
                         "are never selectable (forwarded, not repaired afterwards)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reflowable", default="",
                    help="B1 (#K2-414 sec.2.1): comma list of POUR-REFLOWABLE nets - their copper is NOT an "
                         "obstacle in the maze model (it reflows after routing); the landing no-isolated-copper "
                         "gate is unchanged. '' = disable.")
    ap.add_argument("--coarse-step", dest="coarse_step", default="fine",
                    help="B2 (#K2-414 sec.2.2): 'fine' = use the in-register FINE_STEP (0.10); or a number.")
    ap.add_argument("--port-refs", dest="port_refs", default="",
                    help="#K2-431 sec.2.6 fix 1: footprints whose pads are FIXED PORTS (e.g. J13) - their pads become "
                         "extra goals for their nets (the in-region connector must be terminated ON, not around)")
    ap.add_argument("--channels", default="",
                    help="#K2-429 (A): per-net HARD channel constraints 'net:x0,y0,x1,y1;...' - each edge is routed with "
                         "mr.WALL_RECT set to that net's channel (the maze's EXISTING bound-rect vehicle)")
    ap.add_argument("--order-list", dest="order_list", default=None,
                    help="#K2-415 lever 'order': a file with one net name per line (priority order, first = first)")
    ap.add_argument("--order", default="dist_asc", choices=["dist_asc", "dist_desc", "hard", "list"],
                    help="#K2-396: the maze's in-register deterministic routing order (default unchanged)")
    a = ap.parse_args()
    sp = importlib.util.spec_from_file_location("k2mrfloor", MROUTE)
    mr = importlib.util.module_from_spec(sp); sp.loader.exec_module(mr)
    cv = mr.cv
    orig = cv._req
    cv._req = lambda x, y: max(orig(x, y), a.floor)
    if a.bound_rect:                                  # C35：把域作为**搜索约束**注入（不改迷宫本体）
        mr.WALL_RECT = tuple(float(v) for v in a.bound_rect.split(","))
    # ── #K2-414 §二.1 **B1 敷铜重分类**：可回流网（默认 GND）的铜**不入障碍模型** ──────────────
    POUR = frozenset(n for n in (a.reflowable or "").split(",") if n)
    if POUR and getattr(mr, "f3", None) is not None:
        _orig_ctx = mr.f3.Ctx

        def _ctx_no_pour(b):
            c = _orig_ctx(b)
            c.tracks = [t for t in c.tracks if t["net"] not in POUR]
            c.vias = {u: v for u, v in c.vias.items() if v["net"] not in POUR}
            c.pads = {u: p for u, p in c.pads.items() if p["net"] not in POUR}
            return c
        mr.f3.Ctx = _ctx_no_pour
    # ── #K2-392 第三边：**端口感知目标（port-aware goals）** ────────────────────────────
    # 端点「无空闲起止位」（no-free-start/goal-node）多因该端点落在**框外**（框被 C35 封死），
    # 迷宫在界内找不到属于该岛的格。处置：把**框切残段端口**（∂R 上、同网的 track 端点）当**目标**，
    # 把「跨框另猜目标」改成「接回该网在 ∂R 的端口」——同网铜在框外继续，故接到端口即恢复连通。
    # **不改迷宫本体**：运行期在 wrapper 内给 `mr.solve_edge` 打补丁（与 `cv._req`/`WALL_RECT` 同法）。
    _set_step(a.coarse_step)
    # ── #K2-429 §三.2 **通道分配入链（硬约束）**：逐网把通道喂给迷宫的既有 bound-rect 车辆 ─────────────
    CH = {}
    for _it in [x for x in (a.channels or "").split(";") if x.strip()]:
        _n, _r = _it.split(":", 1)
        CH[_n] = tuple(float(v) for v in _r.split(","))
    _GLOBAL_WALL = mr.WALL_RECT
    mr._CHANNELS = CH                                 # the channel map must live on `mr` (see solve)
    mr._CH_MARGIN = 0.0
    # ── #K2-431 §二.6 修法①：**区内连接器 PTH 焊盘作固定端口目标** ─────────────────────────────
    _PP = []
    if a.port_refs:
        try:
            import pcbnew as _PY
            _bd = _PY.LoadBoard(a.src)
            _want = {r.strip() for r in a.port_refs.split(",") if r.strip()}
            for _fp in _bd.GetFootprints():
                if _fp.GetReference() not in _want:
                    continue
                for _pd in _fp.Pads():
                    if not _pd.GetNetname():
                        continue
                    _p = _pd.GetPosition()
                    _lay = None
                    for _L in ("F.Cu", "B.Cu", "In5.Cu"):
                        if _bd.GetLayerName(_pd.GetLayer()) == _L:
                            _lay = _L
                            break
                    _PP.append((_pd.GetNetname(), round(_PY.ToMM(_p.x), 4), round(_PY.ToMM(_p.y), 4),
                                _lay or "F.Cu"))
        except Exception:                                            # noqa: BLE001
            _PP = []
    mr._PORT_PADS = _PP                               # #K2-430 sec.2.4: FROZEN - the channel already includes
                                                      # the reach; ZERO runtime freedom (no ladder)
    recs = []
    if mr.WALL_RECT:
        recs = _install_port_aware_goals(mr, tuple(mr.WALL_RECT))
    s = mr.run(a.src, a.drc, a.out, a.ledger, a.margin, a.only_net, a.dry_run, a.order, a.order_list)
    # #K2-394 §二.1：**端口可达性预检**并列盘（不可达者**具名**；不改变路由结果）
    if recs:
        pre = {"artifact": "eda_eng_port_reachability_precheck", "board": a.src, "bound_rect": a.bound_rect,
               "n_failed_edges": len(recs),
               "endpoint_own_cell_hits": getattr(mr, "_endpoint_own_cell_hits", {}).get("hits", 0),
               "b1_reflowable": sorted(POUR),
               "b2_grid_step": ("FINE_STEP=%s" % getattr(mr, "FINE_STEP", "?")) if _FINE else _FINE_NUM,
               "endpoint_own_cell_rule": "#K2-412 sec.4.3 (D1): the endpoint-own-cell snap relaxation "
                                         "(bounded, C35-held, seg_exact/via_exact still gate) fires when the plain "
                                         "snap prunes a cell that lies on the net's OWN copper.",
               "unreachable": [r for r in recs if not r["reachable_port"]],
               "reachable_via_port": [r for r in recs if r["reachable_port"]],
               "rule": "#K2-394 sec.2.1: before routing, name every endpoint that cannot reach any same-net frame port "
                       "(reachable => the port retry routes it; unreachable => named for the change-set / expansion decision)."}
        json.dump(pre, open(a.ledger + ".precheck.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json_dumps(s))
    return 0


_FINE = True          # B2 default: use the in-register FINE_STEP (#K2-414 sec.2.2)
_FINE_NUM = None      # explicit numeric override (None = unused)


def _set_step(mode):
    """B2: 'fine' => use mr.FINE_STEP; a number => that number; anything falsy => keep the caller's step."""
    global _FINE, _FINE_NUM
    if mode in (None, "", "keep"):
        _FINE, _FINE_NUM = False, None
    elif mode == "fine":
        _FINE, _FINE_NUM = True, None
    else:
        _FINE, _FINE_NUM = False, float(mode)


def _install_port_aware_goals(mr, wall, tol=0.02):
    """返回**端口可达性预检记录**（#K2-394 §二.1）：每条失败边记录 端口是否可达 / 试了几个端口。"""
    """把 `solve_edge` 包一层：正常失败且原因为 no-free-start/goal-node 时，(i) 改用**同网 ∂R 端口**
    （作为目标或起点）重试一次；(ii) **端点自身格松弛**（#K2-412 §四.3 · 承 #K2-411 §二 D1）。
    确定性（端口按 (layer,x,y,uuid) 排序 · 自身格按 (半径, di, dj)）；不搜索、不调参。"""
    orig = mr.solve_edge
    orig_snap = mr.snap_node
    PORT_PTS = set()
    OWN_CELL = {"hits": 0}                 # #K2-412 §四.3：端点自身格松弛开火次数（写入 precheck 并列盘）
    mr._endpoint_own_cell_hits = OWN_CELL  # 只读读数口（module/桩实例皆可设属性）

    def _own_copper_cell(grid, ctxi, find, comp, net, layer, x, y, maxr):
        """#K2-412 §四.3（D1「端点自身格」）：返回**最近的、格点仍落在本网自己铜上**的格 ——
        只对**端点格**忽略剪枝掩码（端点按构造就在本网铜上 ⇒ 其自身格按定义是合法起/止；异网障碍只是
        **保守地**把该格点剪掉了）。**C35 框在此处显式重加**（绝不因松绑而把起点放到框外）。
        确定性：限定 (2*maxr+1)^2 格，按 (半径, di, dj) 取最小；零参数搜索。
        放行闸 seg_exact/via_exact 与终检 DRC 一概不变 —— 本函数只让迷宫**能起步**。"""
        ci, cj = grid.cell(x, y)
        for r in range(maxr + 1):
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    if max(abs(di), abs(dj)) != r:
                        continue
                    i, j = ci + di, cj + dj
                    if not grid.inside(i, j):
                        continue
                    px, py = grid.pt(i, j)
                    if wall and not (wall[0] - 1e-9 <= px <= wall[2] + 1e-9
                                     and wall[1] - 1e-9 <= py <= wall[3] + 1e-9):
                        continue                       # C35：域外格一律不可选（松绑不越框）
                    if mr.node_in_island(ctxi, find, comp, net, layer, px, py):
                        return (i, j)
        return None

    def _lift_prune(grid, layer, cell):
        """#K2-412 §四.3(b)（承接 D1 的**决定性实锤**）：`astar` 对**被剪枝的起点/终点**直接回
        `start-blocked`（k2_p4_mroute_v1.py:397）—— 光让 `snap` 返回「端点自身铜格」还**不够**，
        该格若仍带剪枝位，迷宫照样不认。故把**这一格**的剪枝位**置零**（**只此一格**；邻格仍被剪 ⇒
        必须立刻走上自由格，首段仍由 seg_exact/via_exact 裁决）。确定性 · 零搜索 · 只在该格确为
        「端点自身铜」时发生（见 `_own_copper_cell` 的 `node_in_island` 前置）。"""
        bad = getattr(grid, "bad", None)
        if isinstance(bad, dict):
            arr = bad.get(layer)
            if arr is not None:
                i, j = cell
                arr[i * grid.ny + j] = 0

    def snap(grid, ctxi, find, comp, net, layer, x, y, maxr=4):
        r = orig_snap(grid, ctxi, find, comp, net, layer, x, y, maxr)
        if r is not None:
            return r
        # ① 端口点：允许**落在端口**（该格可能因邻近异网铜被剪枝）；**最终仍由放行闸 seg_exact/via_exact 判定**。
        if (round(x, 3), round(y, 3)) in PORT_PTS:
            i, j = grid.cell(x, y)
            if grid.inside(i, j):
                return i, j
        # ② #K2-412 §四.3（D1）：端点**就在本网铜上** ⇒ 其自身格按定义合法起/止。松绑**该格**的剪枝掩码
        #    （并把该位**置零**，否则 astar 仍以 `start-blocked` 拒），C35 框仍守（见 _own_copper_cell），
        #    放行闸/终检不改 —— 让迷宫**能起步**，非放水。
        if mr.node_in_island(ctxi, find, comp, net, layer, x, y):
            cell = _own_copper_cell(grid, ctxi, find, comp, net, layer, x, y, maxr)
            if cell is not None:
                _lift_prune(grid, layer, cell)
                OWN_CELL["hits"] += 1
                return cell
        return None

    def _ports(ctx, net):
        out = set()
        for t in ctx.tracks:
            if t.get("net") != net or t.get("layer") not in mr.LAYERS:
                continue
            for (X, Y) in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
                if (abs(X - wall[0]) < tol or abs(X - wall[2]) < tol
                        or abs(Y - wall[1]) < tol or abs(Y - wall[3]) < tol):
                    out.add((t["layer"], round(X, 4), round(Y, 4), t["uuid"]))
        for (pl, px, py, tpu) in sorted(out):
            PORT_PTS.add((round(px, 3), round(py, 3)))
        out2 = [(pl, px, py, "t:" + str(tpu)) for (pl, px, py, tpu) in sorted(out)]
        for (_n, _x, _y, _l) in getattr(mr, "_PORT_PADS", []):       # #K2-431 fix 1: connector pads as ports
            if _n == net:
                PORT_PTS.add((round(_x, 3), round(_y, 3)))
                out2.append((_l, _x, _y, "p:" + str(_x) + ":" + str(_y)))
        return out2

    mr.snap_node = snap

    REC = []

    def solve(ctx, find, compa, compb, net, la, pa, lb, pb, margin, coarse_step):
        _saved = getattr(mr, "WALL_RECT", None)
        _CH = getattr(mr, "_CHANNELS", {})                # NOTE: `CH` lives on `mr` because solve is defined in a
        coarse_step = float(getattr(mr, "FINE_STEP", coarse_step) or coarse_step) if _FINE else float(_FINE_NUM or coarse_step)
        h0 = OWN_CELL["hits"]
        if net in _CH:                                    # MODULE-LEVEL function (main()'s locals are NOT in scope)
            _c = _CH[net]
            _m = float(getattr(mr, "_CH_MARGIN", 0.5))
            sol, why = None, "no-attempt"
            for _w in (_m, _m * 2, _m * 4):               # BOUNDED deterministic ladder (not a search): a wider
                mr.WALL_RECT = (_c[0] - _w, _c[1] - _w, _c[2] + _w, _c[3] + _w)   # channel must not cut the net's
                sol, why = orig(ctx, find, compa, compb, net, la, pa, lb, pb, margin, coarse_step)   # reachable cell
                if sol is not None:
                    break
        else:
            sol, why = orig(ctx, find, compa, compb, net, la, pa, lb, pb, margin, coarse_step)
        mr.WALL_RECT = _saved
        if sol is not None:
            return sol, why
        rec = {"net": net, "why": why, "pa": [round(pa[0], 3), round(pa[1], 3)], "la": mr.LNAME[la],
               "pb": [round(pb[0], 3), round(pb[1], 3)], "lb": mr.LNAME[lb],
               "ports_available": len(_ports(ctx, net)), "ports_tried": 0, "reachable_port": False, "via": None,
               "endpoint_own_cell_hits": OWN_CELL["hits"] - h0}
        if why in ("no-free-start-node", "no-free-goal-node"):
            rec["tries"] = []
            for (pl, px, py, tpu) in _ports(ctx, net):
                rec["ports_tried"] += 1
                cport = find(tpu) if str(tpu).startswith("p:") else find("t:" + str(tpu))
                if cport is None:
                    continue
                s2, w2 = orig(ctx, find, compa, cport, net, la, pa, pl, (px, py), margin, coarse_step)
                rec["tries"].append({"port": [px, py, pl], "dir": "goal", "why": w2})
                if s2 is not None:
                    rec.update({"reachable_port": True, "via": [px, py, pl],
                                "endpoint_own_cell_hits": OWN_CELL["hits"] - h0})
                    REC.append(rec)
                    return s2, "ok-port-goal"
                s2, w3 = orig(ctx, find, cport, compb, net, pl, (px, py), lb, pb, margin, coarse_step)
                rec["tries"].append({"port": [px, py, pl], "dir": "start", "why": w3})
                if s2 is not None:
                    rec.update({"reachable_port": True, "via": [px, py, pl],
                                "endpoint_own_cell_hits": OWN_CELL["hits"] - h0})
                    REC.append(rec)
                    return s2, "ok-port-start"
        rec["endpoint_own_cell_hits"] = OWN_CELL["hits"] - h0
        REC.append(rec)
        mr.WALL_RECT = _saved
        return sol, why

    mr.solve_edge = solve
    return REC


def json_dumps(o):
    import json
    return json.dumps(o, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
