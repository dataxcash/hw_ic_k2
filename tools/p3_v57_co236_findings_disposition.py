#!/usr/bin/env python3
"""CO-236 — L2 自裁（复评/重出件 as-found 幂等入机判）发现入册（幂等、注解原位）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
WHAT = ("**R-CO193-3（复评件须幂等 / 只钉 as-found）无机判齿 ⇒ 空真；二 out-of-band 复评件内嵌现行链派生值 ⇒ 重跑即改写被 pin 之记录、序停机**："
        "`tools/p3_v57_co230_rev19_co225_co229_review.py` 与 `p3_v57_co235_rev19_co231_co234_review.py` 之复评件嵌"
        "`n_sections_now`/`declared_n`/`n_static_declared`（读**现行** runner+boundary）与 `V3_check.{rc,n_teeth}`（跑**现行** `--check`），"
        "行普查亦读**现行** boundary ⇒ **链一成长即漂移**；而该二命令**列于规范复现基线** ⇒ 重跑即**改写被 pin 之记录** ⇒ "
        "t40（pin ≠ 实件）+ t41（boundary ≠ 生成器输出）Fail ⇒ 序静态前置停机 rc=1。"
        "**实测**：co230 复评件 sha 由 `0302e5d87eb81758` 漂至 `86376b12e4cc9ac8`；co235 于失同步态重跑 ⇒ `ff30672798f5f65c`→`3abec28adc9a2d6c`。"
        "承 R-CO193-3（复评件须幂等）+ R-CO225-1（红线之形态无机判齿即空真）。")
DISPO = ("CO-236（L2 自裁）：① **co230 复评件**：节集/缺号自 **as-found（`git show fdb72a2`）重放**；**去链派生计数**"
         "（`n_sections_now`→`n_sections_as_found`；`declared_n`→布尔 `as_found_sections_subset_of_declared`；`n_static_declared`→布尔 `static_face_declared`）；"
         "控制输入改**合成声明集**（纯）；V2 **不内嵌现行 sha**（只留声明值 + 布尔）。② **co235 复评件**：**去现行 `--check` 计数**（`V3_check` 不再内嵌）、"
         "行普查自 **as-found 重放**、V2 不内嵌现行 sha。③ 新增静态齿 **t44_reissue_records_as_found_pure**（`REISSUE_RECORDS_DECLARED` **名集钉定** + "
         "as-found 绑定（记录 `as_found.rev` ∧ 工具 `AF` 声明）+ **链派生键名集** `REISSUE_CHAIN_DERIVED_KEYS` 不得出现 + 残余 `REISSUE_PURITY_RESIDUAL` **显式** + 合成正/负控）；"
         "④ report revision → **CO-203.13**（齿面 45→46）；⑤ **R-CO236-1**。**同 CO 诚实更正**：CO-235 复评件 V6「整行删除 ⇒ 皆 True（残余）」为**失同步态污染读数**；"
         "修后同式注入（pin 表内 3 列行）**t40/t41 False（检出）**；真残余 = §1..§22 手写面散文/无 sha 行删除。")
NEXT = ("凡**复评/重出件**须为**被评对象（as-found）之纯函数**：记录值自 `git show <as-found>` 重放或为链无关布尔；**禁**内嵌现行链派生量（计数/现行 sha）；**同命令重跑须逐字节相同**。"
        "**残余（未闭，界定）**：① 禁法为**键名**启发式（更名即逃逸；须先入 `REISSUE_CHAIN_DERIVED_KEYS`）；② 控制输入仍读**冻结/受 pin** 工件、并对**注入态**跑 `--check`（一致态下稳定）。")
ADD = [{"finding": "co236:F-1", "sev": "mid", "kind": "TOOL_DEFECT", "what": WHAT, "disposition": DISPO,
        "status": "CLOSED", "next": NEXT,
        "evidence": ["修前实测（本会话）：跑 `p3_v57_co230_rev19_co225_co229_review.py` ⇒ co230 复评件 sha `0302e5d87eb81758`→`86376b12e4cc9ac8`（其 P5/V7 记现行节数 100→105、静态齿 41→45）",
                     "修前实测：同处 co235 复评件因内嵌现行 `--check` 计数（45→43）与行普查（584→578 边界态）而 sha 漂移 `ff30672798f5f65c`→`3abec28adc9a2d6c`；且 t40/t41 由 True 变 False ⇒ 静态前置停机",
                     "修后：二工具**同命令重跑逐字节相同**（co230 `3b816ee2247eb7f1`×2；co235 `d6de768766e927f1`×2）；重跑 co230 重出后 `--check` 46/46 全 True",
                     "t44 正/负控：合成记录含 `n_sections_now`/`V3_check` ⇒ 命中（fail-closed）；仅 as-found 键 ⇒ 不命中"],
        "refs": ["CO-193", "CO-225", "CO-230", "CO-235", "CO-236"], "closed_by": ["CO-236"]}]
NOTE = ("；**CO-236（L2 自裁 · 复评/重出件 as-found 幂等入机判）**：+1 TOOL_DEFECT"
        "（`co236:F-1`：R-CO193-3 无机判齿 ⇒ 空真；二复评件内嵌现行链派生值 ⇒ 重跑改写被 pin 之记录、序停机；"
        "处置 = 二复评件 as-found 幂等化 + 声明集/键名集/残余显式 + 静态齿 t44；mid、CLOSED）。")


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
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-236（L2 自裁", NOTE)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
