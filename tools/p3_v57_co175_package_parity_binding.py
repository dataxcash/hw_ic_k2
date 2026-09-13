#!/usr/bin/env python3
"""CO-175 — 交付包 parity/派生绑定补强（⇒ 登记簿）。

性质：只改**登记簿**（L2 政策层）；判据由 `p3_v57_co146_jlc_fab_package.py`（CO146-PKG.9，
t15/t15b 副本 parity + t16/t16b 派生一致性）承载。幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co175_package_parity_binding.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"

ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "交付包内 `04_impedance/impedance_table.{json,md}` 是随单件（板厂**据此控阻抗**；ORDER_NOTES §1/§2 明列为随单附件），"
          "但由 `shutil.copy` 从 STEP2 来源拷贝且**无 parity 牙齿** —— 对照 `06_rulings/*` 有 t07/t07b，此副本若与来源脱钩"
          "（包被独立提交/手改）则**不可见**（CO-159 F-8「来源已修订而包内副本陈旧」同类）。",
  "disposition": "CO-175：`p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.9** —— 新增纯谓词 `copy_parity()` + 牙齿 "
                 "**t15**（两副本与来源**逐字节一致**，缺件 fail-closed）/ **t15b**（判据灵敏度：同 True、异 False、缺件 False）；"
                 "包记录增 `declared_refs.impedance_copy_parity`。",
  "status": "CLOSED", "next": "凡**副本类**随单件（非仅 06_rulings）亦须与来源逐字节绑定的牙齿。",
  "evidence": ["CO-175 实测：改前 `04_impedance/*` 无任何牙齿覆盖（牙齿名集仅含 t07 系列 == 06_rulings）",
               "CO-175 修后：t15/t15b 全 True；fab 牙齿 25→29"],
  "refs": ["CO-175", "CO-159", "CO-146"], "closed_by": ["CO-175"]},
 {"id": "G-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "交付包内 `05_layer_sequence.txt` 由冻结 SPEC（`stackup` + `impedance.per_layer`）**派生**，"
          "但**无派生一致性牙齿** ⇒ 包被独立提交/手改时与 SPEC 脱钩不可见；且该件未在 ORDER_NOTES §1/§2 声明为随单件"
          "（**在包内但未声明**，取用口径不明）。",
  "disposition": "CO-175：同升 **CO146-PKG.9** —— 牙齿 **t16**（包内文本 == `layer_sequence(spec)` **重算**结果）/ "
                 "**t16b**（灵敏度：扰动 SPEC stackup 角色 ⇒ 重算必不同）；包记录增 `declared_refs.layer_sequence_sha16`。"
                 "**如实说明**：该件**不**声明为随单件（ORDER_NOTES 未列），仅作包内层序摘要 ⇒ 本项只做**包内自洽**绑定，"
                 "不改变下单提交口径（ORDER_NOTES 文本**逐字节不变**）。",
  "status": "CLOSED", "next": "若板厂要求随单提交层序摘要 ⇒ 须在 ORDER_NOTES 声明并纳入随单件口径（届时作 L1/L2 判定）。",
  "evidence": ["CO-175 实测：改前 `05_layer_sequence.txt` 无任何牙齿覆盖",
               "CO-175 修后：t16/t16b 全 True（重算一致 + 扰动必不同）"],
  "refs": ["CO-175", "CO-146"], "closed_by": ["CO-175"]},
]

MARK = ("；**CO-175（L2 自裁 · 交付物绑定补强）**：交付包 parity 覆盖缺口关闭 —— `04_impedance/*`（**随单件**，板厂控阻抗依据）"
        "此前**无 parity 牙齿**（对照 06_rulings 有 t07/t07b）⇒ `p3_v57_co146_jlc_fab_package.py` 升 **CO146-PKG.9**，"
        "新增 `copy_parity()` + 牙齿 t15/t15b（副本↔来源逐字节）/ t16/t16b（05_layer_sequence ↔ SPEC 重算）；"
        "ORDER_NOTES **逐字节不变**（co175:G-1/G-2，后者含「在包内但未声明」如实说明）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = "co175:" + it["id"]
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
