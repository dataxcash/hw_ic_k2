#!/usr/bin/env python3
"""CO-170 — 客户可见制造输入（03_stackup 叠层图）与声明定值表的绑定（G-1）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.6）承载。
幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co170_stackup_binding.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co170:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**叠层图（03_stackup，随单提交的**制造输入**）与声明定值表无绑定、无牙齿**：`stackup_svg(spec)` **只接收 SPEC**，"
          "其「外层 1oz / 内层 0.5oz」与铜厚矩形高度为**硬编码字面量**（`0.035` / `0.0175`）。声明定值表 "
          "`jlc_prototype_parameters_v1.json` 改铜厚时叠层图**不会跟随**；且当时牙齿集（13 项）**无一项**读取该图 —— "
          "t09 只绑定 `ORDER_NOTES.md`。实际下单备注 §1/§2 与叠层图**同时**随单提交 ⇒ 制造侧可能按陈旧铜厚/叠层图施工"
          "（与 CO-163 G-1「客户可见定值不得与声明表脱钩」同族，但对象从备注扩到制造图）。",
  "disposition": "CO-170：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.6** —— 抽出记号匹配器 `_tok_match`，新增纯谓词 "
                 "`stackup_svg_binding_checks(svg_text, binding)`（叠层图须逐项含声明表记号：叠层码 / 成品厚 / 外层铜 / 内层铜）；"
                 "牙齿 `t11_stackup_svg_declared_binding` + `t11b_stackup_svg_binding_sensitivity`（声明铜厚漂移 ⇒ 必须判不通过）；"
                 "记录落 `declared_binding.stackup_svg_checks`。**叠层图正文逐字节不变**（仅新增校验）。",
  "status": "CLOSED", "next": "随单提交的**每一件**制造/工程输入都须与声明定值表（或其 SPEC 来源）绑定；新增交付图/表须同步加绑定牙齿。",
  "evidence": ["CO-170 实测（修前）：`stackup_svg(spec)` 签名不接收声明定值表 ⇒ 铜厚为字面量；11/13 牙齿均不读该图",
               "CO-170 复核（修后）：现行声明 ⇒ 4/4 命中（牙齿 15/15）；声明铜厚改 2oz ⇒ `outer_copper=False`，t11 抓住；"
               "叠层图 sha16 44370475b258848f 逐字节不变"],
  "refs": ["CO-170", "CO-163", "CO-167", "CO-158"], "closed_by": ["CO-170"]},
]
MARK = ("；**CO-170（L2 自裁 · 交付物绑定）**：G-1 叠层图（03_stackup，随单提交的制造输入）与声明定值表无绑定、无牙齿"
        "（`stackup_svg(spec)` 铜厚为硬编码字面量）⇒ CO146-PKG.6 增 `_tok_match` + `stackup_svg_binding_checks` + "
        "t11/t11b（叠层图正文逐字节不变）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
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
