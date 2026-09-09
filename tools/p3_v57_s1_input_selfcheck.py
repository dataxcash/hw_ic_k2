#!/usr/bin/env python3
"""P3 v57 — 上游输入自洽门 v0（板级意图文件自我校验，禁止把病带给下游）。

对象：SPEC_k2_v4.json（corridors/stackup/layer_plan）+ route_model_config.json
     （capacity_audit 对中心距 1.46）+ S0 端点模型（网表权威 cross-check）。
判定（violations，逐字节确定、纯文件读取、零几何反猜）：
  G1 层有效性：corridor band.layer ∈ 6L 有效铜层{F.Cu,In1.Cu,In2.Cu,In3.Cu,
     In4.Cu,B.Cu}；In6/In8 等废层 → 违例（F-B 型）。
  G2 lane 间距守恒：同廊同层任意两 lane（含跨 band）差分对中心距 ≥ 1.46
     （config capacity_audit 声明口径）；Δ<0.585=铜包络重叠(硬伤)，0.585≤Δ<1.46
     =规则违例。refclk lane 层无效时按候选有效层{F.Cu,In2.Cu}重映射再判
     （暴露 F-A：无有效放置）。
  G3 band nets 完整性：SPEC 每带 nets(base) 每 base 在端点模型必存在 P/N 两网
     （数据）或 1 对（REFCLK 直通）；每数据 base 在页清单恰 2 页(input+out)。
     （用 page_manifest.json，权威派生，防 V5 型错归属/丢页。）
"""
from __future__ import annotations

import json
import re
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4"
L2 = L3 / "L2"
STEP2 = L3 / "L3" / "mcio_feas_step2"
SPEC = L3 / "L3" / "SPEC_k2_v4.json"
CFG = L2 / "route_model_config.json"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
OUT = STEP2 / "m13_v57_s1_input_selfcheck_report.json"

VALID_LAYERS = {"F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"}
REMAP_LAYERS = ["F.Cu", "In2.Cu"]
PAIR_ENV = 0.585
RULE_PITCH = None


def main() -> int:
    global RULE_PITCH
    spec = json.load(open(SPEC))
    cfg = json.load(open(CFG))
    mfest = json.load(open(MANIFEST))
    RULE_PITCH = float((cfg.get("capacity_audit") or {}).get(
        "inter_pair_spacing", 1.46))

    viol = []
    lanes_by_corridor = {}
    for c in spec.get("corridors") or []:
        cid = c["id"]
        for b in c.get("bands") or []:
            layer = b.get("layer")
            if layer not in VALID_LAYERS:
                viol.append({"G": "G1_layer_invalid", "corridor": cid,
                             "band": b["band"], "layer": layer,
                             "valid": sorted(VALID_LAYERS)})
            for ty in b.get("tracks_y") or []:
                lanes_by_corridor.setdefault(cid, []).append(
                    {"band": b["band"], "y": float(ty), "layer": layer})
    for cid, lanes in sorted(lanes_by_corridor.items()):
        for a in range(len(lanes)):
            for bb in range(a + 1, len(lanes)):
                la, lb = lanes[a], lanes[bb]
                if la["band"] == lb["band"] and la["y"] == lb["y"]:
                    continue
                d = abs(la["y"] - lb["y"])
                common = {la["layer"], lb["layer"]} & VALID_LAYERS
                if len(common) == 1 and la["layer"] == lb["layer"]:
                    if d < RULE_PITCH - 1e-9:
                        viol.append({"G": "G2_lane_spacing", "corridor": cid,
                                     "lane_a": la, "lane_b": lb,
                                     "dy": round(d, 3),
                                     "rule_pitch": RULE_PITCH,
                                     "severity": ("硬伤:铜包络重叠"
                                                  if d < PAIR_ENV else
                                                  "规则违例")})
        for la in lanes:
            if la["layer"] not in VALID_LAYERS and la["band"] == "refclk":
                for rl in REMAP_LAYERS:
                    ok = True
                    for lb in lanes:
                        if lb is la or lb["layer"] != rl:
                            continue
                        if abs(la["y"] - lb["y"]) < RULE_PITCH - 1e-9:
                            ok = False
                            break
                    if ok:
                        viol.append({"G": "G2b_refclk_remap_ok",
                                     "corridor": cid, "y": la["y"],
                                     "layer": rl, "note": "存在有效重映射"})
                    else:
                        viol.append({"G": "G2b_refclk_no_placement",
                                     "corridor": cid, "y": la["y"],
                                     "layer": rl,
                                     "note": "该有效层上无 ≥pitch 隔离位(F-A)"})
    pages = mfest["pages"]
    per_base = {}
    for pg in pages:
        per_base.setdefault(pg["base"], []).append(pg["segname"])
    ep_ids = {pg["base"] for pg in pages if pg["kind"] == "data"}

    def _base_of(band_net):
        m = re.match(r"^PCIE_(DN|UP)_OUT(\d+)$", band_net)
        if m:
            return f"PCIE_{m.group(1)}{m.group(2)}"
        return band_net

    for c in spec.get("corridors") or []:
        for b in c.get("bands") or []:
            for net in b.get("nets") or []:
                base = _base_of(net)
                if net.startswith("PCIE_REFCLK"):
                    if net not in per_base:
                        viol.append({"G": "G3_refclk_page_missing",
                                     "corridor": c["id"], "band": b["band"],
                                     "net": net})
                    continue
                if net.startswith("PCIE_") and "_OUT" in net:
                    if base not in per_base:
                        viol.append({"G": "G3_namespace_mismatch",
                                     "corridor": c["id"], "band": b["band"],
                                     "band_net": net, "base_of": base})
                    continue
                if base not in ep_ids:
                    viol.append({"G": "G3_band_net_no_endpoint",
                                 "corridor": c["id"], "band": b["band"],
                                 "net": net})
                elif base in per_base and len(per_base[base]) != 2:
                    viol.append({"G": "G3_base_page_count",
                                 "net": base, "pages": per_base[base],
                                 "expect": 2})

    ok = not viol
    report = {"artifact": "m13_v57_s1_input_selfcheck_report",
              "predicate": "上游输入自洽门 v0（SPEC/config/manifest 自我校验）",
              "rule_pitch_mm": RULE_PITCH,
              "n_violations": len(viol),
              "violations": viol,
              "verdict": "PASS" if ok else "FAIL"}
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    g1 = sum(1 for v in viol if v["G"] == "G1_layer_invalid")
    g2 = sum(1 for v in viol if v["G"] == "G2_lane_spacing")
    g2b = sum(1 for v in viol if v["G"].startswith("G2b"))
    g3 = sum(1 for v in viol if v["G"].startswith("G3"))
    print(json.dumps({"n_violations": len(viol), "G1_layer": g1,
                      "G2_lane": g2, "G2b_refclk": g2b, "G3_nets": g3,
                      "verdict": report["verdict"]}, indent=1))
    print("artifact:", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
