#!/usr/bin/env python3
"""CO-201 — **出口语义（白名单错误输出）+ 豁免边界合成控**（L2 自裁）：findings 入登记簿（幂等、注解**原位**）+ counts 复算。

G-1 = 白名单「崩溃」检测为 **stderr 文本子串代理**（只认 CPython `Traceback (most recent call last)`）⇒ 非表头形态的错误出口
（`sys.exit("msg")`、库级 SystemExit、解释器外错误）只要 rc 恰为声明值且记录已先落盘即可**冒充预期判决出口**。
G-2 = 写影子**豁免前缀**判据的**段边界**分支（`rel == pre` / `startswith(pre + "/")` 之别）**无合成负控** ⇒ 回归为裸
`startswith(pre)`（兄弟目录/同前缀文件名被误豁免）时**不可证伪**。
只改登记簿。CLI: python3 tools/p3_v57_co201_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co201:G-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**白名单出口语义靠文本子串代理**：`allowlist_decision()` 对白名单步的「崩溃」判据仅查 stderr 是否含 CPython 表头 "
             "`Traceback (most recent call last)`，**其余 stderr 内容一概不看** ⇒ 非表头形态的错误出口"
             "（`sys.exit(\"msg\")`、库抛 SystemExit、解释器外/SIGABRT 之类）在与声明 rc 相同（=1）、且记录已先落盘、"
             "verdict 与牙齿均相符时**冒充「预期判决出口」**（rc 类语义已在 CO-199 收紧，但**出口的错误性**仍无判据）。"
             "即：R-CO199-1「逐项声明语义出口」只约束了 rc **值**，未约束该出口**是否伴生错误**。",
     "disposition": "CO-201（runner 升 **CO-201.1**）：白名单**预期非零出口**须**stderr 全空**（设计出口不打印错误）⇒ 新增停机类 "
                    "`expected_step_error_output`（置于 `expected_step_crashed` 之后，保留更具体的 Traceback 分类）；"
                    "静态齿 **t31**（正控空/纯空白 stderr ⇒ 放行；负控普通错误输出 ⇒ error_output；负控 Traceback ⇒ crashed）。"
                    "红线 **R-CO201-1**。**零基线冲击**：实测 `co146_jlc_dfm_gate` stderr = **0 字节**。",
     "status": "CLOSED", "next": "「预期出口」须同时绑定 **rc 值** 与 **无错误输出**；新增白名单步须实测其 stderr 为空并给出证据。",
     "evidence": ["修前（实测）：`allowlist_decision('co146_jlc_dfm_gate', 1, 'Error: boom', 'FAIL', True, True)` 返回 "
                  "`expected_nonzero`（被当预期 FAIL 放行）",
                  "修后：同一调用 ⇒ `expected_step_error_output`；含 Traceback 者 ⇒ `expected_step_crashed`；空/纯空白 ⇒ `expected_nonzero`",
                  "零基线冲击实测：`p3_v57_co146_jlc_dfm_gate.py` stderr = 0 字节、stdout = 628 字节、rc = 1；规范序收敛 rc=0"],
     "refs": ["CO-201", "CO-199", "CO-165"], "closed_by": ["CO-201"]},
    {"finding": "co201:G-2", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**豁免前缀的段边界分支无合成控**：`shadow_exempt()` 以 `rel == pre or rel.startswith(pre + \"/\")` 判豁免（**实现正确**），"
             "但 t23 的合成控只行使了**接受**分支（子路径/等值），**未行使拒绝分支**（同前缀兄弟路径）⇒ 一旦回归为裸 "
             "`rel.startswith(pre)`，`…/06_rulingsX/`、`…/05_layer_sequence.txtX` 之类**未声明路径将被静默豁免**，"
             "而 `--check` **仍全 True**（判据该分支不可证伪）。属「合成控须逐分支覆盖」（R-CO197-1）之欠账。",
     "disposition": "CO-201：t23 补段边界合成控 —— 正控 `…/06_rulings/sub/a.md`（子路径须豁免）；负控 "
                    "`…/06_rulingsX/a.md` 与 `…/05_layer_sequence.txtX`（**同前缀兄弟路径不得豁免**）。",
     "status": "CLOSED", "next": "字符串前缀/集合归属类判据须对**两种拒绝形态**（等长不同名 / 长前缀）各给负控；违者 fail-closed。",
     "evidence": ["修前：t23 无兄弟路径负控 ⇒ 该分支不受机判（回归不可证伪）",
                  "修后：t23 含 1 正控 + 2 负控；实现保持 `rel == pre or startswith(pre + \"/\")`，`--check` 全 True"],
     "refs": ["CO-201", "CO-189", "CO-197"], "closed_by": ["CO-201"]},
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
    note = ("；**CO-201（L2 自裁 · 出口语义 + 豁免边界）**：+2 TOOL_DEFECT（`co201:G-1`/`G-2`，low，CLOSED；runner 升 **CO-201.1** —— "
            "白名单预期非零出口须 **stderr 全空**（`expected_step_error_output`）+ 静态齿 **t31**；豁免前缀**段边界**补正/负控）。")
    _MARK = "；**CO-201（L2 自裁 · 出口语义"
    _ub = reg["meta"].get("updated_by", "")
    if _MARK in _ub:                                   # 原位替换本段（R-CO197-4）
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
