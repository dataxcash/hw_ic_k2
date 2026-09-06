#!/usr/bin/env python3
"""gen_c5_chip_expect_matrix.py — 生成 C5 芯片级核对期望矩阵（ECO 后网表核对断言底稿）。

背景：REVIEW_ADVERSARIAL_v26 C5 = DS320PR1601 ball→ASIC lane 映射核对。可核部分（真板
J3=0-3/J4=4-7）v27/v28 已核一致；芯片级因 DS320PR1601 网表未落地（ECO ⏳）不可核。
本脚本 = C5 前置准备：从 ds320pr1601_ballmap.json（354 球资产，die 级命名 A/B 端口 ×
PER/PET 列带 × lane × P/N）提取 K2 lanes 0-7 的 64 信号球全名，结合 L1 v2.0 冻结信号流
（A_PORT=host/J2、B_PORT=device/MCIO）生成**期望映射矩阵** → ECO 落地后一次对照核对。

性质（G3 证书边界）：非引擎、非芯片实测 —— 期望矩阵全部派生自已冻结文档 + 已验 ballmap
资产，不新增判断；真实映射以 ECO 后网表为准，若与期望冲突 → 停机对账（冲突即停机），
禁止本矩阵冒充实测。

用法：python3 gen_c5_chip_expect_matrix.py
输出：c5_chip_level_expect_matrix_v28.json（本目录，可复跑禁删）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BALLMAP = HERE / "ds320pr1601_ballmap.json"
OUT = HERE / "c5_chip_level_expect_matrix_v28.json"

# L1 v2.0 §信号流/穿越 + kb corridor_pair_ds320pr1601_dual_band structure 口径
PORT_ROLE = {
    "A": {"side": "host", "connector": "J2 (SlimSAS x8)", "nets": "PCIE_DN/UP0-7 (host 侧)"},
    "B": {"side": "device", "connector": "J3/J4 (MCIO x4+x4)", "nets": "DN_OUT0-7_MCIO / UP0-7 (J3=0-3, J4=4-7)"},
}
BAND_SPEC = {"A_PER": ("A", "PER"), "B_PET": ("B", "PET"),
             "A_PET": ("A", "PET"), "B_PER": ("B", "PER")}
LANES = list(range(8))  # K2 8-of-16 lane


def main() -> int:
    data = json.loads(BALLMAP.read_text(encoding="utf-8"))
    ballmap = data["ballmap"]
    pat = re.compile(r"^([AB])_(PER|PET)([PN])(\d+)$")

    by_band = {}
    for band, (port, _pet) in BAND_SPEC.items():
        balls = {}
        for b in ballmap:
            m = pat.match(b["signal"])
            if not m:
                continue
            p, pet, pn, lane = m.group(1), m.group(2), m.group(3), int(m.group(4))
            if p == port and pet == _pet and lane in LANES:
                balls.setdefault(lane, {})[pn] = b["name"]
        assert len(balls) == 8 and all(len(v) == 2 for v in balls.values()), band
        by_band[band] = balls

    total = sum(len(v) for band in by_band.values() for v in band.values())
    assert total == 64, f"expect 64 signal balls, got {total}"

    matrix = {
        "probe": "c5_chip_level_expect_matrix",
        "level": "alignment_prep (C5 前置准备, 路径 c)",
        "basis": [
            "REVIEW_ADVERSARIAL_v26 C5 (DS320PR1601 ball→ASIC lane 映射核对, 缺口登记)",
            "L1_TOPOLOGY_v2.0 §信号流向/穿越 (A_PORT=host J2 侧, B_PORT=device MCIO 侧; DN: J2→A→re-drive→B→MCIO; UP 反向; 穿越=板级 A 带 In2 东穿)",
            "ds320pr1601_ballmap.json (UltraLibrarian TI 354 球, die 级命名 A/B 端口×PER/PET 列带×lane×P/N)",
            "kb corridor_pair_ds320pr1601_dual_band v5 (provenance: TI SNLS683 Table 5-1 列带逐球解析 全 16 lane 一致)",
        ],
        "port_roles": PORT_ROLE,
        "lane_to_mcio": {"J3": [0, 1, 2, 3], "J4": [4, 5, 6, 7]},
        "refclk": "REFCLK0=J3/REFCLK1=J4 直通不经芯片 (无芯片球, L1 v2.0)",
        "expect_ball_by_band": {
            band: {str(l): {"P": v["P"], "N": v["N"]} for l, v in sorted(balls.items())}
            for band, balls in by_band.items()
        },
        "check_items_after_eco": [
            "ECO 网表: J2 host lanes 0-7 P/N ↔ A 端口球 (A_PER/A_PET 带) — 每 lane 2 球全接",
            "ECO 网表: J3(0-3)/J4(4-7) ↔ B 端口球 (B_PER/B_PET 带) — 与 v27/v28 板级核对衔接",
            "DN/UP 方向: redriver 内部 re-drive (A↔B); 网表接对 P/N/lane 即满足, 方向由芯片配置",
            "REFCLK0/1: 无芯片球, 直通 (断言网表无 REFCLK 接到 DS320PR1601)",
            "若 ECO 网表 A 端口实际接 MCIO (与 L1 A=host 冲突) → 冲突即停机, 回 L1/L2 对账, 禁运行时改判",
        ],
        "total_signal_balls": total,
        "engine_consistency": "64 球 = per_ball 引擎 signal_ball_count=64 (per_ball_escape_6L_report.json; v26/v27 FEASIBLE 同口径)",
        "caveat": "本矩阵 = 期望断言 (已冻结文档+已验资产派生), 非芯片实测; 真实映射以 ECO 后网表为唯一裁决源",
    }
    OUT.write_text(json.dumps(matrix, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.name}: total_balls={total} bands={list(by_band.keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
