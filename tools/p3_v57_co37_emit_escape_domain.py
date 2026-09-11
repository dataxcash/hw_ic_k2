#!/usr/bin/env python3
"""CO-37：派生 SPEC `escape_transition_zone`（ECN-001）的**规则域**工件（L2 自裁；实现 SPEC，非放宽）。

裁定依据：`m13_v57_CO25_d3b_audit_fix_ruling.md` §3（域 = J2/J3/J4/U6 pad 场矩形；域外维持 shop 0.175/0.2）。
本工具只做**闭式派生**（零搜索、零设计决策）：域 = 该器件 pad 场 bbox 外扩 MARGIN；层 = F.Cu（SPEC: per_pin_vertical_escape + no_via ⇒ 逃逸接入段在 F.Cu）。
产出：`m13_v57_co37_escape_domain.json`（引擎/工具 O(1) 消费；供 L4 注入 rule area + `.kicad_dru` 条件引用）。
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
PAD_FIELD = STEP2 / "m13_v57_co09_pad_field.json"
OUT = STEP2 / "m13_v57_co37_escape_domain.json"
MARGIN = 0.5          # ≥ 逃逸段半宽 0.1025 + 邻列 pad 边距余量；覆盖 0.4mm 节距 pad 墙接入段的整段
LAYER = "F.Cu"
REFS = ("J2", "J3", "J4", "U6")     # CO-25 §3 裁定 scope


def sha32(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    pads = json.loads(PAD_FIELD.read_text(encoding="utf-8"))["pads"]
    domains = []
    for ref in REFS:
        ps = [p for p in pads if p["ref"] == ref]
        if not ps:
            raise SystemExit(f"no pads for {ref}")
        x0 = min(p["x"] - p["sx"] / 2 for p in ps) - MARGIN
        y0 = min(p["y"] - p["sy"] / 2 for p in ps) - MARGIN
        x1 = max(p["x"] + p["sx"] / 2 for p in ps) + MARGIN
        y1 = max(p["y"] + p["sy"] / 2 for p in ps) + MARGIN
        domains.append({"id": f"ESC_{ref}", "ref": ref, "n_pads": len(ps), "layer": LAYER,
                        "rect_mm": [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)]})
    doc = {"artifact": "m13_v57_co37_escape_domain", "schema": 1, "revision": "CO37-ESC.1",
           "authority": {"ruling": "m13_v57_CO25_d3b_audit_fix_ruling.md §3 (D3c 自裁, L2)",
                         "spec_constraint": "SPEC.constraints.escape_transition_zone (ECN-001)"},
           "method": {"kind": "closed_form_bbox", "margin_mm": MARGIN, "layer": LAYER,
                      "no_search": True,
                      "basis": "pad 场 bbox 外扩 MARGIN；层=F.Cu（per_pin_vertical_escape + no_via）"},
           "escape_clearance_mm": 0.075,
           "excluded_nets": ["PCIE_REFCLK*"],
           "exclusion_basis": "SPEC.constraints.refclk_isolated=true ⇒ REFCLK 不享受逃逸区放宽（其冲突属 D3a 几何缺陷）",
           "inputs_sha256": {"pad_field": sha32(PAD_FIELD)},
           "domains": domains}
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{doc['revision']}: domains={len(domains)} sha16={sha32(OUT)[:16]}")
    for d in domains:
        print("   %-8s x[%.3f,%.3f] y[%.3f,%.3f]" % (d["id"], *d["rect_mm"][0:1], d["rect_mm"][2],
                                                    d["rect_mm"][1], d["rect_mm"][3]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
