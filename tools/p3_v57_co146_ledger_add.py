#!/usr/bin/env python3
"""CO-146 — 派生值台账登记（K9 口径：来源原则 id + 派生式 + 输入 + 可达性）。

CO-153 收窄：本件现**仅** upsert `DV-CO146-ZDIFF`（其证据 pin = 阻抗表记录的 sha16）——
PDN-DROP 的域/证据归 CO-153 归一、输入/computed 归 CO-149；THERMAL 归 CO-148/CO-149。
（原三 DV 一并重写会 **clobber** 上述归属 —— 曾致 `drop_domain` 静默丢失、T11 牙齿失效。）

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
         "computed": imp["dv_computed_zdiff"],   # CO-156（F-6）：与 evidence_ref.key_path 指向的证据块同源
         "reachability": {"kind": "declared", "verdict": "REACHABLE",
                          "predicate": "as-built 对内净距下，两模型 Zdiff 均落 85Ω±10%（见 computed）",
                          "basis": imp.get("verdict_basis"),
                          "method": "闭式一阶工程近似；终判 = JLC 阻抗控制服务（±10%）",
                          "evidence_ref": {"path": IMP.name, "sha16": s16(IMP),
                                            "key_path": "dv_computed_zdiff"}}},
    ]   # CO-153：本件**仅**维护 DV-CO146-ZDIFF 证据 pin；PDN-DROP/THERMAL 可达性归 CO-149/CO-150/CO-153

    # CO-153：pm_eval schema 自 CO-148 起改用 routes/T_board（无 Tj/hotspot_Tj_C）⇒ 该 DV 归 CO-148/CO-149 拥有；
    # 本件改为**仅在字段齐备时**登记，避免 schema 漂移导致 KeyError（这正是本件曾失修、被移出复现序的根因）。
    if {"Tj", "hotspot_Tj_C"} <= set(pm.get("thermal") or {}):
        new_dv.append(
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
                              "evidence_ref": {"path": PM.name, "sha16": s16(PM),
                                               "key_path": "thermal"}}})
    else:
        print("note(CO-153): pm_eval 无 Tj/hotspot_Tj_C（CO-148 起 schema）⇒ 跳过 DV-CO146-THERMAL（归 CO-148/CO-149 拥有）")
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
