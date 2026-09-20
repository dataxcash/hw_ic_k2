#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""P3 v57 S0 子步2 — 单向审计既有派生物 vs 权威端点模型（铁律 L4）。

权威端点注册表：每网(68, k2_sch 全链名) → 端列表 {side: {ref, xy 板坐标}}。
  side: chip(U6) / conn:{J2|J3|J4}。
被审对象：A. escape_spec.pins；B. 现存 landing 图纸行(P0 基线 52 行)。
按 region 期望端分类：J2 区→期望 conn:J2 端；MCIO 区→conn:J3/J4 端；
U3/U7 区→chip 端。
锚对期望端=ok；锚到非期望权威端=wrong_side_anchor（如连接器区行锚到芯片端
= B1/max-x bug）；锚不在任何权威端=no_endpoint_match（中间焊盘/异常）。
差异一律 authority-first（权威优先待改），绝不允许反向。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
import yaml  # noqa: E402
from eda_core.drc_rules import BoardParser  # noqa: E402

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
SCH = K2 / "boards" / "k2_sch.yaml"
ESCAPE_JSON = (K2 / "pm_gate" / "artifacts" / "k2_v4" / "L2" /
               "escape_spec.json")
OUT = STEP2 / "m13_v57_s0_audit_derived.json"
EPS = 0.05


def near(a, b, eps=EPS):
    return a is not None and b is not None and abs(a[0] - b[0]) <= eps \
        and abs(a[1] - b[1]) <= eps


# ── 权威端点注册表（每 schematic 网名 → {chip|conn:ref: xy}）──
sch = yaml.safe_load(open(SCH))
b = BoardParser(str(K2 / "k2_v4.kicad_pcb")).parse()
pads_by_net = {}
for p in b.pads:
    pads_by_net.setdefault(p.net, []).append(
        (p.footprint_ref, round(float(p.pos[0]), 3),
         round(float(p.pos[1]), 3)))

registry = {}
for net, eps_ in sch["nets"].items():
    if not net.startswith(("PCIE", "REFCLK")):
        continue
    sides = {}
    for e in eps_:
        ref, pin = e.split("/", 1)
        # 端点 pad：该 (ref, net) 唯一（连接器/芯片），取板实现坐标
        cand = [xy for (r, xy) in
                ((pp[0], (pp[1], pp[2])) for pp in pads_by_net.get(net, []))
                if r == ref]
        if cand:
            sides["chip" if ref == "U6" else f"conn:{ref}"] = list(cand[0])
    registry[net] = sides

# ── A. escape_spec 审计 ─────────────────────────────────
es = json.load(open(ESCAPE_JSON))
es_rep = {"n_pins": 0, "chip_refs": {}, "mapped": 0, "net_not_found": [],
          "coord_mismatch": []}
for p in es.get("pins", []):
    es_rep["n_pins"] += 1
    es_rep["chip_refs"].setdefault(p.get("chip_ref"), 0)
    es_rep["chip_refs"][p.get("chip_ref")] += 1
    net = p["net"]
    if net not in registry:
        es_rep["net_not_found"].append(net)
        continue
    es_rep["mapped"] += 1
    xy = [round(float(v), 3) for v in p.get("pin_xy", [])]
    chip = registry[net].get("chip")
    if chip and not near(xy, chip):
        es_rep["coord_mismatch"].append({"net": net, "escape_xy": xy,
                                         "authority_chip_xy": chip})

# ── B. 现存 landing 图纸行审计（P0 基线）──────────────────
P0 = json.load(open("/tmp/opencode/run3_report.json"))
rows = P0["stages"]["landing"]["allocation"]
b_rep = {"n_rows": 0, "by_region_class": {}, "wrong_side_anchor": [],
         "no_endpoint_match": []}
EXPECT = {"J2": {"conn:J2"}, "MCIO": {"conn:J3", "conn:J4"},
          "U3": {"chip"}, "U7": {"chip"}}
for net, rec in sorted(rows.items()):
    b_rep["n_rows"] += 1
    region = rec.get("region")
    anc = rec.get("pad")
    if net not in registry:
        b_rep.setdefault("rows_without_registry", []).append(net)
        continue
    sides = registry[net]
    expect = EXPECT.get(region, set())
    ok = any(k in expect and near(anc, v) for k, v in sides.items())
    if ok:
        key = (region, "endpoint_ok")
    elif any(k not in expect and near(anc, v) for k, v in sides.items()):
        key = (region, "wrong_side_anchor")
    else:
        key = (region, "no_endpoint_match")
    b_rep["by_region_class"].setdefault(key, 0)
    b_rep["by_region_class"][key] += 1
    d = {"net": net, "region": region, "row_anchor": anc,
         "authority_sides": sides}
    if key[1] == "wrong_side_anchor":
        b_rep["wrong_side_anchor"].append(d)
    elif key[1] == "no_endpoint_match":
        b_rep["no_endpoint_match"].append(d)

report = {
    "artifact": "m13_v57_s0_audit_derived",
    "standard": "k2_sch 网表(每网端点语义) + 板端 pad 几何实现（authority-first）",
    "direction": "上游→下游单向；差异 = 权威优先待改",
    "escape_spec": es_rep,
    "landing_rows": {
        "n": b_rep["n_rows"],
        "by_region_class": {f"{r}/{c}": n
                            for (r, c), n
                            in sorted(b_rep["by_region_class"].items())},
        "wrong_side_anchor": b_rep["wrong_side_anchor"],
        "no_endpoint_match": b_rep["no_endpoint_match"],
    },
}
OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True),
               encoding="utf-8")
print(json.dumps({
    "escape_spec": {"pins": es_rep["n_pins"], "mapped": es_rep["mapped"],
                    "coord_mismatch": len(es_rep["coord_mismatch"]),
                    "net_not_found": es_rep["net_not_found"][:12]},
    "landing_by_region_class": report["landing_rows"]["by_region_class"],
    "wrong_side_anchor_n": len(b_rep["wrong_side_anchor"]),
    "no_endpoint_match_n": len(b_rep["no_endpoint_match"]),
}, indent=1, ensure_ascii=False))
print("artifact:", OUT)
