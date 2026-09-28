"""M1 · `eda_eng netplan` --- 拆线清单（#K2-360 §一 M1）。

输入：板 + 放置增量（refs + delta）       输出：**受影响网清单** + **待拆段/孔清单**
判据：清单须**零多零漏**。本节实现"受影响网"来自**板**（footprint pads），并由**真源网表**（独立路径）交叉核。

设计（确定性 · 零搜索）：
  affected_nets(board, refs)  : 逐 ref 取 pad→netname（去空、去重、排序）
  teardown_items(board, nets) : 逐网枚举全部 track（层/起止/宽）与 via（坐标/钻孔/层对），canonical 排序
  plan(board, refs, delta)    : 组合上面两者 + 被移 ref 的 pad 位移（旧→新）
"""
from __future__ import annotations
import json, os


def _pcbnew():
    import pcbnew as P
    return P


def affected_nets(board, refs):
    P = _pcbnew()
    b = P.LoadBoard(board)
    want = set(refs)
    nets = set()
    for fp in b.GetFootprints():
        if fp.GetReference() in want:
            for p in fp.Pads():
                n = p.GetNetname()
                if n:
                    nets.add(n)
    return sorted(nets)


def teardown_items(board, nets):
    P = _pcbnew()
    b = P.LoadBoard(board)
    nm = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    per = {n: {"tracks": [], "vias": []} for n in nets}
    for t in b.GetTracks():
        name = nm.get(t.GetNetCode(), "")
        if name not in per:
            continue
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            per[name]["vias"].append({"at": [round(P.ToMM(pos.x), 4), round(P.ToMM(pos.y), 4)],
                                      "drill_mm": round(P.ToMM(t.GetDrill()), 4),
                                      "layers": [b.GetLayerName(l) for l in t.GetLayerSet().Seq()]})
        else:
            s, e = t.GetStart(), t.GetEnd()
            per[name]["tracks"].append({"layer": t.GetLayerName(),
                                        "a": [round(P.ToMM(s.x), 4), round(P.ToMM(s.y), 4)],
                                        "b": [round(P.ToMM(e.x), 4), round(P.ToMM(e.y), 4)],
                                        "width_mm": round(P.ToMM(t.GetWidth()), 4)})
    for n in per:
        per[n]["tracks"].sort(key=lambda r: (r["layer"], r["a"], r["b"], r["width_mm"]))
        per[n]["vias"].sort(key=lambda r: (r["at"], r["drill_mm"]))
    return per


def moved_pads(board, refs, delta_mm):
    P = _pcbnew()
    b = P.LoadBoard(board)
    want = set(refs)
    out = []
    for fp in b.GetFootprints():
        if fp.GetReference() not in want:
            continue
        for p in fp.Pads():
            pos = p.GetPosition()
            old = [round(P.ToMM(pos.x), 4), round(P.ToMM(pos.y), 4)]
            out.append({"ref": fp.GetReference(), "pad": p.GetNumber(),
                        "net": p.GetNetname(),
                        "old": old,
                        "new": [round(old[0] + delta_mm[0], 4), round(old[1] + delta_mm[1], 4)]})
    out.sort(key=lambda r: (r["ref"], r["pad"]))
    return out


def plan(board, refs, delta_mm):
    nets = affected_nets(board, refs)
    per = teardown_items(board, nets)
    pads = moved_pads(board, refs, delta_mm)
    return {"artifact": "eda_eng_netplan", "board": board, "refs": list(refs), "delta_mm": list(delta_mm),
            "affected_nets": nets, "n_affected_nets": len(nets),
            "teardown": per,
            "teardown_totals": {"tracks": sum(len(v["tracks"]) for v in per.values()),
                                "vias": sum(len(v["vias"]) for v in per.values())},
            "moved_pads": pads, "n_moved_pads": len(pads),
            "touched_nets_outside_affected": 0,     # by construction: only the affected nets are enumerated
            "rule": "#K2-360 M1: the list must be exact (zero extra, zero missing); nets come from the board's "
                    "pad->net map and are cross-checked against the true-source netlist in the tests"}
