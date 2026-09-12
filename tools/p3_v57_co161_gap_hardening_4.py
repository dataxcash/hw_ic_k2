#!/usr/bin/env python3
"""CO-161 — 查漏型 L2 闸硬化（第 4 轮）：处置 2 项实测缺口（G-1..G-2）。

性质：只改**登记簿**（L2 政策层）；两类判据由同 CO 的闸改动承载。幂等：按 `finding` 键 upsert；counts 重算。
证据记号化（不写记录 sha）。CLI: python3 tools/p3_v57_co161_gap_hardening_4.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co161:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**K9 无「必需 DV 清单」牙齿**：台账里删掉 `DV-CO146-THERMAL` / `DV-CO146-PDN-DROP` / `DV-ENGINE-INT_PAIR_PITCH` "
          "任一项时 —— co124 K9 **0 findings**（该域机判静默消失）、co150 的 `t01` 仍 True（T10/T11 负控用**合成注入**，不依赖真 DV 存在）"
          "⇒ 一次 upsert 误删或手工编辑即可让热/压降/保守实现三域覆盖无声失效（R-CO153-1 的静态面缺口）。",
  "disposition": "CO-161：① co124 增 `REQUIRED_DV_IDS`（9 项）与 `derived_value_inventory_missing` 判据（缺项即 K9 finding）；"
                 "② `p3_v57_co153_k9_domain_coverage.py` 的 `KIND_EXPECT` **提为模块级**（必需 DV 清单的单一真值，防两处漂移）；"
                 "③ co150 增牙齿 `t03`（两域 kind 为其声明值，原先仅记录不断言）/`t04`（co124 `required_dv_ids` == co153 `KIND_EXPECT` 键集）"
                 "/`t05`（漂移可辨灵敏度）；④ co124 增负控 T19/T19b。",
  "status": "CLOSED", "next": "新增/删除派生值须同步 `co153.KIND_EXPECT`（单一真值），否则 co124 inventory 判据与 co150 t04 立即 FAIL。",
  "evidence": ["CO-161 实测（修前）：删 DV-CO146-THERMAL/PDN-DROP/ENGINE-INT_PAIR_PITCH ⇒ co124 K9 = []、co150 t01 = True",
               "CO-161 复核（修后）：三类删除均报 `derived_value_inventory_missing:*`；真台账 0 findings"],
  "closed_by": ["CO-161"]},
 {"id": "G-2", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**identity 类 fail-open**：co124 K9 的 `identity` 分支只处理「`form` 含 `span`」一种形式 —— `form` 为未识别式（如 `q = a + b`）"
          "或**缺失**时无任何判据命中、静默通过（实测两者皆 0 findings）⇒ 新增 identity 派生式若不写重算式，K9 形同无判据。",
  "disposition": "CO-161：co124 identity 分支改 **fail-closed** —— `form` 缺失 ⇒ `derived_value_identity_unparsable`（`why=form_missing`）；"
                 "`form` 未识别 ⇒ 新判据 `derived_value_identity_unhandled_form`（`why=form_not_recognized`）；"
                 "新增负控 T20/T20b，并把该 finder id 登记进 `K9_FINDER_IDS`（T18d 源码面覆盖仍成立）。",
  "status": "CLOSED", "next": "新增 identity 派生式必须同时给出可机判的重算分支（否则 FAIL），不得依赖「不识别即放过」。",
  "evidence": ["CO-161 实测（修前）：identity form=`q = a + b` / 无 form ⇒ 0 findings",
               "CO-161 复核（修后）：分别报 `derived_value_identity_unhandled_form` / `derived_value_identity_unparsable`；真台账 0 findings"],
  "closed_by": ["CO-161"]},
]
MARK = ("；**CO-161（L2 自裁 · 查漏型闸硬化 4）**：G-1 K9 必需 DV 清单牙齿（co124 `REQUIRED_DV_IDS` + inventory 判据 + T19；"
        "co153 `KIND_EXPECT` 提模块级作单一真值；co150 t03/t04/t05）⇒ 删 DV 不再静默失覆盖；"
        "G-2 identity fail-closed（未识别/缺 form 必抓 + T20；新 finder id 入 `K9_FINDER_IDS`）。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
        patch = {k: v for k, v in it.items() if k != "id"}
        patch["refs"] = ["CO-161", "CO-160", "CO-159", "CO-156", "CO-153", "CO-150"]
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
