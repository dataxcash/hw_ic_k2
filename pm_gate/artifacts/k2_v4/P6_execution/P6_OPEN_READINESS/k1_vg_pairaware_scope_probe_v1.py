#!/usr/bin/env python3
"""K1 批 6 · VG **对级化次序**上限普查（只读 + 仅 /tmp 影子；handoff §8.2-①）。

问题：(d) 的廉价解（`_k1_escape` VG 兜底对级化）实测 1/8→2/8。本件把「对级化的
       **求解次序 / 轮数 / 择优**」在同一条修正基线上一次量清，回答两问：
       Q1 次序（先 P 还是先 N）是否影响真值？  Q2 双向择优/两轮是否还有增益？

方法：从**冻结容器** `_shared` + `BATCH6_CORRECTED_BASELINE_v1.patch`（= D-1..D-5 +
     ④零长段守卫 + ⑤端点对齐 + (d)对角线 + ⑥耦合）建「修正基线」，再按 **策略** 重写
     `_k1_escape` 的 VG 兜底块（块文本整体替换，策略文本见 STRATEGIES），逐树测
     **修正门下的段级真值**（base 级不得覆盖段级）。
判据口径：净距 = 中心距 ≥ 线宽 + 项目 `p_gap`（D-2 修正量纲）。
产物：证据 JSON（本目录）+ 影子树（/tmp/opencode/vgscope/）。
用法：cd <容器根> && python3 <本件>            # 全量：建树 + 测量
      python3 <本件> --measure <tree> <out>    # 内部：单树测量（子进程用）
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REL = "_shared/eda_core/hs_route_model.py"
PATCH_BASE = os.path.join(HERE, "BATCH6_DRAFT/BATCH6_CORRECTED_BASELINE_v1.patch")
ROOT = "/tmp/opencode/vgscope"

START = '                g_p = HSVisibilityGraph(fcu, net_p, tuple(ep["P"][idx]["pos"]),'
END = ('                    return {"corr_x": corr_x, "P": cand["P"], '
       '"N": cand["N"]}\n')

_PRE = '''                _w = (self.spec.get("impedance") or {}).get("width_mm", 0.09)
                _g = (((self.spec.get("net_classes") or {}).get("PCIe85") or {})
                      .get("diff_pair") or {}).get("p_gap",
                                                   (self.spec.get("impedance") or {}).get("gap_mm", 0.1))
                _clr = _w + _g
'''

_TAIL = '''            except RuntimeError:
                return None
            if sol_p is not None and sol_n is not None:
                cand = {
                    "P": {"pts": [tuple(p) for p in sol_p[0]],
                          "layers": ["F.Cu"] * (len(sol_p[0]) - 1), "via": None},
                    "N": {"pts": [tuple(p) for p in sol_n[0]],
                          "layers": ["F.Cu"] * (len(sol_n[0]) - 1), "via": None},
                }
                if self._k1_escape_verify(fields, net_p, net_n, ep, cand, side):
                    return {"corr_x": corr_x, "P": cand["P"], "N": cand["N"]}
'''

_INDEP_P = '''                g_p = HSVisibilityGraph(fcu, net_p, tuple(ep["P"][idx]["pos"]),
                                        {(corr_x, track_p)})
                sol_p = g_p.solve()
'''
_INDEP_N = '''                g_n = HSVisibilityGraph(fcu, net_n, tuple(ep["N"][idx]["pos"]),
                                        {(corr_x, track_n)})
                sol_n = g_n.solve()
'''
_PAIR_N_ON_P = '''                if sol_p is not None and len(sol_p[0]) >= 2:
                    g_n = HSVisibilityGraph(_PairClearField(fcu, sol_p[0], _clr), net_n,
                                            tuple(ep["N"][idx]["pos"]), {(corr_x, track_n)})
                else:
                    g_n = HSVisibilityGraph(fcu, net_n, tuple(ep["N"][idx]["pos"]),
                                            {(corr_x, track_n)})
                sol_n = g_n.solve()
'''
_PAIR_P_ON_N = '''                if sol_n is not None and len(sol_n[0]) >= 2:
                    g_p = HSVisibilityGraph(_PairClearField(fcu, sol_n[0], _clr), net_p,
                                            tuple(ep["P"][idx]["pos"]), {(corr_x, track_p)})
                else:
                    g_p = HSVisibilityGraph(fcu, net_p, tuple(ep["P"][idx]["pos"]),
                                            {(corr_x, track_p)})
                sol_p = g_p.solve()
'''
_ROUND2 = '''                if sol_n is not None and len(sol_n[0]) >= 2:
                    _r2 = HSVisibilityGraph(_PairClearField(fcu, sol_n[0], _clr), net_p,
                                            tuple(ep["P"][idx]["pos"]),
                                            {(corr_x, track_p)}).solve()
                    if _r2 is not None:
                        sol_p = _r2
'''

_ROUND2_B = """                if sol_p is not None and len(sol_p[0]) >= 2:
                    _r2 = HSVisibilityGraph(_PairClearField(fcu, sol_p[0], _clr), net_n,
                                            tuple(ep["N"][idx]["pos"]),
                                            {(corr_x, track_n)}).solve()
                    if _r2 is not None:
                        sol_n = _r2
