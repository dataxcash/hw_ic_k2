#!/usr/bin/env python3
"""CO-162 — 查漏型 L2 闸硬化（第 5 轮）：co106 verdict fail-open + 基线 pin 非约束（G-1）/ 已声明承载区豁免（G-2）。

性质：只改**登记簿**（L2 政策层）；判据由同 CO 的 co106 改动承载。幂等：按 `finding` 键 upsert；counts 重算。
CLI: python3 tools/p3_v57_co162_verdict_binding.py
"""
from __future__ import annotations
import collections, hashlib, json, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
REG = K2 / "pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json"
KEY = "co162:{}"
ITEMS = [
 {"id": "G-1", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**co106 verdict fail-open + 基线 pin 非约束**：verdict 阶梯为 `PASS if hard else (... else PASS)` —— `hard=False ∧ cls_count 空` 时仍判 **PASS**。"
          "实测两项：① 记录本身即 `checks.A_frame_inset_consistency.ok = False`（2 处板框内缩偏差）而 verdict = PASS；"
          "② 把 `BASE['spec_current']` 改成伪值（基线 pin 漂移）后仍 verdict = PASS / rc = 0（`pin_mismatch` 仅被记录、不参与判定）"
          "⇒ 「基线可复现」与「检查通过」两道保证同时失效。",
  "disposition": "CO-162：co106 抽**纯函数** `verdict_of(checks_ok, teeth_ok, pin_mismatch, cls_count)` 并改判据阶梯 —— "
                 "① `pin_mismatch` 非空 ⇒ `BASELINE_MISMATCH`；② `teeth_ok=False` ⇒ `FAIL(teeth)`；③ 任一 check 失败 ⇒ "
                 "`FAIL_DECLARED_COPPER_MISSING` / `INDETERMINATE_REGION_SCOPED` / `FAIL_CHECKS`（**不再回落 PASS**）。"
                 "增牙齿 `baseline_pin_binding` / `fail_open_closed` / `verdict_positive_control`；co106 升 **CO-106.4**。"
                 "实测：真基线 PASS/rc=0；注入漂移 pin ⇒ `BASELINE_MISMATCH`/rc=1。",
  "status": "CLOSED", "next": "凡带 `base_pins` 的闸，其 verdict 必须显式消费 pin 漂移；违者按 fail-open 处理。",
  "evidence": ["CO-162 实测（修前）：co106 记录 verdict=PASS 而 A.ok=False；注入伪 spec pin ⇒ PASS/rc=0",
               "CO-162 复核（修后）：注入伪 spec pin ⇒ verdict=BASELINE_MISMATCH / rc=1；真基线 PASS/rc=0"],
  "refs": ["CO-162", "CO-161", "CO-160", "CO-106"], "closed_by": ["CO-162"]},
 {"id": "G-2", "sev": "medium", "kind": "TOOL_DEFECT",
  "what": "**co106 的板框内缩判据对「桥接承载区」无声明豁免机制**：`P3V3_BCU_BRIDGE_IN4` / `P3V3_AUX_BCU_BRIDGE_IN4`（T2-ECN-1/2 PM 裁决的局部承载 pour，"
          "非整面平面）被算作内缩偏差，却只被记录、不影响判定 ⇒ 偏差被「静默容忍」（与 CO-139「豁免不得只靠自由文本」口径冲突：既无登记也无 pin）。",
  "disposition": "CO-162：co106 增 `DECLARED_NON_FULL_PLANE` **注册表 + 冻结 SPEC pin 锚定**（`s16(SPEC_CUR) == BASE['spec_current']` 时豁免方生效），"
                 "豁免逐条计入 `interior_carriers_exempt`（含 why）；增牙齿 `carrier_exemption_declared_only`（未登记 id 不得豁免）。"
                 "复核：A 检查 dev=0 / ok=True，豁免 4 条（2 内岛 + 2 桥接承载），verdict PASS/rc=0；SPEC pin 漂移时豁免自动失效并落 BASELINE_MISMATCH。",
  "status": "CLOSED", "next": "新增非整面承载区须登记进注册表（含依据），且其豁免仅在冻结 SPEC pin 成立时生效。",
  "evidence": ["CO-162 实测（修前）：A.ok=False 而 verdict=PASS，2 处桥接承载偏差仅记录",
               "CO-162 复核（修后）：注册表豁免后 A dev=0；SPEC pin 漂移 ⇒ 豁免失效 + BASELINE_MISMATCH"],
  "refs": ["CO-162", "CO-139", "CO-122", "CO-106"], "closed_by": ["CO-162"]},
]
MARK = ("；**CO-162（L2 自裁 · 查漏型闸硬化 5）**：G-1 co106 verdict fail-open（`hard=False ∧ cls_count 空` 仍 PASS）+ 基线 pin 非约束 "
        "⇒ 抽 `verdict_of` 纯函数并令 pin 漂移/check 失败一律非 PASS（+ 3 牙齿）；G-2 桥接承载区无声明豁免 ⇒ 注册表 + 冻结 SPEC pin 锚定豁免 "
        "（+ 1 牙齿）；co106 升 CO-106.4。（承接 z35 §5.4）")


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
