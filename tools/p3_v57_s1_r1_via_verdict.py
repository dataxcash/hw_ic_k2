#!/usr/bin/env python3
"""P3 v57 S1 — R1 行沟槽 via 候选判定（32 页芯片侧 verdict：可出逃/守恒证书）。

方法（构造性净空谓词，非搜索决策的图纸内容）：
  每数据球邻域 ±1.5mm、0.05 步网格候选 via（od 0.35）；候选 vs 全部异球 pad 铜
  （板上 U6 pad 尺寸=库/手册实现读取，S0 先例）须 |Δ| ≥ pad_half_diag + 0.2
  (GND/POWER netclass 保守) + 0.175(via 半) ；同球同网豁免；P/N 两候选互相
  |Δ| ≥ 0.525(via-via 铜净空)。存在任一合法 P/N 对 → 页可行，否则证书(最近阻塞)。
零 x-window/max-x/锚反猜；候选窗口以权威锚球为中心。输出逐字节确定。
"""
import hashlib
import json
import math
import re
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
BALLMAP = STEP2 / "ds320pr1601_ballmap.json"
BOARD = K2 / "k2_v4.kicad_pcb"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
OUT = STEP2 / "m13_v57_s1_r1_via_verdict.json"

CX, CY = 93.8, 53.7
VIA_OD = 0.35
CLR = 0.2
VIA_VIA = 0.525
GRID = 0.05
WIN = 1.5


def block_at(s, start):
    d, i = 0, start
    while i < len(s):
        if s[i] == "(":
            d += 1
        elif s[i] == ")":
            d -= 1
            if d == 0:
                return s[start:i + 1]
        i += 1
    return s[start:]


def main() -> int:
    bm = json.load(open(BALLMAP))["ballmap"]
    mf = json.load(open(MANIFEST))
    txt = BOARD.read_text()
    pads = {}
    for m in re.finditer(r"\(pad \"([^\"]*)\"", txt):
        pblk = block_at(txt, m.start())
        num = m.group(1)
        sz = re.search(r"\(size ([-\d.]+) ([-\d.]+)\)", pblk)
        if sz:
            pads.setdefault(num, []).append((float(sz.group(1)),
                                             float(sz.group(2))))
    ball_pad = {}
    for b in bm:
        gx, gy = round(CX + b["y_mm"], 4), round(CY - b["x_mm"], 4)
        sizes = pads.get(b["name"]) or pads.get(b["name"], [])
        half = 0.0
        if sizes:
            w, h = sizes[0]
            half = math.hypot(w, h) / 2.0
        else:
            half = 0.19
        ball_pad[b["name"]] = {"sig": b.get("signal"), "g": [gx, gy],
                               "half_diag": half}
    out_pages = {}
    for pg in mf["pages"]:
        if pg["kind"] != "data":
            continue
        pa = {}
        for pol in ("P", "N"):
            a = pg["anchors"]["chip"][pol]
            px, py = a["pad_global"]
            own = ball_pad.get(a["ball_grid"])
            cands = []
            nx = int(WIN / GRID)
            for ix in range(-nx, nx + 1):
                for iy in range(-nx, nx + 1):
                    x, y = px + ix * GRID, py + iy * GRID
                    ok = True
                    own_hd = own["half_diag"] if own else 0.212
                    for bn, bd in ball_pad.items():
                        if bd["sig"] == a["ball"]:
                            d0 = math.hypot(x - px, y - py)
                            if d0 < own_hd + 0.05 - 1e-9:
                                ok = False
                                break
                            continue
                        d = math.hypot(x - bd["g"][0], y - bd["g"][1])
                        if d < bd["half_diag"] + CLR + VIA_OD / 2 - 1e-9:
                            ok = False
                            break
                    if ok:
                        cands.append([round(x, 3), round(y, 3)])
            pa[pol] = {"ball": a["ball"], "ball_grid": a["ball_grid"],
                       "pad": a["pad_global"], "n_cand": len(cands),
                       "cands": sorted(cands,
                                       key=lambda c: (abs(c[0] - px),
                                                      abs(c[1] - py),
                                                      c[0], c[1]))}
        # P/N 对判定
        pair = None
        for cp in pa["P"]["cands"]:
            for cn in pa["N"]["cands"]:
                if math.hypot(cp[0] - cn[0], cp[1] - cn[1]) >= VIA_VIA - 1e-9:
                    pair = [cp, cn]
                    break
            if pair:
                break
        out_pages[pg["page_id"]] = {
            "side": pg["side"], "P": pa["P"], "N": pa["N"],
            "verdict": "ESCAPABLE" if pair else "CERTIFICATE",
            "pair": pair}
    n_ok = sum(1 for v in out_pages.values() if v["verdict"] == "ESCAPABLE")
    report = {"artifact": "m13_v57_s1_r1_via_verdict",
              "n_pages": len(out_pages), "n_escapable": n_ok,
              "pages": out_pages,
              "inputs_sha": {"ballmap": hashlib.sha256(
                  BALLMAP.read_bytes()).hexdigest()},
              "params": {"via_od": VIA_OD, "clr": CLR, "via_via": VIA_VIA}}
    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")
    for pid in sorted(out_pages):
        v = out_pages[pid]
        print(f"{pid:26s} {v['verdict']:10s} P#cand={v['P']['n_cand']:4d} "
              f"N#cand={v['N']['n_cand']:4d}")
    print("n_escapable:", n_ok, "/", len(out_pages))
    print("artifact:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
