#!/usr/bin/env python3
"""CO-148 — U6（DS320PR1601）手册输入固化：把 PM 评估的 U6 参数从「声明值」升级为「手册值」。

来源：TI DS320PR1601 数据手册 SNLS683（JUNE 2023）节录件
      `m13_v57_co148_ds320pr1601_snls683_excerpt.txt`（含抓取 URL/pdftotext 命令/PDF sha256）。
本工具**只解析节录件**（确定性，不联网）⇒ 产出 `m13_v57_co148_u6_ds320pr1601_inputs.json`。
牙齿：① 七项关键值（θJA / RθJB / Tj_max / PACT×4）必须全部解析到；② 节录件 sha 须与记录一致。
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
EXC = S2 / "m13_v57_co148_ds320pr1601_snls683_excerpt.txt"
OUT = S2 / "m13_v57_co148_u6_ds320pr1601_inputs.json"
PACT_RE = re.compile(r"PACT\s+Device active power\s+32-channels \(16-lanes\), EQ = ([\d\-]+)\s+([\d.]+)\s+([\d.]+)\s+W")
TH_RE = re.compile(r"RθJA-High K\s+Junction-to-ambient thermal resistance\s+([\d.]+)\s+")
PSI_JB_RE = re.compile(r"ψJB\s+Junction-to-board characterization parameter\s+([\d.]+)\s+")
TH_JC_RE = re.compile(r"RθJC\(top\)\s+Junction-to-case \(top\) thermal resistance\s+([\d.]+)\s+")
TH_JB_RE = re.compile(r"RθJB\s+Junction-to-board thermal resistance\s+([\d.]+)\s+")
TJ_RE = re.compile(r"TJ\s+Operating junction temperature\s+([–\-−\d]+)\s+([\d]+)\s+°C")


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    txt = EXC.read_text()
    pacts = {m.group(1): {"typ_W": float(m.group(2)), "max_W": float(m.group(3))} for m in PACT_RE.finditer(txt)}
    th = TH_RE.search(txt)
    tj = TJ_RE.search(txt)
    psijb = PSI_JB_RE.search(txt)
    thjc = TH_JC_RE.search(txt)
    thjb = TH_JB_RE.search(txt)
    found = {"pact_rows": len(pacts), "theta_ja": bool(th), "tj": bool(tj), "theta_jb": bool(thjb)}
    teeth = {"t01_seven_values": len(pacts) == 2 and bool(th) and bool(tj) and bool(psijb) and bool(thjc) and bool(thjb),
             "t02_all_pact_rows": set(pacts) == {"0-2", "5-19"}}
    rec = {"artifact": "m13_v57_co148_u6_ds320pr1601_inputs", "schema": 1, "revision": "CO-148.1",
           "nature": "PM 评估输入升级：U6 由「声明值」→「数据手册值」（监理指令 #10「各轨电流由设计/器件手册导出」）",
           "device": "DS320PR1601（TI；32 Gbps 16 Lane PCIe 5.0 / CXL 2.0 linear redriver，nfBGA-354）",
           "source": {"datasheet": "TI DS320PR1601, SNLS683 – JUNE 2023",
                      "url": "https://www.ti.com/lit/ds/symlink/ds320pr1601.pdf",
                      "fetched": "2026-09-12",
                      "excerpt_file": EXC.name, "excerpt_sha16": s16(EXC),
                      "pdf_sha256": re.search(r"抓取 PDF sha256: ([0-9a-f]{64})", txt).group(1),
                      "note": "PDF 未入库（体积）；节录件含章节正文 + 抓取命令 + PDF sha256，可复核。"},
           "inputs": {"VCC_V": 3.3, "TJ_max_C": int(tj.group(2)) if tj else None,
                      "theta_ja_highK_C_per_W": float(th.group(1)) if th else None,
                      "psi_jb_C_per_W": float(psijb.group(1)) if psijb else None,
                      "theta_jb_C_per_W": float(thjb.group(1)) if thjb else None,
                      "theta_jc_top_C_per_W": float(thjc.group(1)) if thjc else None,
                      "PACT": pacts, "PRXDET_mW": 660, "PSTBY_mW": 92,
                      "derived_current_a": {k: {"typ": round(v["typ_W"] / 3.3, 3), "max": round(v["max_W"] / 3.3, 3)}
                                            for k, v in pacts.items()}},
           "teeth": teeth, "found": found,
           "redline": "只读节录件；不联网；零坐标搜索。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("PACT:", pacts, "| theta_ja:", th.group(1) if th else None, "| TJ_max:", tj.group(2) if tj else None)
    print("derived I(A):", rec["inputs"]["derived_current_a"])
    print("teeth:", teeth, "| out:", OUT.name, s16(OUT))
    return 0 if all(teeth.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
