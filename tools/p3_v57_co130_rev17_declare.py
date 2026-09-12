#!/usr/bin/env python3
"""CO-130：【L2 自裁 · 施加】SPEC rev-16 → **rev-17**（声明层；期望板逐字节不变）。

内容（全部为「声明」变更，不改几何数值/阈值/冻结源；物理施加另开 CO）：
 1) **D-6 定案施加**：`net_classes_override = {"12V_IN": "POWER"}`（CO-128 L2 裁定）。
    后果（派生，非新增阈值）：12V_IN 线宽下限 0.15→0.5（=POWER width）；对异网净距 0.1→0.2（required 0.375）。
 2) **退役三 zone 的 B.Cu 载体声明**（CO-74 `bcu_power_copper_policy=PROHIBITED` ↔ 声明互斥）：
    `P3V3_BCU_BRIDGE_IN4` / `P3V3_AUX_BCU_BRIDGE_IN4` / `MCU_VDD_BCU_RESISTORS_IN4`
    → `bridge_layer: B.Cu → In4.Cu`；旧 `carrier_change` 移入 `retired_carrier_change_bcu`（审计留存，不删）；
    新增 `carrier_final`（In4 载体 + R1 可行性证据引用）。R1 可行性 = CO-122（C84.1/U4.3）+ CO-127（U2.5/J4.A9）。
 3) **`stackup['In4.Cu']` 文本对齐实际 In4 网集** `{P3V3, MCU_VDD, P3V3_AUX}`（CO-124 K3 finding）。
 4) 新增 `plane_reachability_status.unresolved` 中 12V_IN 的 why 文本（D-6 已裁；承载几何仍待 L3 派生）。
白名单断言：只允许上述路径变化，其它任何漂移即 fail。
CLI: python3 tools/p3_v57_co130_rev17_declare.py
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SRC = L3 / "SPEC_k2_v4.spec-rev-16.json"
OUT = L3 / "SPEC_k2_v4.spec-rev-17.json"
REC = STEP2 / "m13_v57_co130_rev17_declare.json"
CARD = STEP2 / "m13_v57_CO130_rev17_declare.md"
BCU_ZONES = ("P3V3_BCU_BRIDGE_IN4", "P3V3_AUX_BCU_BRIDGE_IN4", "MCU_VDD_BCU_RESISTORS_IN4")
R1_EVIDENCE = {
    "C84.1": {"verdict": "FEASIBLE", "co": "CO-122", "ref": "m13_v57_co122_bridge_target_recarrier_gate.json"},
    "U4.3": {"verdict": "FEASIBLE", "co": "CO-122", "ref": "m13_v57_co122_bridge_target_recarrier_gate.json"},
    "U2.5": {"verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER", "co": "CO-127", "ref": "m13_v57_co127_multires_router.json"},
    "J4.A9": {"verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER", "co": "CO-127", "ref": "m13_v57_co127_multires_router.json"},
}


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def flat(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{p}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f"{p}[{i}]")
    else:
        yield p, o


def main() -> int:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    out = json.loads(json.dumps(src))
    out["spec_version"] = "1.1.spec-rev-17"
    out["net_classes_override"] = {"12V_IN": "POWER"}
    out["net_classes_override_basis"] = {
        "co": "CO-128（L2 自裁 D-6 定案）",
        "finding": "pdn_net_not_power_class:12V_IN（CO-124 K8 补审发现）",
        "why_l2": "网级净距/线宽口径 + PDN 承载 = L2（《宪法》ch.2 PDN 架构）；不改网名/域/层数 ⇒ 无 L1 面",
        "rejected": "改网名为 PWR_12V_IN（波及网表/BOM/板/多工件，爆炸半径大且无增益）",
        "derived_effect": {"width_min_mm": 0.5, "clearance_to_foreign_mm": 0.2, "required_to_foreign_via_center_mm": 0.375},
        "effect_note": "DERIVED（= net_classes['POWER']）；本键不新增阈值，仅补网类归属",
        "rerun": "① 已按新类以确定性绕障复判可行（CO-128）；PDN 计划 via 与该网异网最近 1.701mm ⇒ 现计划坐标不受影响",
    }
    zd = out["pd"]["zone_defs"]
    byname = {z["zone"]: z for z in zd["power_zones"]}
    for name in BCU_ZONES:
        z = byname[name]
        old = z.get("carrier_change")
        if old is not None:
            z["retired_carrier_change_bcu"] = {**old, "retired_by": "CO-130（rev-17）",
                                               "retired_basis": "CO-74 PROHIBITED 与『zone 声明 B.Cu 载体』互斥；R1 已证 In4 可行 ⇒ 退役活跃声明，审计留存"}
            del z["carrier_change"]
        z["bridge_layer"] = "In4.Cu"
        z["carrier_final"] = {
            "layer": "In4.Cu", "co": "CO-130（rev-17）",
            "basis": "R1 确定性重承载至 In4（CO-122/CO-127）；实体几何 = L3 施工确定性派生（本 zone polygons/segments 留空，非手工坐标）",
            "r1_proven": True, "r1_evidence": R1_EVIDENCE,
            "co74_still_holds": "bcu_power_copper_policy=PROHIBITED（B.Cu 不得铺电力铜）保持不变；本件只退役与之矛盾的 B.Cu 载体声明",
        }
    out["stackup"]["In4.Cu"] = "POWER_PLANE (P3V3 east / MCU_VDD west / P3V3_AUX island)"
    prs = zd["plane_reachability_status"]
    for u in prs.get("unresolved", []):
        if u["net"] == "12V_IN":
            u["why"] = ("该网仍无 In4 声明区（承载几何待 L3 确定性派生）；网类已由 CO-128 D-6 定案为 POWER、"
                        "① 承载可行性已由 CO-128 以确定性绕障证得 ⇒ 非「未裁」，属「待派生」")
    zd["rev17_recarrier_note_v1"] = {
        "note": "CO-130【L2 自裁 · 施加 rev-17】：D-6 网类（12V_IN→POWER）+ 退役三 zone 的 B.Cu 载体声明 + stackup In4 文本对齐",
        "level_basis": "《宪法》ch.2：PDN 架构/叠层分配 = L2；不改网名/域集合/层数 ⇒ 无 L1 面（先例 CO-74/CO-117/CO-121/CO-122b）",
        "board_expectation": "仅声明键变更，不改任何坐标 ⇒ L4 板期望逐字节不变（由施加后全链复核）",
        "refs": ["CO-74", "CO-112", "CO-118", "CO-122", "CO-127", "CO-128", "CO-129"],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    a, b = dict(flat(src)), dict(flat(out))
    changed = sorted({k for k in set(a) | set(b) if a.get(k) != b.get(k)})
    bcu_idx = [i for i, z in enumerate(zd["power_zones"]) if z["zone"] in BCU_ZONES]
    allowed_pref = (".spec_version", ".net_classes_override.", ".net_classes_override_basis.",
                    ".stackup.In4.Cu", ".pd.zone_defs.rev17_recarrier_note_v1.",
                    ".pd.zone_defs.plane_reachability_status.unresolved")
    allowed_exact = {".net_classes_override"}
    zone_suffix = (".bridge_layer", ".carrier_change", ".retired_carrier_change_bcu",
                   ".carrier_final")
    def _ok(k):
        if k in allowed_exact or k.startswith(allowed_pref):
            return True
        return any(k.startswith(f".pd.zone_defs.power_zones[{i}]") and k.split("]", 1)[1]
                   .startswith(zone_suffix) for i in bcu_idx)
    unexpected = [k for k in changed if not _ok(k)]
    rec = {"artifact": "m13_v57_co130_rev17_declare", "schema": 1, "revision": "CO-130.1",
           "nature": "L2 自裁 · 施加：SPEC rev-16 → rev-17（D-6 网类 + 退役 B.Cu 载体声明 + stackup 文本）",
           "src": SRC.name, "src_sha16": s16(SRC), "out": OUT.name, "out_sha16": s16(OUT),
           "changes": {"net_classes_override": out["net_classes_override"],
                       "bcu_zones_retired": list(BCU_ZONES),
                       "stackup_in4_text": out["stackup"]["In4.Cu"]},
           "changed_paths": changed, "n_changed_paths": len(changed),
           "unexpected_changed_paths": unexpected, "whitelist_ok": not unexpected,
           "r1_evidence": R1_EVIDENCE,
           "board_untouched": True, "board_sha16_l4": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
           "redline": "不改板/几何坐标/阈值/冻结源；历史 SPEC 不改（新文件 bump）；零坐标搜索"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    CARD.write_text("\n".join([
        "# CO-130 — SPEC rev-16 → **rev-17**（L2 自裁 · 声明层施加）", "",
        f"- out：`{OUT.name}` `{rec['out_sha16']}`", f"- changed_paths：{len(changed)}（unexpected {len(unexpected)}）",
        f"- D-6：`net_classes_override = {json.dumps(out['net_classes_override'], ensure_ascii=False)}`（CO-128 L2 定案）",
        f"- 退役 B.Cu 载体声明：{', '.join(BCU_ZONES)}（bridge_layer → In4.Cu；旧 carrier_change 移入 retired_carrier_change_bcu）",
        f"- stackup In4 文本：`{out['stackup']['In4.Cu']}`（对齐实际网集 P3V3/MCU_VDD/P3V3_AUX）",
        f"- R1 证据：{json.dumps(R1_EVIDENCE, ensure_ascii=False)}", "",
        "白名单断言见记录；期望 L4 板逐字节不变（施加后全链复核）。"]), encoding="utf-8")
    print(json.dumps({"out_sha16": rec["out_sha16"], "n_changed_paths": len(changed),
                      "unexpected": unexpected[:8], "whitelist_ok": rec["whitelist_ok"],
                      "rec_sha16": s16(REC)}, ensure_ascii=False, indent=1))
    return 0 if rec["whitelist_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
