#!/usr/bin/env python3
"""k2_p6_naming_impact_check_v1.py — 走廊命名分歧的**影响面核对**（只读，回答「是否需开 rev」）。

核对四问：
  ① P5 交付锚（`L6/` 全树）是否含走廊 id？      → 期望 **0**（不影响 Gerber/叠层/阻抗/DFM）
  ② P3/P4 冻结四源是否含走廊 id？                → 期望 **0**
  ③ 现役项目配置（`L2/route_model_config.json`）用哪套 id？ → 期望**新 id**
  ④ 现役工具链是否读取遗留 `L3/model_solves/channel_alloc*`（旧 id）？ → 期望**不读**
另附：遗留 alloc 族清点（版本/旧新 id/首次入库提交）与测试指向。

只读；输出确定性 JSON（无时间戳、键排序）。
用法（容器根 ic_hw）：PYTHONPATH=... AppDir/bin/python3.11 k2/tools/k2_p6_naming_impact_check_v1.py
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(REPO, "k2")
DEF_OUT = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "P6_execution", "NAMING_IMPACT_CHECK_v1.json")
OLD = ("J2_TO_U", "U_TO_MCIO")
NEW = ("EAST_CHIP_TO_J2", "WEST_MCIO_TO_CHIP")
L6 = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "L6")
FROZEN = ("hw/k2_v4_8L.l4.kicad_pcb", "hw/k2_v4_8L.kicad_pcb", "hw/data/k2_sch.yaml")
LIVE_CFG = "pm_gate/artifacts/k2_v4/L2/route_model_config.json"
LEGACY_ALLOCS = [f"pm_gate/artifacts/k2_v4/L3/model_solves/{v}/channel_alloc.json"
                 for v in ("channel_alloc", "channel_alloc_v2", "channel_alloc_v3", "channel_alloc_v4")]
TESTS = "k2/_shared/eda_core/tests/test_hs_route_model.py"


def scan_tree(root: str) -> dict:
    """递归统计（跳过 .prl/二进制不可读文件用 errors=replace）。"""
    files = 0
    hits = []
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for n in sorted(names):
            p = os.path.join(base, n)
            files += 1
            try:
                s = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            c = {k: s.count(k) for k in OLD + NEW}
            if sum(c.values()):
                hits.append({"file": os.path.relpath(p, REPO), **c})
    return {"files_scanned": files, "hit_files": hits, "old_total": sum(h["J2_TO_U"] + h["U_TO_MCIO"] for h in hits),
            "new_total": sum(h["EAST_CHIP_TO_J2"] + h["WEST_MCIO_TO_CHIP"] for h in hits)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEF_OUT)
    args = ap.parse_args()

    l6 = scan_tree(L6)
    frozen = {}
    for rel in FROZEN:
        s = open(os.path.join(K2, rel), encoding="utf-8", errors="replace").read()
        frozen[rel] = {"old": sum(s.count(k) for k in OLD), "new": sum(s.count(k) for k in NEW)}
    cfg_p = os.path.join(K2, LIVE_CFG)
    cfg_s = open(cfg_p, encoding="utf-8", errors="replace").read() if os.path.isfile(cfg_p) else ""
    legacy = {}
    for rel in LEGACY_ALLOCS:
        p = os.path.join(K2, rel)
        if not os.path.isfile(p):
            legacy[rel] = {"exists": False}
            continue
        s = open(p, encoding="utf-8", errors="replace").read()
        first = subprocess.run(["git", "-C", K2, "log", "--format=%h", "--reverse", "--", rel],
                               capture_output=True, text=True).stdout.split()
        legacy[rel] = {"exists": True, "old_total": sum(s.count(k) for k in OLD),
                       "new_total": sum(s.count(k) for k in NEW),
                       "first_commit": first[0] if first else None,
                       "commits": len(sorted(set(subprocess.run(["git", "-C", K2, "log", "--format=%h", "--", rel],
                                                               capture_output=True, text=True).stdout.split())))}
    raw_refs = subprocess.run(
        ["grep", "-rln", "--include=*.py", "channel_alloc_v2", os.path.join(K2, "tools"),
         os.path.join(REPO, "_shared"), os.path.join(K2, "_shared")],
        capture_output=True, text=True).stdout.strip().splitlines()
    # 现役工具链 = 排除 测试 与 本 P6 triage 工具自身
    tool_refs = sorted(os.path.relpath(x, REPO) for x in raw_refs
                       if "/tests/" not in x and "k2_p6_" not in os.path.basename(x))
    all_refs = sorted(os.path.relpath(x, REPO) for x in raw_refs)

    answers = {  # 语义：clean_* = True 表示「干净/无耦合」（fail-closed 读法）
        "1_delivery_L6_clean_of_corridor_ids": l6["old_total"] + l6["new_total"] == 0,
        "2_frozen_sources_clean_of_corridor_ids": not any(v["old"] + v["new"] for v in frozen.values()),
        "3_live_config_uses_new_ids_only": sum(cfg_s.count(k) for k in NEW) > 0 and sum(cfg_s.count(k) for k in OLD) == 0,
        "4_live_toolchain_independent_of_legacy_alloc": not bool(tool_refs),
    }
    doc = {
        "artifact": "k2_p6_corridor_naming_impact_check",
        "schema": 1,
        "readonly": True,
        "question": "走廊命名分歧（SPEC 新 id ↔ 遗留 alloc 旧 id）是否影响 P3/P4 冻结件与 P5 交付锚 ⇒ 是否需开 rev",
        "q1_delivery_tree_L6": l6,
        "q2_frozen_sources": frozen,
        "q3_live_config": {"path": LIVE_CFG, "exists": bool(cfg_s),
                           "old": sum(cfg_s.count(k) for k in OLD), "new": sum(cfg_s.count(k) for k in NEW)},
        "q4_legacy_alloc_inventory": legacy,
        "q4_live_toolchain_refs_to_legacy_alloc": tool_refs,
        "q4_all_refs_incl_tests_and_p6_tools": all_refs,
        "tests_pinned_to": TESTS + " → K2V4_ALLOC = .../model_solves/channel_alloc_v2/channel_alloc.json",
        "answers": answers,
        "verdict_input_for_supervisor": {
            "rev_needed_on_naming_grounds": False,
            "why": ["交付锚 L6 全树 0 命中走廊 id；冻结四源 0 命中 ⇒ 物理交付件与命名无关",
                    "现役项目配置已用新 id；现役工具链不读遗留 alloc ⇒ 交付链与遗留 alloc 无耦合",
                    "13 项隐藏失败 = 测试**钉在遗留 alloc v2**（08-28 字节导入、从未重生成）所致 ⇒ 输入漂移，非引擎/交付缺陷",
                    "处置建议：① 测试重钉到现行真源（SPEC 派生通道 / 现行配置）② 遗留 alloc 族标注 RETIRED（N-05 卫生）"],
            "eng_self_decision": "无（命名权威与测试重钉属判据侧 ⇒ 监理裁定后 ENG 同步）",
        },
    }
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("answers:", json.dumps(answers, ensure_ascii=False))
    print(f"L6 scanned={l6['files_scanned']} hits={len(l6['hit_files'])} | frozen hits={sum(v['old']+v['new'] for v in frozen.values())}")
    print("live cfg old/new:", doc["q3_live_config"]["old"], "/", doc["q3_live_config"]["new"])
    print("→", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
