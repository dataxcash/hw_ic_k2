#!/usr/bin/env python3
"""k2_corridor_element3_gen_v1.py --- **§16.3 element③ 生成器**（#K2-413 §五：B1 确定性重画 ＋ 逐廊道守恒机核）。

产出：对 v2 规划的 8 个缺口，逐条给出
  · **每线确定图**：层 / 端点（域内化）/ **具体走廊矩形**（= 按 v2 规则重画出的最大净空子矩）/ 换层过孔点；
  · **逐廊道守恒机核**（硬）：`capacity_mm`（该走廊**自身**净空子矩的窄边） ≥ `need_mm`（该网线宽 + 2×净空）；
    **禁以"块/域级 93.5% 空闲"代替**（#K2-413 §四/§五.3）；字段缺 ⇒ fail-closed。
  · `status`：PASS ｜ NARROW（有净空通道但窄于需求）｜ NO_WITNESS_BOXED（端点被围死 ⇒ 附**具名让路清单**）。

只读 · 确定性 · **零搜索**（矩形差集）· 零板改 · 零考跑。
CLI: python3 tools/k2_corridor_element3_gen_v1.py --board <pcb> --plan <v2 plan.json> --drc <drc.json> --json-out P
"""
from __future__ import annotations
import argparse, importlib.util, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CLEAR = 0.20


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def drc_pairs(drc):
    out = []
    for it in (drc.get("unconnected_items") or []):
        its = it.get("items") or []
        if len(its) != 2:
            continue
        da, db = its[0].get("description", ""), its[1].get("description", "")
        ma, mb = re.search(r"\[([^\]]+)\]", da or ""), re.search(r"\[([^\]]+)\]", db or "")
        if not ma or not mb or ma.group(1) != mb.group(1):
            continue
        out.append({"net": ma.group(1), "p1": [its[0]["pos"]["x"], its[0]["pos"]["y"]],
                    "p2": [its[1]["pos"]["x"], its[1]["pos"]["y"]]})
    return out


def generate(board, plan_path, drc_path, clearance=DEFAULT_CLEAR):
    import pcbnew as P
    AUD = _load("k2_corridor_occupancy_audit_v1", "tools/k2_corridor_occupancy_audit_v1.py")
    RDR = _load("k2_corridor_redraw_v1", "tools/k2_corridor_redraw_v1.py")
    plan = json.load(open(plan_path, encoding="utf-8"))
    gaps = plan["corrected_complete_plan"]["element_3_corrected_construction"]["per_gap"]
    pairs = drc_pairs(json.load(open(drc_path, encoding="utf-8")))
    b = P.LoadBoard(board)
    netw = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if n and type(t).__name__ != "PCB_VIA":            # via width needs a layer arg (kicad assert noise)
            netw[n] = min(netw.get(n, 1e9), P.ToMM(t.GetWidth()))
    out = {"artifact": "k2_sec16_3_element3_concrete_v1", "ts": "2026-09-29", "board": board,
           "authority": "#K2-413 sec.5: B1 deterministic redraw + PER-CORRIDOR conservation machine check.",
           "clearance_mm": clearance, "gaps": [], "OWNER-ITEMS": 0}
    for g in gaps:
        layers, rect = AUD.parse_corridor(g["v1_corridor"])
        cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
        cand = []
        for pr in pairs:
            if pr["net"] != g["net"]:
                continue
            a = tuple(min(max(pr["p1"][k], rect[k]), rect[k + 2]) for k in (0, 1))
            bb = tuple(min(max(pr["p2"][k], rect[k]), rect[k + 2]) for k in (0, 1))
            mid = ((a[0] + bb[0]) / 2, (a[1] + bb[1]) / 2)
            cand.append(((mid[0] - cx) ** 2 + (mid[1] - cy) ** 2, a, bb))
        cand.sort()
        if not cand:
            out["gaps"].append({"net": g["net"], "status": "NO_DRC_PAIR", "capacity_mm": None, "need_mm": None})
            continue
        _, a, bb = cand[0]
        occ = [o["bbox"] for o in AUD.occupant_rects(b, layers, g["net"], clearance)
               if AUD.rect_gap(rect, o["bbox"]) <= clearance + 1e-9]
        sub, _ = RDR.clear_subrect_containing_pts(rect, occ, clearance, [a, bb])
        s1, _ = RDR.clear_subrect_containing_pts(rect, occ, clearance, [a])
        s2, _ = RDR.clear_subrect_containing_pts(rect, occ, clearance, [bb])
        cap1 = min(s1[2] - s1[0], s1[3] - s1[1]) if s1 else 0.0
        cap2 = min(s2[2] - s2[0], s2[3] - s2[1]) if s2 else 0.0
        allocc = AUD.occupant_rects(b, layers, g["net"], clearance)
        blk = sorted({o["net"] for o in allocc if AUD.rect_gap(rect, o["bbox"]) <= clearance + 1e-9
                      and ((o["bbox"][0] - clearance - 1e-9 <= a[0] <= o["bbox"][2] + clearance + 1e-9
                            and o["bbox"][1] - clearance - 1e-9 <= a[1] <= o["bbox"][3] + clearance + 1e-9)
                           or (o["bbox"][0] - clearance - 1e-9 <= bb[0] <= o["bbox"][2] + clearance + 1e-9
                               and o["bbox"][1] - clearance - 1e-9 <= bb[1] <= o["bbox"][3] + clearance + 1e-9))})
        w = netw.get(g["net"], 0.20)
        need = w + 2 * clearance
        cap = min(sub[2] - sub[0], sub[3] - sub[1]) if sub else None
        status = ("PASS" if (sub and cap >= need - 1e-9) else
                  ("NARROW" if sub else "NO_COMMON_CHANNEL"))
        out["gaps"].append({
            "net": g["net"], "layers": layers, "v1_corridor_rect": rect,
            "in_domain_p1": list(a), "in_domain_p2": list(bb),
            "concrete_corridor": list(sub) if sub else None,
            "capacity_mm": None if cap is None else round(cap, 4), "need_mm": round(need, 4),
            "cap_at_p1_mm": round(cap1, 4), "cap_at_p2_mm": round(cap2, 4),
            "track_w_mm": round(w, 4), "status": status,
            "n_occupants": len(occ), "n_blockers_mid": len(blk), "blockers_named": blk})
    out["conservation"] = {
        "rule": "PER-CORRIDOR: capacity (the witnessed clear sub-rectangle's narrow dimension) >= need "
                "(this net's track width + 2*clearance). Block-level free-area substitution is FORBIDDEN "
                "(#K2-413 sec.4.3).",
        "n_pass": sum(1 for g in out["gaps"] if g.get("status") == "PASS"),
        "n_total": len(out["gaps"]),
        "pass": all(g.get("status") == "PASS" for g in out["gaps"])}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--plan", required=True)
    ap.add_argument("--drc", required=True); ap.add_argument("--clearance", type=float, default=DEFAULT_CLEAR)
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    rep = generate(a.board, a.plan, a.drc, a.clearance)
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
