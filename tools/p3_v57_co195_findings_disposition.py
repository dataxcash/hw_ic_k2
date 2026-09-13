#!/usr/bin/env python3
"""CO-195 — **固定点唯一性 oracle**（L2 自裁）：finding 入登记簿（幂等 upsert）+ counts 复算。

来源 = z59 §6.2 指定之「co120 下游快照判据**语义化**」。只改 `L2/input_defect_register_v1.json`。
CLI: python3 tools/p3_v57_co195_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ITEM_REF = "CO-195（新增 `p3_v57_co195_fixpoint_uniqueness_oracle.py`）"
ADD = [
    {"finding": "co195:I-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**键名判据所欲保证的语义性质无独立闸**：co120 P5「下游快照」为**键名启发式**（`*_sha16_after` / `*_current_sha16` / register|ledger 面），"
             "其真正要防的失效模式（CO-151：按文档化序连跑两遍得**另一稳定不动点** ⇒ 提交 pin 不可复现）**没有任何闸直接判**。"
             "实测**值域判据不可行**：35 条记录内嵌**受控集**未来 sha，但其中绝大多数是**冻结历史件 / 自身产物**的合法 pin（如 co16/co37/co69/co95/co98 之 record pin、"
             "各步 `doc_sha16` / `stackup_svg_sha16` / `pm_eval.sha16`）⇒ 换成值域判据会大面积误报（判据不可机判为「非法」）。",
     "disposition": ITEM_REF + " —— 直接判**语义性质**：从**扰动态**启动规范序（登记簿 `meta.counts` 注入越界值 999/OPEN 7），要求 rc=0 + converged "
                    "+ `snapshot()` 复原为规范 sha + 登记簿**逐字节**复原；含 7 牙齿（**结算收敛** / 注入有效 / 收敛 rc=0 / 不动点复原 / "
                    "登记簿逐字节复原 / **判别力**合成控（唯一 vs 非唯一不动点模型） / 排除非空转）。**前置=先结算**：工作树须先收敛为不动点，"
                    "再作扰动实验（否则测的是结算而非路径无关）。工具**自我保护**：`finally` 无条件复原登记簿，绝不留在扰动态。"
                    "co120 键名判据作为**廉价前置代理**保留（不倒桩），语义保证由本 oracle 承载。",
     "status": "CLOSED", "next": "不动点唯一性由 co195 oracle 判；出现新的自指/链式 pin 形态时须**扩扰动量**（见残余）。",
     "evidence": ["实测（预验 @ 125 项基线）：`sha_canon`=f48af2c1a41de4c6 → 注入后 `sha_perturbed`=880d1ec8cbc27698 → 跑序后 `sha_after`=f48af2c1a41de4c6（**逐字节复原**、rc=0/converged）",
                  "实测（终态）：`sha_canon`==`sha_after`==3c9c54ca3ebdfc0f（扰动启动 ⇒ 复原）；oracle **幂等**（连跑记录 sha 恒 `7fb6dce88f8ab5c5`）且**不再牵动** boundary/co77（I-2 修后）",
                  "实测（可行性预验）：登记簿 counts 注入 → 跑序 → 登记簿**逐字节**复原、git tracked 树干净",
                  "判别力合成控：唯一不动点模型（恒定）判 True、非唯一模型（{0,1} 两不动点）判 False",
                  "值域判据**不可行**证据：35 条记录命中受控集未来 sha，绝大多数为冻结件/自身产物合法 pin"],
     "refs": ["CO-195", "CO-151", "CO-152", "CO-193"], "closed_by": ["CO-195"]},
    {"finding": "co195:I-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**oracle 记录自指 + §68 误 pin 可变件（实现期自捕获，G-3 同族）**：初版 `co195` 的判据快照用 `runner.snapshot()`（含**本记录自身**）"
             "⇒ 记录写回后自身字节即变，记录的 `sha_canon` **永不等于**其所在状态的实际 sha（实测 `2d23a14ffdc821cd` ≠ `6c282601e50911d5`，"
             "证据自不自洽）；且 §68 初版把该记录**列入 pin 表** ⇒ oracle 每次重跑后 `boundary_append` 改用新记录 sha 重 pin ⇒ "
             "**规范序不动点随「oracle 是否刚跑」漂移**（实测 boundary `6608cd8e`→`3e5ca535`、co77 `137b4949`→`c8ffe1ce`；即 I-1 所要防的路径相关，"
             "被本 CO 自己的 pin 设计引入）。",
     "disposition": "CO-195：① oracle 判据快照改为**排除本记录自身**（`_snap_excl_self`）+ 记录声明 `snapshot_scope` + 牙齿 "
                    "`t06_self_exclusion_nonvacuous`（排除须非空转）；② §68 **不 pin** 该记录（同 runner report 先例：随规范态变化的证据件一律不入 pin 表），"
                    "并在 §68 显式加注。牙数 8 → 6→（含 t06）。",
     "status": "CLOSED", "next": "新证据件（oracle/report 类，内容随规范态变化）一律**不入** boundary pin 表；其判据快照须排除自身。",
     "evidence": ["实测（修前）：记录 `sha_canon`=2d23a14ffdc821cd ≠ 实际 `snapshot()`=6c282601e50911d5（自指不自洽）",
                  "实测（修前）：oracle 重跑后跑序 ⇒ **两件漂移**：boundary 6608cd8e→3e5ca535、co77 137b4949→c8ffe1ce（pin 耦合）",
                  "实测（修后）：oracle PASS（teeth 6 全 True、`sha_canon`==`sha_after`==排除自身口径）；§68 不再 pin 记录 ⇒ 重跑不再牵动 boundary/co77"],
     "refs": ["CO-195", "CO-193", "CO-152"], "closed_by": ["CO-195"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    by_id = {i["finding"]: n for n, i in enumerate(reg["items"])}
    added, updated = [], []
    for it in ADD:                       # 幂等 **upsert**：新键追加、同键**整条替换**（保定义件↔登记簿同步）
        if it["finding"] in by_id:
            if reg["items"][by_id[it["finding"]]] != it:
                reg["items"][by_id[it["finding"]]] = it
                updated.append(it["finding"])
        else:
            reg["items"].append(it)
            added.append(it["finding"])
    note = ("；**CO-195（L2 自裁 · 固定点唯一性 oracle）**：+1 TOOL_DEFECT（`co195:I-1`，CLOSED；"
            "新增 `p3_v57_co195_fixpoint_uniqueness_oracle.py` —— 扰动启动 ⇒ 要求复原规范态 + 6 牙齿 + 判别力合成控；"
            "I-2 自捕获：oracle 判据快照排除自身 + §68 不 pin 证据件）。")
    if "CO-195（L2 自裁 · 固定点唯一性" not in reg["meta"].get("updated_by", ""):
        reg["meta"]["updated_by"] = reg["meta"].get("updated_by", "") + note
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
