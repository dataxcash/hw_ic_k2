#!/usr/bin/env python3
"""k2_sample_parse_v1.py --- #K2-343 sec.4 W1: SAMPLE LEARNING PIPELINE v1 (parse -> classify -> norms).

Reads the IN-REGISTER product samples (EVM user guides) and extracts, per sample, the CONNECTOR/HEADER INVENTORY
with its functional role.  Then it computes the cross-sample intersection (what every sample carries = the
product-necessary set) versus the singletons (what only some carry = board-specific evaluation furniture).

Charter scope (#K2-343 sec.2): the samples are the LEGAL AUTHORITY for layout policy.  Every extracted fact carries
its document + line citation, and every norm carries an applicability-scope declaration.  Owner is NOT asked
(engineering decisions are autonomous).

Usage: python3 tools/k2_sample_parse_v1.py [--out L2/SAMPLE_RECORDS_v1.json] [--pdfdir <ledger dir>]
"""
import argparse, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = "/home/fila/jqdDev_2025/ic_hw/.omo/supervision/ledger"
OUT = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "SAMPLE_RECORDS_v1.json")
SAMPLES = [("SNLU300", "REF-SNLU300-DS320PR1601RSCEVM-UG.pdf", "DS320PR1601RSC-EVM (16-lane linear redriver x16 riser)"),
           ("SNLU301", "SNLU301-DS320PR412-421EVM.pdf", "DS320PR412-421EVM (x8 redriver/switch riser)"),
           ("SNLU273", "SNLU273-DS160PR810EVM-RSC.pdf", "DS160PR810EVM-RSC (8-lane linear redriver x8 riser)")]
DESIG = re.compile(r"^\s*(JMP\d+[A-Za-z0-9/]*|J\d+|P\d+|SW\d+)\s+(.*)$")
ROLES = [
    ("HOST_EDGE",       ("edge finger", "edge-finger", "straddle", "cem connector", "gold finger")),
    ("POWER_IN",        ("12 v", "12-v", "12v", "vcc source", "power", "supply", "gnd reference", "3.3-v output")),
    ("PRODUCT_HS",      ("mcio", "slimsas", "high-speed", "high speed", "differential")),
    ("PROGRAMMING",     ("jtag", "swd", "tdi", "tdo", "tck", "tms", "trst", "i2c interface", "i2c adapter", "usb2any")),
    ("CONFIG_FURNITURE",("header", "jumper", "mode", "pd_", "power down", "addr", "rsvd", "reserved", "mux", "sel", "enable", "gain",
                         "level", "write protect", "wp", "prsnt", "read_en", "vcc", "clk", "eeprom", "scl", "sda")),
]


def role_of(desc):
    d = desc.lower()
    for r, keys in ROLES:
        for k in keys:
            if k in d:
                return r
    return "UNCLASSIFIED"


def parse_pdf(path, tag):
    txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout
    rows = []
    for i, line in enumerate(txt.splitlines(), 1):
        m = DESIG.match(line)
        if not m:
            continue
        des, desc = m.group(1), m.group(2).strip()
        if not desc or desc.lower().startswith(("designator", "value")):
            continue
        rows.append({"designator": des, "desc": desc[:110], "role": role_of(desc), "cite": "%s text line %d" % (tag, i)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdfdir", default=LEDGER)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    samples, counts = [], {}
    for tag, fn, desc in SAMPLES:
        p = os.path.join(a.pdfdir, fn)
        if not os.path.isfile(p):
            samples.append({"id": tag, "doc": fn, "description": desc, "error": "pdf not in register"})
            continue
        rows = parse_pdf(p, tag)
        c = {}
        for r in rows:
            c[r["role"]] = c.get(r["role"], 0) + 1
        counts[tag] = c
        samples.append({"id": tag, "doc": fn, "description": desc, "n_connector_like": len(rows),
                        "role_histogram": c, "inventory": rows,
                        "figures_in_register": {"SNLU300": ["REF-DS320PR1601EVM-Fig4-1-TopLayer.png",
                                                            "REF-DS320PR1601EVM-Fig4-2-BottomLayer.png"],
                                                "SNLU301": ["S301_layout-20.png", "S301_layout-21.png", "S301_layout-22.png"],
                                                "SNLU273": ["S273_layout-21.png", "S273_layout-22.png"]}[tag]})
    # cross-sample intersection / singletons on the ROLE level (what every sample carries vs what only some carry)
    rolesets = {t: set(counts[t].keys()) for t in counts}
    inter = set.intersection(*rolesets.values()) if rolesets else set()
    union = set.union(*rolesets.values()) if rolesets else set()
    rep = {"artifact": "k2_sample_records_v1", "ts": "2026-09-28",
           "authority": "#K2-343 sec.2/§4 W1: sample learning pipeline (parse -> classify -> norms)",
           "charter_scope": "samples = the legal authority for layout policy; owner is NOT asked (engineering autonomy)",
           "samples": samples,
           "cross_sample": {"per_sample_role_counts": counts, "roles_in_ALL_samples": sorted(inter),
                            "roles_in_SOME_samples": sorted(union - inter),
                            "interpretation": ("roles present in EVERY sample = product-necessary; roles present in "
                                               "only some = board-specific. Config jumpers/selects/debug consoles "
                                               "appear in every EVM because an EVM IS evaluation furniture - they are "
                                               "NOT product-necessary and are the M-ENG-HEADER-FARM habit.")},
           "OWNER-ITEMS": 0}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "per_sample": {t: counts[t] for t in counts},
                      "in_all": sorted(inter), "in_some": sorted(union - inter)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
