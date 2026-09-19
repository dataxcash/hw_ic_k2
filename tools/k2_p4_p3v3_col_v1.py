#!/usr/bin/env python3
"""K2 · P4 增量 14（L2 自裁：**PDN / 走廊 / 过孔策略**）—— P3V3 去耦列 + C82.1 接入 In4 电源面。

依据：owner #14（L2 = PDN/走廊/布线/过孔策略 = 自裁勿停）· 监理 #K2-19 §二（W-1..W-5 授权新写确定性执行器）
     · handoff §5-4（「去耦链 C79/C80/C81/C83 + C82.1 的 P3V3→In4 接入 = 走廊级，T-20」）。

动因（实测，板 62cecafe810c637f）：DRC 未连接 2 组 P3V3 孤岛 ——
  [1] `C82.1`(90.65,64.0) 与 `C83.1`(90.55,62.0) 分立；[2] 去耦列岛 {C79.1,C80.1,C81.1,C83.1}（F.Cu 串联段 59→62）与主网（U6 北侧 y≈54 球扇出 + In4 面）分立。

施工（**纯增**；孔类沿用增量的 `F.Cu..In4.Cu` 盲孔 0.35/0.2 盘中孔 = 增量 12 同型；不放松任何 DRC 下限）：
  T1 **去耦列面接入**：C83.1(90.55,62.0) pad 中心落 **F→In4 盘中孔**（0603 pad 0.6×0.7 ⇒ 环宽充裕；span 裕度 **+0.225**）。
  T2 **C82.1 远端逃逸**：C82.1 中心 span 裕度 **−0.355**（阻断 = `PCIE_DN5_P@In2.Cu`）⇒ 不可原位落孔；
     取**南侧**确定性搜索：0.1mm 网格（x∈[90.0,94.0], y∈[63.6,66.0]）筛「span 裕度 ≥ +0.10 **且** 落点在 In4 `P3V3` fill 内」，
     按 (距离, x, y) 排序取**首个**存在 0/45/90 合法 F.Cu 逃逸者 ⇒ 落 **F→In4 盲孔** + 逃逸段（宽 0.20）。

口径（与 `_shared/eda_core/drc_rules.json` 一致）：
  - **过孔**：span 感知净距（F/In1/In2/In3/In4 逐层）+ 孔-孔 0.25（**无同网豁免**，全量孔）+ 禁布区 + 板边 0.3；**且必须落在目标 zone 的已填充区内**（T-25：
    不重填 zone ⇒ 面覆盖以存储 fill 为准，否则不连通）。
  - **F.Cu 逃逸段**：**层感知** oracle —— 仅 F.Cu 铜 + **其 span 含 F.Cu 的孔**（In 层盲孔的孔对 F.Cu 为假阻断，T-18 同类陷阱）；净距 = net class max；0/45/90 且单腿 ≥0.05。
  - 纯增；复跑确定性（几何 uuid5 派生）；幂等。
CLI: python3 k2_p4_p3v3_col_v1.py --in <board> --out <board> --ledger <json>
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, re, sys, uuid
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
def _load(n, f):
    sp = importlib.util.spec_from_file_location(n, os.path.join(HERE, f))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cv = _load("k2cv", "k2_p4_converge_v1.py")
f3 = _load("k2f3", "k2_p4_ls_xlayer_v1.py")
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
VR, HR, TRHW = 0.175, 0.1, 0.1
# 定式（确定性；由修正后 oracle 逐项验证后固化，见 SPEC 留痕）
TARGETS = [
    # 去耦列岛（C79/C80/C81/C83）：C81.1 -> 西逃逸 -> 落孔
    # re-host(inc101)：原定式孔位 (83.50,60.55) 在新链被 DS320_STRAP_MODE@In2.Cu 堵死（span 裕度 −0.075，P3 时 +0.2425）
    # ⇒ 以本器 oracle（span_margin ≥0.10 ∧ in_zone(In4 P3V3) ∧ 0/45/90 合法 F.Cu 逃逸）确定性重解，
    #    取最大裕度解 (81.00,60.60) 裕度 +1.0726，逃逸 = 45°(90.65,60.00→90.05,60.60) + 西段(→81.00,60.60)。
    dict(name="col", net="P3V3", src=(90.65, 60.00, "C81.1"), via=(81.00, 60.60),
         legs=[(90.65, 60.00), (90.05, 60.60), (81.00, 60.60)]),
    # C82.1（南侧孤岛）：C82.1 -> 东逃逸 -> 落孔
    dict(name="c82", net="P3V3", src=(90.65, 64.00, "C82.1"), via=(94.50, 64.70),
         legs=[(90.65, 64.00), (90.65, 64.70), (94.50, 64.70)]),
]


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def vid(u):
    return str(uuid.uuid5(NS, "k2p4p3v3col|via|F.Cu|In4.Cu|%s|%s" % (fmt(u[0]), fmt(u[1]))))


def sid(x1, y1, x2, y2):
    return str(uuid.uuid5(NS, "k2p4p3v3col|seg|P3V3|%s|%s|%s|%s" % (fmt(x1), fmt(y1), fmt(x2), fmt(y2))))


VIA_BLOCK = ('\t(via blind\n\t\t(at {x} {y})\n\t\t(size 0.35)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "In4.Cu")\n'
             '\t\t(net "P3V3")\n\t\t(uuid "{u}")\n\t)\n')
SEG_BLOCK = ('\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n'
             '\t\t(net "P3V3")\n\t\t(uuid "{u}")\n\t)\n')


def build_ctx(board):
    b = pcbnew.LoadBoard(board)
    c = f3.Ctx(b)
    lid = {pcbnew.LayerName(i): i for i in range(pcbnew.PCB_LAYER_ID_COUNT)}
    vspan = {}
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            ls = t.GetLayerSet()
            vspan[(round(cv.MM(t.GetPosition().x), 4), round(cv.MM(t.GetPosition().y), 4))] = set(
                l for l in range(pcbnew.PCB_LAYER_ID_COUNT) if ls.Contains(l))
    fhole = [(hx, hy, hr, hn) for (hx, hy, hr, hn) in c.holes
             if (round(hx, 4), round(hy, 4)) not in vspan or lid["F.Cu"] in vspan[(round(hx, 4), round(hy, 4))]]
    zfill = []
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        for l in z.GetLayerSet().Seq():
            sps = z.GetFilledPolysList(l)
            for oi in range(sps.OutlineCount()):
                ch = sps.Outline(oi)
                poly = [(cv.MM(ch.CPoint(k).x), cv.MM(ch.CPoint(k).y)) for k in range(ch.PointCount())]
                holes = [[(cv.MM(sps.Hole(oi, hi).CPoint(k).x), cv.MM(sps.Hole(oi, hi).CPoint(k).y))
                          for k in range(sps.Hole(oi, hi).PointCount())] for hi in range(sps.HoleCount(oi))]
                zfill.append((z.GetNetname(), l, poly, holes))
    return b, c, lid, fhole, zfill


def _bb_far(t, x, y, rad):
    """粗筛：按**段 bbox**（非中点！长走线的中点可能远而线段贴身）"""
    return (min(t["x1"], t["x2"]) - rad > x or max(t["x1"], t["x2"]) + rad < x
            or min(t["y1"], t["y2"]) - rad > y or max(t["y1"], t["y2"]) + rad < y)


def span_margin(c, lid, x, y, net):
    SPAN = [lid["F.Cu"], lid["In1.Cu"], lid["In2.Cu"], lid["In3.Cu"], lid["In4.Cu"]]
    rows = []
    for t in c.tracks:
        if t["layer"] not in SPAN or t["net"] == net: continue
        if _bb_far(t, x, y, 0.6): continue
        rows.append((cv.pt_seg_dist(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) - t["hw"] - VR - cv._req(net, t["net"]),
                     "trk/%s@%s" % (t["net"], pcbnew.LayerName(t["layer"]))))
    for p in c.pads.values():
        if p["net"] == net or not any(l in p["lay"] for l in SPAN): continue
        if abs(p["x"] - x) > 2.0 or abs(p["y"] - y) > 2.0: continue
        d = (math.hypot(x - p["x"], y - p["y"]) - min(p["w"], p["h"]) / 2 - VR - cv._req(net, p["net"])) if p["circ"] \
            else (cv.pt_poly_dist(x, y, p["poly"]) - VR - cv._req(net, p["net"]))
        rows.append((d, "pad/%s" % p["net"]))
    for v in c.vias.values():
        if v["net"] == net or not any(l in v["lay"] for l in SPAN): continue
        if abs(v["x"] - x) > 2.0 or abs(v["y"] - y) > 2.0: continue
        rows.append((math.hypot(x - v["x"], y - v["y"]) - v["r"] - VR - cv._req(net, v["net"]), "via/%s" % v["net"]))
    for (hx, hy, hr, hn) in c.holes:                      # 孔-孔：全量孔（无同网豁免）
        if abs(hx - x) > 2.0 or abs(hy - y) > 2.0: continue
        rows.append((math.hypot(x - hx, y - hy) - HR - 0.25 - hr, "hole/%s" % hn))
    for e in c.edge: rows.append((cv.pt_seg_dist(x, y, *e) - VR - 0.3, "edge"))
    for poly in c.keep_v:
        if cv.pt_in_poly(x, y, poly): rows.append((-1.0, "keep_v"))
    rows.sort(); return rows[0] if rows else (9.0, "none")


def raw_hole_margin(c, lid, x, y):
    """只算 孔-孔（含 C82 自身邻域），供写前复算"""
    rows = []
    for (hx, hy, hr, hn) in c.holes:
        if abs(hx - x) > 2.0 or abs(hy - y) > 2.0: continue
        rows.append((math.hypot(x - hx, y - hy) - HR - 0.25 - hr, "hole/%s" % hn))
    rows.sort(); return rows[0] if rows else (9.0, "none")


def pip(px, py, poly):
    ins = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1): ins = not ins
    return ins


def in_zone(zfill, lid, x, y, net):
    for zn, l, poly, holes in zfill:
        if zn != net or l != lid["In4.Cu"]: continue
        if pip(x, y, poly) and not any(pip(x, y, h) for h in holes): return True
    return False


def seg_ok(c, lid, fhole, x1, y1, x2, y2, net, hw=TRHW):
    F = lid["F.Cu"]
    for e in c.edge:
        if cv.seg_seg_dist(x1, y1, x2, y2, *e) < 0.3 + hw: return False
    for poly in c.keep_t:
        if cv.seg_poly_dist(x1, y1, x2, y2, poly) <= 0: return False
    for t in c.tracks:
        if t["layer"] != F or t["net"] == net: continue
        if cv.seg_seg_dist(x1, y1, x2, y2, t["x1"], t["y1"], t["x2"], t["y2"]) < hw + t["hw"] + cv._req(net, t["net"]): return False
    for p in c.pads.values():
        if F not in p["lay"] or p["net"] == net: continue
        rad = hw + cv._req(net, p["net"])
        if p["circ"]:
            if cv.pt_seg_dist(p["x"], p["y"], x1, y1, x2, y2) - min(p["w"], p["h"]) / 2 < rad: return False
        elif cv.seg_poly_dist(x1, y1, x2, y2, p["poly"]) < rad: return False
    for v in c.vias.values():
        if F not in v["lay"] or v["net"] == net: continue
        if cv.pt_seg_dist(v["x"], v["y"], x1, y1, x2, y2) - v["r"] < hw + cv._req(net, v["net"]): return False
    for (hx, hy, hr, hn) in fhole:                       # 层感知孔表
        if hn == net: continue
        if cv.pt_seg_dist(hx, hy, x1, y1, x2, y2) < hr + 0.25 + hw: return False
    return True


def paths_ok(c, lid, fhole, a, bb, net):
    (x1, y1), (x2, y2) = a, bb
    m = min(abs(x2 - x1), abs(y2 - y1))
    sx = math.copysign(m, x2 - x1) if x2 != x1 else 0.0
    sy = math.copysign(m, y2 - y1) if y2 != y1 else 0.0
    cands = [[a, bb], [a, (x1 + sx, y1 + sy), bb], [a, (x2, y1), bb], [a, (x1, y2), bb]]
    for p in cands:
        if any(math.hypot(p[k + 1][0] - p[k][0], p[k + 1][1] - p[k][1]) < 0.05 for k in range(len(p) - 1)): continue
        if all(seg_ok(c, lid, fhole, p[k][0], p[k][1], p[k + 1][0], p[k + 1][1], net) for k in range(len(p) - 1)):
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--ledger", dest="ledger", required=True)
    a = ap.parse_args()
    b, c, lid, fhole, zfill = build_ctx(a.src)
    txt = open(a.src, encoding="utf-8").read()
    ops = []
    blocks = ""
    for tg in TARGETS:
        net = tg["net"]; vx, vy = tg["via"]
        # 幂等
        if vid((vx, vy)) in txt:
            ops.append(dict(target=tg["name"], status="already-present", via=[vx, vy])); continue
        m, blk = span_margin(c, lid, vx, vy, net)
        assert in_zone(zfill, lid, vx, vy, net), "%s: 孔位不在 In4 %s fill 内" % (tg["name"], net)
        assert m > 0, "%s: 孔位 span 裕度 %.4f < 0 (%s)" % (tg["name"], m, blk)
        legs = []
        for k in range(len(tg["legs"]) - 1):
            (x1, y1), (x2, y2) = tg["legs"][k], tg["legs"][k + 1]
            L = math.hypot(x2 - x1, y2 - y1)
            ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
            assert L >= 0.05 and min(abs(ang), abs(ang - 45), abs(ang - 90), abs(ang - 135), abs(ang - 180)) < 1e-6, \
                "%s 腿%d 非 0/45/90 或过短" % (tg["name"], k)
            assert seg_ok(c, lid, fhole, x1, y1, x2, y2, net), "%s 腿%d 非法: %s" % (tg["name"], k, (x1, y1, x2, y2))
            legs.append([x1, y1, x2, y2])
        blocks += VIA_BLOCK.format(x=fmt(vx), y=fmt(vy), u=vid((vx, vy)))
        for (x1, y1, x2, y2) in legs:
            blocks += SEG_BLOCK.format(x1=fmt(x1), y1=fmt(y1), x2=fmt(x2), y2=fmt(y2), u=sid(x1, y1, x2, y2))
        ops.append(dict(target=tg["name"], ref=tg["src"][2], net=net, via=[vx, vy], span="F.Cu..In4.Cu",
                        size=0.35, drill=0.2, margin=round(m, 4), worst=blk, legs=legs))
    for o in ops:
        if o.get("status") == "already-present": continue
        print("OK %-4s %-6s via=(%.2f,%.2f) span裕度=%+.4f (%s) 腿=%d" % (
            o["target"], o["ref"], o["via"][0], o["via"][1], o["margin"], o["worst"], len(o["legs"])))
    if all(o.get("status") == "already-present" for o in ops):
        print("already-applied (idempotent no-op)")
        json.dump(dict(status="noop"), open(a.ledger, "w"), ensure_ascii=False, indent=1); return 0
    rec = dict(targets=ops)
    anchor = txt.index("\n\t(via\n") if "\n\t(via\n" in txt else txt.index("\t(segment\n")
    new = txt[:anchor + 1] + blocks + txt[anchor + 1:]
    # 新增 F→In4 孔须在 In1/In3 的 GND 面上取得 void ⇒ **必须重填 zone**（增量 12 同法）。
    import subprocess, shutil
    src_pro = re.sub(r"\.kicad_pcb$", ".kicad_pro", a.src)
    dst_pro = re.sub(r"\.kicad_pcb$", ".kicad_pro", a.out)
    pro_bytes = open(src_pro, "rb").read()
    tmp = a.out + ".tmp.kicad_pcb"
    open(tmp, "w", encoding="utf-8").write(new)
    open(re.sub(r"\.kicad_pcb$", ".kicad_pro", tmp), "wb").write(pro_bytes)
    r = subprocess.run([sys.executable, "-c",
                        "import pcbnew,sys;b=pcbnew.LoadBoard(sys.argv[1]);pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.Save(sys.argv[2])",
                        tmp, a.out], capture_output=True, text=True)
    open(dst_pro, "wb").write(pro_bytes)          # T-22：无条件恢复 dst pro
    for f in (tmp, re.sub(r"\.kicad_pcb$", ".kicad_pro", tmp)):
        if os.path.exists(f): os.remove(f)
    if r.returncode != 0:
        print("FILL FAIL", r.stderr[-400:]); return 2
    json.dump(dict(status="applied", out=a.out, ops=rec, conservation=dict(
        pure_addition=True, vias_new=len([o for o in ops if o.get("status") != "already-present"]),
        segs_new=sum(len(o["legs"]) for o in ops if o.get("status") != "already-present"),
        zone_refill=True,
        note="纯增：无删除、无改既有铜；孔类 = F.Cu..In4.Cu 盲孔 0.35/0.2（增量 12 同型）；落板后 **区域重填**（新增孔须在 In1/In3 GND 面取得 void）")),
        open(a.ledger, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
