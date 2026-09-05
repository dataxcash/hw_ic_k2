#!/usr/bin/env python3
"""reproduce_ultralibrarian_ballmap.py — 从 Ultra Librarian TI 内嵌页提取 DS320PR1601
nfBGA-354 逐球 (x,y) mm 坐标资产（可复跑，禁删）。

来源：TI 产品页 (www.ti.com/product/DS320PR1601) 的 "CAD symbols, footprints & 3D models"
指向 Ultra Librarian TI 内嵌页（gpn=DS320PR1601&package=ZDG&pin=354），其封装预览为
SVG 矢量（basic/detailed-NFBGA354_ZDG_TEX.svg），焊盘 = 带精确 (x,y) 的 <rect class="pin">，
坐标单位为 mil（×0.0254 → mm）。这是 vendor-validated 机器可读几何（非 raster 图 / 非标签网格）。

用法：python3 reproduce_ultralibrarian_ballmap.py [--out <json>]
输出：ds320pr1601_ballmap.json（354 球 {name,x_mm,y_mm,signal}）
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

UL_DETAIL_SVG = ("https://static.ultralibrarian.com/part-previews/footprints/"
                 "5952071/detailed-NFBGA354_ZDG_TEX.svg")
MIL2MM = 0.0254


def fetch_svg(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_pins(svg: str) -> list[dict]:
    pat = re.compile(
        r'class="pin"[^>]*?transform="rotate\((-?[\d.]+),([-\d.]+),([-\d.]+)\)"'
        r'[^>]*?data-pin_bounding_rect=\s*"([^"]+)"[^>]*?data-pin_name="([^"]*)"',
        re.S)
    out = []
    for m in pat.finditer(svg):
        cx, cy, label, name = float(m.group(2)), float(m.group(3)), m.group(4), m.group(5)
        out.append({"name": label, "signal": name,
                    "x_mm": round(cx * MIL2MM, 4), "y_mm": round(cy * MIL2MM, 4)})
    return out


def _band(sig: str):
    for k in ("A_PER", "B_PET", "A_PET", "B_PER"):
        if sig.startswith(k):
            return k
    return None


def validate(pins: list[dict]) -> dict:
    labels = [p["name"] for p in pins]
    sig = [p for p in pins if _band(p["signal"])]
    gb = defaultdict(list)
    for p in sig:
        gb[_band(p["signal"])].append(p)
    xs = [p["x_mm"] for p in pins]
    ys = [p["y_mm"] for p in pins]
    band_info = {}
    for k in sorted(gb):
        band_info[k] = {"n": len(gb[k]),
                        "x_cols": sorted(set(round(p["x_mm"], 3) for p in gb[k]))}
    v = {
        "n_balls": len(pins),
        "unique_labels": len(set(labels)),
        "duplicate_labels": len(labels) - len(set(labels)),
        "signal_balls": len(sig),
        "band_cols": band_info,
        "array_x_mm": [round(min(xs), 3), round(max(xs), 3)],
        "array_y_mm": [round(min(ys), 3), round(max(ys), 3)],
        "body_target_mm": [8.89, 22.86],
    }
    return v


def main(argv=None) -> int:
    out = Path("ds320pr1601_ballmap.json")
    if argv:
        sys.argv = argv
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
    svg = fetch_svg(UL_DETAIL_SVG)
    pins = extract_pins(svg)
    v = validate(pins)
    asset = {
        "source": "UltraLibrarian TI-embedded (vendor.ultralibrarian.com/TI/embedded/"
                  "?gpn=DS320PR1601&package=ZDG&pin=354) SVG detailed-NFBGA354_ZDG_TEX",
        "package": "nfBGA-354 (ZDG) 22.89x8.9mm 0.6 TYP pitch non-uniform grouped "
                   "escape-optimized array (Intel PCIe5 retimer common footprint)",
        "unit": "SVG workspace units = mil (x0.0254 -> mm); pad 12mil~0.305mm, "
                "array ~7.88x21.94mm in 8.9x22.8 body",
        "validation": v,
        "ballmap": pins,
    }
    out.write_text(json.dumps(asset, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out} : {v['n_balls']} balls, {v['signal_balls']} signals, "
          f"bands={list(v['band_cols'].keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
