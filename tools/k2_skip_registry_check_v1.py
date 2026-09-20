#!/usr/bin/env python3
"""k2_skip_registry_check_v1.py —— **skip 登记完备性核对**（只读；**不新增判据维**）。

用途：把『**skipped 不得充绿**』做成可核对：套件实测 junit 中的**每一条 SKIP** 必须在
      《退役/处置登记件》里有**具名条目**（classes[].tests 或 excluded.tests）。
      未登记 = FAIL（存在『未定性 skip』）。

非判据维：本件只核 ENG **自己的登记完备性**，不产出/不改变任何产品判据，亦不改判据集。

用法：
  python3 k2/tools/k2_skip_registry_check_v1.py --registry <registry.json> --junit <suite.xml> [--out ...]
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET


def norm(name: str) -> str:
    """归一：`tests.test_x.TestY::test_z` / `tests.test_x.TestY.test_z` 皆 ⇒ `TestY::test_z`。"""
    s = name.replace(".py", "").replace(".", "::", 1) if "::" not in name else name
    parts = [p for p in s.replace(".", "::").split("::") if p]
    return "::".join(parts[-2:]) if len(parts) >= 2 else s


def skipped_from_junit(path: str) -> list:
    root = ET.parse(path).getroot()
    out = []
    for tc in root.iter("testcase"):
        for ch in tc:
            if ch.tag == "skipped":
                out.append(f"{tc.get('classname','')}::{tc.get('name','')}")
    return out


def registered_from_registry(doc: dict) -> list:
    out = []
    for c in (doc.get("classes") or []):
        out += list(c.get("tests") or [])
    ex = doc.get("excluded") or {}
    out += list(ex.get("tests") or [])
    for c in (doc.get("retirement_entries") or []):
        out += list(c.get("tests") or [])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--junit", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    reg = json.load(open(a.registry, encoding="utf-8"))
    meas = skipped_from_junit(a.junit)
    regs = registered_from_registry(reg)
    m_norm = {norm(x): x for x in meas}
    r_norm = {norm(x): x for x in regs}
    unregistered = sorted(set(m_norm) - set(r_norm))
    registered_not_seen = sorted(set(r_norm) - set(m_norm))
    doc = {"artifact": "k2_skip_registry_check", "schema": 1, "readonly": True,
           "registry": a.registry, "junit": a.junit,
           "n_skipped_measured": len(meas), "n_registered": len(regs),
           "unregistered_skips": unregistered, "registered_but_not_seen": registered_not_seen,
           "verdict": "PASS" if not unregistered else "FAIL",
           "note": "未登记 skip = 存在未定性 skip ⇒ FAIL；registered_but_not_seen 仅信息项（如该次运行未收集到）"}
    print(f"  实测 skip {len(meas)} · 登记 {len(regs)} ⇒ 未登记 {len(unregistered)} · 登记未出现 {len(registered_not_seen)}")
    for x in unregistered:
        print(f"    UNREGISTERED {x}")
    for x in registered_not_seen:
        print(f"    (info) 登记但本次未出现 {x}")
    print(f"  => {doc['verdict']}")
    if a.out:
        json.dump(doc, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if doc["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
