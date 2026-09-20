#!/usr/bin/env python3
"""B2-4 收口件（**未落件**）：撤 K1 G1.5 WAIVER ⇒ 真机判记录。

背景（既有监理裁定，非本轮发明）：
  · K1-RULING-r03-gbid「G1.5 属真缺口，归批 2（C-3），不作阻塞」；
  · 监理指令 #K1-02 第 3 条「L1 段显式标注实质已过 · 待批 2 修工具」；
  · ⇒ 原文：「**待学习环批 2 修工具后重跑机判并撤 waiver**（RISK-001）」。
批 2 已落 F-1/B2-4（`check_l1.RULES_DOC → <框架根>/docs/PCB_DESIGN_RULES.md`，共享层 fc59771），
实测 K1 G1.5 **真机判 PASS**（两跑逐字节同）：`结构预检 + 工艺常识强条全 PASS（3 份报告）`。

本器 = 把该「撤 waiver」动作做成**可复算的一步**（幂等）：
  ① `k1/pm_gate/tools/k1_closeout_l2_v1.py`：写者常量 G15_EVIDENCE + RISK-001 文案 → 真机判口径；
  ② `k1/pm_gate/state_k1.json`：G1.5.evidence / risks[RISK-001] → 真机判口径（保留撤销前原文以便追溯）。
用法：python3 apply_k1_g15_waiver_retraction_v1.py [--root <k1 目录>] [--apply]   （默认 --check，不写盘）
授权：CHECKLIST B2-4 标「**需监理批**（撤 waiver = 判据收紧）」⇒ 本件仅备料，落件须监理批。
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

OLD_EV_MARK = "WAIVER（账本 C-3）"
NEW_G15 = (
    "真机判 PASS（撤 WAIVER · B2-4 / 账本 C-3 闭环）：check_l1.RULES_DOC 已修为 "
    "`<框架根>/docs/PCB_DESIGN_RULES.md`（共享层 fc59771，F-1/B2-4），K1 侧解析 = "
    "`_shared/docs/PCB_DESIGN_RULES.md`；机判读数（两跑逐字节同）= "
    "「结构预检 + 工艺常识强条全 PASS（3 份报告）」⇒ 依 K1-RULING-r03-gbid + 监理指令 #K1-02 第 3 条"
    "「待学习环批 2 修工具后重跑机判并撤 waiver」（RISK-001），本记录由 **WAIVER 转载真机判**，原 WAIVER 原文见本件撤销留痕。"
)
WAIVER_ARCHIVE_TAG = "【撤销留痕·原 WAIVER 记录】"
OLD_RISK_DESC_MARK = "G1.5 机判不可用"
NEW_RISK_DESC = ("G1.5 WAIVER 已闭环（批 2 F-1/B2-4 修好 RULES_DOC）：K1 G1.5 转为**真机判 PASS**"
                 "（两跑逐字节同：「结构预检 + 工艺常识强条全 PASS（3 份报告）」）⇒ waiver 已撤，账本 C-3 可关。"
                 "原 WAIVER 记录留痕于 L1.gates.G1.5.evidence_waiver_archived。")
OLD_TOOL_MARK = "G15_EVIDENCE = ("


def patch_tool(p: Path, apply: bool) -> str:
    s = p.read_text(encoding="utf-8")
    if "真机判 PASS（撤 WAIVER" in s:
        return "already"
    i = s.index("G15_EVIDENCE = (")
    j = s.index(")\n", i) + 2
    old = s[i:j]
    assert OLD_EV_MARK in old, "G15_EVIDENCE 旧文未命中"
    new = 'G15_EVIDENCE = (\n    "' + NEW_G15 + '")\n'
    s2 = s[:i] + new + s[j:]
    # RISK-001 文案
    k = s2.index('("RISK-001"')
    k2 = s2.index("L3\"),", k) + len("L3\"),")
    old_r = s2[k:k2]
    assert "撤 waiver" in old_r, "RISK-001 旧文未命中"
    new_r = ('("RISK-001", "' + NEW_RISK_DESC + '", "L3"),')
    s2 = s2[:k] + new_r + s2[k2:]
    # 模块 docstring 的「待…撤 waiver」表述
    s2 = s2.replace("        依裁定与 #K1-02 第 3 条记 passed（WAIVER，待学习环批 2 修工具后重跑撤 waiver），\n",
                    "        批 2（F-1/B2-4）修好 RULES_DOC 后**已撤 waiver**：改记真机判 PASS（两跑逐字节同），\n", 1)
    if apply:
        p.write_text(s2, encoding="utf-8")
    return "patched"


def patch_state(p: Path, apply: bool) -> str:
    d = json.loads(p.read_text(encoding="utf-8"))
    g15 = d["stages"]["L1"]["gates"]["G1.5"]
    if "真机判 PASS（撤 WAIVER" in (g15.get("evidence") or ""):
        return "already"
    assert OLD_EV_MARK in (g15.get("evidence") or ""), "state G1.5 旧 WAIVER 文未命中"
    g15["evidence_waiver_archived"] = WAIVER_ARCHIVE_TAG + g15["evidence"]
    g15["evidence"] = NEW_G15
    g15["checked_at"] = "2026-09-20T14:00:00+00:00"
    for r in d.get("risks", []):
        if r.get("id") == "RISK-001":
            assert OLD_RISK_DESC_MARK in r.get("desc", ""), "RISK-001 旧文未命中"
            r["desc_waiver_archived"] = r["desc"]
            r["desc"] = NEW_RISK_DESC
            r["status"] = "closed"
            r["closed_at"] = "2026-09-20T14:00:00+00:00"
    if apply:
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return "patched"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/home/fila/jqdDev_2025/ic_hw/k1")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    root = Path(a.root)
    if a.apply and a.root == "/home/fila/jqdDev_2025/ic_hw/k1":
        print("⛔ 拒绝直接落真源：B2-4 撤 waiver = 判据收紧，须监理批。请用 --root <副本> 演练，或经授权后由监理放行。")
        return 2
    out = {}
    for rel in ("pm_gate/tools/k1_closeout_l2_v1.py", "pm_gate/state_k1.json"):
        p = root / rel
        if rel.endswith(".py"):
            out[rel] = patch_tool(p, a.apply)
        else:
            out[rel] = patch_state(p, a.apply)
    print(json.dumps({"mode": "apply" if a.apply else "check", "root": str(root), "result": out}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
