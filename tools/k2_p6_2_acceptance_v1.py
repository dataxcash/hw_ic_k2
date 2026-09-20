#!/usr/bin/env python3
"""k2_p6_2_acceptance_v1.py —— **P6-2 验收件（机读）**。

判据（《K2 整体整改计划》§② P6 完工判据②）：
  「模板整改后：`k1|k2_jlc_template.kicad_pro` 的 ignore 集 == **manifest 应然集** [结构=0 差异]」

口径（**零新增判据维**；本件只做比对，不改任何文件）：
  应然集 = `criteria/manifest.k2.yaml` 的 `rule_severity_exemptions`（未登记豁免 ⇒ deny-by-default；
           现为空 ⇒ 应然集 = ∅）。`rule_severity_manifest.expect` 文本一并登记为证据。
  受控集 = `git ls-files '*.kicad_pro'`（k2 为 CO-81 口径；k1 侧单列，其应然集归 K1 manifest）。

模式：
  ① 现状体检（默认）：逐文件报 ignore 集 vs 模板 ignore 集 vs 应然集。
  ② `--expect-zero`：差异必须 == 0（阶段门验收；用于 P6-2 完工判据）。
  ③ `--simulate <diff 目录>`：把受控 `.kicad_pro` 复制到 /tmp 镜像并施加补丁（`patch --posix -p1`，
     容器式布局）后评估 ⇒ **落件前预测**，真源零改。

用法：
  python3 k2/tools/k2_p6_2_acceptance_v1.py [--expect-zero] [--simulate <dir>] [--out /tmp/opencode/p6_2_accept.json]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
CONTAINER = K2.parent
MANIFEST_K2 = CONTAINER / "criteria" / "manifest.k2.yaml"
TMPL_K2 = "tools/k2_jlc_template.kicad_pro"
TMPL_K1 = "tools/k1_jlc_template.kicad_pro"


def ignored(p: Path) -> dict:
    d = json.loads(p.read_text(encoding="utf-8"))
    sev = d["board"]["design_settings"]["rule_severities"]
    return sorted(k for k, v in sev.items() if v == "ignore")


def tracked(repo: Path) -> list:
    r = subprocess.run(["git", "ls-files", "*.kicad_pro"], cwd=str(repo), capture_output=True, text=True)
    return sorted(r.stdout.split())


def expected_set() -> dict:
    try:
        import yaml
        m = yaml.safe_load(MANIFEST_K2.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"available": False, "why": f"{type(exc).__name__}: {exc}"}
    ex = m.get("rule_severity_exemptions")
    exp = (m.get("checks") or {}).get("rule_severity_manifest") or {}
    return {"available": True, "set": sorted(ex or []), "expect_text": exp.get("expect"),
            "source": str(MANIFEST_K2.relative_to(CONTAINER))}


def evaluate(root: Path, rels: list, tmpl_rel: str) -> dict:
    tmpl = ignored(root / tmpl_rel) if (root / tmpl_rel).is_file() else None
    rows = []
    for rel in rels:
        p = root / rel
        ig = ignored(p)
        rows.append({"file": rel, "n_ignores": len(ig), "ignores": ig,
                     "vs_template": sorted(set(ig) ^ set(tmpl)) if tmpl is not None else None,
                     "ok_vs_template": (tmpl is not None and ig == tmpl)})
    return {"template": tmpl_rel, "template_ignores": tmpl, "rows": rows,
            "n_mismatch_vs_template": sum(0 if r["ok_vs_template"] else 1 for r in rows)}


def simulate(diff_dir: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="p6_2_sim_", dir="/tmp/opencode"))
    for repo, sub in ((K2, "k2"), (CONTAINER / "k1", "k1")):
        for rel in tracked(repo):
            dst = tmp / sub / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            src = repo / rel
            if src.is_symlink():
                os.symlink(os.readlink(src), dst)
            else:
                shutil.copy2(src, dst)
    diffs = sorted(Path(diff_dir).resolve().glob("*.diff"))  # 绝对化：patch -d 会先 chdir，相对 -i 会失败
    applied = []
    for d in diffs:
        r = subprocess.run(["patch", "--posix", "--batch", "-p1", "-d", str(tmp), "-i", str(d)],
                           capture_output=True, text=True)
        applied.append({"diff": d.name, "rc": r.returncode,
                        "out": (r.stdout + r.stderr).strip().splitlines()[-1:]})
    return tmp, applied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-zero", action="store_true")
    ap.add_argument("--simulate", default=None, help="含 *.diff 的目录（落件前预测）")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    doc = {"artifact": "k2_p6_2_acceptance", "schema": 1, "readonly": True,
           "expected_set_manifest": expected_set(), "mode": "simulate" if a.simulate else "status"}
    if a.simulate:
        root, applied = simulate(a.simulate)
        doc["simulate"] = {"mirror": str(root), "diff_dir": a.simulate, "applied": applied}
        doc["k2"] = evaluate(root / "k2", tracked(K2), TMPL_K2)
        doc["k1"] = evaluate(root / "k1", tracked(CONTAINER / "k1"), TMPL_K1)
        print(f"[simulate] 镜像 {root} · 施加 {len(applied)} 个补丁")
    else:
        doc["k2"] = evaluate(K2, tracked(K2), TMPL_K2)
        doc["k1"] = evaluate(CONTAINER / "k1", tracked(CONTAINER / "k1"), TMPL_K1)

    exp = doc["expected_set_manifest"]
    exp_set = exp.get("set") if exp.get("available") else None
    for label in ("k2", "k1"):
        blk = doc[label]
        for r in blk["rows"]:
            r["ok_vs_expected"] = (exp_set is not None and r["ignores"] == exp_set)
        blk["n_mismatch_vs_expected"] = sum(0 if r["ok_vs_expected"] else 1 for r in blk["rows"])
        print(f"[{label}] 模板 {blk['template']} ignore={len(blk['template_ignores'] or [])} · "
              f"文件差异(模板) {blk['n_mismatch_vs_template']}/{len(blk['rows'])} · "
              f"差异(应然集={exp_set}) {blk['n_mismatch_vs_expected']}/{len(blk['rows'])}")
        for r in blk["rows"]:
            if not r["ok_vs_expected"]:
                print(f"    MISMATCH {r['file']} n_ignore={r['n_ignores']}")

    # 判据② 的**声明范围** = CO-81 的 k2 全受控集 + 两模板；k1 的其它 pro 归 K1 manifest 裁定 ⇒ 单列信息项
    k1_rows = doc["k1"]["rows"]
    k1_tmpl_rows = [r for r in k1_rows if r["file"] == doc["k1"]["template"]]
    k1_other = [r for r in k1_rows if r["file"] != doc["k1"]["template"]]
    doc["scope"] = {"in_scope": "k2 全受控集（CO-81 口径）+ 两模板（`k1|k2_jlc_template.kicad_pro`）",
                    "k1_other_files_mismatch": [r["file"] for r in k1_other if not r["ok_vs_expected"]],
                    "k1_other_note": "K1 侧非模板 pro 的 ignore 集归 **K1 manifest**（待落）裁定；本件只报为信息项，不计入判据② 的成否"}
    zero = (doc["k2"]["n_mismatch_vs_expected"] == 0
            and all(r["ok_vs_expected"] for r in k1_tmpl_rows))
    doc["templates_ok"] = {"k2": all(r["ok_vs_expected"] for r in doc["k2"]["rows"] if r["file"] == doc["k2"]["template"]),
                           "k1": all(r["ok_vs_expected"] for r in k1_tmpl_rows)}
    doc["structural_diff_zero"] = zero
    doc["verdict"] = ("PASS" if zero else "FAIL") if a.expect_zero or a.simulate else ("PASS(state)" if zero else "FAIL(state)")
    print(f"  => 结构差异 == 0 ? {zero} ⇒ {doc['verdict']}")
    if a.out:
        json.dump(doc, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if (zero or not a.expect_zero) else 1


if __name__ == "__main__":
    sys.exit(main())
