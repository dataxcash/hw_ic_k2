#!/usr/bin/env python3
"""CO-235 — L2 自裁（pin 行值之判据面/realign 面同域化）发现入册（幂等、注解原位）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
WHAT = ("**pin 行「值面」之判据面与 realign 面各自由格式隐式给定 ⇒ `**`sha`**` 变体静默逃逸**："
        "① 判据面 = t40 之域（`_PIN_ROW_RE`，**仅 2 列**）⇒ §2 之 3 列 pin 行（14 行）**不在域内**；"
        "② realign 面 = 生成器 `CITE`（亦**按格式**匹配）⇒ 粗体 `**`sha`**` **不被 realign**。"
        "两处皆不在 ⇒ 该值**陈旧/伪造静默通过**。实测（改 §2 粗体行值 `05009687a3f01583`→`deadbeefdeadbeef`）：**t35/t40/t41 皆 True**；"
        "同法改一枚 2 列 pin 行（正控）⇒ t40 **False**。同族：普通 3 列行值伪造 ⇒ t41 False（realign 差分可见）；**整行删除**（§1..§22 不在生成器权威面）⇒ 三齿皆 True。"
        "承 R-CO230-1（判据面之域不得由被判对象自述给出）/ R-CO231-1（pin 须可核）/ R-CO152-1。")
DISPO = ("CO-235（L2 自裁，复评 CO-231..CO-234 之同会话处置）：① 生成器 `CITE` 之 sha 组前允许 `(?:\\*\\*)?` ⇒ realign 面覆盖粗体（值**自愈**，"
         "并由 t41 整件比对覆盖）；② runner **显式声明** `PIN_ROW_FORMATS_DECLARED`（`pin2` = 2 列现状；`pin3` = 3 列 / sha 为第 3 单元格，可粗体、可带尾注），"
         "`boundary_pin_rows()` **遍历声明格式** ⇒ **t40 之值核覆盖 §2 全 14 行**（实测 14/14 值 == 实件）；③ 新增静态齿 **t43_pin_row_format_covered**："
         "boundary 内**一切含 backticked 16-hex 之表行**须匹配**恰一**声明格式，否则须入 `PIN_ROW_FORMAT_EXEMPT`（**名集等式** + 理由 + **同源锚**（补偿牙齿须实存））"
         "⇒ 未声明之**新形态 fail-closed**；④ **口径同步**：§3 之 G7/L5 行为 L5-SI.6/L5-DFM.6 **历史快照**（其值全树无对应件）⇒ 显式标注 + 指向 §104 pin 面之现行 L5"
         "（L5-SI.11/L5-DFM.8/L5-FAB.2/L5-G7.11）—— 承 R-CO152-1（现行 sha 单一承载）/ R-CO208-1（口径逐处同步）；⑤ runner report revision → **CO-203.12**；⑥ **R-CO235-1**。")
NEXT = ("凡以「行的形态」界定判定域者，须**显式声明格式名集** + **覆盖面臂**（域外不得有 carrying-同语义之对象）；且**值面之 realign 面须与判据面同域**（不得一方覆盖、另一方漏过 ⇒ 漏过即静默陈旧）。"
        "**残余（未闭，界定）**：① **行集完备性**仍不判（删一行无人知 —— CO-231 已声明；本件只拦**新形态**）；② §3 之 `gate3` 族值由**锚点齿**承载（G4 == t39；G5/G6 == t40 pin 面；G7 = 历史快照），本件不重核其字面；"
        "③ 生成器仍只拥有各 § 区段（§1..§22 为手工面；承 CO-232 残余）；④ CO-235 自身须下一轮复评（禁自评）。")
ADD = [{"finding": "co235:F-1", "sev": "mid", "kind": "TOOL_DEFECT", "what": WHAT, "disposition": DISPO,
        "status": "CLOSED", "next": NEXT,
        "evidence": ["修前（as-found 态实测，字节复原）：改 §2 粗体 pin 行值 `**`05009687a3f01583`**`→`deadbeefdeadbeef` ⇒ t35/t40/t41 **皆 True**（不可见）",
                     "修前正控：同法改一枚 2 列 pin 行值 ⇒ t40 **False**（可见 —— 证明注入有效、差异由**格式域**造成）",
                     "同族实测：普通 3 列行值伪造 ⇒ t41 **False**；**整行删除**（§1..§22）⇒ t35/t40/t41 **皆 True**",
                     "修后：`--check` 44→**45/45** 全 True（t43 正/负控齐备）；§2 之 14 行值经 t40 核（14/14 == 实件）；同一 E1 注入 ⇒ t41 **False**（realign 差分）"],
        "refs": ["CO-230", "CO-231", "CO-232", "CO-234", "CO-235"], "closed_by": ["CO-235"]}]
NOTE = ("；**CO-235（非执行者对抗复评 CO-231..CO-234 + 同会话处置 · pin 行值之判据面/realign 面同域化）**：+1 TOOL_DEFECT"
        "（`co235:F-1` 判据面与 realign 面**各自**由格式隐式给定 ⇒ `**`sha`**` 变体值陈旧/伪造静默通过；处置 = 生成器 `CITE` 扩粗体 + 声明格式集 + 静态齿 t43（覆盖面）+ 口径同步；mid、CLOSED）。")


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
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-235（非执行者对抗复评", NOTE)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
