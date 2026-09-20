#!/usr/bin/env python3
"""k2_p6_1_acceptance_v1.py —— **P6-1 验收件（机读）**。

用途：把《K2 整体整改计划》§② P6 完工判据① 的**四项同源期望**（#K2-41 §三-⑥ 已裁）
      做成**可机判的验收件**，供 P6 开闸时一条命令出 PASS/FAIL。

判据①（原文）：`adjudicate.py --project k1` 出 verdict，且**必须命中**：
  `ignore_without_ruling(9)` · `no_pipeline(1)` · `no_fp_lib_table(1)` · `sheets_empty(1)`

本件的口径（**不新增任何判据维；19 维集合不动**）：
  ①~③ 判据维 = 判定器 19 维中的既有维（rule_severity_manifest / pipeline_present / fp_lib_table_present）
  ④ `sheets_empty` = **输入侧实测**（rev=3 的 19 维中无该维；加维=新增检查齿 ⇒ owner ② 不许）
      ⇒ 读 `k1/k1_v1.kicad_pro` 的 `board.design_settings.sheets == []`

另含 **2 条完整性/放行前置断言**（非判据维）：
  A. verdict 的维集 == 19（防维集漂移；与 criteria/manifest.k2.yaml 的 countersigned_scope 对齐）
  B. `provisional == false`（**manifest 未经监理签认 ⇒ 不得宣称 P6-1 通过**；G-c2 落件的机器体现）

只读：本件不写任何项目件；输入为 verdict JSON + .kicad_pro。
用法：
  python3 k2/tools/k2_p6_1_acceptance_v1.py \
    --verdict /tmp/opencode/k1_verdict.json --pro k1/k1_v1.kicad_pro [--out /tmp/opencode/k1_p6_1_accept.json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

DIMS_19 = [
    "zone_filled", "device_has_pads", "drill_count", "net_declared_realized", "pin_map_complete",
    "non45_segments", "refdes_sets_equal", "pipeline_present", "verdict_schema", "drc_errors",
    "drc_warning_dispositions", "unconnected_zero", "fp_lib_table_present", "lib_electrical_level",
    "pads_within_outline", "keepout_active", "rule_severity_manifest", "density_and_clearance",
    "ref_plane_continuity",
]
IGNORE_9 = ["copper_sliver", "footprint_filters_mismatch", "footprint_type_mismatch", "missing_courtyard",
            "silk_over_copper", "silk_overlap", "track_not_centered_on_via",
            "tuning_profile_track_geometries", "via_dangling"]


REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _authorized_disabled(manifest_name: str) -> dict:
    """已签认 manifest 中**显式** `enabled: false` 的判据维（口径对齐）。

    防维集漂移的**强化**写法（C-12 护栏）：verdict 少维**必须**在**已签认**
    manifest 里显式关闭，否则仍 FAIL ⇒ 不得静默少维、不得为变绿缩口径。
    依据：`criteria/manifest.k1.yaml` 的 `checks.<dim>.enabled: false`
    （K1 `ref_plane_continuity` 为 vacuous，由监理落件时显式关闭）。"""
    if not manifest_name:
        return {}
    path = os.path.join(REPO, "criteria", str(manifest_name))
    if not os.path.isfile(path):
        return {}
    try:
        import yaml
        m = yaml.safe_load(open(path, encoding="utf-8").read()) or {}
    except Exception:
        return {}
    checks = m.get("checks") or {}
    return {k: v for k, v in checks.items()
            if isinstance(v, dict) and v.get("enabled") is False}


def _fail_map(v: dict) -> dict:
    return {f.get("check"): (f.get("detail") or "") for f in (v.get("fails") or [])}


def check_ignore_without_ruling(fm: dict) -> dict:
    d = fm.get("rule_severity_manifest")
    if d is None:
        return {"ok": False, "why": "verdict 无 rule_severity_manifest 维（判据①第 1 项无法命中）"}
    m = re.search(r"未登记豁免的 ignore\s+(\d+)/(\d+)", d)
    n = int(m.group(1)) if m else None
    hits = [k for k in IGNORE_9 if k in d]
    return {"ok": n == 9 and len(hits) == 9, "expected": "ignore_without_ruling(9)",
            "read": f"未登记 ignore {n}/62" if n is not None else d[:80],
            "names_hit": len(hits), "names": hits}


def check_no_pipeline(fm: dict) -> dict:
    d = fm.get("pipeline_present")
    if d is None:
        return {"ok": False, "why": "verdict 无 pipeline_present 维"}
    m = re.search(r"的目录\s+(\d+)\s+个", d)
    n = int(m.group(1)) if m else None
    scope_ok = "scope=k1" in d
    return {"ok": scope_ok and n == 1 and "k1/sch" in d, "expected": "no_pipeline(1)",
            "read": f"scope=k1? {scope_ok} · 目录数 {n} · 命中 k1/sch? {'k1/sch' in d}"}


def check_no_fp_lib_table(fm: dict) -> dict:
    d = fm.get("fp_lib_table_present")
    if d is None:
        return {"ok": False, "why": "verdict 无 fp_lib_table_present 维"}
    m = re.search(r"fp-lib-table\s*@\s*(\S+?)\s*:", d)
    where = (m.group(1) if m else "")
    return {"ok": ("缺失" in d) and os.path.basename(where.rstrip("/")) == "k1",
            "expected": "no_fp_lib_table(1)", "read": d[:120], "dir": where}


def check_sheets_empty(pro_path: str) -> dict:
    """判据①第 4 项 = **输入侧实测**（rev=3 无该维；不得新增检查齿）。"""
    try:
        d = json.load(open(pro_path, encoding="utf-8"))
        # KiCad pro：`sheets` 为**顶层**键（列表）；兼容旧布局的 board.design_settings.sheets
        if "sheets" in d:
            sheets = d["sheets"]
        else:
            sheets = d.get("board", {}).get("design_settings", {}).get("sheets", "__absent__")
    except Exception as exc:
        return {"ok": False, "expected": "sheets_empty(1)", "why": f"pro 不可读: {type(exc).__name__}: {exc}"}
    return {"ok": sheets == [], "expected": "sheets_empty(1)",
            "read": f"sheets == {sheets!r}", "source": f"输入侧实测 {pro_path}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdict", required=True)
    ap.add_argument("--pro", required=True, help="受审工程文件（k1/k1_v1.kicad_pro）")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if not os.path.exists(a.verdict):
        print(f"[FAIL] verdict 缺失: {a.verdict}（fail-closed）")
        return 1
    v = json.load(open(a.verdict, encoding="utf-8"))
    fm = _fail_map(v)
    dims = sorted(set(fm) | {o.get("check") for o in (v.get("oks") or [])})
    items = {
        "ignore_without_ruling(9)": check_ignore_without_ruling(fm),
        "no_pipeline(1)": check_no_pipeline(fm),
        "no_fp_lib_table(1)": check_no_fp_lib_table(fm),
        "sheets_empty(1)": check_sheets_empty(a.pro),
    }
    disabled = _authorized_disabled(v.get("manifest"))
    dim_set_ok = (set(dims) <= set(DIMS_19)) and (set(DIMS_19) - set(dims)) == set(disabled)
    integrity = {
        "dim_set_is_19": {"ok": dim_set_ok,
                          "read": (f"{len(dims)} 维 · 已签认显式关闭={sorted(disabled)}"),
                          "why": "防维集漂移（非判据维）：维集须 ⊆ 19 维基准，"
                                 "且缺维只能是在**已签认** manifest 中显式 enabled:false 者"},
        "manifest_countersigned": {"ok": v.get("provisional") is False,
                                   "read": f"provisional={v.get('provisional')} · manifest={v.get('manifest')}",
                                   "why": "manifest 未经监理签认 ⇒ 不得宣称 P6-1 通过（G-c2 落件）"},
    }
    ok_items = all(x["ok"] for x in items.values())
    ok_int = all(x["ok"] for x in integrity.values())
    doc = {"artifact": "k2_p6_1_acceptance", "schema": 1, "readonly": True,
           "verdict_file": a.verdict, "pro_file": a.pro,
           "verdict_n_pass": v.get("n_pass"), "verdict_n_fail": v.get("n_fail"),
           "four_items": items, "integrity_prerequisites": integrity,
           "verdict": "PASS" if (ok_items and ok_int) else "FAIL",
           "note": ("四项命中 + 完整性齐 ⇒ P6-1 验收通过" if (ok_items and ok_int)
                    else "四项命中不足或前置未满足（provisional≠false ⇒ 待 G-c2 签认落件）")}
    for k, x in items.items():
        print(f"  [{'OK  ' if x['ok'] else 'MISS'}] {k}: {x.get('read') or x.get('why')}")
    for k, x in integrity.items():
        print(f"  [{'OK  ' if x['ok'] else 'MISS'}] {k}（非判据维）: {x['read']}")
    print(f"  => P6-1 验收: {doc['verdict']}")
    if a.out:
        json.dump(doc, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if doc["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
