"""verify --- 判卷器（DRC / 连通 / 等长 / 倒角 / 走线真变 / 四角禁区）。无 LLM 依赖。

判据（#K2-356 §二.1/2.2）：
  C1 连通 : kicad-cli DRC unconnected_items == 0        （16/16 全链之机器代理）
  C2 DRC  : 总数 <= 基线 且 不长新类                      （基线默认 l14 = 168）
  C3 等长 : 逐对铜长差 max <= 0.15 mm                     （drc_rules.json intra_pair_skew_mm）
  C4 倒角 : 45° 段数 >= 基线                              （默认 2637）
  C5 真变 : 段级元素集差 vs 基线 ≠ 0                       （no-op 判 FAIL · 承 #K2-332）
几何读板需 pcbnew（KiCad 自带 python）；缺失则该项报 SKIPPED（不得当 PASS）。
"""
from __future__ import annotations
import collections, json, os

PAIRS = [(k, "PCIE_DN%d_N" % k, "PCIE_DN%d_P" % k) for k in range(8)]
SKEW_LIMIT = 0.15
BASELINE_BOARD = "hw/k2_v4_8L.l14.kicad_pcb"
BASELINE_DRC_TOTAL = 168
BASELINE_CHAMFER = 2637
_TABLE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      "pm_gate", "artifacts", "k2_v4", "L2", "EDA_ENG_JUDGING_TABLE_v1.json")


def judging_table(path=None):
    """判卷表的**唯一源** = ECO-K2-0002/0003 §6（#K2-361 §二.4）。"""
    p_ = path or _TABLE
    if os.path.isfile(p_):
        return json.load(open(p_, encoding="utf-8"))
    return {"thresholds": {"C1_connectivity": {"value": 0},
                           "C2_drc_no_new_increase": {"value": BASELINE_DRC_TOTAL},
                           "C3_skew": {"value": SKEW_LIMIT},
                           "C4_chamfer_preserved": {"value": BASELINE_CHAMFER},
                           "C5_routing_changed": {"value": ">0"}}}


def class_delta(result_drc, ref_drc, exclude=None):
    """**类别级** DRC 差（M3 残留的具名归因工具）：逐类 delta ＋ 总数 delta。"""
    r = drc_classes(result_drc)["classes"]
    b = drc_classes(ref_drc)["classes"]
    if exclude is None:
        exclude = judging_table()["thresholds"]["C2_drc_no_new_increase"].get("excluded_classes", [])
    rows, excl = {}, {}
    for k in sorted(set(r) | set(b)):
        dd = r.get(k, 0) - b.get(k, 0)
        if not dd:
            continue
        (excl if k in exclude else rows)[k] = {"result": r.get(k, 0), "ref": b.get(k, 0), "delta": dd}
    geo_result = sum(v for k, v in r.items() if k not in exclude)
    geo_ref = sum(v for k, v in b.items() if k not in exclude)
    return {"total_delta": geo_result - geo_ref, "by_class": rows, "excluded_class_rows": excl,
            "excluded_classes": list(exclude), "raw_total_delta": sum(r.values()) - sum(b.values()),
            "attributed": bool(rows) or (geo_result != geo_ref),
            "rule": "#K2-361 sec.2.5: any GEOMETRY class rise must be attributed; library-resolution classes are "
                    "recorded in excluded_class_rows under the pinned caliber (they are never hidden)"}


def drc_classes(j):
    d = json.load(open(j, encoding="utf-8"))
    c = collections.Counter(v.get("type") for v in d.get("violations", []))
    return {"total": sum(c.values()), "classes": dict(c),
            "unconnected": len(d.get("unconnected_items", [])),
            "schematic_parity": len(d.get("schematic_parity", []))}


