#!/usr/bin/env python3
"""CO-177 — 能力表**值**的原文抽取绑定（CO-176 G-2 残余）（⇒ 登记簿）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co146_jlc_dfm_gate.py`（CO146-JLC-DFM.4，t06/t07）
承载。幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co177_capability_value_binding.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"

ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "CO-176 只把能力表**引证（anchor）**绑到抓取件，能力表的**数值/文本主张**（`value`/`min`/`max`/`allowed`…）"
          "仍是**手录** ⇒ 手录值与抓取件脱钩（如把 0.09 误录为 0.10）时 anchor 仍命中、**不可检出**"
          "（DFM 判定随单进包，其限值依据仍不完全可核验）。",
  "disposition": "CO-177：`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.4** —— 新增 `CAPABILITY_VALUE_BIND`"
                 "（每条 `[(正则, [期望值…])]` 或字面量；24/24 覆盖、**29 个捕获组**）+ 纯函数 `_val_eq()` / "
                 "`capability_value_bind_checks()` + 牙齿 **t06**（覆盖/非空/字面量存在/正则匹配/捕获组数一致且逐值相等/"
                 "捕获组总数下限 25）/ **t07**（灵敏度：改期望值即判不通过）；capability 记录升 **CO146-CAP.2** + "
                 "`value_bind` 块；卡/打印补 T6/T7。",
  "status": "CLOSED", "next": "**残余如实登记**：绑定为**人工编写**的正则（非自动生成的抽取器）⇒ 能力页改版后须人工复核绑定；"
                              "「值」的语义（如 preferred/档位选择）仍由人判。",
  "evidence": ["CO-176 残余（记录在案）：只绑 anchor、值仍手录",
               "CO-177 原型实测（去标签+空白归一后）：24/24 覆盖、29 捕获组、0 处不匹配；修后 t06/t07 全 True"],
  "refs": ["CO-177", "CO-176", "CO-146"], "closed_by": ["CO-177"]},
]

MARK = ("；**CO-177（L2 自裁 · 引证可核验性续）**：CO-176 G-2 残余关闭 —— 能力表**值**亦须由抓取件原文抽取核验 ⇒ "
        "`p3_v57_co146_jlc_dfm_gate.py` 升 **CO146-JLC-DFM.4**（`CAPABILITY_VALUE_BIND` 24/24 / 29 捕获组 + 纯函数 "
        "`capability_value_bind_checks` + 牙齿 t06/t07）；记录升 **CO146-CAP.2**（co177:G-1）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = "co177:" + it["id"]
        patch = {k: v for k, v in it.items() if k != "id"}
        if f in have:
            have[f].update(patch); updated.append(f)
        else:
            reg["items"].append(dict(finding=f, **patch)); added.append(f)
    if MARK not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    print(f"register: +{len(added)} / upd {len(updated)} | counts={reg['meta']['counts']} | sha16 {s16(REG)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
