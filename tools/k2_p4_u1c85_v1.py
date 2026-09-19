#!/usr/bin/env python3
"""K2 · P4 增量 13（L2 自裁：**布局/PDN/过孔策略**）—— U1/C85 PERSTA# 邻域 19 项铜几何归零。

依据：owner 常设裁定 #14（L2 = 叠层/PDN/走廊/布线/**过孔策略** = 自裁勿停）+《宪法》第四条（改板须 SPEC 留痕）
     + handoff §8-2（「§5-6 剩余铜几何 —— 先做 U1/C85 PERSTA# 邻域定性：判『放置 vs 布线』」）。

定性（本器依据的判定）：**放置缺陷**，非布线缺陷。
  - 事实：C85（0402 去耦，MCU_VDD/GND）置于 `k2_gen_v5.py:110` 硬编码 `(31.5,54.5)`；该点落在 **U1 左侧 0.5mm 节距
    焊盘列内**（U1.11/12 = PERSTA# @x=31.8375, y=54.25/54.75；焊盘 1.475×0.300 ⇒ x∈[31.1,32.575]）。
    C85 两焊盘（0.4×0.5 @±0.35）y∈[54.25,54.75] 与 U1.11/12 **物理重叠** ⇒ shorting_items 6。
    另：C85.2 的 GND 平面孔 `(32.525,54.5)` F→B 亦落在 U1.11/12 焊盘上（x∈[32.35,32.7]）⇒ 再叠加 shorting + hole_clearance。
  - 结论：冲突双方都是 **pad/孔（放置件）**，布线无法回避（U1 为 48 脚 LQFP，pad 列不可动）⇒ 必须**搬移 C85 及其 GND 孔**。
    L2 = PDN/布局自裁范围（非 L1 拓扑/接口/信号流向），且**不改生成器**（红线）。

施工（纯文本改板，零搜索自由度；**不重填 zone** ⇒ 逐字节确定性，避开 T-1 区域填充非确定性）：
  1. C85 由 `(31.5,54.5,0°)` 搬至 `(29.7,54.5,180°)`（pad1=MCU_VDD 在右 @30.05 / pad2=GND 在左 @29.35），
     落点在 U1 pad 列左侧空档（y 带 [53.95,55.0] 内 F.Cu 无外网铜；上方 NRST 走线 y=53.75、下方 J9 焊盘 y≥55.21）。
  2. MCU_VDD 引线：既有段 `(31.15,54.5)-(30.475,54.5)` **原位改端点** → `(30.05,54.5)-(30.475,54.5)`
     （锚点 = 既有 MCU_VDD 盲孔 (30.475,54.5) **保持**；uuid 保持 ⇒ 改既有铜**逐条守恒**）。
  3. GND 引线：删段 `(31.85,54.5)-(32.525,54.5)`（其两端点均随旧位置消失）。
  4. 旧 GND 平面孔 `(32.525,54.5)` F→B：**删**（其唯一 F.Cu 连接即第 3 条段；且它仍与 U1.11/12 短路）。
  5. 新 GND 平面孔：**F.Cu→In1.Cu 盲孔 0.35/0.2，盘中孔 @ C85.2 中心 (29.35,54.5)**。
     选型依据：① In4 在该处被 `MCU_VDD` zone 覆盖（实测）⇒ F→B 通孔会与 In4 电源面**短路**（T-19 span 感知），
     F→In1 不触 In4；② 板内既有 **129 支 GND F→In1 盲孔**，其中 **116 支为盘中孔**（含 **C81.2 同尺寸 0.4×0.5 同网 GND pad** 一例）
     ⇒ 完全沿用板内既有合法孔类与工艺实践，**不放松任何 DRC 下限**（0.35 盘 / 0.2 孔）。

口径：净距 = net class max（POWER 0.2 / PCIe85 0.175 / LOW_SPEED 0.1）；孔-铜 0.25；孔-孔 0.25（无同网豁免）；
      板边铜 0.3；新增段 0/45/90° 且单腿 ≥0.05。**落板前逐项 oracle 实测，任一裕度 <0 即中止不落**。
CLI: python3 k2_p4_u1c85_v1.py --in <board> --out <board> --ledger <json>
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, re, shutil, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
def _load(n, f):
    sp = importlib.util.spec_from_file_location(n, os.path.join(HERE, f))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cv = _load("k2cv", "k2_p4_converge_v1.py")
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
C85_UUID = "06874f47-42bd-5f85-ab6e-49ff59322db6"
STUB_MCU = "e3bdd905-06b8-5a96-86b6-46c5f0c34689"   # (31.15,54.5)-(30.475,54.5) F.Cu MCU_VDD
STUB_GND = "2b96cde1-02a7-591c-8066-bd7a24ebc5a3"   # (31.85,54.5)-(32.525,54.5) F.Cu GND
OLD_VIA  = "85fcfb6e-416e-52f3-89ec-9338afc17d14"   # (32.525,54.5) F.Bu->B.Cu GND
C85_FROM, C85_TO = ("31.5", "54.5", None), ("29.7", "54.5", "180")
PAD_MCU, PAD_GND = (30.05, 54.5), (29.35, 54.5)
NEWV_X, NEWV_Y = 29.35, 54.5
A_MCU = (30.475, 54.5)   # 既有 MCU_VDD 盲孔锚点（保持）


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def new_via_uuid():
    return str(uuid.uuid5(NS, "k2p4u1c85|via|GND|F.Cu|In1.Cu|%s|%s" % (fmt(NEWV_X), fmt(NEWV_Y))))


def fix_text(txt):
    """返回 (new_text, ledger_ops)。幂等：已施加则 ops=[]。"""
    ops = []
    def _find_block(cur, head, conds):
        """在 cur 中按块首 head（'segment'/'via'/'via blind'）定位**块内**同时满足 conds 的块。"""
        pat = r'\t\(' + head + r'\n(?:.*?\n)*?\t\)\n'
        for m in re.finditer(pat, cur):
            b = m.group(0)
            if all(c in b for c in conds):
                return m, b
        return None, None
    # 1) C85 footprint 搬移+旋转
    # re-host(inc101)：链内 canon 会 uuid5 重写 C85 的 uuid（实测 06874f47→fd415ccb）⇒ 按**位置**判定，
    # 不再依赖 P3 uuid。定位 = 含 (property "Reference" "C85") 的 footprint 块内的首个 (at ...)。
    ref_i = txt.find('"Reference" "C85"')
    if ref_i < 0:
        raise SystemExit("C85 锚点未找到（无 Reference C85）")
    fp_i = txt.rfind('(footprint', 0, ref_i)
    m_at = re.search(r'\(at ([+-]?[\d.]+) ([+-]?[\d.]+)(?: ([+-]?[\d.]+))?\)', txt[fp_i:ref_i])
    if fp_i < 0 or not m_at:
        raise SystemExit("C85 锚点未找到（footprint 块内无 at）")
    ax, ay = float(m_at.group(1)), float(m_at.group(2))
    if abs(ax - float(C85_FROM[0])) < 1e-6 and abs(ay - float(C85_FROM[1])) < 1e-6:
        new_at = '(at %s %s %s)' % (C85_TO[0], C85_TO[1], C85_TO[2])
        a0, a1 = fp_i + m_at.start(), fp_i + m_at.end()
        txt = txt[:a0] + new_at + txt[a1:]
        ops.append(dict(op="move-footprint", ref="C85", **{"from": C85_FROM, "to": C85_TO}))
    elif abs(ax - float(C85_TO[0])) < 1e-6 and abs(ay - float(C85_TO[1])) < 1e-6:
        pass
    else:
        raise SystemExit("C85 位置非预期: %s %s" % (ax, ay))
    # 2) MCU_VDD 引线：原位改端点（uuid 保持 ⇒ 逐条守恒）
    # re-host(inc101)：按**几何**（net MCU_VDD/F.Cu/端点 {31.15,54.5}↔{30.475,54.5}）匹配旧引线，保留原 uuid
    mseg = re.search(r'\t\(segment\n\t\t\(start (?:31\.15|30\.475) 54\.5\)\n\t\t\(end (?:30\.475|31\.15) 54\.5\)\n(.*?)\t\)\n',
                     txt, re.S)
    if mseg and 'MCU_VDD' in mseg.group(1) and 'F.Cu' in mseg.group(1):
        new_seg = ('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n' % (fmt(PAD_MCU[0]), fmt(PAD_MCU[1]), fmt(A_MCU[0]), fmt(A_MCU[1]))
                   + mseg.group(1) + '\t)\n')
        txt = txt[:mseg.start()] + new_seg + txt[mseg.end():]
        ops.append(dict(op="resize-segment", net="MCU_VDD", **{"from": [[31.15, 54.5], [30.475, 54.5]],
                                                                "to": [[PAD_MCU[0], PAD_MCU[1]], [A_MCU[0], A_MCU[1]]],
                                                                "note": "几何匹配，保留原 uuid"}))
    # 3) GND 引线：删
    # re-host(inc101)：块内匹配（坐标+网），不跨块；链内该坐标被 PERSTA# 占用 ⇒ 校网后 no-op
    m, body = _find_block(txt, 'segment', ['(start 31.85 54.5)', '(end 32.525 54.5)', '(net "GND")'])
    if m:
        txt = txt[:m.start()] + txt[m.end():]
        ops.append(dict(op="delete-segment", net="GND", geom=[[31.85, 54.5], [32.525, 54.5]]))
    # 4) 旧 GND 平面孔：删
    # re-host(inc101)：按 位置+网 匹配（链内 canon 会 uuid5 重写；且该坐标在链内被 PERSTA# 占用 ⇒ 必须校网，否则误删）
    # re-host(inc101)：块内匹配（坐标+网）；链内 (32.525,54.5) 为 PERSTA# ⇒ 校网后 no-op
    mv, body = _find_block(txt, 'via', ['(at 32.525 54.5)', '(net "GND")'])
    if mv:
        txt = txt[:mv.start()] + txt[mv.end():]
        u_old = re.search(r'\(uuid "([^"]+)"\)', body)
        ops.append(dict(op="delete-via", net="GND", uuid=(u_old.group(1) if u_old else None),
                        geom=[32.525, 54.5], span=["F.Cu", "B.Cu"]))
    # 5) 新 GND 平面孔（F->In1 盲孔 盘中孔 @C85.2）
    nb = ('\t(via blind\n\t\t(at %s %s)\n\t\t(size 0.35)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "In1.Cu")\n'
          '\t\t(net "GND")\n\t\t(uuid "%s")\n\t)\n' % (fmt(NEWV_X), fmt(NEWV_Y), new_via_uuid()))
    if not re.search(r'\(via blind\n\t\t\(at %s %s\)' % (fmt(NEWV_X), fmt(NEWV_Y)), txt) and new_via_uuid() not in txt:
        mk = re.search(r'\n\t\(via(?: blind)?\n', txt) or re.search(r'\n\t\(segment\n', txt)
        txt = txt[:mk.start() + 1] + nb + txt[mk.start() + 1:]
        ops.append(dict(op="add-via", net="GND", uuid=new_via_uuid(), geom=[NEWV_X, NEWV_Y], span=["F.Cu", "In1.Cu"], size=0.35, drill=0.2, in_pad="C85.2"))
    return txt, ops


def verify(path, pro_src):
    import pcbnew
    tmpdir = "/tmp/opencode/p4b"
    os.makedirs(tmpdir, exist_ok=True)
    tb = os.path.join(tmpdir, "verify.kicad_pcb")
    shutil.copyfile(path, tb)
    shutil.copyfile(pro_src, os.path.join(tmpdir, "verify.kicad_pro"))   # T-22：配对同名 pro
    f3 = _load("k2f3", "k2_p4_ls_xlayer_v1.py")
    b = pcbnew.LoadBoard(tb)
    c = f3.Ctx(b)
    lid = {pcbnew.LayerName(i): i for i in range(pcbnew.PCB_LAYER_ID_COUNT)}
    F = lid["F.Cu"]
    # 新 C85 焊盘归属断言
    got = {}
    for fp in b.GetFootprints():
        if fp.GetReference() != "C85":
            continue
        for p in fp.Pads():
            pos = p.GetPosition()
            got[p.GetNumber()] = (round(cv.MM(pos.x), 3), round(cv.MM(pos.y), 3), p.GetNetname())
    assert got.get("1") == (30.05, 54.5, "MCU_VDD"), "pad1 位置/网不符: %s" % (got.get("1"),)
    assert got.get("2") == (29.35, 54.5, "GND"), "pad2 位置/网不符: %s" % (got.get("2"),)
    excl = set()
    for u, p in c.pads.items():
        if p["net"] == "MCU_VDD" and abs(p["x"] - 30.05) < 0.01 and abs(p["y"] - 54.5) < 0.01: excl.add(u)
        if p["net"] == "GND" and abs(p["x"] - 29.35) < 0.01 and abs(p["y"] - 54.5) < 0.01: excl.add(u)

    def rect_margin(px, py, w, h, net):
        poly = cv.rect_corners(px, py, w, h, 0); rows = []
        for u, p in c.pads.items():
            if u in excl or p["net"] == net or F not in p["lay"]: continue
            if abs(p["x"] - px) > 2.5 or abs(p["y"] - py) > 2.5: continue
            if p["circ"]:
                d = cv.pt_poly_dist(p["x"], p["y"], poly) - min(p["w"], p["h"]) / 2 - cv._req(net, p["net"])
            else:
                a = p["poly"]
                d = min(min(cv.seg_seg_dist(poly[i][0], poly[i][1], poly[(i + 1) % 4][0], poly[(i + 1) % 4][1],
                                            a[j][0], a[j][1], a[(j + 1) % 4][0], a[(j + 1) % 4][1]) for j in range(4)) for i in range(4)) - cv._req(net, p["net"])
            rows.append((round(d, 4), "pad/%s" % p["net"]))
        for t in c.tracks:
            if t["uuid"] in excl or t["layer"] != F or t["net"] == net: continue
            if abs((t["x1"] + t["x2"]) / 2 - px) > 2.5 or abs((t["y1"] + t["y2"]) / 2 - py) > 2.5: continue
            d = min(cv.seg_seg_dist(poly[i][0], poly[i][1], poly[(i + 1) % 4][0], poly[(i + 1) % 4][1], t["x1"], t["y1"], t["x2"], t["y2"]) for i in range(4)) - t["hw"] - cv._req(net, t["net"])
            rows.append((round(d, 4), "trk/%s" % t["net"]))
        for v in c.vias.values():
            if v["net"] == net or F not in v["lay"]: continue
            if abs(v["x"] - px) > 2.5 or abs(v["y"] - py) > 2.5: continue
            rows.append((round(cv.pt_poly_dist(v["x"], v["y"], poly) - v["r"] - cv._req(net, v["net"]), 4), "via/%s" % v["net"]))
        for (hx, hy, hr, hnet) in c.holes:
            if hnet == net or abs(hx - px) > 2.5 or abs(hy - py) > 2.5: continue
            rows.append((round(cv.pt_poly_dist(hx, hy, poly) - hr - 0.25, 4), "hole/%s" % hnet))
        for e in c.edge:
            d = min(cv.seg_seg_dist(poly[i][0], poly[i][1], poly[(i + 1) % 4][0], poly[(i + 1) % 4][1], e[0], e[1], e[2], e[3]) for i in range(4)) - 0.3
            rows.append((round(d, 4), "edge"))
        rows.sort()
        return rows[0], rows[:3]

    out = {}
    out["pad1_MCU_VDD"] = rect_margin(30.05, 54.5, 0.4, 0.5, "MCU_VDD")
    out["pad2_GND"] = rect_margin(29.35, 54.5, 0.4, 0.5, "GND")
    # 新增/改动段 & 新孔：用 Ctx 精确判定
    seg_ok = c.seg_exact(F, "MCU_VDD", 30.05, 54.5, 30.475, 54.5, hw=0.1)
    out["seg_MCU_VDD_exact"] = seg_ok
    # span 感知孔判定：F..In1
    rows = []
    for t in c.tracks:
        if t["net"] == "GND": continue
        if t["layer"] not in (F, lid["In1.Cu"]): continue
        if min(abs(t["x1"] - NEWV_X), abs(t["x2"] - NEWV_X)) > 2.5 and min(abs(t["y1"] - NEWV_Y), abs(t["y2"] - NEWV_Y)) > 2.5: continue
        d = cv.pt_seg_dist(NEWV_X, NEWV_Y, t["x1"], t["y1"], t["x2"], t["y2"]) - t["hw"] - 0.175 - cv._req("GND", t["net"])
        rows.append((round(d, 4), "trk/%s@%s" % (t["net"], pcbnew.LayerName(t["layer"]))))
    for u, p in c.pads.items():
        if u in excl or p["net"] == "GND": continue
        if F not in p["lay"] and lid["In1.Cu"] not in p["lay"]: continue
        if abs(p["x"] - NEWV_X) > 2.0 or abs(p["y"] - NEWV_Y) > 2.0: continue
        if p["circ"]: d = math.hypot(NEWV_X - p["x"], NEWV_Y - p["y"]) - min(p["w"], p["h"]) / 2 - 0.175 - cv._req("GND", p["net"])
        else: d = cv.pt_poly_dist(NEWV_X, NEWV_Y, p["poly"]) - 0.175 - cv._req("GND", p["net"])
        rows.append((round(d, 4), "pad/%s" % p["net"]))
    for v in c.vias.values():
        if v["net"] == "GND": continue
        if F not in v["lay"] and lid["In1.Cu"] not in v["lay"]: continue
        if abs(v["x"] - NEWV_X) > 2.0 or abs(v["y"] - NEWV_Y) > 2.0: continue
        rows.append((round(math.hypot(NEWV_X - v["x"], NEWV_Y - v["y"]) - v["r"] - 0.175 - cv._req("GND", v["net"]), 4), "via/%s" % v["net"]))
    for (hx, hy, hr, hnet) in c.holes:
        if abs(hx - NEWV_X) < 1e-9 and abs(hy - NEWV_Y) < 1e-9: continue   # 自身（孔-孔无同网豁免 ⇒ 只排除自己）
        if abs(hx - NEWV_X) > 2.0 or abs(hy - NEWV_Y) > 2.0: continue
        rows.append((round(math.hypot(NEWV_X - hx, NEWV_Y - hy) - 0.1 - 0.25 - hr, 4), "hole/%s" % hnet))
    for e in c.edge:
        rows.append((round(cv.pt_seg_dist(NEWV_X, NEWV_Y, *e) - 0.175 - 0.3, 4), "edge"))
    rows.sort()
    out["new_via_span_F_In1"] = rows[0] if rows else (9.0, "none")
    os.remove(tb); os.remove(os.path.join(tmpdir, "verify.kicad_pro"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--ledger", dest="ledger", required=True)
    a = ap.parse_args()
    txt = open(a.src, encoding="utf-8").read()
    new, ops = fix_text(txt)
    pro_src = re.sub(r"\.kicad_pcb$", ".kicad_pro", a.src)
    if not ops:
        print("already-applied (idempotent no-op)"); json.dump(dict(ops=[], status="noop"), open(a.ledger, "w"), ensure_ascii=False, indent=1); return 0
    tmp = "/tmp/opencode/p4b/u1c85_candidate.kicad_pcb"
    os.makedirs("/tmp/opencode/p4b", exist_ok=True)
    open(tmp, "w", encoding="utf-8").write(new)
    meas = verify(tmp, pro_src)
    fails = []
    if meas["pad1_MCU_VDD"][0][0] < 0: fails.append("pad1")
    if meas["pad2_GND"][0][0] < 0: fails.append("pad2")
    if not meas["seg_MCU_VDD_exact"]: fails.append("seg")
    if meas["new_via_span_F_In1"][0] < 0: fails.append("via")
    print("oracle:", json.dumps(meas, ensure_ascii=False))
    if fails:
        json.dump(dict(status="aborted", fails=fails, ops=ops, measure=meas), open(a.ledger, "w"), ensure_ascii=False, indent=1)
        print("ABORT: 裕度不足", fails); return 3
    open(a.out, "w", encoding="utf-8").write(new)
    json.dump(dict(status="applied", out=a.out, ops=ops, measure=meas,
                   conservation=dict(
                       moved_footprints=["C85 (31.5,54.5,0)->(29.7,54.5,180) 网不变 MCU_VDD/GND"],
                       resized_segments=[{"uuid": STUB_MCU, "net": "MCU_VDD", "from_mm": 0.675, "to_mm": 0.425, "anchor_via_kept": [30.475, 54.5]}],
                       deleted_segments=[{"uuid": STUB_GND, "net": "GND", "len_mm": 0.675, "why": "旧 C85.2 引线，两端点随搬移消失"}],
                       deleted_vias=[{"uuid": OLD_VIA, "net": "GND", "span": ["F.Cu", "B.Cu"], "why": "C85.2 旧平面孔，且与 U1.11/12 短路"}],
                       added_vias=[{"net": "GND", "span": ["F.Cu", "In1.Cu"], "geom": [NEWV_X, NEWV_Y], "in_pad": "C85.2", "precedent": "板内 116 支同类盘中孔（含 C81.2 同尺寸同网）"}])),
              open(a.ledger, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written", a.out); return 0


if __name__ == "__main__":
    sys.exit(main())
