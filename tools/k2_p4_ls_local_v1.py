#!/usr/bin/env python3
"""K2 · P4 收敛增量 —— 低速/电源**局部闭合**（阶段 F1）：把 DRC 未连接的两端「就近」接上。

依据 owner 常设裁定 #14（**走廊/布线 = L2 自裁 · 勿停**）+ 《宪法》第四条（改板须 SPEC 留痕）。

口径（与 `_shared/eda_core/drc_rules.json` 一致，**不放松任何下限**）：
- 只做**局部**连接：对每个 DRC 未连接边，取两端**铜岛**上最近的可用点，试
  ① 同层 F.Cu 0/45/90° 直连；② 两端铜岛**都已在 B.Cu 有铜**（既有跨层过孔 / 插件孔）时，B.Cu 直连。
- 净距 = net class max（PCIe85 0.175 / POWER 0.2 / LOW_SPEED 0.1，board_min 0.1）；板边铜 0.3；
  禁 track 的禁布区规避；线宽 0.200（与板内既有低速/电源走线同）。
- 纯增；线宽/层沿用板内既有口径；新段一律 0/45/90° 且单腿 ≥0.05。
- **长距离/需跨层落孔的边不在此器范围**（登记 `needs-via-router`，交后续布线增量）。
复跑确定性：排序化 + 几何 uuid5 派生。判定权归监理，本器只交测量。
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, re, shutil, subprocess, sys, uuid
import pcbnew

_HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("k2cv", os.path.join(_HERE, "k2_p4_converge_v1.py"))
cv = importlib.util.module_from_spec(_s); _s.loader.exec_module(cv)
MM = cv.MM
F_CU, B_CU = pcbnew.F_Cu, pcbnew.B_Cu
TRACE_W = 0.20
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
SEG_BLOCK = ('\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width 0.2)\n'
             '\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')


def _fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def seg_uuid(net, layer, x1, y1, x2, y2):
    return str(uuid.uuid5(NS, "k2p4ls|seg|%s|%s|%s|%s|%s|%s" % (net, layer, _fmt(x1), _fmt(y1), _fmt(x2), _fmt(y2))))


class M:
    def __init__(self, b):
        self.pads, self.tracks, self.vias = {}, [], {}
        for fp in b.GetFootprints():
            for p in fp.Pads():
                ls = p.GetLayerSet(); pos, sz = p.GetPosition(), p.GetSize()
                circ = p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
                self.pads[p.m_Uuid.AsString()] = dict(
                    ref=fp.GetReference(), num=p.GetNumber(), net=p.GetNetname(), x=MM(pos.x), y=MM(pos.y),
                    w=MM(sz.x), h=MM(sz.y), circ=circ, onF=ls.Contains(F_CU), onB=ls.Contains(B_CU),
                    poly=None if circ else cv.rect_corners(MM(pos.x), MM(pos.y), MM(sz.x), MM(sz.y), p.GetOrientationDegrees()))
        for t in b.GetTracks():
            u = t.m_Uuid.AsString()
            if isinstance(t, pcbnew.PCB_VIA):
                pos = t.GetPosition(); ls = t.GetLayerSet()
                self.vias[u] = dict(net=t.GetNetname(), x=MM(pos.x), y=MM(pos.y), r=MM(t.GetWidth(F_CU)) / 2,
                                    onF=ls.Contains(F_CU), onB=ls.Contains(B_CU))
            else:
                s, e = t.GetStart(), t.GetEnd()
                self.tracks.append(dict(uuid=u, net=t.GetNetname(), layer=t.GetLayer(), x1=MM(s.x), y1=MM(s.y),
                                        x2=MM(e.x), y2=MM(e.y), hw=MM(t.GetWidth()) / 2))
        self.keep_t = []
        for z in b.Zones():
            if not z.GetIsRuleArea() or not z.GetDoNotAllowTracks():
                continue
            for i in range(z.Outline().OutlineCount()):
                ch = z.Outline().Outline(i)
                self.keep_t.append([(MM(ch.CPoint(k).x), MM(ch.CPoint(k).y)) for k in range(ch.PointCount())])
        self.edge = []
        for d in b.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts and hasattr(d, "GetStart"):
                s, e = d.GetStart(), d.GetEnd()
                self.edge.append((MM(s.x), MM(s.y), MM(e.x), MM(e.y)))

    def seg_ok(self, layer, net, x1, y1, x2, y2, hw):
        for e in self.edge:
            if cv.seg_seg_dist(x1, y1, x2, y2, *e) < 0.3 + hw:
                return False
        for poly in self.keep_t:
            if cv.seg_poly_dist(x1, y1, x2, y2, poly) <= 0:
                return False
        for t in self.tracks:
            if t["layer"] != layer or t["net"] == net:
                continue
            if cv.seg_seg_dist(x1, y1, x2, y2, t["x1"], t["y1"], t["x2"], t["y2"]) < hw + t["hw"] + cv._req(net, t["net"]):
                return False
        for p in self.pads.values():
            on = p["onF"] if layer == F_CU else p["onB"]
            if not on or p["net"] == net:
                continue
            need = hw + cv._req(net, p["net"])
            if p["circ"]:
                if cv.pt_seg_dist(p["x"], p["y"], x1, y1, x2, y2) - min(p["w"], p["h"]) / 2 < need:
                    return False
            elif cv.seg_poly_dist(x1, y1, x2, y2, p["poly"]) < need:
                return False
        for v in self.vias.values():
            on = v["onF"] if layer == F_CU else v["onB"]
            if not on or v["net"] == net:
                continue
            if cv.pt_seg_dist(v["x"], v["y"], x1, y1, x2, y2) - v["r"] < hw + cv._req(net, v["net"]):
                return False
        return True


def islands(m):
    parent = {}
    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def uni(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    for u in m.pads: find("p:" + u)
    for t in m.tracks: find("t:" + t["uuid"])
    for u in m.vias: find("v:" + u)
    for t in m.tracks:
        for u, p in m.pads.items():
            if p["net"] != t["net"]:
                continue
            on = p["onF"] if t["layer"] == F_CU else p["onB"]
            if not on:
                continue
            if cv.pt_seg_dist(p["x"], p["y"], t["x1"], t["y1"], t["x2"], t["y2"]) <= t["hw"] + max(p["w"], p["h"]) / 2 + 0.02:
                uni("p:" + u, "t:" + t["uuid"])
        for u, v in m.vias.items():
            if v["net"] != t["net"]:
                continue
            on = v["onF"] if t["layer"] == F_CU else v["onB"]
            if not on:
                continue
            if cv.pt_seg_dist(v["x"], v["y"], t["x1"], t["y1"], t["x2"], t["y2"]) <= t["hw"] + v["r"] + 0.02:
                uni("v:" + u, "t:" + t["uuid"])
    for i, t in enumerate(m.tracks):
        for s in m.tracks[i + 1:]:
            if s["net"] != t["net"] or s["layer"] != t["layer"]:
                continue
            et = ((t["x1"], t["y1"]), (t["x2"], t["y2"]))
            es = ((s["x1"], s["y1"]), (s["x2"], s["y2"]))
            if any(abs(a[0] - b[0]) <= 0.02 and abs(a[1] - b[1]) <= 0.02 for a in et for b in es):
                uni("t:" + t["uuid"], "t:" + s["uuid"])
    for u, v in m.vias.items():
        for x, p in m.pads.items():
            if p["net"] != v["net"]:
                continue
            on = v["onF"] and p["onF"] or v["onB"] and p["onB"]
            if not on:
                continue
            if math.hypot(v["x"] - p["x"], v["y"] - p["y"]) - max(p["w"], p["h"]) / 2 <= v["r"] + 0.02:
                uni("v:" + u, "p:" + x)
    return find


def run(src, drc_path, out_path, ledger_path):
    b = pcbnew.LoadBoard(src)
    m = M(b)
    find = islands(m)
    drc = json.load(open(drc_path, encoding="utf-8"))
    def layers_of(comp):
        L = set()
        for u, p in m.pads.items():
            if find("p:" + u) == comp:
                if p["onF"]: L.add(F_CU)
                if p["onB"]: L.add(B_CU)
        for t in m.tracks:
            if find("t:" + t["uuid"]) == comp: L.add(t["layer"])
        for u, v in m.vias.items():
            if find("v:" + u) == comp:
                if v["onF"]: L.add(F_CU)
                if v["onB"]: L.add(B_CU)
        return L
    def ports_of(comp, layer):
        """该铜岛在**指定层**上的可用接点（必须该层真有铜，否则会出 track_dangling）"""
        out = []
        for u, p in m.pads.items():
            if find("p:" + u) != comp: continue
            if (p["onF"] if layer == F_CU else p["onB"]): out.append((p["x"], p["y"]))
        for t in m.tracks:
            if find("t:" + t["uuid"]) == comp and t["layer"] == layer:
                out += [(t["x1"], t["y1"]), (t["x2"], t["y2"])]
        for u, v in m.vias.items():
            if find("v:" + u) != comp: continue
            if (v["onF"] if layer == F_CU else v["onB"]): out.append((v["x"], v["y"]))
        return sorted(set(out))
    def locate(uu):
        if uu in m.pads: return "p:" + uu, m.pads[uu]["net"]
        if uu in m.vias: return "v:" + uu, m.vias[uu]["net"]
        for t in m.tracks:
            if t["uuid"] == uu: return "t:" + uu, t["net"]
        return None, None
    edges = []
    for e in drc.get("unconnected_items", []):
        its = e.get("items", [])
        if len(its) != 2: continue
        (ka, na), (kb, nb) = locate(its[0]["uuid"]), locate(its[1]["uuid"])
        if not ka or not kb or na != nb or not na: continue
        dist = math.hypot(its[0]["pos"]["x"] - its[1]["pos"]["x"], its[0]["pos"]["y"] - its[1]["pos"]["y"])
        edges.append((round(dist, 3), na, ka, kb))
    edges.sort()
    added, blocked, blocks = [], [], []
    for dist, net, ka, kb in edges:
        ca, cb = find(ka), find(kb)
        if ca == cb: continue                       # 已被本轮或既有铜连通
        La, Lb = layers_of(ca), layers_of(cb)
        done = False
        for layer in (F_CU, B_CU):
            if done or layer not in La or layer not in Lb: continue
            pa, pb = ports_of(ca, layer), ports_of(cb, layer)
            if not pa or not pb: continue
            cands = sorted(((math.hypot(x1 - x2, y1 - y2), (x1, y1), (x2, y2)) for (x1, y1) in pa for (x2, y2) in pb))[:6]
            for _, (x1, y1), (x2, y2) in cands:
                for pp in cv._paths45((x1, y1), (x2, y2)):
                    if not all(m.seg_ok(layer, net, pp[i][0], pp[i][1], pp[i + 1][0], pp[i + 1][1], TRACE_W / 2)
                               for i in range(len(pp) - 1)):
                        continue
                    for i in range(len(pp) - 1):
                        x1_, y1_, x2_, y2_ = pp[i][0], pp[i][1], pp[i + 1][0], pp[i + 1][1]
                        ln = pcbnew.LayerName(layer)
                        blocks.append(SEG_BLOCK.format(x1=_fmt(x1_), y1=_fmt(y1_), x2=_fmt(x2_), y2=_fmt(y2_),
                                                       layer=ln, net=net, u=seg_uuid(net, ln, x1_, y1_, x2_, y2_)))
                        m.tracks.append(dict(uuid=seg_uuid(net, ln, x1_, y1_, x2_, y2_), net=net, layer=layer,
                                             x1=x1_, y1=y1_, x2=x2_, y2=y2_, hw=TRACE_W / 2))
                    added.append({"net": net, "layer": pcbnew.LayerName(layer), "dist": dist, "legs": len(pp) - 1,
                                  "a": [round(x1, 3), round(y1, 3)], "b": [round(x2, 3), round(y2, 3)]})
                    done = True
                    break
                if done: break
        if not done:
            # 本阶段的**声明边界**：只做两端铜岛间的**短程 0/45/90° 直连**（≤2 腿）；
            # 长距离 / 需在 IC 侧落孔再换层的边 = 后续布线增量（登记，不静默放弃）
            why = "needs-router"
            blocked.append({"net": net, "dist": dist, "why": why,
                            "layers_a": sorted(pcbnew.LayerName(l) for l in La),
                            "layers_b": sorted(pcbnew.LayerName(l) for l in Lb)})
    led = {"stage": "F1", "edges": len(edges), "added": added, "blocked": blocked,
           "F1_summary": {"added": len(added), "blocked": len(blocked),
                          "blocked_reasons": {k: sum(1 for x in blocked if x["why"] == k) for k in sorted({x["why"] for x in blocked})}}}
    json.dump(led, open(ledger_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if blocks:
        txt = open(src, encoding="utf-8").read()
        anchor = txt.index("\t(segment\n")
        tmp = out_path + ".f1_tmp.kicad_pcb"
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
    return led["F1_summary"]


def _fill(tmp, out_path):
    b2 = pcbnew.LoadBoard(tmp)
    if b2 is None:
        raise SystemExit("_fill: LoadBoard -> None")
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    b2.Save(out_path)
    print(json.dumps({"fill": "ok"}))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="K2 P4 阶段 F1：低速/电源局部闭合")
    ap.add_argument("--fill", nargs=2, metavar=("TMP", "OUT"))
    ap.add_argument("--in", dest="src"); ap.add_argument("--drc")
    ap.add_argument("--out"); ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    if a.fill:
        return _fill(a.fill[0], a.fill[1])
    if not (a.src and a.drc and a.out and a.ledger):
        ap.error("--in/--drc/--out/--ledger 必填")
    print(json.dumps(run(a.src, a.drc, a.out, a.ledger), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
