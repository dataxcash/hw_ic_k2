#!/usr/bin/env python3
"""CO-136：【L2 自裁 · 闸卫生续】关闭 CO-135 报告项 F5(b)/F6 + 强化 F1 牙齿。

对象（均为工具/声明/登记卫生，无 L1 项）：
  F6 co106 连续性检测器牙齿原钉死板内定点 (60.0,50.0) 为「In4 无铜」；P3V3_EAST 随 CO-107/CO-117 覆盖该点
     ⇒ 牙齿假阴性、teeth_ok=False 长期带病。改数据无关合成正/负控（只测 pip 分「有铜/无铜」）⇒ rev CO-106.2。
  F5(b) co124 记录硬编码定义件「v1.0 提议件」，实际件 = BASIC_SKILL_VS_REDLINE_v1.1.md ⇒ 版本由文件名派生 ⇒ rev CO-124.2。
  F1   co77 表格行 citation 覆盖新增负控牙齿（合成表格行 + 漂移 sha ⇒ 必抓）⇒ rev CO-77.5。
本件只**校验**上述不变量并对 2 条 TOOL_DEFECT 登记做闭环核对；不改 SPEC/板/冻结源；零坐标搜索。
注意：本记录**不读 boundary**（使其可被 boundary §14 引用而不形成 sha 不动点）。
CLI: python3 tools/p3_v57_co136_gate_hygiene.py
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
REC = S2 / "m13_v57_co136_gate_hygiene.json"
CARD = S2 / "m13_v57_CO136_gate_hygiene.md"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    co106 = json.loads((S2 / "m13_v57_co106_reference_plane_gate.json").read_text(encoding="utf-8"))
    co124 = json.loads((S2 / "m13_v57_co124_input_selfcheck_gate.json").read_text(encoding="utf-8"))
    co77 = json.loads((S2 / "m13_v57_co77_closure_declaration_sweep.json").read_text(encoding="utf-8"))
    reg = json.loads((L2 / "input_defect_register_v1.json").read_text(encoding="utf-8"))
    regf = {i["finding"]: i for i in reg["items"]}

    checks = {
        "F6_co106_teeth_all_true": all(v is True for k, v in co106["teeth"].items() if k != "teeth_ok")
                                   and co106["teeth"]["teeth_ok"] is True,
        "F6_co106_teeth_no_stale_point": co106["revision"] == "CO-106.2",
        "F5b_co124_doc_version": co124["definition_doc"]["status"].startswith("v1.1")
                                 and co124["definition_doc"]["path"].endswith("BASIC_SKILL_VS_REDLINE_v1.1.md"),
        "F5b_co124_findings_still_zero": co124["n_findings"] == 0 and co124["verdict"] == "PASS",
        "F1_co77_table_teeth": co77["teeth"]["table_row_citation_detected"] is True and co77["teeth_ok"] is True,
        "F1_co77_no_mismatch": co77["citation_check"]["mismatches"] == [] and co77["verdict"] == "PASS",
        "REG_co124_label_closed": regf.get("tool_defect:co124_definition_doc_version_label", {}).get("kind") == "TOOL_DEFECT"
                                  and regf.get("tool_defect:co124_definition_doc_version_label", {}).get("status") == "CLOSED",
        "REG_co106_tooth_closed": regf.get("tool_defect:co106_continuity_tooth_stale_point", {}).get("kind") == "TOOL_DEFECT"
                                  and regf.get("tool_defect:co106_continuity_tooth_stale_point", {}).get("status") == "CLOSED",
    }
    verdict = "PASS" if all(checks.values()) else "FAIL"
    rec = {
        "artifact": "m13_v57_co136_gate_hygiene", "schema": 1, "revision": "CO-136",
        "nature": "L2 自裁 · 闸卫生续：关闭 CO-135 F5(b)/F6、强化 F1 牙齿、登记簿闭环",
        "closed_findings": {
            "F6": {"target": "co106 continuity tooth", "fix": "数据无关合成正/负控", "rev": "CO-106.2",
                   "teeth": co106["teeth"]},
            "F5b": {"target": "co124 definition_doc 版本标签", "fix": "版本由文件名派生", "rev": co124["revision"],
                    "status": co124["definition_doc"]["status"]},
            "F1": {"target": "co77 表格行 citation 覆盖", "fix": "正则扩内联+表格 + 负控牙齿", "rev": co77["revision"],
                   "teeth": co77["teeth"]},
        },
        "register": {"n_items": len(reg["items"]), "kinds": reg.get("meta", {}).get("counts", {})},
        "checks": checks, "verdict": verdict,
        "redline": "只读；不改 SPEC/板/冻结源；零坐标搜索；本记录不读 boundary（可被 §14 引用）",
        # 注：不放 co77 记录 sha —— 其含 boundary doc_sha16 ⇒ 与「§14 引用本记录」形成传递不动点。
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-136 — L2 闸卫生续（关闭 CO-135 F5(b)/F6）", "",
             f"- verdict：**{verdict}**",
             f"- F6：co106 `teeth={json.dumps(co106['teeth'], ensure_ascii=False)}`（rev {co106['revision']}）",
             f"- F5(b)：co124 定义件 `{co124['definition_doc']['path']}` → `{co124['definition_doc']['status']}`",
             f"- F1：co77 表格行牙齿 `{co77['teeth']}`，mismatches `{len(co77['citation_check']['mismatches'])}`", "",
             "| 校验 | 通过 |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in checks.items()]
    lines += ["", "登记簿：新增并关闭 2 条 TOOL_DEFECT；OPEN 仍 1（as-built 偏差，待外部输入）。", ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "checks": checks, "rec_sha16": s16(REC), "card_sha16": s16(CARD)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
