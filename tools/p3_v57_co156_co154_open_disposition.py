#!/usr/bin/env python3
"""CO-156 — CO-154 剩余 OPEN findings（F-2 闸覆盖侧 + F-3..F-7）处置（executor · L2 自裁 · 闸硬化）。

只改**登记簿**（L2 政策层）+ 各闸/生产者的判据由同 CO 的对应工具改动承载。幂等：按 `finding` 键更新状态；counts 重算。
证据记号化（指 CO/文件，不写记录 sha）——不得内嵌下游 sha（R-CO152-1）。
CLI: python3 tools/p3_v57_co156_co154_open_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co154:{}"
ITEMS = [
 {"id": "F-2", "sev": "medium",
  "disposition": "CO-156：**闸覆盖侧机判化** —— co120 升 CO-120.3，下游快照键 = `*_sha16_after` ∪ "
                 "`register.*`/`ledger.*` 下的 `sha16*`/`items_total`/`open_total`/`n_items`，未在 SNAPSHOT_DECLARED 声明即 "
                 "FAIL_UNDECLARED_DOWNSTREAM_SNAPSHOT；牙齿增 `negative_control_register_snapshot_caught` / "
                 "`positive_control_declared_register_snapshot_passes`。复核 verdict PASS（snaps 8 / undeclared 0 / teeth 7-7）。"
                 "工件侧（CO-155）已去计数快照 ⇒ co147 记录可复现。",
  "next": "无（已闭）。新增下游快照须在 SNAPSHOT_DECLARED 明文声明。", "closed_by": ["CO-156"]},
 {"id": "F-3", "sev": "low",
  "disposition": "CO-156：**按实件对齐** —— co124 判据扩展 ⇒ 实件 revision bump 至 **CO-124.6**（与 §29 pin 表标签一致；"
                 "§26 处 `CO-124.5` 为 CO-150 时点的历史陈述，保留不删）。co147 以实件 **CO-147.1** 记入 §31 pin 表与 z30/z31 handoff。",
  "next": "无（已闭）。修订号变更须同步 bump 实件、卡与 pin 表。", "closed_by": ["CO-156"]},
 {"id": "F-4", "sev": "medium",
  "disposition": "CO-156：① `p3_v57_co134_req_impl_separation.py` 改**只 upsert 自有条目**（需求 + 其 6 个 DV），"
                 "保留他 CO 归属的 DV —— 受控 stub 复跑实测 9 DV 全保留、DV-CO146-THERMAL.kind 保留（原先整表重写会静默删除）；"
                 "② `p3_v57_co153_k9_domain_coverage.py` 扩为 K9 **全部七域** `kind` 的**规范序内具名生产者**"
                 "（`KIND_EXPECT` 覆盖九 DV / 七域并 assert），使 R-CO153-1 成立。",
  "next": "无（已闭）；域**内容**（computed/domains）仍归各派生 CO。", "closed_by": ["CO-156"]},
 {"id": "F-5", "sev": "medium",
  "disposition": "CO-156：co124 K9 增**域覆盖**判据 —— `kind` 须 ∈ 七域白名单（`KNOWN_KINDS`），且 `domain_cap` 必带非空 `domains`；"
                 "牙齿 `T14_unknown_kind_teeth` / `T14b_empty_domain_cap_teeth` / `T14c_kind_coverage_no_false_positive`。"
                 "co124 牙齿 17 → **24**，全 True。",
  "next": "无（已闭）。", "closed_by": ["CO-156"]},
 {"id": "F-6", "sev": "medium",
  "disposition": "CO-156：`declared` 判据由「钉一个现行文件」升级为**值-证据绑定** —— 须带 `evidence_ref.key_path`，"
                 "且该路径在证据件中的对象须**递归包含**该 DV 的 `computed`（`_contains`）。生产者同批："
                 "`co146_impedance_table` 增 `dv_computed_zdiff` 块、`co146_ledger_add` 以其为 `computed` 并置 `key_path`；"
                 "牙齿 `T15_declared_binding_teeth` / `T15b_declared_binding_no_false_positive`。",
  "next": "无（已闭）。新增 declared 派生值必须给 key_path 且证据件含其 computed。", "closed_by": ["CO-156"]},
 {"id": "F-7", "sev": "low",
  "disposition": "CO-156：`conservative_ge` 的 faithful 口径改为**引用权威 DV** —— 必带 `inputs.span_src`/`w_outer_src`，"
                 "且数值须与 `DV-PAIR-CROSS.computed.span_mm` 及 `DV-INTPAIR-EDGE.computed.edge_outer_binding_mm/2` 一致"
                 "（±5e-4）；`p3_v57_co153_k9_domain_coverage.py` 为其生产者（自台账权威 DV 取值回写，取代自带常数）；"
                 "牙齿 `T16_faithful_provenance_teeth` / `T16b_faithful_provenance_no_false_positive`。",
  "next": "无（已闭）。", "closed_by": ["CO-156"]},
]
MARK = ("；**CO-156（L2 自裁 · 闸硬化 · CO-154 剩余 OPEN 处置）**：F-2（co120 下游快照键通用化 = CO-120.3）/ F-3（co124→CO-124.6）/"
        "F-4（co134 只 upsert + co153 产出七域 kind）/ F-5（K9 域覆盖）/ F-6（declared 值-证据绑定）/ F-7（conservative_ge 引用权威 DV）"
        "全部 CLOSED ⇒ 登记簿 OPEN 0；co124 牙齿 24/24。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
        patch = {"kind": "TOOL_DEFECT", "severity": it["sev"], "disposition": it["disposition"],
                 "status": "CLOSED", "next": it["next"], "closed_by": it["closed_by"],
                 "refs": ["CO-154", "CO-155", "CO-156", "CO-153", "CO-152"],
                 "evidence": [f"CO-154 复评件（{it['id']}）", "CO-156 复核：co124 teeth / co120 teeth / co134 stub 复跑"]}
        if f in have:
            have[f].update(patch)
            updated.append(f)
        else:
            reg["items"].append(dict(finding=f, **patch))
            added.append(f)
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
