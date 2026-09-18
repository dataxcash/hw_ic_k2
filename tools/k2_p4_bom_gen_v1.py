#!/usr/bin/env python3
"""k2_p4_bom_gen_v1.py — K2 · P4 · `k2/fab/k2_v4_bom.csv` 生成器（**ref 集 BOM**；判据消费口径）。

授权：#K2-23 §四 优先序 5「BOM + G11 真源绑定 → pipeline.yaml 安装（乙 + D-7a）→ E2E 复算」；
      骨架与实测见 `k2/docs/K2-P4-BOM-GENERATOR-SKELETON-AND-DRYRUN-v1.md`（inc63）。

schema（**硬约束**）：`Ref` 头 + **每行一个 ref**。
  依据：`_shared/eda_core/pipeline/checks.py::check_bom_consistent` 逐行 `csv.reader(row)[0].split(",")`
  ⇒ 未加引号的多 ref 同行会被拆列、只读到第一个 ⇒ 实测误报「BOM 与 sch 不同步」（inc58 §0-5；inc63 §0-3 负控）。

来源：**真 sch netlist**（`kicad-cli sch export netlist --format kicadsexpr`，经 $SHARUN）；不读板、不读 SPEC（避 C-1）。
交叉核对：ref 集须与真源 yaml（`pm_gate/project.yaml::nets_yaml`）placements 一致（两独立来源，非自证）；不一致 ⇒ fail-closed。
fail-closed：sch 缺 / SHARUN 不可执行 / netlist 导出失败 / 0 器件 / ref 含逗号换行 / 与真源不同集 ⇒ 非零退出，**不落盘**。
确定性（T-38）：排序 + 去重 + 无时间戳 ⇒ 同输入同 sha。
范围：本件只满足**判据消费口径（ref 集）**；含 Value/Footprint/Qty 的**交付级 BOM 属 P5 交付面**（另件另裁）。
写仓库纪律（T-41/T-22）：默认 dry-run（只打印 + 校验 + 报预测 sha）；`--apply --confirm-repo-write` 才落盘，
  且落盘前**自动备份旧件并打印旧 sha**。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K2 = os.path.join(ROOT, "k2")
DEFAULT_SCH = os.path.join(K2, "hw/sch/k2_sch.kicad_sch")
DEFAULT_OUT = os.path.join(K2, "fab/k2_v4_bom.csv")
REF_RE = re.compile(r'\(comp\s+\(ref "([^"]+)"\)')


def sha16(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def sharun_path(explicit: str | None) -> str:
    cand = explicit or os.environ.get("SHARUN") or os.path.join(ROOT, "AppDir/sharun")
    if not (os.path.isfile(cand) and os.access(cand, os.X_OK)):
        raise SystemExit(f"FAIL-CLOSED: SHARUN 不可执行: {cand}")
    return cand


def export_refs(sch: str, sharun: str, tmp_net: str) -> list[str]:
    if not os.path.isfile(sch):
        raise SystemExit(f"FAIL-CLOSED: sch 缺件: {sch}")
    os.makedirs(os.path.dirname(tmp_net), exist_ok=True)
    proc = subprocess.run([sharun, "kicad-cli", "sch", "export", "netlist", sch,
                           "--format", "kicadsexpr", "--output", tmp_net],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"FAIL-CLOSED: netlist 导出失败 rc={proc.returncode}: {proc.stdout[-300:]}{proc.stderr[-300:]}")
    refs = sorted({m.group(1) for m in REF_RE.finditer(io.open(tmp_net, encoding="utf-8").read())})
    if not refs:
        raise SystemExit("FAIL-CLOSED: netlist 0 器件")
    bad = [r for r in refs if "," in r or "\n" in r]
    if bad:
        raise SystemExit(f"FAIL-CLOSED: ref 含逗号/换行（违反「每行一 ref」口径）: {bad[:5]}")
    return refs


def truth_source_refs() -> tuple[list[str], str]:
    """真源 yaml placements refs（经 project.yaml::nets_yaml；交叉核对用）。"""
    sys.path.insert(0, os.path.join(K2, "_shared"))
    os.environ.setdefault("PM_GATE_PROJECT_ROOT", K2)
    import yaml
    cfg_path = os.path.join(K2, "pm_gate/project.yaml")
    nets_yaml = (yaml.safe_load(io.open(cfg_path, encoding="utf-8")) or {}).get("nets_yaml")
    if not nets_yaml:
        raise SystemExit("FAIL-CLOSED: project.yaml 无 nets_yaml 指针")
    path = os.path.join(K2, nets_yaml)
    doc = yaml.safe_load(io.open(path, encoding="utf-8"))
    refs = sorted({p["ref"] for sh in doc.get("sheets", []) for p in sh.get("placements", [])})
    return refs, os.path.relpath(path, ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description="K2 ref 集 BOM 生成器（默认 dry-run）")
    ap.add_argument("--sch", default=DEFAULT_SCH)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--sharun", default=None)
    ap.add_argument("--apply", action="store_true", help="落盘（写仓库须同时 --confirm-repo-write）")
    ap.add_argument("--confirm-repo-write", action="store_true", help="确认写仓库（T-41）")
    a = ap.parse_args()

    sharun = sharun_path(a.sharun)
    tmp_net = "/tmp/opencode/bom_gen_net.kicadsexpr"
    refs = export_refs(a.sch, sharun, tmp_net)
    ts_refs, ts_path = truth_source_refs()
    if refs != ts_refs:
        raise SystemExit(f"FAIL-CLOSED: sch netlist ref 集 != 真源 placements ref 集 "
                         f"(net 独有 {sorted(set(refs) - set(ts_refs))[:5]}; yaml 独有 {sorted(set(ts_refs) - set(refs))[:5]})")
    payload = "Ref\n" + "\n".join(refs) + "\n"
    payload_sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    repo_out = os.path.abspath(DEFAULT_OUT)
    out_abs = os.path.abspath(a.out)
    print(f"[BOM] sch={os.path.relpath(a.sch, ROOT)} refs={len(refs)} · 真源 {ts_path} 交叉核对一致")
    print(f"[BOM] out={os.path.relpath(out_abs, ROOT)} 预测 sha16={payload_sha}")
    if os.path.isfile(out_abs):
        old = io.open(out_abs, encoding="utf-8").read()
        try:
            old_refs = sorted({r.strip() for r in next(csv.reader(io.StringIO(old)))[0:1]})
        except Exception:
            old_refs = []
        print(f"[BOM] 旧件 sha16={sha16(out_abs)} "
              f"(旧 ref 集一致={old == payload if old == payload else 'N/A(内容不同)'})")
    if out_abs == repo_out and not (a.apply and a.confirm_repo_write):
        print("BLOCKED(T-41): 目标是仓库路径；须 --apply --confirm-repo-write（或用 --out 指沙箱）。")
        return 2
    if out_abs != repo_out:
        print(f"[BOM] 沙箱目标（非仓库路径）⇒ 直接落盘：{out_abs}")
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    if os.path.isfile(out_abs):
        bk = f"/tmp/opencode/backup-bom-{time.strftime('%Y%m%dT%H%M%S')}"
        os.makedirs(bk, exist_ok=True)
        shutil.copy2(out_abs, os.path.join(bk, os.path.basename(out_abs)))
        print(f"[T-22] 备份 {os.path.basename(out_abs)} sha16={sha16(out_abs)} -> {bk}/")
    io.open(out_abs, "w", encoding="utf-8", newline="\n").write(payload)
    print(f"[BOM] 落件 {os.path.relpath(out_abs, ROOT)} sha16={sha16(out_abs)} refs={len(refs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
