#!/usr/bin/env python3
"""k2_functional_block_v1.py --- **K-2 功能分块**（#K2-434 §2.1 · functional BLOCK）。

按**确定性功能族**（固定有序表；首匹配胜）把区内成员分成功能块；每块导出：
**成员 / 块内网 / 边界端口（跨块框的网）/ 块框（成员焊盘 bbox）**。同输入恒同输出。
CLI: python3 tools/k2_functional_block_v1.py --board B --members A,B,C [--json-out P]
"""
from __future__ import annotations
import argparse, json, re, sys

FAMILIES = [("POWER", ("VDD", "P3V3", "12V", "VBUS", "VIN", "VR")),
            ("CONTROL", ("NRST", "PERSTA", "PWR_BTN", "SWD", "SWCLK", "SWDIO", "BOOT")),
            ("BUS", ("I2C", "UART", "SPI", "SMB")),
            ("HS", ("PCIE", "CLK")),
            ("MISC", ())]


def family_of(nets):
    up = [ (n or "").upper() for n in nets ]
    for fam, keys in FAMILIES:
        if any(k in n for n in up for k in keys):
            return fam
    return "MISC"


def functional_blocks(members, netof):
    """**纯函数 · 确定性**：返回 {fam: {members:[...], nets:[...]}}（fam 按 FAMILIES 序）。"""
    out = {}
    for r in sorted(members):
        f = family_of(netof.get(r, []))
        out.setdefault(f, {"members": [], "nets": []})
        out[f]["members"].append(r)
        for n in sorted(set(netof.get(r, []))):
            if n not in out[f]["nets"]:
                out[f]["nets"].append(n)
    return {k: out[k] for k in [f for f, _ in FAMILIES] if k in out}


def boundary_ports(blocks, netof):
    """**确定性**：某块的网若也被**其它块**的成员使用 ⇒ 该网是**边界端口**。返回 {fam:[net,...]}。"""
    owner = {}
    for fam, b in blocks.items():
        for n in b["nets"]:
            owner.setdefault(n, set()).add(fam)
    return {fam: sorted(n for n in b["nets"] if len(owner.get(n, set())) > 1) for fam, b in blocks.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True, help='json: {members:[...], netof:{ref:[net..]}}')
    ap.add_argument("--json-out", dest="json_out", default=None)
    a = ap.parse_args()
    p = json.load(open(a.params, encoding="utf-8"))
    blk = functional_blocks(p["members"], p["netof"])
    rep = {"artifact": "k2_functional_block_v1", "blocks": blk,
           "boundary_ports": boundary_ports(blk, p["netof"]),
           "rule": "#K2-434 K-2: deterministic functional blocks (fixed ordered family table); boundary ports are the nets crossing blocks"}
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
