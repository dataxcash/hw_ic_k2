#!/usr/bin/env python3
"""CO-157 — 查漏型 L2 闸硬化（第 3 轮）：处置 4 项实测缺口（H-1..H-4）。

性质：只改**登记簿**（L2 政策层）；四类判据由同 CO 的工具改动承载。幂等：按 `finding` 键更新；counts 重算。
证据记号化（不写记录 sha）。CLI: python3 tools/p3_v57_co157_gate_hardening_3.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co157:{}"
ITEMS = [
 {"id": "H-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "co124 K9 的 `process_floor` 分支（`derived_value_evidence_bad`）与 `identity_unparsable` **无任何负控牙齿** ⇒ "
          "该两类判据虽存在，却未被「牙齿全数按预期触发」覆盖（违 CO-153 以来「每类必带负控」的自定规矩）；"
          "即新增/改动这两支时无回归保护。",
  "disposition": "CO-157：① 新增 `T17_process_floor_evidence_teeth`（合成陈旧 pin 必抓）+ `T17b_..._no_false_positive`；"
                 "② 新增**元牙齿** `T18_k9_finder_id_coverage`（对 `K9_FINDER_IDS` 十类逐类注入，断言全部被触发）、"
                 "`T18b_k9_finder_id_no_undeclared`（无未申报 finder id）、`T18c_k9_finder_battery_nonempty`。"
                 "co124 牙齿 24 → **29**，全 True；verdict PASS / findings 0。",
  "next": "新增 K9 判据时必须同时登记进 `K9_FINDER_IDS` 并保证 T18 通过。"},
 {"id": "H-2", "sev": "low", "kind": "TOOL_DEFECT",
  "what": "判据声明失实：CO-153 记录称 `declared` 判据「与 process_floor 同口径」，但 `process_floor` 实际只验 "
          "`path` 可解析 + `sha16` 现行（**不验 basis、不验 key_path**）⇒ 二者并非同口径（declared 严格更严）。",
  "disposition": "CO-157：① 在 co124 该分支就地订正注释（明示 declared **严于** process_floor）；② 本处置 + boundary §32 记录订正。"
                 "判据本身不变（不为此给 process_floor 追加无验证增益的 basis 仪式）。",
  "next": "记录内不得再出现与实现不符的口径声明。"},
 {"id": "H-3", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "co120 的 `board_superseded` 豁免「机判可证」实为**弱判**：`bool(board) and board != DELIVERED_BOARD` ⇒ 任意自由文本"
          "（如 `board=\"superseded\"`）即可成立豁免类别（实测 basis_ok=True）；该字段本应为板 sha16。",
  "disposition": "CO-157：收严为 `board` 须**匹配板 sha16 格式**（`[0-9a-f]{16}`）且 ≠ 交付板；新增负控/正控牙齿 "
                 "`negative_control_freetext_board_basis_rejected` / `positive_control_board_sha_basis_accepted`。"
                 "co120 升 **CO-120.4**：verdict PASS（basis_not_ok 0 / teeth 9-9）。",
  "next": "新增 `board_superseded` 豁免须给**可比对的板 sha16**。"},
 {"id": "H-4", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "CO-156 新增的 R-CO156-3（派生物生产者「只准 upsert、禁整表重写」）**无机判**（仅声明）——与被其处置的 F-4/F-5 同类缺陷。",
  "disposition": "CO-157：co136 增**源码级守卫** `H4_ledger_upsert_only`（写台账的工具必须先读台账；"
                 "行首 `(LED|LEDGER).write_text` 且全文无 `.read_text` 即违规）+ 负控/正控牙齿"
                 "（`H4_negative_control_write_only_caught` / `H4_positive_control_upsert_ok`）；co136 升 **CO-136.1**，verdict PASS。"
                 "⚠ 声明其**范围**：静态启发式，只保证「未读即写」不出现，不替代语义审查，故 §32 标注为**部分机判**。",
  "next": "新增台账写者必须先读台账；整表重写须在 boundary 显式豁免并说明。"},
]
MARK = ("；**CO-157（L2 自裁 · 闸硬化 3）**：H-1 K9 finder-id 覆盖元牙齿（T17/T17b + T18/T18b/T18c，牙齿 24→29）；"
        "H-2 判据声明失实订正（declared 严于 process_floor）；H-3 co120 `board_superseded` 收严为板 sha16（CO-120.4）；"
        "H-4 R-CO156-3 机判化（co136 CO-136.1 源码守卫 + 正负控）⇒ 4 项 CLOSED。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
        patch = dict(it); patch.pop("id")
        patch.update({"refs": ["CO-157", "CO-156", "CO-154", "CO-152"], "status": "CLOSED",
                      "evidence": [f"CO-157 实测缺口（{it['id']}）", "CO-157 复核：co124 teeth / co120 teeth / co136 teeth"],
                      "closed_by": ["CO-157"]})
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
