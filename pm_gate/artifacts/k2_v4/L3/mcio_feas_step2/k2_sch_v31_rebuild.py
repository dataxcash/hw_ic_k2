#!/usr/bin/env python3
"""k2_sch_v31_rebuild.py — k2_sch.yaml 真板对齐重建 (m13_v31, scope-B gaps A/D)

从 C5 期望矩阵 (v28 + _v30_scopeB_correction) + DS320PR1601.kicad_sym 逐球信号
重建 boards/k2_sch.yaml：
  * 移除 U3/U7 DS160PR810 域 (C17-C32/C49-C64/C65-C72/R4-R7/R9-R12/R17-R20/R22-R27)
  * 新增 DS320PR1601 354pin 符号 (name=signal, 重复信号 GND/N/C/VCC1-4 -> name=ball)
  * 64 差分网按修正后 C5 矩阵重连 (A_PER->PCIE_DN*, B_PET->PCIE_UP_OUT*_J2,
    A_PET->PCIE_DN_OUT*_MCIO, B_PER->PCIE_UP*; J3=lane0-3/J4=lane4-7)
  * P3V3 += U6 VCC1-4 30球 + PD_11-8/PD_15-12; GND += U6 152 GND球 + PD_3-0/PD_7-4 + strap 下端
  * 侧带 (gap A 用户裁决 2026-09-06): SDA/SCL->I2C2, MODE=L2(6.19k), ADDR L0/L0|L0/L1,
    15-8 全 L0, READ_EN_#/ALL_DONE# NC
  * 新 strap 电阻 R35-R39/R42-R45
用法: python3 k2_sch_v31_rebuild.py (输出 stdout 汇总 + 写 boards/k2_sch.yaml)
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
K2_ROOT = next(p for p in HERE.parents if (p / "boards" / "k2_sch.yaml").exists())
BOARDS = K2_ROOT / "boards"
OUT = BOARDS / "k2_sch.yaml"
MATRIX = HERE / "c5_chip_level_expect_matrix_v28.json"
SYMPINS = HERE / "ds320_symbol_pins.json"   # 由 kicad_sym 预生成 (deterministic)

REMOVED_REFS = (
    ["U3", "U7"]
    + [f"C{i}" for i in range(17, 33)]
    + [f"C{i}" for i in range(49, 65)]
    + [f"C{i}" for i in range(65, 73)]
    + ["R4", "R5", "R6", "R7", "R9", "R10", "R11", "R12",
       "R17", "R18", "R19", "R20", "R22", "R23", "R24", "R25", "R26", "R27"]
)

STRAPS = {  # ball: (signal, value)  -- 值 = TI Table7-3/MODE 电平->下拉电阻(E96 1%)
    "FF24": ("MODE", "6.19k"),      # MODE L2 = 6.225kohm ±10% target (E96 6.19k)
    "B23": ("A_ADDR0_7-0", "1k"),   # L0
    "G1": ("A_ADDR1_7-0", "1k"),    # L0
    "B25": ("B_ADDR0_7-0", "8.25k"),# L1
    "F34": ("B_ADDR1_7-0", "1k"),   # L0
    "FF5": ("A_ADDR0_15-8", "1k"),  # L0 (unused bank)
    "FJ3": ("A_ADDR1_15-8", "1k"),  # L0
    "FJ28": ("B_ADDR0_15-8", "1k"), # L0
    "FF30": ("B_ADDR1_15-8", "1k"), # L0
}
STRAP_REFS = {"FF24": "R35", "B23": "R36", "G1": "R37", "B25": "R38", "F34": "R39",
              "FF5": "R42", "FJ3": "R43", "FJ28": "R44", "FF30": "R45"}
STRAP_VAL_SYM = {"6.19k": "R_6K19", "1k": "R_1K", "8.25k": "R_8K25"}

# 新增 strap 电阻符号 (镜像既有 R_* 双引脚定义, 供 sheets/BOM 引用)
RES_SYM = {"R_6K19": {"body_width": 2.0, "pin_pitch": 2.54,
                      "pins": {"left": [["A", "1", "PASSIVE", "POWER_GND"],
                                        ["B", "2", "PASSIVE", "POWER_GND"]]}},
           "R_8K25": {"body_width": 2.0, "pin_pitch": 2.54,
                      "pins": {"left": [["A", "1", "PASSIVE", "POWER_GND"],
                                        ["B", "2", "PASSIVE", "POWER_GND"]]}}}


def main() -> int:
    d = yaml.safe_load((BOARDS / "k2_sch.yaml").read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    eb = matrix["expect_ball_by_band"]
    sp = json.loads(SYMPINS.read_text(encoding="utf-8"))
    pins = sp["pins"]
    ball_sig = {p["ball"]: p["signal"] for p in pins}
    ball_name = {p["ball"]: p["name"] for p in pins}

    # ── 0) 净符号集: 去 REDR_DS160PR810, 加 DS320PR1601 ──────────────
    syms = [s for s in d["symbols"] if s["name"] != "REDR_DS160PR810"]
    ET = {"input": "INPUT", "output": "OUTPUT", "bidirectional": "BIDIR",
          "power_in": "POWER_IN", "power_out": "POWER_OUT",
          "passive": "PASSIVE", "no_connect": "NC"}
    def _grp(sig: str, et: str) -> str:
        if sig[:2] in ("A_", "B_") and re.search(r"[PN]\d+$", sig):
            return "DIFF_PAIR_RX"
        if et in ("power_in", "power_out", "passive", "no_connect"):
            return "POWER_GND"
        return "SIDEBAND"
    right, left = [], []
    for p in pins:
        e = ET[p["etype"]]
        entry = [p["name"], p["ball"], e, _grp(p["signal"], p["etype"])]
        (left if e in ("POWER_IN", "POWER_OUT", "PASSIVE", "NC") else right).append(entry)
    syms.append({
        "name": "DS320PR1601", "ref_prefix": "U", "value": "DS320PR1601",
        "footprint": "ForgeOS:DS320PR1601",
        "body_width": 26.8, "pin_pitch": 2.54,
        "pins": {"right": right, "left": left},
    })
    for rn, rs in RES_SYM.items():
        if not any(s["name"] == rn for s in syms):
            syms.append({"name": rn, "ref_prefix": "R", "value": rn,
                         "footprint": "R_0402_1005Metric", **rs})
    d["symbols"] = syms

    # ── 1) nets: 删含 removed-part 的网 / 成员 ─────────────────────────
    nets = d["nets"]
    def ref_of(member: str) -> str:
        return member.split("/")[0].split("@")[0]
    for nm in list(nets):
        nets[nm] = [m for m in nets[nm] if ref_of(m) not in REMOVED_REFS]
        if not nets[nm]:
            del nets[nm]

    # ── 2) 64 差分网重连 (修正后 C5 矩阵) ──────────────────────────────
    def mcio_end(lane: int, side: str, pn: str) -> str:
        conn = "J3" if lane < 4 else "J4"
        return f"{conn}/{side.upper()}{lane % 4}_{pn}"
    for lane in range(8):
        L = str(lane)
        for band, tmpl, connside in (
                ("A_PER", "PCIE_DN{}_", "j2tx"),
                ("B_PET", "PCIE_UP_OUT{}_", "j2rx"),
                ("A_PET", "PCIE_DN_OUT{}_", "mcio_rx"),
                ("B_PER", "PCIE_UP{}_", "mcio_tx")):
            pball = eb[band][L]["P"]; nball = eb[band][L]["N"]
            # 极性: matrix P 对应信号 ...P{lane}
            sigP = ball_sig[pball]
            pn = "P" if sigP.endswith(f"P{lane}") else ("N")
            sigN = ball_sig[nball]
            # 构造精确 net 名 (真板/矩阵一致)
            if band == "A_PER":
                name_p, name_n = f"PCIE_DN{lane}_P", f"PCIE_DN{lane}_N"
                endp, endn = f"J2/TX{lane}_P", f"J2/TX{lane}_N"
            elif band == "B_PET":
                name_p, name_n = f"PCIE_UP_OUT{lane}_P_J2", f"PCIE_UP_OUT{lane}_N_J2"
                endp, endn = f"J2/RX{lane}_P", f"J2/RX{lane}_N"
            elif band == "A_PET":
                name_p, name_n = f"PCIE_DN_OUT{lane}_P_MCIO", f"PCIE_DN_OUT{lane}_N_MCIO"
                conn = "J3" if lane < 4 else "J4"
                endp, endn = f"{conn}/RX{lane % 4}_P", f"{conn}/RX{lane % 4}_N"
            else:  # B_PER
                name_p, name_n = f"PCIE_UP{lane}_P", f"PCIE_UP{lane}_N"
                conn = "J3" if lane < 4 else "J4"
                endp, endn = f"{conn}/TX{lane % 4}_P", f"{conn}/TX{lane % 4}_N"
            nets[name_p] = [endp, f"U6/{ball_name[pball]}"]
            nets[name_n] = [endn, f"U6/{ball_name[nball]}"]

    # ── 3) P3V3 / GND / 侧带 ──────────────────────────────────────────
    vcc_balls = [p["ball"] for p in pins if p["signal"].startswith("VCC")]
    gnd_balls = [p["ball"] for p in pins if p["signal"] == "GND"]
    nets["P3V3"] += [f"U6/{ball_name[b]}" for b in vcc_balls]
    nets["P3V3"] += ["U6/PD_11-8", "U6/PD_15-12"]          # 未用 lanes8-15 下电 (P3V3 high)
    nets["GND"] += [f"U6/{ball_name[b]}" for b in gnd_balls]
    nets["GND"] += ["U6/PD_3-0", "U6/PD_7-4"]              # lanes0-7 上电 (GND low)
    # SDA/SCL -> I2C2 (R33/R34 上拉已在位)
    nets.setdefault("I2C2_SDA", []).append("U6/SDA")
    nets.setdefault("I2C2_SCL", []).append("U6/SCL")
    # 5-level strap nets (ADDR/MODE): U6 pin + Rxx/A ; Rxx/B -> GND
    for ball, (sig, val) in STRAPS.items():
        r = STRAP_REFS[ball]
        nets[f"DS320_STRAP_{sig}"] = [f"U6/{sig}", f"{r}/A"]
        nets["GND"].append(f"{r}/B")
    # READ_EN_#/ALL_DONE# 悬空 (target 模式, 不接)
    # 移除冗余空网
    for nm in [n for n, m in nets.items() if not m]:
        del nets[nm]
    d["nets"] = nets

    # ── 4) sheets: 去 removed, J3/J4 上 Connectors, U6+strap 独立页 ────
    for sheet in d["sheets"]:
        sheet["placements"] = [pl for pl in sheet["placements"]
                               if pl.get("ref") not in REMOVED_REFS]
    # U6 未上网引脚 = NC (loader 防 dangling)
    wired = {m.split("/", 1)[1] for ms in nets.values() for m in ms
             if m.startswith("U6/")}
    u6_nc = sorted(p["name"] for p in pins if p["name"] not in wired)
    # Connectors 页并入 J3/J4
    conn_sheet = next(s for s in d["sheets"] if s["title"] == "Connectors")
    conn_refs = {pl.get("ref") for pl in conn_sheet["placements"]}
    for ref, sym in (("J3", "MCIO_4i"), ("J4", "MCIO_4i")):
        if ref not in conn_refs:
            conn_sheet["placements"].append({"ref": ref, "symbol": sym,
                                             "nc": ["SMB_CLK", "SMB_DATA",
                                                    "FLEXIO_0A", "CBL_PRES#"],
                                             "card": "2"})
    # 空 AC-coupling 页清除 -> 重建为 DS320 + 新 strap 页 (删旧两页)
    d["sheets"] = [s for s in d["sheets"]
                   if "AC-Coupling" not in s["title"]]
    strap_sheet = {
        "title": "ReDriver DS320PR1601 & Sideband Strap",
        "paper": "A2", "layout": "auto_grid", "columns": 1, "gap": 12.0,
        "placements": [{"ref": "U6", "symbol": "DS320PR1601", "nc": u6_nc, "card": "2"}]
        + [{"ref": STRAP_REFS[b], "symbol": STRAP_VAL_SYM[STRAPS[b][1]],
            "card": "2"} for b in STRAP_REFS],
    }
    # R_10K 存在性: 符号 R_10K 已定义则用之 (值不同仅文档, symbol 取既有 R_10K)
    d["sheets"].insert(1, strap_sheet)

    # ── 5) strap_intents: 新 DS320 侧带意图 (文档化) ──────────────────
    d["strap_intents"] = [
        {"ref": "U6", "pin": "MODE", "level": "L2 (6.225k target; R35 6.19k 1% -> GND)", "note": "SMBus/I2C target mode (TI SNLS683 MODE pin)"},
    ]
    for ball, (sig, val) in STRAPS.items():
        if sig == "MODE":
            continue
        lv = {"A_ADDR0_7-0": "L0(1k)", "A_ADDR1_7-0": "L0(1k)", "B_ADDR0_7-0": "L1(8.25k)",
              "B_ADDR1_7-0": "L0(1k)", "A_ADDR0_15-8": "L0(1k)", "A_ADDR1_15-8": "L0(1k)",
              "B_ADDR0_15-8": "L0(1k)", "B_ADDR1_15-8": "L0(1k)"}[sig]
        d["strap_intents"].append({"ref": "U6", "pin": sig, "level": lv,
                                   "note": f"SMBus addr strap {sig} -> {lv} to GND (Table 7-3)"})
    d["strap_intents"] += [
        {"ref": "U6", "pin": "PD_3-0", "level": "LOW(GND)", "note": "power up lanes0-3 (A+B)"},
        {"ref": "U6", "pin": "PD_7-4", "level": "LOW(GND)", "note": "power up lanes4-7 (A+B)"},
        {"ref": "U6", "pin": "PD_11-8", "level": "HIGH(P3V3)", "note": "power down unused lanes8-11"},
        {"ref": "U6", "pin": "PD_15-12", "level": "HIGH(P3V3)", "note": "power down unused lanes12-15"},
        {"ref": "U6", "pin": "SDA", "level": "-", "note": "SMBus data -> MCU I2C2_SDA (R34 pullup)"},
        {"ref": "U6", "pin": "SCL", "level": "-", "note": "SMBus clock -> MCU I2C2_SCL (R33 pullup)"},
        {"ref": "U6", "pin": "READ_EN_#", "level": "NC", "note": "unused in target mode (internal 1M pull-down)"},
        {"ref": "U6", "pin": "ALL_DONE#", "level": "NC", "note": "High-Z in target mode"},
    ]

    # ── 6) links: diff/单端 语义重连 ───────────────────────────────────
    d["links"] = [l for l in d["links"]
                  if not ((l.get("source") or [None])[0] in REMOVED_REFS
                          or (l.get("target") or [None])[0] in REMOVED_REFS
                          or any(v in REMOVED_REFS for v in (l.get("via") or [])))]
    diff_links = []
    for lane in range(8):
        diff_links += [
            {"id": f"PCIE_DN{lane}", "kind": "diff",
             "source": [f"J2", f"TX{lane}_P"], "target": ["U6", f"A_PERP{lane}"]},
            {"id": f"PCIE_UP_OUT{lane}", "kind": "diff",
             "source": ["U6", f"B_PETP{lane}"], "target": ["J2", f"RX{lane}_P"]},
        ]
        conn = "J3" if lane < 4 else "J4"
        sub = lane % 4
        diff_links += [
            {"id": f"PCIE_DN_OUT{lane}", "kind": "diff",
             "source": ["U6", f"A_PETP{lane}"], "target": [conn, f"RX{sub}_P"]},
            {"id": f"PCIE_UP{lane}", "kind": "diff",
             "source": [conn, f"TX{sub}_P"], "target": ["U6", f"B_PERP{lane}"]},
        ]
    d["links"] = diff_links + d["links"]

    # ── 写盘 ──────────────────────────────────────────────────────────
    OUT.write_text(yaml.dump(d, allow_unicode=True, sort_keys=False, width=200),
                   encoding="utf-8")
    n_nets = len(d["nets"])
    print(f"wrote {OUT} : symbols={len(d['symbols'])} sheets={len(d['sheets'])} "
          f"nets={n_nets} links={len(d['links'])} straps={len(d['strap_intents'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
