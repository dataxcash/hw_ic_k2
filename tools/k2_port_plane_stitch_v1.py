#!/usr/bin/env python3
"""k2_port_plane_stitch_v1.py --- **图纸落地器**（#K2-439 sec.2.10「强制换手段」的实现件 · 实现 sec.16.3 五线图纸）。

按**冻结定值**在清区场上**确定性**加两类铜 —— **零搜索 · 零试参 · 零迭代**：

  * `port_stub` —— **区界端口落点**：一条**止于 ∂R 之内**的短走线（同网同层），把「界外半桩」接进框内，
    并给迷宫一个**框内起步格**（治 `no-free-start-node`）。
  * `via` —— **电源平面缝合**：一个过孔把焊盘／碎段接到其**内层平面**（治 `P3V3`／`P3V3_AUX` 的平面缺失）。
  * `track` —— 一般**确定性短桩**（如图纸线 5 的 F.Cu 桩）。

C6 安全（机证口径）：走线**止于** ∂R ⇒ `outside_geometry` 不增；过孔落在 ∂R **之内或线上**（`pt_in` 含边界）
⇒ 同样不增（本仓在册实践：链自身的缝合过孔就落在 `x=51.5`，两跑 C6 均 = 0）。

CLI: python3 tools/k2_port_plane_stitch_v1.py --board B --rect x0,y0,x1,y1 --spec S.json --out O [--json-out J]
"""
from __future__ import annotations
import argparse, json, os, statistics, sys

LM = {"F.Cu": None}          # filled at runtime from the board


def _default_width(b, net, layer, P):
    """**确定性**：取该网在该层已有走线宽度的中位数（无则 0.25）。"""
    ws = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetname() != net:
            continue
        if b.GetLayerName(t.GetLayer()) == layer:
            ws.append(round(P.ToMM(t.GetWidth()), 4))
    return float(statistics.median(ws)) if ws else 0.25


def validate(spec, rect):
    """**纯函数 · 无 pcbnew**：逐条校验落点是否**在 ∂R 之内** —— 过孔须在内或线上；走线两端须在内或线上。
    返回 refusal 列表（空 = 全部可加）。确定性、零搜索。"""
    x0, y0, x1, y1 = [float(v) for v in rect]

    def _in(pt):
        return (x0 - 1e-6 <= pt[0] <= x1 + 1e-6) and (y0 - 1e-6 <= pt[1] <= y1 + 1e-6)

    out = []
    for i, L in enumerate(spec.get("lines") or []):
        it = {"line": L.get("n", i + 1), "kind": L.get("kind"), "net": L.get("net")}
        if L.get("kind") == "via":
            if not _in([float(v) for v in L["at"]]):
                out.append(dict(it, why="via outside dR", at=L["at"]))
        else:
            for k in (("near", "far") if L.get("kind") == "port_stub" else ("a", "b")):
                if not _in([float(v) for v in L[k]]):
                    out.append(dict(it, why="endpoint outside dR", at=L[k]))
                    break
    return out


def stitch(board, rect, spec, out):
    import pcbnew as P
    b = P.LoadBoard(board)
    layers = {b.GetLayerName(l): l for l in b.GetLayerSet().CuStack()}
    x0, y0, x1, y1 = [float(v) for v in rect]
    report = {"artifact": "k2_port_plane_stitch_v1", "board": board, "rect": [x0, y0, x1, y1],
              "added": [], "refused": [], "OWNER-ITEMS": 0}
    report["refused"].extend(validate(spec, rect))
    _refused_lines = {r.get("line") for r in report["refused"]}
    for i, L in enumerate(spec.get("lines") or []):
        kind, net = L.get("kind"), L.get("net")
        if L.get("n", i + 1) in _refused_lines:
            continue
        item = {"line": L.get("n", i + 1), "kind": kind, "net": net}
        _n = b.FindNet(net)
        if _n is None:
            report["refused"].append(dict(item, why="unknown net"))
            continue
        code = _n.GetNetCode()
        if kind == "via":
            at = [float(v) for v in L["at"]]
            if not (x0 - 1e-6 <= at[0] <= x1 + 1e-6 and y0 - 1e-6 <= at[1] <= y1 + 1e-6):
                report["refused"].append(dict(item, why="via outside dR", at=at))
                continue
            la, lb = L["layers"]
            if la not in layers or lb not in layers:
                report["refused"].append(dict(item, why="unknown layer pair", layers=L["layers"]))
                continue
            vi = P.PCB_VIA(b)
            vi.SetPosition(P.VECTOR2I(P.FromMM(at[0]), P.FromMM(at[1])))
            vi.SetWidth(P.FromMM(float(L.get("size", 0.45)))); vi.SetDrill(P.FromMM(float(L.get("drill", 0.25))))
            vt = L.get("via_type") or ("through" if (la == "F.Cu" and lb == "B.Cu") else "blind")
            vi.SetViaType(P.VIATYPE_THROUGH if vt == "through" else (P.VIATYPE_BURIED if vt == "buried" else P.VIATYPE_BLIND))
            vi.SetLayerPair(layers[la], layers[lb]); vi.SetNetCode(code)
            b.Add(vi)
            report["added"].append(dict(item, at=at, layers=L["layers"], via_type=vt, size=float(L.get("size", 0.45))))
        else:
            layer = L["layer"]
            if layer not in layers:
                report["refused"].append(dict(item, why="unknown layer", layer=layer))
                continue
            a = [float(v) for v in (L["near"] if kind == "port_stub" else L["a"])]
            c = [float(v) for v in (L["far"] if kind == "port_stub" else L["b"])]
            for p in (a, c):
                if not (x0 - 1e-6 <= p[0] <= x1 + 1e-6 and y0 - 1e-6 <= p[1] <= y1 + 1e-6):
                    report["refused"].append(dict(item, why="endpoint outside dR", at=p))
                    break
            else:
                w = float(L.get("width") or _default_width(b, net, layer, P))
                tr = P.PCB_TRACK(b)
                tr.SetStart(P.VECTOR2I(P.FromMM(a[0]), P.FromMM(a[1])))
                tr.SetEnd(P.VECTOR2I(P.FromMM(c[0]), P.FromMM(c[1])))
                tr.SetWidth(P.FromMM(w)); tr.SetLayer(layers[layer]); tr.SetNetCode(code)
                b.Add(tr)
                report["added"].append(dict(item, a=a, b=c, layer=layer, width_mm=w))
    P.SaveBoard(out, b)
    report["n_added"] = len(report["added"]); report["n_refused"] = len(report["refused"])
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--rect", required=True)
    ap.add_argument("--spec", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    rect = [float(v) for v in a.rect.split(",")]
    spec = json.load(open(a.spec, encoding="utf-8"))
    rep = stitch(a.board, rect, spec, a.out)
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0 if rep["n_refused"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
