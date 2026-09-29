#!/usr/bin/env python3
"""k2_joint_channel_alloc_v1.py --- **联合（成组）通道分配内核**（#K2-450 sec.2.4/2.6 · 换手段的实现件）。

WHY（机证根因 · `R1394` 守恒计数：容量 12862 ≫ 需求 257）：框内**不是**没空间，而是**逐网顺序分配**把自由空间切碎 ⇒
**谁最后被服务谁饿死**（残余轮转三轮实证）。本内核把「**一次算出互不相交的通道**」做成**纯函数**：
  * `sequential(...)` —— 旧手段：各网**各取自身跨度**（可**互相重叠**）⇒ 用于 **RED**（同域必现饿死）；
  * `joint(...)` —— 新手段：在走廊内**一次性**把各网跨度**排成互不相交**的槽（保序 · 确定性 · 零搜索）。
`starved(...)` 给出「被别的通道挤住」的网名（**响亮** · 不静默）。
"""
from __future__ import annotations


def _span_w(seg):
    return seg[1] - seg[0]


def sequential(demands, gap=0.0):
    """旧手段（RED）：每网**各取自身跨度**，不互让。返回 {net: (lo,hi)}。"""
    return {d["net"]: (d["lo"], d["hi"]) for d in demands}


def overlaps(chans, gap=0.0):
    """返回**互相重叠**（间距 < gap）的网名对列表（确定性顺序）。"""
    items = sorted(chans.items())
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (n1, a), (n2, b) = items[i], items[j]
            if not (a[1] + gap <= b[0] or b[1] + gap <= a[0]):
                out.append((n1, n2))
    return out


def starved(chans, gap=0.0):
    """被挤住的网（任一重叠对中的网名 · 去重排序）。空 ⇒ 无饿死。"""
    bad = set()
    for a, b in overlaps(chans, gap):
        bad.add(a); bad.add(b)
    return sorted(bad)


def joint(demands, span, gap=0.20):
    """新手段（GREEN）：**一次性联合分配** —— 按「网名排序」固定优先序，把各网跨度**收窄到最小宽度后**
    在 `span` 内**顺序排放**，两两之间留 `gap`；排不下者**具名**返回。确定性 · 零搜索 · 保序。"""
    lo0, hi0 = span
    out, cur, unsat = {}, lo0, []
    for d in sorted(demands, key=lambda x: x["net"]):
        w = max(_span_w((d["lo"], d["hi"])), d.get("min_w", 0.20))
        if cur + w > hi0 + 1e-9:
            unsat.append(d["net"]); continue
        out[d["net"]] = (cur, cur + w); cur += w + gap
    return out, unsat
