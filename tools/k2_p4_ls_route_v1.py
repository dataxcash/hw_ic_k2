#!/usr/bin/env python3
"""K2 · P4 收敛增量 —— 低速/电源 **F.Cu 局部通路（A*，阶段 F2）**：把剩余未连接边中「同层可达」的两端接上。

依据 owner 常设裁定 #14（**走廊/布线 = L2 自裁 · 勿停**）+ 《宪法》第四条（改板须 SPEC 留痕）。

范围（**声明边界，不静默放弃**）：只对**两端铜岛都在 F.Cu 有铜**且**直线距离 ≤ 20mm** 的边做
**同层 F.Cu 0/45/90° 通道搜索**（0.05mm 网格 A*，八方向；含「L 形接入」收尾，保证段角合法）。
净距 = net class max（PCIe85 0.175 / POWER 0.2 / LOW_SPEED 0.1，board_min 0.1）；板边铜 0.3；
禁 track 禁布区规避；线宽 0.200（= 板内既有低速/电源走线口径）；同网铜不视为障碍（需连接）。
**跨层 / 长距离（>20mm）的边不在本阶段范围**，逐条登记 `needs-cross-layer-router`，交后续布线增量。
复跑确定性：排序化 + 几何 uuid5 派生。判定权归监理，本器只交测量。
"""
from __future__ import annotations
import argparse, heapq, importlib.util, json, math, os, re, shutil, subprocess, sys
import pcbnew

_HERE = os.path.dirname(os.path.abspath(__file__))
def _load(name, fn):
    sp = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fn))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cv = _load("k2cv", "k2_p4_converge_v1.py")
f1 = _load("k2f1", "k2_p4_ls_local_v1.py")
MM, F_CU, B_CU = cv.MM, pcbnew.F_Cu, pcbnew.B_Cu
TRACE_W, STEP, MAXDIST, GOALBOX = 0.20, 0.05, 20.0, 2.0
MARGIN = 0.08          # 栅格量化安全余量（> 半格对角）


def blocked_set(m, net, x0, y0, x1, y1, holes, keep_t, edge):
    """把 (x0,y0)-(x1,y1) 包围盒内的**禁入格**（0.05mm 网格，格心=走线中心）写入 set。"""
    hw = TRACE_W / 2.0
    gx0, gy0 = math.floor((x0 - 1.0) / STEP), math.floor((y0 - 1.0) / STEP)
    gx1, gy1 = math.ceil((x1 + 1.0) / STEP), math.ceil((y1 + 1.0) / STEP)
    bad = set()
    def mark(cx, cy, rad):
        for i in range(math.floor((cx - rad) / STEP), math.ceil((cx + rad) / STEP) + 1):
            for j in range(math.floor((cy - rad) / STEP), math.ceil((cy + rad) / STEP) + 1):
                px, py = i * STEP, j * STEP
                if i < gx0 or i > gx1 or j < gy0 or j > gy1: continue
                if (px - cx) ** 2 + (py - cy) ** 2 <= rad * rad: bad.add((i, j))
    def mark_seg(ax, ay, bx, by, rad):
        for i in range(math.floor((min(ax, bx) - rad) / STEP), math.ceil((max(ax, bx) + rad) / STEP) + 1):
            for j in range(math.floor((min(ay, by) - rad) / STEP), math.ceil((max(ay, by) + rad) / STEP) + 1):
                px, py = i * STEP, j * STEP
                if i < gx0 or i > gx1 or j < gy0 or j > gy1: continue
                if cv.pt_seg_dist(px, py, ax, ay, bx, by) <= rad: bad.add((i, j))
    for t in m.tracks:
        if t["layer"] != F_CU or t["net"] == net: continue
        mark_seg(t["x1"], t["y1"], t["x2"], t["y2"], t["hw"] + hw + cv._req(net, t["net"]) + MARGIN)
    for p in m.pads.values():
        if not p["onF"] or p["net"] == net: continue
        r = hw + cv._req(net, p["net"]) + MARGIN
        if p["circ"]:
            mark(p["x"], p["y"], min(p["w"], p["h"]) / 2 + r)
        else:
            for k in range(len(p["poly"])):
                a, b = p["poly"][k], p["poly"][(k + 1) % len(p["poly"])]
                mark_seg(a[0], a[1], b[0], b[1], r)
            xa = [q[0] for q in p["poly"]]; ya = [q[1] for q in p["poly"]]
            for i in range(math.floor((min(xa) - r) / STEP), math.ceil((max(xa) + r) / STEP) + 1):
                for j in range(math.floor((min(ya) - r) / STEP), math.ceil((max(ya) + r) / STEP) + 1):
                    px, py = i * STEP, j * STEP
                    if cv.pt_in_poly(px, py, p["poly"]): bad.add((i, j))
    for v in m.vias.values():
        if not v["onF"] or v["net"] == net: continue
        # 盘净距 **与** 孔-铜 0.25 **取大**（孔规则无同网豁免，但同网此处已跳过）
        mark(v["x"], v["y"], max(v["r"] + hw + cv._req(net, v["net"]),
                                 v.get("hole_r", 0.1) + 0.25 + hw) + MARGIN)
    for (hx, hy, hr, hnet) in holes:
        if hnet == net: continue
        mark(hx, hy, hr + 0.25 + hw + MARGIN)
    for e in edge:
        mark_seg(e[0], e[1], e[2], e[3], hw + 0.3 + MARGIN)
    for poly in keep_t:                      # 禁 track 的禁布区：整块禁入
        xa = [p[0] for p in poly]; ya = [p[1] for p in poly]
        for i in range(math.floor(min(xa) / STEP), math.ceil(max(xa) / STEP) + 1):
            for j in range(math.floor(min(ya) / STEP), math.ceil(max(ya) / STEP) + 1):
                if cv.pt_in_poly(i * STEP, j * STEP, poly): bad.add((i, j))
    return bad, gx0, gx1, gy0, gy1


