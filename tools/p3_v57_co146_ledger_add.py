#!/usr/bin/env python3
"""CO-146 — 派生值台账登记（K9 口径：来源原则 id + 派生式 + 输入 + 可达性）。

幂等（按 id 覆盖）。可达性一律 kind=declared（无 domains 键）——本件派生值的域不是 R3-2 节距模型，
不得借用 pitch_cap 域（否则 K9 域重算误判）。可达性由**闭式一阶计算 + hash-pin 证据件**支撑。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
LED = L2 / "derived_value_ledger_v1.json"
IMP = STEP2 / "m13_v57_co146_impedance_table.json"
PM = STEP2 / "m13_v57_co146_pm_eval.json"


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    led = json.loads(LED.read_text())
    imp, pm = json.loads(IMP.read_text()), json.loads(PM.read_text())
    reqs = {r["id"]: r for r in led["requirements"]}
    reqs.setdefault("REQ-ZDIFF", {
        "id": "REQ-ZDIFF",
        "statement": "高速差分通道阻抗受控 ⇒ 交付几何须使差分阻抗落目标窗口内（板厂阻抗控制服务为保证路径）",
        "source_principle_ref": "SPEC impedance.{target_zdiff,tolerance_pct,coupon_required} + 监理指令 #10 定值表",
        "frozen": True})
    reqs.setdefault("REQ-PDN-DROP", {
        "id": "REQ-PDN-DROP",
        "statement": "电源分配网络压降受控 ⇒ 各轨最坏压降不超预算（域内电源铜承载足量）",
        "source_principle_ref": "LAYOUT_CONSTITUTION ch.5 §4（PDN 压降达标）+ 监理指令 #10 定值表",
        "frozen": True})
    reqs.setdefault("REQ-THERM", {
        "id": "REQ-THERM",
        "statement": "热机械可靠 ⇒ 器件结温不超上限（按声明环境与对流条件）",
        "source_principle_ref": "LAYOUT_CONSTITUTION ch.2（L2 裁判标准含热）+ 监理指令 #10 定值表",
        "frozen": True})
    led["requirements"] = [reqs[k] for k in sorted(reqs)]

    z = imp["rows"][0]
    new_dv = [
        {"id": "DV-CO146-ZDIFF",
         "requirement": "REQ-ZDIFF",
         "form": "Zdiff(w,g,h,b,er) ∈ target±tol　（双闭式模型交叉核对：IPC-2141 族 / Hammerstad–Jensen+Cohn）",
         "inputs": {"w_by_layer": {r["layer"]: r["w_mm"] for r in imp["rows"]},
                    "gap_delivered": {r["layer"]: r["s_mm"] for r in imp["rows"]},
                    "h_or_b": {r["layer"]: r["h_or_b_mm"] for r in imp["rows"]},
                    "er": {r["layer"]: r["er"] for r in imp["rows"]},
                    "target_zdiff": imp["target_zdiff"], "tolerance_pct": imp["tolerance_pct"],
                    "cu_t_m": {"outer": 3.5e-5, "inner": 1.75e-5},
                    "source": "SPEC impedance.per_layer / stackup.dielectric_8l（JLC08161H）"},
         "computed": {"window_ohm": imp["window_ohm"],
                      "zdiff": {r["layer"]: r["zdiff"] for r in imp["rows"]},
                      "nominal_w_for_85": {r["layer"]: r["nominal_w_for_85"] for r in imp["rows"]},
                      "deviation_pct": {r["layer"]: r["deviation_pct"] for r in imp["rows"]},
                      "watch_nominal_max": imp.get("watch", [])},
         "reachability": {"kind": "declared", "verdict": "REACHABLE",
                          "predicate": "as-built 对内净距下，两模型 Zdiff 均落 85Ω±10%（见 computed）",
                          "basis": imp.get("verdict_basis"),
                          "method": "闭式一阶工程近似；终判 = JLC 阻抗控制服务（±10%）",
                          "evidence_ref": {"path": IMP.name, "sha16": s16(IMP)}}},
        {"id": "DV-CO146-PDN-DROP",
         "requirement": "REQ-PDN-DROP",
         "form": "ΔV = I·(R_plane + R_via/N)　且　ΔV/V_rail ≤ 预算",
         "inputs": {"rails": {n: {"I_a": r["I_a"], "I_basis": r["I_basis"]} for n, r in pm["rails"].items()},
                    "drop_budget_pct": pm["declared_inputs"]["supervisor_values_指令10"]["drop_budget_pct"],
                    "copper_oz": {"outer": 1.0, "inner": 0.5},
                    "rho_cu_20C": pm["declared_inputs"]["engineering_declared"]["rho_cu_20C"]["value"],
                    "ambient_C": pm["declared_inputs"]["supervisor_values_指令10"]["ambient_C"],
                    "disclaimer": pm["declared_inputs"]["DISCLAIMER"]},
         "computed": {n: {"R_total_ohm": r["R_total_ohm"], "dV_mV": r["dV_mV"], "drop_pct": r["drop_pct"],
                          "I_max_at_budget_a": r["I_max_at_budget_a"], "verdict": r["verdict"]}
                      for n, r in pm["rails"].items()},
         "reachability": {"kind": "declared", "verdict": "REACHABLE",
                          "predicate": "各轨 I_max@预算 ≥ 声明电流（余量见 computed）",
                          "basis": "几何取自交付板 zone 声明域（filled 缓存不可读）；电流为显式声明值（非实测）",
                          "evidence_ref": {"path": PM.name, "sha16": s16(PM)}}},
        {"id": "DV-CO146-THERMAL",
         "requirement": "REQ-THERM",
         "form": "Tj = Ta + P_total/(h·2A_board) + P_dev·θJA ≤ Tj_limit",
         "inputs": {"ambient_C": pm["declared_inputs"]["supervisor_values_指令10"]["ambient_C"],
                    "convection": pm["declared_inputs"]["supervisor_values_指令10"]["convection"],
                    "h_conv": pm["declared_inputs"]["engineering_declared"]["h_conv"]["value"],
                    "devices": pm["declared_inputs"]["thermal_devices"],
                    "Tj_limit_C": pm["declared_inputs"]["engineering_declared"]["tj_limit_C"]["value"]},
         "computed": {"P_total_W": pm["thermal"]["P_total_W"], "dT_board_C": pm["thermal"]["dT_board_C"],
                      "T_board_C": pm["thermal"]["T_board_C"], "Tj": pm["thermal"]["Tj"],
                      "hotspot_Tj_C": pm["thermal"]["hotspot_Tj_C"], "verdict": pm["thermal"]["verdict"]},
         "reachability": {"kind": "declared", "verdict": "REACHABLE",
                          "predicate": "热点 Tj < Tj_limit（见 computed）",
                          "basis": "P/θJA/h 为显式声明值（非实测）⇒ 器件手册到位后须替换重跑",
                          "evidence_ref": {"path": PM.name, "sha16": s16(PM)}}},
    ]
    have = {d["id"]: i for i, d in enumerate(led["derived_values"])}
    for dv in new_dv:
        if dv["id"] in have:
            led["derived_values"][have[dv["id"]]] = dv
        else:
            led["derived_values"].append(dv)
    LED.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n")
    print("ledger sha16:", s16(LED), "| n_dv:", len(led["derived_values"]),
          "| ids:", [d["id"] for d in led["derived_values"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
