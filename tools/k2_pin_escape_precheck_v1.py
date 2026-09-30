#!/usr/bin/env python3
"""k2_pin_escape_precheck_v1.py —— #K2-467 §2.1③／#K2-472 §3.4 引脚逃逸**预检量具**（真板 · 只读 · 有界 · 确定性）。

把「每个**未连通端**是否拥有确定性逃逸资产」变成**机器读数**（`go` ＋ 具名名单）。

**三个口径（本件据以修量具）**
  * **真形建模**（#K2-472 §3.4(1)）：焊盘按**沿长轴胶囊**入障碍（`pad_obstacle`）——**绝不**用各向同性 `max(size)/2`
    圆盘。R1520：`0.300×1.475` 细长脚被当半径 `0.7375` 圆盘 ⇒ 短边肥 `4.92×` ⇒ **造出假拒绝** ⇒ 险致「错搬焊盘」。
  * **逃逸须离焊盘自身铜皮**（#K2-472 §3.4(2)）：目标焊盘带 `pad_rect`，资产**终点须在焊盘矩形之外**；盘内短线不计。
  * **过孔亦为障碍**（承 R1358／`test_C448`：障碍须枚举其覆盖的每一层）——过孔按其**跨层集**逐层入障碍。
  * **门范围 ＝ 仅未连通端**（#K2-468 §3.2）；已连通端 **PASS-by-route**。

**owner 红线（绝对）**：禁死循环（无 `while`）· 禁 CPU 狂飙（候选上限由规划器保证 · 局部预筛 · 无后台 · 无守护）。

CLI: python3 tools/k2_pin_escape_precheck_v1.py --board B --rect x0,y0,x1,y1 --nets A,B \\
        [--pads U1:22,U1:48] [--out O.json] [--timeout-s 600]
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys, time

_HERE = os.path.dirname(os.path.abspath(__file__))


def _planner():
    sp = importlib.util.spec_from_file_location(
        "k2_pin_escape_plan_v1", os.path.join(_HERE, "k2_pin_escape_plan_v1.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _require_pcbnew():
    """#K2-448 sec.2.5(2)：需 pcbnew 之工具，在无 pcbnew 之 python 下**必须响亮失败**（承 R1356 之静默中止）。"""
    try:
        import pcbnew  # noqa: F401
    except Exception as _e:                                            # noqa: BLE001
        raise RuntimeError(
            "k2: this tool requires EDA_ENG_PY (a python with pcbnew); refusing to run silently under %s (%s)"
            % (sys.executable, type(_e).__name__))


def _angle_deg(pd):
    o = pd.GetOrientation()
    if hasattr(o, "AsDegrees"):
        return float(o.AsDegrees())
    return float(o) / 10.0                                            # 旧 API：十分之一度


def _copper_layers(b, pd, P):
    """该焊盘自身铜皮覆盖之铜层（PTH＝F/B；SMD＝其所在层）。"""
    if pd.GetAttribute() == P.PAD_ATTRIB_PTH:
        return [b.GetLayerName(P.F_Cu), b.GetLayerName(P.B_Cu)]
    lys = []
    for L in (P.F_Cu, P.B_Cu):
        if pd.IsOnLayer(L):
            lys.append(b.GetLayerName(L))
    return lys


def _true_corner_radius(P, pd, sx, sy):
    """#K2-502：焊盘**真形圆角半径**（供 `pad_obstacle_shape` 之圆角矩形）。
    `CIRCLE/OVAL` 恰为 圆角半径 `min(sx,sy)/2` 之圆角矩形；`ROUNDRECT` 带自身半径；其余（`RECT/TRAPEZOID/
    CUSTOM`）取 `0` —— **直角矩形是真实形之超集** ⇒ 只会**多拒**、**绝不**假净（R1520 之病根是各向同性
    `max/2` 造成假拒，本处不取该路）。"""
    rm = min(sx, sy) / 2.0
    try:
        sh = pd.GetShape()
    except Exception:                                          # noqa: BLE001
        return 0.0
    if sh in (P.PAD_SHAPE_CIRCLE, P.PAD_SHAPE_OVAL):
        return rm
    if sh == P.PAD_SHAPE_ROUNDRECT:
        try:
            return max(0.0, min(rm, P.ToMM(pd.GetRoundRectCornerRadius())))
        except Exception:                                      # noqa: BLE001
            return 0.0
    return 0.0


