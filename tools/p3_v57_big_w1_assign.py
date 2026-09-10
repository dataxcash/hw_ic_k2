#!/usr/bin/env python3
"""P3 v57 BIG — W1：page↔lane 无交叉指派契约 + 独立穷举 oracle + MUS 核。

契约（W1 只读设计，机器化）：
  一个带内：pages = [(id, connector_row_y)]；lanes = 该带 lane 中心 y 列表(W0 帧)；
  leg 预算 LEG（可达准入）。指派 = 单射 + 无交叉（按 row 升序 → lane 升序严格递增）
  + 每页 |lane_y − row| ≤ LEG。
判定实现 A（kernel，贪心最早可行，区间严格递增选择——该结构下精确）：
  页按 row 升序，逐个取「> 上一已选索引 且 在允许区间内」的最小索引。
判定实现 B（oracle，独立结构）：对 n≤7 全排列枚举，检查单射/单调/可达 —— 防同源。
MUS（两实现同口径）：(基数升序, id 元组字典序) 首个不可行子集 = 唯一 inclusion-min。
"""
from __future__ import annotations

import itertools
import json
import random
from pathlib import Path

OUT = (Path(__file__).resolve().parents[1] / "pm_gate" / "artifacts" / "k2_v4" /
       "L3" / "mcio_feas_step2" / "m13_v57_big_w1_report.json")


def _allowed(lanes, row, leg):
    return [i for i, y in enumerate(lanes) if abs(y - row) <= leg + 1e-9]


def kernel_feasible(pages, lanes, leg):
    ps = sorted(pages, key=lambda p: (p[1], p[0]))
    L = sorted(lanes)
    prev = -1
    for _, row in ps:
        idx = None
        for i in _allowed(L, row, leg):
            if i > prev:
                idx = i
                break
        if idx is None:
            return False
        prev = idx
    return True


def oracle_feasible(pages, lanes, leg):
    L = sorted(lanes)
    ps = sorted(pages, key=lambda p: (p[1], p[0]))
    n = len(ps)
    if n > len(L):
        return False
    for perm in itertools.permutations(range(len(L)), n):
        if any(perm[i] >= perm[i + 1] for i in range(n - 1)):
            continue
        if all(abs(L[perm[i]] - ps[i][1]) <= leg + 1e-9 for i in range(n)):
            return True
    return False


def mus(pages, lanes, leg, engine):
    ids = sorted(p[0] for p in pages)
    for card in range(1, len(ids) + 1):
        for combo in itertools.combinations(ids, card):
            sub = [p for p in pages if p[0] in set(combo)]
            if not engine(sub, lanes, leg):
                return list(combo)
    return None


def main() -> int:
    rng = random.Random(20260909)
    n_inst = 200
    mism, mus_mism, b12 = [], [], 0
    for _ in range(n_inst):
        n = rng.randint(1, 6)
        lanes = [round(40 + i * 1.46, 3) for i in range(rng.randint(n, n + 3))]
        leg = rng.choice([1.46, 2.92, 4.38, 7.3])
        pages = [(f"P{k}", round(rng.choice(lanes) + rng.choice(
            [-3.0, -1.5, -0.5, 0.0, 0.5, 1.5, 3.0]), 3)) for k in range(n)]
        kf = kernel_feasible(pages, lanes, leg)
        of = oracle_feasible(pages, lanes, leg)
        if kf != of:
            mism.append({"pages": pages, "lanes": lanes, "leg": leg,
                         "kernel": kf, "oracle": of})
            continue
        if not kf:
            mk = mus(pages, lanes, leg, kernel_feasible)
            mo = mus(pages, lanes, leg, oracle_feasible)
            if mk != mo:
                mus_mism.append({"pages": pages, "lanes": lanes, "leg": leg,
                                 "kernel_mus": mk, "oracle_mus": mo})
        # 序无关：pages 三序 → 同判定
        outs = {kernel_feasible(sorted(pages, key=lambda p: p[0]), lanes, leg),
                kernel_feasible(sorted(pages, key=lambda p: p[0], reverse=True),
                                lanes, leg),
                kernel_feasible(pages, lanes, leg)}
        if len(outs) == 1:
            b12 += 1
    ok = not mism and not mus_mism and b12 == n_inst
    rep = {"artifact": "m13_v57_big_w1_report",
           "predicate": "W1 无交叉指派 契约 vs 独立穷举 oracle + MUS + 序无关",
           "n_instances": n_inst, "decision_match": n_inst - len(mism),
           "mus_match": n_inst - len(mism) - len(mus_mism),
           "order_invariant": b12, "mismatch": mism, "mus_mismatch": mus_mism,
           "verdict": "PASS" if ok else "FAIL"}
    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("n_instances", "decision_match",
                                          "mus_match", "order_invariant",
                                          "verdict")}, indent=1))
    print("artifact:", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
