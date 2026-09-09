#!/usr/bin/env python3
"""P3 v57 S1 — 独立穷举基准（A1.1 对照方；与守恒核心结构无关，防同源自证）。

与 p3_v57_s1_conservation.py 共享同一 spec 契约：
  {slots:[{i,pos}], blockers:[{pos,radius}], sep, pages:[{id,domain:[lo,hi]}]}
判定 = 每页在其 domain 内取 2 互异槽（pos 差 ≥ sep、不被 blocker 排除）且槽跨页独占。

本文件实现策略（刻意与核心不同）：
  - 无 MRV / 无前向剪枝 / 无下界计数剪枝；
  - 页按 id 固定序深度优先，逐页枚举止于该页『当前全槽序的最小可行对』；
  - 指派失败即回溯（朴素回溯）。
  判定与 MUS 枚举定义与核心一致（基数升序、元组字典序首个不可行子集）。
"""
from __future__ import annotations

import itertools
from typing import Dict, List, Optional, Tuple


def _pair_candidates_naive(spec: dict, page: dict, used: set) -> List[Tuple[int, int]]:
    """朴树枚举止于 id 序的全候选（被 blocker/used/sep 过滤）。"""
    lo, hi = page["domain"]
    idx = [s for s in spec["slots"]
           if lo <= s["i"] <= hi and s["i"] not in used
           and not any(abs(s["pos"] - b["pos"]) < b["radius"]
                       for b in spec.get("blockers", []))]
    return [(idx[a]["i"], idx[b]["i"])
            for a in range(len(idx))
            for b in range(a + 1, len(idx))
            if idx[b]["pos"] - idx[a]["pos"] >= spec["sep"] - 1e-9]


def _solve_bruteforce(spec: dict) -> Tuple[bool, Optional[Dict[str, Tuple[int, int]]]]:
    """固定 id 序朴素回溯（无启发式）。结果与核心一致（都精确）。"""
    pages = sorted(spec["pages"], key=lambda p: p["id"])
    n = len(pages)
    used: set = set()
    assign: Dict[str, Tuple[int, int]] = {}

    def rec(k: int) -> bool:
        if k == n:
            return True
        p = pages[k]
        for pr in _pair_candidates_naive(spec, p, used):
            i, j = pr
            used.add(i); used.add(j)
            assign[p["id"]] = pr
            if rec(k + 1):
                return True
            del assign[p["id"]]
            used.discard(i); used.discard(j)
        return False

    ok = rec(0)
    return ok, (dict(assign) if ok else None)


def feasible(spec: dict) -> bool:
    return _solve_bruteforce(spec)[0]


def certificate(spec: dict) -> Optional[dict]:
    ids = sorted(p["id"] for p in spec["pages"])
    for card in range(1, len(ids) + 1):
        for combo in itertools.combinations(ids, card):
            sub = {"slots": spec["slots"], "blockers": spec.get("blockers", []),
                   "sep": spec["sep"],
                   "pages": [p for p in spec["pages"] if p["id"] in set(combo)]}
            if not _solve_bruteforce(sub)[0]:
                return {"minimal_core": list(combo),
                        "engine": "_solve_bruteforce",
                        "check": {"core_infeasible": True,
                                  "cardinality": card}}
    return None


def main() -> int:
    print("exhaustive reference (independent) loaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
