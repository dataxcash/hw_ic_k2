#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""reproduce_k2_sch_v31_parity.py — k2_sch.yaml (v31) 网表 vs 真板 U6 逐球 parity (gap D)

断言: yaml U6 每球网名 == 真板 k2_v4.kicad_pcb U6 pad (by pad number=ball) 网名。
板已物理接线子集 = 64 信号 + 30 VCC(P3V3) + 152 GND；侧带 17 球 (gap A 已裁决)
在 sch 侧已连网但真板物理未接 -> 单独清单, 不参与 parity 断言 (登记待物理 ECO)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pcbnew  # noqa: F401  (bare system python lacks this; run under AppDir python)

HERE = Path(__file__).resolve().parent
K2 = next(p for p in HERE.parents if (p / "boards" / "k2_sch.yaml").exists())
YAML = K2 / "boards" / "k2_sch.yaml"
BOARD = K2 / "k2_v4.kicad_pcb"
SYMPINS = HERE / "ds320_symbol_pins.json"

sys.path.insert(0, str(next(p for p in HERE.parents if (p / ".gitmodules").exists()) / "_shared"))
from schlib.loader.yamlloader import load_board_spec  # noqa: E402

SIDEBAND = ["SDA", "SCL", "A_ADDR0_7-0", "A_ADDR1_7-0", "B_ADDR0_7-0", "B_ADDR1_7-0",
            "A_ADDR0_15-8", "A_ADDR1_15-8", "B_ADDR0_15-8", "B_ADDR1_15-8",
            "PD_3-0", "PD_7-4", "PD_11-8", "PD_15-12", "MODE", "READ_EN_#", "ALL_DONE#"]


def main() -> int:
    spec = load_board_spec(str(YAML))
    name2ball = {p["name"]: p["ball"] for p in json.loads(SYMPINS.read_text())["pins"]}
    # yaml: ball -> net
    yball = {}
    for n in spec["nets"]:
        for ref, pin in n.pins:
            if ref == "U6" and pin in name2ball:
                yball[name2ball[pin]] = n.name
    # 板: pad number(=ball) -> netname
    bd = pcbnew.LoadBoard(str(BOARD))
    u6 = [fp for fp in bd.GetFootprints() if fp.GetReference() == "U6"][0]
    bball = {p.GetNumber(): p.GetNetname() for p in u6.Pads()}
    fails, checked = [], 0
    phys_balls = [b for b, n in bball.items() if n != ""]
    for b in phys_balls:
        checked += 1
        if b not in yball:
            fails.append(f"board-wired ball {b} ({bball[b]}) missing in yaml")
        elif yball[b] != bball[b]:
            fails.append(f"ball {b}: board={bball[b]} yaml={yball[b]}")
    # yaml-only sideband sanity: SDA/SCL->I2C2, straps wired, PD mapped, MODE strap; READ_EN_#/ALL_DONE# NC
    nc_ok = all(name2ball[s] not in yball for s in ("READ_EN_#", "ALL_DONE#"))
    sb_need = [s for s in SIDEBAND if s not in ("READ_EN_#", "ALL_DONE#")]
    sb_ok = nc_ok and all(name2ball[s] in yball and yball[name2ball[s]] != "" for s in sb_need)
    exp_sb = {s: yball.get(name2ball[s]) for s in SIDEBAND}
    # counts
    from collections import Counter
    yn = Counter(yball.values())
    bn = Counter(bball.values())
    print(f"PARITY: {checked} board-wired balls checked, fails={len(fails)}")
    for f in fails[:20]:
        print("  FAIL", f)
    print("board netcount:", dict(bn))
    print("yaml  netcount:", {k: v for k, v in yn.items() if v < 200})
    print("sideband yaml nets:", exp_sb)
    print("RESULT:", "PASS" if not fails and sb_ok else "FAIL")
    return 0 if not fails and sb_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
