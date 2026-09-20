#!/usr/bin/env python3
"""K1 逃逸端点可行性普查（只读 + 仅 /tmp 影子）：区分「结构性无解」与「模板/对级受限」。

方法：把 `_k1_escape` 的 V-Graph 兜底分支加诊断（记录 P/N 单网是否各自可达），
在影子树里跑 K1 全量 v4 求解 ⇒ 得到每个冲突端点属：
  · 结构性无解（单网 VG 都不可达）⇒ 须换层/过孔策略（批 6 (b)）；
  · 模板/对级受限（单网各自可达）⇒ 端点几何可解，属 (d) 端点对齐/对级构造。

用法：cd <容器根> && python3 <本件>
"""
import json, os, shutil, sys

SHADOW = "/tmp/opencode/escape_vg_census"
ANCHOR = ('        fcu = fields.get("F.Cu")\n'
          '        if fcu is not None:\n'
          '            try:\n'
          '                g_p = HSVisibilityGraph(fcu, net_p, tuple(ep["P"][idx]["pos"]),\n'
          '                                        {(corr_x, track_p)})\n'
          '                sol_p = g_p.solve()\n'
          '                g_n = HSVisibilityGraph(fcu, net_n, tuple(ep["N"][idx]["pos"]),\n'
          '                                        {(corr_x, track_n)})\n'
          '                sol_n = g_n.solve()\n'
          '            except RuntimeError:\n'
          '                return None')
PATCHED = ('        fcu = fields.get("F.Cu")\n'
           '        if fcu is not None:\n'
           '            _dg = {"net_p": net_p, "net_n": net_n, "side": side, "corr_x": corr_x,\n'
           '                   "track_p": track_p, "track_n": track_n}\n'
           '            try:\n'
           '                g_p = HSVisibilityGraph(fcu, net_p, tuple(ep["P"][idx]["pos"]),\n'
           '                                        {(corr_x, track_p)})\n'
           '                sol_p = g_p.solve()\n'
           '                g_n = HSVisibilityGraph(fcu, net_n, tuple(ep["N"][idx]["pos"]),\n'
           '                                        {(corr_x, track_n)})\n'
           '                sol_n = g_n.solve()\n'
           '            except RuntimeError:\n'
           '                _dg["vg_p"] = "RUNTIME_ERROR"\n'
           '                _dg["vg_n"] = "RUNTIME_ERROR"\n'
           '                _rec(self, _dg)\n'
           '                return None\n'
           '            _dg["vg_p"] = sol_p is not None\n'
           '            _dg["vg_n"] = sol_n is not None\n'
           '            _rec(self, _dg)')


def _find_data_root():
    for c in [os.getcwd()] + [os.path.abspath(os.path.join(os.getcwd(), *([os.pardir] * i)))
                              for i in range(1, 4)]:
        if (os.path.isdir(os.path.join(c, "_shared/eda_core"))
                and os.path.isfile(os.path.join(c, "k1/pm_gate/project.yaml"))):
            return c
    return os.getcwd()


def build(data_root):
    if os.path.exists(SHADOW):
        shutil.rmtree(SHADOW, onerror=lambda f, p, e: (os.chmod(p, 0o777), f(p)))
    os.makedirs(SHADOW, exist_ok=True)
    shutil.copytree(os.path.join(data_root, "_shared"), os.path.join(SHADOW, "_shared"),
                    symlinks=True)
    f = os.path.join(SHADOW, "_shared/eda_core/hs_route_model.py")
    s = open(f).read()
    assert s.count(ANCHOR) == 1, "VG 兜底载体未命中"
    rec = ('\n\ndef _rec(model, d):\n'
           '    model._vg_diag = getattr(model, "_vg_diag", [])\n'
           '    model._vg_diag.append(d)\n\n\n')
    s = s.replace("\ndef pair_endpoints(", rec + "def pair_endpoints(", 1)
    s = s.replace(ANCHOR, PATCHED)
    open(f, "w").write(s)


def run(data_root):
    sys.path.insert(0, os.path.join(SHADOW, "_shared"))
    from eda_core.hs_route_model import HSRouteModel
    from eda_core.route_input import ModelConfig, ProjectRouteConfig
    k1 = os.path.join(data_root, "k1")
    cfg = ModelConfig.from_dict(ProjectRouteConfig.load(
        os.path.join(k1, "pm_gate/artifacts/k1/L2/route_model_config.json")).hs_config())
    m = HSRouteModel(os.path.join(k1, "k1_v1.kicad_pcb"),
                     os.path.join(k1, "pm_gate/artifacts/k1/L3/SPEC_k1.json"),
                     os.path.join(k1, "pm_gate/artifacts/k1/L3/model_solves/channel_alloc/channel_alloc.json"),
                     os.path.join(SHADOW, "_shared/eda_core/drc_rules.json"),
                     pro_path=os.path.join(k1, "k1_v1.kicad_pro"), config=cfg)
    r = m.solve_all_v4(m.v4_bases())
    rows = []
    for d in getattr(m, "_vg_diag", []):
        rows.append({"pair": [d["net_p"], d["net_n"]], "side": d["side"],
                     "corr_x": round(d["corr_x"], 3),
                     "vg_p": d.get("vg_p"), "vg_n": d.get("vg_n"),
                     "class": ("结构性无解" if not (d.get("vg_p") and d.get("vg_n"))
                               else "模板/对级受限")})
    segs = {b: {s["name"]: s["status"] for s in v["segments"]}
            for b, v in r["results"].items()}
    return {"seg_status": segs, "escape_endpoint_census": rows}


def main():
    data_root = _find_data_root()
    build(data_root)
    out = run(data_root)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    json.dump(out, open(os.path.join(SHADOW, "census.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
