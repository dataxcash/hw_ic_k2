#!/usr/bin/env python3
"""K2 · P4 · J-8 密度/间距（v4）正负控驱动（只写 /tmp；仓库板/pro/判据原件不动）。

案：A 安装件（density 未启用）· B POS（control-v4）· C NEG-density（合成拥挤板）·
    D NEG-clearance（阈值 0.12 > 实达 0.100）· E STALE（它板测量）· F MISSING（缺测量）·
    G THRESHOLD-NULL（启用但未给阈值 ⇒ fail-closed）
用法：python3 run_controls_v4.py
"""
import json
import os
import subprocess
import sys

import yaml

CWD = "/home/fila/jqdDev_2025/ic_hw"
D = os.path.join(CWD, "k2/docs/drafts/p4-j8-density-clearance-v1")
V3D = os.path.join(CWD, "k2/docs/drafts/p4-j8-v3-measurement-v1")
TMP = "/tmp/opencode/dc"
K = os.path.join(CWD, "AppDir/usr/bin/python3.11")
BOARD = "k2/hw/k2_v4_8L.l5.kicad_pcb"
PRO = "k2/hw/k2_v4_8L.l5.kicad_pro"
NEG_BOARD = os.path.join(TMP, "neg-density.kicad_pcb")
NEG_REFS = ["R31", "R32", "R33", "R34", "R35", "R36", "R37", "R38"]


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=CWD, **kw)
    return r


def measure(tag, board):
    os.makedirs(TMP, exist_ok=True)
    arts = {"density": os.path.join(TMP, f"dc_{tag}.json"),
            "minclr": os.path.join(TMP, f"mc_{tag}.json"),
            "pwo": os.path.join(TMP, f"pwo_{tag}.json"),
            "v3": os.path.join(TMP, f"v3_{tag}.json")}
    if not all(os.path.exists(v) for v in arts.values()):
        sh([K, os.path.join(D, "measure_density_and_clearance.py"), "--board", board, "--json", arts["density"]])
        sh([K, os.path.join(D, "measure_min_clearance_drc.py"), "--board", board, "--pro", PRO,
            "--kicad-cli", "AppDir/bin/kicad-cli", "--work-dir", os.path.join(TMP, f"clr_{tag}"),
            "--thresholds", "0.100,0.105,0.110,0.150", "--json", arts["minclr"]])
        sh([K, os.path.join(V3D, "measure_pads_within_outline.py"), "--board", board, "--json", arts["pwo"]])
        sh([K, os.path.join(V3D, "measure_ref_plane_continuity.py"), "--board", board, "--json", arts["v3"]])
    return arts


def make_neg_board():
    """合成「密度超限」负控板：把 8 件小件搬到**实测最空**区域（4×2、3mm 间距）⇒ 仅密度超限，间距不破。
    中心 = 板内 2mm 步进网格上「到最近铜/走线距离」最大者（确定性）。"""
    if os.path.exists(NEG_BOARD):
        return
    code = r"""
import math, pcbnew
bd = pcbnew.LoadBoard('%s')
boxes = []
for f in bd.GetFootprints():
    for p in f.Pads():
        b = p.GetBoundingBox(); boxes.append((b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()))
for t in bd.GetTracks():
    b = t.GetBoundingBox(); boxes.append((b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()))
def dist(x, y, b):
    dx = max(b[0] - x, x - b[2], 0); dy = max(b[1] - y, y - b[3], 0)
    return math.hypot(dx, dy)
e = bd.GetBoardEdgesBoundingBox(); step = int(2e6); margin = int(6e6)
best = None
for x in range(e.GetLeft() + margin, e.GetRight() - margin + 1, step):
    if not (int(4.6e6) <= x %% int(10e6) <= int(5.4e6)):
        continue
    for y in range(e.GetTop() + margin, e.GetBottom() - margin + 1, step):
        if not (int(1.6e6) <= y %% int(10e6) <= int(8.4e6)):
            continue
        d = min(dist(x, y, b) for b in boxes)
        if best is None or d > best[0]:
            best = (d, x, y)
d, cx, cy = best
i = 0
for f in bd.GetFootprints():
    if f.GetReference() in %r:
        f.SetPosition(pcbnew.VECTOR2I(int(cx + (i %% 4 - 1.5) * 3e6), int(cy + (i // 4 - 0.5) * 3e6)))
        i += 1
pcbnew.SaveBoard('%s', bd)
print('neg cluster center mm', cx / 1e6, cy / 1e6, 'empty-to-copper mm', round(d / 1e6, 3))
""" % (BOARD, NEG_REFS, NEG_BOARD)
    r = sh([K, "-c", code])
    print(r.stdout.strip() or r.stderr[-400:])


