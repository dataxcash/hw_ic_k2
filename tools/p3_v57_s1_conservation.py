#!/usr/bin/env python3
"""P3 v57 S1 — 守恒判定核心（图纸生成器的资源守恒门；L3 禁贪婪/序无关）。

对象（m13_v57_s1_generator_design.md §1/§2/§4 的机器化）：
  spec = {
    "slots":   [{"i": int, "pos": float}, ...]     # 轴上一维离散候选（升序 pos）
    "blockers":[{"pos": float, "radius": float}, ...]  # 禁列：|pos_slot-pos_b|<radius
    "sep":     float,                               # 页内 P/N 两列最小中心距
    "pages":   [{"id": str, "domain": [lo_i, hi_i]}, ...]  # 每页需 2 个互异槽
  }
  可行 ⇔ 每页在其 domain 内选 2 个槽(i<j, pos 差 ≥ sep, 不被 blocker 排除)，
  且槽全局独占（跨页不共用）。
  证书（不可行）= 规范最小不满足集：按(基数升序, id 元组字典序)首个不可行子集
  ——该子集自动 inclusion-minimal 且唯一确定（与任意枚举序无关）。

实现纪律（L3）：
  - 纯函数；内部一律按 page id canonical sort，杜绝输入序依赖；
  - 引擎 = 确定性递归 + 前向剪枝（禁贪婪 first-fit）；返回唯一(判定, 指派|None)。

与独立基准 p3_v57_s1_exhaustive_ref.py 共享 spec 格式、各自独立实现判定；
A1.1 门（p3_v57_s1_a11_gate.py）对照两引擎输出。
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple


def _slot_blocked(slot_pos: float, blockers) -> bool:
    return any(abs(slot_pos - b["pos"]) < b["radius"] for b in blockers)


def valid_pairs(spec: dict, page: dict, free: set) -> List[Tuple[int, int]]:
    """页在 free 槽集合内的可行 P/N 对（canonical 序：i<j、升序）。"""
    lo, hi = page["domain"]
    cand = [s for s in spec["slots"]
            if lo <= s["i"] <= hi and s["i"] in free
            and not _slot_blocked(s["pos"], spec.get("blockers", []))]
    out = []
    for a in range(len(cand)):
        for bb in range(a + 1, len(cand)):
            if cand[bb]["pos"] - cand[a]["pos"] >= spec["sep"] - 1e-9:
                out.append((cand[a]["i"], cand[bb]["i"]))
    return out


def _solve_kernel(spec: dict) -> Tuple[bool, Optional[Dict[str, Tuple[int, int]]]]:
    """确定性递归 + 前向剪枝。页序 = (候选对个数 asc, id) 动态取最受限；
    结果对序无关（判定唯一）；指派仅作存在性证据（不承诺唯一）。"""
    pages = sorted(spec["pages"], key=lambda p: (9999, p["id"]))
    n = len(pages)
    all_slots = set(s["i"] for s in spec["slots"])
    assign: Dict[str, Tuple[int, int]] = {}

    def feasible_left(k: int, free: set) -> bool:
        # 剩余页最少仍需 2 槽/页（下界剪枝，非贪婪）
        return len(free) >= 2 * (n - k)

    def rec(k: int, free: set) -> bool:
        if k == n:
            return True
        # MRV：取剩余页中当前可行对最少的页（确定性 tie-break = id）
        best_p = None
        best_pairs = None
        for p in pages:
            if p["id"] in assign:
                continue
            pairs = valid_pairs(spec, p, free)
            if not pairs:
                return False                      # 前向检查：某页已无路
            if best_pairs is None or len(pairs) < len(best_pairs) or (
                    len(pairs) == len(best_pairs) and p["id"] < best_p["id"]):
                best_p, best_pairs = p, pairs
        p = best_p
        for pr in best_pairs:
            i, j = pr
            assign[p["id"]] = pr
            nf = free - {i, j}
            if feasible_left(k + 1, nf) and rec(k + 1, nf):
                return True
            del assign[p["id"]]
        return False

    ok = rec(0, all_slots)
    return ok, (dict(assign) if ok else None)


def feasible(spec: dict) -> bool:
    """守恒判定（层谓词）：整组页可同时满足 → True。"""
    return _solve_kernel(spec)[0]


def certificate(spec: dict, engine=_solve_kernel) -> Optional[dict]:
    """不可行 → 规范最小不满足集证书。
    {minimal_core: [page ids], check: {core_infeasible, all_proper_feasible}}
    首个(基数,字典序)不可行子集即 inclusion-minimal 且唯一；可行 → None。"""
    ids = sorted(p["id"] for p in spec["pages"])
    from itertools import combinations
    for card in range(1, len(ids) + 1):
        for combo in combinations(ids, card):
            sub = {"slots": spec["slots"], "blockers": spec.get("blockers", []),
                   "sep": spec["sep"],
                   "pages": [p for p in spec["pages"] if p["id"] in set(combo)]}
            if not engine(sub)[0]:
                return {"minimal_core": list(combo), "engine": engine.__name__,
                        "check": {"core_infeasible": True,
                                  "cardinality": card}}
    return None


def main() -> int:
    print("conservation core (pure) loaded. 用法：feasible(spec) / certificate(spec)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
