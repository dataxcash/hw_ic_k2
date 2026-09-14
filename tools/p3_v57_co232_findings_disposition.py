#!/usr/bin/env python3
"""CO-232 — L2 自裁（boundary 之内容权威性入机判）发现入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co232:F-1", "sev": "mid", "kind": "TOOL_DEFECT",
     "what": "**序内生成物（boundary）之「内容权威性」无机判齿**：R-CO224-1 要求「序内生成物之追注须写入**生成器**」，但既有齿只判「**节集**（t35）+ **pin 行**（t40）」⇒ ① 生成段内之**散文/表格数值手改**不可见"
             "（实测：`24/32` → `31/32` ⇒ t35/t40 皆 True）；② **区段内插入手工追注**不可见（实测：插入后 t35/t40 皆 True）；③ 生成器**只拥有各 § 区段**（`re.sub(MARK + …(?=\\n## |\\Z))`）⇒ **区段外前置**之手工内容在重生成后**存活**且无齿可检。",
     "disposition": "CO-232（L2 自裁）：① 生成器 `p3_v57_co146_boundary_append.py` 增 **`--dump`**（**dry-run**，只算不写，输出 `{dry_run, sha16, lines}`）；"
                    "② 入机判 runner 静态齿 **t41_boundary_is_generator_output**（**双臂**：① 实件 sha16 **== 生成器 dry-run 输出**；② **首行**须为声明标题形态 `BOUNDARY_HEAD_DECLARED`；正/负控皆备）；"
                    "③ 自声明面同步：runner report revision → **CO-203.10**；④ **R-CO232-1**。",
     "status": "CLOSED",
     "next": "凡由**生成器**产出之正典件，其实件内容须**等于生成器输出**（dry-run 比对，双臂：整件 sha16 + 首行形态）；生成段内之追注**须写入生成器**（承 R-CO224-1）。"
             "**残余（未闭，界定）**：生成器**只拥有**各 § 区段 ⇒ 区段**外**（首部除首行、他工具产出区）内容不在其权威面内；本件亦不判节内叙述之**完备性**。",
     "evidence": ["修前判别力（本会话实测）：生成段内改数值主张 `24/32→31/32` ⇒ t35/t40 **皆 True**；生成段内插入手工追注 ⇒ t35/t40 **皆 True**",
                  "修后判别力（本会话实测）：（a）**前置**追注 ⇒ t41 **False**（首行臂）；（b）§104 区段内插入追注 ⇒ t41 **False**（整件 sha16 臂）；回复 ⇒ **True**（`--check` 43/43，实件 sha16 回至 `39cb8380dd1c1fc9`）",
                  "生成器 `--dump` 幂等：同态下 dry-run sha16 == 实件 sha16（实测）；生成器不自我 pin（无自指）"],
     "refs": ["CO-208", "CO-224", "CO-230", "CO-231", "CO-232"], "closed_by": ["CO-232"]},
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
    by = {i["finding"]: n for n, i in enumerate(reg["items"])}
    added, updated = [], []
    for it in ADD:
        if it["finding"] in by:
            if reg["items"][by[it["finding"]]] != it:
                reg["items"][by[it["finding"]]] = it; updated.append(it["finding"])
        else:
            reg["items"].append(it); added.append(it["finding"])
    note = ("；**CO-232（L2 自裁 · boundary 内容权威性入机判）**：+1 TOOL_DEFECT（`co232:F-1` 生成段内手改/手工追注、区段外前置内容皆无齿可检；"
            "处置 = 生成器 `--dump` dry-run + 静态齿 t41（整件 sha16 双臂 + 首行形态）；mid、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-232（L2 自裁", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
