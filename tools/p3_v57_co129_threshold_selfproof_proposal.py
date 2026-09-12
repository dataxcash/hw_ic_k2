#!/usr/bin/env python3
"""CO-129：③ 对间铜边净空 0.875 —— **确定性可达性自证 + 口径修订提案**（按《BASIC_SKILL_VS_REDLINE §4》五项）。

背景（登记项 `threshold_unproved_unregistered:pair_copper_edge_clearance_mm`）：
  L1 硬约束「对间铜边净空 0.875mm（R3-2 3W 强条）」在现行走廊/焊盘场几何内被 CO-86 机判为不可达
  （最小缺额 WEST +0.232 / 焊盘场 +0.682）。依 §4，须先交**自证**（该项属规格缺陷还是工具不够），再出**提案**；
  口径修订的**批准**归 owner（L1 红线），提案是我们的义务。

§4 五项自证：
  1) 目标与判据（可机判谓词）：`∃ L2 构造：对间铜边净空 ≥ 0.875mm`。
     闭式：净空 = 走廊轨距(pitch) − 铜跨(span) ⇒ **pitch_required = span + 0.875**（恒等式，CO-86 同源）。
  2) 输入集 + 确定性算法：pitch 硬上限取自已机判独立实测（CO-85 记录，pin sha）：
     WEST 1.050（球栅逃逸）/ EAST 1.449（图纸 lane.y 均匀）/ 焊盘场 0.600（连接器引脚节距）；
     span 下界由**声明的一阶阻抗模型**（`_shared/eda_core/stackup`，与 CO-71/CO-86 同源）在 85±10%Ω 带内闭式求得。
     算法 = 区间单调性 + 闭式相交；零坐标搜索、零随机。
  3) **算法完备性论证**（为何该类构造无解，而非「家族不够大」）：
     A. **焊盘场（与模型无关，模型自由）**：pitch ≤ 0.600 且 span ≥ 0 ⇒ 净空 ≤ 0.600 < 0.875 ⇒ ∀span 不可达。**完备**。
     B. **WEST（在声明的一阶阻抗模型下完备）**：净空 ≥ 0.875 ⇒ pitch ≥ span+0.875 ≤ 1.050 ⇒ span ≤ 0.175；
        而阻抗带要求 w ≥ w_min 且 Z(w) 在 w 上**严格单调递减**（本件机判）⇒ w_min 为真下界 ⇒ span ≥ 2·w_min+gap = 0.407；
        ⇒ 缺额 ≥ 0.407+0.875−1.050 = **0.232 > 0**。该界对**全体 span** 成立（非网格抽样）。
     C. EAST：pitch ≤ 1.449 ⇒ span ≤ 0.574；交付 span 0.705 缺额 0.131（非主约束，仅记录）。
     ⇒ 结论：0.875 **不是工具不够**，是**阈值几何不可达**（规格缺陷），且与量测/家族无关。
  4) 复现命令 + 原始输出：本件 CLI；并复核 CO-86 记录 sha16 逐字节不变。
  5) 失败/异常记录：写入 rec.failures（若任一牙齿未按预期 ⇒ 该证明作废）。
三只手：T1 焊盘场 span 无关性；T2 假想控制（cap=2.0 ⇒ 0.875 可达，证明闸非恒 FAIL）；T3 阻抗单调性；T4 CO-86 逐字节复现。
输出：**提案 P1（建议）/ P2（备选）**，附分域可达上限表；批准归 owner；本件不改 SPEC/阈值/板/冻结源。
CLI: python3 tools/p3_v57_co129_threshold_selfproof_proposal.py
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-16.json"
CO85 = STEP2 / "m13_v57_co85_nonexecutor_review_pass2.json"
CO86 = STEP2 / "m13_v57_co86_l2_span_option_closure.json"
CO86_TOOL = K2 / "tools/p3_v57_co86_l2_span_option_closure.py"
REC = STEP2 / "m13_v57_co129_threshold_selfproof.json"
CARD = STEP2 / "m13_v57_CO129_threshold_selfproof_proposal.md"
sys.path.insert(0, str(K2.parent / "_shared"))
from eda_core.stackup import _symmetric_stripline_z0 as SL  # noqa: E402

EDGE_REQ = 0.875
TARGET, BAND = 85.0, 0.10
INNER = {"h": 0.50, "t": 0.0175, "er": 3.99}      # In2.Cu / In5.Cu（与 CO-86 同源）
GAP_SPEC = 0.175                                  # SPEC p_gap 备选
CO86_SHA_PIN = "d0a59f85b74687d5"


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def zdiff(w):
    return SL(w, INNER["h"], INNER["t"], INNER["er"], GAP_SPEC)


def main() -> int:
    c85 = json.loads(CO85.read_text(encoding="utf-8"))
    v6 = c85["V6_corridor_pitch_independent"]
    caps = {"WEST_MCIO_TO_CHIP": v6["WEST_MCIO_TO_CHIP"]["pitch_mm"],
            "EAST_CHIP_TO_J2": v6["EAST_CHIP_TO_J2"]["pitch_mm"],
            "pad_field": 0.600}                        # J2/J3/J4 引脚节距（CO-85/CO-86 同源）
    failures = []
    # T3 阻抗单调性：Z(w) 在 w 上严格递减 ⇒ 带内最小 w 即真下界（完备性所需）
    ws = [round(0.050 + i * 0.001, 4) for i in range(0, 351)]
    zs = [zdiff(w) for w in ws]
    mono = all(zs[i] > zs[i + 1] for i in range(len(zs) - 1))
    hi = TARGET * (1 + BAND); lo = TARGET * (1 - BAND)
    in_band = [w for w, z in zip(ws, zs) if lo <= z <= hi]
    w_min = min(in_band) if in_band else None          # 带内最小 w ⇒ 最小 span（对可行性最有利）⇒ 完备性下界用它
    w_nom = min(((w, abs(z - TARGET)) for w, z in zip(ws, zs)), key=lambda t: t[1])[0]
    span_min = round(2 * w_min + GAP_SPEC, 4) if w_min is not None else None
    span_nom = round(2 * w_nom + GAP_SPEC, 4)
    teeth = {"T3_impedance_monotone_decreasing": mono,
             "T1_pad_field_span_independent": all(span + EDGE_REQ > caps["pad_field"] for span in [0.0, 0.2, span_min or 0.407, 0.705, 1.0])}
    # T2 假想控制：cap=2.0 时 0.875 应可达（闸非恒 FAIL）
    teeth["T2_hypothetical_control_reachable"] = bool(span_min is not None and (span_min + EDGE_REQ) <= 2.0)
    # T4 CO-86 逐字节复现（独立证据，非本件重算）
    try:
        subprocess.run([sys.executable, str(CO86_TOOL)], cwd=str(K2), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        teeth["T4_co86_reproduced_byte_identical"] = (s16(CO86) == CO86_SHA_PIN)
    except Exception as e:                                     # pragma: no cover
        teeth["T4_co86_reproduced_byte_identical"] = False
        failures.append(f"CO-86 复现异常：{type(e).__name__}: {e}")
    if not mono:
        failures.append("阻抗非单调 ⇒ w_min 非真下界，WEST 完备性论证作废")
    if w_min is None:
        failures.append("85±10%Ω 带内无解 ⇒ span_min 不可得")
    # 分域可达上限表（net-min span→max edge = cap − span）
    domains = []
    for name, cap in caps.items():
        if name == "pad_field":
            bound = round(cap - span_min, 4) if span_min is not None else None
            reason = "pitch 上限 0.600 < 0.875 ⇒ 与 span 无关，恒不可达"
        else:
            bound = round(cap - span_min, 4) if span_min is not None else None
            reason = f"pitch 上限 {cap} ⇒ span ≤ {round(cap - EDGE_REQ, 4)} 但 span_min={span_min}"
        domains.append({"domain": name, "pitch_cap_mm": cap, "span_min_mm": span_min,
                        "max_achievable_edge_mm": bound, "deficit_vs_0p875": round(EDGE_REQ - bound, 4) if bound is not None else None,
                        "note": reason})
    rows = []
    for label, span in (("delivered_0.705", 0.705), ("option_p_gap_0.585", 0.585),
                        ("impedance_band_span_min", span_min), ("impedance_nominal_85ohm", span_nom)):
        need = round(span + EDGE_REQ, 4)
        rows.append({"label": label, "span_mm": span, "pitch_required_mm": need,
                     "deficit_vs_WEST": round(need - caps["WEST_MCIO_TO_CHIP"], 4),
                     "deficit_vs_EAST": round(need - caps["EAST_CHIP_TO_J2"], 4),
                     "deficit_vs_pad_field": round(need - caps["pad_field"], 4),
                     "passes_all_caps": bool(need <= min(caps.values()))})
    teeth["T1_pad_field_span_independent"] = teeth["T1_pad_field_span_independent"] and (EDGE_REQ > caps["pad_field"])
    teeth_ok = all(teeth.values())
    verdict = ("THRESHOLD_0p875_PROVED_UNREACHABLE_PROPOSAL_ISSUED"
               if teeth_ok and span_min is not None and all(not r["passes_all_caps"] for r in rows)
               else "SELFPROOF_INCOMPLETE")
    proof = {
        "predicate": "∃ L2 构造：对间铜边净空 ≥ 0.875mm（可机判）",
        "identity": "净空 = 走廊轨距(pitch) − 铜跨(span) ⇒ pitch_required = span + 0.875（CO-86 恒等式）",
        "inputs": {"pitch_caps_mm": caps, "pitch_caps_source": "CO-85 V6（球栅逃逸 WEST / 图纸 lane.y EAST）+ 连接器引脚节距 pad_field",
                   "span_min_mm": span_min, "span_min_source": f"声明的一阶阻抗模型（_shared/eda_core/stackup stripline 85±10%Ω，gap={GAP_SPEC}）",
                   "co85_sha16": s16(CO85), "co86_sha16": s16(CO86)},
        "completeness": {
            "A_pad_field_model_free": "pitch ≤ 0.600 且 span ≥ 0 ⇒ 净空 ≤ 0.600 < 0.875 ⇒ ∀span 不可达（与阻抗/家族无关）",
            "B_west_under_declared_impedance": ("净空 ≥ 0.875 ⇒ span ≤ 1.050−0.875 = 0.175；Z(w) 严格递减 ⇒ 带内最小 w="
                                                f"{w_min}（Z≈{round(zdiff(w_min),2)}Ω，仍属 85±10%）⇒ span ≥ 2w_min+gap = {span_min}"
                                                f" ⇒ 缺额 ≥ {round(span_min+EDGE_REQ-1.050,4)} > 0（对全体 span 成立；"
                                                f"CO-86 的名义 85Ω 解 span={span_nom} 给出更大缺额 {round(span_nom+EDGE_REQ-1.050,4)}）"),
            "C_east": "pitch ≤ 1.449 ⇒ span ≤ 0.574；交付 span 0.705 缺额 0.131（非主约束）",
            "why_not_family_limit": "WEST/焊盘场用**区间单调性 + 闭式相交**导出全 span 界，非枚举候选；焊盘场结论完全无需阻抗模型",
            "caveat": "WEST 的 span_min 依赖**一阶阻抗模型**；SI9000/板厂券（外部输入）到货后须复核 w_min（缺该输入不影响焊盘场结论）"},
        "failures": failures,
    }
    proposal = {
        "status": "待 owner 批准（L1 红线：口径修订权在 owner）",
        "P1_recommended": {
            "form": "以 3W **原义**为主口径：对间铜边净空 ≥ 2·w_对（等价于中心距 ≥ 3W）；0.875 降为「w ≥ 0.4375 时的推论」",
            "why": "0.875 = 2×0.4375 只在铜宽 0.4375 时与原义一致；实际对内 w = 0.116..0.205 ⇒ 原义要求净空 0.232..0.410，几何可达",
            "executable_check": "edge_clearance_mm ≥ 2 × trace_width_mm（可机判；厂可核）"},
        "P2_alternative": {
            "form": "保留绝对阈值但改为**分域可达上限**（cap − span_min）：" +
                    "；".join(f"{d['domain']} ≤ {d['max_achievable_edge_mm']}" for d in domains),
            "why": "若必须保留绝对口径，则以 L2 可达上限为界；但焊盘场上限极小（见上表），说明绝对口径不是合适的可执行形式",
            "risk": "分域阈值随 span/叠层变动，维护成本高，且仍不是 3W 原义"},
        "evidence_table": rows,
        "pending_external": "SI9000/板厂阻抗券 ⇒ 复核 w_min/span_min（CO-86 已标记一阶模型）",
    }
    rec = {"artifact": "m13_v57_co129_threshold_selfproof", "schema": 1, "revision": "CO-129.1",
           "nature": "③ 对间铜边净空 0.875 的确定性可达性自证（§4 五项）+ 口径修订提案",
           "definition_doc": {"path": "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md",
                              "sha16": s16(K2 / "pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md")},
           "self_proof_4": proof,
           "impedance_resolution": {"band_ohm": [lo, hi], "w_min_mm": w_min, "span_min_mm": span_min,
                                    "zdiff_at_w_min_ohm": round(zdiff(w_min), 2) if w_min else None,
                                    "w_nominal_85ohm_mm": w_nom, "span_nominal_85ohm_mm": span_nom,
                                    "note": "完备性下界用带内最小 span（对可行性最有利）；CO-86 用名义 85Ω 解"},
           "domain_caps": domains, "rows": rows, "proposal": proposal,
           "teeth": teeth, "teeth_ok": teeth_ok, "verdict": verdict,
           "spec_sha16": s16(SPEC), "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
           "redline": "只读；不改 SPEC/阈值/板/冻结源；无随机、零坐标搜索；提案不改任何冻结值"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-129 — ③ 对间铜边净空 0.875 自证 + 口径提案", "",
             f"- verdict：**{verdict}**", f"- identity：`{proof['identity']}`",
             f"- span_min(带内最小) = **{span_min}**（w_min={w_min}，Z≈{round(zdiff(w_min),2)}Ω）；span_nom(名义85Ω) = {span_nom}；pitch caps = {caps}", "",
             "| span | pitch_required | 缺额 WEST | 缺额 EAST | 缺额焊盘场 | 全过 |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['label']} | {r['pitch_required_mm']} | {r['deficit_vs_WEST']} | "
                     f"{r['deficit_vs_EAST']} | {r['deficit_vs_pad_field']} | {r['passes_all_caps']} |")
    lines += ["", "**完备性**：焊盘场 = 模型自由全 span 不可达（0.600 < 0.875）；WEST = 声明阻抗模型下 span ≥ "
              f"{span_min} ⇒ 缺额 ≥ {round(span_min+EDGE_REQ-1.050,4)}（区间单调，非抽样）。", "",
              f"**提案 P1（建议）**：{proposal['P1_recommended']['form']}。",
              f"**提案 P2（备选）**：{proposal['P2_alternative']['form']}。", "",
              f"牙齿：{json.dumps(teeth, ensure_ascii=False)}",
              f"失败/异常：{json.dumps(failures, ensure_ascii=False)}", "",
              "本件零 SPEC/阈值/板改动；口径修订批准归 owner。"]
    CARD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "w_min": w_min, "span_min": span_min,
                      "caps": caps, "min_deficit_WEST": round(span_min + EDGE_REQ - caps["WEST_MCIO_TO_CHIP"], 4),
                      "teeth": teeth, "failures": failures,
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
