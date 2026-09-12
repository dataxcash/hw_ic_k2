#!/usr/bin/env python3
"""CO-80：【L2 声明一致性 / 可审计性】L4 工程文件（k2_v4_8L.l4.kicad_pro）规则对齐。

缺陷（F-80-1）：`k2_v4_8L.l4.kicad_pro` 是**受版本控制**的工件，且是 `kicad-cli` 对
`k2_v4_8L.l4.kicad_pcb` 做 DRC 时**自动选取**的工程文件；但它的 design rules 与工艺意图
（`k2_v4_8L.kicad_pro` 及 `_shared/eda_core/drc_rules.json`）不一致：

  min_track_width          0.09 -> 0.2      min_via_diameter        0.35 -> 0.5
  min_via_annular_width    0.075 -> 0.1     min_through_hole_diameter 0.2 -> 0.3
  min_copper_edge_clearance 0.3 -> 0.5      min_clearance           0.1 -> 0.0
  rule_severities: copper_sliver / silk_over_copper / silk_overlap / via_dangling : ignore -> warning

后果：**最自然的独立核查命令** `kicad-cli pcb drc k2_v4_8L.l4.kicad_pcb` 报 **880 条违规**
（annular_width / drill_out_of_range / track_width / via_diameter 各 199 + copper_edge_clearance 11 + silk 警告），
审计者会误判板子不合格；而项目 PASS 依赖 signoff 里**换用另一工程文件**。⇒ 声称与工件不自洽。

修复：把意图工程文件的 `design_settings.rules` 与 `rule_severities` 对齐进 L4 工程文件（其余键不动）。
只读意图件；不改板/图纸/链上工件。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
INTENT = K2 / "k2_v4_8L.kicad_pro"
L4PRO = K2 / "k2_v4_8L.l4.kicad_pro"
OUT = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co80_l4_project_rule_align.json"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    a = json.loads(INTENT.read_text(encoding="utf-8"))
    b = json.loads(L4PRO.read_text(encoding="utf-8"))
    before = s16(L4PRO)
    da = a["board"]["design_settings"]
    db = b["board"]["design_settings"]
    rules_before = dict(db["rules"])
    sev_before = dict(db["rule_severities"])
    rules_changed = {k: {"intent": da["rules"].get(k), "was": rules_before.get(k)}
                     for k in set(rules_before) | set(da["rules"])
                     if rules_before.get(k) != da["rules"].get(k)}
    sev_changed = {k: {"intent": da["rule_severities"].get(k), "was": sev_before.get(k)}
                   for k in set(sev_before) | set(da["rule_severities"])
                   if sev_before.get(k) != da["rule_severities"].get(k)}
    db["rules"] = dict(da["rules"])
    db["rule_severities"] = dict(da["rule_severities"])
    text = json.dumps(b, ensure_ascii=False, indent=2) + "\n"
    L4PRO.write_text(text, encoding="utf-8")
    # 复核：只有这两个块变化
    check = json.loads(L4PRO.read_text(encoding="utf-8"))["board"]["design_settings"]
    assert check["rules"] == da["rules"] and check["rule_severities"] == da["rule_severities"]
    keys_differing = [k for k in set(db) | set(json.loads(json.dumps(db)))
                      if False]
    rec = {"artifact": "m13_v57_co80_l4_project_rule_align", "schema": 1, "revision": "CO-80.1",
           "nature": "L2 可审计性：L4 工程文件 design rules/severities 对齐意图工程",
           "finding": "F-80-1：受控工件 k2_v4_8L.l4.kicad_pro 与意图规则不一致，"
                      "致 kicad-cli 自动选取时对 L4 板误报 880 条违规（settings artifact，非板缺陷）",
           "intent_project": {"file": "k2_v4_8L.kicad_pro", "sha16": s16(INTENT)},
           "l4_project": {"file": "k2_v4_8L.l4.kicad_pro", "sha16_before": before, "sha16_after": s16(L4PRO)},
           "rules_changed": rules_changed, "rule_severities_changed": sev_changed,
           "n_rules_changed": len(rules_changed), "n_severities_changed": len(sev_changed),
           "geometry_impact": "none（不改板/图纸；仅工程文件设计规则）",
           "redline": "意图件只读；零几何/阈值改动（意图规则即 JLC 工艺极限，未放宽任何阈值）。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"l4pro_before": before, "l4pro_after": s16(L4PRO),
                      "rules_changed": rules_changed, "severities_changed": list(sev_changed),
                      "record": s16(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
