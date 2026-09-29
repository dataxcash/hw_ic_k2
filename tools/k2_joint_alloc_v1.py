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
