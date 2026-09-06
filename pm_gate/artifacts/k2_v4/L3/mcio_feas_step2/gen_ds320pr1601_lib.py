#!/usr/bin/env python3
"""gen_ds320pr1601_lib.py — 生成 DS320PR1601 KiCad 封装 + 符号（scope-B ECO 前置资产）。

数据源（全部既有资产，零新造）：
  ds320pr1601_ballmap.json — UltraLibrarian TI 354 球 {name, signal, x_mm, y_mm}
  （die 级命名 A/B 端口×PER/PET 列带×lane×P/N，kb machine_ballmap_source 同源）

产出：
  1. footprint  DS320PR1601.kicad_mod（354 smd circle pads，name=球名，at=ballmap x/y mm）
     → <out>/ForgeOS.pretty/（真板 WQFN-64 所在库源目录）
  2. symbol     DS320PR1601.kicad_sym（354 pins：name=signal / number=球名 / 电气类型映射）
     → <out>/DS320PR1601.kicad_sym

性质：机械生成器（KiCad 10 s-expr 文本），非引擎非判定；footprint 由 pcbnew 加载验证，
symbol 由 KiCad s-expr 结构校验（eeschema 无 python API，最终由原理图 ECO 落地验证）。

用法：python3 gen_ds320pr1601_lib.py [--out DIR]
     默认 out = 本目录（脚本所在）；实际库落位由调用方指定（如 ForgeOS.pretty 上级）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
BALLMAP = HERE / "ds320pr1601_ballmap.json"

# L2 v2.0 冻结：NSMD Ø0.3 焊盘（0.6 名义 pitch，禁 via-in-pad）
PAD_D = 0.30
# 体包络（半尺寸）：package 22.9×9.0（L1 v2.0），中心 (0,0) 局部坐标
BODY_HX, BODY_HY = 4.5, 11.45


def _etype(sig: str) -> str:
    if sig == "GND" or sig == "VCC":
        return "power_in"
    if "N/C" in sig or sig.startswith("NC"):
        return "no_connect"
    if "ADDR" in sig:
        return "input"          # 地址/strap 选择引脚
    if sig.startswith(("A_", "B_")):
        return "bidirectional"  # PCIe 差分信号（redriver 双向）
    return "passive"            # RSVD 等


def gen_footprint(balls: list[dict]) -> str:
    lines = []
    lines.append('(footprint "DS320PR1601"')
    lines.append("	(version 20260206)")
    lines.append('	(generator "mcio_gen")')
    lines.append('	(generator_version "10.0")')
    lines.append('	(layer "F.Cu")')
    lines.append('	(property "Reference" "REF**"')
    lines.append("		(at 0 12.5 0)")
    lines.append('		(layer "F.SilkS")')
    lines.append(f'		(uuid "{uuid.uuid4()}")')
    lines.append("		(effects (font (size 1 1) (thickness 0.15)))")
    lines.append("	)")
    lines.append('	(property "Value" "DS320PR1601"')
    lines.append("		(at 0 -12.5 0)")
    lines.append('		(layer "F.Fab")')
    lines.append(f'		(uuid "{uuid.uuid4()}")')
    lines.append("		(effects (font (size 1 1) (thickness 0.15)))")
    lines.append("	)")
    lines.append("	(attr smd)")
    # F.Fab body
    fab = [(BODY_HX, BODY_HY), (-BODY_HX, BODY_HY), (-BODY_HX, -BODY_HY), (BODY_HX, -BODY_HY)]
    for (x1, y1), (x2, y2) in zip(fab, fab[1:] + fab[:1]):
        lines.append(f"	(fp_line (start {x1} {y1}) (end {x2} {y2}) (layer \"F.Fab\") (width 0.1) (uuid \"{uuid.uuid4()}\"))")
    # Courtyard
    cy = BODY_HY + 0.35
    cx = BODY_HX + 0.35
    cyr = [(cx, cy), (-cx, cy), (-cx, -cy), (cx, -cy)]
    for (x1, y1), (x2, y2) in zip(cyr, cyr[1:] + cyr[:1]):
        lines.append(f"	(fp_line (start {x1} {y1}) (end {x2} {y2}) (layer \"F.CrtYd\") (width 0.05) (uuid \"{uuid.uuid4()}\"))")
    # pin1 silk 标记（A1 球 = 最小 x/y 角）
    p1 = min(balls, key=lambda b: (b["x_mm"], b["y_mm"]))
    lines.append(f"	(fp_line (start {p1['x_mm']-0.4} {p1['y_mm']-0.4}) (end {p1['x_mm']+0.4} {p1['y_mm']-0.4}) (layer \"F.SilkS\") (width 0.1) (uuid \"{uuid.uuid4()}\"))")
    lines.append(f"	(fp_line (start {p1['x_mm']+0.4} {p1['y_mm']-0.4}) (end {p1['x_mm']+0.4} {p1['y_mm']+0.4}) (layer \"F.SilkS\") (width 0.1) (uuid \"{uuid.uuid4()}\"))")
    # pads
    for b in sorted(balls, key=lambda b: b["name"]):
        x, y = b["x_mm"], b["y_mm"]
        lines.append(f'	(pad "{b["name"]}" smd circle')
        lines.append(f"		(at {x} {y})")
        lines.append(f"		(size {PAD_D} {PAD_D})")
        lines.append('		(layers "F.Cu" "F.Paste" "F.Mask")')
        lines.append(f'		(uuid "{uuid.uuid4()}")')
        lines.append("	)")
    lines.append(")")
    return "\n".join(lines)


def gen_symbol(balls: list[dict]) -> str:
    pins = []
    for b in sorted(balls, key=lambda b: b["name"]):
        pins.append((b["name"], b["signal"], _etype(b["signal"])))
    # 摆位：分两侧（左 = angle 180 朝外右？约定：右 pins at +X angle 180？）——用 KiCad 惯例：
    # 右侧 pin at (X, y) angle 180（name 朝外），左侧 pin at (-X, y) angle 0。
    # 均分 354 pin 到 左/右；GND/VCC 靠上优先排（视觉可读性粗排，name/number 为网表核心）。
    pins_l = [p for p in pins if p[2] == "power_in"]
    pins_s = [p for p in pins if p[2] != "power_in"]
    # 左右均分（信号左、电源右会过长——电源 153 个占满一侧；改为按序交替均分）
    half = (len(pins) + 1) // 2
    left = pins[:half]
    right = pins[half:]
    YSTEP = 2.54
    LX = -17.0
    RX = 17.0
    out = []
    out.append('(symbol "DS320PR1601" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)')
    out.append('	(property "Reference" "U?" (at 0 0 0) (hide no) (effects (font (size 1.27 1.27))) (id 0))')
    out.append('	(property "Value" "DS320PR1601" (at 0 0 0) (hide no) (effects (font (size 1.27 1.27))) (id 1))')
    out.append('	(property "Footprint" "ForgeOS:DS320PR1601" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))) (id 2))')
    n_units = (len(pins) + 149) // 150   # 每 unit ≤150 pin，避免单 unit 过长
    out.append(f'	(symbol "DS320PR1601_0_1"')
    # body 估算
    per = (len(pins) + 1) // 2
    hbody = max(per * YSTEP / 2 + 10, 60)
    out.append(f'		(rectangle (start -9 -{hbody}) (end 9 {hbody}) (stroke (width 0.254) (type default)) (fill (type background)))')
    for i, (num, name, etype) in enumerate(left):
        y = (i - len(left) / 2) * YSTEP
        out.append(f'		(pin {etype} line (at {LX} {y} 0) (length 2.54) (name "{name}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
    for i, (num, name, etype) in enumerate(right):
        y = (i - len(right) / 2) * YSTEP
        out.append(f'		(pin {etype} line (at {RX} {y} 180) (length 2.54) (name "{name}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')
    out.append("	)")
    out.append(")")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE), help="输出目录（footprint 落 <out>/ForgeOS.pretty/，symbol 落 <out>/）")
    args = ap.parse_args()

    data = json.loads(BALLMAP.read_text(encoding="utf-8"))
    balls = data["ballmap"]
    assert len(balls) == 354

    outdir = Path(args.out)
    fp_dir = outdir / "ForgeOS.pretty"
    fp_dir.mkdir(parents=True, exist_ok=True)
    sym_path = outdir / "DS320PR1601.kicad_sym"

    (fp_dir / "DS320PR1601.kicad_mod").write_text(gen_footprint(balls), encoding="utf-8")
    (sym_path).write_text(gen_symbol(balls), encoding="utf-8")

    # 校验：s-expr 括号平衡
    for p in (fp_dir / "DS320PR1601.kicad_mod", sym_path):
        t = p.read_text(encoding="utf-8")
        bal = t.count("(") - t.count(")")
        print(f"wrote {p}  ({t.count(chr(10))} lines, paren_balance={bal})")
    print("footprint pads:", len(balls))
    ok = ((fp_dir / "DS320PR1601.kicad_mod").read_text(encoding="utf-8").count("(pad ") == 354
          and sym_path.read_text(encoding="utf-8").count("(pin ") == 354)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
