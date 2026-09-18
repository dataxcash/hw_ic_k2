#!/usr/bin/env python3
"""K2 · P4 · **SPEC D1/D2 排针列补正 + 版本 bump**（`column_x`/`positions[*].x` 26.5 → 27.94）。

依据：监理 **#K2-23 §二-7**（G9 几何停点裁「以 `column_x=27.94` 为准 bump SPEC（D1/D2 补正）」）
+ `K2-P4-Z4-STALE-REFRESH-CHECKLIST-v1.md` D1/D2 + P3-4 实测最小余量 0.08mm。

事实（本器 fail-closed 前置）：受审板 `k2/hw/k2_v4_8L.l5.kicad_pcb` 实测 5 排针 x **全 = 27.94**
（J6/J9/J11/J12/J13）；rev-47 SPEC 现值 `column_x=26.5`、`positions[*].x=26.5` ⇒ **SPEC 侧转录误差**，非改需求。

本器只做（**不写板/库/pro**）：
  ① `components.pin_headers.column_x` 26.5 → 27.94；
  ② `components.pin_headers.positions[*][0]` 26.5 → 27.94（逐件保持 y 不变）；
  ③ 新增 `_spec_rev_<new-rev>` 记账卡（含 authority/basis/board_sha16）+ `spec_version` bump；
  ④ 同步 `project.yaml` 的 `spec_name` → 新 rev。

纪律：**T-22**（先备份 + 落改后校验旧 rev 逐字节未变）· **T-41**（写仓库须 `--apply --confirm-repo-write`）·
**rev-N 原件永不改**（修订走版本 bump）· dry-run 自带 `--work-dir` 预览供逐字核对 · 确定性（同输入同输出）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys


def sha16(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


COLUMN_OLD = 26.5
COLUMN_NEW = 27.94


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec-base", required=True)
    ap.add_argument("--spec-new", required=True)
    ap.add_argument("--project-yaml", required=True)
    ap.add_argument("--new-rev", type=int, required=True)
    ap.add_argument("--board", default="k2/hw/k2_v4_8L.l5.kicad_pcb")
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    a = ap.parse_args()

    base_name = os.path.basename(a.spec_base)
    new_name = os.path.basename(a.spec_new)
    d = json.load(open(a.spec_base, encoding="utf-8"))

    # ── fail-closed 前置 ──
    key = "_spec_rev_%d" % a.new_rev
    if key in d:
        print("REFUSE: %s 已存在于 base" % key, file=sys.stderr)
        return 2
    sv_old = d.get("spec_version", "")
    if sv_old != "1.1.spec-rev-%d" % (a.new_rev - 1):
        print("REFUSE: spec_version=%r 非预期（期望 1.1.spec-rev-%d）" % (sv_old, a.new_rev - 1), file=sys.stderr)
        return 2
    ph = d.get("components", {}).get("pin_headers")
    if not isinstance(ph, dict):
        print("REFUSE: 缺 components.pin_headers", file=sys.stderr)
        return 2
    if ph.get("column_x") != COLUMN_OLD:
        print("REFUSE: column_x=%r != %s（前置不符，勿盲改）" % (ph.get("column_x"), COLUMN_OLD), file=sys.stderr)
        return 2
    pos = ph.get("positions") or {}
    if sorted(pos) != ["J11", "J12", "J13", "J6", "J9"]:
        print("REFUSE: positions 件集异常 %r" % sorted(pos), file=sys.stderr)
        return 2
    bad = {k: v for k, v in pos.items() if not (isinstance(v, list) and v and v[0] == COLUMN_OLD)}
    if bad:
        print("REFUSE: 下列 positions x != %s ⇒ %r" % (COLUMN_OLD, bad), file=sys.stderr)
        return 2

    # ── 变更（只碰 D1/D2 + 记账）──
    ph["column_x"] = COLUMN_NEW
    for k in pos:
        pos[k][0] = COLUMN_NEW
    d[key] = {
        "card": "SPEC-REV-%d（G9 排针列补正）" % a.new_rev,
        "at": "2026-09-18",
        "authority": ("owner #14「L2 = 热机械 = 自裁勿停」 + 监理 #K2-23 §二-7"
                      "（G9 几何停点：以 column_x=27.94 为准 bump SPEC，D1/D2 补正）"),
        "basis": [
            "D1/D2 补正：`components.pin_headers.column_x` 与 `positions[*].x` 26.5 → 27.94"
            " —— SPEC 侧**转录误差**，非改需求。",
            "依据：P3-4 实测排针列最小余量 0.08mm（图纸 `D1_pinheader_interference` / `C4` 已按 27.94 复算）；"
            "受审板实测 5 排针 x 全 = 27.94。",
            "G9 判据（生成器 S8 / `check_pin_headers`）继续消费 **SPEC（canonical）**，"
            "**不得**改为消费原始 L3 图纸（否则倒置权威）。",
            "权威链：真源 → SPEC → 板；本 rev **不涉**真源/板/pro/库/criteria；rev-47 原件逐字节不变。",
            "Z4 族内矛盾之一（SPEC 26.5 ↔ drawings.criteria 27.94 ↔ 板 27.94）由本项消除；"
            "图纸整族重生成于 rev-%d 基线（后续步骤）。" % a.new_rev,
        ],
        "board_sha16": sha16(a.board) if os.path.exists(a.board) else None,
    }
    d["spec_version"] = sv_old.replace("spec-rev-%d" % (a.new_rev - 1), "spec-rev-%d" % a.new_rev)

    os.makedirs(a.work_dir, exist_ok=True)
    preview = os.path.join(a.work_dir, new_name)
    with open(preview, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=False)
    print("[plan] column_x %s → %s ; positions[*].x → %s（%d 件）"
          % (COLUMN_OLD, COLUMN_NEW, COLUMN_NEW, len(pos)))
    print("[plan] spec_version: %s → %s ; 新增 %s" % (sv_old, d["spec_version"], key))
    print("[plan] project.yaml: %s → %s" % (base_name, new_name))
    print("[preview] %s (sha16 %s)" % (preview, sha16(preview)))
    if not a.apply:
        print("\n[DRY-RUN] 批准后执行：追加 --apply --confirm-repo-write")
        return 0
    if not a.confirm_repo_write:
        print("REFUSE: --apply 需 --confirm-repo-write（T-41）", file=sys.stderr)
        return 2

    bdir = os.path.join(a.work_dir, "backup")
    os.makedirs(bdir, exist_ok=True)
    shutil.copy2(a.spec_base, os.path.join(bdir, base_name))
    shutil.copy2(a.project_yaml, os.path.join(bdir, os.path.basename(a.project_yaml)))
    base_sha_before = sha16(a.spec_base)
    ytxt = open(a.project_yaml, encoding="utf-8").read()
    if base_name not in ytxt:
        print("REFUSE: project.yaml 未含 %s" % base_name, file=sys.stderr)
        return 2
    shutil.copy2(preview, a.spec_new)
    open(a.project_yaml, "w", encoding="utf-8").write(ytxt.replace(base_name, new_name))
    if sha16(a.spec_base) != base_sha_before:
        raise RuntimeError("旧 rev 被改动 ⇒ 中止（T-22）")
    print("[apply] %s sha16=%s" % (new_name, sha16(a.spec_new)))
    print("[apply] %s sha16=%s" % (os.path.basename(a.project_yaml), sha16(a.project_yaml)))
    print("[apply] 旧 rev 未变：%s %s ✓" % (base_name, base_sha_before))
    return 0


if __name__ == "__main__":
    sys.exit(main())
