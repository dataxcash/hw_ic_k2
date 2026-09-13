#!/usr/bin/env python3
"""CO-213 — 复评 findings 入登记簿（幂等、注解**原位**）+ counts 复算。

入册 3 项（全 `TOOL_DEFECT` / low / CLOSED）：`co213:F-1`（决策前置为代码常量）、`co213:F-3`（pin 再对齐之标签语义未显式化）、
`co213:F-4`（L5 板指纹判别齿过弱 + 消费面无机判）。
**不入册**：`co213:F-2`（z77 政策层 pin 陈旧）—— 属**叙述类**（交接件记录面），非 SPEC/工具缺陷；承 CO-135 F4 之先例
（「handoff pin 失准…属叙述类，保留在 CO-135 记录，不入本登记簿」）⇒ 仅记于 CO-213 复评件，并已于 z78 更正。
只改登记簿。CLI: python3 tools/p3_v57_co213_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co213:F-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**决策前置仍是代码常量（「声明↔实现」漂移之上一层）**：CO-211 把**成本臂**求值化，但工艺选型执行器 `recommend()` 之 B **可行性前置**取 "
             "`_proven = {\"B\": False}` 字面量（as-found 实测：源内无 `b_feasibility`、不读 `measured_placement`），判据件 `decision.precondition_note` 仅为**散文** "
             "⇒ **判据件侧任何编辑（含把 `measured` 改为 32/32）皆不能改判**；唯一可翻转者为改 Python 常量或 t04 之内存注入（正控行使的是**不可达态**）"
             "⇒ 与 R-CO211-1「规则与其前置**同处声明**、实现与声明同源」不符（前置已声明但**未被求值**）。",
     "disposition": "CO-213（L2 自裁）：① 判据件增机读 `F4_route_predicates.B.measured_placement{placed,total}` + `decision.precondition`（谓词 = `placed == total`；"
                    "字段缺失/退化 ⇒ fail-closed 视为未证）；② 执行器 **CO-206.3 → CO-206.4**：`b_feasibility()` 由该字段求值 `proven`，新增**数据驱动**齿 **t07**"
                    "（只改判据件数据即改判为 B；placed<total 或字段缺失 ⇒ 保守路 A）；③ 判据件 **v1.4 → v1.5**；④ 重出证据件 ⇒ 齿 **7/7** 全 True。**R-CO213-1**。",
     "status": "CLOSED",
     "next": "决策规则之**前置**（可行性/门限类）须与规则同处声明，并由**判据件机读字段**求值；禁以代码常量表达前置（否则「填报即改判」为伪）。",
     "evidence": ["as-found 独立复算（自板 pcbnew 普查 + as-found 工具内存重放）：pick=A、三路 cost 皆 None、`has_b_feasibility=False`、源不读 `measured_placement`；"
                  "「前置可否由判据件数据翻转」探测器 = 否",
                  "修后实测：判据件 v1.5 `measured_placement` = 24/32 ⇒ `proven=False` ⇒ pick=A（前置不满足）；将其置 32/32（**零代码改动**）⇒ pick=B；"
                  "字段缺失 ⇒ pick=A（fail-closed）；执行器齿 7/7 全 True、连跑同 sha（幂等）"],
     "refs": ["CO-206", "CO-211", "CO-213"], "closed_by": ["CO-213"]},
    {"finding": "co213:F-3", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**boundary「现行态 pin 再对齐」之标签语义未显式化 ⇒ 同排标签↔sha 可不同版**：写入器之再对齐只重写 sha、**不改同排历史版本标签** ⇒ "
             "同排标签与 sha 可指不同版（实测：§79 两行标 `CO-206.2`/`v1.3` 而 pin 已为 CO-206.3/v1.4 之内容 —— `a5cbcb6` 时 `dea2bbeb89e6fe54`/`e53fc2354e8efd59`，"
             "`86d612b` 起被再对齐为 `dd540e68fcdf4052`/`974334db1405c60b`）；全表「同文件同 sha 对多枚历史标签」之行**数十处**（负控探测器实测冲突文件数 > 0，"
             "如 runner 一行一 sha 而标签跨 CO-164..CO-203.1）；§79 并残留 CO-211 已证伪之「（已编码，填参后自动复算）」表述**且无 §84 指针** ⇒ 读者可据行内标签误判版本。",
     "disposition": "CO-213（L2 自裁）：机制**不改**（现行态对齐为**有意**设计 —— 收口件须能只读 boundary 得**现行** gate 链态；逐行改写 456 处历史标签反致伪史）⇒ "
                    "§79 补**追注**（标签 = 本节成文时口径；sha = 现行实件）并点明现行版本，§86 显式**登记该语义**。**R-CO213-2**。",
     "status": "CLOSED",
     "next": "boundary 内 sha 为**现行态对齐**；同排历史版本标签不得作为 sha 之版本判据 —— 判版本须读该节「现行版本注」或对应 CO 节。",
     "evidence": ["as-found 复算：§79 表 sha 已 = CO-206.4/v1.5 之实件，而标签仍为 `CO-206.2`/`v1.3`；`git show a5cbcb6` 证原始 sha 为 `dea2bbeb89e6fe54`/`e53fc2354e8efd59`",
                  "负控：「同文件同 sha 多标签」探测器对**合成无冲突样本不误报**、对冲突样本命中 ⇒ 判别力成立；as-found boundary 实测冲突文件数十"],
     "refs": ["CO-146", "CO-207", "CO-208", "CO-213"], "closed_by": ["CO-213"]},
    {"finding": "co213:F-4", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**CO-212 之板指纹判别齿过弱 + 消费面无机判**：其 `board_pin_discriminates` 只判「`board_sha256` ≠ 全零哨兵」，**不判别「评的是冻结源还是交付板」**"
             "（二者互换而齿不响）；且全工具集扫描：读三件 L5 记录者 13 件、含 `board_sha256` 者 3 件，**消费者（读记录 ∩ 含板指纹，除生产者）= ∅** "
             "⇒ 板变更后记录不刷新仍**只对人眼可见**（序内/各闸皆不验其板指纹）。",
     "disposition": "CO-213（L2 自裁）：① 自检改**真判别** —— DFM `baseline_sha256` 须 = 冻结源板、被评板 ≠ 冻结源、三件皆钉被评板且非退化 ⇒ 「评错板」即 rc≠0；"
                    "② 记录 **L5-DFM.8 / L5-SI.8 / L5-G7.8** 重出；③ **消费面机判**列为**有据延后**（触发 = 板变更或下次 L5 重跑），据实登记不虚增。",
     "status": "CLOSED",
     "next": "凡「verdict 记录须可追溯被评态」之闸，其**判别齿**须能与**对照态**区分（非仅「非退化」）；被评态绑定若无机判消费者，应登记延后并附触发。",
     "evidence": ["自板复算：三件 as-found 记录 `board_sha256` 均 = 现行 L4 板 `d4e81f647be7f980…`（V6），而判别齿仅比较哨兵",
                  "负控：全工具集消费面扫描 = ∅（除生产者 `p3_v57_l5_signoff.py` 与散文引用者 `p3_v57_co146_boundary_append.py`；复评工具自身已自排除）",
                  "修后实测：DFM 记录 `baseline_sha256` = `fb07d25ac426ff84…`（冻结源板）≠ 被评板 ⇒ 真判别成立；L5 rc=0（DFM PASS / SI PASS skew 0.1300 ≤ 0.15）"],
     "refs": ["CO-172", "CO-193", "CO-207", "CO-212", "CO-213"], "closed_by": ["CO-213"]},
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
    by_id = {i["finding"]: n for n, i in enumerate(reg["items"])}
    added, updated = [], []
    for it in ADD:
        if it["finding"] in by_id:
            if reg["items"][by_id[it["finding"]]] != it:
                reg["items"][by_id[it["finding"]]] = it
                updated.append(it["finding"])
        else:
            reg["items"].append(it)
            added.append(it["finding"])
    note = ("；**CO-213（L2 自裁 · 非执行者对抗复评 CO-207..CO-212 之处置）**：+3 TOOL_DEFECT（`co213:F-1` 决策前置求值化 / `co213:F-3` pin 再对齐标签语义 / "
            "`co213:F-4` L5 板指纹真判别；皆 low、CLOSED）；`co213:F-2`（z77 pin 陈旧）属叙述类**不入册**（承 CO-135 F4 先例），已于 z78 更正。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-213（L2 自裁 · 非执行者对抗复评", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG), "n_items": len(reg["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
