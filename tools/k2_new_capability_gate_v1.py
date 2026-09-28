#!/usr/bin/env python3
"""k2_new_capability_gate_v1.py --- C34 (#K2-375 sec.5): the sec.20 PREREQUISITE machine gate.

WHY: #K2-373 made 'answer the sec.20 three questions FIRST' a prerequisite for a new-capability window, but nothing
enforced it - the ENG wrote a parallel implementation of `relocate` M3 before asking, and the ledger shows an
in-repo product (C17 v1) already covered that stage. C34 = 'the new-product-capability window has no sec.20 gate'.

WHAT: before a new-capability window may open (i.e. before any run), this gate REQUIRES the ledger entry for that
capability to carry:
    Q1 same-kind product exists   (in-repo reading + external reading)
    Q2 copyable artifact          (a non-empty primary_in_repo list, OR an explicit statement that no product is
                                   obtainable - sec.20.5 only allows the custom path in that case)
    Q3 difference list            (what the copyable product does NOT do / what our path adds)
Exit 0 = gate PASS (window may open). Exit 1 = REFUSED (missing prerequisite). Exit 2 = usage/ledger error.

CLI: python3 tools/k2_new_capability_gate_v1.py --capability A_prime_C33_three_questions [--json-out P]
"""
from __future__ import annotations
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "PRODUCT_THREE_QUESTIONS_LEDGER_v1.json")
NO_PRODUCT_MARKERS = ("no product", "not obtainable", "none obtainable", "不存在可抄", "无成品可得")


def check(capability, ledger=LEDGER):
    if not os.path.isfile(ledger):
        return {"verdict": "ERROR", "reason": "ledger not found", "ledger": ledger}
    d = json.load(open(ledger, encoding="utf-8"))
    e = d.get(capability)
    if not isinstance(e, dict):
        return {"verdict": "REFUSED", "capability": capability,
                "reason": "no sec.20 entry for this capability in the ledger - answer the three questions BEFORE opening the window",
                "missing": ["entry"], "ledger": ledger}
    miss = []
    q1 = e.get("Q1_same_kind_product_exists")
    if not isinstance(q1, dict) or not (q1.get("in_repo") or q1.get("external")):
        miss.append("Q1_same_kind_product_exists")
    q2 = e.get("Q2_copyable_product_artifact")
    if not isinstance(q2, dict):
        miss.append("Q2_copyable_product_artifact")
    else:
        arts = q2.get("primary_in_repo") or []
        note = json.dumps(q2, ensure_ascii=False).lower()
        if not arts and not any(m in note for m in NO_PRODUCT_MARKERS):
            miss.append("Q2:no_copyable_artifact_and_no_explicit_no_product_statement")
    if not isinstance(e.get("Q3_difference_list"), dict):
        miss.append("Q3_difference_list")
    out = {"artifact": "k2_new_capability_gate_v1", "capability": capability, "ledger": ledger,
           "missing": miss, "verdict": "REFUSED" if miss else "PASS",
           "rule": "#K2-375 sec.5 (C34): a new-capability window may not open until the ledger carries the sec.20 "
                   "three questions for it (same-kind product / copyable artifact / difference list)"}
    if not miss:
        out["copyable_artifacts"] = (e.get("Q2_copyable_product_artifact") or {}).get("primary_in_repo", [])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capability", required=True)
    ap.add_argument("--ledger", default=LEDGER)
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    r = check(a.capability, a.ledger)
    print(json.dumps(r, ensure_ascii=False))
    if a.json_out:
        json.dump(r, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if r["verdict"] == "PASS" else (2 if r["verdict"] == "ERROR" else 1)


if __name__ == "__main__":
    sys.exit(main())
