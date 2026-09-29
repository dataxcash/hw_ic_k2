#!/usr/bin/env python3
"""k2_contraction_v1.py --- **确定性收缩**（#K2-426 §三）：求"最大可交付挪动子集"的**确定性候选序与两类清单**。

规则（确定性 · 零搜索）：**凡其焊盘挂在"证书点名的不可重连网"上的件，优先入"留守"候选**（撤其位移 ⇒ 其网沿用原线 ⇒
不参与抢位）；其余件按（件号）保序入"可挪"候选。**候选 ≠ 结论**：结论须由"逐件撤后重解"的实测确定（零考跑 · 但需逐件工具跑）。
"""
from __future__ import annotations
import argparse, json, os, sys


def contraction_lists(members, netof, residual_nets):
    """**纯函数 · 确定性**：返回 `(stay_candidates, move_candidates)`。
    `netof`={ref:[net,...]}；`residual_nets`=证书点名的不可重连网集合。"""
    stay, move = [], []
    for r in sorted(members):
        if set(netof.get(r, [])) & set(residual_nets):
            stay.append(r)
        else:
            move.append(r)
    return stay, move


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", help='json: {members:[...],netof:{ref:[net..]},residual_nets:[...]}')
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    p = json.load(open(a.params, encoding="utf-8"))
    st, mv = contraction_lists(p["members"], p["netof"], p["residual_nets"])
    rep = {"artifact": "k2_contraction_v1", "stay_candidates": st, "move_candidates": mv,
           "rule": "#K2-426: parts on the certificate's non-reconnectable nets are the STAY candidates (they keep "
                   "their accepted routing); the rest may move. Candidates are not conclusions - each needs a "
                   "per-part try/re-solve reading (zero EXAM runs).", "OWNER-ITEMS": 0}
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
