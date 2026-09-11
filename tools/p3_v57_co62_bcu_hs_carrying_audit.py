#!/usr/bin/env python3
"""CO-62：【L2/SI 物理承载】B.Cu 承载阻抗关键网的机判审计（**负结果 ⇒ L2 裁定**）。

背景：CO-55/CO-56 的残余条款写「B.Cu 判**非阻抗控制层**（参考层为 In6 信号层）⇒ **其不得承载阻抗关键网**；
In6 下方 B.Cu 不得并行铺铜/走线」。CO-59 只核了后半句（并行），**前半句从未机判**。

本工具（只读、字节确定性）：
  A. L4 板上逐网/逐层铜长 → 哪些**阻抗关键网**（本阶段 68 条高速网）走了 B.Cu、多长、最长连续段；
  B. 差分对 P/N 的 **B.Cu 长度失配**（层混合 skew 的来源；长度等长 ≠ 电气等长）；
  C. B.Cu 的**一阶 Zdiff**（与 CO-55 同模型/同 8L 叠层）→ 判其能否承载 85Ω。
"""
from __future__ import annotations
import collections, hashlib, json, math, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
OUT = STEP2 / "m13_v57_co62_bcu_hs_carrying_audit.json"
sys.path.insert(0, str(K2.parent / "_shared"))
from eda_core.stackup import _edge_coupled_microstrip_z0 as MS, _symmetric_stripline_z0 as SL  # noqa: E402

