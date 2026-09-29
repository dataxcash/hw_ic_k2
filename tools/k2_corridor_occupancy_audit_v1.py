#!/usr/bin/env python3
"""k2_corridor_occupancy_audit_v1.py --- **图纸层（B1）前置件**：把 R1154 已画出的每条域内走廊，
与**当前板**逐件比对，**具名**列出落在走廊（含净空）内的**异网铜** —— 即"要让这条走廊可用，必须
移走/让开的受影响件全集"（#K2-412 §四.2 承 #K2-410/R1102 的"受影响件定界"）。

只读 · 确定性 · 零搜索 · 零板改 · 零考跑。

口径（保守 AABB · 与迷宫同源）：异网铜的包围盒与走廊矩形**最近距离** ≤ `half_width + CLEAR` 即计入；
`CLEAR` 默认 0.20mm（= 本板 K2 验收权威 netclass 净空，承 wrapper 的 `--floor 0.20`）。

CLI: python3 tools/k2_corridor_occupancy_audit_v1.py --board <pcb> --plan <R1154 plan.json> --json-out P
Exit 0 = 审计完成（每走廊给出 clear/occupied 与具名清单）。
"""
from __future__ import annotations
import argparse, json, os, re, sys

CLEAR = 0.20
LAYER_RE = re.compile(r"(F\.Cu|B\.Cu|In\d+(?:\.Cu)?)")   # bare `In5` also occurs in the plan text


def parse_corridor(text):
    """从 R1154 的 `corridor` 描述串取 `(layers, (x0,y0,x1,y1))`。确定性；解析不到 ⇒ 抛错（不静默）。"""
    layers, seen = [], set()
    for L in LAYER_RE.findall(text or ""):
        L = L if L.endswith(".Cu") else L + ".Cu"                  # normalise bare `In5` -> `In5.Cu`
        if L not in seen:
            seen.add(L); layers.append(L)
    m = re.search(r"\(([^)]*)\)", text or "")
    if not m:
        raise ValueError("no parenthesised bounds in corridor: %r" % text)
    inner = m.group(1)
    pairs = re.findall(r"([\d.]+)\s*-\s*([\d.]+)", inner)
    if len(pairs) < 2:
        raise ValueError("cannot read two ranges from corridor: %r" % text)
    x0, x1 = float(pairs[0][0]), float(pairs[0][1])
    y0, y1 = float(pairs[1][0]), float(pairs[1][1])
    clip = re.search(r"clipped\s+to\s+([\d.]+)", inner)          # e.g. 'F.Cu (43.4-81.0 clipped to 51.5, ...)'
    if clip:
        x1 = float(clip.group(1))
    return layers, (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def rect_gap(a, b):
    """两个 AABB 的最近距离（0 = 相交）。"""
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return (dx * dx + dy * dy) ** 0.5


def audit(board_path, plan_path):
    import pcbnew as P
    plan = json.load(open(plan_path, encoding="utf-8"))
    gaps = (plan.get("corrected_complete_plan") or {}).get("per_gap_drawing") or []
    b = P.LoadBoard(board_path)
    out = {"artifact": "k2_corridor_occupancy_audit_v1", "board": board_path, "plan": plan_path,
           "clear_mm": CLEAR, "corridors": [], "OWNER-ITEMS": 0}
    for gi, g in enumerate(gaps):
        layers, rect = parse_corridor(g.get("corridor"))
        occ = []
        for t in b.GetTracks():
            ln = b.GetLayerName(t.GetLayer())
            if ln not in layers or t.GetNetname() == g["net"]:
                continue
            bb = t.GetBoundingBox()
            tb = (P.ToMM(bb.GetLeft()), P.ToMM(bb.GetTop()), P.ToMM(bb.GetRight()), P.ToMM(bb.GetBottom()))
            if rect_gap(rect, tb) <= CLEAR + 1e-9:
                occ.append({"kind": "track/via", "net": t.GetNetname(), "layer": ln,
                            "at": [round(P.ToMM(t.GetStart().x), 3), round(P.ToMM(t.GetStart().y), 3)]})
        for fp in b.GetFootprints():
            for pd in fp.Pads():
                if pd.GetNetname() == g["net"]:
                    continue
                for lay in pd.GetLayerSet().Seq():
                    ln = b.GetLayerName(lay)
                    if ln not in layers:
                        continue
                    bb = pd.GetBoundingBox()
                    pb = (P.ToMM(bb.GetLeft()), P.ToMM(bb.GetTop()), P.ToMM(bb.GetRight()), P.ToMM(bb.GetBottom()))
                    if rect_gap(rect, pb) <= CLEAR + 1e-9:
                        occ.append({"kind": "pad", "net": pd.GetNetname(), "layer": ln,
                                    "ref": fp.GetReference(), "pad": pd.GetNumber()})
                    break
        out["corridors"].append({
            "gap": gi, "net": g["net"], "layers": layers, "rect": [round(v, 3) for v in rect],
            "verdict": "OCCUPIED" if occ else "CLEAR",
            "n_occupants": len(occ), "occupants": occ[:40],
            "rule": "#K2-412 sec.4.2 (R1102/R1154): the items that stand inside the drawn corridor (plus clearance) "
                    "are exactly the affected set that must be moved/cleared before this corridor is usable."})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    rep = audit(a.board, a.plan)
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
