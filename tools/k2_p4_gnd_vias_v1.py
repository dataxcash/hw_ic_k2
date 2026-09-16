#!/usr/bin/env python3
"""K2 · P4 收敛增量 —— GND 平面接入 v2（阶段 E）：层正确净距 + 盘中孔（via-in-pad）。

依据 owner 常设裁定 #14（**过孔策略 = L2 自裁 · 勿停**）+ 《宪法》第四条（改板须 SPEC 留痕）。

对每个 **DRC 未连接的 GND 焊盘**：加 1 支 **F.Cu→In1.Cu 盲孔**（0.20 孔 / 0.35 盘，板内既有唯一类），
圆心**首选焊盘中心（盘中孔）**；不合法时按确定性极坐标网格找位并以 0/45/90° 同网引线接入。

与既有 `k2_p4_converge_v1.py` 阶段 D 的差别（**本器不修改 v1**）：
  1. **层正确**：F.Cu→In1.Cu 盲孔的铜只存在于 F.Cu / In1.Cu ⇒ 只与这两层铜做净距/孔-铜判定
     （v1 的 clear_pt/clear_seg **不分层**，把 In2/In5/B.Cu 走线也当障碍 ⇒ 系统性过保守）。
  2. **盘中孔候选**：v1 只从铜岛端点按 r≥0.35 极坐标找位，**不含焊盘中心**。
判定口径（与 `_shared/eda_core/drc_rules.json` 一致，**不放松任何下限**）：
  净距 = net class max（PCIe85 0.175 / POWER 0.2 / LOW_SPEED 0.1，board_min 0.1）；
  孔-铜 0.25；孔-孔 0.25（**无同网豁免**，含新增孔）；板边铜 0.3；新段 0/45/90° 且单腿 ≥0.05。
纯增（不动既有铜）；uuid 由几何 uuid5 派生（复跑逐字节一致）。判定权归监理，本器只交测量。
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, re, shutil, subprocess, sys, uuid
import pcbnew

_HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("k2cv", os.path.join(_HERE, "k2_p4_converge_v1.py"))
cv = importlib.util.module_from_spec(_s); _s.loader.exec_module(cv)

F_CU, IN1_CU = pcbnew.F_Cu, pcbnew.In1_Cu
SPAN = {F_CU, IN1_CU}
VIA_W, VIA_D = 0.35, 0.20          # 板内既有唯一过孔类（505 支同规格）
VIA_R, HOLE_R = VIA_W / 2.0, VIA_D / 2.0
TRACE_W = 0.20
SEGPAT = re.compile(r'\t\(segment\n\t\t\(start ([\-\d.]+) ([\-\d.]+)\)\n\t\t\(end ([\-\d.]+) ([\-\d.]+)\)\n\t\t\(width ([\-\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net "([^"]*)"\)')


NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
VIA_BLOCK = ('\t(via blind\n\t\t(at {x} {y})\n\t\t(size 0.35)\n\t\t(drill 0.2)\n'
             '\t\t(layers "F.Cu" "In1.Cu")\n\t\t(net "GND")\n\t\t(uuid "{u}")\n\t)\n')
SEG_BLOCK = ('\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width 0.2)\n'
             '\t\t(layer "F.Cu")\n\t\t(net "GND")\n\t\t(uuid "{u}")\n\t)\n')


def _fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def via_uuid(x, y):
    import uuid as _u
    return str(_u.uuid5(NS, "k2p4gnd|via|%s|%s" % (_fmt(x), _fmt(y))))


def seg_uuid(x1, y1, x2, y2):
    import uuid as _u
    return str(_u.uuid5(NS, "k2p4gnd|seg|%s|%s|%s|%s" % (_fmt(x1), _fmt(y1), _fmt(x2), _fmt(y2))))


class Model:
    """按层收集障碍：过孔 F.Cu→In1.Cu 的铜只与其 span 层交互。"""

    def __init__(self, board):
        MM = cv.MM
        self.b = board
        self.tracks = []      # 与 span 相交的走线 (net,x1,y1,x2,y2,hw,layer)
        self.tracks_f = []    # 仅 F.Cu（供新引线判定）
        self.pads = []        # 与 span 相交的焊盘
        self.pads_f = []      # 仅 F.Cu 铜的焊盘（供引线判定）
        self.vias = []        # 与 span 相交的既有过孔 (net,x,y,r,hole)
        self.holes = []       # 全部孔（孔-孔无同网豁免、无分层豁免）
        for t in board.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA):
                ls = t.GetLayerSet()
                pos = t.GetPosition()
                x, y = MM(pos.x), MM(pos.y)
                r = MM(t.GetWidth(F_CU)) / 2.0
                hr = MM(t.GetDrillValue()) / 2.0
                self.holes.append((x, y, hr))
                if ls.Contains(F_CU) or ls.Contains(IN1_CU):
                    self.vias.append((t.GetNetname(), x, y, r, hr))
                continue
            L = t.GetLayer()
            if L not in SPAN:
                continue
            s, e = t.GetStart(), t.GetEnd()
            rec = (t.GetNetname(), MM(s.x), MM(s.y), MM(e.x), MM(e.y), MM(t.GetWidth()) / 2.0, L)
            self.tracks.append(rec)
            if L == F_CU:
                self.tracks_f.append(rec)
        for fp in board.GetFootprints():
            for p in fp.Pads():
                ls = p.GetLayerSet()
                onf = ls.Contains(F_CU)
                if not (onf or ls.Contains(IN1_CU)):
                    continue
                pos, sz = p.GetPosition(), p.GetSize()
                dz = p.GetDrillSize()
                circ = p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
                x, y, w, h = MM(pos.x), MM(pos.y), MM(sz.x), MM(sz.y)
                hr = MM(dz.x) / 2.0 if dz.x > 0 else 0.0
                rec = dict(net=p.GetNetname(), x=x, y=y, w=w, h=h, circ=circ, hole=hr,
                           poly=None if circ else cv.rect_corners(x, y, w, h, p.GetOrientationDegrees()))
                self.pads.append(rec)
                if onf:
                    self.pads_f.append(rec)
                if hr > 0:
                    self.holes.append((x, y, hr))
        self.keep_v = []      # 禁 via 的禁布区
        self.keep_t = []      # 禁 track 的禁布区
        for z in board.Zones():
            if not z.GetIsRuleArea():
                continue
            polys = []
            for i in range(z.Outline().OutlineCount()):
                ch = z.Outline().Outline(i)
                polys.append([(MM(ch.CPoint(k).x), MM(ch.CPoint(k).y)) for k in range(ch.PointCount())])
            if z.GetDoNotAllowVias(): self.keep_v += polys
            if z.GetDoNotAllowTracks(): self.keep_t += polys
        self.edge = []
        for d in board.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts and hasattr(d, "GetStart"):
                s, e = d.GetStart(), d.GetEnd()
                self.edge.append((MM(s.x), MM(s.y), MM(e.x), MM(e.y)))

    # ── 净距（含孔-铜=max(铜净距, 0.25+HOLE_R) 的合并口径，同 v1） ──
    def _need(self, net):
        return max(VIA_R + cv._req("GND", net or ""), HOLE_R + 0.25)

    def via_ok(self, x, y, extra_holes=()):
        for e in self.edge:
            if cv.pt_seg_dist(x, y, *e) < 0.3 + VIA_R:
                return False
        for poly in self.keep_v:
            if cv.pt_in_poly(x, y, poly):
                return False
        for net, x1, y1, x2, y2, hw, _L in self.tracks:
            if net == "GND":
                continue
            if cv.pt_seg_dist(x, y, x1, y1, x2, y2) - hw < self._need(net):
                return False
        for p in self.pads:
            if p["net"] == "GND":
                continue
            need = self._need(p["net"])
            if p["circ"]:
                if math.hypot(x - p["x"], y - p["y"]) - min(p["w"], p["h"]) / 2.0 < need:
                    return False
            elif cv.pt_in_poly(x, y, p["poly"]) or cv.pt_poly_dist(x, y, p["poly"]) < need:
                return False
        for net, vx, vy, vr, _vh in self.vias:
            if net == "GND":
                continue
            if math.hypot(x - vx, y - vy) - vr < self._need(net):
                return False
        for hx, hy, hr in list(self.holes) + list(extra_holes):
            if math.hypot(x - hx, y - hy) < 0.25 + HOLE_R + hr:
                return False
        return True

    def seg_ok(self, x1, y1, x2, y2):
        hw = TRACE_W / 2.0
        for e in self.edge:
            if cv.seg_seg_dist(x1, y1, x2, y2, *e) < 0.3 + hw:
                return False
        for poly in self.keep_t:
            if cv.seg_poly_dist(x1, y1, x2, y2, poly) <= 0:
                return False
        for net, ax, ay, bx, by, thw, _L in self.tracks_f:
            if net == "GND":
                continue
            if cv.seg_seg_dist(x1, y1, x2, y2, ax, ay, bx, by) < hw + thw + cv._req("GND", net):
                return False
        for p in self.pads_f:
            if p["net"] == "GND":
                continue
            need = hw + cv._req("GND", p["net"])
            if p["circ"]:
                if cv.pt_seg_dist(p["x"], p["y"], x1, y1, x2, y2) - min(p["w"], p["h"]) / 2.0 < need:
                    return False
            elif cv.seg_poly_dist(x1, y1, x2, y2, p["poly"]) < need:
                return False
        for net, vx, vy, vr, _vh in self.vias:
            if net == "GND":
                continue
            if cv.pt_seg_dist(vx, vy, x1, y1, x2, y2) - vr < hw + cv._req("GND", net):
                return False
        return True

    @staticmethod
    def in_pad(p, x, y, tol=0.002):
        if p["circ"]:
            return math.hypot(x - p["x"], y - p["y"]) <= min(p["w"], p["h"]) / 2.0 + tol
        return cv.pt_in_poly(x, y, p["poly"]) or cv.pt_poly_dist(x, y, p["poly"]) <= tol


def candidates(px, py):
    """确定性候选序：焊盘中心优先，其后 r 升序、角升序（r 步 0.025 ≤0.50，角步 7.5°）。"""
    out = [(px, py, 0.0)]
    for i in range(1, 21):
        r = 0.025 * i
        for k in range(48):
            a = math.radians(7.5 * k)
            out.append((px + r * math.cos(a), py + r * math.sin(a), r))
    return out


def run(src, drc_path, out_path, ledger_path):
    b = pcbnew.LoadBoard(src)
    M = Model(b)
    drc = json.load(open(drc_path, encoding="utf-8"))
    targets = set()
    for u in drc.get("unconnected_items", []):
        for it in u.get("items", []):
            m = cv._GPAD.search(it.get("description", ""))
            if m and m.group(3) == "GND":
                targets.add((m.group(1), m.group(2)))
    pad_by = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            ls = p.GetLayerSet()
            if not (ls.Contains(F_CU) or ls.Contains(IN1_CU)):
                continue
            pos, sz = p.GetPosition(), p.GetSize()
            dz = p.GetDrillSize()
            circ = p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
            pad_by[(fp.GetReference(), p.GetNumber())] = dict(
                net=p.GetNetname(), x=cv.MM(pos.x), y=cv.MM(pos.y), w=cv.MM(sz.x), h=cv.MM(sz.y), circ=circ,
                hole=cv.MM(dz.x) / 2.0 if dz.x > 0 else 0.0,
                poly=None if circ else cv.rect_corners(cv.MM(pos.x), cv.MM(pos.y), cv.MM(sz.x), cv.MM(sz.y), p.GetOrientationDegrees()))
    added, blocked, blocks = [], [], []
    new_holes = []
    for ref, num in sorted(targets):
        p = pad_by.get((ref, num))
        if p is None or p["net"] != "GND":
            blocked.append({"ref": ref, "num": num, "why": "pad-not-found-or-not-gnd"}); continue

        pick = None
        for x, y, r_off in candidates(p["x"], p["y"]):
            if not M.via_ok(x, y, new_holes):
                continue
            if M.in_pad(p, x, y):
                pick = (x, y, r_off, []); break
            for pp in cv._paths45((p["x"], p["y"]), (x, y)):
                if all(M.seg_ok(pp[i][0], pp[i][1], pp[i + 1][0], pp[i + 1][1]) for i in range(len(pp) - 1)):
                    pick = (x, y, r_off, [(pp[i][0], pp[i][1], pp[i + 1][0], pp[i + 1][1]) for i in range(len(pp) - 1)])
                    break
            if pick:
                break
        if pick is None:
            blocked.append({"ref": ref, "num": num, "why": "no-legal-slot"}); continue
        x, y, r_off, legs = pick
        blocks.append(VIA_BLOCK.format(x=_fmt(x), y=_fmt(y), u=via_uuid(x, y)))
        for x1, y1, x2, y2 in legs:
            blocks.append(SEG_BLOCK.format(x1=_fmt(x1), y1=_fmt(y1), x2=_fmt(x2), y2=_fmt(y2),
                                           u=seg_uuid(x1, y1, x2, y2)))
            M.tracks.append(("GND", x1, y1, x2, y2, TRACE_W / 2.0, F_CU))
        M.vias.append(("GND", x, y, VIA_R, HOLE_R)); M.holes.append((x, y, HOLE_R)); new_holes.append((x, y, HOLE_R))
        added.append({"ref": ref, "num": num, "via": [round(x, 3), round(y, 3)], "offset": round(r_off, 3),
                      "in_pad": bool(M.in_pad(p, x, y)), "legs": len(legs)})
    led = {"stage": "E", "targets": len(targets), "added": added, "blocked": blocked,
           "E_summary": {"added": len(added), "in_pad": sum(1 for a in added if a["in_pad"]),
                         "segments": sum(1 for a in added if a["legs"]), "blocked": len(blocked)}}
    json.dump(led, open(ledger_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # ── 文本注入（真·盲孔：(via blind + layers "F.Cu" "In1.Cu"；uuid 由几何派生） ──
    txt = open(src, encoding="utf-8").read()
    anchor = txt.index("\t(segment\n")
    txt = txt[:anchor] + "".join(blocks) + txt[anchor:]
    # ★ 本 build 的 pcbnew：① 同进程内加载第二块板会 segfault；② LoadBoard 按扩展名分发
    #   ⇒ tmp 必须保持 .kicad_pcb 后缀，且区域填充另起子进程（干净状态）；
    #   ③ 取 DRC/netclass 设置须件与 .kicad_pro 同名同目录 ⇒ 同步复制 pro。
    tmp = out_path + ".stage_e_tmp.kicad_pcb"
    open(tmp, "w", encoding="utf-8").write(txt)
    src_pro = re.sub(r"\.kicad_pcb$", ".kicad_pro", src)
    if os.path.exists(src_pro):
        shutil.copyfile(src_pro, re.sub(r"\.kicad_pcb$", ".kicad_pro", tmp))
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--fill", tmp, out_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("refill failed rc=%d %s" % (r.returncode, r.stderr[-400:]))
    if os.path.exists(src_pro):
        shutil.copyfile(src_pro, re.sub(r"\.kicad_pcb$", ".kicad_pro", out_path))
    os.remove(tmp)
    return led["E_summary"]


def _fill(tmp, out_path):
    b2 = pcbnew.LoadBoard(tmp)
    if b2 is None:
        raise SystemExit("_fill: LoadBoard(%s) -> None" % tmp)
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    b2.Save(out_path)
    print(json.dumps({"fill": "ok", "vias": len([t for t in b2.GetTracks() if isinstance(t, pcbnew.PCB_VIA)])}))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="K2 P4 阶段 E：GND 平面接入 v2（层正确 + 盘中孔）")
    ap.add_argument("--fill", nargs=2, metavar=("TMP", "OUT"), help="内部用：子进程区域填充")
    ap.add_argument("--in", dest="src")
    ap.add_argument("--drc", help="输入板的 kicad-cli pcb drc json")
    ap.add_argument("--out")
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    if a.fill:
        return _fill(a.fill[0], a.fill[1])
    if not (a.src and a.drc and a.out and a.ledger):
        ap.error("--in/--drc/--out/--ledger 必填（除内部 --fill 模式）")
    print(json.dumps(run(a.src, a.drc, a.out, a.ledger), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
