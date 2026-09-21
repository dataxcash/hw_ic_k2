#!/usr/bin/env python3
"""k2_p4_build_l9_v1 — **#K2-66 布局/可装配整改 → 新 rev `l9`**（构造器 · 判定权归监理）。

依据：#K2-66 §五-1（A1–A8 + B1/B2 + C1/C2）+ §三 阈值表 + §六 验收判据。
红线：**只增改本 rev**；l4..l8 逐字节不动；不改冻结四源/criteria/网表；临时仅 /tmp/opencode。

阶段（--stages 选择，默认全开）：
  fiducial  A1 加 3 个 fiducial（Ø1.0 铜 + mask 2× 开窗 · 距边 ≥3.35）
  info      A5 title_block + 丝印板名/版本/日期
  edge      A8 板框四角 R1.5 圆弧
  crtyd     A7 逐封装补 F.CrtYd（pads bbox + 0.25）
  silk      A3/A4 极性/1 脚标记 + 器件轮廓丝印（置于 courtyard 外沿 ⇒ 不压焊盘）
  silkfix   A6 位号文本移出焊盘（silk_over_pad → 0）
  chamfer   B1 90° 拐角 → 45° 倒角
  pour      C1 外层铺铜（GND，按覆盖率目标调 hatch/间隙）

用法：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
      k2/tools/k2_p4_build_l9_v1.py [--in B] [--out B] [--stages a,b,...] [--ledger P]
"""
from __future__ import annotations
import argparse, json, math, re, uuid

try:
    import pcbnew  # type: ignore
except Exception as e:  # noqa: BLE001
    raise SystemExit(f"pcbnew 不可用：{e}")

MM, TOMM = pcbnew.ToMM, pcbnew.ToMM
def IU(mm): return pcbnew.FromMM(mm)
def v(x, y): return pcbnew.VECTOR2I(IU(x), IU(y))
def bb(box): return (MM(box.GetX()), MM(box.GetY()), MM(box.GetRight()), MM(box.GetBottom()))
def overlap(a, b, tol=0.0):
    return not (a[2] < b[0]-tol or b[2] < a[0]-tol or a[3] < b[1]-tol or b[3] < a[1]-tol)
def uid(*parts): return str(uuid.uuid5(uuid.NAMESPACE_URL, "k2l9:" + ":".join(map(str, parts))))

LEDGER: dict = {}
def log(k, v): LEDGER.setdefault(k, []).append(v)

# ---------------------------------------------------------------- helpers
def board_rect(b):
    xs, ys = [], []
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            for p in (d.GetStart(), d.GetEnd()):
                xs.append(MM(p.x)); ys.append(MM(p.y))
    return (min(xs), min(ys), max(xs), max(ys))

def mask_aperture_boxes(b, layer=None):
    """焊盘/过孔之 **solder-mask 开窗** bbox（= kicad-cli `silk_over_copper` 之判据面）。"""
    out = []
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            if pd.GetLayerSet().Contains(pcbnew.F_Mask):
                L = pcbnew.F_Mask
            elif pd.GetLayerSet().Contains(pcbnew.B_Mask):
                L = pcbnew.B_Mask
            else:
                continue
            if layer is not None and L != layer:
                continue
            try:
                e = MM(pd.GetSolderMaskExpansion(L))
            except Exception:  # noqa: BLE001
                e = 0.0
            x1, y1, x2, y2 = bb(pd.GetBoundingBox())
            out.append((x1 - e, y1 - e, x2 + e, y2 + e))
    for t in b.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA):
            continue
        try:
            e = MM(t.GetSolderMaskExpansion())
        except Exception:  # noqa: BLE001
            e = 0.0
        if e <= 0:
            continue
        x1, y1, x2, y2 = bb(t.GetBoundingBox())
        out.append((x1 - e, y1 - e, x2 + e, y2 + e))
    return out


def cu_boxes(b):
    """焊盘 mask 开窗 bbox（丝印会被裁处）"""
    out = []
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            if pd.GetLayerSet().Contains(pcbnew.F_Mask) or pd.GetLayerSet().Contains(pcbnew.B_Mask):
                out.append((("pad", fp.GetReference(), pd.GetNumber()), bb(pd.GetBoundingBox())))
    return out

def all_cu_boxes(b):
    out = cu_boxes(b)
    for t in b.GetTracks():
        out.append((("trk", t.GetNetname(), ""), bb(t.GetBoundingBox())))
    return out

