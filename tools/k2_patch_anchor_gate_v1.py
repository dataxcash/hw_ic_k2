#!/usr/bin/env python3
"""k2_patch_anchor_gate_v1.py —— #K2-466 §2.6 **锚点前置核验闸**（纯函数 · 无 pcbnew · 零考跑）。

立法缘由（本席连错 2 次之根因）：**按记忆打补丁**、未先读当前锚点 ⇒ 半改态转红（`R1476`／`R1480` 两次同根因）。
本闸把纪律机器化：**每个待改文件先读原文 → 断言目标串「当前存在且恰好 1 次」→ 全部通过才写**；
**任一断言失败 ⇒ 整批不写（all-or-nothing）**，**树永不停在半改态**。
"""
from __future__ import annotations
import collections, json, os


def check_anchors(edits):
    """`edits = [{"path":..,"old":..,"new":..}]`（`count` 默认 1）。**只读**。返回 {"ok","problems","counts"}。"""
    problems, counts = [], {}
    for e in edits:
        p, old = e.get("path"), e.get("old")
        want = int(e.get("count", 1))
        if not p or old is None:
            problems.append({"path": p, "why": "missing path/old"}); continue
        if not os.path.isfile(p):
            problems.append({"path": p, "why": "file not found"}); continue
        txt = open(p, encoding="utf-8").read()
        n = txt.count(old)
        counts[p] = counts.get(p, 0) + n
        if n != want:
            problems.append({"path": p, "why": "anchor count %d != expected %d" % (n, want),
                             "anchor_head": old[:60]})
    return {"ok": not problems, "problems": problems, "counts": counts}


def apply_batch(edits):
    """**all-or-nothing**：任一锚点不合格 ⇒ **零写入**；全合格 ⇒ 逐条替换（各 1 次）并写回。返回报告。"""
    chk = check_anchors(edits)
    if not chk["ok"]:
        chk["applied"] = 0
        return chk
    done = []
    for e in edits:
        p, old, new = e["path"], e["old"], e["new"]
        txt = open(p, encoding="utf-8").read()
        assert txt.count(old) == int(e.get("count", 1))
        open(p, "w", encoding="utf-8").write(txt.replace(old, new, int(e.get("count", 1))))
        done.append(p)
    chk["applied"] = len(done); chk["written"] = done
    return chk


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--edits", required=True,
                                                    help="json file: [{'path','old','new'[, 'count']}, ...]")
    a = ap.parse_args(argv)
    rep = apply_batch(json.load(open(a.edits, encoding="utf-8")))
    print(json.dumps(rep, ensure_ascii=False))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
