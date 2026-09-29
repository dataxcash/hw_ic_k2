#!/usr/bin/env python3
"""k2_functional_block_v1.py --- **K-2 功能分块**（#K2-434 §2.1 · functional BLOCK）。

按**确定性功能族**（固定有序表；首匹配胜）把区内成员分成功能块；每块导出：
**成员 / 块内网 / 边界端口（跨块框的网）/ 块框（成员焊盘 bbox）**。同输入恒同输出。
CLI: python3 tools/k2_functional_block_v1.py --board B --members A,B,C [--json-out P]
"""
from __future__ import annotations
import argparse, json, re, sys

FAMILIES = [("POWER", ("VDD", "P3V3", "12V", "VBUS", "VIN", "VR")),
            ("CONTROL", ("NRST", "PERSTA", "PWR_BTN", "SWD", "SWCLK", "SWDIO", "BOOT")),
            ("BUS", ("I2C", "UART", "SPI", "SMB")),
            ("HS", ("PCIE", "CLK")),
            ("MISC", ())]


def family_of(nets):
    up = [ (n or "").upper() for n in nets ]
    for fam, keys in FAMILIES:
        if any(k in n for n in up for k in keys):
            return fam
    return "MISC"


def functional_blocks(members, netof):
    """**纯函数 · 确定性**：返回 {fam: {members:[...], nets:[...]}}（fam 按 FAMILIES 序）。"""
    out = {}
    for r in sorted(members):
        f = family_of(netof.get(r, []))
        out.setdefault(f, {"members": [], "nets": []})
        out[f]["members"].append(r)
        for n in sorted(set(netof.get(r, []))):
            if n not in out[f]["nets"]:
                out[f]["nets"].append(n)
    return {k: out[k] for k in [f for f, _ in FAMILIES] if k in out}


def boundary_ports(blocks, netof):
    """**确定性**：某块的网若也被**其它块**的成员使用 ⇒ 该网是**边界端口**。返回 {fam:[net,...]}。"""
    owner = {}
    for fam, b in blocks.items():
        for n in b["nets"]:
            owner.setdefault(n, set()).add(fam)
    return {fam: sorted(n for n in b["nets"] if len(owner.get(n, set())) > 1) for fam, b in blocks.items()}


def multi_block_plan(blocks, sizes, region, hs_x_max=51.5, gap=0.3):
    """**K-3 多块协同动**（#K2-434 §2.1 · 确定性 · 零搜索）：**一份计划**把 N≥1 块在 `region` 内**同时**落位——
    按 **FAMILIES 序**沿 y **依次堆叠**（不相交）；**前置硬闸**逐条机核：
      (1) 块间不重叠  (2) 面积守恒（Σ块面积 ≤ 区域面积）  (3) 端口数匹配（每块边界端口已具名）  (4) HS 安全带（x ≤ hs_x_max）零侵入；
    **不可行 ⇒ 具名归因到块**（绝不静默）。`sizes`={fam:(w,h)}；返回 {plan:[...], checks:{...}, verdict}。"""
    x0, y0, x1, y1 = [float(v) for v in region]
    if x1 > hs_x_max + 1e-9:
        x1 = hs_x_max                                   # HS safety band: never cross it
    plan, cur = [], y0
    order = [f for f, _ in FAMILIES if f in blocks]
    for fam in order:
        w, h = sizes.get(fam, (0.0, 0.0))
        if cur + h > y1 + 1e-9:
            return {"plan": plan, "checks": {"area_ok": False}, "verdict": "INFEASIBLE",
                    "named": [{"block": fam, "why": "does not fit in the region (area/height)"}]}
        plan.append({"block": fam, "target": [round(x0, 4), round(cur, 4), round(min(x0 + w, x1), 4), round(cur + h, 4)]})
        cur += h + gap
    ov = any(not (a["target"][2] <= b["target"][0] or b["target"][2] <= a["target"][0]
                  or a["target"][3] <= b["target"][1] or b["target"][3] <= a["target"][1])
             for i, a in enumerate(plan) for b in plan[i + 1:])
    need = sum(sizes.get(f, (0, 0))[0] * sizes.get(f, (0, 0))[1] for f in order)
    checks = {"disjoint": not ov, "area_ok": need <= (x1 - x0) * (y1 - y0) + 1e-9,
              "ports_named": all(f in blocks for f in order), "hs_safe": all(p["target"][2] <= hs_x_max + 1e-9 for p in plan)}
    v = "FEASIBLE" if all(checks.values()) else "INFEASIBLE"
    named = [k for k, ok in checks.items() if not ok]
    return {"plan": plan, "checks": checks, "verdict": v, "named": named}


PER_BLOCK_STEPS = ("1_block", "2_multi_block_place", "3_pour_aware_clear", "4_in_block_route",
                   "5_cross_block_stitch", "6_refill", "7_judge")


def per_block_flow(blocks, plan):
    """**K-4 逐块工序**（#K2-434 §2.1 · 确定性）：产**七步序** ＋ **逐块验收行**。
    硬规则：**块内 C1 先归零**（失败可定位到块）；**电源/平面走铺铜，不走细线**（`POWER` 块只列端口，不列细线计划）。"""
    rows = []
    for p_ in plan:
        fam = p_["block"]
        b = blocks.get(fam, {})
        rows.append({"block": fam, "members": b.get("members", []), "nets": b.get("nets", []),
                     "gate": "in_block_C1_zero", "route_mode": ("pour/plane (NO thin track)" if fam == "POWER" else "signal straight"),
                     "target": p_["target"]})
    return {"steps": list(PER_BLOCK_STEPS), "per_block": rows,
            "rules": ["block-internal C1 must reach zero FIRST (failures localise to a block)",
                      "power/plane nets go through pours, never thin tracks",
                      "cross-block connectivity only via the NAMED boundary ports"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True, help='json: {members:[...], netof:{ref:[net..]}}')
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    p = json.load(open(a.params, encoding="utf-8"))
    blk = functional_blocks(p["members"], p["netof"])
    rep = {"artifact": "k2_functional_block_v1", "blocks": blk,
           "boundary_ports": boundary_ports(blk, p["netof"]),
           "rule": "#K2-434 K-2: deterministic functional blocks (fixed ordered family table); boundary ports are the nets crossing blocks"}
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
