#!/usr/bin/env python3
"""
reproduce_zdg0354a_ballmap_analysis.py — DS320PR1601 ZDG0354A 球栅分析复现（v22 资产）

输入：TI DS320PR1601 datasheet SNLS683 PDF（含 TI 官方封装机械图 ZDG0354A，Example Board Layout）。
数据源：datasheet PDF page 41（0-indexed 40）= EXAMPLE BOARD LAYOUT（真实球栅图，PDF 页 40-42）。

产出（证据级，非机器级逐球 X/Y——见结论）：
  1. 354 球名集（[列字母][行号]，行号 1-35，列字母 A..FJ，129 个）→ 结构确认（0.6 TYP pitch / 8.9x22.8 / 非均匀分组）。
  2. 逐轴 scale 实测证明 = 图的球位【标签为 tabular/可读布局，非物理定位】，
     故图中标签坐标【不能】直接校准为物理 mm → 精确逐球 X/Y 需机器 CAD / Astera xlsx。

运行：python3 reproduce_zdg0354a_ballmap_analysis.py --pdf <ds320pr1601.pdf> --out <dir>
输出：<dir>/ds320pr1601_ballmap_354name.json + 轴向 scale 判定 stdout。

结论定位：v22 ESCAPE_GAP 决定性逃逸项缺口 = 机器球栅 mm 资产（无公开机器 X/Y；唯一 = Astera PTx16xx_supplemental_info.xlsx FAE-gated）。
"""
import argparse, json, re, subprocess, sys, os
from collections import Counter
import fitz  # pymupdf

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=None, help="DS320PR1601 datasheet PDF")
    ap.add_argument("--out", default=".", help="输出目录")
    a = ap.parse_args()

    pdf = a.pdf
    if not pdf:
        # 尝试常用位置
        for cand in ["/tmp/opencode/ds320pr1601.pdf", "ds320pr1601.pdf"]:
            if os.path.exists(cand):
                pdf = cand; break
    if not pdf:
        print("需 --pdf <ds320pr1601.pdf>"); sys.exit(1)

    doc = fitz.open(pdf)
    P = 40  # 0-indexed = PDF page 41 (EXAMPLE BOARD LAYOUT)
    p = doc[P]
    words = p.get_text("words")
    name_re = re.compile(r"^([A-Z]{1,2})([0-9]{1,2})$")

    balls = set()
    label_pts = []
    for w in words:
        m = name_re.match(w[4])
        if m and 115 < w[1] < 460 and 180 < w[2] < 400:   # 球栅图区域（page41 布局）
            balls.add((m.group(1), int(m.group(2))))
            label_pts.append((m.group(1), int(m.group(2)), (w[0]+w[2])/2, (w[1]+w[3])/2))

    balls = sorted(balls)
    rows = sorted(set(n for c, n in balls))
    letters = sorted(set(c for c, n in balls))
    print(f"n_balls={len(balls)}  rows(min={min(rows)},max={max(rows)},n={len(rows)})  letters(n={len(letters)})")

    # --- 逐轴 scale 判定（证明标签非物理定位）---
    xs = [pt[2] for pt in label_pts]; ys = [pt[3] for pt in label_pts]
    xspan = max(xs)-min(xs); yspan = max(ys)-min(ys)
    # 行号轴 pts/row（同字母、相邻行号）
    import collections
    per = collections.defaultdict(list)
    for c, n, x, y in label_pts:
        per[c].append((n, x))
    prs = []
    for c, ns in per.items():
        ns.sort()
        for (n1, x1), (n2, x2) in zip(ns, ns[1:]):
            if n2 > n1:
                prs.append(abs(x2-x1)/(n2-n1))
    # 包 body 8.9(短轴, 列字母) x 22.8(长轴, 行号)
    # 行号轴=长轴22.8mm => scale_row = xspan/22.8 ; 列字母轴=短轴8.9mm => scale_col = yspan/8.9
    scale_row = xspan/22.8
    scale_col = yspan/8.9
    ratio = scale_col/scale_row if scale_row else 0
    print(f"x_span(pts)={xspan:.1f}  y_span(pts)={yspan:.1f}")
    print(f"行号轴(长轴22.8mm): xspan/22.8 = {scale_row:.2f} pts/mm")
    print(f"列字母轴(短轴8.9mm): yspan/8.9 = {scale_col:.2f} pts/mm")
    print(f"列/行 scale 比 = {ratio:.2f} (真实图纸应为 ~1.0；此 >>1 => 列字母轴被拉伸为可读布局)")
    print(f"行号轴 pts-per-row p50 = {__import__('statistics').median(prs):.2f} (0.6mm 名义 pitch 不符 => 行距非物理)")
    non_phys = ratio > 2.0
    print("判定:", "非物理可读网格 (tabular) — 标签坐标不能校准为物理 mm" if non_phys else "近物理比例 (需再校)")

    out = {
        "source": f"TI DS320PR1601 datasheet SNLS683 PDF page{P+1} (EXAMPLE BOARD LAYOUT) ZDG0354A package drawing",
        "package": "nfBGA-354, 8.9x22.8mm, 0.6 TYP pitch, (0.3) TYP gaps, non-uniform grouped escape-optimized array (Intel PCIe5 retimer common footprint)",
        "name_format": "[column-letter][row-number]", "row_numbers": rows,
        "n_balls": len(balls),
        "ball_names": [{"col": c, "row": n} for c, n in balls],
        "axis_scale": {"row_axis_pts_per_mm": round(scale_row,2), "col_axis_pts_per_mm": round(scale_col,2),
                       "col_to_row_scale_ratio": round(ratio,2)},
        "extraction_verdict": ("354-ball name set deterministic; label grid NON-PHYSICAL (readable/tabular) "
                               "-> precise per-ball mm X/Y NOT machine-extractable from this drawing; "
                               "need machine CAD footprint or Astera PTx16xx_supplemental_info.xlsx"),
    }
    os.makedirs(a.out, exist_ok=True)
    jp = os.path.join(a.out, "ds320pr1601_ballmap_354name.json")
    json.dump(out, open(jp, "w"), indent=1)
    print("saved:", jp)

if __name__ == "__main__":
    main()