def geometry(path):
    try:
        import pcbnew as P
    except Exception as e:                                     # noqa: BLE001
        return {"skipped": "pcbnew unavailable: %s" % e}
    b = P.LoadBoard(path)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    lens, chamfer, elems = collections.defaultdict(float), 0, collections.Counter()
    for t in b.GetTracks():
        nm = nets.get(t.GetNetCode(), "")
        if nm[:4] == "PCIE":
            lens[nm] += P.ToMM(t.GetLength())
        if t.GetClass() == "PCB_VIA":
            x, y = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
            elems[(nm, "VIA", round(x, 3), round(y, 3))] += 1
            continue
        s, e = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = P.ToMM(s.x), P.ToMM(s.y), P.ToMM(e.x), P.ToMM(e.y)
        dx, dy = abs(bx - ax), abs(by - ay)
        if dx > 0.01 and dy > 0.01 and abs(dx - dy) < 0.005:
            chamfer += 1
        elems[(nm, t.GetLayerName(), round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3))] += 1
    return {"lens": dict(lens), "chamfer_45deg": chamfer, "elems": elems}


def judge(board, drc_json, ref_board, ref_drc_json,
          drc_total=None, chamfer_ref=None, skew_limit=None, table=None, extra=None):
    tbl = judging_table(table)["thresholds"]
    drc_total = tbl["C2_drc_no_new_increase"]["value"] if drc_total is None else drc_total
    chamfer_ref = tbl["C4_chamfer_preserved"]["value"] if chamfer_ref is None else chamfer_ref
    skew_limit = tbl["C3_skew"]["value"] if skew_limit is None else skew_limit
    d, r = drc_classes(drc_json), drc_classes(ref_drc_json)
    g, gr = geometry(board), geometry(ref_board)
    new_classes = sorted(k for k in d["classes"] if k not in r["classes"])
    out = {"C1_connectivity": {"unconnected": d["unconnected"], "pass": d["unconnected"] == 0},
           "C2_drc_no_new_increase": {"total": d["total"], "ref_total": r["total"], "new_classes": new_classes,
                                      "pass": d["total"] <= drc_total and not new_classes}}
    if "skipped" in g or "skipped" in gr:
        out["C3_skew"] = {"skipped": (g.get("skipped") or gr.get("skipped")), "pass": None}
        out["C4_chamfer_preserved"] = {"skipped": True, "pass": None}
        out["C5_routing_changed"] = {"skipped": True, "pass": None}
    else:
        sk = {}
        for tag, n, p in PAIRS:
            if g["lens"].get(n) and g["lens"].get(p):
                sk[tag] = round(abs(g["lens"][n] - g["lens"][p]), 6)
        mx = max(sk.values()) if sk else None
        out["C3_skew"] = {"per_pair_mm": sk, "max_mm": mx, "limit_mm": skew_limit,
                          "pass": mx is not None and mx <= skew_limit}
        out["C4_chamfer_preserved"] = {"count": g["chamfer_45deg"], "ref_count": chamfer_ref,
                                       "pass": g["chamfer_45deg"] >= chamfer_ref}
        diff = sum(1 for k in g["elems"] if k not in gr["elems"]) + sum(1 for k in gr["elems"] if k not in g["elems"])
        out["C5_routing_changed"] = {"element_set_diff": diff, "pass": diff > 0}
    # BLOCK 保真判据（#K2-369 §三.3，已批入 ECO-K2-0002 §6）：由调用方（block 链）算好传入。
    if extra:
        for k in sorted(extra):
            out[k] = extra[k]
    vals = [v["pass"] for v in out.values()]
    verdict = "FAIL" if any(v is False for v in vals) else ("INCOMPLETE" if any(v is None for v in vals) else "PASS")
    return {"criteria": out, "verdict": verdict, "thresholds_used": {
                "drc_total": drc_total, "chamfer_ref": chamfer_ref, "skew_limit": skew_limit},
            "judging_table": "L2/EDA_ENG_JUDGING_TABLE_v1.json (ECO-K2-0002/0003 sec.6)",
            "rule": "PASS iff EVERY criterion holds (C1-C5 in-register + C6/C7 block-fidelity when a block chain is "
                    "graded); None (skipped) is never a PASS (#K2-358: capability must be reproducible)"}
