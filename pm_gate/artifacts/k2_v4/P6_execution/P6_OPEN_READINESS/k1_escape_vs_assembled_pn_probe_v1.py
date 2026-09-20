#!/usr/bin/env python3
"""K1 逃逸门「验证范围」缺口复核件（只读 + 仅 /tmp 影子）。

结论（本件自跑即复现）：`_k1_escape_verify` **只验逃逸候选**，不验「逃逸 ⊕ 走廊段」
拼接后的**整段折线** ⇒ 走廊段引入的 P/N 交叉不会被逃逸门发现，段级仍报 SOLVED。

复现口径：容器 `_shared` + `BATCH6_DRAFT/hs_route_model.patch`（⑤⑥；该 patch 让
TX0.input 走通 VG 兜底，从而触发本缺口）。实测样点 PCIE_TX0/input：
  · 逃逸候选 verify = True，候选内 P/N 中心线最小距 = 0.1483（≥0.1，合法）
  · 拼接后整段 `_path_pn_min_edge_pt` = **-0.09**（铜重叠）
⇒ 差值是**走廊段**引入的；逃逸门看不到它。

用法：cd <容器根> && python3 <本件>
"""
import json, os, shutil, subprocess, sys

SHADOW = "/tmp/opencode/esc_vs_assembled"
DRAFT = "k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/BATCH6_DRAFT/hs_route_model.patch"


def _find_data_root():
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


def build(data_root):
    _rmtree(SHADOW)
    os.makedirs(SHADOW, exist_ok=True)
    shutil.copytree(os.path.join(data_root, "_shared"), os.path.join(SHADOW, "_shared"),
                    symlinks=True)
    subprocess.run(["git", "apply", "-p1", os.path.join(data_root, DRAFT)],
                   cwd=SHADOW, check=True)


def run(data_root):
    sys.path.insert(0, os.path.join(SHADOW, "_shared"))
    from eda_core.hs_route_model import HSRouteModel, _seg_seg_dist, _path_pn_min_edge_pt
    from eda_core.route_input import ModelConfig, ProjectRouteConfig
    k1 = os.path.join(data_root, "k1")
    cfg = ModelConfig.from_dict(ProjectRouteConfig.load(
        os.path.join(k1, "pm_gate/artifacts/k1/L2/route_model_config.json")).hs_config())
    m = HSRouteModel(os.path.join(k1, "k1_v1.kicad_pcb"),
                     os.path.join(k1, "pm_gate/artifacts/k1/L3/SPEC_k1.json"),
                     os.path.join(k1, "pm_gate/artifacts/k1/L3/model_solves/channel_alloc/channel_alloc.json"),
                     os.path.join(SHADOW, "_shared/eda_core/drc_rules.json"),
                     pro_path=os.path.join(k1, "k1_v1.kicad_pro"), config=cfg)
    escape_log, _orig_esc, _orig_ver = [], m._k1_escape, m._k1_escape_verify

    def esc(fields, net_p, net_n, ep, tp, lp, tn, ln, cx, d, side="left"):
        r = _orig_esc(fields, net_p, net_n, ep, tp, lp, tn, ln, cx, d, side)
        if r is not None:
            # 与引擎同口径：**仅同层** 段对参与 P/N 间距判定（异层对不适用）
            mn = min((_seg_seg_dist(r["P"]["pts"][i], r["P"]["pts"][i + 1],
                                    r["N"]["pts"][j], r["N"]["pts"][j + 1])
                      for i in range(len(r["P"]["pts"]) - 1)
                      for j in range(len(r["N"]["pts"]) - 1)
                      if r["P"]["layers"][i] == r["N"]["layers"][j]), default=None)
            mn = None if mn is None else round(mn, 4)
            escape_log.append({"pair": net_p, "side": side,
                               "escape_verify": _orig_ver(fields, net_p, net_n, ep, r, side),
                               "escape_pn_center_min_same_layer": mn})
        return r

    m._k1_escape = esc
    r = m.solve_all_v4(m.v4_bases())
    rows = []
    for b, v in r["results"].items():
        for s in v["segments"]:
            if s.get("status") != "SOLVED":
                continue
            me, pt = _path_pn_min_edge_pt(s["P"]["path"], s["P"]["layers"],
                                          s["N"]["path"], s["N"]["layers"],
                                          s.get("width") or 0.205)
            rows.append({"base": b, "seg": s["name"], "assembled_pn_edge": round(me, 4),
                         "at": [round(x, 3) for x in pt]})
    return {"escape_candidates": escape_log, "assembled_solved_segments": rows,
            "verdict": {
                "gate_scope_gap": any(e["escape_verify"]
                                      and (e["escape_pn_center_min_same_layer"] or 9) >= 0.1
                                      for e in escape_log)
                                  and any(x["assembled_pn_edge"] < 0.1 for x in rows),
                "note": "逃逸候选合法（verify True, ≥0.1）而拼接后整段 <0.1 ⇒ 门只覆盖逃逸段"}}


def main():
    data_root = _find_data_root()
    build(data_root)
    out = run(data_root)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open(os.path.join(SHADOW, "verdict.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
