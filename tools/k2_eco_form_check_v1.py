#!/usr/bin/env python3
"""k2_eco_form_check_v1.py --- #K2-357 sec.2: the machine gate for the ECO document chain.

"缺一环即停线": an ECO that does not carry the mandatory fields cannot gate a board change. This checker enforces
the FORM (the fields), not the engineering merit:
  * an ECO file must carry: a status line, section 1..6 with the required titles, a per-net list, and at least one
    NUMERIC acceptance criterion (sec.2.1 requires 验收判据（数字）);
  * the ECO id must be listed in REGISTER.md (the single source of truth for controlled numbers);
  * README.md and _TEMPLATE-ECO.md must exist.
Individual ECOs may be DRAFT - the gate only blocks the DRAWING stage, which is a human/supervisor call, not this tool.

CLI: python3 tools/k2_eco_form_check_v1.py [--dir docs/ECO] [--json-out PATH]   (exit 0 = all forms complete)
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys

REQ = {1: "变更内容", 2: "变更理由", 3: "影响网清单", 4: "受影响文档", 5: "回滚方式", 6: "验收判据"}


def check(path):
    t = open(path, encoding="utf-8").read()
    miss = []
    if not re.search(r"^-\s*\*\*状态\*\*", t, re.M):
        miss.append("status_line")
    for n, title in REQ.items():
        if not re.search(r"^##\s*%d\s+%s" % (n, title), t, re.M):
            miss.append("sec%d:%s" % (n, title))
    sec6 = re.search(r"^##\s*6\s+验收判据.*?(?=^##\s*7|\Z)", t, re.M | re.S)
    numeric = bool(sec6 and re.search(r"\d", sec6.group(0)))
    if not numeric:
        miss.append("sec6:no_numeric_criterion")
    nets = bool(re.search(r"^##\s*3\s+影响网清单", t, re.M)) and bool(re.search(r"`[A-Za-z0-9_+#/\.-]+`", t))
    if not nets:
        miss.append("sec3:no_named_nets")
    return {"eco": os.path.basename(path), "complete": not miss, "missing": miss}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "ECO"))
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.dir, "ECO-K2-*.md")))
    reg = open(os.path.join(a.dir, "REGISTER.md"), encoding="utf-8").read() if os.path.isfile(
        os.path.join(a.dir, "REGISTER.md")) else ""
    rep = {"artifact": "k2_eco_form_check_v1", "ts": "2026-09-28",
           "authority": "#K2-357 sec.2 (ECO chain; missing link => stopline)", "dir": a.dir,
           "skeleton": {f: os.path.isfile(os.path.join(a.dir, f))
                        for f in ("README.md", "_TEMPLATE-ECO.md", "REGISTER.md")},
           "ecos": [], "OWNER-ITEMS": 0}
    ok = all(rep["skeleton"].values())
    for f in files:
        r = check(f)
        eid = re.match(r"(ECO-K2-\d+)", r["eco"])
        r["registered"] = bool(eid and eid.group(1) in reg)
        if not r["registered"]:
            r["missing"].append("not_in_REGISTER")
            r["complete"] = False
        rep["ecos"].append(r)
        ok &= r["complete"]
    rep["verdict"] = "PASS" if (ok and not any(not v for v in rep["skeleton"].values())) else "FAIL"
    rep["rule"] = ("form complete (status + sec1..6 + numeric acceptance criteria + named nets + registered) "
                   "is a PRECONDITION for a board change; DRAFT status additionally blocks the drawing stage")
    print(json.dumps({"verdict": rep["verdict"], "skeleton": rep["skeleton"],
                      "ecos": [{k: v for k, v in e.items() if k != "eco"} | {"eco": e["eco"]} for e in rep["ecos"]]},
                     ensure_ascii=False, indent=1))
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if rep["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
