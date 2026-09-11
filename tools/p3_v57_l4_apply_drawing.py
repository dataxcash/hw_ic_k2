#!/usr/bin/env python3
"""P3 v57 L4 — 图纸直构（drawing-only construction）。

零设计决策：坐标/层/过孔全部来自 W3 图纸（`m13_v57_w3_joint_assignment.json` 的 34 页
`nodes`/`vias` 与 REFCLK `path`）。PCB **原样消费图纸**：复制冻结 PCB → 删该网旧 track/via
→ 按图纸逐段落 track + 逐层变点落 via。**不改图纸**（图纸 sha 作为输入校验）。

产出：
  - m13_v57_l4_construction.json   (per-net 段/过孔，逐字节 = 图纸几何；供 L4 验证器消费)
  - <dst>.kicad_pcb                (--board 给定时；新建版本化板，冻结板不动)
CLI: python3 p3_v57_l4_apply_drawing.py [--board] [--out-board PATH]
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
MAIN = STEP2 / "m13_v57_w3_joint_assignment.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
OUT = STEP2 / "m13_v57_l4_construction.json"
SRC_PCB = K2 / "k2_v4.kicad_pcb"
DST_PCB = K2 / "k2_v4.l4.kicad_pcb"
LAYER_SET = ["F.Cu", "In2.Cu", "B.Cu"]


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def collapse(nodes):
    """W3 per-point-layer node list -> (points, seg_layers, vias)（层变点=过孔）。"""
    pts = [[nodes[0][0], nodes[0][1]]]; seg = []; vias = []
    cur = nodes[0][2]
    for x, y, L in nodes[1:]:
        if abs(x - pts[-1][0]) < 1e-9 and abs(y - pts[-1][1]) < 1e-9:
            if L != cur:
                vias.append([x, y]); cur = L
            continue
        seg.append(cur); pts.append([x, y]); cur = L
    return pts, seg, vias


def build(art, manifest):
    mp = {p["page_id"]: p for p in manifest["pages"]}
    segs, vias = {}, {}
    for pg in art["pages"]:
        if pg["kind"] == "data":
            f = mp[pg["page_id"]]
            for pol in ("P", "N"):
                net = f["nets"][pol]
                pts, segL, vs = collapse(pg["nodes"][pol])
                segs.setdefault(net, []); vias.setdefault(net, [])
                for i in range(len(segL)):
                    segs[net].append({"layer": segL[i], "a": pts[i], "b": pts[i + 1]})
                vias[net] += vs
        elif pg["kind"] == "refclk":
            rv = pg["refclk"]; net = pg["page_id"]
            pth = rv["path"]
            segs.setdefault(net, []); vias.setdefault(net, [])
            for i in range(len(pth) - 1):
                segs[net].append({"layer": rv["layer"], "a": pth[i], "b": pth[i + 1]})
    nets = sorted(set(segs) | set(vias))
    return {"artifact": "m13_v57_l4_construction", "schema": 1, "revision": "L4-A1",
            "authority": {"drawing": str(MAIN.relative_to(K2)), "drawing_rev": art["revision"],
                          "drawing_sha256": sha(MAIN), "design_decisions": 0},
            "nets": nets, "segments": {n: segs.get(n, []) for n in nets},
            "vias": {n: vias.get(n, []) for n in nets},
            "tally": {"n_nets": len(nets), "n_segments": sum(len(v) for v in segs.values()),
                      "n_vias": sum(len(v) for v in vias.values())}}


def apply_board(rec, src: Path, dst: Path):
    import pcbnew                                                       # noqa: E402
    b = pcbnew.LoadBoard(str(src))
    LM = {"F.Cu": pcbnew.F_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}
    mm = pcbnew.FromMM
    vec = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))                    # noqa: E731
    cache = {}
    def netcode(name):
        if name in cache:
            return cache[name]
        n = b.FindNet(name)
        if n is not None and hasattr(n, "GetNetCode") and n.GetNetCode() > 0:
            cache[name] = n.GetNetCode(); return cache[name]
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); cache[name] = ni.GetNetCode(); return cache[name]
    nets = set(rec["nets"])
    for t in list(b.GetTracks()):
        try:
            if t.GetNetname() in nets:
                b.Remove(t)
        except Exception:                                              # noqa: BLE001
            pass
    for net in rec["nets"]:
        for s in rec["segments"][net]:
            tr = pcbnew.PCB_TRACK(b)
            tr.SetStart(vec(*s["a"])); tr.SetEnd(vec(*s["b"])); tr.SetWidth(mm(0.205))
            tr.SetLayer(LM[s["layer"]]); tr.SetNetCode(netcode(net)); b.Add(tr)
        for v in rec["vias"][net]:
            vi = pcbnew.PCB_VIA(b)
            vi.SetPosition(vec(*v)); vi.SetDrill(mm(0.2)); vi.SetWidth(mm(0.35))
            ls = pcbnew.LSET()
            for ln in ("F.Cu", "In2.Cu", "B.Cu"):
                ls.AddLayer(LM[ln])
            vi.SetLayerSet(ls); vi.SetNetCode(netcode(net)); b.Add(vi)
    pcbnew.SaveBoard(str(dst), b)
    return {"dst": str(dst.relative_to(K2)), "dst_sha256": sha(dst)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", action="store_true")
    ap.add_argument("--out-board", default=None)
    args = ap.parse_args()
    art = json.loads(MAIN.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rec = build(art, manifest)
    rec["application"] = None
    if args.board:
        dst = Path(args.out_board) if args.out_board else DST_PCB
        rec["application"] = apply_board(rec, SRC_PCB, dst)
        rec["authority"]["src_pcb_sha256"] = sha(SRC_PCB)
    OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"L4: nets={rec['tally']['n_nets']} segs={rec['tally']['n_segments']} "
          f"vias={rec['tally']['n_vias']} board={rec['application'] and rec['application']['dst']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
