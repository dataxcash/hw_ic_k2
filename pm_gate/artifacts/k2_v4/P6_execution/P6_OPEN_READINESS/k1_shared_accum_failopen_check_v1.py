#!/usr/bin/env python3
"""K1 HS 模型「段级 SOLVED fail-open」独立复核件（只读 + 仅 /tmp 影子）。

复核两条结论（缺一即不复现）：
  ① 现行引擎的 `solve_all_v4` 在 K1 上 `shared_seg_count == 0`
     ⇒ 跨 base 避让**完全未发生**（累积门挂在 base 级，K1 无全解 base）。
  ② 段级 SOLVED 与 base 级物理判定**自相矛盾**：批 6 用的 ⑥ 树上，TX0 base
     被引擎自己判 `INFEASIBLE / P/N 间距不足 -0.09`，而 TX0 的 input/output
     **两段都报 SOLVED**；RX0/input 更是 P/N 边缘距 0.01（< 项目 spec gap 0.1）
     却因 base 未 SOLVED 而**整道门被跳过**、仍报 SOLVED。
  ③ 修正门（FIX-A 逐段累积 + FIX-B 段级 P/N 门，阈值取 `spec.impedance.gap_mm`）
     后，K1 真值回落为 **1/8（仅 TX0.output）** ⇒ 批 6 的『段级增益』读数作废。

用法：cd <容器根> && python3 <本件>     # 只读真源；影子落 /tmp/opencode/
"""
import argparse, json, os, shutil, subprocess, sys

SHADOW_ROOT = "/tmp/opencode/shared_accum_check"
GATE_OLD = ('            results[base] = res\n'
            '            if res.get("status") == "SOLVED":\n'
            '                for seg in res.get("segments", []):')
GATE_NEW = ('            results[base] = res\n'
            '            if True:  # CANDIDATE-FIX-A: 逐段累积\n'
            '                for seg in res.get("segments", []):')
PN_OLD = ('            res = self.solve_pair_v4(sp, sn, base, segname,\n'
          '                                     shared_segs=shared, shared_vias=vias)\n'
          '            if res.get("status") == "SOLVED":')
PN_NEW = ('            res = self.solve_pair_v4(sp, sn, base, segname,\n'
          '                                     shared_segs=shared, shared_vias=vias)\n'
          '            # CANDIDATE-FIX-B: 段级 P/N 门（阈值 = 项目 spec impedance.gap_mm）\n'
          '            if res.get("status") == "SOLVED" and res.get("P") and res.get("N"):\n'
          '                _me, _pt = _path_pn_min_edge_pt(res["P"]["path"], res["P"]["layers"],\n'
          '                                                res["N"]["path"], res["N"]["layers"],\n'
          '                                                res.get("width") or 0.205)\n'
          '                _thr = (self.spec.get("impedance") or {}).get("gap_mm", 0.1)\n'
          '                if _me is not None and _me < _thr:\n'
          '                    res["status"] = "INFEASIBLE"\n'
          '                    res["reason"] = "P/N gap %.4f < %.3f" % (_me, _thr)\n'
          '            if res.get("status") == "SOLVED":')


def find_data_root():
    for c in [os.getcwd()] + [os.path.abspath(os.path.join(os.getcwd(), *([os.pardir] * i)))
                              for i in range(1, 4)]:
        if (os.path.isdir(os.path.join(c, "_shared/eda_core"))
                and os.path.isfile(os.path.join(c, "k1/pm_gate/project.yaml"))):
            return c
    return os.getcwd()


def _rmtree(path):
    """444/555 权限树的安全删除（先 chmod 自身与父目录）。"""
    def _onerr(func, p, exc):
        try:
            os.chmod(p, 0o777)
            os.chmod(os.path.dirname(p), 0o777)
        except OSError:
            pass
        func(p)
    if os.path.exists(path):
        shutil.rmtree(path, onerror=_onerr)


def build_tree(data_root, name, patch6=False, fix_a=False, fix_b=False):
    dst = os.path.join(SHADOW_ROOT, name)
    _rmtree(dst)
    os.makedirs(SHADOW_ROOT, exist_ok=True)
    shutil.copytree(os.path.join(data_root, "_shared"), os.path.join(dst, "_shared"),
                    symlinks=True)
    if patch6:
        p6 = os.path.join(data_root, "k2/pm_gate/artifacts/k2_v4/P6_execution/"
                          "P6_OPEN_READINESS/BATCH6_DRAFT/hs_route_model.patch")
        subprocess.run(["git", "apply", "-p1", p6], cwd=dst, check=True)
    if fix_a or fix_b:
        f = os.path.join(dst, "_shared/eda_core/hs_route_model.py")
        s = open(f).read()
        if fix_a:
            assert s.count(GATE_OLD) == 1, "FIX-A 载体未命中"
            s = s.replace(GATE_OLD, GATE_NEW)
        if fix_b:
            assert s.count(PN_OLD) == 1, "FIX-B 载体未命中"
            s = s.replace(PN_OLD, PN_NEW)
        open(f, "w").write(s)
    return dst


