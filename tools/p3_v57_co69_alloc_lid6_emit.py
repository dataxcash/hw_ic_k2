#!/usr/bin/env python3
"""CO-69：【L2 引擎 bump 配套】CO16-ALLOC.7 —— stub 层随 LID REV6 由 In6.Cu 迁至 In5.Cu。

方案(a)（CO-67/CO-68）把 In6.Cu 由信号层改为 GND 平面、In5.Cu 由平面改为信号层。
CO16 通道分配工件（CO16-ALLOC.5）内 4 处 `stub_layer="In6.Cu"` 是**引擎消费的物理层名** ⇒ 须版本化迁移。
本工具仅做该字段替换（+ 版本/溯源块），**其余逐字节保留**（机判 diff），产出 ALLOC.7（**不动** CO-60 的候选 `..._v6.json`，其 sha `2ebda54c…` 仍可查）。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
SRC = STEP2 / "m13_v57_co16_channel_allocation_v5.json"
OUT = STEP2 / "m13_v57_co16_channel_allocation_v7.json"
SRC_SHA16 = "0bf6cdc203887a48"


def sha16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    assert sha16(SRC) == SRC_SHA16, f"ALLOC.5 drift: {sha16(SRC)}"
    d5 = json.loads(SRC.read_text(encoding="utf-8"))
    d6 = json.loads(SRC.read_text(encoding="utf-8"))

    moved = []
    for pid, pg in d6["pages"].items():
        if pg.get("stub_layer") == "In6.Cu":
            pg["stub_layer"] = "In5.Cu"
            moved.append(pid)
    assert moved, "no stub_layer=In6.Cu found"
    d6["revision"] = "CO16-ALLOC.7"
    d6["_supersedes"] = {"artifact": "m13_v57_co16_channel_allocation_v5.json", "sha16": SRC_SHA16,
                         "reason": "CO-68 方案(a)：信号层集 In6.Cu -> In5.Cu（此时 In6 为 GND 平面）；仅 stub_layer 字段迁移。注：CO-60 的**候选** `..._v6.json`（sha 2ebda54c…）为走廊 1.580 实验件，本件不触碰。"}
    d6["_changed_fields"] = {"stub_layer": {"from": "In6.Cu", "to": "In5.Cu", "pages": sorted(moved)}}

    # 机判：除版本/溯源/被迁移字段外，其余逐字节同 ALLOC.5
    for k in list(d6):
        if k in ("revision", "_supersedes", "_changed_fields"):
            continue
        if k == "pages":
            for pid in d6[k]:
                pg6 = dict(d6[k][pid]); pg5 = dict(d5[k][pid])
                pg6.pop("stub_layer", None); pg5.pop("stub_layer", None)
                assert pg6 == pg5, f"unexpected change in pages[{pid}]"
        else:
            assert d6[k] == d5[k], f"unexpected change in key {k}"
    OUT.write_text(json.dumps(d6, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": sha16(OUT),
                      "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "moved_pages": sorted(moved)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