def exact_ok(m, holes, net, pts):
    """**精确**复核（不依赖栅格）：逐段与全部异网 F.Cu 铜 / 全部孔 / 板边 / 禁 track 禁布区比对。"""
    hw = TRACE_W / 2.0
    for k in range(len(pts) - 1):
        x1, y1 = pts[k]; x2, y2 = pts[k + 1]
        if math.hypot(x2 - x1, y2 - y1) < 0.001: continue
        for e in m.edge:
            if cv.seg_seg_dist(x1, y1, x2, y2, *e) < 0.3 + hw: return False
        for poly in m.keep_t:
            if cv.seg_poly_dist(x1, y1, x2, y2, poly) <= 0: return False
        for t in m.tracks:
            if t["layer"] != F_CU or t["net"] == net: continue
            if cv.seg_seg_dist(x1, y1, x2, y2, t["x1"], t["y1"], t["x2"], t["y2"]) < hw + t["hw"] + cv._req(net, t["net"]):
                return False
        for p in m.pads.values():
            if not p["onF"] or p["net"] == net: continue
            if p["circ"]:
                if cv.pt_seg_dist(p["x"], p["y"], x1, y1, x2, y2) - min(p["w"], p["h"]) / 2 < hw + cv._req(net, p["net"]):
                    return False
            else:
                if cv.seg_poly_dist(x1, y1, x2, y2, p["poly"]) < hw + cv._req(net, p["net"]):
                    return False
        for v in m.vias.values():
            if not v["onF"] or v["net"] == net: continue
            if cv.pt_seg_dist(v["x"], v["y"], x1, y1, x2, y2) - v["r"] < hw + cv._req(net, v["net"]):
                return False
        for (hx, hy, hr, hnet) in holes:            # 孔-铜 0.25（走线无孔，取中心距 >= hr+0.25+hw）
            if hnet == net: continue
            if cv.pt_seg_dist(hx, hy, x1, y1, x2, y2) < hr + 0.25 + hw:
                return False
    return True


