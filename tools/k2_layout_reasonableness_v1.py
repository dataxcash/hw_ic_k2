#!/usr/bin/env python3
"""k2_layout_reasonableness_v1.py --- **布局合理性常设闸（#K2-403 §二.B）**。

每窗**二值**：R1 主器件-流向对应 · R2 高低速分区 · R3 密度均衡 · R4 孔/边距/连接器对齐
· R5 无逆流长绕 · R6 无重叠。**机器可算者即时算**；**须渲染目视者显式标 `RENDER_REQUIRED`**
（双轨：机器 + 渲染），**不得**以"只注声称"代替（承 C20 纸闸禁）。

机算口径（**基线相对**，基准 = 冻结 l14）：
  R6 无重叠  : kicad-cli DRC `courtyards_overlap` 计数 不高于基线
  R3 密度均衡: `regen.density_quadrants` 的最挤象限面积占比 不高于基线 + 容差
  R4 孔/边距 : DRC `hole_clearance`/`edge_clearance`/`pth_inside_courtyard` 不高于基线
其余（R1/R2/R5）＝ **RENDER_REQUIRED**（渲染目视轨）。

CLI: python3 tools/k2_layout_reasonableness_v1.py --board <pcb> [--drc <json>] [--json-out P]
Exit 0 = PASS（机算行全过）· 1 = FAIL · 2 = 输入/环境错误。
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "hw", "k2_v4_8L.l14.kicad_pcb")
BASE_DRC = os.path.join(ROOT, "pm_gate/artifacts/k2_v4/L2/REROUTE_EXAM_REF_L14_DRC.json")
DENSITY_TOL = 0.02          # 密度容差（绝对百分点）


def _drc(board, out):
    cli = os.environ.get("EDA_ENG_CLI", "kicad-cli")
    r = subprocess.run([cli, "pcb", "drc", "--format", "json", "--severity-all", "-o", out, board],
                       capture_output=True, text=True, timeout=1800)
    return os.path.isfile(out)


def _classes(p):
    d = json.load(open(p, encoding="utf-8"))
    out = {}
    for v in d.get("violations", []):
        out[v.get("type")] = out.get(v.get("type"), 0) + 1
    return out


def _dens(board):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from eda_eng import regen
    d = regen.density_quadrants(board)
    a = d["quadrant_area_pct"]
    return {"quadrants": a, "max_pct": max(a.values())}


def check(board, drc=None, base=BASE, base_drc=BASE_DRC, work=None):
    work = work or "/tmp/opencode"
    os.makedirs(work, exist_ok=True)
    out = {"artifact": "k2_layout_reasonableness_v1", "board": board, "baseline": base, "rows": {}}
    bc, pc = _classes(base_drc), None
    if drc and os.path.isfile(drc):
        pc = _classes(drc)
    else:
        t = os.path.join(work, "lrr_drc.json")
        if not _drc(board, t):
            return dict(out, verdict="ERROR", reason="kicad-cli DRC failed")
        pc = _classes(t)
    bd, pd_ = _dens(base), _dens(board)
    rows = {
      "R6_no_overlap": {"machine": "courtyards_overlap <= baseline",
                        "base": bc.get("courtyards_overlap", 0), "now": pc.get("courtyards_overlap", 0)},
      "R4_hole_edge": {"machine": "hole_clearance+edge_clearance+pth_inside_courtyard <= baseline",
                       "base": sum(bc.get(k, 0) for k in ("hole_clearance", "edge_clearance", "pth_inside_courtyard")),
                       "now": sum(pc.get(k, 0) for k in ("hole_clearance", "edge_clearance", "pth_inside_courtyard"))},
      "R3_density_balance": {"machine": "max quadrant area%% <= baseline + %.2f" % DENSITY_TOL,
                             "base": round(bd["max_pct"], 4), "now": round(pd_["max_pct"], 4),
                             "quadrants": pd_["quadrants"]}}
    for k, v in rows.items():
        v["pass"] = v["now"] <= v["base"] + (DENSITY_TOL if k == "R3_density_balance" else 0)
    render = {k: "RENDER_REQUIRED" for k in ("R1_flow_correspondence", "R2_hs_ls_partition", "R5_no_reverse_detour")}
    verdict = "PASS" if all(v["pass"] for v in rows.values()) else "FAIL"
    return dict(out, rows=rows, render_rows=render, verdict=verdict,
                rule="#K2-403 sec.2.B: a standing binary gate - machine-computable rows are computed now; "
                     "visual rows are explicitly RENDER_REQUIRED (dual-track), never a bare claim.")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--drc", default=None)
    ap.add_argument("--json-out", default=None); ap.add_argument("--work", default=None)
    a = ap.parse_args(argv)
    r = check(a.board, a.drc, work=a.work)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.json_out:
        json.dump(r, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if r.get("verdict") == "PASS" else (2 if r.get("verdict") == "ERROR" else 1)


if __name__ == "__main__":
    sys.exit(main())
