#!/usr/bin/env python3
"""K2 · 原理图 refdes 标注现状探针（只读、确定性；用于 N-07 / F-12 侧核对）。

背景（闭环表 N-07 原文）：「原理图仍有 **7 个未标注 refdes**（`C?/D?/E?/J?/L?/R?/U?`）」。
本器把「实例未标注」与 `lib_symbols` 定义占位符**分开计数**（后者是 KiCad 正常内容，非缺陷）：
  ① 删除 `(lib_symbols …)` 子树（括号配平 + 字符串安全）后，数**实例** `(property "Reference" "X?")`；
  ② 统计实例已标注 refdes 集合并与**板上 refdes** 对比（可排除纯机械件 `H*`）；
  ③ 可选：导出 netlist 并统计其中含 `?` 的 ref 数（KiCad 自身口径）。

用法：
  AppDir/usr/bin/python3.11 k2/tools/k2_refdes_annotation_probe_v1.py \
      --sch-dir k2/hw/sch --board k2/hw/k2_v4_8L.l5.kicad_pcb [--kicad-cli AppDir/bin/kicad-cli] \
      [--netlist-out /tmp/opencode/n07/k2.net] [--json /tmp/opencode/n07/probe.json]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys

import pcbnew

REF_Q = re.compile(r'\(property "Reference" "([A-Z]+)\?"')
REF_N = re.compile(r'\(property "Reference" "([A-Z]+[0-9]+)"')


def strip_lib_symbols(txt: str) -> str:
    out, i, n = [], 0, len(txt)
    while i < n:
        if txt.startswith("(lib_symbols", i):
            j, depth, instr = i + 1, 1, False
            while j < n and depth > 0:
                ch = txt[j]
                if instr:
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == '"':
                        instr = False
                else:
                    if ch == '"':
                        instr = True
                    elif ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                j += 1
            i = j
            continue
        out.append(txt[i])
        i += 1
    return "".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sch-dir", default="k2/hw/sch")
    ap.add_argument("--board", default=None)
    ap.add_argument("--kicad-cli", default=None)
    ap.add_argument("--root-sch", default=None)
    ap.add_argument("--netlist-out", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    res = {"sch_dir": a.sch_dir, "files": [], "totals": {}}
    ann_all = set()
    for f in sorted(glob.glob(os.path.join(a.sch_dir, "*.kicad_sch"))):
        raw = open(f, encoding="utf-8").read()
        body = strip_lib_symbols(raw)
        inst_q = REF_Q.findall(body)
        inst_n = REF_N.findall(body)
        lib_q = len(REF_Q.findall(raw)) - len(inst_q)
        ann_all |= set(inst_n)
        res["files"].append({"file": os.path.basename(f), "instances_annotated": len(inst_n),
                             "instances_unannotated": len(inst_q),
                             "unannotated_prefixes": sorted(set(inst_q)),
                             "lib_symbols_placeholders": lib_q})
    res["totals"]["instances_annotated"] = sum(x["instances_annotated"] for x in res["files"])
    res["totals"]["instances_unannotated"] = sum(x["instances_unannotated"] for x in res["files"])
    res["totals"]["lib_symbols_placeholders"] = sum(x["lib_symbols_placeholders"] for x in res["files"])
    res["totals"]["distinct_unannotated_prefixes"] = sorted({p for x in res["files"]
                                                             for p in x["unannotated_prefixes"]})
    if a.board:
        bd = pcbnew.LoadBoard(a.board)
        board = {f.GetReference() for f in bd.GetFootprints()}
        mech = {r for r in board if r.startswith("H")}
        res["board"] = {"board": a.board, "n_refdes": len(board), "n_mechanical": len(mech),
                        "board_not_sch": sorted((board - mech) - ann_all),
                        "sch_not_board": sorted(ann_all - board)}
    if a.kicad_cli and a.root_sch and a.netlist_out:
        os.makedirs(os.path.dirname(a.netlist_out), exist_ok=True)
        r = subprocess.run([a.kicad_cli, "sch", "export", "netlist", a.root_sch,
                            "--format", "kicadsexpr", "--output", a.netlist_out],
                           capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(a.netlist_out):
            txt = open(a.netlist_out, encoding="utf-8").read()
            refs = re.findall(r'\(ref "([^"]+)"\)', txt)
            res["netlist"] = {"path": a.netlist_out, "n_ref_entries": len(refs),
                              "n_unannotated": sum(1 for x in refs if "?" in x)}
        else:
            res["netlist"] = {"error": (r.stdout + r.stderr)[-300:]}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
