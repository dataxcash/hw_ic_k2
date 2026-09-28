#!/usr/bin/env python3
"""k2_delivery_closure_check_v1.py --- asset for #K2-352 C27 ("delivery closure not machine-checked").

WHY: R910's defect was that the k2 commit existed but the PARENT submodule pointer was never updated/pushed, so the
supervisor side could not see the delivery and the channel could not detect "awaiting ruling" (one wasted turn).
C27 requires the delivery to be an ATOMIC four-piece closure:
    (1) k2 has a commit                      (2) k2 is clean and pushed (origin/main...HEAD == 0/0)
    (3) parent's k2 pointer == that commit   (4) parent is clean and pushed (0/0)
A delivery may only be declared complete when all four hold.

CLI: python3 tools/k2_delivery_closure_check_v1.py [--parent ..] [--sub k2] [--json-out PATH]
Exit 0 = PASS (closure complete), 1 = FAIL.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys


def git(*args, cwd):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument("--sub", default="k2")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    parent = os.path.abspath(a.parent)
    sub = os.path.join(parent, a.sub)
    rep = {"artifact": "k2_delivery_closure_check_v1", "ts": "2026-09-28",
           "authority": "#K2-352 C27 (delivery closure machine check)", "pieces": {}, "OWNER-ITEMS": 0}
    ok = True
    rc, head, _ = git("rev-parse", "HEAD", cwd=sub)
    rep["pieces"]["1_k2_head"] = {"value": head if rc == 0 else None, "ok": rc == 0}
    ok &= rc == 0
    rc, st, _ = git("status", "--porcelain", cwd=sub)
    rep["pieces"]["2a_k2_tree_clean"] = {"porcelain": st, "ok": rc == 0 and st == ""}
    ok &= rc == 0 and st == ""
    rc, cnt, _ = git("rev-list", "--left-right", "--count", "origin/main...HEAD", cwd=sub)
    a1, b1 = (cnt.split() or ["?", "?"])[:2]
    rep["pieces"]["2b_k2_pushed"] = {"behind_ahead": cnt, "ok": cnt == "0\t0"}
    ok &= cnt == "0\t0"
    rc, ptr, _ = git("rev-parse", f"HEAD:{a.sub}", cwd=parent)
    rep["pieces"]["3_parent_pointer_matches"] = {"parent_pointer": ptr if rc == 0 else None, "k2_head": head,
                                                "ok": rc == 0 and ptr == head}
    ok &= rc == 0 and ptr == head
    rc, cnt2, _ = git("rev-list", "--left-right", "--count", "origin/main...HEAD", cwd=parent)
    rep["pieces"]["4_parent_pushed"] = {"behind_ahead": cnt2, "ok": cnt2 == "0\t0"}
    ok &= cnt2 == "0\t0"
    rep["verdict"] = "PASS" if ok else "FAIL"
    rep["rule"] = "a delivery may only be declared complete when all four pieces hold (k2 commit / k2 pushed / parent pointer / parent pushed)"
    print(json.dumps(rep, ensure_ascii=False))
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
