#!/usr/bin/env python3
"""k2_joint_alloc_v1.py --- **块级联合分配**（#K2-425 §四 · 换手段不换目标）。

取代「各网各自重解→抢位」：**一次性、确定性、零搜索**地把块内各网分配到**互不相交的通道**（保序），
通道内再布线。抄样板政策（REF-CASE-LIBRARY A1：先分通道，后布线）。
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys


def joint_channel_assignment(nets, block_rect, pitch=0.6, gap=0.2):
    """**纯函数 · 确定性 · 零搜索**：把 `nets`（保序）分配到 `block_rect` 内**互不相交**的通道。
    通道沿 x 等宽切分（扣 gap）；每条 = {net, channel, lane_x}。保序 ⇒ 不相交 ⇒ **无抢位**。"""
    x0, y0, x1, y1 = [float(v) for v in block_rect]
    n = len(nets)
    if n <= 0:
        return []
    w = ((x1 - x0) - (n - 1) * gap) / n
    out = []
    for i, net in enumerate(nets):
        cx0 = x0 + i * (w + gap)
        out.append({"net": net, "order": i, "channel": [round(cx0, 4), round(y0, 4), round(cx0 + w, 4), round(y1, 4)],
                    "lane_x": round(cx0 + w / 2.0, 4)})
    return out


def content_aware_joint_allocation(nets_pts, block_rect, occupants, clearance=0.20, need=0.60, pad=0.4):
    """**内容感知 · 确定性 · 零搜索**（#K2-427 §四.1 · 取代等宽盲切）：
    按**给定网序**，每网取"含其全部端点、避开（占位者⊕净空）的最大净空子矩"作其通道；**与已分配通道重叠 ⇒ 具名 `OVERLAP`**（绝不静默重叠）。
    `nets_pts`=[[(net,x,y,layer),...],...]（按序）。返回 [{net, channel|None, status, capacity_mm, need_mm}]。"""
    import importlib.util as _iu, os as _os
    _sp = _iu.spec_from_file_location("k2rdj", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "k2_corridor_redraw_v1.py"))
    rd = _iu.module_from_spec(_sp); _sp.loader.exec_module(rd)
    taken, out = [], []
    for row in nets_pts:
        net = row[0][0]
        xs = [p[1] for p in row]; ys = [p[2] for p in row]
        sub = None
        for _pd in (pad, pad * 2, pad * 4):
            box = (min(xs) - _pd, min(ys) - _pd, max(xs) + _pd, max(ys) + _pd)
            _s, _ = rd.clear_subrect_containing_pts(box, occupants, clearance, [(p[1], p[2]) for p in row])
            if _s:
                sub = _s
                if min(_s[2] - _s[0], _s[3] - _s[1]) >= need - 1e-9:
                    break
        cap = min(sub[2] - sub[0], sub[3] - sub[1]) if sub else 0.0
        ovl = bool(sub) and any(not (sub[2] <= t[0] or t[2] <= sub[0] or sub[3] <= t[1] or t[3] <= sub[1]) for t in taken)
        status = ("OK" if (sub and cap >= need - 1e-9 and not ovl) else
                  ("OVERLAP" if ovl else ("NARROW" if sub else "UNPLACEABLE")))
        if sub and not ovl:
            taken.append(sub)
        out.append({"net": net, "channel": list(sub) if sub else None, "status": status,
                    "capacity_mm": round(cap, 4), "need_mm": need})
    return out


def artifact_hash16(rep):
    return hashlib.sha256(json.dumps(rep, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nets", required=True, help="comma-ordered net names")
    ap.add_argument("--rect", required=True, help="x0,y0,x1,y1")
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    nets = [x for x in a.nets.split(",") if x]
    rep = {"artifact": "k2_joint_channel_assignment_v1",
           "channels": joint_channel_assignment(nets, tuple(float(v) for v in a.rect.split(","))),
           "policy": "coordinated single-pass allocation (no competition), per REF-CASE-LIBRARY A1"}
    rep["artifact_hash16"] = artifact_hash16(rep["channels"])
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
