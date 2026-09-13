#!/usr/bin/env python3
"""CO-196 — **验证循环（J-1）+ 扩扰动量（J-2）**（L2 自裁）：findings 入登记簿（幂等 upsert）+ counts 复算。

J-1 = CO-195 的 t28 以 oracle **证据件 verdict** 为输入 ⇒ 与 oracle 的「先结算」前置构成**验证循环**（FAIL 即锁死）。
J-2 = z60 §4 登记之「扩扰动量」触发器达成（CO-195 I-2 即自指/链式 pin 实例）。只改登记簿。
CLI: python3 tools/p3_v57_co196_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ITEM_REF = "CO-196（runner 升 **CO-196.1**；oracle 扩为多扰动量）"
ADD = [
    {"finding": "co196:J-1", "sev": "medium", "kind": "TOOL_DEFECT",
     "what": "**验证循环 ⇒ 不可恢复锁死**：CO-195 的静态齿 **t28** 以 oracle **证据件的 `verdict`** 为输入（要求 `PASS` + teeth 全 True），"
             "而 oracle 自身**前置「先结算」**（须规范序成功跑通）——但规范序的静态前置**包含 t28** ⇒ 证据件一旦为 FAIL（或损坏 / 缺失），"
             "t28 即拒 ⇒ `static_precheck_failed` ⇒ oracle 无法运行 ⇒ **永久无法自愈**（须人工改记录）。"
             "**实测复现**：某次 oracle FAIL 后，`--check` t28=False、order 报 `aborted=static_precheck_failed`、oracle 连跑 **1.7s** 即 "
             "`t00_settle_converged=False`（全部案件牙齿 False）。属「验证者以被验证证据为前置」的反模式。",
     "disposition": ITEM_REF + "：t28 改为**结构性**判据 `oracle_tool_ok(path)` —— **只判工具存在 + 可编译**，**不读证据件**；"
                    "证据件的 PASS 由 oracle 自身与 handoff 复核清单承载；负控覆盖**缺件**分支"
                    "（**语法错**分支另由 **J-4** 以内存合成控补齐 —— 初版以「不存在的路径」冒充语法错控，恒真）。"
                    "原则入红线：**`--check` 不得以被验证证据为输入**。",
     "status": "CLOSED", "next": "静态闸只判**结构性事实**（文件存在/可编译/集合关系）；证据件内容一律不作 `--check` 输入（禁验证循环）。",
     "evidence": ["实测（修前）：证据件 verdict=FAIL_… ⇒ `--check` t28=False、order `static_precheck_failed`、oracle 1.7s 即 settle failed（锁死）",
                  "实测（修后）：同一 FAIL 证据件下 `--check` 全 True、order 正常跑通 ⇒ oracle 可**自愈**（重跑得 PASS）",
                  "实测（修后）：oracle PASS（8 牙齿全 True、3 案全复原）、`--check` t01..t28 全 True（30）"],
     "refs": ["CO-196", "CO-195", "CO-193"], "closed_by": ["CO-196"]},
    {"finding": "co196:J-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**单扰动量 oracle 覆盖面不足（已登记触发达成）**：z60 §4 已裁定「co195 只扰一个扰动量 ⇒ 未覆盖的路径相关性须**扩扰动量**；"
             "触发 = 出现新的自指/链式 pin 写法」。该触发**已发生**：CO-195 的 I-2 缺陷（oracle 证据自指 + §68 误 pin 可变件）正是自指/链式 pin 实例；"
             "而单扰动量（仅登记簿 counts）**无法**在扰动实验内直接暴露该类。",
     "disposition": ITEM_REF + "：oracle 扩为**多扰动量 3 案** —— A 登记簿 `meta.counts`；B **单个 ORDER 步自持记录**注入（步内全量重写 ⇒ 应自愈）；"
                    "C **双件同时**注入（交互）。每案独立要求「收敛 rc=0 + 目标件**逐字节**复原 + 排除自身快照复原」，**任一案失败即停**"
                    "（后续案不在非规范态上开跑）；牙齿 8 项（结算/注入有效/A/B/C/判别力/自排除非空转/无残余扰动）；逐案 `finally` 无条件复原。",
     "status": "CLOSED", "next": "新增扰动量（新件/新 pin 形态）须逐案插入 CASES 并保持「先结算 + 逐案复原 + 失败即停」。",
     "evidence": ["实测（预验）：P-B（单步记录）/ P-C（双扰动）均收敛 rc=0 且逐字节复原",
                  "实测（本件）：3 案 `injection_effective`/`order_converged`/`targets_byte_restored`/`snapshot_restored` 全 True；"
                  "`sha_canon`=`59772fb78183d518`；记录 `b58a374c…`→ 现 `6b69f55ede9e7633`（**不 pin**，随规范态变化）",
                  "判别力合成控（唯一 vs 非唯一不动点）仍 True ⇒ 判据非空转"],
     "refs": ["CO-196", "CO-195", "CO-151"], "closed_by": ["CO-196"]},
    {"finding": "co196:J-3", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**证据件仍含自指字段 ⇒ 非幂等（I-2 同族、更深一层）**：CO-195 I-2 只修了**判据快照**（`_snap_excl_self`），却仍在记录里落盘 "
             "`sha_incl_self = snapshot()`（**含证据件自身**）⇒ 记录内容依赖自身字节 ⇒ **记录非幂等**（实测连跑 "
             "`3f1f9b37869f93ea` → `35549fe1c938139b`）。虽因该件**不入 pin 表**而不破收敛，但**证据不可复现**、误导复核（复核者据记录复算得另一值）。",
     "disposition": ITEM_REF + "：**移除**记录中的 `sha_incl_self`（任何含自身的 sha 一律不落盘）；自排除的**判据**在运行期算（牙齿 `t06`），"
                    "只落**布尔结论**。改后连跑两遍记录 sha 恒为 `5d8f953c12dafba0`（**幂等**）。",
     "status": "CLOSED", "next": "证据/报告类工件**不得落盘任何含自身的 sha**（自指字段一律换成布尔结论）；须逐案验证幂等。",
     "evidence": ["实测（修前）：连跑记录 sha 3f1f9b37869f93ea → 35549fe1c938139b（**非幂等**，因 `sha_incl_self` 含自身）",
                  "实测（修后）：连跑两遍记录 sha 恒为 `5d8f953c12dafba0`（幂等）；牙齿 8 项全 True"],
     "refs": ["CO-196", "CO-195", "CO-193"], "closed_by": ["CO-196"]},
    {"finding": "co196:J-4", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**t28 合成负控恒真（不可证伪）**：J-1 的处置声称「附可证伪负控（不存在 / 语法错 ⇒ False）」，实现却是 "
             "`not oracle_tool_ok(tools/__bad_oracle__.py)` —— 该文件在任何规范态下**都不存在**（无任何序内步创建它），"
             "故该控实际只**重复**了「缺件 ⇒ False」分支（FileNotFoundError），**语法错分支（SyntaxError）从未被行使** ⇒ "
             "声称的「可证伪」不成立（同族：CO-187 F-1 恒真齿 / CO-184 值绑定上下文）。",
     "disposition": "CO-196（runner 升 **CO-196.2**）：新增**纯内存**判据 `src_compiles(src, name)`（compile()，不触盘/无副作用）；"
                    "t28 改为**逐返回路径**各一控 —— 缺件 `not oracle_tool_ok(不存在的路径)`、**语法错** `not src_compiles(非法源)`、"
                    "正控 `src_compiles(合法源)`；`oracle_tool_ok` 复用 `src_compiles`。"
                    "红线 **R-CO196-4**：合成控须与被测判据的**每条返回路径**一一对应，不得以「不存在的路径」冒充某一分支。",
     "status": "CLOSED", "next": "新增/修改判据时，负控须逐分支构造（缺件 / 语法错 / 类型错 各一），并保持**零落盘副作用**（`--check` 不得写盘）。",
     "evidence": ["实测（修前）：`tools/__bad_oracle__.py` 不存在且无步创建 ⇒ 该负控恒真；`--check` t28=True 但**语法错分支不可证伪**",
                  "实测（修后）：t28 含内存合成负控（非法源 ⇒ False）与正控（合法源 ⇒ True）⇒ 两分支均可证伪；`--check` t28=True"],
     "refs": ["CO-196", "CO-195", "CO-187"], "closed_by": ["CO-196"]},
    {"finding": "co196:J-5", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**处置工具注解 upsert 被存在性守卫吞掉 ⇒ 登记簿自述与条目实况不一致**：`co196_findings_disposition.py` 以 "
             "`if CO-196 标记 not in meta.updated_by` 为守卫追加注解；一旦注解文本后续变更"
             "（本件实测：J-3 加入后注解应称「+3」，但守卫判定标记已存在 ⇒ **不重写**）⇒ `meta.updated_by` **永久停留在旧文本**"
             "（实测现存注解仍称「+2 TOOL_DEFECT（co196:J-1(medium)/J-2(low)）」而实有 3 条）。属「自述↔实况」失一致（**审计面**，非功能性）。",
     "disposition": "CO-196：改**可重入** upsert —— `trim` 掉旧 CO-196 注解段（自标记起至末尾）再 `append` 现注解，"
                    "使同一工具重复运行**幂等**且注解**恒与 `ADD` 一致**（本件落地为 `+5`）。",
     "status": "CLOSED", "next": "meta 注解类 upsert 一律**可重入**（先 trim 旧注解再 append）；不得依赖「标记存在即跳过」。",
     "evidence": ["实测（修前）：寄存器 3 条 co196 条目，而 `meta.updated_by` 注解称「+2」且无 J-3（守卫吞更新）",
                  "实测（修后）：注解恒为 `+5 TOOL_DEFECT（co196:J-1(medium)/J-2,J-3,J-4,J-5(low)…）`；工具重复运行幂等（sha 不变）"],
     "refs": ["CO-196", "CO-193"], "closed_by": ["CO-196"]},
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


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
    note = ("；**CO-196（L2 自裁 · 验证循环 + 扩扰动量）**：+5 TOOL_DEFECT（`co196:J-1`(medium)/`J-2`,`J-3`,`J-4`,`J-5`(low)，全 CLOSED；"
            "runner 升 **CO-196.2** —— t28 改结构性（禁验证循环）+ **J-4 逐分支可控**；oracle 扩为多扰动量 3 案 + 8 牙齿 + 去自指字段（幂等）；"
            "**J-5** 注解 upsert 守卫吞更新 ⇒ 改 trim+append 可重入）。")
    # CO-196（J-5）：注解 upsert 须**可重入**（trim 旧注解段 + append 现注解）——旧守卫按「标记存在即跳过」，
    # 会在注解文本变更（+2 → +3 → +5）时吞掉更新，致自述↔实况失一致（实测：3 条条目而注解仍称「+2」）。
    _MARK = "；**CO-196（L2 自裁 · 验证循环"
    _ub = reg["meta"].get("updated_by", "")
    if _MARK in _ub:
        _ub = _ub[: _ub.index(_MARK)]
    reg["meta"]["updated_by"] = _ub + note
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
