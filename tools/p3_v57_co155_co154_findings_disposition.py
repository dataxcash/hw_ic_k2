#!/usr/bin/env python3
"""CO-155 — CO-154 复评 findings 处置（executor · L2 自裁）：登记 7 项并处置 F-1（+F-2 工件侧）。

性质：只改**登记簿**（L2 政策层）+ 清零缺失。幂等：按 `finding` 键存在即更新状态；counts 由 items 重算。
证据一律记号化（指 CO/文件，不写记录 sha）——登记簿内不得嵌下游 sha（R-CO152-1）。
CLI: python3 tools/p3_v57_co155_co154_findings_disposition.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co154:{}"
ITEMS = [
 {"id": "F-1", "status": "CLOSED", "sev": "medium",
  "what": "CO-152 删 CO-150 记录的 `register.open_total` 却未同步 co150 工具第 81/84 行消费者 ⇒ 规范序内必抛 KeyError、card 不刷新。",
  "disposition": "CO-155：删除该两处消费者（卡改静态注记、print 去 open_total）⇒ co150 在规范序内 rc=0；复跑序收敛。",
  "next": "无（已闭合）。", "closed_by": ["CO-155"]},
 {"id": "F-2", "status": "OPEN", "sev": "medium",
  "what": "CO-152 仅清 `*_sha16_after` 下游 sha 快照，未覆盖同族**下游计数/版本快照**：co147 `register.open_total`（现值 1 vs 登记簿 OPEN=0）使提交 pin 不可复现。",
  "disposition": "CO-155（工件侧）：移除 co147 `register.open_total`、co148 `register.items_total`、co136 `register.{n_items,kinds}` ⇒ 三件记录不再嵌下游计数快照；并修复 boundary §25 对 co148 计数快照的消费者（co146_boundary_append）。"
                 "**闸覆盖侧仍 OPEN**：co120 P1 仅抽 `*_record` 键、P5 仅扫 `*_sha16_after` ⇒ `register.*`/`open_total`/`items_total`/嵌套 `sha16` 类下游快照无闸（另实测残留：co136 `register.n_items`/`kinds` —— 已由 CO-155 一并移除；co150 `co124.{revision,verdict,n_findings}` 属**上游**记录引用，键名规范问题另计）。",
  "next": "另开执行 CO：定义「下游快照」机判口径（建议：键名带 `_after`/`snapshot` 标记 + SNAPSHOT_DECLARED 声明册，或显式上游允许表）并给负控；实施前以人工复核承接。",
  "closed_by": []},
 {"id": "F-3", "status": "OPEN", "sev": "low",
  "what": "修订号标签失真：boundary §26 记 co124=CO-124.5、§29 pin 表记 CO-124.6，实件为 CO-124.5；handoff §2 记 co147=CO-147.2，实件/工具为 CO-147.1。",
  "disposition": "CO-155 未处置（须二择一并全链同步：bump 实件 revision 或订正标签）。§30 pin 表已按**实件**记 CO-124.5 / CO-147.1。",
  "next": "另开执行 CO 二择一对齐（若视为新版则 bump 实件 + 同步 co150/卡/handoff）。", "closed_by": []},
 {"id": "F-4", "status": "OPEN", "sev": "medium",
  "what": "R-CO153-1 不成立且无机判：`domain_cap`/`identity`/`process_floor` 生产者 `p3_v57_co134_req_impl_separation.py` **不在**规范序内，且以字面量**整表重写**台账 ⇒ 重跑 co134 会静默删除 CO-146/149/153 归属的 3 个 DV。§29 pin 表自身也把 co134 列为生产者（与其序不含 co134 自相矛盾）。",
  "disposition": "CO-155 未处置（须收窄 co134 为只 upsert 自有三域 + 纳入规范序 + 增 K9 域生产者牙齿）。",
  "next": "另开执行 CO：co134 收窄 + 入序 + 牙齿「七域各有规范序内生产者」。", "closed_by": []},
 {"id": "F-5", "status": "OPEN", "sev": "medium",
  "what": "K9 无「域覆盖」牙齿：`kind` 取未列值或 `domain_cap` 缺 `domains` 时零校验通过（静默）；无牙齿断言 kind ∈ 七域。",
  "disposition": "CO-155 未处置。", "next": "另开执行 CO：K9 增 T14（kind 白名单 + domain_cap 必带非空 domains + 负控）。",
  "closed_by": []},
 {"id": "F-6", "status": "OPEN", "sev": "medium",
  "what": "CO-153 的 `declared` 判据只做证据 pin 检查、与值无语义关联 ⇒ 钉任意现行文件 + 任意非空 basis 即通过（实测 0 findings）。",
  "disposition": "CO-155 未处置。", "next": "另开执行 CO：declared 增「证据件须可解析出与值相关字段」或显式降级为未验证类并计数。",
  "closed_by": []},
 {"id": "F-7", "status": "OPEN", "sev": "low",
  "what": "`conservative_ge` 的 faithful 用 DV 自带 inputs 重算（只证内部自洽），未与 DV-INTPAIR-EDGE 的 edge_outer_binding_mm(0.41)/span_min_mm(0.355) 交叉；同闸两处用不同 span 常量（0.585 vs 0.355）⇒「等同忠实下界」不成立（方向偏保守，结论不变）。",
  "disposition": "CO-155 未处置。", "next": "另开执行 CO：faithful 直引 DV-INTPAIR-EDGE 的权威字段并交叉校验。",
  "closed_by": []},
]
MARK = ("；**CO-155（L2 自裁 · executor · CO-154 复评处置）**：F-1 CLOSED（co150 崩溃修复）；F-2 工件侧（co147/co148 下游计数快照移除）"
        "完成、闸覆盖侧 OPEN；F-3..F-7 OPEN。登记 `co154:F-1..F-7`。")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    reg = json.loads(REG.read_text())
    have = {i["finding"]: i for i in reg["items"]}
    added, updated = [], []
    for it in ITEMS:
        f = KEY.format(it["id"])
        item = {"finding": f, "kind": "TOOL_DEFECT", "severity": it["sev"], "what": it["what"],
                "refs": ["CO-154", "CO-155", "CO-153", "CO-152"], "disposition": it["disposition"],
                "status": it["status"], "next": it["next"], "evidence": [f"CO-154 复评件（{it['id']}）"],
                "closed_by": it["closed_by"]}
        if f in have:
            have[f].update({k: v for k, v in item.items() if k != "finding"})
            updated.append(f)
        else:
            reg["items"].append(item)
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
