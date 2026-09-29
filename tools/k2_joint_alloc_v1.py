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
    """`occupants` 可为 **list**（适用全体）或 **dict {net:[bbox,...]}** —— 后者**逐网排除本网自己的铜**（防自阻塞）。"""
    """**内容感知 · 确定性 · 零搜索**（#K2-427 §四.1 · 取代等宽盲切）：
    按**给定网序**，每网取"含其全部端点、避开（占位者⊕净空）的最大净空子矩"作其通道；**与已分配通道重叠 ⇒ 具名 `OVERLAP`**（绝不静默重叠）。
    `nets_pts`=[[(net,x,y,layer),...],...]（按序）。返回 [{net, channel|None, status, capacity_mm, need_mm}]。"""
    import importlib.util as _iu, os as _os
    _sp = _iu.spec_from_file_location("k2rdj", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "k2_corridor_redraw_v1.py"))
    rd = _iu.module_from_spec(_sp); _sp.loader.exec_module(rd)
    taken, out = [], []
    for row in nets_pts:
        net = row[0][0]
        if isinstance(occupants, dict):                     # PER-NET: exclude the net's own copper (R1206-fix family)
            occ = [bb for n, bbs in occupants.items() if n != net for bb in bbs]
        else:
            occ = occupants
        xs = [p[1] for p in row]; ys = [p[2] for p in row]
        # **组合 R1210 让位（精确近边）**：先把覆盖本网端点的他网铜按确定性让位序平移，再重画（R1222 pad 阶梯）
        _epl = _iu.spec_from_file_location("k2ep", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "k2_endpoint_reach_planner_v1.py"))
        epl = _iu.module_from_spec(_epl); _epl.loader.exec_module(epl)
        _pts = [(p[1], p[2]) for p in row]
        _blk = [bb for bb in occ if any(bb[0] - clearance - 1e-9 <= x <= bb[2] + clearance + 1e-9
                                        and bb[1] - clearance - 1e-9 <= y <= bb[3] + clearance + 1e-9 for (x, y) in _pts)]
        _seq = epl.yield_sequence((min(_pts), max(_pts)), [{"net": "_%d" % i, "bbox": bb} for i, bb in enumerate(_blk)], clearance)
        _moved = epl.apply_yields([{"net": "_%d" % i, "bbox": bb} for i, bb in enumerate(_blk)], _seq)
        occ2 = [bb for bb in occ if bb not in _blk] + _moved
        sub = None
        for _pd in (pad, pad * 2, pad * 4):
            box = (min(xs) - _pd, min(ys) - _pd, max(xs) + _pd, max(ys) + _pd)
            _s, _ = rd.clear_subrect_containing_pts(box, occ2, clearance, [(p[1], p[2]) for p in row])
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


def joint_allocation_by_row(board, drc, rect, clearance=0.20, need=0.60):
    """**按排分组的内容感知分配**（#K2-427 §四.1：样板 group fanout）—— 与 R1220/R1222 同口径的实现（逐排：让位＋pad 阶梯重画＋逐排守恒）。
    委托在册 `k2_block_relayout_gen_v1.plan_from_board`（单一实现，不另起一套），只取 `corridors` 作为"逐通道"读数。"""
    import importlib.util as _iu, os as _os
    _sp = _iu.spec_from_file_location("k2br", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "k2_block_relayout_gen_v1.py"))
    br = _iu.module_from_spec(_sp); _sp.loader.exec_module(br)
    rep = br.plan_from_board(board, drc, rect, clearance, need)
    return [{"net": r["nets"][0] if r["nets"] else "?", "row": r["row"], "channel": r["corridor_after_yield"] or r["corridor"],
             "status": ("OK" if r["conservation"]["pass"] else ("OK_BY_YIELD" if r["conservation_after_yield"]["pass"] else "BLOCKED")),
             "capacity_mm": (r["conservation_after_yield"] or r["conservation"])["capacity_mm"], "need_mm": need,
             "nets": r["nets"]} for r in rep["corridors"]]


def channel_including_reach(row, own_boxes, reach=0.5, pad=0.4):
    """**确定性 · 零搜索 · 冻结定值**（#K2-430 §三.1）：通道 ＝ 含「该排端点」∪「该网在端点邻近的**自己那段铜**」的最小盒
    （`reach`＝邻近阈值）。端点自身可达格在**本网铜上**，故把本网铜纳入 ⇒ 通道不再切断可达格（对治 `no-free-start-free`）。
    返回 `[x0,y0,x1,y1]`（**定值**，同输入恒同输出）。"""
    xs = [p[1] for p in row]; ys = [p[2] for p in row]
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    for bb in own_boxes:
        if not (bb[2] < x0 - reach or bb[0] > x1 + reach or bb[3] < y0 - reach or bb[1] > y1 + reach):
            x0, y0 = min(x0, bb[0] - pad), min(y0, bb[1] - pad)
            x1, y1 = max(x1, bb[2] + pad), max(y1, bb[3] + pad)
    return [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)]


