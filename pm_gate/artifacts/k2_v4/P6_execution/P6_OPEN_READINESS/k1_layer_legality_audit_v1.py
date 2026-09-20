#!/usr/bin/env python3
"""K1 走线**层合法性**审计（只读）：解出的段是否存在「焊盘悬空」的非法层跳。

判两条（缺一即非法）：
  ① 折线**起点层** ∈ 该端点焊盘的 `copper_layers()`（SMD ⇒ 单层；THT ⇒ 全层）；
  ② 折线每一处**层变点**都有 via 记录（段级 `vias` 字段）。

发现（本件自跑即复现）：无 via 的新候选可绕过 ① ⇒ 产出「SMD 焊盘 + 整段走内层」的
假 SOLVED（本会话实测并已自纠，(d) 直接对角线候选的 '+1 增益' 因此作废）。

用法：cd <容器根> && python3 <本件> [--core <core_root>] [--alloc <alloc.json>]
默认 core = 容器 `_shared`；默认 alloc = K1 channel_alloc。
"""
import argparse, json, os, sys


def _find_data_root():
    for c in [os.getcwd()] + [os.path.abspath(os.path.join(os.getcwd(), *([os.pardir] * i)))
                              for i in range(1, 4)]:
        if (os.path.isdir(os.path.join(c, "_shared/eda_core"))
                and os.path.isfile(os.path.join(c, "k1/pm_gate/project.yaml"))):
            return c
    return os.getcwd()


def audit(data_root, core_root, alloc_path):
    sys.path.insert(0, os.path.join(core_root, "_shared"))
    from eda_core.hs_route_model import HSRouteModel
    from eda_core.route_input import ModelConfig, ProjectRouteConfig
    k1 = os.path.join(data_root, "k1")
    cfg = ModelConfig.from_dict(ProjectRouteConfig.load(
        os.path.join(k1, "pm_gate/artifacts/k1/L2/route_model_config.json")).hs_config())
    m = HSRouteModel(os.path.join(k1, "k1_v1.kicad_pcb"),
                     os.path.join(k1, "pm_gate/artifacts/k1/L3/SPEC_k1.json"),
                     alloc_path, os.path.join(core_root, "_shared/eda_core/drc_rules.json"),
                     pro_path=os.path.join(k1, "k1_v1.kicad_pro"), config=cfg)
    r = m.solve_all_v4(m.v4_bases())
    viol, solved = [], 0
    for b, v in r["results"].items():
        for s in v["segments"]:
            if s.get("status") != "SOLVED":
                continue
            solved += 1
            seg_vias = s.get("vias") or []
            for k in ("P", "N"):
                net = s[k]["net"]; pts = s[k]["path"]; lays = s[k]["layers"]
                p0 = tuple(pts[0]); l0 = lays[0]
                pads = [p for p in m.board.pads if p.net == net
                        and abs(p.pos[0] - p0[0]) < 1e-6 and abs(p.pos[1] - p0[1]) < 1e-6]
                if not pads:
                    viol.append({"base": b, "seg": s["name"], "net": net,
                                 "kind": "端点无同名焊盘", "at": [round(x, 3) for x in p0]})
                    continue
                if l0 not in set().union(*[p.copper_layers() for p in pads]):
                    viol.append({"base": b, "seg": s["name"], "net": net,
                                 "kind": "起点层不在焊盘铜层集合（焊盘悬空）",
                                 "layer": l0, "pad_layers": sorted(set().union(*[p.copper_layers() for p in pads])),
                                 "at": [round(x, 3) for x in p0]})
                for i in range(len(lays) - 1):
                    if lays[i] != lays[i + 1]:
                        pt = (pts[i + 1][0], pts[i + 1][1])
                        if not any(abs(vx - pt[0]) < 1e-6 and abs(vy - pt[1]) < 1e-6
                                   for vx, vy in seg_vias):
                            viol.append({"base": b, "seg": s["name"], "net": net,
                                         "kind": "层变点无 via 记录",
                                         "layers": [lays[i], lays[i + 1]],
                                         "at": [round(x, 3) for x in pt]})
    return {"core": core_root, "alloc": os.path.basename(alloc_path),
            "solved_segments": solved, "violations": viol}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--core", default=None)
    ap.add_argument("--alloc", default=None)
    a = ap.parse_args()
    data_root = a.root or _find_data_root()
    core = a.core or data_root
    alloc = a.alloc or os.path.join(
        data_root, "k1/pm_gate/artifacts/k1/L3/model_solves/channel_alloc/channel_alloc.json")
    out = audit(data_root, core, alloc)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
