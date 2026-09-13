#!/usr/bin/env python3
"""CO-178 — DFM 逐项限值须由能力表派生（⇒ 登记簿）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.5，t08）
承载。幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co178_drc_item_limit_derivation.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"

ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "DFM 闸 `_items()` 的逐项判定表里内嵌**硬编码派生值**：板尺寸下限写死 `≥3×3mm`/`3.0`、"
          "阻抗控制层集写死 `(4,6,8,…,20,32)`、最小线宽写死 `3.5mil`、环宽写死 `单边 ≥0.075mm`、"
          "表面处理写死 `6 层及以上`、最小过孔孔壁文本写 `≥0.15mm` 而**判据实为 ≥0.2mm**（文本 ≠ 强制限）"
          "⇒ 能力表（其值已由 CO-177 绑到抓取件）与**判定表文本**脱钩：能力表变更后判定表文本可留陈旧"
          "（本族缺陷已连出 CO-163/170/171/173/175/176/177）。",
  "disposition": "CO-178：`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.5** —— `_items(m, asd, jlcrun, j=None)` "
                 "可注入能力表；上述硬编码一律改由 `JLC8`（+ `MIL_MM`）派生（板尺寸下限取 `board_min_mm`、层集由 "
                 "`impedance_control_layers.value` 解析、mil 由 `MIL_MM` 换算、单边环宽取 `via_annular_note.value/2`、"
                 "HASL 层数由 `surface_finish.quote` 解析、孔壁文本明示「本板按 JLC 建议值判」）；新增 "
                 "`ITEM_DERIVATION_CASES`（13 情形）+ 纯函数 `item_limit_derivation_checks()` + 牙齿 **t08**"
                 "（逐项**派生性证明**：扰动能力表字段 ⇒ 该项 `jlc_limit` 文本**必变**，硬编码则不变 ⇒ 判不通过）。",
  "status": "CLOSED", "next": "判定表文本与判据须**同源**（文本写 0.15 而判 0.2 之类须显式声明口径）。",
  "evidence": ["CO-178 实测（改前源码核）：`_items()` 内 `≥3×3mm` / `(4,6,…,32)` / `(3.5mil)` / `单边 ≥0.075mm` / `6 层及以上` 为字面量",
               "CO-178 修后：t08 十三情形全 True（扰动 ⇒ 文本必变）；判定表文本逐项由 JLC8 派生"],
  "refs": ["CO-178", "CO-177", "CO-171", "CO-146"], "closed_by": ["CO-178"]},
]

MARK = ("；**CO-178（L2 自裁 · 记录派生数字绑定续）**：DFM 逐项判定表内嵌硬编码派生值（板尺寸下限/阻抗控制层集/mil/单边环宽/"
        "HASL 层数/孔壁口径）⇒ `p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.5**：一律由能力表派生 + 牙齿 **t08**"
        "（13 情形**派生性证明**：扰动能力表 ⇒ 限值文本必变）（co178:G-1）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = "co178:" + it["id"]
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