"""

_BESTOF = '''                _cands = []
                for _sp, _sn in ((sol_p, sol_n), (_sp2, _sn2)):
                    if _sp is None or _sn is None:
                        continue
                    _c = {
                        "P": {"pts": [tuple(p) for p in _sp[0]],
                              "layers": ["F.Cu"] * (len(_sp[0]) - 1), "via": None},
                        "N": {"pts": [tuple(p) for p in _sn[0]],
                              "layers": ["F.Cu"] * (len(_sn[0]) - 1), "via": None},
                    }
                    if not self._k1_escape_verify(fields, net_p, net_n, ep, _c, side):
                        continue
                    _me, _pt = _path_pn_min_edge_pt(
                        _c["P"]["pts"], _c["P"]["layers"], _c["N"]["pts"],
                        _c["N"]["layers"], _w)
                    _cands.append((_me if _me is not None else -9.0, _c))
                if _cands:
                    _cands.sort(key=lambda t: -t[0])
                    _c = _cands[0][1]
                    return {"corr_x": corr_x, "P": _c["P"], "N": _c["N"]}
'''

STRATEGIES = {
    # 修正基线本体（无对级化）：应与 POC 的 1/8 一致（自证守卫）
    "np_indep": _INDEP_P + _INDEP_N,
    # R-3 落件候选（= BATCH6_VG_PAIRAWARE_v1.patch 的等价体，去 ⑥）
    "np_pairaware": _INDEP_P + _PAIR_N_ON_P,
    # 同序 + 第二轮 N 避 P（迭代收敛）
    "np_pairaware_r2": _INDEP_P + _PAIR_N_ON_P + _ROUND2,
    # 反序：先解 N，再让 P 避 N
    "pn_pairaware": _INDEP_N + _PAIR_P_ON_N,
    "pn_pairaware_r2": _INDEP_N + _PAIR_P_ON_N + _ROUND2_B,
    # 双向择优：两序都算，取通过修正门且净距更大者
    "best_of": (_INDEP_P + _PAIR_N_ON_P
                + '                _sp2, _sn2 = sol_p, sol_n\n'
                + _INDEP_N + _PAIR_P_ON_N + _BESTOF),
}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _rmtree(path):
    def _onerr(func, p, exc):
        try:
            os.chmod(p, 0o777)
            os.chmod(os.path.dirname(p), 0o777)
        except OSError:
            pass
        func(p)
    if os.path.exists(path):
        shutil.rmtree(path, onerror=_onerr)


def build(data_root, name, strategy=None):
    dst = os.path.join(ROOT, name)
    _rmtree(dst)
    os.makedirs(dst)
    shutil.copytree(os.path.join(data_root, "_shared"), os.path.join(dst, "_shared"),
                    symlinks=True)
    subprocess.run(["git", "apply", "-p1", PATCH_BASE], cwd=dst, check=True)
    f = os.path.join(dst, REL)
    if strategy is not None:
        s = open(f).read()
        i = s.index(START)
        j = s.index(END, i) + len(END)
        body = STRATEGIES[strategy]
        if strategy == "best_of":
            body = (_PRE + body
                    + "            except RuntimeError:\n                return None\n")
        else:
            body = _PRE + body + _TAIL
        s = s[:i] + body + s[j:]
        open(f, "w").write(s)
    return dst


def measure_tree(tree, data_root, with_audit=True):
    """子进程测量（保证 sys.path 干净）。"""
    out = tree + ".measure.json"
    r = subprocess.run([sys.executable, os.path.abspath(__file__),
                        "--measure", tree, out], cwd=tree,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return {"error": r.stderr[-800:]}
    res = json.load(open(out))
    if with_audit:
        a = subprocess.run([sys.executable, os.path.join(
            HERE, "k1_layer_legality_audit_v1.py"), "--root", data_root,
            "--core", tree], cwd=data_root, capture_output=True, text=True)
        try:
            res["layer_legality"] = json.loads(a.stdout)
        except Exception:
            res["layer_legality"] = {"error": a.stdout[-300:] + a.stderr[-300:]}
    res["hs_route_model_sha16"] = sha16(os.path.join(tree, REL))
    return res


# ── 内部：单树测量 ────────────────────────────────────────────────────────
def _measure_main(tree, out_path):
    data_root = os.environ["K1_DATA_ROOT"]
    sys.path.insert(0, os.path.join(tree, "_shared"))
    import eda_core
    assert os.path.abspath(eda_core.__file__).startswith(os.path.abspath(tree)), \
        "eda_core 解析到 %s（影子未生效）" % eda_core.__file__
    from eda_core.hs_route_model import HSRouteModel, _path_pn_min_edge_pt
    from eda_core.route_input import ModelConfig, ProjectRouteConfig
    k1 = os.path.join(data_root, "k1")
    spec_p = os.path.join(k1, "pm_gate/artifacts/k1/L3/SPEC_k1.json")
    spec = json.load(open(spec_p))
    thr = float((spec.get("impedance") or {}).get("gap_mm", 0.1))
    cfg = ModelConfig.from_dict(ProjectRouteConfig.load(
        os.path.join(k1, "pm_gate/artifacts/k1/L2/route_model_config.json")).hs_config())
    m = HSRouteModel(os.path.join(k1, "k1_v1.kicad_pcb"), spec_p,
                     os.path.join(k1, "pm_gate/artifacts/k1/L3/model_solves/"
                                  "channel_alloc/channel_alloc.json"),
                     os.path.join(tree, "_shared/eda_core/drc_rules.json"),
                     pro_path=os.path.join(k1, "k1_v1.kicad_pro"), config=cfg)
    r = m.solve_all_v4(m.v4_bases())
    segs, solved = [], 0
    for b, v in r["results"].items():
        for s in v["segments"]:
            e = {"base": b, "seg": s.get("name"), "status": s.get("status"),
                 "reason": s.get("reason")}
            if s.get("status") == "SOLVED":
                solved += 1
                me, pt = _path_pn_min_edge_pt(s["P"]["path"], s["P"]["layers"],
                                              s["N"]["path"], s["N"]["layers"],
                                              s.get("width") or 0.205)
                e["pn_edge"] = None if me is None else round(me, 4)
                e["pn_edge_at"] = None if pt is None else [round(x, 3) for x in pt]
                e["below_project_gap"] = bool(me is not None and me < thr)
            segs.append(e)
    res = {"tree": tree, "segment_solved": solved, "n_segments": len(segs),
           "project_gap_mm": thr, "shared_seg_count": r.get("shared_seg_count"),
           "shared_via_count": r.get("shared_via_count"),
           "segments": segs,
           "segment_solved_below_project_gap": [
               s for s in segs if s.get("below_project_gap")]}
    json.dump(res, open(out_path, "w"), ensure_ascii=False, indent=1)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", nargs=2, metavar=("TREE", "OUT"))
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    if a.measure:
        return _measure_main(a.measure[0], a.measure[1])
    data_root = os.getcwd()
    os.environ["K1_DATA_ROOT"] = data_root
    out = {"artifact": "k1_vg_pairaware_scope_probe", "schema": 1,
           "data_root": data_root,
           "corrected_baseline_patch_sha16": sha16(PATCH_BASE),
           "strategies": sorted(STRATEGIES), "trees": {}}
    plan = [("np_indep", "np_indep"), ("np_pairaware", "np_pairaware"),
            ("np_pairaware_r2", "np_pairaware_r2"),
            ("pn_pairaware", "pn_pairaware"),
            ("pn_pairaware_r2", "pn_pairaware_r2"), ("best_of", "best_of"),
            ("vg_poc_patch2", None)]  # patch2 本体（含 ⑥），复现 POC 的 2/8
    for name, strat in plan:
        if a.only and a.only != name:
            continue
        tree = build(data_root, name, strategy=strat)
        if name == "vg_poc_patch2":
            subprocess.run(["git", "apply", "-p1", os.path.join(
                HERE, "BATCH6_DRAFT/BATCH6_VG_PAIRAWARE_v1.patch")], cwd=tree, check=True)
        out["trees"][name] = measure_tree(tree, data_root)
        t = out["trees"][name]
        print("%-16s solved=%s shared=%s viol=%s" % (
            name, t.get("segment_solved"), t.get("shared_seg_count"),
            len((t.get("layer_legality") or {}).get("violations", []))))
    json.dump(out, open(os.path.join(HERE, "BATCH6_VG_ORDER_SCOPE_PROBE_v1.json"), "w"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
