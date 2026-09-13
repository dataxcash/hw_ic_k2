#!/usr/bin/env python3
"""CO-148 — U6（DS320PR1601）热裁定：手册输入下的 Tj 超限 → 登记 + L2 处置 + 台账更新。

事实（手册 CNLS683 + 板实测）：PACT 4.7–7.0W / θJA 17.4°C/W / ψJB 5.9 / Tj 上限 120°C；
监理定值环境 40°C 自然对流 ⇒ Tj 121.8°C（EQ0-2 typ）～161.8°C（EQ5-19 max）；ψJB+h 交叉路线 173.6°C。
产出：`L2/L2_RULING_u6_thermal_v1.md` + `m13_v57_co148_thermal_ruling.json` + 登记簿 +2 + 台账 2 项更新。
牙齿：① 最坏 Tj > 上限；② U6 GND 球数 > 该域 GND via 数（散热路径缺口）；③ 登记/台账落位。
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
PMR = S2 / "m13_v57_co146_pm_eval.json"
U6IN = S2 / "m13_v57_co148_u6_ds320pr1601_inputs.json"
REG = L2 / "input_defect_register_v1.json"
LED = L2 / "derived_value_ledger_v1.json"
DOC = L2 / "L2_RULING_u6_thermal_v1.md"
REC = S2 / "m13_v57_co148_thermal_ruling.json"
IDS = ("thermal_defect:u6_ds320pr1601_tj_exceeds_limit_at_40c_natural_convection",
       "tool_defect:co124_k9_has_no_thermal_or_drop_domain_model")


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def u6_thermal_path() -> dict:
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))
    u6 = next(fp for fp in b.GetFootprints() if fp.GetReference() == "U6")
    bb = u6.GetBoundingBox()
    x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
    x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
    gnd_balls = sum(1 for p in u6.Pads() if p.GetNetname() == "GND")
    vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)
            and x0 <= pcbnew.ToMM(t.GetPosition().x) <= x1 and y0 <= pcbnew.ToMM(t.GetPosition().y) <= y1]
    return {"u6_pads": len(list(u6.Pads())), "gnd_balls": gnd_balls,
            "gnd_vias_in_u6_bbox": sum(1 for v in vias if v.GetNetname() == "GND"),
            "all_vias_in_u6_bbox": len(vias),
            "gnd_planes": ["In1.Cu", "In3.Cu", "In6.Cu"], "bottom_side_thermal_pad": "无（U6 在顶层）"}


def main() -> int:
    pm = json.loads(PMR.read_text())
    u6 = json.loads(U6IN.read_text())
    th = pm["thermal"]
    cases = pm["u6_datasheet"]["cases"]
    worst = max(cases.items(), key=lambda kv: kv[1]["Tj_C"])
    best = min(cases.items(), key=lambda kv: kv[1]["Tj_C"])
    path = u6_thermal_path()
    limit = pm["u6_datasheet"]["TJ_max_C"]
    teeth = {"t01_worst_tj_over_limit": worst[1]["Tj_C"] > limit,
             "t02_gnd_via_deficit": path["gnd_balls"] > path["gnd_vias_in_u6_bbox"]}
    # ── 裁定件 ────────────────────────────────────────────────────────────
    doc = ["# L2 裁定 v1.0 — U6（DS320PR1601）热超限处置（CO-148）", "",
           "> 依据：LAYOUT_CONSTITUTION 第二章（**热机械** = L2 职权）；监理指令 #10 定值表（环境 40°C、自然对流、压降 3%）。",
           "> 输入升级：U6 功耗/热阻由「声明值」→ **数据手册值**（TI SNLS683，入库件 "
           f"`{U6IN.name}` `{s16(U6IN)}`）；板 `{s16(BOARD)}`（未改动）。", "",
           "## 1. 事实（机判，可复算）", "",
           f"- U6 手册：PACT = {u6['inputs']['PACT']}（EQ 档）、θJA(high-K) = {u6['inputs']['theta_ja_highK_C_per_W']}°C/W、"
           f"ψJB = {u6['inputs'].get('psi_jb_C_per_W')}°C/W、θJC(top) = {u6['inputs'].get('theta_jc_top_C_per_W')}°C/W、"
           f"Tj 上限 = **{limit}°C**（推荐工作条件）。",
           f"- 按监理定值（Ta = 40°C、自然对流）：**Tj = {best[1]['Tj_C']}°C（{best[0]}，最轻档）～"
           f"{worst[1]['Tj_C']}°C（{worst[0]}，最重档）** ⇒ **全档超上限**；",
           f"  ψJB + 板级对流交叉路线：ΔT_board = {th['dT_board_C']}°C ⇒ Tj = **{th['routes']['psi_jb_plus_board_route_Tj_C']}°C**（两路一致 FAIL）。",
           f"- 允许环境（自然对流、手册 θJA）：{json.dumps({k: v['Ta_max_C'] for k, v in cases.items()}, ensure_ascii=False)} ⇒ "
           f"**40°C 自然对流下不可运行**（最轻档上限亦仅 {best[1]['Ta_max_C']}°C）。",
           f"- 散热路径实测：U6 {path['u6_pads']} 球 / GND 球 **{path['gnd_balls']}**，U6 域内 GND via 仅 **{path['gnd_vias_in_u6_bbox']}** "
           f"（缺口 {path['gnd_balls'] - path['gnd_vias_in_u6_bbox']}）；GND 平面 = {path['gnd_planes']}；底部无热焊盘。", "",
           "## 2. L2 裁定", "",
           "**R4-1（工程侧，本轮自裁）**：PCB 散热路径为**既定义务**：① U6 域 GND via 阵列补强（在现行「零坐标搜索 + 声明 palette」"
           "口径下由 L3 派生落点）；② 保留并扩大 In1/In3/In6 GND 平面在 U6 域的散热覆盖；③ 底部/U6 域铜面最大化。"
           "**触发条件**：仅当需求方确认仍要 40°C 自然对流或要求风冷/散热片时，随下一轮几何修订一并施加（改几何 ⇒ G4 全链重基线）。", "",
           "**追注（CO-224 / 承 R-CO223-1）**：上列 R4-1 中「U6 域 GND via 阵列」之**义务时点**已变更 —— 现行口径**以 CO-222 为准**"
           "（boundary §95）：阵列**不在 rev-19 交付范围**，改列为**条件动作**（**T1** 首件实测 `Tj(U6) > 117.0 ℃` 或未按 O2 实施 ⇒ 开新 rev，"
           "量化目标 `θJA_eff ≤ 9.5 ℃/W`；**T2** U6 域几何因他因修订 ⇒ 同 rev 一并补阵）。上列「既定义务」为**成文时口径**，历史正文不改（承 CO-213 F-3）。", "",
           "**R4-2（输入冲突，须监理/需求方重裁 input）**：监理指令 #10 定值「40°C、自然对流」与器件手册**不相容**"
           f"（最轻档 EQ0-2 typ 4.7W 即需 Ta ≤ {best[1]['Ta_max_C']}°C；最重档 EQ5-19 max 7.0W 需 θJA_eff ≤ "
           f"{worst[1]['required_theta_ja_C_per_W']}°C/W ≪ 手册 17.4）。**处置选项**：(a) 系统强制风冷/顶部散热片（走 θJC "
           f"{u6['inputs'].get('theta_jc_top_C_per_W')}°C/W 路径）使 θJA_eff ≤ {worst[1]['required_theta_ja_C_per_W']}–"
           f"{best[1]['required_theta_ja_C_per_W']}°C/W；(b) 环境定值降额（≤ {best[1]['Ta_max_C']}°C，仅覆盖最轻档）；"
           "(c) 复核 EQ 档位/功耗假设（本板 PCIe5 长通道通常需高 EQ ⇒ 取最重档偏保守但现实）。"
           "**本项不改需求、不改器件选型**（器件选型 = 需求侧），故只报冲突 + 量化选项，等输入重裁后重跑本件。", "",
           "## 3. 残留与闸缺口", "",
           f"- 登记簿 +2：`{IDS[0]}`（HIGH/OPEN）、`{IDS[1]}`（MED/OPEN，K9 无热/压降域模型 ⇒ 本类不可达性不被机判）。",
           "- 台账：DV-CO146-THERMAL 记 `UNREACHABLE_REGISTERED`（由登记簿承接）；DV-CO146-PDN-DROP 输入升级为手册电流。",
           "- 复评债：CO-148 本件 + CO-146/147 全部产物（另一会话，禁自评）。", ""]
    DOC.write_text("\n".join(doc) + "\n")
    # ── 登记簿 ────────────────────────────────────────────────────────────
    reg = json.loads(REG.read_text())
    new = [
        {"finding": IDS[0], "kind": "IMPLEMENTATION_DEVIATION", "severity": "high",
         "what": f"U6（DS320PR1601，TI SNLS683）手册 PACT **{u6['inputs']['PACT']['0-2']['typ_W']}–"
                 f"{u6['inputs']['PACT']['5-19']['max_W']}W**、θJA(high-K) {u6['inputs']['theta_ja_highK_C_per_W']}°C/W、"
                 f"Tj 上限 **{limit}°C**；按监理定值 40°C 自然对流 ⇒ **Tj {best[1]['Tj_C']}–{worst[1]['Tj_C']}°C 全档超限**"
                 f"（ψJB+h 交叉路线 {th['routes']['psi_jb_plus_board_route_Tj_C']}°C）。CO-146 的 U6 声明功耗 1.5W 偏低约 3–4.7 倍"
                 "（PM 输入缺陷，已由手册值替换）。",
         "refs": ["CO-146", "CO-148", "监理指令 #10"],
         "disposition": "L2 工程侧：PCB 散热路径（U6 域 GND via 补强 / GND 平面覆盖 / 铜面最大化）—— GND via 阵列之义务时点**以 CO-222 为准**（条件动作 T1/T2，boundary §95；rev-19 不改几何）；"
                        "**系统侧须监理重裁定值**：40°C 自然对流与手册不相容 ⇒ (a) 强制风冷/顶部散热片使 θJA_eff ≤ "
                        f"{worst[1]['required_theta_ja_C_per_W']}–{best[1]['required_theta_ja_C_per_W']}°C/W，"
                        f"或 (b) 环境 ≤ {best[1]['Ta_max_C']}°C（仅最轻档），或 (c) 复核 EQ/功耗假设。",
         "status": "OPEN",
         "next": "① 监理/需求方重裁环境/风冷输入（一句话）⇒ 重跑 co146_pm_eval；② L2：U6 域热过孔阵列 = 条件动作（T1/T2，以 CO-222 为准；见 boundary §95）。",
         "evidence": [f"手册入库件 {U6IN.name} {s16(U6IN)}", f"PM 评估 {PMR.name} {s16(PMR)}"],
         "closed_by": []},
        {"finding": IDS[1], "kind": "TOOL_DEFECT", "severity": "medium",
         "what": "co124 K9 的派生值可达性判据**只有 R3-2 节距域模型**（pitch_cap − span − edge）：热（Tj）与压降（ΔV）类定值"
                 "即便不可达也不被机判 ⇒ 「工程定值须可达」在本类上**无牙齿**（本件热超限只能靠登记簿承接）。",
         "refs": ["CO-148", "CO-124"],
         "disposition": "登记（不改闸）：建议 K9 扩「热/压降」域模型（域 = 声明环境（Ta/h/θJA）与声明电流，判据 = Tj ≤ 上限 / ΔV ≤ 预算）；"
                        "在扩判据前，本类不可达性以登记簿显式承接（不得静默）。",
         "status": "OPEN",
         "next": "L2：K9 扩热/压降域模型（含负控）——独立于本件的闸硬化任务。",
         "evidence": ["co124 定义件（不复述 sha：register↔co124 记录互钉会形成不动点；见 boundary §25 表）", "本件 §3"],
         "closed_by": []},
    ]
    have = {it["finding"] for it in reg["items"]}
    added = [it for it in new if it["finding"] not in have]
    for it in reg["items"]:
        if it["finding"] in IDS:
            it.update(next(i for i in new if i["finding"] == it["finding"]))
    reg["items"].extend(added)
    MARK = "；**CO-148**：U6 手册输入（TI SNLS683）⇒ 热 Tj 121.8–161.8°C 超上限 120°C ⇒ 登记 +2（热超限 HIGH / K9 无热域模型 MED）。"
    if "CO-148" not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    # ── 台账更新 ─────────────────────────────────────────────────────────
    led = json.loads(LED.read_text())
    for dv in led["derived_values"]:
        if dv["id"] == "DV-CO146-PDN-DROP":
            for n, r in pm["rails"].items():
                if n in dv["inputs"].get("rails", {}):
                    dv["inputs"]["rails"][n].update({"I_a": r["I_a"], "I_basis": r["I_basis"]})
            dv["inputs"]["source_note"] = "P3V3/12V_IN 电流由 U6 手册 PACT（最重档）导出；其余仍为声明值"
            dv["computed"] = {n: {"R_total_ohm": r["R_total_ohm"], "dV_mV": r["dV_mV"], "drop_pct": r["drop_pct"],
                                  "I_max_at_budget_a": r["I_max_at_budget_a"], "verdict": r["verdict"]}
                              for n, r in pm["rails"].items()}
        if dv["id"] == "DV-CO146-THERMAL":
            dv["inputs"]["u6_source"] = {"artifact": U6IN.name, "sha16": s16(U6IN),
                                         "datasheet": "TI SNLS683 (JUNE 2023)",
                                         "PACT_W": u6["inputs"]["PACT"], "theta_ja_C_per_W": u6["inputs"]["theta_ja_highK_C_per_W"],
                                         "psi_jb_C_per_W": u6["inputs"].get("psi_jb_C_per_W"), "TJ_max_C": limit}
            dv["computed"] = {"cases": cases, "hotspot_Tj_C": th["routes"]["theta_ja_route_hotspot_Tj_C"],
                              "psi_jb_route_Tj_C": th["routes"]["psi_jb_plus_board_route_Tj_C"],
                              "Tj_limit_C": limit, "verdict": "FAIL"}
            dv["reachability"] = {"kind": "declared", "verdict": "UNREACHABLE_REGISTERED",
                                  "predicate": "Tj ≤ Tj_limit（按声明环境 Ta/h 与手册 θJA/ψJB）",
                                  "why": "40°C 自然对流下全 EQ 档超限；处置选项见裁定件 R4-2",
                                  "gate_gap": "co124 K9 无热域模型 ⇒ 本项不可达性由登记簿承接（见 TOOL_DEFECT 项）",
                                  "evidence_ref": {"path": REG.name, "sha16": s16(REG)}}
    LED.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n")
    rec = {"artifact": "m13_v57_co148_thermal_ruling", "schema": 1, "revision": "CO-148.2",
           "nature": "L2 裁定：U6 手册输入下的热超限（登记 + 处置 + 台账）",
           "doc": DOC.name, "doc_sha16": s16(DOC), "board_sha16": s16(BOARD),
           "u6_inputs": {"artifact": U6IN.name, "sha16": s16(U6IN)},
           "pm_eval": {"artifact": PMR.name, "sha16": s16(PMR), "verdict": pm["verdict"]},
           "cases": cases, "worst": {"case": worst[0], "Tj_C": worst[1]["Tj_C"]},
           "best": {"case": best[0], "Tj_C": best[1]["Tj_C"]}, "Tj_limit_C": limit,
           "paths_cross_check": th["routes"], "thermal_path": path,
           "co148_items": list(IDS), "items_added_this_run": [i["finding"] for i in added],
           "register": {"file": REG.name,
                        "note": "sha/计数快照已移除（CO-152/CO-155：下游时点观测 ⇒ 记录漂移；现行 sha 见 boundary pin 表）"},
           "ledger": {"file": LED.name,
                      "note": "sha 快照已移除（CO-152 同上）"},
           "owner_visible_input_conflict": "40°C 自然对流（监理定值）vs 器件手册 ⇒ 须重裁环境/风冷输入（R4-2）",
           "teeth": teeth,
           "redline": "只读板/SPEC；不改几何；零坐标搜索；输出只写 L2 政策层 + 登记簿 + 台账。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("worst Tj:", worst, "| best Tj:", best, "| limit:", limit)
    print("path:", path)
    print("register +%d (total %d, OPEN %d) %s | ledger %s" % (len(added), len(reg["items"]),
          sum(1 for i in reg["items"] if i["status"] == "OPEN"), s16(REG), s16(LED)))
    print("teeth:", teeth)
    return 0 if all(teeth.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
