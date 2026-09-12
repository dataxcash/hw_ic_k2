#!/usr/bin/env python3
"""CO-118：【L2 自裁 · 对抗一致性检查】`bcu_power_copper_policy=PROHIBITED`（CO-74）↔ 3 个 bridge zone 的
`bridge_layer="B.Cu"`+`bcu_bridge_bands`+`na_scope_v1.bcu_bridge_zone_targets`（CO-112）**声明冲突**。

机判（只读，零搜索）：
  A `pd.bcu_power_copper_policy`：policy=PROHIBITED 且 basis 明文含「不得铺电力铜/**搭桥**」
  B 3 个 `L3_CONSTRUCTION_DERIVED` zone：`bridge_layer=="B.Cu"` 且 `bcu_bridge_bands` 非空 ⇒ **声明 B.Cu 桥**
  C 同 3 个 zone：`carrier_change.from=="B.Cu"` 且 `to=="In4.Cu"` ⇒ 同一声明又断言**现行载体 = In4** ⇒ 与 B 互斥
  D `na_scope_v1.bcu_bridge_zone_targets.basis` 明文「经 **B.Cu** 桥接 ⇒ 无需本网 In4 铜覆盖」⇒ N/A 裁定**依赖被禁止的载体**
  E 受影响 ppc target（4）坐标 + 现行 In4 覆盖状态（是否落在任何 In4 polygon 内）
  F 后 CO-117：`MCU_VDD_BCU_RESISTORS_IN4` 的 targets（R29/R31-R34）**已被** MCU_VDD_WEST 扩展覆盖 ⇒ 该 zone 的 B.Cu 桥声明已过时

fail-closed 结论：若 CO-74 的「不得搭桥」为硬红线（不得放宽），则 B.Cu 桥不可依赖 ⇒ CO-112 的 N/A 裁定**不成立** ⇒
E 中 4 个 target 成为 **In4 覆盖义务**（当前未覆盖）⇒ 需 rev-16（In4 小区域几何：P3V3 西区 pocket ×3 + P3V3_AUX band pocket ×1；
后者与 L1「P3V3_AUX 西区/band 归属」同族）。
只读；不改 SPEC/板/阈值/冻结源；本件**不下结论性裁定**，只登记冲突 + 后果 + 处置选项。
CLI: python3 tools/p3_v57_co118_bcu_bridge_conflict_check.py
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-15.json"
CO95 = STEP2 / "m13_v57_co95_in4_reachability.json"
OUT = STEP2 / "m13_v57_co118_bcu_bridge_conflict_check.json"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def pip(pg, x, y):
    ins = False
    for i in range(len(pg)):
        x1, y1 = pg[i]; x2, y2 = pg[(i + 1) % len(pg)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(SPEC)); ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.spec).read_text())
    zd = spec["pd"]["zone_defs"]; pd = spec["pd"]
    pol = pd.get("bcu_power_copper_policy", {})
    zones = [z for z in zd["power_zones"] if z.get("geometry_status") == "L3_CONSTRUCTION_DERIVED"]
    polys = [(z["net"], z["zone"], z["polygon"]) for z in zd["power_zones"] if isinstance(z.get("polygon"), list)]
    ppc = {(e["ref"], str(e["pad"])): e for e in zd["power_pad_connect"]["entries"]}
    co95 = {f"{r['ref']}.{r['pad']}": r for r in json.loads(CO95.read_text())["detail"]}

    checks = {}
    checks["A_policy_prohibits_bridging"] = {
        "ok": pol.get("policy") == "PROHIBITED" and "搭桥" in str(pol.get("basis", "")),
        "policy": pol.get("policy"), "basis": pol.get("basis"), "co": pol.get("co"),
        "note": "CO-74：B.Cu = 高速信号层 ⇒ **不得铺电力铜/搭桥**"}
    bcu_assert = [{"zone": z["zone"], "bridge_layer": z.get("bridge_layer"),
                   "n_bands": len(z.get("bcu_bridge_bands") or []), "source": z.get("bcu_bridge_bands_source"),
                   "targets": z.get("targets")} for z in zones]
    checks["B_zones_declare_bcu_bridge"] = {
        "ok": bool(bcu_assert) and all(b["bridge_layer"] == "B.Cu" and b["n_bands"] > 0 for b in bcu_assert),
        "zones": bcu_assert, "note": "CO-112 D1：3 个 zone = B.Cu 桥（含声明几何带）"}
    carrier = [{"zone": z["zone"], "from": (z.get("carrier_change") or {}).get("from"),
                "to": (z.get("carrier_change") or {}).get("to")} for z in zones]
    checks["C_same_zones_assert_in4_carrier"] = {
        "ok": bool(carrier) and all(c["from"] == "B.Cu" and c["to"] == "In4.Cu" for c in carrier),
        "zones": carrier, "note": "同批 zone 的 `carrier_change`（CO-74）断言现行载体 = **In4** ⇒ 与 B 互斥"}
    na = zd["plane_reachability_status"]["na_scope_v1"]["bcu_bridge_zone_targets"]
    checks["D_na_scope_depends_on_bcu"] = {
        "ok": "B.Cu" in na.get("basis", ""), "basis": na.get("basis"), "ref": na.get("ref"),
        "note": "N/A（无需 In4 铜）**依赖 B.Cu 桥**；若 CO-74 红线成立则 N/A 不成立"}
    zone_of = {}
    for b in bcu_assert:
        for t in (b["targets"] or []):
            zone_of[t.split("(")[0].strip()] = b["zone"]
    aff = []
    for r in co95.values():
        if r["reach"] != "covered_bridge_target":
            continue
        key = f"{r['ref']}.{r['pad']}"
        pos = r["via_pos"]
        inside = [f"{n}:{zn}" for n, zn, pg in polys if pip(pg, pos[0], pos[1])]
        aff.append({"target": key, "net": r["net"], "zone": zone_of.get(key),
                    "via_pos": pos, "reach": r["reach"], "inside_in4_net_zone": inside})
    checks["E_affected_targets_uncovered_if_bcu_forbidden"] = {
        "ok": bool(aff) and all(a_["reach"] == "covered_bridge_target" for a_ in aff),
        "n": len(aff), "targets": aff,
        "note": "这些 target 的 In4 可达性**仅**靠 CO-112 的 B.Cu 桥 N/A 裁定；若 CO-74 禁令成立 ⇒ 其载体缺失（当前不在任何 In4 polygon 内）"}
    rez = [z for z in zones if z["zone"] == "MCU_VDD_BCU_RESISTORS_IN4"]
    rez_cov = []
    if rez:
        west = next(pg for n, zn, pg in polys if zn == "MCU_VDD_WEST")
        for e in zd["power_pad_connect"]["entries"]:
            if e["ref"] in (rez[0].get("targets") or []) and e.get("via_pos") and pip(west, *e["via_pos"]):
                rez_cov.append(f"{e['ref']}.{e['pad']}")
    checks["F_bcu_zone_targets_now_in4_covered"] = {
        "ok": bool(rez_cov), "covered_by_in4_now": sorted(rez_cov),
        "note": "CO-117 把 MCU_VDD_WEST 东缘扩到 57.75 ⇒ R29/R31-R34 已被 In4 覆盖 ⇒ 该 zone 的 B.Cu 桥声明**已过时**（勿再依赖）"}
    def _detect(pol_obj):
        return pol_obj.get("policy") == "PROHIBITED" and "搭桥" in str(pol_obj.get("basis", ""))
    teeth = {
        "policy_detector_nonvacuous": _detect(pol),
        "policy_detector_negative_control": _detect({"policy": "ALLOWED", "basis": "B.Cu 允许电力铜（bridging OK）"}) is False,
        "conflict_detected": checks["B_zones_declare_bcu_bridge"]["ok"] and checks["C_same_zones_assert_in4_carrier"]["ok"],
        "na_scope_relies_on_bcu": checks["D_na_scope_depends_on_bcu"]["ok"],
    }
    teeth["teeth_ok"] = all(bool(v) for v in teeth.values())
    hard = all(v["ok"] for v in checks.values()) and teeth["teeth_ok"]
    conflict = checks["A_policy_prohibits_bridging"]["ok"] and checks["B_zones_declare_bcu_bridge"]["ok"] \
        and checks["C_same_zones_assert_in4_carrier"]["ok"] and checks["D_na_scope_depends_on_bcu"]["ok"]
    rec = {
        "artifact": "m13_v57_co118_bcu_bridge_conflict_check", "schema": 1, "revision": "CO-118.1",
        "nature": "L2 对抗一致性检查：B.Cu 电力铜/搭桥禁令（CO-74）↔ B.Cu 桥声明 + N/A 裁定（CO-112）",
        "inputs": {"spec": Path(a.spec).name, "spec_sha16": s16(Path(a.spec)), "co95_record": s16(CO95)},
        "checks": checks, "teeth": teeth,
        "verdict": ("L2_DECLARATION_CONFLICT_OPEN__FAIL_CLOSED_4_TARGETS_UNCOVERED" if (conflict and hard)
                    else "NO_CONFLICT_DETECTED" if hard else "FAIL(mechanics)"),
        "fail_closed_consequence": ("CO-74 basis 明文『不得铺电力铜/**搭桥**』为红线（不得放宽）⇒ B.Cu 桥不可依赖 ⇒ "
                                    "CO-112 的 N/A 裁定不成立 ⇒ E 中 4 个 target（P3V3: C84.1/U2.5/U4.3；P3V3_AUX: J4.A9）"
                                    "成为 **In4 覆盖义务**且当前未覆盖（D 依赖项失效）"),
        "resolution_options": [
            {"id": "R1", "level": "L2", "action": "撤 `na_scope_v1.bcu_bridge_zone_targets` N/A，把 4 target 转为 In4 覆盖义务 ⇒ rev-16 派生 In4 小区域几何（P3V3 西区 pocket ×3 + P3V3_AUX band pocket ×1，异网 ≥0.2、同网连通），再全链重基线"},
            {"id": "R2", "level": "OWNER/红线", "action": "为『限定桥带』开 CO-74 例外（= 放宽『不得搭桥』红线）⇒ 须 owner/PM 明确授权，L2 不得自放宽"},
            {"id": "R3", "level": "L2/流程", "action": "只撤『bridge_layer=B.Cu』过时字段并保留 carrier_change=In4（CO-117 已覆盖 MCU_VDD 电阻区）——但 P3V3/P3V3_AUX 的 3 target 仍未覆盖，不闭合 R1 的实质"}],
        "non_claims": ["只读；不改 SPEC/板/阈值/冻结源", "本件只登记冲突与后果，不代 owner 做 R2 的红线放宽",
                       "零坐标搜索；坐标只取自声明 palette"],
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"CO-118 verdict={rec['verdict']} | conflict={conflict} hard={hard} | affected={checks['E_affected_targets_uncovered_if_bcu_forbidden']['n']}")
    for a_ in checks["E_affected_targets_uncovered_if_bcu_forbidden"]["targets"]:
        print("   %-9s %-10s @%s reach=%s in=%s" % (a_["net"], a_["target"], a_["via_pos"], a_["reach"], a_["inside_in4_net_zone"]))
    return 0 if hard else 1


if __name__ == "__main__":
    raise SystemExit(main())
