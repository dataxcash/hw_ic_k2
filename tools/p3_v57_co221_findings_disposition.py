#!/usr/bin/env python3
"""CO-221 — 登记簿入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [{"finding": "co221:F-1", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**L5 记录自声明面陈旧（已闭项以「开放项」呈现）**：`tools/p3_v57_l5_signoff.py` 生成之 SI/PI/EMC 记录**硬编码**"
          "「阻抗符合性 **NOT_DEMONSTRATED**（**开放项 CO-53**）」，而登记簿 `implementation_deviation:R3-2_asbuilt_interpair_edge` 已 **CLOSED**"
          "（域声明由 CO-147 R2 在 L2 内裁定；B.Cu/In5 已几何闭合；终判交 JLC 阻抗控制服务）⇒ 读者/板厂据记录误判尚欠工程项（方向 = fail-open）。",
  "disposition": "CO-221（L2 自裁）：口径**逐处同步**至登记簿现行表述（本工程**不自证**符合性 ⇒ 交 JLC 阻抗控制服务终判；原「开放项 CO-53」表述**已撤**）；"
                 "记录经生成器重出、boundary pin 再对齐。**R-CO221-1**。",
  "status": "CLOSED",
  "next": "判据记录之**自声明文本**须与**登记簿现行状态**同源同步（已闭项不得以「开放项」呈现）；生成器硬编码之状态词须随裁定**同 commit** 更新。",
  "evidence": ["修前：记录含「（开放项 CO-53）」而 register 该项 CLOSED（`next` = SI/JLC 阻抗控制服务终判；B.Cu/In5 已几何闭合）",
               "修后：记录内不再出现「开放项 CO-53」；`--check` 36/36；序收敛 rc=0 / 2 轮；co120 P5 `l5_bad=0`"],
  "refs": ["CO-53", "CO-147", "CO-208", "CO-217", "CO-221"], "closed_by": ["CO-221"]}]


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
    note = ("；**CO-221（L2 自裁 · 自声明面与登记簿同步）**：+1 TOOL_DEFECT（`co221:F-1` L5 记录硬编码「开放项 CO-53 / NOT_DEMONSTRATED」"
            "而 register 该项已 CLOSED ⇒ 已闭项以「开放项」呈现；处置 = 口径逐处同步、交 JLC 阻抗控制服务终判；low、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-221（L2 自裁 · 自声明面", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
