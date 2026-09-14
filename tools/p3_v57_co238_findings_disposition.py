#!/usr/bin/env python3
"""CO-238 — L2 自裁（非执行者对抗复评 CO-235..CO-237）发现入册（幂等、注解原位）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
WHAT = ("**t44 之工具绑定臂 = 原文子串 ⇒ 注释/散文可替代真绑定而不失 pass**："
        "CO-236 之 `_tool_ok[_rel] = (f'AF = \"{rev}\"' in _tsrc)` 为**原文子串**测试 ⇒ 真绑定（`AF = \"<rev>\"`）"
        "改为**注释**（`# AF = \"<rev>\"`）后，子串仍在 ⇒ t44 仍 True（**静默通过**）。"
        "承 **R-CO202-4**（源内声明之代理判据须 AST 字面量，注释/散文不得满足）与 **CO-215**（同源缺陷：子串即可满足）。")
DISPO = ("CO-238（非执行者对抗复评 CO-235..CO-237 · L2 自裁）：① 绑定判据改 **AST 赋值** —— 存在 `AF` 之 `Assign`/`AnnAssign`，"
         "其值为**字符串常量**且 == 声明之 rev（**注释/散文/拼接一律不满足**；`SyntaxError` ⇒ **fail-closed**）；"
         "② 合成正/负控 6 项（真绑定 / AnnAssign / 注释 / docstring / 错值 / 拼接 / 不可编译）；"
         "③ 扩 **t44** 之绑定臂（**不新增齿**，仍 46）；④ report revision → **CO-203.15**；⑤ **R-CO238-1**。")
NEXT = ("源内声明之**代理判据**须为 **AST 绑定**（注释/散文不得满足，承 R-CO202-4）。"
        "**残余（未闭，界定）**：① 绑定认 `AF` 之**字符串常量**赋值 ⇒ 非字面量构造（拼接/f-string/读取）**不**视为绑定（方向 = fail-closed）；"
        "② `AF` 之外之改名绑定形态不入本判据（须先入声明）；③ as-found 幂等仍为**结构 + 重跑一致性**代理（键名启发式/域文件名形态残余，承 CO-236/CO-237）。")
ADD = [{"finding": "co238:F-1", "sev": "mid", "kind": "TOOL_DEFECT", "what": WHAT, "disposition": DISPO,
        "status": "CLOSED", "next": NEXT,
        "evidence": ["本会话纯复算（as-found `ab9c421`）：co235 复评工具之 `AF = \"03f8d39\"` 改为注释 `# AF = \"03f8d39\"` ⇒ as-found 子串判据 = True（静默通过）；改名后再加注释亦然",
                     "修复判据（AST）判别力合成控：真绑定/AnnAssign ⇒ 认；注释/docstring/错值/拼接 ⇒ 拒；`SyntaxError` ⇒ fail-closed",
                     "as-found 域-声明等式（V6）：受 pin 之 `*_review.json` 14 件 == 声明 ∪ 豁免字面 14 件（域−声明 = ∅，≥ 下限 12）"],
        "refs": ["CO-202", "CO-215", "CO-225", "CO-236", "CO-237", "CO-238"], "closed_by": ["CO-238"]}]
NOTE = ("；**CO-238（非执行者对抗复评 CO-235..CO-237 · L2 自裁）**：+1 TOOL_DEFECT"
        "（`co238:F-1`：t44 工具绑定臂为原文子串 ⇒ 注释/散文可替代真绑定；同源缺陷承 R-CO202-4/CO-215；"
        "处置 = 绑定判据改 AST 赋值 + 正负控 + 扩 t44 绑定臂；mid、CLOSED）。")


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
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-238（非执行者对抗复评", NOTE)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
