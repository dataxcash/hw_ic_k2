#!/usr/bin/env python3
"""CO-198 — **代理 ↔ 语义闸关系机判化**（L2 自裁）：findings 入登记簿（幂等 upsert、注解**原位**）+ counts 复算。

E-1 = 「代理判据（键名启发式）替代语义判据」之处，其**残余** 与**承载语义性质的外部判官**只存在于 boundary 散文
（CO-193 G-4 / CO-195 I-1 如实登记之残余），**无机判绑定** ⇒ 残余不可证伪、不可回归（判官被移除/齿被改名无人发现）。
只改登记簿。CLI: python3 tools/p3_v57_co198_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co198:E-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**代理判据 ↔ 语义闸的绑定只存在于散文、无机判**：co120 的 P5「下游快照」为**键名启发式**（廉价前置代理），"
             "其真正要保证的语义性质（复现序**不动点唯一/路径无关**）由 co195 oracle 承载 —— 但该「代理 ↔ 语义闸」关系"
             "**没有任何机判**：判官工具被移除/改名、其语义齿被删、或代理自身 fail-closed 齿从 pin 表消失，**均无人发现**；"
             "且残余（更名即可逃逸）虽已如实登记，却**无声明面强制**（可被误读为判据完备）。属「声明↔实现绑定」未收尾。",
     "disposition": "CO-198（runner 升 **CO-198.1**）：新增 `PROXY_SEMANTIC_BINDING`（导出**残余**（不得宣称完备）+ "
                    "语义判官工具 + **源内声明**的语义齿名 + 代理齿所在记录）+ 纯判据 `proxy_binding_decision()`"
                    "（`tool_ok`/`src_has`/`proxy_teeth` 可注入 ⇒ 合成控）+ 静态齿 **t29**（正控 + 缺声明/残余空/"
                    "判官缺/齿名未声明/代理齿未 pin 之负控）。**只读判官源**，不读其证据件（R-CO196-1：禁验证循环）。"
                    "红线 **R-CO198-1**。",
     "status": "CLOSED", "next": "新增**代理判据**（启发式/近似/廉价前置）须同时登记 `PROXY_SEMANTIC_BINDING`：残余显式 + "
                                 "外部语义判官（源内齿名）+ 代理齿在 pin 表；否则 t29 fail-closed。",
     "evidence": ["修前（实测）：co120 键名启发式之语义承载仅见于 boundary §66/§68 散文；改写/删除 co195 齿名、或把判官工具移出，"
                  "`--check` **仍全 True**（无任何机判）",
                  "修后：`--check` **t01..t29 全 True（31 项）**；t29 负控（残余空 / 判官缺 / 齿名未声明 / 代理齿未 pin）均判 False"],
     "refs": ["CO-198", "CO-195", "CO-193", "CO-120.6"], "closed_by": ["CO-198"]},
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
    note = ("；**CO-198（L2 自裁 · 代理 ↔ 语义闸关系机判化）**：+1 TOOL_DEFECT（`co198:E-1`，low，CLOSED；"
            "runner 升 **CO-198.1** —— `PROXY_SEMANTIC_BINDING` + `proxy_binding_decision()` + 静态齿 **t29**"
            "（残余显式 + 外部语义判官源内齿名 + 代理齿在 pin 表；只读判官源、不读证据件））。")
    # 注解 upsert：**原位**替换本段（右界 = 下一 `；**CO-` 起点 / 末尾）—— 禁无界裁尾、禁移段（R-CO197-4）。
    _MARK = "；**CO-198（L2 自裁 · 代理"
    _ub = reg["meta"].get("updated_by", "")
    if _MARK in _ub:
        _i = _ub.index(_MARK)
        _j = _ub.find("；**CO-", _i + len(_MARK))
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
