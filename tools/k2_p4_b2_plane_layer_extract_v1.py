#!/usr/bin/env python3
"""K2 · C-LAYER-RECOG（#K2-136 §三.1 授权之「修工具」）—— **平面层可表示**。
纯文本解析 `.kicad_pcb`（**不需 pcbnew**，本机未装）：抽取铜**铺铜（zone fill）**之
`(net "…")` · `(layer "…")` · `(filled_polygon … (pts …))`，按层栅格化为 **net-id 图**。
只读板件（不改任何工程件）；输出至指定路径（临时仅 /tmp/opencode）。
用法: python3 k2_p4_b2_plane_layer_extract_v1.py <board.kicad_pcb> <out_prefix> [cell_mm]
"""
import sys, json, hashlib, math, re
import numpy as np
from PIL import Image, ImageDraw

LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]


def s_blocks(text, key):
    """返回 key 之平衡括号块（含内容），忽略字符串内括号。"""
    out = []
    pat = "(" + key
    i = 0
    while True:
        i = text.find(pat, i)
        if i < 0:
            break
        k = i
        depth = 0
        instr = False
        while k < len(text):
            c = text[k]
            if instr:
                if c == '"' and text[k - 1] != "\\":
                    instr = False
            elif c == '"':
                instr = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        out.append(text[i:k + 1])
        i = k + 1
    return out


def parse_pts(blk):
    pts = []
    for m in re.finditer(r"\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)", blk):
        pts.append((float(m.group(1)), float(m.group(2))))
    return pts


def main():
    board, prefix = sys.argv[1], sys.argv[2]
    cell = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
    text = open(board, encoding="utf-8").read()
    zones = s_blocks(text, "zone")
    pours = {}
    for z in zones:
        mnet = re.search(r'\(net\s+"([^"]*)"\)', z)
        mlay = re.search(r'\(layer\s+"([^"]+)"\)', z)
        if not mnet or not mlay:
            continue
        net, lay = mnet.group(1), mlay.group(1)
        if lay not in LAYERS:
            continue
        for fp in s_blocks(z, "filled_polygon"):
            ml2 = re.search(r'\(layer\s+"([^"]+)"\)', fp)
            L = ml2.group(1) if ml2 else lay
            if L not in LAYERS:
                continue
            pts = parse_pts(fp)
            if len(pts) >= 3:
                pours.setdefault(L, {}).setdefault(net, []).append(pts)
    # 栅格范围 = 全体铺铜之外接框 + 2mm
    if not pours:
        raise SystemExit("no pours found")
    X0 = min(p[0] for L in pours for n in pours[L] for poly in pours[L][n] for p in poly) - 2
    Y0 = min(p[1] for L in pours for n in pours[L] for poly in pours[L][n] for p in poly) - 2
    X1 = max(p[0] for L in pours for n in pours[L] for poly in pours[L][n] for p in poly) + 2
    Y1 = max(p[1] for L in pours for n in pours[L] for poly in pours[L][n] for p in poly) + 2
    NX, NY = int(math.ceil((X1 - X0) / cell)) + 1, int(math.ceil((Y1 - Y0) / cell)) + 1
    netid = {"": 0}
    info = {"schema": 1, "artifact": "k2_p4_b2_plane_layer_extract_v1", "board": board, "cell_mm": cell,
            "bbox": [X0, Y0, X1, Y1], "NX": NX, "NY": NY, "layers": {}, "source_sha256": hashlib.sha256(text.encode()).hexdigest()}
    for L in LAYERS:
        if L not in pours:
            info["layers"][L] = {"nets": {}, "n_polys": 0}
            continue
        img = Image.new("I", (NX, NY), 0)
        dr = ImageDraw.Draw(img)
        cnt = 0
        for net, polys in pours[L].items():
            if net not in netid:
                netid[net] = len(netid)
            nid = netid[net]
            for poly in polys:
                px = [((x - X0) / cell, (y - Y0) / cell) for x, y in poly]
                dr.polygon(px, fill=nid, outline=nid)
                cnt += 1
        arr = np.array(img, dtype=np.int32)
        np.save("%s_%s.npy" % (prefix, L.replace(".", "_")), arr)
        info["layers"][L] = {"nets": {n: netid[n] for n in pours[L]}, "n_polys": cnt,
                             "coverage_mm2": round(float((arr > 0).sum()) * cell * cell, 2)}
    info["netid"] = netid
    json.dump(info, open(prefix + "_planes.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({L: {"n_polys": info["layers"][L]["n_polys"], "coverage_mm2": info["layers"][L]["coverage_mm2"],
                          "nets": list(info["layers"][L]["nets"].keys())}
                      for L in LAYERS if info["layers"][L]["n_polys"]}, ensure_ascii=False, indent=1))
    print("source_sha256:", info["source_sha256"][:16], "  cell:", cell, "  grid:", NX, "x", NY)


if __name__ == "__main__":
    main()
