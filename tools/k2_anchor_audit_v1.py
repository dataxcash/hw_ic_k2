#!/usr/bin/env python3
"""k2_anchor_audit_v1.py --- **出图件锚定审计闸**（#K2-449 sec.2.4 · `M-ENG-ORPHAN-BRIDGE-DISPOSAL` 的关账判据）。

WHY：两次机证（`R1358` 桥区 · `R1374` 衔接）——**无锚的加件会被链的「孤立铜处置」当孤岛清掉**。
本闸对**每一条加入件**判「是否**触到焊盘（pad）或既存铜（route）**」；**无锚即响亮失败**（不得静默出图）。

纯函数部分（`touches` / `audit`）供回归；板侧部分（`audit_board`）读真板。
"""
from __future__ import annotations

TOL = 1e-6


def _pt_in_bbox(p, bb, tol=TOL):
    return (bb[0] - tol) <= p[0] <= (bb[2] + tol) and (bb[1] - tol) <= p[1] <= (bb[3] + tol)


def touches(item, pads, routes, tol=TOL):
    """加入件是否锚定：任一端点落在**焊盘 bbox**内，或与**既存走线端点**重合。"""
    if item.get("kind") == "via":
        pt = tuple(item["at"])
        return any(_pt_in_bbox(pt, p, tol) for p in pads) or any(
            any(abs(pt[0] - r[0]) <= tol and abs(pt[1] - r[1]) <= tol for r in (rr["a"], rr["b"])) for rr in routes)
    for p in (tuple(item["a"]), tuple(item["b"])):
        if any(_pt_in_bbox(p, bb, tol) for bb in pads):
            return True
        for rr in routes:
            if rr.get("layer") and rr["layer"] != item.get("layer"):
                continue
            if any(abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol for q in (rr["a"], rr["b"])):
                return True
    return False


def audit(added, pads, routes, tol=TOL):
    """**簇判定**（#K2-449 sec.2.4 corrected）：把「加件 ＋ 既存走线 ＋ 焊盘」并成连通簇（重合端点；过孔连其层对；
    端点落在焊盘 bbox 内即接焊盘），**加件有锚 ⇔ 其簇含焊盘**。无锚 ⇒ `ok=False`（响亮失败 · 不得出图）。"""
    n = len(added)
    parent = list(range(n + len(routes) + len(pads)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    r0, p0 = n, n + len(routes)

    def ends(it):
        if it.get("kind") == "via":
            return [tuple(it["at"])]
        return [tuple(it["a"]), tuple(it["b"])]

    for i, it in enumerate(added):
        for pt in ends(it):
            for k, bb in enumerate(pads):
                if _pt_in_bbox(pt, bb, tol):
                    union(i, p0 + k)
            for j, rr in enumerate(routes):
                if it.get("kind") != "via" and rr.get("layer") and rr["layer"] != it.get("layer"):
                    continue
                if any(abs(pt[0] - q[0]) <= tol and abs(pt[1] - q[1]) <= tol for q in (rr["a"], rr["b"])):
                    union(i, r0 + j)
    for i in range(n):
        for j in range(i + 1, n):
            if any(abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol for a in ends(added[i]) for b in ends(added[j])):
                if added[i].get("kind") == "via" or added[j].get("kind") == "via" or added[i].get("layer") == added[j].get("layer"):
                    union(i, j)
    for j, rr in enumerate(routes):                    # 既存走线亦可接焊盘
        for pt in (rr["a"], rr["b"]):
            for k, bb in enumerate(pads):
                if _pt_in_bbox(pt, bb, tol):
                    union(r0 + j, p0 + k)
    # #K2-449 sec.2.4 refinement (R1386): the anchored roots are pads AND PRE-EXISTING (kept) copper - a dR port
    # stub's anchor is the KEPT OUTSIDE half-stub, not a pad, so pads alone over-flag every boundary piece.
    anchored_roots = {find(p0 + k) for k in range(len(pads))} | {find(r0 + j) for j in range(len(routes))}
    padless = [added[i] for i in range(n) if find(i) not in anchored_roots]
    return {"ok": not padless, "padless": padless, "n_added": n}


def audit_board(board, rect, added):
    """读真板：焊盘 bbox（区内全部网）＋ **既存铜**（区内，排除本次加入件所在网的自环由调用方保证）→ 逐件审。"""
    import pcbnew as P
    b = P.LoadBoard(board)
    pads = []
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            bb = pd.GetBoundingBox()
            pads.append([P.ToMM(bb.GetLeft()), P.ToMM(bb.GetTop()), P.ToMM(bb.GetRight()), P.ToMM(bb.GetBottom())])
    routes = []
    for t in b.GetTracks():
        a = (round(P.ToMM(t.GetStart().x), 4), round(P.ToMM(t.GetStart().y), 4))
        c = (round(P.ToMM(t.GetEnd().x), 4), round(P.ToMM(t.GetEnd().y), 4))
        if t.GetClass() != "PCB_VIA":
            routes.append({"layer": b.GetLayerName(t.GetLayer()), "a": a, "b": c})
    return audit(added, pads, routes)