def route(m, net, a, b, holes, keep_t, edge):
    """A*(F.Cu, 八方向, 0.05mm) 从 a 到 b 附近，再以 L 形接入 b。返回折线点列或 None。"""
    hw = TRACE_W / 2.0
    bad, gx0, gx1, gy0, gy1 = blocked_set(m, net, a[0], a[1], b[0], b[1], holes, keep_t, edge)
    def seg_clear(x1, y1, x2, y2):
        ln = math.hypot(x2 - x1, y2 - y1)
        n = max(2, int(ln / (STEP / 2)) + 1)
        for k in range(n + 1):
            t = k / n
            i = int(round((x1 + (x2 - x1) * t) / STEP)); j = int(round((y1 + (y2 - y1) * t) / STEP))
            if (i, j) in bad: return False
        return True
    def goal_connector(x, y):
        for cx, cy in ((x, b[1]), (b[0], y)):
            if seg_clear(x, y, cx, cy) and seg_clear(cx, cy, b[0], b[1]):
                return [(cx, cy)]
        return None
    i0, j0 = int(round(a[0] / STEP)), int(round(a[1] / STEP))
    start = (i0, j0)
    if start in bad: return None
    gi, gj = b[0] / STEP, b[1] / STEP
    def h(i, j): return max(abs(i - gi), abs(j - gj)) * STEP * math.sqrt(2)
    DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    openq = [(h(i0, j0), 0.0, start)]
    gscore = {start: 0.0}
    came = {start: None}
    popped = 0
    while openq:
        f, g, cur = heapq.heappop(openq)
        if g > gscore.get(cur, 1e18) + 1e-9: continue
        popped += 1
        if popped > 400000: return None
        x, y = cur[0] * STEP, cur[1] * STEP
        conn = goal_connector(x, y)
        if conn is not None:
            path = []
            n = cur
            while n is not None:
                path.append(n); n = came[n]
            path.reverse()
            pts = [(p[0] * STEP, p[1] * STEP) for p in path]
            return pts + [c for c in conn] + [(b[0], b[1])]
        for dx, dy in DIRS:
            nx, ny = cur[0] + dx, cur[1] + dy
            if nx < gx0 or nx > gx1 or ny < gy0 or ny > gy1: continue
            if (nx, ny) in bad: continue
            ng = g + STEP * (math.sqrt(2) if dx and dy else 1.0)
            if ng < gscore.get((nx, ny), 1e18) - 1e-9:
                gscore[(nx, ny)] = ng; came[(nx, ny)] = cur
                heapq.heappush(openq, (ng + h(nx, ny), ng, (nx, ny)))
    return None


def simplify(pts):
    """合并同向连续步进 → 行走线折线（保持 0/45/90°）。"""
    out = [pts[0]]
    for k in range(1, len(pts)):
        out.append(pts[k])
        while len(out) >= 3:
            (x0, y0), (x1, y1), (x2, y2) = out[-3], out[-2], out[-1]
            v1 = (round(x1 - x0, 6), round(y1 - y0, 6)); v2 = (round(x2 - x1, 6), round(y2 - y1, 6))
            if v1[0] * v2[1] == v1[1] * v2[0] and (v1[0] * v2[0] + v1[1] * v2[1]) > 0:
                out.pop(-2)
            else:
                break
    return out