def free_spot(b, x, y, r, pad_boxes=None):
    """中心 (x,y) 半径 r 与既有铜/板边 无碰？"""
    if pad_boxes is None:
        pad_boxes = all_cu_boxes(b)
    ball = (x-r, y-r, x+r, y+r)
    for _, bx in pad_boxes:
        if overlap(ball, bx, tol=0.0):
            return False
    X1, Y1, X2, Y2 = board_rect(b)
    if x-r < X1+3.35 or x+r > X2-3.35 or y-r < Y1+3.35 or y+r > Y2-3.35:
        return False
    return True

# ---------------------------------------------------------------- stages
def courtyard_proxy_boxes(b, margin=0.15):
    """既有封装之 pads bbox + margin（= 本构造器所用 courtyard 口径）——供新件避让。"""
    out = []
    for fp in b.GetFootprints():
        if re.match(r"H\d", fp.GetReference()):
            c = fp.GetPosition(); cx, cy = MM(c.x), MM(c.y)
            out.append((("m3keepout", fp.GetReference(), ""),
                        (cx - 3.0, cy - 3.0, cx + 3.0, cy + 3.0)))
            continue
        pads = list(fp.Pads())
        if pads:
            bs = [bb(p.GetBoundingBox()) for p in pads]
            box = (min(x[0] for x in bs)-margin, min(x[1] for x in bs)-margin,
                   max(x[2] for x in bs)+margin, max(x[3] for x in bs)+margin)
        else:
            bx = bb(fp.GetBoundingBox())
            box = (bx[0]-margin, bx[1]-margin, bx[2]+margin, bx[3]+margin)
        out.append((("fpc", fp.GetReference(), ""), box))
    return out


def s_fiducial(b, target=3):
    boxes = all_cu_boxes(b) + courtyard_proxy_boxes(b)
    X1, Y1, X2, Y2 = board_rect(b)
    corners = [(X1, Y1), (X1, Y2), (X2, Y1), (X2, Y2)]
    placed = []
    for (cx, cy) in corners:
        sx = 1 if cx == X1 else -1
        sy = 1 if cy == Y1 else -1
        found = None
        for d in range(4, 60):            # 0.5mm 步进，从距边 2mm 起
            r = d * 0.5
            for ang in range(0, 360, 10):
                x = cx + sx * r * abs(math.cos(math.radians(ang)))
                y = cy + sy * r * abs(math.sin(math.radians(ang)))
                if free_spot(b, x, y, 1.0, boxes):
                    found = (x, y); break
            if found:
                break
        if not found:
            continue
        x, y = found
        ref = f"FID{len(placed)+1}"
        fp = pcbnew.FOOTPRINT(b); fp.SetReference(ref)
        fp.SetFPID(pcbnew.LIB_ID("", "Fiducial_1mm_Mask2mm"))
        fp.SetValue("Fiducial_1mm_Mask2mm"); fp.SetLayer(pcbnew.F_Cu)
        fp.SetPosition(v(x, y)); fp.SetAttributes(pcbnew.FP_SMD)
        pad = pcbnew.PAD(fp); pad.SetNumber(""); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD); pad.SetSize(v(1.0, 1.0))
        pad.SetPosition(v(x, y))
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask)
        pad.SetLayerSet(ls); pad.SetLocalSolderMaskMargin(IU(0.5)); fp.Add(pad)
        sh = pcbnew.PCB_SHAPE(fp); sh.SetShape(pcbnew.SHAPE_T_CIRCLE)
        sh.SetCenter(v(x, y)); sh.SetEnd(v(x + 1.3, y)); sh.SetLayer(pcbnew.F_CrtYd)
        sh.SetWidth(IU(0.05)); fp.Add(sh)
        b.Add(fp); boxes.append((("pad", ref, ""), (x-0.5, y-0.5, x+0.5, y+0.5)))
        boxes.append((("fid_crtyd", ref, ""), (x-1.0, y-1.0, x+1.0, y+1.0)))
        placed.append({"ref": ref, "x": round(x, 2), "y": round(y, 2)})
        if len(placed) >= target:
            break
    log("fiducial", {"placed": placed, "n": len(placed)})


