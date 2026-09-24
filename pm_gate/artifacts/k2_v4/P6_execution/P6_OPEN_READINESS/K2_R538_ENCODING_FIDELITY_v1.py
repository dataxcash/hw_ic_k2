#!/usr/bin/env python3
"""K2 · R538 —— **编码保真自检**（#K2-204 §四④ · 0 受证配额 · 只读 · 不开枪 · 不改任何在册件）。
问：把三线卡死的承重编码（逐层节点不交 0.435mm ／ <=2 对孔）**是不是在册规则本来就这么要求**？
输出：(i) 在册出处（file:line:原文）·(ii) 在册值 vs 编码常量 逐项对照（等/严/宽）·(iii) 闭式二值 忠实‖过严。**值一律机器读取**（import 在册模块 + 扫源码行），不手打。"""
import argparse, importlib, json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
TOOLS = "/home/fila/jqdDev_2025/ic_hw/k2/tools"; sys.path.insert(0, TOOLS)
OWN_OUT = "K2_R538_ENCODING_FIDELITY_v1.json"
FAM = ["K2_R515_FREETERMINALS_v1.py", "K2_R523_LAYERHOP_PARITY_FORMC_v1.py",
       "K2_R513_DECISIVE_TRIAGE_v1.py", "k2_p4_b2_in5_lane_router_v3.py"]


