#!/usr/bin/env python3
"""CO-200 — **不动点 oracle 扩扰动量（受控 md 卡片产物）**（L2 自裁）：findings 入登记簿（幂等 upsert、注解**原位**）+ counts 复算。

G-1 = 受控集自 CO-186 起 pin **md 卡片产物**（步内产出、入 pin、受控），而 oracle 的三个扰动案（登记簿 counts /
单步自持 json 记录 / 双件交互）**只扰 json 记录** ⇒ **md 产物面从未被扰动实验行使**：「该步是否**真正全量重写**其 md 产物」
（追加式/增量式写即残留注入行）无机判，与 R-CO186-1「受控 sha 覆盖全部产物」之目的存在**覆盖面缺口**。
只改登记簿。CLI: python3 tools/p3_v57_co200_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co200:G-1", "sev": "low", "kind": "TOOL_DEFECT",
     "what": "**扰动实验覆盖面缺 md 卡片产物**：受控集自 CO-186 起把各步 **md 卡片产物**入 pin（`ORDER_MD_PRODUCTS`，t20 判），"
             "而 `co195` oracle 的三个扰动案（A 登记簿 `meta.counts` / B 单步自持 json 记录 / C 双件交互）**只扰 json 记录** ⇒ "
             "「步是否**真正全量重写**其 md 产物」这一性质**从未被扰动实验行使**（追加式/增量式写会在扰动态残留注入行而无人测）。"
             "即 R-CO186-1「受控 sha 覆盖**全部**产物」在**语义层**存在覆盖面缺口（结构上已 pin，语义上未扰）。",
     "disposition": "CO-200（oracle 升 **CO-200**）：`CASES` 扩第 4 案 **D_md_card_product**（目标 = `co146_impedance_table` 的 md 卡片产物；"
                    "注入**内容行**），与其余案同判「收敛 rc=0 + 目标件**逐字节**复原 + 排除自身快照复原」，**任一案失败即停**；"
                    "牙齿 8 → **9**（`t08_D_md_restored`）；`CASES` 逐案显式 `tooth` 名（新增案不挤占既有齿名，保 CO-198 绑定名稳定）。"
                    "红线 **R-CO200-1**：受控集新增**产物类别**时须同步扩 oracle 扰动量（否则该面只受**结构** pin、不受**语义**扰动）。",
     "status": "CLOSED", "next": "受控集每新增一类产物（md / 报告 / 图 / 二进制），`CASES` 须增对应扰动量；案数须 ≥ 产物类别数。",
     "evidence": ["实测（新增后）：4 案 `injection_effective` / `order_converged` / `targets_byte_restored` / `snapshot_restored` **全 True**；"
                  "牙齿 **9 项全 True**、verdict **PASS**、rc=0；D 案证实该 md 产物为**全量重写**（注入行消失、逐字节复原）",
                  "判别力与自排除齿（t05/t06）与 `no_residual_perturbation`（t07，现覆盖 4 案全部目标件）保持 True"],
     "refs": ["CO-200", "CO-196", "CO-195", "CO-186"], "closed_by": ["CO-200"]},
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
    note = ("；**CO-200（L2 自裁 · oracle 扩扰动量：受控 md 卡片产物）**：+1 TOOL_DEFECT（`co200:G-1`，low，CLOSED；"
            "oracle 升 **CO-200** —— `CASES` + 第 4 案 `D_md_card_product` + 牙齿 8→9 + 逐案显式齿名）。")
    _MARK = "；**CO-200（L2 自裁 · oracle"
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