def write_manifest(name, mutate):
    d = yaml.safe_load(open(os.path.join(D, "manifest.k2.control-v4.yaml")))
    mutate(d)
    p = os.path.join(TMP, name)
    yaml.safe_dump(d, open(p, "w"), allow_unicode=True)
    return p


def run(tag, board, manifest, arts):
    out = os.path.join(TMP, f"verdict-{tag}.json")
    cmd = ["python3", os.path.join(D, "adjudicate.draft-v4.py"), "--project", "k2", "--manifest", manifest,
           "--board", board, "--pro", PRO, "--nets", "k2/hw/data/k2_sch.errata-1.yaml",
           "--sch-dir", "k2/hw/sch", "--root", ".", "--drc-cli", "AppDir/bin/kicad-cli",
           "--drc-work-dir", os.path.join(TMP, f"drc-{tag}"), "--out", out]
    if arts:
        cmd += ["--density-json", arts["density"], "--min-clearance-json", arts["minclr"],
                "--pads-outline-json", arts["pwo"], "--v3-plane-json", arts["v3"]]
    r = sh(cmd)
    if not os.path.exists(out):
        return tag, "NO-VERDICT", (r.stdout[-300:] + r.stderr[-300:]), None
    v = json.load(open(out))
    det = {x["check"]: x for x in v["oks"] + v["fails"]}
    return tag, f"{v['n_pass']}P/{v['n_fail']}F", "", det


def main():
    repo = measure("repo", BOARD)
    make_neg_board()
    neg = measure("neg", NEG_BOARD)
    m_install = os.path.join(D, "manifest.k2.v4.yaml")
    m_ctrl = os.path.join(D, "manifest.k2.control-v4.yaml")
    m_clr = write_manifest("manifest.neg-clearance.yaml",
                           lambda d: d["thresholds"]["density_and_clearance"].update({"min_copper_clearance_mm": 0.12}))
    m_null = write_manifest("manifest.thresh-null.yaml",
                            lambda d: d["thresholds"].pop("density_and_clearance"))
    cases = [
        ("A-install", BOARD, m_install, repo),
        ("B-POS", BOARD, m_ctrl, repo),
        ("C-NEG-density", NEG_BOARD, m_ctrl, neg),
        ("D-NEG-clearance", BOARD, m_clr, repo),
        ("E-STALE", "k2/hw/k2_v4_8L.l4.kicad_pcb", m_ctrl, repo),
        ("F-MISSING", BOARD, m_ctrl, None),
        ("G-THRESH-NULL", BOARD, m_null, repo),
    ]
    print("| 案 | 板 | 整判 | density_and_clearance |")
    print("|---|---|---|---|")
    for tag, b, m, a in cases:
        t, res, err, det = run(tag, b, m, a)
        dc = det.get("density_and_clearance") if det else None
        cell = ("%s | %s" % ("OK" if dc["ok"] else "FAIL", dc["detail"][:150])) if dc else err[:150]
        print("| %s | %s | %s | %s |" % (t, os.path.basename(b), res, cell))
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
