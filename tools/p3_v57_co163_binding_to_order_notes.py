#!/usr/bin/env python3
"""CO-163 — 查漏型 L2 闸硬化（第 6 轮）：下单备注↔声明定值表绑定（G-1）/ 定值来源 pin 核验（G-2）。

性质：只改**登记簿**（L2 政策层）；判据由同 CO 的 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.4）承载。
CLI: python3 tools/p3_v57_co163_binding_to_order_notes.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co163:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**ORDER_NOTES 下单参数与声明定值表无绑定、无牙齿**：`ORDER_NOTES.md` 的「下单参数」表把 `85Ω 差分 ±10%` / `JLC08161H` / "
          "`1.6 mm` / `外层 1oz 内层 0.5oz` / `沉金 ENIG` 写为**字面量**，而同一批值在 L2 政策件 "
          "`jlc_prototype_parameters_v1.json`（监理指令 #10 定值绑定）内有声明。实测：把声明表/SPEC 的目标阻抗改成 100Ω 后，"
          "重新生成的备注**仍写 85Ω**（无任何牙齿发现）⇒ 定值表变更会静默产出**客户可见**的陈旧下单备注。",
  "disposition": "CO-163：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.4** —— 载入声明定值表并新增纯谓词 "
                 "`binding_params_in_note`/`binding_tokens`，牙齿 `t09_order_notes_binding_params`（备注须逐项含声明记号：叠层码/厚度/"
                 "外层铜/内层铜/目标阻抗/容差/表面处理）+ `t09b_binding_param_detector_sensitivity`（注入漂移值必须判不通过）；"
                 "备注正文与 gerber/drill 逐字节不变（仅新增校验）。实测：现行备注 7/7 通过；把定值表改 100Ω/2.0mm ⇒ t09 即刻 FAIL。",
  "status": "CLOSED", "next": "下单备注的参数一律以声明定值表为准；定值变更须同步备注并由 t09 把关。",
  "evidence": ["CO-163 实测（修前）：改声明表/SPEC 目标阻抗 ⇒ 备注仍写 85Ω（无牙齿）",
               "CO-163 复核（修后）：现行备注 7/7 记号命中；定值漂移（100Ω/2.0mm）⇒ t09=False"],
  "refs": ["CO-163", "CO-162", "CO-158", "CO-146"], "closed_by": ["CO-163"]},
 {"id": "G-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "**声明定值表的来源 pin 从未被核验**：`jlc_prototype_parameters_v1.json` 以 `supervisor_instruction.sha16` 声明其绑定来源"
          "（监理指令 #10 件），但无任何闸比对实际件 sha ⇒ 「定值从何而来」的声明链可静默失效（同 CO-139「豁免须 hash-pin」口径）。",
  "disposition": "CO-163：CO146-PKG.4 增牙齿 `t10_declared_binding_source_pinned`（声明表 `supervisor_instruction.sha16` 必须等于实际指令件 sha16；"
                 "路径 `.omo/supervision/ledger/instruction-10-jlc-prototype-ready.md`）+ `t10b_binding_source_pin_discriminates`"
                 "（判据须区分两件，非恒真）；记录内落 `declared_binding.source_instruction{path,available,declared_sha16}` 供审计。"
                 "实测：现行 sha16 `35aafe268ff52f89` 双方一致 ⇒ True。",
  "status": "CLOSED", "next": "定值来源变更须同步 `supervisor_instruction.sha16`；跨仓来源不可达时 t10 fail-closed 并显式记录。",
  "evidence": ["CO-163 实测：声明 sha16 35aafe268ff52f89 == 实际指令件 sha16", "t10b：sha16(定值表) != sha16(指令件) ⇒ 判据可辨"],
  "refs": ["CO-163", "CO-139", "CO-146"], "closed_by": ["CO-163"]},
]
MARK = ("；**CO-163（L2 自裁 · 查漏型闸硬化 6）**：G-1 下单备注参数与声明定值表 `jlc_prototype_parameters_v1.json` 无绑定 ⇒ "
        "CO146-PKG.4 增 `t09/t09b`（逐项记号 + 漂移灵敏度）；G-2 定值来源 pin 未核验 ⇒ `t10/t10b`（监理指令件 sha16 锚定）。")


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
