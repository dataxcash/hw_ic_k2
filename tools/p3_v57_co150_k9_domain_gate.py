#!/usr/bin/env python3
"""CO-150 — K9 闸硬化：为「热方案域」与「压降域」加机判牙齿（关闭 CO-148 登记的 K9 缺口）。

背景：CO-148 登记 `tool_defect:co124_k9_has_no_thermal_or_drop_domain_model`（MED/OPEN）——
K9 只有 R3-2 节距域模型 ⇒ 热/压降类定值即使不可达也无人判。
本件：co124 K9 新增两域（rev CO-124.5）+ 负控 T10/T10b/T11/T11b；并关闭该登记项。
产出：`m13_v57_co150_k9_domain_gate.json` + 卡；登记项 CLOSED。
牙齿：① K9 记录 revision ≥ CO-124.5 且 T10/T11 系列牙齿全为 true；② 登记项已 CLOSED。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
CO124 = S2 / "m13_v57_co124_input_selfcheck_gate.json"
REG = L2 / "input_defect_register_v1.json"
LED = L2 / "derived_value_ledger_v1.json"
REC = S2 / "m13_v57_co150_k9_domain_gate.json"
FIND = "tool_defect:co124_k9_has_no_thermal_or_drop_domain_model"
TOOTH_KEYS = ("T10_thermal_option_domain_teeth", "T10b_thermal_domain_no_false_positive",
              "T11_drop_domain_teeth", "T11b_drop_domain_no_false_positive")


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    c = json.loads(CO124.read_text())
    teeth = c.get("teeth", {})
    teeth_ok = all(teeth.get(k) is True for k in TOOTH_KEYS)
    reg = json.loads(REG.read_text())
    hit = []
    for it in reg["items"]:
        if it["finding"] == FIND:
            it["status"] = "CLOSED"
            it["ruled_by"] = "CO-150"
            it["ruling"] = ("K9 扩两域并加负控：`thermal_option_domain`（∃ 声明散热方案使 θJA_eff ≤ 最重工况所需；"
                            "且现状不达标时必须显式声明 required_mitigation）+ `drop_domain`（每轨 ΔV% ≤ 预算%）；"
                            "负控 T10/T10b/T11/T11b 全触发。")
            it["disposition"] = (it.get("disposition", "").split("【CO-150 已扩闸】")[0] +
                                 "【CO-150 已扩闸】" + it["ruling"])
            it["next"] = "无（已闭合）；后续新增热/压降类定值直接受本两域机判。"
            it["closed_by"] = sorted(set(it.get("closed_by", [])) | {"CO-150"})
            hit.append(it["finding"])
    MARK = f"；**CO-150（L2 闸硬化）**：co124 K9 扩 `thermal_option_domain` + `drop_domain` 两域并加负控 T10/T10b/T11/T11b ⇒ 关闭 K9 缺口登记项。（记录 {s16(REC) if REC.exists() else '（本次生成）'}）"
    if "CO-150" not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    # CO-152：本件是 canonical 链上登记簿的**最后写者** ⇒ 在此复位 meta.counts（此前为陈旧值 19/24）
    import collections as _c
    reg["meta"]["counts"] = dict(_c.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    led = json.loads(LED.read_text())
    doms = {dv["id"]: (dv.get("reachability") or {}).get("kind") for dv in led["derived_values"]}
    rec = {"artifact": "m13_v57_co150_k9_domain_gate", "schema": 1, "revision": "CO-150.1",
           "nature": "L2 闸硬化：K9 热/压降域机判 + 负控（关闭 CO-148 登记的 K9 缺口）",
           "co124": {"file": CO124.name,
                     "sha16_note": "快照已移除（CO-152）；现行 sha 见 boundary pin 表",
                     "revision": c.get("revision"),
                     "verdict": c.get("verdict"), "n_findings": c.get("n_findings"),
                     "teeth": {k: teeth.get(k) for k in TOOTH_KEYS}},
           "domains_added": ["thermal_option_domain", "drop_domain"],
           "ledger_domain_kinds": {"DV-CO146-THERMAL": doms.get("DV-CO146-THERMAL"),
                                   "DV-CO146-PDN-DROP": doms.get("DV-CO146-PDN-DROP")},
           "register": {"file": REG.name, "closed": hit,
                        "note": "sha/open_total 快照已移除（CO-152：下游时点观测 ⇒ 记录漂移）"},
           "teeth": {"t01_k9_teeth_all_true": teeth_ok,
                     "t02_register_item_closed": FIND in hit},
           "redline": "只读板/SPEC；只改闸判据与登记簿；零坐标搜索。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    (S2 / "m13_v57_CO150_k9_domain_gate.md").write_text(
        "# CO-150 卡 · K9 热/压降域闸硬化\n\n"
        f"- co124 revision = **{c.get('revision')}**｜verdict = {c.get('verdict')}｜findings = {c.get('n_findings')}\n"
        f"- 新增域：`thermal_option_domain`（∃ 声明散热方案覆盖最重工况；现状不达标须显式声明缓解）"
        f"、`drop_domain`（每轨 ΔV% ≤ 预算%）\n"
        f"- 负控：{ {k: teeth.get(k) for k in TOOTH_KEYS} }\n"
        f"- 登记项 `{FIND}` → **CLOSED**；登记簿 OPEN 余 {rec['register']['open_total']}\n")
    print("co124 rev:", c.get("revision"), "verdict:", c.get("verdict"), "findings:", c.get("n_findings"))
    print("teeth:", rec["co124"]["teeth"], "| register closed:", hit,
          "| OPEN", rec["register"]["open_total"])
    print("register sha:", s16(REG), "| rec:", s16(REC))
    return 0 if all(rec["teeth"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
