#!/usr/bin/env python3
"""k2_seal_rip_plan_v1.py —— #K2-463 **照图施工**（`_v2` 争用消解件）之**确定性拆件计划器**（纯函数 · 无 pcbnew）。

输入：`_v2` 声明（`band_geometry`／`items_to_yield[].bbox_mm` ＋ `preserve_list`）＋ 板上件清单
      `[{net,layer,x1,y1,x2,y2,width}]`。
输出：**清单式拆除计划**（`{"teardown": {net: {"tracks": [(net,layer,x1,y1,x2,y2,width), ...]}}}` · 即
      `tools/eda_eng/ripup.py::execute` 之输入格式）＋ `n` ＋ `refused`。
纪律（承 #K2-463 §2.2 · 零搜索 · 有界 · 原子）：
· **只撤声明带内**、**只撤 `items_to_yield` 具名之网**、**只撤该层**；`preserve_list` 之网**一律不动**；
· `from_where`／`to_where` 等由图纸件负责（本器只做「按图点名」）；
· **空计划 ⇒ 响亮失败**（`n==0` ⇒ `refused` 具名），绝不静默空跑。
"""
from __future__ import annotations


def _hits(item, box):
    x0, y0, x1, y1 = box
    ix0, ix1 = sorted((float(item["x1"]), float(item["x2"])))
    iy0, iy1 = sorted((float(item["y1"]), float(item["y2"])))
    return not (ix1 < x0 or ix0 > x1 or iy1 < y0 or iy0 > y1)


def rip_plan(band, yield_specs, board_items):
    """`band` ＝ `(x0,y0,x1,y1)`；`yield_specs` ＝ `[{"net":..,"layer":..,"bbox_mm":[..]}]`；
    返回 `{"teardown","n","refused","band"}`。"""
    keep = {s["net"] for s in (yield_specs[0].get("preserve") or [])} if yield_specs else set()
    out, n, refused = {}, 0, []
    for spec in yield_specs:
        net, layer = spec.get("net"), spec.get("layer")
        box = tuple(float(v) for v in (spec.get("bbox_mm") or band))
        if net in keep:
            refused.append({"net": net, "why": "net is listed as PRESERVE - never rip"})
            continue
        hits = [it for it in board_items
                if it.get("net") == net and it.get("layer") == layer and _hits(it, box)]
        if not hits:
            refused.append({"net": net, "why": "no item of this net/layer intersects the declared box"})
            continue
        out.setdefault(net, {"tracks": []})
        for it in sorted(hits, key=lambda z: (round(float(z["x1"]), 4), round(float(z["y1"]), 4),
                                              round(float(z["x2"]), 4), round(float(z["y2"]), 4))):
            out[net]["tracks"].append((net, layer, float(it["x1"]), float(it["y1"]),
                                       float(it["x2"]), float(it["y2"]), float(it.get("width", 0.2))))
            n += 1
    if n == 0:
        return {"teardown": {}, "n": 0, "refused": refused or [{"why": "empty plan"}], "band": list(band),
                "ok": False, "why": "NO-YIELD-ITEMS: the drawing yielded nothing to rip (fail-closed, never a silent no-op)"}
    return {"teardown": out, "n": n, "refused": refused, "band": list(band), "ok": True, "why": None}
