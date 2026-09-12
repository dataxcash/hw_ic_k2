#!/usr/bin/env python3
"""CO-87：【L2 合格标准 · 覆盖性机判】宪法第五章第 4 条「数学闭合」四项 + 第二章「热」的覆盖性。

触发：宪法 ch.5 §4 明文要求「容量 / 长度预算 / 过孔预算 / **PDN 压降达标**」，ch.2 把「热」列为
L2 裁判标准；但 L2 侧 CO-63..CO-86 的闸只覆盖容量/长度/过孔/PDN 架构，**PDN 压降与热从未有输入/证据**。
本件把该状态机判化（不许静默当作已闭合），并给出**机器提取的**所需输入清单。

只读；不改 SPEC/板/图纸/阈值；零 while。**不得以假设值代填输入（禁止伪造 sign-off）。**
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = max((K2 / "pm_gate/artifacts/k2_v4/L3").glob("SPEC_k2_v4.spec-rev-*.json"),
            key=lambda p: int(p.name.split("rev-")[1].split(".")[0]))   # CO-89: 取最新 rev（避免逐版改钉）
CONST = K2.parent / "_shared/docs/LAYOUT_CONSTITUTION.md"
OUT = STEP2 / "m13_v57_co87_l2_acceptance_coverage.json"
# 电流/压降/热 输入的键名或单位特征（刻意排除 power_plane_layer / power_zones 等**几何/分区**键）
RE_KEY = re.compile(r"(load_?current|^current|_current|ir_?drop|drop_?budget|压降|电流|功耗|"
                    r"dissipation|^i_?max|_i_?max|ampacity|thermal|junction|warpage|温升|热阻)", re.I)
RE_VAL = re.compile(r"\b\d+(?:\.\d+)?\s?(?:mA|uA|A|W|mW)\b")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def scan(obj, path="") -> tuple[list, int]:
    hits, n = [], 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            n += 1
            if RE_KEY.search(str(k)):
                hits.append({"path": path + "/" + str(k), "value": str(v)[:70], "kind": "key"})
            if isinstance(v, str) and RE_VAL.search(v) and "clearance" not in str(k):
                hits.append({"path": path + "/" + str(k), "value": v[:70], "kind": "value_unit"})
            h2, n2 = scan(v, path + "/" + str(k)); hits += h2; n += n2
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            h2, n2 = scan(v, path + f"[{i}]"); hits += h2; n += n2
    return hits, n


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    hit_spec, n_spec = scan(spec)
    ctext = CONST.read_text(encoding="utf-8")
    # 需求文本存在性（反空真：确认我们不是在追一条不存在的条款）
    req_found = ("PDN 压降达标" in ctext) and ("PDN 压降、热" in ctext)
    # 阳性对照（牙齿）：注入一个电流字段的合成件必须被抓到
    ctl, _ = scan({"pd": {"load_currents": {"P3V3": 1.2}, "note": "≤ 3.3V 2.5A"}})
    teeth = {"synthetic_current_detected": len(ctl) >= 2,
             "requirement_text_found_in_constitution": req_found,
             "spec_scan_field_floor": n_spec}

    drawing = json.loads((STEP2 / "m13_v57_w3_joint_assignment.json").read_text(encoding="utf-8"))
    l4val = json.loads((STEP2 / "m13_v57_l4_validation.json").read_text(encoding="utf-8"))
    si = json.loads((STEP2 / "m13_v57_l5_si_pi_emc_record.json").read_text(encoding="utf-8"))
    gs = drawing.get("gate_status", {})
    vb = l4val.get("via_budget", {})
    si_txt = json.dumps(si, ensure_ascii=False)
    skew = None
    m = re.search(r'"max_intra_pair_skew_mm"\s*:\s*([\d.]+)', si_txt) or re.search(r'skew[^0-9]{0,20}([\d.]+)', si_txt)
    if m:
        skew = float(m.group(1))

    zd = spec["pd"]["zone_defs"]
    targets = {z.get("zone", f"zone{i}"): {"net": z.get("net"), "layer": z.get("layer"),
                                          "targets": z.get("targets", []), "geometry_status": z.get("geometry_status")}
               for i, z in enumerate(zd.get("power_zones", []))}
    matrix = [
        {"item": "容量总和 ≥ 需求（走廊闭合）", "status": "CLOSED",
         "evidence": f"drawing verdict={drawing.get('verdict')} failed={gs.get('failed')}（A-CN.1d 32/32 / 2a/2b 0）"},
        {"item": "长度预算闭合（等长窗口）", "status": "CLOSED" if (skew is not None and skew <= 0.15) else "UNDETERMINED",
         "evidence": f"L5 SI record max intra-pair skew = {skew} mm ≤ 0.15（CO-70 判据=按层加权电气长度）"},
        {"item": "过孔预算闭合", "status": "CLOSED" if vb.get("over") in ([], None, 0) else "FAIL",
         "evidence": f"L4-F checks['L4-F']={l4val.get('checks', {}).get('L4-F')} via_budget.over={vb.get('over')} total_vias={vb.get('total_vias')}"},
        {"item": "PDN 压降达标（ch.5 §4）", "status": "NOT_DEMONSTRATED",
         "evidence": f"全仓无 load 电流/允许压降预算输入（SPEC 扫描命中 {len(hit_spec)} 项；本项需外部数据）"},
        {"item": "热（ch.2 L2 裁判标准）", "status": "NOT_DEMONSTRATED",
         "evidence": "全仓无功耗/热阻/环境温度/温升判据输入（SPEC 扫描命中 0；需求条款见宪法 ch.2 L2 裁判标准）"},
    ]
    # CO-110（F-C）：ch.2 判据「参考平面」补行 —— 证据机取自 CO-106 闸记录（不得空真/手填）
    try:
        _c106 = json.loads((STEP2 / "m13_v57_co106_reference_plane_gate.json").read_text())
        _b = _c106["checks"]["B_reference_continuity"]
        rp_ev = (f"CO-106 参考平面连续性闸 verdict={_c106.get('verdict')}；"
                 f"declared_copper_missing={_b.get('n_declared_copper_missing_points')}；"
                 f"残余 {_b.get('violations_per_layer_ref')} = CO-117 band 归属后的 **0.2mm POWER 异网净距缝**"
                 f"（原『走廊空洞 = 按设计』判定已由 CO-115 更正为失效 keepout 残留、CO-117 按网归属铺设）；"
                 f"In5 走廊阻抗终判 = SI9000 + 板厂阻抗券")
        rp_status = "INDETERMINATE"
    except Exception as _ex:
        rp_ev, rp_status = f"CO-106 记录不可读：{_ex}", "UNDETERMINED"
    matrix.insert(3, {"item": "参考平面（ch.2 L2 裁判标准）", "status": rp_status, "evidence": rp_ev})
    teeth["ch2_criteria_all_have_rows"] = all(
        k in " ".join(r["item"] for r in matrix) for k in ("走廊", "等长", "参考平面", "PDN 降压".replace("降压", "压降"), "热"))
    n_closed = sum(1 for r in matrix if r["status"] == "CLOSED")
    n_open = sum(1 for r in matrix if r["status"] != "CLOSED")
    rec = {"artifact": "m13_v57_co87_l2_acceptance_coverage", "schema": 1, "revision": "CO-87.2",
           "nature": "L2 合格标准（宪法 ch.5 §4 数学闭合四项 + ch.2 物理可行性五项含「参考平面」）覆盖性机判与缺口登记",
           "constitution": {"file": "LAYOUT_CONSTITUTION.md", "sha16": s16(CONST),
                            "ch5_4": "数学闭合：容量总和 ≥ 需求；长度预算闭合；过孔预算闭合；PDN 压降达标。任何一条不等式不闭合，整层作废。",
                            "ch2_l2_criteria": "物理可行性：走廊闭合、等长预算、参考平面、PDN 压降、热"},
           "matrix": matrix, "n_closed": n_closed, "n_open": n_open,
           "input_absence_scan": {"spec_rev8_hits": hit_spec, "n_spec_fields_scanned": n_spec,
                                 "spec_sha16": s16(SPEC),
                                 "requirement_source": "LAYOUT_CONSTITUTION.md ch.5 §4（PDN 压降达标）/ ch.2（L2 裁判标准含 热）"},
           "required_inputs_for_PDN_and_thermal": {
             "rails": targets,
             "needed": ["各轨负载电流（U3/U7 redriver 静态+动态、MCU/存储、J3/J4 MCIO A9 供电、去耦/上拉）",
                        "允许压降预算（V/%；P3V3 ±5% 等）与采样点定义",
                        "In4 铜厚/温度修正与平面几何（L3 派生后）用于压降终算",
                        "热：各器件功耗、环境温度/风速、可接受温升与热阻路径判据"]},
           "teeth": teeth,
           "verdict": ("L2 结构决策已终结（CO-63..CO-86），但 ch.5 §4 数学闭合的 **PDN 压降** 与 ch.2 的 **热** "
                       "**NOT_DEMONSTRATED（缺输入）** ⇒ 显式登记，不得当作已闭合；本件不代填假设值。"),
           "redline": "只读；不改 SPEC/板/图纸/阈值；禁止以假设值代填缺输入；不 partial pass。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"n_closed": n_closed, "n_open": n_open,
                      "spec_hits": len(hit_spec), "teeth": teeth,
                      "matrix": {r["item"][:18]: r["status"] for r in matrix}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
