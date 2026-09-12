#!/usr/bin/env python3
"""CO-82：【L2 可审计性】L4 工程文件 net_settings（网类 + 网-类指派）对齐意图。

缺陷 F-82-1（F-80-1 同族、CO-81 闸的**覆盖盲区**）：
  `k2_v4_8L.l4.kicad_pro` 只有 `Default` 一个网类、且 `netclass_assignments` 为空；
  而意图件 `k2_v4_8L.kicad_pro` 有 4 类（Default/LOW_SPEED/PCIe85/POWER）+ 146 条指派。
  ⇒ 用该工程文件跑 DRC 时 **PCIe85/LOW_SPEED/POWER 语义完全不生效**
    （PCIe85 的 clearance 0.175 / diff_pair_gap 0.175 / width 0.205 等均不施加），
    而 `Default` 自身又偏严（clearance 0.2 vs 意图 0.1、track 0.2 vs 0.09、via 0.6/0.3 vs 0.35/0.2）。
  CO-81 闸只覆盖 `design_settings.rules` + `rule_severities`，故漏检本项（本件一并补闸）。

修复：把意图件的 `net_settings.classes` 与 `net_settings.netclass_assignments` 对齐进 `.l4.kicad_pro`。
只读意图件；不改板/图纸。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
INTENT = K2 / "k2_v4_8L.kicad_pro"
L4PRO = K2 / "k2_v4_8L.l4.kicad_pro"
OUT = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co82_l4_project_netclass_align.json"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    a = json.loads(INTENT.read_text(encoding="utf-8"))
    b = json.loads(L4PRO.read_text(encoding="utf-8"))
    before = s16(L4PRO)
    ia = a["net_settings"]
    ib = b["net_settings"]
    cls_before = [c.get("name") for c in ib.get("classes", [])]
    asg_before = len(ib.get("netclass_assignments") or {})
    ib["classes"] = json.loads(json.dumps(ia["classes"]))
    ib["netclass_assignments"] = json.loads(json.dumps(ia.get("netclass_assignments") or {}))
    L4PRO.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    chk = json.loads(L4PRO.read_text(encoding="utf-8"))["net_settings"]
    assert [c["name"] for c in chk["classes"]] == [c["name"] for c in ia["classes"]]
    assert chk["netclass_assignments"] == (ia.get("netclass_assignments") or {})
    rec = {"artifact": "m13_v57_co82_l4_project_netclass_align", "schema": 1, "revision": "CO-82.1",
           "nature": "L2 可审计性：L4 工程文件 net_settings 对齐意图",
           "finding": "F-82-1：.l4.kicad_pro 仅 Default 网类且无指派 ⇒ DRC 不施加 PCIe85/LOW_SPEED/POWER 语义；"
                      "CO-81 闸仅覆盖 design_settings.rules/rule_severities，存在覆盖盲区",
           "intent_project": {"file": "k2_v4_8L.kicad_pro", "sha16": s16(INTENT)},
           "l4_project": {"file": "k2_v4_8L.l4.kicad_pro", "sha16_before": before, "sha16_after": s16(L4PRO)},
           "classes_before": cls_before, "assignments_before": asg_before,
           "classes_after": [c["name"] for c in chk["classes"]],
           "assignments_after": len(chk["netclass_assignments"]),
           "geometry_impact": "none（不改板/图纸；仅工程文件网类设置）",
           "redline": "意图件只读；阈值取自意图件，不放宽。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"before": before, "after": s16(L4PRO), "classes_before": cls_before,
                      "classes_after": rec["classes_after"], "assignments": rec["assignments_after"],
                      "record": s16(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
