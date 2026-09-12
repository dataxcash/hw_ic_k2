#!/usr/bin/env python3
"""CO-122：【L2 自裁 · 机判】CO-118 B.Cu 桥冲突的 R1 路径（4 个 target 改用 In4 承载）是否可闭式成立。

背景（CO-118）：CO-74 红线 `bcu_power_copper_policy=PROHIBITED`（B.Cu 不得铺电力铜/搭桥）
↔ CO-112 三桥区 `bridge_layer="B.Cu"`，其 `na_scope_v1.bcu_bridge_zone_targets` 以
「经 B.Cu 桥接 ⇒ 无需本网 In4 铜覆盖」作 N/A 裁定。若禁令成立，则 4 个 target 无载体：
  P3V3   : C84.1 / U2.5 / U4.3（via 均落在**异网** MCU_VDD_WEST 内）
  P3V3_AUX: J4.A9（via 落在**异网** P3V3_EAST 内）
R1 = 改用 In4 承载（本网 pocket + 连回本网 In4 平面），属《宪法》ch.2『PDN 架构 / 走廊分配』= **L2**；
R2 = 放宽 L1 v2.0 冻结的「B.Cu 空置」= owner。

机判问题（每 target 独立）：在**声明式有限家族**内（零坐标搜索），是否存在
  pocket(声明外扩 w) ∪ 走廊(声明侧/声明 y 偏移 dy/声明高 h) 使
  (a) 覆盖 target via；(b) 异网 via 净距 ≥ 0.375（闭式，同 CO-121）；(c) **宿主平面连续性**保持
  （走廊把异网区切开的代价，逐宿主判定）；(d) 走廊与本网 In4 平面面积搭接 ≥ MERGE_MIN；(e) pocket↔走廊搭接 ≥ MERGE_MIN。
无成员通过 ⇒ 显式 NOT_FEASIBLE_WITHIN_DECLARED_FAMILY（不放宽阈值）⇒ R1 非 L2 手段内可闭合，升级 owner（R2）。
只读；不改 SPEC/板/阈值/冻结源；零坐标搜索；施加路径若成立另开 CO（不得与本件混同）。
CLI: python3 tools/p3_v57_co122_bridge_target_recarrier_gate.py
"""
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-15.json"
CO121 = STEP2 / "m13_v57_co121_west_aux_allocation_ruling.json"
REC = STEP2 / "m13_v57_co122_bridge_target_recarrier_gate.json"
CARD = STEP2 / "m13_v57_CO122_bridge_target_recarrier_gate.md"
TARGETS = [("C84", "1", "P3V3"), ("U2", "5", "P3V3"), ("U4", "3", "P3V3"), ("J4", "A9", "P3V3_AUX")]
POCKET_W = (0.75, 1.0, 1.5)
CORR_H = (0.5, 0.8)
CORR_DY = (0.0, 0.5, -0.5, 1.0, -1.0)


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load_co121():
    sp = importlib.util.spec_from_file_location(
        "co121", K2 / "tools/p3_v57_co121_west_aux_allocation_ruling.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def zone_rect(z):
    pg = z["polygon"]
    return (min(p[0] for p in pg), min(p[1] for p in pg), max(p[0] for p in pg), max(p[1] for p in pg))


def overlap(a, b):
    ox = min(a[2], b[2]) - max(a[0], b[0])
    oy = min(a[3], b[3]) - max(a[1], b[1])
    return (ox, oy) if ox > 0 and oy > 0 else (0.0, 0.0)


def main() -> int:
    c = load_co121()
    spec, _rules, west, _t, west_mcu, foreign_all = c.load()
    zd = spec["pd"]["zone_defs"]
    zs = {z["zone"]: z for z in zd["power_zones"]}
    east = zone_rect(zs["P3V3_EAST"])
    entries = {(e["ref"], e["pad"]): e for e in zd["power_pad_connect"]["entries"]}
    co121 = json.loads(CO121.read_text())
    aux_rects = [[float(v) for v in r] for r in co121["family"][co121["chosen"]]]
    aux_net_plane = aux_rects                      # 本网 (P3V3_AUX) In4 平面 = CO-121 chosen（待 CO-122b 施加）
    plane = {"P3V3": [east], "P3V3_AUX": aux_net_plane}
    host_of = {"P3V3": "MCU_VDD_WEST", "P3V3_AUX": "P3V3_EAST"}
    rows, fam_all = [], {}
    for ref, pad, net in TARGETS:
        e = entries.get((ref, pad))
        if e is None:
            e = next(x for x in zd["power_pad_connect"]["entries"]
                     if x["ref"] == ref and x["pad"] == pad)
        via = (float(e["via_pos"][0]), float(e["via_pos"][1]))
        hz = host_of[net]
        host_zone = west if hz == "MCU_VDD_WEST" else east
        host_vias = {f"{x['ref']}.{x['pad']}": tuple(map(float, x["via_pos"]))
                     for x in zd["power_pad_connect"]["entries"]
                     if x["net"] == ("MCU_VDD" if hz == "MCU_VDD_WEST" else "P3V3")
                     and host_zone[0] <= x["via_pos"][0] <= host_zone[2]
                     and host_zone[1] <= x["via_pos"][1] <= host_zone[3]}
        foreign = {k: v for k, v in foreign_all.items() if not k.startswith(f"({net})") and f"({net})" not in k}
        eastward = net == "P3V3"
        best, fam = None, {}
        for w in POCKET_W:
            pocket = (via[0] - w, via[1] - w, via[0] + w, via[1] + w)
            for h in CORR_H:
                for dy in CORR_DY:
                    yc = via[1] + dy
                    if eastward:
                        corr = (via[0], yc - h / 2, east[0] + 0.5, yc + h / 2)
                    else:
                        corr = (aux_rects[2][2] - 0.5, yc - h / 2, via[0], yc + h / 2)
                    rects = [pocket, corr]
                    key = f"{ref}.{pad}|w{w}|h{h}|dy{dy:+.1f}"
                    j = c.judge(rects, host_zone, {f"{ref}.{pad}": via}, host_vias, foreign)
                    merges = [overlap(pocket, corr)]
                    plane_ov = [overlap(corr, p) for p in plane[net]]
                    d_ok = bool(merges) and min(min(m) for m in merges) >= c.MERGE_MIN - c.EPS
                    f_ok = any(min(o) >= c.MERGE_MIN - c.EPS for o in plane_ov)
                    j["d_pocket_corridor_merge"] = d_ok
                    j["f_reaches_own_plane"] = f_ok
                    j["ok"] = j["ok"] and d_ok and f_ok
                    fam[key] = j
                    if j["ok"] and best is None:
                        best = key
        fam_all[f"{ref}.{pad}({net})"] = {"host_zone": hz, "via": list(via),
                                          "own_plane": net, "best": best,
                                          "n_members": len(fam), "results": fam}
        rows.append({"target": f"{ref}.{pad}", "net": net, "host_zone": hz, "via": list(via),
                     "verdict": "FEASIBLE" if best else "NOT_FEASIBLE_WITHIN_DECLARED_FAMILY",
                     "chosen": best})
    ok_all = all(r["verdict"] == "FEASIBLE" for r in rows)
    verdict = ("R1_FEASIBLE_ALL" if ok_all else
               ("R1_INFEASIBLE_SOME" if any(r["verdict"].startswith("NOT") for r in rows) else "INDETERMINATE"))
    rec = {
        "artifact": "m13_v57_co122_bridge_target_recarrier_gate", "schema": 1, "revision": "CO-122.1",
        "nature": "L2 自裁 · 机判：CO-118 R1（4 target 改 In4 承载）是否可闭式成立（声明式有限家族，零搜索）",
        "level": {"ruling": "L2",
                  "basis": "《宪法》ch.2：PDN 架构/走廊分配 = L2；R2（放宽 L1 v2.0『B.Cu 空置』）才归 owner"},
        "inputs": {"spec_sha16": s16(SPEC), "co121_record_sha16": s16(CO121),
                   "co118_record": "m13_v57_co118_bcu_bridge_conflict_check.json"},
        "clearance_mm": 0.375, "merge_min_mm": c.MERGE_MIN,
        "families": fam_all, "rows": rows, "verdict": verdict,
        "consequence": ("R1 在声明式家族内全过 ⇒ 4 target 可由 In4 承载，B.Cu 桥声明（CO-112）应退役为"
                        "『不可用（CO-74 禁令）』并经 CO-122b 施加" if ok_all else
                        "R1 家族内**未全过**：可行 target 可由 In4 承载；未过者**仅证「本声明式家族内无合法成员」**"
                        "（家族受限；未证明不存在 —— 同 CO-94『family-limit 命中』口径，禁把家族不足写成不可行）。"
                        "未过者归 owner（R2 放宽 B.Cu 红线 / L1 变更），或由后继以**更细声明 palette** 复核（逼近搜索红线须先自证不越界）"),
        "family_limited_caveat": ("负结果为**家族受限**负结果（负控/牙齿见 CO-121 口径）；"
                                  "J4.A9 的 f 测 30/30 未过源于家族只含直走廊、不含「向西行至本网 AUX band 的 L 形段」⇒"
                                  "属家族不足而非不可行证据；U2.5 需更细 dy/h palette 复核（dy 步长 0.5、h∈{0.5,0.8} 已声明）"),
        "teeth_note": "本件无负控牙齿（属探索性机判）；负结果按 family-limited 口径报告，不以家族不足当不可行证据",
        "redline": "只读；不改 SPEC/板/阈值/冻结源；零坐标搜索；本件不施加",
        "board_sha16": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-122 — L2 机判：CO-118 R1（4 target 改 In4 承载）可行性", "",
             f"- verdict：**{verdict}**", f"- 净距 {0.375}mm / 搭接 ≥ {c.MERGE_MIN}mm / 零坐标搜索", "",
             "| target | net | 宿主区 | 家族成员 | 判定 | chosen |", "|---|---|---|---|---|---|"]
    for k, v in fam_all.items():
        r = next(x for x in rows if k.startswith(x["target"]))
        lines.append(f"| {k} | {r['net']} | {v['host_zone']} | {v['n_members']} | {r['verdict']} | {v['best'] or '-'} |")
    lines += ["", f"后果：{rec['consequence']}", "", "施加（若 R1 成立）另开 CO-122b；本件零 SPEC/板改动。"]
    CARD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "rows": rows, "rec_sha16": s16(REC), "card_sha16": s16(CARD)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
