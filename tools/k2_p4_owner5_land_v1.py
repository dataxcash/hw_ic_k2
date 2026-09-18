#!/usr/bin/env python3
"""k2_p4_owner5_land_v1.py — 沙箱件落仓库（T-41/T-22 纪律；#K2-24 执行链）。

用法：python3 k2_p4_owner5_land_v1.py --pair <sandbox>=<repo> [--pair ...] --apply --confirm-repo-write
动作：逐对 → 断言 repo 目标存在（否则须 `--allow-new`）→ T-22 备份旧件到 /tmp/opencode/backup-owner5-<ts>/ →
      写入 → 打印 **旧 sha16 → 新 sha16**；任一目标 sha 不符合预期（`--expect <sha16>`）即 fail-closed。
"""
from __future__ import annotations
import argparse, hashlib, os, shutil, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", action="append", required=True, help="<sandbox_src>=<repo_dst>")
    ap.add_argument("--expect", action="append", default=[], help="<repo_dst>=<sha16> 预期新 sha（可多次）")
    ap.add_argument("--allow-new", action="store_true", help="允许目标不存在（新件）")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm-repo-write", action="store_true")
    a = ap.parse_args()
    if not (a.apply and a.confirm_repo_write):
        print("BLOCKED(T-41): 须 --apply --confirm-repo-write")
        return 2
    pairs = [p.split("=", 1) for p in a.pair]
    exp = dict(e.split("=", 1) for e in a.expect)
    for src, dst in pairs:
        if not os.path.isfile(src):
            raise SystemExit(f"FAIL-CLOSED: 沙箱源不存在 {src}")
    ts = time.strftime("%Y%m%dT%H%M%S")
    bk = f"/tmp/opencode/backup-owner5-{ts}"
    os.makedirs(bk, exist_ok=True)
    for src, dst in pairs:
        d_abs = os.path.abspath(dst)
        if not os.path.isfile(d_abs) and not a.allow_new:
            raise SystemExit(f"FAIL-CLOSED: 目标不存在且未 --allow-new: {dst}")
        old = sha16(d_abs) if os.path.isfile(d_abs) else "无(新件)"
        os.makedirs(os.path.dirname(d_abs), exist_ok=True)
        if os.path.isfile(d_abs):
            shutil.copy2(d_abs, os.path.join(bk, os.path.basename(d_abs)))
        shutil.copy2(src, d_abs)
        new = sha16(d_abs)
        if d_abs in {os.path.abspath(k) for k in exp} and exp[d_abs] != new:
            raise SystemExit(f"FAIL-CLOSED: {dst} 新 sha16={new} != 预期 {exp[d_abs]}")
        print(f"[land] {os.path.relpath(d_abs, ROOT):55s} {old} → {new}")
    print(f"[T-22] 旧件备份 -> {bk}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
