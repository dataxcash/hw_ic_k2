#!/usr/bin/env python3
"""P3 v57 S1 — A1.4 单向性门（L4 落地机器谓词，现状 S1 代码 + 派生物重跑覆盖）。

规则（对 tools/p3_v57_s1_*.py 全部 S1 源码静态 grep）：
  G1 禁板文件窗口反猜：无 REGION_WINDOWS / extract_region_pads / x-window 选区；
  G2 禁 max-x 取端反猜：无按 x 最大值选端点的取端写法（x > prev 类收端）；
  G3 禁引擎装配路径：不 import hs_route_model / solve_pipeline / channel_alloc /
     escape_landing / escape_allocator / route_input（生成器不消费旧簿）；
  G4 板文件读取白名单：k2_v4.kicad_pcb 仅 page_manifest.conn_pad_global 内出现
     （REFCLK 第二端 net-join 补录，设计案 §0.1 已声明）；
  G5 锚来源白名单：manifest 每页锚 source ∈ {s0_endpoint_model.chip_audit,
     s0_endpoint_model.connector_audit, s0_method_net_join(...)}。
任一违例 → exit 1（L7）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
K2 = TOOLS.parent
STEP2 = (K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2")
OUT = STEP2 / "m13_v57_s1_a14_report.json"

FORBID_WINDOW = (r"REGION_WINDOWS|extract_region_pads|x_lo|x_hi|board_edge_x|"
                 r"corridor_bound_x|\[\d+\.\d+,\s*\d+\.\d+\].*window")
FORBID_MAX_X = r"p\[\"x\"\]\s*>\s*prev|max\(.*key=.*x|sorted\(.*reverse=True.*x"
FORBID_IMPORTS = (r"hs_route_model|solve_pipeline|channel_alloc|escape_landing|"
                  r"escape_allocator|route_input|column_book|escape_table|"
                  r"construction_fact")
S1_FILES = sorted(TOOLS.glob("p3_v57_s1_*.py"))
S1_FILES = [f for f in S1_FILES if "a11" not in f.name and
            "a13_gate" not in f.name and "a14" not in f.name]


def main() -> int:
    viol = []
    for f in S1_FILES:
        txt = f.read_text(encoding="utf-8")
        if re.search(FORBID_WINDOW, txt):
            viol.append({"rule": "G1_window", "file": f.name,
                         "hit": re.findall(FORBID_WINDOW, txt)[:3]})
        if re.search(FORBID_MAX_X, txt):
            viol.append({"rule": "G2_maxx", "file": f.name})
        if re.search(FORBID_IMPORTS, txt):
            viol.append({"rule": "G3_engine_import", "file": f.name})
        for off, ctx in [(m.start(), txt[max(0, m.start() - 80):m.start() + 40])
                         for m in re.finditer(r"k2_v4\.kicad_pcb", txt)]:
            if f.name != "p3_v57_s1_page_manifest.py":
                viol.append({"rule": "G4_board_read", "file": f.name,
                             "ctx": ctx.strip()[:60]})
    for f in S1_FILES:
        txt = f.read_text(encoding="utf-8")
        reads = [m.start() for m in re.finditer(r"BOARD\.read_text\(|open\(BOARD",
                                                txt)]
        for off in reads:
            fn_ctx = txt[:off].rfind("def ")
            fn = (txt[fn_ctx:off].split("(")[0].replace("def ", "")
                  if fn_ctx >= 0 else "<module>")
            if not (f.name == "p3_v57_s1_page_manifest.py" and
                    fn == "conn_pad_global"):
                viol.append({"rule": "G4b_board_read_call", "file": f.name,
                             "fn": fn})
    mfest = json.load(open(STEP2 / "m13_v57_s1_page_manifest.json"))
    ok_src = {"s0_endpoint_model.chip_audit", "s0_endpoint_model.connector_audit"}
    bad = []
    for pg in mfest["pages"]:
        for side in ("chip", "conn", "conn2"):
            for pol, a in pg["anchors"].get(side, {}).items():
                if not (a["source"] in ok_src or
                        a["source"].startswith("s0_method_net_join")):
                    bad.append({"page": pg["page_id"], "side": side,
                                "pol": pol, "source": a["source"]})
    if bad:
        viol.append({"rule": "G5_anchor_source", "hits": bad[:5]})

    report = {"artifact": "m13_v57_s1_a14_report",
              "predicate": "A1.4 单向性 grep 门（现状 S1 源码+manifest）",
              "files_checked": [f.name for f in S1_FILES],
              "violations": viol,
              "verdict": "PASS" if not viol else "FAIL"}
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    print(json.dumps({"files_checked": len(S1_FILES),
                      "violations": len(viol),
                      "verdict": report["verdict"]}, indent=1,
                      ensure_ascii=False))
    print("artifact:", OUT)
    return 0 if not viol else 1


if __name__ == "__main__":
    raise SystemExit(main())
