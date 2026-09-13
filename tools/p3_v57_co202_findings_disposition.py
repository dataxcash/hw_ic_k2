#!/usr/bin/env python3
"""CO-202 — **非执行者对抗复评 CO-196..CO-201 之处置**（L2 自裁）：findings 入登记簿（幂等、注解**原位**）+ counts 复算。

L-1（CO-196）t28 谓词级控欠覆盖；L-2（CO-199）运行期新停机类 `expected_step_rc_undeclared` 无控；
L-3（CO-198）「源内声明」为原文子串代理；L-4（CO-200）oracle 扰动量类别覆盖不足（.svg/图 无为案）。
只改登记簿。CLI: python3 tools/p3_v57_co202_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co202:L-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**t28 谓词级合成控欠覆盖**：R-CO196-4 明列「缺件 / 语法错 / **类型错** 各一」，而 t28 对被测谓词 `oracle_tool_ok` "
             "仅行使**缺件**与正控；「语法错」控挂在**共享子程序** `src_compiles` 上（不证明谓词之编译失败**传播**），"
             "「类型错」分支**无任何控**（实测 as-found `8a4cc3c`：谓词级 compile/type 控各 False，而 "
             "`oracle_tool_ok(<存在但不可编译件>)` 确返 False ⇒ 实现正确、判据不可证伪）。",
     "disposition": "CO-202（runner 升 **CO-202.1**）：t28 补**谓词自身**之逐返回路径控 —— 「存在但不可编译」"
                    "（`_NONCOMPILE_PROBE` = boundary md：存在 ⇔ 非空转、且 `src_compiles` 为 False ⇔ 真不可编译、"
                    "`oracle_tool_ok` 为 False ⇔ 传播成立）与「类型错」（`oracle_tool_ok(None) is False`）。红线 **R-CO202-1**。",
     "status": "CLOSED", "next": "谓词级负控须覆盖**谓词自身**每条返回路径（含「存在但不可编译」「类型错」），不得仅控其共享子程序。",
     "evidence": ["修前（AST 复算，零落盘）：as-found `8a4cc3c` t28 之谓词级「存在但不可编译」控 False、「类型错」控 False",
                  "修后：t28 含 `_NONCOMPILE_PROBE.exists()` + `not src_compiles(...)` + `oracle_tool_ok(_NONCOMPILE_PROBE) is False` "
                  "+ `oracle_tool_ok(None) is False`；`--check` t28 = True（34 项全 True）"],
     "refs": ["CO-202", "CO-196", "CO-187", "CO-197"], "closed_by": ["CO-202"]},
    {"finding": "co202:L-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**运行期新停机类无合成控**：CO-199 新增之 `expected_step_rc_undeclared`（`allowlist_decision` 之 return 分支）在 runner "
             "源内**仅出现 1 次**（即其自身 return）⇒ 无任何合成控行使该分支（声明面之 `rc_not_declared` 控不覆盖运行期分支）"
             "⇒ 违 R-CO196-4「合成控须与被测判据的每条返回路径一一对应」，该分支**不可证伪**（回归时被 `expected_step_rc_mismatch` "
             "静默吸收，分类永不生效）。",
     "disposition": "CO-202（runner 升 **CO-202.1**）：`allowlist_decision(..., decl=)` 增**可注入声明面**（`decl=None` 时语义不变）⇒ "
                    "运行期每分支可逐一行使；t30 以「声明缺 `rc`」「声明 `rc=0`」两形态行使 `expected_step_rc_undeclared`。红线 **R-CO202-2**。",
     "status": "CLOSED", "next": "运行期新停机类（新 return 分支）须合成控覆盖（声明面可注入）；不得以「当前不可达」免控。",
     "evidence": ["修前（AST 复算，零落盘）：as-found `8a4cc3c` 源内 `expected_step_rc_undeclared` 计数 = 1（仅其 return）⇒ 无控",
                  "修后：t30 以 `{k:v for k,v in _d199.items() if k!='rc'}` 与 `{**_d199,'rc':0}` 两形态 ⇒ `expected_step_rc_undeclared`；"
                  "`--check` t30 = True"],
     "refs": ["CO-202", "CO-199", "CO-196", "CO-197"], "closed_by": ["CO-202"]},
    {"finding": "co202:L-3", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**「源内声明」以原文子串代理**：`proxy_binding_decision` 默认 `has = lambda name: name in src`（**裸子串**）⇒ "
             "判官齿名仅出现于**注释/散文**亦可满足 R-CO198-1「判官**源内声明的齿名**」（实测 `src_has` 注入 "
             "`\"# t00_settle_converged  （仅注释，非声明）\"` ⇒ 返回 `ok`）⇒ 该「机判」判据本身是**文本代理**、非语义"
             "（同文件已备 AST 字面量抽取器 `_source_strings` 却未用）。",
     "disposition": "CO-202（runner 升 **CO-202.1**）：`proxy_binding_decision` 默认「源内声明」改 **AST 字面量集**"
                    "（`set(_source_strings(src))` ⇒ 注释/散文不满足，字典键/值字面量满足）；t29 补**判别力控**"
                    "（注释不满足 / 字面量满足）。红线 **R-CO202-4**。",
     "status": "CLOSED", "next": "「源内声明的名称」类判据须以 **AST 字面量集**判（注释/散文不得满足）；原文子串 `in src` 禁作声明性判据。",
     "evidence": ["修前（内存复算，零落盘）：as-found `8a4cc3c` 默认谓词为 `name in src`；`src_has` 注入注释串 ⇒ `ok`（注释即通过）",
                  "修后：t29 判别力控 —— `_source_strings('# t00_settle_converged')` 不含该名、`_source_strings(\"t = {'t00_settle_converged': False}\")` 含该名；"
                  "现行 `PROXY_SEMANTIC_BINDING` 全条 `ok`；`--check` t29 = True"],
     "refs": ["CO-202", "CO-198", "CO-195", "CO-196"], "closed_by": ["CO-202"]},
    {"finding": "co202:L-4", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**oracle 扰动量类别覆盖不足**：R-CO200-1 宣示「覆盖面 = 类别数（md / 报告 / **图** / 二进制）」，而受控集含 "
             "`.json` / `.md` / **`.svg`（图）** 三类、oracle `CASES` 仅扰 `.json` / `.md` 两类 ⇒ `.svg` 产物"
             "（`JLC08161H_stackup.svg`，CO-174 入 pin）只受**结构** pin（t08/t20），**从未**被「扰动启动 ⇒ 逐字节复原」语义实验行使"
             "（其全量重写性未被证）。且本谱系交接件 §4 之延后触发条件『受控集新增**另一类**产物（报告/图/二进制）』实已于 CO-174 达成 ⇒ 触发已发生。",
     "disposition": "CO-202（oracle 升 **CO-202** + runner 升 **CO-202.1**）：oracle `CASES` 扩第 5 案 `E_svg_product`（目标 = "
                    "`03_stackup/JLC08161H_stackup.svg`，注入内容行；同一「收敛 rc=0 + 逐字节复原 + 排除自身快照」判），牙齿 9 → **10**；"
                    "runner 新增静态齿 **t32**（受控集产物**类别数** ⊆ oracle 扰动量类别数）。红线 **R-CO202-3**。",
     "status": "CLOSED", "next": "受控集**每新增一产物类别**（md / 报告 / 图 / 二进制）须同步增 oracle 扰动量；t32 机判「类别覆盖」。",
     "evidence": ["修前（内存复算，零落盘）：as-found `3734a2f` oracle CASES 类别 {.json,.md} vs 受控集类别 {.json,.md,.svg} ⇒ `.svg` 无案",
                  "修后：oracle 5 案（A/B/C/D/E）`injection_effective`/`order_converged`/`targets_byte_restored`/`snapshot_restored` 全 True、"
                  "10 牙齿全 True、verdict PASS；runner `--check` t32 = True"],
     "refs": ["CO-202", "CO-200", "CO-174", "CO-195"], "closed_by": ["CO-202"]},
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
    note = ("；**CO-202（非执行者对抗复评 CO-196..CO-201）**：+4 TOOL_DEFECT（`co202:L-1`/`L-2`/`L-3`/`L-4`，low，CLOSED；"
            "runner 升 **CO-202.1** —— t28 谓词级逐返回路径控（存在但不可编译 / 类型错）+ `allowlist_decision(decl=)` + "
            "t30 `expected_step_rc_undeclared` 控 + proxy「源内声明」改 AST 字面量集 + 静态齿 **t32**（类别覆盖）；"
            "oracle 升 **CO-202** —— `CASES` 第 5 案 `E_svg_product`（图/.svg 类别）+ 牙齿 9→10）。")
    # 注解 upsert：**原位**替换本段（右界 = 下一 `；**CO-` 起点 / 末尾）—— 禁无界裁尾、禁移段（R-CO197-4）。
    _MARK = "；**CO-202（非执行者对抗复评"
    _ub = reg["meta"].get("updated_by", "")
    if _MARK in _ub:
        _i = _ub.index(_MARK); _j = _ub.find("；**CO-", _i + len(_MARK))
        _ub = _ub[:_i] + note + (_ub[_j:] if _j != -1 else "")
    else:
        _ub = _ub + note
    reg["meta"]["updated_by"] = _ub
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"],
                      "register_sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
