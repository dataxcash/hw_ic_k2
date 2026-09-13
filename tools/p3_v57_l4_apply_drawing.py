#!/usr/bin/env python3
"""P3 v57 L4 — 图纸直构（drawing-only construction）。

零设计决策：坐标/层/过孔全部来自 W3 图纸（`m13_v57_w3_joint_assignment.json` 的 34 页
`nodes`/`vias` 与 REFCLK `path`）。PCB **原样消费图纸**：复制冻结 PCB → 删该网旧 track/via
→ 按图纸逐段落 track + 逐层变点落 via。**不改图纸**（图纸 sha 作为输入校验）。

产出：
  - m13_v57_l4_construction.json   (per-net 段/过孔，逐字节 = 图纸几何；供 L4 验证器消费)
  - <dst>.kicad_pcb                (--board 给定时；新建版本化板，冻结板不动)
CLI: python3 p3_v57_l4_apply_drawing.py [--board] [--out-board PATH] [--escape-domain PATH]

CO-37：`--escape-domain` 时按版本化域工件注入**具名 rule area**（非铜、非布线；供 `.kicad_dru` 条件引用），
实现 SPEC `escape_transition_zone`（ECN-001）；域工件与判据变更须版本化（见 CO-25 §3 / CO-37 裁定）。
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, uuid
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
MAIN = STEP2 / __import__("os").environ.get("L4_MAIN", "m13_v57_w3_joint_assignment.json")
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
OUT = STEP2 / __import__("os").environ.get("L4_OUT", "m13_v57_l4_construction.json")
SRC_PCB = K2 / "k2_v4_8L.kicad_pcb"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-5.json"   # CO-68: 分层线宽口径
DST_PCB = K2 / "k2_v4_8L.l4.kicad_pcb"
PHYS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]  # LID.1 8L top->bottom
LIDX = {n: i for i, n in enumerate(PHYS)}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def collapse(nodes):
    """W3 per-point-layer node list -> (points, seg_layers, vias)。
    同 XY 的连续/重复层变点**合并为一支 via**（layers=[min_layer,max_layer]）——
    物理等价（同点叠层），且消除 DFM holes_co_located（CO-17 §4-2 / CO-18）。"""
    pts = [[nodes[0][0], nodes[0][1]]]; seg = []; cur = nodes[0][2]
    seen = {}

    def note(x, y, L):
        k = (x, y); i = LIDX[L]
        if k in seen:
            seen[k][0] = min(seen[k][0], i); seen[k][1] = max(seen[k][1], i)
        else:
            seen[k] = [i, i]

    note(nodes[0][0], nodes[0][1], cur)
    for x, y, L in nodes[1:]:
        if abs(x - pts[-1][0]) < 1e-9 and abs(y - pts[-1][1]) < 1e-9:
            note(x, y, L); cur = L; continue
        seg.append(cur); pts.append([x, y])
        note(x, y, cur); note(x, y, L); cur = L
    vias = [{"xy": [k[0], k[1]], "layers": [PHYS[v[0]], PHYS[v[1]]]}
            for k, v in seen.items() if v[1] > v[0]]
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
            rv = pg["refclk"]                                  # ROOT-21: P/N 差分对 + 正确网名 (O3)
            for pol in ("P", "N"):
                net = rv["nets"][pol]
                segs.setdefault(net, []); vias.setdefault(net, [])
                if rv.get("nodes", {}).get(pol):               # CO-40 ECS-001：3D 节点（含换层）
                    pts, segL, vs = collapse(rv["nodes"][pol])
                    for i in range(len(segL)):
                        segs[net].append({"layer": segL[i], "a": pts[i], "b": pts[i + 1]})
                    vias[net] += vs
                    continue
                pth = rv["paths"][pol]["path"]                 # 兼容：无 nodes 时按 F.Cu 直段
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


_CANON_TYPES = ("segment", "via", "zone")     # CO-49: pcbnew 保存顺序/uuid 会漂移的三类块
_UUID_RE = re.compile(r'\(uuid "[^"]*"\)')


def _root_children(txt: str):
    """根块 (kicad_pcb ...) 的一级子块 [start,end)（括号/字符串安全扫描）。"""
    i = txt.index("(")
    depth = 0
    start = None
    out = []
    instr = esc = False
    for j in range(i, len(txt)):
        ch = txt[j]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
            continue
        if ch == '"':
            instr = True
            continue
        if ch == "(":
            depth += 1
            if depth == 2:
                start = j
        elif ch == ")":
            if depth == 2 and start is not None:
                out.append((start, j + 1))
                start = None
            depth -= 1
    return out


def canonicalize_board(path: Path) -> int:
    """CO-49：令 L4 板**字节可复现**（解除 pcbnew 的非确定性）。

    实测：pcbnew 保存时仅 `segment`/`via`/`zone` 块的**顺序**与 **uuid** 每次重建漂移；
    其余块（footprint/pad/gr_line/setup/...）逐字节稳定，且这三类块的连续 run 结构稳定。
    本步：① 在每个连续同类 run 内按「去 uuid 文本」排序；② 以该文本派生确定性 uuid5。
    只触碰上述三类块；不改几何/网/层。返回被规范化块数。幂等。
    """
    txt = path.read_text(encoding="utf-8")
    ch = _root_children(txt)
    if len(ch) < 2:
        return 0
    sep = txt[ch[0][1]:ch[1][0]]
    if {txt[ch[i][1]:ch[i + 1][0]] for i in range(len(ch) - 1)} != {sep}:
        raise RuntimeError("CO-49: non-uniform child separators")
    blocks = [txt[a:b] for a, b in ch]
    types = [re.match(r"\(\s*([a-z_]+)", blk).group(1) for blk in blocks]
    out = []
    i, n, ncanon = 0, len(blocks), 0
    while i < n:
        if types[i] in _CANON_TYPES:
            j = i
            while j < n and types[j] == types[i]:
                j += 1
            run = []
            for blk in blocks[i:j]:
                canon = _UUID_RE.sub("", blk)
                det = uuid.uuid5(uuid.NAMESPACE_URL, canon)
                run.append((canon, _UUID_RE.sub('(uuid "%s")' % det, blk)))
                ncanon += 1
            out.extend(blk for _, blk in sorted(run, key=lambda q: q[0]))
            i = j
        else:
            out.append(blocks[i])
            i += 1
    path.write_text(txt[:ch[0][0]] + sep.join(out) + txt[ch[-1][1]:], encoding="utf-8")
    return ncanon


def apply_board(rec, src: Path, dst: Path, domain=None):
    import pcbnew                                                       # noqa: E402
    WIDTH = json.loads(SPEC.read_text(encoding="utf-8"))["impedance"]["width_mm_by_layer"]  # CO-68
    b = pcbnew.LoadBoard(str(src))
    LM = {n: getattr(pcbnew, n.replace(".", "_")) for n in PHYS}   # LID.1 8L (incl. In5/In6)
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
            tr.SetStart(vec(*s["a"])); tr.SetEnd(vec(*s["b"])); tr.SetWidth(mm(WIDTH.get(s["layer"], 0.205)))
            tr.SetLayer(LM[s["layer"]]); tr.SetNetCode(netcode(net)); b.Add(tr)
        for v in rec["vias"][net]:
            vi = pcbnew.PCB_VIA(b)
            vi.SetPosition(vec(*v["xy"])); vi.SetDrill(mm(0.2)); vi.SetWidth(mm(0.35))
            lo, hi = v["layers"]
            i0, i1 = sorted((LIDX[lo], LIDX[hi]))
            through = (i0 == 0 and i1 == len(PHYS) - 1)
            vi.SetViaType(pcbnew.VIATYPE_THROUGH if through else pcbnew.VIATYPE_BLIND)
            vi.SetLayerPair(LM[lo], LM[hi])
            ls = pcbnew.LSET()
            for ln in PHYS[i0:i1 + 1]:
                ls.AddLayer(LM[ln])
            vi.SetLayerSet(ls); vi.SetNetCode(netcode(net)); b.Add(vi)
    n_rule_areas = 0
    if domain:                                          # CO-37: SPEC 逃逸区 named rule areas（非铜）
        for d in domain["domains"]:
            x0, y0, x1, y1 = d["rect_mm"]
            z = pcbnew.ZONE(b)
            z.SetIsRuleArea(True); z.SetZoneName(d["id"]); z.SetLayer(LM[d["layer"]])
            for setter in ("SetDoNotAllowCopperPour", "SetDoNotAllowVias", "SetDoNotAllowTracks",
                           "SetDoNotAllowPads", "SetDoNotAllowFootprints", "SetDoNotAllowZoneFills"):
                if hasattr(z, setter):
                    getattr(z, setter)(False)
            o = z.Outline(); o.NewOutline()
            for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                o.Append(mm(x), mm(y))
            b.Add(z); n_rule_areas += 1
    pcbnew.SaveBoard(str(dst), b)
    n_canon = canonicalize_board(dst)                     # CO-49: 字节可复现（确定性顺序 + uuid）
    return {"dst": str(dst.relative_to(K2)), "dst_sha256": sha(dst), "n_rule_areas": n_rule_areas,
            "canonicalized_blocks": n_canon}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", action="store_true")
    ap.add_argument("--out-board", default=None)
    ap.add_argument("--escape-domain", default=None)
    args = ap.parse_args()
    art = json.loads(MAIN.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rec = build(art, manifest)
    rec["application"] = None
    domain = None
    if args.escape_domain:
        dp = Path(args.escape_domain)
        domain = json.loads(dp.read_text(encoding="utf-8"))
        rec["escape_domain"] = {"artifact": domain["artifact"], "revision": domain["revision"],
                                "sha256": sha(dp), "escape_clearance_mm": domain["escape_clearance_mm"],
                                "excluded_nets": domain.get("excluded_nets", []),
                                "n_domains": len(domain["domains"]),
                                "note": "CO-37：SPEC 逃逸区 rule area（非铜）；域外维持 shop 0.175/0.2"}
    if args.board:
        dst = Path(args.out_board) if args.out_board else DST_PCB
        rec["application"] = apply_board(rec, SRC_PCB, dst, domain)
        rec["authority"]["src_pcb_sha256"] = sha(SRC_PCB)
    OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"L4: nets={rec['tally']['n_nets']} segs={rec['tally']['n_segments']} "
          f"vias={rec['tally']['n_vias']} board={rec['application'] and rec['application']['dst']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