def measure(core_root, data_root):
    sys.path.insert(0, os.path.join(core_root, "_shared"))
    for m in [m for m in sys.modules if m.startswith("eda_core")]:
        del sys.modules[m]
    from eda_core.hs_route_model import HSRouteModel, _path_pn_min_edge_pt
    from eda_core.route_input import ModelConfig, ProjectRouteConfig
    k1 = os.path.join(data_root, "k1")
    spec_p = os.path.join(k1, "pm_gate/artifacts/k1/L3/SPEC_k1.json")
    thr = float((json.load(open(spec_p)).get("impedance") or {}).get("gap_mm", 0.1))
    cfg = ModelConfig.from_dict(ProjectRouteConfig.load(
        os.path.join(k1, "pm_gate/artifacts/k1/L2/route_model_config.json")).hs_config())
    m = HSRouteModel(os.path.join(k1, "k1_v1.kicad_pcb"), spec_p,
                     os.path.join(k1, "pm_gate/artifacts/k1/L3/model_solves/channel_alloc/channel_alloc.json"),
                     os.path.join(core_root, "_shared/eda_core/drc_rules.json"),
                     pro_path=os.path.join(k1, "k1_v1.kicad_pro"), config=cfg)
    r = m.solve_all_v4(m.v4_bases())
    solved, below, bases = 0, [], {}
    for b, v in r["results"].items():
        bases[b] = {"base_status": v.get("status"), "base_reason": v.get("reason"),
                    "base_pn_spacing": v.get("pn_spacing")}
        for s in v["segments"]:
            if s.get("status") != "SOLVED":
                continue
            solved += 1
            me, pt = _path_pn_min_edge_pt(s["P"]["path"], s["P"]["layers"],
                                          s["N"]["path"], s["N"]["layers"],
                                          s.get("width") or 0.205)
            if me is not None and me < thr:
                below.append({"base": b, "seg": s["name"], "pn_edge": round(me, 4),
                              "project_gap": thr, "at": [round(x, 3) for x in pt]})
    return {"seg_solved": solved, "shared_seg_count": r.get("shared_seg_count"),
            "shared_via_count": r.get("shared_via_count"),
            "project_gap_mm": thr,
            "segment_solved_with_pn_edge_below_project_gap": below,
            "bases": bases}


def measure_k2(core_root, data_root):
    """K2 回归探针（锚 = test_hs_route_model.py 的 K2V4_* 口径）。"""
    import hashlib
    sys.path.insert(0, os.path.join(core_root, "_shared"))
    for m in [m for m in sys.modules if m.startswith("eda_core")]:
        del sys.modules[m]
    from eda_core.hs_route_model import HSRouteModel
    k2 = os.path.join(data_root, "k2")
    board = os.path.join(k2, "k2_v4_8L.kicad_pcb")
    spec = os.path.join(k2, "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json")
    alloc = os.path.join(k2, "pm_gate/artifacts/k2_v4/L3/model_solves/pipeline_alloc_current_v1/alloc.json")
    m = HSRouteModel(board, spec, alloc, os.path.join(core_root, "_shared/eda_core/drc_rules.json"),
                     pro_path=board.replace(".kicad_pcb", ".kicad_pro"))
    r = m.solve_all_v4(m.v4_bases())
    sig = {}
    for b, v in r["results"].items():
        sig[b] = (v.get("status"),
                  tuple((s.get("name"), s.get("status")) for s in v.get("segments", [])),
                  v.get("skew"), v.get("pn_spacing"))
    return {"n_bases": len(sig), "solved_bases": sorted(b for b, v in sig.items() if v[0] == "SOLVED"),
            "shared_seg_count": r.get("shared_seg_count"),
            "sig_sha16": hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()[:16]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--k2", action="store_true", help="并跑 K2 回归探针（约 1min/核）")
    a = ap.parse_args()
    data_root = a.root or find_data_root()
    out = {"data_root": data_root, "cases": {}}
    out["cases"]["as_is"] = measure(data_root, data_root)
    out["cases"]["batch6_6_patch_as_is"] = measure(
        build_tree(data_root, "t6", patch6=True), data_root)
    out["cases"]["batch6_6_patch_fixA_fixB"] = measure(
        build_tree(data_root, "t6ab", patch6=True, fix_a=True, fix_b=True), data_root)
    if a.k2:
        out["k2_pristine"] = measure_k2(data_root, data_root)
        out["k2_fixed"] = measure_k2(build_tree(data_root, "k2fixAB", fix_a=True, fix_b=True), data_root)
    c0, c6, c6ab = (out["cases"]["as_is"], out["cases"]["batch6_6_patch_as_is"],
                    out["cases"]["batch6_6_patch_fixA_fixB"])
    out["verdict"] = {
        "as_is_cross_base_avoidance_disabled": c0["shared_seg_count"] == 0,
        "batch6_6_internal_contradiction": bool(
            c6["segment_solved_with_pn_edge_below_project_gap"])
        and any(v["base_status"] != "SOLVED"
                for v in c6["bases"].values()),
        "batch6_6_seg_solved_as_is": c6["seg_solved"],
        "batch6_6_seg_solved_after_fixAB": c6ab["seg_solved"],
        "batch6_6_gain_after_fixAB": c6["seg_solved"] - c6ab["seg_solved"],
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    os.makedirs(SHADOW_ROOT, exist_ok=True)
    json.dump(out, open(os.path.join(SHADOW_ROOT, "verdict.json"), "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
