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
import argparse, importlib.util, os, sys

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
    a = ap.parse_args()
    sp = importlib.util.spec_from_file_location("k2mrfloor", MROUTE)
    mr = importlib.util.module_from_spec(sp); sp.loader.exec_module(mr)
    cv = mr.cv
    orig = cv._req
    cv._req = lambda x, y: max(orig(x, y), a.floor)
    if a.bound_rect:                                  # C35：把域作为**搜索约束**注入（不改迷宫本体）
        mr.WALL_RECT = tuple(float(v) for v in a.bound_rect.split(","))
    # ── #K2-392 第三边：**端口感知目标（port-aware goals）** ────────────────────────────
    # 端点「无空闲起止位」（no-free-start/goal-node）多因该端点落在**框外**（框被 C35 封死），
    # 迷宫在界内找不到属于该岛的格。处置：把**框切残段端口**（∂R 上、同网的 track 端点）当**目标**，
    # 把「跨框另猜目标」改成「接回该网在 ∂R 的端口」——同网铜在框外继续，故接到端口即恢复连通。
    # **不改迷宫本体**：运行期在 wrapper 内给 `mr.solve_edge` 打补丁（与 `cv._req`/`WALL_RECT` 同法）。
    if mr.WALL_RECT:
        _install_port_aware_goals(mr, tuple(mr.WALL_RECT))
    s = mr.run(a.src, a.drc, a.out, a.ledger, a.margin, a.only_net, a.dry_run, "dist_asc", None)
    print(json_dumps(s))
    return 0


def _install_port_aware_goals(mr, wall, tol=0.02):
    """把 `solve_edge` 包一层：正常失败且原因为 no-free-start/goal-node 时，改用**同网 ∂R 端口**
    （作为目标或起点）重试一次。确定性（端口按 (layer,x,y,uuid) 排序）；不搜索、不调参。"""
    orig = mr.solve_edge
    orig_snap = mr.snap_node
    PORT_PTS = set()

    def snap(grid, ctx2, find, comp, net, layer, x, y, maxr=4):
        r = orig_snap(grid, ctx2, find, comp, net, layer, x, y, maxr)
        if r is not None:
            return r
        # 端口点：允许**落在端口**（该格可能因邻近异网铜被剪枝）；**最终仍由放行闸 seg_exact/via_exact 判定**。
        if (round(x, 3), round(y, 3)) in PORT_PTS:
            i, j = grid.cell(x, y)
            if grid.inside(i, j):
                return i, j
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
        return sorted(out)

    mr.snap_node = snap

    def solve(ctx, find, compa, compb, net, la, pa, lb, pb, margin, coarse_step):
        sol, why = orig(ctx, find, compa, compb, net, la, pa, lb, pb, margin, coarse_step)
        if sol is not None or why not in ("no-free-start-node", "no-free-goal-node"):
            return sol, why
        for (pl, px, py, tpu) in _ports(ctx, net):
            cport = find("t:" + tpu)
            s2, _ = orig(ctx, find, compa, cport, net, la, pa, pl, (px, py), margin, coarse_step)
            if s2 is not None:
                return s2, "ok-port-goal"
            s2, _ = orig(ctx, find, cport, compb, net, pl, (px, py), lb, pb, margin, coarse_step)
            if s2 is not None:
                return s2, "ok-port-start"
        return sol, why

    mr.solve_edge = solve


def json_dumps(o):
    import json
    return json.dumps(o, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