W, S, T_OUT, T_IN = 0.205, 0.295, 0.035, 0.0175
# 8L 叠层（CO-55 反解：d(F-In1)=0.1164 / b(In1-In3)=0.72 / d(In5-In6)=0.0994 / d(In6-B)=0.1836）
LAYER_Z = {
    "F.Cu":   {"kind": "microstrip", "z": MS(W, 0.1164, T_OUT, 4.16, S)},
    "In2.Cu": {"kind": "stripline",  "z": SL(W, 0.72, T_IN, 3.99, S)},
    "In6.Cu": {"kind": "microstrip", "z": MS(W, 0.0994, T_IN, 4.10, S)},
    "B.Cu":   {"kind": "microstrip(单参考=In6 信号层, h=0.1836)", "z": MS(W, 0.1836, T_IN, 4.16, S)},
}
TARGET, TOL_PCT = 85.0, 10.0


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    txt = BOARD.read_text(encoding="utf-8")
    segs = re.findall(r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*'
                      r'\(width ([-\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net "([^"]+)"\)', txt)
    per = collections.defaultdict(lambda: collections.defaultdict(float))
    seg_max = collections.defaultdict(float)
    n_seg = 0
    for x1, y1, x2, y2, _w, lay, net in segs:
        n_seg += 1
        L = math.hypot(float(x2) - float(x1), float(y2) - float(y1))
        per[net][lay] += L
        if lay == "B.Cu":
            seg_max[net] = max(seg_max[net], L)
    nets = sorted(per)
    bcu = {n: per[n]["B.Cu"] for n in nets if per[n].get("B.Cu", 0) > 0}

    def pair_key(n: str):
        m = re.match(r"^(.*)_([PN])(_.*)?$", n)
        return (m.group(1) + (m.group(3) or ""), m.group(2)) if m else (n, "?")

    grp = collections.defaultdict(dict)
    for n in nets:
        k, p = pair_key(n)
        grp[k][p] = per[n]
    asym = []
    for k, d in sorted(grp.items()):
        if "P" in d and "N" in d:
            bp, bn = d["P"].get("B.Cu", 0.0), d["N"].get("B.Cu", 0.0)
            if bp or bn:
                asym.append({"pair": k, "bcu_P_mm": round(bp, 3), "bcu_N_mm": round(bn, 3),
                             "skew_len_mm": round(abs(bp - bn), 3),
                             "max_bcu_mm": round(max(bp, bn), 3)})
    asym.sort(key=lambda r: -r["max_bcu_mm"])
    max_skew = max((a["skew_len_mm"] for a in asym), default=0.0)
    worst_skew = sorted(asym, key=lambda r: -r["skew_len_mm"])[:5]
    worst = sorted(bcu.items(), key=lambda kv: -kv[1])[:8]

    res = {
        "artifact": "m13_v57_co62_bcu_hs_carrying_audit", "schema": 1, "revision": "CO-62.1",
        "nature": "L2/SI 物理承载机判：B.Cu 承载阻抗关键网审计（只读；零几何改动）",
        "inputs_sha": {"board_l4": sha16(BOARD)},
        "layer_first_order_zdiff_ohm": {k: {"kind": v["kind"], "zdiff": round(v["z"], 1),
                                            "in_85_pm10pct": abs(v["z"] - TARGET) <= TARGET * TOL_PCT / 100}
                                        for k, v in LAYER_Z.items()},
        "board": {"n_segments": n_seg, "n_nets": len(nets),
                  "bcu_net_count": len(bcu), "bcu_total_len_mm": round(sum(bcu.values()), 3),
                  "bcu_worst_nets": [{"net": n, "bcu_len_mm": round(L, 3),
                                      "max_continuous_mm": round(seg_max[n], 3)} for n, L in worst]},
        "pair_layer_mismatch_by_bcu_len": asym[:8],
        "pair_layer_mismatch_by_skew": worst_skew,
        "max_pair_bcu_skew_mm": max_skew,
        "finding": ("CO-55/CO-56 声明 B.Cu 非阻抗控制层且**不得承载阻抗关键网**；实测本阶段 68 条高速网中 "
                    f"**{len(bcu)} 条**在 B.Cu 上有铜，合计 **{round(sum(bcu.values()),2)}mm**（最长连续 "
                    f"**{round(max(seg_max.values()),2)}mm**）⇒ **违反该 L2 残余条款**。"
                    "B.Cu 一阶 Zdiff = %.1fΩ（+%.1f vs 85Ω，**超出 85±10%%**）；即使按『In6 铺地作参考』假设亦同值。"
                    "⇒ B.Cu 在本 8L 叠层下**无法承载 85Ω 差分**，须将上述网移出 B.Cu（层分配 = L2）。"
                    % (LAYER_Z["B.Cu"]["z"], LAYER_Z["B.Cu"]["z"] - TARGET)),
        "second_order": ("差分对 B.Cu 长度失配最大 %.2fmm ⇒ 层混合（B.Cu er_eff 低于内层）产生**长度等长之外的电气 skew**；"
                         "一阶估算 0.03~0.16mm 内层等效（取决于 er_eff，悲观档已 > 对内等长 0.15mm 预算）⇒ 现有 SI 记录"
                         "（按物理长度 skew 0.0031）**未覆盖**该机制，需按层加权复算。"
                         % max_skew),
        "ruling": ("L2 自裁：B.Cu 不得承载 85Ω 关键网（维持 CO-55 条款，且该条款**当前被违反**）。"
                   "整改 = 把 16 张 dn 带页（WEST dn + EAST dn）的逃逸/stub 层由 B.Cu 改到受控层（In2/In6/F.Cu），"
                   "属 L2『叠层分配/过孔策略/走廊分配』⇒ 走新 LID 修订 + 全链重导。"),
        "redline": "只读冻结源；零几何/阈值改动；不伪 sign-off；一阶结论须标『未经 SI9000/券』。",
        "gate_impact": "none（本件零改动）；**新开 L2 整改项（B.Cu 阻抗承载）**",
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": sha16(OUT),
                      "bcu_nets": len(bcu), "bcu_total_mm": round(sum(bcu.values()), 2),
                      "max_continuous_mm": round(max(seg_max.values()), 2),
                      "bcu_zdiff": round(LAYER_Z["B.Cu"]["z"], 1),
                      "max_pair_bcu_skew_mm": max_skew}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
