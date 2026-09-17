#!/usr/bin/env python3
"""K2 · P4 · J-8「关键间距」真值测量：用 DRC 引擎 bracket 全板最小铜间距（**只出测量，无 verdict**）。

方法：在 `--work-dir`（默认 /tmp）复制板 + 同名 pro（T-8）+ `fp-lib-table`/`lib`，
**仅上调** `min_clearance` 与各 netclass `clearance` 到阈值 T，跑 `kicad-cli pcb drc`，
统计 `clearance` 违规数。0 违规的最大 T 即「实达最小间距 ≥ T」；随后第一个有违规的 T 给出上界
⇒ 真值落在 `[max_zero, first_violating]` 区间。**仓库板/pro 逐字节不动**。

用途：`density_and_clearance` 判定中的 `min_copper_clearance_mm` 证据（阈值归监理）。

用法：
  python3 measure_min_clearance_drc.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
      --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/dc/clr [--json out.json]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import Counter

from j8_dc_common import sha16

NAME = "K2CLR"


def setup_workdir(board, pro, work, clearance_mm):
    os.makedirs(work, exist_ok=True)
    bdst = os.path.join(work, NAME + ".kicad_pcb")
    shutil.copyfile(board, bdst)
    cfg = json.load(open(pro, encoding="utf-8"))
    rules = cfg["board"]["design_settings"].setdefault("rules", {})
    rules["min_clearance"] = clearance_mm
    for c in cfg.get("net_settings", {}).get("classes", []):
        c["clearance"] = clearance_mm
    pstd = os.path.join(work, NAME + ".kicad_pro")
    json.dump(cfg, open(pstd, "w"), indent=2)
    src = os.path.dirname(os.path.abspath(board))
    for f in ("fp-lib-table",):
        if os.path.exists(os.path.join(src, f)):
            shutil.copyfile(os.path.join(src, f), os.path.join(work, f))
    lib = os.path.join(src, "lib")
    if os.path.isdir(lib) and not os.path.isdir(os.path.join(work, "lib")):
        shutil.copytree(lib, os.path.join(work, "lib"))
    return bdst


def drc_clearance_violations(cli, work, bdst):
    out = os.path.join(work, "drc.json")
    subprocess.run([cli, "pcb", "drc", "--format", "json", "--severity-error",
                    "--severity-warning", "--output", out, bdst],
                   capture_output=True, text=True)
    if not os.path.exists(out):
        return None, None
    v = json.load(open(out, encoding="utf-8")).get("violations", [])
    cl = [x for x in v if x.get("type") == "clearance"]
    return len(cl), cl


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--pro", required=True)
    ap.add_argument("--kicad-cli", required=True)
    ap.add_argument("--work-dir", default="/tmp/opencode/dc/clr")
    ap.add_argument("--thresholds", default="0.100,0.105,0.110,0.120,0.150,0.200")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    ts = [float(x) for x in a.thresholds.split(",") if x.strip()]
    table, samples = [], None
    for t in ts:
        bdst = setup_workdir(a.board, a.pro, a.work_dir, t)
        n, cl = drc_clearance_violations(a.kicad_cli, a.work_dir, bdst)
        if n is None:
            print(f"[INFRA] DRC 未产出 JSON @ T={t}", file=sys.stderr)
            return 2
        table.append({"threshold_mm": t, "n_violations": n})
        if n > 0 and samples is None:
            samples = [{"description": x.get("description"), "items": [i.get("description") for i in x.get("items", [])]}
                       for x in cl[:3]]
    zero = [r["threshold_mm"] for r in table if r["n_violations"] == 0]
    pos = [r for r in table if r["n_violations"] > 0]
    res = {"check": "min_copper_clearance_drc_bracket",
           "board": os.path.abspath(a.board), "board_sha16": sha16(a.board),
           "method": f"kicad-cli pcb drc，仅上调 min_clearance/netclass clearance（{a.work_dir} 副本；仓库 pro 未动）",
           "table": table, "max_zero_violation_threshold_mm": max(zero) if zero else None,
           "first_violating_threshold_mm": min(r["threshold_mm"] for r in pos) if pos else None,
           "min_copper_clearance_mm_lower_bound": max(zero) if zero else None,
           "min_copper_clearance_mm_upper_bound": min(r["threshold_mm"] for r in pos) if pos else None,
           "tightest_samples": samples,
           "note": "测量件：不含 verdict 字段；真值区间由 DRC bracket 给出，应然阈值归监理"}
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(res, open(a.json, "w"), ensure_ascii=False, indent=1)
    print(f"[min_clearance_drc] board={os.path.basename(a.board)} sha16={res['board_sha16']}")
    for r in table:
        print(f"  T={r['threshold_mm']:.3f}mm ⇒ clearance 违规 {r['n_violations']}")
    print(f"  实达区间：[{res['min_copper_clearance_mm_lower_bound']}, {res['min_copper_clearance_mm_upper_bound']}] mm")
    if samples:
        print(f"  最紧样本：{samples[0]['items'] or samples[0]['description']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