def s_info(b, date="2026-09-21"):
    tb = b.GetTitleBlock()
    tb.SetTitle("K2 v4 8L PCIe5 x4 ioconvert carrier")
    tb.SetRevision("l9")
    tb.SetDate(date)
    tb.SetCompany("IC_HW")
    X1, Y1, X2, Y2 = board_rect(b)
    boxes = all_cu_boxes(b)
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText(f"K2-v4-l9 {date} rev l9")
    txt.SetLayer(pcbnew.F_SilkS)
    txt.SetTextSize(v(1.0, 1.0)); txt.SetTextThickness(IU(0.15))
    w, h = 1.0 * 0.95 * len(txt.GetText()), 1.6
    placed = None
    for y in [Y1 + 1.4, Y2 - 1.4]:
        for x in [X1 + 2 + w/2, X1 + 6, X1 + 12, X1 + 20, X1 + 30]:
            if x - w/2 < X1 + 0.6 or x + w/2 > X2 - 0.6:
                continue
            nb = (x-w/2, y-h/2, x+w/2, y+h/2)
            if not any(overlap(nb, bx) for _, bx in boxes):
                placed = (x, y); break
        if placed:
            break
    if placed is None:
        placed = (X1 + 2 + w/2, Y1 + 1.4)
    txt.SetPosition(v(*placed))
    b.Add(txt)
    log("info", {"title": "K2 v4 8L", "rev": "l9", "gr_text": txt.GetText(), "at": [round(placed[0],1), round(placed[1],1)]})