def channels_arg(board, drc, rect, clearance=0.20, need=0.60, band=2.0, pad=0.4, reach=0.5):
    """**单一来源**（#K2-431 §二.6 fix 2/3）：产 `--channels` 串 —— 逐排分组 → 每网的**reach-纳入冻结通道**
    （端点 ∪ 本网铜）。确定性 · 零搜索；供链路与干跑**同一口径**。"""
    import importlib.util as _iu, os as _os, collections as _c, json as _j
    _R = _os.path.dirname(_os.path.abspath(__file__))
    def _m(n, f):
        sp = _iu.spec_from_file_location(n, _os.path.join(_R, f)); m = _iu.module_from_spec(sp); sp.loader.exec_module(m); return m
    AUD, DEV, BR = _m("ka2", "k2_corridor_occupancy_audit_v1.py"), _m("kd2", "k2_deviation_gen_v1.py"), _m("kb2", "k2_block_relayout_gen_v1.py")
    eps = []
    for pr in DEV.pairs(_j.load(open(drc, encoding="utf-8"))):
        for p_ in (pr["p1"], pr["p2"]):
            c = DEV._clamp(p_, rect); eps.append((pr["net"], c[0], c[1], pr["layers"][0]))
    rows = BR.group_by_row(eps, band)
    byn = _c.defaultdict(list)
    for o in AUD.occupant_rects(__import__("pcbnew"), ["F.Cu", "In5.Cu"], "__x__", clearance) if False else []:
        pass
    import pcbnew as _P
    b = _P.LoadBoard(board)
    for o in AUD.occupant_rects(b, ["F.Cu", "In5.Cu"], "__x__", clearance):
        byn[o["net"]].append(o["bbox"])
    parts = []
    for rw in rows:
        nets = {p[0] for p in rw}
        own = [bb for n, bbs in byn.items() if n in nets for bb in bbs]
        ch = channel_including_reach(rw, own, reach, pad)
        rs = ",".join("%.4f" % v for v in ch)
        for n in nets:
            parts.append("%s:%s" % (n, rs))
    return ";".join(parts)


def channels_arg_by_block(board, drc, rect, clearance=0.20):
    """**K-2＋K-3 接链用**（#K2-434 · 确定性 · 零搜索）：把 `--channels` 由**功能分块＋多块协同计划**产出 ——
    每网按其**功能族的目标框**（K-3 计划）作通道（再与其本网端点框并集）。失败退回 `channels_arg()`。"""
    import importlib.util as _iu, os as _os, json as _j
    _R = _os.path.dirname(_os.path.abspath(__file__))
    def _m(n, f):
        sp = _iu.spec_from_file_location(n, _os.path.join(_R, f)); m = _iu.module_from_spec(sp); sp.loader.exec_module(m); return m
    FB, DEV = _m("kfb2", "k2_functional_block_v1.py"), _m("kd3", "k2_deviation_gen_v1.py")
    eps = []
    for pr in DEV.pairs(_j.load(open(drc, encoding="utf-8"))):
        for p_ in (pr["p1"], pr["p2"]):
            c = DEV._clamp(p_, rect); eps.append((pr["net"], c[0], c[1]))
    nets = {e[0] for e in eps}
    netof = {n: [n] for n in nets}                       # a net is its own "member" for the family table
    blocks = FB.functional_blocks(sorted(nets), netof)
    # #K2-438 M-2: a plane net (carried by an inner-layer zone) is NOT block-routed - keep it out of the pack
    # sizes, otherwise GND alone spans the board and forces INFEASIBLE.
    _plane = _plane_nets(board)
    sizes = {}
    for fam, b in blocks.items():
        xs = [e[1] for e in eps if e[0] in b["nets"] and e[0] not in _plane]
        ys = [e[2] for e in eps if e[0] in b["nets"] and e[0] not in _plane]
        if xs:
            sizes[fam] = (max(xs) - min(xs) + 1.0, max(ys) - min(ys) + 1.0)
    plan = FB.multi_block_plan(blocks, sizes, rect)
    # #K2-438 M-2: a disjoint rectangle pack is IMPOSSIBLE on this frame (the family spans mutually overlap and
    # their area sum exceeds the frame), so a FEASIBLE verdict must NOT be a precondition AND must NOT gate the
    # output. The functional-block semantics live in the PER-NET family tag; the packer's target frame - WHEN it
    # yields one - is merely unioned onto that net's own endpoint box. This function NEVER returns "" (returning
    # "" is exactly what made K-2/K-3 a no-op).
    tgt = {p_["block"]: p_["target"] for p_ in plan["plan"]} if plan["verdict"] == "FEASIBLE" else {}
    parts = []
    for n in sorted(nets):
        xs = [e[1] for e in eps if e[0] == n]; ys = [e[2] for e in eps if e[0] == n]
        x0, y0 = min(xs) - clearance, min(ys) - clearance
        x1, y1 = max(xs) + clearance, max(ys) + clearance
        t = tgt.get(FB.family_of([n]))                     # OPTIONAL family frame (may be absent)
        if t is not None and n not in _plane:
            x0, y0 = min(t[0], x0), min(t[1], y0)
            x1, y1 = max(t[2], x1), max(t[3], y1)
        x0, y0 = max(rect[0], x0), max(rect[1], y0)        # keep the channel inside the frame
        x1, y1 = min(rect[2], x1), min(rect[3], y1)
        parts.append("%s:%s" % (n, ",".join("%.4f" % v for v in (x0, y0, x1, y1))))
    return ";".join(parts)


def _plane_nets(board):
    """**确定性**：板上「有内层 zone」的网（平面网/电源网）—— 它们由内层铺铜承载，**不参与**逐网通道打包。"""
    out = set()
    try:
        import pcbnew as _P
        _b = _P.LoadBoard(board)
        for _z in _b.Zones():
            _n = _z.GetNetname()
            if not _n:
                continue
            for _l in _z.GetLayerSet().CuStack():
                if _b.GetLayerName(_l) not in ("F.Cu", "B.Cu"):
                    out.add(_n); break
    except Exception:                                                  # noqa: BLE001
        out = set()
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
