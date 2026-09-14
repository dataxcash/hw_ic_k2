#!/usr/bin/env python3
"""CO-227 — L2 自裁（义务时点跨载明面同源 + 载明面名集等式机判化）发现入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co227:F-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**义务时点之载明面枚举无机判齿（域收窄 = 空真）**：CO-222 之 U6 域 GND via 阵列义务时点，其载明面自 CO-224（§97）起以「名集等式」自称 7 面，"
             "但该等式**无机判齿**；CO-225 F-4 实测其域 = 「所声明 grep 目标」= **域收窄**（漏 `L2/input_defect_register_v1.json` 第 8 面）⇒ 违 "
             "**R-CO223-1**（义务时点须跨件同源）/ **R-CO224-1**（载明面须名集等式枚举）/ **R-CO225-1**（无机判齿即空真）。",
     "disposition": "CO-227（L2 自裁）：入机判 runner 静态齿 **t37_obligation_same_source_bound** —— ① 载明面**域显式** + **名集等式**（域内命中集 == "
                    "`OBLIGATION_MARKERS_DECLARED` ∪ 显式豁免，**双向**：禁未登记载明面 + 禁声明面缺席）；② 每面须命中**同源锚**（`CO-222` ∧ `条件动作`）；"
                    "③ 正/负控齐备（域收窄 ⇒ `undeclared_surface` / 声明面缺席 ⇒ `declared_surface_absent` / 标记缺 ⇒ `marker_absent`）。**R-CO227-1**。",
     "status": "CLOSED",
     "next": "「义务时点」类记录之载明面须**域显式 + 名集等式机判**且每面命中**同源锚**；后续同类义务（条件动作 + 触发）须以**同一登记表**扩展（新增载明面未入表即停机）。"
             "注：本件**不**声称全部红线已有机判齿（173 条中仅按需逐案机判化，全量手工映射属「为证而证」）。",
     "evidence": ["实件域内命中 = 8 面，逐面同源锚（CO-222 / 条件动作）齐备 ⇒ t37 PASS（`--check` 39/39）",
                  "以 CO-224 之 7 面 md 域（F-4 形态）驱动纯判据 ⇒ `undeclared_surface`（修前形态必 FAIL，判别力实测）",
                  "漏面显式豁免 ⇒ `ok`（豁免须显式）；声明面缺席 ⇒ `declared_surface_absent`"],
     "refs": ["CO-222", "CO-223", "CO-224", "CO-225", "CO-227"], "closed_by": ["CO-227"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def upsert_note(ub: str, mark: str, note: str) -> str:
    """注解 upsert：**原位**替换本段（右界 = 下一 `；**CO-` 起点 / 末尾）—— 禁无界裁尾、禁移段（R-CO197-4）。"""
    if mark in ub:
        i = ub.index(mark); j = ub.find("；**CO-", i + len(mark))
        return ub[:i] + note + (ub[j:] if j != -1 else "")
    return ub + note


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    by = {i["finding"]: n for n, i in enumerate(reg["items"])}
    added, updated = [], []
    for it in ADD:
        if it["finding"] in by:
            if reg["items"][by[it["finding"]]] != it:
                reg["items"][by[it["finding"]]] = it; updated.append(it["finding"])
        else:
            reg["items"].append(it); added.append(it["finding"])
    note = ("；**CO-227（L2 自裁 · 义务同源机判化）**：+1 TOOL_DEFECT（`co227:F-1` U6 阵列义务之载明面枚举无机判齿 ⇒ 域收窄（CO-225 F-4 实测）；"
            "处置 = 静态齿 t37（载明面域显式 + 名集等式双向 + 每面同源锚 + 正负控）；low、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-227（L2 自裁", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