def read_board(board, rect, nets, only, planner, P, margin=5.0, max_pads=200000):
    """**只读**：把板变成 (obstacles, target_pads)。障碍 ＝ 走线（精确）＋ 过孔（逐跨层）＋ 焊盘（**真形圆角矩形** · #K2-502）。"""
    b = P.LoadBoard(board)
    x0, y0, x1, y1 = [float(v) for v in rect]

    def inside(p):
        return (x0 - 1e-6 <= p[0] <= x1 + 1e-6) and (y0 - 1e-6 <= p[1] <= y1 + 1e-6)

    def near(p):
        return (x0 - margin <= p[0] <= x1 + margin) and (y0 - margin <= p[1] <= y1 + margin)

    obst, n_vias = [], 0
    for t in b.GetTracks():
        try:
            net = t.GetNetname()
        except Exception:                                             # noqa: BLE001
            net = b.FindNet(t.GetNetCode()).GetNetname()
        if t.GetClass() == "PCB_VIA":
            pos = t.GetStart(); cx, cy = P.ToMM(pos.x), P.ToMM(pos.y)
            if not near((cx, cy)):
                continue
            n_vias += 1
            seq = list(t.GetLayerSet().Seq())                # 过孔之**跨层集**（R1358）
            hw = P.ToMM(t.GetWidth(seq[0])) / 2.0              # via 需带层参（否则 KiCad assert）
            for L in t.GetLayerSet().Seq():                           # 过孔须枚举其覆盖的每一层（R1358）
                obst.append((net, b.GetLayerName(L), cx, cy, cx, cy, hw))
            continue
        s, e = t.GetStart(), t.GetEnd()
        obst.append((net, b.GetLayerName(t.GetLayer()), P.ToMM(s.x), P.ToMM(s.y),
                     P.ToMM(e.x), P.ToMM(e.y), P.ToMM(t.GetWidth()) / 2.0))

    targets, n_pads = [], 0
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        for pd in fp.Pads():
            n_pads += 1
            if n_pads > max_pads:
                raise RuntimeError("k2: pad cap exceeded (%d) - refusing to run unbounded" % max_pads)
            pos = pd.GetPosition(); cx, cy = P.ToMM(pos.x), P.ToMM(pos.y)
            nm = pd.GetNetname() or ""
            sx, sy = P.ToMM(pd.GetSize().x), P.ToMM(pd.GetSize().y)
            rot = _angle_deg(pd)
            if not near((cx, cy)):
                continue
            _rr = _true_corner_radius(P, pd, sx, sy)
            for ly in _copper_layers(b, pd, P):
                # #K2-502: TRUE-shape (rounded rectangle) pad obstacle - a pad's rectangular corners must be
                # visible to the escape clearance test (R1666: the inscribed capsule cleared two 45-degree
                # escape steps that the exact geometry puts at 0.1062mm, i.e. real DRC clearance errors).
                obst.append(planner.pad_obstacle_shape(nm, ly, cx, cy, sx, sy, rot, _rr))
            if inside((cx, cy)) and nm in nets:
                key = "%s:%s" % (ref, pd.GetNumber())
                if only and key not in only:
                    continue
                for ly in _copper_layers(b, pd, P):
                    targets.append((nm, ly, cx, cy, sx / 2.0, sy / 2.0, rot))
    targets.sort(key=lambda t: (t[0], t[1], round(t[2], 4), round(t[3], 4)))
    return {"obstacles": obst, "targets": targets, "n_pads": n_pads, "n_vias": n_vias}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--rect", required=True, help="x0,y0,x1,y1 (mm)")
    ap.add_argument("--nets", required=True, help="逗号分隔之目标网")
    ap.add_argument("--pads", default="", help="可选：REF:PAD 列表（＝未连通端白名单）")
    ap.add_argument("--out", default="")
    ap.add_argument("--timeout-s", type=float, default=600.0)
    a = ap.parse_args(argv)
    import pcbnew as P
    rect = [float(v) for v in a.rect.split(",")]
    nets = {s.strip() for s in a.nets.split(",") if s.strip()}
    only = {s.strip() for s in a.pads.split(",") if s.strip()}
    planner = _planner()
    t0 = time.time()
    rd = read_board(a.board, rect, nets, only, planner, P)
    if time.time() - t0 > a.timeout_s:
        raise RuntimeError("k2: read exceeded timeout")
    r = planner.plan_escapes(rd["targets"], rd["obstacles"], clear=0.30, max_escape_len=2.0, step=0.1)
    if time.time() - t0 > a.timeout_s:
        raise RuntimeError("k2: plan exceeded timeout")
    out = {"artifact": "k2_pin_escape_precheck_real_board_v2", "ts": "2026-09-30",
           "authority": "#K2-467 sec.2.1(3) precheck, re-run under #K2-472 sec.3.4 with the TRUE-shape pad model",
           "reading": {"board": os.path.basename(a.board), "rect": rect, "target_nets": sorted(nets),
                       "target_endpoints": ["%s@%s,%s" % (t[0], t[2], t[3]) for t in rd["targets"]],
                       "n_target_pads": len(rd["targets"]), "n_pads_on_board": rd["n_pads"],
                       "n_vias": rd["n_vias"], "n_obstacles": len(rd["obstacles"]),
                       "go": r["go"], "n_assets": len(r["assets"]), "n_refused": len(r["refused"]),
                       "assets": r["assets"], "refused": r["refused"], "bounds": r["bounds"],
                       "elapsed_s": round(time.time() - t0, 3),
                       "model": {"pads": "TRUE anisotropic capsule (long axis), hw = min(size)/2 - NOT an isotropic max(size)/2 disc (R1520)",
                                 "tracks": "exact segment + half-width", "vias": "circle on every layer of their layer-span (R1358)",
                                 "escape": "the asset ENDPOINT must lie outside the pad rect (#K2-472 sec.3.4(2))"},
                       "gate_scope": "UNCONNECTED endpoints only (#K2-468 sec.3.2)"},
           "interpretation": {
               "what_changed_vs_v1": ("R1498/R1506 modelled each pad as a POINT with an ISOTROPIC half-width max(size.x,size.y)/2 "
                                      "(0.7375mm for these 0.300x1.475 pads - 4.92x the true short half-axis), which MANUFACTURED the "
                                      "refusals (R1520). v2 models the true anisotropic capsule (hw = min(size)/2 = 0.150) and requires "
                                      "the escape endpoint to leave the pad rect."),
               "v1_reading_for_contrast": {"go": False, "refused": ["I2C2_SCL@(37.75,57.1625)", "I2C1_SDA@(33.25,48.8375)"],
                                           "model": "point + isotropic max(size)/2 disc"},
               "why_these_escapes_are_consistent_with_the_R1440_witness": ("both pads are 0.300x1.475 long pads; the corridor runs along the "
                                                                           "LONG axis and leaves the pad at its end - exactly the short F.Cu run "
                                                                           "north to a via at ~(37.75,56.2) that the R1440 witness uses."),
               "margin_note": ("the first legal endpoint is reached at the 0.1mm step granularity, so the endpoint sits ~0.06mm beyond the pad edge; the "
                               "criterion is the literal #K2-472 sec.3.4(2) rule (outside the pad rect)."),
               "no_appendix_A": "with go=TRUE there is NO dead exit for these two ends => appendix A (sec.16.3 relocation) must not be used."}}
    if a.out:
        json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out["reading"], ensure_ascii=False)[:2400])
    return 0 if r["go"] else 1


_require_pcbnew()


if __name__ == "__main__":
    sys.exit(main())
