#!/usr/bin/env python3
"""P3 v57 L4 验证器 — 图纸直构的独立复核（应跑在 KiCad python 下：pcbnew）。

判据：
  L4-A 图纸只读：construction.authority.drawing_sha256 == 现盘图纸 sha；冻结源 PCB sha 未变。
  L4-B 几何=图纸：由图纸**独立重算** collapse(points,seg_layers,vias) 逐段 == construction。
  L4-C 链连续：每网段序列首尾相接（端点匹配，容差 1e-6）；层变点有 via。
  L4-D 端点处方：每 data 网首点=chip pad、末点=conn pad（manifest）；REFCLK 首/末=witness 锚。
  L4-E 板已消费：新板 track/via（pcbnew 读）逐条 == construction 记录（网名、层、端点）。
产出 m13_v57_l4_validation.json。
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
MAIN = STEP2 / "m13_v57_w3_joint_assignment.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
REC = STEP2 / "m13_v57_l4_construction.json"
SRC_PCB = K2 / "k2_v4_8L.kicad_pcb"
DST_PCB = K2 / "k2_v4_8L.l4.kicad_pcb"
TOL = 1e-6
PHYS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]  # LID.1 8L top->bottom
LIDX = {n: i for i, n in enumerate(PHYS)}


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def collapse(nodes):
    pts = [[nodes[0][0], nodes[0][1]]]; seg = []; vias = []
    cur = nodes[0][2]
    for x, y, L in nodes[1:]:
        if abs(x - pts[-1][0]) < 1e-9 and abs(y - pts[-1][1]) < 1e-9:
            if L != cur:
                lo, hi = sorted((cur, L), key=lambda n: LIDX[n])
                vias.append({"xy": [x, y], "layers": [lo, hi]}); cur = L
            continue
        seg.append(cur); pts.append([x, y]); cur = L
    return pts, seg, vias


def main() -> int:
    art = json.loads(MAIN.read_text(encoding="utf-8"))
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rec = json.loads(REC.read_text(encoding="utf-8"))
    viol = []

    # L4-A
    if rec["authority"]["drawing_sha256"] != sha(MAIN):
        viol.append({"V": "L4-A", "why": "drawing sha != recorded"})
    if sha(SRC_PCB) != "fb07d25ac426ff84905200a9af88e04dd9e6b9216986c4f4459fd7d556a88c34" and not sha(SRC_PCB).startswith("fb07d25ac426ff84905200a9af88e04dd9e6b9216986c4f4459fd7d556a88c34"):
        viol.append({"V": "L4-A", "why": "frozen src pcb changed", "sha": sha(SRC_PCB)[:16]})

    # L4-B independent recompute
    mp = {p["page_id"]: p for p in man["pages"]}
    exp_segs, exp_vias = {}, {}
    for pg in art["pages"]:
        if pg["kind"] == "data":
            f = mp[pg["page_id"]]
            for pol in ("P", "N"):
                net = f["nets"][pol]
                pts, segL, vs = collapse(pg["nodes"][pol])
                exp_segs.setdefault(net, []); exp_vias.setdefault(net, [])
                for i in range(len(segL)):
                    exp_segs[net].append({"layer": segL[i], "a": pts[i], "b": pts[i + 1]})
                exp_vias[net] += vs
        else:
            rv = pg["refclk"]
            for pol in ("P", "N"):
                net = rv["nets"][pol]; pth = rv["paths"][pol]["path"]
                exp_segs.setdefault(net, []); exp_vias.setdefault(net, [])
                for i in range(len(pth) - 1):
                    exp_segs[net].append({"layer": rv["layer"], "a": pth[i], "b": pth[i + 1]})
    def key(s): return (s["layer"], tuple(round(v, 5) for v in s["a"]), tuple(round(v, 5) for v in s["b"]))
    for net in set(exp_segs) | set(rec["segments"]):
        a = sorted(key(s) for s in exp_segs.get(net, []))
        b = sorted(key(s) for s in rec["segments"].get(net, []))
        if a != b:
            viol.append({"V": "L4-B", "net": net, "exp": len(a), "got": len(b)})
    def vkey(v): return (tuple(round(q, 5) for q in v["xy"]), tuple(v["layers"]))
    for net in set(exp_vias) | set(rec["vias"]):
        a = sorted(vkey(v) for v in exp_vias.get(net, []))
        b = sorted(vkey(v) for v in rec["vias"].get(net, []))
        if a != b:
            viol.append({"V": "L4-B-via", "net": net, "exp": len(a), "got": len(b)})

    # L4-C chain continuity + layer-change vias
    for net, segs in rec["segments"].items():
        if not segs:
            continue
        # adjacency: every point must have degree pattern of a simple chain
        from collections import defaultdict
        deg = defaultdict(int)
        for s in segs:
            rag = lambda p: (round(p[0], 5), round(p[1], 5))  # noqa: E731
            deg[rag(s["a"])] += 1; deg[rag(s["b"])] += 1
        ends = [p for p, d in deg.items() if d == 1]
        others = [p for p, d in deg.items() if d not in (1, 2)]
        if others or len(ends) not in (0, 2):
            viol.append({"V": "L4-C", "net": net, "ends": len(ends), "odd": len(others)})
    for net, vs in rec["vias"].items():
        # every via must sit on >=2 segments of different layers
        for v in vs:
            p = (round(v["xy"][0], 5), round(v["xy"][1], 5))
            lyr = {s["layer"] for s in rec["segments"].get(net, [])
                   if (round(s["a"][0], 5), round(s["a"][1], 5)) == p or (round(s["b"][0], 5), round(s["b"][1], 5)) == p}
            if len(lyr) < 2:
                viol.append({"V": "L4-C-via", "net": net, "via": v, "layers": sorted(lyr)})

    # L4-D endpoints
    for pg in art["pages"]:
        if pg["kind"] == "data":
            f = mp[pg["page_id"]]
            for pol in ("P", "N"):
                net = f["nets"][pol]
                segs = rec["segments"].get(net, [])
                if not segs:
                    viol.append({"V": "L4-D", "net": net, "why": "no segs"}); continue
                # chain ends from degree
                from collections import defaultdict
                deg = defaultdict(int)
                for s in segs:
                    rag = lambda p: (round(p[0], 5), round(p[1], 5))  # noqa: E731
                    deg[rag(s["a"])] += 1; deg[rag(s["b"])] += 1
                ends = {p for p, d in deg.items() if d == 1}
                chip = tuple(round(v, 5) for v in f["anchors"]["chip"][pol]["pad_global"])
                conn = tuple(round(v, 5) for v in f["anchors"]["conn"][pol]["pad_global"])
                if chip not in ends or conn not in ends:
                    viol.append({"V": "L4-D", "net": net, "chip_in": chip in ends, "conn_in": conn in ends})
        else:
            rv = pg["refclk"]
            for pol in ("P", "N"):
                net = rv["nets"][pol]; pp = rv["paths"][pol]; pth = pp["path"]
                if (round(pth[0][0], 5), round(pth[0][1], 5)) != tuple(round(v, 5) for v in pp["j2_pad"]) or \
                   (round(pth[-1][0], 5), round(pth[-1][1], 5)) != tuple(round(v, 5) for v in pp["far_pad"]):
                    viol.append({"V": "L4-D-refclk", "net": net, "pol": pol})

    # L4-E board consumption
    board_ok = False
    if DST_PCB.exists():
        try:
            import pcbnew
            b = pcbnew.LoadBoard(str(DST_PCB))
            got = {}
            for t in b.GetTracks():
                k = t.GetClass()
                if k == "PCB_TRACK":
                    name = t.GetNetname(); L = b.GetLayerName(t.GetLayer())
                    a = (round(pcbnew.ToMM(t.GetStart().x), 5), round(pcbnew.ToMM(t.GetStart().y), 5))
                    c = (round(pcbnew.ToMM(t.GetEnd().x), 5), round(pcbnew.ToMM(t.GetEnd().y), 5))
                    got.setdefault(name, []).append((L, a, c))
            miss = 0
            for net, segs in rec["segments"].items():
                g = sorted(got.get(net, []))
                e = sorted((s["layer"], tuple(round(v, 5) for v in s["a"]), tuple(round(v, 5) for v in s["b"])) for s in segs)
                # board stores a->b possibly reversed; normalise
                e = sorted((l, tuple(sorted((p, q)))) for l, p, q in e)
                g2 = sorted((l, tuple(sorted((p, q)))) for l, p, q in g)
                if e != g2:
                    miss += 1
            # vias: position + physical layer span
            gv = {}
            for t2 in b.GetTracks():
                if t2.GetClass() == "PCB_VIA":
                    ls = t2.GetLayerSet()
                    cu = [i for i in range(pcbnew.PCB_LAYER_ID_COUNT)
                          if ls.Contains(i) and b.GetLayerName(i) in LIDX]
                    span = (min(cu, key=lambda i: LIDX[b.GetLayerName(i)]),
                            max(cu, key=lambda i: LIDX[b.GetLayerName(i)]))
                    spann = (b.GetLayerName(span[0]), b.GetLayerName(span[1]))
                    gv.setdefault(t2.GetNetname(), []).append(
                        ((round(pcbnew.ToMM(t2.GetPosition().x), 5), round(pcbnew.ToMM(t2.GetPosition().y), 5)), spann))
            vmiss = 0
            for net, vs in rec["vias"].items():
                a = sorted(((round(v["xy"][0], 5), round(v["xy"][1], 5)), tuple(v["layers"])) for v in vs)
                c = sorted(gv.get(net, []))
                if a != c:
                    vmiss += 1
            board_ok = (miss == 0 and vmiss == 0)
            if not board_ok:
                viol.append({"V": "L4-E", "why": "board != record", "nets_mismatch": miss, "via_nets_mismatch": vmiss})
        except Exception as ex:                                          # noqa: BLE001
            viol.append({"V": "L4-E", "why": "pcbnew load failed", "err": str(ex)[:120]})
    else:
        viol.append({"V": "L4-E", "why": "dst board missing"})

    out = {"artifact": "m13_v57_l4_validation", "schema": 1, "revision": "L4-V1",
           "verdict": "PASS" if not viol else "FAIL",
           "checks": {"L4-A": not any(v["V"] == "L4-A" for v in viol),
                      "L4-B": not any(v["V"].startswith("L4-B") for v in viol),
                      "L4-C": not any(v["V"].startswith("L4-C") for v in viol),
                      "L4-D": not any(v["V"].startswith("L4-D") for v in viol),
                      "L4-E": board_ok},
           "n_violations": len(viol), "violations": viol[:40],
           "fingerprints": {"drawing_sha256": sha(MAIN), "construction_sha256": sha(REC),
                            "src_pcb_sha256": sha(SRC_PCB), "dst_pcb_sha256": sha(DST_PCB) if DST_PCB.exists() else None},
           "tally": rec["tally"]}
    (STEP2 / "m13_v57_l4_validation.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print("L4 VAL: verdict=%s checks=%s viol=%d" % (out["verdict"], out["checks"], out["n_violations"]))
    return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
