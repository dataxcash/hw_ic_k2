#!/usr/bin/env python3
"""k2_p6_n05_coupling_v1.py — **N-05 耦合图**：哪些「导入后从未变更」的遗留产物**正在被现役代码消费**（只读）。

用途：把 N-05 卫生从「121 孤儿 + 656 被引用」的粗账，收敛成**可裁决的短名单**——
按「消费者是否在**判定路径**上（pm_gate checks/gates/closure_check、pipeline engine）」排序，
供监理裁定 P1（重生成/重钉）范围。复用 `k2_p6_repro_chain_health_v1` 的出处与分类口径（同源，避免两套定义）。

输出：`P6_execution/N05_LEGACY_COUPLING_v1.json`（确定性：键排序、无时间戳）。
用法（容器根 ic_hw）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p6_n05_coupling_v1.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(REPO, "k2")
sys.path.insert(0, os.path.join(K2, "tools"))
import k2_p6_repro_chain_health_v1 as H  # noqa: E402  复用同源口径

DEF_OUT = os.path.join(K2, H.ART, "k2_v4", "P6_execution", "N05_LEGACY_COUPLING_v1.json")
GATE_PATH_RE = re.compile(r"_shared/pm_gate/(check_|gates|closure_check|review)|pipeline/(engine|checks)")
CONSUMER_CAP = 12
LINE_CAP = 6


# 严格口径：默认「词面启发式」会把 frozen/ruling/candidates 这类**结构目录名**误判为引用
# （闸代码里出现的是路径段字面量，不是对该产物的消费）⇒ 严格规则只认：
#   ① 完整文件名（≥10 字符，如 channel_alloc.json） ② 长主干（≥12） ③ **含数字的具体目录**（如 channel_alloc_v2）
STRICT_DIR_RE = re.compile(r"\d")
# nature：**机器生成物** vs **人写文档** —— 只有前者才是 N-05（不可复现）卫生项；
# 人写文档（.md 契约/候选/裁决）由仓库拆分复制而来、未经修改属**正常**。
GENERATED_DIRS = ("model_solves", "drc_locator", "verify", "QA", "tasks")
GENERATED_NAME_RE = re.compile(r"(channel_alloc|capacity_map|hs_rebuild|ref_plane_continuity|"
                               r"report\.json|summary\.json|audit.*\.json|.*_solves?\.json|.*\.json)$")


def nature_of(rel: str) -> str:
    parts = rel.split("/")
    if rel.endswith(".json"):
        if any(d in parts for d in GENERATED_DIRS) or GENERATED_NAME_RE.search(os.path.basename(rel)):
            return "generated_json"
        return "config_or_data_json"
    if rel.endswith(".md") or rel.endswith(".txt"):
        return "authored_doc"
    if rel.endswith((".kicad_pcb", ".kicad_pro", ".pdf", ".csv", ".yaml", ".yml")):
        return "board_or_binary"
    return "other"


def classify() -> list:
    add_map, touch_count, _ = H.provenance()
    live = H.live_files()
    corpus = "\n".join(live.values())
    rows = []
    for rel in sorted(x for x in H._git("ls-files", H.ART).splitlines() if x.strip()):
        parent = os.path.basename(os.path.dirname(rel))
        base = os.path.basename(rel)
        stem = re.sub(r"\.(json|md|yaml|yml|kicad_pcb|kicad_pro|csv|txt)$", "", base)
        via = None
        if len(base) >= 10 and base in corpus:
            via = ("file", base)
        elif len(stem) >= 12 and stem in corpus:
            via = ("stem", stem)
        elif len(parent) >= 8 and STRICT_DIR_RE.search(parent) and parent in corpus:
            via = ("dir", parent)
        added, touched = add_map.get(rel), touch_count.get(rel, 0)
        imported = bool(added and added.startswith(H.IMPORT_COMMIT))
        if imported and touched <= 1:
            cls = "STALE_IMPORT_REFERENCED" if via else "STALE_IMPORT_ORPHAN"
        elif imported:
            cls = "IMPORT_ORIGIN_EVOLVED"
        elif via:
            cls = "LIVE"
        else:
            cls = "RECENT_ORPHAN"
        rows.append({"path": rel, "class": cls, "token": via, "nature": nature_of(rel),
                     "bytes": os.path.getsize(os.path.join(K2, rel)) if os.path.isfile(os.path.join(K2, rel)) else 0})
    return rows


def consumers(token: str, live: dict) -> list:
    kind, tok = token
    out = []
    for rel, text in live.items():
        lines = [i for i, l in enumerate(text.splitlines(), 1) if tok in l]
        if lines:
            out.append({"file": rel, "n_lines": len(lines), "lines": lines[:LINE_CAP]})
    return sorted(out, key=lambda c: (-c["n_lines"], c["file"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEF_OUT)
    args = ap.parse_args()
    live = H.live_files()
    rows = classify()
    coupled = []
    for r in rows:
        if r["class"] != "STALE_IMPORT_REFERENCED" or not r["token"]:
            continue
        cons = consumers(r["token"], live)
        on_gate = [c for c in cons if GATE_PATH_RE.search(c["file"])]
        coupled.append({"artifact": r["path"], "token": f"{r['token'][0]}:{r['token'][1]}", "bytes": r["bytes"],
                        "nature": r["nature"],
                        "n_consumers": len(cons), "on_gate_path": bool(on_gate),
                        "gate_consumers": on_gate[:CONSUMER_CAP],
                        "consumers": cons[:CONSUMER_CAP]})
    coupled.sort(key=lambda x: (not x["on_gate_path"], -x["n_consumers"], -x["bytes"]))
    gate_list = [c for c in coupled if c["on_gate_path"]]
    p1 = [c for c in coupled if c["nature"] == "generated_json"]
    p1.sort(key=lambda x: (not x["on_gate_path"], -x["n_consumers"], -x["bytes"]))
    authored = [c for c in coupled if c["nature"] != "generated_json"]
    doc = {"artifact": "k2_p6_n05_coupling", "schema": 1, "readonly": True,
           "method": "出处口径同 k2_p6_repro_chain_health_v1；引用判定用**严格规则**（完整文件名≥10 / 长主干≥12 / 含数字的具体目录≥8）——"
                     "与普查件（宽松词面启发式，656 为上界）不同，本件是**可裁决的严格集**；消费者 = 现役代码（tools 非 P6 工具 + _shared/{eda_core,pm_gate} 非测试 + 项目配置）中命中 token 的文件:行",
           "strictness": {"census_loose_referenced_bound": 656, "note": "宽松口径把 frozen/ruling/candidates 等结构目录名计入 ⇒ 非消费关系"},
           "counts": {c: sum(1 for r in rows if r["class"] == c) for c in
                      ("STALE_IMPORT_ORPHAN", "STALE_IMPORT_REFERENCED", "IMPORT_ORIGIN_EVOLVED", "RECENT_ORPHAN", "LIVE")},
           "stale_referenced_total": len(coupled),
           "on_gate_path_count": len(gate_list),
           "on_gate_path_shortlist": gate_list,
           "nature_split": {"generated_json": len(p1), "authored_or_other": len(authored)},
           "p1_shortlist_generated_stale": p1,
           "note_nature": "只有 **机器生成物**（nature=generated_json）才是 N-05 卫生项；人写文档（.md 契约/候选/裁决）"
                          "由仓库拆分复制而来且未修改属**正常**，不列入 P1。",
           "top_off_gate_path": [c for c in coupled if not c["on_gate_path"]][:20],
           "reading": ["on_gate_path=True ⇒ 该遗留件被**判定路径**（pm_gate checks/gates/closure_check、pipeline engine）消费 ⇒ N-05 P1 重生成/重钉的首选",
                       "on_gate_path=False ⇒ 多为工具/文档级引用 ⇒ 可降级为 P2/P3",
                       "token 为词面启发式（目录名/长主干）⇒ 消费者列表为上界，裁决前可逐条复核"]}
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("STALE_IMPORT_REFERENCED(strict):", len(coupled), "| 在判定路径上:", len(gate_list),
          "| P1(生成物):", len(p1), "| 人写文档:", len(authored))
    for c in p1[:12]:
        g = c["gate_consumers"][0] if c["gate_consumers"] else {}
        print(f"  {c['artifact']}  (token={c['token']}, 消费者 {c['n_consumers']}) → {g.get('file','-')}:{g.get('lines',['-'])[0]}")
    print("→", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
