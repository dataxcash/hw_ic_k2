#!/usr/bin/env python3
"""k2_p6_repro_chain_health_v1.py — **N-05 复现链健康度普查**（只读；把 N-05 从「登记」变成「可执行清单」）。

背景：N-05「生成器不可复跑」此前只被登记。本轮实证发现遗留 `channel_alloc*`（08-28 自
`strix-halo-ioconvert` **字节导入、从未重生成**、现役链不读）——本器把该现象**全量普查**，
按「git 出处 × 现役引用」给每个产物定性，输出可执行卫生清单（**处置须授权**）。

判定口径：
  · `added_by`   = `git log --reverse --diff-filter=A` 首次新增提交
  · `touched`    = 触及该路径的提交数（1 ⇒ 自首次之后从未变更）
  · `referenced` = 其**父目录名**或**文件名主干**是否出现在**现役代码**（k2/tools/*.py、
                   _shared/eda_core 与 _shared/pm_gate 的非测试模块、项目配置）；测试引用**不计**现役
  分类：`LEGACY_ORPHAN`（首次=导入提交 ∧ 从未再动 ∧ 现役不引用）· `LEGACY_REFERENCED`（同出处但被引用）
        `RECENT_ORPHAN`（后续提交动过但现役不引用）· `LIVE`（被现役引用）

只读 + 自校验：工具内部跑两遍并比对字节，`deterministic` 字段自证（无需外部重复跑）。
用法（容器根 ic_hw）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 k2/tools/k2_p6_repro_chain_health_v1.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(REPO, "k2")
ART = "pm_gate/artifacts"
IMPORT_COMMIT = "1a883b8"          # 建独立 K2 工程：自 strix-halo-ioconvert 字节复制
DEF_OUT = os.path.join(K2, ART, "k2_v4", "P6_execution", "REPRO_CHAIN_HEALTH_v1.json")
DETAIL_CAP = 300


def _git(*args) -> str:
    return subprocess.run(["git", "-C", K2, *args], capture_output=True, text=True).stdout


def provenance() -> dict:
    add_map, touch_count, last_map = {}, {}, {}
    cur = None
    for line in _git("log", "--reverse", "--format=C%H", "--name-only", "--diff-filter=A", "--", ART).splitlines():
        if line.startswith("C"):
            cur = line[1:8]
        elif line.strip():
            add_map.setdefault(line.strip(), cur)
    for line in _git("log", "--format=C%H", "--name-only", "--", ART).splitlines():
        if line.startswith("C"):
            cur = line[1:8]
        elif line.strip():
            p = line.strip()
            touch_count[p] = touch_count.get(p, 0) + 1
            last_map.setdefault(p, cur)
    return add_map, touch_count, last_map


def live_corpus() -> str:
    parts = []
    for base, dirs, files in os.walk(os.path.join(K2, "tools")):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for n in sorted(files):
            if n.endswith(".py") and not n.startswith("k2_p6_"):
                parts.append(open(os.path.join(base, n), encoding="utf-8", errors="replace").read())
    for root in (os.path.join(REPO, "_shared", "eda_core"), os.path.join(REPO, "_shared", "pm_gate")):
        for base, dirs, files in os.walk(root):
            dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", "tests"))
            for n in sorted(files):
                if n.endswith(".py") or n == "project.yaml":
                    parts.append(open(os.path.join(base, n), encoding="utf-8", errors="replace").read())
    for rel in ("pm_gate/project.yaml", "pipeline.yaml"):
        p = os.path.join(K2, rel)
        if os.path.isfile(p):
            parts.append(open(p, encoding="utf-8", errors="replace").read())
    return "\n".join(parts)


def scan() -> dict:
    add_map, touch_count, last_map = provenance()
    corpus = live_corpus()
    rows = []
    for rel in sorted(x for x in _git("ls-files", ART).splitlines() if x.strip()):
        p = os.path.join(K2, rel)
        parent = os.path.basename(os.path.dirname(rel))
        stem = re.sub(r"\.(json|md|yaml|yml|kicad_pcb|kicad_pro|csv|txt)$", "", os.path.basename(rel))
        # 收紧：父目录名命中 > 主干命中；主干须 ≥8 字符（排除 report/summary/data 等泛词误命中）
        via = None
        if len(parent) > 3 and parent in corpus:
            via = f"dir:{parent}"
        elif len(stem) >= 8 and stem in corpus:
            via = f"stem:{stem}"
        referenced = via is not None
        added, touched = add_map.get(rel), touch_count.get(rel, 0)
        imported = bool(added and added.startswith(IMPORT_COMMIT))
        if imported and touched <= 1:                       # 导入后**从未变更** ⇒ 真遗留
            cls = "STALE_IMPORT_REFERENCED" if referenced else "STALE_IMPORT_ORPHAN"
        elif imported:                                      # 导入过但后续演化 ⇒ 正常演进
            cls = "IMPORT_ORIGIN_EVOLVED"
        elif referenced:
            cls = "LIVE"
        else:
            cls = "RECENT_ORPHAN"
        rows.append({"path": rel, "class": cls, "added_by": added, "last_touched": last_map.get(rel),
                     "touched": touched, "referenced": referenced, "ref_via": via,
                     "bytes": os.path.getsize(p) if os.path.isfile(p) else 0})
    counts, bytes_by = {}, {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
        bytes_by[r["class"]] = bytes_by.get(r["class"], 0) + r["bytes"]
    details = {}
    for cls in ("STALE_IMPORT_ORPHAN", "STALE_IMPORT_REFERENCED", "RECENT_ORPHAN"):
        group = sorted((r for r in rows if r["class"] == cls), key=lambda r: -r["bytes"])
        details[cls] = group[:DETAIL_CAP]
        details[cls + "_truncated"] = max(0, len(group) - DETAIL_CAP)
    legacy_dirs: dict = {}
    for r in rows:
        if r["class"].startswith("STALE_IMPORT"):
            d = os.path.dirname(r["path"])
            legacy_dirs[d] = legacy_dirs.get(d, 0) + 1
    return {"artifact": "k2_p6_repro_chain_health", "schema": 1, "readonly": True,
            "import_commit": IMPORT_COMMIT,
            "scope": ART, "tracked_files": len(rows),
            "counts": counts, "bytes_by_class": bytes_by,
            "stale_top_dirs": dict(sorted(legacy_dirs.items(), key=lambda kv: -kv[1])[:25]),
            "details": details,
            "reading": ["STALE_IMPORT_ORPHAN = 1a883b8 字节导入 ∧ 此后从未变更 ∧ 现役代码不引用 ⇒ **N-05 卫生候选**（标 RETIRED 或重生成）",
                        "STALE_IMPORT_REFERENCED = 同上但被现役代码引用 ⇒ **需重生成/重钉**（如 channel_alloc_v2 被测试钉住）",
                        "IMPORT_ORIGIN_EVOLVED = 导入后已被正常演进（非卫生项）· RECENT_ORPHAN = 后续新增但现役不引用",
                        "处置均须授权；本件只读"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEF_OUT)
    args = ap.parse_args()
    first = json.dumps(scan(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    second = json.dumps(scan(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    doc = json.loads(first)
    doc["deterministic"] = (first == second)
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("tracked:", doc["tracked_files"], "| counts:", json.dumps(doc["counts"], ensure_ascii=False))
    print("bytes_by_class:", json.dumps(doc["bytes_by_class"], ensure_ascii=False))
    print("deterministic:", doc["deterministic"], "→", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
