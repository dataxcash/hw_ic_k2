#!/usr/bin/env python3
"""CO-179 — 灵敏度牙齿系统性加严（近失 + 点名）（⇒ 登记簿）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.10）
承载。幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co179_sensitivity_teeth_hardening.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"

ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "两处「灵敏度」牙齿为**弱判据**（不针对被判对象）："
          "① `t07b_parity_detector_sensitivity` 比较 `sha256(包内副本) != sha256(ORDER_NOTES.md)` —— 即**两个不同文件**"
          "必不等，属恒真式，**不检验 parity 判据本身**（若 parity 写成恒真/自比，本齿仍 True）；"
          "② `t10b_binding_source_pin_discriminates` 断言 `sha16(JP) != 声明的 pin` —— 只证明「pin 非自身」、"
          "**不检验 pin 判据**能否拒绝错误 pin。",
  "disposition": "CO-179：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.10** —— "
                 "① 提纯函数 `packaged_parity_checks(out_dir, rulings)`（真件与近失用**同一函数**）；`t07b` 改为"
                 "**近失来源证明**（把来源写成「同长单字节翻转」的临时件 ⇒ 经同一函数必判 False）+ 追加字节 ⇒ False；"
                 "② 提纯函数 `instruction_pin_ok(path, declared)`（须 16 位 hex 且等于来源 sha16）；`t10b` 改为"
                 "**近失证明**（正确 pin ⇒ True；**单 hex 位翻转移** ⇒ False；缺/非法 ⇒ False）。"
                 "实测（变异）：把 `copy_parity` 改为恒真 ⇒ **t07b 与 t15b 双双击穿**（rc=1）。",
  "status": "CLOSED", "next": "凡「灵敏度/负控」牙齿须**对同一被判对象做近失扰动**并断言判据翻转；禁「比较两个不同对象」。",
  "evidence": ["CO-179 源码核（改前）：`t07b` = `sha256(06_rulings 副本) != sha256(ORDER_NOTES.md)`；`t10b` = `sha16(JP) != 声明 pin`",
               "CO-179 变异（改后）：`copy_parity` 恒真 ⇒ mutant false teeth = ['t07b_parity_detector_sensitivity', "
               "'t15b_impedance_copy_parity_sensitivity']；还原后逐字节相同"],
  "refs": ["CO-179", "CO-178", "CO-158", "CO-163", "CO-146"], "closed_by": ["CO-179"]},
 {"id": "G-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "九处「灵敏度」牙齿用 `not all(CHECK(...).values())`（**不点名**须翻转的检查项）：t09b / t11b / t11d / "
          "t12b..t12h。该形在「扰动恰好只翻转目标项」时可用，但若**目标项被写死**而扰动偶发翻转了**其它项**，"
          "旧形**仍判通过** ⇒ 判据与目标项可能脱钩（CO-178 教训同族）。",
  "disposition": "CO-179：同升 **CO146-PKG.10** —— 九处一律改为**成分级点名**："
                 "t09b→`zdiff`；t11b→`outer_copper`；t11d→`geometry_matches_binding`；"
                 "t12b→`drc_as_designed_total`；t12c→`impedance_spread_pct`；t12d→`via_census_F.Cu→In2.Cu`；"
                 "t12e→`mask_gap_mm`；t12f→`thermal_Tj_best_worst`；t12g→`jlc_min_track_width_mil`；"
                 "t12h→`rule_copper_edge_clearance`（逐项经**实测**确认该键确实翻转）。",
  "status": "CLOSED", "next": "如实说明：本项为**稳健性**加严（旧形在该组情形下尚可辨别）；今后新齿默认**点名**。",
  "evidence": ["CO-179 实测：逐项扰动后翻转键集已确认（如 t12b={'drc_as_designed_total'}、"
               "t12d={'via_census_F.Cu→In2.Cu'}、t12f={'thermal_Tj_best_worst'}）",
               "CO-179 修后：29 牙齿全 True；点名项与实测翻转一致"],
  "refs": ["CO-179", "CO-178", "CO-171", "CO-146"], "closed_by": ["CO-179"]},
]

MARK = ("；**CO-179（L2 自裁 · 灵敏度牙齿系统性加严）**：① 弱判据（t07b「比较两个不同文件」/ t10b「pin 非自身」）⇒ "
        "`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.10**：parity/pin 判据**函数化** + **同件近失**证明"
        "（变异：`copy_parity` 恒真 ⇒ t07b/t15b 双双击穿）；② 九处 `not all(...)` 改**成分级点名**"
        "（t09b/t11b/t11d/t12b..h）（co179:G-1/G-2）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = "co179:" + it["id"]
        patch = {k: v for k, v in it.items() if k != "id"}
        if f in have:
            have[f].update(patch); updated.append(f)
        else:
            reg["items"].append(dict(finding=f, **patch)); added.append(f)
    if MARK not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"register: +{len(added)} / upd {len(updated)} | counts={reg['meta']['counts']} | sha16 {s16(REG)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