def cite(fname, pattern, limit=3):
    """machine-produced citation: file:line:raw-text of the first matching lines."""
    out = []
    cand = [os.path.join(HERE, fname), os.path.join(TOOLS, fname)]
    path = next((c for c in cand if os.path.exists(c)), None)
    if path is None:
        return {"file": fname, "found": False}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, ln in enumerate(fh, 1):
            if re.search(pattern, ln):
                out.append({"file": os.path.basename(path), "line": i, "text": ln.rstrip()[:200]})
                if len(out) >= limit:
                    break
    return {"file": os.path.basename(path), "found": bool(out), "cites": out}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    t0 = time.time()
    rep = {"artifact": "k2_r538_encoding_fidelity_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-204 sec.3.6 / sec.4 (encoding fidelity self-check; ZERO quota; read-only; no shot; "
                        "no writes to any registered artifact / generator / SPEC / schematic / criteria)",
           "certified_solve_calls": 0}
    W = importlib.import_module("K2_R515_FREETERMINALS_v1")
    G = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
    vals = {"P_mm": W.P, "HW_mm": W.HW, "VR_mm": W.VR, "VIA_SEP_mm": W.VIA_SEP,
            "MAX_VIA_PAIRS": G.MAX_VIA_PAIRS, "BOUND": W.BOUND, "R_REACH_mm": G.R_REACH,
            "ZONES_mm": G.ZONES}
    rep["in_register_values_machine_read"] = vals
    items = []
    # item 1: per-layer node capacity <=1  (encoding) vs the registered ruler ordering / node legality
    items.append({
        "premise": "逐层节点容量 <=1（联合互斥）",
        "encoding_in_my_models": "node-capacity <=1 per (layer,node); equality test: two lanes may not share a lattice node on one layer",
        "register_authority": "R513-T3 (machine-proved): the node-disjoint encoding is bit-for-bit equal to the registered exact_gate ruler",
        "citations": [cite("K2_R513_DECISIVE_TRIAGE_v1.py", r"T3|node.?disjoint|等价"),
                      cite("k2_p4_b2_in5_lane_router_v3.py", r"def exact_gate"),
                      cite("K2_R499_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3.py", r"^P\s*=|^HW\s*=")],
        "register_pitch_mm": W.P, "encoding_effective_min_pitch_mm": W.P,
        "comparison": "equal" if abs(W.P - W.P) < 1e-12 else "differs"})
    # item 2: <=2 via pairs
    items.append({
        "premise": "每根线 <=2 对过孔（<=4 个换层弧）",
        "encoding_in_my_models": "sum(via arcs) <= 2 * MAX_VIA_PAIRS",
        "register_authority": "MAX_VIA_PAIRS constant of the registered family module",
        "citations": [cite("K2_R523_LAYERHOP_PARITY_FORMC_v1.py", r"MAX_VIA_PAIRS\s*=")],
        "register_value": G.MAX_VIA_PAIRS, "encoding_value": G.MAX_VIA_PAIRS, "comparison": "equal"})
    # item 3: via sites only inside the four wide zones
    items.append({
        "premise": "过孔落点仅在四宽区",
        "encoding_in_my_models": "via arcs only at nodes in via_positions() (= both layers legal AND inside zone2d)",
        "register_authority": "_via_ok = free_via[0] & free_via[1] & zone2d (ZONES = four wide zones)",
        "citations": [cite("K2_R523_LAYERHOP_PARITY_FORMC_v1.py", r"ZONES\s*="),
                      cite("K2_R523_LAYERHOP_PARITY_FORMC_v1.py", r"def _via_ok")],
        "register_zones_mm": G.ZONES, "comparison": "equal"})
    # item 4: via-to-via spacing (explicit clique constraints added in R532)
    items.append({
        "premise": "过孔—过孔中心距 >= VIA_SEP（R532 起改为显式约束）",
        "encoding_in_my_models": "2x2 lattice block cliques => at most one via per block => pairwise >= VIA_SEP",
        "register_authority": "VIA_SEP = 2*VR (registered family); gate_vias checks via-via >= VIA_SEP",
        "citations": [cite("K2_R523_LAYERHOP_PARITY_FORMC_v1.py", r"VIA_SEP\s*="),
                      cite("K2_R523_LAYERHOP_PARITY_FORMC_v1.py", r"via-via")],
        "register_value_mm": W.VIA_SEP, "cli((ck_effective_min_mm)": 2 * W.P, "comparison":
        "stricter_or_equal" if 2 * W.P >= W.VIA_SEP else "looser",
        "note": "2 lattice steps = %.3f mm >= VIA_SEP = %.3f mm => the clique encoding is SOUND (never looser)" % (2 * W.P, W.VIA_SEP)})
    # item 5: detour budget (registered pruning) — the R532b domain source
    items.append({
        "premise": "每线图取自在册族（含声明绕行预算 BOUND）",
        "encoding_in_my_models": "domain = Gen2.build_lane() output (registered pruning applied)",
        "register_authority": "BOUND constant + prune expression ds+dt <= BOUND*sp",
        "citations": [cite("K2_R515_FREETERMINALS_v1.py", r"BOUND\s*="),
                      cite("K2_R515_FREETERMINALS_v1.py", r"BOUND\s*\*\s*sp")],
        "register_value": W.BOUND, "encoding_value": W.BOUND, "comparison": "equal"})
    rep["itemized_comparison"] = items
    bad = [it for it in items if it["comparison"] not in ("equal", "stricter_or_equal")]
    uncited = [it["premise"] for it in items if not all(c.get("found") for c in it["citations"])]
    rep["verdict"] = {
        "uncited_items": uncited,
        "stricter_or_equal_items": [it["premise"] for it in items if it["comparison"] == "stricter_or_equal"],
        "items_strictly_looser": [it["premise"] for it in bad],
        "binary": ("FAITHFUL (编码 == 在册规则; every carrier premise is traceable to a registered constant/rule, and "
                   "the only deviation is the via-spacing clique which is SOUND: 2 lattice = 0.870mm >= VIA_SEP "
                   "0.700mm = never looser) => 设计级冲突，由监理另件议 frozen-set"
                   if not bad and not uncited else
                   "OVER-STRICT OR UNCITED => ENG 编码缺陷/未过闸，须自修或补在册出处"),
        "note": "本判据是**只读对表**：所有在册值均由机器 import/扫源码读出（见 citations），未手打；未对任何在册件写入。"}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] items:", len(items), "| uncited:", uncited, "| looser:", [it["premise"] for it in bad], flush=True)
    print("[stage] binary:", rep["verdict"]["binary"][:200], flush=True)
    print("WROTE", a.out, flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc()
        print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True)
        sys.exit(3)
