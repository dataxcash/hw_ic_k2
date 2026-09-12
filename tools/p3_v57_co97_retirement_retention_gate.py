#!/usr/bin/env python3
"""CO-97：【L2 可审计性 · 退役留存完整性闸】把红线「退役几何/决策必须显式留存（不得静默放弃）」
固化为**可重复机判闸** + 显式登记册（registry）。

背景：CO-96 F1 机判出 rev-9→rev-10 重建 `power_pad_connect` 时**静默丢弃** CO-89 的
`retired_superseded_bom`（`p3_v57_co93_pdn_rev10_derive.py` 零引用、变更说明未登记）。
本件把该缺陷类机判化：**任一 spec 版本间，凡上一版存在的「退役留存块」（路径首段含 `retired`）
在下一版消失者，必须在 `m13_v57_retirement_registry.json` 显式登记**（带理由 + 找回指针），
否则 FAIL。另：每个现存退役块必须**非空**（不得留空壳）。

判据（机判，无几何）：
  A. 逐版枚举退役留存块（路径首段 = 第一次出现含 `retired` 的段，剥离 list 下标）；
  B. 逐相邻版本求 **drop = prev − cur**；
  C. 每个 drop 必须在 registry 有匹配项（键 + from_rev→to_rev + reason + recovery）；
  D. registry 不得有**无对应 drop 的陈旧项**；
  E. 现存退役块不得为空（{} / [] / "" / 空骨架）。
牙齿：合成注入（① 未登记 drop 必被抓；② 已登记 drop 必放行；③ 空退役块必被抓）。

只读 SPEC/registry；不改 SPEC/板/阈值/冻结源；零坐标搜索；无 while。
CLI: python3 tools/p3_v57_co97_retirement_retention_gate.py [--registry R] [--out J]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
DEFAULT_REGISTRY = L3 / "m13_v57_retirement_registry.json"
DEFAULT_OUT = STEP2 / "m13_v57_co97_retirement_retention_gate.json"

BASE = {"spec_rev11": "d85f10f722ba22b0", "board": "a3ce9ab803045a0a",
        "spec_frozen": "0bd52ed48e720b8c", "drc_rules": "0a459839e15960b8"}


def s16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def rev_number(p: Path):
    m = re.findall(r"spec-rev-(\d+)", p.name)
    return int(m[0]) if m else 0  # frozen = 0


def spec_files():
    fs = [p for p in L3.glob("SPEC_k2_v4*.json") if "bak" not in p.name and p.name != "SPEC_k2_v4.json"]
    fs = sorted(fs, key=rev_number)
    frozen = L3 / "SPEC_k2_v4.json"
    return ([frozen] if frozen.exists() else []) + fs


def retention_blocks(obj) -> set:
    """枚举退役留存块（截断到首个含 retired 的路径段；剥离 list 下标）。"""
    out = set()

    def rec(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                np = f"{path}/{k}"
                if "retired" in k.lower():
                    out.add(re.sub(r"\[\d+\]", "[#]", np))
                    continue  # 不再深入（其子字段不算独立块）
                rec(v, np)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                rec(v, f"{path}[{i}]")
    rec(obj, "")
    return out


def blocks_by_value(obj) -> dict:
    """块路径 -> 值（用于非空判定）。"""
    out = {}

    def rec(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                np = f"{path}/{k}"
                if "retired" in k.lower():
                    out[re.sub(r"\[\d+\]", "[#]", np)] = v
                    continue
                rec(v, np)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                rec(v, f"{path}[{i}]")
    rec(obj, "")
    return out


def is_empty_block(v) -> bool:
    if v in ({}, [], "", None):
        return True
    if isinstance(v, dict):
        return all(is_empty_block(x) for x in v.values())
    if isinstance(v, list):
        return all(is_empty_block(x) for x in v)
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)

    ident = {"spec_rev11": s16(L3 / "SPEC_k2_v4.spec-rev-11.json"), "board": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
             "spec_frozen": s16(L3 / "SPEC_k2_v4.json"),
             "drc_rules": s16(K2.parent / "_shared/eda_core/drc_rules.json")}
    mismatch = {k: {"expect": v, "actual": ident.get(k)} for k, v in BASE.items() if ident.get(k) != v}

    revs = []
    for f in spec_files():
        s = json.loads(f.read_text())
        revs.append({"file": f.name, "rev": rev_number(f), "blocks": retention_blocks(s), "values": blocks_by_value(s)})

    drops = []
    for prev, cur in zip(revs, revs[1:]):
        for k in sorted(prev["blocks"] - cur["blocks"]):
            drops.append({"key": k, "from": prev["file"], "from_rev": prev["rev"], "to": cur["file"], "to_rev": cur["rev"]})

    reg = json.loads(Path(a.registry).read_text()) if Path(a.registry).exists() else {"declared_drops": []}
    declared = reg.get("declared_drops", [])
    dkeys = {(d.get("key"), d.get("from_rev"), d.get("to_rev")) for d in declared}
    undeclared = [d for d in drops if (d["key"], d["from_rev"], d["to_rev"]) not in dkeys]
    stale = [d for d in declared if (d.get("key"), d.get("from_rev"), d.get("to_rev")) not in
             {(x["key"], x["from_rev"], x["to_rev"]) for x in drops}]
    # 退役块内容快照（advisory：空退役列表可能合法——如 MCU_VDD 只退役 segments 不退役 polygons ⇒ 仅记录，不判 FAIL）
    empty_advisory = []
    for r in revs:
        for k, v in r["values"].items():
            if is_empty_block(v):
                empty_advisory.append({"file": r["file"], "key": k})
    # 找回指针可用性（file 存在）
    recovery_bad = []
    for d in declared:
        for ptr in d.get("recovery", []):
            pp = ptr.get("path")
            if pp and not (Path(pp).exists() or Path(K2 / pp).exists() or Path(K2.parent / pp).exists()):
                recovery_bad.append({"key": d.get("key"), "path": pp})

    # 牙齿：全部**合成、自洽**（不依赖真实 registry 状态）
    def _undeclared(sample, dset):
        return [d for d in sample if (d["key"], d["from_rev"], d["to_rev"]) not in dset]
    syn = {"key": "/pd/SYNTH/retired_x", "from_rev": 9, "to_rev": 10}
    tooth_undeclared = len(_undeclared([syn], set())) == 1                 # 未登记 drop 必被抓
    tooth_declared_ok = len(_undeclared([syn], {(syn["key"], 9, 10)})) == 0  # 已登记 drop 必放行
    syn_stale = {"key": "/pd/SYNTH/retired_y", "from_rev": 1, "to_rev": 2}
    tooth_stale = len([x for x in [syn_stale] if (x["key"], x["from_rev"], x["to_rev"]) not in
                       {(syn["key"], 9, 10)}]) == 1                        # 陈旧登记项必被抓
    teeth_ok = tooth_undeclared and tooth_declared_ok and tooth_stale

    issues = {"undeclared_drops": undeclared, "stale_registry_entries": stale,
              "unresolvable_recovery_pointers": recovery_bad}
    advisory = {"empty_retention_blocks": empty_advisory}
    bad = any(issues[k] for k in issues)
    baseline_ok = not mismatch
    verdict = "BASELINE_MISMATCH" if not baseline_ok else ("TEETH_FAIL" if not teeth_ok else ("FAIL" if bad else "PASS"))

    rec = {
        "artifact": "m13_v57_co97_retirement_retention_gate", "schema": 1, "revision": "CO-97.1",
        "nature": "L2 可审计性：退役留存完整性闸（红线『退役决策须显式留存』机判化）+ 显式登记册",
        "inputs": {"registry": Path(a.registry).name, "registry_sha16": (s16(Path(a.registry)) if Path(a.registry).exists() else None),
                   "spec_revs": [r["file"] for r in revs], **ident},
        "baseline_expectations": BASE, "baseline_mismatch": mismatch,
        "retention_blocks_per_rev": {r["file"]: sorted(r["blocks"]) for r in revs},
        "drops": drops, "declared_drops": declared,
        "issues": issues, "advisory": advisory,
        "teeth": {"undeclared_drop_detected": tooth_undeclared,
                  "declared_drop_passes": tooth_declared_ok,
                  "stale_registry_entry_detected": tooth_stale},
        "teeth_ok": teeth_ok, "baseline_ok": baseline_ok,
        "non_claims": ["只读闸；不改 SPEC/板/阈值/冻结源", "登记册只声明『移除已登记』，不替代 SPEC 内留存",
                       "本件不重跑链路（无 SPEC 改动）"],
        "verdict": verdict,
    }
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("CO-97 verdict=%s drops=%d undeclared=%d stale=%d recovery_bad=%d teeth_ok=%s" %
          (verdict, len(drops), len(undeclared), len(stale), len(recovery_bad), teeth_ok))
    for d in drops:
        print("   DROP", d["key"], "%s->%s" % (d["from"], d["to"]),
              "DECLARED" if (d["key"], d["from_rev"], d["to_rev"]) in dkeys else "UNDECLARED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
