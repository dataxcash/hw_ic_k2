#!/usr/bin/env python3
"""CO-229 — L2 自裁（义务时点跨载明面同源 + 载明面名集等式机判化）发现入册（幂等、注解**原位**）+ counts 复算。只改登记簿。"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
ADD = [
    {"finding": "co229:F-1", "sev": "mid", "kind": "TOOL_DEFECT",
     "what": "**判定几何源之锚点仅由工件自述承载（R-CO218-1 之「一次性断言」形态）**：SI 等长判定所消费之几何源 `m13_v57_w3_joint_assignment.json`（**非冻结源、非序内 watch**）之**身份**与**16 项上游锚点**"
             "仅由该件自述（`inputs_sha` / `frozen_sha_check`）承载 ⇒ 漂移不可见、无 fail-closed（CO-228 所记残余；方向 fail-open）。",
     "disposition": "CO-229（L2 自裁）：① **身份 pin** `SI_GEOM_SOURCE_SHA16 = 60cbd331836e52b7`（漂移即停机）；② **上游锚点逐项独立复算** `SI_GEOM_PROVENANCE_DECLARED`（16 项逻辑键 → 路径 + sha256）与图纸自述做"
                    "**键集等式 + 自述↔实件一致**；③ **自述诚实性**（`match` 全 True ∧ `drift` 空）；④ 入机判 runner 静态齿 **t39_si_geom_source_anchored**（正/负控齐备）；⑤ 自声明面 bump（runner `CO-203.7`）。**R-CO229-1**。",
     "status": "CLOSED",
     "next": "判定性 verdict 所消费之非冻结、非 watch 工件，其**身份**（sha pin）与**上游锚点**（逐项独立复算 + 键集等式 + 自述↔实件一致）须入规范序机判（承 R-CO218-1 / R-CO228-1）。"
             "**残余（未闭，界定）**：本件不重算几何正确性（由 CO-62/§78 族证据承载），亦不覆盖 L3 全链复现；该 pin 为 **rev-19 专属**，新 rev 变更几何源须显式更新 pin 与锚点表。",
     "evidence": ["实件：几何源 sha16 = 60cbd331836e52b7（= §78 所记冻结图纸）；自述 16 项上游指纹**全部可核**（内容 sha256 逐项一致）；`frozen_sha_check.match` 全 True、`drift = []`",
                  "判别力：篡改声明值 ⇒ `provenance_self_declaration_mismatch`；自述缺一键 ⇒ `provenance_key_drift`；实件漂移 ⇒ `provenance_drift`；不可读 ⇒ `provenance_unreadable`",
                  "修后：`--check` 41/41 全 True"],
     "refs": ["CO-62", "CO-218", "CO-228", "CO-229"], "closed_by": ["CO-229"]},
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
    note = ("；**CO-229（L2 自裁 · 义务同源机判化）**：+1 TOOL_DEFECT（`co229:F-1` U6 阵列义务之载明面枚举无机判齿 ⇒ 域收窄（CO-225 F-4 实测）；"
            "处置 = 静态齿 t37（载明面域显式 + 名集等式双向 + 每面同源锚 + 正负控）；low、CLOSED）。")
    reg["meta"]["updated_by"] = upsert_note(reg["meta"].get("updated_by", ""), "；**CO-229（L2 自裁", note)
    reg["meta"]["counts"] = dict(collections.Counter(i["kind"] for i in reg["items"]))
    reg["meta"]["counts"]["OPEN"] = sum(1 for i in reg["items"] if i["status"] == "OPEN")
    reg["meta"]["counts"]["total"] = len(reg["items"])
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"added": added, "updated": updated, "counts": reg["meta"]["counts"], "sha16": s16(REG)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