def run(src, drc_path, out_path, ledger_path):
    b = pcbnew.LoadBoard(src)
    m = f1.M(b)
    holes = []
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            pos = t.GetPosition()
            u = t.m_Uuid.AsString()
            if u in m.vias:
                m.vias[u]["hole_r"] = MM(t.GetDrillValue()) / 2.0
    for u, v in m.vias.items():
        holes.append((v["x"], v["y"], v.get("hole_r", 0.1), v["net"]))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            dz = p.GetDrillSize()
            if dz.x > 0:
                pos = p.GetPosition()
                holes.append((MM(pos.x), MM(pos.y), MM(dz.x) / 2.0, p.GetNetname()))
    find = f1.islands(m)
    drc = json.load(open(drc_path, encoding="utf-8"))
    def locate(uu):
        if uu in m.pads: return "p:" + uu, m.pads[uu]["net"]
        if uu in m.vias: return "v:" + uu, m.vias[uu]["net"]
        for t in m.tracks:
            if t["uuid"] == uu: return "t:" + uu, t["net"]
        return None, None
    def ports_of(comp):
        out = []
        for u, p in m.pads.items():
            if find("p:" + u) == comp and p["onF"]: out.append((p["x"], p["y"]))
        for t in m.tracks:
            if find("t:" + t["uuid"]) == comp and t["layer"] == F_CU: out += [(t["x1"], t["y1"]), (t["x2"], t["y2"])]
        for u, v in m.vias.items():
            if find("v:" + u) == comp and v["onF"]: out.append((v["x"], v["y"]))
        return sorted(set(out))
    edges = []
    for e in drc.get("unconnected_items", []):
        its = e.get("items", [])
        if len(its) != 2: continue
        (ka, na), (kb, nb) = locate(its[0]["uuid"]), locate(its[1]["uuid"])
        if not ka or not kb or na != nb or not na: continue
        d = math.hypot(its[0]["pos"]["x"] - its[1]["pos"]["x"], its[0]["pos"]["y"] - its[1]["pos"]["y"])
        edges.append((round(d, 3), na, ka, kb))
    edges.sort()
    added, blocked, blocks = [], [], []
    for dist, net, ka, kb in edges:
        ca, cb = find(ka), find(kb)
        if ca == cb: continue
        if dist > MAXDIST:
            blocked.append({"net": net, "dist": dist, "why": "needs-cross-layer-router"}); continue
        pa, pb = ports_of(ca), ports_of(cb)
        if not pa or not pb:
            blocked.append({"net": net, "dist": dist, "why": "no-fcu-port"}); continue
        cands = sorted(((math.hypot(x1 - x2, y1 - y2), (x1, y1), (x2, y2)) for (x1, y1) in pa for (x2, y2) in pb))[:4]
        done = False
        for _, a, bs in cands:
            pts = route(m, net, a, bs, holes, m.keep_t, m.edge)
            if not pts: continue
            pts = simplify(pts)
            if not exact_ok(m, holes, net, pts):
                continue
            for k in range(len(pts) - 1):
                x1, y1, x2, y2 = pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]
                if math.hypot(x2 - x1, y2 - y1) < 0.001: continue
                blocks.append(f1.SEG_BLOCK.format(x1=f1._fmt(x1), y1=f1._fmt(y1), x2=f1._fmt(x2), y2=f1._fmt(y2),
                                                  layer="F.Cu", net=net, u=f1.seg_uuid(net, "F.Cu", x1, y1, x2, y2)))
                m.tracks.append(dict(uuid=f1.seg_uuid(net, "F.Cu", x1, y1, x2, y2), net=net, layer=F_CU,
                                     x1=x1, y1=y1, x2=x2, y2=y2, hw=TRACE_W / 2))
            added.append({"net": net, "dist": dist, "legs": len(pts) - 1, "a": [round(a[0], 3), round(a[1], 3)],
                          "b": [round(bs[0], 3), round(bs[1], 3)]})
            done = True
            break
        if not done:
            blocked.append({"net": net, "dist": dist, "why": "no-legal-path-in-fcu"})
    led = {"stage": "F2", "edges": len(edges), "added": added, "blocked": blocked,
           "F2_summary": {"added": len(added), "blocked": len(blocked),
                          "reasons": {k: sum(1 for x in blocked if x["why"] == k) for k in sorted({x["why"] for x in blocked})}}}
    json.dump(led, open(ledger_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if blocks:
        txt = open(src, encoding="utf-8").read()
        anchor = txt.index("\t(segment\n")
        tmp = out_path + ".f2_tmp.kicad_pcb"
        open(tmp, "w", encoding="utf-8").write(txt[:anchor] + "".join(blocks) + txt[anchor:])
        src_pro = re.sub(r"\.kicad_pcb$", ".kicad_pro", src)
        if os.path.exists(src_pro):
            shutil.copyfile(src_pro, re.sub(r"\.kicad_pcb$", ".kicad_pro", tmp))
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--fill", tmp, out_path], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("fill failed rc=%d %s" % (r.returncode, r.stderr[-300:]))
        if os.path.exists(src_pro):
            shutil.copyfile(src_pro, re.sub(r"\.kicad_pcb$", ".kicad_pro", out_path))
        os.remove(tmp)
    else:
        shutil.copyfile(src, out_path)
    return led["F2_summary"]


def _fill(tmp, out_path):
    b2 = pcbnew.LoadBoard(tmp)
    if b2 is None:
        raise SystemExit("_fill: LoadBoard -> None")
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    b2.Save(out_path)
    print(json.dumps({"fill": "ok"}))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="K2 P4 阶段 F2：低速/电源 F.Cu 局部通路（A*）")
    ap.add_argument("--fill", nargs=2, metavar=("TMP", "OUT"))
    ap.add_argument("--in", dest="src"); ap.add_argument("--drc"); ap.add_argument("--out"); ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    if a.fill:
        return _fill(a.fill[0], a.fill[1])
    if not (a.src and a.drc and a.out and a.ledger):
        ap.error("--in/--drc/--out/--ledger 必填")
    print(json.dumps(run(a.src, a.drc, a.out, a.ledger), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
