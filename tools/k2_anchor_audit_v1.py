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
    """**响亮失败**：返回 `{"ok", "padless":[...]}`；`ok=False` ⇒ 存在无锚加件（不得出图）。"""
    padless = [it for it in added if not touches(it, pads, routes, tol)]
    return {"ok": not padless, "padless": padless, "n_added": len(added)}


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