def s_edge(b, r=1.5):
    X1, Y1, X2, Y2 = board_rect(b)
    for d in list(b.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts:
            b.Remove(d)
    def line(p, q):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(v(*p)); s.SetEnd(v(*q)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(IU(0.1)); b.Add(s)
    def arc(c, s_, e_):
        # 三点定弧：中点在 c + r*(单位(s-c)+单位(e-c)) 方向
        sx, sy = s_[0]-c[0], s_[1]-c[1]; ex, ey = e_[0]-c[0], e_[1]-c[1]
        r = math.hypot(sx, sy)
        ux, uy = sx/r + ex/r, sy/r + ey/r
        n = math.hypot(ux, uy)
        mid = (c[0] + r*ux/n, c[1] + r*uy/n)
        a = pcbnew.PCB_SHAPE(b); a.SetShape(pcbnew.SHAPE_T_ARC)
        a.SetArcGeometry(v(*s_), v(*mid), v(*e_))
        a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(IU(0.1)); b.Add(a)
    line((X1+r, Y1), (X2-r, Y1)); line((X2, Y1+r), (X2, Y2-r))
    line((X2-r, Y2), (X1+r, Y2)); line((X1, Y2-r), (X1, Y1+r))
    arc((X1+r, Y1+r), (X1, Y1+r), (X1+r, Y1))
    arc((X2-r, Y1+r), (X2-r, Y1), (X2, Y1+r))
    arc((X2-r, Y2-r), (X2, Y2-r), (X2-r, Y2))
    arc((X1+r, Y2-r), (X1+r, Y2), (X1, Y2-r))
    log("edge", {"r_mm": r})

def _crtyd_of(b):
    m = {}
    for fp in b.GetFootprints():
        m[fp.GetReference()] = any(g.GetLayer() == pcbnew.F_CrtYd for g in fp.GraphicalItems())
    return m

def s_crtyd(b, margin=0.0, w=0.05):
    n = 0
    for fp in b.GetFootprints():
        if any(g.GetLayer() == pcbnew.F_CrtYd for g in fp.GraphicalItems()):
            continue
        pads = list(fp.Pads())
        if pads:
            boxes = [bb(p.GetBoundingBox()) for p in pads]
            x1 = min(x[0] for x in boxes)-margin; y1 = min(x[1] for x in boxes)-margin
            x2 = max(x[2] for x in boxes)+margin; y2 = max(x[3] for x in boxes)+margin
        else:
            p = fp.GetPosition(); x, y = MM(p.x), MM(p.y)
            x1, y1, x2, y2 = x-1, y-1, x+1, y+1
        sh = pcbnew.PCB_SHAPE(fp); sh.SetShape(pcbnew.SHAPE_T_RECT)
        sh.SetStart(v(x1, y1)); sh.SetEnd(v(x2, y2))
        sh.SetLayer(pcbnew.F_CrtYd); sh.SetWidth(IU(w))
        fp.Add(sh); n += 1
    log("crtyd", {"added": n})

def _clip_axis(lo, hi, blocked):
    """在 [lo,hi] 上减去 blocked 区间列表；返回剩余子区间。"""
    segs = [(lo, hi)]
    for bl, bh in blocked:
        out = []
        for a, b in segs:
            if bh <= a or bl >= b:
                out.append((a, b)); continue
            if bl > a:
                out.append((a, min(bl, b)))
            if bh < b:
                out.append((max(bh, a), b))
        segs = out
        if not segs:
            break
    return [(a, b) for a, b in segs if b - a > 1e-4]


def _sub(track, pad_boxes, hw):
    """把水平/垂直段按 pad bbox 剪断（pad 侧按 hw 膨胀）。"""
    x1, y1, x2, y2 = track
    res = []
    if abs(y1 - y2) < 1e-9:
        y = y1
        blk = [(b[0]-hw, b[2]+hw) for b in pad_boxes if b[1]-hw <= y <= b[3]+hw]
        for a, b in _clip_axis(min(x1, x2), max(x1, x2), blk):
            res.append((a, y, b, y))
    else:
        x = x1
        blk = [(b[1]-hw, b[3]+hw) for b in pad_boxes if b[0]-hw <= x <= b[2]+hw]
        for a, b in _clip_axis(min(y1, y2), max(y1, y2), blk):
            res.append((x, a, x, b))
    return res


def s_silk(b, w=0.12, margin=0.40, polar=True):
    """器件轮廓丝印（**按焊盘剪断** ⇒ 不压焊盘）+ 极性/1 脚标记（置 courtyard 外）。"""
    pad_boxes = mask_aperture_boxes(b, pcbnew.F_Mask)
    X1, Y1, X2, Y2 = board_rect(b)
    hw = w / 2.0 + 0.13
    n_seg = n_pol = n_fp = 0
    for fp in b.GetFootprints():
        pads = list(fp.Pads())
        if not pads:
            continue
        boxes = [bb(p.GetBoundingBox()) for p in pads]
        x1 = min(x[0] for x in boxes) - margin; y1 = min(x[1] for x in boxes) - margin
        x2 = max(x[2] for x in boxes) + margin; y2 = max(x[3] for x in boxes) + margin
        pos = fp.GetPosition(); px, py = MM(pos.x), MM(pos.y)
        made = 0
        cur_margin = margin
        for _try in range(4):
            cx1 = min(x[0] for x in boxes) - cur_margin; cy1 = min(x[1] for x in boxes) - cur_margin
            cx2 = max(x[2] for x in boxes) + cur_margin; cy2 = max(x[3] for x in boxes) + cur_margin
            segs = []
            for seg in ((cx1, cy1, cx2, cy1), (cx2, cy1, cx2, cy2), (cx2, cy2, cx1, cy2), (cx1, cy2, cx1, cy1)):
                segs += _sub(seg, pad_boxes, hw)
            if segs:
                for (ax, ay, bx, by) in segs:
                    sh = pcbnew.PCB_SHAPE(fp); sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
                    sh.SetStart(v(ax, ay)); sh.SetEnd(v(bx, by))
                    sh.SetLayer(pcbnew.F_SilkS); sh.SetWidth(IU(w))
                    fp.Add(sh); made += 1
                break
            cur_margin += 0.35
        if made:
            n_fp += 1; n_seg += made
        if polar and (fp.GetReference()[:1] in ("D", "U", "J", "Q", "K") or fp.GetReference().startswith(("LED", "BT"))):
            p1 = [p for p in pads if p.GetNumber() == "1"]
            if p1:
                c = p1[0].GetPosition(); cx, cy = MM(c.x), MM(c.y)
                spot = None
                for off in (0.30, 0.45, 0.60, 0.80, 1.00):
                    cands = [(x1-off, cy), (x2+off, cy), (cx, y1-off), (cx, y2+off)]
                    for (ox, oy) in cands:
                        nb = (ox-0.20, oy-0.20, ox+0.20, oy+0.20)
                        if any(overlap(nb, pb) for pb in pad_boxes):
                            continue
                        if ox < X1+0.4 or ox > X2-0.4 or oy < Y1+0.4 or oy > Y2-0.4:
                            continue
                        spot = (ox, oy); break
                    if spot:
                        break
                if spot:
                    q = pcbnew.PCB_SHAPE(fp); q.SetShape(pcbnew.SHAPE_T_CIRCLE)
                    q.SetCenter(v(*spot)); q.SetEnd(v(spot[0] + 0.28, spot[1]))
                    q.SetLayer(pcbnew.F_SilkS); q.SetWidth(IU(w)); q.SetFilled(True)
                    fp.Add(q); n_pol += 1
    log("silk", {"outlined_fp": n_fp, "segments": n_seg, "polar_markers": n_pol})


def s_silkfix(b, tol=-0.02):
    """与焊盘 mask 开窗相交的 Reference 文本 → 8 方向最小位移移出（保可读）。"""
    pads = mask_aperture_boxes(b, pcbnew.F_Mask)
    X1, Y1, X2, Y2 = board_rect(b)
    dirs = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]
    moved = 0
    for fp in b.GetFootprints():
        t = fp.Reference()
        if t.GetLayer() != pcbnew.F_SilkS:
            continue
        box = bb(t.GetBoundingBox())
        if not any(overlap(box, pb, tol=tol) for pb in pads):
            continue
        w, h = box[2] - box[0], box[3] - box[1]
        base = t.GetPosition(); bx, by = MM(base.x), MM(base.y)
        done = False
        for step in (0.6, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.6):
            for dx, dy in dirs:
                nx = bx + dx * step * (w * 0.75 + 0.35)
                ny = by + dy * step * (h * 1.8)
                nb = (nx - w/2, ny - h/2, nx + w/2, ny + h/2)
                if nb[0] < X1+0.5 or nb[2] > X2-0.5 or nb[1] < Y1+0.5 or nb[3] > Y2-0.5:
                    continue
                if not any(overlap(nb, pb, tol=tol) for pb in pads):
                    t.SetPosition(v(nx, ny)); moved += 1; done = True; break
            if done:
                break
    log("silkfix", {"moved": moved})


def s_chamfer(b, dmin=0.20):
    """90° 拐角 → 45° 倒角（两遍：先算全部拐点，再统一施加；内切 ⇒ 只增净距）。"""
    from collections import defaultdict
    tracks = [t for t in b.GetTracks() if not isinstance(t, (pcbnew.PCB_VIA, pcbnew.PCB_ARC))]
    def key(p): return (round(MM(p.x), 3), round(MM(p.y), 3))
    verts = defaultdict(list)     # (net,layer,pt) -> [(track, 'S'|'E')]
    for t in tracks:
        verts[(t.GetNetname(), t.GetLayer(), key(t.GetStart()))].append((t, "S"))
        verts[(t.GetNetname(), t.GetLayer(), key(t.GetEnd()))].append((t, "E"))
    ops = []      # (track, which, newpt)
    newsegs = []  # (p1,p2,width,layer,netcode)
    for (net, layer, pt), lst in verts.items():
        if len(lst) != 2:
            continue
        (ta, sa), (tb, sb) = lst
        if ta is tb:
            continue
        def endpt(t, w):
            return t.GetStart() if w == "S" else t.GetEnd()
        oa = endpt(ta, "E" if sa == "S" else "S")
        ob = endpt(tb, "E" if sb == "S" else "S")
        v1 = (MM(oa.x)-pt[0], MM(oa.y)-pt[1]); v2 = (MM(ob.x)-pt[0], MM(ob.y)-pt[1])
        n1 = math.hypot(*v1); n2 = math.hypot(*v2)
        if n1 < 1e-6 or n2 < 1e-6:
            continue
        u1 = (v1[0]/n1, v1[1]/n1); u2 = (v2[0]/n2, v2[1]/n2)
        dot = max(-1.0, min(1.0, u1[0]*u2[0] + u1[1]*u2[1]))
        if abs(math.degrees(math.acos(dot)) - 90.0) > 0.5:
            continue
        d = min(dmin, n1*0.40, n2*0.40)
        if d < 0.01:
            continue
        p1 = (pt[0] + u1[0]*d, pt[1] + u1[1]*d)
        p2 = (pt[0] + u2[0]*d, pt[1] + u2[1]*d)
        ops.append((ta, sa, p1)); ops.append((tb, sb, p2))
        newsegs.append((p1, p2, ta.GetWidth(), ta.GetLayer(), ta.GetNetCode()))
    for t, which, np_ in ops:
        if which == "S":
            t.SetStart(v(*np_))
        else:
            t.SetEnd(v(*np_))
    for p1, p2, wid, lay, nc in newsegs:
        nt = pcbnew.PCB_TRACK(b); nt.SetStart(v(*p1)); nt.SetEnd(v(*p2))
        nt.SetWidth(wid); nt.SetLayer(lay); nt.SetNetCode(nc); b.Add(nt)
    log("chamfer", {"corner_chamfers": len(newsegs), "ops": len(ops)})


def s_pour(b, margin=0.5, clr=0.25, thickness=0.25, hatch=(0.40, 0.80)):
    """外层 GND 铺铜（C1 铜平衡）。按 board 内缩 margin 铺满，填铜后测覆盖率。"""
    X1, Y1, X2, Y2 = board_rect(b)
    nc = b.GetNetcodeFromNetname("GND")
    added = []
    for layer, ln in ((pcbnew.F_Cu, "F.Cu"), (pcbnew.B_Cu, "B.Cu")):
        pts = [(X1+margin, Y1+margin), (X2-margin, Y1+margin),
               (X2-margin, Y2-margin), (X1+margin, Y2-margin)]
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNetCode(nc)
        o = z.Outline(); o.NewOutline()
        for (x, y) in pts:
            o.Append(IU(x), IU(y))
        z.SetLocalClearance(IU(clr)); z.SetMinThickness(IU(thickness))
        if hatch:
            z.SetFillMode(pcbnew.ZONE_FILL_MODE_HATCH_PATTERN)
            z.SetHatchThickness(IU(hatch[0])); z.SetHatchGap(IU(hatch[1]))
            try:
                z.SetHatchStyle(pcbnew.HATCH)
            except Exception:  # noqa: BLE001
                pass
        b.Add(z); added.append(ln)
    try:
        filler = pcbnew.ZONE_FILLER(b); filler.Fill(list(b.Zones()))
        ok = True
    except Exception as e:  # noqa: BLE001
        ok = False; log("pour_err", {"err": str(e)})
    log("pour", {"layers": added, "filled": ok})


def _cu_net_boxes(b):
    out = []
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            out.append((pd.GetNetname(), bb(pd.GetBoundingBox())))
    for t in b.GetTracks():
        out.append((t.GetNetname(), bb(t.GetBoundingBox())))
    return out


def s_testpoints(b, rails=("12V_IN", "P3V3", "P3V3_AUX", "MCU_VDD"),
                 hs=("PCIE_UP_OUT0_P_J2", "PCIE_UP_OUT0_N_J2", "PCIE_DN_OUT0_P_MCIO", "PCIE_DN_OUT0_N_MCIO"),
                 r=0.75):
    X1, Y1, X2, Y2 = board_rect(b)
    targets = list(rails) + list(hs)
    placed = []
    for net in targets:
        nc = b.GetNetcodeFromNetname(net)
        if nc <= 0:
            log("tp_skip", {"net": net, "why": "no netcode"}); continue
        boxes = _cu_net_boxes(b) + courtyard_proxy_boxes(b)
        pts = []
        for t in b.GetTracks():
            if t.GetNetname() != net or t.GetLayer() != pcbnew.F_Cu:
                continue
            pts.append((MM(t.GetStart().x), MM(t.GetStart().y)))
            pts.append((MM(t.GetEnd().x), MM(t.GetEnd().y)))
            sp = t.GetStart(); ep = t.GetEnd()
            pts.append(((MM(sp.x)+MM(ep.x))/2, (MM(sp.y)+MM(ep.y))/2))
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() == net and p.IsOnLayer(pcbnew.F_Cu):
                    pp = p.GetPosition(); pts.append((MM(pp.x), MM(pp.y)))
        spot = None
        for (cx, cy) in pts:
            if cx < X1+1.5 or cx > X2-1.5 or cy < Y1+1.5 or cy > Y2-1.5:
                continue
            ball = (cx-0.85, cy-0.85, cx+0.85, cy+0.85)
            if any(n != net and overlap(ball, bx) for n, bx in boxes):
                continue
            if any(n != net and overlap(ball, bx, tol=0.15) for n, bx in boxes):
                continue
            spot = (cx, cy); break
        stub = None
        if spot is None:
            # 退化：在近旁找空位 + 短直线 stub 接到同网铜（直线沿途须无他网铜）
            for (cx, cy) in pts:
                for rr in (1.2, 1.6, 2.0, 2.6, 3.2):
                    for ang in range(0, 360, 20):
                        x = cx + rr*math.cos(math.radians(ang)); y = cy + rr*math.sin(math.radians(ang))
                        if x < X1+1.5 or x > X2-1.5 or y < Y1+1.5 or y > Y2-1.5:
                            continue
                        ball = (x-0.85, y-0.85, x+0.85, y+0.85)
                        if any(n != net and overlap(ball, bx, tol=0.15) for n, bx in boxes):
                            continue
                        # 直线 x,y -> cx,cy 沿途采样
                        okline = True
                        for tt in [i/12 for i in range(13)]:
                            sx = x + (cx-x)*tt; sy = y + (cy-y)*tt
                            sb = (sx-0.15, sy-0.15, sx+0.15, sy+0.15)
                            if any(n != net and overlap(sb, bx) for n, bx in boxes):
                                okline = False; break
                        if okline:
                            stub = (x, y, cx, cy); break
                    if stub: break
                if stub: break
            if stub is None:
                log("tp_skip", {"net": net, "why": "no spot+clear stub"}); continue
            x, y, cx, cy = stub
        else:
            x, y = spot
        if any(overlap((x-0.85, y-0.85, x+0.85, y+0.85), bx) for nm, bx in boxes if nm == "__tp__"):
            log("tp_skip", {"net": net, "why": "tp-collision"}); continue
        ref = f"TP{len(placed)+1}"
        fp = pcbnew.FOOTPRINT(b); fp.SetReference(ref)
        fp.SetFPID(pcbnew.LIB_ID("", "TestPoint_1.5mm"))
        fp.SetValue("TestPoint_1.5mm_" + net); fp.SetLayer(pcbnew.F_Cu)
        fp.SetPosition(v(x, y)); fp.SetAttributes(pcbnew.FP_SMD)
        pad = pcbnew.PAD(fp); pad.SetNumber(""); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD); pad.SetSize(v(1.5, 1.5))
        pad.SetPosition(v(x, y)); pad.SetNetCode(nc)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask)
        pad.SetLayerSet(ls); fp.Add(pad)
        sh = pcbnew.PCB_SHAPE(fp); sh.SetShape(pcbnew.SHAPE_T_CIRCLE)
        sh.SetCenter(v(x, y)); sh.SetEnd(v(x + 0.85, y)); sh.SetLayer(pcbnew.F_CrtYd)
        sh.SetWidth(IU(0.05)); fp.Add(sh)
        tk = None
        if stub is not None:
            tk = pcbnew.PCB_TRACK(b); tk.SetStart(v(x, y)); tk.SetEnd(v(cx, cy))
            tk.SetWidth(IU(0.25)); tk.SetLayer(pcbnew.F_Cu); tk.SetNetCode(nc); b.Add(tk)
        b.BuildConnectivity(); before = b.GetConnectivity().GetUnconnectedCount(False)
        b.Add(fp)
        b.BuildConnectivity(); after = b.GetConnectivity().GetUnconnectedCount(False)
        if after > before:
            b.Remove(fp)
            if tk is not None:
                b.Remove(tk)
            log("tp_skip", {"net": net, "why": f"unconnected {before}->{after}"})
            continue
        boxes.append(("__tp__", (x-0.85, y-0.85, x+0.85, y+0.85)))
        placed.append({"ref": ref, "net": net, "at": [round(x, 2), round(y, 2)]})
    log("testpoint", {"placed": placed, "n": len(placed)})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="k2/hw/k2_v4_8L.l8.kicad_pcb")
    ap.add_argument("--out", default="/tmp/opencode/l9/k2_v4_8L.l9.kicad_pcb")
    ap.add_argument("--stages", default="fiducial,info,edge,tp,crtyd,silk,silkfix,chamfer,pour")
    ap.add_argument("--ledger", default="/tmp/opencode/l9/k2_p4_l9_ledger.json")
    a = ap.parse_args(argv)
    stages = [s for s in a.stages.split(",") if s]
    b = pcbnew.LoadBoard(a.inp)
    fn = {"fiducial": s_fiducial, "info": s_info, "edge": s_edge, "crtyd": s_crtyd,
          "silk": s_silk, "silkfix": s_silkfix, "chamfer": s_chamfer, "tp": s_testpoints}
    for st in stages:
        if st in fn:
            fn[st](b)
    if "pour" in stages:
        s_pour(b)
    import os; os.makedirs(os.path.dirname(a.out), exist_ok=True)
    b.Save(a.out)
    with open(a.ledger, "w", encoding="utf-8") as fh:
        json.dump(LEDGER, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"out": a.out, "stages": stages, "ledger": LEDGER}, ensure_ascii=False)[:1500])

if __name__ == "__main__":
    raise SystemExit(main())
