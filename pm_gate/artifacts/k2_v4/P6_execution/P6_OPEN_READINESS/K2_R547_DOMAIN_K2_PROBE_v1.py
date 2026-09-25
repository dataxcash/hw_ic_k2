#!/usr/bin/env python3
"""K2 · R547 —— **k 备选域规模探针**（#K2-213 §四④① · 零受证配额 · 只读 · 不求解）。
逐线逐段：第 1 条最短路（按跳数）＋ 禁用其内部点后再求第 2 条 ⇒ **并集膨胀 1 格**为域 ⇒ 报告**bool/约束规模 vs 1.2M 闸**
（回答"k=2~3 备选域能否落在闸内"，供下一窗定序构造选 k）。"""
import argparse, collections, importlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
NID, TERM_BASE, NX, NY = W.NID, W.TERM_BASE, W.NX, W.NY
OWN_OUT = "K2_R547_DOMAIN_K2_PROBE_v1.json"
SPEC = os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")
GATE = 1200000


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    t0 = time.time()
    spec = json.load(open(SPEC))
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    rep = {"artifact": "k2_r547_domain_k2_probe_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-213 sec.4 item 1 (domain definition: k alternates + size vs the 1.2M gate); ZERO quota; read-only",
           "solve_calls": 0, "gate": GATE, "per_lane": {}}
    tot1 = tot2 = 0
    for nm in names:
        wps = spec["per_lane"][nm]["waypoints"]
        chain = [lanes[nm]["src"]] + [w["node"] for w in wps[1:-1]] + [lanes[nm]["snk"]]
        full = collections.defaultdict(set)
        for u, lst in lanes[nm]["adj"].items():
            for (v, _w) in lst:
                full[u].add(v); full[v].add(u)

        def path(src, dst, forb=None):
            prev = {src: None}; dq = collections.deque([src])
            while dq:
                x = dq.popleft()
                if x == dst:
                    p = []; y = dst
                    while y is not None:
                        p.append(y); y = prev[y]
                    return p[::-1]
                for y in full[x]:
                    if y in prev or (forb and y in forb):
                        continue
                    prev[y] = x; dq.append(y)
            return None
        n1 = n2 = 0
        for s in range(len(chain) - 1):
            src, dst = chain[s], chain[s + 1]
            if src == dst:
                continue
            p1 = path(src, dst)
            n1 += len(p1 or [])
            inter = set(x for x in (p1 or []) if x < TERM_BASE and x not in (src, dst))
            p2 = path(src, dst, forb=inter) if inter else None
            n2 += len(p2 or [])
        tot1 += n1; tot2 += n2
        rep["per_lane"][nm] = {"path1_nodes": n1, "path1_plus_alt2_nodes": n2,
                               "growth_ratio": (round(n2 / n1, 2) if n1 else None)}
    approx_bools_k1 = 138364                     # measured in R543c (single-path domain, fired shot)
    rep["projection"] = {"measured_k1_bools": approx_bools_k1,
                         "sum_path1_nodes": tot1, "sum_path1_plus_alt2_nodes": tot2,
                         "projected_k2_bools": int(approx_bools_k1 * (tot2 / tot1)) if tot1 else None,
                         "fits_gate_k2": (approx_bools_k1 * (tot2 / tot1) <= GATE) if tot1 else None,
                         "note": "linear projection from the measured k=1 domain size; a real k=2 build must be measured before firing"}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] sum nodes path1=%d  +alt2=%d  ratio=%.2f  projected k2 bools=%s  fits_gate=%s"
          % (tot1, tot2, (tot2 / tot1 if tot1 else 0), rep["projection"]["projected_k2_bools"], rep["projection"]["fits_gate_k2"]), flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
