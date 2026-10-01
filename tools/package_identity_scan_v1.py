#!/usr/bin/env python3
"""package_identity_scan_v1 - THE SHARED GAUGE (#K2-554 sec.4 item 2d).
Both the ENG's self-check and the supervisor's acceptance call THIS file, so "self-check output == acceptance
evidence". It scans EVERY file of a package for historical board-line identity tokens, EXCEPT the coordinate
formats whose byte streams legitimately contain those letters/digits as incidental hex substrings
(*.gbr, *.drl, *.gbrjob, *drl_map.svg) - that exclusion is the only one, and it is stated here, not implied.

Usage: package_identity_scan_v1.py <package_dir> [<package_dir> ...]     exit 0 = clean, 1 = hits (raw hits on stdout)
"""
import json
import os
import sys

TOKENS = ("l8", "l7", "#K2-36", "#K2-34", "P5")
EXCLUDE_SUFFIX = (".gbr", ".drl", ".gbrjob")
EXCLUDE_NAME_SUFFIX = ("drl_map.svg",)
PHRASES = ("170 warning", "170 全 warning")


def scan(root: str) -> dict:
    hits = {}
    for dirpath, _dirs, files in os.walk(root):
        for f in sorted(files):
            if f.endswith(EXCLUDE_SUFFIX) or f.endswith(EXCLUDE_NAME_SUFFIX):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, root)
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as fh:
                    t = fh.read()
            except OSError:
                continue
            found = sorted({tok for tok in TOKENS if tok in t} | {ph for ph in PHRASES if ph in t})
            if found:
                hits[rel] = found
    return {"package": os.path.abspath(root), "tokens": list(TOKENS) + list(PHRASES),
            "excluded_suffixes": list(EXCLUDE_SUFFIX) + list(EXCLUDE_NAME_SUFFIX),
            "n_hits": len(hits), "hits": hits, "verdict": "CLEAN" if not hits else "HITS"}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    out = [scan(d) for d in argv]
    print(json.dumps(out if len(out) > 1 else out[0], ensure_ascii=False, indent=1))
    return 0 if all(o["verdict"] == "CLEAN" for o in out) else 1


if __name__ == "__main__":
    sys.exit(main())
